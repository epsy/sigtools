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

The ``forwards_to_*`` decorators from this module will leave a "note" on the
decorated object for `sigtools.specifiers.signature` to pick up. These "notes"
tell `signature` in which way the signature of the examinated object
should be crafted. The ``forwards_to_*`` decorators here will help you tell
introspection or documentation tools what the ``*args`` and ``**kwargs``
parameters stand for in your function if it forwards them to another callable.
This should cover most use cases, but you can use `forger_function` or
`set_signature_forger` to create your own.

.. |forwards_params| replace::
    See :ref:`forwards-pick` for more information on the parameters. 

"""

from functools import partial, update_wrapper

from sigtools import _util, modifiers, signatures

__all__ = [
    'signature',
    'forwards_to_function', 'forwards_to_method',
    'forwards_to_super', 'apply_forwards_to_super',
    'forwards',
    'forger_function', 'set_signature_forger',
    ]


_kwowr = modifiers.kwoargs('obj')


signature = _util.forged_signature


def set_signature_forger(obj, forger, emulate=None):
    """Attempts to set the given signature forger on the supplied object.

    This function first tries to set an attribute on ``obj`` and returns it.
    If that fails, it wraps the object that advertises the correct signature (even to `inspect.signature`) and forwards calls.

    :param emulate: If supplied, forces the function to adhere to one strategy:
        either set the attribute or fail(``False``), or always wrap the
        object(``True``). If something else is passed, it is called with
        ``(obj, forger)`` and the return value is used.

    """
    if not emulate:
        try:
            obj._sigtools__forger = forger
            return obj
        except (AttributeError, TypeError):
            if emulate is False:
                raise
    if emulate is None or emulate is True:
        return _ForgerWrapper(obj, forger)
    else:
        return emulate(obj, forger)


def _transform(obj, meta):
    try:
        name = obj.__name__
    except AttributeError:
        return obj
    cls = meta('name', (object,), {name: obj})
    return cls.__dict__[name]


class _ForgerWrapper(object):
    def __init__(self, obj, forger):
        update_wrapper(self, obj)
        self.__wrapped__ = obj
        self._transformed = False
        self._signature_forger = forger
        self.__signature__ = forger(obj=obj)

    def __call__(self, *args, **kwargs):
        return self.__wrapped__(*args, **kwargs)

    def __get__(self, instance, owner):
        if not self._transformed:
            self.__wrapped__ = _transform(self.__wrapped__, type(owner))
            self._transformed = True
        return type(self)(
            _util.safe_get(self.__wrapped__, instance, owner),
            self._signature_forger)


def forger_function(func):
    """Creates a decorator factory which, when applied will set ``func`` as the
    forger function of the decorated object.

    :param callable func: Must return a fake signature for the object passed as
        the named argument ``obj``. Any arguments supplied during decoration
        are also passed.

    The decorator produced by this function also accepts an ``emulate``
    parameter. See `set_signature_forger` for information on it.

    This function can be used as a decorator::

        >>> from sigtools import specifiers, modifiers, support
        >>> @specifiers.forger_function
        ... @modifiers.kwoargs('obj')
        ... def static_signature(obj, sig):
        ...     return sig
        ...
        >>> @static_signature(support.s('a, b, /'))
        ... def my_func(d, e):
        ...     pass
        ...
        >>> print(specifiers.signature(my_func))
        (a, b, /)

    """
    @modifiers.kwoargs('emulate')
    def _apply_forger(emulate=None, *args, **kwargs):
        def _applier(obj):
            return set_signature_forger(
                obj, partial(func, *args, **kwargs), emulate)
        return _applier
    sig = forwards(_apply_forger, func, 0, 'obj')
    update_wrapper(_apply_forger, func, updated=())
    _apply_forger.__signature__ = sig
    return _apply_forger


@modifiers.autokwoargs
def forwards(wrapper, wrapped, *args, **kwargs):
    """Returns an effective signature of ``wrapper`` when it forwards
    its ``*args`` and ``**kwargs`` to ``wrapped``.

    :param callable wrapper: The outer callable
    :param callable wrapped: The callable ``wrapper``'s extra arguments
        are passed to.

    :return: a `inspect.Signature` object

    |forwards_params|

    """
    return signatures.forwards(
        _util.signature(wrapper), signature(wrapped),
        *args, **kwargs)
forwards.__signature__ = forwards(forwards, signatures.forwards, 2)


@_kwowr
def forwards_to_function(obj, *args, **kwargs):
    """Wraps the decorated function to give it the effective signature
    it has when it forwards its ``*args`` and ``**kwargs`` to the static
    callable ``wrapped``.

    ::

        >>> from sigtools.specifiers import forwards_to_function
        >>> def wrapped(x, y):
        ...     return x * y
        ...
        >>> @forwards_to_function(wrapped)
        ... def wrapper(a, *args, **kwargs):
        ...     return a + wrapped(*args, **kwargs)
        ...
        >>> from inspect import signature
        >>> print(signature(wrapper))
        (a, x, y)

    |forwards_params|

    """
    ret = forwards(obj, *args, **kwargs)
    return ret
forwards_to_function.__signature__ = forwards(forwards_to_function,
                                              forwards, 1)
forwards_to_function = forger_function(forwards_to_function)


forwards_to = forwards_to_function


@forger_function
@forwards_to_function(forwards, 2)
@_kwowr
def forwards_to_method(obj, wrapped_name, *args, **kwargs):
    """Wraps the decorated method to give it the effective signature
    it has when it forwards its ``*args`` and ``**kwargs`` to the method
    named by ``wrapped_name``.

    :param str wrapped_name: The name of the wrapped method.

    |forwards_params|

    ::

        >>> from sigtools.specifiers import signature, forwards_to_method
        >>> class Ham(object):
        ...     def egg(self, a, b):
        ...         return a + b
        ...     @forwards_to_method('egg')
        ...     def spam(self, c, *args, **kwargs):
        ...         return c * self.egg(*args, **kwargs)
        ...
        >>> h = Ham()
        >>> print(signature(h.spam))
        (c, a, b)

    """
    try:
        self = obj.__self__
    except AttributeError:
        self = None
    if self is None:
        return _util.signature(obj)
    return forwards(obj, getattr(self, wrapped_name), *args, **kwargs)


forwards_to_ivar = forwards_to_method


def _get_origin_class(obj, cls):
    if cls is not None:
        return cls
    try:
        idx = obj.__code__.co_freevars.index('__class__')
    except ValueError:
        raise ValueError('Class could not be auto-determined.')
    return obj.__closure__[idx].cell_contents


@forger_function
@forwards_to_function(forwards, 2)
@modifiers.kwoargs('obj', 'cls')
def forwards_to_super(obj, cls=None, *args, **kwargs):
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

    |forwards_params|

    """
    try:
        self = obj.__self__
    except AttributeError:
        self = None
    if self is None:
        return _util.signature(obj)
    inner = getattr(
        super(_get_origin_class(obj, cls), self),
        obj.__name__)
    return forwards(obj, inner, *args, **kwargs)


@forwards_to_function(forwards_to_super, 1, 'cls', use_varargs=False)
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

    |forwards_params|

    """
    return partial(_apply_forwards_to_super, member_names,
                   ((0,) + named_args), kwargs)


def _apply_forwards_to_super(member_names, m_args, m_kwargs, cls):
    fts = forwards_to_super(*m_args, cls=cls, **m_kwargs)
    for name in member_names:
        setattr(cls, name, fts(cls.__dict__[name]))
    return cls
