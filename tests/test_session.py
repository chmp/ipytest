import importlib
import types

import pytest

import ipytest

source = """
def test_foo():
    assert True

def test_bar():
    assert False
"""


@pytest.fixture
def module():
    module = types.ModuleType("dummy_module")
    exec(source, module.__dict__, module.__dict__)
    return module


def test_example(module):
    with ipytest.Session(module) as sess:
        assert sess.main(["{test_foo}"]) == 0
        assert sess.main(["{test_bar}"]) != 0


def test_manual(module):
    with ipytest.Session(module) as sess:
        assert pytest.main([f"{sess.module_path.name}::test_foo"]) == 0
        assert pytest.main([f"{sess.module_path.name}::test_bar"]) != 0


def test_import(module):
    with ipytest.Session(module) as sess:
        mod = importlib.import_module(sess.module_name)
        assert mod is module
