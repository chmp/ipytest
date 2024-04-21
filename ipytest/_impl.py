import ast
import contextlib
import fnmatch
import importlib
import os
import pathlib
import re
import shlex
import sys
import threading
import uuid
from types import ModuleType
from typing import Any, Dict, Mapping, Optional, Sequence

import packaging.version
import pytest

from ._config import current_config, default

RANDOM_MODULE_PATH_RETRIES = 10


def run(
    *args,
    module=None,
    plugins=(),
    run_in_thread=default,
    raise_on_error=default,
    addopts=default,
    defopts=default,
    display_columns=default,
    coverage=default,
):
    """Execute all tests in the passed module (defaults to `__main__`) with pytest.

    This function is a thin wrapper around `pytest.main` and will execute any tests
    defined in the current notebook session.

    **NOTE:** In the default configuration `ipytest.run()` will not raise
    exceptions, when tests fail. To raise exceptions on test errors, e.g.,
    inside a CI/CD context, use `ipytest.autoconfig(raise_on_error=True)`.

    **Parameters:**

    - `args`: additional commandline options passed to pytest
    - `module`: the module containing the tests. If not given, `__main__` will
      be used.
    - `plugins`: additional plugins passed to pytest.

    The following parameters override the config options set with
    [`ipytest.config()`][ipytest.config] or
    [`ipytest.autoconfig()`][ipytest.autoconfig].

    - `run_in_thread`: if given, override the config option "run_in_thread".
    - `raise_on_error`: if given, override the config option "raise_on_error".
    - `addopts`: if given, override the config option "addopts".
    - `defopts`: if given, override the config option "defopts".
    - `display_columns`: if given, override the config option "display_columns".

    **Returns**: the exit code of `pytest.main`.
    """
    import ipytest

    run_in_thread = default.unwrap(run_in_thread, current_config["run_in_thread"])
    raise_on_error = default.unwrap(raise_on_error, current_config["raise_on_error"])
    addopts = default.unwrap(addopts, current_config["addopts"])
    defopts = default.unwrap(defopts, current_config["defopts"])
    display_columns = default.unwrap(display_columns, current_config["display_columns"])
    coverage = default.unwrap(coverage, current_config["coverage"])

    if module is None:
        import __main__ as module

    run = run_func_in_thread if run_in_thread else run_func_direct
    exit_code = run(
        _run_impl,
        *args,
        module=module,
        plugins=plugins,
        addopts=addopts,
        defopts=defopts,
        display_columns=display_columns,
        coverage=coverage,
    )

    ipytest.exit_code = exit_code

    if raise_on_error is True and exit_code != 0:
        raise Error(exit_code)

    return exit_code


class Error(RuntimeError):
    """Error raised by ipytest on test failure"""

    def __init__(self, exit_code):
        super().__init__(exit_code)

    def __str__(self):
        return f"ipytest failed with exit_code {self.args[0]}"


