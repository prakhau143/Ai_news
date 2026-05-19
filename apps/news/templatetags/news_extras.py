import json
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def tojson(value):
    """Safely serialize a Python value to a JSON string for use in JS."""
    return mark_safe(json.dumps(str(value) if not isinstance(value, (dict, list, int, float, bool)) else value))

@register.simple_tag(takes_context=True)
def active_nav(context, url_name):
    request = context.get('request')
    if request and request.resolver_match.url_name == url_name:
        return 'active'
    return ''
