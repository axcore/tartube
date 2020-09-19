================================================
Axmud - A modern Multi-User Dungeon (MUD) client
================================================

.. image:: screenshots/shot1r.png
  :alt: Axmud screenshot

* `1 Introduction`_
* `2 Downloads`_
* `3 Running Axmud`_
* `4 Installation on MS Windows`_
* `4.1 Installation on MS Windows using Strawberry Perl`_
* `4.2 Installation on MS Windows using ActivePerl`_
* `4.3 Using Festival on MS Windows`_
* `5 Installation on Linux`_
* `5.1 Installation on Linux using the .DEB package`_
* `5.2 Installation on Linux using the .RPM package`_
* `5.3 Installation on Linux from source`_
* `5.3.1 Installation on Arch-based systems`_
* `5.3.2 Installation on Debian-based systems`_
* `5.3.3 Installation on Fedora`_
* `5.3.4 Installation on Manjaro`_
* `5.3.5 Installation on openSUSE`_
* `5.3.6 Installation on Red Hat Enterprise Linux / CentOS`_
* `6 Installation ON BSD`_
* `6.1 Installation on GhostBSD`_
* `7 List of pre-configured worlds`_
* `8 Contributing`_
* `9 Authors`_
* `10 License`_

1 Introduction
==============

Axmud is a modern Multi-User Dungeon (MUD) client written in Perl 5 / Gtk3. Its features include:

- Telnet, SSH and SSL connections
- ANSI/xterm/truecolour/OSC/RGB colours
- Full support for all major MUD protocols, including MXP and GMCP (with partial Pueblo support)
- Partial VT100 emulation
- Class-based triggers, aliases, macros, timers and hooks
- Graphical automapper
- Over 100 pre-configured worlds
- Multiple approaches to scripting
- Fully customisable from top to bottom, using the command line or the extensive GUI interface
- Native support for visually-impaired users

Axmud is known to work on MS Windows, Linux and \*BSD. It might be possible to install it on other systems such as MacOS, but the authors have not been able to confirm this yet.

Axmud does not yet have a comprehensive manual, but there is lots of information to read:

- Read the `quick help <share/docs/quick/quick.mkd>`__
- Read the `Axmud guide <share/docs/guide/index.mkd>`__, including the section for `visually-impaired users <share/docs/guide/ch16.mkd>`__
- Read the `tutorial <share/docs/tutorial/index.mkd>`__  for the Axbasic scripting language
- In Axmud's main window menu, click **Help > About**
- Just below the menu, click the calendar button to open the object viewer window, and then click on **Help**
- Type **;help** for a list of client commands, or **;help listworld** for help on the **;listworld** client command
- Type **;axbasichelp** for a list of help topics for the Axbasic scripting language
- For further support, visit the `Axmud forum <https://axmud.sourceforge.io/forum/index.php>`__ or our `Github page <https://github.com/axcore/axmud>`__

2 Downloads
===========

Latest version: **v1.3.0 (19 Sep 2020)** (see `recent changes <CHANGES>`__)

Official packages (also available from the `Github release page <https://github.com/axcore/tartube/releases>`__):

- `MS Windows installer <https://sourceforge.net/projects/axmud/files/Axmud-1.3.0/install-axmud-1.3.0.exe/download>`__ from Sourceforge
- `DEB package (for Debian-based distros, e.g. Ubuntu, Linux Mint) <https://sourceforge.net/projects/axmud/files/Axmud-1.3.0/libgames-axmud-perl_1.3.0.deb/download>`__ from Sourceforge
- `RPM package (for RHEL-based distros, e.g. Fedora) <https://sourceforge.net/projects/axmud/files/Axmud-1.3.0/perl-Games-Axmud-1.3.0.noarch.rpm/download>`__ from Sourceforge

Source code:

- `Source code <https://sourceforge.net/projects/axmud/files/Axmud-1.2.041/Games-Axmud-1.2.041.tar.gz/download>`__ from Sourceforge
- `Source code <https://github.com/axcore/axmud>`__ and `support <https://github.com/axcore/axmud/issues>`__ from GitHub

3 Running Axmud
===============

There are several ways to install Axmud (see below). Most of them will add an Axmud icon to your desktop, and an entry in your Start Menu.

There are actually two versions of Axmud: a 'normal' version, and a version with optimised settings for visually-impaired users.

