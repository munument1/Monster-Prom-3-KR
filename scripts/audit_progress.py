"""Summarize verified candidate coverage without committing game-owned sources."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    catalog = [json.loads(line) for line in (ROOT / "work/catalog.jsonl").read_text(encoding="utf-8").splitlines()]
    source_keys = {
        (r["asset"], r["line"], r["event"], r["english_sha256"])
        for r in catalog if r["kind"] == "event"
    }
    kinds_by_row = {
        (r["asset"], r["line"]): r.get("row_type", "dialogue")
        for r in catalog if r["kind"] == "event"
    }
    known_meta = {r["id"] for r in catalog if r["kind"] == "metatext"}
    seen = set()
    per_file = Counter()
    per_kind = Counter()
    for f in sorted((ROOT / "translations").glob("english_events_*.json")):
        doc = json.loads(f.read_text(encoding="utf-8"))
        for x in doc["entries"]:
            key = (f.stem, x["line"], x["event"], x["english_sha256"])
            if key not in source_keys or key in seen:
                raise ValueError(f"unknown/duplicate event translation: {key}")
            seen.add(key)
            per_file[f.stem] += 1
            per_kind[kinds_by_row[f.stem, x["line"]]] += 1
    meta_file = ROOT / "translations/english_metatexts_ko.json"
    translated_meta = json.loads(meta_file.read_text(encoding="utf-8"))["translations"]
    if not set(translated_meta).issubset(known_meta):
        raise ValueError("unknown metatext keys")
    print("Monster Roadtrip KR — progress")
    print(f"Event dialogue: {len(seen):,} / {len(source_keys):,}")
    print(f"UI metatexts:    {len(translated_meta):,} / {len(known_meta):,} (BepInEx runtime bridge required)")
    print(f"TOTAL:           {len(seen)+len(translated_meta):,} / {len(catalog):,} candidate rows")
    if catalog:
        print(f"COVERAGE:        {(len(seen)+len(translated_meta))/len(catalog)*100:.2f}%")
    print("EVENT_ROW_TYPES:")
    for kind in ("dialogue", "choice", "action"):
        overall = sum(v == kind for v in kinds_by_row.values())
        print(f"  {kind}: {per_kind[kind]:,} / {overall:,}")
    print("BY_FILE:")
    for name, count in sorted(per_file.items()):
        print(f"  {name}: {count}")


if __name__ == "__main__":
    main()
