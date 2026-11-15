"""Whisper's soul wave, Soul Cleave's visual (curator 2026-11-15, on Reaping Souls' orbs: "the effect when power attacking is
very underwelming, can we have a horizonal purple slash the fires out in a conal wave infront of us dealing magic
damage?").

  meshes/Zenderal/Whisper/WhisperWave.nif   a horizontal crescent of purple light, the model of Soul Cleave's cone
                     projectile (811, Fire Breath's wave record shape), which carries it out ahead of the player: the
                     projectile's +Y is its flight. One arc (ARC: radius, centre behind the origin, half-angle), three
                     layers along it: a wide purple glow lying flat (OUTER), a narrow lilac core over it (CORE), and an
                     upright purple ribbon (FIN) so the wave still reads seen edge-on from behind. Each layer tapers to
                     points at the tips (sin^TAPER) and fades to its edges in vertex alpha, on its own copy of the
                     soft glow shader of Candlelight's flare sprite "Flash" (vanilla magic\\LightSpellActorFX.nif,
                     FXGlowSpotLinear, additive; the halo's source), colour set, double-sided, no controller. Built in
                     vanilla's Effects\\FXEmptyObject.nif (its spinning child node left off the root).

Usage:  python src/Whisper/tools/05-soul-wave.py [--out-root <dir>]
"""
import argparse
import importlib.util
import os
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
WAVE_OUT = 'meshes/Zenderal/Whisper/WhisperWave.nif'              # 03-build-records.py WAVE_MODEL (checked there)
EMPTY_BSA, EMPTY_KEY = 'Skyrim - Meshes0.bsa', chr(92).join(('meshes', 'effects', 'fxemptyobject.nif'))
FLARE_BSA, FLARE_KEY = 'Skyrim - Meshes1.bsa', chr(92).join(('meshes', 'magic', 'lightspellactorfx.nif'))
ARC = dict(radius=170.0, behind=110.0, half=68.0)                 # the crest 60 ahead, the tips 158 to each side
STEPS = (49, 9)                                                   # vertices along the arc, across a layer
TAPER = 0.6
# layer: (kind, width, rgb, emissive multiple)
LAYERS = {'ZP_WhisperWaveGlow': ('flat', 80.0, (150, 70, 255), 3.0),
          'ZP_WhisperWaveCore': ('flat', 22.0, (235, 200, 255), 3.6),
          'ZP_WhisperWaveFin': ('upright', 60.0, (165, 80, 255), 2.4)}
SHADER_COLOUR = (0.85, 0.55, 1.0)
SLSF2_DOUBLE_SIDED = 0x10


