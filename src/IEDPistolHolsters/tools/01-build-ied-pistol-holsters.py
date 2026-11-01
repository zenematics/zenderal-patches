#!/usr/bin/env python3
"""Give the flintlock pistols their own IED holster, apart from staves.

Why: the pistols are staff-type WEAPs (FlintlockOverhaul / LoopPistolAnims; changing the type
breaks their animations and reload). IED files every weapon into a fixed slot by weapon type,
and Simple Dual Sheath hangs every sheathed staff-type weapon on the gear node `WeaponStaff`
(right hand) / `WeaponStaffLeft` (left), whatever the mesh's Prn says. So the curator could
only move both together: the 2026-10-21 export "Gunslinger 2" re-parents both staff nodes to
the bolt-quiver nodes MOV BOLTXP32 / MOV BOLTABQ for the player, which put the player's staves
on the hips as well.

Mechanism (IED config only, no IED file is edited):
  1. ExtraGearNodes `00300_ZenderalPistolHolsters.json` (committed, src/IEDPistolHolsters/SKSE)
     creates CME/MOV/node chains `ZenPistolRight` / `ZenPistolLeft` beside the XPMSE bolt nodes:
     same parent, MOV transform read from MOV BOLTXP32 / MOV BOLTABQ, end node from
     WeaponStaff / WeaponStaffLeft. A pistol on them sits exactly where it sat on the bolt nodes.
  2. This script writes a full IED export (the curator's config + the changes below) that is
     imported in game with File > Import, without "Merge" (IED's merge replaces whole classes):
       - transforms pdata `WeaponStaff` / `WeaponStaffLeft`, in default_player, default_npc and
         every actor/NPC/race entry that already places them: a placement override, first in
         the list, "Hand (right/left) has keyword Pistol_Animation_By_Loop" -> MOV ZenPistol*.
         IED evaluates it per node (INodeOverride::get_target_node, condition type Hand = the
         processManager's equipped object in that hand).
       - an entry whose base target was a bolt node (the curator's pistol workaround) has it
         moved: that entry's CME BOLT* transform is copied to CME ZenPistol*, and the base
         target is cleared, so staves go back to the default staff node.
       - default_player / default_npc get the same CME ZenPistol* transform when the source
         had one (NPC pistols holster where the player's do).
       - slot displays `staff` / `staff_l`: an equipment override, last in the list (after the
         "Disable ..." ones), "this item has the keyword" -> node ZenPistolRight / Left, so a
         carried, unequipped pistol is displayed in the holster too.
     The keyword `Pistol_Animation_By_Loop 0x801:Pistol animation by Loop.esp` is on all 13
     pistols: Loop's 4 Hunter Pistols and Reversal Shadow's own, plus the pack's 8 through
     KID (AdventurerFlintlockPack_PABL_KID.ini). Loop's 4 Hunter Crossbows carry it too.

Input:  an IED export (default: the newest in <modlistRoot>/overwrite/SKSE/Plugins/IED/Exports;
        export your current config from IED first, File > Export).
Output: <modlistRoot>/mods/Zenderal - IED Pistol Holsters/
          SKSE/Plugins/IED/SkeletonExtensions/ExtraGearNodes/00300_ZenderalPistolHolsters.json
          SKSE/Plugins/IED/Exports/Zenderal - Pistol Holsters.json

Usage:  python 01-build-ied-pistol-holsters.py [--source <export.json>] [--dry-run]
Run only with MO2 and the game closed.
"""
import argparse
import copy
import glob
import json
import os
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
PATCH = os.path.join(ROOT, "src", "IEDPistolHolsters")
NODES_REL = os.path.join("SKSE", "Plugins", "IED", "SkeletonExtensions", "ExtraGearNodes",
                         "00300_ZenderalPistolHolsters.json")
EXPORTS_REL = os.path.join("SKSE", "Plugins", "IED", "Exports")
OUT_NAME = "Zenderal - Pistol Holsters.json"
MOD_NAME = "Zenderal - IED Pistol Holsters"

KEYWORD = {"id": 0x801, "plugin": "Pistol animation by Loop.esp"}   # Pistol_Animation_By_Loop
GROUP = {"data": {"flags": 0}, "version": 1}

# gear node -> (holster name, bolt node the curator used, IED NodeOverrideConditionFlags)
#   Hand condition = type 25; kMatchLeftHand = 1 << 7
SIDES = {
    "WeaponStaff": ("ZenPistolRight", "BOLTXP32", 25),
    "WeaponStaffLeft": ("ZenPistolLeft", "BOLTABQ", 25 | (1 << 7)),
}
# slot -> holster node; EquipmentOverrideConditionFlags: type Keyword = 2, kMatchThisItem = 1 << 10
SLOTS = {"staff": "ZenPistolRight", "staff_l": "ZenPistolLeft"}
SLOT_COND_FLAGS = 2 | (1 << 10)
DESC = "Zenderal pistol holster"


def placement_override(holster, cond_flags):
    return {
        "desc": DESC,
        "flags": 0,
        "override_flags": 0,
        "target": "MOV " + holster,
        "matches": {
            "data": [{
                "flags": cond_flags,
                "kw": dict(KEYWORD),
                "bip": 4294967295,
                "type": 0,
                "f32a": 0.0, "ui32b": 0, "i32a": 0, "ui64a": 0, "ui32c": 0,
                "group": copy.deepcopy(GROUP),
            }],
            "version": 2,
        },
    }


