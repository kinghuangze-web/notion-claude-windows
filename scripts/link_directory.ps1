param([Parameter(Mandatory=$true)][string]$LinkPath,[Parameter(Mandatory=$true)][string]$SourcePath)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $SourcePath -PathType Container)) { throw 'Source directory missing' }
if (Test-Path -LiteralPath $LinkPath) { throw 'Link destination already exists' }
New-Item -ItemType Junction -Path $LinkPath -Target $SourcePath | Out-Null
