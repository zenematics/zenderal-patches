"""Zenderal - Blood Spurt Freeze Fix: Enhanced Blood Textures' zbloodnpc without its zero-direction spurts.

Fog Wood fights froze the game three times (2026-11-06, 2026-11-14 21:36 and 22:57). The 21:36 Shatterveil hang dump
has a job thread looping forever in the engine's ray-grid walk (SkyrimSE.exe+B47666, ID 60796) under
BGSImpactManager::PlayImpactEffect (36215), called from the Papyrus native ObjectReference.PlayImpactEffect
(ID 56208). That native's own arguments, read from its stack slots, are pick direction (0, 0, 0), length 512,
abApplyNodeRotation false, abUseNodeLocalRotation true. In the list only Enhanced Blood Textures' blood spurts pass
those: 12 calls in zbloodnpc (the DF - Enhanced Blood Textures Patch copy wins over EBT's own). 36215 turns a zero
direction into a zero-length pick and plays nothing when the pick misses, so these spurts almost never showed; one
in many reached the grid walk with an end point at 1.4e25 units, and the walk never ends.
See arch-docs/patches/BloodSpurtFreezeFix.md.

This copies the winning zbloodnpc.psc (DF - Enhanced Blood Textures Patch/Source/Scripts), checks that it rebuilds to
the shipped zbloodnpc.pex (same strings, same PlayImpactEffect call count), comments out exactly the 12 zero-direction
PlayImpactEffect calls, compiles the fork and checks: every shipped string kept, the same properties, 12 fewer calls.

Usage (repo root): python src/BloodSpurtFreezeFix/tools/01-build-blood-spurt-freeze-fix.py
"""
import json
import os
import re
import struct
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
OUT_SRC = os.path.join(HERE, "..", "Scripts", "source")
OUT_PEX = os.path.join(HERE, "..", "Scripts", "compiled")
TOOLS = json.load(open(os.path.join(REPO, ".claude", "config", "tools.json"), encoding="utf-8-sig"))
MODS = TOOLS["modsDir"]
WINNER = os.path.join(MODS, "DF - Enhanced Blood Textures Patch")
DF_SOURCE = os.path.join(MODS, "Dismembering Framework", "source", "scripts")  # DismemberingFramework.IsDismembered
SCRIPT = "zbloodnpc"
REMOVED = 12

# a PlayImpactEffect call whose three direction arguments are all literal zero
ZERO_PICK = re.compile(
    rb"(?im)^([ \t]*)(target\.PlayImpactEffect\(\w+, asNodeName, 0 as Float, 0 as Float, 0 as Float, 512 as Float, "
    rb"false, true\))[ \t]*(?=\r?$)")
ANY_ZERO_PICK = re.compile(rb"(?i)PlayImpactEffect\([^)\r\n]*,\s*0(?:\.0+)?(?: as Float)?\s*,\s*0(?:\.0+)?(?: as Float)?\s*,"
                           rb"\s*0(?:\.0+)?(?: as Float)?\s*,")
PROPERTY = re.compile(rb"(?im)^\s*[\w\[\]]+\s+property\s+(\w+)")
TYPE_NAMES = {"float", "int", "bool", "string"}


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


def count_calls(data, method):
    """callmethod instructions naming <method> (opcode 0x17, then the name as an identifier argument)."""
    strs = pex_strings(data)
    idx = [i for i, s in enumerate(strs) if s.lower() == method.lower()]
    assert len(idx) == 1, (method, idx)
    return data.count(bytes([0x17, 0x01]) + struct.pack(">H", idx[0]))


def compile_one(psc, outdir, imports):
    # first wins: psc's own folder must lead, or the compiler takes the same-named script from another import dir
    imports = os.path.dirname(os.path.abspath(psc)) + ";" + imports
    r = subprocess.run([TOOLS["papyrusCompiler"], psc, "-f=" + TOOLS.get("papyrusFlags", "TESV_Papyrus_Flags.flg"),
                        "-i=" + imports, "-o=" + outdir, "-op"], capture_output=True, text=True)
    assert "1 succeeded" in r.stdout, r.stdout + r.stderr
    return open(os.path.join(outdir, SCRIPT + ".pex"), "rb").read()


