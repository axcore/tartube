#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2021 A S Lewis
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


"""Media data classes."""


# Import Gtk modules
#   ...


# Import other modules
import datetime
import functools
import os
import re
import time


# Import our modules
import formats
import mainapp
import utils
# Use same gettext translations
from mainapp import _


# Classes


class GenericMedia(object):

    """Base python class inherited by media.Video, media.Channel,
    media.Playlist and media.Folder."""


    # Public class methods

    def get_type(self):

        if isinstance(self, Channel):
            return 'channel'
        elif isinstance(self, Playlist):
            return 'playlist'
        elif isinstance(self, Folder):
            return 'folder'
        else:
            return 'video'


    def get_translated_type(self, upper_flag=False):

        if not upper_flag:

            if isinstance(self, Channel):
                return _('channel')
            elif isinstance(self, Playlist):
                return _('playlist')
            elif isinstance(self, Folder):
                return _('folder')
            else:
                return _('video')

        else:

            if isinstance(self, Channel):
                return _('Channel')
            elif isinstance(self, Playlist):
                return _('Playlist')
            elif isinstance(self, Folder):
                return _('Folder')
            else:
                return _('Video')


    # Set accessors


    def set_error(self, msg):

        # The media.Folder object has no error/warning IVs (and shouldn't
        #   receive any error/warning messages)
        if not isinstance(self, Folder):
            self.error_list.append(msg)


    def reset_error_warning(self):

        # The media.Folder object has no error/warning IVs (and shouldn't
        #   receive any error/warning messages)
        if not isinstance(self, Folder):
            self.error_list = []
            self.warning_list = []


    def set_fav_flag(self, flag):

        if flag:
            self.fav_flag = True
        else:
            self.fav_flag = False


    def set_nickname(self, nickname):

        if nickname is None or nickname == '':
            self.nickname = self.name
        else:
            self.nickname = nickname


    def set_options_obj(self, options_obj):

        self.options_obj = options_obj


    def reset_options_obj(self):

        self.options_obj = None


    def set_parent_obj(self, parent_obj):

        self.parent_obj = parent_obj


    def set_warning(self, msg):

        # The media.Folder object has no error/warning IVs (and shouldn't
        #   receive any error/warning messages)
        if not isinstance(self, Folder):
            self.warning_list.append(msg)


