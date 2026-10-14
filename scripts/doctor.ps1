. "$PSScriptRoot\env.ps1" -InspectOnly
$git = Get-Command git.exe -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
$paths = [ordered]@{go=$ProjectGo;python=$ProjectPython;claude=$ProjectClaude;git_bash=$ProjectBash;git=if ($git) { $git.Source } else { $null }}
$missing = @()
$tools = [ordered]@{}
foreach ($name in $paths.Keys) {
    $available = [bool]($paths[$name] -and (Test-Path -LiteralPath $paths[$name] -PathType Leaf))
    if ($name -eq 'python' -and $paths[$name] -like '*\WindowsApps\*') { $available = $false }
    $tools[$name] = @{available=$available;path=$paths[$name]}
    if (-not $available) { $missing += $name }
}
$arch = if ($env:PROCESSOR_ARCHITEW6432) { $env:PROCESSOR_ARCHITEW6432 } else { $env:PROCESSOR_ARCHITECTURE }
$supported = [Environment]::OSVersion.Platform -eq 'Win32NT' -and $arch -eq 'AMD64'
$state = if (-not $supported) { 'unsupported_platform' } elseif ($missing.Count) { 'missing_dependency' } else { 'ready_for_setup' }
[ordered]@{state=$state;tools=$tools;missing=$missing;version_checks='performed by setup.ps1';notion_inference_verified=$false} | ConvertTo-Json -Depth 5
if ($state -eq 'ready_for_setup') { exit 0 } else { exit 2 }
