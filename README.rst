===================================================
Tartube - The Easy Way To Watch And Download Videos
===================================================
------------------------------------------------------------
Works with YouTube, BitChute, and hundreds of other websites
------------------------------------------------------------

.. image:: screenshots/tartube.png
  :alt: Tartube screenshot

* `1 Introduction`_
* `2 Why should I use Tartube?`_
* `3 Quick start guide`_
* `4 Downloads`_
* `5 Installation`_
* `6 Getting started`_
* `7. Frequently-Asked Questions`_
* `8. Future plans`_
* `9. Known issues`_
* `10. Contributing`_
* `11. Authors`_
* `12. License`_

1 Introduction
==============

**Tartube** is a GUI front-end for `youtube-dl <https://youtube-dl.org/>`__, partly based on `youtube-dl-gui <https://mrs0m30n3.github.io/youtube-dl-gui/>`__ and written in Python 3 / Gtk 3.

It runs on MS Windows, Linux and BSD. It probably works on MacOS, but the authors have not been able to confirm this.

**Tartube** is beta software. **Test it carefully before you allow it to use your 100TB hard drive**, as it might not behave in the way you're expecting. 

Problems can be reported at `our GitHub page <https://github.com/axcore/tartube/issues>`__.

2 Why should I use Tartube?
===========================

-  You can download individual videos, and even whole channels and playlists, from YouTube and hundreds of other sites (see `here <https://ytdl-org.github.io/youtube-dl/supportedsites.html>`__ for a full list)
-  You can fetch information about those videos, channels and playlists, without actually downloading anything
-  **Tartube** will organise your videos into convenient folders
-  If creators upload their videos to more than one website (**YouTube** and **BitChute**, for example), you can download videos from both sites without creating duplicates
-  Certain popular websites manipulate search results, repeatedly unsubscribe people from their favourite channels and/or deliberately conceal videos that they don't like. **Tartube** won't do any of those things
-  **Tartube** can, in some circumstances, see videos that are region-blocked and/or age-restricted
-  **Tartube** is free and open-source software

3 Quick start guide 
===================

3.1 MS Windows
--------------

-  Download, install and run Tartube
-  When prompted, choose a folder where **Tartube** can store videos
-  When prompted, let **Tartube** install **youtube-dl** for you
-  It's recommended that you install **FFmeg**. From the menu, click **Operations > Install FFmpeg**
-  Go to the YouTube website, and find your favourite channel
-  In Tartube, click the **Add a new channel** button (or from the menu, click **Media > Add channel...** )
-  In the dialogue window, add the name of the channel and the address (URL)
-  Click the **OK** button to close the window
-  Click the **Check all** button. **Tartube** will fetch a list of videos in the channel
-  Click **All Videos** to see that list
-  If you want to download the videos, click the **Download all** button

3.2 Linux/BSD
~~~~~~~~~~~~~

-  Download and install `youtube-dl <https://youtube-dl.org/>`__
-  It's recommended that you install  `Ffmpeg <https://ffmpeg.org/>`__ or `AVConv <https://sourceforge.io/projects/avconv/>`__, too
-  Download Tartube. Installation is not necessary; you can just run the main script (navigate into the **Tartube** directory, open a terminal window, and type **python3 tartube/tartube**)
-  When prompted, choose a directory where **Tartube** can store videos
-  Go to the YouTube website, and find your favourite channel
-  In Tartube, click the **Add a new channel** button (or from the menu, click **Media > Add channel...** )
-  In the dialogue window, add the name of the channel and the address (URL)
-  Click the **OK** button to close the window
-  Click the **Check all** button. **Tartube** will fetch a list of videos in the channel
-  Click **All Videos** to see that list
-  If you want to download the videos, click the **Download all** button

4 Downloads
===========

Latest version: **v1.3.007 (20 Dec 2019)**

-  `MS Windows (32-bit) installer <https://sourceforge.net/projects/tartube/files/v1.3.007/install-tartube-1.3.007-32bit.exe/download>`__ from Sourceforge
-  `MS Windows (64-bit) installer <https://sourceforge.net/projects/tartube/files/v1.3.007/install-tartube-1.3.007-64bit.exe/download>`__ from Sourceforge
-  `Source code <https://sourceforge.net/projects/tartube/files/v1.3.007/tartube_v1.3.007.tar.gz/download>`__ from Sourceforge
-  `Source code <https://github.com/axcore/tartube>`__ and `support <https://github.com/axcore/tartube/issues>`__ from GitHub

