# Monster Roadtrip Korean Font/UI Bridge (optional)

This is source for an optional BepInEx 5 Mono x86 plugin for Monster Prom 3: Monster Roadtrip. It patches the `english_metatexts` lookup and applies Korean fonts to NGUI `UILabel` and Unity UI `Text` components. It does not install itself, copy files into the game, or change game/save data.

## Current status

- Source targets .NET Framework 4.7.2 and x86, matching the game's Unity 2021.3.15f1 Mono x86 runtime.
- The installed game assembly metadata was inspected read-only. The relevant targets are `BeautifulGlitch.CoreAssetManager.GetTextAsset(string)`, `BeautifulGlitch.LocalizedNGUIFont.Refresh()`, `BeautifulGlitch.LocalizedTextFont.Refresh()`, and `UILabel.OnEnable()`; `UnityEngine.UI.Text.OnEnable()` is also patched by name at runtime.
- Font loading order is: `build/fontbundles/roadtrip_korean_fonts.bundle` generated **locally** by `python scripts/expose_camp_fonts.py`, then `work/fonts/Jua.ttf` and `work/fonts/GamjaFlower.ttf` registered with Windows `AddFontResourceExW(FR_PRIVATE)`, then the original Monster Camp Unity 2019 bundle, and finally Windows `Malgun Gothic`. The local font registration is private to this process; it does not install system fonts or edit the registry. The Korean fonts were exposed as two root assets from the original Camp bundle in a **gitignored copy**, so no Unity Editor is needed for the currently tested Steam builds.
- **Live validated 2026-10-24:** The running Monster Roadtrip BepInEx log reported `LoadAllAssets<Font>() returned 2 Font asset(s)`, `Selected header font: 'Jua'`, `Selected body font: 'GamjaFlower'`, and loading of the 195-entry Korean UI metatext preview. An actual title-screen screenshot showed Korean text rendered in the expected distinctive font. Full dialogue and settings screens are not yet validated.
- Build verification passed against the local BepInEx 5.4.23.2 core and the installed game's managed assemblies: `dotnet build src/RoadtripKoreanFontBridge/RoadtripKoreanFontBridge.csproj -c Release --no-restore -warnaserror` completed with 0 warnings and 0 errors. The output PE machine is x86 (`0x14c`). This verifies compilation only, not in-game behavior.
- The plugin checks glyph coverage against Korean characters found in the local UI preview and built event outputs. When the plugin is destroyed, it releases its dynamic Unity fonts and calls `RemoveFontResourceExW` for each private font resource it registered. If every source, including Windows `Malgun Gothic`, fails validation, that role is left unset and a log error is written.
- The UI role choice is a configurable heuristic: object/component names containing `header`, `title`, `heading`, `headline`, `banner`, `logo`, or `sectiontitle`, or a font size at/above the configured threshold, use Jua; other eligible text uses GamjaFlower. Adjust `HeaderFontSizeThreshold` if the game's title/body sizes differ from this default.
- Menus and both Camp font roles were verified in the running game. Long dialogue, every UI scene, TextMeshPro glyphs and full regression tests remain outstanding.

## Build

Requirements: .NET SDK, BepInEx 5 Mono x86 core files (`BepInEx.dll` and `0Harmony.dll`), and the game's `MonsterRoadtrip_Data/Managed` reference assemblies. No dependency DLLs or font binaries are included in source control.

From the repository root in PowerShell:

```powershell
dotnet build .\src\RoadtripKoreanFontBridge\RoadtripKoreanFontBridge.csproj -c Release
```

The project defaults to the local BepInEx archive under ignored `work/tools/BepInEx_win_x86_5.4.23.2/BepInEx/core` and the current Steam installation's `MonsterRoadtrip_Data/Managed` directory. Override those locations on another machine:

```powershell
dotnet build .\src\RoadtripKoreanFontBridge\RoadtripKoreanFontBridge.csproj -c Release `
  -p:BepInExDir="C:\path\to\BepInEx\core" `
  -p:GameManagedDir="C:\path\to\MonsterRoadtrip_Data\Managed"
```

The build output is `src/RoadtripKoreanFontBridge/bin/Release/RoadtripKoreanFontBridge.dll`. Build output folders and DLL/PDB files are ignored.

## Optional local setup

1. Run `python -X utf8 scripts\prepare_camp_fonts.py` then `python -X utf8 scripts\expose_camp_fonts.py` using an installed Monster Camp copy. This creates the preferred local-only `build/fontbundles/roadtrip_korean_fonts.bundle` by exposing existing Font root IDs, without installing Unity Editor or editing either installed game. For future compatibility, the alternative Unity Editor 2021.3.15f1 recipe `scripts\build_camp_font_bundle.ps1` is also available.
2. Use a separate test copy of the game and install the **BepInEx 5 Mono x86** distribution there. Do not use a 64-bit loader for this 32-bit game.
3. Build the plugin and manually place the resulting DLL under the test copy's `BepInEx/plugins/RoadtripKoreanFontBridge/` directory.
4. Run `python -X utf8 scripts\build_ui_preview.py` from the translation repository so `build/preview/english_metatexts.txt` exists. The file is ignored and is not shipped by this plugin.
5. Launch the test copy and inspect `BepInEx/config/munument1.roadtrip.koreanfontbridge.cfg`. Update `RoadtripFontBundlePath`, `LocalFontDirectory`, `MonsterCampFontBundlePath`, and `PreviewFilePath` if the local paths differ. The default local font directory is `D:\Codex_Trans\Monster-Prom-3-KR\work\fonts`.
6. Read the BepInEx log. It reports bundle loading, private font registration, Unity's reported font-family names, glyph coverage, each Harmony patch, and whether the local metatext file was used. If Unity cannot recognize the privately registered family or the font fails Korean glyph coverage, the plugin proceeds to the Monster Camp bundle and then Malgun Gothic.

The plugin only replaces the `english_metatexts` `TextAsset` when the configured preview file exists. Event text overrides remain the separate loose files produced under `build/playtest/game_assets/texts/`; this plugin does not copy or install those files.

## Manual review still required

**Verified:** Steam-launched game, main menu Korean UI, source font selection Jua/GamjaFlower and Harmony metatext loader. **Still to test:** settings submenus, long dialogue, choice/action prompts, line wrapping, scene changes, TextMeshPro-only widgets and game save/load. Some English lines remain because overall translation coverage is partial.
