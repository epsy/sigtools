#!/usr/bin/env python
from setuptools import setup


with open("README.rst") as fh:
    long_description = fh.read()

tests_deps = [
    'repeated_test>=2.1.3',
    'sphinx',
    'mock',
    'coverage',
]

setup(
    name='sigtools',
    version='3.0.0',
    description="Utilities for working with inspect.Signature objects.",
    long_description=long_description,
    long_description_content_type='text/x-rst',
    license='MIT',
    author='Yann Kaiser',
    author_email='kaiser.yann@gmail.com',
    url='https://sigtools.readthedocs.io/',
    packages=['sigtools', 'sigtools.tests'],
    tests_require=tests_deps,
    install_requires=[],
    python_requires='>=3.6',
    extras_require={
        'test': tests_deps,
        'tests': tests_deps,
    },
    test_suite='unittest2.collector',
    keywords='introspection signature',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
