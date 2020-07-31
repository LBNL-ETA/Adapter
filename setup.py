#!/usr/bin/env python

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
import codecs
import os.path

# to access version
def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()

def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")

repo_name = "adapter"

long_description = "This package contains a data input/output adapter"

setup(
    name=repo_name,
    version=get_version("adapter/__init__.py"),
    description="I/O module",
    long_description=long_description,
    # The project's main homepage.
    url="https://bitbucket.org/eetd-ees/adapter",
    # Author details
    author="EES ATCD coders",
    # Choose your license
    license="ETA EAEI EES software",
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=["Programming Language :: Python :: 3.8",],
    keywords="i/o lcc nia shipments aps standards",
    packages=find_packages(exclude=["*.tests", "*.tests"]),
    install_requires=["pandas>=1.0.4", "xlwings>=0.19.4",],
)
