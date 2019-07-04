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


"""Configuration window classes."""


# Import Gtk modules
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, GdkPixbuf


# Import other modules
import os


# Import our modules
import __main__
from . import formats
from . import mainapp
from . import media
from . import utils


# Classes


class GenericConfigWin(Gtk.Window):

    """Generic Python class for windows in which the user can modify various
    settings.


    Inherited by two types of windows - 'preference windows' (in which changes
    are applied immediately), and 'edit window' (in which changes are stored
    temporarily, and only applied once the user has finished making changes.
    """


    # Standard class methods


#   def __init__():             # Provided by child object


    # Public class methods


    def setup(self):

        """Called by self.__init__().

        Sets up the config window when it opens.
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
        self.setup_notebook()
        self.setup_button_strip()
        self.setup_gap()

        # Set up tabs
        self.setup_tabs()

        # Procedure complete
        self.show_all()

        # Inform the main window of this window's birth (so that Tartube
        #   doesn't allow a download/update/refresh operation to start until
        #   all configuration windows have closed)
        self.app_obj.main_win_obj.add_child_window(self)
        # Add a callback so we can inform the main window of this window's
        #   destruction
        self.connect('destroy', self.close)


    def setup_grid(self):

        """Called by self.setup().

        Sets up a Gtk.Grid, on which a notebook and a button strip will be
        placed. (Each of the notebook's tabs also has its own Gtk.Grid.)
        """

        self.grid = Gtk.Grid()
        self.add(self.grid)


    def setup_notebook(self):

        """Called by self.setup().

        Sets up a Gtk.Notebook, after which self.setup_tabs() is called to fill
        it with tabs.
        """

        self.notebook = Gtk.Notebook()
        self.grid.attach(self.notebook, 0, 1, 1, 1)
        self.notebook.set_border_width(self.spacing_size)


    def add_notebook_tab(self, name):

        """Called by various functions in the child edit/preference window.

        Adds a tab to the main Gtk.Notebook, creating a Gtk.Grid inside it, on
        which the calling function can more widgets.

        Args:

            name (string): The name of the tab

        Returns:

            The tab created (in the form of a Gtk.Box) and its Gtk.Grid.

        """

        tab = Gtk.Box()
        self.notebook.append_page(tab, Gtk.Label.new_with_mnemonic(name))
        tab.set_hexpand(True)
        tab.set_vexpand(True)
        tab.set_border_width(self.spacing_size)

        grid = Gtk.Grid()
        tab.add(grid)
        grid.set_border_width(self.spacing_size)
        grid.set_column_spacing(self.spacing_size)
        grid.set_row_spacing(self.spacing_size)

        return tab, grid


#   def setup_button_strip():   # Provided by child object


    def setup_gap(self):

        """Called by self.setup().

        Adds an empty box beneath the button strip for aesthetic purposes.
        """

        hbox = Gtk.HBox()
        self.grid.attach(hbox, 0, 3, 1, 1)
        hbox.set_border_width(self.spacing_size)


    def close(self, also_self):

        """Called from callback in self.setup().

        Inform the main window that this window is closing.

        Args:

            also_self (an object inheriting from config.GenericConfigWin):
                another copy of self

        """

        self.app_obj.main_win_obj.del_child_window(self)


class GenericEditWin(GenericConfigWin):

    """Generic Python class for windows in which the user can modify various
    settings in a class object (such as a media.Video or an
    options.OptionsManager object).

    The modifications are stored temporarily, and only applied once the user
    has finished making changes.
    """


    # Standard class methods


#   def __init__():             # Provided by child object


    # Public class methods


#   def setup():                # Inherited from GenericConfigWin


#   def setup_grid():           # Inherited from GenericConfigWin


#   def setup_notebook():       # Inherited from GenericConfigWin


#   def add_notebook_tab():     # Inherited from GenericConfigWin


    def setup_button_strip(self):

        """Called by self.setup().

        Creates a strip of buttons at the bottom of the window. Any changes the
        user has made are applied by clicking the 'OK' or 'Apply' buttons, and
        cancelled by using the 'Reset' or 'Cancel' buttons.

        The window is closed by using the 'OK' and 'Cancel' buttons.

        If self.multi_button_flag is True, only the 'OK' button is created.
        """

        hbox = Gtk.HBox()
        self.grid.attach(hbox, 0, 2, 1, 1)

        if self.multi_button_flag:

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

        if self.multi_button_flag:

            # 'Cancel' button
            self.cancel_button = Gtk.Button('Cancel')
            hbox.pack_end(self.cancel_button, False, False, self.spacing_size)
            self.cancel_button.get_child().set_width_chars(10)
            self.cancel_button.set_tooltip_text('Cancel changes');
            self.cancel_button.connect(
                'clicked',
                self.on_button_cancel_clicked,
            )


#   def setup_gap():            # Inherited from GenericConfigWin


    # (Non-widget functions)


    def apply_changes(self):

        """Called by self.on_button_ok_clicked() and
        self.on_button_apply_clicked().

        Any changes the user has made are temporarily stored in self.edit_dict.
        Apply to those changes to the object being edited.
        """

        # Apply any changes the user has made
        for key in self.edit_dict.keys():
            setattr(self.edit_obj, self.edit_dict[key])

        # The changes can now be cleared
        self.edit_dict = {}


    def reset_with_new_edit_obj(self, new_edit_obj):

        """At the moment, only called by
        mainapp.TartubeApp.reset_options_manager().

        Resets the object whose values are being edited in this window, i.e.
        self.edit_obj, to the specified object.

        Then redraws the window itself, as if the user had clicked the 'Reset'
        button at the bottom of the window. This makes new_edit_obj's IVs
        visible in the edit window, without the need to destroy the old one and
        replace it with a new one.

        Args:

            new_edit_obj (class): The replacement edit object

        """

        self.edit_obj = new_edit_obj

        # The rest of this function is copied from
        #   self.on_button_reset_clicked()

        # Remove all existing tabs from the notebook
        number = self.notebook.get_n_pages()
        if number:

            for count in range(0, number):
                self.notebook.remove_page(0)

        # Empty self.edit_dict, destroying any changes the user has made
        self.edit_dict = {}

        # Re-draw all the tabs
        self.setup_tabs()

        # Render the changes
        self.show_all()


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

            name (string): The name of the attribute in the object being
                edited

        Returns:

            The original or modified value of that attribute.

        """

        if name in self.edit_dict:
            return self.edit_dict[name]
        else:
            return getattr(self.edit_obj, name)


    # (Add widgets)


    def add_checkbutton(self, grid, text, prop, x, y, wid, hei):

        """Called by various functions in the child edit window.

        Adds a Gtk.CheckButton to the tab's Gtk.Grid.

        Args:

            grid (Gtk.Grid): The grid on which this widget will be placed

            text (string or None): The text to display in the checkbutton's
                label. No label is used if 'text' is an empty string or None

            prop (string or None): The name of the attribute in self.edit_obj
                whose value will be set to the contents of this widget. If
                None, no changes are made to self.edit_dict; it's up to the
                calling function to provide a .connect()

            x, y, wid, hei (int): Position on the grid at which the widget is
                placed

        Returns:

            The checkbutton widget created

        """

        checkbutton = Gtk.CheckButton()
        grid.attach(checkbutton, x, y, wid, hei)
        checkbutton.set_hexpand(True)
        if text is not None and text != '':
            checkbutton.set_label(text)

        if prop is not None:
            checkbutton.set_active(self.retrieve_val(prop))
            checkbutton.connect('toggled', self.on_checkbutton_toggled, prop)

        return checkbutton


    def add_combo(self, grid, combo_list, prop, x, y, wid, hei):

        """Called by various functions in the child edit window.

        Adds a simple Gtk.ComboBox to the tab's Gtk.Grid.

        Args:

            grid (Gtk.Grid): The grid on which this widget will be placed

            combo_list (list): A list of values to display in the combobox.
                This function expects a simple, one-dimensional list. For
                something more complex, see self.add_combo_with_data()

            prop (string or None): The name of the attribute in self.edit_obj
                whose value will be set to the contents of this widget. If
                None, no changes are made to self.edit_dict; it's up to the
                calling function to provide a .connect()

            x, y, wid, hei (int): Position on the grid at which the widget is
                placed

        Returns:

            The combobox widget created

        """

        store = Gtk.ListStore(str)
        for string in combo_list:
            store.append( [string] )

        combo = Gtk.ComboBox.new_with_model(store)
        grid.attach(combo, x, y, wid, hei)
        renderer_text = Gtk.CellRendererText()
        combo.pack_start(renderer_text, True)
        combo.add_attribute(renderer_text, 'text', 0)
        combo.set_entry_text_column(0)

        if prop is not None:
            val = self.retrieve_val(prop)
            index = combo_list.index(val)
            combo.set_active(index)

            combo.connect('changed', self.on_combo_changed, prop)

        return combo


    def add_combo_with_data(self, grid, combo_list, prop, x, y, wid, hei):

        """Called by various functions in the child edit window.

        Adds a more complex Gtk.ComboBox to the tab's Gtk.Grid. This function
        expects a list of values in the form

            [ [val1, val2], [val1, val2], ... ]

        The combobox displays the 'val1' values. If one of them is selected,
        the corresponding 'val2' is used to set the attribute described by
        'prop'.

        Args:

            grid (Gtk.Grid): The grid on which this widget will be placed

            combo_list (list): The list described above. For something more
                simple, see self.add_combo()

            prop (string or None): The name of the attribute in self.edit_obj
                whose value will be set to the contents of this widget. If
                None, no changes are made to self.edit_dict; it's up to the
                calling function to provide a .connect()

            x, y, wid, hei (int): Position on the grid at which the widget is
                placed

        Returns:

            The combobox widget created

        """

        store = Gtk.ListStore(str, str)

        index_list = []
        for mini_list in combo_list:
            store.append( [ mini_list[0], mini_list[1] ] )
            index_list.append(mini_list[1])

        combo = Gtk.ComboBox.new_with_model(store)
        grid.attach(combo, x, y, wid, hei)
        renderer_text = Gtk.CellRendererText()
        combo.pack_start(renderer_text, True)
        combo.add_attribute(renderer_text, 'text', 0)
        combo.set_entry_text_column(0)

        if prop is not None:
            val = self.retrieve_val(prop)
            index = index_list.index(val)
            combo.set_active(index)

            combo.connect('changed', self.on_combo_with_data_changed, prop)

        return combo


    def add_entry(self, grid, prop, x, y, wid, hei):

        """Called by various functions in the child edit window.

        Adds a Gtk.Entry to the tab's Gtk.Grid.

        Args:

            grid (Gtk.Grid): The grid on which this widget will be placed

            prop (string or None): The name of the attribute in self.edit_obj
                whose value will be set to the contents of this widget. If
                None, no changes are made to self.edit_dict; it's up to the
                calling function to provide a .connect()

            x, y, wid, hei (int): Position on the grid at which the widget is
                placed

        Returns:

            The entry widget created

        """

        entry = Gtk.Entry()
        grid.attach(entry, x, y, wid, hei)
        entry.set_hexpand(True)

        if prop is not None:
            value = self.retrieve_val(prop)
            if value is not None:
                entry.set_text(str(value))

            entry.connect('changed', self.on_entry_changed, prop)

        return entry


    def add_image(self, grid, image_path, x, y, wid, hei):

        """Called by various functions in the child edit window.

        Adds a Gtk.Image to the tab's Gtk.Grid.

        Args:

            grid (Gtk.Grid): The grid on which this widget will be placed

            image_path (string): Full path to the image file to load

            x, y, wid, hei (int): Position on the grid at which the widget is
                placed

        Returns:

            The image created

        """

        frame = Gtk.Frame()
        grid.attach(frame, x, y, wid, hei)

        image = Gtk.Image()
        frame.add(image)
        image.set_from_pixbuf(
            self.app_obj.file_manager_obj.load_to_pixbuf(image_path),
        )

        return image


    def add_label(self, grid, text, x, y, wid, hei):

        """Called by various functions in the child edit window.

        Adds a Gtk.Label to the tab's Gtk.Grid.

        Args:

            grid (Gtk.Grid): The grid on which this widget will be placed

            text (string): Pango markup displayed in the label

            x, y, wid, hei (int): Position on the grid at which the widget is
                placed

        Returns:

            The label widget created

        """

        label = Gtk.Label()
        grid.attach(label, x, y, wid, hei)
        label.set_markup(text)
        label.set_hexpand(True)
        label.set_alignment(0, 0.5)

        return label


    def add_radiobutton(self, grid, prev_button, text, prop, value, x, y, \
    wid, hei):

        """Called by various functions in the child edit window.

        Adds a Gtk.RadioButton to the tab's Gtk.Grid.

        Args:

            grid (Gtk.Grid): The grid on which this widget will be placed

            prev_button (Gtk.RadioButton or None): When this is the first
                radio button in the group, None. Otherwise, the previous
                radio button in the group. Use of this IV links the radio
                buttons together, ensuring that only one of them can be active
                at any time

            text (string or None): The text to display in the radiobutton's
                label. No label is used if 'text' is an empty string or None

            prop (string or None): The name of the attribute in self.edit_obj
                whose value will be set to the contents of this widget. If
                None, no changes are made to self.edit_dict; it's up to the
                calling function to provide a .connect()

            value (any): When this radiobutton becomes the active one, and if
                'prop' is not None, then 'prop' and 'value' are added as a new
                key-value pair to self.edit_dict

            x, y, wid, hei (int): Position on the grid at which the widget is
                placed

        Returns:

            The radiobutton widget created

        """

        radiobutton = Gtk.RadioButton.new_from_widget(prev_button)
        grid.attach(radiobutton, x, y, wid, hei)
        radiobutton.set_hexpand(True)
        if text is not None and text != '':
            radiobutton.set_label(text)

        if prop is not None:
            if value is not None and self.retrieve_val(prop) == value:
                radiobutton.set_active(True)

            radiobutton.connect(
                'toggled',
                self.on_radiobutton_toggled, prop, value,
            )

        return radiobutton


    def add_spinbutton(self, grid, min_val, max_val, step, prop, x, y, wid, \
    hei):

        """Called by various functions in the child edit window.

        Adds a Gtk.SpinButton to the tab's Gtk.Grid.

        Args:

            grid (Gtk.Grid): The grid on which this widget will be placed

            min_val (int): The minimum permitted in the spinbutton

            max_val (int or None): The maximum values permitted in the
                spinbutton. If None, this function assigns a very large maximum
                value (a billion)

            step (int): Clicking the up/down arrows in the spin button
                increments/decrements the value by this much

            prop (string or None): The name of the attribute in self.edit_obj
                whose value will be set to the contents of this widget. If
                None, no changes are made to self.edit_dict; it's up to the
                calling function to provide a .connect()

            x, y, wid, hei (int): Position on the grid at which the widget is
                placed

        Returns:

            The spinbutton widget created

        """

        # If the specified value of 'max_valu' was none, just use a very big
        #   number (as Gtk.SpinButton won't accept the None argument)
        if max_val is None:
            max_val = 1000000000

        spinbutton = Gtk.SpinButton.new_with_range(min_val, max_val, step)
        grid.attach(spinbutton, x, y, wid, hei)
        spinbutton.set_hexpand(False)

        if prop is not None:
            spinbutton.set_value(self.retrieve_val(prop))
            spinbutton.connect(
                'value-changed',
                self.on_spinbutton_changed,
                prop,
            )

        return spinbutton


    def add_textview(self, grid, prop, x, y, wid, hei):

        """Called by various functions in the child edit window.

        Adds a Gtk.TextView to the tab's Gtk.Grid. The contents of the textview
        are used as a single string (perhaps including newline characters) to
        set the value of a string attribute.

        Args:

            grid (Gtk.Grid): The grid on which this widget will be placed

            prop (string or None): The name of the attribute in self.edit_obj
                whose value will be set to the contents of this widget. The
                attribute can be an integer, string, list or tuple. If None, no
                changes are made to self.edit_dict; it's up to the calling
                function to provide a .connect()

            x, y, wid, hei (int): Position on the grid at which the widget is
                placed

        Returns:

            The textview and textbuffer widgets created

        """

        scrolled = Gtk.ScrolledWindow()
        grid.attach(scrolled, x, y, wid, hei)
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)

        frame = Gtk.Frame()
        scrolled.add_with_viewport(frame)

        textview = Gtk.TextView()
        frame.add(textview)

        textbuffer = textview.get_buffer()

        if prop is not None:
            value = self.retrieve_val(prop)
            if value is not None:
                if type(value) is list or type(value) is tuple:
                    textbuffer.set_text(str.join('\n', value))
                else:
                    textbuffer.set_text(str(value))

            textbuffer.connect('changed', self.on_textview_changed, prop)

        return textview, textbuffer


    def add_treeview(self, grid, x, y, wid, hei):

        """Called by various functions in the child edit window.

        Adds a Gtk.Treeview to the tab's Gtk.Grid. No callback function is
        created by this function; it's up to the calling code to supply one.

        Args:

            grid (Gtk.Grid): The grid on which this widget will be placed

            x, y, wid, hei (int): Position on the grid at which the widget is
                placed

        Returns:

            The treeview widget created

        """

        scrolled = Gtk.ScrolledWindow()
        grid.attach(scrolled, x, y, wid, hei)
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)

        frame = Gtk.Frame()
        scrolled.add_with_viewport(frame)

        treeview = Gtk.TreeView()
        frame.add(treeview)
        treeview.set_headers_visible(False)

        renderer_text = Gtk.CellRendererText()
        column_text = Gtk.TreeViewColumn(
            '',
            renderer_text,
            text=0,
        )
        treeview.append_column(column_text)

        liststore = Gtk.ListStore(str)
        treeview.set_model(liststore)

        return treeview, liststore


    # Callback class methods


    def on_button_apply_clicked(self, button):

        """Called from a callback in self.setup_button_strip().

        Applies any changes made by the user and re-draws the window's tabs,
        showing their new values.

        Args:

            button (Gtk.Button): The widget clicked

        """

        # Apply any changes the user has made
        self.apply_changes()

        # Remove all existing tabs from the notebook
        number = self.notebook.get_n_pages()
        if number:

            for count in range(0, number):
                self.notebook.remove_page(0)

        # Re-draw all the tabs
        self.setup_tabs()

        # Render the changes
        self.show_all()


    def on_button_cancel_clicked(self, button):

        """Called from a callback in self.setup_button_strip().

        Destroys any changes made by the user and re-draws the window's tabs,
        showing their original values.

        Args:

            button (Gtk.Button): The widget clicked

        """

        # Destroy the window
        self.destroy()


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


    def on_button_reset_clicked(self, button):

        """Called from a callback in self.setup_button_strip().

        Destroys any changes made by the user and re-draws the window's tabs,
        showing their original values.

        Args:

            button (Gtk.Button): The widget clicked

        """

        # Remove all existing tabs from the notebook
        number = self.notebook.get_n_pages()
        if number:

            for count in range(0, number):
                self.notebook.remove_page(0)

        # Empty self.edit_dict, destroying any changes the user has made
        self.edit_dict = {}

        # Re-draw all the tabs
        self.setup_tabs()

        # Render the changes
        self.show_all()


    def on_checkbutton_toggled(self, checkbutton, prop):

        """Called from a callback in self.add_checkbutton().

        Adds a key-value pair to self.edit_dict, using True if the button is
        selected, False if not.

        Args:

            checkbutton (Gtk.CheckButton): The widget clicked

            prop (string): The attribute in self.edit_obj to modify

        """

        if not checkbutton.get_active():
            self.edit_dict[prop] = False
        else:
            self.edit_dict[prop] = True


    def on_combo_changed(self, combo, prop):

        """Called from a callback in self.add_combo().

        Temporarily stores the contents of the widget in self.edit_dict.

        Args:

            combo (Gtk.ComboBox): The widget clicked

            prop (string): The attribute in self.edit_obj to modify

        """

        tree_iter = combo.get_active_iter()
        model = combo.get_model()
        self.edit_dict[prop] = model[tree_iter][0]


    def on_combo_with_data_changed(self, combo, prop):

        """Called from a callback in self.add_combo_with-data().

        Extracts the value visible in the widget, converts it into another
        value, and stores the later in self.edit_dict.

        Args:

            combo (Gtk.ComboBox): The widget clicked

            prop (string): The attribute in self.edit_obj to modify

        """

        tree_iter = combo.get_active_iter()
        model = combo.get_model()
        self.edit_dict[prop] = model[tree_iter][1]


    def on_entry_changed(self, entry, prop):

        """Called from a callback in self.add_entry().

        Temporarily stores the contents of the widget in self.edit_dict.

        Args:

            entry (Gtk.Entry): The widget clicked

            prop (string): The attribute in self.edit_obj to modify

        """

        self.edit_dict[prop] = entry.get_text()


    def on_radiobutton_toggled(self, checkbutton, prop, value):

        """Called from a callback in self.add_radiobutton().

        Adds a key-value pair to self.edit_dict, but only if this radiobutton
        (from those in the group) is the selected one.

        Args:

            checkbutton (Gtk.CheckButton): The widget clicked

            prop (string): The attribute in self.edit_obj to modify

            value (-): The attribute's new value

        """

        if radiobutton.get_active():
            self.edit_dict[prop] = value


    def on_spinbutton_changed(self, spinbutton, prop):

        """Called from a callback in self.add_spinbutton().

        Temporarily stores the contents of the widget in self.edit_dict.

        Args:

            spinbutton (Gtk.SpinkButton): The widget clicked

            prop (string): The attribute in self.edit_obj to modify

        """

        self.edit_dict[prop] = int(spinbutton.get_value())


    def on_textview_changed(self, textbuffer, prop):

        """Called from a callback in self.add_textview().

        Temporarily stores the contents of the widget in self.edit_dict.

        Args:

            textbuffer (Gtk.TextBuffer): The widget modified

            prop (string): The attribute in self.edit_obj to modify

        """

        self.edit_dict[prop] = textbuffer.get_text(
            textbuffer.get_start_iter(),
            textbuffer.get_end_iter(),
            # Don't include hidden characters
            False,
        )


    # (Inherited by VideoEditWin, ChannelPlaylistEditWin and FolderEditWin)


    def on_button_apply_clicked(self, button):

        """Called from callback in self.setup_general_tab().

        Apply download options to the media data object.

        Args:

            button (Gtk.Button): The widget clicked

        """

        if self.edit_obj.options_obj:
            return self.app_obj.system_error(
                401,
                'Download options already applied',
            )

        # Apply download options to the media data object
        self.app_obj.apply_download_options(self.edit_obj)
        # (De)sensitise buttons appropriately
        self.apply_button.set_sensitive(False)
        self.edit_button.set_sensitive(True)
        self.remove_button.set_sensitive(True)


    def on_button_edit_clicked(self, button):

        """Called from callback in self.setup_general_tab().

        Edit download options for the media data object.

        Args:

            button (Gtk.Button): The widget clicked

        """

        if not self.edit_obj.options_obj:
            return self.app_obj.system_error(
                402,
                'Download options not already applied',
            )

        # Open an edit window to show the options immediately
        OptionsEditWin(
            self.app_obj,
            self.edit_obj.options_obj,
            self.edit_obj,
        )


    def on_button_remove_clicked(self, button):

        """Called from callback in self.setup_general_tab().

        Remove download options from the media data object.

        Args:

            button (Gtk.Button): The widget clicked

        """

        if not self.edit_obj.options_obj:
            return self.app_obj.system_error(
                403,
                'Download options not already applied',
            )

        # Remove download options from the media data object
        self.app_obj.remove_download_options(self.edit_obj)
        # (De)sensitise buttons appropriately
        self.apply_button.set_sensitive(True)
        self.edit_button.set_sensitive(False)
        self.remove_button.set_sensitive(False)


