import os.path
import sys

from django_ftl import activate
from django_ftl.bundles import Bundle

main = Bundle([
    'learnscripture/accounts.ftl',
    'learnscripture/activity.ftl',
    'learnscripture/awards.ftl',
    'learnscripture/bibleverses.ftl',
    'learnscripture/catechisms.ftl',
    'learnscripture/choose.ftl',
    'learnscripture/comments.ftl',
    'learnscripture/contact-form.ftl',
    'learnscripture/dashboard.ftl',
    'learnscripture/donations.ftl',
    'learnscripture/emails.ftl',
    'learnscripture/errors.ftl',
    'learnscripture/events.ftl',
    'learnscripture/forms.ftl',
    'learnscripture/groups.ftl',
    'learnscripture/home.ftl',
    'learnscripture/leaderboards.ftl',
    'learnscripture/learn.ftl',
    'learnscripture/lists.ftl',
    'learnscripture/login.ftl',
    'learnscripture/pagination.ftl',
    'learnscripture/referrals.ftl',
    'learnscripture/site.ftl',
    'learnscripture/stats.ftl',
    'learnscripture/terms-of-service.ftl',
    'learnscripture/user-stats.ftl',
    'learnscripture/user-verse-sets.ftl',
    'learnscripture/user-verses.ftl',
    'learnscripture/versesets.ftl',
],
    default_locale='en',
    use_isolating=False,
    require_activate=True)


t = main.format
t_lazy = main.format_lazy


if any(os.path.split(arg)[-1] == 'manage.py' for arg in sys.argv) and (
        'makemigrations' in sys.argv or 'migrate' in sys.argv):
    activate('en')
