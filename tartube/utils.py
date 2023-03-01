#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2023 A S Lewis
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


"""Utility functions used by code copied from youtube-dl-gui."""


# Import Gtk modules
from gi.repository import Gtk, Gdk, GObject


# Import other modules
import datetime
import glob
import hashlib
import locale
import math
import os
import re
import requests
import shutil
import subprocess
import sys
import time
from urllib.parse import urlparse, urljoin


# Import our modules
import classes
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

    Return values:

        The URL added to the entry (or that would have been added to the entry)
            or None if no valid and non-duplicate URL was found in the
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

        drag_drop_text (str): If specified, use this text and ignore the
            clipboard

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


def check_day(this_day_num, target_day_str):

    """Can be called by anything.

    formats.SPECIFIED_DAYS_DICT contains a set of strings representing one or
    more days, e.g. 'every_day', 'monday'.

    Check whether one of those strings matches a particular day.

    Args:

        this_day_num (int): Number in the range 0 (Monday) to 6 (Sunday),
            usually representing today

        target_day_str (str): One of the strings in formats.SPECIFIED_DAYS_DICT

    Return values:

        True if 'this_day_num' matches 'target_day_str', False otherwise

    """

    if target_day_str != 'every_day':

        if (target_day_str == 'weekdays' and this_day_num > 4) \
        or (target_day_str == 'weekends' and this_day_num < 5) \
        or (target_day_str == 'monday' and this_day_num != 0) \
        or (target_day_str == 'tuesday' and this_day_num != 1) \
        or (target_day_str == 'wednesday' and this_day_num != 2) \
        or (target_day_str == 'thursday' and this_day_num != 3) \
        or (target_day_str == 'friday' and this_day_num != 4) \
        or (target_day_str == 'saturday' and this_day_num != 5) \
        or (target_day_str == 'sunday' and this_day_num != 6):
            return False

    return True


def check_url(url):

    """Can be called by anything.

    Checks for valid URLs.

    Args:

        url (str): The URL to check

    Return values:

        True if the URL is valid, False if invalid

    """

    url = strip_whitespace(url)

    # Based on various methods suggested by
    # https://stackoverflow.com/questions/25259134/
    #   how-can-i-check-whether-a-url-is-valid-using-urlparse

    try:
        # Add a scheme, if the specified URL doesn't provide one
        if not re.search(r'^[a-zA-Z]+://', url):
            url = 'http://' + url

        final_url = urlparse(urljoin(url, '/'))
        is_valid = (
            all([final_url.scheme, final_url.netloc, final_url.path])
            and len(final_url.netloc.split('.')) > 1
            and not re.search(r'\s', url)
        )

        return is_valid

    except:
        return False


def clip_add_to_db(app_obj, dest_obj, orig_video_obj, clip_title, \
clip_path=None):

    """Called by downloads.ClipDownloader.extract_stdout_data() and
    process.ProcessManager.run().

    Add the video clip to the Tartube database.

    Args:

        app_obj (mainapp.TartubeApp): The main application

        dest_obj (media.Folder): The folder object into which the new video
            object is to be created

        orig_video_obj (media.Video): The original video, from which the video
            clip has been split

        clip_title (str): The clip title for the new video, matching its
            filename

        clip_path (str): Full path to the clip, if known (if not known, we
            guess the path)

    Return values:

        The new media.Video object on success, or None of failure

    """

    new_video_obj = app_obj.add_video(
        dest_obj,
        None,                   # No source
        False,                  # Not a simulated download
        True,                   # Don't sort the container's child list yet
    )

    if not new_video_obj:

        return None

    else:

        source = orig_video_obj.source
        if source is None or source == '':
            source = _('No link')

        new_video_obj.set_name(clip_title)
        new_video_obj.set_nickname(clip_title)
        new_video_obj.set_video_descrip(
            app_obj,
            _('Split from original video') + ' (' \
            + str(orig_video_obj.dbid) + ')\n' + orig_video_obj.name \
            + '\n' + orig_video_obj.source,
            app_obj.main_win_obj.descrip_line_max_len,
        )

        if clip_path is not None:

            # Use the supplied path (when called by downloads.ClipDownloader)
            new_video_obj.set_file_from_path(clip_path)

        else:

            # Guess the path (when called by process.ProcessManager, it's safe
            #   to do that)
            new_video_obj.set_file(clip_title, orig_video_obj.file_ext)

        # Specifying the original video clones its .receive_time
        new_video_obj.set_receive_time(orig_video_obj)
        new_video_obj.set_upload_time(orig_video_obj.upload_time)

        # (The video length and file size is set elsewhere)

        # The video exists, so mark it as downloaded (even if only the original
        #   video was downloaded)
        app_obj.mark_video_downloaded(new_video_obj, True)

        # Copy the original video's thumbnail, if required
        if app_obj.split_video_copy_thumb_flag:

            thumb_path = find_thumbnail(app_obj, orig_video_obj)
            if thumb_path:

                new_video_path = new_video_obj.get_actual_path(app_obj)
                thumb_name, thumb_ext = os.path.splitext(thumb_path)
                video_name, video_ext = os.path.splitext(new_video_path)
                new_thumb_path = video_name + thumb_ext

                if not os.path.isfile(new_thumb_path):
                    try:
                        shutil.copyfile(thumb_path, new_thumb_path)
                    except:
                        pass

        # Clips split off from an original use a different icon
        new_video_obj.set_split_flag(True)

        # Now the video's properties are fully updated, the parent containers
        #   can be sorted
        dest_obj.sort_children(app_obj)
        app_obj.fixed_all_folder.sort_children(app_obj)

        # If the clips' parent media data object (a channel, playlist or
        #   folder) is selected in the Video Index, update the Video Catalogue
        #   for the clip
        GObject.timeout_add(
            0,
            app_obj.main_win_obj.video_catalogue_update_video,
            new_video_obj,
        )

        return new_video_obj


def clip_extract_data(stamp_list, clip_num):

    """Can be called by anything.

    media.Video.stamp_list stores details for video clips in groups of three,
    in the form
        [start_stamp, stop_stamp, clip_title]

    This function is called with a copy of media.Video.stamp_list (or some data
    in the same format), and the index of one of those groups, corresponding to
    a single video clip.

    If 'stop_stamp' is not specified, then 'start_stamp' of the following
    clip is used (unless that clip also starts at the same time, in which
    case we use the next clip that does not start at the same time).

    If there are no more clips, then this clip will end at the end of the
    video.

    Args:

        stamp_list (list): The copy of a media.Video's .stamp_list IV

        clip_num (int): The index of a group in stamp_list, the first clip is
            #0. It is the calling function's responsibility to ensure that
            clip_num is not outside the bounds of stamp_list

    Return values:

        Returns a list in the form

            start_stamp, stop_stamp, clip_title

        ...in which 'stop_stamp' might have been modified, as described
            above

    """

    list_size = len(stamp_list)
    mini_list = stamp_list[clip_num]

    start_stamp = mini_list[0]
    stop_stamp = mini_list[1]
    clip_title = mini_list[2]

    if stop_stamp is None and clip_num < (list_size - 1):

        for i in range((clip_num + 1), list_size):

            next_list = stamp_list[i]

            if next_list[0] != start_stamp:
                stop_stamp = next_list[0]
                break

    return start_stamp, stop_stamp, clip_title


def clip_prepare_title(app_obj, video_obj, clip_title_dict, clip_title,
clip_num, clip_max):

    """Called by downloads.ClipDownloader.do_download() and
    process.ProcessManager.run().

    Before creating a video clip, decide what its clip title should be.
    The title depends on various settings.

    Args:

        app_obj (mainapp.TartubeApp): The main application

        video_obj (media.Video): The video to be sent to FFmpeg

        clip_title_dict (dict): Dictionary of clip tiles used when splitting a
            video into clips), used to re-name duplicates

        clip_title (str): When splitting a video, the title of this video clip
            (if specified)

        clip_num (int): When splitting a video, the number of video clips split
            so far (including this one, so the first video clip is #1)

        clip_max (int): The number of clips to be split from this video in
            total

    Return values:

        The clip title

    """

    # If 'clip_title' is not specified, use a generic clip title
    # (The value is None only when not splitting a video)
    if clip_title is None or clip_title == '':
        clip_title = app_obj.split_video_custom_title

    # All clips from the same video should be formatted with a fixed number of
    #   digits (so any list of files will appear in the correct order)
    if clip_max > 99:
        clip_str = "{:03d}".format(clip_num)
    elif clip_max > 9:
        clip_str = "{:02d}".format(clip_num)
    else:
        clip_str = str(clip_num)

    # Set the video clip's filename, using the specified format
    # Note that dummy media.Video objects might not have a .file_name set
    #   (especially in an operation started in Classic Mode), so we have to
    #   take account of that
    if app_obj.split_video_name_mode == 'num':
        mod_title = clip_str
    elif app_obj.split_video_name_mode == 'clip':
        mod_title = clip_title
    elif app_obj.split_video_name_mode == 'num_clip':
        mod_title = clip_str + ' ' + clip_title
    elif app_obj.split_video_name_mode == 'clip_num':
        mod_title = clip_title + ' ' + clip_str

    elif app_obj.split_video_name_mode == 'orig':

        if video_obj.file_name is None:
            mod_title = app_obj.split_video_custom_title
        else:
            mod_title = video_obj.file_name

    elif app_obj.split_video_name_mode == 'orig_num':

        if video_obj.file_name is None:
            mod_title = clip_str
        else:
            mod_title = video_obj.file_name + ' ' + clip_str

    elif app_obj.split_video_name_mode == 'orig_clip':

        if video_obj.file_name is None:
            mod_title = clip_title
        else:
            mod_title = video_obj.file_name + ' ' + clip_title

    elif app_obj.split_video_name_mode == 'orig_num_clip':

        if video_obj.file_name is None:
            mod_title = clip_str + ' ' + clip_title
        else:
            mod_title = video_obj.file_name + ' ' + clip_str + ' ' + clip_title

    elif app_obj.split_video_name_mode == 'orig_clip_num':

        if video_obj.file_name is None:
            mod_title = clip_title + ' ' + clip_str
        else:
            mod_title = video_obj.file_name + ' ' + clip_title + ' ' + clip_str

    # Failsafe
    if mod_title is None:
        mod_title = clip_title

    # Ensure that we don't write multiple video clips with the same clip
    #   title (i.e. the same filename)
    count = 0
    this_title = mod_title

    if video_obj.dummy_flag:
        parent_dir = video_obj.dummy_dir
    else:
        parent_dir = video_obj.parent_obj.get_actual_dir(app_obj)

    if video_obj.file_ext is None:

        # (When launched from Classic Mode, we can't rely on the file name/
        #   extension being available; see the comments in
        #   mainapp.TartubeApp.download_manager_finished()
        this_path = os.path.abspath(
            os.path.join(
                parent_dir,
                this_title,
            ),
        )

    elif not app_obj.split_video_subdir_flag:

        this_path = os.path.abspath(
            os.path.join(
                parent_dir,
                this_title + video_obj.file_ext,
            ),
        )

    else:

        this_path = os.path.abspath(
            os.path.join(
                parent_dir,
                video_obj.file_name,
                this_title + video_obj.file_ext,
            ),
        )

    while 1:

        if not this_title in clip_title_dict and not os.path.isfile(this_path):

            return this_title

        else:

            # (Proceed to the next iteration of the loop, adding a number
            #   to the end of the clip title until we get a file path that
            #   hasn't already been written)
            count += 1
            this_title = mod_title + '_' + str(count)

            if video_obj.file_ext is None:

                this_path = os.path.abspath(
                    os.path.join(
                        parent_dir,
                        this_title,
                    ),
                )

            elif not app_obj.split_video_subdir_flag:

                this_path = os.path.abspath(
                    os.path.join(
                        parent_dir,
                        this_title + video_obj.file_ext,
                    ),
                )

            else:

                this_path = os.path.abspath(
                    os.path.join(
                        parent_dir,
                        video_obj.file_name,
                        this_title + video_obj.file_ext,
                    ),
                )


