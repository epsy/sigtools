# sigtools - Python module to manipulate function signatures
# Copyright (c) 2013 Yann Kaiser
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

try:
    zip_longest = itertools.izip_longest
except AttributeError:
    zip_longest = itertools.zip_longest

__all__ = [
    'merge', 'embed', 'mask', 'forwards', 'IncompatibleSignatures',
    'sort_params', 'apply_params',
    ]

def sort_params(sig):
    """Classifies the parameters from sig.

    :param inspect.Signature sig: The signature to operate on

    :returns: A tuple ``(posargs, pokargs, varargs, kwoargs, varkwas)``
    :rtype: ``(list, list, Parameter or None, dict, Parameter or None)``

    ::

        >>> from sigtools import signatures, support
        >>> from pprint import pprint
        >>> pprint(signatures.sort_params(support.s('a, /, b, *args, c, d')))
        ([<Parameter at 0x7fdda4e89418 'a'>],
         [<Parameter at 0x7fdda4e89470 'b'>],
         <Parameter at 0x7fdda4e89c58 'args'>,
         {'c': <Parameter at 0x7fdda4e89c00 'c'>,
          'd': <Parameter at 0x7fdda4e89db8 'd'>},
         None)

    """
    posargs = []
    pokargs = []
    varargs = None
    kwoargs = _util.dod()
    varkwas = None
    for param in sig.parameters.values():
        if param.kind == param.POSITIONAL_ONLY:
            posargs.append(param)
        elif param.kind == param.POSITIONAL_OR_KEYWORD:
            pokargs.append(param)
        elif param.kind == param.VAR_POSITIONAL:
            varargs = param
        elif param.kind == param.KEYWORD_ONLY:
            kwoargs[param.name] = param
        elif param.kind == param.VAR_KEYWORD:
            varkwas = param
        else:
            raise AssertionError('Unknown param kind {0}'.format(param.kind))
    return posargs, pokargs, varargs, kwoargs, varkwas

def apply_params(sig, posargs, pokargs, varargs, kwoargs, varkwargs):
    """Reverses `sort_params`'s operation.

    :returns: A new `inspect.Signature` object based off sig,
        with the given parameters.
    """
    parameters = []
    parameters.extend(posargs)
    parameters.extend(pokargs)
    if varargs:
        parameters.append(varargs)
    parameters.extend(kwoargs.values())
    if varkwargs:
        parameters.append(varkwargs)
    return sig.replace(parameters=parameters)

class IncompatibleSignatures(ValueError):
    """Raised when two or more signatures are incompatible for the requested
    operation.

    :ivar inspect.Signature sig: The signature at which point the
        incompatibility was discovered
    :ivar others: The signatures up until ``sig``
    """

    def __init__(self, sig, others):
        self.sig = sig
        self.others = others

    def __str__(self):
        return '{0} {1}'.format(
            ' '.join(str(sig) for sig in self.others),
            self.sig,
            )

def _concile_meta(left, right):
    default = left.empty
    if left.default != left.empty and right.default != right.empty:
        if left.default == right.default:
            default = left.default
        else:
            # The defaults are different. Short of using an "It's complicated"
            # constant, None is the best replacement available, as a lot of
            # python code already uses None as default then processes an
            # actual default in the function body
            default = None
    annotation = left.empty
    if left.annotation != left.empty and right.annotation != right.empty:
        if left.annotation == right.annotation:
            annotation = left.annotation
    elif left.annotation != left.empty:
        annotation = left.annotation
    elif right.annotation != right.empty:
        annotation = right.annotation
    return left.replace(default=default, annotation=annotation)

