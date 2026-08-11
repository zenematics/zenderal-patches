#!/usr/bin/env python3
"""Merge the contested magic-vendor chests for Zenderal - Kata Fixes.esp.

Four mods add stock to the same seven merchant chests and the last loader wins whole:
KataPUMBSpellPack (15 staves), Apocalypse - Magic of Skyrim (14-45 spell tomes per
chest, 160 in total), xxOpenSpells (4 books), and the EGO SE Emberlord patch (5
entries). The actual winner of all seven in the list is EGO SE - Leveling Redone
(load order 166, vs Apocalypse's 125), which carries NONE of them - so all of that
stock is silently dead in game.

The seven are every container Leveling Redone overrides that anyone else adds stock to;
that set was swept, not guessed, and it is complete as of 2026-08-11 for the mods we
have serialized under reference/mods/.

This builds one override per chest: the WINNER's record copied verbatim (its trims and
gold changes are deliberate and must be forwarded - guardrail 5), with every loser's
additions re-appended. Additions are DERIVED, not hardcoded: an addition is an Items
entry in the loser's version of the chest whose FormKey suffix is the loser's own
plugin - the same definition an xEdit conflict view would use.

A second, separate stage adds CURATED stock - entries no upstream mod ever put in that
chest, which we place there as a list decision. Currently one: Apocalypse's 15 novice
spell tomes at Tarhutie in Riverville. Apocalypse hosts its novice tier at Milbert in
Ark only, and Riverville is where a level-1 player actually is, so its spell merchant
sold no novice Apocalypse magic at all. These are DERIVED too - lifted verbatim from
Apocalypse's own Milbert chest and cross-checked against the WB_<school>000_ tome
naming - so an Apocalypse update that changes the novice set flows through.

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
    "127928": [  # _00E_Merchant_CCMilbert - Milbert Foxhand, Ark (Apocalypse's novice tier)
        ("Apocalypse", "Apocalypse - Magic of Skyrim.esp", 15),
    ],
    "022BF2": [  # _00E_Merchant_MaxusTabbakus02 - Duneville (Apocalypse's apprentice tier)
        ("Apocalypse", "Apocalypse - Magic of Skyrim.esp", 28),
    ],
    "13824A": [  # _00E_Merchant_UC_Barnabas - Undercity (Apocalypse's adept Alt/Conj/Destr)
        ("Apocalypse", "Apocalypse - Magic of Skyrim.esp", 19),
    ],
    "0F9320": [  # _00E_Merchant_CCSteinschlag - Ora Stonehand, Ark (adept Illus/Restor)
        ("Apocalypse", "Apocalypse - Magic of Skyrim.esp", 14),
    ],
}

# Curated stock: chest hex -> [(source tree, source chest hex, selector name, expected count)].
# Unlike MERGES these entries were never in the destination chest under any plugin - we are
# choosing to sell them there. The source chest is only the place we copy the entry block from.
CURATION = {
    "05BCD6": [  # Tarhutie, Riverville - first town, first spell merchant a new player meets
        ("Apocalypse", "127928", "apocalypse_novice_tomes", 15),  # 127928 = Milbert, Ark
    ],
}

ENTRY_RE = re.compile(
    r"- Item:\r?\n    Item: ([0-9A-Fa-f]{6}:[^\r\n]+)\r?\n(?:    Count: [^\r\n]+\r?\n)?")

# Apocalypse book EditorIDs encode school letter + minimum skill level: WB_D000_Blaze_Book is
# Destruction at skill 0. 000 is the novice tier; 025/050/075/100 are the tiers above it.
APO_BOOK_RE = re.compile(r"^WB_(?P<school>[ACDIR])(?P<tier>\d{3})_")


def apocalypse_novice_tomes():
    """FormKeys of every Apocalypse spell tome whose spell is novice tier (skill 0).

    Read off the Books folder rather than listed here, so an Apocalypse update that adds or
    retires a novice tome changes this set instead of silently disagreeing with it.
    """
    d = os.path.join(REF, "Apocalypse", "Books")
    if not os.path.isdir(d):
        sys.exit(f"missing reference tree: {d} - run /spriggit-decompile-reference")
    found, per_school = {}, {}
    for fn in os.listdir(d):
        m = APO_BOOK_RE.match(fn)
        if not m or m.group("tier") != "000":
            continue
        fk = re.search(r"^FormKey: ([0-9A-Fa-f]{6}:[^\r\n]+?)\r?$",
                       open(os.path.join(d, fn), encoding="utf-8", newline="").read(), re.M)
        if not fk:
            sys.exit(f"no FormKey in {fn} - Spriggit shape drift")
        found[fk.group(1)] = fn
        per_school[m.group("school")] = per_school.get(m.group("school"), 0) + 1
    # Apocalypse ships 3 novice tomes in each of the five schools. A school missing from this
    # tally means the naming convention drifted and the selector is quietly under-selecting.
    if sorted(per_school) != ["A", "C", "D", "I", "R"]:
        sys.exit(f"novice tomes: expected all five schools, got {sorted(per_school)}")
    return found


SELECTORS = {"apocalypse_novice_tomes": apocalypse_novice_tomes}


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
        restored = len(additions)

        for tree, src_hex, selector, expect in CURATION.get(hexid, []):
            wanted = SELECTORS[selector]()
            stext = open(find_chest(tree, src_hex), encoding="utf-8", newline="").read()
            adds = [(block, fk) for block, fk in entries(stext)
                    if fk in wanted and fk not in have]
            if len(adds) != expect:
                missing = sorted(wanted[fk] for fk in wanted
                                 if fk not in {f for _, f in adds} and fk not in have)
                sys.exit(f"{hexid}: expected {expect} curated entries via {selector} from"
                         f" {tree}/{src_hex}, found {len(adds)} - not sourced: {missing}")
            additions.extend(adds)
        curated = len(additions) - restored

        # append after the last existing entry, preserving the winner's record otherwise
        last_block = wentries[-1][0]
        idx = wtext.rindex(last_block) + len(last_block)
        merged = wtext[:idx] + "".join(b for b, _ in additions) + wtext[idx:]

        out_n = len(entries(merged))
        want = len(wentries) + len(additions)
        if out_n != want:
            sys.exit(f"{hexid}: merged entry count {out_n} != expected {want}")
        if len({fk for _, fk in entries(merged)}) != out_n:
            sys.exit(f"{hexid}: duplicate Items entry in merged record")

        dst = os.path.join(OUT, os.path.basename(wpath))
        with open(dst, "w", encoding="utf-8", newline="") as f:
            f.write(merged)
        print(f"{hexid}: {len(wentries)} winner entries + {restored} restored"
              f" + {curated} curated -> {out_n}"
              f"  ({os.path.basename(wpath).split(' - ')[0]})")
    print("done - rebuild with build/build.ps1")


if __name__ == "__main__":
    main()
