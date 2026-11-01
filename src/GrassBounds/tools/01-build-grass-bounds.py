r"""Build `Zenderal - Grass Bounds` from the installed list -- never hand-edit its records.

Why: 41 of base Enderal's 72 GRAS records (Skyrim.esm, 2.1.4.4) have no object bounds (OBND 0,0,0),
among them nearly all of Enderal's own grass (`_00E_*`, the Heartland/Suncoast "Nico" grasses).
TexGen skips a GRAS without object bounds when it renders grass LOD billboards (dyndolod.info
Help/Grass-LOD), so DynDOLOD would draw grass LOD only for the other 31; and NGIO's raycast
(Ray-cast-mode 1, Ray-cast-width 0) sizes its capsule from the grass model's bounds.

The patch overrides those 41 records with Enderal 2.1.4.4's record, verbatim, plus ObjectBounds:
the axis-aligned box of every vertex of the WINNING model (loose file by MO2 priority, else the last
archive in load order that has it), node transforms applied, truncated toward zero like the CK. Only Skyrim.esm defines GRAS in the list (asserted), so nothing else is reverted.

Before writing, the bounds code is checked against the 31 records SureAI did give bounds to,
computed from the archive (vanilla) copy of their model. Re-run after any grass mesh mod change.

Usage (repo root):  python src/GrassBounds/tools/01-build-grass-bounds.py [--modlist E:/Zenderal] [--profile Ultra]
"""
import argparse
import math
import os
import re
import shutil
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
REF = os.path.join(REPO, 'reference', 'base-2.1.4.4', 'Skyrim', 'Grasses')
OUT = os.path.join(HERE, '..', 'GrassBoundsESP', 'Grasses')
import lz4.frame

BS = '\\'


# --- archives: index read from the file head only, data by seek -----------------------------------
class BsaIndex:
    def __init__(self, path):
        self.path = path
        with open(path, 'rb') as f:
            head = f.read(36)
            magic, ver, off, flags, nfold, nfile, lfold, lfile, _ = struct.unpack_from('<4sIIIIIIIH', head)
            assert magic == b'BSA\x00' and ver == 105, (path, magic, ver)
            f.seek(0)
            d = f.read(off + 24 * nfold + lfold + nfold + 16 * nfile + lfile + 16)
        self.flags = flags
        counts, p = [], off
        for _ in range(nfold):
            counts.append(struct.unpack_from('<QIIQ', d, p)[1]); p += 24
        entries = []
        for count in counts:
            n = d[p]
            folder = d[p + 1:p + n].decode('latin1').rstrip('\0'); p += 1 + n
            for _ in range(count):
                _, size, foff = struct.unpack_from('<QII', d, p); p += 16
                entries.append([folder, None, size, foff])
        for e in entries:
            end = d.index(b'\0', p); e[1] = d[p:end].decode('latin1'); p = end + 1
        self.files = {(fo + BS + na).lower(): (sz, of) for fo, na, sz, of in entries}

    def read(self, name):
        size, off = self.files[name]
        compressed = bool(self.flags & 0x4) != bool(size & 0x40000000)
        size &= 0x3FFFFFFF
        with open(self.path, 'rb') as f:
            f.seek(off); d = f.read(size)
        p = 0
        if self.flags & 0x100:                      # embedded file name
            p = 1 + d[0]
        if compressed:
            raw = struct.unpack_from('<I', d, p)[0]
            out = lz4.frame.decompress(d[p + 4:])
            assert len(out) == raw, (name, len(out), raw)
            return out
        return d[p:]


# --- NIF: vertex box of the whole tree, SSE (BS 100, BSTriShape) and LE (BS 83, NiTriShapeData) ----
NODES = {'NiNode', 'BSFadeNode', 'BSLeafAnimNode', 'BSMultiBoundNode', 'NiSwitchNode', 'BSOrderedNode',
         'BSTreeNode', 'NiBillboardNode', 'BSValueNode', 'NiLODNode'}
TRISHAPES = {'BSTriShape', 'BSSubIndexTriShape', 'BSMeshLODTriShape', 'BSLODTriShape'}
LEGEOM = {'NiTriShape', 'NiTriStrips'}
IGNORED = set()                                     # leaf types seen that carry no geometry


