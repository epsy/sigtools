#!/usr/bin/env python
from setuptools import setup
import sys

require_funcsigs = sys.version_info < (3,3)
requires = ['six']

if require_funcsigs:
    requires.append('funcsigs>=0.4')

setup(
    name='sigtools',
    version='0.1a2',
    author='Yann Kaiser',
    author_email='kaiser.yann@gmail.com',
    url='http://sigtools.readthedocs.org/',
    packages=['sigtools'],
    install_requires=requires,
    test_suite='sigtools.tests',
    )
