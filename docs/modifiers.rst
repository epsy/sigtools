.. _keyword-only parameters:

Keyword-only parameters
-----------------------

``sigtools`` provides two decorators to emulate keyword-only parameters:

.. autosignature:: sigtools.modifiers.autokwoargs

    Converts all parameters with default values to keyword-only parameters:

    .. code:: python

        from sigtools.modifiers import autokwoargs


        @autokwoargs
        def func(arg, opt1=False, opt2=False, *rest):
            print(arg, rest, opt1, opt2)


        func(1, 2, 3)
        # 1 (2, 3) False False

        func(1, 2, opt2=True)
        # -> 1 (2,) False True

    ..
        x*

    In the example above, the ``opt1`` and ``opt2`` parameters are 'skipped' by
    positional arguments and can only be set using named arguments
    (``opt2=True``).

    If you wish to prevent parameters that have a default from becoming
    keyword-only, you can use the ``exceptions=`` parameter:

    .. code:: python

        @autokwoargs(exceptions=['arg2'])
        def func(arg1, arg2=42, opt1=False, opt2=False):
            print(arg1, arg2, opt1, opt2)

        func(1, 2, opt1=False)
        # 1 2 False False

If you wish to pick individual parameters to convert, use
`sigtools.modifiers.kwoargs`. This module also allows you to add function
annotations using the `~sigtools.modifiers.annotate` decorator.
