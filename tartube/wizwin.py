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


"""Wizard window classes."""


# Import Gtk modules
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Gdk, GdkPixbuf


# Import other modules
import os
import re
import zipfile


# Import our modules
import __main__
import formats
import mainapp
import media
import utils
# Use same gettext translations
from mainapp import _


# Classes


class GenericWizWin(Gtk.Window):

    """Generic Python class for windows in which the user can modify various
    system settings.

    Unlike classes inheriting from GenericEditWin, widgets are arranged in
    pages, with only page visible at a time. The user can cycle through pages
    (when allowed) by clicking the 'Next' or 'Previous' buttons.

    Modifications are usually applied immediately, but the code provides an
    .apply_changes() function for anything that should be applied, when the
    user has cycled through all the pages.
    """


    # Standard class methods


#   def __init__():             # Provided by child object


    # Public class methods


    def is_duplicate(self, app_obj):

        """Called by self.__init__.

        Don't open this wizard window, if another wizard window (if any class)
        is already open.

        Args:

            app_obj (mainapp.TartubeApp): The main application object

        Return values:

            True if a duplicate is found, False if not

        """

        if app_obj.main_win_obj.wiz_win_obj:

            # Duplicate found
            app_obj.main_win_obj.wiz_win_obj.present()
            return True

        else:

            # Not a duplicate
            return False


    def setup(self):

        """Called by self.__init__().

        Sets up the wizard window when it opens.
        """

        # Set the default window size
        self.set_default_size(
            self.app_obj.config_win_width,
            self.app_obj.config_win_height,
        )

        # Set the window's Gtk icon list
        self.set_icon_list(self.app_obj.main_win_obj.win_pixbuf_list)

        # Set up main widgets
        self.setup_grid()
        self.setup_button_strip()

        # Set up the first page (a widget layout on self.inner_grid)
        self.setup_page()

        # Procedure complete
        self.show_all()

        # Inform the main window of this window's birth (so that Tartube
        #   doesn't allow an operation to start until all configuration windows
        #   have closed)
        self.app_obj.main_win_obj.add_child_window(self)

        # Add a callback so we can inform the main window of this window's
        #   destruction
        self.connect('destroy', self.close)


    def setup_grid(self):

        """Called by self.setup().

        Sets up two Gtk.Grids. The first one contains an inner grid, and a
        button strip.
        """

        box = Gtk.Box()
        self.add(box)
        box.set_border_width(self.spacing_size)

        self.grid = Gtk.Grid()
        box.add(self.grid)
        self.grid.set_row_spacing(self.spacing_size)
        self.grid.set_column_spacing(self.spacing_size)

        frame = Gtk.Frame()
        self.grid.attach(frame, 0, 0, 1, 1)
        frame.set_hexpand(True)
        frame.set_vexpand(True)

        self.vbox = Gtk.VBox()
        frame.add(self.vbox)
        self.vbox.set_border_width(self.spacing_size * 2)

        self.inner_grid = Gtk.Grid()
        self.vbox.pack_start(self.inner_grid, True, False, 0)
        self.inner_grid.set_row_spacing(self.spacing_size)
        self.inner_grid.set_column_spacing(self.spacing_size)


    def setup_button_strip(self):

        """Called by self.setup().

        Creates a strip of buttons at the bottom of the window: a 'cancel'
        button on the left, and 'next'/'previous' buttons on the right.

        The window is closed by using the 'cancel' button, or by clicking the
        'next' button on the last page.
        """

        hbox = Gtk.HBox()
        self.grid.attach(hbox, 0, 1, 1, 1)

        # 'Cancel' button
        self.cancel_button = Gtk.Button(_('Cancel'))
        hbox.pack_start(self.cancel_button, False, False, 0)
        self.cancel_button.get_child().set_width_chars(10)
        self.cancel_button.set_tooltip_text(
            _('Close this window without completing it'),
        );
        self.cancel_button.connect('clicked', self.on_button_cancel_clicked)

        # 'Next' button
        self.next_button = Gtk.Button(_('Next'))
        hbox.pack_end(self.next_button, False, False, 0)
        self.next_button.get_child().set_width_chars(10)
        self.next_button.set_tooltip_text(_('Go to the next page'));
        self.next_button.connect('clicked', self.on_button_next_clicked)

        # 'Previous' button
        self.prev_button = Gtk.Button(_('Previous'))
        hbox.pack_end(self.prev_button, False, False, self.spacing_size)
        self.prev_button.get_child().set_width_chars(10)
        self.prev_button.set_tooltip_text(_('Go to the previous page'));
        self.prev_button.connect('clicked', self.on_button_prev_clicked)


    def setup_page(self):

        """Called initially by self.setup(), then by .on_button_next_clicked()
        or .on_button_prev_clicked().

        Sets up the page specified by self.current_page.
        """

        index = self.current_page
        page_func = self.page_list[self.current_page]
        if page_func is None:

            # Emergency fallback
            index = 0
            page_func = self.page_list[0]

        if len(self.page_list) <= 1:
            self.next_button.set_sensitive(False)
            self.prev_button.set_sensitive(False)
        elif index == 0:
            self.next_button.set_sensitive(True)
            self.prev_button.set_sensitive(False)
        else:
            self.next_button.set_sensitive(True)
            self.prev_button.set_sensitive(True)

        if index >= len(self.page_list) - 1:
            self.next_button.set_label(_('OK'))
        else:
            self.next_button.set_label(_('Next'))

        self.next_button.get_child().set_width_chars(10)

        # Replace the inner grid...
        self.vbox.remove(self.inner_grid)

        self.inner_grid = Gtk.Grid()
        self.vbox.pack_start(self.inner_grid, True, False, 0)
        self.inner_grid.set_row_spacing(self.spacing_size)
        self.inner_grid.set_column_spacing(self.spacing_size)

        # ...and then refill it, with the widget layout for the new page
        method = getattr(self, page_func)
        method()

        self.show_all()


    def convert_next_button(self):

        """Can be called by anything.

        Converts the 'Next' to an 'OK' button, and sensitises it.

        Should usually be called from the last page, when the code is ready to
        let the window finish the wizard.
        """

        self.next_button.set_label(_('Finish'))
        self.next_button.get_child().set_width_chars(10)
        self.next_button.set_sensitive(True)


    def apply_changes(self):

        """Called by self.on_button_next_clicked().

        The default function is empty. Any changes that need to be applied,
        when the wizard window closes, can be applied in a function with this
        name.
        """

        pass


    def cancel_changes(self):

        """Called by self.on_button_cancel_clicked().

        The default function is empty. Any changes that need to be applied,
        when the wizard window is closed by clicking the 'Cancel' button, can
        be applied in a function with this name.
        """

        pass


    def close(self, widget):

        """Called from callback in self.setup().

        Inform the main application that this window is closing.

        Args:

            widget (GenericWizWin): This window

        """

        self.app_obj.main_win_obj.del_child_window(self)


    # (Add widgets)


    def add_image(self, image_path, x, y, wid, hei):

        """Called by various functions in the child wizard window.

        Adds a Gtk.Image to self.inner_grid, with more than the usual padding.

        Args:

            image_path (str): Full path to the image file to load

            x, y, wid, hei (int): Position on the grid at which the widget is
                placed

        Return values:

            The Gtk.Box containing the image

        """

        box = Gtk.Box()
        self.inner_grid.attach(box, x, y, wid, hei)
        box.set_border_width(self.spacing_size * 2)

        image = Gtk.Image()
        box.add(image)
        image.set_from_pixbuf(
            self.app_obj.file_manager_obj.load_to_pixbuf(image_path),
        )
        image.set_hexpand(True)

        return box


    def add_label(self, text, x, y, wid, hei):

        """Called by various functions in the child wizard window.

        Adds a Gtk.Label to self.inner_grid.

        Args:

            text (str): Pango markup displayed in the label

            x, y, wid, hei (int): Position on the grid at which the widget is
                placed

        Return values:

            The label widget created

        """

        label = Gtk.Label()
        self.inner_grid.attach(label, x, y, wid, hei)
        label.set_markup(text)
        label.set_hexpand(True)
        label.set_alignment(0.5, 0.5)

        return label


    def add_empty_label(self, x, y, wid, hei):

        """Called by various functions in the child wizard window.

        Adds an empty Gtk.Label (for spacing) to self.inner_grid.

        Args:

            x, y, wid, hei (int): Position on the grid at which the widget is
                placed

        Return values:

            The label widget created

        """

        label = Gtk.Label()
        self.inner_grid.attach(label, x, y, wid, hei)
        # (Using a space, rather than an empty string, better preserves the
        #   intended layout)
        label.set_text(' ')
        label.set_hexpand(True)
        label.set_alignment(0.5, 0.5)

        return label


    def add_checkbutton(self, text, x, y, wid, hei):

        """Called by various functions in the child wizard window.

        Adds a Gtk.CheckButton to self.inner_grid.

        Args:

            text (string or None): The text to display in the checkbutton's
                label. No label is used if 'text' is an empty string or None

            x, y, wid, hei (int): Position on the grid at which the widget is
                placed

        Return values:

            The checkbutton widget created

        """

        checkbutton = Gtk.CheckButton()
        self.inner_grid.attach(checkbutton, x, y, wid, hei)
        checkbutton.set_hexpand(True)
        if text is not None and text != '':
            checkbutton.set_label(text)

        return checkbutton


    def add_radiobutton(self, prev_button, text, x, y, wid, hei):

        """Called by various functions in the child wizard window.

        Adds a Gtk.RadioButton to self.inner_grid.

        Args:

            prev_button (Gtk.RadioButton or None): When this is the first
                radio button in the group, None. Otherwise, the previous
                radio button in the group. Use of this argument links the radio
                buttons together, ensuring that only one of them can be active
                at any time

            text (string or None): The text to display in the radiobutton's
                label. No label is used if 'text' is an empty string or None

            x, y, wid, hei (int): Position on the grid at which the widget is
                placed

        Return values:

            The radiobutton widget created

        """

        radiobutton = Gtk.RadioButton.new_from_widget(prev_button)
        self.inner_grid.attach(radiobutton, x, y, wid, hei)
        radiobutton.set_hexpand(True)
        if text is not None and text != '':
            radiobutton.set_label(text)

        return radiobutton


    def add_textview(self, x, y, wid, hei):

        """Called by various functions in the child wizard window.

        Adds a Gtk.TextView to self.inner_grid.

        Args:

            x, y, wid, hei (int): Position on the grid at which the widget is
                placed

        Return values:

            The scroller, textview and textbuffer widgets created

        """

        frame = Gtk.Frame()
        self.inner_grid.attach(frame, x, y, wid, hei)

        scrolled = Gtk.ScrolledWindow()
        frame.add(scrolled)
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_size_request(-1, 125)

        textview = Gtk.TextView()
        scrolled.add(textview)
        textview.set_wrap_mode(Gtk.WrapMode.WORD)
        textview.set_editable(False)
        textview.set_cursor_visible(False)

        return scrolled, textview, textview.get_buffer()


    # Callback class methods


    def on_button_cancel_clicked(self, button):

        """Called from a callback in self.setup_button_strip().

        Closes the wizard window without applying any changes.

        Args:

            button (Gtk.Button): The widget clicked

        """

        self.cancel_changes()
        self.destroy()


    def on_button_next_clicked(self, button):

        """Called from a callback in self.setup_button_strip().

        Goes to the the next page, or (if already on the last page) applies
        any changes waiting to be applied, then closes the window.

        Args:

            button (Gtk.Button): The widget clicked

        """

        if self.current_page >= (len(self.page_list) - 1):
            self.apply_changes()
            self.destroy()

        else:

            self.current_page += 1
            self.setup_page()


    def on_button_prev_clicked(self, button):

        """Called from a callback in self.setup_button_strip().

        Goes to the previous page.

        Args:

            button (Gtk.Button): The widget clicked

        """

        if self.current_page > 0:
            self.current_page -= 1
            self.setup_page()


