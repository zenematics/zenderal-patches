"""Zenderal - Unskippable Cinematics: Enderal's Bink videos play with abInterruptible = false.

Every Game.PlayBink call in SureAI's 2.1.4.4 source passes `true`, so a key press, a click or the console key ends
the video at once. The intro (after MQP01's Daddy scene) opens with a sentence of narration over black, which reads
as a broken black screen and invites exactly that key press (2026-10-25). Curator's taste: cinematics play through;
Enderal's MCM "Skip videos" (`_00E_VideoSkip`) still skips them on purpose.

For each script below this copies SureAI's source, flips exactly that one PlayBink argument (asserted once), adds a
`; ZP` comment and compiles with the Enderal-first import path. Then it checks the compiled string table against the
game's shipped .pex (extracted from Enderal's BSAs): the only differences allowed are the optimizer's `::temp`
names and the script name's case.

Usage: python 01-build-unskippable-cinematics.py
"""
import json
import os
import re
import struct
import subprocess
import sys
import tempfile

import lz4.frame

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
OUT_SRC = os.path.join(HERE, "..", "Scripts", "source")
OUT_PEX = os.path.join(HERE, "..", "Scripts", "compiled")
TOOLS = json.load(open(os.path.join(REPO, ".claude", "config", "tools.json"), encoding="utf-8-sig"))
SRC = TOOLS["papyrusSource"]["enderal"]
DATA = os.path.join(TOOLS["gameRoot"], "Data")
# script name (as in its Scriptname line) -> the video it plays
SCRIPTS = {
    "_00E_MQP01_Functions": "EnderalIntro.bik",
    "_00E_MQP03_Functions": "MQP03NearDeathExperience.bik",
    "_00E_MQ101_QuickStart": "MQP03NearDeathExperience.bik",
    "_00E_MQ17_Functions": "MQ17BlackGuardian.bik",
    "_00E_MQ18a_Functions": "Enderal_Credits.bik",
    "_00E_MQ18b_Functions": "Enderal_Credits.bik",
    "_00E_FS_MQ18c_Functions": "Enderal_Credits.bik",
}
BSAS = ("E - Misc.bsa", "E - Update.bsa", "Enderal - Forgotten Stories.bsa", "Skyrim - Misc.bsa")


def bsa_file(bsa, want):
    """Bytes of one file from an SSE v105 BSA, or None."""
    f = open(bsa, "rb")
    _, ver, _, aflags, nfold, _, _, lfile, _ = struct.unpack("<4sIIIIIIII", f.read(36))
    folders = [struct.unpack("<QIIQ", f.read(24)) for _ in range(nfold)]
    recs = []
    for _, cnt, _, _ in folders:
        n = f.read(1)[0]
        name = f.read(n)[:-1].decode("cp1252")
        for _ in range(cnt):
            _, size, off = struct.unpack("<QII", f.read(16))
            recs.append((name, size, off))
    names = f.read(lfile).split(b"\0")
    for (folder, size, off), name in zip(recs, names):
        if (folder + "\\" + name.decode("cp1252")).lower() != want.lower():
            continue
        comp = bool(aflags & 4) ^ bool(size & 0x40000000)
        f.seek(off)
        data = f.read(size & 0x3FFFFFFF)
        if aflags & 0x100:
            data = data[1 + data[0]:]
        return lz4.frame.decompress(data[4:]) if comp else data
    return None


def pex_strings(data):
    i = 16
    for _ in range(3):
        i += 2 + struct.unpack_from(">H", data, i)[0]
    n = struct.unpack_from(">H", data, i)[0]
    i += 2
    out = []
    for _ in range(n):
        ln = struct.unpack_from(">H", data, i)[0]
        out.append(data[i + 2:i + 2 + ln].decode("latin1"))
        i += 2 + ln
    return out


def normal(strings):
    return {s.lower() for s in strings if not s.startswith("::temp")}


TYPE_NAMES = {"float", "int", "bool", "string"}


def compile_one(psc, outdir, imports):
    r = subprocess.run([TOOLS["papyrusCompiler"], psc, "-f=" + TOOLS.get("papyrusFlags", "TESV_Papyrus_Flags.flg"),
                        "-i=" + imports, "-o=" + outdir, "-op"], capture_output=True, text=True)
    assert "1 succeeded" in r.stdout, r.stdout + r.stderr
    return open(os.path.join(outdir, os.path.splitext(os.path.basename(psc))[0] + ".pex"), "rb").read()


def main():
    os.makedirs(OUT_SRC, exist_ok=True)
    os.makedirs(OUT_PEX, exist_ok=True)
    imports = ";".join([SRC, TOOLS["papyrusSource"]["skse"], TOOLS["papyrusSource"]["vanilla"]] + TOOLS.get("importDirs", []))
    for script, video in SCRIPTS.items():
        src = os.path.join(SRC, script.lower() + ".psc")
        raw = open(src, "rb").read()
        nl = b"\r\n" if b"\r\n" in raw else b"\n"
        assert re.match(rb"(?i)\s*scriptname\s+" + script.encode(), raw), script
        old = re.compile(rb'(?im)^([ \t]*)Game\.PlayBink\("' + re.escape(video.encode()) + rb'", true\)')
        assert len(old.findall(raw)) == 1, (script, len(old.findall(raw)))
        new = old.sub(lambda m: m.group(1) + b"; ZP: not interruptible - a key press ended it at once" + nl + m.group(1)
                      + b'Game.PlayBink("' + video.encode() + b'", false)', raw)
        dst = os.path.join(OUT_SRC, script + ".psc")
        open(dst, "wb").write(new)
        ours = compile_one(dst, OUT_PEX, imports)
        # SureAI's unmodified source, compiled the same way: the fork must match it exactly (the flag is a literal)
        with tempfile.TemporaryDirectory() as tmp:
            orig = os.path.join(tmp, script + ".psc")
            open(orig, "wb").write(raw)
            rebuilt = compile_one(orig, tmp, imports)
        # (as sorted lists: the compiler writes its string table in an order that varies between runs)
        assert sorted(pex_strings(ours)) == sorted(pex_strings(rebuilt)), (script, "fork's strings differ from a rebuild")
        shipped = None
        for b in BSAS:
            p = os.path.join(DATA, b)
            if os.path.isfile(p):
                shipped = bsa_file(p, "scripts\\" + script.lower() + ".pex")
                if shipped:
                    break
        assert shipped, (script, "not found in Enderal's BSAs")
        a, b = normal(pex_strings(shipped)), normal(pex_strings(ours))
        # the optimizer (-op) can drop an unused temp's type name ("float"); anything else means the source drifted
        extra = (a - b) - TYPE_NAMES
        assert not extra and not (b - a), (script, sorted(a - b)[:8], sorted(b - a)[:8])
        note = f"; shipped also has {sorted(a - b)} (unused temp types)" if a - b else ""
        print(f"  {script:26} {video:30} compiled; = rebuilt source; shipped .pex matches ({len(b)} strings){note}")
    print(f"built {len(SCRIPTS)} scripts")


if __name__ == "__main__":
    sys.exit(main())
