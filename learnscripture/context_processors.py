from .forms import SignUpForm, LogInForm

def session_forms(request):
    # Use callables here to avoid overhead when not needed.  The template will
    # call them when used

    # We need different prefices on each form to avoid clashes with ids of
    # fields. Same prefix must be set in handlers.py

    def signup_form():
        return SignUpForm(prefix="signup")

    def login_form():
        return LogInForm(prefix="login")

    return {'signup_form': signup_form,
            'login_form': login_form}
