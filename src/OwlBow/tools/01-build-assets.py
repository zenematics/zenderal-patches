r"""Owl Bow's mesh and textures: Real Bows' Daedric bow (DecimusMaximus; Pretty Enderal Armory ships it as Firewind's
model, enderal\weapons\bows\firewind.nif, with its textures in textures\weapons\realbows\) remade in silver - never
hand-edit the outputs.

The look (curator, 2026-11-16, from rendered mocks):
  * the whole bow polished silver (Argent Verdict's silver: SILVER_RAMP, its cubemap and Complex Material values);
  * the grip's leather wrap and the cord wraps near the tips gray (GRAY), keeping their grain/stripes, with silver
    bands at their ends and silver lacing down the grip's stitched seam;
  * the black metal spike at each tip replaced by three silver talons curling toward the string, with three silver
    feathers fanned behind them on each face of the limb (talon() / feather(): generated metal ornaments);
  * the string white light faintly tinted blue (its own shape, an emissive shader);
  * no engravings (an owl / falling feather / snowflake set was drawn and removed again the same day).

The mesh: Real Bows' file keeps every block (collision, BSX, Prn = WeaponBow, the bow-draw behavior graph data,
the seven draw bones) byte for byte except the shape. PyNifly writes the two new skinned shapes (bow + ornaments,
string) into a scratch file with the original skin (global-to-skin, skin-to-bone transforms, weights, partition);
their shape, shader, texture-set, skin-instance, skin-data and skin-partition blocks are then spliced in: the bow's
group at the old shape's block indices (as an NiSkinInstance, like the original), the string's appended. The
ornaments are weighted 1.0 to the tip's limb bone (Bow_UpBone2 / Bow_LoBone2, which carry the tips), so they bend
with the draw. They take their texture from an unused corner of the atlas (ORN_UV) painted plain silver.

Outputs (in Zenderal - Patch Collection, not committed):
  meshes\Zenderal\OwlBow\OwlBow.nif
  textures\Zenderal\OwlBow\OwlBow_d.dds, _n.dds, _m.dds (Complex Material), OwlBowString_d.dds, _n.dds
The cubemap is Argent Verdict's (textures\Zenderal\ArgentVerdict\ArgentVerdict_e.dds, also in Patch Collection).
Usage: python 01-build-assets.py [--mods <MO2 mods>] [--target <mod folder>]
"""
import argparse
import importlib.util
import math
import os
import struct
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
SR = os.path.join(REPO, 'src', 'StingAndRise', 'tools')
sys.path.insert(0, SR)
_spec = importlib.util.spec_from_file_location('sr_assets', os.path.join(SR, '01-build-assets.py'))
sr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sr)
import nifse  # noqa: E402
sys.path.insert(0, sr.TOOLS['pynifly'])
from pyn.pynifly import NifFile  # noqa: E402
from pyn.nifdefs import PynBufferTypes, BSTriShapeBuf, ShaderFlags1, ShaderFlags2  # noqa: E402

MESH = 'meshes/enderal/weapons/bows/firewind.nif'
TEX_D = 'textures/weapons/realbows/DaedricBow_d.dds'
TEX_N = 'textures/weapons/realbows/DaedricBow_n.dds'
OUT_MESH = 'meshes/Zenderal/OwlBow/OwlBow.nif'
OUT_D, OUT_N, OUT_M = ('textures/Zenderal/OwlBow/OwlBow_%s.dds' % k for k in ('d', 'n', 'm'))
OUT_SD, OUT_SN = 'textures/Zenderal/OwlBow/OwlBowString_d.dds', 'textures/Zenderal/OwlBow/OwlBowString_n.dds'
CUBEMAP = 'textures\\Zenderal\\ArgentVerdict\\ArgentVerdict_e.dds'
RES = 4096                        # the atlas (Real Bows' is 2048): crisp silver at the bow's size
SILVER_RAMP = ((0.0, (0.42, 0.44, 0.47)), (0.5, (0.78, 0.79, 0.82)), (1.0, (0.97, 0.97, 0.98)))   # Argent Verdict's
GRAY = (0.30, 0.30, 0.31)         # the wraps (curator: "a gray"), times the leather/cord's own grain
COMPLEX = (0.94, 0.93, 1.0)       # silver: reflection, glossiness, metalness (Sting and Rise / Argent Verdict)
WRAP_GLOSS = 0.2                  # wraps: no reflection, matt highlights
STRING_EMIT = (0.86, 0.93, 1.0)   # white energy, slightly blue (curator)
STRING_EMIT_MULT = 2.5
# regions. The tip's metal (sleeve + spike) and the string's nock loops are the near-grey texels at |y| > 44; the
# spike is the metal past SPIKE_Y; the string is the island at u > 0.97; the grip is |y| < 13 and dark; the cord
# wraps are the striped stretch at |y| 32.5..43 (Real Bows' own wraps, measured from its texture)
TIP_Y, SPIKE_Y, GRIP_Y, CORD_Y = 44.0, 53.0, 13.0, (32.5, 43.0)
GRIP_BAND_Y, CORD_BAND_Y = 11.6, (33.4, 42.0)   # silver bands at the wraps' ends
CORD_END = 46.0                                 # the cord wrap runs to the sleeve (non-metal up to here)
CORD_TAIL = 36.0                                # from here, plain limb triangles beside the cord's diagonal end become cord
LACE_U = (0.476, 0.011)            # the grip's stitched seam column in Real Bows' atlas (u centre, half width)
ORN_UV = (0.015, 0.095, 0.32, 0.68)   # unused atlas corner (asserted empty) painted plain silver for the ornaments
TIP_BONES = {1: 'Bow_UpBone2', -1: 'Bow_LoBone2'}
# the tips (rework after the first in-game look, curator 2026-11-16: "clipping, low poly; actual white feathers; more
# definition to the talons"): Real Bows' metal (sleeve + spike) goes; a smooth ferrule lofted along the limb's own
# curve takes its place, closed by a dome; three jointed toes with keeled claws grow out of the dome; three of the
# game's hawk feathers (made white) lie flat along each face of the limb, clear of it
GRIP_FEATHERS = dict(y=13.6, lengths=(6.0, 5.4, 4.8, 4.2), fan=(-4.0, 8.0, 20.0, 32.0), root=0.22)
GRIP_BONES = {1: 'Bow_UpBone1', -1: 'Bow_LoBone1'}
SLEEVE_ROW = dict(t=(0.02, 0.22, 0.42, 0.62, 0.82), lengths=(8.0, 7.6, 7.2, 6.8, 6.4), ang=26.0)
# a row of overlapping feathers along each tip sleeve's back edge (Real Bows' tip metal, from the cord wrap's end to the
# spike's base), on both faces of both limbs, laid toward the tip and out to the back (curator 2026-11-19: the bare
# polished sleeve between the collar and the plume "needs covering with feathers on both sides of the bow", drawn as a
# row of overlapping feather tips along its top). T = fraction of the way from the cord's end to the spike base
NOCK_ARROW = dict(rest_y=4.8, rest_x=0.9, fold=(0.0, 1.0), head=0.1, head_r=0.8, shaft_r=0.3, fletch=(0.76, 0.97), fletch_h=0.32,
                  grip_front=4.7, head_past=12.0, lift=2.5)
# lift: the arrow's line rises this far from the nock to where it crosses the riser (curator 2026-11-16: in first person
# the hand grips higher than in third, and the arrow at the nock's own height ran through the fist)
HOLE = dict(r_tube=0.42, r_ring=0.72, ring_h=0.14, sides=28, reach=6.0)
# the hole through the riser on the arrow's line, lined with a silver tube, a silver ring on each face (curator
# 2026-11-16: the magical bow draws and fires its arrows through this hole). Radii across the line; the riser is
# octagonal there: flat faces and chamfers to +-0.75, sides beyond, so the ring stays on the faces; the tube clears the
# forming arrow's shaft (0.3)
# rest_x: the arrow rest inside the grip; head_past: the head's reach beyond the grip's front at full draw. Radii are the
# full-draw arrow's (designed there; the rest pose is solved and asserted inside the grip)
NOCK_EMIT_MULT = 4.0
FEATHER_SRC = 'meshes/clutter/ingredients/hawkfeather01.nif'
FEATHER_TEX = 'textures/clutter/ingredients/HawkFeatherBeak01.dds'
FEATHER_N = r'textures\clutter\ingredients\HawkFeatherBeak01_n.dds'
OUT_FD = 'textures/Zenderal/OwlBow/OwlBowFeather_d.dds'
PLUME = dict(angles=((0, 0), (18, 8), (-18, 8), (36, 16), (-36, 16), (12, -14), (-12, -14)),   # (out of plane, toward the back) deg
             lengths=(8.5, 7.8, 7.8, 6.8, 6.8, 6.4, 6.4))
COLLAR = dict(y=40.6, lengths=(7.0, 6.6, 6.2, 5.8, 5.4, 5.0), fan=(-10.0, 0.0, 10.0, 20.0, 30.0, 40.0), root=0.2)   # 6 a face   # 6 a face (curator: more feathers)
FEATHER_RAMP = ((0.0, (0.52, 0.53, 0.56)), (0.5, (0.84, 0.85, 0.87)), (1.0, (0.98, 0.98, 0.99)))

def unit(v):
    return v / np.linalg.norm(v)


def components(n, T):
    p = list(range(n))

    def f(x):
        while p[x] != x:
            p[x] = p[p[x]]
            x = p[x]
        return x
    for a, b, c in T:
        for u, v in ((a, b), (b, c)):
            ru, rv = f(u), f(v)
            if ru != rv:
                p[ru] = rv
    return np.array([f(i) for i in range(n)])


def sample(tex, uv):
    h, w = tex.shape[:2]
    return tex[((uv[..., 1] % 1) * (h - 1)).astype(int), ((uv[..., 0] % 1) * (w - 1)).astype(int)][..., :3]


def regions(V, UV, T, tex):
    """Per triangle: string (incl. the nock loops), tip metal (sleeve + spike), spike."""
    cent = V[T].mean(1)
    string = UV[T][:, :, 0].min(1) > 0.97
    w = np.array([[1 / 3, 1 / 3, 1 / 3], [.6, .2, .2], [.2, .6, .2], [.2, .2, .6]])
    S = np.stack([sample(tex, np.einsum('k,tkj->tj', ww, UV[T])) for ww in w], 1)
    grey = (np.abs(cent[:, 1]) > TIP_Y) & ((S.max(2) - S.min(2)).mean(1) < 0.06) & ~string
    r = components(len(V), T[grey])
    rid = r[T[grey][:, 0]]
    ids, cnt = np.unique(rid, return_counts=True)
    gi = np.nonzero(grey)[0]
    metal = np.zeros(len(T), bool)
    metal[gi[np.isin(rid, ids[cnt > 50])]] = True                    # the two sleeve+spike pieces
    string = string.copy()
    string[gi[~np.isin(rid, ids[cnt > 50])]] = True                  # the small grey bits = the string's nock loops
    assert sum(cnt > 50) == 2, cnt
    spike = metal & (np.abs(cent[:, 1]) > SPIKE_Y)
    return string, metal, spike


def hawk_feather(mods_dir, mods):
    """One feather (front + back face) of the game's hawk feather ingredient, in its own frame (length 1): the
    quill's foot at the origin, the quill along +x, the vane's width along y; with its UVs and source shape."""
    _, raw = sr.winner(mods_dir, [], FEATHER_SRC)       # Bethesda's own (SMIM's loose copy has no alpha property)
    d = tempfile.mkdtemp()
    p = os.path.join(d, 'hawk.nif')
    open(p, 'wb').write(raw)
    nif = NifFile(p)
    s = nif.shapes[0]
    V, T, UV = np.array(s.verts, float), np.array(s.tris), np.array(s.uvs, float)
    r = components(len(V), T)
    ids = np.unique(r)
    best = max(ids, key=lambda i: np.ptp(V[r == i], 0).max())          # the longest feather ...
    pair = [i for i in ids if np.linalg.norm(V[r == i].mean(0) - V[r == best].mean(0)) < 1.0]   # ... both faces
    sel = np.isin(r, pair)
    idx = np.nonzero(sel)[0]
    m = -np.ones(len(V), int)
    m[idx] = np.arange(len(idx))
    tri = m[T[sel[T[:, 0]]]]
    P, uv = V[idx], UV[idx]
    # the bare stem (calamus) is the end at the texture's TOP (min v): rendered 2026-11-16, after the first build
    # attached every feather by its rounded tip (curator: "the stems should be what attaches to the bow")
    base, tip = P[uv[:, 1].argmin()], P[uv[:, 1].argmax()]
    x = unit(tip - base)
    c = P - P.mean(0)
    w = np.linalg.svd(c - np.outer(c @ x, x), full_matrices=False)[2][0]
    y = unit(w - (w @ x) * x)
    zz = np.cross(x, y)
    L = np.ptp((P - base) @ x)
    Q = np.stack([(P - base) @ x, (P - base) @ y, (P - base) @ zz], 1) / L
    print('  hawk feather: %d triangles from pieces %s, length %.1f, width %.1f, depth %.2f'
          % (len(tri), pair, L, np.ptp(Q[:, 1]) * L, np.ptp(Q[:, 2]) * L))
    return Q, tri, uv, (nif, s)