class SetupWizWin(GenericWizWin):

    """Python class for a 'wizard window' displayed when Tartube starts and
    no config file can be loaded (meaning that this is a new installation).

    Args:

        app_obj (mainapp.TartubeApp): The main application object

    """


    # Standard class methods


    def __init__(self, app_obj):

        ignore_me = _(
            'TRANSLATOR\'S NOTE: Setup wizard window starts here.' \
            + ' This window is visible on startup, if there is no config' \
            + ' file (settings.json)'
        )

        Gtk.Window.__init__(self, title=_('Tartube setup'))

        if self.is_duplicate(app_obj):
            return

        # IV list - class objects
        # -----------------------
        # The mainapp.TartubeApp object
        self.app_obj = app_obj


        # IV list - Gtk widgets
        # ---------------------
        self.grid = None                        # Gtk.Grid
        self.vbox = None                        # Gtk.VBox
        self.inner_grid = None                  # Gtk.Grid
        self.cancel_button = None               # Gtk.Button
        self.next_button = None                 # Gtk.Button
        self.prev_button = None                 # Gtk.Button
        # (Textbuffers used to display output of an update operation, and the
        #   buttons used to initiate that operation)
        self.downloader_button = None           # Gtk.Button
        self.update_button = None               # Gtk.Button
        self.update_combo = None                # Gtk.ComboBox
        self.update_liststore = None            # Gtk.ListStore
        self.downloader_scrolled = None         # Gtk.ScrolledWindow
        self.downloader_textview = None         # Gtk.TextView
        self.downloader_textbuffer = None       # Gtk.TextBuffer
        self.ffmpeg_button = None               # Gtk.Button
        self.ffmpeg_scrolled = None             # Gtk.ScrolledWindow
        self.ffmpeg_textview = None             # Gtk.TextView
        self.ffmpeg_textbuffer = None           # Gtk.TextBuffer
        self.tutorial_button = None             # Gtk.Button
        self.auto_open_button = None            # Gtk.Button


        # IV list - other
        # ---------------
        # Size (in pixels) of gaps between preference window widgets
        self.spacing_size = self.app_obj.default_spacing_size

        # List of 'pages' (widget layouts on self.inner_grid). Each item in the
        #   list is the function to call
        self.page_list = []                     # Set below
        # The number of the current page (the first is 0), matching an index in
        #   self.page_list
        self.current_page = 0

        # Make the code a little simpler, by checking for MS Windows just once
        #   (set below)
        self.mswin_flag = False

        # User choices; they are applied when the window is closed (and
        #   self.apply_changes() is called)
        # Path to Tartube's data directory
        self.data_dir = None
        # The new value of mainapp.TartubeApp.db_backup_mode, if any
        self.db_backup_mode = None
        # The name of the youtube-dl fork to use, by default ('None' when
        #   youtube-dl itself should be used)
        self.ytdl_fork = 'yt-dlp'
        # Flag set to True if yt-dlp (only), when installed via pip, should be
        #   installed without dependencies
        if os.name == 'nt':
            self.ytdl_fork_no_dependency_flag = True
        else:
            self.ytdl_fork_no_dependency_flag = False
        # The new value of mainapp.TartubeApp.ytdl_update_current, if any
        self.ytdl_update_current = None
        # The new value of
        #   mainapp.TartubeApp.show_classic_tab_on_startup_flag, if any
        self.show_classic_tab_on_startup_flag = None

        # Flag set to True, once the 'More options' button has been clicked,
        #   so that it is never visible again
        self.more_options_flag = False
        # Flag set to True after the user has tried install FFmpeg at least
        #   once (even if the attempt failed)
        self.try_install_ffmpeg_flag = False

        # Flag set to True if the tutorial wizard window should be opened,
        #   after this one closes
        self.open_tutorial_flag = False

        # Standard length of text in the wizard window
        self.text_len = 60

        # Code
        # ----

        # Check for MS Windows
        if os.name == 'nt':

            self.mswin_flag = True

        # Set the page list, which depends on operating system and packaging
        self.page_list = [
            'setup_start_page',
            'setup_db_page',
            'setup_backup_page',
            'setup_set_downloader_page',
        ]

        if self.mswin_flag:
            self.page_list.append('setup_fetch_downloader_page')
            self.page_list.append('setup_fetch_ffmpeg_page')
            self.page_list.append('setup_classic_mode_page')
            self.page_list.append('setup_finish_page_mswin')

        elif __main__.__pkg_strict_install_flag__:
            self.page_list.append('setup_classic_mode_page')
            self.page_list.append('setup_finish_page_strict')

        else:
            self.page_list.append('setup_fetch_downloader_page')
            self.page_list.append('setup_classic_mode_page')
            self.page_list.append('setup_finish_page_default')

        # Set up the wizard window
        self.setup()


    # Public class methods


#   def is_duplicate():         # Inherited from GenericWizWin


#   def setup():                # Inherited from GenericWizWin


#   def setup_grid():           # Inherited from GenericWizWin


#   def setup_button_strip():   # Inherited from GenericWizWin


#   def setup_page():           # Inherited from GenericWizWin


#   def convert_next_button():  # Inherited from GenericWizWin


    def apply_changes(self):

        """Called by self.on_button_next_clicked().

        Apply the settings the user has specified.
        """

        if self.data_dir is not None:
            self.app_obj.set_data_dir(self.data_dir)
            self.app_obj.set_data_dir_alt_list( [ self.data_dir ] )
            self.app_obj.update_data_dirs()

        # (None values are acceptable)
        self.app_obj.set_ytdl_fork(self.ytdl_fork)

        self.app_obj.set_ytdl_fork_no_dependency_flag(
            self.ytdl_fork_no_dependency_flag,
        )

        # (A None value, only if they haven't been changed)
        if self.db_backup_mode is not None:
            self.app_obj.set_db_backup_mode(self.db_backup_mode)

        if self.ytdl_update_current is not None:
            self.app_obj.set_ytdl_update_current(self.ytdl_update_current)

        if self.show_classic_tab_on_startup_flag is not None:
            self.app_obj.set_show_classic_tab_on_startup_flag(
                self.show_classic_tab_on_startup_flag,
            )

        # Continue with general initialisation
        self.app_obj.open_wiz_win_continue(self)


    def cancel_changes(self):

        """Called by self.on_button_cancel_clicked().

        Tartube needs to be shut down (unless an update operation is running,
        in which case we stop it.)
        """

        if self.app_obj.update_manager_obj:

            self.app_obj.update_manager_obj.stop_update_operation()

        else:

            # (Prevent the shutdown code from saving the config file and/or
            #   database)
            self.app_obj.disable_load_save()

            # (Delete the config file, so that this window will appear again,
            #   the next time Tartube runs)
            config_path = self.app_obj.get_config_path()
            if os.path.isfile(config_path):
                os.remove(config_path)

            # Shut down Tartube
            self.app_obj.stop()


