==================================
 Coding standards and methodology
==================================

Coding style
------------

* `PEP8`_ for Python
* 4 space indents for Javascript
* 2 space indents for HTML
* 4 space indents for CSS/LESS
* Normally, every file should end with a newline (but not more than one)

If you are unsure about any formatting issues, please follow the style of
existing code.

See also the file ``../.editorconfig`` which must match this, and see
http://editorconfig.org/ which may have a plugin for your editor to
automatically use this.

If possible, please set up your editor to use 'flake8' to check code as you go.
This can help avoid a lot of errors, as well as keeping coding style consistent.
You should ensure that you are using the right copy of flake8,
and that flake8 is respecting the settings in setup.cfg.

Imports should be sorted as per the isort command. See
https://github.com/timothycrosley/isort/wiki/isort-Plugins for editor plugins
for isort.

.. _PEP8: https://www.python.org/dev/peps/pep-0008/

Identifiers
-----------

We use American spelling variants, not British, for consistency with most
libraries that use American variants.