def feather_texture(mods_dir, mods, out_root):
    """The hawk feather's photo made a white owl feather: its luminance onto FEATHER_RAMP (the dark base and bars
    become pale grey, the barbs' detail kept), alpha unchanged."""
    _, raw = sr.winner(mods_dir, mods, FEATHER_TEX, sr.TEX_BSAS)
    d = sr.load_image(raw)
    lum = d[..., :3] @ np.array([0.299, 0.587, 0.114])
    lo, hi = np.percentile(lum[d[..., 3] > 0.5], [2, 98])
    t = np.clip((lum - lo) / max(hi - lo, 1e-3), 0, 1) ** 0.75
    rgb = sr.ramp(t, FEATHER_RAMP)
    sr.write_texture(np.concatenate([rgb, d[..., 3:4]], -1), os.path.join(out_root, *OUT_FD.split('/')), 'BC7_UNORM')


def bow_z_extent(V, T, keep, pts_xy, radius=0.7):
    """The bow's largest |z| within `radius` (in the bow plane) of each point."""
    B = V[np.unique(T[keep])]
    d2 = ((pts_xy[:, None, :] - B[None, :, :2]) ** 2).sum(2)
    near = d2 < radius ** 2
    return np.where(near.any(1), np.where(near, np.abs(B[None, :, 2]), 0).max(1), 0)


def surface_z(S, pts_xy, grow=0.25):
    """The bow's height under each point: the largest |z| of the triangles S = (P, T) whose outline in the bow plane
    covers it (each triangle's outline grown by GROW, so a stem at a surface's edge still finds it); -1 where none."""
    P, T = S
    A, B, C = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]
    lo = np.minimum(np.minimum(A, B), C)[:, :2] - grow
    hi = np.maximum(np.maximum(A, B), C)[:, :2] + grow
    out = np.full(len(pts_xy), -1.0)
    for i, q in enumerate(pts_xy):
        m = np.nonzero((lo[:, 0] <= q[0]) & (q[0] <= hi[:, 0]) & (lo[:, 1] <= q[1]) & (q[1] <= hi[:, 1]))[0]
        if not len(m):
            continue
        a, b_, c = A[m], B[m], C[m]
        v0, v1, v2 = b_[:, :2] - a[:, :2], c[:, :2] - a[:, :2], q - a[:, :2]
        den = v0[:, 0] * v1[:, 1] - v1[:, 0] * v0[:, 1]
        ok = np.abs(den) > 1e-9
        u = np.where(ok, (v2[:, 0] * v1[:, 1] - v1[:, 0] * v2[:, 1]) / np.where(ok, den, 1), -1)
        w = np.where(ok, (v0[:, 0] * v2[:, 1] - v2[:, 0] * v0[:, 1]) / np.where(ok, den, 1), -1)
        tol = grow / np.maximum(np.linalg.norm(v0, axis=1) + np.linalg.norm(v1, axis=1), 1e-6)
        inside = ok & (u >= -tol) & (w >= -tol) & (u + w <= 1 + tol)
        if inside.any():
            z = np.abs(a[:, 2] + np.clip(u, 0, 1) * (b_[:, 2] - a[:, 2]) + np.clip(w, 0, 1) * (c[:, 2] - a[:, 2]))
            out[i] = z[inside].max()
    return out


def seat_feather(root, x, y, Q, L, face, S, layer, embed=0.08, clear=0.05, layer_rise=0.035):
    """A feather whose stem foot sits on the bow (curator 2026-11-16: "make sure each stem actually connects to the
    bow; some are floating"): the foot EMBED below the surface under it, the feather then rising along its length
    just enough to clear every surface point beneath it (plus CLEAR), the fan's layers parting toward the tips
    (LAYER x LAYER_RISE at full length). S: the surface points (the bow's own vertices + the ferrule's)."""
    along = Q[:, 0] * L
    flat = root + np.outer(along, x) + np.outer(Q[:, 1] * L, y)
    z_root = surface_z(S, root[None, :2])[0]
    assert z_root > 0.1, ('a feather stem with no bow under it', root.round(2))
    z0 = z_root - embed
    under = surface_z(S, flat[:, :2])
    curve = Q[:, 2] * L
    far = along > 0.4
    slope = max(0.0, float(((under + clear - z0 - curve)[far] / along[far]).max()))
    h = z0 + slope * along + curve + layer * layer_rise * along / L
    return flat + np.outer(h, np.array([0, 0, 1.0]) * face)


def grip_feathers(V, T, metal, string, sgn, hawk):
    """A fan of feathers on each face of the limb where it leaves the grip's silver band, lying along the limb
    toward its tip (curator 2026-11-16: "more feathers on other areas of the bow"), weighted to the limb's first
    bone so they bend with it."""
    G = GRIP_FEATHERS
    keep = ~string & ~metal
    B = V[np.unique(T[keep])]
    def centre(y):
        q = B[np.abs(B[:, 1] - y * sgn) < 1.6]
        return np.array([(q[:, 0].min() + q[:, 0].max()) / 2, y * sgn, 0.0])
    c0, c1 = centre(G['y']), centre(G['y'] + 2.5)
    tf = unit(c1 - c0)                                        # along the limb, toward its tip
    z = np.array([0, 0, 1.0])
    b = unit(np.cross(z, tf))
    b = b if b[0] > 0 else -b                                 # the limb's back
    Q, ftri, fuv, _ = hawk
    out = []
    n = len(G['fan'])
    for face in (1, -1):
        for k, (L, ang) in enumerate(zip(G['lengths'], G['fan'])):
            a = math.radians(ang)
            x = unit(tf * math.cos(a) + b * math.sin(a))
            y = unit(np.cross(z * face, x))
            P = seat_feather(c0 + b * (G['root'] * (k - (n - 1) / 2)), x, y, Q, L, face, (V, T[keep]), k)
            out.append((P, ftri if face > 0 else ftri[:, ::-1], fuv))
    return out


def tip_parts(V, T, metal, spike, string, sgn, hawk):
    """One tip: the silver ferrule, a plume of feathers from its dome (the talons went, curator 2026-11-16: "ditch
    the talons and instead add more feathers"), and a collar of feathers rooted on the gray cord wrap just before
    its end and laid toward the tip, hiding the wrap's fringed end and its junction with the ferrule (the curator's
    clipping / missing-texture crops)."""
    # Real Bows' own tip metal (sleeve + spike), painted silver, is back (curator 2026-11-16: "I don't like these odd
    # shaped ends, just remove them for something like the original bow"); the lofted ferrule is gone
    cent = V[T].mean(1)
    side_t = np.sign(cent[:, 1]) == sgn
    spv = V[np.unique(T[spike & side_t])]
    front = spv[np.argsort(np.abs(spv[:, 1]))[:10]].mean(0)          # the spike's base = the sleeve's mouth
    tf = unit(spv[np.argmax(np.abs(spv[:, 1]))] - front)
    z = np.array([0, 0, 1.0])
    b = unit(np.cross(z, tf))
    b = b if b[0] > 0 else -b                                    # the limb's back, away from the string
    silver = []
    Q, ftri, fuv, _ = hawk
    feathers = []
    tk = T[~string & ~metal]
    surf = (V, T[~string & side_t | (~string & ~side_t)])          # what a stem can sit on: the limb and the tip metal
    # the plume: stems sunk in the dome, feathers spreading out past the tip, their broad side facing the bow's side
    apex = front + tf * 0.4                                       # in the sleeve's mouth, around the spike's base
    for (az, ab), L in zip(PLUME['angles'], PLUME['lengths']):
        d = unit(tf * math.cos(math.radians(az)) * math.cos(math.radians(ab)) + z * math.sin(math.radians(az))
                 + b * math.sin(math.radians(ab)))
        w = unit(b - (b @ d) * d)
        nrm_ = np.cross(d, w)
        P = apex + np.outer(Q[:, 0] * L, d) + np.outer(Q[:, 1] * L, w) + np.outer(Q[:, 2] * L, nrm_)
        feathers.append((P, ftri, fuv))
        feathers.append((P + nrm_ * 0.01, ftri[:, ::-1], fuv))   # both faces lit
    # the collar: on each face, rooted on the wrap COLLAR['y'] in, fanned toward the tip
    keep = ~string & ~metal
    Bv = V[np.unique(T[keep])]
    def centre(y):
        q = Bv[np.abs(Bv[:, 1] - y * sgn) < 0.8]
        return np.array([(q[:, 0].min() + q[:, 0].max()) / 2, y * sgn, 0.0])
    c0, c1 = centre(COLLAR['y']), centre(COLLAR['y'] + 1.5)
    td = unit(c1 - c0)                                            # along the limb toward the tip, at the wrap's end
    bd = unit(np.cross(z, td))
    bd = bd if bd @ b > 0 else -bd
    n = len(COLLAR['fan'])
    for face in (1, -1):
        for k, (L, ang) in enumerate(zip(COLLAR['lengths'], COLLAR['fan'])):
            a = math.radians(ang)
            x = unit(td * math.cos(a) + bd * math.sin(a))
            y = unit(np.cross(z * face, x))
            P = seat_feather(c0 + bd * (COLLAR['root'] * (k - (n - 1) / 2)), x, y, Q, L, face, surf, k)
            feathers.append((P, ftri if face > 0 else ftri[:, ::-1], fuv))
    # the sleeve row: rooted on the metal along its back edge, from the cord's end to the spike base
    G = SLEEVE_ROW
    Mv = V[np.unique(T[metal & ~spike & side_t])]
    y_end = CORD_Y[1] * sgn

    def sleeve_centre(yy):
        q = Mv[np.abs(Mv[:, 1] - yy) < 2.5]
        assert len(q) >= 3, ('no sleeve at', yy)
        return np.array([(q[:, 0].min() + q[:, 0].max()) / 2, yy, 0.0]), q[:, 0].max() - q[:, 0].min()
    y_a = Mv[np.argmin(np.abs(Mv[:, 1]))][1] + sgn * 0.6           # the sleeve's start, by the cord's end
    y_b = front[1]
    for face in (1, -1):
        for k, (tt, L) in enumerate(zip(G['t'], G['lengths'])):
            yy = y_a + (y_b - y_a) * tt
            c0_, w0 = sleeve_centre(yy)
            c1_, _ = sleeve_centre(yy + sgn * 1.2)
            td_ = unit(c1_ - c0_)
            bd_ = unit(np.cross(z, td_))
            bd_ = bd_ if bd_ @ b > 0 else -bd_
            a_ = math.radians(G['ang'])
            x = unit(td_ * math.cos(a_) + bd_ * math.sin(a_))
            y = unit(np.cross(z * face, x))
            # rooted on the sleeve's own back-edge vertex at this height, pulled in a little (the sleeve bends hard,
            # so its centre +- a width fraction can land off the metal)
            near = Mv[np.abs(Mv[:, 1] - yy) < 1.5]
            edge = near[np.argmax((near - c0_) @ bd_)]
            root = np.array([edge[0], edge[1], 0.0]) - bd_ * 0.2
            P = seat_feather(root, x, y, Q, L, face, surf, len(COLLAR['fan']) + k)
            feathers.append((P, ftri if face > 0 else ftri[:, ::-1], fuv))
    return silver, feathers


def vertex_normals(P, T):
    n = np.zeros_like(P)
    f = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    for k in range(3):
        np.add.at(n, T[:, k], f)
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)


def ornament_uv(P):
    """Planar UVs inside ORN_UV (plain silver), from the part's own two longest extents."""
    c = P - P.mean(0)
    _, _, vt = np.linalg.svd(c, full_matrices=False)
    q = c @ vt[:2].T
    q = (q - q.min(0)) / np.maximum(np.ptp(q, 0), 1e-6)
    u0, u1, v0, v1 = ORN_UV
    return np.stack([u0 + (u1 - u0) * (0.1 + 0.8 * q[:, 0]), v0 + (v1 - v0) * (0.1 + 0.8 * q[:, 1])], 1)


# ---- texture -------------------------------------------------------------------------------------------------

def rasterise(V, N, UV, T, keep):
    """Per texel of the RES atlas: the triangle that covers it (-1 none) and its bow-space y."""
    H = W = RES
    tid = np.full((H, W), -1, np.int32)
    ypos = np.zeros((H, W), np.float32)
    for k in np.nonzero(keep)[0]:
        t = T[k]
        uv = UV[t] * [W, H]
        x0, y0 = np.floor(uv.min(0)).astype(int) - 1
        x1, y1 = np.ceil(uv.max(0)).astype(int) + 1
        x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, W), min(y1, H)
        if x1 <= x0 or y1 <= y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
        (ax, ay), (bx, by), (cx, cy) = uv
        den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(den) < 1e-12:
            continue
        w0 = ((by - cy) * (gx - cx) + (cx - bx) * (gy - cy)) / den
        w1 = ((cy - ay) * (gx - cx) + (ax - cx) * (gy - cy)) / den
        ok = (w0 >= -0.02) & (w1 >= -0.02) & (1 - w0 - w1 >= -0.02)
        y = w0 * V[t[0], 1] + w1 * V[t[1], 1] + (1 - w0 - w1) * V[t[2], 1]
        tid[y0:y1, x0:x1][ok] = k
        ypos[y0:y1, x0:x1][ok] = y[ok]
    return tid, ypos


def box(a, r):
    out = a.astype(np.float64)
    for ax in (0, 1):
        p = np.pad(out, [(r + 1, r) if i == ax else (0, 0) for i in range(out.ndim)], mode='edge')
        c = np.cumsum(p, axis=ax)
        out = (np.take(c, np.arange(2 * r + 1, c.shape[ax]), axis=ax) - np.take(c, np.arange(0, c.shape[ax] - 2 * r - 1), axis=ax)) / (2 * r + 1)
    return out.astype(np.float32)


