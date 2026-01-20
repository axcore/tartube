#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2026 A S Lewis
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


"""GUI helper functions that do not require Gtk imports."""


def nudge_paned_position(paned, posn):

    """Nudge a Gtk.Paned position to trigger a redraw, then restore it.

    Args:

        paned (Gtk.Paned): The paned widget to adjust.

        posn (int): The current position to restore after nudging.

    """

    paned.set_position(posn + 1)
    paned.set_position(posn)
