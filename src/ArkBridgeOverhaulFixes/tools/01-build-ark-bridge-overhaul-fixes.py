"""Builds the Spriggit YAML for Zenderal - Ark Bridge Overhaul Fixes.esp.

Two things Ark Bridge Overhaul.esp (1.5.1) leaves out of reach:

1. KataPUMB's Grappling Hook (Tier II) book. ABO disables the original under-bridge crate
   07C38C:Skyrim.esm that KataHiddenPowers.esp rests book ref 007985 on, so the book falls away.
   This disables Kata's ref and places a new copy of the same book on ABO's own DungeonCrate02
   0300015F, at the height above the crate the book had on the original one.
2. Magical Symbol 037889:Skyrim.esm. ABO's new _00E_Ark_1024WallGate02 0000E3 (scale 1.4) encloses
   it. It is moved to the spot from the open Nexus bug report on ABO, and its linked light
   03788C (persistent; the symbol's script disables it on pickup) moves with it at the same offset.
3. The river's drop under the first bridge. ABO disables Enderal's stone bridge and moves the
   waterfall curtains beside its pier outward, leaving bare riverbed below the river's edge. New
   copies of the curtains go back at base Enderal's positions, and a strip of water tiles carries
   the river's surface from the cell border to under ABO's plank edge.

Records are copied from the serialized KataHiddenPowers.esp in reference/mods/KataHiddenPowers
(serialize it from the modlist first) and from base Enderal in reference/base/Skyrim, and edited by
assertion, never retyped.

Run from the repo root:  python -I src/ArkBridgeOverhaulFixes/tools/01-build-ark-bridge-overhaul-fixes.py
"""
import math
import os
import shutil

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
KATA = os.path.join(REPO, "reference", "mods", "KataHiddenPowers", "Worldspaces", "Vyn - 001D3C_Skyrim.esm")
BASE = os.path.join(REPO, "reference", "base", "Skyrim", "Worldspaces", "Vyn - 001D3C_Skyrim.esm")
OUT = os.path.join(REPO, "src", "ArkBridgeOverhaulFixes", "ArkBridgeOverhaulFixesESP")
WS = os.path.join(OUT, "Worldspaces", "Vyn - 001D3C_Skyrim.esm")
PLUGIN = "Zenderal - Ark Bridge Overhaul Fixes.esp"

# Magical Symbol 037889 and its light 03788C, as base Enderal places them (no list plugin overrides
# either). New spot from the ABO bug report "Magical Symbol inaccessible" (Juppsi, 2026-04-17).
SYMBOL = (-15903.95, -455.36157, 1295.3542)
SYMBOL_LIGHT = (-15899.832, -454.95584, 1305.0143)
NEW_SYMBOL = (-15529.043, -1103.7936, 1228.9255)
NEW_SYMBOL_ROT_Z = round(math.radians(132.927), 6)
NEW_SYMBOL_LIGHT = tuple(round(NEW_SYMBOL[i] + SYMBOL_LIGHT[i] - SYMBOL[i], 4) for i in range(3))

# ABO moves the curtains either side of the first bridge's pier (BridgeM 07C3F5, x -19306)
# outward (slopes 07C3F7 -19613 -> -19783 and 07C3F9 -19019 -> -18758, talls 07C3F6/07C3F8 the
# same way), leaving the drop at the pier bare. New copies go back at base Enderal's spots;
# ABO's moved ones stay.
CURTAINS = [("000801", "07C3F7:Skyrim.esm"), ("000802", "07C3F9:Skyrim.esm"),
            ("000803", "07C3F6:Skyrim.esm"), ("000804", "07C3F8:Skyrim.esm")]

# The river's surface is cell 001FAB's water (1280), so it stops dead at the cell border y = 0,
# while the riverbed runs on below it to the curtains' crest. Enderal's old walkway sat at ~1520,
# out of sight of that seam; ABO's planks at 1337 look straight at it (found in game at
# (-20003, -69)). A row of 128x128 pieces of the river's own water type (Water512 0FD0CB, water
# DefaultWater 000018 like Vyn's) at the river's height carries the surface from the border to just
# under ABO's plank edge, along the whole span of ABO's bridge. North edges on the border, tiles
# abutting, so nothing overlaps coplanar water.
WATER_TILE = "0FD0CB:Skyrim.esm"
WATER_TILE_SCALE = 0.25          # 512 * 0.25 = 128 units
WATER_X0, WATER_TILES = -20416, 19   # x -20416 .. -17984
WATER_STRIP = [("%06X" % (0x805 + i), (WATER_X0 + 64 + 128 * i, -64, 1280)) for i in range(WATER_TILES)]

