from sigtools import modifiers, specifiers


def inner(a, b):
    raise NotImplementedError


class AClass(object):
    class_attr = True
    """class attr doc"""

    def __init__(self):
        self.abc = 123
        """instance attr doc"""

    @specifiers.forwards_to(inner)
    def outer(self, c, *args, **kwargs):
        raise NotImplementedError


@modifiers.autokwoargs
def kwo(a, b, c=1, d=2):
    raise NotImplementedError


@specifiers.forwards_to(inner)
def outer(c, *args, **kwargs):
    raise NotImplementedError
