from django_ftl.bundles import Bundle


main = Bundle(['learnscripture/main.ftl'],
              default_locale='en',
              require_activate=True)
