#!/usr/bin/env python

import unittest
import sys

from sigtools import modifiers, specifiers, support, _util
from sigtools.tests.util import sigtester

# bulk of the testing happens in test_merge and test_embed

not_py33 = sys.version_info < (3,3)


def _func(*args, **kwargs): pass

class _cls(object):
    method = _func
_inst = _cls()
_im_type = type(_inst.method)


@sigtester
def forwards_tests(self, outer, inner, args, kwargs, expected, expected_get):
    outer_f = support.f(outer)
    inner_f = support.f(inner)
    forw = specifiers.forwards_to_function(inner_f, *args, **kwargs)(outer_f)

    if expected is not None:
        self.assertSigsEqual(
            specifiers.signature(forw),
            support.s(expected)
            )

    if expected_get is not None:
        self.assertSigsEqual(
            specifiers.signature(_util.safe_get(forw, object(), object)),
            support.s(expected_get)
            )

@forwards_tests
class ForwardsTest(object):
    a = (
        'a, *p, b, **k', 'c, *, d', (), {},
        'a, c, *, b, d', 'c, *, b, d')
    b = (
        'a, *p, b, **k', 'a, c, *, b, d', (1, 'b'), {},
        'a, c, *, b, d', 'c, *, b, d')

    def test_call(self):
        outer = support.f('*args, **kwargs')
        inner = support.f('a, *, b')
        forw = specifiers.forwards_to_function(inner)(outer)
        instance = object()
        forw_get_prox = _util.safe_get(forw, instance, object)
        self.assertEqual(
            forw_get_prox(1, b=2),
            {'args': (instance, 1), 'kwargs': {'b': 2}}
            )

@sigtester
def sig_equal(self, obj, sig_str):
    self.assertSigsEqual(specifiers.signature(obj), support.s(sig_str),
                         conv_first_posarg=True)

class _Coop(object):
    @modifiers.kwoargs('cb')
    def method(self, ca, cb, *cr, **ck):
        pass

