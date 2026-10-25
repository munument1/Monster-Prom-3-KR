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
# Match actual variable placeholders rather than any text between percent
# signs. Literal percentages adjacent to placeholders (e.g. `100% OBJECTIFY
# %HISHERCAPS%`) otherwise create false `% ... %` tokens and reject valid
# translations. The source catalog's real percent placeholders use this
# identifier alphabet, including apostrophes in tokens such as `%VERB_'S_'VE%`.
TOKEN = re.compile(r"%[A-Za-z0-9_']+%|\[[^\[\]\r\n]+\]|<[^<>\r\n]+>")
# The English conjugation/name macros in this exact dialogue expand into
# broken Korean ("??? ... 그녀's 그녀의"). The localized line refers to the
# same challenger without these English-only grammatical constructs.
KOREAN_GRAMMAR_TOKEN_EXCEPTIONS = {
    ("english_events_maingame:850",
     "Yup. %CURRENTPLAYERNAME% over here thinks %HESHE%%VERB_'S_'VE% got some big, brass 8-balls between %HISHER% legs!",
     "맞아. 저 도전자는 자기 다리 사이에 큼지막한 황동 8번 공 두 개가 달렸다고 생각하나 봐!"),
}
# Include numeric values embedded directly in identifiers/stat tokens, such as
# "+2BOLDNESS", "+XX", or "Pal 9000"; preserve Arabic digits exactly.
# Variable/control tokens are independently checked by TOKEN.
NUMBER = re.compile(r"(?<!\d)[+-]?\d+(?:\.\d+)?")

# Source stat effects are executable event syntax, not translatable prose.
# The game finds effect tokens using word boundaries. Korean postpositions
# directly after the ASCII enum name (e.g. +N2 MAGIC을) prevent that parse,
# even though the underlying code bytes are otherwise correct. A U+200B
# boundary is invisible to players and was checked against a live Steam game
# load: 345 event-parser errors dropped to the single legacy wrong-enum row.
STAT_EFFECT = re.compile(
    r"(?<![A-Za-z])([+-])(N?[0-9]+)\s*"
    r"(STAMINA|HYPE|MAGIC|MIND|SOUL|MONEY)(?![A-Za-z])"
)
STAT_EFFECT_GLUED_TO_HANGUL = re.compile(
    r"(?P<code>[+-]N?[0-9]+[ ]*(?:STAMINA|HYPE|MAGIC|MIND|SOUL|MONEY))"
    r"(?P<postposition>[\uac00-\ud7a3])"
)
GAME_STAT_BOUNDARY = "\u200b"


def game_safe_stat_effects(korean: str) -> str:
    """Insert an invisible word boundary AFTER valid stat syntax in game TXT.

    Reviewed JSON remains natural Korean and contains no hidden characters.
    This is idempotent, preserves exactly all stat codes and Hangul text, and
    cannot affect UI strings or non-stat conversation.
    """
    return STAT_EFFECT_GLUED_TO_HANGUL.sub(
        lambda hit: hit.group("code") + GAME_STAT_BOUNDARY + hit.group("postposition"),
        korean,
    )

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

# These exact event fields are literal angle-bracket command/cue strings, not
# player-facing prose. Preserve them byte-for-byte; do not generalize this
# exception to arbitrary untranslated English wrapped in angle brackets.
FORMAT_ONLY_EVENT_TAGS = {
    ("english_events_maingame:15506", "<INITIATING DISHONESTY_SCRIPT.txt..........>", "<INITIATING DISHONESTY_SCRIPT.txt..........>"),
    ("english_events_maingame:15311", "<INITIATING_BIRTHDAY_SOUP_CHANT_VER._38_[FINAL_FINAL!!_THIS_TIME_FOR_REAL_FINAL]:>", "<INITIATING_BIRTHDAY_SOUP_CHANT_VER._38_[FINAL_FINAL!!_THIS_TIME_FOR_REAL_FINAL]:>"),
    ("english_events_maingame:15322", "<SINGING_IS_NONNEGOTIABLE>", "<SINGING_IS_NONNEGOTIABLE>"),
    ("english_events_maingame:15323", "<INITIATING_LIFE_CYCLE_OF_SOUP_SONG_[10_HOUR_LOOP]...>", "<INITIATING_LIFE_CYCLE_OF_SOUP_SONG_[10_HOUR_LOOP]...>"),
    ("english_events_maingame:15329", "<INITIATING_SOUPIFICATION_PROCEDURE_ED._[RESISTANCE_IS_FUTILE]:>", "<INITIATING_SOUPIFICATION_PROCEDURE_ED._[RESISTANCE_IS_FUTILE]:>"),
    ("english_events_maingame:15334", "<INITIATING_SOUPIFICATION_PROCEDURE_ED._[ABORT_VIOLENCE]:>", "<INITIATING_SOUPIFICATION_PROCEDURE_ED._[ABORT_VIOLENCE]:>"),
    ("english_events_maingame:15359", "<YES_WAY>", "<YES_WAY>"),
    ("english_events_maingame:15360", "<INITIATING_SEXUALLY_AROUSING_THEME_[!DO_NOT_RELEASE!]_NO._69_(NICE):>", "<INITIATING_SEXUALLY_AROUSING_THEME_[!DO_NOT_RELEASE!]_NO._69_(NICE):>"),
    ("english_events_maingame:15426", "<BE_NOT_AFRAID_CHILDREN_WE_ARE_38.6%_HARMLESS>", "<BE_NOT_AFRAID_CHILDREN_WE_ARE_38.6%_HARMLESS>"),
    ("english_events_maingame:15427", "<INITIATING_CALMING_MELODY_[EVERY_SOUP_IN_ALPHABETICAL_ORDER.WAV]_TAPE_1_OF_6>", "<INITIATING_CALMING_MELODY_[EVERY_SOUP_IN_ALPHABETICAL_ORDER.WAV]_TAPE_1_OF_6>"),
}

