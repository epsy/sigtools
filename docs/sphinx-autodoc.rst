.. _sphinxext:

Improved signatures in `sphinx.ext.autodoc` documentation
---------------------------------------------------------

`Sphinx <https://sphinx-doc.org/>`_, the documentation tool, comes with an
extension, `sphinx.ext.autodoc`, which lets you source some of your
documentation from your code and its docstrings. ``sigtools.sphinxext``, if
activated, automatically improves signatures like explained above.

To activate it, add ``'sigtools.sphinxext'`` to the ``extensions`` list in your
Sphinx's  ``conf.py``:

.. code:: python

    extensions = [
        'sphinx.ext.autodoc', ...
        'sigtools.sphinxext']

If you want to use the automatic signature gathering while ignoring the docstring
in order to supply your own explanations, you can use this directive instead of
:rst:dir:`autofunction`:

.. rst:directive:: .. autosignature:: path.to.callable.object

    Documents a Python object while ignoring the source docstring.
    `sigtools.signature` is used to retrieve the object's call
    signature
