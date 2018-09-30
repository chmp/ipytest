# ipytest - unit tests in IPython notbeooks

Sometimes quick experiments in IPython grow large and you find yourself wanting
unit tests. This module aims to make testing code in IPython notebooks easy. At
its core, it offers a way to run [`pytest`](https://pytest.org) tests inside the
notebook environment. It is also designed to make the transfer of the tests into
proper python modules easy.

Installation: `pip install ipytest`

## Changes

- `0.3.0`: change default pattern for `clean_tests` to match pytest discovery
- `0.2.2`: add support for assert rewriting with current pytest versions
- `0.2.1`: add ipython magics to simplify test execution
- `0.2.0`: support for using pytest inside notebooks
- `0.1.0`: support for running `unittest.FunctionTestCase`,
  `unittest.TestCases`, and `doctests`.

## Features

- support for [pytest](pytest.org) (with all bells and whistles)
- magics for easy execution
- support for standard unittest and doctests

## Examples

- [pytest runner ](./example/Magics.ipynb)
- [pytest runner (no magics)](./example/PyTest.ipynb)
- [unittest runner](./example/Example.ipynb)

## Development

To execute the unit tests of `ipytest` run

    pipenv sync --dev
    pipenv run test

## Reference

### `%%run_pytest ...`

IPython magic that first executes the cell, then executes `run_pytest`.
Any arguments passed on the magic line be passed on to pytest.
To register the magics, run `import ipytest.magics` first.

For example:

```python
%%run_pytest -vvv


def test_example():
    ...

```

### `%%run_pytest[clean] ...`

Same as the `%%run_pytest`, but cleans any previously found tests, i.e., only
tests defined in the current cell are executed.

### `%%rewrite_asserts`

Rewrite any asserts in the current cell using pytest without running the tests.
To get best results run the tests with `run_pytest`.

For example::

```python
%%rewrite_asserts

def test_example():
    ...
```

### `ipytest.run_pytest`
`ipytest.run_pytest(module=None, filename=None, pytest_options=(), pytest_plugins=())`

Execute tests in the passed module (defaults to __main__) with pytest.

**Arguments:**

- module: the module containing the tests.
  If not given, __main__ will be used.
- filename: the filename of the file containing the tests.
  It has to be a real file, e.g., a notebook name, since itts existence will
  be checked by pytest.
  If not given, the __file__ attribute of the passed module will be used.
- pytest_options: additional options passed to pytest
- pytest_plugins: additional plugins passed to pytest.



### `ipytest.clean_tests`
`ipytest.clean_tests(pattern='[Tt]est*', items=None)`

Delete tests with names matching the given pattern.

In IPython the results of all evaluations are kept in global variables
unless explicitly deleted. This behavior implies that when tests are renamed
the previous definitions will still be found if not deleted. This method
aims to simply this process.

An effecitve pattern is to start with the cell containing tests with a call
to clean_tests, then defined all test cases, and finally call run_tests.
This way renaming tests works as expected.

**Arguments:**

- pattern: a glob pattern used to match the tests to delete.
- * **items: the globals object containing the tests. If None is given, the**:
  globals object is determined from the call stack.



### `ipytest.reload`
`ipytest.reload(*mods)`

Reload all modules passed as strings.

This function may be useful, when mixing code in external modules and
notebooks.

Usage:

```
reload("ipytest._util", "ipytest")
```



### `ipytest.run_tests`
`ipytest.run_tests(doctest=False, items=None)`

Run all tests in the given items dictionary.

**Arguments:**

- doctest: if True search for doctests.
- * **items: the globals object containing the tests. If None is given, the**:
  globals object is determined from the call stack.



### `ipytest.collect_tests`
`ipytest.collect_tests(doctest=False, items=None)`

Collect all test cases and return a unittest.TestSuite.

The arguments are the same as for ipytest.run_tests.



### `ipytest.assert_equals`
`ipytest.assert_equals(a, b, *args, **kwargs)`

Compare two objects and throw and exception if they are not equal.

This method uses ipytest.get_assert_function to determine the assert
implementation to use depending on the argument type.

**Arguments**

- a, b: the two objects to compare.
- * **args, kwargs: (keyword) arguments that are passed to the underlying**:
  test function. This option can, for example, be used to set the
  tolerance when comparing numpy.array objects



### `ipytest.get_assert_function`
`ipytest.get_assert_function(a, b)`

Determine the assert function to use depending on the arguments.

If either object is a numpy .ndarray, a pandas.Series, a
pandas.DataFrame, or pandas.Panel, it returns the assert functions
supplied by numpy and pandas.



### `ipytest.unittest_assert_equals`
`ipytest.unittest_assert_equals(a, b)`

Compare two objects with the assertEqual method of unittest.TestCase.




## License

```
The MIT License (MIT)
Copyright (c) 2015 - 2018 Christopher Prohm

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

```