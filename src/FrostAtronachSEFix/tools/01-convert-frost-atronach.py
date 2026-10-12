"""Rebuild the `Zenderal - Frost Atronach SE Fix` MO2 mod from the installed `Frost Atronach SE` mod.

Why: Enderal's Ice Elementals (`_14E_IceElemental 0E11B1` and kin) are `AtronachFrostRace 0131F6`,
skin `NakedAtronachFrost 05B2E8` -> `Actors\\AtronachFrost\\Character Assets\\AtronachFrost.nif`.
`Frost Atronach SE` (Nexus 171447, v1.0.0) replaces that mesh, but despite its name every NIF it ships
is Skyrim LE format (BS stream 83, NiTriShape + NiTriShapeData) -- the game's own copy is stream 100
BSTriShape. The 1.5.97 engine draws the LE skinned shape completely black (reported 2026-10-12).
Its LE `skeleton.nif` (LE Havok ragdoll, bone names identical to vanilla) also outranks XPMSSE's.

This mod ships, without touching the original mod's files:
  * both of its meshes converted to SE through PyNifly (nifly): geometry, UVs, normals, vertex
    colours, skin binds, partitions, the shader block (bar the shader type, below) and all nine
    texture slots carried over;
    weights trimmed to SE's 4 influences per vertex and renormalised (the source has up to 6;
    450 vertices, at most 4.3% weight dropped);
  * XPMSSE's frost atronach `skeleton.nif`, copied verbatim, so the LE skeleton loses.
It must sort ABOVE `Frost Atronach SE` and XPMSSE in MO2 (modlist.txt is highest-priority-first).
The meshes are the author's, so they are generated from the user's install and never committed.

Every conversion is read back and asserted (block layout, geometry, triangles, binds, shader fields,
texture slots, weights), so a mod update fails loudly instead of shipping a broken mesh.

The shader is switched to plain lighting (type 0, MULTI_LAYER_PARALLAX cleared). The SE conversion
alone still rendered black: the author's outer diffuse is ~4% opaque (avg alpha 11, vanilla's is 113)
over a near-black inner layer (avg RGB 20/37/37), so multi-layer parallax shows almost only the inner
layer. Verified in game 2026-10-12: textured with plain lighting. --multilayer keeps the author's shader.

Usage:  python 01-convert-frost-atronach.py <pynifly io_scene_nifly dir> [<modlist root>] [--multilayer]
        (modlist root defaults to E:/Zenderal; PyNifly = github.com/BadDogSkyrim/PyNifly releases,
         V29.1.0 used, unzip io_scene_nifly.zip)
"""
import os, sys, shutil, struct
from collections import defaultdict

NO_MLP = '--multilayer' not in sys.argv
ARGS = [a for a in sys.argv[1:] if a != '--multilayer']
PYN = ARGS[0]
ROOT = ARGS[1] if len(ARGS) > 1 else 'E:/Zenderal'
sys.path.insert(0, PYN)
from pyn.pynifly import NifFile, nifly  # noqa: E402
from pyn.nifdefs import PynBufferTypes, BSTriShapeBuf  # noqa: E402

MULTI_LAYER_PARALLAX = 1 << 24  # SLSF2

SRC_MOD = os.path.join(ROOT, 'mods', 'Frost Atronach SE')
SKEL_MOD = os.path.join(ROOT, 'mods', 'XP32 Maximum Skeleton Special Extended')
OUT_MOD = os.path.join(ROOT, 'mods', 'Zenderal - Frost Atronach SE Fix')
MESHES = [  # (path in source mod, Data-relative output path)
    ('Meshes/actors/AtronachFrost/Character Assets/atronachfrost.nif',
     'meshes/actors/atronachfrost/character assets/atronachfrost.nif'),
    ('Meshes/actors/dlc01/ancientfrostatronach/ancientfrostatronach.nif',
     'meshes/actors/dlc01/ancientfrostatronach/ancientfrostatronach.nif'),
]
SKELETON = 'meshes/actors/atronachfrost/character assets/skeleton.nif'
MAX_INFLUENCES = 4
SE_BLOCKS = {'NiNode': 17, 'BSTriShape': 1, 'BSDismemberSkinInstance': 1, 'NiSkinData': 1,
             'NiSkinPartition': 1, 'BSLightingShaderProperty': 1, 'BSShaderTextureSet': 1}


