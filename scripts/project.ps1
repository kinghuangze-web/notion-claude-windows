param(
    [ValidateSet('init','start','stop','status','verify-local','claude')]
    [string]$Action = 'status',
    [string]$WorkDir,
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$ClaudeArgs
)
. "$PSScriptRoot\env.ps1"
. "$PSScriptRoot\protect-runtime.ps1"
$VenvPython = "$ProjectRoot\.venv\Scripts\python.exe"
if ($Action -eq 'claude') {
    & $VenvPython "$PSScriptRoot\manage.py" start
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    if (-not $WorkDir) { $WorkDir = "$ProjectRoot\demo" }
    if (-not (Test-Path -LiteralPath $WorkDir -PathType Container)) { throw 'Working directory does not exist.' }
    Set-Location -LiteralPath $WorkDir
    & $VenvPython "$PSScriptRoot\claude_notion.py" @ClaudeArgs
} else {
    & $VenvPython "$PSScriptRoot\manage.py" $Action
}
exit $LASTEXITCODE
