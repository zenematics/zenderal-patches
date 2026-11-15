"""Argent Verdict's Smite assets, version 3 (curator 2026-11-14: "Keep the 4 knuckle motes / instead of the Chain
lightning, smite 4 enemies in proximity to the player on charged power attack. the smite beams come from the sky like
regular smite. but the effect is like the effect from the picture (I believe this is the Absolution spell in Dark
hierohant)"): the meshes, textures and sounds tools/02's records point at, written into Zenderal - Patch Collection.
Version 2 (the bolt from the hammer and its chain; VerdictBolt.nif) was removed on 2026-11-15 with its backup.

  meshes/Zenderal/ArgentVerdict/VerdictSmiteBeam.nif: a smite beam (ACTI 856, placed by the release script over each
                enemy). Kittytail's Absolution beam (light/LightDischargeLaser.nif, Dark Hierophant Magic; permission
                on record), the picture's: particle strips flow from an emitter ring past her rune circle (the
                camera-facing FlareFX) to a gravity point BEAM_LENGTH along the mesh (EndGravityNode). Stood on end:
                a new node under the root (a placed reference's transform replaces the root's) turns the beam's +Y to
                -Z, so the circle hangs in the sky and the strips run straight down BEAM_LENGTH to the enemy (the
                script places it BeamLength above the enemy's feet; checked equal). Every palette our white one,
                every emissive and particle colour grey (Dark Hierophant's white light). Thinner than hers (curator,
                first test of version 3: "can we make them thinner?"): every emitter's particle radius and the rings
                the particles start on (EmitRing, EmitterADD) times BEAM_WIDTH; speeds and gravity (the length and the
                timing) untouched. Her textures under
                textures/Light ship at the pack's own paths (no other mod in the list has them); the rest are the
                game's own (checked to resolve).
  meshes/Zenderal/ArgentVerdict/VerdictOrb.nif: an orb (PROJ 85A) that flies out of a beam where it strikes
                (curator 2026-11-14: "add the motes we use on the knuckles as orbs that fire out of the smite beams
                (just like the regular Smite from Prophecy talent but dark heirophant effect)", then, with a picture of
                Prophecy's Smite orbs: "this is what a regular smites orbs look like, I want this but the Dark
                heirophant effects / colors"). Prophecy's Smite orb (Kittytails' Holy Templar Magic,
                lightpower/HolyBoltProj.nif = Bethesda's Dawnguard sunlight projectile, the load order's copy, which
                Prophecy ships) in Dark Hierophant's colours: its starburst rays, flash and sparkles (ORB_WHITE) on
                white palettes with grey colours, its soft wisps and halo (ORB_BLACK) black on normal blending, as the
                beam's impact. The first orb (the knuckle motes' rune circle) was never seen in game.
  meshes/Zenderal/ArgentVerdict/VerdictImpact.nif: where a beam lands (EXPL 857) and where an orb hits (EXPL 85E). Kittytail's impact from Dark
                Hierophant Magic (light/lightimpact.nif, its "BlacklightImpact"; permission on record): its flash and
                ring on white palettes, its mist black (normal blending), every colour key made grey.
  textures/Zenderal/ArgentVerdict/Verdict_<palette>W/K.dds: those palettes, from Bethesda's (the game archives:
                the list's Glorious Gradients recolours the vanilla ones): white = their brightness on a cool white,
                black = near black, alpha kept. gradshockhitW is also the struck target's glow (EFSH 84B, Kittytail's
                white shock glow).
  textures/Light/*.dds: the beam's own textures from the pack (BEAM_TEXTURES, read from the mesh).
  sound/fx/Zenderal/ArgentVerdict/SmiteStrike.wav: the strike (SNDR 80C), Kittytail's flarebig.wav 1.3 times faster
                and 2.4 s long (the Judgement Blade's strike sound, which the curator kept).
  sound/fx/Zenderal/ArgentVerdict/SmiteBell.wav: a church bell over the strike (SNDR 84F; curator 2026-11-14: "add
                this sound addtionally to the smite"), the curator's Motion Array file
                MA_A2DStudios_ChurchBellsImpacts_3.wav (24-bit / 48 kHz stereo; licensed, so neither it nor the
                output is committed) at 16-bit / 44.1 kHz: windowed-sinc resample, TPDF dither, peak kept under
                -0.2 dBFS. Only with --bell <source.wav>; without it the installed copy is kept.
  sound/fx/Zenderal/ArgentVerdict/SmiteCharged.wav: the hammer fully charged, ready to release (SNDR 858; curator
                2026-11-14: "add this sound once the weapon is full charged ready to release its payload"), the
                curator's Motion Array file MA_A2DStudios_ChurchBellsImpacts_0.wav (24-bit / 48 kHz stereo, licensed,
                not committed), converted the same way. Only with --charged <source.wav>.

  textures/Zenderal/ArgentVerdict/VerdictMoteCircle.dds, VerdictMoteRunes.dds: the knuckle motes' textures (motes.py,
                tools/01; curator: "maybe this circle effect shown in the picture as the mote"): Kittytail's cross
                circle (light/mcircle2.dds, 2048) and rune atlas (light/matlas.dds, 1024 x 512) from Absolution's
                circle, downsized (MOTE_TEXTURES: a mote is 1.5 units across), alpha kept.

Replaced the Judgement Blade and Penance fan assets of the same day (tools/03-judgement-blade-assets.py, scrapped
with the idea; its backup was deleted on 2026-11-15 with the other versions).

Source: reference/mods/_raw/DarkHierophantMagic/Ghostlight.bsa (the downloaded archive's contents) and the game's BSAs.

Usage:  python 03-smite-assets.py [--bell <MA_A2DStudios_ChurchBellsImpacts_3.wav>]
                                 [--charged <MA_A2DStudios_ChurchBellsImpacts_0.wav>] [--out-root <dir>]
"""
import argparse
import hashlib
import importlib.util
import io
import os
import struct
import sys
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
BSA = os.path.join(ROOT, 'reference', 'mods', '_raw', 'DarkHierophantMagic', 'Ghostlight.bsa')
TARGET = 'Zenderal - Patch Collection'
BEAM_SRC = 'meshes/light/lightdischargelaser.nif'                 # Kittytail's Absolution beam (Ghostlight.bsa)
BEAM_OUT = 'meshes/Zenderal/ArgentVerdict/VerdictSmiteBeam.nif'
BEAM_END = 'EndGravityNode'                                       # where her strips run to
BEAM_LENGTH = 1024.0                                              # its distance (asserted); the script's BeamLength
ORB_OUT = 'meshes/Zenderal/ArgentVerdict/VerdictOrb.nif'
ORB_SRC = 'meshes/lightpower/holyboltproj.nif'                    # Prophecy's Smite orb (the load order's copy)
ORB_SOURCE = 'Zenderal - Patch Collection'                        # where Prophecy's Holy Templar assets ship
ORB_WHITE = ('Flash03', 'Circle05', 'SuperSpray07', 'pSmallFlare03')   # the rays, the flash, the sparkles
ORB_BLACK = ('Wisps04:0', 'Halo:0')                                     # the soft wisps and halo
BEAM_WIDTH = 0.5                                                  # her particle radii and emitter rings x this
DOWN = np.array([[1.0, 0.0, 0.0], [0.0, 0.0, 1.0], [0.0, -1.0, 0.0]])   # local +Y (the beam) -> -Z, +Z -> +Y
SCRIPT = os.path.join(HERE, '..', 'Scripts', 'source', 'ZP_ArgentVerdictSmiteScript.psc')
IMPACT_SRC = 'meshes/light/lightimpact.nif'                      # Kittytail's (Ghostlight.bsa)
IMPACT_OUT = 'meshes/Zenderal/ArgentVerdict/VerdictImpact.nif'
IMPACT_WHITE = ('Circle01:2', 'Flash:1')
IMPACT_BLACK = ('ImpactMist:0',)
GLOW_PALETTE = 'textures/effects/gradients/gradshockhit.dds'      # the struck target's glow (EFSH 84B)
STRIKE_SRC = 'sound/fx/light/flarebig.wav'
STRIKE_OUT = 'sound/fx/Zenderal/ArgentVerdict/SmiteStrike.wav'
STRIKE = dict(speed=1.3, rate=44100, length=2.4, fade=0.4)
BELL_OUT = 'sound/fx/Zenderal/ArgentVerdict/SmiteBell.wav'
CHARGED_OUT = 'sound/fx/Zenderal/ArgentVerdict/SmiteCharged.wav'
BELL_RATE = 44100
BELL_TAPS = 32                                                   # half-width of the sinc kernel, in input samples
GRAD_DIR = 'textures/Zenderal/ArgentVerdict/'
MOTE_TEXTURES = (('textures/light/mcircle2.dds', GRAD_DIR + 'VerdictMoteCircle.dds', (256, 256)),
                 ('textures/light/matlas.dds', GRAD_DIR + 'VerdictMoteRunes.dds', (512, 256)))
