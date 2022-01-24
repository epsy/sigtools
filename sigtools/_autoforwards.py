import sys
import ast
import collections
import functools
import traceback
import types
import typing

import attr
from sigtools import _signatures, _util
from sigtools._specifiers import forged_signature
from sigtools._types import BaseMarker, Call, CallTreeDescription, FailedTreeDescription

try:
    from collections.abc import MutableMapping
except ImportError:
    from collections import MutableMapping


class UnknownForwards(ValueError):
    def __init__(self, message:str, call_tree: CallTreeDescription = None) -> None:
        super().__init__(message)
        self.call_tree = call_tree

    def to_call_tree(self) -> CallTreeDescription:
        return FailedTreeDescription(
            error = str(self.__cause__ or self),
            attempted = self.call_tree or getattr(getattr(self, "__cause__", None), "call_tree", None),
        )


class UnresolvableName(ValueError):
    pass


class Marker(BaseMarker):
    def __init__(self):
        self.tainted = None

    def get_untainted(self):
        if self.tainted is None:
            return self
        else:
            return Unknown(self.tainted)

class Name(Marker):
    def __init__(self, name):
        super(Name, self).__init__()
        self.name = name

    def __repr__(self):
        return '<name {0!r}>'.format(self.name)

    def __str__(self) -> str:
        return f'<var {self.name}'


class Attribute(Marker):
    def __init__(self, value, attr):
        super(Attribute, self).__init__()
        self.value = value
        self.attr = attr

    def __repr__(self):
        return '<attribute {0!r}.{1}>'.format(self.value, self.attr)

    def __str__(self) -> str:
        return f"{self.value}.{self.attr}"


class Arg(Marker):
    def __init__(self, name):
        super(Arg, self).__init__()
        self.name = name

    def __repr__(self):
        return '<argument {0!r}>'.format(self.name)

    def __str__(self) -> str:
        return f'<arg: {self.name}>'


class Unknown(BaseMarker):
    def __init__(self, source=None):
        self.source = source

    def __iter__(self):
        return iter(())

    def __repr__(self):
        if self.source is None:
            return f"<{self.__class__.__name__}>"
        return f"<{self.__class__.__name__}: {self.source_repr()}>"

    def source_repr(self):
        if isinstance(self.source, list):
            return '[' + ', '.join(
                ast.dump(item) if isinstance(item, ast.AST)
                else item
                for item in self.source) + ']'
        elif isinstance(self.source, ast.AST):
            return ast.dump(self.source)
        else:
            return self.source

    def get_untainted(self):
        return self


class MultipleStarArgs(Unknown):
    def __init__(self, source=None):
        super().__init__(source=source)


class UnknownUntilRuntime(Unknown):
    def __init__(self, source=None):
        super().__init__(source=source)


class PotentiallyModified(Unknown):
    def __init__(self, source=None):
        super().__init__(source=source)


class Namespace(MutableMapping):
    def __init__(self, parent=None):
        self.parent = parent
        self.names = {}
        self.nonlocals = {}
        self.immutables = set()

    def __getitem__(self, name):
        ns = self.nonlocals.get(name, self)
        try:
            return ns.names[name]
        except KeyError:
            if self.parent:
                return self.parent[name]
            else:
                raise

    def __setitem__(self, name, value):
        ns = self.nonlocals.get(name, self)
        ns.names[name] = value
        ns.immutables.discard(name)

    def __delitem__(self, name):
        raise NotImplementedError("Set ns[name] = Unknown(...) instead")

    def __iter__(self):
        return iter(self.names)

    def __len__(self):
        return len(self.names)

    def add_nonlocal(self, name):
        ns = self.parent
        while ns is not None:
            if name in ns.names:
                self.nonlocals[name] = ns
                break
            ns = ns.parent
        else: # refers to variable outside the function being examined
            self.names[name] = Name(name)

    def is_immutable_value(self, name):
        ns = self.nonlocals.get(name, self)
        return name in ns.immutables

    def set_immutable_value(self, name):
        ns = self.nonlocals.get(name, self)
        ns.immutables.add(name)


if sys.version_info < (3,5):
    Starred = type(None)
    def get_starargs(call):
        return call.starargs
    def get_kwargs(call):
        return call.kwargs
else:
    Starred = ast.Starred
    def get_starargs(call):
        ret = [n for n in call.args if isinstance(n, Starred)]
        if not ret:
            return None
        elif len(ret) == 1:
            return ret[0].value
        else:
            return MultipleStarArgs(ret)
    def get_kwargs(call):
        ret = [n for n in call.keywords if n.arg is None]
        if not ret:
            return None
        elif len(ret) == 1:
            return ret[0].value
        else:
            return MultipleStarArgs(ret)

if sys.version_info < (3,4):
    def get_vararg(arg):
        return arg
else:
    def get_vararg(arg):
        return arg.arg

if sys.version_info < (3,):
    def get_param(arg):
        return arg.id
