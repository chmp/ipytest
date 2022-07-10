import pytest

import ipytest

source_code = """
def test_example():
    assert False
"""


def test_default_does_not_raise(ipytest_entry_point):
    ipytest_entry_point("", "", source_code)


def test_raises_with_args(ipytest_entry_point):
    with pytest.raises(ipytest.Error):
        ipytest_entry_point("", "raise_on_error=True", source_code)


def test_raises_with_config(ipytest_entry_point):
    ipytest.config(raise_on_error=True)

    with pytest.raises(ipytest.Error):
        ipytest_entry_point("", "", source_code)
