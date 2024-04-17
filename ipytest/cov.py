"""A coverage.py plugin to support coverage in Jupyter notebooks

The plugin must be enabled in a `.coveragerc` next to the current notebook or
the `pyproject.toml` file. See the [coverage.py docs][coverage-py-config-docs]
for details. In case of a `.coveragerc` file, the minimal configuration reads:

```ini
[run]
plugins =
    ipytest.cov
```

With this config file, the coverage can be collected using
[pytest-cov][ipytest-cov-pytest-cov] with

```python
%%ipytest --cov

def test():
    ...
```

[coverage-py-config-docs]: https://coverage.readthedocs.io/en/latest/config.html
[ipytest-cov-pytest-cov]: https://pytest-cov.readthedocs.io/en/latest/config.html
"""
import linecache
import os
import os.path
import re

import coverage.parser
import coverage.plugin
import coverage.python

# prevent the definitions from being documented in the readme
__all__ = []


config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "coveragerc")


def coverage_init(reg, options):
    reg.add_file_tracer(IPythonPlugin())


class IPythonPlugin(coverage.plugin.CoveragePlugin):
    def __init__(self):
        self._filename_pattern = self._build_filename_pattern()

    @classmethod
    def _build_filename_pattern(self):
        try:
            import ipykernel.compiler

        except ImportError:
            return None

        else:
            return re.compile(
                r"^"
                + re.escape(ipykernel.compiler.get_tmp_directory())
                + re.escape(os.sep)
                + r"\d+.py"
            )

    def file_tracer(self, filename):
        if not self._is_ipython_cell_file(filename):
            return None

        return IPythonFileTracer(filename)

    def file_reporter(self, filename):
        return IPythonFileReporter(filename)

    def _is_ipython_cell_file(self, filename: str):
        if self._filename_pattern is None:
            return False

        if os.path.exists(filename):
            return False

        if self._filename_pattern.match(filename) is None:
            return False

        return filename in linecache.cache


class IPythonFileTracer(coverage.plugin.FileTracer):
    def __init__(self, filename):
        self._filename = filename

    def source_filename(self):
        return self._filename


class IPythonFileReporter(coverage.python.PythonFileReporter):
    @property
    def parser(self):
        if self._parser is None:
            self._parser = coverage.parser.PythonParser(text=self.source())
            self._parser.parse_source()

        return self._parser

    def source(self):
        if self.filename not in linecache.cache:
            raise ValueError()

        return "".join(linecache.cache[self.filename][2])
