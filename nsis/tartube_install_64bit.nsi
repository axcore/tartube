# Tartube v2.5.156 installer script for MS Windows
#
# Copyright (C) 2019-2025 A S Lewis
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#
# Build instructions:
#   - These instructions describe how to create an installer for Tartube on a
#       64-bit MS Windows machine (minimum version: Windows 10, 64bit)
#
#   - Download and install NSIS from
#
#       http://nsis.sourceforge.io/Download/
#
#   - Download the 64-bit version of MSYS2. The downloadable file should look
#       something like 'msys2-x86-64-yyyymmdd.exe'
#
#       http://www.msys2.org/
#
#   - Run the file to install MSYS2. We suggest that you create a top-level
#       folder. Here, we call it C:\testme. Let MSYS2 install itself inside
#       that directory, i.e. C:\testme\msys64
#
#   - Run the MINGW64 terminal, i.e.
#
#       C:\testme\msys64\mingw64.exe
#
#   - We need to install various dependencies. In the terminal window, type
#       this command
#
#       pacman -Syu
#
#   - Usually, the terminal window tells you to close it. Do that, and then
#       open a new MINGW64 terminal window
#
#   - In the new window, type these commands
#
#       pacman -Su
#       pacman -S mingw-w64-x86_64-python3
#       pacman -S mingw-w64-x86_64-python-pip
#       pacman -S mingw-w64-x86_64-python-gobject
#       pacman -S mingw-w64-x86_64-python-requests
#       pacman -S mingw-w64-x86_64-gtk3
#       pacman -S mingw-w64-x86_64-gsettings-desktop-schemas
#
#   - (Don't close the MINGW64 terminal until you have finished the
#       installation)

