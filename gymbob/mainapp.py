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


"""Main application class."""


# Import Gtk modules
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, GdkPixbuf


# Import other modules
from gi.repository import Gio
import datetime
import json
import os
import playsound
import re
import subprocess
import sys
import threading
import time


# Import our modules
import editwin
import gymprog
import __main__
import mainwin


# Classes


class GymBobApp(Gtk.Application):

    """Main python class for the GymBob application."""


    def __init__(self, *args, **kwargs):

        super(GymBobApp, self).__init__(
            *args,
            application_id=None,
            flags=Gio.ApplicationFlags.FLAGS_NONE,
            **kwargs)

        # Instance variable (IV) list - class objects
        # -------------------------------------------
        # The main window object, set as soon as it's created
        self.main_win_obj = None


        # Instance variable (IV) list - other
        # -----------------------------------
        # Default window sizes (in pixels)
        self.main_win_width = 550
        self.main_win_height = 400
        # Default size of edit windows (in pixels)
        self.edit_win_width = 600
        self.edit_win_height = 400
        # Default size (in pixels) of space between various widgets
        self.default_spacing_size = 5

        # For quick lookup, the directory in which the 'gymbob' executable
        #   file is found, and its parent directory
        self.script_dir = sys.path[0]
        self.script_parent_dir = os.path.abspath(
            os.path.join(self.script_dir, os.pardir),
        )
        # The directory in which workout programmes can be stored (as .json
        #   files)
        self.data_dir = os.path.abspath(
            os.path.join(
                os.path.expanduser('~'),
                __main__.__packagename__ + '-data',
            ),
        )

        # List of sound files found in the ../sounds directory
        self.sound_list = []
        # So that a sound can be played from within its own thread, the name of
        #   the sound file to be played is stored here (temporarily) before
        #   self.play_sound() can be called
        self.sound_file = None

        # At all times (after initial setup), a GObject timer runs
        # The timer's ID
        self.script_timer_id = None
        # The timer interval time (in milliseconds)
        self.script_timer_time = 100

        # Flag set to True if the clock is running
        self.clock_running_flag = False
        # The time (matches time.time()) at which the user clicked the START
        #   button
        self.clock_start_time = 0
        # The time at which the STOP button was clicked. If the START button is
        #   subsequently clicked, the value of self.clock_start_time is
        #   adjusted
        self.clock_stop_time = 0

        # Dictionary of gymprog.GymProg objects, each one handling a single
        #   workout programme. Dictionary in the form
        #       prog_dict[unique_name] = GymProg object
        # ...where 'unique_name' is a string with a maximum length of 16
        self.prog_dict = {}
        # The current workout programme object
        self.current_prog_obj = None
        # Flag set to True when the clock is started (from 0), which starts the
        #   workout programme
        self.current_prog_started_flag = False
        # When the clock is started (from 0), the contents of the workout
        #   programme is copied into this IV
        self.current_prog_msg_group_list = []
        # The time (matches the clock time, not time.time()) at which the first
        #   message in self.current_msg_group_list should be displayed. As soon
        #   as the message is displayed, it is removed from the list
        self.current_prog_next_update_time = None

        # Flag set to True if sound should has been muted
        self.mute_sound_flag = False


    def do_startup(self):

        """Gio.Application standard function."""

        Gtk.Application.do_startup(self)

        # Menu actions
        # ------------

        # 'GymBob' column
        quit_menu_action = Gio.SimpleAction.new('quit_menu', None)
        quit_menu_action.connect('activate', self.on_menu_quit)
        self.add_action(quit_menu_action)

        # 'Programmes' column
        new_prog_menu_action = Gio.SimpleAction.new('new_prog_menu', None)
        new_prog_menu_action.connect('activate', self.on_menu_new_prog)
        self.add_action(new_prog_menu_action)

        switch_prog_menu_action = Gio.SimpleAction.new(
            'switch_prog_menu',
            None,
        )
        switch_prog_menu_action.connect('activate', self.on_menu_switch_prog)
        self.add_action(switch_prog_menu_action)

        edit_prog_menu_action = Gio.SimpleAction.new('edit_prog_menu', None)
        edit_prog_menu_action.connect('activate', self.on_menu_edit_prog)
        self.add_action(edit_prog_menu_action)

        delete_prog_menu_action = Gio.SimpleAction.new(
            'delete_prog_menu',
            None,
        )
        delete_prog_menu_action.connect('activate', self.on_menu_delete_prog)
        self.add_action(delete_prog_menu_action)

        # 'Help' column
        about_menu_action = Gio.SimpleAction.new('about_menu', None)
        about_menu_action.connect('activate', self.on_menu_about)
        self.add_action(about_menu_action)

        go_website_menu_action = Gio.SimpleAction.new('go_website_menu', None)
        go_website_menu_action.connect('activate', self.on_menu_go_website)
        self.add_action(go_website_menu_action)

        # Button actions
        # --------------

        start_button_action = Gio.SimpleAction.new('start_button', None)
        start_button_action.connect('activate', self.on_button_start)
        self.add_action(start_button_action)

        stop_button_action = Gio.SimpleAction.new('stop_button', None)
        stop_button_action.connect('activate', self.on_button_stop)
        self.add_action(stop_button_action)

        reset_button_action = Gio.SimpleAction.new('reset_button', None)
        reset_button_action.connect('activate', self.on_button_reset)
        self.add_action(reset_button_action)


    def do_activate(self):

        """Gio.Application standard function."""

        self.start()


    def do_shutdown(self):

        """Gio.Application standard function."""

        # Stop immediately
        Gtk.Application.do_shutdown(self)


    # Public class methods


    def start(self):

        """Called by self.do_activate().

        Performs general initialisation.
        """

        # Create the main window and make it visible
        self.main_win_obj = mainwin.MainWin(self)
        self.main_win_obj.show_all()

        # Start the GObject timer, which runs continuously, even when the
        #   visible clock/stopwatch is not running
        self.script_timer_id = GObject.timeout_add(
            self.script_timer_time,
            self.script_timer_callback,
        )

        # Get a list of available sound files, and sort alphabetically
        sound_dir = os.path.abspath(
            os.path.join(self.script_parent_dir, 'sounds'),
        )

        for (dirpath, dir_list, file_list) in os.walk(sound_dir):
            for filename in file_list:
                if filename != 'COPYING':
                    self.sound_list.append(filename)

        self.sound_list.sort()

        # Create the data directory (in which workout programmes are stored as
        #   .json files), if it doesn't already exist
        if not os.path.isdir(self.data_dir):
            os.makedirs(self.data_dir)

        # Load any workout programmes found in the data directory
        for (dirpath, dir_list, file_list) in os.walk(self.data_dir):

            # The first file (alphabetically) is the new current workout
            #   programme
            file_list.sort()
            for filename in file_list:
                if re.search('\.json$', filename):
                    self.load_prog(filename)


    def stop(self):

        """Called by self.on_menu_quit().

        Performs a clean shutdown.
        """

        # I'm outta here!
        self.quit()


    def save_prog(self, prog_obj):

        """Called by self.on_menu_new_prog() and
        editwin.ProgEditWin.apply_changes().

        Saves the specified workout programme as .json file.

        Args:

            prog_obj (gymprog.GymProg): The workout programme to save

        """

        # Prepare the file's data
        utc = datetime.datetime.utcfromtimestamp(time.time())
        file_path = os.path.abspath(
            os.path.join(self.data_dir, prog_obj.name + '.json'),
        )

        json_dict = {
            # Metadata
            'script_name': __main__.__packagename__,
            'script_version': __main__.__version__,
            'save_date': str(utc.strftime('%d %b %Y')),
            'save_time': str(utc.strftime('%H:%M:%S')),
            # Data
            'prog_name': prog_obj.name,
            'prog_msg_group_list': prog_obj.msg_group_list,
        }

        # Try to save the file
        try:
            with open(file_path, 'w') as outfile:
                json.dump(json_dict, outfile, indent=4)

        except:

            # Save failed
            msg_dialogue_win = Gtk.MessageDialog(
                self.main_win_obj,
                0,
                Gtk.MessageType.ERROR,
                Gtk.ButtonsType.OK,
                'Failed to save the \'' + prog_obj.name + '\' programme',
            )
            msg_dialogue_win.run()
            msg_dialogue_win.destroy()


    def load_prog(self, filename):

        """Called by self.start().

        Loads the named workout programme (a .json file).

        Args:

            filename (str): The name of the workout programme to load, matching
                a key in self.prog_dict, and the name of a file in the data
                directory

        """

        # Get the full filepath for the specified file
        filepath = os.path.abspath(
            os.path.join(self.data_dir, filename),
        )

        # Try to load the file, ignoring any failures
        try:
            with open(filepath) as infile:
                json_dict = json.load(infile)

        except:
            return

        # Do some basic checks on the loaded data
        if not json_dict \
        or not 'script_name' in json_dict \
        or not 'script_version' in json_dict \
        or not 'save_date' in json_dict \
        or not 'save_time' in json_dict \
        or not 'prog_name' in json_dict \
        or not 'prog_msg_group_list' in json_dict \
        or json_dict['script_name'] != __main__.__packagename__:
            return

        # Ignore duplicate names (the file name and programme name should be
        #   the same, but perhaps the user has been editing it by hand...)
        if json_dict['prog_name'] in self.prog_dict:
            return

        # File loaded; create a gymprog.GymProg object for it
        prog_obj = gymprog.GymProg(
            json_dict['prog_name'],
            json_dict['prog_msg_group_list'],
        )

        self.prog_dict[json_dict['prog_name']] = prog_obj

        # The first file loaded is the new current programme. (Files are loaded
        #   in alphabetical order)
        if not self.current_prog_obj:
            self.current_prog_obj = prog_obj
            self.main_win_obj.update_win_title(prog_obj.name)
            self.main_win_obj.update_buttons_on_current_prog()
            self.main_win_obj.update_menu_items_on_prog()


    def delete_prog(self, prog_obj):

        """Called by self.on_menu_delete_prog().

        Deletes the .json file corresponding to the specified workout
        programme.

        Args:

            prog_obj (gymprog.GymProg): The workout programme to delete

        """

        file_path = os.path.abspath(
            os.path.join(self.data_dir, prog_obj.name + '.json'),
        )

        # Delete the file
        try:
            os.remove(file_path)

        except:

            # Deletion failed
            msg_dialogue_win = Gtk.MessageDialog(
                self.main_win_obj,
                0,
                Gtk.MessageType.ERROR,
                Gtk.ButtonsType.OK,
                'Failed to delete the \'' + prog_obj.name + '\' programme',
            )
            msg_dialogue_win.run()
            msg_dialogue_win.destroy()


    def play_sound(self):

        """Called periodically by self.script_timer_callback().

        If a sound file has been set, play it (unless sound is muted).
        """

        sound_file = self.sound_file
        self.sound_file = None

        # (The value might be None or an empty string)
        if not self.mute_sound_flag and sound_file:

            path = os.path.abspath(
                os.path.join(self.script_parent_dir, 'sounds', sound_file),
            )

            if os.path.isfile(path):

                playsound.playsound(path)


    # Callback class methods


    # (Timers)


    def script_timer_callback(self):

        """Called by GObject timer created by self.start(), ten times a second.

        Returns:

            1 to keep the timer going, or None to halt it

        """

        # (Use the same time value to update all main window widgets)
        current_time = time.time()

        # If the programme is running...
        if self.clock_running_flag:

            # Update the contents of textviews in the main window
            # (De)sensitise menu items and/or buttons
            clock_time = current_time - self.clock_start_time
            self.main_win_obj.update_clock_textview(clock_time)

            if self.current_prog_next_update_time is not None \
            and self.current_prog_next_update_time <= clock_time \
            and self.current_prog_msg_group_list:

                mini_list = self.current_prog_msg_group_list.pop(0)
                self.main_win_obj.update_this_info_textview(str(mini_list[1]))
                if mini_list[2]:
                    self.sound_file = mini_list[2]

                if self.current_prog_msg_group_list:

                    # Programme not finished; show the next message as well (in
                    #   a different colour)
                    next_mini_list = self.current_prog_msg_group_list[0]
                    self.current_prog_next_update_time += next_mini_list[0]
                    self.main_win_obj.update_next_info_textview(
                        next_mini_list[1],
                    )

                else:

                    # Programme finished
                    self.current_prog_next_update_time = None
                    self.main_win_obj.update_countdown_textview('')
                    self.main_win_obj.update_next_info_textview('')

            if self.current_prog_next_update_time is not None:

                next_time = self.current_prog_next_update_time - clock_time
                self.main_win_obj.update_countdown_textview(next_time)

        # Play a sound file, if required. In case of long sounds, perform this
        #   action inside its own thread
        if self.sound_file is not None:
            thread = threading.Thread(target=self.play_sound)
            thread.start()

        # Return 1 to keep the timer going
        return 1


    # (Widgets)


    def on_button_start(self, action, par):

        """Called from a callback in self.do_startup().

        Starts the clock.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        # Update IVs
        self.clock_running_flag = True
        if not self.clock_start_time:
            self.clock_start_time = time.time()
        else:
            self.clock_start_time += (time.time() - self.clock_stop_time)

        # (De)sensitise buttons
        self.main_win_obj.update_buttons_on_start()

        if not self.current_prog_started_flag:

            # Clock is at 0; start the workout programme
            self.current_prog_started_flag = True
            self.current_prog_msg_group_list \
            = self.current_prog_obj.msg_group_list.copy()

            # (The workout programme might be empty, so we have to check for
            #   that)
            if self.current_prog_msg_group_list:

                # mini_list is in the form
                #   (time_in_seconds, message, optional_sound_file)
                mini_list = self.current_prog_msg_group_list[0]
                self.current_prog_next_update_time = mini_list[0]

                if len(self.current_prog_msg_group_list) > 1:

                    # Programme not finished; show the next message as well (in
                    #   a different colour)
                    next_mini_list = self.current_prog_msg_group_list[0]
                    self.main_win_obj.update_next_info_textview(
                        next_mini_list[1],
                    )

        # (De)sensitise menu items
        self.main_win_obj.update_menu_items_on_prog()


    def on_button_stop(self, action, par):

        """Called from a callback in self.do_startup().

        Stops the clock.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        # Update IVs
        self.clock_running_flag = False
        self.clock_stop_time = time.time()

        # (De)sensitise buttons
        self.main_win_obj.update_buttons_on_stop()

        # (De)sensitise menu items
        self.main_win_obj.update_menu_items_on_prog()


    def on_button_reset(self, action, par):

        """Called from a callback in self.do_startup().

        Resets the clock.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        # Update IVs
        self.clock_running_flag = False
        self.clock_start_time = 0
        self.clock_stop_time = 0

        self.current_prog_started_flag = False
        self.current_prog_msg_group_list = []
        self.current_prog_next_update_time = None

        # Reset textviews
        self.main_win_obj.update_clock_textview('')
        self.main_win_obj.update_countdown_textview('')
        self.main_win_obj.update_this_info_textview('')
        self.main_win_obj.update_next_info_textview('')

        # (De)sensitise buttons
        self.main_win_obj.update_buttons_on_reset()

        # (De)sensitise menu items
        self.main_win_obj.update_menu_items_on_prog()


    def on_menu_about(self, action, par):

        """Called from a callback in self.do_startup().

        Show a standard 'about' dialogue window.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        dialogue_win = Gtk.AboutDialog()
        dialogue_win.set_transient_for(self.main_win_obj)
        dialogue_win.set_destroy_with_parent(True)

        dialogue_win.set_program_name(__main__.__packagename__.title())
        dialogue_win.set_version('v' + __main__.__version__)
        dialogue_win.set_copyright(__main__.__copyright__)
        dialogue_win.set_license(__main__.__license__)
        dialogue_win.set_website(__main__.__website__)
        dialogue_win.set_website_label(
            __main__.__prettyname__ + ' website'
        )
        dialogue_win.set_comments(__main__.__description__)
        dialogue_win.set_logo(
            self.main_win_obj.icon_pixbuf_dict['icon_64'],
        )
        dialogue_win.set_authors(__main__.__author_list__)
        dialogue_win.set_title('')
        dialogue_win.connect('response', self.on_menu_about_close)

        dialogue_win.show()


    def on_menu_about_close(self, action, par):

        """Called from a callback in self.on_menu_about().

        Close the 'about' dialogue window.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        action.destroy()


    def on_menu_delete_prog(self, action, par):

        """Called from a callback in self.do_startup().

        Prompts the user to delete a workout programme.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        # Open a dialogue window
        dialogue_win = mainwin.DeleteProgDialogue(self.main_win_obj)
        response = dialogue_win.run()

        # Retrieve user choices from the dialogue window...
        prog_name = dialogue_win.prog_name
        # ...before destroying the dialogue window
        dialogue_win.destroy()

        if response == Gtk.ResponseType.OK:

            # Remove the workout programme from the registry
            del self.prog_dict[prog_name]

            # If it's the current programme, update some things
            if self.current_prog_obj is not None \
            and self.current_prog_obj.name == prog_name:

                # Reset the window title
                self.main_win_obj.update_win_title()

                # Delete the corresponding file
                self.delete_prog(self.current_prog_obj)
                self.current_prog_obj = None

                # Artificially click the RESET button to reset the clock and
                #   empty the main window of text
                self.main_win_obj.reset_button.clicked()

                # (De)sensitise buttons
                self.main_win_obj.update_buttons_on_current_prog()

            # Desensitise menu items, if there are no workout programmes left
            self.main_win_obj.update_menu_items_on_prog()


    def on_menu_edit_prog(self, action, par):

        """Called from a callback in self.do_startup().

        Prompts the user to edit the current workout programme.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        # Open the edit window immediately
        editwin.ProgEditWin(self, self.current_prog_obj)


    def on_menu_go_website(self, action, par):

        """Called from a callback in self.do_startup().

        Opens the GymBob website.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        uri = __main__.__website__

        # Open the GymBob home page in the user's default browser
        if sys.platform == "win32":
            os.startfile(uri)
        else:
            opener ="open" if sys.platform == "darwin" else "xdg-open"
            subprocess.call([opener, uri])


    def on_menu_new_prog(self, action, par):

        """Called from a callback in self.do_startup().

        Prompts the user for the name of a new workout programme.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        # Open a dialogue window
        dialogue_win = mainwin.NewProgDialogue(self.main_win_obj)
        response = dialogue_win.run()

        # Retrieve user choices from the dialogue window...
        prog_name = dialogue_win.entry.get_text()
        # ...before destroying the dialogue window
        dialogue_win.destroy()

        if response != Gtk.ResponseType.OK:
            return

        if prog_name in self.prog_dict:

            # Duplicate programme names are not allowed
            msg_dialogue_win = Gtk.MessageDialog(
                self.main_win_obj,
                0,
                Gtk.MessageType.ERROR,
                Gtk.ButtonsType.OK,
                'A programme called \'' + prog_name + '\' already exists!',
            )
            msg_dialogue_win.run()
            msg_dialogue_win.destroy()
            return

        # Create the new workout programme
        prog_obj = gymprog.GymProg(prog_name)
        self.prog_dict[prog_name] = prog_obj
        # Set it as the current programme
        self.current_prog_obj = prog_obj
        # Save the empty programme, creating a .json file
        self.save_prog(prog_obj)

        # Update the main window title to show the current programme
        self.main_win_obj.update_win_title(prog_obj.name)
        # (De)sensitise menu items and buttons
        self.main_win_obj.update_buttons_on_current_prog()
        self.main_win_obj.update_menu_items_on_prog()

        # Open an edit window for the new programme immediately
        editwin.ProgEditWin(self, prog_obj)


    def on_menu_switch_prog(self, action, par):

        """Called from a callback in self.do_startup().

        Prompts the user with a list of workout programmes from which to
        select.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        # Open a dialogue window
        dialogue_win = mainwin.SwitchProgDialogue(self.main_win_obj)
        response = dialogue_win.run()

        # Retrieve user choices from the dialogue window...
        prog_name = dialogue_win.prog_name
        # ...before destroying the dialogue window
        dialogue_win.destroy()

        if response == Gtk.ResponseType.OK:

            # Set the current programme
            self.current_prog_obj = self.prog_dict[prog_name]

            # (De)sensitise menu items and buttons
            self.main_win_obj.update_buttons_on_current_prog()
            self.main_win_obj.update_menu_items_on_prog()

            # Artificially click the RESET button to reset the clock and empty
            #   the main window of text
            self.main_win_obj.reset_button.clicked()

            # Update the main window title to show the current programme
            self.main_win_obj.update_win_title(self.current_prog_obj.name)


    def on_menu_quit(self, action, par):

        """Called from a callback in self.do_startup().

        Terminates the GymBob app.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        # Terminate the script
        self.stop()


    # Set accessors


    def set_mute_sound_flag(self, flag):

        if not flag:
            self.mute_sound_flag = False
        else:
            self.mute_sound_flag = True
