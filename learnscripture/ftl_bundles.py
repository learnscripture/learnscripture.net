import os.path
import sys

from django_ftl import activate
from django_ftl.bundles import Bundle

main = Bundle(['learnscripture/site.ftl',
               'learnscripture/dashboard.ftl',
               'learnscripture/errors.ftl',
               'learnscripture/events.ftl',
               'learnscripture/accounts.ftl',
               'learnscripture/emails.ftl',
               'learnscripture/stats.ftl',
               'learnscripture/awards.ftl',
               'learnscripture/versesets.ftl',
               'learnscripture/bibleverses.ftl',
               'learnscripture/forms.ftl',
               ],
              default_locale='en',
              use_isolating=False,
              require_activate=True)


t = main.format
t_lazy = main.format_lazy


if any(os.path.split(arg)[-1] == 'manage.py' for arg in sys.argv) and 'makemigrations' in sys.argv:
    activate('en')
