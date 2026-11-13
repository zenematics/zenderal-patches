"""Generate Clockwork Thunder's mesh and textures: Ordo Legionis' Nehrimese Flintlock Fucile
(OL_Musket_Rifle 002F9B) in polished Starling gold, with Starling cogs on its forestock, a cog-shaped trigger guard,
a round barrel (Ordo's is hexagonal) and a cog round the muzzle.

Inputs (the curator's installed list, nothing committed):
  rifle mesh   the WINNING loose meshes/OLM/OL_Musket/OL_Musket_Rifle_Animated.nif (Ordo Legionilis
               (Imperial Muskets)' loose copy beats Muskets of the Enderal's BSA). Same file is the
               world model and the 1st-person static OLM_1stPersonMusketRifle 002F9A.
  rifle tex    textures/olm/ol_engflintlockrifle/englishflintlockrifle_{basecolor,metallic,height}.dds
  cog          meshes/clutter/dwemer/dwecog01.nif (Enderal's own Starling cog, E - Meshes.bsa) and its
               diffuse textures/dungeons/dwemerruins/DweMetalSheet01Small.dds

Outputs, into <mods>/<target mod>/ (default Zenderal - Patch Collection):
  meshes/Zenderal/ClockworkThunder/ClockworkThunder.nif
      The rifle mesh rebuilt block by block (nifsplice; every original block byte-identical, asserted)
      with (1) the rifle's texture set pointing at the recoloured diffuse and env mask, and (2) ONE new
      NiTriShape holding all the cogs: same parent and transform as the rifle's own shape, the rifle's
      shader property copied with its own texture set (gold cog textures).
  textures/Zenderal/ClockworkThunder/ClockworkThunder_d.dds    (BC7, mips)  rifle diffuse
  textures/Zenderal/ClockworkThunder/ClockworkThunder_n.dds    (BC7, mips)  rifle normal, highlights raised on metal
  textures/Zenderal/ClockworkThunder/ClockworkThunder_m.dds    (BC7, mips)  Complex Material mask
  textures/Zenderal/ClockworkThunder/ClockworkThunderCog_d/_n/_m.dds          the same for the cogs
  textures/Zenderal/ClockworkThunder/ClockworkThunder_e.dds    gold cubemap (shared by both texture sets)

Polished gold (curator 2026-11-13, after Rise: "the gun metal shiny gold now that we have those new
cubemaps"): Rise's build-4 recipe = Precious Objects Complex Material and Dynamic Cubemap's gold, imported
from src/StingAndRise/tools/01-build-assets.py (GOLD_RAMP, SPEC level, COMPLEX, the gold chrome cubemap).
Metal (the rifle's own metallic map) -> the gold ramp by luminance; wood kept, a little darker. Ordo's
shader was type 0 without Environment_Mapping, so it never reflected at all (why the first, rusted build
read flat): every shader in our mesh is now Environment Map (type 1) with the flag and env scale ENV_SCALE.

Cog placement: in the rifle shape's own space (Z along the gun, muzzle +Z; Y up; X across, scale 0.62
to world). Each cog lies flat on one side of the gun; its inner face sits just under the lowest point of
the gun's surface under the disc and its outer face clear of the highest (so no gap shows under the rim
and the teeth stand proud). The surface is sampled from the rifle's triangles; a disc that leaves the
silhouette, or a surface that varies more than MAX_RELIEF under it, stops the build.

Tangents: computed from UVs in the convention the rifle's own NiTriShapeData uses (checked against it
on every build).

Usage:  python 01-build-assets.py [--mods <MO2 mods dir>] [--target <mod name>] [--preview <png prefix>]
"""
import argparse
import importlib.util
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE)
import nifsplice as ns  # noqa: E402

TOOLS = json.load(open(os.path.join(ROOT, '.claude', 'config', 'tools.json'), encoding='utf-8-sig'))
sys.path.insert(0, TOOLS['pynifly'])
from pyn.pynifly import NifFile  # noqa: E402

_spec = importlib.util.spec_from_file_location('_bsa', os.path.join(ROOT, 'src', 'Prophecy', 'tools', '_bsa.py'))
_bsa = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bsa)
_spec = importlib.util.spec_from_file_location('_rise', os.path.join(ROOT, 'src', 'StingAndRise', 'tools', '01-build-assets.py'))
_rise = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_rise)      # Rise's gold: GOLD_RAMP, COMPLEX, gold_cubemap, write_texture, smallest_mip

MO2 = TOOLS['modlistRoot']
DATA = TOOLS['gameDataDir']
PROFILE = 'Ultra'

RIFLE_MESH = 'meshes/OLM/OL_Musket/OL_Musket_Rifle_Animated.nif'
RIFLE_TEX = 'textures/olm/ol_engflintlockrifle/englishflintlockrifle_%s.dds'
COG_MESH = 'meshes/clutter/dwemer/dwecog01.nif'
COG_TEX = 'textures/dungeons/dwemerruins/DweMetalSheet01Small.dds'
COG_NORMAL = 'textures\\dungeons\\dwemerruins\\DweMetalSheet01Small_n.dds'
MESH_BSAS = ['E - Meshes.bsa', 'Skyrim - Meshes0.bsa', 'Skyrim - Meshes1.bsa']
TEX_BSAS = ['E - Textures1.bsa', 'E - Textures2.bsa'] + ['Skyrim - Textures%d.bsa' % k for k in range(9)]

OUT_MESH = 'meshes/Zenderal/ClockworkThunder/ClockworkThunder.nif'
OUT_D = 'textures/Zenderal/ClockworkThunder/ClockworkThunder_d.dds'
OUT_M = 'textures/Zenderal/ClockworkThunder/ClockworkThunder_m.dds'
OUT_N = 'textures/Zenderal/ClockworkThunder/ClockworkThunder_n.dds'
OUT_E = 'textures/Zenderal/ClockworkThunder/ClockworkThunder_e.dds'
OUT_COG = 'textures/Zenderal/ClockworkThunder/ClockworkThunderCog_d.dds'
OUT_COG_N = 'textures/Zenderal/ClockworkThunder/ClockworkThunderCog_n.dds'
OUT_COG_M = 'textures/Zenderal/ClockworkThunder/ClockworkThunderCog_m.dds'

COG_SHAPE_NAME = 'ClockworkThunderCogs'

# (side, Z along the gun, Y height, radius, in-plane turn in degrees), rifle shape space.
# side -1 = the lock side, +1 = the side-plate side. Big + meshing cog on each side of the butt, one on the
# wrist (lock side) / side plate, a small one on each side of the forestock.
# Curator 2026-11-13 (screenshot): the cogs belong where they make mechanical sense - a gear train on the
# forestock straight in front of the lock, as if the lock drove it. One train, mirrored on both sides; nothing
# on the butt or wrist any more. TRAIN = first cog (Z, Y, radius), then each next cog as (radius, direction in
# degrees from the previous cog's centre, 0 = towards the muzzle, 90 = up). Centres sit MESH x (r1 + r2) apart
# and each cog is turned so its teeth fall into the previous cog's gaps (meshed_turns).
# The forestock's side is a flat band y 22.3..27.2 from the lock plate's front edge (z -13) forward (surface scan
# 2026-11-13), so the train runs along it; the first, largest cog sits against the lock plate.
TRAIN_START = (-10.6, 24.8, 2.2)
TRAIN = [(1.5, -12), (1.9, 12), (1.3, -10)]
MESH = 0.9             # centre distance / (r1 + r2): teeth overlap by ~10% of the radii


