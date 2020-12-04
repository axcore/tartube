#!/usr/bin/env python3

import re
import os

# Yes, in that order.
import colorama
colorama.init()

import sys

import json
import time
import requests
from datetime import datetime, timedelta

import pathlib

retries = 20
tries = 0
dash_tries = 0

def print_error(message):
#   print(colorama.Fore.RED + f"[ERROR] {message}" + colorama.Style.RESET_ALL)
    print(f"[ERROR] {message}")

def print_warning(message):
#   print(colorama.Fore.YELLOW + f"[WARNING] {message}" + colorama.Style.RESET_ALL)
    print(f"[WARNING] {message}")

def print_info(message):
#   print(colorama.Fore.BLUE + f"[INFO] {message}" + colorama.Style.RESET_ALL)
    print(f"[INFO] {message}")


def parse_cookie_file(cookiefile):
    cookies = {}
    with open (cookiefile, 'r') as fp:
        content = fp.read()
        for line in content.split('\n'):
            if 'youtube' in line:
                elements = line.split('\t')
                cookies[elements[5]] = elements[6]
    return cookies

audio_base_url = ""
video_base_url = ""
video_k = 0
audio_k = 0
video_lmt_distance = 0
audio_lmt_distance = 0
video_lmt_number = 0
audio_lmt_number = 0

quality_video_ranking = [
                    402, 138,       # 4320p: AV1 HFR | VP9 HFR | H.264
                    401, 266,       # 2160p: AV1 HFR | VP9.2 HDR HFR | VP9 HFR | VP9 | H.264
                    400, 264,       # 1440p: AV1 HFR | VP9.2 HDR HFR | VP9 HFR | VP9 | H.264
                    399, 299, 137,  # 1080p: AV1 HFR | VP9.2 HDR HFR | VP9 HFR | VP9 | H.264 HFR | H.264
                    398, 298, 136,  # 720p: AV1 HFR | VP9.2 HDR HFR | VP9 HFR | VP9 | H.264 HFR | H.264
                    397, 135,       # 480p: AV1 | VP9.2 HDR HFR | VP9 | H.264
                    396, 134,       # 360p: AV1 | VP9.2 HDR HFR | VP9 | H.264
                    395, 133,       # 240p: AV1 | VP9.2 HDR HFR | VP9 | H.264
                    394, 160        # 144p: AV1 | VP9.2 HDR HFR | VP9 | H.264
                    ]
quality_audio_ranking = [140]

# Experimental - VP9 support
# quality_video_ranking = [
#                   402, 272, 138,                  # 4320p: AV1 HFR | VP9 HFR | H.264
#                   401, 337, 315, 313, 266,        # 2160p: AV1 HFR | VP9.2 HDR HFR | VP9 HFR | VP9 | H.264
#                   400, 336, 308, 271, 264,        # 1440p: AV1 HFR | VP9.2 HDR HFR | VP9 HFR | VP9 | H.264
#                   399, 335, 303, 248, 299, 137,   # 1080p: AV1 HFR | VP9.2 HDR HFR | VP9 HFR | VP9 | H.264 HFR | H.264
#                   398, 334, 302, 247, 298, 136,   # 720p: AV1 HFR | VP9.2 HDR HFR | VP9 HFR | VP9 | H.264 HFR | H.264
#                   397, 333, 244, 135,             # 480p: AV1 | VP9.2 HDR HFR | VP9 | H.264
#                   396, 332, 243, 134,             # 360p: AV1 | VP9.2 HDR HFR | VP9 | H.264
#                   395, 331, 242, 133,             # 240p: AV1 | VP9.2 HDR HFR | VP9 | H.264
#                   394, 330, 278, 160              # 144p: AV1 | VP9.2 HDR HFR | VP9 | H.264
#                   ]
# quality_audio_ranking = [251,250,249,172,171,141,140,139]


args = sys.argv
segment_number = 0
folder_suffix = ""
output_directory = ""
segment_folder_name = ""
cookie_content = {}

