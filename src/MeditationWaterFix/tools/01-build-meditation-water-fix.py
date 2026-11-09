r"""Generate the Meditation Water Fix plugin YAML -- never hand-edit its Worldspaces/.

Report (curator, 2026-11-07): flat grey/purple sheets float among the platforms of the meditation worldspace
Akropolis 0A7FB9 (the Memory Point area). They pop with the camera like Vyn's sea before UnifiedWaterGridFix, cannot be
clicked in the console, survive `tws`, and vanish with Bottled Shaders' Unified Water disabled at boot (verified in
game). Every Akropolis cell has HasWater at the worldspace default height (0), just under the platforms (most
objects sit at z 140-390, the land at about -2048), and Unified Water draws that water as sheets. Vanilla shows no
water there and nothing reaches it.

This plugin forwards each cell's winning header (base Enderal; ClassMenue 0A7FBC from AmnesiaShrine.esp, its last
editor after FS, EGO and Akropolis_Camping) without HasWater and with its water height far below the land, and the
WRLD from its winner Water for Enderal CS (verbatim, needed as the cells' parent; masters it). Refs, land and navmesh
are not carried (header only). Asserted: every cell loses exactly one HasWater and had the default water height.
Re-serialize the cell editors into reference/mods before re-running (see the doc).
"""
import os
import re
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
WS = "Akropolis - 0A7FB9_Skyrim.esm"
BASE = os.path.join(ROOT, "reference", "base-2.1.4.4", "Skyrim", "Worldspaces", WS)
WRLD = os.path.join(ROOT, "reference", "mods", "WaterForEnderalCS", "Worldspaces", WS, "RecordData.yaml")
# later wins; each must be re-serialized after the plugin updates
OVERRIDES = [os.path.join(ROOT, "reference", *p, "Worldspaces", WS) for p in (
    ("base-2.1.4.4", "EnderalFS"), ("mods", "EGO"), ("mods", "AkropolisCamping"), ("mods", "AmnesiaShrine"))]
OUT = os.path.join(ROOT, "src", "MeditationWaterFix", "MeditationWaterFixESP", "Worldspaces", WS)
WATER_HEIGHT = "0"  # v1 used -30000 without HasWater: that removed the sea
SUBLISTS = ("Persistent:", "Temporary:", "Landscape:", "NavigationMeshes:")


def read(p):
    return open(p, encoding="utf-8", newline="").read()


def header_only(text):
    nl = "\r\n" if "\r\n" in text else "\n"
    out, skip = [], False
    for line in text.split(nl):
        if line and not line[0].isspace() and not line.startswith("- "):
            skip = line.startswith(SUBLISTS)
        if not skip:
            out.append(line)
    while out and out[-1] == "":
        out.pop()
    return nl.join(out) + nl, nl


def dewater(text, where):
    """v2 (2026-11-09): keep the water (the curator: the sea under the platforms belongs there; v1's removal showed
    the bare land at -2048). Only the water height changes: the 'use the worldspace default' sentinel 3.4028235E+38
    becomes an explicit 0 (the same height the engine already uses), so Unified Water's cache builder reads a real
    height (hypothesis: it took the sentinel literally, which left Akropolis_cache.wc empty)."""
    text, nl = header_only(text)
    if text.count(f"{nl}- HasWater{nl}") != 1:
        raise SystemExit(f"{where}: expected exactly one HasWater")
    if text.count(f"WaterHeight: 3.4028235E+38{nl}") != 1:
        raise SystemExit(f"{where}: water height is not the default")
    return text.replace(f"WaterHeight: 3.4028235E+38{nl}", f"WaterHeight: {WATER_HEIGHT}{nl}")


def winner(rel):
    best = os.path.join(BASE, rel)
    for o in OVERRIDES:
        p = os.path.join(o, rel)
        if os.path.exists(p):
            best = p
    return best


if os.path.isdir(OUT):
    shutil.rmtree(OUT)
os.makedirs(OUT)
shutil.copyfile(WRLD, os.path.join(OUT, "RecordData.yaml"))
cells = 0
for r, _, fs in os.walk(BASE):
    rel_dir = os.path.relpath(r, BASE)
    if rel_dir == ".":
        continue
    depth = rel_dir.count(os.sep)
    for f in fs:
        rel = os.path.join(rel_dir, f)
        dst = os.path.join(OUT, rel)
        if f == "GroupRecordData.yaml" and depth <= 1:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(os.path.join(BASE, rel), dst)
        elif f == "RecordData.yaml" and depth == 2:
            src = winner(rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "w", encoding="utf-8", newline="") as h:
                h.write(dewater(read(src), rel))
            cells += 1
            if src != os.path.join(BASE, rel):
                print("forwarded", rel, "from", os.path.relpath(src, ROOT).split(os.sep)[2])
print("cells:", cells)
if cells != 18:
    raise SystemExit(f"expected 18 Akropolis cells, got {cells}")
