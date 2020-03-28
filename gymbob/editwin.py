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


"""Edit window classes."""


# Import Gtk modules
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, GdkPixbuf


# Import other modules
import re


# Import our modules
# ...


# Classes


class ProgEditWin(Gtk.Window):

    """Python class for an 'edit window' to modify values in a gymprog.GymProg
    object.

    Args:

        app_obj (mainapp.TartubeApp): The main application object

        edit_obj (gymprog.GymProg): The object whose attributes will be edited
            in this window

    """


    def __init__(self, app_obj, edit_obj):

        Gtk.Window.__init__(self, title='Edit \'' + edit_obj.name + '\'')

        # IV list - class objects
        # -----------------------
        # The mainapp.GymBobApp object
        self.app_obj = app_obj
        # The gymprog.GymProg object being edited
        self.edit_obj = edit_obj


        # IV list - Gtk widgets
        # ---------------------
        self.main_grid = None                   # Gtk.Grid
        self.reset_button = None                # Gtk.Button
        self.apply_button = None                # Gtk.Button
        self.ok_button = None                   # Gtk.Button
        self.cancel_button = None               # Gtk.Button

        self.treeview = None                    # Gtk.TreeView
        self.liststore = None                   # Gtk.ListStore


        # IV list - other
        # ---------------
        # Size (in pixels) of gaps between edit window widgets
        self.spacing_size = self.app_obj.default_spacing_size

        # When the user changes a value, it is not applied to self.edit_obj
        #   immediately; instead, it is stored temporarily in this dictionary
        # If the user clicks the 'OK' or 'Apply' buttons at the bottom of the
        #   window, the changes are applied to self.edit_obj
        # If the user clicks the 'Reset' or 'Cancel' buttons, the dictionary
        #   is emptied and the changes are lost
        # The key-value pairs in the dictionary correspond directly to the
        #   names of attributes, and their values in self.edit_obj
        # Key-value pairs are added to this dictionary whenever the user makes
        #   a change (so if no changes are made when the window is closed, the
        #   dictionary will still be empty)
        self.edit_dict = {}


        # Code
        # ----

        # Set up the edit window
        self.setup()


    # Public class methods


    def setup(self):

        """Called by self.__init__().

        Sets up the edit window when it opens.
        """

        # Set the default window size
        self.set_default_size(
            self.app_obj.edit_win_width,
            self.app_obj.edit_win_height,
        )

        # Set the window's Gtk icon list
        self.set_icon_list(self.app_obj.main_win_obj.icon_pixbuf_list)

        # Set up the window's containing box
        self.main_grid = Gtk.Grid()
        self.add(self.main_grid)

        # Set up main widgets
        self.setup_tab()
        self.setup_button_strip()
        self.setup_gap()

        # Procedure complete
        self.show_all()

        # Inform the main window of this window's birth (so that GymBox doesn't
        #   the clock to start until all configuration windows have closed)
        self.app_obj.main_win_obj.add_child_window(self)
        # Add a callback so we can inform the main window of this window's
        #   destruction
        self.connect('destroy', self.close)


    def setup_tab(self):

        """Called by self.setup().

        Sets up all widgets (except the button strip at the bottom of the
        window).
        """

        mini_grid = Gtk.Grid()
        self.main_grid.attach(mini_grid, 0, 0, 1, 1)
        mini_grid.set_border_width(self.spacing_size)
        mini_grid.set_column_spacing(self.spacing_size)
        mini_grid.set_row_spacing(self.spacing_size)

        # Add a treeview
        frame = Gtk.Frame()
        mini_grid.attach(frame, 0, 0, 5, 1)
        frame.set_hexpand(True)
        frame.set_vexpand(True)

        scrolled = Gtk.ScrolledWindow()
        frame.add(scrolled)
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self.treeview = Gtk.TreeView()
        scrolled.add(self.treeview)
        self.treeview.set_headers_visible(True)

        for i, column_title in enumerate( ['#', 'Time', 'Message', 'Sound'] ):

            renderer_text = Gtk.CellRendererText()
            column_text = Gtk.TreeViewColumn(
                column_title,
                renderer_text,
                text=i,
            )
            self.treeview.append_column(column_text)

        self.treeview_reset()
        self.treeview_refill()

        # Add editing widgets beneath the treeview
        label = Gtk.Label('Time (in seconds)')
        mini_grid.attach(label, 0, 1, 1, 1)

        entry = Gtk.Entry()
        mini_grid.attach(entry, 1, 1, 2, 1)
        entry.set_hexpand(True)
        entry.set_max_width_chars(4)

        label2 = Gtk.Label('Message')
        mini_grid.attach(label2, 0, 2, 1, 1)

        entry2 = Gtk.Entry()
        mini_grid.attach(entry2, 1, 2, 4, 1)
        entry2.set_hexpand(True)

        label3 = Gtk.Label('Sound (optional)')
        mini_grid.attach(label3, 0, 3, 1, 1)

        combostore = Gtk.ListStore(str)
        combostore.append('')
        for sound_file in self.app_obj.sound_list:
            combostore.append( [sound_file] )

        combo = Gtk.ComboBox.new_with_model(combostore)
        mini_grid.attach(combo, 1, 3, 2, 1)
        renderer_text = Gtk.CellRendererText()
        combo.pack_start(renderer_text, True)
        combo.add_attribute(renderer_text, 'text', 0)
        combo.set_entry_text_column(0)
        combo.set_active(0)

        button = Gtk.Button('Add message')
        mini_grid.attach(button, 0, 4, 1, 1)
        button.connect(
            'clicked',
            self.on_button_add_clicked,
            entry,
            entry2,
            combo,
        )

        button2 = Gtk.Button('Update message')
        mini_grid.attach(button2, 1, 4, 1, 1)
        button2.connect(
            'clicked',
            self.on_button_update_clicked,
            entry,
            entry2,
            combo,
        )

        button3 = Gtk.Button('Delete message')
        mini_grid.attach(button3, 2, 4, 1, 1)
        button3.connect('clicked', self.on_button_delete_clicked)

        button4 = Gtk.Button('Move up')
        mini_grid.attach(button4, 3, 4, 1, 1)
        button4.connect('clicked', self.on_button_move_up_clicked)

        button5 = Gtk.Button('Move down')
        mini_grid.attach(button5, 4, 4, 1, 1)
        button5.connect('clicked', self.on_button_move_down_clicked)


    def setup_button_strip(self):

        """Called by self.setup().

        Creates a strip of buttons at the bottom of the window. Any changes the
        user has made are applied by clicking the 'OK' or 'Apply' buttons, and
        cancelled by using the 'Reset' or 'Cancel' buttons.

        The window is closed by using the 'OK' and 'Cancel' buttons.
        """

        hbox = Gtk.HBox()
        self.main_grid.attach(hbox, 0, 1, 1, 1)

        # 'Reset' button
        self.reset_button = Gtk.Button('Reset')
        hbox.pack_start(self.reset_button, False, False, self.spacing_size)
        self.reset_button.get_child().set_width_chars(10)
        self.reset_button.set_tooltip_text(
            'Reset changes without closing the window',
        );
        self.reset_button.connect('clicked', self.on_button_reset_clicked)

        # 'Apply' button
        self.apply_button = Gtk.Button('Apply')
        hbox.pack_start(self.apply_button, False, False, self.spacing_size)
        self.apply_button.get_child().set_width_chars(10)
        self.apply_button.set_tooltip_text(
            'Apply changes without closing the window',
        );
        self.apply_button.connect('clicked', self.on_button_apply_clicked)

        # 'OK' button
        self.ok_button = Gtk.Button('OK')
        hbox.pack_end(self.ok_button, False, False, self.spacing_size)
        self.ok_button.get_child().set_width_chars(10)
        self.ok_button.set_tooltip_text('Apply changes');
        self.ok_button.connect('clicked', self.on_button_ok_clicked)

        # 'Cancel' button
        self.cancel_button = Gtk.Button('Cancel')
        hbox.pack_end(self.cancel_button, False, False, self.spacing_size)
        self.cancel_button.get_child().set_width_chars(10)
        self.cancel_button.set_tooltip_text('Cancel changes');
        self.cancel_button.connect(
            'clicked',
            self.on_button_cancel_clicked,
        )


    def setup_gap(self):

        """Called by self.setup().

        Adds an empty box beneath the button strip for aesthetic purposes.
        """

        hbox = Gtk.HBox()
        self.main_grid.attach(hbox, 0, 2, 1, 1)
        hbox.set_border_width(self.spacing_size)


    def retrieve_val(self, name):

        """Can be called by anything.

        Any changes the user has made are temporarily stored in self.edit_dict.

        Each key corresponds to an attribute in the object being edited,
        self.edit_obj.

        If 'name' exists as a key in that dictionary, retrieve the
        corresponding value and return it. Otherwise, the user hasn't yet
        modified the value, so retrieve directly from the attribute in the
        object being edited.

        Args:

            name (str): The name of the attribute in the object being edited

        Returns:

            The original or modified value of that attribute.

        """

        if name in self.edit_dict:
            return self.edit_dict[name]
        else:
            attrib = getattr(self.edit_obj, name)
            return attrib.copy()


    def treeview_reset(self):

        """Called by self.setup_tab() and several callback functions.

        Creates a model for the Gtk.TreeView to use, replacing any previous
        model in use.
        """

        self.liststore = Gtk.ListStore(int, int, str, str)
        self.treeview.set_model(self.liststore)


    def treeview_refill(self):

        """Called by self.setup_tab() and several callback functions, usually
        after a call to self.treeview_reset().

        Fills the Gtk.Treeview with data.
        """

        msg_group_list = self.retrieve_val('msg_group_list')

        count = 0
        for mini_list in msg_group_list:

            count += 1
            mod_list = mini_list.copy()
            mod_list.insert(0, count)
            self.liststore.append(mod_list)


    def check_entries(self, entry, entry2):

        """Called by self.on_button_add_clicked() and
        .on_button_update_clicked().

        Extracts the value of the two Gtk.Entrys. If either value is invalid,
        displays an error message.

        Args:

            entry, entry2 (Gtk.Entry): The entry boxes to check

        Return values:

            time (int), msg (str): The contents of the boxes, or (None, None)
                if either value is invalid

        """

        time = entry.get_text()
        msg = entry2.get_text()

        if time == '' or not re.search('^\d+$', time):

            msg_dialogue_win = Gtk.MessageDialog(
                self,
                0,
                Gtk.MessageType.ERROR,
                Gtk.ButtonsType.OK,
                'Invalid time value (must\nbe an integer in seconds)',
            )
            msg_dialogue_win.run()
            msg_dialogue_win.destroy()
            return None, None

