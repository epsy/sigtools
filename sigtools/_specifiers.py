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


from sigtools import _signatures, _util


def forged_signature(obj, autoforward=True, args=(), kwargs={}):
    """Retrieve the signature of ``obj``, taking into account any specifier
    from this module.

    If ``autoforward`` is true, the signature will be automatically refined
    based on how ``*args`` and ``**kwargs``.

    If ``args`` and/or ``kwargs`` are specified, they are used by automatic
    signature determination as arguments passed into the function. This is
    useful if the function calls something passed in as a parameter.

    You can use ``emulate=True`` as an argument to the specifiers from this
    module if you wish them to work with `inspect.signature` or its
    `funcsigs<funcsigs:signature>` backport directly.

    ::

        >>> from sigtools import specifiers
        >>> import inspect
        >>> def inner(a, b):
        ...     return a + b
        ...
        >>> @specifiers.forwards_to_function(inner)
        ... def outer(c, *args, **kwargs):
        ...     return c * inner(*args, **kwargs)
        ...
        >>> print(inspect.signature(outer))
        (c, *args, **kwargs)
        >>> print(specifiers.signature(outer))
        (c, a, b)
        >>> @specifiers.forwards_to_function(inner, emulate=True)
        ... def outer(c, *args, **kwargs):
        ...     return c * inner(*args, **kwargs)
        >>> print(inspect.signature(outer))
        (c, a, b)
        >>> print(specifiers.signature(outer))
        (c, a, b)

    :param bool autoforward: Enable automatic signature determination.
    :param sequence args: Positional arguments passed to the function.
    :param mapping: Named arguments passed to the function.

    """
    subject = _util.get_introspectable(obj, af_hint=autoforward)
    if autoforward:
        try:
            subject._sigtools__autoforwards_hint
        except AttributeError:
            pass
        else:
            h = subject._sigtools__autoforwards_hint(subject)
            if h is not None:
                try:
                    ret = _autoforwards.autoforwards_ast(
                        *h, args=args, kwargs=kwargs)
                except _autoforwards.UnknownForwards:
                    pass
                else:
                    return ret
            subject = _util.get_introspectable(subject, af_hint=False)
    forger = getattr(subject, '_sigtools__forger', None)
    if forger is not None:
        ret = forger(obj=subject)
        if ret is not None:
            return ret
    if autoforward:
        try:
            ret = _autoforwards.autoforwards(subject, args, kwargs)
        except _autoforwards.UnknownForwards:
            pass
        else:
            return ret
    return _signatures.signature(obj)


from sigtools import _autoforwards
