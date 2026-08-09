# Authenticated ngrok operation

ngrok is an optional transport, not a replacement for application authentication. Studio remains bound to loopback while ngrok forwards HTTPS traffic to it.

## Start

```powershell
$tokenBytes = New-Object byte[] 32
$randomGenerator = [Security.Cryptography.RandomNumberGenerator]::Create()
$randomGenerator.GetBytes($tokenBytes)
$randomGenerator.Dispose()
$env:CLEAN_PASTE_TOKEN = [BitConverter]::ToString($tokenBytes).Replace("-", "")
.\scripts\run-ngrok.ps1
```

Prerequisites: ngrok installed, `ngrok config add-authtoken` completed, and one endpoint available on the ngrok account. The script forces `CLEAN_PASTE_ENV=production` and `CLEAN_PASTE_HOST=127.0.0.1`.

The public `/health` route intentionally contains only status and version. Every document, project, privacy, artifact, and HAI connector API route requires the bearer token or a short-lived HTTP-only browser session. Do not put the token in a URL, repository, HAI connector JSON, screenshot, or support bundle.

## Stop and incident response

Press `Ctrl+C` in the ngrok terminal. The launcher closes only its own Studio process. Rotate `CLEAN_PASTE_TOKEN` and restart after any suspected exposure. If the ngrok account reports `ERR_NGROK_334`, another endpoint is already using the account's assigned domain; do not pool traffic with an unrelated service. Stop the other endpoint intentionally or add account capacity.

Direct `0.0.0.0` internet exposure without TLS/reverse-proxy review is unsupported.
