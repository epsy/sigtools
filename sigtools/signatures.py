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

from sigtools import modifiers
from sigtools._signatures import (
    signature,
    IncompatibleSignatures,
    sort_params, apply_params,
    merge, embed, mask, forwards
    )

__all__ = [
    'signature',
    'merge', 'embed', 'mask', 'forwards', 'IncompatibleSignatures',
    'sort_params', 'apply_params',
    ]


merge = modifiers.autokwoargs(merge)
embed = modifiers.autokwoargs(embed)
mask = modifiers.autokwoargs(exceptions=('num_args',))(mask)
forwards_sources = modifiers.autokwoargs(exceptions=('num_args',))(forwards)

def forwards(*args, **kwargs):
    """Calls `mask` on ``inner``, then returns the result of calling
    `embed` with ``outer`` and the result of `mask`.

    :param inspect.Signature outer: The outermost signature.
    :param inspect.Signature inner: The inner signature.

    ``use_varargs`` and ``use_varkwargs`` are the same parameters as in
    `.embed`, and ``num_args``, ``named_args``, ``hide_args`` and
    ``hide_kwargs`` are parameters of `.mask`.

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
    return forwards_sources(*args, **kwargs)