WHITE = np.array([0.96, 0.98, 1.0])                              # a cool white, as Kittytail's light
BS = chr(92)


def bsa_index(path):
    """A Skyrim SE (v105) BSA's file table: path -> (size, offset), and the archive flags."""
    f = open(path, 'rb')
    magic, ver, _, aflags, nfold, _, _, lfile, _ = struct.unpack('<4sIIIIIIII', f.read(36))
    if magic != b'BSA\0' or ver != 105:
        sys.exit('%s: not an SE archive (%r %d)' % (path, magic, ver))
    folders = [struct.unpack('<QIIQ', f.read(24)) for _ in range(nfold)]
    recs = []
    for _, cnt, _, _ in folders:
        n = f.read(1)[0]
        name = f.read(n)[:-1].decode('cp1252')
        for _ in range(cnt):
            _, size, off = struct.unpack('<QII', f.read(16))
            recs.append((name, size, off))
    names = f.read(lfile).split(b'\0')
    idx = {(folder + '/' + nm.decode('cp1252')).replace(BS, '/').lower(): (size, off)
           for (folder, size, off), nm in zip(recs, names)}
    return f, aflags, idx


def bsa_read(f, aflags, entry):
    size, off = entry
    f.seek(off)
    data = f.read(size & 0x3FFFFFFF)
    if aflags & 0x100:                                   # embedded file names
        data = data[1 + data[0]:]
    if bool(aflags & 4) ^ bool(size & 0x40000000):       # compressed
        import lz4.frame
        return lz4.frame.decompress(data[4:])
    return data


