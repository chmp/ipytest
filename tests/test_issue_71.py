import types

import pytest

import ipytest

# NOTE: if test selection works, only test1 is executed. Otherwise also test2 is
# executed and exit_code != 0
module_source = """
def test1():
    assert True

def test2():
    assert False
"""


def test_run_defopts(ipytest_entry_point):
    exit_code = ipytest_entry_point(
        "{MODULE}::test1",
        "defopts=False",
        module_source,
    )
    assert exit_code == 0


@pytest.mark.parametrize("node_id", ["{MODULE}::test1", "{test1}"])
def test_run_defopts__auto_magic(ipytest_entry_point, node_id):
    """Test defopts="auto" with explicit node id"""
    exit_code = ipytest_entry_point(
        node_id,
        "",
        module_source,
    )
    assert exit_code == 0


def test_run_defopts__auto_magic__filter(ipytest_entry_point):
    """Test defopts="auto" with -k ..."""
    exit_code = ipytest_entry_point(
        "-k test1",
        "",
        module_source,
    )
    assert exit_code == 0


@pytest.mark.parametrize(
    "node_id",
    ["{MODULE}::test2", "{test2}"],
)
def test_run_defopts__auto_magic__deselect(run_cell_magic, node_id):
    """Test defopts="auto" with --deselect ..."""
    exit_code = run_cell_magic(
        f"--deselect {node_id}",
        module_source,
        module=types.ModuleType("dummy_module"),
    )
    assert exit_code == 0
