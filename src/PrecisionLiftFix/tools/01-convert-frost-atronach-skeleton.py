"""Rebuild the frost atronach skeleton with plain bhkRigidBody ragdoll bodies, for Precision.

Why (2026-10-12): Ice Elementals (AtronachFrostRace 0131F6) float upward on every Precision hit. A debug
build of ZenPrecisionLiftFix.dll logged every ragdoll body's height: the WHOLE ragdoll rises ~15-20 units
together within one physics step and stays there however hard its root is driven down - a constant
offset between the animation pose and the ragdoll's targets, not an impulse and not ground contact.

The frost atronach is the only skeleton in the game whose limb bodies are bhkRigidBodyT (8 of them,
box shapes, with a local offset from their bone). Every other skeleton uses plain bhkRigidBody, which
stores the bone's own bind transform (translation = node world / skeleton scale / havok scale,
rotation = node world rotation - verified on every body of the flame atronach and on the frost
atronach's own COM). adamhynek's PLANCK had to add rigidBodyT handling when mapping pose <-> ragdoll
"mainly relates to frost atronach" (adamhynek/activeragdoll 61bce7e538); Precision has none.

So each bhkRigidBodyT becomes a bhkRigidBody in the normal convention, with its old local offset L
moved INTO the body frame: the box is wrapped in a new bhkConvexTransformShape carrying L, the centre
of mass becomes L(center), and its side of each bhkRagdollConstraint gets pivot' = L(pivot). Every L
here has identity rotation (asserted), so inertia and constraint axes are unchanged. In the body's own
frame the collision geometry and joints are exactly where they were.

Input: XPMSSE's frost atronach skeleton (the one that otherwise wins). Output: the MO2 mod
`Zenderal - Precision Lift Fix`, which must sort ABOVE XPMSSE and `Zenderal - Frost Atronach SE Fix`.
The skeleton is XPMSSE's, so it is generated, never committed.

Usage: python 01-convert-frost-atronach-skeleton.py [<modlist root>]   (default E:/Zenderal)
"""
import os, struct, sys, math

ROOT = sys.argv[1] if len(sys.argv) > 1 else 'E:/Zenderal'
REL = 'meshes/actors/atronachfrost/character assets/skeleton.nif'
SRC = os.path.join(ROOT, 'mods', 'XP32 Maximum Skeleton Special Extended', REL)
OUT = os.path.join(ROOT, 'mods', 'Zenderal - Precision Lift Fix', REL)
HK = 1.0 / 69.99125  # Skyrim units -> Havok

# bhkRigidBody (SSE) field offsets inside the block, verified against PyNifly on every body
RB_SHAPE, RB_TRANS, RB_ROT, RB_INERTIA, RB_CENTER, RB_MASS = 0, 52, 68, 116, 164, 180
# bhkRagdollConstraint: CInfo (u32 n, i32 A, i32 B, u32 prio) then Twist/Plane/Motor/Pivot A, then B
RC_A, RC_B, RC_PIVOT_A, RC_PIVOT_B = 4, 8, 16 + 48, 16 + 112
EXPECTED_T_BODIES = 8


