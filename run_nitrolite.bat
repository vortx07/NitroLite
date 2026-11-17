@echo off
title Starting NitroLite...
cd /d "%~dp0"
if exist "NitroLite.exe" (
    start "" "NitroLite.exe"
) else (
    start "" pythonw main.py
)
exit
