"""Zenderal - Lost One Archer Ammo, part 2: Lost One / skeleton archers keep shooting instead of backing off and staring.

58 winning undead archer NPCs use csDraugrMissile 038A23 (EGO wins it). Unlike every draugr melee style it lacks the
CantWait record flag, so the combat AI may drop into 'wait' (hold position and watch); with Dueling on and EGO's raised
fallback (0.2 -> 0.35) an archer fires, backs off and stares. Override = EGO's record verbatim with:
  CantWait added, Dueling removed, FallbackMult 0, CircleMult 0.05, AvoidThreatChance 0, OffensiveMult 1.0,
  LongRangeStrafeMult 0.1.
Melee draugr styles (000D0D, 072DF6, 072DF7) are left alone.

Usage: python 02-build-archer-combat-style.py <serialized EGO folder>   (reference/mods/EGO)"""
import os
import sys

NAME = "csDraugrMissile - 038A23_Skyrim.esm.yaml"
SRC = os.path.join(sys.argv[1], "CombatStyles", NAME)
HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "..", "LostOneArcherAmmoESP", "CombatStyles")

raw = open(SRC, "rb").read()
nl = "\r\n" if b"\r\n" in raw else "\n"
lines = raw.decode("utf-8").split(nl)


def set_line(old, new):
    n = lines.count(old)
    assert n == 1, (old, n)
    lines[lines.index(old)] = new


# Written in Spriggit's canonical form so the source round-trips: CantWait is record-header bit 0x80000
# (MajorRecordFlagsRaw 524288, echoed as SkyrimMajorRecordFlags/MajorFlags like EGO's melee draugr styles),
# and fields set to 0 are omitted.
assert lines[0] == "FormKey: 038A23:Skyrim.esm" and lines[1] == "EditorID: csDraugrMissile"
assert "SkyrimMajorRecordFlags:" not in lines and "MajorFlags:" not in lines
lines[1:1] = ["MajorRecordFlagsRaw: 524288"]
lines[3:3] = ["SkyrimMajorRecordFlags:", "- CantWait"]
set_line("OffensiveMult: 0.8", "OffensiveMult: 1")
lines.remove("AvoidThreatChance: 0.2")
set_line("  CircleMult: 0.3", "  CircleMult: 0.05")
lines.remove("  FallbackMult: 0.35")
set_line("LongRangeStrafeMult: 0.25", "LongRangeStrafeMult: 0.1")
assert lines.count("- Dueling") == 1
lines.remove("- Dueling")
while lines and lines[-1] == "":
    lines.pop()
lines += ["MajorFlags:", "- AllowDualWielding", ""]

os.makedirs(OUT_DIR, exist_ok=True)
open(os.path.join(OUT_DIR, NAME), "wb").write(nl.join(lines).encode("utf-8"))
print("wrote", NAME)
