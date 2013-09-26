#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright © 2013 Miguel González <migonzalvar@activitycentral.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

from setuptools import setup


__version__ = '0.1.1'

requires = [r.strip() for r in open('requirements.txt') if r]

setup(
    name='authserver',
    packages=['authserver'],
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
    scripts=['authserverctl'],

    # meta
    version=__version__,
    author=u'Miguel González',
    author_email='migonzalvar@activitycentral.com',
    url='https://github.com/migonzalvar/authserver',
    license = "GNU GPLv3+",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Flask',
        'Intended Audience :: Education',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: POSIX',
        'Programming Language :: Python',
    ],
)
