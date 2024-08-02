import pytest

import ipytest


@pytest.mark.parametrize(
    ("include", "removed"),
    [
        ("foo", ("foo", "foo.bar", "foo.baz")),
        ("foo.bar", ("foo.bar",)),
        ("f", ()),
        ("f*", ("foo", "foo.bar", "foo.baz")),
        ("test_*", ("test_example1", "test_example2")),
        pytest.param("*.", (), id="invalid pattern"),
        ("*.bar", ("foo.bar",)),
        ("foo.ba?", ("foo.bar", "foo.baz")),
    ],
)
def test_force_reload_example(include, removed):
    modules = {
        "foo": None,
        "foo.bar": None,
        "foo.baz": None,
        "test_example1": None,
        "test_example2": None,
    }
    expected = set(modules) - set(removed)

    ipytest.force_reload(include, modules=modules)
    assert set(modules) == expected


def test_forc_reload():
    import empty_module

    empty_module.reload_value = 42
    assert hasattr(empty_module, "reload_value") is True

    ipytest.force_reload("empty_module")

    import empty_module

    assert hasattr(empty_module, "reload_value") is False
