#!/home/cciw/webapps/learnscripture_django/venv/bin/python
import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'learnscripture.settings'
import django
django.setup()


def main(email_file):
    import raven.contrib.django.raven_compat
    sentry_client = raven.contrib.django.raven_compat.DjangoClient()
    from accounts.email_reminders import handle_bounce
    try:
        handle_bounce(email_file)
    except:
        sentry_client.captureException()

if __name__ == '__main__':
    main(sys.stdin)
