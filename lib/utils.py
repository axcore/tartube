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


"""Utility functions used by code copied from youtube-dl-gui."""


# Import Gtk modules
from gi.repository import Gtk, Gdk


# Import other modules
import datetime
import locale
import math
import os
import re
import requests
import subprocess
import sys
import textwrap


# Import our modules
from . import formats
from . import mainapp


# Functions


def add_links_from_clipboard(app_obj, widget):

    """Called by mainwin.AddVideoDialogue.__init__(),
    mainwin.AddChannelDialogue.__init__() and
    mainwin.AddPlaylistDialogue.__init__().

    Function to add valid URLs from the clipboard to a Gtk.TextView, ignoring
    anything that is not a valid URL.

    Args:

        app_obj (mainapp.TartubeApp): The main application

        widget (Gtk.Entry or Gtk.TextBuffer): The widget to which valis URLs
            should be added. If an entry, only the first valid URL is added.
            If a textbuffer, all valid URLs are added

    """

    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
    cliptext = clipboard.wait_for_text()

    valid_list = []
    if cliptext is not None and cliptext != Gdk.SELECTION_CLIPBOARD:
        for line in cliptext.split('\n'):
            if check_url(line):

                line = strip_whitespace(line)
                if re.search('\S', line):
                    valid_list.append(line)

    if valid_list:
        if isinstance(widget, Gtk.Entry):
            widget.set_text(valid_list[0])
        elif isinstance(widget, Gtk.TextBuffer):
            widget.set_text(str.join('\n', valid_list))


def check_url(url):

    """Can be called by anything.

    Checks for valid URLs.

    Args:

        url (string): The URL to check

    Returns:

        True if the URL is valid, False if invalid.

    """

    prepared_request = requests.models.PreparedRequest()
    try:
        prepared_request.prepare_url(url, None)
        return True
    except:
        return False


def convert_item(item, to_unicode=False):

    """Based on the convert_item() function in youtube-dl-gui. Now called by
    various functions in downloads.VideoDownloader and in this module.

    Convert item between 'unicode' and 'str'.

    Args:

        item (-): Can be any python item.

        to_unicode (boolean): When True it will convert all the 'str' types
            to 'unicode'. When False it will convert all the 'unicode' types
            back to 'str'.

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

    """Called by mainwin.MainWin.results_list_update_row() and
    downloads.VideoDownloader.confirm_sim_video().

    Converts a full path to a file that would be stored in Tartube's data
    directory (mainapp.TartubeApp.downloads_dir) into the equivalent path in
    Tartube's temporary directory (mainapp.TartubeApp.temp_dl_dir).

    Optionally moves a file from one location to the other.

    Regardless of whether the file is moved or not, creates the destination
    sub-directory if it doesn't already exist, and deletes the destination file
    if it already exists (both of which prevent exceptions being raised).

    Args:

        app_obj (mainapp.TartubeApp): The main application

        old_path (string): Full path to the existing file

        move_flag (True, False): If True, the file is actually moved to the
            new location

    Returns:

        new_path: The converted full file path

    """

    data_dir_len = len(app_obj.downloads_dir)

    new_path = app_obj.temp_dl_dir + old_path[data_dir_len:]
    new_dir, new_filename = os.path.split(new_path.strip("\""))

    # The destination folder must exist, before moving files into it
    if not os.path.exists(new_dir):
        os.makedirs(new_dir)

    # On MS Windows, a file name new_path must not exist, or an exception will
    #   be raised
    if os.path.isfile(new_path):
        os.remove(new_path)

    # Move the file now, if the calling code requires that
    if move_flag:

        # (On MSWin, can't do os.rename if the destination file already exists)
        if os.path.isfile(new_path):
            os.remove(new_path)

        os.rename(old_path, new_path)

    # Return the converted file path
    return new_path


def convert_seconds_to_string(seconds, short_flag=False):

    """Can be called by anything.

    Converts a time in seconds into a formatted string.

    Args:

        seconds (int or float): The time to convert

        short_flag (True or False): If True, show '05:15' rather than '0:05:15'

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


