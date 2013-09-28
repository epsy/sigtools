
import unittest
from functools import partial

from sigtools import _util

class BindingPartial(object):
    def __init__(self, __func, *args, **kwargs):
        self.func = __func
        self.args = args
        self.kwargs = kwargs

    def __get__(self, instance, owner):
        return type(self)(
            self.func.__get__(instance, owner),
            *self.args, **self.kwargs)

    def __call__(self, *args, **kwargs):
        kwargs_ = dict(self.kwargs)
        kwargs_.update(kwargs)
        return self.func(*(self.args + args), **kwargs_)

class SignatureTests(unittest.TestCase):
    def format_func(self, func, args=None, kwargs=None):
        if args is not None and kwargs is not None:
            return '{0}{1} <- *{2}, **{3}'.format(
                _util.qualname(func), _util.signature(func),
                args, kwargs)
        else:
            return '{0}{1}'.format(
                _util.qualname(func), _util.signature(func),
                )

    def assertSigsEqual(self, left, right, *args, **kwargs):
        if left != right:
            raise AssertionError('{0} != {1}'.format(left, right))
        self.assertEqual(left, right, *args, **kwargs)

def make_run_test(func, value, **kwargs):
    def _func(self):
        return func(self, *value, **kwargs)
    return _func

def build_sigtests(func, cls):
    members = {}
    for key, value in cls.__dict__.items():
        if key.startswith('test_') or key.startswith('_'):
            members[key] = value
        else:
            members['test_' + key] = make_run_test(func, value)
    return type(cls.__name__, (SignatureTests, unittest.TestCase), members)

def sigtester(test_func):
    return partial(build_sigtests, test_func)
