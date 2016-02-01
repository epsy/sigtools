from sigtools import support, specifiers
from sigtools.tests.util import Fixtures, tup


_wrapped = support.f('x, y, *, z')


class Py3UnknownAutoforwardsTests(Fixtures):
    def _test(self, func, expected, expected_src):
        sig = specifiers.signature(func)
        self.assertSigsEqual(sig, support.s(expected))
        self.assertSourcesEqual(sig.sources, expected_src, func)
        with self.assertRaises(AssertionError):
            support.test_func_sig_coherent(
                func, check_return=False, check_invalid=False)

    @tup('a, b, *args, **kwargs', {0: ['a', 'b', 'args', 'kwargs']})
    def rebind_subdef_nonlocal(a, b, *args, **kwargs):
        def func():
            nonlocal args, kwargs
            args = 2,
            kwargs = {'z': 3}
            _wrapped(42, *args, **kwargs)
        func()
        _wrapped(*args, **kwargs)

    @tup('a, b, *args, **kwargs', {0: ['a', 'b', 'args', 'kwargs']})
    def nonlocal_backchange(a, b, *args, **kwargs):
        def ret1():
            _wrapped(*args, **kwargs)
        def ret2():
            nonlocal args, kwargs
            args = ()
            kwargs = {}
        ret2()
        ret1()

    @tup('a, *args, **kwargs', {0: ['a', 'args', 'kwargs']})
    def nonlocal_deep(a, *args, **kwargs):
        def l1():
            def l2():
                nonlocal args, kwargs
                args = ()
                kwargs = {}
            l2()
        l1()
        _wrapped(*args, **kwargs)