def nif_box(data, note):
    d = data
    p = d.index(b'\n') + 1
    ver, = struct.unpack_from('<I', d, p); p += 4
    assert ver == 0x14020007, hex(ver)
    p += 1
    user, nblocks, bsver = struct.unpack_from('<III', d, p); p += 12
    assert user == 12 and bsver in (83, 100), (user, bsver)
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
    ngroups, = struct.unpack_from('<I', d, p); p += 4 + 4 * ngroups
    blocks = []
    for i in range(nblocks):
        blocks.append((types[tidx[i] & 0x7FFF], p)); p += sizes[i]

    def avobject(q):
        q += 4                                      # name
        nx, = struct.unpack_from('<I', d, q); q += 4 + 4 * nx
        q += 4 + 4                                  # controller, flags (uint32 for BS > 26)
        t = np.array(struct.unpack_from('<3f', d, q)); q += 12
        R = np.array(struct.unpack_from('<9f', d, q)).reshape(3, 3); q += 36
        s, = struct.unpack_from('<f', d, q); q += 4
        q += 4                                      # collision
        if not np.allclose(R, np.eye(3), atol=1e-5):
            note.append('rotation')
        return q, t, R, s

    pts = []

    def visit(i, M, T):
        typ, q = blocks[i]
        if typ in NODES:
            q, t, R, s = avobject(q)
            M2, T2 = M @ (R.T * s), M @ t + T       # NIF rotations are stored transposed (row = local axis)
            n, = struct.unpack_from('<I', d, q); q += 4
            for c in struct.unpack_from('<%di' % n, d, q):
                if c >= 0:
                    visit(c, M2, T2)
        elif typ in TRISHAPES:
            q, t, R, s = avobject(q)
            q += 16                                 # bounding sphere
            q += 12                                 # skin, shader, alpha
            desc, = struct.unpack_from('<Q', d, q); q += 8
            ntri, nvert = struct.unpack_from('<HH', d, q); q += 4
            dsize, = struct.unpack_from('<I', d, q); q += 4
            assert dsize, 'BSTriShape without vertex data (skinned?)'
            vs = (desc & 0xF) * 4
            buf = np.frombuffer(d[q:q + vs * nvert], np.uint8).reshape(nvert, vs)
            v = buf[:, 0:12].copy().view('<f4').reshape(nvert, 3).astype(np.float64)
            pts.append(v @ (M @ (R.T * s)).T + (M @ t + T))
        elif typ in LEGEOM:
            q, t, R, s = avobject(q)
            data_ref, = struct.unpack_from('<i', d, q)
            dtyp, dq = blocks[data_ref]
            assert dtyp in ('NiTriShapeData', 'NiTriStripsData'), dtyp
            dq += 4                                 # group id
            nvert, = struct.unpack_from('<H', d, dq); dq += 2
            dq += 2                                 # keep / compress flags
            assert d[dq] == 1, 'geometry without vertices'; dq += 1
            v = np.frombuffer(d[dq:dq + 12 * nvert], '<f4').reshape(nvert, 3).astype(np.float64)
            pts.append(v @ (M @ (R.T * s)).T + (M @ t + T))
        else:
            IGNORED.add(typ)

    assert blocks[0][0] in NODES, blocks[0][0]
    visit(0, np.eye(3), np.zeros(3))
    assert pts, 'no geometry'
    allp = np.concatenate(pts)
    return allp.min(axis=0), allp.max(axis=0)


def rounded(box):
    lo, hi = box                                    # the CK truncates toward zero (checked below)
    return [math.trunc(x) for x in lo], [math.trunc(x) for x in hi]


# --- the installed list ------------------------------------------------------------------------------
def enabled_mods(root, profile):
    with open(os.path.join(root, 'profiles', profile, 'modlist.txt'), encoding='utf-8') as f:
        return [l[1:].rstrip('\r\n') for l in f if l.startswith('+')]


def load_order(root, profile):
    with open(os.path.join(root, 'profiles', profile, 'loadorder.txt'), encoding='utf-8') as f:
        return [l.strip() for l in f if l.strip() and not l.startswith('#')]


def data_file(root, mods, rel):
    """Winning loose copy of a Data-relative path: highest-priority mod, else Stock Game/Data."""
    for m in mods:
        f = os.path.join(root, 'mods', m, *rel.split(BS))
        if os.path.isfile(f):
            return m, f
    f = os.path.join(root, 'Stock Game', 'Data', *rel.split(BS))
    return ('Stock Game', f) if os.path.isfile(f) else (None, None)


def archives(root, mods, profile, plugins):
    ini = open(os.path.join(root, 'profiles', profile, 'Enderal.ini'), encoding='utf-8', errors='replace').read()
    names = []
    for key in ('sResourceArchiveList', 'sResourceArchiveList2'):
        m = re.search(r'(?im)^%s=(.*)$' % key, ini)
        names += [n.strip() for n in m.group(1).split(',') if n.strip()]
    for plug in plugins:
        names.append(os.path.splitext(plug)[0] + '.bsa')
    out = []
    for n in names:
        src, path = data_file(root, mods, n)
        if path:
            out.append(path)
    return out                                      # load order: later wins


