"""Generate the reference part of the Readme file.
"""
from __future__ import print_function, absolute_import, division

import inspect
import textwrap

import ipytest


def gen_reference():
    for name in ipytest.__all__:
        obj = getattr(ipytest, name)
        format_object(name, obj)


def format_object(name, obj):
    print("### {}".format(get_function_def(obj)))
    print()
    print(dedent(obj.__doc__))


def get_function_def(obj):
    lines = inspect.getsource(obj).strip().splitlines()
    def_line = lines[0]
    return def_line.replace("def ", "ipytest.").replace("):", ")")


def dedent(s):
    lines = s.splitlines()
    head, tail = lines[0], lines[1:]
    tail = textwrap.dedent("\n".join(tail))
    return "{}\n{}".format(head, tail)


if __name__ == "__main__":
    gen_reference()
