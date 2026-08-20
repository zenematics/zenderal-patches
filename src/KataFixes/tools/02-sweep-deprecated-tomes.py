#!/usr/bin/env python3
"""Sweep every winning container / leveled list / NPC inventory for spell tomes
that teach an EGO-DEPRECATED spell.

READ-ONLY. Reports; never writes. Run it after any modlist or load-order change,
alongside 00-audit-vendor-conflicts.py. The two are complementary:

  00-audit  finds a WINNER silently DELETING a loser's stock.
  02-sweep  finds a WINNER still HANDING OUT deprecated content.

THE BUG IT FINDS. EGO deprecates ~38 base-Enderal/FS spells by renaming them
`*unused` and setting their description to "This spell is no longer used in the
'Gameplay Overhaul'...". It removes the tomes teaching them from its own chest
and list overrides - but any OTHER plugin whose override of those records was
built from the base/FS version carries the dead tomes straight back in. That is
exactly how the 2026-08-20 bug report happened: the rebuilt Apocalypse's chest
overrides (copied from base Enderal) put _05E_SpellBookFireBall,
_05E_SpellBookChainLightning and _05E_SpellBookFrostwind back on Ora Stonehand,
Gabrielle and Torius, and a load-order flip (Apocalypse moved from 125 to 291,
above Leveling Redone) made those overrides win wherever no Zenderal patch
covered the chest. The player sees "Spell Tome: Fire Ball" whose description
reads "no longer used in the Gameplay Overhaul".

HOW IT DECIDES. Everything is judged on the WINNING version under the live
plugins.txt, across every serialized tree it can find (reference/base/,
reference/mods/, and this repo's src/ plugins):
  1. toxic spell  = winning SPEL record's description contains "no longer used"
  2. toxic book   = winning BOOK record Teaches a toxic spell
  3. live hit     = winning Container/LeveledItem/Npc record references a toxic book
Loser-only carriers (blocked by a later winner) are informational; show them
with --all to see which Zenderal merges are load-bearing.

WHAT IT CANNOT SEE. (a) Only serialized trees - a non-serialized plugin that
overrides a container is invisible, so a clean report means "none among the
trees present", not "none". (b) World-PLACED tomes: ~20 base-Enderal dungeon
cells place these books as REFRs (ArkTomb, Felsenwacht, Old Dothulgrad, ...)
and EGO overrides none of those refs. That is upstream EGO-on-Enderal
behaviour, present in any EGO install, and out of scope here - whether EGO's
BSA-packed scripts clean the learned spell up at runtime is unverified.

Usage:  python src/KataFixes/tools/02-sweep-deprecated-tomes.py [--all]
        --all also lists blocked loser-only carriers and the full toxic sets.

RUNTIME NOTE (2026-08-21). On the dev machine this takes ~9 minutes of wall
time while using <1s of CPU - the identical workload driven through importlib
finishes in under a second, and a verbatim copy run from a temp folder is just
as slow, so it is not the code path and not the file's location. Root cause
undiagnosed (environmental; suspect AV/filesystem-filter interference). The
output has been validated against a known-good independent run three times.
"""
import json
import os
import re
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
CONFIG = os.path.join(ROOT, ".claude", "config", "tools.json")
TREE_PARENTS = [
    os.path.join(ROOT, "reference", "base"),
    os.path.join(ROOT, "reference", "mods"),
    os.path.join(ROOT, "src"),
]

# Same entry shapes as 00-audit-vendor-conflicts.py - anchored so a stray
# "Item:" in some other field cannot false-positive.
LIST_TYPES = {
    "Containers": re.compile(
        r"- Item:\r?\n    Item: ([0-9A-Fa-f]{6}:[^\r\n]+?)\r?\n"),
    "LeveledItems": re.compile(
        r"- Data:\r?\n(?:    Level: [^\r\n]+\r?\n)?    Reference: ([0-9A-Fa-f]{6}:[^\r\n]+?)\r?\n"),
    "Npcs": re.compile(
        r"- Item:\r?\n    Item: ([0-9A-Fa-f]{6}:[^\r\n]+?)\r?\n"),
}

# Record hex -> why a live hit there is fine. Keeps a real but intentional
# finding from reading as a to-do every time someone runs this.
DELIBERATE = {
    "0465AE": "SureAI test container (_00E_Test_Container_Book) players never see",
}

