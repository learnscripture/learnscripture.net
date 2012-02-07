from learnscripture import session

class IdentityMiddleware(object):
    def process_request(self, request):
        identity = session.get_identity(request)
        if identity is not None:
            request.identity = identity
