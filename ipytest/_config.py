"""Add syntatic sugar for configuration"""


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

    @config_key(default="[Tt]est*")
    def clean(self, value):
        pass


config = Config()
