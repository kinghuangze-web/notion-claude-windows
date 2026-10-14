@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\setup.ps1"
if errorlevel 1 (echo Setup failed. See the error above.) else (echo Setup complete.)
pause
