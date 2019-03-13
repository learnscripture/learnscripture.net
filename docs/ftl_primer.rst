Fluent primer
#############

This page is for translators who help with LearnScripture.net and is an
introduction to ``Fluent``, the system we use for ‘internationalizing and
localizing’ LearnScripture.net.

The overall process for translating LearnScripture.net looks like this:

1. Developers prepare 'FTL' files containing all the parts of the website that
   need to be translated. ‘FTL’ means “Fluent Translation List”.

2. Developers send the English version of these files to you, the translator, or
   share them in some other way that allows editing using an online editor.

3. You translate the English strings, save the files and send them back to the
   developers.


FTL file format
===============

The FTL file format is described fully in the `Fluent Guide
<https://projectfluent.org/fluent/guide/>`_. This page is a more simple
introduction and describes the features we use in LearnScripture.net

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

If a bit of text is long, it can be continued over multiple lines, but the
following lines must be indented. e.g.::

    a-message = This is a long message that flows onto
       multiple lines.

or::

    a-message =
       This is a long message that flows
       onto multiple lines.

In most cases where the line breaks come doesn't matter. When the text
is for an email, the line breaks usually do matter, and it is important
to keep the email to less than about 70 characters wide.

Substitutions
-------------

Above we have covered simple 'static' strings. The Fluent system has more features
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

When doing these translations, it will be helpful to imagine the sentence with
a specific example of a the substitution.

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


In this way, we don't have to remember to change both messages if we change the
caption on the button.

Notice that for message references, there is no ``$`` symbol (unlike
for variables).

Terms
-----

Terms are a mechanism to re-use common bit of text. You can read about them in
the `Fluent docs <https://projectfluent.org/fluent/guide/terms.html>`_ but we
are not currently using them for LearnScripture.net

`More info about terms <https://projectfluent.org/fluent/guide/terms.html>`_.

Selectors
---------

A common need for translated strings is that a good translation will have
multiple variants, depending on some external contextual information. A typical
example is plural forms. Fluent has a select expression syntax to cope with this
case. It looks like this::

    emails =
        { $unread_emails ->
            [0]     You have no unread emails.
            [one]   You have one unread email.
           *[other] You have { $unreadEmails } unread emails.
        }

Here ``$unread_emails`` will be a number that is compared to each of the options
which are called keys (``0``, ``one`` and ``other``). The keys can be numbers
like ``0``, ``1`` etc. They can also be strings ``zero``, ``one``, ``two``,
``few``, ``many`` and ``other``. Not all of these apply to all languages - for
example English only has ``one`` and ``other`` for cardinals, but other
languages can have several different plural forms (e.g. `Slovenian
<http://www.unicode.org/cldr/charts/30/supplemental/language_plural_rules.html#sl>`_).

So, in this example, if ``$unread_emails = 0``, you get::

    You have no unread emails.

If ``$unread_emails = 1``, you get::

    You have one unread email.

For anything else e.g. ``$unread_emails = 7``, you get::

    You have 7 unread emails.

Notice that the last option has a ``*`` next to it to indicate it is the default
option if nothing else matches - this default is required.

In some cases, a message that in English needs to use this selector can be
written correctly without a selector in another language - and the other way
around. It is up to you to decide if you need to use this.

The same feature can also be used for other kind of variants e.g. some
statements might need different variants depending on the gender of the person
being referred to. If you feel a translation needs some additional information
to do it correctly, please contact the developers.

Attributes
----------

In some cases, there is a single UI element with multiple pieces of text
attached. For example, a text box might have a label and some help text. Rather
than have multiple messages, the two strings are defined in a single message
using an attribute for one or more of the strings. For example::


    # Caption for 'enable vibration' field
    accounts-enable-vibration = Vibrate on mistakes
                          .help-text = Depends on device capabilities.

Here “Vibrate on mistakes” is the main label, and “Depends on device
capabilities” is the ``help-text`` attribute.

If you need to refer to attributes from other messages, it is done using dot syntax e.g.::

       { accounts-enable-vibration.help-text }

`More info about attributes
<https://projectfluent.org/fluent/guide/attributes.html>`_.


Numbers
-------

Fluent has functions for formatting numbers correctly for a given locale. This
handles the fact that, for instance, in England one thousand is written
``1,000`` but in most European countries it is ``1.000``. It can also be used to
add additional formatting options (such as using percentage mode or for currencies).

Without any options the NUMBER function can be used in a placeable like this:

    message = Points: { NUMBER($points) }

In most cases in LearnScripture.net appropriate formatting options have already
been applied, but you can change things like the number of decimal places shown,
using the options described in `Fluent NUMBER docs
<https://projectfluent.org/fluent/guide/functions.html#number>`_.

Dates
-----

Similarly, dates should be formatted using the ``DATETIME`` builtin. Usually the
default formatting will be fine.


HTML
----

HTML is the markup language used to create web pages. In most cases, you don't
need to use HTML or be aware of it to write the translations. Some messages,
however, use small bits of HTML that you need to understand.

Messages that use HTML have a message ID that ends with ``-html``, like this::

    bibleverses-quick-find-example-general-mode-html =
          example: <b>Matt 28:19</b> or <b>make disciples</b>


HTML formatting is done using tags with triangle brackets **<** and **>**. Most
tags come in pairs with and opening and closing tag that wraps a bit of text
e.g. <b> and </b>. The most common mistake is forgetting to close the pair
or forgetting the **/** in the closing tag.

Some of the most common ones you need to know are below:


======  ============  ==================================================  =================================
Tag     Usage         Example                                             Output
======  ============  ==================================================  =================================
b       bold          Here is some <b>bold</b> text                       Here is some **bold** text
i       italics       Did you mean: <i>Genesis</i>                        Did you mean: *Genesis*
a       link          Please <a href="/login/">log in</a> to continue     Please `log in </login/>`_ to continue
======  ============  ==================================================  =================================

Notice for the ``a`` tag, inside the open ``<a>`` there is something extra - an
``href`` attribute. This attribute is the ‘target’ of the link - the place you
go if the link is clicked. Normally this should not be changed, but the words
the link tags go around can be changed according to the conventions of the
language.

Sometimes you will see other attributes in tags - normally these do not need to
be changed.
