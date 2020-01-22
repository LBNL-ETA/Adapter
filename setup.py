#!/usr/bin/env python

# Always prefer setuptools over distutils
from setuptools import setup, find_packages

repo_name = 'adapter'

long_description = "This package contains a data input/output adapter"

setup(
    name=repo_name,

    version='0.0',
    description='I/O module',
    long_description=long_description,

    # The project's main homepage.
    url='https://bitbucket.org/eetd-ees/adapter',

    # Author details
    author='EES coders',

    # Choose your license
    license='ETA EAEI EES software',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Programming Language :: Python :: 3.6',
        ],

    keywords='i/o lcc nia shipments aps standards',

    packages=find_packages(exclude=['adapter/tests', 'adapter/comm/tests']),

    install_requires=[],
    )
