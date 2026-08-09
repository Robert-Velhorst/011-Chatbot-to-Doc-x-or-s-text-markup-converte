param(
    [int]$Port = 8878,
    [int]$InspectionPort = 4040
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repo ".venv\Scripts\python.exe"
$ngrok = Get-Command ngrok.exe -ErrorAction SilentlyContinue

if (-not $ngrok) {
    throw "ngrok.exe is not available on PATH."
}
if (-not (Test-Path -LiteralPath $python)) {
    throw "Missing .venv."
}
$tokenBytes = New-Object byte[] 32
$randomGenerator = [Security.Cryptography.RandomNumberGenerator]::Create()
$randomGenerator.GetBytes($tokenBytes)
$randomGenerator.Dispose()
$testToken = [BitConverter]::ToString($tokenBytes).Replace("-", "")
$env:CLEAN_PASTE_ENV = "production"
$env:CLEAN_PASTE_HOST = "127.0.0.1"
$env:CLEAN_PASTE_PORT = "$Port"
$env:CLEAN_PASTE_TOKEN = $testToken
$env:CLEAN_PASTE_DATA_DIR = Join-Path $repo "work\ngrok-smoke"

$studio = Start-Process -FilePath $python -ArgumentList @(
    "-m", "cleanpaste_studio", "serve", "--host", "127.0.0.1", "--port", "$Port"
) -WorkingDirectory $repo -WindowStyle Hidden -PassThru
$tunnel = $null
$ownsAgent = $false
$tunnelName = "clean-paste-smoke-$PID"
$createdTunnel = $false

try {
    $localReady = $false
    for ($attempt = 0; $attempt -lt 40; $attempt++) {
        try {
            $health = Invoke-RestMethod "http://127.0.0.1:$Port/health" -TimeoutSec 1
            if ($health.status -eq "ok") {
                $localReady = $true
                break
            }
        }
        catch {
            Start-Sleep -Milliseconds 250
        }
    }
    if (-not $localReady) {
        throw "Local production service did not become healthy."
    }

    $agentAvailable = $false
    try {
        $existingTunnels = Invoke-RestMethod "http://127.0.0.1:$InspectionPort/api/tunnels" -TimeoutSec 2
        $agentAvailable = $null -ne $existingTunnels.tunnels
    }
    catch {
        $agentAvailable = $false
    }

    if ($agentAvailable) {
        $body = @{
            name  = $tunnelName
            addr  = "http://127.0.0.1:$Port"
            proto = "http"
        } | ConvertTo-Json
        $created = Invoke-RestMethod "http://127.0.0.1:$InspectionPort/api/tunnels" -Method Post -ContentType "application/json" -Body $body -TimeoutSec 15
        $createdTunnel = $true
        $publicUrl = $created.public_url
    }
    else {
        if (Get-NetTCPConnection -LocalPort $InspectionPort -State Listen -ErrorAction SilentlyContinue) {
            throw "Inspection port $InspectionPort is occupied by a non-ngrok service."
        }
        $tunnel = Start-Process -FilePath $ngrok.Source -ArgumentList @(
            "http", "http://127.0.0.1:$Port", "--web-addr=127.0.0.1:$InspectionPort", "--log=stdout", "--log-format=json"
        ) -WorkingDirectory $repo -WindowStyle Hidden -PassThru
        $ownsAgent = $true
    }

    if (-not $publicUrl) {
        for ($attempt = 0; $attempt -lt 80; $attempt++) {
            try {
                $tunnels = Invoke-RestMethod "http://127.0.0.1:$InspectionPort/api/tunnels" -TimeoutSec 1
                $publicUrl = ($tunnels.tunnels | Where-Object { $_.name -eq $tunnelName -or ($ownsAgent -and $_.proto -eq "https") } | Select-Object -First 1).public_url
                if ($publicUrl) {
                    break
                }
            }
            catch {
                Start-Sleep -Milliseconds 250
            }
        }
    }
    if (-not $publicUrl) {
        throw "ngrok did not publish an HTTPS tunnel."
    }

    $publicHeaders = @{ "ngrok-skip-browser-warning" = "true" }
    $publicHealth = Invoke-RestMethod "$publicUrl/health" -Headers $publicHeaders -TimeoutSec 15
    $unauthorized = 0
    try {
        Invoke-WebRequest "$publicUrl/api/connectors/hai/v1/capabilities" -Headers $publicHeaders -UseBasicParsing -TimeoutSec 15 | Out-Null
    }
    catch {
        $unauthorized = [int]$_.Exception.Response.StatusCode
    }
    $publicHeaders.Authorization = "Bearer $testToken"
    $capabilities = Invoke-RestMethod "$publicUrl/api/connectors/hai/v1/capabilities" -Headers $publicHeaders -TimeoutSec 15
    [pscustomobject]@{
        TunnelScheme       = ([uri]$publicUrl).Scheme
        PublicHealth       = $publicHealth.status
        UnauthorizedStatus = $unauthorized
        AuthorizedBoundary = $capabilities.authority
        LocalBind          = "127.0.0.1:$Port"
    }
}
finally {
    if ($createdTunnel) {
        try {
            Invoke-RestMethod "http://127.0.0.1:$InspectionPort/api/tunnels/$tunnelName" -Method Delete -TimeoutSec 5 | Out-Null
        }
        catch {
        }
    }
    if ($ownsAgent -and $tunnel -and -not $tunnel.HasExited) {
        Stop-Process -Id $tunnel.Id
    }
    if ($studio -and -not $studio.HasExited) {
        Stop-Process -Id $studio.Id
    }
    Remove-Item Env:CLEAN_PASTE_TOKEN -ErrorAction SilentlyContinue
    Remove-Item Env:CLEAN_PASTE_ENV -ErrorAction SilentlyContinue
    Remove-Item Env:CLEAN_PASTE_HOST -ErrorAction SilentlyContinue
    Remove-Item Env:CLEAN_PASTE_PORT -ErrorAction SilentlyContinue
    Remove-Item Env:CLEAN_PASTE_DATA_DIR -ErrorAction SilentlyContinue
}
