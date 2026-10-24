"""Read-only candidates for final Korean name/particle proofreading.

Roadtrip protagonists have the displayed names 빨강, 노랑, 초록, 파랑.
Every name ends in a consonant (ㅇ). The same particle rule applies when
%CURRENTPLAYERNAME% or %CURRENTPLAYERNAMECAPS% expands to those names.

This reports candidate issues; it does not alter translations or source files.
Some source contexts need a human decision. In particular, never globally
replace a predicate ending such as `알잖아` with `알이잖아`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

NAMES = (
    "%CURRENTPLAYERNAMECAPS%",
    "%CURRENTPLAYERNAME%",
    "빨강",
    "노랑",
    "초록",
    "파랑",
)
SUFFIXES = {
    "잖아": "이잖아",
    "가": "이",
    "는": "은",
    "를": "을",
    "랑": "이랑",
    "와": "과",
}

PARTICLE = re.compile(
    "(?P<name>" + "|".join(re.escape(name) for name in NAMES) + ")"
    + "(?P<suffix>" + "|".join(SUFFIXES) + ")"
)


def candidates(korean: str) -> list[tuple[str, str, str]]:
    """Return direct name-suffix attachment candidates, never edit content."""
    return [
        (match.group(), match.group("name") + SUFFIXES[match.group("suffix")], match.group("suffix"))
        for match in PARTICLE.finditer(korean)
    ]


def main() -> None:
    total = 0
    by_suffix = {suffix: 0 for suffix in SUFFIXES}
    for path in sorted((ROOT / "translations").glob("english_events_*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for row in data["entries"]:
            findings = candidates(row["ko"])
            if not findings:
                continue
            for old, new, suffix in findings:
                total += 1
                by_suffix[suffix] += 1
                print(f"{path.stem}:{row['line']} [{row['event']}] candidate {old!r} -> {new!r}")
                print(f"  KO: {row['ko']}")
    print(f"CANDIDATES {total}, by suffix: {by_suffix}")
    print("Review original context before editing; this is not an auto-fix.")


if __name__ == "__main__":
    main()
