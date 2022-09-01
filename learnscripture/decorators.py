from typing import Optional

from django.http import HttpResponseRedirect
from django.http.response import HttpResponse
from django.shortcuts import render
from django.utils.cache import add_never_cache_headers
from django.utils.decorators import method_decorator
from django.utils.functional import wraps
from render_block import render_block_to_string

from learnscripture import session
from learnscripture.ftl_bundles import t

from .utils.urls import build_preferences_url


def require_identity(view_func):
    """
    Creates an identity if there is no identity active
    """

    @wraps(view_func)
    def view(request, *args, **kwargs):
        # Assumes IdentityMiddleware
        if not hasattr(request, "identity"):
            identity = session.start_identity(request)
            request.identity = identity
        return view_func(request, *args, **kwargs)

    return view


require_identity_method = method_decorator(require_identity)


def has_preferences(request):
    identity = getattr(request, "identity", None)
    if identity is None:
        return False
    return identity.preferences_setup


def redirect_via_prefs(request):
    return HttpResponseRedirect(build_preferences_url(request))


def require_preferences(view_func):
    @wraps(view_func)
    def view(request, *args, **kwargs):
        if not has_preferences(request):
            return redirect_via_prefs(request)
        return view_func(request, *args, **kwargs)

    return view


def require_account(view_func):
    """
    Redirects to / if there is no account active
    """
    # NB this doesn't create an account.
    @wraps(view_func)
    def view(request, *args, **kwargs):
        if not hasattr(request, "identity") or request.identity.account_id is None:
            return HttpResponseRedirect("/")
        return view_func(request, *args, **kwargs)

    return view


def require_account_with_redirect(view_func):
    """
    If there is no current account, show a page with links
    for logging in or creating an account.
    """

    @wraps(view_func)
    def view(request, *args, **kwargs):
        if not hasattr(request, "identity") or request.identity.account_id is None:
            response = render(
                request,
                "learnscripture/login_and_redirect.html",
                {
                    "title": t("accounts-login-title"),
                },
            )
            add_never_cache_headers(response)
            return response
        return view_func(request, *args, **kwargs)

    return view


def for_htmx(*, if_hx_target: Optional[str] = None, template: Optional[str] = None, block: Optional[str] = None):
    """
    If the request is from htmx, then render a partial page, using the supplied
    template name.

    If the optional `if_target` parameter is supplied, the
    hx-target header must match the supplied value as well.
    """
    if block and template:
        raise ValueError("Pass only one of 'template' and 'block'")
    if not (block or template):
        raise ValueError("You must pass one of 'template' and 'block'")

    def decorator(view):
        @wraps(view)
        def _view(request, *args, **kwargs):
            resp = view(request, *args, **kwargs)
            if request.headers.get("Hx-Request", False):
                if if_hx_target is None or request.headers.get("Hx-Target", None) == if_hx_target:
                    if not hasattr(resp, "render"):
                        raise ValueError("Cannot modify a response that isn't a TemplateResponse")
                    if resp.is_rendered:
                        raise ValueError("Cannot modify a response that has already been rendered")

                    if template is not None:
                        resp.template_name = template
                    elif block is not None:
                        rendered_block = render_block_to_string(
                            resp.template_name, block, context=resp.context_data, request=request
                        )
                        # Create new simple HttpResponse as replacement
                        resp = HttpResponse(content=rendered_block, status=resp.status_code, headers=resp.headers)

            return resp

        return _view

    return decorator
