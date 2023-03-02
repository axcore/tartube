#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2023 A S Lewis
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


"""Standard python setup file."""


# Import modules
import glob
import os
import setuptools
import sys

# Set a standard long_description, modified only for Debian/RPM packages
long_description="""
Tartube is a GUI front-end for youtube-dl, yt-dlp and other compatible video
downloaders.

It is written in Python 3 / Gtk 3 and runs on MS Windows, Linux, BSD and MacOS.

- You can fetch a list of videos from your favourite channels and playlists on
YouTube, BitChute, and hundreds of other websites
- In buffering is an issue, you can download a temporary copy of a video before
automatically opening it in your favourite media player
- Tartube will organise your videos into convenient folders (if that's what you
want)
- Tartube can alert you when livestreams and debut videos are starting (YouTube
only)
- If creators upload their videos to more than one website (YouTube and
BitChute, for example), Tartube can interact with both sites without creating
duplicates
- Certain websites operate an "only one opinion allowed" policy. If you think
that the censors will remove a video, against the wishes of its creators and
before you've had a chance to watch it, Tartube can make an archive copy
- Certain websites frequently place restrictions on a video, not because it is
unsuitable for some audiences, but for purely political reasons. Tartube can,
in some circumstances, see videos that are region-blocked and/or age-restricted
- Certain websites manipulate search results, repeatedly unsubscribe people
from their favourite channels and/or deliberately conceal videos that they
don't like. Tartube won't do any of those things
- If you want to listen to your favourite discussion videos, for example while
driving a car, Tartube can make an archive copy of just the audio, rather than
the full video
- Tartube is free and open-source software

Note for PyPI users: Tartube should be installed with: pip3 install tartube
"""

alt_description = """
Tartube is a GUI front-end for youtube-dl, yt-dlp and other compatible video
downloaders.
"""

# data_files for setuptools.setup are added here
param_list = []

# For Debian/RPM packaging, use environment variables
# For example, the package maintainer might use any of the following:
#   TARTUBE_PKG=1 python3 setup.py build
#   TARTUBE_PKG_STRICT=1 python3 setup.py build
#   TARTUBE_PKG_NO_DOWNLOAD=1 python3 setup.py build
#
# There are four executables: the default one in ../tartube, and alternative
#   ones in ../pack/bin, ../pack/bin_strict and ../pack/bin_no_download
#
# If TARTUBE_PKG is specified, then ../pack/bin/pkg/tartube is the executable,
#   which means that youtube-dl updates are enabled. Also, icon files are
#   copied into /usr/share/tartube/icons
pkg_var = 'TARTUBE_PKG'
pkg_value = os.environ.get( pkg_var, None )
# If TARTUBE_PKG_STRICT is specified, then ../pack/bin/strict/tartube is the
#   executable, which means that youtube-dl updates are disabled. Also, icon
#   files are copied into /usr/share/tartube/icons
pkg_strict_var = 'TARTUBE_PKG_STRICT'
pkg_strict_value = os.environ.get( pkg_strict_var, None )
# TARTUBE_PKG_NO_DOWNLOAD has all the features of TARTUBE_PKG_STRICT and, in
#   addition, videos cannot be downloaded. Tartube can still fetch a list of
#   videos in channels/playlists, monitor when livestreams start, and so on.
#   The executable is ../pack/bin/no_download/tartube
pkg_no_download_var = 'TARTUBE_PKG_NO_DOWNLOAD'
pkg_no_download_value = os.environ.get( pkg_no_download_var, None )

script_exec = os.path.join('tartube', 'tartube')
icon_path = '/tartube/icons/'
sound_path = '/tartube/sounds/'
pkg_flag = False

if pkg_no_download_value is not None:

    if pkg_no_download_value == '1':
        script_exec = os.path.join('pack', 'bin', 'no_download', 'tartube')
        sys.stderr.write('youtube-dl updates are disabled in this version\n')
        pkg_flag = True

    else:
        sys.stderr.write(
            "Unrecognised '%s=%s' environment variable!\n" % (
                pkg_no_download_var,
                pkg_no_download_value,
            ),
        )

elif pkg_strict_value is not None:

    if pkg_strict_value == '1':
        script_exec = os.path.join('pack', 'bin', 'strict', 'tartube')
        sys.stderr.write('youtube-dl updates are disabled in this version\n')
        pkg_flag = True

    else:
        sys.stderr.write(
            "Unrecognised '%s=%s' environment variable!\n" % (
                pkg_strict_var,
                pkg_strict_value,
            ),
        )

elif pkg_value is not None:

    if pkg_value == '1':
        script_exec = os.path.join('pack', 'bin', 'pkg', 'tartube')
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
    'external',
    'ico',
    'large',
    'locale',
    'overlays',
    'small',
    'status',
    'stock',
    'thumbas',
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
    name = 'tartube',
    version = '2.4.260',
    description = 'GUI front-end for youtube-dl, yt-dlp and other compatible' \
    + ' video downloaders',
    long_description = long_description,
    long_description_content_type = 'text/plain',
    url = 'https://tartube.sourceforge.io',
    author = 'A S Lewis',
    author_email = 'aslewis@cpan.org',
#    license = license,
    license = """LGPLv2.1+""",
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Multimedia :: Video',
        'License :: OSI Approved' \
        + ' :: GNU Lesser General Public License v2 or later (LGPLv2+)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    keywords = 'tartube video download youtube',
    packages = setuptools.find_packages(
        exclude = ('docs', 'icons', 'nsis', 'tests'),
    ),
    include_package_data = True,
    python_requires = '>=3.0, <4',
    install_requires = [
        'feedparser',
#        'pgi',
        'pygobject',
        'matplotlib',
        'playsound',
        'requests',
    ],
    scripts = [script_exec],
    project_urls = {
        'Bug Reports': 'https://github.com/axcore/tartube/issues',
        'Source': 'https://github.com/axcore/tartube',
    },
    data_files = param_list,
)
