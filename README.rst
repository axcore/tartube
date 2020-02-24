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
* `3 Downloads`_
* `4 Quick start guide`_
* `5 Installation`_
* `6 Using Tartube`_
* `7. Frequently-Asked Questions`_
* `8. Contributing`_
* `9. Authors`_
* `10. License`_

1 Introduction
==============

**Tartube** is a GUI front-end for `youtube-dl <https://youtube-dl.org/>`__, partly based on `youtube-dl-gui <https://mrs0m30n3.github.io/youtube-dl-gui/>`__ and written in Python 3 / Gtk 3.

It runs on MS Windows, Linux and BSD. It probably works on MacOS, but the authors have not been able to confirm this.

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

3 Downloads
===========

Latest version: **v1.5.015 (24 Feb 2019)**

-  `MS Windows (32-bit) installer <https://sourceforge.net/projects/tartube/files/v1.5.015/install-tartube-1.5.015-32bit.exe/download>`__ from Sourceforge
-  `MS Windows (64-bit) installer <https://sourceforge.net/projects/tartube/files/v1.5.015/install-tartube-1.5.015-64bit.exe/download>`__ from Sourceforge
-  `Source code <https://sourceforge.net/projects/tartube/files/v1.5.015/tartube_v1.5.015.tar.gz/download>`__ from Sourceforge
-  `Source code <https://github.com/axcore/tartube>`__ and `support <https://github.com/axcore/tartube/issues>`__ from GitHub

4 Quick start guide 
===================

4.1 MS Windows
--------------

-  Download, install and run **Tartube**
-  When prompted, choose a folder where **Tartube** can store videos
-  When prompted, let **Tartube** install **youtube-dl** for you
-  It's strongly recommended that you install **FFmeg**. From the menu, click **Operations > Install FFmpeg**
-  Go to the YouTube website, and find your favourite channel
-  In **Tartube**, click the **Add a new channel** button (or from the menu, click **Media > Add channel...** )
-  In the dialogue window, add the name of the channel and the address (URL)
-  Click the **OK** button to close the window
-  Click the **Check all** button. **Tartube** will fetch a list of videos in the channel
-  Click **All Videos** to see that list
-  If you want to download the videos, click the **Download all** button

4.2 Linux/BSD
~~~~~~~~~~~~~

-  Download and install `youtube-dl <https://youtube-dl.org/>`__
-  It's strongly recommended that you install  `Ffmpeg <https://ffmpeg.org/>`__ or `AVConv <https://sourceforge.io/projects/avconv/>`__, too
-  Download **Tartube**. Installation is not necessary; you can just run the main script (navigate into the **Tartube** directory, open a terminal window, and type **python3 tartube/tartube**)
-  When prompted, choose a directory where **Tartube** can store videos
-  Go to the YouTube website, and find your favourite channel
-  In **Tartube**, click the **Add a new channel** button (or from the menu, click **Media > Add channel...** )
-  In the dialogue window, add the name of the channel and the address (URL)
-  Click the **OK** button to close the window
-  Click the **Check all** button. **Tartube** will fetch a list of videos in the channel
-  Click **All Videos** to see that list
-  If you want to download the videos, click the **Download all** button

5 Installation
==============

5.1 Installation - MS Windows
-----------------------------

MS Windows users should use the installer `available at the **Tartube** website <https://tartube.sourceforge.io/>`__. The installer contains everything you need to run **Tartube**. You must be using Windows Vista or above; the installer will not work on Windows XP.

If you want to use **FFmpeg**, see `6.4 Setting the location of FFmpeg / AVConv`_. 

From v1.4, the installer includes a copy of `AtomicParsley <https://bitbucket.org/jonhedgerows/atomicparsley/wiki/Home>`__, so there is no need to install it yourself.

5.1.1 Manual installation - MS Windows
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Some users report that **Tartube** will install but won't run. This problem should be fixed as of v1.2.0 but, if you still have problems, you can try performing a manual installation. This takes about 10-30 minutes, depending on your internet speed.

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
        
- Download the **Tartube** source code from Sourceforge, using the links above
- Extract it into the folder **C:\\msys64\\home\\YOURNAME**, creating a folder called **C:\\msys64\\home\\YOURNAME\\tartube**
- Now, to run **Tartube**, type these commands in the MINGW64 terminal:

        **cd tartube**
        
        **python3 tartube**

5.2 Installation - MacOS
------------------------

**Tartube** should run on MacOS, but the authors don't have access a MacOS system. If you are a MacOS user, open an issue at our Github page, and we'll work out the installation procedure together.

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

