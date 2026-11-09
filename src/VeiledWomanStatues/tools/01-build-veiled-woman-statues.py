"""Generate `VeiledWomanStatuesESP/`: the Veiled Woman statues back where SureAI placed them.

Player report (Discord, evLRise, 2026-10-23, "Lorebreaking Statue Model"): Enderal shows the Veiled Woman with one
statue - Skyrim's Statue of Meridia mesh, base `LoadScreenStatueofMeridia01 10A17A` - in the ruins tied to her, and
seeing the same figure again and again is how players connect her to those places (Old Sherath above all).
"Mandragorasprouts' Statues for Enderal" (`man_DaedricShrines_Enderal.esp`, Enderal Nexus 618) disables six of those
placements and puts other gods in their spots - Nocturnal ("fits the Veiled Woman more", says its page) in four places
and Kynareth in Old Sherath - and also replaces the Meridia mesh itself (tools/02 restores that).

For each of the four cells (live chains scanned 2026-11-08):
  * the cell header = its current winner's record verbatim (the statue mod, Castle Bleakstar, EVGAT_Enderal);
  * SureAI's placements the mod disabled = base Enderal 2.1 / Forgotten Stories' record verbatim (enabled, original
    position) - the six Meridia statues and the ruin brick the mod hid next to one of them;
  * the mod's replacement statues = its own record with InitiallyDisabled, as it disables SureAI's.
The mod's other statues (Mara, Sanguine, Azura, Hircine, ...) stay. Every chain is asserted, so a new plugin touching
these records stops the build. Load after the statue mod, Castle Bleakstar and EVGAT_Enderal (all masters).

Usage: python 01-build-veiled-woman-statues.py
"""
import os
import re
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
REF = os.path.join(ROOT, "reference")
OUT = os.path.join(ROOT, "src", "VeiledWomanStatues", "VeiledWomanStatuesESP")
FS = "Enderal - Forgotten Stories.esm"
MOD = "man_DaedricShrines_Enderal.esp"
TREES = {
    "Skyrim.esm": os.path.join(REF, "base-2.1.4.4", "Skyrim"),
    FS: os.path.join(REF, "base-2.1.4.4", "EnderalFS"),
    MOD: os.path.join(REF, "mods", "MandragoraStatues"),
    "Castle Bleakstar.esp": os.path.join(REF, "mods", "CastleBleakstar"),
    "EVGAT_Enderal.esp": os.path.join(REF, "mods", "EVGATEnderal"),
}
# cell -> (header winner, [(ref, plugin to copy it from)], [mod refs to disable])
CELLS = {
    "028E8B:" + FS: ("Castle Bleakstar.esp",
                     [("029766", FS), ("029768", FS), ("029B8E", FS), ("029B8F", FS)],
                     ["000807", "00080E", "00080F"]),
    "0A5894:Skyrim.esm": (MOD, [("029953", FS)], ["000806"]),
    "028441:" + FS: (MOD, [("02977A", FS)], ["000805"]),
    "043DEF:Skyrim.esm": ("EVGAT_Enderal.esp", [("0440BF", "Skyrim.esm")], ["000808"]),
}
REF_OWNER = {"029766": FS, "029768": FS, "029B8E": FS, "029B8F": FS, "029953": FS, "02977A": FS, "0440BF": "Skyrim.esm"}
BASE_STATUE = "Base: 10A17A:Skyrim.esm"
LOAD_ORDER = ["Skyrim.esm", "Update.esm", FS, MOD, "Castle Bleakstar.esp", "EVGAT_Enderal.esp"]  # live order, checked


def cell_dir(plugin, cell_fk):
    fid, owner = cell_fk.split(":", 1)
    hits = []
    for dp, dirs, _ in os.walk(os.path.join(TREES[plugin], "Cells")):
        hits += [os.path.join(dp, d) for d in dirs if d.endswith(f"{fid}_{owner}")]
    if len(hits) != 1:
        sys.exit(f"{cell_fk}: expected one cell folder in {plugin}'s tree, found {len(hits)}")
    return hits[0]


def split(text):
    """-> (header text without the ref lists, {list name: [ref blocks]})"""
    lines = text.replace("\r\n", "\n").split("\n")
    header, lists, cur = [], {}, None
    for line in lines:
        if line and not line[0].isspace() and not line.startswith("- "):
            key = line.split(":", 1)[0]
            cur = key if key in ("Temporary", "Persistent", "NavigationMeshes") else None  # children, not header
            if cur:
                lists[cur] = []
                continue
        if cur:
            if line.startswith("- "):
                lists[cur].append([line])
            elif lists[cur]:
                lists[cur][-1].append(line)
        else:
            header.append(line)
    return "\n".join(header).rstrip("\n"), {k: ["\n".join(b) for b in v] for k, v in lists.items()}