def block_name(n, k):
    return n.string(struct.unpack_from('<i', n.blocks[k], 0)[0])


def effect_shader(b):
    """BSEffectShaderProperty (SE): offsets of its emissive colour and greyscale (palette) texture string."""
    nextra = struct.unpack_from('<I', b, 4)[0]
    o = 8 + 4 * nextra + 4                          # name, extra data, controller
    o += 4 + 4 + 8 + 8                              # shader flags 1 and 2, UV offset, UV scale
    o += 4 + struct.unpack_from('<I', b, o)[0]      # source texture
    o += 4 + 16                                     # clamp, lighting influence, env map LOD, unknown; falloff
    emit = o
    o += 16 + 4 + 4                                 # emissive colour, multiple, soft falloff depth
    grey = o
    o += 4 + struct.unpack_from('<I', b, o)[0]      # SE (BSVER 100) ends here: env map, normal, mask are FO4's
    assert o == len(b), ('not an SE effect shader', o, len(b))
    return emit, grey


def palette(sr, mods, rel, kind):
    """A white (W) or black (K) version of Bethesda's palette: brightness on a cool white, or near black."""
    _, raw = sr.winner(mods, [], rel, sr.TEX_BSAS)       # no mods: the game's own archives
    img = sr.load_image(raw).astype(np.float64)
    lum = img[..., 0] * 0.2126 + img[..., 1] * 0.7152 + img[..., 2] * 0.0722
    lum = lum / max(float(lum.max()), 1e-6)
    rgb = lum[..., None] * WHITE if kind == 'W' else (0.02 + 0.06 * lum)[..., None] * np.ones(3)
    return np.concatenate([rgb, img[..., 3:4]], -1)


