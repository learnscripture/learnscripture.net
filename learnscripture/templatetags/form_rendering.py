from django import template
from django.template.loader import get_template

register = template.Library()


@register.filter
def render_form(element):
    return get_template("learnscripture/form_rendering/form.html").render({'form': element})


@register.filter
def render_field(element):
    return get_template("learnscripture/form_rendering/field.html").render({'field': element})


@register.filter
def is_checkbox(field):
    return field.field.widget.__class__.__name__.lower() == "checkboxinput"


@register.filter
def is_radiobutton(field):
    return field.field.widget.__class__.__name__.lower() == "radioselect"
