param(
    [int]$Port = 8877
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$exe = Join-Path $repo "dist\AI-Clean-Paste-Studio\AI-Clean-Paste-Studio.exe"
$testData = Join-Path $repo "work\standalone-smoke"

if (-not (Test-Path -LiteralPath $exe)) {
    throw "Standalone executable not found. Run .\scripts\build-standalone.ps1 first."
}

$tokenBytes = New-Object byte[] 32
$randomGenerator = [Security.Cryptography.RandomNumberGenerator]::Create()
$randomGenerator.GetBytes($tokenBytes)
$randomGenerator.Dispose()
$testToken = [BitConverter]::ToString($tokenBytes).Replace("-", "")
$env:CLEAN_PASTE_PORT = "$Port"
$env:CLEAN_PASTE_ENV = "production"
$env:CLEAN_PASTE_TOKEN = $testToken
$env:CLEAN_PASTE_DATA_DIR = $testData
$process = Start-Process -FilePath $exe -WorkingDirectory (Split-Path $exe) -WindowStyle Hidden -PassThru

try {
    $ready = $false
    for ($attempt = 0; $attempt -lt 80; $attempt++) {
        try {
            $health = Invoke-RestMethod "http://127.0.0.1:$Port/health" -TimeoutSec 1
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
        throw "Standalone did not become healthy on port $Port."
    }

    $headers = @{ Authorization = "Bearer $testToken" }
    $capabilities = Invoke-RestMethod "http://127.0.0.1:$Port/api/connectors/hai/v1/capabilities" -Headers $headers
    $page = Invoke-WebRequest "http://127.0.0.1:$Port/" -UseBasicParsing
    $running = Get-Process -Id $process.Id
    [pscustomobject]@{
        ProcessId      = $process.Id
        Health         = $health.status
        Version        = $health.version
        UIStatus       = $page.StatusCode
        UITitle        = [regex]::Match($page.Content, "<title>(.*?)</title>").Groups[1].Value
        HAIAuthority   = $capabilities.authority
        WorkingSetMB   = [math]::Round($running.WorkingSet64 / 1MB, 1)
        PrivateMemoryMB = [math]::Round($running.PrivateMemorySize64 / 1MB, 1)
        ExecutableMB   = [math]::Round((Get-Item $exe).Length / 1MB, 1)
        FolderMB       = [math]::Round(((Get-ChildItem (Split-Path $exe) -Recurse -File | Measure-Object Length -Sum).Sum / 1MB), 1)
    }
}
finally {
    if ($process -and -not $process.HasExited) {
        Stop-Process -Id $process.Id
    }
    Remove-Item Env:CLEAN_PASTE_TOKEN -ErrorAction SilentlyContinue
    Remove-Item Env:CLEAN_PASTE_ENV -ErrorAction SilentlyContinue
    Remove-Item Env:CLEAN_PASTE_PORT -ErrorAction SilentlyContinue
    Remove-Item Env:CLEAN_PASTE_DATA_DIR -ErrorAction SilentlyContinue
}