def palette_name(rel, kind):
    return GRAD_DIR + 'Verdict_%s%s.dds' % (os.path.splitext(os.path.basename(rel))[0].lower(), kind)


def recolour(sr, mods, n, white, black, made):
    """White and black (see the docstring): each named shape's palette, emissive colour and (black) blending, then
    every colour key grey. Returns how many shapes it changed."""
    assert not n.find('NiPathInterpolator'), 'a path animation: NiPosData is not only colour keys here'
    seen = set()
    for k in range(len(n.blocks)):
        if n.btype(k) not in ('BSTriShape', 'NiParticleSystem'):
            continue
        name = block_name(n, k)
        if name not in white + black:
            continue
        seen.add(name)
        is_black = name in black
        o = sr.nifse.av_fields(n.blocks[k])['end']
        sh, al = struct.unpack_from('<ii', n.blocks[k], o + 20)
        assert sh >= 0 and n.btype(sh) == 'BSEffectShaderProperty', ('no effect shader', name)
        b = bytearray(n.blocks[sh])
        emit, grey = effect_shader(b)
        col = struct.unpack_from('<4f', b, emit)
        g = 0.0 if is_black else max(col[:3])
        struct.pack_into('<4f', b, emit, g, g, g, col[3])
        ln = struct.unpack_from('<I', b, grey)[0]
        if ln:                                                          # a shape with no palette: its colour only
            rel = bytes(b[grey + 4:grey + 4 + ln]).decode('latin-1').replace(BS, '/').lower()
            rel = rel if rel.startswith('textures/') else 'textures/' + rel
            new = palette_name(rel, 'K' if is_black else 'W')
            if new not in made:
                made[new] = palette(sr, mods, rel, 'K' if is_black else 'W')
            enc = new[len('textures/'):].replace('/', BS).encode('latin-1')
            b = b[:grey] + struct.pack('<I', len(enc)) + enc + b[grey + 4 + ln:]
        else:
            assert not is_black, ('a black shape needs a palette', name)
        n.blocks[sh] = bytearray(b)
        if is_black:                                                    # additive -> normal blending
            assert al >= 0 and n.btype(al) == 'NiAlphaProperty'
            a = bytearray(n.blocks[al])
            fl = struct.unpack_from('<H', a, len(a) - 3)[0]
            assert fl & 1 and (fl >> 5) & 15 == 0, ('not additive', name, hex(fl))
            struct.pack_into('<H', a, len(a) - 3, (fl & ~(15 << 5)) | (7 << 5))
            n.blocks[al] = a
    assert seen == set(white + black), ('shapes missing', set(white + black) - seen)
    for k in range(len(n.blocks)):                                     # the animated colours -> grey
        t = n.btype(k)
        b = bytearray(n.blocks[k])
        if t == 'NiPosData':
            nk = struct.unpack_from('<I', b, 0)[0]
            if nk:
                kt = struct.unpack_from('<I', b, 4)[0]
                step = {1: 16, 2: 40, 3: 28}[kt]
                assert len(b) == 8 + nk * step, ('NiPosData', kt, len(b))
                for i in range(nk):
                    p = 8 + i * step + 4
                    g = max(struct.unpack_from('<3f', b, p))
                    struct.pack_into('<3f', b, p, g, g, g)
                    if kt == 2:                                         # tangents: their mean
                        for q in (p + 12, p + 24):
                            m = sum(struct.unpack_from('<3f', b, q)) / 3
                            struct.pack_into('<3f', b, q, m, m, m)
        elif t == 'NiPoint3Interpolator':
            v = struct.unpack_from('<3f', b, 0)
            if max(abs(x) for x in v) < 1e30:
                g = max(v)
                struct.pack_into('<3f', b, 0, g, g, g)
        elif t == 'BSPSysSimpleColorModifier':
            assert len(b) == 85, ('colour modifier layout', len(b))
            for i in range(3):
                p = 37 + 16 * i
                v = struct.unpack_from('<4f', b, p)
                g = max(v[:3])
                struct.pack_into('<4f', b, p, g, g, g, v[3])
        n.blocks[k] = b
    data = n.tobytes()
    assert sr.nifse.Nif(data).tobytes() == data
    return data, len(seen)


