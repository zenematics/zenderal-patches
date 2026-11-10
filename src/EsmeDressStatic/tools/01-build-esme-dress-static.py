"""Build MO2 mod `Zenderal - Esme Dress Static` from the installed Pretty Enderal Clothing.

Report (Longinus + GreaseLord, 2026-11-09): Esme's dress "gives me a seizure", then her chest stretched across the
ground. Pretty Enderal Clothing swaps the female Hunter's Armor cuirass (`huntertorsof_1.nif`) and Esme's hood
(`hoodf_1.nif`) for Fuse00's Adventurer outfit, whose FSMP cloth physics (`Adv_body.xml`, `Adv_hood.xml`) flings the
skirt, sleeve, strap and hood bones when it blows up. Only Esme wears them (outfits 02A46C and 029780).

This copies both meshes out of Pretty's BSA with the FSMP marker renamed: FSMP finds a mesh's physics through a
NiStringExtraData named "HDT Skinned Mesh Physics Object", and the header string is replaced by a same-length name,
so every offset in the file stays put. The bones then hold their bind pose: Pretty's look, no simulation.
Asserted: each mesh has the marker string exactly once and the output differs from the source only in those bytes.

The meshes are Pretty's (and Fuse00's) work, so they are generated from the user's own install, never committed.
Usage: python 01-build-esme-dress-static.py [<mods dir>]   (default E:/Zenderal/mods; needs the lz4 package)
"""
import os
import struct
import sys

import lz4.frame

MODS = sys.argv[1] if len(sys.argv) > 1 else 'E:/Zenderal/mods'
BSA = os.path.join(MODS, 'Pretty Enderal Clothing', 'Pretty Enderal Clothing.bsa')
OUT_MOD = os.path.join(MODS, 'Zenderal - Esme Dress Static')
FOLDER = r'meshes\enderal\armor\immersive armors\hunter'
FILES = ('huntertorsof_1.nif', 'hoodf_1.nif')
OLD = b'HDT Skinned Mesh Physics Object'
NEW = b'ZEN Static Dress (SMP disabled)'
assert len(OLD) == len(NEW)


def read_bsa(path, wanted):
    """Return {lowercase path: bytes} for the wanted files of an SSE (v105) BSA."""
    d = open(path, 'rb').read()
    magic, ver, off, aflags, nfold, nfile, _fold_names, file_names, _ = struct.unpack_from('<4sIIIIIIII', d, 0)
    if magic != b'BSA\0' or ver != 105:
        raise SystemExit(f'{path}: not an SSE BSA ({magic}, {ver})')
    counts, p = [], off
    for _ in range(nfold):
        _h, cnt, _pad, _foff = struct.unpack_from('<QIIQ', d, p)
        counts.append(cnt)
        p += 24
    recs = []
    for cnt in counts:
        ln = d[p]
        folder = d[p + 1:p + ln].decode('cp1252').lower()
        p += 1 + ln
        for _ in range(cnt):
            _h, size, foff = struct.unpack_from('<QII', d, p)
            recs.append((folder, size, foff))
            p += 16
    names = d[p:p + file_names].split(b'\0')
    out = {}
    for (folder, size, foff), name in zip(recs, names):
        full = folder + '\\' + name.decode('cp1252').lower()
        if full not in wanted:
            continue
        comp = bool(aflags & 4) ^ bool(size & 0x40000000)
        size &= 0x3FFFFFFF
        q = foff
        if aflags & 0x100:  # embedded file names
            q += d[q] + 1
            size -= d[foff] + 1
        out[full] = lz4.frame.decompress(d[q + 4:q + size]) if comp else d[q:q + size]
    return out


wanted = {FOLDER + '\\' + f for f in FILES}
found = read_bsa(BSA, wanted)
missing = wanted - set(found)
if missing:
    raise SystemExit(f'not in {BSA}: {sorted(missing)}')
for full, data in sorted(found.items()):
    if data.count(OLD) != 1:
        raise SystemExit(f'{full}: expected the FSMP marker once, found {data.count(OLD)}')
    new = data.replace(OLD, NEW)
    diff = sum(a != b for a, b in zip(data, new))
    if len(new) != len(data) or diff > len(OLD):
        raise SystemExit(f'{full}: unexpected change ({diff} bytes)')
    dst = os.path.join(OUT_MOD, *full.split('\\'))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, 'wb').write(new)
    print(f'{full}: FSMP marker disabled ({diff} bytes changed)')