# Argument parsing
for index, element in enumerate(args):
    # Get video key
    if '?v=' in element:
        folder_suffix = element.split('?v=')[1]
        if '&' in folder_suffix:
            folder_suffix = folder_suffix.split('&')[0]

        segment_folder_name = f"segments_{folder_suffix}"

    if '--start-segment' == element:
        try:
            segment_number = int(args[index + 1])
        except:
            print_warning("Failed to get segment number, setting it to 0!")
            segment_number = 0

    if '--output-directory' == element:
        try:
            output_directory = pathlib.Path(args[index + 1])
            output_directory = output_directory.absolute()
            if not output_directory.exists():
                print_warning("Output directory does not exist, defaulting to the root directory of the script...")
                output_directory = ""
            else:
                print_info(f"Set output directory to {output_directory}")
        except Exception as e:
            print(e)
            print_warning("Output directory could not be set, defaulting to the root directory of the script...")
            output_directory = ""

    if '--cookie-file' == element:
        try:
            cookie_path = pathlib.Path(args[index + 1]).absolute()
            if not cookie_path.exists():
                print_error("Cookie file does not exist, defaulting to empty cookie...")
                cookie_content = {}
            else:
                print_info(f"Found cookie at {cookie_path}")
                cookie_content = parse_cookie_file(cookie_path)
                if cookie_content == {}:
                    print_info("Empty cookie!")
                else:
                    print_info(f"Cookie: {cookie_content}")

        except:
            print_error("Could not parse cookie, defaulting to empty cookie...")
            cookie_content = {}

if folder_suffix == "":
    print_error("No stream link given! Exiting now...")
    exit()


startTime = datetime.now()

# Create folder in root if no output path given
if output_directory == "":
    output_directory = pathlib.Path.cwd() / segment_folder_name
    if not pathlib.Path.is_dir(output_directory):
        pathlib.Path.mkdir(output_directory)
        print_info(f"Created directory {output_directory}")

else:
    output_directory = output_directory / segment_folder_name
    if not pathlib.Path.is_dir(output_directory):
        pathlib.Path.mkdir(output_directory)
        print_info(f"Created directory {output_directory}")

# Could I just have used an already existing mpeg-dash parser? Probably.
# Did the one I could find have any documentation?
# No.

def get_segment_list(dash_content, itag):
    global audio_base_url
    global audio_lmt_number
    global audio_lmt_distance
    global quality_audio_ranking

    global video_base_url
    global video_lmt_number
    global video_lmt_distance
    global quality_video_ranking

    if itag in quality_video_ranking:
        video_base_url = dash_content.split("<Representation id=\"{}\"".format(itag))[1]
        video_base_url = video_base_url.split("</BaseURL>")[0]
        video_base_url = video_base_url.split("<BaseURL>")[1]

        segment_list = []

        for i in range(0, 999999):
            try:
                video_segment_part = dash_content.split("<Representation id=\"{}\"".format(itag))[1]
                video_segment_part = video_segment_part.split("</SegmentList>")[0]
                video_segment_part = video_segment_part.split("sq/{}/".format(i))[1]
                first_segment = i
                video_segment_part = "sq/{}/".format(i) + video_segment_part.split("\"/>")[0]
                break
            except:
                pass
        last_segment = 0
        for i in range(i, 999999):
            try:
                ((dash_content.split("<Representation id=\"{}\"".format(itag))[1]).split("</SegmentList>")[0]).split("sq/{}/".format(i))[1]
            except:
                break
        last_segment = i

        video_lmt_number = 0
        video_lmt_distance = 0

        for j in range(first_segment, first_segment + 10):
            try:
                number = dash_content.split("<Representation id=\"{}\"".format(itag))[1]
                number = number.split("</SegmentList>")[0]
                number = number.split("sq/{}/".format(j))[1]
                number = number.split("/")[1]
                number = number.split("\"/>")[0][:-1]

                if(video_lmt_number == 0):
                    video_lmt_number = int(number)
                if int(number) - video_lmt_number > 0:
                    video_lmt_distance = int(number) - video_lmt_number
                    break
            except:
                pass

        for k in (range(0, last_segment)):
            segment_list.append("{}sq/{}/{}".format(video_base_url, k, video_lmt_number - (video_lmt_distance * (last_segment - k))))

        return segment_list

    if itag in quality_audio_ranking:
        audio_base_url = dash_content.split("<Representation id=\"{}\"".format(itag))[1]
        audio_base_url = audio_base_url.split("</BaseURL>")[0]
        audio_base_url = audio_base_url.split("<BaseURL>")[1]

        segment_list = []

        for i in range(0, 999999):
            try:
                audio_segment_part = dash_content.split("<Representation id=\"{}\"".format(itag))[1]
                audio_segment_part = audio_segment_part.split("</SegmentList>")[0]
                audio_segment_part = audio_segment_part.split("sq/{}/".format(i))[1]
                first_segment = i
                audio_segment_part = "sq/{}/".format(i) + audio_segment_part.split("\"/>")[0]
                break
            except:
                pass
        last_segment = 0
        for i in range(i, 999999):
            try:
                ((dash_content.split("<Representation id=\"{}\"".format(itag))[1]).split("</SegmentList>")[0]).split("sq/{}/".format(i))[1]
            except:
                break
        last_segment = i

        audio_lmt_number = 0
        audio_lmt_distance = 0

        for j in range(first_segment, first_segment + 10):
            try:
                number = dash_content.split("<Representation id=\"{}\"".format(itag))[1]
                number = number.split("</SegmentList>")[0]
                number = number.split("sq/{}/".format(j))[1]
                number = number.split("/")[1]
                number = number.split("\"/>")[0][:-1]

                if(audio_lmt_number == 0):
                    audio_lmt_number = int(number)
                if int(number) - audio_lmt_number > 0:
                    audio_lmt_distance = int(number) - audio_lmt_number
                    break
            except:
                pass

        for k in (range(0, last_segment)):
            segment_list.append("{}sq/{}/{}".format(audio_base_url, k, audio_lmt_number - (audio_lmt_distance * (last_segment - k))))

        return segment_list

