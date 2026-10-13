"""Build the cloaked-horse meshes for `Zenderal - Horse Cloak Fluff Fix` from the installed Fluffworks.

Fluffworks (Fluffy Animals) gives every horse body 16 alpha-tested fur shells (`horseshell.001..016`,
~0.25 units apart, up to ~4 units off the skin). Enderal's cloth barding for the Ark guard horses
(`Enderal\\armor\\horsecloak\\horsecloaksaddle.nif`, armour `HorseCloak 14482A`) was fitted to the
vanilla skin, so the outer shells poke through it.

For each Fluffworks colour mesh the cloak skins use, this script:
  1. casts a ray from every skin vertex (`horse:0`) along its normal and records how far away the
     cloak is (infinite where the cloak does not cover that point);
  2. for every shell vertex, finds its nearest skin vertex and its height above it; if that height
     reaches the cloak (within MARGIN), sinks the vertex just under the skin (INSET).
Inner shells that stay below the cloth are kept, and fur is untouched wherever there is no cloak.
Only vertex positions change: the output is byte-identical to Fluffworks' file apart from those floats.

The meshes are Fluffworks' work, so they are generated from the user's own install, never committed.

Usage:  python 01-trim-fluff-under-cloak.py [<mods dir>] [--dry-run]     (default E:/Zenderal/mods)
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', '..', 'EnderalTextureRestores', 'tools'))
from nif import Nif  # noqa: E402

MOD = 'Zenderal - Horse Cloak Fluff Fix'
FLUFF_MOD = 'Fluffworks (Fluffy Animals)'
FLUFF_DIR = 'meshes/actors/horse/character assets'
CLOAK_BSA = 'E - Meshes.bsa'
CLOAK_PATH = 'meshes\\enderal\\armor\\horsecloak\\horsecloaksaddle.nif'
OUT_DIR = 'meshes/zenderal/horsecloakfluff'

# (Fluffworks mesh, output mesh). Both cloak skins: NakedHorseBlacknWhiteCloakAA 144833 and
# NakedHorsePalominoCloakAA 144836 - the colours Fluffworks' own NakedHorse*AA overrides map to these files.
MESHES = [('HorseBnW.nif', 'HorseBnWCloak.nif'), ('HorsePalomino.nif', 'HorsePalominoCloak.nif')]

MARGIN = 1.5      # sink fur that comes within this many units of the cloth (animation slack)
INSET = 0.3       # how far under the skin a sunk vertex goes
RAY_BACKOFF = 1.0  # start rays this far inside the skin, so cloth touching the skin still counts
EXPECT_SHELLS = 16


def read_bsa_file(bsa_path, want):
    import importlib
    tex = importlib.import_module('01-extract-enderal-textures')
    data = tex.read_from_bsa(bsa_path, want)
    assert data, f'{want} not found in {bsa_path}'
    return data


def ray_hits(origins, dirs, tris):
    """Distance along each ray to the nearest triangle hit (t > 0), inf where none. Möller-Trumbore."""
    v0, v1, v2 = tris[:, 0], tris[:, 1], tris[:, 2]
    e1, e2 = v1 - v0, v2 - v0
    best = np.full(len(origins), np.inf)
    for s in range(0, len(origins), 256):
        o = origins[s:s + 256, None, :]
        d = dirs[s:s + 256, None, :]
        p = np.cross(d, e2[None])
        det = (e1[None] * p).sum(-1)
        ok = np.abs(det) > 1e-9
        inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0)
        tv = o - v0[None]
        u = (tv * p).sum(-1) * inv
        q = np.cross(tv, e1[None])
        v = (d * q).sum(-1) * inv
        t = (e2[None] * q).sum(-1) * inv
        hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0)
        best[s:s + 256] = np.where(hit, t, np.inf).min(1)
    return best


def nearest(points, ref):
    out = np.empty(len(points), int)
    for s in range(0, len(points), 512):
        d = ((points[s:s + 512, None, :] - ref[None]) ** 2).sum(-1)
        out[s:s + 512] = d.argmin(1)
    return out


def cloak_triangles(data_dir, scratch):
    blob = read_bsa_file(os.path.join(data_dir, CLOAK_BSA), CLOAK_PATH)
    tmp = os.path.join(scratch, 'horsecloaksaddle.nif')
    open(tmp, 'wb').write(blob)
    n = Nif(tmp)
    shapes = n.shapes()
    assert [s['name'] for s in shapes] == ['Horse:Cloak'], [s['name'] for s in shapes]
    pos = n.positions(shapes[0])
    return pos[shapes[0]['tris']]


def trim(src, dst, ctris, dry):
    n = Nif(src)
    shapes = {s['name']: s for s in n.shapes()}
    shells = sorted(k for k in shapes if k.startswith('horseshell.'))
    assert len(shells) == EXPECT_SHELLS, shells
    skin = shapes['horse:0']
    B = n.positions(skin)
    N = n.normals(skin)
    N /= np.linalg.norm(N, axis=1, keepdims=True)
    # distance from each skin vertex to the cloak, measured from the skin surface
    reach = ray_hits(B - N * RAY_BACKOFF, N, ctris) - RAY_BACKOFF
    covered = np.isfinite(reach) & (reach < 15)   # ignore far hits through the body/cloak's other side
    reach = np.where(covered, reach, np.inf)
    print(f'  {os.path.basename(src)}: {covered.sum()}/{len(B)} skin vertices under the cloak, '
          f'cloak gap median {np.median(reach[covered]):.2f}')
    total = moved = 0
    for name in shells:
        sh = shapes[name]
        P = n.positions(sh)
        j = nearest(P, B)
        h = ((P - B[j]) * N[j]).sum(1)
        hit = h > reach[j] - MARGIN
        P2 = P.copy()
        P2[hit] -= N[j[hit]] * (h[hit] + INSET)[:, None]
        total += len(P)
        moved += hit.sum()
        if not dry:
            n.set_positions(sh, P2)
        print(f'    {name}: sank {hit.sum():4}/{len(P)}  (height median {np.median(h):.2f})')
    assert moved > 0, 'nothing trimmed - cloak/body alignment changed?'
    assert moved < total, 'every vertex trimmed - coverage test is wrong'
    if not dry:
        before = os.path.getsize(src)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        n.save(dst)
        assert os.path.getsize(dst) == before
        # Re-read: everything except the shells' positions must be untouched.
        a, b = Nif(src), Nif(dst)
        assert a.blocks == b.blocks and a.strings == b.strings
        diff = np.frombuffer(bytes(a.data), np.uint8) != np.frombuffer(bytes(b.data), np.uint8)
        allowed = np.zeros(len(a.data), bool)
        for sh in b.shapes():
            if sh['name'] in shells:
                for i in range(sh['nvert']):
                    o = sh['vdata'] + i * sh['vsize']
                    allowed[o:o + 12] = True
        assert not (diff & ~allowed).any(), 'bytes changed outside shell vertex positions'
        print(f'  -> {dst} ({diff.sum()} bytes changed, all in shell positions)')
    return moved, total


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    dry = '--dry-run' in sys.argv
    mods = args[0] if args else 'E:/Zenderal/mods'
    data_dir = os.path.join(os.path.dirname(os.path.normpath(mods)), 'Stock game', 'Data')
    scratch = os.environ.get('TEMP', '.')
    ctris = cloak_triangles(data_dir, scratch)
    print(f'cloak: {len(ctris)} triangles')
    for src_name, dst_name in MESHES:
        src = os.path.join(mods, FLUFF_MOD, FLUFF_DIR, src_name)
        dst = os.path.join(mods, MOD, OUT_DIR, dst_name)
        trim(src, dst, ctris, dry)


if __name__ == '__main__':
    main()
