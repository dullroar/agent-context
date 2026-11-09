param(
    [Parameter(Mandatory = $true)] [string]$TestParent,
    [Parameter(Mandatory = $true)] [string]$Repo
)
# This test uses only --version/--help, never a model prompt or login.
$ErrorActionPreference = 'Stop'
$python = (Get-Command python -CommandType Application | Select-Object -First 1).Source
$claude = Get-Command claude -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
$copilot = Get-Command copilot -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
$testDir = Join-Path $TestParent ('setup-real-' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $testDir | Out-Null
$env:USERPROFILE = Join-Path $testDir 'profile'
$env:LOCALAPPDATA = Join-Path $env:USERPROFILE 'local'
$env:APPDATA = Join-Path $env:USERPROFILE 'roaming'
$env:CODEX_HOME = Join-Path $env:USERPROFILE 'codex'
$env:CLAUDE_CONFIG_DIR = Join-Path $env:USERPROFILE 'claude'
$env:COPILOT_HOME = Join-Path $env:USERPROFILE 'copilot'
$env:AGENT_CONTEXT_SETUP_HOME = Join-Path $testDir 'integrations'
$env:ANTHROPIC_API_KEY = $null
$env:OPENAI_API_KEY = $null
$env:GITHUB_TOKEN = $null
$env:GH_TOKEN = $null
$env:GITHUB_COPILOT_API_TOKEN = $null
$registry = Join-Path $testDir 'registry space'
$setup = Join-Path $Repo 'scripts\setup.ps1'
$systemPath = "$(Split-Path $python);$env:SystemRoot\System32;$env:SystemRoot"
try {
    if ($claude) {
        $env:PATH = "$(Split-Path $claude.Source);$systemPath"
        & $setup $registry
        if ($LASTEXITCODE -ne 0) { throw "Claude setup failed: $LASTEXITCODE" }
        $launcher = Join-Path $env:AGENT_CONTEXT_SETUP_HOME 'claude\claude.ps1'
        if (-not (Test-Path -LiteralPath $launcher)) { throw 'Claude launcher was not installed' }
        & $launcher --version
        if ($LASTEXITCODE -ne 0) { throw "Claude launcher failed: $LASTEXITCODE" }
        & $setup --uninstall
        if ($LASTEXITCODE -ne 0) { throw "Claude teardown failed: $LASTEXITCODE" }
        Write-Output 'Windows Claude launcher --version: passed'
    } else {
        Write-Output 'Windows Claude launcher --version: unavailable'
    }
    if ($copilot -and $copilot.Source -match '(?i)[\\/]copilot-shim[\\/]') {
        $env:PATH = "$(Split-Path $copilot.Source);$systemPath"
        $output = & $setup $registry
        $output
        if ($LASTEXITCODE -ne 0) { throw "shim inspection failed: $LASTEXITCODE" }
        if (-not ($output -match 'copilot: unsupported: VS Code Copilot shim')) { throw 'shim was not identified' }
        if (Test-Path -LiteralPath (Join-Path $env:AGENT_CONTEXT_SETUP_HOME 'copilot')) { throw 'shim was installed' }
        Write-Output 'Windows VS Code Copilot shim classification: passed without executing shim'
    } else {
        Write-Output 'Windows VS Code Copilot shim classification: unavailable'
    }
} finally {
    Remove-Item -LiteralPath $testDir -Recurse -Force -ErrorAction SilentlyContinue
}
