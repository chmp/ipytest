# Changes

Note: development is tracked on the [`develop` branch](https://github.com/chmp/ipytest/tree/develop).

- `develop`:
    - Use markdown for module documentation
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
