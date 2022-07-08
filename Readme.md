# ipytest - Pytest in Jupyter notebooks

[PyPI](https://pypi.org/project/ipytest)
| [Usage](#usage)
| [Global state](#global-state)
| [Extended Usage](#extended-usage)
| [How does it work?](#how-does-it-work)
| [Changes](Changes.md)
| [Reference](#reference)
| [Development](#development)
| [Related packages](#related-packages)
| [License](#license)

`ipytest` allows you to run [Pytest](https://pytest.org) in Jupyter notebooks.
`ipytest` aims to give access to the full `pytest` experience to make it easy to
transfer tests out of notebooks into separate test files.

Installation:

```bash
pip install ipytest
```

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
and then run pytest. For further details on how to use `ipytest` see [Extended
usage](#extended-usage).

**NOTE:** Some notebook implementations modify the core IPython package and
magics may not work correctly (see [here][issue-47] or [here][issue-50]). In
this case, using [`ipytest.run()`][ipytest.run] and
[`ipytest.clean_tests()`][ipytest.clean_tests] directly should still work as
expected.

[issue-47]: https://github.com/chmp/ipytest/issues/47
[issue-50]: https://github.com/chmp/ipytest/issues/50

## Global state

There are multiple sources of global state when using pytest inside the notebook:

1. pytest will find any test function ever defined. This behavior can lead to
   unexpected results when test functions are renamed, as their previous
   definition is still available inside the kernel. Running
   [`%%ipytest`][ipytest.ipytest] per default deletes any previously defined
   tests. As an alternative the [`ipytest.clean_tests()`][ipytest.clean_tests]
   function allows to delete previously defined tests.
2. Python's module system caches imports and therefore acts as a global state.
   To test the most recent version of any module, the module needs to be
   reloaded. `ipytest` offers the [`ipytest.reload()`][ipytest.reload] function.
   The `autoreload` extension of IPython may also help here. To test local
   packages, it is advisable to install them as development packages, e.g., `pip
   install -e .`.
3. For async code, IPython will create an event loop in the current thread. This
   setup may interfere with async tests. To support these use cases, ipytest
   supports running tests in a separate thread. Simply setup ipytest via
   `ipytest.autoconfig(run_in_thread=True)`.

## Extended usage

It is also possible to use `ipytest` without magics by calling the
[`run`][ipytest.run] function as in:

```python
ipytest.run()
```

This function is a thin wrapper around `pytest.main` and will execute any tests
defined in the current notebook session.  See the [reference](#reference) for a
detailed list of available functionality.

**NOTE:** In its default configuration [`%%ipytest`][ipytest.ipytest] and
[`ipytest.run()`][ipytest.run] will not raise an error, when tests fail. The
reason is that having multiple tracebacks (the one from pytest and ipytest) may
be confusing. To raise exceptions on test errors, e.g., to use ipytest inside a
CI/CD context, use:

```python
ipytest.autoconfig(raise_on_error=True)
```

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

## Reference

[`autoconfig`][ipytest.autoconfig]
| [`%%ipytest`][ipytest.ipytest]
| [`config`][ipytest.config]
| [`exit_code`][ipytest.exit_code]
| [`run`][ipytest.run]
| [`clean_tests`][ipytest.clean_tests]
| [`reload`][ipytest.reload]
| [`Error`][ipytest.Error]

<!-- minidoc "function": "ipytest.autoconfig", "header_depth": 3 -->
### `ipytest.autoconfig(rewrite_asserts=<default>, magics=<default>, clean=<default>, addopts=<default>, run_in_thread=<default>, defopts=<default>, display_columns=<default>, raise_on_error=<default>)`

[ipytest.autoconfig]: #ipytestautoconfigrewrite_assertsdefault-magicsdefault-cleandefault-addoptsdefault-run_in_threaddefault-defoptsdefault-display_columnsdefault-raise_on_errordefault

Configure `ipytest` with reasonable defaults.

Specifically, it sets:

* `rewrite_asserts`: `True`
* `magics`: `True`
* `clean`: `'[Tt]est*'`
* `addopts`: `('-q', '--color=yes')`
* `run_in_thread`: `False`
* `defopts`: `True`
* `display_columns`: `100`
* `raise_on_error`: `False`

See [`ipytest.config`][ipytest.config] for details.

<!-- minidoc -->

### `%%ipytest ...`

[ipytest.ipytest]: #ipytest-

<!-- minidoc "function": "ipytest._impl.pytest_magic", "header": false, "header_depth": 3 -->
IPython magic to first execute the cell, then execute [`ipytest.run()`][ipytest.run].

**Note:** the magics are only available after running
[`ipytest.autoconfig()`][ipytest.autoconfig] or
[`ipytest.config(magics=True)`][ipytest.config].

It cleans any previously found tests, i.e., only tests defined in the
current cell are executed. To disable this behavior, use
[`ipytest.config(clean=False)`][ipytest.config].

Any arguments passed on the magic line are interpreted as command line
arguments to to pytest. For example calling the magic as

```python
%%ipytest -qq
```

is equivalent to passing `-qq` to pytest. See also the section ["How does it
work"](#how-does-it-work) for further details.

The keyword arguments passed to [`ipytest.run()`][ipytest.run] can be
customized by including a comment of the form `# ipytest: arg1=value1,
arg=value2` in the cell source. For example:

```python
%%ipytest {MODULE}::test1
# ipytest: defopts=False
```

is equivalent to `ipytest.run("{MODULE}::test1", defopts=False)`. In this
case, it deactivates default arguments and then instructs pytest to only
execute `test1`.

<!-- minidoc -->

<!-- minidoc "function": "ipytest.config", "header_depth": 3 -->
### `ipytest.config(rewrite_asserts=<keep>, magics=<keep>, clean=<keep>, addopts=<keep>, run_in_thread=<keep>, defopts=<keep>, display_columns=<keep>, raise_on_error=<keep>)`

[ipytest.config]: #ipytestconfigrewrite_assertskeep-magicskeep-cleankeep-addoptskeep-run_in_threadkeep-defoptskeep-display_columnskeep-raise_on_errorkeep

Configure `ipytest`

To update the configuration, call this function as in:

```python
ipytest.config(rewrite_asserts=True)
```

The following settings are supported:

* `rewrite_asserts` (default: `False`): enable ipython AST transforms
  globally to rewrite asserts
* `magics` (default: `False`): if set to `True` register the ipytest magics
* `clean` (default: `[Tt]est*`): the pattern used to clean variables
* `addopts` (default: `()`): pytest command line arguments to prepend to
  every pytest invocation. For example setting
  `ipytest.config(addopts=['-qq'])` will execute pytest with the least
  verbosity. Consider adding `--color=yes` to force color output
* `run_in_thread` (default: `False`): if `True`, pytest will be run a
  separate thread. This way of running is required when testing async code
  with `pytest_asyncio` since it starts a separate event loop
* `defopts` (default: `True`): if `True`, ipytest will add the current
  module to the arguments passed to pytest. If `False` only the arguments
  given and `adopts` are passed. Such a setup may be helpful to customize
  the test selection
* `display_columns` (default: `100`): if not `False`, configure Pytest to
  use the given number of columns for its output. This option will
  temporarily override the `COLUMNS` environment variable.
* `raise_on_error` (default `False` ): if `True`, `ipytest.run` and
  `%%ipytest` will raise an `ipytest.Error` if pytest fails.

<!-- minidoc -->

### `ipytest.exit_code`

[ipytest.exit_code]: #ipytestexit_code

The return code of the last pytest invocation.

<!-- minidoc "function": "ipytest.run", "header_depth": 3 -->
### `ipytest.run(*args, module=None, plugins=(), run_in_thread=<default>, raise_on_error=<default>, addopts=<default>, defopts=<default>, display_columns=<default>)`

[ipytest.run]: #ipytestrunargs-modulenone-plugins-run_in_threaddefault-raise_on_errordefault-addoptsdefault-defoptsdefault-display_columnsdefault

Execute all tests in the passed module (defaults to `__main__`) with pytest.

**Parameters:**

- `args`: additional commandline options passed to pytest
- `module`: the module containing the tests. If not given, `__main__` will
  be used.
- `plugins`: additional plugins passed to pytest.

The following parameters override the config options set with
[`ipytest.config()`][ipytest.config] or
[`ipytest.autoconfig()`][ipytest.autoconfig].

- `run_in_thread`: if given, override the config option "run_in_thread".
- `raise_on_error`: if given, override the config option "raise_on_error".
- `addopts`: if given, override the config option "addopts".
- `defopts`: if given, override the config option "defopts".
- `display_columns`: if given, override the config option "display_columns".

**Returns**: the exit code of `pytest.main`.

<!-- minidoc -->
<!-- minidoc "function": "ipytest.clean_tests", "header_depth": 3 -->
### `ipytest.clean_tests(pattern=<default>, *, module=None)`

[ipytest.clean_tests]: #ipytestclean_testspatterndefault--modulenone

Delete tests with names matching the given pattern.

In IPython the results of all evaluations are kept in global variables
unless explicitly deleted. This behavior implies that when tests are renamed
the previous definitions will still be found if not deleted. This method
aims to simply this process.

An effective pattern is to start with the cell containing tests with a call
to [`ipytest.clean_tests()`][ipytest.clean_tests], then defined all test
cases, and finally call [`ipytest.run()`][ipytest.run]. This way renaming
tests works as expected.

**Parameters:**

- `pattern`: a glob pattern used to match the tests to delete. If not given,
  the `"clean"` config option is used.
- `items`: the globals object containing the tests. If `None` is given, the
    globals object is determined from the call stack.

<!-- minidoc -->
<!-- minidoc "function": "ipytest.reload", "header_depth": 3 -->
### `ipytest.reload(*mods)`

[ipytest.reload]: #ipytestreloadmods

Reload all modules passed as strings.

This function may be useful, when mixing code in external modules and
notebooks.

Usage:

```python
ipytest.reload("ipytest._util", "ipytest")
```

<!-- minidoc -->
<!-- minidoc "class": "ipytest.Error", "header_depth": 3 -->
### `ipytest.Error(exit_code)`

[ipytest.Error]: #ipytesterrorexit_code

Error raised by ipytest on test failure

<!-- minidoc -->

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
Copyright (c) 2015 - 2022 Christopher Prohm

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
