param([switch]$InspectOnly)
# Process-local paths. Resolve installed tools before redirecting application data.
$ErrorActionPreference = 'Stop'
$ProjectRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$ProjectGo = $null
$ProjectPython = $null
$ProjectClaude = $null
$ProjectBash = $null
$localTools = Join-Path $ProjectRoot 'tools.local.ps1'
if (Test-Path -LiteralPath $localTools) { . $localTools }
function Find-ProjectTool([string]$Name, [string[]]$Fallbacks) {
    $found = Get-Command $Name -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) { return $found.Source }
    foreach ($candidate in $Fallbacks) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) { return $candidate }
    }
    return $null
}
if (-not $ProjectGo) { $ProjectGo = Find-ProjectTool 'go.exe' @("$env:ProgramFiles\Go\bin\go.exe") }
if (-not $ProjectClaude) { $ProjectClaude = Find-ProjectTool 'claude.exe' @("$env:USERPROFILE\.local\bin\claude.exe") }
if (-not $ProjectBash) { $ProjectBash = Find-ProjectTool 'bash.exe' @("$env:ProgramFiles\Git\bin\bash.exe", "$env:LOCALAPPDATA\Programs\Git\bin\bash.exe") }
# Prefer Git for Windows over a WSL bash executable found on PATH.
foreach ($candidate in @("$env:ProgramFiles\Git\bin\bash.exe", "$env:LOCALAPPDATA\Programs\Git\bin\bash.exe")) {
    if (-not (Test-Path -LiteralPath $localTools) -and (Test-Path -LiteralPath $candidate)) { $ProjectBash = $candidate; break }
}
if (-not $ProjectPython) {
    $launcher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($launcher) {
        $resolved = & $launcher.Source -3 -c 'import sys; print(sys.executable)' 2>$null
        if ($LASTEXITCODE -eq 0 -and $resolved) { $ProjectPython = ($resolved | Select-Object -Last 1).Trim() }
    }
    if (-not $ProjectPython) { $ProjectPython = Find-ProjectTool 'python.exe' @() }
}
# Preflight reuses discovery without changing environment variables or making directories.
if ($InspectOnly) { return }
$projectEnvironment = @{
    GOPATH = "$ProjectRoot\_cache\go-path"
    GOMODCACHE = "$ProjectRoot\_cache\go-mod"
    GOCACHE = "$ProjectRoot\_cache\go-build"
    GOTMPDIR = "$ProjectRoot\_tmp\go"
    GOENV = 'off'
    GOTOOLCHAIN = 'local'
    GIT_TERMINAL_PROMPT = '0'
    PIP_CACHE_DIR = "$ProjectRoot\_cache\pip"
    PIP_DISABLE_PIP_VERSION_CHECK = '1'
    PYTHONUTF8 = '1'
    PYTHONIOENCODING = 'utf-8'
    PYTHONPYCACHEPREFIX = "$ProjectRoot\_cache\pycache"
    TEMP = "$ProjectRoot\_tmp"
    TMP = "$ProjectRoot\_tmp"
    TMPDIR = "$ProjectRoot\_tmp"
    APPDATA = "$ProjectRoot\runtime\appdata\Roaming"
    LOCALAPPDATA = "$ProjectRoot\runtime\appdata\Local"
    XDG_CACHE_HOME = "$ProjectRoot\_cache\xdg"
    XDG_CONFIG_HOME = "$ProjectRoot\runtime\xdg-config"
    XDG_DATA_HOME = "$ProjectRoot\runtime\xdg-data"
    XDG_STATE_HOME = "$ProjectRoot\runtime\xdg-state"
    CLAUDE_CODE_TMPDIR = "$ProjectRoot\_tmp"
    CLAUDE_CODE_DEBUG_LOGS_DIR = "$ProjectRoot\logs\claude"
    CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC = '1'
    DISABLE_UPDATES = '1'
    DISABLE_AUTOUPDATER = '1'
    DO_NOT_TRACK = '1'
}
if ($ProjectBash) { $projectEnvironment.CLAUDE_CODE_GIT_BASH_PATH = $ProjectBash }
if ($ProjectClaude) { $projectEnvironment.NOTION_CLAUDE_EXE = $ProjectClaude }
foreach ($name in $projectEnvironment.Keys) {
    [Environment]::SetEnvironmentVariable($name, $projectEnvironment[$name], 'Process')
}
foreach ($path in @($env:GOPATH, $env:GOMODCACHE, $env:GOCACHE, $env:GOTMPDIR,
    $env:PIP_CACHE_DIR, $env:PYTHONPYCACHEPREFIX, $env:APPDATA, $env:LOCALAPPDATA,
    $env:XDG_CACHE_HOME, $env:XDG_CONFIG_HOME, $env:XDG_DATA_HOME, $env:XDG_STATE_HOME,
    $env:CLAUDE_CODE_DEBUG_LOGS_DIR,
    "$ProjectRoot\logs", "$ProjectRoot\evidence", "$ProjectRoot\demo")) {
    New-Item -ItemType Directory -Path $path -Force | Out-Null
}
