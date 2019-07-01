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


"""Dialogue manager classes."""


# Import Gtk modules
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, GdkPixbuf


# Import other modules
import threading


# Import our modules
#   ...


# Classes


class DialogueManager(threading.Thread):

    """Called by mainapp.TartubeApp.start().

    Python class to manage message dialogue windows safely (i.e. without
    causing a Gtk crash).

    Args:

        app_obj: The mainapp.TartubeApp object

        main_win_obj (mainwin.MainWin): The main window

    """


    # Standard class methods


    def __init__(self, app_obj, main_win_obj):

        super(DialogueManager, self).__init__()


        # IV list - class objects
        # -----------------------
        # The mainapp.TartubeApp object
        self.app_obj = app_obj
        # The main window
        self.main_win_obj = main_win_obj


    # Public class methods


    def show_msg_dialogue(self, msg, msg_type, button_type,
    parent_win_obj=None, response_dict=None):

        """Can be called by anything.

        Creates a standard Gtk.MessageDialog window.

        Args:

            msg (string): The text to display in the dialogue window

            msg_type (string): The icon to display in the dialogue window:
                'info', 'warning', 'question', 'error'

            button_type (string): The buttons to use in the dialogue window:
                'ok', 'ok-cancel', 'yes-no'

            parent_win_obj (mainwin.MainWin, config.GenericConfigWin or None):
                The parent window for the dialogue window. If None, the main
                window is used as the parent window

            response_dict (dict or None): A dictionary specified if the calling
                code needs a response (e.g., needs to know whether the user
                clicked the 'yes' or 'no' button). If specified, the keys are
                0, 1 or more of the values 'ok', 'cancel', 'yes', 'no'. The
                corresponding values are the mainapp.TartubeApp function called
                if the user clicks that button. The dictionary can also contain
                the key 'data'. If it does, the corresponding value is passed
                to the mainapp.TartubeApp function as an argument

        """

        if parent_win_obj is None:
            parent_win_obj = self.main_win_obj

        dialogue_win = MessageDialogue(
            self,
            msg,
            msg_type,
            button_type,
            parent_win_obj,
            response_dict,
        )

        dialogue_win.create_dialogue()


class MessageDialogue(Gtk.MessageDialog):

    """Called by dialogue.DialogueManager.show_msg_dialogue().

    Creates a standard Gtk.MessageDialog window, and optionally returns a
    response.

    Args:

        msg (string): The text to display in the dialogue window

        msg_type (string): The icon to display in the dialogue window: 'info',
            'warning', 'question', 'error'

        button_type (string): The buttons to use in the dialogue window: 'ok',
            'ok-cancel', 'yes-no'

        parent_win_obj (mainwin.MainWin, config.GenericConfigWin): The parent
            window for the dialogue window

        response_dict (dict or None): A dictionary specified if the calling
            code needs a response (e.g., needs to know whether the user clicked
            the 'yes' or 'no' button). If specified, the keys are 0, 1 or more
            of the values 'ok', 'cancel', 'yes', 'no'. The corresponding values
            are the mainapp.TartubeApp function called if the user clicks that
            button. The dictionary can also contain the key 'data'. If it does,
            the corresponding value is passed to the mainapp.TartubeApp
            function as an argument

    """


    # Standard class methods


    def __init__(self, parent, msg, msg_type, button_type, parent_win_obj,
    response_dict):

        # Prepare arguments
        if msg_type == 'warning':
            msg_type = Gtk.MessageType.WARNING
        elif msg_type == 'question':
            msg_type = Gtk.MessageType.QUESTION
        elif msg_type == 'error':
            msg_type = Gtk.MessageType.ERROR
        else:
            msg_type = Gtk.MessageType.INFO

        if button_type == 'ok-cancel':
            button_type = Gtk.ButtonsType.OK_CANCEL
            default_response = Gtk.ResponseType.OK
        elif button_type == 'yes-no':
            button_type = Gtk.ButtonsType.YES_NO
            default_response = Gtk.ResponseType.YES
        else:
            button_type = Gtk.ButtonsType.OK
            default_response = Gtk.ResponseType.OK

        # Set up the dialogue window
        Gtk.MessageDialog.__init__(
            self,
            parent_win_obj,
            Gtk.DialogFlags.DESTROY_WITH_PARENT,
            msg_type,
            button_type,
            msg,
        )

        self.set_default_response(default_response)
        self.connect(
            'response',
            self.on_clicked,
            parent.app_obj,
            response_dict,
        )


    # Public class methods


    def on_clicked(self, widget, response, app_obj, response_dict):

        """Called from a callback in self.__init__().

        Destroy the dialogue window. If the calling code requires a response,
        call the specified function in mainapp.TartubeApp.

        Args:

            widget (Gtk.MessageDialog): This dialogue window

            response (int): The response, matching a Gtk.ResponseType

            app_obj: The mainapp.TartubeApp object

            response_dict (dict or None): A dictionary specified if the calling
                code needs a response (e.g., needs to know whether the user
                clicked the 'yes' or 'no' button). If specified, the keys are
                0, 1 or more of the values 'ok', 'cancel', 'yes', 'no'. The
                corresponding values are the mainapp.TartubeApp function called
                if the user clicks that button. The dictionary can also contain
                the key 'data'. If it does, the corresponding value is passed
                to the mainapp.TartubeApp function as an argument

        """

        # Destroy the window
        self.destroy()

        # If the calling code requires a response, provide it
        if response_dict is not None:

            func = None
            if response == Gtk.ResponseType.OK and 'ok' in response_dict:
                func = response_dict['ok']
            elif response == Gtk.ResponseType.CANCEL \
            and 'cancel' in response_dict:
                func = response_dict['cancel']
            elif response == Gtk.ResponseType.YES and 'yes' in response_dict:
                func = response_dict['yes']
            elif response == Gtk.ResponseType.NO and 'no' in response_dict:
                func = response_dict['no']

            if func is not None:
                # Call the specified mainapp.TartubeApp function
                method = getattr(app_obj, func)

                # If the dictionary contains a key called 'data', use its
                #   corresponding value as an argument in the call
                if 'data' in response_dict:
                    method(response_dict['data'])
                else:
                    method()


    def create_dialogue(self):

        """Called by dialogue.DialogueManager.show_msg_dialogue().

        Creating the message dialogue window using a Glib timeout keeps this
        code thread-safe.
        """

        GObject.timeout_add(0, self.show_dialogue)


    def show_dialogue(self):

        """Called by the timer created in self.create_dialogue().

        Creating the message dialogue window using a Glib timeout keeps this
        code thread-safe.
        """

        self.show_all()
        return False
