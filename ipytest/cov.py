"""A coverage.py plugin to support coverage in Jupyter notebooks

The plugin must be enabled in a `.coveragerc` next to the current notebook or
the `pyproject.toml` file. See the [coverage.py docs][coverage-py-config-docs]
for details. In case of a `.coveragerc` file, the minimal configuration reads:

```ini
[run]
plugins =
    ipytest.cov
```

With this config file, coverage information can be collected using
[pytest-cov][ipytest-cov-pytest-cov] with

```python
%%ipytest --cov

def test():
    ...
```

`ipytest.autoconfig(coverage=True)` automatically adds the `--cov` flag and the
path of a generated config file to the Pytest invocation. In this case no
further configuration is required.

There are some known issues of `ipytest.cov`

- Each notebook cell is reported as an individual file
- Lines that are executed at import time may not be encountered in tracing and
  may be reported as not-covered (One example is the line of a function
  definition)
- Marking code to be excluded in branch coverage is currently not supported
  (incl. coveragepy pragmas)

[coverage-py-config-docs]: https://coverage.readthedocs.io/en/latest/config.html
[ipytest-cov-pytest-cov]: https://pytest-cov.readthedocs.io/en/latest/config.html
"""
import linecache
import os
import os.path
import re
from typing import Optional

import coverage.parser
import coverage.plugin
import coverage.python

__all__ = ["translate_cell_filenames"]

_cell_filenames_tracker = None
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "coveragerc")


def translate_cell_filenames(enabled=True):
    """Translate the filenames of notebook cells in coverage information.

    If enabled, `ipytest.cov` will translate the temporary file names generated
    by ipykernel (e.g, `ipykernel_24768/3920661193.py`) to their cell names
    (e.g., `In[6]`).

    **Warning**: this is an experimental feature and not subject to any
    stability guarantees.
    """
    global _cell_filenames_tracker

    from IPython import get_ipython

    if enabled and _cell_filenames_tracker is None:
        _cell_filenames_tracker = CellFilenamesTracker()
        _cell_filenames_tracker.register(get_ipython())

    elif not enabled and _cell_filenames_tracker is not None:
        _cell_filenames_tracker.unregister()
        _cell_filenames_tracker = None


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
    # TODO: implement fully from scratch to be independent from PythonFileReporter impl

    def __repr__(self) -> str:
        return f"<IPythonFileReporter {self.filename!r}>"

    @property
    def parser(self):
        if self._parser is None:
            self._parser = coverage.parser.PythonParser(text=self.source())
            self._parser.parse_source()

        return self._parser

    def source(self):
        if self.filename not in linecache.cache:
            raise RuntimeError(f"Could not lookup source for {self.filename!r}")

        return "".join(linecache.cache[self.filename][2])

    def no_branch_lines(self):
        # TODO: figure out how to implement this (require coverage config)
        return set()

    def relative_filename(self) -> str:
        if _cell_filenames_tracker is None:
            return self.filename

        return _cell_filenames_tracker.translate_filename(self.filename)


class CellFilenamesTracker:
    """An IPython plugin to map temporary filenames to cells"""

    def __init__(self):
        self._info = {}
        self._execution_count_counts = {}
        self._shell = None

    def register(self, shell):
        if self._shell is not None:
            self.unregister()

        shell.events.register("post_run_cell", self.on_post_run_cell)
        self._shell = shell

    def unregister(self):
        if self._shell is not None:
            self._shell.events.unregister("post_run_cell", self.on_post_run_cell)
            self._shell = None

    def on_post_run_cell(self, result):
        if self._shell is None:
            return

        try:
            filename = self._shell.compile.get_code_name(
                result.info.raw_cell,
                None,
                None,
            )
        except Exception as _exc:
            # TODO: log exception
            return

        # NOTE: inside magic cells, the cell may be executed without storing the
        # history, e.g., inside the `%%ipytest` cell magic. In that case the
        # `execution_count` is `None`. Use the shell's execution count. However,
        # now it may be found multiple times. Therefore use an increasing
        # counter to avoid collisions
        execution_count = (
            result.execution_count
            if result.execution_count is not None
            else self._shell.execution_count
        )
        if execution_count in self._execution_count_counts:
            self._execution_count_counts[execution_count] += 1
            self._info[
                filename
            ] = f"In[{execution_count}/{self._execution_count_counts[execution_count]}]"

        else:
            self._execution_count_counts[execution_count] = 0
            self._info[filename] = f"In[{execution_count}]"

    def translate_filename(self, filename: str) -> Optional[int]:
        return self._info.get(filename, filename)