def clip_set_destination(app_obj, video_obj):

    """Called by downloads.ClipDownloader.do_download() and
    process.ProcessManager.run().

    Sets the media.Folder and/or the filestem folder in which the video clips
    will be created/downloaded.

    Args:

        app_obj (mainapp.TartubeApp): The main application

        video_obj (media.Video): The video object whose video files is to be
            split into clips

    Return values:

        A list in the form:

            (
                arent_folder_object, parent_directory,
                destination_folder_object, destination_directory
            )

        ...with all values set to None if there was an error

    """

    # parent_obj is either the Video Clips folder, or the original video's
    #   container (which might be a channel, playlist or folder)
    if app_obj.split_video_clips_dir_flag:
        parent_obj = app_obj.fixed_clips_folder
    else:
        parent_obj = video_obj.parent_obj

    parent_dir = parent_obj.get_actual_dir(app_obj)

    # Now set the actual directory into which the video clips are to be
    #   created/downloaded
    # Original and clip files in the same directory
    if not app_obj.split_video_subdir_flag:
        return parent_obj, parent_dir, parent_obj, parent_dir

    # Otherwise, video clips are in a sub-directory of 'parent_dir'
    if not isinstance(parent_obj, media.Folder) \
    or not app_obj.split_video_add_db_flag:

        # Cannot create a media.Folder inside a channel/playlist, so simply
        #   create a sub-directory in the filesystem. The video clips can be
        #   created there, but can't be added to the Tartube database
        dest_dir = os.path.abspath(
            os.path.join(
                parent_obj.get_actual_dir(app_obj),
                # Sub-directory is named after the video
                video_obj.file_name,
            ),
        )

        if not os.path.isdir(dest_dir):
            app_obj.make_directory(dest_dir)

        return parent_obj, parent_dir, None, dest_dir

    # Otherwise, we can create a media.Folder inside another media.Folder
    if video_obj.dbid in app_obj.container_reg_dict:

        # A media.Folder with the right name already exists
        dest_obj = app_obj.media_reg_dict[video_obj.dbid]

        if dest_obj.parent_obj != parent_obj:

            # There is already a media.Folder with the same name, somewhere
            #   else in the database. This is a fatal error
            return None, None, None, None

        else:

            # Use the existing media.Folder
            dest_dir = dest_obj.get_actual_dir(app_obj)

            return parent_obj, parent_dir, dest_obj, dest_dir

    # The media.Folder corresponding to the directory doesn't exist yet
    dest_obj = app_obj.add_folder(
        video_obj.name,             # The folder name
        parent_obj,
        False,                      # No simulated downloads
        parent_obj.restrict_mode,
    )

    if not dest_obj:

        # Some folders (e.g. Unsorted Videos) can't contain other folders
        return None, None, None, None

    else:

        dest_dir = dest_obj.get_actual_dir(app_obj)

        return parent_obj, parent_dir, dest_obj, dest_dir


def compile_mini_options_dict(options_manager_obj):

    """Called by downloads.VideoDownloader.confirm_new_video() and
    .confirm_old_video().

    Also called by downloads.StreamDownloader.do_download().

    Compiles a dictionary containing a subset of download options from the
    specified options.OptionsManager object, to be passed on to
    mainapp.TartubeApp.announce_video_download().

    Args:

        options_manager_obj (options.OptionsManager): The options manager
            for this download

    """

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


def convert_bytes_to_string(num_bytes):

    """Can be called by anything.

    Uses formats.FILESIZE_METRIC_DICT to convert an arbitrary integer, in
    bytes, into a readable string like '27.5 MiB'.

    Based on code from https://stackoverflow.com/questions/12523586/
    python-format-size-application-converting-b-to-kb-mb-gb-tb

    Args:

        num_bytes (int): An integer, 0 or above

    Return values:

        A string formatted to 1dp

    """

    # Don't want to return '0.0 B', this string looks a lot nicer
    if num_bytes == 0:
        return '0 KiB'

    unit_step = 1024
    unit_step_thresh = unit_step - 0.05
    last_label = formats.FILESIZE_METRIC_LIST[-1]

    for unit in formats.FILESIZE_METRIC_LIST:
        if num_bytes < unit_step_thresh:
            break
        if unit != last_label:
            num_bytes /= unit_step

    return '{:.1f} {}'.format(num_bytes, unit)


def convert_enhanced_template_from_json(convert_type, enhanced_name, \
json_dict):

    """Can be called by anything.

    Typically called by media.Channel.update_rss_from_json() and
    media.Playlist.update_rss_from_json().

    'convert_type' is one of the keys in formats.ENHANCED_SITE_DICT. Its
    corresponding value is a list of templates for a URL for a video, channel,
    playlist or RSS feed.

    The values in the list typically contain any of a set of four-letter
    strings (e.g. ' ci '), which can be substituted for values provided by a
    JSON dictionary, which was itself obtained from a video's metadata. See the
    comments in formats.py for the full set of four-letter strings.

    Args:

        convert_type (str): 'convert_video_list', 'convert_channel_list',
            'convert_playlist_list', 'rss_channel_list' or 'rss_playlist_list'

        enhanced_name (str): A key in formats.ENHANCED_SITE_DICT, representing
            a single website

        url (str): A URL from which video/channel/playlist names/IDs can be
            extracted

    Return values:

        Returns the first template whose four-letter strings have all been
            substituted out, or None if no such template is found

    """

    if not enhanced_name in formats.ENHANCED_SITE_DICT:
        return None

    mini_dict = formats.ENHANCED_SITE_DICT[enhanced_name]
    if not convert_type in mini_dict or not mini_dict[convert_type]:
        return None

    for template in mini_dict[convert_type]:

        if 'id' in json_dict \
        and json_dict['id'] \
        and template.find(' vi '):
            template = re.sub(' vi ', json_dict['id'], template)

        if 'title' in json_dict \
        and json_dict['title'] \
        and template.find(' vn '):
            template = re.sub(' vn ', json_dict['title'], template)

        if 'channel_id' in json_dict \
        and json_dict['channel_id'] \
        and template.find(' ci '):
            template = re.sub(' ci ', json_dict['channel_id'], template)

        if 'channel' in json_dict \
        and json_dict['channel'] \
        and template.find(' cn '):
            template = re.sub(' cn ', json_dict['channel'], template)
        # (BitChute doesn't provide a 'channel' in its JSON)
        elif enhanced_name == 'bitchute' \
        and 'uploader' in json_dict \
        and json_dict['uploader'] \
        and template.find(' cn '):
            template = re.sub(' cn ', json_dict['uploader'], template)

        if 'playlist_id' in json_dict \
        and json_dict['playlist_id'] \
        and template.find(' pi '):
            template = re.sub(' pi ', json_dict['playlist_id'], template)

        if 'playlist_title' in json_dict \
        and json_dict['playlist_title'] \
        and template.find(' pn '):
            template = re.sub(' pn ', json_dict['playlist_title'], template)

        if template.find(' ') == -1:
            return template

    return None


def convert_enhanced_template_from_url(convert_type, enhanced_name, url):

    """Can be called by anything.

    Typically called by media.Channel.update_rss_from_url() and
    media.Playlist.update_rss_from_url().

    'convert_type' is one of the keys in formats.ENHANCED_SITE_DICT. Its
    corresponding value is a list of templates for a URL for a video, channel,
    playlist or RSS feed.

    The values in the list typically contain any of a set of four-letter
    strings (e.g. ' ci '), which can be substituted for values extracted from
    the 'url' argument. See the comments in formats.py for the full set of
    four-letter strings.

    Args:

        convert_type (str): 'convert_video_list', 'convert_channel_list',
            'convert_playlist_list', 'rss_channel_list' or 'rss_playlist_list'

        enhanced_name (str): A key in formats.ENHANCED_SITE_DICT, representing
            a single website

        url (str): A URL from which video/channel/playlist names/IDs can be
            extracted

    Return values:

        Returns the first template whose four-letter strings have all been
            substituted out, or None if no such template is found

    """

    if not enhanced_name in formats.ENHANCED_SITE_DICT:
        return None

    mini_dict = formats.ENHANCED_SITE_DICT[enhanced_name]
    if not convert_type in mini_dict or not mini_dict[convert_type]:
        return None

    vid, vname, cid, cname, pid, pname = extract_enhanced_template_components(
        enhanced_name,
        url,
    )

    for template in mini_dict[convert_type]:

        if vid is not None and template.find(' vi '):
            template = re.sub(' vi ', vid, template)
        if vname is not None and template.find(' vn '):
            template = re.sub(' vn ', vname, template)
        if cid is not None and template.find(' ci '):
            template = re.sub(' ci ', cid, template)
        if cname is not None and template.find(' cn '):
            template = re.sub(' cn ', cname, template)
        if pid is not None and template.find(' pi '):
            template = re.sub(' pi ', pid, template)
        if pname is not None and template.find(' pn '):
            template = re.sub(' pn ', pname, template)

        if template.find(' ') == -1:
            return template

    return None


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

    Return values:

        Returns the converted full file path, or None if a filesystem error
            occurs

    """

    if old_path[0:len(app_obj.data_dir)] != app_obj.data_dir:

        # Special case: if 'old_path' is outside Tartube's data directory, then
        #   there is no equivalent path in the temporary directory
        # Instead. dump everything into ../tartube-data/.temp/.dump
        # There is a small risk of duplicates, but that shouldn't be anything
        #   more than an inconvenience
        old_dir, old_file = os.path.split(old_path)
        new_path = os.path.abspath(
            os.path.join(
                app_obj.temp_dir,
                '.dump',
                old_file,
            ),
        )

        new_dir, new_filename = os.path.split(new_path)

    else:

        # Normal conversion within Tartube's data directory
        data_dir_len = len(app_obj.downloads_dir)

        new_path = app_obj.temp_dl_dir + old_path[data_dir_len:]
        new_dir, new_filename = os.path.split(new_path.strip("\""))

    # The destination folder must exist, before moving files into it
    if not os.path.exists(new_dir):
        if not app_obj.make_directory(new_dir):
            return None

    # On MS Windows, a file name new_path must not exist, or an exception will
    #   be raised
    if os.path.isfile(new_path) \
    and not app_obj.remove_file(new_path):
        return None

    # Move the file now, if the calling code requires that
    if move_flag:

        rename_file(app_obj, old_path, new_path)

    # Return the converted file path
    return new_path


def convert_seconds_to_string(seconds, short_flag=False):

    """Can be called by anything.

    Converts a time in seconds into a formatted string.

    Args:

        seconds (int or float): The time to convert

        short_flag (bool): If True, show '05:15' rather than '0:05:15'

    Return values:

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


