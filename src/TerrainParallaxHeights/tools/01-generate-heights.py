"""Rebuild the `Zenderal - Terrain Parallax Heights` MO2 mod: real height maps for Enderal's ground textures.

ENB terrain parallax (`EnableTerrainParallax` / `EnableComplexTerrainParallax`) reads the height of every
landscape layer from the ALPHA channel of its diffuse. Skyrim 202X Complex Terrain Parallax ships proper
heights for the vanilla-path textures (alpha mean ~105, std 3-30), but every SRP Enderal texture under
`enderal/landscape/` (and two of Enderal's own from its BSA) has a flat white alpha = "maximum height
everywhere". Under parallax that pushes the whole texture sideways by an amount that grows with the view
angle: sharp under the camera, smeared into radial streaks further out (seen 2026-10-11 on
`_00E_Rockpath01NRIced` at Frost Crystal Passage, Vyn cell -32,16; turning terrain parallax off fixed it).

This script finds every landscape texture Enderal uses (LTEX -> TXST diffuse, from reference/base), resolves
the winning copy in the live MO2 profile (loose mods by priority, else the game BSAs), and for each one whose
alpha is NOT a height map (flat, or a binary cut-out mask) writes a copy whose RGB is unchanged and whose
alpha is a height derived from the texture's own detail: high-passed luminance, scaled to 202X's range.

The textures are SRP's / SureAI's, so they are generated into the MO2 mod, never committed.
The mod must sort ABOVE `SRP Enderal - Landscapes and Trees` in MO2. Re-run after any SRP update.

Usage:  python 01-generate-heights.py [--dry-run]
"""
import glob, os, re, shutil, struct, subprocess, sys, tempfile

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'SettingsApplier', 'tools', 'capture'))
import bsa  # noqa: E402

Image.MAX_IMAGE_PIXELS = None
Z = 'E:/Zenderal'
PROFILE = 'Alpha 0.5.1'
REF = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'reference', 'base')
MOD = 'Zenderal - Terrain Parallax Heights'
TEXCONV = f'{Z}/Tools/EnderalSEEdit 4.1.5f/Edit Scripts/Texconvx64.exe'
# Load order of the texture archives; later wins.
BSAS = [f'Skyrim - Textures{i}.bsa' for i in range(9)] + ['E - Textures1.bsa', 'E - Textures2.bsa', 'E - Update.bsa']
# Target height distribution, matched to Skyrim 202X Complex Terrain Parallax's landscape textures.
H_MEAN, H_STD, H_MIN, H_MAX = 110.0, 9.0, 60, 170
EXPECTED = 42  # textures needing a height map in Alpha 0.5.1 on 2026-10-11; a change means re-check


def landscape_diffuses():
    txst = {}
    for tree in ('Skyrim', 'EnderalFS', 'Update'):
        for f in glob.glob(f'{REF}/{tree}/TextureSets/*.yaml'):
            y = open(f, encoding='utf-8').read()
            fk = re.search(r'^FormKey: (\S+)', y, re.M).group(1)
            d = re.search(r'^Diffuse: (.+?)\r?$', y, re.M)
            if d:
                txst[fk] = d.group(1).strip().replace('\\', '/').lower()
    out = {}
    for tree in ('Skyrim', 'EnderalFS', 'Update'):
        for f in glob.glob(f'{REF}/{tree}/LandscapeTextures/*.yaml'):
            m = re.search(r'^TextureSet: (\S+)', open(f, encoding='utf-8').read(), re.M)
            if m and m.group(1) in txst:
                out.setdefault(txst[m.group(1)], []).append(os.path.basename(f).split(' - ')[0])
    assert out, 'no LTEX found - is reference/base serialized?'
    return out


def winners(paths, tmp):
    mods = [l[1:].strip() for l in open(f'{Z}/profiles/{PROFILE}/modlist.txt', encoding='utf-8')
            if l.startswith('+') and l[1:].strip() != MOD]
    pat = r'^(textures.)?(' + '|'.join(re.escape(p.replace('/', '\\')) for p in paths) + r')$'
    from_bsa = {}
    for b in BSAS:
        od = os.path.join(tmp, b)
        os.makedirs(od, exist_ok=True)
        for full in bsa.extract(f'{Z}/Stock Game/Data/{b}', pat, od):
            rel = full.replace('\\', '/')
            rel = rel[9:] if rel.startswith('textures/') else rel
            from_bsa[rel] = (b, os.path.join(od, os.path.basename(full)))
    res = {}
    for p in paths:
        for m in mods:
            f = f'{Z}/mods/{m}/textures/{p}'
            if os.path.isfile(f):
                res[p] = (m, f)
                break
        else:
            if p in from_bsa:
                res[p] = from_bsa[p]
    return res