class Nif:
    def __init__(self, path):
        d = open(path, 'rb').read()
        self.d = d
        i = d.index(b'\n') + 1
        self.ver = struct.unpack_from('<I', d, i)[0]; i += 4 + 1
        self.nb_off = i + 4
        self.uv, self.nb, self.bs = struct.unpack_from('<III', d, i); i += 12
        for _ in range(3):
            i += 1 + d[i]
        self.types_off = i
        nt = struct.unpack_from('<H', d, i)[0]; i += 2
        self.types = []
        for _ in range(nt):
            ln = struct.unpack_from('<I', d, i)[0]; i += 4
            self.types.append(d[i:i + ln].decode()); i += ln
        self.idx = list(struct.unpack_from('<%dH' % self.nb, d, i)); i += 2 * self.nb
        self.sizes = list(struct.unpack_from('<%dI' % self.nb, d, i)); i += 4 * self.nb
        self.strings_off = i  # num strings onward is copied verbatim
        ns, _ = struct.unpack_from('<II', d, i); i += 8
        for _ in range(ns):
            i += 4 + struct.unpack_from('<I', d, i)[0]
        ng = struct.unpack_from('<I', d, i)[0]; i += 4 + 4 * ng
        self.blocks_off = i
        self.blocks = []
        for s in self.sizes:
            self.blocks.append(bytearray(d[i:i + s])); i += s
        self.footer = d[i:]

    def type(self, b):
        return self.types[self.idx[b]]

    def add_block(self, type_name, data):
        if type_name not in self.types:
            self.types.append(type_name)
        self.idx.append(self.types.index(type_name))
        self.sizes.append(len(data))
        self.blocks.append(bytearray(data))
        return len(self.blocks) - 1

    def save(self, path):
        d = self.d
        out = bytearray(d[:self.nb_off])
        out += struct.pack('<I', len(self.blocks))
        out += d[self.nb_off + 4:self.types_off]
        out += struct.pack('<H', len(self.types))
        for t in self.types:
            out += struct.pack('<I', len(t)) + t.encode()
        out += struct.pack('<%dH' % len(self.idx), *self.idx)
        out += struct.pack('<%dI' % len(self.sizes), *[len(b) for b in self.blocks])
        out += d[self.strings_off:self.blocks_off]
        for b in self.blocks:
            out += b
        out += self.footer
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, 'wb').write(out)


def f4(buf, off):
    return list(struct.unpack_from('<4f', buf, off))


def put4(buf, off, v):
    struct.pack_into('<4f', buf, off, *v)


def node_world(nif, pyn_nodes):
    """name -> (translation, rotation matrix rows, scale) via PyNifly (reads the same file)."""
    out = {}
    for name, node in pyn_nodes.items():
        g = node.global_transform
        out[name] = (list(g.translation), [list(r) for r in g.rotation], g.scale)
    return out


def mat2quat(m):
    tr = m[0][0] + m[1][1] + m[2][2]
    if tr > 0:
        s = math.sqrt(tr + 1) * 2
        return ((m[2][1] - m[1][2]) / s, (m[0][2] - m[2][0]) / s, (m[1][0] - m[0][1]) / s, 0.25 * s)
    if m[0][0] > m[1][1] and m[0][0] > m[2][2]:
        s = math.sqrt(1 + m[0][0] - m[1][1] - m[2][2]) * 2
        return (0.25 * s, (m[0][1] + m[1][0]) / s, (m[0][2] + m[2][0]) / s, (m[2][1] - m[1][2]) / s)
    if m[1][1] > m[2][2]:
        s = math.sqrt(1 + m[1][1] - m[0][0] - m[2][2]) * 2
        return ((m[0][1] + m[1][0]) / s, 0.25 * s, (m[1][2] + m[2][1]) / s, (m[0][2] - m[2][0]) / s)
    s = math.sqrt(1 + m[2][2] - m[0][0] - m[1][1]) * 2
    return ((m[0][2] + m[2][0]) / s, (m[1][2] + m[2][1]) / s, 0.25 * s, (m[1][0] - m[0][1]) / s)


