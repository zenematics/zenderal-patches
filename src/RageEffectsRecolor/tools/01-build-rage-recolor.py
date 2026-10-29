r"""Rage's effects in red and orange instead of pink and purple (curator 2026-10-27) -- never hand-edit the output.

Prophecy's Rage casts A Dark Warrior's Tale's class actions. Their meshes (KittyClass_DarkWarrior\*.nif in the pack's
BSA) take their colour from greyscale textures looked up in shared gradient palettes, ...\effects\gradients\grad*.dds
(gradillusiondark01, gradreanimate, gradtelekinesis01, gradsummonburst...: the purples and pinks). Vanilla spells share
those palettes, so they are not recoloured in place. Instead:
  * each mesh's palette paths are repointed from ...\gradients\... to ...\gradientz\... (same length: the NIF stores a
    path as a length-prefixed string, so the file keeps its size and every other byte);
  * each palette it uses is copied from the copy that wins in this modlist (a loose file in the enabled mods by MO2
    priority, then Enderal's and Skyrim's texture BSAs - vanilla's in Skyrim - Textures5, Dawnguard's textures\dlc01\
    ones in Textures4) to the same path under ...\gradientz\, recoloured: every coloured pixel's hue set from red (dark)
    to orange (bright); saturation, brightness and alpha kept.
The base colours in these meshes' effect shaders are white, so the palettes are all the colour there is.

Writes a NEW MO2 mod from the user's install; loose files win over the pack's BSA, so its place in the mod list does
not matter. Third-party content, generated on the user's machine, never committed.

Usage: python 01-build-rage-recolor.py [--modlist E:\Zenderal] [--profile Ultra]
"""
import argparse
import colorsys
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'src', 'Prophecy', 'tools'))
sys.path.insert(0, os.path.join(REPO, 'src', 'HorseCloakFluffFix', 'tools'))
import _bsa                                                      # noqa: E402
from nif import Nif, Reader                                      # noqa: E402
from PIL import Image                                            # noqa: E402

PACK_MOD = "A Dark Warrior's Tale"
PACK_BSA = 'KittyClass_DarkWarrior.bsa'
OUT_MOD = 'Zenderal - Rage Effects Recolor'
# the meshes of the six Rage actions' spells (their record closure in the cleaned plugin, 2026-10-27)
MESHES = ['DarkWarriorBeamSlash2Proj.nif', 'DarkWarriorBeamSlashProj.nif', 'DarkWarriorBeamSlashProj_Upgraded.nif',
          'DarkWarriorFlashProj.nif', 'DarkWarriorPierceHazard.nif', 'DarkWarriorPierceHazardCastProj.nif',
          'DarkWarriorSlashProj.nif', 'MAGINV2.nif', 'Maginv.nif']
# Enderal's archives first, then Skyrim's (first match wins)
GAME_BSAS = ['E - Textures2.bsa', 'E - Textures1.bsa'] + [f'Skyrim - Textures{i}.bsa' for i in range(8, -1, -1)]
HUE_DARK, HUE_BRIGHT = 0.0, 20.0      # degrees: blood red at black, deep orange at full brightness (32 was too light: curator)
MIN_SAT = 0.08                        # greys and whites stay as they are
GRAD, GRADZ = b'\\gradients\\', b'\\gradientz\\'


def texconv():
    tools = json.load(open(os.path.join(REPO, '.claude', 'config', 'tools.json'), encoding='utf-8-sig'))
    p = os.path.join(os.path.dirname(tools.get('xedit', '')), 'Edit Scripts', 'Texconvx64.exe')
    assert os.path.isfile(p), f'texconv not found next to tools.json xedit: {p}'
    return p


def recolour(im):
    im = im.convert('RGBA')
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            if s < MIN_SAT:
                continue
            h = (HUE_DARK + (HUE_BRIGHT - HUE_DARK) * v) / 360.0
            r2, g2, b2 = colorsys.hsv_to_rgb(h, s, v)
            px[x, y] = (round(r2 * 255), round(g2 * 255), round(b2 * 255), a)
    return im


