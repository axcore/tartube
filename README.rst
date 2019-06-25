Tartube
=======

**Tartube** is a GUI front-end for `youtube-dl <https://youtube-dl.org/>`__,
partly based on
`youtube-dl-gui <https://mrs0m30n3.github.io/youtube-dl-gui/>`__ and
written in Python 3 / Gtk 3.

It runs on MS Windows, Linux and BSD. It probably works on MacOS, but the
authors have not been able to confirm this.

**Tartube** is **alpha software**. It might not behave in the way you're
expecting. If you find this frustrating, 
`report the problem to the authors <https://github.com/axcore/tartube/issues>`__.

Downloads
---------

-  `MS Windows installer <https://sourceforge.net/projects/tartube/files/v0.3.0/install-tartube-0.3.0.exe/download>`__ from sourceforge.io
-  `Source code <https://sourceforge.net/projects/tartube/files/v0.3.0/tartube_v0.3.0.tar.gz/download>`__ from sourceforge.io
-  `Source code and support <https://github.com/axcore/tarbue>`__ from github

Why should I use Tartube?
-------------------------

-  You can download individual videos, and even whole channels and playlists,
   from YouTube and hundreds of other sites (see
   `here <https://ytdl-org.github.io/youtube-dl/supportedsites.html>`__
   for a full list)
-  You can fetch information about those videos, channels and playlists,
   without actually downloading anything
-  **Tartube** will organise your videos into convenient folders
-  Certain popular websites manipulate search results, repeatedly unsubscribe
   people from their favourite channels and/or deliberately conceal videos that
   they don't like. **Tartube** won't do any of those things
-  **Tartube** can, in some circumstances, see videos that are region-blocked
   and/or age-restricted
   
Screenshots
-----------

.. image:: screenshots/tartube.png
  :alt: Tartube screenshot

Installation
------------

MS Windows users should use the installer available at the Tartube website. The installer contains everything you need to run Tartube, including Python, the Gtk libraries and even a copy of youtube-dl. You must be using Windows Vista or above; the installer will not work on Windows XP.

Tartube should run on MacOS, but the authors don't have access a MacOS system.
If you are a MacOS user, open an issue at our Github page, and we'll work out
the installation procedure together.

Linux/BSD users can use any of the following installation methods.

Linux/BSD Installation requirements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  `youtube-dl <https://youtube-dl.org/>`__ must already be installed
-  `Python 3 <https://www.python.org/downloads>`__
-  `Gtk 3 <https://python-gtk-3-tutorial.readthedocs.io/en/latest/>`__

Optional dependencies
~~~~~~~~~~~~~~~~~~~~~

-  `Python validators module <https://pypi.org/project/validators/>`__
   optional, but recommended
-  `Python moviepy module <https://pypi.org/project/moviepy/>`__ 
-  `Ffmpeg <https://ffmpeg.org/>`__ 

Install using PyPI
~~~~~~~~~~~~~~~~~~

1. Run ``pip3 install tartube``

Install from source
~~~~~~~~~~~~~~~~~~~

1. Download & extract the source
2. Change directory into the **Tartube** directory
3. Run ``python3 setup.py install``

Run without installing
~~~~~~~~~~~~~~~~~~~~~~

1. Download & extract the source
2. Change directory into the **Tartube** directory
3. Run 'python3 tartube.py'

Getting started
---------------

1. Check youtube-dl is updated
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Assuming that **Tartube** is installed and running correctly, then you should
start by checking that **youtube-dl** is also installed and running correctly.

.. image:: screenshots/example1.png
  :alt: Updating youtube-dl

-  Click **Operations > Update youtube-dl**

2. Setting youtube-dl's location
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the update operation fails, you should try modifying **Tartube**'s settings. 

There are several locations on your filesystem where youtube-dl might have been
installed.

.. image:: screenshots/example2.png
  :alt: Updating youtube-dl

-  Click **Edit > System preferences...**
-  Click the **youtube-dl** tab
-  Try changing the setting
   **'Actual path to use during download/update/refresh operations'**
-  Try changing the setting **'Shell command for update operations'**
-  Try the update operation again

3. Choose where to save videos
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before continuing, you should also choose where Tartube saves its videos.

-  Click **Edit > System preferences...**
-  Click the **General** tab
-  Check the location of the **Tartube data directory**
-  If you want to change it, click the **Change** button

4. Introducing system folders
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On the left side of the **Tartube** window is a list of folders. You can store
videos, channels and playlists inside these folders. You can even store folders
inside of other folders.

**Tartube** saves videos on your filesystem using exactly the same structure.

.. image:: screenshots/example3.png
  :alt: Tartube's system folders
  
When you start **Tartube**, there are five folders already visible. You can't
remove any of these folders (but you can hide them, if you want).

Videos saved to the **Temporary Videos** folder are deleted when **Tartube**
shuts down.

5. Adding videos
~~~~~~~~~~~~~~~~

You can add individual videos by clicking the **'Videos'** button near the top
of the window. A popup window will appear.

.. image:: screenshots/example4.png
  :alt: Adding videos

Copy and paste the video's URL into the popup window. You can copy and paste as
many URLs as you like.

When you're finished, click the **OK** button. 

Finally, click on the **Unsorted Videos** folder to see the videos you've
added.

.. image:: screenshots/example5.png
  :alt: Your first added video

6. Adding channels and playlists
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can also add a whole channel by clicking the **'Channel'** button or a
whole playlist by clicking the **'Playlist'** button. 