#   - Optional step: you can check that the dependencies are working by typing
#       this command (if you like):
#
#       gtk3-demo
#
#   - Install Microsoft Visual C++ (a free download from the Microsoft website)
#
#   - Navigate to the folder C:\Windows\System32
#
#   - Copy all the files whose name starts with 'msvcr' (e.g.
#       'msvcr1230_clr0400.dll') into the folder C:\testme\msys64\mingw64\bin
#
#   - In the MINGW64 terminal, type the following commands:
#
#       /mingw64/bin/python3 -m venv ~/ytdl-venv
#       source ~/ytdl-venv/bin/activate
#
#   - In a suitable text editor, open the file
#       C:\testme\msys64\home\YOURNAME\.bashrc
#
#   - Note that YOURNAME should be substituted for your actual Windows
#       username. For example, the file might be
#
#       C:\testme\msys64\home\alice\.bashrc
#
#   - At the top of the file, add the following lines, then save it
#
#       export PIP_HOME="$HOME/.local/pip"
#       export PIP_BIN_DIR="$HOME/.local/bin"
#       export PATH="$PIP_BIN_DIR:$PATH"
#
#   - Nagivate to C:\testme\msys64\mingw64\lib\python3.12\site-packages
#
#   - Copy the following folders to
#       C:\testme\msys64\home\YOURNAME\ytdl-venv\lib\python3.12\site-packages
#
#       certifi
#       charset_normalizer
#       gi
#       idna
#       requests
#       urllib3
#
#   - If you want to install Atomic Parsley (from
#       https://github.com/wez/atomicparsley), copy the MS Windows executable
#       into the C:\testme\msys64\usr\bin folder
#
#   - In the MINGW64 terminal, type the following commands:
#
#       pip install feedparser
#       pip install playsound
#       pacman -S mingw-w64-x86_64-aria2
#
#   - The C:\testme folder now contains about 2GB of data. If you like, you can
#       use all of it (which would create an installer of about 600MB). In most
#       cases, though, you will probably want to remove everything that's not
#       necessary
#
#   - This table shows which files and folders are in the official Tartube
#       installer (which is about 140MB). Files/folders ending in * represent
#       multiple files/folders which must be retained. Everything else can be
#       deleted
#
#   - Note that version numbers will change over time; retain which version of
#       the file/folder is available
#
#       C:\testme\msys64\clang64
#       C:\testme\msys64\clangarm64
#       C:\testme\msys64\dev
#       C:\testme\msys64\etc
#       C:\testme\msys64\home
#       C:\testme\msys64\installerResources
#       C:\testme\msys64\mingw64.exe
#
#       C:\testme\msys64\mingw64\bin
#       C:\testme\msys64\mingw64\bin\gdbus*
#       C:\testme\msys64\mingw64\bin\gdk*
#       C:\testme\msys64\mingw64\bin\gettext*
#       C:\testme\msys64\mingw64\bin\gi-compile_repository
#       C:\testme\msys64\mingw64\bin\gi-decompile_typelib
#       C:\testme\msys64\mingw64\bin\gi-inspect_typelib
#       C:\testme\msys64\mingw64\bin\gio*
#       C:\testme\msys64\mingw64\bin\glib*
#       C:\testme\msys64\mingw64\bin\gobject*
#       C:\testme\msys64\mingw64\bin\gsettings
#       C:\testme\msys64\mingw64\bin\gtk*
#       C:\testme\msys64\mingw64\bin\img2webp
#       C:\testme\msys64\mingw64\bin\json*
#       C:\testme\msys64\mingw64\bin\lib*
#       C:\testme\msys64\mingw64\bin\msvcr*
#       C:\testme\msys64\mingw64\bin\openssl
#       C:\testme\msys64\mingw64\bin\pip*
#       C:\testme\msys64\mingw64\bin\python*
#       C:\testme\msys64\mingw64\bin\sqlite*
#       C:\testme\msys64\mingw64\bin\xml*
#       C:\testme\msys64\mingw64\bin\zlib1.dll
#
#       C:\testme\msys64\mingw64\include\gdk-pixbuf-2.0
#       C:\testme\msys64\mingw64\include\gio-win32-2.0
#       C:\testme\msys64\mingw64\include\glib-2.0
#       C:\testme\msys64\mingw64\include\gsettings-desktop-schemas
#       C:\testme\msys64\mingw64\include\gtk-3.0
#       C:\testme\msys64\mingw64\include\json-glib-1.0
#       C:\testme\msys64\mingw64\include\libxml2
#       C:\testme\msys64\mingw64\include\ncurses
#       C:\testme\msys64\mingw64\include\ncursesw
#       C:\testme\msys64\mingw64\include\openssl
#       C:\testme\msys64\mingw64\include\pycairo
#       C:\testme\msys64\mingw64\include\pygobject-3.0
#       C:\testme\msys64\mingw64\include\python3.12
#       C:\testme\msys64\mingw64\include\readline
#       C:\testme\msys64\mingw64\include\tk8.6
#
#       C:\testme\msys64\mingw64\lib\gdk-pixbuf-2.0
#       C:\testme\msys64\mingw64\lib\gettext
#       C:\testme\msys64\mingw64\lib\gio
#       C:\testme\msys64\mingw64\lib\girepository-1.0
#       C:\testme\msys64\mingw64\lib\glib-2.0
#       C:\testme\msys64\mingw64\lib\gtk-3.0
#       C:\testme\msys64\mingw64\lib\python3.9\asyncio
#       C:\testme\msys64\mingw64\lib\python3.9\collections
#       C:\testme\msys64\mingw64\lib\python3.9\concurrent
#       C:\testme\msys64\mingw64\lib\python3.9\ctypes
#       C:\testme\msys64\mingw64\lib\python3.9\email
#       C:\testme\msys64\mingw64\lib\python3.9\encodings
#       C:\testme\msys64\mingw64\lib\python3.9\ensurepip
#       C:\testme\msys64\mingw64\lib\python3.9\html
#       C:\testme\msys64\mingw64\lib\python3.9\http
#       C:\testme\msys64\mingw64\lib\python3.9\importlib
#       C:\testme\msys64\mingw64\lib\python3.9\json
#       C:\testme\msys64\mingw64\lib\python3.9\lib2to3
#       C:\testme\msys64\mingw64\lib\python3.9\lib-dynload
#       C:\testme\msys64\mingw64\lib\python3.9\logging
#       C:\testme\msys64\mingw64\lib\python3.9\msilib
#       C:\testme\msys64\mingw64\lib\python3.9\multiprocessing
#       C:\testme\msys64\mingw64\lib\python3.9\re
#       C:\testme\msys64\mingw64\lib\python3.9\site-packages
#       C:\testme\msys64\mingw64\lib\python3.9\sqlite3
#       C:\testme\msys64\mingw64\lib\python3.9\tomllib
#       C:\testme\msys64\mingw64\lib\python3.9\urllib
#       C:\testme\msys64\mingw64\lib\python3.9\venv
#       C:\testme\msys64\mingw64\lib\python3.9\xml
#       C:\testme\msys64\mingw64\lib\python3.9\xmlrpc
#       C:\testme\msys64\mingw64\lib\python3.9\zipfile
#       C:\testme\msys64\mingw64\lib\python3.9\*.py
#       C:\testme\msys64\mingw64\lib\sqlite3.36.0
#       C:\testme\msys64\mingw64\lib\terminfo
#       C:\testme\msys64\mingw64\lib\thread2.8.4
#       C:\testme\msys64\mingw64\lib\tk8.6
#
#       C:\testme\msys64\mingw64\share\gettext*
#       C:\testme\msys64\mingw64\share\gir-1.0
#       C:\testme\msys64\mingw64\share\glib-2.0
#       C:\testme\msys64\mingw64\share\gtk-3.0
#       C:\testme\msys64\mingw64\share\icons
#       C:\testme\msys64\mingw64\share\locale\en*
#       C:\testme\msys64\mingw64\share\sqlite
#       C:\testme\msys64\mingw64\share\terminfo
#       C:\testme\msys64\mingw64\share\themes
#       C:\testme\msys64\mingw64\share\thumbnailers
#       C:\testme\msys64\mingw64\share\xml
#
#       C:\testme\msys64\mingw64\ssl
#
#       C:\testme\msys64\tmp
#       C:\testme\msys64\ucrt64
#
#       C:\testme\msys64\usr\bin\core_perl
#       C:\testme\msys64\usr\bin\site_perl
#       C:\testme\msys64\usr\bin\vendor_perl
#       C:\testme\msys64\usr\bin\AtomicParsley
#       C:\testme\msys64\usr\bin\bash
#       C:\testme\msys64\usr\bin\chmod
#       C:\testme\msys64\usr\bin\cut
#       C:\testme\msys64\usr\bin\cygpath
#       C:\testme\msys64\usr\bin\cygwin-console-helper
#       C:\testme\msys64\usr\bin\dir
#       C:\testme\msys64\usr\bin\dirname
#       C:\testme\msys64\usr\bin\env
#       C:\testme\msys64\usr\bin\find
#       C:\testme\msys64\usr\bin\findfs
#       C:\testme\msys64\usr\bin\getent
#       C:\testme\msys64\usr\bin\gettext*
#       C:\testme\msys64\usr\bin\gpg*
#       C:\testme\msys64\usr\bin\grep
#       C:\testme\msys64\usr\bin\hostid
#       C:\testme\msys64\usr\bin\hostname
#       C:\testme\msys64\usr\bin\iconv
#       C:\testme\msys64\usr\bin\id
#       C:\testme\msys64\usr\bin\ln
#       C:\testme\msys64\usr\bin\locale
#       C:\testme\msys64\usr\bin\ls
#       C:\testme\msys64\usr\bin\mintty
#       C:\testme\msys64\usr\bin\mkdir
#       C:\testme\msys64\usr\bin\msys-2.0.dll
#       C:\testme\msys64\usr\bin\msys-argp-0.dll
#       C:\testme\msys64\usr\bin\msys-assuan-0.dll
#       C:\testme\msys64\usr\bin\msys-assuan-9.dll
#       C:\testme\msys64\usr\bin\msys-atomic-1.dll
#       C:\testme\msys64\usr\bin\msys-bz2-1.dll
#       C:\testme\msys64\usr\bin\msys-gcc_s-1.dll
#       C:\testme\msys64\usr\bin\msys-gcrypt-20.dll
#       C:\testme\msys64\usr\bin\msys-gpg-error-0.dll
#       C:\testme\msys64\usr\bin\msys-iconv-2.dll
#       C:\testme\msys64\usr\bin\msys-intl-8.dll
#       C:\testme\msys64\usr\bin\msys-ncurses++w6.dll
#       C:\testme\msys64\usr\bin\msys-ncursesw6.dll
#       C:\testme\msys64\usr\bin\msys-npth-0.dll
#       C:\testme\msys64\usr\bin\msys-pcre-1.dll
#       C:\testme\msys64\usr\bin\msys-pcre2-8-0.dll
#       C:\testme\msys64\usr\bin\msys-readline8.dll
#       C:\testme\msys64\usr\bin\msys-sqlite3-0.dll
#       C:\testme\msys64\usr\bin\msys-stdc++06.dll
#       C:\testme\msys64\usr\bin\msys-z.dll
#       C:\testme\msys64\usr\bin\mv
#       C:\testme\msys64\usr\bin\pac*
#       C:\testme\msys64\usr\bin\rm
#       C:\testme\msys64\usr\bin\rmdir
#       C:\testme\msys64\usr\bin\sed
#       C:\testme\msys64\usr\bin\test
#       C:\testme\msys64\usr\bin\tzset
#       C:\testme\msys64\usr\bin\uname
#       C:\testme\msys64\usr\bin\vercmp
#       C:\testme\msys64\usr\bin\which
#       C:\testme\msys64\usr\bin\xml*
#
#       C:\testme\msys64\usr\lib\gettext
#       C:\testme\msys64\usr\lib\openssl
#       C:\testme\msys64\usr\lib\python3.12
#       C:\testme\msys64\usr\lib\terminfo
#       C:\testme\msys64\usr\lib\thread2.8.5
#
#       C:\testme\msys64\usr\share\cygwin
#       C:\testme\msys64\usr\share\makepkg
#       C:\testme\msys64\usr\share\mintty
#       C:\testme\msys64\usr\share\Msys
#       C:\testme\msys64\usr\share\pacman
#       C:\testme\msys64\usr\share\terminfo
#
#       C:\testme\msys64\usr\ssl
#
#       C:\testme\msys64\var\lib\pacman
#
#   - The following optional dependencies are required for fetching livestreams.
#       If you decide to install them (it's recommended that you do), then type
#       these commands in the MINGW64 terminal
#
#       pip3 install feedparser
#       pip3 install playsound
#
#   - In the terminal window, you could add the following optional package:
#
#       pacman -S mingw-w64-x86_64-aria2
#
#   - Now download the Tartube source code from
#
#       https://sourceforge.net/projects/tartube/
#
#   - Extract it, and copy the whole 'tartube' folder to
#
#       C:\testme\msys64\home\YOURNAME
#
#   - Next, copy all of the files in
#       C:\testme\msys64\home\YOURNAME\tartube\nsis to C:\testme
#
#   - Create the installer by compiling the NSIS script,
#       C:\testme\tartube_install_64bit.nsi (the quickest way to do this is
#       by right-clicking the file and selecting 'Compile NSIS script file')
#
#   - When NSIS is finished, the installer appears in C:\testme

