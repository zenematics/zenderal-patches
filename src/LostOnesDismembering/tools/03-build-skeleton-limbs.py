"""Build the five skeleton limb meshes for `Zenderal - Lost Ones Dismembering`.

DF's severed-limb meshes (Official Creature Asset Pack, `draugr/male/limbs/naked/*.nif`) are rigid:
every shape is skinned to one `Root` node whose skin-to-bone transform carries the real limb bone's
bind rotation, and the vertices are the draugr body's own vertices in bind space. Mihail's ancient
skeleton (`mihailancientskeleton2.nif`, shipped by Lost Ones Revised) uses the same bind pose: every
skin-to-bone rotation equal, translations within 0.07 units [verified 2026-10-19]. So a skeleton limb is:

  DF's draugr limb nif (collision, BloodFX/Origin nodes, Root transform kept)
  + the skeleton shape's triangles whose three vertices are all dominated by the limb's bones,
    skinned rigidly to Root with the DF limb's own transforms, Mihail's shader and textures
  - DF's flesh shapes (Skin, Gore, Bone, eyes) detached from the root (child ref -> -1).

Both assets are their authors' work, so the meshes are generated from the user's own install and never
committed. Every output is read back and asserted.

Usage:  python 03-build-skeleton-limbs.py <pynifly io_scene_nifly dir> [<mods dir>]
        ($Tools.pynifly in .claude/config/tools.json; mods dir defaults to E:/Zenderal/mods)
"""
import os
import sys

PYN = sys.argv[1]
MODS = sys.argv[2] if len(sys.argv) > 2 else 'E:/Zenderal/mods'
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PYN)
sys.path.insert(0, HERE)
from pyn.pynifly import NifFile, nifly  # noqa: E402
from pyn.nifdefs import PynBufferTypes, BSTriShapeBuf  # noqa: E402
from limbmesh import attached_shapes, detach, dominant_bones  # noqa: E402

OUT_MOD = os.path.join(MODS, 'Zenderal - Lost Ones Dismembering')
OUT_DIR = os.path.join('meshes', 'DismemberingFramework', 'Zenderal', 'LostOnesSkeleton')
DF_DIR = os.path.join(MODS, 'DF - Official Creature Asset Pack', 'meshes', 'dismemberingframework',
                      'officialcreaturepack', 'draugr', 'male', 'limbs', 'naked')
SKELETON = os.path.join(MODS, 'Lost Ones Revised', 'Meshes', 'Mihail Monsters and Animals', 'Human',
                        'Ancient Skeleton', 'mihailancientskeleton2.nif')
# output name -> (DF limb file, bone-name prefixes of the limb, minimum triangles expected).
# Variant 2 is used because it is bare-handed: in 0, 3, 4 and 5 one or both hands are an armor.dds
# gauntlet shape and the skeleton shape stops at the wrist (144 forearm tris instead of 794).
LIMBS = {
    'Calf_L': ('calf_l.nif', ('NPC L Calf', 'NPC L Foot', 'NPC L Toe'), 400),
    'Calf_R': ('calf_r.nif', ('NPC R Calf', 'NPC R Foot', 'NPC R Toe'), 400),
    'Forearm_L': ('forearm_l.nif', ('NPC L Forearm', 'NPC L Hand', 'NPC L Finger'), 700),
    'Forearm_R': ('forearm_r.nif', ('NPC R Forearm', 'NPC R Hand', 'NPC R Finger'), 700),
    'Head': ('head.nif', ('NPC Head',), 1000),
}
def cut(sk, prefixes):
    dom = dominant_bones(sk)
    keep = [t for t in sk.tris if all(dom.get(v, '').startswith(prefixes) for v in t)]
    used = sorted({v for t in keep for v in t})
    remap = {v: i for i, v in enumerate(used)}
    return ([sk.verts[v] for v in used], [tuple(remap[v] for v in t) for t in keep],
            [sk.uvs[v] for v in used], [sk.normals[v] for v in used])


