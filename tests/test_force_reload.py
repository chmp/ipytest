import pytest

import ipytest


@pytest.mark.parametrize(
    "include, expected",
    [
        ("foo", ()),
        ("foo.bar", ("foo", "foo.baz")),
        ("f", ("foo", "foo.bar", "foo.baz")),
    ],
)
def test_force_reload_example(include, expected):
    modules = {
        "foo": None,
        "foo.bar": None,
        "foo.baz": None,
    }

    ipytest.force_reload(include, modules=modules)
    assert set(modules) == set(expected)


def test_forc_reload():
    import empty_module

    empty_module.reload_value = 42
    assert hasattr(empty_module, "reload_value") is True

    ipytest.force_reload("empty_module")

    import empty_module

    assert hasattr(empty_module, "reload_value") is False