def nif_header(path):
    """Return (BS stream version, {block type: count}) from a NIF header."""
    d = open(path, 'rb').read()
    i = d.index(b'\n') + 1 + 4 + 1
    uv, nb, bs = struct.unpack('<III', d[i:i + 12]); i += 12
    for _ in range(3):
        i += 1 + d[i]
    nt, = struct.unpack('<H', d[i:i + 2]); i += 2
    types = []
    for _ in range(nt):
        ln, = struct.unpack('<I', d[i:i + 4]); i += 4
        types.append(d[i:i + ln].decode()); i += ln
    counts = defaultdict(int)
    for k in struct.unpack('<%dH' % nb, d[i:i + 2 * nb]):
        counts[types[k]] += 1
    return bs, dict(counts)


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
    bs, _ = nif_header(src_path)
    assert bs == 83, f'{src_path}: expected an LE mesh (stream 83), got {bs} -- has the mod been fixed upstream?'
    src = NifFile(src_path)
    assert len(src.shapes) == 1, src_path
    s = src.shapes[0]
    assert s.blockname == 'NiTriShape' and s.shader.blockname == 'BSLightingShaderProperty', src_path
    weights, per_vert, trimmed = trimmed_weights(s)
    assert len(per_vert) == len(s.verts), f'{src_path}: unweighted vertices'

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    dst = NifFile()
    dst.initialize('SKYRIMSE', out_path, src.root.blockname, src.rootName)
    props = BSTriShapeBuf(); props.bufType = PynBufferTypes.BSTriShapeBufType
    d = dst.createShapeFromData(s.name, s.verts, s.tris, s.uvs, s.normals, props=props)
    if s.colors:
        d.set_colors(s.colors)
    d.transform = s.transform
    s.shader.properties.copyto(d.shader.properties)
    d.shader.properties.bufType = PynBufferTypes.BSLightingShaderPropertyBufType
    if NO_MLP:
        d.shader.properties.Shader_Type = 0
        d.shader.properties.Shader_Flags_2 &= ~MULTI_LAYER_PARALLAX
    d.shader.name = s.shader.name
    d.save_shader_attributes()
    textures = [s.shader._readtexture(src._handle, s._handle, i + 1) for i in range(9)]
    for i, t in enumerate(textures):
        nifly.setShaderTextureSlot(dst._handle, d._handle, i, t.encode('utf-8'))
    d.skin()
    d.set_global_to_skin(s.global_to_skin)
    for b in s.bone_names:
        d.add_bone(b, src.nodes[b].transform)
    for b in s.bone_names:
        d.set_skin_to_bone_xform(b, s.get_shape_skin_to_bone(b))
    for b, w in weights.items():
        d.setShapeWeights(b, w)
    d.set_partitions(s.partitions, s.partition_tris)
    dst.save()

    # ---- read back and assert ----
    bs, blocks = nif_header(out_path)
    assert bs == 100 and blocks == SE_BLOCKS, (out_path, bs, blocks)
    o = NifFile(out_path).shapes[0]
    assert o.blockname == 'BSTriShape'
    assert len(o.verts) == len(s.verts) and len(o.tris) == len(s.tris)

    def maxdiff(a, b):
        return max(max(abs(p - q) for p, q in zip(u, v)) for u, v in zip(a, b))
    assert maxdiff(s.verts, o.verts) < 1e-4, 'verts'
    assert maxdiff(s.uvs, o.uvs) < 1e-3, 'uvs (half precision)'
    assert maxdiff(s.normals, o.normals) < 1e-2, 'normals (byte precision)'
    if s.colors:
        assert maxdiff(s.colors, o.colors) < 1e-2, 'colours'
    canon = lambda ts: sorted(tuple(sorted(t)) for t in ts)  # noqa: E731
    assert canon(s.tris) == canon(o.tris), 'triangles'
    assert o.bone_names == s.bone_names, 'bones'

    def xf(t):
        return list(t.translation) + [x for r in t.rotation for x in r] + [t.scale]
    for b in s.bone_names:
        a, c = xf(s.get_shape_skin_to_bone(b)), xf(o.get_shape_skin_to_bone(b))
        assert max(abs(p - q) for p, q in zip(a, c)) < 1e-4, f'skin-to-bone {b}'
    assert [p.id for p in o.partitions] == [p.id for p in s.partitions], 'partitions'
    pa, pb = s.shader.properties, o.shader.properties
    diff = [f for f, _ in pa._fields_ if f not in ('bufType', 'bufSize') and not f.endswith('ID')
            and str(getattr(pa, f)) != str(getattr(pb, f))]
    # Without multi-layer parallax the type-specific inner-layer fields are not written.
    allowed = {'Shader_Type', 'bslspShaderType', 'Shader_Flags_2', 'parallaxInnerLayerThickness',
               'parallaxRefractionScale', 'parallaxInnerLayerTextureScale', 'parallaxEnvmapStrength'} if NO_MLP else set()
    assert set(diff) <= allowed, f'shader fields changed: {sorted(set(diff) - allowed)}'
    if NO_MLP:
        assert pb.Shader_Type == 0 and not pb.Shader_Flags_2 & MULTI_LAYER_PARALLAX
    ow = defaultdict(dict)
    for bone, pairs in o.bone_weights.items():
        for v, w in pairs:
            if w > 0:
                ow[v][bone] = w
    want = defaultdict(dict)
    for bone, pairs in weights.items():
        for v, w in pairs:
            want[v][bone] = w
    worst = 0
    for v in want:
        assert set(ow[v]) == set(want[v]), f'vertex {v} bone set'
        worst = max(worst, max(abs(ow[v][k] - want[v][k]) for k in want[v]))
    assert worst < 1e-3, f'weights off by {worst}'
    dropped = max((sum(w for k, w in per_vert[v].items() if k not in want[v]) for v in per_vert), default=0)
    print(f'  {os.path.basename(out_path)}: {len(s.verts)} verts, {len(s.tris)} tris, '
          f'{len(s.bone_names)} bones, {trimmed} verts trimmed to {MAX_INFLUENCES} '
          f'(max weight dropped {dropped:.3f}), shader type {pb.Shader_Type}')
    return textures


def check_textures(path, textures):
    """Read the written texture set straight from the file and compare with the source."""
    d = open(path, 'rb').read()
    for t in textures:
        if t:
            assert t.encode('latin1') in d, f'{path}: texture {t} missing'


def main():
    assert os.path.isdir(SRC_MOD), SRC_MOD
    if os.path.isdir(OUT_MOD):
        for entry in os.listdir(OUT_MOD):
            if entry.lower() == 'meshes':
                shutil.rmtree(os.path.join(OUT_MOD, entry))
    os.makedirs(OUT_MOD, exist_ok=True)
    print('Converting', SRC_MOD)
    for rel_src, rel_out in MESHES:
        out = os.path.join(OUT_MOD, rel_out)
        check_textures(out, convert(os.path.join(SRC_MOD, rel_src), out))

    skel_src = os.path.join(SKEL_MOD, SKELETON)
    bs, _ = nif_header(skel_src)
    assert bs == 100, f'{skel_src}: expected SE skeleton, got stream {bs}'
    skel_out = os.path.join(OUT_MOD, SKELETON)
    os.makedirs(os.path.dirname(skel_out), exist_ok=True)
    shutil.copyfile(skel_src, skel_out)
    print('  skeleton.nif: copied from XPMSSE')
    print('Wrote', OUT_MOD, '- sort it ABOVE Frost Atronach SE and XPMSSE, then rebuild CRDW.')


if __name__ == '__main__':
    main()
