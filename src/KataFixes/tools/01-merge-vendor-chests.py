#!/usr/bin/env python3
"""Merge the contested magic-vendor chests for Zenderal - Kata Fixes.esp.

Four mods add stock to the same three merchant chests and the last loader wins whole:
KataPUMBSpellPack (15 staves), Apocalypse - Magic of Skyrim (39-45 spell tomes),
xxOpenSpells (4 books), and the EGO SE Emberlord patch (5 entries). The actual winner
in the list is EGO SE - Leveling Redone, which carries NONE of them - so all of that
stock is silently dead in game.

This builds one override per chest: the WINNER's record copied verbatim (its trims and
gold changes are deliberate and must be forwarded - guardrail 5), with every loser's
additions re-appended. Additions are DERIVED, not hardcoded: an addition is an Items
entry in the loser's version of the chest whose FormKey suffix is the loser's own
plugin - the same definition an xEdit conflict view would use.

Chest 0465BB (_00E_Test_Container_Weapons) is deliberately NOT touched: it is a TEST
container players never see, and its winner (the EGO - KataPUMB Spell Package patch)
can keep its 5-stave version. Which means: before this patch, the staves' only
surviving location in the whole list was a test chest - they were 100% dead in game.

Inputs: the serialized reference trees (regenerate with /spriggit-decompile-reference):
  reference/mods/LevelingRedoneEGO   (EGO SE - Leveling Redone.esp - the winner)
  reference/mods/KataPUMB            (KataPUMBSpellPack.esp)
  reference/mods/Apocalypse          (Apocalypse - Magic of Skyrim.esp)
  reference/mods/xxOpenSpells        (xxOpenSpells.esp)
  reference/mods/KataEmberlord       (EGO SE - KataPUMB Spells - Emberlord sells all spells.esp)

Output: src/KataFixes/KataFixesESP/Containers/*.yaml. Asserts every count.
"""
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
REF = os.path.join(ROOT, "reference", "mods")
OUT = os.path.join(ROOT, "src", "KataFixes", "KataFixesESP", "Containers")

WINNER_TREE = "LevelingRedoneEGO"

# chest hex -> [(loser tree, loser plugin name, expected addition count)]
MERGES = {
    "102AD5": [  # _00E_Merchant_CCFunkentanz - Emberlord & Fireflash, Ark
        ("KataPUMB", "KataPUMBSpellPack.esp", 15),
        ("Apocalypse", "Apocalypse - Magic of Skyrim.esp", 45),
        ("xxOpenSpells", "xxOpenSpells.esp", 4),
        ("KataEmberlord", "EGO SE - KataPUMB Spells - Emberlord sells all spells.esp", 5),
    ],
    "118050": [  # _00E_Merchant_STTurious - Torius, Sun Temple
        ("KataPUMB", "KataPUMBSpellPack.esp", 15),
        ("Apocalypse", "Apocalypse - Magic of Skyrim.esp", 39),
    ],
    "05BCD6": [  # _00E_Merchant_FlusshaimTarhutieContainer - Tarhutie, Riverville
        ("KataPUMB", "KataPUMBSpellPack.esp", 15),
    ],
}

ENTRY_RE = re.compile(
    r"- Item:\r?\n    Item: ([0-9A-Fa-f]{6}:[^\r\n]+)\r?\n(?:    Count: [^\r\n]+\r?\n)?")


def find_chest(tree, hexid):
    d = os.path.join(REF, tree, "Containers")
    if not os.path.isdir(d):
        sys.exit(f"missing reference tree: {d} - run /spriggit-decompile-reference")
    for fn in os.listdir(d):
        if f" - {hexid}_Skyrim.esm.yaml" in fn:
            return os.path.join(d, fn)
    sys.exit(f"chest {hexid} not found in {tree}")


def entries(text):
    """[(full entry block, formkey)] for every Items entry."""
    return [(m.group(0), m.group(1)) for m in ENTRY_RE.finditer(text)]


def main():
    os.makedirs(OUT, exist_ok=True)
    for hexid, losers in MERGES.items():
        wpath = find_chest(WINNER_TREE, hexid)
        wtext = open(wpath, encoding="utf-8", newline="").read()
        wentries = entries(wtext)
        if not wentries:
            sys.exit(f"{hexid}: no Items parsed from winner - regex/shape drift")
        have = {fk for _, fk in wentries}

        additions = []
        for tree, plugin, expect in losers:
            ltext = open(find_chest(tree, hexid), encoding="utf-8", newline="").read()
            adds = [(block, fk) for block, fk in entries(ltext)
                    if fk.endswith(":" + plugin) and fk not in have]
            if len(adds) != expect:
                sys.exit(f"{hexid}: expected {expect} additions from {plugin}, found {len(adds)}"
                         " - load order or mod version changed, re-derive the table")
            additions.extend(adds)

        # append after the last existing entry, preserving the winner's record otherwise
        last_block = wentries[-1][0]
        idx = wtext.rindex(last_block) + len(last_block)
        merged = wtext[:idx] + "".join(b for b, _ in additions) + wtext[idx:]

        out_n = len(entries(merged))
        want = len(wentries) + len(additions)
        if out_n != want:
            sys.exit(f"{hexid}: merged entry count {out_n} != expected {want}")

        dst = os.path.join(OUT, os.path.basename(wpath))
        with open(dst, "w", encoding="utf-8", newline="") as f:
            f.write(merged)
        print(f"{hexid}: {len(wentries)} winner entries + {len(additions)} restored -> {out_n}"
              f"  ({os.path.basename(wpath).split(' - ')[0]})")
    print("done - rebuild with build/build.ps1")


if __name__ == "__main__":
    main()
