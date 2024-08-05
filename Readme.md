# ipytest - pytest in Jupyter notebooks

[PyPI](https://pypi.org/project/ipytest)
| [Usage](#usage)
| [Global state](#global-state)
| [How does it work?](#how-does-it-work)
| [Changes](Changes.md)
| [Reference](#reference)
| [Development](#development)
| [Related packages](#related-packages)
| [License](#license)

`ipytest` allows you to run [pytest](https://pytest.org) in Jupyter notebooks.
`ipytest` aims to give access to the full `pytest` experience and to make it
easy to transfer tests out of notebooks into separate test files.

## Usage

Install `ipytest` by running

```bash
pip install ipytest
```

The suggested way to import `ipytest` is

```python
import ipytest
ipytest.autoconfig()
```

Afterwards in a *new* cell, tests can be executed as in

```python
%%ipytest -qq

def test_example():
    assert [1, 2, 3] == [1, 2, 3]
```

This command will first delete any previously defined tests, execute the cell
and then run pytest. For further details on how to use `ipytest` see the
[**example notebook**](./Example.ipynb) or the [reference](#reference) below.

## Global state

There are multiple sources of global state when using `pytest` inside the notebook:

1. `pytest` will find any test function ever defined. This behavior can lead to unexpected results
   when test functions are renamed, as their previous definition is still available inside the
   kernel. Running [`%%ipytest`][ipytest.ipytest] per default deletes any previously defined tests.
   The [`ipytest.clean()`][ipytest.clean] function allows to delete previously defined tests, as
   well.
2. Python's module system caches imports and therefore acts as a global state. To test the most
   recent version of any module, the module needs to be reloaded. `ipytest` offers the
   [`ipytest.force_reload()`][ipytest.force_reload] function. The `autoreload` extension of IPython
   may also help here. To test local packages, it is advisable to install them as development
   packages, e.g., `pip install -e .`.

   Note that local test files are imported by `pytest` and fall under the same restriction as other
   modules. To test the most recent version of the tests, the corresponding modules need to be
   reloaded. The [import behavior][pytest-import-docs] depends on both whether the tests are
   organized as packages (are `__init__.py` files present?) and the `pytest` configuration. For the
   default `pytest` configuration, `ipytest` can be configured with
   `ipytest.autoconfig(force_reload="test_*")`, assuming test modules prefixed with `test_` not
   organized into packages, or `ipytest.autoconfig(force_reload="tests")`, assuming tests grouped in
   a `tests` package.
3. For async code, IPython will create an event loop in the current thread. This setup may interfere
   with async tests. To support these use cases, ipytest supports running tests in a separate
   thread. Simply setup ipytest via `ipytest.autoconfig(run_in_thread=True)`.

[pytest-import-docs]: https://docs.pytest.org/en/latest/explanation/pythonpath.html

## How does it work?

In its default configuration (via `autoconfig()`), `ipytest` performs the
following steps:

1. Register `pytest`'s assertion rewriter with the IPython kernel. The rewriter
   will rewrite any assert statements entered into the notebook to give better
   error messages. This change will affect also non test based code, but should
   generally improve the development experience.
2. Ensure the notebook can be mapped to a file. `ipytest` will create a
   temporary file in the current directory and remove if afterwards.
3. Register the notebook scope temporarily as a module. This step is necessary
   to allow `pytest`'s doctest plugin to import the notebook.
4. Call `pytest` with the name of the temporary module

**NOTE:** Some notebook implementations modify the core IPython package and
magics may not work correctly (see [here][issue-47] or [here][issue-50]). In
this case, using [`ipytest.run()`][ipytest.run] and
[`ipytest.clean()`][ipytest.clean] directly should still work as expected.

[issue-47]: https://github.com/chmp/ipytest/issues/47
[issue-50]: https://github.com/chmp/ipytest/issues/50

## Reference

[`autoconfig`][ipytest.autoconfig]
| [`%%ipytest`][ipytest.ipytest]
| [`config`][ipytest.config]
| [`exit_code`][ipytest.exit_code]
| [`run`][ipytest.run]
| [`clean`][ipytest.clean]
| [`force_reload`][ipytest.force_reload]
| [`Error`][ipytest.Error]
| [`ipytest.cov`](#ipytestcov)

<!-- minidoc "function": "ipytest.autoconfig", "header_depth": 3 -->
### `ipytest.autoconfig(rewrite_asserts=<default>, magics=<default>, clean=<default>, addopts=<default>, run_in_thread=<default>, defopts=<default>, display_columns=<default>, raise_on_error=<default>, coverage=<default>, force_reload=<default>)`

[ipytest.autoconfig]: #ipytestautoconfigrewrite_assertsdefault-magicsdefault-cleandefault-addoptsdefault-run_in_threaddefault-defoptsdefault-display_columnsdefault-raise_on_errordefault-coveragedefault-force_reloaddefault

Configure `ipytest` with reasonable defaults.

Specifically, it sets:

* `addopts`: `('-q', '--color=yes')`
* `clean`: `'[Tt]est*'`
* `coverage`: `False`
* `defopts`: `'auto'`
* `display_columns`: `100`
* `magics`: `True`
* `raise_on_error`: `False`
* `rewrite_asserts`: `True`
* `run_in_thread`: `False`
* `force_reload`: `()`

See [`ipytest.config`][ipytest.config] for details.

<!-- minidoc -->

### `%%ipytest ...`

[ipytest.ipytest]: #ipytest-

<!-- minidoc "function": "ipytest._impl.ipytest_magic", "header": false, "header_depth": 3 -->
IPython magic to first execute the cell, then execute [`ipytest.run()`][ipytest.run].

**Note:** the magics are only available after running
[`ipytest.autoconfig()`][ipytest.autoconfig] or
[`ipytest.config(magics=True)`][ipytest.config].

It cleans any previously found tests, i.e., only tests defined in the
current cell are executed. To disable this behavior, use
[`ipytest.config(clean=False)`][ipytest.config].

Any arguments passed on the magic line are interpreted as command line
arguments to to `pytest`. For example calling the magic as

```python
%%ipytest -qq
```

is equivalent to passing `-qq` to pytest. The arguments are formatted using
Python's standard string formatting. Currently, only the `{MODULE}` variable
is understood. It is replaced with the filename associated with the
notebook. In addition node ids for tests can be generated by using the test
name as a key, e.g., `{test_example}` will expand to
`{MODULE}::test_example`.

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

**NOTE:** In the default configuration `%%ipytest` will not raise
exceptions, when tests fail. To raise exceptions on test errors, e.g.,
inside a CI/CD context, use `ipytest.autoconfig(raise_on_error=True)`.

<!-- minidoc -->

<!-- minidoc "function": "ipytest.config", "header_depth": 3 -->
### `ipytest.config(rewrite_asserts=<keep>, magics=<keep>, clean=<keep>, addopts=<keep>, run_in_thread=<keep>, defopts=<keep>, display_columns=<keep>, raise_on_error=<keep>, coverage=<keep>, force_reload=<keep>)`

[ipytest.config]: #ipytestconfigrewrite_assertskeep-magicskeep-cleankeep-addoptskeep-run_in_threadkeep-defoptskeep-display_columnskeep-raise_on_errorkeep-coveragekeep-force_reloadkeep

Configure `ipytest`

To update the configuration, call this function as in:

```python
ipytest.config(rewrite_asserts=True)
```

The following settings are supported:

* `rewrite_asserts` (default: `False`): enable ipython AST transforms
  globally to rewrite asserts
* `magics` (default: `False`): if set to `True` register the ipytest magics
* `coverage` (default: `False`): if `True` configure `pytest` to collect
  coverage information. This functionality requires the `pytest-cov` package
  to be installed. It adds `--cov --cov-config={GENERATED_CONFIG}` to the
  arguments when invoking `pytest`. **WARNING**: this option will hide
  existing coverage configuration files. See [`ipytest.cov`](#ipytestcov)
  for details
* `clean` (default: `[Tt]est*`): the pattern used to clean variables
* `addopts` (default: `()`): pytest command line arguments to prepend to
  every pytest invocation. For example setting
  `ipytest.config(addopts=['-qq'])` will execute pytest with the least
  verbosity. Consider adding `--color=yes` to force color output
* `run_in_thread` (default: `False`): if `True`, pytest will be run a
  separate thread. This way of running is required when testing async code
  with `pytest_asyncio` since it starts a separate event loop
* `defopts` (default: `"auto"`): either `"auto"`, `True` or `False`
  * if `"auto"`, `ipytest` will add the current notebook module to the
    command line arguments, if no pytest node ids that reference the
    notebook are provided by the user
  * If `True`, ipytest will add the current module to the arguments passed
    to pytest
  * If `False` only the arguments given and `adopts` are passed to pytest
* `display_columns` (default: `100`): if not `False`, configure pytest to
  use the given number of columns for its output. This option will
  temporarily override the `COLUMNS` environment variable.
* `raise_on_error` (default `False`): if `True`,
  [`ipytest.run`][ipytest.run] and [`%%ipytest`][ipytest.ipytest] will raise
  an `ipytest.Error` if pytest fails.
* `force_reload` (default `()`): a sequence of modules to remove from the
  global module cache before executing tests. The listed modules are passed
  to [`ipytest.force_reload`][ipytest.force_reload]. For simplicity, a
  single module can also be specified as a string. Glob-style wildcards are
  supported.

<!-- minidoc -->

### `ipytest.exit_code`

[ipytest.exit_code]: #ipytestexit_code

The return code of the last pytest invocation.

<!-- minidoc "function": "ipytest.run", "header_depth": 3 -->
### `ipytest.run(*args, module=None, plugins=(), run_in_thread=<default>, raise_on_error=<default>, addopts=<default>, defopts=<default>, display_columns=<default>, coverage=<default>, force_reload=<default>)`

[ipytest.run]: #ipytestrunargs-modulenone-plugins-run_in_threaddefault-raise_on_errordefault-addoptsdefault-defoptsdefault-display_columnsdefault-coveragedefault-force_reloaddefault

Execute all tests in the passed module (defaults to `__main__`) with pytest.

This function is a thin wrapper around `pytest.main` and will execute any tests
defined in the current notebook session.

**NOTE:** In the default configuration `ipytest.run()` will not raise
exceptions, when tests fail. To raise exceptions on test errors, e.g.,
inside a CI/CD context, use `ipytest.autoconfig(raise_on_error=True)`.

**Parameters:**

- `args`: additional commandline options passed to pytest
- `module`: the module containing the tests. If not given, `__main__` will
  be used.
- `plugins`: additional plugins passed to pytest.

The following parameters override the config options set with
[`ipytest.config()`][ipytest.config] or
[`ipytest.autoconfig()`][ipytest.autoconfig]: `run_in_thread`,
`raise_on_error`, `addopts`, `defopts`, `display_columns`, `coverage`,
`force_reload`.

**Returns**: the exit code of `pytest.main`.

<!-- minidoc -->
<!-- minidoc "function": "ipytest.clean", "header_depth": 3 -->
### `ipytest.clean(pattern=<default>, *, module=None)`

[ipytest.clean]: #ipytestcleanpatterndefault--modulenone

Delete tests with names matching the given pattern.

In IPython the results of all evaluations are kept in global variables
unless explicitly deleted. This behavior implies that when tests are renamed
the previous definitions will still be found if not deleted. This method
aims to simply this process.

An effective pattern is to start with the cell containing tests with a call
to [`ipytest.clean()`][ipytest.clean], then defined all test cases, and
finally call [`ipytest.run()`][ipytest.run]. This way renaming tests works
as expected.

**Parameters:**

- `pattern`: a glob pattern used to match the tests to delete. If not given,
  the `"clean"` config option is used.
- `items`: the globals object containing the tests. If `None` is given, the
    globals object is determined from the call stack.

<!-- minidoc -->
<!-- minidoc "function": "ipytest.force_reload", "header_depth": 3 -->
### `ipytest.force_reload(*include, modules: Optional[Dict[str, module]] = None)`

[ipytest.force_reload]: #ipytestforce_reloadinclude-modules-optionaldictstr-module--none

Ensure following imports of the listed modules reload the code from disk

The given modules and their submodules are removed from `sys.modules`.
Next time the modules are imported, they are loaded from disk. The module
names can use glob patterns, e.g., `test_*` to delete all test modules.

If given, the parameter `modules` should be a dictionary of modules to work
on instead of `sys.modules`.

Usage:

```python
ipytest.force_reload("my_package")
from my_package.submodule import my_function
```

This function can be used to ensure that the most recent version of test
files is used inside notebook via:

```python
ipytest.force_reload("test_*")
ipytest.run(".")
```

<!-- minidoc -->
<!-- minidoc "class": "ipytest.Error", "header_depth": 3 -->
### `ipytest.Error(exit_code)`

[ipytest.Error]: #ipytesterrorexit_code

Error raised by ipytest on test failure

<!-- minidoc -->

<!-- minidoc "module": "ipytest.cov", "header_depth": 3 -->
### `ipytest.cov`

A coverage.py plugin to support coverage in Jupyter notebooks

The plugin must be enabled in a `.coveragerc` next to the current notebook or
the `pyproject.toml` file. See the [coverage.py docs][coverage-py-config-docs]
for details. In case of a `.coveragerc` file, the minimal configuration reads:

```ini
[run]
plugins =
    ipytest.cov
```

With this config file, coverage information can be collected using
[pytest-cov][ipytest-cov-pytest-cov] with

```python
%%ipytest --cov

def test():
    ...
```

`ipytest.autoconfig(coverage=True)` automatically adds the `--cov` flag and the
path of a generated config file to the Pytest invocation. In this case no
further configuration is required.

There are some known issues of `ipytest.cov`

- Each notebook cell is reported as an individual file
- Lines that are executed at import time may not be encountered in tracing and
  may be reported as not-covered (One example is the line of a function
  definition)
- Marking code to be excluded in branch coverage is currently not supported
  (incl. coveragepy pragmas)

[coverage-py-config-docs]: https://coverage.readthedocs.io/en/latest/config.html
[ipytest-cov-pytest-cov]: https://pytest-cov.readthedocs.io/en/latest/config.html

#### `ipytest.cov.translate_cell_filenames(enabled=True)`

[ipytest.cov.translate_cell_filenames]: #ipytestcovtranslate_cell_filenamesenabledtrue

Translate the filenames of notebook cells in coverage information.

If enabled, `ipytest.cov` will translate the temporary file names generated
by ipykernel (e.g, `ipykernel_24768/3920661193.py`) to their cell names
(e.g., `In[6]`).

**Warning**: this is an experimental feature and not subject to any
stability guarantees.

<!-- minidoc -->

## Development

Setup a Python 3.10 virtual environment and install the requirements via

```bash
pip install -r requirements-dev.txt
pip install -e .
```

To execute the unit tests of `ipytest` run

```bash
python x.py test
python x.py integration
```

Before committing, execute `python x.py precommit` to update the documentation,
format the code, and run tests.

To create a new release execute:

```bash
python x.py release
```

## Related packages

`ipytest` is designed to enable running tests within an interactive notebook
session. There are also other packages that aim to use test full notebooks:
these packages run the notebook and compare the output of cells to the output of
previous runs. These packages include:

- [nbval](https://github.com/computationalmodelling/nbval)
- [nbmake](https://github.com/treebeardtech/nbmake)
- [pytest-ipynb](https://github.com/zonca/pytest-ipynb) is no longer
  maintained
- ...

While PyTest itself is generally supported, support for PyTest plugins depends
very much on the plugin. The following plugins are known to not work:

- [pytest-xdist](https://github.com/chmp/ipytest/issues/90)

See [`ipytest.cov`](#ipytestcov) on how to use `ipytest` with
[pytest-cov](https://pytest-cov.readthedocs.io/en/latest/config.html).

Please create an issue, if I missed a packaged or mischaracterized any package.

## License

```
The MIT License (MIT)
Copyright (c) 2015 - 2024 Christopher Prohm

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