FK = re.compile(r"^FormKey: ([0-9A-Fa-f]{6}):([^\r\n]+?)\r?$", re.M)
EDID = re.compile(r"^EditorID: ([^\r\n]+?)\r?$", re.M)
TEACH = re.compile(r"^Teaches:\r?\n(?:.+\r?\n)*?\s+Spell: ([0-9A-Fa-f]{6}):([^\r\n]+?)\r?$", re.M)


def load_order():
    """{plugin name lowercased: index} from the live MO2 profile's loadorder.txt.

    NOT plugins.txt: that file omits the implicit base masters, so keying on it
    silently drops Skyrim.esm - which in Enderal is BASE ENDERAL, the tree most
    of the deprecated tomes and their host containers actually live in.
    """
    try:
        cfg = json.load(open(CONFIG, encoding="utf-8"))
    except OSError:
        sys.exit(f"no {CONFIG} - copy tools.example.json and fill it in (CLAUDE.md 'Tooling config')")
    path = os.path.join(cfg["modlistRoot"], "profiles", cfg["modlistProfile"], "loadorder.txt")
    if not os.path.isfile(path):
        sys.exit(f"no load order at {path} - check modlistRoot/modlistProfile in tools.json")
    order = {}
    for line in open(path, encoding="utf-8-sig"):
        line = line.strip()
        if line and not line.startswith("#"):
            order.setdefault(line.lower(), len(order))
    return order


def plugin_roots():
    """{plugin name: tree root} for every serialized tree under TREE_PARENTS.

    A tree root is marked by spriggit-meta.json, which exists ONLY at the root.
    Do not key on RecordData.yaml - every serialized cell folder has one, so a
    naive walk opens tens of thousands of files under reference/base/Skyrim.
    """
    roots = {}
    for parent in TREE_PARENTS:
        if not os.path.isdir(parent):
            continue
        for dirpath, dirs, files in os.walk(parent):
            if "spriggit-meta.json" not in files:
                continue
            dirs[:] = []  # a root never nests another root - stop descending
            if "RecordData.yaml" not in files:
                continue
            text = open(os.path.join(dirpath, "RecordData.yaml"),
                        encoding="utf-8", newline="").read()
            m = re.search(r"^ModKey: ([^\r\n]+?)\r?$", text, re.M)
            if m:
                # Two trees of the same plugin (e.g. a stub next to the real
                # thing) would be a setup error worth hearing about.
                if m.group(1) in roots:
                    print(f"note: duplicate tree for {m.group(1)}: "
                          f"{roots[m.group(1)]} and {dirpath} - keeping the first",
                          file=sys.stderr)
                    continue
                roots[m.group(1)] = dirpath
    return roots


def formkey(text):
    m = FK.search(text)
    return (m.group(1).upper() + ":" + m.group(2)) if m else None


def edid(text, default="?"):
    m = EDID.search(text)
    return m.group(1) if m else default


# "<EditorID> - <hex>_<master>.yaml", or "<hex>_<master>.yaml" when the record
# has no EditorID. The EditorID half can differ between versions (EGO renames
# deprecated spells to *unused), so group by the (hex, master) tail only.
FNKEY = re.compile(r"([0-9A-Fa-f]{6})_(.+)\.yaml$")


def collect_winners(roots, order, group, read_losers=True):
    """({formkey: (plugin, text)}, {formkey: [(plugin, text)]}) for `group`.

    Versions are indexed by FILENAME so only the files that matter get opened:
    winners always, losers only where the record is contested (and only when
    read_losers). Reads go through a thread pool because per-file open cost
    dominates on this machine (~35ms each under Defender) - serially the sweep
    took ~9 minutes for ~16k files.
    """
    versions = defaultdict(list)
    for plugin, root in roots.items():
        rank = order.get(plugin.lower())
        if rank is None:
            continue
        d = os.path.join(root, group)
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            m = FNKEY.search(fn)
            if m:
                fk = m.group(1).upper() + ":" + m.group(2)
                versions[fk].append((rank, plugin, os.path.join(d, fn)))
    to_read = []   # (fk, plugin, path, is_winner)
    for fk, vs in versions.items():
        vs.sort(key=lambda v: v[0])
        to_read.append((fk, vs[-1][1], vs[-1][2], True))
        if read_losers:
            to_read.extend((fk, p, path, False) for _, p, path in vs[:-1])
    with ThreadPoolExecutor(max_workers=16) as pool:
        texts = pool.map(
            lambda job: open(job[2], encoding="utf-8", newline="").read(), to_read)
        winners = {}
        losers = defaultdict(list)
        for (fk, plugin, _, is_winner), text in zip(to_read, texts):
            if is_winner:
                winners[fk] = (plugin, text)
            else:
                losers[fk].append((plugin, text))
    return winners, losers