def is_cool(r, g, b):
    h, s, v = colorsys.rgb_to_hsv(*(max(0.0, min(1.0, x)) for x in (r, g, b)))
    return s >= 0.12 and v >= 0.05 and 195 <= h * 360 <= 345      # blue, violet, purple, pink


def warm(r, g, b):
    """The same red-to-orange rule as the palettes, for a float colour (may exceed 1: kept to scale)."""
    peak = max(r, g, b, 1e-6)
    h, s, v = colorsys.rgb_to_hsv(r / peak, g / peak, b / peak)
    h = (HUE_DARK + (HUE_BRIGHT - HUE_DARK) * v) / 360.0
    return tuple(c * peak for c in colorsys.hsv_to_rgb(h, s, v))


def shader_base_colours(n):
    """Byte offsets of every BSEffectShaderProperty's base colour (SSE: after its source texture and falloff)."""
    out = []
    for typ, p, _ in n.blocks:
        if typ != 'BSEffectShaderProperty':
            continue
        r = Reader(n.data, p)
        r.skip(4); r.skip(4 * r.take('I')); r.skip(4)        # name, extra data, controller
        r.skip(24)                                           # shader flags 1/2, UV offset and scale
        r.skip(r.take('I'))                                  # source texture
        r.skip(20)                                           # clamp/lighting/env LOD/unknown, falloff angles + opacities
        out.append(r.p)
    return out


def particle_colours(n):
    """Byte offsets of the 3 RGBA colours in every BSPSysSimpleColorModifier (a particle system's tint over its life)."""
    out = []
    for typ, p, _ in n.blocks:
        if typ != 'BSPSysSimpleColorModifier':
            continue
        start = p + 4 + 4 + 4 + 1 + 24                       # name, order, target, active; fade/colour percents
        out += [start + 16 * k for k in range(3)]
    return out


# the clouds, smoke and swirls (curator 2026-10-27: "remove the cloud effects"): any shape or particle system whose
# effect shader uses one of these is detached from its parent node, as src/IchorGooNoGlow does
CLOUD_TEXTURES = {'cloud2.dds', 'cloudtile.dds', 'fxcloudroundtilenew.dds', 'fxsmokesub.dds', 'fxsmokesoftsub.dds',
                  'fxsmokepuffanim04.dds', 'fxsteamthickanim.dds', 'darkswirls.dds', 'darkswirls_blurry.dds'}
# not vaportile02: Dark Deluge's (backward power attack) beam is drawn with it - the curator wanted the beam back
# and by the shape's own name: the side attack's purple cloud was 'Vapor01' (magicicewisps.dds, a texture coloured by
# itself, base colour white - no palette or tint to warm) with a dark 'Darkness01' glow (curator 2026-10-27)
CLOUD_NAMES = ('vapor', 'darkness', 'smoke', 'cloud', 'mist', 'fog')
NODE_TYPES = ('NiNode', 'BSFadeNode', 'NiBillboardNode', 'BSValueNode', 'BSOrderedNode', 'NiSwitchNode')
DRAWN_TYPES = ('NiParticleSystem', 'BSTriShape', 'BSStripParticleSystem', 'NiTriShape', 'BSLODTriShape')


def avobject_end(r):
    """Skip an SSE NiAVObject's fields; the reader stops right after them."""
    r.skip(4); r.skip(4 * r.take('I')); r.skip(4)            # name, extra data, controller
    r.skip(4 + 12 + 36 + 4 + 4)                              # flags, translation, rotation, scale, collision


