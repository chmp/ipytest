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
        self.shell.run_cell(cell)
        run_pytest(
            pytest_options=shlex.split(line),
        )


get_ipython().register_magics(IPyTestMagics)
