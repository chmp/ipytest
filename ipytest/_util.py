import fnmatch
import functools as ft
import importlib
import inspect
import os
import sys

from ._config import config


def clean_tests(pattern=None, items=None):
    """Delete tests with names matching the given pattern.

    In IPython the results of all evaluations are kept in global variables
    unless explicitly deleted. This behavior implies that when tests are renamed
    the previous definitions will still be found if not deleted. This method
    aims to simply this process.

    An effecitve pattern is to start with the cell containing tests with a call
    to `clean_tests`, then defined all test cases, and finally call `run_tests`.
    This way renaming tests works as expected.

    **Arguments:**

    - `pattern`: a glob pattern used to match the tests to delete.
    - `items`: the globals object containing the tests. If `None` is given, the
        globals object is determined from the call stack.
    """
    if items is None:
        items = _get_globals_of_caller(distance=1)

    if pattern is None:
        pattern = config.clean

    to_delete = [key for key in items.keys() if fnmatch.fnmatchcase(key, pattern)]

    for key in to_delete:
        del items[key]


def reload(*mods):
    """Reload all modules passed as strings.

    This function may be useful, when mixing code in external modules and
    notebooks.

    Usage::

        reload("ipytest._util", "ipytest")

    """
    for mod in mods:
        importlib.reload(importlib.import_module(mod))


def deprecated(message):
    def decorator(func):
        @ft.wraps(func)
        def impl(*args, **kwargs):
            emit_deprecation_warning(message)
            return func(*args, **kwargs)

        return impl

    return decorator


def emit_deprecation_warning(message):
    if message in emit_deprecation_warning.warned:
        return

    emit_deprecation_warning.warned.add(message)
    print(message, file=sys.stderr)


emit_deprecation_warning.warned = set()


def running_as_test():
    """Check whether the notebook is executed as a test.

    This function may be useful, when running notebooks as integration tests to
    ensure the runtime is not exceedingly long.

    Usage::

        model.fit(x, y, epochs=500 if not ipytest.running_as_test() else 1)

    """
    return os.environ.get("PYTEST_CURRENT_TEST") is not None


def _get_globals_of_caller(distance=0):
    stack = inspect.stack()
    frame_record = stack[distance + 1]
    return frame_record[0].f_globals
