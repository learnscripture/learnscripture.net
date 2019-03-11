from django.template import Library
from django.utils.html import escape, mark_safe

register = Library()


@register.filter
def html_format_text(verse):
    # Convert highlighted_text to HTML
    if hasattr(verse, 'highlighted_text'):
        # Search results can have this attribute
        t = verse.highlighted_text
    else:
        t = verse.text
    bits = t.split('**')
    out = []
    in_bold = False
    for b in bits:
        html = escape(b)
        if in_bold:
            html = '<b>' + html + '</b>'
        out.append(html)
        in_bold = not in_bold
    return mark_safe(''.join(out).replace('\n', '<br>'))
