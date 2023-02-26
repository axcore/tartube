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


"""Constant variables used in various parts of the code."""


# Import Gtk modules
#   ...


# Import other modules
import datetime
import re


# Import our modules
# Use same gettext translations
from mainapp import _


# Supported locales: <ISO 639-1>_<ISO 3166-1 alpha-2>
locale_setup_list = [
    'en_GB',    'English',
    'en_US',    'English (American)',
    'es',       'Español',
    'fr',       'Français',
    'ko_KR',    '한국어',
    'nl_NL',    'Nederlands',
    'ru',       'русский',
    'tr',       'Türkçe',
    'vi',       'Tiếng Việt',
]

LOCALE_DEFAULT = locale_setup_list[0]
LOCALE_LIST = []
LOCALE_DICT = {}

while locale_setup_list:
    key = locale_setup_list.pop(0)
    value = locale_setup_list.pop(0)

    LOCALE_LIST.append(key)
    LOCALE_DICT[key] = value

# Some icons are different at Christmas and on national holidays
today = datetime.date.today()
day = today.strftime('%d')
month = today.strftime('%m')

xmas_flag = False
eesti_flag = False
anglo_flag = False
if (int(month) == 12 and int(day) >= 24) \
or (int(month) == 1 and int(day) <= 5):
    xmas_flag = True
elif (int(month) == 2 and int(day) == 24) \
or (int(month) == 8 and int(day) == 20):
    eesti_flag = True
elif (int(month) == 4 and int(day) == 23) \
or (int(month) == 11 and int(day) == 14):
    anglo_flag = True

language_setup_list = [
    # ISO 639-1 Language Codes (with one extra key-value pair to handle live
    #   chat)
    # English is top of the list, because it's the default setting in
    #   options.OptionsManager
    # NB These values must not contain square brackets [...]
    _('English'), 'en',
    'YouTube live chat', 'live_chat',
    'Abkhazian', 'ab',
    'Afar', 'aa',
    'Afrikaans', 'af',
    'Akan', 'ak',
    'Albanian', 'sq',
    'Amharic', 'am',
    'Arabic', 'ar',
    'Aragonese', 'an',
    'Armenian', 'hy',
    'Assamese', 'as',
    'Avaric', 'av',
    'Avestan', 'ae',
    'Aymara', 'ay',
    'Azerbaijani', 'az',
    'Bambara', 'bm',
    'Bashkir', 'ba',
    'Basque', 'eu',
    'Belarusian', 'be',
    'Bengali (Bangla)', 'bn',
    'Bihari', 'bh',
    'Bislama', 'bi',
    'Bosnian', 'bs',
    'Breton', 'br',
    'Bulgarian', 'bg',
    'Burmese', 'my',
    'Catalan', 'ca',
    'Chamorro', 'ch',
    'Chechen', 'ce',
    'Chichewa, Chewa, Nyanja', 'ny',
    'Chinese', 'zh',
    'Chinese (Simplified)', 'zh-Hans',
    'Chinese (Traditional)', 'zh-Hant',
    'Chuvash', 'cv',
    'Cornish', 'kw',
    'Corsican', 'co',
    'Cree', 'cr',
    'Croatian', 'hr',
    'Czech', 'cs',
    'Danish', 'da',
    'Divehi, Dhivehi, Maldivian', 'dv',
    _('Dutch'), 'nl',
    'Dzongkha', 'dz',
    'Esperanto', 'eo',
    'Estonian', 'et',
    'Ewe', 'ee',
    'Faroese', 'fo',
    'Fijian', 'fj',
    'Finnish', 'fi',
    _('French'), 'fr',
    'Fula, Fulah, Pulaar, Pular', 'ff',
    'Galician', 'gl',
    'Gaelic (Scottish)', 'gd',
    'Gaelic (Manx)', 'gv',
    'Georgian', 'ka',
    'German', 'de',
    'Greek', 'el',
    'Greenlandic, Kalaallisut', 'kl',
    'Guarani', 'gn',
    'Gujarati', 'gu',
    'Haitian Creole', 'ht',
    'Hausa', 'ha',
    'Hebrew', 'he',
    'Herero', 'hz',
    'Hindi', 'hi',
    'Hiri Motu', 'ho',
    'Hungarian', 'hu',
    'Icelandic', 'is',
    'Ido', 'io',
    'Igbo', 'ig',
    'Indonesian', 'id',
    'Interlingua', 'ia',
    'Interlingue', 'ie',
    'Inuktitut', 'iu',
    'Inupiak', 'ik',
    'Irish', 'ga',
    'Italian', 'it',
    'Japanese', 'ja',
    'Javanese', 'jv',
    'Kannada', 'kn',
    'Kanuri', 'kr',
    'Kashmiri', 'ks',
    'Kazakh', 'kk',
    'Khmer', 'km',
    'Kikuyu', 'ki',
    'Kinyarwanda (Rwanda)', 'rw',
    'Kirundi', 'rn',
    'Klingon', 'tlh',       # Actually ISO 639-2
    'Kyrgyz', 'ky',
    'Komi', 'kv',
    'Kongo', 'kg',
    _('Korean'), 'ko',
    'Kurdish', 'ku',
    'Kwanyama', 'kj',
    'Lao', 'lo',
    'Latin', 'la',
    'Latvian (Lettish)', 'lv',
    'Limburgish ( Limburger)', 'li',
    'Lingala', 'ln',
    'Lithuanian', 'lt',
    'Luga-Katanga', 'lu',
    'Luganda, Ganda', 'lg',
    'Luxembourgish', 'lb',
    'Macedonian', 'mk',
    'Malagasy', 'mg',
    'Malay', 'ms',
    'Malayalam', 'ml',
    'Maltese', 'mt',
    'Maori', 'mi',
    'Marathi', 'mr',
    'Marshallese', 'mh',
    'Moldavian', 'mo',
    'Mongolian', 'mn',
    'Nauru', 'na',
    'Navajo', 'nv',
    'Ndonga', 'ng',
    'Northern Ndebele', 'nd',
    'Nepali', 'ne',
    'Norwegian', 'no',
    'Norwegian bokmål', 'nb',
    'Norwegian nynorsk', 'nn',
    'Occitan', 'oc',
    'Ojibwe', 'oj',
    'Old Church Slavonic, Old Bulgarian', 'cu',
    'Oriya', 'or',
    'Oromo (Afaan Oromo)', 'om',
    'Ossetian', 'os',
    'Pāli', 'pi',
    'Pashto, Pushto', 'ps',
    'Persian (Farsi)', 'fa',
    'Polish', 'pl',
    'Portuguese', 'pt',
    'Punjabi (Eastern)', 'pa',
    'Quechua', 'qu',
    'Romansh', 'rm',
    'Romanian', 'ro',
    _('Russian'), 'ru',
    'Sami', 'se',
    'Samoan', 'sm',
    'Sango', 'sg',
    'Sanskrit', 'sa',
    'Serbian', 'sr',
    'Serbo-Croatian', 'sh',
    'Sesotho', 'st',
    'Setswana', 'tn',
    'Shona', 'sn',
    'Sichuan Yi, Nuoso', 'ii',
    'Sindhi', 'sd',
    'Sinhalese', 'si',
    'Swati, Siswati', 'ss',
    'Slovak', 'sk',
    'Slovenian', 'sl',
    'Somali', 'so',
    'Southern Ndebele', 'nr',
    _('Spanish'), 'es',
    'Sundanese', 'su',
    'Swahili (Kiswahili)', 'sw',
    'Swedish', 'sv',
    'Tagalog', 'tl',
    'Tahitian', 'ty',
    'Tajik', 'tg',
    'Tamil', 'ta',
    'Tatar', 'tt',
    'Telugu', 'te',
    'Thai', 'th',
    'Tibetan', 'bo',
    'Tigrinya', 'ti',
    'Tonga', 'to',
    'Tsonga', 'ts',
    _('Turkish'), 'tr',
    'Turkmen', 'tk',
    'Twi', 'tw',
    'Uyghur', 'ug',
    'Ukrainian', 'uk',
    'Urdu', 'ur',
    'Uzbek', 'uz',
    'Venda', 've',
    _('Vietnamese'), 'vi',
    'Volapük', 'vo',
    'Wallon', 'wa',
    'Welsh', 'cy',
    'Wolof', 'wo',
    'Western Frisian', 'fy',
    'Xhosa', 'xh',
    'Yiddish', 'yi',
    'Yoruba', 'yo',
    'Zhuang, Chuang', 'za',
    'Zulu', 'zu',
]