def convert_string_to_bytes(text):

    """Can be called by anything.

    The opposite of utils.convert_bytes_to_string(), converting a stringified
    value (e.g. '25.2KiB/s' or '25.2 KiB/s') into a value in bytes.

    Because of rounding errors (e.g. the value above has been rounded to 1
    decimal place), the value in bytes will only approximate the
    original argument passed to utils.convert_bytes_to_string().

    Args:

        text (str): The text to convert, the output of
            utils.convert_bytes_to_string()

    Return values:

        A value in bytes (or 0 on error)

    """

    # (From '25.2KiB/s', extract '25.2' and 'KiB')
    match = re.search('^([\d\.]+)\s*([\w]+)', text)
    if match:
        value = match.groups()[0]
        unit = match.groups()[1]
    else:
        return 0

    if unit in formats.FILESIZE_METRIC_DICT:
        return int(float(value) * formats.FILESIZE_METRIC_DICT[unit])
    else:
        return 0


def convert_slices_to_clips(app_obj, custom_dl_obj, slice_list, temp_flag):

    """Called by downloads.ClipDownloader.do_download_remove_slices() and
    process.ProcessManager.slice_video().

    Convert a list of video slices to be removed from a video into a list of
    video clips to be retained.

    'slice_list' is a list of dictionaries, one per slice, in the form
        mini_dict['category'] = One of the values in
            formats.SPONSORBLOCK_CATEGORY_LIST (e.g. 'sponsor')
        mini_dict['action'] = One of the values in
            formats.SPONSORBLOCK_ACTION_LIST (e.g. 'skip')
        mini_dict['start_time']
        mini_dict['stop_time'] = Floating point values in seconds, the
            beginning and end of the slice
        mini_dict['duration'] = The video duration, as reported by
            SponsorBlock. This valus is not required by Tartube code, and its
            default value is 0

    The returned list is in groups of two, in the form
        [start_time, stop_time]
    ...where 'start_time' and 'stop_time' are floating-point values in
    seconds. 'stop_time' can be None to signify the end of the video, but
    'start_time' is 0 to signify the start of the video.

    Args:

        app_obj (mainapp.TartubeApp): The main application

        custom_dl_obj (downloads.CustomDLManager or None): The custom download
            manager that applies. If not specified, all slices must be removed

        slice_list (list): The list of slices to be removed, in the form
            described above

        temp_flag (bool): If True, the user specified slices in
            mainwin.on_video_catalogue_process_slice(), so regardless of
            the contents of downloads.CustomDLManager.slice_dict, all slices
            must be removed

    Return values:

        The converted list described above

    """

    clip_list = []
    count = 0
    # (The first clip starts at the beginning of the video)
    previous_time = 0

    for mini_dict in slice_list:

        # (Only remove video slices which the user has opted to remove)
        if temp_flag \
        or custom_dl_obj is None \
        or custom_dl_obj.slice_dict[mini_dict['category']]:

            # (If the video starts with a removable slice, then the first
            #   clip will start after the slice)
            if mini_dict['start_time'] != 0 \
            and mini_dict['start_time'] != '0':

                # Remove this slice
                count += 1

                # This clip start at the end of the previous slice. and
                #   ends at the start of this slice
                clip_list.append([
                    previous_time,
                    mini_dict['start_time'],
                ])

            # Next clip starts at the end of this slice
            if mini_dict['stop_time'] is not None:
                previous_time = mini_dict['stop_time']
            else:
                # This clip ends at the end of the video; ignore any additional
                #   data in slice_list
                return clip_list

    if previous_time != 0 and previous_time != '0':

        # (The last clip starts at the end of the last removable slice, and
        #   ends at the end of the video)
        clip_list.append([ previous_time, None ])

    return clip_list


def convert_youtube_to_hooktube(url):

    """Can be called by anything.

    Converts a YouTube weblink to a HookTube weblink (but doesn't modify links
    to other sites.

    Args:

        url (str): The weblink to convert

    Return values:

        The converted string

    """

    if re.search(r'^https?:\/\/(www\.)+youtube\.com', url):

        url = re.sub(
            r'(www\.)+youtube\.com',
            'hooktube.com',
            url,
            # Substitute first occurrence only
            1,
        )

    return url


def convert_youtube_to_invidious(app_obj, url):

    """Can be called by anything.

    Converts a YouTube weblink to an Invidious weblink (but doesn't modify
    links to other sites).

    Args:

        url (str): The weblink to convert

    Return values:

        The converted string

    """

    if re.search(r'^https?:\/\/(www\.)+youtube\.com', url) \
    and re.search('\w+\.\w+', app_obj.custom_invidious_mirror):

        url = re.sub(
            r'(www\.)+youtube\.com',
            app_obj.custom_invidious_mirror,
            url,
            # Substitute first occurrence only
            1,
        )

    return url


def convert_youtube_to_other(app_obj, url, custom_dl_obj=None):

    """Can be called by anything.

    Converts a YouTube weblink to a weblink pointing at an alternative
    YouTube front-end (such as Hooktube or Invidious).

    Args:

        app_obj (mainapp.TartubeApp): The main application

        url (str): The weblink to convert

        custom_dl_obj (downloads.CustomDLManager or None): The custom download
            manager that provides the alternative front-end. If not specified,
            the General Custom Download Manager is used

    Return values:

        The converted string

    """

    if custom_dl_obj is None:
        custom_dl_obj = app_obj.general_custom_dl_obj

    if re.search(r'^https?:\/\/(www\.)+youtube\.com', url):

        url = re.sub(
            r'(www\.)+youtube\.com',
            custom_dl_obj.divert_website,
            url,
            # Substitute first occurrence only
            1,
        )

    return url


def disk_get_free_space(path, bytes_flag=False):

    """Can be called by anything.

    Returns the size of the disk on which a specified file/directory exists,
    minus the used space on that disk.

    Args:

        path (str): Path to a file/directory on the disk, typically Tartube's
            data directory

        bytes_flag (bool): False to return an integer value in GB (reduced to
            3 decimal places), True to return a value in bytes

    Return values:

        The free space in GB (or in bytes, if the flag is specified), or 0 if
            the size can't be calculated for any reason

    """

    try:
        total_bytes, used_bytes, free_bytes = shutil.disk_usage(
            os.path.realpath(path),
        )

        if not bytes_flag:
            return round( (free_bytes / 1000000000), 3)
        else:
            return free_bytes

    except:
        return 0


def disk_get_total_space(path=None, bytes_flag=False):

    """Can be called by anything.

    Returns the size of the disk on which a specified file/directory exists.

    Args:

        path (str): Path to a file/directory on the disk, typically Tartube's
            data directory

        bytes_flag (bool): False to return an integer value in GB (reduced to
            3 decimal places), True to return a value in bytes

    Return values:

        The total size in GB (or in bytes, if the flag is specified). If no
            path or an invalid path is specified, returns 0

    """

    if path is None \
    or (
        not os.path.isdir(path) and not os.path.isfile(path)
    ):
        return 0

    else:

        total_bytes, used_bytes, free_bytes = shutil.disk_usage(
            os.path.realpath(path),
        )

        if not bytes_flag:
            return round( (total_bytes / 1000000000), 3)
        else:
            return total_bytes


def disk_get_used_space(path=None, bytes_flag=False):

    """Can be called by anything.

    Returns the size of the disk on which a specified file/directory exists,
    minus the free space on that disk.

    Args:

        path (str): Path to a file/directory on the disk, typically Tartube's
            data directory

        bytes_flag (bool): False to return an integer value in GB (reduced to
            3 decimal places), True to return a value in bytes

    Return values:

        The used space in GB (or in bytes, if the flag is specified). If no
            path or an invalid path is specified, returns 0

    """

    if path is None \
    or (
        not os.path.isdir(path) and not os.path.isfile(path)
    ):
        return 0

    else:

        total_bytes, used_bytes, free_bytes = shutil.disk_usage(
            os.path.realpath(path),
        )

        if not bytes_flag:
            return round( (used_bytes / 1000000000), 3)
        else:
            return used_bytes


def extract_dummy_format(format_str):

    """Called by options.OptionsParser.build_video_format() and
    downloads.StreamDownloader.choose_path().

    A media.Video's .dummy_format IV is made up of three optional components
    in a fixed order.

    Extract those components, and return them as a list.

    Args:

        format_str (str): The value of media.Video.dummy_format. The calling
            code should have checked that the value is not None

    Return values:

        A list in the form (convert_flag, format, resolution), with any
            unspecified values returned as None

    """

    convert_flag = False
    this_format = None
    this_res = None

    split_list = format_str.split('_')
    if split_list and split_list[0] == 'convert':
        split_list.pop(0)
        convert_flag = True

    if split_list \
    and (
        split_list[0] in formats.VIDEO_FORMAT_LIST \
        or split_list[0] in formats.AUDIO_FORMAT_LIST
    ):
        this_format = split_list.pop(0)

    if split_list \
    and split_list[0] in formats.VIDEO_RESOLUTION_LIST:
        this_res = formats.VIDEO_RESOLUTION_DICT[split_list.pop(0)]

    return [ convert_flag, this_format, this_res ]


