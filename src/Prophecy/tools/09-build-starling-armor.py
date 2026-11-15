"""Starling Power Armor: the Centurion Armor's mesh in worn, polished gold (curator, 2026-11-15: "retexture it with the
new gold cubemaps including the backpack / power pack? add some worn / scratches").

Ashihito Power Armor's CenturionArmor.nif (reference/mods/_raw) puts vanilla's Steam Centurion textures on the body
(14 plate shapes + Body + the two forearms), SRP's dwemetalsheet01 on the BackPack and SRP's DweLoreCube01 on the
AetheriumCrest, all on env-map shaders with Bethesda's bronze cubemap (15 body shapes in all). This tool

- builds one gold texture set per source (diffuse, normal, Complex Material mask, as Sting and Rise's gold_set does for
  Pretty's metal: every texel's luminance onto Rise's GOLD_RAMP, the normal map's highlight mask raised, a CM mask that
  reflects Dynamic Cubemaps' live surroundings): StarlingArmor, StarlingPack, StarlingCrest under
  textures/Zenderal/Prophecy/, plus Rise's gold chrome cubemap StarlingArmor_e for where CM is off;
- wears them in texture space (seeded, repeatable): tarnish clouds, grime spots, rubbed edges read from the normal
  map's slopes (bright, glossier), hairline scratches (pale fresh metal, duller, a groove in the normal map), a rubbed
  speckle - diffuse, gloss (CM G) and the highlight mask all move together;
- writes the mesh with those shapes' texture paths swapped (nothing else: Glass, the glow Ball and g_Glow keep theirs)
  into src/Prophecy/assets (the mesh is NOT copied by 01-build-trees.py any more) and, by default, into Patch Collection.

PG Patcher Output sits ABOVE Patch Collection in MO2 and had patched the 2026-11-13 copy of this mesh (the backpack
onto SRP's Complex Material, a black cubemap), so the first gold build never showed in game. The mesh is in
PGPatcher's blocklist (Tools/PG Patcher/PGPatcher/cfg/settings.json, `*\actors\ashihitoparace\centurionarmor\centurionarmor.nif`) and its stale output copy was removed; after a PGPatcher rerun, check no copy came back.

Run after 01-build-trees.py (which clears assets/). Textures are not committed (generated); the mesh is.
    python src/Prophecy/tools/09-build-starling-armor.py [--target "Zenderal - Patch Collection" | --no-deploy]
"""
import argparse
import importlib.util
import os
import shutil
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PATCH = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(PATCH))
SR = os.path.join(REPO, 'src', 'StingAndRise', 'tools')
sys.path.insert(0, SR)
_spec = importlib.util.spec_from_file_location('sr_assets', os.path.join(SR, '01-build-assets.py'))
sr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sr)
nifse = sr.nifse

RAW_MESH = os.path.join(REPO, 'reference', 'mods', '_raw', 'AshihitoPowerArmor', 'meshes', 'actors', 'AshihitoPArace',
                        'CenturionArmor', 'CenturionArmor.nif')
MESH_REL = 'meshes/actors/ashihitoparace/centurionarmor/centurionarmor.nif'
TEX_DIR = 'textures/Zenderal/Prophecy/'
CUBEMAP = TEX_DIR + 'StarlingArmor_e.dds'
# source diffuse (as the mesh names it, lower-cased) -> (our set's stem, scratch density per 2048^2, seed)
SETS = {
    'textures\\actors\\dwarvensteamcenturion\\steamcenturion.dds': ('StarlingArmor', 420, 11),
    'textures\\dungeons\\dwemerruins\\dwemetalsheet01.dds': ('StarlingPack', 260, 12),
    'textures\\clutter\\dwelorecube01.dds': ('StarlingCrest', 160, 13),
}
# wear (texture space; dt = shift on the ramp position, dg = glossiness change, dr = reflection change)
WEAR = dict(tarnish=(0.12, 5.0, 17.0),        # spread; cloud cycles across the texture (coarse, fine)
            grime=(0.70, 0.34, 11.0),         # noise threshold, darkening, cycles
            edge=(0.28, 0.65, 0.18),          # slope where edges start / are full; brightening at a full edge
            scratch=(0.24, 0.35, 0.9),        # brightening, gloss cut, groove depth (normal xy units)
            speckle=(0.0025, 0.12))           # dot chance per texel on edges+patches, brightening
