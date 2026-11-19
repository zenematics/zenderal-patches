"""Caldera's mesh and textures (curator 2026-11-16: "lets make a Unique 1handed Mace, I want it to look like a Forge
Hammer with cracks in it with Molten lava in them"; head: "Sledge block (C)", then "this one" on the picture of
Craftsman Tools Replacer's hammer01; handle: "Noble Armory mace handle", then, on that picture again, "change the
handle to this length and width").

The mesh is Pretty Enderal Armory's Aeterna Mace (meshes/weapons/elven/elvenmace.nif = Caenraes' Noble Armory mace,
open with credit: credit Caenraes) with its flanged head taken off (the head core, its six flanges and the knob on
top: 2012 triangles, asserted) and a sledge head of our own in its place. Craftsman Tools Replacer forbids reuse of
its models, so the head is only measured from its hammer01 (head 12.23 x 7.47 x 7.47, a square section, rounded long
edges ~0.7, the haft end 1.6 above the top), never copied:

- the handle in hammer01's proportions to its head (haft 23.34 from its end to the head's underside = 1.91 head
  lengths; 3.18 wide = 0.43 head heights): the Noble mace's long twisted shaft (288 triangles, asserted) is dropped,
  and its collar, leather grip, ring and pommel are shortened (HANDLE_K, along the shaft) and thickened (HANDLE_W,
  round the axis) so the collar sits just inside the head's underside (COLLAR_INTO_HEAD) and the hand (the mesh
  origin: where every one-handed weapon is held) is as far below the head as hammer01's is; normals and tangents are
  carried through the same stretch. The belt loop (Scb, round the grip below the hand) is widened with the grip.
  The pommel and the collar are the head's dark iron (curator 2026-11-16: "change the pommel and steam connecting the
  head to the same color as the hammers head"): our copy of Noble's mace texture (CalderaHandle_d / _m), their texels
  (and only theirs: no other kept piece shares them, asserted) recoloured to IRON's hue at the head's median
  brightness, keeping their engravings' contrast, and their environment mask all but off (the head has none);
- a rounded box HEAD_SIZE (length along the swing, x) with edge radius HEAD_ROUND on the collar's axis, and the
  haft's end standing out of the top (STUB, the haft's width, hammer01's height), worn like the pommel (curator
  2026-11-16, with pictures of the pommel and the stub: "add the worn texturing from the pommel to the head stem"):
  its side is the pommel's worn side panel (from the iron-recoloured handle texture, STUB_SIDE inside the pommel's
  texels, asserted) STUB_REPEAT times round, its top the pommel's hexagonal end cap (STUB_CAP);
- its own 2048 atlas (one chart per face, the stub's side and cap), painted here from 3D fields, so the cracks run on
  across every edge: forged dark iron with hammer dents and worn bright edges; a network of fissures (a warped 3D
  Voronoi's cell walls, a random share of them; finer branches next to them) dark in the diffuse, grooved in the
  normal map (alpha = specular, none in a crack), and molten in the glow map (white-yellow core, orange, deep red
  at the walls, a dim red halo);
- five copies of the head, ZP_CalderaHead0..4, each under its node ZP_CalderaTier0..4: tier t's glow map lights more
  of the fissures (TIER_SHARE; curator 2026-11-16, on the render of the first build's least-lit tier: "let this be
  the most intense the lava on the hammer gets and its starts with no lava on it", "and progressively gets more
  molten cracks on it": tier 0 has none, tier 4 is that render, each tier lights the last one's cracks and more;
  then "the zero hits can we remove all cracks and the cracks only appear after 2 hits": tier 0's head has its own
  diffuse and normal map without a fissure, Caldera_clean_d / _n; tiers 1-4 share the cracked ones);
  only Tier0 is at scale 1 in the file. The charge script lights one tier at a time
  (SKSE NetImmerse.SetNodeScale, as Argent Verdict's knuckle motes). Every copy has its own shader (never shared: two
  shapes on one lighting shader froze the game, Clockwork Thunder), the Noble shader turned into a glow shader
  (type 2, Glow_Map, Own_Emit; no environment map);
- the two blood overlays Edgeblood and Edgeblood01 (copies of the flanged head) now cover the sledge head.

The eruption's small volcanoes (curator 2026-11-16: "remove the fissure effect and instead add smaller volcanos
scattered around, they do very little damage mainly there for effect"; the glowing cracked disk that stood here until
then is described in arch-docs/patches/Caldera.md): Apocalypse's volcano fountain (meshes/ApocNew/DestructionFire_Static_VolcanoNew_Fountain.nif,
Apocalypse's own copy from its BSA: PG Patcher's copy only swaps the cone's dirt-cliff texture for PBR ones, which a
PG Patcher rerun can move) at VENT_SCALE. The scale sits on a new node under the root, never on the root (the game
sets a reference's root transform from the reference). Its one particle system (the lava spray) is in world space,
where a node's scale moves where particles are born but not how fast they fly or how hard they fall, so the emitter's
speed and speed variation and the gravity's strength are scaled by VENT_SCALE as well: the spray then rises VENT_SCALE
as high (v squared over 2 g). The particle size is left alone (the particle system's own node scale, 1.85 in the
file, is what sizes them, and it now sits under the scale node).

The eruption's shockwave: vanilla Fire Storm's ring of flame (meshes/magic/FireStormAreaEffect.nif, the winning
copy) with its root scaled so its own reach marker (BlastRadiusNode, ~615 units) is the eruption script's ShockRadius,
as Sting and Rise's fire nova (Sunrise) does it.

Outputs, into <mods>/<target> (default Zenderal - Patch Collection): meshes/Zenderal/Caldera/Caldera.nif (both
views), CalderaShockwave.nif, CalderaVent.nif, textures/Zenderal/Caldera/Caldera_d.dds, _n.dds (alpha = specular), _g0.._g4.dds,
Caldera_clean_d.dds, Caldera_clean_n.dds (tier 0: no cracks), CalderaHandle_d.dds, CalderaHandle_m.dds.

Usage:  python 01-build-mesh.py [--out-root <dir>]
"""
import argparse
import importlib.util
import math
import os
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
SR = os.path.join(ROOT, 'src', 'StingAndRise', 'tools')
sys.path.insert(0, SR)
_spec = importlib.util.spec_from_file_location('sr_assets', os.path.join(SR, '01-build-assets.py'))
sr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sr)
nifse = sr.nifse
_spec = importlib.util.spec_from_file_location(
    'nifsplice', os.path.join(ROOT, 'src', 'ClockworkThunder', 'tools', 'nifsplice.py'))
ns = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ns)                       # Skyrim LE blocks (Apocalypse's fountain)