def _merge(left, right):
    l_posargs, l_pokargs, l_varargs, l_kwoargs, l_varkwargs = left
    r_posargs, r_pokargs, r_varargs, r_kwoargs, r_varkwargs = right

    posargs = []
    pokargs = []
    varargs = r_varargs and l_varargs
    kwoargs = _util.dod()
    varkwargs = r_varkwargs and l_varkwargs

    l_kwoargs_limbo = _util.dod()
    for l_kwoarg in l_kwoargs.values():
        if l_kwoarg.name in r_kwoargs:
            kwoargs[l_kwoarg.name] = _concile_meta(
                l_kwoarg, r_kwoargs[l_kwoarg.name])
        else:
            l_kwoargs_limbo[l_kwoarg.name] = l_kwoarg

    r_kwoargs_limbo = _util.dod()
    for r_kwoarg in r_kwoargs.values():
        if r_kwoarg.name not in l_kwoargs:
            r_kwoargs_limbo[r_kwoarg.name] = r_kwoarg

    il_pokargs = iter(l_pokargs)
    ir_pokargs = iter(r_pokargs)

    for l_posarg, r_posarg in zip_longest(l_posargs, r_posargs):
        if l_posarg and r_posarg:
            posargs.append(_concile_meta(l_posarg, r_posarg))
        else:
            if l_posarg:
                _merge_unbalanced_pos(l_posarg, ir_pokargs, r_varargs, posargs)
            else:
                _merge_unbalanced_pos(r_posarg, il_pokargs, l_varargs, posargs,
                                      prefer_o=True)

    for l_pokarg, r_pokarg in zip_longest(il_pokargs, ir_pokargs):
        if l_pokarg and r_pokarg:
            if l_pokarg.name == r_pokarg.name:
                pokargs.append(_concile_meta(l_pokarg, r_pokarg))
            else:
                for i, pokarg in enumerate(pokargs):
                    pokargs[i] = pokarg.replace(kind=pokarg.POSITIONAL_ONLY)
                pokargs.append(
                    _concile_meta(l_pokarg, r_pokarg)
                    .replace(kind=l_pokarg.POSITIONAL_ONLY))
        else:
            if l_pokarg:
                _merge_unbalanced_pok(
                    l_pokarg, r_varargs, r_varkwargs, r_kwoargs_limbo,
                    posargs, pokargs, kwoargs)
            else:
                _merge_unbalanced_pok(
                    r_pokarg, l_varargs, l_varkwargs, l_kwoargs_limbo,
                    posargs, pokargs, kwoargs)

    if l_kwoargs_limbo:
        _merge_kwoargs_limbo(l_kwoargs_limbo, r_varkwargs, kwoargs)
    if r_kwoargs_limbo:
        _merge_kwoargs_limbo(r_kwoargs_limbo, l_varkwargs, kwoargs)

    return posargs, pokargs, varargs, kwoargs, varkwargs

def _merge_unbalanced_pos(existing, convert_from, o_varargs, posargs,
                          prefer_o=False):
    try:
        other = next(convert_from)
    except StopIteration:
        if o_varargs:
            posargs.append(existing)
        elif existing.default == existing.empty:
            raise ValueError('Unmatched positional parameter: {0}'.format(existing))
    else:
        if prefer_o:
            posargs.append(
                _concile_meta(other, existing).replace(kind=other.POSITIONAL_ONLY))
        else:
            posargs.append(_concile_meta(existing, other))

def _merge_unbalanced_pok(
        existing,
        o_varargs, o_varkwargs, o_kwargs_limbo,
        posargs, pokargs, kwoargs
        ):
    if existing.name in o_kwargs_limbo:
        kwoargs[existing.name] = _concile_meta(
            existing, o_kwargs_limbo.pop(existing.name)
            ).replace(kind=existing.KEYWORD_ONLY)
    elif o_varargs and o_varkwargs:
        pokargs.append(existing)
    elif o_varkwargs:
        # convert to keyword argument
        kwoargs[existing.name] = existing.replace(
            kind=existing.KEYWORD_ONLY)
    elif o_varargs:
        # convert along with all preceeding to positional args
        posargs.extend(
            a.replace(kind=a.POSITIONAL_ONLY)
            for a in pokargs)
        pokargs[:] = []
        posargs.append(existing.replace(kind=existing.POSITIONAL_ONLY))
    elif existing.default == existing.empty:
        raise ValueError('Unmatched regular parameter: {0}'.format(existing))

