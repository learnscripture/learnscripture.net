from django.conf.urls import url, patterns

from learnscripture.api.handlers import VersesToLearnHandler, ActionCompleteHandler, ChangeVersionHandler, LogOutHandler, SetPreferences, SessionStats, SkipVerseHandler, CancelLearningVerseHandler, ScoreLogs, VerseFind, CheckDuplicatePassageSet, DeleteNotice, ResetProgressHandler, AndroidAppInstalled


from django.http import HttpResponse, Http404, HttpResponseNotAllowed, HttpResponseForbidden, HttpResponseServerError
from django.views.decorators.vary import vary_on_headers
from piston.emitters import Emitter
from piston.resource import CHALLENGE
from piston.resource import Resource as BaseResource
from piston.utils import HttpStatusCode, MimerDataException, translate_mime, rc
from piston.handler import typemapper

class Resource(BaseResource):
    # We need to enable CSRF protection by default, not disable
    def __init__(self, *args, **kwargs):
        super(Resource, self).__init__(*args, **kwargs)
        self.csrf_exempt = getattr(self.handler, 'csrf_exempt', False)


    # Piston's Resource does all error handling in a method error_handler.
    # However, this is a total pain in the neck for debugging, because it means
    # you can't get out a helpful stack trace. So, we have copy-pasted the whole
    # of __call__ in order to override the error handling.

    @vary_on_headers('Authorization')
    def __call__(self, request, *args, **kwargs):
        """
        NB: Sends a `Vary` header so we don't cache requests
        that are different (OAuth stuff in `Authorization` header.)
        """
        rm = request.method.upper()

        # Django's internal mechanism doesn't pick up
        # PUT request, so we trick it a little here.
        if rm == "PUT":
            coerce_put_post(request)

        actor, anonymous = self.authenticate(request, rm)

        if anonymous is CHALLENGE:
            return actor()
        else:
            handler = actor

        # Translate nested datastructs into `request.data` here.
        if rm in ('POST', 'PUT'):
            try:
                translate_mime(request)
            except MimerDataException:
                return rc.BAD_REQUEST
            if not hasattr(request, 'data'):
                if rm == 'POST':
                    request.data = request.POST
                else:
                    request.data = request.PUT

        if not rm in handler.allowed_methods:
            return HttpResponseNotAllowed(handler.allowed_methods)

        meth = getattr(handler, self.callmap.get(rm, ''), None)
        if not meth:
            raise Http404

        # Support emitter both through (?P<emitter_format>) and ?format=emitter.
        em_format = self.determine_emitter(request, *args, **kwargs)

        kwargs.pop('emitter_format', None)

        # Clean up the request object a bit, since we might
        # very well have `oauth_`-headers in there, and we
        # don't want to pass these along to the handler.
        request = self.cleanup_request(request)

        try:
            result = meth(request, *args, **kwargs)

        except Exception, e:
            # CHANGES: this bit overridden
            if isinstance(e, Http404):
                return rc.NOT_FOUND
            elif isinstance(e, HttpStatusCode):
                return e.response
            else:
                raise

        try:
            emitter, ct = Emitter.get(em_format)
            fields = handler.fields

            if hasattr(handler, 'list_fields') and isinstance(result, (list, tuple, QuerySet)):
                fields = handler.list_fields
        except ValueError:
            result = rc.BAD_REQUEST
            result.content = "Invalid output format specified '%s'." % em_format
            return result

        status_code = 200

        # If we're looking at a response object which contains non-string
        # content, then assume we should use the emitter to format that 
        # content
        if self._use_emitter(result):
            status_code = result.status_code
            # Note: We can't use result.content here because that method attempts
            # to convert the content into a string which we don't want. 
            # when _is_string is False _container is the raw data
            result = result._container
     
        srl = emitter(result, typemapper, handler, fields, anonymous)

        try:
            """
            Decide whether or not we want a generator here,
            or we just want to buffer up the entire result
            before sending it to the client. Won't matter for
            smaller datasets, but larger will have an impact.
            """
            if self.stream: stream = srl.stream_render(request)
            else: stream = srl.render(request)

            if not isinstance(stream, HttpResponse):
                resp = HttpResponse(stream, mimetype=ct, status=status_code)
            else:
                resp = stream

            resp.streaming = self.stream

            return resp
        except HttpStatusCode, e:
            return e.response

# These URLs are hardcoded into Javascript instead of using URL reversing
# somehow. That's OK, because if you want to change them, you should be adding
# to them first for the sake of Javascript that is already loaded into the
# browser, and then only remove the old one when you are sure no javascript will
# try to use it.
urlpatterns = patterns('',
                       url(r'^versestolearn/$', Resource(VersesToLearnHandler)),
                       url(r'^actioncomplete/$', Resource(ActionCompleteHandler)),
                       url(r'^changeversion/$', Resource(ChangeVersionHandler)),
                       url(r'^logout/$', Resource(LogOutHandler)),
                       url(r'^setpreferences/$', Resource(SetPreferences)),
                       url(r'^sessionstats/$', Resource(SessionStats)),
                       url(r'^skipverse/$', Resource(SkipVerseHandler)),
                       url(r'^cancellearningverse/$', Resource(CancelLearningVerseHandler)),
                       url(r'^resetprogress/$', Resource(ResetProgressHandler)),
                       url(r'^scorelogs/$', Resource(ScoreLogs)),
                       url(r'^versefind/$', Resource(VerseFind)),
                       url(r'^checkduplicatepassageset/$', Resource(CheckDuplicatePassageSet)),
                       url(r'^deletenotice/$', Resource(DeleteNotice)),
                       url(r'^androidappinstalled/$', Resource(AndroidAppInstalled)),
                       )

