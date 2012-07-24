from collections import namedtuple

from django.core.urlresolvers import reverse
from django.utils import timezone
from fiber.context_processors import page_info

from accounts.forms import PreferencesForm
from accounts.models import DEFAULT_THEME, THEME_FONTS
from learnscripture.utils.context import lazy_dict
from .forms import SignUpForm, LogInForm

NOTICES_EXPIRE_AFTER_DAYS = 3

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
        MenuItem('Choose', reverse('choose')),
        MenuItem('About', '/about/'),
        MenuItem('Contact', '/contact/'),
        ]
    for m in items:
        m.active = request.path_info.startswith(m.path)
    return {'menuitems': items}



lazy_page_info = lazy_dict(page_info, ['fiber_page', 'fiber_current_pages'])

def notices(request):
    # Layer of laziness to avoid expiring notices unless actually rendered
    def get_and_mark_notices():
        l = []
        for notice in request.identity.notices.all().order_by('created'):
            if notice.seen is None:
                notice.seen = timezone.now()
                notice.save()
            elif (timezone.now() - notice.seen).days > NOTICES_EXPIRE_AFTER_DAYS:
                notice.delete()
                notice = None
            if notice is not None:
                l.append(notice)
        return l

    if hasattr(request, 'identity'):
        return {'notices': get_and_mark_notices}
    else:
        return {}


def campaign_context_processor(account):
    return {'account': account}


def theme_fonts(request):
    current_theme = DEFAULT_THEME
    if hasattr(request, 'identity'):
        current_theme = request.identity.interface_theme
    return {'theme_fonts': THEME_FONTS,
            'current_theme': current_theme,
            }
