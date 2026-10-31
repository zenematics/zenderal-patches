"""Generate the Tipped Waterfall Fix plugin YAML and its mesh -- never hand-edit TippedWaterfallFixESP/.

Curator's report (2026-10-31, the stream over the mill-dam walls in MQ01Campsite 015D43, near Finn and Carbos):
water "defying gravity", a white sheet sprayed out sideways from the wall top. SureAI built that stream from the
thin waterfall FXWaterfallThin256x128 (MSTT 1033F2:Skyrim.esm, Effects\\FXWaterfallThin256x128.nif) laid on its
side: refs 072D1D (X rotation -1.46), 072D1E (+1.46) and 072D1F (Y 1.44), i.e. tipped ~84 degrees so the falling
sheet reads as flowing water. "Water for ENB - Particle Waterfalls" replaces that mesh with a particle emitter,
which keeps spraying along the mesh's own down axis: sideways once tipped.

Fix, leaving the particle waterfalls everywhere else: a copy of 1033F2 (new MSTT 0x800) pointing at Enderal's own
mesh (from E - Meshes.bsa) under a new path, and the three refs repointed to it, each verbatim from Skyrim.esm
otherwise. No list plugin overrides the refs or 1033F2; the cell's other overrider, DynDOLOD.esm, carries a header
byte-identical to Skyrim.esm's (binary load-order scan, 2026-10-31), so Skyrim.esm's header is forwarded. The WRLD
header is Skyrim.esm's: load this plugin before DynDOLOD.esp, whose WRLD (and Occlusion's, and Vyn Full Extend's)
then still win.

About 50 more 1033F2 refs across Vyn are tipped more than 20 degrees (scan of reference/base, 2026-10-31); only this
spot is patched. Add a cell's refs to a list like REFS here if another one sprays sideways.

Usage: python 01-build-tipped-waterfall-fix.py [<MO2 mod folder to write the mesh into>]
"""
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
BASE = os.path.join(ROOT, "reference", "base", "Skyrim")
WS = "Vyn - 001D3C_Skyrim.esm"
CELL = ("-1, 0", "-4, 0", "MQ01Campsite - 015D43_Skyrim.esm")
PLUGIN = "Zenderal - Tipped Waterfall Fix.esp"
OUT = os.path.join(ROOT, "src", "TippedWaterfallFix", "TippedWaterfallFixESP")
REFS = ["072D1D", "072D1E", "072D1F"]
NEW = "000800:" + PLUGIN
EDID = "ZEN_FXWaterfallThin256x128Flat"
MESH = "Effects\\Zenderal\\FXWaterfallThin256x128Flat.nif"
CRLF = "\r\n"
SECTIONS = re.compile(r"^(Temporary|Persistent|NavigationMeshes|Landscape|SubCells|TopCell|MajorFlags):")


def read(path):
    with open(path, "r", encoding="utf-8", newline="") as f:
        return f.read().replace(CRLF, "\n").replace("\n", CRLF)


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def header(text):
    out = []
    for line in text.split(CRLF):
        if SECTIONS.match(line):
            break
        out.append(line)
    return CRLF.join(out).rstrip(CRLF) + CRLF


