$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repo ".venv\Scripts\python.exe"
. (Join-Path $PSScriptRoot "native.ps1")

if (-not (Test-Path -LiteralPath $python)) {
    throw "Missing .venv. Run .\scripts\run-local.ps1 first."
}

Push-Location $repo
try {
    Invoke-NativeCommand -FilePath $python -Arguments @("-m", "pip", "install", "-r", "src\windows\requirements.txt")
    Invoke-NativeCommand -FilePath $python -Arguments @("-m", "pip", "install", "-e", ".[standalone]")
    Invoke-NativeCommand -FilePath $python -Arguments @("-m", "PyInstaller", "--noconfirm", "--clean", "AI-Clean-Paste-Companion.spec")
}
finally {
    Pop-Location
}
