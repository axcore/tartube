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


"""Main window class."""


# Import Gtk modules
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Gdk, GdkPixbuf


# Import other modules
from gi.repository import Gio
import math
import os


# Import our modules
import __main__
import mainapp


# Classes


class MainWin(Gtk.ApplicationWindow):

    """Called by mainapp.GymBobApp.start().

    Python class that handles the main window.

    Args:

        app_obj (mainapp.TartubeApp): The main application object

    """


    def __init__(self, app_obj):

        super(MainWin, self).__init__(
            title=__main__.__prettyname__,
            application=app_obj
        )

        # IV list - class objects
        # -----------------------
        # The main application
        self.app_obj = app_obj


        # IV list - Gtk widgets
        # ---------------------
        # (from self.setup_grid)
        self.grid = None                        # Gtk.Grid
        # (from self.setup_menubar)
        self.menubar = None                     # Gtk.MenuBar
        self.new_prog_menu_item = None          # Gtk.MenuItem
        self.switch_prog_menu_item = None       # Gtk.MenuItem
        self.edit_prog_menu_item = None         # Gtk.MenuItem
        self.delete_prog_menu_item = None       # Gtk.MenuItem
        # (from self.setup_win)
        self.clock_textview = None              # Gtk.TextView
        self.countdown_textview = None          # Gtk.TextView
        self.this_info_textview = None          # Gtk.TextView
        self.next_info_textview = None          # Gtk.TextView
        self.start_button = None                # Gtk.Button
        self.pause_button = None                # Gtk.Button
        self.stop_button = None                 # Gtk.Button
        self.reset_button = None                # Gtk.Button


        # IV list - other
        # ---------------
        # Colours to use in the upper/lower textviews, and the font size (in
        #   points, default value is 10)
        self.clock_bg_colour = '#000000'
        self.clock_text_colour = '#FFFFFF'
        self.clock_font_size = 40

        self.countdown_bg_colour = '#000000'
        self.countdown_text_colour = '#FF0000'
        self.countdown_font_size = 40

        self.this_info_bg_colour = '#000000'
        self.this_info_text_colour = '#FFFFFF'
        self.this_info_font_size = 30

        self.next_info_bg_colour = '#000000'
        self.next_info_text_colour = '#FF0000'
        self.next_info_font_size = 30

        # Gymbob icon files are loaded into pixbufs, ready for use. Dictionary
        #   in the form:
        #       key - a string like 'icon_512'
        #       value - a Gdk.Pixbuf
        self.icon_pixbuf_dict = {}
        # The same list of pixbufs in sequential order
        self.icon_pixbuf_list = []

        # List of edit windows (editwin.ProgEditWin objects) that are currently
        #   open. The clock can't be started if any edit windows are open
        self.edit_win_list = []

        # Code
        # ----

        # Set up icon pixbufs
        self.setup_icons()
        # Set up the main window
        self.setup_win()


    # Public class methods


    def setup_icons(self):

        """Called by self.__init__().

        Sets up pixbufs for GymBob icons.
        """

        # The default location for icons is ../icons
        # When installed via PyPI, the icons are moved to ../gymbob/icons
        # When installed via a Debian/RPM package, the icons are moved to
        #   /usr/share/gymbob/icons
        icon_dir_list = []
        icon_dir_list.append(
            os.path.abspath(
                os.path.join(self.app_obj.script_parent_dir, 'icons'),
            ),
        )

        icon_dir_list.append(
            os.path.abspath(
                os.path.join(
                    os.path.dirname(os.path.realpath(__file__)),
                    'icons',
                ),
            ),
        )

        icon_dir_list.append(
            os.path.join(
                '/', 'usr', 'share', __main__.__packagename__, 'icons',
            )
        )

        self.icon_pixbuf_list = []
        for icon_dir_path in icon_dir_list:
            if os.path.isdir(icon_dir_path):

                for size in [16, 24, 32, 48, 64, 128, 256, 512]:

                    path = os.path.abspath(
                        os.path.join(
                            icon_dir_path,
                            'win',
                            __main__.__packagename__ + '_icon_' + str(size) \
                            + '.png',
                        ),
                    )

                    pixbuf = GdkPixbuf.Pixbuf.new_from_file(path)

                    self.icon_pixbuf_list.append(pixbuf)
                    self.icon_pixbuf_dict['icon_' + str(size)] = pixbuf

        # Pass the list of pixbufs to Gtk
        self.set_icon_list(self.icon_pixbuf_list)


    def setup_win(self):

        """Called by self.__init__().

        Sets up the main window, calling various function to create its
        widgets.
        """

        spacing = self.app_obj.default_spacing_size

        # Set the default window size
        self.set_default_size(
            self.app_obj.main_win_width,
            self.app_obj.main_win_height,
        )

        # Create main window widgets
        self.grid = Gtk.Grid()
        self.add(self.grid)

        self.setup_menubar()

        self.clock_textview = self.setup_textview(
            1,
            self.clock_bg_colour,
            self.clock_text_colour,
            self.clock_font_size,
            0, 1, 1, 1,
        )

        self.countdown_textview = self.setup_textview(
            2,
            self.countdown_bg_colour,
            self.countdown_text_colour,
            self.countdown_font_size,
            1, 1, 1, 1,
        )

        self.this_info_textview = self.setup_textview(
            3,
            self.this_info_bg_colour,
            self.this_info_text_colour,
            self.this_info_font_size,
            0, 2, 2, 1,
        )

        self.next_info_textview = self.setup_textview(
            4,
            self.next_info_bg_colour,
            self.next_info_text_colour,
            self.next_info_font_size,
            0, 3, 2, 1,
        )

        self.setup_dummy_textview()

        # Separator
        self.grid.attach(Gtk.Separator(), 0, 4, 2, 1)

        hbox = Gtk.HBox()
        self.grid.attach(hbox, 0, 5, 2, 1)
        hbox.set_border_width(spacing * 2)
        hbox.set_vexpand(True)

        self.start_button = Gtk.Button('START')
        hbox.pack_start(self.start_button, True, True, spacing)
        self.start_button.set_action_name('app.start_button')
        # (These buttons are desensitised until a programme is loaded/created)
        self.start_button.set_sensitive(False)

        self.stop_button = Gtk.Button('STOP')
        hbox.pack_start(self.stop_button, True, True, spacing)
        self.stop_button.set_sensitive(False)
        self.stop_button.set_action_name('app.stop_button')
        self.stop_button.set_sensitive(False)

        self.reset_button = Gtk.Button('RESET')
        hbox.pack_start(self.reset_button, True, True, spacing)
        self.reset_button.set_action_name('app.reset_button')
        self.reset_button.set_sensitive(False)


    def setup_menubar(self):

        """Called by self.setup_win().

        Sets up a Gtk.Menu at the top of the main window.
        """

        self.menubar = Gtk.MenuBar()
        self.grid.attach(self.menubar, 0, 0, 2, 1)

        # GymBob column
        file_menu_column = Gtk.MenuItem.new_with_mnemonic(
            '_' + __main__.__prettyname__,
        )
        self.menubar.add(file_menu_column)

        file_sub_menu = Gtk.Menu()
        file_menu_column.set_submenu(file_sub_menu)

        mute_sound_menu_item = Gtk.CheckMenuItem.new_with_mnemonic(
            '_Mute sound',
        )
        mute_sound_menu_item.set_active(self.app_obj.mute_sound_flag)
        mute_sound_menu_item.connect(
            'activate',
            self.on_menu_mute_sound,
        )
        file_sub_menu.append(mute_sound_menu_item)

        # Separator
        file_sub_menu.append(Gtk.SeparatorMenuItem())

        quit_menu_item = Gtk.MenuItem.new_with_mnemonic('_Quit')
        file_sub_menu.append(quit_menu_item)
        quit_menu_item.set_action_name('app.quit_menu')

        # Programmes column
        edit_menu_column = Gtk.MenuItem.new_with_mnemonic('_Programmes')
        self.menubar.add(edit_menu_column)

        edit_sub_menu = Gtk.Menu()
        edit_menu_column.set_submenu(edit_sub_menu)

        self.new_prog_menu_item = Gtk.MenuItem.new_with_mnemonic(
            '_New programme...',
        )
        edit_sub_menu.append(self.new_prog_menu_item)
        self.new_prog_menu_item.set_action_name('app.new_prog_menu')

        self.switch_prog_menu_item = Gtk.MenuItem.new_with_mnemonic(
            '_Switch programme...',
        )
        edit_sub_menu.append(self.switch_prog_menu_item)
        self.switch_prog_menu_item.set_action_name('app.switch_prog_menu')

        self.edit_prog_menu_item = Gtk.MenuItem.new_with_mnemonic(
            '_Edit current programme...',
        )
        edit_sub_menu.append(self.edit_prog_menu_item)
        self.edit_prog_menu_item.set_action_name('app.edit_prog_menu')

        # Separator
        edit_sub_menu.append(Gtk.SeparatorMenuItem())

        self.delete_prog_menu_item = Gtk.MenuItem.new_with_mnemonic(
            '_Delete programme...',
        )
        edit_sub_menu.append(self.delete_prog_menu_item)
        self.delete_prog_menu_item.set_action_name('app.delete_prog_menu')

        # Help column
        help_menu_column = Gtk.MenuItem.new_with_mnemonic('_Help')
        self.menubar.add(help_menu_column)

        help_sub_menu = Gtk.Menu()
        help_menu_column.set_submenu(help_sub_menu)

        about_menu_item = Gtk.MenuItem.new_with_mnemonic('_About...')
        help_sub_menu.append(about_menu_item)
        about_menu_item.set_action_name('app.about_menu')

        go_website_menu_item = Gtk.MenuItem.new_with_mnemonic('Go to _website')
        help_sub_menu.append(go_website_menu_item)
        go_website_menu_item.set_action_name('app.go_website_menu')

        # (Some menu items are desensitised until a programme is loaded/
        #   created)
        self.edit_prog_menu_item.set_sensitive(False)
        self.switch_prog_menu_item.set_sensitive(False)
        self.delete_prog_menu_item.set_sensitive(False)


    def setup_textview(self, widget_id, bg_colour, text_colour, font_size, \
    x_pos, y_pos, width, height):

        """Called by self.setup_win().

        Creates one of the main window textviews (there are four in all).

        Args:

            widget_id (int): Unique number for this textview (1-4)

            bg_colour, text_colour (str): The colours to use in this textview
                (e.g. '#FFFFFF')

            font_size (int): The font size (in points, e.g. 10)

            x_pos, y_pos, width, height (int): Coordinates on the Gtk3.Grid

        Return values:

            The Gtk.TextView created

        """

        # Add a textview to the grid, using a css style sheet to provide (for
        #   example) monospaced white text on a black background
        scrolled = Gtk.ScrolledWindow()
        self.grid.attach(scrolled, x_pos, y_pos, width, height)
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        frame = Gtk.Frame()
        scrolled.add_with_viewport(frame)

        style_provider = self.set_textview_css(
            '#css_text_id_' + str(widget_id) \
            + ', textview text {\n' \
            + '   background-color: ' + bg_colour + ';\n' \
            + '   color: ' + text_colour + ';\n' \
            + '}\n' \
            + '#css_label_id_' + str(widget_id) \
            + ', textview {\n' \
            + '   font-family: monospace, monospace;\n' \
            + '   font-size: ' + str(font_size) + 'pt;\n' \
            + '}'
        )

        textview = Gtk.TextView()
        frame.add(textview)
        textview.set_wrap_mode(Gtk.WrapMode.WORD)
        textview.set_editable(False)
        textview.set_cursor_visible(False)
        textview.set_hexpand(True)
        textview.set_vexpand(True)

        context = textview.get_style_context()
        context.add_provider(style_provider, 600)

        return textview


    def setup_dummy_textview(self):

        """Called by self.setup_win(), immediately after calls to
        self.setup_textview().

        Resets css properties for the next Gtk.TextView created (presumably by
        another application), so it uses the default style, not the css style
        specified in the calls to self.setup_textview().
        """

        # Create a dummy textview that's not visible in the main window
        textview = Gtk.TextView()
        style_provider = self.set_textview_css(
            '#css_text_id_default, textview text {\n' \
            + '   background-color: unset;\n' \
            + '   color: unset;\n' \
            + '}\n' \
            + '#css_label_id_default, textview {\n' \
            + '   font-family: unset;\n' \
            + '   font-size: unset;\n' \
            + '}'
        )

        context = textview.get_style_context()
        context.add_provider(style_provider, 600)


    def set_textview_css(self, css_string):

        """Called by self.setup_upper_textview() and .setup_lower_textview().

        Applies a CSS style to the current screen, which is used for the
        Gtk.TextView that has just been created.

        Called a third time to create a dummy textview with default properties.

        Args:

            css_string (str): The CSS style to apply

        Returns:

            The Gtk.CssProvider created

        """

        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(bytes(css_string.encode()))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        return style_provider


    # (Update widgets)


    def update_win_title(self, prog_name=None):

        """Called by various functions.

        Changes the title of the main window. If there is a current programme,
        display its name alongside the name of the script.

        Args:

            prog_name (str): The name of a workout programme, matching a key
                in self.app_obj.prog_dict

        """

        if prog_name is not None:
            self.set_title(__main__.__prettyname__ + ' [' + prog_name + ']')
        else:
            self.set_title(__main__.__prettyname__)


    def update_clock_textview(self, time):

        """Called by various functions.

        Updates the main window textview showing the current time.

        Args:

            time (int): The current time (since the programme begun) in seconds

        """

        if not time:
            self.clock_textview.get_buffer().set_text('')
        else:
            self.clock_textview.get_buffer().set_text(
                self.convert_time_to_string(time),
            )


    def update_countdown_textview(self, time):

        """Called by various functions.

        Updates the main window textview showing the time until the next
        message to be displayed.

        Args:

            time (int): The time in seconds

        """

        if not time:
            self.countdown_textview.get_buffer().set_text('')
        else:
            self.countdown_textview.get_buffer().set_text(
                self.convert_time_to_string(math.ceil(time)),
            )


    def update_this_info_textview(self, msg):

        """Called by various functions.

        Updates the main window textview with the current message (if any).

        Args:

            msg (str): The message to display (use an empty string to clear the
                textview)

        """

        self.this_info_textview.get_buffer().set_text(str(msg))


    def update_next_info_textview(self, msg):

        """Called by various functions.

        Updates the main window textview with the next message (if any).

        Args:

            msg (str): The message to display (use an empty string to clear the
                textview)

        """

        self.next_info_textview.get_buffer().set_text(str(msg))


    def update_menu_items_on_prog(self):

        """Called by various functions.

        (De)sensitises menu items depending on whether any workout programmes
        exist, or not.
        """

        if self.app_obj.current_prog_started_flag:
            self.new_prog_menu_item.set_sensitive(False)
        else:
            self.new_prog_menu_item.set_sensitive(True)

        if not self.app_obj.prog_dict:
            self.edit_prog_menu_item.set_sensitive(False)
        else:
            self.edit_prog_menu_item.set_sensitive(True)

        if not self.app_obj.prog_dict \
        or self.app_obj.current_prog_started_flag:
            self.switch_prog_menu_item.set_sensitive(False)
            self.delete_prog_menu_item.set_sensitive(False)
        else:
            self.switch_prog_menu_item.set_sensitive(True)
            self.delete_prog_menu_item.set_sensitive(True)


    def update_buttons_on_start(self):

        """Called by mainapp.GymBobApp.on_button_start().

        (De)sensitises buttons after the user clicks the START button.
        """

        self.start_button.set_sensitive(False)
        self.stop_button.set_sensitive(True)
        self.reset_button.set_sensitive(False)


    def update_buttons_on_stop(self):

        """Called by mainapp.GymBobApp.on_button_stop().

        (De)sensitises buttons after the user clicks the STOP button.
        """

        self.start_button.set_sensitive(True)
        self.stop_button.set_sensitive(False)
        self.reset_button.set_sensitive(True)


    def update_buttons_on_reset(self):

        """Called by mainapp.GymBobApp.on_button_reset().

        (De)sensitises buttons after the user clicks the RESET button.
        """

        self.start_button.set_sensitive(True)
        self.stop_button.set_sensitive(False)
        self.reset_button.set_sensitive(True)


    def update_buttons_on_current_prog(self):

        """Called by various functions.

        (De)sensitises the START, STOP and RESET buttons, depending on whether
        there is a current workout programme, or not.
        """

        if not self.app_obj.current_prog_obj:
            self.start_button.set_sensitive(False)
            self.stop_button.set_sensitive(False)
            self.reset_button.set_sensitive(False)

        else:
            self.start_button.set_sensitive(True)
            self.stop_button.set_sensitive(True)
            self.reset_button.set_sensitive(True)


    # (Support functions)


    def convert_time_to_string(self, time):

        """Called by various functions.

        Converts a time value (an integer in seconds) into a formatted string,
        e.g. '1:27:02'.

        Args:

            time (int): A value in seconds (0 or above)

        Return values:

            The converted string

        """

        minutes = int(time / 60)
        seconds = int(time % 60)

        hours = int(minutes / 60)
        minutes = int(minutes % 60)

        time_str = str(minutes).zfill(2) + ':' + str(seconds).zfill(2)
        if hours > 0:
            time_str = str(hours) + ':' + time_str

        return time_str


    def add_child_window(self, edit_win_obj):

        """Called by editwin.ProgEditWin.setup().

        When an edit window opens, add it to our list of such windows. (A
        workout programme will not start while the window(s) are open.)

        Args:

            edit_win_obj (edit.ProgEditWin): The window to add

        """

        # Check that the window isn't already in the list (unlikely, but check
        #   anyway)
        if not edit_win_obj in self.edit_win_list:

            # Update the IV
            self.edit_win_list.append(edit_win_obj)


    def del_child_window(self, edit_win_obj):

        """Called by editwin.ProgEditWin.close().

        When an edit window closes, remove it to our list of such windows.

        Args:

            edit_win_obj (edit.ProgEditWin): The window to remove

        """

        # Update the IV
        if edit_win_obj in self.edit_win_list:
            self.edit_win_list.remove(edit_win_obj)


    # Callbacks


    def on_menu_mute_sound(self, checkbutton):

        """Called from a callback in self.setup_menubar().

        Mutes (or unmutes) sound effects.

        Args:

            checkbutton (Gtk.CheckButton): The widget clicked.

        """

        self.app_obj.set_mute_sound_flag(checkbutton.get_active())