# Original crate 07C38C (Enderal) and the book Kata placed on it.
OLD_CRATE = (-18547.582, 22.440792, 1549.6398)
BOOK = (-18523.457, 24.240717, 1577.9066)
# ABO's replacement crate 0300015F, read from Ark Bridge Overhaul.esp 1.5.1 (same base 07B824).
NEW_CRATE = (-18027.27, -435.46, 1396.03)
NEW_CRATE_SCALE = 0.97
LIFT = 0.5  # drop the book onto the lid instead of spawning it inside it

NEW_BOOK = tuple(round(NEW_CRATE[i] + (BOOK[i] - OLD_CRATE[i]) * NEW_CRATE_SCALE + (LIFT if i == 2 else 0), 2)
                 for i in range(3))

CRLF = "\r\n"


def read(path):
    with open(path, "r", encoding="utf-8", newline="") as f:
        return f.read()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def replace_once(text, old, new):
    n = text.count(old)
    if n != 1:
        raise SystemExit("expected 1 match for %r, found %d" % (old, n))
    return text.replace(old, new)


def list_item(text, formkey, indent):
    """The '- MutagenObjectType' list item holding `formkey`, at `indent` spaces, CRLF-normalised."""
    lines = text.replace("\r\n", "\n").split("\n")
    head = " " * indent + "- MutagenObjectType:"
    hits = [i for i, l in enumerate(lines) if l == " " * (indent + 2) + "FormKey: " + formkey]
    if len(hits) != 1:
        raise SystemExit("expected 1 %s, found %d" % (formkey, len(hits)))
    start = hits[0] - 1
    if not lines[start].startswith(head):
        raise SystemExit("%s is not the first field of its list item" % formkey)
    end = start + 1
    while end < len(lines) and lines[end].startswith(" " * (indent + 1)):
        end += 1
    return CRLF.join(lines[start:end]) + CRLF


def curtain_copies():
    """New copies of the waterfall curtains ABO moved away from the first bridge's pier, at
    base Enderal's positions, so the river's drop at the cell border is covered again."""
    src = read(os.path.join(BASE, "-1, -1", "-1, -1", "001FAC_Skyrim.esm", "RecordData.yaml"))
    out = []
    for new_id, old in CURTAINS:
        item = list_item(src, old, 0)
        out.append(replace_once(item, "  FormKey: " + old, "  FormKey: %s:%s" % (new_id, PLUGIN)))
    for new_id, pos in WATER_STRIP:
        out.append(CRLF.join([
            "- MutagenObjectType: PlacedObject",
            "  FormKey: %s:%s" % (new_id, PLUGIN),
            "  Base: " + WATER_TILE,
            "  Scale: %s" % WATER_TILE_SCALE,
            "  Placement:",
            "    Position: %s, %s, %s" % pos,
            "    Rotation: 0, 0, 0",
            ""]))
    return out


if os.path.isdir(OUT):
    shutil.rmtree(OUT)

write(os.path.join(OUT, "RecordData.yaml"), CRLF.join([
    "SpriggitSource:",
    "  PackageName: Spriggit.Yaml.Skyrim",
    "  Version: 0.40",
    "ModKey: " + PLUGIN,
    "GameRelease: EnderalSE",
    "ModHeader:",
    "  Flags:",
    "  - Small",
    "  Stats:",
    "    Version: 1.7",
    "  Author: Zenderal",
    "  Description: Puts KataPUMB's Grappling Hook (Tier II) book and a Magical Symbol back within reach around Ark Bridge Overhaul's rebuilt bridge.",
    "  MasterReferences:",
    "  - Master: Skyrim.esm",
    "    FileSize: 0",
    "  - Master: Update.esm",
    "    FileSize: 0",
    "  - Master: Enderal - Forgotten Stories.esm",
    "    FileSize: 0",
    "  - Master: Ark Bridge Overhaul.esp",
    "    FileSize: 0",
    "  - Master: KataHiddenPowers.esp",
    "    FileSize: 0",
    "  INTV: 1",
    ""]))
write(os.path.join(OUT, "spriggit-meta.json"),
      '{\n  "PackageName": "Spriggit.Yaml.Skyrim",\n  "Version": "0.40.0",\n  "Release": "EnderalSE",\n'
      '  "ModKey": "%s"\n}' % PLUGIN)

# WRLD: Kata's header and persistent-cell header (every list override of both carries the same
# data), with the symbol's persistent light as the persistent cell's one ref.
wrld = read(os.path.join(KATA, "RecordData.yaml"))
if "  Persistent:" in wrld:
    raise SystemExit("Kata's Vyn TopCell changed shape; re-check it before building")
light = list_item(read(os.path.join(BASE, "RecordData.yaml")), "03788C:Skyrim.esm", 2)
light = replace_once(light, "      Position: %s, %s, %s" % SYMBOL_LIGHT,
                     "      Position: %s, %s, %s" % NEW_SYMBOL_LIGHT)
wrld = replace_once(wrld, "  WaterHeight: 3.4028235E+38" + CRLF + "  MajorFlags:",
                    "  WaterHeight: 3.4028235E+38" + CRLF + "  Persistent:" + CRLF + light + "  MajorFlags:")
