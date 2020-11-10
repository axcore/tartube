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


"""Utility functions used by code copied from youtube-dl-gui."""


# Import Gtk modules
from gi.repository import Gtk, Gdk


# Import other modules
import datetime
import glob
import locale
import math
import os
import re
import requests
import shutil
import subprocess
import sys
import textwrap
import time


# Import our modules
import formats
import mainapp
import media
# Use same gettext translations
from mainapp import _


# Functions


def add_links_to_entry_from_clipboard(app_obj, entry, duplicate_text=None,
drag_drop_text=None, no_modify_flag=None):

    """Called by various functions in mainWin.AddChannelDialogue and
    mainwin.AddPlaylistDialogue.

    Function to add valid URLs from the clipboard to a Gtk.Entry, ignoring
    anything that is not a valid URL.

    A duplicate URL can be specified, when the dialogue window's clipboard
    monitoring is turned on; it prevents this function adding the same URL
    that was added the previous time.

    Args:

        app_obj (mainapp.TartubeApp): The main application

        entry (Gtk.Entry): The entry to which valis URLs should be added.
            Only the first valid URL is added, replacing any previous contents
            (unless the URL matches the specified duplicate

        duplicate_text (str): If specified, ignore the clipboard contents, if
            it matches this URL

        drag_drop_text (str): If specified, use this text and ignore the
            clipboard

        no_modify_flag (bool): If True, the entry is not updated, instead,
            the URL that would have been added to it is merely returned

    Returns:

        The URL added to the entry (or that would have been added to the entry)
        or None if no valid and non-duplicate URL was found in the clipboard

    """

    if drag_drop_text is None:

        # Get text from the system clipboard
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        cliptext = clipboard.wait_for_text()

    else:

        # Ignore the clipboard, and use the specified text
        cliptext = drag_drop_text

    # Eliminate empty lines and any lines that are not valid URLs (we assume
    #   that it's one URL per line)
    # Use the first valid line that doesn't match the duplicate (if specified)
    if cliptext is not None and cliptext != Gdk.SELECTION_CLIPBOARD:

        for line in cliptext.split('\n'):
            if check_url(line):

                line = strip_whitespace(line)
                if re.search('\S', line) \
                and (duplicate_text is None or line != duplicate_text):

                    if not no_modify_flag:
                        entry.set_text(line)

                    return line

    # No valid and non-duplicate URL found
    return None


def add_links_to_textview(app_obj, link_list, textbuffer, mark_start=None,
mark_end=None, drag_drop_text=None):

    """Called by mainwin.AddVideoDialogue.__init__(),
    .on_window_drag_data_received() and .clipboard_timer_callback().

    Also called by utils.add_links_to_textview_from_clipboard().

    Function to add valid URLs from the clipboard to a Gtk.TextView, ignoring
    anything that is not a valid URL, and ignoring duplicate URLs.

    If some text is supplied as an argument, uses that text rather than the
    clipboard text

    Args:

        app_obj (mainapp.TartubeApp): The main application

        link_list (list): List of URLs to add to the textview

        textbuffer (Gtk.TextBuffer): The textbuffer to which valis URLs should
            be added (unless they are duplicates)

        mark_start, mark_end (Gtk.TextMark): The marks at the start/end of the
            buffer (using marks rather than iters prevents Gtk errors)

    """

    # Eliminate empty lines and any lines that are not valid URLs (we assume
    #   that it's one URL per line)
    # At the same time, trim initial/final whitespace
    valid_list = []
    for line in link_list:
        if check_url(line):

            line = strip_whitespace(line)
            if re.search('\S', line):
                valid_list.append(line)

    if valid_list:

        # Some URLs survived the cull

        # Get the contents of the buffer
        if mark_start is None or mark_end is None:

            # No Gtk.TextMarks supplied, we're forced to use iters
            buffer_text = textbuffer.get_text(
                textbuffer.get_start_iter(),
                textbuffer.get_end_iter(),
                # Don't include hidden characters
                False,
            )

        else:

            buffer_text = textbuffer.get_text(
                textbuffer.get_iter_at_mark(mark_start),
                textbuffer.get_iter_at_mark(mark_end),
                False,
            )

        # Remove any URLs that already exist in the buffer
        line_list = buffer_text.split('\n')
        mod_list = []
        for line in valid_list:
            if not line in line_list:
                mod_list.append(line)

        # Add any surviving URLs to the buffer, first adding a newline
        #   character, if the buffer doesn't end in one
        if mod_list:

            if not re.search('\n\s*$', buffer_text) and buffer_text != '':
                mod_list[0] = '\n' + mod_list[0]

            textbuffer.insert(
                textbuffer.get_end_iter(),
                str.join('\n', mod_list) + '\n',
            )


