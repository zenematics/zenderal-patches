r"""Reprice Gargoyles in Enderal's two summon spells for Magic Patches -- writes only `*_GargoylesInEnderal.esp.yaml`
files in MagicPatchesESP/Spells (deletes its own old ones first; never touches the other generators' files).

Player report (NickyBoy, 2026-11-05): Summon Gargoyle (tome in the Ark catacombs, `ArkTomb 1421B6`) costs 387 while
every other summon is far cheaper. GargoylesInEnderal.esp ports Dawnguard's Conjure Gargoyle untouched: ManualCostCalc,
BaseCost 160 (Summon Gargoyle 000830) and 240 (Summon Gargoyle Guardian 000875), no Arcane Fever. No plugin in the list
overrides either. The list's laddered Entropy summons (this plugin's Apocalypse/Triumvirate repricing, magic dataset
2026-10-15) sit at base ~100 for adept (median 100: Lich 107, Ravagor 104, Pit Fighter 100) and 94-256 for master.

New costs keep the mod's own 2:3 ratio: Summon Gargoyle 160 -> 100 (the adept median), Guardian 240 -> 150. Everything
else verbatim (ManualCostCalc, the vanilla half-cost perk, 60 s duration); no fever, like every other summon in the list.
Asserted: both spells still at 160 / 240. Re-serialize GargoylesInEnderal.esp into reference/mods/GargoylesInEnderal
before re-running.
"""
import glob
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "reference", "mods", "GargoylesInEnderal", "Spells")
OUT = os.path.join(ROOT, "src", "MagicPatches", "MagicPatchesESP", "Spells")
NEW = {"000830": (160, 100), "000875": (240, 150)}

for old in glob.glob(os.path.join(OUT, "*_GargoylesInEnderal.esp.yaml")):
    os.remove(old)
for fid, (was, now) in NEW.items():
    files = glob.glob(os.path.join(SRC, f"* - {fid}_GargoylesInEnderal.esp.yaml"))
    if len(files) != 1:
        raise SystemExit(f"{fid}: expected one source file, got {files}")
    text = open(files[0], encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in text else "\n"
    old_line, new_line = f"BaseCost: {was}{nl}", f"BaseCost: {now}{nl}"
    if text.count(old_line) != 1 or "- ManualCostCalc" not in text:
        raise SystemExit(f"{fid}: BaseCost is no longer {was} with ManualCostCalc")
    with open(os.path.join(OUT, os.path.basename(files[0])), "w", encoding="utf-8", newline="") as f:
        f.write(text.replace(old_line, new_line))
    print(f"{os.path.basename(files[0])}: BaseCost {was} -> {now}")
