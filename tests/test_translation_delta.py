"""Batch-integrity guard tests (pure data, no Git or game mutation)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from verify_translation_delta import is_approved_event_correction, validate_ui  # noqa: E402


class DeltaIntegrity(unittest.TestCase):
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
