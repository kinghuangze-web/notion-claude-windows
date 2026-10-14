@echo off
echo This runs five real Notion AI acceptance stages and uses your account allowance.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\acceptance.ps1" -Run
pause
