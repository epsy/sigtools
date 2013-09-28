# sigtools - Python module to manipulate function signatures
# Copyright (c) 2013 Yann Kaiser
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

from sigtools import _util, signatures

class Combination(object):
    """Creates a callable that passes the first argument through each
    callable, using the result of each pass as the argument to the next
    """
    def __init__(self, *functions):
        funcs = self.functions = []
        for function in functions:
            if isinstance(function, Combination):
                funcs.extend(function.functions)
            else:
                funcs.append(function)
        self.__signature__ = signatures.merge(
            _util.signature(self),
            *(_util.signature(func) for func in funcs))

    def __call__(self, arg, *args, **kwargs):
        for function in self.functions:
            arg = function(arg, *args, **kwargs)
        return arg

    def __repr__(self):
        return '{0.__module__}.{0.__name__}({1})'.format(
            type(self), ', '.join(repr(f) for f in self.functions)
            )
