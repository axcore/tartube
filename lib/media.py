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
from . import mainapp
from . import utils


# Classes


class GenericMedia(object):

    """Base python class inherited by media.Video, media.Channel,
    media.Playlist and media.Folder."""


    # Set accessors


    def set_dl_sim_flag(self, flag):

        if flag:
            self.dl_sim_flag = True
        else:
            self.dl_sim_flag = False


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


    def set_options_obj(self, options_obj):

        self.options_obj = options_obj


    def set_warning(self, msg):

        # The media.Folder object has no error/warning IVs (and shouldn't
        #   receive any error/warning messages)
        if not isinstance(self, Folder):
            self.warning_list.append(msg)


class GenericContainer(GenericMedia):

    """Base python class inherited by media.Channel, media.Playlist and
    media.Folder."""


    # Public class methods


    def compile_all_videos(self, video_list):

        """Can be called by anything. Currently called by
        mainapp.TartubeApp.mark_container_favourite(), and callbacks in
        mainwin.MainWin.on_video_index_mark_new() and
        .on_video_index_mark_not_new().

        Subsquently called by this function recursively.

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


    def count_descendants(self, count_list):

        """Can be called by anything. Currently called by
        mainwin.DeleteContainerDialogue.__init__(), and then again by this
        function recursively.

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
        index = self.find_child_index(child_obj)
        if index is None:
            return False

        else:
            del self.child_list[index]
            if isinstance(child_obj, Video):
                self.vid_count -= 1

                if child_obj.new_flag:
                    self.new_count -= 1

                if child_obj.fav_flag:
                    self.fav_count -= 1

                if child_obj.dl_flag:
                    self.dl_count -= 1

            return True


    def find_child_index(self, child_obj):

        """Can be called by anything.

        Finds the position in self.child_list of a specified child object, or
        returns None if the specified child object is not in self.child_list.

        Args:

            child_obj (media.Video, media.Channel, media.Playlist,
                media.Folder): The child object to find


        Returns:

            An integer describing the position in self.child_list, or None of
                the child object is not found in self.child_list

        """

        try:
            return self.child_list.index(child_obj)
        except:
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

            True or False.

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


    # Set accessors


    def inc_dl_count(self):

        self.dl_count += 1


    def dec_dl_count(self):

        self.dl_count -= 1


    def inc_fav_count(self):

        self.fav_count += 1


    def dec_fav_count(self):

        self.fav_count -= 1


    def inc_new_count(self):

        self.new_count += 1


    def dec_new_count(self):

        self.new_count -= 1


    def set_parent_obj(self, parent_obj):

        self.parent_obj = parent_obj


    # Get accessors


    def get_dir(self, app_obj):

        """Called by self.__init___(), or any other code.

        Fetches the full path to the sub-directory used by this channel,
        playlist or folder.

        Args:

            app_obj (mainapp.TartubeApp): The main application

        Returns:

            The full path to the directory

        """

        dir_list = [self.name]
        obj = self
        while obj.parent_obj:

            obj = obj.parent_obj
            dir_list.insert(0, obj.name)

        return os.path.abspath(os.path.join(app_obj.downloads_dir, *dir_list))


