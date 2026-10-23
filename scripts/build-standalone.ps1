$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot "native.ps1")

Push-Location $repo
try {
    Invoke-NativeCommand -FilePath npm.cmd -Arguments @("run", "studio:build")
    Invoke-NativeCommand -FilePath uv -Arguments @("run", "--frozen", "--all-extras", "--python", "3.15.1", "python", "-m", "PyInstaller", "--noconfirm", "--clean", "AI-Clean-Paste-Studio.spec")
}
finally {
    Pop-Location
}