#   def close():                # Inherited from GenericWizWin


    # (Setup pages)


    def setup_start_page(self):

        """Called by self.setup_page().

        Sets up the widget layout for a page.
        """

        self.add_image(
            self.app_obj.main_win_obj.icon_dict['system_icon'],
            0, 0, 1, 1,
        )

        self.add_label(
            '<span font_size="large" font_weight="bold">' \
            + _('Welcome to Tartube!') + '</span>',
            0, 1, 1, 1,
        )

        if __main__.__pkg_no_download_flag__:

            edition = _('Video downloads are disabled in this package')

        elif __main__.__pkg_strict_install_flag__:

            edition = _(
                'For this package, youtube-dl and FFmpeg must be' \
                + ' installed separately',
            )

        elif __main__.__pkg_install_flag__:

            edition = _('Package edition')

        elif os.name == 'nt':

            edition = _('MS Windows edition')

        else:

            edition = _('Standard edition')

        self.add_label(
            '<span style="italic">' \
            + utils.tidy_up_long_string(edition, self.text_len) + '</span>',
            0, 2, 1, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 3, 1, 1)

        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(
                _('Please take a few moments to set up the application.'),
                self.text_len,
            ) + '</span>',
            0, 4, 1, 1,
        )

        self.add_label(
            '<span font_size="large"  style="italic">' \
            + utils.tidy_up_long_string(
                _('Click the <b>Next</b> button to get started.'),
                self.text_len,
            ) + '</span>',
            0, 5, 1, 1,
        )


    def setup_db_page(self):

        """Called by self.setup_page().

        Sets up the widget layout for a page.
        """

        grid_width = 3

        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(
                _('Tartube stores all of its downloads in one place.'),
                self.text_len,
            ) + '</span>',
            0, 0, grid_width, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 1, grid_width, 1)

        if not self.mswin_flag:

            msg = utils.tidy_up_long_string(
                _(
                    'If you don\'t want to use the default location, then' \
                    + ' click <b>Choose</b> to select a different one.',
                ),
                self.text_len,
            )

            msg2 = utils.tidy_up_long_string(
                _(
                    'If you have used Tartube before, you can select an' \
                    + ' existing directory, instead of creating a new one.',
                ),
                self.text_len,
            )

        else:

            msg = _('Click <b>Choose</b> to create a new folder.')
            msg2 = utils.tidy_up_long_string(
                _(
                    'If you have used Tartube before, you can select an' \
                    + ' existing folder, instead of creating a new one.',
                ),
                self.text_len,
            )

        self.add_label(
            '<span font_size="large" style="italic">' + msg + '</span>',
            0, 2, grid_width, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 3, grid_width, 1)

        self.add_label(
            '<span font_size="large" style="italic">' + msg2 + '</span>',
            0, 4, grid_width, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 5, grid_width, 1)

        button = Gtk.Button(_('Choose'))
        self.inner_grid.attach(button, 1, 6, 1, 1)
        # (Signal connect appears below)

        if not self.mswin_flag:
            button2 = Gtk.Button(_('Use default location'))
            self.inner_grid.attach(button2, 1, 7, 1, 1)
            # (Signal connect appears below)

        # (Empty label for spacing)
        self.add_empty_label(0, 8, grid_width, 1)

        # The specified path appears here, after it has been selected
        if self.data_dir is None:

            label = self.add_label(
                '',
                0, 9, grid_width, 1,
            )

        else:

            label = self.add_label(
                '<span font_size="large" font_weight="bold">' \
                + self.data_dir + '</span>',
                0, 9, grid_width, 1,
            )

        # (Signal connects from above)
        button.connect(
            'clicked',
            self.on_button_choose_folder_clicked,
            label,
        )

        if not self.mswin_flag:

            button2.connect(
                'clicked',
                self.on_button_default_folder_clicked,
                label,
            )

        # Disable the Next button until a folder has been created/selected
        if self.data_dir is None:
            self.next_button.set_sensitive(False)


    def setup_backup_page(self):

        """Called by self.setup_page().

        Sets up the widget layout for a page.
        """

        grid_width = 3

        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(
                _(
                    'When saving the database, Tartube makes a backup' \
                    + ' copy of its database file (in case something goes' \
                    + ' wrong).',
                ),
                self.text_len,
            ) + '</span>',
            0, 0, grid_width, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 1, grid_width, 1)

        radiobutton = self.add_radiobutton(
            None,
            _('Delete the backup as soon as the database has been saved'),
            1, 2, 1, 1,
        )
        radiobutton.set_hexpand(False)
        # (Signal connect appears below)

        radiobutton2 = self.add_radiobutton(
            radiobutton,
            _('Keep the backup file, replacing any previous backup file'),
            1, 3, 1, 1,
        )
        # (Signal connect appears below)
        radiobutton2.set_hexpand(False)

        radiobutton3 = self.add_radiobutton(
            radiobutton2,
            _('Make a new backup file once per day'),
            1, 4, 1, 1,
        )
        radiobutton3.set_hexpand(False)
        # (Signal connect appears below)

        radiobutton4 = self.add_radiobutton(
            radiobutton3,
            _('Make a new backup file every time the database is saved'),
            1, 5, 1, 1,
        )
        radiobutton4.set_active(True)
        radiobutton4.set_hexpand(False)
        # (Signal connect appears below)

        # (Signal connects from above)
        radiobutton.connect(
            'toggled',
            self.on_button_backup_mode_toggled,
            'default',
        )
        radiobutton2.connect(
            'toggled',
            self.on_button_backup_mode_toggled,
            'single',
        )
        radiobutton3.connect(
            'toggled',
            self.on_button_backup_mode_toggled,
            'daily',
        )
        radiobutton4.connect(
            'toggled',
            self.on_button_backup_mode_toggled,
            'always',
        )

        # (Empty labels either side of the radio buttons, so they appear in
        #   the middle)
        self.add_empty_label(0, 2, 1, 1)
        self.add_empty_label(2, 2, 1, 1)


    def setup_set_downloader_page(self):

        """Called by self.setup_page().

        Sets up the widget layout for a page.
        """

        grid_width = 3

        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(
                _('Choose which downloader to use.'),
                self.text_len,
            ) + '</span>',
            0, 0, grid_width, 1,
        )

        # yt-dlp
        radiobutton, checkbutton = self.setup_set_downloader_page_add_button(
            1,                  # Row number
            '<b>yt-dlp</b>: <i>' \
            + self.app_obj.ytdl_fork_descrip_dict['yt-dlp'] \
            + '</i>',
            _('Use yt-dlp'),
            None,               # No radiobutton group yet
            'button'            # Show a checkbutton
        )

        # youtube-dl
        radiobutton2 = self.setup_set_downloader_page_add_button(
            2,                  # Row number
            '<b>youtube-dl</b>: <i>' \
            + self.app_obj.ytdl_fork_descrip_dict['youtube-dl'] \
            + '</i>',
            _('Use youtube-dl'),
            radiobutton,
        )

        # Any other fork
        radiobutton3, entry = self.setup_set_downloader_page_add_button(
            3,                  # Row number
            '<b>' + _('Other forks') + ':</b> <i>' \
            + self.app_obj.ytdl_fork_descrip_dict['custom'] \
            + '</i>',
            _('Use this fork:'),
            radiobutton2,
            'entry',            # Show an entry
        )

        # # Set widgets' initial states
        if self.ytdl_fork is None or self.ytdl_fork == 'youtube-dl':
            radiobutton2.set_active(True)
            checkbutton.set_sensitive(False)
            entry.set_sensitive(False)
        elif self.ytdl_fork == 'yt-dlp':
            radiobutton.set_active(True)
            checkbutton.set_sensitive(True)
            entry.set_sensitive(False)
        else:
            radiobutton3.set_active(True)
            if self.ytdl_fork is not None:
                entry.set_text(self.ytdl_fork)
            else:
                entry.set_text('')
            checkbutton.set_sensitive(False)
            entry.set_sensitive(True)

        # (Signal connects from the call to
        #   self.setup_set_downloader_page_add_button() )
        radiobutton.connect(
            'toggled',
            self.on_button_ytdl_fork_toggled,
            checkbutton,
            entry,
            'yt-dlp',
        )
        checkbutton.connect('toggled', self.on_button_ytdlp_install_toggled)
        radiobutton2.connect(
            'toggled',
            self.on_button_ytdl_fork_toggled,
            checkbutton,
            entry,
            'youtube-dl',
        )
        radiobutton3.connect(
            'toggled',
            self.on_button_ytdl_fork_toggled,
            checkbutton,
            entry,
        )
        entry.connect(
            'changed',
            self.on_entry_ytdl_fork_changed,
            radiobutton3,
        )


    def setup_set_downloader_page_add_button(self, row, label_text, radio_text,
    radiobutton=None, extra_mode=None):

        """Called by self.setup_set_downloader_page().

        Adds widgets for a single downloader option.

        Args:

            row (int): Row number in self.inner_grid

            label_text (str): Text to use in a Gtk.Label

            radio_text (str): Text to use in a Gtk.RadioButton

            radiobutton (Gtk.RadioButton): The previous radiobutton in the same
                group

            extra_mode (str or None): 'entry' to show an extra Gtk.Entry,
                'button' to show an extra Gtk.CheckButton, or None for no
                extra widget

        Return values:

            If 'extra_mode' is None, returns the radiobutton. If 'entry' or
                'button', returns the radiobutton and the extra widget as a
                list

        """

        if not extra_mode:
            grid_width = 1
        else:
            grid_width = 2

        # (Use an event box so the downloader can be selected by clicking
        #   anywhere in the frame)
        event_box = Gtk.EventBox()
        self.inner_grid.attach(event_box, 1, row, 1, 1)
        # (Signal connect appears below)

        frame = Gtk.Frame()
        event_box.add(frame)
        frame.set_border_width(self.spacing_size)
        frame.set_hexpand(False)

        grid = Gtk.Grid()
        frame.add(grid)
        grid.set_border_width(self.spacing_size)
        grid.set_row_spacing(self.spacing_size)

        label = Gtk.Label()
        grid.attach(label, 0, 0, grid_width, 1)
        label.set_markup(utils.tidy_up_long_string(label_text))
        label.set_hexpand(False)
        label.set_alignment(0, 0.5)

        radiobutton2 = Gtk.RadioButton.new_from_widget(radiobutton)
        grid.attach(radiobutton2, 0, 1, 1, 1)
        radiobutton2.set_hexpand(False)
        radiobutton2.set_label('   ' + radio_text)
        # (Signal connect appears in the calling function)

        # (Signal connect from above)
        event_box.connect(
            'button-press-event',
            self.on_frame_downloader_clicked,
            radiobutton2,
        )

        if extra_mode == 'button':

            # For yt-dlp, add a checkbutton, and return it with the radiobutton
            checkbutton = Gtk.CheckButton.new_with_label(
                _(
                _('Install without dependencies') + '\n' \
                + _('(recommended on MS Windows)'),
                ),
            )
            grid.attach(checkbutton, 1, 1, 1, 1)
            if self.ytdl_fork_no_dependency_flag:
                checkbutton.set_active(True)
            # (Signal connect appears in the calling function)

            return radiobutton2, checkbutton

        elif extra_mode == 'entry':

            # For other forks, add an entry, and return it with the radiobutton
            entry = Gtk.Entry()
            grid.attach(entry, 1, 1, 1, 1)
            entry.set_hexpand(True)
            entry.set_editable(True)
            # (Signal connect appears in the calling function)
            radiobutton2.set_hexpand(False)

            return radiobutton2, entry

        else:
            return radiobutton2


    def setup_fetch_downloader_page(self):

        """Called by self.setup_page().

        Sets up the widget layout for a page.
        """

        grid_width = 3

        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(
                _('Click the button to install or update the downloader.'),
                self.text_len,
            ) + '</span>',
            0, 0, grid_width, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 1, grid_width, 1)

        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(
                _(
                    'You should do this, even if you think it is already' \
                    + ' installed.',
                ),
                self.text_len,
            ) + '</span>',
            0, 2, grid_width, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 3, grid_width, 1)

        if os.name != 'nt':
            extra_rows = 0

        else:
            extra_rows = 1
            self.add_label(
                '<span font_size="large" style="italic">' \
                + _('Estimated install size') + ': <b>15 MB</b></span>',
                0, (3 + extra_rows), grid_width, 1,
            )

        self.downloader_button = Gtk.Button(_('Install and update downloader'))
        self.inner_grid.attach(
            self.downloader_button,
            1, (4 + extra_rows), 1, 1,
        )
        self.downloader_button.set_hexpand(False)
        # (Signal connect appears below)

        self.update_button = Gtk.Button(_('More options'))
        # (Making the button invisible doesn't work, so instead don't add it
        #   to the grid at all)
        if os.name != 'nt' and not self.more_options_flag:
            self.inner_grid.attach(
                self.update_button,
                1, (5 + extra_rows), 1, 1,
            )
        self.update_button.set_hexpand(False)
        # (Signal connect appears below)

        # (When the update button is clicked, it is made invisible, and this
        #   widget is made visible instead)
        self.update_liststore = Gtk.ListStore(str, str)
        for item in self.app_obj.ytdl_update_list:
            self.update_liststore.append(
                [item, formats.YTDL_UPDATE_DICT[item]],
            )

        self.update_combo = Gtk.ComboBox.new_with_model(self.update_liststore)
        if os.name != 'nt':
            self.inner_grid.attach(
                self.update_combo,
                1, (5 + extra_rows), 1, 1,
            )
        if not self.more_options_flag:
            self.update_combo.set_visible(False)

        renderer_text = Gtk.CellRendererText()
        self.update_combo.pack_start(renderer_text, True)
        self.update_combo.add_attribute(renderer_text, 'text', 1)
        self.update_combo.set_entry_text_column(1)

        if self.ytdl_update_current is not None:
            ytdl_update_current = self.ytdl_update_current
        else:
            ytdl_update_current = self.app_obj.ytdl_update_current

        self.update_combo.set_active(
            self.app_obj.ytdl_update_list.index(ytdl_update_current),
        )
        # (Signal connect appears below)

        # Update the combo, so that the youtube-dl fork, rather than
        #   youtube-dl itself, is visible (if applicable)
        self.refresh_update_combo()

        self.downloader_scrolled, self.downloader_textview, \
        self.downloader_textbuffer = self.add_textview(
            0, (7 + extra_rows), grid_width, 1,
        )

        # (Signal connects from above)
        self.downloader_button.connect(
            'clicked',
            self.on_button_fetch_downloader_clicked,
        )

        self.update_button.connect(
            'clicked',
            self.on_button_update_path_clicked,
        )

        # (Signal connects from above)
        self.update_combo.connect('changed', self.on_combo_update_changed)


    def setup_fetch_ffmpeg_page(self):

        """Called by self.setup_page().

        Sets up the widget layout for a page.
        """

        grid_width = 3

        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(
                _('Click the button to install FFmpeg.'),
                self.text_len,
            ) + '</span>',
            0, 0, grid_width, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 1, grid_width, 1)

        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(
                _(
                    'Without FFmpeg, Tartube cannot download high-resolution' \
                    + ' videos, and cannot display video thumbnails from' \
                    + ' YouTube.',
                ),
                self.text_len,
            ) + '</span>',
            0, 2, grid_width, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 3, grid_width, 1)

        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(
                _(
                    'The operation might take several minutes. If it fails,' \
                    + ' try clicking the <b>Install FFmpeg</b> button again.',
                ),
                self.text_len,
            ) + '</span>',
            0, 4, grid_width, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 5, grid_width, 1)

        if os.name != 'nt':
            extra_rows = 0

        else:
            extra_rows = 1

            self.add_label(
                '<span font_size="large" style="italic">' \
                + _('Download size') + ': <b>0.3 GB</b> - ' \
                + _('Install size') + ': <b>1.5 GB</b></span>',
                0, (5 + extra_rows), grid_width, 1,
            )

        if not self.try_install_ffmpeg_flag:
            msg = _('Install FFmpeg')
        else:
            msg = _('Reinstall FFmpeg')
        self.ffmpeg_button = Gtk.Button(msg)

        self.inner_grid.attach(self.ffmpeg_button, 1, (6 + extra_rows), 1, 1)
        self.ffmpeg_button.set_hexpand(False)
        # (Signal connect appears below)

        self.ffmpeg_scrolled, self.ffmpeg_textview, self.ffmpeg_textbuffer \
        = self.add_textview(
            0, (7 + extra_rows), grid_width, 1,
        )

        # (Signal connects from above)
        self.ffmpeg_button.connect(
            'clicked',
            self.on_button_fetch_ffmpeg_clicked,
        )


    def setup_classic_mode_page(self):

        """Called by self.setup_page().

        Invites the user to open Tartube at the Classic Mode tab.
        """

        grid_width = 3

        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(
                _('Tartube adds videos to a database.'),
                self.text_len,
            ) + '</span>',
            0, 0, grid_width, 1,
        )

        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(
                _('If you don\'t need a database, you can use Classic Mode.'),
                self.text_len,
            ) + '</span>',
            0, 1, grid_width, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 2, grid_width, 1)

        self.add_image(
            self.app_obj.main_win_obj.icon_dict['setup_classic_icon'],
            0, 3, grid_width, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 4, grid_width, 1)

        if not self.show_classic_tab_on_startup_flag:
            msg = _('Always open Tartube at this tab')
        else:
            msg = _('Don\'t open Tartube at this tab')

        self.auto_open_button = Gtk.Button(msg)
        self.inner_grid.attach(self.auto_open_button, 1, 5, 1, 1)
        self.auto_open_button.set_hexpand(False)
        self.auto_open_button.connect(
            'clicked',
            self.on_button_auto_open_clicked,
        )


    def setup_finish_page_mswin(self):

        """Called by self.setup_page().

        Sets up the widget layout for a page, shown only on MS Windows.
        """

        grid_width = 3

        self.add_image(
            self.app_obj.main_win_obj.icon_dict['ready_icon'],
            0, 0, grid_width, 1,
        )

        self.add_label(
            '<span font_size="large" font_weight="bold">' \
            + _('All done!') + '</span>',
            0, 1, grid_width, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 2, grid_width, 1)

        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(
                _(
                    'If you need to re-install or update the downloader or' \
                    + ' FFmpeg, you can do it from the main window\'s menu.',
                ),
                self.text_len,
            ) + '</span>',
            0, 3, grid_width, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 4, grid_width, 1)

        self.add_label(
            '<span font_size="large"  style="italic">' \
            + utils.tidy_up_long_string(
                _(
                    'Click this button below to see a short tutorial, or' \
                    + ' click the OK button to start Tartube!',
                ),
                self.text_len,
            ) + '</span>',
            0, 5, grid_width, 1,
        )

        self.add_tutorial_button(6)


    def setup_finish_page_strict(self):

        """Called by self.setup_page().

        Sets up the widget layout for a page, shown only after a STRICT install
        from a DEB/RPM package.
        """

        grid_width = 3

        self.add_image(
            self.app_obj.main_win_obj.icon_dict['ready_icon'],
            0, 0, grid_width, 1,
        )

        self.add_label(
            '<span font_size="large" font_weight="bold">' \
            + _('All done!') + '</span>',
            0, 1, grid_width, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 2, grid_width, 1)

        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(
                _(
                    'You must install the downloader on your system, before' \
                    + ' you can use Tartube.'
                ),
                self.text_len,
            ) + '</span>',
            0, 3, grid_width, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 4, grid_width, 1)

        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(
                _(
                    'It is strongly recommended that you install FFmpeg.' \
                    + ' Without it, Tartube cannot download video clips or' \
                    + ' high-resolution videos, and cannot display many' \
                    + ' thumbnails.',
                ),
                self.text_len,
            ) + '</span>',
            0, 5, grid_width, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 6, grid_width, 1)

        self.add_label(
            '<span font_size="large"  style="italic">' \
            + utils.tidy_up_long_string(
                _(
                    'Click this button below to see a short tutorial, or' \
                    + ' click the OK button to start Tartube!',
                ),
                self.text_len,
            ) + '</span>',
            0, 7, grid_width, 1,
        )

        self.add_tutorial_button(8)


    def setup_finish_page_default(self):

        """Called by self.setup_page().

        Sets up the widget layout for a page, for all operating systems except
        MS Windows.
        """

        grid_width = 3

        self.add_image(
            self.app_obj.main_win_obj.icon_dict['ready_icon'],
            0, 0, grid_width, 1,
        )

        self.add_label(
            '<span font_size="large" font_weight="bold">' \
            + _('All done!') + '</span>',
            0, 1, grid_width, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 2, grid_width, 1)

        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(
                _('It is strongly recommended that you install FFmpeg.'),
                self.text_len,
            ) + '</span>',
            0, 3, grid_width, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 4, grid_width, 1)

        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(
                _(
                    'Without FFmpeg, Tartube cannot download video clips or' \
                    + ' high-resolution videos, and cannot display many' \
                    + ' video thumbnails.',
                ),
                self.text_len,
            ) + '</span>',
            0, 5, grid_width, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 6, grid_width, 1)

        self.add_label(
            '<span font_size="large"  style="italic">' \
            + utils.tidy_up_long_string(
                _(
                    'Click this button below to see a short tutorial, or' \
                    + ' click the OK button to start Tartube!',
                ),
                self.text_len,
            ) + '</span>',
            0, 7, grid_width, 1,
        )

        self.add_tutorial_button(8)


    # (Support functions)


    def add_tutorial_button(self, row):

        """Called by several (final) pages to show a button that opens the
        tutorial wizard window.

        Args:

            row (int): The row on which the button is placed

        """

        grid2 = Gtk.Grid()
        self.inner_grid.attach(
            grid2,
            1, row, 1, 1,
        )
        grid2.set_hexpand(False)

        box = Gtk.Box()
        grid2.attach(box, 0, 0, 1, 3)
        box.set_border_width(self.spacing_size * 2)

        image = Gtk.Image()
        box.add(image)
        image.set_from_pixbuf(
            self.app_obj.main_win_obj.pixbuf_dict['learn_left_large'],
        )
        image.set_hexpand(False)

        self.tutorial_button = Gtk.Button(_('Read the tutorial'))
        grid2.attach(
            self.tutorial_button,
            1, 1, 1, 1
        )
        self.tutorial_button.set_hexpand(True)
        self.tutorial_button.connect(
            'clicked',
            self.on_button_tutorial_clicked,
        )

        box2 = Gtk.Box()
        grid2.attach(box2, 2, 0, 1, 3)
        box2.set_border_width(self.spacing_size * 2)

        image2 = Gtk.Image()
        box2.add(image2)
        image2.set_from_pixbuf(
            self.app_obj.main_win_obj.pixbuf_dict['learn_right_large'],
        )
        image2.set_hexpand(False)


    def downloader_page_write(self, msg):

        """Called by updates.UpdateManager.install_ytdl_write_output() or
        self.downloader_fetch_finished().

        When installing/updating youtube-dl (or a fork), write a message in the
        textview.

        N.B. Because Gtk is not thread safe, this function must always be
        called from within GObject.timeout_add().

        Args:

            msg (str): The message to display

        """

        self.downloader_textbuffer.insert(
            self.downloader_textbuffer.get_end_iter(),
            utils.tidy_up_long_string(msg) + '\n',
        )

        adjust = self.downloader_scrolled.get_vadjustment()
        adjust.set_value(adjust.get_upper())

        self.downloader_textview.queue_draw()


    def downloader_fetch_finished(self, msg):

        """Called by mainapp.TartubeApp.update_manager_finished().

        Display the success/failure message in the textview, and re-sensitise
        buttons.

        Args:

            msg (str): The success/failure message to display

        """

        GObject.timeout_add(
            0,
            self.downloader_page_write,
            msg,
        )

        self.downloader_button.set_sensitive(True)
        self.next_button.set_sensitive(True)
        self.prev_button.set_sensitive(True)


    def ffmpeg_page_write(self, msg):

        """Called by updates.UpdateManager.install_ytdl_write_output() or
        self.ffmpeg_fetch_finished().

        When installing FFmpeg, write a message in the textview.

        N.B. Because Gtk is not thread safe, this function must always be
        called from within GObject.timeout_add().

        Args:

            msg (str): The message to display

        """

        self.ffmpeg_textbuffer.insert(
            self.ffmpeg_textbuffer.get_end_iter(),
            utils.tidy_up_long_string(msg) + '\n',
        )

        adjust = self.ffmpeg_scrolled.get_vadjustment()
        adjust.set_value(adjust.get_upper())

        self.downloader_textview.queue_draw()


    def ffmpeg_fetch_finished(self, msg):

        """Called by mainapp.TartubeApp.update_manager_finished().

        Display the success/failure message in the textview, and re-sensitise
        buttons.

        Args:

            msg (str): The success/failure message to display

        """

        GObject.timeout_add(
            0,
            self.ffmpeg_page_write,
            msg,
        )

        self.ffmpeg_button.set_label(_('Reinstall FFmpeg'))
        self.ffmpeg_button.set_sensitive(True)
        self.next_button.set_sensitive(True)
        self.prev_button.set_sensitive(True)

        self.try_install_ffmpeg_flag = True


    def refresh_update_combo(self):

        """Called by self.setup_fetch_downloader_page().

        When the youtube-dl fork is changed, updates the contents of the
        combo created by self.setup_fetch_downloader_page().
        """

        fork = standard = 'youtube-dl'
        if self.ytdl_fork is not None:
            fork = self.ytdl_fork

        count = -1
        for item in self.app_obj.ytdl_update_list:

            count += 1
            descrip = re.sub(standard, fork, formats.YTDL_UPDATE_DICT[item])
            self.update_liststore.set(
                self.update_liststore.get_iter(Gtk.TreePath(count)),
                1,
                descrip,
            )


    # (Callbacks)


    def on_button_auto_open_clicked(self, button):

        """Called from a callback in self.setup_classic_mode_page().

        Sets whether the main window should open at the Classic Mode tab, or
        not.

        Args:

            button (Gtk.Button): The widget clicked

        """

        if not self.show_classic_tab_on_startup_flag:
            self.show_classic_tab_on_startup_flag = True
            button.set_label(_('Don\'t open Tartube at this tab'))
        else:
            self.show_classic_tab_on_startup_flag = False
            button.set_label(_('Always open Tartube at this tab'))


    def on_button_backup_mode_toggled(self, radiobutton, mode):

        """Called from callback in self.setup_backup_page().

        Sets the database file's backup mode.

        Args:

            radiobutton (Gtk.Radiobutton): The widget clicked

            mode (str): The new value of mainapp.TartubeApp.db_backup_mode

        """

        if radiobutton.get_active():
            self.db_backup_mode = mode


    def on_button_cancel_clicked(self, button):

        """Modified version of the standard function, called from a callback in
        self.setup_button_strip().

        Closes the wizard window without applying any changes, unless an
        update operation is in progress.

        Args:

            button (Gtk.Button): The widget clicked

        """

        self.cancel_changes()
        if not self.app_obj.update_manager_obj:
            self.destroy()


    def on_button_choose_folder_clicked(self, button, label):

        """Called from a callback in self.setup_db_page().

        Opens a file chooser dialogue, so the user can set the location of
        Tartube's data directory.

        Args:

            button (Gtk.Button): The widget clicked

            label (Gtk.Label): Once set, the path to the directory is displayed
                in this label

        """

        if not self.mswin_flag:
            title = _('Select Tartube\'s data directory')
        else:
            title = _('Select Tartube\'s data folder')

        dialogue_win = self.app_obj.dialogue_manager_obj.show_file_chooser(
            title,
            self,
            'folder',
        )

        # Get the user's response
        response = dialogue_win.run()
        if response == Gtk.ResponseType.OK:

            self.data_dir = dialogue_win.get_filename()
            label.set_markup(
                '<span font_size="large" font_weight="bold">' + self.data_dir \
                + '</span>',
            )

            # Data directory set, so re-enable the Next button
            self.next_button.set_sensitive(True)

        dialogue_win.destroy()


    def on_button_default_folder_clicked(self, button, label):

        """Called from a callback in self.setup_db_page().

        Sets the default location for Tartube's data directory (not on MS
        Windows).

        Args:

            button (Gtk.Button): The widget clicked

            label (Gtk.Label): Once set, the path to the directory is displayed
                in this label

        """

        self.data_dir = self.app_obj.data_dir
        label.set_markup(
            '<span font_size="large" font_weight="bold">' \
            + self.app_obj.data_dir + '</span>',
        )

        # Data directory set, so re-enable the Next button
        self.next_button.set_sensitive(True)


    def on_button_fetch_downloader_clicked(self, button):

        """Called from a callback in self.setup_fetch_page().

        Starts an update operation to download and install the selected fork of
        youtube-dl.

        Args:

            button (Gtk.Button): The widget clicked

        """

        # Desensitise buttons until the operation is complete
        button.set_sensitive(False)
        self.next_button.set_sensitive(False)
        self.prev_button.set_sensitive(False)

        # Start the update operation
        if not self.app_obj.update_manager_start_from_wizwin(self, 'ytdl'):

            # Operation did not start
            button.set_sensitive(True)
            self.next_button.set_sensitive(True)
            self.prev_button.set_sensitive(True)


    def on_button_fetch_ffmpeg_clicked(self, button):

        """Called from a callback in self.setup_fetch_page().

        Starts an update operation to download and install FFmpeg.

        Args:

            button (Gtk.Button): The widget clicked

        """

        # Desensitise buttons until the operation is complete
        button.set_sensitive(False)
        self.next_button.set_sensitive(False)
        self.prev_button.set_sensitive(False)

        # Start the update operation
        if not self.app_obj.update_manager_start_from_wizwin(self, 'ffmpeg'):

            # Operation did not start
            button.set_sensitive(True)
            self.next_button.set_sensitive(True)
            self.prev_button.set_sensitive(True)


    def on_button_tutorial_clicked(self, button):

        """Called from a callback in self.setup_fetch_page().

        Closes this window, and marks the tutorial wizard window to be opened.

        Args:

            button (Gtk.Button): The widget clicked

        """

        self.open_tutorial_flag = True
        self.apply_changes()
        self.destroy()


    def on_button_update_path_clicked(self, button):

        """Called from a callback in self.setup_fetch_page().

        Makes the 'More options' button invisible, and the update path combo
        visible.

        Args:

            button (Gtk.Button): The widget clicked

        """

        button.set_visible(False)
        self.update_combo.set_visible(True)

        # Flag set to True, once the 'More options' button has been clicked,
        #   so that it is never visible again
        self.more_options_flag = True


    def on_button_ytdl_fork_toggled(self, radiobutton, checkbutton, entry, \
    fork_type=None):

        """Called from callback in self.setup_set_downloader_page().

        Sets the youtube-dl fork to be used. See also
        self.on_entry_ytdl_fork_changed().

        Args:

            radiobutton (Gtk.Radiobutton): The widget clicked

            checkbutton (Gtk.CheckButton): Another widget to be updated

            entry (Gtk.Entry): Another widget to be updated

            fork_type (str): 'yt-dlp', 'youtube-dl', or None for any other fork

        """

        if radiobutton.get_active():

            if fork_type is None:

                fork_name = entry.get_text()
                # (As in the preference window, if the 'other fork' option is
                #   selected, but nothing is entered in the entry box, use
                #   youtube-dl as the downloader)
                if fork_name == '':
                    self.ytdl_fork = None
                else:
                    self.ytdl_fork = fork_name

                checkbutton.set_sensitive(False)
                entry.set_sensitive(True)

            elif fork_type == 'youtube-dl':

                self.ytdl_fork = None
                checkbutton.set_sensitive(False)
                entry.set_text('')
                entry.set_sensitive(False)

            elif fork_type == 'yt-dlp':

                self.ytdl_fork = fork_type
                checkbutton.set_sensitive(True)
                entry.set_text('')
                entry.set_sensitive(False)


    def on_button_ytdlp_install_toggled(self, checkbutton):

        """Called from callback in self.setup_set_downloader_page().

        Sets the flag to install yt-dlp with or without dependencies.

        Args:

            checkbutton (Gtk.CheckButton): The widget clicked

        """

        if checkbutton.get_active():
            self.ytdl_fork_no_dependency_flag = True
        else:
            self.ytdl_fork_no_dependency_flag = False


    def on_combo_update_changed(self, combo):

        """Called from callback in self.setup_fetch_downloader_page().

        Sets the youtube-dl install/update method.

        Args:

            combo (Gtk.ComboBox): The widget clicked

        """

        tree_iter = combo.get_active_iter()
        model = combo.get_model()
        self.ytdl_update_current = model[tree_iter][0]


    def on_entry_ytdl_fork_changed(self, entry, radiobutton):

        """Called from callback in self.setup_set_downloader_page().

        Sets the youtube-dl fork to be used. See also
        self.on_button_ytdl_fork_toggled().

        Args:

            entry (Gtk.Entry): The widget changed

        """

        if radiobutton.get_active():

            entry_text = utils.strip_whitespace(entry.get_text())
            # (As in the preference window, if the 'other fork' option is
            #   selected, but nothing is entered in the entry box, use
            #   youtube-dl as the system default)
            if entry_text == '':
                self.ytdl_fork = None
            else:
                self.ytdl_fork = entry_text


    def on_frame_downloader_clicked(self, event_box, event_button,
    radiobutton):

        """Called from callback in self.setup_set_downloader_page().

        Enables/disables selecting a downloader by clicking anywhere in its
        containing frame.

        Args:

            event_box (Gtk.EventBox): Ignored

            event_button (Gdk.EventButton): Ignored

            radiobutton (Gtk.RadioButton): The radiobutton inside the clicked
                frame, which should be made active

        """

        if not radiobutton.get_active():
            radiobutton.set_active(True)