LANGUAGE_CODE_LIST = []
LANGUAGE_CODE_DICT = {}

while language_setup_list:
    key = language_setup_list.pop(0)
    value = language_setup_list.pop(0)

    LANGUAGE_CODE_LIST.append(key)
    LANGUAGE_CODE_DICT[key] = value

# 'Enhanced' websites. As of v2.3.597, this data is only used to extract RSS
#   feeds, but that functionality could be extended in the future
# The 'convert' templates work like this: any four-character sequence beginning
#   and ending with a space character is replaced:
#       ' vi ' - replaced with video ID
#       ' vn ' - replaced with video name
#       ' ci ' - replaced with channel ID
#       ' cn ' - replaced with channel name
#       ' pi ' - replaced with playlist ID
#       ' pn ' - replaced with playlist name
# The IDs and/or names are those extracted from a full video/channel/playlist
#   URL (or provided by a video's metadata file)
# In each mini-dictionary, the keys 'name', 'pretty_name' must be set. The
#   'detect_list' item must not be empty; all other values can be empty lists,
#   if not applicable
enhanced_setup_list = [
    {
        # Key in the dictionary below
        'name': 'youtube',
        # Name displayed in the Video Catalogue
        'pretty_name': 'YouTube',
        # Regexes to recognise the website (no groups used)
        'detect_list': [
            '^https?:\/\/(www\.)?youtube\.com\/',
        ],
        # Regexes to extract a video ID/name. The second group is used (so that
        #   the optional www can be the first group)
        'extract_vid_list': [
            '^https?:\/\/(www\.)?youtube\.com\/watch\?v=([^\/]+)',
        ],
        'extract_vname_list': [],
        # Regexes to extract a channel/playlist ID/name. The second group is
        #   used
        'extract_cid_list': [
            '^https?:\/\/(www\.)?youtube\.com\/channel\/([^\/]+)',
        ],
        'extract_cname_list': [
            '^https?:\/\/(www\.)?youtube\.com\/user\/([^\/]+)\/videos\/?',
            '^https?:\/\/(www\.)?youtube\.com\/c\/([^\/]+)\/videos\/?',
        ],
        # Regexes to extract a playlist ID/name. The second group is used
        'extract_pid_list': [
            '^https?:\/\/(www\.)?youtube\.com\/channel\?list=([^\/]+)',
            '^https?:\/\/(www\.)?youtube\.com\/playlist\?list=([^\/]+)',
        ],
        'extract_pname_list': [],
        # Templates to convert video ID/name to URL
        'convert_video_list': [
            'https://www.youtube.com/watch?v= vi ',
        ],
        # Templates to convert channel ID/name to URL
        'convert_channel_list': [
            'https://www.youtube.com/c/ cn /videos',
            'https://www.youtube.com/user/ cn /videos',
            'https://www.youtube.com/channel/ ci ',
        ],
        # Templates to convert playlist ID/name to URL
        'convert_playlist_list': [
#           'https://www.youtube.com/channel?list= pi ',
            'https://www.youtube.com/playlist?list= pi ',
        ],
        # Templates to convert channel ID/name to RSS feed
        'rss_channel_list': [
            'https://www.youtube.com/feeds/videos.xml?channel_id= ci ',
        ],
        # Templates to convert playlist ID/name to RSS feed
        'rss_playlist_list': [
            'https://www.youtube.com/feeds/videos.xml?playlist_id= pi ',
        ],
    },
    {
        'name': 'odysee',
        'pretty_name': 'Odysee',
        'detect_list': [
            '^https?:\/\/(www\.)?odysee\.com\/',
        ],
        'extract_vid_list': [],
        'extract_vname_list': [
            '^https?:\/\/(www\.)?odysee\.com\/\@[^\/]+\/([^\:]+)\:',
        ],
        'extract_cid_list': [],
        'extract_cname_list': [
            '^https?:\/\/(www\.)?odysee\.com\/\@([^\:]+)\:',
        ],
        'extract_pid_list': [],
        'extract_pname_list': [],
        'convert_video_list': [],
        'convert_channel_list': [],
        'convert_playlist_list': [],
        'rss_channel_list': [
            'https://lbryfeed.melroy.org/channel/odysee/ cn ',
        ],
        'rss_playlist_list': [],
    },
    {
        'name': 'bitchute',
        'pretty_name': 'BitChute',
        'detect_list': [
            '^https?:\/\/(www\.)?bitchute\.com\/',
        ],
        'extract_vid_list': [
            '^https?:\/\/(www\.)?bitchute\.com\/video\/([^\/]+)',
        ],
        'extract_vname_list': [],
        'extract_cid_list': [
            '^https?:\/\/(www\.)?bitchute\.com\/channel\/([^\/]+)',
        ],
        'extract_cname_list': [],
        'extract_pid_list': [],
        'extract_pname_list': [],
        'convert_video_list': [
            'https://www.bitchute.com/video/ vi ',
        ],
        'convert_channel_list': [
            'https://www.bitchute.com/video/ ci ',
        ],
        'convert_playlist_list': [],
        'rss_channel_list': [
            'https://www.bitchute.com/feeds/rss/channel/ cn ',
        ],
        'rss_playlist_list': [],
    },
    {
        'name': 'twitch',
        'pretty_name': 'Twitch',
        'detect_list': [
            '^https?:\/\/(www\.)?twitch\.tv\/',
        ],
        'extract_vid_list': [
            '^https?:\/\/(www\.)?twitch\.tv\/videos\/([^\/]+)',
        ],
        'extract_vname_list': [],
        'extract_cid_list': [],
        'extract_cname_list': [
            '^https?:\/\/(www\.)?twitch\.tv\/([^\/]+)',
        ],
        'extract_pid_list': [],
        'extract_pname_list': [],
        'convert_video_list': [
            'https://www.twitch.tv/video/ vi ',
        ],
        'convert_channel_list': [
            'https://www.twitch.tv/ cn ',
        ],
        'convert_playlist_list': [],
        'rss_channel_list': [
            'https://twitchrss.appspot.com/vod/ cn ',
        ],
        'rss_playlist_list': [],
    },
]

