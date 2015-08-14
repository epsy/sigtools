from functools import partial

from sigtools import support, modifiers, specifiers
from sigtools.tests.util import sigtester, tup


try:
    from sigtools.tests import autoforwards_py3
except SyntaxError:
    pass
else:
    Py3AutoforwardsTests = autoforwards_py3.Py3AutoforwardsTests


_wrapped = support.f('x, y, *, z')


def func(x):
    pass


@sigtester
def autosigequal(self, func, expected):
    self.assertSigsEqual(
        specifiers.signature(func),
        support.s(expected))


@autosigequal
class AutoforwardsTests(object):
    @tup('a, b, x, y, *, z')
    def global_(a, b, *args, **kwargs):
        pass
        return _wrapped(*args, **kwargs) # pragma: nocover

    def _make_closure():
        wrapped = _wrapped
        def wrapper(b, a, *args, **kwargs):
            return wrapped(*args, **kwargs)
        return wrapper
    closure = _make_closure(), 'b, a, x, y, *, z'

    @tup('a, b, y')
    def args(a, b, *args, **kwargs):
        return _wrapped(a, *args, z=b, **kwargs)

    @tup('a, b, *, z')
    def using_other_varargs(a, b, **kwargs):
        return _wrapped(a, *b, **kwargs)

    @tup('a, b, *args, **kwargs')
    def rebind_args(a, b, *args, **kwargs):
        args = ()
        kwargs = {}
        return _wrapped(*args, **kwargs)

    @tup('a, b, *args, z')
    def unknown_args(a, b, *args, **kwargs):
        args = None
        return _wrapped(*args, **kwargs)

    @tup('a, b, *args, z')
    def expr_args(a, b, *args, **kwargs):
        return _wrapped(*(range(10)), **kwargs)

    @tup('a, b, **kwargs')
    def unknown_kwargs(a, b, *args, **kwargs):
        kwargs = None
        return _wrapped(*args, **kwargs)

    # def test_external_args(self):
    #     def l1():
    #         a = None
    #         def l2(**kwargs):
    #             nonlocal a
    #             _wrapped(*a, **kwargs)
    #         return l2
    #     self._test_func(l1(), '*, z')

    @tup('*args, z')
    def rebind_using_with(*args, **kwargs):
        cm = None
        with cm() as args:
            _wrapped(*args, **kwargs)

    @tup('x, y, /, *, kwop')
    @modifiers.kwoargs('kwop')
    def kwo(kwop, *args):
        _wrapped(*args, z=kwop)

    @tup('a, b, y, *, z')
    def subdef(a, b, *args, **kwargs):
        def func():
            _wrapped(42, *args, **kwargs)

    @tup('a, b, y, *, z')
    def subdef_lambda(a, b, *args, **kwargs):
        lambda: _wrapped(42, *args, **kwargs)

    @tup('a, b, x, y, *, z')
    def rebind_subdef(a, b, *args, **kwargs):
        def func():
            args = ()
            kwargs = {}
            _wrapped(42, *args, **kwargs)
        _wrapped(*args, **kwargs)

    @tup('a, b, x, y, *, z')
    def rebind_subdef_param(a, b, *args, **kwargs):
        def func(*args, **kwargs):
            _wrapped(42, *args, **kwargs)
        _wrapped(*args, **kwargs)

    @tup('a, b, *args, **kwargs')
    def rebind_subdef_lambda_param(a, b, *args, **kwargs):
        lambda *args, **kwargs: _wrapped(*args, **kwargs)


    # @tup('a, b, x, y, *, z')
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

    partial_ = partial(_wrapper, _wrapped), 'a, x, y, *, z'

    @staticmethod
    @modifiers.kwoargs('wrapped')
    def _wrapped_kwoarg(a, wrapped, *args, **kwargs):
        return wrapped(*args, **kwargs)

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


    _wrapped = support.f('d, e, *, f')

    @tup('a, d, e, *, f')
    def global_attribute(a, *args, **kwargs):
        AutoforwardsTests._wrapped(*args, **kwargs)

    def test_instance_attribute(self):
        class A(object):
            def wrapped(self, x, y):
                pass
            def method(self, a, *args, **kwargs):
                self.wrapped(a, *args, **kwargs)
        a = A()
        self.assertSigsEqual(specifiers.signature(a.method),
                             support.s('a, y'))

    @staticmethod
    def _deeparg_l1(l2, *args, **kwargs):
        l2(*args, **kwargs)

    @staticmethod
    def _deeparg_l2(l3, *args, **kwargs):
        l3(*args, **kwargs)

    @tup('x, y, *, z')
    def deeparg(*args, **kwargs):
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

    @tup('a, b, c, x, y, *, z')
    def deeparg_kwo(a, *args, **kwargs):
        AutoforwardsTests._deeparg_kwo_l1(
            *args, l2=AutoforwardsTests._deeparg_kwo_l2, l3=_wrapped, **kwargs)

    @tup('a, x, y, *, z')
    def call_in_args(a, *args, **kwargs):
        func(_wrapped(*args, **kwargs))

    @tup('a, x, y, *, z')
    def call_in_kwargs(a, *args, **kwargs):
        func(kw=_wrapped(*args, **kwargs))

    @tup('a, x, y, *, z')
    def call_in_varargs(a, *args, **kwargs):
        func(*_wrapped(*args, **kwargs))

    @tup('a, x, y, *, z')
    def call_in_varkwargs(a, *args, **kwargs):
        func(**_wrapped(*args, **kwargs))