class GenericContainer(GenericMedia):

    """Base python class inherited by media.Channel, media.Playlist and
    media.Folder."""


    # Public class methods


    def compile_all_containers(self, container_list):

        """Can be called by anything. Subsequently called by this function
        recursively.

        Appends to the specified list this container, then calls all this
        function recursively for all media.Channel, media.Playlist and
        media.Folder objects, so they too can be added to the list.

        Args:

            container_list (list): A list of media.Channel, media.Playlist and
                media.Folder objects

        Returns:

            The modified container_list

        """

        container_list.append(self)
        for child_obj in self.child_list:

            if not isinstance(child_obj, Video):
                child_obj.compile_all_containers(container_list)

        return container_list


    def compile_all_videos(self, video_list):

        """Can be called by anything. Subsequently called by this function
        recursively.

        Appends to the specified list all child objects that are media.Video
        objects, then calls this function recursively for all other child
        objects, so they can add their children too.

        Args:

            video_list (list): A list of media.Video objects

        Returns:

            The modified video_list

        """

        for child_obj in self.child_list:

            if isinstance(child_obj, Video):
                video_list.append(child_obj)
            else:
                child_obj.compile_all_videos(video_list)

        return video_list


    def compile_all_videos_by_frequency(self, data_type, period,
    frequency_dict):

        """Can be called by anything, but mostly called by
        config.GenericConfigWin.on_button_draw_graph_clicked().

        Compile a dictionary of download times for each video in the container
        (including those in sub-folders, channels and playlists).

        The dictionary shows the frequency of downloads for each specified
        time period (for example, a day, a month, etc).

        Args:

            data_type (str): 'receive' to compile video frequencies by
                receive (download) time, 'download' to compile by download time

            period (int): A time period, in seconds (e.g. 86400 for a day)

            frequency_dict (dict): The dictionary compiled so far (empty
                unless multiple containers are being combined into a single
                dictionary)

        Return values:

            Dictionary in the form
                frequency_dict[time_period_number] = number_of_videos

            ...for example, if 10 videos were downloaded today, and 20 were
            downloaded yesterday, and the period is 86400 (representing one
            day), then
                frequency_dict[0] = 10
                frequency_dict[1] = 20

        """

        now = time.time()
        video_list = self.compile_all_videos( [] )

        if data_type == 'receive':

            for video_obj in video_list:

                if video_obj.receive_time:

                    time_units = int((now - video_obj.receive_time) / period)

                    if time_units in frequency_dict:
                        frequency_dict[time_units] += 1
                    else:
                        frequency_dict[time_units] = 1

        else:

            for video_obj in video_list:

                if video_obj.upload_time:

                    time_units = int((now - video_obj.upload_time) / period)

                    if time_units in frequency_dict:
                        frequency_dict[time_units] += 1
                    else:
                        frequency_dict[time_units] = 1

        return frequency_dict


    def compile_all_videos_by_size(self, frequency_dict):

        """Can be called by anything, but mostly called by
        config.GenericConfigWin.on_button_draw_graph_clicked().

        This functions specifies a limited set of file sizes. The set has been
        chosen to produce aesthetic graphs.

        Compile a dictionary containing the number of videos for each size
        range. Videos whose file size is not known are ignored.

        Args:

            frequency_dict (dict): The dictionary compiled so far (empty
                unless multiple containers are being combined into a single
                dictionary)

        Return values:

            Dictionary in the form
                frequency_dict[range_label] = number_of_videos

        """

        for video_obj in self.compile_all_videos( [] ):

            if video_obj.file_size is not None:

                # NB If these labels are changed, when the corresponding
                #   literal values in
                #   config.GenericConfigWin.on_button_draw_graph_clicked() must
                #   be changed too
                if video_obj.file_size < 10_000_000:
                    label = '10MB'
                elif video_obj.file_size < 25_000_000:
                    label = '25MB'
                elif video_obj.file_size < 50_000_000:
                    label = '50MB'
                elif video_obj.file_size < 100_000_000:
                    label = '100MB'
                elif video_obj.file_size < 250_000_000:
                    label = '250MB'
                elif video_obj.file_size < 500_000_000:
                    label = '500MB'
                elif video_obj.file_size < 1000_000_000:
                    label = '1GB'
                elif video_obj.file_size < 2000_000_000:
                    label = '2GB'
                elif video_obj.file_size < 5000_000_000:
                    label = '5GB'
                else:
                    label = '5GB+'

                if label in frequency_dict:
                    frequency_dict[label] += 1
                else:
                    frequency_dict[label] = 1

        return frequency_dict


    def compile_all_videos_by_duration(self, frequency_dict):

        """Can be called by anything, but mostly called by
        config.GenericConfigWin.on_button_draw_graph_clicked().

        This functions specifies a limited set of video durations (in seconds).
        The set has been chosen to produce aesthetic graphs.

        Compile a dictionary containing the number of videos for each duration
        range. Videos whose duration is not known are ignored.

        Args:

            frequency_dict (dict): The dictionary compiled so far (empty
                unless multiple containers are being combined into a single
                dictionary)

        Return values:

            Dictionary in the form
                frequency_dict[range_label] = number_of_videos

        """

        for video_obj in self.compile_all_videos( [] ):

            if video_obj.duration is not None:

                # NB If these labels are changed, when the corresponding
                #   literal values in
                #   config.GenericConfigWin.on_button_draw_graph_clicked() must
                #   be changed too
                if video_obj.duration < 10:
                    label = '10s'
                elif video_obj.duration < 60:
                    label = '1m'
                elif video_obj.duration < 300:
                    label = '5m'
                elif video_obj.duration < 600:
                    label = '10m'
                elif video_obj.duration < 1200:
                    label = '20m'
                elif video_obj.duration < 1800:
                    label = '30m'
                elif video_obj.duration < 3600:
                    label = '1h'
                elif video_obj.duration < 7200:
                    label = '2h'
                elif video_obj.duration < 18000:
                    label = '5h'
                else:
                    label = '5h+'

                if label in frequency_dict:
                    frequency_dict[label] += 1
                else:
                    frequency_dict[label] = 1

        return frequency_dict


    def count_descendants(self, count_list):

        """Can be called by anything. Subsequently called by this function
        recursively.

        Counts the number of child objects, and then calls this function
        recursively in those child objects to count their child objects.

        Args:

            count_list (list): A list representing the child objects counted
                so far. List in the form
                    (
                        total_count, video_count, channel_count,
                        playlist_count, folder_count,
                    )

        Returns:

            The modified count_list

        """

        for child_obj in self.child_list:

            count_list[0] += 1

            if isinstance(child_obj, Video):
                count_list[1] += 1
            else:
                count_list = child_obj.count_descendants(count_list)
                if isinstance(child_obj, Channel):
                    count_list[2] += 1
                elif isinstance(child_obj, Playlist):
                    count_list[3] += 1
                else:
                    count_list[4] += 1

        return count_list


    def del_child(self, child_obj):

        """Can be called by anything.

        Deletes a child object from self.child_list, first checking that it's
        actually a child of this object.

        Args:

            child_obj (media.Video, media.Channel, media.Playlist,
                media.Folder): The child object to delete

        Returns:

            True if the child object was deleted, False if the specified object
                was not a child of this object

        """

        # Check this is really one of our children
        if not child_obj in self.child_list:
            return False

        else:
            self.child_list.remove(child_obj)

            # Git #169, v2.2.026. A user reports that the counts can fall below
            #   0. The authors can't reproduce the problem, but we can still
            #   prevent negative values
            if isinstance(child_obj, Video):
                self.vid_count -= 1
                if self.vid_count < 0:
                    self.vid_count = 0

                if child_obj.bookmark_flag:
                    self.bookmark_count -= 1
                    if self.bookmark_count < 0:
                        self.bookmark_count = 0

                if child_obj.dl_flag:
                    self.dl_count -= 1
                    if self.dl_count < 0:
                        self.dl_count = 0

                if child_obj.fav_flag:
                    self.fav_count -= 1
                    if self.fav_count < 0:
                        self.fav_count = 0

                if child_obj.live_mode:
                    self.live_count -= 1
                    if self.live_count < 0:
                        self.live_count = 0

                if child_obj.missing_flag:
                    self.missing_count -= 1
                    if self.missing_count < 0:
                        self.missing_count = 0

                if child_obj.new_flag:
                    self.new_count -= 1
                    if self.new_count < 0:
                        self.new_count = 0

                if child_obj.waiting_flag:
                    self.waiting_count -= 1
                    if self.waiting_count < 0:
                        self.waiting_count = 0

            return True


    def fetch_tooltip_text(self, app_obj, max_length=None,
    show_error_flag=False):

        """Can be called by anything.

        Returns a string to be used as a tooltip for this channel, playlist or
        folder.

        Args:

            app_obj (mainapp.TartubeApp): The main application

            max_length (int or None): If specified, the maximum line length, in
                characters

            show_error_flag (bool): If True, show the first error/warning
                generated by the channel/playlist/folder

        Returns:

            Text containing the channel/playlist/folder directory path and
                the source (except for folders), ready for display in a tooltip

        """

        text = '#' + str(self.dbid) + ':   ' + self.name + '\n\n'

        if not isinstance(self, Folder):

            translate_note = _(
                'TRANSLATOR\'S NOTE: Source = video/channel/playlist URL',
            )

            text += _('Source:') + '\n'
            if self.source is None:
                text += '<' + _('unknown') + '>'
            else:
                text += self.source

            text += '\n\n'

        text += _('Location:') + '\n'

        location = self.get_default_dir(app_obj)
        if location is None:
            text += '<' + _('unknown') + '>'
        else:
            text += location

        if self.external_dir is not None:

            text += '\n\n' + _('Download destination:') + ' '
            if self.name in app_obj.media_unavailable_dict:
                text += '(' + _('unavailable') + ')'
            else:
                text += self.external_dir

        elif self.master_dbid != self.dbid:

            dest_obj = app_obj.media_reg_dict[self.master_dbid]
            text += '\n\n' + _('Download destination:') + ' ' + dest_obj.name

        # Show the first error/warning
        if show_error_flag \
        and app_obj.show_tooltips_extra_flag \
        and not isinstance(self, Folder):

            error_warning_list = self.error_list + self.warning_list
            length = len (error_warning_list)
            if error_warning_list:

                text += '\n\n' + _('Errors\Warnings') + ' (' \
                + str(length) + '):\n' + str(error_warning_list.pop(0))

                if length > 1:
                    text += '\n...'

        # Need to escape question marks or we'll get a markup error
        text = re.sub('&', '&amp;', text)

        # Apply a maximum line length, if required
        if max_length is not None:
            text = utils.tidy_up_long_descrip(text, max_length)

        return text


    def find_matching_video(self, app_obj, name):

        """Can be called by anything.

        Checks all of this object's child objects, looking for a media.Video
        object with a matching name.

        Args:

            app_obj (mainapp.TartubeApp): The main application

            name (str): The name of the media.Video object to find

        Returns:

            The first matching media.Video object found, or None if no matching
            videos are found.

        """

        method = app_obj.match_method
        first = app_obj.match_first_chars
        ignore = app_obj.match_ignore_chars * -1

        # Defend against two different of a name from the same video, one with
        #   punctuation marks stripped away, and double quotes converted to
        #   single quotes (thanks, YouTube!) by replacing those characters with
        #   whitespace
        # (After extensive testing, this is the only regex sequence I could
        #   find that worked)
        test_name = name[:]

        # Remove punctuation
        test_name = re.sub(r'\W+', ' ', test_name, flags=re.UNICODE)
        # Also need to replace underline characters
        test_name = re.sub(r'[\_\s]+', ' ', test_name)
        # Also need to remove leading/trailing whitespace, in case the original
        #   video name started/ended with a question mark or something like
        #   that
        test_name = re.sub(r'^\s+', '', test_name)
        test_name = re.sub(r'\s+$', '', test_name)

        for child_obj in self.child_list:
            if isinstance(child_obj, Video):

                child_name = child_obj.name[:]
                child_name = re.sub(
                    r'\W+',
                    ' ',
                    child_name,
                    flags=re.UNICODE,
                )
                child_name = re.sub(r'[\_\s]+', ' ', child_name)
                child_name = re.sub(r'^\s+', '', child_name)
                child_name = re.sub(r'\s+$', '', child_name)

                if (
                    method == 'exact_match' \
                    and child_name == test_name
                ) or (
                    method == 'match_first' \
                    and child_name[:first] == test_name[:first]
                ) or (
                    method == 'ignore_last' \
                    and child_name[:ignore] == test_name[:ignore]
                ):
                    return child_obj

        # No matches found
        return None


    def get_depth(self):

        """Can be called by anything.

        There is a limit to the depth of the media registry (a maximum number
        of levels).

        This function finds the level occupied by this container object and
        returns it.

        If this object has no parent, it is at level 1. If it has a parent
        object, and the parent itself has no parent, this object is at level 2.

        Returns:

            The container object's level

        """

        if self.parent_obj is None:
            return 1

        else:
            level = 1
            parent_obj = self.parent_obj

            while parent_obj is not None:
                level += 1
                parent_obj = parent_obj.parent_obj

            return level


    def is_hidden(self):

        """Called by mainwin.MainWin.video_index_add_row() and
        .video_index_select_row().

        If this is a hidden media.Folder object, return True.

        If the parent media.Folder (or the parent's parent, and so on) is
        hidden, return True.

        Otherwise, return False. (media.Channel and media.Playlist objects
        can't be hidden directly.)

        Returns:

            True or False

        """

        if isinstance(self, Folder) and self.hidden_flag:
            return True

        parent_obj = self.parent_obj

        while parent_obj:
            if isinstance(parent_obj, Folder) and parent_obj.hidden_flag:
                return True
            else:
                parent_obj = parent_obj.parent_obj

        return False


    def prepare_export(self, app_obj, include_video_flag, include_channel_flag,
    include_playlist_flag):

        """Called by mainapp.TartubeApp.export_from_db(). Subsequently called
        by this function recursively.

        Creates the dictionary, to be saved as a JSON file, described in the
        comments to that function. This function is called when we want to
        preserve the folder structure of the Tartube database.

        Args:

            app_obj (mainapp.TartubeApp): The main application

            include_video_flag (bool): If True, include videos. If False, don't
                include them

            include_channel_flag (bool): If True, include channels (and their
                videos, if allowed). If False, ignore them

            include_playlist_flag (bool): If True, include playlists (and their
                videos, if allowed). If False, ignore them

        Returns:

            return_dict (dict): A dictionary described in the comments in the
                calling function

        """

        # Ignore the types of media data object that we don't require (and all
        #   of their children)
        # This function should not be called for media.Video objects
        # This function can be called for fixed folders, but apart from the
        #   'Unsorted Videos' and 'Video Clips' folders, we ignore them
        media_type = self.get_type()

        if media_type == 'video' \
        or (media_type == 'channel' and not include_channel_flag) \
        or (media_type == 'playlist' and not include_playlist_flag) \
        or (
            media_type == 'folder'
            and self.fixed_flag
            and self != app_obj.fixed_misc_folder
            and self != app_obj.fixed_clips_folder
        ):
            return {}

        # This dictionary contains values for the children of this object
        db_dict = {}

        for child_obj in self.child_list:

            if isinstance(child_obj, Video):

                # (Don't bother exporting a video whose source URL is not
                #   known)
                if include_video_flag and child_obj.source is not None:

                    mini_dict = {
                        'type': 'video',
                        'dbid': child_obj.dbid,
                        'name': child_obj.name,
                        'nickname': None,
                        'source': child_obj.source,
                        'db_dict': {},
                    }

                    db_dict[child_obj.dbid] = mini_dict

            else:

                mini_dict = child_obj.prepare_export(
                    app_obj,
                    include_video_flag,
                    include_channel_flag,
                    include_playlist_flag,
                )

                if mini_dict:
                    db_dict[child_obj.dbid] = mini_dict

        # This dictionary contains values for this object, and for the children
        #   of this object
        return_dict = {
            'type': media_type,
            'dbid': self.dbid,
            'name': self.name,
            'nickname': self.nickname,
            'source': None,
            'db_dict': db_dict,
        }

        if media_type != 'folder':
            return_dict['source'] = self.source

        # Procedure complete
        return return_dict


    def prepare_flat_export(self, app_obj, db_dict, include_video_flag,
    include_channel_flag, include_playlist_flag):

        """Called by mainapp.TartubeApp.export_from_db(). Subsequently called
        by this function recursively.

        Creates the dictionary, to be saved as a JSON file, described in the
        comments to that function. This function is called when we don't want
        to preserve the folder structure of the Tartube database.

        Args:

            app_obj (mainapp.TartubeApp): The main application

            db_dict (dict): The dictionary described in the comments in the
                calling function

            include_video_flag (bool): If True, include videos. If False, don't
                include them

            include_channel_flag (bool): If True, include channels (and their
                videos, if allowed). If False, ignore them

            include_playlist_flag (bool): If True, include playlists (and their
                videos, if allowed). If False, ignore them

        Returns:

            db_dict (dict): The modified dictionary

        """

        # Ignore the types of media data object that we don't require (and all
        #   of their children)
        # This function should not be called for media.Video objects
        # This function can be called for fixed folders, but apart from the
        #   'Unsorted Videos' and 'Video Clips' folders, we ignore them
        media_type = self.get_type()

        if media_type == 'video' \
        or (media_type == 'channel' and not include_channel_flag) \
        or (media_type == 'playlist' and not include_playlist_flag) \
        or (
            media_type == 'folder'
            and self.fixed_flag
            and self != app_obj.fixed_misc_folder
            and self != app_obj.fixed_clips_folder
        ):
            return {}

        # Add values to the dictionary
        if media_type == 'channel' or media_type == 'playlist':

            child_dict = {}

            for child_obj in self.child_list:

                if isinstance(child_obj, Video):

                    # (Don't bother exporting a video whose source URL is not
                    #   known)
                    if include_video_flag and child_obj.source is not None:

                        child_mini_dict = {
                            'type': 'video',
                            'dbid': child_obj.dbid,
                            'name': child_obj.name,
                            'nickname': None,
                            'source': child_obj.source,
                            'db_dict': {},
                        }

                        child_dict[child_obj.dbid] = child_mini_dict

                else:

                    db_dict = child_obj.prepare_flat_export(
                        app_obj,
                        db_dict,
                        include_video_flag,
                        include_channel_flag,
                        include_playlist_flag,
                    )

            mini_dict = {
                'type': media_type,
                'dbid': self.dbid,
                'name': self.name,
                'nickname': self.nickname,
                'source': self.source,
                'db_dict': child_dict,
            }

            db_dict[self.dbid] = mini_dict

        elif media_type == 'folder':

            for child_obj in self.child_list:

                if not isinstance(child_obj, Video):

                    db_dict = child_obj.prepare_flat_export(
                        app_obj,
                        db_dict,
                        include_video_flag,
                        include_channel_flag,
                        include_playlist_flag,
                    )

        # Procedure complete
        return db_dict


    def recalculate_counts(self):

        """Can be called by anything.

        Recalculates all count IVs.
        """

        self.vid_count = 0
        self.bookmark_count = 0
        self.dl_count = 0
        self.fav_count = 0
        self.live_count = 0
        self.missing_count = 0
        self.new_count = 0
        self.waiting_count = 0

        for child_obj in self.child_list:

            if isinstance(child_obj, Video):
                self.vid_count += 1

                if child_obj.bookmark_flag:
                    self.bookmark_count += 1

                if child_obj.dl_flag:
                    self.dl_count += 1

                if child_obj.fav_flag:
                    self.fav_count += 1

                if child_obj.live_mode:
                    self.live_count += 1

                if child_obj.missing_flag:
                    self.missing_count += 1

                if child_obj.new_flag:
                    self.new_count += 1

                if child_obj.waiting_flag:
                    self.waiting_count += 1


    def test_counts(self):

        """Can be called by anything.

        Recalculates all count IVs, and compares them against the container's
        actual counts.

        Return values:

            True if there is a discrepancy; False if the container's actual
                counts seem to be correct

        """

        vid_count = 0
        bookmark_count = 0
        dl_count = 0
        fav_count = 0
        live_count = 0
        missing_count = 0
        new_count = 0
        waiting_count = 0

        for child_obj in self.child_list:

            if isinstance(child_obj, Video):
                vid_count += 1

                if child_obj.bookmark_flag:
                    bookmark_count += 1

                if child_obj.dl_flag:
                    dl_count += 1

                if child_obj.fav_flag:
                    fav_count += 1

                if child_obj.live_mode:
                    live_count += 1

                if child_obj.missing_flag:
                    missing_count += 1

                if child_obj.new_flag:
                    new_count += 1

                if child_obj.waiting_flag:
                    waiting_count += 1

        if vid_count != self.vid_count \
        or bookmark_count != self.bookmark_count \
        or dl_count != self.dl_count \
        or fav_count != self.fav_count \
        or live_count != self.live_count \
        or missing_count != self.missing_count \
        or new_count != self.new_count \
        or waiting_count != self.waiting_count:
            return True

        else:
            return False


    # Set accessors


    def reset_counts(self, vid_count, bookmark_count, dl_count, fav_count,
    live_count, missing_count, new_count, waiting_count):

        """Called by mainapp.TartubeApp.update_db().

        When a database created by an earlier version of Tartube is loaded,
        the calling function updates IVs as required.

        This function is called if this object's video counts need to be
        changed.
        """

        self.vid_count = vid_count
        self.bookmark_count = bookmark_count
        self.dl_count = dl_count
        self.fav_count = fav_count
        self.live_count = live_count
        self.missing_count = missing_count
        self.new_count = new_count
        self.waiting_count = waiting_count


    def inc_bookmark_count(self):

        self.bookmark_count += 1


    def dec_bookmark_count(self):

        self.bookmark_count -= 1
        if self.bookmark_count < 0:
            self.bookmark_count = 0


    def inc_dl_count(self):

        self.dl_count += 1


    def dec_dl_count(self):

        self.dl_count -= 1
        if self.dl_count < 0:
            self.dl_count = 0


    def set_dl_disable_flag(self, flag):

        if flag:
            self.dl_disable_flag = True
            # This group of flags are mutually exclusive
            self.dl_no_db_flag = False
            self.dl_sim_flag = False

        else:
            self.dl_disable_flag = False


    def set_dl_no_db_flag(self, flag):

        if flag:
            self.dl_no_db_flag = True
            # This group of flags are mutually exclusive
            self.dl_disable_flag = False
            self.dl_sim_flag = False

        else:
            self.dl_no_db_flag = False


    def set_dl_sim_flag(self, flag):

        if flag:
            self.dl_sim_flag = True
            # This group of flags are mutually exclusive
            self.dl_no_db_flag = False
            self.dl_disable_flag = False

        else:
            self.dl_sim_flag = False


    def set_external_dir(self, app_obj, external_dir):

        self.external_dir = external_dir
        if external_dir is not None:

            # If the directory does not exist, try to create it
            if not os.path.isdir(external_dir) \
            and not app_obj.make_directory(external_dir):

                # Failed
                return False

            # If a semaphore file does not exist in the external directory,
            #   create one
            if not app_obj.make_semaphore_file(external_dir):

                # Failed
                return False

        return True


    def inc_fav_count(self):

        self.fav_count += 1


    def dec_fav_count(self):

        self.fav_count -= 1
        if self.fav_count < 0:
            self.fav_count = 0


    def inc_live_count(self):

        self.live_count += 1


    def dec_live_count(self):

        self.live_count -= 1
        if self.live_count < 0:
            self.live_count = 0


    def set_master_dbid(self, app_obj, dbid):

        if dbid == self.master_dbid:
            # No change to the current value
            return

        else:

            # Update the old alternative download destination
            if self.master_dbid != self.dbid:

                # (If mainapp.TartubeApp.fix_integrity_db() is fixing an
                #   error, the old destination object might not exist)
                if self.master_dbid in app_obj.media_reg_dict:
                    old_dest_obj = app_obj.media_reg_dict[self.master_dbid]
                    old_dest_obj.del_slave_dbid(self.dbid)

            # Update this object's IV
            self.master_dbid = dbid

            if self.master_dbid != self.dbid:

                # Update the new alternative download destination
                new_dest_obj = app_obj.media_reg_dict[self.master_dbid]
                new_dest_obj.add_slave_dbid(self.dbid)


    def reset_master_dbid(self):

        self.master_dbid = self.dbid


    def inc_missing_count(self):

        self.missing_count += 1


    def dec_missing_count(self):

        self.missing_count -= 1
        if self.missing_count < 0:
            self.missing_count = 0


    def inc_new_count(self):

        self.new_count += 1


    def dec_new_count(self):

        self.new_count -= 1
        if self.new_count < 0:
            self.new_count = 0


    def inc_waiting_count(self):

        self.waiting_count += 1


    def dec_waiting_count(self):

        self.waiting_count -= 1
        if self.waiting_count < 0:
            self.waiting_count = 0


    def add_slave_dbid(self, dbid):

        """Called by self.set_master_dbid() only."""

        # (Failsafe: don't add the same value to self.slave_dbid_list)
        match_flag = False
        for slave_dbid in self.slave_dbid_list:
            if slave_dbid == dbid:
                match_flag = True
                break

        if not match_flag:
            self.slave_dbid_list.append(dbid)


    def del_slave_dbid(self, dbid):

        """Called by mainapp.TartubeApp.fix_integrity_db() or by
        self.set_master_dbid() only."""

        new_list = []

        for slave_dbid in self.slave_dbid_list:
            if slave_dbid != dbid:
                new_list.append(slave_dbid)

        self.slave_dbid_list = new_list.copy()


    def set_name(self, name):

        # Update the nickname at the same time, if it has the same value as
        #   this object's name
        if self.nickname == self.name:
            self.nickname = name

        self.name = name


    # Get accessors


    def get_actual_dir(self, app_obj, new_name=None):

        """Can be called by anything.

        Fetches the full path to the sub-directory actually used by this
        channel, playlist or folder.

        If self.external_dir is set, returns it.

        Otherwise, if self.dbid and self.master_dbid are the same, then files
        are downloaded to the default location; the sub-directory belonging to
        the channel/playlist/folder. In that case, this function returns the
        same value as self.get_default_dir().

        If self.master_dbid is not the same as self.dbid, then files are
        actually downloaded into the sub-directory used by another channel,
        playlist or folder. This function returns that sub-directory.

        Args:

            app_obj (mainapp.TartubeApp): The main application

        Optional args:

            new_name (str): If specified, fetches the full path to the
                sub-directory that would be used by this channel, playlist or
                folder, if it were renamed to 'new_name'. If not specified, the
                channel/playlist/folder's actual name is used

        Returns:

            The full path to the sub-directory

        """

        if self.external_dir is not None:

            return self.external_dir

        elif self.master_dbid != self.dbid:

            master_obj = app_obj.media_reg_dict[self.master_dbid]
            return master_obj.get_default_dir(app_obj, new_name)

        else:

            return self.get_default_dir(app_obj, new_name)


    def get_default_dir(self, app_obj, new_name=None):

        """Can be called by anything.

        Fetches the full path to the sub-directory used by this channel,
        playlist or folder by default.

        If self.external_dir is set, or if self.master_dbid is not the same as
        self.dbid, then files are actually downloaded to a non-default
        location. To get the actual download location, call
        self.get_actual_dir().

        Args:

            app_obj (mainapp.TartubeApp): The main application

        Optional args:

            new_name (str): If specified, fetches the full path to the
                sub-directory that would be used by this channel, playlist or
                folder, if it were renamed to 'new_name'. If not specified, the
                channel/playlist/folder's actual name is used

        Returns:

            The full path to the sub-directory

        """

        if new_name is not None:
            dir_list = [new_name]
        else:
            dir_list = [self.name]

        obj = self
        while obj.parent_obj:

            obj = obj.parent_obj
            dir_list.insert(0, obj.name)

        return os.path.abspath(os.path.join(app_obj.downloads_dir, *dir_list))


    def get_relative_actual_dir(self, app_obj, new_name=None):

        """Can be called by anything.

        Fetches the path to the sub-directory used by this channel, playlist or
        folder, relative to mainapp.TartubeApp.downloads_dir.

        If self.dbid and self.master_dbid are the same, then files are
        downloaded to the default location; the sub-directory belonging to the
        channel/playlist/folder. In that case, this function returns the same
        value as self.get_default_dir().

        If self.master_dbid is not the same as self.dbid, then files are
        actually downloaded into the sub-directory used by another channel,
        playlist or folder. This function returns that sub-directory.

        Exception: if an external directory is set, returns None (as the
        external directory is always outside Tartube's data directory). THe
        calling code must check for that

        Args:

            app_obj (mainapp.TartubeApp): The main application

            new_name (str): If specified, fetches the relative path to the
                sub-directory that would be used by this channel, playlist or
                folder, if it were renamed to 'new_name'. If not specified, the
                channel/playlist/folder's actual name is used

        Returns:

            The path to the sub-directory relative to
                mainapp.TartubeApp.downloads_dir, or None if an external
                directory has been set

        """

        if self.master_dbid != self.dbid:

            master_obj = app_obj.media_reg_dict[self.master_dbid]
            return master_obj.get_relative_default_dir(app_obj, new_name)

        else:

            return self.get_relative_default_dir(app_obj, new_name)


    def get_relative_default_dir(self, new_name=None):

        """Can be called by anything.

        Fetches the path to the sub-directory used by this channel, playlist or
        folder by default, relative to mainapp.TartubeApp.downloads_dir.

        If self.external_dir is set, or if self.master_dbid is not the same as
        self.dbid, then files are actually downloaded to a non-default
        location. To get the actual relative location, call
        self.get_relative_actual_dir().

        Args:

            new_name (str): If specified, fetches the relative path to the
                sub-directory that would be used by this channel, playlist or
                folder, if it were renamed to 'new_name'. If not specified, the
                channel/playlist/folder's actual name is used

        Returns:

            The path to the sub-directory relative to
                mainapp.TartubeApp.downloads_dir

        """

        if new_name is not None:
            dir_list = [new_name]
        else:
            dir_list = [self.name]

        obj = self
        while obj.parent_obj:

            obj = obj.parent_obj
            dir_list.insert(0, obj.name)

        return os.path.join(*dir_list)


