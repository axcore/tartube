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


"""Download operation classes."""


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
import re
import requests
import subprocess
import sys
import threading
import time


# Import our modules
from . import formats
from . import mainapp
from . import media
from . import options
from . import utils


# !!! Debugging flag
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

    """Called by mainapp.TartubeApp.download_manager_start().

    Based on the DownloadManager class in youtube-dl-gui.

    Python class to manage a download operation.

    Creates one or more downloads.DownloadWorker objects, each of which handles
    a single download.

    This object runs on a loop, looking for available workers and, when one is
    found, assigning them something to download. The worker completes that
    download and then waits for another assignment.

    Args:

        app_obj: The mainapp.TartubeApp object

        force_sim_flag (True/False): True if playlists/channels should just be
            checked for new videos, without downloading anything. False if
            videos should be downloaded (or not) depending on each media data
            object's .dl_sim_flag IV

        download_list_obj(downloads.DownloadManager): An ordered list of
            media data objects to download, each one represented by a
            downloads.DownloadItem object

    """


    # Standard class methods


    def __init__(self, app_obj, force_sim_flag, download_list_obj):

        if DEBUG_FUNC_FLAG:
            print('dl 108 __init__')

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
        # Flag set to True if playlists/channels should just be checked for new
        #   videos, without downloading anything. False if videos should be
        #   downloaded (or not) depending on each media data object's
        #   .dl_sim_flag IV
        self.force_sim_flag = force_sim_flag

        # The time at which the download operation began (in seconds since
        #   epoch)
        self.start_time = time.time()
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


        # Code
        # ----

        # Create an object for converting download options stored in
        #   downloads.DownloadWorker.options_list into a list of youtube-dl
        #   command line options
        self.options_parser_obj = options.OptionsParser(self)

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
            print('dl 185 run')

        # Perform the download operation until there is nothing left to
        #   download, or until something has called
        #   self.stop_download_operation()
        while self.running_flag:
            download_item_obj = self.download_list_obj.fetch_next_item()

            # Exit this loop when there are no more downloads.DownloadItem
            #   objects whose .status is formats.MAIN_STAGE_QUEUED, and when
            #   all workers have finished their downloads
            # Otherwise, wait for an available downloads.DownloadWorker, and
            #   then assign the next downloads.DownloadItem to it
            if not download_item_obj:
                if self.check_workers_all_finished():
                    break

            else:
                worker_obj = self.get_available_worker()
                if worker_obj:

                    # If the worker has been marked as doomed (because the
                    #   number of simultaneous downloads allowed has decreased)
                    #   then we can destroy it now
                    if worker_obj.doomed_flag:
                        worker_obj.close()
                        self.remove_worker(worker_obj)

                    # Otherwise, initialise the worker's IVs for the next job
                    else:
                        worker_obj.prepare_download(download_item_obj)
                        # Change the download stage for that
                        #   downloads.DownloadItem
                        self.download_list_obj.change_item_stage(
                            download_item_obj.dbid,
                            formats.MAIN_STAGE_ACTIVE,
                        )
                        # Update the main window's progress bar
                        self.job_count += 1
                        # Throughout the downloads.py code, instead calling a
                        #   mainapp.py or mainwin.py function directly (which
                        #   is not thread-safe), set a Glib timeout to handle
                        #   it
                        GObject.timeout_add(
                            0,
                            self.app_obj.main_win_obj.update_progress_bar,
                            download_item_obj.media_data_obj.name,
                            self.job_count,
                            len(self.download_list_obj.download_item_list),
                        )

            # Pause a moment, before the next iteration of the loop (don't want
            #   to hog resources)
            time.sleep(self.sleep_time)

        # Download operation complete (or has been stopped)
        # Close all the workers
        for worker_obj in self.worker_list:
            worker_obj.close()

        # Join and collect
        for worker_obj in self.worker_list:
            worker_obj.join()

        # Set the stop time
        self.stop_time = time.time()

        # Tell the Progress Tab to display any remaining download statistics
        #   immediately
        GObject.timeout_add(
            0,
            self.app_obj.main_win_obj.progress_list_display_dl_stats,
        )

        # When youtube-dl reports it is finished, there is a short delay before
        #   the final downloaded video(s) actually exist in the filesystem
        # Therefore, mainwin.MainWin.progress_list_display_dl_stats() may not
        #   have marked the final video(s) as downloaded yet
        # Let the timer run for a few more seconds to allow those videos to be
        #   marked as downloaded (we can stop before that, if all the videos
        #   have been already marked)
        if not self.force_sim_flag:
            GObject.timeout_add(
                0,
                self.app_obj.download_manager_halt_timer,
            )
        else:
            # If we're only simulating downloads, we don't need to wait at all
            GObject.timeout_add(
                0,
                self.app_obj.download_manager_finished,
            )


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
            print('dl 284 change_worker_count')

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


    def check_workers_all_finished(self):

        """Called by self.run().

        Based on DownloadManager._jobs_done().

        Returns:

            True if all downloads.DownloadWorker objects have finished their
                jobs, otherwise returns False

        """

        if DEBUG_FUNC_FLAG:
            print('dl 342 check_workers_all_finished')

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
            print('dl 365 get_available_worker')

        for worker_obj in self.worker_list:
            if worker_obj.available_flag:
                return worker_obj

        return None


    def remove_worker(self, worker_obj):

        """Called by self.run().

        When a worker marked as doomed has completed its download job, this
        function is called to remove it from self.worker_list.

        Args:

            worker_obj (downloads.DownloadWorker): The worker object to remove

        """

        if DEBUG_FUNC_FLAG:
            print('dl 388 remove_worker')

        new_list = []

        for other_obj in self.worker_list:
            if other_obj != worker_obj:
                new_list.append(other_obj)

        self.worker_list = new_list


    def stop_download_operation(self):

        """Called by mainapp.TartubeApp.do_shutdown(), .stop() and a callback
        in .on_button_stop_operation().

        Based on DownloadManager.stop_downloads().

        Stops the download operation. On the next iteration of self.run()'s
        loop, the downloads.DownloadWorker objects are cleaned up.
        """

        if DEBUG_FUNC_FLAG:
            print('dl 411 stop_download_operation')

        self.running_flag = False


