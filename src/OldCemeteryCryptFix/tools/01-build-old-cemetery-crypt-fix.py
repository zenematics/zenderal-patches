"""Generate the Old Cemetery Crypt Fix plugin YAML.

ETATU's Complex Material plugin (Enderal TAT CM Fixes.esp, "Save compatible" 0.92a) re-bases the Old
Cemetery's house shell 016A98 (cell Friedhof 001FF8, Vyn) from SStyrrsHouse 037F05 to its own static
0039C5 "SStyrrsHouse ark", whose model Architecture\\Solitude\\SStyrrsHouse ark.nif ships in no ETATU
archive. A missing mesh renders nothing, so only the crypt door 01D188 is left standing in the open.

This copies ETATU's override of 016A98 verbatim and points Base back at 037F05:Skyrim.esm. The cell and
worldspace headers are forwarded verbatim from ETATU, the last overrider of both (FS and
GargoylesInEnderal touch the cell earlier; nothing after ETATU does).

Reads reference/mods/ETATUCMFixes (gitignored); re-serialize it with spriggit-decompile-reference
before re-running.
"""
import os
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
WSNAME = "Vyn - 001D3C_Skyrim.esm"
ETATU = os.path.join(ROOT, "reference", "mods", "ETATUCMFixes", "Worldspaces", WSNAME)
OUT = os.path.join(ROOT, "src", "OldCemeteryCryptFix", "OldCemeteryCryptFixESP")
OUTWS = os.path.join(OUT, "Worldspaces", WSNAME)
SUB = ("-1, -1", "-1, -1")
CELL = "Friedhof - 001FF8_Skyrim.esm"
REF = "016A98:Skyrim.esm"
OLD_BASE = "  Base: 0039C5:Enderal TAT CM Fixes.esp"
NEW_BASE = "  Base: 037F05:Skyrim.esm"
CRLF = "\r\n"


def read(path):
    with open(path, "r", encoding="utf-8", newline="") as f:
        return f.read()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


if os.path.isdir(os.path.join(OUT, "Worldspaces")):
    shutil.rmtree(os.path.join(OUT, "Worldspaces"))

# Worldspace header + block/sub-block scaffolding (Spriggit drops the tree without them).
write(os.path.join(OUTWS, "RecordData.yaml"), read(os.path.join(ETATU, "RecordData.yaml")))
for rel in [(SUB[0], "GroupRecordData.yaml"), (SUB[0], SUB[1], "GroupRecordData.yaml")]:
    os.makedirs(os.path.join(OUTWS, *rel[:-1]), exist_ok=True)
    shutil.copyfile(os.path.join(ETATU, *rel), os.path.join(OUTWS, *rel))

cell = read(os.path.join(ETATU, *SUB, CELL, "RecordData.yaml"))
if cell.count("  FormKey: ") != 1 or ("  FormKey: " + REF + CRLF) not in cell:
    raise SystemExit(f"ETATU's {CELL} no longer holds exactly {REF}; re-check before building")
if cell.count(OLD_BASE + CRLF) != 1:
    raise SystemExit(f"{REF}: expected ETATU's base 0039C5 once; ETATU may have fixed it - retire this patch?")
write(os.path.join(OUTWS, *SUB, CELL, "RecordData.yaml"), cell.replace(OLD_BASE + CRLF, NEW_BASE + CRLF))
print(f"wrote {REF} -> 037F05 SStyrrsHouse in", OUTWS)