class GenericPrefWin(GenericConfigWin):

    """Generic Python class for windows in which the user can modify various
    system settings.

    Any modifications are applied immediately (unlike in an 'edit window', in
    which the modifications are stored temporarily, and only applied once the
    user has finished making changes).
    """


    # Standard class methods


#   def __init__():             # Provided by child object


    # Public class methods


#   def setup():                # Inherited from GenericConfigWin


#   def setup_grid():           # Inherited from GenericConfigWin


#   def setup_notebook():       # Inherited from GenericConfigWin


#   def add_notebook_tab():     # Inherited from GenericConfigWin


    def setup_button_strip(self):

        """Called by self.setup().

        Creates a strip of buttons at the bottom of the window. For preference
        windows, there is only a single 'OK' button, which closes the window.
        """

        hbox = Gtk.HBox()
        self.grid.attach(hbox, 0, 2, 1, 1)

        # 'OK' button
        self.ok_button = Gtk.Button('OK')
        hbox.pack_end(self.ok_button, False, False, self.spacing_size)
        self.ok_button.get_child().set_width_chars(10)
        self.ok_button.set_tooltip_text('Close this window');
        self.ok_button.connect('clicked', self.on_button_ok_clicked)


#   def setup_gap():            # Inherited from GenericConfigWin


    # (Non-widget functions)


    def reset_window(self):

        """At the moment, only called by mainapp.TartubeApp.switch_db().

        Redraws the window, without the need to destroy the old one and replace
        it with a new one.
        """

        # This code is copied from
        #   config.GenericEditWin.on_button_reset_clicked()

        # Remove all existing tabs from the notebook
        number = self.notebook.get_n_pages()
        if number:

            for count in range(0, number):
                self.notebook.remove_page(0)

        # Re-draw all the tabs
        self.setup_tabs()

        # Render the changes
        self.show_all()


    # (Add widgets)


    def add_checkbutton(self, grid, text, set_flag, mod_flag, x, y, wid, hei):

        """Called by various functions in the child edit window.

        Adds a Gtk.CheckButton to the tab's Gtk.Grid.

        Args:

            grid (Gtk.Grid): The grid on which this widget will be placed

            text (string or None): The text to display in the checkbutton's
                label. No label is used if 'text' is an empty string or None

            set_flag (True or False): True if the checkbutton is selected

            mod_flag (True of False): True if the checkbutton can be toggled
                by the user

            x, y, wid, hei (int): Position on the grid at which the widget is
                placed

        Returns:

            The checkbutton widget created

        """

        checkbutton = Gtk.CheckButton()
        grid.attach(checkbutton, x, y, wid, hei)
        checkbutton.set_active(set_flag)
        checkbutton.set_sensitive(mod_flag)
        checkbutton.set_hexpand(True)
        if text is not None and text != '':
            checkbutton.set_label(text)

        return checkbutton


    def add_combo(self, grid, combo_list, active_val, x, y, wid, hei):

        """Called by various functions in the child edit window.

        Adds a simple Gtk.ComboBox to the tab's Gtk.Grid.

        Args:

            grid (Gtk.Grid): The grid on which this widget will be placed

            combo_list (list): A list of values to display in the combobox.
                This function expects a simple, one-dimensional list. There is
                not generic self.add_combo_with_data() function for preference
                windows.

            active_val (string or None): If not None, a value matching one of
                the items in combo_list, that should be the active row in the
                combobox

            x, y, wid, hei (int): Position on the grid at which the widget is
                placed

        Returns:

            The combobox widget created

        """

        store = Gtk.ListStore(str)

        count = -1
        active_index = 0
        for string in combo_list:
            store.append( [string] )

            count += 1
            if active_val is not None and active_val == string:
                active_index = count

        combo = Gtk.ComboBox.new_with_model(store)
        grid.attach(combo, x, y, wid, hei)
        renderer_text = Gtk.CellRendererText()
        combo.pack_start(renderer_text, True)
        combo.add_attribute(renderer_text, 'text', 0)
        combo.set_entry_text_column(0)
        combo.set_active(active_index)

        return combo


    def add_entry(self, grid, text, edit_flag, x, y, wid, hei):

        """Called by various functions in the child edit window.

        Adds a Gtk.Entry to the tab's Gtk.Grid.

        Args:

            grid (Gtk.Grid): The grid on which this widget will be placed

            text (string or None): The initial contents of the entry.

            edit_flag (True or False): True if the contents of the entry can be
                edited

            x, y, wid, hei (int): Position on the grid at which the widget is
                placed

        Returns:

            The entry widget created

        """

        entry = Gtk.Entry()
        grid.attach(entry, x, y, wid, hei)
        entry.set_hexpand(True)

        if text is not None:
            entry.set_text(str(text))

        if not edit_flag:
            entry.set_editable(False)

        return entry


    def add_label(self, grid, text, x, y, wid, hei):

        """Called by various functions in the child edit window.

        Adds a Gtk.Label to the tab's Gtk.Grid.

        Args:

            grid (Gtk.Grid): The grid on which this widget will be placed

            text (string): Pango markup displayed in the label

            x, y, wid, hei (int): Position on the grid at which the widget is
                placed

        Returns:

            The label widget created

        """

        label = Gtk.Label()
        grid.attach(label, x, y, wid, hei)
        label.set_markup(text)
        label.set_hexpand(True)
        label.set_alignment(0, 0.5)

        return label


    def add_radiobutton(self, grid, prev_button, text, x, y, wid, hei):

        """Called by various functions in the child edit window.

        Adds a Gtk.RadioButton to the tab's Gtk.Grid.

        Args:

            grid (Gtk.Grid): The grid on which this widget will be placed

            prev_button (Gtk.RadioButton or None): When this is the first
                radio button in the group, None. Otherwise, the previous
                radio button in the group. Use of this IV links the radio
                buttons together, ensuring that only one of them can be active
                at any time

            text (string or None): The text to display in the radiobutton's
                label. No label is used if 'text' is an empty string or None

            x, y, wid, hei (int): Position on the grid at which the widget is
                placed

        Returns:

            The radiobutton widget created

        """

        radiobutton = Gtk.RadioButton.new_from_widget(prev_button)
        grid.attach(radiobutton, x, y, wid, hei)
        radiobutton.set_hexpand(True)
        if text is not None and text != '':
            radiobutton.set_label(text)

        return radiobutton


    def add_spinbutton(self, grid, min_val, max_val, step, val, x, y, wid, \
    hei):

        """Called by various functions in the child edit window.

        Adds a Gtk.SpinButton to the tab's Gtk.Grid.

        Args:

            grid (Gtk.Grid): The grid on which this widget will be placed

            min_val (int): The minimum permitted in the spinbutton

            max_val (int or None): The maximum values permitted in the
                spinbutton. If None, this function assigns a very large maximum
                value (a billion)

            step (int): Clicking the up/down arrows in the spin button
                increments/decrements the value by this much

            value (int): The current value of the spinbutton

            x, y, wid, hei (int): Position on the grid at which the widget is
                placed

        Returns:

            The spinbutton widget created

        """

        # If the specified value of 'max_valu' was none, just use a very big
        #   number (as Gtk.SpinButton won't accept the None argument)
        if max_val is None:
            max_val = 1000000000

        spinbutton = Gtk.SpinButton.new_with_range(min_val, max_val, step)
        grid.attach(spinbutton, x, y, wid, hei)
        spinbutton.set_value(val)
        spinbutton.set_hexpand(False)

        return spinbutton


    # Callback class methods


    def on_button_ok_clicked(self, button):

        """Called from a callback in self.setup_button_strip().

        Closes the window.

        Args:

            button (Gtk.Button): The button clicked

        """

        # Destroy the window
        self.destroy()


class OptionsEditWin(GenericEditWin):

    """Python class for an 'edit window' to modify values in an
    options.OptionsManager object.

    Args:

        app_obj (mainapp.TartubeApp): The main application object

        edit_obj (options.OptionsManager): The object whose attributes will be
            edited in this window

        media_data_obj (media.Video, media.Channel, media.Playlist,
            media.Folder or None): The media data object which is the parent of
            the object being edited. None if we're editing the General Options
            Manager

    """


    # Standard class methods


    def __init__(self, app_obj, edit_obj, media_data_obj=None):

        Gtk.Window.__init__(self, title='Download options')

        # IV list - class objects
        # -----------------------
        # The mainapp.TartubeApp object
        self.app_obj = app_obj
        # The options.OptionManager object being edited
        self.edit_obj = edit_obj
        # The media data object which is the parent of the options manager
        #   object. Set to None if we are editing the General Options Manager
        self.media_data_obj = media_data_obj


        # IV list - Gtk widgets
        # ---------------------
        self.grid = None                        # Gtk.Grid
        self.notebook = None                    # Gtk.Notebook
        self.reset_button = None                # Gtk.Button
        self.apply_button = None                # Gtk.Button
        self.ok_button = None                   # Gtk.Button
        self.cancel_button = None               # Gtk.Button


        # IV list - other
        # ---------------
        # Size (in pixels) of gaps between edit window widgets
        self.spacing_size = self.app_obj.default_spacing_size
        # Flag set to True if all four buttons ('Reset', 'Apply', 'Cancel' and
        #   'OK' are required, or False if just the 'OK' button is required
        self.multi_button_flag = True

        # When the user changes a value, it is not applied to self.edit_obj
        #   immediately; instead, it is stored temporarily in this dictionary
        # If the user clicks the 'OK' or 'Apply' buttons at the bottom of the
        #   window, the changes are applied to self.edit_obj
        # If the user clicks the 'Reset' or 'Cancel' buttons, the dictionary
        #   is emptied and the changes are lost
        # In this edit window, the key-value pairs directly correspond to those
        #   in options.OptionsManager.options_dict, rather than corresponding
        #   directly to attributes in the options.OptionsManager object
        # Because of that, we use our own .apply_changes() and .retrieve_val()
        #   functions, rather than relying on the generic functions
        # Key-value pairs are added to this dictionary whenever the user
        #   makes a change (so if no changes are made when the window is
        #   closed, the dictionary will still be empty)
        self.edit_dict = {}

        # IVs used to keep track of widget changes in the 'Files' tab
        # Flag set to to False when that tab's output template widgets are
        #   desensitised, True when sensitised
        self.template_flag = False
        # A list of Gtk widgets to (de)sensitise in when the flag changes
        self.template_widget_list = []


        # Code
        # ----

        # Set up the edit window
        self.setup()


    # Public class methods


