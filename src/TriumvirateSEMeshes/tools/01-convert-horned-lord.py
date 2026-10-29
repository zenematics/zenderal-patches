"""Rebuild the `Zenderal - Triumvirate SE Meshes` MO2 mod: Triumvirate's Horned Lord body converted LE -> SE.

Why (curator, 2026-10-28): Prophecy's Force of Nature turns the player into Triumvirate's Horned Lord race
(`TVR_Verdant_Race_ForceOfNature 000837`), whose skin wears `Triumvirate\\Verdant_Actor_ForceOfNature.nif`. That mesh
ships in Skyrim LE format (stream 83, 14 NiTriShapes). An NPC set to the race showed the form; the player, male or
female, clothed or naked, got no body at all (no shadow), while a plain race swap to a race with an SE body kept the
player visible. RaceMenu's overlays (on, player only, in this list) are the suspected player-only step that fails on
the LE shapes; the curator chose to convert the mesh rather than test further.

This mod ships, without touching Triumvirate's files, the mesh converted through PyNifly (nifly): every shape's
geometry, UVs, normals, vertex colours, skin binds, the shader block, all nine texture slots and the alpha property
carried over; weights trimmed to SE's 4 influences per vertex and renormalised; each shape one SBP_32_BODY partition
(the source has plain NiSkinInstances, no dismember partitions). The shader colour/float controllers (an animated
glow) are not carried over. Loose files beat the BSA, so the mod only needs to be enabled.
The mesh is the author's, so it is generated from the user's install and never committed.

Every shape is read back and asserted (counts, geometry, triangles, bones, skin binds, weights, shader fields,
textures), so a Triumvirate update fails loudly instead of shipping a broken mesh.

Usage:  python src/TriumvirateSEMeshes/tools/01-convert-horned-lord.py [<modlist root>]
        (PyNifly's io_scene_nifly folder comes from tools.json "pynifly"; V29.1.0 used)
"""
import json, os, struct, sys, tempfile
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
TOOLS = json.load(open(os.path.join(REPO, '.claude', 'config', 'tools.json'), encoding='utf-8-sig'))
sys.path.insert(0, TOOLS['pynifly'])
sys.path.insert(0, os.path.join(REPO, 'src', 'Prophecy', 'tools'))
from pyn.pynifly import NifFile, nifly, SkyPartition  # noqa: E402
from pyn.nifdefs import PynBufferTypes, BSTriShapeBuf  # noqa: E402
import _bsa  # noqa: E402

ROOT = sys.argv[1] if len(sys.argv) > 1 else 'E:/Zenderal'
SRC_BSA = os.path.join(ROOT, 'mods', 'Triumvirate - Mage Archetypes', 'Triumvirate - Mage Archetypes.bsa')
OUT_MOD = os.path.join(ROOT, 'mods', 'Zenderal - Triumvirate SE Meshes')
MESHES = [r'meshes\triumvirate\verdant_actor_forceofnature.nif']
MAX_INFLUENCES = 4
BODY = 32


def stream(path):
    d = open(path, 'rb').read()
    i = d.index(b'\n') + 1 + 4 + 1 + 8
    return struct.unpack('<I', d[i:i + 4])[0]


def trimmed_weights(shape):
    """Per-bone weight lists with every vertex cut to its top 4 influences, renormalised."""
    per_vert = defaultdict(dict)
    for bone, pairs in shape.bone_weights.items():
        for v, w in pairs:
            if w > 0:
                per_vert[v][bone] = w
    out = defaultdict(list)
    trimmed = 0
    for v, ws in per_vert.items():
        top = sorted(ws.items(), key=lambda kv: -kv[1])[:MAX_INFLUENCES]
        trimmed += len(ws) > MAX_INFLUENCES
        total = sum(w for _, w in top)
        for bone, w in top:
            out[bone].append((v, w / total))
    return out, per_vert, trimmed


def convert(src_path, out_path):
    assert stream(src_path) == 83, f'{src_path}: expected an LE mesh (stream 83) - has Triumvirate been fixed upstream?'
    src = NifFile(src_path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    dst = NifFile()
    dst.initialize('SKYRIMSE', out_path, src.root.blockname, src.rootName)
    plan = []
    for s in src.shapes:
        assert s.blockname == 'NiTriShape' and s.shader.blockname == 'BSLightingShaderProperty', (src_path, s.name)
        weights, per_vert, trimmed = trimmed_weights(s)
        assert len(per_vert) == len(s.verts), f'{s.name}: unweighted vertices'
        props = BSTriShapeBuf(); props.bufType = PynBufferTypes.BSTriShapeBufType
        d = dst.createShapeFromData(s.name, s.verts, s.tris, s.uvs, s.normals, props=props)
        if s.colors:
            d.set_colors(s.colors)
        d.transform = s.transform
        s.shader.properties.copyto(d.shader.properties)
        d.shader.properties.bufType = PynBufferTypes.BSLightingShaderPropertyBufType
        d.shader.name = s.shader.name
        d.save_shader_attributes()
        textures = [s.shader._readtexture(src._handle, s._handle, i + 1) for i in range(9)]
        for i, t in enumerate(textures):
            nifly.setShaderTextureSlot(dst._handle, d._handle, i, t.encode('utf-8'))
        if s.has_alpha_property:
            d.has_alpha_property = True
            s.alpha_property.properties.copyto(d.alpha_property.properties)
            d.save_alpha_property()
        d.skin()
        d.set_global_to_skin(s.global_to_skin)
        for b in s.bone_names:
            d.add_bone(b, src.nodes[b].transform)
        for b in s.bone_names:
            d.set_skin_to_bone_xform(b, s.get_shape_skin_to_bone(b))
        for b, w in weights.items():
            d.setShapeWeights(b, w)
        d.set_partitions([SkyPartition(BODY, name='SBP_32_BODY')], [0] * len(s.tris))
        plan.append((s, weights, per_vert, trimmed, textures))
    dst.save()

    # ---- read back and assert ----
    assert stream(out_path) == 100, out_path
    out = NifFile(out_path)
    assert len(out.shapes) == len(src.shapes), 'shape count'
    byname = {o.name: o for o in out.shapes}
    data = open(out_path, 'rb').read()

    def maxdiff(a, b):
        return max(max(abs(p - q) for p, q in zip(u, v)) for u, v in zip(a, b))

    def xf(t):
        return list(t.translation) + [x for r in t.rotation for x in r] + [t.scale]

    canon = lambda ts: sorted(tuple(sorted(t)) for t in ts)  # noqa: E731
    for s, weights, per_vert, trimmed, textures in plan:
        o = byname[s.name]
        assert o.blockname == 'BSTriShape', s.name
        assert len(o.verts) == len(s.verts) and len(o.tris) == len(s.tris), f'{s.name}: counts'
        assert maxdiff(s.verts, o.verts) < 1e-4, f'{s.name}: verts'
        assert maxdiff(s.uvs, o.uvs) < 1e-3, f'{s.name}: uvs (half precision)'
        assert maxdiff(s.normals, o.normals) < 1e-2, f'{s.name}: normals (byte precision)'
        if s.colors:
            assert maxdiff(s.colors, o.colors) < 1e-2, f'{s.name}: colours'
        assert canon(s.tris) == canon(o.tris), f'{s.name}: triangles'
        assert o.bone_names == s.bone_names, f'{s.name}: bones'
        for b in s.bone_names:
            a, c = xf(s.get_shape_skin_to_bone(b)), xf(o.get_shape_skin_to_bone(b))
            assert max(abs(p - q) for p, q in zip(a, c)) < 1e-4, f'{s.name}: skin-to-bone {b}'
        assert [p.id for p in o.partitions] == [BODY], f'{s.name}: partitions {[p.id for p in o.partitions]}'
        pa, pb = s.shader.properties, o.shader.properties
        diff = [f for f, _ in pa._fields_ if f not in ('bufType', 'bufSize') and not f.endswith('ID')
                and str(getattr(pa, f)) != str(getattr(pb, f))]
        assert not diff, f'{s.name}: shader fields changed: {diff}'
        assert o.has_alpha_property == s.has_alpha_property, f'{s.name}: alpha property'
        for t in textures:
            if t:
                assert t.encode('latin1') in data, f'{s.name}: texture {t} missing'
        ow = defaultdict(dict)
        for bone, pairs in o.bone_weights.items():
            for v, w in pairs:
                if w > 0:
                    ow[v][bone] = w
        worst = 0
        for bone, pairs in weights.items():
            for v, w in pairs:
                worst = max(worst, abs(ow[v].get(bone, 0) - w))
        assert worst < 1e-3, f'{s.name}: weights off by {worst}'
        dropped = max((sum(w for k, w in per_vert[v].items() if k not in ow[v]) for v in per_vert), default=0)
        print(f'  {s.name}: {len(s.verts)} verts, {len(s.tris)} tris, {len(s.bone_names)} bones, '
              f'{trimmed} verts trimmed (max weight dropped {dropped:.3f}), shader type {pb.Shader_Type}, '
              f'alpha {o.has_alpha_property}')


def main():
    d, listing = _bsa.listing(SRC_BSA)
    os.makedirs(OUT_MOD, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for key in MESHES:
            src = os.path.join(tmp, os.path.basename(key))
            open(src, 'wb').write(_bsa.read(d, listing[key]))
            out = os.path.join(OUT_MOD, key)
            print(key)
            convert(src, out)
    print('Wrote', OUT_MOD, '- enable it in MO2 (loose files beat Triumvirate\'s BSA).')


if __name__ == '__main__':
    main()
