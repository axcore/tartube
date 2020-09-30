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


# Import our modules
import downloads
import utils
# Use same gettext translations
from mainapp import _


# Classes


class UpdateManager(threading.Thread):

    """Called by mainapp.TartubeApp.update_manager_start().

    Python class to create a system child process, to do one of two jobs:

    1. Install FFmpeg (on MS Windows only)

    2. Install youtube-dl, or update it to its most recent version.

    Reads from the child process STDOUT and STDERR, having set up a
    downloads.PipeReader object to do so in an asynchronous way.

    Args:

        app_obj (mainapp.TartubeApp): The main application

        update_type (str): 'ffmpeg' to install FFmpeg (on MS Windows only), or
            'ytdl' to install/update youtube-dl

    """


    # Standard class methods


    def __init__(self, app_obj, update_type):

        super(UpdateManager, self).__init__()

        # IV list - class objects
        # -----------------------
        # The mainapp.TartubeApp object
        self.app_obj = app_obj

        # This object reads from the child process STDOUT and STDERR in an
        #   asynchronous way
        # Standard Python synchronised queue classes
        self.stdout_queue = queue.Queue()
        self.stderr_queue = queue.Queue()
        # The downloads.PipeReader objects created to handle reading from the
        #   pipes
        self.stdout_reader = downloads.PipeReader(self.stdout_queue)
        self.stderr_reader = downloads.PipeReader(self.stderr_queue)

        # The child process created by self.create_child_process()
        self.child_process = None


        # IV list - other
        # ---------------
        # 'ffmpeg' to install FFmpeg (on MS Windows only), or 'ytdl' to
        #   install/update youtube-dl
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
        else:
            self.install_ytdl()


    def create_child_process(self, cmd_list):

        """Called by self.install_ffmpeg() or .install_ytdl().

        Based on code from downloads.VideoDownloader.create_child_process().

        Executes the system command, creating a new child process which
        executes youtube-dl.

        Args:

            cmd_list (list): Python list that contains the command to execute.

        """

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

        # Show information about the update operation in the Output Tab
        self.app_obj.main_win_obj.output_tab_write_stdout(
            1,
            _('Starting update operation, installing FFmpeg'),
        )

        # Create a new child process to install either the 64-bit or 32-bit
        #   version of FFmpeg, as appropriate
        if sys.maxsize <= 2147483647:
            binary = 'mingw-w64-i686-ffmpeg'
        else:
            binary = 'mingw-w64-x86_64-ffmpeg'

        self.create_child_process(
            ['pacman', '-S', binary, '--noconfirm'],
        )

        # Show the system command in the Output Tab
        space = ' '
        self.app_obj.main_win_obj.output_tab_write_system_cmd(
            1,
            space.join( ['pacman', '-S', binary, '--noconfirm'] ),
        )

        # So that we can read from the child process STDOUT and STDERR, attach
        #   a file descriptor to the PipeReader objects
        if self.child_process is not None:

            self.stdout_reader.attach_file_descriptor(
                self.child_process.stdout,
            )

            self.stderr_reader.attach_file_descriptor(
                self.child_process.stderr,
            )

        while self.is_child_process_alive():

            # Read from the child process STDOUT, and convert into unicode for
            #   Python's convenience
            while not self.stdout_queue.empty():

                stdout = self.stdout_queue.get_nowait().rstrip()
                stdout = stdout.decode('cp1252')

                if stdout:

                    # Show command line output in the Output Tab
                    self.app_obj.main_win_obj.output_tab_write_stdout(
                        1,
                        stdout,
                    )

        # The child process has finished
        while not self.stderr_queue.empty():

            # Read from the child process STDERR queue (we don't need to read
            #   it in real time), and convert into unicode for python's
            #   convenience
            stderr = self.stderr_queue.get_nowait().rstrip()
            stderr = stderr.decode('cp1252')

            # Ignore pacman warning messages, e.g. 'warning: dependency cycle
            #   detected:'
            if stderr and not re.match('warning\:', stderr):

                self.stderr_list.append(stderr)

                # Show command line output in the Output Tab
                self.app_obj.main_win_obj.output_tab_write_stdout(
                    1,
                    stderr,
                )

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
        #   mainapp.TartubeApp.update_manager_finished
        if not self.stderr_list:
            self.success_flag = True

        # Show a confirmation in the the Output Tab
        self.app_obj.main_win_obj.output_tab_write_stdout(
            1,
            _('Update operation finished'),
        )

        # Let the timer run for a few more seconds to prevent Gtk errors (for
        #   systems with Gtk < 3.24)
        GObject.timeout_add(
            0,
            self.app_obj.update_manager_halt_timer,
        )


    def install_ytdl(self):

        """Called by self.run().

        Based on code from downloads.VideoDownloader.do_download().

        Creates a child process to run the youtube-dl update.

        Reads from the child process STDOUT and STDERR, and calls the main
        application with the result of the update (success or failure).
        """

        # Show information about the update operation in the Output Tab
        downloader = self.app_obj.get_downloader()
        self.app_obj.main_win_obj.output_tab_write_stdout(
            1,
            _('Starting update operation, installing/updating ' + downloader),
        )

        # Prepare the system command

        # The user can change the system command for updating youtube-dl,
        #   depending on how it was installed
        # (For example, if youtube-dl was installed via pip, then it must be
        #   updated via pip)
        cmd_list \
        = self.app_obj.ytdl_update_dict[self.app_obj.ytdl_update_current]

        mod_list = []
        for arg in cmd_list:

            # Substitute in the fork, if one is specified
            arg = self.app_obj.check_downloader(arg)
            # Convert a path beginning with ~ (not on MS Windows)
            if os.name != 'nt':
                arg = re.sub('^\~', os.path.expanduser('~'), arg)

            mod_list.append(arg)

        # Create a new child process using that command
        self.create_child_process(mod_list)

        # Show the system command in the Output Tab
        space = ' '
        self.app_obj.main_win_obj.output_tab_write_system_cmd(
            1,
            space.join(mod_list),
        )

        # So that we can read from the child process STDOUT and STDERR, attach
        #   a file descriptor to the PipeReader objects
        if self.child_process is not None:

            self.stdout_reader.attach_file_descriptor(
                self.child_process.stdout,
            )

            self.stderr_reader.attach_file_descriptor(
                self.child_process.stderr,
            )

        while self.is_child_process_alive():

            # Read from the child process STDOUT, and convert into unicode for
            #   Python's convenience
            while not self.stdout_queue.empty():

                stdout = self.stdout_queue.get_nowait().rstrip()
                if stdout:

                    if os.name == 'nt':
                        stdout = stdout.decode('cp1252')
                    else:
                        stdout = stdout.decode('utf-8')

                    # "It looks like you installed youtube-dl with a package
                    #   manager, pip, setup.py or a tarball. Please use that to
                    #   update."
                    # "The script youtube-dl is installed in '...' which is not
                    #   on PATH. Consider adding this directory to PATH..."
                    if re.search('It looks like you installed', stdout) \
                    or re.search(
                        'The script ' + downloader + ' is installed',
                        stdout,
                    ):
                        self.stderr_list.append(stdout)

                    else:

                        # Try to intercept the new version number for
                        #   youtube-dl
                        self.intercept_version_from_stdout(stdout)
                        self.stdout_list.append(stdout)

                    # Show command line output in the Output Tab
                    self.app_obj.main_win_obj.output_tab_write_stdout(
                        1,
                        stdout,
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

            if stderr:

                # If the user has pip installed, rather than pip3, they will by
                #   now (mid-2019) be seeing a Python 2.7 deprecation warning.
                #   Ignore that message, if received
                # If a newer version of pip is available, the user will see a
                #   'You should consider upgrading' warning. Ignore that too,
                #   if received
                if not re.search('DEPRECATION', stderr) \
                and not re.search('You are using pip version', stderr) \
                and not re.search('You should consider upgrading', stderr):
                    self.stderr_list.append(stderr)

                # Show command line output in the Output Tab
                self.app_obj.main_win_obj.output_tab_write_stdout(
                    1,
                    stderr,
                )

        # (Generate our own error messages for debugging purposes, in certain
        #   situations)
        if self.child_process is None:

            msg = _('Update did not start')
            self.stderr_list.append(msg)
            self.app_obj.main_win_obj.output_tab_write_stdout(
                1,
                msg,
            )

        elif self.child_process.returncode > 0:

            msg = _('Child process exited with non-zero code: {}').format(
                self.child_process.returncode,
            )
            self.app_obj.main_win_obj.output_tab_write_stdout(
                1,
                msg,
            )

        # Operation complete. self.success_flag is checked by
        #   mainapp.TartubeApp.update_manager_finished
        if not self.stderr_list:
            self.success_flag = True

        # Show a confirmation in the the Output Tab
        self.app_obj.main_win_obj.output_tab_write_stdout(
            1,
            _('Update operation finished'),
        )

        # Let the timer run for a few more seconds to prevent Gtk errors (for
        #   systems with Gtk < 3.24)
        GObject.timeout_add(
            0,
            self.app_obj.update_manager_halt_timer,
        )


    def intercept_version_from_stdout(self, stdout):

        """Called by self.install_yt_dl() only.

        Check a STDOUT message, hoping to intercept the new youtube-dl version
        number.

        Args:

            stdout (str): The STDOUT message

        """

        substring = re.search(
            'Requirement already up\-to\-date.*\(([\d\.]+)\)\s*$',
            stdout,
        )

        if substring:
            self.ytdl_version = substring.group(1)

        else:
            substring = re.search(
                'Successfully installed youtube\-dl\-([\d\.]+)\s*$',
                stdout,
            )

            if substring:
                self.ytdl_version = substring.group(1)


    def is_child_process_alive(self):

        """Called by self.install_ffmpeg(), .install_ytdl() and
        .stop_update_operation().

        Based on code from downloads.VideoDownloader.is_child_process_alive().

        Called continuously during the self.run() loop to check whether the
        child process has finished or not.

        Returns:

            True if the child process is alive, otherwise returns False.

        """

        if self.child_process is None:
            return False

        return self.child_process.poll() is None


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