# Header files
# -------------------------------

Unicode True

    !include "MUI2.nsh"
    !include "Sections.nsh"
    !include "FileFunc.nsh"

# General
# -------------------------------

    !define PROGRAM_NAME             "Tartube"
    !define PROGRAM_VERSION          "2.5.156"

    VIProductVersion                 ${PROGRAM_VERSION}.0
    VIFileVersion                    ${PROGRAM_VERSION}.0

    !define PROGRAM_PUBLISHER        "A S Lewis"
    !define LINK_LOCATION            "http://tartube.sourceforge.io/"
    !define BRANDING_TEXT            "  "
    !define SOURCE_FOLDER            "msys64"

    !define /date CURRENT_YEAR       "%Y"


    ;Name and file
    Name    "${PROGRAM_NAME}"
    Caption "$(Program_caption)"
    OutFile "install-tartube-${PROGRAM_VERSION}-64bit.exe"

    ShowInstDetails show
    ShowUnInstDetails show

    VIAddVersionKey "ProductName"        "${PROGRAM_NAME}"
    VIAddVersionKey "ProductVersion"     "${PROGRAM_VERSION}"
    VIAddVersionKey "Comments"           ""
    VIAddVersionKey "CompanyName"        "${PROGRAM_PUBLISHER}"
    VIAddVersionKey "LegalTrademarks"    "${PROGRAM_PUBLISHER} ${CURRENT_YEAR}"
    VIAddVersionKey "LegalCopyright"     "${PROGRAM_PUBLISHER} ${CURRENT_YEAR}"
    VIAddVersionKey "FileDescription"    "${PROGRAM_NAME} installer"
    VIAddVersionKey "FileVersion"        "${PROGRAM_VERSION}"
    VIAddVersionKey "InternalName"       "${PROGRAM_NAME}"


    ;Default installation folder
    InstallDir "$LOCALAPPDATA\Tartube"

    ;Get installation folder from registry if available
    InstallDirRegKey HKCU "Software\${PROGRAM_NAME}" ""

    ;Request application privileges for Windows Vista
