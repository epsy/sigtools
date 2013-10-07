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

"""Sphinx extension which makes sphinx use the __signature__ attribute
of objects when auto-documenting them."""

try:
    from inspect import signature
except ImportError:
    from funcsigs import signature

def process_signature(app, what, name, obj, options,
                      sig, return_annotation):
    try:
        sig = signature(obj)
    except (TypeError, ValueError):
        return sig, return_annotation
    ret_annot = sig.return_annotation
    if ret_annot != sig.empty:
        sret_annot = '-> {0!r}'.format(ret_annot)
        sig = sig.replace(return_annotation=sig.empty)
    else:
        sret_annot = ''
    return str(sig), sret_annot

def setup(app):
    app.connect('autodoc-process-signature', process_signature)