POLISH_FLOOR = 0.55            # reflection share where the source's env mask / highlight mask is dullest
# the armor's gold: Rise's GOLD_RAMP starts at 0.74 brightness (a dagger's blade reads as highlights); a whole machine
# on it was washed out (first build), so this ramp keeps a dark low end for the recesses and engravings
GOLD_RAMP = ((0.0, (0.20, 0.13, 0.04)), (0.3, (0.52, 0.37, 0.12)), (0.6, (0.86, 0.68, 0.30)), (1.0, (1.0, 0.93, 0.68)))
# tone matching (build 3: the backpack's dark sheet landed a band darker than the plates): each set's luminance
# percentiles TONE_PCT are mapped onto the same ramp positions TONE_AT, so all three sets read as one gold
TONE_PCT = (2, 50, 98)
TONE_AT = (0.0, 0.50, 0.92)


def value_noise(shape, cycles, seed):
    """Smooth 0..1 noise over an (h, w) texture, `cycles` grid cells across (wrapping, so it tiles with the UVs)."""
    h, w = shape
    g = max(int(round(cycles)), 2)
    G = np.random.RandomState(seed).rand(g, g).astype(np.float32)
    y = (np.arange(h) + 0.5) / h * g
    x = (np.arange(w) + 0.5) / w * g
    y0, x0 = np.floor(y).astype(int), np.floor(x).astype(int)
    fy, fx = y - y0, x - x0
    fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
    ya, yb = y0 % g, (y0 + 1) % g
    xa, xb = x0 % g, (x0 + 1) % g
    top = G[ya][:, xa] * (1 - fx)[None, :] + G[ya][:, xb] * fx[None, :]
    bot = G[yb][:, xa] * (1 - fx)[None, :] + G[yb][:, xb] * fx[None, :]
    return top * (1 - fy)[:, None] + bot * fy[:, None]


def scratches(shape, count, seed):
    """Hairline scratches drawn in texture space: short, slightly bent, 1-2 texels wide, softened. 0..1 mask."""
    from PIL import Image, ImageDraw, ImageFilter
    h, w = shape
    rng = np.random.RandomState(seed)
    im = Image.new('L', (w, h), 0)
    dr = ImageDraw.Draw(im)
    for _ in range(count):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        a = rng.uniform(0, 2 * np.pi)
        L = rng.uniform(0.02, 0.18) * w
        bend = rng.uniform(-0.25, 0.25)
        pts = []
        for s in np.linspace(0, 1, 6):
            ang = a + bend * s
            pts.append((x + np.cos(ang) * L * s, y + np.sin(ang) * L * s))
        dr.line(pts, fill=int(rng.uniform(190, 255)), width=int(rng.choice([1, 1, 2, 2, 3])))
    im = im.filter(ImageFilter.GaussianBlur(0.5))
    return np.asarray(im, np.float32) / 255.0