def wrap_tongues(V, UV, T, tex, nrm, tid, ok, string, metal):
    """The grip wrap's UV islands each have a strip past the grip line mapped onto a lighter patch of Real Bows' atlas
    (the upper end's tongue at y 13-18, the lower limb's strip at y -14..-26 on its back), which read as plain metal
    beside the cord (curator 2026-11-19, both ends). Those texels get the same island's own wrap texels (diffuse and
    normal), shifted in v from inside its wrap part; the shifted block must land on the island's dark wrap."""
    lum = tex[..., :3].mean(2)
    t_ = np.maximum(tid, 0).ravel()
    n_ = np.bincount(t_, ok.ravel(), len(T)) + 1e-9
    tri_l = np.bincount(t_, (lum * ok).ravel(), len(T)) / n_
    tcy = np.abs(V[T].mean(1)[:, 1])
    body = ~string & ~metal
    bi = np.nonzero(body)[0]
    comp = components(len(V), T[body])[T[body][:, 0]]
    tex, nrm = tex.copy(), nrm.copy()
    res = tex.shape[0]
    pasted_cord = np.zeros(len(T), bool)
    for c in np.unique(comp):
        m = bi[comp == c]
        if not ((tri_l[m] < 0.2).mean() > 0.6 and tcy[m].min() < GRIP_Y):
            continue
        tongue, wrap = m[tcy[m] >= GRIP_Y], m[tcy[m] < GRIP_Y]
        if not len(tongue):
            continue
        M = ok & np.isin(tid, tongue)
        W = ok & np.isin(tid, wrap) & (lum < 0.2)
        ty, tx = np.nonzero(M)
        wy, wx = np.nonzero(W)
        dv = int(round(np.median(wy) - (ty.min() + ty.max()) / 2))
        sy = ty + dv
        assert (0 <= sy).all() and (sy < res).all()
        hit = W[sy, tx].mean()
        assert hit > 0.8, ('the shifted block misses the wrap', hit)
        tex[ty, tx] = tex[sy, tx]
        nrm[ty, tx] = nrm[sy, tx]
        print('  wrap tongue: %d triangles (y %.1f..%.1f), %d texels from %+d rows of the same island (%.0f%% on wrap)'
              % (len(tongue), tcy[tongue].min(), tcy[tongue].max(), len(ty), dv, 100 * hit))
    # the cord wrap's tip end: its last strip before the sleeve (y CORD_Y[1]..CORD_END) maps onto a lighter patch and was
    # painted plain silver (curator 2026-11-19, the green crops by the collar on both limbs): the cord's own texels in
    side = np.sign(V[T].mean(1)[:, 1])
    # the cord's own texture detail per triangle (paint's cord test): the wrap ends on a diagonal, so the wood wedge past
    # it reaches below y CORD_Y[1] too
    sc = res / 2048.0
    energy = box(np.abs(lum - box(lum, int(4 * sc))), int(7 * sc))
    tri_e = np.bincount(t_, (energy * ok).ravel(), len(T)) / n_
    for c in np.unique(comp):
        m = bi[comp == c]
        cord = m[(tcy[m] > CORD_Y[0] + 2) & (tcy[m] < CORD_Y[1] - 1) & (tri_e[m] > 0.05)]
        if len(cord) < 10:
            continue
        for sg in (1, -1):
            tongue = m[(((tcy[m] >= CORD_Y[1]) & (tcy[m] < CORD_END)) | ((tcy[m] >= CORD_TAIL) & (tri_e[m] <= 0.05)))
                       & (tcy[m] < CORD_END) & (side[m] == sg)]
            src = cord[side[cord] == sg]
            if not len(tongue) or not len(src):
                continue
            # per triangle, the source block (a shift inside the same island) whose texels all land on the
            # cord and best match the cord's typical brightness and grain (2026-11-19: one shift for all of them put a
            # dark, smooth block on the inner bend's bevel facet, which read as a black panel)
            W = ok & np.isin(tid, src)
            wl, we = np.median(lum[W]), np.median(energy[W])
            lum0, en0 = lum.copy(), energy.copy()
            wy_all, wx_all = np.nonzero(W)
            rng = np.random.default_rng(1)
            hits, worst = [], 0.0
            for t in tongue:
                ty, tx = np.nonzero(ok & (tid == t))
                if not len(ty):
                    continue
                best = None
                cy0, cx0 = int(ty.mean()), int(tx.mean())
                for k in rng.choice(len(wy_all), size=min(600, len(wy_all)), replace=False):
                    dv, du = int(wy_all[k]) - cy0, int(wx_all[k]) - cx0
                    sy, sx = ty + dv, tx + du
                    if sy.min() < 0 or sy.max() >= res or sx.min() < 0 or sx.max() >= res:
                        continue
                    on = W[sy, sx].mean()
                    if on < 0.95:
                        continue
                    score = abs(lum0[sy, sx].mean() - wl) / max(wl, 1e-3) + abs(en0[sy, sx].mean() - we) / max(we, 1e-3)
                    if best is None or score < best[0]:
                        best = (score, (dv, du), on)
                assert best is not None, ('no cord block for triangle', int(t))
                sy, sx = ty + best[1][0], tx + best[1][1]
                tex[ty, tx] = tex[sy, sx]
                nrm[ty, tx] = nrm[sy, sx]
                hits.append(best[2])
                worst = max(worst, best[0])
            print('  cord end: %d triangles (y %.1f..%.1f), each from its best-matching cord block (worst mismatch %.2f)'
                  % (len(tongue), sg * tcy[tongue].min(), sg * tcy[tongue].max(), worst))
            pasted_cord[tongue] = True
    return tex, nrm, pasted_cord


def paint(V, N, UV, T, tex, nrm, string, metal):
    from PIL import Image
    if tex.shape[0] != RES:
        tex = np.asarray(Image.fromarray((tex * 255).astype(np.uint8)).resize((RES, RES), Image.LANCZOS), np.float32) / 255
        nrm = np.asarray(Image.fromarray((nrm * 255).astype(np.uint8)).resize((RES, RES), Image.LANCZOS), np.float32) / 255
    tid, ypos = rasterise(V, N, UV, T, ~string)
    ok = tid >= 0
    tex, nrm, pasted_cord = wrap_tongues(V, UV, T, tex, nrm, tid, ok, string, metal)
    ay = np.abs(ypos)
    sc = RES / 2048.0
    lum = tex[..., :3].mean(2)
    energy = box(np.abs(lum - box(lum, int(4 * sc))), int(7 * sc))
    t_ = np.maximum(tid, 0).ravel()
    n_ = np.bincount(t_, ok.ravel(), len(T)) + 1e-9
    tri_l = np.bincount(t_, (lum * ok).ravel(), len(T)) / n_       # per triangle: texel tests left flecks
    tri_e = np.bincount(t_, (energy * ok).ravel(), len(T)) / n_
    tcy = np.abs(V[T].mean(1)[:, 1])
    grip_tri = (tri_l < 0.2) & (tcy < GRIP_Y) & ~metal
    # the wrap's own UV islands, whole (curator 2026-11-19: its end tongue past y 13, near the grip feathers, came out
    # plain silver): every dark triangle of an island that is mostly dark and reaches the grip
    body = ~string & ~metal
    bi = np.nonzero(body)[0]
    comp = components(len(V), T[body])[T[body][:, 0]]
    for c in np.unique(comp):
        m = bi[comp == c]
        if (tri_l[m] < 0.2).mean() > 0.6 and tcy[m].min() < GRIP_Y:
            add = m[(tri_l[m] < 0.2) & ~grip_tri[m]]
            grip_tri[add] = True
            print('  grip wrap island: %d triangles, y %.1f..%.1f, +%d past the grip line' % (len(m), tcy[m].min(), tcy[m].max(), len(add)))
    cord_tri = ((tcy > CORD_Y[0]) & (tcy < CORD_END) & (tri_e > 0.05) | pasted_cord) & ~metal
    if os.environ.get('OWLBOW_DEBUG_TRIS'):
        for i in map(int, os.environ['OWLBOW_DEBUG_TRIS'].split(',')):
            print('  DEBUG tri %d: y %.1f lum %.2f energy %.3f cord %s grip %s metal %s texels %d' % (i, tcy[i], tri_l[i], tri_e[i], cord_tri[i], grip_tri[i], metal[i], (tid == i).sum()))
    grip = ok & grip_tri[np.maximum(tid, 0)]
    cord = ok & cord_tri[np.maximum(tid, 0)]
    wrap = grip | cord
    uu = np.broadcast_to(np.arange(RES, dtype=np.float32)[None, :] / RES, (RES, RES))
    lace = grip & (np.abs(uu - LACE_U[0]) < LACE_U[1]) & (lum > box(lum, int(6 * sc)) + 0.015)
    band = (grip & (ay > GRIP_BAND_Y) & (ay < GRIP_Y)) | (cord & (ay < CORD_BAND_Y[0]))   # cord's tip end: wrap to the sleeve (curator 2026-11-19)
    lining = lace | band
    u0, u1, v0, v1 = ORN_UV
    orn = np.zeros((RES, RES), bool)
    orn[int(v0 * RES):int(v1 * RES), int(u0 * RES):int(u1 * RES)] = True
    assert not (orn & ok).any(), 'the ornament patch overlaps a used island'
    detail = np.clip(0.5 + (lum - box(lum, int(12 * sc))) * 1.2, 0, 1)
    rgb = sr.ramp(0.55 + 0.15 * (detail - 0.5), SILVER_RAMP)
    for m, k in ((grip, 70), (cord, 70)):
        g = np.clip(lum / max(np.percentile(lum[m], k), 1e-3), 0, 1.15)
        rgb = np.where(m[..., None], np.array(GRAY) * (0.55 + 0.6 * g[..., None]), rgb)
    rgb = np.where(lining[..., None], sr.ramp(np.full(lining.shape, 0.75), SILVER_RAMP), rgb)
    rgb = np.where(orn[..., None], sr.ramp(np.full(orn.shape, 0.6), SILVER_RAMP), rgb)
    silver = (ok | orn) & ~(wrap & ~lining)
    # normal: Real Bows' own on the wraps; silver = its relief softened to a third; the ornament patch flat.
    # alpha (highlight mask): silver bright, wraps matt
    n_out = nrm.copy()
    flat = np.array([0.5, 0.5, 1.0], np.float32)
    n_out[..., :3] = np.where(silver[..., None], flat + (nrm[..., :3] - flat) * 0.33, nrm[..., :3])
    n_out[..., :3] = np.where(orn[..., None], flat, n_out[..., :3])
    n_out[..., 3] = np.where(silver, 0.85, 0.15)
    cm = np.stack([COMPLEX[0] * silver, COMPLEX[1] * silver + WRAP_GLOSS * ~silver, COMPLEX[2] * silver,
                   np.zeros(silver.shape)], -1).astype(np.float32)
    print('owl bow atlas %d: silver %.1f%%, grip %.1f%%, cord %.1f%%, lining %.2f%%, ornament patch %.2f%%'
          % (RES, 100 * (silver & ok).mean(), 100 * grip.mean(), 100 * cord.mean(), 100 * lining.mean(), 100 * orn.mean()))
    return rgb, n_out, cm


def write_textures(out_root, rgb, n_out, cm):
    j = lambda rel: os.path.join(out_root, *rel.split('/'))
    sr.write_texture(rgb, j(OUT_D), 'BC7_UNORM')
    sr.write_texture(n_out, j(OUT_N), 'BC7_UNORM')
    sr.write_texture(cm, j(OUT_M), 'BC7_UNORM')
    back = sr.load_image(open(j(OUT_M), 'rb').read())
    mip = sr.smallest_mip(j(OUT_M))
    eps = 4.0 / 255.0
    # Bottled Shaders' Complex Material test, on the 1x1 mip it samples (see Sting and Rise's texconv trap)
    assert back[..., 3].max() <= eps and mip[3] < 1 - eps, 'alpha lost: the mask would not be complex'
    assert max(abs(mip[0] - mip[1]), abs(mip[0] - mip[2]), abs(mip[1] - mip[2])) >= 2 * eps, 'grey 1x1 mip %s' % mip
    s = np.ones((64, 64, 3), np.float32) * np.array(STRING_EMIT)
    sr.write_texture(s, j(OUT_SD), 'BC7_UNORM')
    fl = np.ones((64, 64, 4), np.float32) * np.array([0.5, 0.5, 1.0, 0.6])
    sr.write_texture(fl, j(OUT_SN), 'BC7_UNORM')
    print('textures written; complex mask 1x1 mip', ' '.join('%.3f' % v for v in mip))


# ---- mesh ------------------------------------------------------------------------------------------------------

