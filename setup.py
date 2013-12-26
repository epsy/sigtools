#!/usr/bin/env python
from setuptools import setup
import sys

require_funcsigs = sys.version_info < (3,3)
requirements = ['six']

if require_funcsigs:
    requirements.append('funcsigs>=0.4')

setup(
    name='sigtools',
    version='0.1a2',
    description="Utilities for working with 3.3's inspect.Signature objects.",
    license='MIT',
    author='Yann Kaiser',
    author_email='kaiser.yann@gmail.com',
    url='http://sigtools.readthedocs.org/',
    packages=['sigtools'],
    install_requires=requirements,
    test_suite='sigtools.tests',
    keywords='introspection signature',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    )
