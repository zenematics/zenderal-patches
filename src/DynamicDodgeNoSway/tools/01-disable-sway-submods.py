#!/usr/bin/env python3
"""Make Dynamic Dodge play its normal step dodge when a dodge cancels an attack.

Why: Dynamic Dodge (Smooth, Nexus 79598, "TK Dodge RE-0.55-rc3" OAR set, installed with
the "Attack Cancel Option: Sway") ships two parallel submod sets with identical .hkx names:
  70110-70144  weapon/direction step dodges
  70210-70244  the same conditions + IsAttacking, higher priority -> the on-the-spot "sway"
TK Dodge RE's EnableDodgeAttackCancel stays ON (the cancel itself is wanted); disabling the
20 IsAttacking submods makes an attack-cancel dodge fall through to the matching 701xx one.

Mechanism: an OAR user.json beside a submod's config.json REPLACES that config, so each
user.json is the author's config.json verbatim plus "disabled": true. Dynamic Dodge ships no
user.json, so this release adds files without overwriting any of the author's.

Asserted: every disabled submod carries IsAttacking, and no 701xx submod does (otherwise
the fallback would be excluded too). Verified in game 2026-10-05.

Input: <modlistRoot>/mods/Dynamic Dodge Animation (from .claude/config/tools.json)
Output: src/DynamicDodgeNoSway/meshes/... (regenerated)
"""
import glob
import json
import os
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
REL = os.path.join("meshes", "actors", "character", "animations", "OpenAnimationReplacer",
                   "Dynamic Dodge - TK Dodge RE-0.55-rc3")
OUT_ROOT = os.path.join(ROOT, "src", "DynamicDodgeNoSway", "meshes")
EXPECTED = 20


def is_attacking_gated(cfg):
    return any(c.get("condition") == "IsAttacking" and not c.get("negated") for c in cfg.get("conditions", []))


def main():
    tools = json.load(open(os.path.join(ROOT, ".claude", "config", "tools.json"), encoding="utf-8-sig"))
    src = os.path.join(tools["modlistRoot"], "mods", "Dynamic Dodge Animation", REL)
    if not os.path.isdir(src):
        sys.exit(f"Dynamic Dodge OAR folder not found: {src}")

    for d in glob.glob(os.path.join(src, "701*")):
        if is_attacking_gated(json.load(open(os.path.join(d, "config.json"), encoding="utf-8"))):
            sys.exit(f"{d} is IsAttacking-gated - the step-dodge fallback would not apply")

    if os.path.isdir(OUT_ROOT):
        shutil.rmtree(OUT_ROOT)
    dst = os.path.join(ROOT, "src", "DynamicDodgeNoSway", REL)
    n = 0
    for d in sorted(glob.glob(os.path.join(src, "702*"))):
        cfg = json.load(open(os.path.join(d, "config.json"), encoding="utf-8"))
        if not is_attacking_gated(cfg):
            sys.exit(f"{d} is not IsAttacking-gated - refusing to disable it")
        cfg["disabled"] = True
        out = os.path.join(dst, os.path.basename(d))
        os.makedirs(out)
        with open(os.path.join(out, "user.json"), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(cfg, fh, indent=4)
            fh.write("\n")
        n += 1
    if n != EXPECTED:
        sys.exit(f"expected {EXPECTED} sway submods, disabled {n} - did Dynamic Dodge update?")
    print(f"OK: {n} sway submods disabled")


if __name__ == "__main__":
    main()
