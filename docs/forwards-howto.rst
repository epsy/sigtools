
.. _forwards-pick:

Picking the appropriate arguments for ``forwards``
==================================================

If automatic signature reporting doesn't work for your use case and you still
want to specify how a function's ``*args, **kwargs`` is being used, you may
either use `sigtools.specifiers.forger_function` and `sigtools.support.s`
to override its signature completely, or you can use the ``forwards_to_*``
functions from `sigtools.specifiers`.

For ``forwards_to_*`` decorators, you only need to specify what function
``*args, **kwargs`` are forwarded to and what other arguments are passed in.
Here's a primer with common examples on how to use them.


.. _fwd which:

Picking the appropriate ``forwards_to_*`` decorator
---------------------------------------------------

Several ``forwards_to_*`` decorators exist. You must pick one depending on what
you are forwarding your parameters to:

`~.forwards_to_function`
    When forwarding to a plain function::

        def inner(a, b, c):
            ...

        @specifiers.forwards_to_function(inner)
        def outer(*args, **kwargs):
            inner(*args, **kwargs)

    Provide the inner function as the first argument to
    `~.forwards_to_function`.

`~.forwards_to_method`
    When forwarding to an attribute of the current object, usually to a method::

        class Spam:
            def inner(self, a, b, c):
                ...

            @specifiers.forwards_to_method('inner')
            def outer(self, *args, **kwargs):
                self.inner(*args, **kwargs)

    Provide the inner function's *name* to `~.forwards_to_method`.

    You can also specify a "deep" attribute: ``'attribute.method'`` should be
    specified if a call is made like this::

        self.attribute.method(*args, **kwargs)

`~.forwards_to_super`
    When forwarding to the superclass's method of the same name::

        class Spam:
            def method(self):
                pass

        class Ham(Spam):
            @specifiers.forwards_to_super()
            def method(self, *args, ham, **kwargs):
                super().method(*args, **kwargs)

    This only works when using the short form of :func:`super` introduced in
    Python 3.3. If you are targetting earlier versions, use
    `~.apply_forwards_to_super` on the class, while specifying which methods
    need to receive the decorator.


For the following examples, we will be using the
`~specifiers.forwards_to_function` decorator, although these will work with
other ``forwards_to_*`` decorators.

.. _fwd direct:

``*args`` and ``**kwargs`` are forwarded directly if present
------------------------------------------------------------

You do not need to signal anything about the wrapper function's parameters::

    @specifiers.forwards_to_function(wrapped)
    def outer(arg, *args, **kwargs):
        inner(*args, **kwargs)

This holds true even if you omit one of ``*args`` and ``**kwargs``::

    @specifiers.forwards_to_function(wrapped)
    def outer(**kwargs):
        inner(**kwargs)


.. _fwd pos:

Passing positional arguments to the wrapped function
----------------------------------------------------

Indicate the number of arguments you are passing to the wrapped function::

    @specifiers.forwards_to_function(wrapped, 1)
    def outer(*args, **kwargs):
        inner('abc', *args, **kwargs)

This applies even if the argument comes from the wrapper::

    @specifiers.forwards_to_function(wrapped, 1)
    def outer(arg, *args, **kwargs):
        inner(arg, *args, **kwargs)


.. _fwd named:

Passing named arguments to from the wrapper
-------------------------------------------

Pass the names of the arguments after ``num_args``::

    @specifiers.forwards_to_function(wrapped, 0, 'arg')
    def outer(*args, **kwargs):
        inner(*args, arg='abc', **kwargs)

Once again, the same goes for if that argument comes from the outer
function's::

    @specifiers.forwards_to_function(wrapped, 0, 'arg')
    def outer(*args, arg, **kwargs): # py 3
        inner(*args, arg=arg, **kwargs)

If you combine positional and named arguments, follow the previous advice as
well::

    @specifiers.forwards_to_function(wrapped, 2, 'alpha', 'beta')
    def outer(two, *args, beta, **kwargs):
        inner(one, two=two, *args, alpha='abc', beta=beta, **kwargs)


.. _fwd use:

When the outer function uses ``*args`` or ``**kwargs`` but doesn't forward them to the inner function
-----------------------------------------------------------------------------------------------------

Pass ``use_varargs=False`` if your outer function has an ``*args``-like
parameter but doesn't use it on the inner function directly::

    @specifiers.forwards_to_function(wrapped, use_varargs=False)
    def outer(*args, **kwargs):
        inner(**kwargs)

Pass ``use_varkwargs=False`` if you outer function has a ``**kwargs``-like
parameter but doesn't use it on the inner function directly::

    @specifiers.forwards_to_function(wrapped, use_varkwargs=False)
    def outer(*args, **kwargs):
        inner(*args)


.. _fwd hide:

When the outer function passes an arbitrary ``*args`` or ``**kwargs`` to the inner function
-------------------------------------------------------------------------------------------

Pass ``hide_args=True`` if your outer function uses an arbitrary ``*args`` when
calling the inner function (whether one exists or not in the outer function)::

    @specifiers.forwards_to_function(wrapped, hide_args=True)
    def outer(**kwargs):
        args = other_function(...)
        inner(*args, **kwargs)

If you know exactly how many items ``args`` will have, specify the amount of
items in ``args`` instead, as in :ref:`fwd pos`.

Conversely, pass ``hide_kwargs=True`` if your outer function uses an arbitrary
``*kwargs`` when calling the inner function (whether one exists or not in the
outer function)::

    @specifiers.forwards_to_function(wrapped, hide_args=True)
    def outer(*args):
        kwargs = other_function(...)
        inner(*args, **kwargs)

If you know exactly which keys ``kwargs`` will potentially have, specify all
possible named keys it might have, as in :ref:`fwd named`.

.. note::

   Neither are needed if the outer function hasn't got an ``*args`` nor
   ``**kwargs`` parameter


.. _fwd summary:

Summary
-------

Finally, here's an overview of all parameters from ``forwards_to_*`` functions

.. autosignature:: sigtools.specifiers.forwards_to_function

..

    **num_args**
        The number of arguments you pass by position, excluding ``*args``.

    **\*named_args**
        The names of the arguments you pass by name, excluding ``**kwargs``.

    **use_varargs=**
        Tells if the wrapper's ``*args`` is being passed to the wrapped function.

    **use_varkwargs=**
        Tells if the wrapper's ``**kwargs`` is being passed to the wrapped
        function.

    **hide_args=**
        Tells if the wrapped function is given an ``*args`` parameter
        (other than the wrapper function's) in such a way that all positional
        parameters are consumed.

    **hide_varargs=**
        Tells if the wrapped function is given a ``**kargs`` parameter
        (other than the wrapper function's) in such a way that all keyword
        parameters are consumed.


