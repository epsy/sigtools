
.. _autofwd limits:

Limitations of automatic signature discovery
============================================

`sigtools.specifiers.signature` is able to examine a function to determine
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
use the decorators from the `.specifiers` module:

.. seealso:: :ref:`forwards-pick`
