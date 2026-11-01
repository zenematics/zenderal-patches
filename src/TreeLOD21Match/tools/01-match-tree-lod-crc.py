r"""Build `Zenderal - Tree LOD 2.1 Match` from the installed list -- never hand-edit its meshes.

Why: DynDOLOD finds a tree's 3D LOD model by the CRC32 of the full model
(`<name>_<crc32>[passthru]_lod.nif`). Enderal 2.1 re-saved many tree meshes (2.1.4 merged Fixed Mesh Lighting), so
their CRC32 changed, and the Enderal Arboreal Revived 3D LOD models (made for 2.0) stopped matching: DynDOLOD fell back
to flat billboards for those trees. dyndolod.info (Ultra Tree LOD): "If full models have been converted, update the
CRC32 in the 3D tree LOD filename so they match again."

That is only right when the shape is unchanged. For every tree in DynDOLOD's last Tree Report that no installed mod
(this one aside) has a 3D model for at its current CRC32, this script:
  1. takes the current full model (the copy whose CRC32 DynDOLOD reported: loose by MO2 priority, else archive);
  2. takes the same path from Enderal 2.0's archives (a backup of the pre-2.1 Data folder);
  3. requires that some installed 3D LOD model was made for the 2.0 CRC32;
  4. requires identical vertex positions and triangles in every BSTriShape (normals, colours and shader data may
     differ: they do not change the silhouette);
and only then copies that LOD model (the winning copy) under the current CRC32 into the output mod.
Trees whose shape changed in 2.1 (the iced aspens) are reported and skipped.

Re-run after an Enderal update, a tree mesh mod change or a DynDOLOD update, then rerun DynDOLOD.

Usage (repo root):  python src/TreeLOD21Match/tools/01-match-tree-lod-crc.py
                       [--modlist E:/Zenderal] [--profile Ultra]
                       [--old-data "E:/Zenderal-backups/2026-10-19-pre-AE-migration/Stock game/Data"]
                       [--out "E:/Zenderal/mods/Zenderal - Tree LOD 2.1 Match"] [--dry-run]
"""
import argparse
import collections
import importlib.util
import os
import re
import shutil
import struct
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
_spec = importlib.util.spec_from_file_location(
    'grassbounds', os.path.join(REPO, 'src', 'GrassBounds', 'tools', '01-build-grass-bounds.py'))
gb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gb)               # BsaIndex, enabled_mods, load_order, archives, TRISHAPES

BS = '\\'
LOD_DIR = ('meshes', 'dyndolod', 'lod', 'trees')
OLD_ARCHIVES = ('Skyrim - Meshes0.bsa', 'Skyrim - Meshes1.bsa', 'E - Meshes.bsa', 'E - Update.bsa')