MESH = 'meshes/weapons/elven/elvenmace.nif'        # Pretty's Aeterna Mace (Noble Armory)
SHAPE = 'Noble_Mace_MP'
BLOOD = ('Edgeblood', 'Edgeblood01')                # the flanged head's two blood overlays
HEAD_TRIS = 2012                                    # the flanged head: core 576, 6 flanges x 190, knob 296
HEAD_ISLANDS = 8
HEAD_FROM_Y = 46.0                                  # every flanged-head island starts above this (shape frame)
OUT_MESH = 'meshes/Zenderal/Caldera/Caldera.nif'
SHOCK_SRC = 'meshes/magic/FireStormAreaEffect.nif'      # vanilla Fire Storm's ring of flame
SHOCK_MARKER = 'BlastRadiusNode'                        # the mesh's own marker of the ring's reach
OUT_SHOCK = 'meshes/Zenderal/Caldera/CalderaShockwave.nif'
VENT_SRC = 'meshes/ApocNew/DestructionFire_Static_VolcanoNew_Fountain.nif'   # Apocalypse's volcano (Skyrim LE format)
VENT_BSA = os.path.join('Apocalypse - Magic of Skyrim', 'Apocalypse - Magic of Skyrim.bsa')     # under <mods>
OUT_VENT = 'meshes/Zenderal/Caldera/CalderaVent.nif'
VENT_SCALE = 0.4                   # the small volcanoes (02-build-records.py reads it for the fountain's bounds)
VENT_EMITTER = (420.0, 479.8)      # Apocalypse's spray: speed, speed variation (units a second; asserted)
VENT_GRAVITY = 810.0               # its planar gravity's strength (asserted)
ERUPTION_SCRIPT = os.path.join(HERE, '..', 'Scripts', 'source', 'ZP_CalderaEruptionScript.psc')
TEX = 'textures/Zenderal/Caldera/Caldera'
TIERS = 5

HEAD_SIZE = (13.8, 8.4, 8.4)       # length (x, the swing), height (y, the shaft), depth (z): hammer01's proportions
HEAD_ROUND = 0.8                   # edge radius (hammer01 ~0.7 on its 7.47)
# hammer01 (Craftsman Tools Replacer, measured, 2026-11-16): head 12.23 long, 7.47 high, bottom at y 7.75 above the
# mesh origin; haft from y -15.59, 3.18 wide; haft end 1.57 above the head's top
C_HEAD = (12.23, 7.47)
C_HEAD_BOTTOM, C_HAFT_END, C_HAFT_W, C_STUB = 7.75, -15.59, 3.18, 1.57
C_SCALE = HEAD_SIZE[0] / C_HEAD[0]
SHAFT_TRIS = 288                   # the Noble mace's twisted shaft, dropped
COLLAR_TRIS = 284                  # its collar (the ferrule under the head)
GRIP_TRIS = 1710                   # its leather grip
POMMEL_TRIS = 556                  # its pommel
RING_TRIS = 224                    # the ring at the grip's foot
NOBLE_D = 'textures/weapons/noble armory/mace/mace.dds'
NOBLE_M = 'textures/weapons/noble armory/mace/mace_m.dds'
HANDLE_TEX = 'textures/Zenderal/Caldera/CalderaHandle'
HEAD_MEDIAN = 0.150                # the head's diffuse median brightness (measured on Caldera_d, 2026-11-16)
IRON_MASK = 0.04                   # the pommel's and collar's environment mask (Noble's 0.21-0.27: shiny)
# the head's stub worn like the pommel: texel boxes (x0, y0, x1, y1) in the pommel's own texture area (its UV mask's
# bounding box at 2048, 616 x 223): a side panel with its scuffed facet edges, and the hexagonal end cap
STUB_SIDE = (440, 10, 604, 172)
STUB_CAP = (0, 0, 212, 168)
STUB_REPEAT = 4                    # the side panel round the stub
COLLAR_INTO_HEAD = 0.3
HANDLE_WIDTH = C_HAFT_W / C_HEAD[1] * HEAD_SIZE[1]          # the grip's width (x), as hammer01's haft to its head
STUB = (HANDLE_WIDTH / 2, C_STUB * C_SCALE, 0.35)           # the haft's end above the head: radius, height, dome
ATLAS = 2048                       # diffuse / normal; glow maps at half size
GLOW_SIZE = 1024
PAD = 12                           # texels round every chart

# the fissures (units, the shape frame)
CELL = 2.9                         # primary network: Voronoi cell size
CELL_FINE = 1.15                   # branches
WARP = (0.55, 0.9)                 # domain warp: amplitude, frequency (makes the walls jagged)
WIDTH = 0.105                      # primary crack half-width at its widest
WIDTH_FINE = 0.045
FINE_REACH = 0.55                  # branches show only this close to a lit primary crack
TIER_SHARE = ((0.0, 0.0), (0.12, 0.05), (0.23, 0.11), (0.34, 0.16), (0.45, 0.22))   # (primary, branch) share lit
#                                    (the first build's 0.45 / 0.54 / 0.63 / 0.72 / 0.84: its least-lit is now the most)
COOLED = (0.84, 0.68)              # the dark fissures in the diffuse (the first build's: the curator's picture)
DEPTH = 0.06                       # groove depth (normal map)
HALO = 0.22                        # glow halo falloff
LAVA = ((0.00, (0.55, 0.05, 0.01)), (0.35, (0.95, 0.28, 0.03)), (0.70, (1.00, 0.62, 0.12)), (1.00, (1.00, 0.93, 0.62)))
IRON = (0.155, 0.150, 0.145)       # forged face
IRON_EDGE = (0.36, 0.35, 0.34)     # worn edges
EMISSIVE = ((1.0, 1.0, 1.0), 2.2)  # glow shader: emissive colour, multiple
SPEC = (0.40, 0.75)                # specular (normal alpha): face, worn edge
SEED = 1606


# ---------------------------------------------------------------------------------------------- noise, Voronoi
def _hash(*ints):
    h = np.zeros(np.broadcast(*ints).shape, np.uint64)
    for k, v in enumerate(ints):
        h ^= (np.asarray(v).astype(np.int64).astype(np.uint64) + np.uint64(0x9E3779B97F4A7C15 * (k + 1) & 0xFFFFFFFFFFFFFFFF))
        h *= np.uint64(0xBF58476D1CE4E5B9)
        h ^= h >> np.uint64(31)
    h *= np.uint64(0x94D049BB133111EB)
    h ^= h >> np.uint64(29)
    return (h >> np.uint64(11)).astype(np.float64) / float(1 << 53)


def value_noise(P, freq, seed):
    X = P * freq
    i = np.floor(X).astype(np.int64)
    f = X - i
    f = f * f * (3 - 2 * f)
    out = 0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (f[:, 0] if dx else 1 - f[:, 0]) * (f[:, 1] if dy else 1 - f[:, 1]) * (f[:, 2] if dz else 1 - f[:, 2])
                out = out + w * _hash(i[:, 0] + dx, i[:, 1] + dy, i[:, 2] + dz, np.full(len(P), seed))
    return out


