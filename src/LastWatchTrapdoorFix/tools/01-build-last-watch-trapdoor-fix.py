"""Generate the Last Watch Trapdoor Fix plugin YAML -- never hand-edit its Worldspaces/ or Cells/.

Reported 2026-10-20: after climbing from Ark's Last Watch's Watchtower (DPassTurm 103F39) to the
tower top there is no trapdoor to climb back down.

Two mods rebuild that tower top and neither knows the other:
  * EPPI Improved Locations (EPPIimprovedlacations.esp) disables Enderal's TowerTop01 1043EC and lays
    its own plank floor WRIntCastleFloorWoodMid01QuadS 035BE3 (512x512 x1.17) flat at z 13930, with
    cannons and hay on it -- around Enderal's trapdoor and clutter, which it leaves where base put them.
  * Ark's Last Watch (Last Watch Overhaul.esp, loads after EPPI) also disables 1043EC, re-bases the
    tower to TowerBaseUpper_Snow, and drops the trapdoor 1043D6, its ladder's arrival point
    (1042FD's TeleportDestination) and the top's clutter 20-30 units onto that lower, tilted top.
Together, EPPI's floor covers everything Last Watch lowered: the trapdoor (top ~13920) and loot chest
1043F6 (13902) sit under the planks. Neither Last Watch EPPI patch touches the tower top.

This puts the top back on EPPI's floor: every tower-top ref Last Watch wins keeps its Last Watch
record, with Placement taken from the plugin that was built for EPPI's floor -- EPPI's own override
where it has one, otherwise base Enderal (2.1.4.4), which EPPI kept. 1042FD gets base's destination.
Headers are forwarded from each record's last overrider in the Ultra load order:
  WRLD Vyn 001D3C          <- Water for Enderal CS.esp (its own LodWater 000802 -> mastered)
  CELL 001D40 (persistent) <- Zenderal - Ark Bridge Overhaul Fixes.esp (repo YAML, src/ArkBridgeOverhaulFixes)
  CELL ArksletzteWacht 00291B <- Last Watch - EPPI Improved Locations Patch.esp
  CELL DPassTurm 103F39     <- MinotaursInEnderal.esp
Re-check those winners before re-running after a mod near Ark's Last Watch changes.
"""
import os
import re
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
REF = os.path.join(ROOT, "reference")
WS = "Vyn - 001D3C_Skyrim.esm"
SUB = ("0, 0", "0, 1")
CELL = "ArksletzteWacht - 00291B_Skyrim.esm"
TURM = ("1", "6", "DPassTurm - 103F39_Skyrim.esm")
LW = os.path.join(REF, "mods", "LastWatchOverhaul")
EPPI = os.path.join(REF, "mods", "EPPIimprovedlocations")
BASE = os.path.join(REF, "base-2.1.4.4", "Skyrim")
LWEPPI = os.path.join(REF, "mods", "LastWatchEPPIImproved")
WATER = os.path.join(REF, "mods", "WaterForEnderalCS")
MINO = os.path.join(REF, "mods", "MinotaursInEnderal")
ABOFIX = os.path.join(ROOT, "src", "ArkBridgeOverhaulFixes", "ArkBridgeOverhaulFixesESP")
OUT = os.path.join(ROOT, "src", "LastWatchTrapdoorFix", "LastWatchTrapdoorFixESP")
CRLF = "\r\n"
TRAPDOOR = "1043D6:Skyrim.esm"
LADDER = "1042FD:Skyrim.esm"
# The tower top's refs that Last Watch lowered (all with z > 13800 inside EPPI's floor).
CLUTTER = ["1043ED", "1043EE", "1043EF", "1043F0", "1043F1", "1043F2", "1043F3", "1043F4", "1043F5", "1043F6"]
SECTIONS = re.compile(r"^(Temporary|Persistent|NavigationMeshes|Landscape|SubCells|TopCell|MajorFlags):")


def read(*parts):
    with open(os.path.join(*parts), "r", encoding="utf-8", newline="") as f:
        return f.read().replace(CRLF, "\n").replace("\n", CRLF)  # src/ YAML may be LF


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def header(text):
    """Record lines before the first child-record section."""
    out = []
    for line in text.split(CRLF):
        if SECTIONS.match(line):
            break
        out.append(line)
    return CRLF.join(out).rstrip(CRLF) + CRLF


def trailer(text):
    i = text.find(CRLF + "MajorFlags:" + CRLF)
    return text[i + len(CRLF):] if i >= 0 else ""


def block(text, fk):
    """The '- MutagenObjectType:' list item holding FormKey fk, verbatim, at whatever indent it sits."""
    lines = text.split(CRLF)
    hits = [i for i, l in enumerate(lines) if l.strip() == "FormKey: " + fk and lines[i - 1].lstrip().startswith("- MutagenObjectType:")]
    if len(hits) != 1:
        raise SystemExit(f"{fk}: found {len(hits)} times")
    start = hits[0] - 1
    ind = lines[start][: len(lines[start]) - len(lines[start].lstrip())]
    end = start + 1
    while end < len(lines) and lines[end].startswith(ind + "  "):
        end += 1
    return [l[len(ind):] for l in lines[start:end]]  # de-indented to column 0


