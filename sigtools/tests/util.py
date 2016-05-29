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


from collections import defaultdict
from functools import partial

import unittest2
from repeated_test import tup, WithTestClass

from sigtools._util import funcsigs


__all__ = [
    'conv_first_posarg',
    'transform_exp_sources', 'transform_real_sources',
    'SignatureTests', 'Fixtures', 'tup'
    ]


def conv_first_posarg(sig):
    if not sig.parameters:
        return sig
    first = list(sig.parameters.values())[0]
    first = first.replace(kind=first.POSITIONAL_ONLY)
    return sig.replace(
        parameters=(first,) + tuple(sig.parameters.values())[1:])


def func_to_name(func):
    if isinstance(func, partial):
        return 'functoolspartial_' + str(id(func)) + '_' + func_to_name(func.func)
    try:
        return func.__name__
    except AttributeError:
        s = str(func)
        if s != func:
            return '_' + s
        return s


def transform_exp_sources(d, subject=None):
    ret = defaultdict(list)
    funclist = []
    subject_name = None if subject is None else func_to_name(subject)
    for func, params in d.items():
        if func == '+depths':
            continue
        if func == 0:
            if subject is None:
                raise ValueError(
                    "Used implicit function with no provided subject")
            func = subject
        func = func_to_name(func)
        funclist.append(func)
        for param in params:
            ret[param].append(func)
    if '+depths' not in d:
        val = sorted(funclist)
        if subject is not None:
            try:
                val.remove(subject_name)
            except ValueError:
                pass
            val.insert(0, subject_name)
    else:
        val = d['+depths']
    if isinstance(val, list):
        val = dict((func_to_name(f), i) for i, f in enumerate(val))
    else:
        val = dict((func_to_name(f), v) for f, v in val.items())
    ret['+depths'] = val
    return dict(ret)


def transform_real_sources(d):
    ret = {}
    for param, funcs in d.items():
        if param == '+depths':
            ret[param] = dict(
                (func_to_name(func), v) for func, v in funcs.items())
        else:
            ret[param] = [func_to_name(func) for func in funcs]
    return ret


class SignatureTests(unittest2.TestCase):
    maxDiff = None

    def assertSigsEqual(self, found, expected, *args, **kwargs):
        conv = kwargs.pop('conv_first_posarg', False)
        if expected != found:
            if conv:
                expected = conv_first_posarg(expected)
                found = conv_first_posarg(found)
                if expected == found:
                    return
            raise AssertionError(
                'Did not get expected signature({0}), got {1} instead.'
                .format(expected, found))

    def assertSourcesEqual(self, found, expected, func=None, depth_order=False):
        r = transform_real_sources(found)
        e = transform_exp_sources(expected, func)
        if depth_order:
            rd = r.pop('+depths')
            ed = e.pop('+depths')
        self.assertEqual(r, e)
        if depth_order:
            self.assertEqual(
                [f for f in sorted(rd, key=rd.get) if f in ed],
                [f for f in sorted(ed, key=ed.get)])

    def downgrade_sig(self, sig):
        return funcsigs.Signature(
            sig.parameters.values(),
            return_annotation=sig.return_annotation)


Fixtures = WithTestClass(SignatureTests)