def worn_gold(label, D, N, polish, used, density, seed):
    """One gold set from a source diffuse D (h, w, 4), normal N (h, w, 4) and a 0..1 polish map (h, w): returns
    (diffuse rgb, normal rgba, complex-material mask rgba), each float 0..1."""
    W = WEAR
    h, w = D.shape[:2]
    lum = D[..., :3] @ np.array([0.299, 0.587, 0.114])
    lit = used & (lum > 0.02)
    anchors = np.percentile(lum[lit], TONE_PCT)
    lo, hi = anchors[0], anchors[-1]
    t = np.interp(lum, anchors, TONE_AT)
    # the normal map's slope: where plates meet, rivets, pipe edges = the rubbed, polished edges
    nx, ny = N[..., 0] * 2 - 1, N[..., 1] * 2 - 1
    slope = np.hypot(nx, ny)
    edge = sr.smoothstep(W['edge'][0], W['edge'][1], slope)
    cloud = value_noise((h, w), W['tarnish'][1], seed) * 0.6 + value_noise((h, w), W['tarnish'][2], seed + 1) * 0.4
    grime = sr.smoothstep(W['grime'][0], W['grime'][0] + 0.12, value_noise((h, w), W['grime'][2], seed + 2))
    grime *= 0.5 + 0.5 * value_noise((h, w), W['grime'][2] * 7, seed + 3)
    grime *= 1 - 0.7 * edge                         # grime gathers in the flats and recesses, not on rubbed edges
    sc = scratches((h, w), int(density * (h * w) / (2048 * 2048)), seed + 4)
    rng = np.random.RandomState(seed + 5)
    dens = np.clip(edge + sr.smoothstep(0.62, 0.8, value_noise((h, w), 4.0, seed + 6)), 0, 1)
    dots = (rng.rand(h, w) < dens * W['speckle'][0] * 40).astype(np.float32)
    dots = np.maximum.reduce([dots, np.roll(dots, 1, 0), np.roll(dots, 1, 1), np.roll(dots, (1, 1), (0, 1))]) * 0.8
    dt = ((cloud - 0.5) * 2 * W['tarnish'][0] - W['grime'][1] * grime + W['edge'][2] * edge +
          W['scratch'][0] * sc + W['speckle'][1] * dots)
    rgb = sr.ramp(np.clip(t + dt, 0, 1), GOLD_RAMP)
    rgb = np.where(used[..., None], rgb, D[..., :3])
    # the normal map: scratches cut a groove (the mask's gradient tilts the normal), the highlight mask follows the gold
    gy, gx = np.gradient(sc)
    nx2 = nx - W['scratch'][2] * gx * 8
    ny2 = ny - W['scratch'][2] * gy * 8
    nz = np.sqrt(np.clip(1 - nx2 ** 2 - ny2 ** 2, 0.05, 1))
    n_out = N.copy()
    n_out[..., 0] = np.where(used, nx2 / 2 + 0.5, N[..., 0])
    n_out[..., 1] = np.where(used, ny2 / 2 + 0.5, N[..., 1])
    n_out[..., 2] = np.where(used, nz, N[..., 2])
    a0 = N[..., 3]
    spec = np.clip(sr.SPEC[0] + sr.SPEC[1] * (a0 - sr.SPEC[2]), 0, 1)
    spec = np.clip(spec * (0.75 + 0.25 * polish) - 0.35 * grime - 0.25 * sc + 0.15 * edge, 0.05, 1)
    n_out[..., 3] = np.where(used, spec, a0)
    # Complex Material: R reflects, G glossiness, B metalness, A 0 (parallax off; marks the mask complex)
    shine = np.clip(polish + 0.5 * edge, 0, 1)               # rubbed edges and rivets reflect like the polished plates
    reflect = sr.COMPLEX[0] * (POLISH_FLOOR + (1 - POLISH_FLOOR) * shine) * (1 - 0.6 * grime)
    gloss = np.clip(sr.COMPLEX[1] - 0.06 * (1 - polish) - 0.08 * np.clip(0.5 - cloud, 0, 1) * 2 - 0.3 * grime -
                    W['scratch'][1] * sc + 0.08 * edge, 0.2, 1)
    cm = np.stack([reflect, gloss, np.full_like(gloss, sr.COMPLEX[2]), np.zeros_like(gloss)], -1)
    cm = np.where(used[..., None], cm, np.stack([np.zeros_like(gloss), np.full_like(gloss, 0.2), np.zeros_like(gloss),
                                                 np.zeros_like(gloss)], -1))
    print('%s: %dx%d, %d%% used; luminance %.2f..%.2f onto the gold ramp; edges %.1f%%, grime %.1f%%, %d scratches '
          '(%.1f%% of texels), tarnish +-%.2f; highlight mask %.2f -> %.2f; CM reflect %.2f gloss %.2f' % (
              label, w, h, 100 * used.mean(), lo, hi, 100 * (edge > 0.5).mean(), 100 * (grime > 0.3).mean(),
              int(density * (h * w) / (2048 * 2048)), 100 * (sc > 0.3).mean(), W['tarnish'][0], a0[used].mean(),
              spec[used].mean(), reflect[used].mean(), gloss[used].mean()))
    return rgb, n_out, cm