def main():
    pyn_dir = os.environ.get('PYNIFLY', 'E:/Zen Tools/PyNifly V29.1.0/io_scene_nifly')
    sys.path.insert(0, pyn_dir)
    from pyn.pynifly import NifFile  # noqa: E402

    nif = Nif(SRC)
    assert nif.bs == 100, f'{SRC}: expected an SE skeleton, got stream {nif.bs}'
    src = NifFile(SRC)
    world = node_world(nif, src.nodes)
    body_node = {}
    for name, node in src.nodes.items():
        co = node.collision_object
        if co is not None and co.body is not None and hasattr(co.body.properties, 'translation'):
            body_node[co.body.id] = name

    # The plain body (COM) must already follow the convention - proves our reading of it.
    for b, name in body_node.items():
        if nif.type(b) == 'bhkRigidBody':
            t, R, s = world[name]
            st = f4(nif.blocks[b], RB_TRANS)
            assert all(abs(st[i] * s / HK - t[i]) < 0.05 for i in range(3)), f'{name}: plain body off-convention'

    t_bodies = [b for b in body_node if nif.type(b) == 'bhkRigidBodyT']
    assert len(t_bodies) == EXPECTED_T_BODIES, f'expected {EXPECTED_T_BODIES} bhkRigidBodyT, found {len(t_bodies)}'
    constraints = [b for b in range(len(nif.blocks)) if nif.type(b) == 'bhkRagdollConstraint']
    plain_type = nif.types.index('bhkRigidBody')
    shifted_pivots = 0

    for b in t_bodies:
        name = body_node[b]
        blk = nif.blocks[b]
        L_t = f4(blk, RB_TRANS)
        L_q = f4(blk, RB_ROT)
        assert max(abs(L_q[0]), abs(L_q[1]), abs(L_q[2])) < 1e-6 and abs(abs(L_q[3]) - 1) < 1e-6, f'{name}: offset has a rotation'
        shape = struct.unpack_from('<i', blk, RB_SHAPE)[0]
        assert nif.type(shape) == 'bhkBoxShape', f'{name}: shape is {nif.type(shape)}'
        box = nif.blocks[shape]
        material, radius = struct.unpack_from('<If', box, 0)

        # new bhkConvexTransformShape: Shape, Material, Radius, Unused 8, Matrix44 (column-major)
        # hkTransform layout, as SMIM's milllogpile.nif stores it: translation in floats 12-14, w = 0
        m = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, L_t[0], L_t[1], L_t[2], 0]
        cts = struct.pack('<iIf8x16f', shape, material, radius, *m)
        assert len(cts) == 84
        new_shape = nif.add_block('bhkConvexTransformShape', cts)

        t, R, s = world[name]
        q = mat2quat(R)
        put4(blk, RB_TRANS, [t[0] / s * HK, t[1] / s * HK, t[2] / s * HK, L_t[3]])
        put4(blk, RB_ROT, list(q))
        struct.pack_into('<i', blk, RB_SHAPE, new_shape)
        c = f4(blk, RB_CENTER)
        put4(blk, RB_CENTER, [c[0] + L_t[0], c[1] + L_t[1], c[2] + L_t[2], c[3]])
        nif.idx[b] = plain_type

        for cb in constraints:
            cblk = nif.blocks[cb]
            a, bb = struct.unpack_from('<ii', cblk, RC_A)
            for ent, off in ((a, RC_PIVOT_A), (bb, RC_PIVOT_B)):
                if ent == b:
                    p = f4(cblk, off)
                    put4(cblk, off, [p[0] + L_t[0], p[1] + L_t[1], p[2] + L_t[2], p[3]])
                    shifted_pivots += 1
        print(f'  {name:24s} offset ({L_t[0] / HK:6.1f} {L_t[1] / HK:6.1f} {L_t[2] / HK:6.1f}) -> transform shape block {new_shape}')

    # each limb is in exactly one constraint as child and the inner limbs in one more as parent: 8 + 4
    assert shifted_pivots == 12, f'expected 12 shifted pivots, got {shifted_pivots}'
    nif.save(OUT)

    # ---- read back and assert ----
    chk = Nif(OUT)
    assert len(chk.blocks) == len(Nif(SRC).blocks) + EXPECTED_T_BODIES
    assert sum(1 for b in range(len(chk.blocks)) if chk.type(b) == 'bhkRigidBodyT') == 0
    assert sum(1 for b in range(len(chk.blocks)) if chk.type(b) == 'bhkConvexTransformShape') == EXPECTED_T_BODIES
    out = NifFile(OUT)
    for name, node in out.nodes.items():
        co = node.collision_object
        if co is None or co.body is None or not hasattr(co.body.properties, 'translation'):
            continue
        assert co.body.blockname == 'bhkRigidBody', name
        t, R, s = world[name]
        st = co.body.properties.translation
        assert all(abs(st[i] * s / HK - t[i]) < 0.05 for i in range(3)), f'{name}: readback translation off'
    print(f'Wrote {OUT}: {EXPECTED_T_BODIES} bodies converted, {shifted_pivots} constraint pivots moved')


if __name__ == '__main__':
    main()
