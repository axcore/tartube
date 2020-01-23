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


"""Constant variables used in various parts of the code."""


# Import Gtk modules
#   ...


# Import other modules
import datetime


# Import our modules
#   ...


# Some icons are different at Christmas
today = datetime.date.today()
day = today.strftime("%d")
month = today.strftime("%m")
if (int(month) == 12 and int(day) >= 24) \
or (int(month) == 1 and int(day) <= 5):
    xmas_flag = True
else:
    xmas_flag = False

# Used by utils.format_bytes()
KILO_SIZE = 1024.0
FILESIZE_METRIC_LIST = [
    "B",
    "KiB",
    "MiB",
    "GiB",
    "TiB",
    "PiB",
    "EiB",
    "ZiB",
    "YiB",
]

# Main stages of the download operation
MAIN_STAGE_QUEUED = 'Queued'
MAIN_STAGE_ACTIVE = 'Active'
MAIN_STAGE_PAUSED = 'Paused'                # (not actually used)
MAIN_STAGE_COMPLETED = 'Completed'          # (not actually used)
MAIN_STAGE_ERROR = 'Error'
# Sub-stages of the 'Active' stage
ACTIVE_STAGE_PRE_PROCESS = 'Pre-processing'
ACTIVE_STAGE_DOWNLOAD = 'Downloading'
ACTIVE_STAGE_POST_PROCESS = 'Post-processing'
ACTIVE_STAGE_CHECKING = 'Checking'
# Sub-stages of the 'Completed' stage
COMPLETED_STAGE_FINISHED = 'Finished'
COMPLETED_STAGE_WARNING = 'Warning'
COMPLETED_STAGE_ALREADY = 'Already downloaded'
# Sub-stages of the 'Error' stage
ERROR_STAGE_ERROR = 'Error'                 # (not actually used)
ERROR_STAGE_STOPPED = 'Stopped'
ERROR_STAGE_ABORT = 'Filesize abort'


# Standard dictionaries
FILE_OUTPUT_NAME_DICT = {
    0: 'ID',
    1: 'Title',
    2: 'Title + ID',
    3: 'Custom',
    4: 'Title + Quality',
    5: 'Title + ID + Quality',
}

FILE_OUTPUT_CONVERT_DICT = {
    0: '%(id)s.%(ext)s',
    1: '%(title)s.%(ext)s',
    2: '%(title)s-%(id)s.%(ext)s',
    3: None,
    4: '%(title)s-%(height)sp.%(ext)s',
    5: '%(title)s-%(id)s-%(height)sp.%(ext)s',
}

