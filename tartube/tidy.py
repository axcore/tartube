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


"""Tidy operation classes."""


# Import Gtk modules
import gi
from gi.repository import GObject


# Import other modules
try:
    import moviepy.editor
except:
    pass

import os
import re
import shutil
import threading
import time


# Import our modules
import formats
import media
import utils
# Use same gettext translations
from mainapp import _


# Classes


class TidyManager(threading.Thread):

    """Called by mainapp.TartubeApp.tidy_manager_start().

    Python class to manage the tidy operation, in which videos can be checked
    for corruption and actually existing (or not), and various file types can
    be deleted collectively.

    Args:

        app_obj (mainapp.TartubeApp): The main application

        choices_dict (dict): A dictionary specifying the choices made by the
            user in mainwin.TidyDialogue. The dictionary is in the following
            format:

            media_data_obj: A media.Channel, media.Playlist or media.Folder
                object, or None if all channels/playlists/folders are to be
                tidied up. If specified, the cahnnel/playlist/folder and all of
                its descendants are checked

            corrupt_flag: True if video files should be checked for corruption

            del_corrupt_flag: True if corrupted video files should be deleted

            exist_Flag: True if video files that should exist should be
                checked, in case they don't (and vice-versa)

            del_video_flag: True if downloaded video files should be deleted

            del_others_flag: True if all video/audio files with the same name
                should be deleted (as artefacts of post-processing with FFmpeg
                or AVConv)

            del_archive_flag: True if all youtube-dl archive files should be
                deleted

            move_thumb_flag: True if all thumbnail files should be moved into a
                subdirectory

            del_thumb_flag: True if all thumbnail files should be deleted

            convert_webp_flag: True if all .webp thumbnail files should be
                converted to .jpg

            move_data_flag: True if description, metadata (JSON) and annotation
                files should be moved into a subdirectory

            del_descrip_flag: True if all description files should be deleted

            del_json_flag: True if all metadata (JSON) files should be deleted

            del_xml_flag: True if all annotation files should be deleted

    """


    # Standard class methods


    def __init__(self, app_obj, choices_dict):

        super(TidyManager, self).__init__()

        # IV list - class objects
        # -----------------------
        # The mainapp.TartubeApp object
        self.app_obj = app_obj
        # The media data object (channel, playlist or folder) to be tidied up,
        #   or None if the whole data directory is to be tidied up
        # If specified, the channel/playlist/folder and all of its descendants
        #   are checked
        self.init_obj = choices_dict['media_data_obj']


        # IV list - other
        # ---------------
        # Flag set to False if self.stop_tidy_operation() is called, which
        #   halts the operation immediately
        self.running_flag = True

        # The time at which the tidy operation began (in seconds since epoch)
        self.start_time = int(time.time())
        # The time at which the tidy operation completed (in seconds since
        #   epoch)
        self.stop_time = None
        # The time (in seconds) between iterations of the loop in self.run()
        self.sleep_time = 0.25

        # Flags specifying which actions should be applied
        # True if video files should be checked for corruption
        self.corrupt_flag = choices_dict['corrupt_flag']
        # True if corrupted video files should be deleted
        self.del_corrupt_flag = choices_dict['del_corrupt_flag']
        # True if video files that should exist should be checked, in case they
        #   don't (and vice-versa)
        self.exist_flag = choices_dict['exist_flag']
        # True if downloaded video files should be deleted
        self.del_video_flag = choices_dict['del_video_flag']
        # True if all video/audio files with the same name should be deleted
        #   (as artefacts of post-processing with FFmpeg or AVConv)
        self.del_others_flag = choices_dict['del_others_flag']
        # True if all youtube-dl archive files should be deleted
        self.del_archive_flag = choices_dict['del_archive_flag']
        # True if all thumbnail files should be moved into a subdirectory
        self.move_thumb_flag = choices_dict['move_thumb_flag']
        # True if all thumbnail files should be deleted
        self.del_thumb_flag = choices_dict['del_thumb_flag']
        # True if all .webp thumbnail files should be converted to .jpg.
        #   Requires mainapp.TartubeApp.ffmpeg_fail_flag set to False
        self.convert_webp_flag = choices_dict['convert_webp_flag']
        # True if description, metadata (JSON) and annotation files should be
        #   moved into a subdirectory
        self.move_data_flag = choices_dict['move_data_flag']
        # True if all description files should be deleted
        self.del_descrip_flag = choices_dict['del_descrip_flag']
        # True if all metadata (JSON) files should be deleted
        self.del_json_flag = choices_dict['del_json_flag']
        # True if all annotation files should be deleted
        self.del_xml_flag = choices_dict['del_xml_flag']

        # The number of media data objects whose directories have been tidied
        #   so far...
        self.job_count = 0
        # ...and the total number to tidy (these numbers are displayed in the
        #   progress bar in the Videos tab)
        self.job_total = 0

        # Individual counts, updated as we go
        self.video_corrupt_count = 0
        self.video_corrupt_deleted_count = 0
        self.video_exist_count = 0
        self.video_no_exist_count = 0
        self.video_deleted_count = 0
        self.other_deleted_count = 0
        self.archive_deleted_count = 0
        self.thumb_moved_count = 0
        self.thumb_deleted_count = 0
        self.webp_converted_count = 0
        self.data_moved_count = 0
        self.descrip_deleted_count = 0
        self.json_deleted_count = 0
        self.xml_deleted_count = 0


        # Code
        # ----

        # Do not convert .webp thumbnails, if not allowed
        if self.app_obj.ffmpeg_fail_flag:
            self.convert_webp_flag = False

        # Let's get this party started!
        self.start()


    # Public class methods


    def run(self):

        """Called as a result of self.__init__().

        Compiles a list of media data objects (channels, playlists and folders)
        to tidy up. If self.init_obj is not set, only that channel/playlist/
        folder (and its child channels/playlists/folders) are tidied up;
        otherwise the whole data directory is tidied up.

        Then calls self.tidy_directory() for each item in the list.

        Finally informs the main application that the tidy operation is
        complete.
        """

        # Show information about the tidy operation in the Output Tab
        if not self.init_obj:
            self.app_obj.main_win_obj.output_tab_write_stdout(
                1,
                _('Starting tidy operation, tidying up whole data directory'),
            )

        else:

            media_type = self.init_obj.get_type()

            self.app_obj.main_win_obj.output_tab_write_stdout(
                1,
                _('Starting tidy operation, tidying up \'{0}\'').format(
                    self.init_obj.name,
                )
            )

        if self.corrupt_flag:
            text = _('YES')
        else:
            text = _('NO')

        self.app_obj.main_win_obj.output_tab_write_stdout(
            1,
            '   ' + _('Check videos are not corrupted:') + ' ' + text,
        )

        if self.corrupt_flag:

            if self.del_corrupt_flag:
                text = _('YES')
            else:
                text = _('NO')

            self.app_obj.main_win_obj.output_tab_write_stdout(
                1,
                '   ' + _('Delete corrupted videos:') + ' ' + text,
            )

        if self.exist_flag:
            text = _('YES')
        else:
            text = _('NO')

        self.app_obj.main_win_obj.output_tab_write_stdout(
            1,
            '   ' + _('Check videos do/don\'t exist:') + ' ' + text,
        )

        if self.del_video_flag:
            text = _('YES')
        else:
            text = _('NO')

        self.app_obj.main_win_obj.output_tab_write_stdout(
            1,
            '   ' + _('Delete all video files:') + ' ' + text,
        )

        if self.del_video_flag:

            if self.del_others_flag:
                text = _('YES')
            else:
                text = _('NO')

            self.app_obj.main_win_obj.output_tab_write_stdout(
                1,
                '   ' + _('Delete other video/audio files:') + ' ' + text,
            )

        if self.del_archive_flag:
            text = _('YES')
        else:
            text = _('NO')

        self.app_obj.main_win_obj.output_tab_write_stdout(
            1,
            '   ' + _('Delete downloader archive files:') + ' ' + text,
        )

        if self.move_thumb_flag:
            text = _('YES')
        else:
            text = _('NO')

        self.app_obj.main_win_obj.output_tab_write_stdout(
            1,
            '   ' + _('Move thumbnails into own folder:') + ' ' + text,
        )

        if self.del_thumb_flag:
            text = _('YES')
        else:
            text = _('NO')

        self.app_obj.main_win_obj.output_tab_write_stdout(
            1,
            '   ' + _('Delete all thumbnail files:') + ' ' + text,
        )

        if self.convert_webp_flag:
            text = _('YES')
        else:
            text = _('NO')

        self.app_obj.main_win_obj.output_tab_write_stdout(
            1,
            '   ' + _('Convert .webp thumbnails to .jpg:') + ' ' + text,
        )

        if self.move_data_flag:
            text = _('YES')
        else:
            text = _('NO')

        self.app_obj.main_win_obj.output_tab_write_stdout(
            1,
            '   ' + _('Move other metadata files into own folder:') \
            + ' ' + text,
        )

        if self.del_descrip_flag:
            text = _('YES')
        else:
            text = _('NO')

        self.app_obj.main_win_obj.output_tab_write_stdout(
            1,
            '   ' + _('Delete all description files:') + ' ' + text,
        )

        if self.del_json_flag:
            text = _('YES')
        else:
            text = _('NO')

        self.app_obj.main_win_obj.output_tab_write_stdout(
            1,
            '   ' + _('Delete all metadata (JSON) files:') + ' ' + text,
        )

        if self.del_xml_flag:
            text = _('YES')
        else:
            text = _('NO')

        self.app_obj.main_win_obj.output_tab_write_stdout(
            1,
            '   ' + _('Delete all annotation files:') + ' ' + text,
        )

        # Compile a list of channels, playlists and folders to tidy up (each
        #   one has their own sub-directory inside Tartube's data directory)
        obj_list = []
        if self.init_obj:
            # Add this channel/playlist/folder, and any child channels/
            #   playlists/folders (but not videos, obviously)
            obj_list = self.init_obj.compile_all_containers(obj_list)
        else:
            # Add all channels/playlists/folders in the database
            for dbid in list(self.app_obj.media_name_dict.values()):

                obj = self.app_obj.media_reg_dict[dbid]
                # Don't add private folders
                if not isinstance(obj, media.Folder) or not obj.priv_flag:
                    obj_list.append(obj)

        self.job_total = len(obj_list)

        # Check each sub-directory in turn, updating the media data registry
        #   as we go
        while self.running_flag and obj_list:
            self.tidy_directory(obj_list.pop(0))

            # Pause a moment, before the next iteration of the loop (don't want
            #   to hog resources)
            time.sleep(self.sleep_time)

        # Operation complete. Set the stop time
        self.stop_time = int(time.time())

        # Show a confirmation in the Output Tab
        self.app_obj.main_win_obj.output_tab_write_stdout(
            1,
            _('Tidy operation finished'),
        )

        if self.corrupt_flag:

            self.app_obj.main_win_obj.output_tab_write_stdout(
                1,
                '   ' + _('Corrupted videos found:') + ' ' \
                + str(self.video_corrupt_count),
            )

            self.app_obj.main_win_obj.output_tab_write_stdout(
                1,
                '   ' + _('Corrupted videos deleted:') + ' ' \
                + str(self.video_corrupt_deleted_count),
            )

        if self.exist_flag:

            self.app_obj.main_win_obj.output_tab_write_stdout(
                1,
                '   ' + _('New video files detected:') + ' ' \
                + str(self.video_exist_count),
            )

            self.app_obj.main_win_obj.output_tab_write_stdout(
                1,
                '   ' + _('Missing video files detected:') + ' ' \
                + str(self.video_no_exist_count),
            )

        if self.del_video_flag:

            self.app_obj.main_win_obj.output_tab_write_stdout(
                1,
                '   ' + _('Non-corrupted video files deleted:') + ' ' \
                + str(self.video_deleted_count),
            )

            self.app_obj.main_win_obj.output_tab_write_stdout(
                1,
                '   ' + _('Other video/audio files deleted:') + ' ' \
                + str(self.other_deleted_count),
            )

        if self.del_archive_flag:

            self.app_obj.main_win_obj.output_tab_write_stdout(
                1,
                '   ' + _('Downloader archive files deleted:') + ' ' \
                + str(self.archive_deleted_count),
            )

        if self.move_thumb_flag:

            self.app_obj.main_win_obj.output_tab_write_stdout(
                1,
                '   ' + _('Thumbnail files moved:') + ' ' \
                + str(self.thumb_moved_count),
            )

        if self.del_thumb_flag:

            self.app_obj.main_win_obj.output_tab_write_stdout(
                1,
                '   ' + _('Thumbnail files deleted:') + ' ' \
                + str(self.thumb_deleted_count),
            )

        if self.convert_webp_flag:

            self.app_obj.main_win_obj.output_tab_write_stdout(
                1,
                '   ' + _('.webp thumbnails converted to .jpg:') + ' ' \
                + str(self.webp_converted_count),
            )

        if self.move_data_flag:

            self.app_obj.main_win_obj.output_tab_write_stdout(
                1,
                '   ' + _('Other metadata files moved:') + ' ' \
                + str(self.data_moved_count),
            )

        if self.del_descrip_flag:

            self.app_obj.main_win_obj.output_tab_write_stdout(
                1,
                '   ' + _('Description files deleted:') + ' ' \
                + str(self.descrip_deleted_count),
            )

        if self.del_json_flag:

            self.app_obj.main_win_obj.output_tab_write_stdout(
                1,
                '   ' + _('Metadata (JSON) files deleted:') + ' ' \
                + str(self.json_deleted_count),
            )

        if self.del_xml_flag:

            self.app_obj.main_win_obj.output_tab_write_stdout(
                1,
                '   ' + _('Annotation files deleted:') + ' ' \
                + str(self.xml_deleted_count),
            )

        # Let the timer run for a few more seconds to prevent Gtk errors (for
        #   systems with Gtk < 3.24)
        GObject.timeout_add(
            0,
            self.app_obj.tidy_manager_halt_timer,
        )


    def tidy_directory(self, media_data_obj):

        """Called by self.run().

        Tidy up the directory of a single channel, playlist or folder.

        Args:

            media_data_obj (media.Channel, media.Playlist or media.Folder):
                The media data object whose directory must be tidied up

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

        media_type = media_data_obj.get_type()

        self.app_obj.main_win_obj.output_tab_write_stdout(
            1,
            _('Checking:') + ' \'' + media_data_obj.name + '\'',
        )

        if self.corrupt_flag:
            self.check_video_corrupt(media_data_obj)

        if self.exist_flag:
            self.check_videos_exist(media_data_obj)

        if self.del_video_flag:
            self.delete_video(media_data_obj)

        if self.del_archive_flag:
            self.delete_archive(media_data_obj)

        if self.move_thumb_flag:
            self.move_thumb(media_data_obj)

        if self.del_thumb_flag:
            self.delete_thumb(media_data_obj)

        if self.convert_webp_flag:
            self.convert_webp(media_data_obj)

        if self.move_data_flag:
            self.move_data(media_data_obj)

        if self.del_descrip_flag:
            self.delete_descrip(media_data_obj)

        if self.del_json_flag:
            self.delete_json(media_data_obj)

        if self.del_xml_flag:
            self.delete_xml(media_data_obj)


    def check_video_corrupt(self, media_data_obj):

        """Called by self.tidy_directory().

        Checks all child videos of the specified media data object. If the
        video are corrupted, don't delete them (let the user do that manually).

        Args:

            media_data_obj (media.Channel, media.Playlist or media.Folder):
                The media data object whose directory must be tidied up

        """

        for video_obj in media_data_obj.compile_all_videos( [] ):

            if video_obj.file_name is not None \
            and video_obj.dl_flag:

                video_path = video_obj.get_actual_path(self.app_obj)

                if os.path.isfile(video_path):

                    # Code copied from
                    #   mainapp.TartubeApp.update_video_from_filesystem()
                    # When the video file is corrupted, moviepy freezes
                    #   indefinitely
                    # Instead, let's try placing the procedure inside a thread
                    #   (unlike the original function, this one is never called
                    #   if .refresh_moviepy_timeout is 0)
                    this_thread = threading.Thread(
                        target=self.call_moviepy,
                        args=(video_obj, video_path,),
                    )

                    this_thread.daemon = True
                    this_thread.start()
                    this_thread.join(self.app_obj.refresh_moviepy_timeout)
                    if this_thread.is_alive():

                        # moviepy timed out, so assume the video is corrupted
                        self.video_corrupt_count += 1

                        if self.del_corrupt_flag \
                        and os.path.isfile(video_path):

                            # Delete the corrupted file
                            os.remove(video_path)

                            self.video_corrupt_deleted_count += 1

                            self.app_obj.main_win_obj.output_tab_write_stdout(
                                1,
                                '   ' + _(
                                    'Deleted (possibly) corrupted video file:',
                                ) + ' \'' + video_obj.name + '\'',
                            )

                            self.app_obj.mark_video_downloaded(
                                video_obj,
                                False,
                            )

                        else:

                            # Don't delete it
                            self.app_obj.main_win_obj.output_tab_write_stdout(
                                1,
                                '   ' + _(
                                    'Video file might be corrupt:',
                                ) + ' \'' + video_obj.name + '\'',
                            )


    def check_videos_exist(self, media_data_obj):

        """Called by self.tidy_directory().

        Checks all child videos of the specified media data object. If the
        video should exist, but doesn't (or vice-versa), modify the media.Video
        object's IVs accordingly.

        Args:

            media_data_obj (media.Channel, media.Playlist or media.Folder):
                The media data object whose directory must be tidied up

        """

        for video_obj in media_data_obj.compile_all_videos( [] ):

            if video_obj.file_name is not None:

                video_path = video_obj.get_actual_path(self.app_obj)

                if not video_obj.dl_flag \
                and os.path.isfile(video_path):

                    # File exists, but is marked as not downloaded
                    self.app_obj.mark_video_downloaded(
                        video_obj,
                        True,       # Video is downloaded
                        True,       # ...but don't mark it as new
                    )

                    self.video_exist_count += 1

                    self.app_obj.main_win_obj.output_tab_write_stdout(
                        1,
                        '   ' + _(
                            'Video file exists:',
                        ) + ' \'' + video_obj.name + '\'',
                    )

                elif video_obj.dl_flag \
                and not os.path.isfile(video_path):

                    # File doesn't exist, but is marked as downloaded
                    self.app_obj.mark_video_downloaded(
                        video_obj,
                        False,      # Video is not downloaded
                    )

                    self.video_no_exist_count += 1

                    self.app_obj.main_win_obj.output_tab_write_stdout(
                        1,
                        '   ' + _(
                            'Video file doesn\'t exist:',
                        ) + ' \'' + video_obj.name + '\'',
                    )


    def delete_video(self, media_data_obj):

        """Called by self.tidy_directory().

        Checks all child videos of the specified media data object. If the
        video exists, delete it.

        Args:

            media_data_obj (media.Channel, media.Playlist or media.Folder):
                The media data object whose directory must be tidied up

        """

        ext_list = formats.VIDEO_FORMAT_LIST.copy()
        ext_list.extend(formats.AUDIO_FORMAT_LIST)

        for video_obj in media_data_obj.compile_all_videos( [] ):

            video_path = None
            if video_obj.file_name is not None:

                video_path = video_obj.get_actual_path(self.app_obj)

                # If the video's parent container has an alternative download
                #   destination set, we must check the corresponding media
                #   data object. If the latter also has a media.Video object
                #   matching this video, then this function returns None and
                #   nothing is deleted
                video_path = self.check_video_in_actual_dir(
                    media_data_obj,
                    video_obj,
                    video_path,
                )

            if video_path is not None:

                if video_obj.dl_flag \
                and os.path.isfile(video_path):

                    # Delete the downloaded video file
                    os.remove(video_path)

                    # Mark the video as not downloaded
                    self.app_obj.mark_video_downloaded(video_obj, False)

                    self.video_deleted_count += 1

                if self.del_others_flag:

                    # Also delete all video/audio files with the same name
                    # There might be thousands of files in the directory, so
                    #   using os.walk() or something like that might be too
                    #   expensive
                    # Also, post-processing might create various artefacts, all
                    #   of which must be deleted
                    for ext in ext_list:

                        other_path = video_obj.get_actual_path_by_ext(
                            self.app_obj,
                            ext,
                        )

                        if os.path.isfile(other_path):
                            os.remove(other_path)

                            self.other_deleted_count += 1

        # For an encore, delete all post-processing artefacts in the form
        #   VIDEO_NAME.fNNN.ext, where NNN is an integer and .ext is one of
        #   the video extensions specified by formats.VIDEO_FORMAT_LIST
        #   (.mkv, etc)
        # (The previous code won't pick them up, but we can delete them all
        #   now.)
        # (The alternative download destination, if set, is not affected.)
        check_list = []
        search_path = media_data_obj.get_default_dir(self.app_obj)

        for (dir_path, dir_name_list, file_name_list) in os.walk(search_path):
            check_list.extend(file_name_list)

        char = '|'
        regex = '\.f\d+\.(' + char.join(formats.VIDEO_FORMAT_LIST) + ')$'
        for check_path in check_list:
            if re.search(regex, check_path):

                full_path = os.path.abspath(
                    os.path.join(search_path, check_path),
                )

                if os.path.isfile(full_path):

                    os.remove(full_path)
                    self.other_deleted_count += 1


    def delete_archive(self, media_data_obj):

        """Called by self.tidy_directory().

        Checks the specified media data object's directory. If a youtube-dl
        archive file is found there, delete it.

        Args:

            media_data_obj (media.Channel, media.Playlist or media.Folder):
                The media data object whose directory must be tidied up

        """

        archive_path = os.path.abspath(
            os.path.join(
                media_data_obj.get_default_dir(self.app_obj),
                'ytdl-archive.txt',
            ),
        )

        if os.path.isfile(archive_path):

            # Delete the archive file
            os.remove(archive_path)
            self.archive_deleted_count += 1


    def move_thumb(self, media_data_obj):

        """Called by self.tidy_directory().

        Checks all child videos of the specified media data object. If the
        associated thumbnail file exists, moves it into its own sub-directory.

        Args:

            media_data_obj (media.Channel, media.Playlist or media.Folder):
                The media data object whose directory must be tidied up

        """

        for video_obj in media_data_obj.compile_all_videos( [] ):

            if video_obj.file_name is not None:

                # Thumbnails might be in one of four locations. If the
                #   thumbnail has already been moved into /.thumbs, then of
                #   course we don't move it again (and this function returns an
                #   empty list)
                path_list = utils.find_thumbnail_restricted(
                    self.app_obj,
                    video_obj,
                )

                if path_list:

                    main_path = os.path.abspath(
                        os.path.join(
                            path_list[0], path_list[1],
                        ),
                    )

                    subdir = os.path.abspath(
                        os.path.join(
                            path_list[0], self.app_obj.thumbs_sub_dir,
                        ),
                    )

                    subdir_path = os.path.abspath(
                        os.path.join(
                            path_list[0],
                            self.app_obj.thumbs_sub_dir,
                            path_list[1],
                        ),
                    )

                    if os.path.isfile(main_path) \
                    and not os.path.isfile(subdir_path):

                        try:
                            if not os.path.isdir(subdir):
                                os.makedirs(subdir)

                            shutil.move(main_path, subdir_path)
                            self.thumb_moved_count += 1

                        except:
                            pass


    def delete_thumb(self, media_data_obj):

        """Called by self.tidy_directory().

        Checks all child videos of the specified media data object. If the
        associated thumbnail file exists, delete it.

        Args:

            media_data_obj (media.Channel, media.Playlist or media.Folder):
                The media data object whose directory must be tidied up

        """

        for video_obj in media_data_obj.compile_all_videos( [] ):

            if video_obj.file_name is not None:

                # Thumbnails might be in one of four locations
                thumb_path = utils.find_thumbnail(self.app_obj, video_obj)

                # If the video's parent container has an alternative download
                #   destination set, we must check the corresponding media
                #   data object. If the latter also has a media.Video object
                #   matching this video, then this function returns None and
                #   nothing is deleted
                if thumb_path is not None:

                    thumb_path = self.check_video_in_actual_dir(
                        media_data_obj,
                        video_obj,
                        thumb_path,
                    )

                if thumb_path is not None \
                and os.path.isfile(thumb_path):

                    # Delete the thumbnail file
                    os.remove(thumb_path)
                    self.thumb_deleted_count += 1


    def convert_webp(self, media_data_obj):

        """Called by self.tidy_directory().

        Checks all child videos of the specified media data object. If the
        associated thumbnail file in a .webp or malformed .jpg format exists,
        convert it to .jpg.

        Args:

            media_data_obj (media.Channel, media.Playlist or media.Folder):
                The media data object whose directory must be tidied up

        """

        for video_obj in media_data_obj.compile_all_videos( [] ):

            if video_obj.file_name is not None:

                # Thumbnails might be in one of four locations
                thumb_path = utils.find_thumbnail_webp(self.app_obj, video_obj)

                # If the video's parent container has an alternative download
                #   destination set, we must check the corresponding media
                #   data object. If the latter also has a media.Video object
                #   matching this video, then this function returns None and
                #   nothing is deleted
                if thumb_path is not None:

                    thumb_path = self.check_video_in_actual_dir(
                        media_data_obj,
                        video_obj,
                        thumb_path,
                    )

                if thumb_path is not None \
                and os.path.isfile(thumb_path):

                    # Convert to .jpg
                    if not self.app_obj.ffmpeg_manager_obj.convert_webp(
                        thumb_path
                    ):
                        # FFmpeg is probably not installed; don't try any more
                        #   conversions
                        self.convert_webp_flag = False
                        self.app_obj.set_ffmpeg_fail_flag(True)

                    else:

                        self.webp_converted_count += 1


    def move_data(self, media_data_obj):

        """Called by self.tidy_directory().

        Checks all child videos of the specified media data object. If the
        associated thumbnail file exists, moves it into its own sub-directory.

        Args:

            media_data_obj (media.Channel, media.Playlist or media.Folder):
                The media data object whose directory must be tidied up

        """

        for video_obj in media_data_obj.compile_all_videos( [] ):

            if video_obj.file_name is not None:

                # Description/JSON/annotations files might be in one of four
                #   locations. If the file has already been moved into /.data,
                #   then of course we don't move it again
                for ext in ['.description', '.info.json', '.annotations.xml']:

                    main_path = video_obj.get_actual_path_by_ext(
                        self.app_obj,
                        ext,
                    )

                    subdir = os.path.abspath(
                        os.path.join(
                            video_obj.parent_obj.get_actual_dir(self.app_obj),
                            self.app_obj.metadata_sub_dir,
                        ),
                    )

                    subdir_path \
                    = video_obj.get_actual_path_in_subdirectory_by_ext(
                        self.app_obj,
                        ext,
                    )

                    if os.path.isfile(main_path) \
                    and not os.path.isfile(subdir_path):

                        try:
                            if not os.path.isdir(subdir):
                                os.makedirs(subdir)

                            # (os.rename sometimes fails on external hard
                            #   drives; this is safer)
                            shutil.move(main_path, subdir_path)
                            self.data_moved_count += 1

                        except:
                            pass


    def delete_descrip(self, media_data_obj):

        """Called by self.tidy_directory().

        Checks all child videos of the specified media data object. If the
        associated description file exists, delete it.

        Args:

            media_data_obj (media.Channel, media.Playlist or media.Folder):
                The media data object whose directory must be tidied up

        """

        for video_obj in media_data_obj.compile_all_videos( [] ):

            if video_obj.file_name is not None:

                main_path = video_obj.get_actual_path_by_ext(
                    self.app_obj,
                    '.description',
                )

                # If the video's parent container has an alternative download
                #   destination set, we must check the corresponding media
                #   data object. If the latter also has a media.Video object
                #   matching this video, then this function returns None and
                #   nothing is deleted
                main_path = self.check_video_in_actual_dir(
                    media_data_obj,
                    video_obj,
                    main_path,
                )

                if main_path is not None \
                and os.path.isfile(main_path):

                    # Delete the description file
                    os.remove(main_path)
                    self.descrip_deleted_count += 1

                # (Repeat for a file that might be in the sub-directory
                #   '.data')
                subdir_path = video_obj.get_actual_path_in_subdirectory_by_ext(
                    self.app_obj,
                    '.description',
                )

                subdir_path = self.check_video_in_actual_dir(
                    subdir_path,
                    video_obj,
                    subdir_path,
                )

                if subdir_path is not None \
                and os.path.isfile(subdir_path):

                    os.remove(subdir_path)
                    self.descrip_deleted_count += 1


    def delete_json(self, media_data_obj):

        """Called by self.tidy_directory().

        Checks all child videos of the specified media data object. If the
        associated metadata (JSON) file exists, delete it.

        Args:

            media_data_obj (media.Channel, media.Playlist or media.Folder):
                The media data object whose directory must be tidied up

        """

        for video_obj in media_data_obj.compile_all_videos( [] ):

            if video_obj.file_name is not None:

                main_path = video_obj.get_actual_path_by_ext(
                    self.app_obj,
                    '.info.json',
                )

                # If the video's parent container has an alternative download
                #   destination set, we must check the corresponding media
                #   data object. If the latter also has a media.Video object
                #   matching this video, then this function returns None and
                #   nothing is deleted
                main_path = self.check_video_in_actual_dir(
                    media_data_obj,
                    video_obj,
                    main_path,
                )

                if main_path is not None \
                and os.path.isfile(main_path):

                    # Delete the metadata file
                    os.remove(main_path)
                    self.json_deleted_count += 1

                # (Repeat for a file that might be in the sub-directory
                #   '.data')
                subdir_path = video_obj.get_actual_path_in_subdirectory_by_ext(
                    self.app_obj,
                    '.info.json',
                )

                subdir_path = self.check_video_in_actual_dir(
                    media_data_obj,
                    video_obj,
                    subdir_path,
                )

                if subdir_path is not None \
                and os.path.isfile(subdir_path):

                    os.remove(subdir_path)
                    self.json_deleted_count += 1


    def delete_xml(self, media_data_obj):

        """Called by self.tidy_directory().

        Checks all child videos of the specified media data object. If the
        associated annotation file exists, delete it.

        Args:

            media_data_obj (media.Channel, media.Playlist or media.Folder):
                The media data object whose directory must be tidied up

        """

        for video_obj in media_data_obj.compile_all_videos( [] ):

            if video_obj.file_name is not None:

                main_path = video_obj.get_actual_path_by_ext(
                    self.app_obj,
                    '.annotations.xml',
                )

                # If the video's parent container has an alternative download
                #   destination set, we must check the corresponding media
                #   data object. If the latter also has a media.Video object
                #   matching this video, then this function returns None and
                #   nothing is deleted
                main_path = self.check_video_in_actual_dir(
                    media_data_obj,
                    video_obj,
                    main_path,
                )

                if main_path is not None \
                and os.path.isfile(main_path):

                    # Delete the annotation file
                    os.remove(main_path)
                    self.xml_deleted_count += 1

                # (Repeat for a file that might be in the sub-directory
                #   '.data')
                subdir_path = video_obj.get_actual_path_in_subdirectory_by_ext(
                    self.app_obj,
                    '.annotations.xml',
                )

                subdir_path = self.check_video_in_actual_dir(
                    media_data_obj,
                    video_obj,
                    subdir_path,
                )

                if subdir_path is not None \
                and os.path.isfile(subdir_path):

                    os.remove(subdir_path)
                    self.xml_deleted_count += 1


    def call_moviepy(self, video_obj, video_path):

        """Called by thread inside self.check_video_corrupt().

        When we call moviepy.editor.VideoFileClip() on a corrupted video file,
        moviepy freezes indefinitely.

        This function is called inside a thread, so a timeout of (by default)
        ten seconds can be applied.

        Args:

            video_obj (media.Video): The video object being updated

            video_path (str): The path to the video file itself

        """

        try:
            clip = moviepy.editor.VideoFileClip(video_path)

        except:
            self.video_corrupt_count += 1

            self.app_obj.main_win_obj.output_tab_write_stdout(
                1,
                '   ' + _('Video file might be corrupt:') + ' \'' \
                + video_obj.name + '\'',
            )


    def check_video_in_actual_dir(self, container_obj, video_obj, delete_path):

        """Called by self.delete_video(), .delete_descrip(), .delete_json(),
        .delete_xml() and .delete_thumb().

        If the video's parent container has an alternative download destination
        set, we must check the corresponding media data object. If the latter
        also has a media.Video object matching this video, then this function
        returns None and nothing is deleted. Otherwise, the specified
        delete_path is returned, so it can be deleted.

        Args:

            container_obj (media.Channel, media.Playlist, media.Folder): A
                channel, playlist or folder

            video_obj (media.Video): A video contained in that channel,
                playlist or folder

            delete_path (str): The path to a file which the calling function
                wants to delete

        Returns:

            The specified delete_path if it can be deleted, or None if it
                should not be deleted

        """

        if container_obj.dbid == container_obj.master_dbid:

            # No alternative download destination to check
            return delete_path

        else:

            # Get the channel/playlist/folder acting as container_obj's
            #   alternative download destination
            master_obj = self.app_obj.media_reg_dict[container_obj.master_dbid]

            # Check its videos. Are there any videos with the same name?
            for child_obj in master_obj.child_list:

                if child_obj.file_name is not None \
                and child_obj.file_name == video_obj.file_name:

                    # Don't delete the file associated with this video
                    return None

            # There are no videos with the same name, so the file can be
            #   deleted
            return delete_path


    def stop_tidy_operation(self):

        """Called by mainapp.TartubeApp.do_shutdown(), .stop_continue(),
        .on_button_stop_operation() and mainwin.MainWin.on_stop_menu_item().

        Stops the tidy operation.
        """

        self.running_flag = False
