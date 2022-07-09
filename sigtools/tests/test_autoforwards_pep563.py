import __future__
import importlib.util

from sigtools.tests import util

spec = importlib.util.find_spec("sigtools.tests.test_autoforwards")

if util.python_has_future_annotations:
    source = spec.loader.get_source(spec.name)

    code = compile(
        source,
        spec.origin,
        "exec",
        __future__.annotations.compiler_flag
    )

    exec(code, globals(), locals())
