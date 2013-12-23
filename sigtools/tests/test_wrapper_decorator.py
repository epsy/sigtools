#!/usr/bin/env python

import unittest

from sigtools import _util, wrappers, support
from sigtools.tests.util import sigtester

def tup(*args):
    return lambda wrapped: (wrapped,) + args

@sigtester
def wd_tests(self, func, sig_str, args, kwargs, ret, decorators):
    self.assertSigsEqual(_util.signature(func), support.s(sig_str))
    self.assertEqual(func(*args, **kwargs), ret)
    self.assertEqual(
        list(wrappers.wrappers(func)),
        [x.wrapper for x in decorators])

@wd_tests
class WdTests(object):
    @wrappers.wrapper_decorator
    def _deco_all(func, a, b, *args, **kwargs):
        return a, b, func(*args, **kwargs)

    def test_decorator_repr(self):
        repr(self._deco_all)

    @tup('a, b, j, k, l', (1, 2, 3, 4, 5), {}, (1, 2, (3, 4, 5)), [_deco_all])
    @_deco_all
    def func(j, k, l):
        return j, k, l

    @_deco_all
    def _method(self, n, o):
        return self, n, o

    def test_bound_wrapped_repr(self):
        repr(self._method)

    def test_bound(self):
        self._test_func(
            self._method, 'a, b, n, o',
            (1, 2, 3, 4), {}, (1, 2, (self, 3, 4)),
            [self._deco_all]
            )

    @staticmethod
    @_deco_all
    def _static(d, e, f):
        raise NotImplementedError

    def test_wrapped_repr(self):
        repr(self._static)

    @wrappers.wrapper_decorator(1)
    def _deco_pos(func, p, q, *args, **kwargs):
        return p, func(q, *args, **kwargs)

    @tup('p, q, ma, mb', (1, 2, 3, 4), {}, (1, (2, 3, 4)), [_deco_pos])
    @_deco_pos
    def masked(mq, ma, mb):
        return mq, ma, mb

    @_deco_all
    @_deco_pos
    def _chain(ca, cb, cc):
        return ca, cb, cc

    chain = (
        _chain, 'a, b, p, q, cb, cc',
        (1, 2, 3, 4, 5, 6), {}, (1, 2, (3, (4, 5, 6))),
        [_deco_all, _deco_pos]
        )

if __name__ == '__main__':
    unittest.main()
