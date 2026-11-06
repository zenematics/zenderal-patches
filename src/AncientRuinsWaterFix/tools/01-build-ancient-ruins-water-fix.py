"""Generate the Ancient Ruins Water Fix plugin YAML -- never hand-edit its Cells/.

Player reports (Longinus, GreaseLord, 2026-11-06): "Ancient Ruins looks horrible, probably water texture
overlapping". Ancient Ruins is Myths and Legends VI - The Forgotten One's interior cell 001460 (aaaeew, the
level-50 Forgotten One's lair); all 827 of its records are the mod's and nothing else in the list edits them
(load-order scan 2026-11-06).

The courtyard is a shallow flooded pond: placed water plane 022487 (Water1024, ~3040 units square at height 56.42)
over a floor 0-32 units below the surface, 15 lily pads on it, and 9 of Enderal's sea-floor sponges
(_00E_Underwater_Fingersponge02 0F8F8C, a TREE) rooted at -23 through the floor. In this list the plane draws as a
flat sheet with hard straight edges wherever the floor dips below it (whatever water type: build 3 put DefaultWater
back over Water for Enderal's dark interior type and the edges stayed), and the sponges render flat black at range
and vanish up close (also with the water system off).

Build 6 (curator 2026-11-06, after the mist removal fixed the look): the pond plane and its lily pads are back as
the mod has them; DISABLE lists what stays off. Before that, this disabled the whole pond set-dressing the xEdit way (InitiallyDisabled, enable parent PlayerRef opposite,
z -30000): the plane, the 15 lily pads on its surface, the 6 NicoWave shore-foam strips at its edge (they drew
white segmented lines on dry stone once the water was gone), the 9 sponges, and the courtyard's mist: 7
FXAmbBeamWetMistBig02 beams and the low FXMistLowWet01 022384. Particle Patch's versions of those two meshes double
their brightness and drop the palette tint, tuned for ENB's [PARTICLE] lighting, which this list's Bottled Shaders
does not apply; in this dark interior they drew as white walls (curator, 2026-11-06). Cell only, at the curator's
choice; the meshes stay Particle Patch's everywhere else. Everything else in the cell stays the mod's.
The cell header is copied verbatim (Spriggit needs it for the references). Re-serialize the mod into
reference/mods/MythsAndLegendsVI before re-running.

History: build 1 removed the cell's HasWater (water at 0, under the floor: no change); build 2 shrank the plane
(edges still cut the floor); build 3 gave the plane DefaultWater through activator 0x800 (lighter, same edges).
0x800 (ZEN_Water1024DefaultWater) is retired: never reuse it.
"""
import glob
import os
import re
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
ESP = os.path.join(ROOT, "src", "AncientRuinsWaterFix", "AncientRuinsWaterFixESP")
MOD = os.path.join(ROOT, "reference", "mods", "MythsAndLegendsVI", "Cells")
CELL = "aaaeew - 001460_Myths and Legends VI - The Forgotten One.esp"
POND = "022487:Myths and Legends VI - The Forgotten One.esp"
POND_Z = 56.4189
SPONGE = "0F8F8C:Skyrim.esm"
LILIES = {"03765B", "037652", "037659", "03764D", "037653", "037664", "037662", "037655", "037656", "03765E",
          "037667", "037660", "037658"}                # Enderal's water lily statics
WAVES = {"0BEC29", "0BEC26", "0BEC22", "0C560E", "0C560D"}  # Enderal's NicoWave01-05 shore foam strips
MIST_BEAM = "0777B2:Skyrim.esm"                       # FXAmbBeamWetMistBig02
MIST_LOW = "0B944D:Skyrim.esm"                        # FXMistLowWet01 (the courtyard one lies under the pond, z < 100)
EXPECT = {"pond": 1, "lily": 15, "sponge": 9, "wave": 6, "mist": 8}
DISABLE = ("sponge", "wave", "mist")                 # pond + lilies back since build 6 (curator 2026-11-06)
SECTIONS = re.compile(r"^(Temporary|Persistent|NavigationMeshes|Landscape|SubCells|TopCell|MajorFlags):")
DISABLED = 0x800


def read(path):
    return open(path, encoding="utf-8", newline="").read()


src = glob.glob(os.path.join(MOD, "*", "*", CELL, "RecordData.yaml"))
if len(src) != 1:
    raise SystemExit(f"expected the mod's cell 001460 once, found {len(src)}")
block, sub = src[0].split(os.sep)[-4:-2]
text = read(src[0])
nl = "\r\n" if "\r\n" in text else "\n"
lines = text.split(nl)
head = []
for line in lines:
    if SECTIONS.match(line):
        break
    head.append(line)
