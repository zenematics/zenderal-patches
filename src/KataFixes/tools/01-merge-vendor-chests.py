#!/usr/bin/env python3
"""Merge the contested magic-vendor chests for Zenderal - Kata Fixes.esp.

Three mods add stock to the same three merchant chests and the last loader wins whole:
KataPUMBSpellPack (15 staves), xxOpenSpells (4 books), and the EGO SE Emberlord patch
(5 entries). Whatever the current load order makes the raw winner, the list's intended
resolution is EGO SE - Leveling Redone's BALANCE plus everyone's CONTENT:

  - Leveling Redone's record is the base. Its trims are deliberate leveling work (it
    cuts Funkentanz's spell books from EGO's 79 entries to 62), and every other
    overrider of these chests derives from EGO's lineage WITHOUT mastering Leveling
    Redone - their reverts of its trims are collateral, not decisions. Verified
    2026-08-27: the 18 base spell-book entries Emberlord "restores" at Funkentanz
    trace base -> FS -> EGO -> Emberlord with LR alone trimming them.
  - Each loser's OWN additions are re-appended. An addition is an Items entry whose
    FormKey suffix is the loser's own plugin - the same definition an xEdit conflict
    view would use. (Emberlord's 18 base-book carries are NOT additions by this rule,
    and that is correct: they are LR's trim seen through an older lineage.)

This plugin loads after every one of them, so the merge wins regardless of how the
upstream order shuffles - it moved once already (2026-08-20, the Kata block jumped
above Leveling Redone) without changing what the correct merged record is.

HISTORY: until 2026-08-27 this merged SEVEN chests, because Apocalypse - Magic of
Skyrim overrode six of them directly (160 tomes). Its v1.2.0 Enderal Patch moved all
vendor stock into Enderal's <Merchant>_CustomMerchandise hook lists and no longer
touches any container, so its four exclusive chests (Milbert 127928, Maxus 022BF2,
Barnabas 13824A, Ora 0F9320) are uncontested again and their overrides were DELETED -
keeping them would have double-stocked the tomes (chest entries + hook entries). The
CURATION stage (Apocalypse's 15 novice tomes copied to Tarhutie) went with it: the
hooks now sell every tome deterministically at exactly one shop, and upstream moved
the whole Apprentice tier to Tarhutie in Riverville, which covers the original
level-1-player rationale.

Chest 0465BB (_00E_Test_Container_Weapons) is deliberately NOT touched: it is a TEST
container players never see, and its winner (the EGO - KataPUMB Spell Package patch)
can keep its 5-stave version.

Inputs: the serialized reference trees (regenerate with /spriggit-decompile-reference):
  reference/mods/LevelingRedoneEGO   (EGO SE - Leveling Redone.esp - the balance base)
  reference/mods/KataPUMB            (KataPUMBSpellPack.esp)
  reference/mods/xxOpenSpells       (xxOpenSpells.esp)
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
        ("xxOpenSpells", "xxOpenSpells.esp", 4),
        ("KataEmberlord", "EGO SE - KataPUMB Spells - Emberlord sells all spells.esp", 5),
    ],
    "118050": [  # _00E_Merchant_STTurious - Torius, Sun Temple
        ("KataPUMB", "KataPUMBSpellPack.esp", 15),
    ],
    "05BCD6": [  # _00E_Merchant_FlusshaimTarhutieContainer - Tarhutie, Riverville
        ("KataPUMB", "KataPUMBSpellPack.esp", 15),
    ],
}

# Chests this plugin used to override and MUST NOT any more (see HISTORY above). The
# generator deletes a stale output file for these and fails if one reappears upstream.
RETIRED = {
    "127928": "_00E_Merchant_CCMilbert",
    "022BF2": "_00E_Merchant_MaxusTabbakus02",
    "13824A": "_00E_Merchant_UC_Barnabas",
    "0F9320": "_00E_Merchant_CCSteinschlag",
}

# Curated stock: chest hex -> [(source tree, source chest hex, selector name, expected count)].
# Unlike MERGES these entries were never in the destination chest under any plugin - we are
# choosing to sell them there. Empty since 2026-08-27 (see HISTORY above); the machinery
# stays because it is the shape a future list decision would use.
CURATION = {}

ENTRY_RE = re.compile(
    r"- Item:\r?\n    Item: ([0-9A-Fa-f]{6}:[^\r\n]+)\r?\n(?:    Count: [^\r\n]+\r?\n)?")

SELECTORS = {}


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

    # Guard the HISTORY invariant: the Apocalypse Enderal Patch must stay out of the chest
    # war. If a future version overrides containers again, this merge table is stale.
    apo_containers = os.path.join(REF, "Apocalypse", "Containers")
    if os.path.isdir(apo_containers):
        overridden = [fn for fn in os.listdir(apo_containers)
                      if not fn.endswith("_Apocalypse - Magic of Skyrim.esp.yaml")]
        if overridden:
            sys.exit("reference/mods/Apocalypse overrides foreign Containers again - it "
                     "re-entered the chest war; re-derive MERGES (and check for double-stock "
                     f"vs its hooks): {overridden}")

    # Retired chests: their overrides double-stock now. Delete stale output.
    for hexid, editorid in RETIRED.items():
        stale = [fn for fn in os.listdir(OUT) if f" - {hexid}_Skyrim.esm.yaml" in fn]
        for fn in stale:
            os.remove(os.path.join(OUT, fn))
            print(f"{hexid}: removed retired override {fn}")

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
