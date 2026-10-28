"""Generate `Zenderal - Vyn Full Extend.esp`: flat seabed cells so Unified Water can draw Vyn's distant sea.

Why (2026-10-28, see arch-docs/patches/UnifiedWaterEnderal.md): when a terrain LOD chunk attaches, Unified Water
(Bottled Shaders) removes that chunk's whole vanilla LOD water and adds one plane per cell it has cache data for. A
cell only has data if some plugin gives it a CELL and a LAND record inside the worldspace bounds (NAM0/NAM9). Vyn's
open sea is mostly cells with no record at all, so every chunk that touches the coast lost its water there. Skyrim
hides this with a shipped `Tamriel_precache.wpc` built from sheson's Terrain Tamriel Full Extend; the precache path
is hard-wired to the EditorID "Tamriel", so Vyn needs the records themselves.

This plugin is Enderal's Full Extend for that purpose. For every cell that lies in a 32x32 LOD chunk holding any
Unified Water cell but has no water data itself (00-scan-vyn-water.py's `vyn-water-cells.json`):
  * no CELL anywhere      -> a new CELL (HasWater, no XCLW = Vyn's default water height 0) + a flat LAND at Vyn's
                             default land height -2048, which is what the game and the terrain LOD already assume
                             for a cell with no LAND, so nothing visible moves;
  * a CELL without LAND   -> that CELL's winning record copied byte for byte (all are Skyrim.esm or FS, whose form
                             indices match this plugin's master list) + the same flat LAND;
  * the Vyn WRLD          -> Occlusion.esp's winning record byte for byte, NAM0 widened so the bounds cover every
                             filled cell (Unified Water skips cells outside them).
Placed references are never copied. New records start at 0x800; it is a full plugin (about 24,000 new records, far
past ESL's 2048). Load it LAST, after Occlusion.esp. Binary output, generated, not committed.

Usage: python 01-build-vyn-full-extend.py [<scan json>] [<out .esp>] [<MO2 root>] [<profile>]
"""
import importlib.util
import json
import os
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
SCAN = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "vyn-water-cells.json")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "build", "Zenderal - Vyn Full Extend.esp")
MO2 = sys.argv[3] if len(sys.argv) > 3 else "E:/Zenderal"
PROFILE = sys.argv[4] if len(sys.argv) > 4 else "Ultra"

spec = importlib.util.spec_from_file_location("scan", os.path.join(HERE, "00-scan-vyn-water.py"))
scan = importlib.util.module_from_spec(spec)
sys.argv = [sys.argv[0], MO2, PROFILE]  # the scan module reads argv at import
spec.loader.exec_module(scan)

MASTERS = ["Skyrim.esm", "Update.esm", "Enderal - Forgotten Stories.esm"]
SELF = len(MASTERS) << 24
VYN = 0x001D3C
LOD = 32
LAND_HEIGHT = -2048.0
FORM_VERSION = 44


def record(typ, fid, payload, flags=0, compress=False):
    if compress:
        payload = struct.pack("<I", len(payload)) + zlib.compress(payload, 9)
        flags |= 0x40000
    return typ + struct.pack("<IIIIHH", len(payload), flags, fid, 0, FORM_VERSION, 0) + payload


def group(label, gtype, body):
    return b"GRUP" + struct.pack("<I4sIHHI", 24 + len(body), label, gtype, 0, 0, 0) + body


def sub(typ, data):
    return typ + struct.pack("<H", len(data)) + data


def flat_land(fid):
    vnml = bytes([0, 0, 127]) * (33 * 33)
    vhgt = struct.pack("<f", LAND_HEIGHT / 8.0) + bytes(1089) + bytes(3)
    return record(b"LAND", fid, sub(b"DATA", struct.pack("<I", 0x1)) + sub(b"VNML", vnml) + sub(b"VHGT", vhgt),
                  compress=True)


def new_cell(fid, x, y):
    return record(b"CELL", fid, sub(b"DATA", struct.pack("<H", 0x2)) + sub(b"XCLC", struct.pack("<iiI", x, y, 0)))


def find_records(path, want_cells):
    """-> (raw WRLD record bytes, {(x, y): raw CELL record bytes}) for Vyn in one plugin (records copied verbatim)."""
    buf = open(path, "rb").read()
    hs = struct.unpack_from("<I", buf, 4)[0]
    wrld, cells = None, {}

    def walk(p, e):
        nonlocal wrld
        while p < e:
            if buf[p:p + 4] == b"GRUP":
                gs, lab, gt = struct.unpack_from("<I4sI", buf, p + 4)
                if gt in (4, 5) or (gt == 1 and struct.unpack("<I", lab)[0] == VYN):
                    walk(p + 24, p + gs)
                p += gs
                continue
            sz = struct.unpack_from("<I", buf, p + 4)[0]
            fid = struct.unpack_from("<I", buf, p + 12)[0]
            if buf[p:p + 4] == b"WRLD" and fid == VYN:
                wrld = buf[p:p + 24 + sz]
            elif buf[p:p + 4] == b"CELL" and want_cells:
                _, raw = scan.record_data(buf, p)
                for t, d in scan.subrecords(raw):
                    if t == b"XCLC":
                        xy = struct.unpack_from("<ii", d)
                        if xy in want_cells:
                            cells[xy] = buf[p:p + 24 + sz]
            p += 24 + sz

    pos = 24 + hs
    while pos < len(buf):
        gs = struct.unpack_from("<I", buf, pos + 4)[0]
        if buf[pos + 8:pos + 12] == b"WRLD":
            walk(pos + 24, pos + gs)
        pos += gs
    return wrld, cells


