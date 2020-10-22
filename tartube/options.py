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

    """Called by mainapp.TartubeApp.OptionsManager().

    Partially based on the OptionsManager class in youtube-dl-gui.

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

        hls_prefer_ffmpeg (bool): When True, youtube-dl will prefer FFmpeg
            (N.B. This should not be confused with the 'prefer_ffmpeg' option)

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

        min_sleep_interval (int): Number of seconds to sleep before each
            download when used alone, or a lower bound of a range for
            randomised sleep before each download (minimum possible number of
            seconds to sleep) when used along with max_sleep_interval

        max_sleep_interval (int): Upper bound of a range for randomized sleep
            before each download (maximum possible number of seconds to sleep).
            Can only be used along with a non-zero value for min_sleep_interval

    VIDEO FORMAT OPTIONS

        video_format (str): Video format to download. When this option is set
            to '0' youtube-dl will choose the best video format available for
            the given URL. Otherwise, set in a call to
            OptionsParser.build_video_format(), combining the contents of the
            'video_format_list' and 'video_format_mode' options. The combined
            value is passed to youtube-dl with the -f switch

        all_formats (bool): If True, download all available video formats.
            Also set in the call to OptionsParser.build_video_format()

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
            the 'write_subs' option. Can not be set directly by the user;
            instead, OptionsParser.parse() converts the option 'subs_lang_list'
            to a string, and sets this option to that string

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

        prefer_avconv (bool): Prefer AVConv over FFmpeg for running the
            postprocessors

        prefer_ffmpeg (bool): Prefer FFmpeg over AVConv for running the
            postprocessors

    YOUTUBE-DL-GUI OPTIONS (not passed to youtube-dl directly)

        [used to build the 'save_path' option]

        output_format (int): Option in the range 0-9, which is converted into
            a youtube-dl output template using
            formats.FILE_OUTPUT_CONVERT_DICT. If the value is 0, then the
            custom 'output_template' is used instead

        output_template (str): Can be any output template supported by
            youtube-dl. Ignored if 'output_format' is not 0

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

        move_description (bool):
        move_info (bool):
        move_annotations (bool):
        move_thumbnail (bool):
            During a download operation (real or simulated), if these values
            are True, the video description/JSON/annotations files are moved to
            a '.data' sub-directory, and the thumbnails are moved to a
            '.thumbs' sub-directory, inside the directory containing the videos

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

        video_format_list (list): List of video formats to download, in order
            of preference. If an empty list, youtube-dl will choose the best
            video format available for the given URL. Otherwise, the items in
            this list are keys in formats.VIDEO_FORMAT_DICT. The corresponding
            values are combined and stored as the 'video_format' option, first
            being rearrnaged to put video formats before audio formats
            (otherwise youtube-dl won't download the video formats)

        video_format_mode (str): 'all' to download all available formats,
            ignoring the preference list (sets the option 'all_formats').
            'single' to download the first available format in
            'video_format_list'. 'single_agree' to download the first format in
            'video_format_list' that's available for all videos. 'multiple' to
            download all available formats in 'video_format_list'

        subs_lang_list (list): List of language tags which are used to set
            the 'subs_lang' option

    """


    # Standard class methods


    def __init__(self, uid, name, dbid=None):

        # IV list - other
        # ---------------
        # Unique ID for this options manager
        self.uid = uid
        # A non-unique name for this options manager. Managers that are
        #   attached to a media data object have the same name as that object.
        #   (The name is not unique because, for example, videos could have the
        #   same name as a channel; it's up to the user to avoid duplicate
        #   names)
        self.name = name
        # If this object is attached to a media data object, the .dbid of that
        #   object; otherwise None
        self.dbid = dbid

        # Dictionary of download options for youtube-dl, set by a call to
        #   self.reset_options
        self.options_dict = {}


        # Code
        # ----

        # Initialise youtube-dl options
        self.reset_options()


    # Public class methods


    def clone_options(self, other_options_manager_obj):

        """Called by mainapp.TartubeApp.apply_download_options() and
        .clone_general_options_manager().

        Clones download options from the specified object into those object,
        completely replacing this object's download options.

        Args:

            other_options_manager_obj (options.OptionsManager): The download
                options object (usually the General Options Manager), from
                which options will be cloned

        """

        self.options_dict = other_options_manager_obj.options_dict.copy()

        # In the dictionary's key-value pairs, some values are themselves lists
        #   that must be copied directly
        for key in [
            'match_title_list', 'reject_title_list', 'video_format_list',
            'subs_lang_list',
        ]:
            self.options_dict[key] \
            = other_options_manager_obj.options_dict[key].copy()


    def rearrange_formats(self):

        """Called by config.OptionsEditWin.apply_changes().

        The option 'video_format_list' specifies video formats, audio formats
        or a mixture of both.

        youtube-dl won't download the specified formats properly, if audio
        formats appear before video formats. Therefore, this function is called
        to rearrange the list, putting all video formats above all audio
        formats.
        """

        format_list = self.options_dict['video_format_list']
        video_list = []
        audio_list = []
        comb_list = []

        for code in format_list:

            if code != '0':

                if formats.VIDEO_OPTION_TYPE_DICT[code] is False:
                    video_list.append(code)
                else:
                    audio_list.append(code)

        comb_list.extend(video_list)
        comb_list.extend(audio_list)

        self.options_dict['video_format_list'] = format_list


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
            'hls_prefer_ffmpeg': False,
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
            'min_sleep_interval': 0,
            'max_sleep_interval': 0,
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
            'subs_lang': '',
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
            'output_format': 2,
            'output_template': '%(title)s.%(ext)s',
            'max_filesize_unit' : '',
            'min_filesize_unit' : '',
            'extra_cmd_string' : '',
            # TARTUBE OPTIONS
           'move_description': False,
           'move_info': False,
           'move_annotations': False,
           'move_thumbnail': False,
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
           'video_format_list': [],
           'video_format_mode': 'single',
           'subs_lang_list': [ 'en' ],
        }


    def set_classic_mode_options(self):

        """Called by mainapp.TartubeApp.apply_classic_download_options().

        When the user applies download options in the Classic Mode Tab, a few
        options should have different default values; this function sets them.
        """

        self.options_dict['write_description'] = False
        self.options_dict['write_info'] = False
        self.options_dict['write_annotations'] = False
        self.options_dict['write_thumbnail'] = False

        self.options_dict['move_description'] = False
        self.options_dict['move_info'] = False
        self.options_dict['move_annotations'] = False
        self.options_dict['move_thumbnail'] = False

        self.options_dict['keep_description'] = False
        self.options_dict['keep_info'] = False
        self.options_dict['keep_annotations'] = False
        self.options_dict['keep_thumbnail'] = False

        self.options_dict['sim_keep_description'] = False
        self.options_dict['sim_keep_info'] = False
        self.options_dict['sim_keep_annotations'] = False
        self.options_dict['sim_keep_thumbnail'] = False


    # Set accessors


    def set_dbid(self, dbid):

        self.dbid = dbid


