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


from sigtools._signatures import (
    sort_params, apply_params, IncompatibleSignatures)
from sigtools.support import s
from sigtools._util import OrderedDict

from sigtools.tests.util import SignatureTests, sigtester


class SortParamsTests(SignatureTests):
    def test_empty(self):
        sig = s('')
        self.assertEqual(sort_params(sig), ([], [], None, {}, None))

    def test_collectargs(self):
        sig = s('*args, **kwargs')
        ret = sort_params(sig)
        self.assertEqual(ret[0], [])
        self.assertEqual(ret[1], [])
        self.assertEqual(ret[2].name, 'args')
        self.assertEqual(ret[3], {})
        self.assertEqual(ret[4].name, 'kwargs')

    def test_pos(self):
        sig = s('a, b, /')
        ret = sort_params(sig)
        self.assertEqual(len(ret[0]), 2)
        self.assertEqual(ret[0][0].name, 'a')
        self.assertEqual(ret[0][1].name, 'b')
        self.assertEqual(ret[1:], ([], None, {}, None))

    def test_pok(self):
        sig = s('a, b')
        ret = sort_params(sig)
        self.assertEqual(len(ret[1]), 2)
        self.assertEqual(ret[1][0].name, 'a')
        self.assertEqual(ret[1][1].name, 'b')
        self.assertEqual(ret[0], [])
        self.assertEqual(ret[2:], (None, {}, None))

    def test_order_kwo(self):
        sig = s('*, one, two, three, four, five, six, seven')
        ret = sort_params(sig)
        self.assertEqual(ret[:3], ([], [], None))
        self.assertEqual(
            list(ret[3]),
            ['one', 'two', 'three', 'four', 'five', 'six', 'seven'])
        self.assertEqual(ret[4], None)


def p(sig_str):
    sig = s(sig_str)
    return next(iter(sig.parameters.values()))


class ApplyParamsTests(SignatureTests):
    def test_empty(self):
        self.assertSigsEqual(
            s(''),
            apply_params(s(''), [], [], None, {}, None)
            )

    def test_all(self):
        self.assertSigsEqual(
            s('one, two, /, three, four, *five, six, seven, **eight'),
            apply_params(
                s(''),
                [p('one, /'), p('two, /')],
                [p('three'), p('four')],
                p('*five'),
                OrderedDict(
                    (('six', p('*, six')), ('seven', p('*, seven')))),
                p('**eight')
                )
            )

    def test_roundtrip(self):
        sig_str = 'one, two, /, three, four, *five, six, seven, **eight'
        sig = s(sig_str)
        self.assertEqual(apply_params(s(''), *sort_params(sig)), sig)

@sigtester
def test_exc(self, sig_str, sigs_strs, expected):
    sig = s(sig_str)
    sigs = [s(sig_str_) for sig_str_ in sigs_strs]
    exc = IncompatibleSignatures(sig, sigs)
    self.assertEqual(expected, str(exc))

@test_exc
class ExcTests(object):
    one = 'a, b', ['c, d'], '(c, d) (a, b)'
    two = 'a, b', ['c, d', 'e, f'], '(c, d) (e, f) (a, b)'
