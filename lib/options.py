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


"""Module that contains a class storing download options."""


# Import Gtk modules
#   ...


# Import other modules
import os


# Import our modules
from . import formats
from . import mainapp
from . import media
from . import utils


# Classes


class OptionsManager(object):

    """Partially based on the OptionsManager class in youtube-dl-gui.

    This class handles settings for downloading media. Unlike youtube-dl-gui,
    which has one group of download options applied to all downloads, this
    object can be applied to any of the media data classes in media.py (so it
    can be applied to a single video, or a whole channel, or generally to all
    downloads).

    Tartube's options.OptionsManager implements a subset of options implemented
    by the equivalent class in youtube-dl-gui.

    Options are listed here in the same order in which they appear in
    youtube-dl's documentation.

    OPTIONS

        ignore_errors (boolean): If True, youtube-dl will ignore the errors and
        continue the download operation

    NETWORK OPTIONS

        proxy (string): Use the specified HTTP/HTTPS proxy

    GEO-RESTRICTION

        (none implemented)

    VIDEO SELECTION

        playlist_start (int): Playlist index to start downloading

        playlist_end (int): Playlist index to stop downloading

        max_downloads (int): Maximum number of video files to download from the
            given playlist

        min_filesize (float): Minimum file size of the video file. If the video
            file is smaller than the given size then youtube-dl will abort the
            download operation

        max_filesize (float): Maximum file size of the video file. If the video
            file is larger than the given size then youtube-dl will abort the
            download operation

    DOWNLOAD OPTIONS

        limit_rate (string): Bandwidth limit, in bytes (example strings: 50K or
            4.2M) (not implemented by youtube-dl-gui)
        NB: Can't be directly modified by user

        retries (int): Number of youtube-dl retries

        native_hls (boolean): When True, youtube-dl will prefer the native HLS
            (HTTP Live Streaming) implementation (rather than prefering FFmpeg,
            which is at the current time the better downloader for general
            compatibility)

    FILESYSTEM OPTIONS

        save_path (string): Path where youtube-dl should store the
            downloaded file. The default is supplied by the media data object
        NB: Can't be directly modified by user

        restrict_filenames (boolean): If True, youtube-dl will restrict the
            downloaded file's filename to ASCII characters only

        nomtime (boolean): When True will not use the last-modified header to
            set the file modification time (i.e., use the time at which the
            server believes the resources was last modified)

        write_description (boolean): If True, youtube-dl will write video
            description to a .description file

        write_info (boolean): If True, youtube-dl will write video metadata to
            an .info.json file

    THUMBNAIL IMAGES

        write_thumbnail (boolean): If True youtube-dl will write thumbnail
            image to disk

    VERBOSITY / SIMULATION OPTIONS

        youtube_dl_debug (boolean): When True, will pass '-v' flag to
            youtube-dl

    WORKAROUNDS

        user_agent (string): Specify a custom user agent for youtube-dl

        referer (string): Specify a custom referer to use if the video access
            is restricted to one domain

    VIDEO FORMAT OPTIONS

        video_format (string): Video format to download. When this option is
            set to '0' youtube-dl will choose the best video format available
            for the given URL. Otherwise, this option is set to one of the
            keys in formats.VIDEO_FORMAT_DICT, in which case youtube-dl will
            use the corresponding value to select the video format. See also
            the options 'second_video_format' and 'third_video_format'.

    SUBTITLE OPTIONS

        write_subs (boolean): If True, youtube-dl will try to download the
            subtitles file for the given URL

        write_auto_subs (boolean): If True, youtube-dl will try to download the
            automatic subtitles file for the given URL

        write_all_subs (boolean): If True, youtube-dl will try to download all
            the available subtitles files for the given URL

        subs_lang (string): Language of the subtitles file to download.
            Requires the 'write_subs' option

    AUTHENTIFICATION OPTIONS

        username (string): Username to login with

        password (string): Password to login with

        video_password (string): Video password for the given URL

    ADOBE PASS OPTIONS

        (none implemented)

    POST-PROCESSING OPTIONS

        to_audio (boolean): If True, youtube-dl will post-process the video
            file

        audio_format (string): Audio format of the post-processed file.
            Available values are 'mp3', 'wav', 'aac', 'm4a', 'vorbis', 'opus' &
            'flac'

        audio_quality (string): Audio quality of the post-processed file.
            Available values are '9', '5', '0'. The lowest the value the better
            the quality

        keep_video (boolean): If True, youtube-dl will keep the video file
            after post-processing it

        embed_subs (boolean): If True, youtube-dl will merge the subtitles file
            with the video (only for .mp4 files)

        embed_thumbnail (boolean): When True will embed the thumbnail in the
            audio file as cover art

        add_metadata (boolean): When True will write metadata to the video file

    YOUTUBE-DL-GUI OPTIONS (not passed to youtube-dl directly)

        [used to build the 'save_path' option]

        output_format (int): Option in the range 0-5, which is converted into
            a youtube-dl output template using
            formats.FILE_OUTPUT_CONVERT_DICT. If the value is 3, then the
            custom 'output_template' is used instead

        output_template (string): Can be any output template supported by
            youtube-dl. Ignored if 'output_format' is not 3

        [used to modify the 'video_format' option]

        second_video_format (string): Video format to download, if the format
            specified by the 'video_format' option isn't available. This option
            is ignored when its value is '0' (or when the value of the
            'video_format' option is '0'). Otherwise, its value is one of the
            keys in formats.VIDEO_FORMAT_DICT

        third_video_format (string): Video format to download, if the formats
            specified by the 'video_format' and 'second_video_format' options
            aren't available. This option is ignored when its value is '0' (or
            when the value of the 'video_format' and 'second_video_format'
            options are '0'). Otherwise, its value is one of the keys in
            formats.VIDEO_FORMAT_DICT

        [used in conjunction with the 'min_filesize' and 'max_filesize' options

            max_filesize_unit (string): Maximum file size unit. Available
                values: '' (for bytes), 'k' (for kilobytes, etc), 'm', 'g',
                't', 'p', 'e', 'z', 'y'

            min_filesize_unit (string): Minimum file size unit. Available
                values as above

        [in youtube-dl-gui, this was named 'cmd_args']

        extra_cmd_string: String that contains extra youtube-dl options
            separated by spaces. Components containing whitespace can be
            enclosed within double quotes "..."

    TARTUBE OPTIONS (not passed to youtube-dl directly)

        keep_description (boolean):
        keep_info (boolean):
        keep_thumbnail (boolean):
            During a download operation (not simulated, e.g. when the user
            clicks the 'Download all' button), the video description/JSON/
            thumbnail files are downloaded only if 'write_description',
            'write_info' and/or 'write_thumbnail' are True

            They are initially stored in the same sub-directory in which
            Tartube will store the video

            If these options are True, they stay there; otherwise, they are
            copied into the equivalent location in Tartube's temporary
            directories. (In that case, currently only the thumbnail file is
            actually used by Tartube)

        sim_keep_description (boolean):
        sim_keep_info (boolean):
        sim_keep_thumbnail (boolean):
            During a download operation (simulated, e.g. when the user clicks
            the 'Check all' button), the video's JSON file is always loaded
            into memory

            If 'write_description' and 'sim_description' are both true, the
            description file is written directly to the sub-directory in which
            Tartube would store the video

            If 'write_description' is true but 'keep_description' not, the
            description file is written to the equivalent location in Tartube's
            temporary directories.

            The same applies to the JSON and thumbnail files.
    """


    # Standard class methods


    def __init__(self):

        # IV list - other
        # ---------------
        # Dictionary of download options for youtube-dl, set by a call to
        #   self.reset_options
        self.options_dict = {}


        # Code
        # ----

        # Initialise youtube-dl options
        self.reset_options()


    # Public class methods


    def reset_options(self):

        """Called by self.__init__().

        Resets (or initialises) self.options_dict to its default state.
        """

        self.options_dict = {
            # OPTIONS
            'ignore_errors': True,
            # NETWORK OPTIONS
            'proxy': '',
            # GEO-RESTRICTION
            #   (none implemented)
            # VIDEO SELECTION
            'playlist_start': 1,
            'playlist_end': 0,
            'max_downloads': 0,
            'min_filesize': 0,
            'max_filesize': 0,
            # DOWNLOAD OPTIONS
            'limit_rate': '',             # Can't be directly modified by user
            'retries': 10,
            'native_hls': True,
            # FILESYSTEM OPTIONS
            'save_path': None,             # Can't be directly modified by user
            'restrict_filenames': False,
            'nomtime': False,
            'write_description': True,
            'write_info': False,
            # THUMBNAIL IMAGES
            'write_thumbnail': True,
            # VERBOSITY / SIMULATION OPTIONS
            #   (none implemented)
            # WORKAROUNDS
            'user_agent': '',
            'referer': '',
            # VIDEO FORMAT OPTIONS
            'video_format': '0',
            # SUBTITLE OPTIONS
            'write_subs': False,
            'write_auto_subs': False,
            'write_all_subs': False,
            'subs_lang': 'en',
            # AUTHENTIFICATION OPTIONS
            'username': '',
            'password': '',
            'video_password': '',
            # ADOBE PASS OPTIONS
            #   (none implemented)
            # POST-PROCESSING OPTIONS
            'to_audio': False,
            'audio_format': '',
            'audio_quality': '5',
            'keep_video': False,
            'embed_subs': False,
            'embed_thumbnail': False,
            'add_metadata': False,
            # YOUTUBE-DL-GUI OPTIONS
            'output_format': 1,
            'output_template': os.path.abspath(
                os.path.join(
                    '%(uploader)s',
                    '%(title)s.%(ext)s',
                ),
            ),
            'second_video_format': '0',
            'third_video_format': '0',
            'max_filesize_unit' : '',
            'min_filesize_unit' : '',
            'extra_cmd_string' : '',
            # TARTUBE OPTIONS
           'keep_description': False,
           'keep_info': False,
           'keep_thumbnail': True,
           'sim_keep_description': False,
           'sim_keep_info': False,
           'sim_keep_thumbnail': True,
        }


