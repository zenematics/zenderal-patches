"""Port KataPUMB New Affinities' 24 extra affinities onto Enderal 2.1's _00E_AffinityControl.psc.

Enderal SE 2.1 moved the affinity system out of _00E_Game_SkillmenuSC (quest Levelsystem 010AA2, both
removed in 2.1) into _00E_AffinityControl, the alias script on FS quest AffinityControl 01597B. The
helpers (RegisterAffinity, TryUnlockAffinity, PerkTree_*Index) kept their names and signatures, so
Kata's three marked blocks drop in verbatim:
  1. registrations of affinities 21-44   (Kata: ";KATAPUMB EDITS" ... ";END KATAPUMB EDITS", 1st pair)
  2. their unlock rules                  (the 2nd pair)
  3. their index variables + properties  (";KATAPUMB" ... ";END KATAPUMB")
and every affinity array grows from 21 to 45. _GetScriptVersion() is left at 2.1's value, so
EnderalSE.dll's script-version check still passes.

Inputs: 2.1's source (papyrus-source/enderal-2.1.4.4) and Kata's _00e_game_skillmenusc.psc, which
ships inside KataPUMBAffinities.bsa (tools/02 extracts it). Output: Scripts/source/_00E_AffinityControl.psc.
"""
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
BASE = os.path.join(ROOT, "papyrus-source", "enderal-2.1.4.4", "source", "scripts", "_00e_affinitycontrol.psc")
KATA = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "src", "KataAffinities21", "build", "kata", "scripts", "source", "_00e_game_skillmenusc.psc")
OUT = os.path.join(ROOT, "src", "KataAffinities21", "Scripts", "source", "_00E_AffinityControl.psc")


def read(p):
    with open(p, encoding="cp1252", newline="") as f:
        return f.read().replace("\r\n", "\n")


def once(text, old, new, what):
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{what}: expected 1 match, found {n}")
    return text.replace(old, new)


base, kata = read(BASE), read(KATA)

blocks = re.findall(r"\t;KATAPUMB EDITS\n(.*?)\t;END KATAPUMB EDITS\n", kata, re.S)
if len(blocks) != 2:
    raise SystemExit(f"expected 2 ';KATAPUMB EDITS' blocks in Kata's script, found {len(blocks)}")
register, unlock = blocks
props = re.search(r"\n;KATAPUMB\n(.*?);END KATAPUMB\n", kata, re.S)
if not props:
    raise SystemExit("Kata's ';KATAPUMB' property block not found")
props = props.group(1)

n_reg = len(re.findall(r"= RegisterAffinity\(", register))
n_unl = len(re.findall(r"TryUnlockAffinity\(", unlock))
n_prop = len(re.findall(r"\bProperty\b", props))
if (n_reg, n_unl) != (24, 24):
    raise SystemExit(f"expected 24 registrations / 24 unlock rules, got {n_reg} / {n_unl}")

out = base
for decl in ("Spell", "Message", "Message"):
    pass
out = once(out, "    Affinity_Spells       = New Spell[21]\n    Affinity_Names_Male   = New Message[21]\n    Affinity_Names_Female = New Message[21]\n",
           "    Affinity_Spells       = New Spell[45]\n    Affinity_Names_Male   = New Message[45]\n    Affinity_Names_Female = New Message[45]\n", "affinity arrays")
out = once(out, "\t\taffinitiesUnlocked = new bool[21]\n", "\t\taffinitiesUnlocked = new bool[45]\n", "non-SKSE unlocked array")
out = once(out, "\t\tunlockedAffinityIndices = new int[21]\n", "\t\tunlockedAffinityIndices = new int[45]\n", "non-SKSE index array")

anchor = "\tAffinity_SoulcallerIndex        = RegisterAffinity(20, _00E_FS_Affinity_AbSoulcaller, _00E_FS_Game_Affinity_Soulcaller, _00E_FS_Game_Affinity_Soulcaller_Female)\n"
out = once(out, anchor, anchor + "\n\t;KATAPUMB NEW AFFINITIES (ported to 2.1 by Zenderal)\n" + register + "\t;END KATAPUMB\n", "registration anchor")

anchor = "    TryUnlockAffinity(PerkDistribution, Affinity_SoulcallerIndex, PerkTree_TheriantrophistIndex, PerkTree_PhasmalistIndex)\n"
out = once(out, anchor, anchor + "\n\t;KATAPUMB NEW AFFINITIES (ported to 2.1 by Zenderal)\n" + unlock + "\t;END KATAPUMB\n", "unlock anchor")

out = out.rstrip("\n") + "\n\n;KATAPUMB NEW AFFINITIES (ported to 2.1 by Zenderal)\n" + props + ";END KATAPUMB\n"

if "return 1\nendFunction" not in out.replace("    ", ""):
    raise SystemExit("_GetScriptVersion() no longer returns 1")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="cp1252", newline="\r\n") as f:
    f.write(out)
print(f"ported {n_reg} affinities, {n_unl} unlock rules, {n_prop} properties -> {OUT}")
