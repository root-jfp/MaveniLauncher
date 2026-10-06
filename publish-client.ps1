param(
    [string]$ClientRoot = "$env:USERPROFILE\Downloads\MaveniClient",
    [string]$Version = "",
    [string]$NewsFile = "$PSScriptRoot\news.txt"
)

$ErrorActionPreference = "Stop"
$client = (Resolve-Path -LiteralPath $ClientRoot).Path
if (-not $Version) { $Version = Get-Date -Format "yyyy.MM.dd.HHmm" }

python "$PSScriptRoot\tools\build_manifest.py" `
    --root $client `
    --base-url "https://metin.maveni.net/client" `
    --version $Version `
    --news-file $NewsFile `
    --output (Join-Path $client "manifest.json")

Write-Host "Published manifest $Version for $client"
Write-Host "Friends can now open the launcher and update only changed files."
