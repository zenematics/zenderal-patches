"""Zenderal - Lost One Archer Ammo: Lost One archers fire one arrow and then back off and stare.

EGO gives their bows (Rune Bow 07C983, Silver Steel Bow 07C99D) the NPCsUseAmmo flag, so they spend the stack they
have equipped. Lost Ones Revised - EGO Patch, which wins these NPCs, adds one Old Iron Arrow (0028B0) x1 next to the
real 20-35 arrows; an archer that equips that lone arrow fires once and runs dry, and NPCs don't re-pick ammo in combat.

Every NPC in Lost Ones Revised - EGO Patch that carries 0028B0 x1 beside another ammo stack is copied verbatim minus
that one inventory entry. Nothing else changes (Lost Ones Revised's outfits, EGO's stats, UCR's visuals stay).

Usage: python 01-build-lost-one-archer-ammo.py <serialized Lost Ones Revised - EGO Patch folder>
(reference/mods/LostOnesRevisedEGOPatch, Spriggit 0.40.0)."""
import os
import shutil
import sys

SRC = os.path.join(sys.argv[1], "Npcs")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "LostOneArcherAmmoESP", "Npcs")
ENTRY = ["- Item:", "    Item: 0028B0:Skyrim.esm", "    Count: 1"]
EXPECTED = 8  # 2026-10-22: _20E/_25E/_28E_LostOne01Bow, two _Aggressive, _28E Respawn_Range1500, MQ16_LostOne02, DalGalarDeadServant15

if os.path.isdir(OUT):
    shutil.rmtree(OUT)
os.makedirs(OUT)
done = 0
for f in sorted(os.listdir(SRC)):
    raw = open(os.path.join(SRC, f), "rb").read()
    nl = b"\r\n" if b"\r\n" in raw else b"\n"
    lines = raw.decode("utf-8").split(nl.decode())
    hits = [i for i in range(len(lines) - 2) if lines[i:i + 3] == ENTRY]
    if not hits:
        continue
    assert len(hits) == 1, (f, "0028B0 x1 entry found more than once")
    i = hits[0]
    rest = lines[:i] + lines[i + 3:]
    assert sum(1 for l in rest if l.strip() == "Item: 0028B0:Skyrim.esm") == 0, f
    open(os.path.join(OUT, f), "wb").write(nl.decode().join(rest).encode("utf-8"))
    done += 1
    print("override", f)
assert done == EXPECTED, f"expected {EXPECTED} records, got {done}"
print("wrote", done, "overrides")
