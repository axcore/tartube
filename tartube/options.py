#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2021 A S Lewis
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
import re


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

        proxy (str): Use the specified HTTP/HTTPS proxy. If none is specified,
            then Tartube will cycle through the list of proxies specified in
            mainapp.TartubeApp.dl_proxy_list (if any)

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

        cookies_path (str): Path to the cookie jar. If not specified, then
            Tartube will use the cookie jar 'cookies.txt' in the main
            data directory

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
            seconds to sleep) when used along with 'max_sleep_interval'

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

        yt_skip_dash (bool): If True, do not download DASH-related data with
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

        ap_mso (str): Adobe Pass multiple-system operator (TV provider)
            identifier

        ap_username (str): Multiple-system operator account login

        ap_password (str): Multiple-system operator account password. If this
            option is left out, yt-dlp will ask interactively

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

    YT-DLP OPTIONS (will not work with other downloaders)

        [not passed to yt-dlp directly]

        output_format_list (list): List of arguments used with the '--output'
            parameter, in the form TYPES:TEMPLATE. Each argument should have
            a unique TYPES component. If this option is specified,
            'output_format' and 'output_template' are ignored

        output_path_list (list): List of arguments used with the '--paths'
            paremeter, in the form TYPES:PATH. Each argument should have a
            unique TYPES component. If 'output_path_list' contains any values,
            then 'output_format_list' and/or 'output_format' are used without a
            preceding absolute path

        extractor_args_list (list): Pass these arguments to the extractor. You
            can use this option multiple times to give different arguments to
            different extractors. Each item in the list is in the form
            KEY:ARGS

        [Video Selection Options]

        break_on_existing (bool): If True, stops the download process when
            encountering a file that is in the archive

        break_on_reject (bool): If True, stops the download process when
            encountering a file that has been filtered out

        skip_playlist_after_errors (int): Number of allowed failures until the
            rest of the playlist is skipped

        [Download Options]

        concurrent_fragments (int): Number of fragments of a DASH/hlsnative
            video that should be download concurrently (default is 1)

        throttled_rate (int): Minimum download rate in bytes per second below
            which throttling is assumed and the video data is re-extracted
            (e.g. 100K)

        [Filesystem Options]

        windows_filenames (bool): If True, forces filenames to be MS Windows
            compatible

        trim_filenames (int): Limit the filename length (excluding extension)
            to the specified number of characters

        force_overwrites (bool): If True, overwrites all video and metadata
            files. This option includes '--no-continue' (for which there is no
            Tartube download option)

        write_playlist_metafiles (bool): If True, writes playlist metadata in
            addition to the video metadata when using --write-info-json,
            --write-description etc. (default)

        no_clean_info_json (bool): If True, writes all fields to the infojson
            (default is to remove some private fields)

        [Internet Shortcut Options]

        write_link (bool): If True, writes an internet shortcut file, depending
            on the current platform (.url, .webloc or .desktop). The URL may be
            cached by the OS

        write_url_link (bool): If True, writes a .url Windows internet
            shortcut. The OS caches the URL based on the file path

        write_webloc_link (bool): If True, writes a .webloc macOS internet
            shortcut

        write_desktop_link (bool): If True, writes a .desktop Linux internet
            shortcut

        [Verbosity and Simulation Options]

        ignore_no_formats_error (bool): If True, ignore "No video formats"
            error. Useful for extracting metadata even if the video is not
            actually available for download (experimental)

        force_write_archive (bool): If True, forces download archive entries to
            be written as far as no errors occur, even if -s or another
            simulation option is used

        [Workaround Options]

        sleep_requests (int): Number of seconds to sleep between requests
            during data extraction

        sleep_subtitles (int): Number of seconds to sleep before each download.
            This is the minimum time to sleep when used along with
            'max_sleep_interval'

        [Video Format Options]

        video_multistreams (bool): If True, allows multiple video streams to be
            merged into a single file

        audio_multistreams (bool): If True, allows multiple audio streams to be
            merged into a single file

        check_formats (bool): If True, checks that the formats selected are
            actually downloadable (Experimental)

        allow_unplayable_formats (bool): If True, allows unplayable formats to
            be listed and downloaded. All video post-processing will also be
            turned off

        [Post-Processing Options]

        remux_video (str): Remux the video into another container if necessary
            (currently supported: mp4|mkv|flv|webm|mov|avi|mp3|mka|m4a|ogg
            |opus). If target container does not support the video/audio codec,
            remuxing will fail. You can specify multiple rules; Eg.
            "aac>m4a/mov>mp4/mkv" will remux aac to m4a, mov to mp4 and
            anything else to mkv.

        embed_metadata (bool): Embed metadata including chapter markers (if
            supported by the format) to the video file

        convert_thumbnails (str): Convert the thumbnails to another format
            (currently supported: jpg|png)

        split_chapters (bool): Split video into multiple files based on
            internal chapters. The "chapter:" prefix can be used with
            'output_path_list' and 'output_template_list' to set the output
            filename for the split files

        [Extractor Options]

        extractor_retries (str): Number of retries for known extractor errors
            (default is '3'), or 'infinite'

        no_allow_dynamic_mpd (bool): If True, do not process dynamic DASH
            manifests

        hls_split_discontinuity (bool): If True, splits HLS playlists to
            different formats at discontinuities such as ad breaks

    YOUTUBE-DL-GUI OPTIONS (not passed to youtube-dl directly)

        [used to build the 'save_path_list' option]

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

        extra_cmd_string (str): String that contains extra youtube-dl options
            separated by spaces. Components containing whitespace can be
            enclosed within double quotes "..."

        direct_cmd_flag (str): If True, only those command options specified by
            extra_cmd_string (including the source URL) are used; Tartube
            merely adds the downloader (e.g. 'youtube-dl') and the output
            directory switch (i.e. -o)

        direct_url_flag (str): If True, Tartube assumes that
            'extra_cmd_string' contains the URL to check/download. Otherwise,
            the source URL of each affected media data object(s) is used, as
            normal. Ignored if 'direct_cmd_flag' is False

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

            If 'write_description' and 'sim_keep_description' are both true,
            the description file is written directly to the sub-directory in
            which Tartube would store the video

            If 'write_description' is true but 'sim_keep_description' not, the
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

        downloader_config (bool): If true, a youtube-dl configuration is
            specified with the '--config-location' option. On Linux/MacOS, the
            user-wide configuration file is used
            ('~/.config/youtube-dl/config'). On MS Windows, a file in the
            Tartube directory is used (youtube-dl.conf)

        save_path_list (list): List of arguments used with the '--output'
            parameter. Contains the output template. If the 'output_path_list'
            option is not specified, then the template is preceded by the
            output directory. Arguments are constructed in a call to
            OptionsParser.build_save_path(), and cannot be set directly by the
            user

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

        """Called by mainapp.TartubeApp.apply_download_options(),
        .clone_download_options() and .clone_download_options_from_window().

        Clones download options from the specified object into this object,
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
            'restrict_filenames': False,
            'nomtime': False,
            'write_description': True,
            'write_info': True,
            'write_annotations': True,
            'cookies_path': '',
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
            'ap_mso': '',
            'ap_username': '',
            'ap_password': '',
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
            # YT-DLP OPTIONS
            # (not passed to yt-dlp directly)
            'output_format_list': [],
            'output_path_list': [],
            'extractor_args_list': [],
            # (Video Selection Options)
            'break_on_existing': False,
            'break_on_reject': False,
            'skip_playlist_after_errors': 0,
            # (Download Options)
            'concurrent_fragments': 1,
            'throttled_rate': 0,
            # (Filesystem Options)
            'windows_filenames': False,
            'trim_filenames': 0,
            'force_overwrites': False,
            'write_playlist_metafiles': False,
            'no_clean_info_json': False,
            # (Internet Shortcut Options)
            'write_link': False,
            'write_url_link': False,
            'write_webloc_link': False,
            'write_desktop_link': False,
            # (Verbosity and Simulation Options)
            'ignore_no_formats_error': False,
            'force_write_archive': False,
            # (Workaround Options)
            'sleep_requests': 0,
            'sleep_subtitles': 0,
            # (Video Format Options)
            'video_multistreams': False,
            'audio_multistreams': False,
            'check_formats': False,
            'allow_unplayable_formats': False,
            # (Post-Processing Options)
            'remux_video': '',
            'embed_metadata': False,
            'convert_thumbnails': '',
            'split_chapters': False,
            # (Extractor Options)
            'extractor_retries': '3',
            'no_allow_dynamic_mpd': False,
            'hls_split_discontinuity': False,
            # YOUTUBE-DL-GUI OPTIONS
            'output_format': 2,
            'output_template': '%(title)s.%(ext)s',
            'max_filesize_unit': '',
            'min_filesize_unit': '',
            'extra_cmd_string': '',
            'direct_cmd_flag': False,
            'direct_url_flag': False,
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
            'downloader_config': False,
            'save_path_list': [],
        }


    def set_classic_mode_options(self):

        """Called by mainapp.TartubeApp.apply_classic_download_options().

        When the user applies download options in the Classic Mode tab, a few
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


    def reset_dbid(self):

        self.dbid = None


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
            # --socket-timeout SECONDS
            OptionHolder('socket_timeout', '--socket-timeout', ''),
            # --source-address IP
            OptionHolder('source_address', '--source-address', ''),
            # -4, --force-ipv4
            OptionHolder('force_ipv4', '--force-ipv4', False),
            # -6, --force-ipv6
            OptionHolder('force_ipv6', '--force-ipv6', False),
            # GEO-RESTRICTION
            # --geo-verification-proxy URL
            OptionHolder(
                'geo_verification_proxy',
                '--geo-verification-proxy',
                '',
            ),
            # --geo-bypass
            OptionHolder('geo_bypass', '--geo-bypass', False),
            # --no-geo-bypass
            OptionHolder('no_geo_bypass', '--no-geo-bypass', False),
            # --geo-bypass-country CODE
            OptionHolder('geo_bypass_country', '--geo-bypass-country', ''),
            # --geo-bypass-ip-block IP_BLOCK
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
            # --include-ads
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
            # --cookies FILE
            OptionHolder('cookies_path', '--cookies', ''),
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
            # --sub-lang LANGS
            # NB This '--sub-lang' string is not the one used as a switch by
            #   self.parse()
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
            # --ap-mso MSO
            OptionHolder('ap_mso', '--ap-mso', ''),
            # --ap-username USERNAME
            OptionHolder('ap_username', '--ap-username', ''),
            # --ap-password PASSWORD
            OptionHolder('ap_password', '--ap-password', ''),
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
            # YT-DLP OPTIONS
            # (not given an options.OptionHolder object)