-  `Python xdg module <https://pypi.org/project/xdg/>`__ - recommended so that **Tartube**'s configuration file is saved in a standard location
-  `Python pip <https://pypi.org/project/pip/>`__ - keeping youtube-dl up to date is much simpler when pip is installed
-  `Python moviepy module <https://pypi.org/project/moviepy/>`__ - if the website doesn't tell **Tartube** about the length of its videos, moviepy can work it out
-  `Ffmpeg <https://ffmpeg.org/>`__ or `AVConv <https://sourceforge.io/projects/avconv/>`__ - required for various video post-processing tasks; see the section below if you want to use FFmpeg or AVConv
-  `AtomicParsley <https://bitbucket.org/wez/atomicparsley/src/default/>`__ - required for embedding thumbnails in audio files

5.3.3 Install using PyPI
~~~~~~~~~~~~~~~~~~~~~~~~

**Tartube** can be installed from `PyPI <https://pypi.org/project/tartube/>`__ with or without root privileges.

Here is the procedure for Debian-based distributions, like Ubuntu and Linux Mint. The procedure on other distributions is probably very similar.

5.3.4 Install using PyPI (with root privileges)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Make sure **youtube-dl** has been completely removed from your system
2. Type: ``sudo apt install python3-pip``
3. Type: ``sudo pip3 install youtube-dl tartube``
4. Type: ``tartube``

5.3.5 Install using PyPI (without root privileges)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Type: ``sudo apt install python3-pip``
2. Type: ``pip3 install tartube``
3. The **Tartube** executable is stored in **~/.local/bin** by default. If that is already in your path, you can start **Tartube** by typing ``tartube``. Otherwise, type ``~/.local/bin/tartube``
4. **Tartube** asks you to choose a data directory, so do that
5. In the **Tartube** main window, click **Edit > System preferences... > youtube-dl**
6. In the box marked **Actual path to use**, select **Use PyPI path (\~/.local/bin/youtube-dl)**
7. Click **OK** to close the dialogue window
8. Click **Operations > Update youtube-dl**
9. Once the update has finished, **Tartube** is ready for use

5.3.6 Install from source
~~~~~~~~~~~~~~~~~~~~~~~~~

1. Download & extract the source
2. Change directory into the **Tartube** directory
3. Type: ``python3 setup.py install``
4. Type: ``tartube``

5.3.7 Run without installing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Download & extract the source
2. Change directory into the **Tartube** directory
3. Type: ``python3 tartube/tartube``

6 Using Tartube
===============

* `6.1 Choose where to save videos`_
* `6.2 Check youtube-dl is updated`_
* `6.3 Setting youtube-dl's location`_
* `6.4 Setting the location of FFmpeg / AVConv`_
* `6.4.1 On MS Windows`_
* `6.4.2 On Linux/BSD`_
* `6.5 Introducing system folders`_
* `6.6 Adding videos`_
* `6.7 Adding channels and playlists`_
* `6.8 Adding videos, channels and playlists together`_
* `6.9 Adding folders`_
* `6.10 Things you can do`_
* `6.11 General download options`_
* `6.12 Other download options`_
* `6.13 Custom downloads`_
* `6.13.1 Independent downloads`_
* `6.13.2 Diverting to HookTube/Invidious`_
* `6.13.3 Delays between downloads`_
* `6.14 Watching videos`_
* `6.15 Filtering and finding videos`_
* `6.16 Marking videos`_
* `6.16.1 Bookmarked videos`_
* `6.16.2 Favourite channels, playlists and folders`_
* `6.17 Combining channels, playlists and folders`_
* `6.17.1 Combining one channel and many playlists`_
* `6.17.2 Combining channels from different websites`_
* `6.17.3 Download all videos to a single folder`_
* `6.18 Archiving videos`_
* `6.19 Managing databases`_
* `6.19.1 Importing videos from other applications`_
* `6.19.2 Multiple databases`_
* `6.19.3 Multiple Tartubes`_
* `6.19.4 Exporting/importing the database`_
* `6.20 Converting to audio`_

6.1 Choose where to save videos
-------------------------------

When you first start **Tartube**, you will be asked to choose where **Tartube** should save its videos.

.. image:: screenshots/example1.png
  :alt: Setting Tartube's data folder

Regardless of which location you select, you can change it later, if you need to - see `6.19 Managing databases`_

- In the main menu, click **File > Database preferences...**
- In the new window, check the location of the **Tartube data directory**
- If you want to change it, click the **Change** button

6.2 Check youtube-dl is updated
-------------------------------

*This section does not apply if you installed **Tartube** via an official Debian repository.*

**Tartube** uses **youtube-dl** to interact with websites like YouTube. You should check that **youtube-dl** is also installed and running correctly.

If you are using MS Windows, you will be prompted to install **youtube-dl**; you should click **Yes**.

.. image:: screenshots/example2.png
  :alt: Installing youtube-dl on MS Windows
  
**youtube-dl** is updated every week or so. You can check that **youtube-dl** is installed and up to date:

.. image:: screenshots/example3.png
  :alt: Updating youtube-dl

-  Click **Operations > Update youtube-dl**

6.3 Setting youtube-dl's location
---------------------------------

*This section does not apply if you installed **Tartube** via an official Debian repository.*

If the update operation fails on MS Windows, you should `ask the authors for help <https://github.com/axcore/tartube/>`__.

On other systems, users can modify **Tartube**'s settings. There are several locations on your filesystem where **youtube-dl** might have been installed. 

.. image:: screenshots/example4.png
  :alt: Updating youtube-dl

-  Click **Edit > System preferences... > youtube-dl**
-  Try changing the setting **Actual path to use**
-  Try changing the setting **Shell command for update operations**
-  Try the update operation again

6.4 Setting the location of FFmpeg / AVConv
-------------------------------------------
  
**youtube-dl** can use the `FFmpeg library <https://ffmpeg.org/>`__ or the `AVConv library <https://sourceforge.io/projects/avconv/>`__ for various video-processing tasks, such as converting video files to audio, and for handling large resolutions (1080p and higher). If you want to use FFmpeg or AVConv, you should first install them on your system.

6.4.1 On MS Windows
~~~~~~~~~~~~~~~~~~~

On MS Windows, the usual methods of FFmpeg installation will not work. You **must** download a MinGW-compatible version of FFmpeg. The quickest way to do this is from **Tartube**'s main menu: click **Operations > Install FFmpeg**.

There is no known method of installing a compatible version of AVConv.

6.4.2 On Linux/BSD
~~~~~~~~~~~~~~~~~~

On Linux/BSD, **youtube-dl** might be able to detect FFmpeg/AVConv without any help from you. If not, you can tell **Tartube** where to find FFmpeg/AVConv in this same tab.

.. image:: screenshots/example5.png
  :alt: Updating ffmpeg

6.5 Introducing system folders
------------------------------

On the left side of the **Tartube** window is a list of folders. You can store videos, channels and playlists inside these folders. You can even store folders inside of other folders.

**Tartube** saves videos on your filesystem using exactly the same structure.

.. image:: screenshots/example6.png
  :alt: Tartube's system folders
  
When you start **Tartube**, there are seven folders already visible. You can't remove any of these folders (but you can hide them, if you want).

- The **All Videos** folder shows every video in **Tartube**'s database, whether it has been downloaded or not
- The **Bookmarks** folder shows videos you've bookmarked, because they're interesting or important (see `6.16.1 Bookmarked videos`_ )
- The **Favourite Videos** folder shows videos in a channel, playlist or folder that you've marked as a favourite (see `6.16.2 Favourite channels, playlists and folders`_ )
- The **New Videos** folder shows videos that have been downloaded, but not yet watched
- The **Waiting Videos** folder shows videos that you want to watch soon. When you watch the video, it's automatically removed from the folder (but not from **Tartube**'s database)
- Videos saved to the **Temporary Videos** folder will be deleted when **Tartube** next starts
- The **Unsorted Videos** folder is a useful place to put videos that don't belong to a particular channel or playlist

6.6 Adding videos
-----------------

You can add individual videos by clicking the **'Videos'** button near the top of the window. A dialogue window will appear.

.. image:: screenshots/example7.png
  :alt: Adding videos

Copy and paste the video's URL into the dialogue window. You can copy and paste as many URLs as you like.

When you're finished, click the **OK** button. 

Finally, click on the **Unsorted Videos** folder to see the videos you've added.

.. image:: screenshots/example8.png
  :alt: Your first added video

6.7 Adding channels and playlists
---------------------------------

You can also add a whole channel by clicking the **'Channel'** button or a whole playlist by clicking the **'Playlist'** button. 

**Tartube** will download all of the videos in the channel or playlist.

.. image:: screenshots/example9.png
  :alt: Adding a channel

Copy and paste the channel's URL into the dialogue window. You should also give the channel a name. The channel's name is usually the name used on the website (but you can choose any name you like).

6.8 Adding videos, channels and playlists together
--------------------------------------------------

When adding a long list of URLs, containing a mixture of channels, playlists and individual videos, it's quicker to add them all at the same time. Click the **'Videos'** button near the top of the window, and paste all the links into the dialogue window.

**Tartube** doesn't know anything about these links until you actually download them (or check them). If it's expecting an individual video, but receives a channel or a playlist, **Tartube** will the handle the conversion for you.

By default, **Tartube** converts a link into a channel, when necessary. You can change this behaviour, if you want to.

- In **Tartube**'s main window, click **Edit > System preferences... > Operations > URL flexibility**
- Select one of the behaviours listed there

Unfortunately, there is no way for **Tartube** to distinguish a channel from a playlist. Most video websites don't supply that information.

If your list of URLs contains a mixture of channels and playlists, you can convert one to the other after the download has finished.