class DeleteProgDialogue(Gtk.Dialog):

    """Called by mainapp.GymBobApp.on_menu_switch_prog().

    Python class handling a dialogue window that prompts the user to delete a
    workout programme.

    Args:

        main_win_obj (mainwin.MainWin): The parent main window

    """


    def __init__(self, main_win_obj):

        # IV list - Gtk widgets
        # ---------------------
        self.combo = None                       # Gtk.ComboBox


        # IV list - other
        # ---------------
        self.prog_name = None
        self.prog_list = []


        # Code
        # ----

        Gtk.Dialog.__init__(
            self,
            'Delete programme',
            main_win_obj,
            Gtk.DialogFlags.DESTROY_WITH_PARENT,
            (
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OK, Gtk.ResponseType.OK,
            )
        )

        self.set_modal(True)

        # Set up the dialogue window
        box = self.get_content_area()

        grid = Gtk.Grid()
        box.add(grid)
        grid.set_border_width(main_win_obj.app_obj.default_spacing_size)
        grid.set_row_spacing(main_win_obj.app_obj.default_spacing_size)

        label = Gtk.Label('Select the programme to delete')
        grid.attach(label, 0, 0, 1, 1)

        # Import and display a sorted list of workout programmes
        self.prog_list = list(main_win_obj.app_obj.prog_dict.keys())
        self.prog_list.sort()
        self.prog_name = self.prog_list[0]

        listmodel = Gtk.ListStore(str)
        for item in self.prog_list:
            listmodel.append([item])

        self.combo = Gtk.ComboBox.new_with_model(listmodel)
        grid.attach(self.combo, 0, 1, 1, 1)
        self.combo.set_hexpand(True)

        cell = Gtk.CellRendererText()
        self.combo.pack_start(cell, False)
        self.combo.add_attribute(cell, 'text', 0)
        self.combo.set_active(0)
        self.combo.connect('changed', self.on_combo_changed)

        # Display the dialogue window
        self.show_all()


    def on_combo_changed(self, combo):

        """Called from callback in self.__init__().

        Store the combobox's selected item, so the calling function can
        retrieve it.

        Args:

            combo (Gtk.ComboBox): The clicked widget

        """

        self.prog_name = self.prog_list[combo.get_active()]