#   def setup():                # Inherited from GenericConfigWin


#   def setup_grid():           # Inherited from GenericConfigWin


#   def setup_notebook():       # Inherited from GenericConfigWin


#   def add_notebook_tab():     # Inherited from GenericConfigWin


#   def setup_button_strip():   # Inherited from GenericEditWin


#   def setup_gap():            # Inherited from GenericConfigWin


    # (Non-widget functions)


    def apply_changes(self):

        """Called by self.on_button_ok_clicked() and
        self.on_button_apply_clicked().

        Any changes the user has made are temporarily stored in self.edit_dict.
        Apply to those changes to the object being edited.

        In this edit window we apply changes to self.edit_obj.options_dict
        (rather than to self.edit_obj's attributes directly, as in the generic
        function.)
        """

        # Apply any changes the user has made
        for key in self.edit_dict.keys():
            self.edit_obj.options_dict[key] = self.edit_dict[key]

        # The changes can now be cleared
        self.edit_dict = {}


    def retrieve_val(self, name):

        """Can be called by anything.

        Any changes the user has made are temporarily stored in self.edit_dict.

        In the generic function, each key corresponds to an attribute in the
        object being edited, self.edit_obj. In this window, it corresponds to a
        key in self.edit_obj.options_dict.

        If 'name' exists as a key in that dictionary, retrieve the
        corresponding value and return it. Otherwise, the user hasn't yet
        modified the value, so retrieve directly from the attribute in the
        object being edited.

        Args:

            name (string): The name of the attribute in the object being
                edited

        Returns:

            The original or modified value of that attribute.

        """

        if name in self.edit_dict:
            return self.edit_dict[name]
        elif name in self.edit_obj.options_dict:
            return self.edit_obj.options_dict[name]
        else:
            return self.app_obj.system_error(
                404,
                'Unrecognised property name \'' + name + '\'',
            )


    # (Setup tabs)


    def setup_tabs(self):

        """Called by self.setup(), .on_button_apply_clicked() and
        .on_button_reset_clicked().

        Sets up the tabs for this edit window.
        """

        self.setup_general_tab()
        self.setup_files_tab()
        self.setup_formats_tab()
        self.setup_downloads_tab()
        self.setup_post_process_tab()
        self.setup_subtitles_tab()
        self.setup_others_tab()
        self.setup_advanced_tab()


    def setup_general_tab(self):

        """Called by self.setup_tabs().

        Sets up the 'General' tab.
        """

        tab, grid = self.add_notebook_tab('_General')

        if self.media_data_obj:
            if isinstance(self.media_data_obj, media.Video):
                parent_type = 'video'
            elif isinstance(self.media_data_obj, media.Channel):
                parent_type = 'channel'
            elif isinstance(self.media_data_obj, media.Playlist):
                parent_type = 'playlist'
            else:
                parent_type = 'folder'

        self.add_label(grid,
            '<u>General options</u>',
            0, 0, 2, 1,
        )

        label = self.add_label(grid,
            '',
            0, 1, 2, 1,
        )

        if self.media_data_obj is None:

            label.set_text('These options have been applied to:')

            entry = self.add_entry(grid,
                None,
                0, 2, 2, 1,
            )
            entry.set_text('All channels, playlists and folders')

        else:

            label.set_text(
                'These options have been applied to the ' + parent_type + ':',
            )

            entry = self.add_entry(grid,
                None,
                0, 2, 1, 1,
            )
            entry.set_editable(False)
            entry.set_hexpand(False)
            entry.set_width_chars(8)

            entry2 = self.add_entry(grid,
                None,
                1, 2, 1, 1,
            )
            entry2.set_editable(False)

            entry.set_text('#' + str(self.media_data_obj.dbid))
            entry2.set_text(self.media_data_obj.name)

        self.add_label(grid,
            'Extra youtube-dl command line options (e.g. --help; do not use' \
            + ' -o or --output)',
            0, 3, 2, 1,
        )

        self.add_textview(grid,
            'extra_cmd_string',
            0, 4, 2, 1,
        )

        button = Gtk.Button(
            'Completely reset all download options to their default values',
        )
        grid.attach(button, 0, 5, 2, 1)
        button.connect('clicked', self.on_reset_options_clicked)


    def setup_files_tab(self):

        """Called by self.setup_tabs().

        Sets up the 'Files' tab.
        """

        tab, grid = self.add_notebook_tab('_Files')
        grid_width = 5

        # File output options
        self.add_label(grid,
            '<u>File output options</u>',
            0, 0, grid_width, 1,
        )

        self.add_label(grid,
            'Format for video file names',
            0, 1, grid_width, 1,
        )

        store = Gtk.ListStore(int, str)
        num_list = [0, 1, 2, 4, 5, 3]
        for num in num_list:
            store.append( [num, formats.FILE_OUTPUT_NAME_DICT[num]] )

        current_format = self.edit_obj.options_dict['output_format']
        current_template = formats.FILE_OUTPUT_CONVERT_DICT[current_format]
        if current_template is None:
            current_template = self.edit_obj.options_dict['output_template']

        combo = Gtk.ComboBox.new_with_model(store)
        grid.attach(combo, 0, 2, grid_width, 1)
        renderer_text = Gtk.CellRendererText()
        combo.pack_start(renderer_text, True)
        combo.add_attribute(renderer_text, "text", 1)
        combo.set_entry_text_column(1)
        combo.set_active(num_list.index(current_format))
        # Signal connect appears below

        self.add_label(grid,
            'youtube-dl file output template',
            0, 3, grid_width, 1,
        )

        entry = self.add_entry(grid,
            None,
            0, 4, grid_width, 1,
        )
        entry.set_text(current_template)
        # Signal connect appears below

        self.add_label(grid,
            'Add to template:',
            0, 5, 1, 1,
        )

        store2 = Gtk.ListStore(str)
        for string in (
            'ID',
            'Title',
            'Ext',
            'Uploader',
            'Resolution',
            'Autonumber',
        ):
            store2.append( [string] )

        combo2 = Gtk.ComboBox.new_with_model(store2)
        grid.attach(combo2, 1, 5, 1, 1)
        renderer_text2 = Gtk.CellRendererText()
        combo2.pack_start(renderer_text2, True)
        combo2.add_attribute(renderer_text2, "text", 0)
        combo2.set_entry_text_column(0)
        combo2.set_active(0)

        button2 = Gtk.Button('Add')
        grid.attach(button2, 2, 5, 1, 1)
        # Signal connect appears below

        store3 = Gtk.ListStore(str)
        for string in (
            'View Count',
            'Like Count',
            'Dislike Count',
            'Comment Count',
            'Average Rating',
            'Age Limit',
            'Width',
            'Height',
            'Extractor',
        ):
            store3.append( [string] )

        combo3 = Gtk.ComboBox.new_with_model(store3)
        grid.attach(combo3, 3, 5, 1, 1)
        renderer_text3 = Gtk.CellRendererText()
        combo3.pack_start(renderer_text3, True)
        combo3.add_attribute(renderer_text3, "text", 0)
        combo3.set_entry_text_column(0)
        combo3.set_active(0)

        button3 = Gtk.Button('Add')
        grid.attach(button3, 4, 5, 1, 1)
        # Signal connect appears below

        store4 = Gtk.ListStore(str)
        for string in (
            'View Count',
            'Like Count',
            'Dislike Count',
            'Comment Count',
            'Average Rating',
            'Age Limit',
            'Width',
            'Height',
            'Extractor',
        ):
            store4.append( [string] )

        combo4 = Gtk.ComboBox.new_with_model(store4)
        grid.attach(combo4, 1, 6, 1, 1)
        renderer_text4 = Gtk.CellRendererText()
        combo4.pack_start(renderer_text4, True)
        combo4.add_attribute(renderer_text4, "text", 0)
        combo4.set_entry_text_column(0)
        combo4.set_active(0)

        button4 = Gtk.Button('Add')
        grid.attach(button4, 2, 6, 1, 1)
        # Signal connect appears below

        # Signal connects from above
        combo.connect('changed', self.on_file_tab_combo_changed, entry)
        entry.connect('changed', self.on_file_tab_entry_changed)
        button2.connect(
            'clicked',
            self.on_file_tab_button_clicked,
            entry,
            combo2,
        )
        button3.connect(
            'clicked',
            self.on_file_tab_button_clicked,
            entry,
            combo3,
        )
        button4.connect(
            'clicked',
            self.on_file_tab_button_clicked,
            entry,
            combo4,
        )

        # Add widgets to a list, so we can sensitise them when a custom
        #   template is selected, and desensitise them the rest of the time
        self.template_widget_list = [
            entry,
            combo2,
            combo3,
            combo4,
            button2,
            button3,
            button4,
        ]

        if current_format == 3:
            self.file_tab_sensitise_widgets(True)
        else:
            self.file_tab_sensitise_widgets(False)

        # Filesystem options

        # (empty label for spacing)
        self.add_label(grid,
            '',
            0, 7, grid_width, 1,
        )

        self.add_label(grid,
            '<u>Filesystem options</u>',
            0, 8, grid_width, 1,
        )

        self.add_checkbutton(grid,
            'Restrict filenames to using ASCII characters',
            'restrict_filenames',
            0, 9, grid_width, 1,
        )

        self.add_checkbutton(grid,
            'Set the file modification time from the server',
            'nomtime',
            0, 10, grid_width, 1,
        )


    def setup_formats_tab(self):

        """Called by self.setup_tabs().

        Sets up the 'Formats' tab.
        """

        tab, grid = self.add_notebook_tab('F_ormats')
        grid.set_column_homogeneous(True)

        # Video format options
        self.add_label(grid,
            '<u>Video format options</u>',
            0, 0, 4, 1,
        )

        label = self.add_label(grid,
            'Available video formats',
            0, 1, 2, 1,
        )

        treeview, liststore = self.add_treeview(grid,
            0, 2, 2, 1,
        )

        for key in formats.VIDEO_OPTION_LIST:
            liststore.append([key])

        button = Gtk.Button('Add format >>>')
        grid.attach(button, 0, 3, 2, 1)
        # Signal connect below

        label2 = self.add_label(grid,
            'Preference list (up to three video formats)',
            2, 1, 2, 1,
        )

        treeview2, liststore2 = self.add_treeview(grid,
            2, 2, 2, 1,
        )

        # (Need to reverse formats.VIDEO_OPTION_DICT for quick lookup)
        rev_dict = {}
        for key in formats.VIDEO_OPTION_DICT:
            rev_dict[formats.VIDEO_OPTION_DICT[key]] = key

        # There are three video format options, any or all of which might be
        #   set
        val1 = self.retrieve_val('video_format')
        val2 = self.retrieve_val('second_video_format')
        val3 = self.retrieve_val('third_video_format')
        if val1 != '0':
            liststore2.append([rev_dict[val1]])
        if val2 != '0':
            liststore2.append([rev_dict[val2]])
        if val3 != '0':
            liststore2.append([rev_dict[val3]])

        button2 = Gtk.Button('<<< Remove format')
        grid.attach(button2, 2, 3, 2, 1)
        # Signal connect below

        button3 = Gtk.Button('^ Move up')
        grid.attach(button3, 2, 4, 1, 1)
        # Signal connect below

        button4 = Gtk.Button('v Move down')
        grid.attach(button4, 3, 4, 1, 1)
        # Signal connect below

        # Signal connects from above
        button.connect(
            'clicked',
            self.on_formats_tab_add_clicked,
            button2,
            button3,
            button4,
            treeview,
            liststore2,
        )
        button2.connect(
            'clicked',
            self.on_formats_tab_remove_clicked,
            button,
            button3,
            button4,
            treeview2,
        )
        button3.connect(
            'clicked',
            self.on_formats_tab_up_clicked,
            treeview2,
        )
        button4.connect(
            'clicked',
            self.on_formats_tab_down_clicked,
            treeview2,
        )

        # Desensitise buttons, as appropriate
        if self.retrieve_val('video_format') == '0':
            button2.set_sensitive(False)
            button3.set_sensitive(False)
            button4.set_sensitive(False)

        if self.retrieve_val('third_video_format') != '0':
            button.set_sensitive(False)


    def setup_downloads_tab(self):

        """Called by self.setup_tabs().

        Sets up the 'Downloads' tab.
        """

        tab, grid = self.add_notebook_tab('_Downloads')
        grid_width = 6

        # Download options
        self.add_label(grid,
            '<u>Download options</u>',
            0, 0, grid_width, 1,
        )

        self.add_checkbutton(grid,
            'Prefer HLS (HTTP Live Streaming) over FFmpeg',
            'native_hls',
            0, 1, grid_width, 1,
        )

        self.add_checkbutton(grid,
            'Ignore errors and continue the download operation',
            'ignore_errors',
            0, 2, grid_width, 1,
        )

        self.add_label(grid,
            'Number of retries',
            0, 3, (grid_width - 2), 1,
        )

        self.add_spinbutton(grid,
            1, 99, 1,
            'retries',
            (grid_width - 2), 3, 1, 1,
        )

        # Playlist options
        self.add_label(grid,
            '<u>Playlist options</u>',
            0, 4, grid_width, 1,
        )

        self.add_label(grid,
            'Start downloading playlist from index',
            0, 5, (grid_width - 2), 1,
        )

        self.add_spinbutton(grid,
            1, None, 1,
            'playlist_start',
            (grid_width - 2), 5, 1, 1,
        )

        self.add_label(grid,
            'Stop downloading playlist at index',
            0, 6, (grid_width - 2), 1,
        )

        self.add_spinbutton(grid,
            0, None, 1,
            'playlist_end',
            (grid_width - 2), 6, 1, 1,
        )

        self.add_label(grid,
            'Maximum downloads from a playlist',
            0, 7, (grid_width - 2), 1,
        )

        self.add_spinbutton(grid,
            0, None, 1,
            'max_downloads',
            (grid_width - 2), 7, 1, 1,
        )

        # Video size limit options
        self.add_label(grid,
            '<u>Video size limit options</u>',
            0, 8, grid_width, 1,
        )

        self.add_label(grid,
            'Minimum file size for video downloads',
            0, 9, (grid_width - 2), 1,
        )

        self.add_spinbutton(grid,
            0, None, 1,
            'min_filesize',
            (grid_width - 2), 9, 1, 1,
        )

        self.add_combo_with_data(grid,
            formats.FILE_SIZE_UNIT_LIST,
            'min_filesize_unit',
            (grid_width - 1), 9, 1, 1,
        )

        self.add_label(grid,
            'Maximum file size for video downloads',
            0, 10, (grid_width - 2), 1,
        )

        self.add_spinbutton(grid,
            0, None, 1,
            'max_filesize',
            (grid_width - 2), 10, 1, 1,
        )

        self.add_combo_with_data(grid,
            formats.FILE_SIZE_UNIT_LIST,
            'max_filesize_unit',
            (grid_width - 1), 10, 1, 1,
        )


    def setup_post_process_tab(self):

        """Called by self.setup_tabs().

        Sets up the 'Post-processing' tab.
        """

        tab, grid = self.add_notebook_tab('_Post-processing')
        grid.set_column_homogeneous(True)

        # Post-processing options
        self.add_label(grid,
            '<u>Post-processing options</u>',
            0, 0, 1, 1,
        )

        self.add_checkbutton(grid,
            'Post-process the video file',
            'to_audio',
            0, 1, 1, 1,
        )

        self.add_label(grid,
            'Audio format of the post-processed file',
            0, 2, 1, 1,
        )

        combo_list = formats.AUDIO_FORMAT_LIST
        combo_list.insert(0, '')
        self.add_combo(grid,
            combo_list,
            'audio_format',
            1, 2, 1, 1,
        )

        self.add_label(grid,
            'Audio quality of the post-processed file',
            0, 3, 1, 1,
        )

        combo2_list = [
            ['High', '0'],
            ['Medium', '5'],
            ['Low', '9'],
        ]

        self.add_combo_with_data(grid,
            combo2_list,
            'audio_quality',
            1, 3, 1, 1,
        )

        self.add_checkbutton(grid,
            'Keep video file after post-processing it',
            'keep_video',
            0, 4, 1, 1,
        )

        self.add_checkbutton(grid,
            'Merge subtitles file with video (.mp4 files only)',
            'embed_subs',
            0, 5, 1, 1,
        )

        self.add_checkbutton(grid,
            'Embed thumbnail in audio file as cover art',
            'embed_thumbnail',
            0, 6, 1, 1,
        )

        self.add_checkbutton(grid,
            'Write metadata to the video file',
            'add_metadata',
            0, 7, 1, 1,
        )


    def setup_subtitles_tab(self):

        """Called by self.setup_tabs().

        Sets up the 'Subtitles' tab.
        """

        tab, grid = self.add_notebook_tab('_Subtitles')
        grid.set_column_homogeneous(True)

        # Subtitles options
        self.add_label(grid,
            '<u>Subtitles options</u>',
            0, 0, 2, 1,
        )

        radio_flag = False
        radiobutton = self.add_radiobutton(grid,
            None,
            'Don\'t download the subtitles file',
            None,
            None,
            0, 1, 2, 1,
        )
        if self.retrieve_val('write_subs') is False:
            radiobutton.set_active(True)
            radio_flag = True
        # Signal connect appears below

        radiobutton2 = self.add_radiobutton(grid,
            radiobutton,
            'Download the automatic subtitles file (YouTube only)',
            None,
            None,
            0, 2, 2, 1,
        )
        if self.retrieve_val('write_auto_subs') is True:
            radiobutton.set_active(True)
            radio_flag = True
        # Signal connect appears below

        radiobutton3 = self.add_radiobutton(grid,
            radiobutton2,
            'Download all available subtitles files',
            None,
            None,
            0, 3, 2, 1,
        )
        if self.retrieve_val('write_all_subs') is True:
            radiobutton2.set_active(True)
            radio_flag = True
        # Signal connect appears below

        radiobutton4 = self.add_radiobutton(grid,
            radiobutton3,
            'Download subtitles file for this language',
            None,
            None,
            0, 4, 1, 1,
        )
        if not radio_flag:
            radiobutton.set_active(True)
        # Signal connect appears below

        combo = self.add_combo_with_data(grid,
            formats.LANGUAGE_CODE_LIST,
            'subs_lang',
            1, 4, 1, 1,
        )
        if radio_flag:
            combo.set_sensitive(False)

        # Signal connects from above
        radiobutton.connect(
            'toggled',
            self.on_subtitles_toggled,
            combo,
            'write_subs',
        )
        radiobutton2.connect(
            'toggled',
            self.on_subtitles_toggled,
            combo,
            'write_auto_subs',
        )
        radiobutton3.connect(
            'toggled',
            self.on_subtitles_toggled,
            combo,
            'write_all_subs',
        )
        radiobutton4.connect(
            'toggled',
            self.on_subtitles_toggled,
            combo,
            'subs_lang',
        )


    def setup_others_tab(self):

        """Called by self.setup_tabs().

        Sets up the 'Other files' tab.
        """

        tab, grid = self.add_notebook_tab('O_ther files')
        script = __main__.__packagename__.title()

        # Other file options
        self.add_label(grid,
            '<u>Other file options</u>',
            0, 0, 1, 1,
        )

        self.add_checkbutton(grid,
            'Write video\'s description to a .description file',
            'write_description',
            0, 1, 1, 1,
        )

        self.add_checkbutton(grid,
            'Write video\'s metadata to an .info.json file',
            'write_info',
            0, 2, 1, 1,
        )

        self.add_checkbutton(grid,
            'Write the video\'s thumbnail to the same folder',
            'write_thumbnail',
            0, 3, 1, 1,
        )

        self.add_label(grid,
            '<u>Options during real (not simulated) downloads</u>',
            0, 4, 1, 1,
        )

        self.add_checkbutton(grid,
            'Keep the description file after ' +  script + ' shuts down',
            'keep_description',
            0, 5, 1, 1,
        )

        self.add_checkbutton(grid,
            'Keep the metadata file after ' +  script + ' shuts down',
            'keep_info',
            0, 6, 1, 1,
        )

        self.add_checkbutton(grid,
            'Keep the thumbnail file after ' +  script + ' shuts down',
            'keep_thumbnail',
            0, 7, 1, 1,
        )

        self.add_label(grid,
            '<u>Options during simulated (not real) downloads</u>',
            0, 8, 1, 1,
        )

        self.add_checkbutton(grid,
            'Keep the description file after ' +  script + ' shuts down',
            'sim_keep_description',
            0, 9, 1, 1,
        )

        self.add_checkbutton(grid,
            'Keep the metadata file after ' +  script + ' shuts down',
            'sim_keep_info',
            0, 10, 1, 1,
        )

        self.add_checkbutton(grid,
            'Keep the thumbnail file after ' +  script + ' shuts down',
            'sim_keep_thumbnail',
            0, 11, 1, 1,
        )


    def setup_advanced_tab(self):

        """Called by self.setup_tabs().

        Sets up the 'Advanced' tab.
        """

        tab, grid = self.add_notebook_tab('_Advanced')

        # Authentification options
        self.add_label(grid,
            '<u>Authentification options</u>',
            0, 0, 2, 1,
        )

        self.add_label(grid,
            'Username with which to log in',
            0, 1, 1, 1,
        )

        self.add_entry(grid,
            'username',
            1, 1, 1, 1,
        )

        self.add_label(grid,
            'Password with which to log in',
            0, 2, 1, 1,
        )

        self.add_entry(grid,
            'password',
            1, 2, 1, 1,
        )

        self.add_label(grid,
            'Password required for this URL',
            0, 3, 1, 1,
        )

        self.add_entry(grid,
            'video_password',
            1, 3, 1, 1,
        )

        # Network options
        self.add_label(grid,
            '<u>Network options</u>',
            0, 4, 2, 1,
        )

        self.add_label(grid,
            'Use this HTTP/HTTPS proxy',
            0, 5, 1, 1,
        )

        self.add_entry(grid,
            'proxy',
            1, 5, 1, 1,
        )

        self.add_label(grid,
            'Custom user agent for youtube-dl',
            0, 6, 1, 1,
        )

        self.add_entry(grid,
            'user_agent',
            1, 6, 1, 1,
        )

        self.add_label(grid,
            'Custom referer if video access has restricted domain',
            0, 7, 1, 1,
        )

        self.add_entry(grid,
            'referer',
            1, 7, 1, 1,
        )


    # (Tab support functions)


    def file_tab_sensitise_widgets(self, flag):

        """Called by self.setup_files_tab().

        Sensitises or desensitises a list of widgets in response to the user's
        interactions with widgets on that tab.

        Args:

            flag (True, False): True to sensitise the widgets, False to
                desensitise them

        """

        self.template_flag = flag
        for widget in self.template_widget_list:
            widget.set_sensitive(flag)


    # Callback class methods


    def on_file_tab_button_clicked(self, button, entry, combo):

        """Called by callback in self.setup_files_tab().

        Args:

            button (Gtk.Button): The widget clicked

            entry (Gtk.Entry): Another widget to be modified by this function

            combo (Gtk.ComboBox): Another widget to be modified by this
                function

        """

        tree_iter = combo.get_active_iter()
        model = combo.get_model()
        label = model[tree_iter][0]

        # (Code adapted from youtube-dl-gui's GeneralTab._on_template)
        label = label.lower().replace(' ', '_')
        if label == "ext":
            prefix = '.'
        else:
            prefix = '-'

        # If the output template is empty or ends with a file path separator,
        #   remove the prefix
        output_template = self.retrieve_val('output_template')
        if not output_template or output_template[-1] == os.sep:
            prefix = ''

        formatted = '{0}%({1})s'.format(prefix, label)
        # (Setting the entry updates self.edit_dict)
        entry.set_text(output_template + formatted)


    def on_file_tab_combo_changed(self, combo, entry):

        """Called by callback in self.setup_files_tab().

        Args:

            combo (Gtk.ComboBox): The widget clicked

            entry (Gtk.Entry): Another widget to be modified by this function

        """

        tree_iter = combo.get_active_iter()
        model = combo.get_model()
        row_id, name = model[tree_iter][:2]

        self.edit_dict['output_format'] = row_id

        if row_id == 3:
            self.file_tab_sensitise_widgets(True)
            entry.set_text(self.retrieve_val('output_template'))

        else:
            self.file_tab_sensitise_widgets(False)
            entry.set_text(formats.FILE_OUTPUT_CONVERT_DICT[row_id])


    def on_file_tab_entry_changed(self, entry):

        """Called by callback in self.setup_files_tab().

        Args:

            entry (Gtk.Entry): The widget clicked

        """

        # Only set 'output_template' when option 3 is selected, which is when
        #   the entry is sensitised
        if self.template_flag:
            self.edit_dict['output_template'] = entry.get_text()


    def on_formats_tab_add_clicked(self, add_button, remove_button, \
    up_button, down_button, treeview, other_liststore):

        """Called by callback in self.setup_formats_tab().

        Args:

            add_button (Gtk.Button): The widget clicked

            remove_button, up_button, down_button (Gtk.Button): Other widgets
                to be modified by this function

            treeview (Gtk.TreeView): Another widget to be modified by this
                function

            other_liststore (Gtk.ListStore): Another widget to be modified by
                this function

        """

        selection = treeview.get_selection()
        (model, iter) = selection.get_selected()
        if iter is None:

            # Nothing selected
            return

        else:

            name = model[iter][0]
            # Convert e.g. 'mp4 [360p]' to the extractor code e.g. '18'
            extract_code = formats.VIDEO_OPTION_DICT[name]

        # There are three video format options; set the first one whose value
        #   is not already 0
        val1 = self.retrieve_val('video_format')
        val2 = self.retrieve_val('second_video_format')
        val3 = self.retrieve_val('third_video_format')
        # Check the user's choice of format hasn't already been added
        if extract_code == val1 or extract_code == val2 \
        or extract_code == val3:
            return

        if val1 == '0':
            self.edit_dict['video_format'] = extract_code
        elif val2 == '0':
            self.edit_dict['second_video_format'] = extract_code
        elif val3 == '0':
            self.edit_dict['third_video_format'] = extract_code
            add_button.set_sensitive(False)
        else:
            # 'add_button' should be desensitised, but if clicked, just ignore
            #   it
            return

        # Update the other treeview, adding the format to it (and don't modify
        #   this treeview)
        other_liststore.append([name])
        # Sensitise the other buttons (if desensitised), so the format can be
        #   removed later
        remove_button.set_sensitive(True)
        up_button.set_sensitive(True)
        down_button.set_sensitive(True)


    def on_formats_tab_down_clicked(self, down_button, treeview):

        """Called by callback in self.setup_formats_tab().

        Args:

            down_button (Gtk.Button): The widget clicked

            treeview (Gtk.TreeView): Another widget to be modified by this
                function

        """

        selection = treeview.get_selection()
        (model, path_list) = selection.get_selected_rows()
        if not path_list:

            # Nothing selected
            return

        else:

            this_iter = model.get_iter(path_list[0])
            name = model[this_iter][0]
            # Convert e.g. 'mp4 [360p]' to the extractor code e.g. '18'
            extract_code = formats.VIDEO_OPTION_DICT[name]

        # There are three video format options; the selected one might be any
        #   of them
        val1 = self.retrieve_val('video_format')
        val2 = self.retrieve_val('second_video_format')
        val3 = self.retrieve_val('third_video_format')

        if extract_code == val3:
            # Can't move the last item down
            return

        else:

            if extract_code == val2:
                self.edit_dict['second_video_format'] = val3
                self.edit_dict['third_video_format'] = val2

            elif extract_code == val1:
                self.edit_dict['video_format'] = val2
                self.edit_dict['second_video_format'] = val1

            else:
                # This should not be possible
                return

            this_path = path_list[0]
            next_path = this_path[0]+1
            model.move_after(
                model.get_iter(this_path),
                model.get_iter(next_path),
            )


    def on_formats_tab_remove_clicked(self, remove_button, add_button, \
    up_button, down_button, treeview):

        """Called by callback in self.setup_formats_tab().

        Args:

            remove_button (Gtk.Button): The widget clicked

            add_button, up_button, down_button (Gtk.Button): Other widgets to
                be modified by this function


            treeview (Gtk.TreeView): Another widget to be modified by this
                function

        """

        selection = treeview.get_selection()
        (model, iter) = selection.get_selected()
        if iter is None:

            # Nothing selected
            return

        else:

            name = model[iter][0]
            # Convert e.g. 'mp4 [360p]' to the extractor code e.g. '18'
            extract_code = formats.VIDEO_OPTION_DICT[name]

        # There are three video format options; the selected one might be any
        #   of them
        val1 = self.retrieve_val('video_format')
        val2 = self.retrieve_val('second_video_format')
        val3 = self.retrieve_val('third_video_format')

        if extract_code == val1:
            self.edit_dict['video_format'] = val2
            self.edit_dict['second_video_format'] = val3
            self.edit_dict['third_video_format'] = '0'
        elif extract_code == val2:
            self.edit_dict['second_video_format'] = val3
            self.edit_dict['third_video_format'] = '0'
        elif extract_code == val3:
            self.edit_dict['third_video_format'] = '0'
        else:
            # This should not be possible
            return

        # Update this treeview
        model.remove(iter)
        # Re-sensitise buttons, as appropriate
        add_button.set_sensitive(True)
        if self.retrieve_val('video_format') == '0':
            # Nothing left to remove
            remove_button.set_sensitive(False)
            up_button.set_sensitive(False)
            down_button.set_sensitive(False)


    def on_formats_tab_up_clicked(self, up_button, treeview):

        """Called by callback in self.setup_formats_tab().

        Args:

            button (Gtk.Button): The widget clicked

            treeview (Gtk.TreeView): Another widget to be modified by this
                function

        """

        selection = treeview.get_selection()
        (model, path_list) = selection.get_selected_rows()
        if not path_list:

            # Nothing selected
            return

        else:

            this_iter = model.get_iter(path_list[0])
            name = model[this_iter][0]
            # Convert e.g. 'mp4 [360p]' to the extractor code e.g. '18'
            extract_code = formats.VIDEO_OPTION_DICT[name]

        # There are three video format options; the selected one might be any
        #   of them
        val1 = self.retrieve_val('video_format')
        val2 = self.retrieve_val('second_video_format')
        val3 = self.retrieve_val('third_video_format')

        if extract_code == val1:
            # Can't move the first item up
            return

        else:

            if extract_code == val2:
                self.edit_dict['video_format'] = val2
                self.edit_dict['second_video_format'] = val1

            elif extract_code == val3:
                self.edit_dict['second_video_format'] = val3
                self.edit_dict['third_video_format'] = val2

            else:
                # This should not be possible
                return

            this_path = path_list[0]
            prev_path = this_path[0]-1
            model.move_before(
                model.get_iter(this_path),
                model.get_iter(prev_path),
            )


    def on_reset_options_clicked(self, button):

        """Called by callback in self.setup_general_tab().

        Args:

            button (Gtk.Button): The widget clicked

        """

        if self.media_data_obj is None:

            # Editing the General Options Manager object
            self.app_obj.dialogue_manager_obj.show_msg_dialogue(
                'This operation cannot be reversed.\n' \
                + 'Are you sure you want to continue?',
                'question',
                'yes-no',
                self,           # Parent window is this window
                {
                    'yes': 'reset_options_manager',
                    # (Reset this edit window, if the user clicks 'yes')
                    'data': [self],
                },
            )

        else:

            # Editing an Options Manager object attached to a particular media
            #   data object
            self.app_obj.dialogue_manager_obj.show_msg_dialogue(
                'This operation cannot be reversed.\n' \
                + 'Are you sure you want to continue?',
                'question',
                'yes-no',
                self,           # Parent window is this window
                {
                    'yes': 'reset_options_manager',
                    'data': [self, self.media_data_obj],
                },
            )


    def on_subtitles_toggled(self, radiobutton, combo, prop):

        """Called by callback in self.setup_subtitles_tab().

        Args:

            radiobutton (Gtk.RadioButton): The widget clicked

            combo (Gtk.ComboBox): Another widget to be modified by this
                function

            prop (string): The attribute in self.edit_obj to modify

        """

        if radiobutton.get_active():

            if prop == 'write_subs':
                self.edit_dict['write_subs'] = False
                self.edit_dict['write_auto_subs'] = False
                self.edit_dict['write_all_subs'] = False
                combo.set_sensitive(False)

            elif prop == 'write_auto_subs':
                self.edit_dict['write_subs'] = True
                self.edit_dict['write_auto_subs'] = True
                self.edit_dict['write_all_subs'] = False
                combo.set_sensitive(False)

            elif prop == 'write_all_subs':
                self.edit_dict['write_subs'] = True
                self.edit_dict['write_auto_subs'] = False
                self.edit_dict['write_all_subs'] = True
                combo.set_sensitive(False)

            elif prop == 'subs_lang':
                self.edit_dict['write_subs'] = True
                self.edit_dict['write_auto_subs'] = False
                self.edit_dict['write_all_subs'] = False
                combo.set_sensitive(True)