def add_links_to_textview_from_clipboard(app_obj, textbuffer, mark_start=None,
mark_end=None, drag_drop_text=None):

    """Called by mainwin.AddVideoDialogue.__init__(),
    .on_window_drag_data_received() and .clipboard_timer_callback().

    Function to add valid URLs from the clipboard to a Gtk.TextView, ignoring
    anything that is not a valid URL, and ignoring duplicate URLs.

    If some text is supplied as an argument, uses that text rather than the
    clipboard text

    Args:

        app_obj (mainapp.TartubeApp): The main application

        textbuffer (Gtk.TextBuffer): The textbuffer to which valis URLs should
            be added (unless they are duplicates)

        mark_start, mark_end (Gtk.TextMark): The marks at the start/end of the
            buffer (using marks rather than iters prevents Gtk errors)

        drag_drop_text (str): If specified, use this text and ignore the
            clipboard

    """

    if drag_drop_text is None:

        # Get text from the system clipboard
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        cliptext = clipboard.wait_for_text()

    else:

        # Ignore the clipboard, and use the specified text
        cliptext = drag_drop_text

    # Pass the text on to the next function, first converting it into a list
    if cliptext is not None:
        add_links_to_textview(
            app_obj,
            cliptext.split('\n'),
            textbuffer,
            mark_start,
            mark_end,
        )


def check_url(url):

    """Can be called by anything.

    Checks for valid URLs.

    Args:

        url (str): The URL to check

    Returns:

        True if the URL is valid, False if invalid.

    """

    prepared_request = requests.models.PreparedRequest()
    try:
        prepared_request.prepare_url(url, None)

        # The requests module allows a lot of URLs that are definitely not of
        #   interest to us
        # This filter seems to catch most of the gibberish (although it's not
        #   perfect)
        if re.search('^\S+\.\S', url) \
        or re.search('localhost', url):
            return True
        else:
            return False
    except:
        return False


def convert_item(item, to_unicode=False):

    """Can be called by anything.

    Based on the convert_item() function in youtube-dl-gui.

    Convert item between 'unicode' and 'str'.

    Args:

        item (-): Can be any python item

        to_unicode (bool): When True it will convert all the 'str' types to
            'unicode'. When False it will convert all the 'unicode' types back
            to 'str'

    Returns:

        The converted item

    """

    if to_unicode and isinstance(item, str):
        # Convert str to unicode
        return item.decode(get_encoding(), 'ignore')

    if not to_unicode and isinstance(item, unicode):
        # Convert unicode to str
        return item.encode(get_encoding(), 'ignore')

    if hasattr(item, '__iter__'):
        # Handle iterables
        temp_list = []

        for sub_item in item:
            if isinstance(item, dict):
                temp_list.append(
                    (
                        convert_item(sub_item, to_unicode),
                        convert_item(item[sub_item], to_unicode),
                    )
                )
            else:
                temp_list.append(convert_item(sub_item, to_unicode))

        return type(item)(temp_list)

    return item


def convert_path_to_temp(app_obj, old_path, move_flag=False):

    """Can be called by anything.

    Converts a full path to a file that would be stored in Tartube's data
    directory (mainapp.TartubeApp.downloads_dir) into the equivalent path in
    Tartube's temporary directory (mainapp.TartubeApp.temp_dl_dir).

    Optionally moves a file from one location to the other.

    Regardless of whether the file is moved or not, creates the destination
    sub-directory if it doesn't already exist, and deletes the destination file
    if it already exists (both of which prevent exceptions being raised).

    Args:

        app_obj (mainapp.TartubeApp): The main application

        old_path (str): Full path to the existing file

        move_flag (bool): If True, the file is actually moved to the new
            location

    Returns:

        new_path: The converted full file path, or None if a filesystem error
            occurs

    """

    data_dir_len = len(app_obj.downloads_dir)

    new_path = app_obj.temp_dl_dir + old_path[data_dir_len:]
    new_dir, new_filename = os.path.split(new_path.strip("\""))

    # The destination folder must exist, before moving files into it
    if not os.path.exists(new_dir):
        try:
            os.makedirs(new_dir)
        except:
            return None

    # On MS Windows, a file name new_path must not exist, or an exception will
    #   be raised
    if os.path.isfile(new_path):
        try:
            os.remove(new_path)
        except:
            return None

    # Move the file now, if the calling code requires that
    if move_flag:

        # (On MSWin, can't do os.rename if the destination file already exists)
        if os.path.isfile(new_path):
            os.remove(new_path)

        # (os.rename sometimes fails on external hard drives; this is safer)
        shutil.move(old_path, new_path)

    # Return the converted file path
    return new_path


def convert_seconds_to_string(seconds, short_flag=False):

    """Can be called by anything.

    Converts a time in seconds into a formatted string.

    Args:

        seconds (int or float): The time to convert

        short_flag (bool): If True, show '05:15' rather than '0:05:15'

    Returns:

        The converted string, e.g. '05:12' or '16:05:12'

    """

    # Round up fractional seconds
    if seconds is not None:
        if seconds != int(seconds):
            seconds = int(seconds) + 1
    else:
        seconds = 1

    if short_flag and seconds < 3600:

        # When required, show 05:15 rather than 0:05:15
        minutes = int(seconds / 60)
        seconds = int(seconds % 60)

        return '{:02d}:{:02d}'.format(minutes, seconds)

    else:
        return str(datetime.timedelta(seconds=seconds))


def convert_youtube_id_to_rss(media_type, youtube_id):

    """Can be called by anything; usually called by
    media.GenericRemoteContainer.set_rss().

    Convert the channel/playlist ID provided by YouTube into the full URL for
    the channel/playlist RSS feed.

    Args:

        media_type (str): 'channel' or 'playlist'

        youtube_id (str): The YouTube channel or playlist ID

    Returns:

        The full URL for the RSS feed

    """

    return 'https://www.youtube.com/feeds/videos.xml?' + media_type \
    + '_id=' + youtube_id


