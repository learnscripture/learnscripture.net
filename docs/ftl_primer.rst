Fluent primer
#############

This page is for translators who help with LearnScripture.net and is an
introduction to ``Fluent``, the system we use for ‘internationalizing and
localizing’ LearnScripture.net.

The overall process for translating LearnScripture.net looks like this:

1. Developers prepare 'FTL' files containing all the parts of the website that
   need to be translated. ‘FTL’ means “Fluent Translation List”.

2. Developers send the English version of these files to translators, or share
   them in some other way that allows editing using an online editor.

3. The translator translates the English strings, saves the files and sends
   them back to the developers.


FTL file format
===============

A ‘Fluent Translation List’ file consists of 3 main things:

* Comments - these start with ``#`` and are explanations for the benefit of the
  translator. They do not need to be translated.

* Message IDs - these are words separated by hyphens and are used to identifier
  a particular bit of text. They must not be changed.

* Message body - the actual text to be translated.


Example::

    ### Learn page:

    # Page title
    learn-page-title = Learn


    ## Navbar:

    # Link that takes the user back to the dashboard
    learn-dashboard-link = Dashboard


Here ``### Learn page`` is a comment that applies to the whole of the file --
all the messages that follow are found on the ‘Learn’ page.

After that we have ``# Page title``, a comment which describes the following
message. That message consists of the message ID ``learn-page-title``, followed
by an equals sign, followed by the actual message ``Learn``. This last bit is
the only part that needs to be translated.

The comments can be important for working out how something should be
translated. In this situation, ‘Learn’ is a page title, and so it is a
description of what is happening on the page. In another situation, it might be
the caption on a button that does something when you press it. Depending on the
language, you might want different translations for these different situations.

Below this, we have ``## Navbar:`` which is a comment for the group of items
that follow.

Multi-line text
---------------

TODO

Substitutions
-------------

Above we have covered simple static strings. The Fluent system has more features
to cover additional language needs. The first is substitutions.

For example, on the ‘user activity page’, the title contains the user name for example on
`/user/spookylukey <https://learnscripture.net/user/spookylukey/activity/>`_ it has::

    Recent activity from spookylukey

In the FTL file, the message is defined like this::


    ## User's activity page.

    # Page title
    activity-user-page-title = Recent activity from { $username }

Here ``$username`` is a ‘variable’, a piece of data that is supplied by the
website that will be different for every different user's page.

Notice that the variable is placed between ``{`` and ``}``. Some other things
can also be placed between curly brackets, and together they are called
``placeables``.

Message references
------------------

Another kind of placeable you can come across is a message reference. Sometimes,
it is useful to include one message inside another. For example, you might have
some help text which refers to a button, and the caption on the button is
already defined in another message. To keep them in sync, we can use a message
reference.

For example, in ``catechisms.ftl`` we have::


    # Instructions about how to stop learning a catechism
    catechisms-how-to-opt-out =
        When learning a catechism, you can opt out of any individual question by
        pressing ‘{ learn-stop-learning-this-question }’ on the learning page.

In ``learn.ftl`` we have::


    learn-stop-learning-this-question = Stop learning this question


The final result of the first message will be:

        When learning a catechism, you can opt out of any individual question by
        pressing ‘Stop learning this question’ on the learning page.


Notice that for message references, there is no ``$`` symbol (unlike for variables).

Terms
-----

Terms are a mechanism to re-use common bit of text. You can read about them in
the `Fluent docs <https://projectfluent.org/fluent/guide/terms.html>`_ but we
are not currently using them for. LearnScripture.net



Variants
--------



Attributes
----------



HTML
