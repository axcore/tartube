@echo off
..\..\..\usr\bin\mintty.exe -w hide /bin/env MSYSTEM=MINGW32 /bin/bash -lc /home/user/tartube/tartube_mswin.sh
echo ============================
echo welcome to Tartube 
echo ============================
timeout 5 > NUL
echo %time%
