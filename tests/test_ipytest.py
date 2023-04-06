import ast
import contextlib
import io
import os.path
import types
from types import ModuleType

import pytest

import ipytest
from ipytest._impl import (
    ArgMapping,
    RewriteAssertTransformer,
    eval_defopts_auto,
    eval_run_kwargs,
)


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
    expected = {k for k, v in spec.items() if not v}
    module = types.ModuleType("module")
    vars(module).update(spec)

    ipytest.clean_tests(module=module)

    assert set(vars(module)) & set(spec) == expected


def test_reprs():
    assert repr(ipytest._config.keep) == "<keep>"
    assert repr(ipytest._config.default) == "<default>"


def fake_module(__name__, **items):
    mod = types.ModuleType(__name__)

    for k, v in items.items():
        setattr(mod, k, v)

    return mod


def test_fixtures():
    @pytest.fixture()
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


def test_program_name():
    with io.StringIO() as fobj, contextlib.redirect_stderr(fobj):
        ipytest.run("--foo")
        res = fobj.getvalue()

    assert "error" in res
    assert "%%ipytest" in res
    assert "ipykernel_launcher.py" not in res


@pytest.mark.parametrize(
    ("cell", "expected"),
    [
        pytest.param("", {}),
        pytest.param("def test():\n    assert True", {}),
        pytest.param(
            "# ipytest: defopts=True\ndef test():\n    ....",
            {"defopts": True},
        ),
        pytest.param("# ipytest: defopts=True", {"defopts": True}),
        pytest.param(
            "# ipytest: defopts=True, clean=True",
            {"defopts": True, "clean": True},
        ),
        pytest.param(
            "# ipytest: defopts =  True, clean  =  True",
            {"defopts": True, "clean": True},
        ),
    ],
)
def test_eval_run_kwargs(cell, expected):
    assert eval_run_kwargs(cell) == expected


@pytest.mark.parametrize("value", [True, False])
def test_eval_run_kwargs__module(value):
    dummy_module = ModuleType("dummy_module")
    dummy_module.defopts = value

    assert eval_run_kwargs("# ipytest: defopts =  defopts", module=dummy_module) == {
        "defopts": value,
        "module": dummy_module,
    }


def test_eval_run_kwargs__module_override():
    dummy_module = ModuleType("dummy_module")
    assert eval_run_kwargs("# ipytest: module=None", module=dummy_module) == {
        "module": None,
    }


@pytest.mark.parametrize("cell", ["", "\n", "\ndef test():\n    assert True"])
def test_eval_run_kwargs__module_2(cell):
    dummy_module = ModuleType("dummy_module")
    assert eval_run_kwargs(cell, module=dummy_module) == {"module": dummy_module}


@pytest.mark.parametrize(
    ("args", "defopts"),
    [
        pytest.param(["tmp_foo.py"], False),
        pytest.param(["tmp_foo.py::test1"], False),
        pytest.param(["-k", "test1"], True),
        pytest.param(["-ktest1"], True),
        pytest.param(["./tests"], True),
    ],
)
def test_eval_defopts_auto__true(args, defopts):
    assert eval_defopts_auto(args, {"MODULE": "tmp_foo.py"}) is defopts


@pytest.mark.parametrize(
    ("key", "expected"),
    [
        pytest.param("MODULE", "tmp_foo.py"),
        pytest.param("test1", "tmp_foo.py::test1"),
        pytest.param("TEST_CASE", "tmp_foo.py::TEST_CASE"),
    ],
)
def test_arg_mapping(key, expected):
    arg_mapping = ArgMapping(MODULE="tmp_foo.py")
    assert arg_mapping[key] == expected


def test_arg_mapping__reserved_key():
    arg_mapping = ArgMapping(MODULE="tmp_foo.py")

    with pytest.raises(KeyError):
        arg_mapping["DUMMY"]


@pytest.mark.parametrize("name", ipytest.__all__)
def test_all_objects_in_all_can_be_imported(name):
    assert hasattr(ipytest, name)
