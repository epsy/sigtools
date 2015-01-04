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

from functools import update_wrapper
from weakref import WeakKeyDictionary


def get_funcsigs():
    import inspect
    try:
        inspect.signature
    except AttributeError:
        import funcsigs
        return funcsigs
    else:
        return inspect
funcsigs = get_funcsigs()


try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict


class _Unset(object):
    __slots__ = ()
    def __repr__(self):
        return '<unset>'
UNSET = _Unset()
del _Unset

def noop(func):
    return func

def qualname(obj):
    try:
        return obj.__qualname__
    except AttributeError:
        try:
            return '{0.__module__}.{0.__name__}'.format(obj)
        except AttributeError:
            return repr(obj)

class OverrideableDataDesc(object):
    def __init__(self, *args, **kwargs):
        original = kwargs.pop('original', None)
        if original is not None:
            update_wrapper(self, original)
        try:
            self.custom_getter = kwargs.pop('get')
        except KeyError:
            def cg(func, **kwargs):
                kwargs.update(self.parameters())
                return type(self)(func, **kwargs)
            self.custom_getter = cg
        self.insts = WeakKeyDictionary()
        super(OverrideableDataDesc, self).__init__(*args, **kwargs)

    def __get__(self, instance, owner):
        try:
            getter = type(self.func).__get__
        except AttributeError:
            return self
        else:
            func = getter(self.func, instance, owner)

        try:
            return self.insts[func]
        except KeyError:
            pass

        if func is self.func:
            ret = self
        else:
            ret = self.custom_getter(func, original=self)
        self.insts[func] = ret
        return ret

def safe_get(obj, instance, owner):
    try:
        get = type(obj).__get__
    except (AttributeError, KeyError):
        return obj
    return get(obj, instance, owner)
