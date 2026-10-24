# Installs the verified Roadtrip Korean preview into the user's current game.
# All originals are preserved. Every new file is recorded for reversible removal.
param(
    [string]$GamePath = 'C:\Games\Steam\steamapps\common\Monster Prom 3 - Monster Roadtrip'
)

$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$game = (Resolve-Path -LiteralPath $GamePath -ErrorAction Stop).Path
$data = Join-Path $game 'MonsterRoadtrip_Data'
if (!(Test-Path -LiteralPath (Join-Path $game 'MonsterRoadtrip.exe')) -or
    !(Test-Path -LiteralPath (Join-Path $data 'Managed\Assembly-CSharp.dll'))) {
    throw "Not a recognizable Monster Roadtrip install: $game"
}
if (Get-Process -Name 'MonsterRoadtrip' -ErrorAction SilentlyContinue) {
    throw 'MonsterRoadtrip.exe is running. Exit the game before installation; process was NOT stopped.'
}

$state = Join-Path $repo 'work\install\installed_files.json'
if (Test-Path -LiteralPath $state) {
    throw "Prior installation manifest exists. For safety, run uninstall_local_playtest.ps1 first: $state"
}
$bepinex = Join-Path $repo 'work\tools\BepInEx_win_x86_5.4.23.2'
$bridge = Join-Path $repo 'src\RoadtripKoreanFontBridge\bin\Release\RoadtripKoreanFontBridge.dll'
$events = Join-Path $repo 'build\playtest\game_assets\texts'
$metatext = Join-Path $repo 'build\preview\english_metatexts.txt'
$fonts = Join-Path $repo 'work\fonts'
$roadtripFontBundle = Join-Path $repo 'build\fontbundles\roadtrip_korean_fonts.bundle'
foreach ($file in @($bridge, $metatext, (Join-Path $fonts 'Jua.ttf'), (Join-Path $fonts 'GamjaFlower.ttf'),
    (Join-Path $bepinex 'winhttp.dll'), (Join-Path $bepinex 'doorstop_config.ini'))) {
    if (!(Test-Path -LiteralPath $file -PathType Leaf)) { throw "Missing build input: $file" }
}
if (!(Test-Path -LiteralPath $roadtripFontBundle -PathType Leaf)) {
    & python -X utf8 (Join-Path $PSScriptRoot 'expose_camp_fonts.py')
    if ($LASTEXITCODE -ne 0 -or !(Test-Path -LiteralPath $roadtripFontBundle -PathType Leaf)) {
        throw 'Could not prepare the local-only Jua/GamjaFlower bundle from Monster Camp'
    }
}

$entries = New-Object 'System.Collections.Generic.List[object]'
foreach ($name in @('winhttp.dll','doorstop_config.ini','.doorstop_version')) {
    $entries.Add([pscustomobject]@{source = (Join-Path $bepinex $name); relative = $name})
}
$bepinexRoot = Join-Path $bepinex 'BepInEx'
foreach ($src in Get-ChildItem -LiteralPath $bepinexRoot -Recurse -File) {
    $relative = 'BepInEx\' + $src.FullName.Substring($bepinexRoot.Length).TrimStart('\')
    $entries.Add([pscustomobject]@{source = $src.FullName; relative = $relative})
}
$entries.Add([pscustomobject]@{source = $bridge; relative = 'BepInEx\plugins\RoadtripKoreanFontBridge\RoadtripKoreanFontBridge.dll'})
foreach ($src in Get-ChildItem -LiteralPath $events -Filter 'english_events_*.txt' -File) {
    $entries.Add([pscustomobject]@{source = $src.FullName; relative = ('MonsterRoadtrip_Data\StreamingAssets\game_assets\texts\' + $src.Name)})
}
if (@(Get-ChildItem -LiteralPath $events -Filter 'english_events_*.txt' -File).Count -ne 11) {
    throw 'Expected exactly 11 vetted English-slot event override files'
}

# Conflict gate before any modification. This release never overwrites an existing file.
foreach ($item in $entries) {
    $dest = Join-Path $game $item.relative
    if (Test-Path -LiteralPath $dest) {
        throw "Refusing to overwrite existing game/mod file: $dest"
    }
}

$original = @{
    'Assembly-CSharp.dll' = (Get-FileHash -LiteralPath (Join-Path $data 'Managed\Assembly-CSharp.dll') -Algorithm SHA256).Hash
    'texts_assets_all.bundle' = (Get-FileHash -LiteralPath (Join-Path $data 'StreamingAssets\aa\StandaloneWindows\texts_assets_all.bundle') -Algorithm SHA256).Hash
}
$installed = New-Object 'System.Collections.Generic.List[object]'
try {
    foreach ($item in $entries) {
        $dest = Join-Path $game $item.relative
        $dir = Split-Path -Parent $dest
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Copy-Item -LiteralPath $item.source -Destination $dest -ErrorAction Stop
        $expected = (Get-FileHash -LiteralPath $item.source -Algorithm SHA256).Hash
        $actual = (Get-FileHash -LiteralPath $dest -Algorithm SHA256).Hash
        if ($actual -ne $expected) { throw "Copy integrity mismatch: $dest" }
        $installed.Add([pscustomobject]@{relative = $item.relative; sha256 = $actual})
    }
    $manifest = [ordered]@{
        schema = 1
        game = $game
        installed_at = (Get-Date).ToString('o')
        repository_commit = (git -C $repo rev-parse HEAD)
        original_file_hashes = $original
        files = @($installed.ToArray())
    }
    New-Item -ItemType Directory -Path (Split-Path -Parent $state) -Force | Out-Null
    $manifest | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath $state -Encoding UTF8
    Write-Output "INSTALLED $($installed.Count) new files to: $game"
    Write-Output "ROLLBACK_MANIFEST=$state"
    Write-Output "FONT_SOURCES=$fonts"
    Write-Output "METATEXT_SOURCE=$metatext"
    Write-Output "UNINSTALL_COMMAND=powershell -ExecutionPolicy Bypass -File `"$PSScriptRoot\uninstall_local_playtest.ps1`""
} catch {
    Write-Warning "Install failed, removing newly copied files: $_"
    foreach ($item in @($installed.ToArray())) {
        $dest = Join-Path $game $item.relative
        if (Test-Path -LiteralPath $dest -PathType Leaf) { Remove-Item -LiteralPath $dest -Force }
    }
    throw
}
