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
import locale
import math
import os
import re
import requests
import shutil
import subprocess
import sys
import textwrap


# Import our modules
import formats
import mainapp
import media


# Functions


def add_links_to_textview_from_clipboard(app_obj, textview, mark_start=None,
mark_end=None, drag_drop_text=None):

    """Called by mainwin.AddVideoDialogue.__init__(),
    .clipboard_timer_callback() and .on_window_drag_data_received().

    Function to add valid URLs from the clipboard to a Gtk.TextView, ignoring
    anything that is not a valid URL, and ignoring duplicate URLs.

    If some text is supplied as an argument, uses that text rather than the
    clipboard text

    Args:

        app_obj (mainapp.TartubeApp): The main application

        textview (Gtk.TextBuffer): The textview to which valis URLs should be
            added (unless they are duplicates)

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

    # Eliminate empty lines and any lines that are not valid URLs (we assume
    #   that it's one URL per line)
    # At the same time, trim initial/final whitespace
    valid_list = []
    if cliptext is not None and cliptext != Gdk.SELECTION_CLIPBOARD:
        for line in cliptext.split('\n'):
            if check_url(line):

                line = strip_whitespace(line)
                if re.search('\S', line):
                    valid_list.append(line)

    if valid_list:

        # Some URLs survived the cull

        # Get the contents of the buffer
        if mark_start is None or mark_end is None:

            # No Gtk.TextMarks supplied, we're forced to use iters
            buffer_text = textview.get_text(
                textview.get_start_iter(),
                textview.get_end_iter(),
                # Don't include hidden characters
                False,
            )

        else:

            buffer_text = textview.get_text(
                textview.get_iter_at_mark(mark_start),
                textview.get_iter_at_mark(mark_end),
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

            textview.insert(
                textview.get_end_iter(),
                str.join('\n', mod_list) + '\n',
            )


def add_links_to_entry_from_clipboard(app_obj, entry, duplicate_text=None,
drag_drop_text=None, no_modify_flag=None):

    """Called by mainwin.AddChannelDialogue.__init__() and
    .clipboard_timer_callback(), and the same functions in
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

    Return values:

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

        # (os.rename sometimes fails on external hard drives; this is safer)
        shutil.move(old_path, new_path)

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


def debug_time(msg):

    """Called by all functions in mainapp.py, mainwin.py and downloads.py (but
    only when debug flags are turned on).

    Writes the current time, and the name of the calling function to STDOUT,
    e.g. '2020-01-16 08:55:06 ap 91 __init__'.
    """

    # Uncomment this code to display the time with microseconds
#    print(str(datetime.datetime.now().time()) + ' ' + msg)

    # Uncomment this code to display the time without microseconds
    dt = datetime.datetime.now()
    print(str(dt.replace(microsecond=0)) + ' ' + msg)

    # Uncomment this code to display the message, without a timestamp
#    print(msg)


def disk_get_total_space(path, bytes_flag=False):

    """Called by anything.

    Returns the size of the disk on which a specified file/directory exists.

    Args:

        path (str): Path to a file/directory on the disk, typically Tartube's
            data directory

        bytes_flag (bool): True to return an integer value in MB, false to
            return a value in bytes

    Return values:

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

    """Called by anything.

    Returns the size of the disk on which a specified file/directory exists,
    minus the free space on that disk.

    Args:

        path (str): Path to a file/directory on the disk, typically Tartube's
            data directory

        bytes_flag (bool): True to return an integer value in MB, false to
            return a value in bytes

    Return values:

        The used space in MB (or in bytes, if the flag is specified)

    """

    total_bytes, used_bytes, free_bytes = shutil.disk_usage(
        os.path.realpath(path),
    )

    if not bytes_flag:
        return int(used_bytes / 1000000)
    else:
        return used_bytes


def disk_get_free_space(path, bytes_flag=False):

    """Called by anything.

    Returns the size of the disk on which a specified file/directory exists,
    minus the used space on that disk.

    Args:

        path (str): Path to a file/directory on the disk, typically Tartube's
            data directory

        bytes_flag (bool): True to return an integer value in MB, false to
            return a value in bytes

    Return values:

        The free space in MB (or in bytes, if the flag is specified)

    """

    total_bytes, used_bytes, free_bytes = shutil.disk_usage(
        os.path.realpath(path),
    )

    if not bytes_flag:
        return int(free_bytes / 1000000)
    else:
        return free_bytes


def find_available_name(app_obj, old_name, min_value=2, max_value=9999):

    """Can be called by anything.

    mainapp.TartubeApp.media_name_dict stores the names of all media.Channel,
    media.Playlist and media.Folder objects as keys.

    old_name is the name of an existing media data object. This function
    slightly modifies the name, converting 'my_name' into 'my_name_N', where N
    is the smallest positive integer for which the name is available.

    To preclude any possibility of infinite loops, the function will give up
    after max_value attempts.

    Args:

        app_obj (mainapp.TartubeApp): The main application

        old_name (str): The name which is already in use by a media data object

        min_value (str): The first name to try. 2 by default, so the first
            name checked will be 'my_name_2'

        max_value (int): When to give up. 9999 by default, meaning that this
            function will try everything up to 'my_name_9999' before giving up

    Return values:

        None on failure, the new name on success

    """

    for n in range (min_value, max_value):

        new_name = old_name + '_'  + str(n)
        if not new_name in app_obj.media_name_dict:
            return new_name

    # Failure
    return None


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
                app_obj.downloads_dir,
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


def generate_system_cmd(app_obj, media_data_obj, options_list,
dl_sim_flag=False):

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

    Returns:

        Python list that contains the system command to execute and its
            arguments

    """

    # Simulate the download, rather than actually downloading videos, if
    #   required
    if dl_sim_flag:
        options_list.append('--dump-json')

    # If actually downloading videos, create an archive file so that, if the
    #   user deletes the videos, youtube-dl won't try to download them again
    elif app_obj.allow_ytdl_archive_flag:

        # (Create the archive file in the media data object's own
        #   sub-directory, not the alternative download destination, as this
        #   helps youtube-dl to work the way we want it)
        if isinstance(media_data_obj, media.Video):
            dl_path = media_data_obj.parent_obj.get_dir(app_obj)
        else:
            dl_path = media_data_obj.get_dir(app_obj)

        options_list.append('--download-archive')
        options_list.append(
            os.path.abspath(os.path.join(dl_path, 'ytdl-archive.txt')),
        )

    # Show verbose output (youtube-dl debugging mode), if required
    if app_obj.ytdl_write_verbose_flag:
        options_list.append('--verbose')

    # Supply youtube-dl with the path to the ffmpeg/avconv binary, if the
    #   user has provided one
    if app_obj.ffmpeg_path is not None:
        options_list.append('--ffmpeg-location')
        options_list.append('"' + app_obj.ffmpeg_path + '"')

    # Set the list
    cmd_list = [app_obj.ytdl_path] + options_list + [media_data_obj.source]

    return cmd_list


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


def get_options_manager(app_obj, media_data_obj):

    """Can be called by anything, and is then called by this function
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


def tidy_up_long_descrip(string, max_length=80):

    """Called by media.Video.set_video_descrip(), and also used by
    .fetch_tooltip_text() functions in media.py.

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