class ImportYTWizWin(GenericWizWin):

    """Python class for a 'wizard window' used to import YouTube subscriptions.

    Args:

        app_obj (mainapp.TartubeApp): The main application object

    """


    # Standard class methods


    def __init__(self, app_obj):

        ignore_me = _(
            'TRANSLATOR\'S NOTE: Subscriptions wizard window starts here.' \
            + ' In the menu, click Media > Export/Import > Import' \
            + ' YouTube subscriptions...'
        )

        Gtk.Window.__init__(self, title=_('Import YouTube subscriptions'))

        if self.is_duplicate(app_obj):
            return

        # IV list - class objects
        # -----------------------
        # The mainapp.TartubeApp object
        self.app_obj = app_obj


        # IV list - Gtk widgets
        # ---------------------
        self.grid = None                        # Gtk.Grid
        self.vbox = None                        # Gtk.VBox
        self.inner_grid = None                  # Gtk.Grid
        self.cancel_button = None               # Gtk.Button
        self.next_button = None                 # Gtk.Button
        self.prev_button = None                 # Gtk.Button
        # (From self.setup_finish_page)
        self.liststore = None                   # Gtk.ListStore
        self.checkbutton = None                 # Gtk.CheckButton


        # IV list - other
        # ---------------
        # Size (in pixels) of gaps between preference window widgets
        self.spacing_size = self.app_obj.default_spacing_size

        # List of 'pages' (widget layouts on self.inner_grid). Each item in the
        #   list is the function to call
        self.page_list = []                     # Set below
        # The number of the current page (the first is 0), matching an index in
        #   self.page_list
        self.current_page = 0

        # User choices
        # Path to the YouTube export file
        self.import_path = None
        # Dictionary of importable channels/playlists, in the form described in
        #   mainapp.TartubeApp.export_from_db()
        self.db_dict = {}

        # Standard length of text in the wizard window
        self.text_len = 60


        # Code
        # ----

        # Set the page list
        self.page_list = [
            'setup_start_page',
            'setup_load_page',
            'setup_finish_page',
        ]

        # Set up the wizard window
        self.setup()


    # Public class methods