def write_set(out_root, stem, rgb, nrm, cm):
    d = os.path.join(out_root, *(TEX_DIR + stem + '.dds').split('/'))
    n = os.path.join(out_root, *(TEX_DIR + stem + '_n.dds').split('/'))
    m = os.path.join(out_root, *(TEX_DIR + stem + '_m.dds').split('/'))
    sr.write_texture(rgb, d, 'BC7_UNORM')
    sr.write_texture(nrm, n, 'BC7_UNORM')
    sr.write_texture(cm, m, 'BC7_UNORM')
    back = sr.load_image(open(m, 'rb').read())
    mip = sr.smallest_mip(m)
    eps = 4.0 / 255.0
    # Bottled Shaders' own test on the 1x1 mip: alpha below 1 - eps and not grey, else it reads a plain env mask
    assert back[..., 3].max() <= eps and mip[3] < 1 - eps, 'alpha lost: %s would not be complex' % m
    assert max(abs(mip[0] - mip[1]), abs(mip[0] - mip[2]), abs(mip[1] - mip[2])) >= 2 * eps, 'grey 1x1 mip %s' % (mip,)
    print('  wrote %s, _n, _m (1x1 mip %s)' % (d, ' '.join('%.3f' % v for v in mip)))
    return [d, n, m]


def build_textures(mods_dir, mods, out_root):
    written = []
    for src_d, (stem, density, seed) in SETS.items():
        rel = src_d.replace('\\', '/')
        base = rel[:-4]
        srcs = {}
        for k, r in (('d', rel), ('n', base + '_n.dds')):
            s, raw = sr.winner(mods_dir, mods, r, sr.TEX_BSAS)
            srcs[k] = sr.load_image(raw)
            print('  %s <- %s' % (r, s))
        D, N = srcs['d'], srcs['n']
        if N.shape[:2] != D.shape[:2]:
            from PIL import Image
            N = np.asarray(Image.fromarray((N * 255).astype(np.uint8)).resize(D.shape[1::-1], Image.BILINEAR),
                           np.float32) / 255
        used = D[..., 3] > 0.5 if stem == 'StarlingArmor' else np.ones(D.shape[:2], bool)   # vanilla's atlas has gaps
        try:                                        # the source's env mask, where it has one, is its polish
            s, raw = sr.winner(mods_dir, mods, base + '_m.dds', sr.TEX_BSAS)
            from PIL import Image
            M = sr.load_image(raw)[..., 0]
            M = np.asarray(Image.fromarray((M * 255).astype(np.uint8)).resize(D.shape[1::-1], Image.BILINEAR),
                           np.float32) / 255
            print('  %s <- %s (polish)' % (base + '_m.dds', s))
        except SystemExit:
            M = N[..., 3]                           # else its highlight mask
        lo, hi = np.percentile(M[used], [5, 95])
        polish = np.clip((M - lo) / max(hi - lo, 1e-3), 0, 1)
        rgb, nrm, cm = worn_gold(stem, D, N, polish, used, density, seed)
        written += write_set(out_root, stem, rgb, nrm, cm)
    _, raw = sr.winner(mods_dir, [], sr.CHROME_CUBEMAP, sr.CHROME_BSAS)   # Bethesda's chrome, never a replacer's
    cube = os.path.join(out_root, *CUBEMAP.split('/'))
    sr.gold_cubemap(raw, cube)
    written.append(cube)
    return written


