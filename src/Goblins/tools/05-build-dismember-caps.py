"""Goblin-skinned stump caps for `Zenderal - Goblins Dismembering`. Run after 04.

DF's five naked male Falmer body-cap ARMAs (00083F-000843:DF - Official Creature Pack.esp, race-locked to
FalmerRace) all render one `Dismembered_Addons.nif`: per limb a Bone, a Gore and a Skin shape
(`AA:<Limb>:Skin`, the flesh ring round the stump, textured with vanilla `falmerm.dds`). On a goblin the
ring showed as pale Falmer skin. The goblin rides the Falmer skeleton and its body is bound in the same
skin space (global-to-skin identity on both), with the rings 1-6 units off the goblin surface.

The goblin bodies come in two variants (the cap variants 06 tags each skin with): `goblin.dds`, and the
slightly reshaped `goblinwitch.dds` body of Falmer03/05/06. Per variant this copies the cap nif and
replaces each Skin ring with the same geometry and skinning carrying the goblin body's shader and
textures. UVs come from the goblin body. The goblin's UV seams run through the limbs, so per-vertex
transfer smeared 10-30% of the ring triangles across islands. The ring is therefore unwelded (each
triangle gets its own corners, same positions/normals/weights): a triangle takes the UV island of the
goblin vertex nearest its centroid, and each corner takes the nearest goblin vertex in that island.
Bone and Gore shapes, partitions (DF hides by them) and alpha stay DF's.

DF's own Falmer caps (the Arps') are left alone. Instead `dismember-caps.json`
(committed) plans, per variant and limb, a copy of DF's ARMO (00083A-00083E) and ARMA (00083F-000843)
with the new model, on FormIDs after 04's limbs. 06 writes those records (race -> ZEN_GoblinRace) and
the actor-addon templates (`Zenderal - <variant> - Actor addons data - <part>`, DF's blood art kept)
that 04's plan names.

Usage:  python 05-build-dismember-caps.py <pynifly io_scene_nifly dir> [<modlist root>]
"""
import json
import os
import struct
import sys

PYN = sys.argv[1]
ROOT = sys.argv[2] if len(sys.argv) > 2 else 'E:/Zenderal'
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PYN)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', '..', 'LostOnesDismembering', 'tools'))   # limbmesh.py
import numpy as np  # noqa: E402
from pyn.pynifly import NifFile, nifly  # noqa: E402
from pyn.nifdefs import PynBufferTypes, BSTriShapeBuf  # noqa: E402
from limbmesh import NODE_TYPES, Nif, _child_slots, attached_shapes  # noqa: E402

BS = chr(92)
MODS = os.path.join(ROOT, 'mods')
CAPS = os.path.join(MODS, 'DF - Official Creature Asset Pack', 'meshes', 'dismemberingframework',
                    'officialcreaturepack', 'falmer', 'male', 'armoraddons', 'naked', 'dismembered_addons.nif')
GOBLINS = os.path.join(MODS, 'Goblins', 'meshes', 'actors', 'falmer', 'character assets')
BODY = 'Goblin_body'
OUT_REL = BS.join(['DismemberingFramework', 'Zenderal', 'Goblins', 'Dismembered_Addons_{}.nif'])
OUT_MESHES = os.path.join(MODS, 'Zenderal - Goblins Dismembering', 'meshes')
LIMB_PLAN = os.path.join(HERE, 'dismember-limbs.json')
PLAN = os.path.join(HERE, 'dismember-caps.json')
VARIANTS = {'goblin.dds': 'Goblin', 'goblinwitch.dds': 'GoblinWitch'}       # = 06's CAP_VARIANTS
DF_ADDONS = os.path.join(MODS, 'DF - Official Creature Asset Pack', 'SKSE', 'DismemberingFramework',
                         'OfficialCreaturePack_Falmer_ActorAddonsData_TEMPLATES.json')
# template part -> (cap ring, DF ARMO, DF ARMA)
PARTS = {'L Calf': ('AA:LCalf:Skin', 0x83A, 0x83F), 'R Calf': ('AA:RCalf:Skin', 0x83B, 0x840),
         'L Forearm': ('AA:LForearm:Skin', 0x83C, 0x841), 'R Forearm': ('AA:RForearm:Skin', 0x83D, 0x842),
         'Head': ('AA:Head:Skin', 0x83E, 0x843)}