head = nl.join(head).rstrip(nl) + nl
if "FormKey: 001460:Myths and Legends VI - The Forgotten One.esp" not in head:
    raise SystemExit("header is not cell 001460")

# placed objects with the section they sit in
blocks, cur, section = [], None, None
for line in lines:
    m = SECTIONS.match(line)
    if m:
        section, cur = m.group(1), None
        continue
    if line.startswith("- MutagenObjectType: Placed"):
        cur = [line]
        blocks.append((section, cur))
    elif cur is not None and line.startswith("- "):
        cur = None
    elif cur is not None:
        cur.append(line)


def field(b, prefix):
    hits = [l for l in b if l.startswith(prefix)]
    return hits[0].split(": ", 1)[1] if len(hits) == 1 else None


def kind(b):
    if f"  FormKey: {POND}" in b:
        return "pond"
    base = field(b, "  Base: ")
    pos = field(b, "    Position: ")
    if base == SPONGE:
        return "sponge"
    if base and base[:6] in LILIES and base.endswith(":Skyrim.esm") and pos and abs(float(pos.split(",")[2]) - POND_Z) < 1.0:
        return "lily"
    if base and base[:6] in WAVES and base.endswith(":Skyrim.esm") and pos and abs(float(pos.split(",")[2]) - POND_Z) < 1.0:
        return "wave"
    if base == MIST_BEAM or (base == MIST_LOW and pos and float(pos.split(",")[2]) < 100.0):
        return "mist"
    return None


def disabled(b):
    fk = field(b, "  FormKey: ")
    if any("InitiallyDisabled" in l or l.startswith("  EnableParent:") for l in b):
        raise SystemExit(f"{fk}: already disabled or enable-parented upstream; re-check")
    raw = field(b, "  MajorRecordFlagsRaw: ")
    raw = int(raw) if raw else 0
    old_flags, out, i = [], [], 0
    while i < len(b):
        l = b[i]
        if l.startswith("  MajorRecordFlagsRaw:"):
            i += 1
            continue
        if l.startswith("  SkyrimMajorRecordFlags:"):
            i += 1
            while i < len(b) and b[i].startswith("  - "):
                old_flags.append(b[i])
                i += 1
            continue
        out.append(l)
        i += 1
    flags = ["  MajorRecordFlagsRaw: " + str(raw | DISABLED), "  SkyrimMajorRecordFlags:"] + old_flags + ["  - InitiallyDisabled"]
    res, n_ep, n_z = [], 0, 0
    for l in out:
        if l.startswith("  FormKey: "):
            res += [l] + flags
            continue
        if l.startswith("  Placement:"):
            res += ["  EnableParent:", "    Reference: 000014:Skyrim.esm", "    Flags:",
                    "    - SetEnableStateToOppositeOfParent", "    Unknown: 0x000000"]
            n_ep += 1
        m = re.match(r"^(    Position: [^,]+, [^,]+, )(.+)$", l)
        if m:
            l = m.group(1) + "-30000"
            n_z += 1
        res.append(l)
    if (n_ep, n_z) != (1, 1):
        raise SystemExit(f"{fk}: edit counts {n_ep}/{n_z}, expected 1/1")
    return res


picked = {"pond": [], "lily": [], "sponge": [], "wave": [], "mist": []}
for sec, b in blocks:
    k = kind(b)
    if k:
        picked[k].append((sec, b))
counts = {k: len(v) for k, v in picked.items()}
if counts != EXPECT:
    raise SystemExit(f"expected {EXPECT}, found {counts}")

by_section = {}
for k in DISABLE:
    for sec, b in picked[k]:
        by_section.setdefault(sec, []).extend(disabled(b))

for d in ("Activators", "Cells"):
    if os.path.isdir(os.path.join(ESP, d)):
        shutil.rmtree(os.path.join(ESP, d))
out = os.path.join(ESP, "Cells")
os.makedirs(os.path.join(out, block, sub, CELL))
for rel in ("", block, os.path.join(block, sub)):      # the Cells group scaffolding, copied from the mod
    shutil.copyfile(os.path.join(MOD, rel, "GroupRecordData.yaml"), os.path.join(out, rel, "GroupRecordData.yaml"))
body = head
for sec in ("Persistent", "Temporary"):
    if sec in by_section:
        body += sec + ":" + nl + nl.join(by_section[sec]) + nl
open(os.path.join(out, block, sub, CELL, "RecordData.yaml"), "w", encoding="utf-8", newline="").write(body)
print("disabled:", counts, "sections:", {s: sum(1 for l in v if l.startswith("- MutagenObjectType")) for s, v in by_section.items()})