class GenericRemoteContainer(GenericContainer):

    """Base python class inherited by media.Channel and media.Playlist."""


    # Public class methods


    def add_child(self, app_obj, child_obj, no_sort_flag=False):

        """Can be called by anything.

        Adds a child media data object, which must be a media.Video object.

        Args:

            app_obj (mainapp.TartubeApp): The main application

            child_obj (media.Video): The child object

            no_sort_flag (bool): True when the calling code wants to delay
                sorting the parent container object, for some reason; False if
                not

        """

        # Only media.Video objects can be added to a channel or playlist as a
        #   child object. Also, check this is not already a child object
        if isinstance(child_obj, Video) or child_obj in self.child_list:

            self.child_list.append(child_obj)
            if not no_sort_flag:
                self.sort_children(app_obj)

            if isinstance(child_obj, Video):
                self.vid_count += 1


    def sort_children(self, app_obj):

        """Can be called by anything. For example, called by self.add_child().

        Sorts the child media.Video objects using the standard video-sorting
        function.

        Args:

            app_obj (mainapp.TartubeApp): The main application

        """

        self.last_sort_mode = app_obj.catalogue_sort_mode

        # Sort a copy of the list to prevent 'list modified during sort'
        #   errors
        while True:

            copy_list = self.child_list.copy()
            copy_list.sort(key=functools.cmp_to_key(app_obj.video_compare))

            if len(copy_list) == len(self.child_list):
                self.child_list = copy_list.copy()
                break


    # Set accessors


    def clone_properties(self, other_obj):

        """Called by mainapp.TartubeApp.convert_remote_container() only.

        Copies properties from a media data object (about to be deleted) to
        this media data object.

        Some properties are handled by the calling function; this function
        handles the rest of them.

        Args:

            other_obj (media.Channel, media.Playlist): The object whose
                properties should be copied

        """

        self.options_obj = other_obj.options_obj
        self.nickname = other_obj.nickname
        self.source = other_obj.source
        self.dl_no_db_flag = other_obj.dl_no_db_flag
        self.dl_disable_flag = other_obj.dl_disable_flag
        self.dl_sim_flag = other_obj.dl_sim_flag
        self.fav_flag = other_obj.fav_flag

        self.bookmark_count = other_obj.bookmark_count
        self.dl_count = other_obj.dl_count
        self.fav_count = other_obj.fav_count
        self.live_count = other_obj.live_count
        self.missing_count = other_obj.missing_count
        self.new_count = other_obj.new_count
        self.waiting_count = other_obj.waiting_count

        self.error_list = other_obj.error_list.copy()
        self.warning_list = other_obj.warning_list.copy()


    def set_rss(self, youtube_id):

        """Can be called by anything; called frequently by
        downloads.VideoDownloader.extract_stdout_data().

        Set the RSS feed, but only if it's not already set (to save time).

        Args:

            youtube_id (str): The YouTube channel or playlist ID

        """

        if not self.rss:

            if isinstance(self, Channel):

                self.rss = utils.convert_youtube_id_to_rss(
                    'channel',
                    youtube_id,
                )

            else:

                self.rss = utils.convert_youtube_id_to_rss(
                    'playlist',
                    youtube_id,
                )


    def set_source(self, source):

        self.source = source


