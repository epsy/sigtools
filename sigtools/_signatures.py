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
import collections
from functools import partial

from sigtools import _util

try:
    zip_longest = itertools.izip_longest
except AttributeError: # pragma: no cover
    zip_longest = itertools.zip_longest


class Signature(_util.funcsigs.Signature):
    __slots__ = _util.funcsigs.Signature.__slots__ + ('sources',)

    def __init__(self, *args, **kwargs):
        self.sources = kwargs.pop('sources', {})
        super(Signature, self).__init__(*args, **kwargs)

    @classmethod
    def upgrade(cls, inst, sources):
        if isinstance(inst, cls):
            return inst
        return cls(
            inst.parameters.values(),
            return_annotation=inst.return_annotation,
            sources=sources)

    def replace(self, *args, **kwargs):
        try:
            sources = kwargs.pop('sources')
        except KeyError:
            sources = self.sources
        ret = super(Signature, self).replace(*args, **kwargs)
        ret.sources = sources
        return ret


def default_sources(sig, obj):
    srcs = dict((pname, [obj]) for pname in sig.parameters)
    srcs['+depths'] = {obj: 0}
    return srcs


def set_default_sources(sig, obj):
    """Assigns the source of every parameter of sig to obj"""
    return Signature.upgrade(sig, default_sources(sig, obj))


def signature(obj):
    """Retrieves to unmodified signature from ``obj``, without taking
    `sigtools.specifiers` decorators into account or attempting automatic
    signature discovery.
    """
    if isinstance(obj, partial):
        sig = _util.funcsigs.signature(obj.func)
        sig = set_default_sources(sig, obj.func)
        return _mask(sig, len(obj.args), False, False, False, False,
                     obj.keywords or {}, obj)
    sig =_util.funcsigs.signature(obj)
    return set_default_sources(sig, obj)


def copy_sources(src, func_swap={}, increase=False):
    ret = dict(
        (k, [func_swap.get(f, f) for f in v])
        for k, v in src.items()
        if k != '+depths')
    ret['+depths'] = dict(
        (func_swap.get(f, f), v + increase)
        for f, v in src.get('+depths', {}).items())
    return ret


SortedParameters = collections.namedtuple(
    'SortedParameters',
    'posargs pokargs varargs kwoargs varkwargs sources')


def sort_params(sig, sources=False):
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
    if sources:
        src = getattr(sig, 'sources', {})
        return SortedParameters(posargs, pokargs, varargs, kwoargs, varkwas,
                                copy_sources(src))
    else:
        return posargs, pokargs, varargs, kwoargs, varkwas


def apply_params(sig, posargs, pokargs, varargs, kwoargs, varkwargs,
                 sources=None):
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
    sig = sig.replace(parameters=parameters)
    if sources is not None:
        sig = Signature.upgrade(sig, sources)
        sig.sources = sources
    return sig


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



def _add_sources(ret_src, name, *from_sources):
    target = ret_src.setdefault(name, [])
    target.extend(itertools.chain.from_iterable(
        src.get(name, ()) for src in from_sources))

def _add_all_sources(ret_src, params, from_source):
    """Adds the sources from from_source of all given parameters into the
    lhs sources multidict"""
    for param in params:
        ret_src.setdefault(param.name, []).extend(
            from_source.get(param.name, ()))

def _exclude_from_seq(seq, el):
    for i, x in enumerate(seq):
        if el is x:
            seq[i] = None
            break

def merge_depths(l, r):
    ret = dict(l)
    for func, depth in r.items():
        if func in ret and depth > ret[func]:
            continue
        ret[func] = depth
    return ret


