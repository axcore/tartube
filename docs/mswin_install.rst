Tartube installation problems on MS Windows
===========================================

Some users on MS Windows report that they can't run Tartube at all. There are three possible fixes.

Fix #1
~~~~~~

Wait for v1.2 of Tartube, which should fix the problem.

Fix #2
~~~~~~

Find the **tartube_mswin.sh** file, and modify it.

If you used the MS Windows installer, it should be installed in 

**C:\\Users\\YOURNAME\\AppData\\Local\\Tartube\\msys64\\home\\user\\tartube**

(You may have to `make hidden folders visible <https://support.microsoft.com/en-us/help/14201/windows-show-hidden-files>`__ to see the parent folder.)

Open the file in a text editor, and replace this line

**cd tartube**

with this line

**cd /home/user/tartube/tartube**

Save the file. You may now be able to run Tartube from the Windows Start Menu, or from the desktop shortcut.

Fix #3
~~~~~~

Perform a manual installation. This takes about 10-30 minutes, depending on your internet speed.

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
        
- Download the `Tartube source code <https://sourceforge.net/projects/tartube/files/v0.7.0/tartube_v0.7.0.tar.gz/download>`__ from Sourceforge
- Extract it into the folder **C:\\msys64\\home\\YOURNAME**, creating a folder called **C:\\msys64\\home\\YOURNAME\\tartube**
- Now, to run Tartube, type these commands in the MINGW64 terminal:

        **cd tartube**
        
        **python3 tartube**