# Intentional visual emoticon, not an untranslated English sentence.
LITERAL_EVENT_CUES = {
    ("english_events_maingame:15522", "UwU", "UwU"),
    # Standalone hyphen in a skincare event: source formatting marker, not dialogue.
    ("english_events_maingame:24516", "-", "-"),
    ("english_events_maingame:25419", "-", "-"),
    ("english_events_maingame:26224", "-", "-"),
    ("english_events_maingame:26234", "-", "-"),
    ("english_events_maingame:26034", "-", "-"),
    ("english_events_maingame:26109", "-", "-"),
    ("english_events_maingame:26119", "-", "-"),
    ("english_events_maingame:26348", "-", "-"),
    ("english_events_maingame:26358", "-", "-"),
    ("english_events_maingame:26368", "-", "-"),
    ("english_events_maingame:26378", "-", "-"),
    ("english_events_maingame:26388", "-", "-"),
}

# This source row is a wordless shocked reaction written as `...!`.
# Preserve the user's exact bare Unicode ellipsis without inventing an interjection.
# Keep the exception tied to this exact asset/line/source/translation tuple.
SILENT_REACTION_EXCEPTIONS = {
    ("english_events_pitstop:4512", "...!", "……"),
    ("english_events_pitstop:4797", "...?", "……"),
    ("english_events_maingame:16184", "...?", "……"),
    ("english_events_maingame:16938", "...!", "……"),
    ("english_events_maingame:16939", "...!", "……"),
    ("english_events_maingame:24276", "...!!!", "……"),
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
    format_only_event_tag = (ident, english, korean) in FORMAT_ONLY_EVENT_TAGS
    format_only = format_only_ui or format_only_event_tag or (ident, english, korean) in LITERAL_EVENT_CUES
    if not korean or (not re.search("[가-힣]", korean) and not ellipsis_only and not format_only):
        raise ValueError(f"translation missing Hangul: {ident}")
    if (
        (korean == english and not format_only)
        or "\t" in korean
        or "\r" in korean
        or "\n" in korean
        or "\ufffd" in korean
        or ("???" in korean and not format_only)
    ):
        raise ValueError(f"invalid Korean translation: {ident}")
    if Counter(TOKEN.findall(korean)) != Counter(TOKEN.findall(english)) and (ident, english, korean) not in KOREAN_GRAMMAR_TOKEN_EXCEPTIONS:
        raise ValueError(f"token mismatch: {ident} {TOKEN.findall(english)} != {TOKEN.findall(korean)}")
    if Counter(NUMBER.findall(korean)) != Counter(NUMBER.findall(english)):
        raise ValueError(f"Arabic-digit/stat mismatch: {ident}")
    if Counter(STAT_EFFECT.findall(korean)) != Counter(STAT_EFFECT.findall(english)):
        raise ValueError(f"stat-effect enum expression mismatch: {ident}")


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
        safe_delimiters = 0
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
            game_text = game_safe_stat_effects(row["ko"])
            safe_delimiters += game_text.count(GAME_STAT_BOUNDARY)
            fields[3] = game_text
            lines[num] = "\t".join(fields) + eol
        content = "".join(lines)
        assert len(content.splitlines()) == len(original.splitlines())
        outputs.append((DEST / (name + ".txt"), content, len(visited), safe_delimiters))
        n_total += len(visited)
    # Validate the entire requested selection before writing any output.
    DEST.mkdir(parents=True, exist_ok=True)
    for out, content, count, delimiters in outputs:
        out.write_text(content, encoding="utf-8", newline="\n")
        print(f"BUILT {out.name} translated={count} original_lines={len(content.splitlines())} parser_safe_stat_boundaries={delimiters}")
    print(f"PASS translated_lines={n_total} output={DEST}")


if __name__ == "__main__":
    main()
