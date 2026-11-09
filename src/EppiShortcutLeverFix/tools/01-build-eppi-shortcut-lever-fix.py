r"""Generate the EPPI Shortcut Lever Fix plugin YAML -- never hand-edit its Worldspaces/.

Player report (GreaseLord, 2026-11-06): "you can open old dams water house from beyond the gate". EPPI Obstacles and
Shortcuts (EPPIareadividerandconnectors.esp) closes a Nordic hall end in Vyn cell (-27, 3) with a portcullis
(NorPortcullis 0093E9, activate parent = the pull bar) and puts its pull bar (NorPullBar01 0093EC, persistent) on the
inside wall 131 units behind the portcullis. The engine's activation reach is iActivatePickLength = 150 (base Enderal,
no list plugin changes it), so a player pressed against the bars from outside (east: meadow, skeleton-archer spawn)
could pull it and open the shortcut early.

This plugin moves only that pull bar 64 units further in along the same wall (dx -131 -> -195 from the portcullis, X
-109691.97 -> -109756.21; Y, Z, rotation and everything else verbatim from EPPI): about 200 from the bars, out of
reach, and still in front of EPPI's shaft beam at dx -216 (0093EA).
Headers are forwarded from each record's last overrider in the Ultra load order:
  WRLD Vyn 001D3C          <- Water for Enderal CS.esp (its own LodWater 000802 -> mastered)
  CELL 001D40 (persistent) <- Zenderal - Last Watch Trapdoor Fix.esp (repo YAML, src/LastWatchTrapdoorFix)
Re-serialize reference/mods/EPPIareadividerandconnectors and WaterForEnderalCS before re-running after either updates.
"""
import os
import re
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
WS = "Vyn - 001D3C_Skyrim.esm"
EPPI = os.path.join(ROOT, "reference", "mods", "EPPIareadividerandconnectors", "Worldspaces", WS, "RecordData.yaml")
EPPI_CELL = os.path.join(ROOT, "reference", "mods", "EPPIareadividerandconnectors", "Worldspaces", WS, "-1, 0", "-4, 0",
                         "015D41_Skyrim.esm", "RecordData.yaml")
WATER = os.path.join(ROOT, "reference", "mods", "WaterForEnderalCS", "Worldspaces", WS, "RecordData.yaml")
TOPCELL = os.path.join(ROOT, "src", "LastWatchTrapdoorFix", "LastWatchTrapdoorFixESP", "Worldspaces", WS, "RecordData.yaml")
OUT = os.path.join(ROOT, "src", "EppiShortcutLeverFix", "EppiShortcutLeverFixESP")
CRLF = "\r\n"
LEVER = "0093EC:EPPIareadividerandconnectors.esp"
GATE = "0093E9:EPPIareadividerandconnectors.esp"
OLD_X, NEW_X = "-109691.97", "-109756.21"
SECTIONS = re.compile(r"^(Temporary|Persistent|NavigationMeshes|Landscape|SubCells|TopCell|MajorFlags):")


def read(path):
    with open(path, "r", encoding="utf-8", newline="") as f:
        return f.read().replace(CRLF, "\n").replace("\n", CRLF)


def header(text):
    out = []
    for line in text.split(CRLF):
        if SECTIONS.match(line):
            break
        out.append(line)
    return CRLF.join(out).rstrip(CRLF) + CRLF


def block(text, fk):
    lines = text.split(CRLF)
    hits = [i for i, l in enumerate(lines) if l.strip() == "FormKey: " + fk and lines[i - 1].lstrip().startswith("- MutagenObjectType:")]
    if len(hits) != 1:
        raise SystemExit(f"{fk}: found {len(hits)} times")
    start = hits[0] - 1
    ind = lines[start][: len(lines[start]) - len(lines[start].lstrip())]
    end = start + 1
    while end < len(lines) and lines[end].startswith(ind + "  "):
        end += 1
    return [l[len(ind):] for l in lines[start:end]]


eppi = read(EPPI)
lever = block(eppi, LEVER)
if "  Base: 098668:Skyrim.esm" not in lever:
    raise SystemExit("0093EC is no longer EPPI's pull bar")
gate = "\n".join(block(read(EPPI_CELL), GATE))  # sanity: the gate still names the lever as its activate parent
if LEVER not in gate:
    raise SystemExit("the portcullis no longer hangs on that pull bar")
pos = [i for i, l in enumerate(lever) if l.startswith("    Position: ")]
if len(pos) != 1 or not lever[pos[0]].startswith(f"    Position: {OLD_X}, "):
    raise SystemExit(f"pull bar no longer at X {OLD_X}: {lever[pos[0]] if pos else None}")
lever[pos[0]] = lever[pos[0]].replace(OLD_X, NEW_X, 1)

top = read(TOPCELL)
top = top[top.index("TopCell:" + CRLF):]
top = top[: top.index(CRLF + "  Persistent:" + CRLF)] + CRLF
# Spriggit writes the persistent cell's flags (from MajorRecordFlagsRaw 0x40400) after its refs; same binary either way
trail = "  MajorFlags:" + CRLF + "  - Persistent" + CRLF + "  - 0x40000" + CRLF
lever = [l.replace("Rotation: 0, -0, ", "Rotation: 0, 0, ") for l in lever]  # Spriggit writes -0 as 0
wrld = header(read(WATER)) + top + "  Persistent:" + CRLF + CRLF.join("  " + l for l in lever) + CRLF + trail

if os.path.isdir(os.path.join(OUT, "Worldspaces")):
    shutil.rmtree(os.path.join(OUT, "Worldspaces"))
path = os.path.join(OUT, "Worldspaces", WS, "RecordData.yaml")
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "w", encoding="utf-8", newline="") as f:
    f.write(wrld)
print(f"{LEVER}: X {OLD_X} -> {NEW_X}")
