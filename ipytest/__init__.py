try:
    import pytest as _pytest  # noqa: F401

except ImportError:
    _has_pytest = False

else:
    from ._pytest_support import run_pytest  # noqa: F401

    _has_pytest = True

from ._unittest_support import (
    run_tests,
    collect_tests,
    assert_equals,
    get_assert_function,
    unittest_assert_equals,
)
from ._util import clean_tests, reload


__all__ = (["run_pytest"] if _has_pytest else []) + [
    "run_tests",
    "clean_tests",
    "collect_tests",
    "assert_equals",
    "get_assert_function",
    "unittest_assert_equals",
    "reload",
]
