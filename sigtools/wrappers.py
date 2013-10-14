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

"""
`sigtools.wrappers`: Combine multiple functions
-----------------------------------------------

"""

from functools import partial, update_wrapper

from sigtools import _util, signatures, specifiers

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

@specifiers.forwards_to(specifiers.forwards, 2)
def wrapper_decorator(*args, **kwargs):
    """Turns a function into a decorator that wraps callables with
    that function.

    The wrapped function is passed as first argument to the wrapper.

    As an example, here we create an ``@as_json`` decorator which wraps
    the decorated function and serializes the decorated functions's return
    value::

        >>> from sigtools import modifiers, wrappers
        >>> from json import dumps
        >>> @wrappers.wrapper_decorator
        ... @modifiers.autokwoargs
        ... def as_json(func, sort_keys=False, *args, **kwargs):
        ...     return dumps(func(*args, **kwargs), sort_keys=sort_keys)
        ...
        >>> @as_json
        ... def ret_dict(key, val):
        ...     return {key: val}
        ...
        >>> from inspect import signature
        >>> print(signature(ret_dict))
        (key, val, *, sort_keys=False)
        >>> ret_dict('key', 'value')
        '{"key": "value"}'
    """
    if not kwargs and len(args) == 1 and callable(args[0]):
        return _wrapper_decorator((), {}, args[0])
    return partial(_wrapper_decorator, args, kwargs)

def _wrapper_decorator(f_args, f_kwargs, wrapper):
    ret = partial(_wrapper, f_args, f_kwargs, wrapper)
    update_wrapper(ret, wrapper)
    return ret

def _wrapper(f_args, f_kwargs, wrapper, wrapped):
    ret = partial(wrapper, wrapped)
    sig = specifiers.forwards(ret, wrapped, *f_args, **f_kwargs)
    update_wrapper(ret, wrapped)
    ret.__wrapped__ = wrapped # http://bugs.python.org/issue17482
    ret._sigtools__wrapper = wrapper
    ret.__signature__ = sig
    return ret

def wrappers(obj):
    """For introspection purposes, returns an iterable that yields each
    wrapping function of obj(as done through `wrapper_decorator`, outermost
    wrapper first.

    Continuing from the `wrapper_decorator` example::

        >>> list(wrappers.wrappers(ret_dict))
        [<<function as_json at 0x7fc2f76b5a70> with signature as_json(func, *args, sort_
        keys=False, **kwargs)>]

    """
    while hasattr(obj, '_sigtools__wrapper'):
        yield obj._sigtools__wrapper
        if not hasattr(obj, '__wrapped__'):
            return
        obj = obj.__wrapped__
