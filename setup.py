#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup


__version__ = '0.1'

requires = [r.strip() for r in open('requirements.txt') if r]

setup(
    name='authserver',
    packages=['authserver'],
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
    scripts=['runserver'],

    # meta
    version=__version__,
    author=u'Miguel González',
    author_email='migonzalvar@activitycentral.com',
    url='https://github.com/migonzalvar/authserver',
)
