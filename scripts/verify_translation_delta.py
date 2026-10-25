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
import re
import subprocess
from collections import Counter
from pathlib import Path

from build_playtest import verify_line

ROOT = Path(__file__).resolve().parents[1]

# Confirmed via installed Assembly-CSharp.dll: MainGameEventManager.ProcessStatPatterns
# parses +/-N2 STAMINA and similar signed uppercase stat labels into a StatType
# enum and applies stat changes. The names in these expressions are executable
# game syntax, not untranslated natural-language text.
STAT_EFFECT = re.compile(
    r"(?<![A-Za-z])([+-])(N?[0-9]+)\s*"
    r"(STAMINA|HYPE|MAGIC|MIND|SOUL|MONEY)(?![A-Za-z])"
)


def verify_stat_effects(english: str, korean: str, ident: str) -> None:
    """Only compare actual six-stat effect expressions, not general prose."""
    expected = Counter(STAT_EFFECT.findall(english))
    actual = Counter(STAT_EFFECT.findall(korean))
    if expected != actual:
        raise ValueError(
            f"stat-effect enum expression mismatch: {ident}: "
            f"{dict(expected)} != {dict(actual)}"
        )

# Explicit, source-reviewed corrections to previously committed Korean text.
# Each exception is narrow: the old Korean value, new Korean value, and row
# identity must all match. This does not permit arbitrary edits to old rows.
APPROVED_EVENT_CORRECTIONS = {
    ("english_events_maingame", 850): {
        "old": "맞아. 여기 %CURRENTPLAYERNAME%는 %HESHE%%VERB_'S_'VE% %HISHER% 다리 사이에 큼지막한 황동제 8번 공 두 개가 달렸다고 생각하나 봐!",
        "new": "맞아. 저 도전자는 자기 다리 사이에 큼지막한 황동 8번 공 두 개가 달렸다고 생각하나 봐!",
        "reason": "Screenshot-confirmed English conjugation tokens render as '그녀's 그녀의' and the player name as '???'; replace this exact sentence with a natural referent.",
    },
    ("english_events_endings", 892): {
        "old": "새로운 %CURRENTPLAYERNAME%를 환영하라! 새 시대가 열린다!",
        "new": "새로운 %CURRENTPLAYERNAME%을 환영하라! 새 시대가 열린다!",
        "reason": "Confirmed protagonist-name 받침 particle agreement; exact source-reviewed change.",
    },
    ("english_events_endings", 1057): {
        "old": "밴드는 네가 누군지도 모르지만, 음악 페스티벌 행동 강령을 존중해 관객이 %CURRENTPLAYERNAMECAPS%를 원한다면 %CURRENTPLAYERNAMECAPS%를 무대에 올려 주기로 한다.",
        "new": "밴드는 네가 누군지도 모르지만, 음악 페스티벌 행동 강령을 존중해 관객이 %CURRENTPLAYERNAMECAPS%을 원한다면 %CURRENTPLAYERNAMECAPS%을 무대에 올려 주기로 한다.",
        "reason": "Confirmed protagonist-name 받침 particle agreement; exact source-reviewed change.",
    },
    ("english_events_endings", 1686): {
        "old": "뭐, 그건 미래의 %CURRENTPLAYERNAME%가 알아서 해결할 문제다!",
        "new": "뭐, 그건 미래의 %CURRENTPLAYERNAME%이 알아서 해결할 문제다!",
        "reason": "Confirmed protagonist-name 받침 particle agreement; exact source-reviewed change.",
    },
    ("english_events_endings", 1984): {
        "old": "%CURRENTPLAYERNAME%는 '물 위의 매력덩이'라는 별명으로 궁정 모두의 사랑을 받는다!",
        "new": "%CURRENTPLAYERNAME%은 '물 위의 매력덩이'라는 별명으로 궁정 모두의 사랑을 받는다!",
        "reason": "Confirmed protagonist-name 받침 particle agreement; exact source-reviewed change.",
    },
    ("english_events_endings", 2005): {
        "old": "%CURRENTPLAYERNAME%를 로데오에서 데려올 순 있어도, %CURRENTPLAYERNAME%에게서 로데오를 떼어 놓을 순 없지.",
        "new": "%CURRENTPLAYERNAME%을 로데오에서 데려올 순 있어도, %CURRENTPLAYERNAME%에게서 로데오를 떼어 놓을 순 없지.",
        "reason": "Confirmed protagonist-name 받침 particle agreement; exact source-reviewed change.",
    },
    ("english_events_endings", 2087): {
        "old": "%CURRENTPLAYERNAME%는 '물 위의 매력덩이'라는 별명으로 궁정 모두의 사랑을 받는다!",
        "new": "%CURRENTPLAYERNAME%은 '물 위의 매력덩이'라는 별명으로 궁정 모두의 사랑을 받는다!",
        "reason": "Confirmed protagonist-name 받침 particle agreement; exact source-reviewed change.",
    },
    ("english_events_endings", 2377): {
        "old": "그러다 생각했지. %CURRENTPLAYERNAME%는 엉뚱하고 귀엽고, 날 즐겁게 해 주는 사람이야(%HESHE% %VERB_AMUSES_AMUSE%). 그러니 %HESHE%라면 도와줄지도 모르겠다고.",
        "new": "그러다 생각했지. %CURRENTPLAYERNAME%은 엉뚱하고 귀엽고, 날 즐겁게 해 주는 사람이야(%HESHE% %VERB_AMUSES_AMUSE%). 그러니 %HESHE%라면 도와줄지도 모르겠다고.",
        "reason": "Confirmed protagonist-name 받침 particle agreement; exact source-reviewed change.",
    },
    ("english_events_tutorial", 93): {
        "old": "그럼 적어도 %CURRENTPLAYERNAME%는 적었길 바라야지. 안 그랬으면 우린 진짜 좆된 거야... 좋은 의미로 말고.",
        "new": "그럼 적어도 %CURRENTPLAYERNAME%은 적었길 바라야지. 안 그랬으면 우린 진짜 좆된 거야... 좋은 의미로 말고.",
        "reason": "Confirmed protagonist-name 받침 particle agreement; exact source-reviewed change.",
    },
    ("english_events_endings", 1204): {
        "old": "인어 왕국에 머무는 동안 궁정 사람들은 모두 %CURRENTPLAYERNAME%를 ‘물 위의 매력덩어리’라며 아끼게 된다!",
        "new": "인어 왕국에 머무는 동안 궁정 사람들은 모두 %CURRENTPLAYERNAME%을 ‘물 위의 매력덩어리’라며 아끼게 된다!",
        "reason": "Protagonist names red/yellow/green/blue all end in a consonant; object particle must be 을, not 를.",
    },
    ("english_events_endings", 1223): {
        "old": "인어 왕국에 머무는 동안 궁정 사람들은 모두 %CURRENTPLAYERNAME%를 ‘물 위의 매력덩어리’라며 아끼게 된다!",
        "new": "인어 왕국에 머무는 동안 궁정 사람들은 모두 %CURRENTPLAYERNAME%을 ‘물 위의 매력덩어리’라며 아끼게 된다!",
        "reason": "Protagonist names red/yellow/green/blue all end in a consonant; object particle must be 을, not 를.",
    },
    ("english_events_endings", 1241): {
        "old": "인어 왕국에 머무는 동안 궁정 사람들은 모두 %CURRENTPLAYERNAME%를 ‘물 위의 매력덩어리’라며 아끼게 된다!",
        "new": "인어 왕국에 머무는 동안 궁정 사람들은 모두 %CURRENTPLAYERNAME%을 ‘물 위의 매력덩어리’라며 아끼게 된다!",
        "reason": "Protagonist names red/yellow/green/blue all end in a consonant; object particle must be 을, not 를.",
    },
    ("english_events_endings", 1259): {
        "old": "인어 왕국에 머무는 동안 궁정 사람들은 모두 %CURRENTPLAYERNAME%를 ‘물 위의 매력덩어리’라며 아끼게 된다!",
        "new": "인어 왕국에 머무는 동안 궁정 사람들은 모두 %CURRENTPLAYERNAME%을 ‘물 위의 매력덩어리’라며 아끼게 된다!",
        "reason": "Protagonist names red/yellow/green/blue all end in a consonant; object particle must be 을, not 를.",
    },
    ("english_events_endings", 1279): {
        "old": "인어 왕국에 머무는 동안 궁정 사람들은 모두 %CURRENTPLAYERNAME%를 ‘물 위의 매력덩어리’라며 아끼게 된다!",
        "new": "인어 왕국에 머무는 동안 궁정 사람들은 모두 %CURRENTPLAYERNAME%을 ‘물 위의 매력덩어리’라며 아끼게 된다!",
        "reason": "Protagonist names red/yellow/green/blue all end in a consonant; object particle must be 을, not 를.",
    },
    ("english_events_endings", 1298): {
        "old": "인어 왕국에 머무는 동안 궁정 사람들은 모두 %CURRENTPLAYERNAME%를 ‘물 위의 매력덩어리’라며 아끼게 된다!",
        "new": "인어 왕국에 머무는 동안 궁정 사람들은 모두 %CURRENTPLAYERNAME%을 ‘물 위의 매력덩어리’라며 아끼게 된다!",
        "reason": "Protagonist names red/yellow/green/blue all end in a consonant; object particle must be 을, not 를.",
    },
    ("english_events_endings", 1317): {
        "old": "인어 왕국에 머무는 동안 궁정 사람들은 모두 %CURRENTPLAYERNAME%를 ‘물 위의 매력덩어리’라며 아끼게 된다!",
        "new": "인어 왕국에 머무는 동안 궁정 사람들은 모두 %CURRENTPLAYERNAME%을 ‘물 위의 매력덩어리’라며 아끼게 된다!",
        "reason": "Protagonist names red/yellow/green/blue all end in a consonant; object particle must be 을, not 를.",
    },
    ("english_events_endings", 1336): {
        "old": "인어 왕국에 머무는 동안 궁정 사람들은 모두 %CURRENTPLAYERNAME%를 ‘물 위의 매력덩어리’라며 아끼게 된다!",
        "new": "인어 왕국에 머무는 동안 궁정 사람들은 모두 %CURRENTPLAYERNAME%을 ‘물 위의 매력덩어리’라며 아끼게 된다!",
        "reason": "Protagonist names red/yellow/green/blue all end in a consonant; object particle must be 을, not 를.",
    },
    ("english_events_bubbles", 2051): {
        "old": "나한테 묻지 마! 여기 돈 펑펑 쓰는 사람은 %CURRENTPLAYERNAME%잖아!",
        "new": "나한테 묻지 마! 여기 돈 펑펑 쓰는 사람은 %CURRENTPLAYERNAME%이잖아!",
        "reason": "All protagonist color names end in a consonant, so the copula before 잖아 must be 이잖아.",
    },
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
    ("english_events_endings", 2926): {
        "old": "내가 교단에 들어온다니 추종자들이 얼마나 신났는지 봐!",
        "new": "네가 교단에 들어온다니 추종자들이 얼마나 신났는지 봐!",
        "reason": "The speaker addresses the player who is joining the cult; first-person subject reverses the meaning.",
    },
}

