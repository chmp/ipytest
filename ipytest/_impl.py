from __future__ import print_function, division, absolute_import

import ast
import contextlib
import fnmatch
import importlib
import os
import pathlib
import shlex
import sys
import tempfile
import threading
from types import ModuleType

from typing import Any, Dict, Mapping, Optional, Sequence, Union

import packaging.version
import pytest

from ._config import current_config, default


def run(
    *args: str,
    module: Optional[ModuleType] = None,
    plugins: Sequence[object] = (),
) -> Union[int, pytest.ExitCode]:
    """Execute all tests in the passed module (defaults to `__main__`) with pytest.

    **Parameters:**

    - `args`: additional command line options passed to pytest
    - `module`: the module containing the tests. If not given, `__main__` will
      be used.
    - `plugins`: additional plugins passed to pytest.

    **Returns**: the exit code of `pytest.main`.
    """
    return Session(module).main(args, plugins)


def main(
    args: Optional[Sequence[str]] = None,
    plugins: Optional[Sequence[object]] = None,
) -> Union[int, pytest.ExitCode]:
    """A wrapper around `pytest.main` that registers the current notebook.

    **Parameters:**

    - `args`: additional command line options passed to pytest
    - `plugins`: additional plugins passed to pytest.

    **Returns**: the exit code of `pytest.main`.
    """
    return Session().main(args, plugins)


class Error(RuntimeError):
    """Error raised by ipytest on test failure"""

    def __init__(self, exit_code):
        super().__init__(exit_code)

    def __str__(self):
        return f"ipytest failed with exit_code {self.args[0]}"


def pytest_magic(line: str, cell: str, module: Optional[ModuleType] = None):
    """IPython magic to first execute the cell, then execute [`ipytest.run()`][ipytest.run].

    **Note:** the magics are only available after running
    [`ipytest.autoconfig()`][ipytest.autoconfig] or
    [`ipytest.config(magics=True)`][ipytest.config].

    It cleans any previously found tests, i.e., only tests defined in the
    current cell are executed. To disable this behavior, use
    [`ipytest.config(clean=False)`][ipytest.config].

    Any arguments passed on the magic line are interpreted as command line
    arguments to pytest. For example calling the magic as

    ```python
    %%ipytest -qq
    ```

    is equivalent to passing `-qq` to pytest. See also the section ["How does it
    work"](#how-does-it-work) for further details.

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
    """

    run_args = shlex.split(line)
    run_kwargs = eval_run_kwargs(cell, module=module)

    clean(module=run_kwargs.get("module"))
    _ipython_run_cell(cell)
    Session(**run_kwargs).main(run_args)


# NOTE equivalent to @no_var_expand but does not require an IPython import
# See also: IPython.core.magic.no_var_expand
pytest_magic._ipython_magic_no_var_expand = True


def _ipython_run_cell(cell):
    from IPython import get_ipython

    try:
        get_ipython().run_cell(cell)

    except TypeError as e:
        if "raw_cell" in str(e):
            raise RuntimeError(
                "The ipytest magic cannot evaluate the cell. Most likely you "
                "are running a modified ipython version. Consider using "
                "`ipytest.run` and `ipytest.clean_tests` directly."
            ) from e

        else:
            raise e


def clean(*, pattern: str = default, module: Optional[ModuleType] = None):
    """Delete tests defined in the notebook scope.

    In IPython the results of all evaluations are kept in global variables
    unless explicitly deleted. This behavior implies that when tests are renamed
    the previous definitions will still be found if not deleted. This method
    aims to simply this process.

    An effective pattern is to start with the cell containing tests with a call
    to [`ipytest.clean()`][ipytest.clean], then define all test cases, and
    finally call [`ipytest.run()`][ipytest.run]. This way renaming tests works
    as expected.

    **Parameters:**

    - `pattern`: a glob pattern used to match the tests to delete. If not given,
      the `"clean"` config option is used.
    - `module`: the module to delete the tests from. If `None` is given, the
      current notebook context (`__main__`) is used.
    """
    clean_tests(pattern=pattern, items=vars(module) if module is not None else None)


def clean_tests(pattern: str = default, *, items: Dict[str, Any] = None):
    """Delete tests with names matching the given pattern.

    In IPython the results of all evaluations are kept in global variables
    unless explicitly deleted. This behavior implies that when tests are renamed
    the previous definitions will still be found if not deleted. This method
    aims to simply this process.

    An effective pattern is to start with the cell containing tests with a call
    to [`ipytest.clean_tests()`][ipytest.clean_tests], then define all test
    cases, and finally call [`ipytest.run()`][ipytest.run]. This way renaming
    tests works as expected.

    **Parameters:**

    - `pattern`: a glob pattern used to match the tests to delete. If not given,
      the `"clean"` config option is used.
    - `items`: the globals object containing the tests. If `None` is given, the
      globals of the current notebook context `__main__` is used.
    """
    pattern = default.unwrap(pattern, current_config["clean"])

    if pattern is False:
        return

    if items is None:
        import __main__ as module

        items = vars(module)

    to_delete = [key for key in items.keys() if fnmatch.fnmatchcase(key, pattern)]

    for key in to_delete:
        del items[key]


def reload(*mods: str):
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


