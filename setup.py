#!/usr/bin/env python
import pathlib
from setuptools import setup


setup(
    name="ipytest",
    version="0.10.0b2",
    description="Unit tests in IPython notebooks.",
    long_description=pathlib.Path("Readme.md").read_text(),
    long_description_content_type="text/markdown",
    author="Christopher Prohm",
    url="https://github.com/chmp/ipytest",
    author_email="mail@cprohm.de",
    license="MIT",
    packages=["ipytest"],
    install_requires=["packaging", "ipython", "pytest>=5.4"],
    tests_require=["pytest"],
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
)