def convert_youtube_to_hooktube(url):

    """Can be called by anything.

    Converts a YouTube weblink to a HookTube weblink (but doesn't modify links
    to other sites.

    Args:

        url (str): The weblink to convert

    Returns:

        The converted string

    """

    if re.search(r'^https?:\/\/(www)+\.youtube\.com', url):

        url = re.sub(
            r'youtube\.com',
            'hooktube.com',
            url,
            # Substitute first occurence only
            1,
        )

    return url


def convert_youtube_to_invidious(app_obj, url):

    """Can be called by anything.

    Converts a YouTube weblink to an Invidious weblink (but doesn't modify
    links to other sites).

    Args:

        url (str): The weblink to convert

    Returns:

        The converted string

    """

    if re.search(r'^https?:\/\/(www)+\.youtube\.com', url) \
    and re.search('\w+\.\w+', app_obj.custom_invidious_mirror):

        url = re.sub(
            r'youtube\.com',
            app_obj.custom_invidious_mirror,
            url,
            # Substitute first occurence only
            1,
        )

    return url


def convert_youtube_to_other(app_obj, url):

    """Can be called by anything.

    Converts a YouTube weblink to a weblink pointing at an alternative
    YouTube front-end (such as Hooktube or Invidious).

    Args:

        app_obj (mainapp.TartubeApp): The main application

        url (str): The weblink to convert

    Returns:

        The converted string

    """

    if re.search(r'^https?:\/\/(www)+\.youtube\.com', url):

        url = re.sub(
            r'youtube\.com',
            app_obj.custom_dl_divert_website,
            url,
            # Substitute first occurence only
            1,
        )

    return url


def debug_time(msg):

    """Called by all functions in downloads.py, info.py, mainapp.py,
    mainwin.py, refresh.py, tidy.py and updates.py.

    Writes the current time, and the name of the calling function to STDOUT,
    e.g. '2020-01-16 08:55:06 ap 91 __init__'.

    Args:

        msg (str): The message to write

    """

    # Uncomment this code to display the time with microseconds
#    print(str(datetime.datetime.now().time()) + ' ' + msg)

    # Uncomment this code to display the time without microseconds
    dt = datetime.datetime.now()
    print(str(dt.replace(microsecond=0)) + ' ' + msg)

    # Uncomment this code to display the message, without a timestamp
#    print(msg)

    # This line makes my IDE collapse functions nicely
    return


def disk_get_free_space(path, bytes_flag=False):

    """Can be called by anything.

    Returns the size of the disk on which a specified file/directory exists,
    minus the used space on that disk.

    Args:

        path (str): Path to a file/directory on the disk, typically Tartube's
            data directory

        bytes_flag (bool): True to return an integer value in MB, false to
            return a value in bytes

    Returns:

        The free space in MB (or in bytes, if the flag is specified), or 0 if
            the size can't be calculated for any reason

    """

    try:
        total_bytes, used_bytes, free_bytes = shutil.disk_usage(
            os.path.realpath(path),
        )

        if not bytes_flag:
            return int(free_bytes / 1000000)
        else:
            return free_bytes

    except:
        return 0


def disk_get_total_space(path, bytes_flag=False):

    """Can be called by anything.

    Returns the size of the disk on which a specified file/directory exists.

    Args:

        path (str): Path to a file/directory on the disk, typically Tartube's
            data directory

        bytes_flag (bool): True to return an integer value in MB, false to
            return a value in bytes

    Returns:

        The total size in MB (or in bytes, if the flag is specified)

    """

    total_bytes, used_bytes, free_bytes = shutil.disk_usage(
        os.path.realpath(path),
    )

    if not bytes_flag:
        return int(total_bytes / 1000000)
    else:
        return total_bytes


def disk_get_used_space(path, bytes_flag=False):

    """Can be called by anything.

    Returns the size of the disk on which a specified file/directory exists,
    minus the free space on that disk.

    Args:

        path (str): Path to a file/directory on the disk, typically Tartube's
            data directory

        bytes_flag (bool): True to return an integer value in MB, false to
            return a value in bytes

    Returns:

        The used space in MB (or in bytes, if the flag is specified)

    """

    total_bytes, used_bytes, free_bytes = shutil.disk_usage(
        os.path.realpath(path),
    )

    if not bytes_flag:
        return int(used_bytes / 1000000)
    else:
        return used_bytes