class DownloadWorker(threading.Thread):

    """Called by downloads.DownloadManager.__init__().

    Based on the Worker class in youtube-dl-gui.

    Python class for managing simultaneous downloads. The parent
    downloads.DownloadManager object can create one or more workers, each of
    which handles a single download.

    The download manager runs on a loop, looking for available workers and,
    when one is found, assigns them something to download. The worker
    completes that download and then waits for another assignment.

    Args:

        download_manager_obj (downloads.DownloadManager): The parent download
            manager object.

    """


    # Standard class methods


    def __init__(self, download_manager_obj):

        if DEBUG_FUNC_FLAG:
            print('dl 444 __init__')

        super(DownloadWorker, self).__init__()

        # IV list - class objects
        # -----------------------
        # The parent downloads.DownloadManager object
        self.download_manager_obj = download_manager_obj
        # The downloads.DownloadItem object for the current job
        self.download_item_obj = None
        # The downloads.VideoDownloader object for the current job
        self.video_downloader_obj = None
        # The options.OptionsManager object for the current job
        self.options_manager_obj = None


        # IV list - other
        # ---------------
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
            print('dl 501 run')

        # Import the main application (for convenience)
        app_obj = self.download_manager_obj.app_obj

        # Handle a job, or wait for the downloads.DownloadManager to assign
        #   this worker a job
        while self.running_flag:

            # If this worker is currently assigned a job...
            if not self.available_flag:

                # youtube-dl-gui used a single instance of a
                #   YoutubeDLDownloader object for each instance of a Worker
                #   object.
                # This causes problems, so Tartube will use a new
                #   downloads.VideoDownloader object each time
                # Set up the new downloads.VideoDownloader object
                self.video_downloader_obj = VideoDownloader(
                    self.download_manager_obj,
                    self,
                    self.download_item_obj,
                )

                # Then execute the assigned job
                return_code = self.video_downloader_obj.do_download()

                # Import the media data object (for convenience)
                media_data_obj = self.download_item_obj.media_data_obj

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
                # Do that now (but don't both if mainwin.ComplexCatalogueItem
                #   aren't being used in the Video Catalogue)
                if return_code == VideoDownloader.ERROR \
                and isinstance(media_data_obj, media.Video) \
                and (
                    app_obj.catalogue_mode == 'complex_hide_parent' \
                    or app_obj.catalogue_mode == 'complex_show_parent'
                ):
                    GObject.timeout_add(
                        0,
                        app_obj.main_win_obj.video_catalogue_update_row,
                        media_data_obj,
                    )

                # Call the destructor function of VideoDownloader object
                self.video_downloader_obj.close()

                # This worker is now available for a new job
                self.available_flag = True

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
            print('dl 573 close')

        self.running_flag = False
        if self.video_downloader_obj:
            self.video_downloader_obj.stop()


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
            print('dl 597 prepare_download')

        self.download_item_obj = download_item_obj
        self.options_manager_obj = download_item_obj.options_manager_obj
        self.options_list = self.download_manager_obj.options_parser_obj.parse(
            download_item_obj,
            self.options_manager_obj.options_dict,
        )

        self.available_flag = False


    def set_doomed_flag(self, flag):

        """Called by downloads.DownloadManager.change_worker_count()."""

        if DEBUG_FUNC_FLAG:
            print('dl 614 set_doomed_flag')

        self.doomed_flag = flag


    # Callback class methods


    def data_callback(self, dl_stat_dict):

        """Called by downloads.VideoDownloader.do_download() and
        .last_data_callback().

        Based on Worker._data_hook() and ._talk_to_gui().

        'dl_stat_dict' holds a dictionary of statistics in a standard format
        specified by downloads.VideoDownloader.extract_stdout_data().

        This callback receives that dictionary and passes it on to the main
        window, so the statistics can be displayed there.

        Args:

            dl_stat_dict (dictionary): The dictionary of statistics described
                above

        """

        if DEBUG_FUNC_FLAG:
            print('dl 643 data_callback')

        app_obj = self.download_manager_obj.app_obj
        GObject.timeout_add(
            0,
            app_obj.main_win_obj.progress_list_receive_dl_stats,
            self.download_item_obj,
            dl_stat_dict,
        )


