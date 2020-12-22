#!/usr/bin/env python3

import os
import re
import time
import shutil
import pathlib

# Yes, in THAT ORDER. See here: https://stackoverflow.com/a/61069032
import colorama
colorama.init()

import sys
import subprocess

def print_error(message):
#   print(colorama.Fore.RED + f"[ERROR] {message}" + colorama.Style.RESET_ALL)
    print(f"[ERROR] {message}")

def print_warning(message):
#   print(colorama.Fore.YELLOW + f"[WARNING] {message}" + colorama.Style.RESET_ALL)
    print(f"[WARNING] {message}")

def print_info(message):
#       print(colorama.Fore.CYAN + f"[INFO] {message}" + colorama.Style.RESET_ALL)
    print(f"[INFO] {message}")

def sorted_alphanumeric(data):
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
    return sorted(data, key=alphanum_key)

def merge_v1(audio_list, video_list, video_key, output_directory, segment_folder_name, final_export=0):
	with open(output_directory / "list_{}_audio.txt".format(video_key), "w") as f:
		for i in audio_list:
			f.write(f"file '{i}'\n")

	os.system("ffmpeg -loglevel panic -y -f concat -safe 0 -i \"{}\" -c:a copy \"{}\"".format(output_directory / f"list_{video_key}_audio.txt", output_directory / f"{video_key}_audio_v1_ffmpeg.m4a"))
	os.remove(output_directory / f"list_{video_key}_audio.txt")


	with open(output_directory / f"list_{video_key}_video.txt", "w") as f:
		for i in video_list:
			f.write(f"file '{i}'\n")

	os.system("ffmpeg -loglevel panic -y -f concat -safe 0 -i \"{}\" -c:v copy \"{}\"".format(output_directory / f"list_{video_key}_video.txt", output_directory / f"{video_key}_video_v1_ffmpeg.mp4"))
	os.remove(output_directory / f"list_{video_key}_video.txt")

	if final_export == 1:
		final_output_filename = output_directory / f"{video_key}.mp4"
	else:
		final_output_filename = output_directory / f"{video_key}_v1.mp4"

	os.system("ffmpeg -loglevel panic -y -i \"{}\" -i \"{}\" -c:a copy -c:v copy \"{}\"".format(output_directory / f"{video_key}_video_v1_ffmpeg.mp4", output_directory / f"{video_key}_audio_v1_ffmpeg.m4a", final_output_filename))

	os.remove(output_directory / f"{video_key}_audio_v1_ffmpeg.m4a")
	os.remove(output_directory / f"{video_key}_video_v1_ffmpeg.mp4")


	return (final_output_filename)

def merge_v2(audio_list, video_list, video_key, output_directory, segment_folder_name, final_export=0):
	with open(output_directory / f"concat_{video_key}_audio.ts","wb") as f:
		for i in audio_list:
			with open(i, "rb") as ff:
				shutil.copyfileobj(ff, f)

	os.system("ffmpeg -loglevel panic -y -i \"{}\" -c:a copy \"{}\"".format(output_directory / f"concat_{video_key}_audio.ts", output_directory / f"{video_key}_audio_v2_ffmpeg.m4a"))
	os.remove(output_directory / f"concat_{video_key}_audio.ts")


	with open(output_directory / f"concat_{video_key}_video.ts","wb") as f:
		for i in video_list:
			with open(i, "rb") as ff:
				shutil.copyfileobj(ff, f)

	os.system("ffmpeg -loglevel panic -y -i \"{}\" -c:v copy \"{}\"".format(output_directory / f"concat_{video_key}_video.ts", output_directory / f"{video_key}_video_v2_ffmpeg.mp4"))
	os.remove(output_directory / f"concat_{video_key}_video.ts")


	if final_export == 1:
		final_output_filename = output_directory / f"{video_key}.mp4"
	else:
		final_output_filename = output_directory / f"{video_key}_v2.mp4"


	os.system("ffmpeg -loglevel panic -y -i \"{}\" -i \"{}\" -c:a copy -c:v copy \"{}\"".format(output_directory / f"{video_key}_audio_v2_ffmpeg.m4a", output_directory / f"{video_key}_video_v2_ffmpeg.mp4", output_directory / f"{video_key}_v2.mp4"))
	os.remove(output_directory / f"{video_key}_audio_v2_ffmpeg.m4a")
	os.remove(output_directory / f"{video_key}_video_v2_ffmpeg.mp4")

	return (final_output_filename)

args = sys.argv
output_directory = ""

for index, element in enumerate(args):
	if '?v=' in element:
		video_key = element.split('?v=')[1]
		if '&' in video_key: 
			video_key = video_key.split('&')[0]
		segment_folder_name = f"segments_{video_key}"

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

if video_key == "":
	print_error("No URL given! Exiting now...")
	exit()

# Create folder in root if no output path given
if output_directory == "":
	output_directory = pathlib.Path.cwd()

if not pathlib.Path.is_dir(output_directory / segment_folder_name):
	print_error(f"Directory with stream segments is missing from {output_directory}!")
	print_error(f"Expected directory to be present at {output_directory / segment_folder_name}! Exiting now...")
	exit()

print_info("Checking available segments...")
dirlist = sorted_alphanumeric([x.name for x in pathlib.Path(output_directory / segment_folder_name).glob('*.ts')])
first_segment = int(dirlist[0].split('_')[0])
print_info(f"First segment: {output_directory / dirlist[0]}")
last_segment = int(dirlist[-1].split('_')[0])
print_info(f"Last segment: {output_directory / dirlist[-1]}")
print_info(f"Total number of segments (audio & video): {len(dirlist)}")
print_info("Checking for missing segments...")

