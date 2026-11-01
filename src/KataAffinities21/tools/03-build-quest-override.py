"""Generate the AffinityControl 01597B override for Zenderal - KataPUMB Affinities 2.1 -- never hand-edit it.

The ported _00E_AffinityControl (tools/01) declares Kata's 24 affinity spells and 48 name messages as
properties. This copies FS's quest record verbatim (no list plugin overrides 01597B -- binary scan of
the Ultra load order, 2026-10-20) and appends those 72 properties to alias 0's script, each filled with
the KataPUMBAffinities.esp record whose EditorID equals the property name.

Inputs: reference/base-2.1.4.4/EnderalFS (FS 2.1.4.4), reference/mods/KataPUMBAffinities (Kata's esp
serialized), the ported psc. Output: KataAffinities21ESP/Quests/.
"""
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
FS_QUEST = os.path.join(ROOT, "reference", "base-2.1.4.4", "EnderalFS", "Quests", "AffinityControl - 01597B_Enderal - Forgotten Stories.esm.yaml")
KATA = os.path.join(ROOT, "reference", "mods", "KataPUMBAffinities")
PSC = os.path.join(ROOT, "src", "KataAffinities21", "Scripts", "source", "_00E_AffinityControl.psc")
OUT = os.path.join(ROOT, "src", "KataAffinities21", "KataAffinities21ESP", "Quests", os.path.basename(FS_QUEST))
CRLF = "\r\n"
EXPECTED = 72

psc = open(PSC, encoding="cp1252").read()
kata_block = psc[psc.rindex(";KATAPUMB NEW AFFINITIES"):]  # the property block tools/01 appends last
props = re.findall(r"^(Spell|Message) Property (\w+) auto", kata_block, re.M | re.I)

records = {}
for kind in ("Spells", "Messages"):
    for n in os.listdir(os.path.join(KATA, kind)):
        m = re.match(r"(.+) - ([0-9A-F]{6})_(.+)\.yaml$", n)
        if m:
            records[(kind, m.group(1))] = f"{m.group(2)}:{m.group(3)}"

lines = []
for typ, name in props:
    fk = records.get(("Spells" if typ.lower() == "spell" else "Messages", name))
    if not fk:
        sys.exit(f"property {name}: no {typ} with that EditorID in KataPUMBAffinities.esp")
    lines += ["      - MutagenObjectType: ScriptObjectProperty", f"        Name: {name}", f"        Object: {fk}"]
if len(props) != EXPECTED:
    sys.exit(f"expected {EXPECTED} Kata properties in the ported script, found {len(props)}")

text = open(FS_QUEST, encoding="utf-8", newline="").read().replace(CRLF, "\n")
L = text.split("\n")
start = L.index("    - Name: _00E_AffinityControl")
if L[start + 1] != "      Properties:":
    sys.exit("alias 0's _00E_AffinityControl has no Properties list")
end = start + 2
while end < len(L) and L[end].startswith("      "):
    end += 1
names = {l.split(": ", 1)[1] for l in L[start:end] if l.startswith("        Name: ")}
clash = names & {n for _, n in props}
if clash:
    sys.exit(f"FS already fills {sorted(clash)}")
blocks = [L[i:i + 3] for i in range(start + 2, end, 3)] + [lines[i:i + 3] for i in range(0, len(lines), 3)]
if any(b[0] != "      - MutagenObjectType: ScriptObjectProperty" or not b[1].startswith("        Name: ") for b in blocks):
    sys.exit("unexpected property layout (expected 3-line object properties)")
blocks.sort(key=lambda b: b[1].split(": ", 1)[1].lower())  # Spriggit writes properties case-insensitively sorted
L[start + 2:end] = [l for b in blocks for l in b]
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8", newline="") as f:
    f.write(CRLF.join(L))
print(f"appended {len(props)} Kata properties to alias 0 of AffinityControl -> {OUT}")
