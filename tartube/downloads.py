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


"""Download and livestream operation classes."""


# Import Gtk modules
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GObject


# Import other modules
import datetime
import json
import __main__
import os
import queue
import random
import re
import requests
import shutil
import signal
import subprocess
import sys
import threading
import time


# Import our modules
import formats
import mainapp
import media
import options
import utils
# Use same gettext translations
from mainapp import _

if mainapp.HAVE_FEEDPARSER_FLAG:
    import feedparser


# Debugging flag (calls utils.debug_time at the start of every function)
DEBUG_FUNC_FLAG = False


# Decorator to add thread synchronisation to some functions in the
#   downloads.DownloadList object
_SYNC_LOCK = threading.RLock()

def synchronise(lock):
    def _decorator(func):
        def _wrapper(*args, **kwargs):
            lock.acquire()
            ret_value = func(*args, **kwargs)
            lock.release()
            return ret_value
        return _wrapper
    return _decorator


# Classes
class DownloadManager(threading.Thread):

    """Called by mainapp.TartubeApp.download_manager_continue().

    Based on the DownloadManager class in youtube-dl-gui.

    Python class to manage a download operation.

    Creates one or more downloads.DownloadWorker objects, each of which handles
    a single download.

    This object runs on a loop, looking for available workers and, when one is
    found, assigning them something to download. The worker completes that
    download and then waits for another assignment.

    Args:

        app_obj: The mainapp.TartubeApp object

        operation_type (str): 'sim' if channels/playlists should just be
            checked for new videos, without downloading anything. 'real' if
            videos should be downloaded (or not) depending on each media data
            object's .dl_sim_flag IV

            'custom_real' is like 'real', but with additional options applied
            (specified by a downloads.CustomDLManager object). A 'custom_real'
            operation is sometimes preceded by a 'custom_sim' operation (which
            is the same as a 'sim' operation, except that it is always followed
            by a 'custom_real' operation)

            For downloads launched from the Classic Mode tab, 'classic_real'
            for an ordinary download, or 'classic_custom' for a custom
            download. A 'classic_custom' operation is always preceded by a
            'classic_sim' operation (which is the same as a 'sim' operation,
            except that it is always followed by a 'classic_custom' operation)

        download_list_obj (downloads.DownloadManager): An ordered list of
            media data objects to download, each one represented by a
            downloads.DownloadItem object

        custom_dl_obj (downloads.CustomDLManager or None): The custom download
            manager that applies to this download operation. Only specified
            when 'operation_type' is 'custom_sim', 'custom_real', 'classic_sim'
            or 'classic_real'

            For 'custom_real' and 'classic_real', not specified if
            mainapp.TartubeApp.temp_stamp_list or .temp_slice_list are
            specified (because those values take priority)

    """


    # Standard class methods


    def __init__(self, app_obj, operation_type, download_list_obj, \
    custom_dl_obj):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 124 __init__')

        super(DownloadManager, self).__init__()

        # IV list - class objects
        # -----------------------
        # The mainapp.TartubeApp object
        self.app_obj = app_obj
        # Each instance of this object, which represents a single download
        #   operation, creates its own options.OptionsParser object. That
        #   object convert the download options stored in
        #   downloads.DownloadWorker.options_list into a list of youtube-dl
        #   command line options
        self.options_parser_obj = None
        # An ordered list of media data objects to download, each one
        #   represented by a downloads.DownloadItem object
        self.download_list_obj = download_list_obj
        # The custom download manager (downloads.CustomDLManager) that applies
        #   to this download operation. Only specified when 'operation_type' is
        #   'custom_sim', 'custom_real', 'classic_sim' or 'classic_real'
        # For 'custom_real' and 'classic_real', not specified if
        #   mainapp.TartubeApp.temp_stamp_list or .temp_slice_list are
        #   specified (because those values take priority)
        self.custom_dl_obj = custom_dl_obj
        # List of downloads.DownloadWorker objects, each one handling one of
        #   several simultaneous downloads
        self.worker_list = []


        # IV list - other
        # ---------------
        # 'sim' if channels/playlists should just be checked for new videos,
        #   without downloading anything. 'real' if videos should be downloaded
        #   (or not) depending on each media data object's .dl_sim_flag IV
        # 'custom_real' is like 'real', but with additional options applied
        #   (specified by a downloads.CustomDLManager object). A 'custom_real'
        #   operation is sometimes preceded by a 'custom_sim' operation (which
        #   is the same as a 'sim' operation, except that it is always followed
        #   by a 'custom_real' operation)
        # For downloads launched from the Classic Mode tab, 'classic_real' for
        #   an ordinary download, or 'classic_custom' for a custom download. A
        #   'classic_custom' operation is always preceded by a 'classic_sim'
        #   operation (which is the same as a 'sim' operation, except that it
        #   is always followed by a 'classic_custom' operation)
        # This is the default value for the download operation, when it starts.
        #   If the user wants to add new download.DownloadItem objects during
        #   an operation, the code can call
        #   downloads.DownloadList.create_item() with a non-default value of
        #   operation_type
        self.operation_type = operation_type
        # Shortcut flag to test the operation type; True for 'classic_sim',
        #   'classic_real' and 'classic_custom'; False for all other values
        self.operation_classic_flag = False         # (Set below)

        # The time at which the download operation began (in seconds since
        #   epoch)
        self.start_time = int(time.time())
        # The time at which the download operation completed (in seconds since
        #   epoch)
        self.stop_time = None
        # The time (in seconds) between iterations of the loop in self.run()
        self.sleep_time = 0.25

        # Flag set to False if self.stop_download_operation() is called
        # The False value halts the main loop in self.run()
        self.running_flag = True
        # Flag set to True if the operation has been stopped manually by the
        #   user (via a call to self.stop_download_operation() or
        #   .stop_download_operation_soon()
        self.manual_stop_flag = False

        # Number of download jobs started (number of downloads.DownloadItem
        #   objects which have been allocated to a worker)
        self.job_count = 0
        # The current downloads.DownloadItem being handled by self.run()
        #   (stored in this IV so that anything can update the main window's
        #   progress bar, at any time, by calling self.nudge_progress_bar() )
        self.current_item_obj = None

        # On-going counts of how many videos have been downloaded (real and
        #   simulated, and including videos from which one or more clips have
        #   been extracted), how many clips have been extracted, how many video
        #   slices have been removed, and how much disc space has been consumed
        #   (in bytes), so that the operation can be auto-stopped, if required
        self.total_video_count = 0
        self.total_dl_count = 0
        self.total_sim_count = 0
        self.total_clip_count = 0
        self.total_slice_count = 0
        self.total_size_count = 0
        # Special count for media.Video objects which have already been
        #   checked/downloaded, and are being checked again (directly, for
        #   example after right-clicking the video)
        # If non-zero, prevents mainwin.NewbieDialogue from opening
        self.other_video_count = 0

        # If mainapp.TartubeApp.operation_convert_mode is set to any value
        #   other than 'disable', then a media.Video object whose URL
        #   represents a channel/playlist is converted into multiple new
        #   media.Video objects, one for each video actually downloaded
        # The original media.Video object is added to this list, via a call to
        #   self.mark_video_as_doomed(). At the end of the whole download
        #   operation, any media.Video object in this list is destroyed
        self.doomed_video_list = []

        # When the self.operation_type is 'classic_sim', we just compile a list
        #   of all videos detected. (A single URL may produce multiple videos)
        # A second download operation is due to be launched when this one
        #   finishes, with self.operation_type set to 'classic_custom'. During
        #   that operation, each of these video will be downloaded individually
        # The list is in groups of two, in the form
        #   [ parent_obj, json_dict ]
        # ...where 'parent_obj' is a 'dummy' media.Video object representing a
        #   video, channel or playlist, from which the metedata for a single
        #   video, 'json_dict', has been extracted
        self.classic_extract_list = []

        # Flag set to True when alternative performance limits currently apply,
        #   False when not. By checking the previous value (stored here)
        #   against the new one, we can see whether the period of alternative
        #   limits has started (or stopped)
        self.alt_limits_flag = self.check_alt_limits()
        # Alternative limits are checked every five minutes. The time (in
        #   minutes past the hour) at which the next check should be performed
        self.alt_limits_check_time = None


        # Code
        # ----

        # Set the flag
        if operation_type == 'classic_sim' \
        or operation_type == 'classic_real' \
        or operation_type == 'classic_custom':
            self.operation_classic_flag = True

        # Create an object for converting download options stored in
        #   downloads.DownloadWorker.options_list into a list of youtube-dl
        #   command line options
        self.options_parser_obj = options.OptionsParser(self.app_obj)

        # Create a list of downloads.DownloadWorker objects, each one handling
        #   one of several simultaneous downloads
        # Note that if a downloads.DownloadItem was created by a
        #   media.Scheduled object that specifies more (or fewer) workers,
        #   then self.change_worker_count() will be called
        if self.alt_limits_flag:
            worker_count = self.app_obj.alt_num_worker
        elif self.app_obj.num_worker_apply_flag:
            worker_count = self.app_obj.num_worker_default
        else:
            worker_count = self.app_obj.num_worker_max

        for i in range(1, worker_count + 1):
            self.worker_list.append(DownloadWorker(self))

        # Set the time at which the first check for alternative limits is
        #   performed
        local = utils.get_local_time()
        self.alt_limits_check_time \
        = (int(int(local.strftime('%M')) / 5) * 5) + 5
        if self.alt_limits_check_time > 55:
            self.alt_limits_check_time = 0
        # (Also update the icon in the Progress tab)
        self.app_obj.main_win_obj.toggle_alt_limits_image(self.alt_limits_flag)

        # Let's get this party started!
        self.start()


    # Public class methods


    def run(self):

        """Called as a result of self.__init__().

        On a continuous loop, passes downloads.DownloadItem objects to each
        downloads.DownloadWorker object, as they become available, until the
        download operation is complete.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 254 run')

        manager_string = _('D/L Manager:') + '   '

        self.app_obj.main_win_obj.output_tab_write_stdout(
            0,
            manager_string + _('Starting download operation'),
        )

        # (Monitor changes to the number of workers, and number of available
        #   workers, so that we can display a running total in the Output tab's
        #   summary page)
        local_worker_available_count = 0
        local_worker_total_count = 0

        # Perform the download operation until there is nothing left to
        #   download, or until something has called
        #   self.stop_download_operation()
        while self.running_flag:

            # Send a message to the Output tab's summary page, if required.
            #   The number of workers shown doesn't include those dedicated to
            #   broadcasting livestreams
            available_count = 0
            total_count = 0
            for worker_obj in self.worker_list:
                if not worker_obj.broadcast_flag:
                    total_count += 1
                    if worker_obj.available_flag:
                        available_count += 1

            if local_worker_available_count != available_count \
            or local_worker_total_count != total_count:
                local_worker_available_count = available_count
                local_worker_total_count = total_count
                self.app_obj.main_win_obj.output_tab_write_stdout(
                    0,
                    manager_string + _('Workers: available:') + ' ' \
                    + str(available_count) + ', ' + _('total:') + ' ' \
                    + str(total_count),
                )

            # Auto-stop the download operation, if required
            if self.app_obj.autostop_time_flag:

                # Calculate the current time limit, in seconds
                time_limit = self.app_obj.autostop_time_value \
                * formats.TIME_METRIC_DICT[self.app_obj.autostop_time_unit]

                if (time.time() - self.start_time) > time_limit:
                    break

            # Every five minutes, check whether the period of alternative
            #   performance limits has started (or stopped)
            local = utils.get_local_time()
            if int(local.strftime('%M')) >= self.alt_limits_check_time:

                self.alt_limits_check_time += 5
                if self.alt_limits_check_time > 55:
                    self.alt_limits_check_time = 0

                new_flag = self.check_alt_limits()
                if new_flag != self.alt_limits_flag:

                    self.alt_limits_flag = new_flag
                    if not new_flag:

                        self.app_obj.main_win_obj.output_tab_write_stdout(
                            0,
                            _(
                            'Alternative performance limits no longer apply',
                            ),
                        )

                    else:

                        self.app_obj.main_win_obj.output_tab_write_stdout(
                            0,
                            _('Alternative performance limits now apply'),
                        )

                    # Change the number of workers. Bandwidth changes are
                    #   applied by OptionsParser.build_limit_rate()
                    if self.app_obj.num_worker_default \
                    != self.app_obj.alt_num_worker:

                        if not new_flag:

                            self.change_worker_count(
                                self.app_obj.num_worker_default,
                            )

                        else:

                            self.change_worker_count(
                                self.app_obj.alt_num_worker,
                            )

                    # (Also update the icon in the Progress tab)
                    self.app_obj.main_win_obj.toggle_alt_limits_image(
                        self.alt_limits_flag,
                    )

            # Fetch information about the next media data object to be
            #   downloaded (and store it in an IV, so the main window's
            #   progress bar can be updated at any time, by any code)
            self.current_item_obj = self.download_list_obj.fetch_next_item()

            # Exit this loop when there are no more downloads.DownloadItem
            #   objects whose .status is formats.MAIN_STAGE_QUEUED, and when
            #   all workers have finished their downloads
            # Otherwise, wait for an available downloads.DownloadWorker, and
            #   then assign the next downloads.DownloadItem to it
            if not self.current_item_obj:
                if self.check_workers_all_finished():

                    # Send a message to the Output tab's summary page
                    self.app_obj.main_win_obj.output_tab_write_stdout(
                        0,
                        manager_string + _('All threads finished'),
                    )

                    break

            else:
                worker_obj = self.get_available_worker(
                    self.current_item_obj.media_data_obj,
                )

                # If the worker has been marked as doomed (because the number
                #   of simultaneous downloads allowed has decreased) then we
                #   can destroy it now
                if worker_obj and worker_obj.doomed_flag:

                    worker_obj.close()
                    self.remove_worker(worker_obj)

                # Otherwise, initialise the worker's IVs for the next job
                elif worker_obj:

                    # Send a message to the Output tab's summary page
                    self.app_obj.main_win_obj.output_tab_write_stdout(
                        0,
                        _('Thread #') + str(worker_obj.worker_id) \
                        + ': ' + _('Downloading:') + ' \'' \
                        + self.current_item_obj.media_data_obj.name + '\'',
                    )

                    # Initialise IVs
                    worker_obj.prepare_download(self.current_item_obj)
                    # Change the download stage for that downloads.DownloadItem
                    self.download_list_obj.change_item_stage(
                        self.current_item_obj.item_id,
                        formats.MAIN_STAGE_ACTIVE,
                    )
                    # Update the main window's progress bar (but not for
                    #   workers dedicated to broadcasting livestreams)
                    if not worker_obj.broadcast_flag:
                        self.job_count += 1

                    # Throughout the downloads.py code, instead of calling a
                    #   mainapp.py or mainwin.py function directly (which is
                    #   not thread-safe), set a Glib timeout to handle it
                    if not self.operation_classic_flag:
                        self.nudge_progress_bar()

            # Pause a moment, before the next iteration of the loop (don't want
            #   to hog resources)
            time.sleep(self.sleep_time)

        # Download operation complete (or has been stopped). Send messages to
        #   the Output tab's summary page
        self.app_obj.main_win_obj.output_tab_write_stdout(
            0,
            manager_string + _('Downloads complete (or stopped)'),
        )

        # Close all the workers
        self.app_obj.main_win_obj.output_tab_write_stdout(
            0,
            manager_string + _('Halting all workers'),
        )

        for worker_obj in self.worker_list:
            worker_obj.close()

        # Join and collect
        self.app_obj.main_win_obj.output_tab_write_stdout(
            0,
            manager_string + _('Join and collect threads'),
        )

        for worker_obj in self.worker_list:
            worker_obj.join()

        self.app_obj.main_win_obj.output_tab_write_stdout(
            0,
            manager_string + _('Operation complete'),
        )

        # Set the stop time
        self.stop_time = int(time.time())

        # Tell the Progress List (or Classic Progress List) to display any
        #   remaining download statistics immediately
        if not self.operation_classic_flag:

            GObject.timeout_add(
                0,
                self.app_obj.main_win_obj.progress_list_display_dl_stats,
            )

        else:

            GObject.timeout_add(
                0,
                self.app_obj.main_win_obj.classic_mode_tab_display_dl_stats,
            )

        # Tell the Output tab to display any remaining messages immediately
        GObject.timeout_add(
            0,
            self.app_obj.main_win_obj.output_tab_update_pages,
        )

        # Any media.Video objects which have been marked as doomed, can now be
        #   destroyed
        for video_obj in self.doomed_video_list:
            self.app_obj.delete_video(
                video_obj,
                True,           # Delete any files associated with the video
                True,           # Don't update the Video Index yet
                True,           # Don't update the Video Catalogue yet
            )

        # (Also update the icon in the Progress tab)
        self.app_obj.main_win_obj.toggle_alt_limits_image(False)

        # When youtube-dl reports it is finished, there is a short delay before
        #   the final downloaded video(s) actually exist in the filesystem
        # Therefore, mainwin.MainWin.progress_list_display_dl_stats() may not
        #   have marked the final video(s) as downloaded yet
        # Let the timer run for a few more seconds to allow those videos to be
        #   marked as downloaded (we can stop before that, if all the videos
        #   have been already marked)
        if not self.operation_classic_flag:

            GObject.timeout_add(
                0,
                self.app_obj.download_manager_halt_timer,
            )

        else:

            # For download operations launched from the Classic Mode tab, we
            #   don't need to wait at all
            GObject.timeout_add(
                0,
                self.app_obj.download_manager_finished,
            )


    def apply_ignore_limits(self):

        """Called by mainapp>TartubeApp.script_slow_timer_callback(), after
        starting a download operation to check/download everything.

        One of the media.Scheduled objects specified that operation limits
        should be ignored, so apply that setting to everything in the download
        list.

        (Doing things this way is a lot simpler than the alternatives.)
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 475 apply_ignore_limits')

        for item_id in self.download_list_obj.download_item_list:

            download_item_obj \
            = self.download_list_obj.download_item_dict[item_id]
            download_item_obj.set_ignore_limits_flag()


    def check_alt_limits(self):

        """Called by self.__init__() and .run().

        Checks whether alternative performance limits apply right now, or not.

        Returns:

            True if alternative limits apply, False if not

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 475 check_alt_limits')

        if not self.app_obj.alt_num_worker_apply_flag:
            return False

        # Get the current time and day of the week
        local = utils.get_local_time()
        current_hours = int(local.strftime('%H'))
        current_minutes = int(local.strftime('%M'))
        # 0=Monday, 6=Sunday
        current_day = local.today().weekday()

        # The period of alternative performance limits have a start and stop
        #   time, stored as strings in the form '21:00'
        start_hours = int(self.app_obj.alt_start_time[0:2])
        start_minutes = int(self.app_obj.alt_start_time[3:5])
        stop_hours = int(self.app_obj.alt_stop_time[0:2])
        stop_minutes = int(self.app_obj.alt_stop_time[3:5])

        # Is the current time before or after the start/stop times?
        if current_hours < start_hours \
        or (current_hours == start_hours and current_minutes < start_minutes):
            start_before_flag = True
        else:
            start_before_flag = False

        if current_hours < stop_hours \
        or (current_hours == stop_hours and current_minutes < stop_minutes):
            stop_before_flag = True
        else:
            stop_before_flag = False

        # If the start time is earlier than the stop time, we assume they're on
        #   the same day
        if start_hours < stop_hours \
        or (start_hours == stop_hours and start_minutes < stop_minutes):

            if not self.check_alt_limits_day(current_day) \
            or start_before_flag \
            or (not stop_before_flag):
                return False
            else:
                return True

        # Otherwise, we assume the stop time occurs the following day (e.g.
        #   21:00 to 07:00)
        else:

            prev_day = current_day - 1
            if prev_day < 0:
                prev_day = 6

            if (
                self.check_alt_limits_day(current_day) \
                and (not start_before_flag)
            ) or (
                self.check_alt_limits_day(prev_day) \
                and stop_before_flag
            ):
                return True
            else:
                return False


    def check_alt_limits_day(self, this_day):

        """Called by self.check_alt_limits().

        Test the day(s) of the week on which alternative limits apply. The
        specified day(s) are stored as a string in the form 'every_day',
        'weekdays', 'weekends', or 'monday', 'tuesday' etc.

        Returns:

            True if the alternative limits apply today, False if not

        """

        # Test the day(s) of the week on which alterative limits apply. The
        #   specified day(s) are stored as a string in the form 'every_day',
        #   'weekdays', 'weekends', or 'monday', 'tuesday' etc.
        day_str = self.app_obj.alt_day_string
        if day_str != 'every_day':

            if (day_str == 'weekdays' and this_day > 4) \
            or (day_str == 'weekends' and this_day < 5) \
            or (day_str == 'monday' and this_day != 0) \
            or (day_str == 'tuesday' and this_day != 1) \
            or (day_str == 'wednesday' and this_day != 2) \
            or (day_str == 'thursday' and this_day != 3) \
            or (day_str == 'friday' and this_day != 4) \
            or (day_str == 'saturday' and this_day != 5) \
            or (day_str == 'sunday' and this_day != 6):
                return False

        return True


    def change_worker_count(self, number):

        """Called by mainapp.TartubeApp.set_num_worker_default(). Can also be
        called by self.run() when the period of alternative performances limits
        begins or ends.

        When the number of simultaneous downloads allowed is changed during a
        download operation, this function responds.

        If the number has increased, creates an extra download worker object.

        If the number has decreased, marks the worker as doomed. When its
        current download is completed, the download manager destroys it.

        Args:

            number (int): The new number of simultaneous downloads allowed

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 504 change_worker_count')

        # How many workers do we have already?
        current = len(self.worker_list)
        # If this object hasn't set up its worker pool yet, let the setup code
        #   proceed as normal
        # Sanity check: if the specified value is less than 1, or hasn't
        #   changed, take no action
        if not current or number < 1 or current == number:
            return

        # Usually, the number of workers goes up or down by one at a time, but
        #   we'll check for larger leaps anyway
        for i in range(1, (abs(current-number) + 1)):

            if number > current:

                # The number has increased. If any workers have marked as
                #   doomed, they can be unmarked, allowing them to continue
                match_flag = False

                for worker_obj in self.worker_list:
                    if worker_obj.doomed_flag:
                        worker_obj.set_doomed_flag(True)
                        match_flag = True
                        break

                if not match_flag:
                    # No workers were marked doomed, so create a brand new
                    #   download worker
                    self.worker_list.append(DownloadWorker(self))

            else:

                # The number has decreased. The first worker in the list is
                #   marked as doomed - that is, when it has finished its
                #   current job, it closes (rather than being given another
                #   job, as usual)
                for worker_obj in self.worker_list:
                    if not worker_obj.doomed_flag:
                        worker_obj.set_doomed_flag(True)
                        break


    def check_master_slave(self, media_data_obj):

        """Called by VideoDownloader.do_download().

        When two channels/playlists/folders share a download destination, we
        don't want to download both of them at the same time.

        This function is called when media_data_obj is about to be
        downloaded.

        Every worker is checked, to see if it's downloading to the same
        destination. If so, this function returns True, and
        VideoDownloader.do_download() waits a few seconds, before trying
        again.

        Otherwise, this function returns False, and
        VideoDownloader.do_download() is free to start its download.

        Args:

            media_data_obj (media.Channel, media.Playlist, media.Folder):
                The media data object that the calling function wants to
                download

        Returns:

            True or False, as described above

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 579 check_master_slave')

        for worker_obj in self.worker_list:

            if not worker_obj.available_flag \
            and worker_obj.download_item_obj:

                other_obj = worker_obj.download_item_obj.media_data_obj

                if other_obj.dbid != media_data_obj.dbid:

                    if (
                        not isinstance(other_obj, media.Video)
                        and other_obj.external_dir is not None
                    ):
                        if other_obj.external_dir \
                        == media_data_obj.external_dir:
                            return True

                    # (Alternative download destinations only apply when no
                    #   external directory is specified)
                    elif other_obj.dbid == media_data_obj.master_dbid:
                        return True

        return False


    def check_workers_all_finished(self):

        """Called by self.run().

        Based on DownloadManager._jobs_done().

        Returns:

            True if all downloads.DownloadWorker objects have finished their
                jobs, otherwise returns False

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 609 check_workers_all_finished')

        for worker_obj in self.worker_list:
            if not worker_obj.available_flag:
                return False

        return True


    def create_bypass_worker(self):

        """Called by downloads.DownloadList.create_item().

        For a broadcasting livestream, we create additional workers if
        required, possibly bypassing the limit specified by
        mainapp.TartubeApp.num_worker_default.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 628 create_bypass_worker')

        # How many workers do we have already?
        current = len(self.worker_list)
        # If this object hasn't set up its worker pool yet, let the setup code
        #   proceed as normal
        if not current:
            return

        # If we don't already have the maximum number of workers (or if no
        #   limit currently applies), then we don't need to create any more
        if not self.app_obj.num_worker_apply_flag \
        or current < self.app_obj.num_worker_default:
            return

        # Check the existing workers, in case one is already available
        for worker_obj in self.worker_list:
            if worker_obj.available_flag:
                return

        # Bypass the worker limit to create an additional worker, to be used
        #   only for broadcasting livestreams
        self.worker_list.append(DownloadWorker(self, True))
        # Create an additional page in the main window's Output tab, if
        #   required
        self.app_obj.main_win_obj.output_tab_setup_pages()


    def get_available_worker(self, media_data_obj):

        """Called by self.run().

        Based on DownloadManager._get_worker().

        Args:

            media_data_obj (media.Video, media.Channel, media.Playlist or
                media.Folder): The media data object which is the next to be
                downloaded

        Returns:

            The first available downloads.DownloadWorker, or None if there are
                no available workers

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 676 get_available_worker')

        # Some workers are only available when media_data_obj is media.Video
        #   that's a broadcasting livestream
        if isinstance(media_data_obj, media.Video) \
        and media_data_obj.live_mode == 2:
            broadcast_flag = True
        else:
            broadcast_flag = False

        for worker_obj in self.worker_list:

            if worker_obj.available_flag \
            and (broadcast_flag or not worker_obj.broadcast_flag):
                return worker_obj

        return None


    def mark_video_as_doomed(self, video_obj):

        """Called by VideoDownloader.check_dl_is_correct_type().

        When youtube-dl reports the URL associated with a download item
        object contains multiple videos (or potentially contains multiple
        videos), then the URL represents a channel or playlist, not a video.

        If the channel/playlist was about to be downloaded into a media.Video
        object, then the calling function takes action to prevent it.

        It then calls this function to mark the old media.Video object to be
        destroyed, once the download operation is complete.

        Args:

            video_obj (media.Video): The video object whose URL is not a video,
                and which must be destroyed

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 717 mark_video_as_doomed')

        if isinstance(video_obj, media.Video) \
        and not video_obj in self.doomed_video_list:
            self.doomed_video_list.append(video_obj)


    def nudge_progress_bar (self):

        """Can be called by anything.

        Called by self.run() during the download operation.

        Also called by code in other files, just after that code adds a new
        media data object to our download list.

        Updates the main window's progress bar.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 737 nudge_progress_bar')

        if self.current_item_obj:

            GObject.timeout_add(
                0,
                self.app_obj.main_win_obj.update_progress_bar,
                self.current_item_obj.media_data_obj.name,
                self.job_count,
                    len(self.download_list_obj.download_item_list),
            )


    def register_classic_url(self, parent_obj, json_dict):

        """Called by VideoDownloader.extract_stdout_data().

        When the self.operation_type is 'classic_sim', we just compile a list
        of all videos detected.  (A single URL may produce multiple videos).

        A second download operation is due to be launched when this one
        finishes, with self.operation_type set to 'classic_custom'. During that
        operation, each of these URLs will be downloaded individually.

        Args:

            parent_obj (media.Video, media.Channel, media.Playlist): The
                media data object from which the URL was extracted

            json_dict (dict): Metadata extracted from a single video,
                stored as a dictionary

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 771 register_classic_url')

        self.classic_extract_list.append(parent_obj)
        self.classic_extract_list.append(json_dict)


    def register_clip(self):

        """Called by ClipDownloader.confirm_video().

        A shorter version of self.register_video(). Clips do not count
        towards video limits, but we still keep track of them.

        When all of the clips for a video have been extracted, a further call
        to self.register_video() must be made.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 797 register_clip')

        self.total_clip_count += 1


    def register_slice(self):

        """Called by ClipDownloader.do_download_remove_slices().

        A shorter version of self.register_video(). Video slices removed from
        videos do not count towards video limits, but we still keep track of
        them.

        When all of the video sliceshave been removed, a further call to
        self.register_video() must be made.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 797 register_slice')

        self.total_slice_count += 1


    def register_video(self, dl_type):

        """Called by VideoDownloader.confirm_new_video(), when a video is
        downloaded, or by .confirm_sim_video(), when a simulated download finds
        a new video.

        Can also be called by .confirm_old_video() when downloading from the
        Classic Mode tab.

        Furthermore, called by ClipDownloader.do_download() when all clips for
        a video have been extracted, at least one of them successfully.

        This function adds the new video to its ongoing total and, if a limit
        has been reached, stops the download operation.

        Args:

            dl_type (str): 'new', 'sim', 'old', 'clip' or 'other', depending on
                the calling function

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 797 register_video')

        if dl_type == 'other':
            # Special count for already checked/downloaded media.Videos, in
            #   order to prevent mainwin.NewbieDialogue opening
            self.other_video_count += 1

        else:
            self.total_video_count += 1
            if dl_type == 'new':
                self.total_dl_count += 1
            elif dl_type == 'sim':
                self.total_sim_count += 1

            if self.app_obj.autostop_videos_flag \
            and self.total_video_count >= self.app_obj.autostop_videos_value:
                self.stop_download_operation()


    def register_video_size(self, size=None):

        """Called by mainapp.TartubeApp.update_video_when_file_found().

        Called with the size of a video that's just been downloaded. This
        function adds the size to its ongoing total and, if a limit has been
        reached, stops the download operation.

        Args:

            size (int): The size of the downloaded video (in bytes)

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 825 register_video_size')

        # (In case the filesystem didn't detect the file size, for whatever
        #   reason, we'll check for a None value)
        if size is not None:

            self.total_size_count += size

            if self.app_obj.autostop_size_flag:

                # Calculate the current limit
                limit = self.app_obj.autostop_size_value \
                * formats.FILESIZE_METRIC_DICT[self.app_obj.autostop_size_unit]

                if self.total_size_count >= limit:
                    self.stop_download_operation()


    def remove_worker(self, worker_obj):

        """Called by self.run().

        When a worker marked as doomed has completed its download job, this
        function is called to remove it from self.worker_list.

        Args:

            worker_obj (downloads.DownloadWorker): The worker object to remove

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 857 remove_worker')

        new_list = []

        for other_obj in self.worker_list:
            if other_obj != worker_obj:
                new_list.append(other_obj)

        self.worker_list = new_list


    def stop_download_operation(self):

        """Called by mainapp.TartubeApp.do_shutdown(), .stop_continue(),
        .dl_timer_callback(), .on_button_stop_operation().

        Also called by mainwin.StatusIcon.on_stop_menu_item().

        Also called by self.register_video() and .register_video_size().

        Based on DownloadManager.stop_downloads().

        Stops the download operation. On the next iteration of self.run()'s
        loop, the downloads.DownloadWorker objects are cleaned up.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 884 stop_download_operation')

        self.running_flag = False
        self.manual_stop_flag = True

        # In the Progress List, change the status of remaining items from
        #   'Waiting' to 'Not started'
        self.download_list_obj.abandon_remaining_items()


    def stop_download_operation_soon(self):

        """Called by mainwin.MainWin.on_progress_list_stop_all_soon(), after
        the user clicks the 'Stop after these videos' option in the Progress
        List.

        Stops the download operation, but only after any videos which are
        currently being downloaded have finished downloading.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 900 stop_download_operation_soon')

        self.manual_stop_flag = True

        self.download_list_obj.prevent_fetch_new_items()
        for worker_obj in self.worker_list:
            if worker_obj.running_flag:
                worker_obj.downloader_obj.stop_soon()

        # In the Progress List, change the status of remaining items from
        #   'Waiting' to 'Not started'
        self.download_list_obj.abandon_remaining_items()


