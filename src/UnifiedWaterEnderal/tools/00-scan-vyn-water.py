"""Reproduce Unified Water's per-cell water decision for Vyn against the live load order, and say why each cell fails.

Unified Water (Bottled Shaders / Community Shaders, src/Features/UnifiedWater/WaterCache.cpp) replaces LOD water with
its own planes. For each cell in the worldspace's bounds it reads, from the plugins that contain the worldspace:
  * the LAST plugin's CELL record at (x, y): XCLW (water height; absent = WRLD default) and XCWT (water form);
  * searching on from that plugin towards the first, the first CELL at (x, y) that has a LAND child: VHGT -> the
    cell's lowest land point.
No CELL or no LAND anywhere -> the cell is skipped (no water). Water shows only where water height > lowest land.

Output: counts per reason, an ASCII map of the open-sea area, and `vyn-water-cells.json` (scratch) for the patch
generator. Read-only: it never writes into the modlist.

Usage: python 00-scan-vyn-water.py [--with-self] [<MO2 root>] [<profile>] [<out json>]
"""
import json
import os
import struct
import sys
import zlib

WITH_SELF = "--with-self" in sys.argv
if WITH_SELF:
    sys.argv.remove("--with-self")
MO2 = sys.argv[1] if len(sys.argv) > 1 else "E:/Zenderal"
PROFILE = sys.argv[2] if len(sys.argv) > 2 else "Ultra"
OUT = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "vyn-water-cells.json")
VYN = 0x001D3C
IMPLICIT = ["Skyrim.esm", "Update.esm", "Dawnguard.esm", "HearthFires.esm", "Dragonborn.esm"]
FLT_MAX = struct.unpack("<f", bytes([0xFF, 0xFF, 0x7F, 0x7F]))[0]  # XCLW = FLT_MAX means "use the WRLD default"
MAX_VALID = 50000.0  # kMaxValidCellHeight in WaterCache.cpp


def resolve_files():
    prof = os.path.join(MO2, "profiles", PROFILE)
    where = {}
    data = os.path.join(MO2, "Stock game", "Data")
    for f in os.listdir(data):
        where[f.lower()] = os.path.join(data, f)
    mods = [l[1:].strip() for l in open(os.path.join(prof, "modlist.txt"), encoding="utf-8") if l.startswith("+")]
    for m in reversed(mods):  # bottom of modlist.txt = lowest priority, so later writes win
        d = os.path.join(MO2, "mods", m)
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.lower().endswith((".esm", ".esp", ".esl")):
                    where[f.lower()] = os.path.join(d, f)
    ov = os.path.join(MO2, "overwrite")
    for f in os.listdir(ov):
        if f.lower().endswith((".esm", ".esp", ".esl")):
            where[f.lower()] = os.path.join(ov, f)
    ccc = [l.strip() for l in open(os.path.join(MO2, "Stock game", "Skyrim.ccc"), encoding="utf-8") if l.strip()]
    # our own output is left out, so a rerun sees the holes it has to fill (pass --with-self to check the result)
    active = [l[1:].strip() for l in open(os.path.join(prof, "plugins.txt"), encoding="utf-8") if l.startswith("*")
              and (WITH_SELF or l[1:].strip().lower() != "zenderal - vyn full extend.esp")]
    order = []
    for n in IMPLICIT + ccc + active:
        if n.lower() in where and n.lower() not in [o.lower() for o in order]:
            order.append(n)
    # the engine loads ESM-flagged files (and .esm/.esl names) before plain plugins
    def is_master(n):
        if n.lower().endswith((".esm", ".esl")):
            return True
        with open(where[n.lower()], "rb") as fh:
            return bool(struct.unpack("<I", fh.read(12)[8:12])[0] & 1)
    order = [n for n in order if is_master(n)] + [n for n in order if not is_master(n)]
    return [(n, where[n.lower()]) for n in order]


def subrecords(data):
    i, big = 0, None
    while i + 6 <= len(data):
        t = data[i:i + 4]
        n = struct.unpack_from("<H", data, i + 4)[0]
        if t == b"XXXX":
            big = struct.unpack_from("<I", data, i + 6)[0]
            i += 10
            continue
        if big is not None:
            n, big = big, None
        yield t, data[i + 6:i + 6 + n]
        i += 6 + n


def record_data(buf, off):
    flags = struct.unpack_from("<I", buf, off + 8)[0]
    size = struct.unpack_from("<I", buf, off + 4)[0]
    raw = buf[off + 24:off + 24 + size]
    if flags & 0x40000:
        raw = zlib.decompress(raw[4:])
    return flags, raw


def masters_of(buf):
    hs = struct.unpack_from("<I", buf, 4)[0]
    return [d[:-1].decode("cp1252") for t, d in subrecords(buf[24:24 + hs]) if t == b"MAST"]


def scan_plugin(path, name):
    """-> (defaultWaterHeight or None, {(x, y): dict(cell=bool, xclw, xcwt_raw, land_min)}) for Vyn, or None."""
    buf = open(path, "rb").read()
    ms = masters_of(buf)
    if "Skyrim.esm" in ms:
        vyn_id = (ms.index("Skyrim.esm") << 24) | VYN
    elif name.lower() == "skyrim.esm":
        vyn_id = VYN
    else:
        return None
    hs = struct.unpack_from("<I", buf, 4)[0]
    pos = 24 + hs
    out, default = {}, None
    while pos < len(buf):  # top-level groups
        gsize = struct.unpack_from("<I", buf, pos + 4)[0]
        label = buf[pos + 8:pos + 12]
        if label == b"WRLD":
            parse_wrld_group(buf, pos + 24, pos + gsize, vyn_id, out)
            default = out.pop("__default__", None)
        pos += gsize
    return (default, out) if out or default is not None else None


