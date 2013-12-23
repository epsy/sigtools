:mod:`sigtools` documentation
=============================

.. module:: sigtools

Python 3.3's ``inspect`` module has introduced `signature objects
<http://docs.python.org/3/library/inspect#introspecting-callables-with-the-signature-object>`_,
which provide a new way to introspect callable objects and a protocol for
pretending to have a different call signature.

This package helps module authors enhance their callables' introspectability
if needed, and provides a way to use features the python syntax does not
or did not permit, such as keyword-only parameters.

For versions of Python below 3.3, `a backport of the relevant parts of inspect
is available on pypi <https://pypi.python.org/pypi/funcsigs>`_.

.. automodule:: sigtools.modifiers
    :members:
    :undoc-members:

.. automodule:: sigtools.specifiers
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: sigtools.wrappers
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: sigtools.signatures
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: sigtools.support
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: sigtools.sphinxext