class DownloadWorker(threading.Thread):

    """Called by downloads.DownloadManager.__init__().

    Based on the Worker class in youtube-dl-gui.

    Python class for managing simultaneous downloads. The parent
    downloads.DownloadManager object can create one or more workers, each of
    which handles a single download.

    The download manager runs on a loop, looking for available workers and,
    when one is found, assigns them something to download.

    After the download is completely, the worker optionally checks a channel's
    or a playlist's RSS feed, looking for livestreams.

    When all tasks are completed, the worker waits for another assignment.

    Args:

        download_manager_obj (downloads.DownloadManager): The parent download
            manager object

        broadcast_flag (bool): True if this worker has been created
            specifically to handle broadcasting livestreams (see comments
            below); False if not

    """


    # Standard class methods


    def __init__(self, download_manager_obj, broadcast_flag=False):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 944 __init__')

        super(DownloadWorker, self).__init__()

        # IV list - class objects
        # -----------------------
        # The parent downloads.DownloadManager object
        self.download_manager_obj = download_manager_obj
        # The downloads.DownloadItem object for the current job
        self.download_item_obj = None
        # The downloads.VideoDownloader, downloads.ClipDownloader or
        #   downloads.StreamDownloader object for the current job (if it
        #   exists)
        self.downloader_obj = None
        # The downloads.JSONFetcher object for the current job (if it exists)
        self.json_fetcher_obj = None
        # The options.OptionsManager object for the current job
        self.options_manager_obj = None


        # IV list - other
        # ---------------
        # A number identifying this worker, matching the number of the page
        #   in the Output tab (so the first worker created is #1)
        self.worker_id = len(download_manager_obj.worker_list) + 1

        # The time (in seconds) between iterations of the loop in self.run()
        self.sleep_time = 0.25

        # Flag set to False if self.close() is called
        # The False value halts the main loop in self.run()
        self.running_flag = True
        # Flag set to True when the parent downloads.DownloadManager object
        #   wants to destroy this worker, having called self.set_doomed_flag()
        #   to do that
        # The worker is not destroyed until its current download is complete
        self.doomed_flag = False
        # Downloads of broadcasting livestreams must start as soon as possible.
        #   If the worker limit (mainapp.TartubeApp.num_worker_default) has
        #   been reached, additional workers are created to handle them
        # If True, this worker can only be used for broadcasting livestreams.
        #   If False, it can be used for anything
        self.broadcast_flag = broadcast_flag

        # Options list (used by downloads.VideoDownloader)
        # Initialised in the call to self.prepare_download()
        self.options_list = []
        # Flag set to True when the worker is available for a new job, False
        #   when it is already occupied with a job
        self.available_flag = True


        # Code
        # ----

        # Let's get this party started!
        self.start()


    # Public class methods


    def run(self):

        """Called as a result of self.__init__().

        Waits until this worker has been assigned a job, at which time we
        create a new downloads.VideoDownloader or downloads.StreamDownloader
        object and wait for the result.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 1015 run')

        # Import the main application and custom download manager (for
        #   convenience)
        app_obj = self.download_manager_obj.app_obj
        custom_dl_obj = self.download_manager_obj.custom_dl_obj

        # Handle a job, or wait for the downloads.DownloadManager to assign
        #   this worker a job
        while self.running_flag:

            # If this worker is currently assigned a job...
            if not self.available_flag:

                # Import the media data object (for convenience)
                media_data_obj = self.download_item_obj.media_data_obj

                # If the downloads.DownloadItem was created by a scheduled
                #   download (media.Scheduled), then change the number of
                #   workers, if necessary
                if self.download_item_obj.scheduled_obj:

                    scheduled_obj = self.download_item_obj.scheduled_obj
                    if scheduled_obj.scheduled_num_worker_apply_flag \
                    and scheduled_obj.scheduled_num_worker \
                    != len(self.download_manager_obj.worker_list):

                        self.download_manager_obj.change_worker_count(
                            scheduled_obj.scheduled_num_worker,
                        )

                # When downloading a livestream that's broadcasting now, we
                #   can use Youtube Stream Capture
                # When downloading video clips, use youtube-dl with FFmpeg as
                #   its external downloader
                # Otherwise, use youtube-dl with an argument list determined by
                #   the download options applied
                if app_obj.ytsc_priority_flag \
                and isinstance(media_data_obj, media.Video) \
                and not media_data_obj.dummy_flag \
                and self.download_item_obj.operation_type != 'sim' \
                and self.download_item_obj.operation_type != 'custom_sim' \
                and self.download_item_obj.operation_type != 'classic_sim' \
                and media_data_obj.live_mode == 2 \
                and utils.is_youtube(media_data_obj.source):
                    self.run_stream_downloader(media_data_obj)

                elif isinstance(media_data_obj, media.Video) \
                and not media_data_obj.live_mode \
                and (
                    self.download_item_obj.operation_type == 'custom_real' \
                    or self.download_item_obj.operation_type \
                    == 'classic_custom'
                ) and (
                    (
                        custom_dl_obj \
                        and custom_dl_obj.dl_by_video_flag \
                        and custom_dl_obj.split_flag
                        and media_data_obj.stamp_list
                    ) or (
                        custom_dl_obj \
                        and custom_dl_obj.dl_by_video_flag \
                        and not custom_dl_obj.split_flag \
                        and custom_dl_obj.slice_flag
                        and media_data_obj.slice_list
                    ) or app_obj.temp_stamp_list \
                    or app_obj.temp_slice_list
                ):
                    self.run_clip_slice_downloader(media_data_obj)

                else:
                    self.run_video_downloader(media_data_obj)

                # Send a message to the Output tab's summary page
                app_obj.main_win_obj.output_tab_write_stdout(
                    0,
                    _('Thread #') + str(self.worker_id) \
                    + ': ' + _('Job complete') + ' \'' \
                    + self.download_item_obj.media_data_obj.name + '\'',
                )

                # This worker is now available for a new job
                self.available_flag = True

                # Send a message to the Output tab's summary page
                app_obj.main_win_obj.output_tab_write_stdout(
                    0,
                    _('Thread #') + str(self.worker_id) \
                    + ': ' + _('Worker now available again'),
                )

                # During (real, not simulated) custom downloads, apply a delay
                #   if one has been specified
                if (
                    self.download_item_obj.operation_type == 'custom_real' \
                    or self.download_item_obj.operation_type \
                    == 'classic_custom'
                ) and custom_dl_obj \
                and custom_dl_obj.delay_flag:

                    # Set the delay (in seconds), a randomised value if
                    #   required
                    if custom_dl_obj.delay_min:
                        delay = random.randint(
                            int(custom_dl_obj.delay_min * 60),
                            int(custom_dl_obj.delay_max * 60),
                        )
                    else:
                        delay = int(custom_dl_obj.delay_max * 60)

                    time.sleep(delay)

            # Pause a moment, before the next iteration of the loop (don't want
            #   to hog resources)
            time.sleep(self.sleep_time)


    def run_video_downloader(self, media_data_obj):

        """Called by self.run()

        Creates a new downloads.VideoDownloader to handle the download(s) for
        this job, and destroys it when it's finished.

        If possible, checks the channel/playlist RSS feed for videos we don't
        already have, and mark them as livestreams

        Args:

            media_data_obj (media.Video, media.Channel, media.Playlist,
                media.Folder): The media data object being downloaded. When the
                download operation was launched from the Classic Mode tab, a
                dummy media.Video object

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 1107 run_video_downloader')

        # Import the main application (for convenience)
        app_obj = self.download_manager_obj.app_obj

        # If the download stalls, the VideoDownloader may need to be replaced
        #   with a new one. Use a while loop for that
        first_flag = True
        restart_count = 0

        while True:

            # Set up the new downloads.VideoDownloader object
            self.downloader_obj = VideoDownloader(
                self.download_manager_obj,
                self,
                self.download_item_obj,
            )

            if first_flag:

                first_flag = False
                # Send a message to the Output tab's summary page
                app_obj.main_win_obj.output_tab_write_stdout(
                    0,
                    _('Thread #') + str(self.worker_id) \
                    + ': ' + _('Assigned job:') + ' \'' \
                    + self.download_item_obj.media_data_obj.name \
                    + '\'',
                )

            # Execute the assigned job
            return_code = self.downloader_obj.do_download()

            # If the download stalled, -1 is returned. If we're allowed to
            #   restart a stalled download, do that; otherwise give up
            if return_code > -1 \
            or (
                app_obj.operation_auto_restart_max != 0
                and app_obj.operation_auto_restart_max >= restart_count
            ):
                break

            else:
                restart_count += 1

                # Show confirmation of the restart
                if app_obj.ytdl_output_stdout_flag:
                    app_obj.main_win_obj.output_tab_write_stdout(
                        self.download_worker_obj.worker_id,
                        _('Tartube is restarting a stalled download'),
                    )

                if app_obj.ytdl_write_stdout_flag:
                    print(_('Tartube is restarting a stalled download'))

        # If the downloads.VideoDownloader object collected any youtube-dl
        #   error/warning messages, display them in the Error List
        if media_data_obj.error_list or media_data_obj.warning_list:
            GObject.timeout_add(
                0,
                app_obj.main_win_obj.errors_list_add_row,
                media_data_obj,
            )

        # In the event of an error, nothing updates the video's row in the
        #   Video Catalogue, and therefore the error icon won't be visible
        # Do that now (but don't if mainwin.ComplexCatalogueItem objects aren't
        #   being used in the Video Catalogue)
        if not self.download_item_obj.operation_classic_flag \
        and return_code == VideoDownloader.ERROR \
        and isinstance(media_data_obj, media.Video) \
        and app_obj.catalogue_mode_type != 'simple':
            GObject.timeout_add(
                0,
                app_obj.main_win_obj.video_catalogue_update_video,
                media_data_obj,
            )

        # Call the destructor function of VideoDownloader object
        self.downloader_obj.close()

        # If possible, check the channel/playlist RSS feed for videos we don't
        #   already have, and mark them as livestreams
        if self.running_flag \
        and mainapp.HAVE_FEEDPARSER_FLAG \
        and app_obj.enable_livestreams_flag \
        and (
            isinstance(media_data_obj, media.Channel) \
            or isinstance(media_data_obj, media.Playlist)
        ) and not media_data_obj.dl_no_db_flag \
        and media_data_obj.child_list \
        and media_data_obj.rss:

            # Send a message to the Output tab's summary page
            app_obj.main_win_obj.output_tab_write_stdout(
                0,
                _('Thread #') + str(self.worker_id) \
                + ': ' + _('Checking RSS feed'),
            )

            # Check the RSS feed for the media data object
            self.check_rss(media_data_obj)


    def run_clip_slice_downloader(self, media_data_obj):

        """Called by self.run()

        Creates a new downloads.ClipDownloader to handle the download(s) for
        this job, and destroys it when it's finished.

        Args:

            media_data_obj (media.Video): The media data object being
                downloaded. When the download operation was launched from the
                Classic Mode tab, a dummy media.Video object

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 1107 run_clip_slice_downloader')

        # Import the main application and custom download manager (for
        #   convenience)
        app_obj = self.download_manager_obj.app_obj
        custom_dl_obj = self.download_manager_obj.custom_dl_obj

        # Set up the new downloads.ClipDownloader object
        self.downloader_obj = ClipDownloader(
            self.download_manager_obj,
            self,
            self.download_item_obj,
        )

        # Send a message to the Output tab's summary page
        app_obj.main_win_obj.output_tab_write_stdout(
            0,
            _('Thread #') + str(self.worker_id) \
            + ': ' + _('Assigned job:') + ' \'' \
            + self.download_item_obj.media_data_obj.name \
            + '\'',
        )

        # Execute the assigned job
        # ClipDownloader handles two related operations. Both start by
        #   downloading the video as clips. The second operation concatenates
        #   the clips back together, which has the effect of removing one or
        #   more slices from a video
        if (
            custom_dl_obj \
            and custom_dl_obj.split_flag \
            and media_data_obj.stamp_list
        ) or app_obj.temp_stamp_list:
            return_code = self.downloader_obj.do_download_clip()
        else:
            return_code = self.downloader_obj.do_download_remove_slices()

        # In the event of an error, nothing updates the video's row in the
        #   Video Catalogue, and therefore the error icon won't be visible
        # Do that now (but don't if mainwin.ComplexCatalogueItem objects aren't
        #   being used in the Video Catalogue)
        if not self.download_item_obj.operation_classic_flag \
        and return_code == ClipDownloader.ERROR \
        and app_obj.catalogue_mode_type != 'simple':
            GObject.timeout_add(
                0,
                app_obj.main_win_obj.video_catalogue_update_video,
                media_data_obj,
            )

        # Call the destructor function of ClipDownloader object
        self.downloader_obj.close()


    def run_stream_downloader(self, media_data_obj):

        """Called by self.run()

        A modified version of self.run_video_downloader(), used when
        downloading a media.Video object that's a livestream broadcasting now.
        In that case, we can use Youtube Stream Capture, rather than
        youtube-dl.

        Creates a new downloads.StreamDownloader to handle the download for
        this job, and destroys it when it's finished.

        Args:

            media_data_obj (media.Video): The media data object being
                downloaded

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 1210 run_stream_downloader')

        # Import the main application (for convenience)
        app_obj = self.download_manager_obj.app_obj

        # Set up the new downloads.StreamDownloader object
        self.downloader_obj = StreamDownloader(
            self.download_manager_obj,
            self,
            self.download_item_obj,
        )

        # Send a message to the Output tab's summary page
        app_obj.main_win_obj.output_tab_write_stdout(
            0,
            _('Thread #') + str(self.worker_id) \
            + ': ' + _('Assigned job:') + ' \'' \
            + self.download_item_obj.media_data_obj.name \
            + '\'',
        )

        # Execute the assigned job
        return_code = self.downloader_obj.do_capture()

        # In the event of an error, nothing updates the video's row in the
        #   Video Catalogue, and therefore the error icon won't be visible
        # Do that now (but don't if mainwin.ComplexCatalogueItem objects aren't
        #   being used in the Video Catalogue)
        if not self.download_item_obj.operation_classic_flag \
        and return_code == StreamDownloader.ERROR \
        and app_obj.catalogue_mode_type != 'simple':
            GObject.timeout_add(
                0,
                app_obj.main_win_obj.video_catalogue_update_video,
                media_data_obj,
            )

        # Call the destructor function of StreamDownloader object
        self.downloader_obj.close()


    def close(self):

        """Called by downloads.DownloadManager.run().

        This worker object is closed when:

            1. The download operation is complete (or has been stopped)
            2. The worker has been marked as doomed, and the calling function
                is now ready to destroy it

        Tidy up IVs and stop any child processes.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 1265 close')

        self.running_flag = False

        if self.downloader_obj:
            self.downloader_obj.stop()

        if self.json_fetcher_obj:
            self.json_fetcher_obj.stop()


    def check_rss(self, container_obj):

        """Called by self.run(), after the VideoDownloader has finished.

        If possible, check the channel/playlist RSS feed for videos we don't
        already have, and mark them as livestreams.

        This process works on YouTube (each media.Channel and media.Playlist
        has the URL for its RSS feed set automatically).

        It might work on other compatible websites (the user must set the
        channel's/playlist's RSS feed manually).

        On a compatible website, when youtube-dl fetches a list of videos in
        the channel/playlist, it won't fetch any that are livestreams (either
        waiting to start, or currently broadcasting).

        However, livestreams (both waiting and broadcasting) do appear in the
        RSS feed. We can compare the RSS feed against the channel's/playlist's
        list of child media.Video objects (which has just been updated), in
        order to detect livestreams (with reasonably good accuracy).

        Args:

            container_obj (media.Channel, media.Playlist): The channel or
                playlist which the VideoDownloader has just checked/downloaded.
                (This function is not called for media.Folders or for
                individual media.Video objects)

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 1308 check_rss')

        app_obj = self.download_manager_obj.app_obj

        # Livestreams are usually the first entry in the RSS feed, having not
        #   started yet (or being currently broadcast), but there's no
        #   gurantee of that
        # In addition, although RSS feeds are normally quite short (with
        #    dozens of entries, not thousands), there is no guarantee of this
        # mainapp.TartubeApp.livestream_max_days specifies how many days of
        #   videos we should check, looking for livestreams
        # Implement this by stopping when an entry in the RSS feed matches a
        #   particular media.Video object
        # (If we can't decide which video to match, the default to searching
        #   the whole RSS feed)
        time_limit_video_obj = None
        check_source_list = []

        if app_obj.livestream_max_days:

            # Stop checking the RSS feed at the first matching video that's
            #   older than the specified time
            # (Of course, the 'first video' must not itself be a livestream)
            older_time = int(
                time.time() - (app_obj.livestream_max_days * 86400),
            )

            for child_obj in container_obj.child_list:
                if child_obj.source:

                    # An entry in the RSS feed is a new livestream, if it
                    #   doesn't match one of the videos in this list
                    # (We don't need to check each RSS entry against the
                    #   entire contents of the channel/playlist - which might
                    #   be thousands of videos - just those up to the time
                    #   limit)
                    check_source_list.append(child_obj.source)

            # The time limit will apply to this video, when found
            for child_obj in container_obj.child_list:
                if child_obj.source \
                and not child_obj.live_mode \
                and child_obj.upload_time is not None \
                and child_obj.upload_time < older_time:
                    time_limit_video_obj = child_obj
                    break

        else:

            # Stop checking the RSS feed at the first matching video, no matter
            #   how old
            for child_obj in container_obj.child_list:
                if child_obj.source:
                    check_source_list.append(child_obj.source)

            for child_obj in container_obj.child_list:
                if child_obj.source \
                and not time_limit_video_obj \
                and not child_obj.live_mode:
                    time_limit_video_obj = child_obj
                    break

        # Fetch the RSS feed
        try:
            feed_dict = feedparser.parse(container_obj.rss)
        except:
            return

        # Check each entry in the feed, stopping at the first one which matches
        #   the selected media.Video object
        for entry_dict in feed_dict['entries']:

            if time_limit_video_obj \
            and entry_dict['link'] == time_limit_video_obj.source:

                # Found a matching media.Video object, so we can stop looking
                #   for livestreams now
                break

            elif not entry_dict['link'] in check_source_list:

                # New livestream detected. Create a new JSONFetcher object to
                #   fetch its JSON data
                # If the data is received, the livestream is live. If the data
                #   is not received, the livestream is waiting to go live
                self.json_fetcher_obj = JSONFetcher(
                    self.download_manager_obj,
                    self,
                    container_obj,
                    entry_dict,
                )

                # Then execute the assigned job
                self.json_fetcher_obj.do_fetch()

                # Call the destructor function of the JSONFetcher object
                self.json_fetcher_obj.close()
                self.json_fetcher_obj = None


    def prepare_download(self, download_item_obj):

        """Called by downloads.DownloadManager.run().

        Based on Worker.download().

        Updates IVs for a new job, so that self.run can initiate the download.

        Args:

            download_item_obj (downloads.DownloadItem): The download item
                object describing the URL from which youtube-dl should download
                video(s).

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 1425 prepare_download')

        self.download_item_obj = download_item_obj
        self.options_manager_obj = download_item_obj.options_manager_obj

        self.options_list = self.download_manager_obj.options_parser_obj.parse(
            self.download_item_obj.media_data_obj,
            self.options_manager_obj,
            self.download_item_obj.operation_type,
            self.download_item_obj.scheduled_obj,
        )

        self.available_flag = False


    def set_doomed_flag(self, flag):

        """Called by downloads.DownloadManager.change_worker_count()."""

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 1444 set_doomed_flag')

        self.doomed_flag = flag


    # Callback class methods


    def data_callback(self, dl_stat_dict, last_flag=False):

        """Called by downloads.VideoDownloader.do_download() and
        .last_data_callback().

        Based on Worker._data_hook() and ._talk_to_gui().

        'dl_stat_dict' holds a dictionary of statistics in a standard format
        specified by downloads.VideoDownloader.extract_stdout_data().

        This callback receives that dictionary and passes it on to the main
        window, so the statistics can be displayed there.

        Args:

            dl_stat_dict (dict): The dictionary of statistics described above

            last_flag (bool): True when called by .last_data_callback(),
                meaning that the VideoDownloader object has finished, and is
                sending this function the final set of statistics

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 1476 data_callback')

        main_win_obj = self.download_manager_obj.app_obj.main_win_obj

        if not self.download_item_obj.operation_classic_flag:

            GObject.timeout_add(
                0,
                main_win_obj.progress_list_receive_dl_stats,
                self.download_item_obj,
                dl_stat_dict,
                last_flag,
            )

            # If downloading a video individually, need to update the tooltips
            #   in the Results List to show any errors/warnings (which won't
            #   show up if the video was not downloaded)
            if last_flag \
            and isinstance(self.download_item_obj.media_data_obj, media.Video):

                GObject.timeout_add(
                    0,
                    main_win_obj.results_list_update_tooltip,
                    self.download_item_obj.media_data_obj,
                )

        else:

            GObject.timeout_add(
                0,
                main_win_obj.classic_mode_tab_receive_dl_stats,
                self.download_item_obj,
                dl_stat_dict,
                last_flag,
            )


