r"""Generate the Male Tunic Fix plugin YAML -- never hand-edit its ArmorAddons/.

Player report (cptflame, 2026-11-07): in Forgotten Homeland Part 1 (MQ13a) a male character is given a "female" tunic.
SureAI's _00E_MQ13a_Functions (lines 321 and 474) equips the player with _00E_Mining_FineClothesF_GreenA 13803C
("Tunic") and ClothesJarlShoes, whatever their sex. Base Enderal's addon _00E_Mining_FineClothesF_Green_AA 138036
gives men plain miner's clothes (Clothes\MinerClothes\MinerClothesm_1.nif); Pretty Enderal Clothing (its only and
last overrider) points both sexes at Kilean's Dancer outfit (Enderal\Clothes\Kilean\Dancer\Green_m_1.nif / Green_1.nif),
a dancer's costume that reads as women's clothing on a man.

This plugin is Pretty's 138036 verbatim with only the MALE world and first-person models back to base Enderal's
(asserted: Pretty's male paths are the Dancer ones, base's are the miner ones). Women keep Pretty's dancer tunic.
Re-serialize Pretty Enderal Clothing into reference/mods/Pretty before re-running.
"""
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
NAME = "_00E_Mining_FineClothesF_Green_AA - 138036_Skyrim.esm.yaml"
PRETTY = os.path.join(ROOT, "reference", "mods", "Pretty", "Pretty Enderal Clothing", "ArmorAddons", NAME)
BASE = os.path.join(ROOT, "reference", "base-2.1.4.4", "Skyrim", "ArmorAddons", NAME)
OUT = os.path.join(ROOT, "src", "MaleTunicFix", "MaleTunicFixESP", "ArmorAddons")


def read(p):
    return open(p, encoding="utf-8", newline="").read()


def male_file(text, block):
    m = re.search(rf"^{block}:\r?\n  Male:\r?\n    File: (.+?)\r?$", text, re.M)
    if not m:
        raise SystemExit(f"no {block} male model")
    return m


pretty, base = read(PRETTY), read(BASE)
for block, want_pretty, want_base in (
        ("WorldModel", r"Enderal\Clothes\Kilean\Dancer\Green_m_1.nif", r"Clothes\MinerClothes\MinerClothesm_1.nif"),
        ("FirstPersonModel", r"Enderal\Clothes\Kilean\Dancer\Green_m_1.nif",
         r"Clothes\MinerClothes\1stPersonMinerClothesm_1.nif")):
    p, b = male_file(pretty, block), male_file(base, block)
    if p.group(1) != want_pretty or b.group(1) != want_base:
        raise SystemExit(f"{block}: Pretty {p.group(1)} / base {b.group(1)} are not the expected paths")
    pretty = pretty[:p.start(1)] + want_base + pretty[p.end(1):]
os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, NAME), "w", encoding="utf-8", newline="") as f:
    f.write(pretty)
print("wrote", NAME, "(male models back to base Enderal's miner tunic)")
