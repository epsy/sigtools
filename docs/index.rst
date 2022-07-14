:mod:`sigtools` documentation
=============================

.. module:: sigtools

``sigtools`` is a Python package that improves on introspection tools available
for determining function signatures. This is useful for libraries or tooling
that want to know how a function can be called: Documentation generators, IDEs,
and tools that adapt themselves to functions they are given.

``sigtools`` provides:

- Utilities to boost introspection of callables' signature
- Backports of Python 3's keyword-only parameters for code that used to maintain both Python 2 and 3 compatibility.
- Utilities for combining functions, for instance for creating decorators
- A :doc:`Sphinx <sphinx:usage/index>` extension to make use of improved signature introspection in `sphinx.ext.autodoc`

.. toctree::
    :caption: Guide

    signature-retrieval
    sphinx-autodoc
    modifiers

.. toctree::
    :caption: Reference

    api
    forwards-howto


.. |pip| replace:: pip
.. _pip: https://pip.pypa.io/en/latest/

.. |virtualenv| replace:: virtualenv
.. _virtualenv: https://virtualenv.pypa.io/en/latest/


.. _install:

Installing
==========

You can install `sigtools` using |pip|_. If in an activated |virtualenv|_, type:

.. code-block:: console

    pip install sigtools

If you wish to do a user-wide install:

.. code-block:: console

    pip install --user sigtools

