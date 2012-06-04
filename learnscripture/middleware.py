from app_metrics.utils import metric

class IdentityMiddleware(object):
    def process_request(self, request):
        from learnscripture import session

        identity = session.get_identity(request)
        if identity is not None:
            request.identity = identity

        session.save_referrer(request)


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
            import time
            time.sleep(int(request.GET['sleep']))


        if 'as' in request.GET:
            session.set_identity(request, Account.objects.get(username=request.GET['as']).identity)

        if 'now' in request.GET:
            import time
            from datetime import datetime
            from django.utils import timezone
            now = time.strptime(request.GET['now'], "%Y-%m-%d %H:%M:%S")
            now_ts = time.mktime(now)
            now_dt = datetime.fromtimestamp(now_ts).replace(tzinfo=timezone.utc)
            time.time = lambda: now_ts

            # We can't monkeypatch datetime, but we always use timezone.now so
            # monkeypatch that instead
            timezone.now = lambda: now_dt
