"""Install the verified x86 MonoMod layout fix; preserve latest game progress."""
from __future__ import annotations

import base64
import copy
import hashlib
import html
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7

ROOT = Path(__file__).resolve().parents[1]
GAME = Path(r"C:\Games\Steam\steamapps\common\Monster Prom 3 - Monster Roadtrip")
KEY = b"07372495761297179318254963745127"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def decrypt(raw):
    outer = ET.fromstring(raw)
    cipher = Cipher(algorithms.AES(KEY), modes.ECB()).decryptor()
    padded = cipher.update(base64.b64decode(outer.text)) + cipher.finalize()
    unpad = PKCS7(128).unpadder()
    return outer, (unpad.update(padded) + unpad.finalize()).decode("utf-8")


def repaired_checkpoint(path):
    raw = path.read_bytes()
    outer, text = decrypt(raw)
    tree = ET.fromstring("<R>" + text + "</R>")
    players = list(tree.iter("CorePlayerData"))
    if len(players) != 1:
        raise RuntimeError("Inspect multiplayer names individually; no automatic repair")
    player = players[0]
    if player.findtext("Name") != "???":
        return raw, False
    good = ROOT / "work/install/runtime_fix_20261025_154900/UserData" / path.name
    _, good_text = decrypt(good.read_bytes())
    good_players = list(ET.fromstring("<R>" + good_text + "</R>").iter("CorePlayerData"))
    if len(good_players) != 1:
        raise RuntimeError("Unexpected name recovery backup")
    previous = good_players[0]
    if any(player.findtext(key) != previous.findtext(key) for key in ("Player", "PcProfile", "Pronoun")):
        raise RuntimeError("Current player identity differs from known-good backup")
    name = previous.findtext("Name")
    if not name or "?" in name or text.count("<Name>???</Name>") != 1:
        raise RuntimeError("Ambiguous name recovery")
    updated = text.replace("<Name>???</Name>", "<Name>" + html.escape(name, quote=False) + "</Name>", 1)
    expected = copy.deepcopy(tree)
    next(expected.iter("CorePlayerData")).find("Name").text = name
    if ET.tostring(ET.fromstring("<R>" + updated + "</R>")) != ET.tostring(expected):
        raise RuntimeError("Save fields other than Name changed")
    pad = PKCS7(128).padder()
    padded = pad.update(updated.encode("utf-8")) + pad.finalize()
    cipher = Cipher(algorithms.AES(KEY), modes.ECB()).encryptor()
    payload = base64.b64encode(cipher.update(padded) + cipher.finalize())
    result = raw.replace(outer.text.encode("ascii"), payload, 1)
    if decrypt(result)[1] != updated:
        raise RuntimeError("Encrypted save round-trip mismatch")
    return result, True


def main():
    process = subprocess.run(["tasklist", "/FI", "IMAGENAME eq MonsterRoadtrip.exe"], capture_output=True, text=True, check=True)
    if "monsterroadtrip.exe" in process.stdout.lower():
        raise SystemExit("Exit the game first; no files changed")
    mono = GAME / "MonoBleedingEdge/EmbedRuntime/mono-2.0-bdwgc.dll"
    if sha(mono) != "5C3AD7D6E2B557173D9FA4C3281136ED6992DBE25031979DFEE85D001267761C":
        raise RuntimeError("Unsupported Mono fingerprint")
    replacements = {
        r"BepInEx\core\MonoMod.Utils.dll": ROOT / "build/runtime_compat/MonoMod.Utils.dll",
        r"BepInEx\plugins\RoadtripKoreanFontBridge\RoadtripKoreanFontBridge.dll": ROOT / "src/RoadtripKoreanFontBridge/bin/Release/RoadtripKoreanFontBridge.dll",
    }
    if sha(replacements[r"BepInEx\core\MonoMod.Utils.dll"]) != "BBED1657D03582CDB9399339AD146E9BAFD657EFCB65EEC5364D214E40F15D8B":
        raise RuntimeError("Unexpected corrected MonoMod build")
    state = ROOT / "work/install/installed_files.json"
    old_state = state.read_bytes()
    manifest = json.loads(old_state.decode("utf-8-sig"))
    entries = {entry["relative"]: entry for entry in manifest["files"]}
    for relative in replacements:
        if sha(GAME / relative) != entries[relative]["sha256"]:
            raise RuntimeError("Unrecorded installed change: " + relative)
    checkpoint = next((GAME / "UserData").glob("*_Checkpoint.xml"))
    original_save = checkpoint.read_bytes()
    recovered, name_changed = repaired_checkpoint(checkpoint)
    protected = list((GAME / "UserData").glob("*")) + list((ROOT / "translations").glob("*.json"))
    plugin = GAME / "BepInEx/plugins/RoadtripKoreanFontBridge"
    protected += list(plugin.rglob("*.ttf")) + list(plugin.glob("*.bundle"))
    protected += [GAME / "MonsterRoadtrip_Data/Managed/Assembly-CSharp.dll",
                  GAME / "MonsterRoadtrip_Data/StreamingAssets/aa/StandaloneWindows/texts_assets_all.bundle",
                  mono]
    before = {str(path): sha(path) for path in protected if path.is_file() and path != checkpoint}
    backup = ROOT / "work/install" / ("runtime_bridge_015_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    backup.mkdir()
    shutil.copytree(GAME / "UserData", backup / "UserData")
    shutil.copy2(state, backup / "installed_files.json")
    shutil.copy2(GAME / "BepInEx/config/BepInEx.cfg", backup / "BepInEx.cfg")
    for relative in replacements:
        target = backup / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(GAME / relative, target)
    try:
        for relative, source in replacements.items():
            shutil.copy2(source, GAME / relative)
            if sha(source) != sha(GAME / relative):
                raise RuntimeError("Copy hash mismatch")
            entries[relative]["sha256"] = sha(GAME / relative)
        if checkpoint.read_bytes() != original_save:
            raise RuntimeError("Checkpoint changed during update")
        if name_changed:
            checkpoint.write_bytes(recovered)
        if any(sha(Path(path)) != expected for path, expected in before.items()):
            raise RuntimeError("Protected files changed during update")
        state.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except Exception:
        for relative in replacements:
            shutil.copy2(backup / relative, GAME / relative)
        checkpoint.write_bytes(original_save)
        state.write_bytes(old_state)
        raise
    report = {"bridge_version": "0.1.5", "game_launched": False,
              "isolated_shutdown_verified": True, "full_game_shutdown_verified": False,
              "checkpoint_name_recovered": name_changed, "checkpoint_other_fields_unchanged": True,
              "protected_sha256": before, "updated_sha256": {key: sha(GAME / key) for key in replacements},
              "backup": str(backup)}
    (backup / "update.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("APPLIED corrected MonoMod + bridge 0.1.5; backend remains auto")
    print("Latest progress retained; damaged name field recovered=" + str(name_changed))
    print("BACKUP=" + str(backup))


if __name__ == "__main__":
    main()