def sky_beam(sr, mods, raw, made, nifse):
    """The Absolution beam stood on end, in white (see the docstring). Returns the NIF and the pack textures it names."""
    import re
    n = nifse.Nif(raw)
    ends = [k for k in n.find('NiNode') if block_name(n, k) == BEAM_END]
    assert len(ends) == 1, 'no single ' + BEAM_END
    t, R, sc = nifse.transform(n.blocks[ends[0]])
    assert np.allclose(t, (0.0, BEAM_LENGTH, 0.0)) and np.allclose(R, np.eye(3)) and abs(sc - 1) < 1e-6, ('the end moved', t)
    m = re.search(r'^Float Property BeamLength = ([\d.]+) AutoReadOnly', open(SCRIPT, encoding='utf-8').read(), re.M)
    assert m and abs(float(m.group(1)) - BEAM_LENGTH) < 1e-3, ('the script\'s BeamLength is not', BEAM_LENGTH)
    root = n.roots[0]
    rt, rR, rs = nifse.transform(n.blocks[root])
    assert np.allclose(rt, 0) and np.allclose(rR, np.eye(3)) and abs(rs - 1) < 1e-6, 'the root is transformed'
    _, kids = nifse.node_children(n.blocks[root])
    flags = struct.unpack_from('<I', n.blocks[root], nifse.av_fields(n.blocks[root])['flags'])[0]
    node = struct.pack('<iIiI', n.add_string('ZP_SkyDown'), 0, -1, flags) + struct.pack('<3f', 0.0, 0.0, 0.0)
    node += struct.pack('<9f', *DOWN.reshape(-1)) + struct.pack('<fi', 1.0, -1)
    node += struct.pack('<I', len(kids)) + struct.pack('<%di' % len(kids), *kids) + struct.pack('<I', 0)
    down = n.add_block('NiNode', node)
    n.blocks[root] = nifse.set_children(n.blocks[root], [down])
    assert struct.unpack_from('<I', n.blocks[n.find('BSXFlags')[0]], 4)[0] & 1, 'not Animated: its particles would not run'
    emitters = 0
    for k in n.find('NiPSysMeshEmitter'):                         # thinner: the particles' radius ...
        b = bytearray(n.blocks[k])
        nm = struct.unpack_from('<I', b, 69)[0]
        assert len(b) == 73 + 4 * nm + 20, ('mesh emitter layout', len(b))
        rad, radv = struct.unpack_from('<2f', b, 53)
        struct.pack_into('<2f', b, 53, rad * BEAM_WIDTH, radv * BEAM_WIDTH)
        n.blocks[k] = b
        emitters += 1
    rings = 0
    for k in n.find('BSTriShape'):                                # ... and the rings they start on
        if block_name(n, k).startswith(('EmitRing', 'EmitterADD')):
            t, R, sc = nifse.transform(n.blocks[k])
            n.blocks[k] = nifse.set_transform(n.blocks[k], t, R, sc * BEAM_WIDTH)
            rings += 1
    assert emitters == 11 and rings == 4, ('her emitters changed', emitters, rings)
    shaders = whiten(sr, mods, n, made, nifse)
    data = n.tobytes()
    assert nifse.Nif(data).tobytes() == data
    tex = sorted(set(x.decode('latin-1').lower().replace(BS, '/') for x in re.findall(rb'[A-Za-z0-9_\\/ .-]+[.]dds', raw, re.I)))
    tex = [t if t.startswith('textures/') else 'textures/' + t for t in tex]
    return data, shaders, tex


