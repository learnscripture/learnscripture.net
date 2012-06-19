from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe

from accounts.models import SubscriptionType
from learnscripture.datastructures import make_choices
from learnscripture.utils.html import html_fragment

Feature = make_choices('Feature',
                       [(1, 'CREATE_VERSE_SET', u'Create verse set'),
                        (2, 'CREATE_GROUP', u'Create group'),
                        ])

def check_allowed(request, feature):
    need_to_signup = mark_safe(u'You need to <a href="#" class="signup-link">create an account</a> to access this feature.<span class="reload-after-signup"></span>')

    need_to_subscribe = html_fragment(u"Your free trial or paid subscription has finished, so you cannot create perform this action. You can <a href='%s'>subscribe</a> to enable this feature.",
                                      reverse('subscribe'))
    if feature in [Feature.CREATE_VERSE_SET, Feature.CREATE_GROUP]:
        if not hasattr(request, 'identity') or request.identity.account_id is None:
            return (False, need_to_signup)

        if request.identity.account.subscription in [SubscriptionType.FREE_TRIAL,
                                                     SubscriptionType.PAID_UP,
                                                     SubscriptionType.LIFETIME_FREE]:
            return (True, u'')
        return (False, need_to_subscribe)

    return (True, '')