def extract_enhanced_template_components(enhanced_name, url):

    """Can be called by anything.

    Typically called by utils.convert_enhanced_template_from_url().

    formats.ENHANCED_SITE_DICT provides a set of regexes which can be used to
    extract video/channel/playlist names and IDs from a recognised URL.

    Extracts the names and IDs, returning them as a list.

    Args:

        enhanced_name (str): A key in formats.ENHANCED_SITE_DICT, representing
            a single website

        url (str): A URL from which video/channel/playlist names/IDs can be
            extracted

    Return values:

        A list in the form (vid, vname, cid, cname, pid, pname), any or all of
            which may be None

    """

    if not enhanced_name in formats.ENHANCED_SITE_DICT:
        return None

    mini_dict = formats.ENHANCED_SITE_DICT[enhanced_name]

    vid = None
    for regex in mini_dict['extract_vid_list']:
        match = re.search(regex, url)
        if match:
            # The first group is the optional 'www.' component; we are looking
            #   for the second group
            vid = match.groups()[1]

    vname = None
    for regex in mini_dict['extract_vname_list']:
        match = re.search(regex, url)
        if match:
            vname = match.groups()[1]

    cid = None
    for regex in mini_dict['extract_cid_list']:
        match = re.search(regex, url)
        if match:
            cid = match.groups()[1]

    cname = None
    for regex in mini_dict['extract_cname_list']:
        match = re.search(regex, url)
        if match:
            cname = match.groups()[1]

    pid = None
    for regex in mini_dict['extract_pid_list']:
        match = re.search(regex, url)
        if match:
            pid = match.groups()[1]

    pname = None
    for regex in mini_dict['extract_pname_list']:
        match = re.search(regex, url)
        if match:
            pname = match.groups()[1]

    return vid, vname, cid, cname, pid, pname


def extract_livestream_data(stderr):

    """Called by downloads.JSONFetcher.do_fetch() and
    MiniJSONFetcher.do_fetch().

    Also called by downloads.VideoDownloader.register_error_warning().

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


def extract_path_components(path):

    """Can be called by anything.

    Based on the extract_data() function in youtube-dl-gui's downloaders.py.

    Given a full path to a file, extracts the directory, filename and file
    extension, returning them as a list.

    Args:

        path (str): Full path to a file

    Return values:

        A list if the form (directory, filename, extension)

    """

    directory, fullname = os.path.split(path)
    filename, extension = os.path.splitext(fullname)

    return directory, filename, extension


def fetch_slice_data(app_obj, video_obj, page_num=None, terminal_flag=False):

    """Called by functions in downloads.VideoDownloader,
    downloads.ClipDownloader and process.ProcessManager.

    Contacts the SponsorBlock API server to retrieve video slice data for the
    speciffied video.

    Args:

        app_obj (mainapp.TartubeApp): The main application

        video_obj (media.Video): The video for which SponsorBlock data should
            should be retrieved. The calling code must check that its
            .vid is set

        page_num (int or None): The page number of the Output tab where output
            can be displayed. If None, then no output is displayed in the
            Output tab at all; otherwise, output is displayed (or not)
            depending on the usual Tartube settings

        terminal_flag (bool): If False, then no output is displayed in the
            terminal at all; otherwise, output is displayed (or not) depending
            on the usual Tartube settings

    """

    if not app_obj.sblock_obfuscate_flag:

        # Don't hash the video's ID
        url = 'https://' + app_obj.custom_sblock_mirror + '/skipSegments/'
        payload = { 'videoID': video_obj.vid }

    else:

        # Hash the video's ID
        vid = video_obj.vid
        hashed = hashlib.sha256(vid.encode())
        hex_str = hashed.hexdigest()

        short_str = hex_str[0:4]

        url = 'https://' + app_obj.custom_sblock_mirror + '/skipSegments/' \
        + short_str
        payload = {}

    # Write to the Output tab and/or terminal, if required
    msg = '[SponsorBlock] Contacting ' + url + '...'
    if page_num is not None and app_obj.ytdl_output_stdout_flag:
        app_obj.main_win_obj.output_tab_write_stdout(page_num, msg)
    if terminal_flag and app_obj.ytdl_write_stdout_flag:
        print(msg)

    # Contact the server
    try:
        request_obj = requests.get(
            url,
            params = payload,
            timeout = app_obj.request_get_timeout,
        )

    except:

        msg = '[SponsorBlock] Could not contact server'
        if page_num is not None and app_obj.ytdl_output_stderr_flag:
            app_obj.main_win_obj.output_tab_write_stderr(page_num, msg)
        if terminal_flag and app_obj.ytdl_write_stderr_flag:
            print(msg)

        return

    # 400 = bad request, 404 = not found
    if request_obj.status_code == 400:

        msg = '[SponsorBlock] Server returned error 400: bad request'
        if page_num is not None and app_obj.ytdl_output_stderr_flag:
            app_obj.main_win_obj.output_tab_write_stderr(page_num, msg)
        if terminal_flag and app_obj.ytdl_write_stderr_flag:
            print(msg)

        return

    elif request_obj.status_code == 404:

        msg = '[SponsorBlock] Server returned error 404: video ID not found'
        if page_num is not None and app_obj.ytdl_output_stderr_flag:
            app_obj.main_win_obj.output_tab_write_stderr(page_num, msg)
        if terminal_flag and app_obj.ytdl_write_stderr_flag:
            print(msg)

        return

    # (Conversion to JSON might produce an exception)
    try:
        json_table = request_obj.json()

    except:

        msg = '[SponsorBlock] Server returned invalid data'
        if page_num is not None and app_obj.ytdl_output_stderr_flag:
            app_obj.main_win_obj.output_tab_write_stderr(page_num, msg)
        if terminal_flag and app_obj.ytdl_write_stderr_flag:
            print(msg)

        return

    # Only use the data matching the video (since the video ID may have
    #   been obfuscated just above)
    for mini_dict in json_table:

        if not 'videoID' in mini_dict or not 'segments' in mini_dict:

            msg = '[SponsorBlock] Server returned invalid data'
            if page_num is not None and app_obj.ytdl_output_stderr_flag:
                app_obj.main_win_obj.output_tab_write_stderr(page_num, msg)
            if terminal_flag and app_obj.ytdl_write_stderr_flag:
                print(msg)

            return

        elif mini_dict['videoID'] == video_obj.vid:

            video_obj.convert_slices(mini_dict['segments'])

            if page_num is not None:

                msg = '[SponsorBlock] Video slices retrieved: ' \
                + str(len(video_obj.slice_list))

                if page_num is not None and app_obj.ytdl_output_stdout_flag:
                    app_obj.main_win_obj.output_tab_write_stdout(
                        page_num,
                        msg,
                    )

                if terminal_flag and app_obj.ytdl_write_stdout_flag:
                    print(msg)

            return


def find_available_name(app_obj, old_name, min_value=2, max_value=9999):

    """Can be called by anything.

    Finds a new name for a media.Channel, media.Playlist or media.Folder object
    which is currently named 'old_name'.

    This function slightly modifies the name, converting 'my_name' into
    'my_name_N', where N is the smallest positive integer for which the name is
    available.

    For this function, 'available' means that the name is not illegal (see the
    comments in mainapp.TartubeApp.__init__() for a definition of illegal),
    and is not in use by any other channel, playlist or folder (anywhere in
    the database).

    If the specified 'old_name' is already in a format like 'Channel_4', then
    the old number is stripped away, and this function starts looking from the
    first integer after that (for example, 'Channel_5').

    To preclude any possibility of infinite loops, the function will give up
    after 'max_value' attempts.

    Args:

        app_obj (mainapp.TartubeApp): The main application

        old_name (str): The name which is already in use by a media data object

        min_value (str): The first name to try. 2 by default, so the first
            name checked will be 'my_name_2'

        max_value (int): When to give up. 9999 by default, meaning that this
            function will try everything up to 'my_name_9999' before giving up.
            If set to -1, this function never gives up

    Return values:

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

    # Compile a dictionary of unavailable names
    check_dict = {}
    for this_obj in app_obj.container_reg_dict.values():
        check_dict[this_obj.name] = None

    # Find an available name
    if max_value != -1:

        for n in range (min_value, max_value):

            new_name = old_name + '_'  + str(n)
            if not new_name in check_dict:
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
            if not new_name in check_dict:
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

    Return values:

        The full path to the thumbnail file, or None

    """

    if video_obj.dummy_flag:

        # Special case: 'dummy' video objects (those downloaded in the Classic
        #   Mode tab) use different IVs
        if video_obj.dummy_path is None:
            return None

        file_name, file_ext = os.path.splitext(video_obj.dummy_path)
        for this_ext in formats.IMAGE_FORMAT_EXT_LIST:

            thumb_path = file_name + this_ext
            if os.path.isfile(thumb_path):
                return thumb_path

        # No matching thumbnail found
        return None

    else:

        # All other media.Video objects
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


def find_thumbnail_from_filename(app_obj, dir_path, filename):

    """Can be called by anything.

    A modified version of utils.find_thumbnail(), used when there is no
    media.Video object, but instead the directory and filename for a video
    (and its thumbnail).

    No way to know which image format is used by all websites for their video
    thumbnails, so look for the most common ones, and return the path to the
    thumbnail file if one is found.

    Args:

        app_obj (mainapp.TartubeApp): The main application

        dir_path (str): The full path to the directory in which the video is
            saved, e.g. '/home/yourname/tartube/downloads/Videos'

        filename (str): The video's filename, e.g. 'My Video'

    Return values:

        The full path to the thumbnail file, or None

    """

    for this_ext in formats.IMAGE_FORMAT_EXT_LIST:

        thumb_path = os.path.abspath(
            os.path.join(dir_path, filename + this_ext),
        )

        if os.path.isfile(thumb_path):
            return thumb_path

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

    Return values:

        A list whose items, when combined, will be the full path to the
            thumbnail file. If no thumbnail file was found, an empty list is
            returned

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


def find_thumbnail_webp_intact_or_broken(app_obj, video_obj):

    """Can be called by anything.

    In June 2020, YouTube started serving .webp thumbnails. Gtk cannot display
    them, so Tartube typically converts themto .jpg.

    This is a modified version of utils.find_thumbnail(), which looks for
    thumbnails in the .webp or malformed .jpg format, and return the path to
    the thumbnail file if one is found.

    Args:

        app_obj (mainapp.TartubeApp): The main application

        video_obj (media.Video): The video object handling the downloaded video

    Return values:

        The full path to the thumbnail file, or None

    """

    for ext in ('.webp', '.jpg'):

        main_path = video_obj.get_actual_path_by_ext(app_obj, ext)
        if os.path.isfile(main_path) \
        and (
            app_obj.ffmpeg_manager_obj.is_webp(main_path) \
            or app_obj.ffmpeg_manager_obj.is_mislabelled_webp(main_path)
        ):
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
        and (
            app_obj.ffmpeg_manager_obj.is_webp(subdir_path) \
            or app_obj.ffmpeg_manager_obj.is_mislabelled_webp(subdir_path)
        ):
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


def find_thumbnail_webp_strict(app_obj, video_obj):

    """Can be called by anything.

    A modified version of utils.find_thumbnail_webp_intact_or_broken(), to be
    called by any code which wants a path to a .webp thumbnail, not caring
    whether it is a valid .webp image or not.

    Args:

        app_obj (mainapp.TartubeApp): The main application

        video_obj (media.Video): The video object handling the downloaded video

    Return values:

        The full path to the thumbnail file, or None

    """

    ext = '.webp'

    main_path = video_obj.get_actual_path_by_ext(app_obj, ext)
    if os.path.isfile(main_path):
        return main_path

    subdir_path = video_obj.get_actual_path_in_subdirectory_by_ext(
        app_obj,
        ext,
    )
    if os.path.isfile(subdir_path):
        return subdir_path

    # No webp thumbnail found
    return None


def generate_ytdl_system_cmd(app_obj, media_data_obj, options_list,
dl_sim_flag=False, dl_classic_flag=False, missing_video_check_flag=None,
custom_dl_obj=None, divert_mode=None):

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
            from the Classic Mode tab, False otherwise

        missing_video_check_flag (bool): True if the download operation is
            trying to detect missing videos (downloaded by user, but since
            removed by the creator), False otherwise

        custom_dl_obj (downloads.CustomDLManager or None): The custom download
            manager that applies, if any

        divert_mode (str): If not None, should be one of the values of
            downloads.CustomDLManager.divert_mode: 'default', 'hooktube',
            'invidious' or 'other'. If not 'default', a media.Video object
            whose source URL points to YouTube should be converted to the
            specified alternative YouTube front-end (no conversion takes place
            for channels/playlists/folders)

    Return values:

        A list that contains the system command to execute and its arguments

    """

    # Simulate the download, rather than actually downloading videos, if
    #   required
    if dl_sim_flag:
        options_list.append('--dump-json')

    # If actually downloading videos, use (or create) an archive file so that,
    #   if the user deletes the videos, youtube-dl won't try to download them
    #   again
    # We don't use an archive file when downloading into a system folder,
    #   unless a non-default location for the file has been specified
    if (
        (not dl_classic_flag and app_obj.allow_ytdl_archive_flag) \
        or (dl_classic_flag and app_obj.classic_ytdl_archive_flag)
    ):
        if not dl_classic_flag \
        and (
            not isinstance(media_data_obj, media.Folder)
            or not media_data_obj.fixed_flag
            or app_obj.allow_ytdl_archive_mode != 'default'
        ) and (
            not isinstance(media_data_obj, media.Video)
            or not isinstance(media_data_obj.parent_obj, media.Folder)
            or not media_data_obj.parent_obj.fixed_flag
            or app_obj.allow_ytdl_archive_mode != 'default'
        ):
            # (Create the archive file in the media data object's default
            #   sub-directory, not the alternative download destination, as
            #   this helps youtube-dl to work the way we want it to work)
            if isinstance(media_data_obj, media.Video):
                dl_path = media_data_obj.parent_obj.get_default_dir(app_obj)
            else:
                dl_path = media_data_obj.get_default_dir(app_obj)

            if app_obj.allow_ytdl_archive_mode == 'top':
                archive_dir = app_obj.data_dir
            elif app_obj.allow_ytdl_archive_mode == 'custom':
                if app_obj.allow_ytdl_archive_path is not None \
                and app_obj.allow_ytdl_archive_path != '':
                    archive_dir = app_obj.allow_ytdl_archive_path
                else:
                    # Failsafe
                    archive_dir = dl_path
            else:
                # app_obj.allow_ytdl_archive_mode == 'default'
                archive_dir = dl_path

            options_list.append('--download-archive')
            options_list.append(
                os.path.abspath(
                    os.path.join(archive_dir, app_obj.ytdl_archive_name),
                ),
            )

        elif dl_classic_flag:

            # Create the archive file in destination directory
            dl_path = media_data_obj.dummy_dir

            options_list.append('--download-archive')
            options_list.append(
                os.path.abspath(
                    os.path.join(dl_path, app_obj.ytdl_archive_name),
                ),
            )

    # yt-dlp options
    if app_obj.ytdl_fork is not None and app_obj.ytdl_fork == 'yt-dlp':

        # Fetch video comments, if required
        if (dl_sim_flag and app_obj.check_comment_fetch_flag) \
        or (not dl_sim_flag and app_obj.dl_comment_fetch_flag):
            options_list.append('--write-comments')

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
        and custom_dl_obj.divert_website is not None \
        and len(custom_dl_obj.divert_website) > 2:
            source = convert_youtube_to_other(app_obj, source, custom_dl_obj)

    # Convert a downloader path beginning with ~ (not on MS Windows)
    ytdl_path = app_obj.check_downloader(app_obj.ytdl_path)
    if os.name != 'nt':
        ytdl_path = re.sub('^\~', os.path.expanduser('~'), ytdl_path)

    # Set the list. At the moment, a custom path must be preceded by 'python3'
    #   (Git #243), except on MS Windows when the custom path points at an .exe
    #   (Git #299)
    if app_obj.ytdl_path_custom_flag \
    and (os.name != 'nt' or not re.search('\.exe$', ytdl_path)):
        cmd_list = ['python3'] + [ytdl_path] + options_list + [source]
    else:
        cmd_list = [ytdl_path] + options_list + [source]

    return cmd_list


