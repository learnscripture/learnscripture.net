from django.template import Library

register = Library()


@register.filter
def lookup(dictionary, key):
    return dictionary[key]