# Exact previously reviewed rows whose only authorized edit is correcting a
# protagonist-variable particle. The old and expected new values are derived
# from the immutable baseline row; only these source lines are eligible, and
# any other wording/metadata change still fails the delta guard.
APPROVED_PROTAGONIST_PARTICLE_CORRECTIONS = {
    "english_events_maingame": (
        236, 733, 738, 780, 873, 888, 898, 1099, 1108, 1354, 1422,
        1449, 1534, 1655, 1687, 1768, 1774, 1961, 1966, 1973, 2021, 2044,
        2049, 2117, 2125, 2542, 2767, 2831, 2839, 2912, 2932, 3247, 3512,
        3724, 4079, 4329, 4330, 4331,
    ),
    "english_events_pitstop": (1966,),
}

# The earliest maingame prefix accidentally translated 13 executable signed
# stat enums (e.g. +N2 STAMINA -> +N2 followed by its Korean display name).
# All later batches preserved enums, but those 13 older rows bypassed the
# new-batch-only guard. A live Steam run proved these enum strings affect event
# parsing. Authorize repairs ONLY at these exact physical source rows, with
# the unchanged source effects supplying the only permitted new enum names.
APPROVED_LEGACY_STAT_ENUM_REPAIRS = frozenset((
    369, 1110, 1149, 1159, 1172, 1173, 1225,
    1226, 1242, 1262, 1263, 1310, 1328,
))
LEGACY_STAT_NAME_MAP = {
    "흥": "HYPE",
    "마력": "MAGIC",
    "정신": "MIND",
    "돈": "MONEY",
    "영혼": "SOUL",
    "체력": "STAMINA",
}
LEGACY_STAT_KOREAN = re.compile(r"(?<![A-Za-z])([+-]N[0-9]+)[ ]+(흥|마력|정신|돈|영혼|체력)")
LEGACY_STAT_ENGLISH = re.compile(
    r"(?<![A-Za-z])([+-]N[0-9]+)[ ]+(STAMINA|HYPE|MAGIC|MIND|SOUL|MONEY)(?![A-Za-z])"
)


