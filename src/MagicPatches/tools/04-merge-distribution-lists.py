#!/usr/bin/env python3
"""Merge Enderal's magic distribution leveled lists for Zenderal - Magic Patches.esp.

Two problems, one bug class (last-loader-wins on whole records):

1. The four spell-book LOOT lists (_00E_SpellBooksLootA-D): Apocalypse injects 8 book
   entries into each, but the EGO - KataPUMB Spell Package patch loads later and wins
   with a version that has none of them - Apocalypse tomes never drop as loot.
2. The scroll loot list (00E_ScrollsLowChance -> EGO's 02E_Scrolls): Apocalypse WINS
   this one, but built its override on base Enderal - reverting EGO's rebalance
   (renamed EditorID, ChanceNone 0.5 -> 0.15, 6 entries removed, 2 added) while
   adding its 4 scrolls.

Fix per list: the deliberate winner's record copied verbatim (EGO's for the scroll
list, the EGO-Kata patch's for the loot lists), with Apocalypse's additions
re-appended. Additions are derived: an entry whose Reference is keyed to
Apocalypse's own plugin. Counts asserted.

Ownership note: Zenderal - Magic Patches OWNS these five LVLI records;
Zenderal - Kata Fixes owns the three vendor chests. Neither may touch the other's.

Inputs (regenerate with /spriggit-decompile-reference):
  reference/mods/EGO/esp       (Enderal SE - Gameplay Overhaul.esp)
  reference/mods/KataEGOPatch  (EGO - KataPUMB Spell Package.esp)
  reference/mods/Apocalypse    (Apocalypse - Magic of Skyrim.esp)

Output: src/MagicPatches/MagicPatchesESP/LeveledItems/*.yaml
"""
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
REF = os.path.join(ROOT, "reference", "mods")
OUT = os.path.join(ROOT, "src", "MagicPatches", "MagicPatchesESP", "LeveledItems")

APO = "Apocalypse - Magic of Skyrim.esp"

# list hex -> (winner tree whose version we forward, expected Apocalypse additions)
MERGES = {
    "0905A5": (os.path.join("EGO", "esp"), 4),        # 02E_Scrolls (scroll loot)
    "13798C": ("KataEGOPatch", 8),                    # _00E_SpellBooksLootA
    "13798D": ("KataEGOPatch", 8),                    # _00E_SpellBooksLootB
    "1447A2": ("KataEGOPatch", 8),                    # _00E_SpellBooksLootC
    "1447A3": ("KataEGOPatch", 8),                    # _00E_SpellBooksLootD
}

# one leveled-list entry block: "- Data:" plus every following line indented deeper
BLOCK_RE = re.compile(r"- Data:\r?\n(?:  +[^\r\n]*\r?\n)+")
REF_RE = re.compile(r"Reference: ([0-9A-Fa-f]{6}:[^\r\n]+)")


def find_list(tree, hexid):
    d = os.path.join(REF, tree, "LeveledItems")
    for fn in os.listdir(d):
        if f" - {hexid}_Skyrim.esm.yaml" in fn:
            return os.path.join(d, fn)
    sys.exit(f"list {hexid} not found in {tree}")


def entries(text):
    out = []
    for m in BLOCK_RE.finditer(text):
        r = REF_RE.search(m.group(0))
        if not r:
            sys.exit("entry block without Reference - shape drift")
        out.append((m.group(0), r.group(1)))
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    for hexid, (winner_tree, expect) in MERGES.items():
        wpath = find_list(winner_tree, hexid)
        wtext = open(wpath, encoding="utf-8", newline="").read()
        wentries = entries(wtext)
        if not wentries:
            sys.exit(f"{hexid}: no entries parsed from winner")
        have = {fk for _, fk in wentries}

        atext = open(find_list("Apocalypse", hexid), encoding="utf-8", newline="").read()
        adds = [(b, fk) for b, fk in entries(atext)
                if fk.endswith(":" + APO) and fk not in have]
        if len(adds) != expect:
            sys.exit(f"{hexid}: expected {expect} Apocalypse additions, found {len(adds)}"
                     " - mod version or load order changed, re-derive")

        last = wentries[-1][0]
        idx = wtext.rindex(last) + len(last)
        merged = wtext[:idx] + "".join(b for b, _ in adds) + wtext[idx:]
        n = len(entries(merged))
        if n != len(wentries) + len(adds):
            sys.exit(f"{hexid}: merged count {n} != {len(wentries) + len(adds)}")

        dst = os.path.join(OUT, os.path.basename(wpath))
        with open(dst, "w", encoding="utf-8", newline="") as f:
            f.write(merged)
        print(f"{hexid}: {len(wentries)} winner + {len(adds)} Apocalypse -> {n}"
              f"  ({os.path.basename(wpath).split(' - ')[0]})")
    print("done - rebuild with build/build.ps1")


if __name__ == "__main__":
    main()
