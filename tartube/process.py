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


"""Process operation classes."""


# Import Gtk modules
import gi
from gi.repository import GObject


# Import other modules
import os
import re
import shutil
import threading
import time


# Import our modules
import media
import utils
# Use same gettext translations
from mainapp import _


# Classes


class ProcessManager(threading.Thread):

    """Called by mainapp.TartubeApp.process_manager_start().

    Python class to manage the process operation, in which media.Video objects
    are processed with FFmpeg, using the options specified by a
    ffmpeg_tartube.FFmpegOptionsManager object.

    Args:

        app_obj (mainapp.TartubeApp): The main application

        options_obj (ffmpeg_tartube.FFmpegOptionsManager): Object specifying
            the FFmpeg options to apply

        video_list (list): A list of media.Video objects

    """


    # Standard class methods


    def __init__(self, app_obj, options_obj, video_list):

        super(ProcessManager, self).__init__()

        # IV list - class objects
        # -----------------------
        # The mainapp.TartubeApp object
        self.app_obj = app_obj
        # ffmpeg_tartube.FFmpegOptionsManager object specifying the FFmpeg
        #   options to apply
        self.options_obj = options_obj
        # A list of media.Video objects to be processed with FFmpeg
        self.video_list = video_list


        # IV list - other
        # ---------------
        # Flag set to False if self.stop_process_operation() is called, which
        #   halts the operation immediately
        self.running_flag = True

        # The time at which the process operation began (in seconds since
        #   epoch)
        self.start_time = int(time.time())
        # The time at which the process operation completed (in seconds since
        #   epoch)
        self.stop_time = None
        # The time (in seconds) between iterations of the loop in self.run()
        self.sleep_time = 0.25

        # The number of media.Video objects processed so far...
        self.job_count = 0
        # ...and the total number to process (these numbers are displayed in
        #   the progress bar in the Videos tab)
        self.job_total = len(video_list)
        # The total number of successful and failed FFmpeg procedures
        self.success_count = 0
        self.fail_count = 0
        # Flag set to True if any video file is successfully split (which
        #   may require mainapp.TartubeApp.update_manager_finished to redraw
        #   the Video Index and Video Catalogue)
        self.split_success_flag = False

        # Dictionary of clip tiles used during this operation (i.e. when
        #   splitting a video into clips), used to re-name duplicates
        self.clip_title_dict = {}

        # List of new media.Video objects added to the database. At the end
        #   of the operation, we try to detect their video length/file size in
        #   the usual way
        self.new_video_list = []

        # Code
        # ----

        # Let's get this party started!
        self.start()


    # Public class methods


    def run(self):

        """Called as a result of self.__init__().

        Calls FFmpegManager.run_ffmpeg for every media.Video object in the
        list.

        Then informs the main application that the process operation is
        complete.
        """

        # Show information about the process operation in the Output Tab
        self.app_obj.main_win_obj.output_tab_write_stdout(
            1,
            _('Starting process operation'),
        )

        # Process each video in turn
        dest_dir = None
        while self.running_flag and self.video_list:

            video_obj = self.video_list.pop(0)
            self.job_count += 1

            # Update our progress in the Output Tab
            self.app_obj.main_win_obj.output_tab_write_stdout(
                1,
                _('Video') + ' ' + str(self.job_count) + '/' \
                + str(self.job_total) + ': ' + video_obj.name,
            )

            if self.options_obj.options_dict['output_mode'] != 'split':

                # One source video produces one output video
                self.process_video(video_obj)

            else:

                # Re-extract timestamps from the video's .info.json or
                #   description file, if allowed
                # (No point doing it, if the temporary buffer is set)
                if not self.app_obj.temp_stamp_list:

                    if self.app_obj.video_timestamps_re_extract_flag \
                    and not video_obj.stamp_list:
                        self.app_obj.update_video_from_json(video_obj, True)

                    if self.app_obj.video_timestamps_re_extract_flag \
                    and not video_obj.stamp_list:
                        video_obj.extract_timestamps_from_descrip(self.app_obj)

                # Set the containing folder, creating a media.Folder object
                #   and/or a sub-directory for the video clips, if required
                parent_obj, parent_dir, dest_obj, dest_dir \
                = utils.clip_set_destination(self.app_obj, video_obj)

                if parent_obj is None:

                    # There is already a media.Folder with the same name,
                    #   somewhere else in the database
                    self.app_obj.main_win_obj.output_tab_write_stderr(
                        1,
                        _(
                        'FAILED: Can\'t create the destination folder either' \
                        + ' because a folder with the same name already' \
                        + ' exists, or because new folders can\'t be added' \
                        + ' to the parent folder',
                        ),
                    )

                    self.fail_count += 1
                    # This is a fatal error
                    break

                # Import the correct timestamp list
                if self.app_obj.temp_stamp_list:

                    # Use the temporary buffer
                    stamp_list = self.app_obj.temp_stamp_list.copy()
                    # (The temporary buffer, once used, must be emptied
                    #   immediately)
                    self.app_obj.reset_temp_stamp_list()

                elif self.options_obj.options_dict['split_mode'] == 'video' \
                and video_obj.stamp_list:

                    # Use the video's own timestamp list
                    stamp_list = orig_video_obj.stamp_list.copy()

                elif self.options_obj.options_dict['split_mode'] == 'custom' \
                and self.options_obj.options_dict['split_list']:

                    # Use the timestamp list specified by the FFmpeg options
                    #   object
                    stamp_list = self.options_obj.options_dict['split_list']

                # Split the video
                if stamp_list:

                    # One source video is split into one or more video clips,
                    #   using timestamps provided by the media.Video object
                    #   itself
                    # Each video clip uses a separate FFmpeg command
                    list_size = len(stamp_list)
                    for i in range(list_size):

                        # List in the form
                        #   [start_stamp, stop_stamp, clip_title]
                        # If 'stop_stamp' is not specified, then the
                        #   'start_stamp' of the next clip is used. If there
                        #   are no more clips, then this clip will end at the
                        #   end of the video
                        start_stamp, stop_stamp, clip_title \
                        = utils.prepare_video_clip(stamp_list, i)

                        # Set a (hopefully unique) clip title
                        clip_title = utils.clip_prepare_title(
                            self.app_obj,
                            video_obj,
                            self.clip_title_dict,
                            clip_title,
                            i + 1,
                            list_size,
                        )

                        self.clip_title_dict[clip_title] = None

                        # Update the Output Tab
                        if not stop_stamp:

                            self.app_obj.main_win_obj.output_tab_write_stdout(
                                1,
                                _('Video clip') + ' ' + str(i + 1) + '/' \
                                + str(list_size) + ': ' + start_stamp + ' - ' \
                                + _('End of video') + ': ' + clip_title
                            )

                        else:

                            self.app_obj.main_win_obj.output_tab_write_stdout(
                                1,
                                _('Video clip') + ' ' + str(i + 1) + '/' \
                                + str(list_size) + ': ' + start_stamp + ' - ' \
                                + stop_stamp + ': ' + clip_title
                            )

                        # Extract the clip
                        result = self.process_video(
                            video_obj,
                            dest_dir,
                            start_stamp,
                            stop_stamp,
                            clip_title,
                        )

                        if not result:

                            # Don't continue creating more clips after an error
                            break

                        elif dest_obj \
                        and self.app_obj.split_video_add_db_flag:

                            new_video_obj = utils.clip_add_to_db(
                                self.app_obj,
                                dest_obj,
                                video_obj,
                                clip_title,
                            )

                            if new_video_obj:

                                # All done
                                self.new_video_list.append(new_video_obj)
                                self.split_success_flag = True

                else:

                    self.app_obj.main_win_obj.output_tab_write_stderr(
                        1,
                        _('FAILED: No timestamps associated with video'),
                    )

                    self.fail_count += 1
                    result = False

                # Splitting of this video is complete. Delete the original
                #   video, if required
                if result \
                and self.app_obj.split_video_auto_delete_flag \
                and isinstance(video_obj.parent_obj, media.Folder):
                    self.app_obj.delete_video(
                        video_obj,
                        True,           # Delete all files
                        True,           # Don't update Video Index yet
                        True,           # Or Video Catalogue
                    )

            # Pause a moment, before the next iteration of the loop (don't want
            #   to hog resources)
            time.sleep(self.sleep_time)

        # Operation complete. Set the stop time
        self.stop_time = int(time.time())

        # Show a confirmation in the Output Tab
        self.app_obj.main_win_obj.output_tab_write_stdout(
            1,
            _('Process operation finished'),
        )

        # Let the timer run for a few more seconds to prevent Gtk errors (for
        #   systems with Gtk < 3.24)
        GObject.timeout_add(
            0,
            self.app_obj.process_manager_halt_timer,
        )

        # Open the destination directory, if required
        if dest_dir is not None \
        and self.app_obj.split_video_auto_open_flag:
            utils.open_file(self.app_obj, dest_dir)


    def process_video(self, video_obj, dest_dir=None, start_stamp=None, \
    stop_stamp=None, clip_title=None):

        """Called by self.run().

        Sends a single video to FFmpeg for post-processing.

        Args:

            video_obj (media.Video): The video to be sent to FFmpeg

            dest_dir (str): When splitting a video, the directory into which
                the video clips are saved (which may or may not be the same as
                the directory of the original file). Depending on settings, it
                may be the directory for a media.Folder object, or not. Not
                specified when not splitting a video

            start_stamp, stop_stamp (str): When splitting a video, the
                timestamps at which to start/stop (e.g. '15:29'). If
                'stop_stamp' is not specified, the clip ends at the end of
                the video

            clip_title (str): When splitting a video, the title of this video
                clip (if specified)

        Return values:

            True of success, False on failure

        """

        # mainwin.MainWin.on_video_catalogue_process_ffmpeg_multi() should have
        #   filtered any media.Video objects whose .file_name is unknown, but
        #   just in case, check again
        # (Special case: 'dummy' video objects (those downloaded in the Classic
        #   Mode tab) use different IVs)
        if video_obj.file_name is None \
        and (not video_obj.dummy_flag or video_obj.dummy_path is None):
            self.app_obj.main_win_obj.output_tab_write_stderr(
                1,
                _('FAILED: File name is not known'),
            )

            self.fail_count += 1

            return False

        # Get the source/output files, ahd the full FFmpeg system command (as a
        #   list, and including the source/output files)
        source_path, output_path, cmd_list = self.options_obj.get_system_cmd(
            self.app_obj,
            video_obj,
            start_stamp,
            stop_stamp,
            clip_title,
            dest_dir,
        )

        if source_path is None:

            self.app_obj.main_win_obj.output_tab_write_stderr(
                1,
                _('FAILED: File not found'),
            )

            self.fail_count += 1

            return False

        # Update the main window's progress bar
        GObject.timeout_add(
            0,
            self.app_obj.main_win_obj.update_progress_bar,
            video_obj.name,
            self.job_count,
            self.job_total,
        )

        # Update the Output Tab again
        self.app_obj.main_win_obj.output_tab_write_system_cmd(
            1,
            ' '.join(cmd_list),
        )

        # Process the video
        success_flag, msg \
        = self.app_obj.ffmpeg_manager_obj.run_ffmpeg_with_options(
            video_obj,
            source_path,
            cmd_list,
        )

        if not success_flag:

            self.fail_count += 1

            self.app_obj.main_win_obj.output_tab_write_stderr(
                1,
                _('FAILED:') + ' ' + msg,
            )

            return False

        else:

            self.success_count += 1

            self.app_obj.main_win_obj.output_tab_write_stdout(
                1,
                _('Output file:') + ' ' + output_path,
            )

            # (If splitting files, there is nothing more to do)
            if start_stamp is not None:
                return True

            # Otherwise, delete the original video file, if required
            if self.options_obj.options_dict['delete_original_flag'] \
            and os.path.isfile(source_path) \
            and os.path.isfile(output_path) \
            and source_path != output_path:

                try:

                    os.remove(source_path)

                except:

                    self.fail_count += 1

                    self.app_obj.main_win_obj.output_tab_write_stderr(
                        1,
                        _('Could not delete the original file:') + ' ' \
                        + source_path,
                    )

            # Ignoring changes to the extension, has the video/audio filename
            #   changed?
            new_dir, new_file = os.path.split(output_path)
            new_name, new_ext = os.path.splitext(new_file)
            old_name = video_obj.name

            rename_flag = False
            if (
                self.options_obj.options_dict['add_end_filename'] != '' \
                or self.options_obj.options_dict['regex_match_filename'] \
                != '' \
            ) and old_name != new_name:
                rename_flag = True

            # If the flag is set, rename a thumbnail file to match the
            #   video file
            if rename_flag \
            and self.options_obj.options_dict['rename_both_flag']:

                thumb_path = utils.find_thumbnail(
                    self.app_obj,
                    video_obj,
                    True,           # Rename a temporary thumbnail too
                )

                if thumb_path:

                    thumb_name, thumb_ext = os.path.splitext(thumb_path)
                    new_thumb_path = os.path.abspath(
                        os.path.join(
                            new_dir,
                            new_name + thumb_ext,
                        ),
                    )

                    # (Don't call utils.rename_file(), as we need our own
                    #   try/except)
                    try:

                        # (On MSWin, can't do os.rename if the destination file
                        #   already exists)
                        if os.path.isfile(new_thumb_path):
                            os.remove(new_thumb_path)

                        # (os.rename sometimes fails on external hard drives;
                        #   this is safer)
                        shutil.move(thumb_path, new_thumb_path)

                    except:

                        self.fail_count += 1

                        self.app_obj.main_win_obj.output_tab_write_stderr(
                            1,
                            _('Could not rename the thumbnail:') + ' ' \
                            + thumb_path,
                        )

            # If a video/audio file was processed, update its filename
            if self.options_obj.options_dict['input_mode'] != 'thumb':

                if not video_obj.dummy_flag:
                    video_obj.set_file_from_path(output_path)
                else:
                    video_obj.set_dummy_path(output_path)

                # Also update its .name IV (but its .nickname)
                if rename_flag:
                    video_obj.set_name(new_name)

            return True


    def stop_process_operation(self):

        """Called by mainapp.TartubeApp.do_shutdown(), .stop_continue(),
        .on_button_stop_operation() and mainwin.MainWin.on_stop_menu_item().

        Stops the process operation.
        """

        self.running_flag = False