def parse_wrld_group(buf, pos, end, vyn_id, out):
    cur = None
    while pos < end:
        typ = buf[pos:pos + 4]
        if typ == b"GRUP":
            gsize = struct.unpack_from("<I", buf, pos + 4)[0]
            gtype = struct.unpack_from("<I", buf, pos + 12)[0]
            parent = struct.unpack_from("<I", buf, pos + 8)[0]
            if gtype == 1 and parent == vyn_id:  # world children
                parse_cells(buf, pos + 24, pos + gsize, out)
            pos += gsize
            continue
        size = struct.unpack_from("<I", buf, pos + 4)[0]
        fid = struct.unpack_from("<I", buf, pos + 12)[0]
        if typ == b"WRLD" and fid == vyn_id:
            _, raw = record_data(buf, pos)
            for t, d in subrecords(raw):
                if t == b"DNAM":
                    out["__default__"] = struct.unpack_from("<f", d, 4)[0]  # land, water
        pos += 24 + size


def parse_cells(buf, pos, end, out, current=None):
    while pos < end:
        typ = buf[pos:pos + 4]
        if typ == b"GRUP":
            gsize = struct.unpack_from("<I", buf, pos + 4)[0]
            gtype = struct.unpack_from("<I", buf, pos + 12)[0]
            if gtype in (4, 5):  # exterior blocks / sub-blocks
                parse_cells(buf, pos + 24, pos + gsize, out)
            elif gtype in (6, 9) and current is not None:  # cell children / temporary children
                parse_cells(buf, pos + 24, pos + gsize, out, current)
            elif gtype == 6:
                pass
            pos += gsize
            continue
        size = struct.unpack_from("<I", buf, pos + 4)[0]
        if typ == b"CELL":
            _, raw = record_data(buf, pos)
            xy, xclw, xcwt = None, None, None
            for t, d in subrecords(raw):
                if t == b"XCLC":
                    xy = struct.unpack_from("<ii", d, 0)
                elif t == b"XCLW":
                    xclw = struct.unpack_from("<f", d, 0)[0]
                elif t == b"XCWT":
                    xcwt = struct.unpack_from("<I", d, 0)[0]
            if xy is not None:
                current = xy
                out.setdefault(xy, {})
                out[xy].update(cell=True, xclw=xclw, xcwt=xcwt)
        elif typ == b"LAND" and current is not None:
            _, raw = record_data(buf, pos)
            for t, d in subrecords(raw):
                if t == b"VHGT":
                    off = struct.unpack_from("<f", d, 0)[0]
                    deltas = struct.unpack_from("<1089b", d, 4)
                    lo, row = float("inf"), off
                    for y in range(33):
                        row += deltas[y * 33]
                        acc = 0.0
                        for x in range(33):
                            if x:
                                acc += deltas[y * 33 + x]
                            lo = min(lo, (acc + row) * 8.0)
                    out[current]["land_min"] = lo
        pos += 24 + size


def main():
    files = resolve_files()
    per_file, default = [], None
    for name, path in files:
        try:
            r = scan_plugin(path, name)
        except Exception as e:  # a malformed plugin must not stop the scan
            print(f"  ! {name}: {e}")
            continue
        if r:
            d, cells = r
            if d is not None:
                default = d
            per_file.append((name, cells))
    print(f"{len(per_file)} plugins carry Vyn; default water height {default}")
    allxy = set()
    for _, c in per_file:
        allxy |= set(c)
    # Unified Water's walk: last file with the CELL -> water; then on down to the first one with LAND
    result = {}
    for xy in allxy:
        idx = [i for i, (_, c) in enumerate(per_file) if xy in c and c[xy].get("cell")]
        if not idx:
            result[xy] = ("no-cell", None)
            continue
        top = idx[-1]
        w = per_file[top][1][xy]
        water = w["xclw"] if w["xclw"] not in (None, FLT_MAX) else default
        land = None
        for i in range(top, -1, -1):
            c = per_file[i][1].get(xy)
            if c and c.get("cell") and "land_min" in c:
                land = c["land_min"]
                break
        if land is None:
            result[xy] = ("no-land", per_file[top][0])
        elif water is None or abs(water) >= MAX_VALID or abs(land) >= MAX_VALID:
            result[xy] = ("no-water", per_file[top][0])
        elif water > land:
            result[xy] = ("water", per_file[top][0])
        else:
            result[xy] = ("dry", per_file[top][0])
    from collections import Counter
    print(Counter(v[0] for v in result.values()))
    json.dump({"default": default, "cells": {f"{x},{y}": [r, f, ] for (x, y), (r, f) in result.items()},
               "detail": {f"{x},{y}": {"winner": result[(x, y)][1],
                                        "xclw": next((c[(x, y)]["xclw"] for _, c in reversed(per_file) if (x, y) in c and c[(x, y)].get("cell")), None)}
                          for (x, y) in result}},
              open(OUT, "w"), indent=0)
    xs = [x for x, _ in allxy]
    ys = [y for _, y in allxy]
    sym = {"water": "~", "dry": ".", "no-land": "L", "no-water": "N", "no-cell": " "}
    for y in range(max(ys), min(ys) - 1, -1):
        print(f"{y:4d} " + "".join(sym[result[(x, y)][0]] if (x, y) in result else " " for x in range(min(xs), max(xs) + 1)))
    print(f"     x from {min(xs)}")


if __name__ == "__main__":
    main()
