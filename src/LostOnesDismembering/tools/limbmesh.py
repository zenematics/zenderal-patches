"""Shared helpers for the DF limb mesh generators (03-build-skeleton-limbs.py, 04-build-minotaur-limbs.py).

DF's limb convention [verified 2026-10-19 against the draugr forearm/calf]: every limb shape is skinned
rigidly to one `Root` node, and Root is the template's RefNode bone frame shifted by its `Translation`:
for a body vertex v, skin_to_bone(Root) * v == skin_to_bone(RefNode bone) * v + Translation. The body's
global-to-skin transform is NOT applied (pynifly's vertices are already in skin space).

Callers put PyNifly's io_scene_nifly dir on sys.path before importing this module.
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'HorseCloakFluffFix', 'tools'))
from nif import Nif, Reader  # noqa: E402

import numpy as np  # noqa: E402
from pyn.pynifly import NifFile, nifly  # noqa: E402
from pyn.nifdefs import PynBufferTypes, BSTriShapeBuf  # noqa: E402
from pyn.structs import TransformBuf  # noqa: E402

NODE_TYPES = ('NiNode', 'BSFadeNode')


def dominant_bones(shape):
    best = {}
    for bone, pairs in shape.bone_weights.items():
        for v, w in pairs:
            if v not in best or w > best[v][1]:
                best[v] = (bone, w)
    return {v: b for v, (b, _) in best.items()}


def _child_slots(n, p):
    r = Reader(n.data, p)
    r.skip(4)
    r.skip(4 * r.take('I'))
    r.skip(4 + 4 + 12 + 36 + 4 + 4)
    count = r.take('I')
    return [(r.p + 4 * k, struct.unpack_from('<i', n.data, r.p + 4 * k)[0]) for k in range(count)]


def detach(path, names):
    """Set every node child ref pointing at a shape named in `names` to -1; returns the names detached."""
    n = Nif(path)
    by_block = {sh['block']: sh['name'] for sh in n.shapes()}
    dropped = []
    for typ, p, _ in n.blocks:
        if typ not in NODE_TYPES:
            continue
        for at, ref in _child_slots(n, p):
            if by_block.get(ref) in names:
                struct.pack_into('<i', n.data, at, -1)
                dropped.append(by_block[ref])
    with open(path, 'wb') as fh:
        fh.write(n.data)
    return dropped


def attached_shapes(path):
    n = Nif(path)
    by_block = {sh['block']: sh['name'] for sh in n.shapes()}
    refs = set()
    for typ, p, _ in n.blocks:
        if typ in NODE_TYPES:
            refs |= {ref for _, ref in _child_slots(n, p)}
    return sorted(by_block[b] for b in by_block if b in refs)


def descendants(skel_path, bone):
    n = NifFile(skel_path)
    assert bone in n.nodes, (skel_path, bone)
    out = set()
    for name, node in n.nodes.items():
        p = node
        while p is not None:
            if p.name == bone:
                out.add(name)
                break
            p = p.parent
    return out


def matrix(t):
    return np.array([list(r) for r in t.rotation]), np.array(list(t.translation)), t.scale


def skin_to_ref(shape, ref_bone, bone_set, all_shapes):
    """(A, T, R) taking `shape`'s skin space into `ref_bone` space: x_ref = A x + T, normals by R.
    A carries the skin-to-bone scale (helmet_2's horn shape `fesf` is bound at scale 30.2).

    Directly from the shape's own bind when it is rigged to `ref_bone`. Otherwise (e.g. a body `torso`
    rigged to the hand/twist bones but not the forearm) through a limb bone b it does carry, using the
    b -> ref relation of another shape of the same outfit rigged to both (x_ref = Rr Rb^T (x_b - Tb) + Tr).
    The race skeleton.nif is not used: the meshes' bind pose differs from it by up to 1.6 units."""
    if ref_bone in shape.bone_names:
        R, T, s = matrix(shape.get_shape_skin_to_bone(ref_bone))
        return s * R, T, R
    for b in shape.bone_names:
        if b not in bone_set:
            continue
        for other in all_shapes:
            if ref_bone in other.bone_names and b in other.bone_names:
                Rr, Tr, sr = matrix(other.get_shape_skin_to_bone(ref_bone))
                Rb, Tb, sb = matrix(other.get_shape_skin_to_bone(b))
                Rs, Ts, ss = matrix(shape.get_shape_skin_to_bone(b))
                Arel = (sr / sb) * (Rr @ Rb.T)          # b space -> ref space
                return Arel @ (ss * Rs), Arel @ (Ts - Tb) + Tr, Rr @ Rb.T @ Rs
    raise SystemExit(f'{shape.name}: no bind path to {ref_bone}')


