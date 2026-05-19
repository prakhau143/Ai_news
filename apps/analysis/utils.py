"""
Fetch AI model metrics from Claude API every 6 hours.
Falls back to hardcoded baseline data when API is unavailable.
"""
import json
from django.conf import settings
from django.core.cache import cache

CACHE_KEY = 'ai_model_metrics'
CACHE_TTL = 6 * 60 * 60   # 6 hours

BASELINE_DATA = {
    "models": [
        {
            "name": "GPT-4o",
            "quality_index": 88,
            "price_per_1m_tokens": 5.0,
            "thinking_score": 9.0,
            "coding_score": 9.2,
            "design_score": 7.5,
            "conversation_score": 9.0,
            "accuracy": 87,
            "latency_ms": 1200,
        },
        {
            "name": "Claude 3.5 Sonnet",
            "quality_index": 92,
            "price_per_1m_tokens": 3.0,
            "thinking_score": 9.5,
            "coding_score": 9.6,
            "design_score": 8.2,
            "conversation_score": 9.4,
            "accuracy": 91,
            "latency_ms": 900,
        },
        {
            "name": "Gemini 1.5 Pro",
            "quality_index": 83,
            "price_per_1m_tokens": 3.5,
            "thinking_score": 8.5,
            "coding_score": 8.4,
            "design_score": 8.0,
            "conversation_score": 8.8,
            "accuracy": 84,
            "latency_ms": 1400,
        },
        {
            "name": "DeepSeek V3",
            "quality_index": 85,
            "price_per_1m_tokens": 0.27,
            "thinking_score": 9.0,
            "coding_score": 9.1,
            "design_score": 7.2,
            "conversation_score": 8.5,
            "accuracy": 85,
            "latency_ms": 1100,
        },
        {
            "name": "Llama 3.1 405B",
            "quality_index": 79,
            "price_per_1m_tokens": 1.0,
            "thinking_score": 8.2,
            "coding_score": 8.5,
            "design_score": 7.0,
            "conversation_score": 8.2,
            "accuracy": 80,
            "latency_ms": 1600,
        },
    ]
}


def get_ai_metrics() -> dict:
    """Return metrics from cache, or fetch fresh from Claude, or use baseline."""
    cached = cache.get(CACHE_KEY)
    if cached:
        return cached

    fresh = _fetch_from_claude()
    if fresh:
        cache.set(CACHE_KEY, fresh, CACHE_TTL)
        return fresh

    cache.set(CACHE_KEY, BASELINE_DATA, CACHE_TTL)
    return BASELINE_DATA


def _fetch_from_claude():
    api_key = settings.ANTHROPIC_API_KEY
    if not api_key:
        return None

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        prompt = (
            "Analyze the latest AI models and return ONLY valid JSON with no extra text.\n"
            "Return this exact structure:\n"
            '{"models": [{"name": "...", "quality_index": 0-100, '
            '"price_per_1m_tokens": float, "thinking_score": 0-10, '
            '"coding_score": 0-10, "design_score": 0-10, '
            '"conversation_score": 0-10, "accuracy": 0-100, "latency_ms": int}]}\n\n'
            "Models to include: GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro, DeepSeek V3, Llama 3.1 405B.\n"
            "Use the most current publicly available benchmark data."
        )
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()
        # Strip markdown code fences if present
        if text.startswith('```'):
            text = text.split('```')[1]
            if text.startswith('json'):
                text = text[4:]
        return json.loads(text)
    except Exception as e:
        print(f"[Analysis] Claude fetch failed: {e}")
        return None
