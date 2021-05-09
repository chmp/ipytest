"""Add syntatic sugar for configuration"""
import inspect
import warnings

default_clean = "[Tt]est*"

defaults = dict(
    rewrite_asserts=True,
    magics=True,
    tempfile_fallback=True,
    clean=default_clean,
    addopts=("-q",),
    raise_on_error=False,
    run_in_thread=False,
)

current_config = dict(
    rewrite_asserts=False,
    magics=False,
    tempfile_fallback=False,
    clean=default_clean,
    addopts=(),
    raise_on_error=False,
    run_in_thread=False,
    register_module=False,
)

_rewrite_context = None


class repr_meta(type):
    "Adapt repr for better display in completion"

    def __repr__(self):
        return "<{}>".format(self.__name__)


class keep(metaclass=repr_meta):
    """Sentinel for the config call"""

    pass


class default(metaclass=repr_meta):
    """Sentinel to mark a default argument"""

    pass


def gen_default_docs(func):
    defaults_docs = "\n".join(
        "    * ``{key!s}``: ``{value!r}``".format(key=key, value=value)
        for key, value in defaults.items()
    )
    defaults_docs = defaults_docs.strip()

    func.__doc__ = func.__doc__.format(defaults_docs=defaults_docs)
    return func


@gen_default_docs
def autoconfig(
    rewrite_asserts=default,
    magics=default,
    tempfile_fallback=default,
    clean=default,
    addopts=default,
    raise_on_error=default,
    run_in_thread=default,
    register_module=default,
):
    """Configure ``ipytest`` with reasonable defaults.

    Specifically, it sets:

    {defaults_docs}

    See :func:`ipytest.config` for details.
    """
    args = collect_args()
    config(
        **{
            key: replace_with_default(default, args[key], defaults.get(key))
            for key in current_config
        }
    )


def config(
    rewrite_asserts=keep,
    magics=keep,
    tempfile_fallback=keep,
    clean=keep,
    addopts=keep,
    raise_on_error=keep,
    run_in_thread=keep,
    register_module=keep,
):
    """Configure `ipytest`

    To update the configuration, call this function as in::

        ipytest.config(rewrite_asserts=True, raise_on_error=True)

    The following settings are suported:

    * ``rewrite_asserts`` (default: ``False``): enable ipython AST transforms
        globally to rewrite asserts
    * ``magics`` (default: ``False``): if set to ``True`` register the ipytest
        magics
    * ``clean`` (default: ``[Tt]est*``): the pattern used to clean variables
    * ``addopts`` (default: ``()``): pytest command line arguments to prepend
        to every pytest invocation. For example setting
        ``ipytest.config(addopts=['-qq'])`` will execute pytest with the least
        verbosity
    * ``raise_on_error`` (default: ``False``): if ``True``, unsuccessful
        invocations will raise a ``RuntimeError``
    * ``tempfile_fallback`` (default: ``False``): if ``True``, a temporary file
        is created as a fallback when no valid filename can be determined
    * ``run_in_thread`` (default: ``False``): if ``True``, pytest will be run a
        separate thread. This way of running is required when testing async
        code with ``pytest_asyncio`` since it starts a separate event loop
    * ``register_module`` (default: ``False``): if ``True``, ipytest will
        register the notebook with Python module system. This way the module
        can be imported. Some pytest plugins require importing the module. An
        example is the doctest module. It is strongly recommended to only use
        ``register_module=True`` with the ``tempfile_fallback``, since
        otherwise real modules may be shadowed
    """
    args = collect_args()
    new_config = {
        key: replace_with_default(keep, args[key], current_config.get(key))
        for key in current_config
    }

    if new_config["rewrite_asserts"] != current_config["rewrite_asserts"]:
        configure_rewrite_asserts(new_config["rewrite_asserts"])

    if new_config["magics"] != current_config["magics"]:
        configure_magics(new_config["magics"])

    current_config.update(new_config)
    return dict(current_config)


def configure_rewrite_asserts(enable):
    global _rewrite_context

    from IPython import get_ipython
    from ._pytest_support import RewriteContext

    if enable:
        assert _rewrite_context is None
        _rewrite_context = RewriteContext(shell=get_ipython())
        _rewrite_context.__enter__()

    else:
        assert _rewrite_context is not None
        _rewrite_context.__exit__(None, None, None)
        _rewrite_context = None


def configure_magics(enable):
    from IPython import get_ipython
    from ._pytest_support import IPyTestMagics

    if enable:
        get_ipython().register_magics(IPyTestMagics)

    else:
        warnings.warn("IPython does not support de-registering magics.")


def replace_with_default(sentinel, value, default):
    return default if value is sentinel else value


def collect_args():
    frame = inspect.currentframe()
    frame = frame.f_back
    args, _, _, values = inspect.getargvalues(frame)
    return {key: values[key] for key in args}
