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
import subprocess
import sys
import threading


# Import our modules
from . import downloads
from . import utils


# Classes


class UpdateManager(threading.Thread):

    """Called by mainapp.TartubeApp.update_manager_start().

    Python class to create a system child process, in which we attempt to
    update youtube-dl to its most recent version.

    Reads from the child process STDOUT and STDERR, having set up a
    downloads.PipeReader object to do so in an asynchronous way.

    Args:

        app_obj (mainapp.TartubeApp): The main application

    """


    # Standard class methods


    def __init__(self, app_obj):

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

        # The youtube-dl version number as a string, if captured from the child
        #   process (e.g. '2019.07.02')
        self.ytdl_version = None


        # IV list - other
        # ---------------

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

        Based on code from downloads.VideoDownloader.do_download().

        Creates a child process to run the youtube-dl update.

        Reads from the child process STDOUT and STDERR, and calls the main
        application with the result of the update (success or failure).
        """

        # Prepare the system command

        # The user can change the system command for updating youtube-dl,
        #   depending on how it was installed
        # (For example, if youtube-dl was installed via pip, then it must be
        #   updated via pip)
        cmd_list \
        = self.app_obj.ytdl_update_dict[self.app_obj.ytdl_update_current]

        #  Create a new child process using that command
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
                    if re.search('It looks like you installed', stdout):
                        self.stderr_list.append(stdout)
                    else:
                        # Try to intercept the new version number for
                        #   youtube-dl
                        self.intercept_version_from_stdout(stdout)
                        self.stdout_list.append(stdout)

                        if (self.app_obj.ytdl_write_stdout_flag):
                            print(stdout)


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
                if not re.search('DEPRECATION', stderr):
                    self.stderr_list.append(stderr)

            if (self.app_obj.ytdl_write_stderr_flag):
                print(stderr)

        # (Generate our own error messages for debugging purposes, in certain
        #   situations)
        if self.child_process is None:
            self.stderr_list.append('youtube-dl update did not start')

        elif self.child_process.returncode > 0:
            self.stderr_list.append(
                'Child process exited with non-zero code: {}'.format(
                    self.child_process.returncode,
                )
            )

        # Operation complete; inform the main application of success or failure
        if self.stderr_list:

            GObject.timeout_add(
                0,
                self.app_obj.update_manager_finished,
                False,
                self.ytdl_version,
            )

        else:

            GObject.timeout_add(
                0,
                self.app_obj.update_manager_finished,
                True,
                self.ytdl_version,
            )


    def create_child_process(self, cmd_list):

        """Called by self.run().

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
            # (The code in self.run() will spot that the child process did not
            #   start)
            self.stderr_list.append('Child process did not start')


    def intercept_version_from_stdout(self, stdout):

        """Called by self.run().

        Check a STDOUT message, hoping to intercept the new youtube-dl version
        number.

        Args:

            stdout (string): The STDOUT message

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

        """Called by self.run() and self.stop_update_operation().

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

        """Called by mainapp.TartubeApp.on_button_stop_operation(), .stop() and
        a callback in .on_button_stop_operation().

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