class Video(GenericMedia):

    """Python class that handles an individual video.

    Args:

        app_obj (mainapp.TartubeApp): The main application (not stored as an
            IV)

        dbid (int): A unique ID for this media data object

        name (str): The video name

        parent_obj (media.Channel, media.Playlist, media.Folder): The parent
            media data object, if any

        options_obj (options.OptionsManager): The object specifying download
            options for this video, if any

        no_sort_flag (bool): True when the calling code wants to delay sorting
            the parent container object, for some reason; False if not

    """


    # Standard class methods


    def __init__(self, app_obj, dbid, name, parent_obj=None, options_obj=None,
    no_sort_flag=False, dummy_flag=False):

        # IV list - class objects
        # -----------------------
        # The parent object (a media.Channel, media.Playlist or media.Folder
        #   object. All media.Video objects have a parent)
        self.parent_obj = parent_obj
        # The options.OptionsManager object that specifies how this video is
        #   downloaded (or None, if the parent's options.OptionsManager object
        #   should be used instead)
        self.options_obj = options_obj


        # IV list - other
        # ---------------
        # Unique media data object ID (an integer)
        # When a download operation is launched from the Classic Mode tab, the
        #   code creates a series of dummy media.Video objects that aren't
        #   added to the media data registry. Those dummy objects have negative
        #   dbids
        self.dbid = dbid

        # Video name
        self.name = name
        # Video nickname (displayed in the Video Catalogue)
        # If the video's JSON data has been fetched, self.name matches the
        #   actual filename of the video, and self.nickname is the video's
        #   title
        # (In practical terms, if the user has specified that the video
        #   filename should be in the format NAME + ID, then self.name will be
        #   in the format 'NAME + ID', and self.nickname will be in the format
        #   'NAME')
        # If the video's JSON data has not been fetched, self.name and
        #   self.nickname are the same
        self.nickname = name
        # Download source (a URL)
        self.source = None
        # The website's video ID, if known (e.g. on YouTube, everything after
        #   https://www.youtube.com/watch?v=)
        self.vid = None

        # Flag set to True if Tartube should always simulate the download of
        #   video, or False if the downloads.DownloadManager object should
        #   decide whether to simulate, or not
        self.dl_sim_flag = False

        # Livestream mode: 0 if the video is not a livestream (or if it was a
        #   livestream which has now finished, and behaves like a normal
        #   uploaded video), 1 if the livestream has not started, 2 if the
        #   livestream is currently being broadcast
        # (Using a numerical mode makes the sorting algorithms more efficient)
        self.live_mode = 0
        # YouTube 'premiere' videos and actual livestreams are treated in the
        #   same way, except that for the former, this flag is set to True
        #   (and a different background colour is used in the Video Catalogue)
        self.live_debut_flag = False
        # Flag set to True for a video which was a livestream (self.live_mode
        #   = 1 or 2), but is now not (self.live_mode = 0). Once a livestream
        #   video has been marked as a normal video, it can't be marked as a
        #   livestream again. (This prevents any problems in reading the RSS
        #   feeds from continually marking an old video as a livestream again)
        self.was_live_flag = False
        # The time (matches time.time()) at which a livestream is due to start.
        #   YouTube supplies an approximate time (perhaps in hours or days),
        #   but it's still useful for sorting
        # (For the benefit of the sorting functions, the default value is 0)
        self.live_time = 0
        # When YouTube provides a livestream message,
        #   utils.extract_livestream_data() converts it into some text that can
        #   be displayed in the Video Catalogue
        # The text to display. If the video is not a livestream, or has already
        #   started, or has already finished, or no recognised message was
        #   provided, an empty string
        self.live_msg = ''

        # Flag set to True if the video is archived, meaning that it can't be
        #   auto-deleted (but it can still be deleted manually by the user)
        self.archive_flag = False
        # Flag set to True if the video is marked as bookmarked, so that it
        #   appears in the 'Bookmarks' system folder
        self.bookmark_flag = False
        # Flag set to True if the video is marked a favourite. Upon download,
        #   it's marked as a favourite if the same IV in the parent channel,
        #   playlist or folder (also in the parent's parent, and so on) is True
        self.fav_flag = False
        # Flag set to True if the video is marked as missing (the user has
        #   downloaded it from a channel/playlist, but the video has since
        #   been removed from that channel/playlist by its creator)
        # Videos are only marked missing when
        #   mainapp.TartubeApp.track_missing_videos_flag is set
        self.missing_flag = False
        # Flag set to True at the same time self.dl_sim_flag is set to True,
        #   showing that the video has been downloaded and not watched
        self.new_flag = False
        # Flag set to True if the video is marked add as added to the
        #   'Waiting Videos' system folder
        self.waiting_flag = False

        # The video's filename and extension
        self.file_name = None
        self.file_ext = None

        # When a video is marked to be downloaded in the fixed 'Temporary
        #   Videos' folder, we store the name of the original parent channel/
        #   playlist/folder here, for display in the Video Catalogue
        self.orig_parent = None

        # Flag set to True once the file has been downloaded, and is confirmed
        #   to exist in Tartube's data directory
        self.dl_flag = False
        # Flag set to True if a this video is a video clip has been split off
        #   from another video in Tartube's database (which may or may not
        #   still exist)
        self.split_flag = False
        # The size of the video (in bytes)
        self.file_size = None
        # The video's upload time (in Unix time)
        # YouTube (etc) only supplies a date, which Tartube then converts into
        #   seconds, so videos uploaded on the same day will have the same
        #   value for self.upload_time)
        self.upload_time = None
        # The time at which Tartube downloaded this video (in Unix time)
        # When downloading a channel or playlist, we assume that YouTube (etc)
        #   supplies us with the most recent upload first
        # Therefore, when sorting videos by time, if self.upload_time is the
        #   same (multiple videos were uploaded on the same day), then those
        #   videos are sorted with the lowest value of self.receive_time first
        self.receive_time = None
        # The video's duration (in integer seconds)
        self.duration = None
        # For videos in a channel or playlist (i.e. a media.Video object whose
        #   parent is a media.Channel or media.Playlist object), the video's
        #   index in the channel/playlist. (The server supplies an index even
        #   for a channel, and the user might want to convert a channel to a
        #   playlist)
        # For videos whose parent is a media.Folder, the value remains as None
        self.index = None

        # Video description. A string of any length, containing newline
        #   characters if necessary. (Set to None if the video description is
        #   not known)
        self.descrip = None
        # Video short description - the first line in self.descrip, limited to
        #   a certain number of characters (specifically,
        #   mainwin.MainWin.very_long_string_max_len)
        self.short = None

        # List of timestamps, extracted from the video's description and/or
        #   metadata, or added manually by the user
        # List in groups of three, in the form
        #   [start_stamp, stop_stamp, clip_title]
        # The timestamps are strings in the form n+:n+[:n+], e.g. '15:52',
        #   '01:15:52'
        # When the list of timestamps is extracted from a video's description/
        #   metadata, 'stop_stamp' is None. It is usually set when extracted
        #   from the metadata file
        # When 'stop_stamp' is None, the clip is presumed to be the same as the
        #   next 'start_stamp', or (if there are no more timestamps) the end of
        #   the video
        # The user can insert their own groups of timestamps, in which case
        #   'start_stamp' is compulsory, and 'stop_stamp' is optional (None if
        #   not specified)
        # 'clip_title' is always optional, and is None if not specified
        self.stamp_list = []
        # List containing data retrieved from SponsorBlock, or added manually
        #   by the user
        # Every item in the list is a dictionary containing data for a single
        #   video slice, in the form:
        #       mini_dict['category'] = One of the values in
        #           formats.SPONSORBLOCK_CATEGORY_LIST (e.g. 'sponsor')
        #       mini_dict['action'] = One of the values in
        #           formats.SPONSORBLOCK_ACTION_LIST (e.g. 'skip')
        #       mini_dict['start_time']
        #       mini_dict['stop_time'] = Floating point values in seconds,
        #           the beginning and end of the slice. If 'stop_time' is None,
        #           the end of the video is used
        #       mini_dict['duration'] = The video duration, as reported by
        #           SponsorBlock. This valus is not required by Tartube code,
        #           and its default value is 0
        self.slice_list = []
        # List containing video comments, extracted from the video's metadata.
        #   Only popuplated when downloading the video with yt-dlp
        # List of dictionaries, sorted by timestamp (most recent first). Each
        #   dictionary contains a reduced set of the keys extracted from yt-dl
        #   data, including these compulsory items:
        #       ['id']: (int) Simple seequential integer ID, the first omment
        #           added to the list is 1
        #       ['text']: (str) Text of the comment itself
        #       ['parent']: (int): ID of the parent comment, or None if no
        #           parent
        # These items are optional:
        #       ['timestamp']: (int) Epoch timestamp of the comment. As of
        #           v2.3.318, all comments in a YouTube video share the same
        #           timestamp
        #       ['time']: (str) String describing the comment age, e.g. '3 days
        #           ago'
        #       ['author']: (str) Name of comment author
        #       ['likes']: (int) Number of likes
        #       ['fav_flag']: (bool) True if comment favourited, False if not
        #       ['ul_flag']: (bool) True if commenter is uploader, False if not
        self.comment_list = []

        # List of error/warning messages generated the last time the video was
        #   checked or downloaded. Both set to empty lists if the video has
        #   never been checked or downloaded, or if there was no error/warning
        #   on the last check/download attempt
        # NB If an error/warning message is generated when downloading a
        #   channel or playlist, the message is stored in the media.Channel
        #   or media.Playlist object instead
        self.error_list = []
        self.warning_list = []

        # IVs used only when the download operation is launched from the
        #   Classic Mode tab
        # Flag set to True if this is a dummy media.Video object
        self.dummy_flag = False
        # The destination directory for the download
        self.dummy_dir = None
        # The full path to a downloaded file, if available
        self.dummy_path = None
        # The video/audio format to use
        # Valid strings are the values in formats.VIDEO_FORMAT_LIST and
        #   formats.AUDIO_FORMAT_LIST, which attemps to download the media in
        #   that format
        # Also valid are the same values preceded by 'convert_', which uses
        #   FFmpeg/AVConv to convert the downloaded media into the specified
        #   format
        # Also valid is None, in which case the format(s) specified by the
        #   General Options Manager are u sed
        self.dummy_format = None

        # Code
        # ----

        # Update the parent
        if parent_obj:
            self.parent_obj.add_child(app_obj, self, no_sort_flag)


    # Public class methods


    def ancestor_is_favourite(self):

        """Called by mainapp.TartubeApp.mark_video_downloaded().

        Checks whether any ancestor channel, playlist or folder is marked as
        favourite.

        Returns:

            True if the parent (or the parent's parent, and so on) is marked
            favourite, False otherwise

        """

        parent_obj = self.parent_obj

        while parent_obj:
            if parent_obj.fav_flag:
                return True
            else:
                parent_obj = parent_obj.parent_obj

        return False


    def fetch_tooltip_text(self, app_obj, max_length=None,
    show_error_flag=False):

        """Can be called by anything.

        Returns a string to be used as a tooltip for this video.

        Args:

            app_obj (mainapp.TartubeApp): The main application

            max_length (int or None): If specified, the maximum line length, in
                characters

            show_error_flag (bool): If True, show the first error/warning
                generated by the channel/playlist/folder

        Returns:

            Text containing the video's file path and source, ready for display
            in a tooltip

        """

        if not self.dummy_flag:

            translate_note = _(
                'TRANSLATOR\'S NOTE: WAITING = livestream not started,' \
                + ' LIVE = livestream started',
            )

            if self.live_mode == 1:
                live_str = ' <' + _('WAITING') + '>'
            elif self.live_mode == 2:
                live_str = ' <' + _('LIVE') + '>'
            else:
                live_str = ''

            text \
            = ' #' + str(self.dbid) + live_str + ':   ' + self.name + '\n\n'

            if self.parent_obj:

                if isinstance(self.parent_obj, Channel):
                    text += _('Channel:') + ' '
                elif isinstance(self.parent_obj, Playlist):
                    text += _('Playlist:') + ' '
                else:
                    text += _('Folder:') + ' '

                text += self.parent_obj.name + '\n\n'

            translate_note = _(
                'TRANSLATOR\'S NOTE 2: Source = video/channel/playlist URL',
            )

            text += _('Source:') + '\n'
            if self.source is None:
                text += '<' + _('unknown') + '>'
            else:
                text += self.source

            text += '\n\n' + _('File:') + '\n'
            if self.file_name is None:
                text += '<' + _('unknown') + '>'
            else:
                text += self.get_actual_path(app_obj)

        else:

            # When the download operation is launched from the Classic Mode
            #   tab, there is less to display
            text = _('Source:') + '\n'
            if self.source is None:
                text += '<' + _('unknown') + '>'
            else:
                text += self.source

            if self.dummy_path is not None:
                text += '\n\n' + _('File:') + '\n' + self.dummy_path

        # Show the first error/warning
        if show_error_flag and app_obj.show_tooltips_extra_flag:

            error_warning_list = self.error_list + self.warning_list
            length = len (error_warning_list)
            if error_warning_list:

                text += '\n\n' + _('Errors\Warnings') + ' (' \
                + str(length) + '):\n' + str(error_warning_list.pop(0))

                if length > 1:
                    text += '\n...'

        # Apply a maximum line length, if required
        if max_length is not None:
            text = utils.tidy_up_long_descrip(text, max_length)

        return text


    def read_video_descrip(self, app_obj, max_length):

        """Can be called by anything.

        Reads the .description file, if it exists, and updates IVs.

        Args:

            app_obj (mainapp.TartubeApp): The main application

            max_length (int): When storing the description in this object's
                IVs, the maximum line length to use

        """

        descrip_path = self.check_actual_path_by_ext(app_obj, '.description')
        if descrip_path:

            text = app_obj.file_manager_obj.load_text(descrip_path)
            if text is not None:
                self.set_video_descrip(app_obj, text, max_length)


    def extract_timestamps_from_descrip(self, app_obj):

        """Can be called by anything. Often called by
        self.set_video_descrip().

        From the video description stored as self.descrip, attempt to extract
        the video's timestamps.

        Compiles a list in groups of three, in the form
            [start_stamp, stop_stamp, clip_title]
        'start_stamp' is a string in the form h+:m+[:s+], e.g. '15:52',
            '01:15:52'
        'stop_stamp' is always None, so that if 'start_stamp' is used to split
            a video clip, the clip ends at the next 'start_stamp' (or at the
            end of the video). It's up to the user to specify their own
            'stop_stamp' values explicitly, if they need them.

        Args:

            app_obj (mainapp.TartubeApp): The main application

        """

        if self.descrip is None or self.descrip == '':
            return

        regex = r'^\s*(' + app_obj.timestamp_regex + r')(\s.*)'
        rev_regex = r'^(.*\s)(' + app_obj.timestamp_regex + r')\s*$'
        digit_count = 0

        line_list = self.descrip.split('\n')
        temp_list = []
        stamp_list = []

        for line in line_list:

            # (To improve detection, remove initial/final non-alphanumeric
            #   characters)
            line = re.sub('^[\W\s]+', '', line)
            line = re.sub('[\W\s]+$', '', line)

            # We would like every timestamp to be in the same format, i.e.
            #   either none of them have an h+ component, or all of them
            #   have an h+ component, with exactly the same number of digits
            #   (with any necessary leading zeroes)
            # Extract the timestamps into a temporary list. For each timestamp,
            #   count the number of digits for the h+ component, and store the
            #   highest number of digits found

            # 15:52 Title
            result = re.match(regex, line)

            if result:

                title = result.groups()[5]
                hours = result.groups()[2]
                minutes = result.groups()[3]
                seconds = result.groups()[4]

            else:

                # Title 15:52
                result = re.match(rev_regex, line)
                if result:

                    title = result.groups()[0]
                    hours = result.groups()[3]
                    minutes = result.groups()[4]
                    seconds = result.groups()[5]

            if result:

                # Remove punctuation in the title, such as the hyphen in a line
                #   like 'Intro - 15.52', and strip leading/trailing whitespace
                if title != '':
                    # !!! DEBUG This is not yet tested on other alphabets
                    title = re.sub(r'\s\W+\s', ' ', title)
                    title = utils.strip_whitespace(title)

                # Use None as the title, rather than an empty string
                if title == '':
                    title = None

                # Count the number of digits in the h+ component, having
                #   removed any leading zeroes
                if hours is not None:
                    this_len = len(str(int(hours)))
                    if this_len > digit_count:
                        digit_count = this_len

                # Temporarily store the components
                temp_list.append( [title, hours, minutes, seconds] )

        # Now compile the a list of timestamps, formatted as strings in the
        #   form h:mm:ss or mm:ss, and with the correct number of leading
        #   zeroes applied
        for mini_list in temp_list:

            stamp_list.append(
                [
                    utils.timestamp_quick_format(   # 'start_stamp'
                        app_obj,
                        mini_list[1],               # Hours (optional)
                        mini_list[2],               # Minutes
                        mini_list[3],               # Seconds
                        digit_count,                # Number of digits in h+
                    ),
                    None,                           # 'stop_stamp'
                    mini_list[0],                   # 'clip_title'

                ]
            )

        # Sort by timestamp (since we can't assume the description does that)
        stamp_list.sort()
        self.stamp_list = stamp_list.copy()


    def extract_timestamps_from_chapters(self, app_obj, chapter_list):

        """Called by downloads.VideoDownloader.confirm_sim_video() and
        mainapp.TartubeApp.update_video_from_json().

        When supplied with a list of chapters from the video's metadata,
        convert that data and store it as a list of timestamps.

        For the sake of simplicity, the calling function doesn't check whether
        we're allowed to do that, so this function does the checking.

        Args:

            app_obj (mainapp.TartubeApp): The main application

            chapter_list (list): An ordered list containing a series of python
                dictionaries. Each dictionary corresponds to the start of a
                single chapter, and is expected to contain the keys
                'start_time', 'end_time' and 'title'. YouTube always supplies
                all three, but in common with other parts of the code, we will
                still accept the chapter if 'end_time' and/or 'title' are
                missing

        """

        # Do the checking, as promised above
        if not app_obj.video_timestamps_extract_json_flag \
        or (self.stamp_list and not app_obj.video_timestamps_replace_flag):
            return

        # Extract each chapter in turn
        stamp_list = []
        while chapter_list:

            chapter_dict = chapter_list.pop(0)

            if not 'start_time' in chapter_dict:
                # Ignore this chapter
                continue
            else:
                # Tartube timestamps use whole seconds, so round up any
                #   fractional values
                start = int(chapter_dict['start_time'])

            stop = None
            if 'end_time' in chapter_dict:
                stop = int(chapter_dict['end_time'])
                # If a chapter stops at second #10, the next chapter starts at
                #   second #10
                # But FFmpeg expects the chapter to stop at second #9, so take
                #   account of that
                if chapter_list:
                    stop -= 1

            clip_title = None
            if 'title' in chapter_dict and chapter_dict['title'] != '':
                clip_title = chapter_dict['title']

            # 'start' and 'stop' are in seconds. Convert them to a string in
            #   the usual format, 'mm:ss' or 'h:mm:ss', where the 'h' component
            #   can contain any number of digits
            # The True flag tells the function not to include the 'h' component
            #   if it's zero
            start_stamp = utils.convert_seconds_to_string(start, True)
            if stop is not None:
                stop_stamp = utils.convert_seconds_to_string(stop, True)
            else:
                stop_stamp = None

            stamp_list.append( [start_stamp, stop_stamp, clip_title] )

        # All done
        self.stamp_list = stamp_list


    def set_slices(self, slice_list):

        """Can be called by anything.

        Sets the video's slice list, first sorting it.
        """

        self.slice_list \
        = list(sorted(slice_list, key=lambda x:x['start_time']))


    def convert_slices(self, slice_data_list):

        """Can be called by anything, but principally called by
        utils.fetch_slice_data().

        A modified form of self.set_slices().

        From SponsorBlock we retrieve a slice data for a video. Convert the
        data from used by SponsorBlock into the form used by Tartube, before
        saving it in self.slice_list.
        """

        new_list = []
        for old_mini_dict in slice_data_list:

            # (Filter out invalid data. Don't worry about the 'videoDuration'
            #   field, as Tartube doesn't need it; and ignore the 'UUID' field
            #   completely)
            if 'category' in old_mini_dict \
            and 'actionType' in old_mini_dict \
            and 'segment' in old_mini_dict:

                new_mini_dict = {}
                new_mini_dict['category'] = old_mini_dict['category']
                new_mini_dict['action'] = old_mini_dict['actionType']
                new_mini_dict['start_time'] = old_mini_dict['segment'][0]
                new_mini_dict['stop_time'] = old_mini_dict['segment'][1]
                new_mini_dict['duration'] = old_mini_dict['videoDuration']

                new_list.append(new_mini_dict)

        self.slice_list = list(sorted(new_list, key=lambda x:x['start_time']))


    def reset_slices(self):

        """Can be called by anything.

        Empties the video's slice list.
        """

        self.slice_list = []


    def set_timestamps(self, stamp_list):

        """Can be called by anything.

        Sets the video's timestamp list, first sorting it.
        """

        stamp_list.sort()
        self.stamp_list = stamp_list.copy()


    def reset_timestamps(self):

        """Can be called by anything.

        Empties the video's timestamp list.
        """

        self.stamp_list = []


    def set_comments(self, comment_list):

        """Can be called by anything.

        Sets the video's comments list, after sorting it.
        """

        # 'comment_list' contains a sequence of dictionaries. Some of the keys
        #   in the dictionaries are not required, and must be removed
        # The key is the original field provided by yt-dlp, the corresponding
        #   value is the field used by media.Video
        check_dict = {
            'id': 'id',
            'text': 'text',
            'timestamp': 'timestamp',
            'time_text': 'time',
            'like_count': 'likes',
            'is_favorited': 'fav_flag',
            'author': 'author',
            'author_is_uploader': 'ul_flag',
            'parent': 'parent',
        }

        # Use simple sequential integers for the 'id' and 'parent' fields
        id_count = 1
        parent_dict = {}

        # Process each comment
        new_list = []

        for mini_dict in comment_list:

            new_dict = {}

            for key in mini_dict.keys():
                if key in check_dict and mini_dict[key] is not None:

                    if key == 'id':
                        this_id = id_count
                        parent_dict[mini_dict[key]] = this_id
                        new_dict['id'] = this_id

                        id_count += 1

                    elif key == 'parent':
                        if not mini_dict[key] in parent_dict:
                            new_dict['parent'] = None
                        else:
                            new_dict['parent'] = parent_dict[mini_dict[key]]

                    else:
                        new_dict[check_dict[key]] = mini_dict[key]

            # This key is also compulosry; add a null parent, if not found
            if not 'parent' in new_dict:
                new_dict['parent'] = None

            # These keys are compulsory, ignore the comment if they're not
            #   found
            if 'id' in new_dict and 'text' in new_dict:
                new_list.append(new_dict)

        # Sort comments by timestamp
        # v2.3.317 disabled, since all timestamps are the same for each video
        #   at the moment
