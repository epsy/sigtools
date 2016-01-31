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


from sigtools import support, _specifiers
from sigtools.tests.util import Fixtures




class RoundTripTests(Fixtures):
    def _test(self, sig_str, old_fmt=None):
        sig = support.s(sig_str)
        p_sig_str = str(sig)
        try:
            self.assertEqual('(' + sig_str + ')', p_sig_str)
        except AssertionError:
            if old_fmt is None: raise
            self.assertEqual('(' + old_fmt + ')', p_sig_str)

        pf_sig_str = str(
            _specifiers.forged_signature(support.func_from_sig(sig)))
        try:
            self.assertEqual('(' + sig_str + ')', pf_sig_str)
        except AssertionError:
            if old_fmt is None: raise
            self.assertEqual('(' + old_fmt + ')', pf_sig_str)

    empty = '',

    pok = 'a, b',
    pos = 'a, /, b', '<a>, b'
    pos_old = '<a>, b', 'a, /, b'

    default = 'a=1',
    varargs = '*args',
    varkwargs = '**kwargs',

    kwo = '*args, a',
    kwo_novarargs = '*, a',
    kwo_order = 'a, b=1, *args, c, d, e, f=4',

    defaults = 'a, b=1, *, c, d=1',
    default_after_star = 'a, b, *, c, d=1, e=2',

    annotate = 'a:1, /, b:2, *c:3, d:4, **e:5', '<a>:1, b:2, *c:3, d:4, **e:5'

    def test_return_annotation(self):
        self.assertEqual('() -> 2', str(support.s('', 2)))
        self.assertEqual('() -> 3', str(support.s('', ret=3)))
        self.assertEqual('(a:4) -> 5', str(support.s('a:4', 5)))
        self.assertEqual('(b:6) -> 7', str(support.s('b:6', ret=7)))

    def test_locals(self):
        obj = object()
        sig = support.s('a:o', locals={'o': obj})
        self.assertIs(obj, sig.parameters['a'].annotation)

    def test_name(self):
        func = support.f('a, b, c', name='test_name')
        self.assertEqual(func.__name__, 'test_name')
