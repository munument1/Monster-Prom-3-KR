"""Show the next untranslated Monster Roadtrip candidates without writing files.

The original English text and catalog stay in ignored work/source and work/.
Use --asset english_events_maingame (or english_metatexts) to inspect a batch.

    python -X utf8 scripts/show_translation_queue.py
    python -X utf8 scripts/show_translation_queue.py --asset english_events_maingame --limit 25
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset", help="An asset name such as english_events_maingame or english_metatexts")
    parser.add_argument("--limit", type=int, default=8)
    args = parser.parse_args()
    if args.limit < 1 or args.limit > 500:
        parser.error("--limit must be 1..500")
    catalog = [json.loads(line) for line in (ROOT / "work/catalog.jsonl").read_text("utf-8").splitlines()]
    grouped = defaultdict(list)
    for row in catalog:
        grouped[row["asset"]].append(row)
    if args.asset and args.asset not in grouped:
        parser.error(f"Unknown asset {args.asset}; choose one of {', '.join(sorted(grouped))}")
    assets = [args.asset] if args.asset else sorted(grouped)
    for asset in assets:
        path = ROOT / "translations" / (asset + ("_ko" if asset == "english_metatexts" else "") + ".json")
        if not path.exists():
            raise FileNotFoundError(f"Translation JSON unavailable: {path}")
        doc = json.loads(path.read_text("utf-8"))
        if asset == "english_metatexts":
            existing = set(doc["translations"])
            remaining = [r for r in grouped[asset] if r["id"] not in existing]
        else:
            existing = {r["line"] for r in doc["entries"]}
            remaining = [r for r in grouped[asset] if r["line"] not in existing]
        print(f"\n{asset}: completed={len(existing)}/{len(grouped[asset])}, remaining={len(remaining)}")
        if args.asset:
            for row in remaining[:args.limit]:
                key = str(row["line"]) if asset != "english_metatexts" else row["id"]
                event = row.get("event", "")
                kind = row.get("row_type", "")
                print(f"  {key} {kind} {event} :: {row['english']}")
        elif remaining:
            row = remaining[0]
            key = row["line"] if asset != "english_metatexts" else row["id"]
            print(f"  NEXT: {key} ({row.get('event', '')})")


if __name__ == "__main__":
    main()
