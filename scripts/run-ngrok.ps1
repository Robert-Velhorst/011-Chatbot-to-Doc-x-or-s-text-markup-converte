param(
    [int]$Port = 8765
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repo ".venv\Scripts\python.exe"
$ngrok = Get-Command ngrok.exe -ErrorAction SilentlyContinue

if (-not $ngrok) {
    throw "ngrok.exe is not installed or is not available on PATH. Install ngrok and complete 'ngrok config add-authtoken' first."
}
if (-not (Test-Path -LiteralPath $python)) {
    throw "Missing .venv. Run .\scripts\run-local.ps1 first."
}
if ([string]::IsNullOrWhiteSpace($env:CLEAN_PASTE_TOKEN) -or $env:CLEAN_PASTE_TOKEN.Length -lt 32) {
    throw "Set CLEAN_PASTE_TOKEN to a cryptographically random value of at least 32 characters before opening a tunnel."
}

$env:CLEAN_PASTE_ENV = "production"
$env:CLEAN_PASTE_HOST = "127.0.0.1"
$env:CLEAN_PASTE_PORT = "$Port"
$studio = Start-Process -FilePath $python -ArgumentList @(
    "-m", "cleanpaste_studio", "serve", "--host", "127.0.0.1", "--port", "$Port"
) -WorkingDirectory $repo -WindowStyle Hidden -PassThru

try {
    $ready = $false
    for ($attempt = 0; $attempt -lt 40; $attempt++) {
        try {
            $health = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/health" -TimeoutSec 1
            if ($health.status -eq "ok") {
                $ready = $true
                break
            }
        }
        catch {
            Start-Sleep -Milliseconds 250
        }
    }
    if (-not $ready) {
        throw "Document Studio did not become healthy on port $Port."
    }
    & $ngrok.Source http "http://127.0.0.1:$Port"
}
finally {
    if ($studio -and -not $studio.HasExited) {
        Stop-Process -Id $studio.Id
    }
}
