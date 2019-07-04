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


"""Main application class."""


# Import Gtk modules
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, GdkPixbuf


# Import Python standard modules
from gi.repository import Gio
import cgi
import datetime
import json
import os
import pickle
import re
import shutil
import sys
import time


# Import other Python modules
try:
    import moviepy.editor
    HAVE_MOVIEPY_FLAG = True
except:
    HAVE_MOVIEPY_FLAG = False


# Import our modules
import __main__
from . import config
from . import dialogue
from . import downloads
from . import files
from . import formats
from . import mainwin
from . import media
from . import options
from . import refresh
from . import testing
from . import updates
from . import utils


# !!! Debugging flag
DEBUG_FUNC_FLAG = False


# Classes


class TartubeApp(Gtk.Application):

    """Main python class for the Tartube application."""


    # Standard class methods


    def __init__(self, *args, **kwargs):

        if DEBUG_FUNC_FLAG:
            print('ap 87 __init__')

        super(TartubeApp, self).__init__(
            *args,
            application_id=__main__.__app_id__,
            flags=Gio.ApplicationFlags.FLAGS_NONE,
            **kwargs)

        # Debugging flags (can only be set by editing the source code)
        # Delete the config file and the contents of Tartube's data directory
        #   on startup
        self.debug_delete_data_flag = False
        # After installation, don't show the dialogue windows prompting the
        #   user to choose Tartube's data directory; just use the default
        #   location
        self.debug_no_dialogue_flag = False
        # In the main window's menu, show a menu item for adding a set of
        #   media data objects for testing
        self.debug_test_media_menu_flag = False
        # In the main window's toolbar, show a toolbar item for adding a set of
        #   media data objects for testing
        self.debug_test_media_toolbar_flag = False
        # Show an dialogue window with 'Tartube is already running!' if the
        #   user tries to open a second instance of Tartube
        self.debug_warn_multiple_flag = False
        # Open the main window in the top-left corner of the desktop
        self.debug_open_top_left_flag = False
        # Automatically open the system preferences window on startup
        self.debug_open_pref_win_flag = False
        # Hide all the system folders (this is not reversible by setting the
        #   flag back to False)
        self.debug_hide_folders_flag = False

        # Instance variable (IV) list - class objects
        # -------------------------------------------
        # The main window object, set as soon as it's created
        self.main_win_obj = None
        #
        # At the moment, there are three operations - the download, update and
        #   refresh operations
        # Only one operation can be in progress at a time. When an operation is
        #   in progress, many functions (such as opening configuration windows)
        #   are not possible
        #
        # A download operation is handled by a downloads.DownloadManager
        #   object. It downloads files from a server (for example, it downloads
        #   videos from YouTube)
        # Although its not possible to run more than one download
        #   operation at a time, a single download operation can handle
        #   multiple simultaneous downloads
        # The current downloads.DownloadManager object, if a download operation
        #   is in progress (or None, if not)
        self.download_manager_obj = None
        # An update operation (to update youtube-dl) is handled by an
        #   updates.UpdateManager object. It updates youtube-dl to the latest
        #   version
        # The current updates.UpdateManager object, if an upload operation is
        #   in progress (or None, if not)
        self.update_manager_obj = None
        # A refresh operation compares the media registry with the contents of
        #   Tartube's data directories, adding new videos to the media registry
        #   and marking missing videos as not downloaded, as appropriate
        # The current refresh.RefreshManager object, if a refresh operation is
        #   in progress (or None, if not)
        self.refresh_manager_obj = None
        # When any operation is in progress, the manager object is stored here
        #   (so code can quickly check if an operation is in progress, or not)
        self.current_manager_obj = None
        #
        # The file manager, files.FileManager, for loading thumbnail, icon
        #   and JSON files safely (i.e. without causing a Gtk crash)
        self.file_manager_obj = files.FileManager()
        # The message dialogue manager, dialogue.DialogueManager, for showing
        #   message dialogue windows safely (i.e. without causing a Gtk crash)
        self.dialogue_manager_obj = None
        #
        # Media data classes are those specified in media.py. Those class
        #   objects are media.Video (for individual videos), media.Channel,
        #   media.Playlist and media.Folder (reprenting a sub-directory inside
        #   Tartube's data directory)
        # Some media data objects have a list of children which are themselves
        #   media data objects. In that way, the user can organise their videos
        #   in convenient folders
        # media.Folder objects can have any media data objects as their
        #   children (including other media.Folder objects). media.Channel and
        #   media.Playlist objects can have media.Video objects as their
        #   children. media.Video objects don't have any children
        # (Media data objects are stored in IVs below)
        #
        # During a download operation, youtube-dl is supplied with a set of
        #   download options. Those options are specified by an
        #   options.OptionsManager object
        # Each media data object may have its own options.OptionsManager
        #   object. If not, it uses the options.OptionsManager object of its
        #   parent (or of its parent's parent, and so on)
        # If this chain of family relationships doesn't provide an
        #   options.OptionsManager object, then this default object, known as
        #   the General Options Manager, is used
        self.general_options_obj = None


        # Instance variable (IV) list - other
        # -----------------------------------
        # Default window sizes (in pixels)
        self.main_win_width = 800
        self.main_win_height = 600
        self.config_win_width = 650
        self.config_win_height = 450
        # Flag set to True if the main toolbar should be compressed (by
        #   removing the labels); ideal if the toolbar's contents won't fit in
        #   the standard-sized window (as it almost certainly won't on MS
        #   Windows)
        if os.name != 'nt':
            self.toolbar_squeeze_flag = False
        else:
            self.toolbar_squeeze_flag = True
        # Default size (in pixels) of space between various widgets
        self.default_spacing_size = 5

        # Tartube's data directory (platform-dependant), i.e. 'tartube-data'
        # Note that, using the MSWin installer, Cygwin gives file paths with
        #   both / and \ separators. Throughout the code, we use
        #   os.path.abspath to circumvent this problem
        self.data_dir = os.path.abspath(
            os.path.join(
                os.path.expanduser('~'),
                __main__.__packagename__ + '-data',
            ),
        )
        # The sub-directory into which videos are downloaded
        self.downloads_dir = os.path.abspath(
            os.path.join(
                os.path.expanduser('~'),
                __main__.__packagename__ + '-data',
                'downloads',
            ),
        )
        # A temporary directory, deleted when Tartube starts and stops
        self.temp_dir = os.path.abspath(
            os.path.join(
                os.path.expanduser('~'),
                __main__.__packagename__ + '-data',
                '.temp',
            ),
        )
        # Inside the temporary directory, a downloads folder, replicating the
        #   layout of self.downloads_dir, and used for storing description,
        #   JSON and thumbnail files which the user doesn't want to store in
        #   self.downloads_dir
        self.temp_dl_dir = os.path.abspath(
            os.path.join(
                os.path.expanduser('~'),
                __main__.__packagename__ + '-data',
                '.temp',
                'downloads',
            ),
        )

        # Name of the Tartube config file, always found in the same directory
        #   as tartube.py
        self.config_file_name = 'settings.json'
        # Name of the Tartube database file (storing media data objects). The
        #   database file is always found in self.data_dir
        self.db_file_name = __main__.__packagename__ + '.db'
        # How Tartube should make backups of its database file:
        #   'default' - make a backup file during a save operation, but delete
        #       it when the save operation is complete
        #   'single' - make a backup file during a save operation, replacing
        #       any existing backup file, and don't delete it when the save
        #       operation is complete
        #   'daily' - make a backup file once per day, the first time a save
        #       operation is performed in that day. The file is labelled with
        #       the date, so backup files from previous days are not
        #       overwritten
        #   'always' - always make a backup file, labelled with the date and
        #       time, so that no backup file is ever overwritten
        self.db_backup_mode = 'single'
        # If loading/saving of a config or database file fails, this flag is
        #   set to True, which disables all loading/saving for the rest of the
        #   session
        self.disable_load_save_flag = False

        # The youtube-dl binary to use (platform-dependant) - 'youtube-dl' or
        #   'youtube-dl.exe', depending on the platform. The default value is
        #   set by self.start()
        self.ytdl_bin = None
        # The default path to the youtube-dl binary. The value is set by
        #   self.start(). On MSWin, it is 'youtube-dl.exe'. On Linux, it is
        #   '/usr/bin/youtube-dl'
        self.ytdl_path_default = None
        # The actual path to use in the shell command during a download or
        #   update operation. Initially given the same value as
        #   self.ytdl_path_default
        # On MSWin, this value doesn't change. On Linux, depending on how
        #   youtube-dl was installed, it might be '/usr/bin/youtube-dl' or just
        #   'youtube-dl'
        self.ytdl_path = None
        # The shell command to use during an update operation depends on how
        #   youtube-dl was installed. A dictionary containing some
        #   possibilities, populated by self.start()
        # Dictionary in the form
        #   key: description of the update method
        #   value: list of words to use in the shell command
        self.ytdl_update_dict = {}
        # A list of keys from self.ytdl_update_dict in a standard order (so the
        #   combobox in config.SystemPrefWin is in a standard order)
        self.ytdl_update_list = []
        # The user's choice of shell command; one of the keys in
        #   self.ytdl_update_dict, set by self.start()
        self.ytdl_update_current = None

        # Flag set to True if output youtube-dl's STDOUT should be written to
        #   the terminal window
        self.ytdl_write_stdout_flag = False
        # Flag set to True if we should ignore JSON output when writing to the
        #   terminal window (ignored if self.ytdl_write_stdout_flag is False)
        self.ytdl_write_ignore_json_flag = True
        # Flag set to True if output youtube-dl's STDERR should be written to
        #   the terminal window
        self.ytdl_write_stderr_flag = False
        # Flag set to True if youtube-dl should show verbose output (using the
        #   --verbose option)
        self.ytdl_write_verbose_flag = False

        # During a download operation, a GObject timer runs, so that statistics
        #   in the Progress Tab can be updated at regular intervals
        # There is also a delay between the instant at which youtube-dl
        #   reports a video file has been downloaded, and the instant at which
        #   it appears in the filesystem. The timer checks for newly-existing
        #   files at regular intervals, too
        # The timer's ID (None when no timer is running)
        self.timer_id = None
        # The timer interval time (in milliseconds)
        self.timer_time = 500
        # At the end of the download operation, the timer continues running for
        #   a few seconds, to give new files a chance to appear in the
        #   filesystem. The maximum time to wait (in seconds)
        self.timer_final_time = 10
        # Once that extra time has been applied, the time (matches time.time())
        #   at which to stop waiting
        self.timer_check_time = None

        # During any operation, a flag set to True if the operation was halted
        #   by the user, rather than being allowed to complete naturally
        self.operation_halted_flag = False

        # For a channel/playlist containing hundreds (or more!) videos, a
        #   download operation will take a very long time, even though we might
        #   only want to check for new videos
        # Flag set to True if the download operation should give up checking a
        #   channel or playlist when its starts receiving details of videos
        #   about which it already knows (from a previous download operation)
        # This works well if the website sends video in order, youngest first
        #   (as YouTube does), but won't work at all otherwise
        self.operation_limit_flag = False
        # During simulated video downloads (e.g. after clicking the 'Check all'
        #   button), stop checking the channel/playlist after receiving details
        #   for this many videos, when a media.Video object exists for them
        #   and the object's .file_dir and .name IVs are set
        # Must be an positive integer or 0. If 0, no limit applies. Ignored if
        #   self.operation_limit_flag is False
        self.operation_check_limit = 3
        # During actual video downloads (e.g. after clicking the 'Download all'
        #   button), stop downloading the channel/playlist after receiving
        #   this many 'video already downloaded' messages, when a media.Video
        #   objects exists for them and the object's .dl_flag is set
        # Must be an positive integer or 0. If 0, no limit applies. Ignored if
        #   self.operation_limit_flag is False
        self.operation_download_limit = 3

        # The media data registry
        # Every media data object has a unique .dbid (which is an integer). The
        #   number of media data objects ever created (including any that have
        #   been deleted), used to give new media data objects their .dbid
        self.media_reg_count = 0
        # A dictionary containing all media data objects (but not those which
        #   have been deleted)
        # Dictionary in the form
        #   key = media data object's unique .dbid
        #   value = the media data object itself
        self.media_reg_dict = {}
        # media.Channel, media.Playlist and media.Folder objects must have
        #   unique .name IVs
        # (A channel and a playlist can't have the same name. Videos within a
        #   single channel, playlist or folder can't have the same name.
        #   Videos with different parent objects CAN have the same name)
        # A dictionary used to check that media.Channel, media.Playlist and
        #   media.Folder objects have unique .name IVs (and to look up names
        #   quickly)
        # Dictionary in the form
        #   key = media data object's .name
        #   value = media data object's unique .dbid
        self.media_name_dict = {}
        # An ordered list of media.Channel, media.Playlist and media.Folder
        #   objects which have no parents (in the order they're displayed)
        # This list, combined with each media data object's child list, is
        #   used to construct a family tree. A typical family tree looks
        #   something like this:
        #           Folder
        #               Channel
        #                   Video
        #                   Video
        #               Channel
        #                   Video
        #                   Video
        #           Folder
        #               Folder
        #                   Playlist
        #                       Video
        #                       Video
        #               Folder
        #                   Playlist
        #                       Video
        #                       Video
        #           Folder
        #               Video
        #               Video
        # In that case, the .dbid IVs for the three top-level media.Folder
        #   objects are stored in this list
        self.media_top_level_list = []
        # The maximum depth of the media registry. The diagram above shows
        #   channels on the 2nd level and playlists on the third level.
        #   Container objects cannot be added beyond the following level
        self.media_max_level = 8
        # Standard name for a media.Video object, when the actual name of the
        #   video is not yet known
        self.default_video_name = '(video with no name)'
        # The maximum length of channel, playlist and folder names (does not
        #   apply to video names)
        self.container_name_max_len = 64

        # Some media data objects are fixed (i.e. are created when Tartube
        #   first starts, and cannot be deleted by the user). Shortcuts to
        #   those objects
        # Private folder containing all videos (users cannot add anything to a
        #   private folder, because it's used by Tartube for special purposes)
        self.fixed_all_folder = None
        # Private folder containing only new videos
        self.fixed_new_folder = None
        # Private folder containing only favourite videos
        self.fixed_fav_folder = None
        # Public folder that's used as the first one in the 'Add video'
        #   dialogue window, in which the user can store any individual videos
        self.fixed_misc_folder = None
        # Public folder that's used as the second one in the 'Add video'
        #   dialogue window, in which the user can store any individual videos
        #   that are automatically deleted when Tartube shuts down
        self.fixed_temp_folder = None

        # Flag set to True if an update operation should be automatically
        #   started before the beginning of every download operation
        self.operation_auto_update_flag = False
        # When that flag is True, the following IVs are set by the initial
        #   call to self.download_manager_start(), reminding
        #   self.update_manager_finished() to start a download operation, and
        #   supplying it with the arguments from the original call to
        #   self.download_manager_start()
        self.operation_waiting_flag = False
        self.operation_waiting_sim_flag = False
        self.operation_waiting_obj = None
        # Flag set to True if files should be saved at the end of every
        #   operation
        self.operation_save_flag = True
        # Flag set to True if a dialogue window should be shown at the end of
        #   each download/update/refresh operation
        self.operation_dialogue_flag = True
        # Flag set to True if self.update_video_from_filesystem() should get
        #   the video duration, if not already known, using the moviepy.editor
        #   module (which may be slow)
        self.use_module_moviepy_flag = True

        # Flag set to True if, when checking videos/channels/playlists, we
        #   should timeout after 60 seconds (in case youtube-dl gets stuck
        #   downloading the JSON data)
        self.apply_json_timeout_flag = True
        # Flag set to True if 'Requested formats are incompatible for merge and
        #   will be merged into mkv' messages from youtube-dl should be ignored
        #   (in the Errors/Warnings tab)
        self.ignore_merge_warning_flag = True
        # Flag set to True if YouTube copyright messages should be ignored (in
        #   the Errors/Warnings tab)
        self.ignore_yt_copyright_flag = False
        # Flag set to True if 'Child process exited with non-zero code'
        #   messages should be ignored (in the Errors/Warnings tab)
        self.ignore_child_process_exit_flag = False

        # During a download operation, the number of simultaneous downloads
        #   allowed. (An instruction to youtube-dl to download video(s) from a
        #   single URL is called a download job)
        # NB Because Tartube just passes a set of instructions to youtube-dl
        #   and then waits for the results, an increase in this number is
        #   applied to a download operation immediately, but a decrease is not
        #   applied until one of the download jobs has finished
        self.num_worker_default = 2
        # (Absoute minimum and maximum values)
        self.num_worker_max = 10
        self.num_worker_min = 1
        # Flag set to True when the limit is actually applied, False when not
        self.num_worker_apply_flag = True

        # During a download operation, the bandwith limit (in KiB/s)
        # NB Because Tartube just passes a set of instructions to youtube-dl,
        #   any change in this value is not applied until one of the download
        #   jobs has finished
        self.bandwidth_default = 500
        # (Absolute minimum and maximum values)
        self.bandwidth_max = 10000
        self.bandwidth_min = 1
        # Flag set to True when the limit is currently applied, False when not
        self.bandwidth_apply_flag = False

        # The method of matching downloaded videos against existing
        #   media.Video objects:
        #       'exact_match' - The video name must match exactly
        #       'match_first' - The first n characters of the video name must
        #           match exactly
        #       'ignore_last' - All characters before the last n characters of
        #           the video name must match exactly
        self.match_method = 'exact_match'
        # Default values for self.match_first_chars and .match_ignore_chars
        self.match_default_chars = 10
        # For 'match_first', the number of characters (n) to use. Set to the
        #   default value when self.match_method is not 'match_first'; range
        #   1-999
        self.match_first_chars = self.match_default_chars
        # For 'ignore_last', the number of characters (n) to ignore. Set to the
        #   default value of when self.match_method is not 'ignore_last'; range
        #   1-999
        self.match_ignore_chars = self.match_default_chars

        # How much information to show in the Video Index. False to show
        #   minimal video stats, True to show full video stats
        self.complex_index_flag = False
        # The Video Catalogue has two 'skins', a simple view (without
        #   thumbnails) and a more complex view (with thumbnails)
        # Each skin can be set to show the name of the parent channel/playlist/
        #   folder, or not
        # The current video catalogue mode: 'simple_hide_parent',
        #   'simple_show_parent', 'complex_hide_parent', 'complex_show_parent'
        self.catalogue_mode = 'simple_hide_parent'
        # The video catalogue splits its video list into pages (as Gtk
        #   struggles with a list of hundreds, or thousands, of videos)
        # The number of videos per page, or 0 to always use a single page
        self.catalogue_page_size = 50


    def do_startup(self):

        """Gio.Application standard function."""

        if DEBUG_FUNC_FLAG:
            print('ap 469 do_startup')

        GObject.threads_init()
        Gtk.Application.do_startup(self)

        # Menu actions
        # ------------

        # 'File' column
        save_db_menu_action = Gio.SimpleAction.new('save_db_menu', None)
        save_db_menu_action.connect('activate', self.on_menu_save_db)
        self.add_action(save_db_menu_action)

        quit_menu_action = Gio.SimpleAction.new('quit_menu', None)
        quit_menu_action.connect('activate', self.on_menu_quit)
        self.add_action(quit_menu_action)

        # 'Edit' column
        system_prefs_action = Gio.SimpleAction.new('system_prefs_menu', None)
        system_prefs_action.connect(
            'activate',
            self.on_menu_system_preferences,
        )
        self.add_action(system_prefs_action)

        gen_options_action = Gio.SimpleAction.new('gen_options_menu', None)
        gen_options_action.connect('activate', self.on_menu_general_options)
        self.add_action(gen_options_action)

        # 'Media' column
        add_video_menu_action = Gio.SimpleAction.new('add_video_menu', None)
        add_video_menu_action.connect('activate', self.on_menu_add_video)
        self.add_action(add_video_menu_action)

        add_channel_menu_action = Gio.SimpleAction.new(
            'add_channel_menu',
            None,
        )
        add_channel_menu_action.connect('activate', self.on_menu_add_channel)
        self.add_action(add_channel_menu_action)

        add_playlist_menu_action = Gio.SimpleAction.new(
            'add_playlist_menu',
            None,
        )
        add_playlist_menu_action.connect(
            'activate',
            self.on_menu_add_playlist,
        )
        self.add_action(add_playlist_menu_action)

        add_folder_menu_action = Gio.SimpleAction.new('add_folder_menu', None)
        add_folder_menu_action.connect('activate', self.on_menu_add_folder)
        self.add_action(add_folder_menu_action)

        switch_view_menu_action = Gio.SimpleAction.new(
            'switch_view_menu',
            None,
        )
        switch_view_menu_action.connect('activate', self.on_button_switch_view)
        self.add_action(switch_view_menu_action)

        show_hidden_menu_action = Gio.SimpleAction.new(
            'show_hidden_menu',
            None,
        )
        show_hidden_menu_action.connect('activate', self.on_menu_show_hidden)
        self.add_action(show_hidden_menu_action)

        if self.debug_test_media_menu_flag:
            test_menu_action = Gio.SimpleAction.new('test_menu', None)
            test_menu_action.connect('activate', self.on_menu_test)
            self.add_action(test_menu_action)

        # 'Operations' column
        check_all_menu_action = Gio.SimpleAction.new('check_all_menu', None)
        check_all_menu_action.connect(
            'activate',
            self.on_menu_check_all,
        )
        self.add_action(check_all_menu_action)

        download_all_menu_action = Gio.SimpleAction.new(
            'download_all_menu',
            None,
        )
        download_all_menu_action.connect(
            'activate',
            self.on_menu_download_all,
        )
        self.add_action(download_all_menu_action)

        stop_download_menu_action = Gio.SimpleAction.new(
            'stop_download_menu',
            None,
        )
        stop_download_menu_action.connect(
            'activate',
            self.on_button_stop_operation,
        )
        self.add_action(stop_download_menu_action)

        update_menu_action = Gio.SimpleAction.new('update_ytdl_menu', None)
        update_menu_action.connect('activate', self.on_menu_update_ytdl)
        self.add_action(update_menu_action)

        refresh_db_menu_action = Gio.SimpleAction.new('refresh_db_menu', None)
        refresh_db_menu_action.connect('activate', self.on_menu_refresh_db)
        self.add_action(refresh_db_menu_action)

        # 'Help' column
        about_menu_action = Gio.SimpleAction.new('about_menu', None)
        about_menu_action.connect('activate', self.on_menu_about)
        self.add_action(about_menu_action)

        # Main toolbar actions
        # --------------------

        add_video_toolbutton_action = Gio.SimpleAction.new(
            'add_video_toolbutton',
            None,
        )
        add_video_toolbutton_action.connect(
            'activate',
            self.on_menu_add_video,
        )
        self.add_action(add_video_toolbutton_action)

        add_channel_toolbutton_action = Gio.SimpleAction.new(
            'add_channel_toolbutton',
            None,
        )
        add_channel_toolbutton_action.connect(
            'activate',
            self.on_menu_add_channel,
        )
        self.add_action(add_channel_toolbutton_action)

        add_playlist_toolbutton_action = Gio.SimpleAction.new(
            'add_playlist_toolbutton',
            None,
        )
        add_playlist_toolbutton_action.connect(
            'activate',
            self.on_menu_add_playlist,
        )
        self.add_action(add_playlist_toolbutton_action)

        add_folder_toolbutton_action = Gio.SimpleAction.new(
            'add_folder_toolbutton',
            None,
        )
        add_folder_toolbutton_action.connect(
            'activate',
            self.on_menu_add_folder,
        )
        self.add_action(add_folder_toolbutton_action)

        check_all_toolbutton_action = Gio.SimpleAction.new(
            'check_all_toolbutton',
            None,
        )
        check_all_toolbutton_action.connect(
            'activate',
            self.on_menu_check_all,
        )
        self.add_action(check_all_toolbutton_action)

        download_all_toolbutton_action = Gio.SimpleAction.new(
            'download_all_toolbutton',
            None,
        )
        download_all_toolbutton_action.connect(
            'activate',
            self.on_menu_download_all,
        )
        self.add_action(download_all_toolbutton_action)

        stop_download_button_action = Gio.SimpleAction.new(
            'stop_download_toolbutton',
            None,
        )
        stop_download_button_action.connect(
            'activate',
            self.on_button_stop_operation,
        )
        self.add_action(stop_download_button_action)

        switch_view_button_action = Gio.SimpleAction.new(
            'switch_view_toolbutton',
            None,
        )
        switch_view_button_action.connect(
            'activate',
            self.on_button_switch_view,
        )
        self.add_action(switch_view_button_action)

        if self.debug_test_media_toolbar_flag:
            test_button_action = Gio.SimpleAction.new('test_toolbutton', None)
            test_button_action.connect('activate', self.on_menu_test)
            self.add_action(test_button_action)

        quit_button_action = Gio.SimpleAction.new('quit_toolbutton', None)
        quit_button_action.connect('activate', self.on_menu_quit)
        self.add_action(quit_button_action)

        # Video catalogue toolbar actions
        # -------------------------------

        first_page_toolbutton_action = Gio.SimpleAction.new(
            'first_page_toolbutton',
            None,
        )
        first_page_toolbutton_action.connect(
            'activate',
            self.on_button_first_page,
        )
        self.add_action(first_page_toolbutton_action)

        previous_page_toolbutton_action = Gio.SimpleAction.new(
            'previous_page_toolbutton',
            None,
        )
        previous_page_toolbutton_action.connect(
            'activate',
            self.on_button_previous_page,
        )
        self.add_action(previous_page_toolbutton_action)

        next_page_toolbutton_action = Gio.SimpleAction.new(
            'next_page_toolbutton',
            None,
        )
        next_page_toolbutton_action.connect(
            'activate',
            self.on_button_next_page,
        )
        self.add_action(next_page_toolbutton_action)

        last_page_toolbutton_action = Gio.SimpleAction.new(
            'last_page_toolbutton',
            None,
        )
        last_page_toolbutton_action.connect(
            'activate',
            self.on_button_last_page,
        )
        self.add_action(last_page_toolbutton_action)

        scroll_up_toolbutton_action = Gio.SimpleAction.new(
            'scroll_up_toolbutton',
            None,
        )
        scroll_up_toolbutton_action.connect(
            'activate',
            self.on_button_scroll_up,
        )
        self.add_action(scroll_up_toolbutton_action)

        scroll_down_toolbutton_action = Gio.SimpleAction.new(
            'scroll_down_toolbutton',
            None,
        )
        scroll_down_toolbutton_action.connect(
            'activate',
            self.on_button_scroll_down,
        )
        self.add_action(scroll_down_toolbutton_action)

        # Videos Tab actions
        # ------------------

        # Buttons

        check_all_button_action = Gio.SimpleAction.new(
            'check_all_button',
            None,
        )
        check_all_button_action.connect('activate', self.on_menu_check_all)
        self.add_action(check_all_button_action)

        download_all_button_action = Gio.SimpleAction.new(
            'download_all_button',
            None,
        )
        download_all_button_action.connect(
            'activate',
            self.on_menu_download_all,
        )
        self.add_action(download_all_button_action)


    def do_activate(self):

        """Gio.Application standard function."""

        if DEBUG_FUNC_FLAG:
            print('ap 704 do_activate')

        # Only allow a single main window (raise any existing main windows)
        if not self.main_win_obj:
            self.start()

            # Open the system preferences window, if the debugging flag is set
            if self.debug_open_pref_win_flag:
                config.SystemPrefWin(self)

        else:
            self.main_win_obj.present()

            # Show a warning dialogue window, if the debugging flag is set
            if self.debug_warn_multiple_flag:

                self.dialogue_manager_obj.show_msg_dialogue(
                    utils.upper_case_first(__main__.__packagename__) \
                    + ' is already running!',
                    'warning',
                    'ok',
                )


    def do_shutdown(self):

        """Gio.Application standard function.

        Clean shutdowns (for example, from the main window's toolbar) are
        handled by self.stop().
        """

        if DEBUG_FUNC_FLAG:
            print('ap 737 do_shutdown')

        # Don't prompt the user before halting a download/update/refresh
        #   operation, as we would do in calls to self.stop()
        if self.download_manager_obj:
            self.download_manager_obj.stop_download_operation()
        elif self.update_manager_obj:
            self.update_manager_obj.stop_update_operation()
        elif self.refresh_manager_obj:
            self.refresh_manager_obj.stop_refresh_operation()

        # Stop immediately
        Gtk.Application.do_shutdown(self)


    # Public class methods


    def start(self):

        """Called by self.do_activate().

        Performs general initialisation.
        """

        if DEBUG_FUNC_FLAG:
            print('ap 763 start')

        # Import the script name (for convenience)
        script_name = utils.upper_case_first(__main__.__packagename__)

        # Create the main window
        self.main_win_obj = mainwin.MainWin(self)
        # If the debugging flag is set, move it to the top-left corner of the
        #   desktop
        if self.debug_open_top_left_flag:
            self.main_win_obj.move(0, 0)

        # Make it visible
        self.main_win_obj.show_all()

        # Start the dialogue manager (thread-safe code for Gtk message dialogue
        #   windows)
        self.dialogue_manager_obj = dialogue.DialogueManager(
            self,
            self.main_win_obj,
        )

        # Delete Tartube's config file and data directory, if the debugging
        #   flag is set
        if self.debug_delete_data_flag:
            if os.path.isfile(self.config_file_name):
                os.remove(self.config_file_name)

            if os.path.isdir(self.data_dir):
                shutil.rmtree(self.data_dir)

        # Give mainapp.TartubeApp IVs their initial values
        self.general_options_obj = options.OptionsManager()

        # Set youtube-dl IVs
        if os.name == 'nt':

            if 'PROGRAMFILES(X86)' in os.environ:
                # 64-bit MS Windows
                descrip = 'Windows 64-bit update (recommended)'
                python_path = '..\\..\\..\\mingw64\\bin\python3.exe'
                pip_path = '..\\..\\..\\mingw64\\bin\pip3-script.py'
            else:
                # 32-bit MS Windows
                descrip = 'Windows 32-bit update (recommended)'
                python_path = '..\\..\\..\\mingw32\\bin\python3.exe'
                pip_path = '..\\..\\..\\mingw32\\bin\pip3-script.py'

            self.ytdl_bin = 'youtube-dl'
            self.ytdl_path_default = 'youtube-dl'
            self.ytdl_path = 'youtube-dl'
            self.ytdl_update_dict = {
                descrip: [
                    python_path,
                    pip_path,
                    'install',
                    '--upgrade',
                    'youtube-dl',
                ],
                'Update using pip3': [
                    'pip3', 'install', '--upgrade', 'youtube-dl',
                ],
                'Update using pip': [
                    'pip', 'install', '--upgrade', 'youtube-dl',
                ],
                'Update using default youtube-dl path': [
                    self.ytdl_path_default, '-U',
                ],
                'Update using local youtube-dl path': [
                    'youtube-dl', '-U',
                ],
            }
            self.ytdl_update_list = [
                descrip,
                'Update using pip3',
                'Update using pip',
                'Update using default youtube-dl path',
                'Update using local youtube-dl path',
            ]
            self.ytdl_update_current = descrip

        else:
            self.ytdl_bin = 'youtube-dl'
            self.ytdl_path_default = os.path.abspath(
                os.path.join(os.sep, 'usr', 'bin', self.ytdl_bin),
            )
            self.ytdl_path = 'youtube-dl'
            self.ytdl_update_dict = {
                'Update using pip3 (recommended)': [
                    'pip3', 'install', '--upgrade', 'youtube-dl',
                ],
                'Update using pip': [
                    'pip', 'install', '--upgrade', 'youtube-dl',
                ],
                'Update using default youtube-dl path': [
                    self.ytdl_path_default, '-U',
                ],
                'Update using local youtube-dl path': [
                    'youtube-dl', '-U',
                ],
            }
            self.ytdl_update_list = [
                'Update using pip3 (recommended)',
                'Update using pip',
                'Update using default youtube-dl path',
                'Update using local youtube-dl path',
            ]
            self.ytdl_update_current = 'Update using pip3 (recommended)'

        # If the config file exists, load it. If not, create it
        new_mswin_flag = False
        if os.path.isfile(self.config_file_name):
            self.load_config()
        elif self.debug_no_dialogue_flag:
            self.save_config()
        else:

            # (Need to show an extra prompt at the end of this function)
            if os.name == 'nt':
                new_mswin_flag = True

            # On MS Windows, Cygwin creates a Tartube data directory at
            #   C:\msys64\home\USERNAME\tartube-data, which is not very
            #   convenient
            # Even on Linux/*BSD, the user might want to choose their own data
            #   directory
            # Therefore, on new installations, immediately ask the user to
            #   choose a location for the data directory
            dialogue_win = Gtk.MessageDialog(
                self.main_win_obj,
                0,
                Gtk.MessageType.INFO,
                Gtk.ButtonsType.OK_CANCEL,
                'Welcome to ' + script_name + '!',
            )

            if os.name == 'nt':
                folder = 'folder'
            else:
                folder = 'directory'

            dialogue_win.format_secondary_text(
                script_name + ' will download videos into a single ' + folder \
                + '. (Other\ndownloaded files, such as thumbnails, will be' \
                + ' stored in the\nsame ' + folder + '.)' \
                + '\n\nPlease create that ' + folder + ' now, or select an' \
                + ' existing ' + folder + '.' \
                + '\n\nAlternatively, click the \'Cancel\' button to use' \
                + ' this ' + folder + ':\n\n' + self.data_dir,
            )
            response = dialogue_win.run()
            dialogue_win.destroy()

            if response == Gtk.ResponseType.OK:

                file_chooser_win = Gtk.FileChooserDialog(
                    'Please select ' + script_name + '\'s data ' + folder,
                    self.main_win_obj,
                    Gtk.FileChooserAction.SELECT_FOLDER,
                    (
                        Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                        Gtk.STOCK_OPEN, Gtk.ResponseType.OK,
                    ),
                )

                response = file_chooser_win.run()
                if response == Gtk.ResponseType.OK:
                    self.data_dir = file_chooser_win.get_filename()
                    self.downloads_dir = os.path.abspath(
                        os.path.join(self.data_dir, 'downloads'),
                    )
                    self.temp_dir = os.path.abspath(
                        os.path.join(self.data_dir, '.temp'),
                    )
                    self.temp_dl_dir = os.path.abspath(
                        os.path.join(self.data_dir, '.temp', 'downloads'),
                    )

                file_chooser_win.destroy()

            # All done; create the config file, whether Tartube's data
            #   directory has been changed, or not
            self.save_config()

        # Create Tartube's data directories (if they don't already exist)
        if not os.path.isdir(self.data_dir):
            os.makedirs(self.data_dir)

        if not os.path.isdir(self.downloads_dir):
            os.makedirs(self.downloads_dir)

        # Create the temporary data directories (or empty them, if they already
        #   exist)
        if os.path.isdir(self.temp_dir):
            shutil.rmtree(self.temp_dir)

        if not os.path.isdir(self.temp_dir):
            os.makedirs(self.temp_dir)

        if not os.path.isdir(self.temp_dl_dir):
            os.makedirs(self.temp_dl_dir)

        # If the database file exists, load it. If not, create it
        db_path = os.path.abspath(
            os.path.join(self.data_dir, self.db_file_name),
        )
        if os.path.isfile(db_path):

            self.load_db()

        else:

            # New database. First create fixed media data objects (media.Folder
            #   objects) that can't be removed by the user (though they can be
            #   hidden)
            self.create_system_folders()

            # Populate the Video Index
            self.main_win_obj.video_index_populate()

            # Create the database file
            self.save_db()

        # If self.toolbar_squeeze_flag is set, after loading the config file,
        #   redraw the main toolbar without labels
        if self.toolbar_squeeze_flag:
            self.main_win_obj.redraw_main_toolbar()

        # If file load/save has been disabled, we can now show a dialogue
        #   window
        if self.disable_load_save_flag:
            self.file_error_dialogue(
                'Because of an error,\nfile load/save has been\ndisabled',
            )

        # For new installations, MS Windows must be prompted to perform an
        #   update operation, which installs youtube-dl on their system
        elif new_mswin_flag:

            self.dialogue_manager_obj.show_msg_dialogue(
                'youtube-dl must be installed before you\ncan use ' \
                + utils.upper_case_first(__main__.__packagename__) \
                + '. Do you want to install\nyoutube-dl now?',
                'question',
                'yes-no',
                None,                   # Parent window is main window
                {
                    'yes': 'update_manager_start',
                },
            )


    def stop(self):

        """Called by self.on_menu_quit().

        Before terminating the Tartube app, gets confirmation from the user (if
        a download/update/refresh operation is in progress).

        If no operation is in progress, calls self.stop_continue() to terminate
        the app now. Otherwise, self.stop_continue() is only called when the
        clicks the dialogue window's 'Yes' button.
        """

        if DEBUG_FUNC_FLAG:
            print('ap 900 stop')

        # If a download/update/refresh operation is in progress, get
        #   confirmation before stopping
        if self.current_manager_obj:

            if self.download_manager_obj:
                string = 'a download'
            elif self.update_manager_obj:
                string = 'an update'
            else:
                string = 'a refresh'

            # If the user clicks 'yes', call self.stop_continue() to complete
            #   the shutdown
            self.dialogue_manager_obj.show_msg_dialogue(
                'There is ' + string + ' operation in progress.\n' \
                + 'Are you sure you want to quit ' \
                + utils.upper_case_first(__main__.__packagename__) + '?',
                'question',
                'yes-no',
                None,                   # Parent window is main window
                {
                    'yes': 'stop_continue',
                }
            )

        # No confirmation required, so call self.stop_continue() now
        else:
            self.stop_continue()


    def stop_continue(self):

        """Called by self.stop() or by dialogue.MessageDialogue.on_clicked().

        Terminates the Tartube app. Forced shutdowns (for example, by clicking
        the X in the top corner of the window) are handled by
        self.do_shutdown().
        """

        if DEBUG_FUNC_FLAG:
            print('ap 941 stop_continue')

        if self.download_manager_obj:
            self.download_manager_obj.stop_download_operation()

        elif self.update_manager_obj:
            self.update_manager_obj.stop_update_operation()

        elif self.refresh_manager_obj:
            self.refresh_manager_obj.stop_refresh_operation()

        # Empty any temporary folders from the database
        self.delete_temp_folders()
        # Delete Tartube's temporary folder from the filesystem
        if os.path.isdir(self.temp_dir):
            shutil.rmtree(self.temp_dir)

        # Save the config and database files for the final time
        self.save_config()
        self.save_db()

        # I'm outta here!
        self.quit()


    def system_error(self, error_code, msg):

        """Can be called by anything.

        Wrapper function for mainwin.MainWin.errors_list_add_system_error().

        Args:

            code (int): An error code in the range 100-999

            msg (str): A system error message to display in the main window's
                Errors List.

        Notes:

            Error codes are currently assigned thus:

            100-199: mainapp.py     (in use: 101-125)
            200-299: mainwin.py     (in use: 201-234)
            300-399: downloads.py   (in use: 301-304)
            400-499: config.py      (in use: 401-404)

        """

        if DEBUG_FUNC_FLAG:
            print('ap 991 system_error')

        if self.main_win_obj:
            self.main_win_obj.errors_list_add_system_error(error_code, msg)
        else:
            # Emergency fallback: display in the terminal window
            print('SYSTEM ERROR ' + str(error_code) + ': ' + msg)


    # (Config/database files load/save)


    def load_config(self):

        """Called by self.start() (only).

        Loads the Tartube config file. If loading fails, disables all file
        loading/saving.
        """

        if DEBUG_FUNC_FLAG:
            print('ap 1012 load_config')

        # Sanity check
        if self.current_manager_obj \
        or not os.path.isfile(self.config_file_name) \
        or self.disable_load_save_flag:
            return

        # Try to load the config file
        try:
            with open(self.config_file_name) as infile:
                json_dict = json.load(infile)

        except:
            # Loading failed. Prevent damage to backup files by disabling file
            #   load/save for the rest of this session
            self.disable_load_save()
            # The call to self.file_error_dialogue() writes to the terminal if
            #   the main window doesn't exist (which it shouldn't)
            return self.file_error_dialogue(
                'Failed to load the ' \
                + utils.upper_case_first(__main__.__packagename__) \
                + ' config file',
            )

        # Do some basic checks on the loaded data
        if not json_dict \
        or not 'script_name' in json_dict \
        or not 'script_version' in json_dict \
        or not 'save_date' in json_dict \
        or not 'save_time' in json_dict \
        or json_dict['script_name'] != __main__.__packagename__:

            self.disable_load_save()
            return self.file_error_dialogue(
                'The ' + utils.upper_case_first(__main__.__packagename__) \
                + ' config file is invalid',
            )

        # Convert a version, e.g. 1.234.567, into a simple number, e.g.
        #   1234567, that can be compared with other versions
        version = self.convert_version(json_dict['script_version'])
        # Now check that the config file wasn't written by a more recent
        #   version of Tartube (which this older version might not be able to
        #   read)
        if version is None \
        or version > self.convert_version(__main__.__version__):
            self.disable_load_save()
            return self.file_error_dialogue(
                'Config file can\'t be read\nby this version of ' \
                + utils.upper_case_first(__main__.__packagename__),
            )

        # Set IVs to their new values
        if version >= 5024:  # v0.5.024
            self.toolbar_squeeze_flag = json_dict['toolbar_squeeze_flag']

        self.data_dir = json_dict['data_dir']
        self.downloads_dir = os.path.abspath(
            os.path.join(self.data_dir, 'downloads'),
        )
        self.temp_dir = os.path.abspath(os.path.join(self.data_dir, '.temp'))
        self.temp_dl_dir = os.path.abspath(
            os.path.join(self.data_dir, '.temp', 'downloads'),
        )

        if version >= 3014:  # v0.3.014
            self.db_backup_mode = json_dict['db_backup_mode']

        # (In version v0.5.027, the value of these IVs were overhauled. If
        #   loading from an earlier config file, replace those values with the
        #   new default values)
        if version >= 5027:
            self.ytdl_bin = json_dict['ytdl_bin']
            self.ytdl_path_default = json_dict['ytdl_path_default']
            self.ytdl_path = json_dict['ytdl_path']
            self.ytdl_update_dict = json_dict['ytdl_update_dict']
            self.ytdl_update_list = json_dict['ytdl_update_list']
            self.ytdl_update_current = json_dict['ytdl_update_current']

        self.ytdl_write_stdout_flag = json_dict['ytdl_write_stdout_flag']
        if version >= 5004:  # v0.5.004
            self.ytdl_write_ignore_json_flag \
            = json_dict['ytdl_write_ignore_json_flag']
        self.ytdl_write_stderr_flag = json_dict['ytdl_write_stderr_flag']
        self.ytdl_write_verbose_flag = json_dict['ytdl_write_verbose_flag']

        if version >= 3029:  # v0.3.029
            self.operation_limit_flag = json_dict['operation_limit_flag']
            self.operation_check_limit = json_dict['operation_check_limit']
            self.operation_download_limit \
            = json_dict['operation_download_limit']

        self.operation_auto_update_flag \
        = json_dict['operation_auto_update_flag']
        self.operation_save_flag = json_dict['operation_save_flag']
        self.operation_dialogue_flag = json_dict['operation_dialogue_flag']
        self.use_module_moviepy_flag = json_dict['use_module_moviepy_flag']