class Session:
    """A Session to run pytest with access to a temporary module

    The following parameters override the config options set with
    [`ipytest.config()`][ipytest.config] or
    [`ipytest.autoconfig()`][ipytest.autoconfig]:

    - `run_in_thread`: if given, override the config option "run_in_thread".
    - `raise_on_error`: if given, override the config option "raise_on_error".
    - `addopts`: if given, override the config option "addopts".
    - `defopts`: if given, override the config option "defopts".
    - `display_columns`: if given, override the config option "display_columns".

    Inside an active session the file `self.module_path` can be used inside
    pytest to refer to the current notebook. For example, pytest can be manually
    executed via:

    ```python
    with ipytest.Session() as sess:
        pytest.main([str(sess.module_path)])
    ```
    """

    def __init__(
        self,
        module=None,
        *,
        run_in_thread=default,
        raise_on_error=default,
        addopts=default,
        defopts=default,
        display_columns=default,
    ):
        if module is None:
            import __main__ as module

        self.module = module
        self.run_in_thread = default.unwrap(
            run_in_thread, current_config["run_in_thread"]
        )
        self.raise_on_error = default.unwrap(
            raise_on_error, current_config["raise_on_error"]
        )
        self.addopts = default.unwrap(addopts, current_config["addopts"])
        self.defopts = default.unwrap(defopts, current_config["defopts"])
        self.display_columns = default.unwrap(
            display_columns, current_config["display_columns"]
        )

        self._context = None
        self._module_path = None

    def __enter__(self):
        if self._context is not None:
            raise RuntimeError(
                "Session is not reentrant: cannot use a session in nested " "contexts."
            )

        self._context = _prepared_env(self.module, display_columns=self.display_columns)
        self._module_path = self._context.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb):
        if self._context is None:
            raise RuntimeError("Cannot close a closed session")

        res = self._context.__exit__(exc_type, exc, tb)
        self._context = None
        self._module_path = None
        return res

    def main(
        self,
        args: Optional[Sequence[str]] = None,
        plugins: Optional[Sequence[object]] = None,
    ):
        with _maybe_enter(self):
            exit_code = self._run(
                pytest.main,
                self.build_args(args),
                self.build_plugins(plugins),
            )

        self.handle_exit_code(exit_code)
        return exit_code

    def build_args(self, args: Optional[Sequence[str]] = None) -> Sequence[str]:
        arg_mapping = ArgMapping(
            # use basename to ensure --deselect works
            # (see also: https://github.com/pytest-dev/pytest/issues/6751)
            MODULE=self.module_path.name,
        )

        def _fmt(arg):
            return arg.format_map(arg_mapping)

        all_args = [_fmt(arg) for arg in self.addopts]

        if args is not None:
            all_args.extend(_fmt(arg) for arg in args)

        if (self.defopts is True) or (
            self.defopts == "auto" and eval_defopts_auto(all_args, arg_mapping)
        ):
            all_args.append(_fmt("{MODULE}"))

        return all_args

    def build_plugins(
        self, plugins: Optional[Sequence[object]] = None
    ) -> Sequence[object]:
        return [
            *(plugins if plugins is not None else ()),
            FixProgramNamePlugin(),
        ]

    def handle_exit_code(self, exit_code):
        import ipytest

        ipytest.exit_code = exit_code

        if self.raise_on_error is True and exit_code != 0:
            raise Error(exit_code)

    def _run(self, func, *args, **kwargs):
        if not self.run_in_thread:
            return func(*args, **kwargs)

        res = None

        def _thread():
            nonlocal res
            res = func(*args, **kwargs)

        t = threading.Thread(target=_thread)
        t.start()
        t.join()

        return res

    @property
    def is_active(self):
        return self._context is not None

    @property
    def module_name(self):
        return self.module_path.stem

    @property
    def module_path(self):
        if self._module_path is None:
            raise AttributeError("module_path")

        return self._module_path


class ArgMapping(dict):
    def __missing__(self, key):
        if not (key.isalpha() and key.isupper()):
            return f"{self['MODULE']}::{key}"

        raise KeyError(
            f"Unknown format key {key!r} (known keys: {list(self)}). To "
            f"create the node id for a test with all uppercase characters use "
            f"'{{MODULE}}::{key}'."
        )


@contextlib.contextmanager
def _maybe_enter(ctx):
    if ctx.is_active:
        yield

    else:
        with ctx:
            yield


@contextlib.contextmanager
def _prepared_env(module, *, display_columns):
    with tempfile.NamedTemporaryFile(dir=".", suffix=".py") as f:
        path = pathlib.Path(f.name)
        module_name = path.stem

        if not is_valid_module_name(module_name):
            raise RuntimeError(
                f"Invalid module name {module_name!r} generated by tempfile. "
                "This should not happen, please open an issue at "
                "'https://github.com/chmp/ipytest/issues' to report a bug."
            )

        if module_name in sys.modules:
            raise RuntimeError(
                f"Cannot register module with name {module_name!r}. It would "
                "override an existing module. This should not happen. Please "
                "report a bug at 'https://github.com/chmp/ipytest/issues'."
            )

        with patch(module, "__file__", str(path)):
            with register_module(module, module_name):
                with patched_columns(display_columns=display_columns):
                    yield path


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
            # TODO: re-create a pseudo code to include the asserts?
            rewrite_asserts(node, b"")

        else:
            rewrite_asserts(node)
        return node


class FixProgramNamePlugin:
    def pytest_addoption(self, parser):
        # Explanation:
        #
        # - the prog instance variable is defined, but never overwritten [1]
        # - this variable is passed to the the underlying argparse Parser [2]
        #   via [3]
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