#   def is_duplicate():         # Inherited from GenericWizWin


#   def setup():                # Inherited from GenericWizWin


#   def setup_grid():           # Inherited from GenericWizWin


#   def setup_button_strip():   # Inherited from GenericWizWin


#   def setup_page():           # Inherited from GenericWizWin


#   def convert_next_button():  # Inherited from GenericWizWin


    def apply_changes(self):

        """Called by self.on_button_next_clicked().

        Import the specified channels/playlists into the Tartube database.
        """

        (video_count, channel_count, playlist_count, folder_count) \
        = self.app_obj.process_import(
            self.db_dict,           # The imported data...
            self.db_dict,           # ...already exists in 'flattened' form
            None,                   # No parent 'mini_dict' yet
            False,                  # No videos to import
            self.checkbutton.get_active(),
            True,                   # Imported into selected folder, if any
            0,                      # video_count
            0,                      # channel_count
            0,                      # playlist count
            0,                      # folder_count
        )

        if not channel_count and not playlist_count:
            self.app_obj.dialogue_manager_obj.show_msg_dialogue(
                _('Nothing has been imported'),
                'error',
                'ok',
            )

        else:

            # Show a confirmation
            msg = _('Imported into database') \
                + ':\n\n' + _('Videos') + ': ' + str(video_count) \
                + '\n' + _('Channels') + ': ' + str(channel_count) \
                + '\n' + _('Playlists') + ': ' + str(playlist_count) \
                + '\n' + _('Folders') + ': ' + str(folder_count)

            self.app_obj.dialogue_manager_obj.show_simple_msg_dialogue(
                msg,
                'info',
                'ok',
            )


