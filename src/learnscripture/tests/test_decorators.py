import pytest
from django.core.exceptions import BadRequest
from django.http import HttpRequest, HttpResponse
from django.test.client import RequestFactory

from learnscripture.decorators import exceptions_to_400


def test_exceptions_to_400_decorator(rf: RequestFactory):
    def my_view(request: HttpRequest) -> HttpResponse:
        raise ValueError("aargh!")

    request = rf.get("/")

    with pytest.raises(ValueError):
        my_view(request)

    protected_view = exceptions_to_400(ValueError)(my_view)

    with pytest.raises(BadRequest):
        protected_view(request)
