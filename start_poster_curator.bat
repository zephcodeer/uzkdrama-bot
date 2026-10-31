@echo off
title Poster Curator Studio
cd /d "%~dp0"
echo ==================================================
echo   PUBLIC - POSTER CURATOR STUDIO ISHGA TUSHMOQDA...
echo ==================================================
start http://localhost:8765/poster_curator.html
python scripts/curator_server.py
pause