class _Merger(object):
    def __init__(self, left, right):
        self.l = left
        self.r = right
        self.performed = False

    def perform_once(self):
        self.performed = True
        self._merge()

    def __iter__(self):
        self.perform_once()
        ret = (
            self.posargs, self.pokargs, self.varargs,
            self.kwoargs, self.varkwargs,
            self.src)
        return iter(ret)

    def _merge(self):
        self.posargs = []
        self.pokargs = []
        self.varargs_src = [self.l.varargs, self.r.varargs]
        self.kwoargs = _util.OrderedDict()
        self.varkwargs_src = [
            self.l.varkwargs,
            self.r.varkwargs
            ]
        self.src = {'+depths': self._merge_depths()}


        self.l_unmatched_kwoargs = _util.OrderedDict()
        for param in self.l.kwoargs.values():
            name = param.name
            if name in self.r.kwoargs:
                self.kwoargs[name] = self._concile_meta(
                    param, self.r.kwoargs[name])
                self.src[name] = list(itertools.chain(
                    self.l.sources.get(name, ()), self.r.sources.get(name, ())))
            else:
                self.l_unmatched_kwoargs[param.name] = param

        self.r_unmatched_kwoargs = _util.OrderedDict()
        for param in self.r.kwoargs.values():
            if param.name not in self.l.kwoargs:
                self.r_unmatched_kwoargs[param.name] = param

        il_pokargs = iter(self.l.pokargs)
        ir_pokargs = iter(self.r.pokargs)

        for l_param, r_param in zip_longest(self.l.posargs, self.r.posargs):
            if l_param and r_param:
                p = self._concile_meta(l_param, r_param)
                self.posargs.append(p)
                if l_param.name == r_param.name:
                    _add_sources(self.src, l_param.name,
                                 self.l.sources, self.r.sources)
                else:
                    _add_sources(self.src, l_param.name, self.l.sources)
            else:
                if l_param:
                    self._merge_unbalanced_pos(
                        l_param, self.l.sources,
                        ir_pokargs, self.r.varargs, self.r.sources)
                else:
                    self._merge_unbalanced_pos(
                        r_param, self.r.sources,
                        il_pokargs, self.l.varargs, self.l.sources)

        for l_param, r_param in zip_longest(il_pokargs, ir_pokargs):
            if l_param and r_param:
                if l_param.name == r_param.name:
                    self.pokargs.append(self._concile_meta(l_param, r_param))
                    _add_sources(self.src, l_param.name,
                                 self.l.sources, self.r.sources)
                else:
                    for i, pokarg in enumerate(self.pokargs):
                        self.pokargs[i] = pokarg.replace(
                            kind=pokarg.POSITIONAL_ONLY)
                    self.pokargs.append(
                        self._concile_meta(l_param, r_param)
                        .replace(kind=l_param.POSITIONAL_ONLY))
                    _add_sources(self.src, l_param.name, self.l.sources)
            else:
                if l_param:
                    self._merge_unbalanced_pok(
                        l_param, self.l.sources,
                        self.r.varargs, self.r.varkwargs,
                        self.r_unmatched_kwoargs, self.r.sources)
                else:
                    self._merge_unbalanced_pok(
                        r_param, self.r.sources,
                        self.l.varargs, self.l.varkwargs,
                        self.l_unmatched_kwoargs, self.l.sources)

        if self.l_unmatched_kwoargs:
            self._merge_unmatched_kwoargs(
                self.l_unmatched_kwoargs, self.r.varkwargs, self.l.sources)
        if self.r_unmatched_kwoargs:
            self._merge_unmatched_kwoargs(
                self.r_unmatched_kwoargs, self.l.varkwargs, self.r.sources)

        self.varargs = self._add_starargs(
            self.varargs_src, self.l.varargs, self.r.varargs)
        self.varkwargs = self._add_starargs(
            self.varkwargs_src, self.l.varkwargs, self.r.varkwargs)

    def _merge_depths(self):
        return merge_depths(self.l.sources.get('+depths', {}),
                            self.r.sources.get('+depths', {}))

    def _add_starargs(self, which, left, right):
        if not left or not right:
            return None
        if all(which):
            ret = self._concile_meta(left, right)
            if left.name == right.name:
                _add_sources(self.src, ret.name,
                             self.l.sources, self.r.sources)
            else:
                _add_sources(self.src, ret.name, self.l.sources)
        elif which[0]:
            ret = left
            _add_sources(self.src, ret.name, self.l.sources)
        else:
            ret = right
            _add_sources(self.src, ret.name, self.r.sources)
        return ret

    def _merge_unbalanced_pos(self, existing, src,
                              convert_from, o_varargs, o_src):
        try:
            other = next(convert_from)
        except StopIteration:
            if o_varargs:
                self.posargs.append(existing)
                _add_sources(self.src, existing.name, src)
                _exclude_from_seq(self.varargs_src, o_varargs)
            elif existing.default == existing.empty:
                raise ValueError('Unmatched positional parameter: {0}'
                                 .format(existing))
        else:
            self.posargs.append(self._concile_meta(existing, other))
            _add_sources(self.src, existing.name, src)

    def _merge_unbalanced_pok(
            self, existing, src,
            o_varargs, o_varkwargs, o_kwargs_limbo, o_src):
        """tries to insert positional-or-keyword parameters for which there were
        no matched positional parameter"""
        if existing.name in o_kwargs_limbo:
            self.kwoargs[existing.name] = self._concile_meta(
                existing, o_kwargs_limbo.pop(existing.name)
                ).replace(kind=existing.KEYWORD_ONLY)
            _add_sources(self.src, existing.name, o_src, src)
        elif o_varargs and o_varkwargs:
            self.pokargs.append(existing)
            _add_sources(self.src, existing.name, src)
        elif o_varkwargs:
            # convert to keyword argument
            self.kwoargs[existing.name] = existing.replace(
                kind=existing.KEYWORD_ONLY)
            _add_sources(self.src, existing.name, src)
        elif o_varargs:
            # convert along with all preceeding to positional args
            self.posargs.extend(
                a.replace(kind=a.POSITIONAL_ONLY)
                for a in self.pokargs)
            self.pokargs[:] = []
            self.posargs.append(existing.replace(kind=existing.POSITIONAL_ONLY))
            _add_sources(self.src, existing.name, src)
        elif existing.default == existing.empty:
            raise ValueError('Unmatched regular parameter: {0}'
                             .format(existing))

    def _merge_unmatched_kwoargs(self, unmatched_kwoargs, o_varkwargs, from_src):
        if o_varkwargs:
            self.kwoargs.update(unmatched_kwoargs)
            _add_all_sources(self.src, unmatched_kwoargs.values(), from_src)
            _exclude_from_seq(self.varkwargs_src, o_varkwargs)
        else:
            non_defaulted = [
                arg
                for arg in unmatched_kwoargs.values()
                if arg.default == arg.empty
                ]
            if non_defaulted:
                raise ValueError(
                    'Unmatched keyword parameters: {0}'.format(
                    ' '.join(str(arg) for arg in non_defaulted)))

    def _concile_meta(self, left, right):
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
    ret = sort_params(signatures[0], sources=True)
    for i, sig in enumerate(signatures[1:], 1):
        sorted_params = sort_params(sig, sources=True)
        try:
            ret = SortedParameters(*_Merger(ret, sorted_params))
        except ValueError:
            raise IncompatibleSignatures(sig, signatures[:i])
    ret_sig = apply_params(signatures[0], *ret)
    return ret_sig