5 Installation
==============

5.1 Installation - MS Windows
-----------------------------

MS Windows users should use the installer `available at the Tartube website <https://tartube.sourceforge.io/>`__. The installer contains everything you need to run Tartube. You must be using Windows Vista or above; the installer will not work on Windows XP.

If you want to use **ffmpeg**, see the section below.

**Some users report that Tartube will install but won't run**. This problem should be fixed as of v1.2.0 but, if you still have problems, you can try performing a manual installation. This takes about 10-30 minutes, depending on your internet speed.

- This section assumes you have a 64-bit computer
- Download and install MSYS2 from `msys2.org <https://msys2.org>`__. You need the file that looks something like **msys2-x86_64-yyyymmdd.exe**
- MSYS2 wants to install in **C:\\msys64**, so do that
- Open the MINGW64 terminal, which is **C:\\msys64\\mingw64.exe**
- In the MINGW64 terminal, type:

        **pacman -Syu**
        
- If the terminal wants to shut down, close it, and then restart it
- Now type the following commands, one by one:

        **pacman -Su**
        
        **pacman -S mingw-w64-x86_64-python3**
        
        **pacman -S mingw-w64-x86_64-python3-pip**
        
        **pacman -S mingw-w64-x86_64-python3-gobject**
        
        **pacman -S mingw-w64-x86_64-python3-requests**
        
        **pacman -S mingw-w64-x86_64-gtk3**
        
        **pacman -S mingw-w64-x86_64-gsettings-desktop-schemas**        
        
- Download the Tartube source code from Sourceforge, using the links above
- Extract it into the folder **C:\\msys64\\home\\YOURNAME**, creating a folder called **C:\\msys64\\home\\YOURNAME\\tartube**
- Now, to run Tartube, type these commands in the MINGW64 terminal:

        **cd tartube**
        
        **python3 tartube**

5.2 Installation - MacOS
------------------------

Tartube should run on MacOS, but the authors don't have access a MacOS system. If you are a MacOS user, open an issue at our Github page, and we'll work out the installation procedure together.

5.3 Installation - Linux/BSD
----------------------------

Linux/BSD users can use any of the following installation methods.

5.3.1 Linux/BSD Installation requirements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  `youtube-dl <https://youtube-dl.org/>`__
-  `Python 3 <https://www.python.org/downloads>`__
-  `Gtk 3 <https://python-gtk-3-tutorial.readthedocs.io/en/latest/>`__
-  `Python Requests module <https://3.python-requests.org/>`__

5.3.2 Optional dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  `Python xdg module <https://pypi.org/project/xdg/>`__ - required if you want to package **Tartube**
-  `Python pip <https://pypi.org/project/pip/>`__ - keeping youtube-dl up to date is much simpler when pip is installed
-  `Python moviepy module <https://pypi.org/project/moviepy/>`__ - if the website doesn't tell Tartube about the length of its videos, moviepy can work it out
-  `Ffmpeg <https://ffmpeg.org/>`__ or `AVConv <https://sourceforge.io/projects/avconv/>`__ - see the section below if you want to use FFmpeg or AVConv

5.3.3 Install using PyPI
~~~~~~~~~~~~~~~~~~~~~~~~

Installation via ``pip`` does not work. I have given up trying to make it work.

5.3.4 Install from source
~~~~~~~~~~~~~~~~~~~~~~~~~

1. Download & extract the source
2. Change directory into the **Tartube** directory
3. Type: ``python3 setup.py install``
4. Type: ``tartube``

5.3.5 Run without installing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Download & extract the source
2. Change directory into the **Tartube** directory
3. The executable is inside a further sub-directory, so do **cd tartube** again
4. Type: ``python3 tartube``

6 Getting started
=================

6.1 Choose where to save videos
-------------------------------

When you first start **Tartube**, you will be asked to choose where Tartube should save its videos.

.. image:: screenshots/example1.png
  :alt: Setting Tartube's data folder

Regardless of which location you select, you can change it later, if you need to.

