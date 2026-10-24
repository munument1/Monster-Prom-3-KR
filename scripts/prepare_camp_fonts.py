"""Prepare *local-only* Monster Camp fonts for Roadtrip Korean playtesting.

Reads the user's own installed Monster Camp Addressables FontSet bundle.
Extracts the two original OFL font faces to git-ignored work/fonts/ only.
Does NOT modify either game, install system fonts, or distribute binaries.

Usage: python -X utf8 scripts/prepare_camp_fonts.py
Requires: UnityPy, fonttools
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from io import BytesIO
from pathlib import Path

import UnityPy
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
CAMP_BUNDLE_NAME = "profilesfontsets_assets_all_79f49ff1b358585c59c1388d6a773d92.bundle"
DEFAULT_CAMP = Path(r"C:\Games\Steam\steamapps\common\Monster Prom 2 - Monster Camp")
FONTS = {"header": "Jua", "body": "GamjaFlower"}
FONT_FILES = {"Jua": "Jua.ttf", "GamjaFlower": "GamjaFlower.ttf"}
HANGUL_RANGE = range(0xAC00, 0xD7A4)


def _translation_text() -> str:
    found: list[str] = []
    for filename in sorted((ROOT / "translations").glob("*.json")):
        doc = json.loads(filename.read_text(encoding="utf-8"))
        if filename.stem == "english_metatexts_ko":
            found.extend(doc["translations"].values())
        else:
            found.extend(row["ko"] for row in doc["entries"])
    return "\n".join(found)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--camp", type=Path, default=DEFAULT_CAMP, help="Existing local Monster Camp install")
    parser.add_argument("--audit-only", action="store_true", help="Inspect fonts in memory; do not extract binaries")
    args = parser.parse_args()
    bundle = args.camp / "MonsterCamp_Data/StreamingAssets/aa/StandaloneWindows" / CAMP_BUNDLE_NAME
    if not bundle.is_file():
        raise FileNotFoundError(f"Monster Camp font bundle not found: {bundle}")

    env = UnityPy.load(str(bundle))
    names: dict[str, tuple[bytes, set[int], dict[str, object]]] = {}
    font_ids: dict[int, str] = {}
    korean_set = None
    for obj in env.objects:
        if obj.type.name == "Font":
            asset = obj.read()
            if asset.m_Name not in FONT_FILES:
                continue
            data = bytes(asset.m_FontData)
            tt = TTFont(BytesIO(data))
            codepoints = set((tt.getBestCmap() or {}).keys())
            notices = [r.toUnicode() for r in tt["name"].names if r.nameID == 13]
            if not any("SIL Open Font License" in s for s in notices):
                raise ValueError(f"Missing verifiable OFL license metadata: {asset.m_Name}")
            family = next((r.toUnicode() for r in tt["name"].names if r.nameID == 1), asset.m_Name)
            names[asset.m_Name] = (data, codepoints, {
                "family": family,
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
                "hangul_syllables": sum(cp in codepoints for cp in HANGUL_RANGE),
                "license": "SIL Open Font License 1.1 (embedded font metadata)",
            })
            font_ids[obj.path_id] = asset.m_Name
        elif obj.type.name == "MonoBehaviour":
            try:
                tree = obj.read_typetree()
                if tree.get("m_Name") == "fontset_korean":
                    korean_set = tree
            except Exception:
                pass
    if set(names) != set(FONT_FILES):
        raise ValueError(f"Unexpected Monster Camp font assets: {list(names)}")
    if korean_set is None:
        raise ValueError("Monster Camp fontset_korean profile not found")

    actual_header = font_ids.get(korean_set["unityUiHeaderFont"]["m_PathID"])
    actual_body = font_ids.get(korean_set["unityUiBodyFont"]["m_PathID"])
    if actual_header != FONTS["header"] or actual_body != FONTS["body"]:
        raise ValueError(f"Monster Camp Korean fontset changed: {actual_header}/{actual_body}")

    translated = _translation_text()
    unique = {ord(ch) for ch in translated if ord(ch) in HANGUL_RANGE}
    non_ascii = Counter(ord(ch) for ch in translated if ord(ch) >= 128)
    result: dict[str, object] = {
        "source": "Monster Camp installed fontset_korean (read only)",
        "roles": dict(FONTS),
        "translated_unique_hangul_syllables": len(unique),
        "fonts": {},
        "distribution": "Local playtest only; binary files are gitignored and not uploaded",
    }
    output = ROOT / "work/fonts"
    for role, name in FONTS.items():
        data, glyphs, info = names[name]
        missing = sorted(unique - glyphs)
        missing_symbols = [(cp, n) for cp, n in non_ascii.items() if cp not in glyphs and cp not in unique]
        missing_symbols.sort(key=lambda item: (-item[1], item[0]))
        info["current_translation_missing_hangul"] = len(missing)
        info["current_translation_missing_examples"] = "".join(chr(c) for c in missing[:35])
        info["current_translation_missing_other_characters"] = [
            {"character": chr(cp), "unicode": f"U+{cp:04X}", "occurrences": n}
            for cp, n in missing_symbols
        ]
        info["local_file"] = str(Path("work/fonts") / FONT_FILES[name]).replace("\\", "/")
        result["fonts"][role] = info
        print(f"{role.upper()} {name}: {info['hangul_syllables']}/11172 Hangul; "
              f"missing Hangul in current translations={len(missing)}; "
              f"missing other Unicode={len(missing_symbols)}; sha256={info['sha256'][:16]}...")
        if not args.audit_only:
            output.mkdir(parents=True, exist_ok=True)
            file = output / FONT_FILES[name]
            if file.exists() and file.read_bytes() != data:
                raise FileExistsError(f"Existing font differs; refusing overwrite: {file}")
            if not file.exists():
                file.write_bytes(data)

    if not args.audit_only:
        manifest = output / "font_audit.json"
        manifest.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"LOCAL_ONLY fonts prepared under {output}; manifest={manifest}")
    print(f"PASS: Korean fontset confirmed; unique Hangul glyphs in translations={len(unique)}")


if __name__ == "__main__":
    main()
