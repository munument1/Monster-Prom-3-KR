# Monster Roadtrip Korean Font/UI Bridge (optional)

This is source for an optional BepInEx 5 Mono x86 plugin for Monster Prom 3: Monster Roadtrip. It patches the `english_metatexts` lookup and applies Korean fonts to NGUI `UILabel` and Unity UI `Text` components. It does not install itself, copy files into the game, or change game/save data.

## Current status

- 0.1.5 resets the road marker's section index when starting a valid new path.
  The original MoveAlongPath retained the previous path's -1 completion sentinel,
  causing negative section-loop errors when the next update crossed multiple
  sections. The original curve, destination and save data remain in use. See
  `docs/ROADMAP_MOVEMENT_FIX_2026-10-25.md` for tests and pending gameplay checks.

- 0.1.4 is installed with a fingerprint-gated local MonoMod.Utils correction:
  legacy SetMonoCorlibInternal wrote +0x4F while this x86 Mono uses +0x53,
  corrupting a native pointer before runtime cleanup. Standalone x86 Mono tests
  reproduce the original failure and verify clean shutdown with the correction.
  The failed Cecil trial was reverted to auto. See `docs/MONO_CORLIB_FIX_2026-10-25.md`.

- 0.1.2 protects checkpoint player names from the original ASCII XML writer's
  replacement fallback. Non-ASCII name characters are written as XML character
  references, preserving the existing save encoding and encryption workflow.
  A C# regression probe reproduces the original loss and verifies nine name
  round-trips. User-run gameplay/save/load validation remains pending. See
  `docs/UI_RUNTIME_AUDIT.md` for evidence and the backed-up existing-save repair.

- Source targets .NET Framework 4.7.2 and x86, matching the game's Unity 2021.3.15f1 Mono x86 runtime.
- The installed game assembly metadata was inspected read-only. The relevant targets are `BeautifulGlitch.CoreAssetManager.GetTextAsset(string)`, `BeautifulGlitch.LocalizedNGUIFont.Refresh()`, `BeautifulGlitch.LocalizedTextFont.Refresh()`, and `UILabel.OnEnable()`; `UnityEngine.UI.Text.OnEnable()` is also patched by name at runtime.
- Font loading order is: optional `roadtrip_korean_fonts.bundle` beside the plugin, optional `fonts/Jua.ttf` and `fonts/GamjaFlower.ttf` registered with Windows `AddFontResourceExW(FR_PRIVATE)`, an optional user-configured Monster Camp Unity 2019 bundle, and finally Windows `Malgun Gothic`. Bundle/font paths default to the plugin directory; the Camp bundle path is empty by default. Local font registration is private to this process and does not install system fonts or edit the registry. The locally tested Jua/Gamja Flower assets were extracted from an owned Camp install into gitignored files and are not included in the distributable package.
- **Prior live validation 2026-10-24:** The running Monster Roadtrip BepInEx log reported `LoadAllAssets<Font>() returned 2 Font asset(s)`, `Selected header font: 'Jua'`, `Selected body font: 'GamjaFlower'`, and loaded an earlier 195-entry UI preview. An actual title-screen screenshot showed Korean text in the expected distinctive font. On 2026-10-25 the newest 2,871-key preview and rebuilt bridge DLL were safely reinstalled to the local game with hash checks, but **not** yet confirmed in a fresh game session. Full dialogue and settings screens are not yet validated.
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
4. Run `python -X utf8 scripts\build_ui_preview.py` from the translation repository. The local playtest installer copies the generated `english_metatexts.txt` and optional local font bundle beside the plugin DLL; a distributable package must include the current preview beside the DLL but must not include game-extracted Camp fonts.
5. Launch the test copy and inspect `BepInEx/config/munument1.roadtrip.koreanfontbridge.cfg`. Fresh configs default to `roadtrip_korean_fonts.bundle`, `fonts/`, and `english_metatexts.txt` beside the plugin DLL; `MonsterCampFontBundlePath` is empty by default. Override these paths only when using local optional font assets.
6. Read the BepInEx log. It reports bundle loading, private font registration, Unity's reported font-family names, glyph coverage, each Harmony patch, and whether the local metatext file was used. If Unity cannot recognize the privately registered family or the font fails Korean glyph coverage, the plugin proceeds to the Monster Camp bundle and then Malgun Gothic.

The plugin only replaces the `english_metatexts` `TextAsset` when the configured preview file exists. Event text overrides remain the separate loose files produced under `build/playtest/game_assets/texts/`; this plugin does not copy or install those files.

## Manual review still required

**Verified:** Steam-launched game on an earlier build, main menu Korean UI, font selection Jua/GamjaFlower and Harmony metatext loader; all 30,255 extracted translation candidates now have reviewed Korean entries and pass source-structure checks. **Still to test on the latest build:** settings submenus, long dialogue, choice/action prompts, line wrapping, scene changes, TextMeshPro-only widgets and game save/load. Certain English bracketed developer notes are still preserved with Korean explanations because they are treated as protected markup, not because candidate entries remain untranslated.