ENHANCED_SITE_LIST = []
ENHANCED_SITE_DICT = {}

for mini_dict in enhanced_setup_list:
    ENHANCED_SITE_LIST.append(mini_dict['name'])
    ENHANCED_SITE_DICT[mini_dict['name']] = mini_dict

# Standard list and dictionaries
time_metric_setup_list = [
    'seconds', _('seconds'), 1,
    'minutes', _('minutes'), 60,
    'hours', _('hours'), int(60 * 60),
    'days', _('days'), int(60 * 60 * 24),
    'weeks', _('weeks'), int(60 * 60 * 24 * 7),
    'years', _('years'), int(60 * 60 * 24 * 365),
]

TIME_METRIC_LIST = []
TIME_METRIC_DICT = {}
TIME_METRIC_TRANS_DICT = {}

while time_metric_setup_list:
    key = time_metric_setup_list.pop(0)
    trans_key = time_metric_setup_list.pop(0)
    value = time_metric_setup_list.pop(0)

    TIME_METRIC_LIST.append(key)
    TIME_METRIC_DICT[key] = value
    TIME_METRIC_TRANS_DICT[key] = trans_key

specified_days_setup_list = [
    'every_day', _('Every day'),
    'weekdays', _('Weekdays'),
    'weekends', _('Weekends'),
    'monday', _('Monday'),
    'tuesday', _('Tuesday'),
    'wednesday', _('Wednesday'),
    'thursday', _('Thursday'),
    'friday', _('Friday'),
    'saturday', _('Saturday'),
    'sunday', _('Sunday'),
]

SPECIFIED_DAYS_LIST = []
SPECIFIED_DAYS_DICT = {}

while specified_days_setup_list:
    key = specified_days_setup_list.pop(0)
    value = specified_days_setup_list.pop(0)

    SPECIFIED_DAYS_LIST.append(key)
    SPECIFIED_DAYS_DICT[key] = value

KILO_SIZE = 1024.0
filesize_metric_setup_list = [
    'B',    1,
    'KiB',  int(KILO_SIZE ** 1),
    'MiB',  int(KILO_SIZE ** 2),
    'GiB',  int(KILO_SIZE ** 3),
    'TiB',  int(KILO_SIZE ** 4),
    'PiB',  int(KILO_SIZE ** 5),
    'EiB',  int(KILO_SIZE ** 6),
    'ZiB',  int(KILO_SIZE ** 7),
    'YiB',  int(KILO_SIZE ** 8),
]

FILESIZE_METRIC_LIST = []
FILESIZE_METRIC_DICT = {}

while filesize_metric_setup_list:
    key = filesize_metric_setup_list.pop(0)
    value = filesize_metric_setup_list.pop(0)

    FILESIZE_METRIC_LIST.append(key)
    FILESIZE_METRIC_DICT[key] = value

