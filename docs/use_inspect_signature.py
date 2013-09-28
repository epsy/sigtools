try:
    from inspect import signature
except ImportError:
    from funcsigs import signature

def process_signature(app, what, name, obj, options,
                      sig, return_annotation):
    try:
        sig = signature(obj)
    except TypeError:
        return sig, return_annotation
    ret_annot = sig.return_annotation
    if ret_annot != sig.empty:
        sret_annot = '-> {0!r}'.format(ret_annot)
        sig = sig.replace(return_annotation=sig.empty)
    else:
        sret_annot = ''
    return str(sig), sret_annot

def setup(app):
    app.connect('autodoc-process-signature', process_signature)
