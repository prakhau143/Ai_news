import json
import requests
from datetime import timedelta
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import NewsItem, CATEGORY_THEMES


# ── Dashboard home (graphs only, no news cards) ──────────────────
@login_required
def dashboard_home(request):
    two_days_ago = timezone.now() - timedelta(days=2)
    recent_count = NewsItem.objects.filter(published_at__gte=two_days_ago).count()
    total_count = NewsItem.objects.count()
    from apps.agent.tasks import AGENT_STATUS
    return render(request, 'dashboard/home.html', {
        'recent_count': recent_count,
        'total_count': total_count,
        'agent_status': AGENT_STATUS,
    })


# ── News catalogue (Pinterest grid) ──────────────────────────────
@login_required
def news_catalogue(request):
    two_days_ago = timezone.now() - timedelta(days=2)
    news = NewsItem.objects.filter(published_at__gte=two_days_ago).order_by('-importance', '-published_at')
    category_themes_json = json.dumps({k: {'gradient': v['gradient'], 'icon': v['icon'], 'logo': v['logo']} for k, v in CATEGORY_THEMES.items()})
    return render(request, 'news/catalogue.html', {
        'news': news,
        'category_themes_json': category_themes_json,
    })


# ── News detail (full article) ────────────────────────────────────
@login_required
def news_detail(request, news_id):
    news = get_object_or_404(NewsItem, id=news_id)
    trending = NewsItem.objects.exclude(id=news_id).order_by('-importance', '-published_at')[:6]
    theme = CATEGORY_THEMES.get(news.category, CATEGORY_THEMES['General AI'])
    return render(request, 'news/detail.html', {
        'news': news,
        'trending': trending,
        'theme': theme,
    })


# ── Live search API ────────────────────────────────────────────────
@login_required
def search_news(request):
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse([], safe=False)

    two_days_ago = timezone.now() - timedelta(days=2)
    results = NewsItem.objects.filter(
        published_at__gte=two_days_ago
    ).filter(
        title__icontains=q
    ) | NewsItem.objects.filter(
        published_at__gte=two_days_ago
    ).filter(
        summary__icontains=q
    ) | NewsItem.objects.filter(
        published_at__gte=two_days_ago
    ).filter(
        category__icontains=q
    )

    data = []
    for item in results[:20]:
        theme = CATEGORY_THEMES.get(item.category, CATEGORY_THEMES['General AI'])
        data.append({
            'id': item.id,
            'title': item.title,
            'summary': item.summary[:120],
            'category': item.category,
            'tag': item.tag,
            'gradient': theme['gradient'],
            'icon': theme['icon'],
            'logo': theme['logo'],
            'source': item.source,
        })
    return JsonResponse(data, safe=False)


# ── Fetch AI news JSON (for catalogue JS) ─────────────────────────
@login_required
def fetch_ai_news_api(request):
    two_days_ago = timezone.now() - timedelta(days=2)
    news_qs = NewsItem.objects.filter(published_at__gte=two_days_ago).order_by('-importance', '-published_at')[:60]

    items = []
    for item in news_qs:
        theme = CATEGORY_THEMES.get(item.category, CATEGORY_THEMES['General AI'])
        seeds = theme.get('seeds', [42])
        seed = seeds[item.pk % len(seeds)]
        items.append({
            'id': item.pk,
            'title': item.title,
            'summary': item.summary[:150],
            'category': item.category,
            'tag': item.tag,
            'source': item.source,
            'url': item.source_url,
            'published_at': item.published_at.isoformat(),
            'importance': item.importance,
            'theme': {
                'gradient': theme['gradient'],
                'icon': theme['icon'],
                'logo': theme['logo'],
            },
            'image_url': f"https://picsum.photos/seed/{item.category.replace(' ', '')}{seed}/600/400",
        })

    return JsonResponse({'success': True, 'news': items, 'fresh_count': len(items)})


# ── Generate full article content (Claude + Jina fallback) ────────
@csrf_exempt
@login_required
@require_http_methods(["POST"])
def generate_article_content(request):
    try:
        data = json.loads(request.body)
        title = data.get('title', '')
        summary = data.get('summary', '')
        url = data.get('url', '')
        category = data.get('category', '')
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

    # 1. Try Jina.ai to scrape original article (free, no key)
    if url and url != '#':
        scraped = _scrape_with_jina(url)
        if scraped and len(scraped) > 500:
            return JsonResponse({
                'success': True,
                'title': title,
                'content': _format_content(scraped[:4000]),
                'source': 'scraped',
            })

    # 2. Try Claude API
    anthropic_key = settings.ANTHROPIC_API_KEY
    if anthropic_key:
        result = _generate_with_claude(title, summary, category, anthropic_key)
        if result:
            return JsonResponse({
                'success': True,
                'title': title,
                'content': result,
                'source': 'claude',
            })

    # 3. Fallback: compose from summary
    fallback = _build_fallback_article(title, summary, category)
    return JsonResponse({
        'success': True,
        'title': title,
        'content': fallback,
        'source': 'summary',
    })


def _scrape_with_jina(url):
    try:
        resp = requests.get(f"https://r.jina.ai/{url}", timeout=10,
                            headers={'Accept': 'text/plain'})
        if resp.status_code == 200:
            return resp.text
    except Exception:
        pass
    return None


def _generate_with_claude(title, summary, category, api_key):
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        prompt = (
            f"Write a detailed, engaging 400-word news article about this AI topic:\n\n"
            f"Headline: {title}\n"
            f"Category: {category}\n"
            f"Summary: {summary}\n\n"
            "Include: what happened, why it matters for the AI industry, expert implications. "
            "Use HTML paragraphs (<p> tags). Professional but engaging tone."
        )
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        print(f"[Claude API] Error: {e}")
        return None


def _format_content(text):
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    return ''.join(f'<p>{p}</p>' for p in paragraphs[:15])


def _build_fallback_article(title, summary, category):
    return (
        f"<p><strong>{title}</strong></p>"
        f"<p>{summary}</p>"
        f"<p>This {category} development marks another milestone in the rapidly evolving AI landscape. "
        f"Industry experts are closely watching how this news will shape the competitive dynamics "
        f"among leading AI companies.</p>"
        f"<p><em>Full article generation requires Anthropic API credits. "
        f"<a href='#' onclick='history.back()'>Go back</a> to browse more news.</em></p>"
    )
