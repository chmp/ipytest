from __future__ import print_function, division, absolute_import

import py.path
import pytest


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
    if module is None:  # pragma: no cover
        import __main__ as module

    if filename is None:
        try:
            filename = module.__file__

        except AttributeError:
            raise ValueError('module {} has no __file__ attribute, please pass filename instead.')

    return pytest.main(
        list(pytest_options) + [filename],
        plugins=(
            list(pytest_plugins) +
            [ModuleCollectorPlugin(module=module, filename=filename)]
        ),
    )


class ModuleCollectorPlugin(object):
    """Small pytest plugin collect an already imported module.
    """
    def __init__(self, module, filename):
        self.module = module
        self.filename = filename

    def pytest_ignore_collect(self, path):
        return path != py.path.local(self.filename)

    def pytest_collect_file(self, parent, path):
        if path == py.path.local(self.filename):
            return Module(path=path, parent=parent, module=self.module)


class Module(pytest.Module):
    """Wrapper to expose an already imported module.
    """
    def __init__(self, path, parent, module):
        # NOTE: the path has to have a .py suffix, it is only used for printing
        super(Module, self).__init__(path.new(ext='.py'), parent)
        self._module = module

    def _getobj(self):
        return self._module