def generate_direct_system_cmd(app_obj, media_data_obj, options_obj):

    """Called by downloads.VideoDownloader.do_download() (only).

    A simplified version of utils.generate_ytdl_system_cmd().

    Prepare the system command that instructs youtube-dl to download the
    specified media data object, when the options.OptionsManager object wants
    to set most command line options directly (i.e. when the 'direct_cmd_flag'
    option is True).

    Args:

        app_obj (mainapp.TartubeApp): The main application

        media_data_obj (media.Video, media.Channel, media.Playlist,
            media.Folder): The media data object to be downloaded. Note that
            its source URL might be overriden by the command line options
            specified by the options.OptionsManager object

        options_obj (options.OptionsManager): The options manager object itself

    Return values:

        A list that contains the system command to execute and its arguments

    """

    # Convert a downloader path beginning with ~ (not on MS Windows)
    ytdl_path = app_obj.check_downloader(app_obj.ytdl_path)
    if os.name != 'nt':
        ytdl_path = re.sub('^\~', os.path.expanduser('~'), ytdl_path)

    # Parse the command line options specified by the 'extra_cmd_string' option
    #   (converting a string into a list of elements separated by whitespace)
    options_list = parse_options(options_obj.options_dict['extra_cmd_string'])

    # Set the list. At the moment, a custom path must be preceded by 'python3'
    #   (Git #243), except on MS Windows when the custom path points at an .exe
    #   (Git #299)
    if app_obj.ytdl_path_custom_flag \
    and (os.name != 'nt' or not re.search('\.exe$', ytdl_path)):
        cmd_list = ['python3'] + [ytdl_path] + options_list
    else:
        cmd_list = [ytdl_path] + options_list

    # Add the source URL, if allowed
    if not options_obj.options_dict['direct_url_flag'] \
    and media_data_obj.source is not None:
        cmd_list.append( [media_data_obj.source] )

    return cmd_list


def generate_slice_system_cmd(app_obj, orig_video_obj, options_list, \
temp_dir, clip_count, start_time, stop_time, custom_dl_obj, divert_mode, \
classic_flag):

    """Called by downloads.ClipDownloader.do_download_remove_slices() (only).

    A modified version of utils.generate_split_system_cmd().

    Prepares the system command that instructs youtube-dl to download a video
    clip (instead of downloading the whole video). The downloaded clips are
    expected to be concatenated together to make a single video.

    Args:

        app_obj (mainapp.TartubeApp): The main application

        orig_video_obj (media.Video): The video object for the video from which
            the clip is downloaded

        options_list (list): A list of download options generated by a call to
            options.OptionsParser.parse()

        temp_dir (str): The directory into which the clip will be downloaded;
            should be a temporary directory, which will be removed as soon as
            the clips have been concatenated together

        clip_count (int): The nnumber of clips created so far, including this
            one

        start_time (float): Time in seconds at which the clip starts

        stop_time (float): Time in seconds at which the clip stops. If not
            specified, then the stop point is the end of the video

        custom_dl_obj (downloads.CustomDLManager or None): The custom download
            manager that applies, if any

        divert_mode (str): If not None, should be one of the values of
            downloads.CustomDLManager.divert_mode: 'default', 'hooktube',
            'invidious' or 'other'. If not 'default', a media.Video object
            whose source URL points to YouTube should be converted to the
            specified alternative YouTube front-end (no conversion takes place
            for channels/playlists/folders)

        classic_flag (bool): Specifies the (standard) operation type. True for
            'classic_custom', False for 'custom_real'

    """

    # Filter out download options that get in the way. A list of them is
    #   specified in mainapp.TartubeApp.split_ignore_option_dict
    # Unlike the corresponding code in utils.generate_split_system_cmd(), we
    #   do write the metadata files (if required), but only for the first clip
    # Exception: if the parent container's .dl_no_db_flag is set, don't write
    #   the metadata files at all
    mod_options_list = []
    while options_list:

        item = options_list.pop(0)
        if item in app_obj.split_ignore_option_dict \
        and (
            orig_video_obj.parent_obj.dl_no_db_flag \
            or clip_count > 1 \
            or (
                item != '--write-description' \
                and item != '--write-info-json' \
                and item != '--write-annotations' \
                and item != '--write-thumbnail'
            )
        ):
            if app_obj.split_ignore_option_dict[item]:
                # This option takes an argument
                options_list.pop(0)

        else:
            mod_options_list.append(item)

    # Set the file format. If none is specified by download options, then use
    #   a default one
    # FFmpeg cannot split media in DASH formats, so we need to check for that
    # If --format is not specified but --extract_audio is specified, then don't
    #   insert a --format option at all
    format_match_flag = False
    audio_match_flag = False
    for i in range(0, len(mod_options_list)):

        if mod_options_list[i] == '-f' or mod_options_list[i] == '--format':

            mod_options_list[i+1] = '(' + mod_options_list[i + 1] \
            + ')[protocol!*=dash]'

            format_match_flag = True

        if mod_options_list[i] == '-x' \
        or mod_options_list[i] == '--extract-audio':

            audio_match_flag = True

    if not format_match_flag and not audio_match_flag:

        mod_options_list.append('-f')
        mod_options_list.append('(bestvideo+bestaudio/best)[protocol!*=dash]')

    # On MS Windows and yt-dlp, if --restrict-filenames is not specified, then
    #   insert --windows-filenames. (I can't be sure that yt-dlp knows it is
    #   running on MS Windows, when running inside MSYS2)
    if app_obj.ytdl_fork is not None \
    and app_obj.ytdl_fork == 'yt-dlp' \
    and os.name == 'nt' \
    and not '--restrict-filenames' in mod_options_list:
        mod_options_list.append('--windows-filenames')

    # Supply youtube-dl with the path to the ffmpeg binary, if the user has
    #   provided one
    if app_obj.ffmpeg_path is not None:
        mod_options_list.append('--ffmpeg-location')
        mod_options_list.append(app_obj.ffmpeg_path)

    # Specify the external downloader, and the timestamps for the clip
    slice_arg = '-ss ' + str(start_time)
    if stop_time is not None:
        slice_arg += ' -to ' + str(stop_time)

    mod_options_list.append('--external-downloader')
    mod_options_list.append('ffmpeg')
    mod_options_list.append('--external-downloader-args')
    mod_options_list.append(slice_arg)

    # Set the output template
    mod_options_list.append('-o')
    mod_options_list.append(
        os.path.abspath(
            os.path.join(temp_dir, 'clip_' + str(clip_count) + '.%(ext)s'),
        )
    )

    # Convert a YouTube URL to an alternative YouTube front-end, if required
    source = orig_video_obj.source
    if divert_mode is not None:
        if divert_mode == 'hooktube':
            source = convert_youtube_to_hooktube(source)
        elif divert_mode == 'invidious':
            source = convert_youtube_to_invidious(app_obj, source)
        elif divert_mode == 'custom' \
        and custom_dl_obj.divert_website is not None \
        and len(custom_dl_obj.divert_website) > 2:
            source = convert_youtube_to_other(app_obj, source, custom_dl_obj)

    # Convert a downloader path beginning with ~ (not on MS Windows)
    ytdl_path = app_obj.check_downloader(app_obj.ytdl_path)
    if os.name != 'nt':
        ytdl_path = re.sub('^\~', os.path.expanduser('~'), ytdl_path)

    # Set the list. At the moment, a custom path must be preceded by 'python3'
    #   (Git #243), except on MS Windows when the custom path points at an .exe
    #   (Git #299)
    if app_obj.ytdl_path_custom_flag \
    and (os.name != 'nt' or not re.search('\.exe$', ytdl_path)):
        cmd_list = ['python3'] + [ytdl_path] + mod_options_list + [source]
    else:
        cmd_list = [ytdl_path] + mod_options_list + [source]

    return cmd_list


