# Tartube v0.3.003 installer script for MS Windows
#
# Copyright (C) 2019 A S Lewis
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
#
#
# Build instructions:
#   These instructions describe how to create an installer for Tartube on a
#       64-bit MS Windows machine, Windows Vista or higher. For 32-bit machines
#       see the tartube_install_32bit.nsi file
#   The instructions are based on the method described in
#
#       https://bitbucket.org/sirdeniel/deploy-python-gtk3-apps-for-windows/
#
#   - If you don't have a suitable editor (Notepad is not good enough), 
#       download and install one, e.g. Notepad++ from
#
#       https://notepad-plus-plus.org/
#
#   - On an MS Windows machine, download and install NSIS from
#
#       http://nsis.sourceforge.io/Download/
#
#   - Download the 64-bit version of MSYS2. The downloadable file should look
#       something like 'msys2-x86-64-nnn.exe'
#
#       http://www.msys2.org/
#   
#   - Run the file to install MSYS2. Let it install in its default location
#   - Run the mingw64 terminal, i.e.
#
#       C:\msys64\mingw64.exe       
#
#   - We need to install various dependencies. In the terminal window, type
#       this command
#
#       pacman -Syu
#
#   - Usually, the terminal window tells you to close it. Do that, and then
#       open a new mingw64 terminal window
#   - In the new window, type these commands
#
#       pacman -Su
#       pacman -S mingw-w64-x86_64-gtk3 
#       pacman -S mingw-w64-x86_64-python3 
#       pacman -S mingw-w64-x86_64-python3-gobject
#       pacman -S mingw-w64-x86_64-python3-requests
#
#   - Optional step: you can check that the dependencies are working by typing
#       this command (if you like):
#
#       gtk3-demo       
#
#   - Now download youtube-dl. DO NOT use the installer for MS Windows; instead
#       download the source code from
#
#       https://github.com/ytdl-org/youtube-dl/
#
#   - Extract the 'youtube-dl-master' file. Changed folder into the new
#       'youtube-dl-master' folder, where you will find another folder called
#       'youtube-dl-master'
#   - Rename this inner folder as 'youtube-dl', and then copy that folder to
#
#       C:\msys64\home\YOURNAME
#
#   - Note that, throughout this guide, YOURNAME should be substituted for your
#       actual Windows username. For example, the copied folder might be
#
#       C:\msys64\home\alice\youtube-dl
#
#   - Next, in the mingw64 terminal window, type
#
#       cd youtube-dl
#       python3 setup.py install
#
#   - Now download the Tartube source code from
#
#       https://sourceforge.net/projects/tartube/
#
#   - Extract it, and copy the whole 'tartube' folder to
#
#       C:\msys64\home\YOURNAME
#
#   - Now download the deployment package from 
#
#       https://bitbucket.org/sirdeniel/deploy-python-gtk3-apps-for-windows/
#
#   - Extract it. The folder's contents should look like this
#
#       /sirdeniel-deploy-python-gtk3-apps-for-windows-xxxxxx
#           README.MD
#           /resources
#               build_dist.py
#               config.pmc
#               procmon_files.png
#               save_procmonlog.png
#               start_capture.png
#               start_procmon.bat
#               target_startin_lnk.png
#
#   - Create a new folder
#
#       C:\msys64\home\YOURNAME\procmon
#
#   - Copy everything from the extracted 'resources' folder into the new
#       'procmon' folder
#   - Move the 'build_dst.py' file from the new 'procmon' folder into the
#       parent folder, i.e.
#
#         C:\msys64\home\YOURNAME
#
#   - Download Process Monitor from the official Microsoft site. At the time of
#       writing, it can be found at
#
#       https://docs.microsoft.com/en-us/sysinternals/downloads/procmon
#
#   - Copy the file into the new 'procmon' folder
#   - In the new 'procmon' folder. run the batch file 'start_procmon.bat'
#   - Give permission for the programme to run
#   - Close the 'Process Monitor Filter' window by clicking the OK button, and
#       without making any changes
#   - In the Process Monitor window, click the magnifying glass icon (or press
#       CTRL+E) to begin monitoring
#
#   - Now run Tartube. In the mingw64 terminal window, type
#
#       cd
#       python3 ./youtube-dl/bin/youtube-dl --version
#       cd tartube
#       python3 tartube.py
#
#   - In Tartube, download any video from any supported website (e.g. from
#       YouTube)
#   - Close the Tartube window
#   - In the Process Monitor window, click the magnifying glass (or press
#       CTRL+E) to stop monitoring. Then click 'File > Save'
#   - In the dialogue window, select 'Comma-separated values (CSV)', and change
#       the file path to
#
#         C:\msys64\home\YOURNAME\Logfile.CSV
#
#   - Save the file and close Process Manager
#   - In the minwg64 terminal window, type this
#
#       cd ..
#       python3 build_dist.py
#
#   - This creates a folder called 'dist'
#   - You can now close the mingw64 terminal window
#
#   - DELETE the following folder in its entirety, and replace it with the
#       original source code (as described above)
#
#       C:\msys64\home\YOURNAME\dist\msys64\home\YOURNAME\tartube
#
#   - The youtube-dl might be missing some important files, so copy the
#       original source code into its folder, but DO NOT replace any files that
#       already exist there
#
#       C:\msys64\home\YOURNAME\dist\msys64\home\YOURNAME\youtube-dl
#
#   - Now move the following file into its parent folder:
#
#       C:\msys64\home\YOURNAME\dist\msys64\home\YOURNAME\tartube\nsis\tartube_64bit.bat
#
#   - In other words, its new location is
#
#       C:\msys64\home\YOURNAME\dist\msys64\home\YOURNAME\tartube\tartube.bat
#
#   - Now copy all of the remaining files in this folder
#
#       C:\msys64\home\YOURNAME\dist\msys64\home\YOURNAME\tartube\nsis
#
#   - ...into this folder:
#
#       C:\msys64\home\YOURNAME\dist
#
#   - The installer script (this file) is now at the following location
#
#       C:\msys64\home\YOURNAME\dist\tartube_install_64bit.nsi
#
#   - Open the file in an editor, change the version number just below (in the
#       line starting 'OutFile'), and save it
#   - Compile the installer (e.g. by right-clicking the file and selecting
#       'Compile NSIS script file')

