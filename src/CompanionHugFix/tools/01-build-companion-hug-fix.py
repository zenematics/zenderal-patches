r"""Generate the Companion Hug Fix plugin YAML -- never hand-edit its Globals/.

Player report (Junebug, 2026-11-08): activating a companion (holding E near her) "randomly triggered a makeout
animation". Immersive Interactions' AR_QuestScript.ffriend plays the vanilla hug idle `pa_HugA 0F4699:Skyrim.esm` with
PlayIdleWithTarget when the player activates a follower (relationship rank 3: 1 in 15, when both AR_hugfollower and
AR_hugspouse are 1) or a lover (rank 4: 4 in 15, when AR_hugspouse is 1). In Enderal that IDLE sends `pa_HugB`, Enderal's
own romance clip `enderal\paired_hugb.hkx`, which EnderalPairedAnims made playable again under Pandora. So a Skyrim
friendly hug became an Enderal kiss scene with any companion.

This plugin is ImmersiveInteractions.esp's global `AR_hugspouse 04252B` verbatim with Data 1 -> 0 (asserted), the MCM's
"Hug Spouses and Followers" option, which gates both hug paths. Followers still salute (AR_hugfollower untouched).
Saves where the player toggled that MCM option keep their own value. Re-serialize ImmersiveInteractions.esp into
reference/mods/ImmersiveInteractions before re-running.
"""
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
NAME = "AR_hugspouse - 04252B_ImmersiveInteractions.esp.yaml"
SRC = os.path.join(ROOT, "reference", "mods", "ImmersiveInteractions", "Globals", NAME)
OUT = os.path.join(ROOT, "src", "CompanionHugFix", "CompanionHugFixESP", "Globals")

text = open(SRC, encoding="utf-8", newline="").read()
nl = "\r\n" if "\r\n" in text else "\n"
lines = text.split(nl)
idx = [i for i, l in enumerate(lines) if l == "Data: 1"]
if len(idx) != 1:
    raise SystemExit("expected exactly one 'Data: 1'")
lines[idx[0]] = "Data: 0"
os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, NAME), "w", encoding="utf-8", newline="") as f:
    f.write(nl.join(lines))
print("wrote", NAME, "(AR_hugspouse 1 -> 0)")