def whiten(sr, mods, n, made, nifse):
    """Every effect shader's palette our white one, every emissive and particle colour grey. Returns the shader count."""
    shaders = 0
    for k in n.find('BSEffectShaderProperty'):                    # palettes white, emissive colours grey
        b = bytearray(n.blocks[k])
        emit, grey = effect_shader(b)
        col = struct.unpack_from('<4f', b, emit)
        g = max(col[:3])
        struct.pack_into('<4f', b, emit, g, g, g, col[3])
        ln = struct.unpack_from('<I', b, grey)[0]
        if ln:
            rel = bytes(b[grey + 4:grey + 4 + ln]).decode('latin-1').replace(BS, '/').lower()
            rel = rel if rel.startswith('textures/') else 'textures/' + rel
            new = palette_name(rel, 'W')
            if new not in made:
                made[new] = palette(sr, mods, rel, 'W')
            enc = new[len('textures/'):].replace('/', BS).encode('latin-1')
            b = b[:grey] + struct.pack('<I', len(enc)) + enc + b[grey + 4 + ln:]
        n.blocks[k] = bytearray(b)
        shaders += 1
    for k in n.find('BSPSysSimpleColorModifier'):                 # particle colours grey
        b = bytearray(n.blocks[k])
        assert len(b) == 85, ('colour modifier layout', len(b))
        for i in range(3):
            q = 37 + 16 * i
            v = struct.unpack_from('<4f', b, q)
            g = max(v[:3])
            struct.pack_into('<4f', b, q, g, g, g, v[3])
        n.blocks[k] = b
    assert not n.find('NiPosData') and not n.find('NiPathInterpolator'), 'colour keys to grey too'
    return shaders


def orb(sr, mods, made):
    """The orb (see the docstring): Prophecy's Smite orb in white and black."""
    src, raw = sr.winner(mods, sr.profile_mods(), ORB_SRC)
    assert src == ORB_SOURCE, ('Prophecy\'s Smite orb now comes from', src)
    data, parts = recolour(sr, mods, sr.nifse.Nif(raw), ORB_WHITE, ORB_BLACK, made)
    return data, parts


def strike_sound(raw):
    """FlareBig faster and shorter (see STRIKE): linear resampling of 16-bit PCM."""
    w = wave.open(io.BytesIO(raw))
    ch, width, rate = w.getnchannels(), w.getsampwidth(), w.getframerate()
    assert width == 2, 'not 16-bit PCM'
    x = np.frombuffer(w.readframes(w.getnframes()), '<i2').reshape(-1, ch).astype(np.float64)
    step = STRIKE['speed'] * rate / STRIKE['rate']                     # source frames per output frame
    n_out = min(int(len(x) / step), int(STRIKE['length'] * STRIKE['rate']))
    pos = np.arange(n_out) * step
    i0 = np.floor(pos).astype(int)
    fr = (pos - i0)[:, None]
    y = x[i0] * (1 - fr) + x[np.minimum(i0 + 1, len(x) - 1)] * fr
    nf = int(STRIKE['fade'] * STRIKE['rate'])
    y[-nf:] *= np.linspace(1, 0, nf)[:, None]
    out = io.BytesIO()
    o = wave.open(out, 'wb')
    o.setnchannels(ch)
    o.setsampwidth(2)
    o.setframerate(STRIKE['rate'])
    o.writeframes(np.clip(np.round(y), -32768, 32767).astype('<i2').tobytes())
    o.close()
    return out.getvalue(), rate, len(x) / rate, n_out / STRIKE['rate']