def extract_livestream_data(stderr):

    """Called by downloads.JSONFetcher.do_fetch() and
    MiniJSONFetcher.do_fetch().

    For some reason, YouTube messages giving the (approximate) start time of a
    livestream are written to STDERR.

    Extracts various data and returns it.

    Args:

        stderr (text): A standard YouTube message

    Return values:

        If extraction is successful, returns a dictionary of three values:
            live_msg (str): Text that can be displayed in the Video Catalogue
            live_time (int): Approximate time (matching time.time()) at which
                the livestream is due to start
            live_debut_flag (bool): True for a YouTube 'premiere' video, False
                for an ordinary livestream

        If extraction fails, returns an empty list

    """

    # This live event will begin in a few moments.
    match_list = re.search(
        'This live event will begin in a few moments',
        stderr,
    )

    if match_list:

        return {
            'live_msg': _('Live soon'),
            'live_time': int(time.time()),
            'live_debut_flag': False,
        }

    # Premiere will begin shortly
    match_list = re.search(
        'Premiere will begin shortly',
        stderr,
    )

    if match_list:

        return {
            'live_msg': _('Debut soon'),
            'live_time': int(time.time()),
            'live_debut_flag': True,
        }

    # This live event will begin in N minutes.
    match_list = re.search(
        'This live event will begin in (\d+) minute',
        stderr,
    )

    if match_list:

        group_list = match_list.groups()
        number = int(group_list[0])

        return {
            'live_msg': _('Live in {0} minutes').format(group_list[0]),
            'live_time': int(time.time()) + (number * 60),
            'live_debut_flag': False,
        }

    # Premieres in N minutes
    match_list = re.search(
        'Premieres in (\d+) minute',
        stderr,
    )

    if match_list:

        group_list = match_list.groups()
        number = int(group_list[0])

        return {
            'live_msg': _('Debut in {0} minutes').format(group_list[0]),
            'live_time': int(time.time()) + (number * 60),
            'live_debut_flag': True,
        }

    # This live event will begin in N hours.
    match_list = re.search(
        'This live event will begin in (\d+) hour',
        stderr,
    )

    if match_list:

        group_list = match_list.groups()
        number = int(group_list[0])

        return {
            'live_msg': _('Live in {0} hours').format(group_list[0]),
            'live_time': int(time.time()) + (number * 3600),
            'live_debut_flag': False,
        }

    # Premieres in N hours
    match_list = re.search(
        'Premieres in (\d+) hour',
        stderr,
    )

    if match_list:

        group_list = match_list.groups()
        number = int(group_list[0])

        return {
            'live_msg': _('Debut in {0} hours').format(group_list[0]),
            'live_time': int(time.time()) + (number * 3600),
            'live_debut_flag': True,
        }

    # This live event will begin in N days.
    match_list = re.search(
        'This live event will begin in (\d+) day',
        stderr,
    )

    if match_list:

        group_list = match_list.groups()
        number = int(group_list[0])

        return {
            'live_msg': _('Live in {0} days').format(group_list[0]),
            'live_time': int(time.time()) + (number * 86400),
            'live_debut_flag': False,
        }

    # Premieres in N days
    match_list = re.search(
        'Premieres in (\d+) day',
        stderr,
    )

    if match_list:

        group_list = match_list.groups()
        number = int(group_list[0])

        return {
            'live_msg': _('Debut in {0} days').format(group_list[0]),
            'live_time': int(time.time()) + (number * 86400),
            'live_debut_flag': True,
        }

    # Not a livestream, return an empty dictionary
    return {}


def find_available_name(app_obj, old_name, min_value=2, max_value=9999):

    """Can be called by anything.

    mainapp.TartubeApp.media_name_dict stores the names of all media.Channel,
    media.Playlist and media.Folder objects as keys.

    old_name is the name of an existing media data object. This function
    slightly modifies the name, converting 'my_name' into 'my_name_N', where N
    is the smallest positive integer for which the name is available.

    If the specified old_name is already in that format (for example,
    'Channel_4'), then the old number is stripped away, and this function
    starts looking from the first integer after that (for example,
    'Channel_5').

    To preclude any possibility of infinite loops, the function will give up
    after max_value attempts.

    Args:

        app_obj (mainapp.TartubeApp): The main application

        old_name (str): The name which is already in use by a media data object

        min_value (str): The first name to try. 2 by default, so the first
            name checked will be 'my_name_2'

        max_value (int): When to give up. 9999 by default, meaning that this
            function will try everything up to 'my_name_9999' before giving up.
            If set to -1, this function never gives up

    Returns:

        None on failure, the new name on success

    """

    # If old_name is already in the format 'my_name_N', where N is an integer
    #   in the range min_value < N < max_value, then strip it away
    if re.search(r'\_\d+$', old_name):

        number = int(re.sub(r'^.*\_(\d+)$', r'\1', old_name))
        mod_name = re.sub(r'^(.*)\_\d+$', r'\1', old_name)

        if number >= 2 and number < max_value:

            old_name = mod_name
            min_value = number + 1

    # Find an available name
    if max_value != -1:

        for n in range (min_value, max_value):

            new_name = old_name + '_'  + str(n)
            if not new_name in app_obj.media_name_dict:
                return new_name

        # Failure
        return None

    else:

        # Renaming is essential, for example, in calls from
        #   mainapp.TartubeApp.load_db(). Keep going indefinitely until an
        #   available name is found
        n = 1
        while 1:
            n += 1

            new_name = old_name + '_'  + str(n)
            if not new_name in app_obj.media_name_dict:
                return new_name