def fbm(P, freq, seed, octaves=4):
    s, a, tot = 0, 1.0, 0
    for o in range(octaves):
        s = s + a * value_noise(P, freq * 2 ** o, seed + 17 * o)
        tot += a
        a *= 0.5
    return s / tot


def voronoi_walls(P, cell, seed):
    """Distance to the nearest cell wall of a jittered 3D Voronoi (exact for the two nearest seeds) and a [0, 1)
    hash of that wall's seed pair."""
    out_d = np.empty(len(P))
    out_h = np.empty(len(P))
    for a in range(0, len(P), 200000):
        X = P[a:a + 200000] / cell
        ci = np.floor(X).astype(np.int64)
        best = [np.full(len(X), np.inf), np.full(len(X), np.inf)]
        seeds = [np.zeros((len(X), 3)), np.zeros((len(X), 3))]
        ids = [np.zeros((len(X), 3), np.int64), np.zeros((len(X), 3), np.int64)]
        for ox in (-1, 0, 1):
            for oy in (-1, 0, 1):
                for oz in (-1, 0, 1):
                    c = ci + np.array([ox, oy, oz])
                    j = np.stack([_hash(c[:, 0], c[:, 1], c[:, 2], np.full(len(X), seed + q)) for q in range(3)], 1)
                    sp = c + 0.15 + 0.7 * j
                    d = ((X - sp) ** 2).sum(1)
                    first = d < best[0]
                    second = ~first & (d < best[1])
                    best[1] = np.where(first, best[0], np.where(second, d, best[1]))
                    seeds[1] = np.where(first[:, None], seeds[0], np.where(second[:, None], sp, seeds[1]))
                    ids[1] = np.where(first[:, None], ids[0], np.where(second[:, None], c, ids[1]))
                    best[0] = np.where(first, d, best[0])
                    seeds[0] = np.where(first[:, None], sp, seeds[0])
                    ids[0] = np.where(first[:, None], c, ids[0])
        gap = np.linalg.norm(seeds[1] - seeds[0], axis=1)
        out_d[a:a + len(X)] = (best[1] - best[0]) / (2 * np.maximum(gap, 1e-9)) * cell
        k0 = ids[0][:, 0] * 1000003 + ids[0][:, 1] * 1009 + ids[0][:, 2]          # the pair in a fixed order, so
        k1 = ids[1][:, 0] * 1000003 + ids[1][:, 1] * 1009 + ids[1][:, 2]          # both sides of a wall agree
        out_h[a:a + len(X)] = _hash(np.minimum(k0, k1), np.maximum(k0, k1), np.full(len(X), seed))
    return out_d, out_h


def ramp(stops, x):
    x = np.clip(x, 0, 1)
    out = np.zeros(x.shape + (3,))
    for (a, ca), (b, cb) in zip(stops[:-1], stops[1:]):
        m = (x >= a) & (x <= b)
        t = ((x - a) / max(b - a, 1e-9))[m][:, None]
        out[m] = np.array(ca) * (1 - t) + np.array(cb) * t
    return out


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------------------------------------- the head
def rounded(q, e, r):
    """A point q on the box of half-extents e onto the rounded box (edge radius r), and its normal."""
    inner = np.asarray(e) - r
    c = np.clip(q, -inner, inner)
    d = q - c
    n = d / np.maximum(np.linalg.norm(d, axis=-1, keepdims=True), 1e-12)
    return c + r * n, n


def breaks(ext, r, seg_round=5, seg_flat=2.0):
    """Grid lines along one face axis: dense in the rounded bands, sparse across the flat."""
    flat = np.linspace(-ext + r, ext - r, max(2, int(math.ceil(2 * (ext - r) / seg_flat)) + 1))
    band = np.linspace(-ext, -ext + r, seg_round + 1)
    return np.concatenate([band[:-1], flat, -band[::-1][1:]])


class Chart:
    """One planar chart: texel (col, row) -> a parameter pair -> a point on the surface (and its normal)."""

    def __init__(self, name, w, h, to3d):
        self.name, self.w, self.h, self.to3d = name, w, h, to3d       # w, h in units; to3d(a, b) -> (P, N, edge)
        self.ox = self.oy = 0


def head_charts(centre, e, r):
    charts = []
    for axis in range(3):
        for sg in (1, -1):
            b, c = [k for k in range(3) if k != axis]
            if sg < 0:
                b, c = c, b                                   # keep every chart unmirrored (b x c = sg * axis)

            def to3d(u, v, axis=axis, sg=sg, b=b, c=c):
                q = np.zeros(u.shape + (3,))
                q[..., axis] = sg * e[axis]
                q[..., b] = u - e[b]
                q[..., c] = v - e[c]
                p, n = rounded(q, e, r)
                inner = np.asarray(e) - r
                band = np.abs(q) - inner
                band[..., axis] = 0                                           # the face's own axis is always out
                edge = np.clip(band.max(-1) / r, 0, 1)                        # 0 flat .. 1 at the bevel's middle
                return p + centre, n, edge
            charts.append(Chart('face%d%s' % (axis, '+' if sg > 0 else '-'), 2 * e[b], 2 * e[c], to3d))
    return charts


def stub_charts(base, radius, height, dome):
    circ = 2 * math.pi * radius

    def side(u, v):
        a = u / radius
        p = np.stack([radius * np.cos(a), v, radius * np.sin(a)], -1)
        n = np.stack([np.cos(a), np.zeros_like(a), np.sin(a)], -1)
        return p + base, n, np.full(u.shape, 0.6)

    def cap(u, v):
        x, z = u - radius, v - radius
        rr = np.minimum(np.hypot(x, z) / radius, 1.0)
        y = height + dome * np.sqrt(np.maximum(1 - rr ** 2, 0))
        p = np.stack([x, y, z], -1)
        g = dome / radius * rr / np.maximum(np.sqrt(np.maximum(1 - rr ** 2, 1e-4)), 1e-4)
        n = np.stack([x / np.maximum(np.hypot(x, z), 1e-9) * g, np.ones_like(x), z / np.maximum(np.hypot(x, z), 1e-9) * g], -1)
        n /= np.linalg.norm(n, axis=-1, keepdims=True)
        return p + base, n, np.full(u.shape, 0.6)
    return [Chart('stubside', circ, height, side), Chart('stubcap', 2 * radius, 2 * radius, cap)]


def pack(charts, size, pad):
    """Shelf-pack the charts at one texel density; the largest density that fits."""
    lo, hi = 1.0, 400.0
    for _ in range(40):
        s = (lo + hi) / 2
        x = y = shelf = 0
        ok = True
        for ch in sorted(charts, key=lambda c: -c.h):
            w, h = int(math.ceil(ch.w * s)) + 2 * pad, int(math.ceil(ch.h * s)) + 2 * pad
            if x + w > size:
                x, y, shelf = 0, y + shelf, 0
            if w > size or y + h > size:
                ok = False
                break
            x, shelf = x + w, max(shelf, h)
        lo, hi = (s, hi) if ok else (lo, s)
    s = lo
    x = y = shelf = 0
    for ch in sorted(charts, key=lambda c: -c.h):
        w, h = int(math.ceil(ch.w * s)) + 2 * pad, int(math.ceil(ch.h * s)) + 2 * pad
        if x + w > size:
            x, y, shelf = 0, y + shelf, 0
        ch.ox, ch.oy = x + pad, y + pad
        x, shelf = x + w, max(shelf, h)
    return s


