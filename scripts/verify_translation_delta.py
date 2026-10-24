"""Read-only batch guard: don't overwrite previously reviewed translations.

Compares working translation JSON to a baseline Git revision (default: HEAD).
Only subsequent catalog candidates may be appended, in exact source order.
Includes independent guards against missing per-row metadata, damaged Hangul,
source checksums, variables, tags and Arabic numeric sequences.

    python -X utf8 scripts/verify_translation_delta.py
    python -X utf8 scripts/verify_translation_delta.py --asset english_events_pitstop
    python -X utf8 scripts/verify_translation_delta.py --base-ref HEAD~1

No game files, baseline Git revisions or translation files are modified.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

from build_playtest import verify_line

ROOT = Path(__file__).resolve().parents[1]

# Explicit, source-reviewed corrections to previously committed Korean text.
# Each exception is narrow: the old Korean value, new Korean value, and row
# identity must all match. This does not permit arbitrary edits to old rows.
APPROVED_EVENT_CORRECTIONS = {
    ("english_events_pitstop", 1739): {
        "old": "(하지만 %CURRENTPLAYERNAME%를 거절해서 %HIMHER%에게 상처를 주면 어떡하지? 못되게 보이고 싶진 않은데...)",
        "new": "(하지만 %HIMHER%를 거절해서 %CURRENTPLAYERNAME%의 마음에 상처를 주면 어떡하지? 못되게 보이고 싶진 않은데...)",
        "reason": "The speaker rejects HIMHER, which hurts CURRENTPLAYERNAME's feelings.",
    },
    ("english_events_endings", 685): {
        "old": "생각해 보니 친구들은 널 어디서도 본 적이 없다. 넌 이 로드 트립에 %HISHER% 길을 비집고 들어와 기억을 망가뜨린 빌어먹을 글리치일 뿐이다.",
        "new": "생각해 보니 친구들은 널 어디서도 본 적이 없다. 넌 이 로드트립에 끼어들려고 %HISHER% 기억을 망가뜨린 빌어먹을 글리치일 뿐이다.",
        "reason": "The glitch corrupted their memories to insert itself into the road trip; this is not a literal path/way.",
    },
}


def baseline_json(ref: str, rel_path: str) -> dict:
    result = subprocess.run(
        ["git", "show", f"{ref}:{rel_path}"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    )
    return json.loads(result.stdout.decode("utf-8"))


def read_json(path: Path) -> dict:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError(f"BOM in {path.name}")
    return json.loads(raw.decode("utf-8"))


def is_approved_event_correction(asset: str, old_row: dict, new_row: dict) -> bool:
    """Accept only a precisely enumerated correction to an existing row."""
    if old_row == new_row:
        return False
    ident = (asset, old_row.get("line"))
    approval = APPROVED_EVENT_CORRECTIONS.get(ident)
    if approval is None:
        raise ValueError(f"previously translated event text changed: {asset}:{old_row.get('line')}")
    metadata = ("line", "event", "english_sha256")
    if any(old_row.get(key) != new_row.get(key) for key in metadata):
        raise ValueError(f"approved correction changed row identity: {asset}:{old_row.get('line')}")
    if old_row.get("ko") != approval["old"] or new_row.get("ko") != approval["new"]:
        raise ValueError(f"approved correction value mismatch: {asset}:{old_row.get('line')}")
    return True


def validate_event(path: Path, current: dict, baseline: dict, catalog: list[dict]) -> tuple[int, int]:
    if current["source_sha256"] != baseline["source_sha256"]:
        raise ValueError(f"original source SHA changed: {path.name}")
    old = baseline["entries"]
    new = current["entries"]
    if len(new) < len(old):
        raise ValueError(f"previously translated event rows removed: {path.name}")
    corrected_rows = []
    for old_row, new_row in zip(old, new[:len(old)]):
        if is_approved_event_correction(path.stem, old_row, new_row):
            corrected_rows.append(new_row)
    expected = [
        r for r in catalog
        if r["kind"] == "event" and r["asset"] == path.stem
    ]
    if len(new) > len(expected):
        raise ValueError(f"too many translations in {path.name}")
    if [
        (r["line"], r["event"], r["english_sha256"]) for r in new
    ] != [
        (r["line"], r["event"], r["english_sha256"])
        for r in expected[:len(new)]
    ]:
        raise ValueError(f"noncontiguous or incorrect original metadata: {path.name}")
    source = (ROOT / "work" / "source" / (path.stem + ".txt")).read_text("utf-8")
    if hashlib.sha256(source.encode("utf-8")).hexdigest() != current["source_sha256"]:
        raise ValueError(f"source asset checksum mismatch: {path.name}")
    lines = source.splitlines()
    for row in [*corrected_rows, *new[len(old):]]:
        fields = lines[row["line"]].split("\t")
        if len(fields) < 4:
            raise ValueError(f"bad original text: {path.name}:{row['line']}")
        english = fields[3]
        if hashlib.sha256(english.encode("utf-8")).hexdigest() != row["english_sha256"]:
            raise ValueError(f"original sentence checksum mismatch: {path.name}:{row['line']}")
        verify_line(english, row["ko"], f"{path.stem}:{row['line']}")
    return len(new) - len(old), len(corrected_rows)


def validate_ui(current: dict, baseline: dict, catalog: list[dict]) -> int:
    if current["source_sha256"] != baseline["source_sha256"]:
        raise ValueError("UI source SHA changed")
    old = baseline["translations"]
    new = current["translations"]
    for key, value in old.items():
        if new.get(key) != value:
            raise ValueError(f"reviewed UI text changed: {key}")
    known = [r for r in catalog if r["kind"] == "metatext"]
    expected_new = [r["id"] for r in known if r["id"] not in old][:len(new) - len(old)]
    actual_new = [key for key in new if key not in old]
    if expected_new != actual_new:
        raise ValueError("new UI IDs are not the next catalog sequence")
    by_id = {r["id"]: r for r in known}
    for key in actual_new:
        english = by_id[key]["english"]
        korean = new[key]
        verify_line(english, korean, f"UI:{key}")
    return len(actual_new)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-ref", default="HEAD")
    parser.add_argument("--asset", help="Only check this event asset or english_metatexts (for concurrent edits)")
    args = parser.parse_args()
    catalog = [json.loads(s) for s in (ROOT / "work/catalog.jsonl").read_text("utf-8").splitlines()]
    totals = Counter()
    for path in sorted((ROOT / "translations").glob("english_events_*.json")):
        if args.asset and path.stem != args.asset:
            continue
        baseline = baseline_json(args.base_ref, path.relative_to(ROOT).as_posix())
        new_count, correction_count = validate_event(path, read_json(path), baseline, catalog)
        totals["events"] += new_count
        totals["corrections"] += correction_count
        if new_count:
            print(f"PASS {path.stem}: +{new_count} reviewed event rows")
    if not args.asset or args.asset == "english_metatexts":
        path = ROOT / "translations/english_metatexts_ko.json"
        baseline = baseline_json(args.base_ref, path.relative_to(ROOT).as_posix())
        totals["ui"] = validate_ui(read_json(path), baseline, catalog)
    if args.asset and args.asset != "english_metatexts":
        expected = ROOT / "translations" / (args.asset + ".json")
        if not expected.is_file():
            parser.error(f"unknown event asset: {args.asset}")
    print(f"PASS immutable-baseline QA: +{totals['events']} events, +{totals['ui']} UI, {totals['corrections']} explicitly approved corrections")


if __name__ == "__main__":
    main()
