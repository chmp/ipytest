# Changes

Note: development is tracked on the [`develop` branch](https://github.com/chmp/ipytest/tree/develop).

## `development`

- Support glob patterns in `ipytest.force_reload`. E.g.,
  `ipytest.force_reload("test_*")`

## `0.14.2`

- Support collecting branch coverage in notebooks (e.g., via `--cov--branch`)
- Add `ipytest.autoconfig(coverage=True)` to simplify using `pytest-cov` inside
  notebooks
- Add experimental `ipytest.cov.translate_cell_filenames()` to simplify
  interpretation of collected coverage information

## `0.14.1`

- Add a [Coverage.py](https://coverage.readthedocs.io/en/latest/index.html)
  plugin (`ipytest.cov`) to support collecting coverage information in
  notebooks. See the Readme for usage notes.

## `0.14.0`

- Removed support for Python 3.7 after it reached its end of life
- Updated the dev-requirements (in particular `pytest==8.0.0`)
- Remove deprecated API (`ipytest.clean_tests`, `%%pytest`, `%%pytest[clean]`)

## `0.13.3`

- Include License.md file in sdist for condaforge

## `0.13.2`

- Fix assertion rewriting for python==3.11 ([issue][issue-93])

[issue-93]: https://github.com/chmp/ipytest/issues/93

## `0.13.1`

- Updated readme and doc strings.

## `0.13.0`

Usability improvements:

- Use the same random module name during a notebook session to allow `--ff` and
  similar options to work correctly
- Allow to specify `defopts="auto"`. It only adds the current notebook to the
  PyTest arguments, if no other node id that referencing the notebook is
  specified. This way specifying node ids manually should work as expected
  without any configuration change in most cases
- Add shorthands to generate node ids for tests using `{test_example}` as an
  argument will expand to `{MODULE}::test_example`
- Allow to override `addopts`, `defopts`, `run_in_thread`, `raise_on_error`,
  `display_columns` in `ipytest.run`
- Allow to specify all keyword arguments of `ipytest.run` also in `%%ipytest` by
  including an initial comment of the form `# ipytest: arg1=value1, arg2=value`
- Rename `clean_tests` to `clean` and deprecate `clean_tests`. The optional
  scope argument now expects a module instead of a dictionary
- Add `ipytest.force_reload`, as a simpler to use alternative to the current
  `reload` function

Bug fixes:

- Fix bug for `--deselect {MODULE}::test`
- Disable variable expansion in magics to prevent issues with the `{node_id}`
  shorthands in notebooks

Development changes:

- Use markdown for module documentation and doc strings
- Migrated to `pyproject.toml`
- Updated documentation

## Previous versions

- `0.12.0`:
    - Re-add the `raise_on_error` config option
    - Return the `exit_code` from `ipyest.run()`
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
