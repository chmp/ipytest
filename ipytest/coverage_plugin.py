"""A plugin to support coverage in IPython notebooks"""
import linecache
import os
import os.path
import re

import coverage.parser
import coverage.plugin
import coverage.python


def coverage_init(reg, options):
    reg.add_file_tracer(IPythonPlugin())


class IPythonPlugin(coverage.plugin.CoveragePlugin):
    def __init__(self):
        try:
            import ipykernel.compiler

        except ImportError:
            self._active = False
            self._filename_pattern = None

        else:
            self._active = True
            self._filename_pattern = re.compile(
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
        if not self._active:
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
