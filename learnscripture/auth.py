from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe

from learnscripture.datastructures import make_choices
from learnscripture.utils.html import html_fragment

Feature = make_choices('Feature',
                       [(1, 'CREATE_VERSE_SET', u'Create verse set'),
                        (2, 'CREATE_GROUP', u'Create group'),
                        ])

def check_allowed(request, feature):
    need_to_signup = mark_safe(u'You need to <a href="#" class="signup-link reload-after-signup">create an account</a> or <a href="#" class="login-link reload-after-login">log in</a> to access this feature.')

    if feature in [Feature.CREATE_VERSE_SET, Feature.CREATE_GROUP]:
        if not hasattr(request, 'identity') or request.identity.account_id is None:
            return (False, need_to_signup)

    return (True, '')