#        new_list = list(sorted(new_list, key=lambda x:x['time']))

        # Update the IV
        self.comment_list = new_list


    def reset_comments(self):

        """Can be called by anything.

        Empties the video's comment list.
        """

        self.comment_list = []


    # Set accessors


    def set_archive_flag(self, flag):

        if flag:
            self.archive_flag = True
        else:
            self.archive_flag = False


    def set_bookmark_flag(self, flag):

        if flag:
            self.bookmark_flag = True
        else:
            self.bookmark_flag = False


    def set_cloned_name(self, orig_obj):

        """Called by mainwin.MainWin.on_video_catalogue_mark_temp_dl(), etc.

        When a copy of a video is marked to be downloaded in the fixed
        'Temporary Videos' folder, we can copy across the original video's
        name and description.

        Args:

            orig_obj (media.Video): The original video

        """

        self.name = orig_obj.name
        self.nickname = orig_obj.nickname
        self.descrip = orig_obj.descrip
        self.short = orig_obj.short


    def set_dl_flag(self, flag=False):

        self.dl_flag = flag

        if self.receive_time is None:
            self.receive_time = int(time.time())


    def set_dl_sim_flag(self, flag):

        if flag:
            self.dl_sim_flag = True
        else:
            self.dl_sim_flag = False


    def set_dummy(self, url, dir_str, format_str):

        """Called by mainwin.MainWin.classic_mode_tab_add_urls(), immediately
        after the call to self.new().

        Sets up this media.Video object as a dummy object, not added to the
        media data registry.

        Args:

            url (str): The URL to download (which might reperesent a video,
                channel or playlist; the dummy media.Video object represents
                all of them)

            dir_str (str): The destination directory for the download, chosen
                by the user

            format_str (str): One of the video/audio formats specified by
                formats.VIDEO_FORMAT_LIST and formats.AUDIO_FORMAT_LIST

        """

        self.dummy_flag = True
        self.dummy_dir = dir_str
        self.dummy_path = None
        self.dummy_format = format_str

        self.source = url


    def set_dummy_path(self, path):

        self.dummy_path = path


    def set_duration(self, duration=None):

        if duration is not None:
            if duration != int(duration):
                self.duration = int(duration) + 1
            else:
                self.duration = duration

        else:
            self.duration = None


    def set_file(self, filename, extension):

        self.file_name = filename
        self.file_ext = extension


    def set_file_ext(self, extension):

        self.file_ext = extension


    def set_file_from_path(self, path):

        directory, this_file = os.path.split(path)
        filename, extension = os.path.splitext(this_file)
        self.file_name = filename
        self.file_ext = extension


    def set_file_size(self, size=None):

        self.file_size = size


    def set_index(self, index):

        if index is None:
            self.index = None
        else:
            self.index = int(index)


    def set_live_mode(self, mode):

        self.live_mode = mode


    def set_live_data(self, live_data_dict):

        """Interprets the dictionary returned by
        utils.extract_livestream_data().
        """

        if 'live_msg' in live_data_dict:
            self.live_msg = live_data_dict['live_msg']
        else:
            self.live_msg = ''

        if 'live_time' in live_data_dict:
            self.live_time = live_data_dict['live_time']
        else:
            self.live_time = 0

        if 'live_debut_flag' in live_data_dict:
            self.live_debut_flag = live_data_dict['live_debut_flag']


    def set_missing_flag(self, flag):

        if flag:
            self.missing_flag = True
        else:
            self.missing_flag = False


    def set_mkv(self):

        """Called by mainapp.TartubeApp.update_video_when_file_found() and
        refresh.RefreshManager.refresh_from_default_destination().

        When the warning 'Requested formats are incompatible for merge and will
        be merged into mkv' has been seen, the calling function has found an
        .mkv file rather than the .mp4 file it was expecting.

        Update the IV.
        """

        self.file_ext = '.mkv'


    def set_name(self, name):

        self.name = name


    def set_new_flag(self, flag):

        if flag:
            self.new_flag = True
        else:
            self.new_flag = False


