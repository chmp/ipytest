from __future__ import print_function, absolute_import, division

import unittest
import pytest
import ipytest


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