file_output_setup_list = [
    0, 'Custom',
        None,                           # (The same as option 2 by default)
    1, 'ID',
        '%(id)s.%(ext)s',
    2, 'Title',
        '%(title)s.%(ext)s',
    3, 'Title + ID',
        '%(title)s-%(id)s.%(ext)s',
    4, 'Title + Quality',
        '%(title)s-%(height)sp.%(ext)s',
    5, 'Title + ID + Quality',
        '%(title)s-%(id)s-%(height)sp.%(ext)s',
    6, 'Autonumber + Title',
        '%(playlist_index)s-%(title)s.%(ext)s',
    7, 'Autonumber + Title + ID',
        '%(playlist_index)s-%(title)s-%(id)s.%(ext)s',
    8, 'Autonumber + Title + Quality',
        '%(playlist_index)s-%(title)s-%(height)sp.%(ext)s',
    9, 'Autonumber + Title + ID + Quality',
        '%(playlist_index)s-%(title)s-%(id)s-%(height)sp.%(ext)s',
]

FILE_OUTPUT_NAME_DICT = {}
FILE_OUTPUT_CONVERT_DICT = {}

while file_output_setup_list:
    key = file_output_setup_list.pop(0)
    value = file_output_setup_list.pop(0)
    value2 = file_output_setup_list.pop(0)

    FILE_OUTPUT_NAME_DICT[key] = value
    FILE_OUTPUT_CONVERT_DICT[key] = value2

YTDLP_OUTPUT_TYPE_LIST = [
    'subtitle',
    'thumbnail',
    'description',
    'annotation',
    'infojson',
    'pl_thumbnail',
    'pl_description',
    'pl_infojson',
    'chapter',
]

SPONSORBLOCK_CATEGORY_LIST = [
    'sponsor',
    'selfpromo',
    'interaction',
    'intro',
    'outro',
    'preview',
    'music_offtopic',
]
SPONSORBLOCK_ACTION_LIST = [
    'skip',
]

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
    '144p',     'Any format [144p]',                        False,
    '240p',     'Any format [240p]',                        False,
    '360p',     'Any format [360p]',                        False,
    '480p',     'Any format [480p]',                        False,
    '720p',     'Any format [720p]',                        False,
    '720p60',   'Any format [720p 60fps]',                  False,
    '1080p',    'Any format [1080p]',                       False,
    '1080p60',  'Any format [1080p 60fps]',                 False,
    '1440p',    'Any format [1440p]',                       False,
    '1440p60',  'Any format [1440p 60fps]',                 False,
    '2160p',    'Any format [2160p]',                       False,
    '2160p60',  'Any format [2160p 60fps]',                 False,
    '4320p',    'Any format [4320p]',                       False,
    '4320p60',  'Any format [4320p 60fps]',                 False,
    # Dummy extractor codes - other
    '3gp',      '3gp',                                      False,
    'flv',      'flv',                                      False,
    'm4a',      'm4a',                                      True,
    'mp4',      'mp4',                                      False,
    'webm',     'webm',                                     False,
    # Real extractor codes
    '17',       '3gp [144p] <17>',                          False,
    '36',       '3gp [240p] <36>',                          False,
    '5',        'flv [240p] <5>',                           False,
    '6',        'flv [270p] <6>',                           False,
    '34',       'flv [360p] <34>',                          False,
    '35',       'flv [480p] <35>',                          False,
    # v1.3.037 - not sure whether the HLS format codes should be added here, or
    #   not. 'hls' has not been added as a dummy extractor code because
    #   youtube-dl doesn't support that
    '151',      'hls [72p] <151>',                          False,
    '132',      'hls [240p] <132>',                         False,
    '92',       'hls [240p] (3D) <92>',                     False,
    '93',       'hls [360p] (3D) <93>',                     False,
    '94',       'hls [480p] (3D) <94>',                     False,
    '95',       'hls [720p] (3D) <95>',                     False,
    '96',       'hls [1080p] <96>',                         False,
    '139',      'm4a 48k (DASH Audio) <139>',               True,
    '140',      'm4a 128k (DASH Audio) <140>',              True,
    '256',      'm4a 192k (DASH Audio) <256>',              True,
    '141',      'm4a 256k (DASH Audio) <141>',              True,
    '258',      'm4a 384k (DASH Audio) <258>',              True,
    '18',       'mp4 [360p] <18>',                          False,
    '22',       'mp4 [720p] <22>',                          False,
    '37',       'mp4 [1080p] <37>',                         False,
    '38',       'mp4 [4K] <38>',                            False,
    '160',      'mp4 [144p] (DASH Video) <160>',            False,
    '133',      'mp4 [240p] (DASH Video) <133>',            False,
    '134',      'mp4 [360p] (DASH Video) <134>',            False,
    '135',      'mp4 [480p] (DASH Video) <135>',            False,
    '136',      'mp4 [720p] (DASH Video) <136>',            False,
    '298',      'mp4 [720p 60fps] (DASH Video) <298>',      False,
    '137',      'mp4 [1080p] (DASH Video) <137>',           False,
    '299',      'mp4 [1080p 60fps] (DASH Video) <299>',     False,
    '264',      'mp4 [1440p] (DASH Video) <264>',           False,
    '138',      'mp4 [2160p] (DASH Video) <138>',           False,
    '266',      'mp4 [2160p 60fps] (DASH Video) <266>',     False,
    '82',       'mp4 [360p] (3D) <82>',                     False,
    '83',       'mp4 [480p] (3D) <83>',                     False,
    '84',       'mp4 [720p] (3D) <84>',                     False,
    '85',       'mp4 [1080p] (3D) <85>',                    False,
    '394',      'mp4 [144p] <394>',                         False,
    '395',      'mp4 [240p] <395>',                         False,
    '396',      'mp4 [360p] <396>',                         False,
    '397',      'mp4 [480p] <397>',                         False,
    '398',      'mp4 [720p] <398>',                         False,
    '399',      'mp4 [1080p] <399>',                        False,
    '400',      'mp4 [1440p] <400>',                        False,
    '401',      'mp4 [2160p] <401>',                        False,
    '402',      'mp4 [2880p] <402>',                        False,
    '571',      'mp4 [8k] <571>',                           False,
    '43',       'webm [360p] <43>',                         False,
    '44',       'webm [480p] <44>',                         False,
    '45',       'webm [720p] <45>',                         False,
    '46',       'webm [1080p] <46>',                        False,
    '242',      'webm [240p] (DASH Video) <242>',           False,
    '243',      'webm [360p] (DASH Video) <243>',           False,
    '244',      'webm [480p] (DASH Video) <244>',           False,
    '247',      'webm [720p] (DASH Video) <247>',           False,
    '302',      'webm [720p 60fps] (DASH Video) <302>',     False,
    '248',      'webm [1080p] (DASH Video) <248>',          False,
    '303',      'webm [1080p 60fps] (DASH Video) <303>',    False,
    '271',      'webm [1440p] (DASH Video) <271>',          False,
    '308',      'webm [1440p 60fps] (DASH Video) <300>',    False,
    '313',      'webm [2160p] (DASH Video) <313>',          False,
    '315',      'webm [2160p 60fps] (DASH Video) <315>',    False,
    '272',      'webm [4320p] (DASH Video) <272>',          False,
    '100',      'webm [360p] (3D) <100>',                   False,
    '101',      'webm [480p] (3D) <101>',                   False,
    '102',      'webm [720p] (3D) <102>',                   False,
    '330',      'webm [144p 60fps] (HDR) <330>',            False,
    '331',      'webm [240p 60fps] (HDR) <331>',            False,
    '332',      'webm [360p 60fps] (HDR) <332>',            False,
    '333',      'webm [480p 60fps] (HDR) <333>',            False,
    '334',      'webm [720p 60fps] (HDR) <334>',            False,
    '335',      'webm [1080p 60fps] (HDR) <335>',           False,
    '336',      'webm [1440p 60fps] (HDR) <336>',           False,
    '337',      'webm [2160p 60fps] (HDR) <337>',           False,
    '600',      'webm (36k Audio) <600>',                   True,
    '249',      'webm (52k Audio) <249>',                   True,
    '250',      'webm (64k Audio) <250>',                   True,
    '251',      'webm (116k Audio) <251>',                  True,
    '219',      'webm [144p] <219>',                        False,
    '278',      'webm [144p] <278>',                        False,
    '167',      'webm [360p] <167>',                        False,
    '168',      'webm [480p] <168>',                        False,
    '218',      'webm [480p] <218>',                        False,
    '245',      'webm [480p] <245>',                        False,
    '246',      'webm [480p] <246>',                        False,
    '169',      'webm [1080p] <169>',                       False,
    '171',      'webm 48k (DASH Audio) <171>',              True,
    '172',      'webm 256k (DASH Audio) <172>',             True,
]

