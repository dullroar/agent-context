# Python is also a prerequisite of the registry CLI.
$ErrorActionPreference = 'Stop'
$python = Get-Command python -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $python) {
    [Console]::Error.WriteLine('setup: Python 3.10 or newer is required on Windows.')
    exit 1
}
& $python.Source (Join-Path $PSScriptRoot 'setup.py') @args
exit $LASTEXITCODE
