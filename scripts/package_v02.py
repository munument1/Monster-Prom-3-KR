"""Build and verify v0.2 archives from explicit inputs, without touching the game."""
from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/releases"
STOCK = ROOT / "work/tools/BepInEx_win_x86_5.4.23.2"
FIXED_SHA = "BBED1657D03582CDB9399339AD146E9BAFD657EFCB65EEC5364D214E40F15D8B"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def archive(name: str, items: dict[str, bytes], kind: str) -> None:
    if any(n.startswith(("work/", "UserData/")) or ".." in Path(n).parts for n in items):
        raise ValueError("Unexpected private path")
    manifest = {"version": "v0.2", "bridge_version": "0.1.5", "kind": kind,
                "files": {n: digest(data) for n, data in sorted(items.items())}}
    items["RELEASE_MANIFEST.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    path = OUT / name
    if path.exists():
        backup = ROOT / "work/release_backups" / datetime.now().strftime("%Y%m%d_%H%M%S")
        backup.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup / name)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for n, data in sorted(items.items()):
            z.writestr(n, data)
    with zipfile.ZipFile(path) as z:
        if set(z.namelist()) != set(items) or z.testzip() is not None:
            raise ValueError("ZIP contents or CRC mismatch")
        for n, sha in manifest["files"].items():
            if digest(z.read(n)) != sha:
                raise ValueError(f"ZIP SHA mismatch: {n}")
    print(f"PASS {name}: {len(items)} entries; SHA256={digest(path.read_bytes())}")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    events = sorted((ROOT / "build/playtest/game_assets/texts").glob("english_events_*.txt"))
    if len(events) != 11:
        raise ValueError("Expected 11 event files")
    common = {"MonsterRoadtrip_Data/StreamingAssets/game_assets/texts/" + p.name: p.read_bytes()
              for p in events}
    manual = dict(common)
    manual["README-INSTALL-KO-EN.md"] = (ROOT / "docs/MANUAL_OVERWRITE_LINUX.md").read_bytes()
    archive("Monster-Roadtrip-KR-v0.2-manual-overwrite.zip", manual, "events-only")

    items = dict(common)
    for name in ("winhttp.dll", "doorstop_config.ini", ".doorstop_version"):
        items[name] = (STOCK / name).read_bytes()
    for p in sorted((STOCK / "BepInEx/core").iterdir()):
        if p.is_file():
            items["BepInEx/core/" + p.name] = p.read_bytes()
    fixed = (ROOT / "build/runtime_compat/MonoMod.Utils.dll").read_bytes()
    if digest(fixed) != FIXED_SHA:
        raise ValueError("Incorrect MonoMod compatibility DLL")
    items["BepInEx/core/MonoMod.Utils.dll"] = fixed
    plugin = "BepInEx/plugins/RoadtripKoreanFontBridge/"
    items[plugin + "RoadtripKoreanFontBridge.dll"] = (ROOT / "src/RoadtripKoreanFontBridge/bin/Release/RoadtripKoreanFontBridge.dll").read_bytes()
    items[plugin + "english_metatexts.txt"] = (ROOT / "build/preview/english_metatexts.txt").read_bytes()
    items["README-WINDOWS.md"] = (ROOT / "docs/RELEASE_v0.2.md").read_bytes()
    items["VERIFY-WINDOWS.ps1"] = (ROOT / "scripts/verify_windows_release.ps1").read_bytes()
    items["sources/build_mono_corlib_fix.ps1"] = (ROOT / "scripts/build_mono_corlib_fix.ps1").read_bytes()
    for p in (ROOT / "docs/licenses").glob("*-LICENSE.txt"):
        items["licenses/" + p.name] = p.read_bytes()
    # Font bundles and game-owned DLLs are deliberately excluded.
    archive("Monster-Roadtrip-KR-v0.2-Windows-DragDrop.zip", items, "windows-x86-build25955894")


if __name__ == "__main__":
    main()
