"""Read-only extraction of Monster Roadtrip English TextAssets to ignored work/.

Requires UnityPy. Does not modify, launch, or inject into the installed game.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path

import UnityPy

GAME = Path(r"C:\Games\Steam\steamapps\common\Monster Prom 3 - Monster Roadtrip")
BUNDLE = GAME / "MonsterRoadtrip_Data/StreamingAssets/aa/StandaloneWindows/texts_assets_all.bundle"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "work/source"
CATALOG = ROOT / "work/catalog.jsonl"
INDEX = ROOT / "work/source_manifest.json"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    records = []
    manifest = {}
    rows = 0
    events = 0
    env = UnityPy.load(str(BUNDLE))
    for asset in env.objects:
        if asset.type.name != "TextAsset":
            continue
        obj = asset.read()
        name = obj.m_Name
        if not name.startswith("english_"):
            continue
        data = obj.m_Script
        if isinstance(data, bytes):
            data = data.decode("utf-8-sig")
        assert isinstance(data, str)
        assert "\r" not in data, f"unexpected CR in {name}"
        raw = data.encode("utf-8")
        (OUT / f"{name}.txt").write_bytes(raw)
        manifest[name] = {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "length": len(raw),
            "game_asset": name,
        }
        if name == "english_metatexts":
            # Meta-texts are an array of JSON-style objects with comments.
            for key, source in re.findall(r'^\s*"([A-Za-z0-9_]+)"\s*:\s*"((?:\\.|[^"\\])*)"', data, flags=re.M):
                records.append({"asset": name, "id": key, "english": source, "kind": "metatext"})
            continue

        event = None
        for n, line in enumerate(data.splitlines()):
            if line.startswith(">>>\t"):
                event = line.split("\t", 2)[1]
                events += 1
                continue
            if not line.startswith("\t"):
                continue
            fields = line.split("\t")
            if len(fields) < 4 or not fields[3].strip():
                continue
            original = fields[3]
            records.append({
                "asset": name,
                "event": event,
                "line": n,
                "speaker": fields[1],
                "expression": fields[2],
                "english": original,
                "english_sha256": hashlib.sha256(original.encode("utf-8")).hexdigest(),
                "kind": "event",
            })
            rows += 1
    assert len(manifest) == 12, manifest
    CATALOG.parent.mkdir(exist_ok=True)
    with CATALOG.open("w", encoding="utf-8", newline="\n") as out:
        for rec in records:
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
    INDEX.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"EXTRACTED assets={len(manifest)} events={events} event_rows={rows} total_catalog={len(records)}")
    print(f"META_KEYS={sum(r['kind']=='metatext' for r in records)}")
    print(f"SOURCE={OUT}")
    print(f"CATALOG={CATALOG}")


if __name__ == "__main__":
    main()