#   def cancel_changes():       # Inherited from GenericWizWin


#   def close():                # Inherited from GenericWizWin


    # (Setup pages)


    def setup_start_page(self):

        """Called by self.setup_page().

        Sets up the widget layout for a page.
        """

        self.add_image(
            self.app_obj.main_win_obj.icon_dict['yt_icon'],
            0, 0, 1, 1,
        )

        self.add_label(
            '<span font_size="large" font_weight="bold">' \
            + _('Import YouTube Subscriptions') + '</span>',
            0, 1, 1, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 2, 1, 1)

        row = 2
        for msg in [
            _('Open YouTube in your browser, and sign in'),
            _('Click the channel icon in the top-right corner'),
            _('Select <b>Your data in YouTube</b>'),
            _('Under <b>Your YouTube dashboard</b>, click <b>More</b>'),
            _('Click <b>Download YouTube data</b>'),
            _('Click <b>All YouTube data included</b>'),
            _('Deselect everything except <b>Subscriptions</b>'),
            _('Click <b>Next step</b>, then <b>Create export</b>'),
            _('Wait a few moments, then click  <b>Download</b>'),

        ]:
            row += 1
            self.add_label(
                '<span font_size="large" style="italic">* ' \
                + utils.tidy_up_long_string(msg, self.text_len) + '</span>',
                0, row, 1, 1,
            )


    def setup_load_page(self):

        """Called by self.setup_page().

        Sets up the widget layout for a page.
        """

        grid_width = 3

        self.add_image(
            self.app_obj.main_win_obj.icon_dict['yt_icon'],
            0, 0, grid_width, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 1, grid_width, 1)

        self.add_label(
            '<span font_size="large"  style="italic">' \
            + _('Select the YouTube export file') \
            + '</span>',
            0, 2, grid_width, 1,
        )

        button = Gtk.Button(_('Select file'))
        self.inner_grid.attach(button, 1, 3, 1, 1)
        # (Signal connect appears below)

        # (Empty label for spacing)
        self.add_empty_label(0, 4, grid_width, 1)

        # The specified path appears here, after it has been selected
        if self.import_path is None:

            label = self.add_label(
                '',
                0, 5, grid_width, 1,
            )

        else:

            label = self.add_label(
                '<span font_size="large" font_weight="bold">' \
                + self.import_path + '</span>',
                0, 5, grid_width, 1,
            )

        # (Signal connects from above)
        button.connect(
            'clicked',
            self.on_button_choose_import_clicked,
            label,
        )

        # Disable the Next button until a valid import has been selected
        if self.import_path is None:
            self.next_button.set_sensitive(False)


    def setup_finish_page(self):

        """Called by self.setup_page().

        Sets up the widget layout for a page.
        """

        grid_width = 5

        self.add_image(
            self.app_obj.main_win_obj.icon_dict['yt_icon'],
            0, 0, grid_width, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 1, grid_width, 1)

        scrolled = Gtk.ScrolledWindow()
        self.inner_grid.attach(scrolled, 0, 2, grid_width, 1)
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_size_request(-1, 250)

        frame = Gtk.Frame()
        scrolled.add_with_viewport(frame)

        treeview = Gtk.TreeView()
        frame.add(treeview)
        treeview.set_headers_visible(True)
        treeview.set_can_focus(False)

        for i, column_title in enumerate(
            [ _('Import'), _('Type'), _('Name'), _('URL'), 'hide' ],
        ):
            if i == 0:
                renderer_toggle = Gtk.CellRendererToggle()
                renderer_toggle.connect('toggled', self.on_checkbutton_toggled)
                column_toggle = Gtk.TreeViewColumn(
                    column_title,
                    renderer_toggle,
                    active=i,
                )
                treeview.append_column(column_toggle)
            elif i == 1:
                renderer_pixbuf = Gtk.CellRendererPixbuf()
                column_pixbuf = Gtk.TreeViewColumn(
                    column_title,
                    renderer_pixbuf,
                    pixbuf=i,
                )
                treeview.append_column(column_pixbuf)
                column_pixbuf.set_resizable(False)
            else:
                renderer_text = Gtk.CellRendererText()
                column_text = Gtk.TreeViewColumn(
                    column_title,
                    renderer_text,
                    text=i,
                )
                treeview.append_column(column_text)
                if column_title == 'hide':
                    column_text.set_visible(False)
                else:
                    column_text.set_resizable(True)
                    if i == 2:
                        renderer_text.connect(
                            'edited',
                            self.on_container_name_edited,
                        )
                    elif i == 3:
                        renderer_text.connect(
                            'edited',
                            self.on_container_url_edited,
                        )
                renderer_text.set_property('editable', True)

        self.liststore = Gtk.ListStore(
            bool, GdkPixbuf.Pixbuf, str, str, int,
        )
        treeview.set_model(self.liststore)

        # Populate the treeview

        # (Sorting function for the code immediately below)
        def sort_dict_by_name(this_dict):
            return this_dict['name']

        # Deal with importable channels/playlists in alphabetical order
        for mini_dict in sorted(self.db_dict.values(), key=sort_dict_by_name):

            self.liststore.append([
                mini_dict['import_flag'],
                self.app_obj.main_win_obj.pixbuf_dict[
                    mini_dict['type'] + '_small'
                ],
                mini_dict['name'],
                mini_dict['source'],
                mini_dict['dbid'],
            ])

        # Strip of widgets at the bottom
        self.checkbutton = self.add_checkbutton(
            _('Merge channels/playlists'),
            0, 3, 1, 1,
        )

        button = Gtk.Button(_('Toggle channel/playlist'))
        self.inner_grid.attach(button, 1, 3, 1, 1)
        button.connect(
            'clicked',
            self.on_button_toggle_container_clicked,
            treeview,
        )

        button2 = Gtk.Button(_('Select all'))
        self.inner_grid.attach(button2, 2, 3, 1, 1)
        button2.connect('clicked', self.on_button_select_all_clicked)

        button3 = Gtk.Button(_('Unselect all'))
        self.inner_grid.attach(button3, 3, 3, 1, 1)
        button3.connect('clicked', self.on_button_unselect_all_clicked)


    # (Support functions)


    def validate_import(self, label):

        """Called by self.on_button_choose_import_clicked().

        The path to the export file has been stored in self.import_path.

        Check the file exists, is valid, and contains some YouTube
        subscriptions. Update IVs and the text of 'label' accordingly

        Args:

            label (Gtk.Label): A widget to update

        Return values:

            True on success, False of failure

        """

        fail_msg = None

        # Check a .zip file really exists
        if self.import_path is None \
        or not os.path.isfile(self.import_path) \
        or not zipfile.is_zipfile(self.import_path):
            fail_msg = _('Missing of invalid export file')

        # Prepare to extract the archive in a temporary directory, deleting any
        #   existing directory first
        temp_dir = None
        if not fail_msg:

            temp_dir = os.path.abspath(
                os.path.join(
                    self.app_obj.temp_dir,
                    'zip',
                ),
            )

            if os.path.isdir(temp_dir) \
            and not self.app_obj.remove_directory(temp_dir):
                fail_msg = _('Unable to prepare export file for extraction')

        if not fail_msg:

            if not self.app_obj.make_directory(temp_dir):
                fail_msg = _('Unable to prepare export file for extraction')

        # Extract the subscriptions.csv file from the archive
        if not fail_msg:

            rel_path = os.path.join(
                'Takeout',
                'YouTube and YouTube Music',
                'subscriptions',
                'subscriptions.csv',
            )

            try:
                with(zipfile.ZipFile(self.import_path)) as zip_file:
                    zip_file.extract(member=rel_path, path=temp_dir)

            except:
                fail_msg = _('Unable to extract export file')

        # Check that a subscriptions.csv exists
        if not fail_msg:

            csv_path = os.path.abspath(
                os.path.join(
                    temp_dir,
                    'Takeout',
                    'YouTube and YouTube Music',
                    'subscriptions',
                    'subscriptions.csv',
                ),
            )

            if not os.path.isfile(csv_path):
                fail_msg = _('Missing subscriptions in export file')

        # Extract a list of channels/playlists from the export file
        subscription_list = []
        if not fail_msg:

            # List of lists; each minilist represents one channel/playlist,
            #   and is in the form [name, URL]
            try:

                fh = open(csv_path, 'r')
                count = 0
                for line in fh.readlines():

                    # Ignore the first line, which should be
                    #   'Channel ID,Channel URL,Channel title'
                    count += 1
                    if count > 1:

                        match = re.search(
                            '^([^,]+),([^,]+),([^,\n]+)\n*$',
                            line,
                        )
                        if match:
                            subscription_list.append([
                                match.groups()[2],      # Channel title
                                match.groups()[1],      # URL
                            ])

            except:
                fail_msg = _('Cannot read subscriptions in export file')

        if not fail_msg and not subscription_list:
            fail_msg = _('No subscriptions in export file')

        # Delete the temporary directory and update the text of the label
        if temp_dir is not None:
            self.app_obj.remove_directory(temp_dir)

        if fail_msg:

            # (No channels/playlists are currently importable)
            self.db_dict = {}

            label.set_markup(
                '<span font_size="large" font_weight="bold">' + fail_msg \
                + '</span>',
            )

            return False

        else:

            if len(subscription_list) == 1:

                label.set_markup(
                    '<span font_size="large" font_weight="bold">'  \
                    + _('Export file is valid, extracted 1 subscription') \
                    + '</span>',
                )

            else:

                label.set_markup(
                    '<span font_size="large" font_weight="bold">'  \
                    + _(
                        'Export file is valid, extracted {0} subscriptions',
                    ).format(len(subscription_list)) \
                    + '</span>',
                )

            # Convert 'subscription_list' into the standard export/import
            #   format described in mainapp.TartubeApp.export_from_db()
            self.db_dict = {}
            count = 0

            for mini_list in subscription_list:

                count += 1

                mini_dict = {
                    # (Assume everything is a channel, initially)
                    'type': 'channel',
                    # (Use a fake .dbid; code in mainapp.TartubeApp creates
                    #   new media.Channel and media.Playlist objects with
                    #   real .dbids)
                    'dbid': count,
                    'vid': None,
                    'name': mini_list[0],
                    'nickname': mini_list[0],
                    'file': None,
                    'source': mini_list[1],
                    # (This procedure does not import videos)
                    'db_dict': {},
                    # (Add one of the extra key-value pairs also added by
                    #   mainwin.ImportDialogue)
                    'import_flag': True,
                }

                self.db_dict[count] = mini_dict

            # Procedure complete
            return True


    # (Callbacks)


    def on_button_choose_import_clicked(self, button, label):

        """Called from a callback in self.setup_load_page().

        Opens a file chooser dialogue, so the user can set the location of the
        YouTube export.

        Args:

            button (Gtk.Button): The widget clicked

            label (Gtk.Label): Once set, the path to the directory is displayed
                in this label

        """

        dialogue_win = self.app_obj.dialogue_manager_obj.show_file_chooser(
            'Select the YouTube export',
            self,
            'open',
        )

        # Get the user's response
        response = dialogue_win.run()
        if response == Gtk.ResponseType.OK:

            self.import_path = dialogue_win.get_filename()
            # Check the export file, storing the results in various IVs, and
            #   setting label accordingly
            # Then enable/disable the Next button
            if not self.validate_import(label):
                self.next_button.set_sensitive(False)
            else:
                self.next_button.set_sensitive(True)

        dialogue_win.destroy()


    def on_button_select_all_clicked(self, button):

        """Called from a callback in self.setup_finish_page().

        Mark all channels/playlists to be imported.

        Args:

            button (Gtk.Button): The widget clicked

        """

        for path in range(0, len(self.liststore)):
            self.liststore[path][0] = True

        for mini_dict in self.db_dict.values():
            mini_dict['import_flag'] = True


    def on_button_toggle_container_clicked(self, button, treeview):

        """Called from a callback in self.setup_finish_page().

        Switch the selected channel to a playlist, or vice-versa.

        Args:

            button (Gtk.Button): The widget clicked

            treeview (Gtk.TreeView): The treeview to be modified

        """

        selection = treeview.get_selection()
        (model, tree_iter) = selection.get_selected()
        if tree_iter is None:

            # Nothing selected
            return

        # Update the dictionary of data to be imported
        fake_dbid = model[tree_iter][4]
        for mini_dict in self.db_dict.values():

            if mini_dict['dbid'] == fake_dbid:

                if mini_dict['type'] == 'channel':
                    mini_dict['type'] = 'playlist'
                else:
                    mini_dict['type'] = 'channel'

                # Update the treeview's row
                model[tree_iter] = [
                    mini_dict['import_flag'],
                    self.app_obj.main_win_obj.pixbuf_dict[
                        mini_dict['type'] + '_small'
                    ],
                    mini_dict['name'],
                    mini_dict['source'],
                    mini_dict['dbid'],
                ]

                return


    def on_button_unselect_all_clicked(self, button):

        """Called from a callback in self.setup_finish_page().

        Mark all channels/playlists to be not imported.

        Args:

            button (Gtk.Button): The widget clicked

        """

        for path in range(0, len(self.liststore)):
            self.liststore[path][0] = False

        for mini_dict in self.db_dict.values():
            mini_dict['import_flag'] = False


    def on_checkbutton_toggled(self, checkbutton, path):

        """Called from a callback in self.__init__().

        Respond when the user selects/deselects an item in the treeview.

        Args:

            checkbutton (Gtk.CheckButton): The widget clicked

            path (int): A number representing the widget's row

        """

        # The user has clicked on the checkbutton widget, so toggle the widget
        #   itself
        self.liststore[path][0] = not self.liststore[path][0]

        # Update IVs
        mini_dict = self.db_dict[self.liststore[path][4]]
        mini_dict['import_flag'] = self.liststore[path][0]


    def on_container_name_edited(self, widget, path, text):

        """Called from callback in self.setup_finish_page().

        Updates the name of a channel/playlist.

        Args:

            widget (Gtk.CellRendererText): The widget clicked

            path (int): Path to the treeview line that was edited

            text (str): The new contents of the cell

        """

        # Check the entered text is a valid name
        if text == '' \
        or re.search('^\s*$', text) \
        or not self.app_obj.check_container_name_is_legal(text):
            return

        # Update the column text
        self.liststore[path][2] = text

        # Update IVs
        mini_dict = self.db_dict[self.liststore[path][4]]
        mini_dict['name'] = text
        mini_dict['nickname'] = text


    def on_container_url_edited(self, widget, path, text):

        """Called from callback in self.setup_finish_page().

        Updates the URL of a channel/playlist.

        Args:

            widget (Gtk.CellRendererText): The widget clicked

            path (int): Path to the treeview line that was edited

            text (str): The new contents of the cell

        """

        # Check the entered text is a valid name
        if not utils.check_url(text):
            return

        # Update the column text
        self.liststore[path][3] = text

        # Update IVs
        mini_dict = self.db_dict[self.liststore[path][4]]
        mini_dict['source'] = text


