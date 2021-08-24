#!/usr/bin/env python

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
import codecs
import os.path

# to access version
def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), "r") as fp:
        return fp.read()


def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith("__version__"):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")

long_description = "The `Adapter Python IO` software provides a convenient data table loader from various formats such as `xlsx`, `csv`, `db (sqlite database)`, and `sqlalchemy`. Its main feature is the ability to convert data tables identified in one main and optionally one or more additional input files into `database tables` and `Pandas DataFrames` for downstream usage in any compatible software. `Adapter` builds upon the existing Python packages that allow for the communication between `Python` and `MS Excel`, as well as `databases` and `csv` files. It provides inbuilt capabilities to specify the output location path, as well as a version identifier for a research code run.  In addition to the loading capability, an instance of the `Adapter` `IO` object has the write capability. If invoked, all loaded tables are written as either a single `database` or a set of `csv` files, or both. The purpose of this software is to support the development of research and analytical software through allowing for a simple multi-format IO with versioning and output path specification in the input data itself. The package is supported on `Windows` and `macOS`, as well as for `Linux` for the utilization without any `xlsx` inputs."

setup(
    name="adapterio",
    version=get_version("adapter/__init__.py"),
    description="I/O module",
    long_description=long_description,
    # The project's main homepage.
    url="https://github.com/LBNL-ETA/Adapter",
    # Author details
    author="Milica Grahovac, Youness Bennani, Thomas Burke, Katie Coughlin, Mohan Ganeshalingam, Akhil Mathur, Evan Neill, and Akshay Sharma",
    # Choose your license
    license="BSD-3-Clause-LBNL",
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Programming Language :: Python :: 3.8",
    ],
    keywords="data, tables, IO for research computation, sql, excel, csv, dataframe, connection",
    packages=find_packages(exclude=["*.tests", "*.tests"]),
    install_requires=[
        "pandas>=1.0.4",
        "xlwings>=0.19.4",
        "psycopg2-binary>=2.8.6",
    ],
)
