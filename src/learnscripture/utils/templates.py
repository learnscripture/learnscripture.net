from django.template import loader


def render_to_string_ftl(template_name, context, request=None):
    from learnscripture.context_processors import ftl

    c = context.copy()
    c.update(ftl(None))
    return loader.render_to_string(template_name, c, request=request)