class NewProgDialogue(Gtk.Dialog):

    """Called by mainapp.GymBobApp.on_menu_new_prog().

    Python class handling a dialogue window that prompts the user for the name
    of a new workout programme.

    Args:

        main_win_obj (mainwin.MainWin): The parent main window

    """


    def __init__(self, main_win_obj):

        # IV list - Gtk widgets
        # ---------------------
        self.entry = None                       # Gtk.Entry


        # Code
        # ----

        Gtk.Dialog.__init__(
            self,
            'New programme',
            main_win_obj,
            Gtk.DialogFlags.DESTROY_WITH_PARENT,
            (
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OK, Gtk.ResponseType.OK,
            )
        )

        self.set_modal(True)

        # Set up the dialogue window
        box = self.get_content_area()

        grid = Gtk.Grid()
        box.add(grid)
        grid.set_border_width(main_win_obj.app_obj.default_spacing_size)
        grid.set_row_spacing(main_win_obj.app_obj.default_spacing_size)

        label = Gtk.Label('Enter the name of a new workout programme')
        grid.attach(label, 0, 0, 1, 1)

        self.entry = Gtk.Entry()
        grid.attach(self.entry, 0, 1, 1, 1)
        self.entry.set_hexpand(True)
        self.entry.set_max_length(16)

        # Display the dialogue window
        self.show_all()