video_option_setup_list = [
    # List of YouTube extractor (format) codes, based on the original list in
    #   youtube-dl-gui, and supplemented by this list:
    #
    #   https://gist.github.com/sidneys/7095afe4da4ae58694d128b1034e01e2
    #
    # Unfortunately, as of late September 2019, that list was already out of
    #   date
    # Unfortunately, the list is YouTube-specific, and will not necessarily
    #   work on other websites
    #
    # I'm not sure about the meaning of some extractor codes; in those cases,
    #   I add the code itself to distinguish it from similar codes (e.g.
    #   compare codes 18 and 396)
    #
    # Dummy extractor codes - progressive scan resolutions
    '144p',     'Any format [144p]',                False,
    '240p',     'Any format [240p]',                False,
    '360p',     'Any format [360p]',                False,
    '480p',     'Any format [480p]',                False,
    '720p',     'Any format [720p]',                False,
    '720p60',   'Any format [720p 60fps]',          False,
    '1080p',    'Any format [1080p]',               False,
    '1080p60',  'Any format [1080p 60fps]',         False,
    '1440p',    'Any format [1440p]',               False,
    '1440p60',  'Any format [1440p 60fps]',         False,
    '2160p',    'Any format [2160p]',               False,
    '2160p60',  'Any format [2160p 60fps]',         False,
    '4320p',    'Any format [4320p]',               False,
    '4320p60',  'Any format [4320p 60fps]',         False,
    # Dummy extractor codes - other
    '3gp',      '3gp',                              False,
    'flv',      'flv',                              False,
    'm4a',      'm4a',                              True,
    'mp4',      'mp4',                              False,
    'webm',     'webm',                             False,
    # Real extractor codes
    '17',       '3gp [144p]',                       False,
    '36',       '3gp [240p]',                       False,
    '5',        'flv [240p]',                       False,
    '6',        'flv [270p]',                       False,
    '34',       'flv [360p]',                       False,
    '35',       'flv [480p]',                       False,
    # v1.3.037 - not sure whether the HLS format codes should be added here, or
    #   not. 'hls' has not been added as a dummy extractor code because
    #   youtube-dl doesn't support that
    '151',      'hls [72p]',                        False,
    '132',      'hls [240p]',                       False,
    '92',       'hls [240p] (3D)',                  False,
    '93',       'hls [360p] (3D)',                  False,
    '94',       'hls [480p] (3D)',                  False,
    '95',       'hls [720p] (3D)',                  False,
    '96',       'hls [1080p]',                      False,
    '139',      'm4a 48k (DASH Audio)',             True,
    '140',      'm4a 128k (DASH Audio)',            True,
    '141',      'm4a 256k (DASH Audio)',            True,
    '18',       'mp4 [360p]',                       False,
    '22',       'mp4 [720p]',                       False,
    '37',       'mp4 [1080p]',                      False,
    '38',       'mp4 [4K]',                         False,
    '160',      'mp4 [144p] (DASH Video)',          False,
    '133',      'mp4 [240p] (DASH Video)',          False,
    '134',      'mp4 [360p] (DASH Video)',          False,
    '135',      'mp4 [480p] (DASH Video)',          False,
    '136',      'mp4 [720p] (DASH Video)',          False,
    '298',      'mp4 [720p 60fps] (DASH Video)',    False,
    '137',      'mp4 [1080p] (DASH Video)',         False,
    '299',      'mp4 [1080p 60fps] (DASH Video)',   False,
    '264',      'mp4 [1440p] (DASH Video)',         False,
    '138',      'mp4 [2160p] (DASH Video)',         False,
    '266',      'mp4 [2160p 60fps] (DASH Video)',   False,
    '82',       'mp4 [360p] (3D)',                  False,
    '83',       'mp4 [480p] (3D)',                  False,
    '84',       'mp4 [720p] (3D)',                  False,
    '85',       'mp4 [1080p] (3D)',                 False,
    '394',      'mp4 [144p] <394>',                 False,
    '395',      'mp4 [240p] <395>',                 False,
    '396',      'mp4 [360p] <396>',                 False,
    '397',      'mp4 [480p] <397>',                 False,
    '398',      'mp4 [720p] <398>',                 False,
    '399',      'mp4 [1080p] <399>',                False,
    '400',      'mp4 [1440p] <400>',                False,
    '401',      'mp4 [2160p] <401>',                False,
    '402',      'mp4 [2880p] <402>',                False,
    '43',       'webm [360p]',                      False,
    '44',       'webm [480p]',                      False,
    '45',       'webm [720p]',                      False,
    '46',       'webm [1080p]',                     False,
    '242',      'webm [240p] (DASH Video)',         False,
    '243',      'webm [360p] (DASH Video)',         False,
    '244',      'webm [480p] (DASH Video)',         False,
    '247',      'webm [720p] (DASH Video)',         False,
    '302',      'webm [720p 60fps] (DASH Video)',   False,
    '248',      'webm [1080p] (DASH Video)',        False,
    '303',      'webm [1080p 60fps] (DASH Video)',  False,
    '271',      'webm [1440p] (DASH Video)',        False,
    '308',      'webm [1440p 60fps] (DASH Video)',  False,
    '313',      'webm [2160p] (DASH Video)',        False,
    '315',      'webm [2160p 60fps] (DASH Video)',  False,
    '272',      'webm [4320p] (DASH Video)',        False,
    '100',      'webm [360p] (3D)',                 False,
    '101',      'webm [480p] (3D)',                 False,
    '102',      'webm [720p] (3D)',                 False,
    '330',      'webm [144p 60fps] (HDR)',          False,
    '331',      'webm [240p 60fps] (HDR)',          False,
    '332',      'webm [360p 60fps] (HDR)',          False,
    '333',      'webm [480p 60fps] (HDR)',          False,
    '334',      'webm [720p 60fps] (HDR)',          False,
    '335',      'webm [1080p 60fps] (HDR)',         False,
    '336',      'webm [1440p 60fps] (HDR)',         False,
    '337',      'webm [2160p 60fps] (HDR)',         False,
    '249',      'webm (50k Audio)',                 True,
    '250',      'webm (70k Audio)',                 True,
    '251',      'webm (160k Audio)',                True,
    '219',      'webm [144p] <219>',                False,
    '278',      'webm [144p] <278>',                False,
    '167',      'webm [360p] <167>',                False,
    '168',      'webm [480p] <168>',                False,
    '218',      'webm [480p] <218>',                False,
    '245',      'webm [480p] <245>',                False,
    '246',      'webm [480p] <246>',                False,
    '169',      'webm [1080p] <169>',               False,
    '171',      'webm 48k (DASH Audio)',            True,
    '172',      'webm 256k (DASH Audio)',           True,
]

