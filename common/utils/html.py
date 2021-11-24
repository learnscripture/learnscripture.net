from django.utils.html import format_html


def link(url, text, title=None):
    if title is None or title.strip() == "":
        return format_html('<a href="{0}">{1}</a>', url, text)
    else:
        return format_html('<a href="{0}" title="{1}">{2}</a>', url, title, text)
