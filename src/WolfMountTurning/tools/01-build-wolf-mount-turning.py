"""Generate the Wolf Mount Turning plugin YAML -- never hand-edit WolfMountTurningESP/Races/.

Player report (Junebug, 2026-11-12): Father Shadow, the Shadow of Transience mount (NPC 0450F9, race
HorseFluteWolfMountRace 0450F7, a wolf on WolfProject.hkx), only runs straight when ridden and cannot turn.

Cause (ZenMountTrace + 00-scan-mount-movement.py): a ridden mount moves on the movement types its behaviour graph
names, WolfDefault/WolfRun (Wolf_Default_MT 055D28 / Wolf_Run_MT 0EA64B). EGO (Enderal SE - Gameplay Overhaul.esp)
wins both and drops their RotateWhileMovingRun (stock 360 deg/s -> 0), so as soon as the wolf moves the engine allows
it no turn at all; every key makes it move, so it only runs straight. Wild wolves are what EGO tuned that for.

Fix, mount only: the race's own movement-type speed overrides (RACE MTYP/SPED, Spriggit `MovementTypes`, as vanilla
cows/atronachs use). This plugin carries EGO's winning race record verbatim plus one override per wolf movement type:
EGO's speeds and in-place turn rates, with stock Skyrim.esm's RotateWhileMovingRun. The MOVT records stay EGO's.

Override fields (Mutagen): RotateWalk/RotateRun = in-place turn (walk/run), Unknown = turn while moving, radians.
Re-serialize EGO into reference/mods/EGO before re-running; rerun 00-scan-mount-movement.py to check the winners.
"""
import math
import os
import re
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
ESP = os.path.join(ROOT, "src", "WolfMountTurning", "WolfMountTurningESP")
RACE = "HorseFluteWolfMountRace - 0450F7_Skyrim.esm.yaml"
EGO_RACE = os.path.join(ROOT, "reference", "mods", "EGO", "Races", RACE)
MOVTS = [("055D28:Skyrim.esm", "Wolf_Default_MT - 055D28_Skyrim.esm.yaml"),
         ("0EA64B:Skyrim.esm", "Wolf_Run_MT - 0EA64B_Skyrim.esm.yaml")]
EGO_MOVT = os.path.join(ROOT, "reference", "mods", "EGO", "MovementTypes")
BASE_MOVT = os.path.join(ROOT, "reference", "base", "Skyrim", "MovementTypes")


def read(p):
    return open(p, encoding="utf-8", newline="").read()


def fields(path):
    out = {}
    for m in re.finditer(r"^(\w+): ([-0-9.E+]+)\r?$", read(path), flags=re.M):
        out[m.group(1)] = float(m.group(2))
    return out


def fmt(v):
    return repr(round(v, 7))


def override_block(nl):
    lines = ["MovementTypes:"]
    for fk, name in MOVTS:
        ego = fields(os.path.join(EGO_MOVT, name))
        base = fields(os.path.join(BASE_MOVT, name))
        if "RotateWhileMovingRun" in ego:
            raise SystemExit(f"{name}: EGO now has RotateWhileMovingRun {ego['RotateWhileMovingRun']}; recheck the cause")
        if base.get("RotateWhileMovingRun", 0) <= 0:
            raise SystemExit(f"{name}: stock RotateWhileMovingRun missing")
        lines += [f"- MovementType: {fk}", "  Overrides:"]
        for key in ("ForwardWalk", "ForwardRun", "BackWalk", "BackRun"):
            if ego.get(key):
                lines.append(f"    {key}: {fmt(ego[key])}")
        lines.append(f"    RotateWalk: {fmt(math.radians(ego['RotateInPlaceWalk']))}")
        lines.append(f"    RotateRun: {fmt(math.radians(ego['RotateInPlaceRun']))}")
        lines.append(f"    Unknown: {fmt(math.radians(base['RotateWhileMovingRun']))}")
        print(f"{name}: run {ego['ForwardRun']}, in place {ego['RotateInPlaceWalk']}/{ego['RotateInPlaceRun']} deg/s,"
              f" while moving 0 -> {base['RotateWhileMovingRun']} deg/s (stock)")
    return nl.join(lines) + nl


def main():
    text = read(EGO_RACE)
    nl = "\r\n" if "\r\n" in text else "\n"
    if re.search(r"^MovementTypes:", text, flags=re.M):
        raise SystemExit("EGO's race already has MovementTypes; merge instead of inserting")
    anchors = len(re.findall(r"^EquipmentFlags:", text, flags=re.M))
    if anchors != 1:
        raise SystemExit(f"expected one EquipmentFlags line, found {anchors}")
    text = re.sub(r"^(?=EquipmentFlags:)", override_block(nl).replace("\\", "\\\\"), text, count=1, flags=re.M)
    races = os.path.join(ESP, "Races")
    if os.path.isdir(races):
        shutil.rmtree(races)
    os.makedirs(races)
    with open(os.path.join(races, RACE), "w", encoding="utf-8", newline="") as f:
        f.write(text)
    print("wrote", os.path.relpath(os.path.join(races, RACE), ROOT))


if __name__ == "__main__":
    main()