class DownloadList(object):

    """Called by mainapp.TartubeApp.download_manager_continue().

    Based on the DownloadList class in youtube-dl-gui.

    Python class to keep track of all the media data objects to be downloaded
    (for real or in simulation) during a downloaded operation.

    This object contains an ordered list of downloads.DownloadItem objects.
    Each of those objects represents a media data object to be downloaded
    (media.Video, media.Channel, media.Playlist or media.Folder).

    Videos are downloaded in the order specified by the list.

    Args:

        app_obj (mainapp.TartubeApp): The main application

        operation_type (str): 'sim' if channels/playlists should just be
            checked for new videos, without downloading anything. 'real' if
            videos should be downloaded (or not) depending on each media data
            object's .dl_sim_flag IV

            'custom_real' is like 'real', but with additional options applied
            (specified by a downloads.CustomDLManager object). A 'custom_real'
            operation is sometimes preceded by a 'custom_sim' operation (which
            is the same as a 'sim' operation, except that it is always followed
            by a 'custom_real' operation)

            For downloads launched from the Classic Mode tab, 'classic_real'
            for an ordinary download, or 'classic_custom' for a custom
            download. A 'classic_custom' operation is always preceded by a
            'classic_sim' operation (which is the same as a 'sim' operation,
            except that it is always followed by a 'classic_custom' operation)

        media_data_list (list): List of media.Video, media.Channel,
            media.Playlist and/or media.Folder objects. Can also be a list of
            (exclusively) media.Scheduled objects. If not an empty list, only
            the specified media data objects (and their children) are
            checked/downloaded. If an empty list, all media data objects are
            checked/downloaded. If operation_type is 'classic', then the
            media_data_list contains a list of dummy media.Video objects from a
            previous call to this function. If an empty list, all
            dummy media.Video objects are downloaded

        custom_dl_obj (downloads.CustomDLManager or None): The custom download
            manager that applies to this download operation. Only specified
            when 'operation_type' is 'custom_sim', 'custom_real', 'classic_sim'
            or 'classic_real'

            For 'custom_real' and 'classic_real', not specified if
            mainapp.TartubeApp.temp_stamp_list or .temp_slice_list are
            specified (because those values take priority)

    """


    # Standard class methods


    def __init__(self, app_obj, operation_type, media_data_list, \
    custom_dl_obj):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 1552 __init__')

        # IV list - class objects
        # -----------------------
        self.app_obj = app_obj

        # The custom download manager (downloads.CustomDLManager) that applies
        #   to this download operation. Only specified when 'operation_type' is
        #   'custom_sim', 'custom_real', 'classic_sim' or 'classic_real'
        # For 'custom_real' and 'classic_real', not specified if
        #   mainapp.TartubeApp.temp_stamp_list or .temp_slice_list are
        #   specified (because those values take priority)
        self.custom_dl_obj = custom_dl_obj

        # IV list - other
        # ---------------
        # 'sim' if channels/playlists should just be checked for new videos,
        #   without downloading anything. 'real' if videos should be downloaded
        #   (or not) depending on each media data object's .dl_sim_flag IV
        # 'custom_real' is like 'real', but with additional options applied
        #   (specified by a downloads.CustomDLManager object). A 'custom_real'
        #   operation is sometimes preceded by a 'custom_sim' operation (which
        #   is the same as a 'sim' operation, except that it is always followed
        #   by a 'custom_real' operation)
        # For downloads launched from the Classic Mode tab, 'classic_real' for
        #   an ordinary download, or 'classic_custom' for a custom download. A
        #   'classic_custom' operation is always preceded by a 'classic_sim'
        #   operation (which is the same as a 'sim' operation, except that it
        #   is always followed by a 'classic_custom' operation)
        # This IV records the default setting for this operation. Once the
        #   download operation starts, new download.DownloadItem objects can
        #   be added to the list in a call to self.create_item(), and that call
        #   can specify a value that overrides the default value, just for that
        #   call
        # Overriding the default value is not possible for download operations
        #   initiated from the Classic Mode tab
        self.operation_type = operation_type
        # Shortcut flag to test the operation type; True for 'classic_sim',
        #   'classic_real' and 'classic_custom'; False forall other values
        self.operation_classic_flag = False         # (Set below)
        # Flag set to True in a call to self.prevent_fetch_new_items(), in
        #   which case subsequent calls to self.fetch_next_item() return
        #   nothing, preventing any further downloads
        self.prevent_fetch_flag = False

        # Number of download.DownloadItem objects created (used to give each a
        #   unique ID)
        self.download_item_count = 0

        # An ordered list of downloads.DownloadItem objects, one for each
        #   media.Video, media.Channel, media.Playlist or media.Folder object
        #   (including dummy media.Video objects used by download operations
        #   launched from the Classic Mode tab)
        # This list stores each item's .item_id
        self.download_item_list = []
        # A supplementary list of downloads.DownloadItem objects
        # Suppose self.download_item_list already contains items A B C, and
        #   some of part of the code wants to add items X Y Z to the beginning
        #   of the list, producing the list X Y Z A B C (and not Z Y X A B C)
        # The new items are added (one at a time) to this temporary list, and
        #   then added to the beginning/end of self.download_item_list at the
        #   end of this function (or in the next call to
        #   self.fetch_next_item() )
        self.temp_item_list = []

        # We preserve the 'media_data_list' argument (which may be an empty
        #   list). Used by mainapp.TartubeApp.download_manager_finished during
        #   a 'custom_sim' operation, in order to initiate the subsequent
        #   'custom_real' operation
        self.orig_media_data_list = media_data_list

        # Corresponding dictionary of downloads.DownloadItem items for quick
        #   lookup, containing items from both self.download_item_list and
        #   self.temp_item_list
        # Dictionary in the form
        #   key = download.DownloadItem.item_id
        #   value = the download.DownloadItem object itself
        self.download_item_dict = {}

        # Code
        # ----

        # Set the flag
        if operation_type == 'classic_sim' \
        or operation_type == 'classic_real' \
        or operation_type == 'classic_custom':
            self.operation_classic_flag = True

        # Compile the list

        # Scheduled downloads
        if media_data_list and isinstance(media_data_list[0], media.Scheduled):

            # media_data_list is a list of scheduled downloads
            all_obj = False
            ignore_limits_flag = False

            for scheduled_obj in media_data_list:
                if scheduled_obj.all_flag:
                    all_obj = scheduled_obj
                if scheduled_obj.ignore_limits_flag:
                    ignore_limits_flag = True
                if all_obj:
                    break


            if all_obj:

                # Use all media data objects
                for dbid in self.app_obj.media_top_level_list:
                    obj = self.app_obj.media_reg_dict[dbid]
                    self.create_item(
                        obj,
                        all_obj,    # media.Scheduled object
                        None,       # override_operation_type
                        False,      # priority_flag
                        ignore_limits_flag,
                    )

            else:

                # Use only media data objects specified by the media.Scheduled
                #   objects. Don't add the same media data object twice
                check_dict = {}

                for scheduled_obj in media_data_list:

                    if scheduled_obj.join_mode == 'priority':
                        priority_flag = True
                    else:
                        priority_flag = False

                    for name in scheduled_obj.media_list:
                        if not name in check_dict:

                            dbid = self.app_obj.media_name_dict[name]
                            obj = self.app_obj.media_reg_dict[dbid]

                            self.create_item(
                                obj,
                                scheduled_obj,
                                scheduled_obj.dl_mode,
                                priority_flag,
                                scheduled_obj.ignore_limits_flag,
                            )

                            check_dict[name] = None

        # Normal downloads
        elif not self.operation_classic_flag:

            # For each media data object to be downloaded, create a
            #   downloads.DownloadItem object, and update the IVs above
            if not media_data_list:

                # Use all media data objects
                for dbid in self.app_obj.media_top_level_list:
                    obj = self.app_obj.media_reg_dict[dbid]
                    self.create_item(
                        obj,
                        None,       # media.Scheduled object
                        None,       # override_operation_type
                        False,      # priority_flag
                        False,      # ignore_limits_flag
                    )

            else:

                for media_data_obj in media_data_list:

                    if isinstance(media_data_obj, media.Folder) \
                    and media_data_obj.priv_flag:

                        # Videos in a private folder's .child_list can't be
                        #   downloaded (since they are also a child of a
                        #   channel, playlist or a public folder)
                        GObject.timeout_add(
                            0,
                            app_obj.system_error,
                            301,
                            _('Cannot download videos in a private folder'),
                        )

                    else:

                        # Use the specified media data object
                        self.create_item(
                            media_data_obj,
                            None,       # media.Scheduled object
                            None,       # override_operation_type
                            False,      # priority_flag
                            False,      # ignore_limits_flag
                        )

            # Some media data objects have an alternate download destination,
            #   for example, a playlist ('slave') might download its videos
            #   into the directory used by a channel ('master')
            # This can increase the length of the operation, because a 'slave'
            #   won't start until its 'master' is finished
            # Make sure all designated 'masters' are handled before 'slaves' (a
            #   media data object can't be both a master and a slave)
            self.reorder_master_slave()

        # Downloads from the Classic Mode tab
        else:

            # The download operation was launched from the Classic Mode tab.
            #   Each URL to be downloaded is represented by a dummy media.Video
            #   object (one which is not in the media data registry)
            main_win_obj = self.app_obj.main_win_obj

            # The user may have rearranged rows in the Classic Mode tab, so
            #   get a list of (all) dummy media.Videos in the rearranged order
            # (It should be safe to assume that the Gtk.Liststore contains
            #   exactly the same number of rows, as dummy media.Video objects
            #   in mainwin.MainWin.classic_media_dict)
            dbid_list = []
            for row in main_win_obj.classic_progress_liststore:
                dbid_list.append(row[0])

            # Compile a list of dummy media.Video objects in the correct order
            obj_list = []
            if not media_data_list:

                # Use all of them
                for dbid in dbid_list:
                    obj_list.append(main_win_obj.classic_media_dict[dbid])

            else:

                # Use a subset of them
                for dbid in dbid_list:

                    dummy_obj = main_win_obj.classic_media_dict[dbid]
                    if dummy_obj in media_data_list:
                        obj_list.append(dummy_obj)


            # For each dummy media.Video object, create a
            #   downloads.DownloadItem object, and update the IVs above
            # Don't re-download a video already marked as downloaded (if the
            #   user actually wants to re-download a video, then
            #   mainapp.TartubeApp.on_button_classic_redownload() has reset the
            #   flag)
            for dummy_obj in obj_list:

                if not dummy_obj.dl_flag:
                    self.create_dummy_item(dummy_obj)

        # We can now merge the two DownloadItem lists
        if self.temp_item_list:

            self.download_item_list \
            = self.temp_item_list + self.download_item_list
            self.temp_item_list = []


    # Public class methods


    @synchronise(_SYNC_LOCK)
    def abandon_remaining_items(self):

        """Called by downloads.DownloadManager.stop_download_operation() and
        .stop_download_operation_soon().

        When the download operation has been stopped by the user, any rows in
        the main window's Progress List (or Classic Progress List) currently
        marked as 'Waiting' should be marked as 'Not started'.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 1800 abandon_remaining_items')

        main_win_obj = self.app_obj.main_win_obj
        download_manager_obj = self.app_obj.download_manager_obj

        # In case of any recent calls to self.create_item(), which want to
        #   place new DownloadItems at the beginning of the queue, then
        #   merge the temporary queue into the main one
        if self.temp_item_list:
            self.download_item_list \
            = self.temp_item_list + self.download_item_list

        # 'dl_stat_dict' holds a dictionary of statistics in a standard format
        #   specified by downloads.VideoDownloader.extract_stdout_data()
        # Prepare the dictionary to be passed on to the main window, so the
        #   statistics can be displayed there for every 'Waiting' item
        dl_stat_dict = {}
        dl_stat_dict['status'] = formats.MAIN_STAGE_NOT_STARTED

        for item_id in self.download_item_list:
            this_item = self.download_item_dict[item_id]

            if this_item.stage == formats.MAIN_STAGE_QUEUED:
                this_item.stage = formats.MAIN_STAGE_NOT_STARTED

                if not download_manager_obj.operation_classic_flag:

                    GObject.timeout_add(
                        0,
                        main_win_obj.progress_list_receive_dl_stats,
                        this_item,
                        dl_stat_dict,
                        True,       # Final set of statistics for this item
                    )

                else:

                    GObject.timeout_add(
                        0,
                        main_win_obj.classic_mode_tab_receive_dl_stats,
                        this_item,
                        dl_stat_dict,
                        True,       # Final set of statistics for this item
                    )


    @synchronise(_SYNC_LOCK)
    def change_item_stage(self, item_id, new_stage):

        """Called by downloads.DownloadManager.run().

        Based on DownloadList.change_stage().

        Changes the download stage for the specified downloads.DownloadItem
        object.

        Args:

            item_id (int): The specified item's .item_id

            new_stage: The new download stage, one of the values imported from
                formats.py (e.g. formats.MAIN_STAGE_QUEUED)

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 1800 change_item_stage')

        self.download_item_dict[item_id].stage = new_stage


    def create_item(self, media_data_obj, scheduled_obj=None,
    override_operation_type=None, priority_flag=False,
    ignore_limits_flag=False, recursion_flag=False):

        """Called initially by self.__init__() (or by many other functions,
        for example in mainapp.TartubeApp).

        Subsequently called by this function recursively.

        Creates a downloads.DownloadItem object for media data objects in the
        media data registry.

        Doesn't create a download item object for:
            - media.Video, media.Channel and media.Playlist objects whose
                .source is None
            - media.Video objects whose parent is not a media.Folder (i.e.
                whose parent is a media.Channel or a media.Playlist)
            - media.Video objects in any restricted folder
            - media.Video objects in the fixed 'Unsorted Videos' folder which
                are already marked as downloaded
            - media.Video objects which have an ancestor (e.g. a parent
                media.Channel) for which checking/downloading is disabled
            - media.Video objects whose parent is a media.Folder, and whose
                file IVs are set, and for which a thumbnail exists, if
                mainapp.TartubeApp.operation_sim_shortcut_flag is set, and if
                the operation_type is 'sim'
            - media.Channel and media.Playlist objects for which checking/
                downloading are disabled, or which have an ancestor (e.g. a
                parent media.folder) for which checking/downloading is disabled
            - media.Channel, media.Playlist and media.Folder objects whose
                .dl_no_db_flag is set, during simulated downloads
            - media.Channel and media.Playlist objects during custom downloads
                in which videos are to be downloaded independently
            - media.Channel and media.Playlist objects which are disabled
                because their external directory is not available
            - media.Video objects whose parent channel/playlist/folder is
                marked unavailable because its external directory is not
                accessible
            - media.Folder objects

        Adds the resulting downloads.DownloadItem object to this object's IVs.

        Args:

            media_data_obj (media.Video, media.Channel, media.Playlist,
                media.Folder): A media data object

            scheduled_obj (media.Scheduled): The scheduled download object
                which wants to download media_data_obj (None if no scheduled
                download applies in this case)

            override_operation_type (str): After the download operation has
                started, any code can call this function to add new
                downloads.DownloadItem objects to this downloads.DownloadList,
                specifying a value that overrides the default value of
                self.operation_type. Note that this is not allowed when
                self.operation_type is 'classic_real', 'classic_sim' or
                'classic_custom', and will cause an error. The value is always
                None when called by self.__init__(). Otherwise, the value can
                be None, 'sim', 'real', 'custom_sim' or 'custom_real'

            priority_flag (bool): True if media_data_obj is to be added to the
                beginning of the list, False if it is to be added to the end
                of the list

            ignore_limits_flag (bool): True if operation limits
                (mainapp.TartubeApp.operation_limit_flag) should be ignored

            recursion_flag (bool): True when called by this function
                recursively, False when called (for the first time) by anything
                else. If False and media_data_obj is a media.Video object, we
                download it even if its parent is a channel or a playlist

        Returns:

            The downloads.DownloadItem object created (or None if no object is
                created; only required by calls from
                mainapp.TartubeApp.download_watch_videos() )

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 1873 create_item')

        # Sanity check - if no URL is specified, then there is nothing to
        #   download
        if not isinstance(media_data_obj, media.Folder) \
        and media_data_obj.source is None:
            return None

        # Apply the operation_type override, if specified
        if override_operation_type is not None:

            if self.operation_classic_flag:

                GObject.timeout_add(
                    0,
                    self.app_obj.system_error,
                    302,
                    'Invalid argument in Classic Mode tab download operation',
                )

                return None

            else:

                operation_type = override_operation_type

        else:

            operation_type = self.operation_type

        if operation_type == 'custom_real' \
        or operation_type == 'classic_custom':
            custom_flag = True
        else:
            custom_flag = False

        # Get the options.OptionsManager object that applies to this media
        #   data object
        # (The manager might be specified by obj itself, or it might be
        #   specified by obj's parent, or we might use the default
        #   options.OptionsManager)
        if not self.operation_classic_flag:

            options_manager_obj = utils.get_options_manager(
                self.app_obj,
                media_data_obj,
            )

        else:

            # Classic Mode tab
            if self.app_obj.classic_options_obj is not None:
                options_manager_obj = self.app_obj.classic_options_obj
            else:
                options_manager_obj = self.app_obj.general_options_obj

        # Ignore private folders, and don't download any of their children
        #   (because they are all children of some other non-private folder)
        if isinstance(media_data_obj, media.Folder) \
        and media_data_obj.priv_flag:
            return None

        # Don't download videos that we already have
        # Don't download videos if they're in a channel or playlist (since
        #   downloading the channel/playlist downloads the videos it contains)
        # (Exception: download a single video if that's what the calling code
        #   has specifically requested)
        # (Exception: for custom downloads, do get videos independently of
        #   their channel/playlist, if allowed)
        # Don't download videos in a folder, if this is a simulated download,
        #   and the video has already been checked (exception: if the video
        #   has been passed to the download operation directly, for example by
        #   right-clicking the video and selecting 'Check video')
        # (Exception: do download videos in a folder if they're marked as
        #   livestreams, in case the livestream has finished)
        if isinstance(media_data_obj, media.Video):

            if media_data_obj.dl_flag \
            or (
                not isinstance(media_data_obj.parent_obj, media.Folder) \
                and recursion_flag
                and (
                    not custom_flag
                    or (
                        self.custom_dl_obj \
                        and not self.custom_dl_obj.dl_by_video_flag
                    ) or media_data_obj.dl_flag
                )
            ):
                return None

            if isinstance(media_data_obj.parent_obj, media.Folder) \
            and (
                operation_type == 'sim' \
                or operation_type == 'custom_sim' \
                or operation_type == 'classic_sim'
            ) and self.app_obj.operation_sim_shortcut_flag \
            and recursion_flag \
            and media_data_obj.file_name \
            and not media_data_obj.live_mode \
            and utils.find_thumbnail(self.app_obj, media_data_obj):
                return None

        # Don't download videos in channels/playlists/folders which have been
        #   marked unavailable, because their external directory is not
        #   accessible
        if isinstance(media_data_obj, media.Video):
            if media_data_obj.parent_obj.name \
            in self.app_obj.media_unavailable_dict:
                return None

        elif not isinstance(media_data_obj, media.Video) \
        and media_data_obj.name in self.app_obj.media_unavailable_dict:
            return None

        # Don't simulated downloads of video in channels/playlists/folders
        #   whose whose .dl_no_db_flag is set
        if (operation_type == 'sim' or operation_type == 'custom_sim') \
        and (
            (
                isinstance(media_data_obj, media.Video) \
                and media_data_obj.parent_obj.dl_no_db_flag
            ) or (
                not isinstance(media_data_obj, media.Video) \
                and media_data_obj.dl_no_db_flag
            )
        ):
            return None

        # Don't create a download.DownloadItem object if checking/download is
        #   disabled for the media data object
        if not isinstance(media_data_obj, media.Video) \
        and media_data_obj.dl_disable_flag:
            return None

        # Don't create a download.DownloadItem object for a media.Folder,
        #   obviously
        # Don't create a download.DownloadItem object for a media.Channel or
        #   media.Playlist during a custom download in which videos are to be
        #   downloaded independently
        download_item_obj = None

        if (
            isinstance(media_data_obj, media.Video)
            and custom_flag
            and (
                (self.custom_dl_obj and self.custom_dl_obj.dl_by_video_flag) \
                or self.app_obj.temp_stamp_list \
                or self.app_obj.temp_slice_list
            )
        ) or (
            isinstance(media_data_obj, media.Video)
            and (
                not custom_flag \
                or (
                    self.custom_dl_obj \
                    and not self.custom_dl_obj.dl_by_video_flag
                )
            )
        ) or (
            (
                isinstance(media_data_obj, media.Channel) \
                or isinstance(media_data_obj, media.Playlist)
            ) and (
                not custom_flag \
                or (
                    self.custom_dl_obj \
                    and not self.custom_dl_obj.dl_by_video_flag
                )
            )
        ):
            # (Broadcasting livestreams should always take priority over
            #   everything else)
            if isinstance(media_data_obj, media.Video) \
            and media_data_obj.live_mode == 2:

                broadcast_flag = True
                # For a broadcasting livestream, we create additional workers
                #   if required, possibly bypassing the limit specified by
                #   mainapp.TartubeApp.num_worker_default
                if self.app_obj.download_manager_obj:
                    self.app_obj.download_manager_obj.create_bypass_worker()

            else:

                broadcast_flag = False

            # Create a new download.DownloadItem object...
            self.download_item_count += 1
            download_item_obj = DownloadItem(
                self.download_item_count,
                media_data_obj,
                scheduled_obj,
                options_manager_obj,
                operation_type,
                ignore_limits_flag,
            )

            # ...and add it to our list
            if broadcast_flag:
                self.download_item_list.insert(0, download_item_obj.item_id)
            elif priority_flag:
                self.temp_item_list.append(download_item_obj.item_id)
            else:
                self.download_item_list.append(download_item_obj.item_id)

            self.download_item_dict[download_item_obj.item_id] \
            = download_item_obj

        # Call this function recursively for any child media data objects in
        #   the following situations:
        #   1. A media.Folder object has children
        #   2. A media.Channel/media.Playlist object has child media.Video
        #       objects, and this is a custom download in which videos are to
        #       be downloaded independently of their channel/playlist
        if isinstance(media_data_obj, media.Folder) \
        or (
            not isinstance(media_data_obj, media.Video)
            and custom_flag
            and self.custom_dl_obj
            and self.custom_dl_obj.dl_by_video_flag
        ):
            for child_obj in media_data_obj.child_list:
                self.create_item(
                    child_obj,
                    scheduled_obj,
                    operation_type,
                    priority_flag,
                    ignore_limits_flag,
                    True,                   # Recursion
                )

        # Procedure complete
        return download_item_obj


    def create_dummy_item(self, media_data_obj):

        """Called by self.__init__() only, when the download operation was
        launched from the Classic Mode tab (this function is not called
        recursively).

        Creates a downloads.DownloadItem object for each dummy media.Video
        object.

        Adds the resulting downloads.DownloadItem object to this object's IVs.

        Args:

            media_data_obj (media.Video): A media data object

        Returns:

            The downloads.DownloadItem object created

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 2090 create_dummy_item')

        if self.app_obj.classic_options_obj is not None:
            options_manager_obj = self.app_obj.classic_options_obj
        else:
            options_manager_obj = self.app_obj.general_options_obj

        # Create a new download.DownloadItem object...
        self.download_item_count += 1
        download_item_obj = DownloadItem(
            media_data_obj.dbid,
            media_data_obj,
            None,                       # media.Scheduled object
            options_manager_obj,
            self.operation_type,        # 'classic_real'. 'classic_sim' or
                                        #   'classic_custom'
            False,                      # ignore_limits_flag
        )

        # ...and add it to our list
        self.download_item_list.append(download_item_obj.item_id)
        self.download_item_dict[download_item_obj.item_id] = download_item_obj

        # Procedure complete
        return download_item_obj


    @synchronise(_SYNC_LOCK)
    def fetch_next_item(self):

        """Called by downloads.DownloadManager.run().

        Based on DownloadList.fetch_next().

        Returns:

            The next downloads.DownloadItem object, or None if there are none
                left

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 2131 fetch_next_item')

        if not self.prevent_fetch_flag:

            # In case of any recent calls to self.create_item(), which want to
            #   place new DownloadItems at the beginning of the queue, then
            #   merge the temporary queue into the main one
            if self.temp_item_list:
                self.download_item_list \
                = self.temp_item_list + self.download_item_list

            for item_id in self.download_item_list:
                this_item = self.download_item_dict[item_id]

                # Don't return an item that's marked as
                #   formats.MAIN_STAGE_ACTIVE
                if this_item.stage == formats.MAIN_STAGE_QUEUED:
                    return this_item

        return None


    @synchronise(_SYNC_LOCK)
    def move_item_to_bottom(self, download_item_obj):

        """Called by mainwin.MainWin.on_progress_list_dl_last().

        Moves the specified DownloadItem object to the end of
        self.download_item_list, so it is assigned a DownloadWorker last
        (after all other DownloadItems).

        Args:

            download_item_obj (downloads.DownloadItem): The download item
                object to move

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 2170 move_item_to_bottom')

        # Move the item to the bottom (end) of the list
        if download_item_obj is None \
        or not download_item_obj.item_id in self.download_item_list:
            return
        else:
            self.download_item_list.append(
                self.download_item_list.pop(
                    self.download_item_list.index(download_item_obj.item_id),
                ),
            )


    @synchronise(_SYNC_LOCK)
    def move_item_to_top(self, download_item_obj):

        """Called by mainwin.MainWin.on_progress_list_dl_next().

        Moves the specified DownloadItem object to the start of
        self.download_item_list, so it is the next item to be assigned a
        DownloadWorker.

        Args:

            download_item_obj (downloads.DownloadItem): The download item
                object to move

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 2201 move_item_to_top')

        # Move the item to the top (beginning) of the list
        if download_item_obj is None \
        or not download_item_obj.item_id in self.download_item_list:
            return
        else:
            self.download_item_list.insert(
                0,
                self.download_item_list.pop(
                    self.download_item_list.index(download_item_obj.item_id),
                ),
            )


    @synchronise(_SYNC_LOCK)
    def prevent_fetch_new_items(self):

        """Called by DownloadManager.stop_download_operation_soon().

        Sets the flag that prevents calls to self.fetch_next_item() from
        fetching anything new, which allows the download operation to stop as
        soon as any ongoing video downloads have finished.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 2227 prevent_fetch_new_items')

        self.prevent_fetch_flag = True


    def reorder_master_slave(self):

        """Called by self.__init__() after the calls to self.create_item() are
        finished.

        Some media data objects have an alternate download destination, for
        example, a playlist ('slave') might download its videos into the
        directory used by a channel ('master').

        This can increase the length of the operation, because a 'slave' won't
        start until its 'master' is finished.

        Make sure all designated 'masters' are handled before 'slaves' (a media
        media data object can't be both a master and a slave).

        Even if this doesn't reduce the time the 'slaves' spend waiting to
        start, it at least makes the download order predictable.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 2252 reorder_master_slave')

        master_list = []
        other_list = []
        for item_id in self.download_item_list:
            download_item_obj = self.download_item_dict[item_id]

            if isinstance(download_item_obj.media_data_obj, media.Video) \
            or not download_item_obj.media_data_obj.slave_dbid_list:
                other_list.append(item_id)
            else:
                master_list.append(item_id)

        self.download_item_list = []
        self.download_item_list.extend(master_list)
        self.download_item_list.extend(other_list)


class DownloadItem(object):

    """Called by downloads.DownloadList.create_item() and
    .create_dummy_item().

    Based on the DownloadItem class in youtube-dl-gui.

    Python class used to track the download status of a media data object
    (media.Video, media.Channel, media.Playlist or media.Folder), one of many
    in a downloads.DownloadList object.

    Args:

        item_id (int): The number of downloads.DownloadItem objects created,
            used to give each one a unique ID

        media_data_obj (media.Video, media.Channel, media.Playlist,
            media.Folder): The media data object to be downloaded. When the
            download operation was launched from the Classic Mode tab, a dummy
            media.Video object

        scheduled_obj (media.Scheduled): The scheduled download object which
            wants to download media_data_obj (None if no scheduled download
            applies in this case)

        options_manager_obj (options.OptionsManager): The object which
            specifies download options for the media data object

        operation_type (str): The value that applies to this DownloadItem only
            (might be different from the default value stored in
            DownloadManager.operation_type)

        ignore_limits_flag (bool): Flag set to True if operation limits
            (mainapp.TartubeApp.operation_limit_flag) should be ignored

    """


    # Standard class methods


    def __init__(self, item_id, media_data_obj, scheduled_obj,
    options_manager_obj, operation_type, ignore_limits_flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 2323 __init__')

        # IV list - class objects
        # -----------------------
        # The media data object to be downloaded. When the download operation
        #   was launched from the Classic Mode tab, a dummy media.Video object
        self.media_data_obj = media_data_obj
        # The scheduled download object which wants to download media_data_obj
        #   (None if no scheduled download applies in this case)
        self.scheduled_obj = scheduled_obj
        # The object which specifies download options for the media data object
        self.options_manager_obj = options_manager_obj

        # IV list - other
        # ---------------
        # A unique ID for this object
        self.item_id = item_id
        # The current download stage
        self.stage = formats.MAIN_STAGE_QUEUED

        # The value that applies to this DownloadItem only (might be different
        #   from the default value stored in DownloadManager.operation_type)
        self.operation_type = operation_type
        # Shortcut flag to test the operation type; True for 'classic_sim',
        #   'classic_real' and 'classic_custom'; False for all other values
        self.operation_classic_flag = False         # (Set below)

        # Flag set to True if operation limits
        #   (mainapp.TartubeApp.operation_limit_flag) should be ignored
        self.ignore_limits_flag = ignore_limits_flag


        # Code
        # ----

        # Set the flag
        if operation_type == 'classic_sim' \
        or operation_type == 'classic_real' \
        or operation_type == 'classic_custom':
            self.operation_classic_flag = True


    # Set accessors


    def set_ignore_limits_flag(self):

        """Called by DownloadManager.apply_ignore_limits(), following a call
        from mainapp>TartubeApp.script_slow_timer_callback()."""

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 2382 set_ignore_limits_flag')

        self.ignore_limits_flag = True


class VideoDownloader(object):

    """Called by downloads.DownloadWorker.run_video_downloader().

    Based on the YoutubeDLDownloader class in youtube-dl-gui.

    Python class to create a system child process. Uses the child process to
    instruct youtube-dl to download all videos associated with the URL
    described by a downloads.DownloadItem object (which might be an individual
    video, or a channel or playlist).

    Reads from the child process STDOUT and STDERR, having set up a
    downloads.PipeReader object to do so in an asynchronous way.

    Sets self.return_code to a value in the range 0-5, described below. The
    parent downloads.DownloadWorker object checks that return code once this
    object's child process has finished.

    Args:

        download_manager_obj (downloads.DownloadManager): The download manager
            object handling the entire download operation

        download_worker_obj (downloads.DownloadWorker): The parent download
            worker object. The download manager uses multiple workers to
            implement simultaneous downloads. The download manager checks for
            free workers and, when it finds one, assigns it a
            download.DownloadItem object. When the worker is assigned a
            download item, it creates a new instance of this object to
            interface with youtube-dl, and waits for this object to return a
            return code

        download_item_obj (downloads.DownloadItem): The download item object
            describing the URL from which youtube-dl should download video(s)

    Warnings:

        The calling function is responsible for calling the close() method
        when it's finished with this object, in order for this object to
        properly close down.

    """


    # Attributes


    # Valid values for self.return_code. The larger the number, the higher in
    #   the hierarchy of return codes.
    # Codes lower in the hierarchy (with a smaller number) cannot overwrite
    #   higher in the hierarchy (with a bigger number)
    #
    # 0 - The download operation completed successfully
    OK = 0
    # 1 - A warning occured during the download operation
    WARNING = 1
    # 2 - An error occured during the download operation
    ERROR = 2
    # 3 - The corresponding url video file was larger or smaller from the given
    #   filesize limit
    FILESIZE_ABORT = 3
    # 4 - The video(s) for the specified URL have already been downloaded
    ALREADY = 4
    # 5 - The download operation was stopped by the user
    STOPPED = 5
    # 6 - The download operation has stalled. The parent worker can restart it,
    #   if required
    STALLED = -1


    # Standard class methods


    def __init__(self, download_manager_obj, download_worker_obj, \
    download_item_obj):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 2464 __init__')

        # IV list - class objects
        # -----------------------
        # The downloads.DownloadManager object handling the entire download
        #   operation
        self.download_manager_obj = download_manager_obj
        # The parent downloads.DownloadWorker object
        self.download_worker_obj = download_worker_obj
        # The downloads.DownloadItem object describing the URL from which
        #   youtube-dl should download video(s)
        self.download_item_obj = download_item_obj

        # This object reads from the child process STDOUT and STDERR in an
        #   asynchronous way
        # Standard Python synchronised queue classes
        self.stdout_queue = queue.Queue()
        self.stderr_queue = queue.Queue()
        # The downloads.PipeReader objects created to handle reading from the
        #   pipes
        self.stdout_reader = PipeReader(self.stdout_queue)
        self.stderr_reader = PipeReader(self.stderr_queue)

        # The child process created by self.create_child_process()
        self.child_process = None


        # IV list - other
        # ---------------
        # The current return code, using values in the range 0-5, as described
        #   above
        # The value remains set to self.OK unless we encounter any problems
        # The larger the number, the higher in the hierarchy of return codes.
        #   Codes lower in the hierarchy (with a smaller number) cannot
        #   overwrite higher in the hierarchy (with a bigger number)
        self.return_code = self.OK
        # The time (in seconds) between iterations of the loop in
        #   self.do_download()
        self.sleep_time = 0.1
        # The time (in seconds) to wait for an existing download, which shares
        #   a common download destination with this media data object, to
        #   finish downloading
        self.long_sleep_time = 10

        # The time (matches time.time() ) at which the last activity occured
        #   (last output to STDOUT); used to restart a stalled download, if
        #   required
        self.last_activity_time = None

        # Flag set to True if we are simulating downloads for this media data
        #   object, or False if we actually downloading videos (set below)
        self.dl_sim_flag = False
        # Flag set to True if this download operation was launched from the
        #   Classic Mode tab, False if not (set below)
        self.dl_classic_flag = False

        # Flag set to True by a call from any function to self.stop_soon()
        # After being set to True, this VideoDownloader should give up after
        #   the next call to self.confirm_new_video(), .confirm_old_video()
        #   .confirm_sim_video()
        self.stop_soon_flag = False
        # When self.stop_soon_flag is True, the next call to
        #   self.confirm_new_video(), .confirm_old_video() or
        #   .confirm_sim_video() sets this flag to True, informing
        #   self.do_download() that it can stop the child process
        self.stop_now_flag = False

        # youtube-dl is passed a URL, which might represent an individual
        #   video, a channel or a playlist
        # Assume it's an individual video unless youtube-dl reports a
        #   channel or playlist (in which case, we can update these IVs later)
        # For simulated downloads, both IVs are set to the number of
        #   videos actually found
        self.video_num = None
        self.video_total = None
        # self.extract_stdout_data() detects the completion of a download job
        #   in one of several ways
        # The first time it happens for each individual video,
        #   self.extract_stdout_data() takes action. It calls
        #   self.confirm_new_video(), self.confirm_old_video() or
        #   self.confirm_sim_video() when required
        # On subsequent occasions, the completion message is ignored (as
        #   youtube-dl may pass us more than one completion message for a
        #   single video)
        # There is one exception: in calls to self.confirm_new_video, a
        #   subsequent call to self.confirm_new_video() updates the file
        #   extension of the media.Video. (FFmpeg may send several completion
        #   messages as it converts one file format to another; the final one
        #   is the one we want)
        # Dictionary of videos, used to check for the first completion message
        #   for each unique video
        # Dictionary in the form
        #       key = the video number (matches self.video_num)
        #       value = the media.Video object created
        self.video_check_dict = {}
        # The code imported from youtube-dl-gui doesn't recognise a downloaded
        #   video, if FFmpeg isn't used to extract it (because FFmpeg is not
        #   installed, or because the website doesn't support it, or whatever)
        # In this situation, youtube-dl's STDOUT messages don't definitively
        #   establish when it has finished downloading a video
        # When a file destination is announced; it is temporarily stored in
        #   these IVs. When STDOUT receives a message in the form
        #       [download] 100% of 2.06MiB in 00:02
        #   ...and the filename isn't one that FFmpeg would use (e.g.
        #       'myvideo.f136.mp4' or 'myvideo.f136.m4a', then assume that the
        #       video has finished downloading
        self.temp_path = None
        self.temp_filename = None
        self.temp_extension = None

        # When checking a channel/playlist, this number is incremented every
        #   time youtube-dl gives us the details of a video which the Tartube
        #   database already contains (with a minimum number of IVs already
        #   set)
        # When downloading a channel/playlist, this number is incremented every
        #   time youtube-dl gives us a 'video already downloaded' message
        #   (unless the Tartube database hasn't actually marked the video as
        #   downloaded)
        # Every time the value is incremented, we check the limits specified by
        #   mainapp.TartubeApp.operation_check_limit or
        #   .operation_download_limit. If the limit has been reached, we stop
        #   checking/downloading the channel/playlist
        # No check is carried out if self.download_item_obj represents an
        #   individual media.Video object (and not a whole channel or playlist)
        self.video_limit_count = 0
        # Git issue #9 describes youtube-dl failing to download the video's
        #   JSON metadata. We can't do anything about the youtube-dl code, but
        #   we can apply our own timeout
        # This IV is set whenever self.confirm_sim_video() is called. After
        #   being set, if a certain time has passed without another call to
        #   self.confirm_sim_video, self.do_download() halts the child process
        self.last_sim_video_check_time = None
        # The time to wait, in seconds
        self.last_sim_video_wait_time = 60

        # If mainapp.TartubeApp.operation_convert_mode is set to any value
        #   other than 'disable', then a media.Video object whose URL
        #   represents a channel/playlist is converted into multiple new
        #   media.Video objects, one for each video actually downloaded
        # Flag set to True when self.download_item_obj.media_data_obj is a
        #   media.Video object, but a channel/playlist is detected (regardless
        #   of the value of mainapp.TartubeApp.operation_convert_mode)
        self.url_is_not_video_flag = False

        # For channels/playlists, a list of child media.Video objects, used to
        #   track missing videos (when required)
        self.missing_video_check_list = []
        # Flag set to true (for convenience) if the list is populated
        self.missing_video_check_flag = False


        # Code
        # ----
        # Initialise IVs depending on whether this is a real or simulated
        #   download
        media_data_obj = self.download_item_obj.media_data_obj

        # All media data objects can be marked as simulate downloads only
        #   (except when the download operation was launched from the Classic
        #   Mode tab)
        # The setting applies not just to the media data object, but all of its
        #   descendants
        if not self.download_item_obj.operation_classic_flag:

            if self.download_item_obj.operation_type == 'sim' \
            or self.download_item_obj.operation_type == 'custom_sim':
                dl_sim_flag = True
            else:
                dl_sim_flag = media_data_obj.dl_sim_flag
                parent_obj = media_data_obj.parent_obj

                while not dl_sim_flag and parent_obj is not None:
                    dl_sim_flag = parent_obj.dl_sim_flag
                    parent_obj = parent_obj.parent_obj

            if dl_sim_flag:
                self.dl_sim_flag = True
                self.video_num = 0
                self.video_total = 0
            else:
                self.dl_sim_flag = False
                self.video_num = 1
                self.video_total = 1

        else:

            self.dl_classic_flag = True
            if self.download_item_obj.operation_type == 'classic_sim':
                self.dl_sim_flag = True

            self.video_num = 1
            self.video_total = 1

        # If the user wants to detect missing videos in channels/playlists
        #   (those that have been downloaded by the user, but since removed
        #   from the website by the creator), set that up
        if (
            isinstance(media_data_obj, media.Channel) \
            or isinstance(media_data_obj, media.Playlist)
        ) and (
            self.download_item_obj.operation_type == 'real' \
            or self.download_item_obj.operation_type == 'sim'
        ) and download_manager_obj.app_obj.track_missing_videos_flag:

            # Compile a list of child videos. Videos can be removed from the
            #   list as they are detected
            self.missing_video_check_list = media_data_obj.child_list.copy()
            if self.missing_video_check_list:
                self.missing_video_check_flag = True


    # Public class methods


    def do_download(self):

        """Called by downloads.DownloadWorker.run_video_downloader().

        Based on YoutubeDLDownloader.download().

        Downloads video(s) from a URL described by self.download_item_obj.

        Returns:

            The final return code, a value in the range 0-5 (as described
                above)

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 2691 do_download')

        # Import the main application (for convenience)
        app_obj = self.download_manager_obj.app_obj

        # Set the default return code. Everything is OK unless we encounter
        #   any problems
        self.return_code = self.OK

        if not self.dl_classic_flag:

            # Reset the errors/warnings stored in the media data object, the
            #   last time it was checked/downloaded
            self.download_item_obj.media_data_obj.reset_error_warning()

            # If two channels/playlists/folders share a download destination,
            #   we don't want to download both of them at the same time
            # If this media data obj shares a download destination with another
            #   downloads.DownloadWorker, wait until that download has finished
            #   before starting this one
            if not isinstance(
                self.download_item_obj.media_data_obj,
                media.Video,
            ):
                while self.download_manager_obj.check_master_slave(
                    self.download_item_obj.media_data_obj,
                ):
                    time.sleep(self.long_sleep_time)

        # Prepare a system command...
        options_obj = self.download_worker_obj.options_manager_obj
        if options_obj.options_dict['direct_cmd_flag']:

            cmd_list = utils.generate_direct_system_cmd(
                app_obj,
                self.download_item_obj.media_data_obj,
                options_obj,
            )

        else:

            divert_mode = None
            if (
                self.download_item_obj.operation_type == 'custom_real' \
                or self.download_item_obj.operation_type == 'classic_custom'
            ) and isinstance(
                self.download_item_obj.media_data_obj,
                media.Video,
            ) and self.download_manager_obj.custom_dl_obj:
                divert_mode \
                = self.download_manager_obj.custom_dl_obj.divert_mode

            cmd_list = utils.generate_ytdl_system_cmd(
                app_obj,
                self.download_item_obj.media_data_obj,
                self.download_worker_obj.options_list,
                self.dl_sim_flag,
                self.dl_classic_flag,
                self.missing_video_check_flag,
                self.download_manager_obj.custom_dl_obj,
                divert_mode,
            )

        # ...display it in the Output tab (if required)...
        if app_obj.ytdl_output_system_cmd_flag:
            app_obj.main_win_obj.output_tab_write_system_cmd(
                self.download_worker_obj.worker_id,
                ' '.join(cmd_list),
            )

        # ...and the terminal (if required)...
        if app_obj.ytdl_write_system_cmd_flag:
            print(' '.join(cmd_list))

        # ...and create a new child process using that command
        self.create_child_process(cmd_list)

        # So that we can read from the child process STDOUT and STDERR, attach
        #   a file descriptor to the PipeReader objects
        if self.child_process is not None:

            self.stdout_reader.attach_file_descriptor(
                self.child_process.stdout,
            )

            self.stderr_reader.attach_file_descriptor(
                self.child_process.stderr,
            )

        # While downloading the media data object, update the callback function
        #   with the status of the current job
        while self.is_child_process_alive():

            # Pause a moment between each iteration of the loop (we don't want
            #   to hog system resources)
            time.sleep(self.sleep_time)

            # Read from the child process STDOUT, and convert into unicode for
            #   Python's convenience
            while not self.stdout_queue.empty():

                stdout = self.stdout_queue.get_nowait().rstrip()
                if stdout:

                    self.last_activity_time = time.time()

                    # On MS Windows we use cp1252, so that Tartube can
                    #   communicate with the Windows console
                    stdout = stdout.decode(utils.get_encoding(), 'replace')

                    # Convert the statistics into a python dictionary in a
                    #   standard format, specified in the comments for
                    #   self.extract_stdout_data()
                    dl_stat_dict = self.extract_stdout_data(stdout)
                    # If the job's status is formats.COMPLETED_STAGE_ALREADY
                    #   or formats.ERROR_STAGE_ABORT, set our self.return_code
                    #   IV
                    self.extract_stdout_status(dl_stat_dict)
                    # Pass the dictionary on to self.download_worker_obj so the
                    #   main window can be updated
                    self.download_worker_obj.data_callback(dl_stat_dict)

                    # Show output in the Output tab (if required). For
                    #   simulated downloads, a message is displayed by
                    #   self.confirm_sim_video() instead
                    if app_obj.ytdl_output_stdout_flag \
                    and (
                        not app_obj.ytdl_output_ignore_progress_flag \
                        or not re.match(
                            r'\[download\]\s+[0-9\.]+\%\sof\s.*\sat\s.*\sETA',
                            stdout,
                        )
                    ) and (
                        not app_obj.ytdl_output_ignore_json_flag \
                        or stdout[:1] != '{'
                    ):
                        app_obj.main_win_obj.output_tab_write_stdout(
                            self.download_worker_obj.worker_id,
                            stdout,
                        )

                    # Show output in the terminal (if required). For simulated
                    #   downloads, a message is displayed by
                    #   self.confirm_sim_video() instead
                    if app_obj.ytdl_write_stdout_flag \
                    and (
                        not app_obj.ytdl_write_ignore_progress_flag \
                        or not re.match(
                            r'\[download\]\s+[0-9\.]+\%\sof\s.*\sat\s.*\sETA',
                            stdout,
                        )
                    ) and (
                        not app_obj.ytdl_write_ignore_json_flag \
                        or stdout[:1] != '{'
                    ):
                        # Git #175, Japanese text may produce a codec error
                        #   here, despite the .decode() call above
                        try:
                            print(
                                stdout.encode(utils.get_encoding(), 'replace'),
                            )
                        except:
                            print('STDOUT text with unprintable characters')

            # Apply the JSON timeout, if required
            if app_obj.apply_json_timeout_flag \
            and self.last_sim_video_check_time is not None \
            and self.last_sim_video_check_time < time.time():
                # Halt the child process, which stops checking this channel/
                #   playlist
                self.stop()

                GObject.timeout_add(
                    0,
                    app_obj.system_error,
                    303,
                    'Enforced timeout because downloader took too long to' \
                    + ' fetch a video\'s JSON data',
                )

            # If a download has stalled (there has been no activity for some
            #   time), halt the child process (allowing the parent worker to
            #   restart the stalled download, if required)
            restart_time = (app_obj.operation_auto_restart_time * 60)
            if app_obj.operation_auto_restart_flag \
            and self.last_activity_time is not None \
            and (self.last_activity_time + restart_time) < time.time():

                # Stop the child process
                self.stop()

                # Pass a dictionary of values to downloads.DownloadWorker,
                #   confirming the result of the job. The values are passed on
                #   to the main window
                self.last_data_callback()

                return self.STALLED

            # Stop this video downloader, if required to do so, having just
            #   finished checking/downloading a video
            if self.stop_now_flag:
                self.stop()

        # The child process has finished
        while not self.stderr_queue.empty():

            # Read from the child process STDERR queue (we don't need to read
            #   it in real time), and convert into unicode for python's
            #   convenience
            stderr = self.stderr_queue.get_nowait().rstrip()

            # On MS Windows we use cp1252, so that Tartube can communicate with
            #   the Windows console
            stderr = stderr.decode(utils.get_encoding(), 'replace')

            # A network error is treated the same way as a stalled download
            if app_obj.operation_auto_restart_network_flag \
            and self.is_network_error(stderr):

                self.stop()
                self.last_data_callback()
                return self.STALLED

            # Check for recognised errors/warnings
            if not self.is_ignorable(stderr):

                if self.is_warning(stderr):
                    self.set_return_code(self.WARNING)
                    self.download_item_obj.media_data_obj.set_warning(stderr)

                elif not self.is_debug(stderr):
                    self.set_return_code(self.ERROR)
                    self.download_item_obj.media_data_obj.set_error(stderr)

            # Show output in the Output tab (if required)
            if app_obj.ytdl_output_stderr_flag:
                app_obj.main_win_obj.output_tab_write_stderr(
                    self.download_worker_obj.worker_id,
                    stderr,
                )

            # Show output in the terminal (if required)
            if app_obj.ytdl_write_stderr_flag:
                # Git #175, Japanese text may produce a codec error here,
                #   despite the .decode() call above
                try:
                    print(stderr.encode(utils.get_encoding(), 'replace'))
                except:
                    print('STDERR text with unprintable characters')

        # We also set the return code to self.ERROR if the download didn't
        #   start or if the child process return code is greater than 0
        # Original notes from youtube-dl-gui:
        #   NOTE: In Linux if the called script is just empty Python exits
        #       normally (ret=0), so we can't detect this or similar cases
        #       using the code below
        #   NOTE: In Unix a negative return code (-N) indicates that the child
        #       was terminated by signal N (e.g. -9 = SIGKILL)
        internal_msg = None
        if self.child_process is None:
            self.set_return_code(self.ERROR)
            internal_msg = _('Download did not start')

        elif self.child_process.returncode > 0:
            self.set_return_code(self.ERROR)
            if not app_obj.ignore_child_process_exit_flag:
                internal_msg = _(
                    'Child process exited with non-zero code: {}',
                ).format(self.child_process.returncode)

        if internal_msg:

            # (The message must be visible in the Errors/Warnings tab, the
            #   Output tab and/or the terminal)
            self.download_item_obj.media_data_obj.set_error(internal_msg)

            if app_obj.ytdl_output_stderr_flag:
                app_obj.main_win_obj.output_tab_write_stderr(
                    self.download_worker_obj.worker_id,
                    internal_msg,
                )

            if app_obj.ytdl_write_stderr_flag:
                print(internal_msg)

        # For channels/playlists, detect missing videos (those downloaded by
        #   the user, but since deleted from the website by the creator)
        # We only perform the check if the process completed without errors,
        #   and was not halted early by the user (or halted by the download
        #   manager, because too many videos have been downloaded)
        # We also ignore livestreams
        detected_list = []

        if app_obj.track_missing_videos_flag \
        and self.missing_video_check_list \
        and self.download_manager_obj.running_flag \
        and not self.stop_soon_flag \
        and not self.stop_now_flag \
        and self.return_code <= self.WARNING:
            for check_obj in self.missing_video_check_list:
                if check_obj.dbid in app_obj.media_reg_dict \
                and check_obj.dl_flag \
                and not check_obj.live_mode:

                    # Filter out videos that are too old
                    if (
                        app_obj.track_missing_time_flag \
                        and app_obj.track_missing_time_days > 0
                    ):
                        # Convert the video's upload time from seconds to days
                        days = check_obj.upload_time / (60 * 60 * 24)
                        if days <= app_obj.track_missing_time_days:

                            # Mark this video as missing
                            detected_list.append(check_obj)

                    else:

                        # Mark this video as missing
                        detected_list.append(check_obj)

        for detected_obj in detected_list:
            app_obj.mark_video_missing(
                detected_obj,
                True,       # Video is missing
                True,       # Don't update the Video Index
                True,       # Don't update the Video Catalogue
                True,       # Don't sort the parent channel/playlist
            )

        # Pass a dictionary of values to downloads.DownloadWorker, confirming
        #   the result of the job. The values are passed on to the main
        #   window
        self.last_data_callback()

        # Pass the result back to the parent downloads.DownloadWorker object
        return self.return_code


    def check_dl_is_correct_type(self):

        """Called by self.extract_stdout_data().

        When youtube-dl reports the URL associated with the download item
        object contains multiple videos (or potentially contains multiple
        videos), then the URL represents a channel or playlist, not a video.

        This function checks whether a channel/playlist is about to be
        downloaded into a media.Video object. If so, it takes action to prevent
        that from happening.

        The action taken depends on the value of
        mainapp.TartubeApp.operation_convert_mode.

        Returns:

            False if a channel/playlist was about to be downloaded into a
                media.Video object, which has since been replaced by a new
                media.Channel/media.Playlist object

            True in all other situations (including when a channel/playlist was
                about to be downloaded into a media.Video object, which was
                not replaced by a new media.Channel/media.Playlist object)

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 3032 check_dl_is_correct_type')

        # Special case: if the download operation was launched from the
        #   Classic Mode tab, there is no need to do anything
        if self.dl_classic_flag:
            return True

        # Otherwise, import IVs (for convenience)
        app_obj = self.download_manager_obj.app_obj
        media_data_obj = self.download_item_obj.media_data_obj

        if isinstance(self.download_item_obj.media_data_obj, media.Video):

            # If the mode is 'disable', or if it the original media.Video
            #   object is contained in a channel or a playlist, then we must
            #   stop downloading this URL immediately
            if app_obj.operation_convert_mode == 'disable' \
            or not isinstance(
                self.download_item_obj.media_data_obj.parent_obj,
                media.Folder,
            ):
                self.url_is_not_video_flag = True

                # Stop downloading this URL
                self.stop()
                media_data_obj.set_error(
                    '\'' + media_data_obj.name + '\' ' + _(
                        'This video has a URL that points to a channel or a' \
                        + ' playlist, not a video',
                    ),
                )

                # Don't allow self.confirm_sim_video() to be called
                return False

            # Otherwise, we can create new media.Video objects for each
            #   video downloaded/checked. The new objects may be placd into a
            #   new media.Channel or media.Playlist object
            elif not self.url_is_not_video_flag:

                self.url_is_not_video_flag = True

                # Mark the original media.Video object to be destroyed at the
                #   end of the download operation
                self.download_manager_obj.mark_video_as_doomed(media_data_obj)

                if app_obj.operation_convert_mode != 'multi':

                    # Create a new media.Channel or media.Playlist object and
                    #   add it to the download manager
                    # Then halt this job, so the new channel/playlist object
                    #   can be downloaded
                    self.convert_video_to_container()

                # Don't allow self.confirm_sim_video() to be called
                return False

        # Do allow self.confirm_sim_video() to be called
        return True


    def close(self):

        """Can be called by anything.

        Destructor function for this object.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 3101 close')

        # Tell the PipeReader objects to shut down, thus joining their threads
        self.stdout_reader.join()
        self.stderr_reader.join()


    def compile_mini_options_dict(self, options_manager_obj):

        """Called by self.confirm_new_video() and .confirm_old_video().

        Compiles a dictionary containing a subset of download options from the
        specified options.OptionsManager object, to be passed on to
        mainapp.TartubeApp.announce_video_download().

        Args:

            options_manager_obj (options.OptionsManager): The options manager
                for this download

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 3124 compile_mini_options_dict')

        mini_options_dict = {
            'keep_description': \
                options_manager_obj.options_dict['keep_description'],
            'keep_info': \
                options_manager_obj.options_dict['keep_info'],
            'keep_annotations': \
                options_manager_obj.options_dict['keep_annotations'],
            'keep_thumbnail': \
                options_manager_obj.options_dict['keep_thumbnail'],
            'move_description': \
                options_manager_obj.options_dict['move_description'],
            'move_info': \
                options_manager_obj.options_dict['move_info'],
            'move_annotations': \
                options_manager_obj.options_dict['move_annotations'],
            'move_thumbnail': \
                options_manager_obj.options_dict['move_thumbnail'],
        }

        return mini_options_dict


    def confirm_archived_video(self, filename):

        """Called by self.extract_stdout_data().

        A modified version of self.confirm_old_video(), called when
        youtube-dl's 'has already been recorded in archive' message is detected
        (but only when checking for missing videos).

        Tries to find a match for the video name and, if one is found, marks it
        as not missing.

        Args:

            filename (str): The video name, which should match the .name of a
                media.Video object in self.missing_video_check_list

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 3167 confirm_archived_video')

        # Create shortcut variables (for convenience)
        app_obj = self.download_manager_obj.app_obj
        media_data_obj = self.download_item_obj.media_data_obj

        # media_data_obj is a media.Channel or media.Playlist object. Check its
        #   child objects, looking for a matching video
        match_obj = media_data_obj.find_matching_video(app_obj, filename)
        if match_obj and match_obj in self.missing_video_check_list:
            self.missing_video_check_list.remove(match_obj)


    def confirm_new_video(self, dir_path, filename, extension):

        """Called by self.extract_stdout_data().

        A successful download is announced in one of several ways.

        When an announcement is detected, this function is called. Use the
        first announcement to update self.video_check_dict. For subsequent
        announcments, only a media.Video's file extension is updated (see the
        comments in self.__init__() ).

        Args:

            dir_path (str): The full path to the directory in which the video
                is saved, e.g. '/home/yourname/tartube/downloads/Videos'

            filename (str): The video's filename, e.g. 'My Video'

            extension (str): The video's extension, e.g. '.mp4'

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 3202 confirm_new_video')

        # Import the main application (for convenience)
        app_obj = self.download_manager_obj.app_obj

        # Special case: don't add videos to the Tartube database at all
        media_data_obj = self.download_item_obj.media_data_obj
        if not isinstance(media_data_obj, media.Video) \
        and media_data_obj.dl_no_db_flag:

            # Deal with the video description, JSON data and thumbnail,
            #   according to the settings in options.OptionsManager
            utils.handle_files_after_download(
                app_obj,
                self.download_worker_obj.options_manager_obj,
                dir_path,
                filename,
            )

            # Register the download with DownloadManager, so that download
            #   limits can be applied, if required
            self.download_manager_obj.register_video('new')

        # Special case: if the download operation was launched from the
        #   Classic Mode tab, then we only need to update the dummy
        #   media.Video object, and to move/remove description/metadata/
        #   thumbnail files, as appropriate
        elif self.dl_classic_flag:

            self.confirm_new_video_classic_mode(dir_path, filename, extension)

        # All other cases
        elif not self.video_num in self.video_check_dict:

            # Create a new media.Video object for the video
            if self.url_is_not_video_flag:

                video_obj = app_obj.convert_video_from_download(
                    self.download_item_obj.media_data_obj.parent_obj,
                    self.download_item_obj.options_manager_obj,
                    dir_path,
                    filename,
                    extension,
                    True,               # Don't sort parent containers yet
                )

            else:

                video_obj = app_obj.create_video_from_download(
                    self.download_item_obj,
                    dir_path,
                    filename,
                    extension,
                    True,               # Don't sort parent containers yet
                )

            # If downloading from a channel/playlist, remember the video's
            #   index. (The server supplies an index even for a channel, and
            #   the user might want to convert a channel to a playlist)
            if isinstance(video_obj.parent_obj, media.Channel) \
            or isinstance(video_obj.parent_obj, media.Playlist):
                video_obj.set_index(self.video_num)

            # Contact SponsorBlock server to fetch video slice data
            if app_obj.custom_sblock_mirror != '' \
            and app_obj.sblock_fetch_flag \
            and video_obj.vid != None \
            and (not video_obj.slice_list or app_obj.sblock_replace_flag):
                utils.fetch_slice_data(
                    app_obj,
                    video_obj,
                    self.download_worker_obj.worker_id,
                    True,       # Write to terminal, if allowed
                )

            # Update the main window
            GObject.timeout_add(
                0,
                app_obj.announce_video_download,
                self.download_item_obj,
                video_obj,
                self.compile_mini_options_dict(
                    self.download_worker_obj.options_manager_obj,
                ),
            )

            # Register the download with DownloadManager, so that download
            #   limits can be applied, if required
            self.download_manager_obj.register_video('new')

            # Update the checklist
            self.video_check_dict[self.video_num] = video_obj

        else:

            # Update the video's file extension, in case one file format has
            #   been converted to another (with a new call to this function
            #   each time)
            video_obj = self.video_check_dict[self.video_num]

            if video_obj.file_ext is None \
            or (extension is not None and video_obj.file_ext != extension):
                video_obj.set_file_ext(extension)

        # This VideoDownloader can now stop, if required to do so after a video
        #   has been checked/downloaded
        if self.stop_soon_flag:
            self.stop_now_flag = True


    def confirm_new_video_classic_mode(self, dir_path, filename, extension):

        """Called by self.confirm_new_video() when a download operation was
        launched from the Classic Mode tab.

        Handles the download.

        Args:

            dir_path (str): The full path to the directory in which the video
                is saved, e.g. '/home/yourname/tartube/downloads/Videos'

            filename (str): The video's filename, e.g. 'My Video'

            extension (str): The video's extension, e.g. '.mp4'

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 3203 confirm_new_video_classic_mode')

        # Import the main application (for convenience)
        app_obj = self.download_manager_obj.app_obj

        # Update the dummy media.Video object
        dummy_obj = self.download_item_obj.media_data_obj

        dummy_obj.set_dl_flag(True)
        dummy_obj.set_dummy_path(
            os.path.abspath(os.path.join(dir_path, filename + extension)),
        )

        # Contact SponsorBlock server to fetch video slice data
        if app_obj.custom_sblock_mirror != '' \
        and app_obj.sblock_fetch_flag \
        and video_obj.vid != None \
        and (not video_obj.slice_list or app_obj.sblock_replace_flag):
            utils.fetch_slice_data(
                app_obj,
                video_obj,
                self.download_worker_obj.worker_id,
                True,       # Write to terminal, if allowed
            )

        # Deal with the video description, JSON data and thumbnail, according
        #   to the settings in options.OptionsManager
        utils.handle_files_after_download(
            app_obj,
            self.download_worker_obj.options_manager_obj,
            dir_path,
            filename,
        )

        # Register the download with DownloadManager, so that download limits
        #   can be applied, if required
        self.download_manager_obj.register_video('new')


    def confirm_old_video(self, dir_path, filename, extension):

        """Called by self.extract_stdout_data().

        When youtube-dl reports a video has already been downloaded, make sure
        the media.Video object is marked as downloaded, and upate the main
        window if necessary.

        Args:

            dir_path (str): The full path to the directory in which the video
                is saved, e.g. '/home/yourname/tartube/downloads/Videos'

            filename (str): The video's filename, e.g. 'My Video'

            extension (str): The video's extension, e.g. '.mp4'

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 3295 confirm_old_video')

        # Create shortcut variables (for convenience)
        app_obj = self.download_manager_obj.app_obj
        media_data_obj = self.download_item_obj.media_data_obj

        # Special case: don't add videos to the Tartube database at all
        if not isinstance(media_data_obj, media.Video) \
        and media_data_obj.dl_no_db_flag:

            # Register the download with DownloadManager, so that download
            #   limits can be applied, if required
            self.download_manager_obj.register_video('old')

        # Special case: if the download operation was launched from the
        #   Classic Mode tab, then we only need to update the dummy
        #   media.Video object
        elif self.dl_classic_flag:

            media_data_obj.set_dl_flag(True)
            media_data_obj.set_dummy_path(
                os.path.abspath(os.path.join(dir_path, filename + extension)),
            )

            # Register the download with DownloadManager, so that download
            #   limits can be applied, if required
            self.download_manager_obj.register_video('old')

        # All other cases
        elif isinstance(media_data_obj, media.Video):

            if not media_data_obj.dl_flag:

                GObject.timeout_add(
                    0,
                    app_obj.mark_video_downloaded,
                    media_data_obj,
                    True,               # Video is downloaded
                    True,               # Video is not new
                )

        else:

            # media_data_obj is a media.Channel or media.Playlist object. Check
            #   its child objects, looking for a matching video
            match_obj = media_data_obj.find_matching_video(app_obj, filename)
            if match_obj:

                # This video will not be marked as a missing video
                if match_obj in self.missing_video_check_list:
                    self.missing_video_check_list.remove(match_obj)

                if not match_obj.dl_flag:

                    GObject.timeout_add(
                        0,
                        app_obj.mark_video_downloaded,
                        match_obj,
                        True,           # Video is downloaded
                        True,           # Video is not new
                    )

                else:

                    # This video applies towards the limit (if any) specified
                    #   by mainapp.TartubeApp.operation_download_limit
                    self.video_limit_count += 1

                    if not isinstance(
                        self.download_item_obj.media_data_obj,
                        media.Video,
                    ) \
                    and not self.download_item_obj.ignore_limits_flag \
                    and app_obj.operation_limit_flag \
                    and app_obj.operation_download_limit \
                    and self.video_limit_count >= \
                    app_obj.operation_download_limit:
                        # Limit reached; stop downloading videos in this
                        #   channel/playlist
                        self.stop()

            else:

                # No match found, so create a new media.Video object for the
                #   video file that already exists on the user's filesystem
                video_obj = app_obj.create_video_from_download(
                    self.download_item_obj,
                    dir_path,
                    filename,
                    extension,
                )

                self.video_check_dict[self.video_num] = video_obj

                # Update the main window
                if media_data_obj.external_dir is not None \
                and media_data_obj.master_dbid != media_data_obj.dbid:

                    # The container is storing its videos in another
                    #   container's sub-directory, which (probably) explains
                    #   why we couldn't find a match. Don't add anything to the
                    #   Results List
                    GObject.timeout_add(
                        0,
                        app_obj.announce_video_clone,
                        video_obj,
                    )

                else:

                    # Do add an entry to the Results List (as well as updating
                    #   the Video Catalogue, as normal)
                    GObject.timeout_add(
                        0,
                        app_obj.announce_video_download,
                        self.download_item_obj,
                        video_obj,
                        self.compile_mini_options_dict(
                            self.download_worker_obj.options_manager_obj,
                        ),
                    )

        # This VideoDownloader can now stop, if required to do so after a video
        #   has been checked/downloaded
        if self.stop_soon_flag:
            self.stop_now_flag = True


    def confirm_sim_video(self, json_dict):

        """Called by self.extract_stdout_data().

        After a successful simulated download, youtube-dl presents us with JSON
        data for the video. Use that data to update everything.

        Args:

            json_dict (dict): JSON data from STDOUT, converted into a python
                dictionary

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 3428 confirm_sim_video')

        # Import the main application (for convenience)
        app_obj = self.download_manager_obj.app_obj
        # Call self.stop(), if the limit described in the comments for
        #   self.__init__() have been reached
        stop_flag = False

        # Set the time at which a JSON timeout should be applied, if no more
        #   calls to this function have been made
        self.last_sim_video_check_time \
        = int(time.time()) + self.last_sim_video_wait_time

        # From the JSON dictionary, extract the data we need
        # Git #177 reports that this value might be 'None', so check for that
        if '_filename' in json_dict \
        and json_dict['_filename'] is not None:
            full_path = json_dict['_filename']
            path, filename, extension = self.extract_filename(full_path)
        else:
            GObject.timeout_add(
                0,
                app_obj.system_error,
                304,
                'Missing filename in JSON data',
            )

            return

        # (Git #322, 'upload_date' might be None)
        if 'upload_date' in json_dict \
        and json_dict['upload_date'] is not None:

            try:
                # date_string in form YYYYMMDD
                date_string = json_dict['upload_date']
                dt_obj = datetime.datetime.strptime(date_string, '%Y%m%d')
                upload_time = dt_obj.timestamp()
            except:
                upload_time = None

        else:
            upload_time = None

        if 'duration' in json_dict:
            duration = json_dict['duration']
        else:
            duration = None

        if 'title' in json_dict:
            name = json_dict['title']
        else:
            name = None

        if 'id' in json_dict:
            vid = json_dict['id']

        chapter_list = []
        if 'chapters' in json_dict:
            chapter_list = json_dict['chapters']

        if 'description' in json_dict:
            descrip = json_dict['description']
        else:
            descrip = None

        if 'thumbnail' in json_dict:
            thumbnail = json_dict['thumbnail']
        else:
            thumbnail = None

