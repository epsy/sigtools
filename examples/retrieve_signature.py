import inspect
import functools

from sigtools import signature


def decorator(value_for_first_param):
    def _decorate(wrapped):
        @functools.wraps(wrapped)
        def _wrapper(*args, extra_arg, **kwargs):
            wrapped(value_for_first_param, *args, **kwargs)

        return _wrapper

    return _decorate


@decorator('eggs')
def func(ham, spam):
    return ham, spam


print("inspect:", inspect.signature(func))
# inspect: (ham, spam)

print("sigtools:", specifiers.signature(func))
# sigtools: (spam, *, extra_arg)


def decorator_without_wraps(value_for_first_param):
    def _decorate(wrapped):
        def _wrapper(*args, extra_arg, **kwargs):
            wrapped(value_for_first_param, *args, **kwargs)

        return _wrapper

    return _decorate


@decorator_without_wraps('eggs')
def func_without_wraps(ham, spam):
    return ham, spam


print("inspect w/o wraps:", inspect.signature(func_without_wraps))
# inspect w/o wraps: (*args, extra_arg, **kwargs


print("sigtools w/o wraps:", specifiers.signature(func_without_wraps))
# sigtools w/o wraps: (spam, *, extra_arg)