- In **Tartube**'s main window, right-click a channel, and select **Channel actions > Convert to playlist**
- Alternatively, right-click a playlist, and select **Channel actions > Convert to channel**
- After converting, you can set a name for the new channel/playlist by right-clicking it, and selecting **Channel actions > Rename channel...** or **Playlist actions > Rename playlist...**

6.9 Adding folders
------------------

The left-hand side of the window will quickly still filling up. It's a good idea to create some folders, and to store your channels/playlists inside those folders.

Click the **'Folder'** button near the top of the window,  and create a folder called **Comedy**. 

.. image:: screenshots/example10.png
  :alt: Adding a folder

Then repeat that process to create a folder called **Music**. You can then drag-and-drop your channels and playlists into those folders.

.. image:: screenshots/example11.png
  :alt: A channel inside a folder

6.10 Things you can do
----------------------

Once you've finished adding videos, channels, playlists and folders, you can make **Tartube** do something. **Tartube** offers the following operations:

-  **Check** - Fetches information about videos, but don't download them
-  **Download** - Actually downloads the videos. If you have disabled downloads for a particular item, **Tartube** will just fetch information about it instead
-  **Custom download** - Downloads videos in a non-standard way; see `6.13 Custom downloads`_
-  **Refresh** - Examines your filesystem. If you have manually copied any videos into **Tartube**'s data directory, those videos are added to **Tartube**'s database
-  **Update** - Installs or updates **youtube-dl**, as described in `6.2 Check youtube-dl is updated`_. Also installs FFmpeg (on MS Windows only); see `6.4 Setting the location of FFmpeg / AVConv`_
-  **Info** - Fetches information about a particular video: either the available video/audio formats, or the available subtitles
-  **Tidy** - Tidies up **Tartube**'s data directory, as well as checking that downloaded videos still exist and are not corrupted

.. image:: screenshots/example12.png
  :alt: The Check and Download buttons
  
To **Check** or **Download** videos, channels and playlists, use the main menu, or the buttons near the top of the window, or right-click an individual video, channel or playlist. A **Custom Download** can be started from the main menu or by right-clicking.

To **Refresh** **Tartube**'s database, use the main menu (or right-click a channel/playlist/folder).

**Protip:** Do an **'Update'** operation before you do a **'Check'** or **'Download'** operation

**Protip:** Do a **'Check'** operation before you do **'Refresh'** operation

To fetch **Info** about a video, right-click it. 

To **Tidy** the data directory, use the main menu (or right-click a channel/playlist/folder).

6.11 General download options
-----------------------------

**youtube-dl** offers a large number of download options. This is how to set them.

.. image:: screenshots/example13.png
  :alt: Opening the download options window
  
-  Click **Edit > General download options...**

A new window opens. Any changes you make in this window aren't actually applied until you click the **'Apply'** or **'OK'** buttons.

6.12 Other download options
---------------------------

Those are the *default* download options. If you want to apply a *different* set of download options to a particular channel or particular playlist, you can do so.

At the moment, the general download options apply to *all* the videos, channels, playlists and folders you've added.

.. image:: screenshots/example14.png
  :alt: The window with only general download options applied
  
Now, suppose you want to apply some download options to the **Music** folder:

-  Right-click the folder, and select **Apply download options...**

In the new window, click the **'OK'** button. The options are applied to *everything* in the **Music folder**. A pen icon appears above the folder to remind you of this.

.. image:: screenshots/example15.png
  :alt: Download options applied to the Music folder

Now, suppose you want to add a *different* set of download options, but only for the **Village People** channel.

-  Right-click the channel, and select **Apply download options...**
-  In the new window, click the **'OK'** button

The previous set of download options still applies to everything in the **Music** folder, *except* the **Village People** channel.

.. image:: screenshots/example16.png
  :alt: Download options applied to the Village People channel

6.13 Custom downloads
---------------------

By default, **Tartube** downloads videos as quickly as possible using each video's original address (URL). 

A **Custom download** enables you to modify this behaviour, if desired. It's important to note that a custom download behaves exactly like a regular download until you specify the new behaviour.

-  Click **Edit > System preferences... > Operations > Custom**
-  Select one or more of the three options to enable them
-  To start the custom download, click **Operations > Custom download all**

6.13.1 Independent downloads
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, **Tartube** instructs the underlying **youtube-dl** software to download from a channel or a playlist; it doesn't actually supply a list of videos in each channel/playlist. **youtube-dl** is perfectly capable of working out that information for itself.

If you need to download videos directly, for any reason, you can:

- Firstly, fetch the list of videos, for example by clicking **Operations > Check all** 
- Click **Edit > System preferences... > Operations > Custom** 
- Click **In custom downloads, download each video independently of its channel or playlist** to select it
- You can now start the custom download

