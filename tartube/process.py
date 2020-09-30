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


"""Process operation classes."""


# Import Gtk modules
import gi
from gi.repository import GObject


# Import other modules
import os
import re
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
    are sent to FFmpeg for post-processing.

    Args:

        app_obj (mainapp.TartubeApp): The main application

        option_string (str): A string of FFmpeg options (usually a copy of
            mainapp.TartubeApp.ffmpeg_option_string)

        add_string (str): Text to add to the end of every filename (usually a
            copy of mainapp.TartubeApp.ffmpeg_add_string)

        regex_string, substitute_string (str): A regex substitution to apply to
            every filename (usually a copy of
            mainapp.TartubeApp.ffmpeg_regex_string and
            .ffmpeg_substitute_string); ignored if regex_string is an empty
            string, not ignored if substitute_string is an empty string

        ext_string (str): The replacement file extension to use (usually a copy
            of mainapp.TartubeApp.ffmpeg_ext_string); ignored if an empty
            string

        delete_flag (bool): True if the old video file should be deleted (and
            media.Video IVs updated) if FFmpeg's output file has a different
            name (for example, if the file extension has changed); False
            otherwise

        video_list (list): A list of media.Video objects to be passed to FFmpeg

    """


    # Standard class methods


    def __init__(self, app_obj, option_string, add_string, regex_string,
    substitute_string, ext_string, delete_flag, video_list):

        super(ProcessManager, self).__init__()

        # IV list - class objects
        # -----------------------
        # The mainapp.TartubeApp object
        self.app_obj = app_obj
        # A list of media.Video objects to be passed to FFmpeg
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

        # A string of FFmpeg options (usually a copy of
        #   mainapp.TartubeApp.ffmpeg_option_string)
        self.option_string = option_string
        # That string, converted to a list of options by self.run
        self.option_list = []

        # Text to add to the end of every filename (usually a copy of
        #   mainapp.TartubeApp.ffmpeg_add_string)
        self.add_string = add_string
        # A regex substitution to apply to every filename (usually a copy of
        #   mainapp.TartubeApp.ffmpeg_regex_string and
        #   .ffmpeg_substitute_string); ignored if regex_string is an
        #   empty string, not ignored if substitute_string is an empty string
        self.regex_string = regex_string
        self.substitute_string = substitute_string
        # The replacement file extension to use (usually a copy of
        #   mainapp.TartubeApp.ffmpeg_ext_string); ignored if an empty string
        self.ext_string = ext_string
        # Flag set to True if the old video file should be deleted (and
        #   media.Video IVs updated) if FFmpeg's output file has a different
        #   name (for example, if the file extension has changed); False
        #   otherwise
        self.delete_flag = delete_flag

        # Code
        # ----

        # Prepare a list of FFmpeg options, from the option string specified by
        #   the user
        self.option_list = utils.parse_ytdl_options(self.option_string)

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
        while self.running_flag and self.video_list:

            self.process_video(self.video_list.pop(0))

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


    def process_video(self, video_obj):

        """Called by self.run().

        Sends a single video to FFmpeg for post-processing.

        Args:

            video_obj (media.Video): The video to be sent to FFmpeg

        """

        # Get the path to the video file, which might be in the directory of
        #   its parent channel/playlist/folder, or in a different directory
        #   altogether
        input_path = video_obj.get_actual_path(self.app_obj)
        # Set the output path; the same as the input path, unless the user has
        #   requested changes
        output_file, output_ext = os.path.splitext(input_path)

        if self.add_string != '':
            output_file += self.add_string

        if self.substitute_string != '':
            output_file = re.sub(
                self.regex_string,
                self.substitute_string,
                output_file,
            )

        if self.ext_string != '':
            output_ext = self.ext_string

        output_path = output_file + output_ext

        # Update the main window's progress bar
        self.job_count += 1
        GObject.timeout_add(
            0,
            self.app_obj.main_win_obj.update_progress_bar,
            video_obj.name,
            self.job_count,
            self.job_total,
        )

        # Update our progress in the Output Tab
        self.app_obj.main_win_obj.output_tab_write_stdout(
            1,
            '   ' + _('Video') + ' ' + str(self.job_count) + '/' \
            + str(self.job_total) + ': ' + video_obj.name,
        )

        # Show the system command we're about to execute...
        test_list = self.app_obj.ffmpeg_manager_obj.run_ffmpeg(
            input_path,
            output_path,
            self.option_list,
            True,
        )

        self.app_obj.main_win_obj.output_tab_write_stdout(
            1,
            '      ' + _('Input:') + ' ' + ' '.join(test_list[1]),
        )

        # ...and then send the command to FFmpeg for processing, which returns
        #   a list in the form (success_flag, optional_message)
        result_list = self.app_obj.ffmpeg_manager_obj.run_ffmpeg(
            input_path,
            output_path,
            self.option_list,
        )

        if not result_list or not result_list[0]:
            self.app_obj.main_win_obj.output_tab_write_stdout(
                1,
                '      ' + _('Output: FAILED:') + ' ' + result_list[1],
            )

        else:

            self.app_obj.main_win_obj.output_tab_write_stdout(
                1,
                '      ' + _('Output:') + ' ' +  output_path,
            )

            # Delete the original video file, and update media.Video IVs, if
            #   required
            if self.delete_flag \
            and os.path.isfile(input_path) \
            and os.path.isfile(output_path) \
            and input_path != output_path:
                os.remove(input_path)
                video_obj.set_file(output_file, output_ext)


    def stop_process_operation(self):

        """Called by mainapp.TartubeApp.do_shutdown(), .stop_continue(),
        .on_button_stop_operation() and mainwin.MainWin.on_stop_menu_item().

        Stops the process operation.
        """

        self.running_flag = False