VIDEO_OPTION_LIST = []
VIDEO_ONLY_OPTION_LIST = []
VIDEO_OPTION_DICT = {}

while video_option_setup_list:
    value = video_option_setup_list.pop(0)
    key = video_option_setup_list.pop(0)
    audio_only_flag = video_option_setup_list.pop(0)

    VIDEO_OPTION_LIST.append(key)
    VIDEO_OPTION_DICT[key] = value
    if not audio_only_flag:
        VIDEO_ONLY_OPTION_LIST.append(key)

video_resolution_setup_list = [
    '144p',     '144',
    '240p',     '240',
    '360p',     '360',
    '480p',     '480',
    '720p',     '720',
    '720p60',   '720',
    '1080p',    '1080',
    '1080p60',  '1080',
    '1440p',    '1440',
    '1440p60',  '1440',
    '2160p',    '2160',
    '2160p60',  '2160',
    '4320p',    '4320',
    '4320p60',  '4320',
]

VIDEO_RESOLUTION_LIST = []
VIDEO_RESOLUTION_DICT = {}
VIDEO_RESOLUTION_DEFAULT = '720p'

while video_resolution_setup_list:
    key = video_resolution_setup_list.pop(0)
    value = video_resolution_setup_list.pop(0)

    VIDEO_RESOLUTION_LIST.append(key)
    VIDEO_RESOLUTION_DICT[key] = value

VIDEO_FPS_DICT = {
    # Contains a subset of VIDEO_RESOLUTION_DICT. Only required to distinguish
    #   30fps from 60fps formats, so this
    '720p60':   '60',
    '1080p60':  '60',
    '1440p60':  '60',
    '2160p60':  '60',
    '4320p60':  '60',
}

video_format_setup_list = ['mp4', 'flv', 'ogg', 'webm', 'mkv', 'avi']

VIDEO_FORMAT_LIST = []
VIDEO_FORMAT_DICT = {}

while video_format_setup_list:
    key = value = video_format_setup_list.pop(0)

    VIDEO_FORMAT_LIST.append(key)
    VIDEO_FORMAT_DICT[key] = value

audio_setup_list = ['mp3', 'wav', 'aac', 'm4a', 'vorbis', 'opus', 'flac']

AUDIO_FORMAT_LIST = []
AUDIO_FORMAT_DICT = {}

while audio_setup_list:
    key = value = audio_setup_list.pop(0)

    AUDIO_FORMAT_LIST.append(key)
    AUDIO_FORMAT_DICT[key] = value

FILE_SIZE_UNIT_LIST = [
    ['Bytes', ''],
    ['Kilobytes', 'k'],
    ['Megabytes', 'm'],
    ['Gigabytes', 'g'],
    ['Terabytes', 't'],
    ['Petabytes', 'p'],
    ['Exabytes', 'e'],
    ['Zetta', 'z'],
    ['Yotta', 'y'],
]

