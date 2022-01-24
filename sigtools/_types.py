import traceback
import typing

import attr

from sigtools import _util


class BaseMarker(object):
    def get_untainted(self):
        return self


class SignatureError(ValueError):
    def __init__(self, call_tree, cause) -> None:
        super().__init__(f"{type(cause).__name__}: {cause}")
        self.call_tree = call_tree


class Signature(_util.funcsigs.Signature):
    __slots__ = _util.funcsigs.Signature.__slots__ + ('sources', "call_tree", "name")

    def __init__(self, *args, **kwargs):
        self.sources = kwargs.pop('sources', {})
        self.call_tree = kwargs.pop('call_tree', DefaultLeafCall())
        self.name = kwargs.pop('name', None)
        super(Signature, self).__init__(*args, **kwargs)

    @classmethod
    def upgrade(cls, inst, sources=None, call_tree=None, name=None):
        return cls(
            inst.parameters.values(),
            return_annotation=inst.return_annotation,
            sources=sources or getattr(inst, "sources", None) or {},
            call_tree=call_tree or getattr(inst, "call_tree", None) or DefaultLeafCall(),
            name=name)

    def replace(self, *args, **kwargs):
        sources = kwargs.pop('sources', self.sources)
        call_tree = kwargs.pop('call_tree', self.call_tree)
        name = kwargs.pop('name', self.name)
        ret = super(Signature, self).replace(*args, **kwargs)
        ret.sources = sources
        ret.call_tree = call_tree
        ret.name = name
        return ret

    def __str__(self) -> str:
        return f'{self.name or ""}{super().__str__()}'

    def debug_call_tree(self):
        return '\n'.join( self.__debug_call_tree())

    def __debug_call_tree(self):
        stack = [iter((self,))]
        while stack:
            indent = "    " * (len(stack) - 1)
            for sig in stack[-1]:
                subtree = getattr(sig, "call_tree", DefaultLeafCall())
                yield f'{indent}  signature {sig}:'
                for line in str(subtree).split('\n'):
                    yield f'{indent}    {line}'
                if subtree.signatures:
                    yield f"{indent}    Signatures used:"
                    stack.append(iter(subtree.signatures))
                break
            else:
                stack.pop()



@attr.define
class Call:
    function: BaseMarker
    args: typing.List[BaseMarker]
    kwargs: typing.Dict[str, BaseMarker]
    varargs: BaseMarker
    varkwargs: BaseMarker
    use_varargs: bool
    use_varkwargs: bool
    hide_args: bool
    hide_kwargs: bool
    filename: str
    line: int

    def __str__(self) -> str:
        return f'{self.function}({", ".join(self.__str_args())})'

    def __str_args(self):
        for arg in self.args:
            yield str(arg)
        if self.use_varargs or self.hide_args:
            yield f'*{self.varargs}' # ??
        for key, arg in self.kwargs.items():
            yield f"{key}={arg}"
        if self.use_varkwargs or self.hide_kwargs:
            yield f'**{self.varkwargs}'


class CallTreeDescription:
    signatures: typing.List[Signature]
    determined = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, _):
        if exc_type:
            raise SignatureError(self, exc_val) from exc_val
        return False


@attr.define
class SupplyArgumentsCall(CallTreeDescription):
    signatures: typing.List[Signature] = attr.ib(repr=False)
    num_args: int
    named_args: typing.List[str]
    hide_args: bool
    hide_kwargs: bool
    hide_varargs: bool
    hide_varkwargs: bool

    def __str__(self) -> str:
        args = []
        if self.hide_args:
            args.append("hide all *args")
        else:
            for i in range(self.num_args):
                args.append(f'arg{i + 1}')
            if self.hide_varargs:
                args.append('*args')

        if self.hide_kwargs:
            args.append("hide all **kwargs")
        else:
            for arg in self.named_args:
                args.append(f'{arg}=...')
            if self.hide_varkwargs:
                args.append('**kwargs')

        comma_args = ', '.join(args)
        return f'{getattr(self.signatures[0], "name", "func")}({comma_args})'

@attr.define
class MergedCall(CallTreeDescription):
    signatures: typing.List[Signature] = attr.ib(repr=False)

    @classmethod
    def instantiate(cls, signatures):
        if len(signatures) == 1:
            return signatures[1].call_tree
        else:
            return cls(signatures)

@attr.define
class DefaultLeafCall(CallTreeDescription):
    signatures = ()
    location = attr.ib(init=False, repr=False)
    determined = False

    def __attrs_post_init__(self):
        self.location = traceback.extract_stack()[:-1]

@attr.define
class FunctionDefinition(CallTreeDescription):
    signatures: typing.List[Signature] = attr.ib(init=False, repr=False, default=())
    file: str
    line: int
    determined = False

    def __str__(self) -> str:
        return f'function defined in {self.file} line {self.line}'


@attr.define
class EmbeddedCall(CallTreeDescription):
    signatures: typing.List[Signature] = attr.ib(repr=False)
    use_varargs: bool
    use_varkwargs: bool

    def __str__(self) -> str:
        def _build_supply_args():
            if self.use_varargs:
                yield '*args'
            if self.use_varkwargs:
                yield "**kwargs"
        supply_args = ", ".join(_build_supply_args())

        def _build_chain():
            iter_signatures = iter(self.signatures)
            yield f'def {next(iter_signatures)}'
            for sig in iter_signatures:
                if self.call:
                    yield str(self.call)
                else:
                    name = getattr(sig, "name", "func")
                    yield f'{name}({supply_args}) ({sig.file} line {sig.line})'
                yield f'def {sig}'
        return " => ".join(_build_chain())


@attr.define
class ForwardedCall(CallTreeDescription):
    signatures: typing.List[Signature] = attr.ib(repr=False)
    use_varargs: bool
    use_varkwargs: bool
    num_args: int
    named_args: typing.List[str]
    hide_args: bool
    hide_kwargs: bool
    call: Call = attr.ib()

    @_util.join_generator('\n')
    def __str__(self) -> str:
        outer, inner = self.signatures

        yield (
            f'function {outer}\n'
            f'calls {self.call}\n'
            f'on line {self.call.line} of {self.call.filename}'
        )

        if self.hide_args:
            yield "=> All positional parameters hidden"
        
        if self.hide_kwargs:
            yield "=> All keyword parameters hidden (including position-or-keyword parameters)"
        
        yield (
            f'{self.call.function} has signature {inner}'
        )


@attr.define
class FailedTreeDescription(CallTreeDescription):
    error: str
    attempted: CallTreeDescription
    signatures = ()

    def __attrs_post_init__(self):
        self.signatures = getattr(self.attempted, 'signatures', ())

    def __str__(self) -> str:
        attempted = str(self.attempted).replace("\n", "\n  ")
        return (
            f'Error:\n'
            f'  {self.error}\n'
            f'while attempting:\n'
            f'  {attempted}'
        )