@echo off
title Install NitroLite to Windows Startup
cd /d "%~dp0"

set APP_PATH=%~dp0NitroLite.exe
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "NitroLite" /t REG_SZ /d "\"%APP_PATH%\" --tray" /f

echo [OK] NitroLite.exe has been registered to start automatically with Windows (minimized to system tray)!
echo You can run uninstall_autostart.bat at any time to remove it.
pause
