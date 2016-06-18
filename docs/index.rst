:mod:`sigtools` documentation
=============================

.. module:: sigtools

``sigtools`` is a Python package that improves on introspection tools available
for determining function signatures. This is useful for libraries or tooling
that want to know how a function can be called: Documentation generators, IDEs,
and tools that adapt themselves to functions they are given.

``sigtools`` also provides a backport of Python 3's keyword-only parameters and
function annotations.


.. _keyword-only parameters:

Keyword-only parameters
-----------------------

``sigtools`` provides two decorators to emulate keyword-only parameters:

.. autosignature:: sigtools.modifiers.autokwoargs

    Converts all parameters with default values to keyword-only parameters:

    .. code:: python

        from sigtools.modifiers import autokwoargs


        @autokwoargs
        def func(arg, opt1=False, opt2=False, *rest):
            print(arg, rest, opt1, opt2)


        func(1, 2, 3)
        # 1 (2, 3) False False

        func(1, 2, opt2=True)
        # -> 1 (2,) False True

    ..
        x*

    In the example above, the ``opt1`` and ``opt2`` parameters are 'skipped' by
    positional arguments and can only be set using named arguments
    (``opt2=True``).

    If you wish to prevent parameters that have a default from becoming
    keyword-only, you can use the ``exceptions=`` parameter:

    .. code:: python

        @autokwoargs(exceptions=['arg2'])
        def func(arg1, arg2=42, opt1=False, opt2=False):
            print(arg1, arg2, opt1, opt2)

        func(1, 2, opt1=False)
        # 1 2 False False

If you wish to pick individual parameters to convert, use
`sigtools.modifiers.kwoargs`. This module also allows you to add function
annotations using the `~sigtools.modifiers.annotate` decorator.


.. _signature retrieval:

Improved signature reporting
----------------------------

Python 3.3's ``inspect`` module introduces `signature objects
<http://docs.python.org/3/library/inspect#introspecting-callables-with-the-signature-object>`_,
which represent how a function can be called. Their textual representation
roughly matches the parameter list part of a function definition:

.. code:: python

    import inspect


    def func(abc, *args, **kwargs):
        ...


    print(inspect.signature(func))
    # (abc, *args, **kwargs)

.. autosignature:: sigtools.signature
    :index:

    Improved version of `inspect.signature`. Takes into account decorators from
    `sigtools.specifiers` if present or tries to determine a full signature
    automatically.

For instance, consider this example of a decorator being defined and applied:

.. code:: python

    import inspect

    from sigtools import specifiers


    def decorator(param):
        def _decorate(wrapped):
            def _wrapper(*args, **kwargs):
                wrapped(param, *args, **kwargs)
            return _wrapper
        return _decorate


    @decorator('eggs')
    def func(ham, spam):
        return ham, spam


    print(inspect.signature(func))
    # (*args, **kwargs)

    print(specifiers.signature(func))
    # (spam)

Where `inspect.signature` simply sees ``(*args, **kwargs)`` from ``_wrapper``,
`sigtools.signature` returns the correct signature for the ``*args,
**kwargs`` portion of ``wrapped(param, *args, **params)``.


.. _sphinxext:

Improved signatures in `sphinx.ext.autodoc` documentation
---------------------------------------------------------

`Sphinx <http://sphinx-doc.org/>`_, the documentation tool, comes with an
extension, `sphinx.ext.autodoc`, which lets you source some of your
documentation from your code and its docstrings. ``sigtools.sphinxext``, if
activated, automatically improves signatures like explained above.

To activate it, add ``'sigtools.sphinxext'`` to the ``extensions`` list in your
Sphinx's  ``conf.py``:

.. code:: python

    extensions = [
        'sphinx.ext.autodoc', ...
        'sigtools.sphinxext']

If you want to use the automatic signature gathering while ignoring the docstring
in order to supply your own explanations, you can use this directive instead of
:rst:dir:`autofunction`:

.. rst:directive:: .. autosignature:: object

    Documents a Python object while ignoring the source docstring.
    `sigtools.specifiers.signature` is used to retrieve the object's call
    signature


.. _reference:

Reference
=========

.. toctree::

    api
    forwards-howto
    autofwd-limits
    build-introspect


.. |pip| replace:: pip
.. _pip: https://pip.pypa.io/en/latest/

.. |virtualenv| replace:: virtualenv
.. _virtualenv: https://virtualenv.pypa.io/en/latest/


.. _install:

Installing
==========

You can install `sigtools` using |pip|_. If in an activated |virtualenv|_, type:

.. code-block:: console

    pip install sigtools

If you wish to do a user-wide install:

.. code-block:: console

    pip install --user sigtools