def ipytest_magic(line, cell, module=None):
    """IPython magic to first execute the cell, then execute [`ipytest.run()`][ipytest.run].

    **Note:** the magics are only available after running
    [`ipytest.autoconfig()`][ipytest.autoconfig] or
    [`ipytest.config(magics=True)`][ipytest.config].

    It cleans any previously found tests, i.e., only tests defined in the
    current cell are executed. To disable this behavior, use
    [`ipytest.config(clean=False)`][ipytest.config].

    Any arguments passed on the magic line are interpreted as command line
    arguments to to pytest. For example calling the magic as

    ```python
    %%ipytest -qq
    ```

    is equivalent to passing `-qq` to pytest. The arguments are formatted using
    Python's standard string formatting. Currently, only the `{MODULE}` variable
    is understood. It is replaced with the filename associated with the
    notebook. In addition node ids for tests can be generated by using the test
    name as a key, e.g., `{test_example}` will expand to
    `{MODULE}::test_example`.

    The keyword arguments passed to [`ipytest.run()`][ipytest.run] can be
    customized by including a comment of the form `# ipytest: arg1=value1,
    arg=value2` in the cell source. For example:

    ```python
    %%ipytest {MODULE}::test1
    # ipytest: defopts=False
    ```

    is equivalent to `ipytest.run("{MODULE}::test1", defopts=False)`. In this
    case, it deactivates default arguments and then instructs pytest to only
    execute `test1`.

    **NOTE:** In the default configuration `%%ipytest` will not raise
    exceptions, when tests fail. To raise exceptions on test errors, e.g.,
    inside a CI/CD context, use `ipytest.autoconfig(raise_on_error=True)`.
    """
    from IPython import get_ipython

    run_args = shlex.split(line)
    run_kwargs = eval_run_kwargs(cell, module=module)

    clean(module=run_kwargs.get("module"))

    try:
        get_ipython().run_cell(cell)

    except TypeError as e:
        if "raw_cell" in str(e):
            raise RuntimeError(
                "The ipytest magic cannot evaluate the cell. Most likely you "
                "are running a modified ipython version. Consider using "
                "`ipytest.run` and `ipytest.clean` directly.",
            ) from e

        raise e

    run(*run_args, **run_kwargs)


# NOTE equivalent to @no_var_expand but does not require an IPython import
# See also: IPython.core.magic.no_var_expand
ipytest_magic._ipython_magic_no_var_expand = True


def clean(pattern=default, *, module=None):
    """Delete tests with names matching the given pattern.

    In IPython the results of all evaluations are kept in global variables
    unless explicitly deleted. This behavior implies that when tests are renamed
    the previous definitions will still be found if not deleted. This method
    aims to simply this process.

    An effective pattern is to start with the cell containing tests with a call
    to [`ipytest.clean()`][ipytest.clean], then defined all test cases, and
    finally call [`ipytest.run()`][ipytest.run]. This way renaming tests works
    as expected.

    **Parameters:**

    - `pattern`: a glob pattern used to match the tests to delete. If not given,
      the `"clean"` config option is used.
    - `items`: the globals object containing the tests. If `None` is given, the
        globals object is determined from the call stack.
    """
    pattern = default.unwrap(pattern, current_config["clean"])

    if pattern is False:
        return

    if module is None:
        import __main__ as module

    items = vars(module)
    to_delete = [key for key in items if fnmatch.fnmatchcase(key, pattern)]

    for key in to_delete:
        del items[key]


def reload(*mods):
    """Reload all modules passed as strings.

    This function may be useful, when mixing code in external modules and
    notebooks.

    Usage:

    ```python
    ipytest.reload("ipytest._util", "ipytest")
    ```
    """
    for mod in mods:
        importlib.reload(importlib.import_module(mod))


def force_reload(*include: str, modules: Optional[Dict[str, ModuleType]] = None):
    """Ensure following imports of the listed modules reload the code from disk

    The given modules and their submodules are removed from `sys.modules`.
    Next time the modules are imported, they are loaded from disk.

    If given, the parameter `modules` should be a dictionary of modules to use
    instead of `sys.modules`.

    Usage:

    ```python
    ipytest.force_reload("my_package")
    from my_package.submodule import my_function
    ```
    """
    if modules is None:
        modules = sys.modules

    include_exact = set(include)
    include_prefixes = tuple(name + "." for name in include)

    to_delete = [
        name
        for name in modules
        if (name in include_exact or name.startswith(include_prefixes))
    ]

    for name in to_delete:
        modules.pop(name, None)


def _run_impl(*args, module, plugins, addopts, defopts, display_columns, coverage):
    with _prepared_env(module, display_columns=display_columns) as filename:
        full_args = _build_full_args(
            args, filename, addopts=addopts, defopts=defopts, coverage=coverage
        )
        if coverage:
            warn_for_existing_coverage_configs()

        return pytest.main(full_args, plugins=[*plugins, FixProgramNamePlugin()])