missing_files = False
total_segment_list_sorted_video = []
total_segment_list_sorted_audio = []

for f in range(first_segment, last_segment):
	if not pathlib.Path(output_directory / segment_folder_name / f"{f}_{video_key}_video.ts").is_file():
		print_warning("Missing segment: {}".format(output_directory / segment_folder_name / f"{f}_{video_key}_video.ts"))
		missing_files = True
	elif not pathlib.Path(output_directory / segment_folder_name / f"{f}_{video_key}_audio.ts").is_file():
		print_warning("Missing segment: {}".format(output_directory / segment_folder_name / f"{f}_{video_key}_audio.ts"))
		missing_files = True
	else:
		total_segment_list_sorted_audio.append(output_directory / segment_folder_name / f"{f}_{video_key}_audio.ts")
		total_segment_list_sorted_video.append(output_directory / segment_folder_name / f"{f}_{video_key}_video.ts")

if missing_files == True:
	print_warning("There were missing segments! Merged output might might noticeably skip at certain points...")
else:
	print_info("No missing segments!")

print_info("Analyzing files...")
cmd = " ".join(['ffprobe', '-v', 'quiet', '-hide_banner', '-show_streams','\"{}\"'.format(total_segment_list_sorted_video[0]), '2>&1'])
ffprobe_output = os.popen(cmd).read().split('\n')

for line in ffprobe_output:
	if 'codec_tag_string' in line:
		codec_tag_string = line.split("=")[1]
		print_info(line)
	if 'codec_name' in line:
		codec_name = line.split("=")[1]
		print_info(line)
	if 'r_frame_rate' in line:
		r_frame_rate = line.split("=")[1]
		print_info(line)
	if 'height=' in line:
		height = line.split("=")[1]
		print_info(line)

merge_v1_test_segments_audio = []
merge_v1_test_segments_video = []

print_info("Testing merge method 1 / 2...")
if (len(total_segment_list_sorted_video) + len(total_segment_list_sorted_audio)) >= 200:
	merge_v1_test_segments_audio = total_segment_list_sorted_audio[:100]
	merge_v1_test_segments_video = total_segment_list_sorted_video[:100]
else:
	merge_v1_test_segments_audio = total_segment_list_sorted_audio
	merge_v1_test_segments_video = total_segment_list_sorted_video


v1_test_path = merge_v1(merge_v1_test_segments_audio, merge_v1_test_segments_video, video_key, output_directory, segment_folder_name)

merge_v2_test_segments_audio = []
merge_v2_test_segments_video = []

print_info("Testing merge method 2 / 2...")
if (len(total_segment_list_sorted_video) + len(total_segment_list_sorted_audio)) >= 200:
	merge_v2_test_segments_audio = total_segment_list_sorted_audio[:100]
	merge_v2_test_segments_video = total_segment_list_sorted_video[:100]
else:
	merge_v2_test_segments_audio = total_segment_list_sorted_audio
	merge_v2_test_segments_video = total_segment_list_sorted_video


v2_test_path = merge_v2(merge_v1_test_segments_audio, merge_v1_test_segments_video, video_key, output_directory, segment_folder_name)

print_info("Checking file of method 1...")
cmd = " ".join(['ffprobe', '-v', 'quiet', '-hide_banner', '-show_streams','\"{}\"'.format(v1_test_path), '2>&1'])
ffprobe_output = os.popen(cmd).read().split('\n')

for line in ffprobe_output:
	if 'duration=' in line:
		duration_v1 = float(line.split("=")[1])
		break

print_info(line)

print_info("Checking file of method 2...")
cmd = " ".join(['ffprobe', '-v', 'quiet', '-hide_banner', '-show_streams','\"{}\"'.format(v2_test_path), '2>&1'])
ffprobe_output = os.popen(cmd).read().split('\n')

for line in ffprobe_output:
	if 'duration=' in line:
		duration_v2 = float(line.split("=")[1])
		break

print_info(line)

f1_working = True
f2_working = True

os.remove(v1_test_path)
os.remove(v2_test_path)

if duration_v1 < (len(merge_v1_test_segments_audio) * 0.8) or (duration_v1 > 20 * len(merge_v1_test_segments_audio)):
	print_warning("File of method 1 broken.")
	f1_working = False

if duration_v2 < (len(merge_v2_test_segments_audio) * 0.8) or (duration_v2 > 20 * len(merge_v2_test_segments_audio)):
	print_warning("File of method 2 broken.")
	f2_working = False

if f1_working:
	print_info("Using method 1 for this livestream. This process might take a while...")
	v1_path = merge_v1(total_segment_list_sorted_audio, total_segment_list_sorted_video, video_key, output_directory, segment_folder_name, 1)
	print("Output file: {}".format(v1_path))
elif f2_working:
	print_info("using method 2 for this livestream. This process might take a while...")
	v2_path = merge_v2(total_segment_list_sorted_audio, total_segment_list_sorted_video, video_key, output_directory, segment_folder_name, 1)
	print("Output file: {}".format(v2_path))
else:
	print_error("Both methods aren't working for some reason. Don't delete the recording just yet! If you're sure that you didn't mess with the files in any way, please open an issue on Github and report this.")
