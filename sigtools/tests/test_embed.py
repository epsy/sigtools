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


from sigtools.signatures import signature, embed, IncompatibleSignatures
from sigtools.support import f, s
from sigtools.tests.util import Fixtures


class EmbedTests(Fixtures):
    def _test(self, result, exp_src, *signatures):
        assert len(signatures) >= 2
        sigs = []
        for i, sig_str in enumerate(signatures, 1):
            func = f(sig_str)
            func.__name__ = str(i)
            sigs.append(signature(func))
        sig = embed(*sigs)
        self.assertSigsEqual(sig, s(result))
        self.assertSourcesEqual(None, sig.sources, exp_src)

    passthrough_pos = '<a>', {2: 'a'}, '*args, **kwargs', '<a>'
    passthrough_pok = 'a', {2: 'a'}, '*args, **kwargs', 'a'
    passthrough_kwo = '*, a', {2: 'a'}, '*args, **kwargs', '*, a'

    add_pos_pos = '<a>, <b>', {1: 'a', 2: 'b'}, '<a>, *args, **kwargs', '<b>'
    add_pos_pok = '<a>, b', {1: 'a', 2: 'b'}, '<a>, *args, **kwargs', 'b'
    add_pos_kwo = '<a>, *, b', {1: 'a', 2: 'b'}, '<a>, *args, **kwargs', '*, b'

    add_pok_pos = '<a>, <b>', {1: 'a', 2: 'b'}, 'a, *args, **kwargs', '<b>'
    add_pok_pok = 'a, b', {1: 'a', 2: 'b'}, 'a, *args, **kwargs', 'b'
    add_pok_kwo = 'a, *, b', {1: 'a', 2: 'b'}, 'a, *args, **kwargs', '*, b'

    add_kwo_pos = '<b>, *, a', {1: 'a', 2: 'b'}, '*args, a, **kwargs', '<b>'
    add_kwo_pok = 'b, *, a', {1: 'a', 2: 'b'}, '*args, a, **kwargs', 'b'
    add_kwo_kwo = '*, a, b', {1: 'a', 2: 'b'}, '*args, a, **kwargs', '*, b'

    conv_pok_pos = '<a>', {2: 'a'}, '*args', 'a'
    conv_pok_kwo = '*, a', {2: 'a'}, '**kwargs', 'a'

    three = (
        'a, b, c', {1: 'a', 2: 'b', 3: 'c'},
        'a, *args, **kwargs', 'b, *args, **kwargs', 'c')


class EmbedRaisesTests(Fixtures):
    def _test(self, *signatures):
        assert len(signatures) >= 2
        sigs = [s(sig) for sig in signatures]
        self.assertRaises(IncompatibleSignatures, embed, *sigs)

    no_placeholders_pos = '', '<a>'
    no_placeholders_pok = '', 'a'
    no_placeholders_kwo = '', '*, a'

    no_args_pos = '**kwargs', '<a>'

    dup_pos_pos = '<a>, *args, **kwargs', '<a>'
