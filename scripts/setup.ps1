param([switch]$SkipTests)
. "$PSScriptRoot\env.ps1"
. "$PSScriptRoot\protect-runtime.ps1"
Set-Location -LiteralPath $ProjectRoot
if ((Test-Path -LiteralPath 'runtime\gateway-process.json') -or (Test-Path -LiteralPath 'runtime\full\gateway-process.json')) { throw 'Stop recorded project gateways with scripts/project.ps1 -Action stop before rebuilding.' }
foreach ($pair in @(@('Go',$ProjectGo),@('Python',$ProjectPython),@('Claude Code',$ProjectClaude),@('Git Bash',$ProjectBash))) {
    if (-not $pair[1] -or -not (Test-Path -LiteralPath $pair[1] -PathType Leaf)) {
        throw "Missing $($pair[0]). See README.md or tools.local.ps1.example."
    }
}
if (-not (Get-Command git.exe -ErrorAction SilentlyContinue)) { throw 'Git for Windows is not on PATH.' }
& $ProjectPython -c 'import sys; assert sys.version_info >= (3,11), "Python 3.11+ is required"'
if ($LASTEXITCODE -ne 0) { throw 'Python version check failed.' }
$version = & $ProjectGo version
if ($LASTEXITCODE -ne 0 -or $version -notmatch 'go(\d+)\.(\d+)') { throw 'Unable to read Go version.' }
if ([int]$Matches[1] -lt 1 -or ([int]$Matches[1] -eq 1 -and [int]$Matches[2] -lt 26)) { throw 'Go 1.26+ is required.' }
& $ProjectClaude --version
if ($LASTEXITCODE -ne 0) { throw 'Claude Code executable check failed.' }
# APPDATA was redirected above; this telemetry setting is local to the project.
& $ProjectGo telemetry off
if ($LASTEXITCODE -ne 0) { throw 'Unable to configure project-local Go telemetry.' }
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    & $ProjectPython -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed.' }
}
& .\.venv\Scripts\python.exe -m pip install --only-binary=:all: -r .\scripts\requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed.' }
$base = '2d6d3dc2fa74f929bd9a8ebd3c1569f5dcca1b88'
$source = Join-Path $ProjectRoot '_source'
if (-not (Test-Path -LiteralPath $source)) {
    & git init --quiet $source
    if ($LASTEXITCODE -ne 0) { throw 'Source initialization failed.' }
}
$head = & git -C $source rev-parse --verify --quiet HEAD
if ($LASTEXITCODE -ne 0) {
    & git -C $source -c credential.helper= fetch --depth 1 'https://github.com/SleepingBag945/notion_manager.git' $base
    if ($LASTEXITCODE -ne 0) { throw 'Pinned source download failed. Retry setup after checking GitHub connectivity.' }
    & git -C $source -c core.autocrlf=false checkout --detach $base
    if ($LASTEXITCODE -ne 0) { throw 'Pinned source checkout failed.' }
    $head = & git -C $source rev-parse HEAD
}
if ($head -ne $base) { throw 'Source commit differs from the pinned version; refusing to build.' }
& .\.venv\Scripts\python.exe .\scripts\apply_patches.py
if ($LASTEXITCODE -ne 0) { throw 'Pinned patch application failed; preserve local changes and inspect the error.' }
Push-Location -LiteralPath $source
try {
    & $ProjectGo build -trimpath -o "$ProjectRoot\runtime\notion-manager.exe" ./cmd/notion-manager
    if ($LASTEXITCODE -ne 0) { throw 'Gateway build failed.' }
    if (-not $SkipTests) {
        & $ProjectGo test ./... -skip '^TestAccountFilesUseOwnerOnlyPermissions$'
        if ($LASTEXITCODE -ne 0) { throw 'Applicable Go regression tests failed.' }
    }
} finally { Pop-Location }
$buildRecord = [ordered]@{
    transport = 'agent-session-v2'
    upstream = $base
    exe_sha256 = (Get-FileHash -LiteralPath "$ProjectRoot\runtime\notion-manager.exe" -Algorithm SHA256).Hash.ToLowerInvariant()
    patch_sha256 = (Get-FileHash -LiteralPath "$ProjectRoot\patches\opus55.patch" -Algorithm SHA256).Hash.ToLowerInvariant()
}
$buildRecord | ConvertTo-Json | Set-Content -LiteralPath "$ProjectRoot\runtime\build-info.json" -Encoding UTF8
& .\.venv\Scripts\python.exe .\scripts\manage.py init
if ($LASTEXITCODE -ne 0) { throw 'Local configuration initialization failed.' }
& .\.venv\Scripts\python.exe -m unittest discover -s scripts -p test_launcher.py -v
if ($LASTEXITCODE -ne 0) { throw 'Launcher checks failed.' }
& .\.venv\Scripts\python.exe -m unittest discover -s scripts -p test_readiness.py -v
if ($LASTEXITCODE -ne 0) { throw 'Readiness state checks failed.' }
& .\.venv\Scripts\python.exe -m unittest discover -s scripts -p test_patches.py -v
if ($LASTEXITCODE -ne 0) { throw 'Patch install and upgrade checks failed.' }
& .\.venv\Scripts\python.exe -m unittest discover -s scripts -p test_gateway_environment.py -v
if ($LASTEXITCODE -ne 0) { throw 'Ordinary route activation checks failed.' }
& .\.venv\Scripts\python.exe -m unittest discover -s scripts -p test_config_migration.py -v
if ($LASTEXITCODE -ne 0) { throw 'Configuration migration checks failed.' }
Write-Output 'Setup complete. Use scripts/project.ps1 -Action start, then follow README.md readiness and verification.'
