"""Argent Verdict's mesh and textures: Pretty Enderal Armory's Aeterna Warhammer (Caenraes' Noble Armory model, open
with credit) in polished silver, its head enlarged and its centre block a clenched hand gripping the stake that
carries the face and spike, its forearm flowing into the handle under a bracelet of thorns, with a dark navy leather
grip (curator 2026-11-13: "All silver, white grip", then "change the leather wrapping handle to a dark navy, enlarge
the head of the hammer by 15% / change the middle section of the head to a clenched fist, resembling holding the
hammer and spike like a stake", then "make the hand look more human like", then "reduce the size of the hand by at
least 30%"; 2026-11-14: "lose the base with the roses and have the hand mold into the handle", "make the hand human
again", "add a bracelet of thorns to help blend the wrist to handle").

The mesh (our own copy: the head is reshaped, so Pretty's file can no longer be shared), built from Pretty's:

- the head's centre block (the head piece's triangles between CUT, asserted against the block's measured extent)
  and the knob on top of it are taken off; the face and spike (the rest of the head piece) are scaled HEAD_SCALE
  about the block's centre, and so are the two blood-overlay copies of the head (Edgeblood, Edgeblood01), cut the
  same way;
- fist.py's parts (the hand at fist.HAND_SCALE with its forearm into the shaft, the stake it holds running out to a
  socket round each neck's cut end, the bracelet of thorns on the join; roses.py's vines up the forearm) share one
  UV atlas (fist_tex.py) and are added as two shapes, ZP_ArgentFist and ZP_ArgentRoses (one BSTriShape holds at
  most 65,535 triangles), each with its own copy of the hammer's shader (never shared: two shapes on one lighting
  shader froze the game, Clockwork Thunder) and tangents from the atlas in the hammer's own convention;
- the shaft's top (which ran up into the block) is pulled down and in, inside the forearm (SHAFT_INTO_ARM above its
  end, no higher than the arm still holds it), so it cannot show through;
- the hammer shape's texture set is ours (below), so the record needs no texture swap.

The textures, from Pretty's own with Sting and Rise's pipeline (src/StingAndRise/tools/01-build-assets.py, imported):

- gold_set with a SILVER recipe: every metal texel (Noble Armory's own env mask) onto a neutral silver ramp by its
  brightness (the head's engravings stay as relief in brightness), a Complex Material mask (reflect / gloss /
  metal, alpha 0; its 1x1 mip checked against Bottled Shaders' own test), the normal map's highlight mask raised
  on the metal;
- the grip's leather UV islands (the four wrap strips; metal and dropped islands untouched) recoloured dark navy;
- the fist's painted set (fist_tex.py: skin relief fading to metal down the forearm, knuckle wrinkles, nails, the
  bones through the back of the hand, the bracelet, the sockets' cut lines; on the same silver ramp);
- a silver cubemap graded from Bethesda's chrome studio cubemap, for where Complex Material is off.

The head is the spiked gauntlet (gauntlet.py; curator 2026-11-14: "save what we have but make a variant that is a
spiked Gauntlet", then 2026-11-15: "this version we've made is THE Argent Verdict", "remove the other versions"): the
hand above (fist.py + roses.py) was the first head and stays only as the gauntlet's source, its pose and its painter
(fist.py, fist_tex.py, roses.py); its own mesh and painted set (ArgentFist_*) are gone. The gauntlet's parts are
one shape, ZP_ArgentGauntlet.

Outputs, into <mods>/<target> (default Zenderal - Patch Collection): meshes/Zenderal/ArgentVerdict/ArgentVerdict.nif
(the gauntlet; ArgentVerdictGauntlet.nif until 2026-11-15), textures/Zenderal/ArgentVerdict/ArgentVerdict_d, _n, _m,
_e.dds (the hammer) and ArgentGauntlet_d, _n, _m.dds (the gauntlet).

The mesh carries the four knuckle motes (motes.py; their textures are tools/03's).

Usage:  python 01-build-assets.py [--out-root <dir>]
"""
import argparse
import importlib.util
import os
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SR = os.path.normpath(os.path.join(HERE, '..', '..', 'StingAndRise', 'tools'))
sys.path.insert(0, SR)
_spec = importlib.util.spec_from_file_location('sr_assets', os.path.join(SR, '01-build-assets.py'))
sr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sr)
nifse = sr.nifse
sys.path.insert(0, HERE)
import fist  # noqa: E402
import fist_tex  # noqa: E402
import gauntlet  # noqa: E402
import motes  # noqa: E402

