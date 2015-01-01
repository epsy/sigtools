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

from sigtools import signatures, support
from sigtools.tests.util import sigtester

@sigtester
def mask_tests(self, expected_str, sig_str, num_args=0, named_args=(),
               hide_varargs=False, hide_varkwargs=False):
    self.assertSigsEqual(
        support.s(expected_str),
        signatures.mask(
            support.s(sig_str), num_args, *named_args,
            hide_varargs=hide_varargs, hide_varkwargs=hide_varkwargs))

@mask_tests
class MaskTests(object):
    hide_pos = '<b>', '<a>, <b>', 1
    hide_pos_pok = 'c', '<a>, b, c', 2

    eat_into_varargs = '*args', 'a, *args', 2

    name_pok_last = 'a, b', 'a, b, c', 0, 'c'
    name_pok = 'a, *, c', 'a, b, c', 0, 'b'
    name_pok_last_hide_va = 'a, b', 'a, b, c, *args', 0, 'c'
    name_pok_hide_va = 'a, *, c', 'a, b, c, *args', 0, 'b'

    name_kwo = 'a', 'a, *, b', 0, 'b'

    name_varkwargs = '**kwargs', '**kwargs', 0, 'a'
    name_varkwargs_hide = '', '**kwargs', 0, 'a', False, True

    hide_varargs = 'a, b, *, c', 'a, b, *args, c', 0, '', True, False
    eat_into_varargs_hide = '', 'a, *args', 2, '', True, False

    hide_varargs_absent = '', '', 0, '', True, False
    hide_varkwargs_absent = '', '', 0, '', False, True



@sigtester
def mask_raise_tests(self, sig_str, num_args, named_args=(),
                     hide_varargs=False, hide_varkwargs=False):
    sig = support.s(sig_str)
    try:
        signatures.mask(
            sig, num_args, *named_args,
            hide_varargs=hide_varargs, hide_varkwargs=hide_varkwargs)
    except ValueError:
        pass
    else:
        self.fail('ValueError not raised by mask({0}, {1}, *{2}, '
                  'hide_varargs={3}, hide_varkwargs={4})'.format(
                  sig, num_args, named_args, hide_varargs, hide_varkwargs
                  ))

@mask_raise_tests
class MaskRaiseTests(object):
    no_pos_1 = '', 1
    no_pos_2 = '<a>', 2

    no_pok_2 = 'a', 2
    no_pos_pok_3 = '<a>, b', 3

    key_is_pos = '<a>', 0, 'a'
    key_absent = '', 0, 'a'

    key_twice = 'a', 0, 'aa'
    pos_and_key = 'a', 1, 'a'



if __name__ == '__main__':
    unittest.main()