def cut_shape(nif, shape, ref_bone, bone_set, all_shapes):
    """The shape's triangles inside `bone_set`, as bone-space geometry of `ref_bone`."""
    dom = dominant_bones(shape)
    keep = [t for t in shape.tris if all(dom.get(v) in bone_set for v in t)]
    if not keep:
        return None
    used = sorted({v for t in keep for v in t})
    remap = {v: i for i, v in enumerate(used)}
    A, T, R = skin_to_ref(shape, ref_bone, bone_set, all_shapes)
    v = np.array([shape.verts[i] for i in used]) @ A.T + T
    nrm = np.array([shape.normals[i] for i in used]) @ R.T
    return dict(name=shape.name, verts=[tuple(x) for x in v], normals=[tuple(x) for x in nrm],
                uvs=[shape.uvs[i] for i in used], tris=[tuple(remap[i] for i in t) for t in keep],
                textures=[shape.shader._readtexture(nif._handle, shape._handle, i + 1) for i in range(9)],
                shape=shape)


HAVOK_SCALE = 69.99125      # game units per Havok unit (SSE); DF's wolf leg hull * this == its mesh


def obb_hull(points):
    """Oriented bounding box (PCA axes) of `points` (game units): 8 vertices and 6 planes in Havok units,
    planes as (nx, ny, nz, w) with n . v + w <= 0 inside (the convention DF's own wolf leg hull uses)."""
    P = np.asarray(points, dtype=float)
    c = P.mean(0)
    _, vecs = np.linalg.eigh(np.cov((P - c).T))
    proj = (P - c) @ vecs
    lo, hi = proj.min(0), proj.max(0)
    corners = [c + vecs @ np.array([(hi if (i >> k) & 1 else lo)[k] for k in range(3)]) for i in range(8)]
    planes = []
    for k in range(3):
        for sign in (1.0, -1.0):
            nrm = sign * vecs[:, k]
            w = -max(float(nrm @ q) for q in corners)
            planes.append((*nrm, w / HAVOK_SCALE))
    return [tuple(q / HAVOK_SCALE) for q in corners], planes