def shader_textures(n, idx):
    typ, p, _ = n.blocks[idx]
    if typ != 'BSEffectShaderProperty':
        return set()
    r = Reader(n.data, p)
    r.skip(4); r.skip(4 * r.take('I')); r.skip(4); r.skip(24)
    n1 = r.take('I'); src = bytes(n.data[r.p:r.p + n1]).decode('latin1'); r.skip(n1)
    r.skip(20 + 16 + 8)                                      # flags/falloff, base colour, scale, soft depth
    n2 = r.take('I'); grey = bytes(n.data[r.p:r.p + n2]).decode('latin1')
    return {t.lower().split('\\')[-1] for t in (src, grey) if t}


# Dark Deluge's meshes keep every shape: the curator wanted its beam back, and detaching the vapour shape alone did not
# bring it (2026-10-27) - colours are still fixed there, nothing is removed
KEEP_SHAPES = {'darkwarriorpiercehazard.nif', 'darkwarriorpiercehazardcastproj.nif'}
# the side power attack's cloud (Bloodletter + Soulrender), still there once recoloured - the curator wanted it gone:
# 'Sparkle01', a 64-unit wisp puff (fxmagicwisps01.dds). Exact names: their small 'Sparkle01B' sparks stay
CLOUD_SHAPES = {'darkwarriorslashproj.nif': {'sparkle01'}, 'darkwarriorflashproj.nif': {'sparkle01'}}