def main():
    show_all = "--all" in sys.argv
    order = load_order()
    roots = plugin_roots()
    if not roots:
        sys.exit("no serialized trees found - run /spriggit-decompile-reference")
    unplaced = sorted(p for p in roots if p.lower() not in order)
    if unplaced:
        print(f"note: not in the live load order, skipped: {', '.join(unplaced)}\n")

    # 1. toxic spells: winning SPEL description says "no longer used"
    spell_winners, _ = collect_winners(roots, order, "Spells", read_losers=False)
    toxic_spells = {fk: edid(t) for fk, (p, t) in spell_winners.items()
                    if "no longer used" in t.lower()}

    # 2. toxic books: winning BOOK teaches a toxic spell
    book_winners, _ = collect_winners(roots, order, "Books", read_losers=False)
    toxic_books = {}
    for fk, (plugin, text) in book_winners.items():
        m = TEACH.search(text)
        if m:
            taught = m.group(1).upper() + ":" + m.group(2)
            if taught in toxic_spells:
                toxic_books[fk] = (edid(text), toxic_spells[taught], plugin)

    print(f"toxic spells (winning description says 'no longer used'): {len(toxic_spells)}")
    print(f"toxic books (winning record teaches one): {len(toxic_books)}")
    if show_all:
        for fk, (be, sp, wp) in sorted(toxic_books.items(), key=lambda x: x[1][0]):
            print(f"  {fk}  {be}  teaches {sp}  [book winner: {wp}]")
    print()

    # 3. live hits: winning list-shaped record references a toxic book
    def toxic_refs(entry_re, text):
        """Entry FormKeys present in `text` that are toxic books. The entry
        patterns capture 'hex:master' as ONE group; normalise only the hex."""
        out = set()
        for m in entry_re.finditer(text):
            hexpart, master = m.group(1).split(":", 1)
            out.add(hexpart.upper() + ":" + master)
        return out & set(toxic_books)

    hits, deliberate, blocked = [], [], []
    for group, entry_re in LIST_TYPES.items():
        winners, losers = collect_winners(roots, order, group)
        for fk, (plugin, text) in winners.items():
            found = sorted(toxic_refs(entry_re, text))
            if found:
                rec = (group, fk, edid(text), plugin, found)
                (deliberate if fk.split(":")[0] in DELIBERATE else hits).append(rec)
            winner_set = set(found)
            for lplugin, ltext in losers[fk]:
                lfound = sorted(toxic_refs(entry_re, ltext) - winner_set)
                if lfound:
                    blocked.append((group, fk, edid(text), lplugin, plugin, lfound))

    if hits:
        print(f"LIVE HITS - a winning record still hands out a deprecated tome: {len(hits)}")
        for group, fk, e, plugin, found in sorted(hits):
            print(f"  [{group}] {e} ({fk})  winner={plugin}")
            for b in found:
                be, sp, _ = toxic_books[b]
                print(f"      -> {b} {be} teaches {sp}")
    else:
        print("no live hits - no winning container, leveled list or NPC inventory "
              "hands out a deprecated tome")
    for group, fk, e, plugin, found in sorted(deliberate):
        print(f"  (deliberate) [{group}] {e} ({fk}): {DELIBERATE[fk.split(':')[0]]} "
              f"- {len(found)} toxic books")

    print(f"\nblocked loser-only carriers (a later winner drops them): {len(blocked)}")
    if show_all:
        for group, fk, e, lplugin, wplugin, found in sorted(blocked):
            print(f"  [{group}] {e} ({fk})  loser={lplugin} blocked-by={wplugin}: "
                  f"{', '.join(found)}")

    sys.exit(1 if hits else 0)


if __name__ == "__main__":
    main()
