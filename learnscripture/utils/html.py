from django.utils.html import escape
from django.utils.safestring import mark_safe, SafeData


def html_fragment(template, *args):
    return mark_safe(template % tuple([val if isinstance(val, SafeData)
                                       else escape(val)
                                       for val in args]))