class SwitchProgDialogue(Gtk.Dialog):

    """Called by mainapp.GymBobApp.on_menu_switch_prog().

    Python class handling a dialogue window that prompts the user to switch to
    a new workout programme.

    Args:

        main_win_obj (mainwin.MainWin): The parent main window

    """


    def __init__(self, main_win_obj):

        # IV list - Gtk widgets
        # ---------------------
        self.combo = None                       # Gtk.ComboBox


        # IV list - other
        # ---------------
        self.prog_name = None
        self.prog_list = []


        # Code
        # ----

        Gtk.Dialog.__init__(
            self,
            'Switch programme',
            main_win_obj,
            Gtk.DialogFlags.DESTROY_WITH_PARENT,
            (
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OK, Gtk.ResponseType.OK,
            )
        )

        self.set_modal(True)

        # Set up the dialogue window
        box = self.get_content_area()

        grid = Gtk.Grid()
        box.add(grid)
        grid.set_border_width(main_win_obj.app_obj.default_spacing_size)
        grid.set_row_spacing(main_win_obj.app_obj.default_spacing_size)

        label = Gtk.Label('Set the new workout programme')
        grid.attach(label, 0, 0, 1, 1)

        # Import a sorted list of programmes. The current programme should be
        #   the first item in the list
        import_list = list(main_win_obj.app_obj.prog_dict.keys())
        sorted_list = []
        self.prog_name = main_win_obj.app_obj.current_prog_obj.name

        for item in import_list:
            if item != self.prog_name:
                self.prog_list.append(item)

        self.prog_list.sort()
        self.prog_list.insert(0, self.prog_name)

        listmodel = Gtk.ListStore(str)
        for item in self.prog_list:
            listmodel.append([item])

        self.combo = Gtk.ComboBox.new_with_model(listmodel)
        grid.attach(self.combo, 0, 1, 1, 1)
        self.combo.set_hexpand(True)

        cell = Gtk.CellRendererText()
        self.combo.pack_start(cell, False)
        self.combo.add_attribute(cell, 'text', 0)
        self.combo.set_active(0)
        self.combo.connect('changed', self.on_combo_changed)

        # Display the dialogue window
        self.show_all()


    def on_combo_changed(self, combo):

        """Called from callback in self.__init__().

        Store the combobox's selected item, so the calling function can
        retrieve it.

        Args:

            combo (Gtk.ComboBox): The clicked widget

        """

        self.prog_name = self.prog_list[combo.get_active()]

