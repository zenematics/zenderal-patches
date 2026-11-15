"""Argent Verdict's knuckle motes (curator 2026-11-14: "can the charges be very small motes of light that light up on
each of the knuckles of the hammers gauntlet headpiece", "maybe this circle effect shown in the picture as the mote
but make them very small on each knuckle of the hammers head"; the picture is the rune circle of Kittytail's
Absolution, Dark Hierophant Magic's `light/LightDischargeLaser.nif`, its camera-facing node `FlareFX`).

tools/01 calls add_motes() on the mesh. Over each of the four knuckles (index .. little: the gauntlet's knuckle
guard where each gadling stands; the retired hand head had them on its bone knuckle heads) a node `ZP_ArgentMote1`..`4` at scale 0
(unlit) holds a copy of Kittytail's circle, MOTE_RADIUS across its outer rune ring: her camera-facing node (the
billboard FlareFX, without its lag controller) with her rune rings RunesA / RunesB (the rune atlas), RunesC (the
circle texture on a ring), the cross circle RuneCore and the white flare FlareA (twice her size, the mote's glow).
Each shape is a byte copy with its OWN copy of its effect shader and alpha property (never shared: Clockwork
Thunder's equip freeze), its shader's animation controllers dropped (a weapon runs none: the circle stands still),
emissive multiples set (MULT; her controllers ramped some of them), textures our copies (tools/03:
VerdictMoteCircle / VerdictMoteRunes) and her vanilla palette our white one (Glorious Gradients recolours the
vanilla gradients). The scripts light a mote by setting its node's scale to 1 (SKSE NetImmerse.SetNodeScale, both
views). (Version 2's `ZP_ArgentBoltNode`, where its lightning left the hammer, is gone since 2026-11-15.)
"""
import importlib.util
import os
import struct

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
import fist          # noqa: E402  (tools/01 puts this folder on the path)
import gauntlet      # noqa: E402

LASER = 'meshes/light/lightdischargelaser.nif'
BILLBOARD = 'FlareFX'
PARTS = ('RunesA', 'RunesB', 'RunesC', 'RuneCore', 'FlareA')     # the circle in the picture, outer ring first
RING = 'RunesA'                                                   # its outer rune ring: MOTE_RADIUS
MOTE_RADIUS = 0.75          # mesh units (the knuckles are about 1.8 apart: 2 x BUILD_HALF_W x 0.97 x HAND_SCALE / 4)
OUT = 0.25                  # the mote's centre stands this far off the knuckle's surface
FLARE_SCALE = 2.0           # the white flare (FlareA) at twice Kittytail's size: the mote's glow
MULT = {'RunesA': 1.4, 'RunesB': 1.4, 'RunesC': 1.0, 'RuneCore': 1.0, 'FlareA': 0.8}   # emissive multiples
NODE = 'ZP_ArgentMote%d'
TEXTURES = {'mcircle2.dds': r'textures\Zenderal\ArgentVerdict\VerdictMoteCircle.dds',      # tools/03
            'matlas.dds': r'textures\Zenderal\ArgentVerdict\VerdictMoteRunes.dds',
            'gradshoutselfarea.dds': r'textures\Zenderal\ArgentVerdict\Verdict_gradshoutselfareaW.dds'}
VANILLA_TEXTURES = ('fxwhiteflare01.dds',)                        # kept: the game's own (tools/01 checks it resolves)


