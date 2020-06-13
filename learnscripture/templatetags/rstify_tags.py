from django import template
from django.utils.encoding import force_text, smart_str
from django.utils.safestring import mark_safe
from docutils.core import publish_parts
from docutils.writers import html4css1

register = template.Library()


class TextutilsHTMLWriter(html4css1.Writer):
    def __init__(self):
        html4css1.Writer.__init__(self)
        self.translator_class = TextutilsHTMLTranslator


class TextutilsHTMLTranslator(html4css1.HTMLTranslator):

    def __init__(self, document):
        html4css1.HTMLTranslator.__init__(self, document)

    def visit_admonition(self, node, name=''):
        self.body.append(self.starttag(
            node, 'div', CLASS=(name or 'admonition')))
        self.set_first_last(node)

    def visit_footnote(self, node):
        self.body.append(self.starttag(node, 'p', CLASS='footnote'))
        self.footnote_backrefs(node)

    def depart_footnote(self, node):
        self.body.append('</p>\n')

    def visit_label(self, node):
        self.body.append(self.starttag(node, 'strong', f'[{self.context.pop()}',
                                       CLASS='label'))

    def depart_label(self, node):
        self.body.append(f'</a>]</strong> {self.context.pop()}')


def rstify(text,
           initial_header_level=1,
           language_code='en',
           settings_overrides=None,
           writer_overrides=TextutilsHTMLWriter):

    settings = {
        'initial_header_level': initial_header_level,
        'doctitle_xform': False,
        'language_code': language_code,
        'footnote_references': 'superscript',
        'trim_footnote_reference_space': True,
        'default_reference_context': 'view',
        'link_base': '',
    }

    # Import user settings and overwrite default ones
    user_settings = getattr(settings, "RESTRUCTUREDTEXT_FILTER_SETTINGS", {})
    settings.update(user_settings)

    parts = publish_parts(
        source=smart_str(text),
        writer=writer_overrides(),
        settings_overrides=settings
    )

    return force_text(parts['body'])


@register.filter(name='rstify')
def do_rstify(text, initial_header_level=1):
    return mark_safe(rstify(text, initial_header_level=int(initial_header_level)))
