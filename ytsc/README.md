# youtube_stream_capture
Record YouTube livestreams from start to finish, that includes the ability to rewind up to 12 hours regardless of whether the actual YouTube player allows it or not. Unlike other recording solutions such as streamlink, youtube_stream_capture does not need to be restarted after six hours and therefore can record livestreams without any gaps.

## Installation
Requires `python3`, `aria2c`, `ffmpeg` as well as `ffprobe` (usually bundled with ffmpeg) to be installed and on your systems' PATH.
Example using Ubuntu:
```
# Install FFmpeg
$ sudo apt-get install ffmpeg
$ sudo apt-get install aria2
# Install required python modules
$ python3 -m pip install -r requirements.txt
```

If you're more of a visual learner, [here is a video](https://www.youtube.com/watch?v=vsLhLB7-LV0) showing you how to install and use the script.

## Usage
Starting the livestream capture:
```
$ python3 youtube_stream_capture.py [Link to the livestream] [optional: --output-directory (PATH TO DIRECTORY)] [optional: --start-segment (INT)] [optional: --cookie-file (PATH TO COOKIE.TXT)]
```

Merging all the segments after the stream has ended:
```
$ python3 merge.py [Link to the livestream] [optional: --output-directory (PATH TO DIRECTORY)]
```

Example for Windows:
```
$ python .\youtube_stream_capture.py python https://www.youtube.com/watch?v=wSYFfVrCipA --output-directory C:\Users\mrwnwttk\Desktop\ --start-segment 10
$ python .\merge.py https://www.youtube.com/watch?v=wSYFfVrCipA --output-directory C:\Users\mrwnwttk\Desktop\
```

Example for Linux:
```
$ python3 youtube_stream_caputure.py https://www.youtube.com/watch?v=OIW4RnlYvgs --output-directory /mnt/c/Users/mrwnwttk/Desktop/
$ python3 merge.py https://www.youtube.com/watch?v=OIW4RnlYvgs --output-directory /mnt/c/Users/mrwnwttk/Desktop/
```

Note: if you used the `--output-directory` parameter to start the livestream recording, then you also need to use it as a parameter for `merge.py`.


The `cookie` inside of `youtube_stream_capture.py` has intentionally been left empty. If you run into any 429 errors (Too many requests), try to use your own. Simply export it using a browser extension such as [cookies.txt](https://addons.mozilla.org/de/firefox/addon/cookies-txt/) and pass it as an argument into the script.

Example for Linux:
```
$ python3 youtube_stream_capture.py https://www.youtube.com/watch?v=ADyrjlsfcs --cookie-file /mnt/c/Users/mrwnwttk/Desktop/cookie.txt

[INFO] Found cookie at /mnt/c/Users/X1C4/Downloads/e11d26ef-2825-4311-8ab1-89af050d6b37.txt
[INFO] Cookie: {'VISITOR_INFO1_LIVE': 'XXXXXXXXXXX', 'LOGIN_INFO': 'XXXXXXXXXXXXXXXXXXXXXXXXXX', 'HSID': 'XXXXXXXXXXXXXXXXX', 'SSID': 'XXXXXXXXXXXXX', 'APISID': 'XXXXXXXXXXXX/XXXXXXXXXXXXXXXXX', 'SAPISID': 'XXXXXXXXXXXXXX/XXXXXXXXXXXXXX', '__Secure-3PAPISID': 'XXXXXXX/XXXXXXXXX', 'CONSENT': 'XXXX', '__Secure-3PSID': 'XXXXXXXXX', 'SID': 'XXXXXXXXXXXXXXXXXXXX', 'PREF': 'XXXXXXXX', 'YSC': 'XXXXXXXXXXX', 'SIDCC': 'XXXXXXXXXXXXXXXXXXXXXX', '__Secure-3PSIDCC': 'XXXXXXXXXXXXXXXXXXXX'}
```


## Support
Livestreams that have been running for multiple days (such as the 24/7 music livestreams) are not supported. youtube_stream_capture attempts to go back to the very first segment of a livestream by design. The first segments of those livestreams have long been deleted at this point, so the script just fails. The time limit here is usually about 12 hours.

Support for VP9 livestreams has been added, but is highly experimental at this point and therefore commented out. Use at your own risk and don't bother opening up any issues if something breaks or the video goes out of sync. I don't want to deal with it.

## License
The source code is licensed under GPL v3. For more information, consult the LICENSE file.