def bell_sound(path):
    """The curator's bell at 16-bit / BELL_RATE: windowed-sinc resample (vectorised), TPDF dither, never clipped."""
    w = wave.open(path)
    ch, width, rate, nf = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
    raw = np.frombuffer(w.readframes(nf), np.uint8)
    assert width in (2, 3), '%s: %d-bit PCM not handled' % (path, width * 8)
    if width == 3:
        b = raw.reshape(-1, 3).astype(np.int32)
        v = b[:, 0] | (b[:, 1] << 8) | (b[:, 2] << 16)
        x = np.where(v & 0x800000, v - (1 << 24), v) / float(1 << 23)
    else:
        x = raw.view('<i2') / 32768.0
    x = x.reshape(-1, ch)
    if rate != BELL_RATE:
        ratio = BELL_RATE / rate
        cutoff = min(1.0, ratio) * 0.95
        t = np.arange(int(len(x) * ratio)) / ratio
        y = np.zeros((len(t), ch))
        c0 = np.floor(t).astype(np.int64)
        for off in range(-BELL_TAPS + 1, BELL_TAPS + 1):
            k = c0 + off
            d = t - k
            wgt = np.sinc(cutoff * d) * cutoff * (0.5 + 0.5 * np.cos(np.pi * d / BELL_TAPS)) * (np.abs(d) < BELL_TAPS)
            ok = (k >= 0) & (k < len(x))
            y[ok] += x[k[ok]] * wgt[ok, None]
        x = y
    peak = float(np.abs(x).max())
    gain = 0.98 / peak if peak > 0.98 else 1.0
    rnd = np.random.default_rng(0)
    q = x * gain * 32767 + rnd.random(x.shape) - rnd.random(x.shape)
    out = io.BytesIO()
    o = wave.open(out, 'wb')
    o.setnchannels(ch)
    o.setsampwidth(2)
    o.setframerate(BELL_RATE)
    o.writeframes(np.clip(np.round(q), -32768, 32767).astype('<i2').tobytes())
    o.close()
    return out.getvalue(), '%d ch %d-bit %d Hz %.2f s -> 16-bit %d Hz, peak %.1f dBFS' % (
        ch, width * 8, rate, nf / rate, BELL_RATE, 20 * np.log10(max(peak * gain, 1e-9)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out-root', default=None)
    ap.add_argument('--bell', default=None, help="the curator's MA_A2DStudios_ChurchBellsImpacts_3.wav")
    ap.add_argument('--charged', default=None, help="the curator's MA_A2DStudios_ChurchBellsImpacts_0.wav")
    args = ap.parse_args()
    if not os.path.isfile(BSA):
        sys.exit('%s missing: unpack Dark Hierophant Magic\'s archive there' % BSA)
    sr_spec = importlib.util.spec_from_file_location('sr', os.path.join(ROOT, 'src', 'StingAndRise', 'tools',
                                                                         '01-build-assets.py'))
    sr = importlib.util.module_from_spec(sr_spec)
    sr_spec.loader.exec_module(sr)
    mods = os.path.join(sr.MO2, 'mods')
    out_root = args.out_root or os.path.join(mods, TARGET)
    f, aflags, idx = bsa_index(BSA)
    for rel in (IMPACT_SRC, STRIKE_SRC):
        if rel not in idx:
            sys.exit('%s is not in the pack any more' % rel)
    made = {}
    if BEAM_SRC not in idx:
        sys.exit('%s is not in the pack any more' % BEAM_SRC)
    beam, nshaders, beam_tex = sky_beam(sr, mods, bsa_read(f, aflags, idx[BEAM_SRC]), made, sr.nifse)
    pack_tex = [t for t in beam_tex if t.startswith('textures/light/')]
    for t in beam_tex:
        if t in pack_tex:
            if t not in idx:
                sys.exit('%s names %s, which the pack does not ship' % (BEAM_SRC, t))
        elif not t.startswith('textures/zenderal/'):
            sr.winner(mods, sr.profile_mods(), t, sr.TEX_BSAS)          # the game's own: must resolve
    impact, ni = recolour(sr, mods, sr.nifse.Nif(bsa_read(f, aflags, idx[IMPACT_SRC])), IMPACT_WHITE, IMPACT_BLACK, made)
    orb_nif, orb_parts = orb(sr, mods, made)
    glow = palette_name(GLOW_PALETTE, 'W')
    if glow not in made:
        made[glow] = palette(sr, mods, GLOW_PALETTE, 'W')
    for rel, out, size in MOTE_TEXTURES:                               # the knuckle motes' circle and runes
        from PIL import Image
        img = sr.load_image(bsa_read(f, aflags, idx[rel]))
        assert img.shape[2] == 4 and img.shape[1] >= size[0] and img.shape[0] >= size[1], (rel, img.shape)
        chans = [np.asarray(Image.fromarray(img[..., i].astype(np.float32), 'F').resize(size, Image.LANCZOS))
                 for i in range(4)]
        made[out] = np.clip(np.stack(chans, -1), 0, 1)
    strike, src_rate, src_len, out_len = strike_sound(bsa_read(f, aflags, idx[STRIKE_SRC]))
    outputs = [(BEAM_OUT, beam, 'Kittytail\'s Absolution beam on end (%.0f down), %d shaders white' % (BEAM_LENGTH, nshaders)),
               (ORB_OUT, orb_nif, 'Prophecy\'s Smite orb (Holy Templar), %d parts white and black' % orb_parts),
               (IMPACT_OUT, impact, 'Kittytail\'s impact, %d parts white and black' % ni),
               (STRIKE_OUT, strike, '%d Hz %.1f s -> %d Hz %.1f s (x%.1f)' % (src_rate, src_len, STRIKE['rate'],
                                                                           out_len, STRIKE['speed']))]
    for t in pack_tex:                                                  # her textures, at the pack's paths
        outputs.append((t.replace('textures/light/', 'textures/Light/'), bsa_read(f, aflags, idx[t]), 'Kittytail\'s'))
    for src_path, out, flag, name in ((args.bell, BELL_OUT, '--bell', 'MA_A2DStudios_ChurchBellsImpacts_3.wav'),
                                      (args.charged, CHARGED_OUT, '--charged', 'MA_A2DStudios_ChurchBellsImpacts_0.wav')):
        if src_path:                                                   # the curator's licensed bells
            data, note = bell_sound(src_path)
            outputs.append((out, data, "the curator's " + os.path.basename(src_path) + ', ' + note))
        elif not os.path.isfile(os.path.join(out_root, *out.split('/'))):
            sys.exit('%s is not installed: pass %s <%s>' % (out, flag, name))
        else:
            print('%-56s kept (no %s)' % (out, flag))
    for rel, data, note in outputs:
        p = os.path.join(out_root, *rel.split('/'))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'wb') as fh:
            fh.write(data)
        print('%-56s %8d bytes  md5 %s  %s' % (rel, len(data), hashlib.md5(data).hexdigest(), note))
    for rel, img in sorted(made.items()):
        sr.write_texture(img, os.path.join(out_root, *rel.split('/')), 'BC7_UNORM')
        print('%-56s texture %dx%d' % (rel, img.shape[1], img.shape[0]))
    print('smite assets: written to', out_root)


if __name__ == '__main__':
    main()