-  Click **Edit > System preferences...**
-  Click the **General** tab
-  Check the location of the **Tartube data directory**
-  If you want to change it, click the **Change** button

6.2 Check youtube-dl is updated
-------------------------------

*This section does not apply if you installed Tartube via the Debian repository.*

**Tartube** uses **youtube-dl** to interact with websites like YouTube. You should check that **youtube-dl** is also installed and running correctly.

If you are using MS Windows, you will be prompted to install **youtube-dl**; you should click **Yes**.

.. image:: screenshots/example1b.png
  :alt: Installing youtube-dl on MS Windows
  
**youtube-dl** is updated every week or so. You can check that **youtube-dl** is installed and up to date:

.. image:: screenshots/example1c.png
  :alt: Updating youtube-dl

-  Click **Operations > Update youtube-dl**

6.3 Setting youtube-dl's location
---------------------------------

*This section does not apply if you installed Tartube via the Debian repository.*

If the update operation fails on MS Windows, you should `ask the authors for help <https://github.com/axcore/tartube/>`__.

On other systems, users can modify Tartube's settings. There are several locations on your filesystem where **youtube-dl** might have been installed. 

.. image:: screenshots/example2.png
  :alt: Updating youtube-dl

-  Click **Edit > System preferences...**
-  Click the **youtube-dl** tab
-  Try changing the setting **'Actual path to use during download/update/refresh operations'**
-  Try changing the setting **'Shell command for update operations'**
-  Try the update operation again

6.4 Setting the location of FFmpeg / AVConv
-------------------------------------------
  
**youtube-dl** can use the `FFmpeg library <https://ffmpeg.org/>`__ or the `AVConv library <https://sourceforge.io/projects/avconv/>`__ for various video-processing tasks, such as converting video files to audio, and for handling large resolutions (1080p and higher). If you want to use FFmpeg or AVConv, you should first install them on your system.

6.4.1 On MS Windows
~~~~~~~~~~~~~~~~~~~

On MS Windows, the usual methods of FFmpeg installation will not work. You **must** download a MinGW-compatible version of FFmpeg. The quickest way to do this is from the main menu: click **Operations > Install FFmpeg**.

There is no known method of installing a compatible version of AVConv.

6.4.2 On Linux/BSD
~~~~~~~~~~~~~~~~~~

On Linux/BSD, **youtube-dl** might be able to detect FFmpeg/AVConv without any help from you. If not, you can tell Tartube where to find FFmpeg/AVConv in this same tab.

.. image:: screenshots/example2b.png
  :alt: Updating ffmpeg

6.5 Introducing system folders
------------------------------

On the left side of the **Tartube** window is a list of folders. You can store videos, channels and playlists inside these folders. You can even store folders inside of other folders.

**Tartube** saves videos on your filesystem using exactly the same structure.

.. image:: screenshots/example3.png
  :alt: Tartube's system folders
  
When you start **Tartube**, there are five folders already visible. You can't remove any of these folders (but you can hide them, if you want).

Videos saved to the **Temporary Videos** folder are deleted when **Tartube** shuts down.

6.6 Adding videos
-----------------

You can add individual videos by clicking the **'Videos'** button near the top of the window. A popup window will appear.

.. image:: screenshots/example4.png
  :alt: Adding videos

Copy and paste the video's URL into the popup window. You can copy and paste as many URLs as you like.

When you're finished, click the **OK** button. 

Finally, click on the **Unsorted Videos** folder to see the videos you've added.

.. image:: screenshots/example5.png
  :alt: Your first added video

6.7 Adding channels and playlists
---------------------------------

You can also add a whole channel by clicking the **'Channel'** button or a whole playlist by clicking the **'Playlist'** button. 

**Tartube** will download all of the videos in the channel or playlist.

.. image:: screenshots/example6.png
  :alt: Adding a channel

Copy and paste the channel's URL into the popup window. You should also give the channel a name. The channel's name is usually the name used on the website (but you can choose any name you like).

6.8 Adding folders
------------------

The left-hand side of the window will quickly still filling up. It's a good idea to create some folders, and to store your channels/playlists inside those folders.

Click the **'Folder'** button near the top of the window,  and create a folder called **Comedy**. 

.. image:: screenshots/example7.png
  :alt: Adding a folder

