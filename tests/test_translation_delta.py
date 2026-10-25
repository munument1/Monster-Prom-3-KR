"""Batch-integrity guard tests (pure data, no Git or game mutation)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_playtest import (  # noqa: E402
    FORMAT_ONLY_EVENT_TAGS, LITERAL_EVENT_CUES,
    GAME_STAT_BOUNDARY, SILENT_REACTION_EXCEPTIONS,
    game_safe_stat_effects, verify_line,
)
from verify_translation_delta import (  # noqa: E402
    APPROVED_EVENT_CORRECTIONS, APPROVED_PROTAGONIST_PARTICLE_CORRECTIONS,
    APPROVED_LEGACY_STAT_ENUM_REPAIRS, baseline_json,
    correct_legacy_stat_enum_names, correct_protagonist_particles,
    is_approved_event_correction, read_json, validate_ui, verify_stat_effects,
)


class DeltaIntegrity(unittest.TestCase):
    def test_literal_percentages_next_to_placeholders_are_not_fake_tokens(self):
        english = "WHAT ABOUT %CURRENTPLAYERNAMECAPS%? WE CAN 100% OBJECTIFY %HISHERCAPS% ASS, AND WE'RE COOL IF %HESHECAPS% %VERBCAPS_DIES_DIE%!"
        korean = "그럼 %CURRENTPLAYERNAMECAPS%은 어때? %HISHERCAPS% 엉덩이는 100퍼센트 대상화해도 되고, %HESHECAPS% %VERBCAPS_DIES_DIE%해도 우린 괜찮다고!"
        verify_line(english, korean, "english_events_maingame:14400")

        # Literal percentage signs must not be mistaken for variable syntax.
        verify_line(
            "I'm 50% wolf, 50% man, and 100% psyched!",
            "난 늑대 50퍼센트, 인간 50퍼센트에, 기분은 100퍼센트야!",
            "token:literal-percent",
        )

    def test_apostrophes_in_real_placeholders_remain_tokens(self):
        verify_line(
            "I hope %VERB_'S_'VE% gone.",
            "그 사람이 %VERB_'S_'VE% 갔길 바라.",
            "token:apostrophe-placeholder",
        )

    def test_pitstop_success_rate_sentence_has_no_leftover_english(self):
        root = Path(__file__).resolve().parents[1]
        document = read_json(root / "translations" / "english_events_pitstop.json")
        row = next(row for row in document["entries"] if row["line"] == 6620)
        self.assertEqual(
            row["ko"],
            "살인 대상에 [BABIES]를 포함하라는 %CURRENTPLAYERNAME%의 추가 조언을 따르면 성공률이 97%로 올라갑니다.",
        )
        self.assertNotIn("if following", row["ko"])

    def test_exact_event_command_tags_are_preserved_without_hangul(self):
        for ident, english, korean in FORMAT_ONLY_EVENT_TAGS:
            with self.subTest(ident=ident):
                verify_line(english, korean, ident)
                with self.assertRaisesRegex(ValueError, "translation missing Hangul"):
                    verify_line(english, korean + " ", ident)

    def test_exact_uwu_emoticon_is_intentionally_preserved(self):
        for ident, english, korean in LITERAL_EVENT_CUES:
            with self.subTest(ident=ident):
                verify_line(english, korean, ident)
                with self.assertRaisesRegex(ValueError, "translation missing Hangul"):
                    verify_line(english, korean + "!", ident)

    def test_exact_silent_reaction_exceptions(self):
        self.assertIn(
            ("english_events_maingame:16184", "...?", "……"),
            SILENT_REACTION_EXCEPTIONS,
        )
        for ident, english, korean in SILENT_REACTION_EXCEPTIONS:
            with self.subTest(ident=ident):
                verify_line(english, korean, ident)
                with self.assertRaises(ValueError):
                    verify_line(english, korean + "!", ident)

    def test_actual_stat_change_enum_tokens_are_immutable(self):
        original = "You lose -N2 STAMINA, but gain +N2 HYPE!"
        korean = "너는 -N2 STAMINA를 잃지만 +N2 HYPE를 얻었다!"
        verify_stat_effects(original, korean, "stat:valid")
        for invalid in (
            "너는 -N2 체력을 잃지만 +N2 HYPE를 얻었다!",
            "너는 -N2 SOUL을 잃지만 +N2 HYPE를 얻었다!",
            "너는 +N2 STAMINA를 잃지만 +N2 HYPE를 얻었다!",
            "너는 -N2 STAMINA를 잃지만 +N3 HYPE를 얻었다!",
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(ValueError, "stat-effect enum expression mismatch"):
                    verify_stat_effects(original, invalid, "stat:invalid")
        # Ordinary prose is not a stat-change expression and may be localized.
        verify_stat_effects("The STAMINA of your friend", "친구의 체력", "stat:prose")

    def test_signed_stat_enums_must_survive_the_main_builder_too(self):
        source = "You gain +N2 MAGIC but lose -N2 STAMINA."
        verify_line(source, "넌 +N2 MAGIC을 얻지만 -N2 STAMINA를 잃는다.", "stat:build")
        with self.assertRaisesRegex(ValueError, "stat-effect enum expression mismatch"):
            verify_line(source, "넌 +N2 마력을 얻지만 -N2 STAMINA를 잃는다.", "stat:broken")

    def test_live_game_parser_requires_invisible_boundary_before_hangul_particles(self):
        ko = "너는 +N2 MAGIC을 얻고 -N2 STAMINA를 잃는다. 일반적인 STAMINA는 체력이다."
        generated = game_safe_stat_effects(ko)
        self.assertEqual(
            generated,
            "너는 +N2 MAGIC" + GAME_STAT_BOUNDARY + "을 얻고 -N2 STAMINA"
            + GAME_STAT_BOUNDARY + "를 잃는다. 일반적인 STAMINA는 체력이다.",
        )
        self.assertEqual(generated.replace(GAME_STAT_BOUNDARY, ""), ko)
        self.assertEqual(game_safe_stat_effects(generated), generated)

    def test_fixed_number_stat_effects_have_the_same_parser_boundary(self):
        ko = "-2 STAMINA를 잃고 +2 HYPE와 +1MAGIC을 얻는다."
        generated = game_safe_stat_effects(ko)
        self.assertEqual(generated.replace(GAME_STAT_BOUNDARY, ""), ko)
        self.assertEqual(generated.count(GAME_STAT_BOUNDARY), 3)
        self.assertEqual(game_safe_stat_effects(generated), generated)

    def test_exact_13_legacy_stat_enum_repairs_preserve_immutable_source(self):
        root = Path(__file__).resolve().parents[1]
        old = baseline_json("HEAD", "translations/english_events_maingame.json")
        now = read_json(root / "translations/english_events_maingame.json")
        before = {r["line"]: r for r in old["entries"]}
        after = {r["line"]: r for r in now["entries"]}
        source_lines = (root / "work/source/english_events_maingame.txt").read_text("utf-8").splitlines()
        self.assertEqual(len(APPROVED_LEGACY_STAT_ENUM_REPAIRS), 13)
        for line in APPROVED_LEGACY_STAT_ENUM_REPAIRS:
            with self.subTest(line=line):
                original = before[line]
                repaired = after[line]
                english = source_lines[line].split("\t")[3]
                self.assertEqual(
                    repaired["ko"], correct_legacy_stat_enum_names(english, original["ko"])
                )
                verify_stat_effects(english, repaired["ko"], f"english_events_maingame:{line}")
                self.assertTrue(is_approved_event_correction(
                    "english_events_maingame", original, repaired,
                ))
                with self.assertRaisesRegex(ValueError, "approved legacy stat repair value mismatch"):
                    is_approved_event_correction(
                        "english_events_maingame", original, {**repaired, "ko": repaired["ko"] + "!"},
                    )

    def test_new_name_particle_corrections_match_exact_baseline_rows(self):
        checked_lines = {
            "english_events_endings": (892, 1057, 1204, 1223, 1241, 1259,
                                       1279, 1298, 1317, 1336, 1686, 1984,
                                       2005, 2087, 2377),
            "english_events_tutorial": (93,),
        }
        root = Path(__file__).resolve().parents[1]
        for asset, lines in checked_lines.items():
            original = baseline_json("HEAD", f"translations/{asset}.json")
            updated = read_json(root / "translations" / f"{asset}.json")
            by_line_old = {row["line"]: row for row in original["entries"]}
            by_line_new = {row["line"]: row for row in updated["entries"]}
            for line in lines:
                with self.subTest(asset=asset, line=line):
                    self.assertIn((asset, line), APPROVED_EVENT_CORRECTIONS)
                    self.assertTrue(is_approved_event_correction(
                        asset, by_line_old[line], by_line_new[line]
                    ))
                    wrong = {**by_line_new[line], "ko": by_line_new[line]["ko"] + "!"}
                    with self.assertRaisesRegex(ValueError, "approved correction value mismatch"):
                        is_approved_event_correction(asset, by_line_old[line], wrong)

    def test_exact_approved_protagonist_particle_corrections_match_baseline_rows(self):
        root = Path(__file__).resolve().parents[1]
        for asset, lines in APPROVED_PROTAGONIST_PARTICLE_CORRECTIONS.items():
            original = baseline_json("HEAD", f"translations/{asset}.json")
            updated = read_json(root / "translations" / f"{asset}.json")
            by_line_old = {row["line"]: row for row in original["entries"]}
            by_line_new = {row["line"]: row for row in updated["entries"]}
            for line in lines:
                with self.subTest(asset=asset, line=line):
                    old = by_line_old[line]
                    new = by_line_new[line]
                    expected = correct_protagonist_particles(old["ko"])
                    self.assertNotEqual(expected, old["ko"])
                    self.assertEqual(new["ko"], expected)
                    self.assertTrue(is_approved_event_correction(asset, old, new))
                    arbitrary = {**new, "ko": new["ko"] + "!"}
                    with self.assertRaisesRegex(ValueError, "approved protagonist particle correction value mismatch"):
                        is_approved_event_correction(asset, old, arbitrary)

    def test_reviewed_player_object_particle_in_all_merkingdom_endings(self):
        old_text = "인어 왕국에 머무는 동안 궁정 사람들은 모두 %CURRENTPLAYERNAME%를 ‘물 위의 매력덩어리’라며 아끼게 된다!"
        new_text = "인어 왕국에 머무는 동안 궁정 사람들은 모두 %CURRENTPLAYERNAME%을 ‘물 위의 매력덩어리’라며 아끼게 된다!"
        for line in (1204, 1223, 1241, 1259, 1279, 1298, 1317, 1336):
            old = {
                "line": line,
                "event": "ending_mvp_merkingdom_blue",
                "english_sha256": "c360ddb723f7255e9dfb698b0e1b78a96bbfcbfc154d359edcae543f00be3237",
                "ko": old_text,
            }
            new = {**old, "ko": new_text}
            with self.subTest(line=line):
                self.assertTrue(is_approved_event_correction("english_events_endings", old, new))
                with self.assertRaisesRegex(ValueError, "approved correction value mismatch"):
                    is_approved_event_correction("english_events_endings", old, {**new, "ko": new_text + "!"})

    def setUp(self) -> None:
        self.catalog = [
            {"kind": "metatext", "id": "A", "english": "Play"},
            {"kind": "metatext", "id": "B", "english": "Settings"},
            {"kind": "metatext", "id": "C", "english": "Quit"},
        ]
        self.original = {"source_sha256": "unchanged", "translations": {"A": "플레이"}}

    def test_next_source_ui_batch_is_accepted(self):
        newer = {"source_sha256": "unchanged", "translations": {"A": "플레이", "B": "설정"}}
        self.assertEqual(validate_ui(newer, self.original, self.catalog), 1)

    def test_previous_reviewed_text_cannot_be_replaced(self):
        newer = {"source_sha256": "unchanged", "translations": {"A": "시작", "B": "설정"}}
        with self.assertRaisesRegex(ValueError, "reviewed UI text changed"):
            validate_ui(newer, self.original, self.catalog)

    def test_skipping_a_source_key_is_rejected(self):
        newer = {"source_sha256": "unchanged", "translations": {"A": "플레이", "C": "종료"}}
        with self.assertRaisesRegex(ValueError, "next catalog sequence"):
            validate_ui(newer, self.original, self.catalog)

    def test_only_exact_reviewed_event_correction_is_allowed(self):
        old = {
            "line": 1739,
            "event": "pitstop_passenger_loveanother_yellow_1",
            "english_sha256": "ae214a54a10ddd39c0849d5666acfa286c58aa0f4d27cf27c48dfa55ad9dcb45",
            "ko": "(하지만 %CURRENTPLAYERNAME%를 거절해서 %HIMHER%에게 상처를 주면 어떡하지? 못되게 보이고 싶진 않은데...)",
        }
        new = {**old, "ko": "(하지만 %HIMHER%를 거절해서 %CURRENTPLAYERNAME%의 마음에 상처를 주면 어떡하지? 못되게 보이고 싶진 않은데...)"}
        self.assertTrue(is_approved_event_correction("english_events_pitstop", old, new))

    def test_exact_protagonist_jana_correction_is_allowed(self):
        old = {
            "line": 2051,
            "event": "bubble_low_money1",
            "english_sha256": "3c1ce5f148a97848886c20025ba896c223ed8ce8f49067dc13362d873a1fdc15",
            "ko": "나한테 묻지 마! 여기 돈 펑펑 쓰는 사람은 %CURRENTPLAYERNAME%잖아!",
        }
        new = {**old, "ko": "나한테 묻지 마! 여기 돈 펑펑 쓰는 사람은 %CURRENTPLAYERNAME%이잖아!"}
        self.assertTrue(is_approved_event_correction("english_events_bubbles", old, new))
        with self.assertRaisesRegex(ValueError, "approved correction value mismatch"):
            is_approved_event_correction("english_events_bubbles", old, {**new, "ko": new["ko"] + "!"})

    def test_only_exact_reviewed_ending_correction_is_allowed(self):
        old = {
            "line": 685,
            "event": "ending_failure_glitch_3",
            "english_sha256": "b9862f53f8dde310e9943a9e9cc091843b4936578b536d599e33646bc31d192e",
            "ko": "생각해 보니 친구들은 널 어디서도 본 적이 없다. 넌 이 로드 트립에 %HISHER% 길을 비집고 들어와 기억을 망가뜨린 빌어먹을 글리치일 뿐이다.",
        }
        new = {**old, "ko": "생각해 보니 친구들은 널 어디서도 본 적이 없다. 넌 이 로드트립에 끼어들려고 %HISHER% 기억을 망가뜨린 빌어먹을 글리치일 뿐이다."}
        self.assertTrue(is_approved_event_correction("english_events_endings", old, new))
        arbitrary = {**new, "ko": new["ko"] + "!"}
        with self.assertRaisesRegex(ValueError, "approved correction value mismatch"):
            is_approved_event_correction("english_events_endings", old, arbitrary)

    def test_only_exact_reviewed_ending_pronoun_correction_is_allowed(self):
        old = {
            "line": 2926,
            "event": "ending_date_lamb",
            "english_sha256": "74f3febe9fcb847c56836a37262fb9c8ca948c8e223bf020706f093c1554f992",
            "ko": "내가 교단에 들어온다니 추종자들이 얼마나 신났는지 봐!",
        }
        new = {**old, "ko": "네가 교단에 들어온다니 추종자들이 얼마나 신났는지 봐!"}
        self.assertTrue(is_approved_event_correction("english_events_endings", old, new))
        arbitrary = {**new, "ko": new["ko"] + "!"}
        with self.assertRaisesRegex(ValueError, "approved correction value mismatch"):
            is_approved_event_correction("english_events_endings", old, arbitrary)

    def test_unapproved_event_edit_is_rejected(self):
        old = {"line": 1739, "event": "pitstop_passenger_loveanother_yellow_1", "english_sha256": "ae214a54a10ddd39c0849d5666acfa286c58aa0f4d27cf27c48dfa55ad9dcb45", "ko": "old"}
        new = {**old, "ko": "arbitrary edit"}
        with self.assertRaisesRegex(ValueError, "approved correction value mismatch"):
            is_approved_event_correction("english_events_pitstop", old, new)


if __name__ == "__main__":
    unittest.main()