class VideoEditWin(GenericEditWin):

    """Python class for an 'edit window' to modify values in a media.Video
    object.

    Args:

        app_obj (mainapp.TartubeApp): The main application object

        edit_obj (media.Video): The object whose attributes will be edited in
            this window

    """


    # Standard class methods


    def __init__(self, app_obj, edit_obj):

        Gtk.Window.__init__(self, title='Video properties')

        # IV list - class objects
        # -----------------------
        # The mainapp.TartubeApp object
        self.app_obj = app_obj
        # The media.Video object being edited
        self.edit_obj = edit_obj


        # IV list - Gtk widgets
        # ---------------------
        self.grid = None                        # Gtk.Grid
        self.notebook = None                    # Gtk.Notebook
        self.reset_button = None                # Gtk.Button
        self.apply_button = None                # Gtk.Button
        self.ok_button = None                   # Gtk.Button
        self.cancel_button = None               # Gtk.Button
        # (Non-standard widgets)
        self.apply_button = None                # Gtk.Button
        self.edit_button = None                 # Gtk.Button
        self.remove_button = None               # Gtk.Button


        # IV list - other
        # ---------------
        # Size (in pixels) of gaps between edit window widgets
        self.spacing_size = self.app_obj.default_spacing_size
        # Flag set to True if all four buttons ('Reset', 'Apply', 'Cancel' and
        #   'OK' are required, or False if just the 'OK' button is required
        self.multi_button_flag = False

        # When the user changes a value, it is not applied to self.edit_obj
        #   immediately; instead, it is stored temporarily in this dictionary
        # If the user clicks the 'OK' or 'Apply' buttons at the bottom of the
        #   window, the changes are applied to self.edit_obj
        # If the user clicks the 'Reset' or 'Cancel' buttons, the dictionary
        #   is emptied and the changes are lost
        # The key-value pairs in the dictionary correspond directly to
        #   the names of attributes, and their balues in self.edit_obj
        # Key-value pairs are added to this dictionary whenever the user
        #   makes a change (so if no changes are made when the window is
        #   closed, the dictionary will still be empty)
        self.edit_dict = {}


        # Code
        # ----

        # Set up the edit window
        self.setup()


    # Public class methods


