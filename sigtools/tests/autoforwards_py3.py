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
    def _test(self, func, ensure_incoherent=True):
        self.assertSigsEqual(
            specifiers.signature(func),
            signatures.signature(func))
        if ensure_incoherent:
            with self.assertRaises(AssertionError):
                support.test_func_sig_coherent(
                    func, check_return=False, check_invalid=False)

    @tup()
    def rebind_subdef_nonlocal(a, b, *args, **kwargs):
        def func():
            nonlocal args, kwargs
            args = 2,
            kwargs = {'z': 3}
            _wrapped(42, *args, **kwargs)
        func()
        _wrapped(*args, **kwargs)

    @tup()
    def nonlocal_backchange(a, b, *args, **kwargs):
        def ret1():
            _wrapped(*args, **kwargs)
        def ret2():
            nonlocal args, kwargs
            args = ()
            kwargs = {}
        ret2()
        ret1()

    @tup()
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
        self._test(make_closure(), ensure_incoherent=False)

    def test_deleted(self):
        def makef(**kwargs):
            def func():
                _wrapped(**kwargs) # pyflakes: silence
            del kwargs
            return func
        self._test(makef, ensure_incoherent=False)

    def test_super(self):
        class Base:
            def method(self, x, y, *, z):
                pass
        class Derived(Base):
            def method(self, *args, a, **kwargs):
                super().method(*args, **kwargs)
        class MixIn(Base):
            def method(self, *args, b, **kwargs):
                super().method(*args, **kwargs)
        class MixedIn(Derived, MixIn):
            pass
        for cls in [Derived, MixedIn]:
            with self.subTest(cls=cls.__name__):
                self._test(cls().method)
