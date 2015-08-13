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
