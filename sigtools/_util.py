
from functools import partial
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
signature = funcsigs.signature

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
        return '{0.__module__}.{0.__name__}'.format(obj)

class RoProxy(object):
    """Read-only proxy with extra attributes"""

    def __init__(self, subject, **attrs):
        """Proxies subject with attrs as extra attributes"""
        self.__subject = subject
        for key, value in attrs.items():
            setattr(self, key, value)

    def __getattr__(self, attr):
        return getattr(self.__subject, attr)

class OverrideableDataDesc(object):
    def __init__(self, *args, **kwargs):
        try:
            self.custom_getter = kwargs.pop('get')
        except KeyError:
            self.custom_getter = partial(type(self), **self.parameters())
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
            ret = self.custom_getter(func)
        self.insts[func] = ret
        return ret