The optimised version will start talking at you, as soon as you start it. (If you don't hear anything, then perhaps there are no text-to-speech engines installed on your system.)

If you're running Axmud from the command line, visually-impaired users can run this script:

        **baxmud.pl**

Other users can run this script:

        **axmud.pl**

Using either script, you can specify a world to which Axmud connects immediately:

        **axmud.pl empiremud.net 4000**

If you omit the port number, Axmud connects using the generic port 23:

        **axmud.pl elephant.org**

If a world profile already exists, you can specify its name instead:

        **axmud.pl cryosphere**

You can force Axmud to use a particular text-to-speech engine by adding the engine's name to the end of those commands. This overrides (almost) all other text-to-speech settings.

Acceptable engine names are 'espeak', 'esng' (for espeak-ng), 'flite' (for Festival Lite), 'festival', 'swift' and 'none' (for the dummy engine, which produces no sound). For example:

        **baxmud.pl empiremud.net 4000 esng**
        **axmud.pl cryosphere festival**

Note that on MS Windows, Flite is not supported, and other speech engines are assumed to be installed in their default locations.

4 Installation on MS Windows
============================

The easiest way to use Axmud on Windows is to download and run the Windows installer.

The installer contains everything you need to run Axmud, including a copy of Strawberry Perl, several text-to-speech engine and all the required modules and libraries.

Users who already have Strawberry Perl and/or ActivePerl installed on their system can install Axmud manually using the following methods.

4.1 Installation on MS Windows using Strawberry Perl
----------------------------------------------------

Axmud v1.2.0 (and all later versions) is known to work with both 32-bit and 64-bit editions of Strawberry Perl.

After installing Strawberry Perl on your system, open a command prompt. From the Windows Start menu, you can click:

        **All Programs > Strawberry Perl > Perl (command line)**

Next, get some modules from CPAN:

        **cpan Archive::Extract IO::Socket::INET6 IPC::Run Math::Round Net::OpenSSH Path::Tiny Regexp::IPv6**

Then get the following module:

        **cpan File::ShareDir::Install**

If the line above generates an error, try this line instead:

        **cpanm --force --build-args SHELL=cmd.exe --install-args SHELL=cmd.exe File::ShareDir::Install**

Now we need some modules from the Sisyphusion repo. (If you are reading this document some time in the distant future and find the repo is no longer available, you can either search around for a replacement, or you can use the installer.)

        **ppm set repository sisyphusion http://sisyphusion.tk/ppm**
        **ppm set save**
        **ppm install Glib Gtk3 GooCanvas2**

Before continuing, you should remove the following folder. When asked **Are you sure (Y/N)?**, type **y**.

        **rmdir /s C:\Strawberry\perl\site\lib\sisyphusion_gtk2_themes_temp**

Now type this the following command. At the time of writing, it produces a *cannot remove directory - permission denied* error. This is expected and does not affect Axmud installation.

        **ppm install http://www.sisyphusion.tk/ppm/PPM-Sisyphusion-Gtk2_theme.ppd**

Now we need to copy a .dll file from one location to another:

        **copy C:\Strawberry\perl\site\lib\auto\Cairo\s1sfontconfig-1.dll C:\Strawberry\perl\bin\s1sfontconfig-1.dll**

Download the Axmud source code file (ending .tar.gz), and extract it in a convenient location (e.g. your Downloads folder). If you don't have anything capable of extracting a .tar.gz archive, you can use 7-Zip.

From the same command prompt window as earlier, change to that directory, for example:

        **cd C:\Users\YOURNAME\Downloads\Games-Axmud-1.2.345**

From this point, installation is standard.

        **perl Makefile.PL**
        **gmake**
        **gmake install**
        **axmud.pl**

4.2 Installation on MS Windows using ActivePerl
-----------------------------------------------

Axmud is known to work with both 32-bit and 64-bit editions of ActivePerl.

First, open a command prompt. From the Windows Start menu, type **cmd** inside the **Search programs and files** box.

Then we can get some modules from CPAN:

        **ppm install dmake**
        **ppm install Archive::Extract File::ShareDir::Install IO::Socket::INET6 IPC::Run Math::Round Net::OpenSSH Path::Tiny Regexp::IPv6**

Now we need some modules from the Sisyphusion repo. (If you are reading this document some time in the distant future and find the repo is no longer available, you can either search around for a replacement, or you can use the installer.)

        **ppm repo add http://www.sisyphusion.tk/ppm**
        **ppm install Glib Gtk3 GooCanvas2 -- force**

Download the Axmud source code file (ending .tar.gz), and extract it in a convenient location (e.g. your Downloads folder). If you don't have anything capable of extracting a .tar.gz archive, you can use 7-Zip.

From the same command prompt window as earlier, change to that directory, for example:

        **cd C:\Users\YOURNAME\Downloads\Games-Axmud-1.2.345**

From this point, installation is standard.

        **perl Makefile.PL**
        **dmake**
        **dmake install**
        **axmud.pl**

4.3 Using Festival on MS Windows
--------------------------------

Axmud cannot use the Festival text-to-speech engine without patching the `Perl IPC::Run module <https://metacpan.org/pod/IPC::Run>`__. Instructions for doing this can be found in the Axmud source code, in the file **../axmud/nsis/axmud_installer.nsi**.

The MS Windows installer already contains a patched version of IPC::Run.

5 Installation on Linux
=======================

There are three methods of installation on Linux - install using the **.deb** package, install using the **.rpm** package or install manually using the source code.

5.1 Installation on Linux using the .DEB package
------------------------------------------------

**.deb** packages are typically supported on Debian-based systems (such as Ubuntu and Linux Mint).

Installation may be as simple as downloading the **.deb** package and double-clicking on it. If not, you can install the package from the command line.

Open a terminal and navigate to the directory where the downloaded file is, for example:

        **cd Downloads**

Then install the package:

        **sudo dpkg -i libgames-axmud-perl_X.Y.ZZZ.deb**

You must replace the **X.Y.ZZZ** with the actual version number you've downloaded, for example:

        **sudo dpkg -i libgames-axmud-perl_1.2.345.deb**

When installation is complete, start Axmud by typing:

        **axmud.pl**

5.2 Installation on Linux using the .RPM package
------------------------------------------------

**.rpm** packages are typically supported on Fedora-based systems (such as Red Hat Enterprise Linux and CentOS).

The package can be installed from the command line.

Open a terminal and navigate to the directory where the downloaded file is, for example:

        ** cd Downloads**

Then install the package:

        **sudo yum localinstall perl-Games-Axmud-X.Y.ZZZ.noarch.rpm**

You must replace the **X.Y.ZZZ** with the actual version number you've downloaded, for example:

        **sudo yum localinstall perl-Games-Axmud-1.2.345.noarch.rpm**

When installation is complete, start Axmud by typing:

        **axmud.pl**

5.3 Installation on Linux from source
-------------------------------------

Manual installation is quite simple on most modern Linux systems.

This document contains complete instruction for some of the most popular distros:

- Arch-based systems (such as Arch Linux)
- Debian-based systems (such as Debian, Ubuntu and Linux Mint)
- Fedora
- Manjaro
- openSUSE (see below)
- Red Hat Enterprise Linux and CentOS

Axmud v1.2.0 (and later versions) cannot easily be easily installed on openSUSE, as the required graphics library (Gtk3) is not yet available through openSUSE's software repositories. We suggest that you continue using Axmud v1.1.405 for the time being.

5.3.1 Installation on Arch-based systems
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

(These instructions have been tested on Arch Linux. For Manjaro, see the section below.)

First, download the source code from the Axmud website (the most recent file ending .tar.gz).

Open a terminal window and navigate to the directory containing the downloaded file, for example:

        **cd Downloads**

Decompress the .tar.gz file:

        **tar -pzxvf Games-Axmud-X.Y.ZZZ.tar.gz**
        **cd Games-Axmud-X.Y.ZZZ**

You must replace the **X.Y.ZZZ** with the actual version number you've downloaded, for example:

        **tar -pzxvf Games-Axmud-1.2.345.tar.gz**
        **cd Games-Axmud-1.2.345**

Make sure you have the right dependencies:

        **sudo pacman -S gtk3 perl-gtk3 goocanvas wmctrl**
        **sudo pacman -S perl-cpanplus-dist-arch**
        **setupdistarch**
        **sudo cpanp i Archive::Zip File::Copy::Recursive File::HomeDir File::ShareDir File::ShareDir::Install Glib Gtk3 GooCanvas2 IO::Socket::INET6 IPC::Run JSON Math::Round Net::OpenSSH Path::Tiny Regexp::IPv6**

At the time of writing, there are some issues with installing certain libraries on Arch. If you know that those issues have been fixed, you can type this command to allow Axmud to use SSL connections:

        **sudo cpanp i IO::Socket::SSL**

If you want to use sound effects and/or text-to-speech, you should also type:

        **sudo pacman -S sox timidity++ espeak-ng**

Then install Axmud itself:

        **perl Makefile.PL**
        **make**
        **sudo make install**

When installation is complete, start Axmud by typing:

        **axmud.pl**

Axmud's default text-to-speech engine is eSpeak but, at the time of writing, there are some issues with its installation on Arch systems. Assuming that an alternative speech engine has been installed using the instructions just above, visually-impaired users should start Axmud by typing this, the first time:

        **baxmud.pl esng**

Once Axmud has started, type the following commands, which replace Axmud's default speech engine with espeak-ng:

        **;config all engine esng**
        **;save**

Thereafter, visually-impaired users can start Axmud by typing:

        **baxmud.pl**

5.3.2 Installation on Debian-based systems
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

(These instructions have been tested on Debian, Ubuntu and Linux Mint.)

First, download the source code from the Axmud website (the most recent file ending .tar.gz).

Open a terminal window and navigate to the directory containing the downloaded file, for example:

        **cd Downloads**

Decompress the .tar.gz file:

        **tar -pzxvf Games-Axmud\*.tar.gz**

        **cd Games-Axmud**\*

Make sure you have the right dependencies:

        **sudo apt-get update**
        **sudo apt-get install build-essential libgtk3-perl libgoocanvas-2.0-dev wmctrl**
        **sudo cpan install Archive::Extract File::HomeDir File::ShareDir File::ShareDir::Install GooCanvas2 JSON Math::Round Net::OpenSSH Path::Tiny Regexp::IPv6**

If you want to use sound effects and/or text-to-speech, you should also type:

        **sudo apt-get install libsox-fmt-all timidity**

Then install Axmud itself:

        **perl Makefile.PL**
        **make**
        **sudo make install**

When installation is complete, start Axmud by typing:

        **axmud.pl**

5.3.3 Installation on Fedora
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First, download the source code from the Axmud website (the most recent file ending .tar.gz).

Open a terminal window and navigate to the directory containing the downloaded file, for example:

        **cd Downloads**

Decompress the .tar.gz file:

        **tar -pzxvf Games-Axmud-X.Y.ZZZ.tar.gz**
        **cd Games-Axmud-X.Y.ZZZ**

You must replace the X.Y.ZZZ with the actual version number you've downloaded, for example:

        **tar -pzxvf Games-Axmud-1.2.345.tar.gz**
        **cd Games-Axmud-1.2.345**

Make sure you have the right dependencies:

        **sudo rpm --import http://li.nux.ro/download/nux/RPM-GPG-KEY-nux.ro**
        **sudo rpm -Uvh http://li.nux.ro/download/nux/dextop/el7/x86_64/nux-dextop-release-0-1.el7.nux.noarch.rpm**
        **sudo dnf install cpan**
        **sudo dnf install 'perl(Archive::Extract)' 'perl(File::Copy::Recursive)' 'perl(File::Fetch)' 'perl(File::HomeDir)' 'perl(File::ShareDir)' 'perl(File::ShareDir::Install)' 'perl(Glib)' 'perl(Gtk3)' 'perl(GooCanvas2)' 'perl(IO::Socket::INET6)' 'perl(IPC::Run)' 'perl(JSON)' 'perl(Math::Round)' 'perl(Net::OpenSSH)' 'perl(Path::Tiny)' 'perl(Regexp::IPv6)' 'perl(Time::Piece)'**

If you want to use sound effects and/or text-to-speech, you should also type:

        **sudo dnf install sox timidity++**

Then install Axmud itself:

        **perl Makefile.PL**
        **make**
        **sudo make install**

When installation is complete, start Axmud by typing:

        **axmud.pl**

5.3.4 Installation on Manjaro
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Manjaro's rolling release version is affected by a recurring issue (Perl modules are not updated when the Perl itself is updated, meaning that any Perl applications will immediately stop working). If you're using the rolling release
version, consider installing via `Perl homebrew <https://perlbrew.pl/>`__ instead.

These instructions work on both the stable and rolling releases of Manjaro.

First, download the source code from the Axmud website (the most recent file ending .tar.gz).

Open a terminal window and navigate to the directory containing the downloaded file, for example:

        **cd Downloads**

Decompress the .tar.gz file:

        **tar -pzxvf Games-Axmud-X.Y.ZZZ.tar.gz**
        **cd Games-Axmud-X.Y.ZZZ**

You must replace the X.Y.ZZZ with the actual version number you've downloaded, for example:

        **tar -pzxvf Games-Axmud-1.2.345.tar.gz**
        **cd Games-Axmud-1.2.345**

Make sure you have the right dependencies:

        **sudo pacman -S base-devel gtk3 goocanvas perl-gtk3 perl-goocanvas2 wmctrl cpanminus**
        **sudo cpanm Archive::Extract File::Copy::Recursive File::HomeDir File::ShareDir File::ShareDir::Install Glib IO::Socket::INET6 IO::Socket::SSL IPC::Run JSON Math::Round Net::OpenSSH Path::Tiny Regexp::IPv6**
        **sudo cpanm Archive::Zip --force**

If you want to use sound effects and/or text-to-speech, you should also type:

        **sudo pacman -S sox timidity++**

Then install Axmud itself:

        **perl Makefile.PL**
        **make**
        **sudo make install**

When installation is complete, start Axmud by typing:

        **axmud.pl**

5.3.5 Installation on openSUSE
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Axmud v1.2.0 (and later versions) cannot easily be easily installed on openSUSE, as the required graphics library (Gtk3) is not yet available through openSUSE's software repositories. We suggest that you continue using Axmud v1.1.405 for the time being.

5.3.6 Installation on Red Hat Enterprise Linux / CentOS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First, download the source code from the Axmud website (the most recent file ending .tar.gz).

Open a terminal window and navigate to the directory containing the downloaded file, for example:

        **cd Downloads**

Decompress the .tar.gz file:

        **tar -pzxvf Games-Axmud-X.Y.ZZZ.tar.gz**
        **cd Games-Axmud-X.Y.ZZZ**

You must replace the X.Y.ZZZ with the actual version number you've downloaded, for example:

        **tar -pzxvf Games-Axmud-1.2.345.tar.gz**
        **cd Games-Axmud-1.2.345**

Now we need to add an extra repository. First get the key:

        **sudo rpm --import http://li.nux.ro/download/nux/RPM-GPG-KEY-nux.ro**

Then add the repository. On CentOS/RHEL 6, do this:

        **sudo rpm -Uvh http://li.nux.ro/download/nux/dextop/el6/x86_64/nux-dextop-release-0-2.el6.nux.noarch.rpm**

On CentOS/RHEL 7, do this:

        **sudo rpm -Uvh http://li.nux.ro/download/nux/dextop/el7/x86_64/nux-dextop-release-0-1.el7.nux.noarch.rpm**

Now make sure you have the right dependencies:

        **sudo yum groupinstall 'Development Tools'**
        **sudo yum install epel-release cpan goocanvas2 wmctrl**
        **sudo yum install 'perl(Archive::Extract)' 'perl(Archive::Tar)' 'perl(Archive::Zip)' 'perl(File::Copy::Recursive)' 'perl(File::Fetch)' 'perl(File::HomeDir)' 'perl(File::ShareDir)' 'perl(File::ShareDir::Install)' 'perl(Glib)' 'perl(Gtk3)' 'perl(IO::Socket::INET6)' 'perl(IPC::Run)' 'perl(JSON)' 'perl(Math::Round)' 'perl(Net::OpenSSH)' 'perl(Path::Tiny)' 'perl(Regexp::IPv6)' 'perl(Time::Piece)'**
        **sudo cpan install GooCanvas2**

If you want to use sound effects and/or text-to-speech, you should also type:

        **sudo yum install sox libtimidity**

Then install Axmud itself:

        **perl Makefile.PL**
        **make**
        **sudo make install**

When installation is complete, start Axmud by typing:

        **axmud.pl**

6 Installation ON BSD
=====================

Manual installation using the source code is quite simple on BSD. (At the time of writing, no installer is available).

6.1 Installation on GhostBSD
----------------------------

(These instructions have been tested on GhostBSD, which is based on FreeBSD. It's likely that installation instructions are the same or very similar on all distros based on FreeBSD, OpenBSD or NetBSD.)

Open a terminal window and navigate to the directory containing the downloaded file, for example:

        **cd Downloads**

Decompress the .tar.gz file:

        **tar -pzxvf Games-Axmud-X.Y.ZZZ.tar.gz**
        **cd Games-Axmud-X.Y.ZZZ**

You must replace the X.Y.ZZZ with the actual version number you've downloaded, for example:

        **tar -pzxvf Games-Axmud-1.2.345.tar.gz**
        **cd Games-Axmud-1.2.345**

Make sure you have the right dependencies:

        **sudo pkg install goocanvas2 wmctrl**
        **sudo cpan install Archive::Extract Archive::Zip File::Copy::Recursive File::HomeDir File::ShareDir File::ShareDir::Install Glib Gtk3 GooCanvas2 IO::Socket::INET6 IO::Socket::SSL IPC::Run JSON Math::Round Net::OpenSSH Path::Tiny Regexp::IPv6**

If you want to use sound effects and/or text-to-speech, you should also type:

        **sudo pkg install sox timidity++**

Then install Axmud itself:

        **perl Makefile.PL**
        **make**
        **sudo make install**

When installation is complete, start Axmud by typing:

        **axmud.pl**

7 List of pre-configured worlds
===============================

Axmud can be used with any world that supports telnet, SSH or SSL connections. The following pre-configured worlds have already been set up to use the automapper, handle connections and so on.

- `3-Kingdoms <http://www.3k.org/>`__ (`Mudstats page <http://mudstats.com/World/3-Kingdoms>`__)
- `3-Scapes <http://www.3k.org/about3s.php>`__ (`Mudstats page <http://mudstats.com/World/3Scapes>`__)
- `4Dimensions <http://4dimensions.org/>`__ (`Mudstats page <http://mudstats.com/World/4Dimensions>`__)
- `Aardwolf MUD <http://www.aardwolf.com/>`__ (`Mudstats page <http://mudstats.com/World/AardwolfMUD>`__)
- `Achaea, Dreams of Divine Lands <http://www.achaea.com/>`__ (`Mudstats page <http://mudstats.com/World/Achaea,DreamsofDivineLands>`__)
- `Adventures Unlimited <https://tharel.net/>`__ (`Mudstats page <http://mudstats.com/World/AdventuresUnlimited>`__)
- `Aetolia, the Midnight Age <http://www.aetolia.com/>`__ (`Mudstats page <http://mudstats.com/World/Aetolia,theMidnightAge>`__)
- `Age of Chaos <http://aoc.pandapub.com/>`__ (`Mudstats page <http://mudstats.com/World/AgeofChaos>`__)
- `Alter Aeon <http://alteraeon.com/>`__ (`Mudstats page <http://mudstats.com/World/AlterAeon>`__)
- `Ancient Anguish <http://ancient.anguish.org/>`__ (`Mudstats page <http://mudstats.com/World/AncientAnguish>`__)
- `Archipelago MUD <http://the-firebird.net:8004/>`__ (`Mudstats page <http://mudstats.com/World/ArchipelagoMUD>`__)
- `ArcticMud <http://arcticmud.org/>`__ (`Mudstats page <http://mudstats.com/World/ArticMUD>`__)
- `Avalon (Germany) <http://avalon.mud.de/>`__ (`Mudstats page <http://mudstats.com/World/Avalon(Germany)>`__)
- `Avalon: The Legend Lives <http://www.avalon-rpg.com/>`__ (`Mudstats page <http://mudstats.com/World/Avalon,TheLegendLives>`__)
- `Avatar MUD <http://www.outland.org/>`__ (`Mudstats page <http://mudstats.com/World/AVATARMud>`__)
- `BatMUD <http://www.bat.org/>`__ (`Mudstats page <http://mudstats.com/World/BatMUD>`__)
- `Bedlam <http://bedlam.mudportal.com/>`__ (`Mudstats page <http://mudstats.com/World/Bedlam>`__)
- `Burning MUD <http://burningmud.com/>`__ (`Mudstats page <http://mudstats.com/World/BurningMUD>`__)
- `Bylins MUD <http://www.bylins.su/>`__
- `CLOK <http://wiki.contrarium.net/index.php?title=Main_Page>`__ (`Mudstats page <http://mudstats.com/World/CLOK>`__)
- `Carrion Fields <http://www.carrionfields.net/>`__ (`Mudstats page <http://mudstats.com/World/CarrionFields>`__)
- `Clessidra MUD <http://www.clessidra.it/>`__ (`Top Mud Sites page <http://www.topmudsites.com/forums/muddisplay.php?s=97c4b801dd5c8dc5fc88f00334c3a3eb&amp;mudid=jokerclex>`__)
- `CoffeeMud <coffeemud.net>`__ (`Mudstats page <http://mudstats.com/World/BLANK>`__)
- `Cryosphere <http://cryosphere.net/>`__ (`Mudstats page <http://mudstats.com/World/Cryosphere>`__)
- `CyberASSAULT <http://www.cyberassault.org/>`__ (`Mudstats page <http://mudstats.com/World/CyberASSAULT>`__)
- `Dark Realms: City of Syne <http://darkrealmscos.com/>`__
- `Dark and Shattered Lands <http://www.dsl-mud.org/>`__ (`Mudstats page <http://mudstats.com/World/DarkandShatteredLands>`__)
- `DartMUD <http://dartmud.com>`__ (`Mudstats page <http://mudstats.com/World/Dartmud>`__)
- `Dawn <http://dawnmud.com/>`__ (`Mudstats page <http://mudstats.com/World/Dawn>`__)
- `Dead Souls Dev <http://dead-souls.net/>`__ (`Mudstats page <http://mudstats.com/World/DeadSoulsPrime>`__)
- `Dead Souls Local <http://dead-souls.net/>`__ (`Mudstats page <http://mudstats.com/World/DeadSoulsPrime>`__)
- `Dead Souls Prime <http://dead-souls.net/>`__ (`Mudstats page <http://mudstats.com/World/DeadSoulsPrime>`__)
- `Discworld MUD <http://discworld.starturtle.net/lpc/>`__ (`Mudstats page <http://mudstats.com/World/DiscworldMUD>`__)
- `Dragon Swords <http://www.dragonswordsmud.com/>`__ (`Mudstats page <http://mudstats.com/World/DragonSwordsMUD>`__)
- `DragonStone <http://www.garbledtransmissions.com/dragonstone>`__ (`Mudstats page <http://mudstats.com/World/DragonStone>`__)
- `DuneMUD <http://www.dunemud.com/>`__ (`Mudstats page <http://mudstats.com/World/DuneMUD>`__)
- `Duris: Land of BloodLust <http://www.durismud.com/>`__ (`Mudstats page <http://mudstats.com/World/DurisLandofBloodLust>`__)
- `Elephant MUD <http://www.elephant.org/>`__ (`Mudstats page <http://mudstats.com/World/ElephantMud>`__)
- `Elysium RPG <http://www.elysium-rpg.com/wiki/Main_Page>`__ (`Top Mud Sites page <http://www.topmudsites.com/forums/muddisplay.php?mudid=elysium>`__)
- `EmpireMUD 2.0 <https://empiremud.net/>`__ (`Mudstats page <http://mudstats.com/World/EmpireMUD20>`__)
- `End of the Line <http://www.eotl.org/>`__ (`Mudstats page <http://mudstats.com/World/EndoftheLine>`__)
- `Eternal Darkness <eternaldarkness.net>`__ (`Mudstats page <http://mudstats.com/World/2001sEternalDarkness>`__)
- `Forest's Edge <https://theforestsedge.com/>`__
- `Forgotten Kingdoms <http://www.forgottenkingdoms.org/>`__ (`Mudstats page <http://mudstats.com/World/ForgottenKingdoms>`__)
- `Genesis <https://www.genesismud.org/>`__ (`Mudstats page <http://mudstats.com/World/Genesis>`__)
- `Godwars: Rebirth of Apocalypse <http://www.godwars.net/~apoc/>`__ (`Mudstats page <http://mudstats.com/World/GodWarsRebirthOfApocalypse>`__)
- `GreaterMUD <http://greatermud.com/>`__ (`Mudstats page <http://mudstats.com/World/GreaterMUD>`__)
- `HellMOO <http://hellmoo.org/>`__ (`Mudstats page <http://mudstats.com/World/HellMOO>`__)
- `HexOnyx <http://mud.hexonyx.com/>`__ (`Top Mud Sites page <http://www.topmudsites.com/forums/muddisplay.php?mudid=albus>`__)
- `HolyQuest <http://www.holyquest.org/>`__ (`Mudstats page <http://mudstats.com/World/HolyQuest>`__)
- `Iberia MUD <http://iberiamud.mooo.com/>`__ (`Mudstats page <http://mudstats.com/World/IberiaMUD>`__)
- `Icesus <http://www.icesus.org/>`__ (`Mudstats page <http://mudstats.com/World/Icesus>`__)
- `ifMUD <http://allthingsjacq.com/ifMUDfaq/>`__ (`Mudstats page <http://mudstats.com/World/ifMUD>`__)
- `Imperian: Sundered Heavens <http://www.imperian.com/>`__ (`Mudstats page <http://mudstats.com/World/ImperianTheSunderedHeavens>`__)
- `Islands <http://islands-game.wikia.com/wiki/Paanau_Ariki_Islands_Wiki>`__ (`Mudstats page <http://mudstats.com/World/BLANK>`__)
- `LambdaMOO <http://lambda.moo.mud.org/>`__ (`Mudstats page <http://mudstats.com/World/LambdaMOO>`__)
- `LegendMUD <https://www.legendmud.org/>`__ (`Mudstats page <http://mudstats.com/World/LegendMUD>`__)
- `Legends of Kallisti <http://www.legendsofkallisti.com/>`__ (`Mudstats page <http://mudstats.com/World/KallistiMUD>`__)
- `Lost Souls <http://lostsouls.org/>`__ (`Mudstats page <http://mudstats.com/World/BLANK>`__)
- `Lowlands <http://lolamud.net/>`__
- `Luminari MUD <http://www.luminarimud.com/>`__ (`Mudstats page <http://mudstats.com/World/LuminariMUD>`__)
- `Lusternia: Age of Ascension <http://www.lusternia.com/>`__ (`Mudstats page <http://mudstats.com/World/Lusternia>`__)
- `MUD1 (British Legends) <http://www.british-legends.com>`__ (`Mudstats page <http://mudstats.com/World/Multi-UserDungeon(BritishLegends)>`__)
- `MUD2 (Canadian server) <http://www.mud2.com/>`__ (`Mudstats page <http://mudstats.com/World/MUD2>`__)
- `MUD2 (UK server) <http://www.mudii.co.uk/>`__ (`Mudstats page <http://mudstats.com/World/MUDII>`__)
- `MUME - Multi Users In Middle Earth <http://mume.org/>`__ (`Mudstats page <http://mudstats.com/World/MUME-MultiUsersInMiddleEarth>`__)
- `Materia Magica <http://www.materiamagica.com/>`__ (`Mudstats page <http://mudstats.com/World/MateriaMagica>`__)
- `Medievia <http://www.medievia.com>`__ (`Mudstats page <http://mudstats.com/World/Medievia>`__)
- `Merentha <http://merentha.com/>`__ (`Mudstats page <http://mudstats.com/World/Merentha>`__)
- `Midnight Sun <http://midnightsun2.org:3328/>`__ (`Mudstats page <http://mudstats.com/World/MidnightSunII>`__)
- `Miriani <https://www.toastsoft.net/>`__ (`Mudstats page <http://mudstats.com/World/Miriani>`__)
- `MorgenGrauen <http://mg.mud.de/>`__ (`Mudstats page <http://mudstats.com/World/MorgenGrauen>`__)
- `NannyMUD <http://www.lysator.liu.se/nanny/>`__ (`Mudstats page <http://mudstats.com/World/NannyMUD>`__)
- `Nanvaent <http://www.nanvaent.org/>`__ (`Mudstats page <http://mudstats.com/World/Nanvaent>`__)
- `New Worlds: Ateraan <http://ateraan.com/>`__ (`Mudstats page <http://mudstats.com/World/NewWorldsAteeran>`__)
- `Nodeka <http://www.nodeka.com/>`__ (`Mudstats page <http://mudstats.com/World/Nodeka>`__)
- `Nuclear War <http://nuclearwarmudusa.com>`__ (`Mudstats page <http://mudstats.com/World/NuclearWar>`__)
- Penultimate Destination (`Mudstats page <http://mudstats.com/World/PenultimateDestination>`__)
- `Pict MUD <pict.genesismuds.com>`__ (`Mudstats page <http://mudstats.com/World/Pict>`__)
- `RavenMUD <http://ravenmud.com/>`__ (`Mudstats page <http://mudstats.com/World/RavenMUD>`__)
- `Realms of Despair <http://www.realmsofdespair.com/>`__ (`Mudstats page <http://mudstats.com/World/RealmsofDespair>`__)
- `Realms of Wonder <https://mud.killerpcs.com/>`__ (`Top Mud Sites page <http://www.topmudsites.com/forums/muddisplay.php?s=8215145c2d9a5688d8929d0d6df845f0&mudid=realmsofwonder>`__)
- `RealmsMUD <http://realmsmud.org/>`__ (`Mudstats page <http://mudstats.com/World/Realmsmud>`__)
- `Reinos de Leyenda <https://www.reinosdeleyenda.es/>`__ (`Mudstats page <http://mudstats.com/World/ReinosdeLeyenda(ElRenacimiento)>`__)
- `RetroMUD <http://www.retromud.org/>`__ (`Mudstats page <http://mudstats.com/World/RetroMUD>`__)
- `RoninMUD <http://roninmud.org/>`__ (`Mudstats page <http://mudstats.com/World/RoninMUD>`__)
- `Rupert <http://rupert.twyst.org/>`__ (`Mudstats page <http://mudstats.com/World/Rupert>`__)
- `SlothMUD III <http://www.slothmud.org>`__ (`Mudstats page <http://mudstats.com/World/SlothMUDIII>`__)
- `Star Wars Mud <http://www.swmud.org/>`__ (`Mudstats page <http://mudstats.com/World/StarWarsMud(SWmud)>`__)
- `StickMUD <http://stickmud.com/index.php/Home>`__ (`Mudstats page <http://mudstats.com/World/BLANK>`__)
- `Stonia <http://stonia.ttu.ee/>`__ (`Top Mud Sites page <http://www.topmudsites.com/forums/mudinfo-cham.html>`__)
- `Tempora Heroica <http://www.ibiblio.org/TH/>`__ (`Mudstats page <http://mudstats.com/World/TemporaHeroica>`__)
- `The Inquisition: Legacy <https://ti-legacy.com/>`__ (`Mudstats page <http://mudstats.com/World/TheInquisitionLegacy>`__)
- The Land (`Mudstats page <http://mudstats.com/World/TheLand>`__)
- `The Two Towers <http://www.t2tmud.org/>`__ (`Mudstats page <http://mudstats.com/World/TheTwoTowersMUD>`__)
- `The Unofficial SquareSoft MUD <http://uossmud.sandwich.net/>`__ (`Mudstats page <http://mudstats.com/World/TheUnofficialSquaresoftMUD>`__)
- `The Wheel of Time MUD <http://www.wotmud.org>`__ (`Mudstats page <http://mudstats.com/World/WheelofTime>`__)
- `TorilMUD <http://www.torilmud.org/>`__ (`Mudstats page <http://mudstats.com/World/TorilMud,theSojournersHome>`__)
- `Tsunami <http://www.thebigwave.net/index.php>`__ (`Mudstats page <http://mudstats.com/World/Tsunami>`__)
- `Valhalla MUD <http://www.valhalla.com/>`__ (`Mudstats page <http://mudstats.com/World/ValhallaMUD>`__)
- `Viking MUD <http://www.vikingmud.org>`__ (`Mudstats page <http://mudstats.com/World/VikingMUD>`__)
- `Waterdeep <http://www.waterdeep.org/>`__ (`Mudstats page <http://mudstats.com/World/Waterdeep>`__)
- `ZombieMUD <http://zombiemud.org/>`__ (`Mudstats page <http://mudstats.com/World/ZombieMUD>`__)

8 Contributing
==============

- Report a bug: Use the Github `issues <https://github.com/axcore/tartube/issues>`__ page, or visit the `Axmud forum <https://axmud.sourceforge.io/forum/index.php>`__

9 Authors
=========

See the `AUTHORS <AUTHORS>`__ file.

10 License
==========

Axmud is licensed under the `GNU General Public License v3.0 <https://www.gnu.org/licenses/gpl-3.0.en.html>`__.

✨🍰✨
