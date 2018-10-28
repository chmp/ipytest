"""Add syntatic sugar for configuration"""
import warnings


class ConfigKey:
    def __init__(self, func, default=None):
        self.func = func
        self.value = default

    def __get__(self, instance, owner):
        return self.value

    def __set__(self, instance, value):
        if self.value == value:
            return

        self.value = value
        self.func(instance, value)


def config_key(**kwargs):
    def decorator(func):
        return ConfigKey(func, **kwargs)

    return decorator


class Config:
    def __init__(self):
        self._rewrite_context = None

    def __call__(self, **updates):
        """Perform multiple context updates at the same time.

        The return value can be used as a context manager to revert any changes
        upon exit::

            with ipytest.config(base_args=['-qq']):
                ipytest.run()

        """
        context = ConfigContext(self, updates)
        context.__enter__()
        return context

    @config_key(default=False)
    def rewrite_asserts(self, value):
        from IPython import get_ipython
        from ._pytest_support import RewriteContext

        if value:
            assert self._rewrite_context is None
            self._rewrite_context = RewriteContext(shell=get_ipython())
            self._rewrite_context.__enter__()

        else:
            assert self._rewrite_context is not None
            self._rewrite_context.__exit__(None, None, None)
            self._rewrite_context = None

    @config_key(default=False)
    def magics(self, value):
        from IPython import get_ipython
        from ._pytest_support import IPyTestMagics

        if value:
            get_ipython().register_magics(IPyTestMagics)

        else:
            warnings.warn("IPython does not support de-registering magics.")
            pass

    @config_key(default="[Tt]est*")
    def clean(self, value):
        pass

    @config_key(default=())
    def base_args(self, value):
        pass

    @config_key(default=False)
    def raise_on_error(self, value):
        pass


class ConfigContext:
    def __init__(self, config, updates):
        self.config = config
        self.updates = updates
        self.old_values = None

    def __enter__(self):
        # re-entry, just do nothing
        if self.old_values is not None:
            return self

        self.old_values = {k: getattr(self.config, k) for k in self.updates}

        for k, v in self.updates.items():
            setattr(self.config, k, v)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.old_values is None:
            raise RuntimeError("Cannot exit, before entering.")

        for k, v in self.old_values.items():
            setattr(self.config, k, v)

        self.old_values = None


config = Config()