def find_thumbnail(app_obj, video_obj, temp_dir_flag=False):

    """Can be called by anything.

    No way to know which image format is used by all websites for their video
    thumbnails, so look for the most common ones, and return the path to the
    thumbnail file if one is found.

    Args:

        app_obj (mainapp.TartubeApp): The main application

        video_obj (media.Video): The video object handling the downloaded video

        temp_dir_flag (bool): If True, this function will look in Tartube's
            temporary data directory, if the thumbnail isn't found in the main
            data directory

    Returns:

        path (str): The full path to the thumbnail file, or None

    """

    for ext in formats.IMAGE_FORMAT_LIST:

        # Look in Tartube's permanent data directory
        normal_path = video_obj.check_actual_path_by_ext(app_obj, ext)
        if normal_path is not None:
            return normal_path

        elif temp_dir_flag:

            # Look in temporary data directory
            data_dir_len = len(app_obj.downloads_dir)

            temp_path = video_obj.get_actual_path_by_ext(app_obj, ext)
            temp_path = app_obj.temp_dl_dir + temp_path[data_dir_len:]
            if os.path.isfile(temp_path):
                return temp_path

    # Catch YouTube .jpg thumbnails, in the form .jpg?...
    # v2.2.005 The glob.glob() call crashes on certain videos. I'm not sure
    #   why, but we can circumvent the crash with try...except
    normal_path = video_obj.get_actual_path_by_ext(app_obj, '.jpg*')
    try:
        for glob_path in glob.glob(normal_path):
            if os.path.isfile(glob_path):
                return glob_path
    except:
        pass

    if temp_dir_flag:

        temp_path = video_obj.get_actual_path_by_ext(app_obj, '.jpg*')
        temp_path = app_obj.temp_dl_dir + temp_path[data_dir_len:]

        try:
            for glob_path in glob.glob(temp_path):
                if os.path.isfile(glob_path):
                    return glob_path
        except:
            pass

    # No matching thumbnail found
    return None


def find_thumbnail_restricted(app_obj, video_obj):

    """Called by mainapp.TartubeApp.update_video_when_file_found().

    Modified version of utils.find_thumbnail().

    Returns the path of the thumbnail in the same directory as its video. The
    path is returned as a list, so the calling code can convert it into the
    equivalent path in the '.thumbs' subdirectory.

    Args:

        app_obj (mainapp.TartubeApp): The main application

        video_obj (media.Video): The video object handling the downloaded video

    Returns:

        return_list (list): A list whose items, when combined, will be the full
            path to the thumbnail file. If no thumbnail file was found, an
            empty list is returned

    """

    for ext in formats.IMAGE_FORMAT_LIST:

        actual_dir = video_obj.parent_obj.get_actual_dir(app_obj)
        test_path = os.path.abspath(
            os.path.join(
                actual_dir,
                video_obj.file_name + ext,
            ),
        )

        if os.path.isfile(test_path):
            return [ actual_dir, video_obj.file_name + ext ]

    # No matching thumbnail found
    return []


def find_thumbnail_webp(app_obj, video_obj):

    """Can be called by anything.

    In June 2020, YouTube started serving .webp thumbnails. Gtk cannot display
    them, so Tartube typically converts themto .jpg.

    This is a modified version of utils.find_thumbnail(), which looks for
    thumbnails in the .webp or malformed .jpg format, and return the path to
    the thumbnail file if one is found.

    Args:

        app_obj (mainapp.TartubeApp): The main application

        video_obj (media.Video): The video object handling the downloaded video

    Returns:

        path (str): The full path to the thumbnail file, or None

    """

    for ext in ('.webp', '.jpg'):

        main_path = video_obj.get_actual_path_by_ext(app_obj, ext)
        if os.path.isfile(main_path) \
        and app_obj.ffmpeg_manager_obj.is_webp(main_path):
            return main_path

        # The extension may be followed by additional characters, e.g.
        #   .jpg?sqp=-XXX (as well as several other patterns)
        # v2.2.005 The glob.glob() call crashes on certain videos. I'm not
        #   sure why, but we can circumvent the crash with try...except
        try:
            for actual_path in glob.glob(main_path + '*'):
                if os.path.isfile(actual_path) \
                and app_obj.ffmpeg_manager_obj.is_webp(actual_path):
                    return actual_path
        except:
            pass

        subdir_path = video_obj.get_actual_path_in_subdirectory_by_ext(
            app_obj,
            ext,
        )

        if os.path.isfile(subdir_path) \
        and app_obj.ffmpeg_manager_obj.is_webp(subdir_path):
            return subdir_path

        try:
            for actual_path in glob.glob(subdir_path + '*'):
                if os.path.isfile(actual_path) \
                and app_obj.ffmpeg_manager_obj.is_webp(actual_path):
                    return actual_path
        except:
            pass

    # No webp thumbnail found
    return None


def format_bytes(num_bytes):

    """Can be called by anything.

    Based on the format_bytes() function in youtube-dl-gui.

    Convert bytes into a formatted string, e.g. '23.5GiB'.

    Args:

        num_bytes (float): The number to convert

    Returns:

        The formatted string

    """

    if num_bytes == 0.0:
        exponent = 0
    else:
        exponent = int(math.log(num_bytes, formats.KILO_SIZE))

    suffix = formats.FILESIZE_METRIC_LIST[exponent]
    output_value = num_bytes / (formats.KILO_SIZE ** exponent)

    return "%.2f%s" % (output_value, suffix)