#   def setup():                # Inherited from GenericConfigWin


#   def setup_grid():           # Inherited from GenericConfigWin


#   def setup_notebook():       # Inherited from GenericConfigWin


#   def add_notebook_tab():     # Inherited from GenericConfigWin


#   def setup_button_strip():   # Inherited from GenericEditWin


#   def setup_gap():            # Inherited from GenericConfigWin


    # (Non-widget functions)


#   def apply_changes():        # Inherited from GenericConfigWin


#   def retrieve_val():         # Inherited from GenericConfigWin


    # (Setup tabs)


    def setup_tabs(self):

        """Called by self.setup(), .on_button_apply_clicked() and
        .on_button_reset_clicked().

        Sets up the tabs for this edit window.
        """

        self.setup_general_tab()
        self.setup_descrip_tab()
        self.setup_errors_warnings_tab()


    def setup_general_tab(self):

        """Called by self.setup_tabs().

        Sets up the 'General' tab.
        """

        tab, grid = self.add_notebook_tab('_General')

        self.add_label(grid,
            '<u>General properties</u>',
            0, 0, 2, 1,
        )

        entry = self.add_entry(grid,
            None,
            0, 1, 1, 1,
        )
        entry.set_text('#' + str(self.edit_obj.dbid))
        entry.set_editable(False)
        entry.set_hexpand(False)
        entry.set_width_chars(8)

        entry2 = self.add_entry(grid,
            'name',
            1, 1, 1, 1,
        )
        entry2.set_editable(False)

        parent_obj = self.edit_obj.parent_obj
        if isinstance(parent_obj, media.Channel):
            icon_path \
            = self.app_obj.main_win_obj.icon_dict['channel_none_large']
        elif isinstance(parent_obj, media.Playlist):
            icon_path \
            = self.app_obj.main_win_obj.icon_dict['playlist_none_large']
        else:
            icon_path \
            = self.app_obj.main_win_obj.icon_dict['folder_none_large']

        self.add_image(grid,
            icon_path,
            0, 2, 1, 1,
        )

        entry3 = self.add_entry(grid,
            None,
            1, 2, 1, 1,
        )
        entry3.set_text(parent_obj.name)
        entry3.set_editable(False)

        label = self.add_label(grid,
            'URL',
            0, 3, 1, 1,
        )
        label.set_hexpand(False)

        entry4 = self.add_entry(grid,
            'source',
            1, 3, 1, 1,
        )
        entry4.set_editable(False)

        label2 = self.add_label(grid,
            'File',
            0, 4, 1, 1,
        )
        label2.set_hexpand(False)

        entry5 = self.add_entry(grid,
            None,
            1, 4, 1, 1,
        )
        entry5.set_editable(False)
        if self.edit_obj.file_dir:
            entry5.set_text(
                os.path.abspath(
                    os.path.join(
                        self.edit_obj.file_dir,
                        self.edit_obj.file_name + self.edit_obj.file_ext,
                    ),
                )
            )

        # To avoid messing up the neat format of the rows above, add another
        #   grid, and put the next set of widgets inside it
        grid2 = Gtk.Grid()
        grid.attach(grid2, 0, 5, 2, 1)
        grid2.set_vexpand(False)
        grid2.set_border_width(self.spacing_size)
        grid2.set_column_spacing(self.spacing_size)
        grid2.set_row_spacing(self.spacing_size)

        checkbutton = self.add_checkbutton(grid2,
            'Always simulate download of this video',
            'dl_sim_flag',
            0, 0, 1, 1,
        )
        checkbutton.set_sensitive(False)

        label3 = self.add_label(grid2,
            'Duration',
            1, 0, 1, 1,
        )
        label3.set_hexpand(False)

        entry6 = self.add_entry(grid2,
            None,
            2, 0, 1, 1,
        )
        entry6.set_editable(False)
        if self.edit_obj.duration is not None:
            entry6.set_text(
                utils.convert_seconds_to_string(self.edit_obj.duration),
            )

        checkbutton2 = self.add_checkbutton(grid2,
            'Video is marked as unwatched',
            'new_flag',
            0, 1, 1, 1,
        )
        checkbutton2.set_sensitive(False)

        label4 = self.add_label(grid2,
            'File size',
            1, 1, 1, 1,
        )
        label4.set_hexpand(False)

        entry7 = self.add_entry(grid2,
            None,
            2, 1, 1, 1,
        )
        entry7.set_editable(False)
        if self.edit_obj.file_size is not None:
            entry7.set_text(self.edit_obj.get_file_size_string())

        checkbutton3 = self.add_checkbutton(grid2,
            'Video is marked as favourite',
            'fav_flag',
            0, 2, 1, 1,
        )
        checkbutton3.set_sensitive(False)

        label5 = self.add_label(grid2,
            'Upload time',
            1, 2, 1, 1,
        )
        label5.set_hexpand(False)

        entry8 = self.add_entry(grid2,
            None,
            2, 2, 1, 1,
        )
        entry8.set_editable(False)
        if self.edit_obj.upload_time is not None:
            entry8.set_text(self.edit_obj.get_upload_time_string())

        checkbutton4 = self.add_checkbutton(grid2,
            'Video has been downloaded',
            'dl_flag',
            0, 3, 1, 1,
        )
        checkbutton4.set_sensitive(False)

        label6 = self.add_label(grid2,
            'Receive time',
            1, 3, 1, 1,
        )
        label6.set_hexpand(False)

        entry9 = self.add_entry(grid2,
            None,
            2, 3, 1, 1,
        )
        entry9.set_editable(False)
        if self.edit_obj.receive_time is not None:
            entry9.set_text(self.edit_obj.get_receive_time_string())

        # To avoid messing up the formatting again, put the next buttons inside
        #   an hbox
        hbox = Gtk.HBox()
        grid.attach(hbox, 0, 6, 2, 1)

        self.apply_button = Gtk.Button('Apply download options')
        hbox.pack_start(self.apply_button, True, True, self.spacing_size)
        self.apply_button.connect('clicked', self.on_button_apply_clicked)

        self.edit_button = Gtk.Button('Edit download options')
        hbox.pack_start(self.edit_button, True, True, self.spacing_size)
        self.edit_button.connect('clicked', self.on_button_edit_clicked)

        self.remove_button = Gtk.Button('Remove download options')
        hbox.pack_start(self.remove_button, True, True, self.spacing_size)
        self.remove_button.connect('clicked', self.on_button_remove_clicked)

        if self.edit_obj.options_obj:
            self.apply_button.set_sensitive(False)
        else:
            self.edit_button.set_sensitive(False)
            self.remove_button.set_sensitive(False)


    def setup_descrip_tab(self):

        """Called by self.setup_tabs().

        Sets up the 'Description' tab.
        """

        tab, grid = self.add_notebook_tab('_Description')

        self.add_label(grid,
            '<u>Video description</u>',
            0, 0, 1, 1,
        )

        self.add_textview(grid,
            'descrip',
            0, 1, 1, 1,
        )


    def setup_errors_warnings_tab(self):

        """Called by self.setup_tabs().

        Sets up the 'Errors / Warnings' tab.
        """

        tab, grid = self.add_notebook_tab('_Errors / Warnings')

        self.add_label(grid,
            '<u>Errors / Warnings</u>',
            0, 0, 1, 1,
        )

        self.add_label(grid,
            '<i>Error messages produced the last time this video was' \
            + ' checked/downloaded</i>',
            0, 1, 1, 1,
        )

        textview, textbuffer = self.add_textview(grid,
            'error_list',
            0, 2, 1, 1,
        )
        textview.set_editable(False)
        textview.set_wrap_mode(Gtk.WrapMode.WORD)

        self.add_label(grid,
            '<i>Warning messages produced the last time this video was' \
            + ' checked/downloaded</i>',
            0, 3, 1, 1,
        )

        textview2, textbuffer2 = self.add_textview(grid,
            'warning_list',
            0, 4, 1, 1,
        )
        textview2.set_editable(False)
        textview2.set_wrap_mode(Gtk.WrapMode.WORD)


    # Callback class methods


#   def on_button_apply_clicked():  # Inherited from GenericConfigWin


#   def on_button_edit_clicked():   # Inherited from GenericConfigWin


#   def on_button_remove_clicked(): # Inherited from GenericConfigWin


    def never_called_func(self):

        """Function that is never called, but which makes this class object
        collapse neatly in my IDE."""

        pass


class ChannelPlaylistEditWin(GenericEditWin):

    """Python class for an 'edit window' to modify values in a media.Channel or
    media.Playlist object.

    Args:

        app_obj (mainapp.TartubeApp): The main application object

        edit_obj (media.Channel, media.Playlist): The object whose attributes
            will be edited in this window

    """


    # Standard class methods


    def __init__(self, app_obj, edit_obj):

        if isinstance(edit_obj, media.Channel):
            media_type = 'channel'
            win_title = 'Channel properties'
        else:
            media_type = 'playlist'
            win_title = 'Playlist properties'

        Gtk.Window.__init__(self, title=win_title)

        # IV list - class objects
        # -----------------------
        # The mainapp.TartubeApp object
        self.app_obj = app_obj
        # The media.Channel or media.Playlist object being edited
        self.edit_obj = edit_obj


        # IV list - Gtk widgets
        # ---------------------
        self.grid = None                        # Gtk.Grid
        self.notebook = None                    # Gtk.Notebook
        self.reset_button = None                # Gtk.Button
        self.apply_button = None                # Gtk.Button
        self.ok_button = None                   # Gtk.Button
        self.cancel_button = None               # Gtk.Button
        # (Non-standard widgets)
        self.apply_button = None                # Gtk.Button
        self.edit_button = None                 # Gtk.Button
        self.remove_button = None               # Gtk.Button


        # IV list - other
        # ---------------
        # Size (in pixels) of gaps between edit window widgets
        self.spacing_size = self.app_obj.default_spacing_size
        # Flag set to True if all four buttons ('Reset', 'Apply', 'Cancel' and
        #   'OK' are required, or False if just the 'OK' button is required
        self.multi_button_flag = False

        # When the user changes a value, it is not applied to self.edit_obj
        #   immediately; instead, it is stored temporarily in this dictionary
        # If the user clicks the 'OK' or 'Apply' buttons at the bottom of the
        #   window, the changes are applied to self.edit_obj
        # If the user clicks the 'Reset' or 'Cancel' buttons, the dictionary
        #   is emptied and the changes are lost
        # The key-value pairs in the dictionary correspond directly to
        #   the names of attributes, and their balues in self.edit_obj
        # Key-value pairs are added to this dictionary whenever the user
        #   makes a change (so if no changes are made when the window is
        #   closed, the dictionary will still be empty)
        self.edit_dict = {}

        # String set to 'channel' or 'playlist'
        self.media_type = media_type


        # Code
        # ----

        # Set up the edit window
        self.setup()


    # Public class methods


#   def setup():                # Inherited from GenericConfigWin


#   def setup_grid():           # Inherited from GenericConfigWin


#   def setup_notebook():       # Inherited from GenericConfigWin


#   def add_notebook_tab():     # Inherited from GenericConfigWin


#   def setup_button_strip():   # Inherited from GenericEditWin


#   def setup_gap():            # Inherited from GenericConfigWin


    # (Non-widget functions)


#   def apply_changes():        # Inherited from GenericConfigWin


