# sigtools - Collection of Python modules for manipulating function signatures
# Copyright (c) 2013-2015 Yann Kaiser
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""
`sigtools.signatures`: Signature object manipulation
----------------------------------------------------

The functions here are high-level operations that produce a signature from
other signature objects, as opposed to dealing with each parameter
individually. They are most notably used by the decorators from
`sigtools.specifiers` to compute combined signatures.

"""

import itertools

from sigtools import _util, modifiers
from sigtools._signatures import (
    signature,
    IncompatibleSignatures,
    sort_params, apply_params,
    _merge, _embed, _mask,
    )

__all__ = [
    'signature',
    'merge', 'embed', 'mask', 'forwards', 'IncompatibleSignatures',
    'sort_params', 'apply_params',
    ]

def merge(*signatures):
    """Tries to compute a signature for which a valid call would also validate
    the given signatures.

    It guarantees any call that conforms to the merged signature will
    conform to all the given signatures. However, some calls that don't
    conform to the merged signature may actually work on all the given ones
    regardless.

    :param inspect.Signature signatures: The signatures to merge together.

    :returns: a `inspect.Signature` object
    :raises: `IncompatibleSignatures`

    ::

        >>> from sigtools import signatures, support
        >>> print(signatures.merge(
        ...     support.s('one, two, *args, **kwargs'),
        ...     support.s('one, two, three, *, alpha, **kwargs'),
        ...     support.s('one, *args, beta, **kwargs')
        ...     ))
        (one, two, three, *, alpha, beta, **kwargs)

    The resulting signature does not necessarily validate all ways of
    conforming to the underlying signatures::

        >>> from sigtools import signatures
        >>> from inspect import signature
        >>>
        >>> def left(alpha, *args, **kwargs):
        ...     return alpha
        ...
        >>> def right(beta, *args, **kwargs):
        ...     return beta
        ...
        >>> sig_left = signature(left)
        >>> sig_right = signature(right)
        >>> sig_merged = signatures.merge(sig_left, sig_right)
        >>> 
        >>> print(sig_merged)
        (alpha, /, *args, **kwargs)
        >>> 
        >>> kwargs = {'alpha': 'a', 'beta': 'b'}
        >>> left(**kwargs), right(**kwargs) # both functions accept the call
        ('a', 'b')
        >>> 
        >>> sig_merged.bind(**kwargs) # the merged signature doesn't
        Traceback (most recent call last):
          File "<input>", line 1, in <module>
          File "/usr/lib64/python3.4/inspect.py", line 2642, in bind
            return args[0]._bind(args[1:], kwargs)
          File "/usr/lib64/python3.4/inspect.py", line 2542, in _bind
            raise TypeError(msg) from None
        TypeError: 'alpha' parameter is positional only, but was passed as a keyword

    """
    assert signatures, "Expected at least one signature"
    ret = sort_params(signatures[0])
    for i, sig in enumerate(signatures[1:], 1):
        sorted_params = sort_params(sig)
        try:
            ret = _merge(ret, sorted_params)
        except ValueError:
            raise IncompatibleSignatures(sig, signatures[:i])
    return apply_params(signatures[0], *ret)

@modifiers.autokwoargs
def embed(use_varargs=True, use_varkwargs=True, *signatures):
    """Embeds a signature within another's ``*args`` and ``**kwargs``
    parameters, as if a function with the outer signature called a function with
    the inner signature with just ``f(*args, **kwargs)``.

    :param inspect.Signature signatures: The signatures to embed within
        one-another, outermost first.
    :param bool use_varargs: Make use of the ``*args``-like parameter.
    :param bool use_varkwargs: Make use of the ``*kwargs``-like parameter.

    :returns: a `inspect.Signature` object
    :raises: `IncompatibleSignatures`

    ::

        >>> from sigtools import signatures, support
        >>> print(signatures.embed(
        ...     support.s('one, *args, **kwargs'),
        ...     support.s('two, *args, kw, **kwargs'),
        ...     support.s('last'),
        ...     ))
        (one, two, last, *, kw)
        >>> # use signatures.mask() to remove self-like parameters
        >>> print(signatures.embed(
        ...     support.s('self, *args, **kwargs'),
        ...     signatures.mask(
        ...         support.s('self, *args, keyword, **kwargs'), 1),
        ...     ))
        (self, *args, keyword, **kwargs)
    """
    assert signatures
    ret = sort_params(signatures[0])
    for i, sig in enumerate(signatures[1:], 1):
        try:
            ret = _embed(ret, sort_params(sig), use_varargs, use_varkwargs)
        except ValueError:
            raise IncompatibleSignatures(sig, signatures[:i])
    return apply_params(signatures[0], *ret)


@modifiers.autokwoargs(exceptions=('num_args',))
def mask(sig, num_args=0, hide_varargs=False,
            hide_varkwargs=False, *named_args):
    """Removes the given amount of positional parameters and the given named
    parameters from ``sig``.

    :param inspect.Signature sig: The signature to operate on
    :param int num_args: The amount of positional arguments passed
    :param str named_args: The names of named arguments passed
    :param hide_varargs: If true, mask the ``*args``-like parameter
        completely if present.
    :param hide_varkwargs: If true, mask the ``*kwargs``-like parameter
        completely if present.
    :return: a `inspect.Signature` object
    :raises: `ValueError` if the signature cannot handle the arguments
        to be passed.

    ::

        >>> from sigtools import signatures, support
        >>> print(signatures.mask(support.s('a, b, *, c, d'), 1, 'd'))
        (b, *, c)
        >>> print(signatures.mask(support.s('a, b, *args, c, d'), 3, 'd'))
        (*args, c)
        >>> print(signatures.mask(support.s('*args, c, d'), 2, 'd', hide_varargs=True))
        (*, c)

    """
    return _mask(sig, num_args, hide_varargs, hide_varkwargs, named_args)


@modifiers.autokwoargs
def forwards(outer, inner,
             use_varargs=True, use_varkwargs=True, *args, **kwargs):
    """Calls `mask` on ``inner``, then returns the result of calling
    `embed` with ``outer`` and the result of `mask`.

    :param inspect.Signature outer: The outermost signature.
    :param inspect.Signature inner: The inner signature.

    ``use_varargs`` and ``use_varkwargs`` are the same parameters as in
    `.embed`, and ``num_args``, ``named_args`` are parameters of `.mask`.

    :return: the resulting `inspect.Signature` object
    :raises: `IncompatibleSignatures`

    ::

        >>> from sigtools import support, signatures
        >>> print(signatures.forwards(
        ...     support.s('a, *args, x, **kwargs'),
        ...     support.s('b, c, *, y, z'),
        ...     1, 'y'))
        (a, c, *, x, z)

    .. seealso::
        :ref:`forwards-pick`

    """
    return embed(
        outer,
        mask(inner, *args, hide_varargs=False, hide_varkwargs=False, **kwargs),
        use_varargs=use_varargs, use_varkwargs=use_varkwargs)
forwards.__signature__ = forwards(
    signature(forwards), signature(mask),
    1, 'hide_varargs', 'hide_varkwargs')
