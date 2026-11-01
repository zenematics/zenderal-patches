"""Generate `NoCrystalBasesESP/`: Enderal's four crystal-cluster base statics drawn as nothing.

Curator's test (2026-10-26, Crystal Forest): the flat, pale ground pieces under the crystal clusters
(`_00E_CrystalArcane_Base 0FA16A`, console "crystalbase01pink.nif") look odd; the crystals themselves stay. The four
`crystalbase01*` statics are `_00E_CrystalArcane_Base 0FA16A` (pink), `_00E_CrystalRed_Base 0FA16B`,
`_00E_CrystalGreen_Base 0824B8` and `_00E_CrystalBlue_Base 0824B9`, all `Skyrim.esm` (base Enderal), and no list plugin
overrides them (scan 2026-10-26). Each override is base Enderal's record verbatim with the model swapped for
`Effects\\FXEmptyObject.nif` (an empty mesh in Skyrim - Meshes0.bsa) and its texture-hash `Data` dropped, so every
placed base vanishes, collision included, without touching a single placed reference.

Usage: python 01-build-no-crystal-bases.py [<reference/base dir>]   (default: the repo's reference/base)
"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REF = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "..", "..", "reference", "base")
OUT = os.path.join(HERE, "..", "NoCrystalBasesESP", "Statics")
BASES = {
    "0FA16A": "_00E_CrystalArcane_Base",
    "0FA16B": "_00E_CrystalRed_Base",
    "0824B8": "_00E_CrystalGreen_Base",
    "0824B9": "_00E_CrystalBlue_Base",
}
EMPTY = b"Effects\\FXEmptyObject.nif"

if os.path.isdir(OUT):
    shutil.rmtree(OUT)
os.makedirs(OUT)
for fid, edid in BASES.items():
    name = "%s - %s_Skyrim.esm.yaml" % (edid, fid)
    for root in ("EnderalFS", "Skyrim"):  # Forgotten Stories wins if it overrides one
        src = os.path.join(REF, root, "Statics", name)
        if os.path.isfile(src):
            break
    else:
        raise SystemExit("not found: " + name)
    raw = open(src, "rb").read()
    nl = b"\r\n" if b"\r\n" in raw else b"\n"
    lines = raw.split(nl)
    files = [i for i, l in enumerate(lines) if l.startswith(b"  File: ") and b"crystalbase01" in l.lower()]
    assert len(files) == 1, (name, "model line not found exactly once")
    i = files[0]
    lines[i] = b"  File: " + EMPTY
    if i + 1 < len(lines) and lines[i + 1].startswith(b"  Data: "):
        del lines[i + 1]
    open(os.path.join(OUT, name), "wb").write(nl.join(lines))
    print("%s %s <- %s" % (fid, edid, root))