6.13.2 Diverting to HookTube/Invidious
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If **Tartube** can't download a video from YouTube, it's sometimes possible to obtain it from an alternative website instead.

- Click **Edit > System preferences... > Operations > Custom** 
- Click **In custom downloads, obtain the video from HookTube rather than YouTube** to select it
- Alternatively click **In custom downloads, obtain the video from Invidious rather than YouTube** to select it
- You can now start the custom download

HookTube/Invidious can only handle requests for videos, not whole channels or playlists. You should normally enable independent downloads as well.

6.13.3 Delays between downloads
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If a video website is complaining that you are downloading videos too quickly, it's possible to add a delay betwen downloads. The delay can be of a fixed or random duration.

- Click **Edit > System preferences... > Operations > Custom** 
- Click **In custom downloads, apply a delay after each video/channel/playlist download** to select it
- Select the maximum delay
- If you also set a minimum delay, **Tartube** uses a random value between these two numbers
- You can now start the custom download

The delay is applied after downloading a channel or a playlist. If you want to apply the delay after each video, you should enable independent downloads as well.

6.14 Watching videos
--------------------

If you've downloaded a video, you can watch it by clicking the word **Player**.

.. image:: screenshots/example17.png
  :alt: Watching a video

If you haven't downloaded the video yet, you can watch it online by clicking the word **YouTube** or **Website**. (One or the other will be visible).

If it's a YouTube video that is restricted (not available in certain regions, or without confirming your age), it's sometimes possible to watch the same video without restrictions on the **HookTube** and/or **Invidious** websites.

6.15 Filtering and finding videos
---------------------------------

Beneath the videos you'll find a toolbar. The buttons are self-explanatory, except for the one on the right.

.. image:: screenshots/example18.png
  :alt: The video catalogue toolbar

Click that button, and a second row of buttons is revealed. You can use these buttons to filter out videos, change the order in which videos are displayed, or find a video uploaded at a certain date.

.. image:: screenshots/example19.png
  :alt: The toolbar's hidden buttons revealed

- Click the **Sort by** button to sort the videos alphabetically
- Click the button again to sort the videos by date of upload
- Click the **Find date** button to select a date. If there are more videos than will fit on a single page, **Tartube** will show the page containing the videos uploaded closest to this date

You can search for videos by applying a filter. For example, you could search for videos whose name contains the word **PewDiePie**:

- In the **Filter** box, type **pewdiepie**
- The search is case-insensitive, so it doesn't matter if you type **PewDiePie** or **pewdiepie**
- Click the magnifiying glass button. All matching videos are displayed
- Click the cancel button next it to remove the filter

You can search using a *regular expression* (regex), too. These searches are also case-insensitive. For example, to find all videos whose name begins with the word "village":

- In the **Filter** box, type **\^village**
- Click the **Regex** button to select it
- Click the magnifying glass button. All matching videos are displayed
- To search using ordinary text, rather than a regex, de-select the **Regex** button

6.16 Marking videos
-------------------

You can mark videos, channels, playlists and folders that you find interesting, or which are important.

- You can **bookmark** a video
- You can **favourite** a channel, playlist or folder

Bookmarked and favourite videos shouldn't be confused with archived videos, which are protected from automatic deletion - see `6.18 Archiving videos`_.

6.16.1 Bookmarked videos
~~~~~~~~~~~~~~~~~~~~~~~~

There are several ways to bookmark a video.

- Right-click a video, and click **Video is bookmarked** to select it
- If the **Bookmarked** label is visible under the video's name, click it
- Right-click a channel, and select **Channel contents > Mark as bookmarked**. This will bookmark every video in the channel, but it won't bookmark videos that are added to the channel later
- (This can also be done with playlists and folders)

A bookmarked video appears in **Tartube**'s own **Bookmarks** folder, as well as in its usual location.

6.16.2 Favourite channels, playlists and folders
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When you mark a channel, playlist or folder as a favourite, all of its videos will also be visible in **Tartube**'s own **Favourite Videos** folder.

If new videos are later added to the channel, playlist or folder, they will automatically appear in the **Favourite Videos** folder.

(It's possible to mark or unmark an individual video as a favourite, but it's better to use bookmarking for that.)

- Right-click a channel, and select **Channel contents > Mark as favourite**
- Right-click a playlist, and select **Playlist contents > Mark as favourite**
- Right-click a folder, and select **Folder contents > All contents > Mark as favourite**
- If you just want to mark a folder's videos as favourite, and not any channels or playlists it contains, select **Folder contents > Just folder videos > Mark as favourite**

6.17 Combining channels, playlists and folders
----------------------------------------------

**Tartube** can download videos from several channels and/or playlists into a single directory (folder) on your computer's hard drive. There are three situations in which this might be useful:

- A channel has several playlists. You have added both the channel and its playlists to **Tartube**'s database, but you don't want to download duplicate videos
- A creator releases their videos on **BitChute** as well as on **YouTube**. You have added both channels, but you don't want to download duplicate videos
- You don't care about keeping videos in separate directories/folders on your filesystem. You just want to download all videos to one place

6.17.1 Combining one channel and many playlists
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A creator might have a single channel, and several playlists. The playlists contain videos from that channel (but not necessarily *every* video).

You can add the channel and its playlists in the normal way but, if you do, **Tartube** will download many videos twice.

The solution is to tell **Tartube** to store all the videos from the channel and its playlists in a single location. In that way, you can still see a list of videos in each playlist, but duplicate videos are not actually downloaded to your filesystem.

- Click **Media > Add channel**..., and then enter the channel's details
- Click **Media > Add playlist**... for each playlist
- Now, right-click on each playlist in turn and select **Playlist actions > Set download destination...**
- In the dialogue window, click **Choose a different directory/folder**, select the name of the channel, then click the **OK button**

6.17.2 Combining channels from different websites
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A creator might release their videos on **YouTube**, but also on a site like **BitChute**. Sometimes they will only release a particular video on **BitChute**.

You can add both channels in the normal way but, if you do, **Tartube** will download many videos twice.

The solution is to tell **Tartube** to store videos from both channels in a single location. In that way, you can still see a list of videos in each channel, but duplicate videos are not actually downloaded to your filesystem.

- Click **Media > Add channel**..., and then enter the **YouTube** channel's details
- Click **Media > Add channel**..., and then enter the **BitChute** channel's details
- Right-click the **BitChute** channel and select **Channel actions > Set download destination...**
- In the dialogue window, click **Choose a different directory/folder**, select the name of the **YouTube** channel, then click the **OK button**

It doesn't matter which of the two channels you use as the download destination. There is also no limit to the number of parallel channels, so if a creator uploads videos to a dozen different websites, you can add them all.

6.17.3 Download all videos to a single folder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you don't care about keeping videos in separate directories/folders on your filesystem, you can download *all* videos into the **Unsorted videos** folder. Regardless of whether you have added one channel or a thousand, all the videos will be stored in that one place.

- Click **Edit > General download options... > Files > Filesystem**
- Click the **Download all videos into this folder** button to select it
- In the combo next to it, select **Unsorted Videos**

Alternatively, you could select **Temporary Videos**. If you do, videos will be deleted when you shut down **Tartube** (and will not be re-downloaded in the future).

6.18 Archiving videos
---------------------

You can tell **Tartube** to automatically delete videos after some period of time. This is useful if you don't have an infinitely large hard drive.

- Click **Edit > System preferences... > Filesystem > Video Deletion** 
- Click the **Automatically delete downloaded videos after this many days** button to select it
- If you want to, change the number of days from 30 to some other value

If you want to protect your favourite videos from being deleted automatically, you can *archive* them. Only videos that have actually been downloaded can be archived.

- Right-click a video, and select **Video is archived**

You can also archive all the videos in a channel, playlist or folder. 

- For example, right-click a folder and select **Channel contents > Mark videos as archived**
- This action applies to *all* videos that are *currently* in the folder, including the contents of any channels and playlists in that folder
- It doesn't apply to any videos you might download in the future

6.19 Managing databases
-----------------------

**Tartube** downloads all of its videos into a single directory (folder) - the **Tartube data directory**. The contents of this directory comprise the **Tartube database**.

*You should not use this directory (folder) for any other purpose*. 

**Tartube** stores important files here, some of which are invisible (by default). Don't let other applications store their files here, too.

*You can modify the contents of the directory yourself, if you want, but don't do it while **Tartube** is running.* 

It's fine to add new videos to the database, or to remove them. Just be careful that you don't delete any sub-directories (folders), including those which are hidden, and don't modify the **Tartube** database file, **tartube.db**.

6.19.1 Importing videos from other applications
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Tartube** is a GUI front-end for `youtube-dl <https://youtube-dl.org/>`__, but it is not the only one. If you've downloaded videos using another application, this is how to add them to **Tartube**'s database.

- In **Tartube**'s main window, add each channel and playlist in the normal way
- When you're ready, click the **Check all** button. This adds a list of videos to **Tartube**'s database, without actually downloading the videos themselves
- Copy the video files into **Tartube**'s data directory (folder). For example, copy all your **PewDiePie** videos into **../tartube-data/downloads/PewDiePie**
- In the **Tartube** menu, click **Operations > Refresh database**. **Tartube** will search for video files, and try to match them with the contents of its database
- The whole process might some time, so be patient

6.19.2 Multiple databases
~~~~~~~~~~~~~~~~~~~~~~~~~

**Tartube** can only use one database at a time, but you can create as many as you want.