def detach_clouds(n, extra=()):
    """Every drawn block whose shader uses a cloud texture, or named in extra: its parent's child ref -> -1. Returns how many."""
    clouds = set()
    for i, (typ, p, _) in enumerate(n.blocks):
        if typ in DRAWN_TYPES:
            r = Reader(n.data, p)
            name = (n.string(Reader(n.data, p).take('i')) or '').lower()
            avobject_end(r)
            r.skip(16 + 4)                                   # bounding sphere, skin
            shader = r.take('i')
            if (0 <= shader < len(n.blocks) and shader_textures(n, shader) & CLOUD_TEXTURES) or name.startswith(CLOUD_NAMES) or name in extra:
                clouds.add(i)
    done = 0
    for typ, p, _ in n.blocks:
        if typ not in NODE_TYPES:
            continue
        r = Reader(n.data, p)
        avobject_end(r)
        for _ in range(r.take('I')):
            if r.take('i') in clouds:
                struct.pack_into('<i', n.data, r.p - 4, -1)
                done += 1
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--modlist', default=r'E:\Zenderal')
    ap.add_argument('--profile', default='Ultra')
    a = ap.parse_args()
    mods_dir = os.path.join(a.modlist, 'mods')
    enabled = [l[1:].strip() for l in open(os.path.join(a.modlist, 'profiles', a.profile, 'modlist.txt'),
                                           encoding='utf-8-sig') if l.startswith('+')]          # highest priority first
    out = os.path.join(mods_dir, OUT_MOD)
    shutil.rmtree(os.path.join(out, 'meshes'), ignore_errors=True)
    shutil.rmtree(os.path.join(out, 'textures'), ignore_errors=True)

    # the meshes, from the pack's BSA: every ...\gradients\ path -> ...\gradientz\ (the 's' becomes 'z', case kept)
    d, l = _bsa.listing(os.path.join(mods_dir, PACK_MOD, PACK_BSA))
    want = {m.lower(): m for m in MESHES}
    palettes = set()        # full lower-case paths, e.g. textures\dlc01\effects\gradients\gradshadowshield.dds
    done = 0
    for k, v in l.items():
        name = k.split('\\')[-1]
        if name not in want:
            continue
        data = bytearray(_bsa.read(d, v))
        low = bytes(data).lower()
        n, i = 0, low.find(GRAD)
        while i >= 0:
            data[i + 9] = ord('z') if data[i + 9] == ord('s') else ord('Z')
            start = low.rfind(b'textures\\', 0, i)
            end = low.find(b'.dds', i) + 4
            palettes.add(low[start:end].decode('latin1'))
            n += 1
            i = low.find(GRAD, i + 1)
        dst = os.path.join(out, 'meshes', 'KittyClass_DarkWarrior', want[name])
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, 'wb').write(bytes(data))
        # effect shaders tinted with a cool base colour (0.75, 0.25, 1.0 in 11 shaders, several with no palette at all:
        # the curator's "black / pink-purple clouds", 2026-10-27) get the same red-to-orange rule. Fixed-size floats,
        # rewritten in place. Particle emitters and the colour controllers' keys carry no purple (surveyed). The
        # particles' own tints do: BSPSysSimpleColorModifier's 3 colours - Sparkle01 fades dark blue -> red -> dark blue,
        # which blends through magenta and violet (the side power attack's cloud the curator kept seeing, 2026-10-27).
        nf = Nif(dst)
        tinted = 0
        for off in shader_base_colours(nf) + particle_colours(nf):
            r, g, b = struct.unpack_from('<3f', nf.data, off)
            if is_cool(r, g, b):
                struct.pack_into('<3f', nf.data, off, *warm(r, g, b))
                tinted += 1
        gone = 0 if name in KEEP_SHAPES else detach_clouds(nf, CLOUD_SHAPES.get(name, ()))
        if tinted or gone:
            open(dst, 'wb').write(bytes(nf.data))
        print(f'{want[name]}: {n} palette paths repointed, {tinted} shader colours warmed, {gone} cloud effects removed')
        done += 1
    assert done == len(MESHES), f'{done} of {len(MESHES)} meshes found in {PACK_BSA}'

    # each palette: the winning copy, recoloured, at its path under ...\gradientz\
    archives = []
    for b in GAME_BSAS:
        p = os.path.join(a.modlist, 'Stock Game', 'Data', b)
        if os.path.isfile(p):
            archives.append((b, *_bsa.listing(p)))
    tc = texconv()
    missing = []
    with tempfile.TemporaryDirectory() as tmp:
        for pal in sorted(palettes):
            src = None
            for m in enabled:                                   # Windows paths are case-insensitive
                f = os.path.join(mods_dir, m, pal)
                if os.path.isfile(f):
                    src = ('mod ' + m, open(f, 'rb').read())
                    break
            if not src:
                for b, bd, bl in archives:
                    if pal in bl:
                        src = (b, _bsa.read(bd, bl[pal]))
                        break
            if not src:
                missing.append(pal)        # missing in the game already: the mesh draws it the same way as before
                continue
            name = pal.split('\\')[-1]
            raw = os.path.join(tmp, name)
            open(raw, 'wb').write(src[1])
            im = recolour(Image.open(raw))
            png = os.path.join(tmp, name[:-4] + '.png')
            im.save(png)
            dst_dir = os.path.join(out, *pal.replace('\\gradients\\', '\\gradientz\\').split('\\')[:-1])
            os.makedirs(dst_dir, exist_ok=True)
            r = subprocess.run([tc, '-nologo', '-y', '-f', 'B8G8R8A8_UNORM', '-m', '1', '-o', dst_dir, png],
                               capture_output=True, text=True)
            assert r.returncode == 0, f'texconv failed on {pal}: {r.stdout}{r.stderr}'
            for f in os.listdir(dst_dir):          # texconv writes .DDS
                if f.lower() == name and f != name:
                    os.replace(os.path.join(dst_dir, f), os.path.join(dst_dir, name))
            print(f'{pal}: from {src[0]}, {im.width}x{im.height}, recoloured')
    meta = os.path.join(out, 'meta.ini')
    if not os.path.exists(meta):
        open(meta, 'w', encoding='utf-8', newline='\r\n').write('[General]\nmodid=0\nversion=1.0\ninstalled=true\n')
    for m in missing:
        print(f'NOT FOUND (missing in the game too, left as it was): {m}')
    print(f'{done} meshes, {len(palettes) - len(missing)} of {len(palettes)} palettes -> {out}')


if __name__ == '__main__':
    main()
