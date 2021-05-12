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

from ._config import current_config
from . import _util


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
    import ipytest

    run = _util.run_in_thread if current_config["run_in_thread"] else _util.run_direct
    ipytest.exit_code = run(
        _run_impl,
        *args,
        module=module,
        plugins=plugins,
    )


def _run_impl(*args, module, plugins):
    with _prepared_module(module) as (valid_filename, prepared_module):
        full_args = _build_full_args(args, valid_filename)
        plugin = ModuleCollectorPlugin(module=prepared_module, filename=valid_filename)
        return pytest.main(full_args, plugins=[*plugins, plugin])


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

    with valid_filename(module) as filename:
        p = pathlib.Path(filename)
        module_name = p.stem
        module_filename = str(p.with_suffix(".py"))

        with registered_module(module, module_name, module_filename):
            yield filename, module


@contextlib.contextmanager
def valid_filename(module):
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
def registered_module(module, module_name, module_filename):
    if not _util.is_valid_module_name(module_name):
        warnings.warn(f"Cannot register module with the invalid name {module_name!r}")
        yield
        return

    elif module_name in sys.modules:
        warnings.warn(
            f"Cannot register module with name {module_name!r}. It would "
            "override and existing module. Consider not setting __file__ "
            "inside the notebook. This way a random module name will be generated."
        )
        yield
        return

    with _util.patch(module, "__file__", module_filename):
        with _util.register_module(module, module_name):
            yield


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


def get_pytest_version():
    return packaging.version.parse(pytest.__version__)


def run_pytest_clean(line, cell):
    _util.clean_tests()
    get_ipython().run_cell(cell)
    run(*shlex.split(line))


def run_pytest(line, cell):
    get_ipython().run_cell(cell)
    run(*shlex.split(line))
