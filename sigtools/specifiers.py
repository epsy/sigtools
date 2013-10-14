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
`sigtools.specifiers`: Decorators to enhance a callable's signature
-------------------------------------------------------------------

"""

from functools import partial, update_wrapper
import operator

from sigtools import _util, modifiers, signatures

__all__ = [
    'forwards',
    'forwards_to', 'forwards_to_method',
    'forwards_to_super', 'apply_forwards_to_super', 'forwards_to_ivar',
    ]

def forwards(wrapper, wrapped, *args, **kwargs):
    """Returns an effective signature of ``wrapper`` when it forwards
    its ``*args`` and ``**kwargs`` to ``wrapped``.

    :param callable wrapper: The outer callable
    :param callable wrapped: The callable ``wrapper``'s extra arguments
        are passed to.

    See `sigtools.signatures.mask` for the other parameters' documentation.
    """
    return signatures.embed(
        _util.signature(wrapper),
        signatures.mask(_util.signature(wrapped), *args, **kwargs))
forwards.__signature__ = forwards(forwards, signatures.mask)

class _ProxyForwardsTo(object):
    def __init__(self, forwards_inst, wrapper, sig):
        update_wrapper(self, wrapper)
        self.__forwards_inst = forwards_inst
        self.__wrapper = wrapper
        self.__signature__ = sig

    def __call__(self, *args, **kwargs):
        return self.__wrapper(*args, **kwargs)

    def __get__(self, instance, owner):
        return type(self.__forwards_inst).__get__(
            self.__forwards_inst, instance, owner)

class _BaseForwardsTo(object):
    def __init__(self, wrapped, m_args, m_kwargs, wrapper):
        update_wrapper(self, wrapper)
        self.wrapped = wrapped
        self.wrapper = wrapper
        self.m_args = m_args
        self.m_kwargs = m_kwargs

    def _forwards(self, wrapper, wrapped, **kwargs):
        return _ProxyForwardsTo(
            self, wrapper, self._signature(wrapper, wrapped, **kwargs))

    def _signature(self, wrapper, wrapped):
        return forwards(wrapper, wrapped, *self.m_args, **self.m_kwargs)

    def __get__(self, instance, owner):
        return self.get(instance, owner)

class _ForwardsTo(_BaseForwardsTo):
    def __init__(self, *args, **kwargs):
        super(_ForwardsTo, self).__init__(*args, **kwargs)
        self.__signature__ = self._signature(self.wrapper, self.wrapped)

    def get(self, instance, owner):
        wrapper = _util.safe_get(self.wrapper, instance, owner)
        return self._forwards(wrapper, self.wrapped)

    def __call__(self, *args, **kwargs):
        return self.wrapper(*args, **kwargs)

def forwards_to(wrapped, *args, **kwargs):
    """Wraps the decorated function to give it the effective signature
    it has when it forwards its ``*args`` and ``**kwargs`` to the static
    callable wrapped.

    ::

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

    """
    return partial(_ForwardsTo, wrapped, args, kwargs)
forwards_to.__signature__ = forwards(forwards_to, signatures.mask)

class _ForwardsToMethod(_BaseForwardsTo):
    def get(self, instance, owner):
        wrapper = _util.safe_get(self.wrapper, instance, owner)
        wrapped = getattr(owner, self.wrapped)
        if instance is not None:
            wrapped = _util.safe_get(wrapped, instance, owner)
        else:
            wrapped = _util.safe_get(wrapped, object(), owner)
        return self._forwards(wrapper, wrapped)

@forwards_to(signatures.mask)
def forwards_to_method(wrapped_name, *args, **kwargs):
    """Wraps the decorated method to give it the effective signature
    it has when it forwards its ``*args`` and ``**kwargs`` to the method
    named by ``wrapped_name``.

    :param str wrapped_name: The name of the wrapped method.
    """
    return partial(_ForwardsToMethod,
                   wrapped_name, args, kwargs)

class _ForwardsToIvar(_BaseForwardsTo):
    def __get__(self, instance, owner):
        wrapper = _util.safe_get(self.wrapper, instance, owner)
        if instance is None:
            return wrapper
        else:
            return self._forwards(wrapper, self.wrapped(instance))

@forwards_to(signatures.mask)
def forwards_to_ivar(wrapped_name, *args, **kwargs):
    """Wraps the decorated method to give it the effective signature it has
    when it forwards its ``*args`` and ``**kwargs`` to the named instance
    variables.

    :param str wrapped_name: The name of the wrapped instance variable.
    """
    return partial(_ForwardsToIvar,
                   operator.attrgetter(wrapped_name), args, kwargs)

class _ForwardsToSuper(_BaseForwardsTo):
    def __init__(self, cls, m_args, m_kwargs, wrapper):
        update_wrapper(self, wrapper)
        self.wrapper = wrapper
        self.cls = cls
        self.m_args = m_args
        self.m_kwargs = m_kwargs

    def get_class(self, owner):
        if self.cls is None:
            func = _util.safe_get(self.wrapper, None, owner)
            try:
                idx = func.__code__.co_freevars.index('__class__')
            except ValueError:
                raise ValueError('Class could not be auto-determined.')
            self.cls = func.__closure__[idx].cell_contents
        return self.cls

    def get_super(self, instance, owner):
        cls = self.get_class(owner)
        if instance is None:
            return super(cls, owner)
        else:
            return super(cls, instance)

    def get_wrapped(self, wrapper, instance, owner):
        wrapped = getattr(self.get_super(None, owner), wrapper.__name__)
        if instance is None:
            return _util.safe_get(wrapped, object(), owner)
        else:
            return _util.safe_get(wrapped, instance, owner)

    def __get__(self, instance, owner):
        wrapper = _util.safe_get(self.wrapper, instance, owner)
        wrapped = self.get_wrapped(wrapper, instance, owner)
        return self._forwards(wrapper, wrapped)

@forwards_to(signatures.mask)
def forwards_to_super(*args, **kwargs):
    """Wraps the decorated method to give it the effective signature it has
    when it forwards its ``*args`` and ``**kwargs`` to the same method on
    the super object for the class it belongs in.

    You can only use this decorator directly in Python versions 3.3 and up,
    and the wrapped function must make use of the arg-less form of super::

        >>> from sigtools.specifiers import forwards_to_super
        >>> class Base:
        ...     def func(self, x, y):
        ...         return x * y
        ..
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
    `apply_forwards_to_super` instead.

    """
    return partial(_ForwardsToSuper, None, args, kwargs)

#@forwards_to(signatures.mask, 2, hide_varargs=True)
@modifiers.autokwoargs
def apply_forwards_to_super(num_args=0, named_args=(), *member_names,
                            **kwargs):
    """Applies the `forwards_to_super` decorator on
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
    return partial(_apply_forwards_to_super, member_names,
                   ((0,) + named_args), kwargs)

def _apply_forwards_to_super(member_names, m_args, m_kwargs, cls):
    for name in member_names:
        setattr(cls, name,
            _ForwardsToSuper(
                cls, m_args, m_kwargs,
                cls.__dict__[name]))
    return cls

