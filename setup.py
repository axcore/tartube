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
import glob
import os
import setuptools
import sys

# Set a standard long_description, modified only for Debian/RPM packages
long_description="""
Tartube is a GUI front-end for youtube-dl, partly based on youtube-dl-gui
and written in Python 3 / Gtk 3.

- You can download individual videos, and even whole channels and
playlists, from YouTube and hundreds of other websites
- You can fetch information about those videos, channels and playlists,
without actually downloading anything
- Tartube will organise your videos into convenient folders
- If creators upload their videos to more than one website (YouTube and
BitChute, for example), you can download videos from both sites without
creating duplicates
- Certain popular websites manipulate search results, repeatedly
unsubscribe people from their favourite channels and/or deliberately
conceal videos that they don't like. Tartube won't do any of those things
- Tartube can, in some circumstances, see videos that are region-blocked
and/or age-restricted

Note for PyPI users: Tartube should be installed with: pip3 install tartube
"""

alt_description = """
Tartube is a GUI front-end for youtube-dl, partly based on youtube-dl-gui
and written in Python 3 / Gtk 3.
"""

# data_files for setuptools.setup are added here
param_list = []

# For Debian/RPM packaging, use environment variables
# For example, the package maintainer might use either of the following:
#   TARTUBE_PKG=1 python3 setup.py build
#   TARTUBE_PKG_STRICT=1 python3 setup.py build
# (Specifying both variables is the same as specifying TARTUBE_PKG_STRICT
#   alone)
#
# There are three executables: the default one in ../tartube, and two
#   alternative ones in ../pack/bin and ../pack/bin_strict
# If TARTUBE_PKG_STRICT is specified, then ../pack/bin_strict/tartube is the
#   executable, which means that youtube-dl updates are disabled. Also, icon
#   files are copied into /usr/share/tartube/icons
pkg_strict_var = 'TARTUBE_PKG_STRICT'
pkg_strict_value = os.environ.get( pkg_strict_var, None )
script_exec = os.path.join('tartube', 'tartube')
icon_path = '/tartube/icons/'
sound_path = '/tartube/sounds/'
pkg_flag = False

if pkg_strict_value is not None:

    if pkg_strict_value == '1':
        script_exec = os.path.join('pack', 'bin_strict', 'tartube')
        sys.stderr.write('youtube-dl updates are disabled in this version\n')
        pkg_flag = True

    else:
        sys.stderr.write(
            "Unrecognised '%s=%s' environment variable!\n" % (
                pkg_strict_var,
                pkg_strict_value,
            ),
        )

# If TARTUBE_PKG is specified, then ../pack/bin/tartube is the executable,
#   which means that youtube-dl updates are enabled. Also, icon files are
#   copied into /usr/share/tartube/icons
pkg_var = 'TARTUBE_PKG'
pkg_value = os.environ.get( pkg_var, None )

if pkg_value is not None:

    if pkg_value == '1':
        script_exec = os.path.join('pack', 'bin', 'tartube')
        pkg_flag = True

    else:
        sys.stderr.write(
            "Unrecognised '%s=%s' environment variable!\n" % (
                pkg_var,
                pkg_value,
            ),
        )

# Apply changes if either environment variable was specified
if pkg_flag:

    # Icons/sounds must be copied into the right place
    icon_path = '/usr/share/tartube/icons/'
    sound_path = '/usr/share/tartube/sounds/'
    # Use a shorter long description, as the standard one tends to cause errors
    long_description = alt_description
    # Add a desktop file
    param_list.append(('share/applications', ['pack/tartube.desktop']))
    param_list.append(('share/pixmaps', ['pack/tartube.png']))
    param_list.append(('share/pixmaps', ['pack/tartube.xpm']))
    # Add a manpage
    param_list.append(('share/man/man1', ['pack/tartube.1']))

# For PyPI installations and Debian/RPM packaging, copy everything in ../icons
#   and ../sounds into a suitable location
subdir_list = [
    'dialogue',
    'large',
    'locale',
    'small',
    'status',
    'toolbar',
    'win',
]

for subdir in subdir_list:
    for path in glob.glob('icons/' + subdir + '/*'):
        param_list.append((icon_path + subdir + '/', [path]))

for path in glob.glob('sounds/*'):
    param_list.append((icon_path + '/', [path]))

# Setup
setuptools.setup(
    name='tartube',
    version='2.2.117',
    description='GUI front-end for youtube-dl',
    long_description=long_description,
    long_description_content_type='text/plain',
    url='https://tartube.sourceforge.io',
    author='A S Lewis',
    author_email='aslewis@cpan.org',
#    license=license,
    license="""GPLv3+""",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
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
    install_requires=['feedparser', 'pgi', 'playsound', 'requests'],
    scripts=[script_exec],
    project_urls={
        'Bug Reports': 'https://github.com/axcore/tartube/issues',
        'Source': 'https://github.com/axcore/tartube',
    },
    data_files=param_list,
)
