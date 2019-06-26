#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 A S Lewis
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
import setuptools


# Import documents
#with open('README.rst', 'r') as f:
#    long_description = f.read()
#
#with open('LICENSE') as f:
#    license = f.read()


# Setup
setuptools.setup(
    name='tartube',
    version='0.3.003',
    description='GUI front-end for youtube-dl',
#    long_description=long_description,
    long_description="""Tartube is a GUI front-end for youtube-dl, partly based
        on youtube-dl-gui and written in Python 3 / Gtk 3""",
    long_description_content_type='text/markdown',
    author='A S Lewis',
    author_email='aslewis@cpan.org',
    url='https://github.com/axcore/tartube',
#    license=license,
    license="""GPL3+""",
    packages=setuptools.find_packages()
)
