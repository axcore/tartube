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


"""Download and livestream operation classes."""


# Import Gtk modules
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GObject


# Import other modules
import datetime
import json
import __main__
import signal
import os
import queue
import random
import re
import requests
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
            object's .dl_sim_flag IV. 'custom' is like 'real', but with
            additional options applied (specified by IVs like
            self.custom_dl_by_video_flag). 'classic' if the Classic Mode Tab is
            open, and the user has clicked the download button there

        download_list_obj(downloads.DownloadManager): An ordered list of
            media data objects to download, each one represented by a
            downloads.DownloadItem object

    """


    # Standard class methods


    def __init__(self, app_obj, operation_type, download_list_obj):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 119 __init__')

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
        # List of downloads.DownloadWorker objects, each one handling one of
        #   several simultaneous downloads
        self.worker_list = []


        # IV list - other
        # ---------------
        # 'sim' if channels/playlists should just be checked for new videos,
        #   without downloading anything. 'real' if videos should be downloaded
        #   (or not) depending on each media data object's .dl_sim_flag IV.
        #   'custom' is like 'real', but with additional options applied
        #   (specified by IVs like self.custom_dl_by_video_flag). 'classic' if
        #   the Classic Mode Tab is open, and the user has clicked the download
        #   button there
        # This is the default value for the download operation, when it starts.
        #   If the user wants to add new download.DownloadItem objects during
        #   an operation, the code can call
        #   downloads.DownloadList.create_item() with a non-default value of
        #   operation_type
        self.operation_type = operation_type

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

        # Number of download jobs started (number of downloads.DownloadItem
        #   objects which have been allocated to a worker)
        self.job_count = 0
        # The current downloads.DownloadItem being handled by self.run()
        #   (stored in this IV so that anything can update the main window's
        #   progress bar, at any time, by calling self.nudge_progress_bar() )
        self.current_item_obj = None

        # On-going counts of how many videos have been downloaded (real and
        #   simulated), and how much disk space has been consumed (in bytes),
        #   so that the operation can be auto-stopped, if required
        self.total_video_count = 0
        self.total_dl_count = 0
        self.total_sim_count = 0
        self.total_size_count = 0

        # If mainapp.TartubeApp.operation_convert_mode is set to any value
        #   other than 'disable', then a media.Video object whose URL
        #   represents a channel/playlist is converted into multiple new
        #   media.Video objects, one for each video actually downloaded
        # The original media.Video object is added to this list, via a call to
        #   self.mark_video_as_doomed(). At the end of the whole download
        #   operation, any media.Video object in this list is destroyed
        self.doomed_video_list = []


        # Code
        # ----

        # Create an object for converting download options stored in
        #   downloads.DownloadWorker.options_list into a list of youtube-dl
        #   command line options
        self.options_parser_obj = options.OptionsParser(self.app_obj)

        # Create a list of downloads.DownloadWorker objects, each one handling
        #   one of several simultaneous downloads
        for i in range(1, self.app_obj.num_worker_default + 1):
            self.worker_list.append(DownloadWorker(self))

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
            utils.debug_time('dld 219 run')

        manager_string = _('D/L Manager:') + '   '

        self.app_obj.main_win_obj.output_tab_write_stdout(
            0,
            manager_string + _('Starting download operation'),
        )

        # (Monitor changes to the number of workers, and number of available
        #   workers, so that we can display a running total in the Output Tab's
        #   summary page)
        local_worker_available_count = 0
        local_worker_total_count = 0

        # Perform the download operation until there is nothing left to
        #   download, or until something has called
        #   self.stop_download_operation()
        while self.running_flag:

            # Send a message to the Output Tab's summary page, if required
            available_count = 0
            total_count = 0
            for worker_obj in self.worker_list:
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

                    # Send a message to the Output Tab's summary page
                    self.app_obj.main_win_obj.output_tab_write_stdout(
                        0,
                        manager_string + _('All threads finished'),
                    )

                    break

            else:
                worker_obj = self.get_available_worker()

                # If the worker has been marked as doomed (because the number
                #   of simultaneous downloads allowed has decreased) then we
                #   can destroy it now
                if worker_obj and worker_obj.doomed_flag:

                    worker_obj.close()
                    self.remove_worker(worker_obj)

                # Otherwise, initialise the worker's IVs for the next job
                elif worker_obj:

                    # Send a message to the Output Tab's summary page
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
                    # Update the main window's progress bar
                    self.job_count += 1
                    # Throughout the downloads.py code, instead of calling a
                    #   mainapp.py or mainwin.py function directly (which is
                    #   not thread-safe), set a Glib timeout to handle it
                    if self.operation_type != 'classic':
                        self.nudge_progress_bar()

            # Pause a moment, before the next iteration of the loop (don't want
            #   to hog resources)
            time.sleep(self.sleep_time)

        # Download operation complete (or has been stopped). Send messages to
        #   the Output Tab's summary page
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
        if self.operation_type != 'classic':

            GObject.timeout_add(
                0,
                self.app_obj.main_win_obj.progress_list_display_dl_stats,
            )

        else:

            GObject.timeout_add(
                0,
                self.app_obj.main_win_obj.classic_mode_tab_display_dl_stats,
            )

        # Tell the Output Tab to display any remaining messages immediately
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

        # When youtube-dl reports it is finished, there is a short delay before
        #   the final downloaded video(s) actually exist in the filesystem
        # Therefore, mainwin.MainWin.progress_list_display_dl_stats() may not
        #   have marked the final video(s) as downloaded yet
        # Let the timer run for a few more seconds to allow those videos to be
        #   marked as downloaded (we can stop before that, if all the videos
        #   have been already marked)
        if self.operation_type != 'classic':
            GObject.timeout_add(
                0,
                self.app_obj.download_manager_halt_timer,
            )
        else:
            # For download operations launched from the Classic Mode Tab, we
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
            utils.debug_time('dld 435 apply_ignore_limits')

        for item_id in self.download_list_obj.download_item_list:

            download_item_obj \
            = self.download_list_obj.download_item_dict[item_id]
            download_item_obj.set_ignore_limits_flag()


    def change_worker_count(self, number):

        """Called by mainapp.TartubeApp.set_num_worker_default().

        When the number of simultaneous downloads allowed is changed during a
        download operation, this function responds.

        If the number has increased, creates an extra download worker object.

        If the number has decreased, marks the worker as doomed. When its
        current download is completed, the download manager destroys it.

        Args:

            number (int): The new value of
                mainapp.TartubeApp.num_worker_default

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 437 change_worker_count')

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
            utils.debug_time('dld 512 check_master_slave')

        for worker_obj in self.worker_list:

            if not worker_obj.available_flag \
            and worker_obj.download_item_obj:

                other_obj = worker_obj.download_item_obj.media_data_obj

                if other_obj.dbid != media_data_obj.dbid \
                and other_obj.dbid == media_data_obj.master_dbid:
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
            utils.debug_time('dld 542 check_workers_all_finished')

        for worker_obj in self.worker_list:
            if not worker_obj.available_flag:
                return False

        return True


    def get_available_worker(self):

        """Called by self.run().

        Based on DownloadManager._get_worker().

        Returns:

            The first available downloads.DownloadWorker, or None if there are
                no available workers.

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 565 get_available_worker')

        for worker_obj in self.worker_list:
            if worker_obj.available_flag:
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
            utils.debug_time('dld 596 mark_video_as_doomed')

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
            utils.debug_time('dld 616 nudge_progress_bar')

        if self.current_item_obj:

            GObject.timeout_add(
                0,
                self.app_obj.main_win_obj.update_progress_bar,
                self.current_item_obj.media_data_obj.name,
                self.job_count,
                    len(self.download_list_obj.download_item_list),
            )


    def register_video(self, dl_type):

        """Called by VideoDownloader.confirm_new_video(), when a video is
        downloaded, or by .confirm_sim_video(), when a simulated download finds
        a new video.

        (Can also be called by .confirm_old_video() when downloading from the
        Classic Mode Tab.)

        This function adds the new video to its ongoing total and, if a limit
        has been reached, stops the download operation.

        Args:

            dl_type (str): 'new', 'sim' or 'old', depending on the calling
                function

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 641 register_video')

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
            utils.debug_time('dld 665 register_video_size')

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
            utils.debug_time('dld 697 remove_worker')

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
            utils.debug_time('dld 724 stop_download_operation')

        self.running_flag = False


    def stop_download_operation_soon(self):

        """Called by mainwin.MainWin.on_progress_list_stop_all_soon(), after
        the user clicks the 'Stop after these videos' option in the Progress
        List.

        Stops the download operation, but only after any videos which are
        currently being downloaded have finished downloading.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 740 stop_download_operation_soon')

        self.download_list_obj.prevent_fetch_new_items()
        for worker_obj in self.worker_list:
            if worker_obj.running_flag:
                worker_obj.video_downloader_obj.stop_soon()


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
            manager object.

    """


    # Standard class methods


    def __init__(self, download_manager_obj):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 780 __init__')

        super(DownloadWorker, self).__init__()

        # IV list - class objects
        # -----------------------
        # The parent downloads.DownloadManager object
        self.download_manager_obj = download_manager_obj
        # The downloads.DownloadItem object for the current job
        self.download_item_obj = None
        # The downloads.VideoDownloader object for the current job (if it
        #   exists)
        self.video_downloader_obj = None
        # The downloads.JSONFetcher object for the current job (if it exists)
        self.json_fetcher_obj = None
        # The options.OptionsManager object for the current job
        self.options_manager_obj = None


        # IV list - other
        # ---------------
        # A number identifying this worker, matching the number of the page
        #   in the Output Tab (so the first worker created is #1)
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
        create a new downloads.VideoDownloader object and wait for the result.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 844 run')

        # Import the main application (for convenience)
        app_obj = self.download_manager_obj.app_obj

        # Handle a job, or wait for the downloads.DownloadManager to assign
        #   this worker a job
        while self.running_flag:

            # If this worker is currently assigned a job...
            if not self.available_flag:

                # Import the media data object (for convenience)
                media_data_obj = self.download_item_obj.media_data_obj

                # If the download stalls, the VideoDownloader may need to be
                #   replaced with a new one. Use a while loop for that
                first_flag = True
                while True:

                    # Set up the new downloads.VideoDownloader object
                    self.video_downloader_obj = VideoDownloader(
                        self.download_manager_obj,
                        self,
                        self.download_item_obj,
                    )

                    if first_flag:

                        first_flag = False
                        # Send a message to the Output Tab's summary page
                        app_obj.main_win_obj.output_tab_write_stdout(
                            0,
                            _('Thread #') + str(self.worker_id) \
                            + ': ' + _('Assigned job:') + ' \'' \
                            + self.download_item_obj.media_data_obj.name \
                            + '\'',
                        )

                    # Execute the assigned job
                    return_code = self.video_downloader_obj.do_download()
                    # If a restart is required, -1 is returned
                    if return_code > -1:
                        break

                # If the downloads.VideoDownloader object collected any
                #   youtube-dl error/warning messages, display them in the
                #   Error List
                if media_data_obj.error_list or media_data_obj.warning_list:
                    GObject.timeout_add(
                        0,
                        app_obj.main_win_obj.errors_list_add_row,
                        media_data_obj,
                    )

                # In the event of an error, nothing updates the video's row in
                #   the Video Catalogue, and therefore the error icon won't be
                #   visible
                # Do that now (but don't if mainwin.ComplexCatalogueItem
                #   objects aren't being used in the Video Catalogue)
                if self.download_item_obj.operation_type != 'classic' \
                and return_code == VideoDownloader.ERROR \
                and isinstance(media_data_obj, media.Video) \
                and app_obj.catalogue_mode_type != 'simple':
                    GObject.timeout_add(
                        0,
                        app_obj.main_win_obj.video_catalogue_update_video,
                        media_data_obj,
                    )

                # Call the destructor function of VideoDownloader object
                self.video_downloader_obj.close()

                # If possible, check the channel/playlist RSS feed for videos
                #   we don't already have, and mark them as livestreams
                if self.running_flag \
                and mainapp.HAVE_FEEDPARSER_FLAG \
                and app_obj.enable_livestreams_flag \
                and (
                    isinstance(media_data_obj, media.Channel) \
                    or isinstance(media_data_obj, media.Playlist)
                ) and media_data_obj.child_list \
                and media_data_obj.rss:

                    # Send a message to the Output Tab's summary page
                    app_obj.main_win_obj.output_tab_write_stdout(
                        0,
                        _('Thread #') + str(self.worker_id) \
                        + ': ' + _('Checking RSS feed'),
                    )

                    # Check the RSS feed for the media data object
                    self.check_rss(media_data_obj)

                # Send a message to the Output Tab's summary page
                app_obj.main_win_obj.output_tab_write_stdout(
                    0,
                    _('Thread #') + str(self.worker_id) \
                    + ': ' + _('Job complete') + ' \'' \
                    + self.download_item_obj.media_data_obj.name + '\'',
                )

                # This worker is now available for a new job
                self.available_flag = True

                # Send a message to the Output Tab's summary page
                app_obj.main_win_obj.output_tab_write_stdout(
                    0,
                    _('Thread #') + str(self.worker_id) \
                    + ': ' + _('Worker now available again'),
                )

                # During custom downloads, apply a delay if one has been
                #   specified
                if self.download_item_obj.operation_type == 'custom' \
                and app_obj.custom_dl_delay_flag:

                    # Set the delay (in seconds), a randomised value if
                    #   required
                    if app_obj.custom_dl_delay_min:
                        delay = random.randint(
                            int(app_obj.custom_dl_delay_min * 60),
                            int(app_obj.custom_dl_delay_max * 60),
                        )
                    else:
                        delay = int(app_obj.custom_dl_delay_max * 60)

                    time.sleep(delay)

            # Pause a moment, before the next iteration of the loop (don't want
            #   to hog resources)
            time.sleep(self.sleep_time)


    def close(self):

        """Called by downloads.DownloadManager.run().

        This worker object is closed when:

            1. The download operation is complete (or has been stopped)
            2. The worker has been marked as doomed, and the calling function
                is now ready to destroy it

        Tidy up IVs and stop any child processes.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 986 close')

        self.running_flag = False

        if self.video_downloader_obj:
            self.video_downloader_obj.stop()

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
            utils.debug_time('dld 1029 check_rss')

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
            utils.debug_time('dld 1176 prepare_download')

        self.download_item_obj = download_item_obj
        self.options_manager_obj = download_item_obj.options_manager_obj

        self.options_list = self.download_manager_obj.options_parser_obj.parse(
            self.download_item_obj.media_data_obj,
            self.options_manager_obj,
            self.download_item_obj.operation_type,
        )

        self.available_flag = False


    def set_doomed_flag(self, flag):

        """Called by downloads.DownloadManager.change_worker_count()."""

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 1200 set_doomed_flag')

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
            utils.debug_time('dld 1232 data_callback')

        app_obj = self.download_manager_obj.app_obj

        if self.download_item_obj.operation_type != 'classic':

            GObject.timeout_add(
                0,
                app_obj.main_win_obj.progress_list_receive_dl_stats,
                self.download_item_obj,
                dl_stat_dict,
                last_flag,
            )

        else:

            GObject.timeout_add(
                0,
                app_obj.main_win_obj.classic_mode_tab_receive_dl_stats,
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
            object's .dl_sim_flag IV. 'custom' is like 'real', but with
            additional options applied (specified by IVs like
            self.custom_dl_by_video_flag). 'classic' if the Classic Mode Tab is
            open, and the user has clicked the download button there

        media_data_list (list): List of media.Video, media.Channel,
            media.Playlist and/or media.Folder objects. Can also be a list of
            (exclusively) media.Scheduled objects. If not an empty list, only
            the specified media data objects (and their children) are
            checked/downloaded. If an empty list, all media data objects are
            checked/downloaded. If operation_type is 'classic', then the
            media_data_list contains a list of dummy media.Video objects from a
            previous call to this function. If an empty list, all
            dummy media.Video objects are downloaded

    """


    # Standard class methods


    def __init__(self, app_obj, operation_type, media_data_list):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 1302 __init__')

        # IV list - class objects
        # -----------------------
        self.app_obj = app_obj


        # IV list - other
        # ---------------
        # 'sim' if channels/playlists should just be checked for new videos,
        #   without downloading anything. 'real' if videos should be downloaded
        #   (or not) depending on each media data object's .dl_sim_flag IV.
        #   'custom' is like 'real', but with additional options applied
        #   (specified by IVs like self.custom_dl_by_video_flag). 'classic' if
        #   the Classic Mode Tab is open, and the user has clicked the download
        #   button there
        # This IV records the default setting for this operation. Once the
        #   download operation starts, new download.DownloadItem objects can
        #   be added to the list in a call to self.create_item(), and that call
        #   can specify a value ('sim', 'real' or 'custom') that overrides the
        #   default value, just for that call
        # Overriding the default value is not possible for download operations
        #   initiated from the Classic Mode tab
        self.operation_type = operation_type
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
        #   launched from the Classic Mode Tab)
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

        # Corresponding dictionary of downloads.DownloadItem items for quick
        #   lookup, containing items from both self.download_item_list and
        #   self.temp_item_list
        # Dictionary in the form
        #   key = download.DownloadItem.item_id
        #   value = the download.DownloadItem object itself
        self.download_item_dict = {}

        # Code
        # ----

        if media_data_list and isinstance(media_data_list[0], media.Scheduled):

            # media_data_list is a list of scheduled downloads
            all_flag = False
            ignore_limits_flag = False

            for scheduled_obj in media_data_list:
                if scheduled_obj.all_flag:
                    all_flag = True
                if scheduled_obj.ignore_limits_flag:
                    ignore_limits_flag = True

            if all_flag:

                # Use all media data objects
                for dbid in self.app_obj.media_top_level_list:
                    obj = self.app_obj.media_reg_dict[dbid]
                    self.create_item(
                        obj,
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
                                scheduled_obj.dl_mode,
                                priority_flag,
                                scheduled_obj.ignore_limits_flag,
                            )

                            check_dict[name] = None

        elif self.operation_type != 'classic':

            # For each media data object to be downloaded, create a
            #   downloads.DownloadItem object, and update the IVs above
            if not media_data_list:

                # Use all media data objects
                for dbid in self.app_obj.media_top_level_list:
                    obj = self.app_obj.media_reg_dict[dbid]
                    self.create_item(
                        obj,
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

                        # Use the specified media data object. The True value
                        #   tells self.create_item() to download
                        #   media_data_obj, even if it is a video in a channel
                        #   or a playlist (which otherwise would be handled by
                        #   downloading the channel/playlist)
                        self.create_item(
                            media_data_obj,
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

        else:

            # The download operation was launched from the Classic Mode Tab.
            #   Each URL to be downloaded is represented by a dummy media.Video
            #   object (one which is not in the media data registry)
            main_win_obj = self.app_obj.main_win_obj

            # The user may have rearranged rows in the Classic Mode Tab, so
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
            for dummy_obj in obj_list:
                self.create_dummy_item(dummy_obj)

        # We can now merge the two DownloadItem lists
        if self.temp_item_list:

            self.download_item_list \
            = self.temp_item_list + self.download_item_list
            self.temp_item_list = []


    # Public class methods


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
            utils.debug_time('dld 1453 change_item_stage')

        self.download_item_dict[item_id].stage = new_stage


    def create_item(self, media_data_obj, override_operation_type=None,
    priority_flag=False, ignore_limits_flag=False, recursion_flag=False):

        """Called initially by self.__init__() (or by many other functions,
        for example in mainapp.TartubeApp).

        Subsequently called by this function recursively.

        Creates a downloads.DownloadItem object for media data objects in the
        media data registry.

        Doesn't create a download item object for:
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
            - media.Channel and media.Playlist objects during custom downloads
                in which videos are to be downloaded independently
            - media.Folder objects

        Adds the resulting downloads.DownloadItem object to this object's IVs.

        Args:

            media_data_obj (media.Video, media.Channel, media.Playlist,
                media.Folder): A media data object

            override_operation_type (str): After the download operation has
                started, any code can call this function to add new
                downloads.DownloadItem objects to this downloads.DownloadList,
                specifying a value that overrides the default value of
                self.operation_type. Note that this is not allowed when
                self.operation_type is 'classic', and will cause an error. The
                value is always None when called by self.__init__(). Otherwise,
                the value can be None, 'sim', 'real' or 'custom'

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
            utils.debug_time('dld 1508 create_item')

        # Apply the operation_type override, if specifed
        if override_operation_type is not None:

            if self.operation_type == 'classic':

                GObject.timeout_add(
                    0,
                    app_obj.system_error,
                    306,
                    'Invalid argument in Classic Mode tab download operation',
                )

                return None

            else:

                operation_type = override_operation_type

        else:

            operation_type = self.operation_type

        # Get the options.OptionsManager object that applies to this media
        #   data object
        # (The manager might be specified by obj itself, or it might be
        #   specified by obj's parent, or we might use the default
        #   options.OptionsManager)
        if operation_type != 'classic':
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
        #   and the video has already been checked
        # (Exception: do download videos in a folder if they're marked as
        #   livestreams, in case the livestream has finished)
        if isinstance(media_data_obj, media.Video):

            if media_data_obj.dl_flag \
            or (
                not isinstance(media_data_obj.parent_obj, media.Folder) \
                and recursion_flag
                and (
                    operation_type != 'custom'
                    or not self.app_obj.custom_dl_by_video_flag
                    or media_data_obj.dl_flag
                )
            ):
                return None

            if isinstance(media_data_obj.parent_obj, media.Folder) \
            and operation_type == 'sim' \
            and self.app_obj.operation_sim_shortcut_flag \
            and media_data_obj.file_name \
            and not media_data_obj.live_mode \
            and utils.find_thumbnail(self.app_obj, media_data_obj):
                return None

        # Don't create a download.DownloadItem object if the media data object
        #   has an ancestor for which checking/downloading is disabled
        if isinstance(media_data_obj, media.Video):
            dl_disable_flag = False
        else:
            dl_disable_flag = media_data_obj.dl_disable_flag

        parent_obj = media_data_obj.parent_obj

        while not dl_disable_flag and parent_obj is not None:
            dl_disable_flag = parent_obj.dl_disable_flag
            parent_obj = parent_obj.parent_obj

        if dl_disable_flag:
            return None

        # Don't create a download.DownloadItem object for a media.Folder,
        #   obviously
        # Don't create a download.DownloadItem object for a media.Channel or
        #   media.Playlist during a custom download in which videos are to be
        #   downloaded independently
        download_item_obj = None

        if (
            isinstance(media_data_obj, media.Video)
            and operation_type == 'custom'
            and self.app_obj.custom_dl_by_video_flag
            and not media_data_obj.dl_flag
        ) or (
            isinstance(media_data_obj, media.Video)
            and (
                operation_type != 'custom'
                or not self.app_obj.custom_dl_by_video_flag
            )
        ) or (
            (
                isinstance(media_data_obj, media.Channel) \
                or isinstance(media_data_obj, media.Playlist)
            ) and (
                operation_type != 'custom'
                or not self.app_obj.custom_dl_by_video_flag
            )
        ):
            # Create a new download.DownloadItem object...
            self.download_item_count += 1
            download_item_obj = DownloadItem(
                self.download_item_count,
                media_data_obj,
                options_manager_obj,
                operation_type,
                ignore_limits_flag,
            )

            # ...and add it to our list
            if priority_flag:
                self.download_item_list.append(download_item_obj.item_id)
            else:
                self.temp_item_list.append(download_item_obj.item_id)

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
            and operation_type == 'custom'
            and self.app_obj.custom_dl_by_video_flag
        ):
            for child_obj in media_data_obj.child_list:
                self.create_item(
                    child_obj,
                    operation_type,
                    priority_flag,
                    ignore_limits_flag,
                    True,                   # Recursion
                )

        # Procedure complete
        return download_item_obj


    def create_dummy_item(self, media_data_obj):

        """Called by self.__init__() only, when the download operation was
        launched from the Classic Mode Tab (this function is not called
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
            utils.debug_time('dld 1647 create_dummy_item')

        if self.app_obj.classic_options_obj is not None:
            options_manager_obj = self.app_obj.classic_options_obj
        else:
            options_manager_obj = self.app_obj.general_options_obj

        # Create a new download.DownloadItem object...
        self.download_item_count += 1
        download_item_obj = DownloadItem(
            media_data_obj.dbid,
            media_data_obj,
            options_manager_obj,
            self.operation_type,        # 'classic'
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
                left.

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 1680 fetch_next_item')

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
            utils.debug_time('dld 1712 move_item_to_bottom')

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
            utils.debug_time('dld 1743 move_item_to_top')

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
            utils.debug_time('dld 1769 prevent_fetch_new_items')

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
            utils.debug_time('dld 1794 reorder_master_slave')

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

        item_id (int) - The number of downloads.DownloadItem objects created,
            used to give each one a unique ID

        media_data_obj (media.Video, media.Channel, media.Playlist,
            media.Folder): The media data object to be downloaded. When the
            download operation was launched from the Classic Mode Tab, a dummy
            media.Video object

        options_manager_obj (options.OptionsManager): The object which
            specifies download options for the media data object

        operation_type (str): The value that applies to this DownloadItem only
            (might be different from the default value stored in
            DownloadManager.operation_type): 'sim' if channels/playlists should
            just be checked for new videos, without downloading anything.
            'real' if videos should be downloaded (or not) depending on each
            media data object's .dl_sim_flag IV. 'custom' is like 'real', but
            with additional options applied (specified by IVs like
            self.custom_dl_by_video_flag). 'classic' if the Classic Mode Tab is
            open, and the user has clicked the download button there

    """


    # Standard class methods


    def __init__(self, item_id, media_data_obj, options_manager_obj,
    operation_type, ignore_limits_flag):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 1844 __init__')

        # IV list - class objects
        # -----------------------
        # The media data object to be downloaded. When the download operation
        #   was launched from the Classic Mode Tab, a dummy media.Video object
        self.media_data_obj = media_data_obj
        # The object which specifies download options for the media data object
        self.options_manager_obj = options_manager_obj

        # IV list - other
        # ---------------
        # A unique ID for this object
        self.item_id = item_id
        # The current download stage
        self.stage = formats.MAIN_STAGE_QUEUED

        # The value that applies to this DownloadItem only (might be different
        #   from the default value stored in DownloadManager.operation_type):
        #   'sim' if channels/playlists should just be checked for new videos,
        #   without downloading anything. 'real' if videos should be downloaded
        #   (or not) depending on each media data object's .dl_sim_flag IV.
        #   'custom' is like 'real', but with additional options applied
        #   (specified by IVs like self.custom_dl_by_video_flag). 'classic' if
        #   the Classic Mode Tab is open, and the user has clicked the download
        #   button there
        self.operation_type = operation_type
        # Flag set to True if operation limits
        #   (mainapp.TartubeApp.operation_limit_flag) should be ignored
        self.ignore_limits_flag = ignore_limits_flag


    # Set accessors


    def set_ignore_limits_flag(self):

        """Called by DownloadManager.apply_ignore_limits(), following a call
        from mainapp>TartubeApp.script_slow_timer_callback()."""

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 1844 set_ignore_limits_flag')

        self.ignore_limits_flag = True


class VideoDownloader(object):

    """Called by downloads.DownloadWorker.run().

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
    # 6 - The download operation has stalled, and must be restarted by the
    #   parent worker
    RESTART = -1


    # Standard class methods


    def __init__(self, download_manager_obj, download_worker_obj, \
    download_item_obj):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 1937 __init__')

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
        #   Classic Mode Tab, False if not (set below)
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
        # Dictionary of videos, used to check for the first completion message
        #   for each unique video
        # Dictionary in the form
        #       key = the video number (matches self.video_num)
        #       value = the video name (not actually used by anything at the
        #           moment)
        self.video_check_dict = {}
        # The code imported from youtube-dl-gui doesn't recognise a downloaded
        #   video, if Ffmpeg isn't used to extract it (because Ffmpeg is not
        #   installed, or because the website doesn't support it, or whatever)
        # In this situation, youtube-dl's STDOUT messages don't definitively
        #   establish when it has finished downloading a video
        # When a file destination is announced; it is temporarily stored in
        #   these IVs. When STDOUT receives a message in the form
        #       [download] 100% of 2.06MiB in 00:02
        #   ...and the filename isn't one that Ffmpeg would use (e.g.
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
        #   Mode Tab)
        # The setting applies not just to the media data object, but all of its
        #   descendants
        if self.download_item_obj.operation_type != 'classic':

            if self.download_item_obj.operation_type == 'sim':
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

        """Called by downloads.DownloadWorker.run().

        Based on YoutubeDLDownloader.download().

        Downloads video(s) from a URL described by self.download_item_obj.

        Returns:

            The final return code, a value in the range 0-5 (as described
            above)

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 2131 do_download')

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
        divert_mode = None
        if not self.dl_classic_flag \
        and self.download_item_obj.operation_type == 'custom' \
        and isinstance(self.download_item_obj.media_data_obj, media.Video):
            divert_mode = app_obj.custom_dl_divert_mode

        cmd_list = utils.generate_system_cmd(
            app_obj,
            self.download_item_obj.media_data_obj,
            self.download_worker_obj.options_list,
            self.dl_sim_flag,
            self.dl_classic_flag,
            self.missing_video_check_flag,
            divert_mode,
        )

        # ...display it in the Output Tab (if required)...
        if app_obj.ytdl_output_system_cmd_flag:
            space = ' '
            app_obj.main_win_obj.output_tab_write_system_cmd(
                self.download_worker_obj.worker_id,
                space.join(cmd_list),
            )

        # ...and the terminal (if required)...
        if app_obj.ytdl_write_system_cmd_flag:
            space = ' '
            print(space.join(cmd_list))

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

        # While downloading the video, update the callback function with
        #   the status of the current job
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
                    if os.name == 'nt':
                        stdout = stdout.decode('cp1252', errors="replace")
                    else:
                        stdout = stdout.decode('utf-8', errors="replace")

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

                    # Show output in the Output Tab (if required). For
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
                            print(stdout)
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
                    302,
                    'Enforced timeout because downloader took too long to' \
                    + ' fetch a video\'s JSON data',
                )

            # Restart a stalled download, if required
            restart_time = (app_obj.operation_auto_restart_time * 60)
            if app_obj.operation_auto_restart_flag \
            and self.last_activity_time is not None \
            and (self.last_activity_time + restart_time) < time.time():

                # Show confirmation of the restart
                if app_obj.ytdl_output_stdout_flag:
                    app_obj.main_win_obj.output_tab_write_stdout(
                        self.download_worker_obj.worker_id,
                        _('Tartube is restarting stalled download'),
                    )

                if app_obj.ytdl_write_stdout_flag:
                    print(_('Tartube is restarting stalled download'))

                # Tell the parent worker to replace this VideoDownloader with a
                #   new one
                self.stop()
                return self.RESTART

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
            if os.name == 'nt':
                stderr = stderr.decode('cp1252', errors="replace")
            else:
                stderr = stderr.decode('utf-8', errors="replace")

            if not self.is_ignorable(stderr):

                if self.is_warning(stderr):
                    self.set_return_code(self.WARNING)
                    self.download_item_obj.media_data_obj.set_warning(stderr)

                elif not self.is_debug(stderr):
                    self.set_return_code(self.ERROR)
                    self.download_item_obj.media_data_obj.set_error(stderr)

            # Show output in the Output Tab (if required)
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
                    print(stderr)
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
        if self.child_process is None:
            self.set_return_code(self.ERROR)
            self.download_item_obj.media_data_obj.set_error(
                _('Download did not start'),
            )

        elif self.child_process.returncode > 0:
            self.set_return_code(self.ERROR)

            if not app_obj.ignore_child_process_exit_flag:
                self.download_item_obj.media_data_obj.set_error(
                    _('Child process exited with non-zero code: {}').format(
                        self.child_process.returncode,
                    )
                )

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
            utils.debug_time('dld 2387 check_dl_is_correct_type')

        # Special case: if the download operation was launched from the
        #   Classic Mode Tab, there is no need to do anything
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

        """Called by DownloadWorker.run().

        Destructor function for this object.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 2456 close')

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
            utils.debug_time('dld 2457 compile_mini_options_dict')

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
            utils.debug_time('dld 2458 confirm_archived_video')

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
        first announcement to update self.video_check_dict, and ignore
        subsequent announcements.

        Args:

            dir_path (str): The full path to the directory in which the video
                is saved, e.g. '/home/yourname/tartube/downloads/Videos'

            filename (str): The video's filename, e.g. 'My Video'

            extension (str): The video's extension, e.g. '.mp4'

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 2485 confirm_new_video')

        # Special case: if the download operation was launched from the
        #   Classic Mode Tab, then we only need to update the dummy
        #   media.Video object
        if self.dl_classic_flag:

            media_data_obj = self.download_item_obj.media_data_obj
            media_data_obj.set_dummy_path(
                os.path.abspath(os.path.join(dir_path, filename + extension)),
            )

            # Register the download with DownloadManager, so that download
            #   limits can be applied, if required
            self.download_manager_obj.register_video('new')

        # All other cases
        elif not self.video_num in self.video_check_dict:

            app_obj = self.download_manager_obj.app_obj
            self.video_check_dict[self.video_num] = filename

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
            # The True argument specifies that this function is the caller
            self.download_manager_obj.register_video('new')

        # This VideoDownloader can now stop, if required to do so after a video
        #   has been checked/downloaded
        if self.stop_soon_flag:
            self.stop_now_flag = True


    def confirm_old_video(self, dir_path, filename, extension):

        """Called by self.extract_stdout_data().

        When youtube-dl reports a video has already been downloaded, make sure
        the media.Video object is marked as downloaded, and upate the video
        catalogue in the main window if necessary.

        Args:

            dir_path (str): The full path to the directory in which the video
                is saved, e.g. '/home/yourname/tartube/downloads/Videos'

            filename (str): The video's filename, e.g. 'My Video'

            extension (str): The video's extension, e.g. '.mp4'

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 2581 confirm_old_video')

        # Create shortcut variables (for convenience)
        app_obj = self.download_manager_obj.app_obj
        media_data_obj = self.download_item_obj.media_data_obj

        # Special case: if the download operation was launched from the
        #   Classic Mode Tab, then we only need to update the dummy
        #   media.Video object
        if self.dl_classic_flag:

            media_data_obj.set_dummy_path(
                os.path.abspath(os.path.join(dir_path, filename, extension)),
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
                self.video_check_dict[self.video_num] = filename

                video_obj = app_obj.create_video_from_download(
                    self.download_item_obj,
                    dir_path,
                    filename,
                    extension,
                )

                # Update the main window
                if media_data_obj.master_dbid != media_data_obj.dbid:

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
            utils.debug_time('dld 2715 confirm_sim_video')

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
                303,
                'Missing filename in JSON data',
            )

            return

        if 'upload_date' in json_dict:
            # date_string in form YYYYMMDD
            date_string = json_dict['upload_date']
            dt_obj = datetime.datetime.strptime(date_string, '%Y%m%d')
            upload_time = dt_obj.timestamp()
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

        if 'description' in json_dict:
            descrip = json_dict['description']
        else:
            descrip = None

        if 'thumbnail' in json_dict:
            thumbnail = json_dict['thumbnail']
        else:
            thumbnail = None

        if 'webpage_url' in json_dict:
            source = json_dict['webpage_url']
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

            if upload_time is not None:
                video_obj.set_upload_time(upload_time)

            if duration is not None:
                video_obj.set_duration(duration)

            if source is not None:
                video_obj.set_source(source)

            if descrip is not None:
                video_obj.set_video_descrip(
                    descrip,
                    app_obj.main_win_obj.descrip_line_max_len,
                )

            # If downloading from a channel/playlist, remember the video's
            #   index. (The server supplies an index even for a channel, and
            #   the user might want to convert a channel to a playlist)
            if isinstance(video_obj.parent_obj, media.Channel) \
            or isinstance(video_obj.parent_obj, media.Playlist):
                video_obj.set_index(playlist_index)

            # Now we can sort the parent containers
            video_obj.parent_obj.sort_children()
            app_obj.fixed_all_folder.sort_children()
            if video_obj.bookmark_flag:
                app_obj.fixed_bookmark_folder.sort_children()
            if video_obj.fav_flag:
                app_obj.fixed_fav_folder.sort_children()
            if video_obj.live_mode:
                app_obj.fixed_live_folder.sort_children()
            if video_obj.missing_flag:
                app_obj.fixed_missing_folder.sort_children()
            if video_obj.new_flag:
                app_obj.fixed_new_folder.sort_children()
            if video_obj.waiting_flag:
                app_obj.fixed_waiting_folder.sort_children()

        else:

            # This video will not be marked as a missing video
            if video_obj in self.missing_video_check_list:
                self.missing_video_check_list.remove(video_obj)

            if video_obj.file_name \
            and video_obj.name != app_obj.default_video_name:

                # This video must not be displayed in the Results List, and
                #   does counts towards the limit (if any) specified by
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
                    #   stop checking videos in this channel playlist
                    stop_flag = True

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

            if not video_obj.upload_time and upload_time is not None:
               video_obj.set_upload_time(upload_time)

            if not video_obj.duration and duration is not None:
                video_obj.set_duration(duration)

            if not video_obj.source and source is not None:
                video_obj.set_source(source)

            if not video_obj.descrip and descrip is not None:
                video_obj.set_video_descrip(
                    descrip,
                    app_obj.main_win_obj.descrip_line_max_len,
                )

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
                    request_obj = requests.get(thumbnail)
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
                    307,
                    app_obj.ffmpeg_fail_msg,
                )

            # Move to the sub-directory, if required
            if options_dict['move_thumbnail']:

                utils.move_thumbnail_to_subdir(app_obj, video_obj)

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
        #   anything in the Output Tab/terminal window; so do that now (if
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
            if os.name == 'nt':
                filename = filename.encode().decode('cp1252', errors="replace")

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
            utils.debug_time('dld 3132 convert_video_to_container')

        app_obj = self.download_manager_obj.app_obj
        old_video_obj = self.download_item_obj.media_data_obj
        container_obj = old_video_obj.parent_obj

        # Some media.Folder objects cannot contain channels or playlists (for
        #   example, the 'Unsorted Videos' folder)
        # If that is the case, the new channel/playlist is created without a
        #   parent. Otherwise, it is created at the same location as the
        #   original media.Video object
        if container_obj.restrict_flag:
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
        utils.generate_system_cmd().

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
            utils.debug_time('dld 3251 create_child_process')

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
            utils.debug_time('dld 3302 extract_filename')

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
            utils.debug_time('dld 3352 extract_stdout_data')

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
                    #   Ffmpeg, then this marks the end of a video download
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
                dl_stat_dict['status'] = formats.COMPLETED_STAGE_ALREADY
                path, filename, extension = self.extract_filename(
                    ' '.join(stdout_with_spaces_list[1:-4]),
                )

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

        elif stdout_list[0] == '[ffmpeg]':

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
                        304,
                        'Invalid JSON data received from server',
                    )

                    return dl_stat_dict

                if json_dict:

                    # If youtube-dl is about to download a channel or playlist
                    #   into a media.Video object, decide what to do to prevent
                    #   that
                    # The called function returns a True/False value,
                    #   specifically to allow this code block to call
                    #   self.confirm_sim_video when required
                    # v1.3.063 At this point, self.video_num can be None or 0
                    #   for a URL that's an individual video, but > 0 for a URL
                    #   that's actually a channel/playlist
                    if not self.video_num \
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
            utils.debug_time('dld 3635 extract_stdout_status')

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

            True if the child process is alive, otherwise returns False.

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 3663 is_child_process_alive')

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
            utils.debug_time('dld 3693 is_debug')

        return stderr.split(' ')[0] == '[debug]'


    def is_ignorable(self, stderr):

        """Called by self.do_download().

        Before testing a STDERR message, see if it's one of the frequent
        messages which the user has opted to ignore (if any).

        Args:

            stderr (str): A message from the child process STDERR

        Returns:

            True if the STDERR message is ignorable, False if it should be
                tested further.

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 3717 is_ignorable')

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
            utils.debug_time('dld 3836 is_warning')

        return stderr.split(':')[0] == 'WARNING'


    def last_data_callback(self):

        """Called by self.download().

        Based on YoutubeDLDownloader._last_data_hook().

        After the child process has finished, creates a new Python dictionary
        in the standard form described by self.extract_stdout_data().

        Sets key-value pairs in the dictonary, then passes it to the parent
        downloads.DownloadWorker object, confirming the result of the child
        process.

        The new key-value pairs are used to update the main window.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 3858 last_data_callback')

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
        else:
            dl_stat_dict['status'] = formats.ERROR_STAGE_ABORT

        # Use some empty values in dl_stat_dict so that the Progress Tab
        #   doesn't show arbitrary data from the last file downloaded
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
            utils.debug_time('dld 3912 set_return_code')

        if code >= self.return_code:
            self.return_code = code


    def set_temp_destination(self, path, filename, extension):

        """Called by self.extract_stdout_data()."""

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 3923 set_temp_destination')

        self.temp_path = path
        self.temp_filename = filename
        self.temp_extension = extension


    def reset_temp_destination(self):

        """Called by self.extract_stdout_data()."""

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 3935 reset_temp_destination')

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
            utils.debug_time('dld 3952 stop')

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
            utils.debug_time('dld 3982 stop_soon')

        self.stop_soon_flag = True


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
            utils.debug_time('dld 4051 __init__')

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
            # A time.struct_time object; convert to Unix time, to match
            #   media.Video.upload_time
            dt_obj = datetime.datetime.fromtimestamp(
                time.mktime(entry_dict['published_parsed']),
            )

            self.video_upload_time = int(dt_obj.timestamp())


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
            utils.debug_time('dld 4141 do_fetch')

        # Import the main app (for convenience)
        app_obj = self.download_manager_obj.app_obj

        # Convert a youtube-dl path beginning with ~ (not on MS Windows)
        #   (code copied from utils.generate_system_cmd() )
        ytdl_path = app_obj.check_downloader(app_obj.ytdl_path)
        if os.name != 'nt':
            ytdl_path = re.sub('^\~', os.path.expanduser('~'), ytdl_path)

        # Generate the system command...
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
                stdout = stdout.decode()
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
                    stderr = stderr.decode()
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
                        request_obj = requests.get(self.video_thumb_source)
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
                        308,
                        app_obj.ffmpeg_fail_msg,
                    )


    def close(self):

        """Called by downloads.DownloadWorker.check_rss().

        Destructor function for this object.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 4275 close')

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
            utils.debug_time('dld 4302 create_child_process')

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
            utils.debug_time('dld 4347 is_child_process_alive')

        if self.child_process is None:
            return False

        return self.child_process.poll() is None


    def stop(self):

        """Called by DownloadWorker.close().

        Terminates the child process.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 4363 stop')

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


class LivestreamManager(threading.Thread):

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
            utils.debug_time('dld 4405 __init__')

        super(LivestreamManager, self).__init__()

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
            utils.debug_time('dld 4468 run')

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
            utils.debug_time('dld 4517 mark_video_as_missing')

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
            utils.debug_time('dld 4539 mark_video_as_started')

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
            utils.debug_time('dld 4561 mark_video_as_stopped')

        self.video_stopped_dict[video_obj.dbid] = video_obj


    def stop_livestream_operation(self):

        """Can be called by anything.

        Based on downloads.DownloadManager.stop_downloads().

        Stops the livestream operation. On the next iteration of self.run()'s
        loop, the downloads.MiniJSONFetcher objects are cleaned up.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 4577 stop_livestream_operation')

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

    """Called by downloads.LivestreamManager.run().

    A modified version of downlaods.JSONFetcher (the former is called by
    downloads.DownloadWorker only; using a second Python class for the same
    objective makes the code somewhat simpler).

    Python class to fetch JSON data for a livestream video, using youtube-dl.

    Creates a system child process and uses the child process to instruct
    youtube-dl to fetch the JSON data for the video.

    Reads from the child process STDOUT and STDERR, having set up a
    downloads.PipeReader object to do so in an asynchronous way.

    Args:

        livestream_manager_obj (downloads.LivestreamManager): The livestream
            manager object handling the entire livestream operation

        video_obj (media.Video): The livestream video whose JSON data should be
            fetched (the equivalent of right-clicking the video in the Video
            Catalogue, and selecting 'Check this video')

    """


    # Standard class methods


    def __init__(self, livestream_manager_obj, video_obj):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 4626 __init__')

        # IV list - class objects
        # -----------------------
        # The downloads.LivestreamManager object handling the entire livestream
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

        """Called by downloads.LivestreamManager.run().

        Downloads JSON data for the livestream video, self.video_obj.

        If the data can be downloaded, we assume that the livestream is
        currently broadcasting. If we get a 'This video is unavailable' error,
        we assume that the livestream is waiting to start.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 4674 do_fetch')

        # Import the main app (for convenience)
        app_obj = self.livestream_manager_obj.app_obj

        # Convert a youtube-dl path beginning with ~ (not on MS Windows)
        #   (code copied from utils.generate_system_cmd() )
        ytdl_path = app_obj.check_downloader(app_obj.ytdl_path)
        if os.name != 'nt':
            ytdl_path = re.sub('^\~', os.path.expanduser('~'), ytdl_path)

        # Generate the system command...
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
                stdout = stdout.decode()
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

                    if 'description' in json_dict:
                        self.video_obj.set_video_descrip(
                            json_dict['description'],
                            app_obj.main_win_obj.descrip_line_max_len,
                        )

        # Messages indicating that a livestream is waiting to start are in
        #   STDERR (for some reason)
        while not self.stderr_queue.empty():

            stderr = self.stderr_queue.get_nowait().rstrip()
            if stderr:

                # (Convert bytes to string)
                stderr = stderr.decode()

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

        """Called by downloads.LivestreamManager.run().

        Destructor function for this object.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 4794 close')

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
            utils.debug_time('dld 4821 create_child_process')

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
            utils.debug_time('dld 4866 is_child_process_alive')

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
            utils.debug_time('dld 4895 parse_json')

        # (Try/except to check for invalid JSON)
        try:
            return json.loads(stdout)

        except:
            GObject.timeout_add(
                0,
                app_obj.system_error,
                305,
                'Invalid JSON data received from server',
            )

            return {}


    def stop(self):

        """Called by DownloadWorker.close().

        Terminates the child process.
        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 4920 stop')

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
        convert the queued items back to 'unicode', if necessary.

    """


    # Standard class methods


    def __init__(self, queue):

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 4969 __init__')

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
            utils.debug_time('dld 5006 run')

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
            utils.debug_time('dld 5048 attach_file_descriptor')

        self.file_descriptor = filedesc


    def join(self, timeout=None):

        """Called by downloads.VideoDownloader.close(), which is the destructor
        function for that object.

        Join the thread and update IVs.

        Args:

            timeout (-): No calling code sets a timeout

        """

        if DEBUG_FUNC_FLAG:
            utils.debug_time('dld 5067 join')

        self.running_flag = False
        super(PipeReader, self).join(timeout)
