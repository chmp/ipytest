import pytest

from ipytest._impl import find_coverage_configs


@pytest.mark.parametrize(
    "files, expected",
    [
        pytest.param({".coveragerc": ""}, [".coveragerc"]),
        pytest.param({"setup.cfg": ""}, []),
        pytest.param({"setup.cfg": "[coverage:"}, ["setup.cfg"]),
        pytest.param({"tox.ini": ""}, []),
        pytest.param({"tox.ini": "[coverage:"}, ["tox.ini"]),
        pytest.param({"pyproject.toml": ""}, []),
        pytest.param({"pyproject.toml": "[tool.coverage"}, ["pyproject.toml"]),
        pytest.param(
            {
                ".coveragerc": "",
                "setup.cfg": "[coverage:",
                "pyproject.toml": "[tool.coverage",
                "tox.ini": "[coverage:",
            },
            [".coveragerc", "setup.cfg", "tox.ini", "pyproject.toml"],
        ),
    ],
)
def test_find_coverage_configs(tmp_path, files, expected):
    for name, content in files.items():
        tmp_path.joinpath(name).write_text(content)

    assert [p.name for p in find_coverage_configs(tmp_path)] == expected