Then repeat that process to create a folder called **Music**. You can then drag-and-drop your channels and playlists into those folders.

.. image:: screenshots/example8.png
  :alt: A channel inside a folder

6.9 Things you can do
----------------------

Once you've finished adding videos, channels, playlists and folders, there are basically four things **Tartube** can do:

-  **'Check'** - Fetch information about videos, but don't download them
-  **'Download'** - Actually download the videos. If you have disabled downloads for a particular item, **Tartube** will just fetch information about it instead
-  **'Update'** - Updates youtube-dl, as described above
-  **'Refresh'** - Examines your filesystem. If you have manually copied any videos into **Tartube**'s data directory, those videos are added to
   **Tartube**'s database

.. image:: screenshots/example9.png
  :alt: The Check and Download buttons
  
To **Check** or **Download** videos, channels and playlists, use the buttons near the top of the window. To **Refresh** **Tartube**'s database, use the menu.

**Protip:** Do an **'Update'** operation before you do a **'Check'** or **'Download'** operation

**Protip:** Do a **'Check'** operation before you do **'Refresh'** operation

6.10 General download options
-----------------------------

**youtube-dl** offers a large number of download options. This is how to set them.

.. image:: screenshots/example10.png
  :alt: Opening the download options window
  
-  Click **Edit > General download options...**

A new window opens. Any changes you make in this window aren't actually applied until you click the **'Apply'** or **'OK'** buttons.

6.11 Other download options
---------------------------

Those are the *default* download options. If you want to apply a *different* set of download options to a particular channel or particular playlist, you can do so.

At the moment, the general download options apply to *all* the videos, channels, playlists and folders you've added.

.. image:: screenshots/example11.png
  :alt: The window with only general download options applied
  
Now, suppose you want to apply some download options to the **Music** folder:

-  Right-click the folder, and select **Apply download options...**

In the new window, click the **'OK'** button. The options are applied to *everything* in the **Music folder**. A pen icon appears above the folder to remind you of this.

.. image:: screenshots/example12.png
  :alt: Download options applied to the Music folder

Now, suppose you want to add a *different* set of download options, but only for the **Village People** channel.

-  Right-click the channel, and select **Apply download options...**
-  In the new window, click the **'OK'** button

The previous set of download options still applies to everything in the **Music** folder, *except* the **Village People** channel.

.. image:: screenshots/example13.png
  :alt: Download options applied to the Village People channel

6.12 Favourite videos
---------------------

You can mark channels, playlists and even whole folders as favourites.

-  Right-click the channel, playlist or folder, and select
   **Mark videos > Favourite**

When you do that, any videos you download will appear in the **Favourite Videos** folder (as well as in their normal location).

6.13 Watching videos
--------------------

If you've downloaded a video, you can watch it by clicking the word **Player**.

.. image:: screenshots/example14.png
  :alt: Watching a video

If you haven't downloaded the video yet, you can watch it online by clicking the word **YouTube** or **Website**. (One or the other will be visible).

If it's a YouTube video that is restricted (not available in certain regions, or without confirming your age), it's often possible to watch the same video without restrictions on the **HookTube** website.

6.14 Combining channels, playlists and folders
----------------------------------------------

**Tartube** can download videos from several channels and/or playlists into a single directory (folder) on your computer's hard drive. There are three situations in which this might be useful:

- A channel has several playlists. You have added both the channel and its playlists to Tartube's database, but you don't want to download duplicate videos
- A creator releases their videos on **BitChute** as well as on **YouTube**. You have added both channels, but you don't want to download duplicate videos
- You don't care about keeping videos in separate directories/folders on your filesystem. You just want to download all videos to one place

6.14.1 Combining one channel and many playlists
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A creator might have a single channel, and several playlists. The playlists contain videos from that channel (but not necessarily *every* video).

You can add the channel and its playlists in the normal way but, if you do, **Tartube** will download many videos twice.

The solution is to tell **Tartube** to store all the videos from the channel and its playlists in a single location. In that way, you can still see a list of videos in each playlist, but duplicate videos are not actually downloaded to your filesystem.

