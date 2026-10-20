#!/usr/bin/env python3
"""Raise RaySense Cover Animation and both RaySense wall-lean mods above every competing OAR set.

Why: the curator wants these to win whenever their RaySense conditions are true. In the
Ultra profile the highest competitor on the idles they replace (mt_idle, 1hm/2hm/2hw/bow/
staff/mlh/mrh idles, the sneak idles) is Beam Walking Assist at 2110000084, with Edge
Lookdown at 2110000070-071. Several Cover submods sat below both (2110000000-069), and
Sonder's Raysense Wall Leaning shipped at 7005000-007 - below EVG Conditional Idles (~86M)
and UNDERDOG (~2B), so it could never play.

New bands, each author's internal order kept by a constant offset:
  Cover Animation          2110000000-231  ->  2140000000-231   (top: a cover exit beats a lean)
  Sonder's Wall Leaning       7005000-007  ->  2130000100-107
  Simple Wall Lean (wm)   2078869540-546  ->  2130000000-006
All three bands sit above Beam Walking (2110000084) and Edge Lookdown, and below int32 max.

Mechanism: an OAR user.json beside a submod's config.json REPLACES that config, so each
user.json is the author's config.json verbatim with only "priority" changed. None of the
three mods ships a user.json, so this adds files without overwriting any of the authors'.
Caveat: OAR's in-game editor also writes user.json (into MO2's overwrite), which would win
over these.

Input: <modlistRoot>/mods/<the three mods> (from .claude/config/tools.json)
Output: src/RaySensePriority/meshes/... (regenerated)
"""
import json
import os
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
OUT_ROOT = os.path.join(ROOT, "src", "RaySensePriority", "meshes")
OAR_REL = os.path.join("meshes", "actors", "character", "animations", "OpenAnimationReplacer")

# mod folder, OAR mod folder, old priority range, new base, expected submod count
MODS = [
    ("RaySense - Cover Animation", "RaySense - Cover Animation", (2110000000, 2110000231), 2140000000, 38),
    ("Sonder's Raysense Wall Leaning", "SDB_RSWL", (7005000, 7005007), 2130000100, 8),
    ("Simple Wall Lean (RaySense)", "RaySense - wm Lean against the walll", (2078869540, 2078869546), 2130000000, 4),
]
INT32_MAX = 2147483647


def find_ci(base, rel):
    """Resolve rel under base case-insensitively (mods ship Meshes/ vs meshes/)."""
    cur = base
    for part in rel.split(os.sep):
        match = [e for e in os.listdir(cur) if e.lower() == part.lower()]
        if not match:
            sys.exit(f"missing {part} under {cur}")
        cur = os.path.join(cur, match[0])
    return cur


def main():
    tools = json.load(open(os.path.join(ROOT, ".claude", "config", "tools.json"), encoding="utf-8-sig"))
    mods_dir = os.path.join(tools["modlistRoot"], "mods")

    if os.path.isdir(OUT_ROOT):
        shutil.rmtree(OUT_ROOT)
    total = 0
    for mod, oar_mod, (lo, hi), new_base, expected in MODS:
        src = find_ci(os.path.join(mods_dir, mod), os.path.join(OAR_REL, oar_mod))
        n = 0
        for dp, _dn, fn in os.walk(src):
            if "user.json" in fn:
                sys.exit(f"{dp} already ships a user.json - it would be overwritten")
            if "config.json" not in fn or dp == src:
                continue
            cfg = json.load(open(os.path.join(dp, "config.json"), encoding="utf-8-sig"))
            old = cfg.get("priority")
            if not isinstance(old, int) or not lo <= old <= hi:
                sys.exit(f"{dp}: priority {old!r} outside expected {lo}-{hi} - did {mod} update?")
            cfg["priority"] = new_base + (old - lo)
            assert cfg["priority"] <= INT32_MAX
            out = os.path.join(OUT_ROOT, "actors", "character", "animations", "OpenAnimationReplacer",
                               oar_mod, os.path.relpath(dp, src))
            os.makedirs(out)
            with open(os.path.join(out, "user.json"), "w", encoding="utf-8", newline="\n") as fh:
                json.dump(cfg, fh, indent=4, ensure_ascii=False)
                fh.write("\n")
            n += 1
        if n != expected:
            sys.exit(f"{mod}: expected {expected} submods, wrote {n} - did it update?")
        print(f"{mod}: {n} submods -> {new_base}-{new_base + hi - lo}")
        total += n
    print(f"OK: {total} user.json files")


if __name__ == "__main__":
    main()
