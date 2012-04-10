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

    return {'signup_form': lambda: SignUpForm(prefix="signup"),
            'login_form': lambda: LogInForm(prefix="login"),
            'preferences_form': lambda: PreferencesForm(instance=request.identity
                                                        if hasattr(request, 'identity')
                                                        else None),
            }

def referral_links(request):
    def mk_referral_link():
        if not hasattr(request, 'identity'):
            return None
        identity = request.identity
        if identity.account is None:
            return None
        return identity.account.make_referral_link(request.build_absolute_uri())

    return {'referral_link': mk_referral_link}


class MenuItem(object):
    def __init__(self, caption=None, path=None, active=None):
        self.caption = caption
        self.path = path
        self.active = active

def menu(request):
    items = [
        MenuItem('Dashboard', reverse('dashboard')),
        MenuItem('Learn', reverse('learn')),
        MenuItem('About', '/about/'),
        MenuItem('Contact', '/contact/'),
        ]
    for m in items:
        m.active = request.path_info.startswith(m.path)
    return {'menuitems': items}



lazy_page_info = lazy_dict(page_info, ['fiber_page', 'fiber_current_pages'])
