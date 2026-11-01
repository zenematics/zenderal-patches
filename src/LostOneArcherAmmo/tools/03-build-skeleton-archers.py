"""Zenderal - Lost One Archer Ammo, part 3: skeleton archers ("Awoken Lost One") get something to shoot.

The winning mihailancientskeletons.esp is Lost Ones Revised's copy (it outranks the Ancient Skeletons mod's own). It
replaces the inventory of 11 skeleton archer records:
  - 7 carry Mihail's EAWO_LostOneBow (00463A) and ONE Old Iron Arrow (0028B0 x1): the arrow ran out in game (an
    Awoken Lost One was found with none), so they fired once and backed off;
  - 4 ghost archers (_20E_SkelettBogenGhost_*) carry a sword + shield skin and no bow or arrows at all.
Override = Mihail's record verbatim, with the lone arrow raised to 15 (his own count on his other archers) and, on the
ghosts, EGO's bow kit appended (Rune Bow 07C983 + 18 Old Rune Arrows 08659D, EGO's _20E_SkelettBogenGhost inventory).

Usage: python 03-build-skeleton-archers.py <serialized winning mihailancientskeletons.esp folder>
(reference/mods/mihailancientskeletons, serialized from mods/Lost Ones Revised/mihailancientskeletons.esp)."""
import os
import re
import sys

SRC = os.path.join(sys.argv[1], "Npcs")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "LostOneArcherAmmoESP", "Npcs")
LONE = ["- Item:", "    Item: 0028B0:Skyrim.esm", "    Count: 1"]
BOW_KIT = ["- Item:", "    Item: 07C983:Skyrim.esm", "    Count: 1", "- Item:", "    Item: 08659D:Skyrim.esm", "    Count: 18"]
EXPECT_ARROW, EXPECT_GHOST = 7, 4

os.makedirs(OUT, exist_ok=True)
arrow = ghost = 0
for f in sorted(os.listdir(SRC)):
    if "SkelettBogen" not in f:
        continue
    raw = open(os.path.join(SRC, f), "rb").read()
    nl = "\r\n" if b"\r\n" in raw else "\n"
    lines = raw.decode("utf-8").split(nl)
    items = [l.strip() for l in lines if l.startswith("    Item: ")]
    hits = [i for i in range(len(lines) - 2) if lines[i:i + 3] == LONE]
    if hits:
        assert len(hits) == 1, f
        lines[hits[0] + 2] = "    Count: 15"
        arrow += 1
    elif re.match(r"_20E_SkelettBogenGhost_", f) and not any(i.split()[1] in ("07C983:Skyrim.esm", "00463A:mihailancientskeletons.esp") for i in items):
        start = lines.index("Items:")
        end = start + 1
        while end < len(lines) and (lines[end].startswith("- ") or lines[end].startswith("  ")):
            end += 1
        lines[end:end] = BOW_KIT
        ghost += 1
    else:
        continue
    open(os.path.join(OUT, f), "wb").write(nl.join(lines).encode("utf-8"))
    print("override", f)
assert (arrow, ghost) == (EXPECT_ARROW, EXPECT_GHOST), (arrow, ghost)
print(f"wrote {arrow} arrow fixes + {ghost} ghost bow kits")
