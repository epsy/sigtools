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

import itertools
from functools import partial

from sigtools import _util

try:
    from collections import abc
except ImportError: # pragma: no cover
    import collections as abc

try:
    zip_longest = itertools.izip_longest
except AttributeError: # pragma: no cover
    zip_longest = itertools.zip_longest


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
    kwoargs = _util.OrderedDict()
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
    kwoargs = _util.OrderedDict()
    varkwargs = r_varkwargs and l_varkwargs

    l_kwoargs_limbo = _util.OrderedDict()
    for l_kwoarg in l_kwoargs.values():
        if l_kwoarg.name in r_kwoargs:
            kwoargs[l_kwoarg.name] = _concile_meta(
                l_kwoarg, r_kwoargs[l_kwoarg.name])
        else:
            l_kwoargs_limbo[l_kwoarg.name] = l_kwoarg

    r_kwoargs_limbo = _util.OrderedDict()
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
    e_kwoargs = _util.OrderedDict()

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


def _pop_chain(*sequences):
    for sequence in sequences:
        while sequence:
            yield sequence.pop(0)


def _mask(sig, num_args, hide_varargs, hide_varkwargs, named_args):
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

    partial_mode = isinstance(named_args, abc.Mapping)

    for kwarg_name in named_args:
        if kwarg_name in consumed_names:
            raise ValueError('Duplicate argument: {0!r}'.format(kwarg_name))
        elif kwarg_name in pokargs_by_name:
            i = pokargs.index(pokargs_by_name[kwarg_name])
            pokargs, param, conv_kwoargs = (
                pokargs[:i], pokargs[i], pokargs[i+1:])
            kwoargs.update(
                (p.name, p.replace(kind=p.KEYWORD_ONLY))
                for p in conv_kwoargs)
            if partial_mode:
                kwoargs[param.name] = param.replace(
                    kind=param.KEYWORD_ONLY, default=named_args[param.name])
            varargs = None
            pokargs_by_name.clear()
        elif kwarg_name in kwoargs:
            if partial_mode:
                param = kwoargs[kwarg_name]
                kwoargs[kwarg_name] = param.replace(
                    kind=param.KEYWORD_ONLY, default=named_args[kwarg_name])
            else:
                kwoargs.pop(kwarg_name)
        elif not varkwargs:
            raise ValueError(
                'Named parameter {0!r} not found in signature: {1}'
                .format(kwarg_name, sig))
        elif partial_mode:
            kwoargs[kwarg_name] = _util.funcsigs.Parameter(
                kwarg_name, _util.funcsigs.Parameter.KEYWORD_ONLY,
                default=named_args[kwarg_name])
        consumed_names.add(kwarg_name)

    if hide_varkwargs:
        varkwargs = None

    return apply_params(sig, posargs, pokargs, varargs, kwoargs, varkwargs)



def signature(obj):
    if isinstance(obj, partial):
        sig = _util.funcsigs.signature(obj.func)
        return _mask(sig, len(obj.args), False, False, obj.keywords or {})
    return _util.funcsigs.signature(obj)


# This function is exposed as `sigtools.specifiers.signature`.
# it is here so that `sigtools.modifiers` may use it without causing
# circular imports
def forged_signature(obj):
    """Retrieve the signature of ``obj``, taking into account any specifier
    from this module.

    You can use ``emulate=True`` as an argument to the specifiers from this
    module if you wish them to work with `inspect.signature` or its
    `funcsigs<funcsigs:signature>` backport directly.

    ::

        >>> from sigtools import specifiers
        >>> import inspect
        >>> def inner(a, b):
        ...     return a + b
        ...
        >>> @specifiers.forwards_to_function(inner)
        ... def outer(c, *args, **kwargs):
        ...     return c * inner(*args, **kwargs)
        ...
        >>> print(inspect.signature(outer))
        (c, *args, **kwargs)
        >>> print(specifiers.signature(outer))
        (c, a, b)
        >>> @specifiers.forwards_to_function(inner, emulate=True)
        ... def outer(c, *args, **kwargs):
        ...     return c * inner(*args, **kwargs)
        #fixme

    """
    forger = getattr(obj, '_sigtools__forger', None)
    if forger is not None:
        ret = forger(obj=obj)
        if ret is not None:
            return ret
    return signature(obj)