# ISO 639-1 Language Codes
LANGUAGE_CODE_LIST = [
    # English is top of the list, because it's the default setting in
    #   options.OptionsManager
    ['English', 'en'],
    ['Abkhazian', 'ab'],
    ['Afar', 'aa'],
    ['Afrikaans', 'af'],
    ['Akan', 'ak'],
    ['Albanian', 'sq'],
    ['Amharic', 'am'],
    ['Arabic', 'ar'],
    ['Aragonese', 'an'],
    ['Armenian', 'hy'],
    ['Assamese', 'as'],
    ['Avaric', 'av'],
    ['Avestan', 'ae'],
    ['Aymara', 'ay'],
    ['Azerbaijani', 'az'],
    ['Bambara', 'bm'],
    ['Bashkir', 'ba'],
    ['Basque', 'eu'],
    ['Belarusian', 'be'],
    ['Bengali (Bangla)', 'bn'],
    ['Bihari', 'bh'],
    ['Bislama', 'bi'],
    ['Bosnian', 'bs'],
    ['Breton', 'br'],
    ['Bulgarian', 'bg'],
    ['Burmese', 'my'],
    ['Catalan', 'ca'],
    ['Chamorro', 'ch'],
    ['Chechen', 'ce'],
    ['Chichewa, Chewa, Nyanja', 'ny'],
    ['Chinese', 'zh'],
    ['Chinese (Simplified)', 'zh-Hans'],
    ['Chinese (Traditional)', 'zh-Hant'],
    ['Chuvash', 'cv'],
    ['Cornish', 'kw'],
    ['Corsican', 'co'],
    ['Cree', 'cr'],
    ['Croatian', 'hr'],
    ['Czech', 'cs'],
    ['Danish', 'da'],
    ['Divehi, Dhivehi, Maldivian', 'dv'],
    ['Dutch', 'nl'],
    ['Dzongkha', 'dz'],
    ['Esperanto', 'eo'],
    ['Estonian', 'et'],
    ['Ewe', 'ee'],
    ['Faroese', 'fo'],
    ['Fijian', 'fj'],
    ['Finnish', 'fi'],
    ['French', 'fr'],
    ['Fula, Fulah, Pulaar, Pular', 'ff'],
    ['Galician', 'gl'],
    ['Gaelic (Scottish)', 'gd'],
    ['Gaelic (Manx)', 'gv'],
    ['Georgian', 'ka'],
    ['German', 'de'],
    ['Greek', 'el'],
    ['Greenlandic', 'kl'],
    ['Guarani', 'gn'],
    ['Gujarati', 'gu'],
    ['Haitian Creole', 'ht'],
    ['Hausa', 'ha'],
    ['Hebrew', 'he'],
    ['Herero', 'hz'],
    ['Hindi', 'hi'],
    ['Hiri Motu', 'ho'],
    ['Hungarian', 'hu'],
    ['Icelandic', 'is'],
    ['Ido', 'io'],
    ['Igbo', 'ig'],
    ['Indonesian', 'id'],
    ['Interlingua', 'ia'],
    ['Interlingue', 'ie'],
    ['Inuktitut', 'iu'],
    ['Inupiak', 'ik'],
    ['Irish', 'ga'],
    ['Italian', 'it'],
    ['Japanese', 'ja'],
    ['Javanese', 'jv'],
    ['Kalaallisut, Greenlandic', 'kl'],
    ['Kannada', 'kn'],
    ['Kanuri', 'kr'],
    ['Kashmiri', 'ks'],
    ['Kazakh', 'kk'],
    ['Khmer', 'km'],
    ['Kikuyu', 'ki'],
    ['Kinyarwanda (Rwanda)', 'rw'],
    ['Kirundi', 'rn'],
    ['Kyrgyz', 'ky'],
    ['Komi', 'kv'],
    ['Kongo', 'kg'],
    ['Korean', 'ko'],
    ['Kurdish', 'ku'],
    ['Kwanyama', 'kj'],
    ['Lao', 'lo'],
    ['Latin', 'la'],
    ['Latvian (Lettish)', 'lv'],
    ['Limburgish ( Limburger)', 'li'],
    ['Lingala', 'ln'],
    ['Lithuanian', 'lt'],
    ['Luga-Katanga', 'lu'],
    ['Luganda, Ganda', 'lg'],
    ['Luxembourgish', 'lb'],
    ['Manx', 'gv'],
    ['Macedonian', 'mk'],
    ['Malagasy', 'mg'],
    ['Malay', 'ms'],
    ['Malayalam', 'ml'],
    ['Maltese', 'mt'],
    ['Maori', 'mi'],
    ['Marathi', 'mr'],
    ['Marshallese', 'mh'],
    ['Moldavian', 'mo'],
    ['Mongolian', 'mn'],
    ['Nauru', 'na'],
    ['Navajo', 'nv'],
    ['Ndonga', 'ng'],
    ['Northern Ndebele', 'nd'],
    ['Nepali', 'ne'],
    ['Norwegian', 'no'],
    ['Norwegian bokmål', 'nb'],
    ['Norwegian nynorsk', 'nn'],
    ['Nuosu', 'ii'],
    ['Occitan', 'oc'],
    ['Ojibwe', 'oj'],
    ['Old Church Slavonic, Old Bulgarian', 'cu'],
    ['Oriya', 'or'],
    ['Oromo (Afaan Oromo)', 'om'],
    ['Ossetian', 'os'],
    ['Pāli', 'pi'],
    ['Pashto, Pushto', 'ps'],
    ['Persian (Farsi)', 'fa'],
    ['Polish', 'pl'],
    ['Portuguese', 'pt'],
    ['Punjabi (Eastern)', 'pa'],
    ['Quechua', 'qu'],
    ['Romansh', 'rm'],
    ['Romanian', 'ro'],
    ['Russian', 'ru'],
    ['Sami', 'se'],
    ['Samoan', 'sm'],
    ['Sango', 'sg'],
    ['Sanskrit', 'sa'],
    ['Serbian', 'sr'],
    ['Serbo-Croatian', 'sh'],
    ['Sesotho', 'st'],
    ['Setswana', 'tn'],
    ['Shona', 'sn'],
    ['Sichuan Yi', 'ii'],
    ['Sindhi', 'sd'],
    ['Sinhalese', 'si'],
    ['Siswati', 'ss'],
    ['Slovak', 'sk'],
    ['Slovenian', 'sl'],
    ['Somali', 'so'],
    ['Southern Ndebele', 'nr'],
    ['Spanish', 'es'],
    ['Sundanese', 'su'],
    ['Swahili (Kiswahili)', 'sw'],
    ['Swati', 'ss'],
    ['Swedish', 'sv'],
    ['Tagalog', 'tl'],
    ['Tahitian', 'ty'],
    ['Tajik', 'tg'],
    ['Tamil', 'ta'],
    ['Tatar', 'tt'],
    ['Telugu', 'te'],
    ['Thai', 'th'],
    ['Tibetan', 'bo'],
    ['Tigrinya', 'ti'],
    ['Tonga', 'to'],
    ['Tsonga', 'ts'],
    ['Turkish', 'tr'],
    ['Turkmen', 'tk'],
    ['Twi', 'tw'],
    ['Uyghur', 'ug'],
    ['Ukrainian', 'uk'],
    ['Urdu', 'ur'],
    ['Uzbek', 'uz'],
    ['Venda', 've'],
    ['Vietnamese', 'vi'],
    ['Volapük', 'vo'],
    ['Wallon', 'wa'],
    ['Welsh', 'cy'],
    ['Wolof', 'wo'],
    ['Western Frisian', 'fy'],
    ['Xhosa', 'xh'],
    ['Yiddish', 'yi'],
    ['Yoruba', 'yo'],
    ['Zhuang, Chuang', 'za'],
    ['Zulu', 'zu'],
]