def generate_split_system_cmd(app_obj, orig_video_obj, options_list, dest_dir,
clip_title, start_stamp, stop_stamp, custom_dl_obj, divert_mode, classic_flag):

    """Called by downloads.ClipDownloader.do_download() (only).

    A simplified version of utils.generate_ytdl_system_cmd().

    Prepares the system command that instructs youtube-dl to download a video
    clip (instead of downloading the whole video).

    Args:

        app_obj (mainapp.TartubeApp): The main application

        orig_video_obj (media.Video): The video object for the video from which
            the clip is downloaded

        options_list (list): A list of download options generated by a call to
            options.OptionsParser.parse()

        dest_dir (str): The directory into which the clip will be downloaded

        clip_title (str): The title of the clip (used as the clip's filename,
            so must not be None)

        start_stamp (str): Timestamp at which the clip starts (in a format
            recognised by FFmpeg)

        stop_stamp (str or None): Timestamp at which the clip stops. If not
            specified, then the stop point is the end of the video

        custom_dl_obj (downloads.CustomDLManager or None): The custom download
            manager that applies, if any

        divert_mode (str): If not None, should be one of the values of
            downloads.CustomDLManager.divert_mode: 'default', 'hooktube',
            'invidious' or 'other'. If not 'default', a media.Video object
            whose source URL points to YouTube should be converted to the
            specified alternative YouTube front-end (no conversion takes place
            for channels/playlists/folders)

        classic_flag (bool): Specifies the (standard) operation type. True for
            'classic_custom', False for 'custom_real'

    """

    # Filter out download options that get in the way. A list of them is
    #   specified in mainapp.TartubeApp.split_ignore_option_dict
    mod_options_list = []
    while options_list:

        item = options_list.pop(0)
        if item in app_obj.split_ignore_option_dict:

            if app_obj.split_ignore_option_dict[item]:
                # This option takes an argument
                options_list.pop(0)

        else:
            mod_options_list.append(item)

    # Set the file format. If none is specified by download options, then use
    #   a default one
    # FFmpeg cannot split media in DASH formats, so we need to check for that
    # If --format is not specified but --extract_audio is specified, then don't
    #   insert a --format option at all
    format_match_flag = False
    audio_match_flag = False
    for i in range(0, len(mod_options_list)):

        if mod_options_list[i] == '-f' or mod_options_list[i] == '--format':

            mod_options_list[i+1] = '(' + mod_options_list[i + 1] \
            + ')[protocol!*=dash]'

            format_match_flag = True

        if mod_options_list[i] == '-x' \
        or mod_options_list[i] == '--extract-audio':

            audio_match_flag = True

    if not format_match_flag and not audio_match_flag:

        mod_options_list.append('-f')
        mod_options_list.append('(bestvideo+bestaudio/best)[protocol!*=dash]')

    # On MS Windows and yt-dlp, if --restrict-filenames is not specified, then
    #   insert --windows-filenames. (I can't be sure that yt-dlp knows it is
    #   running on MS Windows, when running inside MSYS2)
    if app_obj.ytdl_fork is not None \
    and app_obj.ytdl_fork == 'yt-dlp' \
    and os.name == 'nt' \
    and not '--restrict-filenames' in mod_options_list:
        mod_options_list.append('--windows-filenames')

    # Supply youtube-dl with the path to the ffmpeg binary, if the user has
    #   provided one
    if app_obj.ffmpeg_path is not None:
        mod_options_list.append('--ffmpeg-location')
        mod_options_list.append(app_obj.ffmpeg_path)

    # Specify the external downloader, and the timestamps for the clip
    stamp_arg = '-ss ' + start_stamp
    if stop_stamp is not None:
        stamp_arg += ' -to ' + stop_stamp

    mod_options_list.append('--external-downloader')
    mod_options_list.append('ffmpeg')
    mod_options_list.append('--external-downloader-args')
    mod_options_list.append(stamp_arg)

    # Set the output template
    if not classic_flag:

        template = os.path.abspath(
            os.path.join(dest_dir, clip_title + '.%(ext)s'),
        )

    else:

        template = os.path.abspath(
            os.path.join(orig_video_obj.dummy_dir, clip_title + '.%(ext)s'),
        )

    mod_options_list.append('-o')
    mod_options_list.append(template)

    # Convert a YouTube URL to an alternative YouTube front-end, if required
    source = orig_video_obj.source
    if divert_mode is not None:
        if divert_mode == 'hooktube':
            source = convert_youtube_to_hooktube(source)
        elif divert_mode == 'invidious':
            source = convert_youtube_to_invidious(app_obj, source)
        elif divert_mode == 'custom' \
        and custom_dl_obj.divert_website is not None \
        and len(custom_dl_obj.divert_website) > 2:
            source = convert_youtube_to_other(app_obj, source, custom_dl_obj)

    # Convert a downloader path beginning with ~ (not on MS Windows)
    ytdl_path = app_obj.check_downloader(app_obj.ytdl_path)
    if os.name != 'nt':
        ytdl_path = re.sub('^\~', os.path.expanduser('~'), ytdl_path)

    # Set the list. At the moment, a custom path must be preceded by 'python3'
    #   (Git #243), except on MS Windows when the custom path points at an .exe
    #   (Git #299)
    if app_obj.ytdl_path_custom_flag \
    and (os.name != 'nt' or not re.search('\.exe$', ytdl_path)):
        cmd_list = ['python3'] + [ytdl_path] + mod_options_list + [source]
    else:
        cmd_list = [ytdl_path] + mod_options_list + [source]

    return cmd_list


def generate_m3u_system_cmd(app_obj, media_data_obj):

    """Called by downloads.StreamDownloader.do_download_m3u().

    Prepare the system command that instructs youtube-dl to download the
    .m3u manifest for the URL associated with the media data object.

    Args:

        app_obj (mainapp.TartubeApp): The main application

        media_data_obj (media.Video): The media data object whose .m3u manifest
            is to be downloaded

    Return values:

        A list that contains the system command to execute and its arguments

    """

    # Convert a downloader path beginning with ~ (not on MS Windows)
    ytdl_path = app_obj.check_downloader(app_obj.ytdl_path)
    if os.name != 'nt':
        ytdl_path = re.sub('^\~', os.path.expanduser('~'), ytdl_path)

    # Set the list. At the moment, a custom path must be preceded by 'python3'
    #   (Git #243), except on MS Windows when the custom path points at an .exe
    #   (Git #299)
    if app_obj.ytdl_path_custom_flag \
    and (os.name != 'nt' or not re.search('\.exe$', ytdl_path)):
        cmd_list = ['python3'] + [ytdl_path] + ['-g'] + [media_data_obj.source]
    else:
        cmd_list = [ytdl_path] + ['-g'] + [media_data_obj.source]

    return cmd_list


def generate_streamlink_system_cmd(app_obj, media_data_obj, path):

    """Called by downloads.StreamDownloader.do_download_streamlink().

    Prepare the system command that instructs streamlink to download the
    media.Video object.

    Args:

        app_obj (mainapp.TartubeApp): The main application

        media_data_obj (media.Video): The media data object whose URL is to be
            downloaded

        path (str): The full path to the output video

    Return values:

        A list that contains the system command to execute and its arguments

    """

    if app_obj.streamlink_path is None:
        # (Assume the binary is in the user's PATH)
        streamlink_path = 'streamlink'
    else:
        streamlink_path = app_obj.streamlink_path

    return [
        streamlink_path,
        '--hls-live-restart',
        '--force',          # Streamlink has no option to resume old stream
        '--stream-timeout',
        str(app_obj.livestream_dl_timeout * 60),
        '-o',
        path,
        media_data_obj.source,
        'best',
    ]


