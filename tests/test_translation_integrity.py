"""Read-only sanity checks. Does not launch or modify the installed game."""

import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_playtest import verify_line  # noqa: E402


class TranslationIntegrity(unittest.TestCase):
    def test_original_manifest_12_text_assets(self):
        manifest = json.loads((ROOT / "work/source_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(len(manifest), 12)
        self.assertIn("english_metatexts", manifest)
        for name, row in manifest.items():
            data = (ROOT / "work/source" / f"{name}.txt").read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), row["sha256"])

    def test_catalog_counts(self):
        records = [json.loads(line) for line in (ROOT / "work/catalog.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(sum(row["kind"] == "event" for row in records), 26234)
        self.assertEqual(sum(row["kind"] == "metatext" for row in records), 2871)

    def test_tokens_and_numbers_preserved(self):
        verify_line("Hello, %PLAYER%! [n] +2 SMARTS", "안녕, %PLAYER%! [n] +2 SMARTS", "example")
        with self.assertRaisesRegex(ValueError, "token mismatch"):
            verify_line("Hello, %PLAYER%! [n]", "안녕, %OTHER%! [n]", "bad-token")
        with self.assertRaisesRegex(ValueError, "Arabic-digit/stat mismatch"):
            verify_line("Win +2 SMARTS", "승리 +3 SMARTS", "bad-stat")

    def test_metatext_preview_is_explicitly_separate(self):
        meta = json.loads((ROOT / "translations/english_metatexts_ko.json").read_text(encoding="utf-8"))
        self.assertGreater(len(meta["translations"]), 0)
        self.assertIn("TIT_BTN_PLY", meta["translations"])
        self.assertEqual(meta["translations"]["TIT_BTN_PLY"], "플레이")


if __name__ == "__main__":
    unittest.main()
