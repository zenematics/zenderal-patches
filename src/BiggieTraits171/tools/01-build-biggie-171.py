r"""Build a copy of Biggie Traits.esp at HEDR 1.71 -- never hand-edit the copy.

Biggie Traits.esp (the Enderal conversion) is a HEDR 1.70 light plugin whose 148 records sit below object ID 0x800.
xEdit (and DynDOLOD) read every sub-0x800 ID in a pre-1.71 plugin as a Skyrim.esm form, so 47 of them "override"
base Enderal records of another type and DynDOLOD stops: "Record [STAT:00000064] in file Skyrim.esm is being
overridden by record [KYWD:00000064] in file Biggie Traits.esp ... version 1.7 which does not support form IDs
< 0x800". In game they were never broken (arch-docs/patches/TraitsRework.md, HEDR bullet) - this only makes the
header say what the records already are. 1.71 is the version that allows a light plugin's own IDs below 0x800.

The copy is the original byte for byte except the HEDR version float (file offset 30: 1.70 -> 1.71). It goes in a
NEW mod folder that must sit ABOVE the original in MO2's mod list, so its .esp wins the file conflict; the original
stays enabled for its scripts, interface files and meshes. plugins.txt is unchanged (same filename). The copy is
third-party content, generated on the user's machine, never committed.

Every plugin that masters Biggie Traits.esp must be 1.71 too (a pre-1.71 plugin's reference to a 1.71 light
plugin's sub-0x800 form resolves to Skyrim.esm - the FHR Parry Poise failure). As of 2026-10-23: Zen Traits.esp is
1.71 already and Zenderal - Traits.esp is built at 1.71 alongside this. Re-check after adding any Biggie patch.

Usage: python 01-build-biggie-171.py [--modlist E:\Zenderal]
"""
import argparse
import os
import struct
import sys

SRC_MOD = "Biggie Traits - Enderal Conversion"
OUT_MOD = "Biggie Traits - HEDR 1.71 (Zenderal)"
PLUGIN = "Biggie Traits.esp"
HEDR_OFFSET = 30                      # TES4 header (24) + 'HEDR' + size (6): the version float comes first
OLD, NEW = 1.70, 1.71

ap = argparse.ArgumentParser()
ap.add_argument("--modlist", default=r"E:\Zenderal")
a = ap.parse_args()
src = os.path.join(a.modlist, "mods", SRC_MOD, PLUGIN)
out_dir = os.path.join(a.modlist, "mods", OUT_MOD)

data = bytearray(open(src, "rb").read())
if data[0:4] != b"TES4" or data[24:28] != b"HEDR":
    sys.exit(f"{src}: not a TES4 header with HEDR first")
version = struct.unpack_from("<f", data, HEDR_OFFSET)[0]
flags = struct.unpack_from("<I", data, 8)[0]
if round(version, 2) != OLD:
    sys.exit(f"{src}: HEDR {version:.2f}, expected {OLD:.2f} -- the mod changed; re-check before patching")
if not flags & 0x200:
    sys.exit(f"{src}: no light-plugin flag -- the mod changed; re-check")
struct.pack_into("<f", data, HEDR_OFFSET, NEW)

os.makedirs(out_dir, exist_ok=True)
built = os.path.join(out_dir, PLUGIN)
open(built, "wb").write(data)

orig = open(src, "rb").read()
diff = [i for i in range(len(orig)) if orig[i] != data[i]]
if len(orig) != len(data) or not diff or min(diff) < HEDR_OFFSET or max(diff) >= HEDR_OFFSET + 4:
    sys.exit(f"copy differs outside the HEDR version float: {diff[:10]}")
meta = os.path.join(out_dir, "meta.ini")
if not os.path.exists(meta):
    open(meta, "w", encoding="utf-8", newline="\r\n").write("[General]\nmodid=0\nversion=1.0.0\ninstalled=true\n")
print(f"{built}: HEDR {version:.2f} -> {struct.unpack_from('<f', data, HEDR_OFFSET)[0]:.2f}, "
      f"{len(diff)} byte(s) changed, light flag kept")