def _build_full_args(args, filename, *, addopts, defopts, coverage):
    arg_mapping = ArgMapping(
        # use basename to ensure --deselect works
        # (see also: https://github.com/pytest-dev/pytest/issues/6751)
        MODULE=os.path.basename(filename),
    )

    def _fmt(arg):
        return arg.format_map(arg_mapping)

    if coverage:
        import ipytest.cov

        coverage_args = ("--cov", f"--cov-config={ipytest.cov.config_path}")

    else:
        coverage_args = ()

    all_args = [
        *coverage_args,
        *(_fmt(arg) for arg in addopts),
        *(_fmt(arg) for arg in args),
    ]

    if defopts == "auto":
        defopts = eval_defopts_auto(all_args, arg_mapping)

    return [*all_args, *(["--", filename] if defopts else [])]


class ArgMapping(dict):
    def __missing__(self, key):
        if not (key.isalpha() and key.isupper()):
            return f"{self['MODULE']}::{key}"

        raise KeyError(
            f"Unknown format key {key!r} (known keys: {list(self)}). To "
            f"create the node id for a test with all uppercase characters use "
            f"'{{MODULE}}::{key}'.",
        )


@contextlib.contextmanager
def _prepared_env(module, *, display_columns):
    with random_module_path() as path:
        module_name = path.stem

        if not is_valid_module_name(module_name):
            raise RuntimeError(
                f"Invalid module name {module_name!r} generated by tempfile. "
                "This should not happen, please open an issue at "
                "'https://github.com/chmp/ipytest/issues' to report a bug.",
            )

        if module_name in sys.modules:
            raise RuntimeError(
                f"Cannot register module with name {module_name!r}. It would "
                "override an existing module. This should not happen. Please "
                "report a bug at 'https://github.com/chmp/ipytest/issues'.",
            )

        with patch(module, "__file__", str(path)), register_module(module, module_name):
            with patched_columns(display_columns=display_columns):
                yield str(path)


class RewriteAssertTransformer(ast.NodeTransformer):
    def register_with_shell(self, shell):
        shell.ast_transformers.append(self)

    def unregister_with_shell(self, shell):
        shell.ast_transformers[:] = [
            transformer
            for transformer in shell.ast_transformers
            if transformer is not self
        ]

    def visit(self, node):
        from _pytest.assertion.rewrite import rewrite_asserts

        pytest_version = get_pytest_version()
        if pytest_version.release[0] >= 5:
            # get the currently executing code from ipython?
            # TODO: re-create a pseudo code to include the asserts?
            rewrite_asserts(node, b"")

        else:
            rewrite_asserts(node)

        self._custom_fix_locations(node)

        return node

    @staticmethod
    def _custom_fix_locations(node):
        if isinstance(node, ast.Module):
            for item in node.body:
                if hasattr(item, "end_lineno") and item.end_lineno is None:
                    item.end_lineno = item.lineno


class FixProgramNamePlugin:
    def pytest_addoption(self, parser):
        # Explanation:
        #
        # - the prog instance variable is defined, but never overwritten [1]
        # - this variable is passed to the the underlying argparse Parser [2]
        # - with a `None` value argparse uses sys.argv array to determine the
        #   program name
        #
        # [1]: https://github.com/pytest-dev/pytest/blob/6d6bc97231f2d9a68002f1d191828fd3476ca8b8/src/_pytest/config/argparsing.py#L41
        # [2]: https://github.com/pytest-dev/pytest/blob/6d6bc97231f2d9a68002f1d191828fd3476ca8b8/src/_pytest/config/argparsing.py#L397
        # [3]: https://github.com/pytest-dev/pytest/blob/6d6bc97231f2d9a68002f1d191828fd3476ca8b8/src/_pytest/config/argparsing.py#L119
        #
        parser.prog = "%%ipytest"


