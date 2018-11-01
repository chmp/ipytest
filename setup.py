#!/usr/bin/env python

from setuptools import setup


def _read(fname):
    with open(fname) as fobj:
        return fobj.read()


setup(
    name="ipytest",
    version="0.5.0b4",
    description="Unit tests in IPython notebooks.",
    long_description=_read("Readme.md"),
    author="Christopher Prohm",
    author_email="mail@cprohm.de",
    license="MIT",
    packages=["ipytest"],
    tests_require=["pytest"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
    ],
)