K = 24                 # goblin vertices considered per corner
ISLAND = 0.05          # a candidate within this UV distance of the triangle's reference is in its island
MAX_SPAN = 0.06        # asserted: the widest UV extent of any rebuilt ring triangle


def goblin_bodies():
    """{variant: (nif, body shape)}; asserts every Goblins body nif of a variant carries the same body."""
    out = {}
    for f in sorted(os.listdir(GOBLINS)):
        if not f.lower().startswith('falmer') or not f.lower().endswith('.nif'):
            continue
        nf = NifFile(os.path.join(GOBLINS, f))
        b = [s for s in nf.shapes if s.name == BODY]
        assert len(b) == 1, f
        var = VARIANTS[b[0].textures['Diffuse'].split(BS)[-1].lower()]
        if var not in out:
            out[var] = (nf, b[0])
        else:
            ref = out[var][1]
            assert np.allclose(ref.verts, b[0].verts) and np.allclose(ref.uvs, b[0].uvs), f
    assert sorted(out) == sorted(VARIANTS.values()), sorted(out)
    return out


def ring_uvs(shape, gv, guv):
    """Unwelded corners (old vertex index per corner) and their UVs."""
    v = np.asarray(shape.verts)
    corners, uvs = [], []
    for t in shape.tris:
        c = v[list(t)].mean(0)
        ref = guv[np.argmin(((gv - c) ** 2).sum(1))]
        for i in t:
            d = ((gv - v[i]) ** 2).sum(1)
            cand = np.argsort(d)[:K]
            same = [j for j in cand if np.abs(guv[j] - ref).max() < ISLAND]
            corners.append(i)
            uvs.append(tuple(guv[same[0]]) if same else tuple(ref))
    return corners, uvs


def rebuild(n, old, body, body_nif, corners, uvs):
    props = BSTriShapeBuf()
    props.bufType = PynBufferTypes.BSTriShapeBufType
    verts = [old.verts[i] for i in corners]
    normals = [old.normals[i] for i in corners]
    tris = [(3 * k, 3 * k + 1, 3 * k + 2) for k in range(len(old.tris))]
    d = n.createShapeFromData(old.name, verts, tris, uvs, normals, props=props, parent=old.parent)
    body.shader.properties.copyto(d.shader.properties)
    d.shader.properties.bufType = PynBufferTypes.BSLightingShaderPropertyBufType
    d.shader.name = body.shader.name
    d.save_shader_attributes()
    for k in range(9):
        t = body.shader._readtexture(body_nif._handle, body._handle, k + 1)
        nifly.setShaderTextureSlot(n._handle, d._handle, k, t.encode('utf-8'))
    if old.has_alpha_property:
        d.has_alpha_property = True
        d.alpha_property.properties.flags = old.alpha_property.properties.flags
        d.alpha_property.properties.threshold = old.alpha_property.properties.threshold
        d.save_alpha_property()
    d.skin()
    d.set_global_to_skin(old.global_to_skin)
    at = {}
    for k, i in enumerate(corners):
        at.setdefault(i, []).append(k)
    # All bones first, then every skin-to-bone, then the weights: add_bone resets the skin-to-bone of the
    # bones added before it, so set-per-bone in one loop left all but the last at identity (the 3-bone head
    # ring's Spine2/L Clavicle -> a spike from the neck on every decapitated goblin, seen in game 2026-10-22).
    for bone in old.bone_weights:
        d.add_bone(bone, n.nodes[bone].transform)
    for bone in old.bone_weights:
        d.set_skin_to_bone_xform(bone, old.get_shape_skin_to_bone(bone))
    for bone, pairs in old.bone_weights.items():
        d.setShapeWeights(bone, [(k, w) for i, w in pairs for k in at.get(i, [])])
    d.set_partitions(old.partitions, [old.partition_tris[0]] * len(tris))
    return len(verts), len(tris)


