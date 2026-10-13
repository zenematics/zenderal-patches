"""Rebuild the `Zenderal - Enderal Texture Restores` MO2 mod from the game's own BSAs.

Some Skyrim texture mods override textures that Enderal re-authored at a vanilla path, on meshes Enderal
still uses as-is. This mod ships Enderal's (or vanilla's) original files loose so they win again.
It must sort ABOVE every mod listed in RESTORES' `beats` in MO2 (modlist.txt is highest-priority-first).

The files are SureAI's/Bethesda's, so they are extracted from the user's own install, never committed.

Usage:  python 01-extract-enderal-textures.py [<mods dir>]     (default E:/Zenderal/mods)
"""
import os, sys, hashlib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'SettingsApplier', 'tools', 'capture'))
from bsa import lz4_frame  # noqa: E402
import struct  # noqa: E402

MOD = 'Zenderal - Enderal Texture Restores'
BS = chr(92)

# (texture path, source archive, why). Source archive is the one the unmodded game would load it from.
RESTORES = [
    # DweFloorRubbleFlat01 (0B28B4) is an alpha-tested decal. Enderal re-authored its diffuse as cracked
    # slabs (~27% cut out); Stony AF Markarth and Dwemer Ruins 2K replaces it with Markarth shards (~72%
    # cut out, 0.20 cut-out IoU), which reads as bright chips on the Sun Coast temple ruins.
    ('textures\\dungeons\\dwemerruins\\dwestonerubble01.dds', 'E - Textures1.bsa',
     'Enderal diffuse; beats Stony AF 2K, SRP Enderal Dungeons, Underground, Skyrim 202X'),
    # Enderal ships no _n of its own for it; the unmodded game pairs its diffuse with vanilla's normal map.
    ('textures\\dungeons\\dwemerruins\\dwestonerubble01_n.dds', 'Skyrim - Textures4.bsa',
     'vanilla normal Enderal uses with it'),
]


def read_from_bsa(path, want):
    with open(path, 'rb') as fh:
        d = fh.read()
    magic, ver, fro, aflags, fcount, filecount, tfnl, tfil, ff = struct.unpack_from('<4sIIIIIIII', d, 0)
    assert magic == b'BSA\x00' and ver == 105, (path, magic, ver)
    p = fro
    counts = []
    for _ in range(fcount):
        counts.append(struct.unpack_from('<QIIQ', d, p)[1]); p += 24
    recs = []
    for c in counts:
        ln = d[p]; name = d[p + 1:p + ln].rstrip(b'\0').decode('latin1'); p += 1 + ln
        for _ in range(c):
            h, size, off = struct.unpack_from('<QII', d, p); p += 16
            recs.append((name, size, off))
    names = d[p:p + tfil].split(b'\0')
    for (dn, size, off), n in zip(recs, names):
        if (dn + BS + n.decode('latin1')).lower() != want:
            continue
        comp = bool(aflags & 4) ^ bool(size & 0x40000000); size &= 0x3FFFFFFF
        q = off
        if aflags & 0x100:
            ln = d[q]; q += 1 + ln; size -= 1 + ln
        blob = d[q:q + size]
        if not comp:
            return blob
        data = lz4_frame(blob[4:])
        assert len(data) == struct.unpack_from('<I', blob, 0)[0], want
        return data
    raise SystemExit(f'{want} not found in {path}')


def main():
    mods = sys.argv[1] if len(sys.argv) > 1 else 'E:/Zenderal/mods'
    data_dir = os.path.join(os.path.dirname(mods.rstrip('/' + BS)), 'Stock Game', 'Data')
    out_root = os.path.join(mods, MOD)
    for rel, archive, why in RESTORES:
        blob = read_from_bsa(os.path.join(data_dir, archive), rel.lower())
        assert blob[:4] == b'DDS ', rel
        out = os.path.join(out_root, *rel.split(BS))
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, 'wb') as fh:
            fh.write(blob)
        print(f'{len(blob):>9}  {hashlib.sha1(blob).hexdigest()[:12]}  {rel}  <- {archive}  ({why})')
    print(f'{len(RESTORES)} files -> {out_root}')


if __name__ == '__main__':
    main()
