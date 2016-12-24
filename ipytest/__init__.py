import fnmatch
import doctest as _doctest
import inspect
import itertools as it
import unittest

try:
    import numpy as _np
    _has_numpy = True

except ImportError:
    _has_numpy = False

try:
    import pandas as _pd
    import pandas.util.testing as _pd_testing
    _has_pandas = True

except ImportError:
    _has_pandas = False


try:
    import pytest as _pytest  # noqa: F401

except ImportError:
    _has_pytest = False

else:
    from ._pytest_support import run_pytest  # noqa: F401
    _has_pytest = True


__all__ = (['run_pytest'] if _has_pytest else []) + [
    "run_tests",
    "clean_tests",
    "collect_tests",
    "assert_equals",
    "get_assert_function",
    "unittest_assert_equals",
]


def run_tests(doctest=False, items=None):
    """Run all tests in the given items dictionary.

    **Arguments:**

    - `doctest`: if True search for doctests.
    - `items`: the globals object containing the tests. If `None` is given, the
        globals object is determined from the call stack.
    """
    if items is None:
        items = _get_globals_of_caller(distance=1)

    suite = unittest.TestSuite(collect_tests(items=items, doctest=doctest))
    unittest.TextTestRunner(verbosity=2).run(suite)


def clean_tests(pattern="test*", items=None):
    """Delete tests with names matching the given pattern.

    In IPython the results of all evaluations are kept in global variables
    unless explicitly deleted. This behavior implies that when tests are renamed
    the previous definitions will still be found if not deleted. This method
    aims to simply this process.

    An effecitve pattern is to start with the cell containing tests with a call
    to `clean_tests`, then defined all test cases, and finally call `run_tests`.
    This way renaming tests works as expected.

    **Arguments:**

    - `pattern`: a glob pattern used to match the tests to delete.
    - `items`: the globals object containing the tests. If `None` is given, the
        globals object is determined from the call stack.
    """
    if items is None:
        items = _get_globals_of_caller(distance=1)

    to_delete = [key for key in items.keys()
                 if fnmatch.fnmatchcase(key, pattern)]

    for key in to_delete:
        del items[key]


def collect_tests(doctest=False, items=None):
    """Collect all test cases and return a `unittest.TestSuite`.

    The arguments are the same as for `ipytest.run_tests`.
    """
    if items is None:
        items = _get_globals_of_caller(distance=1)

    def _impl():
        for (key, value) in sorted(items.items()):
            if _is_test_function(key, value):
                yield unittest.FunctionTestCase(value)

            elif _is_test_class(key, value):
                for func_name in _get_test_functions(value):
                    yield value(func_name)

        for item in _doctests():
            yield item

    def _doctests():
        if not doctest:
            return

        finder = _doctest.DocTestFinder()
        candidates = [
            (key, obj)
            for (key, obj) in items.items()
            if (
                not key.startswith("_") and
                (callable(obj) or inspect.isclass(obj))
            )
        ]

        tests = it.chain.from_iterable(
            finder.find(obj, name=key) for (key, obj) in candidates
        )

        for test in tests:
            if not test.examples:
                continue

            yield _DocTestCase(test)

    return list(_impl())


def assert_equals(a, b, *args, **kwargs):
    """Compare two objects and throw and exception if they are not equal.

    This method uses `ipytest.get_assert_function` to determine the assert
    implementation to use depending on the argument type.

    **Arguments**

    - `a`, `b`: the two objects to compare.
    - `args`, `kwargs`: (keyword) arguments that are passed to the underlying
        test function. This option can, for example, be used to set the
        tolerance when comparing `numpy.array` objects
    """
    test_func = get_assert_function(a, b)
    test_func(a, b, *args, **kwargs)


def get_assert_function(a, b):
    """Determine the assert function to use depending on the arguments.

    If either object is a `numpy .ndarray`, a `pandas.Series`, a
    `pandas.DataFrame`, or `pandas.Panel`, it returns the assert functions
    supplied by `numpy` and `pandas`.
    """
    if _has_pandas:
        if isinstance(a, _pd.Series) or isinstance(b, _pd.Series):
            return _pd_testing.assert_series_equal

        if isinstance(a, _pd.DataFrame) or isinstance(b, _pd.DataFrame):
            return _pd_testing.assert_frame_equal

        if isinstance(a, _pd.Panel) or isinstance(b, _pd.Panel):
            return _pd_testing.assert_panelnd_equal

    if _has_numpy:
        if isinstance(a, _np.ndarray) or isinstance(b, _np.ndarray):
            return _np.testing.assert_allclose

    return unittest_assert_equals


def unittest_assert_equals(a, b):
    """Compare two objects with the `assertEqual` method of `unittest.TestCase`.
    """
    tc = _DummyTestCase()
    tc.assertEqual(a, b)


def _is_test_function(key, value):
    return key.startswith("test") and callable(value)


def _is_test_class(key, value):
    return (
        isinstance(value, type) and
        issubclass(value, unittest.TestCase)
    )


def _get_test_functions(test_class):
    return (
        key
        for key in test_class.__dict__.keys()
        if key.startswith("test")
    )


class _DummyTestCase(unittest.TestCase):
    def runTest(self):
        pass


class _DocTestCase(unittest.TestCase):
    def __init__(self, doctest, **kwargs):
        self.doctest = doctest
        super(_DocTestCase, self).__init__(**kwargs)

    def runTest(self):
        runner = _doctest.DocTestRunner()
        runner.run(self.doctest)


def _get_globals_of_caller(distance=0):
    stack = inspect.stack()
    frame_record = stack[distance + 1]
    return frame_record[0].f_globals
