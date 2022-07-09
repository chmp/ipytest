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


def test_run_defopts__run():
    module = types.ModuleType("dummy_module")
    exec(module_source, module.__dict__, module.__dict__)

    exit_code = ipytest.run("{MODULE}::test1", module=module, defopts=False)
    assert exit_code == 0


def test_run_defopts__magic(run_cell_magic):
    exit_code = run_cell_magic(
        "{MODULE}::test1",
        "# ipytest: defopts=False\n\n" + module_source,
        module=types.ModuleType("dummy_module"),
    )
    assert exit_code == 0


def test_run_defopts__auto_run():
    module = types.ModuleType("dummy_module")
    exec(module_source, module.__dict__, module.__dict__)

    exit_code = ipytest.run("{MODULE}::test1", module=module)
    assert exit_code == 0


def test_run_defopts__auto_magic(run_cell_magic):
    exit_code = run_cell_magic(
        "{MODULE}::test1",
        module_source,
        module=types.ModuleType("dummy_module"),
    )
    assert exit_code == 0


def test_run_defopts__auto_magic_filter(run_cell_magic):
    """Make sure defopts="auto" also works with -k ..."""
    exit_code = run_cell_magic(
        "-k test1",
        module_source,
        module=types.ModuleType("dummy_module"),
    )
    assert exit_code == 0
