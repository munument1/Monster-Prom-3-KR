"""Create a translation-only reproduction ZIP, never bundle game-owned assets.

The ZIP is a source/test kit, NOT a self-contained Workshop mod. It excludes
extracted game TextAssets, font files, BepInEx dependencies and all work/ data.
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "build/releases/Monster-Roadtrip-KR-100pct-source-testkit.zip"
BRIDGE = ROOT / "src/RoadtripKoreanFontBridge/bin/Release/RoadtripKoreanFontBridge.dll"


def files_to_package() -> list[tuple[Path, str]]:
    files: list[Path] = [ROOT / "README.md"]
    for directory, suffixes in (
        ("docs", {".md", ".json"}),
        ("translations", {".json"}),
        ("scripts", {".py", ".ps1"}),
        ("tests", {".py", ".cs", ".rs"}),
        ("src/RoadtripKoreanFontBridge", {".cs", ".csproj", ".md"}),
    ):
        files.extend(
            file for file in (ROOT / directory).iterdir()
            if file.is_file() and file.suffix.lower() in suffixes
            and not file.name.startswith("CODEX_HANDOFF_")
        )
    items = [(file, file.relative_to(ROOT).as_posix()) for file in files]
    items.extend((file, file.relative_to(ROOT).as_posix())
                 for file in (ROOT / "docs/licenses").glob("*.txt"))
    if BRIDGE.is_file():
        # Our own plugin code, not game/BepInEx binaries or extracted fonts.
        # Keep the author's build output at the installer-expected relative path.
        items.append((BRIDGE, BRIDGE.relative_to(ROOT).as_posix()))
    return sorted(items, key=lambda item: item[1])


def main() -> None:
    items = files_to_package()
    assert (ROOT / "docs/RELEASE_CANDIDATE.md").is_file()
    assert (ROOT / "translations/english_events_maingame.json").is_file()
    assert len(items) == len({name for _, name in items})
    manifest: dict[str, object] = {
        "kind": "translation-source-testkit-not-workshop-release",
        "candidate_coverage": "30255/30255",
        "game_owned_assets_included": False,
        "items": {},
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path, name in items:
            assert path.is_file(), path
            if name.startswith(("work/", "build/")):
                raise ValueError(f"Refusing to bundle ignored game data: {name}")
            if path.suffix.lower() in {".assets", ".bundle", ".ttf", ".otf", ".exe"}:
                raise ValueError(f"Refusing to bundle game/font binary: {name}")
            data = path.read_bytes()
            archive.writestr(name, data)
            manifest["items"][name] = hashlib.sha256(data).hexdigest()
        archive.writestr("TESTKIT_MANIFEST.json", json.dumps(manifest, indent=2) + "\n")

    with zipfile.ZipFile(OUTPUT) as archive:
        included = json.loads(archive.read("TESTKIT_MANIFEST.json"))
        for name, digest in included["items"].items():
            if hashlib.sha256(archive.read(name)).hexdigest() != digest:
                raise ValueError(f"ZIP digest mismatch: {name}")
        if set(archive.namelist()) != set(included["items"]) | {"TESTKIT_MANIFEST.json"}:
            raise ValueError("Unexpected ZIP contents")
    print(f"PASS SOURCE TESTKIT: {OUTPUT}")
    print(f"FILES={len(items)} BYTES={OUTPUT.stat().st_size}")
    print(f"SHA256={hashlib.sha256(OUTPUT.read_bytes()).hexdigest()}")
    print("No game-owned asset files, third-party loader or font binaries are bundled.")


if __name__ == "__main__":
    main()
