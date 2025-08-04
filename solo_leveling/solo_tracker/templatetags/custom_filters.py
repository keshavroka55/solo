from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    return float(value) * float(arg)

@register.filter
def div(value, arg):
    try:
        return float(value) / float(arg)
    except ZeroDivisionError:
        return 0