#   def retrieve_val():         # Inherited from GenericConfigWin


    # (Setup tabs)


    def setup_tabs(self):

        """Called by self.setup(), .on_button_apply_clicked() and
        .on_button_reset_clicked().

        Sets up the tabs for this edit window.
        """

        self.setup_general_tab()
        self.setup_errors_warnings_tab()


    def setup_general_tab(self):

        """Called by self.setup_tabs().

        Sets up the 'General' tab.
        """

        tab, grid = self.add_notebook_tab('_General')

        self.add_label(grid,
            '<u>General properties</u>',
            0, 0, 2, 1,
        )

        entry = self.add_entry(grid,
            None,
            0, 1, 1, 1,
        )
        entry.set_text('#' + str(self.edit_obj.dbid))
        entry.set_editable(False)
        entry.set_hexpand(False)
        entry.set_width_chars(8)

        entry2 = self.add_entry(grid,
            'name',
            1, 1, 1, 1,
        )
        entry2.set_editable(False)

        main_win_obj = self.app_obj.main_win_obj
        parent_obj = self.edit_obj.parent_obj
        if parent_obj:
            icon_path = main_win_obj.icon_dict['folder_none_large']
        else:
            icon_path = main_win_obj.icon_dict['folder_no_parent_none_large']

        self.add_image(grid,
            icon_path,
            0, 2, 1, 1,
        )

        entry3 = self.add_entry(grid,
            None,
            1, 2, 1, 1,
        )
        entry3.set_editable(False)
        if parent_obj:
            entry3.set_text(parent_obj.name)

        label = self.add_label(grid,
            'URL',
            0, 3, 1, 1,
        )
        label.set_hexpand(False)

        entry4 = self.add_entry(grid,
            'source',
            1, 3, 1, 1,
        )
        entry4.set_editable(False)

        label2 = self.add_label(grid,
            'Directory',
            0, 4, 1, 1,
        )
        label2.set_hexpand(False)

        entry5 = self.add_entry(grid,
            None,
            1, 4, 1, 1,
        )
        entry5.set_editable(False)
        entry5.set_text(self.edit_obj.get_dir(self.app_obj))

        # To avoid messing up the neat format of the rows above, add another
        #   grid, and put the next set of widgets inside it
        grid2 = Gtk.Grid()
        grid.attach(grid2, 0, 5, 2, 1)
        grid2.set_vexpand(False)
        grid2.set_border_width(self.spacing_size)
        grid2.set_column_spacing(self.spacing_size)
        grid2.set_row_spacing(self.spacing_size)

        checkbutton = self.add_checkbutton(grid2,
            'Always simulate download of videos in this ' + self.media_type,
            'dl_sim_flag',
            0, 0, 1, 1,
        )
        checkbutton.set_sensitive(False)

        checkbutton2 = self.add_checkbutton(grid2,
            'This ' + self.media_type + ' is marked as a favourite',
            'fav_flag',
            0, 1, 1, 1,
        )
        checkbutton2.set_sensitive(False)

        self.add_label(grid2,
            'Total videos',
            1, 0, 1, 1,
        )
        entry6 = self.add_entry(grid2,
            'vid_count',
            2, 0, 1, 1,
        )
        entry6.set_editable(False)
        entry6.set_width_chars(8)
        entry6.set_hexpand(False)

        self.add_label(grid2,
            'New videos',
            1, 1, 1, 1,
        )
        entry7 = self.add_entry(grid2,
            'new_count',
            2, 1, 1, 1,
        )
        entry7.set_editable(False)
        entry7.set_width_chars(8)
        entry7.set_hexpand(False)

        self.add_label(grid2,
            'Favourite videos',
            1, 2, 1, 1,
        )
        entry8 = self.add_entry(grid2,
            'fav_count',
            2, 2, 1, 1,
        )
        entry8.set_editable(False)
        entry8.set_width_chars(8)
        entry8.set_hexpand(False)

        self.add_label(grid2,
            'Downloaded videos',
            1, 3, 1, 1,
        )
        entry9 = self.add_entry(grid2,
            'dl_count',
            2, 3, 1, 1,
        )
        entry9.set_editable(False)
        entry9.set_width_chars(8)
        entry9.set_hexpand(False)

        # To avoid messing up the formatting again, but the next buttons inside
        #   an hbox
        hbox = Gtk.HBox()
        grid.attach(hbox, 0, 6, 2, 1)

        self.apply_button = Gtk.Button('Apply download options')
        hbox.pack_start(self.apply_button, True, True, self.spacing_size)
        self.apply_button.connect('clicked', self.on_button_apply_clicked)

        self.edit_button = Gtk.Button('Edit download options')
        hbox.pack_start(self.edit_button, True, True, self.spacing_size)
        self.edit_button.connect('clicked', self.on_button_edit_clicked)

        self.remove_button = Gtk.Button('Remove download options')
        hbox.pack_start(self.remove_button, True, True, self.spacing_size)
        self.remove_button.connect('clicked', self.on_button_remove_clicked)

        if self.edit_obj.options_obj:
            self.apply_button.set_sensitive(False)
        else:
            self.edit_button.set_sensitive(False)
            self.remove_button.set_sensitive(False)


    def setup_errors_warnings_tab(self):

        """Called by self.setup_tabs().

        Sets up the 'Errors / Warnings' tab.
        """

        tab, grid = self.add_notebook_tab('_Errors / Warnings')

        self.add_label(grid,
            '<u>Errors / Warnings</u>',
            0, 0, 1, 1,
        )

        self.add_label(grid,
            '<i>Error messages produced the last time this ' \
            + self.media_type + ' was checked/downloaded</i>',
            0, 1, 1, 1,
        )

        textview, textbuffer = self.add_textview(grid,
            'error_list',
            0, 2, 1, 1,
        )
        textview.set_editable(False)
        textview.set_wrap_mode(Gtk.WrapMode.WORD)

        self.add_label(grid,
            '<i>Warning messages produced the last time this ' \
            + self.media_type + ' was checked/downloaded</i>',
            0, 3, 1, 1,
        )

        textview2, textbuffer2 = self.add_textview(grid,
            'warning_list',
            0, 4, 1, 1,
        )
        textview2.set_editable(False)
        textview2.set_wrap_mode(Gtk.WrapMode.WORD)


    # Callback class methods


#   def on_button_apply_clicked():  # Inherited from GenericConfigWin


#   def on_button_edit_clicked():   # Inherited from GenericConfigWin


#   def on_button_remove_clicked(): # Inherited from GenericConfigWin


    def never_called_func(self):

        """Function that is never called, but which makes this class object
        collapse neatly in my IDE."""

        pass


class FolderEditWin(GenericEditWin):

    """Python class for an 'edit window' to modify values in a media.Folder
    object.

    Args:

        app_obj (mainapp.TartubeApp): The main application object

        edit_obj (media.Folder): The object whose attributes will be edited in
            this window

    """


    # Standard class methods


    def __init__(self, app_obj, edit_obj):

        Gtk.Window.__init__(self, title='Folder properties')

        # IV list - class objects
        # -----------------------
        # The mainapp.TartubeApp object
        self.app_obj = app_obj
        # The media.Folder object being edited
        self.edit_obj = edit_obj


        # IV list - Gtk widgets
        # ---------------------
        self.grid = None                        # Gtk.Grid
        self.notebook = None                    # Gtk.Notebook
        self.reset_button = None                # Gtk.Button
        self.apply_button = None                # Gtk.Button
        self.ok_button = None                   # Gtk.Button
        self.cancel_button = None               # Gtk.Button
        # (Non-standard widgets)
        self.apply_button = None                # Gtk.Button
        self.edit_button = None                 # Gtk.Button
        self.remove_button = None               # Gtk.Button


        # IV list - other
        # ---------------
        # Size (in pixels) of gaps between edit window widgets
        self.spacing_size = self.app_obj.default_spacing_size
        # Flag set to True if all four buttons ('Reset', 'Apply', 'Cancel' and
        #   'OK' are required, or False if just the 'OK' button is required
        self.multi_button_flag = False

        # When the user changes a value, it is not applied to self.edit_obj
        #   immediately; instead, it is stored temporarily in this dictionary
        # If the user clicks the 'OK' or 'Apply' buttons at the bottom of the
        #   window, the changes are applied to self.edit_obj
        # If the user clicks the 'Reset' or 'Cancel' buttons, the dictionary
        #   is emptied and the changes are lost
        # The key-value pairs in the dictionary correspond directly to
        #   the names of attributes, and their balues in self.edit_obj
        # Key-value pairs are added to this dictionary whenever the user
        #   makes a change (so if no changes are made when the window is
        #   closed, the dictionary will still be empty)
        self.edit_dict = {}


        # Code
        # ----

        # Set up the edit window
        self.setup()


    # Public class methods


#   def setup():                # Inherited from GenericConfigWin


#   def setup_grid():           # Inherited from GenericConfigWin


#   def setup_notebook():       # Inherited from GenericConfigWin


#   def add_notebook_tab():     # Inherited from GenericConfigWin


#   def setup_button_strip():   # Inherited from GenericEditWin


#   def setup_gap():            # Inherited from GenericConfigWin


    # (Non-widget functions)


#   def apply_changes():        # Inherited from GenericConfigWin


#   def retrieve_val():         # Inherited from GenericConfigWin


    # (Setup tabs)


    def setup_tabs(self):

        """Called by self.setup(), .on_button_apply_clicked() and
        .on_button_reset_clicked().

        Sets up the tabs for this edit window.
        """

        self.setup_general_tab()


    def setup_general_tab(self):

        """Called by self.setup_tabs().

        Sets up the 'General' tab.
        """

        tab, grid = self.add_notebook_tab('_General')

        self.add_label(grid,
            '<u>General properties</u>',
            0, 0, 2, 1,
        )

        entry = self.add_entry(grid,
            None,
            0, 1, 1, 1,
        )
        entry.set_text('#' + str(self.edit_obj.dbid))
        entry.set_editable(False)
        entry.set_hexpand(False)
        entry.set_width_chars(8)

        entry2 = self.add_entry(grid,
            'name',
            1, 1, 1, 1,
        )
        entry2.set_editable(False)

        main_win_obj = self.app_obj.main_win_obj
        parent_obj = self.edit_obj.parent_obj
        if parent_obj:
            icon_path = main_win_obj.icon_dict['folder_none_large']
        else:
            icon_path = main_win_obj.icon_dict['folder_no_parent_none_large']

        self.add_image(grid,
            icon_path,
            0, 2, 1, 1,
        )

        entry3 = self.add_entry(grid,
            None,
            1, 2, 1, 1,
        )
        entry3.set_editable(False)
        if parent_obj:
            entry3.set_text(parent_obj.name)

        label = self.add_label(grid,
            'Directory',
            0, 3, 1, 1,
        )
        label.set_hexpand(False)

        entry4 = self.add_entry(grid,
            None,
            1, 3, 1, 1,
        )
        entry4.set_editable(False)
        entry4.set_text(self.edit_obj.get_dir(self.app_obj))

        # To avoid messing up the neat format of the rows above, add another
        #   grid, and put the next set of widgets inside it
        grid2 = Gtk.Grid()
        grid.attach(grid2, 0, 4, 2, 1)
        grid2.set_vexpand(False)
        grid2.set_border_width(self.spacing_size)
        grid2.set_column_spacing(self.spacing_size)
        grid2.set_row_spacing(self.spacing_size)

        checkbutton = self.add_checkbutton(grid2,
            'Always simulate download of videos',
            'dl_sim_flag',
            0, 0, 1, 1,
        )
        checkbutton.set_sensitive(False)

        checkbutton2 = self.add_checkbutton(grid2,
            'This folder is marked as a favourite',
            'fav_flag',
            0, 1, 1, 1,
        )
        checkbutton2.set_sensitive(False)

        checkbutton3 = self.add_checkbutton(grid2,
            'This folder is hidden',
            'hidden_flag',
            0, 2, 1, 1,
        )
        checkbutton3.set_sensitive(False)

        checkbutton4 = self.add_checkbutton(grid2,
            'This folder can\'t be deleted by the user',
            'fixed_flag',
            1, 0, 1, 1,
        )
        checkbutton4.set_sensitive(False)

        checkbutton5 = self.add_checkbutton(grid2,
            'This is a system-controlled folder',
            'priv_flag',
            1, 1, 1, 1,
        )
        checkbutton5.set_sensitive(False)

        checkbutton6 = self.add_checkbutton(grid2,
            'Only videos can be added to this folder',
            'restrict_flag',
            1, 2, 1, 1,
        )
        checkbutton6.set_sensitive(False)

        checkbutton7 = self.add_checkbutton(grid2,
            'All contents deleted when ' \
            + utils.upper_case_first(__main__. __packagename__) \
            + ' shuts down',
            'temp_flag',
            1, 3, 1, 1,
        )
        checkbutton7.set_sensitive(False)

        # To avoid messing up the formatting again, but the next buttons inside
        #   an hbox
        hbox = Gtk.HBox()
        grid.attach(hbox, 0, 6, 2, 1)

        self.apply_button = Gtk.Button('Apply download options')
        hbox.pack_start(self.apply_button, True, True, self.spacing_size)
        self.apply_button.connect('clicked', self.on_button_apply_clicked)

        self.edit_button = Gtk.Button('Edit download options')
        hbox.pack_start(self.edit_button, True, True, self.spacing_size)
        self.edit_button.connect('clicked', self.on_button_edit_clicked)

        self.remove_button = Gtk.Button('Remove download options')
        hbox.pack_start(self.remove_button, True, True, self.spacing_size)
        self.remove_button.connect('clicked', self.on_button_remove_clicked)

        if self.edit_obj.options_obj:
            self.apply_button.set_sensitive(False)
        else:
            self.edit_button.set_sensitive(False)
            self.remove_button.set_sensitive(False)


    # Callback class methods


#   def on_button_apply_clicked():  # Inherited from GenericConfigWin


#   def on_button_edit_clicked():   # Inherited from GenericConfigWin


#   def on_button_remove_clicked(): # Inherited from GenericConfigWin


    def never_called_func(self):

        """Function that is never called, but which makes this class object
        collapse neatly in my IDE."""

        pass


class SystemPrefWin(GenericPrefWin):

    """Python class for a 'preference window' to modify various system
    settings.

    Args:

        app_obj (mainapp.TartubeApp): The main application object

    """


    # Standard class methods


    def __init__(self, app_obj):


        Gtk.Window.__init__(self, title='System preferences')

        # IV list - class objects
        # -----------------------
        # The mainapp.TartubeApp object
        self.app_obj = app_obj


        # IV list - Gtk widgets
        # ---------------------
        self.grid = None                        # Gtk.Grid
        self.notebook = None                    # Gtk.Notebook
        self.ok_button = None                   # Gtk.Button
        # (IVs used to handle widget changes in the 'General' tab)
        self.radiobutton = None                 # Gkt.RadioButton
        self.radiobutton2 = None                # Gkt.RadioButton
        self.radiobutton3 = None                # Gkt.RadioButton
        self.spinbutton = None                  # Gkt.SpinButton
        self.spinbutton2 = None                 # Gkt.SpinButton


        # IV list - other
        # ---------------
        # Size (in pixels) of gaps between preference window widgets
        self.spacing_size = self.app_obj.default_spacing_size


        # Code
        # ----

        # Set up the preference window
        self.setup()


    # Public class methods


#   def setup():                # Inherited from GenericConfigWin


#   def setup_grid():           # Inherited from GenericConfigWin


#   def setup_notebook():       # Inherited from GenericConfigWin


#   def add_notebook_tab():     # Inherited from GenericConfigWin


#   def setup_button_strip():   # Inherited from GenericPrefWin


