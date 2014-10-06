from datetime import datetime
import os
import time

from django.utils import timezone
from django.conf import settings
from django.core.urlresolvers import resolve, Resolver404

from app_metrics.utils import metric

class IdentityMiddleware(object):
    def process_request(self, request):
        from learnscripture import session

        identity = session.get_identity(request)
        if identity is not None:
            request.identity = identity

        session.save_referrer(request)


class TokenLoginMiddleware(object):
    """
    Do login if there is a valid token in request.GET['t'].

    This enables us to send people emails that have URLs allowing them to log in
    automatically.
    """
    def process_request(self, request):
        from learnscripture import session
        from accounts.models import Account
        from accounts.tokens import check_login_token
        token = request.GET.get('t', None)
        if token is None:
            return
        account_name = check_login_token(token)
        if account_name is None:
            return
        try:
            account = Account.objects.get(username=account_name)
        except Account.DoesNotExist:
            return

        # Success, fake a log in:
        session.login(request, account.identity)
        # Need to do django.contrib.auth login for the sake of some views that
        # look for request.user (e.g. password change).
        from django.contrib.auth import login
        # Need to frig it because we are not going to call authenticate.
        account.backend = settings.AUTHENTICATION_BACKENDS[0]
        login(request, account)


class StatsMiddleware(object):
    def process_request(self, request):
        metric('request_all')
        accept = request.environ.get('HTTP_ACCEPT', '')
        if accept.startswith('application/json'):
            metric('request_json')
        elif accept.startswith('text/html'):
            metric('request_html')


class DebugMiddleware(object):
    def process_request(self, request):
        from learnscripture import session
        from accounts.models import Account

        if 'sleep' in request.GET:
            time.sleep(int(request.GET['sleep']))


        if 'as' in request.GET:
            session.set_identity(request.session, Account.objects.get(username=request.GET['as']).identity)

        if 'now' in request.GET:
            now = time.strptime(request.GET['now'], "%Y-%m-%d %H:%M:%S")
            now_ts = time.mktime(now)
            now_dt = datetime.fromtimestamp(now_ts).replace(tzinfo=timezone.utc)
            time.time = lambda: now_ts

            # We can't monkeypatch datetime, but we always use timezone.now so
            # monkeypatch that instead
            timezone.now = lambda: now_dt


class PaypalDebugMiddleware(object):
    def process_request(self, request):
        if 'paypal/ipn/' in request.path:
            open(os.path.join(os.environ['HOME'],
                              'learnscripture-paypal-request-%s' %
                              datetime.now().isoformat()),
                 'wb').write(request.META.get('CONTENT_TYPE', '') + '\n\n' + request.body)

LEARNING_VIEWS = [
    'dashboard',
    'learn',
    'learnscripture.api.versestolearn',
    'learnscripture.api.actioncomplete',
    'learnscripture.api.skipverse',
    'learnscripture.api.cancellearningverse',
    'learnscripture.api.cancellearningpassage',
    'learnscripture.api.resetprogress',
    ]

class TrackingMiddleware(object):
    def process_response(self, request, response):
        identity = getattr(request, 'identity', None)
        if identity is not None and identity.track_learning:
            try:
                match = resolve(request.path)
            except Resolver404:
                return response
            if match.view_name in LEARNING_VIEWS:
                from tracking.models import HttpLog
                try:
                    HttpLog.log_request_response(request, response)
                except:
                    pass # Don't take down process if we can't log
        return response