def generate_system_cmd(app_obj, media_data_obj, options_list,
dl_sim_flag=False, dl_classic_flag=False, missing_video_check_flag=None,
divert_mode=None):

    """Called by downloads.VideoDownloader.do_download() and
    mainwin.SystemCmdDialogue.update_textbuffer().

    Based on YoutubeDLDownloader._get_cmd().

    Prepare the system command that instructs youtube-dl to download the
    specified media data object.

    Args:

        app_obj (mainapp.TartubeApp): The main application

        media_data_obj (media.Video, media.Channel, media.Playlist,
            media.Folder): The media data object to be downloaded

        options_list (list): A list of download options generated by a call to
            options.OptionsParser.parse()

        dl_sim_flag (bool): True if a simulated download is to take place,
            False if a real download is to take place

        dl_classic_flag (bool): True if the download operation was launched
            from the Classic Mode Tab, False otherwise

        missing_video_check_flag (bool): True if the download operation is
            trying to detect missing videos (downloaded by user, but since
            removed by the creator), False otherwise

        divert_mode (str): If not None, should be one of the values of
            mainapp.TartubeApp.custom_dl_divert_mode: 'default', 'hooktube',
            'invidious' or 'other'. If not 'default', a media.Video object
            whose source URL points to YouTube should be converted to the
            specified alternative YouTube front-end (no conversion takes place
            for channels/playlists/folders)

    Returns:

        Python list that contains the system command to execute and its
            arguments

    """

    # Simulate the download, rather than actually downloading videos, if
    #   required
    if dl_sim_flag:
        options_list.append('--dump-json')

    # If actually downloading videos, use (or create) an archive file so that,
    #   if the user deletes the videos, youtube-dl won't try to download them
    #   again
    # We don't use an archive file when downloading into a system folder
    if (
        not dl_classic_flag and app_obj.allow_ytdl_archive_flag \
        or dl_classic_flag and app_obj.classic_ytdl_archive_flag
    ):
        if not dl_classic_flag \
        and (
            not isinstance(media_data_obj, media.Folder)
            or not media_data_obj.fixed_flag
        ) and (
            not isinstance(media_data_obj, media.Video)
            or not isinstance(media_data_obj.parent_obj, media.Folder)
            or not media_data_obj.parent_obj.fixed_flag
        ):
            # (Create the archive file in the media data object's default
            #   sub-directory, not the alternative download destination, as
            #   this helps youtube-dl to work the way we want it to work)
            if isinstance(media_data_obj, media.Video):
                dl_path = media_data_obj.parent_obj.get_default_dir(app_obj)
            else:
                dl_path = media_data_obj.get_default_dir(app_obj)

            options_list.append('--download-archive')
            options_list.append(
                os.path.abspath(os.path.join(dl_path, 'ytdl-archive.txt')),
            )

        elif dl_classic_flag:

            # Create the archive file in destination directory
            dl_path = media_data_obj.dummy_dir

            options_list.append('--download-archive')
            options_list.append(
                os.path.abspath(os.path.join(dl_path, 'ytdl-archive.txt')),
            )

    # Show verbose output (youtube-dl debugging mode), if required
    if app_obj.ytdl_write_verbose_flag:
        options_list.append('--verbose')

    # Supply youtube-dl with the path to the ffmpeg/avconv binary, if the
    #   user has provided one
    # If both paths have been set, prefer ffmpeg, unless the 'prefer_avconv'
    #   download option had been specified
    if '--prefer-avconv' in options_list and app_obj.avconv_path is not None:
        options_list.append('--ffmpeg-location')
        options_list.append(app_obj.avconv_path)
    elif app_obj.ffmpeg_path is not None:
        options_list.append('--ffmpeg-location')
        options_list.append(app_obj.ffmpeg_path)
    elif app_obj.avconv_path is not None:
        options_list.append('--ffmpeg-location')
        options_list.append(app_obj.avconv_path)

    # Convert a YouTube URL to an alternative YouTube front-end, if required
    source = media_data_obj.source
    if isinstance(media_data_obj, media.Video) and divert_mode:
        if divert_mode == 'hooktube':
            source = convert_youtube_to_hooktube(source)
        elif divert_mode == 'invidious':
            source = convert_youtube_to_invidious(app_obj, source)
        elif divert_mode == 'custom' \
        and app_obj.custom_dl_divert_website is not None \
        and len(app_obj.custom_dl_divert_website) > 2:
            source = convert_youtube_to_other(app_obj, source)

    # Convert a path beginning with ~ (not on MS Windows)
    ytdl_path = app_obj.check_downloader(app_obj.ytdl_path)
    if os.name != 'nt':
        ytdl_path = re.sub('^\~', os.path.expanduser('~'), ytdl_path)

    # Set the list
    cmd_list = [ytdl_path] + options_list + [source]

    return cmd_list


def get_encoding():

    """Called by utils.convert_item().

    Based on the get_encoding() function in youtube-dl-gui.

    Returns:

        The system encoding.

    """

    try:
        encoding = locale.getpreferredencoding()
        'TEST'.encode(encoding)
    except:
        encoding = 'UTF-8'

    return encoding


def get_options_manager(app_obj, media_data_obj):

    """Can be called by anything. Subsequently called by this function
    recursively.

    Fetches the options.OptionsManager which applies to the specified media
    data object.

    The media data object might specify its own options.OptionsManager, or
    we might have to use the parent's, or the parent's parent's (and so
    on). As a last resort, use General Options Manager.

    Args:

        app_obj (mainapp.TartubeApp): The main application

        media_data_obj (media.Video, media.Channel, media.Playlist,
            media.Folder): A media data object

    Returns:

        The options.OptionsManager object that applies to the specified
            media data object

    """

    if media_data_obj.options_obj:
        return media_data_obj.options_obj
    elif media_data_obj.parent_obj:
        return get_options_manager(app_obj, media_data_obj.parent_obj)
    else:
        return app_obj.general_options_obj


def is_youtube(url):

    """Can be called by anything.

    Checks whether a link is a YouTube link or not.

    Args:

        url (str): The weblink to check

    Returns:

        True if it's a YouTube link, False if not

    """

    if re.search(r'^https?:\/\/(www)+\.youtube\.com', url):
        return True
    else:
        return False