- Click **Media > Add channel**..., and then enter the channel's details
- Click **Media > Add playlist**... for each playlist
- Now, right-click on each playlist in turn and select **Playlist actions > Set download destination...**
- In the dialogue window, click **Choose a different directory/folder**, select the name of the channel, then click the **OK button**

6.14.2 Combining channels from different websites
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A creator might release their videos on **YouTube**, but also on a site like **BitChute**. Sometimes they will only release a particular video on **BitChute**.

You can add both channels in the normal way but, if you do, **Tartube** will download many videos twice.

The solution is to tell **Tartube** to store videos from both channels in a single location. In that way, you can still see a list of videos in each channel, but duplicate videos are not actually downloaded to your filesystem.

- Click **Media > Add channel**..., and then enter the **YouTube** channel's details
- Click **Media > Add channel**..., and then enter the **BitChute** channel's details
- Right-click the **BitChute** channel and select **Channel actions > Set download destination...**
- In the dialogue window, click **Choose a different directory/folder**, select the name of the **YouTube** channel, then click the **OK button**

It doesn't matter which of the two channels you use as the download destination. There is also no limit to the number of parallel channels, so if a creator uploads videos to a dozen different websites, you can add them all.

6.14.3 Download all videos to a single folder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you don't care about keeping videos in separate directories/folders on your filesystem, you can download *all* videos into the **Unsorted videos** folder. Regardless of whether you have added one channel or a thousand, all the videos will be stored in that one place.

- Click **Edit > General download options... > Files**
- Click the **Download all videos into this folder** button to select it
- In the combo next to it, select **Unsorted Videos**

Alternatively, you could select **Temporary Videos**. If you do, videos will be deleted when you shut down **Tartube** (and will not be re-downloaded in the future).

6.15 Archiving videos
---------------------

You can tell **Tartube** to automatically delete videos after some period of time. This is useful if you don't have an infinitely large hard drive.

- Click **Edit > System preferences... > Videos** 
- Click the **Automatically delete downloaded videos after this many days** button to select it
- If you want to, change the number of days from 30 to some other value

If you want to protect your favourite videos from being deleted automatically, you can *archive* them. Only videos that have actually been downloaded can be archived.

- Right-click a video, and select **Video is archived**

You can also archive all the videos in a channel, playlist or folder. 

- For example, right-click a folder and select **Channel contents > Mark videos as archived**
- This action applies to *all* videos that are *currently* in the folder, including the contents of any channels and playlists in that folder
- It doesn't apply to any videos you might download in the future

6.16 Exporting/importing the Tartube database
---------------------------------------------

You can export the contents of **Tartube**'s database and, at any time in the future, import that information into a different **Tartube** database, perhaps on a different computer.

It is important to note that *only a list of videos, channels, playlists, folders are exported*. The videos themselves are not exported, and neither are any thumbnail, description or metadata files.

- Click **Media > Export from database**
- In the dialogue window, choose what you want to export
- If you want a list of videos, channels and playlists that you can edit by hand, select the **Export as plain text** option
- Click the **OK** button, then select where to save the export file

It is safe to share this export file with other people. It doesn't contain any personal information.

This is how to import the data into a different **Tartube** database.

- Click **Media > Import into database > JSON export file** or **Media > Import into database > Plain text export file**
- Select the export file you created earlier
- A dialogue window will appear. You can choose how much of the database you want to import

6.17 Importing videos from other applications
---------------------------------------------

**Tartube** is a GUI front-end for `youtube-dl <https://youtube-dl.org/>`__, but it is not the only one. If you've downloaded videos using another application, this is how to add them to Tartube's database.

- In **Tartube**'s main window, add each channel and playlist in the normal way
- When you're ready, click the **Check all** button. This adds a list of videos to Tartube's database, without actually downloading the videos themselves
- Copy the video files into Tartube's data folder. For example, copy all your **PewDiePie** videos into **../tartube-data/downloads/PewDiePie**
- In the **Tartube** menu, click **Operations > Refresh database**. **Tartube** will search for video files, and try to match them with the contents of its database
- The whole process might some time, so be patient

7. Frequently-Asked Questions
=============================

**Q: Why is the installer so big?**

Tartube is a Linux application. The installer for MS Windows contains not just Tartube itself, but a copy of Python and a whole bunch of essential graphics libraries, all of them ported to MS Windows.

