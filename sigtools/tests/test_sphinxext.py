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

from sigtools import sphinxext
from sigtools.tests import sphinxextfixt


app = object()


class SphinxExtTests(unittest.TestCase):
    def test_forge(self):
        r = sphinxext.process_signature(
            app, 'function', 'sigtools.tests.sphinxextfixt.outer',
            sphinxextfixt.outer, {}, '(c, *args, **kwargs)', None)
        self.assertEqual(('(c, a, b)', ''), r)

    def test_method_forge(self):
        r = sphinxext.process_signature(
            app, 'method', 'sigtools.tests.sphinxextfixt.AClass.outer',
            sphinxextfixt.AClass.outer, {}, '(c, *args, **kwargs)', None)
        self.assertEqual(('(c, a, b)', ''), r)

    def test_modifiers(self):
        r = sphinxext.process_signature(
            app, 'function', 'sigtools.tests.sphinxextfixt.kwo',
            sphinxextfixt.AClass.outer, {}, '(a, b, c=1, d=2)', None)
        self.assertEqual(('(a, b, *, c=1, d=2)', ''), r)

    def test_attribute(self):
        r = sphinxext.process_signature(
            app, 'attribute', 'sigtools.tests.sphinxextfixt.AClass.class_attr',
            sphinxextfixt.AClass.class_attr, {}, None, None)
        self.assertEqual((None, None), r)

    def test_inst_attr(self):
        r = sphinxext.process_signature(
            app, 'attribute', 'sigtools.tests.sphinxextfixt.AClass.abc',
            None, {}, None, None)
        self.assertEqual((None, None), r)