def _merge_kwoargs_limbo(kwoargs_limbo, o_varkwargs, kwoargs):
    if o_varkwargs:
        kwoargs.update(kwoargs_limbo)
    else:
        non_defaulted = [
            arg
            for arg in kwoargs_limbo.values()
            if arg.default == arg.empty
            ]
        if non_defaulted:
            raise ValueError(
                'Unmatched keyword parameters: {0}'.format(
                ' '.join(str(arg) for arg in non_defaulted)))

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

def _check_no_dupes(collect, params):
    names = [param.name for param in params]
    dupes = collect.intersection(names)
    if dupes:
        raise ValueError('Duplicate parameter names: ' + ' '.join(dupes))
    collect.update(names)

def _embed(outer, inner, use_varargs=True, use_varkwargs=True):
    o_posargs, o_pokargs, o_varargs, o_kwoargs, o_varkwargs = outer

    i_posargs, i_pokargs, i_varargs, i_kwoargs, i_varkwargs = _merge(
        inner, ([], [], use_varargs and o_varargs,
                {}, use_varkwargs and o_varkwargs))

    names = set()

    e_posargs = []
    e_pokargs = []
    e_kwoargs = _util.dod()

    e_posargs.extend(o_posargs)
    _check_no_dupes(names, o_posargs)
    if i_posargs:
        _check_no_dupes(names, o_pokargs)
        e_posargs.extend(arg.replace(kind=arg.POSITIONAL_ONLY) for arg in o_pokargs)
        _check_no_dupes(names, i_posargs)
        e_posargs.extend(i_posargs)
    else:
        _check_no_dupes(names, o_pokargs)
        e_pokargs.extend(o_pokargs)
    _check_no_dupes(names, i_pokargs)
    e_pokargs.extend(i_pokargs)

    _check_no_dupes(names, o_kwoargs.values())
    e_kwoargs.update(o_kwoargs)
    _check_no_dupes(names, i_kwoargs.values())
    e_kwoargs.update(i_kwoargs)

    return (
        e_posargs, e_pokargs, i_varargs if use_varargs else o_varargs,
        e_kwoargs, i_varkwargs if use_varkwargs else o_varkwargs
        )

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

def _pop_chain(*sequences):
    for sequence in sequences:
        while sequence:
            yield sequence.pop(0)

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
    posargs, pokargs, varargs, kwoargs, varkwargs = sort_params(sig)

    pokargs_by_name = dict((p.name, p) for p in pokargs)

    consumed_names = set()

    if num_args:
        consume = num_args
        for param in _pop_chain(posargs, pokargs):
            consume -= 1
            consumed_names.add(param.name)
            if not consume:
                break
        else:
            if not varargs:
                raise ValueError(
                    'Signature cannot be passed {0} arguments: {1}'
                    .format(num_args, sig))

    if hide_varargs:
        varargs = None

    for kwarg_name in named_args:
        if kwarg_name in consumed_names:
            raise ValueError('Duplicate argument: {0!r}'.format(kwarg_name))
        elif kwarg_name in pokargs_by_name:
            i = pokargs.index(pokargs_by_name[kwarg_name])
            pokargs, conv_kwoargs = pokargs[:i], pokargs[i+1:]
            kwoargs.update(
                (p.name, p.replace(kind=p.KEYWORD_ONLY))
                for p in conv_kwoargs)
            varargs = None
            pokargs_by_name.clear()
        elif kwarg_name in kwoargs:
            kwoargs.pop(kwarg_name)
        elif not varkwargs:
            raise ValueError(
                'Named parameter {0!r} not found in signature: {1}'
                .format(kwarg_name, sig))
        consumed_names.add(kwarg_name)

    if hide_varkwargs:
        varkwargs = None

    return apply_params(sig, posargs, pokargs, varargs, kwoargs, varkwargs)

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
    _util.signature(forwards), _util.signature(mask),
    1, 'hide_varargs', 'hide_varkwargs')