MESH = 'meshes/weapons/elven/elvenwarhammer.nif'      # Pretty's Aeterna Warhammer (= its 1st-person mesh)
SHAPE = 'Noble'                                       # Noble_Warhammer_MP
TEX = 'textures/weapons/noble armory/warhammer/'
OUT_D = 'textures/Zenderal/ArgentVerdict/ArgentVerdict_d.dds'
OUT_N = 'textures/Zenderal/ArgentVerdict/ArgentVerdict_n.dds'
OUT_M = 'textures/Zenderal/ArgentVerdict/ArgentVerdict_m.dds'
OUT_E = 'textures/Zenderal/ArgentVerdict/ArgentVerdict_e.dds'
# the head: the spiked gauntlet, its own painted texture set for the generated parts (the hammer's silver set beside
# it); the hand head ('hand': ArgentVerdict.nif, ArgentFist_*, shapes ZP_ArgentFist + ZP_ArgentRoses) retired 2026-11-15
HEAD = dict(mesh='meshes/Zenderal/ArgentVerdict/ArgentVerdict.nif', tex='textures/Zenderal/ArgentVerdict/ArgentGauntlet',
            shapes=(('fist', 'ZP_ArgentGauntlet'),))
BLOOD = ('Edgeblood', 'Edgeblood01')                 # the head's two blood-overlay copies
BLOCK = ((-3.75, 37.45, -2.20), (4.25, 41.46, 2.07))  # the head's centre block (measured; asserted within 0.05)
CUT = (-4.2, 4.6)             # head triangles with their centre's x in here are the block (and its neck stubs)
HEAD_SCALE = 1.15             # curator: "enlarge the head of the hammer by 15%"
KNOB_TRIS = 384               # the knob on top of the block: its own piece, everything above y 40.5
SHAFT_INTO_ARM = 1.0          # the shaft's top is pulled down to this far above the forearm's end (inside it; no
#                               higher than the arm still holds the whole shaft: it leans back as it rises)
SHAFT_RADIUS_Y = (-14.0, -8.0)  # the shaft's radius is measured on its vertices this far below the block's centre
#                                 (its ring at y 28.1: the rings above run up into the block and are wider)
# polished silver: a cool, near-neutral ramp (Rise's gold ramp's brightness, without its colour)
SILVER_RAMP = ((0.0, (0.42, 0.44, 0.47)), (0.5, (0.78, 0.79, 0.82)), (1.0, (0.97, 0.97, 0.98)))
# (the darker low end keeps the head's engraving readable: at 0.56 the first build read near white all over)
SILVER_CUBE_RAMP = ((0.0, (0.06, 0.06, 0.07)), (0.35, (0.42, 0.43, 0.45)), (0.7, (0.86, 0.87, 0.89)),
                    (1.0, (1.0, 1.0, 1.0)))
GRIP_Y = (-45.0, 34.0)        # the shaft below the head (Y 36..44): its leather islands are the wrap
NAVY = ((0.06, 0.09, 0.22), 1.0)    # dark navy leather at its 75th-percentile brightness, contrast kept
# (first build: white, ((0.93, 0.93, 0.91), 0.55); curator: "change the leather wrapping handle to a dark navy")


def set_positions(b, pos, used):
    """An unskinned SE BSTriShape with its vertex positions replaced (full-precision floats; every other vertex field
    kept) and its bound sphere refitted round the vertices the triangles use."""
    o = nifse.av_fields(b)['end']
    desc = struct.unpack_from('<Q', b, o + 28)[0]
    ntri, nvert, _ = struct.unpack_from('<HHI', b, o + 36)
    _, _, vs = nifse._layout(desc)
    assert pos.shape == (nvert, 3)
    b = bytearray(b)
    buf = np.frombuffer(bytes(b[o + 44:o + 44 + nvert * vs]), np.uint8).reshape(nvert, vs).copy()
    buf[:, 0:12] = pos.astype('<f4').view(np.uint8).reshape(nvert, 12)
    b[o + 44:o + 44 + nvert * vs] = buf.tobytes()
    P = pos[np.unique(used)]
    c = (P.min(0) + P.max(0)) / 2
    struct.pack_into('<4f', b, o, *c, float(np.linalg.norm(P - c, axis=1).max()))
    return bytes(b)