def _t3():
    spec = importlib.util.spec_from_file_location('smite_assets', os.path.join(HERE, '03-smite-assets.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def knuckles(c, info):
    """The four knuckles in the mesh's frame: (point on the surface, outward direction), index .. little.
    The same formulas as gauntlet.armoured_hand (the knuckle guard), then the same placement as gauntlet.gauntlet
    (scaled HAND_SCALE, turned about the stake by the tilt, at c)."""
    b, half_w = fist.BUILD_STAKE_R, fist.BUILD_HALF_W
    k = 2 * half_w * 0.97 / fist.HAND_BREADTH_MM
    widths = np.array([f['width'] for f in fist.FINGERS])
    widths = widths / widths.sum() * 2 * half_w * 0.97
    xs = -half_w * 0.97 + np.concatenate([[0.0], np.cumsum(widths)[:-1]]) + widths / 2
    J = fist.finger_joints(b, k, xs)
    pts, dirs = [], []
    for j in J:
        n1 = fist.away(j['M'], j['P'], j['x'])
        kd = unit(0.45 * n1 + np.array([0.0, 0.0, -1.0]))
        pts.append(j['M'] + kd * gauntlet.GUARD[2] * j['hd'] + kd * k * gauntlet.GUARD[0])   # the guard's
        dirs.append(kd)
    th = -np.radians(info['tilt'])
    R = np.array([[1.0, 0.0, 0.0], [0.0, np.cos(th), -np.sin(th)], [0.0, np.sin(th), np.cos(th)]])
    P = np.asarray(c, float) + (fist.HAND_SCALE * np.array(pts)) @ R.T
    D = unit(np.array(dirs) @ R.T)
    return P, D


def _strip_net(b, name_idx):
    """NiObjectNET head: our name, no extra data (asserted), no controller."""
    b = bytearray(b)
    assert struct.unpack_from('<I', b, 4)[0] == 0, 'extra data on a copied block'
    struct.pack_into('<ii', b, 0, name_idx, 0)
    struct.pack_into('<i', b, 8, -1)
    return b


def _effect_shader(b, mult):
    """A copy of an SE BSEffectShaderProperty: no name, no controller, textures remapped (TEXTURES), the multiple."""
    b = _strip_net(b, -1)
    o = 12 + 4 + 4 + 8 + 8                          # NiObjectNET (no extra data), flags 1 and 2, UV offset, UV scale

    def swap(b, at):
        ln = struct.unpack_from('<I', b, at)[0]
        old = bytes(b[at + 4:at + 4 + ln]).decode('latin-1')
        base = old.replace('/', chr(92)).split(chr(92))[-1].lower()
        if base in TEXTURES:
            new = TEXTURES[base].encode('latin-1')
        else:
            assert not ln or base in VANILLA_TEXTURES, ('a texture with no copy', old)
            new = old.encode('latin-1')
        return bytearray(b[:at] + struct.pack('<I', len(new)) + new + b[at + 4 + ln:]), at + 4 + len(new), new
    b, o, src = swap(b, o)
    o += 4 + 16                                     # clamp, lighting influence, env map LOD, unknown; falloff
    emit = o
    struct.pack_into('<f', b, emit + 16, mult)
    o += 16 + 4 + 4
    b, o, grey = swap(b, o)
    assert o == len(b), ('not an SE effect shader', o, len(b))
    return b, src.decode('latin-1'), grey.decode('latin-1')


def _node(nif, name, flags, t, s, kids, billboard_tail=None):
    """A new NiNode (or, with billboard_tail, NiBillboardNode): no extra data, controller, collision or effects."""
    b = struct.pack('<iIiI', nif.add_string(name), 0, -1, flags) + struct.pack('<3f', *[float(x) for x in t])
    b += struct.pack('<9f', *np.eye(3).reshape(-1)) + struct.pack('<fi', float(s), -1)
    b += struct.pack('<I', len(kids)) + struct.pack('<%di' % len(kids), *kids) + struct.pack('<I', 0)
    if billboard_tail is not None:
        b += billboard_tail
    return nif.add_block('NiBillboardNode' if billboard_tail is not None else 'NiNode', b)


def add_motes(nif, c, info, nifse):
    """The four motes, appended to the root (see the module docstring). Returns a summary."""
    t3 = _t3()
    f, aflags, idx = t3.bsa_index(t3.BSA)
    src = nifse.Nif(t3.bsa_read(f, aflags, idx[LASER]))
    by_name = {}
    for k in range(len(src.blocks)):
        if src.btype(k) in ('BSTriShape', 'NiBillboardNode'):
            by_name.setdefault(t3.block_name(src, k), k)
    bb = by_name[BILLBOARD]
    assert src.btype(bb) == 'NiBillboardNode'
    o, kids = nifse.node_children(src.blocks[bb])
    bb_tail = bytes(src.blocks[bb][o + 4 + 4 * len(kids) + 4:])          # its billboard mode
    assert len(bb_tail) == 2, ('billboard layout', bb_tail)
    bb_flags = struct.unpack_from('<I', src.blocks[bb], nifse.av_fields(src.blocks[bb])['flags'])[0]
    parts = []
    for name in PARTS:
        k = by_name[name]
        assert k in kids, (name, 'is not under', BILLBOARD)
        s = nifse.read_trishape(src.blocks[k])                         # unskinned, no particle data (asserted)
        parts.append((name, k, s))
    ring = next(s for nm, _, s in parts if nm == RING)
    ring_r = float(np.abs(ring['pos'][:, :2]).max()) * nifse.transform(src.blocks[by_name[RING]])[2]
    bb_scale = MOTE_RADIUS / ring_r
    P, D = knuckles(c, info)
    root = nif.roots[0]
    _, rkids = nifse.node_children(nif.blocks[root])
    new_roots = []
    seen = set()
    for i, (p, d) in enumerate(zip(P, D), 1):
        shapes = []
        for name, k, s in parts:
            sb = bytearray(src.blocks[k])
            sh, tx, gr = _effect_shader(src.blocks[s['shader']], MULT[name])
            seen |= {tx, gr}
            sh_i = nif.add_block('BSEffectShaderProperty', sh)
            al_i = nif.add_block('NiAlphaProperty', _strip_net(src.blocks[s['alpha']], -1))
            sb = _strip_net(sb, nif.add_string('%s_%s%d' % (name, 'Mote', i)))
            struct.pack_into('<i', sb, s['av']['coll'], -1)
            struct.pack_into('<ii', sb, s['shader_at'], sh_i, al_i)
            if name == 'FlareA':
                t, R, sc = nifse.transform(sb)
                sb = nifse.set_transform(sb, t, R, sc * FLARE_SCALE)
            shapes.append(nif.add_block('BSTriShape', sb))
        bill = _node(nif, 'ZP_ArgentMoteCircle%d' % i, bb_flags, (0.0, 0.0, 0.0), bb_scale, shapes, bb_tail)
        new_roots.append(_node(nif, NODE % i, 14, p + d * OUT, 0.0, [bill]))      # scale 0: unlit
    nif.blocks[root] = nifse.set_children(nif.blocks[root], rkids + new_roots)
    gaps = np.linalg.norm(np.diff(P, axis=0), axis=1)
    return dict(points=P, dirs=D, ring_r=ring_r, scale=bb_scale, gaps=gaps, textures=sorted(seen - {''}))
