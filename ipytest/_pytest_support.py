from __future__ import print_function, division, absolute_import

import ast
import contextlib
import pathlib
import shlex
import sys
import tempfile
import warnings

import packaging.version
import py.path
import pytest

from IPython import get_ipython
from IPython.core.magic import Magics, magics_class, cell_magic

from ._config import current_config
from ._util import clean_tests, patch, run_direct, run_in_thread


def run(*args, module=None, plugins=()):
    """Execute all tests in the passed module (defaults to __main__) with pytest.

    :param args:
        additional commandline options passed to pytest
    :param module:
        the module containing the tests. If not given, `__main__` will be used.
    :param filename:
        the filename of the file containing the tests. It has to be a real
        file, e.g., a notebook name, since itts existence will be checked by
        pytest. If not given, the `__file__` attribute of the passed module
        will be used.
    :param plugins:
        additional plugins passed to pytest.
    """
    run = run_in_thread if current_config["run_in_thread"] else run_direct
    return run(
        _run_impl,
        *args,
        module=module,
        plugins=plugins,
    )


def _run_impl(*args, module, plugins):
    with _prepared_module(module) as (valid_filename, prepared_module):
        full_args = _build_full_args(args, valid_filename)
        plugin = ModuleCollectorPlugin(module=prepared_module, filename=valid_filename)
        exit_code = pytest.main(full_args, plugins=[*plugins, plugin])

    if current_config["raise_on_error"] and exit_code != 0:
        raise RuntimeError(f"Error in pytest invocation. Exit code: {exit_code}")

    return exit_code


def _build_full_args(args, valid_filename):
    def _fmt(arg):
        return arg.format(MODULE=valid_filename)

    return [
        *(_fmt(arg) for arg in current_config["addopts"]),
        *(_fmt(arg) for arg in args),
        *([valid_filename] if current_config["defopts"] else []),
    ]


@contextlib.contextmanager
def _prepared_module(module):
    if module is None:  # pragma: no cover
        import __main__ as module

    with _valid_filename(module) as valid_filename:
        with _register_module(valid_filename, module):
            yield valid_filename, module


@contextlib.contextmanager
def _valid_filename(module):
    filename = getattr(module, "__file__", None)

    if filename is not None and pathlib.Path(filename).exists():
        yield filename

    else:
        if filename is not None:
            warnings.warn(
                f"The configured filename {filename} could not be found. "
                "A temporary file with be used instead."
            )

        with tempfile.NamedTemporaryFile(dir=".", suffix=".py") as f:
            yield f.name


@contextlib.contextmanager
def _register_module(filename, module):
    p = pathlib.Path(filename)
    module_name = p.stem
    module_file = str(p.with_suffix(".py"))

    if not _is_valid_module_name(module_name):
        raise ValueError(
            f"Cannot register module with the invalid name {module_name!r}"
        )

    if module_name in sys.modules:
        raise ValueError(
            f"Cannot register module with name {module_name!r}. It would "
            "override and existing module. Consider not setting __file__ "
            "inside the notebook. This way a random module name will be generated."
        )

    with patch(module, "__file__", module_file):
        sys.modules[module_name] = module
        try:
            yield

        finally:
            del sys.modules[module_name]


def _is_valid_module_name(name):
    return all(c not in name for c in ".- ")


class ModuleCollectorPlugin(object):
    """Pytest plugin to collect an already imported module.

    Usage::

        pytest.main(
            [],
            plugins=[
                ModuleCollectorPlugin(module, "module.py"),
            ],
        )

    While the filename can be chosen arbitrarily, it must be a file that exists
    on disk, as Pytest will check for its existence. The module itself will be
    handled in the normal way by Pytest during collection.
    """

    def __init__(self, module, filename):
        self.module = module
        self.filename = filename

    def pytest_collect_file(self, parent, path):
        if path == py.path.local(self.filename):
            # NOTE: the path has to have a .py suffix, it is only used for printing
            return Module.from_parent(
                parent, fspath=path.new(ext=".py"), module=self.module
            )


class Module(pytest.Module):
    """Wrapper to expose an already imported module."""

    def _getobj(self):
        return self._module

    @classmethod
    def from_parent(cls, parent, *, fspath, module):
        self = super().from_parent(parent, fspath=fspath)
        self._module = module
        return self


class RewriteContext:
    def __init__(self, shell):
        self.shell = shell
        self.transformer = None

    def register(self):
        assert self.transformer is None

        self.transformer = RewriteAssertTransformer()
        self.shell.ast_transformers.append(self.transformer)

    def unregister(self):
        self.shell.ast_transformers[:] = [
            transformer
            for transformer in self.shell.ast_transformers
            if transformer is not self.transformer
        ]
        self.transformer = None


class RewriteAssertTransformer(ast.NodeTransformer):
    def visit(self, node):
        from _pytest.assertion.rewrite import rewrite_asserts

        pytest_version = get_pytest_version()
        if pytest_version.release[0] >= 5:
            # TODO: re-create a pseudo code to include the asserts?
            rewrite_asserts(node, b"")

        else:
            rewrite_asserts(node)
        return node


def get_pytest_version():
    return packaging.version.parse(pytest.__version__)


@magics_class
class IPyTestMagics(Magics):
    @cell_magic("run_pytest[clean]")
    def run_pytest_clean(self, line, cell):
        clean_tests()
        return self.run_pytest(line, cell)

    @cell_magic
    def run_pytest(self, line, cell):
        import ipytest

        self.shell.run_cell(cell)
        ipytest.exit_code = run(*shlex.split(line))