def chart_mesh(ch, us, vs, s, size):
    """The chart's vertices on the grid us x vs (units), with atlas UVs; quads split along their shorter diagonal."""
    U, V = np.meshgrid(us, vs)
    P, N, _ = ch.to3d(U, V)
    uv = np.stack([(ch.ox + U * s) / size, (ch.oy + V * s) / size], -1)
    nu, nv = len(us), len(vs)
    T = []
    for j in range(nv - 1):
        for i in range(nu - 1):
            a, b, c, d = j * nu + i, j * nu + i + 1, (j + 1) * nu + i + 1, (j + 1) * nu + i
            T += [(a, b, c), (a, c, d)]
    return P.reshape(-1, 3), N.reshape(-1, 3), uv.reshape(-1, 2), np.array(T)


def build_geometry(centre, s, charts):
    e = np.array(HEAD_SIZE) / 2
    parts = []
    for ch in charts[:6]:
        axis = int(ch.name[4])
        b, c = [k for k in range(3) if k != axis]
        if ch.name.endswith('-'):
            b, c = c, b
        us = breaks(e[b], HEAD_ROUND) + e[b]
        vs = breaks(e[c], HEAD_ROUND) + e[c]
        parts.append(chart_mesh(ch, us, vs, s, ATLAS))
    side, cap = charts[6], charts[7]
    seg = 20
    us = np.linspace(0, side.w, seg + 1)
    vs = np.linspace(0, STUB[1], 5)                           # from the head's (flat) top to the stub's rim
    parts.append(chart_mesh(side, us, vs, s, ATLAS))
    # the cap: a fan of rings
    ring_r = np.linspace(0, STUB[0], 5)[1:]
    ang = np.linspace(0, 2 * math.pi, seg + 1)[:-1]
    uu = [np.array([STUB[0]])]
    vv = [np.array([STUB[0]])]
    for rr in ring_r:
        uu.append(STUB[0] + rr * np.cos(ang))
        vv.append(STUB[0] + rr * np.sin(ang))
    U, V = np.concatenate(uu), np.concatenate(vv)
    P, N, _ = cap.to3d(U, V)
    uv = np.stack([(cap.ox + U * s) / ATLAS, (cap.oy + V * s) / ATLAS], -1)
    T = [(0, 1 + (i + 1) % seg, 1 + i) for i in range(seg)]
    for k in range(len(ring_r) - 1):
        a0, b0 = 1 + k * seg, 1 + (k + 1) * seg
        for i in range(seg):
            i1 = (i + 1) % seg
            T += [(a0 + i, a0 + i1, b0 + i1), (a0 + i, b0 + i1, b0 + i)]
    parts.append((P, N, uv, np.array(T)))
    Vs, Ns, UVs, Ts, off = [], [], [], [], 0
    for P, N, uv, T in parts:
        Vs.append(P)
        Ns.append(N)
        UVs.append(uv)
        Ts.append(T + off)
        off += len(P)
    V, N, UV, T = np.concatenate(Vs), np.concatenate(Ns), np.concatenate(UVs), np.concatenate(Ts)
    # face winding outward (normal . cross > 0)
    cr = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    flip = (cr * N[T].mean(1)).sum(1) < 0
    T[flip] = T[flip][:, [0, 2, 1]]
    return V, N, UV, T


# ---------------------------------------------------------------------------------------------- the textures
def stub_worn(images, charts, s, patches):
    """The stub's charts (and their padding) from the pommel's worn patches: the side panel STUB_REPEAT times round
    (whole repeats, so the wrap has no seam), the end cap across the top."""
    side, cap = patches
    for ch in charts:
        if not ch.name.startswith('stub'):
            continue
        x0, y0 = max(ch.ox - PAD, 0), max(ch.oy - PAD, 0)
        x1 = min(ch.ox + int(math.ceil(ch.w * s)) + PAD, ATLAS)
        y1 = min(ch.oy + int(math.ceil(ch.h * s)) + PAD, ATLAS)
        cols, rows = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
        u = (cols - ch.ox) / s
        v = np.clip((rows - ch.oy) / s, 0, ch.h)
        if ch.name == 'stubside':
            pw, ph = side.shape[1], side.shape[0]
            pc = (np.mod(u / ch.w * STUB_REPEAT, 1) * pw).astype(int).clip(0, pw - 1)
            pr = (v / ch.h * ph).astype(int).clip(0, ph - 1)
            texels = side[pr, pc]
        else:
            pw, ph = cap.shape[1], cap.shape[0]
            pc = (np.clip(u / ch.w, 0, 1) * pw).astype(int).clip(0, pw - 1)
            pr = (v / ch.h * ph).astype(int).clip(0, ph - 1)
            texels = cap[pr, pc]
        for img in images:
            img[y0:y1, x0:x1] = texels