class DownloadList(object):

    """Called by mainapp.TartubeApp.download_manager_start().

    Based on the DownloadList class in youtube-dl-gui.

    Python class to keep track of all the media data objects to be downloaded
    (for real or in simulation) during a downloaded operation.

    This object contains an ordered list of downloads.DownloadItem objects.
    Each of those objects represents a media data object to be downloaded
    (media.Video, media.Channel, media.Playlist or media.Folder).

    Videos are downloaded in the order specified by the list.

    Args:

        app_obj (mainapp.TartubeApp): The main application

        media_data_obj (media.Video, media.Channel, media.Playlist,
            media.Folder or None): The media data object to download. If
            specified, that object and any media data objects it contains are
            downloaded. If none, all media data objects in Tartube's media data
            registry are downloaded

    """


    # Standard class methods


    def __init__(self, app_obj, media_data_obj):

        if DEBUG_FUNC_FLAG:
            print('dl 686 __init__')

        # IV list - class objects
        # -----------------------
        self.app_obj = app_obj


        # IV list - other
        # ---------------
        # Number of download.DownloadItem objects created (used to give each a
        #   unique ID)
        self.download_item_count = 0

        # An ordered list of downloads.DownloadList items, one for each
        #   media.Video, media.Channel, media.Playlist or media.Folder object
        # This list stores each item's .dbid
        self.download_item_list = []
        # Corresponding dictionary of downloads.DownloadList items for quick
        #   lookup. Dictionary in the form
        #       key = download.DownloadItem.dbid
        #       value = the download.DownloadItem object itself
        self.download_item_dict = {}


        # Code
        # ----

        # For each media data object to be downloaded, created a
        #   downloads.DownloadItem object, and update the IVs above
        if not media_data_obj:

            # Use all media data objects
            for dbid in self.app_obj.media_top_level_list:
                obj = self.app_obj.media_reg_dict[dbid]
                self.create_item(obj)

        elif isinstance(media_data_obj, media.Folder) \
        and media_data_obj.priv_flag:

            # Videos in a private folder's .child_list can't be downloaded
            #   (since they are also a child of a channel, playlist or a public
            #   folder)
            GObject.timeout_add(
                0,
                app_obj.system_error,
                301,
                'Cannot download videos in a private folder',
            )

        else:

            # Use the specified media data object. The True value tells
            #   self.create_item to download media_data_obj, even if it is a
            #   video in a channel or a playlist (which otherwise would be
            #   handled by downloading the channel/playlist)
            self.create_item(media_data_obj, True)


    # Public class methods


    @synchronise(_SYNC_LOCK)
    def change_item_stage(self, dbid, new_stage):

        """Called by downloads.DownloadManager.run().

        Based on DownloadList.change_stage().

        Changes the download stage for the specified downloads.DownloadItem
        object.

        Args:

            dbid (int): The specified item's .dbid

            new_stage: The new download stage, one of the values imported from
                formats.py (e.g. formats.MAIN_STAGE_QUEUED)

        """

        if DEBUG_FUNC_FLAG:
            print('dl 765 change_item_stage')

        self.download_item_dict[dbid].stage = new_stage


    def create_item(self, media_data_obj, init_flag=False):

        """Called by self.__init__(), or by this function recursively.

        Creates a downloads.DownloadItem object for media data objects in the
        media data registry.

        Doesn't create a download item object for:
            - media.Video objects whose parent is not a media.Folder (i.e.
                whose parent is a media.Channel or a media.Playlist)
            - media.Video objects in any restricted folder
            - media.Video objects in the fixed 'Unsorted Videos' folder which
                are already marked as downloaded
            - media.Folder objects

        Adds the resulting downloads.DownloadItem object to this object's IVs.

        Args:

            media_data_obj (media.Video, media.Channel, media.Playlist,
                media.Folder): A media data object

            init_flag (True, False): True when called by self.__init__, and
                False when called by this function recursively. If True and
                media_data_obj is a media.Video object, we download it even if
                its parent is a channel or a playlist

        """

        if DEBUG_FUNC_FLAG:
            print('dl 800 create_item')

        # Get the options.OptionsManager object that applies to this media
        #   data object
        # (The manager might be specified by obj itself, or it might be
        #   specified by obj's parent, or we might use the default
        #   options.OptionsManager)
        options_manager_obj = self.get_options_manager(media_data_obj)

        # Ignore private folders, and don't download any of their children
        #   (because they are all children of some other non-private folder)
        if isinstance(media_data_obj, media.Folder) \
        and media_data_obj.priv_flag:
            return

        # Don't download videos that we already have
        # Don't download videos if they're in a channel or playlist (since
        #   downloading the channel/playlist downloads the videos it contains)
        # (Exception: download a single video if that's what the calling code
        #   has specifically requested)
        if isinstance(media_data_obj, media.Video):

            if media_data_obj.dl_flag \
            or (
                not isinstance(media_data_obj.parent_obj, media.Folder) \
                and not init_flag
            ):
                return

        # Don't create a download.DownloadItem object for a media.Folder,
        #   obviously
        if not isinstance(media_data_obj, media.Folder):

            # Create a new download.DownloadItem object...
            self.download_item_count += 1
            download_item_obj = DownloadItem(
                self.download_item_count,
                media_data_obj,
                options_manager_obj,
            )

            # ...and add it to our list
            self.download_item_list.append(download_item_obj.dbid)
            self.download_item_dict[download_item_obj.dbid] \
            = download_item_obj

        # If the media data object has children, call this function recursively
        #   for each of them
        if not isinstance(media_data_obj, media.Video):
            for child_obj in media_data_obj.child_list:
                self.create_item(child_obj)


    @synchronise(_SYNC_LOCK)
    def fetch_next_item(self):

        """Called by downloads.DownloadManager.run().

        Based on DownloadList.fetch_next().

        Returns:

            The next downloads.DownloadItem object, or None if there are none
                left.

        """

        if DEBUG_FUNC_FLAG:
            print('dl 868 fetch_next_item')

        for dbid in self.download_item_list:
            this_item = self.download_item_dict[dbid]

            # Don't return an item that's marked as formats.MAIN_STAGE_ACTIVE
            if this_item.stage == formats.MAIN_STAGE_QUEUED:
                return this_item

        return None


    def get_options_manager(self, media_data_obj):

        """Called by self.create_item() or by this function recursively.

        Fetches the options.OptionsManager which applies to the specified media
        data object.

        The media data object might specify its own options.OptionsManager, or
        we might have to use the parent's, or the parent's parent's (and so
        on). As a last resort, use General Options Manager.

        Args:

            obj(media.Video, media.Channel, media.Playlist, media.Folder):
                A media data object

        Returns:

            The options.OptionsManager object that applies to the specified
                media data object

        """

        if DEBUG_FUNC_FLAG:
            print('dl 904 get_options_manager')

        if media_data_obj.options_obj:
            return media_data_obj.options_obj
        elif media_data_obj.parent_obj:
            return self.get_options_manager(media_data_obj.parent_obj)
        else:
            return self.app_obj.general_options_obj


