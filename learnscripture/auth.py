from accounts.models import SubscriptionType
from learnscripture.datastructures import make_choices

Feature = make_choices('Feature',
                       [(1, 'CREATE_VERSE_SET', u'Create verse set'),
                        ])

def check_allowed(request, feature):
    if feature == Feature.CREATE_VERSE_SET:
        if request.identity.account_id is None:
            return (False, u"You need to create an account first to create verse sets.")

        if request.identity.account.subscription in [SubscriptionType.FREE_TRIAL,
                                                     SubscriptionType.PAID_UP,
                                                     SubscriptionType.LIFETIME_FREE]:
            return (True, u'')
        return (False, u"Your free trial or paid subscription has finished, so you cannot create or edit verse sets.")
    return (True, '')

