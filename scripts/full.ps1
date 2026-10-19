param(
    [string]$WorkDir,
    [switch]$Inspect,
    [switch]$Stop,
    [Parameter(ValueFromRemainingArguments=$true)][string[]]$ClaudeArgs
)
. "$PSScriptRoot\env.ps1"
. "$PSScriptRoot\protect-runtime.ps1"
$python = "$ProjectRoot\.venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) { throw 'Run Setup.cmd first.' }
$options = @()
if ($WorkDir) { $options += @('--workdir', $WorkDir) }
if ($Inspect) { $options += '--inspect' }
if ($Stop) { $options += '--stop' }
& $python "$PSScriptRoot\full_mode_v2.py" @options -- @ClaudeArgs
exit $LASTEXITCODE
