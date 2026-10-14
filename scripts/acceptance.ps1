param([switch]$Run)
. "$PSScriptRoot\env.ps1"
. "$PSScriptRoot\protect-runtime.ps1"
if ($Run) {
    & "$ProjectRoot\.venv\Scripts\python.exe" "$PSScriptRoot\manage.py" start
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & "$ProjectRoot\.venv\Scripts\python.exe" "$PSScriptRoot\acceptance.py" --run
} else { & "$ProjectRoot\.venv\Scripts\python.exe" "$PSScriptRoot\acceptance.py" }
exit $LASTEXITCODE
