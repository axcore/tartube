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


"""FFmpeg manager classes."""


# Import Gtk modules
#   ...


# Import other modules
import os
import re
import shutil
import subprocess


# Import our modules
import mainapp
import utils


# Classes


class FFmpegManager(object):

    """Called by mainapp.TartubeApp.__init__().

    Python class to manage calls to FFmpeg that Tartube wants to make,
    independently of youtube-dl.

    Most of the code in this file has been updated from youtube-dl itself.

    Args:

        app_obj (mainapp.TartubeApp): The main application object

    """


    # Standard class methods


    def __init__(self, app_obj):


        super(FFmpegManager, self).__init__()

        # IV list - class objects
        # -----------------------
        # The main application
        self.app_obj = app_obj


    # Public class methods


    def convert_webp(self, thumbnail_filename):

        """Called by mainapp.TartubeApp.update_video_when_file_found(),
        downloads.VideoDownloader.confirm_sim_video() and
        downloads.JSONFetcher.do_fetch().

        Adapted from youtube-dl/youtube-dl/postprocessor/embedthumbnail.py.

        In June 2020, YouTube changed its image format from .jpg to .webp.
        Unfortunately, the Gtk library doesn't support that format.

        Worse still, YouTube also began sending .webp thumbnails mislabelled as
        .jpg.

        In response, in September 2020 youtube-dl implemented a fix for
        embedded thumbnails, using FFmpeg to convert .webp to .jpg. That code
        has been adapted here, so that YouTube thumbnails can be converted and
        made visible in the main window again.

        Args:

            thumbnail_filename (str): Full path to the webp file to be
                converted to jpg

        Return values:

            False if an attempted conversion fails, or True otherwise
                (including when no conversion is attempted)

        """

        # Sanity check
        if not os.path.isfile(thumbnail_filename) \
        or self.app_obj.ffmpeg_fail_flag:
            return True

        # Retain original thumbnails, if required
        if self.app_obj.ffmpeg_convert_webp_flag \
        and self.app_obj.ffmpeg_retain_webp_flag:
            retain_flag = True
        else:
            retain_flag = False

        # Correct extension for .webp files with the wrong extension
        #   (youtube-dl #25687, #25717)
        _, thumbnail_ext = os.path.splitext(thumbnail_filename)
        if thumbnail_ext:

            # Remove the initial full stop
            thumbnail_ext = thumbnail_ext[1:].lower()

            if thumbnail_ext != 'webp' and self.is_webp(thumbnail_filename):

                # .webp mislabelled as .jpg
                thumbnail_webp_filename = self.replace_extension(
                    thumbnail_filename,
                    'webp',
                )

                if not retain_flag:
                    try:
                        os.rename(thumbnail_filename, thumbnail_webp_filename)
                    except:
                        return False
                else:
                    try:
                        shutil.copyfile(
                            thumbnail_filename,
                            thumbnail_webp_filename,
                        )
                    except:
                        return False

                thumbnail_filename = thumbnail_webp_filename
                thumbnail_ext = 'webp'

            elif thumbnail_ext == 'webp' and \
            self.is_mislabelled_webp(thumbnail_filename):

                # .jpg mislabelled as .webp (Git #478)
                thumbnail_jpg_filename = self.replace_extension(
                    thumbnail_filename,
                    'jpg',
                )

                if not retain_flag:
                    try:
                        os.rename(thumbnail_filename, thumbnail_jpg_filename)
                    except:
                        return False
                else:
                    try:
                        shutil.copyfile(
                            thumbnail_filename,
                            thumbnail_jpg_filename,
                        )
                    except:
                        return False

                thumbnail_filename = thumbnail_jpg_filename
                thumbnail_ext = 'jpg'

        # Convert unsupported thumbnail formats to JPEG
        #   (youtube-dl #25687, #25717)
        if thumbnail_ext not in ['jpg', 'png']:

            # NB: % is supposed to be escaped with %% but this does not work
            #   for input files so working around with standard substitution
            escaped_thumbnail_filename = thumbnail_filename.replace('%', '#')
            escaped_thumbnail_jpg_filename = self.replace_extension(
                escaped_thumbnail_filename,
                'jpg',
            )

            # Handle special characters
            try:
                os.rename(thumbnail_filename, escaped_thumbnail_filename)
            except:
                return False

            # Run FFmpeg to convert the thumbnail(s)
            success_flag, msg = self.run_ffmpeg(
                escaped_thumbnail_filename,
                escaped_thumbnail_jpg_filename,
                ['-bsf:v', 'mjpeg2jpeg'],
            )

            if not success_flag:

                # Conversion failed; most likely because FFmpeg is not
                #   installed
                # Rename back to unescaped
                try:
                    os.rename(escaped_thumbnail_filename, thumbnail_filename)
                except:
                    pass

                return False

            else:

                # Conversion succeeded
                # Rename the (converted file) to unescaped for further
                #   processing
                thumbnail_jpg_filename = self.replace_extension(
                    thumbnail_filename,
                    'jpg',
                )

                try:
                    os.rename(
                        escaped_thumbnail_jpg_filename,
                        thumbnail_jpg_filename
                    )
                except:
                    return False

                if not retain_flag:

                    # The original .webp file is not retained
                    self.app_obj.remove_file(escaped_thumbnail_filename)

        # Procedure complete
        return True


    def _ffmpeg_filename_argument(self, path):

        """Called by self.run_ffmpeg_multiple_files().

        Adapted from youtube-dl/youtube-dl/postprocessor/ffmpeg.py.

        Returns a filename in a format that won't confuse FFmpeg.

        Args:

            path (str): The full path to a file to be processed by FFmpeg

        Return values:

            The modified string

        """

        # Always use 'file:' because the filename may contain ':' (ffmpeg
        #   interprets that as a protocol) or can start with '-' (-- is broken
        #   in  ffmpeg, see https://ffmpeg.org/trac/ffmpeg/ticket/2127 for
        #   details)
        # Also leave '-' intact in order not to break streaming to stdout
        return 'file:' + path if path != '-' else path


    def get_executable(self):

        """Called by self.run_ffmpeg_multiple_files().

        Not adapted from youtube-dl.

        Returns the path to the FFmpeg executable, which the user may have
        specified themselves. If not, assume ffmpeg is in the system path.

        Return values:

            The path to the executable

        """

        if self.app_obj.ffmpeg_path:
            return self.app_obj.ffmpeg_path
        else:
            return 'ffmpeg'


    def is_webp(self, path):

        """Called by self.convert_webp() and
        utils.find_thumbnail_webp_intact_or_broken().

        Adapted from youtube-dl/youtube-dl/postprocessor/embedthumbnail.py.

        Tests whether a file is a .webp file (perhaps mislabelled as a .jpg
        file).

        Args:

            path (str): The full path to a file to be processed by FFmpeg

        """

        with open(path, 'rb') as fh:
            data = fh.read(12)

        # Test .webp magic number
        return data[0:4] == b'RIFF' and data[8:] == b'WEBP'


    def is_mislabelled_webp(self, path):

        """Called by self.convert_webp() and
        utils.find_thumbnail_webp_intact_or_broken().

        Adapted from self.is_webp().

        Tests whether a file is a .jpg file (perhaps mislabelled as a .webp
        file), hoping to handle Git #478.

        Args:

            path (str): The full path to a file to be processed by FFmpeg

        """

        with open(path, 'rb') as fh:
            data = fh.read(3)

        return data[0:3] == b'\xff\xd8\xff'


    def replace_extension(self, path, ext, expected_real_ext=None):

        """Called by self.convert_webp().

        Adapted from youtube-dl/youtube-dl/utils.py.

        Given the full path to a file, replaces the extension, and returns the
        modified path.

        Args:

            path (str): The full path to a file

            ext (str): The new file extension

            expected_real_ext (str): Not used by Tartube

        Return values:

            The modified path

        """

        name, real_ext = os.path.splitext(path)

        return '{0}.{1}'.format(
            name if not expected_real_ext \
            or real_ext[1:] == expected_real_ext \
            else path,
            ext,
        )


    def run_ffmpeg(self, input_path, out_path, opt_list, test_flag=False):

        """Can be called by anything (currently called only by
        self.convert_webp() ).

        Adapted from youtube-dl/youtube-dl/postprocessor/ffmpeg.py.

        self.run_ffmpeg_multiple_files() expects a list of files. Pass on
        this function's parameters in the expected format.

        Args:

            input_path (str): Full path to a file to be processed by FFmpeg

            out_path (str): Full path to FFmpeg's output file

            opt_list (list): List of FFmpeg command line options (may be an
                empty list)

            test_flag (bool): If True, just returns the FFmpeg system command,
                rather than executing it

        Return values:

            Returns a list of two items, in the form
                (success_flag, optional_message)

        """

        return self.run_ffmpeg_multiple_files(
            [ input_path ],
            out_path,
            opt_list,
            test_flag,
        )


    def run_ffmpeg_multiple_files(self, input_path_list, out_path, opt_list, \
    test_flag=False):

        """Can be called by anything (currently called only by
        self.run_ffmpeg() ).

        Adapted from youtube-dl/youtube-dl/postprocessor/ffmpeg.py.

        Prepares the FFmpeg system command, and then executes it.

        Args:

            input_path_list (list): List of full paths to files to be
                processed by FFmpeg. At the moment, Tartube only processes one
                file at a time

            out_path (str): Full path to FFmpeg's output file

            opt_list (list): List of FFmpeg command line options (may be an
                empty list)

            test_flag (bool): If True, just returns the FFmpeg system command,
                rather than executing it

        Return values:

            Returns a list of two items, in the form
                (success_flag, optional_message)

        """

        # Get the modification time for the oldest file
        oldest_mtime = min(os.stat(path).st_mtime for path in input_path_list)

        # Prepare the system command
        files_cmd_list = []
        for path in input_path_list:
            files_cmd_list.extend(['-i', self._ffmpeg_filename_argument(path)])

        cmd_list = [self.get_executable(), '-y']
        cmd_list += ['-loglevel', 'repeat+info']
        cmd_list += (
            files_cmd_list
            + opt_list
            + [self._ffmpeg_filename_argument(out_path)]
        )

        # Return the system command only, if required
        if test_flag:
            return [ True, cmd_list ]

        # Execute the system command in a subprocess
        try:
            p = subprocess.Popen(
                cmd_list,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
            )

        except Exception as e:
            return [ False, str(e) ]

        stdout, stderr = p.communicate()
        if p.returncode != 0:
            stderr = stderr.decode(utils.get_encoding(), 'replace')
            return [ False, stderr.strip().split('\n')[-1] ]

        else:
            return [ self.try_utime(out_path, oldest_mtime, oldest_mtime), '' ]


    def run_ffmpeg_directly(self, video_obj, source_path, cmd_list):

        """Modified version of self.run_ffmpeg(), called by
        process.ProcessManager.process_video().

        Adapted from youtube-dl/youtube-dl/postprocessor/ffmpeg.py.

        Prepares the FFmpeg system command, and then executes it.

        Args:

            video_obj (media.Video): The video object to be processed

            source_path (str): The full path to the source file

            cmd_list (list): The FFmpeg system command to use, as a list

        Return values:

            Returns a list of two items, in the form
                (success_flag, optional_message)

        """

        # Get the file's modification time
        mod_time = os.stat(source_path).st_mtime

        # Execute the system command in a subprocess
        try:
            p = subprocess.Popen(
                cmd_list,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
            )

        except Exception as e:
            return [ False, str(e) ]

        stdout, stderr = p.communicate()
        if p.returncode != 0:
            stderr = stderr.decode(utils.get_encoding(), 'replace')
            return [ False, stderr.strip().split('\n')[-1] ]

        else:
            return [ self.try_utime(source_path, mod_time, mod_time), '' ]


    def try_utime(self, path, atime, mtime):

        """Called by self.run_ffmpeg_multiple_files().

        Adapted from youtube-dl/youtube-dl/postprocessor/common.py.

        Return values:

            True on success, False on failure

        """

        try:
            os.utime(path, (atime, mtime))
            return True

        except Exception:
            return False