class DownloadItem(object):

    """Called by downloads.DownloadList.create_item().

    Based on the DownloadItem class in youtube-dl-gui.

    Python class used to track the download status of a media data object
    (media.Video, media.Channel, media.Playlist or media.Folder), one of many
    in a downloads.DownloadList object.

    Args:

        dbid (int) - The number of downloads.DownloadItem objects created, used
            to give each one a unique ID

        media_data_obj (media.Video, media.Channel, media.Playlist,
            media.Folder): A media data object to be downloaded

        options_manager_obj (options.OptionsManager): The object which
            specifies download options for the media data object

    """


    # Standard class methods


    def __init__(self, dbid, media_data_obj, options_manager_obj):

        if DEBUG_FUNC_FLAG:
            print('dl 944 __init__')

        # IV list - class objects
        # -----------------------
        # The media data object to be downloaded
        self.media_data_obj = media_data_obj
        # The object which specifies download options for the media data object
        self.options_manager_obj = options_manager_obj


        # IV list - other
        # ---------------
        # A unique ID for this object
        self.dbid = dbid
        # The current download stage
        self.stage = formats.MAIN_STAGE_QUEUED


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

        download_manager_obj (downloads.DownloadManager) - The download
            manager object handling the entire download operation.

        download_worker_obj (downloads.DownloadWorker) - The parent download
            worker object. The download manager uses multiple workers to
            implement simultaneous downloads. The download manager checks for
            free workers and, when it finds one, assigns it a
            download.DownloadItem object. When the worker is assigned a
            download item, it creates a new instance of this object to
            interface with youtube-dl, and waits for this object to return a
            return code.

        download_item_obj (downloads.DownloadItem) - The download item object
            describing the URL from which youtube-dl should download video(s).

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


    # Standard class methods


    def __init__(self, download_manager_obj, download_worker_obj, \
    download_item_obj):

        if DEBUG_FUNC_FLAG:
            print('dl 1036 __init__')

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

        # Flag set to True if we are simulating downloads for this media data
        #   object, or False if we actually downloading videos (set below)
        self.dl_sim_flag = None

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

        # Code
        # ----
        # Initialise IVs depending on whether this is a real or simulated
        #   download
        media_data_obj = self.download_item_obj.media_data_obj

        # If the media data object is a video, channel or playlist, it can be
        #   marked as a simulated download only
        # If it's a video inside a folder and the folder itself is marked as
        #   simulated downloads only, apply that to all videos in the folder
        if self.download_manager_obj.force_sim_flag \
        or media_data_obj.dl_sim_flag \
        or (
            isinstance(media_data_obj, media.Video) \
            and isinstance(media_data_obj.parent_obj, media.Folder) \
            and media_data_obj.parent_obj.dl_sim_flag
        ):
            self.dl_sim_flag = True
            self.video_num = 0
            self.video_total = 0
        else:
            self.dl_sim_flag = False
            self.video_num = 1
            self.video_total = 1


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
            print('dl 1162 do_download')

        # Import the main application (for convenience)
        app_obj = self.download_manager_obj.app_obj

        # Set the default return code. Everything is OK unless we encounter
        #   any problems
        self.return_code = self.OK

        # Reset the errors/warnings stored in the media data object, the last
        #   time it was checked/downloaded
        self.download_item_obj.media_data_obj.reset_error_warning()

        # Prepare a system command...
        cmd_list = self.get_system_cmd()
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

                    if os.name == 'nt':
                        stdout = stdout.decode('cp1252')
                    else:
                        stdout = stdout.decode('utf-8')

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

                    if (app_obj.ytdl_write_stdout_flag):

                        name = utils.upper_case_first(__main__.__packagename__)
                        # JSON output starts with {, in case we need to ignore
                        if not app_obj.ytdl_write_ignore_json_flag:
                            print(stdout)

                        else:
                            if stdout[:1] == '{':
                                print('<' + name + ' received JSON data>')
                            else:
                                print(stdout)

            # Apply the JSON timeout, if required
            if app_obj.apply_json_timeout_flag \
            and self.last_sim_video_check_time is not None \
            and self.last_sim_video_check_time < int(time.time()):
                # Halt the child process, which stops checking this channel/
                #   playlist
                self.stop()

                GObject.timeout_add(
                    0,
                    app_obj.system_error,
                    302,
                    'Enforced timeout on youtube-dl because it took too long' \
                    + ' to fetch a video\'s JSON data',
                )

        # The child process has finished
        while not self.stderr_queue.empty():

            # Read from the child process STDERR queue (we don't need to read
            #   it in real time), and convert into unicode for python's
            #   convenience
            stderr = self.stderr_queue.get_nowait().rstrip()
            if os.name == 'nt':
                stderr = stderr.decode('cp1252')
            else:
                stderr = stderr.decode('utf-8')

            if not self.is_ignorable(stderr):

                if self.is_warning(stderr):
                    self.set_return_code(self.WARNING)
                    self.download_item_obj.media_data_obj.set_warning(stderr)

                elif not self.is_debug(stderr):
                    self.set_return_code(self.ERROR)
                    self.download_item_obj.media_data_obj.set_error(stderr)

            if (app_obj.ytdl_write_stderr_flag):
                print(stderr)

        # We also set the return code to self.ERROR if the download didn't
        #   start or if the child process return code is greater than 0
        # Original notes from youtube-dl-gui:
        #   NOTE: In Linux if the called script is just empty Python exits
        #       normally (ret=0), so we cant detect this or similar cases
        #       using the code below
        #   NOTE: In Unix a negative return code (-N) indicates that the child
        #       was terminated by signal N (e.g. -9 = SIGKILL)
        if self.child_process is None:
            self.set_return_code(self.ERROR)
            self.download_item_obj.media_data_obj.set_error(
                'Download did not start',
            )

        elif self.child_process.returncode > 0:
            self.set_return_code(self.ERROR)
            self.download_item_obj.media_data_obj.set_error(
                'Child process exited with non-zero code: {}'.format(
                    self.child_process.returncode,
                )
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
        videos), then the URL is a channel or playlist, not a video.

        Cannot store data for a channel or playlist in a media.Video object,
        so stop the child process immediately and display a system error.
        """

        if isinstance(self.download_item_obj.media_data_obj, media.Video):

            self.stop()
            self.download_item_obj.media_data_obj.set_error(
                'The video \'' + self.download_item_obj.media_data_obj.name \
                + '\' has a source URL that points to a channel or a' \
                + ' playlist, not a video',
            )


    def close(self):

        """Called by downloads.DownloadWorker.run() and .close().

        Destructor function for this object.
        """

        if DEBUG_FUNC_FLAG:
            print('dl 1279 close')

        # Tell the PipeReader objects to shut down, thus joining their threads
        self.stdout_reader.join()
        self.stderr_reader.join()


    def confirm_new_video(self, dir_path, filename, extension):

        """Called by self.extract_stdout_data().

        A successful download is announced in one of several ways.

        When an announcement is detected, this function is called. Use the
        first announcement to update self.video_check_dict, and ignore
        subsequent announcements.

        Args:

            dir_path (string): The full path to the directory in which the
                video is saved, e.g. '/home/yourname/tartube/downloads/Videos'

            filename (string): The video's filename, e.g. 'My Video'

            extension (string): The video's extension, e.g. '.mp4'

        """

        if DEBUG_FUNC_FLAG:
            print('dl 1308 confirm_new_video')

        if not self.video_num in self.video_check_dict:
            self.video_check_dict[self.video_num] = filename

            # Create a new media.Video object for the video
            app_obj = self.download_manager_obj.app_obj
            video_obj = app_obj.create_video_from_download(
                self.download_item_obj,
                dir_path,
                filename,
                extension,
                True,               # Don't sort parent containers yet
            )

            # If downloading from a playlist, remember the video's index in
            #   that playlist
            if isinstance(video_obj.parent_obj, media.Playlist):
                video_obj.set_index(self.video_num)

            # Fetch the options.OptionsManager object used for this download
            options_manager_obj = self.download_worker_obj.options_manager_obj

            # Update the main window
            GObject.timeout_add(
                0,
                app_obj.announce_video_download,
                self.download_item_obj,
                video_obj,
                options_manager_obj.options_dict['keep_description'],
                options_manager_obj.options_dict['keep_info'],
                options_manager_obj.options_dict['keep_thumbnail'],
            )


    def confirm_old_video(self, dir_path, filename, extension):

        """Called by self.extract_stdout_data().

        When youtube-dl reports a video has already been downloaded, make sure
        the media.Video object is marked as downloaded, and upate the video
        catalogue in the main window if necessary.

        Args:

            dir_path (string): The full path to the directory in which the
                video is saved, e.g. '/home/yourname/tartube/downloads/Videos'

            filename (string): The video's filename, e.g. 'My Video'

            extension (string): The video's extension, e.g. '.mp4'

        """

        if DEBUG_FUNC_FLAG:
            print('dl 1360 confirm_old_video')

        # Create shortcut variables (for convenience)
        app_obj = self.download_manager_obj.app_obj
        media_data_obj = self.download_item_obj.media_data_obj

        if isinstance(media_data_obj, media.Video):

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

                # Fetch the options.OptionsManager object used for this
                #   download
                options_manager_obj \
                = self.download_worker_obj.options_manager_obj

                # Update the main window
                GObject.timeout_add(
                    0,
                    app_obj.announce_video_download,
                    self.download_item_obj,
                    video_obj,
                    options_manager_obj.options_dict['keep_description'],
                    options_manager_obj.options_dict['keep_info'],
                    options_manager_obj.options_dict['keep_thumbnail'],
                )


    def confirm_sim_video(self, json_dict):

        """Called by self.extract_stdout_data().

        After a successful simulated download, youtube-dl presents us with JSON
        data for the video. Use that data to update everything.

        Args:

            json_dict (dict): JSON data from STDOUT, converted into a python
                dictionary

        """

        if DEBUG_FUNC_FLAG:
            print('dl 1426 confirm_sim_video')

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
        if '_filename' in json_dict:
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

        # Does an existing media.Video object match this video?
        media_data_obj = self.download_item_obj.media_data_obj
        video_obj = None
        if isinstance(media_data_obj, media.Video):
            video_obj = media_data_obj
        else:
            # media_data_obj is a media.Channel or media.Playlist object. Check
            #   its child objects, looking for a matching video
            # (video_obj is set to None, if no match is found)
            video_obj = media_data_obj.find_matching_video(app_obj, filename)

        new_flag = False
        if not video_obj:

            # No matching media.Video object found, so create a new one
            new_flag = True

            video_obj = app_obj.create_video_from_download(
                self.download_item_obj,
                path,
                filename,
                extension,
                # Don't sort parent container objects yet; wait for
                #   mainwin.MainWin.results_list_update_row() to do it
                True,
            )

            # Update its IVs with the JSON information we extracted
            if name is not None:
                video_obj.set_name(name)

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

            # Only save the playlist index when this video is actually stored
            #   inside a media.Playlist object
            if isinstance(video_obj.parent_obj, media.Playlist) \
            and playlist_index is not None:
                video_obj.set_index(playlist_index)

            # Now we can sort the parent containers
            video_obj.parent_obj.sort_children()
            app_obj.fixed_all_folder.sort_children()
            if video_obj.new_flag:
                app_obj.fixed_new_folder.sort_children()
            if video_obj.fav_flag:
                app_obj.fixed_fav_folder.sort_children()

        else:

            if video_obj.file_dir \
            and video_obj.name != app_obj.default_video_name:

                # This video applies towards the limit (if any) specified by
                #   mainapp.TartubeApp.operation_check_limit
                self.video_limit_count += 1

                if not isinstance(
                    self.download_item_obj.media_data_obj,
                    media.Video,
                ) \
                and app_obj.operation_limit_flag \
                and app_obj.operation_check_limit \
                and self.video_limit_count >= app_obj.operation_check_limit:
                    # Limit reached. When we reach the end of this function,
                    #   stop checking videos in this channel playlist
                    stop_flag = True

            # If the 'Add videos' button was used, the path/filename/extension
            #   won't be set yet
            if not video_obj.file_dir and full_path:
                video_obj.set_file(path, filename, extension)

            # Update any video object IVs that are not set
            if video_obj.name == app_obj.default_video_name \
            and name is not None:
                video_obj.set_name(name)

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

            # Only save the playlist index when this video is actually stored
            #   inside a media.Playlist object
            if not video_obj.index \
            and isinstance(video_obj.parent_obj, media.Playlist) \
            and playlist_index is not None:
                video_obj.set_index(playlist_index)

        # Deal with the video description, JSON data and thumbnail, according
        #   to the settings in options.OptionsManager
        options_dict =self.download_worker_obj.options_manager_obj.options_dict

        if descrip and options_dict['write_description']:
            descrip_path = os.path.abspath(
                os.path.join(path, filename + '.description'),
            )
            if not options_dict['sim_keep_description']:
                descrip_path = utils.convert_path_to_temp(
                    app_obj,
                    descrip_path,
                )

            # (Don't replace a file that already exists)
            if not os.path.isfile(descrip_path):
                fh = open(descrip_path, 'wb')
                fh.write(descrip.encode('utf-8'))
                fh.close()

        if options_dict['write_info']:
            json_path = os.path.abspath(
                os.path.join(path, filename + '.info.json'),
            )
            if not options_dict['sim_keep_info']:
                json_path = utils.convert_path_to_temp(app_obj, json_path)

            if not os.path.isfile(json_path):
                with open(json_path, 'w') as outfile:
                    json.dump(json_dict, outfile, indent=4)

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
            thumb_path = os.path.abspath(
                os.path.join(
                    video_obj.file_dir,
                    video_obj.file_name + remote_ext,
                ),
            )

            if not options_dict['sim_keep_thumbnail']:
                thumb_path = utils.convert_path_to_temp(app_obj, thumb_path)

            if not os.path.isfile(thumb_path):
                request_obj = requests.get(thumbnail)
                with open(thumb_path, 'wb') as outfile:
                    outfile.write(request_obj.content)

        # If a new media.Video object was created, add a line to the Results
        #   List, as well as updating the Video Catalogue
        if new_flag:

            GObject.timeout_add(
                0,
                app_obj.announce_video_download,
                self.download_item_obj,
                video_obj,
            )

        else:

            # Otherwise, just update the Video Catalogue
            GObject.timeout_add(
                0,
                app_obj.main_win_obj.video_catalogue_update_row,
                video_obj,
            )

        # Stop checking videos in this channel/playlist, if a limit has been
        #   reached
        if stop_flag:
            self.stop()


    def create_child_process(self, cmd_list):

        """Called by self.do_download() immediately after the call to
        self.get_system_cmd().

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
            print('dl 1637 create_child_process')

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

