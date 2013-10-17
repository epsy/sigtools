#!/usr/bin/env python

import unittest

from sigtools import signatures, test
from test.util import sigtester

@sigtester
def mask_tests(self, expected_str, sig_str, num_args=0, named_args=(),
               hide_varargs=False, hide_varkwargs=False):
    self.assertSigsEqual(
        test.s(expected_str),
        signatures.mask(
            test.s(sig_str), num_args, *named_args,
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
    sig = test.s(sig_str)
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