def get_new_segment(dash_content, itag, old_segment_number):
    global video_base_url
    global video_lmt_distance
    global video_lmt_number

    global audio_base_url
    global audio_lmt_distance
    global audio_lmt_number

    global quality_audio_ranking
    global quality_video_ranking

    if itag in quality_audio_ranking:
        return "{}sq/{}/{}".format(audio_base_url, old_segment_number, audio_lmt_number - (audio_lmt_distance * (old_segment_number)))
    if itag in quality_video_ranking:
        return "{}sq/{}/{}".format(video_base_url, old_segment_number, video_lmt_number - (video_lmt_distance * (old_segment_number)))

def run_script():
    global output_directory
    global segment_number
    global dash_tries
    global cookie_content
    req = requests.get(sys.argv[1])
    headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36'
    }

    req = requests.get(sys.argv[1], headers=headers, cookies=cookie_content)
    print("Status code: {}".format(req.status_code))
    if req.status_code == 429:
        print_error("Too many requests. Please try again later (or get yourself another IP, I don't make the rules).")
        print_error("You might also just need to get yourself a new cookie. I'm not YouTube, what do I know?")
        return -1
    content_page = req.text
    content_page = content_page.split("var ytplayer = ytplayer || {};ytplayer.config = ")
    content_page = content_page[1]
    content_page = content_page.split(";ytplayer.web_player_context_config = ")
    content_page = content_page[0]

    filename_thing = sys.argv[1].split('?v=')
    filename_thing = filename_thing[1]
    try:
        j = json.loads(content_page)
    except Exception as e:
        print(e)

    x = json.loads(j['args']['player_response'])

    for el in x['responseContext']['serviceTrackingParams']:
        for i in el['params']:
            if i['key'] == 'cver':
                cver_string = i['value']

    # Select the best possible quality
    quality_video_ids = []
    quality_audio_ids = []

    global quality_video_ranking
    global quality_audio_ranking

    for i in range(len(x['streamingData']['adaptiveFormats'])):
        try:
            if x['streamingData']['adaptiveFormats'][i]['qualityLabel'] is not None:
                quality_video_ids.append(x['streamingData']['adaptiveFormats'][i]['itag'])
        except:
            pass

    for i in range(len(x['streamingData']['adaptiveFormats'])):
        try:
            if x['streamingData']['adaptiveFormats'][i]['audioQuality'] is not None:
                quality_audio_ids.append(x['streamingData']['adaptiveFormats'][i]['itag'])
        except:
            pass

    for i in quality_video_ranking:
        if i in quality_video_ids:
            chosen_quality_video = i
            break

    for i in quality_audio_ranking:
        if i in quality_audio_ids:
            chosen_quality_audio = i
            break

    print("Chosen video quality: {}".format(chosen_quality_video))
    print("Chose audio quality: {}".format(chosen_quality_audio))

    dash_url = x['streamingData']['dashManifestUrl']
    r = requests.get(dash_url).text

    dash_content = requests.get(dash_url).text
    global tries
    global retries
    video_segment_list = []

    session = requests.Session()
    biggest_segment = 0

    video_segment_list = get_segment_list(dash_content, chosen_quality_video)
    audio_segment_list = get_segment_list(dash_content, chosen_quality_audio)

    for i in range(segment_number, 999999):
        i = segment_number
        try:

            print("Segment number: {}".format(segment_number))
            print(f"Total number of segments: {len(video_segment_list)}")
            if segment_number > (len(video_segment_list)):
                dash_content = requests.get(dash_url).text
                time.sleep(50)
                segment_number = segment_number - 5
                continue
        # Segment might not be in list yet
        except:
            print("Exception")
            dash_content = requests.get(dash_url).text
            time.sleep(10)
            segment_number = segment_number - 5
            continue

        print(f"URL: {video_segment_list[segment_number]}")
        if segment_number < len(video_segment_list):

            while(True):
                try:
                    if(dash_tries == retries):
                        print("Exceeded {} retries! Exiting...".format(retries))
                        return -1

                    r = session.head(video_segment_list[segment_number])
                    if  r.status_code == 200:
                        break
                    dash_tries += 1
                    time.sleep(4)
                except:
                    dash_tries += 1
                    time.sleep(4)

            os.system("aria2c -c --auto-file-renaming=false --max-tries=100 --retry-wait=5 -j 3 -x 3 -s 3 -k 1M \"{}\" -d \"{}\" -o \"{}\"".format(video_segment_list[segment_number], output_directory, f"{segment_number}_{filename_thing}_video.ts"))
            while(True):
                try:
                    r = session.head(audio_segment_list[segment_number])
                    if r.status_code == 200:
                        break
                    time.sleep(2)
                except:
                    time.sleep(2)

            os.system("aria2c -c --auto-file-renaming=false --max-tries=100 --retry-wait=5 -j 3 -x 3 -s 3 -k 1M \"{}\" -d \"{}\" -o \"{}\"".format(audio_segment_list[segment_number], output_directory, f"{segment_number}_{filename_thing}_audio.ts"))
            try:
                if pathlib.Path(output_directory / f"{segment_number}_{filename_thing}_video.ts").stat().st_size < 2000 or pathlib.Path(output_directory / f"{segment_number}_{filename_thing}_audio.ts").stat().st_size < 2000:
                    segment_number -= 4
                    print("Trying again!")
                    continue
                else:
                    # It worked!
                    segment_number += 1
                    global startTime
                    print("Time since last reset: {}".format(datetime.now() - startTime))
            except:
                    segment_number -= 3
                    print("Trying again!")
                    continue

        if segment_number > biggest_segment:
            dash_tries = 0
            biggest_segment = segment_number
        else:
            dash_tries += 1

        if segment_number >= len(video_segment_list):
            print("Tries: {}".format(dash_tries))
            time.sleep(1)
            dash_content = requests.get(dash_url).text

            video_segment_list.append(get_new_segment(dash_content, int(chosen_quality_video), segment_number))
            audio_segment_list.append(get_new_segment(dash_content, int(chosen_quality_audio), segment_number))

            if dash_tries == retries:
                print("Exceeded {} retries! Exiting...".format(retries))
                return -1
        if ((datetime.now() - startTime) > timedelta(hours=5)):
            startTime = datetime.now()
            print("Reloading script!")
            return 0

# Yes I know this is ugly, shut up
ret = 0
while(True):
    try:
        ret = run_script()
        if ret == -1:
            exit()
    except:
        if ret == -1:
            exit()
        ret = 0
        time.sleep(10)
        pass
