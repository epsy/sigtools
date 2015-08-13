import inspect
import ast
import collections
from collections.abc import MutableMapping
import functools

from sigtools import _signatures
from sigtools._specifiers import forged_signature


class Name(object):
    def __init__(self, name):
        self.name = name

class Arg(object):
    def __init__(self, name):
        self.name = name

class Unknown(object):
    def __init__(self, source=None):
        self.source = source

    def __repr__(self):
        if self.source is None:
            return "<irrelevant>"
        return "<unknown until runtime: {0}>".format(ast.dump(self.source))

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
    'wrapped num_args named_args '
    'use_varargs use_varkwargs '
    'hide_args hide_kwargs')


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
            self.namespace[arg.arg] = Arg(arg.arg) if main else Unknown(arg)
        for arg in args.kwonlyargs:
            self.namespace[arg.arg] = Arg(arg.arg) if main else Unknown(arg)

        varargs = varkwargs = None
        if args.vararg:
            varargs = self.namespace[args.vararg.arg] = Varargs()
        if args.kwarg:
            varkwargs = self.namespace[args.kwarg.arg] = Varkwargs()
        if main:
            self.varargs = varargs
            self.varkwargs = varkwargs

    def resolve_name(self, name):
        if isinstance(name, ast.Name):
            id = name.id
            return self.namespace.get(id, Name(id))
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
            stararg = self.resolve_name(found)
            if stararg == original:
                return True, False
            return False, True
        else:
            return False, False

    def process_Call(self, node):
        wrapped = self.resolve_name(node.func)
        num_args = len(node.args)
        named_args = [kw.arg for kw in node.keywords]
        use_varargs, hide_args = \
            self.has_hide_starargs(node.starargs, self.varargs)
        use_varkwargs, hide_kwargs = \
            self.has_hide_starargs(node.kwargs, self.varkwargs)
        self.calls.append(Call(
            wrapped, num_args, named_args,
            use_varargs, use_varkwargs,
            hide_args, hide_kwargs))

    def visit_Call(self, node):
        if self.namespace.parent is None:
            self.process_Call(node)
        else:
            self.to_revisit.append((node, self.namespace))

    def __iter__(self):
        return iter(self.calls)


class UnresolvableCall(ValueError):
    pass


def forward_signatures(func, calls, args, kwargs, sig=None):
    sig = _signatures.signature(func) if sig is None else sig
    bap = sig.bind_partial(*args, **kwargs)
    for (
            wrapped, num_args, keywords,
            use_varargs, use_varkwargs,
            hide_args, hide_kwargs) in calls:
        if not (use_varargs or use_varkwargs):
            continue
        if isinstance(wrapped, Name):
            try:
                index = func.__code__.co_freevars.index(wrapped.name)
            except ValueError:
                wrapped_func = func.__globals__[wrapped.name]
            else:
                wrapped_func = func.__closure__[index].cell_contents
        elif isinstance(wrapped, Arg):
            try:
                wrapped_func = bap.arguments[wrapped.name]
            except KeyError:
                raise UnresolvableCall(wrapped)
        else:
            raise UnresolvableCall(wrapped)
        wrapped_sig = forged_signature(wrapped_func)
        try:
            yield _signatures.forwards(
                sig, wrapped_sig,
                num_args,
                hide_args, hide_kwargs,
                use_varargs, use_varkwargs,
                *keywords)
        except ValueError:
            raise UnresolvableCall()


def autoforwards_partial(par, args, kwargs):
    wsig = autoforwards(par.func, par.args, {})
    if wsig is not None:
        return _signatures._mask(
            wsig, len(par.args),
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
        return None
    try:
        code = func.__code__
    except AttributeError:
        return None
    try:
        rawsource = inspect.getsource(code)
    except OSError:
        return None
    source = inspect.cleandoc('\n' + rawsource)
    module = ast.parse(source)
    func_ast = module.body[0]
    return autoforwards_ast(func, func_ast, None, args, kwargs)


def autoforwards_hint(func, args, kwargs):
    h = func._sigtools__autoforwards_hint(func)
    if h is not None:
        return autoforwards_ast(h[0], h[1], h[2], args, kwargs)


def autoforwards_ast(func, func_ast, sig, args=(), kwargs={}):
    sigs = list(forward_signatures(
        func, CallListerVisitor(func_ast),
        args, kwargs, sig))
    if sigs:
        return _signatures.merge(*sigs)


def autoforwards(obj, args=(), kwargs={}):
    try:
        obj._sigtools__autoforwards_hint
    except AttributeError:
        pass
    else:
        return autoforwards_hint(obj, args, kwargs)
    if isinstance(obj, functools.partial):
        return autoforwards_partial(obj, args, kwargs)
    else:
        return autoforwards_function(obj, args, kwargs)