#   def set_options_obj():      # Inherited from GenericMedia


    def set_orig_parent(self, parent_obj):

        self.orig_parent = parent_obj.name


    def set_parent_obj(self, parent_obj):

        self.parent_obj = parent_obj


    def set_receive_time(self, other_video_obj=None):

        """Can be called by anything.

        Usually, the video's receive time is set to the moment the media.Video
        object is created; but in case we need to clone another video's
        receive time, the other video can be specified as an argument.

        Args:

            other_vide_obj (media.Video): The video whose .receive_time should
                be clone

        """

        if other_video_obj is None:
            self.receive_time = int(time.time())
        else:
            self.receive_time = other_video_obj.receive_time


    def set_source(self, source):

        self.source = source


    def set_split_flag(self, flag):

        if flag:
            self.split_flag = True
        else:
            self.split_flag = False


    def set_upload_time(self, unix_time=None):

        self.upload_time = int(unix_time)


    def set_vid(self, vid):

        self.vid = vid


    def set_video_descrip(self, app_obj, descrip, max_length):

        """Can be called by anything.

        Converts the video description into a list of lines, max_length
        characters long (longer lines are split into shorter ones).

        Then uses the first line to set the short description, and uses all
        lines to set the full description.

        Args:

            app_obj (mainapp.TartubeApp): The main application

            descrip (str): The video description

            max_length (int): A maximum line size

        """

        if descrip is not None and descrip != '':

            self.descrip = utils.tidy_up_long_descrip(descrip, max_length)
            self.short = utils.shorten_string(descrip, max_length)

            # Extract timestamps from the description, if allowed
            if app_obj.video_timestamps_extract_descrip_flag \
            and (
                app_obj.video_timestamps_replace_flag \
                or not self.stamp_list
            ):
                self.extract_timestamps_from_descrip(app_obj)

        else:
            self.descrip = None
            self.short = None


    def reset_video_descrip(self):

        self.descrip = None
        self.short = None


    def set_waiting_flag(self, flag):

        if flag:
            self.waiting_flag = True
        else:
            self.waiting_flag = False


    def set_was_live_flag(self, flag):

        if flag:
            self.was_live_flag = True
        else:
            self.was_live_flag = False


    # Get accessors


    def get_actual_path(self, app_obj):

        """Can be called by anything.

        Returns the full path to the video file in its actual location.

        If self.dbid and self.master_dbid are the same, then files are
        downloaded to the default location; the sub-directory belonging to the
        channel/playlist/folder. In that case, this function returns the same
        value as self.get_default_path().

        If self.master_dbid is not the same as self.dbid, then files are
        actually downloaded into the sub-directory used by another channel,
        playlist or folder. This function returns a path to the file in that
        sub-directory.

        Args:

            app_obj (mainapp.TartubeApp): The main application

        Returns:

            The path described above

        """

        return os.path.abspath(
            os.path.join(
                self.parent_obj.get_actual_dir(app_obj),
                self.file_name + self.file_ext,
            ),
        )


    def get_actual_path_by_ext(self, app_obj, ext):

        """Can be called by anything.

        Returns the full path to a file associated with the video; specifically
        one with the same file name, but a different extension (for example,
        the video's thumbnail file).

        If self.dbid and self.master_dbid are the same, then files are
        downloaded to the default location; the sub-directory belonging to the
        channel/playlist/folder. In that case, this function returns the same
        value as self.get_default_path_by_ext().

        If self.master_dbid is not the same as self.dbid, then files are
        actually downloaded into the sub-directory used by another channel,
        playlist or folder. This function returns a path to the file in that
        sub-directory.

        Args:

            app_obj (mainapp.TartubeApp): The main application

            ext (str): The extension, e.g. 'png' or '.png'

        Returns:

            The full file path (the file may or may not exist)

        """

        # Add the full stop, if not supplied by the calling function
        if not ext.find('.') == 0:
            ext = '.' + ext

        return os.path.abspath(
            os.path.join(
                self.parent_obj.get_actual_dir(app_obj),
                self.file_name + ext,
            ),
        )


    def get_actual_path_in_subdirectory_by_ext(self, app_obj, ext):

        """Can be called by anything.

        Modified version of self.get_actual_path_by_ext().

        The file might be stored in the same directory as its video, or in the
        sub-directory '.thumbs' (for thumbnails) or '.data' (for everything
        else).

        self.get_actual_path_by_ext() returns the former; this function returns
        the latter.

        Args:

            app_obj (mainapp.TartubeApp): The main application

            ext (str): The extension, e.g. 'png' or '.png'

        Returns:

            The full file path (the file may or may not exist)

        """

        # Add the full stop, if not supplied by the calling function
        if not ext.find('.') == 0:
            ext = '.' + ext

        # There are two sub-directories, one for thumbnails, one for metadata
        if ext in formats.IMAGE_FORMAT_EXT_LIST:

            return os.path.abspath(
                os.path.join(
                    self.parent_obj.get_actual_dir(app_obj),
                    app_obj.thumbs_sub_dir,
                    self.file_name + ext,
                ),
            )

        else:

            return os.path.abspath(
                os.path.join(
                    self.parent_obj.get_actual_dir(app_obj),
                    app_obj.metadata_sub_dir,
                    self.file_name + ext,
                ),
            )


    def check_actual_path_by_ext(self, app_obj, ext):

        """Can be called by anything.

        Modified version of self.get_actual_path_by_ext().

        The file has the same name as its video, but with a different extension
        (for example, the video's thumbnail file).

        The file might be stored in the same directory as its video, or in the
        sub-directory '.thumbs' (for thumbnails) or '.data' (for everything
        else).

        This function checks to see whether the file exists in the same
        directory as its folder and, if so, returns the file path. If not, it
        checks to see whether the file exists in the '.thumbs' or '.data'
        sub-directory and, if so, returns the file path.

        Args:

            app_obj (mainapp.TartubeApp): The main application

            ext (str): The extension, e.g. 'png' or '.png'

        Returns:

            The full path to the file if it exists, or None if not

        """

        # Add the full stop, if not supplied by the calling function
        if not ext.find('.') == 0:
            ext = '.' + ext

        # Check the normal location
        main_path = os.path.abspath(
            os.path.join(
                self.parent_obj.get_actual_dir(app_obj),
                self.file_name + ext,
            ),
        )

        if os.path.isfile(main_path):
            return main_path

        # Check the sub-directory location
        if ext in formats.IMAGE_FORMAT_EXT_LIST:

            subdir_path = os.path.abspath(
                os.path.join(
                    self.parent_obj.get_actual_dir(app_obj),
                    app_obj.thumbs_sub_dir,
                    self.file_name + ext,
                ),
            )

        else:

            subdir_path = os.path.abspath(
                os.path.join(
                    self.parent_obj.get_actual_dir(app_obj),
                    app_obj.metadata_sub_dir,
                    self.file_name + ext,
                ),
            )

        if os.path.isfile(subdir_path):
            return subdir_path
        else:
            return None


    def get_default_path(self, app_obj):

        """Can be called by anything.

        Returns the full path to the video file in its default location.

        If self.master_dbid is not the same as self.dbid, then files are
        actually downloaded into the sub-directory used by another channel,
        playlist or folder. To get the actual path to the video file, call
        self.get_actual_path().

        Args:

            app_obj (mainapp.TartubeApp): The main application

        Returns:

            The full file path (the file may or may not exist)

        """

        return os.path.abspath(
            os.path.join(
                self.parent_obj.get_default_dir(app_obj),
                self.file_name + self.file_ext,
            ),
        )


    def get_default_path_by_ext(self, app_obj, ext):

        """Can be called by anything.

        Returns the full path to a file associated with the video; specifically
        one with the same file name, but a different extension (for example,
        the video's thumbnail file).

        If self.master_dbid is not the same as self.dbid, then files are
        actually downloaded into the sub-directory used by another channel,
        playlist or folder. To get the actual path to the associated file, call
        self.get_actual_path_by_ext().

        Args:

            app_obj (mainapp.TartubeApp): The main application

            ext (str): The extension, e.g. 'png' or '.png'

        Returns:

            The full file path (the file may or may not exist)

        """

        # Add the full stop, if not supplied by the calling function
        if not ext.find('.') == 0:
            ext = '.' + ext

        return os.path.abspath(
            os.path.join(
                self.parent_obj.get_default_dir(app_obj),
                self.file_name + ext,
            ),
        )


    def get_default_path_in_subdirectory_by_ext(self, app_obj, ext):

        """Can be called by anything.

        Modified version of self.get_default_path_by_ext().

        The file might be stored in the same directory as its video, or in the
        sub-directory '.thumbs' (for thumbnails) or '.data' (for everything
        else).

        self.get_default_path_by_ext() returns the former; this function
        returns the latter.

        Args:

            app_obj (mainapp.TartubeApp): The main application

            ext (str): The extension, e.g. 'png' or '.png'

        Returns:

            The full file path (the file may or may not exist)

        """

        # Add the full stop, if not supplied by the calling function
        if not ext.find('.') == 0:
            ext = '.' + ext

        # There are two sub-directories, one for thumbnails, one for metadata
        if ext in formats.IMAGE_FORMAT_EXT_LIST:

            return os.path.abspath(
                os.path.join(
                    self.parent_obj.get_default_dir(app_obj),
                    app_obj.thumbs_sub_dir,
                    self.file_name + ext,
                ),
            )

        else:

            return os.path.abspath(
                os.path.join(
                    self.parent_obj.get_default_dir(app_obj),
                    app_obj.metadata_sub_dir,
                    self.file_name + ext,
                ),
            )


    def get_file_size_string(self):

        """Can be called by anything.

        Converts self.file_size, in bytes, into a formatted string.

        Returns:

            The converted string, or None if self.file_size is not set

        """

        if self.file_size:
            return utils.format_bytes(self.file_size)
        else:
            return ""


    def get_receive_date_string(self, pretty_flag=False):

        """Can be called by anything.

        A modified version of self.get_receive_time_string(), returning just
        the date, not the date and the time.

        Args:

            pretty_flag (bool): If True, the strings 'Today' and 'Yesterday'
                are returned, when possible

        Returns:

            The formatted string, or None if self.receive_time is not set

        """

        if not self.receive_time:
            return None

        elif not pretty_flag:
            timestamp = datetime.datetime.fromtimestamp(self.receive_time)
            return timestamp.strftime('%Y-%m-%d')

        else:
            today = datetime.date.today()
            today_str = today.strftime('%y%m%d')

            yesterday = datetime.date.today() - datetime.timedelta(days=1)
            yesterday_str = yesterday.strftime('%y%m%d')

            testday = datetime.datetime.fromtimestamp(self.receive_time)
            testday_str = testday.strftime('%y%m%d')

            if testday_str == today_str:
                return _('Today')
            elif testday_str == yesterday_str:
                return _('Yesterday')
            else:
                return testday.strftime('%Y-%m-%d')


    def get_receive_time_string(self):

        """Can be called by anything.

        Converts self.upload_time, in Unix time, into a formatted string.

        Returns:

            The formatted string, or None if self.receive_time is not set

        """

        if self.receive_time:
            return str(datetime.datetime.fromtimestamp(self.receive_time))
        else:
            return None


    def get_upload_date_string(self, pretty_flag=False):

        """Can be called by anything.

        A modified version of self.get_upload_time_string(), returning just the
        date, not the date and the time.

        Args:

            pretty_flag (bool): If True, the strings 'Today' and 'Yesterday'
                are returned, when possible

        Returns:

            The formatted string, or None if self.upload_time is not set

        """

        if not self.upload_time:
            return None

        elif not pretty_flag:
            timestamp = datetime.datetime.fromtimestamp(self.upload_time)
            return timestamp.strftime('%Y-%m-%d')

        else:
            today = datetime.date.today()
            today_str = today.strftime('%y%m%d')

            yesterday = datetime.date.today() - datetime.timedelta(days=1)
            yesterday_str = yesterday.strftime('%y%m%d')

            testday = datetime.datetime.fromtimestamp(self.upload_time)
            testday_str = testday.strftime('%y%m%d')

            if testday_str == today_str:
                return _('Today')
            elif testday_str == yesterday_str:
                return _('Yesterday')
            else:
                return testday.strftime('%Y-%m-%d')


    def get_upload_time_string(self):

        """Can be called by anything.

        Converts self.upload_time, in Unix time, into a formatted string.

        Returns:

            The formatted string, or None if self.upload_time is not set

        """

        if self.upload_time:
            return str(datetime.datetime.fromtimestamp(self.upload_time))
        else:
            return None


