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


"""Constant variables used in various parts of the code."""


# Import Gtk modules
#   ...


# Import other modules
#   ...


# Import our modules
#   ...


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
    # Extractor code - description
    # !!! TODO: Add a large range of extractor codes (currently, can't find
    #   a list)
    '3gp',  '3gp',
    '17',   '3gp [144p]',
    '36',   '3gp [240p]',
    'flv',  'flv',
    '5',    'flv [240p]',
    '34',   'flv [360p]',
    '35',   'flv [480p]',
    'webm', 'webm',
    '43',   'webm [360p]',
    '44',   'webm [480p]',
    '45',   'webm [720p]',
    '46',   'webm [1080p]',
    'mp4',  'mp4',
    '18',   'mp4 [360p]',
    '22',   'mp4 [720p]',
    '37',   'mp4 [1080p]',
    '38',   'mp4 [4K]',
    '160',  'mp4 [144p] (DASH Video)',
    '133',  'mp4 [240p] (DASH Video)',
    '134',  'mp4 [360p] (DASH Video)',
    '135',  'mp4 [480p] (DASH Video)',
    '136',  'mp4 [720p] (DASH Video)',
    '137',  'mp4 [1080p] (DASH Video)',
    '264',  'mp4 [1440p] (DASH Video)',
    '138',  'mp4 [2160p] (DASH Video)',
    '242',  'webm [240p] (DASH Video)',
    '243',  'webm [360p] (DASH Video)',
    '244',  'webm [480p] (DASH Video)',
    '247',  'webm [720p] (DASH Video)',
    '248',  'webm [1080p] (DASH Video)',
    '271',  'webm [1440p] (DASH Video)',
    '272',  'webm [2160p] (DASH Video)',
    '82',   'mp4 [360p] (3D)',
    '83',   'mp4 [480p] (3D)',
    '84',   'mp4 [720p] (3D)',
    '85',   'mp4 [1080p] (3D)',
    '100',  'webm [360p] (3D)',
    '101',  'webm [480p] (3D)',
    '102',  'webm [720p] (3D)',
    'wav',  'wav',                      # Not imported from youtube-dl-gui
    'm4a',  'm4a',                      # Not imported from youtube-dl-gui
    '139',  'm4a 48k (DASH Audio)',
    '140',  'm4a 128k (DASH Audio)',
    '141',  'm4a 256k (DASH Audio)',
    '171',  'webm 48k (DASH Audio)',
    '172',  'webm 256k (DASH Audio)',
    'aac',  'aac',                      # Not imported from youtube-dl-gui
    'mp3',  'mp3',                      # Not imported from youtube-dl-gui
    'ogg',  'ogg',                      # Not imported from youtube-dl-gui
]

VIDEO_OPTION_LIST = []
VIDEO_OPTION_DICT = {}

while video_option_setup_list:
    value = video_option_setup_list.pop(0)
    key = video_option_setup_list.pop(0)

    VIDEO_OPTION_LIST.append(key)
    VIDEO_OPTION_DICT[key] = value

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

DIALOGUE_ICON_DICT = {
    'system_icon': 'system_icon_64.png',
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

    'folder_no_parent_both_large': 'folder_blue_both.png',
    'folder_no_parent_left_large': 'folder_blue_left.png',
    'folder_no_parent_none_large': 'folder_blue_none.png',
    'folder_no_parent_right_large': 'folder_blue_right.png',
}

SMALL_ICON_DICT = {
    'video_small': 'video.png',
    'channel_small': 'playlist.png',
    'playlist_small': 'channel.png',
    'folder_small': 'folder.png',

    'download_small': 'download.png',
    'check_small': 'check.png',
    'have_file_small': 'have_file.png',
    'no_file_small': 'no_file.png',
    'ok_small': 'ok.png',
    'error_small': 'error.png',
    'warning_small': 'warning.png',
    'system_error_small': 'system_error.png',
    'system_warning_small': 'system_warning.png',
}

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
