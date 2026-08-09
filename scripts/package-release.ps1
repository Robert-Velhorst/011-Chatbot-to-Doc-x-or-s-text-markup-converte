param(
    [string]$Version = "0.2.0"
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$workRoot = [IO.Path]::GetFullPath((Join-Path $repo "work"))
$staging = [IO.Path]::GetFullPath((Join-Path $workRoot "release-$Version"))
$outputs = Join-Path $repo "outputs"

if (-not $staging.StartsWith($workRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Release staging path escaped the workspace work directory."
}
if ((Split-Path $staging -Leaf) -ne "release-$Version") {
    throw "Unexpected release staging directory."
}

function Copy-TreeFiles {
    param(
        [string]$Source,
        [string]$Destination
    )
    $sourcePath = [IO.Path]::GetFullPath($Source)
    Get-ChildItem -LiteralPath $sourcePath -Recurse -File | ForEach-Object {
        $relative = $_.FullName.Substring($sourcePath.Length).TrimStart("\", "/")
        if ($relative -notmatch "(^|[\\/])(node_modules|dist|build|__pycache__|\.pytest_cache|\.ruff_cache|\.playwright-cli)([\\/]|$)" -and $_.Extension -ne ".pyc") {
            $target = Join-Path $Destination $relative
            New-Item -ItemType Directory -Force -Path (Split-Path $target -Parent) | Out-Null
            Copy-Item -LiteralPath $_.FullName -Destination $target
        }
    }
}

function New-ReleaseZip {
    param(
        [string]$Source,
        [string]$Name
    )
    $target = Join-Path $outputs $Name
    Compress-Archive -Path (Join-Path $Source "*") -DestinationPath $target -CompressionLevel Optimal -Force
}

if (Test-Path -LiteralPath $staging) {
    Remove-Item -LiteralPath $staging -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $staging, $outputs | Out-Null

$chrome = Join-Path $staging "chrome"
Copy-TreeFiles (Join-Path $repo "dist\chrome-extension") $chrome
New-ReleaseZip $chrome "AI-Clean-Paste-Chrome-v$Version.zip"

$companion = Join-Path $staging "companion"
Copy-TreeFiles (Join-Path $repo "dist\AI-Clean-Paste-Companion") $companion
Copy-Item -LiteralPath (Join-Path $repo "docs\WINDOWS_STANDALONE.md") -Destination (Join-Path $companion "README.md")
New-ReleaseZip $companion "AI-Clean-Paste-Companion-Windows-v$Version.zip"

$studio = Join-Path $staging "studio"
Copy-TreeFiles (Join-Path $repo "dist\AI-Clean-Paste-Studio") $studio
Copy-Item -LiteralPath (Join-Path $repo "docs\WINDOWS_STANDALONE.md") -Destination (Join-Path $studio "README.md")
New-ReleaseZip $studio "AI-Clean-Paste-Studio-Windows-v$Version.zip"

$hai = Join-Path $staging "hai"
Copy-TreeFiles (Join-Path $repo "integrations\hai") $hai
Copy-Item -LiteralPath (Join-Path $repo "docs\NGROK.md") -Destination (Join-Path $hai "NGROK.md")
New-ReleaseZip $hai "AI-Clean-Paste-HAI-Connector-v$Version.zip"

$source = Join-Path $staging "source"
foreach ($directory in @(".github", "docs", "fixtures", "integrations", "scripts", "src", "studio-ui", "tests")) {
    Copy-TreeFiles (Join-Path $repo $directory) (Join-Path $source $directory)
}
foreach ($file in @(
    ".env.example", ".gitignore", "AI-Clean-Paste-Companion.spec", "AI-Clean-Paste-Studio.spec",
    "docker-compose.yml", "Dockerfile", "package.json", "package-lock.json", "pyproject.toml",
    "README.md", "tsconfig.json", "vitest.config.ts"
)) {
    Copy-Item -LiteralPath (Join-Path $repo $file) -Destination (Join-Path $source $file)
}
New-ReleaseZip $source "AI-Clean-Paste-Complete-Source-v$Version.zip"

$hashLines = Get-ChildItem -LiteralPath $outputs -Filter "*v$Version.zip" | Sort-Object Name | ForEach-Object {
    $hash = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    "$hash  $($_.Name)"
}
[IO.File]::WriteAllLines((Join-Path $outputs "SHA256SUMS.txt"), $hashLines, [Text.UTF8Encoding]::new($false))

Get-ChildItem -LiteralPath $outputs -Filter "*v$Version.zip" | Sort-Object Name | Select-Object Name, Length
