source = '''
def is_even(n):
    """Check if a number is even

    >>> is_even(2)
    True
    >>> is_even(3)
    False
    """
    return n % 2 == 0
'''


def test_example(ipytest_entry_point):
    exit_code = ipytest_entry_point("--doctest-modules", "", source)
    assert exit_code == 0
