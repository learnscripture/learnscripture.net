from django.template import loader

from learnscripture.context_processors import ftl


def render_to_string_ftl(template_name, context):
    c = context.copy()
    c.update(ftl(None))
    return loader.render_to_string(template_name, c)
