"""Whisper's soul wisp, its look (curator 2026-11-15: "if the wave kills an enemy, let it spawn a purple wisp", "Fights
for you", "the wisp lasts for 30 seconds, only 1 wisp at a time"; the records are 03-build-records.py's).

  meshes/Zenderal/Whisper/WhisperWisp.nif    Enderal's Wisp's glow in purple: vanilla Actors\\Witchlight\\Character
                     Assets\\WitchlightMesh.nif (the art FXWitchlightMeshObject 08CDCE that FXWitchlightAttachSCRIPT
                     plays on every Wisp, Skyrim's Witchlight race), byte for byte but for its colours:
                       - its swirl spheres (sTREAKSiNNER, Sphere01, Sphere02) and its main glow (glowMain:0) take their
                         colour from the palette GradWhitchlight alone (a palette shader: colour = multiple x
                         palette(texture green, shader red x vertex red), Bottled Shaders' Effect.hlsl), so the palette
                         is repointed at our purple copy (PALETTE);
                       - its body (BODY, a lit, glowing stream texture) gets a purple copy of its diffuse (FLUID) and a
                         purple emissive colour (EMISSIVE); its glow map is grey and stays vanilla's;
                       - its rainbow glare (Cylinder01:0) and its glow streak (GlowStreak), no palette colour, get
                         purple shader colours (GLARE, STREAK).
                     Its controllers stay (an actor runs them: the swirls turn, the glow pulses).
  textures/Zenderal/Whisper/WhisperWisp_gradwhitchlight.dds   the game's own GradWhitchlight (not Glorious
                     Gradients' recolour), brightness normalised and laid on RAMP, alpha kept
  textures/Zenderal/Whisper/WhisperWisp_fluid.dds   the game's own FXfluidStream01, brightness on RAMP, alpha kept
  meshes/Zenderal/Whisper/WhisperWispBurst.nif   the wisp's burst when an Entropy spell strikes it (curator: "it
                     explodes"): vanilla Magic\\ExplosionIllusionLight01.nif (the model of the Wisp's own death
                     explosion wispDeathExplosion 0F1189), byte for byte but for its palettes: GradIllusion01 and
                     GradIllusion01Thin, which Glorious Gradients makes teal in this list, repointed at purple copies of
                     the game's own (BURST_PALETTES)

Usage:  python src/Whisper/tools/06-soul-wisp.py [--out-root <dir>]
"""
import argparse
import importlib.util
import os
import struct

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
SRC = 'meshes/actors/witchlight/character assets/witchlightmesh.nif'
OUT = 'meshes/Zenderal/Whisper/WhisperWisp.nif'           # 03-build-records.py WISP_MODEL (checked there)
TEX_DIR = 'textures/Zenderal/Whisper/'
PALETTE_SRC, PALETTE = 'textures/effects/gradients/gradwhitchlight.dds', TEX_DIR + 'WhisperWisp_gradwhitchlight.dds'
FLUID_SRC, FLUID = 'textures/effects/fxfluidstream01.dds', TEX_DIR + 'WhisperWisp_fluid.dds'
RAMP = ((0.0, (0.0, 0.0, 0.0)), (0.3, (0.20, 0.04, 0.42)), (0.65, (0.58, 0.22, 1.0)), (1.0, (0.88, 0.70, 1.0)))
EMISSIVE = (0.70, 0.30, 1.0)          # vanilla (0.46, 1.0, 0.91), teal
GLARE = (0.62, 0.32, 0.80)            # vanilla 0.72 grey (alpha 0.51 kept)
STREAK = (0.30, 0.12, 0.40)           # vanilla (0.16, 0.33, 0.33), teal
BURST_SRC = 'meshes/magic/explosionillusionlight01.nif'
BURST_OUT = 'meshes/Zenderal/Whisper/WhisperWispBurst.nif'   # 03-build-records.py WISP_BURST_MODEL (checked there)
BURST_PALETTES = {'gradillusion01.dds': TEX_DIR + 'WhisperWisp_gradillusion01.dds',
                  'gradillusion01thin.dds': TEX_DIR + 'WhisperWisp_gradillusion01thin.dds'}
PALETTE_SHAPES = ('sTREAKSiNNER', 'Sphere02', 'Sphere01', 'glowMain:0')
GLARE_SHAPE, STREAK_SHAPE, BODY_SHAPE = 'Cylinder01:0', 'GlowStreak', 'BODY'
LSP_TEXSET, LSP_EMISSIVE = 40, 44     # BSLightingShaderProperty (SE, no extra data)
BS = chr(92)