class TutorialWizWin(GenericWizWin):

    """Python class for a 'wizard window' used to show a short tutorial.

    Args:

        app_obj (mainapp.TartubeApp): The main application object

    """


    # Standard class methods


    def __init__(self, app_obj):

        ignore_me = _(
            'TRANSLATOR\'S NOTE: Tutorial wizard window starts here.' \
            + ' In the menu, click Help > Show tutorial...'
        )

        Gtk.Window.__init__(self, title=_('Tartube Tutorial'))

        if self.is_duplicate(app_obj):
           return

        # IV list - class objects
        # -----------------------
        # The mainapp.TartubeApp object
        self.app_obj = app_obj


        # IV list - Gtk widgets
        # ---------------------
        self.grid = None                        # Gtk.Grid
        self.vbox = None                        # Gtk.VBox
        self.inner_grid = None                  # Gtk.Grid
        self.cancel_button = None               # Gtk.Button
        self.next_button = None                 # Gtk.Button
        self.prev_button = None                 # Gtk.Button


        # IV list - other
        # ---------------
        # Size (in pixels) of gaps between preference window widgets
        self.spacing_size = self.app_obj.default_spacing_size

        # List of 'pages' (widget layouts on self.inner_grid). Each item in the
        #   list is the function to call
        self.page_list = []                     # Set below
        # The number of the current page (the first is 0), matching an index in
        #   self.page_list
        self.current_page = 0

        # Standard length of text in the wizard window
        self.text_len = 70


        # Code
        # ----

        # Set the page list
        # N.B. If more pages are added, mainwin.MainWin.tutorial_page_count
        #   must be updated with the new page count!
        self.page_list = ['setup_start_page']
        for i in range(1, self.app_obj.main_win_obj.tutorial_page_count):
            self.page_list.append('setup_page_' + str(i))

        self.page_list.append('setup_finish_page')

        # Set up the wizard window
        self.setup()


    # Public class methods


#   def is_duplicate():         # Inherited from GenericWizWin


    def setup(self):

        """Called by self.__init__().

        Sets up the wizard window when it opens.
        """

        # Set the non-default size for this wizard window
        self.set_default_size(750, 575)

        # Set the window's Gtk icon list
        self.set_icon_list(self.app_obj.main_win_obj.win_pixbuf_list)

        # Set up main widgets
        self.setup_grid()
        self.setup_button_strip()

        # Set up the first page (a widget layout on self.inner_grid)
        self.setup_page()

        # Procedure complete
        self.show_all()

        # Inform the main window of this window's birth (so that Tartube
        #   doesn't allow an operation to start until all configuration windows
        #   have closed)
        self.app_obj.main_win_obj.add_child_window(self)

        # Add a callback so we can inform the main window of this window's
        #   destruction
        self.connect('destroy', self.close)


#   def setup_grid():           # Inherited from GenericWizWin


#   def setup_button_strip():   # Inherited from GenericWizWin


#   def setup_page():           # Inherited from GenericWizWin


#   def convert_next_button():  # Inherited from GenericWizWin


#   def apply_changes():        # Inherited from GenericWizWin


#   def cancel_changes():       # Inherited from GenericWizWin


#   def close():                # Inherited from GenericWizWin


    # (Setup pages)


    def setup_start_page(self):

        """Called by self.setup_page().

        Sets up the widget layout for a page.
        """

        self.add_image(
            self.app_obj.main_win_obj.icon_dict['system_icon'],
            0, 0, 1, 1,
        )

        self.add_label(
            '<span font_size="large" font_weight="bold">' \
            + _('Tartube Tutorial') + '</span>',
            0, 1, 1, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 2, 1, 1)

        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(
                _('This tutorial will take about five minutes.'),
                self.text_len,
            ) + '</span>',
            0, 4, 1, 1,
        )

        self.add_label(
            '<span font_size="large"  style="italic">' \
            + utils.tidy_up_long_string(
                _('Click the <b>Next</b> button to get started.'),
                self.text_len,
            ) + '</span>',
            0, 5, 1, 1,
        )


    def setup_page_1(self):

        """Called by self.setup_page().

        Sets up the widget layout for a page.
        """

        self.add_image(
            self.app_obj.main_win_obj.icon_dict['tutorial1'],
            0, 0, 1, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 1, 1, 1)

        msg = _('Click the \'Add a new channel\' button.')
        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(msg, self.text_len) + '</span>',
            0, 2, 1, 1,
        )


    def setup_page_2(self):

        """Called by self.setup_page().

        Sets up the widget layout for a page.
        """

        self.add_image(
            self.app_obj.main_win_obj.icon_dict['tutorial2'],
            0, 0, 1, 1,
        )

        msg = _(
            'In the first box, give the channel a name. In the second box,' \
            + ' paste the channel\'s URL.',
        )
        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(msg, self.text_len) + '</span>',
            0, 1, 1, 1,
        )


    def setup_page_3(self):

        """Called by self.setup_page().

        Sets up the widget layout for a page.
        """

        self.add_image(
            self.app_obj.main_win_obj.icon_dict['tutorial3'],
            0, 0, 1, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 1, 1, 1)

        msg = _('Your new channel is added to Tartube\'s database.')
        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(msg, self.text_len) + '</span>',
            0, 2, 1, 1,
        )


    def setup_page_4(self):

        """Called by self.setup_page().

        Sets up the widget layout for a page.
        """

        self.add_image(
            self.app_obj.main_win_obj.icon_dict['tutorial4'],
            0, 0, 1, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 1, 1, 1)

        msg = _(
            'Click \'Check all\' to fetch a list of videos. Click \'Download' \
            + ' all\' to download the videos.',
        )
        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(msg, self.text_len) + '</span>',
            0, 2, 1, 1,
        )


    def setup_page_5(self):

        """Called by self.setup_page().

        Sets up the widget layout for a page.
        """

        self.add_image(
            self.app_obj.main_win_obj.icon_dict['tutorial5'],
            0, 0, 1, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 1, 1, 1)

        msg = _('As well as adding channels, you can add playlists.')
        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(msg, self.text_len) + '</span>',
            0, 2, 1, 1,
        )


    def setup_page_6(self):

        """Called by self.setup_page().

        Sets up the widget layout for a page.
        """

        self.add_image(
            self.app_obj.main_win_obj.icon_dict['tutorial6'],
            0, 0, 1, 1,
        )

