from django.urls import reverse
from furl import furl


def get_next_url_for_request(request):
    """
    Intelligently get the next URL to return to (after a login/signup or similar action)
    Return None if there isn't one
    """
    if request is None:
        return None

    # - Sometimes we don't to return "back here"
    # - But not if "here" is somewhere not very useful, like the login page
    # - Want to propagate an existing "next", which is important
    #   to avoid an infinite stream of new /signup/ URLs when this code
    #   is called from the /signup/ page itself.

    if "next" in request.GET:
        return request.GET["next"]
    else:
        # For partials responding to htmx requests, we should use
        # the browser URL, not the request URL, which conveniently
        # if passed in HX-Current-URL
        if hx_current_url := request.headers.get("HX-Current-URL", None):
            current_full_url = furl(hx_current_url).path
        else:
            current_full_url = request.get_full_path()
        current_path = furl(current_full_url).path

        if str(current_path) not in [
            reverse(url_name)
            for url_name in [
                "signup",
                "login",
                "preferences",
            ]
        ]:
            return current_full_url
    return None


def build_signup_url(request):
    return build_url_generic(request, "signup")


def build_login_url(request):
    return build_url_generic(request, "login")


def build_preferences_url(request):
    return build_url_generic(request, "preferences")


def build_url_generic(request, view_name):
    base_furl = furl(reverse(view_name))
    next_url = get_next_url_for_request(request)
    if next_url:
        base_furl.args["next"] = next_url
    return str(base_furl)