class FFmpegOptionsManager(object):

    """This class handles options to passed to FFmpeg, when the user wants to
    process video(s) directly (i.e. not via youtube-dl).

    Adapted from FFmpeg Command Line Wizard, by AndreKR
        (https://github.com/AndreKR/ffmpeg-command-line-wizard).

    OPTIONS (NAME TAB)

        extra_cmd_string (str): A string of extra FFmpeg options, to be applied
            to the system command (if an empty string, nothing is added)

    OPTIONS (FILE TAB)

        add_end_filename (str): A string to be added to the end of the
            filename, converting the source file to an output file with a
            different name (if an empty string, nothing is added)

        regex_match_filename (str):
        regex_apply_subst (str):
            Two strings used in a regex substituion. If the first regex matches
            the filename, the second string is used in the substitution. This
            converts the source file to an output file with a different name.
            (If the first string is an empty string, the filename is not
            changed)

        rename_both_flag (bool): If True, when a video is renamed (using any of
            the options above), the thumbnail is also renamed (but not
            vice-versa; renaming the thumbnail does not affect the video)

        change_file_ext (str): A new file extension. If not an empty string,
            then FFmpeg converts the video/audio/image file from one format to
            another. (If an empty string, the format is not changed. Ignored
            if 'output_mode' is 'gif')

        delete_original_flag (bool): If True and the source/output files have
            different names, then the source file is deleted

    OPTIONS (SETTINGS TAB)

        input_mode (str): 'video' to convert a video/audio file (the one
            downloaded by the specified media.Video object), or 'thumb' to
            convert that video's thumbnail (if it has been downloaded)

        output_mode (str): Always set to 'thumb' if 'input_mode' is set to
            'thumb'. Otherwise, the default value is 'h264'. The other possible
            values are 'gif' (in which case the video format is changed to
            .GIF), 'merge' (in which case the video is merged with au audio
            file with the same file name), 'split' (in which case the video is
            split into pieces according to timestamps) or 'slice' (In which
            case slices are removed from a video); in all four cases, the
            'change_file_ext' option is ignored)

        audio_flag (bool): If True, and if 'input_mode' is 'video', the video's
            audio is preserved when the file is converted. Ignored if
            'input_mode' is 'thumb'

        audio_bitrate (int): Value that's a multiple of 16 (minimum value is
            16)

        quality_mode (str): 'crf' for 'Manual rate factor', or 'abr' for
            'Determine from target bitrate (2-Pass)'

        rate_factor (int): Value in the range 0-51. Ignored if 'quality_mode'
            is 'abr'

        dummy_file (str): A dummy file is created during the first pass. The
            name of that file: 'output', 'dummy', '/dev/null/' for Linux,
            'NUL' for MS Windows. Ignored if 'quality_mode' is 'crf'

        patience_preset (str): Affects how long the file conversion takes, and
            also the size of the output file. Values are those used by FFmpeg
            itself: 'ultrafast', 'superfast', 'veryfast', 'faster', 'fast',
            'medium', 'slow', 'slower', 'veryslow'

        gpu_encoding (str): Optimisations for various GPUs. One of the values
            'libx264', 'libx265', 'h264_amf', 'hevc_amf', 'h264_nvenc',
            'hevc_nvenc'

        hw_accel (str): Hardware acceleration mode: 'none', 'auto', 'vdpau',
            'dxva2', 'vaapi', 'qsv'

        palette_mode (str): Ignored unless 'output_mode' is 'gif'. Values are
            'faster' or 'better'

        split_mode (str): Ignored unless 'output_mode' is 'split'. Values are
            'video' to use the video's timestamps to split the file, or
            'custom' to use a custom set of timestamps to split the file

        split_list (list): Ignored unless 'split_mode' is 'custom'. A list
            of timestamps and clip titles used to split the video into clips.
            A list in groups of three, in the form
                [start_stamp, stop_stamp, clip_title]
            If 'stop_stamp' is None, then the end of the video (or the next
                'start_stamp') is used. 'clip_title' is optional (None if not
                specified)

        slice_mode (str): Ignored unless 'output_mode' is 'slice'. Values are
            'video' to remove slices from the video using the video's own
            slice list, or 'custom' to use a custom set of slices

        slice_list (list): Ignored unless 'slice_mode' is 'custom'. A list of
            video slice data used to remove slices from a video, in the form
            described by media.Video.__init__()

    OPTIONS (OPTIMISATIONS TAB)

        seek_flag (bool): True to optimise for fast seeking (shorter keyframe
            interval, about 10% larger file)

        tuning_film_flag (bool): True if the input video is a high-quality
            movie

        tuning_animation_flag (bool): True if the input video is an animated
            movie

        tuning_grain_flag (bool): True if the input video contains film grain

        tuning_still_image_flag (bool): True if the input video is an image
            slideshow

        tuning_fast_decode_flag (bool): True to optimise for really weak CPU
            playback devices

        profile_flag (bool): True to optimise for really old devices (requires
            rate factor above 0)

        fast_start_flag (bool): True to move headers to the beginning of the
            file (so it can play while still downloading)

        tuning_zero_latency_flag (bool): True for fast encoding and low
            latency streaming

        limit_flag (bool): True to limit the bitrate, using the values
            specified by the options 'limit_mbps' and 'limit_buffer'

        limit_mbps (int): Bitrate limit in Mbit/s. Value that's a multiple of
            0.2 (minimum value is 0). Ignored if 'limit_flag' is False

        limit_buffer (int): Assume a receiving buffer (in seconds), Value
            that's a multiple of 0.2 (minimum value is 0). Ignored if
            'limit_flag' is False

    """


    # Standard class methods


    def __init__(self, uid, name):

        # IV list - other
        # ---------------
        # Unique ID for this options manager
        self.uid = uid
        # A non-unique name for this options manager
        self.name = name

        # Dictionary of FFmpeg options, set by a call to self.reset_options
        self.options_dict = {}


        # Code
        # ----

        # Initialise FFmpeg options
        self.reset_options()


    # Public class methods


    def clone_options(self, other_options_manager_obj):

        """Called by mainapp.TartubeApp.clone_ffmpeg_options() and
        .clone_ffmpeg_options_from_window().

        Clones FFmpeg options from the specified object into this object,
        completely replacing this object's FFmpeg options.

        Args:

            other_options_manager_obj (ffmpeg_tartube.FFmpegOptionsManager):
                The FFmpeg options object (usually the current one), from which
                options will be cloned

        """

        # (All values are scalars; there are no lists/dictionaries to copy)
        self.options_dict = other_options_manager_obj.options_dict.copy()


    def reset_options(self):

        """Called by self.__init__().

        Resets (or initialises) self.options_dict to its default state.
        """

        self.options_dict = {
            # NAME TAB
            'extra_cmd_string': '',
            # FILE TAB
            'add_end_filename': '',
            'regex_match_filename': '',
            'regex_apply_subst': '',
            'rename_both_flag': False,
            'change_file_ext': '',
            'delete_original_flag': False,
            # SETTINGS TAB
             # 'video', 'thumb'
            'input_mode': 'video',
            # 'h264', 'gif', 'merge', 'split', 'thumb'
            'output_mode': 'h264',
            # SETTINGS TAB ('output_mode' = 'h264')
            'audio_flag': True,
            'audio_bitrate': 128,
            # 'cfg', 'abr'
            'quality_mode': 'crf',
            'rate_factor': 23,
            # 'output', 'dummy', '/dev/null/', 'NUL'
            'dummy_file': 'output',
            # 'ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium',
            #   'slow', 'slower', 'veryslow'
            'patience_preset': 'medium',
            # 'libx264', 'libx265', 'h264_amf', 'hevc_amf', 'h264_nvenc',
            #   'hevc_nvenc'
            'gpu_encoding': 'libx264',
            # 'none', 'auto', 'vdpau', 'dxva2', 'vaapi', 'qsv'
            'hw_accel': 'none',
            # SETTINGS TAB ('output_mode' = 'gif')
            'palette_mode': 'faster',       # 'faster', 'better'
            # SETTINGS TAB ('output_mode' = 'split')
            'split_mode': 'video',          # 'video', 'custom'
            'split_list': [],               # list in groups of 3
            # SETTINGS TAB ('output_mode' = 'slice')
            'slice_mode': 'video',          # 'video', 'custom'
            'slice_list': [],               # list of dictionaries
            # OPTIMISATIONS TAB ('output_mode' = 'h264')
            'seek_flag': True,
            'tuning_film_flag': False,
            'tuning_animation_flag': False,
            'tuning_grain_flag': False,
            'tuning_still_image_flag': False,
            'tuning_fast_decode_flag': False,
            'profile_flag': False,
            'fast_start_flag': True,
            'tuning_zero_latency_flag': False,
            'limit_flag': False,
            'limit_mbps': 1,
            'limit_buffer': 2,
            # NOT VISIBLE IN THE EDIT WINDOW (a constant value)
            'bitrate': 0,
        }


    def get_system_cmd(self, app_obj, video_obj=None, start_point=None,
    stop_point=None, clip_title=None, clip_dir=None, edit_dict=[]):

        """Can be called by anything.

        Given the FFmpeg options specified by self.options_dict, generates the
        FFmpeg system command, returning it as a list of options.

        N.B. The 'delete_original_flag' option is not applied until the end of
        the process operation.

        Args:

            app_obj (mainapp.TartubeApp): The main application

            video_obj (media.Video or None): If specified, uses the video's
                downloaded file as the source file. Not specified when called
                from config.FFmpegOptionsEditWin, in which case a specimen
                source file is used (so that a specimen system command can be
                displayed in the edit window)

            start_point, stop_point, clip_title, clip_dir (str):
                When splitting a video, the points at which to start/stop
                (timestamps or values in seconds), the clip title, and the
                destination directory for sections (if not the same as the
                original file). Ignored if 'output_mode' is not 'split' or
                'slice'. If 'output_mode' is 'split' or 'slice', then these
                arguments are not specified when called from
                config.FFmpegOptionsEditWin, in which case specimen timestamps/
                titles are used

            edit_dict (dict): When called from the edit window, any changes
                that have been made to the FFmpeg options, but which have not
                yet been saved to this object. We take those changes into
                account when compiling the system command.

        Return values:

            Returns a tuple of three items:

                - The full path to the source file
                - The full path to the output file
                - A (python) list of options comprising the complete system
                    commmand (including the FFmpeg binary and the source/output
                    files)

        """

        opt_list = []
        tuning_list = []
        return_list = []

        # When called from the edit window (config.FFmpegOptionsEditWin), any
        #   changes in the edit window may not have been applied to
        #   self.options_dict yet
        # To produce an up-to-date system command, use a temporary copy of
        #   self.options_dict, to which the unapplied changes have been added
        options_dict = self.options_dict.copy()
        for key in edit_dict:
            options_dict[key] = edit_dict[key]

        # (Shortcuts to values retrieved several times)
        bitrate = options_dict['bitrate']
        input_mode = options_dict['input_mode']
        limit_buffer = options_dict['limit_buffer']
        limit_mbps = options_dict['limit_mbps']
        output_mode = options_dict['output_mode']
        rate_factor = options_dict['rate_factor']

        # The 'extra_cmd_string' item must be processed, and split into
        #   a list of separate items, preserving everything inside quotes as a
        #   single item (just as we do for youtube-dl download options)
        extra_cmd_string = options_dict['extra_cmd_string']
        if extra_cmd_string != '':
            extra_cmd_list = utils.parse_options(extra_cmd_string)
        else:
            extra_cmd_list = []

        # FFmpeg binary
        binary = app_obj.ffmpeg_manager_obj.get_executable()

        # Set variables describing the full path to the source video/audio and/
        #   or source thumbnail files

        # If no media.Video object was specified, then use specimen paths that
        #   can be displayed in the edit window's textview
        if video_obj is None:

            source_video_path = 'source.ext'
            source_audio_path = 'source.ext'
            source_thumb_path = 'source.jpg'

        else:

            if video_obj.dummy_flag:

                # (Special case: 'dummy' video objects (those downloaded in the
                #   Classic Mode tab) use different IVs)

                # If a specified media.Video has an unknown path, then return
                #   an empty list; there is nothing for FFmpeg to convert
                if video_obj.dummy_path is None:
                    return None

                # Check the video/audio file actually exists. If not, there is
                #   nothing for FFmpeg to convert
                source_video_path = video_obj.dummy_path
                if not os.path.exists(source_video_path) \
                and input_mode == 'video':
                    return None, None, []

            else:

                # If a specified media.Video has an unknown filename, then
                #   return an empty list; there is nothing for FFmpeg to
                #   convert
                if video_obj.file_name is None:
                    return None, None, []

                # Check the video/audio file actually exists, and is marked as
                #   downloaded. If not, there is nothing for FFmpeg to convert
                source_video_path = video_obj.get_actual_path(app_obj)
                if (
                    not os.path.exists(source_video_path) \
                    or not video_obj.dl_flag
                ) and input_mode == 'video':
                    return None, None, []

            # Find the video's thumbnail
            source_thumb_path = utils.find_thumbnail(app_obj, video_obj, True)
            if source_thumb_path is None and input_mode == 'thumb':
                # Return an empty list; there is nothing for FFmpeg to convert
                return None, None, []

            # If 'output_mode' is 'merge', then look for an audio file with the
            #   same name as the video file (but otherwise don't bother)
            source_audio_path = None
            if output_mode == 'merge':

                name, video_ext = os.path.splitext(source_video_path)
                for audio_ext in formats.AUDIO_FORMAT_LIST:

                    audio_path = os.path.abspath(os.path.join(name, audio_ext))
                    if os.path.isfile(audio_path):
                        source_audio_path = audio_path
                        break

                if source_audio_path is None:
                    # Nothing merge
                    return None, None, []

        # Break down the full path into its components, so that we can set the
        #   output file, after applying optional modifications
        if input_mode == 'video':
            output_dir, output_file = os.path.split(source_video_path)
        else:
            output_dir, output_file = os.path.split(source_thumb_path)

        output_name, output_ext = os.path.splitext(output_file)

        add_end_filename = options_dict['add_end_filename']
        if add_end_filename != '':

            # Remove trailing whitepsace
            add_end_filename = re.sub(
                r'\s+$',
                '',
                options_dict['add_end_filename'],
            )

            # Update the filename
            output_name += add_end_filename

        regex_match_filename = options_dict['regex_match_filename']
        if regex_match_filename != '':

            output_name = re.sub(
                regex_match_filename,
                options_dict['regex_apply_subst'],
                output_name,
            )

        change_file_ext = options_dict['change_file_ext'].lower()
        if change_file_ext == '':
            output_file = output_name + output_ext
        else:
            output_file = output_name + '.' + change_file_ext

        if video_obj is None:
            output_path = output_file
        else:
            output_path = os.path.abspath(
                os.path.join(output_dir, output_file),
            )

        # Special case: when called from config.FFmpegOptionsEditWin, then show
        #   a specimen system command resembling the one that will eventually
        #   be generated by FFmpegManager.run_ffmpeg_multiple_files()
        if app_obj.ffmpeg_simple_options_flag \
        and video_obj is None \
        and output_mode != 'split' \
        and output_mode != 'slice':

            return_list.append(binary)
            return_list.append('-y')
            return_list.append('-loglevel')
            return_list.append('repeat+info')
            return_list.append('-i')

            if input_mode == 'video':
                return_list.append(source_video_path)
            else:
                return_list.append(source_thumb_path)

            if extra_cmd_list:
                return_list.extend(extra_cmd_list)

            return_list.extend(
                [
                    app_obj.ffmpeg_manager_obj._ffmpeg_filename_argument(
                        output_path,
                    ),
                ],
            )

            return source_video_path, output_path, return_list

        # When the full GUI layout is visible, apply all FFmpeg options
        if input_mode == 'video':

            opt_list.append('-i')
            opt_list.append(source_video_path)

        else:

            opt_list.append('-i')
            opt_list.append(source_thumb_path)

        # H.264
        if output_mode == 'h264':

            # In the original code, this was marked:
            #   Only necessary if the output filename does not end with .mp4
            opt_list.append('-c:v')
            opt_list.append(options_dict['gpu_encoding'])

            opt_list.append('-preset')
            opt_list.append(options_dict['patience_preset'])

            if options_dict['hw_accel'] != 'none':
                opt_list.append('-hwaccel')
                opt_list.append(options_dict['hw_accel'])

            if options_dict['tuning_film_flag']:
                tuning_list.append('film')
            if options_dict['tuning_animation_flag']:
                tuning_list.append('animation')
            if options_dict['tuning_grain_flag']:
                tuning_list.append('grain')
            if options_dict['tuning_still_image_flag']:
                tuning_list.append('stillimage')
            if options_dict['tuning_fast_decode_flag']:
                tuning_list.append('fastdecode')
            if options_dict['tuning_zero_latency_flag']:
                tuning_list.append('zerolatency')

            if tuning_list:
                opt_list.append('-tune')
                opt_list.append(','.join(tuning_list))

            if options_dict['fast_start_flag']:
                opt_list.append('-movflags')
                opt_list.append('faststart')

            if input_mode == 'video' and options_dict['audio_flag']:
                opt_list.append('-c:a')
                opt_list.append('aac')
                opt_list.append('-b:a')
                opt_list.append(
                    str(options_dict['audio_bitrate']) + 'k',
                )

            if options_dict['profile_flag'] and rate_factor != 0:
                opt_list.append('-profile:v')
                opt_list.append('baseline')
                opt_list.append('-level')
                opt_list.append('3.0')

            if options_dict['limit_flag']:
                opt_list.append('-maxrate')
                opt_list.append(str(limit_mbps) + 'M')
                opt_list.append('-bufsize')
                opt_list.append((str(limit_mbps) * str(limit_buffer)) + 'M')

            if options_dict['seek_flag']:

                # In the original code, this was marked:
                #   Inserts an I-frame every 15 frames
                opt_list.append('-x264-params')
                opt_list.append('keyint=15')

            # In the original code, this was marked:
            #   Preserves the frame timestamps of VFR videos
            opt_list.append('-vsync')
            opt_list.append('2')
            opt_list.append('-enc_time_base')
            opt_list.append('-1')

            if options_dict['quality_mode'] == 'crf':

                return_list.append(binary)
                return_list.extend(opt_list)
                return_list.append('-crf')
                return_list.append(str(rate_factor))

                if extra_cmd_list:
                    return_list.extend(extra_cmd_list)

                return_list.append(output_path)

            else:
                dummy_file = options_dict['dummy_file']
                if dummy_file == 'output':
                    dummy_file = output_path

                return_list.append(binary)
                return_list.append('-y')
                return_list.extend(opt_list)
                return_list.append('-b:v')
                return_list.append(str(bitrate))
                return_list.append('-pass')
                return_list.append('1')
                return_list.append('-f')
                return_list.append('mp4')
                return_list.append(dummy_file)

                return_list.append('&&')
                return_list.append(binary)
                return_list.extend(opt_list)
                return_list.append('-b:v')
                return_list.append(str(bitrate))
                return_list.append('-pass')
                return_list.append('2')

                if extra_cmd_list:
                    return_list.extend(extra_cmd_list)

                return_list.append(output_path)

        # GIF
        elif output_mode == 'gif':

            if options_dict['palette_mode'] == 'faster':

                return_list.append(binary)
                return_list.extend(opt_list)

                if extra_cmd_list:
                    return_list.extend(extra_cmd_list)

                return_list.append(output_name + '.gif')

            else:

                return_list.append(binary)
                return_list.extend(opt_list)
                return_list.append('-vf')
                return_list.append('palettegen')
                return_list.append('palette.png')

                return_list.append('&&')
                return_list.append(binary)
                return_list.extend(opt_list)
                return_list.append('-i')
                return_list.append('palette.png')
                return_list.append('-filter_complex')
                return_list.append('"[0:v][1:v] paletteuse"')

                if extra_cmd_list:
                    return_list.extend(extra_cmd_list)

                return_list.append(output_name + '.gif')

        # Merge video/audio
        elif output_mode == 'merge':

            return_list.append(binary)
            return_list.extend(opt_list)

            return_list.append('-i')
            return_list.append(source_audio_path)
            return_list.append('-c:v')
            return_list.append('copy')
            return_list.append('-c:a')
            return_list.append('copy')

            return_list.append(output_path)

        # Split video by timestamps, or times in seconds
        elif output_mode == 'split' or output_mode == 'slice':

            return_list.append(binary)
            return_list.extend(opt_list)

            if output_mode == 'split':

                return_list.append('-ss')
                if start_point is None:
                    # (A specimen timestamp)
                    return_list.append('0:00')
                else:
                    return_list.append(str(start_point))

                # (If no timestamp is specified, the end of the video is used)
                if stop_point is not None:
                    return_list.append('-to')
                    return_list.append(str(stop_point))

            else:

                return_list.append('-ss')
                if start_point is None:
                    # (A specimen time, in seconds)
                    return_list.append('0')
                else:
                    return_list.append(str(start_point))

                # (If no timestamp is specified, the end of the video is used)
                if stop_point is not None:
                    return_list.append('-to')
                    return_list.append(str(stop_point))

            if clip_title is None or clip_title == "":
                # (When called from config.FFmpegOptionsEditWin)
                clip_title = app_obj.split_video_generic_title

            if clip_dir is None:

                output_path = os.path.abspath(
                    os.path.join(output_dir, clip_title + output_ext),
                )

            else:

                output_path = os.path.abspath(
                    os.path.join(clip_dir, clip_title + output_ext),
                )

            return_list.append(output_path)

        # Video thumbnails
        else:

            return_list.append(binary)
            return_list.extend(opt_list)
            return_list.append(output_path)

        # All done
        if output_mode == 'thumb':
            return source_thumb_path, output_path, return_list
        else:
            return source_video_path, output_path, return_list