class Channel(GenericRemoteContainer):

    """Python class that handles a channel (e.g. on YouTube).

    Args:

        app_obj (mainapp.TartubeApp): The main application (not stored as an
            IV)

        dbid (int): A unique ID for this media data object

        name (str): The channel name

        parent_obj (media.Folder): The parent media data object, if any

        options_obj (options.OptionsManager): The object specifying download
            options for this channel, if any

    """


    # Standard class methods


    def __init__(self, app_obj, dbid, name, parent_obj=None, options_obj=None):

        # IV list - class objects
        # -----------------------
        # The parent object (a media.Folder object if this channel is
        #   downloaded into a particular sub-directory, or None otherwise)
        self.parent_obj = parent_obj
        # List of media.Video objects for this channel
        self.child_list = []
        # The options.OptionsManager object that specifies how this channel is
        #   downloaded (or None, if the parent's options.OptionsManager object
        #   should be used instead)
        self.options_obj = options_obj


        # IV list - other
        # ---------------
        # Unique media data object ID (an integer)
        self.dbid = dbid

        # Channel name
        self.name = name
        # Channel nickname (displayed in the Video Index; the same as .name,
        #   unless the user changes it)
        self.nickname = name
        # Download source (a URL)
        self.source = None
        # RSS feed source (a URL), used by livestream operations on compatible
        #   websites. For YouTube channels, set automatically during a download
        #   operation. For channels on other websites, can be set manually
        self.rss = None

        # The value of mainapp.TartubeApp.catalogue_sort_mode, the last time
        #   self.sort_children() was called. (When the user changes the sort
        #   mode, we don't sort self.child_list() until we actually need to
        #   display it)
        self.last_sort_mode = 'default'

        # External download destination - a directory at a fixed position in
        #   the filesystem, outside Tartube's data directory. Use is not
        #   recommended because of potential file read/write problems, but is
        #   available to users who need it
        # If specified, the full path to the external directory
        self.external_dir = None
        # Alternative download destination - the dbid of a channel, playlist or
        #   folder in whose directory videos, thumbnails (etc) are downloaded.
        #   By default, set to the dbid of this channel; but can be set to the
        #   dbid of any other channel/playlist/folder
        # Used for: (1) adding a channel and its playlists to the Tartube
        #   database, so that duplicate videos don't exist on the user's
        #   filesystem, (2) tying together, for example, a YouTube and a
        #   BitChute account, so that duplicate videos don't exist on the
        #   user's filesystem
        # NB A media data object can't have an alternative download destination
        #   and itself be the alternative download destination for another
        #   media data object; it must be one or the other (or neither)
        # NB Ignored if self.external_dir is specified
        self.master_dbid = dbid
        # A list of dbids for any channel, playlist or folder that uses this
        #   channel as its alternative destination
        self.slave_dbid_list = []

        # The flags in this group are mutually exclusive; only one flag (or
        #   none of them) should be True
        # Flag set to True if videos in this channel should be downloaded, but
        #   not added to the database. (If True, the channel and its videos
        #   are never checked)
        self.dl_no_db_flag = False
        # Flag set to True if this channel should never be checked or
        #   downloaded
        self.dl_disable_flag = False
        # Flag set to True if Tartube should always simulate the download of
        #   videos in this channel, or False if the downloads.DownloadManager
        #   object should decide whether to simulate, or not
        self.dl_sim_flag = False

        # Flag set to True if this channel is marked as favourite, meaning
        #   that all child video objects are automatically marked as
        #   favourites
        # (Child video objects will also be marked as favourite if one of this
        #   channel's ancestors are marked as favourite)
        self.fav_flag = False

        # The total number of child video objects
        self.vid_count = 0
        # The number of child video objects that are marked as bookmarked,
        #   downloaded, favourite, livestreams, missing, new and in the
        #   'Waiting Videos' system folders
        self.bookmark_count = 0
        self.dl_count = 0
        self.fav_count = 0
        self.live_count = 0
        self.missing_count = 0
        self.new_count = 0
        self.waiting_count = 0

        # List of error/warning messages generated the last time the channel
        #   was checked or downloaded. Both set to empty lists if the channel
        #   has never been checked or downloaded, or if there was no error/
        #   warning on the last check/download attempt
        # NB If an error/warning message is generated when downloading an
        #   individual video (not in a channel or playlist), the message is
        #   stored in the media.Video object
        self.error_list = []
        self.warning_list = []


        # Code
        # ----

        # Update the parent (if any)
        if self.parent_obj:
            self.parent_obj.add_child(app_obj, self)


    # Public class methods


#   def add_child():                # Inherited from GenericRemoteContainer


#   def del_child():                # Inherited from GenericContainer


#   def sort_children():            # Inherited from GenericRemoteContainer


    # Set accessors


#   def reset_counts():             # Inherited from GenericContainer


#   def set_dl_sim_flag():          # Inherited from GenericMedia


#   def set_options_obj():          # Inherited from GenericMedia


#   def set_source():               # Inherited from GenericRemoteContainer


    # Get accessors


#   def get_actual_dir():           # Inherited from GenericContainer


#   def get_default_dir():          # Inherited from GenericContainer


#   def get_relative_actual_dir():  # Inherited from GenericContainer


#   def get_relative_default_dir(): # Inherited from GenericContainer


    def never_called_func(self):

        """Function that is never called, but which makes this class object
        collapse neatly in my IDE."""

        pass


class Playlist(GenericRemoteContainer):

    """Python class that handles a playlist (e.g. on YouTube).

    Args:

        app_obj (mainapp.TartubeApp): The main application (not stored as an
            IV)

        dbid (int): A unique ID for this media data object

        name (str): The playlist name

        parent_obj (media.Folder): The parent media data object, if any

        options_obj (options.OptionsManager): The object specifying download
            options for this channel, if any

    """


    # Standard class methods


    def __init__(self, app_obj, dbid, name, parent_obj=None, options_obj=None):

        # IV list - class objects
        # -----------------------
        # The parent object (a media.Folder object if this playlist is
        #   downloaded into a particular sub-directory, or None otherwise)
        self.parent_obj = parent_obj
        # List of media.Video objects for this playlist
        self.child_list = []
        # The options.OptionsManager object that specifies how this playlist
        #   is downloaded (or None, if the parent's options.OptionsManager
        #   object should be used instead)
        self.options_obj = options_obj


        # IV list - other
        # ---------------
        # Unique media data object ID (an integer)
        self.dbid = dbid

        # Playlist name
        self.name = name
        # Playlist nickname (displayed in the Video Index; the same as .name,
        #   unless the user changes it)
        self.nickname = name
        # Download source (a URL)
        self.source = None
        # RSS feed source (a URL), used by livestream operations on compatible
        #   websites. Set automatically for YouTube videos, and can be set
        #   manually by the user for other websites
        self.rss = None

        # The value of mainapp.TartubeApp.catalogue_sort_mode, the last time
        #   self.sort_children() was called. (When the user changes the sort
        #   mode, we don't sort self.child_list() until we actually need to
        #   display it)
        self.last_sort_mode = 'default'

        # External download destination - a directory at a fixed position in
        #   the filesystem, outside Tartube's data directory. Use is not
        #   recommended because of potential file read/write problems, but is
        #   available to users who need it
        # If specified, the full path to the external directory
        self.external_dir = None
        # Alternative download destination - the dbid of a channel, playlist or
        #   folder in whose directory videos, thumbnails (etc) are downloaded.
        #   By default, set to the dbid of this playlist; but can be set to the
        #   dbid of any other channel/playlist/folder
        # Used for: (1) adding a channel and its playlists to the Tartube
        #   database, so that duplicate videos don't exist on the user's
        #   filesystem, (2) tying together, for example, a YouTube and a
        #   BitChute account, so that duplicate videos don't exist on the
        #   user's filesystem
        # NB A media data object can't have an alternative download destination
        #   and itself be the alternative download destination for another
        #   media data object; it must be one or the other (or neither)
        # NB Ignored if self.external_dir is specified
        self.master_dbid = dbid
        # A list of dbids for any channel, playlist or folder that uses this
        #   playlist as its alternative destination
        self.slave_dbid_list = []

        # The flags in this group are mutually exclusive; only one flag (or
        #   none of them) should be True
        # Flag set to True if videos in this playlist should be downloaded, but
        #   not added to the database. (If True, the playlist and its videos
        #   are never checked)
        self.dl_no_db_flag = False
        # Flag set to True if this playlist should never be checked or
        #   downloaded
        self.dl_disable_flag = False
        # Flag set to True if Tartube should always simulate the download of
        #   videos in this playlist, or False if the downloads.DownloadManager
        #   object should decide whether to simulate, or not
        self.dl_sim_flag = False

        # Flag set to True if this playlist is marked as favourite, meaning
        #   that all child video objects are automatically marked as
        #   favourites
        # (Child video objects will also be marked as favourite if one of this
        #   playlist's ancestors are marked as favourite)
        self.fav_flag = False

        # The total number of child video objects
        self.vid_count = 0
        # The number of child video objects that are marked as bookmarked,
        #   downloaded, favourite, livestreams, missing, new and in the
        #   'Waiting Videos' system folders
        self.bookmark_count = 0
        self.dl_count = 0
        self.fav_count = 0
        self.live_count = 0
        self.missing_count = 0
        self.new_count = 0
        self.waiting_count = 0

        # List of error/warning messages generated the last time the channel
        #   was checked or downloaded. Both set to empty lists if the channel
        #   has never been checked or downloaded, or if there was no error/
        #   warning on the last check/download attempt
        # NB If an error/warning message is generated when downloading an
        #   individual video (not in a channel or playlist), the message is
        #   stored in the media.Video object
        self.error_list = []
        self.warning_list = []


        # Code
        # ----

        # Update the parent (if any)
        if self.parent_obj:
            self.parent_obj.add_child(app_obj, self)


    # Public class methods


#   def add_child():                # Inherited from GenericRemoteContainer


#   def del_child():                # Inherited from GenericContainer


#   def sort_children():            # Inherited from GenericRemoteContainer


    # Set accessors


#   def reset_counts():             # Inherited from GenericContainer


#   def set_dl_sim_flag():          # Inherited from GenericMedia


#   def set_options_obj():          # Inherited from GenericMedia


#   def set_source():               # Inherited from GenericRemoteContainer


    # Get accessors


#   def get_actual_dir():           # Inherited from GenericContainer


#   def get_default_dir():          # Inherited from GenericContainer


#   def get_relative_actual_dir():  # Inherited from GenericContainer


#   def get_relative_default_dir(): # Inherited from GenericContainer


    def never_called_func(self):

        """Function that is never called, but which makes this class object
        collapse neatly in my IDE."""

        pass