def paint(charts, s, centre, stub=None):
    """Per texel of the atlas: its surface point, then the iron, the fissures and the lava of every tier."""
    pos = np.zeros((ATLAS, ATLAS, 3))
    nrm = np.zeros((ATLAS, ATLAS, 3))
    edge = np.zeros((ATLAS, ATLAS))
    head = np.zeros((ATLAS, ATLAS), bool)
    used = np.zeros((ATLAS, ATLAS), bool)
    for ch in charts:
        x0, y0 = max(ch.ox - PAD, 0), max(ch.oy - PAD, 0)
        x1 = min(ch.ox + int(math.ceil(ch.w * s)) + PAD, ATLAS)
        y1 = min(ch.oy + int(math.ceil(ch.h * s)) + PAD, ATLAS)
        cols, rows = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
        u = np.clip((cols - ch.ox) / s, 0, ch.w)
        v = np.clip((rows - ch.oy) / s, 0, ch.h)
        P, N, E = ch.to3d(u, v)
        pos[y0:y1, x0:x1], nrm[y0:y1, x0:x1], edge[y0:y1, x0:x1] = P, N, E
        head[y0:y1, x0:x1] = not ch.name.startswith('stub')
        used[y0:y1, x0:x1] = True
    m = used.reshape(-1)
    P = pos.reshape(-1, 3)[m] - centre
    print('caldera textures: %d texels on the surface, %.1f texels a unit' % (m.sum(), s))
    warp = np.stack([fbm(P, WARP[1], SEED + 1 + q, 3) for q in range(3)], 1) - 0.5
    Pw = P + WARP[0] * 2 * warp
    d1, h1 = voronoi_walls(Pw, CELL, SEED + 10)
    d2, h2 = voronoi_walls(Pw * 1.0 + 3.7, CELL_FINE, SEED + 20)
    wvar = 0.45 + 1.0 * fbm(P, 0.9, SEED + 30, 3)
    w1 = WIDTH * wvar
    w2 = WIDTH_FINE * (0.5 + 0.8 * fbm(P, 2.1, SEED + 31, 3))
    is_head = head.reshape(-1)[m]

    def lit_field(share):
        a = (h1 < share[0]) & is_head
        prim = np.where(a, np.clip(1 - d1 / w1, 0, 1), 0)
        near = np.where(a, d1, np.inf)
        # distance to the nearest lit primary wall, for the branches: the primary distance where lit, else far
        reach = np.exp(-np.minimum(near, 5) / FINE_REACH)
        b = (h2 < share[1]) & is_head & (reach > 0.05)
        fine = np.where(b, np.clip(1 - d2 / w2, 0, 1) * smoothstep(0.05, 0.35, reach), 0)
        core = np.maximum(prim, fine)
        halo = np.where(a, np.exp(-d1 / HALO), 0) * 0.35
        return core, halo

    cooled_core, _ = lit_field(COOLED)
    dents = fbm(P, 1.3, SEED + 40, 4)
    grain = fbm(P, 6.0, SEED + 41, 3)
    E = edge.reshape(-1)[m]
    wear = smoothstep(0.35, 1.0, E) * (0.6 + 0.4 * fbm(P, 3.0, SEED + 42, 3))
    base = np.array(IRON) * (0.85 + 0.3 * dents[:, None] + 0.12 * (grain[:, None] - 0.5))
    base = base * (1 - wear[:, None]) + np.array(IRON_EDGE) * (0.9 + 0.2 * grain[:, None]) * wear[:, None]
    clean = base.copy()                                 # tier 0: the iron without a single fissure
    near_cool = smoothstep(0.0, 1.0, np.clip(1 - np.where(is_head & (h1 < COOLED[0]), d1, 9) / 0.45, 0, 1))
    base = base * (1 - 0.35 * near_cool[:, None]) + np.array((0.30, 0.07, 0.02)) * 0.35 * near_cool[:, None]
    fissure = smoothstep(0.0, 0.6, cooled_core)
    diff = base * (1 - fissure[:, None]) + np.array((0.035, 0.012, 0.006)) * fissure[:, None]
    def diffuse(values):
        out = np.zeros((ATLAS, ATLAS, 3))
        out.reshape(-1, 3)[m] = np.clip(values, 0, 1)
        return out

    def normal(groove, crack):
        # dents (+ grooves), in each chart's own (u right, v down) frame; alpha = specular, none in a crack
        hgt = np.zeros((ATLAS, ATLAS))
        hgt.reshape(-1)[m] = 0.03 * (dents - 0.5) + 0.006 * (grain - 0.5) - DEPTH * groove
        gy, gx = np.gradient(hgt)
        n = np.stack([-gx * s, -gy * s, np.ones_like(gx)], -1)
        n /= np.linalg.norm(n, axis=-1, keepdims=True)
        spec = np.zeros((ATLAS, ATLAS))
        spec.reshape(-1)[m] = (SPEC[0] * (1 - wear) + SPEC[1] * wear) * (1 - crack)
        return np.concatenate([n * 0.5 + 0.5, spec[..., None]], -1)
    D, D0 = diffuse(diff), diffuse(clean)
    if stub is not None:
        stub_worn((D, D0), charts, s, stub)
    NM = normal(smoothstep(0.0, 0.8, cooled_core), fissure)
    NM0 = normal(np.zeros(len(P)), np.zeros(len(P)))
    glows = []
    for t, share in enumerate(TIER_SHARE):
        core, halo = lit_field(share)
        flicker = 0.75 + 0.25 * fbm(P, 1.7, SEED + 50, 3)
        col = ramp(LAVA, core * flicker) * smoothstep(0.0, 0.15, core)[:, None]
        col = col + np.array((0.45, 0.06, 0.01)) * (halo * (1 - smoothstep(0.0, 0.15, core)))[:, None]
        G = np.zeros((ATLAS, ATLAS, 3))
        G.reshape(-1, 3)[m] = np.clip(col, 0, 1)
        G = G.reshape(GLOW_SIZE, ATLAS // GLOW_SIZE, GLOW_SIZE, ATLAS // GLOW_SIZE, 3).mean((1, 3))
        glows.append(G)
        print('caldera tier %d: primary share %.2f, branches %.2f, lit texels %.2f%%' % (
            t, share[0], share[1], 100.0 * (core > 0.05).mean()))
    return D, NM, D0, NM0, glows


# ---------------------------------------------------------------------------------------------- the NIF
def _node(nif, name, flags, t, scale, kids):
    """A new NiNode: no extra data, controller, collision or effects (Argent Verdict's motes.py shape)."""
    b = struct.pack('<iIiI', nif.add_string(name), 0, -1, flags) + struct.pack('<3f', *[float(x) for x in t])
    b += struct.pack('<9f', *np.eye(3).reshape(-1)) + struct.pack('<fi', float(scale), -1)
    b += struct.pack('<I', len(kids)) + struct.pack('<%di' % len(kids), *kids) + struct.pack('<I', 0)
    return nif.add_block('NiNode', b)


def tangent_convention(s):
    """Argent Verdict's: the source shape's tangent / bitangent against its UV derivatives (median vertex)."""
    du, dv = sr.uv_derivatives(s['pos'], s['uv'], s['tris'])
    du, dv = sr.normalize(du), sr.normalize(dv)
    Tn, Bn = sr.normalize(s['tangent']), sr.normalize(s['bitangent'])
    m = {('tan', 'du'): np.median((Tn * du).sum(1)), ('tan', 'dv'): np.median((Tn * dv).sum(1)),
         ('bit', 'du'): np.median((Bn * du).sum(1)), ('bit', 'dv'): np.median((Bn * dv).sum(1))}
    tan = max(('du', 'dv'), key=lambda d: abs(m[('tan', d)]))
    bit = max(('du', 'dv'), key=lambda d: abs(m[('bit', d)]))
    assert tan != bit and abs(m[('tan', tan)]) > 0.9 and abs(m[('bit', bit)]) > 0.9, m
    return tan, np.sign(m[('tan', tan)]), bit, np.sign(m[('bit', bit)])


def frames(s, V, N, UV, T):
    tan_axis, tan_sign, bit_axis, bit_sign = tangent_convention(s)
    du, dv = sr.uv_derivatives(V, UV, T)
    deriv = {'du': du, 'dv': dv}

    def frame(d, alt):
        f = d - N * (N * d).sum(1, keepdims=True)
        weak = np.linalg.norm(f, axis=1) < 1e-6
        f[weak] = np.cross(N[weak], alt[weak])
        weak = np.linalg.norm(f, axis=1) < 1e-6
        f[weak] = np.cross(N[weak], np.array([1.0, 0.0, 0.0]))
        return sr.normalize(f)
    other = {'du': dv, 'dv': du}
    tangent = tan_sign * frame(deriv[tan_axis], other[tan_axis])
    bitangent = bit_sign * frame(deriv[bit_axis], other[bit_axis])
    assert np.isfinite(tangent).all() and np.isfinite(bitangent).all()
    return tangent, bitangent


def glow_shader(nif, src_shader, glow_rel, tex=TEX):
    """A copy of the Noble shader as a glow shader: type 2, Glow_Map + Own_Emit, no environment map; our set."""
    sh = nifse.copy_lighting_shader(nif, nif, src_shader)
    b = bytearray(nif.blocks[sh])
    assert struct.unpack_from('<I', b, 0)[0] == 1 and len(b) == 104, 'the Noble shader is no longer an env-map shader'
    f1, f2 = struct.unpack_from('<II', b, 16)
    assert f1 & 0x80 and f1 & 0x400000, hex(f1)
    struct.pack_into('<I', b, 0, 2)                                    # Glow Shader
    struct.pack_into('<II', b, 16, f1 & ~0x80, (f2 | 0x40) & ~0x8000)  # no Environment_Mapping / EnvMap light fade
    struct.pack_into('<3f', b, 44, *EMISSIVE[0])
    struct.pack_into('<f', b, 56, EMISSIVE[1])
    struct.pack_into('<f', b, 72, 30.0)                                # glossiness: forged iron, duller than Noble's
    nif.blocks[sh] = bytes(b[:100])                                    # type 1 ends with its env-map scale
    ts = struct.unpack_from('<i', nif.blocks[sh], nifse.LSP_TEXSET)[0]
    paths = nifse.texture_paths(nif.blocks[ts])
    paths[0] = (tex + '_d.dds').replace('/', chr(92))
    paths[1] = (tex + '_n.dds').replace('/', chr(92))
    paths[2] = glow_rel.replace('/', chr(92))
    for k in range(3, len(paths)):
        paths[k] = ''
    nif.blocks[ts] = nifse.texture_set(paths)
    return sh


def iron_pieces(T, UV, lab, pieces, others):
    """Noble's mace diffuse and environment mask with the given pieces' texels in the head's iron: each texel's
    brightness scaled so the pieces' median is the head's, in IRON's hue; their mask down to IRON_MASK. The texels
    are the pieces' UV triangles widened by 3 texels (mip edges), never into the other kept pieces' own."""
    from PIL import Image, ImageDraw
    mods = os.path.join(sr.MO2, 'mods')
    D = sr.load_image(sr.winner(mods, sr.profile_mods(), NOBLE_D, sr.TEX_BSAS)[1]).copy()
    M = sr.load_image(sr.winner(mods, sr.profile_mods(), NOBLE_M, sr.TEX_BSAS)[1]).copy()

    def cover(ids, size):
        im = Image.new('L', (size, size), 0)
        dr = ImageDraw.Draw(im)
        for tri in T[np.isin(lab, ids)]:
            dr.polygon([(UV[v, 0] % 1 * size, UV[v, 1] % 1 * size) for v in tri], fill=255)
        return np.asarray(im) > 0

    def widen(m, n):
        for _ in range(n):
            g = m.copy()
            g[1:] |= m[:-1]
            g[:-1] |= m[1:]
            g[:, 1:] |= m[:, :-1]
            g[:, :-1] |= m[:, 1:]
            m = g
        return m
    lum = np.array([0.2126, 0.7152, 0.0722])
    iron = np.array(IRON) / (np.array(IRON) @ lum)
    for img, kind in ((D, 'diffuse'), (M, 'mask')):
        size = img.shape[0]
        assert img.shape[1] == size
        mine, theirs = cover(pieces, size), cover(others, size)
        if kind == 'diffuse':
            pm = cover((pieces[0],), size)                # the pommel's own texels: the stub's worn patches
            ys, xs = np.nonzero(pm)
            box = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
        assert not (mine & theirs).any(), ('a kept piece shares the pommel / collar texels', kind)
        area = widen(mine, 3) & ~widen(theirs, 1)
        if kind == 'diffuse':
            L = img[..., :3] @ lum
            scale = HEAD_MEDIAN / float(np.median(L[mine]))
            img[area, :3] = np.clip(L[area, None] * scale * iron, 0, 1)
            print('caldera pommel + collar: %d texels, brightness x%.3f to the head median %.3f' % (
                area.sum(), scale, HEAD_MEDIAN))
        else:
            img[area, :3] = IRON_MASK
    bx, by = box[0], box[1]
    patches = []
    for (x0, y0, x1, y1), full in ((STUB_SIDE, True), (STUB_CAP, False)):
        X0, Y0, X1, Y1 = bx + x0, by + y0, bx + x1, by + y1
        assert X1 <= box[2] and Y1 <= box[3], ('a stub patch leaves the pommel', (x0, y0, x1, y1))
        inside = pm[Y0:Y1, X0:X1].mean()
        assert inside > (0.995 if full else 0.6), ('a stub patch is not the pommel', inside)
        patches.append(D[Y0:Y1, X0:X1, :3].copy())
    print('caldera stub: the pommel side panel %dx%d x%d round, its end cap %dx%d' % (
        patches[0].shape[1], patches[0].shape[0], STUB_REPEAT, patches[1].shape[1], patches[1].shape[0]))
    return D, M, patches


def build_mesh(nif):
    hits = [i for i in nif.find('BSTriShape') if sr.name_of(nif, i) == SHAPE]
    assert len(hits) == 1, hits
    k = hits[0]
    s = nifse.read_trishape(nif.blocks[k])
    xf = nifse.transform(nif.blocks[k])
    P, T = s['pos'], s['tris']
    _, wid = np.unique(np.round(P * 1e4).astype(np.int64), axis=0, return_inverse=True)
    lab = sr.islands(T, wid.ravel())
    head = [l for l in np.unique(lab) if P[np.unique(T[lab == l])][:, 1].min() > HEAD_FROM_Y]
    cut = np.isin(lab, head)
    assert len(head) == HEAD_ISLANDS and cut.sum() == HEAD_TRIS, ('the flanged head changed', len(head), cut.sum())

    def island(tris, what):
        hit = [l for l in np.unique(lab) if (lab == l).sum() == tris and l not in head]
        assert len(hit) == 1, ('no single ' + what, hit)
        return hit[0]
    shaft, collar, grip = island(SHAFT_TRIS, 'shaft'), island(COLLAR_TRIS, 'collar'), island(GRIP_TRIS, 'grip')
    pommel, ring = island(POMMEL_TRIS, 'pommel'), island(RING_TRIS, 'ring')
    handle_tex = iron_pieces(T, s['uv'], lab, (pommel, collar), (grip, ring))      # pommel first: the stub's patches
    sv, cv, gv = (P[np.unique(T[lab == l])] for l in (shaft, collar, grip))
    assert sv[:, 1].min() > cv[:, 1].min() and sv[:, 1].max() > 46.0, 'the shaft is no longer above the collar'
    keep = T[~(cut | (lab == shaft))]
    # the handle: hammer01's length and width to its head; the hand (the mesh origin) as far below the head
    t0, R0, s0 = xf
    assert np.allclose(R0, np.eye(3), atol=1e-6) and abs(s0 - 1) < 1e-5, 'the Noble shape is rotated or scaled'
    hand = -t0[1]                                           # world y 0 in the shape frame
    axis = np.array([(cv[:, 0].min() + cv[:, 0].max()) / 2, 0, (cv[:, 2].min() + cv[:, 2].max()) / 2])
    used = np.unique(keep)
    y_top, y_end = cv[:, 1].max(), P[used, 1].min()        # collar top, pommel end
    head_bottom = hand + C_HEAD_BOTTOM * C_SCALE
    length = (C_HEAD_BOTTOM - C_HAFT_END) * C_SCALE         # haft end to head underside
    K = (length + COLLAR_INTO_HEAD) / (y_top - y_end)
    W = HANDLE_WIDTH / (gv[:, 0].max() - gv[:, 0].min())
    DY = head_bottom + COLLAR_INTO_HEAD - y_top * K
    S = np.array([W, K, W])
    P2 = (P - axis) * S + axis
    P2[:, 1] = P[:, 1] * K + DY
    N2 = sr.normalize(s['normal'] / S)
    T2, B2 = sr.normalize(s['tangent'] * S), sr.normalize(s['bitangent'] * S)
    ts = struct.unpack_from('<i', nif.blocks[s['shader']], nifse.LSP_TEXSET)[0]
    paths = nifse.texture_paths(nif.blocks[ts])
    assert paths[0].lower() == NOBLE_D.replace('/', chr(92)) and paths[5].lower() == NOBLE_M.replace('/', chr(92)), paths
    paths[0] = (HANDLE_TEX + '_d.dds').replace('/', chr(92))
    paths[5] = (HANDLE_TEX + '_m.dds').replace('/', chr(92))
    nif.blocks[ts] = nifse.texture_set(paths)
    av = struct.unpack_from('<I', nif.blocks[k], s['av']['flags'])[0]
    nif.blocks[k] = nifse.write_trishape(struct.unpack_from('<i', nif.blocks[k], 0)[0], av, xf, s['desc'],
                                         P2, s['uv'], N2, T2, B2, None, keep, s['shader'], s['alpha'])
    grip_world = (gv[:, 1].min() * K + DY + t0[1], gv[:, 1].max() * K + DY + t0[1])
    assert grip_world[0] < -3 and grip_world[1] > 3, ('the hand is no longer on the grip', grip_world)
    # the belt loop round the grip below the hand: widened with it (its own frame; it stays where the hand is)
    sc = [i for i in nif.find('BSTriShape') if sr.name_of(nif, i) == 'Scb']
    assert len(sc) == 1, sc
    c = nifse.read_trishape(nif.blocks[sc[0]])
    ct, cR, cs = nifse.transform(nif.blocks[sc[0]])
    Pn = (c['pos'] * cs) @ cR.T + ct - t0                  # into the handle's frame (R0 = I, s0 = 1: asserted)
    Pn[:, [0, 2]] = (Pn[:, [0, 2]] - axis[[0, 2]]) * W + axis[[0, 2]]
    Pc = ((Pn + t0 - ct) @ cR) / cs
    Sc = np.array([W, 1.0, W])

    def carry(v, inverse):
        w = v @ cR.T
        return sr.normalize((w / Sc if inverse else w * Sc) @ cR)
    cav = struct.unpack_from('<I', nif.blocks[sc[0]], c['av']['flags'])[0]
    nif.blocks[sc[0]] = nifse.write_trishape(struct.unpack_from('<i', nif.blocks[sc[0]], 0)[0], cav, (ct, cR, cs),
                                             c['desc'], Pc, c['uv'], carry(c['normal'], True),
                                             carry(c['tangent'], False), carry(c['bitangent'], False), None,
                                             c['tris'], c['shader'], c['alpha'])
    top_y = head_bottom
    shaft_r = HANDLE_WIDTH / 2
    e = np.array(HEAD_SIZE) / 2
    centre = np.array([axis[0], head_bottom + e[1], axis[2]])
    assert shaft_r < min(e[0], e[2]) - HEAD_ROUND, ('the handle does not fit the head', shaft_r)
    # charts, atlas, geometry
    charts = head_charts(centre, e, HEAD_ROUND) + stub_charts(centre + np.array([0, e[1], 0]), STUB[0], STUB[1], STUB[2])
    dens = pack(charts, ATLAS, PAD)
    V, N, UV, Tri = build_geometry(centre, dens, charts)
    tangent, bitangent = frames(s, V, N, UV, Tri)
    # the five tiers
    av_flags = struct.unpack_from('<I', nif.blocks[k], s['av']['flags'])[0]
    root = nif.roots[0]
    _, kids = nifse.node_children(nif.blocks[root])
    new = []
    for t in range(TIERS):
        sh = glow_shader(nif, s['shader'], TEX + '_g%d.dds' % t, TEX + '_clean' if t == 0 else TEX)   # no cracks at 0
        shape = nifse.write_trishape(nif.add_string('ZP_CalderaHead%d' % t), av_flags, xf, s['desc'],
                                     V, UV, N, tangent, bitangent, None, Tri, sh, -1)
        si = nif.add_block('BSTriShape', shape)
        new.append(_node(nif, 'ZP_CalderaTier%d' % t, 14, (0.0, 0.0, 0.0), 1.0 if t == 0 else 0.0, [si]))
    nif.blocks[root] = nifse.set_children(nif.blocks[root], kids + new)
    # the blood overlays onto the new head (each its own block, shader, alpha and flags; positions into its frame)
    t0, R0, s0 = xf
    world = (V * s0) @ R0.T + t0
    tn, bn = frames(s, V, N, UV, Tri)
    for name in BLOOD:
        bl = [i for i in nif.find('BSTriShape') if sr.name_of(nif, i) == name]
        assert len(bl) == 1, (name, bl)
        b = nifse.read_trishape(nif.blocks[bl[0]])
        assert len(b['tris']) == HEAD_TRIS, ('a blood overlay is no longer the flanged head', name, len(b['tris']))
        bt, bR, bs = nifse.transform(nif.blocks[bl[0]])
        Vb = ((world - bt) @ bR) / bs
        b_flags = struct.unpack_from('<I', nif.blocks[bl[0]], b['av']['flags'])[0]
        name_idx = struct.unpack_from('<i', nif.blocks[bl[0]], 0)[0]
        nif.blocks[bl[0]] = nifse.write_trishape(name_idx, b_flags, (bt, bR, bs), b['desc'], Vb, UV, N @ R0.T @ bR,
                                                 tn @ R0.T @ bR, bn @ R0.T @ bR, None, Tri, b['shader'], b['alpha'])
    print('caldera mesh: flanged head (%d triangles, %d pieces) and shaft cut; handle x%.3f long, x%.3f wide (%.2f '
          'wide), haft end to head %.2f, grip world y %.2f..%.2f; head %s round %.2f, underside y %.2f (world %.2f), '
          'axis x %.2f z %.2f; stub r %.2f + %.2f; %d vertices / %d triangles a tier, %d tiers; %d charts at %.1f '
          'texels a unit' % (cut.sum(), len(head), K, W, HANDLE_WIDTH, length, grip_world[0], grip_world[1],
                             HEAD_SIZE, HEAD_ROUND, top_y, top_y + t0[1], axis[0], axis[2], STUB[0], STUB[1], len(V),
                             len(Tri), TIERS, len(charts), dens))
    return nif, charts, dens, centre, handle_tex


def build_vent(nif):
    """Apocalypse's volcano fountain at VENT_SCALE (nifsplice, LE): a scale node under the root holding the root's
    children, and the world-space spray's speed and gravity scaled with it (see the module's docstring)."""
    root = nif.roots[0]
    assert nif.btype(root) == 'BSFadeNode', nif.btype(root)
    o, _ = ns.avobject_fields(nif.blocks[root])
    assert struct.unpack_from('<f', nif.blocks[root], o['scale'])[0] == 1.0
    _, kids = ns.node_children(nif.blocks[root])
    systems = nif.find('NiParticleSystem')
    assert len(systems) == 1, ('Apocalypse\'s fountain changed', systems)
    emitters = nif.find('NiPSysCylinderEmitter')
    gravity = nif.find('NiPSysGravityModifier')
    assert len(emitters) == 1 and len(gravity) == 1, (emitters, gravity)
    # the emitter: 13 bytes of modifier (name, order, target, active), then speed, speed variation
    b = nif.blocks[emitters[0]]
    speed = struct.unpack_from('<2f', b, 13)
    assert all(abs(a - w) < 0.05 for a, w in zip(speed, VENT_EMITTER)), speed
    struct.pack_into('<2f', b, 13, *(v * VENT_SCALE for v in speed))
    # planar gravity: modifier (13), gravity object (4), axis (12), decay (4), then strength, force type (0 = planar)
    b = nif.blocks[gravity[0]]
    strength, force = struct.unpack_from('<fI', b, 33)
    assert abs(strength - VENT_GRAVITY) < 0.05 and force == 0, (strength, force)
    struct.pack_into('<f', b, 33, strength * VENT_SCALE)
    scale_node = _node(nif, 'ZP_CalderaVentScale', 14, (0.0, 0.0, 0.0), VENT_SCALE, kids)
    nif.blocks[root] = ns.set_children(nif.blocks[root], [scale_node])
    print('caldera vent: Apocalypse\'s fountain x%.2f (%d nodes under the scale node), spray %.0f +- %.0f -> %.0f +- '
          '%.0f, gravity %.0f -> %.0f' % (VENT_SCALE, len(kids), speed[0], speed[1], speed[0] * VENT_SCALE,
                                          speed[1] * VENT_SCALE, strength, strength * VENT_SCALE))
    return nif


def build_shockwave(nif):
    """Fire Storm's ring scaled so its reach (BlastRadiusNode) is the eruption script's ShockRadius."""
    import re
    radius = float(re.search(r'^Float Property ShockRadius = ([\d.]+) AutoReadOnly', open(ERUPTION_SCRIPT).read(),
                             re.M).group(1))
    marker = [k for k in nif.find('NiNode') if sr.name_of(nif, k) == SHOCK_MARKER]
    assert len(marker) == 1, 'no single ' + SHOCK_MARKER
    reach = float(np.linalg.norm(nifse.transform(nif.blocks[marker[0]])[0][:2]))
    assert 500 < reach < 700, ('the ring changed size', reach)
    root = nif.roots[0]
    t, R, sc = nifse.transform(nif.blocks[root])
    assert abs(sc - 1) < 1e-6
    nif.blocks[root] = nifse.set_transform(nif.blocks[root], t, R, radius / reach)
    print('caldera shockwave: Fire Storm ring, reach %.0f -> %.0f (scale %.3f)' % (reach, radius, radius / reach))
    return nif


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
    nif, charts, dens, centre, (HD, HM, stub) = build_mesh(nif)
    sr.write_texture(HD, os.path.join(out_root, *(HANDLE_TEX + '_d.dds').split('/')), 'BC7_UNORM')
    sr.write_texture(HM, os.path.join(out_root, *(HANDLE_TEX + '_m.dds').split('/')), 'BC7_UNORM')
    D, NM, D0, NM0, glows = paint(charts, dens, centre, stub)
    sr.write_texture(D, os.path.join(out_root, *(TEX + '_d.dds').split('/')), 'BC7_UNORM')
    sr.write_texture(NM, os.path.join(out_root, *(TEX + '_n.dds').split('/')), 'BC7_UNORM')
    sr.write_texture(D0, os.path.join(out_root, *(TEX + '_clean_d.dds').split('/')), 'BC7_UNORM')
    sr.write_texture(NM0, os.path.join(out_root, *(TEX + '_clean_n.dds').split('/')), 'BC7_UNORM')
    for t, G in enumerate(glows):
        sr.write_texture(G, os.path.join(out_root, *(TEX + '_g%d.dds' % t).split('/')), 'BC7_UNORM')
    out = nif.tobytes()
    back = nifse.Nif(out)
    assert back.tobytes() == out
    sr.check_refs(back)
    p = os.path.join(out_root, *OUT_MESH.split('/'))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'wb') as fh:
        fh.write(out)
    print('wrote %s (%d bytes, %d blocks)' % (p, len(out), len(back.blocks)))
    print('PyNifly reads it as', sr.readback(p))
    bsa_path = os.path.join(args.mods, VENT_BSA)
    data, listing = sr._bsa.listing(bsa_path)
    raw = sr._bsa.read(data, listing[VENT_SRC.replace('/', chr(92)).lower()])
    vent = ns.Nif(raw)
    assert vent.tobytes() == raw, 'round trip failed: ' + VENT_SRC
    print('%-48s from %s' % (VENT_SRC, os.path.basename(bsa_path)))
    out = build_vent(vent).tobytes()
    assert ns.Nif(out).tobytes() == out
    p = os.path.join(out_root, *OUT_VENT.split('/'))
    with open(p, 'wb') as fh:
        fh.write(out)
    print('wrote %s (%d bytes)' % (p, len(out)))
    _, ring = sr.load(args.mods, mods, SHOCK_SRC)
    out = build_shockwave(ring).tobytes()
    assert nifse.Nif(out).tobytes() == out
    p = os.path.join(out_root, *OUT_SHOCK.split('/'))
    with open(p, 'wb') as fh:
        fh.write(out)
    print('wrote %s (%d bytes)' % (p, len(out)))


if __name__ == '__main__':
    main()