;    RequestExecutionLevel user

    ;Request application privileges to write info in program list
    RequestExecutionLevel Admin

    ; Extra stuff here
    BrandingText "${BRANDING_TEXT}"

# Variables
# -------------------------------

###   Var StartMenuFolder

# Interface settings
# -------------------------------

    !define MUI_ABORTWARNING
    !define MUI_ICON                             "tartube_icon.ico"
    !define MUI_UNICON                           "tartube_icon.ico"
    !define MUI_HEADERIMAGE
    !define MUI_HEADERIMAGE_BITMAP               "tartube_header.bmp"
    !define MUI_HEADERIMAGE_UNBITMAP             "tartube_header.bmp"
    !define MUI_WELCOMEFINISHPAGE_BITMAP         "tartube_wizard.bmp"

# Pages
# -------------------------------

    !insertmacro MUI_PAGE_WELCOME

    !insertmacro MUI_PAGE_LICENSE                "license.txt"

    !insertmacro MUI_PAGE_DIRECTORY

    !define MUI_STARTMENUPAGE_REGISTRY_ROOT      "SHCTX"
    !define MUI_STARTMENUPAGE_REGISTRY_KEY       "Software\${PROGRAM_NAME}"
    !define MUI_STARTMENUPAGE_REGISTRY_VALUENAME "Startmenu"
    !define MUI_STARTMENUPAGE_DEFAULTFOLDER      "${PROGRAM_NAME}"

    !insertmacro MUI_PAGE_INSTFILES

    !define MUI_FINISHPAGE_RUN                   "$INSTDIR\${SOURCE_FOLDER}\home\user\tartube\tartube_64bit.bat"
    !define MUI_FINISHPAGE_RUN_TEXT              "$(RunTartube)"
    !define MUI_FINISHPAGE_RUN_NOTCHECKED
    !define MUI_FINISHPAGE_LINK                  "$(VisitTartubeSite)"
    !define MUI_FINISHPAGE_LINK_LOCATION         "${LINK_LOCATION}"

    !insertmacro MUI_PAGE_FINISH
    !insertmacro MUI_UNPAGE_CONFIRM
    !insertmacro MUI_UNPAGE_INSTFILES