#        elif msg == '':
#
#            msg_dialogue_win = Gtk.MessageDialog(
#                self,
#                0,
#                Gtk.MessageType.ERROR,
#                Gtk.ButtonsType.OK,
#                'Invalid message (must\ncontain some characters)',
#            )
#            msg_dialogue_win.run()
#            msg_dialogue_win.destroy()
#            return None, None

        else:

            return time, msg


    def apply_changes(self):

        """Called by self.on_button_ok_clicked() and
        self.on_button_apply_clicked().

        Any changes the user has made are temporarily stored in self.edit_dict.
        Apply to those changes to the object being edited.
        """

        # Apply any changes the user has made
        for key in self.edit_dict.keys():
            setattr(self.edit_obj, key, self.edit_dict[key])

        # The changes can now be cleared
        self.edit_dict = {}

        # Save the programme file
        self.app_obj.save_prog(self.edit_obj)


    def close(self, also_self):

        """Called from callback in self.setup().

        Inform the main window that this window is closing.

        Args:

            also_self (editwin.ProgEditWin): Another copy of self

        """

        self.app_obj.main_win_obj.del_child_window(self)


    # (Callbacks)


    def on_button_add_clicked(self, button, entry, entry2, combo):

        """Called from a callback in self.setup_tab().

        Adds a message to the treeview.

        Args:

            button (Gtk.Button): The widget clicked

            entry, entry2 (Gtk.Entry): The contents of these entry boxes are
                aded to the treeview (and the gymprog.GymProg programme)

            combo (Gtk.ComboBox): The contents of this combobox is added to the
                treeview

        """

        time, msg = self.check_entries(entry, entry2)

        tree_iter = combo.get_active_iter()
        model = combo.get_model()
        filename = model[tree_iter][0]

        if time is not None:

            msg_group_list = self.retrieve_val('msg_group_list')

            # mini_list is in the form
            #   (time_in_seconds, message, optional_sound_file)
            mini_list = [int(time), str(msg), str(filename)]
            msg_group_list.append(mini_list)
            self.edit_dict['msg_group_list'] = msg_group_list

            mini_list2 = [
                len(msg_group_list), int(time), str(msg), str(filename),
            ]
            self.liststore.append(mini_list2)


    def on_button_apply_clicked(self, button):

        """Called from a callback in self.setup_button_strip().

        Applies any changes made by the user, but doesn't close the window.

        Args:

            button (Gtk.Button): The widget clicked

        """

        # Apply any changes the user has made
        self.apply_changes()


    def on_button_cancel_clicked(self, button):

        """Called from a callback in self.setup_button_strip().

        Destroys any changes made by the user and closes the window.

        Args:

            button (Gtk.Button): The widget clicked

        """

        # Destroy the window
        self.destroy()


    def on_button_delete_clicked(self, button):

        """Called from a callback in self.setup_tab().

        Deletes a message from the treeview.

        Args:

            button (Gtk.Button): The widget clicked

        """

        selection = self.treeview.get_selection()
        (model, iter) = selection.get_selected()
        if iter is None:

            # Nothing selected
            return

        row_num = model[iter][0]

        msg_group_list = self.retrieve_val('msg_group_list')
        count = 0
        mod_list = []

        # mini_list is in the form
        #   (time_in_seconds, message, optional_sound_file)
        for mini_list in msg_group_list:

            count += 1
            if count != row_num:
                mod_list.append(mini_list)

        self.edit_dict['msg_group_list'] = mod_list

        self.treeview_reset()
        self.treeview_refill()


    def on_button_ok_clicked(self, button):

        """Called from a callback in self.setup_button_strip().

        Destroys any changes made by the user and then closes the window.

        Args:

            button (Gtk.Button): The widget clicked

        """

        # Apply any changes the user has made
        self.apply_changes()

        # Destroy the window
        self.destroy()


    def on_button_move_down_clicked(self, button):

        """Called from a callback in self.setup_tab().

        Moves a message one place down in the treeview.

        Args:

            button (Gtk.Button): The widget clicked

        """

        selection = self.treeview.get_selection()
        (model, iter) = selection.get_selected()
        if iter is None:

            # Nothing selected
            return

        row_num = model[iter][0]
        msg_group_list = self.retrieve_val('msg_group_list')

        if row_num < len(msg_group_list):

            count = 0
            mod_list = []

            # mini_list is in the form
            #   (time_in_seconds, message, optional_sound_file)
            for mini_list in msg_group_list:

                count += 1
                if count != row_num:
                    mod_list.append(mini_list)
                else:
                    insert_list = mini_list.copy()

            mod_list.insert(row_num, insert_list)

            self.edit_dict['msg_group_list'] = mod_list

            self.treeview_reset()
            self.treeview_refill()

            selection = self.treeview.get_selection()
            selection.select_path(row_num)


    def on_button_move_up_clicked(self, button):

        """Called from a callback in self.setup_tab().

        Moves a message one place up in the treeview.

        Args:

            button (Gtk.Button): The widget clicked

        """

        selection = self.treeview.get_selection()
        (model, iter) = selection.get_selected()
        if iter is None:

            # Nothing selected
            return

        row_num = model[iter][0]
        msg_group_list = self.retrieve_val('msg_group_list')

        if row_num > 1:

            count = 0
            mod_list = []

            # mini_list is in the form
            #   (time_in_seconds, message, optional_sound_file)
            for mini_list in msg_group_list:

                count += 1
                if count != row_num:
                    mod_list.append(mini_list)
                else:
                    insert_list = mini_list.copy()

            mod_list.insert(row_num - 2, insert_list)

            self.edit_dict['msg_group_list'] = mod_list

            self.treeview_reset()
            self.treeview_refill()

            selection = self.treeview.get_selection()
            selection.select_path(row_num - 2)


    def on_button_reset_clicked(self, button):

        """Called from a callback in self.setup_button_strip().

        Destroys any changes made by the user and updates the window, showing
        self.edit_obj's original values

        Args:

            button (Gtk.Button): The widget clicked

        """

        # Empty self.edit_dict, destroying any changes the user has made
        self.edit_dict = {}

        # Reset the treeview
        self.treeview_reset()
        self.treeview_refill()

        # Render the changes
        self.show_all()


    def on_button_update_clicked(self, button, entry, entry2, combo):

        """Called from a callback in self.setup_tab().

        Updates the selected message in the treeview.

        Args:

            button (Gtk.Button): The widget clicked

            entry, entry2 (Gtk.Entry): The contents of these entry boxes are
                aded to the treeview, updating the selected line (and the
                gymprog.GymProg programme)

            combo (Gtk.ComboBox): The contents of this combobox is added to the
                treeview

        """

        selection = self.treeview.get_selection()
        (model, iter) = selection.get_selected()
        if iter is None:

            # Nothing selected
            return

        row_num = model[iter][0]
        time, msg = self.check_entries(entry, entry2)
        tree_iter = combo.get_active_iter()
        model = combo.get_model()
        filename = model[tree_iter][0]

        if time is not None:

            msg_group_list = self.retrieve_val('msg_group_list')

            # mini_list is in the form
            #   (time_in_seconds, message, optional_sound_file)
            mini_list = [int(time), str(msg), str(filename)]
            msg_group_list[row_num - 1] = mini_list
            self.edit_dict['msg_group_list'] = msg_group_list

            self.treeview_reset()
            self.treeview_refill()