def get_encoding():

    """Called by utils.convert_item().

    Based on the get_encoding() function in youtube-dl-gui.

    Return values:

        The system encoding

    """

    try:
        encoding = locale.getpreferredencoding()
        'TEST'.encode(encoding)
    except:
        encoding = 'UTF-8'

    return encoding


def get_local_time():

    """Can be called by anything.

    Returns a datetime object that has been converted from UTC to the local
    time zone.

    Return values:

        A datetime.datetime object, configured to the local time zone

    """

    utc = datetime.datetime.utcfromtimestamp(time.time())
    return utc.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)


def get_dl_config_path(app_obj):

    """Can be called by anything.

    Returns the full path to the youtube-dl configuration file, in the location
    Tartube assuems it to be.

    Args:

        app_obj (mainapp.TartubeApp): The main application

    Return values:

        The full path

    """

    if app_obj.ytdl_fork is None:
        ytdl_fork = 'youtube-dl'
    else:
        ytdl_fork = app_obj.ytdl_fork

    if os.name != 'nt':

        return os.path.abspath(
            os.path.join(
                os.path.expanduser('~'),
                '.config',
                ytdl_fork,
                'config',
            ),
        )

    else:

        return os.path.abspath(
            os.path.join(
                app_obj.script_parent_dir,
                ytdl_fork + '.conf',
            ),
        )


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

    Return values:

        The options.OptionsManager object that applies to the specified media
            data object

    """

    if media_data_obj.options_obj:
        return media_data_obj.options_obj
    elif media_data_obj.parent_obj:
        return get_options_manager(app_obj, media_data_obj.parent_obj)
    else:
        return app_obj.general_options_obj


def handle_files_after_download(app_obj, options_obj, dir_path, filename,
dummy_obj=None):

    """Called by various functions in downloads.py, after a video is checked/
    downloaded but not added to Tartube's database.

    Handles the removal of the description, JSON and thumbnail files, according
    to the settings in the options.OptionsManager object.

    Args:

        app_obj (mainapp.TartubeApp): The main application

        options_obj (options.OptionsManager object): Specifies the download
            options for this download

        dir_path (str): The full path to the directory in which the video is
            saved, e.g. '/home/yourname/tartube/downloads/Videos'

        filename (str): The video's filename, e.g. 'My Video'

        dummy_obj (media.Video or None): If specified, a 'dummy' video used by
            the Classic Mode tab (and not added to Tartube's database)

    """

    # Description file
    descrip_path = os.path.abspath(
        os.path.join(dir_path, filename + '.description'),
    )

    if descrip_path and not options_obj.options_dict['keep_description']:

        new_path = convert_path_to_temp(
            app_obj,
            descrip_path,
        )

        if os.path.isfile(descrip_path):
            if not os.path.isfile(new_path):
                app_obj.move_file_or_directory(descrip_path, new_path)
            else:
                app_obj.remove_file(descrip_path)

    # (Don't replace a file that already exists)
    elif descrip_path \
    and not os.path.isfile(descrip_path) \
    and options_obj.options_dict['move_description'] \
    and dummy_obj:

        move_metadata_to_subdir(app_obj, dummy_obj, '.description')

    # JSON data file
    json_path = os.path.abspath(
        os.path.join(dir_path, filename + '.info.json'),
    )

    if json_path and not options_obj.options_dict['keep_info']:

        new_path = convert_path_to_temp(app_obj, json_path)

        if os.path.isfile(json_path):
            if not os.path.isfile(new_path):
                app_obj.move_file_or_directory(json_path, new_path)
            else:
                app_obj.remove_file(json_path)

    elif json_path \
    and not os.path.isfile(json_path) \
    and options_obj.options_dict['move_info'] \
    and dummy_obj:

        move_metadata_to_subdir(app_obj, dummy_obj, '.info.json')

    # (Annotations removed by YouTube in 2019 - see comments elsewhere)

    # Thumbnail file
    if dummy_obj:
        thumb_path = find_thumbnail(app_obj, dummy_obj)
    else:
        thumb_path = find_thumbnail_from_filename(app_obj, dir_path, filename)

    if thumb_path and not options_obj.options_dict['keep_thumbnail']:

        new_path = convert_path_to_temp(app_obj, thumb_path)

        if os.path.isfile(thumb_path):
            if not os.path.isfile(new_path):
                app_obj.move_file_or_directory(thumb_path, new_path)
            else:
                app_obj.remove_file(thumb_path)

    elif thumb_path \
    and not os.path.isfile(thumb_path) \
    and options_obj.options_dict['move_thumbnail'] \
    and dummy_obj:

        move_thumbnail_to_subdir(app_obj, dummy_obj)


def is_enhanced(url):

    """Can be called by anything, usually called by
    media.GenericRemoteContainer.set_source().

    Checks whether a URL matches one of the 'enhanced' websites specified by
    formats.ENHANCED_SITE_DICT.

    Args:

        url (str or None): The URL to check

    Return values:

        Returns a key in formats.ENHANCED_SITE_DICT or, if the URL does not
        match an 'enhanced' website, returns None. If no URL is specified,
        returns None

    """

    if url is None:
        return None

    for key in formats.ENHANCED_SITE_LIST:

        mini_dict = formats.ENHANCED_SITE_DICT[key]
        for regex in mini_dict['detect_list']:
            if re.search(regex, url):
                return mini_dict['name']

    return None


def is_video_enhanced(video_obj):

    """Can be called by anything.

    Checks whether a video's parent channel or playlist matches one of the
    'enhanced' websites specified by formats.ENHANCED_SITE_DICT.

    If the video's parent is a media.Folder, do the check on the video's own
    .source.

    Args:

        video_obj (media.Video): The media data object to check

    Return values:

        Returns a key in formats.ENHANCED_SITE_DICT or, if the video does not
        originate from an 'enhanced' website, returns None. If no URL is
        specified, returns None

    """

    if isinstance(video_obj.parent_obj, media.Folder):
        return is_enhanced(video_obj.source)
    else:
        return is_enhanced(video_obj.parent_obj.source)


def match_subs(custom_dl_obj, subs_list):

    """Called by downloads.DownloadList.create_item() and
    downloads.VideoDownloader.confirm_sim_video().

    The CustomDLManager object may specify one or more languages; compare
    that list to a video's list of available subtitles, to see if there are any
    matches.

    Args:

        custom_dl_obj (downloads.CustomDLManager): The custom download
            mager which specifies a list of languages

        subs_list (list): A list of language codes extracted from the video's
            metadata, one for each set of subtitles

    Return values:

        True if any language matches an available subtitle, False if none
            of them match

    """

    # 'short_code' is a value in formats.LANGUAGE_CODE_DICT, e.g. 'en',
    #   'live_chat'
    for short_code in custom_dl_obj.dl_if_subs_list:

        # media.VideoObj.subs_list contains the language code specified by
        #   the metadata file, e.g. 'en_US'. Ignore everything but the
        #   first two letters
        for long_code in subs_list:
            if long_code.lower().startswith(short_code):
                return True

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

    main_path = video_obj.get_actual_path_by_ext(app_obj, ext)
    subdir = os.path.abspath(
        os.path.join(
            video_obj.parent_obj.get_actual_dir(app_obj),
            app_obj.metadata_sub_dir,
        ),
    )

    subdir_path = video_obj.get_actual_path_in_subdirectory_by_ext(
        app_obj,
        ext,
    )

    if os.path.isfile(main_path) and not os.path.isfile(subdir_path):

        if not os.path.isdir(subdir):
            app_obj.make_directory(subdir)

        app_obj.move_file_or_directory(main_path, subdir_path)


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

            if not os.path.isdir(subdir):
                app_obj.make_directory(subdir)

            app_obj.move_file_or_directory(main_path, subdir_path)


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


def parse_options(text):

    """Called by options.OptionsParser.parse() or info.InfoManager.run().

    Also called by ffmpeg_tartube.FFmpegOptionsManager.get_system_cmd() to
    parse FFmpeg command-line options on the same basis.

    Parses a string containing one or more youtube-dl download options and
    their arguments (or the FFmpeg equivalent).

    Anything inside double quotes constitutes a single argument (which can
    therefore contain whitespace characters).

    If the string contains any newline characters, that characters terminates
    the argument, closing newline character or not.

    Args:

        text (str): The string to parse, e.g. '--do-something "foo bar baz"'

    Return values:

        A separated list of youtube-dl download options (or the FFmpeg
            equivalent)

    """

    # Add options, one at a time, to a list
    return_list = []

    for line in text.splitlines():

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
                return_list.append(' '.join(quote_list))

                quote_flag = False
                quote_list = []

    return return_list


def rename_file(app_obj, old_path, new_path):

    """Can be called by anything.

    Renames (mmoves) a file. (Is not usually called for directories, but could
    be.)

    Args:

        app_obj (mainapp.TartubeApp): The main application

        old_path (str): Full path to the file to be renamed

        new_path (str): Full path to the renamed file

    """

    try:

        # (On MSWin, can't do os.rename if the destination file already exists)
        if os.path.isfile(new_path):
            app_obj.remove_file(new_path)

        # (os.rename sometimes fails on external hard drives; this is safer)
        shutil.move(old_path, new_path)

    except:

        app_obj.system_error(
            503,
            'Could not rename \'' + str(old_path) + '\'',
        )


def shorten_string(string, num_chars):

    """Can be called by anything.

    If string is longer than num_chars, truncates it and adds an ellipsis.

    Args:

        string (string): The string to convert

        num_chars (int): The maximum length of the desired string

    Return values:

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

    Return values:

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
                # Exception: try to split URLs on the '/' character neareest
                #   to the end of the first 'num_chars' characters of 'word'
                shortended_word = word[0:num_chars]
                pos = shortended_word.rfind('/')
                if pos > -1:
                    pos += 1
                    line_list.append(word[0:pos])
                    line_list.append(word[pos:])

                else:

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


def stream_output_is_ignorable(stderr):

    """Called by downloads.StreamDownloader.read_child_process() and
    downloads.VideoDownloader.read_child_process()

    Special handling of messages received from STDERR during direct livestream
    downloads (i.e. youtube-dl without .m3u).

    From the text received, we strip out anything we don't want. The calling
    code will use the modified text (if any remains) in its STDOUT stream.

    Args:

        stderr (str): The text received from STDERR

    Return values:

        A modified stderr, or None if the whole text should be ignored

    """

    match = re.search('^(frame.*speed\=\s*[\S]+x)', stderr)
    if match:
        return match.groups()[0]

    # (All but the first two lines occur only near the beginning of the
    #   output)
    for regex in [
        '^\[hls\s\@\s\w+\]\s',
        '^\[https\s\@\s\w+\]\s',
        '^Input\s\#\d+,\s',
        '^Output\s\#\d+,\s',
        '^Stream mapping\:',
        '^Press \[q\] to stop,',
        '^[\s]{2}',
    ]:
        if re.search(regex, stderr):
            return None

    return stderr


def strip_double_quotes(input_list):

    """Can be called by anything. Mostly called by code that creates a child
    process to run a system command.

    Strips leading and trailing double quotes from every string in a list.

    Args:

        string_list (list): A list of strings to modify

    Return values:

        The modified list

    """

    return_list = []
    for item in input_list:
        return_list.append(item.strip('"'))

    return return_list


def strip_whitespace(string):

    """Can be called by anything.

    Removes any leading/trailing whitespace from a string.

    Args:

        string (str): The string to convert

    Return values:

        The converted string

    """

    if string is not None:
        string = string.strip()

    return string


def strip_whitespace_multiline(string):

    """Can be called by anything.

    An extended version of utils.strip_whitepspace.

    Divides a string into lines, removes empty lines, removes any leading/
    trailing whitespace from each line, then combines the lines back into a
    single string (with lines separated by newline characters).

    Args:

        string (str): The string to convert

    Return values:

        The converted string

    """

    line_list = string.splitlines()
    mod_list = []

    for line in line_list:
        line = line.strip()

        if re.search('\S', line):
            mod_list.append(line)

    return "\n".join(mod_list)


def tidy_up_container_name(app_obj, string, max_length):

    """Called by mainapp.TartubeApp.on_menu_add_channel(),
    .on_menu_add_playlist() and .on_menu_add_folder().

    Before creating a channel, playlist or folder, tidies up the name.

    Removes any leading/trailing whitespace. Reduces multiple whitespace
    characters to a single space character. Applies a maximum length.

    Also replaces any forward/backward slashes with hyphens (if the user
    specifies a name like 'Foo / Bar', that would create a directory on the
    filesystem called .../Foo/Bar, which is definitely not what we want).

    Args:

        app_obj (mainapp.TartubeApp): The main application

        string (str): The string to convert

        max_length (int): The maximum length of the converted string (should be
            mainapp.TartubeApp.container_name_max_len)

    Return values:

        The converted string, or an empty string for an irretrievable name

    """

    if string:

        string = string.strip()
        string = re.sub(r'\s+', ' ', string)

        # Get rid of ASCII control characters (illegal on Windows, a pain in
        #   the behind on POSIX)
        string = re.sub(r'[\x00-\x1F]', '', string)

        if os.name != 'nt':
            # Forbidden characters on POSIX: /
            # Forbidden on MacOS, depending on context: :
            string = re.sub(r'[\/\:]', '-', string)

        else:
            # Illegal filenames
            if string in app_obj.illegal_name_mswin_list:
                return ''

            for illegal in app_obj.illegal_name_mswin_list:
                if re.search('^' + illegal + '\.', string):
                    return ''

            # Forbidden characters on MS Windows: < > : " / \ | ? *
            string = re.sub(r'[\<\>\:\/\\\|\?\*]', '-', string)
            string = re.sub(r'[\"]', '\'', string)

            # Cannot end with a dot
            string = re.sub(r'\.+$', '', string)

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

    Return values:

        The converted string

    """

    if string:

        line_list = []

        for line in string.split('\n'):

            if line == '':
                # Preserve empty lines
                line_list.append('')

            else:

                w = classes.ModTextWrapper(
                    width=max_length,
                    break_long_words=False,
                    # Split up URLs on the forward slash character, as well as
                    #   on hyphen(s)
                    break_on_hyphens=True,
                )

                new_list = w.wrap(line)

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

    Return values:

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

                w = classes.ModTextWrapper(
                    width=max_length,
                    break_long_words=split_words_flag,
                    # Split up URLs on the forward slash character, as well as
                    #   on hyphen(s)
                    break_on_hyphens=split_words_flag,
                )

                new_list = w.wrap(line)

                for mini_line in new_list:
                    line_list.append(mini_line)

        return '\n'.join(line_list)

    else:

        # Empty string
        return string


def timestamp_add_second(app_obj, stamp=None):

    """Can be called by anything.

    Adds a second to a timestamp, converting a value like '1:59' to '2:00', or
    a value like '1:59:59' to '2:00:00'.

    Args:

        app_obj (mainapp.TartubeApp): The main application

        stamp (str): A timestamp in the form 'mm:ss' or 'h:mm:ss'. Leading
            zeroes are optional for all components, and the 'h' component can
            contain any number of digits

    Return values:

        The converted string. If the supplied timestamp is invalid or not
            specified, its value is returned unmodified

    """

    if stamp is not None:

        regex = r'^' + app_obj.timestamp_regex + r'$'
        match = re.search(regex, stamp)
        if match:

            hours = match.groups()[1]
            if hours is not None:
                hours = int(hours)

            minutes = int(match.groups()[2])
            seconds = int(match.groups()[3])

            seconds += 1
            if seconds >= 60:
                seconds = 0
                minutes += 1

                if minutes >= 60:
                    minutes = 0
                    if hours is not None:
                        hours += 1
                    else:
                        hours = 1

            stamp = '{:02d}'.format(minutes) + ':{:02d}'.format(seconds)
            if hours:
                stamp = str(hours) + ':' + stamp

    return stamp


def timestamp_compare(app_obj, start_stamp, stop_stamp):

    """Can be called by anything, after the user has manually entered a start
    and stop timestamp.

    Checks that either of the following is True:

        1. 'stop_stamp' is None
        2. 'start_stamp' occurs earlier than 'stop_stamp'

    Args:

        start_stamp (str): A timestamp in the form 'mm:ss' or 'h:mm:ss'.
            Leading zeroes are optional for all components, and the 'h'
            component can contain any number of digits

        stop_stamp (str or None): If specified, another timestamp in the same
            format

    Return values:

        False if 'stop_stamp' is earlier than 'start_stamp', if 'start_stamp'
            is invalid, or 'stop_stamp' is specified and invalid; True
            otherwise

    """

    if stop_stamp is None:
        return True

    regex = r'^' + app_obj.timestamp_regex + r'$'
    match = re.search(regex, start_stamp)
    if not match:
        return False

    else:
        if match.groups()[1] is not None:
            start_hours = int(match.groups()[1])
        else:
            start_hours = 0

        start_seconds = int(match.groups()[3]) \
        + (int(match.groups()[2]) * 60) \
        + (start_hours * 3600)

    match = re.search(regex, stop_stamp)
    if not match:
        return False

    else:
        if match.groups()[1] is not None:
            stop_hours = int(match.groups()[1])
        else:
            stop_hours = 0

        stop_seconds = int(match.groups()[3]) \
        + (int(match.groups()[2]) * 60) \
        + (stop_hours * 3600)

    if stop_seconds < start_seconds:
        return False
    else:
        return True


def timestamp_convert_to_seconds(app_obj, stamp):

    """Can be called by anything.

    Converts a timestamp to a value in seconds.

    Args:

        app_obj (mainapp.TartubeApp): The main application

        stamp (str): A timestamp in the form 'mm:ss' or 'h:mm:ss'. Leading
            zeroes are optional for all components, and the 'h' component can
            contain any number of digits

    Return values:

        The converted value, or the original value if 'stamp' is not a valid
            timestamp

    """

    regex = r'^' + app_obj.timestamp_regex + r'$'
    match = re.search(regex, stamp)
    if match:
        hours = match.groups()[1]
        if hours is not None:
            hours = int(hours)

        minutes = int(match.groups()[2])
        seconds = int(match.groups()[3])

        if hours:
            return seconds + minutes*60 + hours*60*60
        else:
            return seconds + minutes*60

    else:
        return stamp


def timestamp_format(app_obj, stamp):

    """Can be called by anything.

    The user can specify timestamps without leading zeroes, for example '1:59'
    for '01:59', or even '1:5' or '01:05'.

    Add leading zeroes for the minutes and seconds components. Removes leading
    zeroes for the hours component, if specified. This ensures that any list of
    timestamps is sorted correctly.

    Args:

        app_obj (mainapp.TartubeApp): The main application

        stamp (str): A timestamp in the form 'mm:ss' or 'h:mm:ss'. Leading
            zeroes are optional for all components, and the 'h' component can
            contain any number of digits

    Return values:

        The converted string. If the supplied timestamp is invalid, it is
            returned unmodified

    """

    regex = r'^' + app_obj.timestamp_regex + r'$'
    match = re.search(regex, stamp)
    if match:

        hours = match.groups()[1]
        if hours is not None:
            hours = int(hours)

        minutes = int(match.groups()[2])
        seconds = int(match.groups()[3])

        stamp = '{:02d}'.format(minutes) + ':{:02d}'.format(seconds)
        if hours:
            stamp = str(int(hours)) + ':' + stamp

    return stamp


def timestamp_quick_format(app_obj, hours, minutes, seconds,
    hour_digit_count=None):

    """Can be called by anything.

    A shorter version of utils.timestamp_format(), used when the hours, minutes
    and seconds components have already been extracted. (It would be wasteful
    to use the same regex to extract them again).

    The original timestamp was in the form 'mm:ss' or 'h:mm:ss'. Leading zeroes
    are optional for all components, and the 'h' component can contain any
    number of digits

    Add leading zeroes for the minutes and seconds components.

    Removes leading zeroes for the hours component, if specified. However, if
    'hour_digit_count' is specified, adds leading zeroes to make the correct
    number of digits.

    As a result of calling this function, any list of timestamps processed with
    this function can be sorted in the correct order.

    Args:

        app_obj (mainapp.TartubeApp): The main application

        hours (str or None): Optional string with the "h" component

        minutes, seconds (str): Non-optional strings with the 'mm' and 'ss'
            components

        hour_digit_count (int): The number of digits to use in the hours
            component, if specified

    """

    stamp = '{:02d}'.format(int(minutes)) + ':{:02d}'.format(int(seconds))

    if hours is None and hour_digit_count is not None:
        hours = 0

    if hours is not None:

        # Remove leading zeroes
        hours = str(int(hours))

        if hour_digit_count is None or len(hours) >= hour_digit_count:

            stamp = hours + ':' + stamp

        elif len(hours) < hour_digit_count:

            # Add leading zeroes
            stamp = hours.rjust(hour_digit_count, '0') + ':' + stamp

    return stamp


def to_string(data):

    """Can be called by anything.

    Convert any data type to a string.

    Args:

        data (-): The data type

    Return values:

        The converted string

    """

    return '%s' % data


def upper_case_first(string):

    """Can be called by anything.

    Args:

        string (str): The string to capitalise

    Return values:

        The converted string

    """

    return string[0].upper() + string[1:]