def needs_height(a):
    """True when the alpha is not a height map: flat, pinned to an extreme, or a cut-out mask."""
    if a.std() < 2.0:
        return True
    return np.mean((a <= 10) | (a >= 245)) > 0.6


def blur_wrap(x, sigma):
    """Gaussian blur with wrap-around edges (the textures tile)."""
    h, w = x.shape
    fy, fx = np.fft.fftfreq(h)[:, None], np.fft.fftfreq(w)[None, :]
    g = np.exp(-2 * (np.pi * sigma) ** 2 * (fx ** 2 + fy ** 2))
    return np.real(np.fft.ifft2(np.fft.fft2(x) * g))


def make_height(rgb):
    lum = rgb[..., 0] * 0.299 + rgb[..., 1] * 0.587 + rgb[..., 2] * 0.114
    size = max(lum.shape)
    hp = lum - blur_wrap(lum, size / 32.0)     # keep stones/clods, drop large-scale tint variation
    # Complex parallax traces the height field; sharp/grainy heights trace as fuzz (Boris, ENB POM guide:
    # 'apply manual blur to the heightmap in areas where it is too sharp'). Keep only stone/clod-scale shapes.
    hp = blur_wrap(hp, max(2.0, size / 256))
    hp = (hp - hp.mean()) / (hp.std() + 1e-6)
    return np.clip(H_MEAN + H_STD * hp, H_MIN, H_MAX).round().astype(np.uint8)


def write_rgba_dds(path, rgba):
    h, w = rgba.shape[:2]
    hdr = struct.pack('<4sIIIIIII44sIIIIIIIIIIIII', b'DDS ', 124, 0x100F, h, w, w * 4, 0, 1, b'\0' * 44,
                      32, 0x41, 0, 32, 0x000000FF, 0x0000FF00, 0x00FF0000, 0xFF000000,
                      0x1000, 0, 0, 0, 0)
    with open(path, 'wb') as fh:
        fh.write(hdr + np.ascontiguousarray(rgba).tobytes())


def main():
    dry = '--dry-run' in sys.argv
    diffuses = landscape_diffuses()
    with tempfile.TemporaryDirectory() as tmp:
        win = winners(sorted(diffuses), tmp)
        todo = []
        for p, (src_name, src) in sorted(win.items()):
            a = np.asarray(Image.open(src).convert('RGBA'))[..., 3]
            if needs_height(a):
                todo.append((p, src_name, src))
        for p, s, _ in todo:
            print(f'{p}  <- {s}  ({",".join(diffuses[p])[:70]})')
        print(f'{len(todo)} textures need a height map')
        if len(todo) != EXPECTED:
            sys.exit(f'expected {EXPECTED}; the list changed - review the set above, then update EXPECTED')
        if dry:
            return
        for p, s, src in todo:
            rgba = np.array(Image.open(src).convert('RGBA'))
            rgb_before = rgba[..., :3].copy()
            rgba[..., 3] = make_height(rgba[..., :3].astype(np.float32) / 255.0)
            raw = os.path.join(tmp, 'in.dds')
            write_rgba_dds(raw, rgba)
            outdir = os.path.join(Z, 'mods', MOD, 'textures', os.path.dirname(p))
            os.makedirs(outdir, exist_ok=True)
            enc = os.path.join(tmp, 'enc')
            os.makedirs(enc, exist_ok=True)
            r = subprocess.run([TEXCONV, '-nologo', '-y', '-f', 'BC7_UNORM', '-m', '0', '-o', enc, raw],
                               capture_output=True, text=True)
            if r.returncode:
                sys.exit(f'texconv failed on {p}:\n{r.stdout}{r.stderr}')
            dst = os.path.join(outdir, os.path.basename(p))
            shutil.move(os.path.join(enc, 'in.dds'), dst)
            # Verify: alpha is now a height map, colour survived the re-encode.
            out = np.asarray(Image.open(dst).convert('RGBA'))
            assert out.shape == rgba.shape, (p, out.shape, rgba.shape)
            a = out[..., 3].astype(float)
            assert 90 < a.mean() < 130 and 4 < a.std() < 15, (p, a.mean(), a.std())
            err = np.abs(out[..., :3].astype(int) - rgb_before.astype(int)).mean()
            assert err < 4, (p, err)
            print(f'  wrote {p}  alpha {a.mean():.0f}+-{a.std():.1f}  rgb err {err:.2f}')
    print(f'done: {len(todo)} textures in mods/{MOD}')


if __name__ == '__main__':
    main()
