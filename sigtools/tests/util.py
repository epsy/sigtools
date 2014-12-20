
import unittest
from functools import partial

from sigtools import _util

def conv_first_posarg(sig):
    if not sig.parameters:
        return sig
    first = list(sig.parameters.values())[0]
    first = first.replace(kind=first.POSITIONAL_ONLY)
    return sig.replace(
        parameters=(first,) + tuple(sig.parameters.values())[1:])

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

    def assertSigsEqual(self, found, expected, *args, **kwargs):
        conv = kwargs.pop('conv_first_posarg', False)
        if expected != found:
            if conv:
                expected = conv_first_posarg(expected)
                found = conv_first_posarg(found)
                if expected == found:
                    return
            raise AssertionError(
                'Did not get expected signature({0}), got {1} instead.'
                .format(expected, found))

    def assertIs(self, left, right):
        return self.assertTrue(left is right)
    if hasattr(unittest.TestCase, 'assertIs'):
        del assertIs

    def assertRaises(self, _exc, _func, *args, **kwargs):
        try:
            _func(*args, **kwargs)
        except _exc:
            pass
        else:
            self.fail("{0} did not raise {1}".format(_func, _exc))
    if hasattr(unittest.TestCase, 'assertRaises'):
        del assertRaises

def make_run_test(func, value, **kwargs):
    def _func(self):
        return func(self, *value, **kwargs)
    return _func

def build_sigtests(func, cls):
    members = {
            '_test_func': func,
        }
    for key, value in cls.__dict__.items():
        if key.startswith('test_') or key.startswith('_'):
            members[key] = value
        else:
            members['test_' + key] = make_run_test(func, value)
    return type(cls.__name__, (SignatureTests, unittest.TestCase), members)

def sigtester(test_func):
    return partial(build_sigtests, test_func)
