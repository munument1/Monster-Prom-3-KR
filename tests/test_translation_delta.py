"""Batch-integrity guard tests (pure data, no Git or game mutation)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from verify_translation_delta import validate_ui  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