def string_full_draw(src_nif):
    """The rigid motion of Bow_StringBone1 from the bind pose to full draw, as a 4x4 matrix: forward kinematics of the
    bow's own skeleton on the last frame of its draw animation (meshes\\weapons\\bow\\animations\\bow_drawheavy.hkx,
    the vanilla bow behavior's clip, read from Skyrim - Animations.bsa; its last frame = bow_idledrawn's), times the
    inverse of the bone's bind world transform from the bow nif. The string halves SWING about the limb tips (about
    38 degrees), they do not slide: a straight-back model put the arrow's back end ~12 units above the fingers."""
    sys.path.insert(0, os.path.join(sr.TOOLS['pynifly'], 'hkx'))
    import anim_skyrim
    d, l = _bsa_listing('Skyrim - Animations.bsa')
    tmp = tempfile.mkdtemp()
    paths = {}
    for n in ('skeleton.hkx', 'bow_drawheavy.hkx'):
        key = [k for k in l if k.endswith(chr(92) + n) and chr(92) + 'weapons' + chr(92) + 'bow' + chr(92) in k]
        assert len(key) == 1, (n, key)
        paths[n] = os.path.join(tmp, n)
        open(paths[n], 'wb').write(_bsa_read(d, l[key[0]]))
    sk = anim_skyrim.load_skyrim_skeleton(paths['skeleton.hkx'])
    names = [b if isinstance(b, str) else getattr(b, 'name', str(b)) for b in sk.bones]
    anim = anim_skyrim.load_skyrim_animation(paths['bow_drawheavy.hkx'])
    last = len(anim.tracks[0].translations) - 1

    def qm(q):
        x, y, z, w = q
        return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                         [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                         [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    W = []
    for i, p in enumerate(sk.parents):
        tr = anim.tracks[i]
        M = np.eye(4)
        M[:3, :3] = qm(tr.rotations[last])
        M[:3, 3] = tr.translations[last]
        W.append(M if p < 0 else W[p] @ M)

    def bind(name):
        nd = src_nif.nodes[name]
        M = np.eye(4)
        M[:3, :3] = np.array(nd.transform.rotation).reshape(3, 3)
        M[:3, 3] = nd.transform.translation
        par = nd.parent
        return (bind(par.name) if par is not None and par.name in names else np.eye(4)) @ M
    i = names.index('Bow_StringBone1')
    mid = names.index('Bow_MidBone')
    assert np.allclose(W[mid], bind('Bow_MidBone'), atol=1e-2), 'the riser moves in the draw animation'
    full = W[i] @ np.linalg.inv(bind('Bow_StringBone1'))
    W = []
    for j, p in enumerate(sk.parents):                     # the same at half the clip: the arrow half formed
        tr = anim.tracks[j]
        M = np.eye(4)
        M[:3, :3] = qm(tr.rotations[last // 2])
        M[:3, 3] = tr.translations[last // 2]
        W.append(M if p < 0 else W[p] @ M)
    return full, W[i] @ np.linalg.inv(bind('Bow_StringBone1'))


def _bsa_listing(name):
    sys.path.insert(0, os.path.join(REPO, 'src', 'Prophecy', 'tools'))
    import _bsa
    d, l = _bsa.listing(os.path.join(sr.DATA, name))
    return d, l


def _bsa_read(d, entry):
    import _bsa
    return _bsa.read(d, entry)


def nock_arrow(V, T, UV, string, s, Ms, Mh):
    """The arrow that forms as the string is drawn (curator 2026-11-16): at full draw (the bow animation's last
    frame, Ms) it lies from the string's nock K to HEAD_PAST beyond the grip's front, along K -> arrow rest; at rest
    it is folded inside the grip, at the arrow rest. Each vertex is weighted f to Bow_StringBone1 and 1 - f to
    Bow_MidBone (static), so under linear blend skinning its full-draw position is f Ms(v) + (1 - f) v = A(f) v + f t.
    The arrow is DESIGNED in its full-draw pose and every vertex's rest position solved: v = A(f)^-1 (P - f t), with
    f per ring chosen so the two ends rest at the arrow rest (f_n for the nock, f_h for the head, linear between).
    So at full draw the arrow is exactly the designed one (round, aligned with the fingers), wherever the string
    goes; between rest and full draw it forms along the way."""
    A_ = NOCK_ARROW
    sv = np.unique(T[string])
    weights = {}
    for b in s.bone_names:
        for vi, w in s.bone_weights[b]:
            weights.setdefault(vi, {})[b] = w
    ring = sv[np.abs(V[sv, 1] - A_['rest_y']) < 0.05]
    assert len(ring) >= 4, ring
    assert all(weights[r] == {'Bow_StringBone1': 1.0} for r in ring), 'the nock ring is not on Bow_StringBone1 alone'
    N = V[ring].mean(0)
    R0 = np.array([A_['rest_x'], N[1] + A_['lift'], 0.0])          # the arrow rest, inside the grip (the hole's line)
    FOLD = np.array([A_['fold'][0], A_['fold'][1], 0.0])            # where the folded arrow sits: the grip's thick middle
    R, t = Ms[:3, :3], Ms[:3, 3]
    K = R @ N + t                                                   # the nock at full draw
    u = unit(R0 - K)                                                # the arrow's line at full draw (nock -> head)
    global ARROW_LINE
    ARROW_LINE = (R0, u)
    H = R0 + u * ((A_['grip_front'] - R0[0]) / max(u[0], 1e-3) + A_['head_past'])

    def amat(f):
        return f * R + (1 - f) * np.eye(3)

    def rest_of(P, f):
        return np.linalg.solve(amat(f), P - f * t)

    # the riser's own shape: per height y, its x range and z half-thickness (Real Bows' riser vertices)
    riser = V[np.unique(T[~string])]
    riser = riser[np.abs(riser[:, 1]) < 12]

    # inside test against the riser's own triangles: a point is inside when it is between the surface above and the
    # surface below it (rays along +-z through the closed riser), by at least MARGIN on both
    rt = T[~string]
    rt = rt[np.abs(V[rt].mean(1)[:, 1]) < 14]
    Ta, Tb, Tc = V[rt[:, 0]], V[rt[:, 1]], V[rt[:, 2]]
    lo2 = np.minimum(np.minimum(Ta, Tb), Tc)[:, :2]
    hi2 = np.maximum(np.maximum(Ta, Tb), Tc)[:, :2]

    def z_hits(q):
        m = np.nonzero((lo2[:, 0] <= q[0]) & (q[0] <= hi2[:, 0]) & (lo2[:, 1] <= q[1]) & (q[1] <= hi2[:, 1]))[0]
        out = []
        for i in m:
            a2, b2, c2 = Ta[i], Tb[i], Tc[i]
            v0, v1, v2 = b2[:2] - a2[:2], c2[:2] - a2[:2], q[:2] - a2[:2]
            den = v0[0] * v1[1] - v1[0] * v0[1]
            if abs(den) < 1e-12:
                continue
            u_ = (v2[0] * v1[1] - v1[0] * v2[1]) / den
            w_ = (v0[0] * v2[1] - v2[0] * v0[1]) / den
            if u_ >= 0 and w_ >= 0 and u_ + w_ <= 1:
                out.append(a2[2] + u_ * (b2[2] - a2[2]) + w_ * (c2[2] - a2[2]))
        return out

    def outside(Q, margin=0.15):
        tot = 0.0
        for q in Q:
            zs = z_hits(q)
            above = [z for z in zs if z > q[2]]
            below = [z for z in zs if z < q[2]]
            if not above or not below:
                tot += 5.0
                continue
            tot += max(0.0, q[2] + margin - min(above)) + max(0.0, max(below) - q[2] + margin)
        return tot

    fs = np.linspace(-2.5, 3.0, 551)

    Rh, th = Mh[:3, :3], Mh[:3, 3]
    K_half = Rh @ N + th
    H_half = R0 + (H - R0) * 0.5

    def best_f(Pring, tt):
        # the travel factor whose folded ring sits inside the riser, then whose position at half draw lies nearest
        # the half-formed arrow (from the string's real half-draw nock to a head half way out)
        tgt = H_half + (K_half - H_half) * tt
        def score(f):
            r = [rest_of(p, f) for p in Pring]
            c = np.mean(r, 0)
            half = f * (Rh @ c + th) + (1 - f) * c
            return (round(outside(r), 3), np.linalg.norm(half - tgt))
        return min(fs, key=score)
    # the arrow at full draw: rings along K -> H (t = 1 at the nock), cross-sections perpendicular to the axis
    ax = unit(H - K)
    e1 = unit(np.cross(ax, [0, 0, 1.0]))
    e2 = np.cross(e1, ax)
    L = np.linalg.norm(H - K)

    def radius(tt):
        if tt < A_['head']:
            return A_['head_r'] * (tt / A_['head']) ** 0.8
        if tt < A_['head'] + 0.02:
            return A_['shaft_r'] + (A_['head_r'] - A_['shaft_r']) * (1 - (tt - A_['head']) / 0.02)
        return A_['shaft_r']
    pts, f_of, tris = [], [], []
    sides = 10
    ts = np.concatenate([np.linspace(0, A_['head'] + 0.02, 8), np.linspace(A_['head'] + 0.04, 1, 14)])
    f_ring = []
    for k, tt in enumerate(ts):
        c = H + (K - H) * tt
        r = radius(tt)
        ringp = [c + (e1 * math.cos(2 * math.pi * j / sides) + e2 * math.sin(2 * math.pi * j / sides)) * r
                 for j in range(sides)]
        fin = [c + (e1 * math.cos(2 * math.pi * fi / 3 + math.pi / 6) + e2 * math.sin(2 * math.pi * fi / 3 + math.pi / 6))
               * (A_['shaft_r'] + A_['fletch_h']) for fi in range(3)] if tt >= A_['fletch'][0] - 0.02 else []
        f = best_f(np.array(ringp + fin), tt)
        f_ring.append(f)
        pts += ringp
        f_of += [f] * sides
    f_n, f_h = f_ring[-1], f_ring[0]
    f_at = lambda tt: float(np.interp(tt, ts, f_ring))
    for k in range(len(ts) - 1):
        for j in range(sides):
            a0, a1 = k * sides + j, k * sides + (j + 1) % sides
            tris += [(a0, a1, a0 + sides), (a1, a1 + sides, a0 + sides)]
    for fi in range(3):                                             # three fletching fins near the nock
        q = 2 * math.pi * fi / 3 + math.pi / 6
        off = e1 * math.cos(q) + e2 * math.sin(q)
        base = len(pts)
        for tt, h in ((A_['fletch'][0], 0.0), (A_['fletch'][0] + 0.06, A_['fletch_h']), (A_['fletch'][1], A_['fletch_h']),
                      (A_['fletch'][1], 0.0)):
            c = H + (K - H) * tt
            for lift in (A_['shaft_r'], A_['shaft_r'] + h):
                pts.append(c + off * lift)
                f_of.append(best_f(np.array([c + off * lift]), tt))     # each fin vertex folds on its own
        for a, b2 in ((0, 2), (2, 4), (4, 6)):
            tris += [(base + a, base + b2, base + a + 1), (base + a + 1, base + b2, base + b2 + 1)]
            tris += [(base + a, base + a + 1, base + b2), (base + a + 1, base + b2 + 1, base + b2)]
    P_full = np.array(pts)
    rest = np.array([rest_of(p, f) for p, f in zip(P_full, f_of)])
    # at rest every vertex must hide inside the grip (riser x -2.4..2.3, z +-1.08 around the arrow rest)
    lo, hi = rest.min(0), rest.max(0)
    bad = outside(rest, margin=0.0)
    print('  forming arrow: full draw %.1f long, nock K %s, f nock %.2f / head %.2f; rest box x %.2f..%.2f y %.2f..%.2f'
          ' z %.2f..%.2f; outside the riser by %.3f in all' % (L, K.round(2), f_n, f_h, lo[0], hi[0], lo[1], hi[1],
                                                              lo[2], hi[2], bad))
    if bad >= 0.05:
        per = [(outside([q], 0.0), i, q.round(2)) for i, q in enumerate(rest)]
        per.sort(key=lambda x: -x[0])
        print('   worst:', [(round(a, 2), i, list(q)) for a, i, q in per[:8]], 'rings f', np.round(f_ring, 2))
    assert bad < 0.05, 'the folded arrow pokes out of the grip'
    back = np.array([f * (R @ v + t) + (1 - f) * v for v, f in zip(rest, f_of)])
    assert np.abs(back - P_full).max() < 1e-4
    nrm = vertex_normals(rest, np.array(tris))
    wts = [[('Bow_StringBone1', f), ('Bow_MidBone', 1 - f)] for f in f_of]
    return rest, np.array(tris), nrm, wts


def signed_weights(nif, shape_name, true_w):
    """Write the forming arrow's signed weights into its skin blocks. PyNifly drops a negative weight, so the arrow
    is written with each one's absolute value and fixed here: NiSkinData's per-bone lists, the partition's float
    weights and its vertex data's half-float weights (what the engine skins with). true_w: per vertex
    {bone name: weight}. Asserts every vertex's weights sum to 1 afterwards."""
    k = [k for k in nif.find('BSTriShape') if nif.string(struct.unpack_from('<i', nif.blocks[k], 0)[0]) == shape_name]
    assert len(k) == 1
    o = nifse.av_fields(nif.blocks[k[0]])['end']
    skin = struct.unpack_from('<i', nif.blocks[k[0]], o + 16)[0]
    data, part = struct.unpack_from('<ii', nif.blocks[skin], 0)
    nb = struct.unpack_from('<I', nif.blocks[skin], 12)[0]
    bnames = [nif.string(struct.unpack_from('<i', nif.blocks[b], 0)[0])
              for b in struct.unpack_from('<%di' % nb, nif.blocks[skin], 16)]
    # NiSkinData: skin transform (52), bones, has-weights, per bone: transform (52) + sphere (16) + count + (idx, w)
    d = nif.blocks[data]
    i = 52
    nbones, hasw = struct.unpack_from('<IB', d, i)
    assert nbones == nb and hasw == 1
    i += 5
    fixed = 0
    for bi in range(nbones):
        i += 68
        nv = struct.unpack_from('<H', d, i)[0]
        i += 2
        for j in range(nv):
            vi, w = struct.unpack_from('<Hf', d, i + 6 * j)
            want = true_w[vi].get(bnames[bi], 0.0)
            assert abs(abs(want) - w) < 1e-3, (vi, bnames[bi], want, w)
            if want < 0:
                struct.pack_into('<f', d, i + 6 * j + 2, want)
                fixed += 1
        i += 6 * nv
    # NiSkinPartition: header, global vertex data, then the one partition
    p = nif.blocks[part]
    npart, dsz, vsz, desc = struct.unpack_from('<IIIQ', p, 0)
    assert npart == 1
    _, off, vs = nifse._layout(desc)
    assert vs == vsz
    sk = off(7)                                           # skin data: 4 half weights + 4 bone indices
    i = 20 + dsz
    nv, nt, nbn, nst, nwpv = struct.unpack_from('<5H', p, i)
    i += 10
    pbones = struct.unpack_from('<%dH' % nbn, p, i)
    i += 2 * nbn
    assert p[i] == 1
    vmap = struct.unpack_from('<%dH' % nv, p, i + 1)
    i += 1 + 2 * nv
    assert p[i] == 1
    wat = i + 1
    i = wat + 4 * nv * nwpv + 2 * nst
    assert p[i] == 1 and nst == 0
    i += 1 + 6 * nt
    assert p[i] == 1
    bidx = np.frombuffer(bytes(p[i + 1:i + 1 + nv * nwpv]), np.uint8).reshape(nv, nwpv)
    for pv in range(nv):
        gv = vmap[pv]
        tw = true_w[gv]
        for slot in range(nwpv):
            # the partition's float weights follow ITS bone index table ...
            fw = struct.unpack_from('<f', p, wat + 4 * (pv * nwpv + slot))[0]
            if fw != 0:
                struct.pack_into('<f', p, wat + 4 * (pv * nwpv + slot), tw.get(bnames[pbones[bidx[pv, slot]]], 0.0))
            # ... the vertex data's half weights follow the vertex's own 4 index bytes
            at = 20 + gv * vsz + sk
            hw = struct.unpack_from('<e', p, at + 2 * slot)[0]
            if hw != 0:
                name = bnames[pbones[p[at + 8 + slot]]]
                struct.pack_into('<e', p, at + 2 * slot, tw.get(name, 0.0))
        s_ = sum(struct.unpack_from('<e', p, 20 + gv * vsz + sk + 2 * s)[0] for s in range(nwpv))
        assert abs(s_ - 1.0) < 2e-2, (gv, s_, tw)
    print('  forming arrow: %d negative skin-data weights written; every vertex sums to 1' % fixed)


ARROW_LINE = None


def arrow_hole(g, R0, a):
    """Cut a round hole through the riser along the arrow's line (R0, a) in the bow group g (P, UV, N, T, W) and add a
    silver tube lining it and a raised silver ring on each face. Per face, the riser triangles reaching within r_ring
    of the line are replaced by a fan between their own outer boundary (same positions: no cracks with the rest) and a
    circle of radius r_tube on the original surface; the tube joins the two circles. Every new vertex takes the UV and
    bone weights of the surface under it, so the hole bends with the riser."""
    H = HOLE
    e1 = unit(np.cross(a, [0.0, 0.0, 1.0]))
    e2 = np.cross(a, e1)
    P, T = g['P'], g['T']
    nP0 = len(P)

    def q2(X):
        d = np.asarray(X) - R0
        return np.stack([d @ e1, d @ e2], -1)

    def ang(X):
        q = q2(X)
        return math.atan2(q[1], q[0])
    tri3 = P[T]
    n = np.cross(tri3[:, 1] - tri3[:, 0], tri3[:, 2] - tri3[:, 0])
    n = n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    along = (tri3.mean(1) - R0) @ a
    Q = q2(tri3.reshape(-1, 3)).reshape(-1, 3, 2)

    def tri_hits_disk(qs, r):
        a2, b2, c2 = qs

        def side(p0, p1):
            return (p1[0] - p0[0]) * (0 - p0[1]) - (p1[1] - p0[1]) * (0 - p0[0])
        s1, s2, s3 = side(a2, b2), side(b2, c2), side(c2, a2)
        if (s1 >= 0 and s2 >= 0 and s3 >= 0) or (s1 <= 0 and s2 <= 0 and s3 <= 0):
            return True
        for p0, p1 in ((a2, b2), (b2, c2), (c2, a2)):
            d = p1 - p0
            t = np.clip(-(p0 @ d) / max(d @ d, 1e-12), 0, 1)
            if np.linalg.norm(p0 + t * d) < r:
                return True
        return False
    near = np.nonzero(np.abs(along) < H['reach'])[0]
    hit = np.array([i for i in near if tri_hits_disk(Q[i], H['r_ring'] + 0.02)], int)
    facing = n[hit] @ a
    assert np.all(np.abs(facing) > 0.3), ('a side face reaches the hole', facing.round(2))
    newP, newUV, newW, newT, want = [], [], [], [], []

    def vert(p, uv, w):
        newP.append(np.asarray(p, float))
        newUV.append(np.asarray(uv, float))
        newW.append(list(w))
        return nP0 + len(newP) - 1

    def tri(i, j, k, d):
        newT.append((i, j, k))
        want.append(d)
    circles = {}
    silver = []
    ns = H['sides']
    th = [2 * math.pi * k / ns - math.pi for k in range(ns)]

    def rad(t_):
        return e1 * math.cos(t_) + e2 * math.sin(t_)
    for sgn in (1, -1):
        face = hit[np.sign(facing) == sgn]
        assert len(face), sgn

        def surface(q, face=face):
            for i in face:
                A2, B2, C2 = Q[i]
                m = np.array([[B2[0] - A2[0], C2[0] - A2[0]], [B2[1] - A2[1], C2[1] - A2[1]]])
                if abs(np.linalg.det(m)) < 1e-12:
                    continue
                u_, v_ = np.linalg.solve(m, q - A2)
                if u_ >= -1e-6 and v_ >= -1e-6 and u_ + v_ <= 1 + 1e-6:
                    b = np.array([1 - u_ - v_, u_, v_])
                    vi = T[i]
                    w = {}
                    for k, bb in zip(vi, b):
                        for bone, x in g['W'][k]:
                            w[bone] = w.get(bone, 0.0) + bb * x
                    return b @ P[vi], b @ g['UV'][vi], sorted((bn, x) for bn, x in w.items() if x > 1e-6)
            raise AssertionError('no surface under %s on face %d' % (q, sgn))
        edges = {}
        for i in face:
            for x, y in ((T[i][0], T[i][1]), (T[i][1], T[i][2]), (T[i][2], T[i][0])):
                k = (min(x, y), max(x, y))
                edges[k] = edges.get(k, 0) + 1
        bnd = {k for k, c in edges.items() if c == 1}
        loop = sorted({v for k in bnd for v in k}, key=lambda v: ang(P[v]))
        for x, y in zip(loop, loop[1:] + loop[:1]):
            assert (min(x, y), max(x, y)) in bnd, 'the cut boundary is not star-shaped around the line'
        assert min(np.linalg.norm(q2(P[loop]), axis=1)) > H['r_ring'], 'the boundary comes inside the ring'
        circ = []
        for t_ in th:
            p, uv, w = surface(H['r_tube'] * np.array([math.cos(t_), math.sin(t_)]))
            circ.append(vert(p, uv, w))
        circles[sgn] = circ
        outer = [vert(P[v], g['UV'][v], g['W'][v]) for v in loop]
        oa = [ang(P[v]) for v in loop]
        no = len(outer)
        # zipper between the outer loop and the circle, both sorted by angle from -pi
        i = j = 0
        while i < no or j < ns:
            na = oa[i + 1] if i + 1 < no else oa[0] + 2 * math.pi
            nc = th[j + 1] if j + 1 < ns else th[0] + 2 * math.pi
            if j >= ns or (i < no and na <= nc):
                tri(outer[i % no], outer[(i + 1) % no], circ[j % ns], sgn * a)
                i += 1
            else:
                tri(circ[j % ns], circ[(j + 1) % ns], outer[i % no], sgn * a)
                j += 1
        # the raised ring: inner wall from the circle up, top annulus, outer wall down to the surface at r_ring
        c_in, top_in, top_out, base_out = [], [], [], []
        for k, t_ in enumerate(th):
            d2 = np.array([math.cos(t_), math.sin(t_)])
            p_i = newP[circ[k] - nP0]
            w_i = newW[circ[k] - nP0]
            po, _, wo = surface(H['r_ring'] * d2)
            c_in.append(vert(p_i, (0, 0), w_i))
            top_in.append(vert(p_i + sgn * a * H['ring_h'], (0, 0), w_i))
            top_out.append(vert(po + sgn * a * H['ring_h'], (0, 0), wo))
            base_out.append(vert(po - sgn * a * 0.03, (0, 0), wo))
        silver.append(c_in + top_in + top_out + base_out)
        for k in range(ns):
            k2 = (k + 1) % ns
            for (x0, x1), (y0, y1), d in (((c_in[k], c_in[k2]), (top_in[k], top_in[k2]), -rad(th[k])),
                                          ((top_in[k], top_in[k2]), (top_out[k], top_out[k2]), sgn * a),
                                          ((top_out[k], top_out[k2]), (base_out[k], base_out[k2]), rad(th[k]))):
                tri(x0, x1, y0, d)
                tri(x1, y1, y0, d)
    # the tube: its own copies of both circles, front to back, facing the line
    tf = [vert(newP[c - nP0], (0, 0), newW[c - nP0]) for c in circles[1]]
    tb = [vert(newP[c - nP0], (0, 0), newW[c - nP0]) for c in circles[-1]]
    silver.append(tf + tb)
    for k in range(ns):
        k2 = (k + 1) % ns
        d = -rad(th[k])
        tri(tf[k], tf[k2], tb[k], d)
        tri(tf[k2], tb[k2], tb[k], d)
    newP = np.array(newP)
    allP = np.vstack([P, newP])
    newT = np.array(newT)
    flipped = 0
    for k, (t3, d) in enumerate(zip(newT, want)):
        nn = np.cross(allP[t3[1]] - allP[t3[0]], allP[t3[2]] - allP[t3[0]])
        if nn @ d < 0:
            newT[k] = t3[[0, 2, 1]]
            flipped += 1
    newUV = np.array(newUV, float)
    for part in silver:
        idx = np.array(part) - nP0
        newUV[idx] = ornament_uv(newP[idx])
    keep = np.ones(len(T), bool)
    keep[hit] = False
    allT = np.vstack([T[keep], newT])
    g['P'] = allP
    g['UV'] = np.vstack([g['UV'], newUV])
    g['W'] = list(g['W']) + newW
    g['T'] = allT
    g['N'] = np.vstack([g['N'], vertex_normals(allP, allT)[nP0:]])
    span = (newP - R0) @ a
    cen = R0 + a * ((np.array([newP[c - nP0] for c in circles[1]]) - R0) @ a).mean()
    print('  arrow hole: %d riser triangles replaced (front %d, back %d); hole centre %s, through %.2f..%.2f along the'
          ' line; ring r %.2f, tube r %.2f; %d new vertices'
          % (len(hit), (facing > 0).sum(), (facing < 0).sum(), cen.round(2), span.min(), span.max(), H['r_ring'],
             H['r_tube'], len(newP)))


NOCK_TRUE_WEIGHTS = None
GROUP_NAMES = ('OwlBow', 'OwlBowString', 'OwlBowFeathers', 'OwlBowNockArrow')


def build_shapes(src_nif, string, metal, spike, V, UV, T, hawk):
    """The bow (minus Real Bows' tip metal and the string, plus the ferrules, toes and claws), the string, and the
    feathers, as PyNifly shapes in a scratch nif. Returns the scratch path."""
    s = src_nif.shapes[0]
    weights = {}
    for b in s.bone_names:
        for vi, w in s.bone_weights[b]:
            weights.setdefault(vi, []).append((b, w))
    groups = []
    for tmask in (~string, string):
        tris = T[tmask]
        used = np.unique(tris)
        remap = -np.ones(len(V), int)
        remap[used] = np.arange(len(used))
        groups.append(dict(P=V[used], UV=UV[used], N=np.array(s.normals)[used], T=remap[tris],
                           W=[weights[i] for i in used]))
    groups.append(dict(P=np.zeros((0, 3)), UV=np.zeros((0, 2)), N=np.zeros((0, 3)), T=np.zeros((0, 3), int), W=[]))
    bow, _, fea = groups
    nadd = 0

    def add(g, P, Tt, uv, bone):
        base = len(g['P'])
        g['P'] = np.vstack([g['P'], P])
        g['UV'] = np.vstack([g['UV'], uv])
        g['N'] = np.vstack([g['N'], vertex_normals(P, Tt)])
        g['T'] = np.vstack([g['T'], Tt + base])
        g['W'] += [[(bone, 1.0)]] * len(P)
    for sgn in (1, -1):
        silver, feathers = tip_parts(V, T, metal, spike, string, sgn, hawk)
        for P, Tt in silver:
            add(bow, P, Tt, ornament_uv(P), TIP_BONES[sgn])
            nadd += len(P)
        for P, Tt, uv in feathers:
            add(fea, P, Tt, uv, TIP_BONES[sgn])
        for P, Tt, uv in grip_feathers(V, T, metal, string, sgn, hawk):
            add(fea, P, Tt, uv, GRIP_BONES[sgn])
    nock = nock_arrow(V, T, UV, string, s, *string_full_draw(src_nif))      # also sets ARROW_LINE
    arrow_hole(bow, *ARROW_LINE)
    print('bow shape: %d original vertices kept, %d added silver vertices; string %d; feathers %d'
          % (len(bow['P']) - nadd, nadd, len(groups[1]['P']), len(fea['P'])))
    nP, nT, nN, nW = nock
    global NOCK_TRUE_WEIGHTS
    NOCK_TRUE_WEIGHTS = [dict(w) for w in nW]                      # signed; signed_weights() writes them back
    groups.append(dict(P=nP, UV=np.full((len(nP), 2), 0.5), N=nN, T=nT, W=[[(b, abs(x)) for b, x in w] for w in nW]))
    print('forming arrow: %d vertices, collapsed at the nock (bind)' % len(nP))
    hawk_nif, hawk_shape = hawk[3]
    tmp = os.path.join(tempfile.mkdtemp(), 'owlbow_shapes.nif')
    dst = NifFile()
    dst.initialize('SKYRIMSE', tmp, 'BSFadeNode', 'DaedricBowSkinned.nif')
    for name, g in zip(GROUP_NAMES, groups):
        props = BSTriShapeBuf()
        props.bufType = PynBufferTypes.BSTriShapeBufType
        o = dst.createShapeFromData(name, [tuple(p) for p in g['P']], [tuple(t) for t in g['T']],
                                    [tuple(u) for u in g['UV']], [tuple(n) for n in g['N']], props=props)
        src_shader = hawk_shape if name == 'OwlBowFeathers' else s
        src_shader.shader.properties.copyto(o.shader.properties)
        p = o.shader.properties
        p.bufType = PynBufferTypes.BSLightingShaderPropertyBufType
        f1, f2 = p.Shader_Flags_1, p.Shader_Flags_2 & ~ShaderFlags2.GLOW_MAP
        if name == 'OwlBow':
            p.Shader_Type = 1                                              # environment map
            p.Shader_Flags_1 = f1 | ShaderFlags1.ENVIRONMENT_MAPPING
            p.Shader_Flags_2 = f2
            p.Env_Map_Scale = 1.0
            p.Spec_Color[0], p.Spec_Color[1], p.Spec_Color[2] = 0.9, 0.92, 0.95
            p.Emissive_Mult = 0.0
        elif name in ('OwlBowString', 'OwlBowNockArrow'):
            p.Shader_Type = 0
            p.Shader_Flags_1 = (f1 | ShaderFlags1.OWN_EMIT) & ~ShaderFlags1.ENVIRONMENT_MAPPING
            p.Shader_Flags_2 = f2
            for i, c in enumerate(STRING_EMIT):
                p.Emissive_Color[i] = c
            p.Emissive_Color[3] = 1.0
            p.Emissive_Mult = STRING_EMIT_MULT if name == 'OwlBowString' else NOCK_EMIT_MULT
            if name == 'OwlBowNockArrow':
                p.Emissive_Color[0] = p.Emissive_Color[1] = p.Emissive_Color[2] = 1.0     # pure white energy
        else:                                                              # the hawk feather's own material
            p.Shader_Flags_1 = f1 | ShaderFlags1.SKINNED
            p.Shader_Flags_2 = f2 | ShaderFlags2.DOUBLE_SIDED
        o.save_shader_attributes()          # texture paths: set_textures() rewrites the spliced texture set
        if name == 'OwlBowFeathers':
            assert hawk_shape.has_alpha_property
            o.has_alpha_property = True
            hawk_shape.alpha_property.properties.copyto(o.alpha_property.properties)
            o.save_alpha_property()
        o.skin()
        o.set_global_to_skin(s.global_to_skin)
        bones = [b for b in s.bone_names if any(bb == b for w in g['W'] for bb, _ in w)]
        for b in bones:
            o.add_bone(b, src_nif.nodes[b].transform)
        for b in bones:
            o.set_skin_to_bone_xform(b, s.get_shape_skin_to_bone(b))
        per_bone = {b: [] for b in bones}
        for vi, ws in enumerate(g['W']):
            tot = sum(w for _, w in ws) if name != 'OwlBowNockArrow' else 1.0   # the arrow's are signed (fixed after)
            for b, w in ws:
                per_bone[b].append((vi, w / tot))
        for b in bones:
            o.setShapeWeights(b, per_bone[b])
        o.set_partitions(s.partitions, [0] * len(g['T']))
    dst.save()
    return tmp


def set_textures(nif, k, paths):
    """Rewrite a BSShaderTextureSet block with exactly these 9 slot paths."""
    nif.blocks[k] = nifse.texture_set([p.replace('/', '\\') for p in paths])


def splice(orig_raw, tmp_path):
    """Real Bows' file with its shape group replaced by the scratch file's shape groups (the first in place of the
    original's six blocks, the others appended and hung on the root)."""
    out = nifse.Nif(orig_raw)
    assert out.tobytes() == orig_raw
    new = nifse.Nif(open(tmp_path, 'rb').read())
    o_shape = out.find('BSTriShape')
    assert len(o_shape) == 1
    o_shape = o_shape[0]
    o_group = list(range(o_shape, o_shape + 6))
    assert [out.btype(k) for k in o_group] == ['BSTriShape', 'BSLightingShaderProperty', 'BSShaderTextureSet',
                                               'NiSkinInstance', 'NiSkinData', 'NiSkinPartition'], [out.btype(k) for k in o_group]
    node_of = {out.string(struct.unpack_from('<i', out.blocks[k], 0)[0]): k for k in range(len(out.blocks))
               if out.btype(k) in ('NiNode', 'BSFadeNode')}
    groups = []
    for k in new.find('BSTriShape'):
        b = new.blocks[k]
        o = nifse.av_fields(b)['end']
        skin, shader, alpha = struct.unpack_from('<iii', b, o + 16)
        tset = struct.unpack_from('<i', new.blocks[shader], nifse.LSP_TEXSET)[0]
        data, part = struct.unpack_from('<ii', new.blocks[skin], 0)
        groups.append(dict(shape=k, shader=shader, tset=tset, skin=skin, data=data, part=part, alpha=alpha,
                           name=new.string(struct.unpack_from('<i', b, 0)[0])))
    assert tuple(g['name'] for g in groups) == GROUP_NAMES, [g['name'] for g in groups]
    _, children = nifse.node_children(out.blocks[0])
    order = ('shape', 'shader', 'tset', 'skin', 'data', 'part')
    types = ('BSTriShape', 'BSLightingShaderProperty', 'BSShaderTextureSet', 'NiSkinInstance', 'NiSkinData',
             'NiSkinPartition')
    for gi, g in enumerate(groups):
        idx = dict(zip(order, o_group)) if gi == 0 else {}
        for key, typ in zip(order, types):
            blk = bytearray(new.blocks[g[key]])
            if key == 'skin':
                # BSDismemberSkinInstance -> NiSkinInstance: data, partition, skeleton root, bones; drop the
                # partition list (the original is a plain NiSkinInstance)
                nb = struct.unpack_from('<I', blk, 12)[0]
                assert new.btype(g[key]) in ('BSDismemberSkinInstance', 'NiSkinInstance'), new.btype(g[key])
                blk = blk[:16 + 4 * nb]
            if gi == 0:
                out.blocks[idx[key]] = blk
            else:
                idx[key] = out.add_block(typ, blk)
        idx['alpha'] = -1
        if g['alpha'] >= 0:
            ab = bytearray(new.blocks[g['alpha']])
            assert new.btype(g['alpha']) == 'NiAlphaProperty' and struct.unpack_from('<iIi', ab, 0) == (-1, 0, -1)
            idx['alpha'] = out.add_block('NiAlphaProperty', ab)
        sb = out.blocks[idx['shape']]
        o = nifse.av_fields(sb)['end']
        struct.pack_into('<i', sb, 0, out.add_string(g['name']))
        assert struct.unpack_from('<I', sb, 4)[0] == 0, 'extra data on the new shape'
        f = nifse.av_fields(sb)
        assert struct.unpack_from('<i', sb, f['ctrl'])[0] == -1 and struct.unpack_from('<i', sb, f['coll'])[0] == -1
        struct.pack_into('<iii', sb, o + 16, idx['skin'], idx['shader'], idx['alpha'])
        shb = out.blocks[idx['shader']]
        nm = struct.unpack_from('<i', shb, 4)[0]
        struct.pack_into('<i', shb, 4, -1 if nm < 0 else out.add_string(new.string(nm)))
        assert struct.unpack_from('<i', shb, nifse.LSP_CTRL)[0] == -1
        struct.pack_into('<i', shb, nifse.LSP_TEXSET, idx['tset'])
        kb = out.blocks[idx['skin']]
        nb = struct.unpack_from('<I', kb, 12)[0]
        bones = struct.unpack_from('<%di' % nb, kb, 16)
        names = [new.string(struct.unpack_from('<i', new.blocks[x], 0)[0]) for x in bones]
        struct.pack_into('<iii', kb, 0, idx['data'], idx['part'], 0)
        struct.pack_into('<%di' % nb, kb, 16, *[node_of[n] for n in names])
        if gi > 0:
            children = children + [idx['shape']]
        g['idx'] = idx
    out.blocks[0] = nifse.set_children(out.blocks[0], children)
    return out, groups


# ---- the arrows and the snow -------------------------------------------------------------------------------

BOUND_ARROW = ('meshes/weapons/boundweapons/boundarrow.nif', 'meshes/weapons/boundweapons/boundarrowflight.nif')
ARROW_D = 'textures/weapons/daedric/DaedricArrow.dds'      # the bound arrow's diffuse (its mesh is the Daedric arrow)
OUT_ARROW = ('meshes/Zenderal/OwlBow/IceArrow.nif', 'meshes/Zenderal/OwlBow/IceArrowFlight.nif')
OUT_ARROW_D = 'textures/Zenderal/OwlBow/EnergyArrow_d.dds'
OLD_FILES = ('textures/Zenderal/OwlBow/IceArrow_d.dds', 'textures/Zenderal/OwlBow/IceArrow_m.dds')   # build 1's
ARROW_RAMP = ((0.0, (0.80, 0.86, 0.92)), (1.0, (1.0, 1.0, 1.0)))
ARROW_EMIT, ARROW_EMIT_MULT = (1.0, 1.0, 1.0), 3.0     # pure white energy (curator 2026-11-16)
# The game shows this flight model on the string too, but holds its controllers at their first key there and runs
# them once it is fired (2026-11-16, in game: with alpha keyed 0 -> 1 the arrow was invisible until fired). So an
# alpha 0 -> 1 controller hides it on the string and shows it in flight; the arrow that forms on the string is the
# bow's own (nock_arrow).
FLIGHT_SHOW = 0.05          # seconds after it is fired the arrow is fully visible
LSP_EMIT, LSP_EMIT_MULT, LSP_F1 = 44, 56, 16          # BSLightingShaderProperty (SE, no extra data) field offsets
SNOW_SRC = 'meshes/effects/ambient/fxambgentlyfallingsnow00.nif'
# The flakes' texture: the game's own FXSnowSub.dds (Skyrim - Textures5.bsa: white, four flakes in its alpha) copied to
# our own path. The list's winning textures/effects/FXSnowSub.dds is The Weathers of Enderal's blank 4x4 with alpha 0
# (it turns vanilla's particle snow off), so every flake drew as nothing: the trace showed the art attached and its
# particles alive (2026-11-17)
FLAKE_SRC = 'textures/effects/FXSnowSub.dds'
OUT_FLAKE = 'textures/Zenderal/OwlBow/SnowveilFlakes.dds'
SNOW_PSYS = 'PCloudSnowFlakes09'
OUT_SNOW = 'meshes/Zenderal/OwlBow/OwlBowSnowFX.nif'
SNOW = dict(radius=2.4, radiusvar=0.6, life=2.4, lifevar=0.8, speed=2.0, speedvar=1.5, gravity=14.0,
            birth=24.0, max_particles=90)     # 2026-11-17: denser (was 9/s, 40 flakes, r 0.35: hardly seen)
# radius: the game's own falling snow (PCloudSnowFlakes09) is 3.5 (+-0.52): each particle is a sprite with a flake in
# it. 0.35-0.8 drew nothing visible in game (2026-11-17)
SNOW_COLOR, SNOW_ALPHA = (0.92, 0.96, 1.0), 0.85
TRAIL = dict(box=((-0.7, 2.0, -0.7), (0.7, 66.0, 0.7)), radius=3.0, radiusvar=0.8, life=0.8, lifevar=0.3, speed=1.0,
             speedvar=1.5, gravity=8.0, birth=220.0, max_particles=260)
# the fired arrow's snow trail (flight_snow): flakes born along the shaft (BoundArrowFlight:0 runs y 0.9..66.3) in
# world space, so they hang behind the arrow and drift down
SNOW_BOX = (np.array([-6.5, 0.0, 0.0]), (22.0, 108.0, 4.0))   # the bow's own space: string to back, tip to tip


def float_controller(nif, target, var, keys, nxt=-1):
    """A clamped BSLightingShaderPropertyFloatController on `target` (layout from the bound arrow's own: next,
    flags, frequency, phase, start, stop, target, interpolator, controlled variable) with linear keys; returns its
    index. Flags 0x48 = the bound arrow's (active), plus cycle type 2 = clamp: plays once and holds the last key."""
    data = struct.pack('<II', len(keys), 1) + b''.join(struct.pack('<2f', t, v) for t, v in keys)
    kd = nif.add_block('NiFloatData', data)
    ki = nif.add_block('NiFloatInterpolator', struct.pack('<fi', -3.4028234663852886e+38, kd))
    c = struct.pack('<iHffffiiI', nxt, 0x48 | (2 << 1), 1.0, 0.0, keys[0][0], keys[-1][0], target, ki, var)
    assert len(c) == 34
    return nif.add_block('BSLightingShaderPropertyFloatController', c)


def energy_arrows(mods_dir, mods, out_root):
    """The arrows (curator 2026-11-16: no quiver; the arrow forms out of pure white energy as the string is drawn).
    From the game's bound arrow: the ammo model (shown on the back, at the QUIVER node) keeps every block but its
    root shows nothing (the quiver and its six arrows taken off); the flight model, which the game also puts on the
    string while drawing, is white energy (a near-white diffuse made from the Daedric arrow's, white own-emit) and
    glows steadily in flight and is invisible on the string (see above)."""
    j = lambda rel: os.path.join(out_root, *rel.split('/'))
    for old in OLD_FILES:
        if os.path.exists(j(old)):
            os.remove(j(old))
    _, raw_d = sr.winner(mods_dir, mods, ARROW_D, sr.TEX_BSAS)
    d = sr.load_image(raw_d)
    lum = d[..., :3] @ np.array([0.299, 0.587, 0.114])
    lo, hi = np.percentile(lum, [3, 97])
    rgb = sr.ramp(np.clip((lum - lo) / max(hi - lo, 1e-3), 0, 1), ARROW_RAMP)
    sr.write_texture(np.concatenate([rgb, d[..., 3:4]], -1), j(OUT_ARROW_D), 'BC7_UNORM')
    # ammo model: nothing on the back
    _, raw = sr.winner(mods_dir, mods, BOUND_ARROW[0])
    nif = nifse.Nif(raw)
    assert nif.string(0) == 'Arrow' and nif.btype(0) == 'BSFadeNode'
    _, kids = nifse.node_children(nif.blocks[0])
    assert [nif.btype(k) for k in kids] == ['NiNode', 'BSTriShape'], kids
    nif.blocks[0] = nifse.set_children(nif.blocks[0], [])
    data = nif.tobytes()
    assert nifse.Nif(data).tobytes() == data
    os.makedirs(os.path.dirname(j(OUT_ARROW[0])), exist_ok=True)
    open(j(OUT_ARROW[0]), 'wb').write(data)
    # flight / nocked model: white energy that forms
    _, raw = sr.winner(mods_dir, mods, BOUND_ARROW[1])
    nif = nifse.Nif(raw)
    (lsp,) = nif.find('BSLightingShaderProperty')
    b = nif.blocks[lsp]
    assert len(b) == 104 and struct.unpack_from('<i', b, 12)[0] == -1
    struct.pack_into('<3f', b, LSP_EMIT, *ARROW_EMIT)
    struct.pack_into('<f', b, LSP_EMIT_MULT, ARROW_EMIT_MULT)
    tset = struct.unpack_from('<i', b, 40)[0]
    paths = nifse.texture_paths(nif.blocks[tset])
    assert paths[0].lower().endswith('daedricarrow.dds'), paths
    paths[0] = OUT_ARROW_D.replace('/', chr(92))
    nif.blocks[tset] = nifse.texture_set(paths)
    shape = [k for k in nif.find('BSTriShape') if nif.string(struct.unpack_from('<i', nif.blocks[k], 0)[0]) == 'BoundArrowFlight:0']
    assert len(shape) == 1
    o = nifse.av_fields(nif.blocks[shape[0]])['end']
    alpha = struct.unpack_from('<i', nif.blocks[shape[0]], o + 24)[0]
    assert nif.btype(alpha) == 'NiAlphaProperty' and struct.unpack_from('<H', nif.blocks[alpha], 12)[0] & 1, 'no blending'
    al = float_controller(nif, lsp, 12, [(0.0, 0.0), (FLIGHT_SHOW, 1.0)])
    struct.pack_into('<i', nif.blocks[lsp], 12, al)
    shape = [k for k in nif.find('BSTriShape') if nif.string(struct.unpack_from('<i', nif.blocks[k], 0)[0]) == 'BoundArrowFlight:0']
    assert len(shape) == 1
    o = nifse.av_fields(nif.blocks[shape[0]])['end']
    alpha = struct.unpack_from('<i', nif.blocks[shape[0]], o + 24)[0]
    assert nif.btype(alpha) == 'NiAlphaProperty' and struct.unpack_from('<H', nif.blocks[alpha], 12)[0] & 1, 'no blending'
    data = nif.tobytes()
    assert nifse.Nif(data).tobytes() == data
    open(j(OUT_ARROW[1]), 'wb').write(data)
    print('energy arrows: %s (no quiver), %s (white; invisible on the string, shown %.2f s after firing)' % (OUT_ARROW[0], OUT_ARROW[1], FLIGHT_SHOW))


def snow_fx(mods_dir, mods, out_root):
    """The bow's light snowfall (enchant art: shows while the bow is drawn): Chillrend's enchant art with the
    look of the game's gently falling snow (FXSnowSub flakes: its shader, alpha, particle data and colour curve),
    the emitter box over the whole bow, slow flakes drifting down in world space. Other blocks byte-identical."""
    _, tpl = sr.winner(mods_dir, mods, sr.ART_TEMPLATE)
    _, sraw = sr.winner(mods_dir, mods, SNOW_SRC)
    art, orig, snow = nifse.Nif(tpl), nifse.Nif(tpl), nifse.Nif(sraw)
    assert art.string(0) == 'ChillrendEnchFX'
    art.strings[0] = b'OwlBowSnowFX'
    (psys,) = art.find('NiParticleSystem')
    f, amods, ectl = sr.psys_parts(art, psys)
    ssys = [k for k in snow.find('NiParticleSystem') if sr.name_of(snow, k) == SNOW_PSYS]
    assert len(ssys) == 1, ssys
    sf, smods, _ = sr.psys_parts(snow, ssys[0])
    changed = set()

    def put(k, b):
        art.blocks[k] = bytearray(b)
        changed.add(k)

    for k, sk in ((f['shader'], sf['shader']), (f['alpha'], sf['alpha'])):
        assert art.btype(k) == snow.btype(sk), (art.btype(k), snow.btype(sk))
        put(k, snow.blocks[sk])
    data = bytearray(snow.blocks[sf['data']])
    assert struct.unpack_from('<i', data, 0)[0] == 0
    struct.pack_into('<H', data, 4, SNOW['max_particles'])
    put(f['data'], data)
    (col,), (scol,) = amods['BSPSysSimpleColorModifier'], smods['BSPSysSimpleColorModifier']
    # visible flakes (2026-11-17: none showed in game): the ambient snow peaks at colour alpha 0.35, blends normally
    # and is lit by the scene (dark in a dark wood). Rise's flames (Chillrend's art + the torch's look) show: they are
    # additive and self-lit. So: its timing, colours SNOW_COLOR at SNOW_ALPHA; alpha blend SRC_ALPHA + ONE, no test;
    # the shader's Effect Lighting flag (flags2 0x40000000) off
    cv = list(struct.unpack('<18f', bytes(nifse.simple_color_values(snow.blocks[scol]))))
    for c in range(3):
        cv[6 + 4 * c:9 + 4 * c] = SNOW_COLOR
    cv[6 + 4 + 3] = SNOW_ALPHA
    put(col, nifse.set_simple_color_values(art.blocks[col], struct.pack('<18f', *cv)))
    ab = bytearray(art.blocks[f['alpha']])
    fl_ = struct.unpack_from('<H', ab, 12)[0]
    struct.pack_into('<H', ab, 12, ((fl_ & ~0x1FE) | 1 | (6 << 1) | (0 << 5)) & ~0x200)
    put(f['alpha'], ab)
    sb_ = bytearray(art.blocks[f['shader']])
    struct.pack_into('<I', sb_, 16, struct.unpack_from('<I', sb_, 16)[0] & ~0x40000000)
    # the source texture (a sized string at 36) -> our copy of the game's own flakes
    n_ = struct.unpack_from('<I', sb_, 36)[0]
    assert bytes(sb_[40:40 + n_]).lower().endswith(b'fxsnowsub.dds'), bytes(sb_[40:40 + n_])
    path = OUT_FLAKE.replace('/', chr(92)).encode('latin1')
    sb_ = sb_[:36] + struct.pack('<I', len(path)) + path + sb_[40 + n_:]
    put(f['shader'], sb_)
    _, flake = sr.winner(mods_dir, [], FLAKE_SRC, sr.TEX_BSAS)      # vanilla only: the list's copy is blank
    fd = sr.load_image(flake)
    assert fd.shape[0] >= 64 and fd[..., 3].max() > 0.9, 'not the game\'s own flakes'
    fp = os.path.join(out_root, *OUT_FLAKE.split('/'))
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    open(fp, 'wb').write(flake)
    (scl,) = amods['BSPSysScaleModifier']
    put(scl, nifse.set_scale_values(art.blocks[scl], [1.0] * len(nifse.scale_values(art.blocks[scl]))))
    (emi,) = amods['NiPSysBoxEmitter']
    e = nifse.box_emitter(art.blocks[emi])
    e.update(speed=SNOW['speed'], speedvar=SNOW['speedvar'], decl=0.0, declvar=math.pi, planar=0.0,
             planarvar=2 * math.pi, radius=SNOW['radius'], radiusvar=SNOW['radiusvar'], life=SNOW['life'],
             lifevar=SNOW['lifevar'], whd=tuple(float(x) for x in SNOW_BOX[1]))
    put(emi, nifse.set_box_emitter(art.blocks[emi], e))
    (spn,) = amods['NiPSysSpawnModifier']
    put(spn, nifse.set_spawn_life(art.blocks[spn], SNOW['life'], SNOW['lifevar']))
    (grv,) = amods['NiPSysGravityModifier']
    gobj = struct.unpack_from('<i', art.blocks[grv], nifse.MOD_BASE)[0]
    put(grv, nifse.set_gravity(art.blocks[grv], (0.0, 0.0, -1.0), SNOW['gravity'], 1))
    t, R, sc_ = nifse.transform(art.blocks[gobj])
    put(gobj, nifse.set_transform(art.blocks[gobj], t, np.eye(3), sc_))
    interp = struct.unpack_from('<i', art.blocks[ectl], 26)[0]
    assert art.btype(interp) == 'NiFloatInterpolator' and struct.unpack_from('<i', art.blocks[interp], 4)[0] == -1
    b = bytearray(art.blocks[interp])
    struct.pack_into('<f', b, 0, SNOW['birth'])
    put(interp, b)
    for k in (e['obj'], psys):
        put(k, nifse.set_transform(art.blocks[k], SNOW_BOX[0], np.eye(3), 1.0))
    # world space (Chillrend's art is local): flakes drift down and stay behind as the bow moves, and the arrow's
    # trail (flight_snow, built from this nif) hangs behind it instead of travelling with it
    pb = bytearray(art.blocks[psys])
    pb[nifse.av_fields(pb)['end'] + 48] = 1
    put(psys, pb)
    for k in range(len(orig.blocks)):
        if k not in changed:
            assert art.blocks[k] == orig.blocks[k], 'block %d changed' % k
    data = art.tobytes()
    assert nifse.Nif(data).tobytes() == data
    p = os.path.join(out_root, *OUT_SNOW.split('/'))
    open(p, 'wb').write(data)
    print('snow: %s, %d of %d blocks changed' % (OUT_SNOW, len(changed), len(art.blocks)))


WIND_ALPHA = 1.0            # the vanilla tracer's opacity times this (0.35 showed nothing in game, 2026-11-17)
EFFECT_ALPHA_VAR = 5        # BSEffectShaderPropertyFloatController: Alpha Transparency (base colour alpha)


def import_tracer(dst, src):
    """Copy the vanilla arrow's tracer (TracerRoot: the long faint streak trailShort and the spinning Flow swirl, with
    their effect shaders, alpha properties and Flow's spin controller) from the bound arrow's flight nif `src` into
    `dst`; returns the new TracerRoot. References are remapped per block type (only these types occur, asserted).
    Each effect shader's base alpha is scaled by WIND_ALPHA and keyed 0 -> that over FLIGHT_SHOW (clamped), the
    arrow's own trick: on the string the game holds controllers at their first key, so the wind shows only in flight."""
    (root,) = [k for k in nifse.node_children(src.blocks[0])[1] if src.string(struct.unpack_from('<i', src.blocks[k], 0)[0]) == 'TracerRoot']
    order, todo = [], [root]
    while todo:                                   # the branch, in visit order
        k = todo.pop(0)
        if k < 0 or k in order:
            continue
        order.append(k)
        b, t = src.blocks[k], src.btype(k)
        if t in ('NiNode', 'BSValueNode'):
            todo += nifse.node_children(b)[1]
            todo.append(struct.unpack_from('<i', b, nifse.av_fields(b)['ctrl'])[0])
        elif t == 'BSTriShape':
            f = nifse.av_fields(b)
            todo += list(struct.unpack_from('<ii', b, f['end'] + 20))
        elif t == 'NiTransformController':
            todo.append(struct.unpack_from('<i', b, 26)[0])
        elif t == 'NiTransformInterpolator':
            todo.append(struct.unpack_from('<i', b, 32)[0])
    new = {}
    for k in order:                               # reserve indices first, so references can point forward
        new[k] = dst.add_block(src.btype(k), b'')
    remap = lambda r: new[r] if r >= 0 else -1
    shaders = []
    for k in order:
        b, t = bytearray(src.blocks[k]), src.btype(k)
        if t in ('NiNode', 'BSValueNode', 'BSTriShape', 'BSEffectShaderProperty', 'NiAlphaProperty'):
            struct.pack_into('<i', b, 0, dst.add_string(src.string(struct.unpack_from('<i', b, 0)[0]) or ''))
            assert struct.unpack_from('<I', b, 4)[0] == 0, (k, t, 'extra data')
        if t in ('NiNode', 'BSValueNode', 'BSTriShape'):
            f = nifse.av_fields(b)
            struct.pack_into('<i', b, f['ctrl'], remap(struct.unpack_from('<i', b, f['ctrl'])[0]))
            # shown always: the bound arrow keeps its tracer under a hidden AddOnNode99, which the game only shows on
            # a tracer roll (trace 2026-11-17: hidden in flight)
            struct.pack_into('<I', b, f['flags'], struct.unpack_from('<I', b, f['flags'])[0] & ~1)
            assert struct.unpack_from('<i', b, f['coll'])[0] == -1
        if t in ('NiNode', 'BSValueNode'):
            o, kids = nifse.node_children(b)
            ne = o + 4 + 4 * len(kids)
            assert struct.unpack_from('<I', b, ne)[0] == 0, 'effects list'
            b = nifse.set_children(b, [remap(c) for c in kids])
        elif t == 'BSTriShape':
            f = nifse.av_fields(b)
            assert struct.unpack_from('<i', b, f['end'] + 16)[0] == -1, 'skinned'
            sh, al = struct.unpack_from('<ii', b, f['end'] + 20)
            struct.pack_into('<ii', b, f['end'] + 20, remap(sh), remap(al))
        elif t in ('BSEffectShaderProperty', 'NiAlphaProperty'):
            assert struct.unpack_from('<i', b, 8)[0] == -1, (k, t, 'controller')
            if t == 'BSEffectShaderProperty':
                shaders.append(new[k])
        elif t == 'NiTransformController':
            assert struct.unpack_from('<i', b, 0)[0] == -1
            struct.pack_into('<ii', b, 22, remap(struct.unpack_from('<i', b, 22)[0]), remap(struct.unpack_from('<i', b, 26)[0]))
        elif t == 'NiTransformInterpolator':
            struct.pack_into('<i', b, 32, remap(struct.unpack_from('<i', b, 32)[0]))
        elif t == 'NiTransformData':
            pass
        else:
            raise AssertionError('tracer block type %s not handled' % t)
        dst.blocks[new[k]] = b
    for k in shaders:
        b = dst.blocks[k]
        o = 36                                    # name, extra (0), ctrl, flags1, flags2, uv offset, uv scale
        o += 4 + struct.unpack_from('<I', b, o)[0] + 4 + 16   # source texture, clamp/lighting/lod/unused, falloff 4f
        a = struct.unpack_from('<f', b, o + 12)[0] * WIND_ALPHA       # base colour alpha
        struct.pack_into('<f', b, o + 12, a)
    names = [src.string(struct.unpack_from('<i', src.blocks[k], 0)[0]) for k in order if src.btype(k) == 'BSTriShape']
    print('  wind: %s from the bound arrow (%d blocks), opacity x%.2f' % (', '.join(names), len(order), WIND_ALPHA))
    return new[root]


def flight_snow(out_root):
    """The fired arrow trails snow (curator 2026-11-17: "a snow effect from the bow and arrow"). Built from the bow's
    own snowfall (OUT_SNOW, written by snow_fx): the flight arrow's shape and its blocks (lighting shader with its
    show-in-flight alpha controller, texture set, alpha property) are copied into it, the emitter box runs along the
    shaft, and the birth rate is keyed 0 -> TRAIL['birth'] over FLIGHT_SHOW, clamped: on the string the game holds
    controllers at their first key (see FLIGHT_SHOW), so it snows only once the arrow is loosed. Particles are in
    world space, so they stay behind as a trail. Written over OUT_ARROW[1]."""
    j = lambda rel: os.path.join(out_root, *rel.split('/'))
    art = nifse.Nif(open(j(OUT_SNOW), 'rb').read())
    fl = nifse.Nif(open(j(OUT_ARROW[1]), 'rb').read())
    (shape,) = [k for k in fl.find('BSTriShape') if fl.string(struct.unpack_from('<i', fl.blocks[k], 0)[0]) == 'BoundArrowFlight:0']
    sb = bytearray(fl.blocks[shape])
    f = nifse.av_fields(sb)
    assert struct.unpack_from('<I', sb, f['nextra'])[0] == 0 and struct.unpack_from('<i', sb, f['ctrl'])[0] == -1
    assert struct.unpack_from('<i', sb, f['coll'])[0] == -1 and struct.unpack_from('<i', sb, f['end'] + 16)[0] == -1
    lsp, ap = struct.unpack_from('<ii', sb, f['end'] + 20)
    assert fl.btype(lsp) == 'BSLightingShaderProperty' and fl.btype(ap) == 'NiAlphaProperty'
    lb = bytearray(fl.blocks[lsp])
    assert struct.unpack_from('<I', lb, 8)[0] == 0
    ctl, tset = struct.unpack_from('<i', lb, 12)[0], struct.unpack_from('<i', lb, 40)[0]
    assert fl.btype(ctl) == 'BSLightingShaderPropertyFloatController' and struct.unpack_from('<i', fl.blocks[ctl], 0)[0] == -1
    cb = bytearray(fl.blocks[ctl])
    interp = struct.unpack_from('<i', cb, 26)[0]
    ib = bytearray(fl.blocks[interp])
    fdata = struct.unpack_from('<i', ib, 4)[0]
    assert fl.btype(interp) == 'NiFloatInterpolator' and fl.btype(fdata) == 'NiFloatData'
    ab = bytearray(fl.blocks[ap])
    assert struct.unpack_from('<I', ab, 4)[0] == 0 and struct.unpack_from('<i', ab, 8)[0] == -1
    # copy into the snow nif, references remapped
    n_tset = art.add_block('BSShaderTextureSet', fl.blocks[tset])
    n_data = art.add_block('NiFloatData', fl.blocks[fdata])
    struct.pack_into('<i', ib, 4, n_data)
    n_interp = art.add_block('NiFloatInterpolator', ib)
    n_lsp = art.add_block('BSLightingShaderProperty', lb)
    struct.pack_into('<ii', cb, 22, n_lsp, n_interp)              # target, interpolator
    n_ctl = art.add_block('BSLightingShaderPropertyFloatController', cb)
    lb = art.blocks[n_lsp]
    struct.pack_into('<i', lb, 4, art.add_string(fl.string(struct.unpack_from('<i', lb, 4)[0]) or ''))
    struct.pack_into('<i', lb, 12, n_ctl)
    struct.pack_into('<i', lb, 40, n_tset)
    struct.pack_into('<i', ab, 0, art.add_string(fl.string(struct.unpack_from('<i', ab, 0)[0]) or ''))
    n_ap = art.add_block('NiAlphaProperty', ab)
    struct.pack_into('<i', sb, 0, art.add_string('IceArrowFlight:0'))
    struct.pack_into('<ii', sb, f['end'] + 20, n_lsp, n_ap)
    n_shape = art.add_block('BSTriShape', sb)
    # root: the flight's name and BSX flags; children = the arrow + the snow (the Chillrend billboard dropped)
    root = art.blocks[0]
    art.strings[struct.unpack_from('<i', root, 0)[0]] = b'IceArrowFlight'
    (bsx,) = art.find('BSXFlags')
    (fbsx,) = fl.find('BSXFlags')
    struct.pack_into('<I', art.blocks[bsx], 4, struct.unpack_from('<I', fl.blocks[fbsx], 4)[0])
    _, kids = nifse.node_children(root)
    kids = [k for k in kids if art.btype(k) != 'NiBillboardNode'] + [n_shape, import_tracer(art, fl)]
    art.blocks[0] = nifse.set_children(root, kids)
    # the trail: emitter along the shaft, finer and shorter-lived flakes, birth keyed to start on release
    (psys,) = art.find('NiParticleSystem')
    pf, amods, ectl = sr.psys_parts(art, psys)
    lo, hi = TRAIL['box']
    centre = (np.array(lo) + np.array(hi)) / 2
    (emi,) = amods['NiPSysBoxEmitter']
    e = nifse.box_emitter(art.blocks[emi])
    e.update(speed=TRAIL['speed'], speedvar=TRAIL['speedvar'], radius=TRAIL['radius'], radiusvar=TRAIL['radiusvar'],
             life=TRAIL['life'], lifevar=TRAIL['lifevar'], whd=tuple(float(x) for x in np.array(hi) - np.array(lo)))
    art.blocks[emi] = nifse.set_box_emitter(art.blocks[emi], e)
    for k in (e['obj'], psys):
        art.blocks[k] = nifse.set_transform(art.blocks[k], centre, np.eye(3), 1.0)
    (spn,) = amods['NiPSysSpawnModifier']
    art.blocks[spn] = nifse.set_spawn_life(art.blocks[spn], TRAIL['life'], TRAIL['lifevar'])
    (grv,) = amods['NiPSysGravityModifier']
    art.blocks[grv] = nifse.set_gravity(art.blocks[grv], (0.0, 0.0, -1.0), TRAIL['gravity'], 1)
    struct.pack_into('<H', art.blocks[pf['data']], 4, TRAIL['max_particles'])
    # constant birth rate (2026-11-17: a 0 -> birth key "to spare the string" showed nothing; the arrow on the string
    # is the AMMO model's Arrow:0, traced 2026-11-16, so the flight model never sits there)
    e_interp = struct.unpack_from('<i', art.blocks[ectl], 26)[0]
    assert struct.unpack_from('<i', art.blocks[e_interp], 4)[0] == -1
    struct.pack_into('<f', art.blocks[e_interp], 0, TRAIL['birth'])
    data = art.tobytes()
    assert nifse.Nif(data).tobytes() == data
    open(j(OUT_ARROW[1]), 'wb').write(data)
    nf = NifFile(j(OUT_ARROW[1]))
    names = [s.name for s in nf.shapes]
    assert 'IceArrowFlight:0' in names, names
    print('arrow snow trail: %s, arrow + world-space flakes along y %.0f..%.0f, %.0f/s'
          % (OUT_ARROW[1], lo[1], hi[1], TRAIL['birth']))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mods', default=os.path.join(sr.MO2, 'mods'))
    ap.add_argument('--target', default='Zenderal - Patch Collection')
    args = ap.parse_args()
    mods = sr.profile_mods()
    out_root = os.path.join(args.mods, args.target)
    assert os.path.isdir(out_root), out_root
    src_label, raw = sr.winner(args.mods, mods, MESH)
    if src_label != sr.EXPECT_SOURCE:
        sys.exit('%s now comes from %s, not %s' % (MESH, src_label, sr.EXPECT_SOURCE))
    tex = sr.pretty(args.mods, mods, TEX_D)
    nrm = sr.pretty(args.mods, mods, TEX_N)
    tmpd = tempfile.mkdtemp()
    src_path = os.path.join(tmpd, 'firewind.nif')
    open(src_path, 'wb').write(raw)
    src_nif = NifFile(src_path)
    s = src_nif.shapes[0]
    V = np.array(s.verts, float)
    UV = np.array(s.uvs, float)
    T = np.array(s.tris, int)
    N = np.array(s.normals, float)
    string, metal, spike = regions(V, UV, T, tex)
    print('regions: string %d tris, tip metal %d, spike %d of %d' % (string.sum(), metal.sum(), spike.sum(), len(T)))
    rgb, n_out, cm = paint(V, N, UV, T, tex, nrm, string, metal)
    write_textures(out_root, rgb, n_out, cm)
    hawk = hawk_feather(args.mods, mods)
    feather_texture(args.mods, mods, out_root)
    tmp = build_shapes(src_nif, string, metal, spike, V, UV, T, hawk)
    out, groups = splice(raw, tmp)
    signed_weights(out, 'OwlBowNockArrow', NOCK_TRUE_WEIGHTS)
    for g in groups:
        paths = {'OwlBow': [OUT_D, OUT_N, '', '', CUBEMAP, OUT_M, '', '', ''],
                 'OwlBowString': [OUT_SD, OUT_SN, '', '', '', '', '', '', ''],
                 'OwlBowFeathers': [OUT_FD, FEATHER_N, '', '', '', '', '', '', ''],
                 'OwlBowNockArrow': [OUT_SD, OUT_SN, '', '', '', '', '', '', '']}[g['name']]
        set_textures(out, g['idx']['tset'], paths)
    data = out.tobytes()
    back = nifse.Nif(data)
    assert back.tobytes() == data
    sr.check_refs(back)
    p = os.path.join(out_root, *OUT_MESH.split('/'))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'wb').write(data)
    # read back with PyNifly: both shapes, skinned to the bow's bones, the original extra data kept
    rb = NifFile(p)
    names = [x.name for x in rb.shapes]
    assert tuple(names) == GROUP_NAMES, names
    for x in rb.shapes:
        assert x.has_skin_instance and set(x.bone_names) <= set(s.bone_names), (x.name, x.bone_names)
    kept = [back.btype(k) for k in range(len(back.blocks))]
    for t in ('BSBehaviorGraphExtraData', 'BSInvMarker', 'BSXFlags', 'NiStringExtraData', 'bhkCollisionObject'):
        assert t in kept, t
    allv = np.vstack([np.array(x.verts) for x in rb.shapes])
    print('wrote %s (%d bytes, %d blocks); bounds %s .. %s; textures %s'
          % (p, len(data), len(back.blocks), allv.min(0).round(1), allv.max(0).round(1), rb.shapes[0].textures))
    energy_arrows(args.mods, mods, out_root)
    snow_fx(args.mods, mods, out_root)
    flight_snow(out_root)


if __name__ == '__main__':
    main()
