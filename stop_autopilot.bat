@echo off
title Stop Autopilot Listener
cd /d "E:\Agent\Drama Bot"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "E:\Agent\Drama Bot\scripts\stop_autopilot.ps1"
ping 127.0.0.1 -n 4 >nul
exit /b 0
