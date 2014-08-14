``sigtools``: utilities to manipulate callable objects' signatures
==================================================================

The ``sigtools`` python library provides:

* Decorators to specify keyword-only parameters, annotations and
  positional-only parameters, even on python2: ``sigtools.modifiers``
* Decorators to specify how ``*args, **kwargs`` are handled, in a way
  that can be introspected: ``sigtools.specifiers``
* Function combination routines that preserve signatures: ``sigtools.wrappers``
* Functions to manipulate signature objects likewise: ``sigtools.signatures``

The documentation can be found at Read The Docs:
http://sigtools.readthedocs.org

Installing
----------

Within a `virtualenv
<http://virtualenv.readthedocs.org/en/latest/virtualenv.html>`_::

    $ pip install sigtools

Or for a user-wide install::

    $ pip install --user sigtools
