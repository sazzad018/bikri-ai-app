from django import template
from django.utils.timesince import timesince

register = template.Library()

@register.filter
def replace(value, arg):
    args = arg.split(",")
    if len(args) < 2:
        raise ValueError("replace filter requires two arguments separated by a comma")
    return value.replace(args[0], args[1])

@register.filter
def split(value, arg):
    if type(value) == str:
        return value.split(arg)
    raise TypeError("Input must be a string")
