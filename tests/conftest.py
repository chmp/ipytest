import inspect
import shlex
import types
import unittest.mock

import pytest

import ipytest._config
import ipytest._impl


@pytest.fixture()
def value_from_conftest():
    return 42


@pytest.fixture(params=["func", "magic"])
def ipytest_entry_point(request, run_cell_magic, scoped_config):
    """A unified interface for the main entry points of ipytest"""
    if request.param == "func":

        def run_wrapper(run_args, run_kwargs, source):
            module = types.ModuleType("dummy_module")
            exec(source, module.__dict__, module.__dict__)

            run_args = shlex.split(run_args)
            run_kwargs = eval("dict(" + run_kwargs + ")")

            return ipytest.run(*run_args, module=module, **run_kwargs)

        return run_wrapper

    if request.param == "magic":

        def magic_wrapper(run_args, run_kwargs, source):
            return run_cell_magic(
                run_args,
                source if not run_kwargs else f"# ipytest: {run_kwargs}\n{source}",
                module=types.ModuleType("dummy_module"),
            )

        return magic_wrapper

    raise ValueError(f"Unknown entry point mode {request.param}")


@pytest.fixture()
def run_cell_magic(mock_ipython):
    """A wrapper around ipytest to simplify executing the cell magic"""

    def run_cell_magic(line, cell, *, module=None):
        mock_ipython.module = module

        cell = inspect.cleandoc(cell)
        ipytest._impl.ipytest_magic(line, cell, module=module)

        return ipytest.exit_code

    return run_cell_magic


# NOTE: do not set autouse=True to not interfere with notebook tests
@pytest.fixture()
def scoped_config():
    """A fixture to reset the config at the end of the test"""
    original_config = ipytest._config.current_config.copy()
    try:
        yield ipytest._config.current_config

    finally:
        ipytest._config.current_config.update(original_config)

    ipytest._config._rewrite_transformer = None


# NOTE: do not set autouse=True to not interfere with notebook tests
@pytest.fixture()
def mock_ipython():
    """Register a fake IPython implementation during the test"""
    ipython = MockIPython()

    with unittest.mock.patch("IPython.get_ipython", return_value=ipython):
        yield ipython


class MockIPython:
    def __init__(self, *, module=None):
        self.module = module
        self.ast_transformers = []
        self.magic_functions = {}

    def register_magic_function(self, func, type, name):
        self.magic_functions[name] = type

    def run_cell(self, code):
        exec(code, self.module.__dict__, self.module.__dict__)
