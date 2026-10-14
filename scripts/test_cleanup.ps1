$ErrorActionPreference = 'Stop'
$project = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot)).TrimEnd('\')
$fixture = [IO.Path]::GetFullPath((Join-Path $project ('_tmp\cleanup-check-' + [Guid]::NewGuid().ToString('N'))))
if (-not $fixture.StartsWith($project + '\_tmp\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Fixture escaped its test directory.' }
New-Item -ItemType Directory -Path (Join-Path $fixture 'scripts'),(Join-Path $fixture 'runtime'),(Join-Path $fixture 'docs') -Force | Out-Null
Copy-Item -LiteralPath "$PSScriptRoot\cleanup.ps1" -Destination (Join-Path $fixture 'scripts\cleanup.ps1')
Copy-Item -LiteralPath "$PSScriptRoot\process-time.ps1" -Destination (Join-Path $fixture 'scripts\process-time.ps1')
Set-Content -LiteralPath (Join-Path $fixture '.project-id') -Value 'invalid-marker'
Set-Content -LiteralPath (Join-Path $fixture 'runtime\synthetic.txt') -Value 'synthetic-local-data'
Set-Content -LiteralPath (Join-Path $fixture 'docs\keep.txt') -Value 'preserved-deliverable'
$ErrorActionPreference = 'Continue'
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $fixture 'scripts\cleanup.ps1') -Execute 2>$null
$negativeCode = $LASTEXITCODE
$ErrorActionPreference = 'Stop'
if ($negativeCode -eq 0 -or -not (Test-Path -LiteralPath (Join-Path $fixture 'runtime\synthetic.txt'))) { throw 'Invalid project marker was accepted.' }
Set-Content -LiteralPath (Join-Path $fixture '.project-id') -Value 'notion-claude-windows-v1'
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $fixture 'scripts\cleanup.ps1')
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath (Join-Path $fixture 'runtime\synthetic.txt'))) { throw 'Preview changed fixture data.' }
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $fixture 'scripts\cleanup.ps1') -Execute
if ($LASTEXITCODE -ne 0 -or (Test-Path -LiteralPath (Join-Path $fixture 'runtime')) -or
    -not (Test-Path -LiteralPath (Join-Path $fixture 'docs\keep.txt'))) { throw 'Partial cleanup did not preserve the expected deliverable.' }
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $fixture 'scripts\cleanup.ps1') -Execute -RemoveProject
if ($LASTEXITCODE -ne 0 -or (Test-Path -LiteralPath $fixture)) { throw 'Full fixture cleanup failed.' }
Write-Output 'PASS: invalid marker refusal, unchanged preview, partial cleanup and full fixture cleanup.'
