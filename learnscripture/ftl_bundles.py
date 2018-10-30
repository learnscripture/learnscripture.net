from django_ftl.bundles import Bundle


main = Bundle(['learnscripture/site.ftl',
               'learnscripture/dashboard.ftl',
               'learnscripture/errors.ftl',
               'learnscripture/events.ftl',
               ],
              default_locale='en',
              require_activate=True)

t = main.format
t_lazy = main.format_lazy