def get_pytest_version():
    return packaging.version.parse(pytest.__version__)


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
def random_module_path():
    filename = getattr(random_module_path, "_filename", None)

    if filename is None:
        for _ in range(RANDOM_MODULE_PATH_RETRIES):
            filename = f"t_{uuid.uuid4().hex}.py"

            if pathlib.Path(filename).exists():
                continue

            setattr(random_module_path, "_filename", filename)
            break

        else:
            raise RuntimeError("Internal error: Could not generate a module filename")

    path = pathlib.Path(filename)
    if path.exists():
        raise RuntimeError(f"Module filename {filename} does already exist")
    path.write_text("")

    try:
        yield path

    finally:
        path.unlink()


@contextlib.contextmanager
def register_module(obj, name):
    if name in sys.modules:
        raise RuntimeError(f"Cannot overwrite existing module {name}")

    sys.modules[name] = obj
    try:
        yield

    finally:
        del sys.modules[name]


@contextlib.contextmanager
def patched_columns(*, display_columns):
    if not display_columns:
        yield
        return

    # NOTE: since values have to be strings, None identifies unset values
    prev_columns = os.environ.get("COLUMNS")

    os.environ["COLUMNS"] = str(display_columns)
    yield

    if prev_columns is not None:
        os.environ["COLUMNS"] = prev_columns

    else:
        del os.environ["COLUMNS"]


def run_func_direct(func, *args, **kwargs):
    return func(*args, **kwargs)


def run_func_in_thread(func, *args, **kwargs):
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


RUN_OPTIONS_MARKER = "# ipytest:"


def eval_run_kwargs(cell: str, module=None) -> Dict[str, Any]:
    """Parse the `ipytest:` comment inside a cell

    If the cell does not start with `# ipytest:` and empty dict is returned.
    Otherwise, the rest of the line is evaluated as keyword args. Any references
    to variables are evaluated to the module object. If not given it defaults to
    `__main__`.

    If the module is given and not overwritten inside the comment, it is also
    returned as keyword argument.
    """
    if module is not None:
        eval_module = module

    else:
        import __main__ as eval_module

    lines = cell.splitlines()
    if not lines:
        return {"module": module} if module is not None else {}

    first_line = lines[0]
    if not first_line.startswith(RUN_OPTIONS_MARKER):
        return {"module": module} if module is not None else {}

    run_options = first_line[len(RUN_OPTIONS_MARKER) :]
    kwargs = eval(f"dict({run_options!s})", eval_module.__dict__, eval_module.__dict__)

    if "module" not in kwargs and module is not None:
        kwargs["module"] = module

    return kwargs


def eval_defopts_auto(args: Sequence[str], arg_mapping: Mapping[str, str]) -> bool:
    """Parse the arguments and determine whether to add the notebook"""

    module_name = arg_mapping["MODULE"]

    def is_notebook_node_id(prev: Optional[str], arg: str) -> bool:
        return (
            prev not in {"-k", "--deselect"}
            and not arg.startswith("-")
            and arg.startswith(module_name)
        )

    return all(
        not is_notebook_node_id(prev, arg) for prev, arg in zip([None, *args], args)
    )


def warn_for_existing_coverage_configs():
    if configs := find_coverage_configs("."):
        print(
            "Warning: found existing coverage.py configuration in "
            f"{[p.name for p in configs]}. "
            "These config files are ignored when using "
            "`ipytest.autoconfig(coverage=True)`."
            "Consider adding the `ipytest.cov` plugin directly to the config "
            "files and adding  `--cov` to the `%%ipytest` invocation.",
            file=sys.stderr,
        )


def find_coverage_configs(root):
    root = pathlib.Path(root)

    result = []
    if (p := root.joinpath(".coveragerc")).exists():
        result.append(p)

    result += _find_files_with_lines(root, ["setup.cfg", "tox.ini"], r"^\[coverage:.*$")
    result += _find_files_with_lines(root, ["pyproject.toml"], r"^\[tool\.coverage.*$")

    return result


def _find_files_with_lines(root, paths, pat):
    for path in paths:
        path = root.joinpath(path)
        if path.exists():
            try:
                with open(path, "rt") as fobj:
                    for line in fobj:
                        if re.match(pat, line) is not None:
                            yield path
                            break

            except Exception:
                pass
