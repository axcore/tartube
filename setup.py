#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-z2020 A S Lewis
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.


"""Standard python setup file."""


# Import modules
import glob
import os
import setuptools
import sys

# Set a standard long_description, modified only for Debian/RPM packages
long_description="""
Designed for use at the gym, GymBob prompts the user (graphically and using
sound effects) at regular intervals during a workout. The workout programmes
are completely customistable. GymBob is written in Python 3 / Gtk 3 and runs
on Linux/*BSD.
"""

# data_files for setuptools.setup are added here
param_list = []

# For Debian/RPM packaging, use environment variables:
#   GYMBOB_PKG=1 python3 setup.py build
script_exec = os.path.join('gymbob', 'gymbob')
icon_path = '/tartube/icons/'

pkg_flag = False
pkg_var = 'TARTUBE_PKG'
pkg_value = os.environ.get( pkg_var, None )

if pkg_value is not None:

    if pkg_value == '1':

        # Icons must be copied into the right place
        icon_path = '/usr/share/tartube/icons/'
        # Add a desktop file
        param_list.append(('share/applications', ['pack/gymbob.desktop']))
        param_list.append(('share/pixmaps', ['pack/gymbob.png']))
        param_list.append(('share/pixmaps', ['pack/gymbob.xpm']))
        # Add a manpage
        param_list.append(('share/man/man1', ['pack/gymbob.1']))

    else:
        sys.stderr.write(
            "Unrecognised '%s=%s' environment variable!\n" % (
                pkg_var,
                pkg_value,
            ),
        )

# For PyPI installations and Debian/RPM packaging, copy everything in ../icons
#   into a suitable location
subdir_list = ['win']
for subdir in subdir_list:
    for path in glob.glob('icons/' + subdir + '/*'):
        param_list.append((icon_path + subdir + '/', [path]))

# Setup
setuptools.setup(
    name='gymbob',
    version='1.002',
    description='Simple script to prompt the user during a workout',
    long_description=long_description,
    long_description_content_type='text/plain',
    url='https://gymbob.sourceforge.io',
    author='A S Lewis',
    author_email='aslewis@cpan.org',
#    license=license,
    license="""GPLv3+""",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Games/Entertainment',
        'License :: OSI Approved' \
        + ' :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='gymbob gym workout',
    packages=setuptools.find_packages(
        exclude=('docs', 'icons', 'tests'),
    ),
    include_package_data=True,
    python_requires='>=3.0, <4',
    install_requires=['playsound'],
    scripts=[script_exec],
    project_urls={
        'Bug Reports': 'https://github.com/axcore/gymbob/issues',
        'Source': 'https://github.com/axcore/gymbob',
    },
    data_files=param_list,
)