def widen_wrld(raw, min_x, min_y):
    """Occlusion.esp's WRLD verbatim with NAM0 (world-unit lower bound) lowered to cover (min_x, min_y)."""
    typ, size, flags, fid = struct.unpack_from("<4sIII", raw, 0)
    assert typ == b"WRLD" and fid == VYN and not flags & 0x40000, (typ, hex(fid), hex(flags))
    data = raw[24:]
    out, i, changed = b"", 0, 0
    while i < len(data):
        t = data[i:i + 4]
        n = struct.unpack_from("<H", data, i + 4)[0]
        d = data[i + 6:i + 6 + n]
        assert t != b"XXXX" and t != b"OFST", t  # neither is present in the winning record (checked 2026-10-28)
        if t == b"NAM0":
            x0, y0 = struct.unpack("<ff", d)
            d = struct.pack("<ff", min(x0, min_x * 4096.0), min(y0, min_y * 4096.0))
            changed += 1
        out += t + struct.pack("<H", len(d)) + d
        i += 6 + n
    assert changed == 1
    return raw[:4] + struct.pack("<I", len(out)) + raw[8:24] + out


def main():
    data = json.load(open(SCAN))
    cells = {tuple(map(int, k.split(","))): v for k, v in data["cells"].items()}
    need = set()
    for (x, y), (reason, _) in cells.items():
        if reason == "water":
            cx, cy = x // LOD, y // LOD
            for xx in range(cx * LOD, cx * LOD + LOD):
                for yy in range(cy * LOD, cy * LOD + LOD):
                    c = cells.get((xx, yy))
                    if c is None or c[0] in ("no-cell", "no-land"):
                        need.add((xx, yy))
    no_land = {xy for xy in need if xy in cells and cells[xy][0] == "no-land"}
    owners = {cells[xy][1] for xy in no_land}
    assert owners <= {"Skyrim.esm", "Enderal - Forgotten Stories.esm"}, owners  # verbatim copy is only safe for these

    files = dict(scan.resolve_files())
    copied = {}
    for owner in sorted(owners):
        _, found = find_records(files[owner.lower()] if owner.lower() in files else files[owner], {xy for xy in no_land if cells[xy][1] == owner})
        copied.update(found)
    assert set(copied) == no_land, (len(copied), len(no_land))
    wrld_raw, _ = find_records(files["Occlusion.esp"], set())
    assert wrld_raw, "Occlusion.esp has no Vyn WRLD"
    min_x = min(x for x, _ in need)
    min_y = min(y for _, y in need)
    wrld = widen_wrld(wrld_raw, min_x, min_y)

    next_id = 0x800
    blocks = {}
    for (x, y) in sorted(need, key=lambda c: (c[1], c[0])):
        if (x, y) in copied:
            cell_rec = copied[(x, y)]
            cell_fid = struct.unpack_from("<I", cell_rec, 12)[0]
        else:
            cell_fid = SELF | next_id
            next_id += 1
            cell_rec = new_cell(cell_fid, x, y)
        land_fid = SELF | next_id
        next_id += 1
        children = group(struct.pack("<I", cell_fid), 6, group(struct.pack("<I", cell_fid), 9, flat_land(land_fid)))
        bx, by, sx, sy = x // 32, y // 32, x // 8, y // 8
        blocks.setdefault((bx, by), {}).setdefault((sx, sy), []).append(cell_rec + children)
    assert next_id <= 0xFFFFFF

    body = b""
    for (bx, by), subs in sorted(blocks.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        sb = b""
        for (sx, sy), recs in sorted(subs.items(), key=lambda kv: (kv[0][1], kv[0][0])):
            sb += group(struct.pack("<hh", sy, sx), 5, b"".join(recs))  # labels are (Y, X), checked on Skyrim.esm
        body += group(struct.pack("<hh", by, bx), 4, sb)
    world = wrld + group(struct.pack("<I", VYN), 1, body)
    top = group(b"WRLD", 0, world)

    # records + groups: WRLD, each CELL + LAND, the cell-children and temporary groups of each cell, every
    # sub-block and block group, the world-children group and the top WRLD group
    num_records = 1 + len(need) * 4 + sum(len(s) for s in blocks.values()) + len(blocks) + 2
    hedr = struct.pack("<fII", 1.7, num_records, next_id)
    tes4 = sub(b"HEDR", hedr) + sub(b"CNAM", b"Zenderal\0")
    tes4 += sub(b"SNAM", b"Flat seabed cells and wider Vyn bounds so Unified Water covers Vyn's whole sea.\0")
    for m in MASTERS:
        tes4 += sub(b"MAST", m.encode() + b"\0") + sub(b"DATA", bytes(8))
    header = b"TES4" + struct.pack("<IIIIHH", len(tes4), 0, 0, 0, FORM_VERSION, 0) + tes4

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "wb").write(header + top)
    print(f"{len(need)} cells filled ({len(need) - len(no_land)} new CELLs, {len(no_land)} copied), "
          f"{len(need)} LANDs, ids 0x800-0x{next_id - 1:X}; NAM0 min cell {min_x},{min_y}; {os.path.getsize(OUT)} bytes -> {OUT}")


if __name__ == "__main__":
    main()