else:
    def get_param(arg):
        return arg.arg


class CallListerVisitor(ast.NodeVisitor):
    def __init__(self, func, filename):
        self.func = func
        self.filename = filename
        self.namespace = Namespace()
        self.calls = []
        self.to_revisit = []
        self.varargs = None
        self.varkwargs = None

        self.process_parameters(func.args, main=True)
        for stmt in func.body:
            self.visit(stmt)
        for node, ns in self.to_revisit:
            self.namespace = ns
            self.process_Call(node)

    def process_parameters(self, args, main=False):
        for arg in args.args:
            name = get_param(arg)
            self.namespace[name] = Arg(name) if main else UnknownUntilRuntime(arg)
        if sys.version_info > (3,):
            for arg in args.kwonlyargs:
               self.namespace[arg.arg] = Arg(arg.arg) if main else UnknownUntilRuntime(arg)

        varargs = varkwargs = None
        if args.vararg:
            name = get_vararg(args.vararg)
            varargs = self.namespace[name] = Arg(name)
            self.namespace.set_immutable_value(name)
        if args.kwarg:
            name = get_vararg(args.kwarg)
            varkwargs = self.namespace[name] = Arg(name)
        if main:
            self.varargs = varargs
            self.varkwargs = varkwargs

    def resolve_name(self, name, ro=False, tainted=False):
        try:
            if isinstance(name, ast.Name):
                id = name.id
                ret = self.namespace.get(id, Name(id))
            elif isinstance(name, ast.Attribute):
                value = self.resolve_name(name.value, ro=True, tainted=tainted)
                ret = Attribute(value, name.attr)
            elif isinstance(name, Unknown):
                ret = name
            else:
                ret = Unknown(name)
            if not tainted:
                return ret.get_untainted()
            return ret
        finally:
            if not isinstance(name, Unknown) and not (ro and isinstance(name, ast.Name)):
                self.visit(name)

    def visit_FunctionDef(self, node):
        self.namespace = Namespace(self.namespace)
        self.process_parameters(node.args)
        body = node.body
        try:
            iter(body)
        except TypeError: # handle lambdas as well
            body = [node.body]
        for stmt in body:
            self.visit(stmt)
        self.namespace = self.namespace.parent

    visit_Lambda = visit_FunctionDef

    def visit_Nonlocal(self, node):
        for name in node.names:
            self.namespace.add_nonlocal(name)

    def visit_Name(self, node):
        immutable = self.namespace.is_immutable_value(node.id)
        if not (immutable and isinstance(node.ctx, ast.Load)):
            if node.id in self.namespace:
                self.namespace[node.id] = PotentiallyModified(self.namespace[node.id])
            else:
                self.namespace[node.id] = UnknownUntilRuntime(Name(node.id))

    def visit_Attribute(self, node):
        pass

    def has_hide_starargs(self, found, original):
        if found:
            if found == original:
                return True, False
            return False, True
        else:
            return False, False

    def process_Call(self, node):
        wrapped = self.resolve_name(node.func, ro=True, tainted=True)
        if isinstance(wrapped, Attribute):
            instance = wrapped
            while isinstance(instance, Attribute):
                instance = instance.value
            if isinstance(instance, Arg):
                self.namespace[instance.name].tainted = node
        args = [self.resolve_name(arg) for arg in node.args
                if not isinstance(arg, Starred)]
        kwargs = dict(
            (kw.arg, self.resolve_name(kw.value))
            for kw in node.keywords if kw.arg is not None)
        starargs = get_starargs(node)
        starkwargs = get_kwargs(node)
        varargs = self.resolve_name(starargs, ro=True) if starargs else None
        varkwargs = self.resolve_name(starkwargs, ro=True) if starkwargs else None
        use_varargs, hide_args = \
            self.has_hide_starargs(varargs, self.varargs)
        use_varkwargs, hide_kwargs = \
            self.has_hide_starargs(varkwargs, self.varkwargs)
        self.calls.append(Call(
            wrapped, args, kwargs, varargs, varkwargs,
            use_varargs, use_varkwargs,
            hide_args, hide_kwargs,
            self.filename,
            node.lineno,
            ))

    def visit_Call(self, node):
        if self.namespace.parent is None:
            self.process_Call(node)
        else:
            self.to_revisit.append((node, self.namespace))

    def __iter__(self):
        return iter(self.calls)


class EmptyBoundArguments(object):
    def __init__(self):
        self.arguments = {}