#   def setup_gap():            # Inherited from GenericConfigWin


    # (Setup tabs)


    def setup_tabs(self):

        """Called by self.setup(), .on_button_apply_clicked() and
        .on_button_reset_clicked().

        Sets up the tabs for this preference window.
        """

        self.setup_general_tab()
        self.setup_backups_tab()
        self.setup_videos_tab()
        self.setup_ytdl_tab()
        self.setup_performance_tab()
        self.setup_debug_tab()


    def setup_general_tab(self):

        """Called by self.setup_tabs().

        Sets up the 'General' tab.
        """

        tab, grid = self.add_notebook_tab('_General')
        grid_width = 3

        # General preferences
        self.add_label(grid,
            '<u>General preferences</u>',
            0, 0, grid_width, 1,
        )

        label = self.add_label(grid,
            'Language',
            0, 1, 1, 1,
        )
        label.set_hexpand(False)

        # (This is a placeholder, to be replaced when we add translations)
        store = Gtk.ListStore(GdkPixbuf.Pixbuf, str)
        pixbuf = self.app_obj.file_manager_obj.load_to_pixbuf(
            os.path.abspath(os.path.join('icons', 'locale', 'flag_uk.png')),
        )
        store.append( [pixbuf, 'English'] )

        combo = Gtk.ComboBox.new_with_model(store)
        grid.attach(combo, 1, 1, (grid_width - 1), 1)
        combo.set_hexpand(True)

        renderer_pixbuf = Gtk.CellRendererPixbuf()
        combo.pack_start(renderer_pixbuf, False)
        combo.add_attribute(renderer_pixbuf, 'pixbuf', 0)

        renderer_text = Gtk.CellRendererText()
        combo.pack_start(renderer_text, True)
        combo.add_attribute(renderer_text, 'text', 1)

        combo.set_active(0)
        # (End of placeholder)

        label2 = self.add_label(grid,
            utils.upper_case_first(__main__. __packagename__) \
            + ' data directory',
            0, 2, 1, 1,
        )
        label2.set_hexpand(False)

        entry = self.add_entry(grid,
            self.app_obj.data_dir,
            False,
            1, 2, 1, 1,
        )
        entry.set_sensitive(False)

        button = Gtk.Button('Change')
        grid.attach(button, 2, 2, 1, 1)
        button.connect('clicked', self.on_data_dir_button_clicked, entry)
        if self.app_obj.disable_load_save_flag:
            button.set_sensitive(False)

        # Main window preferences
        self.add_label(grid,
            '<u>Main window preferences</u>',
            0, 3, grid_width, 1,
        )

        checkbutton = self.add_checkbutton(grid,
            'Don\'t show labels in the toolbar',
            self.app_obj.toolbar_squeeze_flag,
            True,                   # Can be toggled by user
            0, 4, grid_width, 1,
        )
        checkbutton.connect('toggled', self.on_squeeze_button_toggled)

        # Operation preferences
        self.add_label(grid,
            '<u>Operation preferences</u>',
            0, 5, grid_width, 1,
        )

        checkbutton2 = self.add_checkbutton(grid,
            'Automatically update youtube-dl before every download operation',
            self.app_obj.operation_auto_update_flag,
            True,                   # Can be toggled by user
            0, 6, grid_width, 1,
        )
        checkbutton2.connect('toggled', self.on_auto_update_button_toggled)

        checkbutton3 = self.add_checkbutton(grid,
            'Automatically save files at the end of a download/update/' \
            + 'refresh operation',
            self.app_obj.operation_save_flag,
            True,                   # Can be toggled by user
            0, 7, grid_width, 1,
        )
        checkbutton3.connect('toggled', self.on_save_button_toggled)

        checkbutton4 = self.add_checkbutton(grid,
            'Show a dialogue window at the end of a download/update/refresh' \
            + ' operation',
            self.app_obj.operation_dialogue_flag,
            True,                   # Can be toggled by user
            0, 8, grid_width, 1,
        )
        checkbutton4.connect('toggled', self.on_dialogue_button_toggled)

        # Module preferences
        self.add_label(grid,
            '<u>Module preferences</u>',
            0, 9, grid_width, 1,
        )

        checkbutton5 = self.add_checkbutton(grid,
            'Use \'moviepy\' module to get a video\'s duration, if not known'
            + ' (may be slow)',
            self.app_obj.use_module_moviepy_flag,
            True,                   # Can be toggled by user
            0, 10, grid_width, 1,
        )
        checkbutton5.connect('toggled', self.on_moviepy_button_toggled)
        if not mainapp.HAVE_MOVIEPY_FLAG:
            checkbutton5.set_sensitive(False)


    def setup_backups_tab(self):

        """Called by self.setup_tabs().

        Sets up the 'Backups' tab.
        """

        tab, grid = self.add_notebook_tab('_Backups')

        # General preferences
        self.add_label(grid,
            '<u>Backup preferences</u>',
            0, 0, 1, 1,
        )
        self.add_label(grid,
            'When saving a database file, ' \
            + utils.upper_case_first(__main__. __packagename__) \
            + ' makes a backup copy of it (in case something goes wrong)',
            0, 1, 1, 1,
        )

        radiobutton = self.add_radiobutton(grid,
            None,
            'Delete the backup file as soon as the save procedure is' \
            + ' finished',
            0, 2, 1, 1,
        )
        # Signal connect appears below

        radiobutton2 = self.add_radiobutton(grid,
            radiobutton,
            'Keep the backup file, replacing any previous backup file',
            0, 3, 1, 1,
        )
        if self.app_obj.db_backup_mode == 'single':
            radiobutton2.set_active(True)
        # Signal connect appears below

        radiobutton3 = self.add_radiobutton(grid,
            radiobutton2,
            'Make a new backup file once per day, after the day\'s first' \
            + ' save procedure',
            0, 4, 1, 1,
        )
        if self.app_obj.db_backup_mode == 'daily':
            radiobutton3.set_active(True)
        # Signal connect appears below

        radiobutton4 = self.add_radiobutton(grid,
            radiobutton3,
            'Make a new backup file for every save procedure',
            0, 5, 1, 1,
        )
        if self.app_obj.db_backup_mode == 'always':
            radiobutton4.set_active(True)
        # Signal connect appears below

        # Signal connects from above
        radiobutton.connect(
            'toggled',
            self.on_backup_button_toggled,
            'default',
        )

        radiobutton2.connect(
            'toggled',
            self.on_backup_button_toggled,
            'single',
        )

        radiobutton3.connect(
            'toggled',
            self.on_backup_button_toggled,
            'daily',
        )

        radiobutton4.connect(
            'toggled',
            self.on_backup_button_toggled,
            'always',
        )


    def setup_videos_tab(self):

        """Called by self.setup_tabs().

        Sets up the 'Videos' tab.
        """

        tab, grid = self.add_notebook_tab('_Videos')
        grid_width = 2

        # Video matching preferences
        self.add_label(grid,
            '<u>Video matching preferences</u>',
            0, 0, grid_width, 1,
        )

        self.add_label(grid,
            'When matching videos on the filesystem:',
            0, 1, grid_width, 1,
        )

        self.radiobutton = self.add_radiobutton(grid,
            None,
            'The video names must match exactly',
            0, 2, grid_width, 1,
        )
        # Signal connect appears below

        self.radiobutton2 = self.add_radiobutton(grid,
            self.radiobutton,
            'The first n characters must match exactly',
            0, 3, (grid_width - 1), 1,
        )
        # Signal connect appears below

        self.spinbutton = self.add_spinbutton(grid,
            1, 999, 1, self.app_obj.match_first_chars,
            2, 3, 1, 1,
        )
        # Signal connect appears below

        self.radiobutton3 = self.add_radiobutton(grid,
            self.radiobutton2,
            'Ignore the last n characters; the remaining name must match' \
            + ' exactly',
            0, 4, (grid_width - 1), 1,
        )
        # Signal connect appears below

        self.spinbutton2 = self.add_spinbutton(grid,
            1, 999, 1, self.app_obj.match_ignore_chars,
            2, 4, 1, 1,
        )
        # Signal connect appears below

        self.add_label(grid,
            'In the Video Index (the left side of the \'Videos\' tab):',
            0, 5, grid_width, 1,
        )

        checkbutton = self.add_checkbutton(grid,
            'Show detailed statistics about the videos in each channel' \
            + ' / playlist / folder',
            self.app_obj.complex_index_flag,
            True,               # Can be toggled by user
            0, 6, grid_width, 1,
        )
        checkbutton.connect('toggled', self.on_complex_button_toggled)

        # (Widgets are sensitised/desensitised, based on the radiobutton)
        if self.app_obj.match_method == 'exact_match':
            self.spinbutton.set_sensitive(False)
            self.spinbutton2.set_sensitive(False)
        elif self.app_obj.match_method == 'match_first':
            self.radiobutton2.set_active(True)
            self.spinbutton2.set_sensitive(False)
        else:
            self.radiobutton3.set_active(True)
            self.spinbutton.set_sensitive(False)

        # Signal connects from above
        self.radiobutton.connect('toggled', self.on_match_button_toggled)
        self.radiobutton2.connect('toggled', self.on_match_button_toggled)
        self.radiobutton3.connect('toggled', self.on_match_button_toggled)
        self.spinbutton.connect(
            'value-changed',
            self.on_match_spinbutton_changed,
        )
        self.spinbutton2.connect(
            'value-changed',
            self.on_match_spinbutton_changed,
        )


    def setup_ytdl_tab(self):

        """Called by self.setup_tabs().

        Sets up the 'youtube-dl' tab.
        """

        tab, grid = self.add_notebook_tab('_youtube-dl')

        # youtube-dl preferences
        self.add_label(grid,
            '<u>youtube-dl preferences</u>',
            0, 0, 2, 1,
        )

        label = self.add_label(grid,
            'youtube-dl executable (system-dependant)',
            0, 1, 1, 1,
        )

        entry = self.add_entry(grid,
            self.app_obj.ytdl_bin,
            False,
            1, 1, 1, 1,
        )
        entry.set_sensitive(False)

        label2 = self.add_label(grid,
            'Default path to youtube-dl executable',
            0, 2, 1, 1,
        )

        entry2 = self.add_entry(grid,
            self.app_obj.ytdl_path_default,
            False,
            1, 2, 1, 1,
        )
        entry2.set_sensitive(False)

        label3 = self.add_label(grid,
            'Actual path to use during download/update/refresh operations',
            0, 3, 1, 1,
        )

        combo_list = [
            [
                'Use default path (' + self.app_obj.ytdl_path_default \
                + ')',
                self.app_obj.ytdl_path_default,
            ],
            [
                'Use local path (' + self.app_obj.ytdl_bin + ')',
                self.app_obj.ytdl_bin,
            ],
        ]

        store = Gtk.ListStore(str, str)
        for mini_list in combo_list:
            store.append( [ mini_list[0], mini_list[1] ] )

        combo = Gtk.ComboBox.new_with_model(store)
        grid.attach(combo, 1, 3, 1, 1)
        renderer_text = Gtk.CellRendererText()
        combo.pack_start(renderer_text, True)
        combo.add_attribute(renderer_text, "text", 0)
        combo.set_entry_text_column(0)

        if self.app_obj.ytdl_path == self.app_obj.ytdl_path_default:
            combo.set_active(0)
        else:
            combo.set_active(1)

        combo.connect('changed', self.on_ytdl_path_combo_changed)

        label4 = self.add_label(grid,
            'Shell command for update operations',
            0, 4, 1, 1,
        )

        combo2 = self.add_combo(grid,
            self.app_obj.ytdl_update_list,
            self.app_obj.ytdl_update_current,
            1, 4, 1, 1,
        )
        combo2.connect('changed', self.on_update_combo_changed)

        # Timeout preferences
        self.add_label(grid,
            '<u>Timeout preferences</u>',
            0, 5, 2, 1,
        )

        checkbutton = self.add_checkbutton(grid,
            'When checking videos, apply a 60-second timeout while fetching' \
            + ' JSON data',
            self.app_obj.apply_json_timeout_flag,
            True,                   # Can be toggled by user
            0, 6, 2, 1,
        )
        checkbutton.connect('toggled', self.on_json_button_toggled)

        # Errors/Warnings tab preferences
        self.add_label(grid,
            '<u>Errors/Warnings tab preferences</u>',
            0, 7, 2, 1,
        )

        checkbutton2 = self.add_checkbutton(grid,
            'Ignore \'Requested formats are incompatible for merge\' warnings',
            self.app_obj.ignore_merge_warning_flag,
            True,                   # Can be toggled by user
            0, 8, 2, 1,
        )
        checkbutton2.connect('toggled', self.on_merge_button_toggled)

        checkbutton3 = self.add_checkbutton(grid,
            'Ignore YouTube copyright errors',
            self.app_obj.ignore_yt_copyright_flag,
            True,                   # Can be toggled by user
            0, 9, 2, 1,
        )
        checkbutton3.connect('toggled', self.on_copyright_button_toggled)

        checkbutton4 = self.add_checkbutton(grid,
            'Ignore \'Child process exited with non-zero code\' errors',
            self.app_obj.ignore_child_process_exit_flag,
            True,                   # Can be toggled by user
            0, 10, 2, 1,
        )
        checkbutton4.connect('toggled', self.on_child_process_button_toggled)


    def setup_performance_tab(self):

        """Called by self.setup_tabs().

        Sets up the 'Performance' tab.
        """

        tab, grid = self.add_notebook_tab('_Performance')
        grid_width = 3

        # Performance limits
        self.add_label(grid,
            '<u>Performance limits</u>',
            0, 0, grid_width, 1,
        )

        checkbutton = self.add_checkbutton(grid,
            'Limit simultaneous downloads to',
            self.app_obj.num_worker_apply_flag,
            True,               # Can be toggled by user
            0, 1, 1, 1,
        )
        checkbutton.set_hexpand(False)
        checkbutton.connect('toggled', self.on_worker_button_toggled)

        spinbutton = self.add_spinbutton(grid,
            self.app_obj.num_worker_min,
            self.app_obj.num_worker_max,
            1,                  # Step
            self.app_obj.num_worker_default,
            1, 1, 1, 1,
        )
        spinbutton.connect('value-changed', self.on_worker_spinbutton_changed)

        checkbutton2 = self.add_checkbutton(grid,
            'Limit download speed to',
            self.app_obj.bandwidth_apply_flag,
            True,               # Can be toggled by user
            0, 2, 1, 1,
        )
        checkbutton2.set_hexpand(False)
        checkbutton2.connect('toggled', self.on_bandwidth_button_toggled)

        spinbutton2 = self.add_spinbutton(grid,
            self.app_obj.bandwidth_min,
            self.app_obj.bandwidth_max,
            1,                  # Step
            self.app_obj.bandwidth_default,
            1, 2, 1, 1,
        )
        spinbutton2.connect(
            'value-changed',
            self.on_bandwidth_spinbutton_changed,
        )

        self.add_label(grid,
            'KiB/s',
            2, 2, 1, 1,
        )

        # Time-saving preferences
        self.add_label(grid,
            '<u>Time-saving preferences</u>',
            0, 3, grid_width, 1,
        )

        checkbutton3 = self.add_checkbutton(grid,
            'Stop checking/downloading a channel/playlist when it starts' \
            + ' sending videos we already have',
            self.app_obj.operation_limit_flag,
            True,               # Can be toggled by user
            0, 4, grid_width, 1,
        )
        checkbutton3.set_hexpand(False)
        # Signal connect appears below

        self.add_label(grid,
            'Stop after this many videos (when checking)',
            0, 5, 1, 1,
        )

        entry = self.add_entry(grid,
            self.app_obj.operation_check_limit,
            True,
            1, 5, 1, 1,
        )
        entry.set_hexpand(False)
        entry.set_width_chars(4)
        entry.connect('changed', self.on_check_limit_changed)
        if not self.app_obj.operation_limit_flag:
            entry.set_sensitive(False)

        self.add_label(grid,
            'Stop after this many videos (when downloading)',
            0, 6, 1, 1,
        )

        entry2 = self.add_entry(grid,
            self.app_obj.operation_download_limit,
            True,
            1, 6, 1, 1,
        )
        entry2.set_hexpand(False)
        entry2.set_width_chars(4)
        entry2.connect('changed', self.on_download_limit_changed)
        if not self.app_obj.operation_limit_flag:
            entry2.set_sensitive(False)

        # Signal connect from above
        checkbutton3.connect(
            'toggled',
            self.on_limit_button_toggled,
            entry,
            entry2,
        )


    def setup_debug_tab(self):

        """Called by self.setup_tabs().

        Sets up the 'Debug' tab.
        """

        tab, grid = self.add_notebook_tab('_Debug')

        # Debugging options
        self.add_label(grid,
            '<u>Debugging options</u>',
            0, 0, 1, 1,
        )

        checkbutton = self.add_checkbutton(grid,
            'Write output from youtube-dl\'s STDOUT to the terminal',
            self.app_obj.ytdl_write_stdout_flag,
            True,               # Can be toggled by user
            0, 1, 1, 1,
        )
        checkbutton.set_hexpand(False)
        # Signal connect appears below

        checkbutton2 = self.add_checkbutton(grid,
            '...but don\'t write each video\'s JSON data',
            self.app_obj.ytdl_write_ignore_json_flag,
            True,               # Can be toggled by user
            0, 2, 1, 1,
        )
        checkbutton2.set_hexpand(False)
        checkbutton2.connect('toggled', self.on_stdout_json_button_toggled)
        if not self.app_obj.ytdl_write_stdout_flag:
            checkbutton2.set_sensitive(False)

        # Signal connect from above
        checkbutton.connect(
            'toggled',
            self.on_stdout_button_toggled,
            checkbutton2,
        )

        checkbutton3 = self.add_checkbutton(grid,
            'Write output from youtube-dl\'s STDERR to the terminal',
            self.app_obj.ytdl_write_stderr_flag,
            True,               # Can be toggled by user
            0, 3, 1, 1,
        )
        checkbutton3.set_hexpand(False)
        checkbutton3.connect('toggled', self.on_stderr_button_toggled)

        checkbutton4 = self.add_checkbutton(grid,
            'Write verbose output (youtube-dl debugging mode)',
            self.app_obj.ytdl_write_verbose_flag,
            True,               # Can be toggled by user
            0, 4, 1, 1,
        )
        checkbutton4.set_hexpand(False)
        checkbutton4.connect('toggled', self.on_verbose_button_toggled)


    # Callback class methods


    def on_auto_update_button_toggled(self, checkbutton):

        """Called from callback in self.setup_general_tab().

        Enables/disables automatic update operation before every download
        operation.

        Args:

            checkbutton (Gtk.CheckButton): The widget clicked

        """

        if checkbutton.get_active() \
        and not self.app_obj.operation_auto_update_flag:
            self.app_obj.set_operation_auto_update_flag(True)
        elif not checkbutton.get_active() \
        and self.app_obj.operation_auto_update_flag:
            self.app_obj.set_operation_auto_update_flag(False)


    def on_backup_button_toggled(self, radiobutton, value):

        """Called from callback in self.setup_backups_tab().

        Updates IVs in the main application.

        Args:

            radiobutton (Gtk.RadioButton): The widget clicked

            value (string): The new value of the IV

        """

        if radiobutton.get_active():
            self.app_obj.set_db_backup_mode(value)


    def on_bandwidth_button_toggled(self, checkbutton):

        """Called from callback in self.setup_general_tab().

        Enables/disables the download speed limit. Toggling the corresponding
        Gtk.CheckButton in the Progress Tab sets the IV (and makes sure the two
        checkbuttons have the same status).

        Args:

            checkbutton (Gtk.CheckButton): The widget clicked

        """

        other_flag = self.app_obj.main_win_obj.checkbutton2.get_active()

        if (checkbutton.get_active() and not other_flag):
            self.app_obj.main_win_obj.checkbutton2.set_active(True)
        elif (not checkbutton.get_active() and other_flag):
            self.app_obj.main_win_obj.checkbutton2.set_active(False)


    def on_bandwidth_spinbutton_changed(self, spinbutton):

        """Called from callback in self.setup_general_tab().

        Sets the simultaneous download limit. Setting the value of the
        corresponding Gtk.SpinButton in the Progress Tab sets the IV (and
        makes sure the two spinbuttons have the same value).

        Args:

            spinbutton (Gtk.SpinButton): The widget clicked

        """

        self.app_obj.main_win_obj.spinbutton2.set_value(spinbutton.get_value())


    def on_check_limit_changed(self, entry):

        """Called from callback in self.setup_performance_tab().

        Sets the limit at which a download operation will stop checking a
        channel or playlist.

        Args:

            entry (Gtk.Entry): The widget changed

        """

        text = entry.get_text()
        if text.isdigit() and int(text) >= 0:
            self.app_obj.set_operation_check_limit(int(text))


    def on_complex_button_toggled(self, checkbutton):

        """Called from callback in self.setup_videos_tab().

        Switches between simple/complex views in the Video Index.

        Args:

            checkbutton (Gtk.CheckButton): The widget clicked

        """

        redraw_flag = False
        if checkbutton.get_active() and not self.app_obj.complex_index_flag:
            self.app_obj.set_complex_index_flag(True)
            redraw_flag = True
        elif not checkbutton.get_active() and self.app_obj.complex_index_flag:
            self.app_obj.set_complex_index_flag(False)
            redraw_flag = True

        if redraw_flag:
            # Redraw the Video Index and the Video Catalogue (since nothing in
            #   the Video Index will be selected)
            self.app_obj.main_win_obj.video_index_reset()
            self.app_obj.main_win_obj.video_catalogue_reset()
            self.app_obj.main_win_obj.video_index_populate()


    def on_child_process_button_toggled(self, checkbutton):

        """Called from callback in self.setup_ytdl_tab().

        Enables/disables ignoring of child process exit error messages.

        Args:

            checkbutton (Gtk.CheckButton): The widget clicked

        """

        if checkbutton.get_active() \
        and not self.app_obj.ignore_child_process_exit_flag:
            self.app_obj.set_ignore_child_process_exit_flag(True)
        elif not checkbutton.get_active() \
        and self.app_obj.ignore_child_process_exit_flag:
            self.app_obj.set_ignore_child_process_exit_flag(False)


    def on_copyright_button_toggled(self, checkbutton):

        """Called from callback in self.setup_ytdl_tab().

        Enables/disables ignoring of YouTube copyright errors messages.

        Args:

            checkbutton (Gtk.CheckButton): The widget clicked

        """

        if checkbutton.get_active() \
        and not self.app_obj.ignore_yt_copyright_flag:
            self.app_obj.set_ignore_yt_copyright_flag(True)
        elif not checkbutton.get_active() \
        and self.app_obj.ignore_yt_copyright_flag:
            self.app_obj.set_ignore_yt_copyright_flag(False)


    def on_data_dir_button_clicked(self, button, entry):

        """Called from callback in self.setup_general_tab().

        Opens a window in which the user can select Tartube's data directoy.
        If the user actually selects it, call the main application to take
        action.

        Args:

            button (Gtk.Button): The widget clicked

            entry (Gtk.Entry): Another widget to be modified by this function

        """

        dialogue_win = Gtk.FileChooserDialog(
            'Please select ' \
            + utils.upper_case_first(__main__.__packagename__) \
            + '\'s data directory',
            self,
            Gtk.FileChooserAction.SELECT_FOLDER,
            (
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN, Gtk.ResponseType.OK,
            ),
        )

        response = dialogue_win.run()
        if response == Gtk.ResponseType.OK:
            new_path = dialogue_win.get_filename()

        dialogue_win.destroy()

        if response == Gtk.ResponseType.OK:

            # In the past, I accidentally created a new database directory
            #   just inside an existing one, rather than switching to the
            #   existing one
            # If no database file exists, prompt the user to create a new one
            db_path = os.path.abspath(
                os.path.join(new_path, self.app_obj.db_file_name),
            )
            if not os.path.isfile(db_path):

                self.app_obj.dialogue_manager_obj.show_msg_dialogue(
                    'Are you sure you want to create\na new database at this' \
                    + ' location?\n\n' + new_path,
                    'question',
                    'yes-no',
                    self,           # Parent window is this window
                    {
                        'yes': 'switch_db',
                        'data': [new_path, self],
                    },
                )

            # Database file already exists, so load it now
            elif not self.app_obj.switch_db([new_path, self]):

                if self.app_obj.disable_load_save_flag:
                    button.set_sensitive(False)

                self.app_obj.dialogue_manager_obj.show_msg_dialogue(
                    'Database file not loaded',
                    'error',
                    'ok',
                    self,           # Parent window is this window
                )

            else:

                entry.set_text(self.app_obj.data_dir)
                if self.app_obj.disable_load_save_flag:
                    button.set_sensitive(False)

                self.app_obj.dialogue_manager_obj.show_msg_dialogue(
                    'Database file loaded',
                    'info',
                    'ok',
                    self,           # Parent window is this window
                )


    def on_dialogue_button_toggled(self, checkbutton):

        """Called from callback in self.setup_general_tab().

        Enables/disables the dialogue window at the end of a download/update/
        refresh operation.

        Args:

            checkbutton (Gtk.CheckButton): The widget clicked

        """

        if checkbutton.get_active() \
        and not self.app_obj.operation_dialogue_flag:
            self.app_obj.set_operation_dialogue_flag(True)
        elif not checkbutton.get_active() \
        and self.app_obj.operation_dialogue_flag:
            self.app_obj.set_operation_dialogue_flag(False)


    def on_download_limit_changed(self, entry):

        """Called from callback in self.setup_performance_tab().

        Sets the limit at which a download operation will stop downloading a
        channel or playlist.

        Args:

            entry (Gtk.Entry): The widget changed

        """

        text = entry.get_text()
        if text.isdigit() and int(text) >= 0:
            self.app_obj.set_operation_download_limit(int(text))


    def on_json_button_toggled(self, checkbutton):

        """Called from callback in self.setup_ytdl_tab().

        Enables/disables apply a 60-second timeout when fetching a video's JSON
        data.

        Args:

            checkbutton (Gtk.CheckButton): The widget clicked

        """

        if checkbutton.get_active() \
        and not self.app_obj.apply_json_timeout_flag:
            self.app_obj.set_apply_json_timeout_flag(True)
        elif not checkbutton.get_active() \
        and self.app_obj.apply_json_timeout_flag:
            self.app_obj.set_apply_json_timeout_flag(False)


    def on_limit_button_toggled(self, checkbutton, entry, entry2):

        """Called from callback in self.setup_performance_tab().

        Sets the limit at which a download operation will stop downloading a
        channel or playlist.

        Args:

            checkbutton (Gtk.CheckButton): The widget clicked
            entry, entry2 (Gtk.Entry): The entry boxes which must be
                sensitised/desensitised, according to the new setting of the IV

        """

        if checkbutton.get_active() and not self.app_obj.operation_limit_flag:
            self.app_obj.set_operation_limit_flag(True)
            entry.set_sensitive(True)
            entry2.set_sensitive(True)

        elif not checkbutton.get_active() \
        and self.app_obj.operation_limit_flag:
            self.app_obj.set_operation_limit_flag(False)
            entry.set_sensitive(False)
            entry2.set_sensitive(False)


    def on_match_button_toggled(self, radiobutton):

        """Called from callback in self.setup_videos_tab().

        Updates IVs in the main application and sensities/desensities widgets.

        Args:

            radiobutton (Gtk.RadioButton): The widget clicked

        """

        default_val = self.app_obj.match_default_chars

        if radiobutton.get_active():

            if radiobutton == self.radiobutton:
                self.app_obj.set_match_method('exact_match')
                # (Changing the contents of the widgets automatically updates
                #   mainapp.TartubeApp IVs)
                self.spinbutton.set_value(default_val)
                self.spinbutton.set_sensitive(False)
                self.spinbutton2.set_value(default_val)
                self.spinbutton2.set_sensitive(False)

            elif radiobutton == self.radiobutton2:
                self.app_obj.set_match_method('match_first')
                self.spinbutton.set_sensitive(True)
                self.spinbutton2.set_value(default_val)
                self.spinbutton2.set_sensitive(False)

            else:
                self.app_obj.set_match_method('ignore_last')
                self.spinbutton.set_value(default_val)
                self.spinbutton.set_sensitive(False)
                self.spinbutton2.set_sensitive(True)


    def on_match_spinbutton_changed(self, spinbutton):

        """Called from callback in self.setup_general_tab().

        Updates IVs in the main application and sensities/desensities widgets.

        Args:

            spinbutton (Gtk.SpinButton): The widget clicked

        """

        if spinbutton == self.spinbutton:
            self.app_obj.set_match_first_chars(spinbutton.get_value())
        else:
            self.app_obj.set_match_ignore_chars(spinbutton.get_value())


    def on_merge_button_toggled(self, checkbutton):

        """Called from callback in self.setup_ytdl_tab().

        Enables/disables ignoring of 'Requested formats are incompatible for
        merge and will be merged into mkv' warning messages.

        Args:

            checkbutton (Gtk.CheckButton): The widget clicked

        """

        if checkbutton.get_active() \
        and not self.app_obj.ignore_merge_warning_flag:
            self.app_obj.set_ignore_merge_warning_flag(True)
        elif not checkbutton.get_active() \
        and self.app_obj.ignore_merge_warning_flag:
            self.app_obj.set_ignore_merge_warning_flag(False)


    def on_moviepy_button_toggled(self, checkbutton):

        """Called from callback in self.setup_general_tab().

        Enables/disables use of the moviepy.editor module.

        Args:

            checkbutton (Gtk.CheckButton): The widget clicked

        """

        if checkbutton.get_active() \
        and not self.app_obj.use_module_moviepy_flag:
            self.app_obj.set_use_module_moviepy_flag(True)
        elif not checkbutton.get_active() \
        and self.app_obj.use_module_moviepy_flag:
            self.app_obj.set_use_module_moviepy_flag(False)


    def on_save_button_toggled(self, checkbutton):

        """Called from callback in self.setup_general_tab().

        Enables/disables automatic saving of files at the end of a download/
        update/refresh operation.

        Args:

            checkbutton (Gtk.CheckButton): The widget clicked

        """

        if checkbutton.get_active() and not self.app_obj.operation_save_flag:
            self.app_obj.set_operation_save_flag(True)
        elif not checkbutton.get_active() and self.app_obj.operation_save_flag:
            self.app_obj.set_operation_save_flag(False)


    def on_squeeze_button_toggled(self, checkbutton):

        """Called from callback in self.setup_general_tab().

        Enables/disables labels in the main window's main toolbar.

        Args:

            checkbutton (Gtk.CheckButton): The widget clicked

        """

        if checkbutton.get_active() \
        and not self.app_obj.toolbar_squeeze_flag:
            self.app_obj.set_toolbar_squeeze_flag(True)
        elif not checkbutton.get_active() \
        and self.app_obj.toolbar_squeeze_flag:
            self.app_obj.set_toolbar_squeeze_flag(False)


    def on_stderr_button_toggled(self, checkbutton):

        """Called from a callback in self.setup_ytdl_tab().

        Enables/disables writing output from youtube-dl's STDERR to the
        terminal.

        Args:

            checkbutton (Gtk.CheckButton): The widget clicked

        """

        if checkbutton.get_active() \
        and not self.app_obj.ytdl_write_stderr_flag:
            self.app_obj.set_ytdl_write_stderr_flag(True)
        elif not checkbutton.get_active() \
        and self.app_obj.ytdl_write_stderr_flag:
            self.app_obj.set_ytdl_write_stderr_flag(False)


    def on_stdout_button_toggled(self, checkbutton, checkbutton2):

        """Called from a callback in self.setup_ytdl_tab().

        Enables/disables writing output from youtube-dl's STDOUT to the
        terminal.

        Args:

            checkbutton (Gtk.CheckButton): The widget clicked

            checkbutton2 (Gtk.CheckButton): A different checkbutton to
                sensitise/desensitise, according to the new value of the flag

        """

        if checkbutton.get_active() \
        and not self.app_obj.ytdl_write_stdout_flag:
            self.app_obj.set_ytdl_write_stdout_flag(True)
            checkbutton2.set_sensitive(True)

        elif not checkbutton.get_active() \
        and self.app_obj.ytdl_write_stdout_flag:
            self.app_obj.set_ytdl_write_stdout_flag(False)
            checkbutton2.set_sensitive(False)


    def on_stdout_json_button_toggled(self, checkbutton):

        """Called from a callback in self.setup_ytdl_tab().

        Enables/disables writing output from youtube-dl's STDOUT to the
        terminal.

        Args:

            checkbutton (Gtk.CheckButton): The widget clicked

        """

        if checkbutton.get_active() \
        and not self.app_obj.ytdl_write_ignore_json_flag:
            self.app_obj.set_ytdl_write_ignore_json_flag(True)
        elif not checkbutton.get_active() \
        and self.app_obj.ytdl_write_ignore_json_flag:
            self.app_obj.set_ytdl_write_ignore_json_flag(False)


    def on_update_combo_changed(self, combo):

        """Called from a callback in self.setup_ytdl_tab().

        Extracts the value visible in the combobox, converts it into another
        value, and uses that value to update the main application's IV.

        Args:

            combo (Gtk.ComboBox): The widget clicked

        """

        tree_iter = combo.get_active_iter()
        model = combo.get_model()
        self.app_obj.set_ytdl_update_current(model[tree_iter][0])


    def on_verbose_button_toggled(self, checkbutton):

        """Called from a callback in self.setup_ytdl_tab().

        Enables/disables writing verbose output (youtube-dl debugging mode).

        Args:

            checkbutton (Gtk.CheckButton): The widget clicked

        """

        if checkbutton.get_active() \
        and not self.app_obj.ytdl_write_verbose_flag:
            self.app_obj.set_ytdl_write_verbose_flag(True)
        elif not checkbutton.get_active() \
        and self.app_obj.ytdl_write_verbose_flag:
            self.app_obj.set_ytdl_write_verbose_flag(False)


    def on_worker_button_toggled(self, checkbutton):

        """Called from callback in self.setup_general_tab().

        Enables/disables the simultaneous download limit. Toggling the
        corresponding Gtk.CheckButton in the Progress Tab sets the IV (and
        makes sure the two checkbuttons have the same status).

        Args:

            checkbutton (Gtk.CheckButton): The widget clicked

        """

        other_flag = self.app_obj.main_win_obj.checkbutton.get_active()

        if (checkbutton.get_active() and not other_flag):
            self.app_obj.main_win_obj.checkbutton.set_active(True)
        elif (not checkbutton.get_active() and other_flag):
            self.app_obj.main_win_obj.checkbutton.set_active(False)


    def on_worker_spinbutton_changed(self, spinbutton):

        """Called from callback in self.setup_general_tab().

        Sets the simultaneous download limit. Setting the value of the
        corresponding Gtk.SpinButton in the Progress Tab sets the IV (and
        makes sure the two spinbuttons have the same value).

        Args:

            spinbutton (Gtk.SpinButton): The widget clicked

        """

        self.app_obj.main_win_obj.spinbutton.set_value(spinbutton.get_value())


    def on_ytdl_path_combo_changed(self, combo):

        """Called from a callback in self.setup_ytdl_tab().

        Extracts the value visible in the combobox, converts it into another
        value, and uses that value to update the main application's IV.

        Args:

            combo (Gtk.ComboBox): The widget clicked

        """

        tree_iter = combo.get_active_iter()
        model = combo.get_model()
        self.app_obj.set_ytdl_path(model[tree_iter][1])

