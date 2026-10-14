@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\project.ps1" -Action claude
pause
