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

"""Tools to manipulate signatures directly.

"""
import itertools

from sigtools import modifiers

try:
    zip_longest = itertools.izip_longest
except AttributeError:
    zip_longest = itertools.zip_longest

def sort_params(sig):
    """Classifies the parameters from sig.

    :returns: A tuple ``(posargs, pokargs, varargs, kwoargs, varkwas)``
    :rtype: ``(list, list, Parameter or None, dict, Parameter or None)``
    """
    posargs = []
    pokargs = []
    varargs = None
    kwoargs = {}
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
    """Reverses :py:func:`sort_params`'s operation.

    :returns: A new signature object based off sig, with the given parameters.
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

    :ivar sig: The signature at which point the incompatibility was discovered
    :ivar others: The signatures up until ``sig``
    """

    def __init__(self, sig, others):
        self.sig = sig
        self.others = others

    def __str__(self):
        return '{0} {1}'.format(
            self.sig,
            ' '.join(str(sig) for sig in self.others)
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

def _filter_ignored(seq, ignore):
    return [
        arg for arg in seq
        if arg.name not in ignore
        ]

def _merge(left, right, ignore):
    l_posargs, l_pokargs, l_varargs, l_kwoargs, l_varkwargs = left
    r_posargs, r_pokargs, r_varargs, r_kwoargs, r_varkwargs = right

    l_posargs = _filter_ignored(l_posargs, ignore)
    r_posargs = _filter_ignored(r_posargs, ignore)
    l_pokargs = _filter_ignored(l_pokargs, ignore)
    r_pokargs = _filter_ignored(r_pokargs, ignore)

    posargs = []
    pokargs = []
    varargs = r_varargs and l_varargs
    kwoargs = {}
    varkwargs = r_varkwargs and l_varkwargs

    l_kwoargs_limbo = {}
    for l_kwoarg in l_kwoargs.values():
        if l_kwoarg.name in ignore:
            continue
        if l_kwoarg.name in r_kwoargs:
            kwoargs[l_kwoarg.name] = _concile_meta(
                l_kwoarg, r_kwoargs[l_kwoarg.name])
        else:
            l_kwoargs_limbo[l_kwoarg.name] = l_kwoarg

    r_kwoargs_limbo = {}
    for r_kwoarg in r_kwoargs.values():
        if r_kwoarg.name in ignore:
            continue
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

@modifiers.kwoargs('ignore')
def merge(ignore=(), *signatures):
    """Tries to compute one common signature from multiple ones.

    It guarantees any call that conforms to the merged signature will
    conform to all the given signatures. However, some calls that don't
    conform to the merged signature may actually work on all the given ones.

    :returns: a signature object
    :raises: :py:class:`IncompatibleSignatures`

    Example::

        >>> from sigtools import signatures, test
        >>> print(signatures.merge(
        ...     test.s('one, two, *args, **kwargs'),
        ...     test.s('one, two, three, *, alpha, **kwargs'),
        ...     test.s('one, *args, beta, **kwargs')
        ...     ))
        (one, two, three, *, beta, alpha, **kwargs)

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
        >>> kwargs = {'alpha': 'a', 'beta': 'b'}
        >>> left(**kwargs), right(**kwargs) # both functions accept the call
        ('a', 'b')
        >>> 
        >>> print(sig_merged)
        (<alpha>, *args, **kwargs)
        >>> sig_merged.bind(**kwargs) # the merged signature doesn't
        Traceback (most recent call last):
          File "<input>", line 1, in <module>
          File "/usr/lib/python3.3/inspect.py", line 2036, in bind
            return __bind_self._bind(args, kwargs)
          File "/usr/lib/python3.3/inspect.py", line 1944, in _bind
            raise TypeError(msg) from None
        TypeError: 'alpha' parameter is positional only, but was passed as a keyword


    """
    assert signatures, "Expected at least one signature"
    ret = sort_params(signatures[0])
    for i, sig in enumerate(signatures[1:], 1):
        sorted_params = sort_params(sig)
        try:
            ret = _merge(ret, sorted_params, ignore=ignore)
        except ValueError:
            raise IncompatibleSignatures(sig, signatures[:i])
    return apply_params(signatures[0], *ret)

def _check_no_dupes(collect, params):
    names = [param.name for param in params]
    dupes = collect.intersection(names)
    if dupes:
        raise ValueError('Duplicate parameter names: ' + ' '.join(dupes))
    collect.update(names)

def _embed(outer, inner, share):
    o_posargs, o_pokargs, o_varargs, o_kwoargs, o_varkwargs = outer

    i_posargs, i_pokargs, i_varargs, i_kwoargs, i_varkwargs = _merge(
        ([], [], o_varargs, {}, o_varkwargs), inner, ignore=share)

    names = set()

    e_posargs = []
    e_pokargs = []
    e_kwoargs = {}

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

    return e_posargs, e_pokargs, i_varargs, e_kwoargs, i_varkwargs

@modifiers.kwoargs('share')
def embed(share=(), *signatures):
    """Embeds a signature within another's ``*args`` and ``**kwargs``
    parameters.

    :param share: a sequence of parameter names that are shared across the
        passed signatures.
    :returns: a signature object
    :raises: :py:class:`IncompatibleSignatures`

    Example:

        >>> from sigtools import signatures, test
        >>> print(signatures.embed(
        ...     test.s('one, *args, **kwargs'),
        ...     test.s('two, *args, kw, **kwargs'),
        ...     test.s('last'),
        ...     ))
        (one, two, last, *, kw)
        >>> 
        >>> print(signatures.embed(
        ...     test.s('self, *args, **kwargs'),
        ...     test.s('self, *args, keyword, **kwargs'),
        ...     share=['self']
        ...     ))
        (self, *args, keyword, **kwargs)
    """
    assert signatures
    ret = sort_params(signatures[0])
    for i, sig in enumerate(signatures[1:], 1):
        try:
            ret = _embed(ret, sort_params(sig), share=share)
        except ValueError:
            raise IncompatibleSignatures(sig, signatures[:i])
    return apply_params(signatures[0], *ret)

