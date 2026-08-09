function Invoke-NativeCommand {
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [string]$FilePath,
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Arguments
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Native command failed with exit code $LASTEXITCODE`: $FilePath $($Arguments -join ' ')"
    }
}