def build(name, df_file, prefixes, min_tris, skel_nif, sk, textures):
    src = os.path.join(DF_DIR, df_file)
    out = os.path.join(OUT_MOD, OUT_DIR, name + '.nif')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    verts, tris, uvs, normals = cut(sk, prefixes)
    assert len(tris) >= min_tris, (name, len(tris))

    n = NifFile(src)
    old = [s for s in n.shapes]
    old_names = {s.name for s in old}
    ref = [s for s in old if s.name.endswith(':Skin')][0]
    assert ref.bone_names == ['Root'], (name, ref.bone_names)
    new_name = ref.name.rsplit(':', 1)[0] + ':Skeleton'
    props = BSTriShapeBuf()
    props.bufType = PynBufferTypes.BSTriShapeBufType
    d = n.createShapeFromData(new_name, verts, tris, uvs, normals, props=props, parent=ref.parent)
    sk.shader.properties.copyto(d.shader.properties)
    d.shader.properties.bufType = PynBufferTypes.BSLightingShaderPropertyBufType
    d.shader.name = sk.shader.name
    d.save_shader_attributes()
    for i, t in enumerate(textures):
        nifly.setShaderTextureSlot(n._handle, d._handle, i, t.encode('utf-8'))
    d.skin()
    d.set_global_to_skin(ref.global_to_skin)
    d.add_bone('Root', n.nodes['Root'].transform)
    d.set_skin_to_bone_xform('Root', ref.get_shape_skin_to_bone('Root'))
    d.setShapeWeights('Root', [(i, 1.0) for i in range(len(verts))])
    d.set_partitions(ref.partitions, [0] * len(tris))
    n.filepath = out
    n.save()

    dropped = detach(out, old_names)
    assert sorted(dropped) == sorted(old_names), (name, dropped, old_names)
    left = attached_shapes(out)
    assert left == [new_name], (name, left)

    # ---- read back ----
    o = NifFile(out)
    s = [x for x in o.shapes if x.name == new_name][0]
    assert len(s.verts) == len(verts) and len(s.tris) == len(tris), name
    assert s.bone_names == ['Root'], name
    assert max(abs(a - b) for u, v in zip(verts, s.verts) for a, b in zip(u, v)) < 1e-4, name
    data = open(out, 'rb').read()
    for t in textures:
        if t:
            assert t.encode('latin1') in data, (name, t)
    assert b'bhkRigidBody' in data, name
    lo = [round(min(v[i] for v in verts), 1) for i in range(3)]
    hi = [round(max(v[i] for v in verts), 1) for i in range(3)]
    print(f'  {name}: {len(verts)} verts, {len(tris)} tris, bbox {lo}..{hi} (DF flesh {sorted(old_names)} detached)')


def main():
    skel_nif = NifFile(SKELETON)
    sk = [s for s in skel_nif.shapes if s.name == 'skeleton']
    assert len(sk) == 1, SKELETON
    sk = sk[0]
    textures = [sk.shader._readtexture(skel_nif._handle, sk._handle, i + 1) for i in range(9)]
    assert textures[0].lower().endswith('skeleton.dds'), textures[0]
    # The skeleton must share DF's draugr bind pose for its vertices to land inside DF's limbs.
    draugr = NifFile(os.path.join(DF_DIR, 'forearm_r.nif'))
    ref = [s for s in draugr.shapes if s.name.endswith(':Skin')][0]
    a = sk.get_shape_skin_to_bone('NPC R Forearm [RLar]')
    b = ref.get_shape_skin_to_bone('Root')
    rot = max(abs(x - y) for ra, rb in zip(a.rotation, b.rotation) for x, y in zip(ra, rb))
    assert rot < 1e-3, f'skeleton bind rotation differs from DF draugr forearm by {rot}'
    print('Building skeleton limbs ->', os.path.join(OUT_MOD, OUT_DIR))
    for name, (df_file, prefixes, min_tris) in LIMBS.items():
        build(name, df_file, prefixes, min_tris, skel_nif, sk, textures)
    print('Done - rebuild CRDW before testing.')


if __name__ == '__main__':
    main()
