"""Build the pus beetle skeleton for `Zenderal - Pus Beetle Fixes` from the installed Pus Beetle Replacer.

Arrows and spells hit a creature's ragdoll capsules (the skeleton's bhkCapsuleShapes), not its visible mesh. Pus Beetle
Replacer (Enderal SE Nexus 48) puts 4thUnknown's kwama forager on the chaurus skeleton but keeps the chaurus capsules:
22.6% of the new body sits more than 10 units outside them (vanilla chaurus: 3.1%), up to 34 on the tail and 23 on the
head, so many ranged hits passed straight through.

This copies the replacer's skeleton.nif and grows each capsule's radius by the 95th percentile of how far the vertices it
is nearest to lie outside it (never shrinking, capped at +25 units). Body vertices are put in skeleton space through
their dominant bone (boneWorld * boneBind * v). It prints the coverage before and after and asserts the result is at
least as good as vanilla's (<= 5% of vertices more than 10 units outside).

The skeleton is the mod author's work, so it is generated from the user's own install, never committed.

Usage:  python 01-widen-hit-capsules.py [<mods dir>] [--dry-run]     (default E:/Zenderal/mods)
"""
import os
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'HorseCloakFluffFix', 'tools'))
from nif import Nif, Reader  # noqa: E402

MOD = 'Zenderal - Pus Beetle Fixes'
SRC_MOD = 'Pus Beetle Replacer'
DIR = os.path.join('Meshes', 'actors', 'chaurus', 'character assets')
HK = 69.99          # game units per Havok unit
CAP = 25.0          # largest radius increase, game units


def world_transforms(nif):
    nodes = nif.nodes()
    parent = {}
    for i in nodes:
        r = Reader(nif.data, nif.blocks[i][1])
        r.skip(4); r.skip(4 * r.take('I')); r.skip(4 + 4 + 12 + 36 + 4 + 4)
        for c in [r.take('i') for _ in range(r.take('I'))]:
            if c >= 0:
                parent[c] = i
    cache = {}

    def M(i):
        if i not in cache:
            n = nodes[i]
            T = np.eye(4); T[:3, :3] = n['R'] * n['s']; T[:3, 3] = n['t']
            cache[i] = M(parent[i]) @ T if parent.get(i) in nodes else T
        return cache[i]
    return {nodes[i]['name']: M(i) for i in nodes}, {i: M(i) for i in nodes}


def capsules(nif):
    """(shape block offset, world point a, world point b, radius) per ragdoll capsule."""
    _, wt = world_transforms(nif)
    out = []
    for typ, p, _ in nif.blocks:
        if typ != 'bhkBlendCollisionObject':
            continue
        target, _, body = struct.unpack_from('<iHi', nif.data, p)
        shape = struct.unpack_from('<i', nif.data, nif.blocks[body][1])[0]
        assert nif.blocks[shape][0] == 'bhkCapsuleShape', nif.blocks[shape][0]
        sp = nif.blocks[shape][1]
        r0, = struct.unpack_from('<f', nif.data, sp + 4)
        r1, = struct.unpack_from('<f', nif.data, sp + 28)
        r2, = struct.unpack_from('<f', nif.data, sp + 44)
        assert abs(r0 - r1) < 1e-4 and abs(r0 - r2) < 1e-4, (r0, r1, r2)
        p1 = np.array(struct.unpack_from('<3f', nif.data, sp + 16)) * HK
        p2 = np.array(struct.unpack_from('<3f', nif.data, sp + 32)) * HK
        M = wt[target]
        out.append((sp, (M @ np.append(p1, 1))[:3], (M @ np.append(p2, 1))[:3], r0 * HK))
    return out


def body_points(skel, skin):
    bonew, _ = world_transforms(skel)
    knodes = skin.nodes()
    pts = []
    for sh in skin.shapes():
        if sh['skin'] < 0:
            continue
        pos = skin.positions(sh)
        w, idx = skin.skin_info(sh)
        dom = idx[np.arange(len(idx)), w.argmax(1)]
        for v, bi in zip(pos, dom):
            bname = knodes[sh['bones'][bi]]['name']
            bR, bt, bs = sh['boneT'][bi]
            B = np.eye(4); B[:3, :3] = bR * bs; B[:3, 3] = bt
            pts.append((bonew[bname] @ B @ np.append(v, 1))[:3])
    return np.array(pts)


def outside(pts, caps, radii):
    D = []
    for (_, a, b, _), r in zip(caps, radii):
        ab = b - a
        t = np.clip(((pts - a) @ ab) / max(ab @ ab, 1e-9), 0, 1)
        D.append(np.linalg.norm(pts - (a + t[:, None] * ab), axis=1) - r)
    return np.array(D)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    dry = '--dry-run' in sys.argv
    mods = args[0] if args else 'E:/Zenderal/mods'
    src = os.path.join(mods, SRC_MOD, DIR)
    skel = Nif(os.path.join(src, 'skeleton.nif'))
    pts = body_points(skel, Nif(os.path.join(src, 'ChauurusSkin.nif')))
    caps = capsules(skel)
    assert len(caps) == 26, len(caps)

    old = [c[3] for c in caps]
    D = outside(pts, caps, old)
    near = D.argmin(0)
    new = []
    for ci, r in enumerate(old):
        dd = D[ci, near == ci]
        grow = min(CAP, max(0.0, float(np.percentile(dd, 95)))) if len(dd) else 0.0
        new.append(r + grow)

    before = D.min(0)
    after = outside(pts, caps, new).min(0)
    print(f'body verts {len(pts)}; outside by > 10 units: {100 * np.mean(before > 10):.1f}% -> {100 * np.mean(after > 10):.1f}%,'
          f' max {before.max():.0f} -> {after.max():.0f}; radii grown {sum(n > o for n, o in zip(new, old))}/26,'
          f' largest +{max(n - o for n, o in zip(new, old)):.1f}')
    assert np.mean(after > 10) <= 0.05, 'coverage still worse than vanilla chaurus'

    for (sp, _, _, _), r in zip(caps, new):
        for off in (4, 28, 44):
            struct.pack_into('<f', skel.data, sp + off, r / HK)
    if not dry:
        out = os.path.join(mods, MOD, DIR, 'skeleton.nif')
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, 'wb') as f:
            f.write(skel.data)
        print('wrote', out)


if __name__ == '__main__':
    main()