#       # Removed v0.5.003
#        self.use_module_validators_flag \
#        = json_dict['use_module_validators_flag']

        if version >= 5004:  # v0.5.004
            self.apply_json_timeout_flag \
            = json_dict['apply_json_timeout_flag']
        if version >= 1027:  # v0.1.028
            self.ignore_merge_warning_flag \
            = json_dict['ignore_merge_warning_flag']
        if version >= 5004:  # v0.5.004
            self.ignore_yt_copyright_flag \
            = json_dict['ignore_yt_copyright_flag']
            self.ignore_child_process_exit_flag \
            = json_dict['ignore_child_process_exit_flag']

        self.num_worker_default = json_dict['num_worker_default']
        self.num_worker_apply_flag = json_dict['num_worker_apply_flag']

        self.bandwidth_default = json_dict['bandwidth_default']
        self.bandwidth_apply_flag = json_dict['bandwidth_apply_flag']

        self.match_method = json_dict['match_method']
        self.match_first_chars = json_dict['match_first_chars']
        self.match_ignore_chars = json_dict['match_ignore_chars']

        self.complex_index_flag = json_dict['complex_index_flag']
        if version >= 3019:  # v0.3.019
            self.catalogue_mode = json_dict['catalogue_mode']
        if version >= 3023:  # v0.3.023
            self.catalogue_page_size = json_dict['catalogue_page_size']


    def save_config(self):

        """Called by self.start(), .stop(), switch_db(),
        .download_manager_finished(), .update_manager_finished and
        .refresh_manager_finished().

        Saves the Tartube config file. If saving fails, disables all file
        loading/saving.
        """

        if DEBUG_FUNC_FLAG:
            print('ap 1117 save_config')

        # Sanity check
        if self.current_manager_obj or self.disable_load_save_flag:
            return

        # Prepare values
        utc = datetime.datetime.utcfromtimestamp(time.time())

        # Prepare a dictionary of data to save as a JSON file
        json_dict = {
            # Metadata
            'script_name': __main__.__packagename__,
            'script_version': __main__.__version__,
            'save_date': str(utc.strftime('%d %b %Y')),
            'save_time': str(utc.strftime('%H:%M:%S')),
            # Data
            'toolbar_squeeze_flag': self.toolbar_squeeze_flag,

            'data_dir': self.data_dir,

            'db_backup_mode': self.db_backup_mode,

            'ytdl_bin': self.ytdl_bin,
            'ytdl_path_default': self.ytdl_path_default,
            'ytdl_path': self.ytdl_path,
            'ytdl_update_dict': self.ytdl_update_dict,
            'ytdl_update_list': self.ytdl_update_list,
            'ytdl_update_current': self.ytdl_update_current,

            'ytdl_write_stdout_flag': self.ytdl_write_stdout_flag,
            'ytdl_write_ignore_json_flag': self.ytdl_write_ignore_json_flag,
            'ytdl_write_stderr_flag': self.ytdl_write_stderr_flag,
            'ytdl_write_verbose_flag': self.ytdl_write_verbose_flag,

            'operation_limit_flag': self.operation_limit_flag,
            'operation_check_limit': self.operation_check_limit,
            'operation_download_limit': self.operation_download_limit,

            'operation_auto_update_flag': self.operation_auto_update_flag,
            'operation_save_flag': self.operation_save_flag,
            'operation_dialogue_flag': self.operation_dialogue_flag,
            'use_module_moviepy_flag': self.use_module_moviepy_flag,

            'apply_json_timeout_flag': self.apply_json_timeout_flag,
            'ignore_merge_warning_flag': self.ignore_merge_warning_flag,
            'ignore_yt_copyright_flag': self.ignore_yt_copyright_flag,
            'ignore_child_process_exit_flag': \
            self.ignore_child_process_exit_flag,

            'num_worker_default': self.num_worker_default,
            'num_worker_apply_flag': self.num_worker_apply_flag,

            'bandwidth_default': self.bandwidth_default,
            'bandwidth_apply_flag': self.bandwidth_apply_flag,

            'match_method': self.match_method,
            'match_first_chars': self.match_first_chars,
            'match_ignore_chars': self.match_ignore_chars,

            'complex_index_flag': self.complex_index_flag,
            'catalogue_mode': self.catalogue_mode,
            'catalogue_page_size': self.catalogue_page_size,
        }

        # Try to save the file
        try:
            with open(self.config_file_name, 'w') as outfile:
                json.dump(json_dict, outfile, indent=4)

        except:
            self.disable_load_save()
            return self.file_error_dialogue(
                'Failed to save the ' \
                + utils.upper_case_first(__main__.__packagename__) \
                + ' config file',
            )


    def load_db(self):

        """Called by self.start() and .switch_db().

        Loads the Tartube database file. If loading fails, disables all file
        loading/saving.

        Returns:

            True on success, False on failure

        """

        if DEBUG_FUNC_FLAG:
            print('ap 1190 load_db')

        # Sanity check
        path = os.path.abspath(os.path.join(self.data_dir, self.db_file_name))
        if self.current_manager_obj \
        or not os.path.isfile(path) \
        or self.disable_load_save_flag:
            return False

        # Reset main window tabs now so the user can't manipulate their widgets
        #   during the load
        if self.main_win_obj:
            self.main_win_obj.video_index_reset()
            self.main_win_obj.video_catalogue_reset()
            self.main_win_obj.progress_list_reset()
            self.main_win_obj.results_list_reset()
            self.main_win_obj.errors_list_reset()

        # Try to load the database file
        try:
            f = open(path, 'rb')
            load_dict = pickle.load(f)
            f.close()

        except:
            self.disable_load_save()
            self.file_error_dialogue(
                'Failed to load the ' \
                + utils.upper_case_first(__main__.__packagename__) \
                + ' database file',
            )

            return False

        # Do some basic checks on the loaded data
        if not load_dict \
        or not 'script_name' in load_dict \
        or not 'script_version' in load_dict \
        or not 'save_date' in load_dict \
        or not 'save_time' in load_dict \
        or load_dict['script_name'] != __main__.__packagename__:
            self.file_error_dialogue(
                'The ' + utils.upper_case_first(__main__.__packagename__) \
                + ' database file is invalid',
            )

            return False

        # Convert a version, e.g. 1.234.567, into a simple number, e.g.
        #   1234567, that can be compared with other versions
        version = self.convert_version(load_dict['script_version'])
        # Now check that the database file wasn't written by a more recent
        #   version of Tartube (which this older version might not be able to
        #   read)
        if version is None \
        or version > self.convert_version(__main__.__version__):
            self.disable_load_save()
            self.file_error_dialogue(
                'Database file can\'t be read\nby this version of ' \
                + utils.upper_case_first(__main__.__packagename__),
            )

            return False

        # Set IVs to their new values
        self.general_options_obj = load_dict['general_options_obj']
        self.media_reg_count = load_dict['media_reg_count']
        self.media_reg_dict = load_dict['media_reg_dict']
        self.media_name_dict = load_dict['media_name_dict']
        self.media_top_level_list = load_dict['media_top_level_list']
        self.fixed_all_folder = load_dict['fixed_all_folder']
        self.fixed_new_folder = load_dict['fixed_new_folder']
        self.fixed_fav_folder = load_dict['fixed_fav_folder']
        self.fixed_misc_folder = load_dict['fixed_misc_folder']
        self.fixed_temp_folder = load_dict['fixed_temp_folder']

        # Empty any temporary folders
        self.delete_temp_folders()

        # Update the loaded data for this version of Tartube
        self.update_db(version)

        # If the debugging flag is set, hide all fixed (system) folders
        if self.debug_hide_folders_flag:
            self.fixed_all_folder.set_hidden_flag(True)
            self.fixed_fav_folder.set_hidden_flag(True)
            self.fixed_new_folder.set_hidden_flag(True)
            self.fixed_temp_folder.set_hidden_flag(True)
            self.fixed_misc_folder.set_hidden_flag(True)

        # Repopulate the Video Index, showing the new data
        if self.main_win_obj:
            self.main_win_obj.video_index_populate()

        return True


    def update_db(self, version):

        """Called by self.load_db().

        When the Tartube database created by a previous version of Tartube is
        loaded, update IVs as required.

        Args:

            version (int): The version of Tartube that created the database,
                already converted to a simple integer by self.convert_version()

        """

        if DEBUG_FUNC_FLAG:
            print('ap 1191 update_db')

        fixed_folder_list = [
            self.fixed_all_folder,
            self.fixed_new_folder,
            self.fixed_fav_folder,
        ]

        if version < 3012:  # v0.3.012

            # This version fixed some problems, in which the deletion of media
            #   data objects was not handled correctly
            # Repair the media data registry, as required
            for folder_obj in fixed_folder_list:

                # Check that videos in 'All Videos', 'New Videos' and
                #   'Favourite Videos' still exist in the media data registry
                copy_list = folder_obj.child_list.copy()
                for child_obj in copy_list:
                    if isinstance(child_obj, media.Video) \
                    and not child_obj.parent_obj.dbid in self.media_reg_dict:
                        folder_obj.del_child(child_obj)

                # Video counts in 'All Videos', 'New Videos' and 'Favourite
                #   Videos' might be wrong
                vid_count = new_count = fav_count = dl_count = 0

                for child_obj in folder_obj.child_list:
                    if isinstance(child_obj, media.Video):
                        vid_count += 1

                        if child_obj.new_flag:
                            new_count += 1

                        if child_obj.fav_flag:
                            fav_count += 1

                        if child_obj.dl_flag:
                            dl_count += 1

                folder_obj.reset_counts(
                    vid_count,
                    new_count,
                    fav_count,
                    dl_count,
                )

        if version < 4003:  # v0.4.002

            # This version fixes video format options, which were stored
            #   incorrectly in options.OptionsManager
            key_list = [
                'video_format',
                'second_video_format',
                'third_video_format',
            ]

            options_obj_list = [self.general_options_obj]
            for media_data_obj in self.media_reg_dict.values():
                if media_data_obj.options_obj is not None:
                    options_obj_list.append(media_data_obj.options_obj)

            for options_obj in options_obj_list:
                for key in key_list:

                    val = options_obj.options_dict[key]
                    if val != '0':

                        if val in formats.VIDEO_OPTION_DICT:
                            # Invert the key-value pair used before v0.4.002
                            options_obj.options_dict[key] \
                            = formats.VIDEO_OPTION_DICT[val]

                        else:
                            # Completely invalid format description, so
                            #   just reset it
                            options_obj.options_dict[key] = '0'

        if version < 4004:  # v0.4.004

            # This version fixes a bug in which moving a channel, playlist or
            #   folder to a new location in the media data registry's tree
            #   failed to update all the videos that moved with it
            # To be safe, update every video in the registry
            for media_data_obj in self.media_reg_dict.values():
                if isinstance(media_data_obj, media.Video):
                    media_data_obj.reset_file_dir(self)

        if version < 4015:  # v0.4.015

            # This version fixes issues with sorting videos. Channels,
            #   playlists and folders in a loaded database might not be sorted
            #   correctly, so just sort them all using the new algorithms
            container_list = [
                self.fixed_all_folder,
                self.fixed_new_folder,
                self.fixed_fav_folder,
                self.fixed_misc_folder,
                self.fixed_temp_folder,
            ]

            for dbid in self.media_name_dict.values():
                container_list.append(self.media_reg_dict[dbid])

            for container_obj in container_list:
                container_obj.sort_children()

        if version < 4022:  # v0.4.022

            # This version fixes a rare issue in which media.Video.index was
            #   set to a string, rather than int, value
            # Update all existing videos
            for media_data_obj in self.media_reg_dict.values():
                if isinstance(media_data_obj, media.Video) \
                and media_data_obj.index is not None:
                    media_data_obj.index = int(media_data_obj.index)


    def save_db(self):

        """Called by self.start(), .stop(), .switch_db(),
        .download_manager_finished(), .update_manager_finished(),
        .refresh_manager_finished() and .on_menu_save_db().

        Saves the Tartube database file. If saving fails, disables all file
        loading/saving.
        """

        if DEBUG_FUNC_FLAG:
            print('ap 1279 save_db')

        # Sanity check
        if self.current_manager_obj or self.disable_load_save_flag:
            return

        # Prepare values
        utc = datetime.datetime.utcfromtimestamp(time.time())
        path = os.path.abspath(os.path.join(self.data_dir, self.db_file_name))
        bu_path = os.path.abspath(os.path.join(self.data_dir, 'tartube_BU.db'))
        temp_bu_path = os.path.abspath(
            os.path.join(self.data_dir, 'tartube_TEMP_BU.db'),
        )

        # Prepare a dictionary of data to save, using Python pickle
        save_dict = {
            # Metadata
            'script_name': __main__.__packagename__,
            'script_version': __main__.__version__,
            'save_date': str(utc.strftime('%d %b %Y')),
            'save_time': str(utc.strftime('%H:%M:%S')),
            # Data
            'general_options_obj' : self.general_options_obj,
            'media_reg_count': self.media_reg_count,
            'media_reg_dict': self.media_reg_dict,
            'media_name_dict': self.media_name_dict,
            'media_top_level_list': self.media_top_level_list,
            'fixed_all_folder': self.fixed_all_folder,
            'fixed_new_folder': self.fixed_new_folder,
            'fixed_fav_folder': self.fixed_fav_folder,
            'fixed_misc_folder': self.fixed_misc_folder,
            'fixed_temp_folder': self.fixed_temp_folder,
        }

        # Back up any existing file
        if os.path.isfile(path):
            try:
                shutil.copyfile(path, temp_bu_path)

            except:
                self.disable_load_save()
                return self.file_error_dialogue(
                    'Failed to save the ' \
                    + utils.upper_case_first(__main__.__packagename__) \
                    + ' database file (could not make a backup copy of' \
                    + ' the existing file)',
                )

        # Try to save the file
        try:
            f = open(path, 'wb')
            pickle.dump(save_dict, f)
            f.close()

        except:

            self.disable_load_save()

            if os.path.isfile(temp_bu_path):
                return self.file_error_dialogue(
                    'Failed to save the ' \
                    + utils.upper_case_first(__main__.__packagename__) \
                    + ' database file\n\n' \
                    + 'A backup of the previous file can be found at:\n' \
                    + '   ' + temp_bu_path,
                )

            else:
                return self.file_error_dialogue(
                    'Failed to save the ' \
                    + utils.upper_case_first(__main__.__packagename__) \
                    + ' database file',
                )

        # In the event that there was no database file to backup, then the
        #   following code isn't necessary
        if os.path.isfile(temp_bu_path):

            # Make the backup file permanent, or not, depending on settings
            if self.db_backup_mode == 'default':
                os.remove(temp_bu_path)

            elif self.db_backup_mode == 'single':
                # (On MSWin, can't do os.rename if the destination file already
                #   exists)
                if os.path.isfile(bu_path):
                    os.remove(bu_path)

                os.rename(temp_bu_path, bu_path)

            elif self.db_backup_mode == 'daily':

                daily_bu_path = os.path.abspath(
                    os.path.join(
                        self.data_dir,
                        'tartube_BU_' + str(utc.strftime('%Y_%m_%d')) + '.db',
                    ),
                )

                # Only make a new backup file once per day
                if not os.path.isfile(daily_bu_path):

                    if os.path.isfile(daily_bu_path):
                        os.remove(daily_bu_path)

                    os.rename(temp_bu_path, daily_bu_path)
                else:

                    os.remove(temp_bu_path)

            elif self.db_backup_mode == 'always':

                always_bu_path = os.path.abspath(
                    os.path.join(
                        self.data_dir,
                        'tartube_BU_' \
                        + str(utc.strftime('%Y_%m_%d_%H_%M_%S')) + '.db',
                    ),
                )

                if os.path.isfile(always_bu_path):
                    os.remove(always_bu_path)

                os.rename(temp_bu_path, always_bu_path)


    def switch_db(self, data_list):

        """Called by config.SystemPrefWin.on_data_dir_button_clicked().

        When the user select a new location for a data directory, first save
        our existing database.

        Then load the database at the new location, if exists, or create a new
        database there, if not.

        Args:

            data_list (list): A list containing two items: the full file path
                to the location of the new data directory, and the system
                preferences window (config.SystemPrefWin) that the user has
                open

        Returns:

            True on success, False on failure

        """

        if DEBUG_FUNC_FLAG:
            print('ap 1363 switch_db')

        # Extract values from the argument list
        path = data_list.pop(0)
        pref_win_obj = data_list.pop(0)

        # Sanity check
        if self.current_manager_obj or self.disable_load_save_flag:
            return False

        # If the old path is the same as the new one, we don't need to do
        #   anything
        if path == self.data_dir:
            return False

        # Save the existing database
        self.save_db()

        # Delete Tartube's temporary folder from the filesystem
        if os.path.isdir(self.temp_dir):
            shutil.rmtree(self.temp_dir)

        # Update IVs...
        self.data_dir = path
        self.downloads_dir = os.path.abspath(os.path.join(path, 'downloads'))
        self.temp_dir = os.path.abspath(os.path.join(path, '.temp'))
        self.temp_dl_dir = os.path.abspath(
            os.path.join(path, '.temp', 'downloads'),
        )
        # ...then save the config file to preserve them
        self.save_config()

        # Any of those directories that don't exist should be created
        if not os.path.isdir(self.data_dir):
            os.makedirs(self.data_dir)

        if not os.path.isdir(self.downloads_dir):
            os.makedirs(self.downloads_dir)

        if not os.path.isdir(self.temp_dir):
            os.makedirs(self.temp_dir)

        if not os.path.isdir(self.temp_dl_dir):
            os.makedirs(self.temp_dl_dir)

        # If the database file itself exists; load it. If not, create it
        db_path = os.path.abspath(
            os.path.join(self.data_dir, self.db_file_name),
        )
        if not os.path.isfile(db_path):

            # Reset main window widgets
            self.main_win_obj.video_index_reset()
            self.main_win_obj.video_catalogue_reset()
            self.main_win_obj.progress_list_reset()
            self.main_win_obj.results_list_reset()
            self.main_win_obj.errors_list_reset()

            # Reset database IVs
            self.reset_db()

            # Create a new database file
            self.save_db()

            # Repopulate the Video Index, showing the new data
            self.main_win_obj.video_index_populate()

            # If the system preferences window is open, reset it to show the
            #   new data directory
            if pref_win_obj and pref_win_obj.is_visible():
                pref_win_obj.reset_window()

                self.dialogue_manager_obj.show_msg_dialogue(
                    'Database file created',
                    'info',
                    'ok',
                    pref_win_obj,
                )

            else:

                # (Parent window is the main window)
                self.dialogue_manager_obj.show_msg_dialogue(
                    'Database file created',
                    'info',
                    'ok',
                )

            return True

        else:
            return self.load_db()


    def reset_db(self):

        """Called by self.switch_db().

        Resets media registry IVs, so that a new Tartube database file can be
        created.
        """

        if DEBUG_FUNC_FLAG:
            print('ap 1435 reset_db')

        # Reset IVs to their default states
        self.general_options_obj = options.OptionsManager()
        self.media_reg_count = 0
        self.media_reg_dict = {}
        self.media_name_dict = {}
        self.media_top_level_list = []
        self.fixed_all_folder = None
        self.fixed_new_folder = None
        self.fixed_fav_folder = None
        self.fixed_misc_folder = None
        self.fixed_temp_folder = None

        # Create new system folders (which sets the values of
        #   self.fixed_all_folder, etc)
        self.create_system_folders()


    def create_system_folders(self):

        """Called by self.start() and .reset_db().

        Creates the fixed (system) media.Folder objects that can't be
        destroyed by the user.
        """

        if DEBUG_FUNC_FLAG:
            print('ap 1463 create_system_folders')

        self.fixed_all_folder = self.add_folder(
            'All Videos',
            None,           # No parent folder
            True,           # Fixed (folder cannot be removed)
            True,           # Private
            True,           # Can only contain videos
            False,          # Not temporary
        )

        self.fixed_fav_folder = self.add_folder(
            'Favourite Videos',
            None,           # No parent folder
            True,           # Fixed (folder cannot be removed)
            True,           # Private
            True,           # Can only contain videos
            False,          # Not temporary
        )
        self.fixed_fav_folder.set_fav_flag(True)

        self.fixed_new_folder = self.add_folder(
            'New Videos',
            None,           # No parent folder
            True,           # Fixed (folder cannot be removed)
            True,           # Private
            True,           # Can only contain videos
            False,          # Not temporary
        )

        self.fixed_temp_folder = self.add_folder(
            'Temporary Videos',
            None,           # No parent folder
            True,           # Fixed (folder cannot be removed)
            False,          # Public
            False,          # Can contain any media data object
            True,           # Temporary
        )

        self.fixed_misc_folder = self.add_folder(
            'Unsorted Videos',
            None,           # No parent folder
            True,           # Fixed (folder cannot be removed)
            False,          # Public
            True,           # Can only contain videos
            False,          # Not temporary
        )


    def disable_load_save(self):

        """Called by self.load_config(), .save_config(), load_db() and
        .save_db().

        After an error, disables loading/saving, and desensitises the main
        window's menu item.
        """

        if DEBUG_FUNC_FLAG:
            print('ap 1522 disable_load_save')

        self.disable_load_save_flag = True
        if self.main_win_obj is not None:
            self.main_win_obj.save_db_menu_item.set_sensitive(False)


    def file_error_dialogue(self, msg):

        """Called by self.load_config(), .save_config(), load_db() and
        .save_db().

        After a failure to load/save a file, display a dialogue window if the
        main window is open, or write to the terminal if not.

        Args:

            msg (string): The message to display

        """

        if DEBUG_FUNC_FLAG:
            print('1544 file_error_dialogue')

        if self.main_win_obj and self.dialogue_manager_obj:
            self.dialogue_manager_obj.show_msg_dialogue(msg, 'error', 'ok')

        else:
            # Main window not open yet, so remove any newline characters
            #   (which look weird when printed to the terminal)
            msg = re.sub(
                r'\n',
                ' ',
                msg,
            )

            print('FILE ERROR: ' + msg)


    def delete_temp_folders(self):

        """Called by self.load_db() and self.stop().

        Deletes the contents of any folders marked temporary, such as the
        'Temporary Videos' folder. (The folders themselves are not deleted).
        """

        if DEBUG_FUNC_FLAG:
            print('ap 1570 delete_temp_folders')

        for name in self.media_name_dict:

            dbid = self.media_name_dict[name]
            media_data_obj = self.media_reg_dict[dbid]

            if isinstance(media_data_obj, media.Folder) \
            and media_data_obj.temp_flag:

                # Delete all child objects
                for child_obj in media_data_obj.child_list:
                    if isinstance(child_obj, media.Video):
                        self.delete_video(child_obj)
                    else:
                        self.delete_container(child_obj)

                # Remove files from the filesystem, leaving an empty directory
                dir_path = media_data_obj.get_dir(self)
                if os.path.isdir(dir_path):
                    shutil.rmtree(dir_path)

                os.makedirs(dir_path)


    def convert_version(self, version):

        """Can be called by anything, but mostly called by self.load_config()
        and load_db().

        Converts a Tartube version number, a string in the form '1.234.567',
        into a simple integer in the form 1234567.

        The calling function can then compare the version number for this
        installation of Tartube with the version number that created the file.

        Args:

            version (string): A string in the form '1.234.567'

        Returns:

            The simple integer, or None if the 'version' argument was invalid

        """

        if DEBUG_FUNC_FLAG:
            print('ap 1615 convert_version')

        num_list = version.split('.')
        if len(num_list) != 3:
            return None
        else:
            return (int(num_list[0]) * 1000000) + (int(num_list[1]) * 1000) \
            + int(num_list[2])


    # (Download/Update/Refresh operations)


    def download_manager_start(self, force_sim_flag=False, \
    media_data_obj=None):

        """Caled by self.update_manager_finished() and by callbacks in
        self.on_menu_check_all() and .on_menu_download_all().

        Also called by callbacks in mainwin.MainWin.on_video_index_download(),
        .on_video_index_check(), on_video_catalogue_check(),
        .on_video_catalogue_download() and .on_video_catalogue_re_download().

        When the user clicks the 'Check all' or 'Download all' buttons (or
        their equivalents in the main window's menu or toolbar), initiate a
        download operation.

        Creates a new downloads.DownloadManager object to handle the download
        operation. When the operation is complete,
        self.download_manager_finished() is called.

        Args:

            force_sim_flag (True/False): True if playlists/channels should
                just be checked for new videos, without downloading anything.
                False if videos should be downloaded (or not) depending on
                each media data object's .dl_sim_flag IV

            media_data_obj (media.Video, media.Channel, media.Playlist,
                media.Folder): The media data object to download. If set, that
                object and any media data objects it contains are downloaded.
                If none, all media data objects are downloaded

        """

        if DEBUG_FUNC_FLAG:
            print('ap 1661 download_manager_start')

        if self.current_manager_obj:
            # Download, update or refresh operation already in progress
            return self.system_error(
                101,
                'Download, update or refresh operation already in progress',
            )

        elif self.main_win_obj.config_win_list:
            # Download operation is not allowed when a configuration window is
            #   open
            self.dialogue_manager_obj.show_msg_dialogue(
                'A download operation cannot start\nif one or more' \
                + ' configuration\nwindows are still open',
                'error',
                'ok',
            )

            return

        # If the flag is set, do an update operation before starting the
        #   download operation
        if self.operation_auto_update_flag and not self.operation_waiting_flag:
            self.update_manager_start()
            # These IVs tells self.update_manager_finished to start a download
            #   operation
            self.operation_waiting_flag = True
            self.operation_waiting_sim_flag = force_sim_flag
            self.operation_waiting_obj = media_data_obj
            return

        # The media data registry consists of a collection of media data
        #   objects (media.Video, media.Channel, media.Playlist and
        #   media.Folder)
        # If media_data_obj was specified by the calling function, that media
        #   data object and all of its children are assigned a
        #   downloads.DownloadItem object
        # Otherwise, all media data objects are assigned a
        #   downloads.DownloadItem object
        # Those downloads.DownloadItem objects are collectively stored in a
        #   downloads.DownloadList object
        download_list_obj = downloads.DownloadList(self, media_data_obj)
        if not download_list_obj.download_item_list:

            if force_sim_flag:
                msg = 'There is nothing to check!'
            else:
                msg = 'There is nothing to download!'

            self.dialogue_manager_obj.show_msg_dialogue(msg, 'error', 'ok')
            return

        # During a download operation, show a progress bar in the Videos Tab
        self.main_win_obj.show_progress_bar(force_sim_flag)
        # Reset the Progress List
        self.main_win_obj.progress_list_reset()
        # Reset the Results List
        self.main_win_obj.results_list_reset()
        # Initialise the Progress List with one row for each media data object
        #   in the downloads.DownloadList object
        self.main_win_obj.progress_list_init(download_list_obj)
        # (De)sensitise other widgets, as appropriate
        self.main_win_obj.sensitise_operation_widgets(False)
        # Make the widget changes visible
        self.main_win_obj.show_all()

        # During a download operation, a GObject timer runs, so that statistics
        #   in the Progress Tab can be updated at regular intervals
        # There is also a delay between the instant at which youtube-dl
        #   reports a video file has been downloaded, and the instant at which
        #   it appears in the filesystem. The timer checks for newly-existing
        #   files at regular intervals, too
        # Create the timer
        self.timer_id = GObject.timeout_add(
            self.timer_time,
            self.timer_callback,
        )

        # Initiate the download operation. Any code can check whether a
        #   download, update or refresh operation is in progress, or not, by
        #   checking this IV
        self.current_manager_obj = downloads.DownloadManager(
            self,
            force_sim_flag,
            download_list_obj,
        )
        self.download_manager_obj = self.current_manager_obj


    def download_manager_halt_timer(self):

        """Called by downloads.DownloadManager.run() when that function has
        finished.

        During a download operation, a GObject timer was running. Let it
        continue running for a few seconds more.
        """

        if DEBUG_FUNC_FLAG:
            print('ap 1761 download_manager_halt_timer')

        if self.timer_id:
            self.timer_check_time = time.time() + self.timer_final_time


    def download_manager_finished(self):

        """Called by self.timer_callback() and downloads.DownloadManager.run().

        The download operation has finished, so update IVs and main window
        widgets.
        """

        if DEBUG_FUNC_FLAG:
            print('ap 1776 download_manager_finished')

        # Get the time taken by the download operation, so we can convert it
        #   into a nice string below (e.g. '05:15')
        time_num = int(
            self.download_manager_obj.stop_time \
            - self.download_manager_obj.start_time
        )

        # Any code can check whether a download/update/refresh operation is in
        #   progress, or not, by checking this IV
        self.current_manager_obj = None
        self.download_manager_obj = None

        # Stop the timer and reset IVs
        GObject.source_remove(self.timer_id)
        self.timer_id = None
        self.timer_check_time = None

        # After a download operation, remove the progress bar in the Videos Tab
        self.main_win_obj.hide_progress_bar()
        # (De)sensitise other widgets, as appropriate
        self.main_win_obj.sensitise_operation_widgets(True)
        # Make the widget changes visible
        self.main_win_obj.show_all()

        # After a download operation, save files, if allowed
        if self.operation_save_flag:
            self.save_config()
            self.save_db()

        # Then show a dialogue window, if allowed
        if self.operation_dialogue_flag:

            if not self.operation_halted_flag:
                msg = 'Download operation complete'
            else:
                msg = 'Download operation halted'

            if time_num >= 10:
                msg += '\n\nTime taken: ' \
                + utils.convert_seconds_to_string(time_num, True)

            self.dialogue_manager_obj.show_msg_dialogue(msg, 'info', 'ok')

        # Reset operation IVs
        self.operation_halted_flag = False


    def update_manager_start(self):

        """Called by self.download_manager_start() and by a callback in
        self.on_menu_update_ytdl().

        Initiates an update operation to update the system's youtube-dl.

        Creates a new updates.UpdateManager object to handle the update
        operation. When the operation is complete,
        self.update_manager_finished() is called.
        """

        if DEBUG_FUNC_FLAG:
            print('ap 1838 update_manager_start')

        if self.current_manager_obj:
            # Download, update or refresh operation already in progress
            return self.system_error(
                102,
                'Download, update or refresh operation already in progress',
            )

        elif self.main_win_obj.config_win_list:
            # Update operation is not allowed when a configuration window is
            #   open
            self.dialogue_manager_obj.show_msg_dialogue(
                'An update operation cannot start\nif one or more' \
                + ' configuration\nwindows are still open',
                'error',
                'ok',
            )

            return

        # During an update operation, certain widgets are modified and/or
        #   desensitised
        self.main_win_obj.modify_widgets_in_update_operation(False)

        # Initiate the update operation. Any code can check whether a
        #   download, update or refresh operation is in progress, or not, by
        #   checking this IV
        self.current_manager_obj = updates.UpdateManager(self)
        self.update_manager_obj = self.current_manager_obj


    def update_manager_finished(self, success_flag=True, ytdl_version=None):

        """Called by updates.UpdateManager.run().

        The update operation has finished, so update IVs and main window
        widgets.

        Args:

            success_flag (True or False): True if the update operation
                succeeded, False if not

            ytdl_version (string): Set if the update manager was able to
                capture the new youtube-dl version number, or None if not

        """

        if DEBUG_FUNC_FLAG:
            print('ap 1885 update_manager_finished')

        # Any code can check whether a download/update/refresh operation is in
        #   progress, or not, by checking this IV
        self.current_manager_obj = None
        self.update_manager_obj = None

        # During an update operation, certain widgets are modified and/or
        #   desensitised; restore them to their original state
        self.main_win_obj.modify_widgets_in_update_operation(True)

        # After an update operation, save files, if allowed
        if self.operation_save_flag:
            self.save_config()
            self.save_db()

        # Then show a dialogue window, if allowed (and if a download operation
        #   is not waiting to start)
        if self.operation_dialogue_flag and not self.operation_waiting_flag:

            if not success_flag:
                msg = 'Update operation failed'
            elif self.operation_halted_flag:
                msg = 'Update operation halted'
            else:
                msg = 'Update operation complete'
                if ytdl_version is not None:
                    msg += '\n\nyoutube-dl version: ' + ytdl_version
                else:
                    msg += '\n\nyoutube-dl version: (unknown)'

            self.dialogue_manager_obj.show_msg_dialogue(msg, 'info', 'ok')

        # Reset operation IVs
        self.operation_halted_flag = False

        # If a download operation is waiting to start, start it
        if self.operation_waiting_flag:
            self.download_manager_start(
                self.operation_waiting_sim_flag,
                self.operation_waiting_obj,
            )

            # Reset those IVs, ready for any future download operations
            self.operation_waiting_flag = False
            self.operation_waiting_sim_flag = False
            self.operation_waiting_obj = None


    def refresh_manager_start(self, media_data_obj=None):

        """Called by a callback in self.on_menu_refresh_db() and by a
        callback in mainwin.MainWin.on_video_index_refresh().

        Initiates a refresh operation to compare Tartube's data directory with
        the media registry, updating the registry as appropriate.

        Creates a new refresh.RefreshManager object to handle the refresh
        operation. When the operation is complete,
        self.refresh_manager_finished() is called.

        Args:

            media_data_obj (media.Channel, media.Playlist, media.Folder or
                None): If specified, only this channel/playlist/folder is
                refreshed. If not specified, the entire media registry is
                refreshed

        """

        if DEBUG_FUNC_FLAG:
            print('ap 1952 refresh_manager_start')

        if self.current_manager_obj:
            # Download, update or refresh operation already in progress
            return self.system_error(
                103,
                'Download, update or refresh operation already in progress',
            )

        elif media_data_obj is not None \
        and isinstance(media_data_obj, media.Video):
            return self.system_error(
                104,
                'Refresh operation cannot be applied to an individual video',
            )

        elif self.main_win_obj.config_win_list:
            # Refresh operation is not allowed when a configuration window is
            #   open
            self.dialogue_manager_obj.show_msg_dialogue(
                'A refresh operation cannot start\nif one or more' \
                + ' configuration\nwindows are still open',
                'error',
                'ok',
            )

            return

        # During a refresh operation, certain widgets are modified and/or
        #   desensitised
        self.main_win_obj.modify_widgets_in_refresh_operation(False)

        # Initiate the refresh operation. Any code can check whether a
        #   download, update or refresh operation is in progress, or not, by
        #   checking this IV
        self.current_manager_obj = refresh.RefreshManager(self, media_data_obj)
        self.refresh_manager_obj = self.current_manager_obj

        self.refresh_manager_obj.run()


    def refresh_manager_finished(self):

        """Called by refresh.RefreshManager.run().

        The refresh operation has finished, so update IVs and main window
        widgets.
        """

        if DEBUG_FUNC_FLAG:
            print('ap 2002 refresh_manager_finished')

        # Any code can check whether a download/update/refresh operation is in
        #   progress, or not, by checking this IV
        self.current_manager_obj = None
        self.refresh_manager_obj = None

        # During a refresh operation, certain widgets are modified and/or
        #   desensitised; restore them to their original state
        self.main_win_obj.modify_widgets_in_refresh_operation(True)

        # After a refresh operation, save files, if allowed
        if self.operation_save_flag:
            self.save_config()
            self.save_db()

        # Then show a dialogue window, if allowed
        if self.operation_dialogue_flag:

            if not self.operation_halted_flag:
                msg = 'Refresh operation complete'
            else:
                msg = 'Refresh operation halted'

            self.dialogue_manager_obj.show_msg_dialogue(msg, 'info', 'ok')

        # Reset operation IVs
        self.operation_halted_flag = False


    # (Download operation support functions)


    def create_video_from_download(self, download_item_obj, dir_path, \
    filename, extension, no_sort_flag=False):

        """Called downloads.VideoDownloader.confirm_new_video() and
        .confirm_sim_video().

        When an individual video has been downloaded, this function is called
        to create a new media.Video object.

        Args:

            download_item_obj (downloads.DownloadItem) - The object used to
                track the download status of a media data object (media.Video,
                media.Channel or media.Playlist)

            dir_path (string): The full path to the directory in which the
                video is saved, e.g. '/home/yourname/tartube/downloads/Videos'

            filename (string): The video's filename, e.g. 'My Video'

            extension (string): The video's extension, e.g. '.mp4'

            no_sort_flag (True or False): True when called by
                downloads.VideoDownloader.confirm_sim_video(), because the
                video's parent containers (including the 'All Videos' folder)
                should delay sorting their lists of child objects until that
                calling function is ready. False when called by anything else

        Returns:

            video_obj (media.Video) - The video object created

        """

        if DEBUG_FUNC_FLAG:
            print('ap 2064 create_video_from_download')

        # The downloads.DownloadItem handles a download for a video, a channel
        #   or a playlist
        media_data_obj = download_item_obj.media_data_obj
        video_obj = None

        if isinstance(media_data_obj, media.Video):

            # The downloads.DownloadItem object is handling a single video
            video_obj = media_data_obj
            # If the video was added manually (for example, using the 'Add
            #   videos' button), then its filepath won't be set yet
            if not video_obj.file_dir:
                video_obj.set_file(dir_path, filename, extension)

        else:

            # The downloads.DownloadItem object is handling a channel or
            #   playlist
            # Does a media.Video object already exist?
            for child_obj in media_data_obj.child_list:

                if isinstance(child_obj, media.Video) \
                and child_obj.file_dir and child_obj.file_dir == dir_path \
                and child_obj.file_name and child_obj.file_name == filename:
                    video_obj = child_obj

            if video_obj is None:

                # Create a new media data object for the video
                video_obj = self.add_video(media_data_obj, None, no_sort_flag)

                # Since we have them to hand, set the video's file path IVs
                #   immediately
                video_obj.set_file(dir_path, filename, extension)

        # If the video is in a channel or a playlist, assume that youtube-dl is
        #   supplying a list of videos in the order of upload, newest first -
        #   in which case, now is a good time to set the video's .receive_time
        #   IV
        # (If not, the IV is set by media.Video.set_dl_flag when the video is
        #   actually downloaded)
        if isinstance(video_obj.parent_obj, media.Channel) \
        or isinstance(video_obj.parent_obj, media.Playlist):
            video_obj.set_receive_time()

        return video_obj


    def announce_video_download(self, download_item_obj, video_obj, \
    keep_description=None, keep_info=None, keep_thumbnail=None):

        """Called downloads.VideoDownloader.confirm_new_video(),
        .confirm_old_video() and .confirm_sim_video().

        Updates the main window.

        Args:

            download_item_obj (downloads.DownloadItem): The download item
                object describing the URL from which youtube-dl should download
                video(s).

            video_obj (media.Video): The video object for the downloaded video

            keep_description (True, False, None):
            keep_info (True, False, None):
            keep_thumbnail (True, False, None):
                Settings from the options.OptionsManager object used to
                    download the video (set to 'None' for a simulated download)

        """

        if DEBUG_FUNC_FLAG:
            print('ap 2138 announce_video_download')

        # If the video's parent media data object (a channel, playlist or
        #   folder) is selected in the Video Index, update the Video Catalogue
        #   for the downloaded video
        self.main_win_obj.video_catalogue_update_row(video_obj)

        # Update the Results List
        self.main_win_obj.results_list_add_row(
            download_item_obj,
            video_obj,
            keep_description,
            keep_info,
            keep_thumbnail,
        )


    def update_video_when_file_found(self, video_obj, video_path, temp_dict, \
    mkv_flag=False):

        """Called by mainwin.MainWin.results_list_update_row().

        When youtube-dl reports it is finished, there is a short delay before
        the final downloaded video(s) actually exist in the filesystem.

        Once the calling function has confirmed the file exists, it calls this
        function to update the media.Video object's IVs.

        Args:

            video_obj (media.Video): The video object to update

            video_path (string): The full filepath to the video file that has
                been confirmed to exist

            temp_dict (dict): Dictionary of values used to update the video
                object, in the form:

                'video_obj': not required by this function, as we already have
                    it
                'row_num': not required by this function
                'keep_description', 'keep_info', 'keep_thumbnail': flags from
                    the options.OptionsManager object used for to download the
                    video (not added to the dictionary at all for simulated
                    downloads)

            mkv_flag (True or False): If the warning 'Requested formats are
                incompatible for merge and will be merged into mkv' has been
                seen, the calling function has found an .mkv file rather than
                the .mp4 file it was expecting, and has set this flag to True

        """

        if DEBUG_FUNC_FLAG:
            print('ap 2192 update_video_when_file_found')

        # Only set the .name IV if the video is currently unnamed
        if video_obj.name == self.default_video_name:
            video_obj.set_name(video_obj.file_name)

        # If it's an .mkv file because of a failed merge, update the IV
        if mkv_flag:
            video_obj.set_mkv()

        # Set the file size
        video_obj.set_file_size(os.path.getsize(video_path))

        # If the JSON file was downloaded, we can extract video statistics from
        #   it
        self.update_video_from_json(video_obj)

        # For any of those statistics that haven't been set (because the JSON
        #   file was missing or didn't contain the right statistics), set them
        #   directly
        self.update_video_from_filesystem(video_obj, video_path)

        # Delete the description, JSON and thumbnail files, if required to do
        #   so
        if 'keep_description' in temp_dict \
        and not temp_dict['keep_description']:

            old_path = os.path.abspath(
                os.path.join(
                    video_obj.file_dir,
                    video_obj.file_name + '.description',
                ),
            )

            if os.path.isfile(old_path):
                utils.convert_path_to_temp(
                    self,
                    old_path,
                    True,               # Move the file
                )

        if 'keep_info' in temp_dict and not temp_dict['keep_info']:

            old_path = os.path.abspath(
                os.path.join(
                    video_obj.file_dir,
                    video_obj.file_name + '.info.json',
                ),
            )

            if os.path.isfile(old_path):
                utils.convert_path_to_temp(
                    self,
                    old_path,
                    True,               # Move the file
                )

        if 'keep_thumbnail' in temp_dict and not temp_dict['keep_thumbnail']:

            old_path = utils.find_thumbnail(self, video_obj)
            if old_path is not None:
                utils.convert_path_to_temp(
                    self,
                    old_path,
                    True,               # Move the file
                )


        # Mark the video as (fully) downloaded (and update everything else)
        self.mark_video_downloaded(video_obj, True)


    def update_video_from_json(self, video_obj):

        """Called by self.update_video_when_file_found() and
        refresh.RefreshManager.refresh_from_filesystem().

        If a video's JSON file exists, extract video statistics from it, and
        use them to update the video object.

        Args:

            video_obj (media.Video): The video object to update

        """

        if DEBUG_FUNC_FLAG:
            print('ap 2275 update_video_from_json')

        json_path = os.path.abspath(
            os.path.join(
                video_obj.file_dir,
                video_obj.file_name + '.info.json',
            ),
        )

        if os.path.isfile(json_path):

            json_dict = self.file_manager_obj.load_json(json_path)

            if 'upload_date' in json_dict:
                # date_string in form YYYYMMDD
                date_string = json_dict['upload_date']
                dt_obj = datetime.datetime.strptime(date_string, '%Y%m%d')
                video_obj.set_upload_time(dt_obj.timestamp())

            if 'duration' in json_dict:
                video_obj.set_duration(json_dict['duration'])

            if 'webpage_url' in json_dict:
                video_obj.set_source(json_dict['webpage_url'])

            if 'description' in json_dict:
                video_obj.set_video_descrip(
                    json_dict['description'],
                    self.main_win_obj.descrip_line_max_len,
                )


    def update_video_from_filesystem(self, video_obj, video_path):

        """Called by self.update_video_when_file_found() and
        refresh.RefreshManager.refresh_from_filesystem().

        If a video's JSON file does not exist, or did not contain the
        statistics we were looking for, we can set some of them directly from
        the filesystem.

        Args:

            video_obj (media.Video): The video object to update

            video_path (string): The full path to the video's file

        """

        if DEBUG_FUNC_FLAG:
            print('ap 2323 update_video_from_filesystem')

        if video_obj.upload_time is None:
            video_obj.set_upload_time(os.path.getmtime(video_path))

        if video_obj.duration is None \
        and HAVE_MOVIEPY_FLAG \
        and self.use_module_moviepy_flag:
            clip = moviepy.editor.VideoFileClip(video_path)
            video_obj.set_duration(clip.duration)

        # (Can't set the video source directly)

        if video_obj.descrip is None:
            video_obj.read_video_descrip(
                self,
                self.main_win_obj.descrip_line_max_len,
            )


    # (Add media data objects)


    def add_video(self, parent_obj, source=None, no_sort_flag=False):

        """Can be called by anything. Mostly called by
        self.create_video_from_download() and self.on_menu_add_video().

        Creates a new media.Video object, and updates IVs.

        Args:

            parent_obj (media.Channel, media.Playlist or media.Folder): The
                media data object for which the new media.Video object is the
                child (all videos have a parent)

            source (string): The video's source URL, if known

            no_sort_flag (True or False): True when
                self.create_video_from_download() is called by
                downloads.VideoDownloader.confirm_sim_video(), because the
                video's parent containers (including the 'All Videos' folder)
                should delay sorting their lists of child objects until that
                calling function is ready. False when called by anything else

        Returns:

            The new media.Video object

        """

        if DEBUG_FUNC_FLAG:
            print('ap 2369 add_video')

        # Videos can't be placed inside other videos
        if parent_obj and isinstance(parent_obj, media.Video):
            return self.system_error(
                105,
                'Videos cannot be placed inside other videos',
            )

        # Videos can't be added directly to a private folder
        elif parent_obj and isinstance(parent_obj, media.Folder) \
        and parent_obj.priv_flag:
            return self.system_error(
                106,
                'Videos cannot be placed inside a private folder',
            )

        # Create a new media.Video object
        video_obj = media.Video(
            self.media_reg_count,
            self.default_video_name,
            parent_obj,
            None,                   # Use default download options
            no_sort_flag,
        )

        if source is not None:
            video_obj.set_source(source)

        # Update IVs
        self.media_reg_count += 1
        self.media_reg_dict[video_obj.dbid] = video_obj

        # The private 'All Videos' folder also has this video as a child object
        self.fixed_all_folder.add_child(video_obj, no_sort_flag)

        # Update the row in the Video Index for both the parent and private
        #   folder
        self.main_win_obj.video_index_update_row_text(video_obj.parent_obj)
        self.main_win_obj.video_index_update_row_text(self.fixed_all_folder)

        return video_obj


    def add_channel(self, name, parent_obj=None, source=None, \
    dl_sim_flag=None):

        """Can be called by anything. Mostly called by
        mainwin.MainWin.on_menu_add_channel().

        Creates a new media.Channel object, and updates IVs.

        Args:

            name (string): The channel name

            parent_obj (media.Folder): The media data object for which the new
                media.Channel object is a child (if any)

            source (string): The channel's source URL, if known

            dl_sim_flag (True, False): True if we should simulate downloads for
                videos in this channel, False if we should actually download
                them (when allowed)

        Returns:

            The new media.Channel object

        """

        if DEBUG_FUNC_FLAG:
            print('ap 2440 add_channel')

        # Channels can only be placed inside an unrestricted media.Folder
        #   object (if they have a parent at all)
        if parent_obj \
        and (
            not isinstance(parent_obj, media.Folder) \
            or parent_obj.restrict_flag
        ):
            return self.system_error(
                107,
                'Channels cannot be added to a restricted folder',
            )

        # There is a limit to the number of levels allowed in the media
        #   registry
        if parent_obj and parent_obj.get_depth() >= self.media_max_level:
            return self.system_error(
                108,
                'Channel exceeds maximum depth of media registry',
            )

        # Create a new media.Channel object
        channel_obj = media.Channel(
            self,
            self.media_reg_count,
            name,
            parent_obj,
            None,                   # Use default download options
        )

        if source is not None:
            channel_obj.set_source(source)

        if dl_sim_flag is not None:
            channel_obj.set_dl_sim_flag(dl_sim_flag)

        # Update IVs
        self.media_reg_count += 1
        self.media_reg_dict[channel_obj.dbid] = channel_obj
        self.media_name_dict[channel_obj.name] = channel_obj.dbid
        if not parent_obj:
            self.media_top_level_list.append(channel_obj.dbid)

        # Create the directory used by this channel (if it doesn't already
        #   exist)
        dir_path = channel_obj.get_dir(self)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        return channel_obj


    def add_playlist(self, name, parent_obj=None, source=None, \
    dl_sim_flag=None):

        """Can be called by anything. Mostly called by
        mainwin.MainWin.on_menu_add_playlist().

        Creates a new media.Playlist object, and updates IVs.

        Args:

            name (string): The playlist name

            parent_obj (media.Folder): The media data object for which the new
                media.Playlist object is a child (if any)

            source (string): The playlist's source URL, if known

            dl_sim_flag (True, False): True if we should simulate downloads for
                videos in this playlist, False if we should actually download
                them (when allowed)

        Returns:

            The new media.Playlist object

        """

        if DEBUG_FUNC_FLAG:
            print('ap 2521 add_playlist')

        # Playlists can only be place inside an unrestricted media.Folder
        #   object (if they have a parent at all)
        if parent_obj \
        and (
            not isinstance(parent_obj, media.Folder) \
            or parent_obj.restrict_flag
        ):
            return self.system_error(
                109,
                'Playlists cannot be added to a restricted folder',
            )

        # There is a limit to the number of levels allowed in the media
        #   registry
        if parent_obj and parent_obj.get_depth() >= self.media_max_level:
            return self.system_error(
                110,
                'Playlist exceeds maximum depth of media registry',
            )

        # Create a new media.Playlist object
        playlist_obj = media.Playlist(
            self,
            self.media_reg_count,
            name,
            parent_obj,
            None,                   # Use default download options
        )

        if source is not None:
            playlist_obj.set_source(source)

        if dl_sim_flag is not None:
            playlist_obj.set_dl_sim_flag(dl_sim_flag)

        # Update IVs
        self.media_reg_count += 1
        self.media_reg_dict[playlist_obj.dbid] = playlist_obj
        self.media_name_dict[playlist_obj.name] = playlist_obj.dbid
        if not parent_obj:
            self.media_top_level_list.append(playlist_obj.dbid)

        # Create the directory used by this playlist (if it doesn't already
        #   exist)
        dir_path = playlist_obj.get_dir(self)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        # Procedure complete
        return playlist_obj


    def add_folder(self, name, parent_obj=None, fixed_flag=False, \
    priv_flag=False, restrict_flag=False, temp_flag=False):

        """Can be called by anything. Mostly called by
        mainwin.MainWin.on_menu_add_folder().

        Creates a new media.Folder object, and updates IVs.

        Args:

            name (string): The folder name

            parent_obj (media.Folder): The media data object for which the new
                media.Channel object is a child (if any)

            fixed_flag, priv_flag, restrict_flag, temp_flag (True, False):
                flags sent to the object's .__init__() function

        Returns:

            The new media.Folder object

        """

        if DEBUG_FUNC_FLAG:
            print('ap 2600 add_folder')

        # Folders can only be placed inside an unrestricted media.Folder object
        #   (if they have a parent at all)
        if parent_obj \
        and (
            not isinstance(parent_obj, media.Folder) \
            or parent_obj.restrict_flag
        ):
            return self.system_error(
                111,
                'Folders cannot be added to another restricted folder',
            )

        # There is a limit to the number of levels allowed in the media
        #   registry
        if parent_obj and parent_obj.get_depth() >= self.media_max_level:
            return self.system_error(
                112,
                'Folder exceeds maximum depth of media registry',
            )

        folder_obj = media.Folder(
            self,
            self.media_reg_count,
            name,
            parent_obj,
            None,                   # Use default download options
            fixed_flag,
            priv_flag,
            restrict_flag,
            temp_flag,
        )

        # Update IVs
        self.media_reg_count += 1
        self.media_reg_dict[folder_obj.dbid] = folder_obj
        self.media_name_dict[folder_obj.name] = folder_obj.dbid
        if not parent_obj:
            self.media_top_level_list.append(folder_obj.dbid)

        # Create the directory used by this folder (if it doesn't already
        #   exist)
        # Obviously don't do that for private folders
        dir_path = folder_obj.get_dir(self)
        if not folder_obj.priv_flag and not os.path.exists(dir_path):
            os.makedirs(dir_path)

        # Procedure complete
        return folder_obj


    # (Move media data objects)


    def move_container_to_top(self, media_data_obj):

        """Called by mainwin.MainWin.on_video_index_move_to_top().

        Before moving a channel, playlist or folder, get confirmation from the
        user.

        After getting confirmation, call self.move_container_to_top_continue()
        to move the channel, playlist or folder to the top level (in other
        words, removes its parent folder).

        Args:

            media_data_obj (media.Channel, media.Playlist, media.Folder): The
                moving media data object

        """

        if DEBUG_FUNC_FLAG:
            print('ap 2674 move_container_to_top')

        # Do some basic checks
        if media_data_obj is None or isinstance(media_data_obj, media.Video) \
        or self.current_manager_obj or not media_data_obj.parent_obj:
            return self.system_error(
                113,
                'Move container to top request failed sanity check',
            )

        # Prompt the user for confirmation
        if isinstance(media_data_obj, media.Channel):
            source_type = 'channel'
        elif isinstance(media_data_obj, media.Playlist):
            source_type = 'playlist'
        else:
            source_type = 'folder'

        # If the user clicks 'yes', call self.move_container_to_top_continue()
        #   to complete the move
        self.dialogue_manager_obj.show_msg_dialogue(
            'Are you sure you want to move this ' + source_type + ':\n' \
            + '   ' + media_data_obj.name + '\n\n' \
            + 'This procedure will move all downloaded files\n' \
            + 'to the top level of ' \
            + utils.upper_case_first(__main__.__packagename__) \
            + '\'s data directory',
            'question',
            'yes-no',
            None,                   # Parent window is main window
            # Arguments passed directly to .move_container_to_top_continue()
            {
                'yes': 'move_container_to_top_continue',
                'data': media_data_obj,
            },
        )


    def move_container_to_top_continue(self, media_data_obj):

        """Called by dialogue.MessageDialogue.on_clicked().

        Moves a channel, playlist or folder to the top level (in other words,
        removes its parent folder).
        """

        # Move the sub-directories to their new location
        shutil.move(media_data_obj.get_dir(self), self.downloads_dir)

        # Update IVs
        media_data_obj.parent_obj.del_child(media_data_obj)
        media_data_obj.set_parent_obj(None)
        self.media_top_level_list.append(media_data_obj.dbid)

        # All videos which are descendents of media_data_obj must have their
        #   .file_dir IV updated to the new location
        for video_obj in media_data_obj.compile_all_videos( [] ):
            video_obj.reset_file_dir(self)

        # Save the database (because, if the user terminates Tartube and then
        #   restarts it, then tries to perform a download operation, a load of
        #   Python error messages will be generated, complaining that
        #   directories don't exist)
        self.save_db()

        # Remove the moving object from the Video Index, and put it back there
        #   at its new location
        self.main_win_obj.video_index_delete_row(media_data_obj)
        self.main_win_obj.video_index_add_row(media_data_obj)

        # Select the moving object, which redraws the Video Catalogue
        # !!! TODO BUG: This doesn't work because the .select_iter() call
        #   generates an error
        self.main_win_obj.video_index_select_row(media_data_obj)


    def move_container(self, source_obj, dest_obj):

        """Called by mainwin.MainWin.on_video_index_drag_data_received().

        Before moving a channel, playlist or folder, get confirmation from the
        user.

        After getting confirmation, call self.move_container_continue() to move
        the channel, playlist or folder into another folder.

        Args:

            source_obj (media.Channel, media.Playlist, media.Folder): The
                moving media data object

            dest_obj ( media.Folder): The destination folder

        """

        if DEBUG_FUNC_FLAG:
            print('ap 2758 move_container')

        # Do some basic checks
        if source_obj is None or isinstance(source_obj, media.Video) \
        or dest_obj is None or isinstance(dest_obj, media.Video) \
        or source_obj == dest_obj:
            return self.system_error(
                114,
                'Move container request failed sanity check',
            )

        # Ignore Video Index drag-and-drop during an download/update/refresh
        #   operation
        elif self.current_manager_obj:
            return

        elif not isinstance(dest_obj, media.Folder):

            self.dialogue_manager_obj.show_msg_dialogue(
                'Channels, playlists and folders can\nonly be dragged into' \
                + ' a folder',
                'error',
                'ok',
            )

            return

        elif isinstance(source_obj, media.Folder) and source_obj.fixed_flag:

            self.dialogue_manager_obj.show_msg_dialogue(
                'The fixed folder \'' + dest_obj.name \
                + '\'\ncannot be moved (but it can still\nbe hidden)',
                'error',
                'ok',
            )

            return

        elif dest_obj.restrict_flag:

            self.dialogue_manager_obj.show_msg_dialogue(
                'The folder \'' + dest_obj.name \
                + '\'\ncan only contain videos',
                'error',
                'ok',
            )

            return

        # Prompt the user for confirmation
        if isinstance(source_obj, media.Channel):
            source_type = 'channel'
        elif isinstance(source_obj, media.Playlist):
            source_type = 'playlist'
        else:
            source_type = 'folder'

        if not dest_obj.temp_flag:
            temp_string = ''
        else:
            temp_string = '\n\nWARNING: The destination folder is marked\n' \
            + 'as temporary, so everything inside it will be\nDELETED when ' \
            + utils.upper_case_first(__main__.__packagename__) + ' ' \
            + 'shuts down!'

        # If the user clicks 'yes', call self.move_container_continue() to
        #   complete the move
        self.dialogue_manager_obj.show_msg_dialogue(
            'Are you sure you want to move this ' + source_type + ':\n' \
            + '   ' + source_obj.name + '\n' \
            + 'into this folder:\n' \
            + '   ' + dest_obj.name + '\n\n' \
            + 'This procedure will move all downloaded files\n' \
            + 'to the new location' \
            + temp_string,
            'question',
            'yes-no',
            None,                   # Parent window is main window
            # Arguments passed directly to .move_container_continue()
            {
                'yes': 'move_container_continue',
                'data': [source_obj, dest_obj],
            },
        )


    def move_container_continue(self, media_list):

        """Called by dialogue.MessageDialogue.on_clicked().

        Moves a channel, playlist or folder into another folder.
        """

        source_obj = media_list[0]
        dest_obj = media_list[1]

        # Move the sub-directories to their new location
        shutil.move(source_obj.get_dir(self), dest_obj.get_dir(self))

        # Update both media data objects' IVs
        if source_obj.parent_obj:
            source_obj.parent_obj.del_child(source_obj)

        dest_obj.add_child(source_obj)
        source_obj.set_parent_obj(dest_obj)

        if source_obj.dbid in self.media_top_level_list:
            index = self.media_top_level_list.index(source_obj.dbid)
            del self.media_top_level_list[index]

        # All videos which are descendents of dest_obj must have their
        #   .file_dir IV updated to the new location
        for video_obj in source_obj.compile_all_videos( [] ):
            video_obj.reset_file_dir(self)

        # Save the database (because, if the user terminates Tartube and then
        #   restarts it, then tries to perform a download operation, a load of
        #   Python error messages will be generated, complaining that
        #   directories don't exist)
        self.save_db()

        # Remove the moving object from the Video Index, and put it back there
        #   at its new location
        self.main_win_obj.video_index_delete_row(source_obj)
        self.main_win_obj.video_index_add_row(source_obj)
        # Select the moving object, which redraws the Video Catalogue
        # !!! TODO BUG: This doesn't work because the .select_iter() call
        #   generates an error
        self.main_win_obj.video_index_select_row(source_obj)


    # (Delete media data objects)


    def delete_video(self, video_obj, no_update_index_flag=False):

        """Called by self.delete_temp_folders(), .delete_container(),
        mainwin.MainWin.video_catalogue_popup_menu() and a callback in
        mainwin.MainWin.on_video_catalogue_delete_video().

        Deletes a video object from the media registry.

        Args:

            video_obj (media.Video): The media.Video object to delete

            no_update_index_flag (True or False): True when called by
                self.delete_container(), in which case the Video Index is not
                updated (because the calling function wants to do that)

        """

        if DEBUG_FUNC_FLAG:
            print('ap 2899 delete_video')

        if not isinstance(video_obj, media.Video):
            return self.system_error(
                115,
                'Delete video request failed sanity check',
            )

        # Remove the video from its parent object
        video_obj.parent_obj.del_child(video_obj)

        # Remove the corresponding entry in private folder's child lists
        update_list = [video_obj.parent_obj]
        if self.fixed_all_folder.del_child(video_obj):
            update_list.append(self.fixed_all_folder)

        if self.fixed_new_folder.del_child(video_obj):
            update_list.append(self.fixed_new_folder)

        if self.fixed_fav_folder.del_child(video_obj):
            update_list.append(self.fixed_fav_folder)

        # Remove the video from our IVs
        del self.media_reg_dict[video_obj.dbid]

        # (If emptying a temporary folder on startup, the main window won't be
        #   visible yet)
        if self.main_win_obj:
            # Remove the video from the catalogue, if present
            self.main_win_obj.video_catalogue_delete_row(video_obj)

            # Update rows in the Video Index
            if not no_update_index_flag:
                for container_obj in update_list:
                    self.main_win_obj.video_index_update_row_text(
                        container_obj,
                    )


    def delete_container(self, media_data_obj):

        """Can be called by anything.

        Before deleting a channel, playlist or folder object from the media
        data registry, get confirmation from the user.

        The process is split across three functions.

        This functions obtains confirmation from the user. If deleting files,
        a second confirmation is required, and self.delete_container_continue()
        is called in response.

        In either case, self.delete_container_complete() is then called to
        update the media data registry.

        Args:

            media_data_obj (media.Channel, media.Playlist, media.Folder):
                The container media data object

        """

        if DEBUG_FUNC_FLAG:
            print('ap 2962 delete_container')

        # Check this isn't a video or a fixed folder (which cannot be removed)
        if isinstance(media_data_obj, media.Video) \
        or (
            isinstance(media_data_obj, media.Folder)
            and media_data_obj.fixed_flag
        ):
            return self.system_error(
                116,
                'Delete container request failed sanity check',
            )

        # Prompt the user for confirmation, even if the container object has no
        #   children
        # (Even though there are no children, we can't guarantee that the
        #   sub-directories in Tartube's data directory are empty)
        dialogue_win = mainwin.DeleteContainerDialogue(
            self.main_win_obj,
            media_data_obj,
        )

        response = dialogue_win.run()

        # Retrieve user choices from the dialogue window...
        if dialogue_win.button2.get_active():
            delete_file_flag = True
        else:
            delete_file_flag = False

        # ...before destroying it
        dialogue_win.destroy()

        if response != Gtk.ResponseType.OK:
            return

        # Get a second confirmation, if required to delete files
        if delete_file_flag:

            self.dialogue_manager_obj.show_msg_dialogue(
                'Are you SURE you want to delete files?\nThis procedure' \
                ' cannot be reversed!',
                'question',
                'yes-no',
                None,                   # Parent window is main window
                # Arguments passed directly to .delete_container_continue()
                {
                    'yes': 'delete_container_continue',
                    'data': media_data_obj,
                }
            )

        # No second confirmation required, so we can proceed directly to the
        #   call to self.delete_container_complete()
        else:
            self.delete_container_complete(media_data_obj)


    def delete_container_continue(self, media_data_obj):

        """Called by dialogue.MessageDialogue.on_clicked().

        When deleting a container, after the user has specified that files
        should be deleted too, this function is called to delete those files.

        Args:

            media_data_obj (media.Channel, media.Playlist, media.Folder):
                The container media data object

        """

        if DEBUG_FUNC_FLAG:
            print('ap 3034 delete_container_continue')

        # Confirmation obtained, so delete the files
        container_dir = media_data_obj.get_dir(self)
        if os.path.isdir(container_dir):
            shutil.rmtree(container_dir)

        # Now call self.delete_container_complete() to handle the media data
        #   registry
        self.delete_container_complete(media_data_obj)


    def delete_container_complete(self, media_data_obj, recursive_flag=False):

        """Called by self.delete_container(), .delete_container_continue()
        and then recursively by this function.

        Deletes a channel, playlist or folder object from the media data
        registry.

        This function calls itself recursively to delete all of the container
        object's descendants.

        Args:

            media_data_obj (media.Channel, media.Playlist, media.Folder):
                The container media data object

            recursive_flag (True, False): Set to False on the initial call to
                this function from some other part of the code, and True when
                this function calls itself recursively

        """

        if DEBUG_FUNC_FLAG:
            print('ap 3068 delete_container_complete')

        # Confirmation has been obtained, and any files have been deleted (if
        #   required), so now deal with the media data registry

        # Recursively remove all of the container object's children. The code
        #   doesn't work as intended, unless we make a copy of the list of
        #   child objects first
        copy_list = media_data_obj.child_list.copy()
        for child_obj in copy_list:
            if isinstance(child_obj, media.Video):
                self.delete_video(child_obj, True)
            else:
                self.delete_container_complete(child_obj, True)

        # Remove the container object from its own parent object (if it has
        #   one)
        if media_data_obj.parent_obj:
            media_data_obj.parent_obj.del_child(media_data_obj)

        # Remove the media data object from our IVs
        del self.media_reg_dict[media_data_obj.dbid]
        del self.media_name_dict[media_data_obj.name]
        if media_data_obj.dbid in self.media_top_level_list:
            index = self.media_top_level_list.index(media_data_obj.dbid)
            del self.media_top_level_list[index]

        # During the initial call to this function, delete the container
        #   object from the Video Index (which automatically resets the Video
        #   Catalogue)
        if not recursive_flag:
            self.main_win_obj.video_index_delete_row(media_data_obj)

            # Also redraw the private folders in the Video Index, to show the
            #   correct number of downloaded/new videos, etc
            self.main_win_obj.video_index_update_row_text(
                self.fixed_all_folder,
            )

            self.main_win_obj.video_index_update_row_text(
                self.fixed_new_folder,
            )

            self.main_win_obj.video_index_update_row_text(
                self.fixed_fav_folder,
            )


    # (Change media data object settings, updating all related things)


    def mark_video_new(self, video_obj, flag, no_update_index_flag=False):

        """Can be called by anything.

        Marks a video object as new (i.e. unwatched by the user), or as not
        new (already watched by the user).

        The video object's .new_flag IV is updated.

        Args:

            video_obj (media.Video): The media.Video object to mark.

            flag (True or False): True to mark the video as new, False to mark
                it as not new.

            no_update_index_flag (True or False): False if the Video Index
                should not be updated, because the calling function wants to do
                that itself.

        """

        if DEBUG_FUNC_FLAG:
            print('ap 3126 mark_video_new')

        # (List of Video Index rows to update, at the end of this function)
        update_list = [self.fixed_new_folder]
        if not no_update_index_flag:
            update_list.append(video_obj.parent_obj)
            update_list.append(self.fixed_all_folder)
            if video_obj.fav_flag:
                update_list.append(self.fixed_fav_folder)

        # Mark the video as new or not new
        if not isinstance(video_obj, media.Video):
            return self.system_error(
                117,
                'Mark video as new request failed sanity check',
            )

        elif not flag:

            # Mark video as not new
            if not video_obj.new_flag:

                # Already marked
                return

            else:

                # Update the video object's IVs
                video_obj.set_new_flag(False)
                # Update the parent object
                video_obj.parent_obj.dec_new_count()

                # Remove this video from the private 'New Videos' folder
                self.fixed_new_folder.del_child(video_obj)
                self.fixed_new_folder.dec_new_count()
                # Update the Video Catalogue, if that folder is the visible one
                #    (deleting the row, if the 'New Videos' folder is visible)
                if self.main_win_obj.video_index_current is not None \
                and self.main_win_obj.video_index_current \
                == self.fixed_new_folder.name:
                    self.main_win_obj.video_catalogue_delete_row(video_obj)

                else:
                    self.main_win_obj.video_catalogue_update_row(video_obj)

                # Update other private folders
                self.fixed_all_folder.dec_new_count()
                if video_obj.fav_flag:
                    self.fixed_fav_folder.dec_new_count()

        else:

            # Mark video as new
            if video_obj.new_flag:

                # Already marked
                return

            else:

                # Update the video object's IVs
                video_obj.set_new_flag(True)
                # Update the parent object
                video_obj.parent_obj.inc_new_count()

                # Add this video to the private 'New Videos' folder
                self.fixed_new_folder.add_child(video_obj)
                self.fixed_new_folder.inc_new_count()
                # Update the Video Catalogue, if that folder is the visible one
                self.main_win_obj.video_catalogue_update_row(video_obj)

                # Update other private folders
                self.fixed_all_folder.inc_new_count()
                if video_obj.fav_flag:
                    self.fixed_fav_folder.inc_new_count()

        # Update rows in the Video Index
        for container_obj in update_list:
            self.main_win_obj.video_index_update_row_text(container_obj)


    def mark_video_downloaded(self, video_obj, flag):

        """Can be called by anything.

        Marks a video object as downloaded (i.e. the video file exists on the
        user's filesystem) or not downloaded.

        The video object's .dl_flag IV is updated.

        Args:

            video_obj (media.Video): The media.Video object to mark.

            flag (True or False): True to mark the video as downloaded, False
                to mark it as not downloaded.

        """

        if DEBUG_FUNC_FLAG:
            print('ap 3226 mark_video_downloaded')

        # (List of Video Index rows to update, at the end of this function)
        update_list = [video_obj.parent_obj, self.fixed_all_folder]

        # Mark the video as downloaded or not downloaded
        if not isinstance(video_obj, media.Video):
            return self.system_error(
                118,
                'Mark video as downloaded request failed sanity check',
            )

        elif not flag:

            # Mark video as not downloaded
            if not video_obj.dl_flag:

                 # Already marked
                 return

            else:

                # Update the video object's IVs
                video_obj.set_dl_flag(False)
                # Update the parent container object
                video_obj.parent_obj.dec_dl_count()
                # Update private folders
                self.fixed_all_folder.dec_dl_count()
                self.fixed_new_folder.dec_dl_count()
                if video_obj.fav_flag:
                    self.fixed_fav_folder.dec_dl_count()
                    update_list.append(self.fixed_fav_folder)

                # Also mark the video as not new
                self.mark_video_new(video_obj, False, True)

        else:

            # Mark video as downloaded
            if video_obj.dl_flag:

                 # Already marked
                 return

            else:

                # If any ancestor channels, playlists or folders are marked as
                #   favourite, the video must be marked favourite as well
                if video_obj.ancestor_is_favourite():
                    self.mark_video_favourite(video_obj, True, True)

                # Update the video object's IVs
                video_obj.set_dl_flag(True)
                # Update the parent container object
                video_obj.parent_obj.inc_dl_count()
                # Update private folders
                self.fixed_all_folder.inc_dl_count()
                self.fixed_new_folder.inc_dl_count()
                if video_obj.fav_flag:
                    self.fixed_fav_folder.inc_dl_count()
                    update_list.append(self.fixed_fav_folder)

                # Also mark the video as new
                self.mark_video_new(video_obj, True, True)

        # Update rows in the Video Index
        for container_obj in update_list:
            self.main_win_obj.video_index_update_row_text(container_obj)


    def mark_video_favourite(self, video_obj, flag, \
    no_update_index_flag=False):

        """Can be called by anything.

        Marks a video object as favourite or not favourite.

        The video object's .fav_flag IV is updated.

        Args:

            video_obj (media.Video): The media.Video object to mark.

            flag (True or False): True to mark the video as favourite, False
                to mark it as not favourite.

            no_update_index_flag (True or False): False if the Video Index
                should not be updated, because the calling function wants to do
                that itself.

        """

        if DEBUG_FUNC_FLAG:
            print('ap 3319 mark_video_favourite')

        # (List of Video Index rows to update, at the end of this function)
        update_list = [self.fixed_fav_folder]
        if not no_update_index_flag:
            update_list.append(video_obj.parent_obj)
            update_list.append(self.fixed_all_folder)
            if video_obj.new_flag:
                update_list.append(self.fixed_new_folder)

        # Mark the video as favourite or not favourite
        if not isinstance(video_obj, media.Video):
            return self.system_error(
                119,
                'Mark video as favourite request failed sanity check',
            )

        elif not flag:

            # Mark video as not favourite
            if not video_obj.fav_flag:

                # Already marked
                return

            else:

                # Update the video object's IVs
                video_obj.set_fav_flag(False)
                # Update the parent object
                video_obj.parent_obj.dec_fav_count()

                # Remove this video from the private 'Favourite Videos' folder
                self.fixed_fav_folder.del_child(video_obj)
                self.fixed_fav_folder.dec_new_count()
                self.fixed_fav_folder.dec_fav_count()
                self.fixed_fav_folder.dec_dl_count()
                # Update the Video Catalogue, if that folder is the visible one
                #    (deleting the row, if the 'New Videos' folder is visible)
                if self.main_win_obj.video_index_current is not None \
                and self.main_win_obj.video_index_current \
                == self.fixed_fav_folder.name:
                    self.main_win_obj.video_catalogue_delete_row(video_obj)

                else:
                    self.main_win_obj.video_catalogue_update_row(video_obj)

                # Update other private folders
                self.fixed_all_folder.dec_fav_count()
                if video_obj.new_flag:
                    self.fixed_new_folder.dec_fav_count()

        else:

            # Mark video as favourite
            if video_obj.fav_flag:

                # Already marked
                return

            else:

                # Update the video object's IVs
                video_obj.set_fav_flag(True)
                # Update the parent object
                video_obj.parent_obj.inc_fav_count()

                # Add this video to the private 'Favourite Videos' folder
                self.fixed_fav_folder.add_child(video_obj)
                self.fixed_fav_folder.inc_new_count()
                self.fixed_fav_folder.inc_fav_count()
                self.fixed_fav_folder.inc_dl_count()

                # Update the Video Catalogue, if that folder is the visible one
                self.main_win_obj.video_catalogue_update_row(video_obj)

                # Update other private folders
                self.fixed_all_folder.inc_fav_count()
                if video_obj.new_flag:
                    self.fixed_new_folder.inc_fav_count()

        # Update rows in the Video Index
        for container_obj in update_list:
            self.main_win_obj.video_index_update_row_text(container_obj)


    def mark_folder_hidden(self, folder_obj, flag):

        """Called by callbacks in self.on_menu_show_hidden() and
        mainwin.MainWin.on_video_index_hide_folder().

        Marks a folder as hidden (not visible in the Video Index) or not
        hidden (visible in the Video Index, although the user might be
        required to expand the tree to see it).

        Args:

            folder_obj (media.Folder): The folder object to mark

            flag (True or False): True to mark the folder as hidden, False to
                mark it as not hidden.

        """

        if DEBUG_FUNC_FLAG:
            print('ap 3424 mark_folder_hidden')

        if not isinstance(folder_obj, media.Folder):
            return self.system_error(
                120,
                'Mark folder as hidden request failed sanity check',
            )

        if not flag:

            # Mark folder as not hidden
            if not folder_obj.hidden_flag:

                # Already marked
                return

            else:

                # Update the folder object's IVs
                folder_obj.set_hidden_flag(False)
                # Update the Video Index
                self.main_win_obj.video_index_add_row(folder_obj)

        else:

            # Mark video as hidden
            if folder_obj.hidden_flag:

                # Already marked
                return

            else:

                # Update the folder object's IVs
                folder_obj.set_hidden_flag(True)
                # Update the Video Index
                self.main_win_obj.video_index_delete_row(folder_obj)


    def mark_container_favourite(self, media_data_obj, flag):

        """Called by mainwin.MainWin.on_video_index_mark_favourite() and
        .on_video_index_mark_not_favourite().

        Mark this channel, playlist or folder as favourite. Also mark any
        descendant videos as favourite (but not descendent channels, playlists
        or folders).

        Args:

            media_data_obj (media.Channel, media.Playlist or media.Folder):
                The container object to update

            flag (True or False): True to mark as favourite, False to mark as
                not favourite

        """

        if DEBUG_FUNC_FLAG:
            print('ap 3483 mark_container_favourite')

        if isinstance(media_data_obj, media.Video):
            return self.system_error(
                121,
                'Mark container as favourite request failed sanity check',
            )

        # Special arrangements for private folders. Mark the videos as
        #   favourite, but don't modify their parent channels, playlists and
        #   folders
        # (For the private 'Favourite Videos' folder, don't need to do anything
        #   if 'flag' is True, because the popup menu item is desensitised)
        if media_data_obj == self.fixed_all_folder:

            # Check every video
            for other_obj in list(self.media_reg_dict.values()):

                if isinstance(other_obj, media.Video):
                    self.mark_video_favourite(other_obj, flag, True)

        elif media_data_obj == self.fixed_new_folder:

            # Check videos in this folder
            for other_obj in self.fixed_new_folder.child_list:

                if isinstance(other_obj, media.Video) \
                and other_obj.new_flag:
                    self.mark_video_favourite(other_obj, flag, True)

        elif not flag and media_data_obj == self.fixed_fav_folder:

            # Check videos in this folder
            for other_obj in self.fixed_fav_folder.child_list:

                if isinstance(other_obj, media.Video) \
                and other_obj.fav_flag:
                    self.mark_video_favourite(other_obj, flag, True)

        else:

            # Check only video objects that are descendants of the specified
            #   media data object
            for other_obj in media_data_obj.compile_all_videos( [] ):

                if isinstance(other_obj, media.Video):
                    self.mark_video_favourite(other_obj, flag, True)
                else:
                    # For channels, playlists and folders, we can set the IV
                    #   directly
                    other_obj.set_fav_flag(flag)

            # The channel, playlist or folder itself is also marked as
            #   favourite (obviously, we don't do that for private folders)
            media_data_obj.set_fav_flag(flag)

        # In all cases, update the row on the Video Index
        self.main_win_obj.video_index_update_row_icon(media_data_obj)
        self.main_win_obj.video_index_update_row_text(media_data_obj)


    def apply_download_options(self, media_data_obj):

        """Called by callbacks in
        mainwin.MainWin.on_video_index_apply_options() and
        GenericEditWin.on_button_apply_clicked().

        Applies a download options object (options.OptionsManager) to a media
        data object, and also to any of its descendants (unless they too have
        an applied download options object).

        The download options are passed to youtube-dl during a download
        operation.

        Args:

            media_data_obj (media.Video, media.Channel, media.Playlist or
                media.Folder): The media data object to which the download
                options are applied.

        """

        if DEBUG_FUNC_FLAG:
            print('ap 3566 apply_download_options')

        if self.current_manager_obj \
        or media_data_obj.options_obj\
        or (
            isinstance(media_data_obj, media.Folder)
            and media_data_obj.priv_flag
        ):
            return self.system_error(
                122,
                'Apply download options request failed sanity check',
            )

        # Apply download options to the media data object
        media_data_obj.set_options_obj(options.OptionsManager())
        # Update the row in the Video Index
        self.main_win_obj.video_index_update_row_icon(media_data_obj)


    def remove_download_options(self, media_data_obj):

        """Called by callbacks in
        mainwin.MainWin.on_video_index_remove_options() and
        GenericEditWin.on_button_remove_clicked().

        Removes a download options object (options.OptionsManager) from a media
        data object, an action which also affects its descendants (unless they
        too have an applied download options object).

        Args:

            media_data_obj (media.Video, media.Channel, media.Playlist or
                media.Folder): The media data object from which the download
                options are removed.

        """

        if DEBUG_FUNC_FLAG:
            print('ap 3604 remove_download_options')

        if self.current_manager_obj or not media_data_obj.options_obj:
            return self.system_error(
                123,
                'Remove download options request failed sanity check',
            )

        # Remove download options from the media data object
        media_data_obj.set_options_obj(None)
        # Update the row in the Video Index
        self.main_win_obj.video_index_update_row_icon(media_data_obj)


    # (Interact with media data objects)


    def watch_video_in_player(self, video_obj):

        """Called by callback in
        mainwin.MainWin.on_video_catalogue_watch_video() and
        mainwin.ComplexCatalogueItem.on_click_watch_player_label().

        Watch a video using the system's default media player, first checking
        that a file actually exists.

        Args:

            video_obj (media.Video): The video to watch

        """

        if DEBUG_FUNC_FLAG:
            print('ap 3637 watch_video_in_player')

        path = os.path.abspath(
            os.path.join(
                video_obj.file_dir,
                video_obj.file_name + video_obj.file_ext,
            ),
        )

        if not os.path.isfile(path):

            self.dialogue_manager_obj.show_msg_dialogue(
                'The video file is missing from ' \
                + utils.upper_case_first(__main__.__packagename__) \
                + '\'s\ndata directory (try downloading the\nvideo again!',
                'error',
                'ok',
            )

        else:
            utils.open_file(cgi.escape(path, quote=True))


    # (Options manager objects)


    def reset_options_manager(self, data_list):

        """Called by dialogue.on_clicked(), which was in turn called by
        config.OptionsEditWin.on_reset_options_clicked().

        Resets the specified download options object, setting its options to
        their default values.

        Args:

            data_list (list): List of values supplied by the dialogue window.
                The first is the edit window for the download options object
                (which must be reset). The second optional value is the media
                data object to which the download options object belongs.

        """

        edit_win_obj = data_list.pop(0)

        # Replace the old object with a new one, which has the effect of
        #   resetting its download options to the default values
        options_obj = options.OptionsManager()

        if data_list:

            # The Download Options object belongs to the specified media data
            #   object
            media_data_obj = data_list.pop(0)
            media_data_obj.set_options_obj(options_obj)

        else:

            # The General Download Options object
            self.general_options_obj = options_obj

        # Reset the edit window to display the new (default) values
        edit_win_obj.reset_with_new_edit_obj(options_obj)


    # Callback class methods (for Gio actions)


    # (Download operation timer)


    def timer_callback(self):

        """Called by gobject timer created by self.download_manager_start().

        During a download operation, a GObject timer runs, so that statistics
        in the Progress Tab can be updated at regular intervals

        There is also a delay between the instant at which youtube-dl reports a
        video file has been downloaded, and the instant at which it appears in
        the filesystem. The timer checks for newly-existing files at regular
        intervals, too

        Returns:

            1 to keep the timer going, or None to halt it

        """

        if DEBUG_FUNC_FLAG:
            print('ap 3683 timer_callback')

        if self.timer_check_time is None:
            self.main_win_obj.progress_list_display_dl_stats()
            self.main_win_obj.results_list_update_row()

            # Download operation still in progress, return 1 to keep the timer
            #   going
            return 1

        elif self.timer_check_time > time.time():
            self.main_win_obj.progress_list_display_dl_stats()
            self.main_win_obj.results_list_update_row()

            if self.main_win_obj.results_list_temp_list:
                # Not all downloaded files confirmed to exist yet, so return 1
                #   to keep the timer going a little longer
                return 1

        # The download operation has finished. The call to
        #   self.download_manager_finished() destroys the timer
        self.download_manager_finished()


    # (Menu item and toolbar button callbacks)


    def on_button_first_page(self, action, par):

        """Called from a callback in self.do_startup().

        Changes the Video Catalogue page to the first one.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        if DEBUG_FUNC_FLAG:
            print('ap 3685 on_button_first_page')

        self.main_win_obj.video_catalogue_redraw_all(
            self.main_win_obj.video_index_current,
            1,
        )


    def on_button_last_page(self, action, par):

        """Called from a callback in self.do_startup().

        Changes the Video Catalogue page to the last one.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        if DEBUG_FUNC_FLAG:
            print('ap 3686 on_button_last_page')

        self.main_win_obj.video_catalogue_redraw_all(
            self.main_win_obj.video_index_current,
            self.main_win_obj.catalogue_toolbar_last_page,
        )


    def on_button_next_page(self, action, par):

        """Called from a callback in self.do_startup().

        Changes the Video Catalogue page to the next one.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        if DEBUG_FUNC_FLAG:
            print('ap 3687 on_button_next_page')

        self.main_win_obj.video_catalogue_redraw_all(
            self.main_win_obj.video_index_current,
            self.main_win_obj.catalogue_toolbar_current_page + 1,
        )


    def on_button_previous_page(self, action, par):

        """Called from a callback in self.do_startup().

        Changes the Video Catalogue page to the previous one.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        if DEBUG_FUNC_FLAG:
            print('ap 3688 on_button_previous_page')

        self.main_win_obj.video_catalogue_redraw_all(
            self.main_win_obj.video_index_current,
            self.main_win_obj.catalogue_toolbar_current_page - 1,
        )


    def on_button_scroll_down(self, action, par):

        """Called from a callback in self.do_startup().

        Scrolls the Video Catalogue page to the bottom.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        if DEBUG_FUNC_FLAG:
            print('ap 3689 on_button_scroll_down')

        adjust = self.main_win_obj.catalogue_scrolled.get_vadjustment()
        adjust.set_value(adjust.get_upper())


    def on_button_scroll_up(self, action, par):

        """Called from a callback in self.do_startup().

        Scrolls the Video Catalogue page to the top.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        if DEBUG_FUNC_FLAG:
            print('ap 3690 on_button_scroll_up')

        self.main_win_obj.catalogue_scrolled.get_vadjustment().set_value(0)


    def on_button_stop_operation(self, action, par):

        """Called from a callback in self.do_startup().

        Stops the current download/update/refresh operation.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        if DEBUG_FUNC_FLAG:
            print('ap 3725 on_button_stop_operation')

        self.operation_halted_flag = True

        if self.download_manager_obj:
            self.download_manager_obj.stop_download_operation()
        elif self.update_manager_obj:
            self.update_manager_obj.stop_update_operation()
        elif self.refresh_manager_obj:
            self.refresh_manager_obj.stop_refresh_operation()


    def on_button_switch_view(self, action, par):

        """Called from a callback in self.do_startup().

        Toggles between simple and complex views in the Video Catalogue, and
        between showing the names of each video's parent channel/playlist/
        folder

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        if DEBUG_FUNC_FLAG:
            print('ap 3752 on_button_switch_view')

        # There are four modes in a fixed sequence; switch to the next mode in
        #   the sequence
        if self.catalogue_mode == 'simple_hide_parent':
            self.catalogue_mode = 'simple_show_parent'
        elif self.catalogue_mode == 'simple_show_parent':
            self.catalogue_mode = 'complex_hide_parent'
        elif self.catalogue_mode == 'complex_hide_parent':
            self.catalogue_mode = 'complex_show_parent'
        else:
            self.catalogue_mode = 'simple_hide_parent'

        # Redraw the Video Catalogue, but only if something was already drawn
        #   there (and keep the current page number)
        if self.main_win_obj.video_index_current is not None:
            self.main_win_obj.video_catalogue_redraw_all(
                self.main_win_obj.video_index_current,
                self.main_win_obj.catalogue_toolbar_current_page,
            )


    def on_menu_about(self, action, par):

        """Called from a callback in self.do_startup().

        Show a standard 'about' dialogue window.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        if DEBUG_FUNC_FLAG:
            print('ap 3782 on_menu_about')

        dialogue_win = Gtk.AboutDialog()
        dialogue_win.set_transient_for(self.main_win_obj)
        dialogue_win.set_destroy_with_parent(True)

        dialogue_win.set_program_name(__main__.__packagename__.title())
        dialogue_win.set_version('v' + __main__.__version__)
        dialogue_win.set_copyright(__main__.__copyright__)
        dialogue_win.set_license(__main__.__license__)
        dialogue_win.set_website(__main__.__website__)
        dialogue_win.set_website_label(
            __main__.__packagename__.title() + ' website'
        )
        dialogue_win.set_comments(__main__.__description__)
        dialogue_win.set_logo(
            self.main_win_obj.pixbuf_dict['system_icon'],
        )
        dialogue_win.set_authors(__main__.__author_list__)
        dialogue_win.set_title('')
        dialogue_win.connect('response', self.on_menu_about_close)

        dialogue_win.show()


    def on_menu_about_close(self, action, par):

        """Called from a callback in self.do_startup().

        Close the 'about' dialogue window.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        if DEBUG_FUNC_FLAG:
            print('ap 3822 on_menu_about_close')

        action.destroy()


    def on_menu_add_channel(self, action, par):

        """Called from a callback in self.do_startup().

        Creates a dialogue window to allow the user to specify a new channel.
        If the user specifies a channel, creates a media.Channel object.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        if DEBUG_FUNC_FLAG:
            print('ap 3843 on_menu_add_channel')

        dialogue_win = mainwin.AddChannelDialogue(self.main_win_obj)
        response = dialogue_win.run()

        # Retrieve user choices from the dialogue window...
        name = dialogue_win.entry.get_text()
        source = dialogue_win.entry2.get_text()
        dl_sim_flag = dialogue_win.button2.get_active()

        # ...and find the name of the parent media data object (a
        #   media.Folder), if one was specified...
        parent_name = None
        if hasattr(dialogue_win, 'parent_name'):
            parent_name = dialogue_win.parent_name

        # ...before destroying the dialogue window
        dialogue_win.destroy()

        if response == Gtk.ResponseType.OK:

            if not name or re.match('^\s*$', name):
                self.dialogue_manager_obj.show_msg_dialogue(
                    'You must give the channel a name',
                    'error',
                    'ok',
                )

            elif not source or not utils.check_url(source):
                self.dialogue_manager_obj.show_msg_dialogue(
                    'You must enter a valid URL',
                    'error',
                    'ok',
                )

            elif name in self.media_name_dict:

                # Another channel, playlist or folder is already using this
                #   name
                self.reject_media_name(name)

            else:

                # Remove leading/trailing whitespace from the name; make sure
                #   the name is not excessively long
                name = utils.tidy_up_container_name(
                    name,
                    self.container_name_max_len,
                )

                # Find the parent media data object (a media.Folder), if
                #   specified
                parent_obj = None
                if parent_name and parent_name in self.media_name_dict:
                    dbid = self.media_name_dict[parent_name]
                    parent_obj = self.media_reg_dict[dbid]

                # Create the new channel
                channel_obj = self.add_channel(
                    name,
                    parent_obj,
                    source,
                    dl_sim_flag,
                )

                # Add the channel to Video Index
                if channel_obj:
                    self.main_win_obj.video_index_add_row(channel_obj)


    def on_menu_add_folder(self, action, par):

        """Called from a callback in self.do_startup().

        Creates a dialogue window to allow the user to specify a new folder.
        If the user specifies a folder, creates a media.Folder object.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        if DEBUG_FUNC_FLAG:
            print('ap 3927 on_menu_add_folder')

        dialogue_win = mainwin.AddFolderDialogue(self.main_win_obj)
        response = dialogue_win.run()

        # Retrieve user choices from the dialogue window...
        name = dialogue_win.entry.get_text()

        # ...and find the name of the parent media data object (a
        #   media.Folder), if one was specified...
        parent_name = None
        if hasattr(dialogue_win, 'parent_name'):
            parent_name = dialogue_win.parent_name

        # ...before destroying the dialogue window
        dialogue_win.destroy()

        if response == Gtk.ResponseType.OK:

            if not name or re.match('^\s*$', name):
                self.dialogue_manager_obj.show_msg_dialogue(
                    'You must give the folder a name',
                    'error',
                    'ok',
                )

            elif name in self.media_name_dict:

                # Another channel, playlist or folder is already using this
                #   name
                self.reject_media_name(name)

            else:

                # Remove leading/trailing whitespace from the name; make sure
                #   the name is not excessively long
                name = utils.tidy_up_container_name(
                    name,
                    self.container_name_max_len,
                )

                # Find the parent media data object (a media.Folder), if
                #   specified
                parent_obj = None
                if parent_name and parent_name in self.media_name_dict:
                    dbid = self.media_name_dict[parent_name]
                    parent_obj = self.media_reg_dict[dbid]

                # Create the new folder
                folder_obj = self.add_folder(name, parent_obj)

                # Add the folder to the Video Index
                if folder_obj:
                    self.main_win_obj.video_index_add_row(folder_obj)


    def on_menu_add_playlist(self, action, par):

        """Called from a callback in self.do_startup().

        Creates a dialogue window to allow the user to specify a new playlist.
        If the user specifies a playlist, creates a media.PLaylist object.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        if DEBUG_FUNC_FLAG:
            print('ap 3992 on_menu_add_playlist')

        dialogue_win = mainwin.AddPlaylistDialogue(self.main_win_obj)
        response = dialogue_win.run()

        # Retrieve user choices from the dialogue window...
        name = dialogue_win.entry.get_text()
        source = dialogue_win.entry2.get_text()
        dl_sim_flag = dialogue_win.button2.get_active()

        # ...and find the name of the parent media data object (a
        #   media.Folder), if one was specified...
        parent_name = None
        if hasattr(dialogue_win, 'parent_name'):
            parent_name = dialogue_win.parent_name

        # ...before destroying the dialogue window
        dialogue_win.destroy()

        if response == Gtk.ResponseType.OK:

            if not name or re.match('^\s*$', name):
                self.dialogue_manager_obj.show_msg_dialogue(
                    'You must give the playlist a name',
                    'error',
                    'ok',
                )

            elif not source or not utils.url_check(source):
                self.dialogue_manager_obj.show_msg_dialogue(
                    'You must enter a valid URL',
                    'error',
                    'ok',
                )

            elif name in self.media_name_dict:

                # Another channel, playlist or folder is already using this
                #   name
                self.reject_media_name(name)

            else:

                # Remove leading/trailing whitespace from the name; make sure
                #   the name is not excessively long
                name = utils.tidy_up_container_name(
                    name,
                    self.container_name_max_len,
                )

                # Find the parent media data object (a media.Folder), if
                #   specified
                parent_obj = None
                if parent_name and parent_name in self.media_name_dict:
                    dbid = self.media_name_dict[parent_name]
                    parent_obj = self.media_reg_dict[dbid]

                # Create the playlist
                playlist_obj = self.add_playlist(
                    name,
                    parent_obj,
                    source,
                    dl_sim_flag,
                )

                # Add the playlist to the Video Index
                if playlist_obj:
                    self.main_win_obj.video_index_add_row(playlist_obj)


    def on_menu_add_video(self, action, par):

        """Called from a callback in self.do_startup().

        Creates a dialogue window to allow the user to specify one or more
        videos. If the user supplies some URLs, creates media.Video objects.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        if DEBUG_FUNC_FLAG:
            print('ap 4076 on_menu_add_video')

        dialogue_win = mainwin.AddVideoDialogue(self.main_win_obj)
        response = dialogue_win.run()

        # Retrieve user choices from the dialogue window...
        text = dialogue_win.textbuffer.get_text(
            dialogue_win.textbuffer.get_start_iter(),
            dialogue_win.textbuffer.get_end_iter(),
            False,
        )

        # ...and find the parent media data object (a media.Channel,
        #   media.Playlist or media.Folder)...
        parent_name = self.fixed_misc_folder.name
        if hasattr(dialogue_win, 'parent_name'):
            parent_name = dialogue_win.parent_name

        dbid = self.media_name_dict[parent_name]
        parent_obj = self.media_reg_dict[dbid]

        # ...before destroying the dialogue window
        dialogue_win.destroy()

        if response == Gtk.ResponseType.OK:

            # Split text into a list of lines and filter out invalid URLs
            video_list = []
            duplicate_list = []
            for line in text.split('\n'):

                # Remove leading/trailing whitespace
                line = utils.strip_whitespace(line)

                # Perform checks on the URL. If it passes, remove leading/
                #   trailing whitespace
                if utils.check_url(line):
                    video_list.append(utils.strip_whitespace(line))

            # Check everything in the list against other media.Video objects
            #   with the same parent folder
            for line in video_list:
                if parent_obj.check_duplicate_video(line):
                    duplicate_list.append(line)
                else:
                    self.add_video(parent_obj, line)

            # In the Video Index, select the parent media data object, which
            #   updates both the Video Index and the Video Catalogue
            self.main_win_obj.video_index_select_row(parent_obj)
            # !!! TODO BUG: That doesn't work, possibly because of the gtk_iter
            #   error we have been getting, so artificially update the Video
            #   Catalogue if the parent container is the visible one
