import shlex

from IPython import get_ipython
from IPython.core.magic import Magics, magics_class, cell_magic

from ipytest._config import config
from ipytest._pytest_support import run
from ipytest._util import clean_tests, emit_deprecation_warning


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

        run(*shlex.split(line))

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
        emit_deprecation_warning(
            "Assertion rewriting via magics is deprecated. "
            "Use iyptest.config.rewrite_asserts = True instead."
        )

        # follow InteractiveShell._run_cell
        cell_name = self.shell.compile.cache(cell, self.shell.execution_count)
        mod = self.shell.compile.ast_parse(cell, filename=cell_name)

        # rewrite assert statements
        from _pytest.assertion.rewrite import rewrite_asserts

        rewrite_asserts(mod)

        # follow InteractiveShell.run_ast_nodes
        code = self.shell.compile(mod, cell_name, "exec")
        self.shell.run_code(code)


get_ipython().register_magics(IPyTestMagics)
