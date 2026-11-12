"""Check the built plugin against the live winner.

The RACE 0450F7 record in dist/WolfMountTurning/Zenderal - Wolf Mount Turning.esp must equal the load order's winning
record (EGO's) subrecord for subrecord, except for the added MTYP/SPED pairs, which must name the two wolf movement
types with RotateWhileMovingRun > 0. Exits non-zero on any difference.

Run from the repo root after deserializing: python -I src/WolfMountTurning/tools/02-verify.py
"""
import importlib.util
import os
import struct
import sys
import zlib

HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
BUILT = os.path.join(ROOT, "dist", "WolfMountTurning", "Zenderal - Wolf Mount Turning.esp")
spec = importlib.util.spec_from_file_location("scan", os.path.join(HERE, "00-scan-mount-movement.py"))
scan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scan)
WOLF_MOVTS = {0x055D28, 0x0EA64B}


def race_subrecords(path):
    data = open(path, "rb").read()
    hdr = struct.unpack_from("<I", data, 4)[0]
    pos = 24 + hdr
    while pos < len(data):
        typ = data[pos:pos + 4]
        size = struct.unpack_from("<I", data, pos + 4)[0]
        if typ == b"GRUP":
            label = data[pos + 8:pos + 12]
            if struct.unpack_from("<i", data, pos + 12)[0] == 0 and label != b"RACE":
                pos += size
                continue
            pos += 24
            continue
        if typ == b"RACE" and struct.unpack_from("<I", data, pos + 12)[0] & 0xFFFFFF == 0x0450F7:
            rflags = struct.unpack_from("<I", data, pos + 8)[0]
            body = data[pos + 24:pos + 24 + size]
            if rflags & 0x40000:
                body = zlib.decompress(body[4:])
            return list(scan.subrecords(body))
        pos += 24 + size
    raise SystemExit(f"RACE 0450F7 not found in {path}")


def main():
    winner = None
    for name, path in scan.plugin_paths():
        if name.lower() == "zenderal - wolf mount turning.esp":
            continue
        try:
            subs = race_subrecords(path)
        except SystemExit:
            continue
        winner = (name, subs)
    print("winning RACE 0450F7 outside this patch:", winner[0])
    built = race_subrecords(BUILT)
    plain = [(t, d) for t, d in built if t not in (b"MTYP", b"SPED")]
    # Spriggit writes MTNM names and attacks (ATKD + ATKE pairs) in its own sorted order; the engine looks attacks
    # up by event, so compare those as paired multisets and everything else in sequence.
    def split(subs):
        seq, names, attacks = [], [], []
        i = 0
        while i < len(subs):
            t, d = subs[i]
            if t == b"MTNM":
                names.append(d)
            elif t == b"ATKD" and i + 1 < len(subs) and subs[i + 1][0] == b"ATKE":
                attacks.append((d, subs[i + 1][1]))
                i += 1
            else:
                seq.append((t, d))
            i += 1
        return seq, sorted(names), sorted(attacks)
    mine, theirs = split(plain), split(winner[1])
    for label, a, b in zip(("ordered subrecords", "MTNM names", "attacks"), mine, theirs):
        if a != b:
            print("DIFFERENT:", label, len(a), len(b))
            for i, (x, y) in enumerate(zip(a, b)):
                if x != y:
                    print("  first difference at", i, x[0] if isinstance(x[0], bytes) else x, "|", y[0] if isinstance(y[0], bytes) else y)
                    break
            return 1
        print(f"same {label}: {len(a)}")
    print("all other subrecords identical to", winner[0])
    pairs = [(t, d) for t, d in built if t in (b"MTYP", b"SPED")]
    seen = set()
    for i in range(0, len(pairs), 2):
        (ta, da), (tb, db) = pairs[i], pairs[i + 1]
        movt = struct.unpack_from("<I", da)[0] & 0xFFFFFF
        speeds = scan.sped(db)
        print(f"  MTYP {movt:06X}: {speeds}")
        if ta != b"MTYP" or tb != b"SPED" or movt not in WOLF_MOVTS or speeds["RotateWhileMovingRun"] <= 0:
            return 1
        seen.add(movt)
    if seen != WOLF_MOVTS:
        print("missing overrides:", WOLF_MOVTS - seen)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