def _module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def fx_offsets(b):
    """BSEffectShaderProperty (SE): offsets of its source texture string, its colour and its palette string."""
    nextra = struct.unpack_from('<I', b, 4)[0]
    o = 8 + 4 * nextra + 4 + 4 + 4 + 8 + 8          # name, extra data, controller; flags 1 and 2, UV offset and scale
    src = o
    o += 4 + struct.unpack_from('<I', b, o)[0] + 4 + 16
    colour = o
    o += 16 + 4 + 4
    grey = o
    assert o + 4 + struct.unpack_from('<I', b, o)[0] == len(b), 'not the SE effect shader layout'
    return src, colour, grey


def string_at(b, at):
    ln = struct.unpack_from('<I', b, at)[0]
    return bytes(b[at + 4:at + 4 + ln]).decode('latin-1')


def set_string(b, at, value):
    ln = struct.unpack_from('<I', b, at)[0]
    enc = value.encode('latin-1')
    return bytes(b[:at]) + struct.pack('<I', len(enc)) + enc + bytes(b[at + 4 + ln:])


def purple(sr, mods, rel):
    """The game's own copy of a texture (not a mod's), brightness normalised and laid on RAMP, alpha kept."""
    src, raw = sr.winner(mods, [], rel, sr.TEX_BSAS)
    img = sr.load_image(raw).astype(np.float64)
    lum = img[..., 0] * 0.2126 + img[..., 1] * 0.7152 + img[..., 2] * 0.0722
    lum = lum / max(float(lum.max()), 1e-6)
    return np.concatenate([sr.ramp(lum, RAMP), img[..., 3:4]], -1).astype(np.float32), src


