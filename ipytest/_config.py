"""Add syntatic sugar for configuration"""
import inspect
import warnings

default_clean = "[Tt]est*"

defaults = {
    "addopts": ("-q", "--color=yes"),
    "clean": default_clean,
    "coverage": False,
    "defopts": "auto",
    "display_columns": 100,
    "magics": True,
    "raise_on_error": False,
    "rewrite_asserts": True,
    "run_in_thread": False,
}

current_config = {
    "addopts": (),
    "clean": default_clean,
    "coverage": False,
    "defopts": "auto",
    "display_columns": 100,
    "magics": False,
    "raise_on_error": False,
    "rewrite_asserts": False,
    "run_in_thread": False,
}

_rewrite_transformer = None


class sentinel:
    "Adapt repr for better display in completion"

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"<{self.name}>"

    def unwrap(self, value, default):
        """If `value` is the sentinel return the default else the value"""
        return value if value is not self else default


keep = sentinel("keep")
default = sentinel("default")


def gen_default_docs(func):
    defaults_docs = "\n".join(
        f"    * `{key!s}`: `{value!r}`" for key, value in defaults.items()
    )
    defaults_docs = defaults_docs.strip()

    func.__doc__ = func.__doc__.format(defaults_docs=defaults_docs)
    return func


@gen_default_docs
def autoconfig(
    rewrite_asserts=default,
    magics=default,
    clean=default,
    addopts=default,
    run_in_thread=default,
    defopts=default,
    display_columns=default,
    raise_on_error=default,
    coverage=default,
):
    """Configure `ipytest` with reasonable defaults.

    Specifically, it sets:

    {defaults_docs}

    See [`ipytest.config`][ipytest.config] for details.
    """
    args = collect_args()
    config(
        **{key: default.unwrap(args[key], defaults.get(key)) for key in current_config},
    )


def config(
    rewrite_asserts=keep,
    magics=keep,
    clean=keep,
    addopts=keep,
    run_in_thread=keep,
    defopts=keep,
    display_columns=keep,
    raise_on_error=keep,
    coverage=default,
):
    """Configure `ipytest`

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
    * `raise_on_error` (default `False` ): if `True`,
      [`ipytest.run`][ipytest.run] and [`%%ipytest`][ipytest.ipytest] will raise
      an `ipytest.Error` if pytest fails.
    """
    args = collect_args()
    new_config = {
        key: keep.unwrap(args[key], current_config.get(key)) for key in current_config
    }

    if new_config["rewrite_asserts"] != current_config["rewrite_asserts"]:
        configure_rewrite_asserts(new_config["rewrite_asserts"])

    if new_config["magics"] != current_config["magics"]:
        configure_magics(new_config["magics"])

    current_config.update(new_config)
    return dict(current_config)


def configure_rewrite_asserts(enable):
    global _rewrite_transformer

    from IPython import get_ipython

    from ._impl import RewriteAssertTransformer

    shell = get_ipython()

    if enable:
        assert _rewrite_transformer is None
        _rewrite_transformer = RewriteAssertTransformer()
        _rewrite_transformer.register_with_shell(shell)

    else:
        assert _rewrite_transformer is not None
        _rewrite_transformer.unregister_with_shell(shell)
        _rewrite_transformer = None


def configure_magics(enable):
    from IPython import get_ipython

    from ._impl import ipytest_magic

    if enable:
        get_ipython().register_magic_function(ipytest_magic, "cell", "ipytest")

    else:
        warnings.warn("IPython does not support de-registering magics.")


def collect_args():
    frame = inspect.currentframe()
    frame = frame.f_back
    args, _, _, values = inspect.getargvalues(frame)
    return {key: values[key] for key in args}
