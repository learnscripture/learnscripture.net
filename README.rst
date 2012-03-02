README
======

TODO



Business logic
==============

As usual with Django apps, there is debate about where best to put business
logic. Since this is a relatively small app, most business logic has been put
onto Models, which attempt to encapsulate a lot of the schema so that client
code can (roughly) obey the Law of Demeter

This means that a lot of business logic is driven off the Identity (which in
turn delegates to Account for some things). A middleware attaches identity to
the request object where it is available.