def correct_legacy_stat_enum_names(english: str, korean: str) -> str:
    """Replace ONLY proven Korean stat enums by the source's exact code names."""
    source_effects = list(LEGACY_STAT_ENGLISH.finditer(english))
    old_effects = list(LEGACY_STAT_KOREAN.finditer(korean))
    if not source_effects or len(source_effects) != len(old_effects):
        raise ValueError("legacy source/translated stat-code counts disagree")
    parts: list[str] = []
    previous = 0
    for source, old in zip(source_effects, old_effects):
        if (
            source.group(1) != old.group(1)
            or LEGACY_STAT_NAME_MAP.get(old.group(2)) != source.group(2)
        ):
            raise ValueError("legacy stat enums do not match original source")
        parts.extend((korean[previous:old.start()], source.group(0)))
        previous = old.end()
    parts.append(korean[previous:])
    return "".join(parts)

PROTAGONIST_VARIABLES = ("%CURRENTPLAYERNAMECAPS%", "%CURRENTPLAYERNAME%")
WRONG_PROTAGONIST_PARTICLES = {
    "가": "이",
    "는": "은",
    "를": "을",
    "랑": "이랑",
    "와": "과",
}


def correct_protagonist_particles(korean: str) -> str:
    """Return the exact particle-only correction authorized for listed rows."""
    corrected = korean
    for name in PROTAGONIST_VARIABLES:
        for wrong, right in WRONG_PROTAGONIST_PARTICLES.items():
            corrected = corrected.replace(name + wrong, name + right)
    return corrected


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
    metadata = ("line", "event", "english_sha256")
    if asset == "english_events_maingame" and ident[1] in APPROVED_LEGACY_STAT_ENUM_REPAIRS:
        if any(old_row.get(key) != new_row.get(key) for key in metadata):
            raise ValueError(f"approved stat repair changed row identity: {asset}:{ident[1]}")
        source_lines = (ROOT / "work/source/english_events_maingame.txt").read_text("utf-8").splitlines()
        english = source_lines[ident[1]].split("\t")[3]
        if hashlib.sha256(english.encode("utf-8")).hexdigest() != old_row["english_sha256"]:
            raise ValueError(f"approved stat repair lost source identity: {asset}:{ident[1]}")
        corrected = correct_legacy_stat_enum_names(english, old_row["ko"])
        if corrected == old_row["ko"] or new_row["ko"] != corrected:
            raise ValueError(f"approved legacy stat repair value mismatch: {asset}:{ident[1]}")
        return True
    if approval is None:
        if old_row.get("line") not in APPROVED_PROTAGONIST_PARTICLE_CORRECTIONS.get(asset, ()):
            raise ValueError(f"previously translated event text changed: {asset}:{old_row.get('line')}")
        if any(old_row.get(key) != new_row.get(key) for key in metadata):
            raise ValueError(f"approved correction changed row identity: {asset}:{old_row.get('line')}")
        expected = correct_protagonist_particles(old_row.get("ko", ""))
        if expected == old_row.get("ko") or new_row.get("ko") != expected:
            raise ValueError(f"approved protagonist particle correction value mismatch: {asset}:{old_row.get('line')}")
        return True
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
        verify_stat_effects(english, row["ko"], f"{path.stem}:{row['line']}")
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