class OptionsParser(object):

    """Called by downloads.DownloadManager.__init__() and by
    mainwin.SystemCmdDialogue.update_textbuffer().

    This object converts the download options specified by an
    options.OptionsManager object into a list of youtube-dl command line
    options, whenever required.

    Args:

        app_obj (mainapp.TartubeApp): The main application

    """


    # Standard class methods


    def __init__(self, app_obj):

        # IV list - class objects
        # -----------------------
        # The main application
        self.app_obj = app_obj


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
            OptionHolder('hls_prefer_ffmpeg', '--hls-prefer-ffmpeg', False),
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
            # --sleep-interval SECONDS
            OptionHolder('min_sleep_interval', '--sleep-interval', 0),
            # --max-sleep-interval SECONDS
            OptionHolder('max_sleep_interval', '--max-sleep-interval', 0),
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
            # --sub-lang LANGS. NB This '--sub-lang' string is not the one
            #   used as a switch by self.parse()
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
#           OptionHolder('output_format', '', 2),
#           OptionHolder('output_template', '', ''),
#           OptionHolder('max_filesize_unit', '', ''),
#           OptionHolder('min_filesize_unit', '', ''),
#           OptionHolder('extra_cmd_string', '', ''),
            # TARTUBE OPTIONS (not given an options.OptionHolder object)
