param(
    [ValidateSet('init','start','stop','status','ready','verify-local','claude')]
    [string]$Action = 'status',
    [string]$WorkDir,
    [Parameter(ValueFromRemainingArguments=$true)][string[]]$ClaudeArgs
)
if ($Action -eq 'claude') {
    . "$PSScriptRoot\env.ps1" -InspectOnly
    if (-not $ProjectClaude) { throw 'Native Claude Code CLI is missing.' }
    $env:NOTION_CLAUDE_EXE = $ProjectClaude
} else { . "$PSScriptRoot\env.ps1" }
. "$PSScriptRoot\protect-runtime.ps1"
$python = "$ProjectRoot\.venv\Scripts\python.exe"
if ($Action -eq 'stop' -and -not (Test-Path -LiteralPath $python)) {
    if ((Test-Path -LiteralPath "$ProjectRoot\runtime\gateway-process.json") -or (Test-Path -LiteralPath "$ProjectRoot\runtime\full\gateway-process.json")) { throw 'A recorded gateway exists but project Python is missing; verify ownership before recovery.' }
    Write-Output 'No recorded project gateway; nothing to stop.'
    exit 0
}
if ($Action -eq 'claude') {
    & $python "$PSScriptRoot\manage.py" start
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    if (-not $WorkDir) { throw 'Specify the actual user working directory with -WorkDir.' }
    if (-not (Test-Path -LiteralPath $WorkDir -PathType Container)) { throw 'Working directory does not exist.' }
    Set-Location -LiteralPath $WorkDir
    & $python "$PSScriptRoot\claude_full.py" @ClaudeArgs
} else { & $python "$PSScriptRoot\manage.py" $Action }
exit $LASTEXITCODE
