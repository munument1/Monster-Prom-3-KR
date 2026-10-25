"""Read-only inspection of local Roadtrip logs and x86 crash minidumps.

Does not launch the game or modify saves, translations, fonts or loader files.
Only summaries are written to the repository's ignored work/testlogs directory.
"""
from __future__ import annotations

import json
import os
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def inspect_dump(path: Path) -> dict:
    data = path.read_bytes()
    if data[:4] != b"MDMP":
        raise ValueError("Not a Windows minidump")
    count, directory = struct.unpack_from("<II", data, 8)
    streams = {}
    for i in range(count):
        kind, size, offset = struct.unpack_from("<III", data, directory + 12 * i)
        if offset + size > len(data):
            raise ValueError("Truncated stream")
        streams[kind] = (size, offset)
    record = streams[6][1]
    code, _, _, address, params = struct.unpack_from("<IIQQI", data, record + 8)
    info = struct.unpack_from("<15Q", data, record + 40)
    result = {"dump": path.parent.name, "exception": hex(code),
              "parameters": [hex(x) for x in info[:min(params, 15)]]}
    modules = []
    module_stream = streams[4][1]
    for i in range(struct.unpack_from("<I", data, module_stream)[0]):
        offset = module_stream + 4 + 108 * i
        base, size = struct.unpack_from("<QI", data, offset)
        name_offset = struct.unpack_from("<I", data, offset + 20)[0]
        length = struct.unpack_from("<I", data, name_offset)[0]
        name = Path(data[name_offset + 4:name_offset + 4 + length].decode("utf-16-le")).name
        modules.append((base, size, name))

    def symbol(pointer):
        return next((f"{name}+{hex(pointer - base)}" for base, size, name in modules
                     if base <= pointer < base + size), hex(pointer))

    result["fault"] = symbol(address)
    # These offsets describe Windows x86 CONTEXT, not x64 CONTEXT.
    if 7 in streams and struct.unpack_from("<H", data, streams[7][1])[0] == 0:
        context = struct.unpack_from("<I", data, record + 164)[0]
        frame = struct.unpack_from("<I", data, context + 180)[0]
        thread = struct.unpack_from("<I", data, record)[0]
        thread_stream = streams[3][1]
        result["frames"] = [symbol(address)]
        for i in range(struct.unpack_from("<I", data, thread_stream)[0]):
            offset = thread_stream + 4 + 48 * i
            if struct.unpack_from("<I", data, offset)[0] != thread:
                continue
            start, size, memory = struct.unpack_from("<QII", data, offset + 24)
            for _ in range(12):
                if not start <= frame < start + size - 8:
                    break
                previous, target = struct.unpack_from("<II", data, memory + frame - start)
                result["frames"].append(symbol(target))
                if previous <= frame:
                    break
                frame = previous
    return result


def inspect_log(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    crash = next((i for i, line in enumerate(lines) if "Crash!!!" in line), len(lines))
    before = lines[:crash]
    return {
        "file": path.name,
        "errors_before_crash": [{"line": i + 1, "text": line} for i, line in enumerate(before)
                                if line.startswith(">ERROR") or "[Error" in line or "Exception:" in line],
        "ended_events": [line for line in before if ">Ended event:" in line],
        "checkpoint_writes": sum(">Save checkpoint" in line for line in before),
        "quit_before_crash": any("GeneralManager OnApplicationQuit" in line for line in before),
        "crash": crash != len(lines),
        "native_library_probe_lines": sum("Fallback handler could not load library" in line for line in before),
    }


def main():
    home = Path.home()
    logs = home / "AppData/LocalLow/Beautiful Glitch/Monster Roadtrip"
    crashes = Path(os.environ.get("TEMP", str(home / "AppData/Local/Temp"))) / "Beautiful Glitch/Monster Roadtrip/Crashes"
    report = {"game_launched": False,
              "logs": [inspect_log(p) for p in (logs / "Player.log", logs / "Player-prev.log") if p.is_file()],
              "dumps": [inspect_dump(p) for p in sorted(crashes.glob("*/crash.dmp"))]}
    out = ROOT / "work/testlogs/exit_crash_audit.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for log in report["logs"]:
        print(log["file"], "errors=" + str(len(log["errors_before_crash"])),
              "quit_then_crash=" + str(log["quit_before_crash"] and log["crash"]))
    for dump in report["dumps"]:
        print(dump["dump"], dump["fault"], dump["exception"])
    print("REPORT=" + str(out))


if __name__ == "__main__":
    main()
