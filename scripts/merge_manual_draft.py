"""Safely review/append an independently hand-translated event draft.

The input must be authored by a translation worker, not a machine translation
service. Dry run by default. Use --apply only when the owner of the destination
JSON has stopped editing, and only at the exact next contiguous catalog index.

Example:
    python -X utf8 scripts/merge_manual_draft.py work/manual_drafts/maingame_04000_04099.json
    python -X utf8 scripts/merge_manual_draft.py work/manual_drafts/maingame_04000_04099.json --apply

The script never changes source, catalog, game files, Git or old reviewed rows.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path

from build_playtest import verify_line
from verify_translation_delta import verify_stat_effects

ROOT = Path(__file__).resolve().parents[1]
ASSETS = {"english_events_maingame", "english_events_pitstop"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_draft(path: Path) -> dict:
    if not path.is_file() or not path.resolve().is_relative_to((ROOT / "work" / "manual_drafts").resolve()):
        raise ValueError("Draft file must be inside work/manual_drafts")
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError("UTF-8 BOM is not allowed")
    draft = json.loads(raw.decode("utf-8"))
    if not isinstance(draft, dict) or draft.get("asset") not in ASSETS:
        raise ValueError("Invalid hand-translation draft asset")
    return draft


def verify_not_corrupt(original: str, translated: str, ident: str) -> None:
    """Reject obviously damaged UTF-8 text without rejecting silent reactions."""
    if "\ufffd" in translated:
        raise ValueError(f"Replacement character in Korean draft: {ident}")
    # PowerShell 5.1 piping can irreversibly turn Hangul into a run of '?'.
    # Keep punctuation-only reactions when the original is punctuation too.
    spoken_source = re.sub(r"%[^%]+%", "", original)
    if (
        re.search(r"[A-Za-z]", spoken_source)
        and not re.search(r"[가-힣]", translated)
        and re.search(r"\?{2,}", translated)
    ):
        raise ValueError(f"Suspected '?' encoding corruption in Korean draft: {ident}")


def prepare(draft: dict, reviewed: dict) -> list[dict]:
    asset = draft["asset"]
    source_file = ROOT / "work" / "source" / (asset + ".txt")
    source_bytes = source_file.read_bytes()
    source_sha = sha(source_bytes)
    if reviewed["source_sha256"] != source_sha or draft.get("source_sha256") != source_sha:
        raise ValueError("Source SHA mismatch")
    candidate_catalog = [
        json.loads(line)
        for line in (ROOT / "work" / "catalog.jsonl").read_text("utf-8").splitlines()
        if line.strip()
    ]
    catalog = [r for r in candidate_catalog if r["asset"] == asset and r["kind"] == "event"]
    start = draft.get("first_index")
    end = draft.get("last_index")
    rows = draft.get("rows")
    if type(start) is not int or type(end) is not int or not isinstance(rows, list):
        raise ValueError("Draft index/rows schema invalid")
    if start != len(reviewed["entries"]):
        raise ValueError(f"Noncontiguous merge: draft starts {start} but reviewed count is {len(reviewed['entries'])}")
    if end < start or end >= len(catalog) or len(rows) != end - start + 1:
        raise ValueError("Wrong draft range or number of rows")
    source_lines = source_bytes.decode("utf-8").splitlines()
    result = []
    for i, draft_row in enumerate(rows, start=start):
        expected = catalog[i]
        if not isinstance(draft_row, dict):
            raise ValueError(f"Malformed draft row {i}")
        if draft_row.get("i") != i or any(draft_row.get(k) != expected[k] for k in ("line", "event", "english_sha256")):
            raise ValueError(f"Wrong catalog metadata for draft row {i}")
        original = source_lines[expected["line"]].split("\t")
        if len(original) < 4 or original[3] != expected["english"]:
            raise ValueError(f"Bad source physical line for draft row {i}")
        if sha(original[3].encode("utf-8")) != expected["english_sha256"]:
            raise ValueError(f"Changed English source in draft row {i}")
        translated = draft_row.get("ko")
        if not isinstance(translated, str):
            raise ValueError(f"Missing Korean draft row {i}")
        verify_not_corrupt(original[3], translated, f"{asset}:{expected['line']}")
        verify_line(original[3], translated, f"{asset}:{expected['line']}")
        verify_stat_effects(original[3], translated, f"{asset}:{expected['line']}")
        for name in ("%CURRENTPLAYERNAME%", "%CURRENTPLAYERNAMECAPS%"):
            for bad in ("가", "는", "를", "랑", "와", "잖아"):
                if name + bad in translated:
                    raise ValueError(f"Wrong player-name particle at draft index {i}")
        result.append(
            {
                "line": expected["line"],
                "event": expected["event"],
                "english_sha256": expected["english_sha256"],
                "ko": translated,
            }
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("draft", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    draft = load_draft((ROOT / args.draft).resolve())
    path = ROOT / "translations" / (draft["asset"] + ".json")
    old_bytes = path.read_bytes()
    reviewed = json.loads(old_bytes.decode("utf-8"))
    additions = prepare(draft, reviewed)
    print(
        f"PASS DRAFT: {draft['asset']} indices {draft['first_index']}–{draft['last_index']} "
        f"rows={len(additions)}, existing prefix={len(reviewed['entries'])}"
    )
    if not args.apply:
        print("DRY RUN. No reviewed JSON has changed.")
        return
    raw = old_bytes.decode("utf-8")
    suffix = "\n  ]\n}\n"
    if not raw.endswith(suffix) or not reviewed["entries"]:
        raise ValueError("Unexpected reviewed file layout; aborting without a write")
    # No old row contents are reformatted: only the comma after the previous
    # final row and the new, already validated rows are inserted.
    head = raw[: -len(suffix)]
    payload = ",\n".join("    " + json.dumps(row, ensure_ascii=False) for row in additions)
    candidate = (head + ",\n" + payload + suffix).encode("utf-8")
    verify = json.loads(candidate.decode("utf-8"))
    if verify["entries"][: len(reviewed["entries"])] != reviewed["entries"]:
        raise ValueError("Old reviewed entries changed; aborting")
    if verify["entries"][len(reviewed["entries"]) :] != additions:
        raise ValueError("Draft append verification failed; aborting")
    # The active translator must have released file ownership before --apply.
    # Recheck no other editor wrote since the initial read.
    if sha(path.read_bytes()) != sha(old_bytes):
        raise RuntimeError("Concurrent destination modification detected; aborting")
    tmp = path.with_suffix(".json.manualmerge.tmp")
    try:
        tmp.write_bytes(candidate)
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()
    print(f"PASS APPENDED {len(additions)} directly authored Korean rows")


if __name__ == "__main__":
    main()
