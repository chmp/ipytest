# ipytest - unit tests in IPython notbeooks

Sometimes quick experiments in IPython grow large and you find yourself wanting
unit tests. This module aims to make testing code in IPython notebooks easy. At
its core, it offers a test runner that execute all tests defined inside the
notebook environment. It is also designed to make the transfer of the tests into
proper python modules easy.

## Example

```python
# In[1]:
def fibonacci(i):
    """Compute the fibonacci sequence.

    >>> [fibonacci(n) for n in range(7)]
    [1, 1, 2, 3, 5, 8, 13]

    """
    if i == 0 or i == 1:
        return 1
    return fibonacci(i - 1) + fibonacci(i - 2)

# In[2]:
import ipytest
ipytest.clean_tests("test_fibonacci*")

def test_fibonacci_0():
    assert fibonacci(0) == 1

def test_fibonacci_1():
    assert fibonacci(1) == 1

def test_fibonacci_2():
    assert fibonacci(2) == 2

def test_fibonacci_3():
    assert fibonacci(3) == 3

def test_fibonacci_4():
    assert fibonacci(4) == 5

def test_fibonacci_5():
    assert fibonacci(5) == 8

def test_fibonacci_6():
    assert fibonacci(6) == 13

ipytest.run_tests(doctest=True)     
```

## Installation

```bash
pip install ipytest
```

## Features

- simple interface
- builds on standard unittest
- support for doctests
- support for pandas and numpy.

## Reference

### ipytest.run_pytest(module=None, filename=None, pytest_options=(), pytest_plugins=())

Execute tests in the passed module (defaults to __main__) with pytest.

**Arguments:**

- `module`: the module containing the tests.
  If not given, `__main__` will be used.
- `filename`: the filename of the file containing the tests.
  It has to be a real file, e.g., a notebook name, since itts existence will
  be checked by pytest.
  If not given, the `__file__` attribute of the passed module will be used.
- `pytest_options`: additional options passed to pytest
- `pytest_plugins`: additional plugins passed to pytest.

### ipytest.run_tests(doctest=False, items=None)

Run all tests in the given items dictionary.

**Arguments:**

- `doctest`: if True search for doctests.
- `items`: the globals object containing the tests. If `None` is given, the
    globals object is determined from the call stack.

### ipytest.clean_tests(pattern="test*", items=None)

Delete tests with names matching the given pattern.

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

### ipytest.collect_tests(doctest=False, items=None)

Collect all test cases and return a `unittest.TestSuite`.

The arguments are the same as for `ipytest.run_tests`.

### ipytest.assert_equals(a, b, *args, **kwargs)

Compare two objects and throw and exception if they are not equal.

This method uses `ipytest.get_assert_function` to determine the assert
implementation to use depending on the argument type.

**Arguments**

- `a`, `b`: the two objects to compare.
- `args`, `kwargs`: (keyword) arguments that are passed to the underlying
    test function. This option can, for example, be used to set the
    tolerance when comparing `numpy.array` objects

### ipytest.get_assert_function(a, b)

Determine the assert function to use depending on the arguments.

If either object is a `numpy .ndarray`, a `pandas.Series`, a
`pandas.DataFrame`, or `pandas.Panel`, it returns the assert functions
supplied by `numpy` and `pandas`.

### ipytest.unittest_assert_equals(a, b)

Compare two objects with the `assertEqual` method of `unittest.TestCase`.


## License

    The MIT License (MIT)
    Copyright (c) 2015 - 2016 Christopher Prohm

    Permission is hereby granted, free of charge, to any person obtaining a
    copy of this software and associated documentation files (the "Software"),
    to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense,
    and/or sell copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
    DEALINGS IN THE SOFTWARE.
