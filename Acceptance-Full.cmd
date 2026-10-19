@echo off
echo This runs real Notion AI requests and local file operations.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\acceptance-full.ps1" -Run
pause
