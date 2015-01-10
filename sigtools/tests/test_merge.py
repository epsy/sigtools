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


from sigtools.signatures import merge, IncompatibleSignatures
from sigtools.support import s
from sigtools.tests.util import sigtester


@sigtester
def merge_tests(self, result, *signatures):
    assert len(signatures) >= 2
    sigs = [s(sig) for sig in signatures]
    self.assertSigsEqual(
        merge(*sigs),
        s(result)
        )

@sigtester
def merge_raise_tests(self, *signatures):
    assert len(signatures) >= 2
    sigs = [s(sig) for sig in signatures]
    self.assertRaises(IncompatibleSignatures, merge, *sigs)

@merge_tests
class MergeTests(object):
    posarg_default_erase = '', '', '<a>=1'
    posarg_stars = '<a>', '*args', '<a>'

    posarg_convert = '<a>', '<a>', 'b'
    posarg_convert_left = '<a>', 'a', '<b>'

    pokarg_default_erase = '', '', 'a=1'

    pokarg_star_convert_pos = '<a>', '*args', 'a'
    pokarg_star_convert_kwo = '*, a', '**kwargs', 'a'
    pokarg_star_keep = 'a', '*args, **kwargs', 'a'

    pokarg_rename = '<a>', 'a', 'b'
    pokarg_rename_second = '<a>, <b>', 'a, b', 'a, c'

    pokarg_found_kwo = '*, a', '*, a', 'a'
    pokarg_found_kwo_r = '*, a', 'a', '*, a'

    kwarg_default_erase = '', '', '*, a=1'
    kwarg_stars = '*, a=1', '**kwargs', '*, a=1'

    kwoarg_same = '*, a', '*, a', '*, a'
    posarg_same = '<a>', '<a>', '<a>'
    pokarg_same = 'a', 'a', 'a'

    default_same = 'a=1', 'a=1', 'a=1'
    default_diff = 'a=None', 'a=1', 'a=2'
    default_one = 'a', 'a=1', 'a'
    default_one_r = 'a', 'a', 'a=1'

    annotation_both_diff = 'a', 'a:1', 'a:2'
    annotation_both_same = 'a:1', 'a:1', 'a:1'
    annotation_left = 'a:1', 'a:1', 'a'
    annotation_right = 'a:1', 'a', 'a:1'

    star_erase = '', '*args', ''
    star_same = '*args', '*args', '*args'
    star_extend = '<a>, *args', '*args', '<a>, *args'

    stars_erase = '', '**kwargs', ''
    stars_same = '**kwargs', '**kwargs', '**kwargs'
    star_extend = '*, a, **kwargs', '**kwargs', '*, a, **kwargs'

@merge_raise_tests
class MergeRaiseTests(object):
    posarg_raise = '', '<a>'
    pokarg_raise = '', 'a'

    kwarg_raise = '*, a', ''
    kwarg_r_raise = '', '*, a'
