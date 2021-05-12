import contextlib
import fnmatch
import importlib
import sys
import threading

from ._config import current_config


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
        import __main__

        items = vars(__main__)

    if pattern is None:
        pattern = current_config["clean"]

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


@contextlib.contextmanager
def patch(obj, attr, val):
    had_attr = hasattr(obj, attr)
    prev_val = getattr(obj, attr, None)

    setattr(obj, attr, val)

    try:
        yield

    finally:
        if not had_attr:
            delattr(obj, attr)

        else:
            setattr(obj, attr, prev_val)


@contextlib.contextmanager
def register_module(obj, name):
    if name in sys.modules:
        raise RuntimeError(f"Cannot overwrite existing module {name}")

    sys.modules[name] = obj
    try:
        yield

    finally:
        del sys.modules[name]


def run_direct(func, *args, **kwargs):
    return func(*args, **kwargs)


def run_in_thread(func, *args, **kwargs):
    res = None

    def _thread():
        nonlocal res
        res = func(*args, **kwargs)

    t = threading.Thread(target=_thread)
    t.start()
    t.join()

    return res


def is_valid_module_name(name):
    return all(c not in name for c in ".- ")