#           OptionHolder('output_format_list', '', []),
#           OptionHolder('output_path_list', '', []),
            # (Video Selection Options)
            # --break-on-existing
            OptionHolder('break_on_existing', '--break-on-existing', False),
            # --break-on-reject
            OptionHolder('break_on_reject', '--break-on-reject', False),
            # --skip-playlist-after-errors N
            OptionHolder(
                'skip_playlist_after_errors',
                '--skip-playlist-after-errors',
                0,
            ),
            # (Download Options)
            # --concurrent-fragments N
            OptionHolder('concurrent_fragments', '--concurrent-fragments', 1),
            # --throttled-rate RATE
            OptionHolder('throttled_rate', '--throttled-rate', 0),
            # (Filesystem Options)
            # --windows-filenames
            OptionHolder('windows_filenames', '--windows-filenames', False),
            # --trim-filenames LENGTH
            OptionHolder('trim_filenames', '--trim-filenames', 0),
            # --force-overwrites
            OptionHolder('force_overwrites', '--force-overwrites', False),
            # --write-playlist-metafiles
            OptionHolder(
                'write_playlist_metafiles',
                '--write-playlist-metafiles',
                False,
            ),
            # --no-clean-infojson
            OptionHolder('no_clean_info_json', '--no-clean-infojson', False),
            # (Internet Shortcut Options)
            # --write-link
            OptionHolder('write_link', '--write-link', False),
            # --write-url-link
            OptionHolder('write_url_link', '--write-url-link', False),
            # --write-webloc-link
            OptionHolder('write_webloc_link', '--write-webloc-link', False),
            # --write-desktop-link
            OptionHolder('write_desktop_link', '--write-desktop-link', False),
            # (Verbosity and Simulation Options)
            # --ignore-no-formats-error
            OptionHolder(
                'ignore_no_formats_error',
                '--ignore-no-formats-error',
                False,
            ),
            # --force-write-archive
            OptionHolder(
                'force_write_archive',
                '--force-write-archive',
                False,
            ),
            # (Workaround Options)
            # --sleep-requests SECONDS
            OptionHolder('sleep_requests', '--sleep-requests', 0),
            # --sleep-subtitles SECONDS
            OptionHolder('sleep_subtitles', '--sleep-subtitles', 0),
            # (Video Format Options)
            # --video-multistreams
            OptionHolder('video_multistreams', '--video-multistreams', False),
            # --audio-multistreams
            OptionHolder('audio_multistreams', '--audio-multistreams', False),
            # --check-formats
            OptionHolder('check_formats', '--check-formats', False),
            # --allow-unplayable-formats
            OptionHolder(
                'allow_unplayable_formats',
                '--allow-unplayable-formats',
                False,
            ),
            # (Post-Processing Options)
            # --remux-video FORMAT
            OptionHolder('remux_video', '--remux-video', ''),
            # --embed-metadata
            OptionHolder('embed_metadata', '--embed-metadata', False),
            # --convert-thumbnails FORMAT
            OptionHolder('convert_thumbnails', '--convert-thumbnails', ''),
            # --split-chapters
            OptionHolder('split_chapters', '--split-chapters', False),
            # (Extractor Options)
            # --extractor-retries RETRIES
            OptionHolder('extractor_retries', '--extractor-retries', '3'),
            # --no-allow-dynamic-mpd
            OptionHolder(
                'no_allow_dynamic_mpd',
                '--no-allow-dynamic-mpd',
                False,
            ),
            # --hls-split-discontinuity
            OptionHolder(
                'hls_split_discontinuity',
                '--hls-split-discontinuity',
                False,
            ),
            # YOUTUBE-DL-GUI OPTIONS (not given an options.OptionHolder object)
