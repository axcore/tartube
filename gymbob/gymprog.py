#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 A S Lewis
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


"""Workout programme classes."""


# Import Gtk modules
# ...


# Import other modules
# ...


# Import our modules
# ...


# Classes


class GymProg(object):

    """Can be called by anything.

    Python class that handles a workout programme.

    Args:

        name (str): A unique programme name

        msg_group_list (list): List of messages to display in the main window,
            in the form described below

    """


    # Standard class methods


    def __init__(self, name, msg_group_list=[]):

        # IV list - other
        # ---------------
        # A unique programme name
        self.name = name

        # The programme is made up of a sequence of messages, displayed after
        #   fixed intervals
        # A message group is a list in the form [int, txt, txt]:
        #   int: Time in seconds between this message and the previous one
        #   txt: The message itself (or an empty string to overwrite the
        #       previous message, leaving no message visible)
        #   txt: Name of the sound file (.wav or .ogg) in the ../sounds
        #       folder to play when this message is displayed (or an empty
        #       string to play no sound)
        # The message groups are stored in this sequential list
        self.msg_group_list = msg_group_list

