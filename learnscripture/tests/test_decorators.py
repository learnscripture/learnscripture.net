import pytest
from django.http import HttpRequest, HttpResponse
from django.http.response import HttpResponseBadRequest
from django.test.client import RequestFactory

from learnscripture.decorators import exceptions_to_400


def test_exceptions_to_400_decorator(rf: RequestFactory):
    def my_view(request: HttpRequest) -> HttpResponse:
        raise ValueError("aargh!")

    request = rf.get("/")

    with pytest.raises(ValueError):
        my_view(request)

    protected_view = exceptions_to_400(ValueError)(my_view)
    response = protected_view(request)

    assert isinstance(response, HttpResponseBadRequest)
