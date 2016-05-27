from sigtools import support, specifiers
from sigtools.tests.util import Fixtures, tup


_wrapped = support.f('x, y, *, z')


class Py35UnknownAutoforwardsTests(Fixtures):
    def _test(self, func, expected, expected_src):
        sig = specifiers.signature(func)
        self.assertSigsEqual(sig, support.s(expected))
        self.assertSourcesEqual(sig.sources, expected_src, func)
        with self.assertRaises(AssertionError):
            support.test_func_sig_coherent(
                func, check_return=False, check_invalid=False)

    @tup('v, w, *a, **k', {0: 'vwak'})
    def double_starargs(v, w, *a, **k):
        _wrapped(*a, *a)

    @tup('v, w, *a, **k', {0: 'vwak'})
    def double_kwargs(v, w, *a, **k):
        _wrapped(**k, **w)
