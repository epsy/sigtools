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


import unittest2

from sigtools.support import s
from sigtools.tests import util as tutil


class UtilTests(unittest2.TestCase):
    def test_conv_first_posarg(self):
        self.assertEqual(s(''), tutil.conv_first_posarg(s('')))
        self.assertEqual(
            s('one, /, two, *three, four, **five'),
            tutil.conv_first_posarg(s('one, two, *three, four, **five')))


class SignatureTestsTests(tutil.SignatureTests):
    def test_sigs_equal(self):
        self.assertSigsEqual(s('one'), s('one'))
        self.assertSigsEqual(s('*, one'), s('*, one'))

        with self.assertRaises(AssertionError):
            self.assertSigsEqual(s('one'), s('two'))
        with self.assertRaises(AssertionError):
            self.assertSigsEqual(s('one'), s('*, one'))

    def test_sigs_equal_conv_first(self):
        self.assertSigsEqual(s('self, /, one'), s('self, one'),
                             conv_first_posarg=True)
        self.assertSigsEqual(s('self, one'), s('self, /, one'),
                             conv_first_posarg=True)
        self.assertSigsEqual(s('self, /, *, one'), s('self, *, one'),
                             conv_first_posarg=True)
        self.assertSigsEqual(s('self, *, one'), s('self, /, *, one'),
                             conv_first_posarg=True)

        with self.assertRaises(AssertionError):
            self.assertSigsEqual(s('self, /, one'), s('self, two'),
                                 conv_first_posarg=True)
        with self.assertRaises(AssertionError):
            self.assertSigsEqual(s('self, /, one'), s('self, *, one'),
                                 conv_first_posarg=True)

    def test_assertIs(self):
        self.assertIs(*([],)*2)
        with self.assertRaises(AssertionError):
            self.assertIs([], [])