def tangent_convention(s):
    """Sting and Rise's tangent_convention by the median vertex, not the mean: the hammer's mirrored UV islands store
    flipped tangents (mean agreement 0.84), but the convention of the rest is clear."""
    du, dv = sr.uv_derivatives(s['pos'], s['uv'], s['tris'])
    du, dv = sr.normalize(du), sr.normalize(dv)
    Tn, Bn = sr.normalize(s['tangent']), sr.normalize(s['bitangent'])
    m = {('tan', 'du'): np.median((Tn * du).sum(1)), ('tan', 'dv'): np.median((Tn * dv).sum(1)),
         ('bit', 'du'): np.median((Bn * du).sum(1)), ('bit', 'dv'): np.median((Bn * dv).sum(1))}
    tan = max(('du', 'dv'), key=lambda d: abs(m[('tan', d)]))
    bit = max(('du', 'dv'), key=lambda d: abs(m[('bit', d)]))
    assert tan != bit and abs(m[('tan', tan)]) > 0.9 and abs(m[('bit', bit)]) > 0.9, m
    return tan, np.sign(m[('tan', tan)]), bit, np.sign(m[('bit', bit)])


def add_fist(nif, k, s, xf, name, tex, V, N, UV, T):
    """Append one of the fist's shapes to the root: its own copy of the hammer's shader (never shared: two shapes on
    one lighting shader froze the game, Clockwork Thunder) with the fist's texture set, tangents from its atlas UVs in
    the hammer's own convention."""
    assert len(V) < 65536 and len(T) < 65536, ('too big for one BSTriShape', name, len(V), len(T))
    b = nif.blocks[s['shader']]
    assert struct.unpack_from('<I', b, 0)[0] == 1 and not struct.unpack_from('<I', b, 16)[0] & 0x1000, \
        'the hammer shader is no longer a tangent-space environment-map shader'
    tan_axis, tan_sign, bit_axis, bit_sign = tangent_convention(s)
    du, dv = sr.uv_derivatives(V, UV, T)
    deriv = {'du': du, 'dv': dv}

    def frame(d, alt):
        f = d - N * (N * d).sum(1, keepdims=True)
        weak = np.linalg.norm(f, axis=1) < 1e-6
        f[weak] = np.cross(N[weak], alt[weak])
        weak = np.linalg.norm(f, axis=1) < 1e-6
        f[weak] = np.cross(N[weak], np.array([0.0, 0.0, 1.0]))
        weak = np.linalg.norm(f, axis=1) < 1e-6
        f[weak] = np.cross(N[weak], np.array([1.0, 0.0, 0.0]))
        return sr.normalize(f)
    other = {'du': dv, 'dv': du}
    tangent = tan_sign * frame(deriv[tan_axis], other[tan_axis])
    bitangent = bit_sign * frame(deriv[bit_axis], other[bit_axis])
    assert np.isfinite(tangent).all() and np.isfinite(bitangent).all()
    shader = nifse.copy_lighting_shader(nif, nif, s['shader'])
    ts = struct.unpack_from('<i', nif.blocks[shader], nifse.LSP_TEXSET)[0]
    paths = nifse.texture_paths(nif.blocks[ts])
    assert paths[4].lower().startswith('textures' + chr(92) + 'cubemaps') and paths[5].lower().endswith('_m.dds'), paths
    for slot, rel in ((0, tex + '_d.dds'), (1, tex + '_n.dds'), (4, OUT_E), (5, tex + '_m.dds')):
        paths[slot] = rel.replace('/', chr(92))
    nif.blocks[ts] = nifse.texture_set(paths)
    av_flags = struct.unpack_from('<I', nif.blocks[k], s['av']['flags'])[0]
    shape = nifse.write_trishape(nif.add_string(name), av_flags, xf, s['desc'],
                                 V, UV, N, tangent, bitangent, None, T, shader, -1)
    new = nif.add_block('BSTriShape', shape)
    root = nif.roots[0]
    _, kids = nifse.node_children(nif.blocks[root])
    nif.blocks[root] = nifse.set_children(nif.blocks[root], kids + [new])


