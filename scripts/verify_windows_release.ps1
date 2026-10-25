# Read-only check before manually copying the Windows release into the game.
param([Parameter(Mandatory=$true)][string]$GamePath)
$ErrorActionPreference = 'Stop'
function Get-ReleaseSHA256([string]$Path) {
    $stream = [System.IO.File]::OpenRead($Path)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try { return [BitConverter]::ToString($sha.ComputeHash($stream)).Replace('-', '') }
    finally { $sha.Dispose(); $stream.Dispose() }
}
$game = (Resolve-Path -LiteralPath $GamePath).Path
$expected = @{
    'MonoBleedingEdge\EmbedRuntime\mono-2.0-bdwgc.dll' = '5C3AD7D6E2B557173D9FA4C3281136ED6992DBE25031979DFEE85D001267761C'
    'MonsterRoadtrip_Data\Managed\Assembly-CSharp.dll' = 'A647DB4EB5501E577BB431ABE58C094BF3AECAC94DD5E5C64EEFEA6FD3958562'
    'MonsterRoadtrip_Data\StreamingAssets\aa\StandaloneWindows\texts_assets_all.bundle' = '905D468901BD781D5F9A3768B739EAE96A0E5E246C0D0F1FD936BA2044DA83E1'
}
foreach ($item in $expected.GetEnumerator()) {
    $path = Join-Path $game $item.Key
    if (!(Test-Path -LiteralPath $path) -or (Get-ReleaseSHA256 $path) -ne $item.Value) {
        throw "Unsupported or modified game file: $($item.Key). Do not install this Windows release."
    }
}
$manifestPath = Join-Path $PSScriptRoot 'RELEASE_MANIFEST.json'
if (Test-Path -LiteralPath $manifestPath) {
    $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    foreach ($item in $manifest.files.PSObject.Properties) {
        $path = Join-Path $PSScriptRoot $item.Name
        if (!(Test-Path -LiteralPath $path) -or (Get-ReleaseSHA256 $path) -ne $item.Value) {
            throw "Release file missing or changed: $($item.Name)"
        }
    }
}
Write-Output 'PASS: supported Windows x86 game build; available package hashes match. No files were changed.'
