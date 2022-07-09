import unittest.mock
import inspect
import types
import shlex

import pytest

import ipytest._impl


@pytest.fixture(params=["func", "magic"])
def ipytest_entry_point(request, run_cell_magic):
    if request.param == "func":

        def run_wrapper(run_args, run_kwargs, source):
            module = types.ModuleType("dummy_module")
            exec(source, module.__dict__, module.__dict__)

            run_args = shlex.split(run_args)
            run_kwargs = eval("dict(" + run_kwargs + ")")

            return ipytest.run(*run_args, module=module, **run_kwargs)

        return run_wrapper

    elif request.param == "magic":

        def magic_wrapper(run_args, run_kwargs, source):
            return run_cell_magic(
                run_args,
                source if not run_kwargs else f"# ipytest: {run_kwargs}\n{source}",
                module=types.ModuleType("dummy_module"),
            )

        return magic_wrapper

    else:
        raise ValueError(f"Unknown entry point mode {mode}")


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