def _check_no_dupes(collect, params):
    names = [param.name for param in params]
    dupes = collect.intersection(names)
    if dupes:
        raise ValueError('Duplicate parameter names: ' + ' '.join(dupes))
    collect.update(names)


def _clear_defaults(ita):
    for param in ita:
        yield param.replace(default=param.empty)


def _embed(outer, inner, use_varargs=True, use_varkwargs=True, depth=1):
    o_posargs, o_pokargs, o_varargs, o_kwoargs, o_varkwargs, o_src = outer

    stars_sig = SortedParameters(
        [], [], use_varargs and o_varargs,
        {}, use_varkwargs and o_varkwargs, {})

    i_posargs, i_pokargs, i_varargs, i_kwoargs, i_varkwargs, i_src = \
        _Merger(inner, stars_sig)

    names = set()

    e_posargs = []
    e_pokargs = []
    e_kwoargs = _util.OrderedDict()

    e_posargs.extend(o_posargs)
    _check_no_dupes(names, o_posargs)
    if i_posargs:
        _check_no_dupes(names, o_pokargs)
        e_posargs.extend(arg.replace(kind=arg.POSITIONAL_ONLY) for arg in o_pokargs)
        if i_posargs[0].default is i_posargs[0].empty:
            e_posargs = list(_clear_defaults(e_posargs))
        _check_no_dupes(names, i_posargs)
        e_posargs.extend(i_posargs)
    else:
        _check_no_dupes(names, o_pokargs)
        if i_pokargs and i_pokargs[0].default == i_pokargs[0].empty:
            e_posargs = list(_clear_defaults(e_posargs))
            e_pokargs.extend(_clear_defaults(o_pokargs))
        else:
            e_pokargs.extend(o_pokargs)
    _check_no_dupes(names, i_pokargs)
    e_pokargs.extend(i_pokargs)

    _check_no_dupes(names, o_kwoargs.values())
    e_kwoargs.update(o_kwoargs)
    _check_no_dupes(names, i_kwoargs.values())
    e_kwoargs.update(i_kwoargs)

    src = dict(i_src, **o_src)
    if o_varargs and use_varargs:
        src.pop(o_varargs.name, None)
    if o_varkwargs and use_varkwargs:
        src.pop(o_varkwargs.name, None)

    src['+depths'] = merge_depths(
        o_src.get('+depths', {}),
        dict((f, v+depth) for f, v in i_src.get('+depths', {}).items()))

    return (
        e_posargs, e_pokargs, i_varargs if use_varargs else o_varargs,
        e_kwoargs, i_varkwargs if use_varkwargs else o_varkwargs,
        src
        )

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
    ret = sort_params(signatures[0], sources=True)
    for i, sig in enumerate(signatures[1:], 1):
        try:
            ret = _embed(ret, sort_params(sig, sources=True),
                         use_varargs, use_varkwargs, i)
        except ValueError:
            raise IncompatibleSignatures(sig, signatures[:i])
    return apply_params(signatures[0], *ret)


