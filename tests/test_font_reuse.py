"""Optional local-only check for Monster Camp fonts used by Roadtrip Korean.

No font binary, game-owned bundle, or installed game is included in this repo.
The test is skipped on machines where fonts have not been prepared locally.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCAL_FONTS = ROOT / "work/fonts"


class PreparedFontTest(unittest.TestCase):
    def test_prepared_camp_fonts_cover_current_hangul(self) -> None:
        try:
            from fontTools.ttLib import TTFont
        except ImportError:
            self.skipTest("fonttools is an optional local dependency")
        paths = [LOCAL_FONTS / "Jua.ttf", LOCAL_FONTS / "GamjaFlower.ttf"]
        if not all(path.is_file() for path in paths):
            self.skipTest("Monster Camp fonts are not prepared locally")
        strings: list[str] = []
        for p in (ROOT / "translations").glob("*.json"):
            doc = json.loads(p.read_text(encoding="utf-8"))
            if p.stem == "english_metatexts_ko":
                strings.extend(doc["translations"].values())
            else:
                strings.extend(e["ko"] for e in doc["entries"])
        unique_hangul = {ord(ch) for text in strings for ch in text if 0xAC00 <= ord(ch) <= 0xD7A3}
        self.assertGreater(len(unique_hangul), 900)
        for path in paths:
            with self.subTest(font=path.stem):
                tt = TTFont(path)
                cmap = set((tt.getBestCmap() or {}).keys())
                self.assertEqual(unique_hangul - cmap, set())
        gamja = TTFont(LOCAL_FONTS / "GamjaFlower.ttf")
        cmap = set((gamja.getBestCmap() or {}).keys())
        self.assertTrue(all(cp in cmap for cp in range(0xAC00, 0xD7A4)))


if __name__ == "__main__":
    unittest.main()