def cog_train(teeth):
    z, y, r = TRAIN_START
    chain = [(z, y, r, 0.0)]
    for r2, ang in TRAIN:
        z1, y1, r1, t1 = chain[-1]
        a = math.radians(ang)
        d = MESH * (r1 + r2)
        z2, y2 = z1 + d * math.cos(a), y1 + d * math.sin(a)
        # meshing: rotation of gear 2 mirrors gear 1's about the line of centres (ratio r1/r2), plus half a
        # tooth so a tooth faces a gap; the cog's teeth start at in-plane angle 0
        t2 = -(r1 / r2) * (t1 - ang) + ang + 180.0 + 180.0 / teeth
        chain.append((z2, y2, r2, t2))
    return [(side, z, y, r, t) for side in (-1, +1) for z, y, r, t in chain]


def cog_profile(CV):
    """(teeth, angle of the first tooth's centre in degrees, hole radius / tip radius) of the cog mesh.
    Enderal's dwecog01: 6 teeth (tips 23.6, body 18.1), finger-sized hole (~9.7)."""
    ang = np.degrees(np.arctan2(CV[:, 1], CV[:, 0])) % 360
    rad = np.hypot(CV[:, 0], CV[:, 1])
    tips = np.sort(ang[rad > 0.95 * rad.max()])
    gaps = np.diff(np.concatenate([tips, tips[:1] + 360]))
    cut = np.where(gaps > 15)[0]           # a gap of more than 15 degrees separates two teeth
    teeth = len(cut)
    first = tips[(cut[0] + 1) % len(tips)]
    last = tips[cut[1 % teeth]] if teeth > 1 else tips[-1]
    centre = (first + ((last - first) % 360) / 2) % 360
    return teeth, centre, float(rad.min() / rad.max())


# Curator 2026-11-13: "make the trigger guard ... cog shaped". The guard piece is dropped from the rifle's
# triangles and the cog stands in its place round the trigger (trigger piece: z -34.1..-28.9, y 17.5..22.1).
GUARD_BOX = ((-1.6, 1.6), (11.5, 22.5), (-55.5, -18.0))   # (x, y, z) bounds the guard piece must lie in
GUARD_MIN_TRIS = 500
# Curator 2026-11-13: "on the right side where the cogs are there's a gold panel underneath, just remove it". Ordo's
# oval escutcheon on the lock side of the forestock (its own welded piece, 64 triangles, x -3.05..-2.68,
# y 24.1..25.9, z -4.5..-1.3 on the 2026-11-13 mesh) sat under the third and fourth cogs; it is dropped, and the cogs
# are seated on the stock without it. The stock's own surface runs on underneath it.
OVAL_BOX = ((-3.6, -2.0), (23.0, 27.0), (-6.0, 0.0))
OVAL_TRIS = (40, 100)
GUARD_CENTRE = (-31.5, 19.6)   # (z, y): the hole's centre, round the trigger's tip
GUARD_HOLE = 3.6               # hole radius: clears the trigger tip (5.2 long, 4.6 tall; its top is in the wood)
GUARD_THICK = 1.4              # across the gun (the old guard was 2.8 wide; curator: subtle)
GUARD_BAND = 0.9               # ring width from the hole to the rim between the teeth
GUARD_TOOTH = 0.8              # tooth height above that rim
# Round barrel (curator 2026-11-13: "make the barrel cylindrical"). Ordo's barrel is one welded hexagonal tube
# (240 triangles, every vertex on a hexagon round the bore axis, corners at 0/60/.. deg): each triangle is split
# BARREL_SPLITS times (midpoints, so the 60 deg faces become 15 deg) and every point mapped from its hexagon onto
# the circle of BARREL_K x the hexagon's corner radius (0.909 = the circle with the hexagon's area). UVs follow
# each triangle, so the texture is the barrel's own. The new barrel is its own shape on the rifle's shader.
BARREL_MIN_TRIS = 200
RIB_MIN_TRIS = 100       # the hexagonal rib between barrel and ramrod (108 triangles) is rounded too
MUZZLE_REACH = 1.5
BARREL_SPLITS = 2
BARREL_K = 0.909
BARREL_SHAPE_NAME = 'ClockworkThunderBarrel'
# Muzzle cog (curator 2026-11-13: "a cog over the hole"): dwecog01 remapped like the guard, standing across the
# barrel at its muzzle face, its hole the bore's circle, one tooth straight up. The rifle has no front-sight blade
# (the aim line runs over the muzzle top), so the top tooth reads as one; it rises about 0.4 world units over the
# muzzle, under the crosshair dot (1 deg above the muzzle = ~1.1 units at that distance).
MUZZLE_BAND = 0.55     # ring from the bore out to the rim between the teeth
MUZZLE_TOOTH = 0.45    # tooth height above that rim
MUZZLE_THICK = 0.6     # along the barrel
MUZZLE_PROUD = 0.15    # its front face this far ahead of the muzzle face
THICKNESS = 0.9        # cog thickness above the surface's highest point under it (shape units)
SINK = 0.15            # inner face this far under the surface's lowest point under the disc
MAX_RELIEF = 4.0       # surface may vary this much under a disc, else the spot is too curved
SAMPLE_STEP = 0.3      # surface sample spacing (shape units)
CELL = 0.35            # surface height under a cog vertex = highest sample within this distance

# colours (linear-ish sRGB 0..1)
WOOD_DARKEN = 0.82
METAL_SPEC = 0.85      # normal-map alpha (highlight mask) on metal: Precious's 0.63-0.88, Rise's ~0.8
WOOD_GLOSS = 0.2       # Complex Material glossiness off the metal (no reflection, no metalness there)
ENV_SCALE = 1.0        # as Rise's blade shader (Vanilla Fresnel saturates the mask)
SLSF1_ENVIRONMENT_MAPPING = 0x80
SHADER_TYPE_ENVMAP = 1


# ---- inputs ----------------------------------------------------------------------------------------------

def profile_mods():
    lines = open(os.path.join(MO2, 'profiles', PROFILE, 'modlist.txt'), encoding='utf-8').read().splitlines()
    return [l[1:] for l in lines if l.startswith('+')]


def find_ci(base, rel):
    cur = base
    for part in rel.replace('\\', '/').split('/'):
        if not os.path.isdir(cur):
            return None
        hit = [e for e in os.listdir(cur) if e.lower() == part.lower()]
        if not hit:
            return None
        cur = os.path.join(cur, hit[0])
    return cur if os.path.isfile(cur) else None