VIDEO_OPTION_LIST = []
VIDEO_OPTION_DICT = {}
VIDEO_OPTION_TYPE_DICT = {}

while video_option_setup_list:
    value = video_option_setup_list.pop(0)
    key = video_option_setup_list.pop(0)
    audio_only_flag = video_option_setup_list.pop(0)

    VIDEO_OPTION_LIST.append(key)
    VIDEO_OPTION_DICT[key] = value
    VIDEO_OPTION_TYPE_DICT[value] = audio_only_flag

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
    #   30fps from 60fps formats
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

# (Used for detecting video thumbnails. Unfortunately Gtk can't display .webp
#   files yet)
IMAGE_FORMAT_LIST = ['.jpg', '.png', '.gif']
# (The same list including .webp, for any code that needs it)
IMAGE_FORMAT_EXT_LIST = ['.jpg', '.png', '.gif', '.webp']

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

DIALOGUE_ICON_DICT = {
    'newbie_classic_icon': 'newbie_classic_icon.png',
    'newbie_icon': 'newbie_icon_64.png',
    'ready_icon': 'ready_icon_64.png',
    'setup_classic_icon': 'setup_classic_icon.png',
    'system_icon': 'system_icon_64.png',
    'yt_icon': 'yt_icon_32.png',
    'yt_remind_icon_en': 'yt_remind_icon_en.png',
    'yt_remind_icon_es': 'yt_remind_icon_es.png',
    'yt_remind_icon_fr': 'yt_remind_icon_fr.png',
    'yt_remind_icon_kr': 'yt_remind_icon_kr.png',
    'yt_remind_icon_nl': 'yt_remind_icon_nl.png',
    'yt_remind_icon_ru': 'yt_remind_icon_ru.png',
    'yt_remind_icon_vi': 'yt_remind_icon_vi.png',
}
if xmas_flag:
    DIALOGUE_ICON_DICT['system_icon'] = 'system_icon_xmas_64.png'
elif eesti_flag:
    DIALOGUE_ICON_DICT['system_icon'] = 'system_icon_eesti_64.png'
elif anglo_flag:
    DIALOGUE_ICON_DICT['system_icon'] = 'system_icon_anglo_64.png'

if xmas_flag:
    STATUS_ICON_DICT = {
        'default_icon': 'status_default_icon_xmas_64.png',
        'check_icon': 'status_check_icon_xmas_64.png',
        'check_live_icon': 'status_check_live_icon_xmas_64.png',
        'download_icon': 'status_download_icon_xmas_64.png',
        'download_live_icon': 'status_download_live_icon_xmas_64.png',
        'update_icon': 'status_update_icon_xmas_64.png',
        'refresh_icon': 'status_refresh_icon_xmas_64.png',
        'info_icon': 'status_info_icon_xmas_64.png',
        'tidy_icon': 'status_tidy_icon_xmas_64.png',
        'livestream_icon': 'status_livestream_icon_xmas_64.png',
        'process_icon': 'status_process_icon_xmas_64.png',
    }
