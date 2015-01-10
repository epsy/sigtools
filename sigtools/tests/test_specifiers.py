#!/usr/bin/env python
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


import unittest
import sys
from functools import partial

from sigtools import modifiers, specifiers, support, _util
from sigtools.tests.util import sigtester

# bulk of the testing happens in test_merge and test_embed

not_py33 = sys.version_info < (3,3)


def _func(*args, **kwargs):
    raise NotImplementedError

class _cls(object):
    method = _func
_inst = _cls()
_im_type = type(_inst.method)


@sigtester
def forwards_tests(self, outer, inner, args, kwargs, expected, expected_get):
    outer_f = support.f(outer)
    inner_f = support.f(inner)
    forw = specifiers.forwards_to_function(inner_f, *args, **kwargs)(outer_f)

    self.assertSigsEqual(
        specifiers.signature(forw),
        support.s(expected)
        )

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
        raise NotImplementedError

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
            super() # pragma: no cover

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
        if sys.version_info >= (3,3):
            self._test_func(self._sub_inst.fts, 's, l, *, m')

    sub_afts_cls = _Derivate.afts, 'self, asup, *args, **kwargs'
    sub_afts = _sub_inst.afts, 'asup, n, *, o'

    def test_chain_fts(self):
        if sys.version_info < (3,3):
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
                raise NotImplementedError

        class Cls(object):
            @specifiers.forwards_to_method('__init__', emulate=True)
            def __new__(cls):
                raise NotImplementedError

            def __init__(self):
                raise NotImplementedError

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
                raise NotImplementedError
        method = Cls().func
        func = specifiers.forwards_to_method('abc')(method)
        self.assertTrue(isinstance(func, specifiers._ForgerWrapper))
        self.assertEquals(func.__wrapped__, method)
        self.assertRaises(
            AttributeError,
            specifiers.forwards_to_method('abc', emulate=False), Cls().func)

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
                raise NotImplementedError
            def n(self):
                raise NotImplementedError
        class Sub(Cls):
            @specifiers.forwards_to_super()
            def m(self, *args, **kwargs):
                raise NotImplementedError
            @specifiers.forwards_to_super()
            def n(self, *args, **kwargs):
                super(Sub, self).n(*args, **kwargs) # pragma: no cover
        self.assertRaises(ValueError, specifiers.signature, Sub().m)
        if sys.version_info < (3,):
            self.assertRaises(ValueError, specifiers.signature, Sub().n)


@sig_equal
class PartialSigTests(object):
    _func1 = support.f('a, b, c, *args, d, e, **kwargs')

    pos = partial(_func1, 1), 'b, c, *args, d, e, **kwargs'
    kwkw = partial(_func1, d=1), 'a, b, c, *args, e, d=1, **kwargs'
    kwkws = partial(_func1, f=1), 'a, b, c, *args, d, e, f=1, **kwargs'

    kwposlast = partial(_func1, c=1), 'a, b, *, d, e, c=1, **kwargs'
    kwposlast = partial(_func1, b=1), 'a, *, d, e, c, b=1, **kwargs'


class ForgerFunctionTests(unittest.TestCase):
    def test_deco(self):
        @specifiers.forger_function
        def forger(obj):
            return support.s('abc')
        @forger()
        def forged():
            raise NotImplementedError
        self.assertEqual(support.s('abc'), specifiers.signature(forged))

    def test_directly_applied(self):
        def forger(obj):
            return support.s('abc')
        def forged():
            raise NotImplementedError
        specifiers.set_signature_forger(forged, forger)
        self.assertEqual(support.s('abc'), specifiers.signature(forged))

    def test_forger_lazy(self):
        class Flag(Exception): pass
        @specifiers.forger_function
        def forger(obj):
            raise Flag
        @forger()
        def forged():
            pass
        self.assertEqual(forged(), None)
        self.assertRaises(Flag, specifiers.signature, forged)

    def test_orig_sig(self):
        @specifiers.forger_function
        def forger(obj):
            return None
        @forger()
        def forged(alpha):
            raise NotImplementedError
        self.assertEqual(support.s('alpha'), specifiers.signature(forged))