def strip_ours(overrides):
    """Drop a previous run's override so reruns don't stack."""
    return [o for o in overrides if o.get("desc") != DESC]


def patch_holder(holder, label, log, migrate=True):
    """holder = transforms class data with optional 'data' (CME transforms) and 'pdata'."""
    pdata = holder.setdefault("pdata", {})
    cme = holder.setdefault("data", {})
    seeded = {}
    for gear, (holster, bolt, cond_flags) in SIDES.items():
        entry = pdata.setdefault(gear, {})
        for sex in ("m", "f"):
            p = entry.setdefault(sex, {"flags": 0, "parent_flags": 0})
            target = p.get("target", "")
            if migrate and target == "MOV " + bolt:
                src = cme.get("CME " + bolt, {}).get(sex)
                if src is not None and ("CME " + holster) not in cme:
                    seeded.setdefault("CME " + holster, {})[sex] = copy.deepcopy(src)
                del p["target"]
                log.append(f"{label} {gear}/{sex}: base target {target} -> default (staves); "
                           f"pistol spot {'copied from CME ' + bolt if src is not None else 'left at bolt default'}")
            ov = p.get("overrides", {"data": [], "version": 1})
            ov["data"] = [placement_override(holster, cond_flags)] + strip_ours(ov.get("data", []))
            ov["version"] = 1
            p["overrides"] = ov
            log.append(f"{label} {gear}/{sex}: pistol override -> MOV {holster} "
                       f"(base {p.get('target', 'default')})")
    for k, v in seeded.items():
        cme[k] = v
    return seeded


def slot_override(base, holster):
    cfg = {k: copy.deepcopy(base[k]) for k in ("exl", "flags") if k in base}
    cfg["node"] = {"flags": 0, "name": holster}
    return {
        "config": cfg,
        "desc": DESC,
        "flags": 0,
        "matches": {
            "data": [{
                "flags": SLOT_COND_FLAGS,
                "keyword": dict(KEYWORD),
                "bslot": 4294967295,
                "type": 255,
                "f32a": 0.0, "ui32b": 0, "i32a": 0, "ui64a": 0, "ui32c": 0,
                "group": copy.deepcopy(GROUP),
            }],
            "version": 2,
        },
    }


def patch_slots(slot_data, label, log):
    for slot, holster in SLOTS.items():
        sx = slot_data.get(slot)
        if not sx:
            continue
        for sex in ("m", "f"):
            base = sx.get(sex)
            if base is None:
                continue
            ao = base.setdefault("ao", {"data": [], "version": 1})
            ao["data"] = strip_ours(ao.get("data", [])) + [slot_override(base, holster)]
            log.append(f"{label} slot {slot}/{sex}: display override -> {holster}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    tools = json.load(open(os.path.join(ROOT, ".claude", "config", "tools.json"), encoding="utf-8-sig"))
    mo2 = tools["modlistRoot"]
    if args.source:
        src = args.source
    else:
        cands = [f for f in glob.glob(os.path.join(mo2, "overwrite", EXPORTS_REL, "*.json"))
                 if os.path.basename(f) != OUT_NAME]
        if not cands:
            sys.exit("no IED export found; export from IED (File > Export) or pass --source")
        src = max(cands, key=os.path.getmtime)
    print("source:", src)
    conf = json.load(open(src, encoding="utf-8"))
    data = conf["data"]

    log = []
    tr = data["transforms"]["data"]
    seeded = {}
    for cls in ("actor", "npc", "race"):
        for e in tr[cls]["data"]:
            holder = e["data"]["data"]
            pd = holder.get("pdata", {})
            if not any(g in pd for g in SIDES):
                continue
            label = f"{cls} {e['form']['plugin']}:{e['form']['id']:06X}"
            for k, v in patch_holder(holder, label, log).items():
                seeded.setdefault(k, v)
    for cls in ("default_player", "default_npc"):
        holder = tr[cls]["data"]
        patch_holder(holder, cls, log, migrate=False)
        for k, v in seeded.items():
            if k not in holder["data"]:
                holder["data"][k] = copy.deepcopy(v)
                log.append(f"{cls}: {k} transform seeded from the migrated entry")

    sl = data["slot"]["data"]
    for cls in ("default_player", "default_npc"):
        patch_slots(sl[cls]["data"], cls, log)
    for cls in ("actor", "npc", "race"):
        for e in sl[cls]["data"]:
            patch_slots(e["data"]["data"], f"{cls} {e['form']['plugin']}:{e['form']['id']:06X}", log)

    print("\n".join(log))
    # every class must carry both pistol overrides; the slot displays both sides
    n_place = sum(1 for line in log if "pistol override" in line)
    n_slot = sum(1 for line in log if "display override" in line)
    if n_place < 8 or n_slot < 8:
        sys.exit(f"expected >= 8 placement and 8 display overrides, got {n_place}/{n_slot}")
    if args.dry_run:
        return

    mod = os.path.join(mo2, "mods", MOD_NAME)
    os.makedirs(os.path.join(mod, os.path.dirname(NODES_REL)), exist_ok=True)
    shutil.copyfile(os.path.join(PATCH, NODES_REL), os.path.join(mod, NODES_REL))
    out = os.path.join(mod, EXPORTS_REL, OUT_NAME)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(conf, fh, ensure_ascii=False, separators=(",", ":"))
    print("wrote", out)
    print("wrote", os.path.join(mod, NODES_REL))


if __name__ == "__main__":
    main()
