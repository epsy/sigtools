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


from sigtools.signatures import forwards
from sigtools.support import s

from sigtools.tests.util import Fixtures


class ForwardsTests(Fixtures):
    def _test(self, exp_sig, exp_src, outer, inner,
                    num_args=0, named_args=(),
                    hide_args=False, hide_kwargs=False,
                    use_varargs=True, use_varkwargs=True):
        sig = forwards(
                    s(outer, name='o'), s(inner, name='i'),
                    num_args, *named_args,
                    hide_args=hide_args, hide_kwargs=hide_kwargs,
                    use_varargs=use_varargs, use_varkwargs=use_varkwargs)
        self.assertSigsEqual(sig, s(exp_sig))
        self.assertSourcesEqual(sig.sources, {
                'o': exp_src[0], 'i': exp_src[1]})

    a = 'a, b', ['a', 'b'], 'a, *args, **kwargs', 'b'

    pass_pos = 'a, c', ['a', 'c'], 'a, *p, **k', 'b, c', 1
    pass_kw = 'a, *, c', ['a', 'c'], 'a, *p, **k', 'b, c', 0, 'b'

    dont_use_varargs = (
        'a, *p, b', ['ap', 'b'], 'a, *p, **k', 'b',
        0, (), False, False, False, True)

    through_kw = (
        'a, b, *, z', ['ab', 'z'], 'a, b, **k', 'x, y, *, z', 2, (), True)

    kwo = 'x, y, /, *, k', ['k', 'xy'], '*args, k', 'x, y, *, z', 0, 'z'
