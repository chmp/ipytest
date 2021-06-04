import ast
import os.path
import types

import pytest

import ipytest

from ipytest._impl import RewriteAssertTransformer


@pytest.mark.parametrize(
    "spec",
    [
        # any key that maps to true is expected to be removed by clean_tests
        {"test": True, "foo": False},
        {"test_clean": True, "foo": False},
        {"Test": True, "hello": False},
        {"TestClass": True, "world": False},
        {"Test_Class": True, "world": False},
        {"teST": False, "bar": False},
        {"TEst_Class": False, "world": False},
        {"_test_clean": False, "foo": False},
        {"_Test_Class": False, "world": False},
    ],
)
def test_clean(spec):
    expected = {k: v for k, v in spec.items() if not v}
    actual = spec.copy()
    ipytest.clean_tests(items=actual)

    assert actual == expected


def test_reprs():
    assert repr(ipytest._config.keep) == "<keep>"
    assert repr(ipytest._config.default) == "<default>"


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

    ipytest.run(
        module=fake_module(
            __name__="empty_module",
            __file__=os.path.join(os.path.dirname(__file__), "empty_module.py"),
            my_fixture=my_fixture,
            test_example=test_example,
        ),
    )
    assert ipytest.exit_code == 0


def test_parametrize():
    @pytest.mark.parametrize("val", [0, 2, 4, 8, 10])
    def test_example(val):
        assert val % 2 == 0

    ipytest.run(
        module=fake_module(
            __name__="empty_module",
            __file__=os.path.join(os.path.dirname(__file__), "empty_module.py"),
            test_example=test_example,
        ),
    )
    assert ipytest.exit_code == 0


def test_rewrite_assert_transformer_runs():
    with open(__file__, "rt") as fobj:
        source = fobj.read()

    node = ast.parse(source)
    RewriteAssertTransformer().visit(node)
