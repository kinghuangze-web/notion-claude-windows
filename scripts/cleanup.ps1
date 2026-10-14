param([switch]$Execute, [switch]$RemoveProject)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\process-time.ps1"
$cleanupRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot)).TrimEnd('\')
if ($cleanupRoot -eq [IO.Path]::GetPathRoot($cleanupRoot).TrimEnd('\') -or
    $cleanupRoot -eq $env:USERPROFILE -or $cleanupRoot -eq $env:ProgramFiles -or
    $cleanupRoot -eq $env:SystemRoot) { throw 'Refusing cleanup of a system or user root.' }
if ((Get-Item -LiteralPath $cleanupRoot).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Redirected project roots are not supported.' }
$marker = Join-Path $cleanupRoot '.project-id'
if (-not (Test-Path -LiteralPath $marker) -or (Get-Content -LiteralPath $marker -Raw).Trim() -ne 'notion-claude-windows-v1') { throw 'Project identity marker is missing or invalid.' }
$targets = if ($RemoveProject) { @($cleanupRoot) } else {
    @('runtime','_cache','_tmp','.venv','demo','_source') | ForEach-Object { Join-Path $cleanupRoot $_ }
}
foreach ($target in $targets) {
    $absolute = [IO.Path]::GetFullPath($target)
    if ($absolute -ne $cleanupRoot -and -not $absolute.StartsWith($cleanupRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Cleanup target escapes the project.' }
    Write-Output "Cleanup target: $absolute"
}
if (-not $Execute) { Write-Output 'Preview only. Use -Execute to remove these paths.'; exit 0 }
# Inspect each directory without traversing junctions, then refuse redirected targets.
$pending = New-Object 'System.Collections.Generic.Stack[string]'
foreach ($target in $targets) { if (Test-Path -LiteralPath $target) { $pending.Push($target) } }
while ($pending.Count) {
    $current = $pending.Pop()
    $item = Get-Item -LiteralPath $current -Force
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Redirected cleanup target: $current" }
    if ($item.PSIsContainer) {
        foreach ($child in Get-ChildItem -LiteralPath $current -Force) {
            if ($child.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Redirected cleanup entry: $($child.FullName)" }
            if ($child.PSIsContainer) { $pending.Push($child.FullName) }
        }
    }
}
$sessionRecords = Join-Path $cleanupRoot 'runtime\claude-processes'
if (Test-Path -LiteralPath $sessionRecords) {
    foreach ($file in Get-ChildItem -LiteralPath $sessionRecords -Filter '*.json') {
        $record = Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json
        $running = Get-CimInstance Win32_Process -Filter "ProcessId = $([int]$record.pid)"
        if ($running -and $running.ExecutablePath -eq $record.exe -and
            [Math]::Abs(([DateTimeOffset]$running.CreationDate).ToUnixTimeMilliseconds() - (Get-RecordedCreationMilliseconds $record.creation_date)) -lt 1000) {
            throw 'Close the recorded project Claude Code session before cleanup.'
        }
    }
}
$gatewayRecordPath = Join-Path $cleanupRoot 'runtime\gateway-process.json'
if (Test-Path -LiteralPath $gatewayRecordPath) {
    $record = Get-Content -LiteralPath $gatewayRecordPath -Raw | ConvertFrom-Json
    $expectedExe = Join-Path $cleanupRoot 'runtime\notion-manager.exe'
    if ([IO.Path]::GetFullPath($record.exe) -ne $expectedExe) { throw 'Gateway record has an unexpected executable.' }
    $running = Get-CimInstance Win32_Process -Filter "ProcessId = $([int]$record.pid)"
    if ($running) {
        if ($running.ExecutablePath -ne $expectedExe -or
            [Math]::Abs(([DateTimeOffset]$running.CreationDate).ToUnixTimeMilliseconds() - (Get-RecordedCreationMilliseconds $record.creation_date)) -ge 1000) { throw 'Gateway PID was reused; refusing to stop it.' }
        Stop-Process -Id ([int]$record.pid) -ErrorAction Stop
        $deadline = [DateTime]::UtcNow.AddSeconds(10)
        while (Get-CimInstance Win32_Process -Filter "ProcessId = $([int]$record.pid)") {
            if ([DateTime]::UtcNow -gt $deadline) { throw 'Gateway remains active; cleanup aborted.' }
            Start-Sleep -Milliseconds 100
        }
    }
}
foreach ($target in $targets) { if (Test-Path -LiteralPath $target) { Remove-Item -LiteralPath $target -Recurse -Force } }
Write-Output 'Cleanup complete. Existing Go/Git/Python/Claude installations were not removed.'
