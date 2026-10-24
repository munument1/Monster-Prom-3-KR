"""Build source-faithful loose event text files from reviewed Korean translations.

Only translated files are output. The game installation is never modified.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "work/source"
DEST = ROOT / "build/playtest/game_assets/texts"
TOKEN = re.compile(r"%[^%\r\n]+%|\[[^\[\]\r\n]+\]|<[^<>\r\n]+>")
# Include numeric values embedded directly in identifiers/stat tokens, such as
# "+2BOLDNESS", "+XX", or "Pal 9000"; preserve Arabic digits exactly.
# Variable/control tokens are independently checked by TOKEN.
NUMBER = re.compile(r"(?<!\d)[+-]?\d+(?:\.\d+)?")

# A source-reviewed UI counter format has no prose to localize. Keep this
# exception exact so ordinary untranslated English cannot bypass Hangul QA.
FORMAT_ONLY_UI = {
    ("UI:RES_NEX", "[0] of [1]", "[0] / [1]"),
    ("RES_NEX", "[0] of [1]", "[0] / [1]"),
    # This radio preset is literally named `???` in the English source; it is
    # not encoding damage. Keep this exact UI key/source/value tuple unchanged.
    ("PSE_RAD_RADIONOISE", "???", "???"),
    ("UI:PSE_RAD_RADIONOISE", "???", "???"),
}

# This source row is a wordless shocked reaction written as `...!`.
# Preserve the user's exact bare Unicode ellipsis without inventing an interjection.
# Keep the exception tied to this exact asset/line/source/translation tuple.
SILENT_REACTION_EXCEPTIONS = {
    ("english_events_pitstop:4512", "...!", "……"),
    ("english_events_pitstop:4797", "...?", "……"),
}


def verify_line(english: str, korean: str, ident: str) -> None:
    # An ellipsis-only reaction is a *complete*, legitimate dialogue line in
    # this game. Its Korean localization remains punctuation-only (……), so do
    # not force invented words into a silent character's reaction. No other
    # Hangul-free text is accepted only for the explicit format-only UI
    # exception below.
    source_ellipsis = english.strip()
    # Some source dialogue wraps a silent ellipsis in literal quotation marks,
    # e.g. `"..."`. It is still a punctuation-only reaction, not untranslated
    # prose; Korean may render it as the conventional Unicode ellipsis `……`.
    for left, right in (("\"", "\""), ("“", "”"), ("'", "'")):
        if source_ellipsis.startswith(left) and source_ellipsis.endswith(right) and len(source_ellipsis) >= 2:
            source_ellipsis = source_ellipsis[1:-1].strip()
            break
    source_is_ellipsis = (
        (len(source_ellipsis) >= 3 and all(ch == "." for ch in source_ellipsis))
        or (len(source_ellipsis) >= 1 and all(ch == "…" for ch in source_ellipsis))
    )
    korean_is_ellipsis = len(korean) >= 1 and all(ch == "…" for ch in korean)
    ellipsis_only = (source_is_ellipsis and korean_is_ellipsis) or (
        (ident, english.strip(), korean) in SILENT_REACTION_EXCEPTIONS
    )
    format_only_ui = (ident, english, korean) in FORMAT_ONLY_UI
    if not korean or (not re.search("[가-힣]", korean) and not ellipsis_only and not format_only_ui):
        raise ValueError(f"translation missing Hangul: {ident}")
    if (
        (korean == english and not format_only_ui)
        or "\t" in korean
        or "\r" in korean
        or "\n" in korean
        or "\ufffd" in korean
        or ("???" in korean and not format_only_ui)
    ):
        raise ValueError(f"invalid Korean translation: {ident}")
    if Counter(TOKEN.findall(korean)) != Counter(TOKEN.findall(english)):
        raise ValueError(f"token mismatch: {ident} {TOKEN.findall(english)} != {TOKEN.findall(korean)}")
    if Counter(NUMBER.findall(korean)) != Counter(NUMBER.findall(english)):
        raise ValueError(f"Arabic-digit/stat mismatch: {ident}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create verified Roadtrip event text overrides")
    parser.add_argument(
        "--only",
        metavar="ASSET",
        help="Verify/build only a given english_events_* asset (supports concurrent translation work)",
    )
    args = parser.parse_args()
    files = sorted((ROOT / "translations").glob("english_events_*.json"))
    if args.only:
        name = args.only.removesuffix(".json")
        files = [f for f in files if f.stem == name]
    if not files:
        raise RuntimeError("No translation files")
    n_total = 0
    outputs: list[tuple[Path, str, int]] = []
    for f in files:
        doc = json.loads(f.read_text(encoding="utf-8"))
        name = f.stem
        original = (SRC / f"{name}.txt").read_text(encoding="utf-8")
        sha = hashlib.sha256(original.encode("utf-8")).hexdigest()
        if sha != doc["source_sha256"]:
            raise ValueError(f"source asset changed: {name}")
        lines = original.splitlines(keepends=True)
        visited = set()
        previous_num = -1
        for row in doc["entries"]:
            num = row["line"]
            if not isinstance(num, int) or not (0 <= num < len(lines)):
                raise ValueError(f"out of range source row: {name}:{num}")
            if num <= previous_num:
                raise ValueError(f"translated lines are not in source order: {name}:{num}")
            previous_num = num
            if num in visited:
                raise ValueError(f"duplicate line: {name}:{num}")
            visited.add(num)
            line = lines[num]
            eol = "\n" if line.endswith("\n") else ""
            fields = (line[:-1] if eol else line).split("\t")
            if len(fields) < 4:
                raise ValueError(f"bad source row: {name}:{num}")
            source = fields[3]
            source_hash = hashlib.sha256(source.encode("utf-8")).hexdigest()
            if source_hash != row["english_sha256"]:
                raise ValueError(f"source sentence changed: {name}:{num}")
            event = next((x.split("\t")[1].rstrip("\r\n") for x in reversed(lines[:num]) if x.startswith(">>>\t")), None)
            if event != row["event"]:
                raise ValueError(f"event changed: {name}:{num}")
            verify_line(source, row["ko"], f"{name}:{num}")
            fields[3] = row["ko"]
            lines[num] = "\t".join(fields) + eol
        content = "".join(lines)
        assert len(content.splitlines()) == len(original.splitlines())
        outputs.append((DEST / (name + ".txt"), content, len(visited)))
        n_total += len(visited)
    # Validate the entire requested selection before writing any output.
    DEST.mkdir(parents=True, exist_ok=True)
    for out, content, count in outputs:
        out.write_text(content, encoding="utf-8", newline="\n")
        print(f"BUILT {out.name} translated={count} original_lines={len(content.splitlines())}")
    print(f"PASS translated_lines={n_total} output={DEST}")


if __name__ == "__main__":
    main()
