# Monster Roadtrip Korean Font/UI Bridge (optional)

This is source for an optional BepInEx 5 Mono x86 plugin for Monster Prom 3: Monster Roadtrip. It patches the `english_metatexts` lookup and applies Korean fonts to NGUI `UILabel` and Unity UI `Text` components. It does not install itself, copy files into the game, or change game/save data.

## Current status

- Source targets .NET Framework 4.7.2 and x86, matching the game's Unity 2021.3.15f1 Mono x86 runtime.
- The installed game assembly metadata was inspected read-only. The relevant targets are `BeautifulGlitch.CoreAssetManager.GetTextAsset(string)`, `BeautifulGlitch.LocalizedNGUIFont.Refresh()`, `BeautifulGlitch.LocalizedTextFont.Refresh()`, and `UILabel.OnEnable()`; `UnityEngine.UI.Text.OnEnable()` is also patched by name at runtime.
- Font loading order is: the optional `build/fontbundles/roadtrip_korean_fonts.bundle` made with Unity 2021.3.15f1, then the original Monster Camp Unity 2019 bundle, then Windows `Malgun Gothic` if a role still has no validated font. The Camp bundle contains Font objects named `Jua` and `GamjaFlower`, and its `fontset_korean` profile points to Jua for the Unity UI header and GamjaFlower for the body. However, the Camp bundle's named container exposes profile roots, and the profile's original C# type is not part of Monster Roadtrip. The plugin tries `AssetBundle.LoadFromFile`, `LoadAllAssets<Font>()`, and direct named Font lookups, but **successful cross-version loading is unverified**.
- The current workspace has Unity Editor 6000.x versions but no Unity 2021.3.15f1 editor, and `build/fontbundles/roadtrip_korean_fonts.bundle` has not been generated. The first bundle path therefore falls through until a compatible bundle is built locally.
- Build verification passed against the local BepInEx 5.4.23.2 core and the installed game's managed assemblies: `dotnet build src/RoadtripKoreanFontBridge/RoadtripKoreanFontBridge.csproj -c Release --no-restore -warnaserror` completed with 0 warnings and 0 errors. The output PE machine is x86 (`0x14c`). This verifies compilation only, not in-game behavior.
- The plugin checks glyph coverage against Korean characters found in the local UI preview and built event outputs. If a requested font cannot be loaded or fails that check, it tries the Windows `Malgun Gothic` dynamic font. If the fallback also fails, that role is left unset and a log error is written.
- The UI role choice is a configurable heuristic: object/component names containing `header`, `title`, `heading`, `headline`, `banner`, `logo`, or `sectiontitle`, or a font size at/above the configured threshold, use Jua; other eligible text uses GamjaFlower. Adjust `HeaderFontSizeThreshold` if the game's title/body sizes differ from this default.
- This source has not been tested in a running game. A successful build does not prove that Unity 2019 font assets load in Unity 2021 or that all UI layouts remain correct.

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

1. If a matching Unity 2021.3.15f1 Editor is available, prepare the local-only `work/fonts/Jua.ttf` and `work/fonts/GamjaFlower.ttf`, then run `scripts\build_camp_font_bundle.ps1 -UnityEditorPath "C:\path\to\Unity 2021.3.15f1\Editor\Unity.exe"`. This creates the optional `build/fontbundles/roadtrip_korean_fonts.bundle` locally. Other Unity editor versions are rejected by the script.
2. Use a separate test copy of the game and install the **BepInEx 5 Mono x86** distribution there. Do not use a 64-bit loader for this 32-bit game.
3. Build the plugin and manually place the resulting DLL under the test copy's `BepInEx/plugins/RoadtripKoreanFontBridge/` directory.
4. Run `python -X utf8 scripts\build_ui_preview.py` from the translation repository so `build/preview/english_metatexts.txt` exists. The file is ignored and is not shipped by this plugin.
5. Launch the test copy and inspect `BepInEx/config/munument1.roadtrip.koreanfontbridge.cfg`. Update `RoadtripFontBundlePath`, `MonsterCampFontBundlePath`, and `PreviewFilePath` if the local paths differ.
6. Read the BepInEx log. It reports bundle loading, discovered font names, glyph coverage, each Harmony patch, and whether the local metatext file was used. If neither bundle exposes valid Jua/GamjaFlower assets, the log will show the Malgun Gothic fallback.

The plugin only replaces the `english_metatexts` `TextAsset` when the configured preview file exists. Event text overrides remain the separate loose files produced under `build/playtest/game_assets/texts/`; this plugin does not copy or install those files.

## Manual review still required

Test the main menu, settings, long text, dialogue, choice/action prompts, line wrapping, and scene changes on a disposable game copy. Confirm the BepInEx log says which fonts were selected and that the actual Korean glyphs display. Font loading, layout, and runtime patch behavior remain **UNTESTED** until that validation is performed.