# Languages
# -------------------------------

    !insertmacro MUI_LANGUAGE "English"
    !insertmacro MUI_LANGUAGE "Italian"

    LangString RunTartube        ${LANG_ENGLISH} "Run ${PROGRAM_NAME}"
    LangString VisitTartubeSite  ${LANG_ENGLISH} "Visit the ${PROGRAM_NAME} website for the latest news and support"
    LangString UninstallTartube  ${LANG_ENGLISH} "Uninstall ${PROGRAM_NAME}"
    LangString GtkGraphicsTest   ${LANG_ENGLISH} "Gtk graphics test"
    LangString Program_installer ${LANG_ENGLISH} "${PROGRAM_NAME} installer"
    LangString Program_caption   ${LANG_ENGLISH} "Setup of ${PROGRAM_NAME} ${PROGRAM_VERSION}"

    LangString RunTartube        ${LANG_ITALIAN} "Esegui ${PROGRAM_NAME}"
    LangString VisitTartubeSite  ${LANG_ITALIAN} "Visita il sito web di ${PROGRAM_NAME} per le ultime novità ed il supporto"
    LangString UninstallTartube  ${LANG_ITALIAN} "Disinstalla ${PROGRAM_NAME}"
    LangString GtkGraphicsTest   ${LANG_ITALIAN} "Test grafica Gtk"
    LangString Program_installer ${LANG_ITALIAN} "${PROGRAM_NAME} installer"
    LangString Program_caption   ${LANG_ITALIAN} "Installazione di ${PROGRAM_NAME} ${PROGRAM_VERSION}"


