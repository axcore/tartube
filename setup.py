#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2020 A S Lewis
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
import os
import setuptools
import sys

# Import documents
#with open('README.rst', 'r') as f:
#    long_description = f.read()
#
#with open('LICENSE') as f:
#    license = f.read()


# For the Debian distribution, use an environment variable. When specified,
#   the 'tartube_debian' file is the executable, rather than the 'tartube'
#   file
# When the 'tartube_debian' file is the executable, youtube-dl updates are
#   disabled, and Tartube's config file is stored at $XDG_CONFIG_HOME
# The package maintainer should use
#   TARTUBE_NO_UPDATES=1 python3 setup.py build
env_var_name = 'TARTUBE_NO_UPDATES'
env_var_value = os.environ.get( env_var_name, None )
script_exec = os.path.join('tartube', 'tartube')

if env_var_value is not None:

    if env_var_value == '1':
        script_exec = os.path.join('tartube', 'tartube_debian')
        sys.stderr.write('youtube-dl updates are disabled in this version')

    else:
        sys.stderr.write(
            "Unrecognised '%s=%s' environment variable!\n" % (
                env_var_name,
                env_var_value,
            ),
        )


# Setup
setuptools.setup(
    name='tartube',
    version='1.3.086',
    description='GUI front-end for youtube-dl',
#    long_description=long_description,
    long_description="""Tartube is a GUI front-end for youtube-dl, partly based
        on youtube-dl-gui and written in Python 3 / Gtk 3""",
    long_description_content_type='text/markdown',
    url='https://tartube.sourceforge.io',
    author='A S Lewis',
    author_email='aslewis@cpan.org',
#    license=license,
#    license="""GPL3+""",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Multimedia :: Video',
        'License :: OSI Approved' \
        + ' :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='tartube video download youtube',
    packages=setuptools.find_packages(
        exclude=('docs', 'icons', 'nsis', 'tests'),
    ),
    include_package_data=True,
    python_requires='>=3.0, <4',
    install_requires=['requests', 'xdg'],
    scripts=[script_exec],
    project_urls={
        'Bug Reports': 'https://github.com/axcore/tartube/issues',
        'Source': 'https://github.com/axcore/tartube',
    },
)
