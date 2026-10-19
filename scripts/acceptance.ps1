param([switch]$Run, [switch]$Mcp)
. "$PSScriptRoot\env.ps1" -InspectOnly
if ($ProjectClaude) { $env:NOTION_CLAUDE_EXE = $ProjectClaude }
. "$PSScriptRoot\protect-runtime.ps1"
$options = @()
if ($Run) { $options += '--run' }
if ($Mcp) { $options += '--mcp' }
& "$ProjectRoot\.venv\Scripts\python.exe" "$PSScriptRoot\acceptance.py" @options
exit $LASTEXITCODE