For example, if you've just bought an external hard drive, you can create a new database on that hard drive.

- In the main menu, click **File > Database preferences...**
- In the new window, click the **Change** button
- Another new window appears. Use it to create a directory (folder) on your external hard drive

**Tartube** remembers the location of the databases it has loaded. To switch back to your original database:

- In the main menu, click **File > Database preferences...**
- In the list, click the path to the original database to select it
- Click the **Switch** button

6.19.3 Multiple Tartubes
~~~~~~~~~~~~~~~~~~~~~~~~

**Tartube** can't load more than one database, but you can run as many instances of **Tartube** as you want.

If you have added three databases to the list, and if you have three **Tartube** windows open at the same time, then by default each window will be using a different database.

By default, the databases are loaded in the order they appear in the list.

6.19.4 Exporting/importing the database
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

6.20 Converting to audio
------------------------

**Tartube** can automatically extract the audio from its downloaded videos, if that's what you want.

The first step is to make sure that either FFmpeg or AVconv is installed on your system - see `6.4 Setting the location of FFmpeg / AVconv`_.

The remaining steps are simple:

- In **Tartube**'s main window, click **Edit > General download options...**

In the new window, if the **Sound only** tab is visible, do this:

- Click the **Sound Only** tab
- Select the checkbox **Download each video, extract the sound, and then discard the original videos**
- In the boxes below, select an audio format and an audio quality
- Click the **OK** button at the bottom of the window to apply your changes

If the **Post-process** tab is visible, do this:

- Click on the **Post-process** tab
- Select the checkbox **Post-process video files to convert them to audio-only files** 
- If you want, click the button **Keep video file after post-processing it** to select it
- In the box labelled **Audio format of the post-processed file**, specify what type of audio file you want - **.mp3**, **.wav**, etc 
- Click the **OK** button at the bottom of the window to apply your changes

7. Frequently-Asked Questions
=============================

**Q: I can't install Tartube / I can't run Tartube / Tartube doesn't work properly / Tartube keeps crashing!**

A: Please report any problems to the authors at our `Github page <https://github.com/axcore/tartube/issues>`__ 

A: Crashes are usually caused by the Gtk graphics library. Depending on the version of the library installed on your system, **Tartube** may restrict some minor cosmetic features, or not, in an effort to avoid such crashes.

If crashes are a problem, you can force **Tartube** to restrict those cosmetic features, regardless of your current Gtk library.

- Click **Edit > System preferences... > General > Modules**
- Click **Assume that Gtk is broken, and disable some minor features** to select it

**Q: When I try to download videos, nothing happens! In the Errors/Warnings tab, I can see "Download did not start"!**

A: See `6.3 Setting youtube-dl's location`_

**Q: I can't download my favourite video!**

A: Make sure **youtube-dl** is updated; see `6.2 Check youtube-dl is updated`_

A: Before submitting a `bug report <https://github.com/axcore/tartube/issues>`__, find out whether **Tartube** is responsible for the problem, or not. You can do this by opening a terminal window, and typing something like this:

**youtube-dl <url>**

...where **\<url\>** is the address of the video. If the video downloads successfully, then it's a **Tartube** problem that you can report. If it doesn't download, you should submit a bug report to the authors of `youtube-dl <https://github.com/ytdl-org/youtube-dl/issues>`__ instead.

Because most people don't like typing, **Tartube** offers a shortcut.

- Click **Operations > Test youtube-dl**, or right-click a video, and select **Downloads > Test system command**
- In the dialogue window, enter the address (URL) of the video
- You can add more **youtube-dl** download options, if you want. See `here <https://github.com/ytdl-org/youtube-dl/>`__ for a complete list of them
- Click the **OK** button to close the window and begin the test
- Click the **Output** Tab to watch the test as it progresses
- When the test is finished, a temporary directory (folder) opens, containing anything that **youtube-dl** was able to download

**Q: After I downloaded some videos, Tartube crashed, and now all my videos are missing!**

A: **Tartube** creates a backup copy of its database, before trying to save a new copy. In the unlikely event of a failure, you can replace the broken database file with the backup file. 

- Open the data directory (folder). If you're not sure where to find **Tartube**'s data directory , you can click **Edit > System preferences... > Filesystem > Database**
- Make sure **Tartube** is not running. The **Tartube** window is sometimes minimised, and sometimes only visible in the system tray. A good way to make sure is to run **Tartube**, then close it by clicking **File > Quit**
- In the data directory is the broken **tartube.db** file. You should rename to something else, in case you want to examine it later
- In the same directory, you might be able to see a directory called **.backups**
- If **.backups** is not visible, then it is hidden. (On many Linux/BSD system, pressing **CTRL + H** will reveal hidden folders)
- Inside the **.backups** directory, you'll find some backup copies of the database file
- Choose the most recent one, copy it into the directory above, and rename the copy as **tartube.db**, replacing the old broken file
- Restart **Tartube**
- Click the **Check All** button. **Tartube** will update its database with any videos you've downloaded that were not in the backup database file

