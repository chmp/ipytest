import unittest.mock
import inspect

import pytest

import ipytest._impl


@pytest.fixture
def run_cell_magic():
    def run_cell_magic(line, cell, *, module=None):
        ipython = MockIPython(module=module)
        cell = inspect.cleandoc(cell)

        with unittest.mock.patch.object(ipytest._impl, "get_ipython", lambda: ipython):
            ipytest._impl.pytest_magic(line, cell, module=module)

        return ipytest.exit_code

    return run_cell_magic


class MockIPython:
    def __init__(self, *, module):
        self.module = module

    def run_cell(self, code):
        exec(code, self.module.__dict__, self.module.__dict__)