class OptionsParser(object):

    """Called by downloads.DownloadManager.__init__().

    Each download operation, handled by the downloads.DownloadManager, creates
    an instance of this class.

    This object converts the download options specified by an
    options.OptionsManager object into a list of youtube-dl command line
    options, whenever required.

    Args:

        download_manager_obj (downloads.DownloadManager) - The parent
            download manager object

    """


    # Standard class methods


    def __init__(self, download_manager_obj):

        # IV list - class objects
        # -----------------------
        # The parent downloads.DownloadManager object
        self.download_manager_obj = download_manager_obj


        # IV list - other
        # ---------------
        # List of options.OptionHolder objects, with their initial settings
        # The options here are in the same order in which they appear in
        #   youtube-dl's options list
        self.option_holder_list = [
            # OPTIONS
            # -i, --ignore-errors
            OptionHolder('ignore_errors', '-i', False),
            # NETWORK OPTIONS
            # --proxy URL
            OptionHolder('proxy', '--proxy', ''),
            # GEO-RESTRICTION
            #   (none implemented)
            # VIDEO SELECTION
            # --playlist-start NUMBER
            OptionHolder('playlist_start', '--playlist-start', 1),
            # --playlist-end NUMBER
            OptionHolder('playlist_end', '--playlist-end', 0),
            # --max-downloads NUMBER
            OptionHolder('max_downloads', '--max-downloads', 0),
            # --min-filesize SIZE
            OptionHolder('min_filesize', '--min-filesize', 0),
            # --max-filesize SIZE
            OptionHolder('max_filesize', '--max-filesize', 0),
            # DOWNLOAD OPTIONS
            # -r, --limit-rate RATE
            OptionHolder('limit_rate', '-r', ''),
            # -R, --retries RETRIES
            OptionHolder('retries', '-R', 10),
            # --hls-prefer-native
            OptionHolder('native_hls', '--hls-prefer-native', False),
            # FILESYSTEM OPTIONS
            # -o, --output TEMPLATE
            OptionHolder('save_path', '-o', ''),
            # --restrict-filenames
            OptionHolder('restrict_filenames', '--restrict-filenames', False),
            # --no-mtime
            OptionHolder('nomtime', '--no-mtime', False),
            # --write-description
            OptionHolder('write_description', '--write-description', False),
            # --write-info-json
            OptionHolder('write_info', '--write-info-json', False),
            # THUMBNAIL IMAGES
            # --write-thumbnail
            OptionHolder('write_thumbnail', '--write-thumbnail', False),
            # VERBOSITY / SIMULATION OPTIONS
            #   (none implemented)
            # WORKAROUNDS
            # --user-agent UA
            OptionHolder('user_agent', '--user-agent', ''),
            # --referer URL
            OptionHolder('referer', '--referer', ''),
            # VIDEO FORMAT OPTIONS
            # -f, --format FORMAT
            OptionHolder('video_format', '-f', '0'),
            # SUBTITLE OPTIONS
            # --write-sub
            OptionHolder('write_subs', '--write-sub', False),
            # --write-auto-sub
            OptionHolder('write_auto_subs', '--write-auto-sub', False),
            # --all-subs
            OptionHolder('write_all_subs', '--all-subs', False),
            # --sub-lang LANGS
            OptionHolder('subs_lang', '--sub-lang', '', ['write_subs']),
            # AUTHENTIFICATION OPTIONS
            # -u, --username USERNAME
            OptionHolder('username', '-u', ''),
            # -p, --password PASSWORD
            OptionHolder('password', '-p', ''),
            # --video-password PASSWORD
            OptionHolder('video_password', '--video-password', ''),
            # ADOBE PASS OPTIONS
            #   (none implemented)
            # POST-PROCESSING OPTIONS
            # -x, --extract-audio
            OptionHolder('to_audio', '-x', False),
            # --audio-format FORMAT
            OptionHolder('audio_format', '--audio-format', ''),
            # --audio-quality QUALITY
            OptionHolder(
                'audio_quality',
                '--audio-quality',
                '5',
                ['to_audio'],
            ),
            # -k, --keep-video
            OptionHolder('keep_video', '-k', False),
            # --embed-subs
            OptionHolder(
                'embed_subs',
                '--embed-subs',
                False,
                ['write_auto_subs', 'write_subs'],
            ),
            # --embed-thumbnail
            OptionHolder('embed_thumbnail', '--embed-thumbnail', False),
            # --add-metadata
            OptionHolder('add_metadata', '--add-metadata', False),
            # YOUTUBE-DL-GUI OPTIONS (not given an options.OptionHolder object)
#           OptionHolder('output_format', '', 1),
#           OptionHolder('output_template', '', ''),
#           OptionHolder('second_video_format', '', '0'),
#           OptionHolder('third_video_format', '', '0'),
#           OptionHolder('max_filesize_unit', '', ''),
#           OptionHolder('min_filesize_unit', '', ''),
#           OptionHolder('extra_cmd_string', '', ''),
            # TARTUBE OPTIONS (not given an options.OptionHolder object)
#           OptionHolder('keep_description', '', False),
#           OptionHolder('keep_info', '', False),
#           OptionHolder('keep_thumbnail', '', False),
#           OptionHolder('sim_keep_description', '', False),
#           OptionHolder('sim_keep_info', '', False),
#           OptionHolder('sim_keep_thumbnail', '', False),
        ]


    # Public class methods


    def parse(self, download_item_obj, options_dict):

        """Called by downloads.DownloadWorker.prepare_download().

        Converts the download options stored in the specified
        options.OptionsManager object into a list of youtube-dl command line
        options.

        Args:

            download_item_obj (downloads.DownloadItem) - The object handling
                the download

            options_dict (dict): Python dictionary containing download options;
                taken from options.OptionsManager.options_dict

        Returns:

            List of strings with all the youtube-dl command line options

        """

        # Force youtube-dl's progress bar to be outputted as separate lines
        options_list = ['--newline']

        # Create a copy of the dictionary...
        copy_dict = options_dict.copy()
        # ...then modify various values in the copy. Set the 'save_path' option
        self.build_save_path(download_item_obj, copy_dict)
        # Set the 'video_format' option
        self.build_video_format(copy_dict)
        # Set the 'min_filesize' and 'max_filesize' options
        self.build_file_sizes(copy_dict)
        # Set the 'limit_rate' option
        self.build_limit_rate(copy_dict)

        # Reset the 'playlist_start', 'playlist_end' and 'max_downloads'
        #   options if we're not downloading a video in a playlist
        if (
            isinstance(download_item_obj.media_data_obj, media.Video) \
            and not isinstance(
                download_item_obj.media_data_obj.parent_obj,
                media.Playlist,
            )
        ) or not isinstance(download_item_obj.media_data_obj, media.Playlist):
            copy_dict['playlist_start'] = 1
            copy_dict['playlist_end'] = 0
            copy_dict['max_downloads'] = 0

        # Parse basic youtube-dl command line options
        for option_holder_obj in self.option_holder_list:

            # First deal with special cases...
            if option_holder_obj.name == 'to_audio':
                if copy_dict['audio_format'] == '':
                    value = copy_dict[option_holder_obj.name]

                    if value != option_holder_obj.default_value:
                        options_list.append(option_holder_obj.switch)

            elif option_holder_obj.name == 'audio_format':
                value = copy_dict[option_holder_obj.name]

                if value != option_holder_obj.default_value:
                    options_list.append('-x')
                    options_list.append(option_holder_obj.switch)
                    options_list.append(utils.to_string(value))

                    # The '-x' / '--audio-quality' switch must precede the
                    #   '--audio-quality' switch, if both are used
                    # Therefore, if the current value of the 'audio_quality'
                    #   option is not the default value ('5'), then insert the
                    #   '--audio-quality' switch into the options list right
                    #   now
                    if copy_dict['audio_quality'] != '5':
                        options_list.append('--audio-quality')
                        options_list.append(
                            utils.to_string(copy_dict['audio_quality']),
                        )

            elif option_holder_obj.name == 'audio_quality':
                # If the '--audio-quality' switch was not added by the code
                #   block just above, then follow the standard procedure
                if option_holder_obj.switch not in options_list:
                    if option_holder_obj.check_requirements(copy_dict):
                        value = copy_dict[option_holder_obj.name]

                        if value != option_holder_obj.default_value:
                            options_list.append(option_holder_obj.switch)
                            options_list.append(utils.to_string(value))

            # For all other options, just check the value is valid
            elif option_holder_obj.check_requirements(copy_dict):
                value = copy_dict[option_holder_obj.name]

                if value != option_holder_obj.default_value:
                    options_list.append(option_holder_obj.switch)

                    if not option_holder_obj.is_boolean():
                        options_list.append(utils.to_string(value))

        # Parse the 'extra_cmd_string' option, which can contain arguments
        #   inside double quotes "..." (arguments that can therefore contain
        #   whitespace)

        # Set a flag for an item beginning with double quotes, and reset it for
        #   an item ending in double quotes
        quote_flag = False
        # Temporary list to hold such quoted arguments
        quote_list = []

        for item in copy_dict['extra_cmd_string'].split():

            quote_flag = (quote_flag or item[0] == "\"")

            if quote_flag:
                quote_list.append(item)
            else:
                options_list.append(item)

            if quote_flag and item[-1] == "\"":

                # Special case mode is over. Append our special items to the
                #   options list
                options_list.append(" ".join(quote_list)[1:-1])

                quote_flag = False
                quote_list = []

        # Parsing complete
        return options_list


    def build_file_sizes(self, copy_dict):

        """Called by self.parse().

        Build the value of the 'min_filesize' and 'max_filesize' options and
        store them in the options dictionary.

        Args:
            copy_dict (dict): Copy of the original options dictionary.

        """

        if copy_dict['min_filesize']:
            copy_dict['min_filesize'] = \
            utils.to_string(copy_dict['min_filesize']) + \
            copy_dict['min_filesize_unit']

        if copy_dict['max_filesize']:
            copy_dict['max_filesize'] = \
            utils.to_string(copy_dict['max_filesize']) + \
            copy_dict['max_filesize_unit']


    def build_limit_rate(self, copy_dict):

        """Called by self.parse().

        Build the value of the 'limit_rate' option and store it in the options
        dictionary.

        Args:

            copy_dict (dict): Copy of the original options dictionary.

        """

        # Import the main app (for convenience)
        app_obj = self.download_manager_obj.app_obj

        # Set the bandwidth limit (e.g. '50K')
        if app_obj.bandwidth_apply_flag:

            # The bandwidth limit is divided equally between the workers
            limit = int(app_obj.bandwidth_default / app_obj.num_worker_default)
            copy_dict['limit_rate'] = str(limit) + 'K'


    def build_save_path(self, download_item_obj, copy_dict):

        """Called by self.parse().

        Build the value of the 'save_path' option and store it in the options
        dictionary.

        Args:

            download_item_obj (downloads.DownloadItem) - The object handling
                the download

            copy_dict (dict): Copy of the original options dictionary.

        """

        # Set the directory in which any downloaded videos will be saved
        media_data_obj = download_item_obj.media_data_obj
        if isinstance(media_data_obj, media.Video):
            save_path = media_data_obj.parent_obj.get_dir(
                self.download_manager_obj.app_obj
            )

        else:
            save_path = media_data_obj.get_dir(
                self.download_manager_obj.app_obj
            )

        # Set the youtube-dl output template for the video's file
        template = formats.FILE_OUTPUT_CONVERT_DICT[copy_dict['output_format']]
        # In the case of copy_dict['output_format'] = 3
        if template is None:
            template = copy_dict['output_template']

        copy_dict['save_path'] = os.path.abspath(
            os.path.join(save_path, template),
        )


    def build_video_format(self, copy_dict):

        """Called by self.parse().

        Build the value of the 'video_format' option and store it in the
        options dictionary.

        Args:
            copy_dict (dict): Copy of the original options dictionary.

        """

        if copy_dict['video_format'] != '0' and \
        copy_dict['second_video_format'] != '0':

            if copy_dict['third_video_format'] != '0':

                copy_dict['video_format'] = copy_dict['video_format'] + '+' \
                + copy_dict['second_video_format'] + '+' \
                + copy_dict['second_video_format']

            else:
                copy_dict['video_format'] = copy_dict['video_format'] + '+' \
                + copy_dict['second_video_format']


