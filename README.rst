Tartube
=======

Tartube is a GUI front-end for `youtube-dl <https://youtube-dl.org/>`__,
partly based on
`youtube-dl-gui <https://mrs0m30n3.github.io/youtube-dl-gui/>`__ and
written in Python 3 / Gtk 3.

Tartube is **alpha software**. It crashes a lot. If you find this
frustrating, find a solution and then `send it to
me <https://github.com/axcore/tartube/issues>`__.

Screenshots
-----------

.. image:: screenshots/tartube.png
  :alt: Tartube screenshot

Why should I use Tartube?
-------------------------

-  You can download individual videos, and even whole channels and
   playlists, from hundreds of different websites
-  You can fetch information about those videos, channels and playlists,
   without actually downloading anything
-  Tartube will organise your videos into convenient folders
-  Certain popular video websites manipulate search results, repeatedly
   unsubscribe people from their favourite channels and/or deliberately
   conceal videos which challenge their preferred political views. Tartube won't do any of those things
-  Tartube can, in some circumstances, see videos that are
   region-blocked and age-restricted

Requirements
------------

-  A working installation of `youtube-dl <https://youtube-dl.org/>`__
-  `Python 3+ <https://www.python.org/downloads>`__
-  `Gtk 3+ <https://python-gtk-3-tutorial.readthedocs.io/en/latest/>`__
-  `Python validators module <https://pypi.org/project/validators/>`__
   optional, but recommended
-  `Python moviepy module <https://pypi.org/project/moviepy/>`__
   optional

Downloads
---------

-  `Source <http://tartube.sourceforge.io/>`__ from sourceforge.io
-  `Source <https://github.com/axcore/tarbue>`__ from github

Installation
------------

Install from source
~~~~~~~~~~~~~~~~~~~

1. Download & extract the source
2. Change directory into the Tartube directory
3. Run ``python3 setup.py install``

Install using PyPI
~~~~~~~~~~~~~~~~~~

1. Run ``pip install tartube``

Install using MS Windows Installer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There is no installer for MS Windows yet.

Run without installing
~~~~~~~~~~~~~~~~~~~~~~

1. Download & extract the source
2. Change directory into the Tartube directory
3. Run 'python3 tartube.py'

Frequently-Asked Questions
--------------------------

**Q: I can't install Tartube!**

A: I have no experience of writing in Python and I'm still working it
out for myself. Contact me on the `Github
issues <https://github.com/axcore/tartube/issues>`__ page if you can do
better than me.

**Q: I can't run Tartube!**

A: See above.

**Q: Tartube doesn't work properly!**

A: See above.

**Q: Tartube keeps crashing!**

A: See above.

**Q: How do I use Tartube?**

A: Assuming that Tartube is installed and running correctly, then you
should start by checking that youtube-dl is also installed and running
correctly.

-  Click **Operations > Update youtube-dl**

There are several locations on your filesystem where youtube-dl might
have been installed. If the update operation fails, you should try
modifying Tartube's settings.

-  Click **Edit > System preferences...**
-  Click the **youtube-dl** tab
-  Try changing the setting **'Actual path to use during
   download/update/refresh operations'**
-  Try changing the setting **'Shell command for update operations'**
-  Try the update operation again

On the left side of the Tartube window is a list of folders. You can
store videos, channels and playlists inside these folders. You can even
store folders inside of other folders.

Tartube saves videos on your filesystem using exactly the same
structure.

When you start Tartube, there are five folders already visible. You
can't remove any of these folders (but you can hide them, if you want).

Videos saved to the 'Temporary Videos' folder are deleted when Tartube
shuts down.

Once you've finished adding videos, channels, playlists and folders,
there are four things Tartube can do:

-  **'Check'** - Fetch information about videos, but don't download them
-  **'Download'** - Actually download the videos. If you have disabled
   downloads for a particular item, Tartube will just fetch information
   about it instead
-  **'Update'** - Updates youtube-dl, as described above
-  **'Refresh'** - Examines your filesystem. If you have manually copied
   any videos into Tartube's data directory, those videos are added to
   Tartube's database

**Protip:** Do an **'Update'** operation before you do a **'Check'** or
**'Download'** operation

**Protip:** Do a **'Check'** operation before you do **'Refresh'**
operation

youtube-dl offers a large number of download options. This is how to set
them.

-  Click **Edit > General download options...**

Any changes you make in the new window aren't actually applied until you
click the **'Apply'** or **'OK'** buttons.

Those are the *default* download options. If you want to apply a
*different* set of download options to a particular channel or
particular playlist, you can do so.

For example, suppose you have added these folders and channels:

::

        Comedy folder
            CollegeHumor channel
            PewDiePie channel
        Politics folder
            Liberal folder
                The Young Turks channel
            Conservative folder
                Joe Rogan channel
                Mark Dice channel

The general download options apply to all of these channels. Now,
suppose you apply some download options to the Politics folder:

-  Right-click the folder, and select **Apply download options...**

Tartube's database now looks something like this:

::

        Comedy folder
            CollegeHumor channel
            PewDiePie channel
        ++Politics folder
            Liberal folder
                The Young Turks channel
            Conservative folder
                Joe Rogan channel
                Mark Dice channel

The new download options (marked ++) apply to *everything* inside the
Politics folder - The Young Turks, Joe Rogan and Mark Dice.

Now, suppose you add another set of download options (marked @@) to the
Conservative folder:

::

        Comedy folder
            CollegeHumor channel
            PewDiePie channel
        **Politics folder
            Liberal folder
                The Young Turks channel
            @@Conservative folder
                Joe Rogan channel
                Mark Dice channel

These new download options only apply to Joe Rogan and Mark Dice. They
don't apply to The Young Turks, which are still using the *previous* set
of download options. They don't apply to CollegeHumor or PewDiePie,
which are still using the *default* download options.

Future plans
------------

-  Fix the endless crashes, somehow
-  Support for multiple databases (so you can store videos on two
   external hard drives at the same time)
-  Add download scheduling
-  Add video archiving
-  Allow selection of multiple videos in the catalogue, so the same
   action can be applied to all of them at the same time
-  Tie channels and playlists together, so that they won't both download
   the same video
-  Add tooltips for everything
-  Add more youtube-dl options

Known issues
------------

-  Tartube crashes continuously and often
-  Alphabetic sorting of channels/playlists/folders doesn't always work
   as intended, due to an unresolved Gtk issue
-  Channels/playlists/folder selection does not always work as intended,
   due to an unresolved Gtk issue
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
