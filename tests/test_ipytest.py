from __future__ import print_function, absolute_import, division

import unittest
import pytest
import ipytest


class TestDiscovery(unittest.TestCase):
    def test_self(self):
        actual = set(ipytest.collect_tests())
        expected = {
            unittest.FunctionTestCase(test_get_assert_function_numpy),
            unittest.FunctionTestCase(test_get_assert_function_pandas_frame),
            unittest.FunctionTestCase(test_get_assert_function_pandas_series),
            unittest.FunctionTestCase(test_get_assert_function_pandas_panel),
            unittest.FunctionTestCase(test_clean),
            TestDiscovery("test_self"),
            TestDiscovery("test_doctest"),
            TestAssertEquals("test_nonequal_fails"),
        }

        assert actual == expected

    def test_doctest(self):
        # NOTE: do not import globally, otherwise it will be collected by pytest
        from ipytest._unittest_support import _DocTestCase

        actual = set(ipytest.collect_tests(doctest=True))
        num_doctests = len({obj for obj in actual if isinstance(obj, _DocTestCase)})

        self.assertEqual(num_doctests, 1)


class TestAssertEquals(unittest.TestCase):
    """Canary test to make sure assert_equals actuals checks for equality.
    """

    def test_nonequal_fails(self):
        with self.assertRaises(AssertionError):
            ipytest.assert_equals(1, 2)


def test_get_assert_function_numpy():
    try:
        import numpy as np

    except ImportError:
        return

    actual = ipytest.get_assert_function(np.array(1), None)
    expected = np.testing.assert_allclose

    assert actual == expected

    actual = ipytest.get_assert_function(None, np.array(1))
    expected = np.testing.assert_allclose

    assert actual == expected

    actual = ipytest.get_assert_function(np.array(1), np.array(2))
    expected = np.testing.assert_allclose

    assert actual == expected


def test_get_assert_function_pandas_frame():
    try:
        import pandas as pd
        import pandas.util.testing as pdt

    except ImportError:
        return

    expected = pdt.assert_frame_equal

    actual = ipytest.get_assert_function(pd.DataFrame(), None)
    ipytest.assert_equals(actual, expected)

    actual = ipytest.get_assert_function(None, pd.DataFrame())
    ipytest.assert_equals(actual, expected)

    actual = ipytest.get_assert_function(pd.DataFrame(), pd.DataFrame())
    ipytest.assert_equals(actual, expected)


def test_get_assert_function_pandas_series():
    try:
        import pandas as pd
        import pandas.util.testing as pdt

    except ImportError:
        return

    expected = pdt.assert_series_equal

    actual = ipytest.get_assert_function(pd.Series(), None)
    ipytest.assert_equals(actual, expected)

    actual = ipytest.get_assert_function(None, pd.Series())
    ipytest.assert_equals(actual, expected)

    actual = ipytest.get_assert_function(pd.Series(), pd.Series())
    ipytest.assert_equals(actual, expected)


def test_get_assert_function_pandas_panel():
    try:
        import pandas as pd
        import pandas.util.testing as pdt

    except ImportError:
        return

    expected = pdt.assert_panelnd_equal

    actual = ipytest.get_assert_function(pd.Panel(), None)
    ipytest.assert_equals(actual, expected)

    actual = ipytest.get_assert_function(None, pd.Panel())
    ipytest.assert_equals(actual, expected)

    actual = ipytest.get_assert_function(pd.Panel(), pd.Panel())
    ipytest.assert_equals(actual, expected)


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


def foo():
    """Example for a doctest.

    >>> foo()
    None
    """
    pass
