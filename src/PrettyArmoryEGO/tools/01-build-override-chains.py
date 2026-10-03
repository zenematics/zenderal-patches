#!/usr/bin/env python3
"""Record the live override chain of every armour-related record in the installed modlist.

Reads each enabled plugin's binary directly (record headers only - no Spriggit, so all ~290
plugins scan in seconds) and lists, per FormKey, every plugin that defines or overrides it,
in load order. 02-merge-pretty-ego.py reads the result to decide which plugins to merge.

Paths come from .claude/config/tools.json (modlistRoot) - never hardcoded. The MO2 profile
defaults to the one ModOrganizer.ini has selected; pass a profile name to override.

Output: reference/mods/Pretty/_chains.json (gitignored, regenerable).

Usage:  python 01-build-override-chains.py ["<MO2 profile name>"]
"""
import json
import os
import re
import struct
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
OUT = os.path.join(ROOT, "reference", "mods", "Pretty", "_chains.json")
TYPES = {b"ARMO", b"WEAP", b"AMMO", b"ARMA", b"OUTF", b"NPC_", b"STAT", b"PROJ"}
BASE = ["Skyrim.esm", "Update.esm", "Enderal - Forgotten Stories.esm"]


def tools():
    with open(os.path.join(ROOT, ".claude", "config", "tools.json"), encoding="utf-8-sig") as f:
        t = json.load(f)
    if not t.get("modlistRoot"):
        sys.exit("tools.json has no modlistRoot - run the modlist-install skill or fill it in")
    return t


def selected_profile(mlroot):
    ini = open(os.path.join(mlroot, "ModOrganizer.ini"), encoding="utf-8", errors="replace").read()
    m = re.search(r"^selected_profile=(?:@ByteArray\()?(.*?)\)?\s*$", ini, re.M)
    if not m:
        sys.exit("no selected_profile in ModOrganizer.ini - pass a profile name")
    return m.group(1)


def plugin_paths(mlroot, prof, game_data):
    """lowercase plugin filename -> path, resolved the way MO2's VFS would (priority order)."""
    mods = [l[1:].strip() for l in open(os.path.join(prof, "modlist.txt"), encoding="utf-8")
            if l.startswith("+")]
    paths = {}
    for d in reversed(mods):  # modlist.txt is highest-priority FIRST, so walk it backwards
        p = os.path.join(mlroot, "mods", d)
        if os.path.isdir(p):
            for f in os.listdir(p):
                if f.lower().endswith((".esp", ".esm", ".esl")):
                    paths[f.lower()] = os.path.join(p, f)
    for f in os.listdir(game_data):
        if f.lower().endswith((".esp", ".esm", ".esl")) and f.lower() not in paths:
            paths[f.lower()] = os.path.join(game_data, f)
    return paths


def scan(path):
    """(masters, [(type, raw formid)]) for every record of a TYPES group."""
    b = open(path, "rb").read()
    hsz = struct.unpack_from("<I", b, 4)[0]
    pos, end, masters = 24, 24 + hsz, []
    while pos < end:
        t = b[pos:pos + 4]
        sz = struct.unpack_from("<H", b, pos + 4)[0]
        if t == b"MAST":
            masters.append(b[pos + 6:pos + 6 + sz - 1].decode("cp1252"))
        pos += 6 + sz
    recs = []

    def walk(p, stop):
        while p < stop:
            t = b[p:p + 4]
            sz = struct.unpack_from("<I", b, p + 4)[0]
            if t == b"GRUP":
                walk(p + 24, p + sz)
                p += sz
            else:
                if t in TYPES:
                    recs.append((t.decode(), struct.unpack_from("<I", b, p + 12)[0]))
                p += 24 + sz

    while pos < len(b):
        sz = struct.unpack_from("<I", b, pos + 4)[0]
        if b[pos + 8:pos + 12] in TYPES:
            walk(pos + 24, pos + sz)
        pos += sz
    return masters, recs


def main():
    t = tools()
    mlroot = t["modlistRoot"]
    pname = sys.argv[1] if len(sys.argv) > 1 else selected_profile(mlroot)
    prof = os.path.join(mlroot, "profiles", pname)
    game_data = t.get("gameDataDir") or os.path.join(mlroot, "Stock Game", "Data")
    paths = plugin_paths(mlroot, prof, game_data)
    order = list(BASE)
    for l in open(os.path.join(prof, "plugins.txt"), encoding="utf-8"):
        l = l.strip()
        if l.startswith("*") and l[1:] not in order:
            order.append(l[1:])
    chain = {}
    missing = []
    for pl in order:
        if pl.lower() not in paths:
            missing.append(pl)
            continue
        masters, recs = scan(paths[pl.lower()])
        for typ, fid in recs:
            idx = fid >> 24
            owner = masters[idx] if idx < len(masters) else pl
            chain.setdefault(f"{fid & 0xFFFFFF:06X}:{owner}", {"type": typ, "chain": []})["chain"].append(pl)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"profile": pname, "order": order, "chain": chain}, f, indent=0)
    pretty = [p for p in order if p.startswith("Pretty")]
    print(f"profile '{pname}': {len(order)} active plugins, {len(chain)} records -> {OUT}")
    print(f"Pretty plugins active: {len(pretty)}")
    if missing:
        print("not found on disk (skipped):", ", ".join(missing))
    if not pretty:
        sys.exit("no Pretty plugin is active in this profile - nothing to merge")


if __name__ == "__main__":
    main()
