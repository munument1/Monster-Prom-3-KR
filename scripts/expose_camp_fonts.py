"""Expose Monster Camp's original Jua/Gamja fonts as root assets for Roadtrip.

The original Unity 2019 Monster Camp font bundle has only FontSetProfile assets
in its visible AssetBundle container. Roadtrip has no FontSetProfile class, so
LoadAllAssets<Font>() returns zero even though both font objects are embedded.

This script modifies ONLY a *local output copy*: it registers the existing Font
objects as two additional container roots. No embedded font data or source game
DLL/AssetBundle is changed. The resulting Unity 2019 serialized bundle was
tested loading both fonts in Roadtrip Unity 2021.3.15f1 (Windows, 2026-10-24).

The generated bundle includes game-owned objects and MUST NOT be committed or
redistributed. Recreate it only from the user's locally installed Monster Camp.

Usage: python -X utf8 scripts/expose_camp_fonts.py
Dependency: UnityPy
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import tempfile
from pathlib import Path

import UnityPy
from UnityPy.classes.PPtr import PPtr
from UnityPy.classes.generated import AssetInfo

ROOT = Path(__file__).resolve().parents[1]
CAMP = Path(r"C:\Games\Steam\steamapps\common\Monster Prom 2 - Monster Camp")
SOURCE_BUNDLE_NAME = "profilesfontsets_assets_all_79f49ff1b358585c59c1388d6a773d92.bundle"
OUTPUT = ROOT / "build/fontbundles/roadtrip_korean_fonts.bundle"
EXPECTED_FONTS = {"Jua", "GamjaFlower"}


def read_font_roots(bundle_path: Path) -> dict[str, int]:
    """Validate that an existing output bundle exposes both fonts by path ID."""
    # UnityPy's filename-backed reader can hold an exclusive Windows handle.
    # Read bytes so the generated candidate can be moved/cleaned up on Windows.
    env = UnityPy.load(bundle_path.read_bytes())
    ab = next(obj.read() for obj in env.objects if obj.type.name == "AssetBundle")
    roots = {
        key.removeprefix("Assets/KoreanFonts/").removesuffix(".ttf"): info.asset.m_PathID
        for key, info in ab.m_Container
        if key.startswith("Assets/KoreanFonts/") and key.endswith(".ttf")
    }
    font_ids = {
        obj.read().m_Name: obj.path_id
        for obj in env.objects
        if obj.type.name == "Font" and obj.read().m_Name in EXPECTED_FONTS
    }
    if roots != font_ids or set(roots) != EXPECTED_FONTS:
        raise ValueError(f"Font root references do not match real embedded fonts: {roots} vs {font_ids}")
    return roots


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--camp", type=Path, default=CAMP, help="User-owned Monster Camp install")
    parser.add_argument("--output", type=Path, default=OUTPUT, help="Ignored local output bundle path")
    args = parser.parse_args()

    source = args.camp / "MonsterCamp_Data/StreamingAssets/aa/StandaloneWindows" / SOURCE_BUNDLE_NAME
    if not source.is_file():
        raise FileNotFoundError(f"Monster Camp original font bundle not found: {source}")

    output = args.output.resolve()
    if output == source.resolve():
        raise ValueError("Refusing to overwrite the original Monster Camp bundle")
    # Keep all output in the ignored project build tree; no accidental game edits.
    if ROOT.resolve() not in output.parents or "build" not in output.relative_to(ROOT).parts:
        raise ValueError("Output must be inside this repository's ignored build/ directory")

    if output.exists():
        roots = read_font_roots(output)
        print(f"PASS EXISTING BUNDLE: {output} roots={roots}")
        return

    env = UnityPy.load(str(source))
    object_ref = next(obj for obj in env.objects if obj.type.name == "AssetBundle")
    asset_bundle = object_ref.read()
    korean_profile = next(
        info for key, info in asset_bundle.m_Container
        if key.endswith("/fontset_korean.asset")
    )
    font_ids = {
        obj.read().m_Name: obj.path_id
        for obj in env.objects
        if obj.type.name == "Font" and obj.read().m_Name in EXPECTED_FONTS
    }
    if set(font_ids) != EXPECTED_FONTS:
        raise ValueError(f"Expected Jua/GamjaFlower were not both found: {font_ids}")

    for name, path_id in font_ids.items():
        key = f"Assets/KoreanFonts/{name}.ttf"
        if any(old_key == key for old_key, _ in asset_bundle.m_Container):
            raise ValueError(f"Font already exposed in source bundle: {key}")
        asset_bundle.m_Container.append((
            key,
            AssetInfo(
                asset=PPtr(m_FileID=0, m_PathID=path_id,
                           assetsfile=korean_profile.asset.assetsfile),
                preloadIndex=korean_profile.preloadIndex,
                preloadSize=korean_profile.preloadSize,
            ),
        ))
    asset_bundle.m_Container.sort(key=lambda row: row[0])
    asset_bundle.save()

    output.parent.mkdir(parents=True, exist_ok=True)
    workdir = ROOT / "work"
    workdir.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="roadtrip_font_bundle_", dir=workdir) as temporary:
        env.save(pack="lz4", out_path=temporary)
        candidate = Path(temporary) / source.name
        if not candidate.is_file():
            raise RuntimeError("UnityPy did not emit the expected output bundle")
        roots = read_font_roots(candidate)
        if output.exists():
            raise FileExistsError(f"Output unexpectedly appeared while building: {output}")
        shutil.move(str(candidate), str(output))
        print(f"PASS BUILT {output} ({output.stat().st_size:,} bytes)")
        print(f"ROOTS {roots}")
        print(f"OUTPUT_SHA256 {hashlib.sha256(output.read_bytes()).hexdigest()}")
        print("LOCAL ONLY: includes original Monster Camp content, do not distribute or upload")


if __name__ == "__main__":
    main()
