"""Audit the optional release font container, not the installed game bundle."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


class PublicFonts(unittest.TestCase):
    def test_only_native_font_dependencies_and_public_font_bytes_are_packaged(self):
        from build_public_font_bundle import OUT, PUBLIC, validate
        if not OUT.is_file() or not (PUBLIC / "Jua.ttf").is_file():
            self.skipTest("Prepare optional public OFL font container first")
        report = validate(OUT)
        self.assertEqual(report["objects"], 7)
        self.assertGreaterEqual(report["korean_syllables"], 1468)


if __name__ == "__main__":
    unittest.main()