def fist_textures(out_root, asm, tex):
    """The generated parts' painted set (fist_tex.py): diffuse, normal (alpha = highlight), Complex Material mask."""
    D, NM, CM = fist_tex.paint(asm, SILVER_RAMP)
    sr.write_texture(D, os.path.join(out_root, *(tex + '_d.dds').split('/')), 'BC7_UNORM')
    sr.write_texture(NM, os.path.join(out_root, *(tex + '_n.dds').split('/')), 'BC7_UNORM')
    mask = os.path.join(out_root, *(tex + '_m.dds').split('/'))
    sr.write_texture(CM, mask, 'BC7_UNORM')
    mip = sr.smallest_mip(mask)
    eps = 4.0 / 255.0
    assert mip[3] < 1 - eps and max(abs(mip[0] - mip[1]), abs(mip[0] - mip[2]), abs(mip[1] - mip[2])) >= 2 * eps, mip
    print('argent verdict %s textures: %dx%d atlas, complex mask 1x1 mip %s' % (
        tex.split('/')[-1], D.shape[1], D.shape[0], ' '.join('%.3f' % v for v in mip)))
    return D


def build_mesh(nif):
    hits = [i for i in nif.find('BSTriShape') if sr.name_of(nif, i).startswith(SHAPE)]
    assert len(hits) == 1
    k = hits[0]
    root = nif.roots[0]
    assert k == nifse.node_children(nif.blocks[root])[1][0], "the hammer is not the root's first shape"
    s = nifse.read_trishape(nif.blocks[k])
    xf = nifse.transform(nif.blocks[k])
    assert np.allclose(xf[0], 0) and np.allclose(xf[1], np.eye(3)) and abs(xf[2] - 1) < 1e-6, 'hammer is transformed'
    P, T = s['pos'].copy(), s['tris']
    _, wid = np.unique(np.round(P * 1e4).astype(np.int64), axis=0, return_inverse=True)
    lab = sr.islands(T, wid.ravel())

    def piece(pred, what):
        hit = [l for l in np.unique(lab) if pred(P[np.unique(T[lab == l])])]
        assert len(hit) == 1, ('no single ' + what, len(hit))
        return hit[0]
    head = piece(lambda V: np.ptp(V[:, 0]) > 20, 'head')
    knob = piece(lambda V: V[:, 1].min() > 40.5, 'knob')
    shaft = piece(lambda V: V[:, 1].min() < 0 and V[:, 1].max() > 37, 'shaft top')
    assert (lab == knob).sum() == KNOB_TRIS, ('the knob changed', (lab == knob).sum())
    cx = P[T][:, :, 0].mean(1)
    block = (lab == head) & (cx > CUT[0]) & (cx < CUT[1])
    bp = P[np.unique(T[block])]
    lo, hi = np.array(BLOCK)
    inner = bp[(bp[:, 0] > lo[0] - 0.05) & (bp[:, 0] < hi[0] + 0.05)]
    assert np.allclose(inner.min(0), lo, atol=0.05) and np.allclose(inner.max(0), hi, atol=0.05), \
        ("the head's centre block moved", inner.min(0), inner.max(0))
    c = (lo + hi) / 2
    keep = T[~(block | (lab == knob))]
    hv = np.unique(T[lab == head])
    P[hv] = c + (P[hv] - c) * HEAD_SCALE
    cut_x = (c[0] + (CUT[0] - c[0]) * HEAD_SCALE, c[0] + (CUT[1] - c[0]) * HEAD_SCALE)
    # the necks' half height / depth where they were cut (the sockets fit round them), the shaft's radius
    neck = [P[hv][np.abs(P[hv, 0] - x) < 0.35] for x in cut_x]
    neck_half = (max(np.abs(q[:, 1] - c[1]).max() for q in neck), max(np.abs(q[:, 2] - c[2]).max() for q in neck))
    sv = np.unique(T[lab == shaft])
    near = sv[(P[sv, 1] > c[1] + SHAFT_RADIUS_Y[0]) & (P[sv, 1] < c[1] + SHAFT_RADIUS_Y[1])]   # where the arm meets it
    assert len(near) >= 8, ('no shaft ring where the forearm meets it', len(near))
    shaft_r = float(np.hypot(P[near, 0] - c[0], P[near, 2] - c[2]).max())
    grids, info = gauntlet.gauntlet(c, cut_x, neck_half, shaft_r)
    shaft_top = min(info['shaft_join_y'] + SHAFT_INTO_ARM, info['shaft_held_y'] - 0.05)
    assert shaft_top > info['shaft_join_y'] + 0.2, ('the forearm holds too little of the shaft', shaft_top)
    top = sv[P[sv, 1] > shaft_top]
    P[top, 1] = shaft_top
    # ... and drawn in to the shaft's own radius: its rings up in the block were wider and poked through the arm
    rad = np.hypot(P[top, 0] - c[0], P[top, 2] - c[2])
    pull = np.minimum(1.0, shaft_r * 0.97 / np.maximum(rad, 1e-6))
    P[top, 0] = c[0] + (P[top, 0] - c[0]) * pull
    P[top, 2] = c[2] + (P[top, 2] - c[2]) * pull
    nif.blocks[k] = nifse.set_triangles(nif.blocks[k], keep)
    nif.blocks[k] = set_positions(nif.blocks[k], P, keep)
    # the blood overlays: the head again, cut and scaled the same way
    for name in BLOOD:
        hit = [i for i in nif.find('BSTriShape') if sr.name_of(nif, i) == name]
        assert len(hit) == 1, name
        b = nifse.read_trishape(nif.blocks[hit[0]])
        assert np.allclose(nifse.transform(nif.blocks[hit[0]])[1], np.eye(3))
        Pb, Tb = b['pos'], b['tris']
        assert len(Tb) == (lab == head).sum(), (name, 'is no longer a copy of the head')
        bc = Pb[Tb][:, :, 0].mean(1)
        bkeep = Tb[~((bc > CUT[0]) & (bc < CUT[1]))]
        assert len(bkeep) == (lab == head).sum() - block.sum(), (name, "cut differs from the head's")
        nif.blocks[hit[0]] = nifse.set_triangles(nif.blocks[hit[0]], bkeep)
        nif.blocks[hit[0]] = set_positions(nif.blocks[hit[0]], c + (Pb - c) * HEAD_SCALE, bkeep)
    # the fist, the stake and the sockets: one shape on its own atlas (added before the hammer's texture set
    # changes: its shader is copied from the hammer's)
    asm = fist_tex.assemble(grids)
    parts = fist_tex.split(asm)
    V_ = HEAD
    for group, name in V_['shapes']:
        if group in parts:
            add_fist(nif, k, s, xf, name, V_['tex'], *parts[group])
    assert set(parts) <= {g for g, _ in V_['shapes']}, parts.keys()
    # the knuckle motes (the charges, unlit): motes.py
    m = motes.add_motes(nif, c, info, nifse)
    print('argent verdict motes: 4 x Kittytail\'s circle (ring %.1f -> %.2f units, x %.4f) at %s, knuckles %s apart; '
          'textures %s' % (m['ring_r'], motes.MOTE_RADIUS, m['scale'],
                           ' '.join('(%.2f %.2f %.2f)' % tuple(p) for p in m['points']),
                           ' '.join('%.2f' % g for g in m['gaps']), ', '.join(m['textures'])))
    assert (m['gaps'] > 2 * motes.MOTE_RADIUS * 0.9).all(), ('the motes overlap', m['gaps'])
    # the hammer's own texture set: ours
    ts = struct.unpack_from('<i', nif.blocks[s['shader']], nifse.LSP_TEXSET)[0]
    paths = nifse.texture_paths(nif.blocks[ts])
    for slot, rel in ((0, OUT_D), (1, OUT_N), (4, OUT_E), (5, OUT_M)):
        paths[slot] = rel.replace('/', chr(92))
    nif.blocks[ts] = nifse.texture_set(paths)
    V = asm['V']
    print('argent verdict mesh: block (%d triangles) and knob (%d) cut, head x %.2f, face and spike scaled %.2f '
          '(cut ends at x %.2f / %.2f, necks %.2f x %.2f), shaft (r %.2f) top pulled down to y %.2f (%d vertices); '
          'fist (scale %.2f, x %.2f .. %.2f) + stake (r %.2f) + sockets: %d parts, %d vertices / %d triangles, x '
          '%.2f .. %.2f, y %.2f .. %.2f, z %.2f .. %.2f; atlas %.1f texels per unit; shapes %s' % (
              block.sum(), KNOB_TRIS, c[0], HEAD_SCALE, cut_x[0], cut_x[1], neck_half[0], neck_half[1], shaft_r,
              shaft_top, len(top), fist.HAND_SCALE, info['hand_x'][0], info['hand_x'][1],
              info['stake_r'], len(grids), len(V), len(asm['T']), V[:, 0].min(), V[:, 0].max(), V[:, 1].min(),
              V[:, 1].max(), V[:, 2].min(), V[:, 2].max(), asm['density'],
              ', '.join('%s %d tris' % (g, len(p[3])) for g, p in parts.items())))
    return nif, asm


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mods', default=os.path.join(sr.MO2, 'mods'))
    ap.add_argument('--target', default='Zenderal - Patch Collection')
    ap.add_argument('--out-root', default=None)
    args = ap.parse_args()
    mods = sr.profile_mods()
    out_root = args.out_root or os.path.join(args.mods, args.target)
    assert os.path.isdir(out_root), out_root
    src, nif = sr.load(args.mods, mods, MESH)
    if src != sr.EXPECT_SOURCE:
        sys.exit('%s now comes from %s, not %s' % (MESH, src, sr.EXPECT_SOURCE))
    shape = sr.main_shape(nif, SHAPE)        # Pretty's, untouched: the grip's UV islands
    sr.GOLD_RAMP = SILVER_RAMP                         # gold_set / gold_cubemap read these module constants
    sr.CUBE_RAMP = SILVER_CUBE_RAMP
    sr.gold_set(args.mods, mods, out_root, 'argent verdict (silver)', TEX + 'warhammer.dds', TEX + 'warhammer_n.dds',
                TEX + 'warhammer_m.dds', OUT_D, OUT_N, OUT_M, grip=(shape, GRIP_Y) + NAVY)
    _, raw = sr.winner(args.mods, [], sr.CHROME_CUBEMAP, sr.CHROME_BSAS)   # Bethesda's, never a replacer's
    sr.gold_cubemap(raw, os.path.join(out_root, *OUT_E.split('/')))
    for t in motes.VANILLA_TEXTURES:                    # the motes' flare: the game's own texture
        sr.winner(args.mods, mods, 'textures/effects/' + t, sr.TEX_BSAS)
    _, fresh = sr.load(args.mods, mods, MESH)
    mesh, asm = build_mesh(fresh)
    fist_textures(out_root, asm, HEAD['tex'])
    out = mesh.tobytes()
    back = nifse.Nif(out)
    assert back.tobytes() == out
    sr.check_refs(back)
    p = os.path.join(out_root, *HEAD['mesh'].split('/'))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'wb') as fh:
        fh.write(out)
    print('wrote %s (%d bytes, %d blocks)' % (p, len(out), len(back.blocks)))
    print('PyNifly reads it as', sr.readback(p))
    for gone in ('meshes/Zenderal/ArgentVerdict/ArgentVerdictGauntlet.nif',   # the gauntlet's old path, the hand's set
                 'textures/Zenderal/ArgentVerdict/ArgentFist_d.dds', 'textures/Zenderal/ArgentVerdict/ArgentFist_n.dds',
                 'textures/Zenderal/ArgentVerdict/ArgentFist_m.dds'):
        q = os.path.join(out_root, *gone.split('/'))
        if os.path.exists(q):
            os.remove(q)
            print('removed', q)
    print('argent verdict: mesh and texture sets written to', out_root)


if __name__ == '__main__':
    main()
