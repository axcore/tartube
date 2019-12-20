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
import formats
import mainapp
import media
import utils


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

        ignore_errors (bool): If True, youtube-dl will ignore the errors and
            continue the download operation

        abort_on_error (bool): If True, youtube-dl will abord downloading
            further playlist videos if an error occurs

    NETWORK OPTIONS

        proxy (str): Use the specified HTTP/HTTPS proxy

        socket_timeout (str): Time to wait before giving up, in seconds

        source_address (str): Client-side IP address to bind to

        force_ipv4 (str): Make all connections via IPv4

        force_ipv6 (str): Make all connections via IPv6

    GEO-RESTRICTION

        geo_verification_proxy (str): Use this proxy to verify the IP address
            for some geo-restricted sites

        geo_bypass (bool): Bypass geographic restriction via faking
            X-Forwarded-For HTTP header

        no_geo_bypass (bool): Do not bypass geographic restriction via faking
            X-Forwarded-For HTTP header

        geo_bypass_country (str): Force bypass geographic restriction with
            explicitly provided two-letter ISO 3166-2 country code

        geo_bypass_ip_block (str): Force bypass geographic restriction with
            explicitly provided IP block in CIDR notation

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

        date (str): Download only videos uploaded on this date (YYYYMMDD)

        date_before (str): Download only videos uploaded on or before this date
            (YYYYMMDD)

        date_after (str): Download only videos uploaded on or after this date
            (YYYYMMDD)

        min_views (int): Do not download any videos with fewer than this many
            views

        max_views (int): Do not download any videos with more than this many
            views

        match_filter (str): Generic video filter (see the comments in the
            youtube-dl documentation). Tartube automatically adds quotes to
            the beginning and end of the string

        age_limit (str): Download only videos suitable for the given age

        include_ads (bool): Download advertisements (experimental)

    DOWNLOAD OPTIONS

        limit_rate (str): Bandwidth limit, in bytes (example strings: 50K or
            4.2M) (not implemented by youtube-dl-gui)
        NB: Can't be directly modified by user

        retries (int): Number of youtube-dl retries

        playlist_reverse (bool): When True, download playlist videos in reverse
            order

        playlist_random (bool): When True, download playlist videos in random
            order

        native_hls (bool): When True, youtube-dl will prefer the native HLS
            (HTTP Live Streaming) implementation (rather than prefering FFmpeg,
            which is at the current time the better downloader for general
            compatibility)

        prefer_ffmpeg (bool): When True, youtube-dl will prefer FFmpeg

        external_downloader (str): Use the specified external downloaded.
            youtube-dl currently supports the strings 'aria2c', 'avconv',
            'axel', 'curl', 'ffmpeg', 'httpie', 'wget' (use an empty string to
            disable this option)

        external_arg_string (str): Arguments to pass to the external
            downloader. Tartube automatically adds quotes to the beginning and
            end of the string

    FILESYSTEM OPTIONS

        save_path (str): Path where youtube-dl should store the downloaded
            file. The default is supplied by the media data object
        NB: Can't be directly modified by user

        restrict_filenames (bool): If True, youtube-dl will restrict the
            downloaded file's filename to ASCII characters only

        nomtime (bool): When True will not use the last-modified header to set
            the file modification time (i.e., use the time at which the server
            believes the resources was last modified)

        write_description (bool): If True, youtube-dl will write video
            description to a .description file

        write_info (bool): If True, youtube-dl will write video metadata to an
            .info.json file

        write_annotations (bool): If True, youtube-dl will write video
            annotations to an .annotations.xml file

    THUMBNAIL IMAGES

        write_thumbnail (bool): If True youtube-dl will write thumbnail image
            to disc

    VERBOSITY / SIMULATION OPTIONS

        youtube_dl_debug (bool): When True, will pass '-v' flag to youtube-dl

    WORKAROUNDS

        force_encoding (str): Force the specified encoding

        no_check_certificate (bool): If True, suppress HTTPS certificate
            validation

        prefer_insecure (bool): If True, use an unencrypted connection to
            retrieve information about the video. (Currently supported only for
            YouTube)

        user_agent (str): Specify a custom user agent for youtube-dl

        referer (str): Specify a custom referer to use if the video access is
            restricted to one domain

    VIDEO FORMAT OPTIONS

        video_format (str): Video format to download. When this option is set
            to '0' youtube-dl will choose the best video format available for
            the given URL. Otherwise, this option is set to one of the keys in
            formats.VIDEO_FORMAT_DICT, in which case youtube-dl will use the
            corresponding value to select the video format. See also the
            options 'second_video_format' and 'third_video_format'.

        all_formats (bool): If True, download all available video formats

        prefer_free_formats (bool): If True, prefer free video formats unless
            one is specfied by video_format, etc

        yt_skip_dash (bool): If True, do not download DASh-related data with
            YouTube videos

        merge_output_format (str): If a merge is required (e.g.
            bestvideo+bestaudio), output to this container format. youtube-dl
            supports the strings 'mkv', 'mp4', 'ogg', 'webm', 'flv' (or an
            empty string to ignore this option)

    SUBTITLE OPTIONS

        write_subs (bool): If True, youtube-dl will try to download the
            subtitles file for the given URL

        write_auto_subs (bool): If True, youtube-dl will try to download the
            automatic subtitles file for the given URL

        write_all_subs (bool): If True, youtube-dl will try to download all the
            the available subtitles files for the given URL

        subs_format (str): Subtitle format preference. youtube-dl supports
            'srt', 'ass', 'vtt', 'lrc' or combinations thereof, e.g.
            'ass/srt/best'

        subs_lang (str): Language of the subtitles file to download. Requires
            the 'write_subs' option

    AUTHENTIFICATION OPTIONS

        username (str): Username to login with

        password (str): Password to login with

        two_factor (str): Two-factor authentification code

        net_rc (bool): If True, use .netrc authentification data

        video_password (str): Video password for the given URL

    ADOBE PASS OPTIONS

        (none implemented)

    POST-PROCESSING OPTIONS

        extract_audio (bool): If True, youtube-dl will post-process the video
            file

        audio_format (str): Audio format of the post-processed file. Available
            values are 'mp3', 'wav', 'aac', 'm4a', 'vorbis', 'opus' & 'flac'

        audio_quality (str): Audio quality of the post-processed file.
            Available values are '9', '5', '0'. The lowest the value the better
            the quality

        recode_video (str): Encode the video to another format if necessary.
            One of the strings 'avi', 'flv', 'mkv', 'mp4', 'ogg', 'webm', or an
            empty string if disabled

        pp_args (str): Give these arguments to the postprocessor. Tartube
            automatically adds quotes to the beginning and end of the string

        keep_video (bool): If True, youtube-dl will keep the video file after
            post-processing it

        embed_subs (bool): If True, youtube-dl will merge the subtitles file
            with the video (only for .mp4 files)

        embed_thumbnail (bool): When True will embed the thumbnail in the audio
            file as cover art

        add_metadata (bool): When True will write metadata to the video file

        fixup_policy (str): Automatically correct known faults of the file.
            The string can be 'never', 'warn', 'detect_or_worn' or an empty
            string if disabled

        prefer_avconv (bool): Prefer avconv over ffmpeg for running the
            postprocessors

        prefer_ffmpeg (bool): Prefer ffmpeg over avconv for running the
            postprocessors

    YOUTUBE-DL-GUI OPTIONS (not passed to youtube-dl directly)

        [used to build the 'save_path' option]

        output_format (int): Option in the range 0-5, which is converted into
            a youtube-dl output template using
            formats.FILE_OUTPUT_CONVERT_DICT. If the value is 3, then the
            custom 'output_template' is used instead

        output_template (str): Can be any output template supported by
            youtube-dl. Ignored if 'output_format' is not 3

        [used to modify the 'video_format' option]

        second_video_format (str): Video format to download, if the format
            specified by the 'video_format' option isn't available. This option
            is ignored when its value is '0' (or when the value of the
            'video_format' option is '0'), and also if 'video_format' is set
            to one of the keys in formats.VIDEO_RESOLUTION_DICT (e.g. 1080p).
            Otherwise, its value is one of the keys in
            formats.VIDEO_FORMAT_DICT

        third_video_format (str): Video format to download, if the formats
            specified by the 'video_format' and 'second_video_format' options
            aren't available. This option is ignored when its value is '0' (or
            when the value of the 'video_format' and 'second_video_format'
            options are '0'), and also if 'video_format' or
            'second_video_format' are set to one of the keys in
            formats.VIDEO_RESOLUTION_DICT (e.g. 1080p). Otherwise, its value is
            one of the keys in formats.VIDEO_FORMAT_DICT

        [used in conjunction with the 'min_filesize' and 'max_filesize' options

            max_filesize_unit (str): Maximum file size unit. Available values:
                '' (for bytes), 'k' (for kilobytes, etc), 'm', 'g', 't', 'p',
                'e', 'z', 'y'

            min_filesize_unit (str): Minimum file size unit. Available values
                as above

        [in youtube-dl-gui, this was named 'cmd_args']

        extra_cmd_string: String that contains extra youtube-dl options
            separated by spaces. Components containing whitespace can be
            enclosed within double quotes "..."

    TARTUBE OPTIONS (not passed to youtube-dl directly)

        keep_description (bool):
        keep_info (bool):
        keep_annotations (bool):
        keep_thumbnail (bool):
            During a download operation (not simulated, e.g. when the user
            clicks the 'Download all' button), the video description/JSON/
            annotations/thumbnail files are downloaded only if
            'write_description', 'write_info', 'write_annotations' and/or
            'write_thumbnail' are True

            They are initially stored in the same sub-directory in which
            Tartube will store the video

            If these options are True, they stay there; otherwise, they are
            copied into the equivalent location in Tartube's temporary
            directories.

        sim_keep_description (bool):
        sim_keep_info (bool):
        sim_keep_annotations (bool):
        sim_keep_thumbnail (bool):
            During a download operation (simulated, e.g. when the user clicks
            the 'Check all' button), the video's JSON file is always loaded
            into memory

            If 'write_description' and 'sim_description' are both true, the
            description file is written directly to the sub-directory in which
            Tartube would store the video

            If 'write_description' is true but 'keep_description' not, the
            description file is written to the equivalent location in Tartube's
            temporary directories.

            The same applies to the JSON, annotations and thumbnail files.

        use_fixed_folder (str or None): If not None, then all videos are
            downloaded to one of Tartube's fixed folders (not including private
            folders) - currently, that group consists of only 'Temporary
            Videos' and 'Unsorted Videos'. The value should match the name of
            the folder

        match_title_list (list): Download only matching titles (regex or
            caseless sub-string). Each item in the list is passed to youtube-dl
            as a separate --match-title argument

        reject_title_list (list): Skip download for any matching titles (regex
            or caseless sub-string). Each item in the list is passed to
            youtube-dl as a separate --reject-title argument

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
            'abort_on_error': False,
            # NETWORK OPTIONS
            'proxy': '',
            'socket_timeout': '',
            'source_address': '',
            'force_ipv4': False,
            'force_ipv6': False,
            # GEO-RESTRICTION
            'geo_verification_proxy': '',
            'geo_bypass': False,
            'no_geo_bypass': False,
            'geo_bypass_country': '',
            'geo_bypass_ip_block': '',
            # VIDEO SELECTION
            'playlist_start': 1,
            'playlist_end': 0,
            'max_downloads': 0,
            'min_filesize': 0,
            'max_filesize': 0,
            'date': '',
            'date_before': '',
            'date_after': '',
            'min_views': 0,
            'max_views': 0,
            'match_filter': '',
            'age_limit': '',
            'include_ads': False,
            # DOWNLOAD OPTIONS
            'limit_rate': '',             # Can't be directly modified by user
            'retries': 10,
            'playlist_reverse': False,
            'playlist_random': False,
            'native_hls': True,
            'prefer_ffmpeg': False,
            'external_downloader': '',
            'external_arg_string': '',
            # FILESYSTEM OPTIONS
            'save_path': None,             # Can't be directly modified by user
            'restrict_filenames': False,
            'nomtime': False,
            'write_description': True,
            'write_info': True,
            'write_annotations': True,
            # THUMBNAIL IMAGES
            'write_thumbnail': True,
            # VERBOSITY / SIMULATION OPTIONS
            #   (none implemented)
            # WORKAROUNDS
            'force_encoding': '',
            'no_check_certificate': False,
            'prefer_insecure': False,
            'user_agent': '',
            'referer': '',
            # VIDEO FORMAT OPTIONS
            'video_format': '0',
            'all_formats': False,
            'prefer_free_formats': False,
            'yt_skip_dash': False,
            'merge_output_format': '',
            # SUBTITLE OPTIONS
            'write_subs': False,
            'write_auto_subs': False,
            'write_all_subs': False,
            'subs_format': '',
            'subs_lang': 'en',
            # AUTHENTIFICATION OPTIONS
            'username': '',
            'password': '',
            'two_factor': '',
            'net_rc': False,
            'video_password': '',
            # ADOBE PASS OPTIONS
            #   (none implemented)
            # POST-PROCESSING OPTIONS
            'extract_audio': False,
            'audio_format': '',
            'audio_quality': '5',
            'recode_video': '',
            'pp_args': '',
            'keep_video': False,
            'embed_subs': False,
            'embed_thumbnail': False,
            'add_metadata': False,
            'fixup_policy': '',
            'prefer_avconv': False,
            'prefer_ffmpeg': False,
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
           'keep_annotations': False,
           'keep_thumbnail': True,
           'sim_keep_description': False,
           'sim_keep_info': False,
           'sim_keep_annotations': False,
           'sim_keep_thumbnail': True,
           'use_fixed_folder': None,
           'match_title_list': [],
           'reject_title_list': [],
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
            # --abort-on-error
            OptionHolder('abort_on_error', '--abort-on-error ', False),
            # NETWORK OPTIONS
            # --proxy URL
            OptionHolder('proxy', '--proxy', ''),
            OptionHolder('socket_timeout', '--socket-timeout', ''),
            OptionHolder('source_address', '--source-address', ''),
            OptionHolder('force_ipv4', '--force-ipv4', False),
            OptionHolder('force_ipv6', '--force-ipv6', False),
            # GEO-RESTRICTION
            OptionHolder(
                'geo_verification_proxy',
                '--geo-verification-proxy',
                '',
            ),
            OptionHolder('geo_bypass', '--geo-bypass', False),
            OptionHolder('no_geo_bypass', '--no-geo-bypass', False),
            OptionHolder('geo_bypass_country', '--geo-bypass-country', ''),
            OptionHolder('geo_bypass_ip_block', '--geo-bypass-ip-block', ''),
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
            # --date DATE
            OptionHolder('date', '--date', ''),
            # --datebefore DATE
            OptionHolder('date_before', '--datebefore', ''),
            # --dateafter DATE
            OptionHolder('date_after', '--dateafter', ''),
            # --min-views COUNT
            OptionHolder('min_views', '--min-views', 0),
            # --max-views COUNT
            OptionHolder('max_views', '--max-views', 0),
            # --match-filter FILTER
            OptionHolder('match_filter', '--match-filter', ''),
            # --age-limit YEARS
            OptionHolder('age_limit', '--age-limit', ''),
            # --include-ads FILTER
            OptionHolder('include_ads', '--include-ads', False),
            # DOWNLOAD OPTIONS
            # -r, --limit-rate RATE
            OptionHolder('limit_rate', '-r', ''),
            # -R, --retries RETRIES
            OptionHolder('retries', '-R', 10),
            # --playlist-reverse
            OptionHolder('playlist_reverse', '--playlist-reverse', False),
            # --playlist-random
            OptionHolder('playlist_random', '--playlist-random', False),
            # --hls-prefer-native
            OptionHolder('native_hls', '--hls-prefer-native', False),
            # --hls-prefer-ffmpeg
            OptionHolder('prefer_ffmpeg', '--hls-prefer-ffmpeg', False),
            # --external-downloader COMMAND
            OptionHolder('external_downloader', '--external-downloader', ''),
            # --external-downloader-args ARGS
            OptionHolder(
                'external_arg_string',
                '--external-downloader-args',
                '',
            ),
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
            # --write-annotations
            OptionHolder('write_annotations', '--write-annotations', False),
            # THUMBNAIL IMAGES
            # --write-thumbnail
            OptionHolder('write_thumbnail', '--write-thumbnail', False),
            # VERBOSITY / SIMULATION OPTIONS
            #   (none implemented)
            # WORKAROUNDS
            # --encoding ENCODING
            OptionHolder('force_encoding', '--encoding', ''),
            # --no-check-certificate
            OptionHolder(
                'no_check_certificate',
                '--no-check-certificate',
                False,
            ),
            # --prefer-insecure
            OptionHolder('prefer_insecure', '--prefer-insecure ', False),
            # --user-agent UA
            OptionHolder('user_agent', '--user-agent', ''),
            # --referer URL
            OptionHolder('referer', '--referer', ''),
            # VIDEO FORMAT OPTIONS
            # -f, --format FORMAT
            OptionHolder('video_format', '-f', '0'),
            # --all-formats
            OptionHolder('all_formats', '--all-formats', False),
            # --prefer-free-formats
            OptionHolder(
                'prefer_free_formats',
                '--prefer-free-formats',
                False,
            ),
            # --youtube-skip-dash-manifest
            OptionHolder(
                'yt_skip_dash',
                '--youtube-skip-dash-manifest',
                False,
            ),
            # --merge-output-format FORMAT
            OptionHolder('merge_output_format', '--merge-output-format', ''),
            # SUBTITLE OPTIONS
            # --write-sub
            OptionHolder('write_subs', '--write-sub', False),
            # --write-auto-sub
            OptionHolder('write_auto_subs', '--write-auto-sub', False),
            # --all-subs
            OptionHolder('write_all_subs', '--all-subs', False),
            # --sub-format FORMAT
            OptionHolder('subs_format', '--sub-format', ''),
            # --sub-lang LANGS
            OptionHolder('subs_lang', '--sub-lang', '', ['write_subs']),
            # AUTHENTIFICATION OPTIONS
            # -u, --username USERNAME
            OptionHolder('username', '-u', ''),
            # -p, --password PASSWORD
            OptionHolder('password', '-p', ''),
            # -2, --twofactor TWOFACTOR
            OptionHolder('two_factor', '--twofactor', ''),
            # -n, --netrc
            OptionHolder('net_rc', '--netrc', False),
            # --video-password PASSWORD
            OptionHolder('video_password', '--video-password', ''),
            # ADOBE PASS OPTIONS
            #   (none implemented)
            # POST-PROCESSING OPTIONS
            # -x, --extract-audio
            OptionHolder('extract_audio', '-x', False),
            # --audio-format FORMAT
            OptionHolder('audio_format', '--audio-format', ''),
            # --audio-quality QUALITY
            OptionHolder(
                'audio_quality',
                '--audio-quality',
                '5',
                ['extract_audio'],
            ),
            # --recode-video FORMAT
            OptionHolder('recode_video', '--recode-video', ''),
            # --postprocessor-args ARGS
            OptionHolder('pp_args', '--postprocessor-args', ''),
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
            # --fixup POLICY
            OptionHolder('fixup_policy', '--fixup', ''),
            # --prefer-avconv
            OptionHolder('prefer_avconv', '--prefer-avconv', False),
            # --prefer-ffmpeg
            OptionHolder('prefer_ffmpeg', '--prefer-ffmpeg', False),
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
#           OptionHolder('keep_annotations', '', False),
#           OptionHolder('keep_thumbnail', '', False),
#           OptionHolder('sim_keep_description', '', False),
#           OptionHolder('sim_keep_info', '', False),
#           OptionHolder('sim_keep_annotations', '', False),
#           OptionHolder('sim_keep_thumbnail', '', False),
#           OptionHolder('use_fixed_folder', '', None),
#           OptionHolder('match_title_list', '', []),
#           OptionHolder('reject_title_list', '', []),
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
        self.build_video_format(download_item_obj, copy_dict)
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
            if option_holder_obj.name == 'extract_audio':
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

            elif option_holder_obj.name == 'match_filter' \
            or option_holder_obj.name == 'external_arg_string' \
            or option_holder_obj.name == 'pp_args':
                value = copy_dict[option_holder_obj.name]
                if value != '':
                    options_list.append(option_holder_obj.switch)
                    options_list.append('"' + utils.to_string(value) + '"')

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

        # Parse the 'match_title_list' and 'reject_title_list'
        for item in copy_dict['match_title_list']:
            options_list.append('--match-title')
            options_list.append(item)

        for item in copy_dict['reject_title_list']:
            options_list.append('--reject-title')
            options_list.append(item)

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
        app_obj = self.download_manager_obj.app_obj
        media_data_obj = download_item_obj.media_data_obj
        override_name = copy_dict['use_fixed_folder']

        if not isinstance(media_data_obj, media.Video) \
        and override_name is not None \
        and override_name in app_obj.media_name_dict:

            # Because of the override, save all videos to a fixed folder
            other_dbid = app_obj.media_name_dict[override_name]
            other_obj = app_obj.media_reg_dict[other_dbid]
            save_path = other_obj.get_dir(app_obj)

        else:

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


    def build_video_format(self, download_item_obj, copy_dict):

        """Called by self.parse().

        Build the value of the 'video_format' option and store it in the
        options dictionary.

        Args:

            download_item_obj (downloads.DownloadItem) - The object handling
                the download

            copy_dict (dict): Copy of the original options dictionary.

        """

        # The 'video_format', 'second_video_format' and 'third_video_format'
        #   can have the values of the keys in formats.VIDEO_OPTION_DICT, which
        #   are either real extractor codes (e.g. '35' representing
        #   'flv [480p]') or dummy extractor codes (e.g. 'mp4')
        # Some dummy extractor codes are in the form '720p', '1080p' etc,
        #   representing progressive scan resolutions. If the user specifies
        #   at least one of those codes, the first one is used, and all other
        #   extractor codes (are ignored)
        resolution_dict = formats.VIDEO_RESOLUTION_DICT.copy()
        app_obj = self.download_manager_obj.app_obj

        # If the progressive scan resolution is specified, it overrides all
        #   other video format options
        if app_obj.video_res_apply_flag:
            height = resolution_dict[app_obj.video_res_default]
        elif copy_dict['video_format'] in resolution_dict:
            height = resolution_dict[copy_dict['video_format']]
        elif copy_dict['second_video_format'] in resolution_dict:
            height = resolution_dict[copy_dict['second_video_format']]
        elif copy_dict['third_video_format'] in resolution_dict:
            height = resolution_dict[copy_dict['third_video_format']]
        else:
            height = None

        if height is not None:

            # Use a youtube-dl argument in the form
            #   'bestvideo[height<=?height]+bestaudio/best[height<=height]'
            copy_dict['video_format'] = 'bestvideo[height<=?' \
            + str(height) + ']+bestaudio/best[height<=?' + str(height) + ']'
            # After a progressive scan resolution, all other extract codes are
            #   ignored
            copy_dict['second_video_format'] = '0'
            copy_dict['third_video_format'] = '0'

        # Not using a progressive scan resolution
        elif copy_dict['video_format'] != '0' and \
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
