# Make a *local* Roadtrip-compatible Jua/Gamja Flower AssetBundle using Unity 2021.3.15f1.
# Original Steam games and user's saves are never changed.
# This command is NOT run automatically and requires a matching Unity Editor.
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$UnityEditorPath
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$fontDir = Join-Path $root 'work\fonts'
$project = Join-Path $root 'work\unity_font_project'
$output = Join-Path $root 'build\fontbundles'
$source = Join-Path $PSScriptRoot 'unity_editor\BuildRoadtripKoreanFonts.cs'

$editor = (Resolve-Path -LiteralPath $UnityEditorPath -ErrorAction Stop).Path
if ($editor -notmatch '2021\.3\.15f1' -or (Split-Path -Leaf $editor) -ne 'Unity.exe') {
    throw 'Use a real Unity 2021.3.15f1 Editor\Unity.exe path; other versions may make incompatible bundles.'
}

foreach ($filename in @('Jua.ttf','GamjaFlower.ttf')) {
    if (!(Test-Path -LiteralPath (Join-Path $fontDir $filename))) {
        throw "Missing local font $filename. Run python scripts\prepare_camp_fonts.py first."
    }
}

$assets = Join-Path $project 'Assets\KoreanFonts'
$editorScript = Join-Path $project 'Assets\Editor'
$projectSettings = Join-Path $project 'ProjectSettings'
foreach ($dir in @($assets,$editorScript,$projectSettings,$output)) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
}
Set-Content -LiteralPath (Join-Path $projectSettings 'ProjectVersion.txt') -Value 'm_EditorVersion: 2021.3.15f1' -Encoding ASCII
foreach ($filename in @('Jua.ttf','GamjaFlower.ttf')) {
    Copy-Item -LiteralPath (Join-Path $fontDir $filename) -Destination (Join-Path $assets $filename) -Force
}
Copy-Item -LiteralPath $source -Destination (Join-Path $editorScript 'BuildRoadtripKoreanFonts.cs') -Force

$env:ROADTRIP_FONT_BUNDLE_OUT = $output
$log = Join-Path $root 'work\unity_font_bundle_build.log'
& $editor -batchmode -nographics -quit -projectPath $project -executeMethod RoadtripFontBundleBuild.Build -logFile $log
if ($LASTEXITCODE -ne 0) { throw "Unity Editor failed. Check log: $log" }
$bundle = Join-Path $output 'roadtrip_korean_fonts.bundle'
if (!(Test-Path -LiteralPath $bundle)) { throw "Expected local font bundle was not generated: $bundle" }
Write-Output "LOCAL ONLY: $bundle"
Write-Output 'No installed game, Steam configuration, or save files were modified.'