if not xmas_flag:
    DIALOGUE_ICON_DICT = {
        'system_icon': 'system_icon_64.png',
    }
else:
    DIALOGUE_ICON_DICT = {
        'system_icon': 'system_icon_xmas_64.png',
    }

if not xmas_flag:
    STATUS_ICON_DICT = {
        'default_icon': 'status_default_icon_64.png',
        'check_icon': 'status_check_icon_64.png',
        'download_icon': 'status_download_icon_64.png',
        'update_icon': 'status_update_icon_64.png',
        'refresh_icon': 'status_refresh_icon_64.png',
    }
else:
    STATUS_ICON_DICT = {
        'default_icon': 'status_default_icon_xmas_64.png',
        'check_icon': 'status_check_icon_xmas_64.png',
        'download_icon': 'status_download_icon_xmas_64.png',
        'update_icon': 'status_update_icon_xmas_64.png',
        'refresh_icon': 'status_refresh_icon_xmas_64.png',
    }

TOOLBAR_ICON_DICT = {
    'tool_channel_large': 'channel_large.png',
    'tool_channel_small': 'channel_small.png',
    'tool_check_large': 'check_large.png',
    'tool_check_small': 'check_small.png',
    'tool_download_large': 'download_large.png',
    'tool_download_small': 'download_small.png',
    'tool_folder_large': 'folder_large.png',
    'tool_folder_small': 'folder_small.png',
    'tool_playlist_large': 'playlist_large.png',
    'tool_playlist_small': 'playlist_small.png',
    'tool_quit_large': 'quit_large.png',
    'tool_quit_small': 'quit_small.png',
    'tool_stop_large': 'stop_large.png',
    'tool_stop_small': 'stop_small.png',
    'tool_switch_large': 'switch_large.png',
    'tool_switch_small': 'switch_small.png',
    'tool_test_large': 'test_large.png',
    'tool_test_small': 'test_small.png',
    'tool_video_large': 'video_large.png',
    'tool_video_small': 'video_small.png',
}

