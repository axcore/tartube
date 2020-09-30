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


"""FFmpeg manager classes."""


# Import Gtk modules
#   ...


# Import other modules
import os
import subprocess


# Import our modules
#   ...


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

        Returns:

            False if an attempted conversion fails, or True otherwise
                (including when no conversion is attempted)

        """

        # Sanity check
        if not os.path.isfile(thumbnail_filename) \
        or self.app_obj.ffmpeg_fail_flag:
            return True

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

                os.rename(thumbnail_filename, thumbnail_webp_filename)
                thumbnail_filename = thumbnail_webp_filename
                thumbnail_ext = 'webp'

        # Convert unsupported thumbnail formats to JPEG
        #   (youtube-dl #25687, #25717)
        if thumbnail_ext not in ['jpg', 'png']:

            # NB: % is supposed to be escaped with %% but this does not work
            # for input files so working around with standard substitution
            escaped_thumbnail_filename = thumbnail_filename.replace('%', '#')
            os.rename(thumbnail_filename, escaped_thumbnail_filename)
            escaped_thumbnail_jpg_filename = self.replace_extension(
                escaped_thumbnail_filename,
                'jpg',
            )

            # Run FFmpeg, which eturns a list in the form
            #   (success_flag, optional_message)
            result_list = self.run_ffmpeg(
                escaped_thumbnail_filename,
                escaped_thumbnail_jpg_filename,
                ['-bsf:v', 'mjpeg2jpeg'],
            )

            if not result_list or not result_list[0]:

                # Conversion failed; most likely because FFmpeg is not
                #   installed
                # Rename back to unescaped
                os.rename(escaped_thumbnail_filename, thumbnail_filename)

                return False

            else:

                # Conversion succeeded
                os.remove(escaped_thumbnail_filename)
                thumbnail_jpg_filename = self.replace_extension(
                    thumbnail_filename,
                    'jpg',
                )

                # Rename back to unescaped for further processing
                os.rename(
                    escaped_thumbnail_jpg_filename,
                    thumbnail_jpg_filename
                )

        # Procedure complete
        return True


    def _ffmpeg_filename_argument(self, path):

        """Called by self.run_ffmpeg_multiple_files().

        Adapted from youtube-dl/youtube-dl/postprocessor/ffmpeg.py.

        Returns a filename in a format that won't confuse FFmpeg.

        Args:

            path (str): The full path to a file to be processed by FFmpeg

        Returns:

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

        Returns:

            The path to the executable

        """

        if self.app_obj.ffmpeg_path:
            return self.app_obj.ffmpeg_path
        else:
            return 'ffmpeg'


    def is_webp(self, path):

        """Called by self.convert_webp() and utils.find_thumbnail_webp().

        Adapted from youtube-dl/youtube-dl/postprocessor/embedthumbnail.py.

        Tests whether a file is a .webp file (perhaps mislabelled as a .jpg
        file).

        Args:

            path (str): The full path to a file to be processed by FFmpeg

        """

        with open(path, 'rb') as fh:
            data = fh.read(12)

        return data[0:4] == b'RIFF' and data[8:] == b'WEBP'


    def replace_extension(self, path, ext, expected_real_ext=None):

        """Called by self.convert_webp().

        Adapted from youtube-dl/youtube-dl/utils.py.

        Given the full path to a file, replaces the extension, and returns the
        modified path.

        Args:

            path (str): The full path to a file

            ext (str): The new file extension

            expected_real_ext (str): Not used by Tartube

        Returns:

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

        """Can be called by anything.

        Currently called by self.convert_webp() and
        process.ProcessManager.process_video().

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

        """

        return self.run_ffmpeg_multiple_files(
            [ input_path ],
            out_path,
            opt_list,
            test_flag,
        )


    def run_ffmpeg_multiple_files(self, input_path_list, out_path, opt_list, \
    test_flag=False):

        """Can be called by anything.

        Currently called by self.run_ffmpeg().

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

        except:
            # If FFmpeg is not installed on the user's system, this is the
            #   result
            return [ False, 'Could not find FFmpeg' ]

        stdout, stderr = p.communicate()
        if p.returncode != 0:
            stderr = stderr.decode('utf-8', 'replace')
            return [ False, stderr.strip().split('\n')[-1] ]

        else:
            return [ self.try_utime(out_path, oldest_mtime, oldest_mtime), '' ]


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

