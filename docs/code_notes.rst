Bible verse references
======================

How Bible verses are referred to is a key issue in the project.

There are a number of constraints and requirements:

1. We need ``UserVerseStatus`` to be able to cope with catechisms and Bible verses,
   so a direct FK from ``UserVerseStatus`` to ``Verse`` isn't possible.

2. We also cope with people learning multi-verse references which span multiple
   ``Verse`` records (e.g. "Ephesians 2:8-9") as a single item which also means
   that we need an ID which is more flexible than a simple FK.

3. In some Bible versions, verse divisions are different, for example in Turkish
   TCL02, there is no Matthew 1:1 and 1:2 - they are combined into "Matta 1:1-2"

4. When displaying references, we always use the reference of the text,
   regardless of any other language preference there might be.

5. Sometimes we want to be able to use a 'language neutral' reference. Verse
   sets are not specific to the version or language used, so if someone is
   searching for a verse set that contains "John 3:16", for example, or the same
   thing in a different language, the same list of verse sets should be
   returned.

   Similarly, it should be possible to display and then choose to learn a verse
   set in any desired version (which gives issues about how to map verses
   when some texts may have combined verses as above).

For this reason, we have two types of reference - ``localized_reference`` and
``internal_reference``. In theory ``internal_reference`` could be just the
English version, but to ensure we aren't confusing the two we create a
different, language neutral encoding only for internal use.

We then ensure that everywhere we refer to references, we use variable and
function names that include either ``localized`` or ``internal``, to make it
obvious when we are passing the wrong thing.

Some models will use ``internal_reference`` as an ID. Other models will use
``localized_reference``, usually in conjunction with ``version_id`` - since each
``TextVersion`` has a single language, there is just one correct way to localize
a verse reference for a given ``TextVersion``.



Client-side/server-side
=======================

We use jQuery for client-side code where it is relatively simple stuff, and
preferably HTMX where possible.

We use Elm for the 'learn' page.

Apart from the Elm code, for rendering HTML we use server side Django templates
everywhere. This has significant advantages over a library like JsRender:

* Only one template system used, and a very capable one.
* No duplication of essentially the same template server side and client side.
* All localized strings are in server side code, so we don't need a client side
  i18n solution (apart from Elm code, which is handled well by elm-fluent)

This has the result that some of our API calls return rendered HTML instead of
the more usual JSON data that might be manipulated client-side.