LARGE_ICON_DICT = {
    'video_both_large': 'video_both.png',
    'video_left_large': 'video_left.png',
    'video_none_large': 'video_none.png',
    'video_right_large': 'video_right.png',

    'channel_both_large': 'channel_both.png',
    'channel_left_large': 'channel_left.png',
    'channel_none_large': 'channel_none.png',
    'channel_right_large': 'channel_right.png',

    'playlist_both_large': 'playlist_both.png',
    'playlist_left_large': 'playlist_left.png',
    'playlist_none_large': 'playlist_none.png',
    'playlist_right_large': 'playlist_right.png',

    'folder_both_large': 'folder_yellow_both.png',
    'folder_left_large': 'folder_yellow_left.png',
    'folder_none_large': 'folder_yellow_none.png',
    'folder_right_large': 'folder_yellow_right.png',

    'folder_private_both_large': 'folder_red_both.png',
    'folder_private_left_large': 'folder_red_left.png',
    'folder_private_none_large': 'folder_red_none.png',
    'folder_private_right_large': 'folder_red_right.png',

    'folder_fixed_both_large': 'folder_green_both.png',
    'folder_fixed_left_large': 'folder_green_left.png',
    'folder_fixed_none_large': 'folder_green_none.png',
    'folder_fixed_right_large': 'folder_green_right.png',

    'folder_temp_both_large': 'folder_blue_both.png',
    'folder_temp_left_large': 'folder_blue_left.png',
    'folder_temp_none_large': 'folder_blue_none.png',
    'folder_temp_right_large': 'folder_blue_right.png',

    'folder_no_parent_both_large': 'folder_black_both.png',
    'folder_no_parent_left_large': 'folder_black_left.png',
    'folder_no_parent_none_large': 'folder_black_none.png',
    'folder_no_parent_right_large': 'folder_black_right.png',

    'copy_large': 'copy.png',
    'hand_left_large': 'hand_left.png',
    'hand_right_large': 'hand_right.png',
    'question_large': 'question.png',
    'warning_large': 'warning.png',
}

SMALL_ICON_DICT = {
    'video_small': 'video.png',
    'channel_small': 'channel.png',
    'playlist_small': 'playlist.png',
    'folder_small': 'folder.png',

    'archived_small': 'archived.png',
    'arrow_up_small': 'arrow_up.png',
    'arrow_down_small': 'arrow_down.png',
    'check_small': 'check.png',
    'download_small': 'download.png',
    'error_small': 'error.png',
    'folder_black_small': 'folder_black.png',
    'folder_blue_small': 'folder_blue.png',
    'folder_green_small': 'folder_green.png',
    'folder_red_small': 'folder_red.png',
    'have_file_small': 'have_file.png',
    'no_file_small': 'no_file.png',
    'system_error_small': 'system_error.png',
    'system_warning_small': 'system_warning.png',
    'warning_small': 'warning.png',
}

if not xmas_flag:
    WIN_ICON_LIST = [
        'system_icon_16.png',
        'system_icon_24.png',
        'system_icon_32.png',
        'system_icon_48.png',
        'system_icon_64.png',
        'system_icon_128.png',
        'system_icon_256.png',
        'system_icon_512.png',
    ]
else:
    WIN_ICON_LIST = [
        'system_icon_xmas_16.png',
        'system_icon_xmas_24.png',
        'system_icon_xmas_32.png',
        'system_icon_xmas_48.png',
        'system_icon_xmas_64.png',
        'system_icon_xmas_128.png',
        'system_icon_xmas_256.png',
        'system_icon_xmas_512.png',
    ]
