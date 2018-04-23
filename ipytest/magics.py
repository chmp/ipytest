import shlex

from IPython.core.magic import Magics, magics_class, cell_magic

from ipytest import clean_tests, run_pytest


@magics_class
class IPyTestMagics(Magics):
    @cell_magic('run_pytest[clean]')
    def run_pytest_clean(self, line, cell):
        import __main__
        clean_tests(items=__main__.__dict__)
        return self.run_pytest(line, cell)


    @cell_magic
    def run_pytest(self, line, cell):
        self.rewrite_asserts(line, cell)
        run_pytest(
            pytest_options=shlex.split(line),
        )

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
        from _pytest.assertion.rewrite import rewrite_asserts
        ipy = get_ipython()

        # follow InteractiveShell._run_cell
        cell_name = ipy.compile.cache(cell, ipy.execution_count)
        mod = ipy.compile.ast_parse(cell, filename=cell_name)

        # rewrite assert statements
        rewrite_asserts(mod)

        # follow InteractiveShell.run_ast_nodes
        code = ipy.compile(mod, cell_name, 'exec')
        self.shell.run_code(code)



get_ipython().register_magics(IPyTestMagics)