def move_metadata_to_subdir(app_obj, video_obj, ext):

    """Can be called by anything.

    Moves a description, JSON or annotations file from the same directory as
    its video, into the subdirectory '.data'.

    Args:

        app_obj (mainapp.TartubeApp): The main application

        video_obj (media.Video): The file's parent video

        ext (str): The file extension, which will be one of '.description',
            '.info.json' or '.annotations.xml'

    """

    main_path = video_obj.get_actual_path_by_ext(app_obj, '.description')
    subdir = os.path.abspath(
        os.path.join(
            video_obj.parent_obj.get_actual_dir(app_obj),
            app_obj.metadata_sub_dir,
        ),
    )

    subdir_path = video_obj.get_actual_path_in_subdirectory_by_ext(
        app_obj,
        '.description',
    )

    if os.path.isfile(main_path) and not os.path.isfile(subdir_path):

        try:
            if not os.path.isdir(subdir):
                os.makedirs(subdir)

            # (os.rename sometimes fails on external hard drives; this
            #   is safer)
            shutil.move(main_path, subdir_path)

        except:
            pass


def move_thumbnail_to_subdir(app_obj, video_obj):

    """Can be called by anything.

    Moves a thumbnail file from the same directory as its video, into the
    subdirectory '.thumbs'.

    Args:

        app_obj (mainapp.TartubeApp): The main application

        video_obj (media.Video): The file's parent video

    """

    path_list = find_thumbnail_restricted(app_obj, video_obj)
    if path_list:

        main_path = os.path.abspath(
            os.path.join(
                path_list[0], path_list[1],
            ),
        )

        subdir = os.path.abspath(
            os.path.join(
                path_list[0], app_obj.thumbs_sub_dir,
            ),
        )

        subdir_path = os.path.abspath(
            os.path.join(
                path_list[0], app_obj.thumbs_sub_dir, path_list[1],
            ),
        )

        if os.path.isfile(main_path) \
        and not os.path.isfile(subdir_path):

            try:
                if not os.path.isdir(subdir):
                    os.makedirs(subdir)

                shutil.move(main_path, subdir_path)

            except:
                pass


def open_file(app_obj, uri):

    """Can be called by anything.

    Opens a file using the system's default software (e.g. open a media file in
    the default media player; open a weblink in the default browser).

    Args:

        app_obj (mainapp.TartubeApp): The main application

        uri (str): The URI to open

    """

    if sys.platform == "win32":

        try:
            os.startfile(uri)
        except:
            app_obj.system_error(
                501,
                'Could not open \'' + str(uri) + '\'',
            )

    else:

        opener = "open" if sys.platform == "darwin" else "xdg-open"
        # (Assume a return code of 0 on success)
        if subprocess.call([opener, uri]):
            app_obj.system_error(
                502,
                'Could not open \'' + str(uri) + '\'',
            )


def parse_ytdl_options(options_string):

    """Called by options.OptionsParser.parse() or info.InfoManager.run().

    Also called by process.ProcessManager.__init__, to parse FFmpeg command-
    line options on the same basis.

    Parses the 'extra_cmd_string' option, which can contain arguments inside
    double quotes "..." (arguments that can therefore contain whitespace)

    If options_string contains newline characters, then it terminates an
    argument, closing newline character or not.

    Args:

        options_string (str): A string containing various youtube-dl
            download options, as described above

    Returns:

        A separated list of youtube-dl download options

    """

    # Add options, one at a time, to a list
    return_list = []

    for line in options_string.splitlines():

        # Set a flag for an item beginning with double quotes, and reset it for
        #   an item ending in double quotes
        quote_flag = False
        # Temporary list to hold such quoted arguments
        quote_list = []

        for item in line.split():

            quote_flag = (quote_flag or item[0] == "\"")

            if quote_flag:
                quote_list.append(item)
            else:
                return_list.append(item)

            if quote_flag and item[-1] == "\"":

                # Special case mode is over
                return_list.append(" ".join(quote_list)[1:-1])

                quote_flag = False
                quote_list = []

    return return_list


def shorten_string(string, num_chars):

    """Can be called by anything.

    If string is longer than num_chars, truncates it and adds an ellipsis.

    Args:

        string (string): The string to convert

        num_chars (int): The maximum length of the desired string

    Returns:

        The converted string

    """

    if string and len(string) > num_chars:
        num_chars -= 3
        string = string[:num_chars] + '...'

    return string


def shorten_string_two_lines(string, num_chars):

    """Can be called by anything.

    Modified version of shorten_string(). Reduces the string to two lines
    (separated by a newline character). Each line has the specified maximum
    length. If there is too much text to fit on the second line, truncates it
    and adds an ellipsis.

    Args:

        string (string): The string to convert

        num_chars (int): The maximum length of the desired string

    Returns:

        The converted string

    """

    if string and len(string) > num_chars:

        line_list = []
        current_line = ''

        for word in string.split():

            if len(word) > num_chars:

                # To keep the code simple, the algorithm ends here, with this
                #   word on a separate line. This may produce a return string
                #   containing only line
                if current_line != '':
                    line_list.append(current_line)

                line_list.append(word[0:num_chars] + '...')
                break

            else:

                if current_line != '':
                    mod_line = current_line + ' ' + word
                else:
                    mod_line = word

                if len(mod_line) > num_chars:

                    if current_line != '':
                        line_list.append(current_line)

                    current_line = word

                else:

                    current_line = mod_line

        line_list.append(current_line)

        # Dispense with everything but the first two lines
        line_count = len(line_list)
        if line_count > 2:

            return line_list[0] + '\n' + line_list[1] + '...'

        elif line_count == 2:

            return line_list[0] + '\n' + line_list[1]

        else:

            return line_list[0]

    else:

        # 'string' is empty or short, so there's no need to split it up at all
        return string


