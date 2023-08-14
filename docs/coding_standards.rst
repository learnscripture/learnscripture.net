==================================
 Coding standards and methodology
==================================

Coding style
------------

* Black for Python
* 4 space indents for Javascript
* 2 space indents for HTML
* 4 space indents for CSS/LESS
* Normally, every file should end with a newline (but not more than one)

If you are unsure about any formatting issues, please follow the style of
existing code.

See also the file ``../.editorconfig`` which must match this, and see
http://editorconfig.org/ which may have a plugin for your editor to
automatically use this.

If possible, please set up your editor to use 'ruff' to check code as you go.
This can help avoid a lot of errors, as well as keeping coding style consistent.

Using `pre-commit <https://pre-commit.com/>`_ will allow you to automate these
linting checks and formatting before checking in to git.

Identifiers
-----------

We use American spelling variants, not British, for consistency with most
libraries that use American variants.
