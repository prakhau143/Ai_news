import json
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render
from .utils import get_ai_metrics, CACHE_KEY


@login_required
def ai_analysis(request):
    metrics = get_ai_metrics()
    return render(request, 'analysis/index.html', {
        'metrics_json': json.dumps(metrics),
    })


@login_required
def ai_metrics_api(request):
    """Force-refresh metrics from Claude and return JSON."""
    if request.GET.get('refresh') == '1':
        cache.delete(CACHE_KEY)
    metrics = get_ai_metrics()
    return JsonResponse(metrics)