#        if 'webpage_url' in json_dict:
#            source = json_dict['webpage_url']
#        else:
#            source = None
        # !!! DEBUG: yt-dlp Git #119: filter out the extraneous characters at
        #   the end of the URL, if present
        if 'webpage_url' in json_dict:

            source = re.sub(
                r'\&has_verified\=.*\&bpctr\=.*',
                '',
                json_dict['webpage_url'],
            )

        else:
            source = None

        if 'playlist_index' in json_dict:
            playlist_index = json_dict['playlist_index']
        else:
            playlist_index = None

        if 'is_live' in json_dict:
            if json_dict['is_live']:
                live_flag = True
            else:
                live_flag = False
        else:
            live_flag = False

        if 'comments' in json_dict:
            comment_list = json_dict['comments']
        else:
            comment_list = []

        # Does an existing media.Video object match this video?
        media_data_obj = self.download_item_obj.media_data_obj
        video_obj = None

        if self.url_is_not_video_flag:

            # media_data_obj has a URL which represents a channel or playlist,
            #   but media_data_obj itself is a media.Video object
            # media_data_obj's parent is a media.Folder object. Check its
            #   child objects, looking for a matching video
            # (video_obj is set to None, if no match is found)
            video_obj = media_data_obj.parent_obj.find_matching_video(
                app_obj,
                filename,
            )

            if not video_obj:
                video_obj = media_data_obj.parent_obj.find_matching_video(
                    app_obj,
                    name,
                )

        elif isinstance(media_data_obj, media.Video):

            # media_data_obj is a media.Video object
            video_obj = media_data_obj

        else:

            # media_data_obj is a media.Channel or media.Playlist object. Check
            #   its child objects, looking for a matching video
            # (video_obj is set to None, if no match is found)
            video_obj = media_data_obj.find_matching_video(app_obj, filename)
            if not video_obj:
                video_obj = media_data_obj.find_matching_video(app_obj, name)

        new_flag = False
        update_results_flag = False
        if not video_obj:

            # No matching media.Video object found, so create a new one
            new_flag = True
            update_results_flag = True

            if self.url_is_not_video_flag:

                video_obj = app_obj.convert_video_from_download(
                    self.download_item_obj.media_data_obj.parent_obj,
                    self.download_item_obj.options_manager_obj,
                    path,
                    filename,
                    extension,
                    # Don't sort parent container objects yet; wait for
                    #   mainwin.MainWin.results_list_update_row() to do it
                    True,
                )

            else:

                video_obj = app_obj.create_video_from_download(
                    self.download_item_obj,
                    path,
                    filename,
                    extension,
                    True,
                )

            # Update its IVs with the JSON information we extracted
            if filename is not None:
                video_obj.set_name(filename)

            if name is not None:
                video_obj.set_nickname(name)
            elif filename is not None:
                video_obj.set_nickname(filename)

            if vid is not None:
                video_obj.set_vid(vid)

            if upload_time is not None:
                video_obj.set_upload_time(upload_time)

            if duration is not None:
                video_obj.set_duration(duration)

            if source is not None:
                video_obj.set_source(source)

            if chapter_list:
                video_obj.extract_timestamps_from_chapters(
                    app_obj,
                    chapter_list,
                )

            if descrip is not None:
                video_obj.set_video_descrip(
                    app_obj,
                    descrip,
                    app_obj.main_win_obj.descrip_line_max_len,
                )

            if comment_list and app_obj.comment_store_flag:
                video_obj.set_comments(comment_list)

            # If downloading from a channel/playlist, remember the video's
            #   index. (The server supplies an index even for a channel, and
            #   the user might want to convert a channel to a playlist)
            if isinstance(video_obj.parent_obj, media.Channel) \
            or isinstance(video_obj.parent_obj, media.Playlist):
                video_obj.set_index(playlist_index)

            # Now we can sort the parent containers
            video_obj.parent_obj.sort_children(app_obj)
            app_obj.fixed_all_folder.sort_children(app_obj)
            if video_obj.bookmark_flag:
                app_obj.fixed_bookmark_folder.sort_children(app_obj)
            if video_obj.fav_flag:
                app_obj.fixed_fav_folder.sort_children(app_obj)
            if video_obj.live_mode:
                app_obj.fixed_live_folder.sort_children(app_obj)
            if video_obj.missing_flag:
                app_obj.fixed_missing_folder.sort_children(app_obj)
            if video_obj.new_flag:
                app_obj.fixed_new_folder.sort_children(app_obj)
            if video_obj in app_obj.fixed_recent_folder.child_list:
                app_obj.fixed_recent_folder.sort_children(app_obj)
            if video_obj.waiting_flag:
                app_obj.fixed_waiting_folder.sort_children(app_obj)

        else:

            # This video will not be marked as a missing video
            if video_obj in self.missing_video_check_list:
                self.missing_video_check_list.remove(video_obj)

            if video_obj.file_name \
            and video_obj.name != app_obj.default_video_name:

                # This video must not be displayed in the Results List, and
                #   counts towards the limit (if any) specified by
                #   mainapp.TartubeApp.operation_check_limit
                self.video_limit_count += 1

                if not isinstance(
                    self.download_item_obj.media_data_obj,
                    media.Video,
                ) \
                and not self.download_item_obj.ignore_limits_flag \
                and app_obj.operation_limit_flag \
                and app_obj.operation_check_limit \
                and self.video_limit_count >= app_obj.operation_check_limit:
                    # Limit reached. When we reach the end of this function,
                    #   stop checking videos in this channel/playlist
                    stop_flag = True

                # The call to DownloadManager.register_video() below doesn't
                #   take account of this situation, so make our own call
                self.download_manager_obj.register_video('other')

            else:

                # This video must be displayed in the Results List, and counts
                #   towards the limit (if any) specified by
                #   mainapp.TartubeApp.autostop_videos_value
                update_results_flag = True

            # If the 'Add videos' button was used, the path/filename/extension
            #   won't be set yet
            if not video_obj.file_name and full_path:
                video_obj.set_file(filename, extension)

            # Update any video object IVs that are not set
            if video_obj.name == app_obj.default_video_name \
            and filename is not None:
                video_obj.set_name(filename)

            if video_obj.nickname == app_obj.default_video_name:
                if name is not None:
                    video_obj.set_nickname(name)
                elif filename is not None:
                    video_obj.set_nickname(filename)

            if not video_obj.vid and vid is not None:
                video_obj.set_vid(vid)

            if not video_obj.upload_time and upload_time is not None:
               video_obj.set_upload_time(upload_time)

            if not video_obj.duration and duration is not None:
                video_obj.set_duration(duration)

            if not video_obj.source and source is not None:
                video_obj.set_source(source)

            if chapter_list:
                video_obj.extract_timestamps_from_chapters(
                    app_obj,
                    chapter_list,
                )

            if not video_obj.descrip and descrip is not None:
                video_obj.set_video_descrip(
                    app_obj,
                    descrip,
                    app_obj.main_win_obj.descrip_line_max_len,
                )

            if not video_obj.comment_list and comment_list:
                video_obj.set_comments(comment_list)

            # If downloading from a channel/playlist, remember the video's
            #   index. (The server supplies an index even for a channel, and
            #   the user might want to convert a channel to a playlist)
            if isinstance(video_obj.parent_obj, media.Channel) \
            or isinstance(video_obj.parent_obj, media.Playlist):
                video_obj.set_index(playlist_index)

        # Deal with livestreams
        if video_obj.live_mode != 2 and live_flag:

            GObject.timeout_add(
                0,
                app_obj.mark_video_live,
                video_obj,
                2,                  # Livestream is broadcasting
                {},                 # No livestream data
                True,               # Don't update Video Index yet
                True,               # Don't update Video Catalogue yet
            )

        elif video_obj.live_mode != 0 and not live_flag:

            GObject.timeout_add(
                0,
                app_obj.mark_video_live,
                video_obj,
                0,                  # Livestream has finished
                {},                 # Reset any livestream data
                True,               # Don't update Video Index yet
                True,               # Don't update Video Catalogue yet
            )

        # Deal with the video description, JSON data and thumbnail, according
        #   to the settings in options.OptionsManager
        options_dict \
        = self.download_worker_obj.options_manager_obj.options_dict

        if descrip and options_dict['write_description']:

            descrip_path = os.path.abspath(
                os.path.join(path, filename + '.description'),
            )

            if not options_dict['sim_keep_description']:

                descrip_path = utils.convert_path_to_temp(
                    app_obj,
                    descrip_path,
                )

            # (Don't replace a file that already exists, and obviously don't
            #   do anything if the call returned None because of a filesystem
            #   error)
            if descrip_path is not None and not os.path.isfile(descrip_path):

                try:
                    fh = open(descrip_path, 'wb')
                    fh.write(descrip.encode('utf-8'))
                    fh.close()

                    if options_dict['move_description']:
                        utils.move_metadata_to_subdir(
                            app_obj,
                            video_obj,
                            '.description',
                        )

                except:
                    pass

        if options_dict['write_info']:

            json_path = os.path.abspath(
                os.path.join(path, filename + '.info.json'),
            )

            if not options_dict['sim_keep_info']:
                json_path = utils.convert_path_to_temp(app_obj, json_path)

            if json_path is not None and not os.path.isfile(json_path):

                try:
                    with open(json_path, 'w') as outfile:
                        json.dump(json_dict, outfile, indent=4)

                    if options_dict['move_info']:
                        utils.move_metadata_to_subdir(
                            app_obj,
                            video_obj,
                            '.info.json',
                        )

                except:
                    pass

        # v2.1.101 - Annotations were removed by YouTube in 2019, so this
        #   feature is not available, and will not be available until the
        #   authors have some annotations to test
