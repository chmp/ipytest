# ipytest - Unit tests in IPython notebooks

[Usage](#usage)
| [Global state](#global-state)
| [How does it work?](#how-does-it-work)
| [Changes](#changes)
| [Reference](#reference)
| [Development](#development)
| [Related packages](#related-packages)
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
the core API below. The suggested way to import `ipytest` is:

```python
import ipytest
ipytest.autoconfig()
```

Afterwards in a *new* cell, tests can be executed as in:

```python
%%ipytest -qq

def test_example():
    assert [1, 2, 3] == [1, 2, 3]
```

This command will first delete any previously defined tests, execute the cell
and then run pytest. It is also possible to use `ipytest` without magics by
calling the `run` function as in:

```python
ipytest.run()
```

This function is a thin wrapper around `pytest.main` and will execute any tests
defined in the current notebook session.  See the [reference](#reference) for a
detailed list of available functionality.

**NOTE:** Some notebook implementations modify the core IPython package and
magics may not work correctly (see [here][issue-47] or [here][issue-50]). In
this case, using `ipytest.run` and `ipytest.clean_tests` directly should still
work as expected.

[issue-47]: https://github.com/chmp/ipytest/issues/47
[issue-50]: https://github.com/chmp/ipytest/issues/50

## Global state

There are multiple sources of global state when using pytest inside the notebook:

1. pytest will find any test function ever defined. This behavior can lead to
   unexpected results when test functions are renamed, as their previous
   definition is still available inside the kernel. `ipytest` ships the
   [`clean_test`](#ipytestclean_tests) function to delete such instances.
   Also the [`%%ipytest`](#ipyest) magic clears any
   previously defined tests.
2. Python's module system caches imports and therefore acts as a global state.
   To test the most recent version of any module, the module needs to be
   reloaded. `ipytest` offers the [`reload`](#ipytestreload) function. The
   `autoreload` extension of IPython may also help here. To test local
   packages, it is advisable to install them as development packages, e.g.,
   `pip install -e .`.
3. For async code, IPython will create an event loop in the current thread.
   This setup may interfere with async tests. To support these use cases,
   ipytest supports running tests in a separate thread. Simply setup ipytest
   via `ipytest.autoconfig(run_in_thread=True)`.

## How does it work?

In its default configuration (via `autoconfig()`), `ipytest` performs the
following steps:

1. Register pytest's assertion rewriter with the IPython kernel. The rewriter
   will rewrite any assert statements entered into the notebook to give better
   error messages. This change will affect also non test based code, but should
   generally improve the development experience.
2. Ensure the notebook can be mapped to a file. `ipytest` will create a
   temporary file in the current directory and remove if afterwards.
3. Register the notebook scope temporarily as a module. This step is necessary
   to allow pytest's doctest plugin to import the notebook.
4. Call pytest with the name of the temporary module

`ipytest` can pass additional arguments to pytest. Per default, only the
filename that is associated with the notebook is passed. There are a number of
ways to configure this behavior:

- `ipytest.config(addopts=...)` or `ipytest.autconfig(addopts=...)` allow to
  specify a list of strings that are added to the command line. For example,
  `ipytest.autoconfig(addopts=["-x", "--pdb"])` will attach the debugger on the
  first test failure and not run further tests.
- `ipytest.run(...)`: allows to specify additional arguments as strings
- `%%ipytest` allows to specify additional arguments in the same line
- `ipytest.config(defopts=False)` or `ipytest.autoconfig(defopts=False)` will
  instruct `ipytest` to not pass the current module filename. It can still be
  passed manually by adding `{MODULE}` to the command line.

The arguments are formatted using Python's standard string formatting.
Currently, only the `{MODULE}` variable is understood. It is replaced with the
filename associated with the notebook.

## Changes

Note: development is tracked on the `develop` branch.

- `0.11.0`:
    - Overwrite the program name in pytest error messages for incorrect arguments
    - Deprecate `%%run_pytest` and `%%run_pytest[clean]` in favor of `%%ipytest`
    - Force color pytest output by default by adding `--color=yes` to the
      default `addopts` value
    - Configure the number of columns available to pytest
    - Add warning and workaround for non-standard IPython implementations
- `0.10.0`:
    - Remove the `ModuleCollectorPlugin` in favor of relying on pytest's builtin
      collection mechanism
    - Allow to fully customize the command line and to skip passing the
      current module as an argument
    - Simplify config implementation: restrict config changes to function calls
    - Allow to use the generated module name in the arguments passed to pytest
      by using `{MODULE}`
    - Require `python>=3.6`
    - Remove `%%rewrite_asserts` magic
    - Remove `tempfile_fallback` config option
    - Remove `register_module` config option
    - Remove `raise_on_error` config option
    - Remove `filename` argument for `ipytest.run`
    - Remove `return_exit_code` argument from `ipytest.run`
    - Remove `running_as_test` function
- `0.9.1`:
    - Add `ipython` as an explicit dependency
- `0.9.0`:
    - Add `Pytest>=5.4` to the requirements
    - Remove legacy functionality, mostly plain unittest integration
    - The `tempfile_fallback` also kicks in, if a filename was configured, but
      the file does not exist
    - Add `register_module` option to register the notebook with the module
      system of Python. This way `--doctest-modules` works as expected
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

## Reference

### `ipytest.autoconfig`
`ipytest.autoconfig(rewrite_asserts=<default>, magics=<default>, clean=<default>, addopts=<default>, run_in_thread=<default>, defopts=<default>, display_columns=<default>)`

Configure `ipytest` with reasonable defaults.

Specifically, it sets:

- `rewrite_asserts`: `True`
- `magics`: `True`
- `clean`: `'[Tt]est*'`
- `addopts`: `('-q', '--color=yes')`
- `run_in_thread`: `False`
- `defopts`: `True`
- `display_columns`: `100`

See [ipytest.config](#ipytestconfig) for details.



### `%%ipytest ...`

IPython magic that first executes the cell, then executes `ipytest.run()`. Any
arguments passed on the magic line be passed on to pytest. It cleans any
previously found tests, i.e., only tests defined in the current cell are
executed. To disable this behavior, use `ipytest.config(clean=False)`. To
register the magics, run `ipytest.autoconfig()` or `ipytest.config(magics=True)`
first.

Additional arguments can be passed to pytest. See the section "How does it work"
for specifics.

For example:

```python
%%ipytest -qq


def test_example():
    ...

```

### `ipytest.config`
`ipytest.config(rewrite_asserts=<keep>, magics=<keep>, clean=<keep>, addopts=<keep>, run_in_thread=<keep>, defopts=<keep>, display_columns=<keep>)`

Configure ipytest

To update the configuration, call this function as in:

```python
ipytest.config(rewrite_asserts=True)
```

The following settings are supported:

- `rewrite_asserts` (default: `False`): enable ipython AST transforms
  globally to rewrite asserts
- `magics` (default: `False`): if set to `True` register the ipytest
  magics
- `clean` (default: `[Tt]est*`): the pattern used to clean variables
- `addopts` (default: `()`): pytest command line arguments to prepend
  to every pytest invocation. For example setting
  `ipytest.config(addopts=['-qq'])` will execute pytest with the least
  verbosity. Consider adding `--color=yes` to force color output
- `run_in_thread` (default: `False`): if `True`, pytest will be run a
  separate thread. This way of running is required when testing async
  code with `pytest_asyncio` since it starts a separate event loop
- `defopts` (default: `True`): if `True`, ipytest will add the
  current module to the arguments passed to pytest. If `False` only the
  arguments given and `adopts` are passed. Such a setup may be helpful
  to customize the test selection
- `display_columns` (default: `100`) if not False, configure Pytest
  to use the given number of columns for its output. This option will
  temporarily override the `COLUMNS` environment variable.



### `ipytest.exit_code`

The return code of the last pytest invocation.

### `ipytest.run`
`ipytest.run(*args, module=None, plugins=())`

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

```python
reload("ipytest._util", "ipytest")
```



## Development

Setup the virtual environment via:

```bash
pip install -r requirements-dev.txt
```

To execute the unit tests of `ipytest` run

```bash
python make.py test
python make.py integration
```

Before commit execute `python make.py precommit` to update the documentation,
format the code, and run tests.

To create a new release execute:

```bash
python make.py release
```


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


## License

```
The MIT License (MIT)
Copyright (c) 2015 - 2021 Christopher Prohm

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