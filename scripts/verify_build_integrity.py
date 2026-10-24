"""Independently verify ALL Roadtrip preview TXT files against source assets.

Unlike the builder, this checker never writes any file: it independently checks
that only the fourth field of the specifically translated physical source rows
has changed. It also checks the source-asset SHA, line ordering, tags and digits.

Usage (after build_playtest.py): python -X utf8 scripts/verify_build_integrity.py
All game-owned sources and build outputs are read-only inputs.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from build_playtest import verify_line

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "work/source"
OUTPUT = ROOT / "build/playtest/game_assets/texts"


def sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def check_one(path: Path) -> tuple[int, int, int]:
    name = path.stem
    doc = json.loads(path.read_text(encoding="utf-8"))
    original = (SOURCE / (name + ".txt")).read_text(encoding="utf-8")
    built = (OUTPUT / (name + ".txt")).read_text(encoding="utf-8")
    if sha256(original) != doc["source_sha256"]:
        raise ValueError(f"source_sha256 changed: {name}")
    original_lines = original.splitlines(keepends=True)
    output_lines = built.splitlines(keepends=True)
    if len(original_lines) != len(output_lines):
        raise ValueError(f"source line count changed: {name}")
    if (original.endswith("\n")) != (built.endswith("\n")):
        raise ValueError(f"source EOF format changed: {name}")

    changes = {}
    previous = -1
    for row in doc["entries"]:
        line = row["line"]
        if not isinstance(line, int) or line <= previous or line >= len(original_lines):
            raise ValueError(f"invalid, duplicated or unsorted physical source line: {name}:{line}")
        previous = line
        if line in changes:
            raise ValueError(f"duplicated source line: {name}:{line}")
        changes[line] = row

    for i, (before, after) in enumerate(zip(original_lines, output_lines)):
        if i not in changes:
            if before != after:
                raise ValueError(f"untranslated source line changed: {name}:{i}")
            continue

        row = changes[i]
        fields_before = before.rstrip("\n").split("\t")
        fields_after = after.rstrip("\n").split("\t")
        if len(fields_before) < 4 or len(fields_before) != len(fields_after):
            raise ValueError(f"dialogue tab/field structure changed: {name}:{i}")
        if fields_before[:3] != fields_after[:3] or fields_before[4:] != fields_after[4:]:
            raise ValueError(f"dialogue metadata/control structure changed: {name}:{i}")
        if before.endswith("\n") != after.endswith("\n"):
            raise ValueError(f"line-ending structure changed: {name}:{i}")
        english, korean = fields_before[3], fields_after[3]
        if sha256(english) != row["english_sha256"]:
            raise ValueError(f"sentence sha changed: {name}:{i}")
        if korean != row["ko"]:
            raise ValueError(f"built translation differs from reviewed JSON: {name}:{i}")
        verify_line(english, korean, f"{name}:{i}")
        event = next(
            (x.split("\t", 2)[1].rstrip("\r\n") for x in reversed(original_lines[:i]) if x.startswith(">>>\t")),
            None,
        )
        if event != row["event"]:
            raise ValueError(f"wrong source event: {name}:{i}")

    return len(changes), len(original_lines), len(original) - len(built)


def main() -> None:
    n = 0
    files = sorted((ROOT / "translations").glob("english_events_*.json"))
    if not files:
        raise RuntimeError("No translated event assets found")
    for path in files:
        translated, lines, byte_delta = check_one(path)
        n += translated
        print(f"PASS {path.stem}: {translated} translated / {lines} physical rows; chars_delta={byte_delta}")
    print(f"PASS INDEPENDENT STRUCTURE QA: {n} translated event fields / {len(files)} assets; untouched rows byte-identical")


if __name__ == "__main__":
    main()