#        if options_dict['write_annotations']:
#
#            xml_path = os.path.abspath(
#                os.path.join(path, filename + '.annotations.xml'),
#            )
#
#            if not options_dict['sim_keep_annotations']:
#                xml_path = utils.convert_path_to_temp(app_obj, xml_path)

        if thumbnail and options_dict['write_thumbnail']:

            # Download the thumbnail, if we don't already have it
            # The thumbnail's URL is something like
            #   'https://i.ytimg.com/vi/abcdefgh/maxresdefault.jpg'
            # When saved to disc by youtube-dl, the file is given the same name
            #   as the video (but with a different extension)
            # Get the thumbnail's extension...
            remote_file, remote_ext = os.path.splitext(thumbnail)
            # Fix for Odysee videos, whose thumbnail extension is not specified
            #   in the .info.json fiel
            if remote_ext == '':
                remote_ext = '.webp'

            # ...and thus get the filename used by youtube-dl when storing the
            #   thumbnail locally
            thumb_path = video_obj.get_actual_path_by_ext(app_obj, remote_ext)

            if not options_dict['sim_keep_thumbnail']:
                thumb_path = utils.convert_path_to_temp(app_obj, thumb_path)

            if thumb_path is not None and not os.path.isfile(thumb_path):

                # v2.0.013 The requests module fails if the connection drops
                # v1.2.006 Writing the file fails if the directory specified
                #   by thumb_path doesn't exist
                # Use 'try' so that neither problem is fatal
                try:
                    request_obj = requests.get(
                        thumbnail,
                        timeout = app_obj.request_get_timeout,
                    )

                    with open(thumb_path, 'wb') as outfile:
                        outfile.write(request_obj.content)

                except:
                    pass

            # Convert .webp thumbnails to .jpg, if required
            thumb_path = utils.find_thumbnail_webp(app_obj, video_obj)
            if thumb_path is not None \
            and not app_obj.ffmpeg_fail_flag \
            and app_obj.ffmpeg_convert_webp_flag \
            and not app_obj.ffmpeg_manager_obj.convert_webp(thumb_path):

                app_obj.set_ffmpeg_fail_flag(True)
                GObject.timeout_add(
                    0,
                    app_obj.system_error,
                    305,
                    app_obj.ffmpeg_fail_msg,
                )

            # Move to the sub-directory, if required
            if options_dict['move_thumbnail']:

                utils.move_thumbnail_to_subdir(app_obj, video_obj)

        # Contact SponsorBlock server to fetch video slice data
        if app_obj.custom_sblock_mirror != '' \
        and app_obj.sblock_fetch_flag \
        and video_obj.vid != None \
        and (not video_obj.slice_list or app_obj.sblock_replace_flag):
            utils.fetch_slice_data(
                app_obj,
                video_obj,
                self.download_worker_obj.worker_id,
                True,       # Write to terminal, if allowed
            )

        # If a new media.Video object was created (or if a video whose name is
        #   unknown, now has a name), add a line to the Results List, as well
        #   as updating the Video Catalogue
        # The True argument passes on the download options 'move_description',
        #   etc, but not 'keep_description', etc
        if update_results_flag:

            GObject.timeout_add(
                0,
                app_obj.announce_video_download,
                self.download_item_obj,
                video_obj,
                # No call to self.compile_mini_options_dict, because this
                #   function deals with download options like
                #   'move_description' by itself
                {},
            )

        else:

            # Otherwise, just update the Video Catalogue
            GObject.timeout_add(
                0,
                app_obj.main_win_obj.video_catalogue_update_video,
                video_obj,
            )

        # For simulated downloads, self.do_download() has not displayed
        #   anything in the Output tab/terminal window; so do that now (if
        #   required)
        if (app_obj.ytdl_output_stdout_flag):

            app_obj.main_win_obj.output_tab_write_stdout(
                self.download_worker_obj.worker_id,
                '[' + video_obj.parent_obj.name + '] <' \
                + _('Simulated download of:') + ' \'' + filename + '\'>',
            )

        if (app_obj.ytdl_write_stdout_flag):

            # v2.2.039 Partial fix for Git #106, #115 and #175, for which we
            #   get a Python error when print() receives unicode characters
            filename = filename.encode().decode(
                utils.get_encoding(),
                'replace',
            )

            try:

                print(
                    '[' + video_obj.parent_obj.name + '] <' \
                    + _('Simulated download of:') + ' \'' + filename + '\'>',
                )

            except:

                print(
                    '[' + video_obj.parent_obj.name + '] <' \
                    + _(
                    'Simulated download of video with unprintable characters',
                    ) + '>',
                )

        # If a new media.Video object was created (or if a video whose name is
        #   unknown, now has a name), register the simulated download with
        #   DownloadManager, so that download limits can be applied, if
        #   required
        if update_results_flag:
            self.download_manager_obj.register_video('sim')

        # Stop checking videos in this channel/playlist, if a limit has been
        #   reached
        if stop_flag:
            self.stop()

        # This VideoDownloader can now stop, if required to do so after a video
        #   has been checked/downloaded
        elif self.stop_soon_flag:
            self.stop_now_flag = True


    def convert_video_to_container(self):

        """Called by self.check_dl_is_correct_type().

        Creates a new media.Channel or media.Playlist object to replace an
        existing media.Video object. The new object is given some of the
        properties of the old one.

        This function doesn't destroy the old object; DownloadManager.run()
        handles that.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 3931 convert_video_to_container')

        app_obj = self.download_manager_obj.app_obj
        old_video_obj = self.download_item_obj.media_data_obj
        container_obj = old_video_obj.parent_obj

        # Some media.Folder objects cannot contain channels or playlists (for
        #   example, the 'Unsorted Videos' folder)
        # If that is the case, the new channel/playlist is created without a
        #   parent. Otherwise, it is created at the same location as the
        #   original media.Video object
        if container_obj.restrict_mode != 'open':
            container_obj = None

        # Decide on a name for the new channel/playlist, e.g. 'channel_1' or
        #   'playlist_4'. The name must not already be in use. The user can
        #   customise the name when they're ready
        name = utils.find_available_name(
            app_obj,
            # e.g. 'channel'
            app_obj.operation_convert_mode,
            # Allow 'channel_1', if available
            1,
        )

        # (Prevent any possibility of an infinite loop by giving up after
        #   thousands of attempts)
        name = None
        new_container_obj = None

        for n in range (1, 9999):
            test_name = app_obj.operation_convert_mode + '_'  + str(n)
            if not test_name in app_obj.media_name_dict:
                name = test_name
                break

        if name is not None:

            # Create the new channel/playlist. Very unlikely that the old
            #   media.Video object has its .dl_sim_flag set, but we'll use it
            #   nonetheless
            if app_obj.operation_convert_mode == 'channel':

                new_container_obj = app_obj.add_channel(
                    name,
                    container_obj,      # May be None
                    source = old_video_obj.source,
                    dl_sim_flag = old_video_obj.dl_sim_flag,
                )

            else:

                new_container_obj = app_obj.add_playlist(
                    name,
                    container_obj,      # May be None
                    source = old_video_obj.source,
                    dl_sim_flag = old_video_obj.dl_sim_flag,
                )

        if new_container_obj is None:

            # New channel/playlist could not be created (for some reason), so
            #   stop downloading from this URL
            self.stop()
            media_data_obj.set_error(
                '\'' + media_data_obj.name + '\' ' + _(
                    'This video has a URL that points to a channel or a' \
                    + ' playlist, not a video',
                ),
            )

        else:

            # Update IVs for the new channel/playlist object
            new_container_obj.set_options_obj(old_video_obj.options_obj)
            new_container_obj.set_source(old_video_obj.source)

            # Add the new channel/playlist to the Video Index (but don't
            #   select it)
            app_obj.main_win_obj.video_index_add_row(new_container_obj, True)

            # Add the new channel/playlist to the download manager's list of
            #   things to download...
            new_download_item_obj \
            = self.download_manager_obj.download_list_obj.create_item(
                new_container_obj,
                self.download_item_obj.scheduled_obj,
                self.download_item_obj.operation_type,
                False,                  # priority_flag
                self.download_item_obj.ignore_limits_flag,
            )
            # ...and add a row the Progress List
            app_obj.main_win_obj.progress_list_add_row(
                new_download_item_obj.item_id,
                new_download_item_obj.media_data_obj,
            )

            # Stop this download job, allowing the replacement one to start
            self.stop()


    def create_child_process(self, cmd_list):

        """Called by self.do_download() immediately after the call to
        utils.generate_ytdl_system_cmd().

        Based on YoutubeDLDownloader._create_process().

        Executes the system command, creating a new child process which
        executes youtube-dl.

        Args:

            cmd_list (list): Python list that contains the command to execute.

        Returns:

            None on success, or the new value of self.return_code if there's an
                error

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 4053 create_child_process')

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
            # (There is no need to update the media data object's error list,
            #   as the code in self.do_download() will notice the child
            #   process didn't start, and set its own error message)
            self.set_return_code(self.ERROR)


    def extract_filename(self, input_data):

        """Called by self.confirm_sim_video() and .extract_stdout_data().

        Based on the extract_data() function in youtube-dl-gui's
        downloaders.py.

        Extracts various components of a filename.

        Args:

            input_data (str): Full path to a file which has been downloaded
                and saved to the filesystem

        Returns:

            Returns the path, filename and extension components of the full
                file path.

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 4104 extract_filename')

        path, fullname = os.path.split(input_data.strip("\""))
        filename, extension = os.path.splitext(fullname)

        return path, filename, extension


    def extract_stdout_data(self, stdout):

        """Called by self.do_download().

        Based on the extract_data() function in youtube-dl-gui's
        downloaders.py.

        Extracts youtube-dl statistics from the child process.

        Args:

            stdout (str): String that contains a line from the child process
                STDOUT (i.e., a message from youtube-dl)

        Returns:

            Python dictionary in a standard format also used by the main window
            code. Dictionaries in this format are generally called
            'dl_stat_dict' (or some variation of it).

            The returned dictionary can be empty if there is no data to
            extract, otherwise it contains one or more of the following keys:

            'status'         : Contains the status of the download
            'path'           : Destination path
            'filename'       : The filename without the extension
            'extension'      : The file extension
            'percent'        : The percentage of the video being downloaded
            'eta'            : Estimated time for the completion of the
                                download
            'speed'          : Download speed
            'filesize'       : The size of the video file being downloaded
            'playlist_index' : The playlist index of the current video file
                                being downloaded
            'playlist_size'  : The number of videos in the playlist
            'dl_sim_flag'    : Flag set to True if we are simulating downloads
                                for this media data object, or False if we
                                actually downloading videos (set below)

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 4154 extract_stdout_data')

        # Import the media data object (for convenience)
        media_data_obj = self.download_item_obj.media_data_obj

        # Initialise the dictionary with default key-value pairs for the main
        #   window to display, to be overwritten (if possible) with new key-
        #   value pairs as this function interprets the STDOUT message
        dl_stat_dict = {
            'playlist_index': self.video_num,
            'playlist_size': self.video_total,
            'dl_sim_flag': self.dl_sim_flag,
        }

        # If STDOUT has not been received by this function, then the main
        #   window can be passed just the default key-value pairs
        if not stdout:
            return dl_stat_dict

        # In some cases, we want to preserve the multiple successive whitespace
        #   characters in the STDOUT message, in order to extract filenames
        #   in their original form
        # In other cases, we just eliminate multiple successive whitespace
        #   characters
        stdout_with_spaces_list = stdout.split(' ')
        stdout_list = stdout.split()

        # (Flag set to True when self.confirm_new_video(), etc, are called)
        confirm_flag = False

        # Extract the data
        stdout_list[0] = stdout_list[0].lstrip('\r')
        if stdout_list[0] == '[download]':

            dl_stat_dict['status'] = formats.ACTIVE_STAGE_DOWNLOAD

            # Get path, filename and extension
            if stdout_list[1] == 'Destination:':
                path, filename, extension = self.extract_filename(
                    ' '.join(stdout_with_spaces_list[2:]),
                )

                dl_stat_dict['path'] = path
                dl_stat_dict['filename'] = filename
                dl_stat_dict['extension'] = extension

                # v2.3.013 - the path to the subtitles file is being mistaken
                #   for the path to the video file here. Only use the
                #   destination if the path is a recognised video/audio format
                #   (and if we don't already have it)
                short_ext = extension[1:]
                if self.temp_path is None \
                and (
                    short_ext in formats.VIDEO_FORMAT_LIST \
                    or short_ext in formats.AUDIO_FORMAT_LIST
                ):
                    self.set_temp_destination(path, filename, extension)

            # Get progress information
            if '%' in stdout_list[1]:
                if stdout_list[1] != '100%':
                    dl_stat_dict['percent'] = stdout_list[1]
                    dl_stat_dict['eta'] = stdout_list[7]
                    dl_stat_dict['speed'] = stdout_list[5]
                    dl_stat_dict['filesize'] = stdout_list[3]

                else:
                    dl_stat_dict['percent'] = '100%'
                    dl_stat_dict['eta'] = ''
                    dl_stat_dict['speed'] = ''
                    dl_stat_dict['filesize'] = stdout_list[3]

                    # If the most recently-received filename isn't one used by
                    #   FFmpeg, then this marks the end of a video download
                    # (See the comments in self.__init__)
                    if len(stdout_list) > 4 \
                    and stdout_list[4] == 'in' \
                    and self.temp_filename is not None \
                    and not re.match(r'.*\.f\d{1,3}$', self.temp_filename):

                        self.confirm_new_video(
                            self.temp_path,
                            self.temp_filename,
                            self.temp_extension,
                        )

                        self.reset_temp_destination()
                        confirm_flag = True

            # Get playlist information (when downloading a channel or a
            #   playlist, this line is received once per video)
            if stdout_list[1] == 'Downloading' and stdout_list[2] == 'video':
                dl_stat_dict['playlist_index'] = stdout_list[3]
                self.video_num = stdout_list[3]
                dl_stat_dict['playlist_size'] = stdout_list[5]
                self.video_total = stdout_list[5]

                # If youtube-dl is about to download a channel or playlist into
                #   a media.Video object, decide what to do to prevent it
                if not self.dl_classic_flag:
                    self.check_dl_is_correct_type()

            # Remove the 'and merged' part of the STDOUT message when using
            #   FFmpeg to merge the formats
            if stdout_list[-3] == 'downloaded' and stdout_list[-1] == 'merged':
                stdout_list = stdout_list[:-2]
                stdout_with_spaces_list = stdout_with_spaces_list[:-2]

                dl_stat_dict['percent'] = '100%'

            # Get file already downloaded status
            if stdout_list[-1] == 'downloaded':

                path, filename, extension = self.extract_filename(
                    ' '.join(stdout_with_spaces_list[1:-4]),
                )

                # v2.3.013 - same problem as above
                short_ext = extension[1:]
                if short_ext in formats.VIDEO_FORMAT_LIST \
                or short_ext in formats.AUDIO_FORMAT_LIST:

                    dl_stat_dict['status'] = formats.COMPLETED_STAGE_ALREADY
                    dl_stat_dict['path'] = path
                    dl_stat_dict['filename'] = filename
                    dl_stat_dict['extension'] = extension
                    self.reset_temp_destination()

                    self.confirm_old_video(path, filename, extension)
                    confirm_flag = True

            # Get filesize abort status
            if stdout_list[-1] == 'Aborting.':
                dl_stat_dict['status'] = formats.ERROR_STAGE_ABORT

            # When checking for missing videos, respond to the 'has already
            #   been recorded in archive' message (which is otherwise ignored)
            if not confirm_flag \
            and self.missing_video_check_list:

                match = re.search(
                    r'^\[download\]\s(.*)\shas already been recorded in' \
                    + ' archive$',
                    stdout,
                )

                if match:
                    self.confirm_archived_video(match.group(1))

        elif stdout_list[0] == '[hlsnative]':

            # Get information from the native HLS extractor (see
            #   https://github.com/rg3/youtube-dl/blob/master/youtube_dl/
            #       downloader/hls.py#L54
            dl_stat_dict['status'] = formats.ACTIVE_STAGE_DOWNLOAD

            if len(stdout_list) == 7:
                segment_no = float(stdout_list[6])
                current_segment = float(stdout_list[4])

                # Get the percentage
                percent = '{0:.1f}%'.format(current_segment / segment_no * 100)
                dl_stat_dict['percent'] = percent

        # youtube-dl uses [ffmpeg], yt-dlp uses [Merger]
        elif stdout_list[0] == '[ffmpeg]' or stdout_list[0] == '[Merger]':

            # Using FFmpeg, not the the native HLS extractor
            # A successful video download is announced in one of several ways.
            #   Use the first announcement to update self.video_check_dict, and
            #   ignore subsequent announcements
            dl_stat_dict['status'] = formats.ACTIVE_STAGE_POST_PROCESS

            # Get the final file extension after the merging process has
            #   completed
            if stdout_list[1] == 'Merging':
                path, filename, extension = self.extract_filename(
                    ' '.join(stdout_with_spaces_list[4:]),
                )

                dl_stat_dict['path'] = path
                dl_stat_dict['filename'] = filename
                dl_stat_dict['extension'] = extension
                self.reset_temp_destination()

                self.confirm_new_video(path, filename, extension)

            # Get the final file extension after simple FFmpeg post-processing
            #   (i.e. not after a file merge)
            if stdout_list[1] == 'Destination:':
                path, filename, extension = self.extract_filename(
                    ' '.join(stdout_with_spaces_list[2:]),
                )

                dl_stat_dict['path'] = path
                dl_stat_dict['filename'] = filename
                dl_stat_dict['extension'] = extension
                self.reset_temp_destination()

                self.confirm_new_video(path, filename, extension)

            # Get final file extension after the recoding process
            if stdout_list[1] == 'Converting':
                path, filename, extension = self.extract_filename(
                    ' '.join(stdout_with_spaces_list[8:]),
                )

                dl_stat_dict['path'] = path
                dl_stat_dict['filename'] = filename
                dl_stat_dict['extension'] = extension
                self.reset_temp_destination()

                self.confirm_new_video(path, filename, extension)

        elif (
            isinstance(media_data_obj, media.Channel)
            and not media_data_obj.rss \
            and stdout_list[0] == '[youtube:channel]' \
        ) or (
            isinstance(media_data_obj, media.Playlist) \
            and not media_data_obj.rss \
            and stdout_list[0] == '[youtube:playlist]' \
            and stdout_list[2] == 'Downloading' \
            and stdout_list[3] == 'webpage'
        ):
            # YouTube only: set the channel/playlist RSS feed, if not already
            #   set, first removing the final colon that should be there
            youtube_id = re.sub('\:*$', '', stdout_list[1])
            media_data_obj.set_rss(youtube_id)

        elif stdout_list[0][0] == '{':

            # JSON data, the result of a simulated download. Convert to a
            #   python dictionary
            if self.dl_sim_flag:

                # (Try/except to check for invalid JSON)
                try:
                    json_dict = json.loads(stdout)

                except:

                    GObject.timeout_add(
                        0,
                        self.download_manager_obj.app_obj.system_error,
                        306,
                        'Invalid JSON data received from server',
                    )

                    return dl_stat_dict

                if json_dict:

                    # For some Classic Mode custom downloads, Tartube performs
                    #   two consecutive download operations: one simulated
                    #   download to fetch URLs of individual videos, and
                    #   another to download each video separately
                    # If we're on the first operation, the dummy media.Video
                    #   object's URL may represent an individual video, or a
                    #   channel or playlist
                    # In both cases, we simply make a list of each video
                    #   detected, along with its metadata, ready for the
                    #   second operation
                    if self.download_item_obj.operation_type == 'classic_sim':

                        # (If the URL can't be retrieved for any reason, then
                        #   just ignore this batch of JSON)
                        if 'webpage_url' in json_dict:
                            self.download_manager_obj.register_classic_url(
                                self.download_item_obj.media_data_obj,
                                json_dict,
                            )

                    # If youtube-dl is about to download a channel or playlist
                    #   into a media.Video object, decide what to do to prevent
                    #   that
                    # The called function returns a True/False value,
                    #   specifically to allow this code block to call
                    #   self.confirm_sim_video when required
                    # v1.3.063 At this point, self.video_num can be None or 0
                    #   for a URL that's an individual video, but > 0 for a URL
                    #   that's actually a channel/playlist
                    elif not self.video_num \
                    or self.check_dl_is_correct_type():
                        self.confirm_sim_video(json_dict)

                    self.video_num += 1
                    dl_stat_dict['playlist_index'] = self.video_num
                    self.video_total += 1
                    dl_stat_dict['playlist_size'] = self.video_total

                    dl_stat_dict['status'] = formats.ACTIVE_STAGE_CHECKING

                    # YouTube only: set the channel/playlist RSS feed, if not
                    #   already set
                    if isinstance(media_data_obj, media.Channel) \
                    and not media_data_obj.rss \
                    and 'channel_id' in json_dict \
                    and json_dict['channel_id'] \
                    and utils.is_youtube(media_data_obj.source):
                        media_data_obj.set_rss(json_dict['channel_id'])

                    elif isinstance(media_data_obj, media.Playlist) \
                    and not media_data_obj.rss \
                    and 'playlist_id' in json_dict \
                    and json_dict['playlist_id'] \
                    and utils.is_youtube(media_data_obj.source):
                        media_data_obj.set_rss(json_dict['playlist_id'])

        elif stdout_list[0][0] != '[' or stdout_list[0] == '[debug]':

            # (Just ignore this output)
            return dl_stat_dict

        else:

            # The download has started
            dl_stat_dict['status'] = formats.ACTIVE_STAGE_PRE_PROCESS

        return dl_stat_dict


    def extract_stdout_status(self, dl_stat_dict):

        """Called by self.do_download() immediately after a call to
        self.extract_stdout_data().

        Based on YoutubeDLDownloader._extract_info().

        If the job's status is formats.COMPLETED_STAGE_ALREADY or
        formats.ERROR_STAGE_ABORT, translate that into a new value for the
        return code, and then use that value to actually set self.return_code
        (which halts the download).

        Args:

            dl_stat_dict (dict): The Python dictionary returned by the call to
                self.extract_stdout_data(), in the standard form described by
                the comments for that function

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 4478 extract_stdout_status')

        if 'status' in dl_stat_dict:
            if dl_stat_dict['status'] == formats.COMPLETED_STAGE_ALREADY:
                self.set_return_code(self.ALREADY)
                dl_stat_dict['status'] = None

            if dl_stat_dict['status'] == formats.ERROR_STAGE_ABORT:
                self.set_return_code(self.FILESIZE_ABORT)
                dl_stat_dict['status'] = None


    def is_child_process_alive(self):

        """Called by self.do_download() and self.stop().

        Based on YoutubeDLDownloader._proc_is_alive().

        Called continuously during the self.do_download() loop to check whether
        the child process has finished or not.

        Returns:

            True if the child process is alive, otherwise returns False

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 4506 is_child_process_alive')

        if self.child_process is None:
            return False

        return self.child_process.poll() is None


    def is_debug(self, stderr):

        """Called by self.do_download().

        Based on YoutubeDLDownloader._is_warning().

        After the child process has terminated with an error of some kind,
        checks the STERR message to see if it's an error or just a debug
        message (generated then youtube-dl verbose output is turned on).

        Args:

            stderr (str): A message from the child process STDERR

        Returns:

            True if the STDERR message is a youtube-dl debug message, False if
                it's an error

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 4536 is_debug')

        return stderr.split(' ')[0] == '[debug]'


    def is_ignorable(self, stderr):

        """Called by self.do_download().

        Before testing a STDERR message, see if it's one of the frequent
        messages which the user has opted to ignore (if any).

        Args:

            stderr (str): A message from the child process STDERR

        Returns:

            True if the STDERR message is ignorable, False if it should be
                tested further

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 4560 is_ignorable')

        app_obj = self.download_manager_obj.app_obj
        media_data_obj = self.download_item_obj.media_data_obj

        if (
            app_obj.ignore_http_404_error_flag \
            and (
                re.search(
                    r'unable to download video data\: HTTP Error 404',
                    stderr,
                ) or re.search(
                    r'Unable to extract video data',
                    stderr,
                )
            )
        ) or (
            app_obj.ignore_data_block_error_flag \
            and re.search(r'Did not get any data blocks', stderr)
        ) or (
            app_obj.ignore_merge_warning_flag \
            and re.search(
                r'Requested formats are incompatible for merge',
                stderr,
            )
        ) or (
            app_obj.ignore_missing_format_error_flag \
            and re.search(
                r'No video formats found; please report this issue',
                stderr,
            )
        ) or (
            app_obj.ignore_no_annotations_flag \
            and re.search(
                r'There are no annotations to write',
                stderr,
            )
        ) or (
            app_obj.ignore_no_subtitles_flag \
            and re.search(
                r'video doesn\'t have subtitles',
                stderr,
            )
        ) or (
            app_obj.ignore_yt_age_restrict_flag \
            and (
                re.search(
                    r'ERROR\: Content Warning',
                    stderr,
                ) or re.search(
                    r'This video may be inappropriate for some users',
                    stderr,
                ) or re.search(
                    r'Sign in to confirm your age',
                    stderr,
                )
            )
        ) or (
            app_obj.ignore_yt_copyright_flag \
            and (
                re.search(
                    r'This video contains content from.*copyright grounds',
                    stderr,
                ) or re.search(
                    r'Sorry about that\.',
                    stderr,
                )
            )
        ) or (
            app_obj.ignore_yt_payment_flag \
            and re.search(
                r'This video requires payment to watch',
                stderr,
            )

        ) or (
            app_obj.ignore_yt_uploader_deleted_flag \
            and (
                re.search(
                    r'The uploader has not made this video available',
                    stderr,
                )
            )
        ) or re.search(r'This live event will begin', stderr) \
        or re.search(r'Premiere will begin', stderr) \
        or re.search(r'Premieres in', stderr):
            # This message is ignorable
            return True

        # Check the custom list of messages
        for item in app_obj.ignore_custom_msg_list:
            if (
                (not app_obj.ignore_custom_regex_flag) \
                and stderr.find(item) > -1
            ) or (
                app_obj.ignore_custom_regex_flag and re.search(item, stderr)
            ):
                # This message is ignorable
                return True

        # This message is not ignorable
        return False


    def is_network_error(self, stderr):

        """Called by self.do_download().

        Try to detect network errors, indicating a stalled download.

        youtube-dl's output is system-dependent, so this function may not
        detect every type of network error.

        Args:

            stderr (str): A message from the child process STDERR

        Returns:

            True if the STDERR message seems to be a network error, False if it
                should be tested further

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 4561 is_network_error')

        # v2.3.012, this error is seen on MS Windows:
        #   unable to download video data: <urlopen error [WinError 10060] A
        #   connection attempt failed because the connected party did not
        #   properly respond after a period of time, or established connection
        #   failed because connected host has failed to respond>
        # Don't know yet what the equivalent on other operating systems is, so
        #   we'll detect the first part, which is a string generated by
        #   youtube-dl itself

        if re.search(r'unable to download video data', stderr):
            return True
        else:
            return False


    def is_warning(self, stderr):

        """Called by self.do_download().

        Based on YoutubeDLDownloader._is_warning().

        After the child process has terminated with an error of some kind,
        checks the STERR message to see if it's an error or just a warning.

        Args:

            stderr (str): A message from the child process STDERR

        Returns:

            True if the STDERR message is a warning, False if it's an error

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 4684 is_warning')

        return stderr.split(':')[0] == 'WARNING'


    def last_data_callback(self):

        """Called by self.do_download().

        Based on YoutubeDLDownloader._last_data_hook().

        After the child process has finished, creates a new Python dictionary
        in the standard form described by self.extract_stdout_data().

        Sets key-value pairs in the dictonary, then passes it to the parent
        downloads.DownloadWorker object, confirming the result of the child
        process.

        The new key-value pairs are used to update the main window.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 4706 last_data_callback')

        dl_stat_dict = {}

        if self.return_code == self.OK:
            dl_stat_dict['status'] = formats.COMPLETED_STAGE_FINISHED
        elif self.return_code == self.ERROR:
            dl_stat_dict['status'] = formats.MAIN_STAGE_ERROR
            dl_stat_dict['eta'] = ''
            dl_stat_dict['speed'] = ''
        elif self.return_code == self.WARNING:
            dl_stat_dict['status'] = formats.COMPLETED_STAGE_WARNING
            dl_stat_dict['eta'] = ''
            dl_stat_dict['speed'] = ''
        elif self.return_code == self.STOPPED:
            dl_stat_dict['status'] = formats.ERROR_STAGE_STOPPED
            dl_stat_dict['eta'] = ''
            dl_stat_dict['speed'] = ''
        elif self.return_code == self.ALREADY:
            dl_stat_dict['status'] = formats.COMPLETED_STAGE_ALREADY
        elif self.return_code == self.STALLED:
            dl_stat_dict['status'] = formats.MAIN_STAGE_STALLED
        else:
            dl_stat_dict['status'] = formats.ERROR_STAGE_ABORT

        # Use some empty values in dl_stat_dict so that the Progress tab
        #   doesn't show arbitrary data from the last file downloaded
        # Exception: in Classic Mode, don't do that for self.ALREADY, otherwise
        #   the filename will never be visible
        if not self.dl_classic_flag or self.return_code != self.ALREADY:
            dl_stat_dict['filename'] = ''
            dl_stat_dict['extension'] = ''
        dl_stat_dict['percent'] = ''
        dl_stat_dict['eta'] = ''
        dl_stat_dict['speed'] = ''
        dl_stat_dict['filesize'] = ''

        # The True argument shows that this function is the caller
        self.download_worker_obj.data_callback(dl_stat_dict, True)


    def set_return_code(self, code):

        """Called by self.do_download(), .create_child_process(),
        .extract_stdout_status() and .stop().

        Based on YoutubeDLDownloader._set_returncode().

        After the child process has terminated with an error of some kind,
        sets a new value for self.return_code, but only if the new return code
        is higher in the hierarchy of return codes than the current value.

        Args:

            code (int): A return code in the range 0-5

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 4760 set_return_code')

        if code >= self.return_code:
            self.return_code = code


    def set_temp_destination(self, path, filename, extension):

        """Called by self.extract_stdout_data()."""

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 4771 set_temp_destination')

        self.temp_path = path
        self.temp_filename = filename
        self.temp_extension = extension


    def reset_temp_destination(self):

        """Called by self.extract_stdout_data()."""

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 4783 reset_temp_destination')

        self.temp_path = None
        self.temp_filename = None
        self.temp_extension = None


    def stop(self):

        """Called by DownloadWorker.close() and also by
        mainwin.MainWin.on_progress_list_stop_now().

        Terminates the child process and sets this object's return code to
        self.STOPPED.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 4800 stop')

        if self.is_child_process_alive():

            if os.name == 'nt':
                # os.killpg is not available on MS Windows (see
                #   https://bugs.python.org/issue5115 )
                self.child_process.kill()

                # When we kill the child process on MS Windows the return code
                #   gets set to 1, so we want to reset the return code back to
                #   0
                self.child_process.returncode = 0

            else:
                os.killpg(self.child_process.pid, signal.SIGKILL)

            self.set_return_code(self.STOPPED)


    def stop_soon(self):

        """Can be called by anything. Currently called by
        mainwin.MainWin.on_progress_list_stop_soon().

        Sets the flag that causes this VideoDownloader to stop after the
        current video.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 4830 stop_soon')

        self.stop_soon_flag = True


