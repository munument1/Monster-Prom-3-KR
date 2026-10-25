"""Exercise the actual C# save helper through the game's ASCII XML workflow."""
import shutil
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]


class SaveNameEncodingTest(unittest.TestCase):
    @unittest.skipUnless(shutil.which("dotnet"), ".NET SDK is required for C# XML regression")
    def test_unicode_names_survive_legacy_ascii_save(self):
        with tempfile.TemporaryDirectory(prefix="roadtrip-name-") as temp:
            project = Path(temp) / "Probe.csproj"
            helper = ROOT / "src/RoadtripKoreanFontBridge/SaveNameEncoding.cs"
            probe = ROOT / "tests/SaveNameEncodingProbe.cs"
            project.write_text(
                '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>'
                '<OutputType>Exe</OutputType><TargetFramework>net8.0</TargetFramework>'
                '</PropertyGroup><ItemGroup>'
                f'<Compile Include="{escape(str(helper))}" />'
                f'<Compile Include="{escape(str(probe))}" />'
                '</ItemGroup></Project>', encoding="utf-8"
            )
            result = subprocess.run(
                ["dotnet", "run", "--project", str(project), "--verbosity", "quiet"],
                capture_output=True, text=True, encoding="utf-8", timeout=60,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("9 Unicode/XML name round-trips preserved", result.stdout)

    @unittest.skipUnless(shutil.which("dotnet"), ".NET SDK is required for original-DLL regression")
    def test_original_game_crypto_reader_and_stat_parser(self):
        game = Path(os.environ.get(
            "MONSTER_ROADTRIP_GAME",
            r"C:\Games\Steam\steamapps\common\Monster Prom 3 - Monster Roadtrip",
        ))
        if not (game / "MonsterRoadtrip_Data/Managed/Assembly-CSharp.dll").is_file():
            self.skipTest("User-owned Monster Roadtrip DLL is not available locally")
        events = [
            ROOT / "work/source/english_events_maingame.txt",
            ROOT / "build/playtest/game_assets/texts/english_events_maingame.txt",
            game / "MonsterRoadtrip_Data/StreamingAssets/game_assets/texts/english_events_maingame.txt",
        ]
        if not all(path.is_file() for path in events):
            self.skipTest("Source, built and installed local event files are required")
        with tempfile.TemporaryDirectory(prefix="roadtrip-contract-") as temp:
            project = Path(temp) / "Probe.csproj"
            files = [ROOT / "src/RoadtripKoreanFontBridge/SaveNameEncoding.cs", ROOT / "tests/GameRuntimeContractProbe.cs"]
            project.write_text(
                '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>'
                '<OutputType>Exe</OutputType><TargetFramework>net8.0</TargetFramework>'
                '</PropertyGroup><ItemGroup>' + ''.join(
                    f'<Compile Include="{escape(str(path))}" />' for path in files
                ) + '</ItemGroup></Project>', encoding="utf-8"
            )
            for event in events:
                with self.subTest(event=event):
                    result = subprocess.run(
                        ["dotnet", "run", "--project", str(project), "--verbosity", "quiet", "--", str(game), str(event)],
                        capture_output=True, text=True, encoding="utf-8", timeout=60,
                    )
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertIn("PASS original DLL Encrypt/Decrypt + UnserializeString", result.stdout)
                    self.assertIn("evilmenu outcome 3; diner_doom raw definitions=3", result.stdout)

    @unittest.skipUnless(shutil.which("dotnet"), ".NET SDK is required for original-DLL stat audit")
    def test_all_event_stat_expressions_match_original_game_regex(self):
        game = Path(os.environ.get("MONSTER_ROADTRIP_GAME", r"C:\Games\Steam\steamapps\common\Monster Prom 3 - Monster Roadtrip"))
        if not (game / "MonsterRoadtrip_Data/Managed/Assembly-CSharp.dll").is_file():
            self.skipTest("User-owned game DLL is unavailable")
        source = ROOT / "work/source"
        built = ROOT / "build/playtest/game_assets/texts"
        if not (source / "english_events_maingame.txt").is_file() or not built.is_dir():
            self.skipTest("Local source and built events are required")
        with tempfile.TemporaryDirectory(prefix="roadtrip-stats-") as temp:
            project = Path(temp) / "Probe.csproj"
            project.write_text(
                '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType>'
                '<TargetFramework>net8.0</TargetFramework></PropertyGroup><ItemGroup>'
                f'<Compile Include="{escape(str(ROOT / "tests/AllEventStatProbe.cs"))}" />'
                '</ItemGroup></Project>', encoding="utf-8"
            )
            result = subprocess.run(
                ["dotnet", "run", "--project", str(project), "--verbosity", "quiet", "--", str(game), str(source), str(built)],
                capture_output=True, text=True, encoding="utf-8", timeout=60,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("mismatches=0", result.stdout)
