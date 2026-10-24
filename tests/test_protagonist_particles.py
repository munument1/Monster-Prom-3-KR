"""Checks that final proofreading catches the user's color-name particle rule."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from audit_protagonist_particles import candidates  # noqa: E402


class ProtagonistParticleCandidates(unittest.TestCase):
    def test_copula_before_jana(self):
        for name in ("빨강", "노랑", "초록", "파랑", "%CURRENTPLAYERNAME%"):
            with self.subTest(name=name):
                self.assertIn((name + "잖아", name + "이잖아", "잖아"), candidates(name + "잖아!"))

    def test_subject_and_object_particles(self):
        self.assertIn(("%CURRENTPLAYERNAME%가", "%CURRENTPLAYERNAME%이", "가"), candidates("%CURRENTPLAYERNAME%가 왔다"))
        self.assertIn(("파랑를", "파랑을", "를"), candidates("파랑를 만나"))

    def test_predicate_ending_is_not_name_suffix(self):
        self.assertEqual(candidates("네가 맞잖아! 우리도 알잖아."), [])
        self.assertEqual(candidates("%CURRENTPLAYERNAME%이잖아!"), [])


if __name__ == "__main__":
    unittest.main()
