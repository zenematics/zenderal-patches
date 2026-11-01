r"""Andrasta's Owl's body: Mihail's Barn Owl mesh re-rigged onto Triumvirate's raven skeleton - never hand-edit the output.

Mihail's Barn Owls (mihailowl.esp, curator-installed 2026-10-23) adds no creature, only an animated Activator: owl1.nif
flies a baked path, owl1go.nif flaps in place. Both are skinned to the owl's OWN bones (BoneMain, BoneL/RWing01/02 under
the vanilla bird-of-prey rig FXbirdOPrey02NoNest -> ... -> BirdOPreyBody03), so worn as a creature skin on the raven
(Triumvirate's Call Raven race: Mihail's crow skeleton, chaurus-flyer bones and behavior) it drew nothing - the bones
are not in that skeleton (in game 2026-10-23: the spawn sound, no owl).

This rebuilds owl1go.nif's two shapes as an SE skinned mesh bound to the raven skeleton:
  * pose: each vertex in the owl's own displayed bind (BirdOPreyBody03's 0.5 scale x the skin-to-bone transforms'
    0.667 scale and ~77 degree pitch: a horizontal owl facing +Y, 95 units across), scaled x1.5 to the crow's 143-unit
    wingspan, then moved so the owl's shoulders sit on the midpoint of the crow's two top-wing bones;
  * weights: BoneMain -> ChaurusFlyerNeck (what the crow's body follows), BoneLWing01/02 -> ChaurusFlyerTopWingLeft,
    BoneRWing01/02 -> ChaurusFlyerTopWingRight; a vertex's existing body/wing blend is kept;
  * binds: the crow mesh's (basecrow.nif) own skin-to-bone transforms and bone nodes for those three bones, so the
    owl binds exactly as the crow did and flaps with the raven's flight animations; partition = the crow's.
Shaders, textures (Mihail's owl.dds / owl_n.dds) and alpha come from owl1go.nif.

Output: <MO2 mods>/Zenderal - Prophecy/meshes/Zenderal/Prophecy/BarnOwl.nif (built from two mods' assets - not committed).
Usage: python 05-build-owl-mesh.py [<MO2 mods dir>]
"""
import json, math, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
TOOLS = json.load(open(os.path.join(REPO, '.claude', 'config', 'tools.json'), encoding='utf-8-sig'))
sys.path.insert(0, TOOLS['pynifly'])
sys.path.insert(0, HERE)
from pyn.pynifly import NifFile, nifly  # noqa: E402
from pyn.nifdefs import PynBufferTypes, BSTriShapeBuf  # noqa: E402
import _bsa  # noqa: E402

MODS = sys.argv[1] if len(sys.argv) > 1 else r'E:\Zenderal\mods'
OWL = os.path.join(MODS, 'Barn Owls- Mihail Monsters and Animals (SE-AE)', 'Meshes', 'Mihail Monsters and Animals',
                   'Chicken', 'Owl', 'owl1go.nif')
TVR_BSA = os.path.join(MODS, 'Triumvirate - Mage Archetypes', 'Triumvirate - Mage Archetypes.bsa')
CROW = 'mihail monsters and animals/dwarven centurion/old god/magic/basecrow.nif'
OUT = os.path.join(MODS, 'Zenderal - Prophecy', 'meshes', 'Zenderal', 'Prophecy', 'BarnOwl.nif')
BONE_MAP = {'BoneMain': 'ChaurusFlyerNeck', 'BoneHead': 'ChaurusFlyerNeck', 'BoneTail01': 'ChaurusFlyerNeck',
            'BoneTail02': 'ChaurusFlyerNeck',
            'BoneLWing01': 'ChaurusFlyerTopWingLeft', 'BoneLWing02': 'ChaurusFlyerTopWingLeft',
            'BoneRWing01': 'ChaurusFlyerTopWingRight', 'BoneRWing02': 'ChaurusFlyerTopWingRight'}
SHOULDERS = ('BoneLWing02', 'BoneRWing01')            # the owl's inner wing bones
CROW_WINGS = ('ChaurusFlyerTopWingLeft', 'ChaurusFlyerTopWingRight')
SCALE = 1.5                                            # owl's displayed 95-unit wingspan -> the crow's 143


def mat(x):
    """TransformBuf -> (3x3 rows, translation, scale)"""
    return [list(r) for r in x.rotation], list(x.translation), x.scale


def apply(m, v):
    r, t, s = m
    return [s * sum(r[i][j] * v[j] for j in range(3)) + t[i] for i in range(3)]