def rewrite_hull(path, vertices, planes):
    """Replace the nif's single bhkConvexVerticesShape vertex/plane arrays in place (Havok units).

    Binary, because PyNifly's setCollConvexVerts APPENDS to an existing shape's arrays (the wolf hull's
    16 verts + 12 planes stayed). Block layout (SSE): material u32, radius f32, two
    bhkWorldObjCInfoProperty (12 bytes each), u32 count + Vector4 vertices, u32 count + Vector4 planes.
    The header's block-size entry is updated to the new length."""
    n = Nif(path)
    hits = [i for i, (t, _, _) in enumerate(n.blocks) if t == 'bhkConvexVerticesShape']
    assert len(hits) == 1, (path, hits)
    i = hits[0]
    _, pos, size = n.blocks[i]
    old = bytes(n.data[pos:pos + size])
    nv = struct.unpack_from('<I', old, 32)[0]
    nn = struct.unpack_from('<I', old, 36 + 16 * nv)[0]
    assert 40 + 16 * (nv + nn) == size, (path, nv, nn, size)
    new = old[:32] + struct.pack('<I', len(vertices)) + b''.join(struct.pack('<4f', v[0], v[1], v[2], 0.0) for v in vertices)
    new += struct.pack('<I', len(planes)) + b''.join(struct.pack('<4f', *q) for q in planes)
    # offset of the block-size table: header up to the per-block type indices (as Nif() parses it)
    r = Reader(n.data, n.data.index(b'\n') + 1)
    r.skip(4 + 1 + 4)
    nblocks = r.take('I')
    r.skip(4)
    for _ in range(3):
        r.skip(r.take('B'))
    for _ in range(r.take('H')):
        r.skip(r.take('I'))
    sizes_at = r.p + 2 * nblocks
    assert struct.unpack_from('<I', n.data, sizes_at + 4 * i)[0] == size, path
    data = bytes(n.data[:pos]) + new + bytes(n.data[pos + size:])
    data = bytearray(data)
    struct.pack_into('<I', data, sizes_at + 4 * i, len(new))
    with open(path, 'wb') as fh:
        fh.write(data)


def build_nif(container, pieces, translation, out, fit_hull=False):
    """fit_hull: replace the container's collision hull with an OBB of the new geometry (in Root space,
    which is the collision body's space in DF's limb nifs). Needed when the limb does not run along the
    container limb's axis: the borrowed wolf hull sat across a spider leg and launched the corpse."""
    n = NifFile(container)
    old = {s.name for s in n.shapes}
    ref = n.shapes[0]
    assert ref.bone_names == ['Root'], (container, ref.bone_names)
    s2b = TransformBuf()
    s2b.translation[0], s2b.translation[1], s2b.translation[2] = translation
    for i, pc in enumerate(pieces):
        props = BSTriShapeBuf()
        props.bufType = PynBufferTypes.BSTriShapeBufType
        d = n.createShapeFromData(f'Limb:{i}:{pc["name"]}', pc['verts'], pc['tris'], pc['uvs'], pc['normals'],
                                  props=props, parent=ref.parent)
        src = pc['shape']
        src.shader.properties.copyto(d.shader.properties)
        d.shader.properties.bufType = PynBufferTypes.BSLightingShaderPropertyBufType
        d.shader.name = src.shader.name
        d.save_shader_attributes()
        for k, t in enumerate(pc['textures']):
            nifly.setShaderTextureSlot(n._handle, d._handle, k, t.encode('utf-8'))
        if src.has_alpha_property:
            d.has_alpha_property = True
            d.alpha_property.properties.flags = src.alpha_property.properties.flags
            d.alpha_property.properties.threshold = src.alpha_property.properties.threshold
            d.save_alpha_property()
        d.skin()
        d.set_global_to_skin(TransformBuf())
        d.add_bone('Root', n.nodes['Root'].transform)
        d.set_skin_to_bone_xform('Root', s2b)
        d.setShapeWeights('Root', [(k, 1.0) for k in range(len(pc['verts']))])
        d.set_partitions(ref.partitions, [0] * len(pc['tris']))
    n.filepath = out
    n.save()
    dropped = detach(out, old)
    assert sorted(dropped) == sorted(old), (out, dropped, old)
    if fit_hull:
        tr = np.array(translation)
        rewrite_hull(out, *obb_hull(np.vstack([np.asarray(pc['verts']) + tr for pc in pieces])))
    left = attached_shapes(out)
    assert len(left) == len(pieces), (out, left)
    o = NifFile(out)
    for i, pc in enumerate(pieces):
        s = [x for x in o.shapes if x.name == f'Limb:{i}:{pc["name"]}'][0]
        assert len(s.verts) == len(pc['verts']) and len(s.tris) == len(pc['tris']), out
        assert max(abs(a - b) for u, w in zip(pc['verts'], s.verts) for a, b in zip(u, w)) < 1e-3, out
    data = open(out, 'rb').read()
    assert b'bhkRigidBody' in data, out
