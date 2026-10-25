# Monster Roadtrip Korean translation — manual overwrite package

This package contains the 11 event-text override files only. It is designed for users who prefer copying files manually, including Linux/Steam Deck users.

## Install

1. Exit the game.
2. Open the game's installation directory (Steam: Manage → Browse local files).
3. Back up any existing files with the same names in `MonsterRoadtrip_Data/StreamingAssets/game_assets/texts/`.
4. Copy the included `MonsterRoadtrip_Data/` directory into the game directory, merging folders and allowing the 11 included `english_events_*.txt` files to replace same-named files.
5. Launch the game. Keep the game language set to English; the game uses these `english_` text overrides as the translation slot.

## Uninstall / rollback

Restore the 11 original files from your backup. If you did not have files with those names before installation, remove only the 11 `english_events_*.txt` files supplied by this package. Do not delete the entire `texts` directory.

## Platform notes

- This archive does not include a Windows-only installer, BepInEx Windows binaries, or the Windows-specific font bundle.
- The event text overrides are plain files and are intended to be copied on Windows or Linux. The optional UI metatext/font bridge is not included here; its Linux runtime compatibility has not been validated, so some UI labels may remain untranslated or use fallback fonts.
- This is a manual-overwrite test/release candidate. Back up existing files first. Do not overwrite other mods' files without checking for conflicts.

## Contents

`MonsterRoadtrip_Data/StreamingAssets/game_assets/texts/english_events_*.txt` — 11 translated event-text files.
