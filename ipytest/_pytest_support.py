from __future__ import print_function, division, absolute_import

import ast
import contextlib
import shlex
import warnings
import tempfile

import py.path
import pytest

from IPython import get_ipython
from IPython.core.magic import Magics, magics_class, cell_magic

from ._config import config
from ._util import deprecated, clean_tests


@deprecated("ipytest.run_pytest is deprecated, prefer ipytest.run.")
def run_pytest(module=None, filename=None, pytest_options=(), pytest_plugins=()):
    """Execute tests in the passed module (defaults to __main__) with pytest.

    **Arguments:**

    - `module`: the module containing the tests.
      If not given, `__main__` will be used.
    - `filename`: the filename of the file containing the tests.
      It has to be a real file, e.g., a notebook name, since itts existence will
      be checked by pytest.
      If not given, the `__file__` attribute of the passed module will be used.
    - `pytest_options`: additional options passed to pytest
    - `pytest_plugins`: additional plugins passed to pytest.
    """
    return run(
        *pytest_options,
        filename=filename,
        module=module,
        plugins=pytest_plugins,
        return_exit_code=True,
    )


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
    if module is None:  # pragma: no cover
        import __main__ as module

    with _valid_filename(filename, module) as valid_filename:
        exit_code = pytest.main(
            list(config.addopts) + list(args) + [valid_filename],
            plugins=(
                list(plugins)
                + [ModuleCollectorPlugin(module=module, filename=valid_filename)]
            ),
        )

    if config.raise_on_error and exit_code != 0:
        raise RuntimeError(
            "Error in pytest invocation. Exit code: {}".format(exit_code)
        )

    if return_exit_code:
        return exit_code


@contextlib.contextmanager
def _valid_filename(filename, module):
    if filename is not None:
        yield filename
        return

    filename = getattr(module, "__file__", None)
    if filename is not None:
        yield filename
        return

    if not config.tempfile_fallback:
        raise ValueError(
            "module {} has no valid __file__, please pass filename instead."
        )

    # generate an empty temporary file to use as a fallback
    with tempfile.NamedTemporaryFile(dir=".", suffix=".ipynb") as f:
        yield f.name


class ModuleCollectorPlugin(object):
    """Small pytest plugin collect an already imported module.
    """

    def __init__(self, module, filename):
        self.module = module
        self.filename = filename

    def pytest_collect_file(self, parent, path):
        if path == py.path.local(self.filename):
            return Module(path=path, parent=parent, module=self.module)


class Module(pytest.Module):
    """Wrapper to expose an already imported module.
    """

    def __init__(self, path, parent, module):
        # NOTE: the path has to have a .py suffix, it is only used for printing
        super(Module, self).__init__(path.new(ext=".py"), parent)
        self._module = module

    def _getobj(self):
        return self._module


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

        rewrite_asserts(node)
        return node


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