def _module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def layer_geometry(kind, width, rgb):
    """One layer of the crescent: positions, UVs, normals, tangents, bitangents, colours, triangles."""
    nu, nv = STEPS
    t = np.linspace(0.0, 1.0, nu)
    v = np.linspace(-0.5, 0.5, nv)
    a = np.radians(-ARC['half'] + 2 * ARC['half'] * t)
    taper = np.sin(np.pi * t) ** TAPER
    out = np.stack([np.sin(a), np.cos(a), np.zeros_like(a)], -1)          # radial, in the plane
    along = np.stack([np.cos(a), -np.sin(a), np.zeros_like(a)], -1)       # the arc's direction
    centre = np.array([0.0, -ARC['behind'], 0.0])
    T_, V_ = np.meshgrid(np.arange(nu), np.arange(nv), indexing='ij')
    off = (v[V_] * width * taper[T_])[..., None]
    base = centre + ARC['radius'] * out[T_]
    if kind == 'flat':
        P = base + off * out[T_]
        N = np.broadcast_to(np.array([0.0, 0.0, 1.0]), P.shape)
        B = out[T_]
    else:                                                                 # upright: a ribbon standing on the arc
        P = base + off * np.array([0.0, 0.0, 1.0])
        N = out[T_]
        B = np.broadcast_to(np.array([0.0, 0.0, 1.0]), P.shape)
    Tg = along[T_]
    UV = np.stack([t[T_], v[V_] + 0.5], -1)
    alpha = np.clip(1.0 - (2.0 * v[V_]) ** 2, 0.0, 1.0) * taper[T_]
    C = np.zeros((nu, nv, 4), np.uint8)
    C[..., :3] = np.array(rgb, np.uint8)
    C[..., 3] = np.round(255 * alpha).astype(np.uint8)
    idx = np.arange(nu * nv).reshape(nu, nv)
    tris = []
    for i in range(nu - 1):
        for j in range(nv - 1):
            q = idx[i, j], idx[i + 1, j], idx[i + 1, j + 1], idx[i, j + 1]
            tris += [(q[0], q[1], q[2]), (q[0], q[2], q[3])]
    flat = lambda x: np.ascontiguousarray(x.reshape(-1, x.shape[-1]))   # noqa: E731
    return (flat(P).astype(np.float64), flat(UV), flat(np.array(N, float)), flat(np.array(Tg, float)),
            flat(np.array(B, float)), flat(C), np.array(tris, np.int64))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out-root', default=None, help='default: the installed Zenderal - Patch Collection')
    args = ap.parse_args()
    sr = _module('sr_assets', os.path.join(ROOT, 'src', 'StingAndRise', 'tools', '01-build-assets.py'))
    nifse = sr.nifse
    b02 = _module('w02', os.path.join(HERE, '02-build-mesh.py'))
    out_root = args.out_root or os.path.join(sr.MO2, 'mods', 'Zenderal - Patch Collection')
    d, listing = b02._bsa.listing(os.path.join(b02.DATA, EMPTY_BSA))
    nif = nifse.Nif(b02._bsa.read(d, listing[EMPTY_KEY]))
    assert [nif.btype(i) for i in range(len(nif.blocks))][:3] == ['BSFadeNode', 'BSXFlags', 'NiNode'], 'not the empty object'
    d, listing = b02._bsa.listing(os.path.join(b02.DATA, FLARE_BSA))
    src = nifse.Nif(b02._bsa.read(d, listing[FLARE_KEY]))
    flash = next(k for k in range(len(src.blocks)) if src.btype(k) == 'BSTriShape'
                 and src.string(struct.unpack_from('<i', src.blocks[k], 0)[0]) == 'Flash')
    fs = nifse.read_trishape(src.blocks[flash])
    av_flags = struct.unpack_from('<I', src.blocks[flash], fs['av']['flags'])[0]
    root = nif.roots[0]
    shapes = []
    for name, (kind, width, rgb, mult) in LAYERS.items():
        b = bytearray(src.blocks[fs['shader']])                          # Candlelight's soft glow shader
        assert struct.unpack_from('<I', b, 4)[0] == 0
        struct.pack_into('<ii', b, 0, -1, 0)
        struct.pack_into('<i', b, 8, -1)                                 # no controller
        struct.pack_into('<I', b, 16, struct.unpack_from('<I', b, 16)[0] | SLSF2_DOUBLE_SIDED)
        at = 36
        ln = struct.unpack_from('<I', b, at)[0]
        at += 4 + ln + 4 + 16
        struct.pack_into('<4f', b, at, *SHADER_COLOUR, 1.0)
        struct.pack_into('<f', b, at + 16, mult)
        at += 16 + 4 + 4
        assert at + 4 + struct.unpack_from('<I', b, at)[0] == len(b), 'not the SE effect shader layout'
        shader = nif.add_block('BSEffectShaderProperty', bytes(b))
        al = bytearray(src.blocks[fs['alpha']])
        struct.pack_into('<ii', al, 0, -1, 0)
        struct.pack_into('<i', al, 8, -1)
        alpha = nif.add_block('NiAlphaProperty', bytes(al))
        P, UV, N, Tg, B, C, T = layer_geometry(kind, width, rgb)
        xf = (np.zeros(3), np.eye(3), 1.0)
        data = nifse.write_trishape(nif.add_string(name), av_flags, xf, fs['desc'], P, UV, N, Tg, B, C, T, shader, alpha)
        shapes.append(nif.add_block('BSTriShape', data))
    nif.blocks[root] = nifse.set_children(nif.blocks[root], shapes)       # the spinning child node left off
    data = nif.tobytes()
    back = nifse.Nif(data)
    assert back.tobytes() == data
    assert nifse.node_children(back.blocks[back.roots[0]])[1] == shapes
    for k in shapes:
        rs = nifse.read_trishape(back.blocks[k])
        assert back.btype(rs['shader']) == 'BSEffectShaderProperty' and back.btype(rs['alpha']) == 'NiAlphaProperty'
        assert np.abs(rs['pos']).max() < 400, 'the wave is out of shape'
    p = os.path.join(out_root, *WAVE_OUT.split('/'))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'wb') as fh:
        fh.write(data)
    P = np.vstack([nifse.read_trishape(back.blocks[k])['pos'] for k in shapes])
    print('%s: %d bytes; %d layers (%s), x %.0f..%.0f, y %.0f..%.0f, z %.0f..%.0f' % (
        p, len(data), len(shapes), ', '.join(LAYERS), P[:, 0].min(), P[:, 0].max(), P[:, 1].min(), P[:, 1].max(),
        P[:, 2].min(), P[:, 2].max()))


if __name__ == '__main__':
    main()
