#!/usr/bin/env python
import unittest

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
    try:
        merge(*sigs)
    except IncompatibleSignatures as e:
        str(e)
    else:
        self.fail('IncompatibleSignatures not raised when merging '
            + ' '.join(str(sig) for sig in sigs)) #pragma: no cover

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

    pokarg_convert_name = '<a>', 'a', 'b'

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

# @sigtester
# def merge_ignore_tests(self, expected_sig_str, ignore, *sig_strs):
#     assert len(sig_strs) >= 2
#     sigs = [s(sig_str) for sig_str in sig_strs]
#     self.assertSigsEqual(
#         s(expected_sig_str),
#         merge(*sigs, ignore=ignore)
#         )
# 
# @merge_ignore_tests
# class MergeIgnoreTests(object):
#     ignore_pos_pos = '', 'a', '<a>', '<a>'
#     ignore_pos_pok = '', 'a', '<a>', 'a'
#     ignore_pos_kwo = '', 'a', '<a>', '*, a'
# 
#     ignore_pok_pos = '', 'a', 'a', '<a>'
#     ignore_pok_pok = '', 'a', 'a', 'a'
#     ignore_pok_kwo = '', 'a', 'a', '*, a'
# 
#     ignore_kwo_pos = '', 'a', '*, a', '<a>'
#     ignore_kwo_pok = '', 'a', '*, a', 'a'
#     ignore_kwo_kwo = '', 'a', '*, a', '*, a'

if __name__ == '__main__':
    unittest.main()
