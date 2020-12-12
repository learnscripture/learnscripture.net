from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django_ftl.templatetags import ftl as ftl_tags

from accounts.forms import PreferencesForm
from accounts.models import DEFAULT_THEME, THEME_FONTS
from bibleverses.languages import DEFAULT_LANGUAGE
from learnscripture.ftl_bundles import main as main_bundle
from learnscripture.ftl_bundles import t
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
        MenuItem(t('site-nav-choose'), reverse('choose')),
        MenuItem(t('site-nav-help'), '/help/')
        if identity is not None and identity.default_to_dashboard
        else MenuItem(t('site-nav-about'), '/about/'),
        MenuItem(t('site-nav-contact'), '/contact/'),
    ]
    for m in items:
        m.active = request.path_info.startswith(m.path)
    return {'menuitems': items}


def notices(request):
    # Layer of laziness to avoid expiring notices unless actually rendered
    def get_and_mark_notices():
        notices = []
        for notice in request.identity.notices.all().order_by('created'):
            if notice.seen is None:
                notice.seen = timezone.now()
                notice.save()
            elif (timezone.now() - notice.seen).days > NOTICES_EXPIRE_AFTER_DAYS:
                notice.delete()
                notice = None
            if notice is not None:
                notices.append(notice)
        return notices

    def get_site_notices():
        if hasattr(request, 'identity'):
            default_language_code = request.identity.default_language_code
        else:
            default_language_code = DEFAULT_LANGUAGE.code
        return SiteNotice.objects.current(default_language_code)

    retval = {'site_notices': memoize_nullary(get_site_notices)}

    if hasattr(request, 'identity'):
        retval['notices'] = memoize_nullary(get_and_mark_notices)

        if request.identity.account is not None:
            retval['donation_drives'] = memoize_nullary(lambda: DonationDrive.objects.current_for_account(request.identity.account))

    return retval


def request_account(request):
    account = account_from_request(request)
    # Everywhere we need request_account we might also need default_language_code
    if hasattr(request, 'identity'):
        default_language_code = request.identity.default_language_code
    else:
        default_language_code = DEFAULT_LANGUAGE.code
    return {
        'request_account': account,
        'default_language_code': default_language_code
    }


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
                         }}


def ftl(request):
    return {
        ftl_tags.MODE_VAR_NAME: 'server',
        ftl_tags.BUNDLE_VAR_NAME: main_bundle,
    }


def indexing(request):
    retval = {}
    if 'p' in request.GET or 'from_item' in request.GET:
        # For paginated or HTMX paginated pages, we want target items to be
        # indexed, but the boring (or possibly partial) list of items should not
        # be indexed.
        retval['noindex_but_follow'] = True
    return retval
