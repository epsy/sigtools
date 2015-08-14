import sys
import ast
import collections
import functools
import types

from sigtools import _signatures, _util
from sigtools._specifiers import forged_signature

try:
    from collections.abc import MutableMapping
except ImportError:
    from collections import MutableMapping


class UnknownForwards(ValueError):
    pass


class UnresolvableName(ValueError):
    pass


class Name(object):
    def __init__(self, name):
        self.name = name

class Attribute(object):
    def __init__(self, value, attr):
        self.value = value
        self.attr = attr

class Arg(object):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<argument {0!r}>'.format(self.name)

class Unknown(object):
    def __init__(self, source=None):
        self.source = source

    def __iter__(self):
        return iter(())

    def items(self):
        return ()

    def __repr__(self):
        if self.source is None:
            return "<irrelevant>"
        source = self.source
        if isinstance(source, ast.AST):
            source = ast.dump(source)
        return "<unknown until runtime: {0}>".format(source)

class Varargs(object): pass
class Varkwargs(object): pass


class Namespace(MutableMapping):
    def __init__(self, parent=None):
        self.parent = parent
        self.names = {}
        self.nonlocals = {}

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

    def __delitem__(self, name):
        self[name] = Unknown()

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
            self.names[name] = Unknown()


Call = collections.namedtuple(
    'Call',
    'wrapped args kwargs varargs varkwargs '
    'use_varargs use_varkwargs '
    'hide_args hide_kwargs')


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
    def __init__(self, func):
        self.func = func
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
            self.namespace[name] = Arg(name) if main else Unknown(arg)
        if sys.version_info > (3,):
            for arg in args.kwonlyargs:
               self.namespace[arg.arg] = Arg(arg.arg) if main else Unknown(arg)

        varargs = varkwargs = None
        if args.vararg:
            name = get_vararg(args.vararg)
            varargs = self.namespace[name] = Arg(name)
        if args.kwarg:
            name = get_vararg(args.kwarg)
            varkwargs = self.namespace[name] = Arg(name)
        if main:
            self.varargs = varargs
            self.varkwargs = varkwargs

    def resolve_name(self, name):
        if isinstance(name, ast.Name):
            id = name.id
            return self.namespace.get(id, Name(id))
        elif isinstance(name, ast.Attribute):
            value = self.resolve_name(name.value)
            return Attribute(value, name.attr)
        self.visit(name)
        return Unknown(name)

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
        if isinstance(node.ctx, ast.Store):
            self.namespace[node.id] = Unknown(node)

    def has_hide_starargs(self, found, original):
        if found:
            if found == original:
                return True, False
            return False, True
        else:
            return False, False

    def process_Call(self, node):
        wrapped = self.resolve_name(node.func)
        args = [self.resolve_name(arg) for arg in node.args]
        kwargs = {kw.arg: self.resolve_name(kw.value) for kw in node.keywords}
        varargs = self.resolve_name(node.starargs) if node.starargs else None
        varkwargs = self.resolve_name(node.kwargs) if node.kwargs else None
        use_varargs, hide_args = \
            self.has_hide_starargs(varargs, self.varargs)
        use_varkwargs, hide_kwargs = \
            self.has_hide_starargs(varkwargs, self.varkwargs)
        self.calls.append(Call(
            wrapped, args, kwargs, varargs, varkwargs,
            use_varargs, use_varkwargs,
            hide_args, hide_kwargs))

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
                return func.__globals__[obj.name]
            else:
                return func.__closure__[index].cell_contents
        elif isinstance(obj, Arg):
            try:
                arg = args[obj.name]
                if not isinstance(arg, Unknown):
                    return arg
            except KeyError:
                pass
            raise UnresolvableName(obj)
        elif isinstance(obj, Attribute):
            return getattr(resolve_name(obj.value, func, args), obj.attr)
        else:
            raise UnresolvableName(obj)
    except UnresolvableName:
        if unknown:
            return Unknown(obj)
        raise


def forward_signatures(func, calls, args, kwargs, sig=None):
    sig = _signatures.signature(func) if sig is None else sig
    if args or kwargs:
        bap = sig.bind_partial(*args, **kwargs)
    else:
        bap = EmptyBoundArguments()
    def rn(obj, unknown=True):
        return resolve_name(obj, func, bap.arguments, unknown=unknown)
    for (
            wrapped, fwdargs, fwdkwargs, fwdvarargs, fwdvarkwargs,
            use_varargs, use_varkwargs,
            hide_args, hide_kwargs) in calls:
        if not (use_varargs or use_varkwargs):
            continue
        try:
            wrapped_func = rn(wrapped, unknown=False)
        except UnresolvableName:
            raise UnknownForwards
        fwdargsvals = [rn(arg) for arg in fwdargs]
        fwdargsvals.extend(rn(fwdvarargs))
        fwdkwargsvals = {n: rn(arg) for n, arg in fwdkwargs.items()}
        fwdkwargsvals.update(rn(fwdvarkwargs))
        wrapped_sig = forged_signature(
            wrapped_func, args=fwdargsvals, kwargs=fwdkwargsvals)
        try:
            yield _signatures.forwards(
                sig, wrapped_sig,
                len(fwdargs),
                hide_args, hide_kwargs,
                use_varargs, use_varkwargs,
                *fwdkwargs)
        except ValueError:
            raise UnknownForwards


def autoforwards_partial(par, args, kwargs):
    return _signatures._mask(
        autoforwards(par.func, par.args, {}),
        len(par.args),
        False, False, False, False,
        par.keywords or {})


def any_params_star(sig):
    for param in sig.parameters.values():
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            return True
    return False


def autoforwards_function(func, args, kwargs):
    sig = _signatures.signature(func)
    if not any_params_star(sig):
        raise UnknownForwards
    func_ast = _util.get_ast(func)
    if func_ast is None:
        raise UnknownForwards
    return autoforwards_ast(func, func_ast, None, args, kwargs)


def autoforwards_hint(func, args, kwargs):
    h = func._sigtools__autoforwards_hint(func)
    if h is not None:
        return autoforwards_ast(h[0], h[1], h[2], args, kwargs)
    else:
        raise UnknownForwards()


def autoforwards_ast(func, func_ast, sig, args=(), kwargs={}):
    sigs = list(forward_signatures(
        func, CallListerVisitor(func_ast),
        args, kwargs, sig))
    if sigs:
        return _signatures.merge(*sigs)
    else:
        raise UnknownForwards('No forwarding of *args, **kwargs found')


def autoforwards_method(method, args, kwargs):
    if method.__self__ is False:
        raise UnknownForwards
    sig = autoforwards(
        method.__func__, (method.__self__,) + tuple(args), kwargs)
    return _signatures.mask(sig, 1)


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
