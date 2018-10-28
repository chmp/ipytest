# ipytest - unit tests in IPython notbeooks

Sometimes quick experiments in IPython grow large and you find yourself wanting
unit tests. This module aims to make testing code in IPython notebooks easy. At
its core, it offers a way to run [`pytest`](https://pytest.org) tests inside the
notebook environment. It is also designed to make the transfer of the tests into
proper python modules easy.

Installation: `pip install ipytest`

Features:

- support for [pytest](pytest.org) inside notebooks (with all bells and
  whistles)
- tight integration with IPython via magics and automatic code transforms

## Changes

Note: development is tracked on the `develop` branch.

- `dev`: fix assertion rewriting via magics in `ipython>=7`. Add support to
  raise a `RuntimeError` on test errors. Add support to set base arguments.
  Allow to set multiple config values at the same time. Use config to control
  magics.
- `0.4.0`: add support for automatic AST transforms, deprecate non pytest API.
- `0.3.0`: change default pattern for `clean_tests` to match pytest discovery
- `0.2.2`: add support for assert rewriting with current pytest versions
- `0.2.1`: add ipython magics to simplify test execution
- `0.2.0`: support for using pytest inside notebooks
- `0.1.0`: support for running `unittest.FunctionTestCase`,
  `unittest.TestCases`, and `doctests`.

## Usage

For usage see the [example notebook](./Example.ipynb) or the documentation for
the core API below.

The suggested way to import `ipytest` is:

```python
import ipytest
ipytest.config(rewrite_asserts=True, magics=True)

__file__ = "INSERT YOUR NOTEBOOK FILENAME HERE"
```

## Reference

### `ipytest.run`
`ipytest.run(*args)`

Execute all tests in the passed module (defaults to __main__) with pytest.

#### Parameters

* **args** (*any*):
  additional commandline options passed to pytest
* **module** (*any*):
  the module containing the tests. If not given, __main__ will be used.
* **filename** (*any*):
  the filename of the file containing the tests. It has to be a real
  file, e.g., a notebook name, since itts existence will be checked by
  pytest. If not given, the __file__ attribute of the passed module
  will be used.
* **plugins** (*any*):
  additional plugins passed to pytest.



### `%%run_pytest ...`

IPython magic that first executes the cell, then executes `ipytest.run()`.
Any arguments passed on the magic line be passed on to pytest.
To register the magics, run `ipytest.config.magics = True` first.

For example:

```python
%%run_pytest -qq


def test_example():
    ...

```

### `%%run_pytest[clean] ...`

Same as the `%%run_pytest`, but cleans any previously found tests, i.e., only
tests defined in the current cell are executed.
To register the magics, run `ipytest.config.magics = True` first.

### `%%rewrite_asserts`

Rewrite any asserts in the current cell using pytest without running the tests.
To get best results run the tests with `run_pytest`.
To register the magics, run `ipytest.config.magics = True` first.

For example::

```python
%%rewrite_asserts

def test_example():
    ...
```

### `ipytest.config`

Configure `ipytest`. The following settings are suported:

- `ipytest.config.rewrite_asserts` (default: `False`): enable ipython AST
  transforms globally to rewrite asserts.
- `ipytest.config.magics` (default: `False`): if set to `True` register the
  ipytest magics.
- `ipytest.config.clean` (default: `[Tt]est*`): the pattern used to clean
  variables.
- `ipytest.config.base_args` (default: `()`): pytest command line arguments to
  prepend to every pytest invocation. For example setting
  `ipytest.config.base_args = ['-qq']` will execute pytest with the least
  verbosity.
- `ipytest.config.raise_on_error` (default: `False`): if `True`, unsuccessful
  invocations will raise a `RuntimeError`.

To set multiple arguments at once, the config object can also be called, as in:

```python

ipytest.config(rewrite_asserts=True, raise_on_error=True)
```

### `ipytest.exit_code`

The return code of the last pytest invocation.

## Development

To execute the unit tests of `ipytest` run

    pipenv sync --dev
    pipenv run test

Before commit execute `pipenv run precommit` to update the documentation,
format the code, and run tests.

### `ipytest.clean_tests`
`ipytest.clean_tests(pattern=None, items=None)`

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



## Legacy functionality

### `ipytest.run_pytest`
`ipytest.run_pytest(*args, **kwargs)`

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



### `ipytest.run_tests`
`ipytest.run_tests(*args, **kwargs)`

Run all tests in the given items dictionary.

**Arguments:**

- doctest: if True search for doctests.
- * **items: the globals object containing the tests. If None is given, the**:
  globals object is determined from the call stack.



### `ipytest.collect_tests`
`ipytest.collect_tests(*args, **kwargs)`

Collect all test cases and return a unittest.TestSuite.

The arguments are the same as for ipytest.run_tests.



### `ipytest.assert_equals`
`ipytest.assert_equals(*args, **kwargs)`

Compare two objects and throw and exception if they are not equal.

This method uses ipytest.get_assert_function to determine the assert
implementation to use depending on the argument type.

**Arguments**

- a, b: the two objects to compare.
- * **args, kwargs: (keyword) arguments that are passed to the underlying**:
  test function. This option can, for example, be used to set the
  tolerance when comparing numpy.array objects



### `ipytest.get_assert_function`
`ipytest.get_assert_function(*args, **kwargs)`

Determine the assert function to use depending on the arguments.

If either object is a numpy .ndarray, a pandas.Series, a
pandas.DataFrame, or pandas.Panel, it returns the assert functions
supplied by numpy and pandas.



### `ipytest.unittest_assert_equals`
`ipytest.unittest_assert_equals(*args, **kwargs)`

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
