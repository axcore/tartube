@echo off
start ..\..\..\usr\bin\mintty.exe -w hide /bin/env MSYSTEM=MINGW32 /bin/bash -lc /home/user/tartube/tartube_mswin.sh
start ..\..\..\usr\bin\mintty.exe -w hide /bin/env MSYSTEM=MINGW64 /bin/bash -lc /home/user/tartube/tartube_mswin.sh
title Tartube
echo ============================
echo welcome to Tartube
echo ============================
timeout 5 > NUL
echo %time%