def build_mesh():
    """The mod's mesh with the three sets' shapes retargeted (and the pack's specular tint whitened); everything
    else byte-identical."""
    raw = open(RAW_MESH, 'rb').read()
    nif = nifse.Nif(raw)
    assert nif.tobytes() == raw
    swapped = {}
    for k in nif.find('BSTriShape'):
        b = nif.blocks[k]
        o = nifse.av_fields(b)['end']
        sh = struct.unpack_from('<i', b, o + 20)[0]
        if sh < 0 or nif.btype(sh) != 'BSLightingShaderProperty':
            continue
        ts = struct.unpack_from('<i', nif.blocks[sh], nifse.LSP_TEXSET)[0]
        paths = nifse.texture_paths(nif.blocks[ts])
        key = paths[0].lower()
        if key not in SETS:
            continue
        stem = SETS[key][0]
        assert struct.unpack_from('<I', nif.blocks[sh], 0)[0] == 1, ('not an env-map shader', k)
        new = list(paths)
        new[0] = (TEX_DIR + stem + '.dds').replace('/', '\\')
        new[1] = (TEX_DIR + stem + '_n.dds').replace('/', '\\')
        new[4] = CUBEMAP.replace('/', '\\')
        new[5] = (TEX_DIR + stem + '_m.dds').replace('/', '\\')
        nif.blocks[ts] = nifse.texture_set(new)
        if stem == 'StarlingPack':      # the mod gave the pack a bronze specular tint; white, as the body's
            struct.pack_into('<3f', nif.blocks[sh], 76, 1.0, 1.0, 1.0)
        swapped.setdefault(stem, []).append(nif.string(struct.unpack_from('<i', b, 0)[0]))
    assert sorted(swapped) == sorted(s for s, _, _ in SETS.values()), swapped
    assert len(swapped['StarlingArmor']) == 15 and len(swapped['StarlingPack']) == 1 and len(swapped['StarlingCrest']) == 1, {
        k: len(v) for k, v in swapped.items()}
    out = nif.tobytes()
    back = nifse.Nif(out)
    assert back.tobytes() == out and len(back.blocks) == len(nif.blocks)
    for k in back.find('BSShaderTextureSet'):
        for p in nifse.texture_paths(back.blocks[k]):
            assert not p or p.lower().startswith('textures\\'), p
    print('mesh: %d shapes on StarlingArmor, BackPack -> StarlingPack, %s -> StarlingCrest; %d -> %d bytes' % (
        len(swapped['StarlingArmor']), swapped['StarlingCrest'][0], len(raw), len(out)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mods', default=os.path.join(sr.MO2, 'mods'))
    ap.add_argument('--target', default='Zenderal - Patch Collection', help='MO2 mod to deploy into as well')
    ap.add_argument('--no-deploy', action='store_true')
    args = ap.parse_args()
    mods = sr.profile_mods()
    assets = os.path.join(PATCH, 'assets')
    files = build_textures(args.mods, mods, assets)
    mesh = build_mesh()
    mp = os.path.join(assets, *MESH_REL.split('/'))
    os.makedirs(os.path.dirname(mp), exist_ok=True)
    open(mp, 'wb').write(mesh)
    files.append(mp)
    print('PyNifly reads it as', sr.readback(mp))
    if not args.no_deploy:
        target = os.path.join(args.mods, args.target)
        assert os.path.isdir(target), target
        for f in files:
            rel = os.path.relpath(f, assets)
            dst = os.path.join(target, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(f, dst)
        print('deployed %d files into %s' % (len(files), target))


if __name__ == '__main__':
    main()