write(os.path.join(WS, "RecordData.yaml"), wrld)

for rel in [("-1, 0", "GroupRecordData.yaml"), ("-1, 0", "-1, 0", "GroupRecordData.yaml"),
            ("-1, -1", "GroupRecordData.yaml"), ("-1, -1", "-1, -1", "GroupRecordData.yaml")]:
    os.makedirs(os.path.dirname(os.path.join(WS, *rel)), exist_ok=True)
    shutil.copyfile(os.path.join(KATA, *rel), os.path.join(WS, *rel))

# Cell (-5, 0): Kata's cell (the list winner) with its book ref disabled the xEdit way.
cell_a = read(os.path.join(KATA, "-1, 0", "-1, 0", "001FAB_Skyrim.esm", "RecordData.yaml"))
cell_a = replace_once(cell_a,
    "  FormKey: 007985:KataHiddenPowers.esp" + CRLF,
    "  FormKey: 007985:KataHiddenPowers.esp" + CRLF +
    "  MajorRecordFlagsRaw: 2048" + CRLF +
    "  SkyrimMajorRecordFlags:" + CRLF +
    "  - InitiallyDisabled" + CRLF)
cell_a = replace_once(cell_a,
    "  Owner: 000007:Skyrim.esm" + CRLF,
    "  Owner: 000007:Skyrim.esm" + CRLF +
    "  EnableParent:" + CRLF +
    "    Reference: 000014:Skyrim.esm" + CRLF +
    "    Flags:" + CRLF +
    "    - SetEnableStateToOppositeOfParent" + CRLF +
    "    Unknown: 0x000000" + CRLF)
cell_a = replace_once(cell_a, "    Position: -18523.457, 24.240717, 1577.9066",
                      "    Position: -18523.457, 24.240717, -30000")
write(os.path.join(WS, "-1, 0", "-1, 0", "001FAB_Skyrim.esm", "RecordData.yaml"), cell_a)

# Cell (-5, -1): Kata's cell header (the list winner), with the Ark location every other
# plugin keeps restored, plus the new book ref on ABO's crate.
cell_b = read(os.path.join(KATA, "-1, -1", "-1, -1", "001FAC_Skyrim.esm", "RecordData.yaml"))
if "Temporary:" in cell_b or "Location:" in cell_b:
    raise SystemExit("Kata's 001FAC changed shape; re-check it before building")
cell_b = replace_once(cell_b, "- 07C979:Skyrim.esm" + CRLF + "MajorFlags:",
    "- 07C979:Skyrim.esm" + CRLF +
    "Location: 0A1A12:Skyrim.esm" + CRLF +
    "Temporary:" + CRLF +
    "- MutagenObjectType: PlacedObject" + CRLF +
    "  FormKey: 000800:" + PLUGIN + CRLF +
    "  Base: 006D00:KataHiddenPowers.esp" + CRLF +
    "  Owner: 000007:Skyrim.esm" + CRLF +
    "  Placement:" + CRLF +
    "    Position: %s, %s, %s" % NEW_BOOK + CRLF +
    "    Rotation: -0.00069080025, -0.00031644572, 0.0046792827" + CRLF +
    "".join(curtain_copies()) +
    "MajorFlags:")
write(os.path.join(WS, "-1, -1", "-1, -1", "001FAC_Skyrim.esm", "RecordData.yaml"), cell_b)

# Cell (-4, -1) CapitalCityDoor: base Enderal's header (every list override carries the same
# data), cut before its LAND, plus the moved symbol.
cell_c_src = read(os.path.join(BASE, "-1, -1", "-1, -1", "CapitalCityDoor - 001FA5_Skyrim.esm", "RecordData.yaml"))
header = cell_c_src.replace("\r\n", "\n").split("Landscape:\n")[0]
if not header.rstrip("\n").endswith("Location: 0A1A12:Skyrim.esm"):
    raise SystemExit("CapitalCityDoor header changed shape; re-check it before building")
symbol = list_item(cell_c_src, "037889:Skyrim.esm", 0)
symbol = replace_once(symbol, "    Position: %s, %s, %s" % SYMBOL, "    Position: %s, %s, %s" % NEW_SYMBOL)
symbol = replace_once(symbol, "    Rotation: 0, -0, 0.42000002", "    Rotation: 0, -0, %s" % NEW_SYMBOL_ROT_Z)
write(os.path.join(WS, "-1, -1", "-1, -1", "CapitalCityDoor - 001FA5_Skyrim.esm", "RecordData.yaml"),
      header.replace("\n", CRLF) + "Temporary:" + CRLF + symbol)

print("new book at", NEW_BOOK)
print("new symbol at", NEW_SYMBOL, "rot z", NEW_SYMBOL_ROT_Z, "light at", NEW_SYMBOL_LIGHT)
