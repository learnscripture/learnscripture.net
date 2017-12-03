from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from accounts.forms import PreferencesForm
from accounts.models import DEFAULT_THEME, THEME_FONTS
from learnscripture.models import SiteNotice
from learnscripture.views import account_from_request
from payments.models import DonationDrive

NOTICES_EXPIRE_AFTER_DAYS = 3


def memoize_nullary(f):
    """
    Memoizes a function that takes no arguments.  The memoization lasts only as
    long as we hold a reference to the return value.
    """
    def func():
        if not hasattr(func, 'retval'):
            func.retval = f()
        return func.retval
    return func


def session_forms(request):
    # Use callables here to avoid overhead when not needed.  The template will
    # call them when used

    return {
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

    return {'referral_link': memoize_nullary(mk_referral_link)}


class MenuItem(object):
    def __init__(self, caption=None, path=None, active=None):
        self.caption = caption
        self.path = path
        self.active = active


def menu(request):
    identity = getattr(request, 'identity', None)
    items = [
        MenuItem('Choose', reverse('choose')),
        MenuItem('Help', '/help/')
        if identity is not None and identity.default_to_dashboard
        else MenuItem('About', '/about/'),
        MenuItem('Contact', '/contact/'),
    ]
    for m in items:
        m.active = request.path_info.startswith(m.path)
    return {'menuitems': items}


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

    retval = {'site_notices': memoize_nullary(SiteNotice.objects.current)}

    if hasattr(request, 'identity'):
        retval['notices'] = memoize_nullary(get_and_mark_notices)

        if request.identity.account is not None:
            retval['donation_drives'] = memoize_nullary(lambda: DonationDrive.objects.current_for_account(request.identity.account))

    return retval


def request_account(request):
    return {'request_account': account_from_request(request)}


def campaign_context_processor(account):
    return {'account': account}


def themes(request):
    current_theme = DEFAULT_THEME
    if hasattr(request, 'identity'):
        current_theme = request.identity.interface_theme
    return {'theme_fonts': THEME_FONTS,
            'current_theme': current_theme,
            }


def settings_processor(request):
    return {'settings': {'SENTRY_DSN': settings.SENTRY_DSN,
                         'GOOGLE_ANALYTICS_ACCOUNT': settings.GOOGLE_ANALYTICS_ACCOUNT,
                         }}