class GenericRemoteContainer(GenericContainer):

    """Base python class inherited by media.Channel and media.Playlist."""


    # Public class methods


    def add_child(self, child_obj, no_sort_flag=False):

        """Called by media.Video.__init__().

        Adds a child media data object, which must be a media.Video object.

        Args:

            child_obj (media.Video): The child object

            no_sort_flag (True or False): True when the calling code wants to
                delay sorting the parent container object, for some reason;
                False if not

        """

        # Only media.Video objects can be added to a channel or playlist as a
        #   child object. Also, check this is not already a child object
        if isinstance(child_obj, Video) or child_obj in self.child_list:

            self.child_list.append(child_obj)
            if not no_sort_flag:
                self.sort_children()

            if isinstance(child_obj, Video):
                self.vid_count += 1


    def do_sort(self, obj1, obj2):

        """Sorting function used by functools.cmp_to_key(), and called by
        self.sort_children().

        Sort videos by upload time, with the most recent video first.

        When downloading a channel or playlist, we assume that YouTube (etc)
        supplies us with the most recent upload first. Therefore, when the
        upload time is the same, sort by the order in youtube-dl fetches the
        videos.

        Args:

            obj1, obj2 (media.Video) - Video objects being sorted

        Returns:

            -1 if obj1 comes first, 1 if obj2 comes first, 0 if they are equal

        """

        # The video's index is not relevant unless sorting a playlist
        if isinstance(self, Playlist) \
        and obj1.index is not None and obj2.index is not None:
            if obj1.index < obj2.index:
                return -1
            else:
                return 1
        elif obj1.upload_time is not None and obj2.upload_time is not None:
            if obj1.upload_time > obj2.upload_time:
                return -1
            elif obj1.upload_time < obj2.upload_time:
                return 1
            else:
                if obj1.receive_time < obj2.receive_time:
                    return -1
                elif obj1.receive_time > obj2.receive_time:
                    return 1
                else:
                    return 0
        else:
            return 0


    def find_matching_video(self, app_obj, name):

        """Can be called by anything.

        Checks all of this object's child objects, looking for a media.Video
        object with a matching name.

        Args:

            app_obj (mainapp.TartubeApp): The main application

            name (string): The name of the media.Video object to find

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


    def sort_children(self):

        """Can be called by anything. For example, called by self.add_child().

        Sorts the child media.Video objects by upload time.
        """

        self.child_list.sort(key=functools.cmp_to_key(self.do_sort))


    # Set accessors


    def set_source(self, source):

        self.source = source


class Video(GenericMedia):

    """Python class that handles an individual video.

    Args:

        dbid (int): A unique ID for this media data object

        name (string): The video name

        parent_obj (media.Channel, media.Playlist, media.Folder): The parent
            media data object, if any

        options_obj (options.OptionsManager): The object specifying download
            options for this video, if any

        no_sort_flag (True or False): True when the calling code wants to
            delay sorting the parent container object, for some reason; False
            if not

    """


    # Standard class methods


    def __init__(self, dbid, name, parent_obj, options_obj=None,
    no_sort_flag=False):

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
        self.dbid = dbid

        # Video name
        self.name = name
        # Download source (a URL)
        self.source = None

        # Flag set to True if Tartube should always simulate the download of
        #   video, or False if the downloads.DownloadManager object should
        #   decide whether to simulate, or not
        self.dl_sim_flag = False
        # Flag set to True at the same time self.dl_sim_flag is set to True,
        #   showing that the video has been downloaded and not watched
        self.new_flag = False
        # Flag set to True if the video is marked a favourite. Upon download,
        #   it's marked as a favourite if the same IV in the parent channel,
        #   playlist or folder (also in the parent's parent, and so on) is True
        self.fav_flag = False

        # The file's directory, name and extension
        self.file_dir = None
        self.file_name = None
        self.file_ext = None

        # Flag set to True once the file has been downloaded, and is confirmed
        #   to exist in Tartube's data directory
        self.dl_flag = False
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
        # For videos in a playlist (i.e. a media.Video object whose parent is
        #   a media.Playlist object), the video's index in the playlist. For
        #   all other situations, the value remains as None
        self.index = None

        # Video description. A string of any length, containing newline
        #   characters if necessary. (Set to None if the video description is
        #   not known)
        self.descrip = None
        # Video short description - the first line in self.descrip, limited to
        #   a certain number of characters (specifically,
        #   mainwin.MainWin.long_string_max_len)
        self.short = None

        # List of error/warning messages generated the last time the video was
        #   checked or downloaded. Both set to empty lists if the video has
        #   never been checked or downloaded, or if there was no error/warning
        #   on the last check/download attempt
        # NB If an error/warning message is generated when downloading a
        #   channel or playlist, the message is stored in the media.Channel
        #   or media.Playlist object instead
        self.error_list = []
        self.warning_list = []


        # Code
        # ----

        # Update the parent
        self.parent_obj.add_child(self, no_sort_flag)


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


    def read_video_descrip(self, app_obj, max_length):

        """Can be called by anything.

        Reads the .description file, if it exists, and updates IVs.

        Args:

            app_obj (mainapp.TartubeApp): The main application

            max_length (int): When storing the description in this object's
                IVs, the maximum line length to use

        """

        descrip_path = os.path.abspath(
            os.path.join(
                self.file_dir,
                self.file_name + '.description',
            ),
        )

        text = app_obj.file_manager_obj.load_text(descrip_path)
        if text is not None:
            self.set_video_descrip(text, max_length)


    # Set accessors


    def set_dl_flag(self, flag=False):

        self.dl_flag = flag

        if self.receive_time is None:
            self.receive_time = int(time.time())


#   def set_dl_sim_flag():      # Inherited from GenericMedia


    def set_duration(self, duration=None):

        if duration is not None:
            if duration != int(duration):
                self.duration = int(duration) + 1
            else:
                self.duration = duration

        else:
            self.duration = None


    def set_file(self, path, filename, extension):

        self.file_dir = path
        self.file_name = filename
        self.file_ext = extension


    def reset_file_dir(self, app_obj):

        """Called by mainapp.TartubeApp.move_container_to_top_continue()
        and .move_container_continue().

        After moving a channel, playlist or folder to a new location in the
        media data registry's tree, every media.Video object which has been
        moved along with it must have its .file_dir IV updated.
        """

        self.file_dir = self.parent_obj.get_dir(app_obj)


    def set_file_size(self, size=None):

        self.file_size = size


    def set_index(self, index):

        self.index = int(index)


    def set_mkv(self):

        """Called by mainapp.TartubeApp.update_video_when_file_found().

        When the warning 'Requested formats are incompatible for merge and will
        be merged into mkv' has been seen, the calling function has found an
        .mkv file rather than the .mp4 file it was expecting.

        Update the IV.
        """

        self.file_ext = '.mkv'


    def set_name(self, name):

        """Called by mainwin.MainWin.results_list_update_row() to set the name
        of an unnamed video, replacing the default name (specified by
        mainapp.TartubeApp.default_video_name).

        Also called by media.VideoDownloader.confirm_sim_video().
        """

        self.name = name


    def set_new_flag(self, flag):

        if flag:
            self.new_flag = True
        else:
            self.new_flag = False


#   def set_options_obj():      # Inherited from GenericMedia


    def set_receive_time(self):

        self.receive_time = int(time.time())


    def set_source(self, source):

        self.source = source


    def set_upload_time(self, unix_time=None):

        self.upload_time = int(unix_time)


    def set_video_descrip(self, descrip, max_length):

        """Called by mainapp.TartubeApp.update_video_from_json() and
        downloads.VideoDownloader.confirm_sim_video().

        Converts the video description into a list of lines, max_length
        characters long (longer lines are split into shorter ones).

        Then uses the first line to set the short description, and uses all
        lines to set the full description.

        Args:

            descrip (string): The video description

            max_length (int): A maximum line size

        """

        if descrip:

            self.descrip = utils.tidy_up_long_descrip(descrip, max_length)
            self.short = utils.shorten_string(descrip, max_length)

        else:
            self.descrip = None
            self.short = None


    # Get accessors


    def get_file_size_string(self):

        """Can be called by anything.

        Converts self.file_size, in bytes, into a formatted string.

        Returns:

            The converted string, or None if self.file_size is not set

        """

        if self.file_size:
            return utils.format_bytes(self.file_size)
        else:
            return None


    def get_receive_date_string(self):

        """Can be called by anything.

        A modified version of self.get_receive_time_string(), returning just
        the date, not the date and the time.

        Returns:

            The formatted string, or None if self.receive_time is not set

        """

        if self.receive_time:
            timestamp = datetime.datetime.fromtimestamp(self.receive_time)
            return timestamp.strftime('%Y-%m-%d')
        else:
            return None


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


    def get_upload_date_string(self):

        """Can be called by anything.

        A modified version of self.get_upload_time_string(), returning just the
        date, not the date and the time.

        Returns:

            The formatted string, or None if self.upload_time is not set

        """

        if self.upload_time:
            timestamp = datetime.datetime.fromtimestamp(self.upload_time)
            return timestamp.strftime('%Y-%m-%d')
        else:
            return None


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

        name (string) - The channel name

        parent_obj (media.Folder) - The parent media data object, if any

        options_obj (options.OptionsManager) - The object specifying download
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
        # Download source (a URL)
        self.source = None

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
        # The number of child video objects that are marked as new,
        #   favourite, and downloaded
        self.new_count = 0
        self.fav_count = 0
        self.dl_count = 0

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
            self.parent_obj.add_child(self)


    # Public class methods


#   def add_child():            # Inherited from GenericRemoteContainer


#   def del_child():            # Inherited from GenericContainer


#   def do_sort():              # Inherited from GenericRemoteContainer


#   def find_child_index():     # Inherited from GenericContainer


#   def sort_children():        # Inherited from GenericRemoteContainer


    # Set accessors


#   def set_dl_sim_flag():      # Inherited from GenericMedia


#   def set_options_obj():      # Inherited from GenericMedia


#   def set_source():           # Inherited from GenericRemoteContainer


    # Get accessors


#   def get_dir():              # Inherited from GenericContainer


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

        name (string) - The playlist name

        parent_obj (media.Folder) - The parent media data object, if any

        options_obj (options.OptionsManager) - The object specifying download
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
        # Download source (a URL)
        self.source = None

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
        # The number of child video objects that are marked as new,
        #   favourite, and downloaded
        self.new_count = 0
        self.fav_count = 0
        self.dl_count = 0

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
            self.parent_obj.add_child(self)


    # Public class methods


#   def add_child():            # Inherited from GenericRemoteContainer


#   def del_child():            # Inherited from GenericContainer


#   def do_sort():              # Inherited from GenericRemoteContainer


#   def find_child_index():     # Inherited from GenericContainer


#   def sort_children():        # Inherited from GenericRemoteContainer


    # Set accessors


#   def set_dl_sim_flag():      # Inherited from GenericMedia


#   def set_options_obj():      # Inherited from GenericMedia


#   def set_source():           # Inherited from GenericRemoteContainer


    # Get accessors


#   def get_dir():              # Inherited from GenericContainer


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

        name (string) - The folder name

        parent_obj (media.Folder) - The parent media data object, if any

        options_obj (options.OptionsManager) - The object specifying download
            options for this channel, if any

        fixed_flag (True, False) - If True, this folder can't be deleted by the
            user

        priv_flag (True, False) - If True, the user can't add anything to this
            folder, because Tartube uses it for special purposes

        restrict_flag (True, False) - If True, this folder cannot contain
            channels, playlists and other folders (can only contain videos)

        temp_flag (True, False) - If True, the folder's contents should be
            deleted when Tartube shuts down (but the folder itself remains)

    """


    # Standard class methods


    def __init__(self, app_obj, dbid, name, parent_obj=None, \
    options_obj=None, fixed_flag=False, priv_flag=False, restrict_flag=False, \
    temp_flag=False):

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

        # Flag set to False if the folder can be deleted by the user, or True
        #   if it can't be deleted by the user
        self.fixed_flag = fixed_flag
        # Flag set to True to mark this as a private folder, meaning that the
        #   user can't add anything to it (because Tartube uses it for special
        #   purposes)
        self.priv_flag = priv_flag
        # Flag set to False if other channels, playlists and folders can be
        #   added as children of this folder, or True if only videos can be
        #   added as children of this folder
        self.restrict_flag = restrict_flag
        # Flag set to True for any folder whose contents should be deleted when
        #   Tartube shuts down (but the folder itself remains)
        self.temp_flag = temp_flag

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
        # The number of child video objects that are marked as new,
        #   favourite, and downloaded
        self.new_count = 0
        self.fav_count = 0
        self.dl_count = 0


        # Code
        # ----

        # Update the parent (if any)
        if self.parent_obj:
            self.parent_obj.add_child(self)


    # Public class methods


    def add_child(self, child_obj, no_sort_flag=False):

        """Called by media.Video.__init__(), media.Channel.__init__(),
        media.Playlist.__init__() or another instance of
        media.Folder.__init__().

        Also called to add videos to fixed folders like 'All Videos'.

        Adds a child media data object, which can be any type of media data
        object (including another media.Folder object).

        Args:

            child_obj (media.Video, media.Channel, media.Playlist,
                media.Folder): The child object

        """

        # Check this is not already a child object
        if not child_obj in self.child_list:

            self.child_list.append(child_obj)
            if not no_sort_flag:
                self.sort_children()

            if isinstance(child_obj, Video):
                self.vid_count += 1


    def check_duplicate_video(self, source):

        """Called by mainapp.TartubeApp.on_menu_add_video().

        When the user adds new videos using the 'Add Videos' dialogue window,
        the calling function calls this function to check that the folder
        doesn't contain a duplicate video (i.e., one whose source URL is the
        same).

        Args:

            source (string): The video URL to check

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


#   def del_child():            # Inherited from GenericContainer


    def do_sort(self, obj1, obj2):

        """Sorting function used by functools.cmp_to_key(), and called by
        self.sort_children().

        Sorts the child media.Video, media.Channel, media.Playlist and
        media.Folder objects.

        Firstly, sort by class - folders, channels/playlists, then videos.

        Within folders, channels and playlists, sort alphabetically. Within
        videos, sort by upload time.

        Args:

            obj1, obj2 (media.Video, media.Channel, media.Playlist or
                media.Folder) - Media data objects being sorted

        Returns:

            -1 if obj1 comes first, 1 if obj2 comes first, 0 if they are equal

        """

        if str(obj1.__class__) == str(obj2.__class__) \
        or (
            isinstance(obj1, GenericRemoteContainer) \
            and isinstance(obj2, GenericRemoteContainer)
        ):
            if isinstance(obj1, Video):

                if obj1.upload_time is not None \
                and obj2.upload_time is not None:
                    if obj1.upload_time > obj2.upload_time:
                        return -1
                    elif obj1.upload_time < obj2.upload_time:
                        return 1
                    else:
                        # In private folders (e.g. 'All Videos'), the most
                        #   recently received video goes to the top of the list
                        if self.priv_flag:
                            if obj1.receive_time > obj2.receive_time:
                                return -1
                            elif obj1.receive_time < obj2.receive_time:
                                return 1
                            else:
                                return 0
                        # ...but for everything else, the sorting algorithm is
                        #   the same as for GenericRemoteContainer.do_sort(),
                        #   in which we assume the website is sending us
                        #   videos, newest first
                        else:
                            if obj1.receive_time < obj2.receive_time:
                                return -1
                            elif obj1.receive_time > obj2.receive_time:
                                return 1
                            else:
                                return 0
                else:
                    return 0
            else:
                if obj1.name.lower() < obj2.name.lower():
                    return -1
                elif obj1.name.lower() > obj2.name.lower():
                    return 1
                else:
                    return 0
        else:
            if isinstance(obj1, Folder):
                return -1
            elif isinstance(obj2, Folder):
                return 1
            elif isinstance(obj1, Channel) or isinstance(obj1, Playlist):
                return -1
            elif isinstance(obj2, Channel) or isinstance(obj2, Playlist):
                return 1
            else:
                return 0


#   def find_child_index():     # Inherited from GenericContainer


    def sort_children(self):

        """Can be called by anything. For example, called by self.add_child().

        Sorts the child media.Video, media.Channel, media.Playlist and
        media.Folder objects.
        """

        self.child_list.sort(key=functools.cmp_to_key(self.do_sort))


    # Set accessors


    def reset_counts(self, vid_count, new_count, fav_count, dl_count):

        """Called by mainapp.TartubeApp.update_db().

        When a database created by an earlier version of Tartube is loaded,
        the calling function updates IVs as required.

        This function is called if this object's video counts need to be
        changed.
        """

        self.vid_count = vid_count
        self.new_count = new_count
        self.fav_count = fav_count
        self.dl_count = dl_count


#   def set_dl_sim_flag():      # Inherited from GenericMedia


    def set_hidden_flag(self, flag):

        if flag:
            self.hidden_flag = True
        else:
            self.hidden_flag = False


#   def set_options_obj():      # Inherited from GenericMedia


    # Get accessors


#   def get_dir():              # Inherited from GenericContainer


    def never_called_func(self):

        """Function that is never called, but which makes this class object
        collapse neatly in my IDE."""

        pass
