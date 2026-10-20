"""Generate the EPPI Riverville Cobble Removal plugin YAML -- never hand-edit its Worldspaces/.

Curator's taste (2026-10-20): EPPI Riverville (EPPIriverville.esp) paves Riverville with 98 placed
copies of its own static NorPlatBgFloorRaised01_EPPIrivervillecobble (STAT 029B46:EPPIriverville.esp,
model NorPlatBgFloorRaised01.nif): pale raised cobble plates laid over the streets of seven Riverville
exterior cells. The curator wants them gone.

This disables all 98 the xEdit way (InitiallyDisabled, enable parent PlayerRef opposite, z -30000),
copying every ref verbatim from EPPI. No list plugin overrides any of them (binary load-order scan,
2026-10-20). Headers are forwarded from each record's last overrider in the Ultra load order:
  WRLD Vyn 001D3C        <- Water for Enderal CS.esp (its own LodWater 000802 -> mastered)
  CELL 001EB1 / 001EA7   <- Zenderal - RiverBush.esp (repo YAML, src/RiverBush)
  CELL 001EB9 / 001E9C / 001EA6 / 001EB0 / 001EB2  <- EPPIriverville.esp
Re-check those winners (and re-serialize reference/mods/EPPIriverville + WaterForEnderalCS with
spriggit-decompile-reference) before re-running after a mod in Riverville changes.
"""
import os
import re
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
REF = os.path.join(ROOT, "reference", "mods")
WS = "Vyn - 001D3C_Skyrim.esm"
SUB = ("-1, -1", "-3, -1")
EPPI = os.path.join(REF, "EPPIriverville", "Worldspaces", WS)
WATER = os.path.join(REF, "WaterForEnderalCS", "Worldspaces", WS)
RIVERBUSH = os.path.join(ROOT, "src", "RiverBush", "RiverBushESP", "Worldspaces", WS)
OUT = os.path.join(ROOT, "src", "EppiRivervilleCobbleRemoval", "EppiRivervilleCobbleRemovalESP")
OUTWS = os.path.join(OUT, "Worldspaces", WS)
CRLF = "\r\n"
BASE = "  Base: 029B46:EPPIriverville.esp"
EXPECTED = 98
HEADER_FROM = {  # cell folder -> tree whose header wins
    "FlusshaimZentrum - 001EB1_Skyrim.esm": RIVERBUSH,
    "FlusshaimMittelweg - 001EA7_Skyrim.esm": RIVERBUSH,
    "001EB9_Skyrim.esm": EPPI,
    "FlusshaimEingang - 001E9C_Skyrim.esm": EPPI,
    "FlusshaimMarktplatz - 001EA6_Skyrim.esm": EPPI,
    "FlusshaimMarktplatz2 - 001EB0_Skyrim.esm": EPPI,
    "FlusshaimHonigpresse - 001EB2_Skyrim.esm": EPPI,
}
REF_SECTIONS = re.compile(r"^(Temporary|Persistent|NavigationMeshes|Landscape|SubCells|TopCell|MajorFlags):")


def read(path):
    with open(path, "r", encoding="utf-8", newline="") as f:
        return f.read().replace(CRLF, "\n").replace("\n", CRLF)  # src/RiverBush YAML is LF


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def header(text):
    """Record lines before the first child-record section."""
    out = []
    for line in text.split(CRLF):
        if REF_SECTIONS.match(line):
            break
        out.append(line)
    return CRLF.join(out).rstrip(CRLF) + CRLF


def trailer(text):
    i = text.find(CRLF + "MajorFlags:" + CRLF)
    return text[i + len(CRLF):] if i >= 0 else ""


def cobble_blocks(text):
    """Every '- MutagenObjectType:' item under Temporary whose Base is the cobble static, verbatim."""
    lines = text.split(CRLF)
    try:
        start = lines.index("Temporary:")
    except ValueError:
        return []
    blocks, i = [], start + 1
    while i < len(lines) and (lines[i].startswith("- ") or lines[i].startswith("  ")):
        if lines[i].startswith("- MutagenObjectType:"):
            j = i + 1
            while j < len(lines) and lines[j].startswith("  "):
                j += 1
            block = lines[i:j]
            if BASE in block:
                blocks.append(block)
            i = j
        else:
            i += 1
    return blocks


def disabled(block):
    fk = next(l for l in block if l.startswith("  FormKey: "))[len("  FormKey: "):]
    if any("InitiallyDisabled" in l or l.startswith("  EnableParent:") for l in block):
        raise SystemExit(f"{fk}: already disabled or enable-parented upstream; re-check before building")
    out, n_flag, n_ep, n_z = [], 0, 0, 0
    raw = "  MajorRecordFlagsRaw: 2048"
    anchor = next((l for l in block if l.startswith("  VersionControl:")), raw)
    for l in block:
        if l == "  FormKey: " + fk:
            out += [l, raw]
            if anchor == raw:
                out += ["  SkyrimMajorRecordFlags:", "  - InitiallyDisabled"]
                n_flag += 1
            continue
        if l.startswith("  MajorRecordFlagsRaw:") or l.startswith("  SkyrimMajorRecordFlags:"):
            raise SystemExit(f"{fk}: ref already carries record flags; merge by hand")
        if l.startswith("  Placement:"):
            out += ["  EnableParent:", "    Reference: 000014:Skyrim.esm", "    Flags:",
                    "    - SetEnableStateToOppositeOfParent", "    Unknown: 0x000000"]
            n_ep += 1
        m = re.match(r"^(    Position: [^,]+, [^,]+, )(.+)$", l)
        if m:
            l = m.group(1) + "-30000"
            n_z += 1
        out.append(l)
        if l == anchor:
            out += ["  SkyrimMajorRecordFlags:", "  - InitiallyDisabled"]
            n_flag += 1
    if (n_flag, n_ep, n_z) != (1, 1, 1):
        raise SystemExit(f"{fk}: edit counts {n_flag}/{n_ep}/{n_z}, expected 1/1/1")
    return out


if os.path.isdir(os.path.join(OUT, "Worldspaces")):
    shutil.rmtree(os.path.join(OUT, "Worldspaces"))

write(os.path.join(OUTWS, "RecordData.yaml"), header(read(os.path.join(WATER, "RecordData.yaml"))))
for rel in [(SUB[0], "GroupRecordData.yaml"), (SUB[0], SUB[1], "GroupRecordData.yaml")]:
    os.makedirs(os.path.join(OUTWS, *rel[:-1]), exist_ok=True)
    shutil.copyfile(os.path.join(EPPI, *rel), os.path.join(OUTWS, *rel))

total = 0
for cell, htree in HEADER_FROM.items():
    eppi_text = read(os.path.join(EPPI, *SUB, cell, "RecordData.yaml"))
    blocks = cobble_blocks(eppi_text)
    if not blocks:
        raise SystemExit(f"{cell}: no cobble refs found")
    body = ["Temporary:"]
    for b in blocks:
        body += disabled(b)
    head_text = read(os.path.join(htree, *SUB, cell, "RecordData.yaml"))
    write(os.path.join(OUTWS, *SUB, cell, "RecordData.yaml"), header(head_text) + CRLF.join(body) + CRLF + trailer(head_text))
    total += len(blocks)
    print(f"{cell}: {len(blocks)} cobble refs disabled (header from {os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(htree))))})")

if total != EXPECTED:
    raise SystemExit(f"expected {EXPECTED} disabled refs, wrote {total}")
print(f"wrote {total} disabled refs to {OUTWS}")