def ref_block(text, fk):
    """The '- MutagenObjectType:' item with this FormKey under Temporary, verbatim."""
    lines = text.split(CRLF)
    for i, line in enumerate(lines):
        if line == "  FormKey: %s:Skyrim.esm" % fk and lines[i - 1].startswith("- MutagenObjectType:"):
            j = i + 1
            while j < len(lines) and lines[j].startswith("  "):
                j += 1
            return lines[i - 1:j]
    raise SystemExit(fk + ": not found in the cell")


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    write(os.path.join(OUT, "RecordData.yaml"), CRLF.join([
        "SpriggitSource:", "  PackageName: Spriggit.Yaml.Skyrim", "  Version: 0.40", "ModKey: " + PLUGIN,
        "GameRelease: EnderalSE", "ModHeader:", "  Flags:", "  - Small", "  Stats:", "    Version: 1.7",
        "  Author: Zenderal",
        "  Description: SureAI's tipped thin waterfalls at the MQ01 campsite mill dam use Enderal's own mesh again.",
        "  MasterReferences:", "  - Master: Skyrim.esm", "    FileSize: 0", "  - Master: Update.esm", "    FileSize: 0",
        "  - Master: Enderal - Forgotten Stories.esm", "    FileSize: 0", "  INTV: 1", ""]))
    write(os.path.join(OUT, "spriggit-meta.json"), "{" + CRLF + '  "PackageName": "Spriggit.Yaml.Skyrim",' + CRLF +
          '  "Version": "0.40.0",' + CRLF + '  "Release": "EnderalSE",' + CRLF + '  "ModKey": "' + PLUGIN + '"' + CRLF + "}")

    # the new waterfall base: 1033F2 verbatim, new FormKey/EditorID/model path
    src = read(os.path.join(BASE, "MoveableStatics", "FXWaterfallThin256x128 - 1033F2_Skyrim.esm.yaml"))
    new, n = re.subn(r"(?m)^FormKey: 1033F2:Skyrim\.esm(?=\r?$)", "FormKey: " + NEW, src)
    new, m = re.subn(r"(?m)^EditorID: FXWaterfallThin256x128(?=\r?$)", "EditorID: " + EDID, new)
    new, k = re.subn(r"(?m)^  File: Effects\\FXWaterfallThin256x128\.nif(?=\r?$)", lambda _: "  File: " + MESH, new)
    assert (n, m, k) == (1, 1, 1), (n, m, k)
    write(os.path.join(OUT, "MoveableStatics", "%s - 000800_%s.yaml" % (EDID, PLUGIN)), new)

    ws_in = os.path.join(BASE, "Worldspaces", WS)
    ws_out = os.path.join(OUT, "Worldspaces", WS)
    write(os.path.join(ws_out, "RecordData.yaml"), header(read(os.path.join(ws_in, "RecordData.yaml"))))
    for rel in [(CELL[0], "GroupRecordData.yaml"), (CELL[0], CELL[1], "GroupRecordData.yaml")]:
        os.makedirs(os.path.join(ws_out, *rel[:-1]), exist_ok=True)
        shutil.copyfile(os.path.join(ws_in, *rel), os.path.join(ws_out, *rel))
    cell = read(os.path.join(ws_in, *CELL, "RecordData.yaml"))
    body = ["Temporary:"]
    for fk in REFS:
        blk = ref_block(cell, fk)
        hits = [i for i, l in enumerate(blk) if l == "  Base: 1033F2:Skyrim.esm"]
        assert len(hits) == 1 and not any("EnableParent" in l or "Disabled" in l for l in blk), fk
        blk[hits[0]] = "  Base: " + NEW
        rot = next(l for l in blk if l.startswith("    Rotation: "))
        rx, ry = (abs(float(v)) for v in rot.split(": ")[1].split(", ")[:2])
        assert max(rx, ry) > 1.0, (fk, rot)  # only tipped ones
        body += blk
    write(os.path.join(ws_out, *CELL, "RecordData.yaml"), header(cell) + CRLF.join(body) + CRLF)
    print("wrote %d repointed refs + MSTT %s to %s" % (len(REFS), NEW, OUT))

    if len(sys.argv) > 1:  # Enderal's own mesh into the MO2 mod (E - Meshes.bsa wins over Skyrim - Meshes0.bsa)
        sys.path.insert(0, os.path.join(ROOT, "src", "EnderalTextureRestores", "tools"))
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "etr", os.path.join(ROOT, "src", "EnderalTextureRestores", "tools", "01-extract-enderal-textures.py"))
        etr = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(etr)
        blob = etr.read_from_bsa("E:/Zenderal/Stock game/Data/E - Meshes.bsa",
                                 "meshes\\effects\\fxwaterfallthin256x128.nif")
        assert blob[:20].startswith(b"Gamebryo File Format"), blob[:20]
        dest = os.path.join(sys.argv[1], "meshes", *MESH.lower().split("\\"))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        open(dest, "wb").write(blob)
        print("mesh (%d bytes) -> %s" % (len(blob), dest))


if __name__ == "__main__":
    main()
