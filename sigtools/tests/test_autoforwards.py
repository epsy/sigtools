import sys
from functools import partial, wraps

from sigtools import support, modifiers, specifiers, _util
from sigtools.tests.util import Fixtures, tup


if sys.version_info >= (3,):
    from sigtools.tests import autoforwards_py3
    Py3AutoforwardsTests = autoforwards_py3.Py3UnknownAutoforwardsTests


_wrapped = support.f('x, y, *, z', name='_wrapped')


def func(*args, **kwargs):
    pass


class AutoforwardsTests(Fixtures):
    def _test(self, func, expected, sources, incoherent=False):
        sig = specifiers.signature(func)
        self.assertSigsEqual(sig, support.s(expected))
        self.assertSourcesEqual(sig.sources, sources, func)
        if not incoherent:
            support.test_func_sig_coherent(
                func, check_return=False, check_invalid=False)

    @tup('a, b, x, y, *, z',
         {'global_': ('a', 'b'), '_wrapped': ('x', 'y', 'z')})
    def global_(a, b, *args, **kwargs):
        return _wrapped(*args, **kwargs)

    def _make_closure():
        wrapped = _wrapped
        def wrapper(b, a, *args, **kwargs):
            return wrapped(*args, **kwargs)
        return wrapper
    closure = (
        _make_closure(),
        'b, a, x, y, *, z', {'wrapper': 'ba', '_wrapped': 'xyz'})

    @tup('a, b, y', {'args': 'ab', '_wrapped': 'y'})
    def args(a, b, *args, **kwargs):
        return _wrapped(a, *args, z=b, **kwargs)

    @tup('a, b, *, z', {'using_other_varargs': 'ab', '_wrapped': 'z'})
    def using_other_varargs(a, b, **kwargs):
        return _wrapped(a, *b, **kwargs)

    # def test_external_args(self):
    #     def l1():
    #         a = None
    #         def l2(**kwargs):
    #             nonlocal a
    #             _wrapped(*a, **kwargs)
    #         return l2
    #     self._test_func(l1(), '*, z')

    @tup('x, y, /, *, kwop', {'kwo': ['kwop'], '_wrapped': 'xy'})
    @modifiers.kwoargs('kwop')
    def kwo(kwop, *args):
        _wrapped(*args, z=kwop)

    @tup('a, b, y, *, z', {'subdef': 'ab', '_wrapped': 'yz'})
    def subdef(a, b, *args, **kwargs):
        def func():
            _wrapped(42, *args, **kwargs)
        func()

    @tup('a, b, y, *, z', {'subdef_lambda': 'ab', '_wrapped': 'yz'})
    def subdef_lambda(a, b, *args, **kwargs):
        (lambda: _wrapped(42, *args, **kwargs))()

    @tup('a, b, x, y, *, z', {0: 'ab', '_wrapped': 'xyz'})
    def rebind_in_subdef(a, b, *args, **kwargs):
        def func():
            args = 1,
            kwargs = {'z': 2}
            _wrapped(42, *args, **kwargs)
        _wrapped(*args, **kwargs)
        func()

    @tup('a, b, x, y, *, z', {'rebind_subdef_param': 'ab', '_wrapped': 'xyz'})
    def rebind_subdef_param(a, b, *args, **kwargs):
        def func(*args, **kwargs):
            _wrapped(42, *args, **kwargs)
        _wrapped(*args, **kwargs)
        func(2, z=3)

    @tup('a, b, *args, **kwargs',
         {'rebind_subdef_lambda_param': ['a', 'b', 'args', 'kwargs']})
    def rebind_subdef_lambda_param(a, b, *args, **kwargs):
        f = lambda *args, **kwargs: _wrapped(*args, **kwargs)
        f(1, 2, z=3)

    # @tup('a, b, x, y, *, z', {0: 'ab', '_wrapped': 'xyz'})
    # def nonlocal_already_executed(a, b, *args, **kwargs):
    #     def make_ret2(args, kwargs):
    #         def ret2():
    #             _wrapped(*args, **kwargs)
    #     make_ret2(args, kwargs)
    #     def ret1():
    #         nonlocal args, kwargs
    #         args = ()
    #         kwargs = {}

    def _wrapper(wrapped, a, *args, **kwargs):
        return wrapped(*args, **kwargs)

    partial_ = partial(_wrapper, _wrapped), 'a, x, y, *, z', {
            _wrapper: 'a', _wrapped: 'xyz'}

    @staticmethod
    @modifiers.kwoargs('wrapped')
    def _wrapped_kwoarg(a, wrapped, *args, **kwargs):
        return wrapped(*args, **kwargs) # pragma: no cover

    def test_partial_kwo(self):
        """When given keyword arguments, functools.partial only makes them
        defaults. The full signature is therefore not fully determined, since
        the user can replace wrapped and change the meaning of *args, **kwargs.

        The substitution could be made in good faith that the user wouldn't
        change the value of the parameter, but this would potentially cause
        confusing documentation where a function description says remaining
        arguments will be forwarded to the given function, while the signature
        in the documentation only shows the default target's arguments.
        """
        func = partial(AutoforwardsTests._wrapped_kwoarg, wrapped=_wrapped)
        expected = support.s('a, *args, wrapped=w, **kwargs',
                             locals={'w': _wrapped})
        self.assertSigsEqual(specifiers.signature(func), expected)


    _wrapped_attr = staticmethod(support.f('d, e, *, f'))

    @tup('a, d, e, *, f', {0: 'a', 'func': 'def'})
    def global_attribute(a, *args, **kwargs):
        AutoforwardsTests._wrapped_attr(*args, **kwargs)

    def test_instance_attribute(self):
        class A(object):
            def wrapped(self, x, y):
                pass
            def method(self, a, *args, **kwargs):
                self.wrapped(a, *args, **kwargs)
        a = A()
        self._test(a.method, 'a, y', {0: 'a', 'wrapped': 'y'})

    def test_get_from_object(self):
        class A(object):
            def wrapped(self, x, y):
                pass
            def method(self, a, *p, **k):
                self.wrapped(a, *p, **k)
        method = _util.safe_get(A.__dict__['method'], object(), type(A))
        self._test(method, 'a, *p, **k', {0: 'apk'}, incoherent=True)

    def test_unset_attribute(self):
        class A(object):
            def method(self, a, *p, **k):
                self.wrapped(a, *p, **k)
        a = A()
        self._test(a.method, 'a, *p, **k', {0: 'apk'}, incoherent=True)

    @staticmethod
    @modifiers.kwoargs('b')
    def _deeparg_l1(l2, b, *args, **kwargs):
        l2(*args, **kwargs)

    @staticmethod
    @modifiers.kwoargs('c')
    def _deeparg_l2(l3, c, *args, **kwargs):
        l3(*args, **kwargs)

    @tup('x, y, *, a, b, c, z', {
            0: 'a', '_deeparg_l1': 'b', '_deeparg_l2': 'c', _wrapped: 'xyz'})
    @modifiers.kwoargs('a')
    def deeparg(a, *args, **kwargs):
        AutoforwardsTests._deeparg_l1(
            AutoforwardsTests._deeparg_l2, _wrapped,
            *args, **kwargs)

    @staticmethod
    @modifiers.kwoargs('l2')
    def _deeparg_kwo_l1(l2, b, *args, **kwargs):
        l2(*args, **kwargs)

    @staticmethod
    @modifiers.kwoargs('l3')
    def _deeparg_kwo_l2(l3, c, *args, **kwargs):
        l3(*args, **kwargs)

    @tup('a, b, c, x, y, *, z', {
        0: 'a', '_deeparg_kwo_l1': 'b', '_deeparg_kwo_l2': 'c', _wrapped: 'xyz'})
    def deeparg_kwo(a, *args, **kwargs):
        AutoforwardsTests._deeparg_kwo_l1(
            *args, l2=AutoforwardsTests._deeparg_kwo_l2, l3=_wrapped, **kwargs)

    @tup('a, x, y, *, z', {0: 'a', _wrapped: 'xyz'})
    def call_in_args(a, *args, **kwargs):
        func(_wrapped(*args, **kwargs))

    @tup('a, x, y, *, z', {0: 'a', _wrapped: 'xyz'})
    def call_in_kwargs(a, *args, **kwargs):
        func(kw=_wrapped(*args, **kwargs))

    @tup('a, x, y, *, z', {0: 'a', _wrapped: 'xyz'})
    def call_in_varargs(a, *args, **kwargs):
        func(*_wrapped(*args, **kwargs))

    @tup('a, x, y, *, z', {0: 'a', _wrapped: 'xyz'})
    def call_in_varkwargs(a, *args, **kwargs):
        func(**_wrapped(*args, **kwargs))

    @tup('y, *, z', {_wrapped: 'yz'})
    @wraps(_wrapped)
    def functools_wrapped(*args, **kwargs):
        _wrapped(1, *args, **kwargs)

    @tup('a, b, *args, z',
         {'unknown_args': ['a', 'b', 'args'], '_wrapped': 'z'})
    def unknown_args(a, b, *args, **kwargs):
        args = (1, 2)
        return _wrapped(*args, **kwargs)

    # @tup('a, b, c, x, y, *, z', {0: 'ab', 'sub': 'c', '_wrapped': 'xyz'})
    # def use_subdef(a, b, *args, **kwargs):
    #     def sub(c, *args, **kwargs):
    #         _wrapped(*args, **kwargs)
    #     sub(1, *args, **kwargs)

    @tup('a, b, x=None, y=None, *, z=None', {0: 'ab', '_wrapped': 'xyz'})
    def partial(a, b, *args, **kwargs):
        partial(_wrapped, *args, **kwargs)

    @tup('a, b, y=None', {0: 'ab', '_wrapped': 'y'})
    def partial_args(a, b, *args, **kwargs):
        partial(_wrapped, a, *args, z=b, **kwargs)
