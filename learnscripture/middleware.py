import os
import time
import urllib.parse
from datetime import datetime
from importlib import import_module

from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.utils import translation as gettext_translation
from django.utils.http import urlencode
from django.utils.translation import LANGUAGE_SESSION_KEY
from django_ftl import override


def identity_middleware(get_response):
    from learnscripture import session

    def middleware(request):

        identity = session.get_identity(request)
        if identity is not None:
            request.identity = identity

        session.save_referrer(request)
        return get_response(request)
    return middleware


def activate_language_from_request(get_response):
    # Similar to django_ftl.middleware.activate_from_request_session, but with our defaults
    def middleware(request):
        identity = getattr(request, 'identity', None)
        if identity is not None:
            language_code = identity.interface_language
        else:
            language_code = request.session.get(LANGUAGE_SESSION_KEY, settings.LANGUAGE_CODE)
        request.LANGUAGE_CODE = language_code
        with override(language_code, deactivate=True):
            # For some things, e.g. 'timeuntil' templatetag, it is useful to
            # have gettext translation available as well, at least
            # until we have a replacement.
            gettext_translation.activate(language_code)
            retval = get_response(request)
            return retval

    return middleware


def token_login_middleware(get_response):
    """
    Do login if there is a valid token in request.GET['t'].

    This enables us to send people emails that have URLs allowing them to log in
    automatically.
    """
    from accounts.models import Account
    from accounts.tokens import check_login_token
    from learnscripture import session

    def middleware(request):
        token = request.GET.get('t', None)
        if token is None:
            return get_response(request)
        account_name = check_login_token(token)
        if account_name is None:
            return get_response(request)
        try:
            account = Account.objects.get(username=account_name)
        except Account.DoesNotExist:
            return get_response(request)

        # Success, do a log in:
        session.login(request, account.identity)

        # Redirect to hide access token
        d = request.GET.copy()
        del d['t']
        url = urllib.parse.urlunparse(('', '', request.path, '', d.urlencode(), ''))
        return HttpResponseRedirect(url)

    return middleware


def pwa_tracker_middleware(get_response):
    def middleware(request):
        if 'fromhomescreen' in request.GET and 'fromhomescreen' not in request.session:
            request.session['fromhomescreen'] = '1'
        return get_response(request)
    return middleware


def feature_flipper_middleware(get_response):
    def middleware(request):
        try:
            request.i18n_options_enabled = request.identity.i18n_options_enabled
        except AttributeError:
            request.i18n_options_enabled = False
        return get_response(request)
    return middleware


def debug_middleware(get_response):
    from learnscripture import session
    from accounts.models import Account

    def middleware(request):
        if 'sleep' in request.GET:
            time.sleep(int(request.GET['sleep']))

        if 'as' in request.GET:
            account = Account.objects.get(username=request.GET['as'])
            session.login(request, account.identity)
            params = request.GET.copy()
            del params['as']
            query = urlencode(params, doseq=True)
            return HttpResponseRedirect(request.path + ("?" + query if query else ""))

        if 'as_session' in request.GET:
            session_key = request.GET['as_session']
            engine = import_module(settings.SESSION_ENGINE)
            request.session = engine.SessionStore(session_key)
            request.session.accessed = True
            request.session.modified = True
            params = request.GET.copy()
            del params['as_session']
            query = urlencode(params, doseq=True)
            return HttpResponseRedirect(request.path + ("?" + query if query else ""))

        if 'now' in request.GET:
            now = time.strptime(request.GET['now'], "%Y-%m-%d %H:%M:%S")
            now_ts = time.mktime(now)
            now_dt = datetime.fromtimestamp(now_ts).replace(tzinfo=timezone.utc)
            time.time = lambda: now_ts

            # We can't monkeypatch datetime, but we always use timezone.now so
            # monkeypatch that instead
            timezone.now = lambda: now_dt

        return get_response(request)

    return middleware


def paypal_debug_middleware(get_response):
    def middleware(request):
        if 'paypal/ipn/' in request.path:
            open(os.path.join(os.environ['HOME'],
                              'learnscripture-paypal-request-%s' %
                              datetime.now().isoformat()),
                 'wb').write(request.META.get('CONTENT_TYPE', '') + '\n\n' + request.body)

        return get_response(request)
    return middleware