# Installer sections
# -------------------------------

Section "Tartube" SecClient

    SectionIn RO
    SetOutPath "$INSTDIR"

    File "tartube_icon.ico"
    File /r ${SOURCE_FOLDER}

    SetOutPath "$INSTDIR\${SOURCE_FOLDER}\home\user\tartube"

    # Start Menu
    CreateDirectory "$SMPROGRAMS\${PROGRAM_NAME}"
    CreateShortCut  "$SMPROGRAMS\${PROGRAM_NAME}\${PROGRAM_NAME}.lnk"     "$INSTDIR\${SOURCE_FOLDER}\home\user\tartube\tartube_64bit.bat"   "" "$INSTDIR\tartube_icon.ico" "" SW_SHOWMINIMIZED
    CreateShortCut  "$SMPROGRAMS\${PROGRAM_NAME}\$(UninstallTartube).lnk" "$INSTDIR\Uninstall.exe"                                          "" "$INSTDIR\tartube_icon.ico"
    CreateShortCut  "$SMPROGRAMS\${PROGRAM_NAME}\$(GtkGraphicsTest).lnk"  "$INSTDIR\${SOURCE_FOLDER}\mingw64\bin\gtk3-demo-application.exe" "" "$INSTDIR\tartube_icon.ico" ""

    # Desktop icon
    CreateShortcut "$DESKTOP\Tartube.lnk" "$INSTDIR\${SOURCE_FOLDER}\home\user\tartube\tartube_64bit.bat" "" "$INSTDIR\tartube_icon.ico" "" SW_SHOWMINIMIZED

    # Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"

SectionEnd

Section -Post
   !define PRODUCT_UNINST_ROOT_KEY  "HKLM"
   !define PRODUCT_UNINST_KEY       "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PROGRAM_NAME}"
   WriteRegStr   ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName"     "$(^Name)"
   WriteRegStr   ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion"  "${PROGRAM_VERSION}"
   WriteRegStr   ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\Uninstall.exe"
   WriteRegStr   ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon"     "$INSTDIR\Uninstall.exe"
   WriteRegStr   ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher"       "${PROGRAM_PUBLISHER}"
   ;  ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
   ;  IntFmt $0 "0x%08X" $0
   ;  Following lines will make uninstaller work - do not change anything, unless you really want to.
   ;WriteRegDWORD ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "EstimatedSize"   "$0"
SectionEnd
  
# Uninstaller sections
# -------------------------------

Section "Uninstall"

    Delete   "$SMPROGRAMS\${PROGRAM_NAME}\${PROGRAM_NAME}.lnk"
    Delete   "$SMPROGRAMS\${PROGRAM_NAME}\$(UninstallTartube).lnk"
    Delete   "$SMPROGRAMS\${PROGRAM_NAME}\$(GtkGraphicsTest).lnk"
    RMDir /r "$SMPROGRAMS\${PROGRAM_NAME}"
    Delete   "$DESKTOP\${PROGRAM_NAME}.lnk"

    RMDir /r "$INSTDIR"
    Delete   "$INSTDIR\Uninstall.exe"

    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PROGRAM_NAME}"

SectionEnd
