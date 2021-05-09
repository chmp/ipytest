from __future__ import print_function, division, absolute_import

import ast
import os.path
import types

import pytest

import ipytest

from ipytest._pytest_support import RewriteAssertTransformer


def fake_module(__name__, **items):
    mod = types.ModuleType(__name__)

    for k, v in items.items():
        setattr(mod, k, v)

    return mod


def test_fixtures():
    @pytest.fixture
    def my_fixture():
        return 42

    def test_example(my_fixture):
        assert my_fixture == 42

    assert 0 == ipytest.run(
        module=fake_module(
            __name__="empty_module",
            __file__=os.path.join(os.path.dirname(__file__), "empty_module.py"),
            my_fixture=my_fixture,
            test_example=test_example,
        ),
    )


def test_parametrize():
    @pytest.mark.parametrize("val", [0, 2, 4, 8, 10])
    def test_example(val):
        assert val % 2 == 0

    assert 0 == ipytest.run(
        module=fake_module(
            __name__="empty_module",
            __file__=os.path.join(os.path.dirname(__file__), "empty_module.py"),
            test_example=test_example,
        ),
    )


def test_rewrite_assert_transformer_runs():
    with open(__file__, "rt") as fobj:
        source = fobj.read()

    node = ast.parse(source)
    RewriteAssertTransformer().visit(node)