def detach_first(path, names):
    """Detach the FIRST (lowest block) shape of each name: DF's original rings; the rebuilt ones keep the name."""
    nf = Nif(path)
    first = {}
    for sh in nf.shapes():
        if sh['name'] in names and sh['name'] not in first:
            first[sh['name']] = sh['block']
    drop = set(first.values())
    hit = 0
    for typ, p, _ in nf.blocks:
        if typ not in NODE_TYPES:
            continue
        for at, ref in _child_slots(nf, p):
            if ref in drop:
                struct.pack_into('<i', nf.data, at, -1)
                hit += 1
    assert hit == len(names), (hit, names)
    with open(path, 'wb') as fh:
        fh.write(nf.data)


def build(variant, body_nif, body):
    gv, guv = np.asarray(body.verts), np.asarray(body.uvs)
    n = NifFile(CAPS)
    rings = [s for s in n.shapes if s.name.endswith(':Skin')]
    assert sorted(s.name for s in rings) == sorted(p[0] for p in PARTS.values()), [s.name for s in rings]
    assert np.allclose(body.global_to_skin.translation[:], 0, atol=1e-3)
    built = {}
    for old in rings:
        assert np.allclose(old.global_to_skin.translation[:], 0, atol=1e-3), old.name
        assert len(set(old.partition_tris)) == 1, old.name
        corners, uvs = ring_uvs(old, gv, guv)
        span = max(np.ptp(np.asarray(uvs[3 * k:3 * k + 3]), axis=0).max() for k in range(len(old.tris)))
        assert span < MAX_SPAN, (variant, old.name, span)
        built[old.name] = rebuild(n, old, body, body_nif, corners, uvs) + (span,)
    out = os.path.join(OUT_MESHES, *OUT_REL.format(variant).split(BS))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    n.filepath = out
    n.save()
    detach_first(out, set(built))

    o = NifFile(out)
    shown = attached_shapes(out)
    assert len(shown) == len(NifFile(CAPS).shapes), shown
    want = body.textures['Diffuse'].lower()
    for name, (nv, nt, span) in built.items():
        s = [x for x in o.shapes if x.name == name][-1]
        assert len(s.verts) == nv and len(s.tris) == nt, name
        assert s.textures['Diffuse'].lower() == want, (name, s.textures)
        src = [x for x in NifFile(CAPS).shapes if x.name == name][0]
        assert sorted(s.bone_names) == sorted(src.bone_names), (name, s.bone_names, src.bone_names)
        for bone in src.bone_names:                 # every bind transform as DF's (read back from disk)
            a, b = s.get_shape_skin_to_bone(bone), src.get_shape_skin_to_bone(bone)
            assert np.allclose(list(a.translation), list(b.translation), atol=1e-3) and \
                np.allclose([list(r) for r in a.rotation], [list(r) for r in b.rotation], atol=1e-4) and \
                abs(a.scale - b.scale) < 1e-4, (variant, name, bone, list(a.translation), list(b.translation))
        print(f'  {name}: {nt} tris, {nv} corners, max UV span {span:.3f}')
    print(f'{variant}: {want} -> {out}')


def main():
    limbs = json.load(open(LIMB_PLAN, encoding='utf-8'))
    used = {e['cap'] for e in limbs if e['cap']}
    addons = json.load(open(DF_ADDONS, encoding='utf-8'))
    fid = max(int(e['fid'], 16) for e in limbs) + 1
    plan = []
    for variant, (body_nif, body) in sorted(goblin_bodies().items()):
        assert variant in used, variant
        build(variant, body_nif, body)
        for part, (_, armo, arma) in PARTS.items():
            df = addons[f'Falmer - Male - Actor addons data - {part}']
            assert df['ActorArmorAddon'] == f'DF - Official Creature Pack.esp:0x{armo:X}', (part, df)
            plan.append(dict(variant=variant, part=part, template=f'Zenderal - {variant} - Actor addons data - {part}',
                             armo=f'{fid:06X}', arma=f'{fid + 1:06X}', df_armo=f'{armo:06X}', df_arma=f'{arma:06X}',
                             edid=f'ZEN_{variant}_{part.replace(" ", "")}', art=df['ActorArtObject'],
                             mesh=OUT_REL.format(variant)))
            fid += 2
    assert fid <= 0xFFF, 'ESL range exhausted'
    with open(PLAN, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(plan, fh, indent=2)
        fh.write('\n')
    print(f'{len(plan)} cap ARMO/ARMA pairs {plan[0]["armo"]}-{plan[-1]["arma"]} -> {PLAN}')


if __name__ == '__main__':
    main()
