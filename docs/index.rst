:mod:`sigtools` documentation
=============================

Python 3.3's ``inspect`` module has introduced `signature objects
<http://docs.python.org/3/library/inspect#introspecting-callables-with-the-signature-object>`_,
which provide a new way to introspect callable objects and a protocol for
pretending to have a different call signature.

This package helps module authors enhance their callables' introspectability
if needed, and provides a way to use features the python syntax does not
or did not permit, such as keyword-only parameters.

For versions of Python below 3.3, `a backport of the relevant parts of inspect
is available on pypi <https://pypi.python.org/pypi/funcsigs>`_.

:mod:`modifiers`: Change the effective signature of a callable
--------------------------------------------------------------

.. automodule:: sigtools.modifiers
    :members:
    :undoc-members:

:mod:`specifiers`: Enhance a callable's signature
-------------------------------------------------

.. automodule:: sigtools.specifiers
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`wrappers`: Combine multiple functions
-------------------------------------------

.. automodule:: sigtools.wrappers
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`signatures`: Algorithms that operate on signatures directly
-----------------------------------------------------------------

.. automodule:: sigtools.signatures
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`test`: Utilities for use in interactive sessions or unit tests
--------------------------------------------------------------------

.. automodule:: sigtools.test
    :members:
    :undoc-members:
    :show-inheritance:

