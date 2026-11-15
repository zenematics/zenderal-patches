"""Whisper's base mesh: billyro's Stalwart Axe (one-handed) converted from Skyrim LE to SE.

Why (curator, 2026-11-15): Whisper, a unique one-handed Entropy axe, is built on billyro's Stalwart Axe (Skyrim LE
Nexus 70388, 2015; billyro gave the curator permission to use his weapons). The axe only exists as an LE upload
(NIF stream 83, NiTriShapes), and every later design step (nifse.py, the gold/silver texture recipes, ornaments) works
on SE BSTriShapes, so this converts it once.

Input: the two downloads unpacked into reference/mods/_raw/StalwartAxe/ (gitignored, never committed):
    main/  = "Stalwart Axe-70388-1.7z"              (meshes axe1h/axe2h, 2K textures, the original plugin)
    4k/    = "Stalwart Axe - 4K Textures-70388-1.7z" (axe.dds / axe_m.dds / axe_n.dds at 4K)
Output: reference/mods/_raw/StalwartAxe/se/meshes/billyro/stalwartaxe/axe1h.nif (gitignored too: the author's mesh).

Carried over through PyNifly (nifly): every shape's geometry, UVs, normals, vertex colours and transform; the
lighting shaders (fields + all nine texture slots) and the blood edge's effect shader (fields + its texture strings);
alpha properties; the root's BSXFlags and BSInvMarker; the collision object, rigid body and convex vertices shape.
Everything is read back and asserted, so an archive that is not the expected one fails loudly.

Usage:  python src/Whisper/tools/01-convert-stalwart.py
        (PyNifly's io_scene_nifly folder comes from tools.json "pynifly"; V29.1.0 used)
"""
import json, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
TOOLS = json.load(open(os.path.join(REPO, '.claude', 'config', 'tools.json'), encoding='utf-8-sig'))
sys.path.insert(0, TOOLS['pynifly'])
from pyn.pynifly import NifFile, nifly, BSXFlags, BSInvMarker, NiStringExtraData  # noqa: E402
from pyn.nifdefs import PynBufferTypes, BSTriShapeBuf  # noqa: E402

RAW = os.path.join(REPO, 'reference', 'mods', '_raw', 'StalwartAxe')
MESH = os.path.join('meshes', 'billyro', 'stalwartaxe', 'axe1h.nif')
SRC = os.path.join(RAW, 'main', MESH)
OUT = os.path.join(RAW, 'se', MESH)
EXPECTED_SHAPES = {'Scb', 'EdgeBlood01', 'EdgeBlood', '1stPersonSteelWarAxe:0'}   # holder, blood x2, the axe


def stream(path):
    d = open(path, 'rb').read()
    i = d.index(b'\n') + 1 + 4 + 1 + 8
    return struct.unpack('<I', d[i:i + 4])[0]


def copy_props(src_props):
    """A fresh buffer of the same ctypes type with the same field values."""
    p = type(src_props)()
    src_props.copyto(p)
    return p


def convert():
    assert os.path.isfile(SRC), f'{SRC} missing: unpack "Stalwart Axe-70388-1.7z" into {os.path.join(RAW, "main")}'
    assert stream(SRC) == 83, f'{SRC}: expected an LE mesh (stream 83)'
    src = NifFile(SRC)
    assert {s.name for s in src.shapes} == EXPECTED_SHAPES, sorted(s.name for s in src.shapes)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    dst = NifFile()
    dst.initialize('SKYRIMSE', OUT, src.root.blockname, src.rootName)
    dst.root.transform = src.root.transform

    # root extra data: BSXFlags (havok/collision bits), the inventory marker (item-menu rotation and zoom) and the
    # string `Prn` = `WeaponAxe`: the skeleton node the equipped axe hangs from. The first build carried only the
    # first two: the game had nowhere to attach the axe, so it was invisible equipped while the inventory preview
    # (which needs no skeleton) showed it. Every root extra data block is accounted for (asserted)
    every = list(src.root.extra_data())
    bsx = list(src.root.extra_data(blockname='BSXFlags'))
    inv = list(src.root.extra_data(blockname='BSInvMarker'))
    strs = list(src.root.extra_data(blockname='NiStringExtraData'))
    assert len(bsx) == 1 and len(inv) == 1 and len(every) == len(bsx) + len(inv) + len(strs), \
        [e.blockname for e in every]
    prn = {e.name: e.string_data for e in strs}
    assert prn.get('Prn') == 'WeaponAxe', prn
    BSXFlags.New(dst, name=bsx[0].name, flags=bsx[0].properties.integerData, parent=dst.root)
    for e in strs:
        NiStringExtraData.New(dst, name=e.name, string_value=e.string_data, parent=dst.root)
    BSInvMarker.New(dst, name=inv[0].name, rotation=inv[0].rotation, zoom=inv[0].zoom, parent=dst.root)

    plan = []
    for s in src.shapes:
        assert s.blockname == 'NiTriShape', (s.name, s.blockname)
        props = BSTriShapeBuf(); props.bufType = PynBufferTypes.BSTriShapeBufType
        d = dst.createShapeFromData(s.name, s.verts, s.tris, s.uvs, s.normals, props=props, parent=dst.root)
        if s.colors:
            d.set_colors(s.colors)
        d.transform = s.transform
        # the shape's NiAVObject flags (0x8000E; the blood edges 0x8000F, hidden until a hit shows them). PyNifly
        # writes 0 otherwise, and without the selective-update bits the game never moves the shapes with the hand:
        # the equipped axe was invisible while the inventory preview (which updates everything) showed it
        d.flags = s.flags
        effect = s.shader.properties.bufType == PynBufferTypes.BSEffectShaderPropertyBufType
        # the shape's own shader buffer, filled field by field: replacing the buffer object, or carrying the
        # source's block IDs over, wrote an effect shader the file could not be read back with (PyNifly's exporter
        # fills the buffer in place too)
        dp, sp = d.shader.properties, s.shader.properties
        for f, _ in sp._fields_:
            if not f.endswith('ID') and f != 'bufSize':
                setattr(dp, f, getattr(sp, f))
        dp.bufType = sp.bufType                                     # lighting or effect
        if effect:
            dp.bBSLightingShaderProperty = 0
        d.shader.name = s.shader.name or ''
        d.save_shader_attributes()
        textures = [] if effect else [s.shader._readtexture(src._handle, s._handle, i + 1) for i in range(9)]
        for i, t in enumerate(textures):
            nifly.setShaderTextureSlot(dst._handle, d._handle, i, t.encode('utf-8'))
        if s.has_alpha_property:
            d.has_alpha_property = True
            s.alpha_property.properties.copyto(d.alpha_property.properties)
            d.save_alpha_property()
        plan.append((s, effect, textures))

    # collision: the root's bhkCollisionObject -> bhkRigidBody -> bhkConvexVerticesShape, field for field
    sc = src.root.collision_object
    assert sc is not None and sc.blockname == 'bhkCollisionObject', sc
    sb = sc.body
    ss = sb.shape
    assert sb.blockname == 'bhkRigidBody' and ss.blockname == 'bhkConvexVerticesShape', (sb.blockname, ss.blockname)
    dc = dst.root.add_collision(None, flags=sc.properties.flags)
    db = dc.add_body(copy_props(sb.properties))
    db.add_shape(copy_props(ss.properties), vertices=[v[:3] for v in ss.vertices], normals=ss.normals)
    dst.save()

    # ---- read back and assert ----
    assert stream(OUT) == 100, OUT
    out = NifFile(OUT)
    byname = {o.name: o for o in out.shapes}
    assert set(byname) == EXPECTED_SHAPES, sorted(byname)
    data = open(OUT, 'rb').read()

    def maxdiff(a, b):
        return max(max(abs(p - q) for p, q in zip(u, v)) for u, v in zip(a, b))

    canon = lambda ts: sorted(tuple(sorted(t)) for t in ts)  # noqa: E731
    for s, effect, textures in plan:
        o = byname[s.name]
        assert o.blockname == 'BSTriShape', s.name
        assert o.flags == s.flags and o.flags & 0xE == 0xE, f'{s.name}: flags {o.flags:#x} (source {s.flags:#x})'
        assert len(o.verts) == len(s.verts) and len(o.tris) == len(s.tris), f'{s.name}: counts'
        assert maxdiff(s.verts, o.verts) < 1e-4, f'{s.name}: verts'
        assert maxdiff(s.uvs, o.uvs) < 1e-3, f'{s.name}: uvs (half precision)'
        assert maxdiff(s.normals, o.normals) < 1e-2, f'{s.name}: normals (byte precision)'
        if s.colors:
            assert maxdiff(s.colors, o.colors) < 1e-2, f'{s.name}: colours'
        assert canon(s.tris) == canon(o.tris), f'{s.name}: triangles'
        assert o.shader.properties.bufType == s.shader.properties.bufType, f'{s.name}: shader block type'
        pa, pb = s.shader.properties, o.shader.properties
        diff = [f for f, _ in pa._fields_ if f not in ('bufType', 'bufSize') and not f.endswith('ID')
                and str(getattr(pa, f)) != str(getattr(pb, f))]
        assert not diff, f'{s.name}: shader fields changed: {diff}'
        assert o.has_alpha_property == s.has_alpha_property, f'{s.name}: alpha property'
        for t in textures:
            if t:
                assert t.encode('latin1') in data, f'{s.name}: texture {t} missing'
        if effect:
            assert s.shader.properties.sourceTexture in data, f'{s.name}: effect texture missing'
        print(f'  {s.name}: {len(s.verts)} verts, {len(s.tris)} tris, '
              f'{"effect" if effect else "lighting"} shader, alpha {o.has_alpha_property}')
    oc = out.root.collision_object
    assert oc is not None and oc.body is not None and oc.body.shape is not None, 'collision lost'
    ov, sv = oc.body.shape.vertices, ss.vertices
    assert len(ov) == len(sv) and maxdiff([v[:3] for v in sv], [v[:3] for v in ov]) < 1e-4, 'collision vertices'
    assert abs(oc.body.properties.mass - sb.properties.mass) < 1e-4, 'collision mass'
    assert list(out.root.extra_data(blockname='BSXFlags'))[0].properties.integerData == bsx[0].properties.integerData
    assert len(list(out.root.extra_data(blockname='BSInvMarker'))) == 1
    assert {e.name: e.string_data for e in out.root.extra_data(blockname='NiStringExtraData')} == prn, 'Prn lost'
    print(f'  collision: {len(ov)} hull vertices, mass {oc.body.properties.mass:g}, layer '
          f'{oc.body.properties.collisionFilter_layer}; BSX {bsx[0].properties.integerData}')
    print('Wrote', OUT)


if __name__ == '__main__':
    convert()
