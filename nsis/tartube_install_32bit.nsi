# Tartube v1.2.008 installer script for MS Windows
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
#   - These instructions describe how to create an installer for Tartube on a
#       32-bit MS Windows machine, Windows Vista or higher. For 64-bit machines
#       see the tartube_install_64bit.nsi file
#
#   - Download and install NSIS from
#
#       http://nsis.sourceforge.io/Download/
#
#   - Download the 32-bit version of MSYS2. The downloadable file should look
#       something like 'msys2-i686-yyyymmdd.exe'
#
#       http://www.msys2.org/
#
#   - Run the file to install MSYS2. We suggest that you create a directory
#       called C:\testme, and then let MSYS2 install itself inside that
#       directory, i.e. C:\testme\msys32
#   - Run the mingw32 terminal, i.e.
#
#       C:\testme\msys32\mingw32.exe
#
#   - We need to install various dependencies. In the terminal window, type
#       this command
#
#       pacman -Syu
#
#   - Usually, the terminal window tells you to close it. Do that, and then
#       open a new mingw32 terminal window
#   - In the new window, type these commands
#
#       pacman -Su
#       pacman -S mingw-w64-i686-python3
#       pacman -S mingw-w64-i686-python3-pip
#       pacman -S mingw-w64-i686-python3-gobject
#       pacman -S mingw-w64-i686-python3-requests
#       pacman -S mingw-w64-i686-gtk3
#       pacman -S mingw-w64-i686-gsettings-desktop-schemas
#
#   - Optional step: you can check that the dependencies are working by typing
#       this command (if you like):
#
#       gtk3-demo
#
#   - Now download the Tartube source code from
#
#       https://sourceforge.net/projects/tartube/
#
#   - Extract it, and copy the whole 'tartube' folder to
#
#       C:\testme\msys32\home\YOURNAME
#
#   - Note that, throughout this guide, YOURNAME should be substituted for your
#       actual Windows username. For example, the copied folder might be
#
#       C:\testme\msys32\home\alice\tartube
#
#   - The C:\testme folder now contains about 2GB of data. If you like, you can
#       use all of it (which would create an installer of about 600MB). In most
#       cases, though, you will probably want to remove everything that's not
#       necessary. This table shows which files and folders are in the official
#       Tartube installer (which is about 90MB). Everything else can be
#       deleted:
#
#       C:\testme\msys32\dev
#       C:\testme\msys32\etc
#       C:\testme\msys32\home
#       C:\testme\msys32\mingw32\bin
#       C:\testme\msys32\mingw32\lib\gdk-pixbuf-2.0
#       C:\testme\msys32\mingw32\lib\girepository-1.0
#       C:\testme\msys32\mingw32\lib\glib-2.0
#       C:\testme\msys32\mingw32\lib\gtk-3.0
#       C:\testme\msys32\mingw32\lib\python3.7
#       C:\testme\msys32\mingw32\lib\thread2.8.4
#       C:\testme\msys32\mingw32\share\gir-1.0
#       C:\testme\msys32\mingw32\share\glib-2.0
#       C:\testme\msys32\mingw32\share\gtk-3.0
#       C:\testme\msys32\mingw32\share\icons
#       C:\testme\msys32\mingw32\share\locale
#       C:\testme\msys32\mingw32\share\themes
#       C:\testme\msys32\mingw32\share\thumbnailers
#       C:\testme\msys32\tmp
#       C:\testme\msys32\usr\bin\bash
#       C:\testme\msys32\usr\bin\chmod
#       C:\testme\msys32\usr\bin\cygpath
#       C:\testme\msys32\usr\bin\cygwin-console-helper
#       C:\testme\msys32\usr\bin\env
#       C:\testme\msys32\usr\bin\find
#       C:\testme\msys32\usr\bin\findfs
#       C:\testme\msys32\usr\bin\hostid
#       C:\testme\msys32\usr\bin\hostname
#       C:\testme\msys32\usr\bin\iconv
#       C:\testme\msys32\usr\bin\id
#       C:\testme\msys32\usr\bin\ln
#       C:\testme\msys32\usr\bin\locale
#       C:\testme\msys32\usr\bin\mintty
#       C:\testme\msys32\usr\bin\mkdir
#       C:\testme\msys32\usr\bin\msys-2.0.dll
#       C:\testme\msys32\usr\bin\msys-gcc_s-1.dll
#       C:\testme\msys32\usr\bin\msys-iconv-2.dll
#       C:\testme\msys32\usr\bin\msys-intl-8.dll
#       C:\testme\msys32\usr\bin\test
#       C:\testme\msys32\usr\bin\tzset
#
#   - Now go into the C:\testme\msys32\home\YOURNAME\tartube\nsis folder, and
#       MOVE all the windows batch files into the folder above, i.e. into
#       C:\testme\msys32\home\YOURNAME\tartube
#   - Next, COPY all the remaining files in
#       C:\testme\msys32\home\YOURNAME\tartube\nsis to C:\testme
#   - Create the installer by compiling the NSIS script,
#       C:\testme\tartube_install_32bit.nsi (the quickest way to do this is
#       by right-clicking the file and selecting 'Compile NSIS script file')
#   - When NSIS is finished, the installer appears in C:\testme

