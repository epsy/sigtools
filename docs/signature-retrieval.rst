
.. _signature retrieval:

============================
Improved signature reporting
============================

Python's `inspect` module can produce `signature objects
<https://docs.python.org/3/library/inspect#introspecting-callables-with-the-signature-object>`_,
which represent how a function can be called. Their textual representation
roughly matches the parameter list part of a function definition:

.. code:: python

    import inspect


    def func(abc, *args, **kwargs):
        ...


    print(inspect.signature(func))
    # (abc, *args, **kwargs)

``sigtools`` introduces its own version of ``signature`` with improvements:

.. autosignature:: sigtools.signature
    :index:

    Improved version of `inspect.signature`. Takes into account decorators from
    `sigtools.specifiers` if present or tries to determine a full signature
    automatically.

    See `sigtools.specifiers.signature` for detailed reference.

For instance, consider this example of a decorator being defined and applied:

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
