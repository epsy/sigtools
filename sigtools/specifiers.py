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

"""Tools to specify the significance of extra argument receivers."""

from functools import partial, update_wrapper

from sigtools import _util, modifiers, signatures

__all__ = [
    'forwards_to', 'forwards_to_ivar',
    'forwards_to_super', 'apply_forwards_to_super',
    'forwards'
    ]

share_kwoarg = modifiers.kwoargs('share')

@share_kwoarg
def forwards(wrapper, share=(), *wrapped):
    """Returns an effective signature of wrapper when it forwards
    its ``*args`` and ``**kwargs`` to every function in wrapped.

    :param sequence share: Parameter names from the wrapper that are
        forwarded as well as ``*args``, ``**kwargs``
    """
    inner_sig = signatures.merge(*(_util.signature(func) for func in wrapped))
    return signatures.embed(
        _util.signature(wrapper), inner_sig, share=share)

@modifiers.kwoargs('share', 'get_wrapped')
def forwards_to(share=(), get_wrapped=True, *wrapped):
    """Wraps the decorated function to give it the effective signature
    it has when it forwards its ``*args`` and ``**kwargs`` to every
    function in wrapped.

    :param sequence share: Parameter names from the wrapper that are
        forwarded as well as ``*args``, ``**kwargs``

    Example::

        >>> from sigtools.specifiers import forwards_to
        >>> def wrapped(x, y):
        ...     return x * y
        ...
        >>> @forwards_to(wrapped)
        ... def wrapper(a, *args, **kwargs):
        ...     return a + wrapped(*args, **kwargs)
        ...
        >>> from inspect import signature
        >>> print(signature(wrapper))
        (a, x, y)

    Using the share parameter::

        >>> from sigtools.specifiers import forwards_to
        >>> class A:
        ...     def wrapped(self, x, y):
        ...         return x * y
        ...     @forwards_to(wrapped, share=('self'))
        ...     def wrapper(self, a, *args, **kwargs):
        ...         return a + self.wrapped(*args, **kwargs)
        ...
        >>> from inspect import signature
        >>> print(signature(A.wrapper))
        (self, a, x, y)
        >>> print(signature(A().wrapper))
        (a, x, y)

    """
    return partial(_ForwardsTo, wrapped, share, get_wrapped)

class _ForwardsTo(object):
    def __init__(self, wrapped, share, get_wrapped, wrapper):
        update_wrapper(self, wrapper)
        self.wrapped = wrapped
        self.wrapper = wrapper
        self.get_wrapped = get_wrapped
        self.share = share
        self.__signature__ = forwards(wrapper, *wrapped, share=share)

    def __get__(self, instance, owner):
        new_wrapper = self.wrapper.__get__(instance, owner)
        if self.get_wrapped:
            new_wrapped = [
                wrapped.__get__(instance, owner)
                for wrapped in self.wrapped]
        if new_wrapper == self.wrapper and new_wrapped == self.wrapped:
            return self
        return type(self)(new_wrapped, self.share, self.get_wrapped,
                          new_wrapper)

    def __call__(self, *args, **kwargs):
        return self.wrapper(*args, **kwargs)

@share_kwoarg
def forwards_to_ivar(share=(), *wrapped_names):
    """Wraps the decorated method to give it the effective signature it has
    when it forwards its ``*args`` and ``**kwargs`` to the named instance
    variables.
    """
    return partial(_ForwardsToIvar, wrapped_names, share=share)

class _ForwardsToIvar(object):
    def __init__(self, wrapped, wrapper, share):
        self.wrapped = wrapped
        self.wrapper = wrapper
        self.share = share
        update_wrapper(self, self.wrapped)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return _ForwardsTo(
            [getattr(instance, name) for name in self.wrapped],
            self.wrapper, self.share)

    def __call__(self, *args, **kwargs):
        return self.wrapped(*args, **kwargs)

@share_kwoarg
def forwards_to_super(share=('self')):
    """Wraps the decorated method to give it the effective signature it has
    when it forwards its ``*args`` and ``**kwargs`` to the same method on
    the super object for the class it belongs in.

    You can only use this decorator directly in Python versions 3.3 and up,
    and the wrapped function must make use of the arg-less form of super::

        >>> from sigtools.specifiers import forwards_to_super
        >>> class Base:
        ...     def func(self, x, y):
        ...         return x * y
        ...
        >>> class Subclass(Base):
        ...     @forwards_to_super()
        ...     def func(self, a, *args, **kwargs):
        ...         return a + super().func(*args, **kwargs)
        ...
        >>> from inspect import signature
        >>> print(signature(Subclass.func))
        (self, a, x, y)
        >>> print(signature(Subclass().func))
        (a, x, y)

    If you need to use similar functionality in older python versions, use
    :func:`apply_forwards_to_super` instead.

    """
    return partial(_ForwardsToSuper, share)

class _ForwardsToSuper(object):
    def __init__(self, share, wrapper, cls=None):
        self.share = share
        self.wrapper = wrapper
        self.cls = cls
        update_wrapper(self, wrapper)

    def get_class(self):
        if self.cls is None:
            try:
                idx = self.wrapper.__code__.co_freevars.index('__class__')
            except IndexError:
                raise ValueError('Class could not be auto-determined.')
            self.cls = self.wrapper.__closure__[idx].cell_contents
        return self.cls

    def get_super(self, instance, owner):
        cls = self.get_class()
        if instance is not None:
            return super(cls, instance)
        else:
            return super(cls, owner)

    def __get__(self, instance, owner): #FIXME this is run too often
        wrapper = self.wrapper.__get__(instance, owner)
        wrapped = getattr(self.get_super(instance, owner),
                          self.wrapper.__name__)
        return _ForwardsTo((wrapped,), self.share, True, wrapper)

@share_kwoarg
def apply_forwards_to_super(share={}, *member_names):
    """Applies the :func:`forwards_to_super` decorator on
    ``member_names`` in the decorated class, in a way which
    works in Python 2.6 and up.

        >>> from sigtools.specifiers import apply_forwards_to_super
        >>> class Base:
        ...     def func(self, x, y):
        ...         return x * y
        ...
        >>> @apply_forwards_to_super('func')
        ... class Subclass(Base):
        ...     def func(self, a, *args, **kwargs):
        ...         return a + super(Subclass, self).func(*args, **kwargs)
        ...
        >>> from inspect import signature
        >>> print(signature(Subclass.func))
        (self, a, x, y)
        >>> print(signature(Subclass().func))
        (a, x, y)

    """
    return partial(_apply_forwards_to_super, member_names, share)

def _apply_forwards_to_super(member_names, share, cls):
    for name in member_names:
        setattr(cls, name, _ForwardsToSuper(
            share.get(name, ('self',)), cls.__dict__[name], cls))
    return cls