#        # (Empty label for spacing)
#        self.add_empty_label(0, 1, 1, 1)

        msg = _(
            'If you want to add videos individually, click the \'Add new' \
            + ' videos\' button. They will be downloaded to the' \
            + ' \'Unsorted Videos\' folder.' \
        )
        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(msg, self.text_len) + '</span>',
            0, 1, 1, 1,
        )


    def setup_page_7(self):

        """Called by self.setup_page().

        Sets up the widget layout for a page.
        """

        self.add_image(
            self.app_obj.main_win_obj.icon_dict['tutorial7'],
            0, 0, 1, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 1, 1, 1)

        msg = _(
            'You can organise your videos into folders. Click the \'Add a' \
            + ' new folder\' button.',
        )
        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(msg, self.text_len) + '</span>',
            0, 2, 1, 1,
        )


    def setup_page_8(self):

        """Called by self.setup_page().

        Sets up the widget layout for a page.
        """

        self.add_image(
            self.app_obj.main_win_obj.icon_dict['tutorial8'],
            0, 0, 1, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 1, 1, 1)

        msg = _(
            'You can drag-and-drop channels and playlists into the right' \
            + ' folder.',
        )
        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(msg, self.text_len) + '</span>',
            0, 2, 1, 1,
        )


    def setup_page_9(self):

        """Called by self.setup_page().

        Sets up the widget layout for a page.
        """

        self.add_image(
            self.app_obj.main_win_obj.icon_dict['tutorial9'],
            0, 0, 1, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 1, 1, 1)

        msg = _(
            'You can check the progress of your downloads in the' \
            + ' \'Progress\' tab.',
        )
        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(msg, self.text_len) + '</span>',
            0, 2, 1, 1,
        )


    def setup_page_10(self):

        """Called by self.setup_page().

        Sets up the widget layout for a page.
        """

        self.add_image(
            self.app_obj.main_win_obj.icon_dict['tutorial10'],
            0, 0, 1, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 1, 1, 1)

        msg = _('Advanced users can see more detail in the \'Output\' tab.')
        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(msg, self.text_len) + '</span>',
            0, 2, 1, 1,
        )


    def setup_page_11(self):

        """Called by self.setup_page().

        Sets up the widget layout for a page.
        """

        self.add_image(
            self.app_obj.main_win_obj.icon_dict['tutorial11'],
            0, 0, 1, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 1, 1, 1)

        msg = _(
            'A summary of any problems will appear in the' \
            + ' \'Errors / Warnings\' tab.',
        )
        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(msg, self.text_len) + '</span>',
            0, 2, 1, 1,
        )


    def setup_page_12(self):

        """Called by self.setup_page().

        Sets up the widget layout for a page.
        """

        self.add_image(
            self.app_obj.main_win_obj.icon_dict['tutorial12'],
            0, 0, 1, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 1, 1, 1)

        msg = _(
            'If you don\'t want to build a database of videos, then you' \
            + ' can use the \'Classic Mode\' tab.',
        )
        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(msg, self.text_len) + '</span>',
            0, 2, 1, 1,
        )


    def setup_page_13(self):

        """Called by self.setup_page().

        Sets up the widget layout for a page.
        """

        self.add_image(
            self.app_obj.main_win_obj.icon_dict['tutorial13'],
            0, 0, 1, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 1, 1, 1)

        msg = _(
            'In the box at the top, paste the URLs of videos, channels' \
            + ' and playlists.',
        )
        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(msg, self.text_len) + '</span>',
            0, 2, 1, 1,
        )


    def setup_page_14(self):

        """Called by self.setup_page().

        Sets up the widget layout for a page.
        """

        self.add_image(
            self.app_obj.main_win_obj.icon_dict['tutorial14'],
            0, 0, 1, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 1, 1, 1)

        msg = _('Set the download folder.')
        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(msg, self.text_len) + '</span>',
            0, 2, 1, 1,
        )


    def setup_page_15(self):

        """Called by self.setup_page().

        Sets up the widget layout for a page.
        """

        self.add_image(
            self.app_obj.main_win_obj.icon_dict['tutorial15'],
            0, 0, 1, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 1, 1, 1)

        msg = _('Choose the video or audio format.')
        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(msg, self.text_len) + '</span>',
            0, 2, 1, 1,
        )


    def setup_page_16(self):

        """Called by self.setup_page().

        Sets up the widget layout for a page.
        """

        self.add_image(
            self.app_obj.main_win_obj.icon_dict['tutorial16'],
            0, 0, 1, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 1, 1, 1)

        msg = _('Click the \'Add URLs\' button.')
        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(msg, self.text_len) + '</span>',
            0, 2, 1, 1,
        )


    def setup_page_17(self):

        """Called by self.setup_page().

        Sets up the widget layout for a page.
        """

        self.add_image(
            self.app_obj.main_win_obj.icon_dict['tutorial17'],
            0, 0, 1, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 1, 1, 1)

        msg = _(
            'If you like, you can now set up more downloads using' \
            + ' a different download folder and/or format.',
        )
        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(msg, self.text_len) + '</span>',
            0, 2, 1, 1,
        )


    def setup_page_18(self):

        """Called by self.setup_page().

        Sets up the widget layout for a page.
        """

        self.add_image(
            self.app_obj.main_win_obj.icon_dict['tutorial18'],
            0, 0, 1, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 1, 1, 1)

        msg = _('When you\'re ready, click the \'Download all\' button.')
        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(msg, self.text_len) + '</span>',
            0, 2, 1, 1,
        )


    def setup_page_19(self):

        """Called by self.setup_page().

        Sets up the widget layout for a page.
        """

        self.add_image(
            self.app_obj.main_win_obj.icon_dict['tutorial19'],
            0, 0, 1, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 1, 1, 1)

        msg = _(
            'Download options changes the way your videos are downloaded.' \
            + ' To see them, click \'Edit > General download options...\'',
        )
        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(msg, self.text_len) + '</span>',
            0, 2, 1, 1,
        )


    def setup_page_20(self):

        """Called by self.setup_page().

        Sets up the widget layout for a page.
        """

        self.add_image(
            self.app_obj.main_win_obj.icon_dict['tutorial20'],
            0, 0, 1, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 1, 1, 1)

        msg = _(
            'A completely different set of download options is used in the ' \
            + ' the \'Classic Mode\' tab. Click the menu button in the' \
            + ' top-right corner.',
        )
        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(msg, self.text_len) + '</span>',
            0, 2, 1, 1,
        )


    def setup_page_21(self):

        """Called by self.setup_page().

        Sets up the widget layout for a page.
        """

        self.add_image(
            self.app_obj.main_win_obj.icon_dict['tutorial21'],
            0, 0, 1, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 1, 1, 1)

        msg = _(
            'The new window has many options you can try. For example, to' \
            + ' download videos as .mp3 files, click the \'Convert\' tab.',
        )
        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(msg, self.text_len) + '</span>',
            0, 2, 1, 1,
        )


    def setup_page_22(self):

        """Called by self.setup_page().

        Sets up the widget layout for a page.
        """

        self.add_image(
            self.app_obj.main_win_obj.icon_dict['tutorial22'],
            0, 0, 1, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 1, 1, 1)

        msg = _(
            'Advanced users can specify download options directly,' \
            + ' overriding settings anywhere else in this window.',
        )
        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(msg, self.text_len) + '</span>',
            0, 2, 1, 1,
        )


    def setup_page_23(self):

        """Called by self.setup_page().

        Sets up the widget layout for a page.
        """

        self.add_image(
            self.app_obj.main_win_obj.icon_dict['tutorial23'],
            0, 0, 1, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 1, 1, 1)

        msg = _(
            'You can apply a separate set of download options to a channel.' \
            + ' Right-click it, and select \'Downloads > Apply download' \
            + ' options...\'',
        )
        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(msg, self.text_len) + '</span>',
            0, 2, 1, 1,
        )


    def setup_page_24(self):

        """Called by self.setup_page().

        Sets up the widget layout for a page.
        """

        self.add_image(
            self.app_obj.main_win_obj.icon_dict['tutorial24'],
            0, 0, 1, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 1, 1, 1)

        msg = _(
            'The icon changes to remind you that the channel has its own' \
            + ' set of download options.',
        )
        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(msg, self.text_len) + '</span>',
            0, 2, 1, 1,
        )


    def setup_page_25(self):

        """Called by self.setup_page().

        Sets up the widget layout for a page.
        """

        self.add_image(
            self.app_obj.main_win_obj.icon_dict['tutorial25'],
            0, 0, 1, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 1, 1, 1)

        msg = _(
            'If you add download options to a folder, they apply to all' \
            + ' videos, channels and playlists inside that folder.',
        )
        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(msg, self.text_len) + '</span>',
            0, 2, 1, 1,
        )


    def setup_page_26(self):

        """Called by self.setup_page().

        Sets up the widget layout for a page.
        """

        self.add_image(
            self.app_obj.main_win_obj.icon_dict['tutorial26'],
            0, 0, 1, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 1, 1, 1)

        msg = _(
            'yt-dlp is updated frequently, so don\'t forget to download' \
            + ' the updates. Click \'Operations > Update yt-dlp\'.',
        )
        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(msg, self.text_len) + '</span>',
            0, 2, 1, 1,
        )


    def setup_page_27(self):

        """Called by self.setup_page().

        Sets up the widget layout for a page.
        """

        self.add_image(
            self.app_obj.main_win_obj.icon_dict['tutorial27'],
            0, 0, 1, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 1, 1, 1)

        msg = _(
            'More help is available on our website. Click \'Help >' \
            + ' Go to website\'.',
        )
        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(msg, self.text_len) + '</span>',
            0, 2, 1, 1,
        )


    def setup_finish_page(self):

        """Called by self.setup_page().

        Sets up the widget layout for a page.
        """


        self.add_image(
            self.app_obj.main_win_obj.icon_dict['system_icon'],
            0, 0, 1, 1,
        )

        self.add_label(
            '<span font_size="large" font_weight="bold">' \
            + _('Tartube Tutorial') + '</span>',
            0, 1, 1, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 2, 1, 1)

        self.add_label(
            '<span font_size="large" style="italic">' \
            + utils.tidy_up_long_string(
                _('That\'s the end of the tutorial.'),
                self.text_len,
            ) + '</span>',
            0, 3, 1, 1,
        )

        # (Empty label for spacing)
        self.add_empty_label(0, 4, 1, 1)

        self.add_label(
            '<span font_size="large"  style="italic">' \
            + utils.tidy_up_long_string(
                _(
                    'You can read it again at any time by clicking' \
                    + ' \'Help > Show tutorial...\' in Tartube\'s menu.',
                ),
                self.text_len,
            ) + '</span>',
            0, 5, 1, 1,
        )
