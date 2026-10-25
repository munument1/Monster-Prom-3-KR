"""Regression coverage for the hand-translated draft corruption guard."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from merge_manual_draft import verify_not_corrupt  # noqa: E402


class DraftCorruption(unittest.TestCase):
    def test_windows_pipe_question_mark_damage_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "encoding corruption"):
            verify_not_corrupt("What a fantastic game!", "?? ??? ?", "draft:1")

    def test_replacement_character_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Replacement character"):
            verify_not_corrupt("You win!", "이\ufffd!", "draft:2")

    def test_valid_hangul_and_silent_ellipsis_are_accepted(self):
        verify_not_corrupt("You win!", "네가 이겼어!", "draft:3")
        verify_not_corrupt("...", "……", "draft:4")

    def test_literal_question_marks_in_a_punctuation_only_source(self):
        verify_not_corrupt("???", "???", "draft:5")


if __name__ == "__main__":
    unittest.main()