def shape_geometry(d):
    """Per BSTriShape: (transform bytes, vertex count, triangle count, positions, triangles). LE geometry -> None."""
    p = d.index(b'\n') + 1 + 5
    user, nblocks, bsver = struct.unpack_from('<III', d, p); p += 12
    if bsver != 100:
        return None
    for _ in range(3):
        p += 1 + d[p]
    ntypes, = struct.unpack_from('<H', d, p); p += 2
    types = []
    for _ in range(ntypes):
        n, = struct.unpack_from('<I', d, p); types.append(d[p + 4:p + 4 + n].decode('latin1')); p += 4 + n
    tidx = struct.unpack_from('<%dH' % nblocks, d, p); p += 2 * nblocks
    sizes = struct.unpack_from('<%dI' % nblocks, d, p); p += 4 * nblocks
    nstr, = struct.unpack_from('<I', d, p); p += 8
    for _ in range(nstr):
        n, = struct.unpack_from('<I', d, p); p += 4 + n
    ng, = struct.unpack_from('<I', d, p); p += 4 + 4 * ng
    out = []
    for i in range(nblocks):
        typ = types[tidx[i] & 0x7FFF]
        if typ in gb.LEGEOM:
            return None
        if typ in gb.TRISHAPES:
            q = p + 4
            nx, = struct.unpack_from('<I', d, q); q += 4 + 4 * nx
            q += 8                                  # controller, flags
            xf = d[q:q + 52]; q += 52 + 4           # translation, rotation, scale; collision
            q += 16 + 12                            # bounding sphere; skin, shader, alpha
            desc, = struct.unpack_from('<Q', d, q); q += 8
            ntri, nvert = struct.unpack_from('<HH', d, q); q += 4
            q += 4                                  # data size
            vs = (desc & 0xF) * 4
            pos = b''.join(d[q + k * vs:q + k * vs + 12] for k in range(nvert))
            out.append((xf, nvert, ntri, pos, d[q + vs * nvert:q + vs * nvert + 6 * ntri]))
        p += sizes[i]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--modlist', default='E:/Zenderal')
    ap.add_argument('--profile', default='Ultra')
    ap.add_argument('--old-data', default='E:/Zenderal-backups/2026-10-19-pre-AE-migration/Stock game/Data')
    ap.add_argument('--out', default='E:/Zenderal/mods/Zenderal - Tree LOD 2.1 Match')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    root = a.modlist
    mods = gb.enabled_mods(root, a.profile)
    out_name = os.path.basename(a.out.rstrip('/\\'))
    mods = [m for m in mods if m != out_name]       # our own copies must not count as available models
    plugins = gb.load_order(root, a.profile)
    bsas = [gb.BsaIndex(p) for p in gb.archives(root, mods, a.profile, plugins)]
    old = [gb.BsaIndex(os.path.join(a.old_data, n)) for n in OLD_ARCHIVES if os.path.isfile(os.path.join(a.old_data, n))]
    assert old, 'no Enderal 2.0 archives under %s' % a.old_data

    # installed 3D tree LOD models: name -> {crc: path of the winning copy}
    lods = collections.defaultdict(dict)
    for m in reversed(mods):                        # lowest priority first, so higher priority overwrites
        d = os.path.join(root, 'mods', m, *LOD_DIR)
        if os.path.isdir(d):
            for f in os.listdir(d):
                mm = re.match(r'(.+)_([0-9a-f]{8})(.*_lod(?:_flat)?\.nif)$', f, re.I)
                if mm:
                    lods[mm.group(1).lower()][mm.group(2).lower()] = (os.path.join(d, f), mm.group(3))

    report = open(os.path.join(root, 'Tools', 'DynDOLOD', 'Logs', 'DynDOLOD_EnderalSE_Tree_Report.txt'),
                  encoding='utf-8', errors='replace').read()
    done, skipped, seen = [], [], set()
    for m in re.finditer(r'\n(\S+)(?: "[^"\n]*")? \[TREE:([0-9A-F]{8})\] (\S.*?\.nif) \[(?:Original )?CRC32:([0-9A-F]{8})\]', report):
        rel, crc = m.group(3), m.group(4).lower()
        name = os.path.basename(rel.replace(BS, '/'))[:-4].lower()
        # judged by what is installed, not by the report: after a DynDOLOD run our own copies show as "found"
        if name not in lods or crc in lods[name] or (rel.lower(), crc) in seen:
            continue
        seen.add((rel.lower(), crc))
        cur = None
        for mo in mods:
            f = os.path.join(root, 'mods', mo, *rel.split(BS))
            if os.path.isfile(f):
                b = open(f, 'rb').read()
                if '%08x' % zlib.crc32(b) == crc:
                    cur = b; break
        if cur is None:
            for b in reversed(bsas):
                if rel.lower() in b.files:
                    x = b.read(rel.lower())
                    if '%08x' % zlib.crc32(x) == crc:
                        cur = x; break
        prev = next((b.read(rel.lower()) for b in reversed(old) if rel.lower() in b.files), None)
        if cur is None or prev is None:
            skipped.append((name, crc, 'no %s copy' % ('current' if cur is None else 'Enderal 2.0'))); continue
        oc = '%08x' % zlib.crc32(prev)
        if oc not in lods[name]:
            skipped.append((name, crc, 'no 3D model for the 2.0 CRC %s' % oc)); continue
        g_old, g_new = shape_geometry(prev), shape_geometry(cur)
        if g_old is None or g_new is None or g_old != g_new:
            skipped.append((name, crc, 'shape changed since 2.0 (CRC %s)' % oc)); continue
        src, suffix = lods[name][oc]
        dst = os.path.join(a.out, *LOD_DIR, '%s_%s%s' % (name, crc.upper(), suffix))
        done.append((name, oc, crc, src, dst))

    for name, crc, why in sorted(skipped):
        print('skip  %-26s %s  %s' % (name, crc, why))
    for name, oc, crc, src, dst in sorted(done):
        print('match %-26s 2.0 %s -> 2.1 %s  from %s' % (name, oc, crc, os.path.relpath(src, os.path.join(root, 'mods'))))
    if a.dry_run:
        return
    if os.path.isdir(os.path.join(a.out, 'meshes')):
        shutil.rmtree(os.path.join(a.out, 'meshes'))
    for name, oc, crc, src, dst in done:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
    print('wrote %d 3D tree LOD models to %s' % (len(done), a.out))


if __name__ == '__main__':
    main()