def _pop_chain(*sequences):
    for sequence in sequences:
        while sequence:
            yield sequence.pop(0)


def _remove_from_src(src, ita):
    for name in ita:
        src.pop(name, None)


def _pnames(ita):
    for p in ita:
        yield p.name


def _mask(sig, num_args, hide_args, hide_kwargs,
          hide_varargs, hide_varkwargs, named_args, partial_obj):
    posargs, pokargs, varargs, kwoargs, varkwargs, src \
        = sort_params(sig, sources=True)

    pokargs_by_name = dict((p.name, p) for p in pokargs)
    consumed_names = set()

    if hide_args:
        consumed_names.update(p.name for p in posargs)
        consumed_names.update(p.name for p in pokargs)
        posargs = []
        pokargs = []
    elif num_args:
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

    _remove_from_src(src, consumed_names)

    if hide_args or hide_varargs:
        if varargs:
            src.pop(varargs.name, None)
        varargs = None

    partial_mode = partial_obj is not None

    if hide_kwargs:
        _remove_from_src(src, _pnames(pokargs))
        _remove_from_src(src, kwoargs)
        pokargs = []
        kwoargs = {}
        named_args = []

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
            else:
                src.pop(kwarg_name, None)
            if varargs:
                src.pop(varargs.name, None)
                varargs = None
            pokargs_by_name.clear()
        elif kwarg_name in kwoargs:
            if partial_mode:
                param = kwoargs[kwarg_name]
                kwoargs[kwarg_name] = param.replace(
                    kind=param.KEYWORD_ONLY, default=named_args[kwarg_name])
            else:
                src.pop(kwarg_name, None)
                kwoargs.pop(kwarg_name)
        elif not varkwargs:
            raise ValueError(
                'Named parameter {0!r} not found in signature: {1}'
                .format(kwarg_name, sig))
        elif partial_mode:
            kwoargs[kwarg_name] = _util.funcsigs.Parameter(
                kwarg_name, _util.funcsigs.Parameter.KEYWORD_ONLY,
                default=named_args[kwarg_name])
            src[kwarg_name] = [partial_obj]
        consumed_names.add(kwarg_name)

    if hide_kwargs or hide_varkwargs:
        if varkwargs:
            src.pop(varkwargs.name, None)
        varkwargs = None

    if partial_mode:
        src = copy_sources(src, increase=True)
        src['+depths'][partial_obj] = 0
    ret = apply_params(sig, posargs, pokargs, varargs, kwoargs, varkwargs, src)
    return ret


def mask(sig, num_args=0,
         hide_args=False, hide_kwargs=False,
         hide_varargs=False, hide_varkwargs=False,
         *named_args):
    """Removes the given amount of positional parameters and the given named
    parameters from ``sig``.

    :param inspect.Signature sig: The signature to operate on
    :param int num_args: The amount of positional arguments passed
    :param str named_args: The names of named arguments passed
    :param hide_args: If true, mask all positional parameters
    :param hide_kwargs: If true, mask all keyword parameters
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
    return _mask(sig, num_args, hide_args, hide_kwargs,
                 hide_varargs, hide_varkwargs, named_args, None)


def forwards(outer, inner, num_args=0,
             hide_args=False, hide_kwargs=False,
             use_varargs=True, use_varkwargs=True,
             partial=False, *named_args):
    """Calls `mask` on ``inner``, then returns the result of calling
    `embed` with ``outer`` and the result of `mask`.

    :param inspect.Signature outer: The outermost signature.
    :param inspect.Signature inner: The inner signature.
    :param bool partial: Set to `True` if the arguments are passed to
        ``partial(func_with_inner, *args, **kwargs)`` rather than
        ``func_with_inner``.

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
    if partial:
        params = []
        for param in inner.parameters.values():
            if param.kind in [param.VAR_POSITIONAL, param.VAR_KEYWORD]:
                params.append(param)
            else:
                params.append(param.replace(default=None))
        inner = inner.replace(parameters=params)
    return embed(
        use_varargs, use_varkwargs,
        outer,
        mask(inner, num_args,
             hide_args, hide_kwargs, False, False,
             *named_args))
