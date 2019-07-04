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


"""Refresh operation classes."""


# Import Gtk modules
#   ...


# Import other modules
import os
import threading


# Import our modules
from . import formats
from . import media


# Classes


class RefreshManager(threading.Thread):

    """Called by mainapp.TartubeApp.update_manager_start().

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


    # Public class methods


    def run(self):

        """Called by mainapp.TartubeApp.refresh_manager_start().

        Compiles a list of media data objects (channels, playlists and folders)
        to refresh. If self.init_obj is not set, only that channel/playlist/
        folder is refreshed; otherwise the whole media registry is refreshed.

        Then calls self.refresh_from_filesystem() for each item in the list.

        Finally informs the main application that the refresh operation is
        complete.
        """

        # Compile a list of channels, playlists and folders to refresh (each
        #   one has their own sub-directory inside Tartube's data directory)
        obj_list = []
        if self.init_obj:
            obj_list.append(self.init_obj)
        else:
            for dbid in list(self.app_obj.media_name_dict.values()):

                obj = self.app_obj.media_reg_dict[dbid]
                # Don't add private folders
                if not isinstance(obj, media.Folder) or not obj.priv_flag:
                    obj_list.append(obj)

        # Check each sub-directory in turn, updating the media data registry
        #   as we go
        while self.running_flag and obj_list:
            self.refresh_from_filesystem(obj_list.pop(0))

        # Operation complete; inform the main application
        self.app_obj.refresh_manager_finished()


    def refresh_from_filesystem(self, media_data_obj):

        """Called by self.run().

        Refresh a single channel, playlist or folder.

        If a file is missing in the channel/playlist/folder's sub-directory,
        mark the video object as not downloaded.

        If unexpected video files exist in the sub-directory, create a new
        media.Video object for them.

        Args:

            media_data_obj (media.Channel, media.Playlist or media.Folder):
                The media data object to refresh

        """

        # Get the sub-directory for this media data object
        dir_path = media_data_obj.get_dir(self.app_obj)

        # Get a list of video files in the sub-directory
        file_list = []
        for rel_path in os.listdir(dir_path):

            # We're only interested in files with a recognised file extension
            filename, ext = os.path.splitext(rel_path)
            # (Remove the initial .)
            ext = ext[1:]
            if ext in formats.VIDEO_FORMAT_DICT:
                file_list.append(rel_path)

        # Compile a dictionary of video objects in this channel/playlist/folder
        #   so we can eliminate them one by one
        check_dict = {}
        for child_obj in media_data_obj.child_list:

            # (If self.stop_refresh_operation() has been called, give up
            #   immediately)
            if not self.running_flag:
                return

            if isinstance(child_obj, media.Video) and child_obj.file_dir:

                # Does the video file still exist?
                check_path = child_obj.file_name + child_obj.file_ext
                if child_obj.dl_flag and not check_path in file_list:
                    self.app_obj.mark_video_downloaded(child_obj, False)

                else:
                    check_dict[check_path] = child_obj

        # Check every video file in the sub-directory. Does it match an
        #   existing media.Video object?
        for rel_path in file_list:

            # (If self.stop_refresh_operation() has been called, give up
            #   immediately)
            if not self.running_flag:
                return

            if rel_path in check_dict:

                # File matched. If it is not marked as downloaded, we can mark
                #   it so now
                child_obj = check_dict[rel_path]
                if not child_obj.dl_flag:
                    self.app_obj.mark_video_downloaded(child_obj, True)

                # Eliminate this media.Video object; no other video file
                #   should match it (guards against two video files with the
                #   same name, one with an .mp4 extension, the other with an
                #   .mkv extension)
                del check_dict[rel_path]

            else:

                # File didn't match a media.Video object, so create a new one
                video_obj = self.app_obj.add_video(media_data_obj, None)
                video_path = os.path.abspath(os.path.join(dir_path, rel_path))

                # Set the new video object's IVs
                filename, ext = os.path.splitext(rel_path)
                video_obj.set_name(filename)
                video_obj.set_file(dir_path, filename, ext)

                if ext == '.mkv':
                    video_obj.set_mkv()

                video_obj.set_file_size(
                    os.path.getsize(
                        os.path.abspath(os.path.join(dir_path, rel_path)),
                    ),
                )

                # If the video's JSON file exists downloaded, we can extract
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
                #   Video Index and Video Catalogue
                self.app_obj.mark_video_downloaded(video_obj, True)


    def stop_refresh_operation(self):

        """Called by mainapp.TartubeApp.do_shutdown(), .stop() and a callback
        in .on_button_stop_operation().

        Stops the refresh operation.
        """

        self.running_flag = False
