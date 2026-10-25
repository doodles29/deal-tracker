@echo off
cd /d "%~dp0"
"%LOCALAPPDATA%\Programs\Python\Python312\python.exe" check.py >> check.log 2>&1