def main():
    os.makedirs(OUT_SRC, exist_ok=True)
    os.makedirs(OUT_PEX, exist_ok=True)
    assert os.path.isfile(os.path.join(DF_SOURCE, "dismemberingframework.psc")), DF_SOURCE
    imports = ";".join([TOOLS["papyrusSource"]["enderal"], TOOLS["papyrusSource"]["skse"],
                        TOOLS["papyrusSource"]["vanilla"], DF_SOURCE] + TOOLS.get("importDirs", []))

    raw = open(os.path.join(WINNER, "Source", "Scripts", SCRIPT + ".psc"), "rb").read()
    shipped = open(os.path.join(WINNER, "Scripts", SCRIPT + ".pex"), "rb").read()
    assert re.search(rb"(?im)^\s*scriptname\s+" + SCRIPT.encode() + rb"\b", raw), "not zbloodnpc"
    a = normal(pex_strings(shipped))
    calls_shipped = count_calls(shipped, "PlayImpactEffect")

    with tempfile.TemporaryDirectory() as tmp:
        orig = os.path.join(tmp, SCRIPT + ".psc")
        open(orig, "wb").write(raw)
        rebuilt_pex = compile_one(orig, tmp, imports)
    rebuilt = normal(pex_strings(rebuilt_pex))
    drift = ((a - rebuilt) | (rebuilt - a)) - TYPE_NAMES
    assert not drift, ("the shipped source differs from the shipped .pex", sorted(drift)[:8])
    assert count_calls(rebuilt_pex, "PlayImpactEffect") == calls_shipped, "call count differs from the shipped .pex"
    print(f"  shipped source rebuilds to the shipped .pex ({len(a)} strings, {calls_shipped} PlayImpactEffect calls)")

    hits = ZERO_PICK.findall(raw)
    assert len(hits) == REMOVED, f"expected {REMOVED} zero-direction spurts, found {len(hits)}"
    assert len(ANY_ZERO_PICK.findall(raw)) == REMOVED, "a zero-direction call this pattern does not cover"
    new = ZERO_PICK.sub(lambda m: m.group(1) + b"; ZBS: zero-direction spurt removed (it froze the game): "
                        + m.group(2), raw)
    live = b"\n".join(line for line in new.splitlines() if not line.lstrip().startswith(b";"))
    assert not ANY_ZERO_PICK.search(live), "a zero-direction call is left"
    header = (b"; Zenderal - Blood Spurt Freeze Fix: the DF - Enhanced Blood Textures Patch's zbloodnpc minus its 12\r\n"
              b"; PlayImpactEffect calls with pick direction (0, 0, 0) ('; ZBS'). Nothing else changed.\r\n"
              b"; Generated by src/BloodSpurtFreezeFix/tools/01-build-blood-spurt-freeze-fix.py\r\n")
    new = header + new
    assert PROPERTY.findall(raw) == PROPERTY.findall(new), "the fork must declare exactly the original properties"

    dst = os.path.join(OUT_SRC, SCRIPT + ".psc")
    open(dst, "wb").write(new)
    pex = compile_one(dst, OUT_PEX, imports)
    ours = normal(pex_strings(pex))
    lost = (a - ours) - TYPE_NAMES
    assert not lost, ("the fork lost shipped strings", sorted(lost)[:8])
    calls_ours = count_calls(pex, "PlayImpactEffect")
    assert calls_ours == calls_shipped - REMOVED, (calls_ours, calls_shipped)
    print(f"  fork compiled: all shipped strings kept, {len(PROPERTY.findall(new))} properties as the original, "
          f"PlayImpactEffect calls {calls_shipped} -> {calls_ours}")
    print(f"  -> {os.path.relpath(dst, REPO)}")
    print(f"  -> {os.path.relpath(os.path.join(OUT_PEX, SCRIPT + '.pex'), REPO)}")


if __name__ == "__main__":
    sys.exit(main())
