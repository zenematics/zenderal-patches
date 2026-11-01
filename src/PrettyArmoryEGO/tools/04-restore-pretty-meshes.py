#!/usr/bin/env python3
"""Add 4 overrides where EGO's model swap hides a Pretty mesh no Pretty plugin record points at.

Found 2026-10-30 comparing the Nexus "PEA - EGO Patch" (Enderal mod 1143) with this patch. EGO repoints these
records at vanilla Skyrim/Dragonborn meshes; Pretty replaces the meshes at the ORIGINAL Enderal paths inside its
BSAs, and no Pretty plugin overrides the records, so 01/02 never see them (no Pretty plugin in the chain):

  02C5E9:FS          Tharael's Bow        EGO DLC02 NordicBow       -> Weapons\\NordHero\\NordHeroBow.nif (Pretty Common)
  0670F5:Skyrim.esm  Leaf Dancer's Bow    EGO GlassBowSkinned       -> sabre_cat_bow.nif (Pretty Unique)
  05BB24:Skyrim.esm  Steel Arrow          EGO DLC02 NordicArrow     -> Weapons\\Steel\\SteelArrow.nif
  03BE12:Skyrim.esm  ArrowSteelProjectile EGO NordicArrowFlight     -> Weapons\\Steel\\SteelArrowFlight.nif
                     (the steel arrow meshes shown are ERA Part 1's loose ones, which beat Pretty's BSA copy)

Each override = EGO's record verbatim with Model / FirstPersonModel / ObjectBounds taken from the Enderal record
EGO overrides (FS's when FS overrides base), the same three fields Zenderal - Moonsteel Pretty Patch swaps.
PEA's circlet / novice robe / nomad amulet hookups are NOT taken: they point at armatures (000823-00082B:Pretty
Unique Armory, 00082E:Pretty Factions, 000806:Pretty Unique Sets) that the list's Pretty 2.0 plugins lack.

Run after 02 and 03 (02 wipes the record folders). Fails if a chain gained another plugin since this was written.
"""
import collections
import glob
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
REF = os.path.join(ROOT, "reference")
ESP = os.path.join(ROOT, "src", "PrettyArmoryEGO", "PrettyArmoryEGOESP")
EGO = "Enderal SE - Gameplay Overhaul.esp"
TREES = {"Skyrim.esm": os.path.join(REF, "base-2.1.4.4", "Skyrim"),
         "Enderal - Forgotten Stories.esm": os.path.join(REF, "base-2.1.4.4", "EnderalFS"),
         EGO: os.path.join(REF, "mods", "EGO - Enderal Gameplay Overhaul")}
RECORDS = {  # FormKey -> (folder, expected live chain)
    "02C5E9:Enderal - Forgotten Stories.esm": ("Weapons", ["Enderal - Forgotten Stories.esm", EGO]),
    "0670F5:Skyrim.esm": ("Weapons", ["Skyrim.esm", "Enderal - Forgotten Stories.esm", EGO]),
    "05BB24:Skyrim.esm": ("Ammunitions", ["Skyrim.esm", EGO]),
    "03BE12:Skyrim.esm": ("Projectiles", ["Skyrim.esm", EGO]),
}
SWAP = ("Model", "FirstPersonModel", "ObjectBounds")


def find(plugin, folder, fk):
    fid, owner = fk.split(":", 1)
    hits = glob.glob(os.path.join(TREES[plugin], folder, f"* - {fid}_{owner}.yaml"))
    if len(hits) != 1:
        sys.exit(f"{fk}: expected one {folder} record in {plugin}'s tree, found {len(hits)}")
    return hits[0]


def fields(path):
    out, cur = collections.OrderedDict(), None
    with open(path, encoding="utf-8-sig", newline="") as f:
        for line in f.read().splitlines():
            if line and not line[0].isspace() and not line.startswith("- "):
                cur = line.split(":", 1)[0]
                out[cur] = [line]
            elif cur is not None:
                out[cur].append(line)
    return out


def main():
    chains = json.load(open(os.path.join(REF, "mods", "Pretty", "_chains.json"), encoding="utf-8"))["chain"]
    for fk, (folder, expect) in RECORDS.items():
        live = chains.get(fk, {}).get("chain")
        if live != expect:
            sys.exit(f"{fk}: live chain is now {live}, not {expect} - re-check before forwarding EGO's record")
        ego_path = find(EGO, folder, fk)
        e = fields(ego_path)
        b = fields(find(expect[-2], folder, fk))
        out, swapped = collections.OrderedDict(), []
        for k, v in e.items():
            if k in SWAP:
                if k in b:
                    out[k] = b[k]
                    swapped.append(k)
                continue  # EGO's own model field without a base counterpart is dropped
            out[k] = v
        for k in SWAP:  # a model field only the base record has goes after EditorID/ObjectBounds order
            if k in b and k not in out:
                keys = list(b)
                prev = [p for p in keys[:keys.index(k)] if p in out]
                items = list(out.items())
                at = [i for i, (kk, _) in enumerate(items) if kk == prev[-1]][0] + 1 if prev else len(items)
                items.insert(at, (k, b[k]))
                out = collections.OrderedDict(items)
                swapped.append(k)
        assert "Model" in swapped, (fk, swapped)
        d = os.path.join(ESP, folder)
        os.makedirs(d, exist_ok=True)
        name = os.path.basename(ego_path)
        with open(os.path.join(d, name), "w", encoding="utf-8", newline="") as f:
            f.write("\r\n".join(l for v in out.values() for l in v) + "\r\n")
        print(f"{fk} {name.split(' - ')[0]}: {', '.join(sorted(set(swapped)))} from {expect[-2]}")


if __name__ == "__main__":
    main()
