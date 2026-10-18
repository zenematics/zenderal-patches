"""Generate the Perpetuum Theater EVGAT Fix plugin YAML.

EVG Animated Traversal - Enderal Addon 2.3 (EVGAT_Enderal.esp) places four refs in Ark's Nobles
Quarter that were laid out against base Enderal's old theater: plank 0009CC and sign post 0009CD
(a climbing scaffold) and two 867x1202 collision planes 0009CA / 0009CB. The Perpetuum Theater
rebuilds that area and its own EVGAT patch (1.0) does not touch these four, so the plank and post
hang in the air and the planes stand as invisible walls in the new courtyard.

This disables all four the xEdit way (InitiallyDisabled, enable parent PlayerRef opposite, z -30000),
and forwards the winning cell / worldspace headers verbatim:
  WRLD 07072B  <- Perpetuum Theater - Enderal TAT CM Fixes.esp (last overrider)
  CELL 07076D  <- Perpetuum Theater - Enderal TAT CM Fixes.esp (last overrider)
  CELL 070770  <- EVGAT_Enderal.esp (last overrider)

Reads the serialized plugins in reference/mods/ (gitignored); re-serialize them with
spriggit-decompile-reference before re-running.
"""
import os
import re
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
REF = os.path.join(ROOT, "reference", "mods")
WSNAME = "CapitalCityUpperCity - 07072B_Skyrim.esm"
EVGAT = os.path.join(REF, "EVGATEnderal", "Worldspaces", WSNAME)
THETATU = os.path.join(REF, "PerpetuumTheaterETATU", "Worldspaces", WSNAME)
OUT = os.path.join(ROOT, "src", "PerpetuumTheaterEVGATFix", "PerpetuumTheaterEVGATFixESP")
OUTWS = os.path.join(OUT, "Worldspaces", WSNAME)
CRLF = "\r\n"
SUB = ("-1, -1", "-1, -1")
CELL_76D = "07076D_Skyrim.esm"
CELL_770 = "UpperQuarterWatchtower - 070770_Skyrim.esm"
REF_SECTIONS = re.compile(r"^(Temporary|Persistent|NavigationMeshes|Landscape|SubCells|TopCell|MajorFlags):")


def read(path):
    with open(path, "r", encoding="utf-8", newline="") as f:
        return f.read()


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
    """The MajorFlags block that closes a cell file, if any."""
    i = text.find(CRLF + "MajorFlags:" + CRLF)
    return text[i + len(CRLF):] if i >= 0 else ""


def ref_block(text, fk):
    """One '- MutagenObjectType:' list item under Temporary, verbatim."""
    lines = text.split(CRLF)
    start = next(i for i, l in enumerate(lines) if l == "  FormKey: " + fk) - 1
    if not lines[start].startswith("- MutagenObjectType:"):
        raise SystemExit(f"{fk}: unexpected layout above FormKey")
    end = start + 1
    while end < len(lines) and lines[end].startswith("  "):
        end += 1
    return lines[start:end]


def disabled(block, fk):
    """Insert the xEdit-style disable into a verbatim ref block; assert each edit lands once."""
    if any("InitiallyDisabled" in l or l.startswith("  EnableParent:") for l in block):
        raise SystemExit(f"{fk}: already disabled or enable-parented upstream; re-check before building")
    out = []
    n_flag = n_ep = n_z = 0
    # Spriggit's order: FormKey, MajorRecordFlagsRaw, [VersionControl], SkyrimMajorRecordFlags.
    raw = "  MajorRecordFlagsRaw: 2048"
    anchor = next((l for l in block if l.startswith("  VersionControl:")), raw)
    for l in block:
        if l == "  FormKey: " + fk:
            out += [l, raw]
            if anchor == raw:
                out += ["  SkyrimMajorRecordFlags:", "  - InitiallyDisabled"]
                n_flag += 1
            continue
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


def cell(src_header_file, src_ref_file, fks):
    text = read(src_header_file)
    refs_text = read(src_ref_file)
    body = ["Temporary:"]
    for fk in fks:
        body += disabled(ref_block(refs_text, fk), fk)
    return header(text) + CRLF.join(body) + CRLF + trailer(text)


if os.path.isdir(os.path.join(OUT, "Worldspaces")):
    shutil.rmtree(os.path.join(OUT, "Worldspaces"))

# Worldspace header + block/sub-block scaffolding (Spriggit drops the tree without them).
write(os.path.join(OUTWS, "RecordData.yaml"), header(read(os.path.join(THETATU, "RecordData.yaml"))))
for rel in [(SUB[0], "GroupRecordData.yaml"), (SUB[0], SUB[1], "GroupRecordData.yaml")]:
    os.makedirs(os.path.join(OUTWS, *rel[:-1]), exist_ok=True)
    shutil.copyfile(os.path.join(EVGAT, *rel), os.path.join(OUTWS, *rel))

write(os.path.join(OUTWS, *SUB, CELL_76D, "RecordData.yaml"),
      cell(os.path.join(THETATU, *SUB, CELL_76D, "RecordData.yaml"),
           os.path.join(EVGAT, *SUB, CELL_76D, "RecordData.yaml"),
           ["0009CA:EVGAT_Enderal.esp", "0009CC:EVGAT_Enderal.esp", "0009CD:EVGAT_Enderal.esp"]))
write(os.path.join(OUTWS, *SUB, CELL_770, "RecordData.yaml"),
      cell(os.path.join(EVGAT, *SUB, CELL_770, "RecordData.yaml"),
           os.path.join(EVGAT, *SUB, CELL_770, "RecordData.yaml"),
           ["0009CB:EVGAT_Enderal.esp"]))

n = sum(read(os.path.join(dp, f)).count("- InitiallyDisabled") for dp, _, fs in os.walk(OUTWS) for f in fs)
if n != 4:
    raise SystemExit(f"expected 4 disabled refs, wrote {n}")
print("wrote 4 disabled refs to", OUTWS)