elif eesti_flag:
    STATUS_ICON_DICT = {
        'default_icon': 'status_default_icon_eesti_64.png',
        'check_icon': 'status_check_icon_eesti_64.png',
        'check_live_icon': 'status_check_live_icon_eesti_64.png',
        'download_icon': 'status_download_icon_eesti_64.png',
        'download_live_icon': 'status_download_live_icon_eesti_64.png',
        'update_icon': 'status_update_icon_eesti_64.png',
        'refresh_icon': 'status_refresh_icon_eesti_64.png',
        'info_icon': 'status_info_icon_eesti_64.png',
        'tidy_icon': 'status_tidy_icon_eesti_64.png',
        'livestream_icon': 'status_livestream_icon_eesti_64.png',
        'process_icon': 'status_process_icon_eesti_64.png',
    }
elif anglo_flag:
    STATUS_ICON_DICT = {
        'default_icon': 'status_default_icon_anglo_64.png',
        'check_icon': 'status_check_icon_anglo_64.png',
        'check_live_icon': 'status_check_live_icon_anglo_64.png',
        'download_icon': 'status_download_icon_anglo_64.png',
        'download_live_icon': 'status_download_live_icon_anglo_64.png',
        'update_icon': 'status_update_icon_anglo_64.png',
        'refresh_icon': 'status_refresh_icon_anglo_64.png',
        'info_icon': 'status_info_icon_anglo_64.png',
        'tidy_icon': 'status_tidy_icon_anglo_64.png',
        'livestream_icon': 'status_livestream_icon_anglo_64.png',
        'process_icon': 'status_process_icon_anglo_64.png',
    }
else:
    STATUS_ICON_DICT = {
        'default_icon': 'status_default_icon_64.png',
        'check_icon': 'status_check_icon_64.png',
        'check_live_icon': 'status_check_live_icon_64.png',
        'download_icon': 'status_download_icon_64.png',
        'download_live_icon': 'status_download_live_icon_64.png',
        'update_icon': 'status_update_icon_64.png',
        'refresh_icon': 'status_refresh_icon_64.png',
        'info_icon': 'status_info_icon_64.png',
        'tidy_icon': 'status_tidy_icon_64.png',
        'livestream_icon': 'status_livestream_icon_64.png',
        'process_icon': 'status_process_icon_64.png',
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
    'tool_hide_large': 'hide_large.png',
    'tool_hide_small': 'hide_small.png',
    'tool_options_large': 'options_large.png',
    'tool_options_small': 'options_small.png',
    'tool_playlist_large': 'playlist_large.png',
    'tool_playlist_small': 'playlist_small.png',
    'tool_preferences_large': 'preferences_large.png',
    'tool_preferences_small': 'preferences_small.png',
    'tool_quit_large': 'quit_large.png',
    'tool_quit_small': 'quit_small.png',
    'tool_stop_large': 'stop_large.png',
    'tool_stop_small': 'stop_small.png',
    'tool_switch_large': 'switch_large.png',
    'tool_switch_small': 'switch_small.png',
    'tool_video_large': 'video_large.png',
    'tool_video_small': 'video_small.png',
}

LARGE_ICON_DICT = {
    'attention_large': 'attention.png',
    'channel_large': 'channel.png',
    'copy_large': 'copy.png',
    'cursor_large': 'cursor.png',
    'error_large': 'error.png',
    'folder_large': 'folder_yellow.png',
    'folder_fixed_large': 'folder_green.png',
    'folder_no_parent_large': 'folder_black.png',
    'folder_private_large': 'folder_red.png',
    'folder_temp_large': 'folder_blue.png',
    'hand_left_large': 'hand_left.png',
    'hand_right_large': 'hand_right.png',
    'learn_left_large': 'learn_left.png',
    'learn_right_large': 'learn_right.png',
    'limits_off_large': 'limits_off.png',
    'limits_on_large': 'limits_on.png',
    'playlist_large': 'playlist.png',
    'question_large': 'question.png',
    'video_large': 'video.png',
    'warning_large': 'warning.png',
}

LARGE_ICON_COMPOSITE_LIST = [
    'channel_large',
    'folder_large',
    'folder_fixed_large',
    'folder_no_parent_large',
    'folder_private_large',
    'folder_temp_large',
    'playlist_large',
    'video_large',
]

SMALL_ICON_DICT = {
    'video_small': 'video.png',
    'channel_small': 'channel.png',
    'playlist_small': 'playlist.png',
    'folder_small': 'folder.png',

    'archived_small': 'archived.png',
    'arrow_up_small': 'arrow_up.png',
    'arrow_down_small': 'arrow_down.png',
    'attention_small': 'attention.png',
    'check_small': 'check.png',
    'comment_small': 'comment.png',
    'debut_now_small': 'debut_now.png',
    'debut_wait_small': 'debut_wait.png',
    'delete_small': 'delete.png',
    'dl_options_small': 'dl_options.png',
    'download_small': 'download.png',
    'error_small': 'error.png',
    'external_small': 'external.png',
    'favourite_small': 'favourite.png',
    'folder_black_small': 'folder_black.png',
    'folder_blue_small': 'folder_blue.png',
    'folder_green_small': 'folder_green.png',
    'folder_red_small': 'folder_red.png',
    'keyboard_small': 'keyboard.png',
    'likes_small': 'likes.png',
    'have_file_small': 'have_file.png',
    'live_now_small': 'live_now.png',
    'live_old_small': 'live_old.png',
    'live_old_no_file_small': 'live_old_no_file.png',
    'live_wait_small': 'live_wait.png',
    'no_file_small': 'no_file.png',
    'slice_small': 'slice.png',
    'split_file_small': 'split_file.png',
    'stamp_small': 'stamp.png',
    'subs_small': 'subs.png',
    'system_error_small': 'system_error.png',
    'system_warning_small': 'system_warning.png',
    'unavailable_small': 'unavailable.png',
    'uploader_small': 'uploader.png',
    'warning_small': 'warning.png',
}

