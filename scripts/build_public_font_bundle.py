"""Package public OFL fonts in a minimal native Unity font container.

Uses the local bundle only as a serialization-format template. No game scripts,
profiles, images, shaders, other fonts or original font bytes are retained.
Output is separate from the user's tested local bundle and game installation.
"""
from __future__ import annotations

import copy
import argparse
import hashlib
import json
import urllib.request
from collections import Counter
from pathlib import Path

import UnityPy
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "work/public_fonts"
OUT = ROOT / "build/public_fonts/roadtrip_korean_fonts.bundle"
NAMES = ("Jua", "GamjaFlower")


def pointers(value):
    if isinstance(value, dict):
        if set(value) == {"m_FileID", "m_PathID"}:
            yield value
        else:
            for v in value.values():
                yield from pointers(v)
    elif isinstance(value, (tuple, list)):
        for v in value:
            yield from pointers(v)


def validate(path: Path) -> dict:
    env = UnityPy.load(path.read_bytes())
    objects = {o.path_id: o for o in env.objects}
    assert Counter(o.type.name for o in objects.values()) == {
        "Font": 2, "Material": 2, "Texture2D": 2, "AssetBundle": 1}
    for o in objects.values():
        d = o.read_typetree()
        for p in pointers(d):
            if p["m_PathID"] == 0:
                continue
            assert (p["m_FileID"] == 0 and p["m_PathID"] in objects) or (
                p["m_FileID"] == 1 and p["m_PathID"] == 10101)
        if o.type.name == "Font":
            assert d["m_Name"] in NAMES
            assert bytes(d["m_FontData"]) == (PUBLIC / (d["m_Name"] + ".ttf")).read_bytes()
            assert not d["m_CharacterRects"] and not d["m_KerningValues"]
        elif o.type.name == "Texture2D":
            assert d["m_Width"] == d["m_Height"] == d["m_CompleteImageSize"] == 0
            assert d["m_StreamData"]["size"] == 0 and not d["image data"]
        elif o.type.name == "AssetBundle":
            assert {k for k, _ in d["m_Container"]} == {
                "Assets/KoreanFonts/" + n + ".ttf" for n in NAMES}
            assert not d["m_Dependencies"]
    serialized = next(iter(objects.values())).assets_file
    assert len(serialized.types) == 4 and not serialized.script_types
    required = set()
    for p in (ROOT / "translations").glob("*.json"):
        required.update(c for c in p.read_text(encoding="utf-8") if "\uac00" <= c <= "\ud7a3")
    for name in NAMES:
        cmap = TTFont(PUBLIC / (name + ".ttf")).getBestCmap()
        assert all(ord(c) in cmap for c in required), name
    return {"objects": len(objects), "korean_syllables": len(required),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true", help="Download pinned public OFL originals")
    args = parser.parse_args()
    provenance = json.loads((ROOT / "docs/PUBLIC_FONT_SOURCES.json").read_text())
    if args.fetch:
        PUBLIC.mkdir(parents=True, exist_ok=True)
        for name, item in provenance["files"].items():
            raw = urllib.request.urlopen(item["url"]).read()
            assert hashlib.sha256(raw).hexdigest() == item["sha256"], name
            (PUBLIC / name).write_bytes(raw)
    for name, item in provenance["files"].items():
        assert hashlib.sha256((PUBLIC / name).read_bytes()).hexdigest() == item["sha256"]
    env = UnityPy.load((ROOT / "build/fontbundles/roadtrip_korean_fonts.bundle").read_bytes())
    bundle = next(iter(env.files.values()))
    serialized = next(f for f in bundle.files.values() if hasattr(f, "objects"))
    objects = serialized.objects
    ab = next(o for o in objects.values() if o.type.name == "AssetBundle")
    keep = [ab]
    for name in NAMES:
        font = next(o for o in objects.values() if o.type.name == "Font" and o.read().m_Name == name)
        d = font.read_typetree()
        keep.extend([font, objects[d["m_DefaultMaterial"]["m_PathID"]], objects[d["m_Texture"]["m_PathID"]]])
    ids = {o.path_id: i + 1 for i, o in enumerate(keep)}
    for o in keep:
        d = copy.deepcopy(o.read_typetree())
        if o.type.name == "Font":
            d["m_FontData"] = list((PUBLIC / (d["m_Name"] + ".ttf")).read_bytes())
        if o.type.name == "AssetBundle":
            d["m_Name"] = d["m_AssetBundleName"] = "roadtrip_korean_fonts.bundle"
            d["m_Dependencies"] = []
            d["m_MainAsset"] = {"preloadIndex": 0, "preloadSize": 0,
                                "asset": {"m_FileID": 0, "m_PathID": 0}}
            d["m_PreloadTable"] = [{"m_FileID": 0, "m_PathID": x.path_id} for x in keep[1:]]
            d["m_Container"] = [
                ("Assets/KoreanFonts/" + name + ".ttf",
                 {"preloadIndex": i * 3, "preloadSize": 3,
                  "asset": {"m_FileID": 0, "m_PathID": keep[1 + i * 3].path_id}})
                for i, name in enumerate(NAMES)]
        for p in pointers(d):
            if p["m_FileID"] == 0 and p["m_PathID"] != 0:
                p["m_PathID"] = ids[p["m_PathID"]]
        o.save_typetree(d)
    used_types = sorted({o.type_id for o in keep})
    types = [serialized.types[i] for i in used_types]
    for o in keep:
        o.path_id = ids[o.path_id]
        o.type_id = used_types.index(o.type_id)
    serialized.types = types
    serialized.objects = {o.path_id: o for o in keep}
    serialized.script_types = []
    serialized.ref_types = []
    serialized.userInformation = "Public OFL Jua and Gamja Flower; font-only container"
    assert len(serialized.externals) == 1
    assert serialized.externals[0].path == "Library/unity default resources"
    serialized.name = "CAB-roadtrip-public-ofl-fonts"
    bundle.files = {serialized.name: serialized}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(bundle.save(packer="lz4"))
    print("PASS public font-only bundle:", json.dumps(validate(OUT)))


if __name__ == "__main__":
    main()
