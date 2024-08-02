import pytest

import ipytest


@pytest.mark.parametrize(
    ("include", "removed"),
    [
        ("foo", ("foo", "foo.bar", "foo.baz")),
        ("foo.bar", ("foo.bar",)),
        ("f", ()),
    ],
)
def test_force_reload_example(include, removed):
    modules = {
        "foo": None,
        "foo.bar": None,
        "foo.baz": None,
    }

    ipytest.force_reload(include, modules=modules)
    assert set(modules) == (set(modules) - set(removed))


def test_forc_reload():
    import empty_module

    empty_module.reload_value = 42
    assert hasattr(empty_module, "reload_value") is True

    ipytest.force_reload("empty_module")

    import empty_module

    assert hasattr(empty_module, "reload_value") is False
