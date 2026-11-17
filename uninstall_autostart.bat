@echo off
title Uninstall NitroLite from Windows Startup
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "NitroLite" /f
echo [OK] NitroLite has been removed from Windows Startup.
pause