def gras_plugins(root, mods, plugins):
    """Plugins in the load order that contain a GRAS top group with records."""
    hits = []
    for plug in plugins:
        src, path = data_file(root, mods, plug)
        if not path:
            continue
        with open(path, 'rb') as f:
            d = f.read()
        q = 24 + struct.unpack_from('<I', d, 4)[0]
        while q + 24 <= len(d) and d[q:q + 4] == b'GRUP':
            size, label = struct.unpack_from('<I4s', d, q + 4)
            if label == b'GRAS' and size > 24:
                hits.append(plug)
            q += size
    return hits


def read_ref():
    recs = []
    for f in sorted(os.listdir(REF)):
        raw = open(os.path.join(REF, f), 'rb').read()
        t = raw.decode('utf-8')
        m = re.search(r'(?m)^Model:\r?\n  File: (.+?)\r?$', t)
        b = re.search(r'(?m)^ObjectBounds:\r?\n  First: (.+?)\r?\n  Second: (.+?)\r?$', t)
        bounds = None
        if b:
            bounds = ([int(x) for x in b.group(1).split(',')], [int(x) for x in b.group(2).split(',')])
        recs.append(dict(file=f, raw=raw, model=m.group(1).strip() if m else None, bounds=bounds))
    return recs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--modlist', default='E:/Zenderal')
    ap.add_argument('--profile', default='Ultra')
    a = ap.parse_args()
    mods = enabled_mods(a.modlist, a.profile)
    plugins = load_order(a.modlist, a.profile)

    owners = gras_plugins(a.modlist, mods, plugins)
    assert owners == ['Skyrim.esm'], 'another plugin defines/overrides GRAS now: %s' % owners

    bsas = [BsaIndex(p) for p in archives(a.modlist, mods, a.profile, plugins)]

    def from_archive(rel):
        key = 'meshes' + BS + rel.lower()
        for b in reversed(bsas):
            if key in b.files:
                return os.path.basename(b.path), b.read(key)
        return None, None

    def winning(rel):
        m, f = data_file(a.modlist, mods, 'meshes' + BS + rel)
        if f:
            return m, open(f, 'rb').read()
        return from_archive(rel)

    recs = read_ref()
    assert len(recs) == 72, len(recs)

    # 1. check the bounds code against SureAI's own bounds (archive copy of the model)
    bad, missing = [], []
    for r in recs:
        if not r['bounds']:
            continue
        src, data = from_archive(r['model'])
        if not data:
            missing.append(r['model'])
            continue
        note = []
        got = rounded(nif_box(data, note))
        if (got[0], got[1]) != (r['bounds'][0], r['bounds'][1]):
            bad.append((r['file'], r['bounds'], got, src, note))
    checked = sum(1 for r in recs if r['bounds']) - len(missing)
    print('check: %d/%d authored bounds reproduced from the archive meshes (model in no archive: %s)'
          % (checked - len(bad), checked, missing))
    for b in bad:
        print('  MISMATCH', b)
    if len(bad) > checked // 4:
        raise SystemExit('bounds code disagrees with the CK on more than a quarter of the records')

    # 2. the zero-bound records, from the winning model
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    n, nomodel = 0, []
    for r in recs:
        if r['bounds']:
            continue
        src, data = winning(r['model'])
        if not data:                                # nothing to draw, nothing to billboard: leave it alone
            nomodel.append((r['file'].rsplit(' - ', 1)[0], r['model']))
            continue
        note = []
        lo, hi = rounded(nif_box(data, note))
        raw = r['raw']
        nl = b'\r\n' if b'\r\n' in raw else b'\n'
        lines = raw.split(nl)
        i = lines.index(b'Model:')
        assert not any(l.startswith(b'ObjectBounds') for l in lines)
        lines[i:i] = [b'ObjectBounds:',
                      ('  First: %d, %d, %d' % tuple(lo)).encode(),
                      ('  Second: %d, %d, %d' % tuple(hi)).encode()]
        open(os.path.join(OUT, r['file']), 'wb').write(nl.join(lines))
        n += 1
        print('%-48s %-22s %s %s  %s%s' % (r['file'].rsplit(' - ', 1)[0], src, lo, hi, r['model'],
                                         '  [' + ','.join(sorted(set(note))) + ']' if note else ''))
    assert n + len(nomodel) == 41, (n, nomodel)
    print('wrote %d GRAS overrides; skipped, model exists nowhere: %s' % (n, nomodel))
    print('geometry-free block types passed over: %s' % sorted(IGNORED))


if __name__ == '__main__':
    main()
