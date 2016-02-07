from __future__ import print_function, absolute_import, division

import unittest
import ipytest


class TestDiscovery(unittest.TestCase):
    def test_self(self):
        actual = set(ipytest.collect_tests()) 
        expected = {
            unittest.FunctionTestCase(test_get_assert_function_numpy),
            unittest.FunctionTestCase(test_get_assert_function_pandas_frame),
            unittest.FunctionTestCase(test_get_assert_function_pandas_series),
            unittest.FunctionTestCase(test_get_assert_function_pandas_panel),
            TestDiscovery("test_self"),
            TestDiscovery("test_doctest"),
            TestAssertEquals('test_nonequal_fails'),
        }

        assert actual == expected

    def test_doctest(self):
        actual = set(ipytest.collect_tests(doctest=True)) 
        num_doctests = len({
            obj for obj in actual 
            if isinstance(obj, ipytest._DocTestCase)
        })

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
        import pandas.util.testing
    
    except ImportError:
        return
    
    expected = pd.util.testing.assert_frame_equal
    
    actual = ipytest.get_assert_function(pd.DataFrame(), None) 
    ipytest.assert_equals(actual, expected)
    
    actual = ipytest.get_assert_function(None, pd.DataFrame()) 
    ipytest.assert_equals(actual, expected)
    
    actual = ipytest.get_assert_function(pd.DataFrame(), pd.DataFrame()) 
    ipytest.assert_equals(actual, expected)


def test_get_assert_function_pandas_series():
    try:
        import pandas as pd
        import pandas.util.testing
    
    except ImportError:
        return
    
    expected = pd.util.testing.assert_series_equal
    
    actual = ipytest.get_assert_function(pd.Series(), None)
    ipytest.assert_equals(actual, expected)
    
    actual = ipytest.get_assert_function(None, pd.Series())
    ipytest.assert_equals(actual, expected)
    
    actual = ipytest.get_assert_function(pd.Series(), pd.Series())
    ipytest.assert_equals(actual, expected)


def test_get_assert_function_pandas_panel():
    try:
        import pandas as pd
        import pandas.util.testing
    
    except ImportError:
        return
    
    expected = pd.util.testing.assert_panelnd_equal
    
    actual = ipytest.get_assert_function(pd.Panel(), None)
    ipytest.assert_equals(actual, expected)
    
    actual = ipytest.get_assert_function(None, pd.Panel())
    ipytest.assert_equals(actual, expected)
    
    actual = ipytest.get_assert_function(pd.Panel(), pd.Panel())
    ipytest.assert_equals(actual, expected)
    

def foo():
    """Example for a doctest.

    >>> foo()
    None
    """
    pass