**Tartube** will download all of the videos in the channel or playlist.

.. image:: screenshots/example6.png
  :alt: Adding a channel

Copy and paste the channel's URL into the popup window. You should also give
the channel a name. The channel's name is usually the name used on the website
(but you can choose any name you like).

7. Adding folders
~~~~~~~~~~~~~~~~~

The left-hand side of the window will quickly still filling up. It's a good
idea to create some folders, and to store your channels/playlists inside those
folders.

Click the **'Folder'** button near the top of the window,  and create a folder
called **Comedy**. 

.. image:: screenshots/example7.png
  :alt: Adding a folder

Then repeat that process to create a folder called **Music**. You can then
drag-and-drop your channels and playlists into those folders.

.. image:: screenshots/example8.png
  :alt: A channel inside a folder

8. Things you can do
~~~~~~~~~~~~~~~~~~~~

Once you've finished adding videos, channels, playlists and folders, there are
basically four things **Tartube** can do:

-  **'Check'** - Fetch information about videos, but don't download them
-  **'Download'** - Actually download the videos. If you have disabled
   downloads for a particular item, **Tartube** will just fetch information
   about it instead
-  **'Update'** - Updates youtube-dl, as described above
-  **'Refresh'** - Examines your filesystem. If you have manually copied any
   videos into **Tartube**'s data directory, those videos are added to
   **Tartube**'s database

.. image:: screenshots/example9.png
  :alt: The Check and Download buttons
  
To **Check** or **Download** videos, channels and playlists, use the buttons
near the top of the window. To **Refresh** **Tartube**'s database, use the
menu.

**Protip:** Do an **'Update'** operation before you do a **'Check'** or
**'Download'** operation

**Protip:** Do a **'Check'** operation before you do **'Refresh'** operation

9. General download options
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**youtube-dl** offers a large number of download options. This is how to set
them.

.. image:: screenshots/example10.png
  :alt: Opening the download options window
  
-  Click **Edit > General download options...**

A new window opens. Any changes you make in this window aren't actually applied
until you click the **'Apply'** or **'OK'** buttons.

10. Other download options
~~~~~~~~~~~~~~~~~~~~~~~~~~

Those are the *default* download options. If you want to apply a *different*
set of download options to a particular channel or particular playlist, you can
do so.

At the moment, the general download options apply to *all* the videos,
channels, playlists and folders you've added.

.. image:: screenshots/example11.png
  :alt: The window with only general download options applied
  
Now, suppose you want to apply some download options to the **Music** folder:

-  Right-click the folder, and select **Apply download options...**

In the new window, click the **'OK'** button. The options are applied to
*everything* in the **Music folder**. A pen icon appears above the folder to
remind you of this.

.. image:: screenshots/example12.png
  :alt: Download options applied to the Music folder

Now, suppose you want to add a *different* set of download options, but only
for the **Village People** channel.

-  Right-click the channel, and select **Apply download options...**
-  In the new window, click the **'OK'** button

The previous set of download options still applies to everything in the
**Music** folder, *except* the **Village People** channel.

.. image:: screenshots/example13.png
  :alt: Download options applied to the Village People channel

11. Favourite videos
~~~~~~~~~~~~~~~~~~~~

You can mark channels, playlists and even whole folders as favourites.

-  Right-click the channel, playlist or folder, and select
   **Mark videos > Favourite**

When you do that, any videos you download will appear in the 
**Favourite Videos** folder (as well as in their normal location).

12. Watching videos
~~~~~~~~~~~~~~~~~~~

If you've downloaded a video, you can watch it by clicking the word **Player**.

.. image:: screenshots/example14.png
  :alt: Watching a video

If you haven't downloaded the video yet, you can watch it online by clicking
the word **YouTube** or **Website**. (One or the other will be visible).

If it's a YouTube video that is restricted (not available in certain regions,
or without confirming your age), it's often possible to watch the same video
without restrictions on the **HookTube** website.

Frequently-Asked Questions
--------------------------

**Q: I can't install Tartube!**

A: I have little experience of writing in Python and I'm still working it out
for myself. Contact me on the `Github
issues <https://github.com/axcore/tartube/issues>`__ page if you can do
better than me.

**Q: I can't run Tartube!**

A: See above.

**Q: Tartube doesn't work properly!**

A: See above.

**Q: Tartube keeps crashing!**

A: Most of the crashes are fixed now. Are you using the most recent version?

Future plans
------------

-  Fix the endless crashes **DONE**
-  Support for multiple databases (so you can store videos on two external hard
   drives at the same time)
-  Add download scheduling
-  Add video archiving
-  Allow selection of multiple videos in the catalogue, so the same action can
   be applied to all of them at the same time
-  Tie channels and playlists together, so that they won't both download the
   same video
-  Add tooltips for everything
-  Add more youtube-dl options

Known issues
------------

-  Tartube crashes continuously and often **FIXED**
-  Alphabetic sorting of channels/playlists/folders doesn't always work as
   intended, due to an unresolved Gtk issue
-  Channels/playlists/folder selection does not always work as intended, due to
   an unresolved Gtk issue
-  Users can type in comboboxes, but this should not be possible

Contributing
------------

-  Report a bug: Use the Github
   `issues <https://github.com/axcore/tartube/issues>`__ page

Authors
-------

See the `AUTHORS <AUTHORS>`__ file.

License
-------

Tartube is licensed under the `GNU General Public License
v3.0 <https://www.gnu.org/licenses/gpl-3.0.en.html>`__.

✨🍰✨
