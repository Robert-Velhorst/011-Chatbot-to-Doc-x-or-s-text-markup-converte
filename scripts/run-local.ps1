param(
    [int]$Port = 8765,
    [string]$DataDir = "runtime/studio"
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot "native.ps1")

Push-Location $repo
try {
    Invoke-NativeCommand -FilePath uv -Arguments @("sync", "--frozen", "--python", "3.15.1")
    Invoke-NativeCommand -FilePath npm.cmd -Arguments @("ci", "--ignore-scripts")
    Invoke-NativeCommand -FilePath npm.cmd -Arguments @("run", "studio:build")
    $env:CLEAN_PASTE_DATA_DIR = [System.IO.Path]::GetFullPath((Join-Path $repo $DataDir))
    $env:CLEAN_PASTE_PORT = "$Port"
    Invoke-NativeCommand -FilePath uv -Arguments @("run", "--frozen", "--python", "3.15.1", "python", "-m", "cleanpaste_studio", "serve")
}
finally {
    Pop-Location
}
