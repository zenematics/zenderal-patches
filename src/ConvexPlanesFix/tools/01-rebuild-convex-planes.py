r"""Build `Zenderal - Convex Planes Fix` from the installed list -- never hand-edit its meshes.

Why: a bhkConvexVerticesShape stores its hull twice, as vertices and as plane equations
(nx, ny, nz, w), with n the outward unit normal and n.x + w = 0 on the face. Havok's ray cast
against the shape divides by n.dir per plane. JS Common Cages SE 1.03 ships every one of its
convex hulls with all plane normals (0, 0, 0) and w values that fit no face of the hull, so a ray
against one returns a NaN hit distance.

That NaN is what crashed players in the Ark bank vault (`CapitalCityBankSafe 00990F`, where
Bank of Ark SE places cage `0084AB` on base `MetalCageLongDouble01 0CE0AD`). SkyrimSE.exe 1.7.104's
function 43870 (image +0x7E9810) quicksorts hkpRootCdPoint hits (64 bytes, distance at +0x1C)
with unguarded inner loops: `while (pivot < a[j].dist) j--` never stops when the pivot is NaN
(comiss sets CF on unordered), so it walks off the array to the stack guard page:
EXCEPTION_STACK_OVERFLOW at +0x7E98BB, index around -16000, from a guard's foot IK raycast
(2026-11-03) or the crosshair pick (1.5.97, 2026-10-11).

The fix rebuilds each broken hull's planes from its own vertices (the vertices are clean): the
distinct outward faces of the convex hull, repeated to fill the stored plane count so the block
keeps its size and nothing else in the file moves. Checked against Enderal's healthy hulls: 705 of
1299 stored plane sets equal this computation exactly (the rest are simplified by the exporter).

Scope: the WINNING copy of every mesh in the list (resolver shared with CollisionMoppFix). A hull
is broken when any stored normal is shorter than 0.5. The meshes are other authors' work, so they
are generated, never committed. Re-run after PG Patcher, a mesh mod change or a load-order change;
the mod must outrank every source of the meshes it ships.

Usage (repo root):  python src/ConvexPlanesFix/tools/01-rebuild-convex-planes.py
                        [--modlist E:/Zenderal] [--profile Ultra] [--dry-run]
"""
import argparse
import importlib.util
import itertools
import math
import os
import shutil
import struct

_spec = importlib.util.spec_from_file_location(
    'mopp', os.path.join(os.path.dirname(__file__), '..', '..', 'CollisionMoppFix', 'tools',
                         '01-fix-broken-mopp.py'))
_mopp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mopp)

BS = '\\'
MOD = 'Zenderal - Convex Planes Fix'
EPS = 1e-4                  # relative to the hull's size


def blocks(d):
    """([(type, offset, size)] of every block of an SSE nif, offset of the block-size array)"""
    p = d.index(b'\n') + 1

    def take(fmt):
        nonlocal p
        v = struct.unpack_from('<' + fmt, d, p)
        p += struct.calcsize('<' + fmt)
        return v[0]
    assert take('I') == 0x14020007
    p += 1
    assert take('I') == 12
    nb = take('I')
    take('I')
    for _ in range(3):
        p += 1 + d[p]
    types = []
    for _ in range(take('H')):
        n = take('I')
        types.append(d[p:p + n].decode('latin1'))
        p += n
    ti = [take('H') for _ in range(nb)]
    sizes_at = p                                # offset of the block-size array
    sz = [take('I') for _ in range(nb)]
    nstr = take('I')
    take('I')                                   # max string length
    for _ in range(nstr):
        n = take('I')
        p += n
    n = take('I')                               # groups
    p += 4 * n
    out = []
    for i in range(nb):
        out.append((types[ti[i] & 0x7FFF], p, sz[i]))
        p += sz[i]
    return out, sizes_at


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def cross(u, v):
    return (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])


def dot(u, v):
    return u[0] * v[0] + u[1] * v[1] + u[2] * v[2]


def hull_faces(P):
    """distinct outward face planes (nx, ny, nz, w) of the convex hull of P (brute force, small P)"""
    size = max(max(abs(c) for c in p) for p in P) or 1.0
    eps = EPS * size
    out = []
    for a, b, c in itertools.combinations(range(len(P)), 3):
        n = cross(sub(P[b], P[a]), sub(P[c], P[a]))
        L = math.sqrt(dot(n, n))
        if L < 1e-9 * size * size:
            continue
        n = (n[0] / L, n[1] / L, n[2] / L)
        w = -dot(n, P[a])
        s = [dot(n, p) + w for p in P]
        if max(s) > eps:
            if min(s) < -eps:
                continue                        # points on both sides: not a face
            n, w = (-n[0], -n[1], -n[2]), -w
        if not any(abs(n[0] - f[0]) + abs(n[1] - f[1]) + abs(n[2] - f[2]) < 1e-5 and abs(w - f[3]) < eps
                   for f in out):
            out.append((n[0], n[1], n[2], w))
    return out, eps


