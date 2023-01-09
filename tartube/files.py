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


"""File manager classes."""


# Import Gtk modules
#   ...


# Import other modules
from gi.repository import GdkPixbuf
import json
import os
import threading


# Import our modules
import utils


# Classes


class FileManager(threading.Thread):

    """Called by mainapp.TartubeApp.__init__().

    Python class to manage loading of thumbnail, icon and JSON files safely
    (i.e. without causing a Gtk crash).
    """


    # Standard class methods


    def __init__(self):

        super(FileManager, self).__init__()


    # Public class methods


    def load_json(self, full_path):

        """Can be called by anything.

        Given the full path to a JSON file, loads the file into a Python
        dictionary and returns the dictionary.

        Args:

            full_path (str): The full path to the JSON file

        Return values:

            The JSON data, converted to a Python dictionary (an empty
                dictionary if the file is missing or can't be loaded)

        """

        empty_dict = {}
        if not os.path.isfile(full_path):
            return empty_dict

        # RFC 7159: JSON should be represented by UTF-8
        with open(
            full_path,
            'r',
            encoding='UTF-8',
            errors='ignore',
        ) as json_file:

            try:
                json_dict = json.load(json_file)
                return json_dict

            except:
                return empty_dict


    def load_text(self, full_path):

        """Can be called by anything.

        Given the full path to a text file, loads it.

        Args:

            full_path (str): The full path to the text file

        Return values:

            The contents of the text file as a string, or or None if the file
                is missing or can't be loaded

        """

        if not os.path.isfile(full_path):
            return None

        with open(
            full_path,
            'r',
            encoding='UTF-8',
            errors='ignore',
        ) as text_file:

            try:
                text = text_file.read()
                return text

            except:
                return None


    def load_to_pixbuf(self, full_path, width=None, height=None):

        """Can be called by anything.

        Given the full path to an icon file, loads the icon into a pibxuf, and
        returns the pixbuf.

        Args:

            full_path (str): The full path to the icon file

            width, height (int or None): If both are specified, the icon is
                scaled to that size

        Return values:

            A GdkPixbuf (as a tuple), or None if the file is missing or can't
                be loaded

        """

        if not os.path.isfile(full_path):
            return None

        try:
            # (Returns a tuple)
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(full_path)
        except:
            return None

        if width is not None and height is not None:
            pixbuf = pixbuf.scale_simple(
                width,
                height,
                GdkPixbuf.InterpType.BILINEAR,
            )

        return pixbuf