def find_block(plugin, cell_fk, ref):
    _, lists = split(open(os.path.join(cell_dir(plugin, cell_fk), "RecordData.yaml"), encoding="utf-8").read())
    hits = [b for blocks in lists.values() for b in blocks if re.search(rf"^  FormKey: {ref}:", b, re.M)]
    if len(hits) != 1:
        sys.exit(f"{ref} in {plugin}'s {cell_fk}: expected one record, found {len(hits)}")
    return hits[0]


def disable(block):
    """InitiallyDisabled on a placed ref, written the way the statue mod writes its own."""
    assert "InitiallyDisabled" not in block, block[:80]
    m = re.search(r"^  MajorRecordFlagsRaw: (\d+)$", block, re.M)
    if m:
        raw = f"  MajorRecordFlagsRaw: {int(m.group(1)) | 0x800}"
        if "\n  SkyrimMajorRecordFlags:" in block:
            block = block.replace(m.group(0), raw)
            return block.replace("\n  SkyrimMajorRecordFlags:", "\n  SkyrimMajorRecordFlags:\n  - InitiallyDisabled", 1)
        return block.replace(m.group(0), raw + "\n  SkyrimMajorRecordFlags:\n  - InitiallyDisabled")
    fk = re.search(r"^  FormKey: .*$", block, re.M).group(0)  # same place the statue mod writes them
    return block.replace(fk, fk + "\n  MajorRecordFlagsRaw: 2048\n  SkyrimMajorRecordFlags:\n  - InitiallyDisabled", 1)


def main():
    for d in ("Cells",):
        shutil.rmtree(os.path.join(OUT, d), ignore_errors=True)
    referenced = set()
    for cell_fk, (winner, restore, off) in CELLS.items():
        src_dir = cell_dir(winner, cell_fk)
        header, _ = split(open(os.path.join(src_dir, "RecordData.yaml"), encoding="utf-8").read())
        temp = []
        for ref, plugin in restore:
            b = find_block(plugin, cell_fk, ref)
            mod_b = find_block(MOD, cell_fk, ref)
            assert "InitiallyDisabled" in mod_b and "InitiallyDisabled" not in b, ref
            temp.append(b)
        statues = sum(BASE_STATUE in b for b in temp)
        for ref in off:
            b = find_block(MOD, cell_fk, ref)
            temp.append(disable(b))
        text = header + "\nTemporary:\n" + "\n".join(temp) + "\n"
        rel = os.path.relpath(src_dir, os.path.join(TREES[winner], "Cells"))
        dst = os.path.join(OUT, "Cells", rel)
        os.makedirs(dst, exist_ok=True)
        with open(os.path.join(dst, "RecordData.yaml"), "w", encoding="utf-8", newline="") as f:
            f.write(text.replace("\n", "\r\n"))
        # interior block / sub-block scaffolding, copied from the winner's tree
        parts = rel.split(os.sep)[:-1]
        for i in range(len(parts) + 1):
            g = os.path.join(TREES[winner], "Cells", *parts[:i], "GroupRecordData.yaml")
            if os.path.isfile(g):
                shutil.copyfile(g, os.path.join(OUT, "Cells", *parts[:i], "GroupRecordData.yaml"))
        referenced |= set(re.findall(r"\b[0-9A-F]{6}:([^\r\n:]+?\.es[mp])\b", text)) | {winner}
        print(f"{cell_fk}: header from {winner}; {statues} Veiled Woman statue(s) + {len(restore) - statues} other "
              f"object(s) restored; {len(off)} replacement(s) disabled")
    unknown = referenced - set(LOAD_ORDER)
    if unknown:
        sys.exit(f"output references plugins outside LOAD_ORDER: {unknown}")
    masters = [p for p in LOAD_ORDER if p in referenced or p in ("Skyrim.esm", "Update.esm", FS)]
    rd = os.path.join(OUT, "RecordData.yaml")
    text = open(rd, encoding="utf-8").read()
    block = "".join(f"  - Master: {m}\r\n    FileSize: 0\r\n" for m in masters)
    text = re.sub(r"  MasterReferences:\r?\n(?:  - Master: .*\r?\n    FileSize: 0\r?\n)+", "  MasterReferences:\r\n" + block, text)
    open(rd, "w", encoding="utf-8", newline="").write(text)
    print("masters:", ", ".join(masters))


if __name__ == "__main__":
    main()
