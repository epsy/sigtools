
.. _build introspect:
.. _signature retrieval:

============================
Improved signature reporting
============================

Whether it is for building documentation or minimizing repetition for the users
of your library or framework, inspecting callables might be something that could
help you achieve it.

Python has provided tools to help you do this for a while.
The `inspect` module in version 2.1 added `~inspect.getargspec`
which made use of code and function attributes dating back to Python 1.3.
Python 3.3 introduced `inspect.signature`
which polished the concept such that
a `inspect.Signature` object describes a function's
parameters, annotations and default values.

.. autosignature:: sigtools.signature
    :index:

    Improved version of `inspect.signature`. Takes into account decorators from
    `sigtools.specifiers` if present or tries to determine a full signature
    automatically.

    See `sigtools.specifiers.signature` for detailed reference.

`sigtools.signature` is a drop-in replacement for `inspect.signature`, with a
few key improvements:

* It can automatically traverse through decorators, while keeping track of
  which functions owns each parameter
* It helps you evaluate parameter annotations in the proper context,
  for instance when the parameter annotation is defined in
  a module that enables :pep:`postponed evaluation of annotations <563>`.
* It supports a mechanism for functions to dynamically alter their reported
  signature

.. _using sigtools.signature:

Using `sigtools.signature`
==========================

Python's `inspect` module can produce :ref:`signature objects
<python:inspect-signature-object>`,
which represent how a function can be called. Their textual representation
roughly matches the parameter list part of a function definition:

.. code:: python

    import inspect


    def func(abc, *args, **kwargs):
        ...


    print(inspect.signature(func))
    # (abc, *args, **kwargs)

You can do the same with `sigtools.signature`::

    from sigtools import signature

    print(signature(func))
    # (abc, *args, **kwargs)

You can use the resulting object the same way as `inspect.Signature`, for example::

    sig = signature(myfunc)
    for param in sig.parameters.values():
        print(param.name, param.kind)
    # param POSITIONAL_OR_KEYWORD
    # decorator_param KEYWORD_ONLY


.. _signature-decorator-example:

Introspection through decorators
================================

As alluded to above,
`sigtools.signature` will look through decorators
and produce a signature that takes parameters that such decorators add or remove into account:

.. literalinclude:: /../examples/retrieve_signature.py
    :end-at: # sigtools:

Where `inspect.signature` simply sees the signature of ``func`` itself,
`sigtools.signature` sees how things fit together:

- It understands that
  ``_wrapper`` uses its ``*args`` and ``**kwargs``
  by passing them to ``wrapped``, which is ``func``,
- It sees that one argument to ``func`` is supplied by ``_wrapper``
- It sees that ``_wrapper`` has a parameter of its own.

This lets `sigtools.signature` determine
the effective signature of ``func`` as decorated.

.. note:: Is `functools.wraps` necessary?

    `~functools.wraps` is recommended when writing decorators,
    because it copies attributes from the wrapped function to the wrapper,
    such as the name and docstring,
    which is generally useful.

    `sigtools.signature` will continue working the same,
    but `inspect.signature` will show ``_wrapper``'s signature:

    .. literalinclude:: /../examples/retrieve_signature.py
        :start-at: inspect w/o wraps

    In the example above this note, `inspect.signature` uses `inspect.unwrap`
    to find the function to get the innermost function
    (``func`` as defined in the source, before decorators),
    and takes the signature from that.
    If the decorator alters the effective signature of whatever it wraps,
    like above, this will probably produce an incorrect signature.

.. note::

    While `sigtools.signature` should generally work with most python code (see :ref:`autofwd limits`),
    ``sigtools`` recommends `sigtools.wrappers.decorator`
    as the simplest way to write custom decorators
    while preserving as much information as possible.

    For instance, decorators defined with `~sigtools.wrappers.decorator` are set up in a way
    that the :ref:`source <parameter-sources>` of each parameter points to a function
    on which the docstring is not overwritten, unlike in the example above.


.. _evaluating stringified annotations:
.. _evaluating pep-563 annotations:

Evaluating :pep:`563` stringified annotations
=============================================

`sigtools.signature` returns instances
of `~sigtools.signatures.UpgradedSignatures`,
on which parameters have a new attribute
`~sigtools.signature.UpgradedParameter.upgraded_annotation`.
The return signature is also available as
`~sigtools.signature.UpgradedSignature.upgraded_return_annotation`.
Both have a value of type `~sigtools.signature.UpgradedAnnotation`,
which allow you to get the value of an annotation as seen in the source.


.. literalinclude:: /../examples/postponed_annotation.py


.. autoclass:: sigtools.signatures.UpgradedAnnotation
    :noindex:
    :members: source_value

.. autoclass:: sigtools.signatures.UpgradedSignature
    :noindex:
    :members: upgraded_return_annotation, parameters

    .. py:attribute:: parameters
        :type: sigtools.signatures.UpgradedParameter

.. autoclass:: sigtools.signatures.UpgradedParameter
    :noindex:
    :members: upgraded_annotation

.. _parameter-sources:

Parameter provenance
====================

.. warning::

    Interface is likely to change in `sigtools` 5.0.

`sigtools.signature` adds a ``sources`` attribute to the signature object.
For each parameter, it lists all functions that will receive this parameter::

    for param in sig.parameters.values():
        print(param.name, sig.sources[param.name])
    # param [<function myfunc at ...>]
    # decorator_param [<function decorator.<locals>._wrapper at ...>]

Additionally, this attribute contains the *depth* of each function, if you need
a reliable order for them::

    print(sig.sources['+depths'])
    # {<function decorator.<locals>._wrapper at 0x7f354829c6a8>: 0,
    #  <function myfunc at 0x7f354829c730>: 1}



.. _autofwd limits:

Limitations of automatic signature discovery
============================================

`sigtools.signature` is able to examine a function to determine
how its ``*args, **kwargs`` parameters are being used, even when no information
is otherwise provided.

This is very useful for documentation or introspection tools, because it means
authors of documented or introspected code don't have to worry about providing
this meta-information.

It should handle almost all instances of decorator code, though more unusual
code could go beyond its ability to understand it. If this happens it will fall
back to a generic signature.

Here is a list of the current limitations:

* It requires the source code to be available. This means automatic
  introspection of functions that were defined in missing ``.py`` files, in
  code passed to :func:`eval` or in an :ref:`interactive
  session<tut-interactive>` will fail.
* It doesn't handle transformations or resetting of ``args`` and ``kwargs``
* It doesn't handle Python 3.5's multiple ``*args`` and ``**kwargs`` support
* It doesn't handle calls to the superclass

In some other instances, the signature genuinely can't be determined in
advance.  For instance, if you call one function or another depending on a
parameter, and these functions have incompatible signatures, there wouldn't be
*one* common signature for the outer function.

If you still need accurate signature reporting when automatic discovery fails,
you can use the decorators from the `.specifiers` module:

.. seealso:: :ref:`forwards-pick`

.. _inspect support:

Getting more help
=================

If there is anything you wish to discuss more thoroughly, feel free to come by
the sigtools `gitter chat <https://gitter.im/epsy/sigtools>`_.
