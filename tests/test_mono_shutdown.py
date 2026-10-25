"""Optional isolated x86 Mono regression; never starts Unity or accesses saves."""
import json
import os
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SANDBOX = ROOT / "build/shutdown_probe"
STOCK = ROOT / "work/tools/BepInEx_win_x86_5.4.23.2/BepInEx/core/MonoMod.Utils.dll"
FIXED = ROOT / "build/runtime_compat/MonoMod.Utils.dll"


class MonoShutdownTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not all(p.is_file() for p in [SANDBOX / "mono_shutdown_host.exe", SANDBOX / "MonoShutdownProbe.exe", STOCK, FIXED]):
            raise unittest.SkipTest("Prepare the optional local x86 Mono shutdown probes first")

    def run_probe(self, library, mode):
        shutil.copy2(library, SANDBOX / "MonoMod.Utils.dll")
        env = dict(os.environ)
        env.pop("MONOMOD_DMD_TYPE", None)
        env["ROADTRIP_SHUTDOWN_PROBE"] = mode
        return subprocess.run([str(SANDBOX / "mono_shutdown_host.exe")], cwd=SANDBOX,
                              env=env, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=20)

    def test_original_library_corrupts_pointer_and_crashes(self):
        result = self.run_probe(STOCK, "corlib")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("POINTER_4C_BEFORE=00000000", result.stdout)
        self.assertIn("POINTER_4C_AFTER=01000000", result.stdout)
        self.assertNotIn("AFTER_MONO_CLEANUP", result.stdout)

    def test_roadmap_prefix_binds_private_field_and_valid_path_argument(self):
        result = self.run_probe(FIXED, "roadmap")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("ROADMAP_CASES=6", result.stdout)
        self.assertIn("AFTER_MONO_CLEANUP", result.stdout)

    def test_corrected_library_preserves_pointer_and_shuts_down(self):
        for mode in ["corlib", "harmony", "harmony-unpatch"]:
            with self.subTest(mode=mode):
                result = self.run_probe(FIXED, mode)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("AFTER_MONO_CLEANUP", result.stdout)
                if mode == "corlib":
                    self.assertIn("POINTER_4C_AFTER=00000000", result.stdout)
                    self.assertIn("CORLIB_53=1", result.stdout)
                else:
                    self.assertIn("PATCH_RESULT=7", result.stdout)