_bsa_cache = {}


def winner(mods_dir, mods, rel, bsas):
    """(source label, bytes): the highest-priority loose copy, else the first BSA that has it."""
    for mod in mods:
        p = find_ci(os.path.join(mods_dir, mod), rel)
        if p:
            return mod, open(p, 'rb').read()
    key = rel.replace('/', '\\').lower()
    for name in bsas:
        path = os.path.join(DATA, name)
        if not os.path.isfile(path):
            continue
        if name not in _bsa_cache:
            _bsa_cache[name] = _bsa.listing(path)
        data, listing = _bsa_cache[name]
        if key in listing:
            return name, _bsa.read(data, listing[key])
    sys.exit('no source for ' + rel)


def load_dds(raw):
    tmp = tempfile.NamedTemporaryFile(suffix='.dds', delete=False)
    tmp.write(raw)
    tmp.close()
    im = Image.open(tmp.name)
    im.load()
    os.remove(tmp.name)
    return im


def texconv():
    p = os.path.join(os.path.dirname(TOOLS['xedit']), 'Edit Scripts', 'Texconvx64.exe')
    assert os.path.isfile(p), p
    return p


def write_bc7(rgb_float, out_path, fmt="BC7_UNORM"):
    """rgb(a) float 0..1 array -> BC7 DDS with a full mip chain."""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    arr = np.clip(rgb_float * 255.0 + 0.5, 0, 255).astype(np.uint8)
    mode = 'RGB' if arr.ndim == 3 and arr.shape[2] == 3 else 'L'
    tmpdir = tempfile.mkdtemp()
    png = os.path.join(tmpdir, os.path.splitext(os.path.basename(out_path))[0] + '.png')
    Image.fromarray(arr, mode).save(png)
    r = subprocess.run([texconv(), '-nologo', '-y', '-f', fmt, '-m', '0', '-o', tmpdir, png],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    dds = png[:-4] + '.dds'
    shutil.move(dds, out_path)
    os.remove(png)
    os.rmdir(tmpdir)


# ---- recolour --------------------------------------------------------------------------------------------

def fbm(h, w, seed, octaves=6, base=8):
    """Fractal value noise 0..1, tileable enough for a weapon atlas."""
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, total = 1.0, 0.0
    for o in range(octaves):
        n = base * (2 ** o)
        grid = rng.random((n + 1, n + 1)).astype(np.float32)
        im = Image.fromarray((grid * 65535).astype(np.uint16).astype(np.int32), 'I').resize((w, h), Image.BICUBIC)
        out += amp * (np.asarray(im, np.float32) / 65535.0)
        total += amp
        amp *= 0.55
    out /= total
    lo, hi = np.percentile(out, 1), np.percentile(out, 99)
    return np.clip((out - lo) / (hi - lo), 0, 1)


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def polished_gold(rgb, metal, normal, label):
    """rgb HxWx3, metal HxW 0..1 (weight), normal HxWx4 (alpha = highlight mask). Rise's recipe (see the
    docstring): returns (diffuse RGB, normal RGBA, Complex Material mask RGBA)."""
    on = metal > 0.5
    lum = (rgb * np.array([0.299, 0.587, 0.114])).sum(-1)
    lo, hi = np.percentile(lum[on], [5, 95])
    gold = _rise.ramp(np.clip((lum - lo) / max(hi - lo, 1e-3), 0, 1), _rise.GOLD_RAMP)
    out = rgb * WOOD_DARKEN * (1 - metal[..., None]) + gold * metal[..., None]
    n = normal.copy()
    n[..., 3] = METAL_SPEC * metal + normal[..., 3] * (1 - metal)
    cm = np.stack([_rise.COMPLEX[0] * metal,                       # R: reflects
                   _rise.COMPLEX[1] * metal + WOOD_GLOSS * (1 - metal),   # G: glossiness
                   _rise.COMPLEX[2] * metal,                       # B: metalness
                   np.zeros_like(metal)], -1)                      # A: no parallax (and marks it complex)
    print('%s gold: %d%% metal, luminance %.2f..%.2f onto the gold ramp, diffuse mean on metal %s'
          % (label, 100 * metal.mean(), lo, hi, ' '.join('%.2f' % v for v in out[on].mean(0))))
    return np.clip(out, 0, 1), np.clip(n, 0, 1), cm


def write_complex_mask(cm, path):
    """Bottled Shaders' own test on the 1x1 mip it samples: alpha below 1 - eps and not grey (Rise's checks)."""
    _rise.write_texture(cm, path, 'BC7_UNORM')
    mip = _rise.smallest_mip(path)
    eps = 4.0 / 255.0
    assert mip[3] < 1 - eps, 'alpha lost: the mask would not be complex (%s)' % mip
    assert max(abs(mip[0] - mip[1]), abs(mip[0] - mip[2]), abs(mip[1] - mip[2])) >= 2 * eps, \
        'grey 1x1 mip %s: Bottled Shaders would read a plain env mask' % mip
    print('complex mask %s: 1x1 mip %s' % (os.path.basename(path), ' '.join('%.3f' % v for v in mip)))


def make_envmapped(b):
    """BSLightingShaderProperty (BS 83) of type 0 -> Environment Map (type 1): the type, the SLSF1 flag, and
    the type's trailing env-map scale. Layout after the texture-set ref: emissive colour 12, emissive mult 4,
    clamp 4, alpha 4, refraction 4, glossiness 4, specular colour 12, specular strength 4, lighting effects 8."""
    t = ns.shader_texset_offset(b)
    assert struct.unpack_from('<I', b, 0)[0] == 0 and len(b) == t + 60, ('not a plain type-0 shader', len(b), t)
    f1 = 8 + 4 * struct.unpack_from('<I', b, 8)[0] + 4 + 4
    out = bytearray(b)
    struct.pack_into('<I', out, 0, SHADER_TYPE_ENVMAP)
    struct.pack_into('<I', out, f1, struct.unpack_from('<I', out, f1)[0] | SLSF1_ENVIRONMENT_MAPPING)
    return out + struct.pack('<f', ENV_SCALE)


# ---- geometry --------------------------------------------------------------------------------------------

def tri_normals(V, T):
    n = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    return n / np.maximum(ln, 1e-12)


def uv_derivatives(V, UV, T):
    """Per-vertex dP/du and dP/dv, area-weighted, orthogonalised against nothing (raw)."""
    du = np.zeros_like(V)
    dv = np.zeros_like(V)
    p0, p1, p2 = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    t0, t1, t2 = UV[T[:, 0]], UV[T[:, 1]], UV[T[:, 2]]
    e1, e2 = p1 - p0, p2 - p0
    a1, a2 = t1 - t0, t2 - t0
    det = a1[:, 0] * a2[:, 1] - a2[:, 0] * a1[:, 1]
    ok = np.abs(det) > 1e-12
    r = np.where(ok, 1.0 / np.where(ok, det, 1), 0)[:, None]
    dpdu = (e1 * a2[:, 1:2] - e2 * a1[:, 1:2]) * r
    dpdv = (e2 * a1[:, 0:1] - e1 * a2[:, 0:1]) * r
    for k in range(3):
        np.add.at(du, T[:, k], dpdu)
        np.add.at(dv, T[:, k], dpdv)
    return du, dv


def ortho(vec, N):
    v = vec - (vec * N).sum(1, keepdims=True) * N
    ln = np.linalg.norm(v, axis=1, keepdims=True)
    return v / np.maximum(ln, 1e-12)


def tangent_convention(d):
    """Which UV derivative the NIF's 'tangents' / 'bitangents' arrays hold, read off the rifle itself.
    Returns (tangent_is, tangent_sign, bitangent_is, bitangent_sign) with *_is in {'du', 'dv'}."""
    V = np.array(d['verts'])
    N = np.array(d['normals'])
    UV = np.array(d['uvs'])
    T = np.array(d['tris'])
    du, dv = uv_derivatives(V, UV, T)
    du, dv = ortho(du, N), ortho(dv, N)
    st = np.array(d['tangents'])
    sb = np.array(d['bitangents'])
    res = []
    for stored in (st, sb):
        best = None
        for name, ref in (('du', du), ('dv', dv)):
            dot = (stored * ref).sum(1)
            good = np.linalg.norm(ref, axis=1) > 0.5
            m = float(np.median(dot[good]))
            if best is None or abs(m) > abs(best[2]):
                best = (name, 1 if m > 0 else -1, m)
        assert abs(best[2]) > 0.9, ('tangent convention unclear', best)
        res.append(best)
    return res[0][0], res[0][1], res[1][0], res[1][1]


def surface_samples(V, T, sign):
    """Points densely sampled on the rifle's triangles that face the given side (X sign)."""
    N = tri_normals(V, T)
    face = N[:, 0] * sign > 0.2
    P0, P1, P2 = V[T[face, 0]], V[T[face, 1]], V[T[face, 2]]
    # about one sample every SAMPLE_STEP along a triangle's longest edge (the forestock is long thin triangles)
    edge = np.max([np.linalg.norm(P1 - P0, axis=1), np.linalg.norm(P2 - P1, axis=1),
                   np.linalg.norm(P0 - P2, axis=1)], axis=0)
    ks = np.clip(np.ceil(edge / SAMPLE_STEP), 6, 160).astype(int)
    pts = []
    for k in np.unique(ks):
        sel = ks == k
        A, B, C = P0[sel], P1[sel], P2[sel]
        for a in range(k + 1):
            for b in range(k + 1 - a):
                u, v = a / k, b / k
                pts.append(A * (1 - u - v) + B * u + C * v)
    return np.concatenate(pts)


def place_cog(cog, samples, side, z, y, r, turn_deg):
    """Cog verts/normals/tris placed on the rifle (shape space). cog = (V, N, T) in its own XY plane."""
    CV, CN, CT = cog
    rad = np.max(np.linalg.norm(CV[:, :2], axis=1))
    k = r / rad
    # surface under the disc: outwardness = X * side
    d = np.hypot(samples[:, 2] - z, samples[:, 1] - y)
    under = samples[d <= r]
    assert len(under) > 200, ('cog leaves the gun', side, z, y, r, len(under))
    # disc coverage: every ring sector must have surface under it
    ang = np.arctan2(under[:, 1] - y, under[:, 2] - z)
    rr = np.hypot(under[:, 2] - z, under[:, 1] - y)
    for a0 in np.linspace(-math.pi, math.pi, 12, endpoint=False):
        sel = (ang >= a0) & (ang < a0 + math.pi / 6) & (rr > 0.7 * r)
        assert sel.sum() > 3, ('cog overhangs the silhouette', side, z, y, r, a0)
    out_w = under[:, 0] * side
    zmin, zmax = CV[:, 2].min(), CV[:, 2].max()
    tz = (THICKNESS + SINK) / (zmax - zmin)
    t = math.radians(turn_deg)
    c, s = math.cos(t), math.sin(t)
    # cog local (x, y, zc): in-plane turn, then x -> gun Z, y -> gun Y, zc -> outward. The cog is bent onto the
    # gun: each vertex rides on the surface height under it (the highest sample within CELL), like an inlay.
    rx = CV[:, 0] * c - CV[:, 1] * s
    ry = CV[:, 0] * s + CV[:, 1] * c
    gy, gz = y + ry * k, z + rx * k
    surf = np.empty(len(CV))
    for i in range(len(CV)):
        dd = np.hypot(under[:, 1] - gy[i], under[:, 2] - gz[i])
        near = dd < CELL
        surf[i] = out_w[near].max() if near.any() else out_w[np.argmin(dd)]
    # a cell holding only hidden inner faces (the forestock's barrel channel, the lock's inside) reads far below
    # the visible surface; such cells take the disc's median instead
    med = float(np.median(surf))
    holes = surf < med - 0.6
    surf[holes] = med
    lo, hi = float(surf.min()), float(surf.max())
    assert hi - lo <= MAX_RELIEF, ('surface too curved under cog', side, z, y, r, hi - lo)
    P = np.stack([side * (surf - SINK + (CV[:, 2] - zmin) * tz), gy, gz], axis=1)
    M = np.array([[0, 0, side * tz], [s * k, c * k, 0], [c * k, -s * k, 0]], float)
    tris = CT.copy()
    if np.linalg.det(M) < 0:
        tris = tris[:, [0, 2, 1]]
    # normals from the bent mesh (the cog's vertices are already split at its hard edges)
    PN = np.zeros_like(P)
    fn_raw = np.cross(P[tris[:, 1]] - P[tris[:, 0]], P[tris[:, 2]] - P[tris[:, 0]])
    for kk in range(3):
        np.add.at(PN, tris[:, kk], fn_raw)
    PN /= np.maximum(np.linalg.norm(PN, axis=1, keepdims=True), 1e-12)
    # same split structure as the source: a vertex's new normal must stay near its transformed original
    ref = CN @ np.linalg.inv(M)
    ref /= np.linalg.norm(ref, axis=1, keepdims=True)
    agree = (PN * ref).sum(1)
    assert np.median(agree) > 0.9, ('bent normals disagree with the cog', float(np.median(agree)))
    # sanity: the face normal of the outer face points outward
    fn = tri_normals(P, tris)
    outward = (fn[:, 0] * side > 0.9).sum()
    assert outward > len(tris) * 0.2, ('cog faces inward', side, z, y)
    return P, PN, tris, (lo, hi)


def piece_in_box(V, T, box, tris_range, label):
    """Indices of the one position-welded piece of the rifle mesh lying wholly inside box, with a triangle count
    in tris_range."""
    comp = components(V, T)
    (x0, x1), (y0, y1), (z0, z1) = box
    hits = []
    for c in np.unique(comp):
        n = int((comp == c).sum())
        if not tris_range[0] <= n <= tris_range[1]:
            continue
        pv = V[np.unique(T[comp == c])]
        lo, hi = pv.min(0), pv.max(0)
        if lo[0] >= x0 and hi[0] <= x1 and lo[1] >= y0 and hi[1] <= y1 and lo[2] >= z0 and hi[2] <= z1:
            hits.append(c)
    assert len(hits) == 1, (label + ' not found uniquely', hits)
    return np.where(comp == hits[0])[0]


def guard_triangles(V, T):
    """Indices of the trigger guard's triangles: the position-welded piece of the rifle mesh that lies in
    GUARD_BOX (bounds z -54.9..-18.5, y 11.9..22.1, x +-1.4 on the 2026-11-13 mesh: loop + rear scroll)."""
    key = {}
    wid = np.array([key.setdefault(tuple(np.round(v, 3)), i) for i, v in enumerate(V)])
    parent = list(range(len(V)))

    def f(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for tr in T:
        a = f(wid[tr[0]])
        for k in (1, 2):
            b = f(wid[tr[k]])
            parent[b] = a
    comp = np.array([f(wid[tr[0]]) for tr in T])
    (x0, x1), (y0, y1), (z0, z1) = GUARD_BOX
    hits = []
    for c in np.unique(comp):
        pv = V[np.unique(T[comp == c])]
        lo, hi = pv.min(0), pv.max(0)
        if lo[0] >= x0 and hi[0] <= x1 and lo[1] >= y0 and hi[1] <= y1 and lo[2] >= z0 and hi[2] <= z1                 and (comp == c).sum() > GUARD_MIN_TRIS:
            hits.append(c)
    assert len(hits) == 1, ('trigger guard not found uniquely', hits)
    return np.where(comp == hits[0])[0]


def guard_cog(cog, hole, tooth0):
    """The cog standing in the gun's side plane round the trigger, as the trigger guard: centred on X = 0,
    GUARD_THICK thick, one tooth pointing straight down. Curator 2026-11-13 ("thinner, subtle"): the cog is
    remapped radially, piecewise linear: its finger hole -> GUARD_HOLE, its body rim -> + GUARD_BAND, its tooth
    tips -> + GUARD_TOOTH, so the ring is a thin band with short teeth instead of the cog's broad disc."""
    CV, CN, CT = cog
    H, B, T = GUARD_HOLE, GUARD_HOLE + GUARD_BAND, GUARD_HOLE + GUARD_BAND + GUARD_TOOTH
    x, y = remap_cog_radii(CV, H, B, T)
    zmin, zmax = CV[:, 2].min(), CV[:, 2].max()
    tz = GUARD_THICK / (zmax - zmin)
    t = math.radians(-90.0 - tooth0)
    c, s = math.cos(t), math.sin(t)
    gz, gy = GUARD_CENTRE
    rx, ry = x * c - y * s, x * s + y * c
    P = np.stack([(CV[:, 2] - (zmin + zmax) / 2) * tz, gy + ry, gz + rx], axis=1)
    M = np.array([[0, 0, tz], [s, c, 0], [c, -s, 0]], float)
    tris = CT.copy()
    if np.linalg.det(M) < 0:
        tris = tris[:, [0, 2, 1]]
    # normals from the remapped mesh (its vertices are split at the hard edges)
    PN = np.zeros_like(P)
    fn_raw = np.cross(P[tris[:, 1]] - P[tris[:, 0]], P[tris[:, 2]] - P[tris[:, 0]])
    for kk in range(3):
        np.add.at(PN, tris[:, kk], fn_raw)
    PN /= np.maximum(np.linalg.norm(PN, axis=1, keepdims=True), 1e-12)
    print('guard cog: hole %.1f, band to %.1f, tips %.1f, %.1f thick; z %.1f..%.1f, y %.1f..%.1f'
          % (H, B, T, GUARD_THICK, P[:, 2].min(), P[:, 2].max(), P[:, 1].min(), P[:, 1].max()))
    return P, PN, tris


def components(V, T):
    """Per-triangle id of the position-welded piece it belongs to."""
    key = {}
    wid = np.array([key.setdefault(tuple(np.round(v, 3)), i) for i, v in enumerate(V)])
    parent = list(range(len(V)))

    def f(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for tr in T:
        a = f(wid[tr[0]])
        for k in (1, 2):
            parent[f(wid[tr[k]])] = a
    return np.array([f(wid[tr[0]]) for tr in T])


def hex_factor(theta):
    """Radius of a unit-corner hexagon (corners at multiples of 60 deg) at angle theta (radians)."""
    a = np.mod(theta, math.pi / 3) - math.pi / 6
    return math.cos(math.pi / 6) / np.cos(a)


def barrel_triangles(V, T):
    """The hexagonal tubes along the muzzle: every welded piece of >= BARREL_MIN_TRIS (or the 108-triangle rib under
    the barrel, >= RIB_MIN_TRIS) that reaches within MUZZLE_REACH of the mesh's max Z and has every vertex on a
    hexagon round its own axis (the round ramrod does not). Returns [(triangle indices, axis (x, y))], the barrel
    (the piece reaching the max Z) first."""
    comp = components(V, T)
    zmax = V[:, 2].max()
    out = []
    for c in np.unique(comp):
        tris = np.where(comp == c)[0]
        P = V[np.unique(T[tris])]
        if len(tris) < RIB_MIN_TRIS or P[:, 2].max() < zmax - MUZZLE_REACH:
            continue
        ax = np.array([(P[:, 0].max() + P[:, 0].min()) / 2, (P[:, 1].max() + P[:, 1].min()) / 2])
        d = P[:, :2] - ax
        keep = np.hypot(d[:, 0], d[:, 1]) > 1e-3
        ang = np.degrees(np.arctan2(d[keep, 1], d[keep, 0]))
        off = np.abs(np.mod(ang + 180, 60))
        off = np.minimum(off, 60 - off)
        if off.max() < 1.0:
            out.append((abs(P[:, 2].max() - zmax) < 0.01 and len(tris) >= BARREL_MIN_TRIS, tris, ax))
    out.sort(key=lambda o: not o[0])
    assert out and out[0][0] and sum(o[0] for o in out) == 1, ('barrel not found uniquely', [len(o[1]) for o in out])
    return [(tris, ax) for _, tris, ax in out]


def round_barrel(V, T, UV, tris, ax):
    """New (V, N, T, UV) for the barrel: split, mapped onto circles, normals smoothed within 45 deg."""
    pts, uvs = [], []
    for t in T[tris]:
        tri_list = [[(V[i], UV[i]) for i in t]]
        for _ in range(BARREL_SPLITS):
            nxt = []
            for a, b, c in tri_list:
                ab = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
                bc = ((b[0] + c[0]) / 2, (b[1] + c[1]) / 2)
                ca = ((c[0] + a[0]) / 2, (c[1] + a[1]) / 2)
                nxt += [[a, ab, ca], [ab, b, bc], [ca, bc, c], [ab, bc, ca]]
            tri_list = nxt
        for tri in tri_list:
            for pp, uu in tri:
                pts.append(pp)
                uvs.append(uu)
    P = np.array(pts, float)
    UVn = np.array(uvs, float)
    d = P[:, :2] - ax
    rho = np.hypot(d[:, 0], d[:, 1])
    th = np.arctan2(d[:, 1], d[:, 0])
    rn = BARREL_K * rho / hex_factor(th)
    P[:, 0] = ax[0] + rn * np.cos(th)
    P[:, 1] = ax[1] + rn * np.sin(th)
    TT = np.arange(len(P)).reshape(-1, 3)
    fn = tri_normals(P, TT)
    # normals smoothed over welded positions, only between faces within 45 deg (muzzle and breech steps stay hard)
    key = {}
    wid = np.array([key.setdefault(tuple(np.round(p, 4)), i) for i, p in enumerate(P)])
    acc = {}
    for k in range(len(P)):
        acc.setdefault(wid[k], []).append(k // 3)
    N = np.zeros_like(P)
    for k in range(len(P)):
        own = fn[k // 3]
        fs = fn[acc[wid[k]]]
        fs = fs[fs @ own > math.cos(math.radians(45))]
        n = fs.sum(0)
        N[k] = n / max(np.linalg.norm(n), 1e-12)
    # weld identical (position, uv, normal) corners
    uniq = {}
    idx = np.array([uniq.setdefault((tuple(np.round(P[k], 4)), tuple(np.round(UVn[k], 5)),
                                     tuple(np.round(N[k], 3))), len(uniq)) for k in range(len(P))])
    first = np.zeros(len(uniq), int)
    first[idx[::-1]] = np.arange(len(P))[::-1]
    TT = idx.reshape(-1, 3)
    TT = TT[(TT[:, 0] != TT[:, 1]) & (TT[:, 1] != TT[:, 2]) & (TT[:, 0] != TT[:, 2])]
    out_r = np.hypot(P[first][:, 0] - ax[0], P[first][:, 1] - ax[1])
    print('round barrel: %d -> %d triangles, %d verts; radius %.2f..%.2f (hexagon corners were %.2f..%.2f)'
          % (len(tris), len(TT), len(first), out_r[out_r > 0.01].min(), out_r.max(), rho[rho > 0.01].min(),
             rho.max()))
    return P[first], N[first], TT, UVn[first]


def remap_cog_radii(CV, H, B, T):
    """dwecog01 remapped radially, piecewise linear: finger hole -> H, body rim -> B, tooth tips -> T.
    Returns (x, y) of the remapped disc (its thickness axis Z untouched)."""
    r = np.linalg.norm(CV[:, :2], axis=1)
    h0, t0 = r.min(), r.max()
    b0 = r[r < 0.9 * t0].max()                  # the body rim between the teeth (18.1 of 23.6 on dwecog01)
    assert h0 < b0 < t0, (h0, b0, t0)
    rn = np.where(r <= h0 + 1e-6, H * r / h0,
                  np.where(r <= b0, H + (r - h0) / (b0 - h0) * (B - H), B + (r - b0) / (t0 - b0) * (T - B)))
    scale = rn / np.maximum(r, 1e-9)
    return CV[:, 0] * scale, CV[:, 1] * scale


def muzzle_cog(cog, tooth0, ax, bore, zface):
    """The cog standing across the barrel at the muzzle: its disc in X/Y round the bore axis, hole = the bore,
    one tooth straight up (+Y), front face MUZZLE_PROUD ahead of the muzzle face."""
    CV, CN, CT = cog
    H = bore
    B, T = H + MUZZLE_BAND, H + MUZZLE_BAND + MUZZLE_TOOTH
    x, y = remap_cog_radii(CV, H, B, T)
    t = math.radians(90.0 - tooth0)
    c, s = math.cos(t), math.sin(t)
    zmin, zmax = CV[:, 2].min(), CV[:, 2].max()
    tz = MUZZLE_THICK / (zmax - zmin)
    P = np.stack([ax[0] + x * c - y * s, ax[1] + x * s + y * c,
                  zface + MUZZLE_PROUD - (zmax - CV[:, 2]) * tz], axis=1)
    tris = CT.copy()
    PN = np.zeros_like(P)
    fn_raw = np.cross(P[tris[:, 1]] - P[tris[:, 0]], P[tris[:, 2]] - P[tris[:, 0]])
    for kk in range(3):
        np.add.at(PN, tris[:, kk], fn_raw)
    PN /= np.maximum(np.linalg.norm(PN, axis=1, keepdims=True), 1e-12)
    print('muzzle cog: hole %.2f, band to %.2f, tips %.2f, %.2f thick, z %.2f..%.2f'
          % (H, B, T, MUZZLE_THICK, P[:, 2].min(), P[:, 2].max()))
    return P, PN, tris


# ---- preview ---------------------------------------------------------------------------------------------

def preview(prefix, layers):
    """Side views (lock side, plate side): painter's algorithm over (V, T, UV, texture) layers."""
    SC = 8
    for side, sign in (('lock', -1), ('plate', 1)):
        img = Image.new('RGB', (180 * SC, 40 * SC), (38, 40, 52))
        from PIL import ImageDraw
        dr = ImageDraw.Draw(img)
        items = []
        for V, T, UV, tex in layers:
            W, H = tex.size
            px = tex.load()
            depth = V[T].mean(1)[:, 0] * sign
            fn = tri_normals(V, T)
            for i in range(len(T)):
                u = UV[T[i]].mean(0)
                col = px[int(u[0] % 1 * (W - 1)), int(u[1] % 1 * (H - 1))]
                shade = 0.55 + 0.45 * max(0.0, fn[i, 0] * sign * 0.7 + fn[i, 1] * 0.3)
                col = tuple(int(c * shade) for c in col[:3])
                items.append((depth[i], [((V[j, 2] + 84) * SC, (36 - V[j, 1]) * SC) for j in T[i]], col))
        items.sort(key=lambda it: it[0])
        for _, pts, col in items:
            dr.polygon(pts, fill=col)
        img.save('%s_%s.png' % (prefix, side))


# ---- main ------------------------------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mods', default=os.path.join(MO2, 'mods'))
    ap.add_argument('--target', default='Zenderal - Patch Collection')
    ap.add_argument('--preview', default=None)
    ap.add_argument('--out-root', default=None, help='write here instead of <mods>/<target> (dry run)')
    args = ap.parse_args()
    mods = profile_mods()
    out_root = args.out_root or os.path.join(args.mods, args.target)
    assert os.path.isdir(out_root), out_root

    src, raw = winner(args.mods, mods, RIFLE_MESH, MESH_BSAS)
    print('rifle mesh from', src)
    nif = ns.Nif(raw)
    assert nif.tobytes() == raw, 'nifsplice round trip'
    shapes = nif.find('NiTriShape')
    assert len(shapes) == 1, shapes
    sh = shapes[0]
    fo = ns.trishape_fields(nif.blocks[sh])
    data_i = struct.unpack_from('<i', nif.blocks[sh], fo['data'])[0]
    shader_i = struct.unpack_from('<i', nif.blocks[sh], fo['shader'])[0]
    texset_i = struct.unpack_from('<i', nif.blocks[shader_i], ns.shader_texset_offset(nif.blocks[shader_i]))[0]
    assert nif.btype(data_i) == 'NiTriShapeData' and nif.btype(texset_i) == 'BSShaderTextureSet'
    root = nif.roots[0]
    _, kids = ns.node_children(nif.blocks[root])
    assert sh in kids, 'rifle shape is not a child of the root'
    rd = ns.read_trishape_data(nif.blocks[data_i])
    RV, RT, RUV = np.array(rd['verts']), np.array(rd['tris']), np.array(rd['uvs'])
    drop = guard_triangles(RV, RT)
    keep = np.setdiff1d(np.arange(len(RT)), drop)
    print('trigger guard: %d of %d rifle triangles dropped' % (len(drop), len(RT)))
    RT = RT[keep]
    oval = piece_in_box(RV, RT, OVAL_BOX, OVAL_TRIS, 'lock-side oval escutcheon')
    print('oval escutcheon under the cogs: %d rifle triangles dropped' % len(oval))
    RT = RT[np.setdiff1d(np.arange(len(RT)), oval)]
    tubes = barrel_triangles(RV, RT)
    btris, bax = tubes[0]
    bP = RV[np.unique(RT[btris])]
    bd = np.hypot(bP[:, 0] - bax[0], bP[:, 1] - bax[1])
    bzface = float(bP[:, 2].max())
    bore = BARREL_K * float(bd[np.abs(bP[:, 2] - bzface) < 0.02].min())
    print('barrel axis (%.2f, %.2f), muzzle face z %.2f, bore radius %.2f; %d hexagonal tube(s)'
          % (bax[0], bax[1], bzface, bore, len(tubes)))
    BV, BN, BT, BUV = [], [], [], []
    for tris_, ax_ in tubes:
        v_, n_, t_, uv_ = round_barrel(RV, RT, RUV, tris_, ax_)
        BT.append(t_ + sum(len(x) for x in BV))
        BV.append(v_)
        BN.append(n_)
        BUV.append(uv_)
    BV, BN, BT, BUV = np.concatenate(BV), np.concatenate(BN), np.concatenate(BT), np.concatenate(BUV)
    RT_SURF = RT          # the cogs sit on the rifle as it was (old barrel included)
    RT = RT[np.setdiff1d(np.arange(len(RT)), np.concatenate([t for t, _ in tubes]))]
    nif.blocks[data_i] = bytearray(ns.replace_triangles(nif.blocks[data_i], RT.tolist()))
    conv = tangent_convention(rd)
    print('tangent convention (tangents, bitangents):', conv)

    # ---- textures
    tex = {}
    for k in ('basecolor', 'metallic', 'height'):
        s, b = winner(args.mods, mods, RIFLE_TEX % k, TEX_BSAS)
        print('rifle', k, 'from', s)
        tex[k] = load_dds(b)
    base = np.asarray(tex['basecolor'].convert('RGB'), np.float32) / 255.0
    size = base.shape[1], base.shape[0]
    metal = np.asarray(tex['metallic'].convert('L').resize(size, Image.BILINEAR), np.float32) / 255.0
    height = np.asarray(tex['height'].convert('L').resize(size, Image.BILINEAR), np.float32) / 255.0
    s, b = winner(args.mods, mods, RIFLE_TEX % 'normal', TEX_BSAS)
    print('rifle normal from', s)
    rnorm = _rise.load_image(b)
    assert rnorm.shape[:2] == base.shape[:2], (rnorm.shape, base.shape)
    rgb, rnorm, cm = polished_gold(base, metal, rnorm, 'rifle')
    write_bc7(rgb, os.path.join(out_root, OUT_D))
    _rise.write_texture(rnorm, os.path.join(out_root, *OUT_N.split('/')), 'BC7_UNORM')
    write_complex_mask(cm, os.path.join(out_root, *OUT_M.split('/')))
    s, b = winner(args.mods, mods, COG_TEX, TEX_BSAS)
    print('cog texture from', s)
    cogtex = np.asarray(load_dds(b).convert('RGB'), np.float32) / 255.0
    s, b = winner(args.mods, mods, COG_NORMAL.replace('\\', '/'), TEX_BSAS)
    print('cog normal from', s)
    cognorm = _rise.load_image(b)
    cogtex = np.asarray(Image.fromarray((cogtex * 255).astype(np.uint8)).resize(cognorm.shape[1::-1], Image.BILINEAR),
                        np.float32) / 255.0
    cog_rgb, cognorm, cog_cm = polished_gold(cogtex, np.ones(cogtex.shape[:2], np.float32), cognorm, 'cog')
    write_bc7(cog_rgb, os.path.join(out_root, OUT_COG))
    _rise.write_texture(cognorm, os.path.join(out_root, *OUT_COG_N.split('/')), 'BC7_UNORM')
    write_complex_mask(cog_cm, os.path.join(out_root, *OUT_COG_M.split('/')))
    src_e, raw_e = winner(args.mods, [], _rise.CHROME_CUBEMAP, _rise.CHROME_BSAS)   # Bethesda's, never a replacer's
    print('chrome cubemap from', src_e)
    _rise.gold_cubemap(raw_e, os.path.join(out_root, *OUT_E.split('/')))

    # ---- cogs
    s, b = winner(args.mods, mods, COG_MESH, MESH_BSAS)
    print('cog mesh from', s)
    tmp = tempfile.NamedTemporaryFile(suffix='.nif', delete=False)
    tmp.write(b)
    tmp.close()
    cn = NifFile(tmp.name)
    assert len(cn.shapes) == 1
    cs = cn.shapes[0]
    CV = np.array(cs.verts, float)
    CN = np.array(cs.normals, float)
    CT = np.array(cs.tris, int)
    CUV = np.array(cs.uvs, float)
    ctx = cs.transform
    assert abs(ctx.scale - 1) < 1e-6 and np.allclose(np.array(ctx.translation), 0), 'cog shape transform'
    del cn
    os.remove(tmp.name)
    CV -= CV.mean(0) * np.array([1, 1, 0])
    CV[:, 2] -= (CV[:, 2].max() + CV[:, 2].min()) / 2

    samples = {s_: surface_samples(RV, RT_SURF, s_) for s_ in (-1, 1)}
    AV, AN, AT, AUV = [], [], [], []
    teeth, tooth0, hole = cog_profile(CV)
    print('cog: %d teeth, first tooth at %.1f deg, hole %.2f of the tip radius' % (teeth, tooth0, hole))
    assert 4 <= teeth <= 40 and 0.2 < hole < 0.6, (teeth, hole)
    for side, z, y, r, turn in cog_train(teeth):
        P, PN, tris, (lo, hi) = place_cog((CV, CN, CT), samples[side], side, z, y, r, turn)
        print('cog side %+d at z %.1f y %.1f r %.1f: surface %.2f..%.2f' % (side, z, y, r, lo, hi))
        AT.append(tris + sum(len(v) for v in AV))
        AV.append(P)
        AN.append(PN)
        AUV.append(CUV)
    for P, PN, tris in (guard_cog((CV, CN, CT), hole, tooth0),
                        muzzle_cog((CV, CN, CT), tooth0, bax, bore, bzface)):
        AT.append(tris + sum(len(v) for v in AV))
        AV.append(P)
        AN.append(PN)
        AUV.append(CUV)
    V = np.concatenate(AV)
    N = np.concatenate(AN)
    T = np.concatenate(AT)
    UV = np.concatenate(AUV)
    assert len(V) < 65535
    du, dv = uv_derivatives(V, UV, T)
    der = {'du': ortho(du, N), 'dv': ortho(dv, N)}
    tan = der[conv[0]] * conv[1]
    bit = der[conv[2]] * conv[3]
    center = (V.min(0) + V.max(0)) / 2
    radius = float(np.linalg.norm(V - center, axis=1).max())

    # ---- mesh
    rifle_set = ns.read_texture_set(nif.blocks[texset_i])
    print('rifle texture set was', rifle_set)
    nif.blocks[texset_i] = bytearray(ns.texture_set(
        [OUT_D.replace('/', '\\'), OUT_N.replace('/', '\\')] + rifle_set[2:4] +
        [OUT_E.replace('/', '\\'), OUT_M.replace('/', '\\')] + rifle_set[6:]))
    nif.blocks[shader_i] = make_envmapped(nif.blocks[shader_i])   # before the cog/barrel copies are taken
    old = ns.read_texture_set(nif.blocks[texset_i])
    assert old[0].endswith('ClockworkThunder_d.dds') and old[5].endswith('ClockworkThunder_m.dds'), old
    cog_texset = nif.add_block('BSShaderTextureSet', ns.texture_set(
        [OUT_COG.replace('/', '\\'), OUT_COG_N.replace('/', '\\'), '', '', OUT_E.replace('/', '\\'),
         OUT_COG_M.replace('/', '\\')] + [''] * (len(rifle_set) - 6)))
    shader = bytearray(nif.blocks[shader_i])
    struct.pack_into('<i', shader, ns.shader_texset_offset(shader), cog_texset)
    cog_shader = nif.add_block('BSLightingShaderProperty', shader)
    cog_data = nif.add_block('NiTriShapeData', ns.trishape_data(
        V.tolist(), N.tolist(), tan.tolist(), bit.tolist(), UV.tolist(), T.tolist(), center.tolist(), radius))
    shape = bytearray(nif.blocks[sh])
    struct.pack_into('<I', shape, fo['name'], nif.add_string(COG_SHAPE_NAME))
    struct.pack_into('<i', shape, fo['data'], cog_data)
    struct.pack_into('<i', shape, fo['shader'], cog_shader)
    cog_shape = nif.add_block('NiTriShape', shape)
    # the round barrel: a copy of the rifle's shape with its own data, and its OWN copies of the rifle's shader
    # property and texture set (same textures). Sharing the rifle's shader block froze the game on equip
    # (curator 2026-11-13); the cog shape, which never shared one, equipped fine.
    du, dv = uv_derivatives(BV, BUV, BT)
    bder = {'du': ortho(du, BN), 'dv': ortho(dv, BN)}
    bcenter = (BV.min(0) + BV.max(0)) / 2
    barrel_data = nif.add_block('NiTriShapeData', ns.trishape_data(
        BV.tolist(), BN.tolist(), (bder[conv[0]] * conv[1]).tolist(), (bder[conv[2]] * conv[3]).tolist(),
        BUV.tolist(), BT.tolist(), bcenter.tolist(), float(np.linalg.norm(BV - bcenter, axis=1).max())))
    bshape = bytearray(nif.blocks[sh])
    struct.pack_into('<I', bshape, fo['name'], nif.add_string(BARREL_SHAPE_NAME))
    struct.pack_into('<i', bshape, fo['data'], barrel_data)
    barrel_texset = nif.add_block('BSShaderTextureSet', bytes(nif.blocks[texset_i]))
    bshader = bytearray(nif.blocks[shader_i])
    struct.pack_into('<i', bshader, ns.shader_texset_offset(bshader), barrel_texset)
    struct.pack_into('<i', bshape, fo['shader'], nif.add_block('BSLightingShaderProperty', bshader))
    barrel_shape = nif.add_block('NiTriShape', bshape)
    at = kids.index(sh) + 1
    nif.blocks[root] = ns.set_children(nif.blocks[root], kids[:at] + [barrel_shape, cog_shape] + kids[at:])
    out = nif.tobytes()
    # read back: our parser, then PyNifly (an independent reader)
    back = ns.Nif(out)
    rb = ns.read_trishape_data(back.blocks[cog_data])
    assert len(rb['verts']) == len(V) and len(rb['tris']) == len(T)
    orig = ns.Nif(raw)
    assert len(back.blocks) == len(orig.blocks) + 8
    rbb = ns.read_trishape_data(back.blocks[barrel_data])
    assert len(rbb['verts']) == len(BV) and len(rbb['tris']) == len(BT)
    for k in range(len(orig.blocks)):
        if k not in (root, texset_i, data_i, shader_i):
            assert back.blocks[k] == orig.blocks[k], 'original block %d changed' % k
    mesh_path = os.path.join(out_root, OUT_MESH)
    os.makedirs(os.path.dirname(mesh_path), exist_ok=True)
    with open(mesh_path, 'wb') as fh:
        fh.write(out)
    chk = NifFile(mesh_path)
    names = sorted(s_.name for s_ in chk.shapes)
    assert COG_SHAPE_NAME in names and BARREL_SHAPE_NAME in names and len(chk.shapes) == 3, names
    cog_chk = [s_ for s_ in chk.shapes if s_.name == COG_SHAPE_NAME][0]
    assert len(cog_chk.verts) == len(V) and np.allclose(np.array(cog_chk.verts), V, atol=1e-3)
    print('wrote', mesh_path, len(out), 'bytes;', len(V), 'cog verts,', len(T), 'tris')
    for p in (OUT_D, OUT_N, OUT_M, OUT_COG, OUT_COG_N, OUT_COG_M, OUT_E):
        print('wrote', os.path.join(out_root, p))

    if args.preview:
        preview(args.preview, [
            (RV, RT, RUV, Image.fromarray((rgb * 255).astype(np.uint8)).resize((1024, 1024))),
            (BV, BT, BUV, Image.fromarray((rgb * 255).astype(np.uint8)).resize((1024, 1024))),
            (V, T, UV, Image.fromarray((cog_rgb * 255).astype(np.uint8)).resize((512, 512))),
        ])
        Image.fromarray((rgb * 255).astype(np.uint8)).resize((1024, 1024)).save(args.preview + '_atlas.png')


if __name__ == '__main__':
    main()