#            if self.main_win_obj.video_index_current is not None \
#            and self.main_win_obj.video_index_current == parent_obj.name:
#                self.main_win_obj.video_catalogue_redraw_all(parent_obj.name)
            if self.main_win_obj.video_index_current is not None \
            and (
                self.main_win_obj.video_index_current == parent_obj.name \
                or self.main_win_obj.video_index_current == 'All Videos'
            ):
                self.main_win_obj.video_catalogue_redraw_all(
                    self.main_win_obj.video_index_current,
                )

            # If any duplicates were found, inform the user
            if duplicate_list:

                msg = 'The following videos are duplicates:'
                for line in duplicate_list:
                    msg += '\n' + line

                self.dialogue_manager_obj.show_msg_dialogue(
                    msg,
                    'warning',
                    'ok',
                )


    def on_menu_check_all(self, action, par):

        """Called from a callback in self.do_startup().

        Call a function to start a new download operation (if allowed).

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        if DEBUG_FUNC_FLAG:
            print('ap 4137 on_menu_check_all')

        self.download_manager_start(True)


    def on_menu_download_all(self, action, par):

        """Called from a callback in self.do_startup().

        Call a function to start a new download operation (if allowed).

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        if DEBUG_FUNC_FLAG:
            print('ap 4157 on_menu_download_all')

        self.download_manager_start(False)


    def on_menu_general_options(self, action, par):

        """Called from a callback in self.do_startup().

        Opens an edit window for the General Options Manager.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        if DEBUG_FUNC_FLAG:
            print('ap 4177 on_menu_general_options')

        config.OptionsEditWin(self, self.general_options_obj, None)


    def on_menu_refresh_db(self, action, par):

        """Called from a callback in self.do_startup().

        Starts a refresh operation.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        if DEBUG_FUNC_FLAG:
            print('ap 4197 on_menu_refresh_db')

        self.refresh_manager_start()


    def on_menu_save_db(self, action, par):

        """Called from a callback in self.do_startup().

        Save the Tartube database.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        if DEBUG_FUNC_FLAG:
            print('ap 4217 on_menu_save_db')

        self.save_db()

        # Show a dialogue window for confirmation (unless file load/save has
        #   been disabled, in which case a dialogue has already appeared)
        if not self.disable_load_save_flag:

            self.dialogue_manager_obj.show_msg_dialogue(
                'Database saved',
                'info',
                'ok',
            )


    def on_menu_show_hidden(self, action, par):

        """Called from a callback in self.do_startup().

        Un-hides all hidden media.Folder objects (and their children)

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        if DEBUG_FUNC_FLAG:
            print('ap 4247 on_menu_show_hidden')

        for name in self.media_name_dict:

            dbid = self.media_name_dict[name]
            media_data_obj = self.media_reg_dict[dbid]

            if isinstance(media_data_obj, media.Folder) \
            and media_data_obj.hidden_flag:
                self.mark_folder_hidden(media_data_obj, False)


    def on_menu_system_preferences(self, action, par):

        """Called from a callback in self.do_startup().

        Opens a preference window to edit system preferences.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        if DEBUG_FUNC_FLAG:
            print('ap 4274 on_menu_system_preferences')

        config.SystemPrefWin(self)


    def on_menu_test(self, action, par):

        """Called from a callback in self.do_startup().

        Add a set of media data objects for testing. This function can only be
        called if the debugging flags are set.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        if DEBUG_FUNC_FLAG:
            print('ap 4295 on_menu_test')

        # Add media data objects for testing: videos, channels, playlists and/
        #   or folders
        testing.add_test_media(self)

        # Clicking the Test button more than once just adds illegal duplicate
        #   channels/playlists/folders (and non-illegal duplicate videos), so
        #   just disable the button and the menu item
        # (Check the widgets exist, in case they have been commented out)
        if self.main_win_obj.test_menu_item:
            self.main_win_obj.test_menu_item.set_sensitive(False)
        if self.main_win_obj.test_button:
            self.main_win_obj.test_button.set_sensitive(False)

        # Redraw the video catalogue, if a Video Index row is selected
        if self.main_win_obj.video_index_current is not None:
            self.main_win_obj.video_catalogue_redraw_all(
                self.main_win_obj.video_index_current,
            )


    def on_menu_update_ytdl(self, action, par):

        """Called from a callback in self.do_startup().

        Start an update operation to update the system's youtube-dl.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        if DEBUG_FUNC_FLAG:
            print('ap 4332 on_menu_update_ytdl')

        self.update_manager_start()


    def on_menu_quit(self, action, par):

        """Called from a callback in self.do_startup().

        Terminates the Tartube app.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        if DEBUG_FUNC_FLAG:
            print('ap 4352 on_menu_quit')

        self.stop()


    # (Callback support functions)


    def reject_media_name(self, name):

        """Called by self.on_menu_add_channel(), .on_menu_add_playlist()
        and .on_menu_add_folder().

        If the user specifies a name for a channel, playlist or folder that's
        already in use by a channel, playlist or folder, tell them why they
        can't use it.

        Args:

            name (str): The name specified by the user

        """

        if DEBUG_FUNC_FLAG:
            print('ap 4376 reject_media_name')

        # Get the existing media data object with this name
        dbid = self.media_name_dict[name]
        media_data_obj = self.media_reg_dict[dbid]

        if isinstance(media_data_obj, media.Channel):
            string = 'channel'
        elif isinstance(media_data_obj, media.Playlist):
            string = 'playlist'
        elif isinstance(media_data_obj, media.Folder):
            string = 'folder'

        self.dialogue_manager_obj.show_msg_dialogue(
            'There is already a ' + string + ' with that name\n' \
            + '(so please choose a different name)',
            'error',
            'ok',
        )


    # Set accessors


    def set_apply_json_timeout_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            print('ap 4413 set_apply_json_timeout_flag')

        if not flag:
            self.apply_json_timeout_flag = False
        else:
            self.apply_json_timeout_flag = True


    def set_bandwidth_default(self, value):

        """Called by mainwin.MainWin.on_spinbutton2_changed().

        Sets the new bandwidth limit. If a download operation is in progress,
        the new value is applied to the next download job.

        Args:

            value (int): The new bandwidth limit

        """

        if DEBUG_FUNC_FLAG:
            print('ap 4414 set_bandwidth_default')

        if value < self.bandwidth_min or value > self.bandwidth_max:
            return self.system_error(
                124,
                'Set bandwidth request failed sanity check',
            )

        self.bandwidth_default = value


    def set_bandwidth_apply_flag(self, flag):

        """Called by mainwin.MainWin.on_checkbutton2_changed().

        Applies or releases the bandwidth limit. If a download operation is in
        progress, the new setting is applied to the next download job.
        """

        if DEBUG_FUNC_FLAG:
            print('ap 4434 set_bandwidth_apply_flag')

        if not flag:
            self.bandwidth_apply_flag = False
        else:
            self.bandwidth_apply_flag = True


    def set_catalogue_page_size(self, size):

        if DEBUG_FUNC_FLAG:
            print('ap 4434 set_catalogue_page_size')

        self.catalogue_page_size = size


    def set_complex_index_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            print('ap 4445 set_complex_index_flag')

        if not flag:
            self.complex_index = False
        else:
            self.complex_index = True


    def set_db_backup_mode(self, value):

        if DEBUG_FUNC_FLAG:
            print('ap 4446 set_db_backup_mode')

        self.db_backup_mode = value


    def set_ignore_child_process_exit_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            print('ap 4456 set_ignore_child_process_exit_flag')

        if not flag:
            self.ignore_child_process_exit_flag = False
        else:
            self.ignore_child_process_exit_flag = True


    def set_ignore_merge_warning_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            print('ap 4457 set_ignore_merge_warning_flag')

        if not flag:
            self.ignore_merge_warning_flag = False
        else:
            self.ignore_merge_warning_flag = True


    def set_ignore_yt_copyright_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            print('a7 4458 set_ignore_yt_copyright_flag')

        if not flag:
            self.ignore_yt_copyright_flag = False
        else:
            self.ignore_yt_copyright_flag = True


    def set_match_first_chars(self, num_chars):

        if DEBUG_FUNC_FLAG:
            print('ap 4467 set_match_first_chars')

        self.match_first_chars = num_chars


    def set_match_ignore_chars(self, num_chars):

        if DEBUG_FUNC_FLAG:
            print('ap 4475 set_match_ignore_chars')

        self.match_ignore_chars = num_chars


    def set_match_method(self, method):

        if DEBUG_FUNC_FLAG:
            print('ap 4483 set_match_method')

        self.match_method = method


    def set_num_worker_apply_flag(self, flag):

        """Called by mainwin.MainWin.on_checkbutton_changed().

        Applies or releases the simultaneous download limit. If a download
        operation is in progress, the new setting is applied to the next
        download job.
        """

        if DEBUG_FUNC_FLAG:
            print('ap 4498 set_num_worker_apply_flag')

        if not flag:
            self.bandwidth_apply_flag = False
        else:
            self.bandwidth_apply_flag = True


    def set_num_worker_default(self, value):

        """Called by mainwin.MainWin.on_spinbutton_changed() and
        .on_checkbutton_changed().

        Sets the new value for the number of simultaneous downloads allowed. If
        a download operation is in progress, informs the download manager
        object, so the number of download workers can be adjusted.

        Args:

            value (int): The new number of simultaneous downloads

        """

        if DEBUG_FUNC_FLAG:
            print('ap 4522 set_num_worker_default')

        if value < self.num_worker_min or value > self.num_worker_max:
            return self.system_error(
                125,
                'Set simultaneous downloads request failed sanity check',
            )

        old_value = self.num_worker_default
        self.num_worker_default = value

        if old_value != value and self.download_manager_obj:
            self.download_manager_obj.change_worker_count(value)


    def set_operation_auto_update_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            print('ap 4540 set_operation_auto_update_flag')

        if not flag:
            self.operation_auto_update_flag = False
        else:
            self.operation_auto_update_flag = True


    def set_operation_check_limit(self, value):

        if DEBUG_FUNC_FLAG:
            print('ap 4541 set_operation_check_limit')

        self.operation_check_limit = value


    def set_operation_dialogue_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            print('ap 4551 set_operation_dialogue_flag')

        if not flag:
            self.operation_dialogue_flag = False
        else:
            self.operation_dialogue_flag = True


    def set_operation_download_limit(self, value):

        if DEBUG_FUNC_FLAG:
            print('ap 4552 set_operation_download_limit')

        self.operation_download_limit = value


    def set_operation_limit_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            print('ap 4553 set_operation_limit_flag')

        if not flag:
            self.operation_limit_flag = False
        else:
            self.operation_limit_flag = True


    def set_operation_save_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            print('ap 4562 set_operation_save_flag')

        if not flag:
            self.operation_save_flag = False
        else:
            self.operation_save_flag = True


    def set_toolbar_squeeze_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            print('ap 4563 set_toolbar_squeeze_flag')

        if not flag:
            self.toolbar_squeeze_flag = False
        else:
            self.toolbar_squeeze_flag = True

        if self.main_win_obj and self.main_win_obj.main_toolbar:
            self.main_win_obj.redraw_main_toolbar()


    def set_use_module_moviepy_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            print('ap 4573 set_use_module_moviepy_flag')

        if not flag:
            self.use_module_moviepy_flag = False
        else:
            self.use_module_moviepy_flag = True


    def set_ytdl_path(self, path):

        if DEBUG_FUNC_FLAG:
            print('ap 4595 set_ytdl_path')

        self.ytdl_path = path


    def set_ytdl_update_current(self, string):

        if DEBUG_FUNC_FLAG:
            print('ap 4603 set_ytdl_update_current')

        self.ytdl_update_current = string


    def set_ytdl_write_ignore_json_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            print('ap 4604 set_ytdl_write_ignore_json_flag')

        if not flag:
            self.ytdl_write_ignore_json_flag = False
        else:
            self.ytdl_write_ignore_json_flag = True


    def set_ytdl_write_stderr_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            print('ap 4611 set_ytdl_write_stderr_flag')

        if not flag:
            self.ytdl_write_stderr_flag = False
        else:
            self.ytdl_write_stderr_flag = True


    def set_ytdl_write_stdout_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            print('ap 4622 set_ytdl_write_stdout_flag')

        if not flag:
            self.ytdl_write_stdout_flag = False
        else:
            self.ytdl_write_stdout_flag = True


    def set_ytdl_write_verbose_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            print('ap 4633 set_ytdl_write_verbose_flag')

        if not flag:
            self.ytdl_write_verbose_flag = False
        else:
            self.ytdl_write_verbose_flag = True
