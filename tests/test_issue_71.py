import types

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


def test_run_defopts__auto_magic(ipytest_entry_point):
    """Test defopts="auto" with explicit node id"""
    exit_code = ipytest_entry_point(
        "{MODULE}::test1",
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


def test_run_defopts__auto_magic__deselect(ipytest_entry_point):
    """Test defopts="auto" with --deselect ..."""
    exit_code = ipytest_entry_point(
        "--deselect {MODULE}::test2",
        "",
        module_source,
    )
    assert exit_code == 0


def test_run_defopts__auto_magic__deselect(run_cell_magic):
    """Test defopts="auto" with --deselect ..."""
    exit_code = run_cell_magic(
        "--deselect {MODULE}::test2",
        module_source,
        module=types.ModuleType("dummy_module"),
    )
    assert exit_code == 0
