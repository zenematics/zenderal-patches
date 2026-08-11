#!/usr/bin/env python3
"""Audit reference/mods/ for stock one plugin adds and a LATER plugin silently deletes.

READ-ONLY. Reports; never writes. Run it before authoring any patch that touches a vendor
chest, an NPC inventory or a leveled list, and after any modlist change.

THE BUG IT FINDS. A Container's Items list and a LeveledItem's Entries list are not merged
by the engine - the last plugin to override the record supplies the whole list. So when mod
A adds 45 spell tomes to a merchant and unrelated mod B later overrides that same merchant
for its own reasons, A's 45 tomes are gone. Nothing warns you: both mods are installed, both
are enabled, the merchant exists and has stock, and the items simply are not in the game.
That is how 160 Apocalypse spell tomes were dead across seven chests in this list.

WHAT COUNTS AS AN ADDITION. Only entries whose FormKey suffix is the LOSER'S OWN plugin.
An entry carrying a master's suffix that the winner lacks is the winner deliberately TRIMMING
the master's stock - forwarding those would revert the winner's balance work (guardrail 5).
Leveling Redone trims heavily: it cuts Milbert from 91 entries to 33. Get this filter wrong
and a "restore the lost stock" patch quietly undoes a rebalance mod.

WHAT IT CANNOT SEE. Only what is serialized under reference/mods/. The list carries 300+
plugins; a conflict from one nobody has decompiled will not appear here. A silent report
means "none among the trees present", not "none".

Usage:  python src/KataFixes/tools/00-audit-vendor-conflicts.py [--all]
        --all also lists conflicts already handled by a Zenderal patch.
"""
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
REF = os.path.join(ROOT, "reference", "mods")
CONFIG = os.path.join(ROOT, ".claude", "config", "tools.json")

# Record types whose payload is a list the last override replaces wholesale.
LIST_TYPES = {
    "Containers": re.compile(
        r"- Item:\r?\n    Item: ([0-9A-Fa-f]{6}:[^\r\n]+?)\r?\n"),
    "LeveledItems": re.compile(
        r"- Data:\r?\n(?:    Level: [^\r\n]+\r?\n)?    Reference: ([0-9A-Fa-f]{6}:[^\r\n]+?)\r?\n"),
    "Npcs": re.compile(
        r"- Item:\r?\n    Item: ([0-9A-Fa-f]{6}:[^\r\n]+?)\r?\n"),
}


# Record hex -> why we are deliberately NOT restoring it. Keeps a real but intentional finding
# from reading as a to-do every time someone runs this.
DELIBERATE = {
    "0465BB": "test container players never see - the staves' pre-patch survival was here",
}


def load_order():
    """{plugin name lowercased: index} from the live MO2 profile's plugins.txt."""
    try:
        cfg = json.load(open(CONFIG, encoding="utf-8"))
    except OSError:
        sys.exit(f"no {CONFIG} - copy tools.example.json and fill it in (CLAUDE.md 'Tooling config')")
    path = os.path.join(cfg["modlistRoot"], "profiles", cfg["modlistProfile"], "plugins.txt")
    if not os.path.isfile(path):
        sys.exit(f"no load order at {path} - check modlistRoot/modlistProfile in tools.json")
    order = {}
    for line in open(path, encoding="utf-8-sig"):
        line = line.strip()
        if line and not line.startswith("#"):
            order.setdefault(line.lstrip("*").lower(), len(order))
    return order


def plugin_roots():
    """{plugin name: serialized tree root} for every plugin under reference/mods/."""
    roots = {}
    for dirpath, _, files in os.walk(REF):
        if "RecordData.yaml" not in files:
            continue
        text = open(os.path.join(dirpath, "RecordData.yaml"), encoding="utf-8", newline="").read()
        m = re.search(r"^ModKey: ([^\r\n]+?)\r?$", text, re.M)
        if m:
            roots[m.group(1)] = dirpath
    return roots


def main():
    show_all = "--all" in sys.argv
    order = load_order()
    roots = plugin_roots()
    if not roots:
        sys.exit(f"no serialized plugins under {REF} - run /spriggit-decompile-reference")

    unplaced = [p for p in roots if p.lower() not in order]
    if unplaced:
        print(f"note: not in the live load order, skipped: {', '.join(sorted(unplaced))}\n")

    # (type, record filename) -> {plugin: path}
    records = {}
    for plugin, root in roots.items():
        if plugin.lower() not in order:
            continue
        for rtype in LIST_TYPES:
            d = os.path.join(root, rtype)
            if not os.path.isdir(d):
                continue
            for fn in os.listdir(d):
                if fn.endswith(".yaml"):
                    records.setdefault((rtype, fn), {})[plugin] = os.path.join(d, fn)

    # What our own patches already override, so handled conflicts can be filtered out.
    ours = set()
    for dirpath, _, files in os.walk(os.path.join(ROOT, "src")):
        rtype = os.path.basename(dirpath)
        if rtype in LIST_TYPES:
            ours.update((rtype, fn) for fn in files if fn.endswith(".yaml"))

    findings, handled = [], 0
    for (rtype, fn), byplugin in sorted(records.items()):
        if len(byplugin) < 2:
            continue
        winner = max(byplugin, key=lambda p: order[p.lower()])
        entry_re = LIST_TYPES[rtype]
        kept = set(entry_re.findall(open(byplugin[winner], encoding="utf-8", newline="").read()))
        for loser, path in byplugin.items():
            if loser == winner:
                continue
            lost = [fk for fk in entry_re.findall(open(path, encoding="utf-8", newline="").read())
                    if fk.endswith(":" + loser) and fk not in kept]
            if not lost:
                continue
            hexid = re.search(r" - ([0-9A-F]{6})_", fn)
            skip = (rtype, fn) in ours or (hexid and hexid.group(1) in DELIBERATE)
            if skip:
                handled += 1
                if not show_all:
                    continue
            findings.append((rtype, fn, loser, winner, len(lost), skip))

    if not findings:
        print(f"no unhandled conflicts across {len(records)} records"
              f" ({handled} already covered by a Zenderal patch)")
        return
    print(f"{'TYPE':<14} {'RECORD':<46} {'LOST BY':<34} {'DELETED BY':<30} N")
    for rtype, fn, loser, winner, n, done in sorted(findings, key=lambda r: -r[4]):
        hexid = re.search(r" - ([0-9A-F]{6})_", fn)
        mark = ""
        if done:
            why = DELIBERATE.get(hexid.group(1) if hexid else "")
            mark = f"  [deliberate: {why}]" if why else "  [already patched]"
        print(f"{rtype:<14} {fn.split(' - ')[0][:45]:<46} {loser[:33]:<34} {winner[:29]:<30} {n}{mark}")
    print(f"\n{sum(n for *_, n, done in findings if not done)} entries lost across"
          f" {len({(t, f) for t, f, _, _, _, d in findings if not d})} records."
          " Each is stock the player can never obtain.")
    print("Fix by overriding the record with the WINNER's version plus the losers' own entries -"
          " see src/KataFixes/tools/01-merge-vendor-chests.py.")


if __name__ == "__main__":
    main()
