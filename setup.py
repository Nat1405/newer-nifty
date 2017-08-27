# Shamelessly based on STScI's JWST calibration pipeline.

from __future__ import print_function

import os
import subprocess
import sys
from setuptools import setup, find_packages, Extension, Command
from glob import glob

NAME = 'niftyprealpha'
SCRIPTS = glob('scripts/*')
PACKAGE_DATA = {
    '': ['*.dat', '*.cfg', '*.fits']
}

setup(
    name=NAME,
    version="1.0.0.dev1",
    author='ncomeau',
    author_email='ncomeau@gemini.edu',
    description='Data reduction script for Gemini NIFS',
    url='http://www.gemini.edu',
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    scripts=SCRIPTS,
    packages=find_packages(),
    package_data=PACKAGE_DATA
)
