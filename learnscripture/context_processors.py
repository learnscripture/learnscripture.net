from collections import namedtuple

from django.core.urlresolvers import reverse
from fiber.context_processors import page_info

from accounts.forms import PreferencesForm
from learnscripture.utils.context import lazy_dict
from .forms import SignUpForm, LogInForm


def session_forms(request):
    # Use callables here to avoid overhead when not needed.  The template will
    # call them when used

    # We need different prefices on each form to avoid clashes with ids of
    # fields. Same prefix must be set in handlers.py

    def signup_form():
        return SignUpForm(prefix="signup")

    def login_form():
        return LogInForm(prefix="login")

    def preferences_form():
        if hasattr(request, 'identity'):
            instance = request.identity
        else:
            instance = None

        return PreferencesForm(instance=instance)

    return {'signup_form': signup_form,
            'login_form': login_form,
            'preferences_form': preferences_form,
            }

class MenuItem(object):
    def __init__(self, caption=None, path=None, active=None):
        self.caption = caption
        self.path = path
        self.active = active

def menu(request):
    items = [
        MenuItem('Dashboard', reverse('start')),
        MenuItem('Learn', reverse('learn')),
        MenuItem('About', '/about/'),
        MenuItem('Contact', '/contact/'),
        ]
    for m in items:
        m.active = request.path_info.startswith(m.path)
    return {'menuitems': items}



lazy_page_info = lazy_dict(page_info, ['fiber_page', 'fiber_current_pages'])