@sig_equal
class ForwardsAttributeTests(object):
    class _Base(object):
        def __init__(self, decorated=None):
            self.decorated = decorated
            self.coop = _Coop()

        @modifiers.kwoargs('b')
        def inner(self, a, b):
            raise NotImplementedError

        @specifiers.forwards_to_method('inner')
        def ftm(self, *args, **kwargs):
            raise NotImplementedError

        @specifiers.forwards_to_ivar('decorated')
        def fti(self, *args, **kwargs):
            raise NotImplementedError

        @specifiers.forwards_to_method('ftm')
        @modifiers.kwoargs('d')
        def ftm2(self, c, d, *args2, **kwargs2):
            raise NotImplementedError

        @modifiers.kwoargs('m')
        def fts(self, l, m):
            raise NotImplementedError

        @modifiers.kwoargs('o')
        def afts(self, n, o):
            raise NotImplementedError

        @specifiers.forwards_to_method('ftm2')
        @modifiers.kwoargs('q')
        def chain_fts(self, p, q, *args, **kwargs):
            raise NotImplementedError

        @specifiers.forwards_to_method('ftm2')
        @modifiers.kwoargs('s')
        def chain_afts(self, r, s, *args, **kwargs):
            raise NotImplementedError

        @specifiers.forwards_to_method('coop.method')
        @modifiers.kwoargs('bc')
        def ccm(self, ba, bb, bc, *args, **kwargs):
            raise NotImplementedError

    @_Base
    @modifiers.kwoargs('b')
    def _base_inst(a, b):
        raise NotImplementedError

    @specifiers.apply_forwards_to_super('afts', 'chain_afts')
    class _Derivate(_Base):
        @specifiers.forwards_to_method('inner')
        def ftm(self, e, *args, **kwoargs):
            raise NotImplementedError

        @specifiers.forwards_to_super()
        def fts(self, s, *args, **kwargs):
            super() # pramga: no cover

        def afts(self, asup, *args, **kwargs):
            raise NotImplementedError

        @specifiers.forwards_to_super()
        def chain_fts(self, u, *args, **kwargs):
            super() # pragma: no cover

        def chain_afts(self, v, *args, **kwargs):
            raise NotImplementedError

    @_Derivate
    @modifiers.kwoargs('y')
    def _sub_inst(x, y):
        raise NotImplementedError

    base_method = _base_inst.ftm, 'a, *, b'
    base_method2 = _base_inst.ftm2, 'c, a, *, d, b'

    base_method_cls = _Base.ftm, 'self, *args, **kwargs'

    base_ivar = _base_inst.fti, 'a, *, b'

    base_coop = _base_inst.ccm, 'ba, bb, ca, *cr, bc, cb, **ck'

    sub_method = _sub_inst.ftm, 'e, a, *, b'

    sub_method2 = _sub_inst.ftm2, 'c, e, a, *, d, b'

    sub_ivar = _sub_inst.fti, 'x, *, y'

    def test_fts(self):
        if not_py33:
            return

        self._test_func(self._sub_inst.fts, 's, l, *, m')

    sub_afts_cls = _Derivate.afts, 'self, asup, *args, **kwargs'
    sub_afts = _sub_inst.afts, 'asup, n, *, o'

    def test_chain_fts(self):
        if not_py33:
            return

        self._test_func(self._Derivate.chain_fts,
                        'self, u, *args, **kwargs')
        self._test_func(self._sub_inst.chain_fts,
                        'u, p, c, e, a, *, d, b, q')

    chain_afts_cls = _Derivate.chain_afts, 'self, v, *args, **kwargs'
    chain_afts = _sub_inst.chain_afts, 'v, r, c, e, a, *, d, b, s'

    def test_transform(self):
        class _callable(object):
            def __call__(self):
                pass

        class Cls(object):
            @specifiers.forwards_to_method('__init__', emulate=True)
            def __new__(cls):
                pass

            def __init__(self):
                pass

            abc = None
            if sys.version_info >= (3,):
                abc = specifiers.forwards_to_method('__init__', emulate=True)(
                    _callable()
                    )
        Cls.abc
        Cls.__new__
        self.assertEqual(type(Cls.__dict__['__new__'].__wrapped__),
                         staticmethod)
        Cls.__new__
        self.assertEqual(type(Cls.__dict__['__new__'].__wrapped__),
                         staticmethod)

    def test_emulation(self):
        func = specifiers.forwards_to_method('abc', emulate=False)(_func)
        self.assertTrue(_func is func)

        func = specifiers.forwards_to_method('abc')(_func)
        self.assertTrue(_func is func)

        class Cls(object):
            func = specifiers.forwards_to_method('abc')(_func)
        func = getattr(Cls.func, '__func__', func)
        self.assertTrue(_func is func)
        self.assertTrue(_func is Cls().func.__func__)

        class Cls(object):
            func = _func

            def abc(self, x):
                pass
        func = specifiers.forwards_to_method('abc')(Cls().func)
        self.assertTrue(isinstance(func, specifiers._ForgerWrapper))
        try:
            specifiers.forwards_to_method('abc', emulate=False)(Cls().func)
        except AttributeError:
            pass
        else:
            self.fail('Did not raise AttributeError')

        class Emulator(object):
            def __init__(self, obj, forger):
                self.obj = obj
                self.forger = forger

        func = specifiers.forwards_to_function(func, emulate=Emulator)(_func)
        self.assertTrue(isinstance(func, Emulator))

        @specifiers.forwards_to_function(_func, emulate=True)
        def func(x, y, *args, **kwargs):
            return x + y
        self.assertEqual(5, func(2, 3))

    def test_super_fail(self):
        class Cls(object):
            def m(self):
                pass
            def n(self):
                pass
        class Sub(Cls):
            @specifiers.forwards_to_super()
            def m(self, *args, **kwargs):
                pass
            @specifiers.forwards_to_super()
            def n(self, *args, **kwargs):
                super(Sub, self).n(*args, **kwargs)
        self.assertRaises(ValueError, specifiers.signature, Sub().m)
        if sys.version_info < (3,):
            self.assertRaises(ValueError, specifiers.signature, Sub().n)


if __name__ == '__main__':
    unittest.main()