# Header files
# -------------------------------

    !include "MUI2.nsh"
    !include "Sections.nsh"

# General
# -------------------------------

    ;Name and file
    Name "Tartube"
    OutFile "install-tartube-0.3.003-64bit.exe"

    ;Default installation folder
    InstallDir "$LOCALAPPDATA\Tartube"

    ;Get installation folder from registry if available
    InstallDirRegKey HKCU "Software\Tartube" ""

    ;Request application privileges for Windows Vista
    RequestExecutionLevel user

    ; Extra stuff here
    BrandingText " "

# Variables
# -------------------------------

###   Var StartMenuFolder

# Interface settings
# -------------------------------

    !define MUI_ABORTWARNING
    !define MUI_ICON "tartube_icon.ico"
    !define MUI_UNICON "tartube_icon.ico"
    !define MUI_HEADERIMAGE
    !define MUI_HEADERIMAGE_BITMAP "tartube_header.bmp"
    !define MUI_HEADERIMAGE_UNBITMAP "tartube_header.bmp"
    !define MUI_WELCOMEFINISHPAGE_BITMAP "tartube_wizard.bmp"

# Pages
# -------------------------------

    !insertmacro MUI_PAGE_WELCOME

    !insertmacro MUI_PAGE_LICENSE "license.txt"

    !insertmacro MUI_PAGE_DIRECTORY

    !define MUI_STARTMENUPAGE_REGISTRY_ROOT "SHCTX"
    !define MUI_STARTMENUPAGE_REGISTRY_KEY "Software\Tartube"
    !define MUI_STARTMENUPAGE_REGISTRY_VALUENAME "Startmenu"
    !define MUI_STARTMENUPAGE_DEFAULTFOLDER "Tartube"

    !insertmacro MUI_PAGE_INSTFILES

    !define MUI_FINISHPAGE_RUN "$INSTDIR\msys64\home\user\tartube\tartube.bat"
    !define MUI_FINISHPAGE_RUN_TEXT "Run Tartube"
    !define MUI_FINISHPAGE_RUN_NOTCHECKED
    !define MUI_FINISHPAGE_LINK "Visit the Tartube website for the latest news \
        and support"
    !define MUI_FINISHPAGE_LINK_LOCATION "http://tartube.sourceforge.io/"
    !insertmacro MUI_PAGE_FINISH

    !insertmacro MUI_UNPAGE_CONFIRM
    !insertmacro MUI_UNPAGE_INSTFILES

# Languages
# -------------------------------

    !insertmacro MUI_LANGUAGE "English"

# Installer sections
# -------------------------------

Section "Tartube" SecClient

    SectionIn RO
    SetOutPath "$INSTDIR"

    File "tartube_icon.ico"
    File /r msys64

    SetOutPath "$INSTDIR\msys64\home\user\tartube"

    # Start Menu
    CreateShortCut "$SMPROGRAMS\Tartube.lnk" \
        "$INSTDIR\msys64\home\user\tartube\tartube.bat" \
        "" \
        "$INSTDIR\tartube_icon.ico"

    # Desktop icon
    CreateShortcut "$DESKTOP\Tartube.lnk" \
        "$INSTDIR\msys64\home\user\tartube\tartube.bat" \
        "" \
        "$INSTDIR\tartube_icon.ico"

    # Store installation folder
    WriteRegStr HKCU "Software\Tartube" "" $INSTDIR

    # Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"

SectionEnd

# Uninstaller sections
# -------------------------------

Section "Uninstall"

    Delete "$INSTDIR\Uninstall.exe"

    RMDir "$INSTDIR"

    DeleteRegKey /ifempty HKCU "Software\Tartube"

SectionEnd
