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


from collections import defaultdict

from sigtools import _signatures, _util


def _params_from_sig(func, sig):
    params = defaultdict(set)
    _autoforwards.add_params(params, func, sig)
    return sig, params

def forged_signature(obj, autoforward=True, args=(), kwargs={}):
    """
    Returns the signature of obj, along with a `dict` mapping each parameter
    name to the function it comes from.

    See `~sigtools.specifiers.signature` for an explanation of the parameters.
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
            try:
                sig, src = ret
            except (TypeError, ValueError):
                return _params_from_sig(subject, ret)
            return sig, src
    if autoforward:
        try:
            ret = _autoforwards.autoforwards(subject, args, kwargs)
        except _autoforwards.UnknownForwards:
            pass
        else:
            return ret
    return _params_from_sig(obj, _signatures.signature(obj))


from sigtools import _autoforwards
