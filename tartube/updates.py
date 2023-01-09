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


"""Update operation classes."""


# Import Gtk modules
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GObject


# Import other modules
import os
import queue
import re
import requests
import signal
import subprocess
import sys
import threading
import time


# Import our modules
import downloads
import utils
# Use same gettext translations
from mainapp import _


# Classes


class UpdateManager(threading.Thread):

    """Called by mainapp.TartubeApp.update_manager_start() or
    .update_manager_start_from_wizwin().

    Python class to create a system child process, to do one of two jobs:

    1. Install FFmpeg, matplotlib or streamlink (on MS Windows only)

    2. Install youtube-dl, or update it to its most recent version.

    Reads from the child process STDOUT and STDERR, having set up a
    downloads.PipeReader object to do so in an asynchronous way.

    Args:

        app_obj (mainapp.TartubeApp): The main application

        update_type (str): 'ffmpeg' to install FFmpeg (on MS Windows only),
            'matplotlib' to install matplotlib (on MS Windows only),
            'streamlink' to install streamlink (on MS Windows onlY), or 'ytdl'
            to install/update youtube-dl (or a fork of it)

        wiz_win_obj (wizwin.SetupWizWin or None): The calling setup wizard
            window (if set, the main window doesn't exist yet)

    """


    # Standard class methods


    def __init__(self, app_obj, update_type, wiz_win_obj=None):

        super(UpdateManager, self).__init__()

        # IV list - class objects
        # -----------------------
        # The mainapp.TartubeApp object
        self.app_obj = app_obj
        # The calling setup wizard window (if set, the main window doesn't
        #   exist yet)
        self.wiz_win_obj = wiz_win_obj

        # The child process created by self.create_child_process()
        self.child_process = None

        # Read from the child process STDOUT (i.e. self.child_process.stdout)
        #   and STDERR (i.e. self.child_process.stderr) in an asynchronous way
        #   by polling this queue.PriorityQueue object
        self.queue = queue.PriorityQueue()
        self.stdout_reader = downloads.PipeReader(self.queue, 'stdout')
        self.stderr_reader = downloads.PipeReader(self.queue, 'stderr')


        # IV list - other
        # ---------------
        # The time (in seconds) between iterations of the loop in
        #   self.install_ffmpeg(), .install_matplotlib(), .install_streamlink()
        #   and .install_ytdl()
        self.sleep_time = 0.1

        # 'ffmpeg' to install FFmpeg (on MS Windows only), 'matplotlib' to
        #   install matplotlib (on MS Windows only), 'streamlink' to install
        #   streamlink (on MS Windows only) or 'ytdl' to install/update
        #   youtube-dl (or a fork of it)
        self.update_type = update_type
        # Flag set to True if the update operation succeeds, False if it fails
        self.success_flag = False

        # The youtube-dl version number as a string, if captured from the child
        #   process (e.g. '2019.07.02')
        self.ytdl_version = None

        # (For debugging purposes, store any STDOUT/STDERR messages received;
        #   otherwise we would just set a flag if a STDERR message was
        #   received)
        self.stdout_list = []
        self.stderr_list = []


        # Code
        # ----

        # Let's get this party started!
        self.start()


    # Public class methods


    def run(self):

        """Called as a result of self.__init__().

        Initiates the download.
        """

        if self.update_type == 'ffmpeg':
            self.install_ffmpeg()
        elif self.update_type == 'matplotlib':
            self.install_matplotlib()
        elif self.update_type == 'streamlink':
            self.install_streamlink()
        else:
            self.install_ytdl()


    def create_child_process(self, cmd_list):

        """Called by self.install_ffmpeg(), .install_matplotlib(),
        .install_streamlink() or .install_ytdl().

        Based on code from downloads.VideoDownloader.create_child_process().

        Executes the system command, creating a new child process which
        executes youtube-dl.

        Updates self.stderr_list in the event of an error.

        Args:

            cmd_list (list): Python list that contains the command to execute

        """

        # Strip double quotes from arguments
        # (Since we're sending the system command one argument at a time, we
        #   don't need to retain the double quotes around any single argument
        #   and, in fact, doing so would cause an error)
        cmd_list = utils.strip_double_quotes(cmd_list)

        # Create the child process
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
            # (The code in self.run() will spot that the child process did not
            #   start)
            self.stderr_list.append(_('Child process did not start'))


    def install_ffmpeg(self):

        """Called by self.run().

        A modified version of self.install_ytdl, that installs FFmpeg on an
        MS Windows system.

        Creates a child process to run the installation process.

        Reads from the child process STDOUT and STDERR, and calls the main
        application with the result of the update (success or failure).
        """

        # Show information about the update operation in the Output tab
        self.install_ffmpeg_write_output(
            _('Starting update operation, installing FFmpeg'),
        )

        # Create a new child process to install either the 64-bit or 32-bit
        #   version of FFmpeg, as appropriate
        if sys.maxsize <= 2147483647:
            binary = 'mingw-w64-i686-ffmpeg'
        else:
            binary = 'mingw-w64-x86_64-ffmpeg'

        # Prepare a system command...
        cmd_list = ['pacman', '-S', binary, '--noconfirm']
        # ...and display it in the Output tab (if required)
        self.install_ffmpeg_write_output(
            ' '.join(cmd_list),
            True,                   # A system command, not a message
        )

        # Create a new child process using that command...
        self.create_child_process(cmd_list)
        # ...and set up the PipeReader objects to read from the child process
        #   STDOUT and STDERR
        if self.child_process is not None:
            self.stdout_reader.attach_fh(self.child_process.stdout)
            self.stderr_reader.attach_fh(self.child_process.stderr)

        while self.is_child_process_alive():

            # Pause a moment between each iteration of the loop (we don't want
            #   to hog system resources)
            time.sleep(self.sleep_time)

            # Read from the child process STDOUT and STDERR, in the correct
            #   order, until there is nothing left to read
            while self.read_ffmpeg_child_process():
                pass

        # (Generate our own error messages for debugging purposes, in certain
        #   situations)
        if self.child_process is None:
            self.stderr_list.append(_('FFmpeg installation did not start'))

        elif self.child_process.returncode > 0:
            self.stderr_list.append(
                _('Child process exited with non-zero code: {}').format(
                    self.child_process.returncode,
                )
            )

        # Operation complete. self.success_flag is checked by
        #   mainapp.TartubeApp.update_manager_finished()
        if not self.stderr_list:
            self.success_flag = True

        # Show a confirmation in the the Output tab (or wizard window textview)
        self.install_ffmpeg_write_output(_('Update operation finished'))

        # Let the timer run for a few more seconds to prevent Gtk errors
        GObject.timeout_add(
            0,
            self.app_obj.update_manager_halt_timer,
        )


    def install_ffmpeg_write_output(self, msg, system_cmd_flag=False):

        """Called by self.install_ffmpeg().

        Writes a message to the Output tab (or to the setup wizard window, if
        called from there).

        Args:

            msg (str): The message to display

            system_cmd_flag (bool): If True, display system commands in a
                different colour in the Output tab (ignored when writing in
                the setup wizard window)

        """

        if not self.wiz_win_obj:

            if not system_cmd_flag:
                self.app_obj.main_win_obj.output_tab_write_stdout(1, msg)
            else:
                self.app_obj.main_win_obj.output_tab_write_system_cmd(1, msg)

        else:

            GObject.timeout_add(
                0,
                self.wiz_win_obj.ffmpeg_page_write,
                msg,
            )


    def install_matplotlib(self):

        """Called by self.run().

        A modified version of self.install_ytdl, that installs matplotlib on an
        MS Windows system.

        Creates a child process to run the installation process.

        Reads from the child process STDOUT and STDERR, and calls the main
        application with the result of the update (success or failure).
        """

        # Show information about the update operation in the Output tab
        self.install_matplotlib_write_output(
            _('Starting update operation, installing matplotlib'),
        )

        # Create a new child process to install either the 64-bit or 32-bit
        #   version of matplotlib, as appropriate
        if sys.maxsize <= 2147483647:
            binary = 'mingw-w64-i686-python-matplotlib'
        else:
            binary = 'mingw-w64-x86_64-python-matplotlib'

        # Prepare a system command...
        cmd_list = ['pacman', '-S', binary, '--noconfirm']
        # ...and display it in the Output tab (if required)
        self.install_matplotlib_write_output(
            ' '.join(cmd_list),
            True,                   # A system command, not a message
        )

        # Create a new child process using that command...
        self.create_child_process(cmd_list)
        # ...and set up the PipeReader objects to read from the child process
        #   STDOUT and STDERR
        if self.child_process is not None:
            self.stdout_reader.attach_fh(self.child_process.stdout)
            self.stderr_reader.attach_fh(self.child_process.stderr)

        while self.is_child_process_alive():

            # Pause a moment between each iteration of the loop (we don't want
            #   to hog system resources)
            time.sleep(self.sleep_time)

            # Read from the child process STDOUT and STDERR, in the correct
            #   order, until there is nothing left to read
            while self.read_matplotlib_child_process():
                pass

        # (Generate our own error messages for debugging purposes, in certain
        #   situations)
        if self.child_process is None:
            self.stderr_list.append(_('matplotlib installation did not start'))

        elif self.child_process.returncode > 0:
            self.stderr_list.append(
                _('Child process exited with non-zero code: {}').format(
                    self.child_process.returncode,
                )
            )

        # Operation complete. self.success_flag is checked by
        #   mainapp.TartubeApp.update_manager_finished()
        if not self.stderr_list:
            self.success_flag = True

        # Show a confirmation in the the Output tab (or wizard window textview)
        self.install_matplotlib_write_output(_('Update operation finished'))

        # Let the timer run for a few more seconds to prevent Gtk errors
        GObject.timeout_add(
            0,
            self.app_obj.update_manager_halt_timer,
        )


    def install_matplotlib_write_output(self, msg, system_cmd_flag=False):

        """Called by self.install_matplotlib().

        Writes a message to the Output tab (or to the setup wizard window, if
        called from there).

        Args:

            msg (str): The message to display

            system_cmd_flag (bool): If True, display system commands in a
                different colour in the Output tab (ignored when writing in
                the setup wizard window)

        """

        if not system_cmd_flag:
            GObject.timeout_add(
                0,
                self.app_obj.main_win_obj.output_tab_write_stdout,
                1,
                msg,
            )

        else:
            GObject.timeout_add(
                0,
                self.app_obj.main_win_obj.output_tab_write_system_cmd,
                1,
                msg,
            )


    def install_streamlink(self):

        """Called by self.run().

        A modified version of self.install_ytdl, that installs streamlink on an
        MS Windows system.

        Creates a child process to run the installation process.

        Reads from the child process STDOUT and STDERR, and calls the main
        application with the result of the update (success or failure).
        """

        # Show information about the update operation in the Output tab
        self.install_streamlink_write_output(
            _('Starting update operation, installing streamlink'),
        )

        # Create a new child process to install either the 64-bit or 32-bit
        #   version of streamlink, as appropriate
        if sys.maxsize <= 2147483647:
            binary = 'mingw-w64-i686-streamlink'
        else:
            binary = 'mingw-w64-x86_64-streamlink'

        # Prepare a system command...
        cmd_list = ['pacman', '-S', binary, '--noconfirm']
        # ...and display it in the Output tab (if required)
        self.install_streamlink_write_output(
            ' '.join(cmd_list),
            True,                   # A system command, not a message
        )

        # Create a new child process using that command...
        self.create_child_process(cmd_list)
        # ...and set up the PipeReader objects to read from the child process
        #   STDOUT and STDERR
        if self.child_process is not None:
            self.stdout_reader.attach_fh(self.child_process.stdout)
            self.stderr_reader.attach_fh(self.child_process.stderr)

        while self.is_child_process_alive():

            # Pause a moment between each iteration of the loop (we don't want
            #   to hog system resources)
            time.sleep(self.sleep_time)

            # Read from the child process STDOUT and STDERR, in the correct
            #   order, until there is nothing left to read
            while self.read_streamlink_child_process():
                pass

        # (Generate our own error messages for debugging purposes, in certain
        #   situations)
        if self.child_process is None:
            self.stderr_list.append(_('streamlink installation did not start'))

        elif self.child_process.returncode > 0:
            self.stderr_list.append(
                _('Child process exited with non-zero code: {}').format(
                    self.child_process.returncode,
                )
            )

        # Operation complete. self.success_flag is checked by
        #   mainapp.TartubeApp.update_manager_finished()
        if not self.stderr_list:
            self.success_flag = True

        # Show a confirmation in the the Output tab (or wizard window textview)
        self.install_streamlink_write_output(_('Update operation finished'))

        # Let the timer run for a few more seconds to prevent Gtk errors
        GObject.timeout_add(
            0,
            self.app_obj.update_manager_halt_timer,
        )


    def install_streamlink_write_output(self, msg, system_cmd_flag=False):

        """Called by self.install_streamlink().

        Writes a message to the Output tab (or to the setup wizard window, if
        called from there).

        Args:

            msg (str): The message to display

            system_cmd_flag (bool): If True, display system commands in a
                different colour in the Output tab (ignored when writing in
                the setup wizard window)

        """

        if not system_cmd_flag:
            GObject.timeout_add(
                0,
                self.app_obj.main_win_obj.output_tab_write_stdout,
                1,
                msg,
            )

        else:
            GObject.timeout_add(
                0,
                self.app_obj.main_win_obj.output_tab_write_system_cmd,
                1,
                msg,
            )


    def install_ytdl(self):

        """Called by self.run().

        Based on code from downloads.VideoDownloader.do_download().

        Creates a child process to run the youtube-dl update.

        Reads from the child process STDOUT and STDERR, and calls the main
        application with the result of the update (success or failure).
        """

        # Show information about the update operation in the Output tab (or in
        #   the setup wizard window, if called from there)
        downloader = self.app_obj.get_downloader(self.wiz_win_obj)
        self.install_ytdl_write_output(
            _('Starting update operation, installing/updating ' + downloader),
        )

        # Prepare the system command

        # The user can change the system command for updating youtube-dl,
        #   depending on how it was installed
        # (For example, if youtube-dl was installed via pip, then it must be
        #   updated via pip)
        if self.wiz_win_obj \
        and self.wiz_win_obj.ytdl_update_current is not None:
            ytdl_update_current = self.wiz_win_obj.ytdl_update_current
        else:
            ytdl_update_current = self.app_obj.ytdl_update_current

        # Special case: install yt-dlp with no dependencies, if required
        if (
            (
                not self.wiz_win_obj \
                and self.app_obj.ytdl_fork == 'yt-dlp' \
                and self.app_obj.ytdl_fork_no_dependency_flag
            ) or (
                self.wiz_win_obj \
                and self.wiz_win_obj.ytdl_fork == 'yt-dlp' \
                and self.wiz_win_obj.ytdl_fork_no_dependency_flag
            )
        ):
            if ytdl_update_current == 'ytdl_update_pip':
                ytdl_update_current = 'ytdl_update_pip_no_dependencies'

            elif ytdl_update_current == 'ytdl_update_pip3' \
            or ytdl_update_current == 'ytdl_update_pip3_recommend':
                ytdl_update_current = 'ytdl_update_pip3_no_dependencies'

            elif ytdl_update_current == 'ytdl_update_win_64':
                ytdl_update_current = 'ytdl_update_win_64_no_dependencies'

            elif ytdl_update_current == 'ytdl_update_win_32':
                ytdl_update_current = 'ytdl_update_win_32_no_dependencies'

        # Prepare a system command...
        if os.name == 'nt' \
        and ytdl_update_current == 'ytdl_update_custom_path' \
        and re.search('\.exe$', self.app_obj.ytdl_path):
            # Special case: on MS Windows, a custom path may point at an .exe,
            #   therefore 'python3' must be removed from the system command
            #   (we can't run 'python3.exe youtube-dl.exe' or anything like
            #   that)
            cmd_list = [self.app_obj.ytdl_path, '-U']

        else:
            cmd_list = self.app_obj.ytdl_update_dict[ytdl_update_current]

        mod_list = []
        for arg in cmd_list:

            # Substitute in the fork, if one is specified
            arg = self.app_obj.check_downloader(arg, self.wiz_win_obj)
            # Convert a path beginning with ~ (not on MS Windows)
            if os.name != 'nt':
                arg = re.sub('^\~', os.path.expanduser('~'), arg)

            mod_list.append(arg)

        # ...and display it in the Output tab (if required)
        self.install_ytdl_write_output(
            ' '.join(mod_list),
            True,                   # A system command, not a message
        )

        # Create a new child process using that command...
        self.create_child_process(mod_list)
        # ...and set up the PipeReader objects to read from the child process
        #   STDOUT and STDERR
        if self.child_process is not None:
            self.stdout_reader.attach_fh(self.child_process.stdout)
            self.stderr_reader.attach_fh(self.child_process.stderr)

        while self.is_child_process_alive():

            # Pause a moment between each iteration of the loop (we don't want
            #   to hog system resources)
            time.sleep(self.sleep_time)

            # Read from the child process STDOUT and STDERR, in the correct
            #   order, until there is nothing left to read
            while self.read_ytdl_child_process(downloader):
                pass

        # (Generate our own error messages for debugging purposes, in certain
        #   situations)
        if self.child_process is None:

            msg = _('Update did not start')

            self.stderr_list.append(msg)
            self.install_ytdl_write_output(msg)

        elif self.child_process.returncode > 0:

            msg = _('Child process exited with non-zero code: {}').format(
                self.child_process.returncode,
            )

            self.stderr_list.append(msg)
            self.install_ytdl_write_output(msg)

        # Operation complete. self.success_flag is checked by
        #   mainapp.TartubeApp.update_manager_finished
        if not self.stderr_list:
            self.success_flag = True

        # Show a confirmation in the the Output tab (or wizard window textview)
        self.install_ytdl_write_output(_('Update operation finished'))

        # Let the timer run for a few more seconds to prevent Gtk errors (for
        #   systems with Gtk < 3.24)
        GObject.timeout_add(
            0,
            self.app_obj.update_manager_halt_timer,
        )


    def install_ytdl_write_output(self, msg, system_cmd_flag=False):

        """Called by self.install_ytdl().

        Writes a message to the Output tab (or to the setup wizard window, if
        called from there).

        Args:

            msg (str): The message to display

            system_cmd_flag (bool): If True, display system commands in a
                different colour in the Output tab (ignored when writing in
                the setup wizard window)

        """

        if not self.wiz_win_obj:

            if not system_cmd_flag:
                self.app_obj.main_win_obj.output_tab_write_stdout(1, msg)
            else:
                self.app_obj.main_win_obj.output_tab_write_system_cmd(1, msg)

        else:

            GObject.timeout_add(
                0,
                self.wiz_win_obj.downloader_page_write,
                msg,
            )


    def intercept_version_from_stdout(self, stdout, downloader):

        """Called by self.install_yt_dl() only.

        Check a STDOUT message, hoping to intercept the new youtube-dl version
        number.

        Args:

            stdout (str): The STDOUT message

            downloader (str): The name of the downloader, e.g. 'yt-dlp'

        """

        regex_list = [
            'Requirement already up\-to\-date\: ' + downloader \
            + ' in .*\(([^\(\)]+)\)\s*$',
            'Requirement already satisfied\: ' + downloader \
            + ' in .*\(([^\(\)]+)\)\s*$',
            'yt-dlp is up to date \(([^\(\)]+)\)\s*$',
            'Successfully installed ' + downloader + '\-([^\(\)]+)\s*$',
        ]

        for regex in regex_list:
            substring = re.search(regex, stdout)
            if substring:
                self.ytdl_version = substring.group(1)
                return


    def is_child_process_alive(self):

        """Called by self.install_ffmpeg(), .install_matplotlib(),
        .install_streamlink(), .install_ytdl() and .stop_update_operation().

        Based on code from downloads.VideoDownloader.is_child_process_alive().

        Called continuously during the self.run() loop to check whether the
        child process has finished or not.

        Return values:

            True if the child process is alive, otherwise returns False.

        """

        if self.child_process is None:
            return False

        return self.child_process.poll() is None


    def read_ffmpeg_child_process(self):

        """Called by self.install_ffmpeg().

        Reads from the child process STDOUT and STDERR, in the correct order.

        Return values:

            True if either STDOUT or STDERR were read, None if both queues were
                empty

        """

        # mini_list is in the form [time, pipe_type, data]
        try:
            mini_list = self.queue.get_nowait()

        except:
            # Nothing left to read
            return None

        # Failsafe check
        if not mini_list \
        or (mini_list[1] != 'stdout' and mini_list[1] != 'stderr'):

            # Just in case...
            GObject.timeout_add(
                0,
                self.app_obj.system_error,
                701,
                'Malformed STDOUT or STDERR data',
            )

        # STDOUT or STDERR has been read
        data = mini_list[2].rstrip()
        # On MS Windows we use cp1252, so that Tartube can communicate with the
        #   Windows console
        data = data.decode(utils.get_encoding(), 'replace')

        # STDOUT
        if mini_list[1] == 'stdout':

            # Show command line output in the Output tab (or wizard window
            #   textview)
            self.install_ffmpeg_write_output(data)

        # STDERR
        else:

            # Ignore pacman warning messages, e.g. 'warning: dependency cycle
            #   detected:'
            if data and not re.search('^warning\:', data):

                self.stderr_list.append(data)

                # Show command line output in the Output tab (or wizard window
                #   textview)
                self.install_ffmpeg_write_output(data)

        # Either (or both) of STDOUT and STDERR were non-empty
        self.queue.task_done()
        return True


    def read_matplotlib_child_process(self):

        """Called by self.install_matplotlib().

        Reads from the child process STDOUT and STDERR, in the correct order.

        Return values:

            True if either STDOUT or STDERR were read, None if both queues were
                empty

        """

        # mini_list is in the form [time, pipe_type, data]
        try:
            mini_list = self.queue.get_nowait()

        except:
            # Nothing left to read
            return None

        # Failsafe check
        if not mini_list \
        or (mini_list[1] != 'stdout' and mini_list[1] != 'stderr'):

            # Just in case...
            GObject.timeout_add(
                0,
                self.app_obj.system_error,
                702,
                'Malformed STDOUT or STDERR data',
            )

        # STDOUT or STDERR has been read
        data = mini_list[2].rstrip()
        # On MS Windows we use cp1252, so that Tartube can communicate with the
        #   Windows console
        data = data.decode(utils.get_encoding(), 'replace')

        # STDOUT
        if mini_list[1] == 'stdout':

            # Show command line output in the Output tab (or wizard window
            #   textview)
            self.install_matplotlib_write_output(data)

        # STDERR
        else:

            # Ignore pacman warning messages, e.g. 'warning: dependency cycle
            #   detected:'
            if data and not re.search('^warning\:', data):

                self.stderr_list.append(data)

                # Show command line output in the Output tab (or wizard window
                #   textview)
                self.install_matplotlib_write_output(data)

        # Either (or both) of STDOUT and STDERR were non-empty
        self.queue.task_done()
        return True


    def read_streamlink_child_process(self):

        """Called by self.install_matplotlib().

        Reads from the child process STDOUT and STDERR, in the correct order.

        Return values:

            True if either STDOUT or STDERR were read, None if both queues were
                empty

        """

        # mini_list is in the form [time, pipe_type, data]
        try:
            mini_list = self.queue.get_nowait()

        except:
            # Nothing left to read
            return None

        # Failsafe check
        if not mini_list \
        or (mini_list[1] != 'stdout' and mini_list[1] != 'stderr'):

            # Just in case...
            GObject.timeout_add(
                0,
                self.app_obj.system_error,
                703,
                'Malformed STDOUT or STDERR data',
            )

        # STDOUT or STDERR has been read
        data = mini_list[2].rstrip()
        # On MS Windows we use cp1252, so that Tartube can communicate with the
        #   Windows console
        data = data.decode(utils.get_encoding(), 'replace')

        # STDOUT
        if mini_list[1] == 'stdout':

            # Show command line output in the Output tab (or wizard window
            #   textview)
            self.install_streamlink_write_output(data)

        # STDERR
        else:

            # Ignore pacman warning messages, e.g. 'warning: dependency cycle
            #   detected:'
            if data and not re.search('^warning\:', data):

                self.stderr_list.append(data)

                # Show command line output in the Output tab (or wizard window
                #   textview)
                self.install_streamlink_write_output(data)

        # Either (or both) of STDOUT and STDERR were non-empty
        self.queue.task_done()
        return True


    def read_ytdl_child_process(self, downloader):

        """Called by self.install_ytdl().

        Reads from the child process STDOUT and STDERR, in the correct order.

        Args:

            downloader (str): e.g. 'youtube-dl'

        Return values:

            True if either STDOUT or STDERR were read, None if both queues were
                empty

        """

        # mini_list is in the form [time, pipe_type, data]
        try:
            mini_list = self.queue.get_nowait()

        except:
            # Nothing left to read
            return None

        # Failsafe check
        if not mini_list \
        or (mini_list[1] != 'stdout' and mini_list[1] != 'stderr'):

            # Just in case...
            GObject.timeout_add(
                0,
                self.app_obj.system_error,
                704,
                'Malformed STDOUT or STDERR data',
            )

        # STDOUT or STDERR has been read
        data = mini_list[2].rstrip()
        # On MS Windows we use cp1252, so that Tartube can communicate with the
        #   Windows console
        data = data.decode(utils.get_encoding(), 'replace')

        # STDOUT
        if mini_list[1] == 'stdout':

            # "It looks like you installed youtube-dl with a package manager,
            #   pip, setup.py or a tarball. Please use that to update."
            # "The script youtube-dl is installed in '...' which is not on
            #   PATH. Consider adding this directory to PATH..."
            if re.search('It looks like you installed', data) \
            or re.search(
                'The script ' + downloader + ' is installed',
                data,
            ):
                self.stderr_list.append(data)

            else:

                # Try to intercept the new version number for youtube-dl
                self.intercept_version_from_stdout(data, downloader)
                self.stdout_list.append(data)

            # Show command line output in the Output tab (or wizard window
            #   textview)
            self.install_ytdl_write_output(data)

        # STDERR
        else:

            # If the user has pip installed, rather than pip3, they will by now
            #   (mid-2019) be seeing a Python 2.7 deprecation warning. Ignore
            #   that message, if received
            # If a newer version of pip is available, the user will see a
            #   'You should consider upgrading' warning. Ignore that too, if
            #   received
            if not re.search('DEPRECATION', data) \
            and not re.search('You are using pip version', data) \
            and not re.search('You should consider upgrading', data):
                self.stderr_list.append(data)

            # Show command line output in the Output tab (or wizard window
            #   textview)
            self.install_ytdl_write_output(data)

        # Either (or both) of STDOUT and STDERR were non-empty
        self.queue.task_done()
        return True


    def stop_update_operation(self):

        """Called by mainapp.TartubeApp.do_shutdown(), .stop_continue(),
        .on_button_stop_operation() and mainwin.MainWin.on_stop_menu_item().

        Based on code from downloads.VideoDownloader.stop().

        Terminates the child process.
        """

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
