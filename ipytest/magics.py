import shlex
import warnings

from IPython import get_ipython
from IPython.core.magic import Magics, magics_class, cell_magic

from ipytest._config import config
from ipytest._pytest_support import run, RewriteContext
from ipytest._util import clean_tests


@magics_class
class IPyTestMagics(Magics):
    @cell_magic("run_pytest[clean]")
    def run_pytest_clean(self, line, cell):
        import __main__

        clean_tests(items=__main__.__dict__)
        return self.run_pytest(line, cell)

    @cell_magic
    def run_pytest(self, line, cell):
        # If config.rewrite_asserts is True assertions are being
        # rewritten by default, do not re-rewrite them.
        if not config.rewrite_asserts:
            self.rewrite_asserts(line, cell)

        else:
            self.shell.run_cell(cell)

        import ipytest

        ipytest.exit_code = run(*shlex.split(line), return_exit_code=True)

    @cell_magic
    def rewrite_asserts(self, line, cell):
        """Rewrite asserts with pytest.

        Usage::

            %%rewrite_asserts

            ...

            # new cell:
            from ipytest import run_pytest
            run_pytest()
        """
        if config.rewrite_asserts:
            warnings.warn("skip rewriting as global rewriting is active")
            return

        with RewriteContext(get_ipython()):
            self.shell.run_cell(cell)


get_ipython().register_magics(IPyTestMagics)
