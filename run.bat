@echo off
rem Starts the Deal Tracker. Open http://localhost:5000 on this laptop,
rem or http://<this-laptop-ip>:5000 on a phone on the same wifi.
cd /d "%~dp0"
"%LOCALAPPDATA%\Programs\Python\Python312\python.exe" app.py
pause
