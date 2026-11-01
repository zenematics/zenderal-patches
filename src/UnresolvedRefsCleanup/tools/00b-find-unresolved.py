"""Unresolved FormKeys in WINNING records across the whole Ultra load order.
Index: every record defined by any loaded plugin (binary headers). Winners: for each record FormKey, the
serialized YAML file of the last plugin (load order) containing it. Reports winner records referencing a
FormKey nobody defines, with the YAML field name. usage: unresolved_winners.py <serializedRoot> <out.json>"""
import collections
import json
import os
import re
import struct
import sys

sys.stdout.reconfigure(encoding="utf-8")
SER, OUTJ = sys.argv[1], sys.argv[2]
root = r"E:\Zenderal"
mods = [l[1:].strip() for l in open(root + r"\profiles\Ultra\modlist.txt", encoding="utf-8") if l.startswith("+")]
plugins = [l[1:].strip() for l in open(root + r"\profiles\Ultra\plugins.txt", encoding="utf-8") if l.startswith("*")]
order = ["Skyrim.esm", "Update.esm", "Dawnguard.esm", "HearthFires.esm", "Dragonborn.esm", "Enderal - Forgotten Stories.esm"] + plugins


def find(p):
    for m in mods:
        f = os.path.join(root, "mods", m, p)
        if os.path.isfile(f):
            return f
    f = os.path.join(root, "Stock Game", "Data", p)
    return f if os.path.isfile(f) else None


defined, loaded = set(), set()
for p in order:
    f = find(p)
    if not f:
        continue
    loaded.add(p.lower())
    b = open(f, "rb").read()
    hsz = struct.unpack_from("<I", b, 4)[0]
    hdr, ms, i = b[24:24 + hsz], [], 0
    while i < len(hdr):
        t = hdr[i:i + 4]
        s = struct.unpack_from("<H", hdr, i + 4)[0]
        if t == b"MAST":
            ms.append(hdr[i + 6:i + 6 + s - 1].decode("cp1252"))
        i += 6 + s
    names = ms + [p]
    stack = [(24 + hsz, len(b))]
    while stack:
        off, end = stack.pop()
        while off < end:
            typ = b[off:off + 4]
            size = struct.unpack_from("<I", b, off + 4)[0]
            if typ == b"GRUP":
                stack.append((off + 24, off + size))
                off += size
                continue
            fid = struct.unpack_from("<I", b, off + 12)[0]
            hi = fid >> 24
            defined.add((fid & 0xFFFFFF, (names[hi] if hi < len(names) else p).lower()))
            off += 24 + size
defined.add((0x000014, "skyrim.esm"))

FK = re.compile(r"\b([0-9A-F]{6}):([^\r\n,\]'\"]+?\.(?:esm|esp|esl))\b")
REC = re.compile(r"^(\s*)(?:- MutagenObjectType: \w+\n\s*)?FormKey: ([0-9A-F]{6}:[^\r\n]+)$", re.M)
pos = {re.sub(r"[^A-Za-z0-9]", "", p): k for k, p in enumerate(order)}
# winner per record: scan every YAML, record top-level FormKey per file (files hold one record, except
# cell/worldspace RecordData which hold nested refs: treat each nested '- MutagenObjectType' item as a record)
owner = {}  # recordKey -> (order idx, plugin, path)
for d in sorted(os.listdir(SER)):
    k = pos.get(d)
    full = os.path.join(SER, d)
    if k is None or not os.path.isdir(full):
        continue
    for dp, _, fn in os.walk(full):
        for n in fn:
            if not n.endswith(".yaml") or n.startswith("Group"):
                continue
            p = os.path.join(dp, n)
            t = open(p, encoding="utf-8").read().replace("\r", "")
            for m in re.finditer(r"^\s*(?:- MutagenObjectType: \w+\n\s*)?FormKey: (\S+(?: \S+)*\.es[mpl])$", t, re.M):
                key = m.group(1)
                if key not in owner or owner[key][0] < k:
                    owner[key] = (k, order[k], p)
# check winners: per file, which record keys it wins; then scan that record's text block for unresolved refs
files = collections.defaultdict(set)
for key, (k, pl, p) in owner.items():
    files[p].add(key)
bad = []
for p, keys in files.items():
    t = open(p, encoding="utf-8").read().replace("\r", "")
    lines = t.split("\n")
    # split into record blocks: top-level record (indent 0 FormKey) + nested list items
    starts = [(i, re.match(r"^(\s*)", l).group(1)) for i, l in enumerate(lines) if re.match(r"^\s*(- MutagenObjectType: \w+$|FormKey: )", l)]
    blocks = []
    for j, (i, ind) in enumerate(starts):
        if lines[i].lstrip().startswith("FormKey:") and i > 0 and lines[i - 1].lstrip().startswith("- MutagenObjectType"):
            continue
        end = len(lines)
        for i2, ind2 in starts[j + 1:]:
            if len(ind2) <= len(ind):
                end = i2
                break
        fk = next((re.sub(r"^\s*FormKey: ", "", l) for l in lines[i:i + 3] if l.strip().startswith("FormKey:")), None)
        blocks.append((fk, i, end))
    for fk, i, end in blocks:
        if fk not in keys:
            continue
        # only lines of this block that are not inside a nested child record block
        child = [(a, b2) for fk2, a, b2 in blocks if a > i and b2 <= end and fk2 != fk]
        for ln in range(i, end):
            if any(a <= ln < b2 for a, b2 in child):
                continue
            for m in FK.finditer(lines[ln]):
                ref = (int(m.group(1), 16), m.group(2).strip().lower())
                if ref not in defined and ref[0] < 0x800 and (ref[0], "skyrim.esm") in defined:
                    continue  # engine-hardcoded form (PlayerRef 0x14 ...) that Spriggit labels with the plugin's own name
                if ref not in defined and not lines[ln].strip().startswith("FormKey:"):
                    field = lines[ln].strip().split(":")[0].lstrip("- ")
                    prev = lines[ln - 1].strip() if field == "Object" else ""
                    bad.append({"record": fk, "winner": owner[fk][1], "file": p, "line": ln, "field": field,
                                "prev": prev, "ref": f"{m.group(1)}:{m.group(2).strip()}",
                                "why": "master not loaded" if ref[1] not in loaded else "missing record"})
json.dump(bad, open(OUTJ, "w", encoding="utf-8"), indent=1)
print(len(bad), "unresolved references in", len({b['record'] for b in bad}), "winning records")
for w, c in collections.Counter(b["winner"] for b in bad).most_common():
    print(f"  {c:4}  {w}")
print("by field:", collections.Counter(b["field"] for b in bad).most_common(15))