def convert_youtube_to_hooktube(url):

    """Can be called by anything.

    Converts a YouTube weblink to a HookTube weblink (but doesn't modify links
    to other sites.

    Args:
        url (string): The weblink to convert

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


def find_thumbnail(app_obj, video_obj, temp_dir_flag=False):

    """Called by mainwin.MainWin.results_list_update_row() and
    mainwin.ComplexCatalogueItem.update_thumb_image().

    No way to know which image format is used by all websites for their video
    thumbnails, so look for the most common ones, and return the path to the
    thumbnail file if one is found.

    Args:

        app_obj (mainapp.TartubeApp): The main application

        video_obj (media.Video): The video object handling the downloaded video

        temp_dir_flag (True, False): If True, this function will look in
            Tartube's temporary data directory, if the thumbnail isn't found in
            the main data directory.

    Returns:

        path (string): The full path to the thumbnail file, or None

    """

    for ext in ('.jpg', '.png', '.gif'):

        # Look in main data directory
        path = os.path.abspath(
            os.path.join(
                video_obj.file_dir,
                video_obj.file_name + ext,
            ),
        )

        if os.path.isfile(path):
            return path

        elif temp_dir_flag:

            # Look in temporary data directory
            data_dir_len = len(app_obj.downloads_dir)

            temp_path = app_obj.temp_dl_dir + path[data_dir_len:]
            if os.path.isfile(temp_path):
                return temp_path

    return None


def format_bytes(num_bytes):

    """Based on the format_bytes() function in youtube-dl-gui. Now called by
    media.Video.get_file_size_string() and so on.

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


def get_encoding():

    """Based on the get_encoding() function in youtube-dl-gui. Now called
    by utils.convert_item().

    Returns:

        The system encoding.

    """

    try:
        encoding = locale.getpreferredencoding()
        'TEST'.encode(encoding)
    except:
        encoding = 'UTF-8'

    return encoding


def open_file(uri):

    """Can be called by anything.

    Opens a file using the system's default software (e.g. open a media file in
    the default media player; open a weblink in the default browser).

    Args:

        uri (string): The URI to open

    """

    if sys.platform == "win32":
        os.startfile(uri)
    else:
        opener ="open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, uri])


def remove_shortcuts(path):

    """Based on the remove_shortcuts() function in youtube-dl-gui. Now called
    by options.OptionsParser.build_save_path().

    Return the specified path after removing any shortcuts.

    Args:

        path (string): The path to convert

    Returns:

        The converted path

    """

    return path.replace('~', os.path.expanduser('~'))


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


def strip_whitespace(string):

    """Called by anything.

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


def tidy_up_container_name(string, max_length):

    """Called by mainapp.TartubeApp.on_menu_add_channel(),
    .on_menu_add_playlist() and .on_menu_add_folder().

    Before creating a channel, playlist or folder, tidies up the name.

    Removes any leading/trailing whitespace. Reduces multiple whitespace
    characters to a single space character. Applies a maximum length.

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

        return string[0:max_length]

    else:

        # Empty string
        return string


def tidy_up_long_string(string, max_length=80, reduce_flag=True):

    """Called by mainwin.MainWin.errors_list_add_row() (or by anything else).

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

        reduce_flag (True, False): If True, initial and final whitespace is
            removed, and multiple successive whitespace characters are
            reduced to a single space character

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


def tidy_up_long_descrip(string, max_length=80):

    """Called by media.Video.set_video_descrip().

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


def to_string(data):

    """Based on the to_string() function in youtube-dl-gui. Now called by
    by options.OptionsParser.parse(), .build_file_sizes() and so on.

    Convert any data type to a string.

    Args:

        data (-): The data type

    Returns:

        The converted string

    """

    return '%s' % data


def upper_case_first(string):

    """Can be called by anything, but mainly used to capitalise
    __main__.__packagename__.

    Args:

        string (string): The string to capitalise

    Returns:

        The converted string

    """

    return string[0].upper() + string[1:]