**Tartube** can make more frequent backups of your database file, if you want. See the options in **Edit > System preferences... > Filesystem > Backups**.

Note that **Tartube** does not create backup copies of the videos you've downloaded. That is your responsibility!

**Q: I clicked the 'Check all' button, but the operation takes so long! It only found two new videos!**

A: By default, the underlying **youtube-dl** software checks an entire channel, even if it contains hundreds of videos. 

You can drastically reduce the time this takes by telling **Tartube** to stop checking/downloading videos, if it receives (for example) notifications for three videos it has already checked/downloaded.

This works well on sites like YouTube, which send information about videos in the order they were uploaded, newest first. We can't guarantee it will work on every site.

- Click **Edit > System preferences... > Operations > Time-saving**
- Select the checkbox **Stop checking/downloading a channel/playlist when it starts sending vidoes we already have**
- In the **Stop after this many videos (when checking)** box, enter the value 3
- In the **Stop after this many videos (when downloading)** box, enter the value 3
- Click **OK** to close the window

**Q: I clicked the 'Download all' button, but the operation takes so long! It only downloaded two new videos!**

A: **youtube-dl** can create an archive file especially for the purpose of speeding up downloads, when some of your channels and playlists have no new videos to download, but when others do. 

To enable this functionality, click **Edit > System preferences... > youtube-dl > Allow youtube-dl to create its own archive**. The functionality is enabled by default.

**Q: Tartube always downloads its channels and playlists into ../tartube-data/downloads. Why doesn't it just download directly into ../tartube-data?**

A: This was implemented in v1.4.0. If you installed an earlier version of **Tartube**, you don't need to take any action; **Tartube** can cope with both the old and new file structures.

If you installed an earlier version of **Tartube**, and if you want to move your channels and playlists out of **../tartube-data/downloads**, this is how to do it:

- Open the data directory (folder). If you're not sure where to find **Tartube**'s data directory, you can click **Edit > System preferences... > Filesystem > Database**.
- Make sure **Tartube** is not running. The **Tartube** window is sometimes minimised, and sometimes only visible in the system tray. A good way to make sure is to run **Tartube**, then close it by clicking **File > Quit**
- Now open the **downloads** directory
- Move everything inside that directory into the directory above, e.g. move everything from **../tartube-data/downloads** into **../tartube-data**
- Delete the empty **downloads** directory
- You can now restart **Tartube**

**Q: I want to convert the video files to audio files!**

A: See `6.20 Converting to audio`_

**Q: The main window is full of folders I never use! I can't see my own channels, playlists and folders!**

A: Right-click the folders you don't want to see, and select **Folder actions > Hide folder**. To reverse this step, in the main menu click **Media > Show hidden folders**

A: In the main menu, click **Edit > System preferences... > Windows > Main window > Show smaller icons in the Video Index** to select it

A: If you have many channels and playlists, create a folder, and then drag-and-drop the channels/playlists into it

**Q: I want to see all the videos on a single page, not spread over several pages!**

A: At the bottom of the **Tartube** window, set the page size to zero, and press **ENTER**.

**Q: The toolbar is too small! There isn't enough room for all the buttons!**

A: Click **Edit > System preferences... > Windows > Main window > Don't show labels in the toolbar**.

MS Windows users can already see a toolbar without labels.

**Q: Why is the Windows installer so big?**

**Tartube** is a Linux application. The installer for MS Windows contains not just **Tartube** itself, but a copy of Python and a whole bunch of essential graphics libraries, all of them ported to MS Windows.

If you're at all suspicious that such a small application uses such a large installer, you are invited to examine the installed files for yourself: 

**C:\\Users\\YOURNAME\\AppData\\Local\\Tartube**

(You might need to enable hidden folders; this can be done from the Control Panel.)

Everything is copied into this single folder. The installer doesn't modify the Windows registry, nor does it copy files anywhere else (other than to the desktop and the Start Menu). 

The NSIS scripts used to create the installers can be found here:

**C:\\Users\\YOURNAME\\AppData\\Local\\Tartube\\msys64\\home\\user\\tartube\\nsis**

The scripts contain full instructions, so you should be able to create your own installer, and compare it with the official one.

8. Contributing
===============

-  Report a bug: Use the Github
   `issues <https://github.com/axcore/tartube/issues>`__ page

9. Authors
==========

See the `AUTHORS <AUTHORS>`__ file.

10. License
===========

**Tartube** is licensed under the `GNU General Public License v3.0 <https://www.gnu.org/licenses/gpl-3.0.en.html>`__.

✨🍰✨