If you're at all suspicious that such a small application uses such a large installer, you are invited to examine the installed files for yourself: 

**C:\\Users\\YOURNAME\\AppData\\Local\\Tartube**

(You might need to enable hidden folders; this can be done from the Control Panel.)

Everything is copied into this single folder. The installer doesn't modify the Windows registry, nor does it copy files anywhere else (other than to the desktop and the Start Menu). 

The NSIS scripts used to create the installers can be found here:

**C:\\Users\\YOURNAME\\AppData\\Local\\Tartube\\msys64\\home\\user\\tartube\\nsis**

The scripts contain full instructions, so you should be able to create your own installer, and compare it with the official one.

**Q: I can't install Tartube / I can't run Tartube / Tartube doesn't work properly / Tartube keeps crashing!**

A: Tartube is beta software. Please report any problems to the authors at our `Github page <https://github.com/axcore/tartube/issues>`__ 

**Q: After I downloaded some videos, Tartube crashed, and now all my videos are missing!**

A: Tartube creates a backup copy of the database, before trying to save a new copy. In the unlikely event of a failure, you can replace the broken database file with the backup file. 

To find Tartube's data directory (folder), click **Edit > System preferences... > General**.

- You can discard the broken **tartube.db** file
- Find the **tartube_TEMP_BU.db** file, and rename it **tartube.db**
- Restart Tartube
- Click the **Check All** button. Tartube will find all the last set of videos you downloaded, and add them to its database (without having to re-download them)

Tartube can make more frequent backups of your database file, if you want. See the options in **Edit > System preferences... > Backups**.

Note that Tartube does not create backup copies of the videos you've downloaded. That is your responsibility!

**Q: I want to see all the videos on a single page, not spread over several pages!**

A: At the bottom of the Tartube window, set the page size to zero, and press ENTER.

**Q: I just want to check for new videos, but it takes so long!**

A: By default, the underlying **youtube-dl** software checks an entire channel, even if it contains hundreds of videos. 

You can drastically reduce the time this takes by telling Tartube to stop checking/downloading videos, if it receives (for example) notifications for three videos it has already checked/downloaded.

This works well on sites like YouTube, which send information about videos in the order they were uploaded, newest first. We can't guarantee it will work on every site.

- Click **Edit > System preferences... > Performance**
- Select the checkbox **Stop checking/downloading a channel/playlist when it starts sending vidoes we already have**
- In the **Stop after this many videos (when checking)** box, enter the value 3
- In the **Stop after this many videos (when downloading)** box, enter the value 3
- Click **OK** to close the window

**Q: The toolbar is too small! There isn't enough room for all the buttons!**

A: Click **Edit > System preferences... > General > Don't show labels in the toolbar**.

MS Windows users can already see a toolbar without labels.

8. Future plans
===============

-  Fix the endless crashes **DONE**
-  Support for multiple databases (so you can store videos on two external hard    drives at the same time)
-  Add download scheduling **DONE**
-  Add video archiving **DONE**
-  Allow selection of multiple videos in the catalogue, so the same action can be applied to all of them at the same time **DONE**
-  Tie channels and playlists together, so that they won't both download the same video **DONE**
-  Add tooltips for everything **DONE**
-  Add more youtube-dl options **DONE**
-  Expand this guide to explain all features of Tartube

9. Known issues
===============

-  Tartube crashes continuously and often **FIXED**
-  Alphabetic sorting of channels/playlists/folders doesn't always work as intended, due to an unresolved Gtk issue **FIXED**
-  Channels/playlists/folder selection does not always work as intended, due to an unresolved Gtk issue **FIXED**
-  Users can type in comboboxes, but this should not be possible **FIXED**
-  Some MS Windows users report that Tartube will install, but not run **FIXED**
-  Some MS Windows users report that Tartube doesn't recognise FFmpeg **FIXED**
-  Installation via **pip** does not work

10. Contributing
================

-  Report a bug: Use the Github
   `issues <https://github.com/axcore/tartube/issues>`__ page

11. Authors
===========

See the `AUTHORS <AUTHORS>`__ file.

12. License
===========

Tartube is licensed under the `GNU General Public License v3.0 <https://www.gnu.org/licenses/gpl-3.0.en.html>`__.

✨🍰✨
