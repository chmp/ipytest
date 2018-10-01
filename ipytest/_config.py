"""Add syntatic sugar for configuration"""
import sys


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
        self.func(value)


def config_key(**kwargs):
    def decorator(func):
        return ConfigKey(func, **kwargs)

    return decorator


class Config:
    @config_key(default=False)
    def rewrite_asserts(value):
        from IPython import get_ipython
        from ._pytest_support import RewriteAssertTransformer

        if value:
            RewriteAssertTransformer.register(shell=get_ipython())

        else:
            RewriteAssertTransformer.unregister(shell=get_ipython())

    @config_key(default="[Tt]est*")
    def clean(value):
        pass


config = Config()