class ClipDownloader(object):

    """Called by downloads.DownloadWorker.run_clip_slice_downloader().

    A modified VideoDownloader to download one or more video clips from a
    specified video (rather than downloading the complete video).

    Optionally concatenates the clips back together, which has the effect of
    removing one or more slices from a video.

    Python class to create multiple system child processes, one for each clip.

    Reads from the child process STDOUT and STDERR, having set up a
    downloads.PipeReader object to do so in an asynchronous way.

    Sets self.return_code to a value in the range 0-5, described below. The
    parent downloads.DownloadWorker object checks that return code once this
    object's child process has finished.

    Args:

        download_manager_obj (downloads.DownloadManager): The download manager
            object handling the entire download operation

        download_worker_obj (downloads.DownloadWorker): The parent download
            worker object. The download manager uses multiple workers to
            implement simultaneous downloads. The download manager checks for
            free workers and, when it finds one, assigns it a
            download.DownloadItem object. When the worker is assigned a
            download item, it creates a new instance of this object to
            interface with youtube-dl, and waits for this object to return a
            return code

        download_item_obj (downloads.DownloadItem): The download item object
            describing the URL from which youtube-dl should download clip(s)

    Warnings:

        The calling function is responsible for calling the close() method
        when it's finished with this object, in order for this object to
        properly close down.

    """


    # Attributes (the same set used by VideoDownloader; not all of them are
    #   used by ClipDownloader)


    # Valid values for self.return_code. The larger the number, the higher in
    #   the hierarchy of return codes.
    # Codes lower in the hierarchy (with a smaller number) cannot overwrite
    #   higher in the hierarchy (with a bigger number)
    #
    # 0 - The download operation completed successfully
    OK = 0
    # 1 - A warning occured during the download operation
    WARNING = 1
    # 2 - An error occured during the download operation
    ERROR = 2
    # 3 - The corresponding url video file was larger or smaller from the given
    #   filesize limit
    FILESIZE_ABORT = 3
    # 4 - The video(s) for the specified URL have already been downloaded
    ALREADY = 4
    # 5 - The download operation was stopped by the user
    STOPPED = 5
    # 6 - The download operation has stalled. The parent worker can restart it,
    #   if required
    STALLED = -1


    # Standard class methods


    def __init__(self, download_manager_obj, download_worker_obj, \
    download_item_obj):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 2464 __init__')

        # IV list - class objects
        # -----------------------
        # The downloads.DownloadManager object handling the entire download
        #   operation
        self.download_manager_obj = download_manager_obj
        # The parent downloads.DownloadWorker object
        self.download_worker_obj = download_worker_obj
        # The downloads.DownloadItem object describing the URL from which
        #   youtube-dl should download video(s)
        self.download_item_obj = download_item_obj

        # This object reads from the child process STDOUT and STDERR in an
        #   asynchronous way
        # Standard Python synchronised queue classes
        self.stdout_queue = queue.Queue()
        self.stderr_queue = queue.Queue()
        # The downloads.PipeReader objects created to handle reading from the
        #   pipes
        self.stdout_reader = PipeReader(self.stdout_queue)
        self.stderr_reader = PipeReader(self.stderr_queue)

        # The child process created by self.create_child_process()
        self.child_process = None


        # IV list - other
        # ---------------
        # The current return code, using values in the range 0-5, as described
        #   above
        # The value remains set to self.OK unless we encounter any problems
        # The larger the number, the higher in the hierarchy of return codes.
        #   Codes lower in the hierarchy (with a smaller number) cannot
        #   overwrite higher in the hierarchy (with a bigger number)
        self.return_code = self.OK
        # The time (in seconds) between iterations of the loop in
        #   self.do_download_clips()
        self.sleep_time = 0.1

        # Flag set to True if this download operation was launched from the
        #   Classic Mode tab, False if not (set below)
        self.dl_classic_flag = False
        # Flag set to True if an attempt to copy an original videos' thumbnail
        #   fails (in which case, don't try again)
        self.thumb_copy_fail_flag = False

        # Flag set to True by a call from any function to self.stop_soon()
        # After being set to True, this ClipDownloader should give up after
        #   the next clip has been downloaded
        self.stop_soon_flag = False
        # When self.stop_soon_flag is True, the next call to
        #   self.extract_stdout_data() for a downloaded clip sets this flag to
        #   True, informing self.do_download_clips() that it can stop the child
        #   process
        self.stop_now_flag = False

        # Named for compatibility with VideoDownloader, both IVs are set to the
        #   number of clips that have been downloaded
        self.video_num = 0
        self.video_total = 0

        # Output generated by youtube-dl/FFmpeg may vary, depending on the
        #   file format specified. We have to record every file path
        #   we receive; the last path received is the one that remains on the
        #   filesystem (earlier ones are generally deleted).
        # These two variables are reset at the beginning/end of every clip
        # The file path currently being downloaded/processed
        self.dl_path = None
        # Flag set to True when youtube-dl/FFmpeg appears to have finished
        #   downloading/post-processing the clip
        self.dl_confirm_flag = False

        # Dictionary of clip tiles used during this operation (i.e. when
        #   splitting a video into clips), used to re-name duplicates
        # Not used when removing video slices
        self.clip_title_dict = {}

        # Code
        # ----
        # Initialise IVs
        if self.download_item_obj.operation_classic_flag:
            self.dl_classic_flag = True


    # Public class methods


    def do_download_clips(self):

        """Called by downloads.DownloadWorker.run_clip_slice_downloader().

        Using the URL described by self.download_item_obj (which must
        represent a media.Video object, during a 'custom_real' or
        'classic_custom' download operation), downloads a series of one or more
        clips, using the timestamps specified by the media.Video itself.

        Returns:

            The final return code, a value in the range 0-5 (as described
                above)

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 2691 do_download_clips')

        # Import the main application and video object (for convenience)
        app_obj = self.download_manager_obj.app_obj
        orig_video_obj = self.download_item_obj.media_data_obj

        # Set the default return code. Everything is OK unless we encounter any
        #   problems
        self.return_code = self.OK

        if not self.dl_classic_flag:

            # Reset the errors/warnings stored in the media data object, the
            #   last time it was checked/downloaded
            self.download_item_obj.media_data_obj.reset_error_warning()

        # Re-extract timestamps from the video's .info.json or description
        #   file, if allowed
        # (No point doing it, if the temporary buffer is set)
        if not app_obj.temp_stamp_list:

            if app_obj.video_timestamps_re_extract_flag \
            and not orig_video_obj.stamp_list:
                app_obj.update_video_from_json(orig_video_obj, 'chapters')

            if app_obj.video_timestamps_re_extract_flag \
            and not orig_video_obj.stamp_list:
                orig_video_obj.extract_timestamps_from_descrip(app_obj)

            # Check that at least one timestamp now exists
            if not orig_video_obj.stamp_list:

                app_obj.main_win_obj.output_tab_write_stderr(
                    self.download_worker_obj.worker_id,
                    _('No timestamps defined in video\'s timestamp list'),
                )

                self.stop()

                return self.ERROR

        # Set the containing folder, creating a media.Folder object and/or a
        #   sub-directory for the video clips, if required
        parent_obj, parent_dir, dest_obj, dest_dir \
        = utils.clip_set_destination(app_obj, orig_video_obj)

        if parent_obj is None:

            # Duplicate media.Folder name, this is a fatal error
            app_obj.main_win_obj.output_tab_write_stderr(
                self.download_worker_obj.worker_id,
                _(
                'FAILED: Can\'t create the destination folder either because' \
                + ' a folder with the same name already exists, or because' \
                + ' new folders can\'t be added to the parent folder',
                ),
            )

            self.stop()

            return self.ERROR

        # If the temporary buffer specifies a timestamp list, use it; otherwise
        #   use the video's actual timestamp list
        if not app_obj.temp_stamp_list:
            stamp_list = orig_video_obj.stamp_list.copy()

        else:
            stamp_list = app_obj.temp_stamp_list.copy()
            # (The temporary buffer, once used, must be emptied immediately)
            app_obj.reset_temp_stamp_list()

        # Download the clips, one at a time
        list_size = len(stamp_list)
        for i in range(list_size):

            # Reset detection variables
            self.dl_path = None
            self.dl_confirm_flag = False

            # List in the form [start_stamp, stop_stamp, clip_title]
            # If 'stop_stamp' is not specified, then 'start_stamp' of the next
            #   clip is used. If there are no more clips, then this clip will
            #   end at the end of the video
            start_stamp, stop_stamp, clip_title \
            = utils.clip_extract_data(stamp_list, i)

            # Set a (hopefully unique) clip title
            clip_title = utils.clip_prepare_title(
                app_obj,
                orig_video_obj,
                self.clip_title_dict,
                clip_title,
                i + 1,
                list_size,
            )

            self.clip_title_dict[clip_title] = None

            # Prepare a system command...
            if self.download_manager_obj.custom_dl_obj is not None:
                divert_mode \
                = self.download_manager_obj.custom_dl_obj.divert_mode
            else:
                divert_mode = None

            cmd_list = utils.generate_split_system_cmd(
                app_obj,
                orig_video_obj,
                self.download_worker_obj.options_list.copy(),
                dest_dir,
                clip_title,
                start_stamp,
                stop_stamp,
                self.download_manager_obj.custom_dl_obj,
                divert_mode,
                self.dl_classic_flag,
            )

            # ...display it in the Output tab (if required)...
            if app_obj.ytdl_output_system_cmd_flag:
                app_obj.main_win_obj.output_tab_write_system_cmd(
                    self.download_worker_obj.worker_id,
                    ' '.join(cmd_list),
                )

            # ...and the terminal (if required)
            if app_obj.ytdl_write_system_cmd_flag:
                print(' '.join(cmd_list))

            # Write an additional message in the Output tab, in the same style
            #   as those produced by youtube-dl/FFmpeg (and therefore not
            #   translated)
            app_obj.main_win_obj.output_tab_write_stdout(
                self.download_worker_obj.worker_id,
                '[' + __main__.__packagename__ + '] Downloading clip ' \
                + str(i + 1) + '/' + str(list_size),
            )

            # Create a new child process using the command
            self.create_child_process(cmd_list)

            # Pass data on to self.download_worker_obj so the main window can
            #   be updated
            self.download_worker_obj.data_callback({
                'playlist_index': i + 1,
                'playlist_size': list_size,
                'status': formats.ACTIVE_STAGE_DOWNLOAD,
                'filename': clip_title,
                # This guarantees the the Classic Progress List shows the clip
                #   title, not the original filename
                'clip_flag': True,
            })

            # So that we can read from the child process STDOUT and STDERR,
            #   attach a file descriptor to the PipeReader objects
            if self.child_process is not None:

                self.stdout_reader.attach_file_descriptor(
                    self.child_process.stdout,
                )

                self.stderr_reader.attach_file_descriptor(
                    self.child_process.stderr,
                )

            # While downloading the media data object, update the callback
            #   function with the status of the current job
            while self.is_child_process_alive():

                # Pause a moment between each iteration of the loop (we don't
                #   want to hog system resources)
                time.sleep(self.sleep_time)

                # Read from the child process STDOUT, and convert into unicode
                #   for Python's convenience
                while not self.stdout_queue.empty():

                    stdout = self.stdout_queue.get_nowait().rstrip()
                    if stdout:

                        # On MS Windows we use cp1252, so that Tartube can
                        #   communicate with the Windows console
                        stdout = stdout.decode(utils.get_encoding(), 'replace')

                        # Remove weird carriage returns that insert empty lines
                        #   into the Output tab
                        stdout = re.sub(r"[\r]+", "", stdout)

                        # Extract output from stdout
                        self.extract_stdout_data(stdout)

                        # Show output in the Output tab (if required)
                        if app_obj.ytdl_output_stdout_flag:

                            app_obj.main_win_obj.output_tab_write_stdout(
                                self.download_worker_obj.worker_id,
                                stdout,
                            )

                        # Show output in the terminal (if required)
                        if app_obj.ytdl_write_stdout_flag:

                            # Git #175, Japanese text may produce a codec error
                            #   here, despite the .decode() call above
                            try:
                                print(
                                    stdout.encode(
                                        utils.get_encoding(),
                                        'replace',
                                    ),
                                )
                            except:
                                print(
                                    'STDOUT text with unprintable characters'
                                )

                # Stop this clip downloader, if required to do so, having just
                #   finished downloading a clip
                if self.stop_now_flag:
                    self.stop()

            # The child process has finished
            while not self.stderr_queue.empty():

                # v2.3.168 I'm not sure that any detectable errors are actually
                #   produced, but nevertheless this section can handle any
                #   such errors

                # Read from the child process STDERR queue (we don't need to
                #   read it in real time), and convert into unicode for
                #   python's convenience
                stderr = self.stderr_queue.get_nowait().rstrip()

                # On MS Windows we use cp1252, so that Tartube can communicate
                #   with the Windows console
                stderr = stderr.decode(utils.get_encoding(), 'replace')

                # After a network error, stop trying to download clips
                if self.is_network_error(stderr):

                    self.stop()
                    self.last_data_callback()
                    return self.STALLED

                # Show output in the Output tab (if required)
                if (app_obj.ytdl_output_stderr_flag):
                    app_obj.main_win_obj.output_tab_write_stderr(
                        self.download_worker_obj.worker_id,
                        stderr,
                    )

                # Show output in the terminal (if required)
                if (app_obj.ytdl_write_stderr_flag):
                    # Git #175, Japanese text may produce a codec error here,
                    #   despite the .decode() call above
                    try:
                        print(stderr.encode(utils.get_encoding(), 'replace'))
                    except:
                        print('STDERR text with unprintable characters')

            # We also set the return code to self.ERROR if the download didn't
            #   start or if the child process return code is greater than 0
            # Original notes from youtube-dl-gui:
            #   NOTE: In Linux if the called script is just empty Python exits
            #       normally (ret=0), so we can't detect this or similar cases
            #       using the code below
            #   NOTE: In Unix a negative return code (-N) indicates that the
            #       child was terminated by signal N (e.g. -9 = SIGKILL)
            if self.child_process is None:
                self.set_return_code(self.ERROR)
                app_obj.main_win_obj.output_tab_write_stderr(
                    self.download_worker_obj.worker_id,
                    _('FAILED: Clip download did not start'),
                )

            elif self.child_process.returncode > 0:
                self.set_return_code(self.ERROR)
                app_obj.main_win_obj.output_tab_write_stderr(
                    self.download_worker_obj.worker_id,
                        _(
                        'FAILED: Child process exited with non-zero code: {}'
                        ).format(self.child_process.returncode),
                )

            # General error handling
            if self.return_code != self.OK:

                break

            # Deal with a confirmed download (if any)
            if self.dl_path is not None and self.dl_confirm_flag:

                self.confirm_video_clip(
                    dest_obj,
                    dest_dir,
                    orig_video_obj,
                    clip_title
                )

        # If at least one clip was extracted...
        if self.video_total:

            # ...then the number of video downloads must be incremented
            self.download_manager_obj.register_video('clip')

            # Delete the original video, if required, and if it's not inside a
            #   channel/playlist
            # (Don't bother trying to delete a 'dummy' media.Video object, for
            #   download operations launched from the Classic Mode tab)
            if app_obj.split_video_auto_delete_flag \
            and not isinstance(orig_video_obj.parent_obj, media.Channel) \
            and not isinstance(orig_video_obj.parent_obj, media.Playlist) \
            and not orig_video_obj.dummy_flag:

                app_obj.delete_video(
                    orig_video_obj,
                    True,           # Delete all files
                    True,           # Don't update Video Index yet
                    True,           # Don't update Video Catalogue yet
                )

            # Open the destination directory, if required to do so
            if dest_dir is not None \
            and app_obj.split_video_auto_open_flag:
                utils.open_file(app_obj, dest_dir)

        # Pass a dictionary of values to downloads.DownloadWorker, confirming
        #   the result of the job. The values are passed on to the main
        #   window
        self.last_data_callback()

        # Pass the result back to the parent downloads.DownloadWorker object
        return self.return_code


    def do_download_remove_slices(self):

        """Called by downloads.DownloadWorker.run_clip_slice_downloader().

        Modified version of self.do_download_clips().

        The media.Video object specifies one or more video slices that must be
        removed. We start by downloading the video in clips, as before. The
        clips are the portions of the video that we want to keep.

        Then, we concatenate the clips back together, which has the effect of
        'downloading' a video with the specified slices removed.

        Returns:

            The final return code, a value in the range 0-5 (as described
                above)

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 2691 do_download_remove_slices')

        # Import the main application and video object (for convenience)
        app_obj = self.download_manager_obj.app_obj
        orig_video_obj = self.download_item_obj.media_data_obj

        # Set the default return code. Everything is OK unless we encounter any
        #   problems
        self.return_code = self.OK

        if not self.dl_classic_flag:

            # Reset the errors/warnings stored in the media data object, the
            #   last time it was checked/downloaded
            self.download_item_obj.media_data_obj.reset_error_warning()

        # Contact the SponsorBlock server to update the video's slice data, if
        #   allowed
        # (No point doing it, if the temporary buffer is set)
        if not app_obj.temp_slice_list:

            if app_obj.sblock_re_extract_flag \
            and not orig_video_obj.slice_list:
                utils.fetch_slice_data(
                    app_obj,
                    orig_video_obj,
                    self.download_worker_obj.worker_id,
                )

            # Check that at least one slice now exists
            if not orig_video_obj.slice_list:

                app_obj.main_win_obj.output_tab_write_stderr(
                    self.download_worker_obj.worker_id,
                    _('No slices defined in video\'s slice list'),
                )

                self.stop()
                return self.ERROR

        # Create a temporary directory for this video so we don't accidentally
        #   overwrite anything
        parent_dir = orig_video_obj.parent_obj.get_actual_dir(app_obj)
        temp_dir = self.create_temp_dir(orig_video_obj, parent_dir)
        if temp_dir is None:
            return self.ERROR

        # If the temporary buffer specifies a slice list, use it; otherwise
        #   use the video's actual slice list
        if not app_obj.temp_slice_list:
            slice_list = orig_video_obj.slice_list.copy()
            temp_flag = False

        else:
            slice_list = app_obj.temp_slice_list.copy()
            # (The temporary buffer, once used, must be emptied immediately)
            app_obj.reset_temp_slice_list()
            temp_flag = True

        # Convert this list from a list of video slices to be removed, to a
        #   list of video clips to be retained
        # The returned list is in groups of two, in the form
        #   [start_time, stop_time]
        # ...where 'start_time' and 'stop_time' are floating-point values in
        #   seconds. 'stop_time' can be None to signify the end of the video,
        #   but 'start_time' is 0 to signify the start of the video
        clip_list = utils.convert_slices_to_clips(
            app_obj,
            self.download_manager_obj.custom_dl_obj,
            slice_list,
            temp_flag,
        )

        # Download the clips, one at a time
        confirmed_list = []
        count = 0
        list_size = len(clip_list)
        for mini_list in clip_list:

            count += 1
            start_time = mini_list[0]
            stop_time = mini_list[1]

            # Reset detection variables
            self.dl_path = None
            self.dl_confirm_flag = False

            # Prepare a system command...
            if self.download_manager_obj.custom_dl_obj is not None:
                divert_mode \
                = self.download_manager_obj.custom_dl_obj.divert_mode
            else:
                divert_mode = None

            cmd_list = utils.generate_slice_system_cmd(
                app_obj,
                orig_video_obj,
                self.download_worker_obj.options_list.copy(),
                temp_dir,
                count,
                start_time,
                stop_time,
                self.download_manager_obj.custom_dl_obj,
                divert_mode,
                self.dl_classic_flag,
            )

            # ...display it in the Output tab (if required)...
            if app_obj.ytdl_output_system_cmd_flag:
                app_obj.main_win_obj.output_tab_write_system_cmd(
                    self.download_worker_obj.worker_id,
                    ' '.join(cmd_list),
                )

            # ...and the terminal (if required)
            if app_obj.ytdl_write_system_cmd_flag:
                print(' '.join(cmd_list))

            # Write an additional message in the Output tab, in the same style
            #   as those produced by youtube-dl/FFmpeg (and therefore not
            #   translated)
            app_obj.main_win_obj.output_tab_write_stdout(
                self.download_worker_obj.worker_id,
                '[' + __main__.__packagename__ + '] Downloading clip ' \
                + str(count) + '/' + str(list_size),
            )

            # Create a new child process using the command
            self.create_child_process(cmd_list)

            # Pass data on to self.download_worker_obj so the main window can
            #   be updated
            if stop_time is not None:
                clip = 'Clip ' + str(start_time) + 's - ' + str(stop_time) \
                + 's'
            else:
                clip = 'Clip ' + str(start_time) + 's - end'

            self.download_worker_obj.data_callback({
                'playlist_index': count,
                'playlist_size': list_size,
                'status': formats.ACTIVE_STAGE_DOWNLOAD,
                'filename': clip,
            })

            # So that we can read from the child process STDOUT and STDERR,
            #   attach a file descriptor to the PipeReader objects
            if self.child_process is not None:

                self.stdout_reader.attach_file_descriptor(
                    self.child_process.stdout,
                )

                self.stderr_reader.attach_file_descriptor(
                    self.child_process.stderr,
                )

            # While downloading the media data object, update the callback
            #   function with the status of the current job
            while self.is_child_process_alive():

                # Pause a moment between each iteration of the loop (we don't
                #   want to hog system resources)
                time.sleep(self.sleep_time)

                # Read from the child process STDOUT, and convert into unicode
                #   for Python's convenience
                while not self.stdout_queue.empty():

                    stdout = self.stdout_queue.get_nowait().rstrip()
                    if stdout:

                        # On MS Windows we use cp1252, so that Tartube can
                        #   communicate with the Windows console
                        stdout = stdout.decode(utils.get_encoding(), 'replace')

                        # Remove weird carriage returns that insert empty lines
                        #   into the Output tab
                        stdout = re.sub(r"[\r]+", "", stdout)

                        # Extract output from stdout
                        self.extract_stdout_data(stdout)

                        # Show output in the Output tab (if required)
                        if app_obj.ytdl_output_stdout_flag:

                            app_obj.main_win_obj.output_tab_write_stdout(
                                self.download_worker_obj.worker_id,
                                stdout,
                            )

                        # Show output in the terminal (if required)
                        if app_obj.ytdl_write_stdout_flag:

                            # Git #175, Japanese text may produce a codec error
                            #   here, despite the .decode() call above
                            try:
                                print(
                                    stdout.encode(
                                        utils.get_encoding(),
                                        'replace',
                                    ),
                                )
                            except:
                                print(
                                    'STDOUT text with unprintable characters'
                                )

                # Stop this clip downloader, if required to do so, having just
                #   finished downloading a clip
                if self.stop_now_flag:
                    self.stop()

            # The child process has finished
            while not self.stderr_queue.empty():

                # v2.3.168 I'm not sure that any detectable errors are actually
                #   produced, but nevertheless this section can handle any
                #   such errors

                # Read from the child process STDERR queue (we don't need to
                #   read it in real time), and convert into unicode for
                #   python's convenience
                stderr = self.stderr_queue.get_nowait().rstrip()

                # On MS Windows we use cp1252, so that Tartube can communicate
                #   with the Windows console
                stderr = stderr.decode(utils.get_encoding(), 'replace')

                # After a network error, stop trying to download clips
                if self.is_network_error(stderr):

                    self.stop()
                    self.last_data_callback()
                    return self.STALLED

                # Show output in the Output tab (if required)
                if (app_obj.ytdl_output_stderr_flag):
                    app_obj.main_win_obj.output_tab_write_stderr(
                        self.download_worker_obj.worker_id,
                        stderr,
                    )

                # Show output in the terminal (if required)
                if (app_obj.ytdl_write_stderr_flag):
                    # Git #175, Japanese text may produce a codec error here,
                    #   despite the .decode() call above
                    try:
                        print(stderr.encode(utils.get_encoding(), 'replace'))
                    except:
                        print('STDERR text with unprintable characters')

            # We also set the return code to self.ERROR if the download didn't
            #   start or if the child process return code is greater than 0
            # Original notes from youtube-dl-gui:
            #   NOTE: In Linux if the called script is just empty Python exits
            #       normally (ret=0), so we can't detect this or similar cases
            #       using the code below
            #   NOTE: In Unix a negative return code (-N) indicates that the
            #       child was terminated by signal N (e.g. -9 = SIGKILL)
            if self.child_process is None:
                self.set_return_code(self.ERROR)
                app_obj.main_win_obj.output_tab_write_stderr(
                    self.download_worker_obj.worker_id,
                    _('FAILED: Clip download did not start'),
                )

            elif self.child_process.returncode > 0:
                self.set_return_code(self.ERROR)
                app_obj.main_win_obj.output_tab_write_stderr(
                    self.download_worker_obj.worker_id,
                        _(
                        'FAILED: Child process exited with non-zero code: {}'
                        ).format(self.child_process.returncode),
                )

            # General error handling
            if self.return_code != self.OK:

                break

            # Add a confirmed download to the list
            if self.dl_path is not None and self.dl_confirm_flag:

                confirmed_list.append(self.dl_path)
                self.video_num += 1
                self.video_total += 1

        # If fewer clips than expected were downloaded, then don't use any of
        #   them
        if len(confirmed_list) != len(clip_list):

            self.set_return_code(self.ERROR)

            app_obj.main_win_obj.output_tab_write_stderr(
                self.download_worker_obj.worker_id,
                _('FAILED: One or more clips were not downloaded'),
            )

        else:

            # Otherwise, get the video's (original) file extension from the
            #   first clip
            file_path, file_ext = os.path.splitext(confirmed_list[0])

            # Ordinarily, the user will check a video before custom downloading
            #   it. If not, the media.Video object won't have a .file_name set,
            #   which breaks the code below; in that case, we'll have to
            #   generate a name ourselves
            if orig_video_obj.file_name is None:
                fallback_name = _('Video') + ' ' + str(orig_video_obj.dbid)
                orig_video_obj.set_name(fallback_name)
                orig_video_obj.set_nickname(fallback_name)
                orig_video_obj.set_file(fallback_name, file_ext)

            # If there is more than one clip, they must be concatenated to
            #   produce a single video (like the original video, from which the
            #   video slices have been removed)
            if len(confirmed_list) == 1:
                output_path = confirmed_list[0]

            else:
                # For FFmpeg's benefit, write a text file listing every clip
                line_list = []
                clips_file = os.path.abspath(
                    os.path.join(temp_dir, 'clips.txt'),
                )

                for confirmed_path in confirmed_list:
                    line_list.append('file \'' + confirmed_path + '\'')

                with open(clips_file, 'w') as fh:
                    fh.write('\n'.join(line_list))

                # Prepare the FFmpeg command to concatenate the clips together
                output_path = os.path.abspath(
                    os.path.join(
                        temp_dir,
                        orig_video_obj.file_name + file_ext,
                    ),
                )

                cmd_list = [
                    app_obj.ffmpeg_manager_obj.get_executable(),
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

                # ...display it in the Output tab (if required)...
                if app_obj.ytdl_output_system_cmd_flag:
                    app_obj.main_win_obj.output_tab_write_system_cmd(
                        self.download_worker_obj.worker_id,
                        ' '.join(cmd_list),
                    )

                # ...and the terminal (if required)
                if app_obj.ytdl_write_system_cmd_flag:
                    print(' '.join(cmd_list))


                # Create a new child process using the command
                self.create_child_process(cmd_list)

                # Pass data on to self.download_worker_obj so the main window
                #   can be updated
                self.download_worker_obj.data_callback({
                    'playlist_index': self.video_total,
                    'playlist_size': self.video_total,
                    'status': formats.ACTIVE_STAGE_CONCATENATE,
                    'filename': '',
                })

                # So that we can read from the child process STDOUT and STDERR,
                #   attach a file descriptor to the PipeReader objects
                if self.child_process is not None:

                    self.stdout_reader.attach_file_descriptor(
                        self.child_process.stdout,
                    )

                    self.stderr_reader.attach_file_descriptor(
                        self.child_process.stderr,
                    )

                # Wait for the concatenation to finish. We are not bothered
                #   about reading the child process STDOUT/STDERR, since we can
                #   just test for the existence of the output file
                while self.is_child_process_alive():
                    time.sleep(self.sleep_time)

                if not os.path.isfile(output_path):

                    app_obj.main_win_obj.output_tab_write_stderr(
                        self.download_worker_obj.worker_id,
                        _('FAILED: Can\'t concatenate clips'),
                    )

                    return self.ERROR

            # Move the single video file back into the parent directory,
            #   replacing any file of the same name that's already there
            moved_path = os.path.abspath(
                os.path.join(
                    parent_dir,
                    orig_video_obj.file_name + file_ext,
                ),
            )

            if os.path.isfile(moved_path):
                app_obj.remove_file(moved_path)

            if not app_obj.move_file_or_directory(output_path, moved_path):
                app_obj.main_win_obj.output_tab_write_stderr(
                    self.download_worker_obj.worker_id,
                    _(
                        'FAILED: Clips were concatenated, but could not move' \
                        + ' the output file out of the temporary directory',
                    ),
                )

                return self.ERROR

            # Also move metadata files, if they don't already exist in the
            #   parent directory (or its /.data and ./thumbs sub-directories)
            self.move_metadata_files(orig_video_obj, temp_dir, parent_dir)

            # downloads.DownloadManager tracks the number of video slices
            #   removed
            for i in range(len(slice_list)):
                self.download_manager_obj.register_slice()

            # Update Tartube's database
            self.confirm_video_remove_slices(orig_video_obj, moved_path)

        # Delete the temporary directory
        app_obj.remove_directory(temp_dir)

        # Pass a dictionary of values to downloads.DownloadWorker, confirming
        #   the result of the job. The values are passed on to the main
        #   window
        self.last_data_callback()

        # Pass the result back to the parent downloads.DownloadWorker object
        return self.return_code


    def close(self):

        """Can be called by anything.

        Destructor function for this object.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 3101 close')

        # Tell the PipeReader objects to shut down, thus joining their threads
        self.stdout_reader.join()
        self.stderr_reader.join()


    def confirm_video_clip(self, dest_obj, dest_dir, orig_video_obj, \
    clip_title):

        """Called by self.do_download_clips() when a video clip is confirmed as
        having been downloaded.

        Args:

            dest_obj (media.Folder): The folder object into which the new video
                object is to be created

            dest_dir (str): The path to that folder on the filesystem

            orig_video_obj (media.Video): The original video, from which the
                video clip has been split

            clip_title (str): The clip title for the new video, matching its
                filename

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 3102 confirm_video_clip')

        # Import the main application (for convenience)
        app_obj = self.download_manager_obj.app_obj

        # Download confirmed
        self.video_num += 1
        self.video_total += 1
        self.download_manager_obj.register_clip()

        if dest_obj \
        and app_obj.split_video_add_db_flag \
        and not orig_video_obj.dummy_flag:

            # Add the clip to Tartube's database
            clip_video_obj = utils.clip_add_to_db(
                app_obj,
                dest_obj,
                orig_video_obj,
                clip_title,
                self.dl_path,
            )

            if clip_video_obj and not orig_video_obj.dummy_flag:

                # Update the Results List (unless the download operation was
                #   launched from the Classic Mode tab)
                app_obj.main_win_obj.results_list_add_row(
                    self.download_item_obj,
                    clip_video_obj,
                    {},                 # No 'mini_options_dict' to apply
                )

        elif app_obj.split_video_copy_thumb_flag \
        and not self.thumb_copy_fail_flag:

            # The call to utils.clip_add_to_db() copies the original thumbnail,
            #   when required
            # Since we're not going to call that, copy the thumbnail here
            thumb_path = utils.find_thumbnail(app_obj, orig_video_obj)
            if thumb_path is not None:

                _, thumb_ext = os.path.splitext(thumb_path)
                new_path = os.path.abspath(
                    os.path.join(dest_dir, clip_title + thumb_ext),
                )

                try:

                    shutil.copyfile(thumb_path, new_path)

                except:

                    GObject.timeout_add(
                        0,
                        app_obj.system_error,
                        999,
                        _(
                            'Failed to copy the original video\'s' \
                            + ' thumbnail',
                        ),
                    )

                    # Don't try to copy orig_video_obj's thumbnail again
                    self.thumb_copy_fail_flag = True

        # This ClipDownloader can now stop, if required to do so after a clip
        #   has been downloaded
        if self.stop_soon_flag:
            self.stop_now_flag = True


    def confirm_video_remove_slices(self, orig_video_obj, output_path):

        """Called by self.do_download_remove_slices().

        Once a video has been downloaded as a sequence of clips, then
        concatenated into a single video file (thereby removing one or more
        video slices), make sure the medai.Video object is marked as
        downloaded, and update the main window.

        Args:

            orig_video_obj (media.Video): The video to be downloaded

            output_path (str): Full path to the concatenated video

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 2691 confirm_video_remove_slices')

        # Import the main application (for convenience)
        app_obj = self.download_manager_obj.app_obj

        # Special case: don't add videos to the Tartube database
        if orig_video_obj.parent_obj.dl_no_db_flag:
            # (Do nothing, in this case)
            pass

        # Special case: if the download operation was launched from the
        #   Classic Mode tab, then we only need to update the dummy
        #   media.Video object, and to move/remove description/metadata/
        #   thumbnail files, as appropriate
        elif self.dl_classic_flag:

            orig_video_obj.set_dl_flag(True)
            orig_video_obj.set_dummy_path(output_path)

        elif not orig_video_obj.dl_flag:

            # Mark the video as downloaded
            GObject.timeout_add(
                0,
                app_obj.mark_video_downloaded,
                orig_video_obj,
                True,               # Video is downloaded
            )

            # Do add an entry to the Results List (as well as updating the
            #   Video Catalogue, as normal)
            GObject.timeout_add(
                0,
                app_obj.announce_video_download,
                self.download_item_obj,
                orig_video_obj,
                # No call to self.compile_mini_options_dict, because this
                #   function deals with download options like
                #   'move_description' by itself
                {},
            )

        # Register the download with DownloadManager, so that download limits
        #   can be applied, if required
        self.download_manager_obj.register_video('new')

        # Timestamp and slice information is now obsolete for this video, and
        #   can be removed, if required
        if app_obj.slice_video_cleanup_flag:
            orig_video_obj.reset_timestamps()
            orig_video_obj.reset_slices()


    def create_child_process(self, cmd_list):

        """Called by self.do_download_clips() shortly after the call to
        utils.generate_split_system_cmd().

        Based on YoutubeDLDownloader._create_process().

        Executes the system command, creating a new child process which
        executes youtube-dl.

        Args:

            cmd_list (list): Python list that contains the command to execute.

        Returns:

            None on success, or the new value of self.return_code if there's an
                error

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 4053 create_child_process')

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
            # (There is no need to update the media data object's error list,
            #   as the code in self.do_download_clips() will notice the child
            #   process didn't start, and set its own error message)
            self.set_return_code(self.ERROR)


    def create_temp_dir(self, orig_video_obj, parent_dir):

        """Called by self.do_download_remove_slices().

        Before downloading a video in clips, and then concatenating the clips,
        create a temporary directory for the clips so we don't accidentally
        overwrite anything.

        Args:

            orig_video_obj (media.Video): The video to be downloaded

            parent_dir (str): Full path to the parent container's directory

        Return values:

            The temporary directory created on success, None on failure

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 4154 create_temp_dir')

        # Import the main application (for convenience)
        app_obj = self.download_manager_obj.app_obj

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
                app_obj.remove_directory(temp_dir)

            app_obj.make_directory(temp_dir)

            return temp_dir

        except:
            app_obj.main_win_obj.output_tab_write_stderr(
                self.download_worker_obj.worker_id,
                _('FAILED: Can\'t create a temporary folder for video clips'),
            )

            self.stop()

            return None


    def extract_stdout_data(self, stdout):

        """Called by self.do_download_clips().

        Extracts output from the child process.

        Output generated by youtube-dl/FFmpeg may vary, depending on the file
        format specified. We have to record every file path we receive; the
        lsat path received is the one that remains on the filesystem (earlier
        ones are generally deleted).

        Args:

            stdout (str): String that contains a line from the child process
                STDOUT (i.e., a message from youtube-dl)

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 4154 extract_stdout_data')

        # Import the main application (for convenience)
        app_obj = self.download_manager_obj.app_obj

        # Check for a media file being downloaded
        match = re.search(r'^\[download\] Destination\:\s(.*)$', stdout)
        if match:

            self.dl_path = match.group(1)
            return

        match = re.search(r'^\[ffmpeg\] Destination\:\s(.*)$', stdout)
        if match:

            self.dl_path = match.group(1)
            self.dl_confirm_flag = True
            return

        # Check for completion of a media file download
        match = re.search(r'^\[download\] 100% of .* in', stdout)
        if match:

            self.dl_confirm_flag = True
            return

        # Check for confirmation of post-processing
        match = re.search(
            r'^\[ffmpeg\] Merging formats into \"(.*)\"$',
            stdout
        )
        if match:

            self.dl_path = match.group(1)
            self.dl_confirm_flag = True

            return


    def is_child_process_alive(self):

        """Called by self.do_download_clips(), .do_download_remove_slices and
        .stop().

        Based on YoutubeDLDownloader._proc_is_alive().

        Called continuously during the loop to check whether the child process
        has finished or not.

        Returns:

            True if the child process is alive, otherwise returns False

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 4506 is_child_process_alive')

        if self.child_process is None:
            return False

        return self.child_process.poll() is None


    def is_network_error(self, stderr):

        """Called by self.do_download_clips(); an exact copy of the function in
        VideoDownloader.

        Try to detect network errors, indicating a stalled download.

        youtube-dl's output is system-dependent, so this function may not
        detect every type of network error.

        Args:

            stderr (str): A message from the child process STDERR

        Returns:

            True if the STDERR message seems to be a network error, False if it
                should be tested further

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 4561 is_network_error')

        # v2.3.012, this error is seen on MS Windows:
        #   unable to download video data: <urlopen error [WinError 10060] A
        #   connection attempt failed because the connected party did not
        #   properly respond after a period of time, or established connection
        #   failed because connected host has failed to respond>
        # Don't know yet what the equivalent on other operating systems is, so
        #   we'll detect the first part, which is a string generated by
        #   youtube-dl itself

        if re.search(r'unable to download video data', stderr):
            return True
        else:
            return False


    def last_data_callback(self):

        """Called by self.do_download_clips().

        Based on VideoDownloader.last_data_callback().

        After the child process has finished, creates a new Python dictionary
        in the standard form described by self.extract_stdout_data().

        Sets key-value pairs in the dictonary, then passes it to the parent
        downloads.DownloadWorker object, confirming the result of the child
        process.

        The new key-value pairs are used to update the main window.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 4706 last_data_callback')

        dl_stat_dict = {}

        # (Some of these statuses are not actually used, but the code
        #   references them, in case they are added in future)
        if self.return_code == self.OK:
            dl_stat_dict['status'] = formats.COMPLETED_STAGE_FINISHED
        elif self.return_code == self.ERROR:
            dl_stat_dict['status'] = formats.MAIN_STAGE_ERROR
        elif self.return_code == self.WARNING:
            dl_stat_dict['status'] = formats.COMPLETED_STAGE_WARNING
        elif self.return_code == self.STOPPED:
            dl_stat_dict['status'] = formats.ERROR_STAGE_STOPPED
        elif self.return_code == self.ALREADY:
            dl_stat_dict['status'] = formats.COMPLETED_STAGE_ALREADY
        elif self.return_code == self.STALLED:
            dl_stat_dict['status'] = formats.MAIN_STAGE_STALLED
        else:
            dl_stat_dict['status'] = formats.ERROR_STAGE_ABORT

        # In the Classic Progress List, the 'Incoming File' column showed
        #   clipped names. Replace that with the full video name
        dl_stat_dict['filename'] = self.download_item_obj.media_data_obj.name
        dl_stat_dict['clip_flag'] = True

        # The True argument shows that this function is the caller
        self.download_worker_obj.data_callback(dl_stat_dict, True)


    def move_metadata_files(self, orig_video_obj, temp_dir, parent_dir):

        """Called by self.do_download_remove_slices().

        After moving the (concatenated) video file from its temporary directory
        into the parent container's directory, do the same to the metadata
        files.

        Depending on settings in the options.OptionsManager, they may be
        moved into a sub-directory of the parent cotainer's directory instead.

        Args:

            orig_video_obj (media.Video): The video that was downloaded as a
                sequence of clips

            temp_dir (str): Full path to the temporary directory into which the
                video and its metadata files was downloaded

            parent_dir (str): Full path to the parent container's directory

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 4706 move_metadata_files')

        # Import the main application (for convenience)
        app_obj = self.download_manager_obj.app_obj

        # Handle the description file
        options_obj = self.download_worker_obj.options_manager_obj
        if options_obj.options_dict['keep_description']:

            descrip_path = os.path.abspath(
                os.path.join(temp_dir, 'clip_1.description'),
            )

            if os.path.isfile(descrip_path):

                moved_path = os.path.abspath(
                    os.path.join(
                        parent_dir,
                        orig_video_obj.file_name + '.description',
                    ),
                )

                if options_obj.options_dict['move_description']:
                    final_path = os.path.abspath(
                        os.path.join(
                            parent_dir,
                            '.data',
                            orig_video_obj.file_name + '.description',
                        ),
                    )
                else:
                    final_path = moved_path

                if not os.path.isfile(moved_path) \
                and not os.path.isfile(final_path):
                    app_obj.move_file_or_directory(descrip_path, moved_path)

                    # Further move the file into its sub-directory, if
                    #   required, first creating that sub-directory if it
                    #   doesn't exist
                    if options_obj.options_dict['move_description']:
                        utils.move_metadata_to_subdir(
                            app_obj,
                            orig_video_obj,
                            '.description',
                        )

        # Handle the .info.json file
        if options_obj.options_dict['keep_info']:

            json_path = os.path.abspath(
                os.path.join(temp_dir, 'clip_1.info.json'),
            )

            if os.path.isfile(json_path):

                moved_path = os.path.abspath(
                    os.path.join(
                        parent_dir,
                        orig_video_obj.file_name + '.info.json',
                    ),
                )

                if options_obj.options_dict['move_info']:
                    final_path = os.path.abspath(
                        os.path.join(
                            parent_dir,
                            '.data',
                            orig_video_obj.file_name + '.info.json',
                        ),
                    )
                else:
                    final_path = moved_path

                if not os.path.isfile(moved_path) \
                and not os.path.isfile(final_path):
                    app_obj.move_file_or_directory(json_path, moved_path)

                    if options_obj.options_dict['move_info']:
                        utils.move_metadata_to_subdir(
                            app_obj,
                            orig_video_obj,
                            '.info.json',
                        )

        # v2.1.101 - Annotations were removed by YouTube in 2019, so this
        #   feature is not available, and will not be available until the
        #   authors have some annotations to test
#       if options_obj.options_dict['keep_annotations']:
#
#           xml_path = os.path.abspath(
#               os.path.join(temp_dir, 'clip_1.annotations.xml'),
#           )
#
#           if os.path.isfile(xml_path):
#
#               moved_path = os.path.abspath(
#                   os.path.join(
#                       parent_dir,
#                       orig_video_obj.file_name + '.annotations.xml',
#                   ),
#               )
#
#               if options_obj.options_dict['move_annotations']:
#                   final_path = os.path.abspath(
#                       os.path.join(
#                           parent_dir,
#                           '.data',
#                           orig_video_obj.file_name + '.annotations.xml',
#                       ),
#                   )
#               else:
#                   final_path = moved_path
#
#               if not os.path.isfile(moved_path) \
#               and not os.path.isfile(final_path):
#                   app_obj.move_file_or_directory(xml_path, moved_path)
#
#                   if options_obj.options_dict['move_annotations']:
#                       utils.move_metadata_to_subdir(
#                           app_obj,
#                           orig_video_obj,
#                           '.annotations.xml',
#                       )

        # Handle the thumbnail
        if options_obj.options_dict['keep_thumbnail']:

            thumb_path = utils.find_thumbnail_from_filename(
                app_obj,
                temp_dir,
                'clip_1',
            )

            if thumb_path is not None and os.path.isfile(thumb_path):

                name, ext = os.path.splitext(thumb_path)

                moved_path = os.path.abspath(
                    os.path.join(
                        parent_dir,
                        orig_video_obj.file_name + ext,
                    ),
                )

                if not os.path.isfile(moved_path):
                    app_obj.move_file_or_directory(thumb_path, moved_path)

                    # Convert .webp thumbnails to .jpg, if required
                    convert_path = utils.find_thumbnail_webp(
                        app_obj,
                        orig_video_obj,
                    )
                    if convert_path is not None \
                    and not app_obj.ffmpeg_fail_flag \
                    and app_obj.ffmpeg_convert_webp_flag \
                    and not app_obj.ffmpeg_manager_obj.convert_webp(
                        convert_path,
                    ):
                        app_obj.set_ffmpeg_fail_flag(True)
                        GObject.timeout_add(
                            0,
                            app_obj.system_error,
                            999,
                            app_obj.ffmpeg_fail_msg,
                        )

                    # Move to the sub-directory, if required
                    if options_obj.options_dict['move_thumbnail']:
                        utils.move_thumbnail_to_subdir(
                            app_obj,
                            orig_video_obj,
                        )


    def set_return_code(self, code):

        """Called by self.do_download_clips(), .do_download_remove_slices(),
        .create_child_process() and .stop().

        Based on YoutubeDLDownloader._set_returncode().

        After the child process has terminated with an error of some kind,
        sets a new value for self.return_code, but only if the new return code
        is higher in the hierarchy of return codes than the current value.

        Args:

            code (int): A return code in the range 0-5

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 4760 set_return_code')

        if code >= self.return_code:
            self.return_code = code


    def stop(self):

        """Called by DownloadWorker.close() and also by
        mainwin.MainWin.on_progress_list_stop_now().

        Terminates the child process and sets this object's return code to
        self.STOPPED.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 4800 stop')

        if self.is_child_process_alive():

            if os.name == 'nt':
                # os.killpg is not available on MS Windows (see
                #   https://bugs.python.org/issue5115 )
                self.child_process.kill()

                # When we kill the child process on MS Windows the return code
                #   gets set to 1, so we want to reset the return code back to
                #   0
                self.child_process.returncode = 0

            else:
                os.killpg(self.child_process.pid, signal.SIGKILL)

            self.set_return_code(self.STOPPED)


    def stop_soon(self):

        """Can be called by anything. Currently called by
        mainwin.MainWin.on_progress_list_stop_soon().

        Sets the flag that causes this ClipDownloader to stop after the
        current video.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 4830 stop_soon')

        self.stop_soon_flag = True


class StreamDownloader(object):

    """Called by downloads.DownloadWorker.run_stream_downloader().

    Python class to create a system child process. Uses the child process to
    instruct Youtube Stream Capture (YTSC) to download the currently-
    broadcasting livestream associated with the URL described by a
    downloads.DownloadItem object (which is always an individual video).

    Reads from the child process STDOUT, having set up a downloads.PipeReader
    object to do so in an asynchronous way. (STDERR is available, but is
    currently ignored).

    Sets self.return_code to a value in the range 0-5, described below. The
    parent downloads.DownloadWorker object checks that return code once this
    object's child process has finished.

    Args:

        download_manager_obj (downloads.DownloadManager): The download manager
            object handling the entire download operation

        download_worker_obj (downloads.DownloadWorker): The parent download
            worker object. The download manager uses multiple workers to
            implement simultaneous downloads. The download manager checks for
            free workers and, when it finds one, assigns it a
            download.DownloadItem object. When the worker is assigned a
            download item, it creates a new instance of this object to
            interface with youtube-dl, and waits for this object to return a
            return code

        download_item_obj (downloads.DownloadItem): The download item object
            describing the URL from which Youtube Stream Capture should
            download a livestream video.

    Warnings:

        The calling function is responsible for calling the close() method
        when it's finished with this object, in order for this object to
        properly close down.

    """

    # Attributes


    # Valid vlues for self.return_code, following the model established by
    #   downloads.VideoDownloader (but with a smaller set of values)
    # 0 - The download operation completed successfully
    OK = 0
    # 2 - An error occured during the download operation
    ERROR = 2
    # 5 - The download operation was stopped by the user
    STOPPED = 5


    # Standard class methods


    def __init__(self, download_manager_obj, download_worker_obj, \
    download_item_obj):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 4898 __init__')

        # IV list - class objects
        # -----------------------
        # The downloads.DownloadManager object handling the entire download
        #   operation
        self.download_manager_obj = download_manager_obj
        # The parent downloads.DownloadWorker object
        self.download_worker_obj = download_worker_obj
        # The downloads.DownloadItem object describing the URL from which
        #   youtube-dl should download video(s)
        self.download_item_obj = download_item_obj

        # This object reads from the child process STDOUT in an asynchronous
        #   way. STDERR is not read, but for conformity with
        #   downloads.VideoDownloader (and for future changes to the code), it
        #   is available
        # Standard Python synchronised queue classes
        self.stdout_queue = queue.Queue()
        self.stderr_queue = queue.Queue()
        # The downloads.PipeReader objects created to handle reading from the
        #   pipes
        self.stdout_reader = PipeReader(self.stdout_queue)
        self.stderr_reader = PipeReader(self.stderr_queue)

        # The child process created by self.create_child_process()
        self.child_process = None


        # IV list - other
        # ---------------
        # The current return code, using values in the range 0-5, as described
        #   above
        # The value remains set to self.OK unless we encounter any problems
        # The larger the number, the higher in the hierarchy of return codes.
        #   Codes lower in the hierarchy (with a smaller number) cannot
        #   overwrite higher in the hierarchy (with a bigger number)
        self.return_code = self.OK
        # The time (in seconds) between iterations of the loop in
        #   self.do_child_process()
        self.sleep_time = 0.1

        # Name of the two YTSC scipts used
        self.ytsc_capture_script = 'youtube_stream_capture.py'
        self.ytsc_merge_script = 'merge.py'
        # Actualy path to the YTSC script; used to find the merge script (which
        #   should be in the same directory)
        self.ytsc_capture_path = None
        self.ytsc_merge_path = None

        # The directory in which YTSC stores video segments, before they are
        #   merged into the eventual output video
        self.segments_dir = None
        # Full path to the temporary directory used for this download
        self.temp_dir_path = None
        # Full path to the output file
        self.output_path = None

        # YTSC sometimes fails to commence downloading a stream, but succeeds
        #   after a restart. The number of restarts attempted to far
        self.restart_count = 0
        # On the current attempt, the time (matches time.time()) at which we
        #   should either restart, or give up
        self.restart_time = None
        # Flag set to True by self.do_child_process(), if the child process has
        #   been halted, but a restart should be performed
        self.do_restart_flag = False
        # Flag set to True after a call to self.stop(), meaning that no more
        #   restarts are allowed (for example, once the user has clicked the
        #   main window's 'Stop' button
        self.no_restart_flag = False

        # YTSC splits a video into segments, downloaded individually and later
        #   merged into an output video file. The highest segment number
        #   downloaded so far
        self.segment_count = 0


    # Public class methods


    def do_capture(self):

        """Called by downloads.DownloadWorker.run_stream_downloader().

        YTSC runs in two stages. First, it downloads the broadcasting
        livestream in segments, and stores them in a segments directory (with
        a custom name). That stage is handled by this function.

        If the first stage is successful, the second stage is handled by a call
        to self.do_merge(), in which the segments are merged into a video
        output file.

        This function returns the final return code, regardless of whether
        the second stage is performed, or not.

        Returns:

            The final return code, a value in the range 0-5 (as described
                above)

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 5002 do_capture')

        # Import the main app and the media.Video object (for convenience)
        app_obj = self.download_manager_obj.app_obj
        video_obj = self.download_item_obj.media_data_obj

        # This object creates more messages for the Output tab and/or terminal,
        #   than downloads.VideoDownloader would do, as the output generated by
        #   Youtube Stream Capture is not easy for the user to interpret
        self.show_msg(_('Tartube is starting the stream capture...'))

        # Create a temporary directory, in which the video segments (and the
        #   merged output file) can be kept during the process
        # For some reason, the system will not delete the sub-directory
        #   containing the video segments, at the moment the proceeds
        #   completes. However, Tartube's temporary directories are all
        #   deleted on shutdown anyway
        self.temp_dir_path = os.path.abspath(
            os.path.join(app_obj.temp_ytsc_dir, 'dbid_' + str(video_obj.dbid)),
        )

        try:
            if not os.path.isdir(self.temp_dir_path):
                app_obj.make_directory(self.temp_dir_path)

        except:
            self.download_item_obj.media_data_obj.set_error(
                _('Could not create a destination directory, capture halted'),
            )

            self.set_return_code(self.ERROR)
            # Pass a dictionary of values to downloads.DownloadWorker,
            #   confirming the result of the job. The values are passed on to
            #   the main window
            self.last_data_callback()

            return self.return_code

        # Set the path to the capture script; if nont has been specified,
        #   assume the file is in the user's path
        if app_obj.ytsc_path is not None:
            self.ytsc_capture_path = app_obj.ytsc_path
        else:
            self.ytsc_capture_path = self.ytsc_capture_script

        if not os.path.isfile(self.ytsc_capture_path):

            self.download_item_obj.media_data_obj.set_error(
                _('Youtube Stream Capture script not found:') + ' ' \
                + self.ytsc_capture_path,
            )

            self.set_return_code(self.ERROR)
            self.last_data_callback()
            return self.return_code

        # Get the full paths to the merge script
        if self.ytsc_capture_path == self.ytsc_capture_script:

            self.ytsc_merge_path = self.ytsc_merge_script

        else:

            capture_dir, capture_file = os.path.split(self.ytsc_capture_path)
            self.ytsc_merge_path = os.path.abspath(
                os.path.join(
                    capture_dir, self.ytsc_merge_script,
                ),
            )

        if not os.path.isfile(self.ytsc_merge_path):

            self.download_item_obj.media_data_obj.set_error(
                _('Youtube Stream Capture script not found:') + ' ' \
                + self.ytsc_merge_path,
            )

            self.set_return_code(self.ERROR)
            self.last_data_callback()
            return self.return_code

        # Stream capture attempts sometimes fail without getting started, in
        #   which case the capture can be restarted (if settings permit it;
        #   otherwise only one attempt is made)
        while not self.restart_count \
        or (self.do_restart_flag and not self.no_restart_flag):

            # Set the time after which we should stop waiting for the first
            #   segment
            self.restart_time \
            = int(time.time() + (app_obj.ytsc_wait_time * 60))
            # (The flag is set back to True later, if another restart is
            #   required)
            self.do_restart_flag = False
            self.restart_count += 1

            # Generate the system command; if none has been specified, assume
            #   the file is in the user's path
            cmd_list = ['python3'] + [self.ytsc_capture_path] \
            + [video_obj.source] + ['--output-directory'] \
            + [self.temp_dir_path]

            # ...and display it in the Output tab/terminal, if required
            self.show_cmd(' '.join(cmd_list))

            # Create a new child process using that system command...
            self.create_child_process(cmd_list)
            # ...and let it run until it has finished
            self.do_capture_child_process()

        # YTSC produces a return code of 0 on success and -1 on failure
        # Other values have been observed, commonly -9 (when self.stop() is
        #   called, and sometimes for other unknown reasons). After that, the
        #   video segments cannot be merged
        # If 0, we can proceed to the next stage. Otherwise, we must stop now
        msg = ''
        if self.child_process is None:

            msg = _('Download did not start')

        elif self.child_process.returncode == -1:

            msg = _('Failed to capture the livestream')

        elif self.child_process.returncode == -9:

            msg = _('Stream capture terminated')

        elif self.child_process.returncode != 0:

            msg = _('Child process exited with non-zero code: {}').format(
                self.child_process.returncode,
            )

        elif not self.segment_count:

            msg = _('Stream captured terminated without downloading any' \
                + ' video segments (indicating an error with the stream)',
            )

        if msg != '':

            self.show_msg(msg)
            self.download_item_obj.media_data_obj.set_error(msg)

            self.set_return_code(self.ERROR)
            self.last_data_callback()
            return self.return_code

        else:

            # Capture successful
            self.show_msg(_('Stream capture successful'))

            # Now start another system process to merge the segments together
            #   into a single output video, and return the return code of that
            #   process
            return self.do_merge()


    def do_merge(self):

        """Called by self.do_capture().

        Having completed the download, locate the video segments and attempt to
        merge them into a single video output file.

        Returns:

            The final return code, a value in the range 0-5 (as described
            above)

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 5177 do_merge')

        # Import the main app and the media.Video object (for convenience)
        app_obj = self.download_manager_obj.app_obj
        video_obj = self.download_item_obj.media_data_obj

        # Show a confirmation message
        self.show_msg(_('Merging file segments...'))

        # Generate the system command...
        cmd_list = ['python3'] + [self.ytsc_merge_path] + [video_obj.source] \
        + ['--output-directory'] + [self.temp_dir_path]
        # ...and display it in the Output tab/terminal, if required
        self.show_cmd(' '.join(cmd_list))

        # Create a new child process using that system command...
        self.create_child_process(cmd_list)
        # ...and let it run until it has finished
        self.do_merge_child_process()

        # We also set the return code to self.ERROR if the download didn't
        #   start
        # (At the moment, the merge scripts do not return non-zero return
        #   codes)
        if self.child_process is None:

            self.download_item_obj.media_data_obj.set_error(
                _('Segment merge did not start'),
            )

            self.set_return_code(self.ERROR)
            self.last_data_callback()
            return self.return_code

        # Check that a merged file was detected, and that it exists
        if self.output_path is None:

            self.download_item_obj.media_data_obj.set_error(
                _('Segment merge completed, but path not detected'),
            )

            self.set_return_code(self.ERROR)
            self.last_data_callback()
            return self.return_code

        elif not os.path.isfile(self.output_path):

            self.download_item_obj.media_data_obj.set_error(
                _('Segment merge completed, but output file not found'),
            )

            self.set_return_code(self.ERROR)
            self.last_data_callback()
            return self.return_code

        # Move the merged file to its permanent location
        container_dir = video_obj.parent_obj.get_actual_dir(app_obj)
        output_file, output_ext = os.path.splitext(self.output_path)
        new_path = os.path.abspath(
            os.path.join(
                container_dir,
                video_obj.file_name + output_ext,
            ),
        )

        utils.rename_file(app_obj, self.output_path, new_path)

        if os.path.isfile(new_path):

            self.show_msg(_('File moved to:') + ' ' + new_path)
            video_obj.set_file_from_path(new_path)
            app_obj.mark_video_downloaded(video_obj, True)
            app_obj.mark_video_live(video_obj, 0)

            self.show_msg(_('Livestream download is complete'))

        else:

            self.download_item_obj.media_data_obj.set_error(
                _('Failed to move output file'),
            )

            self.set_return_code(self.ERROR)

        # Pass a dictionary of values to downloads.DownloadWorker, confirming
        #   the result of the job. The values are passed on to the main window
        self.last_data_callback()

        # All done
        return self.return_code


    def do_capture_child_process(self):

        """Called by self.do_capture().

        YTSC runs in two stages. First, it downloads the broadcasting
        livestream in segments, and stores them in a segments directory (with
        a custom name). Then, it merges the segments into a single video
        output file.

        This function is called at the first stage to create the child process
        and to check YTSC's output to STDOUT.

        The function returns after the child process stops.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 5285 do_capture_child_process')


        # Import the main app (for convenience)
        app_obj = self.download_manager_obj.app_obj

        # So that we can read from the child process STDOUT and STDERR, attach
        #   a file descriptor to the PipeReader objects
        # (As described above, STDERR is currently ignored, but might be used
        #   in the future)
        if self.child_process is not None:

            self.stdout_reader.attach_file_descriptor(
                self.child_process.stdout,
            )

            self.stderr_reader.attach_file_descriptor(
                self.child_process.stderr,
            )

        # While capturing the stream or merging the video segments, update the
        #   callback function with the status of the current job
        while self.is_child_process_alive():

            # Pause a moment between each iteration of the loop (we don't want
            #   to hog system resources)
            time.sleep(self.sleep_time)

            # Read from the child process STDOUT, and convert into unicode for
            #   Python's convenience
            while not self.stdout_queue.empty():

                stdout = self.stdout_queue.get_nowait().rstrip()
                if stdout:

                    # On MS Windows we use cp1252, so that Tartube can
                    #   communicate with the Windows console
                    stdout = stdout.decode(utils.get_encoding(), 'replace')

                    # Intercept various STDOUT messages
                    finished_flag = False
                    write_flag = False

                    # Intercept the segment number, and update the IV (but
                    #   don't display that line in the Output tab)
                    match = re.search('^Segment number\: (\d+)', stdout)
                    if match:

                        segment_num = int(match.group(1))
                        if segment_num > self.segment_count:
                            self.segment_count = segment_num

                    # Intercept the segments directory, if we don't already
                    #   have it
                    if not write_flag and self.segments_dir is None:

                        match = re.search(
                            '^[INFO] Created directory (.*)',
                            stdout,
                        )

                        if match:

                            write_flag = True
                            self.segments_dir = match.group(1)

                    # Intercept other messages which can be displayed, even
                    #   when verbose output is turned off
                    # (Some of lines captured here, could also have been
                    #   captured by the code block above)
                    if not write_flag \
                    and (
                        re.search('^\w+\|OK\s+\|', stdout) \
                        or re.search('^\w+\|ERR\s+\|', stdout)
                    ):
                        write_flag = True

                    # Intercept the message, showing that the first stage is
                    #   complete
                    if not write_flag:

                        match = re.search('Exceeded.*retries', stdout)
                        if match:
                            finished_flag = True
                            write_flag = True

                    # Pass a dictionary of values to self.download_worker_obj
                    #   so the main window can be updated
                    # The dictionary is based on the one created by
                    #   downloads.VideoDownloader (but with far fewer values
                    #   included)
                    dl_stat_dict = {
                        'playlist_index': self.segment_count,
                        'playlist_size': '?',
                        'dl_sim_flag': False,
                        'status': formats.ACTIVE_STAGE_CAPTURE,
                    }

                    self.download_worker_obj.data_callback(dl_stat_dict)

                    # Show output in the Output tab (if required)
                    if app_obj.ytsc_write_verbose_flag \
                    or (app_obj.ytdl_output_stdout_flag and write_flag):
                        app_obj.main_win_obj.output_tab_write_stdout(
                            self.download_worker_obj.worker_id,
                            stdout,
                        )

                    # Show output in the terminal (if required)
                    if app_obj.ytsc_write_verbose_flag \
                    or (app_obj.ytdl_write_stdout_flag and write_flag):
                        # Git #175, Japanese text may produce a codec error
                        #   here, despite the .decode() call above
                        try:
                            print(
                                stdout.encode(utils.get_encoding(), 'replace'),
                            )
                        except:
                            print('STDOUT text with unprintable characters')

                    # If the download appears to be complete, stop the child
                    #   process
                    if finished_flag:
                        self.stop()

            # If no segments have been received and it's time to give up (or to
            #   restart the child process), then do so
            if not self.segment_count \
            and self.restart_time < time.time():

                # Halt the child process, but don't let it forbid restarts
                self.stop(True)

                if not self.no_restart_flag \
                and self.restart_count <= app_obj.ytsc_restart_max:

                    self.do_restart_flag = True
                    self.show_msg(
                        _(
                            'Stream capture is frozen, trying again' \
                            + ' (restart #{0})'.format(self.restart_count),
                        ),
                    )

                else:

                    self.show_msg(_('Stream capture is frozen, giving up'))

                # (In both cases, self.is_child_process_alive() might return
                #   True right now, so return control to the calling function
                #   early)
                break


    def do_merge_child_process(self):

        """Called by self.do_merge().

        YTSC runs in two stages. First, it downloads the broadcasting
        livestream in segments, and stores them in a segments directory (with
        a custom name). Then, it merges the segments into a single video
        output file.

        This function is called at the second stage to create the child process
        and to check YTSC's output to STDOUT.

        The function returns after the child process stops.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 5456 do_merge_child_process')


        # Import the main app (for convenience)
        app_obj = self.download_manager_obj.app_obj

        # So that we can read from the child process STDOUT and STDERR, attach
        #   a file descriptor to the PipeReader objects
        # (As described above, STDERR is currently ignored, but might be used
        #   in the future)
        if self.child_process is not None:

            self.stdout_reader.attach_file_descriptor(
                self.child_process.stdout,
            )

            self.stderr_reader.attach_file_descriptor(
                self.child_process.stderr,
            )

        # While capturing the stream or merging the video segments, update the
        #   callback function with the status of the current job
        while self.is_child_process_alive():

            # Pause a moment between each iteration of the loop (we don't want
            #   to hog system resources)
            time.sleep(self.sleep_time)

            # Read from the child process STDOUT, and convert into unicode for
            #   Python's convenience
            while not self.stdout_queue.empty():

                stdout = self.stdout_queue.get_nowait().rstrip()
                if stdout:

                    # On MS Windows we use cp1252, so that Tartube can
                    #   communicate with the Windows console
                    stdout = stdout.decode(utils.get_encoding(), 'replace')

                    # Intercept various STDOUT messages, depending on whether
                    #   the merge has started yet, or not
                    finished_flag = False
                    write_flag = False

                    # Intercept output file information
                    if re.search('^\[INFO\]', stdout) \
                    or re.search('^\[WARNING\]', stdout) \
                    or re.search('^\[ERROR\]', stdout):
                        write_flag = True

                    else:

                        match = re.search('^Output file\: (.*)', stdout)
                        if match:
                            self.output_path = match.group(1)
                            finished_flag = True
                            write_flag = True

                    # Pass a dictionary of values to self.download_worker_obj
                    #   so the main window can be updated
                    # The dictionary is based on the one created by
                    #   downloads.VideoDownloader (but with far fewer values
                    #   included)
                    dl_stat_dict = {
                        'playlist_index': self.segment_count,
                        'playlist_size': '?',
                        'dl_sim_flag': False,
                        'status': formats.ACTIVE_STAGE_MERGE,
                    }

                    self.download_worker_obj.data_callback(dl_stat_dict)

                    # Show output in the Output tab (if required)
                    if app_obj.ytsc_write_verbose_flag \
                    or (app_obj.ytdl_output_stdout_flag and write_flag):
                        app_obj.main_win_obj.output_tab_write_stdout(
                            self.download_worker_obj.worker_id,
                            stdout,
                        )

                    # Show output in the terminal (if required)
                    if app_obj.ytsc_write_verbose_flag \
                    or (app_obj.ytdl_write_stdout_flag and write_flag):
                        # Git #175, Japanese text may produce a codec error
                        #   here, despite the .decode() call above
                        try:
                            print(
                                stdout.encode(utils.get_encoding(), 'replace'),
                            )
                        except:
                            print('STDOUT text with unprintable characters')

                    # If the download appears to be complete, stop the child
                    #   process
                    if finished_flag:
                        self.stop()


    def close(self):

        """Can be called by anything.

        Destructor function for this object.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 5563 close')

        # Tell the PipeReader objects to shut down, thus joining their threads
        self.stdout_reader.join()
        self.stderr_reader.join()


    def create_child_process(self, cmd_list):

        """Called by self.do_child_process().

        Based on YoutubeDLDownloader._create_process().

        Executes the system command, creating a new child process which
        executes youtube-dl.

        Args:

            cmd_list (list): Python list that contains the command to execute.

        Returns:

            True on success, False on an error

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 5590 create_child_process')

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

            return True

        except (ValueError, OSError) as error:
            # (Errors are expected and frequent)
            return False


    def is_child_process_alive(self):

        """Called by self.do_child_process() and self.stop().

        Based on YoutubeDLDownloader._proc_is_alive().

        Called continuously during the self.do_fetch() loop to check whether
        the child process has finished or not.

        Returns:

            True if the child process is alive, otherwise returns False

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 5635 is_child_process_alive')

        if self.child_process is None:
            return False

        return self.child_process.poll() is None


    def last_data_callback(self):

        """Called by self.do_capture() or .do_merge().

        Based on YoutubeDLDownloader._last_data_hook().

        After the child process has finished, creates a new Python dictionary
        in the standard form described by self.extract_stdout_data().

        Sets key-value pairs in the dictonary, then passes it to the parent
        downloads.DownloadWorker object, confirming the result of the child
        process.

        The new key-value pairs are used to update the main window.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 5660 last_data_callback')

        dl_stat_dict = {}

        if self.return_code == self.OK:
            dl_stat_dict['status'] = formats.COMPLETED_STAGE_FINISHED
        elif self.return_code == self.ERROR:
            dl_stat_dict['status'] = formats.MAIN_STAGE_ERROR
        elif self.return_code == self.STOPPED:
            dl_stat_dict['status'] = formats.ERROR_STAGE_STOPPED

        # Use some empty values in dl_stat_dict so that the Progress tab
        #   doesn't show arbitrary data from the last file downloaded
        dl_stat_dict['playlist_index'] = ''
        dl_stat_dict['playlist_size'] = ''
        dl_stat_dict['dl_sim_flag'] = ''

        # The True argument shows that this function is the caller
        self.download_worker_obj.data_callback(dl_stat_dict, True)


    def set_return_code(self, code):

        """Called by self.do_capture() and .do_merge().

        Based on YoutubeDLDownloader._set_returncode().

        After the child process has terminated with an error of some kind,
        sets a new value for self.return_code, but only if the new return code
        is higher in the hierarchy of return codes than the current value.

        Args:

            code (int): A return code in the range 0-5

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 5698 set_return_code')

        if code >= self.return_code:
            self.return_code = code


    def show_cmd(self, cmd):

        """Called by self.do_capture() and .do_merge().

        Shows a system command in the Output tab and/or terminal window, if
        required.

        Args:

            cmd (str): The system command to display

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 5718 show_cmd')

        # Import the main app (for convenience)
        app_obj = self.download_manager_obj.app_obj

        # Display the command in the Output tab, if allowed
        if app_obj.ytdl_output_system_cmd_flag:

            app_obj.main_win_obj.output_tab_write_system_cmd(
                self.download_worker_obj.worker_id,
                cmd,
            )

        # Display the message in the terminal, if allowed
        if app_obj.ytdl_write_system_cmd_flag:
            try:
                print(cmd)
            except:
                print('Command echoed in STDOUT with unprintable characters')


    def show_msg(self, msg):

        """Called by self.do_capture() and .do_merge().

        Shows a message in the Output tab and/or terminal window, if required.

        Args:

            msg (str): The message to display

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 5752 show_msg')

        # Import the main app (for convenience)
        app_obj = self.download_manager_obj.app_obj

        # Display the message in the Output tab, if allowed
        if app_obj.ytdl_output_stdout_flag:

            app_obj.main_win_obj.output_tab_write_stdout(
                self.download_worker_obj.worker_id,
                msg,
            )

        # Display the message in the terminal, if allowed
        if app_obj.ytdl_write_stdout_flag:
            try:
                print(msg)
            except:
                print('Message echoed in STDOUT with unprintable characters')


    def stop(self, restart_flag=False):

        """Called by DownloadWorker.close() and self.do_child_process().

        Terminates the child process.

        Args:

            restart_flag (bool): If False, no restarts are allowed (perhaps
                because the user has clicked the 'Stop' button in the main
                window's toolbar). If True, don't explicitly forbid restarts
                yet

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 5789 stop')

        if not restart_flag:
            self.no_restart_flag = True

        if self.is_child_process_alive():

            if os.name == 'nt':
                # os.killpg is not available on MS Windows (see
                #   https://bugs.python.org/issue5115 )
                self.child_process.kill()

                # When we kill the child process on MS Windows the return code
                #   gets set to 1, so we want to reset the return code back to
                #   0
                self.child_process.returncode = 0

            else:
                os.killpg(self.child_process.pid, signal.SIGKILL)


    def stop_soon(self):

        """Can be called by anything. Currently called by
        mainwin.MainWin.on_progress_list_stop_soon().

        This objects only downloads a single video, so we can ignore an
        instruction to stop after that download has finished.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 5820 stop_soon')

        pass


class JSONFetcher(object):

    """Called by downloads.DownloadWorker.check_rss().

    Python class to download JSON data for a video which is believed to be a
    livestream, using youtube-dl.

    The video has been found in the channel's/playlist's RSS feed, but not by
    youtube-dl, when the channel/playlist was last checked downloaded.

    If the data can be downloaded, we assume that the livestream is currently
    broadcasting. If we get a 'This video is unavailable' error, we assume that
    the livestream is waiting to start.

    This is the behaviour exhibited on YouTube. It might work on other
    compatible websites, too, if the user has set manually set the URL for the
    channel/playlist RSS feed.

    This class creates a system child process and uses the child process to
    instruct youtube-dl to fetch the JSON data for the video.

    Reads from the child process STDOUT and STDERR, having set up a
    downloads.PipeReader object to do so in an asynchronous way.

    If one of the two outcomes described above takes place, the media.Video
    object's IVs are updated to mark it as a livestream.

    Args:

        download_manager_obj (downloads.DownloadManager): The download manager
            object handling the entire download operation

        download_worker_obj (downloads.DownloadWorker): The parent download
            worker object. The download manager uses multiple workers to
            implement simultaneous downloads. The download manager checks for
            free workers and, when it finds one, assigns it a
            download.DownloadItem object. When the worker is assigned a
            download item, it creates a new instance of this object for each
            detected livestream, and waits for this object to complete its
            task

        container_obj (media.Channel, media.Playlist): The channel/playlist
            in which a livestream has been detected

        entry_dict (dict): A dictionary of values generated when reading the
            RSS feed (provided by the Python feedparser module. The dictionary
            represents available data for a single livestream video

    Warnings:

        The calling function is responsible for calling the close() method
        when it's finished with this object, in order for this object to
        properly close down.

    """


    # Standard class methods


    def __init__(self, download_manager_obj, download_worker_obj, \
    container_obj, entry_dict):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 5889 __init__')

        # IV list - class objects
        # -----------------------
        # The downloads.DownloadManager object handling the entire download
        #   operation
        self.download_manager_obj = download_manager_obj
        # The parent downloads.DownloadWorker object
        self.download_worker_obj = download_worker_obj
        # The media.Channel or media.Playlist object in which a livestream has
        #   been detected
        self.container_obj = container_obj

        # This object reads from the child process STDOUT and STDERR in an
        #   asynchronous way
        # Standard Python synchronised queue classes
        self.stdout_queue = queue.Queue()
        self.stderr_queue = queue.Queue()
        # The downloads.PipeReader objects created to handle reading from the
        #   pipes
        self.stdout_reader = PipeReader(self.stdout_queue)
        self.stderr_reader = PipeReader(self.stderr_queue)

        # The child process created by self.create_child_process()
        self.child_process = None


        # IV list - other
        # ---------------
        # A dictionary of values generated when reading the RSS feed (provided
        #   by the Python feedparser module. The dictionary represents
        #   available data for a single livestream video
        self.entry_dict = entry_dict
        # Important data is extracted from the entry (below), and added to
        #   these IVs, ready for use
        self.video_name = None
        self.video_source = None
        self.video_descrip = None
        self.video_thumb_source = None
        self.video_upload_time = None

        # The time (in seconds) between iterations of the loop in
        #   self.do_fetch()
        self.sleep_time = 0.1


        # Code
        # ----
        # Initialise IVs from the RSS feed entry for the livestream video
        #   (saves a bit of time later)
        if 'title' in entry_dict:
            self.video_name = entry_dict['title']

        if 'link' in entry_dict:
            self.video_source = entry_dict['link']

        if 'summary' in entry_dict:
            self.video_descrip = entry_dict['summary']

        if 'media_thumbnail' in entry_dict \
        and entry_dict['media_thumbnail'] \
        and 'url' in entry_dict['media_thumbnail'][0]:
            self.video_thumb_source = entry_dict['media_thumbnail'][0]['url']

        if 'published_parsed' in entry_dict:

            try:
                # A time.struct_time object; convert to Unix time, to match
                #   media.Video.upload_time
                dt_obj = datetime.datetime.fromtimestamp(
                    time.mktime(entry_dict['published_parsed']),
                )

                self.video_upload_time = int(dt_obj.timestamp())

            except:
                self.video_upload_time = None


    # Public class methods


    def do_fetch(self):

        """Called by downloads.DownloadWorker.check_rss().

        Downloads JSON data for the livestream video whose URL is
        self.video_source.

        If the data can be downloaded, we assume that the livestream is
        currently broadcasting. If we get a 'This video is unavailable' error,
        we assume that the livestream is waiting to start.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 5979 do_fetch')

        # Import the main app (for convenience)
        app_obj = self.download_manager_obj.app_obj

        # Convert a youtube-dl path beginning with ~ (not on MS Windows)
        #   (code copied from utils.generate_ytdl_system_cmd() )
        ytdl_path = app_obj.check_downloader(app_obj.ytdl_path)
        if os.name != 'nt':
            ytdl_path = re.sub('^\~', os.path.expanduser('~'), ytdl_path)

        # Generate the system command...
        if app_obj.ytdl_path_custom_flag:
            cmd_list = ['python3'] + [ytdl_path] + ['--dump-json'] \
            + [self.video_source]
        else:
            cmd_list = [ytdl_path] + ['--dump-json'] + [self.video_source]
        # ...and create a new child process using that command
        self.create_child_process(cmd_list)

        # So that we can read from the child process STDOUT and STDERR, attach
        #   a file descriptor to the PipeReader objects
        if self.child_process is not None:

            self.stdout_reader.attach_file_descriptor(
                self.child_process.stdout,
            )

            self.stderr_reader.attach_file_descriptor(
                self.child_process.stderr,
            )

        # Wait for the process to finish
        while self.is_child_process_alive():

            # Pause a moment between each iteration of the loop (we don't want
            #   to hog system resources)
            time.sleep(self.sleep_time)

        # Process has finished. If the JSON data has been received, indicating
        #   a livestream currently broadcasting, it's in STDOUT
        new_video_flag = False
        while not self.stdout_queue.empty():

            stdout = self.stdout_queue.get_nowait().rstrip()
            if stdout:

                # (Convert bytes to string)
                stdout = stdout.decode(utils.get_encoding(), 'replace')
                if stdout[:1] == '{':

                    # Broadcasting livestream detected; create a new
                    #   media.Video object
                    GObject.timeout_add(
                        0,
                        app_obj.create_livestream_from_download,
                        self.container_obj,
                        2,                      # Livestream has started
                        self.video_name,
                        self.video_source,
                        self.video_descrip,
                        self.video_upload_time,
                    )

                    new_video_flag = True

        # Messages indicating that a livestream is waiting to start are in
        #   STDERR (for some reason)
        if not new_video_flag:

            while not self.stderr_queue.empty():

                stderr = self.stderr_queue.get_nowait().rstrip()
                if stderr:

                    # (Convert bytes to string)
                    stderr = stderr.decode(utils.get_encoding(), 'replace')
                    live_data_dict = utils.extract_livestream_data(stderr)
                    if live_data_dict:

                        # Waiting livestream detected; create a new media.Video
                        #   object
                        GObject.timeout_add(
                            0,
                            app_obj.create_livestream_from_download,
                            self.container_obj,
                            1,                  # Livestream waiting to start
                            self.video_name,
                            self.video_source,
                            self.video_descrip,
                            self.video_upload_time,
                            live_data_dict,
                        )

                        new_video_flag = True

        if new_video_flag:

            # Download the video's thumbnail, if possible
            if self.video_thumb_source:

                # Get the thumbnail's extension...
                remote_file, remote_ext = os.path.splitext(
                    self.video_thumb_source,
                )

                # ...and thus get the filename used by youtube-dl when storing
                #   the thumbnail locally (assuming that the video's name, and
                #   the filename when it is later downloaded, are the same)
                local_thumb_path = os.path.abspath(
                    os.path.join(
                        self.container_obj.get_actual_dir(app_obj),
                        self.video_name + remote_ext,
                    ),
                )

                options_obj = self.download_worker_obj.options_manager_obj
                if not options_obj.options_dict['sim_keep_thumbnail']:
                    local_thumb_path = utils.convert_path_to_temp(
                        app_obj,
                        local_thumb_path,
                    )

                elif options_obj.options_dict['move_thumbnail']:
                    local_thumb_path = os.path.abspath(
                        os.path.join(
                            self.container_obj.get_actual_dir(app_obj),
                            app_obj.thumbs_sub_dir,
                            self.video_name + remote_ext,
                        )
                    )

                if local_thumb_path:
                    try:
                        request_obj = requests.get(
                            self.video_thumb_source,
                            timeout = app_obj.request_get_timeout,
                        )

                        with open(local_thumb_path, 'wb') as outfile:
                            outfile.write(request_obj.content)

                    except:
                        pass

                # Convert .webp thumbnails to .jpg, if required
                if local_thumb_path is not None \
                and not app_obj.ffmpeg_fail_flag \
                and app_obj.ffmpeg_convert_webp_flag \
                and not app_obj.ffmpeg_manager_obj.convert_webp(
                    local_thumb_path
                ):
                    app_obj.set_ffmpeg_fail_flag(True)
                    GObject.timeout_add(
                        0,
                        app_obj.system_error,
                        307,
                        app_obj.ffmpeg_fail_msg,
                    )


    def close(self):

        """Called by downloads.DownloadWorker.check_rss().

        Destructor function for this object.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 6140 close')

        # Tell the PipeReader objects to shut down, thus joining their threads
        self.stdout_reader.join()
        self.stderr_reader.join()


    def create_child_process(self, cmd_list):

        """Called by self.do_fetch().

        Based on YoutubeDLDownloader._create_process().

        Executes the system command, creating a new child process which
        executes youtube-dl.

        Args:

            cmd_list (list): Python list that contains the command to execute.

        Returns:

            True on success, False on an error

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 6167 create_child_process')

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

            return True

        except (ValueError, OSError) as error:
            # (Errors are expected and frequent)
            return False


    def is_child_process_alive(self):

        """Called by self.do_fetch() and self.stop().

        Based on YoutubeDLDownloader._proc_is_alive().

        Called continuously during the self.do_fetch() loop to check whether
        the child process has finished or not.

        Returns:

            True if the child process is alive, otherwise returns False.

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 6212 is_child_process_alive')

        if self.child_process is None:
            return False

        return self.child_process.poll() is None


    def stop(self):

        """Called by DownloadWorker.close().

        Terminates the child process.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 6228 stop')

        if self.is_child_process_alive():

            if os.name == 'nt':
                # os.killpg is not available on MS Windows (see
                #   https://bugs.python.org/issue5115 )
                self.child_process.kill()

                # When we kill the child process on MS Windows the return code
                #   gets set to 1, so we want to reset the return code back to
                #   0
                self.child_process.returncode = 0

            else:
                os.killpg(self.child_process.pid, signal.SIGKILL)


class StreamManager(threading.Thread):

    """Called by mainapp.TartubeApp.livestream_manager_start().

    Python class to create a system child process, to check media.Video objects
    already marked as livestreams, to see whether they have started or stopped
    broadcasting.

    Reads from the child process STDOUT and STDERR, having set up a
    downloads.PipeReader object to do so in an asynchronous way.

    Args:

        app_obj (mainapp.TartubeApp): The main application

    """


    # Standard class methods


    def __init__(self, app_obj):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 6270 __init__')

        super(StreamManager, self).__init__()

        # IV list - class objects
        # -----------------------
        # The mainapp.TartubeApp object
        self.app_obj = app_obj
        # The downloads.MiniJSONFetcher object used to check each media.Video
        #   object marked as a livestream
        self.mini_fetcher_obj = None


        # IV list - other
        # ---------------
        # A local list of media.Video objects marked as livestreams (in case
        #   the mainapp.TartubeApp IV changes during the course of this
        #   operation)
        # Dictionary in the form:
        #   key = media data object's unique .dbid
        #   value = the media data object itself
        self.video_dict = {}
        # A subset of self.video_dict, containing only videos whose livestream
        #   status has changed from waiting to live
        # Used by mainapp.TartubeApp.livestream_manager_finished() to update
        #   the Video Catalogue, create a desktop notification and/or open the
        #   livestream in the system's web browser
        self.video_started_dict = {}
        # A subset of self.video_dict, containing only videos whose livestream
        #   status has changed from live to finished
        # Used by mainapp.TartubeApp.livestream_manager_stopped() to update
        #   the Video Catalogue
        self.video_stopped_dict = {}
        # A subset of self.video_dict, containing only videos which were
        #   currently broadcasting livestreams, but for which there is no
        #   JSON data (indicating that the video has been deleted, or is
        #   temporarily unavailable on the website)
        # Used by mainapp.TartubeApp.livestream_manager_finished() to remove
        #   the video(s) from the Video Catalogue
        self.video_missing_dict = {}

        # Flag set to False if self.stop_livestream_operation() is called
        # The False value halts the loop in self.run()
        self.running_flag = True

        # Code
        # ----

        # Let's get this party started!
        self.start()


    # Public class methods


    def run(self):

        """Called as a result of self.__init__().

        Initiates the download.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 6333 run')

        # Generate a local list of media.Video objects marked as livestreams
        #   (in case the mainapp.TartubeApp IV changes during the course of
        #   this operation)
        self.video_dict = self.app_obj.media_reg_live_dict.copy()

        for video_obj in self.video_dict.values():

            if not self.running_flag:
                break

            # For each media.Video in turn, try to fetch JSON data
            # If the data is received, assume the livestream is live. If a
            #   'This video is unavailable' error is received, the livestream
            #   is waiting to go live
            self.mini_fetcher_obj = MiniJSONFetcher(self, video_obj)

            # Then execute the assigned job
            self.mini_fetcher_obj.do_fetch()

            # Call the destructor function of the MiniJSONFetcher object
            #   (first checking it still exists, in case
            #   self.stop_livestream_operation() has been called)
            if self.mini_fetcher_obj:
                self.mini_fetcher_obj.close()
                self.mini_fetcher_obj = None

        # Operation complete. If self.stop_livestream_operation() was called,
        #   then the mainapp.TartubeApp function has already been called
        if self.running_flag:
            self.running_flag = False
            self.app_obj.livestream_manager_finished()


    def mark_video_as_missing(self, video_obj):

        """Called by downloads.MiniJSONFetcher.do_fetch().

        If a media.Video object marked as a livestream is missing in the
        parent channel's/playlist's RSS feed, then add the video to an IV, so
        that mainapp.TartubeApp.livestream_manager_finished() can take
        appropriate action, when the livestream operation is finished.

        Args:

            video_obj (media.Video): The livestream video which was not found
                in the RSS stream

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 6385 mark_video_as_missing')

        self.video_missing_dict[video_obj.dbid] = video_obj


    def mark_video_as_started(self, video_obj):

        """Called by downloads.MiniJSONFetcher.do_fetch().

        If a media.Video object marked as a livestream has started
        broadcasting, then add the video to an IV, so that
        mainapp.TartubeApp.livestream_manager_finished() can take appropriate
        action, when the livestream operation is finished.

        Args:

            video_obj (media.Video): The livestream video which has started
                broadcasting

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 6407 mark_video_as_started')

        self.video_started_dict[video_obj.dbid] = video_obj


    def mark_video_as_stopped(self, video_obj):

        """Called by downloads.MiniJSONFetcher.do_fetch().

        If a media.Video object marked as a livestream has stopped
        broadcasting, then add the video to an IV, so that
        mainapp.TartubeApp.livestream_manager_finished() can take appropriate
        action, when the livestream operation is finished.

        Args:

            video_obj (media.Video): The livestream video which has stopped
                broadcasting

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 6429 mark_video_as_stopped')

        self.video_stopped_dict[video_obj.dbid] = video_obj


    def stop_livestream_operation(self):

        """Can be called by anything.

        Based on downloads.DownloadManager.stop_downloads().

        Stops the livestream operation. On the next iteration of self.run()'s
        loop, the downloads.MiniJSONFetcher objects are cleaned up.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 6445 stop_livestream_operation')

        self.running_flag = False

        # Halt the MiniJSONFetcher; it doesn't matter if it was in the middle
        #   of doing something
        if self.mini_fetcher_obj:
            self.mini_fetcher_obj.close()
            self.mini_fetcher_obj = None

        # Call the mainapp.TartubeApp function to update everything (it's not
        #   called from self.run(), in this situation)
        self.app_obj.livestream_manager_finished()


class MiniJSONFetcher(object):

    """Called by downloads.StreamManager.run().

    A modified version of downloads.JSONFetcher (the former is called by
    downloads.DownloadWorker only; using a second Python class for the same
    objective makes the code somewhat simpler).

    Python class to fetch JSON data for a livestream video, using youtube-dl.

    Creates a system child process and uses the child process to instruct
    youtube-dl to fetch the JSON data for the video.

    Reads from the child process STDOUT and STDERR, having set up a
    downloads.PipeReader object to do so in an asynchronous way.

    Args:

        livestream_manager_obj (downloads.StreamManager): The livestream
            manager object handling the entire livestream operation

        video_obj (media.Video): The livestream video whose JSON data should be
            fetched (the equivalent of right-clicking the video in the Video
            Catalogue, and selecting 'Check this video')

    """


    # Standard class methods


    def __init__(self, livestream_manager_obj, video_obj):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 6494 __init__')

        # IV list - class objects
        # -----------------------
        # The downloads.StreamManager object handling the entire livestream
        #   operation
        self.livestream_manager_obj = livestream_manager_obj
        # The media.Video object for which new JSON data must be fetched
        #   (the equivalent of right-clicking the video in the Video Catalogue,
        #   and selecting 'Check this video')
        self.video_obj = video_obj

        # This object reads from the child process STDOUT and STDERR in an
        #   asynchronous way
        # Standard Python synchronised queue classes
        self.stdout_queue = queue.Queue()
        self.stderr_queue = queue.Queue()
        # The downloads.PipeReader objects created to handle reading from the
        #   pipes
        self.stdout_reader = PipeReader(self.stdout_queue)
        self.stderr_reader = PipeReader(self.stderr_queue)

        # The child process created by self.create_child_process()
        self.child_process = None


        # IV list - other
        # ---------------
        # The time (in seconds) between iterations of the loop in
        #   self.do_fetch()
        self.sleep_time = 0.1


    # Public class methods


    def do_fetch(self):

        """Called by downloads.StreamManager.run().

        Downloads JSON data for the livestream video, self.video_obj.

        If the data can be downloaded, we assume that the livestream is
        currently broadcasting. If we get a 'This video is unavailable' error,
        we assume that the livestream is waiting to start.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 6542 do_fetch')

        # Import the main app (for convenience)
        app_obj = self.livestream_manager_obj.app_obj

        # Convert a youtube-dl path beginning with ~ (not on MS Windows)
        #   (code copied from utils.generate_ytdl_system_cmd() )
        ytdl_path = app_obj.check_downloader(app_obj.ytdl_path)
        if os.name != 'nt':
            ytdl_path = re.sub('^\~', os.path.expanduser('~'), ytdl_path)

        # Generate the system command...
        if app_obj.ytdl_path_custom_flag:
            cmd_list = ['python3'] + [ytdl_path] + ['--dump-json'] \
            + [self.video_obj.source]
        else:
            cmd_list = [ytdl_path] + ['--dump-json'] + [self.video_obj.source]
        # ...and create a new child process using that command
        self.create_child_process(cmd_list)

        # So that we can read from the child process STDOUT and STDERR, attach
        #   a file descriptor to the PipeReader objects
        if self.child_process is not None:

            self.stdout_reader.attach_file_descriptor(
                self.child_process.stdout,
            )

            self.stderr_reader.attach_file_descriptor(
                self.child_process.stderr,
            )

        # Wait for the process to finish
        while self.is_child_process_alive():

            # Pause a moment between each iteration of the loop (we don't want
            #   to hog system resources)
            time.sleep(self.sleep_time)

        # Process has finished. If the JSON data has been received, indicating
        #   a livestream currently broadcasting, it's in STDOUT
        while not self.stdout_queue.empty():

            stdout = self.stdout_queue.get_nowait().rstrip()
            if stdout:

                # (Convert bytes to string)
                stdout = stdout.decode(utils.get_encoding(), 'replace')
                if stdout[:1] == '{':

                    # Broadcasting livestream detected
                    json_dict = self.parse_json(stdout)
                    if self.video_obj.live_mode == 1:

                        # Waiting livestream has gone live
                        GObject.timeout_add(
                            0,
                            app_obj.mark_video_live,
                            self.video_obj,
                            2,              # Livestream is broadcasting
                            {},             # No livestream data
                            True,           # Don't update Video Index yet
                            True,           # Don't update Video Catalogue yet
                        )
                        # (Mark this video as modified, so that
                        #   mainapp.TartubeApp can update the Video Catalogue
                        #   once the livestream operation has finished)
                        self.livestream_manager_obj.mark_video_as_started(
                            self.video_obj,
                        )

                    elif self.video_obj.live_mode == 2 \
                    and not json_dict['is_live']:

                        # Broadcasting livestream has finished
                        GObject.timeout_add(
                            0,
                            app_obj.mark_video_live,
                            self.video_obj,
                            0,                  # Livestream has finished
                            {},             # Reset any livestream data
                            None,           # Reset any l/s server messages
                            True,           # Don't update Video Index yet
                            True,           # Don't update Video Catalogue yet
                        )
                        self.livestream_manager_obj.mark_video_as_stopped(
                            self.video_obj,
                        )

                    # The video's name and description might change during the
                    #   livestream; update them, if so
                    if 'title' in json_dict:
                        self.video_obj.set_nickname(json_dict['title'])

                    if 'id' in json_dict:
                        self.video_obj.set_vid(json_dict['id'])

                    if 'description' in json_dict:
                        self.video_obj.set_video_descrip(
                            app_obj,
                            json_dict['description'],
                            app_obj.main_win_obj.descrip_line_max_len,
                        )

        # Messages indicating that a livestream is waiting to start are in
        #   STDERR (for some reason)
        while not self.stderr_queue.empty():

            stderr = self.stderr_queue.get_nowait().rstrip()
            if stderr:

                # (Convert bytes to string)
                stderr = stderr.decode(utils.get_encoding(), 'replace')

                # (v2.2.100: In approximately October 2020, YouTube started
                #   using a new error message for livestreams waiting to start
                if self.video_obj.live_mode == 1:

                    live_data_dict = utils.extract_livestream_data(stderr)
                    if live_data_dict:
                        self.video_obj.set_live_data(live_data_dict)

                elif self.video_obj.live_mode == 2 \
                and re.search('This video is unavailable', stderr):

                    # The livestream broadcast has been deleted by its owner
                    #   (or is not available on the website, possibly
                    #   temporarily)
                    self.livestream_manager_obj.mark_video_as_missing(
                        self.video_obj,
                    )


    def close(self):

        """Called by downloads.StreamManager.run().

        Destructor function for this object.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 6675 close')

        # Tell the PipeReader objects to shut down, thus joining their threads
        self.stdout_reader.join()
        self.stderr_reader.join()


    def create_child_process(self, cmd_list):

        """Called by self.do_fetch().

        Based on YoutubeDLDownloader._create_process().

        Executes the system command, creating a new child process which
        executes youtube-dl.

        Args:

            cmd_list (list): Python list that contains the command to execute.

        Returns:

            True on success, False on an error

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 6702 create_child_process')

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

            return True

        except (ValueError, OSError) as error:
            # (Errors are expected and frequent)
            return False


    def is_child_process_alive(self):

        """Called by self.do_fetch() and self.stop().

        Based on YoutubeDLDownloader._proc_is_alive().

        Called continuously during the self.do_fetch() loop to check whether
        the child process has finished or not.

        Returns:

            True if the child process is alive, otherwise returns False

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 6747 is_child_process_alive')

        if self.child_process is None:
            return False

        return self.child_process.poll() is None


    def parse_json(self, stdout):

        """Called by self.do_fetch().

        Code copied from downloads.VideoDownloader.extract_stdout_data().

        Converts the receivd JSON data into a dictionary, and returns the
        dictionary.

        Args:

            stdout (str): A string of JSON data as it was received from
                youtube-dl (and starting with the character { )

        Returns:

            The JSON data, converted into a Python dictionary

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 6776 parse_json')

        # (Try/except to check for invalid JSON)
        try:
            return json.loads(stdout)

        except:
            GObject.timeout_add(
                0,
                app_obj.system_error,
                308,
                'Invalid JSON data received from server',
            )

            return {}


    def stop(self):

        """Called by DownloadWorker.close().

        Terminates the child process.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 6801 stop')

        if self.is_child_process_alive():

            if os.name == 'nt':
                # os.killpg is not available on MS Windows (see
                #   https://bugs.python.org/issue5115 )
                self.child_process.kill()

                # When we kill the child process on MS Windows the return code
                #   gets set to 1, so we want to reset the return code back to
                #   0
                self.child_process.returncode = 0

            else:
                os.killpg(self.child_process.pid, signal.SIGKILL)


class CustomDLManager(object):

    """Called by mainapp.TartubeApp.create_custom_dl_manager().

    Python class to store settings for a custom download. The user can create
    as many instances of this object as they like, and can launch a custom
    download using settings from any of them.

    Args:

        uid (int): Unique ID for this custom download manager (unique only to
            this class of objects)

        name (str): Non-unique name forthis custom download manager

    """


    # Standard class methods


    def __init__(self, uid, name):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 6494 __init__')

        # IV list - other
        # ---------------
        # Unique ID for this custom download manager
        self.uid = uid
        # A non-unique name for this custom download manager
        self.name = name

        # If True, during a custom download, download every video which is
        #   marked as not downloaded (often after clicking the 'Check all'
        #   button); don't download channels/playlists directly
        self.dl_by_video_flag = False
        # If True, during a custom download, perform a simulated download first
        #   (as happens by default in custom downloads launched from the
        #   Classic Mode tab). Ignored if self.dl_by_video_flag is False
        self.dl_precede_flag = False
        # If True, during a custom download, split a video into video clips
        #   using its timestamps. Ignored if self.dl_by_video_flag is False
        # Note that IVs for splitting videos (e.g.
        #   mainapp.TartubeApp.split_video_name_mode) apply in this situation
        #   as well
        self.split_flag = False
        # If True, during a custom download, video slices identified by
        #   SponsorBlock are removed. Ignored if self.dl_by_video_flag is
        #   False, or if self.split_flag is True
        self.slice_flag = False
        # A dictionary specifying which categories of video slice should be
        #   removed. Keys are SponsorBlock categories; values are True to
        #   remove the slice, False to retain it
        # NB A sorted list of keys from this dictionary appears in
        #   formats.SPONSORBLOCK_CATEGORY_LIST
        self.slice_dict = {
            'sponsor': True,
            'selfpromo': False,
            'interaction': False,
            'intro': False,
            'outro': False,
            'preview': False,
            'music_offtopic': False,
        }
        # If True, during a custom download, a delay (in minutes) is applied
        #   between media data object downloads. When applied to a
        #   channel/playlist, the delay occurs after the whole channel/
        #   playlist. When applied directly to videos, the delay occurs after
        #   each video
        # NB The delay is applied during real downloads, but not during
        #   simulated downloads (operation types 'custom_sim' or 'classic_sim')
        self.delay_flag = False
        # The maximum delay to apply (in minutes, minimum value 0.2). Ignored
        #   if self.delay_flag is False
        self.delay_max = 5
        # The minimum delay to apply (in minutes, minimum value 0, maximum
        #   value self.delay_max). If specified, the delay is a random length
        #   of time between this value and self.delay_max. Ignored if
        #   self.delay_flag is False
        self.delay_min = 0
        # During a custom download, any videos whose source URL is YouTube can
        #   be diverted to another website. This IV uses the values:
        #       'default' - Use the original YouTube URL
        #       'hooktube' - Divert to hooktube.com
        #       'invidious' - Divert to invidio.us
        #       'other' - user enters their own alternative front-end website
        self.divert_mode = 'default'
        # If self.divert_mode is 'other', the address of the YouTube
        #   alternative. The string directly replaces the 'youtube.com' part of
        #   a URL; so the string must be something like 'hooktube.com' not
        #   'http://hooktube.com' or anything like that
        # Ignored if it does not contain at least 3 characters. Ignored for any
        #   other value of self.divert_mode
        self.divert_website = ''


    # Public class methods


    def clone_settings(self, other_obj):

        """Called by mainapp.TartubeApp.clone_custom_dl_manager_from_window().

        Clones custom download settings from the specified object into this
        object, completely replacing this object's settings.

        Args:

            other_obj (downloads.CustomDLManager): The custom download manager
                object (usually the current one), from which settings will be
                cloned

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 6494 clone_settings')

        self.dl_by_video_flag = other_obj.dl_by_video_flag
        self.split_flag = other_obj.split_flag
        self.slice_flag = other_obj.slice_flag
        self.slice_dict = other_obj.slice_dict.copy()
        self.divert_mode = other_obj.divert_mode
        self.divert_website = other_obj.divert_website
        self.delay_flag = other_obj.delay_flag
        self.delay_min = other_obj.delay_min


    def reset_settings(self):

        """Currently not called by anything (but might be needed in the
        future).

        Resets settings to their default values.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 6494 reset_settings')

        self.dl_by_video_flag = False
        self.split_flag = False
        self.slice_flag = False
        self.slice_dict = {
            'sponsor': True,
            'selfpromo': False,
            'interaction': False,
            'intro': False,
            'outro': False,
            'preview': False,
            'music_offtopic': False,
        }
        self.divert_mode = 'default'
        self.divert_website = ''
        self.delay_flag = False
        self.delay_max = 5
        self.delay_min = 0


    def set_dl_precede_flag(self, flag):

        """Can be called by anything. Mostly called by
        mainapp.TartubeApp.start() and .set_dl_precede_flag().

        Updates the IV.

        Args:

            flag (bool): The new value of the IV

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 6494 set_dl_precede_flag')

        if not flag:
            self.dl_precede_flag = False
        else:
            self.dl_by_video_flag = True
            self.dl_precede_flag = True


class PipeReader(threading.Thread):

    """Called by downloads.VideoDownloader.__init__().

    Based on the PipeReader class in youtube-dl-gui.

    Python class used by downloads.VideoDownloader and updates.UpdateManager to
    avoid deadlocks when reading from child process pipes STDOUT and STDERR.

    This class uses python threads and queues in order to read from child
    process pipes in an asynchronous way.

    Args:

        queue (queue.Queue): Python queue to store the output of the child
            process.

    Warnings:

        All the actions are based on 'str' types. The calling function must
        convert the queued items back to 'unicode', if necessary

    """


    # Standard class methods


    def __init__(self, queue):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 6850 __init__')

        super(PipeReader, self).__init__()

        # IV list - other
        # ---------------
        # Python queue to store the output of the child process.
        self.output_queue = queue

        # The time (in seconds) between iterations of the loop in self.run()
        self.sleep_time = 0.25
        # Flag that is set to False by self.join(), which enables the loop in
        #   self.run() to terminate
        self.running_flag = True
        # Set by self.attach_file_descriptor(). The file descriptor for the
        #   child process STDOUT or STDERR
        self.file_descriptor = None


        # Code
        # ----

        # Let's get this party started!
        self.start()


    # Public class methods


    def run(self):

        """Called as a result of self.__init__().

        Reads from STDOUT or STERR using the attached filed descriptor.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 6887 run')

        # Use this flag so that the loop can ignore FFmpeg error messsages
        #   (because the parent VideoDownloader object shouldn't use that as a
        #   serious error)
        ignore_line = False

        while self.running_flag:

            if self.file_descriptor is not None:

                for line in iter(self.file_descriptor.readline, str('')):

                    if line == b'':
                        break

                    if str.encode('ffmpeg version') in line:
                        ignore_line = True

                    if not ignore_line:
                        self.output_queue.put_nowait(line)

                self.file_descriptor = None
                ignore_line = False

            time.sleep(self.sleep_time)


    def attach_file_descriptor(self, filedesc):

        """Called by downloads.VideoDownloader.do_download and comparable
        functions.

        Sets the file descriptor for the child process STDOUT or STDERR.

        Args:

            filedesc (filehandle): The open filehandle for STDOUT or STDERR

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 6929 attach_file_descriptor')

        self.file_descriptor = filedesc


    def join(self, timeout=None):

        """Called by downloads.VideoDownloader.close(), which is the destructor
        function for that object.

        Join the thread and update IVs.

        Args:

            timeout (-): No calling code sets a timeout

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 6948 join')

        self.running_flag = False
        super(PipeReader, self).join(timeout)
