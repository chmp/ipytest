from __future__ import print_function, division, absolute_import

import ast
import contextlib
import pathlib
import shlex
import sys
import tempfile
import threading
import warnings

import packaging.version
import py.path
import pytest

from IPython import get_ipython
from IPython.core.magic import Magics, magics_class, cell_magic

from ._config import config
from ._util import deprecated, clean_tests


def run(*args, module=None, filename=None, plugins=(), return_exit_code=False):
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
    if not config.run_in_thread:
        return _run_impl(
            *args,
            module=module,
            filename=filename,
            plugins=plugins,
            return_exit_code=return_exit_code,
        )

    exit_code = None

    def _thread():
        nonlocal exit_code
        exit_code = _run_impl(
            *args,
            module=module,
            filename=filename,
            plugins=plugins,
            return_exit_code=return_exit_code,
        )

    t = threading.Thread(target=_thread)
    t.start()
    t.join()

    return exit_code


def _run_impl(*args, module, filename, plugins, return_exit_code):
    if module is None:  # pragma: no cover
        import __main__ as module

    with _prepared_module(filename, module) as (valid_filename, prepared_module):
        exit_code = pytest.main(
            list(config.addopts) + list(args) + [valid_filename],
            plugins=(
                list(plugins)
                + [
                    ModuleCollectorPlugin(
                        module=prepared_module, filename=valid_filename
                    )
                ]
            ),
        )

    if config.raise_on_error and exit_code != 0:
        raise RuntimeError(
            "Error in pytest invocation. Exit code: {}".format(exit_code)
        )

    if return_exit_code:
        return exit_code


@contextlib.contextmanager
def _prepared_module(filename, module):
    with _valid_filename(filename, module) as valid_filename:
        with _register_module(valid_filename, module):
            yield valid_filename, module


@contextlib.contextmanager
def _valid_filename(filename, module):
    if filename is None:
        filename = getattr(module, "__file__", None)

    if filename is not None:
        if pathlib.Path(filename).exists():
            yield filename
            return

        else:
            warnings.warn(
                "The configured filename could not be found\n"
                "Consider\n"
                "\n"
                "* removing the explicit filename and using tempfile_fallback=True, or\n"
                "* correcting the filename"
            )

    if not config.tempfile_fallback:
        raise ValueError(
            "module {} has no valid __file__ and tempfile_fallback not configured, please pass filename instead."
        )

    suffix = ".ipynb" if not config.register_module else ".py"
    with tempfile.NamedTemporaryFile(dir=".", suffix=suffix) as f:
        yield f.name


@contextlib.contextmanager
def _register_module(filename, module):
    if not config.register_module:
        yield
        return

    if not config.tempfile_fallback:
        warnings.warn(
            "ipytest is configured with register_module=True and "
            "tempfile_fallback=False. This setup may shadow other modules "
            "and lead to hard-to-debug errors. It is strongly recommended "
            "to only use register_module with the tempfile fallback."
        )

    prev_file = getattr(module, "__file__", False)

    p = pathlib.Path(filename)
    module_name = p.stem
    module_file = str(p.with_suffix(".py"))

    if "." in module_name or " " in module_name:
        raise ValueError(
            "Cannot register module wiht the invalid name {!r}".format(module_name)
        )

    if module_name in sys.modules:
        # TODO: improve the error message
        raise ValueError(
            (
                "Cannot register module wiht name {!r}. Consider not setting "
                "__file__ inside the notebook and using the tempfile_fallback. "
                "This way a random module name will be generated."
            ).format(module_name)
        )

    sys.modules[module_name] = module
    module.__file__ = module_file

    try:
        yield

    finally:
        del sys.modules[module_name]
        if prev_file is False:
            del module.__file__

        else:
            module.__file__ = prev_file


class ModuleCollectorPlugin(object):
    """Small pytest plugin collect an already imported module.
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
    """Wrapper to expose an already imported module.
    """

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

    def __enter__(self):
        self.register()
        return self

    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        self.unregister()

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
        import __main__

        clean_tests(items=__main__.__dict__)
        return self.run_pytest(line, cell)

    @cell_magic
    def run_pytest(self, line, cell):
        # If config.rewrite_asserts is True assertions are being
        # rewritten by default, do not re-rewrite them.
        if not config.rewrite_asserts:
            self.rewrite_asserts(line, cell)

        else:
            self.shell.run_cell(cell)

        import ipytest

        ipytest.exit_code = run(*shlex.split(line), return_exit_code=True)

    @cell_magic
    def rewrite_asserts(self, line, cell):
        """Rewrite asserts with pytest.

        Usage::

            %%rewrite_asserts

            ...

            # new cell:
            from ipytest import run_pytest
            run_pytest()
        """
        if config.rewrite_asserts:
            warnings.warn("skip rewriting as global rewriting is active")
            return

        with RewriteContext(get_ipython()):
            self.shell.run_cell(cell)
