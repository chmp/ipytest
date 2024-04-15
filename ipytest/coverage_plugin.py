"""A plugin to support coverage in IPython notebooks"""
import coverage.plugin
import coverage.python
import coverage.parser

import linecache
import os.path
import re


def coverage_init(reg, options):
    reg.add_file_tracer(IPythonPlugin())


class IPythonPlugin(coverage.plugin.CoveragePlugin):
    ipython_cell_filename_pattern = r"^.*[\\/]ipykernel_\d+[\\/]\d+.py$"

    def file_tracer(self, filename):
        if self._is_ipython_cell_file(filename):
            return IPythonFileTracer(filename)

    def file_reporter(self, filename):
        return IPythonFileReporter(filename)

    @classmethod
    def _is_ipython_cell_file(cls, filename):
        if os.path.exists(filename):
            return False

        if re.match(cls.ipython_cell_filename_pattern, filename) is None:
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