def shape_shader(n, nifse, name):
    """The shader block of the named shape (skinned shapes too: the shader ref sits after the NiAVObject fields)."""
    hits = [k for k in range(len(n.blocks)) if n.btype(k) == 'BSTriShape'
            and n.string(struct.unpack_from('<i', n.blocks[k], 0)[0]) == name]
    assert len(hits) == 1, (name, hits)
    o = nifse.av_fields(n.blocks[hits[0]])['end']
    sh, al = struct.unpack_from('<ii', n.blocks[hits[0]], o + 20)
    return sh


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out-root', default=None, help='default: the installed Zenderal - Patch Collection')
    args = ap.parse_args()
    sr = _module('sr_assets', os.path.join(ROOT, 'src', 'StingAndRise', 'tools', '01-build-assets.py'))
    nifse = sr.nifse
    mods = os.path.join(sr.MO2, 'mods')
    out_root = args.out_root or os.path.join(mods, 'Zenderal - Patch Collection')
    src, raw = sr.winner(mods, sr.profile_mods(), SRC)
    assert src == 'Skyrim - Meshes0.bsa', ('the Wisp\'s glow now comes from', src)
    n = nifse.Nif(raw)
    assert n.tobytes() == raw, 'round trip failed'
    pal_ours = PALETTE[len('textures/'):].replace('/', BS)
    fluid_ours = FLUID[len('textures/'):].replace('/', BS)
    done = {}
    for name in PALETTE_SHAPES:                                     # the palette parts: our purple palette
        sh = shape_shader(n, nifse, name)
        assert n.btype(sh) == 'BSEffectShaderProperty', name
        b = n.blocks[sh]
        _, _, grey = fx_offsets(b)
        assert string_at(b, grey).lower().endswith('gradwhitchlight.dds'), (name, string_at(b, grey))
        assert struct.unpack_from('<I', b, 12 + 4 * struct.unpack_from('<I', b, 4)[0])[0] & 0x10, (name, 'no palette colour')
        n.blocks[sh] = set_string(b, grey, 'textures' + BS + pal_ours)
        done[name] = 'palette'
    for name, rgb in ((GLARE_SHAPE, GLARE), (STREAK_SHAPE, STREAK)):  # no palette colour: the shader colour
        sh = shape_shader(n, nifse, name)
        b = bytearray(n.blocks[sh])
        assert not struct.unpack_from('<I', b, 12 + 4 * struct.unpack_from('<I', b, 4)[0])[0] & 0x10, name
        _, colour, _ = fx_offsets(b)
        struct.pack_into('<3f', b, colour, *rgb)
        n.blocks[sh] = bytes(b)
        done[name] = 'colour %s' % (rgb,)
    sh = shape_shader(n, nifse, BODY_SHAPE)                          # the body: purple diffuse and emissive
    assert n.btype(sh) == 'BSLightingShaderProperty'
    b = bytearray(n.blocks[sh])
    assert len(b) == 100 and struct.unpack_from('<I', b, 8)[0] == 0, 'not the SE lighting shader layout'
    struct.pack_into('<3f', b, LSP_EMISSIVE, *EMISSIVE)
    n.blocks[sh] = bytes(b)
    ts = struct.unpack_from('<i', b, LSP_TEXSET)[0]
    paths = nifse.texture_paths(n.blocks[ts])
    assert paths[0].lower() == r'textures\effects\fxfluidstream01.dds', paths
    paths[0] = 'textures' + BS + fluid_ours
    n.blocks[ts] = nifse.texture_set(paths)
    done[BODY_SHAPE] = 'diffuse + emissive %s' % (EMISSIVE,)
    data = n.tobytes()
    back = nifse.Nif(data)
    assert back.tobytes() == data
    for name in PALETTE_SHAPES:                                     # read back
        b = back.blocks[shape_shader(back, nifse, name)]
        assert string_at(b, fx_offsets(b)[2]) == 'textures' + BS + pal_ours, name
    for name, rgb in ((GLARE_SHAPE, GLARE), (STREAK_SHAPE, STREAK)):
        b = back.blocks[shape_shader(back, nifse, name)]
        assert np.allclose(struct.unpack_from('<3f', b, fx_offsets(b)[1]), rgb, atol=1e-6), name
    b = back.blocks[shape_shader(back, nifse, BODY_SHAPE)]
    assert nifse.texture_paths(back.blocks[struct.unpack_from('<i', b, LSP_TEXSET)[0]])[0] == 'textures' + BS + fluid_ours
    assert len(back.blocks) == len(n.blocks) and [back.btype(k) for k in range(len(back.blocks))] == \
        [nifse.Nif(raw).btype(k) for k in range(len(back.blocks))], 'the block list changed'
    p = os.path.join(out_root, *OUT.split('/'))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'wb') as fh:
        fh.write(data)
    textures = [(PALETTE, PALETTE_SRC), (FLUID, FLUID_SRC)]
    print('%s: %d bytes from %s; %s' % (p, len(data), SRC, '; '.join('%s %s' % kv for kv in done.items())))
    # the burst: every effect shader on a GradIllusion01(Thin) palette repointed at our purple copy
    src, raw = sr.winner(mods, sr.profile_mods(), BURST_SRC)
    assert src == 'Skyrim - Meshes1.bsa', ('the burst now comes from', src)
    n = nifse.Nif(raw)
    assert n.tobytes() == raw, 'round trip failed'
    swapped = {}
    for k in range(len(n.blocks)):
        if n.btype(k) != 'BSEffectShaderProperty':
            continue
        b = n.blocks[k]
        _, _, grey = fx_offsets(b)
        base = string_at(b, grey).replace('/', BS).split(BS)[-1].lower()
        if base in BURST_PALETTES:
            ours = BURST_PALETTES[base]
            n.blocks[k] = set_string(b, grey, 'textures' + BS + ours[len('textures/'):].replace('/', BS))
            swapped[base] = swapped.get(base, 0) + 1
        else:
            assert not base, ('a palette the burst keeps unrecoloured', base)
    assert set(swapped) == set(BURST_PALETTES), ('palettes not found', set(BURST_PALETTES) - set(swapped))
    data = n.tobytes()
    assert nifse.Nif(data).tobytes() == data
    p = os.path.join(out_root, *BURST_OUT.split('/'))
    with open(p, 'wb') as fh:
        fh.write(data)
    print('%s: %d bytes from %s; palettes swapped %s' % (p, len(data), BURST_SRC, swapped))
    textures += [(ours, 'textures/effects/gradients/' + base) for base, ours in BURST_PALETTES.items()]
    for rel, src_rel in textures:
        img, srcname = purple(sr, mods, src_rel)
        sr.write_texture(img, os.path.join(out_root, *rel.split('/')), 'BC7_UNORM')
        print('%s: %dx%d from %s (%s), purple' % (rel, img.shape[1], img.shape[0], src_rel, srcname))


if __name__ == '__main__':
    main()
