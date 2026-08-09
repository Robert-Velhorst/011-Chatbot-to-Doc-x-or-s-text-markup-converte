param(
    [int]$Port = 8765,
    [string]$DataDir = "runtime/studio"
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repo ".venv\Scripts\python.exe"
. (Join-Path $PSScriptRoot "native.ps1")

if (-not (Test-Path -LiteralPath $python)) {
    Invoke-NativeCommand -FilePath py -Arguments @("-3.12", "-m", "venv", (Join-Path $repo ".venv"))
}

Invoke-NativeCommand -FilePath $python -Arguments @("-m", "pip", "install", "-e", $repo, "--disable-pip-version-check", "--progress-bar", "off")
Push-Location $repo
try {
    Invoke-NativeCommand -FilePath npm.cmd -Arguments @("install")
    Invoke-NativeCommand -FilePath npm.cmd -Arguments @("run", "studio:build")
    $env:CLEAN_PASTE_DATA_DIR = [System.IO.Path]::GetFullPath((Join-Path $repo $DataDir))
    $env:CLEAN_PASTE_PORT = "$Port"
    Invoke-NativeCommand -FilePath $python -Arguments @("-m", "cleanpaste_studio", "serve")
}
finally {
    Pop-Location
}
