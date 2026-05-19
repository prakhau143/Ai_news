"""
News fetcher: GNews API → filter → categorize → save to DB.
Only keeps AI-related news from the last 2 days.
"""
import requests
from datetime import datetime, timedelta, timezone as pytz
from django.conf import settings

AI_KEYWORDS = [
    'artificial intelligence', 'ai ', ' ai,', 'machine learning', 'deep learning',
    'neural network', 'llm', 'large language model', 'gpt', 'chatgpt', 'openai',
    'claude', 'anthropic', 'gemini', 'deepseek', 'llama', 'mistral', 'copilot',
    'generative ai', 'ai model', 'ai agent', 'autonomous', 'transformer model',
    'diffusion model', 'stable diffusion', 'midjourney', 'ai chip', 'nvidia',
    'robot', 'automation', 'natural language', 'computer vision',
]

CATEGORY_KEYWORDS = {
    'OpenAI':    ['openai', 'chatgpt', 'gpt-4', 'gpt4', 'gpt-5', 'o1 ', 'o3 ', 'sora'],
    'Google':    ['google', 'gemini', 'deepmind', 'bard', 'vertex ai', 'google ai'],
    'Anthropic': ['anthropic', 'claude'],
    'Meta':      ['meta ', 'llama', 'meta ai', 'facebook ai', 'pytorch'],
    'DeepSeek':  ['deepseek'],
    'AI Agents': ['ai agent', 'autonomous agent', 'agentic', 'multi-agent'],
    'Research':  ['research', 'paper', 'study', 'arxiv', 'benchmark', 'dataset'],
    'Startup':   ['startup', 'funding', 'raises', 'seed round', 'series a', 'valuation'],
    'Healthcare':['healthcare', 'medical ai', 'drug discovery', 'health ai', 'clinical'],
    'Robotics':  ['robot', 'robotics', 'humanoid', 'boston dynamics', 'tesla robot'],
    'Tools':     ['tool', 'plugin', 'extension', 'api', 'sdk', 'platform', 'release'],
}

GNEWS_QUERIES = [
    'artificial intelligence',
    'ChatGPT OpenAI',
    'Google Gemini AI',
    'DeepSeek AI model',
    'Claude Anthropic',
    'AI agents autonomous',
    'large language model',
    'AI startup funding',
]


def detect_category(title: str, description: str) -> str:
    text = (title + ' ' + description).lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return cat
    return 'General AI'


def is_ai_related(title: str, description: str) -> bool:
    text = (title + ' ' + (description or '')).lower()
    return any(kw in text for kw in AI_KEYWORDS)


def detect_tag(importance: int, title: str) -> str:
    title_lower = title.lower()
    if any(w in title_lower for w in ['breakthrough', 'launch', 'new', 'announces', 'release']):
        return 'NEW'
    if importance >= 7:
        return 'HOT'
    if any(w in title_lower for w in ['trending', 'viral', 'popular', 'record']):
        return 'TRENDING'
    return 'NEW'


def score_importance(title: str, description: str) -> int:
    text = (title + ' ' + (description or '')).lower()
    score = 5
    high_impact = ['breakthrough', 'revolutionary', 'first ever', 'record', 'billion', 'trillion']
    medium_impact = ['major', 'significant', 'launch', 'release', 'announce', 'update']
    for w in high_impact:
        if w in text:
            score += 2
    for w in medium_impact:
        if w in text:
            score += 1
    return min(score, 10)


def fetch_articles_from_gnews(query: str, max_results: int = 10) -> list:
    api_key = settings.GNEWS_API_KEY
    if not api_key:
        return []

    url = (
        f"https://gnews.io/api/v4/search"
        f"?q={requests.utils.quote(query)}"
        f"&lang=en&max={max_results}"
        f"&sortby=publishedAt"
        f"&token={api_key}"
    )
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            return resp.json().get('articles', [])
        print(f"[GNews] Error {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        print(f"[GNews] Request failed: {e}")
    return []


def parse_published_at(dt_str: str):
    """Parse GNews datetime string to timezone-aware datetime."""
    from django.utils import timezone as dj_tz
    try:
        # GNews format: '2024-05-18T12:30:00Z'
        dt = datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%SZ')
        return dt.replace(tzinfo=pytz.utc)
    except Exception:
        return dj_tz.now()


def run_fetch_cycle() -> int:
    """Fetch news, filter, save new items. Returns count of new items saved."""
    from django.utils import timezone as dj_tz
    from apps.news.models import NewsItem

    two_days_ago = dj_tz.now() - timedelta(days=2)
    saved = 0

    # Rotate through queries to avoid rate limits
    import random
    queries = random.sample(GNEWS_QUERIES, min(3, len(GNEWS_QUERIES)))

    seen_titles = set(
        NewsItem.objects.filter(published_at__gte=two_days_ago)
        .values_list('title', flat=True)
    )

    for query in queries:
        articles = fetch_articles_from_gnews(query, max_results=10)
        for art in articles:
            title = art.get('title', '').strip()
            description = art.get('description', '') or ''

            if not title or title in seen_titles:
                continue
            if not is_ai_related(title, description):
                continue

            pub_at = parse_published_at(art.get('publishedAt', ''))
            if pub_at < two_days_ago:
                continue

            category = detect_category(title, description)
            importance = score_importance(title, description)
            tag = detect_tag(importance, title)

            from apps.news.models import CATEGORY_THEMES
            seeds = CATEGORY_THEMES.get(category, CATEGORY_THEMES['General AI'])['seeds']
            image_seed = seeds[saved % len(seeds)]

            NewsItem.objects.create(
                title=title,
                summary=description[:500],
                source=art.get('source', {}).get('name', ''),
                source_url=art.get('url', ''),
                category=category,
                tag=tag,
                importance=importance,
                image_seed=image_seed,
                published_at=pub_at,
            )
            seen_titles.add(title)
            saved += 1

    # Remove news older than 3 days to keep DB clean
    old_cutoff = dj_tz.now() - timedelta(days=3)
    deleted, _ = NewsItem.objects.filter(published_at__lt=old_cutoff).delete()
    if deleted:
        print(f"[Agent] Removed {deleted} expired news items")

    return saved
