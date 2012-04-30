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