#        # Encode the system command for the child process, converting unicode
#        #   to str so the MS Windows shell can accept it (see
#        #   http://stackoverflow.com/a/9951851/35070 )
#        if sys.version_info < (3, 0):
#            cmd_list = utils.convert_item(cmd_list, to_unicode=False)

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

        """Called by self.extract_stdout_data().

        Based on the extract_data() function in youtube-dl-gui's
        downloaders.py.

        Extracts various components of a filename.

        Args:
            input_data (string): Full path to a file which has been downloaded
                and saved to the filesystem

        Returns:

            Returns the path, filename and extension components of the full
                file path.

        """

        if DEBUG_FUNC_FLAG:
            print('dl 1693 extract_filename')

        path, fullname = os.path.split(input_data.strip("\""))
        filename, extension = os.path.splitext(fullname)

        return path, filename, extension


    def extract_stdout_data(self, stdout):

        """Called by self.do_download().

        Based on the extract_data() function in youtube-dl-gui's
        downloaders.py.

        Extracts youtube-dl statistics from the child process.

        Args:
            stdout (string): String that contains a line from the child process
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
            print('dl 1741 extract_stdout_data')

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

            # Get playlist information (when downloading a channel or a
            #   playlist, this line is received once per video)
            if stdout_list[1] == 'Downloading' and stdout_list[2] == 'video':
                dl_stat_dict['playlist_index'] = stdout_list[3]
                self.video_num = stdout_list[3]
                dl_stat_dict['playlist_size'] = stdout_list[5]
                self.video_total = stdout_list[5]

                # If downloading an individual video, rather than a channel or
                #   a playlist, stop the download immediately
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

            # Get filesize abort status
            if stdout_list[-1] == 'Aborting.':
                dl_stat_dict['status'] = formats.ERROR_STAGE_ABORT

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
                        app_obj.system_error,
                        304,
                        'Invalid JSON data received from server',
                    )

                # (JSON is valid)
                self.confirm_sim_video(json_dict)

                self.video_num += 1
                dl_stat_dict['playlist_index'] = self.video_num
                self.video_total += 1
                dl_stat_dict['playlist_size'] = self.video_total

                dl_stat_dict['status'] = formats.ACTIVE_STAGE_CHECKING

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
            print('dl 1969 extract_stdout_status')

        if 'status' in dl_stat_dict:
            if dl_stat_dict['status'] == formats.COMPLETED_STAGE_ALREADY:
                self.set_return_code(self.ALREADY)
                dl_stat_dict['status'] = None

            if dl_stat_dict['status'] == formats.ERROR_STAGE_ABORT:
                self.set_return_code(self.FILESIZE_ABORT)
                dl_stat_dict['status'] = None


    def get_system_cmd(self):

        """Called by self.do_download().

        Based on YoutubeDLDownloader._get_cmd().

        Prepare the system command that creates the child process, executing
        youtube-dl.

        Returns:

            Python list that contains the system command to execute.

        """

        if DEBUG_FUNC_FLAG:
            print('dl 1997 get_system_cmd')

        options_list = self.download_worker_obj.options_list

        # Simulate the download, rather than actually downloading videos, if
        #   required
        if self.dl_sim_flag:
            options_list.append('--dump-json')

        # Show verbose output (youtube-dl debugging mode), if required
        if self.download_manager_obj.app_obj.ytdl_write_verbose_flag:
            options_list.append('--verbose')

        # Set the list
        cmd_list = [self.download_manager_obj.app_obj.ytdl_path] \
        + options_list + [self.download_item_obj.media_data_obj.source]

        return cmd_list


    def is_child_process_alive(self):

        """Called by self.do_download() and self.stop().

        Based on YoutubeDLDownloader._proc_is_alive().

        Called continuously during the self.do_download() loop to check whether
        the child process has finished or not.

        Returns:

            True if the child process is alive, otherwise returns False.

        """

        if DEBUG_FUNC_FLAG:
            print('dl 2033 is_child_process_alive')

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

            stderr (string): A message from the child process STDERR.

        Returns:

            True if the STDERR message is a youtube-dl debug message, False if
                it's an error

        """

        if DEBUG_FUNC_FLAG:
            print('dl 2063 is_debug')

        return stderr.split(' ')[0] == '[debug]'


    def is_ignorable(self, stderr):

        """Called by self.do_download().

        Before testing a STDERR message, see if it's one of the frequent
        messages which the user has opted to ignore (if any).

        Args:

            stderr (string): A message from the child process STDERR.

        Returns:

            True if the STDERR message is ignorable, False if it should be
                tested further.

        """

        if DEBUG_FUNC_FLAG:
            print('dl 2087 is_ignorable')

        app_obj = self.download_manager_obj.app_obj

        if app_obj.ignore_merge_warning_flag \
        and re.search(r'Requested formats are incompatible for merge', stderr):
            return True

        elif app_obj.ignore_yt_copyright_flag \
        and re.search(
            r'This video contains contents from.*copyright grounds',
            stderr,
        ):
            return True

        elif app_obj.ignore_child_process_exit_flag \
        and re.search(
            r'Child process exited with non\-zero code',
            stderr,
        ):
            return True

        else:
            # Not ignorable
            return False


    def is_warning(self, stderr):

        """Called by self.do_download().

        Based on YoutubeDLDownloader._is_warning().

        After the child process has terminated with an error of some kind,
        checks the STERR message to see if it's an error or just a warning.

        Args:

            stderr (string): A message from the child process STDERR.

        Returns:

            True if the STDERR message is a warning, False if it's an error

        """

        if DEBUG_FUNC_FLAG:
            print('dl 2116 is_warning')

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
            print('dl 2138 last_data_callback')

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

        self.download_worker_obj.data_callback(dl_stat_dict)


    def set_return_code(self, code):

        """Called by self.do_download() and self.stop().

        Based on YoutubeDLDownloader._set_returncode().

        After the child process has terminated with an error of some kind,
        sets a new value for self.return_code, but only if the new return code
        is higher in the hierarchy of return codes than the current value.

        Args:

            code (int): A return code in the range 0-5

        """

        if DEBUG_FUNC_FLAG:
            print('dl 2190 set_return_code')

        if code >= self.return_code:
            self.return_code = code


    def set_temp_destination(self, path, filename, extension):

        """Called by self.extract_stdout_data()."""

        self.temp_path = path
        self.temp_filename = filename
        self.temp_extension = extension


    def reset_temp_destination(self):

        """Called by self.extract_stdout_data()."""

        self.temp_path = None
        self.temp_filename = None
        self.temp_extension = None


    def stop(self):

        """Called by downloads.DownloadWorker.close().

        Terminates the child process and sets this object's return code to
        self.STOPPED.
        """

        if DEBUG_FUNC_FLAG:
            print('dl 2223 stop')

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

        All the operations are based on 'str' types. The calling function must
        convert the queued items back to 'unicode', if necessary.

    """


    # Standard class methods


    def __init__(self, queue):

        if DEBUG_FUNC_FLAG:
            print('dl 2274 __init__')

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
            print('dl 2311 run')

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

        """Called by downloads.VideoDownloader.do_download().

        Sets the file descriptor for the child process STDOUT or STDERR.

        Args:

            filedesc (filehandle): The open filehandle for STDOUT or STDERR

        """

        if DEBUG_FUNC_FLAG:
            print('dl 2352 attach_file_descriptor')

        self.file_descriptor = filedesc


    def join(self, timeout=None):

        """Called by downloads.VideoDownloader.close(), which is the destructor
        function for that object.

        Join the thread and update IVs

        Args:

            timeout (-): No calling code sets a timeout

        """

        if DEBUG_FUNC_FLAG:
            print('dl 2371 join')

        self.running_flag = False
        super(PipeReader, self).join(timeout)