#           OptionHolder('output_format', '', 2),
#           OptionHolder('output_template', '', ''),
#           OptionHolder('max_filesize_unit', '', ''),
#           OptionHolder('min_filesize_unit', '', ''),
#           OptionHolder('extra_cmd_string', '', ''),
#           OptionHolder('direct_cmd_flag', '', False),
#           OptionHolder('direct_url_flag', '', False),
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
#           OptionHolder('downloader_config', '', False),
#           OptionHolder('save_path_list', '', []),
        ]


    # Public class methods


    def parse(self, media_data_obj, options_manager_obj,
    operation_type='real', scheduled_obj=None):

        """Called by downloads.DownloadWorker.prepare_download() and
        mainwin.MainWin.update_textbuffer() and several other functions.

        Converts the download options stored in the specified
        options.OptionsManager object into a list of youtube-dl command line
        options.

        Args:

            media_data_obj (media.Video, media.Channel, media.Playlist,
                media.Folder): The media data object being downloaded

            options_manager_obj (options.OptionsManager): The object containing
                the download options for this media data object

            operation_type (str): 'sim', 'real', 'custom_sim', 'custom_real',
                'classic_sim', 'classic_real', 'classic_custom' (matching
                possible values of downloads.DownloadManager.operation_type)

            scheduled_obj (media.Scheduled): If a scheduled download is
                involved, the corresponding object (so bandwidth limits can be
                extracted)

        Returns:

            List of strings with all the youtube-dl command line options

        """

        # Force youtube-dl's progress bar to be outputted as separate lines
        options_list = ['--newline']

        # Create a copy of the dictionary...
        copy_dict = options_manager_obj.options_dict.copy()
        # ...then modify various values in the copy. Set the 'video_format' and
        #   'all_formats' options
        self.build_video_format(media_data_obj, copy_dict, operation_type)
        # Set the 'min_filesize' and 'max_filesize' options
        self.build_file_sizes(copy_dict)
        # Set the 'limit_rate' option
        self.build_limit_rate(copy_dict, scheduled_obj)
        # Set the 'proxy' option
        self.build_proxy(copy_dict)

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

                if copy_dict['extract_audio'] \
                and value != option_holder_obj.default_value:
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

            elif option_holder_obj.name == 'cookies_path':
                cookies_path = copy_dict[option_holder_obj.name]
                options_list.append('--cookies')
                # If no path is specified, use a standard location for the
                #   cookie jar (otherwise youtube-dl(c) will write it to
                #   ../tartube/tartube)
                if cookies_path == '':
                    options_list.append(
                        os.path.abspath(
                            os.path.join(
                                self.app_obj.data_dir,
                                self.app_obj.cookie_file_name,
                            ),
                        ),
                    )
                else:
                    options_list.append(cookies_path)

            # For all other options, just check the value is valid
            elif option_holder_obj.check_requirements(copy_dict):
                value = copy_dict[option_holder_obj.name]

                if value != option_holder_obj.default_value:
                    options_list.append(option_holder_obj.switch)

                    if not option_holder_obj.is_boolean():
                        options_list.append(utils.to_string(value))

        # Parse the 'match_title_list' and 'reject_title_list'
        for item in copy_dict['match_title_list']:
            options_list.append('--match-title')
            options_list.append(item)

        for item in copy_dict['reject_title_list']:
            options_list.append('--reject-title')
            options_list.append(item)

        # Parse the 'subs_lang_list' option
        if copy_dict['write_subs'] \
        and not copy_dict['write_auto_subs'] \
        and not copy_dict['write_all_subs'] \
        and copy_dict['subs_lang_list']:

            options_list.append('--sub-lang')
            options_list.append(','.join(copy_dict['subs_lang_list']))

        # Parse the 'extractor_args_list' option
        for item in copy_dict['extractor_args_list']:
            options_list.append('--extractor-args')
            options_list.append(item)

        # Parse the 'save_path_list' option
        options_list = self.build_paths(
            media_data_obj,
            copy_dict,
            operation_type,
            options_list,
        )

        # Parse the 'extra_cmd_string' option, so it overrules everything else.
        #   The option can contain arguments inside double quotes "..."
        #   (arguments that can therefore contain whitespace)
        parsed_list = utils.parse_options(copy_dict['extra_cmd_string'])
        for item in parsed_list:
            options_list.append(item)

        # Parse the 'downloader_config' option, so it overrules everything
        #   else
        if copy_dict['downloader_config']:

            options_list.append('--config-location')
            options_list.append(utils.get_dl_config_path(self.app_obj))

        # Filter out yt-dlp options, if required. A list of them is specified
        #   in mainapp.TartubeApp.ytdlp_exclusive_options_dict
        if self.app_obj.ytdlp_filter_options_flag \
        and (
            self.app_obj.ytdl_fork is None \
            or self.app_obj.ytdl_fork != 'yt-dlp'
        ):
            filter_list = options_list.copy()
            options_list = []

            while filter_list:

                item = filter_list.pop(0)
                if item in self.app_obj.ytdlp_exclusive_options_dict:

                    if self.app_obj.ytdlp_exclusive_options_dict[item]:
                        # This option takes an argument
                        filter_list.pop(0)

                else:
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


    def build_limit_rate(self, copy_dict, scheduled_obj):

        """Called by self.parse().

        Build the value of the 'limit_rate' option and store it in the options
        dictionary.

        Args:

            copy_dict (dict): Copy of the original options dictionary

            scheduled_obj (media.Scheduled): If a scheduled download is
                involved, the corresponding object (so bandwidth limits can be
                extracted)

        """

        # Set the bandwidth limit (e.g. '50K'). If alternative performance
        #   limits currently apply, use that limit instead
        if self.app_obj.download_manager_obj \
        and scheduled_obj \
        and scheduled_obj.scheduled_bandwidth_apply_flag:

            # The bandwidth limit is divided equally between the workers
            limit = int(
                scheduled_obj.scheduled_bandwidth
                / len(self.app_obj.download_manager_obj.worker_list)
            )

            copy_dict['limit_rate'] = str(limit) + 'K'

        elif self.app_obj.download_manager_obj \
        and self.app_obj.download_manager_obj.alt_limits_flag \
        and self.app_obj.alt_bandwidth_apply_flag:

            limit = int(
                self.app_obj.alt_bandwidth
                / self.app_obj.alt_num_worker
            )

            copy_dict['limit_rate'] = str(limit) + 'K'

        elif self.app_obj.bandwidth_apply_flag:

            limit = int(
                self.app_obj.bandwidth_default
                / self.app_obj.num_worker_default
            )

            copy_dict['limit_rate'] = str(limit) + 'K'


    def build_proxy(self, copy_dict):

        """Called by self.parse().

        Build the value of the 'proxy' option and store it in the options
        dictionary.

        Args:

            copy_dict (dict): Copy of the original options dictionary.

        """

        # If the option is already specified, we use it. Otherwise, cycle
        #   through the proxies in the main appliation's list
        if not copy_dict['proxy']:

            proxy = self.app_obj.get_proxy()
            if proxy is not None:

                copy_dict['proxy'] = proxy


    def build_paths(self, media_data_obj, copy_dict, operation_type, \
    options_list):

        """Called by self.parse().

        Build the value of the 'save_path_list' option, and add it directly to
        the options list.

        Args:

            media_data_obj (media.Video, media.Channel, media.Playlist,
                media.Folder): The media data object being downloaded

            copy_dict (dict): Copy of the original options dictionary

            operation_type (str): 'sim', 'real', 'custom_sim', 'custom_real',
                'classic_sim', 'classic_real', 'classic_custom' (matching
                possible values of downloads.DownloadManager.operation_type)

            options_list (list): List of download options compiled so far; this
                function adds options directly to the list

        Return values:

            The modified options_list

        """

        # First, set the download directory

        override_name = copy_dict['use_fixed_folder']

        if operation_type == 'classic_sim' \
        or operation_type == 'classic_real' \
        or operation_type == 'classic_custom':

            # Special case: if a download operation was launched from the
            #   Classic Mode tab, the directory is specified in that tab
            dir_path = media_data_obj.dummy_dir

        elif not isinstance(media_data_obj, media.Video) \
        and override_name is not None \
        and override_name in self.app_obj.media_name_dict:

            # Because of the override, save all videos to a system folder
            other_dbid = self.app_obj.media_name_dict[override_name]
            other_obj = self.app_obj.media_reg_dict[other_dbid]
            dir_path = other_obj.get_default_dir(self.app_obj)

        elif isinstance(media_data_obj, media.Video):
            dir_path = media_data_obj.parent_obj.get_actual_dir(self.app_obj)

        else:
            dir_path = media_data_obj.get_actual_dir(self.app_obj)

        # Secondly, set the file output template, which may be preceded by the
        #   download directory

        # (When 'output_format_list' is specified, then 'output_format' and
        #   'output_template' are ignored. However, 'output_format_list' is
        #   normally only used with yt-dlp)
        if not copy_dict['output_format_list'] \
        or self.app_obj.ytdl_fork is None \
        or self.app_obj.ytdl_fork != 'yt-dlp' \
        or not self.app_obj.ytdlp_filter_options_flag:
            # Set the youtube-dl output template for the video's file
            template \
            = formats.FILE_OUTPUT_CONVERT_DICT[copy_dict['output_format']]
            # In the case of copy_dict['output_format'] = 0
            if template is None:
                template = copy_dict['output_template']

            options_list.append('--output')

            # (When 'output_path_list' is specified, the template is used
            #   without a preceding directory path)
            if copy_dict['output_path_list']:
                options_list.append(template)
            else:
                options_list.append(
                    os.path.abspath(os.path.join(dir_path, template)),
                )

        else:

            for item in copy_dict['output_format_list']:
                options_list.append('--output')
                options_list.append(item)

        # Thirdly, set the yt-dlp option 'output_path_list'
        if copy_dict['output_path_list']:

            for item in copy_dict['output_path_list']:
                options_list.append('--paths')
                options_list.append(item)

        return options_list


    def build_video_format(self, media_data_obj, copy_dict, operation_type):

        """Called by self.parse().

        Build the value of the 'video_format' and 'all_formats' options and
        store them in the options dictionary.

        Args:

            media_data_obj (media.Video, media.Channel, media.Playlist,
                media.Folder): The media data object being downloaded

            copy_dict (dict): Copy of the original options dictionary

            operation_type (str): 'sim', 'real', 'custom_sim', 'custom_real',
                'classic_sim', 'classic_real', 'classic_custom' (matching
                possible values of downloads.DownloadManager.operation_type)

        """

        if isinstance(media_data_obj, media.Video):

            # Special case: if a download operation was launched from the
            #   Classic Mode tab, the video format may be specified by that tab
            if (
                operation_type == 'classic_sim' \
                or operation_type == 'classic_real' \
                or operation_type == 'classic_custom'
            ) and media_data_obj.dummy_format is not None:

                format_str = media_data_obj.dummy_format
                convert_flag = False
                # If format_str is not None, then it is one of Tartube's
                #   standard media formats, or one of those values preceded by
                #   'convert_'. Remove the trailing text, if found
                match = re.search('^convert_(.*)$', format_str)
                if match:
                    format_str = match.group(1)
                    convert_flag = True

                if not convert_flag:

                    # Download the video in the specified format, if available

                    # Ignore all video/audio formats except the one specified
                    #   by the user in the Classic Mode tab
                    copy_dict['video_format'] = format_str
                    copy_dict['all_formats'] = False
                    copy_dict['video_format_list'] = []
                    copy_dict['video_format_mode'] = ''
                    copy_dict['recode_video'] = ''

                    # v2.1.009: Since the user doesn't have the possibility of
                    #   setting the -f and --merge-output-format options to the
                    #   same value (e.g. 'mp4'), we must do so artificially
                    copy_dict['merge_output_format'] = format_str

                    return

                elif format_str in formats.VIDEO_FORMAT_DICT:

                    # Converting video formats requires post-processing
                    # Ignore all video/audio formats except the one specified
                    #   by the user in the Classic Mode tab
                    copy_dict['video_format'] = '0'
                    copy_dict['all_formats'] = False
                    copy_dict['video_format_list'] = []
                    copy_dict['video_format_mode'] = ''
                    copy_dict['recode_video'] = ''

                    # v2.1.009: Since the user doesn't have the possibility of
                    #   setting the -f and --merge-output-format options to the
                    #   same value (e.g. 'mp4'), we must do so artificially
                    copy_dict['merge_output_format'] = format_str

                    return

                elif format_str in formats.AUDIO_FORMAT_DICT:

                    # Converting audio formats requires post-processing
                    copy_dict['video_format'] = '0'
                    copy_dict['all_formats'] = False
                    copy_dict['video_format_list'] = []
                    copy_dict['video_format_mode'] = ''
                    copy_dict['extract_audio'] = True
                    copy_dict['audio_format'] = format_str
                    copy_dict['recode_video'] = ''

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
        if operation_type == 'sim' or operation_type == 'classic_sim':

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