class OptionHolder(object):

    """Called from options.OptionsParser.__init__().

    The options parser object converts the download options specified by an
    options.OptionsManager object into a list of youtube-dl command line
    options, whenever required.

    Each option has a name, a command line switch, a default value and an
    optional list of requirements; they are stored together in an instance of
    this object.

    Args:

        name (string): Option name. Must be a valid option name
            from the optionsmanager.OptionsManager class (see the list in
            at the beginning of the options.OptionsManager class).

        switch (string): The option command line switch. See
            https://github.com/rg3/youtube-dl/#options

        default_value (any): The option default value. Must be the same type
            as the corresponding option from the optionsmanager.OptionsManager
            class.

        requirements (list): The requirements for the given option. This
            argument is a list of strings with the name of all the options
            that this specific option needs. If there are no requirements, the
            IV is set to None. (For example 'subs_lang' needs the 'write_subs'
            option to be enabled.)

    """


    # Standard class methods


    def __init__(self, name, switch, default_value, requirement_list=None):

        # IV list - other
        # ---------------
        self.name = name
        self.switch = switch
        self.default_value = default_value
        self.requirement_list = requirement_list


    # Public class methods


    def check_requirements(self, copy_dict):

        """Called by options.OptionsParser.parse().

        Check if options required by another option are enabled, or not.

        Args:

            copy_dict (dict): Copy of the original options dictionary.

        Returns:

            True if any of the required options is enabled, otherwise returns
                False.

        """

        if not self.requirement_list:
            return True

        return any([copy_dict[req] for req in self.requirement_list])


    def is_boolean(self):

        """Called by options.OptionsParser.parse().

        Returns:

            True if the option is a boolean switch, otherwise returns False

        """

        return type(self.default_value) is bool