def resolve_name(obj, func, args, unknown=False):
    try:
        if isinstance(obj, Name):
            try:
                index = func.__code__.co_freevars.index(obj.name)
            except ValueError:
                try:
                    return func.__globals__[obj.name]
                except KeyError:
                    raise UnresolvableName(obj)
            else:
                try:
                    try:
                        return func.__closure__[index].cell_contents
                    except AttributeError: # pragma: no cover
                        return func.func_closure[index].cell_contents
                except ValueError:
                    raise UnresolvableName(obj)
        elif isinstance(obj, Arg):
            try:
                return args[obj.name]
            except KeyError:
                raise UnresolvableName(obj)
        elif isinstance(obj, Attribute):
            attr_owner = resolve_name(obj.value, func, args)
            try:
                return getattr(attr_owner, obj.attr)
            except AttributeError:
                raise UnresolvableName(obj)
        else:
            raise UnresolvableName(obj)
    except UnresolvableName:
        if unknown:
            return Unknown(obj)
        raise


def forward_signatures(func, calls, args, kwargs, sig):
    if args or kwargs:
        bap = sig.bind_partial(*args, **kwargs)
    else:
        bap = EmptyBoundArguments()
    def rn(obj, unknown=True):
        return resolve_name(obj, func, bap.arguments, unknown=unknown)
    for call  in calls:
        if not (call.use_varargs or call.use_varkwargs):
            continue
        try:
            wrapped_func = rn(call.function, unknown=False)
        except UnresolvableName:
            raise UnknownForwards(f"Could not resolve method {call.function}")
        fwdargsvals = [rn(arg) for arg in call.args]
        fwdargsvals.extend(rn(call.varargs))
        fwdkwargsvals = dict((n, rn(arg)) for n, arg in call.kwargs.items())
        fwdkwargsvals.update(rn(call.varkwargs))
        using_partial = wrapped_func == functools.partial
        if using_partial:
            wrapped_func = fwdargsvals.pop(0)
        try:
            wrapped_sig = forged_signature(
                wrapped_func, args=fwdargsvals, kwargs=fwdkwargsvals)
        except (ValueError, TypeError):
            raise UnknownForwards(f"Error getting signature for {call}")
        try:
            ausig = _signatures.forwards(
                sig, wrapped_sig,
                len(call.args) - using_partial,
                call.hide_args, call.hide_kwargs,
                call.use_varargs, call.use_varkwargs,
                using_partial, *call.kwargs, name=str(call.function), call=call)
            yield ausig
        except ValueError as e:
            raise UnknownForwards(f"Error performing Forward on {sig} => {wrapped_sig}") from e


def autoforwards_partial(par, args, kwargs):
    sig = autoforwards(par.func, par.args, {})
    return _signatures._mask(
        sig, len(par.args),
        False, False, False, False,
        par.keywords or {}, par)


def any_params_star(sig):
    for param in sig.parameters.values():
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            return True
    return False


class cleanup_functools_wrapper(object):
    attrs = ['__wrapped__', '__signature__']

    def __init__(self, func):
        self.func = func

    def __enter__(self):
        try:
            self.saved_attrs
        except AttributeError:
            pass
        else:
            raise NotImplementedError('This context manager is not reentrant')
        self.saved_attrs = {}
        for attr in self.attrs:
            try:
                self.saved_attrs[attr] = getattr(self.func, attr)
                delattr(self.func, attr)
            except AttributeError:
                pass

    def __exit__(self, *exc):
        for attr, val in self.saved_attrs.items():
            setattr(self.func, attr, val)


def autoforwards_function(func, args, kwargs):
    with cleanup_functools_wrapper(func):
        sig = _signatures.signature(func)
    if not any_params_star(sig):
        return sig
    func_ast = _util.get_ast(func)
    if func_ast is None:
        raise UnknownForwards(f"Cannot get function AST for {func}")
    return autoforwards_ast(func, func_ast, sig, args, kwargs)


def autoforwards_hint(func, args, kwargs):
    h = func._sigtools__autoforwards_hint(func)
    if h is not None:
        return autoforwards_ast(h[0], h[1], h[2], args, kwargs)
    else:
        raise UnknownForwards("No hint available")


def autoforwards_ast(func, func_ast, sig, args=(), kwargs={}):
    filename = '<unknown>'
    try:
        filename = func.__code__.co_filename
    except AttributeError:
        pass
    sigs = list(forward_signatures(
        func, CallListerVisitor(func_ast, filename),
        args, kwargs, sig))
    if sigs:
        return _signatures.merge(*sigs)
    else:
        raise UnknownForwards('No forwarding of *args, **kwargs found')


def autoforwards_method(method, args, kwargs):
    if method.__self__ is None:
        raise UnknownForwards("Unbound method")
    return _signatures.mask(
        autoforwards(method.__func__, (method.__self__,) + tuple(args), kwargs),
        1)


def autoforwards(obj, args=(), kwargs={}):
    try:
        obj._sigtools__autoforwards_hint
    except AttributeError:
        pass
    else:
        return autoforwards_hint(obj, args, kwargs)
    if isinstance(obj, functools.partial):
        return autoforwards_partial(obj, args, kwargs)
    elif isinstance(obj, types.MethodType):
        return autoforwards_method(obj, args, kwargs)
    else:
        return autoforwards_function(obj, args, kwargs)
