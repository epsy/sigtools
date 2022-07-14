from __future__ import annotations

import attrs

from sigtools import signature


def myfunc(my_param: MyInput) -> MyOutput:
    return MyOutput(ham=my_param.spam)


@attrs.define
class MyInput:
    spam: str


@attrs.define
class MyOutput:
    ham: str


sig = signature(myfunc)

print(sig)
# (my_param: 'MyInput') -> 'MyOutput'

print(repr(sig.return_annotation))
# 'MyOutput'
print(repr(sig.upgraded_return_annotation.source_value()))
# <class '__main__.MyOutput'>

print(repr(sig.parameters["my_param"].annotation))
# 'MyInput'
print(repr(sig.parameters["my_param"].upgraded_annotation.source_value()))
# <class '__main__.MyInput'>

print(sig.evaluated())
# (my_param: __main__.MyInput) -> __main__.MyOutput
