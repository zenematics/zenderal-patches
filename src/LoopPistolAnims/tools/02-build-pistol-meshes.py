"""Write third-person copies of the 8 Gentleman's Flintlock pistol meshes, rotated to sit in Loop's grip.

Loop's aim/fire pose (01-build-loop-pistol-anims.py) is a LEFT-hand pose authored around his own `pistol.nif`,
whose barrel runs straight along the attach node's +Y with the grip angled back toward +X; in his aim clip the
left-hand attach node (Shield) points +Y level forward and +X down (FK, 2026-10-17). The Gentleman's pistols are
staff meshes: the GRIP runs along +Y and the barrel slants 20-30 degrees toward +X, so in Loop's pose the
gun points off to the side. Each copy rotates its one NiTriShape about
Z by the angle that lays its barrel on Loop's (fitted from side-view overlays; barrel line and the grip at
the hand both land on Loop's). Only the NiTriShape's 52-byte transform changes; geometry, shader and
collision are byte-identical (collision stays unrotated, so a dropped pistol's physics shape is off by the
same angle).

First person keeps the originals: the WEAP FirstPersonModel statics point at the same files and first person
plays vanilla staff clips. The Flintlock Overhaul's WEAP overrides point Model at these copies
(src/FlintlockOverhaul/tools/01-build-damage.py, LOOP_MODELS).

Copies are Gentleman's assets, never committed. Written into the `Zenderal - Loop Pistol Animations` MO2 mod.

Usage:  python 02-build-pistol-meshes.py [<mods dir>]     (default E:/Zenderal/mods)
"""
import os, sys, math, struct, hashlib

MOD = 'Zenderal - Loop Pistol Animations'
SOURCE_MOD = "A Gentleman's Flintlock Armoury - Special Edition"
SRC_DIR = ['meshes', 'PowderMagePack', 'weapons']
OUT_DIR = ['meshes', 'Zenderal', 'LoopPistols']
# mesh (relative to PowderMagePack/weapons) -> rotation about Z in degrees (counterclockwise, +Y toward -X)
ROTATIONS = {
    'BattlestainedFP/FlintlockPistol.nif': 25.8,
    'BattlestainedFP/FlintlockPistol01.nif': 25.8,
    'BattlestainedFP/FlintlockPistol02.nif': 25.8,
    'BattlestainedFP/FlintlockPistol03.nif': 25.8,
    'PistoolFP/Pistool.nif': 19.6,
    'LowPolyFP/Pistool02.nif': 21.4,
    'LowPolyFP/Pistool03.nif': 21.4,
    'LowPolyFP/Pistool04.nif': 24.0,
}
# After the rotation, move every mesh along the attach node's +X (straight down in Loop's aim pose) so the grip
# sits in the fist. In game 2026-10-17 (v4) the barrel aimed level but the stock rode ~35 px above the wrist at
# ~9 px/unit; 4 units.
DROP = 4.0


def blocks(b):
    """(type, offset) of every block of a Skyrim LE/SE NIF (20.2.0.7, BS stream 83/100)."""
    o = b.index(b'\n') + 1 + 5
    _, nb, bsver = struct.unpack_from('<III', b, o); o += 12
    if bsver not in (83, 100):  # the Gentleman's meshes are Skyrim LE (83); same header layout up to here
        raise SystemExit(f'unexpected BS stream version {bsver}')
    for _ in range(3):
        o += 1 + b[o]
    nt, = struct.unpack_from('<H', b, o); o += 2
    types = []
    for _ in range(nt):
        n, = struct.unpack_from('<I', b, o); o += 4
        types.append(b[o:o + n].decode()); o += n
    idx = struct.unpack_from(f'<{nb}H', b, o); o += 2 * nb
    sizes = struct.unpack_from(f'<{nb}I', b, o); o += 4 * nb
    ns, _ = struct.unpack_from('<II', b, o); o += 8
    for _ in range(ns):
        n, = struct.unpack_from('<I', b, o); o += 4 + n
    ng, = struct.unpack_from('<I', b, o); o += 4 + 4 * ng
    out = []
    for i in range(nb):
        out.append((types[idx[i]], o)); o += sizes[i]
    return out


def rotate_shape(b, off, deg, drop=0.0):
    """Pre-multiply a NiAVObject's transform by a rotation about Z, then move it `drop` along +X."""
    p = off + 4
    ne, = struct.unpack_from('<I', b, p); p += 4 + 4 * ne + 8  # extra data, controller, flags
    t = struct.unpack_from('<3f', b, p)
    r = struct.unpack_from('<9f', b, p + 12)
    m = [r[0:3], r[3:6], r[6:9]]
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    rz = [[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]]
    m2 = [[sum(rz[i][k] * m[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
    t2 = [sum(rz[i][k] * t[k] for k in range(3)) for i in range(3)]
    t2[0] += drop
    patch = struct.pack('<3f', *t2) + struct.pack('<9f', *(v for row in m2 for v in row))
    return b[:p] + patch + b[p + 48:]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    mods = args[0] if args else 'E:/Zenderal/mods'
    if '--test-loop-mesh' in sys.argv:
        # diagnostic: every copy becomes Loop's own pistol.nif, the mesh his pose was made for
        loop = os.path.join(mods, 'Simple Pistol Shooting Animation by loop 3.0 - SSE', 'meshes', 'weapons',
                            'pistol animation by loop', 'pistol.nif')
        for rel in ROTATIONS:
            dst = os.path.join(mods, MOD, *OUT_DIR, *rel.split('/'))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(loop, 'rb') as src, open(dst, 'wb') as fh:
                fh.write(src.read())
            print(f'TEST  Loop pistol.nif -> {rel}')
        return
    for rel, deg in ROTATIONS.items():
        src = os.path.join(mods, SOURCE_MOD, *SRC_DIR, *rel.split('/'))
        dst = os.path.join(mods, MOD, *OUT_DIR, *rel.split('/'))
        b = open(src, 'rb').read()
        shapes = [off for t, off in blocks(b) if t in ('NiTriShape', 'BSTriShape')]
        if len(shapes) != 1:
            raise SystemExit(f'{rel}: expected one shape, found {len(shapes)}')
        out = rotate_shape(b, shapes[0], deg, DROP)
        if len(out) != len(b):
            raise SystemExit(f'{rel}: size changed')
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, 'wb') as fh:
            fh.write(out)
        print(f'{hashlib.sha1(out).hexdigest()[:12]}  {deg:5.1f} deg  {rel}')
    print(f'{len(ROTATIONS)} meshes -> {os.path.join(mods, MOD, *OUT_DIR)}')


if __name__ == '__main__':
    main()
