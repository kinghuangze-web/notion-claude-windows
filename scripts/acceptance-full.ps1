param([switch]$Run, [switch]$Mcp)
. "$PSScriptRoot\env.ps1"
. "$PSScriptRoot\protect-runtime.ps1"
$options = @()
if ($Run) { $options += '--run' }
if ($Mcp) { $options += '--mcp' }
& "$ProjectRoot\.venv\Scripts\python.exe" "$PSScriptRoot\acceptance_v2.py" @options
exit $LASTEXITCODE