class Folder(GenericContainer):

    """Python class that handles a sub-directory inside Tartube's data folder,
    into which other media data objects (media.Video, media.Channel,
    media.Playlist and other media.Folder objects) can be downloaded.

    Args:

        app_obj (mainapp.TartubeApp): The main application (not stored as an
            IV)

        dbid (int): A unique ID for this media data object

        name (str): The folder name

        parent_obj (media.Folder): The parent media data object, if any

        options_obj (options.OptionsManager): The object specifying download
            options for this channel, if any

        fixed_flag (bool): If True, this folder can't be deleted by the user

        priv_flag (bool): If True, the user can't add anything to this folder,
            because Tartube uses it for special purposes

        restrict_mode (str): 'full' if this folder can contain videos, but not
            channels/playlists/folders, 'partial' if this folder can contain
            videos and folders, but not channels and playlists, 'open' if this
            folder can contain any combination of videos, channels, playlists
            and folders

        temp_flag (bool): If True, the folder's contents should be deleted
            when Tartube shuts down (but the folder itself remains)

    """


    # Standard class methods


    def __init__(self, app_obj, dbid, name, parent_obj=None, options_obj=None,
    restrict_mode='open',  fixed_flag=False, priv_flag=False, temp_flag=False):

        # IV list - class objects
        # -----------------------
        # The parent object (another media.Folder object, or None if no parent)
        self.parent_obj = parent_obj
        # List of media.Video, media.Channel, media.Playlist and media.Folder
        #   objects for which this object is the parent
        self.child_list = []
        # The options.OptionsManager object that specifies how this channel is
        #   downloaded (or None, if the parent's options.OptionsManager object
        #   should be used instead)
        self.options_obj = options_obj


        # IV list - other
        # ---------------
        # Unique media data object ID (an integer)
        self.dbid = dbid

        # Folder name
        self.name = name
        # Folder nickname (displayed in the Video Index; the same as .name,
        #   unless the user changes it). Note that the nickname of a fixed
        #   folder can't be changed
        self.nickname = name

        # The value of mainapp.TartubeApp.catalogue_sort_mode, the last time
        #   self.sort_children() was called. (When the user changes the sort
        #   mode, we don't sort self.child_list() until we actually need to
        #   display it)
        self.last_sort_mode = 'default'

        # External download destination - a directory at a fixed position in
        #   the filesystem, outside Tartube's data directory. Use is not
        #   recommended because of potential file read/write problems, but is
        #   available to users who need it
        # If specified, the full path to the external directory
        # NB Fixed folders cannot have an external directory
        self.external_dir = None
        # Alternative download destination - the dbid of a channel, playlist or
        #   folder in whose directory videos, thumbnails (etc) are downloaded.
        #   By default, set to the dbid of this folder; but can be set to the
        #   dbid of any other channel/playlist/folder
        # Used for: (1) adding a channel and its playlists to the Tartube
        #   database, so that duplicate videos don't exist on the user's
        #   filesystem, (2) tying together, for example, a YouTube and a
        #   BitChute account, so that duplicate videos don't exist on the
        #   user's filesystem
        # NB A media data object can't have an alternative download destination
        #   and itself be the alternative download destination for another
        #   media data object; it must be one or the other (or neither)
        # NB Fixed folders cannot have an alternative download destination
        # NB Ignored if self.external_dir is specified
        self.master_dbid = dbid
        # A list of dbids for any channel, playlist or folder that uses this
        #   folder as its alternative destination
        self.slave_dbid_list = []

        # Contents restriction mode: 'full' if this folder can contain
        #   videos, but not channels/playlists/folders, 'partial' if this
        #   folder can contain videos and folders, but not channels and
        #   playlists, 'open' if this folder can contain any combination of
        #   videos, channels, playlists and folders
        self.restrict_mode = restrict_mode
        # Flag set to False if the folder can be deleted by the user, or True
        #   if it can't be deleted by the user
        self.fixed_flag = fixed_flag
        # Flag set to True to mark this as a private folder, meaning that the
        #   user can't add anything to it (because Tartube uses it for special
        #   purposes)
        self.priv_flag = priv_flag
        # Flag set to True for any folder whose contents should be deleted when
        #   Tartube shuts down (but the folder itself remains)
        self.temp_flag = temp_flag

        # The flags in this group are mutually exclusive; only one flag (or
        #   none of them) should be True
        # Flag set to True if videos in this folder should be downloaded, but
        #   not added to the database. (If True, the folder and its videos
        #   are never checked)
        self.dl_no_db_flag = False
        # Flag set to True if this folder should never be checked or
        #   downloaded. If True, the setting applies to any descendant
        #   channels, playlists and folders
        self.dl_disable_flag = False
        # Flag set to True if Tartube should always simulate the download of
        #   videos in this folder, or False if the downloads.DownloadManager
        #   object should decide whether to simulate, or not
        self.dl_sim_flag = False

        # Flag set to True if this folder is hidden (not visible in the Video
        #   Index). Note that only folders can be hidden; channels and
        #   playlists cannot
        self.hidden_flag = False
        # Flag set to True if this folder is marked as favourite, meaning that
        #   any descendant video objects are automatically marked as favourites
        #   (but not descendant channels, playlists or folders)
        # (Descendant video objects will also be marked as favourite if one of
        #   this folder's ancestors are marked as favourite)
        self.fav_flag = False

        # The total number of child video objects
        self.vid_count = 0
        # The number of child video objects that are marked as bookmarked,
        #   downloaded, favourite, livestreams, missing, new and in the
        #   'Waiting Videos' system folders
        self.bookmark_count = 0
        self.dl_count = 0
        self.fav_count = 0
        self.live_count = 0
        self.missing_count = 0
        self.new_count = 0
        self.waiting_count = 0


        # Code
        # ----

        # Update the parent (if any)
        if self.parent_obj:
            self.parent_obj.add_child(app_obj, self)


    # Public class methods


    def add_child(self, app_obj, child_obj, no_sort_flag=False):

        """Can be called by anything.

        Adds a child media data object, which can be any type of media data
        object (including another media.Folder object).

        Args:

            app_obj (mainapp.TartubeApp): The main application

            child_obj (media.Video, media.Channel, media.Playlist,
                media.Folder): The child object

            no_sort_flag (bool): If True, the child list is not sorted after
                the new object has been added

        """

        # Check this is not already a child object
        if not child_obj in self.child_list:

            self.child_list.append(child_obj)
            if not no_sort_flag:
                self.sort_children(app_obj)

            if isinstance(child_obj, Video):
                self.vid_count += 1


    def check_duplicate_video(self, source):

        """Called by mainapp.TartubeApp.on_menu_add_video() and
        mainwin.MainWin.on_window_drag_data_received().

        When the user adds new videos using the 'Add Videos' dialogue window,
        the calling function calls this function to check that the folder
        doesn't contain a duplicate video (i.e., one whose source URL is the
        same).

        Args:

            source (str): The video URL to check

        Returns:

            True if any of the child media.Video objects in this folder have
                the same source URL; False otherwise

        """

        for child_obj in self.child_list:

            if isinstance(child_obj, Video) \
            and child_obj.source is not None \
            and child_obj.source == source:
                # Duplicate found
                return True

        # No duplicate found
        return False


    def check_duplicate_video_by_path(self, app_obj, path):

        """Called by mainwin.MainWin.on_window_drag_data_received().

        A modified version of self.check_duplicate_video(), which checks for
        media.Video objects with duplicate paths, instead of dupliate URLs.

        Args:

            app_obj (mainapp.TartubeApp): The main application

            path (str): The full file path to check

        Returns:

            True if any of the child media.Video objects in this folder have
                the same source URL; False otherwise

        """

        for child_obj in self.child_list:

            if isinstance(child_obj, Video) \
            and child_obj.file_name is not None:

                child_path = child_obj.get_actual_path(app_obj)
                if child_path is not None and child_path == path:

                    # Duplicate found
                    return True

        # No duplicate found
        return False


#   def del_child():                # Inherited from GenericContainer


    def sort_children(self, app_obj):

        """Can be called by anything. For example, called by self.add_child().

        Sorts the child media.Video, media.Channel, media.Playlist and
        media.Folder objects.
        """

        self.last_sort_mode = app_obj.catalogue_sort_mode

        # Sort a copy of the list to prevent 'list modified during sort'
        #   errors
        while True:

            copy_list = self.child_list.copy()
            copy_list.sort(
                key=functools.cmp_to_key(app_obj.folder_child_compare),
            )

            if len(copy_list) == len(self.child_list):
                self.child_list = copy_list.copy()
                break


    # Set accessors


#   def reset_counts():             # Inherited from GenericContainer


#   def set_dl_sim_flag():          # Inherited from GenericMedia


    def set_hidden_flag(self, flag):

        if flag:
            self.hidden_flag = True
        else:
            self.hidden_flag = False


#   def set_options_obj():          # Inherited from GenericMedia


    # Get accessors


#   def get_actual_dir():           # Inherited from GenericContainer


#   def get_default_dir():          # Inherited from GenericContainer


#   def get_relative_actual_dir():  # Inherited from GenericContainer


#   def get_relative_default_dir(): # Inherited from GenericContainer


    def never_called_func(self):

        """Function that is never called, but which makes this class object
        collapse neatly in my IDE."""

        pass


class Scheduled(object):

    """Python class that handles a scheduled download operation.

    Args:

        name (str): Unique name for the scheduled download (a string, minimum 1
            character)

        dl_mode (str): Download operation type: 'sim' (for simulated
            downloads), 'real' (for real downloads) or 'custom_real' (for
            custom downloads; the value is checked before being used, and
            converted to 'custom_sim' where necessary)

        start_mode (str): 'none' to disable this schedule, 'start' to perform
            the operation whenever Tartube starts, or 'scheduled' to perform
            the operation at regular intervals

    """


    # Standard class methods


    def __init__(self, name, dl_mode, start_mode):

        # IV list - other
        # ---------------
        # Unique name for the scheduled download (a string, minimum 1
        #   character)
        self.name = name

        # Download operation type: 'sim' (for simulated downloads), 'real' (for
        #   real downloads) or 'custom_real' (for all custom downloads; the
        #   value is checked before being used, and converted to 'custom_sim'
        #   where necessary)
        self.dl_mode = dl_mode
        # The .uid of the custom download programme to use (a key in
        #   mainapp.TartubeApp.custom_dl_reg_dict). If None or an unrecognised
        #   value, a 'real' download takes place
        # Ignored if self.dl_mode is not 'custom_real'
        self.custom_dl_uid = None
        # Start mode - 'none' to disable this schedule, 'start' to perform the
        #   operation whenever Tartube starts, or 'scheduled' to perform the
        #   operation at regular intervals
        self.start_mode = start_mode

        # The time between scheduled downloads, when self.start_mode is
        #   'scheduled' (minimum value 1, ignored for other values of
        #   self.start_mode)
        self.wait_value = 2
        # ...using this unit (any of the values in formats.TIME_METRIC_LIST;
        #   the 'seconds' value is not available in the edit window's combobox)
        self.wait_unit = 'hours'

        # The time (system time, in seconds) at which this scheduled download
        #   last started (regardless of whether it was scheduled to begin at
        #   that time, or not)
        self.last_time = 0
        # When self.start_mode is 'start', mainapp.TartubeApp.start sets this
        #   value to the time at which the scheduled download should start
        #   (which will be a few seconds after startup)
        # Once the scheduled download is started, the value is set back to 0
        self.only_time = 0

        # When multiple scheduled downloads are due to start at the same time,
        #   a flag that marks this as an exclusive scheduled download
        # Scheduled downloads are checked in the order specified by
        #   mainapp.TartubeApp.scheduled_list. If this is flag is True for any
        #   of them, only one of the flagged downloads starts
        self.exclusive_flag = False
        # When this scheduled download is due to start, what to do if another
        #   download operation is in progress: 'join' to add media data objects
        #   to the current download operation (at the end of the existing
        #   list), 'priority' to add media data objects to the current download
        #   operation (at the beginning of the existing list), 'skip' to wait
        #   until the next scheduled operation time instead
        # Note that this affects a download operation already in progress,
        #   not one which is about to start (because multiple scheduled
        #   downloads are due to start at the same time)
        self.join_mode = 'skip'

        # Flag set to True if Tartube should shut down after this scheduled
        #   download operation occurs, False if not
        self.shutdown_flag = False
        # Flag set to True if the whole channel/playlist/folder should be
        #   checked/downloaded, regardless of the value of
        #   mainapp.TartubeApp.operation_limit_flag, etc
        self.ignore_limits_flag = False

        # Maximum simultaneous downloads. If the flag is True, the specified
        #   value overrides the equivalent mainapp.TartubeApp IV

        # Maximum download bandwidth. If the flag is True, the specified
        #   value overrides the equivalent mainapp.TartubeApp IV
        self.scheduled_num_worker = 2
        self.scheduled_num_worker_apply_flag = False
        self.scheduled_bandwidth = 500
        self.scheduled_bandwidth_apply_flag = False

        # Flag set to True if the download operation should encompass all
        #   media data objects
        self.all_flag = True
        # List of names of media.Channel, media.Playlist and media.Folder
        #   objects to add to the download operation (not the objects
        #   themselves). All of their children are also added). Ignored if
        #   self.all_flag is True
        self.media_list = []


    # Public class methods


    # Set accessors


    def reset_custom_dl_uid(self):

        self.custom_dl_uid = None
        if self.dl_mode == 'custom_real':
            self.dl_mode = 'real'


    def set_last_time(self, time):

        self.last_time = time


    def add_media(self, name):

        self.media_list.append(name)
        self.all_flag = False


    def set_only_time(self, time):

        self.only_time = time
