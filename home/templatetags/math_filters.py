from django import template

register = template.Library()

@register.filter
def subtract(value, arg):
    """減法過濾器"""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return 0 