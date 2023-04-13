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


"""Refresh operation classes."""


# Import Gtk modules
import gi
from gi.repository import GObject


# Import other modules
import os
import threading
import time


# Import our modules
import formats
import media
import utils
# Use same gettext translations
from mainapp import _


# Classes


class RefreshManager(threading.Thread):

    """Called by mainapp.TartubeApp.refresh_manager_continue().

    Python class to manage the refresh operation, in which the media registry
    is checked against Tartube's data directory and updated as appropriate.

    Args:

        app_obj (mainapp.TartubeApp): The main application

        init_obj (media.Channel, media.Playlist, media.Folder or None): If
            specified, only this media data object is refreshed. If not
            specified, the whole media data registry is refreshed.

    """


    # Standard class methods


    def __init__(self, app_obj, init_obj=None):

        super(RefreshManager, self).__init__()

        # IV list - class objects
        # -----------------------
        # The mainapp.TartubeApp object
        self.app_obj = app_obj
        # The media data object (channel, playlist or folder) to refresh, or
        #   None if the whole media data registry is to be refreshed
        self.init_obj = init_obj


        # IV list - other
        # ---------------
        # Flag set to False if self.stop_refresh_operation() is called, which
        #   halts the operation immediately
        self.running_flag = True

        # The time at which the refresh operation began (in seconds since
        #   epoch)
        self.start_time = int(time.time())
        # The time at which the refresh operation completed (in seconds since
        #   epoch)
        self.stop_time = None
        # The time (in seconds) between iterations of the loop in self.run()
        self.sleep_time = 0.25

        # The number of media data objects refreshed so far...
        self.job_count = 0
        # ...and the total number to refresh (these numbers are displayed in
        #   the progress bar in the Videos tab)
        self.job_total = 0

        # Total number of videos analysed
        self.video_total_count = 0
        # Number of videos matched with a media.Video object in the database
        self.video_match_count = 0
        # Number of videos not matched, and therefore given a new media.Video
        #   object
        self.video_new_count = 0


        # Code
        # ----

        # Let's get this party started!
        self.start()


    # Public class methods


    def run(self):

        """Called as a result of self.__init__().

        Compiles a list of media data objects (channels, playlists and folders)
        to refresh. If self.init_obj is not set, only that channel/playlist/
        folder (and its child channels/playlists/folders) are refreshed;
        otherwise the whole media registry is refreshed.

        Then calls self.refresh_from_default_destination() for each item in the
        list.

        Finally informs the main application that the refresh operation is
        complete.
        """

        # Show information about the refresh operation in the Output tab
        if not self.init_obj:
            self.app_obj.main_win_obj.output_tab_write_stdout(
                1,
                _('Starting refresh operation, analysing whole database'),
            )

        else:

            media_type = self.init_obj.get_type()

            self.app_obj.main_win_obj.output_tab_write_stdout(
                1,
                _('Starting refresh operation, analysing \'{}\'').format(
                    self.init_obj.name,
                ),
            )

        # Compile a list of channels, playlists and folders to refresh (each
        #   one has their own sub-directory inside Tartube's data directory)
        obj_list = []
        if self.init_obj:
            # Add this channel/playlist/folder, and any child channels/
            #   playlists/folders (but not videos, obviously)
            obj_list = self.init_obj.compile_all_containers(obj_list)
        else:
            # Add all channels/playlists/folders in the database
            for dbid in self.app_obj.container_reg_dict.keys():

                obj = self.app_obj.media_reg_dict[dbid]
                # Don't add private folders
                if not isinstance(obj, media.Folder) or not obj.priv_flag:
                    obj_list.append(obj)

        self.job_total = len(obj_list)

        # Check each sub-directory in turn, updating the media data registry
        #   as we go
        while self.running_flag and obj_list:

            obj = obj_list.pop(0)

            if obj.external_dir is not None or obj.dbid != obj.master_dbid:
                self.refresh_from_actual_destination(obj)
            else:
                self.refresh_from_default_destination(obj)

            # Pause a moment, before the next iteration of the loop (don't want
            #   to hog resources)
            time.sleep(self.sleep_time)

        # Operation complete. Set the stop time
        self.stop_time = int(time.time())

        # Show a confirmation in the Output tab
        self.app_obj.main_win_obj.output_tab_write_stdout(
            1,
            _('Refresh operation finished'),
        )

        self.app_obj.main_win_obj.output_tab_write_stdout(
            1,
            '   ' + _('Number of video files analysed:') + '             ' \
            + str(self.video_total_count),
        )

        self.app_obj.main_win_obj.output_tab_write_stdout(
            1,
            '   ' + _('Video files already in the database:') + '        ' \
            + str(self.video_match_count),
        )

        self.app_obj.main_win_obj.output_tab_write_stdout(
            1,
            '   ' + _('New videos found and added to the database:') + ' ' \
            +  str(self.video_new_count),
        )

        # Let the timer run for a few more seconds to prevent Gtk errors
        GObject.timeout_add(
            0,
            self.app_obj.refresh_manager_halt_timer,
        )


    def refresh_from_default_destination(self, media_data_obj):

        """Called by self.run().

        Refreshes a single channel, playlist or folder, for which an
        alternative download destination has not been set.

        If a file is missing in the channel/playlist/folder's sub-directory,
        mark the video object as not downloaded.

        If unexpected video files exist in the sub-directory, create a new
        media.Video object for them.

        Args:

            media_data_obj (media.Channel, media.Playlist or media.Folder):
                The media data object to refresh

        """

        # Update the main window's progress bar
        self.job_count += 1
        GObject.timeout_add(
            0,
            self.app_obj.main_win_obj.update_progress_bar,
            media_data_obj.name,
            self.job_count,
            self.job_total,
        )

        # Keep a running total of matched/new videos for this channel, playlist
        #   or folder
        local_total_count = 0
        local_match_count = 0
        local_new_count = 0

        # Update our progress in the Output tab
        if isinstance(media_data_obj, media.Channel):
            string = _('Channel:') + '  '
        elif isinstance(media_data_obj, media.Playlist):
            string = _('Playlist:') + ' '
        else:
            string = _('Folder:') + '   '

        self.app_obj.main_win_obj.output_tab_write_stdout(
            1,
            string + media_data_obj.name,
        )

        # Get the sub-directory for this media data object
        dir_path = media_data_obj.get_default_dir(self.app_obj)

        # Get a list of video files in the sub-directory
        try:
            init_list = os.listdir(dir_path)
        except:
            # Can't read the directory
            return

        # From this list, filter out files without a recognised video/audio
        #   file extension (.mp4, .webm, etc)
        mod_list = []
        for relative_path in init_list:

            # (If self.stop_refresh_operation() has been called, give up
            #   immediately)
            if not self.running_flag:
                return

            # (Don't handle unwisely-named directories...)
            if os.path.isfile(
                os.path.abspath(
                    os.path.join(dir_path, relative_path),
                ),
            ):

                filename, ext = os.path.splitext(relative_path)
                # (Remove the initial .)
                ext = ext[1:]
                if ext in formats.VIDEO_FORMAT_DICT \
                or ext in formats.AUDIO_FORMAT_DICT:

                    mod_list.append(relative_path)

        # From the new list, filter out duplicate filenames (e.g. if the list
        #   contains both 'my_video.mp4' and 'my_video.webm', filter out the
        #   second one, adding to a list of alternative files)
        filter_list = []
        filter_dict = {}
        alt_list = []
        for relative_path in mod_list:

            # (If self.stop_refresh_operation() has been called, give up
            #   immediately)
            if not self.running_flag:
                return

            filename, ext = os.path.splitext(relative_path)

            if not filename in filter_dict:
                filter_list.append(relative_path)
                filter_dict[filename] = relative_path

            else:
                alt_list.append(relative_path)

        # Now compile a dictionary of media.Video objects in this channel/
        #   playlist/folder, so we can eliminate them one by one
        check_dict = {}
        for child_obj in media_data_obj.child_list:

            # (If self.stop_refresh_operation() has been called, give up
            #   immediately)
            if not self.running_flag:
                return

            if isinstance(child_obj, media.Video) and child_obj.file_name:

                # Does the video file still exist?
                this_file = child_obj.file_name + child_obj.file_ext
                if child_obj.dl_flag and not this_file in init_list:
                    self.app_obj.mark_video_downloaded(child_obj, False)
                else:
                    check_dict[child_obj.file_name] = child_obj

        # If this channel/playlist/folder is the alternative download
        #   destination for other channels/playlists/folders, compile a
        #   dicationary of their media.Video objects
        # (If we find a video we weren't expecting, before creating a new
        #   media.Video object, we must first check it isn't one of them)
        slave_dict = {}
        for slave_dbid in media_data_obj.slave_dbid_list:

            # (If self.stop_refresh_operation() has been called, give up
            #   immediately)
            if not self.running_flag:
                return

            slave_obj = self.app_obj.media_reg_dict[slave_dbid]
            for child_obj in slave_obj.child_list:

                if isinstance(child_obj, media.Video) and child_obj.file_name:
                    slave_dict[child_obj.file_name] = child_obj

        # Now try to match each video file (in filter_list) with an existing
        #   media.Video object (in check_dict)
        # If there is no match, and if the video file doesn't match a video
        #   in another channel/playlist/folder (for which this is the
        #   alternative download destination), then we can create a new
        #   media.Video object
        for relative_path in filter_list:

            # (If self.stop_refresh_operation() has been called, give up
            #   immediately)
            if not self.running_flag:
                return

            filename, ext = os.path.splitext(relative_path)

            if self.app_obj.refresh_output_videos_flag:

                self.app_obj.main_win_obj.output_tab_write_stdout(
                    1,
                    '   ' + _('Checking:') + ' '  + filename,
                )

            if filename in check_dict:

                # File matched
                self.video_total_count += 1
                local_total_count += 1
                self.video_match_count += 1
                local_match_count += 1

                # If it is not marked as downloaded, we can mark it so now
                child_obj = check_dict[filename]
                if not child_obj.dl_flag:
                    self.app_obj.mark_video_downloaded(child_obj, True)

                # Make sure the stored extension is correct (e.g. if we've
                #   matched an existing .webm video file, with an expected
                #   .mp4 video file)
                if child_obj.file_ext != ext:
                    child_relative_path \
                    = child_obj.file_name + child_obj.file_ext

                    if not child_relative_path in alt_list:
                        child_obj.set_file(filename, ext)

                # Take this opportunity to update the video file size (etc),
                #   in case they weren't set during the original download
                self.app_obj.update_video_from_filesystem(
                    child_obj,
                    child_obj.get_actual_path(self.app_obj),
                )

                # Eliminate this media.Video object; no other video file should
                #   match it
                del check_dict[filename]

                # Update our progress in the Output tab (if required)
                if self.app_obj.refresh_output_videos_flag:
                    self.app_obj.main_win_obj.output_tab_write_stdout(
                        1,
                    '   ' + _('Match:') + ' '  + filename,
                    )

            elif filename not in slave_dict:

                # File didn't match a media.Video object
                self.video_total_count += 1
                local_total_count += 1
                self.video_new_count += 1
                local_new_count += 1

                # Display the list of non-matching videos, if required
                if self.app_obj.refresh_output_videos_flag \
                and self.app_obj.refresh_output_verbose_flag:

                    for failed_path in check_dict.keys():
                        self.app_obj.main_win_obj.output_tab_write_stdout(
                            1,
                            '   ' + _('Non-match:') + ' '  + filename,
                        )

                # Create a new media.Video object
                video_obj = self.app_obj.add_video(media_data_obj, None)
                video_path = os.path.abspath(
                    os.path.join(
                        dir_path,
                        filter_dict[filename],
                    )
                )

                # Set the new video object's IVs
                filename, ext = os.path.splitext(filter_dict[filename])
                video_obj.set_name(filename)
                video_obj.set_nickname(filename)
                video_obj.set_file(filename, ext)

                if ext == '.mkv':
                    video_obj.set_mkv()

                video_obj.set_file_size(
                    os.path.getsize(
                        os.path.abspath(
                            os.path.join(dir_path, filter_dict[filename]),
                        ),
                    ),
                )

                # If the video's JSON file has been downloaded, we can extract
                #   video statistics from it
                self.app_obj.update_video_from_json(video_obj)

                # For any of those statistics that haven't been set (because
                #   the JSON file was missing or didn't contain the right
                #   statistics), set them directly
                self.app_obj.update_video_from_filesystem(
                    video_obj,
                    video_path,
                )

                # This call marks the video as downloaded, and also updates the
                #   Video Index and Video Catalogue (if required)
                self.app_obj.mark_video_downloaded(video_obj, True)

                if self.app_obj.refresh_output_videos_flag:
                    self.app_obj.main_win_obj.output_tab_write_stdout(
                        1,
                        '   ' + _('New video:') + ' '  + filename,
                    )

        # Check complete, display totals
        self.app_obj.main_win_obj.output_tab_write_stdout(
            1,
            '   ' + _('Total videos:') + ' ' + str(local_total_count) \
            + ', ' + _('matched:') + ' ' + str(local_match_count) \
            + ', ' + _('new:') + ' ' + str(local_new_count),
        )


    def refresh_from_actual_destination(self, media_data_obj):

        """Called by self.run().

        A modified version of self.refresh_from_default_destination().
        Refreshes a single channel, playlist or folder, for which an
        alternative download destination has been set.

        If a file is missing in the alternative download destination, mark the
        video object as not downloaded.

        Don't check for unexpected video files in the alternative download
        destination - we expect that they exist.

        Args:

            media_data_obj (media.Channel, media.Playlist or media.Folder):
                The media data object to refresh

        """

        # Update the main window's progress bar
        self.job_count += 1
        GObject.timeout_add(
            0,
            self.app_obj.main_win_obj.update_progress_bar,
            media_data_obj.name,
            self.job_count,
            self.job_total,
        )

        # Keep a running total of matched videos for this channel, playlist or
        #   folder
        local_total_count = 0
        local_match_count = 0
        # (No new media.Video objects are created)
        local_missing_count = 0

        # Update our progress in the Output tab
        if isinstance(media_data_obj, media.Channel):
            string = _('Channel:') + '  '
        elif isinstance(media_data_obj, media.Playlist):
            string = _('Playlist:') + ' '
        else:
            string = _('Folder:') + '   '

        self.app_obj.main_win_obj.output_tab_write_stdout(
            1,
            string + media_data_obj.name,
        )

        # Get the alternative download destination
        dir_path = media_data_obj.get_actual_dir(self.app_obj)

        # Get a list of video files in that sub-directory
        try:
            init_list = os.listdir(dir_path)
        except:
            # Can't read the directory
            return

        # Now check each media.Video object, to see if the video file still
        #   exists (or not)
        for child_obj in media_data_obj.child_list:

            if isinstance(child_obj, media.Video) and child_obj.file_name:

                this_file = child_obj.file_name + child_obj.file_ext
                if child_obj.dl_flag and not this_file in init_list:

                    local_missing_count += 1

                    # Video doesn't exist, so mark it as not downloaded
                    self.app_obj.mark_video_downloaded(child_obj, False)

                    # Update our progress in the Output tab (if required)
                    self.app_obj.main_win_obj.output_tab_write_stdout(
                        1,
                        '      ' + _('Missing:') + ' ' + child_obj.name,
                    )

                elif not child_obj.dl_flag and this_file in init_list:

                    self.video_total_count += 1
                    local_total_count += 1
                    self.video_match_count += 1
                    local_match_count += 1

                    # Video exists, so mark it as downloaded (but don't mark it
                    #   as new)
                    self.app_obj.mark_video_downloaded(child_obj, True, True)

                    # Update our progress in the Output tab (if required)
                    if self.app_obj.refresh_output_videos_flag:
                        self.app_obj.main_win_obj.output_tab_write_stdout(
                            1,
                            '      ' + _('Match:') + ' ' + child_obj.name,
                        )

        # Check complete, display totals
        self.app_obj.main_win_obj.output_tab_write_stdout(
            1,
            '   ' + _('Total videos:') + ' ' + str(local_total_count) \
            + ', ' + _('matched:') + ' ' + str(local_match_count) \
            + ', ' + _('missing:') + ' ' + str(local_missing_count),
        )


    def stop_refresh_operation(self):

        """Called by mainapp.TartubeApp.do_shutdown(), .stop_continue(),
        .on_button_stop_operation() and mainwin.MainWin.on_stop_menu_item().

        Stops the refresh operation.
        """

        self.running_flag = False
