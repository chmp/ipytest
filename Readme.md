# ipytest - Unit tests in IPython notebooks

[Usage](#usage)
| [Global state](#global-state)
| [Changes](#changes)
| [Related packages](#related-packages)
| [Reference](#reference)
| [Development](#development)
| [License](#license)


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

## Usage

For usage see the [example notebook](./Example.ipynb) or the documentation for
the core API below.

The suggested way to import `ipytest` is:

```python
import ipytest
ipytest.autoconfig()
```

Afterwards test in the current cell can be executed as in:

```python
%%run_pytest[clean] -qq

def test_example():
    assert [1, 2, 3] == [1, 2, 3]
```

This command will first delete any previously defined tests, execute the cell
and then run pytest. See the [reference](#reference) for a detailed list of
available functionality.

## Global state

There are two sources of global state when using pytest inside the notebook:

1. pytest will find any test function ever defined. This behavior can lead to
   unexpected results when test functions are renamed, as their previous
   definition is still available inside the kernel. `ipytest` ships the
   [`clean_test`](#ipytestclean_tests) function to delete such instances.
   Also the [`%%run_pytest[clean]`](#run_pytestclean-) magic clears any
   previously defined tests.
2. Python's module system caches imports and therefore acts as a global state.
   To test the most recent version of any module, the module needs to be
   reloaded. `ipytest` offers the [`reload`](#ipytestreload) function. The
   `autoreload` extension of IPython may also help here. To test local
   packages, it is advisable to install them as development packages, e.g.,
   `pip install -e .`.

## Changes

Note: development is tracked on the `develop` branch.

- `development`:
    - Add `Pytest>=5.0` to the requirements
    - Remove legacy functionality, mostly plain unittest integration
- `0.8.1`: release with sdist for conda-forge
- `0.8.0`:
    - Add the `autoconfig` helper to simplfy setup with reasonable defaults
    - Stop using deprecated pytest API
- `0.7.1`:
    - fix assertion rewriting for `pytest>=5.0.0`
- `0.7.0`:
    - add option to run tests in separate threads. This change allows to test
      async code with the `pytest_asyncio` plugin
    - add a proper signature to `ipytest.config(...)` and show the current
      settings as a repr.
- `0.6.0`: officially remove python 2 support. While `ipytest` was marked to
  work on python 2 and python 3, this statement was not tested and most likely
  not true. This change only documents the current state.
- `0.5.0`:
    - Fix assertion rewriting via magics in `ipython>=7`
    - Add support to raise a `RuntimeError` on test errors (set
      `ipytest.config.raise_on_error = True`)
    - Add support to set base arguments (set `ipytest.config.addopts = []`)
    - Add config setting to enable magics (set `ipytest.config.magics = True`).
    - Add config setting to create a temporary file to work without the
      notebook filename (set `ipytest.config.tempfile_fallback = True`).
    - Allow to set multiple config values at the same time by calling the
      config object (`ipytest.config(...)`).
    - Add `ipytest.running_as_test()` to detect whether a notebook is executed
      as a test.
- `0.4.0`: add support for automatic AST transforms, deprecate non pytest API.
- `0.3.0`: change default pattern for `clean_tests` to match pytest discovery
- `0.2.2`: add support for assert rewriting with current pytest versions
- `0.2.1`: add ipython magics to simplify test execution
- `0.2.0`: support for using pytest inside notebooks
- `0.1.0`: support for running `unittest.FunctionTestCase`,
  `unittest.TestCases`, and `doctests`.

## Related packages

`ipytest` is designed to enable running tests within an interactive notebook
session. There are also other packages that aim to use notebooks as tests
themselves, for example by comparing the output of running all cells to the
output of previous runs. These packages include:

- [nbval](https://github.com/computationalmodelling/nbval) is actively
  maintained. It is also used in the integration tests of `ipytest`.
- [pytest-ipynb](https://github.com/zonca/pytest-ipynb) seems to be no longer
  maintained as the latest commit was on March 2016. .
- ...

Please create an issue, if I missed a packaged or mischaracterized any package.

## Reference

### `ipytest.autoconfig`
`ipytest.autoconfig(rewrite_asserts=<default>, magics=<default>, tempfile_fallback=<default>, clean=<default>, addopts=<default>, raise_on_error=<default>, run_in_thread=<default>)`

Configure `ipytest` with reasonable defaults.

Specifically, it sets:

- `rewrite_asserts`: `True`
- `magics`: `True`
- `tempfile_fallback`: `True`
- `clean`: `'[Tt]est*'`
- `addopts`: `('-q',)`
- `raise_on_error`: `False`
- `run_in_thread`: `False`

See [ipytest.config](#ipytestconfig) for details.



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

### `ipytest.config`

Configure `ipytest`. The following settings are suported:

- `ipytest.config.rewrite_asserts` (default: `False`): enable ipython AST
  transforms globally to rewrite asserts.
- `ipytest.config.magics` (default: `False`): if set to `True` register the
  ipytest magics.
- `ipytest.config.clean` (default: `[Tt]est*`): the pattern used to clean
  variables.
- `ipytest.config.addopts` (default: `()`): pytest command line arguments to
  prepend to every pytest invocation. For example setting
  `ipytest.config.addopts= ['-qq']` will execute pytest with the least
  verbosity.
- `ipytest.config.raise_on_error` (default: `False`): if `True`, unsuccessful
  invocations will raise a `RuntimeError`.
- `ipytest.config.tempfile_fallback` (default: `False`): if `True`, a temporary
  file is created as a fallback when no valid filename can be determined.
- `ipytest.config.run_in_thread` (default: `False`): if `True`, pytest will be
  run a separate thread. This way of running is required when testing async
  code with `pytest_asyncio` since it starts a separate event loop.

To set multiple arguments at once, the config object can also be called, as in:

```python

ipytest.config(rewrite_asserts=True, raise_on_error=True)
```

### `ipytest.exit_code`

The return code of the last pytest invocation.

### `ipytest.run`
`ipytest.run(*args, module=None, filename=None, plugins=(), return_exit_code=False)`

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



### `ipytest.running_as_test`
`ipytest.running_as_test()`

Check whether the notebook is executed as a test.

This function may be useful, when running notebooks as integration tests to
ensure the runtime is not exceedingly long.

Usage:

```
model.fit(x, y, epochs=500 if not ipytest.running_as_test() else 1)
```



### `%%rewrite_asserts`

Rewrite any asserts in the current cell using pytest without running the tests.
To get best results run the tests with `run`.
To register the magics, run `ipytest.config.magics = True` first.

For example::

```python
%%rewrite_asserts

def test_example():
    ...
```

## Development

To execute the unit tests of `ipytest` run

    pipenv sync --dev
    pipenv run test

Before commit execute `pipenv run precommit` to update the documentation,
format the code, and run tests.

To create a new release execute:

```bash
pipenv run release
```

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