# Header files
# -------------------------------

    !include "MUI2.nsh"
    !include "Sections.nsh"

# General
# -------------------------------

    ;Name and file
    Name "Tartube"
    OutFile "install-tartube-1.2.008-32bit.exe"

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

    !define MUI_FINISHPAGE_RUN "$INSTDIR\msys32\home\user\tartube\tartube_32bit.bat"
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
    File /r msys32

    SetOutPath "$INSTDIR\msys32\home\user\tartube"

    # Start Menu
    CreateDirectory "$SMPROGRAMS\Tartube"
    CreateShortCut "$SMPROGRAMS\Tartube\Tartube.lnk" \
        "$INSTDIR\msys32\home\user\tartube\tartube_32bit.bat" \
        "" "$INSTDIR\tartube_icon.ico" "" SW_SHOWMINIMIZED
    CreateShortCut "$SMPROGRAMS\Tartube\Uninstall Tartube.lnk" \
        "$INSTDIR\Uninstall.exe" \
        "" "$INSTDIR\tartube_icon.ico"
    # Temporary Start Menu link for bugfixing on MS Windows 10
    CreateShortCut "$SMPROGRAMS\Tartube\Test Gtk graphics.lnk" \
        "$INSTDIR\msys32\home\user\tartube\hello_world_32bit.bat" \
        "" "$INSTDIR\tartube_icon.ico" ""

    # Desktop icon
    CreateShortcut "$DESKTOP\Tartube.lnk" \
        "$INSTDIR\msys32\home\user\tartube\tartube_32bit.bat" \
        "" "$INSTDIR\tartube_icon.ico" "" SW_SHOWMINIMIZED

    # Store installation folder
    WriteRegStr HKLM \
        "Software\Microsoft\Windows\CurrentVersion\Uninstall\Tartube" \
        "DisplayName" "Tartube"
    WriteRegStr HKLM \
        "Software\Microsoft\Windows\CurrentVersion\Uninstall\Tartube" \
        "UninstallString" "$\"$INSTDIR\Uninstall.exe$\""
    WriteRegStr HKLM \
        "Software\Microsoft\Windows\CurrentVersion\Uninstall\Tartube" \
        "Publisher" "A S Lewis"
    WriteRegStr HKLM \
        "Software\Microsoft\Windows\CurrentVersion\Uninstall\Tartube" \
        "DisplayVersion" "1.2.008"

    # Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"

SectionEnd

# Uninstaller sections
# -------------------------------

Section "Uninstall"

    Delete "$SMPROGRAMS\Tartube\Tartube.lnk"
    Delete "$SMPROGRAMS\Tartube\Uninstall Tartube.lnk"
    Delete "$SMPROGRAMS\Tartube\Gtk graphics test.lnk"
    RMDir /r "$SMPROGRAMS\Tartube"
    Delete "$DESKTOP\Tartube.lnk"

    RMDir /r "$INSTDIR"
    Delete "$INSTDIR\Uninstall.exe"

    DeleteRegKey HKLM \
        "Software\Microsoft\Windows\CurrentVersion\Uninstall\Tartube"

SectionEnd
