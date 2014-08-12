
from functools import partial, update_wrapper
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

def get_ordereddict_or_dict():
    import collections
    try:
        return collections.OrderedDict
    except AttributeError:
        return dict
dod = get_ordereddict_or_dict()

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