def compose(a, b):
    """a after b: p -> a(b(p))"""
    ra, ta, sa = a
    rb, tb, sb = b
    r = [[sum(ra[i][k] * rb[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
    return r, apply(a, tb), sa * sb


def world(nif, name):
    node = nif.nodes[name]
    m = mat(node.transform)
    p = getattr(node, 'parent', None)
    return compose(world(nif, p.name), m) if p is not None and p.name in nif.nodes else m


def main():
    owl = NifFile(OWL)
    d, l = _bsa.listing(TVR_BSA)
    key = [k for k in l if k.lower().replace('\\', '/').endswith(CROW)]
    assert len(key) == 1, 'basecrow.nif not in Triumvirate BSA'
    tmp = OUT + '.crow.tmp'
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(tmp, 'wb').write(_bsa.read(d, l[key[0]]))
    crow = NifFile(tmp)

    # the crow's binds for the three target bones
    s2b, partition = {}, None
    for s in crow.shapes:
        for b in s.bone_names:
            s2b.setdefault(b, s.get_shape_skin_to_bone(b))
        if partition is None and s.partitions:
            partition = s.partitions[0]
    targets = sorted(set(BONE_MAP.values()))
    assert all(b in s2b and b in crow.nodes for b in targets), 'crow bones missing'
    assert partition is not None, 'crow mesh has no partition'

    # the owl's displayed bind: bone world (rig) x skin-to-bone, per shape (all its bones share one rotation)
    shapes = owl.shapes
    assert [s.name for s in shapes] == ['a', 'b'], [s.name for s in shapes]
    disp = {}
    for s in shapes:
        b0 = s.bone_names[0]
        disp[s.name] = compose(world(owl, b0), mat(s.get_shape_skin_to_bone(b0)))
        for b in s.bone_names:   # every bone must agree on the displayed bind
            m = compose(world(owl, b), mat(s.get_shape_skin_to_bone(b)))
            assert max(abs(x - y) for x, y in zip(apply(m, [10, 20, 30]), apply(disp[s.name], [10, 20, 30]))) < 1e-2, (s.name, b)
    shoulder = [sum(apply(world(owl, b), [0, 0, 0])[i] for b in SHOULDERS) / 2 for i in range(3)]
    crow_mid = [sum(crow.nodes[b].transform.translation[i] for b in CROW_WINGS) / 2 for i in range(3)]
    move = [crow_mid[i] - SCALE * shoulder[i] for i in range(3)]

    dst = NifFile()
    dst.initialize('SKYRIMSE', OUT, 'NiNode', 'Scene Root')
    for s in shapes:
        m = disp[s.name]
        verts = [tuple(SCALE * c + move[i] for i, c in enumerate(apply(m, v))) for v in s.verts]
        rot = m[0]
        normals = []
        for n in s.normals:
            q = [sum(rot[i][j] * n[j] for j in range(3)) for i in range(3)]
            ln = math.sqrt(sum(c * c for c in q)) or 1.0
            normals.append(tuple(c / ln for c in q))
        props = BSTriShapeBuf(); props.bufType = PynBufferTypes.BSTriShapeBufType
        o = dst.createShapeFromData('BarnOwl_' + s.name, verts, s.tris, s.uvs, normals, props=props)
        if s.colors:
            o.set_colors(s.colors)
        s.shader.properties.copyto(o.shader.properties)
        o.shader.properties.bufType = PynBufferTypes.BSLightingShaderPropertyBufType
        o.shader.name = s.shader.name
        o.save_shader_attributes()
        for i in range(9):
            t = s.shader._readtexture(owl._handle, s._handle, i + 1)
            nifly.setShaderTextureSlot(dst._handle, o._handle, i, t.encode('utf-8'))
        if s.has_alpha_property:
            o.has_alpha_property = True
            s.alpha_property.properties.copyto(o.alpha_property.properties)
            o.save_alpha_property()
        # weights: owl bones -> crow bones, a vertex's blend kept, renormalised
        per_vert = {}
        for b, pairs in s.bone_weights.items():
            nb = BONE_MAP[b]
            for v, w in pairs:
                per_vert.setdefault(v, {}).setdefault(nb, 0.0)
                per_vert[v][nb] += w
        assert len(per_vert) == len(s.verts), f'{s.name}: unweighted vertices'
        weights = {}
        for v, bw in per_vert.items():
            tot = sum(bw.values())
            for b, w in bw.items():
                weights.setdefault(b, []).append((v, w / tot))
        o.skin()
        o.set_global_to_skin(crow.shapes[0].global_to_skin)
        used = sorted(weights)
        for b in used:
            o.add_bone(b, crow.nodes[b].transform)
        for b in used:
            o.set_skin_to_bone_xform(b, s2b[b])
        for b in used:
            o.setShapeWeights(b, weights[b])
        o.set_partitions([partition], [0] * len(s.tris))
    dst.save()
    os.remove(tmp)

    # ---- read back and assert ----
    back = NifFile(OUT)
    assert [x.name for x in back.shapes] == ['BarnOwl_a', 'BarnOwl_b']
    for x, s in zip(back.shapes, shapes):
        assert len(x.verts) == len(s.verts) and len(x.tris) == len(s.tris), x.name
        assert set(x.bone_names) <= set(targets), (x.name, x.bone_names)
    xs = [v[0] for x in back.shapes for v in x.verts]; ys = [v[1] for x in back.shapes for v in x.verts]
    zs = [v[2] for x in back.shapes for v in x.verts]
    for other in ('Zenderal - Prophecy v2 (Sanctum)', 'Zenderal - Prophecy v3 (Constellation)'):   # same mesh, every build
        root = os.path.join(MODS, other)
        if os.path.isdir(root):
            dst_path = os.path.join(root, 'meshes', 'Zenderal', 'Prophecy', 'BarnOwl.nif')
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            shutil.copyfile(OUT, dst_path)
            print('   copied to', dst_path)
    print(f'{OUT}: {sum(len(x.verts) for x in back.shapes)} verts, bones {sorted(set(b for x in back.shapes for b in x.bone_names))}, '
          f'x {min(xs):.0f}..{max(xs):.0f} y {min(ys):.0f}..{max(ys):.0f} z {min(zs):.0f}..{max(zs):.0f} '
          f'(crow wing pivots at {[round(c, 1) for c in crow_mid]})')


if __name__ == '__main__':
    main()
