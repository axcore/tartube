#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2020 A S Lewis
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
import datetime
import json
import math
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

try:
    from xdg.BaseDirectory import xdg_config_home
    HAVE_XDG_FLAG = True
except:
    HAVE_XDG_FLAG = False


# Import our modules
import __main__
import config
import dialogue
import downloads
import files
import formats
import mainwin
import media
import options
import refresh
import testing
import threading
import updates
import utils


# Debugging flag (calls utils.debug_time at the start of every function)
DEBUG_FUNC_FLAG = False


# Classes


class TartubeApp(Gtk.Application):

    """Main python class for the Tartube application."""


    # Standard class methods


    def __init__(self, *args, **kwargs):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('ap 93 __init__')

        super(TartubeApp, self).__init__(
            *args,
            application_id=__main__.__app_id__,
            flags=Gio.ApplicationFlags.FLAGS_NONE,
            **kwargs)

        # Debugging flags
        # ---------------
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
        # Automatically open the general download options window on startup
        self.debug_open_options_win_flag = False
        # Hide all the system folders (this is not reversible by setting the
        #   flag back to False)
        self.debug_hide_folders_flag = False


        # Instance variable (IV) list - class objects
        # -------------------------------------------
        # The main window object, set as soon as it's created
        self.main_win_obj = None
        # The system tray icon (a mainapp.StatusIcon object, inheriting from
        #   Gtk.StatusIcon)
        self.status_icon_obj = None
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
        # Default size (in pixels) of space between various widgets
        self.default_spacing_size = 5

        # The current Gtk version
        self.gtk_version_major = Gtk.get_major_version()
        self.gtk_version_minor = Gtk.get_minor_version()
        self.gtk_version_micro = Gtk.get_micro_version()
        # Gtk v3.22.* produces numerous error/warning messages in the terminal
        #   when the Video Index and Video Catalogue are updated. Whatever the
        #   issues were, they appear to have been (mostly) fixed by Gtk v3.24.*
        # Flag set to True by self.start() if Tartube is being run before
        #   Gtk v3.24, in which case some cosmetic functions (mostly related
        #   to sorting the Video Index and Video Catalogue) are disabled
        self.gtk_broken_flag = False
        # The flag above is set automatically, but the user can set this flag
        #   themselves. If True, Tartube behaves as if self.gtk_broken_flag was
        #   set (on all systems)
        self.gtk_emulate_broken_flag = False

        # At all times (after initial setup), two GObject timers run - a fast
        #   one and a slow one
        # The slow timer's ID
        self.script_slow_timer_id = None
        # The slow timer interval time (in milliseconds)
        self.script_slow_timer_time = 60000
        # The fast timer's ID
        self.script_fast_timer_id = None
        # The fast timer interval time (in milliseconds)
        self.script_fast_timer_time = 1000

        # Flag set to True if the main toolbar should be compressed (by
        #   removing the labels); ideal if the toolbar's contents won't fit in
        #   the standard-sized window (as it almost certainly won't on MS
        #   Windows)
        if os.name != 'nt':
            self.toolbar_squeeze_flag = False
        else:
            self.toolbar_squeeze_flag = True
        # Flag set to True if tooltips should be visible in the Video Index
        #   and the Video Catalogue
        self.show_tooltips_flag = True
        # Flag set to True if small icons should be used in the Video Index,
        #   False if large icons should be used
        self.show_small_icons_in_index = False
        # Flag set to True if the Video Index treeview should auto-expand
        #   when an item is clicked, to show its children (only folders
        #   have children visible in the Video Index, though)
        self.auto_expand_video_index_flag = False
        # Flag set to True if the 'Download all' buttons in the main window
        #   toolbar and in the Videos tab should be disabled (in case the u
        #   user is sure they only want to do 'Check all' operations
        self.disable_dl_all_flag = False
        # Flag set to True if an icon should be displayed in the system tray
        self.show_status_icon_flag = True
        # Flag set to True if the main window should close to the tray, rather
        #   than halting the application altogether. Ignore if
        #   self.show_status_icon_flag is False
        self.close_to_tray_flag = True

        # Flag set to True if rows in the Progress List should be hidden once
        #   the download operation has finished with the corresponding media
        #   data object (so the user can see the media data objects currently
        #   being downloaded more easily)
        self.progress_list_hide_flag = False
        # Flag set to True if new rows should be added to the Results List
        #   at the top, False if they should be added at the bottom
        self.results_list_reverse_flag = False

        # Flag set to True if system error messages should be shown in the
        #   Errors/Warnings tab
        self.system_error_show_flag = True
        # Flag set to True if system warning messages should be shown in the
        #   Errors/Warnings tab
        self.system_warning_show_flag = True
        # Flag set to True if operation error messages should be shown in the
        #   Errors/Warnings tab
        self.operation_error_show_flag = True
        # Flag set to True if system warning messages should be shown in the
        #   Errors/Warnings tab
        self.operation_warning_show_flag = True
        # Flag set to True if the total number of system error/warning messages
        #   shown in the tab label is not reset until the 'Clear the list'
        #   button is explicitly clicked (normally, the total numbers are
        #   reset when the user switches to a different tab)
        self.system_msg_keep_totals_flag = False

        # For quick lookup, the directory in which the 'tartube' executable
        #   file is found, and its parent directory
        self.script_dir = sys.path[0]
        self.script_parent_dir = os.path.abspath(
            os.path.join(self.script_dir, os.pardir),
        )

        # Tartube's data directory (platform-dependant), i.e. 'tartube-data'
        # Note that, using the MSWin installer, Cygwin gives file paths with
        #   both / and \ separators. Throughout the code, we use
        #   os.path.abspath to circumvent this problem
        self.default_data_dir = os.path.abspath(
            os.path.join(
                os.path.expanduser('~'),
                __main__.__packagename__ + '-data',
            ),
        )
        self.data_dir = self.default_data_dir
        # The data directory is structured like this:
        #   /tartube-data
        #       tartube.db          [the Tartube database file]
        #       /.backups
        #           tartube_BU.db   [any number of database file backups]
        #       /.temp              [temporary directory, deleted on startup]
        #       /pewdiepie          [example of a custom media.Channel]
        #       /Temporary Videos   [standard media.Folder]
        #       /Unsorted Videos    [standard media.Folder]
        # Before v1.3.099, the data directory was structured like this:
        #   /tartube-data
        #       tartube.db
        #       tartube_BU.db
        #       /.temp
        #       /downloads
        #           /pewdiepie
        #           /Temporary Videos
        #           /Unsorted Videos
        # Tartube can read from both stcuctures although, when creating a new
        #   data directory, only the new structure is created
        #
        # The sub-directory into which videos are downloaded (new and old
        #   style)
        self.downloads_dir = os.path.abspath(
            os.path.join(
                os.path.expanduser('~'),
                __main__.__packagename__ + '-data',
            ),
        )
        self.alt_downloads_dir = os.path.abspath(
            os.path.join(
                os.path.expanduser('~'),
                __main__.__packagename__ + '-data',
                'downloads',
            ),
        )
        # A hidden directory, used for storing backups of the Tartube database
        #   file
        self.backup_dir = os.path.abspath(
            os.path.join(
                os.path.expanduser('~'),
                __main__.__packagename__ + '-data',
                '.backups',
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

        # Name of the Tartube config file
        self.config_file_name = 'settings.json'
        # The config file can be stored at one of two locations, depending on
        #   the value of __main__.__debian_install_flag__
        self.config_file_path = os.path.abspath(
            os.path.join(self.script_parent_dir, self.config_file_name),
        )

        if not HAVE_XDG_FLAG:
            self.config_file_xdg_path = None
        else:
            self.config_file_xdg_path = os.path.abspath(
                os.path.join(
                    xdg_config_home,
                    __main__.__packagename__,
                    self.config_file_name,
                   ),
            )

        # Name of the Tartube database file (storing media data objects). The
        #   database file is always found in self.data_dir
        self.db_file_name = __main__.__packagename__ + '.db'
        # Names of the database export files (one for JSON, for for plain text)
        self.export_json_file_name \
        = __main__.__packagename__ + '_db_export.json'
        self.export_text_file_name \
        = __main__.__packagename__ + '_db_export.txt'
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
        # Optional error message generated when self.disable_load_save_flag
        #   was set to True
        self.disable_load_save_msg = None
        # Users have reported that the Tartube database file was corrupted. On
        #   inspection, it was almost completely empty, presumably because
        #   self.save_db had been called before .load_db
        # As the corruption was catastrophic, make sure that can never happen
        #   again with this flag, set to False until the code has either
        #   loaded a database file, or wants to call .save_db to create one
        self.allow_db_save_flag = False

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

        # Flag set to True if youtube-dl system commands should be displayed in
        #   the Output Tab
        self.ytdl_output_system_cmd_flag = True
        # Flag set to True if youtube-dl's STDOUT should be displayed in the
        #   Output Tab
        self.ytdl_output_stdout_flag = True
        # Flag set to True if we should ignore JSON output when displaying text
        #   in the Output Tab (ignored if self.ytdl_output_stdout_flag is
        #   False)
        self.ytdl_output_ignore_json_flag = True
        # Flag set to True if we should ignore download progress (as a
        #   percentage) when displaying text in the Output Tab (ignored if
        #   self.ytdl_output_stdout_flag is False)
        self.ytdl_output_ignore_progress_flag = True
        # Flag set to True if youtube-dl's STDERR should be displayed in the
        #   Output Tab
        self.ytdl_output_stderr_flag = True
        # Flag set to True if pages in the Output Tab should be emptied at the
        #   start of each operation
        self.ytdl_output_start_empty_flag = True
        # Flag set to True if a summary page should be visible in the Output
        #   Tab. Changes to this flag are applied when Tartube restarts
        self.ytdl_output_show_summary_flag = False

        # Flag set to True if youtube-dl system commands should be written to
        #   the terminal window
        self.ytdl_write_system_cmd_flag = False
        # Flag set to True if youtube-dl's STDOUT should be written to the
        #   terminal window
        self.ytdl_write_stdout_flag = False
        # Flag set to True if we should ignore JSON output when writing to the
        #   terminal window (ignored if self.ytdl_write_stdout_flag is False)
        self.ytdl_write_ignore_json_flag = True
        # Flag set to True if we should ignore download progress (as a
        #   percentage) when writing to the terminal window (ignored if
        #   self.ytdl_write_stdout_flag is False)
        self.ytdl_write_ignore_progress_flag = True
        # Flag set to True if youtube-dl's STDERR should be written to the
        #   terminal window
        self.ytdl_write_stderr_flag = False

        # Flag set to True if youtube-dl should show verbose output (using the
        #   --verbose option). The setting applies to both the Output Tab and
        #   the terminal window
        self.ytdl_write_verbose_flag = False

        # Flag set to True if, during a refresh operation, videos should be
        #   displayed in the Output Tab. Set to False if only channels,
        #   playlists and folders should be displayed there
        self.refresh_output_videos_flag = True
        # Flag set to True if, during a refresh operation, non-matching videos
        #   should be displayed in the Output Tab. Set to False if only
        #   matching videos should be displayed there. Ignore if
        #   self.refresh_output_videos_flag is False
        self.refresh_output_verbose_flag = False
        # The moviepy module hangs indefinitely, if it is used to open a
        #   corrupted video file
        #   (see https://github.com/Zulko/moviepy/issues/639)
        # To counter this, self.update_video_from_filesystem() moves the
        #   operation into a thread, and applies a timeout to that thread
        # The timeout (in seconds) to apply. Must be an integer, 0 or above.
        #   If 0, the moviepy operation is allowed to hang indefinitely
        self.refresh_moviepy_timeout = 10

        # Path to the ffmpeg/avconv binary (or the directory containing the
        #   binary). If set to any value besides None,
        #   downloads.VideoDownloader will pass the value to youtube-dl using
        #   its --ffmpeg-location option
        self.ffmpeg_path = None

        # Flag set to True if the General Options Manager
        #   (self.general_options_obj) should be cloned whenever the user
        #   applies a new options manager to a media data object (e.g. by
        #   right-clicking a channel in the Video Index, and selecting
        #   Downloads > Apply options manager)
        self.auto_clone_options_flag = True

        # During a download operation, a GObject timer runs, so that the
        #   Progress Tab and Output Tab can be updated at regular intervals
        # There is also a delay between the instant at which youtube-dl
        #   reports a video file has been downloaded, and the instant at which
        #   it appears in the filesystem. The timer checks for newly-existing
        #   files at regular intervals, too
        # The timer's ID (None when no timer is running)
        self.dl_timer_id = None
        # The timer interval time (in milliseconds)
        self.dl_timer_time = 500
        # At the end of the download operation, the timer continues running for
        #   a few seconds, to give new files a chance to appear in the
        #   filesystem. The maximum time to wait (in seconds)
        self.dl_timer_final_time = 10
        # Once that extra time has been applied, the time (matches time.time())
        #   at which to stop waiting
        self.dl_timer_check_time = None

        # During a download operation, we periodically check whether the device
        #   containing self.data_dir is running out of space
        # The check interval time (in seconds)
        self.dl_timer_disk_space_time = 60
        # The time (matchs time.time()) at which the next check takes place
        self.dl_timer_disk_space_check_time = None

        # Flag set to True if Tartube should warn if the system is running out
        #   of disk space (on the drive containing self.data_dir), False if
        #   not. The warning is issued at the start of a download operation
        self.disk_space_warn_flag = True
        # The amount of free disk space (in Mb) below which the warning is
        #   issued. If 0, no warning is issued. Ignored if
        #   self.disk_space_warn_flag is False
        self.disk_space_warn_limit = 1000
        # Flag set to True if Tartube should refuse to start a download
        #   operation, and halt an existing download operation, if the system
        #   is running out of disk space (on the drive containing
        #   self.data_dir), False if not
        self.disk_space_stop_flag = True
        # The amount of free disk space (in Mb) below which the refusal/halt
        #   is enacted. If 0, a download operation will continue downloading
        #   files until the device actually runs out of space. Ignored if
        #   self.disk_space_stop_flag is False
        self.disk_space_stop_limit = 500
        # The IVs above can be set to any number (0 or above), but the
        #   Gtk.SpinButtons in the system preferences window increment/
        #   decrement the value by this many Mb at a time
        self.disk_space_increment = 100
        # An absolute minimum of disk space, below which a download operation
        #   will not start, or will halt, regardless of the values of the IVs
        #   above (in Mb)
        self.disk_space_abs_limit = 50

        # During an update operation, a separate GObject timer runs, so that
        #   the Output Tab can be updated at regular intervals
        # The timer's ID (None when no timer is running)
        self.update_timer_id = None
        # The timer interval time (in milliseconds)
        self.update_timer_time = 500
        # At the end of the update operation, the timer continues running for
        #   a few seconds, to prevent various Gtk errors (and occasionally
        #   crashes) for systems with Gtk < 3.2. The maximum time to wait (in
        #   seconds)
        self.update_timer_final_time = 5
        # Once that extra time has been applied, the time (matches time.time())
        #   at which to stop waiting
        self.update_timer_check_time = None

        # During a refresh operation, a separate GObject timer runs, so that
        #   the Output Tab can be updated at regular intervals
        # The timer's ID (None when no timer is running)
        self.refresh_timer_id = None
        # The timer interval time (in milliseconds)
        self.refresh_timer_time = 500
        # At the end of the refresh operation, the timer continues running for
        #   a few seconds, to prevent various Gtk errors (and occasionally
        #   crashes) for systems with Gtk < 3.2. The maximum time to wait (in
        #   seconds)
        self.refresh_timer_final_time = 5
        # Once that extra time has been applied, the time (matches time.time())
        #   at which to stop waiting
        self.refresh_timer_check_time = None

        # During any operation, a flag set to True if the operation was halted
        #   by the user, rather than being allowed to complete naturally
        self.operation_halted_flag = False
        # During a download operation, a flag set to True if Tartube must shut
        #   down when the operation is finished
        self.halt_after_operation_flag = False
        # During a download operation, a flag set to True if no dialogue
        #   window must be shown at the end of that operation (but not
        #   necessarily any future download operations)
        self.no_dialogue_this_time_flag = False

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
        # Forbidden names for channels, playlists and folders. This is to
        #   prevent the user overwriting directories in self.data_dir, that
        #   Tartube uses for its own purposes, and to prevent the user fooling
        #   Tartube into thinking that the old file structure is being used
        # Every item in this list is a regex; a name for a channel, playlist
        #   or folder must not match any item in the list. (media.Video
        #   objects can still have any name)
        self.illegal_name_regex_list = [
            r'^\.',
            r'^downloads$',
            __main__.__packagename__,
        ]

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

        # A list of media.Video objects the user wants to watch, as soon as
        #   they have been downloaded. Videos are added by a call to
        #   self.watch_after_dl_list(), and removed by a call to
        #   self.announce_video_download()
        self.watch_after_dl_list = []

        # Automatic 'Download all' download operations - 'none' to disable,
        #   'start' to perform the operation whenever Tartube starts, or
        #   'scheduled' to perform the operation at regular intervals
        self.scheduled_dl_mode = 'none'
        # The time (in hours) between 'scheduled' 'Download all' operations, if
        #   enabled (can be fractional)
        self.scheduled_dl_wait_hours = 2
        # The time (system time, in seconds) at which the last 'Download all'
        #   operation started (regardless of whether it was 'scheduled' or not)
        self.scheduled_dl_last_time = 0

        # Automatic 'Check all' download operations - 'none' to disable,
        #   'start' to perform the operation whenever Tartube starts, or
        #   'scheduled' to perform the operation at regular intervals
        self.scheduled_check_mode = 'none'
        # The time (in hours) between 'scheduled' 'Check all' operations, if
        #   enabled (can be fractional)
        self.scheduled_check_wait_hours = 2
        # The time (system time, in seconds) at which the last 'Check all'
        #   operation started (regardless of whether it was scheduled or not)
        self.scheduled_check_last_time = 0

        # Flag set to True if Tartube should shut down after a 'Download all'
        #   operation (if self.scheduled_dl_mode is not 'none'), and after a
        #   'Check all' operation (if self.scheduled_check_mode is not 'none')
        self.scheduled_shutdown_flag = False

        # Flag set to True if a download operation should auto-stop after a
        #   certain period of time (applies to both real and simulated
        #   downloads)
        self.autostop_time_flag = False
        # Auto-stop after this amount of time (minimum value 1)...
        self.autostop_time_value = 1
        # ...in this many units (any of the values in
        #   formats.TIME_METRIC_LIST)
        self.autostop_time_unit = 'hours'
        # Flag set to True if a download operation should auto-stop after a
        #   certain number of videos (applies to both real and simulated
        #   downloads)
        self.autostop_videos_flag = False
        # Auto-stop after this many videos (minimum value 1)
        self.autostop_videos_value = 100
        # Flag set to True if a download operation should auto-stop after
        #   downloading videos of a certain combined size (applies to real
        #   downloads only; the specified size is approximate, because it
        #   relies on th video size reported by youtube-dl, and doesn't take
        #   account of thumbnails, JSON data, and so on)
        self.autostop_size_flag = False
        # Auto-stop after this amount of diskspace (minimum value 1)...
        self.autostop_size_value = 1
        # ...in this many units (any of the values in
        #   formats.FILESIZE_METRIC_LIST)
        self.autostop_size_unit = 'GiB'

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
        self.operation_waiting_list = []
        # Flag set to True if files should be saved at the end of every
        #   operation
        self.operation_save_flag = True
        # How to notify the user at the end of each download/update/refresh
        #   operation: 'dialogue' to use a dialogue window, 'desktop' to use a
        #   desktop notification, or 'default' to do neither
        # NB Desktop notifications don't work on MS Windows
        self.operation_dialogue_mode = 'dialogue'
        # What to do when the user creates a media.Video object whose URL
        #   represents a channel or playlist
        # 'channel' to create a new media.Channel object, and place all the
        #   downloaded videos inside it (the original media.Video object is
        #   destroyed)
        # 'playlist' to create a new media.Playlist object, and place all the
        #   downloaded videos inside it (the original media.Video object is
        #   destroyed)
        # 'multi' to create a new media.Video object for each downloaded video,
        #   placed in the same folder as the original media.Video object (the
        #   original is destroyed)
        # 'disable' to download nothing from the URL
        # There are some restrictions. If the original media.Video object is
        #   contained in a folder whose .restrict_flag is False, and if the
        #   mode is 'channel' or 'playlist', then the new channel/playlist is
        #   not created in that folder. If the original media.Video object is
        #   contained in a channel or playlist, all modes to default to
        #   'disable'
        self.operation_convert_mode = 'channel'
        # Flag set to True if self.update_video_from_filesystem() should get
        #   the video duration, if not already known, using the moviepy.editor
        #   module (an optional dependency)
        self.use_module_moviepy_flag = True

        # Flag set to True if dialogue windows for adding videos, channels and
        #   playlists should copy the contents of the system clipboard
        self.dialogue_copy_clipboard_flag = True
        # Flag set to True if dialogue windows for adding channels and
        #   playlists should continually re-open, whenever the use clicks the
        #   OK button (so multiple channels etc can be added quickly)
        self.dialogue_keep_open_flag = False

        # Flag set to True if, when downloading videos, youtube-dl should be
        #   passed, --download-archive, creating the file ytdl-archive.txt
        # If the file exists, youtube-dl won't re-download a video a user has
        #   deleted
        self.allow_ytdl_archive_flag = True
        # If self.allow_ytdl_archive_flag is set, youtube-dl will have created
        #   a ytdl_archive.txt, recording every video ever downloaded in the
        #   parent directory
        # This will prevent a successful re-downloading of the video. In
        #   response, the archive file is temporarily renamed, and the details
        #   are stored in these IVs
        self.ytdl_archive_path = None
        self.ytdl_archive_backup_path = None
        # Flag set to True if, when checking videos/channels/playlists, we
        #   should timeout after 60 seconds (in case youtube-dl gets stuck
        #   downloading the JSON data)
        self.apply_json_timeout_flag = True

        # Flag set to True if 'Child process exited with non-zero code'
        #   messages, generated by Tartube, should be ignored (in the
        #   Errors/Warnings tab)
        self.ignore_child_process_exit_flag = True
        # Flag set to True if 'unable to download video data: HTTP Error 404'
        #   messages from youtube-dl should be ignored (in the Errors/Warnings
        #   tab)
        self.ignore_http_404_error_flag = False
        # Flag set to True if 'Did not get any data blocks' messages from
        #   youtube-dl should be ignored (in the Errors/Warnings tab)
        self.ignore_data_block_error_flag = False
        # Flag set to True if 'Requested formats are incompatible for merge and
        #   will be merged into mkv' messages from youtube-dl should be ignored
        #   (in the Errors/Warnings tab)
        self.ignore_merge_warning_flag = False
        # Flag set to True if 'No video formats found; please report this
        #   issue on...' messages from youtube-dl should be ignored (in the
        #   Errors/Warnings tab)
        self.ignore_missing_format_error_flag = False
        # Flag set to True if 'There are no annotations to write' messages
        #   should be ignored (in the Errors/Warnings tab)
        self.ignore_no_annotations_flag = False
        # Flag set to True if 'video doesn't have subtitles' errors should be
        #   ignored (in the Errors/Warnings tab)
        self.ignore_no_subtitles_flag = False

        # Flag set to True if YouTube copyright messages should be ignored (in
        #   the Errors/Warnings tab)
        self.ignore_yt_copyright_flag = False
        # Flag set to True if YouTube age-restriction messages should be
        #   ignored (in the Errors/Warnings tab)
        self.ignore_yt_age_restrict_flag = False
        # Flag set to True if 'The uploader has not made this video available'
        #   messages should be ignored (in the Errors/Warnings tab)
        self.ignore_yt_uploader_deleted_flag = False

        # Websites other than YouTube typically use different error messages
        # A custom list of strings or regexes, which are matched against error
        #   messages. Any matching error messages are not displayed in the
        #   Errors/Warnings tab. The user can add
        self.ignore_custom_msg_list = []
        # Flag set to True if the contents of the list are regexes, False if
        #   they are ordinary strings
        self.ignore_custom_regex_flag = False

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

        # During a download operation, the maximum video resolution to
        #   download. Must be one of the keys in formats.VIDEO_RESOLUTION_DICT
        #   (e.g. '720p')
        self.video_res_default = '720p'
        # Flag set to True when this maximum video resolution is applied. When
        #   applied, it overrides the download options 'video_format',
        #   'second_video_format' and 'third_video_format' (see the comments
        #   in options.OptionsManager)
        self.video_res_apply_flag = False

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

        # Automatic video deletion. Applies only to downloaded videos (not to
        #   checked videos)
        # Flag set to True if videos should be deleted after a certain time
        self.auto_delete_flag = False
        # Flag set to True if videos are automatically deleted after a certain
        #   time, but only if they have been watched (media.Video.dl_flag is
        #   True, media.Video.new_flag is False; ignored if
        #   self.auto_delete_old_flag is False)
        self.auto_delete_watched_flag = False
        # Videos are automatically deleted after this many days (must be an
        #   integer, minimum value 1; ignored if self.auto_delete_old_flag is
        #   False)
        self.auto_delete_days = 30

        # Temporary folder emptying (applies to all media.Folder objects whose
        #   .temp_flag is True)
        # Temporary folders are always emptied when Tartube starts. Flag set to
        #   True if they should be emptied when Tartube shuts down, as well
        self.delete_on_shutdown_flag = False

        # How much information to show in the Video Index. False to show
        #   minimal video stats, True to show full video stats
        self.complex_index_flag = False
        # The Video Catalogue has two 'skins', a simple view (without
        #   thumbnails) and a more complex view (with thumbnails)
        # Each skin can be set to show the name of the parent channel/playlist/
        #   folder, or not
        # The current video catalogue mode: 'simple_hide_parent',
        #   'simple_show_parent', 'complex_hide_parent', 'complex_show_parent'
        self.catalogue_mode = 'complex_show_parent'
        # The video catalogue splits its video list into pages (as Gtk
        #   struggles with a list of hundreds, or thousands, of videos)
        # The number of videos per page, or 0 to always use a single page
        self.catalogue_page_size = 50

        # Flag set to True if a smaller set of options should be shown in the
        #   download options edit window (for inexperienced users)
        self.simple_options_flag = True


    def do_startup(self):

        """Gio.Application standard function."""

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 856 do_startup')

        GObject.threads_init()
        Gtk.Application.do_startup(self)

        # Menu actions
        # ------------

        # 'File' column
        change_db_menu_action = Gio.SimpleAction.new('change_db_menu', None)
        change_db_menu_action.connect('activate', self.on_menu_change_db)
        self.add_action(change_db_menu_action)

        save_db_menu_action = Gio.SimpleAction.new('save_db_menu', None)
        save_db_menu_action.connect('activate', self.on_menu_save_db)
        self.add_action(save_db_menu_action)

        save_all_menu_action = Gio.SimpleAction.new('save_all_menu', None)
        save_all_menu_action.connect('activate', self.on_menu_save_all)
        self.add_action(save_all_menu_action)

        close_tray_menu_action = Gio.SimpleAction.new('close_tray_menu', None)
        close_tray_menu_action.connect('activate', self.on_menu_close_tray)
        self.add_action(close_tray_menu_action)

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

        export_db_menu_action = Gio.SimpleAction.new('export_db_menu', None)
        export_db_menu_action.connect('activate', self.on_menu_export_db)
        self.add_action(export_db_menu_action)

        import_json_menu_action = Gio.SimpleAction.new(
            'import_json_menu',
            None,
        )
        import_json_menu_action.connect('activate', self.on_menu_import_json)
        self.add_action(import_json_menu_action)

        import_text_menu_action = Gio.SimpleAction.new(
            'import_text_menu',
            None,
        )
        import_text_menu_action.connect(
            'activate',
            self.on_menu_import_plain_text,
        )
        self.add_action(import_text_menu_action)

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

        refresh_db_menu_action = Gio.SimpleAction.new('refresh_db_menu', None)
        refresh_db_menu_action.connect('activate', self.on_menu_refresh_db)
        self.add_action(refresh_db_menu_action)

        ytdl_menu_action = Gio.SimpleAction.new('update_ytdl_menu', None)
        ytdl_menu_action.connect('activate', self.on_menu_update_ytdl)
        self.add_action(ytdl_menu_action)

        ffmpeg_menu_action = Gio.SimpleAction.new('install_ffmpeg_menu', None)
        ffmpeg_menu_action.connect('activate', self.on_menu_install_ffmpeg)
        self.add_action(ffmpeg_menu_action)

        stop_operation_menu_action = Gio.SimpleAction.new(
            'stop_operation_menu',
            None,
        )
        stop_operation_menu_action.connect(
            'activate',
            self.on_button_stop_operation,
        )
        self.add_action(stop_operation_menu_action)

        # 'Help' column
        about_menu_action = Gio.SimpleAction.new('about_menu', None)
        about_menu_action.connect('activate', self.on_menu_about)
        self.add_action(about_menu_action)

        go_website_menu_action = Gio.SimpleAction.new('go_website_menu', None)
        go_website_menu_action.connect('activate', self.on_menu_go_website)
        self.add_action(go_website_menu_action)

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

        stop_operation_button_action = Gio.SimpleAction.new(
            'stop_operation_toolbutton',
            None,
        )
        stop_operation_button_action.connect(
            'activate',
            self.on_button_stop_operation,
        )
        self.add_action(stop_operation_button_action)

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

        find_date_toolbutton_action = Gio.SimpleAction.new(
            'find_date_toolbutton',
            None,
        )
        find_date_toolbutton_action.connect(
            'activate',
            self.on_button_find_date,
        )
        self.add_action(find_date_toolbutton_action)

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
            utils.debug_time('app 1193 do_activate')

        # Only allow a single main window (raise any existing main windows)
        if not self.main_win_obj:
            self.start()

            # Open the system preferences window, if the debugging flag is set
            if self.debug_open_pref_win_flag:
                config.SystemPrefWin(self)

            # Open the general download options window, if the debugging flag
            #   is set
            if self.debug_open_options_win_flag:
                config.OptionsEditWin(self, self.general_options_obj, None)

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
            utils.debug_time('app 1231 do_shutdown')

        # Stop the GObject timers immediately
        if self.script_slow_timer_id:
            GObject.source_remove(self.script_slow_timer_id)
        if self.script_fast_timer_id:
            GObject.source_remove(self.script_fast_timer_id)
        if self.dl_timer_id:
            GObject.source_remove(self.dl_timer_id)
        if self.update_timer_id:
            GObject.source_remove(self.update_timer_id)
        if self.refresh_timer_id:
            GObject.source_remove(self.refresh_timer_id)

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
        if os.name == 'nt':
            # Under MS Windows, all methods of shutting down after an update
            #   operation fail - except this method
            os._exit(0)


    # Public class methods


    def start(self):

        """Called by self.do_activate().

        Performs general initialisation.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 1271 start')

        # Import the script name (for convenience)
        script_name = utils.upper_case_first(__main__.__packagename__)

        # Gtk v3.22.* produces numerous error/warning messages in the terminal
        #   when the Video Index and Video Catalogue are updated. Whatever the
        #   issues were, they appear to have been fixed by Gtk v3.24.*
        if self.gtk_version_major < 3 \
        or (self.gtk_version_major == 3 and self.gtk_version_minor < 24):

            self.gtk_broken_flag = True

        # Create the main window
        self.main_win_obj = mainwin.MainWin(self)
        # Most main widgets are desensitised, until the database file has been
        #   loaded
        self.main_win_obj.sensitise_widgets_if_database(False)
        # If the debugging flag is set, move it to the top-left corner of the
        #   desktop
        if self.debug_open_top_left_flag:
            self.main_win_obj.move(0, 0)
        # Make it visible
        self.main_win_obj.show_all()

        # Prepare to add an icon to the system tray. The icon is made visible,
        #   if required, after the config file is loaded
        self.status_icon_obj = mainwin.StatusIcon(self)

        # Start the dialogue manager (thread-safe code for Gtk message dialogue
        #   windows)
        self.dialogue_manager_obj = dialogue.DialogueManager(
            self,
            self.main_win_obj,
        )

        # Give mainapp.TartubeApp IVs their initial values

        # Set the General Options Manager
        self.general_options_obj = options.OptionsManager()

        # Set youtube-dl IVs
        if __main__.__debian_install_flag__:
            self.ytdl_bin = 'youtube-dl'
            self.ytdl_path_default = os.path.abspath(
                os.path.join(os.sep, 'usr', 'bin', self.ytdl_bin),
            )
            self.ytdl_path = 'youtube-dl'
            self.ytdl_update_dict = {
                'youtube-dl updates are disabled': [],
            }
            self.ytdl_update_list = [
                'youtube-dl updates are disabled',
            ]
            self.ytdl_update_current = 'youtube-dl updates are disabled'

        elif os.name == 'nt':

            if 'PROGRAMFILES(X86)' in os.environ:
                # 64-bit MS Windows
                descrip = 'Windows 64-bit update (recommended)'
                python_path = '..\\..\\..\\..\\mingw64\\bin\python3.exe'
                pip_path = '..\\..\\..\\..\\mingw64\\bin\pip3-script.py'
            else:
                # 32-bit MS Windows
                descrip = 'Windows 32-bit update (recommended)'
                python_path = '..\\..\\..\\..\\mingw32\\bin\python3.exe'
                pip_path = '..\\..\\..\\..\\mingw32\\bin\pip3-script.py'

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
                    'pip3', 'install', '--upgrade', '--user', 'youtube-dl',
                ],
                'Update using pip3 (omit --user option)': [
                    'pip3', 'install', '--upgrade', 'youtube-dl',
                ],
                'Update using pip': [
                    'pip', 'install', '--upgrade', '--user', 'youtube-dl',
                ],
                'Update using pip (omit --user option)': [
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
                'Update using pip3 (omit --user option)',
                'Update using pip',
                'Update using pip (omit --user option)',
                'Update using default youtube-dl path',
                'Update using local youtube-dl path',
            ]
            self.ytdl_update_current = 'Update using pip3 (recommended)'

        # If the config file exists, load it. If not, create it
        new_config_flag = False

        if (
            not __main__.__debian_install_flag__
            and os.path.isfile(self.config_file_path)
        ) or (
            __main__.__debian_install_flag__
            and self.config_file_xdg_path is not None
            and os.path.isfile(self.config_file_xdg_path)
        ):
            self.load_config()

        elif self.debug_no_dialogue_flag:
            self.save_config()
            new_config_flag = True

        else:

            # New Tartube installation
            new_config_flag = True

            # Show the status icon in the system tray (which would normally be
            #   done after the config file had been loaded)
            if self.status_icon_obj and self.show_status_icon_flag:
                self.status_icon_obj.show_icon()

            # On MS Windows, tell the user that they must set the location of
            #   the data directory, self.data_dir. On other operating systems,
            #   ask the user if they want to use the default location, or
            #   choose a custom one
            custom_flag = self.notify_user_of_data_dir()
            if custom_flag and not self.prompt_user_for_data_dir():

                # The user declined to specify a data directory, so shut down
                #   Tartube. Destroying the main window calls
                #   self.do_shutdown()
                return self.main_win_obj.destroy()

            # All done; create the config file, whether Tartube's data
            #   directory has been changed, or not
            self.save_config()

        # Check that the data directory specified by self.data_dir actually
        #   exists. If not, the most common reason is that the user has
        #   forgotten to mount an external drive
        if not new_config_flag \
        and not self.debug_no_dialogue_flag \
        and not os.path.exists(self.data_dir):

            # Ask the user what to do next. The False argument tells the
            #   dialogue window that it's a missing directory
            dialogue_win = mainwin.MountDriveDialogue(
                self.main_win_obj,
                False,
            )
            dialogue_win.run()

            # If the data directory now exists, or can be created in principle
            #   by the code just below (because the user wants to use the
            #   default location), then available_flag will be True
            available_flag = dialogue_win.available_flag
            dialogue_win.destroy()

            if not available_flag:

                # The user opted to shut down Tartube. Destroying the main
                #   window calls self.do_shutdown()
                return self.main_win_obj.destroy()

        # Create Tartube's data directories (if they don't already exist)
        if not os.path.isdir(self.data_dir):

            # React to a 'Permission denied' error by asking the user what to
            #   do next. If necessary, shut down Tartube
            # The True argument means that the drive is unwriteable
            if not self.make_directory(self.data_dir):
                return self.main_win_obj.destroy()

        # Create the directory for database file backups
        if not os.path.isdir(self.backup_dir):
            if not self.make_directory(self.backup_dir):
                return self.main_win_obj.destroy()

        # Create the temporary data directories (or empty them, if they already
        #   exist)
        if os.path.isdir(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)

            except:
                if not self.make_directory(self.temp_dir):
                    return self.main_win_obj.destroy()
                else:
                    shutil.rmtree(self.temp_dir)

        if not os.path.isdir(self.temp_dir):
            if not self.make_directory(self.temp_dir):
                return self.main_win_obj.destroy()

        if not os.path.isdir(self.temp_dl_dir):
            if not self.make_directory(self.temp_dl_dir):
                return self.main_win_obj.destroy()

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
            self.allow_db_save_flag = True
            self.save_db()

        # Now the config file has been loaded (or created), we can add the
        #   right number of pages to the Output Tab
        self.main_win_obj.output_tab_setup_pages()

        # If the system's Gtk is an early, broken version, display a system
        #   warning
        if self.gtk_broken_flag:
            self.system_warning(
                126,
                'Gtk v' + str(self.gtk_version_major) + '.' \
                + str(self.gtk_version_minor) + '.' \
                + str(self.gtk_version_micro) \
                + ' is broken, which may cause problems when running ' \
                + utils.upper_case_first(__main__.__packagename__) \
                + '. If possible, please update it to at least Gtk v3.24',
            )

        elif self.gtk_emulate_broken_flag:
            self.system_warning(
                140,
                utils.upper_case_first(__main__.__packagename__) \
                + ' is assuming the Gtk v' + str(self.gtk_version_major)
                + ' is broken; some (minor) features are disabled',
            )

        # If file load/save has been disabled, we can now show a dialogue
        #   window
        if self.disable_load_save_flag:

            if self.disable_load_save_msg is None:

                self.file_error_dialogue(
                    'Because of an error,\nfile load/save has been\ndisabled',
                )

            else:

                self.file_error_dialogue(
                    self.disable_load_save_msg + '\n\nBecause of the error,' \
                    + '\nfile load/save been\ndisabled',
                )

        # Start the script's GObject slow timer
        self.script_slow_timer_id = GObject.timeout_add(
            self.script_slow_timer_time,
            self.script_slow_timer_callback,
        )

        # Start the script's GObject fast timer
        self.script_fast_timer_id = GObject.timeout_add(
            self.script_fast_timer_time,
            self.script_fast_timer_callback,
        )

        if not self.disable_load_save_flag:

            # For new installations, MS Windows must be prompted to perform an
            #   update operation, which installs youtube-dl on their system
            if new_config_flag and os.name == 'nt':

                self.dialogue_manager_obj.show_msg_dialogue(
                    'youtube-dl must be installed before you\ncan use ' \
                    + utils.upper_case_first(__main__.__packagename__) \
                    + '. Do you want to install\nyoutube-dl now?',
                    'question',
                    'yes-no',
                    None,                   # Parent window is main window
                    {
                        'yes': 'update_manager_start',
                        # Install FFmpeg, not youtube-dl
                        'data': False,
                    },
                )

            # If a 'Download all' or 'Check all' operation is scheduled to
            #   occur on startup, then initiate it
            elif self.scheduled_dl_mode == 'start':
                self.download_manager_start(
                    False,      # 'Download all'
                    True,       # This function is the calling function
                )

            elif self.scheduled_check_mode == 'start':
                self.download_manager_start(
                    True,       # 'Check all'
                    True,       # This function is the calling function
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
            utils.debug_time('app 1581 stop')

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

        """Called by self.stop(), self.download_manager_finished() or by
        dialogue.MessageDialogue.on_clicked().

        Terminates the Tartube app. Forced shutdowns (for example, by clicking
        the X in the top corner of the window) are handled by
        self.do_shutdown().
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 1624 stop_continue')

        if self.download_manager_obj:
            self.download_manager_obj.stop_download_operation()

        elif self.update_manager_obj:
            self.update_manager_obj.stop_update_operation()

        elif self.refresh_manager_obj:
            self.refresh_manager_obj.stop_refresh_operation()

        # Stop the GObject timers immediately. So this action is not repeated
        #   in the standard call to self.do_shutdown, reset the IVs
        if self.script_slow_timer_id:
            GObject.source_remove(self.script_slow_timer_id)
            self.script_slow_timer_id = None

        if self.script_fast_timer_id:
            GObject.source_remove(self.script_fast_timer_id)
            self.script_fast_timer_id = None

        if self.dl_timer_id:
            GObject.source_remove(self.dl_timer_id)
            self.dl_timer_id = None

        if self.update_timer_id:
            GObject.source_remove(self.update_timer_id)
            self.update_timer_id = None

        if self.refresh_timer_id:
            GObject.source_remove(self.refresh_timer_id)
            self.refresh_timer_id = None

        # Empty any temporary folders from the database (if allowed; those
        #   temporary folders are always deleted when Tartube starts)
        if self.delete_on_shutdown_flag:
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

            Error codes for this function and for self.system_warning are
            currently assigned thus:

            100-199: mainapp.py     (in use: 101-140)
            200-299: mainwin.py     (in use: 201-240)
            300-399: downloads.py   (in use: 301-304)
            400-499: config.py      (in use: 401-404)

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 1696 system_error')

        if self.main_win_obj and self.system_error_show_flag:
            self.main_win_obj.errors_list_add_system_error(error_code, msg)
        else:
            # Emergency fallback: display in the terminal window
            print('SYSTEM ERROR ' + str(error_code) + ': ' + msg)


    def system_warning(self, error_code, msg):

        """Can be called by anything.

        Wrapper function for mainwin.MainWin.errors_list_add_system_warning().

        Args:

            code (int): An error code in the range 100-999. This function and
                self.system_error() share the same error codes

            msg (str): A system error message to display in the main window's
                Errors List.

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 1722 system_warning')

        if self.main_win_obj and self.system_warning_show_flag:
            self.main_win_obj.errors_list_add_system_warning(error_code, msg)
        else:
            # Emergency fallback: display in the terminal window
            print('SYSTEM WARNING ' + str(error_code) + ': ' + msg)


    # (Config/database files load/save)


    def load_config(self):

        """Called by self.start() (only).

        Loads the Tartube config file. If loading fails, disables all file
        loading/saving.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 1743 load_config')

        # The config file can be stored at one of two locations, depending on
        #   the value of __main__.__debian_install_flag__
        if __main__.__debian_install_flag__ \
        and self.config_file_xdg_path is not None:
            config_file_path = self.config_file_xdg_path
        else:
            config_file_path = self.config_file_path

        # Sanity check
        if self.current_manager_obj \
        or not os.path.isfile(config_file_path) \
        or self.disable_load_save_flag:
            return

        # Try to load the config file
        try:
            with open(config_file_path) as infile:
                json_dict = json.load(infile)

        except:
            # Loading failed. Prevent damage to backup files by disabling file
            #   load/save for the rest of this session
            self.disable_load_save(
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

            self.disable_load_save(
                'The ' + utils.upper_case_first(__main__.__packagename__) \
                + ' config file is invalid (missing data)',
            )

        # Convert a version, e.g. 1.234.567, into a simple number, e.g.
        #   1234567, that can be compared with other versions
        version = self.convert_version(json_dict['script_version'])
        # Now check that the config file wasn't written by a more recent
        #   version of Tartube (which this older version might not be able to
        #   read)
        if version is None \
        or version > self.convert_version(__main__.__version__):
            self.disable_load_save(
                'Config file can\'t be read\nby this version of ' \
                + utils.upper_case_first(__main__.__packagename__),
            )

        # Since v1.0.008, config files have identified their file type
        if version >= 1000008 \
        and (
            not 'file_type' in json_dict or json_dict['file_type'] != 'config'
        ):
            self.disable_load_save(
                'The ' + utils.upper_case_first(__main__.__packagename__) \
                + ' config file is invalid (missing file type)',
            )

        # Set IVs to their new values
        if version >= 1003122:  # v1.3.122
            self.gtk_emulate_broken_flag = json_dict['gtk_emulate_broken_flag']

        if version >= 5024:     # v0.5.024
            self.toolbar_squeeze_flag = json_dict['toolbar_squeeze_flag']
        if version >= 1001064:  # v1.1.064
            self.show_tooltips_flag = json_dict['show_tooltips_flag']
        if version >= 1001075:  # v1.1.075
            self.show_small_icons_in_index \
            = json_dict['show_small_icons_in_index']
        if version >= 1001077:  # v1.1.077
            self.auto_expand_video_index_flag \
            = json_dict['auto_expand_video_index_flag']
        if version >= 1001064:  # v1.1.064
            self.disable_dl_all_flag = json_dict['disable_dl_all_flag']
        if version >= 1003024:  # v1.3.024
            self.show_status_icon_flag = json_dict['show_status_icon_flag']
            self.close_to_tray_flag = json_dict['close_to_tray_flag']

        # (Setting the value of the Gtk widgets automatically sets the IVs)
        if version >= 1003129:  # v1.3.129
            self.main_win_obj.hide_finished_checkbutton.set_active(
                json_dict['progress_list_hide_flag'],
            )
        if version >= 1000029:  # v1.0.029
            self.main_win_obj.reverse_results_checkbutton.set_active(
                json_dict['results_list_reverse_flag'],
            )

        if version >= 1003069:  # v1.3.069
            self.main_win_obj.show_system_error_checkbutton.set_active(
                json_dict['system_error_show_flag'],
            )
        if version >= 6006:     # v0.6.006
            self.main_win_obj.show_system_warning_checkbutton.set_active(
                json_dict['system_warning_show_flag'],
            )
        if version >= 1003079:  # v1.3.079
            self.main_win_obj.show_operation_error_checkbutton.set_active(
                json_dict['operation_error_show_flag'],
            )
            self.main_win_obj.show_operation_warning_checkbutton.set_active(
                json_dict['operation_warning_show_flag'],
            )

        if version >= 1000007:  # v1.0.007
            self.system_msg_keep_totals_flag \
            = json_dict['system_msg_keep_totals_flag']

        self.data_dir = json_dict['data_dir']
        # (Update other paths to match)
        self.downloads_dir = self.data_dir
        self.alt_downloads_dir = os.path.abspath(
            os.path.join(self.data_dir, 'downloads'),
        )
        self.backup_dir = os.path.abspath(
            os.path.join(self.data_dir, '.backups'),
        )
        self.temp_dir = os.path.abspath(os.path.join(self.data_dir, '.temp'))
        self.temp_dl_dir = os.path.abspath(
            os.path.join(self.data_dir, '.temp', 'downloads'),
        )

        if version >= 3014:     # v0.3.014
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
        # (In version 1.3.903, these IVs were modified a little, but not
        #   on MS Windows)
        if os.name != 'nt' and version <= 1003090:   # v1.3.090
            self.ytdl_update_dict['Update using pip3 (recommended)'] \
            = ['pip3', 'install', '--upgrade', '--user', 'youtube-dl']
            self.ytdl_update_dict['Update using pip3 (omit --user option)'] \
            = ['pip3', 'install', '--upgrade', 'youtube-dl']
            self.ytdl_update_dict['Update using pip'] \
            = ['pip', 'install', '--upgrade', '--user', 'youtube-dl']
            self.ytdl_update_dict['Update using pip (omit --user option)'] \
            = ['pip', 'install', '--upgrade', 'youtube-dl']
            self.ytdl_update_list = [
                'Update using pip3 (recommended)',
                'Update using pip3 (omit --user option)',
                'Update using pip',
                'Update using pip (omit --user option)',
                'Update using default youtube-dl path',
                'Update using local youtube-dl path',
            ]

        if version >= 1003074:  # v1.3.074
            self.ytdl_output_system_cmd_flag \
            = json_dict['ytdl_output_system_cmd_flag']
        if version >= 1002030:  # v1.2.030
            self.ytdl_output_stdout_flag = json_dict['ytdl_output_stdout_flag']
            self.ytdl_output_ignore_json_flag \
            = json_dict['ytdl_output_ignore_json_flag']
            self.ytdl_output_ignore_progress_flag \
            = json_dict['ytdl_output_ignore_progress_flag']
            self.ytdl_output_stderr_flag = json_dict['ytdl_output_stderr_flag']
            self.ytdl_output_start_empty_flag \
            = json_dict['ytdl_output_start_empty_flag']
        if version >= 1003064:  # v1.3.064
            self.ytdl_output_show_summary_flag \
            = json_dict['ytdl_output_show_summary_flag']

        if version >= 1003074:  # v1.3.074
            self.ytdl_write_system_cmd_flag \
            = json_dict['ytdl_write_system_cmd_flag']
        self.ytdl_write_stdout_flag = json_dict['ytdl_write_stdout_flag']
        if version >= 5004:     # v0.5.004
            self.ytdl_write_ignore_json_flag \
            = json_dict['ytdl_write_ignore_json_flag']
        if version >= 1002030:  # v1.2.030
            self.ytdl_write_ignore_progress_flag \
            = json_dict['ytdl_write_ignore_progress_flag']
        self.ytdl_write_stderr_flag = json_dict['ytdl_write_stderr_flag']

        self.ytdl_write_verbose_flag = json_dict['ytdl_write_verbose_flag']

        if version >= 1002024:  # v1.2.024
            self.refresh_output_videos_flag \
            = json_dict['refresh_output_videos_flag']
        if version >= 1002027:  # v1.2.027
            self.refresh_output_verbose_flag \
            = json_dict['refresh_output_verbose_flag']
        if version >= 1003012:  # v1.3.012
            self.refresh_moviepy_timeout = json_dict['refresh_moviepy_timeout']

        if version >= 1003032:  # v1.3.032
            self.auto_clone_options_flag = json_dict['auto_clone_options_flag']

        if version >= 1002030:  # v1.2.037
            self.disk_space_warn_flag = json_dict['disk_space_warn_flag']
            self.disk_space_warn_limit = json_dict['disk_space_warn_limit']
            self.disk_space_stop_flag = json_dict['disk_space_stop_flag']
            self.disk_space_stop_limit = json_dict['disk_space_stop_limit']

        if version >= 1001054:  # v1.1.054
            self.ffmpeg_path = json_dict['ffmpeg_path']

        if version >= 3029:     # v0.3.029
            self.operation_limit_flag = json_dict['operation_limit_flag']
            self.operation_check_limit = json_dict['operation_check_limit']
            self.operation_download_limit \
            = json_dict['operation_download_limit']

        if version >= 1001067:  # v1.0.067
            self.scheduled_dl_mode = json_dict['scheduled_dl_mode']
            self.scheduled_dl_wait_hours = json_dict['scheduled_dl_wait_hours']
            self.scheduled_dl_last_time = json_dict['scheduled_dl_last_time']

            self.scheduled_check_mode = json_dict['scheduled_check_mode']
            self.scheduled_check_wait_hours \
            = json_dict['scheduled_check_wait_hours']
            self.scheduled_check_last_time \
            = json_dict['scheduled_check_last_time']

            # Renamed in v1.3.120
            if 'scheduled_stop_flag' in json_dict:
                self.scheduled_shutdown_flag = json_dict['scheduled_stop_flag']
            else:
                self.scheduled_shutdown_flag \
                = json_dict['scheduled_shutdown_flag']

        if version >= 1003112:  # v1.3.112
            self.autostop_time_flag = json_dict['autostop_time_flag']
            self.autostop_time_value = json_dict['autostop_time_value']
            self.autostop_time_unit = json_dict['autostop_time_unit']
            self.autostop_videos_flag = json_dict['autostop_videos_flag']
            self.autostop_videos_value = json_dict['autostop_videos_value']
            self.autostop_size_flag = json_dict['autostop_size_flag']
            self.autostop_size_value = json_dict['autostop_size_value']
            self.autostop_size_unit = json_dict['autostop_size_unit']

        self.operation_auto_update_flag \
        = json_dict['operation_auto_update_flag']
        self.operation_save_flag = json_dict['operation_save_flag']
#       # Removed v1.3.028
#        self.operation_dialogue_flag = json_dict['operation_dialogue_flag']
        if version >= 1003028:  # v1.3.028
            self.operation_dialogue_mode = json_dict['operation_dialogue_mode']
        if version >= 1003060:  # v1.3.060
            self.operation_convert_mode = json_dict['operation_convert_mode']

        self.use_module_moviepy_flag = json_dict['use_module_moviepy_flag']
#       # Removed v0.5.003
#        self.use_module_validators_flag \
#        = json_dict['use_module_validators_flag']

        if version >= 1000006:  # v1.0.006
            self.dialogue_copy_clipboard_flag \
            = json_dict['dialogue_copy_clipboard_flag']
            self.dialogue_keep_open_flag \
            = json_dict['dialogue_keep_open_flag']
            # Removed v1.3.022
#            self.dialogue_keep_container_flag \
#            = json_dict['dialogue_keep_container_flag']

        if version >= 1003018:  # v1.3.018
            self.allow_ytdl_archive_flag \
            = json_dict['allow_ytdl_archive_flag']
        if version >= 5004:     # v0.5.004
            self.apply_json_timeout_flag \
            = json_dict['apply_json_timeout_flag']

        if version >= 5004:     # v0.5.004
            self.ignore_child_process_exit_flag \
            = json_dict['ignore_child_process_exit_flag']
        if version >= 1003088:  # v1.3.088
            self.ignore_http_404_error_flag \
            = json_dict['ignore_http_404_error_flag']
            self.ignore_data_block_error_flag \
            = json_dict['ignore_data_block_error_flag']
        if version >= 1027:     # v0.1.028
            self.ignore_merge_warning_flag \
            = json_dict['ignore_merge_warning_flag']
        if version >= 1003088:  # v1.3.088
            self.ignore_missing_format_error_flag \
            = json_dict['ignore_missing_format_error_flag']
        if version >= 1001077:  # v1.1.077
            self.ignore_no_annotations_flag \
            = json_dict['ignore_no_annotations_flag']
        if version >= 1002004:  # v1.2.004
            self.ignore_no_subtitles_flag \
            = json_dict['ignore_no_subtitles_flag']

        if version >= 5004:     # v0.5.004
            self.ignore_yt_copyright_flag \
            = json_dict['ignore_yt_copyright_flag']
        if version >= 1003084:  # v1.3.084
            self.ignore_yt_age_restrict_flag \
            = json_dict['ignore_yt_age_restrict_flag']
        if version >= 1003088:  # v1.3.088
            self.ignore_yt_age_restrict_flag \
            = json_dict['ignore_yt_uploader_deleted_flag']

        if version >= 1003090:  # v1.3.090
            self.ignore_custom_msg_list \
            = json_dict['ignore_custom_msg_list']
            self.ignore_custom_regex_flag \
            = json_dict['ignore_custom_regex_flag']

        # (Setting the value of the Gtk widgets automatically sets the IVs)
        self.main_win_obj.num_worker_spinbutton.set_value(
            json_dict['num_worker_default'],
        )
        self.main_win_obj.num_worker_checkbutton.set_active(
            json_dict['num_worker_apply_flag'],
        )

        self.main_win_obj.bandwidth_spinbutton.set_value(
            json_dict['bandwidth_default'],
        )
        self.main_win_obj.bandwidth_checkbutton.set_active(
            json_dict['bandwidth_apply_flag'],
        )

        if version >= 1002011:  # v1.2.011
            self.main_win_obj.set_video_res_limit(
                json_dict['video_res_default'],
            )
            self.main_win_obj.video_res_checkbutton.set_active(
                json_dict['video_res_apply_flag'],
            )

        self.match_method = json_dict['match_method']
        self.match_first_chars = json_dict['match_first_chars']
        self.match_ignore_chars = json_dict['match_ignore_chars']

        if version >= 1001029:  # v1.1.029
            self.auto_delete_flag = json_dict['auto_delete_flag']
            self.auto_delete_watched_flag \
            = json_dict['auto_delete_watched_flag']
            self.auto_delete_days = json_dict['auto_delete_days']

        if version >= 1002041:  # v1.2.041
            self.delete_on_shutdown_flag = json_dict['delete_on_shutdown_flag']

        self.complex_index_flag = json_dict['complex_index_flag']
        if version >= 3019:  # v0.3.019
            self.catalogue_mode = json_dict['catalogue_mode']
        if version >= 3023:  # v0.3.023
            self.catalogue_page_size = json_dict['catalogue_page_size']

        if version >= 1002013:  # v1.2.013
            self.simple_options_flag = json_dict['simple_options_flag']

        # Now update various widgets, having loaded the config file

        # If the tray icon should be visible, make it visible
        if self.show_status_icon_flag:
            self.status_icon_obj.show_icon()

        # If self.toolbar_squeeze_flag is set, redraw the main toolbar without
        #   labels
        if self.toolbar_squeeze_flag:
            self.main_win_obj.redraw_main_toolbar()

        # If self.show_tooltips_flag is not set, disable tooltips
        if not self.show_tooltips_flag:
            self.main_win_obj.disable_tooltips()

        # If self.disable_dl_all_flag, disable the 'Download all' buttons
        if self.disable_dl_all_flag:
            self.main_win_obj.disable_dl_all_buttons()

        # Set the page size in the Video Catalogue
        self.main_win_obj.catalogue_size_entry.set_text(
            str(self.catalogue_page_size),
        )


    def save_config(self):

        """Called by self.start(), .stop(), switch_db(),
        .download_manager_finished(), .update_manager_finished and
        .refresh_manager_finished().

        Saves the Tartube config file. If saving fails, disables all file
        loading/saving.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 2051 save_config')

        # The config file can be stored at one of two locations, depending on
        #   the value of __main__.__debian_install_flag__
        if __main__.__debian_install_flag__ \
        and self.config_file_xdg_path is not None:
            config_file_path = self.config_file_xdg_path
        else:
            config_file_path = self.config_file_path

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
            'file_type': 'config',
            # Data
            'gtk_emulate_broken_flag': self.gtk_emulate_broken_flag,

            'toolbar_squeeze_flag': self.toolbar_squeeze_flag,
            'show_tooltips_flag': self.show_tooltips_flag,
            'show_small_icons_in_index': self.show_small_icons_in_index,
            'auto_expand_video_index_flag': self.auto_expand_video_index_flag,
            'disable_dl_all_flag': self.disable_dl_all_flag,
            'show_status_icon_flag': self.show_status_icon_flag,
            'close_to_tray_flag': self.close_to_tray_flag,

            'progress_list_hide_flag': self.progress_list_hide_flag,
            'results_list_reverse_flag': self.results_list_reverse_flag,

            'system_error_show_flag': self.system_error_show_flag,
            'system_warning_show_flag': self.system_warning_show_flag,
            'operation_error_show_flag': self.operation_error_show_flag,
            'operation_warning_show_flag': self.operation_warning_show_flag,
            'system_msg_keep_totals_flag': self.system_msg_keep_totals_flag,

            'data_dir': self.data_dir,

            'db_backup_mode': self.db_backup_mode,

            'ytdl_bin': self.ytdl_bin,
            'ytdl_path_default': self.ytdl_path_default,
            'ytdl_path': self.ytdl_path,
            'ytdl_update_dict': self.ytdl_update_dict,
            'ytdl_update_list': self.ytdl_update_list,
            'ytdl_update_current': self.ytdl_update_current,

            'ytdl_output_system_cmd_flag': self.ytdl_output_system_cmd_flag,
            'ytdl_output_stdout_flag': self.ytdl_output_stdout_flag,
            'ytdl_output_ignore_json_flag': self.ytdl_output_ignore_json_flag,
            'ytdl_output_ignore_progress_flag': \
            self.ytdl_output_ignore_progress_flag,
            'ytdl_output_stderr_flag': self.ytdl_output_stderr_flag,
            'ytdl_output_start_empty_flag': self.ytdl_output_start_empty_flag,
            'ytdl_output_show_summary_flag': \
            self.ytdl_output_show_summary_flag,

            'ytdl_write_system_cmd_flag': self.ytdl_write_system_cmd_flag,
            'ytdl_write_stdout_flag': self.ytdl_write_stdout_flag,
            'ytdl_write_ignore_json_flag': self.ytdl_write_ignore_json_flag,
            'ytdl_write_ignore_progress_flag': \
            self.ytdl_write_ignore_progress_flag,
            'ytdl_write_stderr_flag': self.ytdl_write_stderr_flag,

            'ytdl_write_verbose_flag': self.ytdl_write_verbose_flag,

            'refresh_output_videos_flag': self.refresh_output_videos_flag,
            'refresh_output_verbose_flag': self.refresh_output_verbose_flag,
            'refresh_moviepy_timeout': self.refresh_moviepy_timeout,

            'auto_clone_options_flag': self.auto_clone_options_flag,

            'disk_space_warn_flag': self.disk_space_warn_flag,
            'disk_space_warn_limit': self.disk_space_warn_limit,
            'disk_space_stop_flag': self.disk_space_stop_flag,
            'disk_space_stop_limit': self.disk_space_stop_limit,

            'ffmpeg_path': self.ffmpeg_path,

            'operation_limit_flag': self.operation_limit_flag,
            'operation_check_limit': self.operation_check_limit,
            'operation_download_limit': self.operation_download_limit,

            'scheduled_dl_mode': self.scheduled_dl_mode,
            'scheduled_dl_wait_hours': self.scheduled_dl_wait_hours,
            'scheduled_dl_last_time': self.scheduled_dl_last_time,

            'scheduled_check_mode': self.scheduled_check_mode,
            'scheduled_check_wait_hours': self.scheduled_check_wait_hours,
            'scheduled_check_last_time': self.scheduled_check_last_time,

            'scheduled_shutdown_flag': self.scheduled_shutdown_flag,

            'autostop_time_flag': self.autostop_time_flag,
            'autostop_time_value': self.autostop_time_value,
            'autostop_time_unit': self.autostop_time_unit,
            'autostop_videos_flag': self.autostop_videos_flag,
            'autostop_videos_value': self.autostop_videos_value,
            'autostop_size_flag': self.autostop_size_flag,
            'autostop_size_value': self.autostop_size_value,
            'autostop_size_unit': self.autostop_size_unit,

            'operation_auto_update_flag': self.operation_auto_update_flag,
            'operation_save_flag': self.operation_save_flag,
            'operation_dialogue_mode': self.operation_dialogue_mode,
            'operation_convert_mode': self.operation_convert_mode,
            'use_module_moviepy_flag': self.use_module_moviepy_flag,

            'dialogue_copy_clipboard_flag': self.dialogue_copy_clipboard_flag,
            'dialogue_keep_open_flag': self.dialogue_keep_open_flag,

            'allow_ytdl_archive_flag': self.allow_ytdl_archive_flag,
            'apply_json_timeout_flag': self.apply_json_timeout_flag,

            'ignore_child_process_exit_flag': \
            self.ignore_child_process_exit_flag,
            'ignore_http_404_error_flag': self.ignore_http_404_error_flag,
            'ignore_data_block_error_flag': self.ignore_data_block_error_flag,
            'ignore_merge_warning_flag': self.ignore_merge_warning_flag,
            'ignore_missing_format_error_flag': \
            self.ignore_missing_format_error_flag,
            'ignore_no_annotations_flag': self.ignore_no_annotations_flag,
            'ignore_no_subtitles_flag': self.ignore_no_subtitles_flag,

            'ignore_yt_copyright_flag': self.ignore_yt_copyright_flag,
            'ignore_yt_age_restrict_flag': self.ignore_yt_age_restrict_flag,
            'ignore_yt_uploader_deleted_flag': \
            self.ignore_yt_uploader_deleted_flag,

            'ignore_custom_msg_list': self.ignore_custom_msg_list,
            'ignore_custom_regex_flag': self.ignore_custom_regex_flag,

            'num_worker_default': self.num_worker_default,
            'num_worker_apply_flag': self.num_worker_apply_flag,

            'bandwidth_default': self.bandwidth_default,
            'bandwidth_apply_flag': self.bandwidth_apply_flag,

            'video_res_default': self.video_res_default,
            'video_res_apply_flag': self.video_res_apply_flag,

            'match_method': self.match_method,
            'match_first_chars': self.match_first_chars,
            'match_ignore_chars': self.match_ignore_chars,

            'auto_delete_flag': self.auto_delete_flag,
            'auto_delete_watched_flag': self.auto_delete_watched_flag,
            'auto_delete_days': self.auto_delete_days,

            'delete_on_shutdown_flag': self.delete_on_shutdown_flag,

            'complex_index_flag': self.complex_index_flag,
            'catalogue_mode': self.catalogue_mode,
            'catalogue_page_size': self.catalogue_page_size,

            'simple_options_flag': self.simple_options_flag,
        }

        # Try to save the file
        try:
            with open(config_file_path, 'w') as outfile:
                json.dump(json_dict, outfile, indent=4)

        except:
            self.disable_load_save()
            self.file_error_dialogue(
                'Failed to save the ' \
                + utils.upper_case_first(__main__.__packagename__) \
                + ' config file\n\nFile load/save has been disabled',
            )


    def load_db(self):

        """Called by self.start() and .switch_db().

        Loads the Tartube database file. If loading fails, disables all file
        loading/saving.

        Returns:

            True on success, False on failure

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 2214 load_db')

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
            self.main_win_obj.show_all()

        # Most main widgets are desensitised, until the database file has been
        #   loaded
        self.main_win_obj.sensitise_widgets_if_database(False)

        # Try to load the database file
        try:
            f = open(path, 'rb')
            load_dict = pickle.load(f)
            f.close()

        except:
            self.disable_load_save(
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
            self.disable_load_save(
                'Database file can\'t be read\nby this version of ' \
                + utils.upper_case_first(__main__.__packagename__),
            )

            return False

        # Before v1.3.099, self.data_dir and self.downloads_dir were different
        # If a /downloads directory exists, then the data directory is using
        #   the old structure
        old_flag = False
        if os.path.isdir(self.alt_downloads_dir):

            # Use the old location of self.downloads_dir
            old_flag = True
            self.downloads_dir = self.alt_downloads_dir
            # Move any database backup files to their new location
            self.move_backup_files()

        else:

            # Use the new location
            self.downloads_dir = self.data_dir

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

        # Update the loaded data for this version of Tartube
        self.update_db(version)

        # As of v1.3.099, some container names have become illegal. Replace any
        #   illegal names with legal ones
        if version <= 1003099:

            for old_name in self.media_name_dict.keys():
                if not self.check_container_name_is_legal(old_name):

                    dbid = self.media_name_dict[old_name]
                    media_data_obj = self.media_reg_dict[dbid]

                    # Generate a new name; the function returns None on failure
                    new_name = utils.find_available_name('downloads')
                    if new_name is not None:
                        self.rename_container_silently(
                            media_data_obj,
                            new_name,
                        )

        # If the old structure is being used, the user might try to manually
        #   copy the contents of the /downloads folder into the folder above
        # To prevent problems when that happens, preemptively rename any media
        #   data object called 'downloads'
        if old_flag and 'downloads' in self.media_name_dict:

            dbid = self.media_name_dict['downloads']
            media_data_obj = self.media_reg_dict[dbid]

            # Generate a new name; the function returns None on failure
            new_name = utils.find_available_name('downloads')
            if new_name is not None:
                self.rename_container_silently(media_data_obj, new_name)

        # Empty any temporary folders
        self.delete_temp_folders()

        # Auto-delete old downloaded videos
        self.auto_delete_old_videos()

        # If the debugging flag is set, hide all fixed (system) folders
        if self.debug_hide_folders_flag:
            self.fixed_all_folder.set_hidden_flag(True)
            self.fixed_fav_folder.set_hidden_flag(True)
            self.fixed_new_folder.set_hidden_flag(True)
            self.fixed_temp_folder.set_hidden_flag(True)
            self.fixed_misc_folder.set_hidden_flag(True)

        # Now that a database file has been loaded, most main window widgets
        #   can be sensitised...
        self.main_win_obj.sensitise_widgets_if_database(True)
        # ...and saving the database file is now allowed
        self.allow_db_save_flag = True

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
            utils.debug_time('app 2330 update_db')

        fixed_folder_list = [
            self.fixed_all_folder,
            self.fixed_new_folder,
            self.fixed_fav_folder,
        ]

        options_obj_list = [self.general_options_obj]
        for media_data_obj in self.media_reg_dict.values():
            if media_data_obj.options_obj is not None \
            and not media_data_obj.options_obj in options_obj_list:
                options_obj_list.append(media_data_obj.options_obj)

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
                    media_data_obj.reset_file_dir()

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

        if version < 6003:  # v0.6.003

            # This version fixes an issue in which deleting an individual video
            #   and then re-adding the same video, downloading it then deleting
            #   it a second time, messes up the parent container's count IVs
            # Nothing for it but to recalculate them all, just in case
            for dbid in self.media_name_dict.values():
                container_obj = self.media_reg_dict[dbid]

                vid_count = new_count = fav_count = dl_count = 0

                for child_obj in container_obj.child_list:
                    if isinstance(child_obj, media.Video):
                        vid_count += 1

                        if child_obj.new_flag:
                            new_count += 1

                        if child_obj.fav_flag:
                            fav_count += 1

                        if child_obj.dl_flag:
                            dl_count += 1

                container_obj.reset_counts(
                    vid_count,
                    new_count,
                    fav_count,
                    dl_count,
                )

        if version < 1000013:  # v1.0.013

            # This version adds nicknames to channels, playlists and folders
            for dbid in self.media_name_dict.values():
                container_obj = self.media_reg_dict[dbid]
                container_obj.nickname = container_obj.name

        if version < 1000031:  # v1.0.031

            # This version adds nicknames to videos. If the database is large,
            #   warn the user before continuing
            if self.media_reg_dict.len() > 1000:

                dialogue_win = self.dialogue_manager_obj.show_msg_dialogue(
                    utils.upper_case_first(__main__.__packagename__) \
                    + ' is applying an essential\ndatabase update.\n\nThis' \
                    + ' might take a few minutes,\nso please be patient.',
                    'info',
                    'ok',
                    self.main_win_obj,
                )

                dialogue_win.set_modal(True)

            for media_data_obj in self.media_reg_dict.values():
                if isinstance(media_data_obj, media.Video):

                    media_data_obj.nickname = media_data_obj.name

                    # If the video's JSON data has been saved, we can use that
                    #   to set the nickname
                    json_path = os.path.abspath(
                        os.path.join(
                            self.downloads_dir,
                            media_data_obj.file_dir,
                            media_data_obj.file_name + '.info.json',
                        ),
                    )

                    if os.path.isfile(json_path):
                        json_dict = self.file_manager_obj.load_json(json_path)
                        if 'title' in json_dict:
                            media_data_obj.nickname = json_dict['title']


        if version < 1001031:  # v1.1.031

            # This version adds the ability to disable checking/downloading for
            #   media data objects
            for dbid in self.media_name_dict.values():
                media_data_obj = self.media_reg_dict[dbid]
                media_data_obj.dl_disable_flag = False

        if version < 1001032:  # v1.1.032

            # This version adds video archiving. Archived videos cannot be
            #   auto-deleted
            for media_data_obj in self.media_reg_dict.values():
                if isinstance(media_data_obj, media.Video):
                    media_data_obj.archive_flag = False

        if version < 1001037:  # v1.1.037

            # This version adds alternative destination directories for a
            #   channel's/playlist's/folder's videos, thumbnails (etc)
            for dbid in self.media_name_dict.values():
                media_data_obj = self.media_reg_dict[dbid]
                media_data_obj.master_dbid = media_data_obj.dbid
                media_data_obj.slave_dbid_list = []

        if version < 1001045:  # v1.1.045

            # This version adds a new option to options.OptionsManager
            for options_obj in options_obj_list:
                options_obj.options_dict['use_fixed_folder'] = None

        if version < 1001060:  # v1.1.060

            # This version adds new options to options.OptionsManager
            for options_obj in options_obj_list:
                options_obj.options_dict['abort_on_error'] = False

                options_obj.options_dict['socket_timeout'] = ''
                options_obj.options_dict['source_address'] = ''
                options_obj.options_dict['force_ipv4'] = False
                options_obj.options_dict['force_ipv6'] = False

                options_obj.options_dict['geo_verification_proxy'] = ''
                options_obj.options_dict['geo_bypass'] = False
                options_obj.options_dict['no_geo_bypass'] = False
                options_obj.options_dict['geo_bypass_country'] = ''
                options_obj.options_dict['geo_bypass_ip_block'] = ''

                options_obj.options_dict['match_title_list'] = []
                options_obj.options_dict['reject_title_list'] = []

                options_obj.options_dict['date'] = ''
                options_obj.options_dict['date_before'] = ''
                options_obj.options_dict['date_after'] = ''
                options_obj.options_dict['min_views'] = 0
                options_obj.options_dict['max_views'] = 0
                options_obj.options_dict['match_filter'] = ''
                options_obj.options_dict['age_limit'] = ''
                options_obj.options_dict['include_ads'] = False

                options_obj.options_dict['playlist_reverse'] = False
                options_obj.options_dict['playlist_random'] = False
                options_obj.options_dict['prefer_ffmpeg'] = False
                options_obj.options_dict['external_downloader'] = ''
                options_obj.options_dict['external_arg_string'] = ''

                options_obj.options_dict['force_encoding'] = ''
                options_obj.options_dict['no_check_certificate'] = False
                options_obj.options_dict['prefer_insecure'] = False

                options_obj.options_dict['all_formats'] = False
                options_obj.options_dict['prefer_free_formats'] = False
                options_obj.options_dict['yt_skip_dash'] = False
                options_obj.options_dict['merge_output_format'] = ''

                options_obj.options_dict['subs_format'] = ''

                options_obj.options_dict['two_factor'] = ''
                options_obj.options_dict['net_rc'] = False

                options_obj.options_dict['recode_video'] = ''
                options_obj.options_dict['pp_args'] = ''
                options_obj.options_dict['fixup_policy'] = ''
                options_obj.options_dict['prefer_avconv'] = False
                options_obj.options_dict['prefer_ffmpeg'] = False

                options_obj.options_dict['write_annotations'] = True
                options_obj.options_dict['keep_annotations'] = False
                options_obj.options_dict['sim_keep_annotations'] = False

                # (Also rename one option)
                options_obj.options_dict['extract_audio'] \
                = options_obj.options_dict['to_audio']
                options_obj.options_dict.pop('to_audio')

        if version < 1003004:  # v1.3.004

            # The way that directories are stored in media.VideoObj.file_dir
            #   has changed. Reset those values for all video objects
            for media_data_obj in self.media_reg_dict.values():
                if isinstance(media_data_obj, media.Video):

                    media_data_obj.reset_file_dir()

        if version < 1003009:  # v1.3.009

            # In earlier versions,
            #   refresh.RefreshManager.refresh_from_filesystem() set a video's
            #   .name, but not its .nickname
            # The .refresh_from_filesystem() is already fixed, but we need to
            #   check every video in the database, and set its .nickname if
            #   not set
            for media_data_obj in self.media_reg_dict.values():
                if isinstance(media_data_obj, media.Video):
                    if (
                        media_data_obj.nickname is None \
                        or media_data_obj.nickname == self.default_video_name
                    ) and media_data_obj.name is not None \
                    and media_data_obj.name != self.default_video_name:
                        media_data_obj.nickname = media_data_obj.name

        if version < 1003017:  # v1.3.017

            for options_obj in options_obj_list:

                # In earlier versions, the 'prefer_ffmpeg' and
                #   'hls_prefer_ffmpeg' download options had been confused
                options_obj.options_dict['hls_prefer_ffmpeg'] = False

                # In earlier versions, MS Windows users could set the
                #   'prefer_ffmpeg' and 'prefer_avconv' options, even though
                #   the MS Windows installer does not provide AVConv. Reset
                #   both values
                options_obj.options_dict['prefer_ffmpeg'] = False
                options_obj.options_dict['prefer_avconv'] = False

                # In earlier versions, the download options 'video_format',
                #   'second_video_format' and/or 'third_video_format' could
                #   incorrectly be set to a sound format like 'mp3'. This is
                #   not the way youtube-dl-gui was supposed to implement its
                #   formats; remove them, if the user has specified them
                if not options_obj.options_dict['third_video_format'] \
                in formats.VIDEO_OPTION_DICT:
                    options_obj.options_dict['third_video_format'] = '0'

                if not options_obj.options_dict['second_video_format'] \
                in formats.VIDEO_OPTION_DICT:
                    options_obj.options_dict['second_video_format'] = '0'
                    if options_obj.options_dict['third_video_format'] != '0':
                        options_obj.options_dict['second_video_format'] \
                        = options_obj.options_dict['third_video_format']
                        options_obj.options_dict['third_video_format'] = '0'

                if not options_obj.options_dict['video_format'] \
                in formats.VIDEO_OPTION_DICT:
                    options_obj.options_dict['video_format'] = '0'
                    if options_obj.options_dict['second_video_format'] != '0':
                        options_obj.options_dict['video_format'] \
                        = options_obj.options_dict['second_video_format']
                        options_obj.options_dict['second_video_format'] \
                        = options_obj.options_dict['third_video_format']

        if version < 1003106:  # v1.3.106

            # This version adds a new option to options.OptionsManager
            for options_obj in options_obj_list:
                if options_obj.options_dict['subs_lang'] == '':
                    options_obj.options_dict['subs_lang_list'] = []
                else:
                    options_obj.options_dict['subs_lang_list'] \
                    = [ options_obj.options_dict['subs_lang'] ]

        if version < 1003110:  # v1.3.110

            # Before this version, the 'output_template' in
            #   options.OptionManager was completely broken, containing both
            #   the filepath to this file, and an '%(uploader)s string that
            #   broke the structure of Tartube's data directory
            # Reset the value if it seems to contain either
            for options_obj in options_obj_list:
                output_template = options_obj.options_dict['output_template']
                if re.search(sys.path[0], output_template) \
                or re.search('\%\(uploader\)s', output_template):
                    options_obj.options_dict['output_template'] \
                    = '%(title)s.%(ext)s'

        if version < 1003111:  # v1.3.111

            # In this version, formats.py.FILE_OUTPUT_NAME_DICT and
            #   .FILE_OUTPUT_CONVERT_DICT, so that the custom format's index
            #   is 0 (was 3)
            for options_obj in options_obj_list:
                output_format = options_obj.options_dict['output_format']
                if output_format == 3:
                    options_obj.options_dict['output_format'] = 0
                elif output_format < 3:
                    options_obj.options_dict['output_format'] \
                    = output_format + 1


    def save_db(self):

        """Called by self.start(), .stop(), .switch_db(),
        .download_manager_finished(), .update_manager_finished(),
        .refresh_manager_finished() and .on_menu_save_db().

        Saves the Tartube database file. If saving fails, disables all file
        loading/saving.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 2707 save_db')

        # Sanity check
        if self.current_manager_obj \
        or self.disable_load_save_flag \
        or not self.allow_db_save_flag:
            return

        # Prepare values
        utc = datetime.datetime.utcfromtimestamp(time.time())
        path = os.path.abspath(os.path.join(self.data_dir, self.db_file_name))
        bu_path = os.path.abspath(
            os.path.join(
                self.backup_dir,
                __main__.__packagename__ + '_BU.db',
            ),
        )
        temp_bu_path = os.path.abspath(
            os.path.join(
                self.backup_dir,
                __main__.__packagename__ + '_TEMP_BU.db',
            ),
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
                    + ' database file\n\n(Could not make a backup copy of' \
                    + ' the existing file)\n\nFile load/save has been' \
                    + ' disabled',
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
                    + '   ' + temp_bu_path \
                    + '\n\nFile load/save has been disabled',
                )

            else:
                return self.file_error_dialogue(
                    'Failed to save the ' \
                    + utils.upper_case_first(__main__.__packagename__) \
                    + ' database file\n\nFile load/save has been' \
                    + ' disabled',
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

                # (os.rename sometimes fails on external hard drives; this is
                #   safer)
                shutil.move(temp_bu_path, bu_path)

            elif self.db_backup_mode == 'daily':

                daily_bu_path = os.path.abspath(
                    os.path.join(
                        self.backup_dir,
                        __main__.__packagename__ + '_BU_' \
                        + str(utc.strftime('%Y_%m_%d')) + '.db',
                    ),
                )

                # Only make a new backup file once per day
                if not os.path.isfile(daily_bu_path):

                    if os.path.isfile(daily_bu_path):
                        os.remove(daily_bu_path)

                    shutil.move(temp_bu_path, daily_bu_path)

                else:

                    os.remove(temp_bu_path)

            elif self.db_backup_mode == 'always':

                always_bu_path = os.path.abspath(
                    os.path.join(
                        self.backup_dir,
                        __main__.__packagename__ + '_BU_' \
                        + str(utc.strftime('%Y_%m_%d_%H_%M_%S')) + '.db',
                    ),
                )

                if os.path.isfile(always_bu_path):
                    os.remove(always_bu_path)

                shutil.move(temp_bu_path, always_bu_path)

        # Saving a database file, in order to create a new file, is much like
        #   loading one: main window widgets can now be sensitised
        self.main_win_obj.sensitise_widgets_if_database(True)


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
            utils.debug_time('app 2857 switch_db')

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

        # Update IVs for the new location of the data directory
        self.data_dir = path
        self.downloads_dir = path
        self.alt_downloads_dir = os.path.abspath(
            os.path.join(path, 'downloads'),
        )
        self.backup_dir = os.path.abspath(os.path.join(path, '.backups'))
        self.temp_dir = os.path.abspath(os.path.join(path, '.temp'))
        self.temp_dl_dir = os.path.abspath(
            os.path.join(path, '.temp', 'downloads'),
        )

        # Before v1.3.099, self.data_dir and self.downloads_dir were different
        # If a /downloads directory exists, then the data directory is using
        #   the old structure
        if os.path.isdir(self.alt_downloads_dir):

            # Use the old location of self.downloads_dir
            self.downloads_dir = self.alt_downloads_dir

        else:

            # Use the new location
            self.downloads_dir = self.data_dir

#        # Save the config file now, to preserve the new location of the data
#        #   directory
#        self.save_config()

        # Any of those directories that don't exist should be created
        if not os.path.isdir(self.data_dir):
            # React to a 'Permission denied' error by asking the user what to
            #   do next. If necessary, shut down Tartube
            # The True argument means that the drive is unwriteable
            if not self.make_directory(self.data_dir):
                return False

        if not os.path.isdir(self.backup_dir):
            if not self.make_directory(self.backup_dir):
                return False

        # (The temporary data directory should be emptied, if it already
        #   exists)
        if os.path.isdir(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)

            except:
                if not self.make_directory(self.temp_dir):
                    return False
                else:
                    shutil.rmtree(self.temp_dir)

        if not os.path.isdir(self.temp_dir):
            if not self.make_directory(self.temp_dir):
                return self.main_win_obj.destroy()

        if not os.path.isdir(self.temp_dl_dir):
            if not self.make_directory(self.temp_dl_dir):
                return self.main_win_obj.destroy()

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

            # Save the config file, to preserve the new location of the data
            #   directory
            self.save_config()

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

            if not self.load_db():

                return False

            else:

                # Save the config file, to preserve the new location of the
                #   data directory
                self.save_config()
                return True


    def reset_db(self):

        """Called by self.switch_db().

        Resets media registry IVs, so that a new Tartube database file can be
        created.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 2960 reset_db')

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


    def auto_delete_old_videos(self):

        """Called by self.load_db().

        After loading the Tartube database, auto-delete any old downloaded
        videos (if auto-deletion is enabled)
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 3263 auto_delete_old_videos')

        if not self.auto_delete_flag:
            return

        # Calculate the system time before which any downloaded videos can be
        #   deleted
        time_limit = int(time.time()) - (self.auto_delete_days * 24 * 60 * 60)

        # Import a list of media data objects (as self.media_reg_dict will be
        #   modified during this operation)
        media_list = list(self.media_reg_dict.values())

        # Auto-delete any videos as required
        for media_data_obj in media_list:

            if isinstance(media_data_obj, media.Video) \
            and media_data_obj.dl_flag \
            and not media_data_obj.archive_flag \
            and media_data_obj.receive_time < time_limit \
            and (
                not self.auto_delete_watched_flag \
                or not media_data_obj.new_flag
            ):
                # Ddelete this video
                self.delete_video(media_data_obj, True, True, True)


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
            utils.debug_time('app 3313 convert_version')

        num_list = version.split('.')
        if len(num_list) != 3:
            return None
        else:
            return (int(num_list[0]) * 1000000) + (int(num_list[1]) * 1000) \
            + int(num_list[2])


    def create_system_folders(self):

        """Called by self.start() and .reset_db().

        Creates the fixed (system) media.Folder objects that can't be
        destroyed by the user.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 3119 create_system_folders')

        self.fixed_all_folder = self.add_folder(
            'All Videos',
            None,           # No parent folder
            False,          # Allow downloads
            True,           # Fixed (folder cannot be removed)
            True,           # Private
            True,           # Can only contain videos
            False,          # Not temporary
        )

        self.fixed_fav_folder = self.add_folder(
            'Favourite Videos',
            None,           # No parent folder
            False,          # Allow downloads
            True,           # Fixed (folder cannot be removed)
            True,           # Private
            True,           # Can only contain videos
            False,          # Not temporary
        )
        self.fixed_fav_folder.set_fav_flag(True)

        self.fixed_new_folder = self.add_folder(
            'New Videos',
            None,           # No parent folder
            False,          # Allow downloads
            True,           # Fixed (folder cannot be removed)
            True,           # Private
            True,           # Can only contain videos
            False,          # Not temporary
        )

        self.fixed_temp_folder = self.add_folder(
            'Temporary Videos',
            None,           # No parent folder
            False,          # Allow downloads
            True,           # Fixed (folder cannot be removed)
            False,          # Public
            False,          # Can contain any media data object
            True,           # Temporary
        )

        self.fixed_misc_folder = self.add_folder(
            'Unsorted Videos',
            None,           # No parent folder
            False,          # Allow downloads
            True,           # Fixed (folder cannot be removed)
            False,          # Public
            True,           # Can only contain videos
            False,          # Not temporary
        )


    def delete_temp_folders(self):

        """Called by self.load_db() and self.stop().

        Deletes the contents of any folders marked temporary, such as the
        'Temporary Videos' folder. (The folders themselves are not deleted).
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 3226 delete_temp_folders')

        # (Must compile a list of top-level container objects first, or Python
        #   will complain about the dictionary changing size)
        obj_list = []
        for dbid in self.media_name_dict.values():
            obj_list.append(self.media_reg_dict[dbid])

        for media_data_obj in obj_list:

            if isinstance(media_data_obj, media.Folder) \
            and media_data_obj.temp_flag:

                # Delete all child objects
                for child_obj in list(media_data_obj.child_list.copy()):
                    if isinstance(child_obj, media.Video):
                        self.delete_video(child_obj)
                    else:
                        self.delete_container(child_obj)

                # Remove files from the filesystem, leaving an empty directory
                dir_path = media_data_obj.get_dir(self)
                if os.path.isdir(dir_path):
                    shutil.rmtree(dir_path)

                os.makedirs(dir_path)


    def disable_load_save(self, error_msg=None):

        """Called by self.load_config(), .save_config(), load_db() and
        .save_db().

        After an error, disables loading/saving, and desensitises many widgets
        in the main window.

        Args:

            error_msg (str or None): An optional error message that can be#
                retrieved later, if required

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 3178 disable_load_save')

        # Ignore subsequent calls to this function; only the initial error
        #   is of interest
        if not self.disable_load_save_flag:

            self.disable_load_save_flag = True
            self.allow_db_save_flag = False
            self.disable_load_save_msg = error_msg

            if self.main_win_obj is not None:
                self.main_win_obj.sensitise_widgets_if_database(False)


    def file_error_dialogue(self, msg):

        """Called by self.load_config(), .save_config(), load_db() and
        .save_db().

        After a failure to load/save a file, display a dialogue window if the
        main window is open, or write to the terminal if not.

        Args:

            msg (string): The message to display

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 3200 file_error_dialogue')

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


    def make_directory(self, dir_path):

        """Called by self.start() and .switch_db().

        The call to os.makedirs() might fail with a 'Permission denied' error,
        meaning that the specified directory is unwriteable.

        Convenience function to intercept the error, and display a Tartube
        dialogue instead.

        Args:

            dir_path (str): The path to the directory to be created with a
                call to os.makedirs()

        Return values:

            True if the directory was created, False if not

        """

        try:
            os.makedirs(dir_path)
            return True

        except:

            # The True argument tells the dialogue window that it's an
            #   unwriteable directory
            dialogue_win = mainwin.MountDriveDialogue(self.main_win_obj, True)
            dialogue_win.run()
            available_flag = dialogue_win.available_flag
            dialogue_win.destroy()

            return available_flag


    def move_backup_files(self):

        """Called by self.load_db() and .switch_db().

        Before v1.3.099, Tartube's data directory used a different structure,
        with the database backup files stored in self.data_dir itself.

        After v1.3.099, they are stored in self.backup_dir.

        The calling function has detected that the old file structure is being
        used. As a convenience to the user, move all the backup files to their
        new location.
        """

        for filename in os.listdir(path=self.data_dir):
            if re.search(r'^tartube_BU_.*\.db$', filename):

                old_path = os.path.abspath(
                    os.path.join(self.data_dir, filename),
                )

                new_path = os.path.abspath(
                    os.path.join(self.backup_dir, filename),
                )

                shutil.move(old_path, new_path)


    def notify_user_of_data_dir(self):

        """Called by self.start().

        On MS Windows, tell the user that they must set the location of the
        Tartube data directory, self.data_dir. On other operating systems, ask
        the user if they want to use the default location, or choose a custom
        one.

        Return values:

            True to choose a custom location for the data directory, False to
                use the default location.

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 2996 notify_user_of_data_dir')

        if os.name == 'nt':

            # On MS Windows, Cygwin creates a Tartube data directory at
            #   C:\msys64\home\USERNAME\tartube-data, which is not very
            #   convenient. Force the user to nominate the directory they want
            script_name = utils.upper_case_first(__main__.__packagename__)
            dialogue_win = self.dialogue_manager_obj.show_msg_dialogue(
                'Welcome to ' + script_name + '!\n\nClick OK to create a' \
                + ' folder in which\n' + script_name + ' can store its' \
                + ' videos\n\nIf you have used ' + script_name \
                + ' before,\nyou can select an existing folder\ninstead of' \
                + ' creating a new one',
                'info',
                'ok',
                self.main_win_obj,
            )

            # Because of Gtk weirdness, the dialogue window isn't actually
            #   modal; but these lines at least make sure the dialogue window
            #   is visible above the file chooser dialogue that
            #   self.prompt_user_for_data_dir() is about to create
            dialogue_win.set_transient_for(self.main_win_obj)
            dialogue_win.set_modal(True)

            return True

        else:

            # On Linux/BSD, offer the user a choice between using the default
            #   data directory specified by self.data_dir, or specifying their
            #   own data directory
            dialogue_win = mainwin.SetDirectoryDialogue(
                self.main_win_obj,
                self.data_dir,
            )

            response = dialogue_win.run()

            # Retrieve user choices from the dialogue window, before destroying
            #   it
            custom_flag = False
            if response == Gtk.ResponseType.OK \
            and dialogue_win.button2.get_active():
                custom_flag = True

            dialogue_win.destroy()

            return custom_flag


    def prompt_user_for_data_dir(self):

        """Called by self.start(), immediately after a call to
        self.notify_user_of_data_dir().

        Prompt the user for the location of a new data directory.

        Return values:

            True if the user selects a location, False if they do not.

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 3062 prompt_user_for_data_dir')

        script_name = utils.upper_case_first(__main__.__packagename__)

        if os.name == 'nt':
            folder = 'folder'
        else:
            folder = 'directory'

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
        if response == Gtk.ResponseType.OK:

            # Location selected; the remaining code in self.start() will
            #   create the data directory, if necessary
            return True

        else:

            # Location not selected. Tartube will now shut down
            return False


    # (Download/Update/Refresh operations)


    def download_manager_start(self, force_sim_flag=False, \
    automatic_flag=False, media_data_list=[]):

        """Called by self.update_manager_finished(), .start() and
        .script_slow_timer_callback(), and by callbacks in .on_menu_check_all()
        and .on_menu_download_all().

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

            force_sim_flag (bool): True if playlists/channels should just be
                checked for new videos, without downloading anything. False if
                videos should be downloaded (or not) depending on each media
                data object's .dl_sim_flag IV

            automatic_flag (bool): True when called by self.start() or
                self.script_slow_timer_callback(). If the download operation
                does not start, no dialogue window is displayed (as it normally
                would be)

            media_data_list (list): List of media.Video, media.Channel,
                media.Playlist and/or media.Folder objects. If not an empty
                list, only those media data objects and their descendants are
                checked/downloaded. If an empty list, all media data objects
                are checked/downloaded

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 3366 download_manager_start')

        if self.current_manager_obj:

            # Download, update or refresh operation already in progress
            if not automatic_flag:
                self.system_error(
                    101,
                    'Download, update or refresh operation already in' \
                    + ' progress',
                )

            return

        elif self.main_win_obj.config_win_list:

            # Download operation is not allowed when a configuration window is
            #   open
            if not automatic_flag:
                self.dialogue_manager_obj.show_msg_dialogue(
                    'A download operation cannot start\nif one or more' \
                    + ' configuration\nwindows are still open',
                    'error',
                    'ok',
                )

            return

        # If the device containing self.data_dir is running low on space,
        #   warn the user before proceeding
        disk_space = utils.disk_get_free_space(self.data_dir)
        total_space = utils.disk_get_total_space(self.data_dir)

        if (
            self.disk_space_stop_flag \
            and self.disk_space_stop_limit != 0 \
            and disk_space <= self.disk_space_stop_limit
        ) or disk_space < self.disk_space_abs_limit:

            # Refuse to proceed with the operation
            if not automatic_flag:
                self.dialogue_manager_obj.show_msg_dialogue(
                    'You only have ' + str(disk_space) + ' / ' \
                    + str(total_space) + 'Mb\nremaining on your device',
                    'error',
                    'ok',
                )

            return

        elif self.disk_space_warn_flag \
        and self.disk_space_warn_limit != 0 \
        and disk_space <= self.disk_space_warn_limit:

            if automatic_flag:

                # Don't perform a schedules download operation if disk space is
                #   below the limit at which a warning would normally be issued
                return

            else:

                # Warn the user that their free disk space is running low, and
                #   get confirmation before starting the download operation
                self.dialogue_manager_obj.show_msg_dialogue(
                    'You only have ' + str(disk_space) + ' / ' \
                    + str(total_space) + 'Mb\nremaining on your device.' \
                    + '\n\nAre you sure you want to\ncontinue?',
                    'question',
                    'yes-no',
                    None,                   # Parent window is main window
                    # Arguments passed directly to .download_manager_continue()
                    {
                        'yes': 'download_manager_continue',
                        'data': [
                            force_sim_flag,
                            automatic_flag,
                            media_data_list,
                        ],
                    },
                )

        else:

            # Start the download operation immediately
            self.download_manager_continue(
                [force_sim_flag, automatic_flag, media_data_list],
            )


    def download_manager_continue(self, arg_list):

        """Called by dialogue.MessageDialogue.on_clicked() or by
        self.download_manager_start() directly.

        Having obtained confirmation from the user (if required), start the
        download operation.

        Args:

            arg_list (list): List of arguments originally supplied to
                self.download_manager_start(). A list in the form

                    [ force_sim_flag, automatic_flag, media_data_list ]

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 3474 download_manager_continue')

        # Extract arguments from arg_list
        force_sim_flag = arg_list.pop(0)
        automatic_flag = arg_list.pop(0)
        media_data_list = arg_list.pop(0)

        # The media data registry consists of a collection of media data
        #   objects (media.Video, media.Channel, media.Playlist and
        #   media.Folder)
        # If a list of media data objects was specified by the calling
        #   function, those media data object and all of their descendants are
        #   are assigned a downloads.DownloadItem object
        # Otherwise, all media data objects are assigned a
        #   downloads.DownloadItem object
        # Those downloads.DownloadItem objects are collectively stored in a
        #   downloads.DownloadList object
        download_list_obj = downloads.DownloadList(self, media_data_list)
        if not download_list_obj.download_item_list:

            if not automatic_flag:
                if force_sim_flag:
                    msg = 'There is nothing to check!'
                else:
                    msg = 'There is nothing to download!'

                self.dialogue_manager_obj.show_msg_dialogue(msg, 'error', 'ok')

            return

        # If the flag is set, do an update operation before starting the
        #   download operation
        if self.operation_auto_update_flag and not self.operation_waiting_flag:

            # The False argument means 'install youtube-dl, not FFmpeg'
            self.update_manager_start(False)
            # These IVs tells self.update_manager_finished to start a download
            #   operation
            self.operation_waiting_flag = True
            self.operation_waiting_sim_flag = force_sim_flag
            self.operation_waiting_obj_list = media_data_list
            return

        # For the benefit of future scheduled download operations, set the
        #   time at which this operation began
        if not media_data_list:
            if not force_sim_flag:
                self.scheduled_dl_last_time = int(time.time())
            else:
                self.scheduled_check_last_time = int(time.time())

        # If Tartube should shut down after this download operation, set a
        #   flag that self.download_manager_finished() can check
        if automatic_flag:
            if self.scheduled_shutdown_flag:
                self.halt_after_operation_flag = True
            else:
                self.no_dialogue_this_time_flag = True

        # During a download operation, show a progress bar in the Videos Tab
        self.main_win_obj.show_progress_bar(force_sim_flag)
        # Reset the Progress List
        self.main_win_obj.progress_list_reset()
        # Reset the Results List
        self.main_win_obj.results_list_reset()
        # Reset the Output Tab
        self.main_win_obj.output_tab_reset_pages()
        # Initialise the Progress List with one row for each media data object
        #   in the downloads.DownloadList object
        self.main_win_obj.progress_list_init(download_list_obj)
        # (De)sensitise other widgets, as appropriate
        self.main_win_obj.sensitise_operation_widgets(False)
        # Make the widget changes visible
        self.main_win_obj.show_all()

        # During a download operation, a GObject timer runs, so that the
        #   Progress Tab and Output Tab can be updated at regular intervals
        # There is also a delay between the instant at which youtube-dl
        #   reports a video file has been downloaded, and the instant at which
        #   it appears in the filesystem. The timer checks for newly-existing
        #   files at regular intervals, too
        # Create the timer
        self.dl_timer_id = GObject.timeout_add(
            self.dl_timer_time,
            self.dl_timer_callback,
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

        # Update the status icon in the system tray
        self.status_icon_obj.update_icon()


    def download_manager_halt_timer(self):

        """Called by downloads.DownloadManager.run() when that function has
        finished.

        During a download operation, a GObject timer was running. Let it
        continue running for a few seconds more.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 3585 download_manager_halt_timer')

        if self.dl_timer_id:
            self.dl_timer_check_time \
            = int(time.time()) + self.dl_timer_final_time


    def download_manager_finished(self):

        """Called by self.dl_timer_callback() and
        downloads.DownloadManager.run().

        The download operation has finished, so update IVs and main window
        widgets.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 3602 download_manager_finished')

        # Get the time taken by the download operation, so we can convert it
        #   into a nice string below (e.g. '05:15')
        # For refresh operations, RefreshManager.stop_time() might not have
        #   been set at this point (for some reason), so we need to check for
        #   the equivalent problem
        if self.download_manager_obj.stop_time is not None:
            time_num = int(
                self.download_manager_obj.stop_time \
                - self.download_manager_obj.start_time
            )
        else:
            time_num = int(time.time() - self.download_manager_obj.start_time)

        # Any code can check whether a download/update/refresh operation is in
        #   progress, or not, by checking this IV
        self.current_manager_obj = None
        self.download_manager_obj = None

        # Stop the timer and reset IVs
        GObject.source_remove(self.dl_timer_id)
        self.dl_timer_id = None
        self.dl_timer_check_time = None
        # (All videos marked to be launched in the system's default media
        #   player should have been launched already, but just to be safe,
        #   empty this list)
        self.watch_after_dl_list = []

        # After a download operation, save files, if allowed
        if self.operation_save_flag:
            self.save_config()
            self.save_db()

        # After a download operation, update the status icon in the system tray
        self.status_icon_obj.update_icon()
        # Remove the progress bar in the Videos Tab
        self.main_win_obj.hide_progress_bar()
        # (De)sensitise other widgets, as appropriate
        self.main_win_obj.sensitise_operation_widgets(True)
        # Make the widget changes visible (not necessary if the main window has
        #   been closed to the system tray)
        if self.main_win_obj.is_visible():
            self.main_win_obj.show_all()

        # Reset operation IVs
        self.operation_halted_flag = False

        # If updates to the Video Index were disabled because of Gtk issues,
        #   we must now redraw the Video Index and Video Catalogue from
        #   scratch
        if self.gtk_broken_flag or self.gtk_emulate_broken_flag:
            self.main_win_obj.video_index_reset()
            self.main_win_obj.video_catalogue_reset()
            self.main_win_obj.video_index_populate()

            current_container = self.main_win_obj.video_index_current
            if current_container and current_container in self.media_name_dict:
                dbid = self.media_name_dict[current_container]
                self.main_win_obj.video_index_select_row(
                    self.media_reg_dict[dbid],
                )

        # If the youtube-dl archive file was temporarily renamed to enable a
        #   video to be re-downloaded (by
        #   mainwin.MainWin.on_video_catalogue_re_download() ), restore the
        #   archive file's original name
        self.reset_backup_archive()

        # If Tartube is due to shut down, then shut it down
        if self.halt_after_operation_flag:
            self.stop_continue()

        # Otherwise, show a dialogue window or desktop notification, if allowed
        elif not self.no_dialogue_this_time_flag:

            if not self.operation_halted_flag:
                msg = 'Download operation complete'
            else:
                msg = 'Download operation halted'

            if time_num >= 10:
                msg += '\n\nTime taken: ' \
                + utils.convert_seconds_to_string(time_num, True)

            if self.operation_dialogue_mode == 'dialogue':
                self.dialogue_manager_obj.show_msg_dialogue(msg, 'info', 'ok')
            elif self.operation_dialogue_mode == 'desktop':
                self.main_win_obj.notify_desktop(None, msg)

        # In any case, reset those IVs
        self.halt_after_operation_flag = False
        self.no_dialogue_this_time_flag = False


    def update_manager_start(self, ffmpeg_flag=False):

        """Called by self.download_manager_start() or by callbacks in
        self.on_menu_install_ffmpeg() and .on_menu_update_ytdl().

        Initiates an update operation to do one of two jobs:

        1. Install FFmpeg (on MS Windows only)

        2. Install youtube-dl, or update it to its most recent version.

        Creates a new updates.UpdateManager object to handle the update
        operation. When the operation is complete,
        self.update_manager_finished() is called.

        Args:

            ffmpeg_flag (bool): If True, install FFmpeg (on MS Windows only).
                If False (or None), installs/updates youtube-dl

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 3720 update_manager_start')

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

        elif __main__.__debian_install_flag__:
            # Update operation is disabled in the Debian package. It should not
            #   be possible to call this function, but we'll show an error
            #   message anyway
            return self.system_error(
                103,
                'Update operations are disabled in this version of ' \
                + utils.upper_case_first(__main__.__packagename__),
            )

        elif ffmpeg_flag and os.name != 'nt':
            # The Update operation can only install FFmpeg on the MS Windows
            #   installation of Tartube. It should not be possible to call this
            #   function, but we'll show an error message anyway
            return self.system_error(
                134,
                'Update operation cannot install FFmpeg on your operating' \
                + ' system',
            )

        # During an update operation, certain widgets are modified and/or
        #   desensitised
        self.main_win_obj.output_tab_reset_pages()

        self.main_win_obj.modify_widgets_in_update_operation(
            False,
            ffmpeg_flag,
        )

        # During an update operation, a GObject timer runs, so that the Output
        #   Tab can be updated at regular intervals
        # Create the timer
        self.update_timer_id = GObject.timeout_add(
            self.update_timer_time,
            self.update_timer_callback,
        )

        # Initiate the update operation. Any code can check whether a
        #   download, update or refresh operation is in progress, or not, by
        #   checking this IV
        self.current_manager_obj = updates.UpdateManager(self, ffmpeg_flag)
        self.update_manager_obj = self.current_manager_obj

        # Update the status icon in the system tray
        self.status_icon_obj.update_icon()


    def update_manager_halt_timer(self):

        """Called by updates.UpdateManager.install_ffmpeg() or
        .install_ytdl() when those functions have finished.

        During an update operation, a GObject timer was running. Let it
        continue running for a few seconds more.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 3798 update_manager_halt_timer')

        if self.update_timer_id:
            self.update_timer_check_time \
            = int(time.time()) + self.update_timer_final_time


    def update_manager_finished(self):

        """Called by self.update_timer_callback().

        The update operation has finished, so update IVs and main window
        widgets.

        Args:

            success_flag (True or False): True if the update operation
                succeeded, False if not

            ytdl_version (string): When installing/updating youtube-dl, set to
                the new youtube-dl version number, if the update manager was
                able to capture it. Otherwise set to None

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 3824 update_manager_finished')

        # Import IVs from updates.UpdateManager, before it is destroyed
        ffmpeg_flag = self.update_manager_obj.ffmpeg_flag
        success_flag = self.update_manager_obj.success_flag
        ytdl_version = self.update_manager_obj.ytdl_version

        # Any code can check whether a download/update/refresh operation is in
        #   progress, or not, by checking this IV
        self.current_manager_obj = None
        self.update_manager_obj = None

        # Stop the timer and reset IVs
        GObject.source_remove(self.update_timer_id)
        self.update_timer_id = None
        self.update_timer_check_time = None

        # After an update operation, save files, if allowed
        if self.operation_save_flag:
            self.save_config()
            self.save_db()

        # During an update operation, certain widgets are modified and/or
        #   desensitised; restore them to their original state
        self.main_win_obj.modify_widgets_in_update_operation(True)
        # Update the status icon in the system tray
        self.status_icon_obj.update_icon()

        # Then show a dialogue window/desktop notification, if allowed (and if
        #   a download operation is not waiting to start)
        if self.operation_dialogue_mode != 'default' \
        and not self.operation_waiting_flag:

            if ffmpeg_flag:

                if not success_flag:
                    msg = 'Installation failed'
                else:
                    msg = 'Installation complete'

            else:
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

            if self.operation_dialogue_mode == 'dialogue':
                self.dialogue_manager_obj.show_msg_dialogue(msg, 'info', 'ok')
            elif self.operation_dialogue_mode == 'desktop':
                self.main_win_obj.notify_desktop(None, msg)

        # Reset operation IVs
        self.operation_halted_flag = False

        # If a download operation is waiting to start, start it
        if self.operation_waiting_flag:
            self.download_manager_continue(
                [
                    self.operation_waiting_sim_flag,
                    False,
                    self.operation_waiting_list,
                ],
            )

            # Reset those IVs, ready for any future download operations
            self.operation_waiting_flag = False
            self.operation_waiting_sim_flag = False
            self.operation_waiting_list = []


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
            utils.debug_time('app 3922 refresh_manager_start')

        if self.current_manager_obj:
            # Download, update or refresh operation already in progress
            return self.system_error(
                104,
                'Download, update or refresh operation already in progress',
            )

        elif media_data_obj is not None \
        and isinstance(media_data_obj, media.Video):
            return self.system_error(
                105,
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

        # The user might not be aware of what a refresh operation is, or the
        #   effect it might have on Tartube's database
        # Warn them, and give them the opportunity to back out
        if os.name == 'nt':
            folder = 'folder'
        else:
            folder = 'directory'

        if not media_data_obj:
            string = 'click\nthe \'Check all\' button in the main window.\n\n'
        elif isinstance(media_data_obj, media.Channel):
            string = '\nright-click the channel and select \'Check channel\'' \
            + '.\n\n'
        elif isinstance(media_data_obj, media.Playlist):
            string = '\nright-click the playlist and select \'Check' \
            + ' playlist\'.\n\n'
        else:
            string = '\nright-click the folder and select \'Check folder\'' \
            + '.\n\n'

        self.dialogue_manager_obj.show_msg_dialogue(
            'During a refresh operation, ' \
            + utils.upper_case_first(__main__.__packagename__) \
            + ' analyses its data\n' + folder + ', looking for videos that' \
            + ' haven\'t yet been\nadded to its database.\n\n' \
            + 'You only need to perform a refresh operation if you\nhave' \
            + ' manually copied videos into ' \
            + utils.upper_case_first(__main__.__packagename__) \
            + '\'s data\n' + folder + '.\n\n' \
            + 'Before starting a refresh operation, you should ' + string \
            + 'Are you sure you want to procede with the refresh\noperation?',
            'question',
            'yes-no',
            None,                   # Parent window is main window
            # Arguments passed directly to .move_container_to_top_continue()
            {
                'yes': 'refresh_manager_continue',
                'data': media_data_obj,
            },
        )


    def refresh_manager_continue(self, media_data_obj=None):

        """Called by dialogue.MessageDialogue.on_clicked().

        Having obtained confirmation from the user, start the refresh
        operation.

        Args:

            media_data_obj (media.Channel, media.Playlist, media.Folder or
                None): If specified, only this channel/playlist/folder is
                refreshed. If not specified, the entire media registry is
                refreshed

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 4009 refresh_manager_continue')

        # Reset the Output Tab
        self.main_win_obj.output_tab_reset_pages()
        # During a refresh operation, certain widgets are modified and/or
        #   desensitised
        self.main_win_obj.modify_widgets_in_refresh_operation(False)

        # During a refresh operation, a GObject timer runs, so that the Output
        #   Tab can be updated at regular intervals
        # Create the timer
        self.refresh_timer_id = GObject.timeout_add(
            self.refresh_timer_time,
            self.refresh_timer_callback,
        )

        # Initiate the refresh operation. Any code can check whether a
        #   download, update or refresh operation is in progress, or not, by
        #   checking this IV
        self.current_manager_obj = refresh.RefreshManager(self, media_data_obj)
        self.refresh_manager_obj = self.current_manager_obj

        # Update the status icon in the system tray
        self.status_icon_obj.update_icon()


    def refresh_manager_halt_timer(self):

        """Called by refresh.RefreshManager.run() when that function has
        finished.

        During a refresh operation, a GObject timer was running. Let it
        continue running for a few seconds more.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 4045 refresh_manager_halt_timer')

        if self.refresh_timer_id:
            self.refresh_timer_check_time \
            = int(time.time()) + self.refresh_timer_final_time


    def refresh_manager_finished(self):

        """Called by self.refresh_timer_callback().

        The refresh operation has finished, so update IVs and main window
        widgets.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 4061 refresh_manager_finished')

        # Get the time taken by the download operation, so we can convert it
        #   into a nice string below (e.g. '05:15')
        # For some reason, RefreshManager.stop_time() might not be set, so we
        #   need to check for that
        if self.refresh_manager_obj.stop_time is not None:
            time_num = int(
                self.refresh_manager_obj.stop_time \
                - self.refresh_manager_obj.start_time
            )
        else:
            time_num = int(time.time() - self.refresh_manager_obj.start_time)

        # Any code can check whether a download/update/refresh operation is in
        #   progress, or not, by checking this IV
        self.current_manager_obj = None
        self.refresh_manager_obj = None

        # Stop the timer and reset IVs
        GObject.source_remove(self.refresh_timer_id)
        self.refresh_timer_id = None
        # Any remanining messages generated by refresh.RefreshManager should be
        #   shown in the Output Tab immediately
        self.main_win_obj.output_tab_update_pages()
        # Update the status icon in the system tray
        self.status_icon_obj.update_icon()

        # After a refresh operation, save files, if allowed
        if self.operation_save_flag:
            self.save_config()
            self.save_db()

        # During a refresh operation, certain widgets are modified and/or
        #   desensitised; restore them to their original state
        self.main_win_obj.modify_widgets_in_refresh_operation(True)

        # If updates to the Video Index were disabled because of Gtk issues,
        #   we must now redraw the Video Index and Video Catalogue from
        #   scratch
        if self.gtk_broken_flag or self.gtk_emulate_broken_flag:
            self.main_win_obj.video_index_reset()
            self.main_win_obj.video_catalogue_reset()
            self.main_win_obj.video_index_populate()

        # Then show a dialogue window/desktop notification, if allowed
        if self.operation_dialogue_mode != 'default':

            if not self.operation_halted_flag:
                msg = 'Refresh operation complete'
            else:
                msg = 'Refresh operation halted'

            if time_num >= 10:
                msg += '\n\nTime taken: ' \
                + utils.convert_seconds_to_string(time_num, True)

            if self.operation_dialogue_mode == 'dialogue':
                self.dialogue_manager_obj.show_msg_dialogue(msg, 'info', 'ok')
            elif self.operation_dialogue_mode == 'desktop':
                self.main_win_obj.notify_desktop(None, msg)

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
            utils.debug_time('app 4165 create_video_from_download')

        # The downloads.DownloadItem handles a download for a video, a channel
        #   or a playlist
        media_data_obj = download_item_obj.media_data_obj

        if isinstance(media_data_obj, media.Video):

            # The downloads.DownloadItem object is handling a single video
            video_obj = media_data_obj
            # If the video was added manually (for example, using the 'Add
            #   videos' button), then its filepath won't be set yet
            if not video_obj.file_dir:
                video_obj.set_file(filename, extension)

        else:

            # The downloads.DownloadItem object is handling a channel or
            #   playlist
            # Does a media.Video object already exist?
            video_obj = None
            for child_obj in media_data_obj.child_list:

                child_file_dir = None
                if child_obj.file_dir is not None:
                    child_file_dir = os.path.abspath(
                        os.path.join(
                            self.downloads_dir,
                            child_obj.file_dir,
                        ),
                    )

                if isinstance(child_obj, media.Video) \
                and child_file_dir \
                and child_file_dir == dir_path \
                and child_obj.file_name \
                and child_obj.file_name == filename:
                    video_obj = child_obj

            if video_obj is None:

                # Create a new media data object for the video
                options_manager_obj = download_item_obj.options_manager_obj
                override_name \
                = options_manager_obj.options_dict['use_fixed_folder']
                if override_name is not None \
                and override_name in self.media_name_dict:

                    other_dbid = self.media_name_dict[override_name]
                    other_parent_obj = self.media_reg_dict[other_dbid]

                    video_obj = self.add_video(
                        other_parent_obj,
                        None,
                        False,
                        no_sort_flag,
                    )

                else:
                    video_obj = self.add_video(
                        media_data_obj,
                        None,
                        False,
                        no_sort_flag,
                    )

                # Since we have them to hand, set the video's file path IVs
                #   immediately
                video_obj.set_file(filename, extension)

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


    def convert_video_from_download(self, container_obj, options_manager_obj,
    dir_path, filename, extension, no_sort_flag=False):

        """Called downloads.VideoDownloader.confirm_new_video() and
        .confirm_sim_video().

        A modified version of self.create_video_from_download, called when
        youtube-dl is about to download a channel or playlist into a
        media.Video object.

        Args:

            container_obj (media.Folder): The folder into which a replacement
                media.Video object is to be created

            options_manager_obj (options.OptionsManager): The download options
                for this media data object

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
            utils.debug_time('app 4166 convert_video_from_download')

        # Does the container object already contain this video?
        video_obj = None
        for child_obj in container_obj.child_list:

            child_file_dir = None
            if child_obj.file_dir is not None:
                child_file_dir = os.path.abspath(
                    os.path.join(
                        self.downloads_dir,
                        child_obj.file_dir,
                       ),
                )

            if isinstance(child_obj, media.Video) \
            and child_file_dir \
            and child_file_dir == dir_path \
            and child_obj.file_name \
            and child_obj.file_name == filename:
                video_obj = child_obj

        if video_obj is None:

            # Create a new media data object for the video
            override_name \
            = options_manager_obj.options_dict['use_fixed_folder']
            if override_name is not None \
            and override_name in self.media_name_dict:

                other_dbid = self.media_name_dict[override_name]
                other_container_obj = self.media_reg_dict[other_dbid]

                video_obj = self.add_video(
                    other_container_obj,
                    None,
                    False,
                    no_sort_flag,
                )

            else:
                video_obj = self.add_video(
                    container_obj,
                    None,
                    False,
                    no_sort_flag,
                )

            # Since we have them to hand, set the video's file path IVs
            #   immediately
            video_obj.set_file(filename, extension)

        return video_obj


    def announce_video_download(self, download_item_obj, video_obj, \
    keep_description=None, keep_info=None, keep_annotations=None,
    keep_thumbnail=None):

        """Called by downloads.VideoDownloader.confirm_new_video(),
        .confirm_old_video() and .confirm_sim_video().

        Updates the main window.

        Args:

            download_item_obj (downloads.DownloadItem): The download item
                object describing the URL from which youtube-dl should download
                video(s).

            video_obj (media.Video): The video object for the downloaded video

            keep_description (True, False, None):
            keep_info (True, False, None):
            keep_annotations (True, False, None):
            keep_thumbnail (True, False, None):
                Settings from the options.OptionsManager object used to
                    download the video (set to 'None' for a simulated download)

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 4273 announce_video_download')

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
            keep_annotations,
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
                'keep_description', 'keep_info', 'keep_annotations',
                    'keep_thumbnail': flags from the options.OptionsManager
                    object used for to download the video (not added to the
                    dictionary at all for simulated downloads)

            mkv_flag (True or False): If the warning 'Requested formats are
                incompatible for merge and will be merged into mkv' has been
                seen, the calling function has found an .mkv file rather than
                the .mp4 file it was expecting, and has set this flag to True

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 4328 update_video_when_file_found')

        # Only set the .name IV if the video is currently unnamed
        if video_obj.name == self.default_video_name:
            video_obj.set_name(video_obj.file_name)
            # (The video's title, stored in the .nickname IV, will be updated
            #   from the JSON data in a momemnt)
            video_obj.set_nickname(video_obj.file_name)

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

        # Delete the description, JSON, annotations and thumbnail files, if
        #   required to do so
        if 'keep_description' in temp_dict \
        and not temp_dict['keep_description']:

            old_path = os.path.abspath(
                os.path.join(
                    self.downloads_dir,
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
                    self.downloads_dir,
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

        if 'keep_annotations' in temp_dict \
        and not temp_dict['keep_annotations']:

            old_path = os.path.abspath(
                os.path.join(
                    self.downloads_dir,
                    video_obj.file_dir,
                    video_obj.file_name + '.annotations.xml',
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

        # Register the video's size with the download manager, so that disk
        #   space limits can be applied, if required
        if self.download_manager_obj and video_obj.dl_flag:
            self.download_manager_obj.register_video_size(video_obj.file_size)

        # If required, launch this video in the system's default media player
        if video_obj in self.watch_after_dl_list:

            self.watch_after_dl_list.remove(video_obj)
            self.watch_video_in_player(video_obj)
            self.mark_video_new(video_obj, False)


    def announce_video_clone(self, video_obj):

        """Called by downloads.VideoDownloader.confirm_old_video().

        This is a modified version of self.update_video_when_file_found(),
        called when a channel/playlist/folder is using an alternative
        download destination for its videos (in which case,
        self.update_video_when_file_found() can't be called).

        Args:

            video_obj (media.Video): The video which already exists on the
                user's filesystem (in the alternative download destination)

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 4446 announce_video_clone')

        video_path = os.path.abspath(
            os.path.join(
                self.downloads_dir,
                video_obj.file_dir,
                video_obj.file_name + video_obj.file_ext,
            )
        )

        # Only set the .name IV if the video is currently unnamed
        if video_obj.name == self.default_video_name:
            video_obj.set_name(video_obj.file_name)
            # (The video's title, stored in the .nickname IV, will be updated
            #   from the JSON data in a momemnt)
            video_obj.set_nickname(video_obj.file_name)

        # Set the file size
        video_obj.set_file_size(os.path.getsize(video_path))

        # If the JSON file was downloaded, we can extract video statistics from
        #   it
        self.update_video_from_json(video_obj)

        # For any of those statistics that haven't been set (because the JSON
        #   file was missing or didn't contain the right statistics), set them
        #   directly
        self.update_video_from_filesystem(video_obj, video_path)

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
            utils.debug_time('app 4494 update_video_from_json')

        json_path = os.path.abspath(
            os.path.join(
                self.downloads_dir,
                video_obj.file_dir,
                video_obj.file_name + '.info.json',
            ),
        )

        if os.path.isfile(json_path):

            json_dict = self.file_manager_obj.load_json(json_path)

            if 'title' in json_dict:
                video_obj.set_nickname(json_dict['title'])

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
            utils.debug_time('app 4548 update_video_from_filesystem')

        if video_obj.upload_time is None:
            video_obj.set_upload_time(os.path.getmtime(video_path))

        if video_obj.duration is None \
        and HAVE_MOVIEPY_FLAG \
        and self.use_module_moviepy_flag:

#            try:
#                clip = moviepy.editor.VideoFileClip(video_path)
#                video_obj.set_duration(clip.duration)
#            except:
#                self.system_error(
#                    132,
#                    '\'' + video_obj.parent_obj.name + '\': moviepy module' \
#                    + 'failed to fetch duration of video \'' \
#                    + video_obj.name + '\'',
#                )
            # v1.2.040 - When the video file is corrupted, moviepy freezes
            #   indefinitely
            # Instead, let's try placing the operation inside a thread
            #   (unless the user has specified a timeout of zero; in which
            #   case, don't use a thread and let moviepy freeze indefinitely)
            if not self.refresh_moviepy_timeout:

                clip = moviepy.editor.VideoFileClip(video_path)
                video_obj.set_duration(clip.duration)

            else:

                this_thread = threading.Thread(
                    target=self.set_duration_from_moviepy,
                    args=(video_obj, video_path,),
                )

                this_thread.daemon = True
                this_thread.start()
                this_thread.join(self.refresh_moviepy_timeout)
                if this_thread.is_alive():
                    self.system_error(
                        132,
                        '\'' + video_obj.parent_obj.name \
                        + '\': moviepy module' \
                        + 'failed to fetch duration of video \'' \
                        + video_obj.name + '\'',
                    )

        # (Can't set the video source directly)

        if video_obj.descrip is None:
            video_obj.read_video_descrip(
                self,
                self.main_win_obj.descrip_line_max_len,
            )


    def set_duration_from_moviepy(self, video_obj, video_path):

        """Called by thread inside self.update_video_from_filesystem().

        When we call moviepy.editor.VideoFileClip() on a corrupted video file,
        moviepy freezes indefinitely.

        This function is called inside a thread, so a timeout of ten seconds
        can be applied.

        Args:

            video_obj (media.Video): The video object being updated

            video_path (str): The path to the video file itself

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 4624 set_duration_from_moviepy')

        try:
            clip = moviepy.editor.VideoFileClip(video_path)
            video_obj.set_duration(clip.duration)
        except:
            self.system_error(
                132,
                '\'' + video_obj.parent_obj.name + '\': moviepy module' \
                + 'failed to fetch duration of video \'' \
                + video_obj.name + '\'',
            )


    def set_backup_archive(self, media_data_obj):

        """Called by mainwin.MainWin.on_video_catalogue_re_download().

        If self.allow_ytdl_archive_flag is set, youtube-dl will have created a
        ytdl_archive.txt, recording every video ever downloaded in the parent
        directory.

        This will prevent a successful re-downloading of the video.

        Change the name of the archive file temporarily. After the download
        operation is complete, self.reset_backup_archive() is called to
        restore its original name.

        Args:

            media_data_obj (media.Video): The video object to be re-downloaded

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 4659 set_backup_archive')

        archive_path = os.path.abspath(
            os.path.join(
                media_data_obj.parent_obj.get_dir(self),
                'ytdl-archive.txt',
            )
        )

        if os.path.isfile(archive_path):

            bu_path = os.path.abspath(
                os.path.join(
                    media_data_obj.parent_obj.get_dir(self),
                    'bu_archive.txt',
                )
            )

            # (On MSWin, can't do os.rename if the destination file already
            #   exists)
            if os.path.isfile(bu_path):
                os.remove(bu_path)

            # (os.rename sometimes fails on external hard drives; this is
            #   safer)
            shutil.move(archive_path, bu_path)

            # Store both paths, so self.reset_backup_archive() can retrieve
            #   them
            self.ytdl_archive_path = archive_path
            self.ytdl_archive_backup_path = bu_path


    def reset_backup_archive(self):

        """Called by self.download_manager_finished().

        If the youtube-dl archive file was temporarily renamed (in a call to
        self.set_backup_archive()), in order to enable the video to be
        re-downloaded, then restore the archive file's original name.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 4700 reset_backup_archive')

        if self.ytdl_archive_path is not None \
        and self.ytdl_archive_backup_path is not None \
        and os.path.isfile(self.ytdl_archive_backup_path):

            # (On MSWin, can't do os.rename if the destination file already
            #   exists)
            if os.path.isfile(self.ytdl_archive_path):
                os.remove(self.ytdl_archive_path)

            # (os.rename sometimes fails on external hard drives; this is
            #   safer)
            shutil.move(
                self.ytdl_archive_backup_path,
                self.ytdl_archive_path,
            )

        # Regardless of whether a backup archive file was created during a
        #   re-download operation, or not, reset the IVs
        self.ytdl_archive_path = None
        self.ytdl_archive_backup_path = None


    # (Add media data objects)


    def add_video(self, parent_obj, source=None, dl_sim_flag=False,
    no_sort_flag=False):

        """Can be called by anything. Mostly called by
        self.create_video_from_download() and self.on_menu_add_video().

        Creates a new media.Video object, and updates IVs.

        Args:

            parent_obj (media.Channel, media.Playlist or media.Folder): The
                media data object for which the new media.Video object is the
                child (all videos have a parent)

            source (string): The video's source URL, if known

            dl_sim_flag (bool): If True, the video object's .dl_sim_flag IV is
                set to True, which forces simulated downloads

            no_sort_flag (bool): True when
                self.create_video_from_download() is called by
                downloads.VideoDownloader.confirm_sim_video(), because the
                video's parent containers (including the 'All Videos' folder)
                should delay sorting their lists of child objects until that
                calling function is ready. False when called by anything else

        Returns:

            The new media.Video object

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 4751 add_video')

        # Videos can't be placed inside other videos
        if parent_obj and isinstance(parent_obj, media.Video):
            return self.system_error(
                106,
                'Videos cannot be placed inside other videos',
            )

        # Videos can't be added directly to a private folder
        elif parent_obj and isinstance(parent_obj, media.Folder) \
        and parent_obj.priv_flag:
            return self.system_error(
                107,
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

        if dl_sim_flag:
            video_obj.set_dl_sim_flag(True)

        # Update IVs
        self.media_reg_count += 1
        self.media_reg_dict[video_obj.dbid] = video_obj

        # The private 'All Videos' folder also has this video as a child object
        self.fixed_all_folder.add_child(video_obj, no_sort_flag)

        # Update the row in the Video Index for both the parent and private
        #   folder
        self.main_win_obj.video_index_update_row_text(video_obj.parent_obj)
        self.main_win_obj.video_index_update_row_text(self.fixed_all_folder)

        # If the video's parent is the one visible in the Video Catalogue (or
        #   if 'Unsorted Videos' or 'Temporary Videos', etc, is the one visible
        #   in the Video Catalogue), the new video itself won't be visible
        #   there yet
        # Make sure the video is visible, if appropriate
        self.main_win_obj.video_catalogue_update_row(video_obj)

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
            utils.debug_time('app 4830 add_channel')

        # Channels can only be placed inside an unrestricted media.Folder
        #   object (if they have a parent at all)
        if parent_obj \
        and (
            not isinstance(parent_obj, media.Folder) \
            or parent_obj.restrict_flag
        ):
            return self.system_error(
                108,
                'Channels cannot be added to a restricted folder',
            )

        # There is a limit to the number of levels allowed in the media
        #   registry
        if parent_obj and parent_obj.get_depth() >= self.media_max_level:
            return self.system_error(
                109,
                'Channel exceeds maximum depth of media registry',
            )

        # Some names are not allowed at all
        if name is None \
        or re.match('^\s*$', name) \
        or not self.check_container_name_is_legal(name):
            return self.system_error(
                136,
                'Illegal channel name',
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
            utils.debug_time('app 4911 add_playlist')

        # Playlists can only be place inside an unrestricted media.Folder
        #   object (if they have a parent at all)
        if parent_obj \
        and (
            not isinstance(parent_obj, media.Folder) \
            or parent_obj.restrict_flag
        ):
            return self.system_error(
                110,
                'Playlists cannot be added to a restricted folder',
            )

        # There is a limit to the number of levels allowed in the media
        #   registry
        if parent_obj and parent_obj.get_depth() >= self.media_max_level:
            return self.system_error(
                111,
                'Playlist exceeds maximum depth of media registry',
            )

        # Some names are not allowed at all
        if name is None \
        or re.match('^\s*$', name) \
        or not self.check_container_name_is_legal(name):
            return self.system_error(
                137,
                'Illegal playlist name',
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


    def add_folder(self, name, parent_obj=None, dl_sim_flag=False,
    fixed_flag=False, priv_flag=False, restrict_flag=False, temp_flag=False):

        """Can be called by anything. Mostly called by
        self.on_menu_add_folder().

        Creates a new media.Folder object, and updates IVs.

        Args:

            name (string): The folder name

            parent_obj (media.Folder): The media data object for which the new
                media.Channel object is a child (if any)

            dl_sim_flag (bool): If True, the folders .dl_sim_flag IV is set to
                True, which forces simulated downloads for any videos,
                channels or playlists contained in the folder

            fixed_flag, priv_flag, restrict_flag, temp_flag (bool): Flags sent
                to the object's .__init__() function

        Returns:

            The new media.Folder object

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 4990 add_folder')

        # Folders can only be placed inside an unrestricted media.Folder object
        #   (if they have a parent at all)
        if parent_obj \
        and (
            not isinstance(parent_obj, media.Folder) \
            or parent_obj.restrict_flag
        ):
            return self.system_error(
                112,
                'Folders cannot be added to another restricted folder',
            )

        # There is a limit to the number of levels allowed in the media
        #   registry
        if parent_obj and parent_obj.get_depth() >= self.media_max_level:
            return self.system_error(
                113,
                'Folder exceeds maximum depth of media registry',
            )

        # Some names are not allowed at all
        if name is None \
        or re.match('^\s*$', name) \
        or not self.check_container_name_is_legal(name):
            return self.system_error(
                138,
                'Illegal folder name',
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

        if dl_sim_flag:
            folder_obj.set_dl_sim_flag(True)

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
            utils.debug_time('app 5064 move_container_to_top')

        # Do some basic checks
        if media_data_obj is None or isinstance(media_data_obj, media.Video) \
        or self.current_manager_obj or not media_data_obj.parent_obj:
            return self.system_error(
                114,
                'Move container to top request failed sanity check',
            )

        # Check that the target directory doesn't already exist (unlikely, but
        #   possible if the user has been copying files manually)
        target_path = os.path.abspath(
            os.path.join(
                self.downloads_dir,
                media_data_obj.name,
            ),
        )

        if os.path.isdir(target_path) or os.path.isfile(target_path):

            if os.name == 'nt':
                folder = 'folder'
            else:
                folder = 'directory'

            # (The same error message appears in self.move_container() )
            self.dialogue_manager_obj.show_msg_dialogue(
                'Cannot move anything to\n\n' + target_path + '\n\nbecause a' \
                + ' file or ' + folder + ' with the same name already\n' \
                + 'exists (although ' \
                + utils.upper_case_first(__main__.__packagename__) \
                + '\'s database doesn\'t know\nanything about it).\n\n' \
                + 'You probably created that file/' + folder \
                + ' accidentally,\nin which case, you should delete it' \
                + ' manually before\ntrying again.',
                'error',
                'ok',
            )

            return

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

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 5143 move_container_to_top_continue')

        # Move the sub-directories to their new location
        shutil.move(media_data_obj.get_dir(self), self.downloads_dir)

        # Update IVs
        media_data_obj.parent_obj.del_child(media_data_obj)
        media_data_obj.set_parent_obj(None)
        self.media_top_level_list.append(media_data_obj.dbid)

        # All videos which are descendents of media_data_obj must have their
        #   .file_dir IV updated to the new location
        for video_obj in media_data_obj.compile_all_videos( [] ):
            video_obj.reset_file_dir()

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
            utils.debug_time('app 5193 move_container')

        # Do some basic checks
        if source_obj is None or isinstance(source_obj, media.Video) \
        or dest_obj is None or isinstance(dest_obj, media.Video):
            return self.system_error(
                115,
                'Move container request failed sanity check',
            )

        elif source_obj == dest_obj:
            # No need for a system error message if the user drags a folder
            #   onto itself; just do nothing
            return

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

        # Check that the target directory doesn't already exist (unlikely, but
        #   possible if the user has been copying files manually)
        target_path = os.path.abspath(
            os.path.join(
                dest_obj.get_dir(self),
                source_obj.name,
            ),
        )

        if os.path.isdir(target_path) or os.path.isfile(target_path):

            if os.name == 'nt':
                folder = 'folder'
            else:
                folder = 'directory'

            self.dialogue_manager_obj.show_msg_dialogue(
                'Cannot move anything to\n\n' + target_path + '\n\nbecause a' \
                + ' file or ' + folder + ' with the same name already\n' \
                + 'exists (although ' \
                + utils.upper_case_first(__main__.__packagename__) \
                + '\'s database doesn\'t know\nanything about it).\n\n' \
                + 'You probably created that file/' + folder \
                + ' accidentally,\nin which case, you should delete it' \
                + ' manually before\ntrying again.',
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

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 5322 move_container_continue')

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
            video_obj.reset_file_dir()

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
        self.main_win_obj.video_index_select_row(source_obj)


    # (Convert channels to playlists, and vice-versa)


    def convert_remote_container(self, old_obj):

        """Called by mainwin.MainWin.on_video_index_convert_container().

        Converts a media.Channel object into a media.Playlist object, or vice-
        versa.

        Usually called after the user has copy-pasted a list of URLs into the
        mainwin.AddVideoDialogue window, some of which actually represent
        channels or playlists, not individual videos. During the next
        download operation, new channels or playlists can be automatically
        created (depending on the value of self.operation_convert_mode

        The user can then convert a channel to a playlist, and back again, as
        required.

        Args:

            old_obj (media.Channel, media.Playlist): The media data object to
                convert

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 5392 delete_video')

        if (
            not isinstance(old_obj, media.Channel) \
            and not isinstance(old_obj, media.Playlist)
        ) or self.current_manager_obj:
            return self.system_error(
                135,
                'Convert container request failed sanity check',
            )

        # If old_obj is a media.Channel, create a playlist. If old_obj is
        #   a media.Playlist, create a channel
        if isinstance(old_obj, media.Channel):

            new_obj = self.add_playlist(
                old_obj.name,
                old_obj.parent_obj,
                old_obj.source,
                old_obj.dl_sim_flag,
            )

        elif isinstance(old_obj, media.Playlist):

            new_obj = self.add_channel(
                old_obj.name,
                old_obj.parent_obj,
                old_obj.source,
                old_obj.dl_sim_flag,
            )

        # Move any children from the old object to the new one
        for child_obj in old_obj.child_list:

            # The True argument means to delay sorting the child list
            new_obj.add_child(child_obj, True)
            child_obj.set_parent_obj(new_obj)

        # Deal with alternative download destinations
        if old_obj.master_dbid:
            new_obj.set_master_dbid(self, old_obj.master_dbid)
            master_obj = self.media_reg_dict[old_obj.master_dbid]
            master_obj.del_slave_dbid(old_obj.dbid)

        for slave_dbid in old_obj.slave_dbid_list:
            slave_obj = self.media_reg_dict[slave_dbid]
            slave_obj.set_master_dbid(self, new_obj.dbid)

        # Copy remaining properties from the old object to the new one
        new_obj.clone_properties(old_obj)

        # Remove the old object from the media data registry.
        #   self.media_name_dict should already be updated
        del self.media_reg_dict[old_obj.dbid]
        if old_obj.dbid in self.media_top_level_list:
            self.media_top_level_list.remove(old_obj.dbid)

        # Remove the old object from the Video Index...
        self.main_win_obj.video_index_delete_row(old_obj)
        # ...and add the new one, selecting it at the same time
        self.main_win_obj.video_index_add_row(new_obj)


    # (Delete media data objects)


    def delete_video(self, video_obj, delete_files_flag=False,
    no_update_index_flag=False, no_update_catalogue_flag=False):

        """Called by self.delete_temp_folders(), .delete_old_videos(),
        .delete_container(), mainwin.MainWin.video_catalogue_popup_menu() and a
        callback in mainwin.MainWin.on_video_catalogue_delete_video().

        Deletes a video object from the media registry.

        Args:

            video_obj (media.Video): The media.Video object to delete

            delete_files_flag (True or False): True when called by
                mainwin.MainWin.on_video_catalogue_delete_video, in which case
                the video and its associated files are deleted from the
                filesystem

            no_update_index_flag (True or False): True when called by
                self.delete_old_videos() or self.delete_container(), in which
                case the Video Index is not updated

            no_update_catalogue_flag (True or False): True when called by
                self.delete_old_videos(), in which case the Video Catalogue is
                not updated

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 5392 delete_video')

        if not isinstance(video_obj, media.Video):
            return self.system_error(
                116,
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
        # v1.2.017 When deleting folders containing thousands of videos, I
        #   noticed that a small number of video DBIDs didn't exist in the
        #   registry. Not sure what the cause is, but the following lines
        #   prevent a python error
        if video_obj.dbid in self.media_reg_dict:
            del self.media_reg_dict[video_obj.dbid]

        # Delete files from the filesystem, if required
        if delete_files_flag and video_obj.file_dir:

            # There might be thousands of files in the directory, so using
            #   os.walk() or something like that might be too expensive
            # Also, post-processing might create various artefacts, all of
            #   which must be deleted
            ext_list = [
                'description',
                'info.json',
                'annotations.xml',
            ]
            ext_list.extend(formats.VIDEO_FORMAT_LIST)
            ext_list.extend(formats.AUDIO_FORMAT_LIST)

            print(ext_list)

            for ext in ext_list:

                file_path = os.path.abspath(
                    os.path.join(
                        self.downloads_dir,
                        video_obj.file_dir,
                        video_obj.file_name + '.' + ext,
                    ),
                )

                if os.path.isfile(file_path):
                    os.remove(file_path)

            # (Thumbnails might be in one of two locations, so are handled
            #   separately)
            thumb_path = utils.find_thumbnail(self, video_obj)
            if thumb_path and os.path.isfile(thumb_path):
                os.remove(thumb_path)

        # Remove the video from the catalogue, if present
        if not no_update_catalogue_flag:
            self.main_win_obj.video_catalogue_delete_row(video_obj)

        # Update rows in the Video Index, first checking that the parent
        #   container object is currently drawn there (which it might not be,
        #   if emptying temporary folders on startup)
        if not no_update_index_flag:
            for container_obj in update_list:

                if container_obj.name \
                in self.main_win_obj.video_index_row_dict:
                    self.main_win_obj.video_index_update_row_text(
                        container_obj,
                    )


    def delete_container(self, media_data_obj, empty_flag=False):

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

            empty_flag (True or False): If True, the container media data
                object is to be emptied, rather than being deleted


        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 5520 delete_container')

        # Check this isn't a video or a fixed folder (which cannot be removed)
        if isinstance(media_data_obj, media.Video) \
        or (
            isinstance(media_data_obj, media.Folder)
            and media_data_obj.fixed_flag
        ):
            return self.system_error(
                117,
                'Delete container request failed sanity check',
            )

        # Prompt the user for confirmation, even if the container object has no
        #   children
        # (Even though there are no children, we can't guarantee that the
        #   sub-directories in Tartube's data directory are empty)
        # Exception: don't prompt for confirmation if media_data_obj is
        #   somewhere inside a temporary folder
        confirm_flag = True
        delete_file_flag = False
        parent_obj = media_data_obj.parent_obj

        while parent_obj is not None:
            if isinstance(parent_obj, media.Folder) and parent_obj.temp_flag:
                # The media data object is somewhere inside a temporary folder;
                #   no need to prompt for confirmation
                confirm_flag = False

            parent_obj = parent_obj.parent_obj

        if confirm_flag:

            # Prompt the user for confirmation
            dialogue_win = mainwin.DeleteContainerDialogue(
                self.main_win_obj,
                media_data_obj,
                empty_flag,
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
                    'data': [media_data_obj, empty_flag],
                }
            )

        # No second confirmation required, so we can proceed directly to the
        #   call to self.delete_container_complete()
        else:
            self.delete_container_complete(media_data_obj, empty_flag)


    def delete_container_continue(self, data_list):

        """Called by dialogue.MessageDialogue.on_clicked().

        When deleting a container, after the user has specified that files
        should be deleted too, this function is called to delete those files.

        Args:

            data_list (list): A list of two items. The first is the container
                media data object; the second is a flag set to True if the
                container should be emptied, rather than being deleted

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 5612 delete_container_continue')

        # Unpack the arguments
        media_data_obj = data_list[0]
        empty_flag = data_list[1]

        # Confirmation obtained, so delete the files
        container_dir = media_data_obj.get_dir(self)
        if os.path.isdir(container_dir):
            shutil.rmtree(container_dir)

        # If emptying the container rather than deleting it, just create a
        #   replacement (empty) directory on the filesystem
        if empty_flag:
            os.makedirs(container_dir)

        # Now call self.delete_container_complete() to handle the media data
        #   registry
        self.delete_container_complete(media_data_obj, empty_flag)


    def delete_container_complete(self, media_data_obj, empty_flag,
    recursive_flag=False):

        """Called by self.delete_container(), .delete_container_continue()
        and then recursively by this function.

        Deletes a channel, playlist or folder object from the media data
        registry.

        This function calls itself recursively to delete all of the container
        object's descendants.

        Args:

            media_data_obj (media.Channel, media.Playlist, media.Folder):
                The container media data object

            empty_flag (True or False): If True, the container media data
                object is to be emptied, rather than being deleted

            recursive_flag (True, False): Set to False on the initial call to
                this function from some other part of the code, and True when
                this function calls itself recursively

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 5660 delete_container_complete')

        # Confirmation has been obtained, and any files have been deleted (if
        #   required), so now deal with the media data registry

        # Recursively remove all of the container object's children. The code
        #   doesn't work as intended, unless we make a copy of the list of
        #   child objects first
        copy_list = media_data_obj.child_list.copy()
        for child_obj in copy_list:
            if isinstance(child_obj, media.Video):
                self.delete_video(child_obj, False, True)
            else:
                self.delete_container_complete(child_obj, False, True)

        if not empty_flag or recursive_flag:

            # Remove the container object from its own parent object (if it has
            #   one)
            if media_data_obj.parent_obj:
                media_data_obj.parent_obj.del_child(media_data_obj)

            # Reset alternative download destinations
            media_data_obj.set_master_dbid(self, media_data_obj.dbid)

            # Remove the media data object from our IVs
            del self.media_reg_dict[media_data_obj.dbid]
            del self.media_name_dict[media_data_obj.name]
            if media_data_obj.dbid in self.media_top_level_list:
                index = self.media_top_level_list.index(media_data_obj.dbid)
                del self.media_top_level_list[index]

        # During the initial call to this function, delete the container
        #   object from the Video Index (which automatically resets the Video
        #   Catalogue)
        # (If deleting the contents of temporary folders while loading a
        #   Tartube database, the Video Index may not yet have been drawn, so
        #   we have to check for that)
        if not recursive_flag and not empty_flag \
        and media_data_obj.name in self.main_win_obj.video_index_row_dict:

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

        elif not recursive_flag and empty_flag:

            # When emptying the container, the quickest way to update the Video
            #   Index is just to redraw it from scratch
            self.main_win_obj.video_index_reset()
            self.main_win_obj.video_catalogue_reset()
            self.main_win_obj.video_index_populate()


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
            utils.debug_time('app 5752 mark_video_new')

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
                118,
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
                #   (the folder's .new_count is automatically updated)
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
                if video_obj.fav_flag:
                    self.fixed_new_folder.inc_fav_count()
#                if video_obj.dl_flag:
#                    self.fixed_new_folder.inc_dl_count()
                # Update the Video Catalogue, if that folder is the visible one
                self.main_win_obj.video_catalogue_update_row(video_obj)

                # Update other private folders
                self.fixed_all_folder.inc_new_count()
                if video_obj.fav_flag:
                    self.fixed_fav_folder.inc_new_count()

        # Update rows in the Video Index
        for container_obj in update_list:
            self.main_win_obj.video_index_update_row_text(container_obj)


    def mark_video_downloaded(self, video_obj, dl_flag, not_new_flag=False):

        """Can be called by anything.

        Marks a video object as downloaded (i.e. the video file exists on the
        user's filesystem) or not downloaded.

        The video object's .dl_flag IV is updated.

        Args:

            video_obj (media.Video): The media.Video object to mark.

            dl_flag (True or False): True to mark the video as downloaded,
                False to mark it as not downloaded.

            not_new_flag (True or False): Set to True when called by
                downloads.confirm_old_video(). The video is downloaded, but not
                new

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 5861 mark_video_downloaded')

        # (List of Video Index rows to update, at the end of this function)
        update_list = [video_obj.parent_obj, self.fixed_all_folder]

        # Mark the video as downloaded or not downloaded
        if not isinstance(video_obj, media.Video):
            return self.system_error(
                119,
                'Mark video as downloaded request failed sanity check',
            )

        elif not dl_flag:

            # Mark video as not downloaded
            if not video_obj.dl_flag:

                # Already marked
                return

            else:

                # Update the video object's IVs
                video_obj.set_dl_flag(False)
                # (A video that is not downloaded cannot be marked archived)
                video_obj.set_archive_flag(False)
                # Update the parent container object
                video_obj.parent_obj.dec_dl_count()
                # Update private folders
                self.fixed_all_folder.dec_dl_count()
                self.fixed_new_folder.dec_dl_count()
                if video_obj.fav_flag:
                    self.fixed_fav_folder.dec_dl_count()
                    update_list.append(self.fixed_fav_folder)

                # Also mark the video as not new
                if not not_new_flag:
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
                if not not_new_flag:
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
            utils.debug_time('app 5958 mark_video_favourite')

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
                120,
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
                #   (the folder's .new_count, .fav_count and .dl_count IVs are
                #   automatically updated)
                self.fixed_fav_folder.del_child(video_obj)
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
            utils.debug_time('app 6062 mark_folder_hidden')

        if not isinstance(folder_obj, media.Folder):
            return self.system_error(
                121,
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


    def mark_container_archived(self, media_data_obj, flag,
    only_child_videos_flag):

        """Called by mainwin.MainWin.on_video_index_mark_archived() and
        .on_video_index_mark_not_archived().

        Marks any descedant videos as archived.

        Args:

            media_data_obj (media.Channel, media.Playlist or media.Folder):
                The container object to update

            flag (True or False): True to mark as archived, False to mark as
                not archived

            only_child_videos_flag (True or False): Set to True if only child
                video objects should be marked; False if the container object
                and all its descendants should be marked

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 6124 mark_container_archived')

        if isinstance(media_data_obj, media.Video):
            return self.system_error(
                122,
                'Mark container as archived request failed sanity check',
            )

        # Special arrangements for private folders
        if media_data_obj == self.fixed_all_folder:

            # Check every video
            for other_obj in list(self.media_reg_dict.values()):

                if isinstance(other_obj, media.Video) and other_obj.dl_flag:
                    other_obj.set_archive_flag(flag)

        elif media_data_obj == self.fixed_new_folder:

            # Check videos in this folder
            for other_obj in self.fixed_new_folder.child_list:

                if isinstance(other_obj, media.Video) and other_obj.dl_flag \
                and other_obj.new_flag:
                    other_obj.set_archive_flag(flag)

        elif not flag and media_data_obj == self.fixed_fav_folder:

            # Check videos in this folder
            for other_obj in self.fixed_fav_folder.child_list:

                if isinstance(other_obj, media.Video) and other_obj.dl_flag \
                and other_obj.fav_flag:
                    other_obj.set_archive_flag(flag)

        elif only_child_videos_flag:

            # Check videos in this channel/playlist/folder
            for other_obj in media_data_obj.child_list:

                if isinstance(other_obj, media.Video):
                    other_obj.set_archive_flag(flag)

        else:

            # Check videos in this channel/playlist/folder, and in any
            #   descendant channels/playlists/folders
            for other_obj in media_data_obj.compile_all_videos( [] ):

                if isinstance(other_obj, media.Video) and other_obj.dl_flag:
                    other_obj.set_archive_flag(flag)

        # In all cases, update the row on the Video Index
        self.main_win_obj.video_index_update_row_icon(media_data_obj)
        self.main_win_obj.video_index_update_row_text(media_data_obj)
        # If this container is the one visible in the Video Catalogue, redraw
        #   the Video Catalogue
        if self.main_win_obj.video_index_current == media_data_obj.name:
            self.main_win_obj.video_catalogue_redraw_all(
                self.main_win_obj.video_index_current,
            )


    def mark_container_favourite(self, media_data_obj, flag,
    only_child_videos_flag):

        """Called by mainwin.MainWin.on_video_index_mark_favourite() and
        .on_video_index_mark_not_favourite().

        Marks this channel, playlist or folder as favourite. Also marks any
        descendant videos as favourite (but not descendent channels, playlists
        or folders).

        Args:

            media_data_obj (media.Channel, media.Playlist or media.Folder):
                The container object to update

            flag (True or False): True to mark as favourite, False to mark as
                not favourite

            only_child_videos_flag (True or False): Set to True if only child
                video objects should be marked; False if the container object
                and all its descendants should be marked

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 6212 mark_container_favourite')

        if isinstance(media_data_obj, media.Video):
            return self.system_error(
                123,
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

        elif only_child_videos_flag:

            # Check videos in this folder
            for other_obj in media_data_obj.child_list:

                if isinstance(other_obj, media.Video):
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


    def rename_container(self, media_data_obj):

        """Called by mainwin.MainWin.on_video_index_rename_destination().

        Renames a channel, playlist or folder. Also renames the corresponding
        directory in Tartube's data directory.

        Args:

            media_data_obj (media.Channel, media.Playlist, media.Folder): The
                media data object to be renamed

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 6291 rename_container')

        # Do some basic checks
        if media_data_obj is None or isinstance(media_data_obj, media.Video) \
        or self.current_manager_obj or self.main_win_obj.config_win_list \
        or (
            isinstance(media_data_obj, media.Folder) \
            and media_data_obj.fixed_flag
        ):
            return self.system_error(
                124,
                'Rename container request failed sanity check',
            )

        # Prompt the user for a new name
        dialogue_win = mainwin.RenameContainerDialogue(
            self.main_win_obj,
            media_data_obj,
        )

        response = dialogue_win.run()

        # Retrieve user choices from the dialogue window, before destroying it
        new_name = dialogue_win.entry.get_text()
        dialogue_win.destroy()

        if response == Gtk.ResponseType.OK and new_name != '' \
        and new_name != media_data_obj.name:

            # Check that the name is legal
            if new_name is None \
            or re.match('^\s*$', new_name) \
            or not self.check_container_name_is_legal(new_name):
                return self.dialogue_manager_obj.show_msg_dialogue(
                    'The name \'' + new_name + '\' is not allowed',
                    'error',
                    'ok',
                )

            # Check that an existing channel/playlist/folder isn't already
            #   using this name
            if new_name in self.media_name_dict:
                return self.dialogue_manager_obj.show_msg_dialogue(
                    'The name \'' + new_name + '\' is already in use',
                    'error',
                    'ok',
                )

            # Attempt to rename the sub-directory itself
            old_dir = media_data_obj.get_dir(self)
            new_dir = media_data_obj.get_dir(self, new_name)
            try:
                shutil.move(old_dir, new_dir)

            except:
                return self.dialogue_manager_obj.show_msg_dialogue(
                    'Failed to rename \'' + media_data_obj.name + '\'',
                    'error',
                    'ok',
                )

            # Filesystem updated, so now update the media data object itself.
            #   This call also updates the object's .nickname IV
            old_name = media_data_obj.name
            media_data_obj.set_name(new_name)
            # Update the media data registry
            del self.media_name_dict[old_name]
            self.media_name_dict[new_name] = media_data_obj.dbid

            # All videos which are descendents of media_data_obj must have
            #   their .file_dir IV updated to the new location
            for video_obj in media_data_obj.compile_all_videos( [] ):
                video_obj.reset_file_dir()

            # Reset the Video Index and the Video Catalogue (this prevents a
            #   lot of problems)
            self.main_win_obj.video_catalogue_reset()
            self.main_win_obj.video_index_reset()
            self.main_win_obj.video_index_populate()

            # Save the database file (since the filesystem itself has changed)
            self.save_db()


    def rename_container_silently(self, media_data_obj, new_name):

        """Called by self.start().

        A modified form of self.rename_container. No dialogue windows are used,
        no widgets are updated or desensitised, and the Tartube database file
        is not saved.

        No checks are carried out; it's up to the calling function to check
        this function's return value, and respond appropriately.

        Renames a channel, playlist or folder. Also renames the corresponding
        directory in Tartube's data directory.


        Args:

            media_data_obj (media.Channel, media.Playlist, media.Folder): The
                media data object to be renamed

            new_name (str): The object's new name

        Returns:
            True on success, False on failure

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 6292 rename_container_silently')

        # Nothing in the Tartube code should be capable of calling this
        #   function with an illegal name, but we'll still check
        if not self.check_container_name_is_legal(new_name):
            self.system_error(
                139,
                'Illegal container name',
            )

            return False

        # Attempt to rename the sub-directory itself
        old_dir = media_data_obj.get_dir(self)
        new_dir = media_data_obj.get_dir(self, new_name)
        try:
            shutil.move(old_dir, new_dir)

        except:
            return False

        # Filesystem updated, so now update the media data object itself. This
        #   call also updates the object's .nickname IV
        old_name = media_data_obj.name
        media_data_obj.set_name(new_name)
        # Update the media data registry
        del self.media_name_dict[old_name]
        self.media_name_dict[new_name] = media_data_obj.dbid

        # All videos which are descendents of media_data_obj must have their
        #   .file_dir IV updated to the new location
        for video_obj in media_data_obj.compile_all_videos( [] ):
            video_obj.reset_file_dir()

        return True


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
            utils.debug_time('app 6387 apply_download_options')

        if self.current_manager_obj \
        or media_data_obj.options_obj\
        or (
            isinstance(media_data_obj, media.Folder)
            and media_data_obj.priv_flag
        ):
            return self.system_error(
                125,
                'Apply download options request failed sanity check',
            )

        # Apply download options to the media data object
        media_data_obj.set_options_obj(options.OptionsManager())
        # If required, clone download options from the General Options Manager
        #   into the new download options manager
        if self.auto_clone_options_flag:
            media_data_obj.options_obj.clone_options(
                self.general_options_obj,
            )

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
            utils.debug_time('app 6432 remove_download_options')

        if self.current_manager_obj or not media_data_obj.options_obj:
            return self.system_error(
                126,
                'Remove download options request failed sanity check',
            )

        # Remove download options from the media data object
        media_data_obj.set_options_obj(None)
        # Update the row in the Video Index
        self.main_win_obj.video_index_update_row_icon(media_data_obj)


    def check_container_name_is_legal(self, name):

        """Called by self.on_menu_add_channel(), etc, by self.add_channel(),
        etc, self.rename_container() and self.rename_container_silently().

        Checks that the name of a channel, playlist or folder is legal, i.e.
        that it doesn't match one of the regexes in
        self.illegal_name_regex_list.

        Does not check whether an existing container is already using the name;
        that's the responsibility of the calling code.

        Args:

            name (str): A proposed name for a media.Channel, media.Playlist or
                media.Folder object

        Return values:

            True if the name is legal, False if it is illegal

        """

        for regex in self.illegal_name_regex_list:
            if re.search(regex, name, re.IGNORECASE):
                # Illegal name
                return False

        # Legal name
        return True


    # (Export/import data to/from the Tartube database)

    def export_from_db(self, media_list):

        """
        Called by self.on_menu_export_db() or by any other function.

        Exports a summary of the Tartube database to an export file - either a
        structured JSON file, or a plain text file, at the user's option.

        The export file typically contains a list of videos, channels,
        playlists and folders, but not any downloaded files (videos,
        thumbnails, etc).

        The export file is not the same as a Tartube database file (usually
        tartube.db) and cannot be loaded as a database file. However, the
        export file can be imported into an existing database.

        Args:

            media_list (list): A list of media data objects. If specified, only
                those objects (and any media data objects they contain) are
                included in the export. If an empty list is passed, the whole
                database is included.

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 6474 export_from_db')

        # If the specified list is empty, a summary of the whole database is
        #   exported
        if not media_list:
            whole_flag = True
        else:
            whole_flag = False

        # Prompt the user for which kinds of media data object should be
        #   included in the export, and which type of file (JSON or plain text)
        #   should be created
        dialogue_win = mainwin.ExportDialogue(self.main_win_obj, whole_flag)
        response = dialogue_win.run()

        # Retrieve user choices from the dialogue window...
        include_video_flag = dialogue_win.checkbutton.get_active()
        include_channel_flag = dialogue_win.checkbutton2.get_active()
        include_playlist_flag = dialogue_win.checkbutton3.get_active()
        preserve_folder_flag = dialogue_win.checkbutton4.get_active()
        plain_text_flag = dialogue_win.checkbutton5.get_active()
        # ...before destroying the dialogue window
        dialogue_win.destroy()

        if response != Gtk.ResponseType.OK:
            return

        # Prompt the user for the file path to use
        file_chooser_win = Gtk.FileChooserDialog(
            'Select where to save the database export',
            self.main_win_obj,
            Gtk.FileChooserAction.SAVE,
            (
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN, Gtk.ResponseType.OK,
            ),
        )

        if not plain_text_flag:
            file_chooser_win.set_current_name(self.export_json_file_name)
        else:
            file_chooser_win.set_current_name(self.export_text_file_name)

        response = file_chooser_win.run()
        if response != Gtk.ResponseType.OK:
            file_chooser_win.destroy()
            return

        file_path = file_chooser_win.get_filename()
        file_chooser_win.destroy()
        if not file_path:
            return

        # Compile a dictionary of data to export, representing the contents of
        #   the database (in whole or in part)
        # Throughout the export/import code, dictionaries in this form are
        #   called 'db_dict'
        # Depending on the user's choices, the dictionary preserves the folder
        #   structure of the database (or not)
        #
        # Key-value pairs in the dictionary are in the form
        #
        #       dbid: mini_dict
        #
        # 'dbid' is each media data object's .dbid
        # 'mini_dict' is a dictionary of values representing a media data
        #   object
        #
        # The same 'mini_dict' structure is used during export and
        #   import procedures. Its keys are:
        #
        #       type        - set to 'video', 'channel', 'playlist' or 'folder'
        #       dbid        - set to the media data object's .dbid
        #       name        - set to the media data object's .name IV
        #       nickname    - set to the media data object's .nickname IV (or
        #                       None for videos)
        #       source      - set to the media data object's .source IV (or
        #                       None for folders)
        #       db_dict     - the children of this media data object, stored in
        #                       the form described above
        #
        # The import process adds some extra keys to a 'mini_dict' while
        #   processing it, but only for channels/playlists/folders. The extra
        #   keys are:
        #
        #       display_name
        #               - the media data object's name, indented for display
        #                   in mainwin.ImportDialogueWin
        #       video_count
        #               - the number of videos this media data object contains
        #       import_flag
        #               - True if the user has selected this media data object
        #                   to be imported, False if they have deselected it
        db_dict = {}

        # Compile the contents of the 'db_dict' to export
        # If the media_list argument is empty, use the whole database.
        #   Otherwise, use only the specified media data objects (and any media
        #   data objects they contain)
        if preserve_folder_flag and not plain_text_flag:

            if media_list:

                for media_data_obj in media_list:

                    mini_dict = media_data_obj.prepare_export(
                        include_video_flag,
                        include_channel_flag,
                        include_playlist_flag,
                    )

                    if mini_dict:
                        db_dict[media_data_obj.dbid] = mini_dict

            else:

                for dbid in self.media_top_level_list:

                    media_data_obj = self.media_reg_dict[dbid]

                    mini_dict = media_data_obj.prepare_export(
                        include_video_flag,
                        include_channel_flag,
                        include_playlist_flag,
                    )

                    if mini_dict:
                        db_dict[media_data_obj.dbid] = mini_dict

        else:

            if media_list:

                for media_data_obj in media_list:

                    db_dict = media_data_obj.prepare_flat_export(
                        db_dict,
                        include_video_flag,
                        include_channel_flag,
                        include_playlist_flag,
                    )

            else:

                for dbid in self.media_top_level_list:

                    media_data_obj = self.media_reg_dict[dbid]

                    db_dict = media_data_obj.prepare_flat_export(
                        db_dict,
                        include_video_flag,
                        include_channel_flag,
                        include_playlist_flag,
                    )

        if not db_dict:

            return self.dialogue_manager_obj.show_msg_dialogue(
                'There is nothing to export!',
                'error',
                'ok',
            )

        # Export a JSON file
        if not plain_text_flag:

            # The exported JSON file has the same metadata as a config file,
            #   with only the 'file_type' being different

            # Prepare values
            utc = datetime.datetime.utcfromtimestamp(time.time())

            # Prepare a dictionary of data to save as a JSON file
            json_dict = {
                # Metadata
                'script_name': __main__.__packagename__,
                'script_version': __main__.__version__,
                'save_date': str(utc.strftime('%d %b %Y')),
                'save_time': str(utc.strftime('%H:%M:%S')),
                'file_type': 'db_export',
                # Data
                'db_dict': db_dict,
            }

            # Try to save the file
            try:
                with open(file_path, 'w') as outfile:
                    json.dump(json_dict, outfile, indent=4)

            except:
                return self.dialogue_manager_obj.show_msg_dialogue(
                    'Failed to save the database export file',
                    'error',
                    'ok',
                )

        # Export a plain text file
        else:

            # The text file contains lines, in groups of three, in the
            #   following format:
            #
            #       @type
            #       <name>
            #       <url>
            #
            # ...where '@type' is one of '@video', '@channel' or '@playlist'
            #   (the folder structure is never preserved in a plain text
            #   export)
            # A video belongs to the channel/playlist above it

            # Prepare the list of lines
            line_list = []

            for dbid in db_dict.keys():

                media_data_obj = self.media_reg_dict[dbid]

                if isinstance(media_data_obj, media.Channel):
                    line_list.append('@channel')
                    line_list.append(media_data_obj.name)
                    line_list.append(media_data_obj.source)

                elif isinstance(media_data_obj, media.Playlist):
                    line_list.append('@playlist')
                    line_list.append(media_data_obj.name)
                    line_list.append(media_data_obj.source)

                else:
                    continue

                if include_video_flag:

                    for child_obj in media_data_obj.child_list:
                        # (Nothing but videos should be in this list, but we'll
                        #   check anyway)
                        if isinstance(child_obj, media.Video):
                            line_list.append('@video')
                            line_list.append(child_obj.name)
                            line_list.append(child_obj.source)

            # Try to save the file
            try:
                with open(file_path, 'w') as outfile:
                    for line in line_list:
                        outfile.write(line + '\n')

            except:
                return self.dialogue_manager_obj.show_msg_dialogue(
                    'Failed to save the database export file',
                    'error',
                    'ok',
                )

        # Export was successful
        self.dialogue_manager_obj.show_msg_dialogue(
            'Database export file saved to\n' + file_path,
            'info',
            'ok',
        )


    def import_into_db(self, json_flag):

        """Called by self.on_menu_import_json() or by any other function.

        Imports the contents of a JSON export file or a plain text export file
        generated by a call to self.export_from_db().

        After prompting the user, creates new media.Video, media.Channel,
        media.Playlist and/or media.Folder objects. Checks for duplicates and
        handles them appropriately.

        A JSON export file contains a dictionary, 'db_dict', containing further
        dictionaries, 'mini_dict', whose formats are described in the comments
        in self.export_from_db().

        A plain text export file contains lines in groups of three, in the
        format described in the comments in self.export_from_db().

        Args:

            json_flag (bool): True if a JSON export file should be imported,
                False if a plain text export file should be imported

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 6762 import_into_db')

        # Prompt the user for the export file to load
        file_chooser_win = Gtk.FileChooserDialog(
            'Select the database export',
            self.main_win_obj,
            Gtk.FileChooserAction.OPEN,
            (
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN, Gtk.ResponseType.OK,
            ),
        )

        response = file_chooser_win.run()
        if response != Gtk.ResponseType.OK:
            file_chooser_win.destroy()
            return

        file_path = file_chooser_win.get_filename()
        file_chooser_win.destroy()
        if not file_path:
            return

        # Try to load the export file
        if not json_flag:

            text = self.file_manager_obj.load_text(file_path)
            if text is None:
                return self.dialogue_manager_obj.show_msg_dialogue(
                    'Failed to load the database export file',
                    'error',
                    'ok',
                )

            # Parse the text file, creating a db_dict in the form described in
            #   the comments in self.export_from_db()
            db_dict = self.parse_text_import(text)

        else:

            json_dict = self.file_manager_obj.load_json(file_path)
            if not json_dict:
                return self.dialogue_manager_obj.show_msg_dialogue(
                    'Failed to load the database export file',
                    'error',
                    'ok',
                )

            # Do some basic checks on the loaded data
            # (At the moment, JSON export files are compatible with all
            #   versions of Tartube after v1.0.0; this may change in future)
            if not json_dict \
            or not 'script_name' in json_dict \
            or not 'script_version' in json_dict \
            or not 'save_date' in json_dict \
            or not 'save_time' in json_dict \
            or not 'file_type' in json_dict \
            or json_dict['script_name'] != __main__.__packagename__ \
            or json_dict['file_type'] != 'db_export':
                return self.dialogue_manager_obj.show_msg_dialogue(
                    'The database export file is invalid',
                    'error',
                    'ok',
                )

            # Retrieve the database data itself. db_dict is in the form
            #   described in the comments in self.export_from_db()
            db_dict = json_dict['db_dict']

        if not db_dict:
            return self.dialogue_manager_obj.show_msg_dialogue(
                'The database export file\nis invalid (or empty)',
                'error',
                'ok',
            )

        # Prompt the user to allow them to select which videos/channels/
        #   playlists/folders to actually import, and how to deal with
        #   duplicate channels/playlists/folders
        dialogue_win = mainwin.ImportDialogue(self.main_win_obj, db_dict)
        response = dialogue_win.run()

        # Retrieve user choices from the dialogue window, before destroying the
        #   dialogue window
        # 'flat_db_dict' is a flattened version of the imported 'db_dict' (i.e.
        #   with its folder structure removed), and with additional key-value
        #   pairs added to each 'mini_dict'. (The new key-value pairs are also
        #   described in the comments in self.export_from_db() )
        import_videos_flag = dialogue_win.checkbutton.get_active()
        merge_duplicates_flag = dialogue_win.checkbutton.get_active()
        flat_db_dict = dialogue_win.flat_db_dict
        dialogue_win.destroy()

        if response != Gtk.ResponseType.OK:
            return

        # Process the imported 'db_dict', creating new videos/channels/
        #   playlists/folders as required, and dealing appropriately with
        #   any duplicates
        (video_count, channel_count, playlist_count, folder_count) \
        = self.process_import(
            db_dict,                # The imported data
            flat_db_dict,           # The flattened version of that dictionary
            None,                   # No parent 'mini_dict' yet
            import_videos_flag,
            merge_duplicates_flag,
            0,                      # video_count
            0,                      # channel_count
            0,                      # playlist count
            0,                      # folder_count
        )

        if not video_count and not channel_count and not playlist_count \
        and not folder_count:
            self.dialogue_manager_obj.show_msg_dialogue(
                'Nothing was imported from\nthe database export file',
                'error',
                'ok',
            )

        else:

            # Update the Video Catalogue, in case any new videos have been
            #   imported into it
            self.main_win_obj.video_catalogue_redraw_all(
                self.main_win_obj.video_index_current,
            )

            # Show a confirmation
            msg = 'Imported:' \
            + '\n\nVideos: ' + str(video_count) \
            + '\nChannels: ' + str(channel_count) \
            + '\nPlaylists: ' + str(playlist_count) \
            + '\nFolders: ' + str(folder_count)

            self.dialogue_manager_obj.show_msg_dialogue(msg, 'info', 'ok')


    def parse_text_import(self, text):

        """Called by self.import_into_db().

        Given the contents of a plain text database export, which has been
        loaded into memory, convert the contents into the db_dict format
        described in the comments in self.export_from_db(), as if a JSON
        database export had been loaded.

        The text file contains lines, in groups of three, in the following
        format:

            @type
            <name>
            <url>

        ...where '@type' is one of '@video', '@channel' or '@playlist' (the
        folder structure is never preserved in a plain text export).

        A video belongs to the channel/playlist above it.

        Args:

            text (str): The contents of the loaded plain text file

        Returns:

            db_dict (dict): The converted data in the form described in the
                comments in self.export_from_db()

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 6933 parse_text_import')

        db_dict = {}
        dbid = 0
        last_container_mini_dict = None

        # Split text into separate lines
        line_list = text.split('\n')

        # Remove all empty lines (including those containing only whitespace)
        mod_list = []
        for line in line_list:
            if re.match('\S', line):
                mod_list.append(line)

        # Extract each group of three lines, and check they are valid
        # If a group of three is invalid (or if we reach the end of the file
        #   in the middle of a group of 3), ignore that group and any
        #   subsequent groups, and just use the data already extracted
        while len(mod_list) > 2:

            media_type = mod_list[0]
            name = mod_list[1]
            source = mod_list[2]

            mod_list = mod_list[3:]

            if media_type is None \
            or (
                media_type != '@video' and media_type != '@channel' \
                and media_type != '@playlist'
            ) \
            or name is None or name == '' \
            or source is None or not utils.check_url(source):
                break

            # A valid group of three; add an entry to db_dict using a fake dbid
            dbid += 1

            mini_dict = {
                'type': None,
                'dbid': dbid,
                'name': name,
                'nickname': name,
                'source': source,
                'db_dict': {},
            }

            if media_type == '@video':
                mini_dict['type'] = 'video'
                # A video belongs to the previous channel or playlist (if any)
                if last_container_mini_dict is not None:
                    last_container_mini_dict['db_dict'][dbid] = mini_dict

            elif media_type == '@channel':
                mini_dict['type'] = 'channel'
                last_container_mini_dict = mini_dict

            else:
                mini_dict['type'] = 'playlist'
                last_container_mini_dict = mini_dict

            db_dict[dbid] = mini_dict

        # Procedure complete
        return db_dict


    def process_import(self, db_dict, flat_db_dict, parent_obj,
    import_videos_flag, merge_duplicates_flag, video_count, channel_count,
    playlist_count, folder_count):

        """Called by self.import_into_db() and then recursively by this
        function.

        Process a 'db_dict' (in the format described in the comments in
        self.export_from_db() ).

        Create new videos/channels/playlists/folders as required, and deal
        appropriately with any duplicates

        Args:

            db_dict (dict): The dictionary described in self.export_from_db();
                if called from self.import_into_db(), the original imported
                dictionary; if called recursively, a dictionary from somewhere
                inside the original imported dictionary

            flat_db_dict (dict): A flattened version of the original imported
                'db_dict' (not necessarily the same 'db_dict' provided by the
                argument above). Flattened means that the folder structure has
                been removed, and additional key-value pairs have been added to
                each 'mini_dict'

            parent_obj (media.Channel, media.Playlist, media.Folder or None):
                The contents of db_dict are all children of this parent media
                data object

            import_videos_flag (bool): If True, any video objects are imported.
                If False, video objects are ignored

            merge_duplicates_flag (bool): If True, imported channels/playlists/
                folders with the same name (and source URL) as an existing
                channel/playlist/folder are merged with them. If False, the
                imported channel/playlist/folder is renamed

            video_count, channel_count, playlist_count, folder_count (int): The
                total number of videos/channels/playlists/folders imported so
                far

        Return values:

            video_count, channel_count, playlist_count, folder_count (int): The
                updated counts after importing videos/channels/playlists/
                folders

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 7052 process_import')

        # To optimise the code below, compile a dictionary for quick lookup,
        #   containing the source URLs for all videos in the parent channel/
        #   playlist/folder
        url_check_dict = {}
        if parent_obj:
            for child_obj in parent_obj.child_list:
                if isinstance(child_obj, media.Video) \
                and child_obj.source is not None:
                    url_check_dict[child_obj.source] = None

        # Deal in turn with each video/channel/playlist/folder stored at the
        #   top level of 'db_dict'
        # The dbid is the one used in the database from which the export file
        #   was generated. Once imported into our database, the new media data
        #   object will be given a different dbid
        # (In other words, we can't compare this dbid with those used in
        #   self.media_reg_dict)
        for dbid in db_dict.keys():

            media_data_obj = None

            # Each 'mini_dict' contains details for a single video/channel/
            #   playlist/folder
            mini_dict = db_dict[dbid]

            # Check whether the user has marked this item to be imported, or
            #   not
            if int(dbid) in flat_db_dict:

                check_dict = flat_db_dict[int(dbid)]
                if not check_dict['import_flag']:

                    # Don't import this one
                    continue

            # This item is marked to be imported
            if mini_dict['type'] == 'video':

                if import_videos_flag:

                    # Check that a video with the same URL doesn't already
                    #   exist in the parent channel/playlist/folder. If so,
                    #   don't import this duplicate video
                    if not mini_dict['source'] in url_check_dict:

                        # This video isn't a duplicate, so we can import it
                        video_obj = self.add_video(
                            parent_obj,
                            mini_dict['source'],
                        )

                        if video_obj:
                            video_count += 1
                            video_obj.set_name(mini_dict['name'])

            else:

                if mini_dict['name'] in self.media_name_dict:

                    old_dbid = self.media_name_dict[mini_dict['name']]
                    old_obj = self.media_reg_dict[old_dbid]

                    # A channel/playlist/folder with the same name already
                    #   exists in our database. Rename it if the user wants
                    #   that, or if the two have different source URLs
                    if not merge_duplicates_flag \
                    or old_obj.source != mini_dict['source']:

                        # Rename the imported channel/playlist/folder
                        mini_dict['name'] = self.rename_imported_container(
                            mini_dict['name'],
                        )

                        mini_dict['nickname'] = self.rename_imported_container(
                            mini_dict['nickname'],
                        )

                    else:

                        # Use the existing channel/playlist/folder of the same
                        #   name, thereby merging the two
                        old_dbid = self.media_name_dict[mini_dict['name']]
                        media_data_obj = self.media_reg_dict[old_dbid]

                # Import the channel/playlist/folder
                if mini_dict['type'] == 'channel':
                    media_data_obj = self.add_channel(
                        mini_dict['name'],
                        parent_obj,
                        mini_dict['source'],
                    )

                    if media_data_obj:
                        channel_count += 1

                elif mini_dict['type'] == 'playlist':
                    media_data_obj = self.add_playlist(
                        mini_dict['name'],
                        parent_obj,
                        mini_dict['source'],
                    )

                    if media_data_obj:
                        playlist_count += 1

                elif mini_dict['type'] == 'folder':
                    media_data_obj = self.add_folder(
                        mini_dict['name'],
                        parent_obj,
                    )

                    if media_data_obj:
                        folder_count += 1

                # If the channel/playlist/folder was successfully imported,
                #   set its nickname, update the Video Index, then deal with
                #   any children by calling this function recursively
                if media_data_obj is not None:

                    media_data_obj.set_nickname(mini_dict['nickname'])

                    self.main_win_obj.video_index_add_row(media_data_obj)

                    if mini_dict['db_dict']:

                        (
                            video_count, channel_count, playlist_count,
                            folder_count,
                        ) = self.process_import(
                            mini_dict['db_dict'],
                            flat_db_dict,
                            media_data_obj,
                            import_videos_flag,
                            merge_duplicates_flag,
                            video_count,
                            channel_count,
                            playlist_count,
                            folder_count,
                        )

        # Procedure complete
        return video_count, channel_count, playlist_count, folder_count


    def rename_imported_container(self, name):

        """Called by self.process_import() (only).

        When importing a channel/playlist/folder whose name is the same as an
        existing channel/playlist/folder, this function is called to rename
        the imported one (when necessary).

        For example, converts 'Comedy' to 'Comedy (2)'.

        Args:

            name (str): The name of the imported channel/playlist/folder

        Return values:

            The converted name

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 7219 rename_imported_container')

        count = 1
        while True:

            count += 1
            new_name = name + ' (' + str(count) + ')'

            if not new_name in self.media_name_dict:
                return new_name


    # (Interact with media data objects)


    def watch_video_in_player(self, video_obj):

        """Called by callback in
        mainwin.MainWin.on_video_catalogue_watch_video() and
        mainwin.ComplexCatalogueItem.on_click_watch_player_label().

        Also called by self.announce_video_download().

        Watch a video using the system's default media player, first checking
        that a file actually exists.

        Args:

            video_obj (media.Video): The video to watch

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 7252 watch_video_in_player')

        path = os.path.abspath(
            os.path.join(
                self.downloads_dir,
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
            utils.open_file(path)


    def download_watch_videos(self, video_list, watch_flag=True):

        """Called by callbacks in
        mainwin.ComplexCatalogueItem.on_click_watch_player_label(),
        mainwin.MainWin.on_video_catalogue_dl_and_watch() and
        mainwin.MainWin.on_video_catalogue_dl_and_watch_multi().

        Download the specified videos and, when they have been downloaded,
        launch them in the system's default media player.

        Args:

            video_list (list): List of media.Video objects to download and
                watch

            watch_flag (bool): If False, the video(s) are not launched in the
                system's default media player after being downloaded

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 7297 download_watch_videos')

        # Sanity check: this function is only for videos
        for video_obj in video_list:
            if not isinstance(video_obj, media.Video):
                return self.system_error(
                    127,
                    'Download and watch video request failed sanity check',
                )

        # Add the video to the list of videos to be launched in the system's
        #   default media player, the next time a download operation finishes
        if watch_flag:
            for video_obj in video_list:
                self.watch_after_dl_list.append(video_obj)

        if self.download_manager_obj:

            # Download operation already in progress. Add these videos to its
            #   list
            for video_obj in video_list:
                download_item_obj \
                = self.download_manager_obj.download_list_obj.create_item(
                    video_obj,
                    True,
                )

                if download_item_obj:

                    # Add a row to the Progress List
                    self.main_win_obj.progress_list_add_row(
                        download_item_obj.item_id,
                        video_obj,
                    )

        else:

            # Start a new download operation to download this video
            self.download_manager_start(False, False, video_list)


    # (Options manager objects)


    def clone_general_options_manager(self, data_list):

        """Called by dialogue.on_clicked(), which was in turn called by
        config.OptionsEditWin.on_clone_options_clicked().

        (Not called by self.apply_download_options(), which can handle its own
        cloning).

        Clones the options from the General Options manager into the specified
        download options manager.reset_options_manager

        Args:

            data_list (list): List of values supplied by the dialogue window.
                The first is the edit window for the download options object
                (which must be reset). The second value is the download options
                manager object, into which new options will be cloned.

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 7362 clone_general_options_manager')

        edit_win_obj = data_list.pop(0)
        options_obj = data_list.pop(0)

        # Clone values from the general download options manager
        options_obj.clone_options(self.general_options_obj)
        # Reset the edit window to display the new (cloned) values
        edit_win_obj.reset_with_new_edit_obj(options_obj)


    def reset_options_manager(self, data_list):

        """Called by dialogue.on_clicked(), which was in turn called by
        config.OptionsEditWin.on_reset_options_clicked().

        Resets the specified download options manager object, setting its
        options to their default values.

        Args:

            data_list (list): List of values supplied by the dialogue window.
                The first is the edit window for the download options object
                (which must be reset). The second optional value is the media
                data object to which the download options object belongs.

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 7391 reset_options_manager')

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


    # Callback class methods


    # (Timers)


    def script_slow_timer_callback(self):

        """Called by GObject timer created by self.start().

        Once a minute, check whether it's time to perform a scheduled 'Download
        all' or 'Check all' operation and, if so, perform it.

        Returns:

            1 to keep the timer going, or None to halt it

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 7435 script_slow_timer_callback')

        if not self.disable_load_save_flag \
        and not self.current_manager_obj \
        and not self.main_win_obj.config_win_list:

            if self.scheduled_dl_mode == 'scheduled':

                wait_time = self.scheduled_dl_wait_hours * 3600
                if (self.scheduled_dl_last_time + wait_time) < time.time():
                    self.download_manager_start(
                        False,      # 'Download all'
                        True,       # This function is the calling function
                    )

            elif self.scheduled_check_mode == 'scheduled':

                wait_time = self.scheduled_check_wait_hours * 3600
                if (self.scheduled_check_last_time + wait_time) < time.time():
                    self.download_manager_start(
                        True,       # 'Check all'
                        True,       # This function is the calling function
                    )

        # Return 1 to keep the timer going
        return 1


    def script_fast_timer_callback(self):

        """Called by GObject timer created by self.start().

        Once a second, check whether there are any mainwin.Catalogue objects to
        add to the Video Catalogue and, if so, add them.

        Returns:

            1 to keep the timer going, or None to halt it

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 7436 script_fast_timer_callback')

        self.main_win_obj.video_catalogue_retry_insert_items()

        # Return 1 to keep the timer going
        return 1


    def dl_timer_callback(self):

        """Called by GObject timer created by self.download_manager_start().

        During a download operation, a GObject timer runs, so that the Progress
        Tab and Output Tab can be updated at regular intervals.

        There is also a delay between the instant at which youtube-dl reports a
        video file has been downloaded, and the instant at which it appears in
        the filesystem. The timer checks for newly-existing files at regular
        intervals, too.

        During download operations, youtube-dl output is temporarily stored
        (because Gtk widgets cannot be updated from within a thread). This
        function calls  mainwin.MainWin.output_tab_update_pages()  to display
        that output in the Output Tab.

        If required, this function periodically checks whether the device
        containing self.data_dir is running out of space (and halts the
        operation, if so.)

        Returns:

            1 to keep the timer going, or None to halt it

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 7491 dl_timer_callback')

        # Periodically check (if required) whether the device is running out of
        #   disk space
        if self.dl_timer_disk_space_check_time is None:
            # First check occurs 60 seconds after the operation begins
            self.dl_timer_disk_space_check_time \
            = time.time() + self.dl_timer_disk_space_time

        elif self.dl_timer_disk_space_check_time < time.time():

            self.dl_timer_disk_space_check_time \
            = time.time() + self.dl_timer_disk_space_time

            disk_space = utils.disk_get_free_space(self.data_dir)

            if (
                self.disk_space_stop_flag \
                and self.disk_space_stop_limit != 0 \
                and disk_space <= self.disk_space_stop_limit
            ) or disk_space < self.disk_space_abs_limit:

                # Stop the download operation
                self.system_error(
                    133,
                    'Download operation halted because the device is running' \
                    + ' out of space',
                )

                self.download_manager_obj.stop_download_operation()
                # Return 1 to keep the timer going, which allows the operation
                #   to finish naturally
                return 1

        # Disk space check complete, now update main window widgets
        if self.dl_timer_check_time is None:
            self.main_win_obj.progress_list_display_dl_stats()
            self.main_win_obj.results_list_update_row()
            self.main_win_obj.output_tab_update_pages()
            if self.progress_list_hide_flag:
                self.main_win_obj.progress_list_check_hide_rows()

            # Download operation still in progress, return 1 to keep the timer
            #   going
            return 1

        elif self.dl_timer_check_time > time.time():
            self.main_win_obj.progress_list_display_dl_stats()
            self.main_win_obj.results_list_update_row()
            self.main_win_obj.output_tab_update_pages()
            if self.progress_list_hide_flag:
                self.main_win_obj.progress_list_check_hide_rows()

            if self.main_win_obj.results_list_temp_list:
                # Not all downloaded files confirmed to exist yet, so return 1
                #   to keep the timer going a little longer
                return 1

        # The download operation has finished. The call to
        #   self.download_manager_finished() destroys the timer
        self.download_manager_finished()


    def update_timer_callback(self):

        """Called by GObject timer created by self.update_manager_start().

        During an update operation, a GObject timer runs, so that the Output
        Tab can be updated at regular intervals.

        For the benefit of systems with Gtk < 3.24, the timer continues running
        for a few seconds at the end of the update operation.

        During update operations, messages generated by updates.UpdateManager
        are temporarily stored (because Gtk widgets cannot be updated from
        within a thread). This function calls
        mainwin.MainWin.output_tab_update_pages() to display those messages in
        the Output Tab.

        Returns:

            1 to keep the timer going

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 7573 update_timer_callback')

        if self.update_timer_check_time is None:

            self.main_win_obj.output_tab_update_pages()
            # Update operation still in progress, return 1 to keep the timer
            #   going
            return 1

        elif self.update_timer_check_time > time.time():

            self.main_win_obj.output_tab_update_pages()
            # Cooldown time not yet finished, return 1 to keep the timer going
            return 1

        else:
            # The update operation has finished. The call to
            #   self.update_manager_finished() destroys the timer
            self.update_manager_finished()


    def refresh_timer_callback(self):

        """Called by GObject timer created by self.refresh_manager_start().

        During a refresh operation, a GObject timer runs, so that the Output
        Tab can be updated at regular intervals.

        For the benefit of systems with Gtk < 3.24, the timer continues running
        for a few seconds at the end of the refresh operation.

        During refresh operations, messages generated by refresh.RefreshManager
        are temporarily stored (because Gtk widgets cannot be updated from
        within a thread). This function calls
        mainwin.MainWin.output_tab_update_pages() to display those messages in
        the Output Tab.

        Returns:

            1 to keep the timer going

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 7617 refresh_timer_callback')

        if self.refresh_timer_check_time is None:

            self.main_win_obj.output_tab_update_pages()
            # Refresh operation still in progress, return 1 to keep the timer
            #   going
            return 1

        elif self.refresh_timer_check_time > time.time():

            self.main_win_obj.output_tab_update_pages()
            # Cooldown time not yet finished, return 1 to keep the timer going
            return 1

        else:
            # The refresh operation has finished. The call to
            #   self.refresh_manager_finished() destroys the timer
            self.refresh_manager_finished()


    # (Menu item and toolbar button callbacks)


    def on_button_find_date(self, action, par):

        """Called from a callback in self.do_startup().

        Changes the Video Catalogue page to the first one containing a video
        whose upload time is the first one on or after date specified by the
        user.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 7658 on_button_find_date')

        # Sanity check
        if not self.main_win_obj.video_catalogue_dict:
            return self.system_error(
                128,
                'Find videos by date request failed sanity check',
            )

        # Prompt the user for a new calendar date
        dialogue_win = mainwin.CalendarDialogue(self.main_win_obj)
        response = dialogue_win.run()

        # Retrieve user choices from the dialogue window, before destroying it
        if response == Gtk.ResponseType.OK:
            date_tuple = dialogue_win.calendar.get_date()

        dialogue_win.destroy()

        if response == Gtk.ResponseType.OK and date_tuple:

            year = date_tuple[0]            # e.g. 2011
            month = date_tuple[1] + 1       # Values in range 0-11
            day = date_tuple[2]             # Values in range 1-31

            # Convert the specified date into the epoch time at the start of
            #   that day
            epoch_time = datetime.datetime(year, month, day, 0, 0).timestamp()

            # Get the channel, playlist or folder currently visible in the
            #   Video Catalogue
            dbid = self.media_name_dict[self.main_win_obj.video_index_current]
            container_obj = self.media_reg_dict[dbid]

            count = 0
            for child_obj in container_obj.child_list:

                if isinstance(child_obj, media.Video) \
                and child_obj.upload_time is not None \
                and child_obj.upload_time < epoch_time:
                    break

                else:
                    count += 1

            # Find the corresponding page in the Video Catalogue...
            page_num = math.ceil(count / self.catalogue_page_size)
            # ...and make it visible
            self.main_win_obj.video_catalogue_redraw_all(
                self.main_win_obj.video_index_current,
                page_num,
                True,           # Reset scrollbars
            )


    def on_button_first_page(self, action, par):

        """Called from a callback in self.do_startup().

        Changes the Video Catalogue page to the first one.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 7728 on_button_first_page')

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
            utils.debug_time('app 7751 on_button_last_page')

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
            utils.debug_time('app 7774 on_button_next_page')

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
            utils.debug_time('app 7797 on_button_previous_page')

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
            utils.debug_time('app 7820 on_button_scroll_down')

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
            utils.debug_time('app 7841 on_button_scroll_up')

        self.main_win_obj.catalogue_scrolled.get_vadjustment().set_value(0)


    def on_button_stop_operation(self, action, par):

        """Called from a callback in self.do_startup().

        Stops the current download/update/refresh operation.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 7861 on_button_stop_operation')

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
            utils.debug_time('app 7890 on_button_switch_view')

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
            utils.debug_time('app 7927 on_menu_about')

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
            utils.debug_time('app 7967 on_menu_about_close')

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
            utils.debug_time('app 7988 on_menu_add_channel')

        keep_open_flag = True
        dl_sim_flag = False
        monitor_flag = False

        # If a folder (but not a channel/playlist) is selected in the Video
        #   Index, use that as the dialogue window's suggested parent folder
        suggest_parent_name = None
        if self.main_win_obj.video_index_current:
            dbid = self.media_name_dict[self.main_win_obj.video_index_current]
            container_obj = self.media_reg_dict[dbid]
            if isinstance(container_obj, media.Folder) \
            and not container_obj.fixed_flag \
            and not container_obj.restrict_flag:
                suggest_parent_name = container_obj.name

        while keep_open_flag:

            dialogue_win = mainwin.AddChannelDialogue(
                self.main_win_obj,
                suggest_parent_name,
                dl_sim_flag,
                monitor_flag,
            )

            response = dialogue_win.run()

            # Retrieve user choices from the dialogue window...
            name = dialogue_win.entry.get_text()
            source = dialogue_win.entry2.get_text()
            dl_sim_flag = dialogue_win.radiobutton2.get_active()
            monitor_flag = dialogue_win.checkbutton.get_active()

            # ...and find the name of the parent media data object (a
            #   media.Folder), if one was specified...
            parent_name = None
            if hasattr(dialogue_win, 'parent_name'):
                parent_name = dialogue_win.parent_name
            elif suggest_parent_name is not None:
                parent_name = suggest_parent_name

            # ...and halt the timer, if running
            if dialogue_win.clipboard_timer_id:
                GObject.source_remove(dialogue_win.clipboard_timer_id)

            # ...before destroying the dialogue window
            dialogue_win.destroy()

            if response != Gtk.ResponseType.OK:

                keep_open_flag = False

            else:

                if name is None or re.match('^\s*$', name):

                    keep_open_flag = False
                    self.dialogue_manager_obj.show_msg_dialogue(
                        'You must give the channel a name',
                        'error',
                        'ok',
                    )

                elif not self.check_container_name_is_legal(name):

                    keep_open_flag = False
                    self.dialogue_manager_obj.show_msg_dialogue(
                        'The name \'' + name + '\' is not allowed',
                        'error',
                        'ok',
                    )

                elif not source or not utils.check_url(source):

                    keep_open_flag = False
                    self.dialogue_manager_obj.show_msg_dialogue(
                        'You must enter a valid URL',
                        'error',
                        'ok',
                    )

                elif name in self.media_name_dict:

                    # Another channel, playlist or folder is already using this
                    #   name
                    keep_open_flag = False
                    self.reject_container_name(name)

                else:

                    keep_open_flag = self.dialogue_keep_open_flag

                    # Remove leading/trailing whitespace from the name; make
                    #   sure the name is not excessively long
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

                        if self.dialogue_keep_open_flag \
                        and self.dialogue_keep_container_flag:
                            suggest_parent_name = parent_name

                    # Create the new channel
                    channel_obj = self.add_channel(
                        name,
                        parent_obj,
                        source,
                        dl_sim_flag,
                    )

                    # Add the channel to Video Index
                    if channel_obj:

                        if suggest_parent_name is not None \
                        and suggest_parent_name \
                        == self.main_win_obj.video_index_current:
                            # The channel has been added to the currently
                            #   selected folder; the True argument tells the
                            #   function not to select the channel
                            self.main_win_obj.video_index_add_row(
                                channel_obj,
                                True,
                            )

                        else:
                            # Do select the new channel
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
            utils.debug_time('app 8124 on_menu_add_folder')

        # If a folder is selected in the Video Index, the dialogue window
        #   should suggest that as the new folder's parent folder
        suggest_parent_name = None
        if self.main_win_obj.video_index_current:
            dbid = self.media_name_dict[self.main_win_obj.video_index_current]
            container_obj = self.media_reg_dict[dbid]
            if isinstance(container_obj, media.Folder) \
            and not container_obj.fixed_flag \
            and not container_obj.restrict_flag:
                suggest_parent_name = container_obj.name

        dialogue_win = mainwin.AddFolderDialogue(
            self.main_win_obj,
            suggest_parent_name,
        )

        response = dialogue_win.run()

        # Retrieve user choices from the dialogue window...
        name = dialogue_win.entry.get_text()
        dl_sim_flag = dialogue_win.radiobutton2.get_active()

        # ...and find the name of the parent media data object (a
        #   media.Folder), if one was specified...
        parent_name = None
        if hasattr(dialogue_win, 'parent_name'):
            parent_name = dialogue_win.parent_name

        # ...before destroying the dialogue window
        dialogue_win.destroy()

        if response == Gtk.ResponseType.OK:

            if name is None or re.match('^\s*$', name):

                self.dialogue_manager_obj.show_msg_dialogue(
                    'You must give the folder a name',
                    'error',
                    'ok',
                )

            elif not self.check_container_name_is_legal(name):

                self.dialogue_manager_obj.show_msg_dialogue(
                    'The name \'' + name + '\' is not allowed',
                    'error',
                    'ok',
                )

            elif name in self.media_name_dict:

                # Another channel, playlist or folder is already using this
                #   name
                self.reject_container_name(name)

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
                folder_obj = self.add_folder(name, parent_obj, dl_sim_flag)

                # Add the folder to the Video Index
                if folder_obj:

                    if self.main_win_obj.video_index_current:
                        # The new folder has been added inside the currently
                        #   selected folder; the True argument tells the
                        #   function not to select the new folder
                        self.main_win_obj.video_index_add_row(
                            folder_obj,
                            True,
                        )

                    else:
                        # Do select the new folder
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
            utils.debug_time('app 8223 on_menu_add_playlist')

        keep_open_flag = True
        dl_sim_flag = False
        monitor_flag = False

        # If a folder (but not a channel/playlist) is selected in the Video
        #   Index, use that as the dialogue window's suggested parent folder
        suggest_parent_name = None
        if self.main_win_obj.video_index_current:
            dbid = self.media_name_dict[self.main_win_obj.video_index_current]
            container_obj = self.media_reg_dict[dbid]
            if isinstance(container_obj, media.Folder) \
            and not container_obj.fixed_flag \
            and not container_obj.restrict_flag:
                suggest_parent_name = container_obj.name

        while keep_open_flag:

            dialogue_win = mainwin.AddPlaylistDialogue(
                self.main_win_obj,
                suggest_parent_name,
                dl_sim_flag,
                monitor_flag,
            )

            response = dialogue_win.run()

            # Retrieve user choices from the dialogue window...
            name = dialogue_win.entry.get_text()
            source = dialogue_win.entry2.get_text()
            dl_sim_flag = dialogue_win.radiobutton2.get_active()
            monitor_flag = dialogue_win.checkbutton.get_active()

            # ...and find the name of the parent media data object (a
            #   media.Folder), if one was specified...
            parent_name = None
            if hasattr(dialogue_win, 'parent_name'):
                parent_name = dialogue_win.parent_name
            elif suggest_parent_name is not None:
                parent_name = suggest_parent_name

            # ...and halt the timer, if running
            if dialogue_win.clipboard_timer_id:
                GObject.source_remove(dialogue_win.clipboard_timer_id)

            # ...before destroying the dialogue window
            dialogue_win.destroy()

            if response != Gtk.ResponseType.OK:

                keep_open_flag = False

            else:

                if name is None or re.match('^\s*$', name):

                    keep_open_flag = False
                    self.dialogue_manager_obj.show_msg_dialogue(
                        'You must give the playlist a name',
                        'error',
                        'ok',
                    )

                elif not self.check_container_name_is_legal(name):

                    keep_open_flag = False
                    self.dialogue_manager_obj.show_msg_dialogue(
                        'The name \'' + name + '\' is not allowed',
                        'error',
                        'ok',
                    )

                elif not source or not utils.check_url(source):

                    keep_open_flag = False
                    self.dialogue_manager_obj.show_msg_dialogue(
                        'You must enter a valid URL',
                        'error',
                        'ok',
                    )

                elif name in self.media_name_dict:

                    # Another channel, playlist or folder is already using this
                    #   name
                    keep_open_flag = False
                    self.reject_container_name(name)

                else:

                    keep_open_flag = self.dialogue_keep_open_flag

                    # Remove leading/trailing whitespace from the name; make
                    #   sure the name is not excessively long
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

                        if self.dialogue_keep_open_flag \
                        and self.dialogue_keep_container_flag:
                            suggest_parent_name = parent_name

                    # Create the playlist
                    playlist_obj = self.add_playlist(
                        name,
                        parent_obj,
                        source,
                        dl_sim_flag,
                    )

                    # Add the playlist to the Video Index
                    if playlist_obj:

                        if suggest_parent_name is not None \
                        and suggest_parent_name \
                        == self.main_win_obj.video_index_current:
                            # The playlist has been added to the currently
                            #   selected folder; the True argument tells the
                            #   function not to select the playlist
                            self.main_win_obj.video_index_add_row(
                                playlist_obj,
                                True,
                            )

                        else:
                            # Do select the new playlist
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
            utils.debug_time('app 8358 on_menu_add_video')

        dialogue_win = mainwin.AddVideoDialogue(self.main_win_obj)
        response = dialogue_win.run()

        # Retrieve user choices from the dialogue window...
        text = dialogue_win.textbuffer.get_text(
            dialogue_win.textbuffer.get_start_iter(),
            dialogue_win.textbuffer.get_end_iter(),
            False,
        )

        dl_sim_flag = dialogue_win.radiobutton2.get_active()

        # ...and find the parent media data object (a media.Channel,
        #   media.Playlist or media.Folder)...
        parent_name = self.fixed_misc_folder.name
        if hasattr(dialogue_win, 'parent_name'):
            parent_name = dialogue_win.parent_name

        dbid = self.media_name_dict[parent_name]
        parent_obj = self.media_reg_dict[dbid]

        # ...and halt the timer, if running
        if dialogue_win.clipboard_timer_id:
            GObject.source_remove(dialogue_win.clipboard_timer_id)

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
                    self.add_video(parent_obj, line, dl_sim_flag)

            # In the Video Index, select the parent media data object, which
            #   updates both the Video Index and the Video Catalogue
            self.main_win_obj.video_index_select_row(parent_obj)

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


    def on_menu_change_db(self, action, par):

        """Called from a callback in self.do_startup().

        Opens the preference window at the right tab, so that the user can
        switch databases.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 8359 on_menu_change_db')

        config.SystemPrefWin(self, True)


    def on_menu_check_all(self, action, par):

        """Called from a callback in self.do_startup().

        Call a function to start a new download operation (if allowed).

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 8438 on_menu_check_all')

        self.download_manager_start(True)


    def on_menu_close_tray(self, action, par):

        """Called from a callback in self.do_startup().

        Closes the main window to the system tray.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 8439 on_menu_close_tray')

        self.main_win_obj.toggle_visibility()


    def on_menu_download_all(self, action, par):

        """Called from a callback in self.do_startup().

        Call a function to start a new download operation (if allowed).

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 8458 on_menu_download_all')

        self.download_manager_start(False)


    def on_menu_export_db(self, action, par):

        """Called from a callback in self.do_startup().

        Exports data from the Tartube database.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 8478 on_menu_export_db')

        self.export_from_db( [] )


    def on_menu_general_options(self, action, par):

        """Called from a callback in self.do_startup().

        Opens an edit window for the General Options Manager.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 8498 on_menu_general_options')

        config.OptionsEditWin(self, self.general_options_obj, None)


    def on_menu_go_website(self, action, par):

        """Called from a callback in self.do_startup().

        Opens the Tartube website.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 8518 on_menu_go_website')

        utils.open_file(__main__.__website__)


    def on_menu_import_json(self, action, par):

        """Called from a callback in self.do_startup().

        Imports data into from a JSON export file into the Tartube database.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 8538 on_menu_import_json')

        self.import_into_db(True)


    def on_menu_import_plain_text(self, action, par):

        """Called from a callback in self.do_startup().

        Imports data into from a plain text export file into the Tartube
        database.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 8559 on_menu_import_plain_text')

        self.import_into_db(False)


    def on_menu_install_ffmpeg(self, action, par):

        """Called from a callback in self.do_startup().

        Start an update operation to install FFmpeg (on MS Windows only).

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 8579 on_menu_install_ffmpeg')

        # The True argument means 'install FFmpeg, not youtube-dl'
        self.update_manager_start(True)


    def on_menu_refresh_db(self, action, par):

        """Called from a callback in self.do_startup().

        Starts a refresh operation.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 8600 on_menu_refresh_db')

        self.refresh_manager_start()


    def on_menu_save_all(self, action, par):

        """Called from a callback in self.do_startup().

        Save the config file, and then the Tartube database.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 8601 on_menu_save_all')

        if not self.disable_load_save_flag:
            self.save_config()
        if not self.disable_load_save_flag:
            self.save_db()

        # Show a dialogue window for confirmation (unless file load/save has
        #   been disabled, in which case a dialogue has already appeared)
        if not self.disable_load_save_flag:

            self.dialogue_manager_obj.show_msg_dialogue(
                'Data saved',
                'info',
                'ok',
            )


    def on_menu_save_db(self, action, par):

        """Called from a callback in self.do_startup().

        Save the Tartube database.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 8620 on_menu_save_db')

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
            utils.debug_time('app 8650 on_menu_show_hidden')

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
            utils.debug_time('app 8677 on_menu_system_preferences')

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
            utils.debug_time('app 8698 on_menu_test')

        # Add media data objects for testing: videos, channels, playlists and/
        #   or folders
        testing.add_test_media(self)

        # Clicking the Test button more than once just adds illegal duplicate
        #   channels/playlists/folders (and non-illegal duplicate videos), so
        #   just disable the button and the menu item
        self.main_win_obj.desensitise_test_widgets()

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
            utils.debug_time('app 8735 on_menu_update_ytdl')

        # The False argument means 'install youtube-dl, not FFmpeg'
        self.update_manager_start(False)


    def on_menu_quit(self, action, par):

        """Called from a callback in self.do_startup().

        Terminates the Tartube app.

        Args:

            action (Gio.SimpleAction): Object generated by Gio

            par (None): Ignored

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 8756 on_menu_quit')

        self.stop()


    # (Callback support functions)


    def reject_container_name(self, name):

        """Called by self.on_menu_add_channel(), .on_menu_add_playlist()
        and .on_menu_add_folder().

        If the user specifies a name for a channel, playlist or folder that's
        already in use by a channel, playlist or folder, tell them why they
        can't use it.

        Args:

            name (str): The name specified by the user

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 8780 reject_container_name')

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


    def set_allow_ytdl_archive_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 8807 set_allow_ytdl_archive_flag')

        if not flag:
            self.allow_ytdl_archive_flag = False
        else:
            self.allow_ytdl_archive_flag = True


    def set_apply_json_timeout_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 8818 set_apply_json_timeout_flag')

        if not flag:
            self.apply_json_timeout_flag = False
        else:
            self.apply_json_timeout_flag = True


    def set_auto_clone_options_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 8829 set_auto_clone_options_flag')

        if not flag:
            self.auto_clone_options_flag = False
        else:
            self.auto_clone_options_flag = True


    def set_auto_delete_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 8840 set_auto_delete_flag')

        if not flag:
            self.auto_delete_flag = False
        else:
            self.auto_delete_flag = True


    def set_auto_delete_watched_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 8851 set_auto_delete_watched_flag')

        if not flag:
            self.auto_delete_watched_flag = False
        else:
            self.auto_delete_watched_flag = True


    def set_auto_delete_days(self, days):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 8862 set_auto_delete_days')

        self.auto_delete_days = days


    def set_auto_expand_video_index_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 8870 set_auto_expand_video_index_flag')

        if not flag:
            self.auto_expand_video_index_flag = False
        else:
            self.auto_expand_video_index_flag = True


    def set_autostop_size_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 8871 set_autostop_size_flag')

        if not flag:
            self.autostop_size_flag = False
        else:
            self.autostop_size_flag = True


    def set_autostop_size_unit(self, value):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 8872 set_autostop_size_unit')

        self.autostop_size_unit = value


    def set_autostop_size_value(self, value):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 8873 set_autostop_size_value')

        self.autostop_size_value = value


    def set_autostop_time_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 8874 set_autostop_time_flag')

        if not flag:
            self.autostop_time_flag = False
        else:
            self.autostop_time_flag = True


    def set_autostop_time_unit(self, value):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 8875 set_autostop_time_unit')

        self.autostop_time_unit = value


    def set_autostop_time_value(self, value):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 8876 set_autostop_time_value')

        self.autostop_time_value = value


    def set_autostop_videos_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 8877 set_autostop_videos_flag')

        if not flag:
            self.autostop_videos_flag = False
        else:
            self.autostop_videos_flag = True


    def set_autostop_videos_value(self, value):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 8878 set_autostop_videos_value')

        self.autostop_videos_value = value


    def set_bandwidth_default(self, value):

        """Called by mainwin.MainWin.on_spinbutton2_changed().

        Sets the new bandwidth limit. If a download operation is in progress,
        the new value is applied to the next download job.

        Args:

            value (int): The new bandwidth limit

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 8892 set_bandwidth_default')

        if value < self.bandwidth_min or value > self.bandwidth_max:
            return self.system_error(
                129,
                'Set bandwidth request failed sanity check',
            )

        self.bandwidth_default = value


    def set_bandwidth_apply_flag(self, flag):

        """Called by mainwin.MainWin.on_checkbutton2_changed().

        Applies or releases the bandwidth limit. If a download operation is in
        progress, the new setting is applied to the next download job.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 8912 set_bandwidth_apply_flag')

        if not flag:
            self.bandwidth_apply_flag = False
        else:
            self.bandwidth_apply_flag = True


    def set_catalogue_page_size(self, size):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 8923 set_catalogue_page_size')

        self.catalogue_page_size = size


    def set_close_to_tray_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 8931 set_close_to_tray_flag')

        if not flag:
            self.close_to_tray_flag = False
        else:
            self.close_to_tray_flag = True


    def set_complex_index_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 8942 set_complex_index_flag')

        if not flag:
            self.complex_index_flag = False
        else:
            self.complex_index_flag = True


    def reset_data_dir(self):

        """Called by mainwin.MountDriveDialogue.on_default_clicked() only;
        everything else should call self.switch_db().

        The call to this function resets the value of self.data_dir without
        actually loading the database.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 8960 reset_data_dir')

        self.data_dir = self.default_data_dir


    def set_db_backup_mode(self, value):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 8969 set_db_backup_mode')

        self.db_backup_mode = value


    def set_delete_on_shutdown_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 8976 set_delete_on_shutdown_flag')

        if not flag:
            self.delete_on_shutdown_flag = False
        else:
            self.delete_on_shutdown_flag = True


    def set_dialogue_copy_clipboard_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 8987 set_dialogue_copy_clipboard_flag')

        if not flag:
            self.dialogue_copy_clipboard_flag = False
        else:
            self.dialogue_copy_clipboard_flag = True


    def set_dialogue_keep_open_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 8998 set_dialogue_keep_open_flag')

        if not flag:
            self.dialogue_keep_open_flag = False
        else:
            self.dialogue_keep_open_flag = True


    def set_disable_dl_all_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9009 set_disable_dl_all_flag')

        if not flag:
            self.disable_dl_all_flag = False
            self.main_win_obj.enable_dl_all_buttons()

        else:
            self.disable_dl_all_flag = True
            self.main_win_obj.disable_dl_all_buttons()


    def set_disk_space_stop_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9023 set_disk_space_stop_flag')

        if not flag:
            self.disk_space_stop_flag = False
        else:
            self.disk_space_stop_flag = True


    def set_disk_space_stop_limit(self, value):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9034 set_disk_space_stop_limit')

        self.disk_space_stop_limit = value


    def set_disk_space_warn_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9042 set_disk_space_warn_flag')

        if not flag:
            self.disk_space_warn_flag = False
        else:
            self.disk_space_warn_flag = True


    def set_disk_space_warn_limit(self, value):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9053 set_disk_space_warn_limit')

        self.disk_space_warn_limit = value


    def set_ffmpeg_path(self, path):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9061 set_ffmpeg_path')

        self.ffmpeg_path = path


    def set_gtk_emulate_broken_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9062 set_gtk_emulate_broken_flag')

        if not flag:
            self.gtk_emulate_broken_flag = False
        else:
            self.gtk_emulate_broken_flag = True


    def set_ignore_child_process_exit_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9069 set_ignore_child_process_exit_flag')

        if not flag:
            self.ignore_child_process_exit_flag = False
        else:
            self.ignore_child_process_exit_flag = True


    def set_ignore_custom_msg_list(self, custom_list):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9070 set_ignore_custom_msg_list')

        self.ignore_custom_msg_list = custom_list.copy()


    def set_ignore_custom_regex_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9071 set_ignore_custom_regex_flag')

        if not flag:
            self.ignore_custom_regex_flag = False
        else:
            self.ignore_custom_regex_flag = True


    def set_ignore_data_block_error_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9116 set_ignore_data_block_error_flag')

        if not flag:
            self.ignore_data_block_error_flag = False
        else:
            self.ignore_data_block_error_flag = True


    def set_ignore_http_404_error_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9115 set_ignore_http_404_error_flag')

        if not flag:
            self.ignore_http_404_error_flag = False
        else:
            self.ignore_http_404_error_flag = True


    def set_ignore_merge_warning_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9080 set_ignore_merge_warning_flag')

        if not flag:
            self.ignore_merge_warning_flag = False
        else:
            self.ignore_merge_warning_flag = True


    def set_ignore_missing_format_error_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9117 set_ignore_missing_format_error_flag')

        if not flag:
            self.ignore_missing_format_error_flag = False
        else:
            self.ignore_missing_format_error_flag = True


    def set_ignore_no_annotations_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9091 set_ignore_no_annotations_flag')

        if not flag:
            self.ignore_no_annotations_flag = False
        else:
            self.ignore_no_annotations_flag = True


    def set_ignore_no_subtitles_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9102 set_ignore_no_subtitles_flag')

        if not flag:
            self.ignore_no_subtitles_flag = False
        else:
            self.ignore_no_subtitles_flag = True


    def set_ignore_yt_age_restrict_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9113 set_ignore_yt_age_restrict_flag')

        if not flag:
            self.ignore_yt_age_restrict_flag = False
        else:
            self.ignore_yt_age_restrict_flag = True


    def set_ignore_yt_copyright_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9114 set_ignore_yt_copyright_flag')

        if not flag:
            self.ignore_yt_copyright_flag = False
        else:
            self.ignore_yt_copyright_flag = True


    def set_ignore_yt_uploader_deleted_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9118 set_ignore_yt_uploader_deleted_flag')

        if not flag:
            self.ignore_yt_uploader_deleted_flag = False
        else:
            self.ignore_yt_uploader_deleted_flag = True


    def set_match_first_chars(self, num_chars):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9124 set_match_first_chars')

        self.match_first_chars = num_chars


    def set_match_ignore_chars(self, num_chars):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9132 set_match_ignore_chars')

        self.match_ignore_chars = num_chars


    def set_match_method(self, method):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9140 set_match_method')

        self.match_method = method


    def set_num_worker_apply_flag(self, flag):

        """Called by mainwin.MainWin.on_checkbutton_changed().

        Applies or releases the simultaneous download limit. If a download
        operation is in progress, the new setting is applied to the next
        download job.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9155 set_num_worker_apply_flag')

        if not flag:
            self.bandwidth_apply_flag = False
        else:
            self.bandwidth_apply_flag = True


    def set_num_worker_default(self, value):

        """Called by mainwin.MainWin.on_spinbutton_changed() and
        .on_checkbutton_changed().

        Sets the new value for the number of simultaneous downloads allowed. If
        a download operation is in progress, informs the download manager
        object, so the number of download workers can be adjusted. Also
        increases the number of pages in the Output Tab, if necessary.

        Args:

            value (int): The new number of simultaneous downloads

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9180 set_num_worker_default')

        if value < self.num_worker_min or value > self.num_worker_max:
            return self.system_error(
                130,
                'Set simultaneous downloads request failed sanity check',
            )

        old_value = self.num_worker_default
        self.num_worker_default = value

        if old_value != value and self.download_manager_obj:
            self.download_manager_obj.change_worker_count(value)

        if value > self.main_win_obj.output_page_count:
            self.main_win_obj.output_tab_setup_pages()


    def set_operation_auto_update_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9201 set_operation_auto_update_flag')

        if not flag:
            self.operation_auto_update_flag = False
        else:
            self.operation_auto_update_flag = True


    def set_operation_check_limit(self, value):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9212 set_operation_check_limit')

        self.operation_check_limit = value


    def set_operation_convert_mode(self, mode):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9220 set_operation_convert_mode')

        if mode == 'disable' or mode == 'multi' or mode == 'channel' \
        or mode == 'playlist':
            self.operation_convert_mode = mode


    def set_operation_dialogue_mode(self, mode):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9221 set_operation_dialogue_mode')

        if mode == 'default' or mode == 'desktop' or mode == 'dialogue':
            self.operation_dialogue_mode = mode


    def set_operation_download_limit(self, value):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9229 set_operation_download_limit')

        self.operation_download_limit = value


    def set_operation_error_show_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9230 set_operation_error_show_flag')

        if not flag:
            self.operation_error_show_flag = False
        else:
            self.operation_error_show_flag = True


    def set_operation_halted_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9237 set_operation_halted_flag')

        if not flag:
            self.operation_halted_flag = False
        else:
            self.operation_halted_flag = True


    def set_operation_limit_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9248 set_operation_limit_flag')

        if not flag:
            self.operation_limit_flag = False
        else:
            self.operation_limit_flag = True


    def set_operation_save_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9259 set_operation_save_flag')

        if not flag:
            self.operation_save_flag = False
        else:
            self.operation_save_flag = True


    def set_operation_warning_show_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9406 set_operation_warning_show_flag')

        if not flag:
            self.operation_warning_show_flag = False
        else:
            self.operation_warning_show_flag = True


    def set_progress_list_hide_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9407 set_progress_list_hide_flag')

        if not flag:
            self.progress_list_hide_flag = False
        else:
            self.progress_list_hide_flag = True
            # If a download operation is in progress, hide any hideable rows
            #   immediately
            if self.download_manager_obj:
                self.main_win_obj.progress_list_check_hide_rows(True)


    def set_refresh_moviepy_timeout(self, value):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9408 set_refresh_moviepy_timeout')

        self.refresh_moviepy_timeout = value


    def set_results_list_reverse_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9278 set_results_list_reverse_flag')

        if not flag:
            self.results_list_reverse_flag = False
        else:
            self.results_list_reverse_flag = True


    def set_scheduled_check_mode(self, value):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9289 set_scheduled_check_mode')

        self.scheduled_check_mode = value


    def set_scheduled_check_wait_hours(self, value):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9297 set_scheduled_check_wait_hours')

        self.scheduled_check_wait_hours = value


    def set_scheduled_dl_mode(self, value):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9305 set_scheduled_dl_mode')

        self.scheduled_dl_mode = value


    def set_scheduled_dl_wait_hours(self, value):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9313 set_scheduled_dl_wait_hours')

        self.scheduled_dl_wait_hours = value


    def set_scheduled_shutdown_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9321 set_scheduled_shutdown_flag')

        if not flag:
            self.scheduled_shutdown_flag = False
        else:
            self.scheduled_shutdown_flag = True


    def set_simple_options_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9332 set_simple_options_flag')

        if not flag:
            self.simple_options_flag = False
        else:
            self.simple_options_flag = True


    def set_show_small_icons_in_index(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9343 set_show_small_icons_in_index')

        if not flag:
            self.show_small_icons_in_index = False
        else:
            self.show_small_icons_in_index = True

        # Redraw the Video Index (and Video Catalogue)
        self.main_win_obj.video_catalogue_reset()
        self.main_win_obj.video_index_reset()
        self.main_win_obj.video_index_populate()


    def set_show_status_icon_flag(self, flag):

        """Called by config.SystemPrefWin.on_show_status_icon_toggled().

        Shows/hides the status icon in the system tray.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9364 set_show_status_icon_flag')

        if not flag:
            self.show_status_icon_flag = False
            if self.status_icon_obj:
                self.status_icon_obj.hide_icon()

        else:
            self.show_status_icon_flag = True
            if self.status_icon_obj:
                self.status_icon_obj.show_icon()


    def set_show_tooltips_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9380 set_show_tooltips_flag')

        if not flag:
            self.show_tooltips_flag = False
            # (The True argument forces the Video Catalogue to be redrawn)
            self.main_win_obj.disable_tooltips(True)

        else:
            self.show_tooltips_flag = True
            self.main_win_obj.enable_tooltips(True)


    def set_system_error_show_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9381 set_system_error_show_flag')

        if not flag:
            self.system_error_show_flag = False
        else:
            self.system_error_show_flag = True


    def set_system_msg_keep_totals_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9395 set_system_msg_keep_totals_flag')

        if not flag:
            self.system_msg_keep_totals_flag = False
        else:
            self.system_msg_keep_totals_flag = True


    def set_system_warning_show_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9406 set_system_warning_show_flag')

        if not flag:
            self.system_warning_show_flag = False
        else:
            self.system_warning_show_flag = True


    def set_toolbar_squeeze_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9417 set_toolbar_squeeze_flag')

        if not flag:
            self.toolbar_squeeze_flag = False
        else:
            self.toolbar_squeeze_flag = True

        if self.main_win_obj and self.main_win_obj.main_toolbar:
            self.main_win_obj.redraw_main_toolbar()


    def set_use_module_moviepy_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9431 set_use_module_moviepy_flag')

        if not flag:
            self.use_module_moviepy_flag = False
        else:
            self.use_module_moviepy_flag = True


    def set_video_res_apply_flag(self, flag):

        """Called by mainwin.MainWin.on_checkbutton2_changed().

        Applies or releases the video resolution limit. If a download operation
        is in progress, the new setting is applied to the next download job.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9448 set_video_res_apply_flag')

        if not flag:
            self.video_res_apply_flag = False
        else:
            self.video_res_apply_flag = True


    def set_video_res_default(self, value):

        """Called by mainwin.MainWin.set_video_res_limit(),
        .on_combobox_changed(), and
        config.SystemPrefWin.on_video_res_combo_changed().

        Sets the new video resolution limit. If a download operation is in
        progress, the new value is applied to the next download job.

        Args:

            value (str): The new video resolution limit (a key in
                formats.VIDEO_RESOLUTION_DICT, e.g. '720p')

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9473 set_video_res_default')

        if not value in formats.VIDEO_RESOLUTION_DICT:
            return self.system_error(
                131,
                'Set video resolution request failed sanity check',
            )

        self.video_res_default = value


    def set_refresh_output_verbose_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9487 set_refresh_output_verbose_flag')

        if not flag:
            self.refresh_output_verbose_flag = False
        else:
            self.refresh_output_verbose_flag = True


    def set_refresh_output_videos_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9498 set_refresh_output_videos_flag')

        if not flag:
            self.refresh_output_videos_flag = False
        else:
            self.refresh_output_videos_flag = True


    def set_ytdl_output_show_summary_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9509 set_ytdl_output_show_summary_flag')

        if not flag:
            self.ytdl_output_show_summary_flag = False
        else:
            self.ytdl_output_show_summary_flag = True


    def set_ytdl_output_start_empty_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9510 set_ytdl_output_start_empty_flag')

        if not flag:
            self.ytdl_output_start_empty_flag = False
        else:
            self.ytdl_output_start_empty_flag = True


    def set_ytdl_output_ignore_json_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9520 set_ytdl_output_ignore_json_flag')

        if not flag:
            self.ytdl_output_ignore_json_flag = False
        else:
            self.ytdl_output_ignore_json_flag = True


    def set_ytdl_output_ignore_progress_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9531 set_ytdl_output_ignore_progress_flag')

        if not flag:
            self.ytdl_output_ignore_progress_flag = False
        else:
            self.ytdl_output_ignore_progress_flag = True


    def set_ytdl_output_stderr_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9542 set_ytdl_output_stderr_flag')

        if not flag:
            self.ytdl_output_stderr_flag = False
        else:
            self.ytdl_output_stderr_flag = True


    def set_ytdl_output_stdout_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9553 set_ytdl_output_stdout_flag')

        if not flag:
            self.ytdl_output_stdout_flag = False
        else:
            self.ytdl_output_stdout_flag = True


    def set_ytdl_output_system_cmd_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9554 set_ytdl_output_system_cmd_flag')

        if not flag:
            self.ytdl_output_system_cmd_flag = False
        else:
            self.ytdl_output_system_cmd_flag = True


    def set_ytdl_path(self, path):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9564 set_ytdl_path')

        self.ytdl_path = path


    def set_ytdl_update_current(self, string):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9572 set_ytdl_update_current')

        self.ytdl_update_current = string


    def set_ytdl_write_ignore_json_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9580 set_ytdl_write_ignore_json_flag')

        if not flag:
            self.ytdl_write_ignore_json_flag = False
        else:
            self.ytdl_write_ignore_json_flag = True


    def set_ytdl_write_ignore_progress_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9591 set_ytdl_write_ignore_progress_flag')

        if not flag:
            self.ytdl_write_ignore_progress_flag = False
        else:
            self.ytdl_write_ignore_progress_flag = True


    def set_ytdl_write_stderr_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9602 set_ytdl_write_stderr_flag')

        if not flag:
            self.ytdl_write_stderr_flag = False
        else:
            self.ytdl_write_stderr_flag = True


    def set_ytdl_write_stdout_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9613 set_ytdl_write_stdout_flag')

        if not flag:
            self.ytdl_write_stdout_flag = False
        else:
            self.ytdl_write_stdout_flag = True


    def set_ytdl_write_system_cmd_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9614 set_ytdl_write_system_cmd_flag')

        if not flag:
            self.ytdl_write_system_cmd_flag = False
        else:
            self.ytdl_write_system_cmd_flag = True


    def set_ytdl_write_verbose_flag(self, flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('app 9624 set_ytdl_write_verbose_flag')

        if not flag:
            self.ytdl_write_verbose_flag = False
        else:
            self.ytdl_write_verbose_flag = True