def strip_whitespace(string):

    """Can be called by anything.

    Removes any leading/trailing whitespace from a string.

    Args:

        string (str): The string to convert

    Returns:

        The converted string

    """

    if string:
        string = re.sub(r'^\s+', '', string)
        string = re.sub(r'\s+$', '', string)

    return string


def strip_whitespace_multiline(string):

    """Can be called by anything.

    An extended version of utils.strip_whitepspace.

    Divides a string into lines, removes empty lines, removes any leading/
    trailing whitespace from each line, then combines the lines back into a
    single string (with lines separated by newline characters).

    Args:

        string (str): The string to convert

    Returns:

        The converted string

    """

    line_list = string.splitlines()
    mod_list = []

    for line in line_list:
        line = re.sub(r'^\s+', '', line)
        line = re.sub(r'\s+$', '', line)

        if re.search('\S', line):
            mod_list.append(line)

    return "\n".join(mod_list)


def tidy_up_container_name(string, max_length):

    """Called by mainapp.TartubeApp.on_menu_add_channel(),
    .on_menu_add_playlist() and .on_menu_add_folder().

    Before creating a channel, playlist or folder, tidies up the name.

    Removes any leading/trailing whitespace. Reduces multiple whitespace
    characters to a single space character. Applies a maximum length.

    Also replaces any forward/backward slashes with hyphens (if the user
    specifies a name like 'Foo / Bar', that would create a directory on the
    filesystem called .../Foo/Bar, which is definitely not what we want).

    Args:

        string (str): The string to convert

        max_length (int): The maximum length of the converted string (should be
            mainapp.TartubeApp.container_name_max_len)

    Returns:

        The converted string

    """

    if string:

        string = re.sub(r'^\s+', '', string)
        string = re.sub(r'\s+$', '', string)
        string = re.sub(r'\s+', ' ', string)
        string = re.sub(r'[\/\\]', '-', string)

        return string[0:max_length]

    else:

        # Empty string
        return string


def tidy_up_long_descrip(string, max_length=80):

    """Can be called by anything.

    A modified version of utils.tidy_up_long_string. In this case, the
    specified string can contain any number of newline characters. We begin
    by splitting that string into a list of lines.

    Then we split any line which is longer than the specified maximum length,
    which gives us a (possibly longer) list of lines.

    Finally we recombine those lines into a single string, with lines joined by
    newline characters.

    Args:

        string (str): The string to convert

        max_length (int): The maximum length of lines, before they are
            recombined into a single string

    Returns:

        The converted string

    """

    if string:

        line_list = []

        for line in string.split('\n'):

            if line == '':
                # Preserve empty lines
                line_list.append('')

            else:

                new_list = textwrap.wrap(
                    line,
                    width=max_length,
                    # Don't split up URLs
                    break_long_words=False,
                    break_on_hyphens=False,
                )

                for mini_line in new_list:
                    line_list.append(mini_line)

        return '\n'.join(line_list)

    else:

        # Empty string
        return string


def tidy_up_long_string(string, max_length=80, reduce_flag=True,
split_words_flag=False):

    """Can be called by anything.

    The specified string can contain any number of newline characters.

    Replaces newline characters with a single space character.

    Optionally reduces multiple whitespace characters and removes initial/
    final whitespace character(s).

    Then splits the string into a list of lines, each with the specified
    maximum length.

    Finally recombines those lines into a single string, with lines joined by
    newline characters.

    Args:

        string (str): The string to convert

        max_length (int): The maximum length of lines, before they are
            recombined into a single string

        reduce_flag (bool): If True, initial and final whitespace is removed,
            and multiple successive whitespace characters are reduced to a
            single space character

        split_words_flag(bool): If True, the function will break words
            (including hyphenated words) into smaller pieces, if necessary

    Returns:

        The converted string

    """

    if string:

        string = re.sub(r'\r\n', ' ', string)

        if reduce_flag:
            string = re.sub(r'^\s+', '', string)
            string = re.sub(r'\s+$', '', string)
            string = re.sub(r'\s+', ' ', string)

        line_list = []
        for line in string.split('\n'):

            if line == '':
                # Preserve empty lines
                line_list.append('')

            else:
                new_list = textwrap.wrap(
                    line,
                    width=max_length,
                    # Don't split up URLs by default
                    break_long_words=split_words_flag,
                    break_on_hyphens=split_words_flag,
                )

                for mini_line in new_list:
                    line_list.append(mini_line)

        return '\n'.join(line_list)

    else:

        # Empty string
        return string


def to_string(data):

    """Can be called by anything.

    Convert any data type to a string.

    Args:

        data (-): The data type

    Returns:

        The converted string

    """

    return '%s' % data


def upper_case_first(string):

    """Can be called by anything.

    Args:

        string (str): The string to capitalise

    Returns:

        The converted string

    """

    return string[0].upper() + string[1:]