THUMB_ICON_DICT = {
    'thumb_none_tiny': 'thumb_none_tiny.png',
    'thumb_none_small': 'thumb_none_small.png',
    'thumb_none_medium': 'thumb_none_medium.png',
    'thumb_none_large': 'thumb_none_large.png',
    'thumb_none_enormous': 'thumb_none_enormous.png',

    'thumb_left_tiny': 'thumb_left_tiny.png',
    'thumb_left_small': 'thumb_left_small.png',
    'thumb_left_medium': 'thumb_left_medium.png',
    'thumb_left_large': 'thumb_left_large.png',
    'thumb_left_enormous': 'thumb_left_enormous.png',

    'thumb_right_tiny': 'thumb_right_tiny.png',
    'thumb_right_small': 'thumb_right_small.png',
    'thumb_right_medium': 'thumb_right_medium.png',
    'thumb_right_large': 'thumb_right_large.png',
    'thumb_right_enormous': 'thumb_right_enormous.png',

    'thumb_both_tiny': 'thumb_both_tiny.png',
    'thumb_both_small': 'thumb_both_small.png',
    'thumb_both_medium': 'thumb_both_medium.png',
    'thumb_both_large': 'thumb_both_large.png',
    'thumb_both_enormous': 'thumb_both_enormous.png',

    'thumb_default_tiny': 'thumb_default_tiny.png',
    'thumb_default_small': 'thumb_default_small.png',
    'thumb_default_medium': 'thumb_default_medium.png',
    'thumb_default_large': 'thumb_default_large.png',
    'thumb_default_enormous': 'thumb_default_enormous.png',

    'thumb_block_tiny': 'thumb_block_tiny.png',
    'thumb_block_small': 'thumb_block_small.png',
    'thumb_block_medium': 'thumb_block_medium.png',
    'thumb_block_large': 'thumb_block_large.png',
    'thumb_block_enormous': 'thumb_block_enormous.png',
}

EXTERNAL_ICON_DICT = {
    'ytdl_gui': 'youtube-dl-gui.png',
}

# (Replaces system stock icons, if not available)
STOCK_ICON_DICT = {
    'stock_add': 'add_small.png',
    'stock_cancel': 'cancel_small.png',
    'stock_delete': 'delete_small.png',
    'stock_execute': 'ffmpeg_small.png',
    'stock_file': 'file_small.png',
    'stock_find': 'find_small.png',
    'stock_go_back': 'go_back_small.png',
    'stock_go_down': 'go_down_small.png',
    'stock_go_forward': 'go_forward_small.png',
    'stock_go_up': 'go_up_small.png',
    'stock_goto_first': 'goto_first_small.png',
    'stock_goto_last': 'goto_last_small.png',
    'stock_hide_filter': 'hide_filter_small.png',
    'stock_index': 'index_small.png',
    'stock_media_play': 'media_play_small.png',
    'stock_media_stop': 'media_stop_small.png',
    'stock_open': 'open_small.png',
    'stock_properties': 'properties.png',
    'stock_properties_large': 'properties_large.png',
    'stock_redo': 'resort_small.png',           # Used for a sorting button
    'stock_refresh': 'refresh_small.png',
    'stock_show_filter': 'show_filter_small.png',
    'stock_sort_ascending': 'sort_ascending_small.png',
    'stock_sort_descending': 'sort_descending_small.png',
}

if xmas_flag:
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
elif eesti_flag:
    WIN_ICON_LIST = [
        'system_icon_eesti_16.png',
        'system_icon_eesti_24.png',
        'system_icon_eesti_32.png',
        'system_icon_eesti_48.png',
        'system_icon_eesti_64.png',
        'system_icon_eesti_128.png',
        'system_icon_eesti_256.png',
        'system_icon_eesti_512.png',
    ]
elif anglo_flag:
    WIN_ICON_LIST = [
        'system_icon_anglo_16.png',
        'system_icon_anglo_24.png',
        'system_icon_anglo_32.png',
        'system_icon_anglo_48.png',
        'system_icon_anglo_64.png',
        'system_icon_anglo_128.png',
        'system_icon_anglo_256.png',
        'system_icon_anglo_512.png',
    ]
else:
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

CONFIG_WIN_ICON_LIST = [
    'config_icon_16.png',
    'config_icon_24.png',
    'config_icon_32.png',
    'config_icon_48.png',
    'config_icon_64.png',
    'config_icon_128.png',
    'config_icon_256.png',
    'config_icon_512.png',
]

