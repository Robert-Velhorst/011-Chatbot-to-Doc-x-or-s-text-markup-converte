$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repo ".venv\Scripts\python.exe"
. (Join-Path $PSScriptRoot "native.ps1")

if (-not (Test-Path -LiteralPath $python)) {
    throw "Missing .venv. Run .\scripts\run-local.ps1 once or create the environment from README.md."
}

Push-Location $repo
try {
    Invoke-NativeCommand -FilePath npm.cmd -Arguments @("run", "check")
    Invoke-NativeCommand -FilePath npm.cmd -Arguments @("test")
    Invoke-NativeCommand -FilePath npm.cmd -Arguments @("run", "build")
    Invoke-NativeCommand -FilePath npm.cmd -Arguments @("run", "studio:build")
    Invoke-NativeCommand -FilePath $python -Arguments @("-m", "ruff", "check", "src\studio", "tests\studio")
    Invoke-NativeCommand -FilePath $python -Arguments @("-m", "pytest", "tests", "-q")
    Invoke-NativeCommand -FilePath $python -Arguments @("-m", "cleanpaste_studio", "doctor")
    Invoke-NativeCommand -FilePath $python -Arguments @("-m", "cleanpaste_studio", "convert", "fixtures\studio\sample-brief.md", "--out", "work\verification", "--formats", "pdf,markdown,text")
}
finally {
    Pop-Location
}
