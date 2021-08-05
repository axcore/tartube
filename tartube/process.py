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
import subprocess
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

        # The child process created by self.create_child_process(). Used only
        #   by self.slice_video() to concatenate video clips; all other child
        #   processes are handled by ffmpeg_tartube.FFmpegManager
        self.child_process = None

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
        # Flag set to True if a fatal error occurs
        self.fatal_error_flag = False

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

        # Show information about the process operation in the Output tab
        self.app_obj.main_win_obj.output_tab_write_stdout(
            1,
            _('Starting process operation'),
        )

        # Process each video in turn
        dest_dir_list = []
        check_dict = {}
        while self.running_flag and self.video_list:

            video_obj = self.video_list.pop(0)
            self.job_count += 1

            # Update our progress in the Output tab
            self.app_obj.main_win_obj.output_tab_write_stdout(
                1,
                _('Video') + ' ' + str(self.job_count) + '/' \
                + str(self.job_total) + ': ' + video_obj.name,
            )

            if self.options_obj.options_dict['output_mode'] == 'split':

                # Split the video into video clips
                dest_dir = self.split_video(video_obj)
                if self.fatal_error_flag:
                    break

                else:
                    # Add the returned destination directory to a list,
                    #   first checking for duplicates
                    if not dest_dir in check_dict:
                        dest_dir_list.append(dest_dir)
                        check_dict[dest_dir] = None

            elif self.options_obj.options_dict['output_mode'] == 'slice':

                # Produce a single output video with slices removed
                dest_dir = self.slice_video(video_obj)
                if self.fatal_error_flag:
                    # This is a fatal error
                    break

                else:
                    # Add the returned destination directory to a list,
                    #   first checking for duplicates
                    if not dest_dir in check_dict:
                        dest_dir_list.append(dest_dir)
                        check_dict[dest_dir] = None

            else:

                # Process the video with FFmpeg. One source video produces one
                #   output video
                self.process_video(video_obj)

            # Pause a moment, before the next iteration of the loop (don't want
            #   to hog resources)
            time.sleep(self.sleep_time)

        # Operation complete. Set the stop time
        self.stop_time = int(time.time())

        # Show a confirmation in the Output tab
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

        # Open the destination directories, if required
        if self.options_obj.options_dict['output_mode'] == 'split' \
        and self.app_obj.split_video_auto_open_flag:

            for dest_dir in dest_dir_list:
                utils.open_file(self.app_obj, dest_dir)


    def create_child_process(self, cmd_list):

        """Called by self.slice_video() only, in order to concatenate video
        clips into a single video file. All other child process are handled by
        ffmpeg_tartube.FFmpegManager.

        Based on YoutubeDLDownloader._create_process().

        Executes the system command, creating a new child process which
        concatenates files.

        Args:

            cmd_list (list): Python list that contains the command to execute.

        """

        info = preexec = None
        if os.name == 'nt':
            # Hide the child process window that MS Windows helpfully creates
            #   for us
            info = subprocess.STARTUPINFO()
            info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        else:
            # Make this child process the process group leader, so that we can
            #   later kill the whole process group with os.killpg
            preexec = os.setsid

        try:
            self.child_process = subprocess.Popen(
                cmd_list,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=preexec,
                startupinfo=info,
            )

        except (ValueError, OSError) as error:
            pass


    def create_temp_dir(self, orig_video_obj, parent_dir):

        """Called by self.slice_video().

        Before splitting a video into clips, and then concatenating the clips,
        create a temporary directory for the clips so we don't accidentally
        overwrite anything.

        Args:

            orig_video_obj (media.Video): The video to be split

            parent_dir (str): Full path to the parent container's directory

        Return values:

            The temporary directory created on success, None on failure

        """

        # Work out where the temporary directory should be...
        temp_dir = os.path.abspath(
            os.path.join(
                parent_dir,
                '.clips_' + str(orig_video_obj.dbid)
            ),
        )

        # ...then create it
        try:
            if os.path.isdir(temp_dir):
                self.app_obj.remove_directory(temp_dir)

            self.app_obj.make_directory(temp_dir)

            return temp_dir

        except:
            return None


    def is_child_process_alive(self):

        """Called by self.split_video().

        Based on YoutubeDLDownloader._proc_is_alive().

        Called continuously during concatenation of video clips to check
        whether the child process has finished or not.

        Returns:

            True if the child process is alive, otherwise returns False.

        """

        if self.child_process is None:
            return False

        return self.child_process.poll() is None


    def process_video(self, orig_video_obj, dest_dir=None, start_point=None, \
    stop_point=None, clip_title=None):

        """Called by self.run(), .slice_video() and .split_video().

        Sends a single video to FFmpeg for post-processing.

        Args:

            orig_video_obj (media.Video): The video to be sent to FFmpeg

            dest_dir (str): When splitting a video, the directory into which
                the video clips are saved (which may or may not be the same as
                the directory of the original file). Depending on settings, it
                may be the directory for a media.Folder object, or not. Not
                specified when not splitting a video

            start_point, stop_point (str): When splitting a video, the
                timestamps at which to start/stop (e.g. '15:29'). If
                'stop_point' is not specified, the clip ends at the end of
                the video. When removing video slices, the time (in seconds)
                at the beginning/end of each slice. If 'stop_point' is not
                specified, the slice ends at the end of the video

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
        if orig_video_obj.file_name is None \
        and (
            not orig_video_obj.dummy_flag
            or orig_video_obj.dummy_path is None
        ):
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
            orig_video_obj,
            start_point,
            stop_point,
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
            orig_video_obj.name,
            self.job_count,
            self.job_total,
        )

        # Update the Output tab again
        self.app_obj.main_win_obj.output_tab_write_system_cmd(
            1,
            ' '.join(cmd_list),
        )

        # Process the video
        success_flag, msg \
        = self.app_obj.ffmpeg_manager_obj.run_ffmpeg_with_options(
            orig_video_obj,
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
            if start_point is not None:
                return True

            # Otherwise, delete the original video file, if required
            if self.options_obj.options_dict['delete_original_flag'] \
            and os.path.isfile(source_path) \
            and os.path.isfile(output_path) \
            and source_path != output_path:

                if not self.app_obj.remove_file(source_path):
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
            old_name = orig_video_obj.name

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
                    orig_video_obj,
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

                    # (On MSWin, can't do os.rename if the destination file
                    #   already exists)
                    if os.path.isfile(new_thumb_path):
                        self.app_obj.remove_file(new_thumb_path)

                    # (os.rename sometimes fails on external hard drives; this
                    #   is safer)
                    if not self.app_obj.move_file_or_directory(
                        thumb_path,
                        new_thumb_path,
                    ):
                        self.fail_count += 1

                        self.app_obj.main_win_obj.output_tab_write_stderr(
                            1,
                            _('Could not rename the thumbnail:') + ' ' \
                            + thumb_path,
                        )

            # If a video/audio file was processed, update its filename
            if self.options_obj.options_dict['input_mode'] != 'thumb':

                if not orig_video_obj.dummy_flag:
                    orig_video_obj.set_file_from_path(output_path)
                else:
                    orig_video_obj.set_dummy_path(output_path)

                # Also update its .name IV (but its .nickname)
                if rename_flag:
                    orig_video_obj.set_name(new_name)

            return True


    def slice_video(self, orig_video_obj):

        """Called by self.run().

        Removes slices from a video using FFmpeg.

        Args:

            orig_video_obj (media.Video): The video to be sent to FFmpeg

        Return values:

            The video's parent directory on success, None on failure

        """

        # Contact the SponsorBlock server to update the video's slice data, if
        #   allowed
        # (No point doing it, if the temporary buffer is set)
        if not self.app_obj.temp_slice_list:

            if self.app_obj.sblock_re_extract_flag \
            and not orig_video_obj.slice_list:
                utils.fetch_slice_data(
                    app_obj,
                    orig_video_obj,
                    self.download_worker_obj.worker_id,
                )

        # Import the correct slice list
        if self.app_obj.temp_slice_list:

            # Use the temporary buffer
            slice_list = self.app_obj.temp_slice_list.copy()
            temp_flag = True
            # (The temporary buffer, once used, must be emptied immediately)
            self.app_obj.reset_temp_slice_list()

        elif self.options_obj.options_dict['slice_mode'] == 'video' \
        and orig_video_obj.slice_list:

            # Use the video's own slice list
            slice_list = orig_video_obj.slice_list.copy()
            temp_flag = False

        elif self.options_obj.options_dict['slice_mode'] == 'custom' \
        and self.options_obj.options_dict['slice_list']:

            # Use the slice list specified by the FFmpeg options object
            slice_list = self.options_obj.options_dict['slice_list']
            temp_flag = False

        # Convert this list from a list of video slices to be removed, to a
        #   list of video clips to be retained
        # The returned list is in groups of two, in the form
        #   [start_time, stop_time]
        # ...where 'start_time' and 'stop_time' are floating-point values in
        #   seconds. 'stop_time' can be None to signify the end of the video,
        #   but 'start_time' is 0 to signify the start of the video
        clip_list = utils.convert_slices_to_clips(
            self.app_obj,
            self.app_obj.general_custom_dl_obj,
            slice_list,
            temp_flag,
        )
        if not clip_list:

            self.app_obj.main_win_obj.output_tab_write_stderr(
                1,
                _('FAILED: No slices associated with video'),
            )

            self.fail_count += 1
            return None

        # Create a temporary directory for this video so we don't accidentally
        #   overwrite anything
        parent_dir = orig_video_obj.parent_obj.get_actual_dir(self.app_obj)
        orig_video_path = orig_video_obj.get_actual_path(self.app_obj)
        temp_dir = self.create_temp_dir(orig_video_obj, parent_dir)
        if temp_dir is None:

            self.app_obj.main_win_obj.output_tab_write_stderr(
                1,
                _('FAILED: Can\'t create temporary directory'),
            )

            self.fail_count += 1
            self.fatal_error_flag = True
            return None

        # Extract the clips, one at a time. For each video clip, we use a
        #   separate FFmpeg command
        list_size = len(clip_list)
        for i in range(list_size):

            mini_list = clip_list[i]
            start_time = mini_list[0]
            stop_time = mini_list[1]

            # Update the Output tab
            if not stop_time:

                self.app_obj.main_win_obj.output_tab_write_stdout(
                    1,
                    _('Video clip') + ' ' + str(i + 1) + '/' + str(list_size) \
                    + ': ' + str(start_time) + ' - ' + _('End of video')
                )

            else:

                self.app_obj.main_win_obj.output_tab_write_stdout(
                    1,
                    _('Video clip') + ' ' + str(i + 1) + '/' + str(list_size) \
                    + ': ' + str(start_time) + ' - ' + str(stop_time)
                )

            # Extract the clip
            if not self.process_video(
                orig_video_obj,
                temp_dir,
                start_time,
                stop_time,
                'clip_' + str(i + 1),       # Clip title
            ):
                # Don't continue creating more clips after an error
                self.fatal_error_flag = True
                # (Delete the temporary directory after failure)
                self.app_obj.remove_directory(temp_dir)
                return None

        # If there is more than one clip, they must be concatenated to produce
        #   a single video (like the original video, from which the video
        #   slices have been removed)
        if list_size == 1:
            output_path = os.path.abspath(
                os.path.join(temp_dir, 'clip_1' + orig_video_obj.file_ext),
            )

        else:
            # For FFmpeg's benefit, write a text file listing every clip
            line_list = []
            clips_file = os.path.abspath(
                os.path.join(temp_dir, 'clips.txt'),
            )

            for i in range(list_size):
                line_list.append(
                    'file \'' + os.path.abspath(
                        os.path.join(
                            temp_dir,
                            'clip_' + str(i + 1) + orig_video_obj.file_ext,
                        ),
                    ),
                )

            with open(clips_file, 'w') as fh:
                fh.write('\n'.join(line_list))

            # Prepare the FFmpeg command to concatenate the clips together
            output_path = os.path.abspath(
                os.path.join(
                    temp_dir,
                    orig_video_obj.file_name + orig_video_obj.file_ext,
                ),
            )

            cmd_list = [
                self.app_obj.ffmpeg_manager_obj.get_executable(),
                '-safe',
                '0',
                '-f',
                'concat',
                '-i',
                clips_file,
                '-c',
                'copy',
                output_path,
            ]

            # Update the Output tab again
            self.app_obj.main_win_obj.output_tab_write_system_cmd(
                1,
                ' '.join(cmd_list),
            )

            # Create a new child process using the command
            self.create_child_process(cmd_list)

            # Wait for the concatenation to finish. We are not bothered
            #   about reading the child process STDOUT/STDERR, since we can
            #   just test for the existence of the output file
            while self.is_child_process_alive():
                time.sleep(self.sleep_time)

            if not os.path.isfile(output_path):

                self.app_obj.main_win_obj.output_tab_write_stderr(
                    1,
                    _('FAILED: Can\'t concatenate clips'),
                )

                # (Delete the temporary directory after failure)
                self.fail_count += 1
                self.app_obj.remove_directory(temp_dir)
                return None

        # Move the single video file back into the parent directory, replacing
        #   any file of the same name that's already there
        if os.path.isfile(orig_video_path):
            self.app_obj.remove_file(orig_video_path)

        if not self.app_obj.move_file_or_directory(
            output_path,
            orig_video_path,
        ):
            self.app_obj.main_win_obj.output_tab_write_stderr(
                1,
                _(
                    'FAILED: Clips were concatenated, but could not move' \
                    + ' the output file out of the temporary directory',
                ),
            )

            # (Delete the temporary directory after failure)
            self.fail_count += 1
            self.app_obj.remove_directory(temp_dir)
            return None

        # Delete the temporary directory
        self.app_obj.remove_directory(temp_dir)

        # Procedure successful
        return parent_dir


    def split_video(self, orig_video_obj):

        """Called by self.run().

        Splits a video into video clips using FFmpeg.

        Args:

            orig_video_obj (media.Video): The video to be sent to FFmpeg

        Return values:

            The destination directory of the clips on success, None on failure

        """

        # Re-extract timestamps from the video's .info.json or .description
        #   file, if allowed
        # (No point doing it, if the temporary buffer is set)
        if not self.app_obj.temp_stamp_list:

            if self.app_obj.video_timestamps_re_extract_flag \
            and not orig_video_obj.stamp_list:
                self.app_obj.update_video_from_json(orig_video_obj, 'chapters')

            if self.app_obj.video_timestamps_re_extract_flag \
            and not orig_video_obj.stamp_list:
                orig_video_obj.extract_timestamps_from_descrip(self.app_obj)

        # Set the containing folder, creating a media.Folder object and/or a
        #   sub-directory for the video clips, if required
        parent_obj, parent_dir, dest_obj, dest_dir \
        = utils.clip_set_destination(self.app_obj, orig_video_obj)

        if parent_obj is None:

            # There is already a media.Folder with the same name, somewhere
            #   else in the database
            self.app_obj.main_win_obj.output_tab_write_stderr(
                1,
                _(
                'FAILED: Can\'t create the destination folder either because' \
                + ' a folder with the same name already exists, or because' \
                + ' new folders can\'t be added to the parent folder',
                ),
            )

            self.fail_count += 1
            self.fatal_error_flag = True
            return None

        # Import the correct timestamp list
        if self.app_obj.temp_stamp_list:

            # Use the temporary buffer
            stamp_list = self.app_obj.temp_stamp_list.copy()
            # (The temporary buffer, once used, must be emptied immediately)
            self.app_obj.reset_temp_stamp_list()

        elif self.options_obj.options_dict['split_mode'] == 'video' \
        and orig_video_obj.stamp_list:

            # Use the video's own timestamp list
            stamp_list = orig_video_obj.stamp_list.copy()

        elif self.options_obj.options_dict['split_mode'] == 'custom' \
        and self.options_obj.options_dict['split_list']:

            # Use the timestamp list specified by the FFmpeg options object
            stamp_list = self.options_obj.options_dict['split_list']

        # Split the video
        if stamp_list:

            # One source video is split into one or more video clips, using
            #   timestamps provided by the media.Video object itself
            # Each video clip uses a separate FFmpeg command
            list_size = len(stamp_list)
            for i in range(list_size):

                # List in the form
                #   [start_stamp, stop_stamp, clip_title]
                # If 'stop_stamp' is not specified, then the 'start_stamp' of
                #   the next clip is used. If there are no more clips, then
                #   this clip will end at the end of the video
                start_stamp, stop_stamp, clip_title \
                = utils.clip_extract_data(stamp_list, i)

                # Set a (hopefully unique) clip title
                clip_title = utils.clip_prepare_title(
                    self.app_obj,
                    orig_video_obj,
                    self.clip_title_dict,
                    clip_title,
                    i + 1,
                    list_size,
                )

                self.clip_title_dict[clip_title] = None

                # Update the Output tab
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
                if not self.process_video(
                    orig_video_obj,
                    dest_dir,
                    start_stamp,
                    stop_stamp,
                    clip_title,
                ):
                    # Don't continue creating more clips after an error
                    self.fatal_error_flag = True
                    return None

                elif dest_obj \
                and self.app_obj.split_video_add_db_flag:

                    new_video_obj = utils.clip_add_to_db(
                        self.app_obj,
                        dest_obj,
                        orig_video_obj,
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
            return None

        # Splitting of this video is complete. Delete the original video, if
        #   required
        if self.app_obj.split_video_auto_delete_flag \
        and isinstance(orig_video_obj.parent_obj, media.Folder):
            self.app_obj.delete_video(
                orig_video_obj,
                True,           # Delete all files
                True,           # Don't update Video Index yet
                True,           # Or Video Catalogue
            )

        # Procedure successful
        return dest_dir


    def stop_process_operation(self):

        """Called by mainapp.TartubeApp.do_shutdown(), .stop_continue(),
        .on_button_stop_operation() and mainwin.MainWin.on_stop_menu_item().

        Stops the process operation.
        """

        self.running_flag = False