#           OptionHolder('move_description', '', False),
#           OptionHolder('move_info', '', False),
#           OptionHolder('move_annotations', '', False),
#           OptionHolder('move_thumbnail', '', False),
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
#           OptionHolder('video_format_list', '', []),
#           OptionHolder('video_format_mode', '', 'single'),
#           OptionHolder('subs_lang_list', '', []),
        ]


    # Public class methods


    def parse(self, media_data_obj, options_manager_obj,
    operation_type='real'):

        """Called by downloads.DownloadWorker.prepare_download() and
        mainwin.MainWin.update_textbuffer().

        Converts the download options stored in the specified
        options.OptionsManager object into a list of youtube-dl command line
        options.

        Args:

            media_data_obj (media.Video, media.Channel, media.Playlist,
                media.Folder): The media data object being downloaded

            options_manager_obj (options.OptionsManager): The object containing
                the download options for this media data object

            operation_type (str): 'sim', 'real', 'custom', 'classic' (matching
                possible values of downloads.DownloadManager.operation_type)

        Returns:

            List of strings with all the youtube-dl command line options

        """

        # Force youtube-dl's progress bar to be outputted as separate lines
        options_list = ['--newline']

        # Create a copy of the dictionary...
        copy_dict = options_manager_obj.options_dict.copy()
        # ...then modify various values in the copy. Set the 'save_path' option
        self.build_save_path(media_data_obj, copy_dict, operation_type)
        # Set the 'video_format' option and 'all_formats' options
        self.build_video_format(media_data_obj, copy_dict, operation_type)
        # Set the 'min_filesize' and 'max_filesize' options
        self.build_file_sizes(copy_dict)
        # Set the 'limit_rate' option
        self.build_limit_rate(copy_dict)

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

            elif option_holder_obj.name == 'subs_lang_list':
                # Convert the list to a comma-separated string, that the
                #   'subs_lang' option can use
                lang_list = copy_dict[option_holder_obj.name]
                if lang_list:

                    comma = ','
                    options_list.append('--sub-lang')
                    options_list.append(comma.join(lang_list))

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
        parsed_list = utils.parse_ytdl_options(copy_dict['extra_cmd_string'])
        for item in parsed_list:
            options_list.append(item)

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

        # Set the bandwidth limit (e.g. '50K')
        if self.app_obj.bandwidth_apply_flag:

            # The bandwidth limit is divided equally between the workers
            limit = int(
                self.app_obj.bandwidth_default
                / self.app_obj.num_worker_default
            )

            copy_dict['limit_rate'] = str(limit) + 'K'


    def build_save_path(self, media_data_obj, copy_dict, operation_type):

        """Called by self.parse().

        Build the value of the 'save_path' option and store it in the options
        dictionary.

        Args:

            media_data_obj (media.Video, media.Channel, media.Playlist,
                media.Folder): The media data object being downloaded

            copy_dict (dict): Copy of the original options dictionary

            operation_type (str): 'sim', 'real', 'custom', 'classic' (matching
                possible values of downloads.DownloadManager.operation_type)

        """

        # Special case: if a download operation was launched from the Classic
        #   Mode Tab, the save path is specified in that tab
        if operation_type == 'classic':

            save_path = media_data_obj.dummy_dir

        else:

            # Set the directory in which any downloaded videos will be saved
            override_name = copy_dict['use_fixed_folder']

            if not isinstance(media_data_obj, media.Video) \
            and override_name is not None \
            and override_name in self.app_obj.media_name_dict:

                # Because of the override, save all videos to a fixed folder
                other_dbid = self.app_obj.media_name_dict[override_name]
                other_obj = self.app_obj.media_reg_dict[other_dbid]
                save_path = other_obj.get_default_dir(self.app_obj)

            else:

                if isinstance(media_data_obj, media.Video):
                    save_path = media_data_obj.parent_obj.get_actual_dir(
                        self.app_obj,
                    )

                else:
                    save_path = media_data_obj.get_actual_dir(self.app_obj)

        # Set the youtube-dl output template for the video's file
        template = formats.FILE_OUTPUT_CONVERT_DICT[copy_dict['output_format']]
        # In the case of copy_dict['output_format'] = 0
        if template is None:
            template = copy_dict['output_template']

        copy_dict['save_path'] = os.path.abspath(
            os.path.join(save_path, template),
        )


    def build_video_format(self, media_data_obj, copy_dict, operation_type):

        """Called by self.parse().

        Build the value of the 'video_format' and 'all_formats' options and
        store them in the options dictionary.

        Args:

            media_data_obj (media.Video, media.Channel, media.Playlist,
                media.Folder): The media data object being downloaded

            copy_dict (dict): Copy of the original options dictionary

            operation_type (str): 'sim', 'real', 'custom', 'classic' (matching
                possible values of downloads.DownloadManager.operation_type)

        """

        if isinstance(media_data_obj, media.Video):

            # Special case: if a download operation was launched from the
            #   Classic Mode Tab, the video format may be specified by that tab
            if operation_type == 'classic' \
            and media_data_obj.dummy_format:

                dummy_format = media_data_obj.dummy_format

                if dummy_format in formats.VIDEO_FORMAT_DICT:

                    # Ignore all video/audio formats except the one specified
                    #   by the user in the Classic Mode Tab
                    copy_dict['video_format'] = dummy_format
                    copy_dict['all_formats'] = False
                    copy_dict['video_format_list'] = []
                    copy_dict['video_format_mode'] = ''

                    # v2.1.009: Since the user doesn't have the possibility of
                    #   setting the -f and --merge-output-format options to the
                    #   same value (e.g. 'mp4'), we must do so artificially
                    copy_dict['merge_output_format'] = dummy_format

                    return

                elif dummy_format in formats.AUDIO_FORMAT_DICT:

                    # Downloading audio formats requires post-processing
                    copy_dict['video_format'] = '0'
                    copy_dict['all_formats'] = False
                    copy_dict['video_format_list'] = []
                    copy_dict['video_format_mode'] = ''
                    copy_dict['extract_audio'] = True
                    copy_dict['audio_format'] = dummy_format

                    return

            # Special case: for broadcasting livestreams, use only HLS
            # v2.0.067: Downloading livestreams doesn't work at all for me, so
            #   I'm not sure whether this is appropriate, or not. Once it's
            #   fixed, perhaps we can offer the user a choice of formats
            if media_data_obj.live_mode:

                copy_dict['video_format'] = '95'
                copy_dict['all_formats'] = False
                copy_dict['video_format_list'] = []
                copy_dict['video_format_mode'] = ''

                return

        # Special case: for simulated downloads, don't specify any video
        #   formats; if the format isn't available for some videos, we'll get
        #   an error for each of them (rather than the simulated download we
        #   were hoping for)
        if operation_type == 'sim':

            copy_dict['video_format'] = '0'
            copy_dict['all_formats'] = False
            copy_dict['video_format_list'] = []
            copy_dict['video_format_mode'] = ''

            return

        # The 'video_format_list' options contains values corresponding to the
        #   keys in formats.VIDEO_OPTION_DICT, which are either real extractor
        #   codes (e.g. '35' representing 'flv [480p]') or dummy extractor
        #   codes (e.g. 'mp4')
        # Some dummy extractor codes are in the form '720p', '1080p60' etc,
        #   representing progressive scan resolutions. If the user specifies
        #   at least one of those codes, the first one is used, and all other
        #   extractor codes are ignored
        video_format_list = copy_dict['video_format_list']
        resolution_dict = formats.VIDEO_RESOLUTION_DICT.copy()
        fps_dict = formats.VIDEO_FPS_DICT.copy()

        # If the progressive scan resolution is specified, it overrides all
        #   other video format options
        height = None
        fps = None

        if self.app_obj.video_res_apply_flag:
            height = resolution_dict[self.app_obj.video_res_default]
            # (Currently, formats.VIDEO_FPS_DICT only lists formats with 60fps)
            if self.app_obj.video_res_default in fps_dict:
                fps = fps_dict[self.app_obj.video_res_default]

        else:

            for item in video_format_list:

                if item in resolution_dict:
                    height = resolution_dict[item]
                    if item in fps_dict:
                        fps = fps_dict[item]

                    break

        if height is not None:

            # (Currently, formats.VIDEO_FPS_DICT only lists formats with 60fps)
            if fps is None:

                # Use a youtube-dl argument in the form
                #   'bestvideo[height<=?height]+bestaudio/best[height<=height]'
                copy_dict['video_format'] = 'bestvideo[height<=?' \
                + str(height) + ']+bestaudio/best[height<=?' + str(height) \
                + ']'

            else:

                copy_dict['video_format'] = 'bestvideo[height<=?' \
                + str(height) + '][fps<=?' + str(fps) \
                + ']+bestaudio/best[height<=?' + str(height) + ']'

            copy_dict['all_formats'] = False
            copy_dict['video_format_list'] = []
            copy_dict['video_format_mode'] = ''

        # Not using a progressive scan resolution
        elif video_format_list:

            video_format_mode = copy_dict['video_format_mode']

            if video_format_mode == 'all':
                copy_dict['video_format'] = 0
                copy_dict['all_formats'] = True

            else:

                copy_dict['all_formats'] = False

                if video_format_mode == 'single_agree':
                    char = '/'
                elif video_format_mode == 'multiple':
                    char = ','
                else:
                    # mode is 'single'
                    char = '+'

                copy_dict['video_format'] = char.join(video_format_list)

            copy_dict['video_format_list'] = []
            copy_dict['video_format_mode'] = ''


class OptionHolder(object):

    """Called from options.OptionsParser.__init__().

    The options parser object converts the download options specified by an
    options.OptionsManager object into a list of youtube-dl command line
    options, whenever required.

    Each option has a name, a command line switch, a default value and an
    optional list of requirements; they are stored together in an instance of
    this object.

    Args:

        name (str): Option name. Must be a valid option name from the
            optionsmanager.OptionsManager class (see the list in at the
            beginning of the options.OptionsManager class)

        switch (str): The option command line switch. See
            https://github.com/rg3/youtube-dl/#options

        default_value (any): The option default value. Must be the same type
            as the corresponding option from the optionsmanager.OptionsManager
            class.

        requirement_list (list): The requirements for the given option. This
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
