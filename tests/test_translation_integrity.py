"""Read-only sanity checks. Does not launch or modify the installed game."""

import hashlib
import json
import subprocess
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
        self.assertEqual(sum(row["kind"] == "event" for row in records), 27384)
        self.assertEqual(sum(row.get("row_type") == "dialogue" for row in records), 26234)
        self.assertEqual(sum(row.get("row_type") == "choice" for row in records), 777)
        self.assertEqual(sum(row.get("row_type") == "action" for row in records), 373)
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

    def test_default_event_playtest_changes_only_dialogue(self):
        """The generated loose file cannot alter event structure or directives."""
        subprocess.run(
            [sys.executable, str(ROOT / "scripts/build_playtest.py"), "--only", "english_events_default"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        source = (ROOT / "work/source/english_events_default.txt").read_text(encoding="utf-8").splitlines()
        built = (ROOT / "build/playtest/game_assets/texts/english_events_default.txt").read_text(encoding="utf-8").splitlines()
        doc = json.loads((ROOT / "translations/english_events_default.json").read_text(encoding="utf-8"))
        self.assertEqual(len(source), len(built))
        translated_lines = {entry["line"]: entry["ko"] for entry in doc["entries"]}
        for i, (original_line, output_line) in enumerate(zip(source, built)):
            if i not in translated_lines:
                self.assertEqual(original_line, output_line)
            else:
                a, b = original_line.split("\t"), output_line.split("\t")
                self.assertEqual(len(a), len(b))
                self.assertEqual(a[:3], b[:3])
                self.assertEqual(a[4:], b[4:])
                self.assertEqual(b[3], translated_lines[i])


if __name__ == "__main__":
    unittest.main()
