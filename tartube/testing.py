#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2022 A S Lewis
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


"""Test code."""


# Import Gtk modules
#   ...


# Import other modules
#   ...


# Import our modules
import media


# Functions


def run_test_code(app_obj):

    """Called by mainapp.TartubeApp.on_menu_test_code().

    Executes some arbitrary test code, and returns a result.

    Args:

        app_obj (mainapp.TartubeApp): The main application

    """

    # ... insert code here ...

    # ...

    # ... insert code here ...

    return "Hello world"


def add_test_media(app_obj):

    """Called by mainapp.TartubeApp.on_menu_test().

    Adds a set of media data objects for testing. This function can only be
    called if the debugging flags are set.

    Enables/disables various media objects by changing the 0s and 1s in the
    code below.

    The videos, channels and playlists listed here have been chosen because
    they are short. They have no connection to the Tartube developers.

    Args:

        app_obj (mainapp.TartubeApp): The main application

    """

    # Test videos

    if True:

        if True:
            video = app_obj.add_video(
                app_obj.fixed_misc_folder,
                'https://www.youtube.com/watch?v=668nUCeBHyY',
            )
            video.set_name('Nature Beautiful short video 720p HD')

        if True:
            video2 = app_obj.add_video(
                app_obj.fixed_misc_folder,
                'https://www.youtube.com/watch?v=MJXayNvM3_E',
            )
            video2.set_name('2019 BMW K 1600 B Imperial Blue - Short Video')

        if True:
            video3 = app_obj.add_video(
                app_obj.fixed_misc_folder,
                'https://www.youtube.com/watch?v=jypAVuatE5w',
            )
            video3.set_name('our shortest dumb video')

        if True:
            video4 = app_obj.add_video(
                app_obj.fixed_misc_folder,
                'https://www.youtube.com/watch?v=zhWDdy_5v2w',
            )
            video4.set_name('What Happens In One Minute?')

        if True:
            video5 = app_obj.add_video(
                app_obj.fixed_misc_folder,
                'https://www.youtube.com/watch?v=jNQXAC9IVRw',
            )
            video5.set_name('Me at the zoo')

    # Test channel

    if True and not app_obj.is_container('Test channel'):
        channel = app_obj.add_channel(
            'Test channel',
            None,           # No parent
            'https://www.youtube.com/channel/UCQqM9nXKbGaYFfl0mh6ShRA/' \
            + 'featured',
            None,
        )
        app_obj.main_win_obj.video_index_add_row(channel)

    # Test playlist

    if True and not app_obj.is_container('Test playlist'):
        playlist = app_obj.add_playlist(
            'Test playlist',
            None,           # No parent
            'https://www.youtube.com/watch?v=tPEE9ZwTmy0&list=' \
            + 'PLHJH2BlYG-EEBtw2y1njWpDukJSTs8Qqx',
            None,
        )
        app_obj.main_win_obj.video_index_add_row(playlist)

    # Test folder

    if True:

        if True and not app_obj.is_container('Test folder'):
            folder = app_obj.add_folder(
                'Test folder',
                None,           # No parent
            )
            app_obj.main_win_obj.video_index_add_row(folder)

        if True and not app_obj.is_container('Test folder 2'):
            folder2 = app_obj.add_folder(
                'Test folder 2',
                None,           # No parent
            )
            app_obj.main_win_obj.video_index_add_row(folder2)

        if True and not app_obj.is_container('Test folder 3'):
            folder3 = app_obj.add_folder(
                'Test folder 3',
                folder2,
            )
            app_obj.main_win_obj.video_index_add_row(folder3)

        if True and not app_obj.is_container('Test folder 4'):
            folder4 = app_obj.add_folder(
                'Test folder 4',
                folder2,
            )
            app_obj.main_win_obj.video_index_add_row(folder4)


def setup_screenshots(app_obj):

    """Call this function from testing.run_test_code, when required.

    Sets up four fake channels, with fake videos, in order to take screenshots
    for the README.

    Args:

        app_obj (mainapp.TartubeApp): The main application

    """

    folder = app_obj.add_folder(
        'Comedy',
        None,           # No parent
    )
    app_obj.main_win_obj.video_index_add_row(folder)

    folder2 = app_obj.add_folder(
        'History',
        None,           # No parent
    )
    app_obj.main_win_obj.video_index_add_row(folder2)

    channel_list = [
#        'PewDiePie',
#        'https://www.youtube.com/user/PewDiePie/videos',
#        4472,
#        'Comedy',

#        'Luke TheNotable',
#        'https://www.youtube.com/c/LukeTheNotable/videos',
#        416,
#        'Comedy',

#        'Historia Civilis',
#        'https://www.youtube.com/c/HistoriaCivilis/videos',
#        81,
#        'History',

#        'OverSimplified',
#        'https://www.youtube.com/c/OverSimplified/videos',
#        27,
#        'History',

#        'AlternateHistoryHub',
#        'https://www.youtube.com/c/AlternateHistoryHub/videos',
#        235,
#        'History',

#        'The Armchair Historian',
#        'https://www.youtube.com/c/TheArmchairHistorian/videos',
#        135,
#        'History',

        'Rebecca Black',
        'https://www.youtube.com/user/rebecca/videos',
        239,
        'Comedy',

        'Voxis Productions',
        'https://www.youtube.com/c/VoxisProductions/videos',
        65,
        'Comedy',

        'History Matters',
        'https://www.youtube.com/c/TenMinuteHistory/videos',
        247,
        'History',

        'TimeGhost History',
        'https://www.youtube.com/c/TimeGhost/videos',
        208,
        'History',
    ]

    while channel_list:

        channel_name = channel_list.pop(0)
        channel_url = channel_list.pop(0)
        video_count = channel_list.pop(0)
        folder_name = channel_list.pop(0)
        folder_obj = app_obj.get_first_container(folder_name)

        channel_obj = app_obj.add_channel(
            channel_name,
            folder_obj,
            channel_url,
            None,
        )
        app_obj.main_win_obj.video_index_add_row(channel_obj)

        for i in range(0, video_count):
            video_obj = app_obj.add_video(
                channel_obj,
               'https://www.youtube.com/',  # Fake URL
            )
            video_obj.name = video_obj.nickname = 'Fake video'
            video_obj.upload_time = 1
            video_obj.receive_time = 1

            app_obj.mark_video_downloaded(video_obj, True)


def setup_screenshots2(app_obj):

    """Call this function from testing.run_test_code, when required.

    Makes sure all videos are marked as downloaded.
    """

    for media_data_obj in app_obj.media_reg_dict.values():
        if isinstance(media_data_obj, media.Video) \
        and not media_data_obj.dl_flag:
            app_obj.mark_video_downloaded(media_data_obj, True)

