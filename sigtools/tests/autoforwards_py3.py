from sigtools import support, specifiers, signatures
from sigtools.tests.util import Fixtures, tup


_wrapped = support.f('x, y, *, z')


class Py3AutoforwardsTests(Fixtures):
    def _test(self, func, expected, expected_src, incoherent=False):
        sig = specifiers.signature(func)
        self.assertSigsEqual(sig, support.s(expected))
        self.assertSourcesEqual(sig.sources, expected_src, func)
        if not incoherent:
            support.test_func_sig_coherent(
                func, check_return=False, check_invalid=False)

    def test_nonlocal_outside(self):
        x = _wrapped
        def l1(*args, **kwargs):
            nonlocal x
            x(*args, **kwargs)
        self._test(l1, 'x, y, *, z', {_wrapped: 'xyz'})


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

    def test_missing_freevar(self):
        def make_closure():
            var = 1
            del var
            def func(a, *p, **k):
                var(*p, **k) # pyflakes: silence
            return func
        func = make_closure()
        self.assertSigsEqual(
            specifiers.signature(func),
            signatures.signature(func))

    def test_deleted(self):
        def makef(**kwargs):
            def func():
                _wrapped(**kwargs) # pyflakes: silence
            del kwargs
            return func
        self._test(makef, '**kwargs', {0: ['kwargs']})