def do_translate(config_flag=False):

    """Function called for the first time below, setting various values.

    If mainapp.TartubeApp.load_config() changes the locale to something else,
    called for a second time to update those values.

    Args:

        config_flag (bool): False for the initial call, True for the second
            call from mainapp.TartubeApp.load_config()

    """

    global FOLDER_ALL_VIDEOS, FOLDER_BOOKMARKS, FOLDER_FAVOURITE_VIDEOS, \
    FOLDER_LIVESTREAMS, FOLDER_MISSING_VIDEOS, FOLDER_NEW_VIDEOS, \
    FOLDER_RECENT_VIDEOS, FOLDER_WAITING_VIDEOS, FOLDER_TEMPORARY_VIDEOS, \
    FOLDER_UNSORTED_VIDEOS, FOLDER_VIDEO_CLIPS

    global YTDL_UPDATE_DICT

    global MAIN_STAGE_QUEUED, MAIN_STAGE_NOT_STARTED, MAIN_STAGE_ACTIVE, \
    MAIN_STAGE_PAUSED, MAIN_STAGE_COMPLETED, MAIN_STAGE_ERROR, \
    MAIN_STAGE_STALLED, ACTIVE_STAGE_PRE_PROCESS, ACTIVE_STAGE_DOWNLOAD, \
    ACTIVE_STAGE_CONCATENATE, ACTIVE_STAGE_POST_PROCESS, \
    ACTIVE_STAGE_CAPTURE, ACTIVE_STAGE_MERGE, ACTIVE_STAGE_CHECKING, \
    COMPLETED_STAGE_FINISHED, COMPLETED_STAGE_WARNING, \
    COMPLETED_STAGE_ALREADY, ERROR_STAGE_ERROR, ERROR_STAGE_STOPPED, \
    ERROR_STAGE_ABORT

    global TIME_METRIC_TRANS_DICT

    global FILE_OUTPUT_NAME_DICT, FILE_OUTPUT_CONVERT_DICT

    global VIDEO_OPTION_LIST, VIDEO_OPTION_DICT

    # System folder names
    FOLDER_ALL_VIDEOS = _('All Videos')
    FOLDER_BOOKMARKS = _('Bookmarks')
    FOLDER_FAVOURITE_VIDEOS = _('Favourite Videos')
    FOLDER_LIVESTREAMS = _('Livestreams')
    FOLDER_MISSING_VIDEOS = _('Missing Videos')
    FOLDER_NEW_VIDEOS = _('New Videos')
    FOLDER_RECENT_VIDEOS = _('Recent Videos')
    FOLDER_WAITING_VIDEOS = _('Waiting Videos')
    FOLDER_TEMPORARY_VIDEOS = _('Temporary Videos')
    FOLDER_UNSORTED_VIDEOS = _('Unsorted Videos')
    FOLDER_VIDEO_CLIPS = _('Video Clips')

    # youtube-dl update shell commands
    YTDL_UPDATE_DICT = {
        'ytdl_update_default_path':
            _('Update using default youtube-dl path'),
        'ytdl_update_local_path':
            _('Update using local youtube-dl path'),
        'ytdl_update_custom_path':
            _('Update using custom youtube-dl path'),
        'ytdl_update_pip':
            _('Update using pip'),
        'ytdl_update_pip_no_dependencies':
            _('Update using pip (use --no-dependencies option)'),
        'ytdl_update_pip_omit_user':
            _('Update using pip (omit --user option)'),
        'ytdl_update_pip3':
            _('Update using pip3'),
        'ytdl_update_pip3_no_dependencies':
            _('Update using pip3 (use --no-dependencies option)'),
        'ytdl_update_pip3_omit_user':
            _('Update using pip3 (omit --user option)'),
        'ytdl_update_pip3_recommend':
            _('Update using pip3 (recommended)'),
        'ytdl_update_pypi_path':
            _('Update using PyPI youtube-dl path'),
        'ytdl_update_win_32':
            _('Windows 32-bit update (recommended)'),
        'ytdl_update_win_32_no_dependencies':
            _('Windows 32-bit update (use --no-dependencies option)'),
        'ytdl_update_win_64':
            _('Windows 64-bit update (recommended)'),
        'ytdl_update_win_64_no_dependencies':
            _('Windows 64-bit update (use --no-dependencies option)'),
        'ytdl_update_disabled':
            _('youtube-dl updates are disabled'),
    }

    #  Download operation stages
    MAIN_STAGE_QUEUED = _('Queued')
    MAIN_STAGE_NOT_STARTED = _('Not started')
    MAIN_STAGE_ACTIVE = _('Active')
    MAIN_STAGE_PAUSED = _('Paused')                     # (not actually used)
    MAIN_STAGE_COMPLETED = _('Completed')               # (not actually used)
    MAIN_STAGE_ERROR = _('Error')
    MAIN_STAGE_STALLED = _('Stalled')
    # Sub-stages of the 'Active' stage
    ACTIVE_STAGE_PRE_PROCESS = _('Pre-processing')
    ACTIVE_STAGE_DOWNLOAD = _('Downloading')
    ACTIVE_STAGE_CONCATENATE = _('Concatenating')
    ACTIVE_STAGE_POST_PROCESS = _('Post-processing')
    ACTIVE_STAGE_CHECKING = _('Checking')
    # Sub-stages of the 'Completed' stage
    COMPLETED_STAGE_FINISHED = _('Finished')
    COMPLETED_STAGE_WARNING = _('Warning')
    COMPLETED_STAGE_ALREADY = _('Already downloaded')
    # Sub-stages of the 'Error' stage
    ERROR_STAGE_ERROR = _('Error')                      # (not actually used)
    ERROR_STAGE_STOPPED = _('Stopped')
    ERROR_STAGE_ABORT = _('Filesize abort')

    if config_flag:

        for key in TIME_METRIC_TRANS_DICT:
            TIME_METRIC_TRANS_DICT[key] = _(key)

        # File output templates use a combination of English words, each of
        #   which must be translated
        ignore_me = _(
            'TRANSLATOR\'S NOTE: ID refers to a video\'s unique ID on the' \
            + ' website, e.g. on YouTube "CS9OO0S5w2k"',
        )

        new_name_dict = {}
        for key in FILE_OUTPUT_NAME_DICT.keys():

            mod_value \
            = re.sub('Custom', _('Custom'), FILE_OUTPUT_NAME_DICT[key])
            mod_value = re.sub('ID', _('ID'), mod_value)
            mod_value = re.sub('Title', _('Title'), mod_value)
            mod_value = re.sub('Quality', _('Quality'), mod_value)
            mod_value = re.sub('Autonumber', _('Autonumber'), mod_value)

            new_name_dict[key] = mod_value

        FILE_OUTPUT_NAME_DICT = new_name_dict

        # Video/audio formats. A number of them contain 'Any format', which
        #   must be translated
        new_list = []
        new_dict = {}
        for item in VIDEO_OPTION_LIST:

            mod_item = re.sub('Any format', _('Any format'), item)
            new_list.append(mod_item)
            new_dict[mod_item] = VIDEO_OPTION_DICT[item]

        VIDEO_OPTION_LIST = new_list
        VIDEO_OPTION_DICT = new_dict

    # End of this function
    return


# Call the function for the first time
do_translate()
