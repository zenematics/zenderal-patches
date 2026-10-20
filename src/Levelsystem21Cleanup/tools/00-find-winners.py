"""Find every record whose WINNING override in the Ultra load order still references quest Levelsystem
010AA2:Skyrim.esm (deleted in Enderal 2.1). Reads the plugins' binaries (decompressing compressed records).
Writes winners.json for tools/01 and prints the plugins to serialize. Usage: 00-find-winners.py <out winners.json>
"""
import collections
import json
import os
import struct
import sys
import zlib

root = r"E:\Zenderal"
mods = [l[1:].strip() for l in open(root + r"\profiles\Ultra\modlist.txt", encoding="utf-8") if l.startswith("+")]
plugins = [l[1:].strip() for l in open(root + r"\profiles\Ultra\plugins.txt", encoding="utf-8") if l.startswith("*")]
order = ["Skyrim.esm", "Update.esm", "Enderal - Forgotten Stories.esm"] + plugins
TARGET = 0x010AA2
SELF = "Zenderal - 2.1 Levelsystem Cleanup.esp"


def find(p):
    for m in mods:
        f = os.path.join(root, "mods", m, p)
        if os.path.isfile(f):
            return f
    f = os.path.join(root, "Stock Game", "Data", p)
    return f if os.path.isfile(f) else None


def records(b, off, end):
    while off < end:
        typ = b[off:off + 4]
        size = struct.unpack_from("<I", b, off + 4)[0]
        if typ == b"GRUP":
            yield from records(b, off + 24, off + size)
            off += size
            continue
        flags, fid = struct.unpack_from("<II", b, off + 8)
        yield typ, flags, fid, off + 24, size
        off += 24 + size


touch = collections.defaultdict(list)
info = {}
for p in order:
    if p == SELF:
        continue
    f = find(p)
    if not f:
        continue
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
    sk = names.index("Skyrim.esm") if "Skyrim.esm" in names else None
    pat = struct.pack("<I", (sk << 24) | TARGET) if sk is not None else None
    for typ, flags, fid, doff, size in records(b, 24 + hsz, len(b)):
        hi = fid >> 24
        key = (names[hi] if hi < len(names) else p, fid & 0xFFFFFF)
        data = b[doff:doff + size]
        has = False
        if pat and key != ("Skyrim.esm", TARGET):
            if flags & 0x40000:
                try:
                    data = zlib.decompress(data[4:])
                except zlib.error:
                    data = b""
            has = pat in data
        if has or key in touch:
            ed = ""
            if data[:4] == b"EDID":
                n = struct.unpack_from("<H", data, 4)[0]
                ed = data[6:6 + n - 1].decode("cp1252", "replace")
            info.setdefault(key, (typ.decode(), ed))
            touch[key].append((p, has))
out = []
for key, lst in touch.items():
    if any(h for _, h in lst) and lst[-1][1]:
        out.append({"origin": key[0], "id": f"{key[1]:06X}", "type": info[key][0], "edid": info[key][1], "winner": lst[-1][0]})
out.sort(key=lambda r: (r["winner"], r["type"], r["id"]))
json.dump(out, open(sys.argv[1], "w", encoding="utf-8"), indent=1)
print(len(out), "winning records still reference 010AA2")
for w in sorted({r["winner"] for r in out}):
    print("serialize:", w)