def sub(blk, key):
    """(start, end) of the '  key:' sub-mapping inside a column-0 block."""
    i = blk.index("  " + key + ":")
    j = i + 1
    while j < len(blk) and blk[j].startswith("    "):
        j += 1
    return i, j


def take(target, donor, key):
    """target with its key sub-mapping replaced by donor's."""
    ti, tj = sub(target, key)
    di, dj = sub(donor, key)
    return target[:ti] + donor[di:dj] + target[tj:]


def indent(blk, ind):
    return [ind + l for l in blk]


def pos(blk, key="Placement"):
    i, j = sub(blk, key)
    return next(l for l in blk[i:j] if l.startswith("    Position:")).split(": ", 1)[1]


for d in ("Worldspaces", "Cells"):
    if os.path.isdir(os.path.join(OUT, d)):
        shutil.rmtree(os.path.join(OUT, d))
log = []

# WRLD + persistent cell: the trapdoor, back at base's spot on EPPI's floor.
lw_wrld = read(LW, "Worldspaces", WS, "RecordData.yaml")
top = read(ABOFIX, "Worldspaces", WS, "RecordData.yaml")
top = top[top.index("TopCell:" + CRLF):]
top = top[: top.index(CRLF + "  Persistent:" + CRLF)] + CRLF
trap = take(block(lw_wrld, TRAPDOOR), block(read(BASE, "Worldspaces", WS, "RecordData.yaml"), TRAPDOOR), "Placement")
log.append(f"{TRAPDOOR} trapdoor: {pos(block(lw_wrld, TRAPDOOR))} -> {pos(trap)}")
wrld = header(read(WATER, "Worldspaces", WS, "RecordData.yaml")) + top + "  Persistent:" + CRLF + CRLF.join(indent(trap, "  ")) + CRLF
write(os.path.join(OUT, "Worldspaces", WS, "RecordData.yaml"), wrld)

# Exterior cell: the tower top's clutter, back on EPPI's floor.
for rel in [(SUB[0], "GroupRecordData.yaml"), (SUB[0], SUB[1], "GroupRecordData.yaml")]:
    os.makedirs(os.path.join(OUT, "Worldspaces", WS, *rel[:-1]), exist_ok=True)
    shutil.copyfile(os.path.join(LW, "Worldspaces", WS, *rel), os.path.join(OUT, "Worldspaces", WS, *rel))
lw_cell = read(LW, "Worldspaces", WS, *SUB, CELL, "RecordData.yaml")
eppi_cell = read(EPPI, "Worldspaces", WS, *SUB, CELL, "RecordData.yaml")
base_cell = read(BASE, "Worldspaces", WS, *SUB, CELL, "RecordData.yaml")
body = ["Temporary:"]
for fid in CLUTTER:
    fk = fid + ":Skyrim.esm"
    donor_text, donor = (eppi_cell, "EPPI") if "FormKey: " + fk in eppi_cell else (base_cell, "base")
    lw_blk = block(lw_cell, fk)
    new = take(lw_blk, block(donor_text, fk), "Placement")
    body += new
    log.append(f"{fk}: {pos(lw_blk)} -> {pos(new)} ({donor})")
head_text = read(LWEPPI, "Worldspaces", WS, *SUB, CELL, "RecordData.yaml")
write(os.path.join(OUT, "Worldspaces", WS, *SUB, CELL, "RecordData.yaml"), header(head_text) + CRLF.join(body) + CRLF + trailer(head_text))

# Interior: the ladder up lands the player where the trapdoor now is.
for rel in [("GroupRecordData.yaml",), (TURM[0], "GroupRecordData.yaml"), (TURM[0], TURM[1], "GroupRecordData.yaml")]:
    os.makedirs(os.path.join(OUT, "Cells", *rel[:-1]), exist_ok=True)
    shutil.copyfile(os.path.join(LW, "Cells", *rel), os.path.join(OUT, "Cells", *rel))
lw_turm = read(LW, "Cells", *TURM, "RecordData.yaml")
ladder = take(block(lw_turm, LADDER), block(read(BASE, "Cells", *TURM, "RecordData.yaml"), LADDER), "TeleportDestination")
log.append(f"{LADDER} ladder destination: {pos(block(lw_turm, LADDER), 'TeleportDestination')} -> {pos(ladder, 'TeleportDestination')}")
head_text = read(MINO, "Cells", *TURM, "RecordData.yaml")
write(os.path.join(OUT, "Cells", *TURM, "RecordData.yaml"), header(head_text) + "Persistent:" + CRLF + CRLF.join(ladder) + CRLF + trailer(head_text))

print(CRLF.join(log).replace(CRLF, "\n"))
if len(log) != 2 + len(CLUTTER):
    raise SystemExit(f"expected {2 + len(CLUTTER)} overrides, wrote {len(log)}")
print(f"wrote {len(log)} overrides to {OUT}")
