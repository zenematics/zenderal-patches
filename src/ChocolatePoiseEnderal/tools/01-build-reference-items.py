#!/usr/bin/env python3
"""Give Chocolate Poise - Reforged the reference items it looks for, so poise works in Enderal.

Why: ChocolatePoiseReforged.dll (v4.0.0) scales every hit's poise damage against reference
equipment it fetches BY VANILLA EDITORID at startup (HitEventHandler::InitializeEquipmentCache):
  IronDagger / DaedricWarhammer                  weapon damage min / max
  ArmorHideGauntlets / ArmorDaedricGauntlets     gauntlet armor min / max
  ArmorHideShield / ArmorDaedricShield           shield armor min / max
  ArmorDaedricCuirass / Helmet / Boots / ...     MaxArmorRating (EffectiveReference)
None of these EditorIDs exist in Enderal (its Skyrim.esm is base Enderal), so every lookup
logged NULL, EffectiveReference = 0, and a debug run (2026-10-05) logged Final Poise Damage
0.00 on all 65 hits in both directions: poise was dead list-wide, which also made For Honor
Reforged's "parry breaks poise -> knockdown" unreachable.

Fix: NEW, unplaced, unlisted records carrying exactly those EditorIDs (po3 Tweaks' editorID
cache makes them findable), each a verbatim copy of the Enderal item that plays the vanilla
item's role - common-tier weakest for "min", top standard tier for "max", no uniques. Source
= the live record (EGO's YAML where EGO overrides it, else FS, else base Enderal). Only the
FormKey and EditorID change; names are collapsed to one English value (plugin not Localized).
Nothing references these records, so they can never appear in game.

Output: src/ChocolatePoiseEnderal/ChocolatePoiseEnderalESP/{Weapons,Armors}/ (regenerated)
"""
import glob
import os
import re
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
REF = os.path.join(ROOT, "reference")
OUT = os.path.join(ROOT, "src", "ChocolatePoiseEnderal", "ChocolatePoiseEnderalESP")
PLUGIN = "Zenderal - Chocolate Poise Enderal Fix.esp"

# (new FormID, vanilla EditorID CPR looks up, group, Enderal source FormKey)
ITEMS = [
    (0x800, "IronDagger",            "Weapons", "0028D2:Skyrim.esm"),  # _01E_02_IronDagger, 3 dmg
    (0x801, "DaedricWarhammer",      "Weapons", "07C993:Skyrim.esm"),  # _04E_31Aeternaschlachthammer, 42
    (0x802, "ArmorHideGauntlets",    "Armors",  "01CBFB:Skyrim.esm"),  # _01E_05_LeatherArmProtectors
    (0x803, "ArmorDaedricGauntlets", "Armors",  "033EB9:Skyrim.esm"),  # _50E_HSet_SkybreakerGauntlets
    (0x804, "ArmorHideShield",       "Armors",  "0030CB:Skyrim.esm"),  # _01E_05_LeatherShield
    (0x805, "ArmorDaedricShield",    "Armors",  "138270:Skyrim.esm"),  # _04E_30Wegeslosenschild
    (0x806, "ArmorDaedricCuirass",   "Armors",  "033EB7:Skyrim.esm"),  # _50E_HSet_SkybreakerCuirass
    (0x807, "ArmorDaedricHelmet",    "Armors",  "150398:Skyrim.esm"),  # _50E_HSet_SkybreakerHelmet
    (0x808, "ArmorDaedricBoots",     "Armors",  "033EB5:Skyrim.esm"),  # _50E_HSet_SkybreakerBoots
]
# winner order: later trees override earlier ones
TREES = [os.path.join(REF, "base", "Skyrim"), os.path.join(REF, "base", "EnderalFS"), os.path.join(REF, "mods", "EGO")]


def find(group, fk):
    hit = None
    for t in TREES:
        for f in glob.glob(os.path.join(t, group, "*.yaml")):
            if open(f, encoding="utf-8").readline().strip() == f"FormKey: {fk}":
                hit = f
    if not hit:
        sys.exit(f"{fk} not found in {group}")
    return hit


def collapse_name(text):
    m = re.search(r"^Name:\n  TargetLanguage: English\n  Values:\n((?:  - .*\n(?:    .*\n)*)+)", text, re.M)
    if not m:
        return text
    eng = re.search(r"Language: English\n    String: (.*)", m.group(1)).group(1)
    text = text[:m.start()] + f"Name:\n  TargetLanguage: English\n  Value: {eng}\n" + text[m.end():]
    # a localized record's empty Description has no value line; non-localized Spriggit writes Value: ''
    return re.sub(r"^(Description:\n  TargetLanguage: English\n)(?!  Value)", r"\1  Value: ''\n", text, flags=re.M)


def main():
    for g in ("Weapons", "Armors"):
        shutil.rmtree(os.path.join(OUT, g), ignore_errors=True)
        os.makedirs(os.path.join(OUT, g))
    for fid, eid, group, src in ITEMS:
        path = find(group, src)
        t = open(path, encoding="utf-8").read().replace("\r\n", "\n")
        old_eid = re.search(r"^EditorID: (.+)$", t, re.M).group(1)
        t, n1 = re.subn(r"^FormKey: .+$", f"FormKey: {fid:06X}:{PLUGIN}", t, count=1, flags=re.M)
        t, n2 = re.subn(r"^EditorID: .+$", f"EditorID: {eid}", t, count=1, flags=re.M)
        if (n1, n2) != (1, 1):
            sys.exit(f"{src}: FormKey/EditorID not replaced")
        t = collapse_name(t)
        if "  Values:" in t.split("\nDescription:")[0]:
            sys.exit(f"{src}: Name still multi-language")
        out = os.path.join(OUT, group, f"{eid} - {fid:06X}_{PLUGIN}.yaml")
        open(out, "w", encoding="utf-8", newline="\n").write(t)
        stat = re.search(r"^  Damage: (\S+)", t, re.M) or re.search(r"^ArmorRating: (\S+)", t, re.M)
        print(f"{eid:<22} <- {old_eid:<36} {stat.group(1) if stat else '?'}  ({os.path.relpath(path, REF).split(os.sep)[1]})")

    # NOTE: do NOT try to supply ForceFullBodyStagger here. CPR looks it up by vanilla FormID
    # 0x10CED7, which in Enderal is a placed REFR (cell QKerker) - a FACT at that ID collides
    # with a live record of another type. See CLAUDE.md.
    shutil.rmtree(os.path.join(OUT, "Factions"), ignore_errors=True)
    print(f"OK: {len(ITEMS)} reference items")


if __name__ == "__main__":
    main()