def fix(data):
    """-> (fixed bytes or None, report lines). Raises AssertionError on anything it will not touch.

    A rebuilt plane set that fits the stored slots is written in place (padded by repeating faces);
    one that needs more slots grows the block, and its entry in the header's block-size array."""
    blks, sizes_at = blocks(data)
    edits = []                                  # (block index, offset of plane count, old count, planes)
    report = []
    for i, (ty, o, sz) in enumerate(blks):
        if ty != 'bhkConvexVerticesShape':
            continue
        p = o + 4 + 4 + 12 + 12                 # material, radius, vertices + normals properties
        nv = struct.unpack_from('<I', data, p)[0]
        p += 4
        V = [struct.unpack_from('<4f', data, p + 16 * k) for k in range(nv)]
        p += 16 * nv
        nn = struct.unpack_from('<I', data, p)[0]
        N = [struct.unpack_from('<4f', data, p + 4 + 16 * k) for k in range(nn)]
        assert p + 4 + 16 * nn == o + sz, 'block %d: size mismatch' % i
        if all(math.sqrt(dot(n, n)) >= 0.5 for n in N):
            continue
        P = [v[:3] for v in V]
        assert nv >= 4 and all(math.isfinite(c) for v in V for c in v), 'block %d: bad vertices' % i
        F, eps = hull_faces(P)
        assert len(F) >= 4, 'block %d: only %d faces' % (i, len(F))
        for f in F:                              # every face is a real supporting plane
            s = [dot(f, q) + f[3] for q in P]
            assert max(s) <= eps and sum(1 for x in s if abs(x) <= eps) >= 3, 'block %d: bad face' % i
        planes = [F[k % len(F)] for k in range(max(nn, len(F)))]
        edits.append((i, p, nn, planes))
        report.append('block %d: %d verts, %d zero normals -> %d faces in %d slots%s'
                      % (i, nv, sum(1 for n in N if math.sqrt(dot(n, n)) < 0.5), len(F), len(planes),
                         ' (grown from %d)' % nn if len(planes) > nn else ''))
    if not edits:
        return None, []
    d = bytearray(data)
    for i, p, nn, planes in reversed(edits):     # back to front: earlier offsets stay valid
        body = struct.pack('<I', len(planes)) + b''.join(struct.pack('<4f', *f) for f in planes)
        d[p:p + 4 + 16 * nn] = body
        if len(planes) != nn:
            old = struct.unpack_from('<I', d, sizes_at + 4 * i)[0]
            struct.pack_into('<I', d, sizes_at + 4 * i, old + 16 * (len(planes) - nn))
    # the result parses, every block but the edited ones is byte-identical, every hull is clean now
    nb, _ = blocks(bytes(d))
    assert len(nb) == len(blks)
    touched = {e[0] for e in edits}
    for i, ((t0, o0, s0), (t1, o1, s1)) in enumerate(zip(blks, nb)):
        assert t0 == t1
        if i not in touched:
            assert data[o0:o0 + s0] == d[o1:o1 + s1], 'block %d changed' % i
    assert data[blks[-1][1] + blks[-1][2]:] == d[nb[-1][1] + nb[-1][2]:], 'footer changed'
    return bytes(d), report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--modlist', default='E:/Zenderal')
    ap.add_argument('--profile', default='Ultra')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    mods = _mopp.enabled_mods(a.modlist, a.profile)
    plugins = _mopp.load_order(a.modlist, a.profile)

    winners = {}                                # rel.lower() -> (source, rel, reader), first seen wins
    for src, d in _mopp.loose_dirs(a.modlist, mods):
        if src == MOD:
            continue                            # never read our own output back
        md = os.path.join(d, 'meshes')
        for r, _, fs in os.walk(md):
            for fn in fs:
                if fn.lower().endswith('.nif'):
                    f = os.path.join(r, fn)
                    rel = os.path.relpath(f, d).replace('/', BS)
                    winners.setdefault(rel.lower(), (src, rel, lambda f=f: open(f, 'rb').read()))
    bsas = _mopp.archives(a.modlist, mods, a.profile, plugins)
    for src, path in reversed(bsas):
        b = _mopp.BsaIndex(path)
        for key in b.files:
            if key.endswith('.nif'):
                winners.setdefault(key, ('%s (%s)' % (os.path.basename(path), src), key,
                                         lambda b=b, key=key: b.read(key)))

    out = os.path.join(a.modlist, 'mods', MOD)
    if not a.dry_run and os.path.isdir(os.path.join(out, 'meshes')):
        shutil.rmtree(os.path.join(out, 'meshes'))
    with_cvs = 0
    written, refused = [], []
    for key, (src, rel, read) in sorted(winners.items()):
        data = read()
        if b'bhkConvexVerticesShape' not in data:
            continue
        with_cvs += 1
        try:
            fixed, report = fix(data)
        except (AssertionError, ValueError, struct.error) as e:
            refused.append((rel, src, str(e)))
            continue
        if fixed is None:
            continue
        written.append((rel, src, report))
        if not a.dry_run:
            dst = os.path.join(out, *rel.split(BS))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            open(dst, 'wb').write(fixed)
    if not a.dry_run:
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, 'meta.ini'), 'w', encoding='utf-8') as f:
            f.write('[General]\ngameName=EnderalSE\nmodid=0\nversion=1.0.0\ninstallationFile=\nrepository=\n'
                    'notes=Generated by zenderal-patches src/ConvexPlanesFix/tools/01-rebuild-convex-planes.py\n')

    for rel, src, report in written:
        print('fixed   %s  [from %s]  %d hulls' % (rel, src, len(report)))
    for rel, src, why in refused:
        print('REFUSED %s  [%s]: %s' % (rel, src, why))
    print('%s %d meshes; %d winning meshes with convex hulls of %d mesh paths, %d archives'
          % ('would write' if a.dry_run else 'wrote', len(written), with_cvs, len(winners), len(bsas)))
    if refused:
        raise SystemExit('%d meshes could not be checked or fixed (above)' % len(refused))


if __name__ == '__main__':
    main()
