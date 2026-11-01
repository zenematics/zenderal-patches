#!/usr/bin/env python3
"""Forward each NPC's face from the face mod that owns it. Run after 02 (and 01).

02 builds an NPC override from the Pretty winner plus EGO's gameplay, so its face fields are Pretty's or base
Enderal's. A face replacer loading between Pretty and this patch (Malphas' Blessing on Tealor `01ADF1`, reported
2026-10-28) ships a baked FaceGen mesh made for ITS head parts, skin and morphs; this patch loads last, so it put
the old head parts back on top of that mesh and Tealor kept his vanilla look.

For every NPC record in the patch, the face OWNER is the last plugin in the record's live chain (01's
`_chains.json`, this patch excluded) that changed any FACE field from base. If the owner is not the plugin 02
took the face from, all FACE fields are copied from the owner's record as one group (head parts must match its
FaceGen mesh, so fields are never mixed between plugins), and every plugin those fields name is added as a master
in live load order. Everything else in the record is untouched. Asserted and idempotent.

The owner's record must be in a reference tree 02 knows (reference/mods/PrettyContext/<plugin name>/ for
non-Pretty plugins; serialize with the spriggit-decompile-reference skill).

Usage:  python 03-forward-npc-faces.py
"""
import collections
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
ESP = os.path.join(HERE, "..", "PrettyArmoryEGOESP")
CHAINS = os.path.join(ROOT, "reference", "mods", "Pretty", "_chains.json")
REF = os.path.join(ROOT, "reference")
SELF = "Zenderal - Pretty Armory EGO Patch.esp"
BASE = ["Skyrim.esm", "Update.esm", "Enderal - Forgotten Stories.esm"]
FACE = ["HeadParts", "HairColor", "HeadTexture", "FaceMorph", "FaceParts", "TintLayers", "TextureLighting",
        "WornArmor", "Height", "Weight"]

TREES = {
    "Skyrim.esm": os.path.join(REF, "base", "Skyrim"),
    "Update.esm": os.path.join(REF, "base", "Update"),
    "Enderal - Forgotten Stories.esm": os.path.join(REF, "base", "EnderalFS"),
    "Enderal SE - Gameplay Overhaul.esp": os.path.join(REF, "mods", "EGO"),
}
for sub in ("Pretty", "PrettyContext"):
    d = os.path.join(REF, "mods", sub)
    for n in os.listdir(d):
        if os.path.isdir(os.path.join(d, n)):
            TREES[n + ".esp"] = os.path.join(d, n)

FK_RE = re.compile(r"\b[0-9A-F]{6}:([^\r\n:]+?\.es[pml])\b")


def parse(text):
    """OrderedDict top-level field -> list of lines."""
    out, cur = collections.OrderedDict(), None
    for line in text.splitlines():
        if line and not line[0].isspace() and not line.startswith("- "):
            cur = line.split(":", 1)[0]
            out[cur] = [line]
        elif cur is not None:
            out[cur].append(line)
    return out


def record(plugin, fk):
    fid, master = fk.split(":", 1)
    if plugin not in TREES:
        sys.exit(f"no reference tree for {plugin} - serialize it into reference/mods/PrettyContext/")
    hits = glob.glob(os.path.join(TREES[plugin], "Npcs", f"* - {fid}_{master}.yaml"))
    if len(hits) != 1:
        sys.exit(f"{fk} not found once in {plugin}'s reference tree ({len(hits)} hits) - re-serialize it")
    return parse(open(hits[0], encoding="utf-8-sig").read())


def face(rec):
    return {f: rec.get(f) for f in FACE}


def main():
    data = json.load(open(CHAINS, encoding="utf-8"))
    order = data["order"]
    changed, new_masters = 0, set()
    for path in sorted(glob.glob(os.path.join(ESP, "Npcs", "*.yaml"))):
        m = re.search(r" - ([0-9A-F]{6})_(.+)\.yaml$", os.path.basename(path))
        fk = f"{m.group(1)}:{m.group(2)}"
        chain = [p for p in data["chain"][fk]["chain"] if p != SELF]
        base_p = [p for p in chain if p in BASE][-1]
        base = face(record(base_p, fk))
        owner = None
        for p in chain[chain.index(base_p) + 1:]:
            if face(record(p, fk)) != base:
                owner = p
        raw = open(path, encoding="utf-8-sig", newline="").read()
        ours = parse(raw.replace("\r\n", "\n"))
        if owner is None or face(record(owner, fk)) == face(ours):
            print(f"{fk} {os.path.basename(path)}: face already {owner or base_p}'s")
            continue
        src = record(owner, fk)
        # rebuild in our field order; a face field we lack goes after its predecessor in the owner's order
        out = collections.OrderedDict((k, v) for k, v in ours.items() if k not in FACE or src.get(k))
        for f in FACE:
            if src.get(f) is None:
                continue
            if f in out:
                out[f] = src[f]
                continue
            keys = list(src)
            prev = [k for k in keys[:keys.index(f)] if k in out]
            items = list(out.items())
            at = items.index(next(i for i in items if i[0] == prev[-1])) + 1 if prev else len(items)
            items.insert(at, (f, src[f]))
            out = collections.OrderedDict(items)
        assert face(out) == face(src), fk
        assert {k: v for k, v in out.items() if k not in FACE} == {k: v for k, v in ours.items() if k not in FACE}, fk
        text = "\r\n".join(l for block in out.values() for l in block) + "\r\n"
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        refs = {r for f in FACE if src.get(f) for r in FK_RE.findall("\n".join(src[f]))}
        new_masters |= refs
        diff = [f for f in FACE if ours.get(f) != src.get(f)]
        print(f"{fk} {os.path.basename(path)}: face from {owner} ({', '.join(diff)})")
        changed += 1

    # masters: add any the forwarded faces name, keeping live load order
    rd = os.path.join(ESP, "RecordData.yaml")
    text = open(rd, encoding="utf-8-sig", newline="").read()
    have = re.findall(r"- Master: (.+?)\r?\n", text)
    missing = [p for p in new_masters if p not in have]
    if missing:
        assert all(p in order for p in missing), missing
        masters = sorted(set(have) | set(missing), key=lambda p: order.index(p) if p in order else -1)
        block = "".join(f"  - Master: {p}\r\n    FileSize: 0\r\n" for p in masters)
        text, n = re.subn(r"  MasterReferences:\r?\n(?:  - Master: .+\r?\n    FileSize: \d+\r?\n)+",
                          "  MasterReferences:\r\n" + block, text)
        assert n == 1, "MasterReferences block not found"
        with open(rd, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        print("masters added:", ", ".join(missing))
    print(f"{changed} NPC face(s) forwarded")


if __name__ == "__main__":
    main()
