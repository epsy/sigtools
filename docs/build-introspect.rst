
.. _build introspect:

Building signature-inspecting tools with sigtools
=================================================

Whether it is for building documentation or minimizing repetition for the users
of your library or framework, inspecting callables might be something that will
help you achieve this.

Python has long provided tools to help you do this. The `inspect` module in
version 2.1 brought `~inspect.getargspec` which made use of attributes dating
back to Python 1.3. Python 3.3 brought `inspect.signature` which improved upon
the concept and made of an object-oriented approach to describing function
signatures.

`sigtools.signature` is a drop-in replacement for `inspect.signature`, with a
few key improvements:

* It is available on Python 2, thanks to `funcsigs <funcsigs.signature>`
* It can automatically traverse through decorators, while keeping track of
  which functions owns each parameter
* It supports a mechanism for functions to dynamically alter their reported
  signature

Separately, `sigtools.modifiers` brings keyword-only parameters and annotations
to Python 2, allowing you to rely on these features without having to dismiss
Python 2 compatility.


.. _using sigtools.signature:

Using ``sigtools.signature``
----------------------------

As with `inspect.signature`, simply call `sigtools.signature` with an object
to inspect::

    signature(myfunc)
    # <Signature (param, *, decorator_param)>

The objects `sigtools.signature` returns are `inspect.Signature` objects. You
can get an orderred dict containing all parameters using the
`~inspect.Signature.parameter` attribute, and so forth::

    sig = signature(myfunc)
    for param in sig.parameters.values():
        print(param.name, param.kind)
    # param POSITIONAL_OR_KEYWORD
    # decorator_param KEYWORD_ONLY

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


.. _inspect support:

Getting more help
-----------------

If there is anything you wish to discuss more thoroughly, feel free to come by
the sigtools `gitter chat <https://gitter.im/epsy/sigtools>`_.
