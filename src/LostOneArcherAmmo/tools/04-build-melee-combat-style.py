"""Zenderal - Lost One Archer Ammo, part 4: shielded skeletons attack instead of holding their guard.

Ancient Skeletons (Mihail) rebuilds Enderal's sword skeletons (e.g. _10E_Skelett_Range1200 046EF1) with an iron sword and
an iron shield. Their combat style, csDraugrMelee 000D0D (EGO wins it; Enderal's own has the same flag), is Dueling: a
dueling NPC with a shield holds its block and waits for an opening, so in cramped ruins it stood blocking at 2 m for as
long as the player stayed, and in the open it attacked only now and then (reported 2026-10-24, ref 000E1248).
Override = EGO's record verbatim minus Dueling. It already has CantWait; offensive/defensive values are left as EGO set them.

Usage: python 04-build-melee-combat-style.py <serialized EGO folder>   (reference/mods/EGO)"""
import os
import sys

NAME = "csDraugrMelee - 000D0D_Skyrim.esm.yaml"
SRC = os.path.join(sys.argv[1], "CombatStyles", NAME)
HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "..", "LostOneArcherAmmoESP", "CombatStyles")

raw = open(SRC, "rb").read()
nl = "\r\n" if b"\r\n" in raw else "\n"
lines = raw.decode("utf-8").split(nl)

assert lines[0] == "FormKey: 000D0D:Skyrim.esm" and lines[2] == "EditorID: csDraugrMelee"
assert "- CantWait" in lines
assert lines.count("- Dueling") == 1
lines.remove("- Dueling")

os.makedirs(OUT_DIR, exist_ok=True)
open(os.path.join(OUT_DIR, NAME), "wb").write(nl.join(lines).encode("utf-8"))
print("wrote", NAME)
