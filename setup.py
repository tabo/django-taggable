#!/usr/bin/env python

import os
from distutils.command.install import INSTALL_SCHEMES
from distutils.core import setup

version = '0.01'

classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: Apache Software License",
    "Programming Language :: Python",
    "Operating System :: OS Independent",
    "Topic :: Software Development :: Libraries",
    "Topic :: Utilities",
    "Environment :: Web Environment",
    "Framework :: Django",
]

root_dir = os.path.dirname(__file__)
if not root_dir:
    root_dir = '.'
long_desc = open(root_dir + '/README').read()

setup(
    name='django-taggable',
    version=version,
    url='http://code.tabo.pe/django-taggable/',
    author='Gustavo Picon',
    author_email='tabo@tabo.pe',
    license='Apache License 2.0',
    packages = ['taggable'],
    package_dir={'taggable': 'taggable'},
    description='Efficient Tagging for Django 1.1+',
    classifiers=classifiers,
    long_description=long_desc,
)

