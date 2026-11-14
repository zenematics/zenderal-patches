"""Argent Verdict's head (curator 2026-11-13/14): the centre of the hammer's head is a clenched human hand holding the
face and spike like a stake ("change the middle section of the head to a clenched fist, resembling holding the hammer
and spike like a stake", "make the hand look more human like", "reduce the size of the hand by at least 30%"), its
forearm flowing into the handle ("can we lose the base with the roses and have the hand mold into the handle? / and
make the hand human again"), bones breaking through the back of the hand ("remove the engraving from the back of the
hand, instead have skeletal structures protruding from the hand"). Our own geometry, generated here with angel.py's primitives; proportions from an adult
hand.

The hammer's head lies along X (face at -X, spike at +X), the shaft along -Y, the flat faces toward +-Z. The hand is
laid out in a local frame round the stake (x along it, u up, w forward toward +Z) at full size (85 mm across the
knuckles = 2 x BUILD_HALF_W x 0.97 units, round a stake of BUILD_STAKE_R), then scaled HAND_SCALE about the stake and
cocked back TILT degrees, so the wrist stands over the shaft:

- four fingers, index (thumb side, -X) to little, each three phalanges of an adult's proportions (middle finger
  longest, little finger shortest and slimmest): the proximal phalanx runs from its knuckle over the top of the
  stake, the middle one down its front, the distal one tucks back under it into the palm. Each phalanx is its own
  rounded, slightly square-sectioned volume, waisted between its joints, so the joints read as knuckles and creases;
  a nail on each fingertip;
- bones break through the back of the hand: the four metacarpals rise out of the skin near the wrist and run, half
  standing out, to bone knuckle heads (the knuckle row, sloping down to the little finger as in a clenched fist), and
  carpals peep out at the back of the wrist; the back of the hand is otherwise a rounded slab; the flesh of the palm
  and the fingers' undersides fills the curl round the stake, so no gap shows from the side;
- the thumb (metacarpal, proximal, distal) rises from a fleshy thenar mound at the base of the palm and lies across
  the index and middle fingers' middle phalanges, its nail outward;
- the palm's surface runs on down past the wrist as the forearm, one surface with the hand, narrowing, turning a
  little and becoming the shaft: no cuff, its section easing from the wrist's to the shaft's round and its centre
  from behind the stake onto the shaft's axis, ending in a round just over the shaft, its flutes running out from
  under it; a bracelet of thorns (two twisted thorny strands) sits on the join, and a thorny rose vine (roses.py)
  winds up the forearm from it toward the wrist, with roses, a bud and leaves;
- the stake runs out of both sides of the fist to the face's and spike's necks, each neck ending in a socket.

Every part is a Grid: rings of points (each ring wrapped), optionally closed at either end by a centre point, with
the coordinates fist_tex.py paints its patterns in (`paint`, millimetres of the full-size hand) and what kind of
surface it is. `fist(c, neck_x, neck_half, shaft_r)` returns (grids, info) in the mesh's own coordinates: c = the
stake's centre, neck_x = the face's and spike's cut neck ends (mesh x), neck_half = the necks' half height / depth
there, shaft_r = the shaft's radius near its top.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'StingAndRise', 'tools'))
import angel  # noqa: E402  (closed-volume primitives)

HAND_BREADTH_MM = 85.0     # adult hand across the knuckles
BUILD_HALF_W = 5.37        # the hand is laid out at the v2 size (its breadth spanned the cut gap) ...
BUILD_STAKE_R = 1.55       # ... round a stake this thick (the necks' radius) ...
HAND_SCALE = 0.68          # ... then scaled (curator: "reduce the size of the hand by at least 30%")
# per finger, index .. little: width at the knuckle (mm), phalanx lengths joint to joint (mm), half thickness (mm),
# the proximal phalanx's rise toward the middle joint and the middle phalanx's lean back (degrees), the distal
# phalanx's angle under the stake (degrees from straight back)
FINGERS = (
    dict(width=21.0, lengths=(44.0, 25.0, 20.0), thick=9.8, rise=-3.0, lean=4.0, tuck=46.0),
    dict(width=21.0, lengths=(49.0, 30.0, 21.0), thick=10.0, rise=0.0, lean=6.0, tuck=42.0),
    dict(width=20.0, lengths=(46.0, 28.0, 21.0), thick=9.5, rise=3.0, lean=8.0, tuck=40.0),
    dict(width=17.5, lengths=(36.0, 21.0, 18.0), thick=8.4, rise=8.0, lean=12.0, tuck=36.0),
)
TAPER = (1.0, 0.93, 0.86, 0.78)        # a finger's half extents at its knuckle, middle joint, end joint, tip
PRESS = 0.92                           # a phalanx's centre line sits this many half thicknesses off the stake
SECTION_E = 2.5                        # finger cross-section superellipse exponent (2 = round; fingers press flat)
NAIL = (0.62, 0.40, 1.1)               # nail: half width (x the finger's), half length (x the phalanx), thickness mm
THUMB = dict(                          # local (x / half breadth, u, w in mm from the stake's axis) and radii (mm)
    cmc=(-0.58, -44.0, -4.0), mcp=(-0.97, -16.0, 23.0), ip=(-0.42, -2.0, 40.0), tip=(0.12, 2.0, 38.0),
    radii=((10.5, 9.5), (11.2, 9.8), (10.2, 8.6), (8.6, 7.0)))    # (side, dorsal) at cmc, mcp, ip, tip
WRIST_MM = (58.0, 38.0)                # wrist breadth and thickness
TILT = 8.0                             # degrees the hand is cocked back about the stake (the wrist moves under it)
STAKE_PRESS = 0.96                     # the stake's radius, x the scaled build stake (the fingers press into it)
SOCKET = dict(margin=0.16, over=0.55, reach=0.32, shoulder=0.18)   # round each neck end (mesh units)
# the forearm into the shaft: where it has become the shaft (mesh units below the wrist's centre), how far its oval
# turns on the way (deg), its end's radius (x the shaft's, which its twisted flutes run out under), where its skin
# fades to polished metal (mm below the wrist)
FOREARM = dict(length=4.4, turn=25.0, over=1.025, metal_mm=(14.0, 42.0))
# the bracelet of thorns round the forearm's end (mesh units): strand radius, how far the two strands wind round
# each other, their twists round the ring, how far above the arm's end, its thorns (count; length, base radius)
THORNS = dict(strand=0.12, twist=0.11, turns=7, rise=0.06, samples=130, count=26, thorn=(0.46, 0.085))
# bones breaking through the back of the hand (curator 2026-11-14: "remove the engraving from the back of the hand,
# instead have skeletal structures protruding from the hand"): each metacarpal from its base near the wrist (x mm,
# u = METACARPAL_BASE_U) to its finger's knuckle, its profile (along 0..1, half width, half depth, mm, x BONE_SIZE),
# and how much of its depth stands out of the skin along it (0 = sunk, 1 = sitting on the skin); the knuckles become
# bone heads; carpals peeping out at the back of the wrist (centre x, u mm; radii x, u, w mm; how much stands out)
METACARPAL_BASES = (-14.0, -4.0, 6.5, 15.5)
METACARPAL_BASE_U = -44.0
METACARPAL = ((0.0, 6.0, 5.4), (0.14, 4.4, 4.0), (0.6, 3.7, 3.5), (0.84, 5.4, 5.6), (1.0, 6.2, 6.4))
BONE_SIZE = 1.2
PROTRUDE = ((0.0, 0.1), (0.25, 0.55), (0.8, 0.6), (1.0, 0.5))
KNUCKLE_BONE = (0.82, 0.92, 0.98, 0.5)    # bone head radii (x the old knuckle's side, depth, depth) and lift (x depth)
WRIST_BONES = (((-12.0, -50.0), (6.5, 5.0, 5.5), 0.45), ((-1.5, -51.0), (6.0, 5.5, 5.5), 0.5),
               ((9.0, -50.0), (5.5, 5.0, 5.0), 0.45), ((17.0, -48.0), (4.0, 4.0, 4.0), 0.4))
ROSE_VINE = (0.38, 0.25)               # the rose vine climbs from this far above the arm's end to this far below the wrist
WRIST_CUT_MM = 9.0                     # the palm's rings are cut this far above its base (its rounded bottom below)


class Grid:
    """A closed surface as a stack of wrapped rings P (n, m, 3), closed at either end by a centre point (or open);
    paint = the same points in the coordinates the patterns are drawn in (mm); kind = what surface it is."""

    def __init__(self, P, kind, cap0=None, cap1=None, meta=None, density=1.0):
        self.P = np.asarray(P, float)
        self.cap0 = None if cap0 is None else np.asarray(cap0, float)
        self.cap1 = None if cap1 is None else np.asarray(cap1, float)
        self.kind, self.meta, self.density = kind, dict(meta or {}), density
        self.paint, self.paint_cap0, self.paint_cap1 = self.P.copy(), self.cap0, self.cap1
        self.paint_rot = np.eye(3)           # mesh-frame directions -> paint-frame directions

    def apply(self, fn):
        self.P = fn(self.P)
        self.cap0 = None if self.cap0 is None else fn(self.cap0)
        self.cap1 = None if self.cap1 is None else fn(self.cap1)


# ---- geometry helpers

def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def se(a, e):
    """Superellipse cos/sin: |cos|^e + |sin|^e = 1 shapes (2 = circle, more = squarer)."""
    c, s = np.cos(a), np.sin(a)
    return np.sign(c) * np.abs(c) ** (2.0 / e), np.sign(s) * np.abs(s) ** (2.0 / e)


def capsule(A, B, side_ref, dors_ref, half_a, half_b, kind='phal', e=SECTION_E, waist=0.05, rings_n=22, m=20,
            cap=0.85, meta=None):
    """A rounded, superellipse-sectioned volume from joint A to joint B: half extents (side, dorsal) half_a at A,
    half_b at B, a little waisted between, its ends rounded past each joint by cap x the dorsal half extent."""
    A, B = np.asarray(A, float), np.asarray(B, float)
    L = np.linalg.norm(B - A)
    t = (B - A) / L
    dors = unit(dors_ref - t * (dors_ref @ t))
    side = np.cross(t, dors)
    if side @ side_ref < 0:
        side = -side
    ea, eb = cap * half_a[1], cap * half_b[1]
    s_ends_a = [-ea * np.cos(np.pi / 2 * k / 6) for k in range(1, 6)]
    s_ends_b = [L + eb * np.sin(np.pi / 2 * k / 6) for k in range(1, 6)]
    S = np.array(s_ends_a + list(np.linspace(0, L, rings_n)) + s_ends_b)
    cs, sn = se(2 * np.pi * np.arange(m) / m, e)
    R = []
    for s in S:
        f = min(max(s / L, 0.0), 1.0)
        hs = half_a[0] + (half_b[0] - half_a[0]) * f
        hd = half_a[1] + (half_b[1] - half_a[1]) * f
        if s < 0:
            k = np.sqrt(max(1.0 - (s / ea) ** 2, 0.0))
        elif s > L:
            k = np.sqrt(max(1.0 - ((s - L) / eb) ** 2, 0.0))
        else:
            k = 1.0 - waist * np.sin(np.pi * f)
        R.append(A + t * s + k * (hs * cs[:, None] * side + hd * sn[:, None] * dors))
    meta = dict(meta or {}, A=A, t=t, dors=dors, side=side, L=L, hd=(half_a[1] + half_b[1]) / 2)
    return Grid(R, kind, cap0=A - t * ea, cap1=B + t * eb, meta=meta)


def ellipsoid(c, axes, radii, kind='skin', nu=20, nv=14, meta=None):
    """An ellipsoid with its radii along the rows of `axes` (rings round the second axis)."""
    c, axes, radii = np.asarray(c, float), np.asarray(axes, float), np.asarray(radii, float)
    th = np.pi * np.arange(1, nv) / nv
    ph = 2 * np.pi * np.arange(nu) / nu
    R = [c + (radii * np.stack([np.sin(t) * np.cos(ph), np.full(nu, np.cos(t)), np.sin(t) * np.sin(ph)], -1)) @ axes
         for t in th]
    return Grid(R, kind, cap0=c + radii[1] * axes[1], cap1=c - radii[1] * axes[1], meta=meta)


def bone_path(C, out_ref, prof, k, size=1.0, e=2.3, m=14, cap=0.8):
    """A bone along the curve C (local frame), its depth toward out_ref (the outward direction it stands out to):
    superellipse sections whose half extents (mm, x size, x k) follow prof along it, each end rounded."""
    C = np.asarray(C, float)
    seg = np.linalg.norm(np.diff(C, axis=0), axis=1)
    sl = np.concatenate([[0.0], np.cumsum(seg)])
    f = sl / sl[-1]
    ts = np.array([q[0] for q in prof])
    hs = np.interp(f, ts, [q[1] for q in prof]) * k * size
    hd = np.interp(f, ts, [q[2] for q in prof]) * k * size
    tang = unit(np.gradient(C, axis=0))
    out_ref = np.asarray(out_ref, float)
    dors = unit(out_ref[None, :] - tang * (tang @ out_ref)[:, None])
    side = np.cross(tang, dors)
    cs, sn = se(2 * np.pi * np.arange(m) / m, e)
    rings = []
    for j in range(1, 5):                                           # rounded start, beyond C[0]
        q = np.cos(np.pi / 2 * j / 5)
        rings.insert(0, C[0] - tang[0] * cap * hd[0] * q + np.sqrt(1 - q * q) * (
            hs[0] * cs[:, None] * side[0] + hd[0] * sn[:, None] * dors[0]))
    for i in range(len(C)):
        rings.append(C[i] + hs[i] * cs[:, None] * side[i] + hd[i] * sn[:, None] * dors[i])
    for j in range(1, 5):                                           # rounded end, beyond C[-1]
        q = np.sin(np.pi / 2 * j / 5)
        rings.append(C[-1] + tang[-1] * cap * hd[-1] * q + np.sqrt(1 - q * q) * (
            hs[-1] * cs[:, None] * side[-1] + hd[-1] * sn[:, None] * dors[-1]))
    return Grid(rings, 'bone', cap0=C[0] - tang[0] * cap * hd[0], cap1=C[-1] + tang[-1] * cap * hd[-1])


def palm_back(S, x, u):
    """The back of the hand's surface (its w, the box's back at ŵ < 0) above local (x, u): the deformed box's own
    superellipse, solved for ŵ."""
    x, u = np.asarray(x, float), np.asarray(u, float)
    e = S['e']
    t = np.clip((u - S['u_bot']) / (S['u_top'](x) - S['u_bot']), 0, 1)
    uh = 2 * t - 1
    xl, xr = S['xl'](u), S['xr'](u)
    xh = np.clip(2 * (x - xl) / (xr - xl) - 1, -1, 1)
    wh = -np.clip(1 - np.abs(xh) ** e - np.abs(uh) ** e, 0, 1) ** (1 / e)
    return S['w_back'](x, u) + (S['w_front'](x, u) - S['w_back'](x, u)) * (wh + 1) / 2


def tube(C, r, kind, m=24, meta=None, density=1.0):
    """A tube along the curve C (radius per sample), its ends closed flat."""
    C = np.asarray(C, float)
    _, Nn, Bn = angel.frames(C)
    a = 2 * np.pi * np.arange(m) / m
    R = [C[k] + r[k] * (np.cos(a)[:, None] * Nn[k] + np.sin(a)[:, None] * Bn[k]) for k in range(len(C))]
    return Grid(R, kind, cap0=C[0], cap1=C[-1], meta=meta, density=density)


def deformed_box(S, kind, nu=56, nv=40, meta=None, density=1.0):
    """A unit superellipsoid (|x|^e + |y|^e + |z|^e = 1, rings along y) mapped onto a shape given by section
    functions: x from xl(u) to xr(u), u from u_bot to u_top(x), w from w_back(x, u) to w_front(x, u)."""
    e = S['e']
    th = np.pi * np.arange(1, nv) / nv
    ph = 2 * np.pi * np.arange(nu) / nu
    f = lambda a: np.sign(a) * np.abs(a) ** (2.0 / e)
    U = np.array([np.stack([f(np.sin(t)) * f(np.cos(ph)), np.full(nu, f(np.cos(t))), f(np.sin(t)) * f(np.sin(ph))], -1)
                  for t in th])
    poles = np.array([[0.0, 1.0, 0.0], [0.0, -1.0, 0.0]])

    def mapped(Q):
        xh, uh, wh = Q[..., 0], Q[..., 1], Q[..., 2]
        t = (uh + 1) / 2
        u0 = S['u_bot'] + (S['u_top_mean'] - S['u_bot']) * t
        x = S['xl'](u0) + (S['xr'](u0) - S['xl'](u0)) * (xh + 1) / 2
        u = S['u_bot'] + (S['u_top'](x) - S['u_bot']) * t
        w = S['w_back'](x, u) + (S['w_front'](x, u) - S['w_back'](x, u)) * (wh + 1) / 2
        return np.stack([x, u, w], -1)
    R = mapped(U)
    # rings run top (u_top) to bottom (u_bot)
    return Grid(R, kind, cap0=mapped(poles[0]), cap1=mapped(poles[1]), meta=meta, density=density)


# ---- the hand, in the local frame (x along the stake, u up, w forward; the stake's axis at u = w = 0)

def finger_joints(b, k, xs):
    """Each finger's joint centres (knuckle, middle, end joint, tip) and half extents."""
    out = []
    for f, x in zip(FINGERS, xs):
        L1, L2, L3 = (k * v for v in f['lengths'])
        hs = k * f['width'] / 2 * 1.03                       # neighbours just touch
        hd = k * f['thick']
        corner = b + PRESS * hd                              # middle joint: over the top-front edge of the stake
        a, l, g = np.radians(f['rise']), np.radians(f['lean']), np.radians(f['tuck'])
        P = np.array([x, corner, corner])
        M = P - L1 * np.array([0.0, np.sin(a), np.cos(a)])
        D = P + L2 * np.array([0.0, -np.cos(l), -np.sin(l)])
        Tp = D + L3 * np.array([0.0, -np.sin(g), -np.cos(g)])
        out.append(dict(x=x, M=M, P=P, D=D, T=Tp, hs=hs, hd=hd, L3=L3))
    return out


def away(seg_a, seg_b, x):
    """The direction square to a finger segment (in its x plane) that points away from the stake."""
    d = unit(seg_b - seg_a)
    p = np.array([0.0, -d[2], d[1]])
    mid = (seg_a + seg_b) / 2 - np.array([x, 0.0, 0.0])
    return p if p @ mid > 0 else -p


def palm_shape(b, half_w, k, J):
    """The back of the hand and the palm as one deformed superellipsoid: its section functions."""
    Mx = np.array([j['x'] for j in J])
    Mu = np.array([j['M'][1] for j in J])
    Mw = np.array([j['M'][2] for j in J])
    hd = np.array([j['hd'] for j in J])
    wrist_hx, wrist_hz = k * WRIST_MM[0] / 2, k * WRIST_MM[1] / 2
    u_bot = -6.6 * b / 1.55                                  # the wrist (the hand's base) below the stake
    knuckle_back = Mw - 0.7 * hd
    back_low_u = (u_bot, 0.53 * u_bot)
    back_low_w = (-(2.45 + wrist_hz) * b / 1.55, -4.5 * b / 1.55)
    xl_knots = ((u_bot, -wrist_hx), (0.55 * u_bot, -half_w * 0.88), (0.25 * u_bot, -half_w * 0.95),
                (Mu.max(), -half_w * 0.95))
    xr_knots = ((u_bot, wrist_hx), (0.55 * u_bot, half_w * 0.86), (0.25 * u_bot, half_w * 0.97),
                (Mu.min(), half_w * 0.93))
    front_knots = ((u_bot, 0.0), (0.68 * u_bot, -0.15), (0.45 * u_bot, -0.55), (-b * 1.1, -b + 0.25),
                   (0.0, -b + 0.2), (Mu.max(), -b + 0.45))

    def xl(u):
        return np.interp(u, *zip(*xl_knots))

    def xr(u):
        return np.interp(u, *zip(*xr_knots))

    def u_top(x):
        return np.interp(x, Mx, Mu + 0.2 * hd)

    def w_back(x, u):
        top = np.interp(x, Mx, knuckle_back)
        low = np.interp(u, back_low_u, back_low_w)
        s = np.clip((u - back_low_u[1]) / (u_top(x) - 0.4 - back_low_u[1]), 0.0, 1.0)
        s = s * s * (3 - 2 * s)
        return low + (top - low) * s

    def w_front(x, u):
        w = np.interp(u, *zip(*front_knots))
        hyp = 0.25 * np.clip(x / half_w, 0, 1) * np.exp(-((u - 0.45 * u_bot) / 1.6) ** 2)   # hypothenar
        return w + hyp

    return dict(u_bot=u_bot, xl=xl, xr=xr, u_top=u_top, w_back=w_back, w_front=w_front, e=3.0,
                u_top_mean=float(np.mean(Mu + 0.2 * hd)), wrist_w=(back_low_w[0] + 0.0) / 2)


def curl_filler(b, half_w, J):
    """The flesh inside the curl: under the proximal phalanges (from the knuckles to the stake), behind the middle
    ones and down under the stake to the palm, so the side of the fist shows no hole."""
    xs = np.array([j['x'] for j in J])
    top = np.array([j['M'][1] for j in J]) + 0.1
    back = np.array([j['M'][2] + 0.4 * j['hd'] for j in J])
    front = np.array([j['P'][2] - 0.55 * j['hd'] for j in J])
    u_bot = -2.4 * b / 1.55
    return dict(xl=lambda u: np.full_like(np.asarray(u, float), -0.9 * half_w),
                xr=lambda u: np.full_like(np.asarray(u, float), 0.9 * half_w),
                u_bot=u_bot, u_top=lambda x: np.interp(x, xs, top), u_top_mean=float(top.mean()),
                w_back=lambda x, u: np.interp(x, xs, back),
                w_front=lambda x, u: np.where(u > -0.5, np.interp(x, xs, front),
                                              -0.2 + (np.interp(x, xs, front) + 0.2) * (u - u_bot) / (-0.5 - u_bot)),
                e=4.0)


def thumb(half_w, k):
    p = {n: np.array([THUMB[n][0] * half_w, k * THUMB[n][1], k * THUMB[n][2]]) for n in ('cmc', 'mcp', 'ip', 'tip')}
    rad = [(k * a, k * d) for a, d in THUMB['radii']]
    refs = ((-0.85, 0.0, 0.55), (-0.25, 0.15, 1.0), (0.0, 0.3, 1.0))
    side_ref = np.array([0.0, 1.0, 0.0])
    grids = []
    names = ('cmc', 'mcp', 'ip', 'tip')
    wrinkles = ((), (1,), (0,))          # the joint ends (0 = start, 1 = end) with knuckle wrinkles: the IP joint
    for i in range(3):
        A, B = p[names[i]], p[names[i + 1]]
        grids.append(capsule(A, B, side_ref, np.array(refs[i]), rad[i], rad[i + 1], e=2.2, waist=0.04,
                             meta=dict(wrinkle_ends=wrinkles[i])))
    # the thenar mound: the fleshy pad between the thumb's metacarpal and the palm
    d = unit(p['mcp'] - p['cmc'])
    toward_palm = np.array([0.6, 0.0, -0.5])
    inward = unit(toward_palm - d * (toward_palm @ d))
    third = np.cross(d, inward)
    c = p['cmc'] + (p['mcp'] - p['cmc']) * 0.46 + inward * k * 8.0
    grids.append(ellipsoid(c, (inward, d, third), (k * 16.0, k * 31.0, k * 15.0)))
    # the thumbnail, outward
    d3 = unit(p['tip'] - p['ip'])
    n3 = unit(np.array(refs[2]) - d3 * (np.array(refs[2]) @ d3))
    L3 = np.linalg.norm(p['tip'] - p['ip'])
    at = p['ip'] + d3 * 0.6 * L3 + n3 * rad[2][1] * 0.82
    grids.append(ellipsoid(at, (np.cross(d3, n3), d3, n3), (rad[2][0] * 0.62, L3 * 0.36, k * NAIL[2] * 1.1),
                           kind='nail', meta=dict(side=np.cross(d3, n3))))
    return grids


def hand(b, half_w):
    """The hand at the build size, local frame. Returns grids, the scale k (units per mm) and the palm's shape."""
    k = 2 * half_w * 0.97 / HAND_BREADTH_MM
    widths = np.array([f['width'] for f in FINGERS])
    widths = widths / widths.sum() * 2 * half_w * 0.97
    xs = -half_w * 0.97 + np.concatenate([[0.0], np.cumsum(widths)[:-1]]) + widths / 2
    J = finger_joints(b, k, xs)
    grids = []
    X = np.array([1.0, 0.0, 0.0])
    for j in J:
        hs, hd = j['hs'], j['hd']
        ext = [(hs * t, hd * t) for t in TAPER]
        segs = ((j['M'], j['P'], ext[0], ext[1], (1,)), (j['P'], j['D'], ext[1], ext[2], (0, 1)),
                (j['D'], j['T'], ext[2], ext[3], (0,)))
        for A, B, ha, hb, wr in segs:              # wrinkles over the middle and end joints, not the knuckle
            grids.append(capsule(A, B, X, away(A, B, j['x']), ha, hb, meta=dict(wrinkle_ends=wr)))
        # the knuckle: the metacarpal head, bone standing out of the back of the hand
        d1 = unit(j['P'] - j['M'])
        n1 = away(j['M'], j['P'], j['x'])
        kd = unit(0.45 * n1 + np.array([0.0, 0.0, -1.0]))
        rs, rd, rw, lift = KNUCKLE_BONE
        grids.append(ellipsoid(j['M'] + kd * lift * hd, (X, d1, kd), (hs * rs, hd * rd, hd * rw), kind='bone'))
        # the nail on the fingertip (its back faces away from the stake)
        d3 = unit(j['T'] - j['D'])
        n3 = away(j['D'], j['T'], j['x'])
        at = j['D'] + d3 * (0.62 * j['L3']) + n3 * (hd * TAPER[2] * 0.86)
        grids.append(ellipsoid(at, (X, d3, n3), (hs * TAPER[2] * NAIL[0], j['L3'] * NAIL[1], k * NAIL[2]),
                               kind='nail', meta=dict(side=X)))
    S = palm_shape(b, half_w, k, J)
    grids.append(deformed_box(S, 'palm'))
    # the metacarpals breaking through the back of the hand, from the wrist to the knuckle heads
    out = np.array([0.0, 0.0, -1.0])
    for j, bx in zip(J, METACARPAL_BASES):
        f = np.linspace(0, 1, 22)
        head = j['M']
        x = bx * k + (head[0] - bx * k) * f
        u = METACARPAL_BASE_U * k + (head[1] - 0.35 * j['hd'] - METACARPAL_BASE_U * k) * f
        hd = np.interp(f, [q[0] for q in METACARPAL], [q[2] for q in METACARPAL]) * k * BONE_SIZE
        q = np.interp(f, [p_[0] for p_ in PROTRUDE], [p_[1] for p_ in PROTRUDE])
        w = palm_back(S, x, u) - (2 * q - 1) * hd                    # q of its depth out of the skin
        w = np.minimum(w, j['M'][2])                                # never in front of its knuckle
        C = np.stack([x, u, w], -1)
        k3 = np.ones(5) / 5                                          # smooth the path a little
        C = np.stack([np.convolve(np.pad(C[:, i], 2, mode='edge'), k3, mode='valid') for i in range(3)], -1)
        grids.append(bone_path(C, out, METACARPAL, k, BONE_SIZE))
    # carpals peeping out at the back of the wrist
    for (cx, cu), rr, q in WRIST_BONES:
        r = np.array(rr) * k
        w = float(palm_back(S, cx * k, cu * k)) - (2 * q - 1) * r[2]
        grids.append(ellipsoid((cx * k, cu * k, w), np.eye(3), r, kind='bone'))
    grids.append(deformed_box(curl_filler(b, half_w, J), 'skin', nu=36, nv=26, density=0.5))   # mostly hidden
    # the hypothenar: the pad along the little finger's edge of the palm, under the curled fingertips
    grids.append(ellipsoid((half_w * 0.6, 0.52 * S['u_bot'], -1.25 * b / 1.55), np.eye(3),
                           (k * 13.0, k * 21.0, k * 9.0)))
    grids += thumb(half_w, k)
    return grids, k, S


def inside(points, poly):
    """Even-odd test of 2D points against a closed polygon."""
    x, y = points[:, 0][:, None], points[:, 1][:, None]
    x1, y1 = poly[:, 0][None, :], poly[:, 1][None, :]
    x2, y2 = np.roll(poly[:, 0], -1)[None, :], np.roll(poly[:, 1], -1)[None, :]
    cross = ((y1 > y) != (y2 > y)) & (x < (x2 - x1) * (y - y1) / np.where(y2 != y1, y2 - y1, 1e-12) + x1)
    return cross.sum(1) % 2 == 1


def into_shaft(palm, c, R, sc, k, S, shaft_r):
    """The palm's rings cut at the wrist (WRIST_CUT_MM above its base, before its rounded bottom) and run on down as
    the forearm, one surface with the hand: the first rings keep the wrist's own section, then it narrows, turns a
    little and settles, nearly tangent, into a round just over the shaft's ridges (FOREARM['over'] x its radius) on
    the shaft's axis, where it ends; the shaft's twisted flutes run out from under it (an exact fit to its fluted,
    twisting section left the arm showing through the flutes). Mesh frame. Returns the y where the forearm ends and
    the highest y where it still holds the whole shaft, and its rings (mesh frame, centred on c)."""
    u_mm = palm.paint[:, :, 1].mean(1)
    cut = int(np.argmin(np.abs(u_mm - (S['u_bot'] / k + WRIST_CUT_MM))))
    keep = palm.P[:cut + 1] - c
    top = keep[-1]
    ctr = top.mean(0)
    D = top - ctr
    m = top.shape[0]
    a = 2 * np.pi * np.arange(m) / m
    base = R @ np.array([0.0, S['u_bot'], S['wrist_w']]) * sc
    join = base[1] - FOREARM['length']
    y0 = ctr[1]
    rings = []
    for f in np.linspace(0.0, 1.0, 28)[1:]:
        y = y0 + (join - y0) * f
        g = np.clip((f - 0.1) / 0.9, 0, 1)
        g = g * g * (3 - 2 * g)                                     # the wrist at first, then easing in
        rx = np.abs(D[:, 0]).max() * (1 - g) + shaft_r * FOREARM['over'] * g
        rz = np.abs(D[:, 2]).max() * (1 - g) + shaft_r * FOREARM['over'] * g
        e = 2.6 - 0.6 * g
        turn = np.radians(FOREARM['turn']) * g
        cs, sn = se(a, e)
        px, pz = rx * cs, rz * sn
        ox, oz = px * np.cos(turn) - pz * np.sin(turn), px * np.sin(turn) + pz * np.cos(turn)
        b = np.clip(f / 0.3, 0, 1)
        b = b * b * (3 - 2 * b)                                     # from the palm's own section to the oval
        cx, cz = ctr[0] * (1 - g), ctr[2] * (1 - g)
        rings.append(np.stack([cx + (1 - b) * D[:, 0] + b * ox, y + (1 - b) * D[:, 1],
                               cz + (1 - b) * D[:, 2] + b * oz], -1))
    # how high the shaft may run up inside: the forearm leans back as it rises, so above some height the shaft
    # would come out of its front
    circle = shaft_r * np.stack([np.cos(a[::2]), np.sin(a[::2])], -1)
    held = join
    for ring in rings[::-1]:
        if not inside(circle, ring[:, [0, 2]]).all():
            break
        held = float(ring[:, 1].mean())
    P = np.concatenate([keep, np.array(rings)], 0) + c
    palm.P = P
    palm.cap1 = P[-1].mean(0)
    palm.paint = ((P - c) @ R) / sc / k                             # back to the local frame, mm
    palm.paint_cap1 = ((palm.cap1 - c) @ R) / sc / k
    palm.meta['skin_fade'] = (S['u_bot'] / k - FOREARM['metal_mm'][1], S['u_bot'] / k - FOREARM['metal_mm'][0])
    return join, held, rings


def ring_surface(rings):
    """The forearm's surface from its rings (top to bottom): the point at height y and angle theta round each ring's
    own centre, and the outward normal there."""
    rings = [np.asarray(r, float) for r in rings]
    ys = np.array([r[:, 1].mean() for r in rings])
    tabs = []
    for r in rings:
        cx, cz = r[:, 0].mean(), r[:, 2].mean()
        phi = np.arctan2(r[:, 2] - cz, r[:, 0] - cx)
        o = np.argsort(phi)
        ph, rr, yy = phi[o], np.hypot(r[o, 0] - cx, r[o, 2] - cz), r[o, 1]
        ph = np.concatenate([ph - 2 * np.pi, ph, ph + 2 * np.pi])
        tabs.append((cx, cz, ph, np.tile(rr, 3), np.tile(yy, 3)))

    def point(y, theta):
        i = int(np.clip(np.searchsorted(-ys, -y) - 1, 0, len(ys) - 2))
        f = np.clip((ys[i] - y) / (ys[i] - ys[i + 1]), 0, 1)
        th = (theta + np.pi) % (2 * np.pi) - np.pi
        P = []
        for cx, cz, ph, rr, yy in (tabs[i], tabs[i + 1]):
            r = np.interp(th, ph, rr)
            P.append(np.array([cx + r * np.cos(th), np.interp(th, ph, yy), cz + r * np.sin(th)]))
        return P[0] * (1 - f) + P[1] * f

    def surface(y, theta):
        P = point(y, theta)
        tu = point(y, theta + 0.01) - point(y, theta - 0.01)
        tv = point(y + 0.02, theta) - point(y - 0.02, theta)
        n = unit(np.cross(tu, tv))
        ax = np.array([P[0] - np.interp(y, ys[::-1], [t[0] for t in tabs][::-1]), 0.0,
                       P[2] - np.interp(y, ys[::-1], [t[1] for t in tabs][::-1])])
        return P, (n if n @ ax > 0 else -n)
    return surface


def thorn_bracelet(join, shaft_r):
    """Round the forearm's end, where it becomes the shaft (mesh frame, centred on the shaft's axis): two thorny
    strands twisted round each other into a ring, its inner side resting on the arm's end, thorns pointing out, up and
    down (curator 2026-11-14: "a bracelet of thorns to help blend the wrist to handle")."""
    B = THORNS
    end_r = shaft_r * FOREARM['over']
    R0 = end_r + B['twist'] + B['strand'] * 0.75                   # the ring's centre line: strands just touch the arm
    y0 = join + B['rise']
    t = np.linspace(0, 2 * np.pi, B['samples'] + 1)
    t = np.concatenate([t, t[1:3] + 2 * np.pi])                    # run on past the start: the loop closes inside itself
    er = np.stack([np.cos(t), np.zeros_like(t), np.sin(t)], -1)
    ey = np.array([0.0, 1.0, 0.0])
    out, strands = [], []
    for k in range(2):                                              # two branches, a little uneven, like wood
        ph = B['turns'] * t + np.pi * k
        tw = B['twist'] * (1 + 0.25 * np.sin(3 * t + 1.3 * k))
        off = tw[:, None] * (np.cos(ph)[:, None] * er + np.sin(ph)[:, None] * ey)
        C = R0 * er + y0 * ey + off
        strands.append((C, off / tw[:, None] * B['twist']))
        out.append(tube(C, B['strand'] * (1 + 0.15 * np.sin(5 * t + 2.1 * k)), 'thorn', m=10))
    rng = np.random.RandomState(7)
    for i in range(B['count']):                                     # thorns along both strands, alternately
        C, off = strands[i % 2]
        j = int((i + 0.5) / B['count'] * B['samples'])
        out_dir = unit(off[j] / B['twist'] * 0.6 + er[j] * 1.0 + ey * rng.uniform(-0.7, 0.7))
        base = C[j] + out_dir * B['strand'] * 0.6
        tip = base + out_dir * B['thorn'][0] * rng.uniform(0.8, 1.15)
        hook = unit(np.cross(er[j], ey)) * B['thorn'][0] * 0.18 * (1 if i % 3 else -1)
        n = 7
        f = np.linspace(0, 1, n)
        Cn = base + np.outer(f, tip - base) + np.outer(f ** 2, hook)      # curved a little, like a rose thorn
        out.append(tube(Cn, B['thorn'][1] * np.linspace(1, 0.04, n) ** 1.3, 'thorn', m=8))
    return out


def socket(x_end, toward, half, stake_r):
    """Round a neck's cut end (at mesh-local x_end, the fist toward `toward` = +-1): a superellipse-sectioned
    socket over the neck's last SOCKET['over'], closing down onto the stake past the end."""
    hy, hz = half[0] + SOCKET['margin'], half[1] + SOCKET['margin']
    prof = [(-SOCKET['over'], 0.95), (-SOCKET['over'] + 0.06, 1.0), (SOCKET['reach'] - 0.08, 1.0),
            (SOCKET['reach'], 0.94), (SOCKET['reach'] + 0.05, None), (SOCKET['reach'] + SOCKET['shoulder'], 'stake')]
    m = 40
    a = 2 * np.pi * np.arange(m) / m
    R = []
    for d, f in prof:
        x = x_end + toward * d
        if f == 'stake':
            ry = rz = stake_r * 1.04
            e = 2.0
        elif f is None:
            ry, rz, e = 0.82 * hy, 0.82 * hz, 3.0
        else:
            ry, rz, e = f * hy, f * hz, 3.5
        cs, sn = se(a, e)
        R.append(np.stack([np.full(m, x), ry * cs, rz * sn], -1))
    R = np.array(R)
    return Grid(R, 'socket', cap0=R[0].mean(0), cap1=R[-1].mean(0), meta=dict(x=[x_end + toward * d for d, _ in prof]))


def fist(c, neck_x, neck_half, shaft_r):
    c = np.asarray(c, float)
    grids, k, S = hand(BUILD_STAKE_R, BUILD_HALF_W)
    # scaled about the stake and cocked back (TILT); the forearm carries the wrist's remaining offset onto the shaft
    th = -np.radians(TILT)
    cth, sth = np.cos(th), np.sin(th)
    R = np.array([[1.0, 0.0, 0.0], [0.0, cth, -sth], [0.0, sth, cth]])   # acts on (x, u, w)
    sc = HAND_SCALE
    for g in grids:
        g.paint = g.P / k                                    # millimetres of the full-size hand, local frame
        g.paint_cap0 = None if g.cap0 is None else g.cap0 / k
        g.paint_cap1 = None if g.cap1 is None else g.cap1 / k
        g.paint_rot = R.T                                    # mesh directions back to the local frame
        g.meta['mm'] = 1.0 / k
        g.apply(lambda P: c + (sc * np.asarray(P)) @ R.T)
        if 'A' in g.meta:
            g.meta['A'] = g.meta['A'] / k
        if 'L' in g.meta:
            g.meta['L'] = g.meta['L'] / k
            g.meta['hd'] = g.meta['hd'] / k
    ks = k * sc                                              # mesh units per mm of the full-size hand
    join, held, arm = into_shaft(next(g for g in grids if g.kind == 'palm'), c, R, sc, k, S, shaft_r)
    stake_r = BUILD_STAKE_R * sc * STAKE_PRESS
    x0, x1 = neck_x[0] - c[0], neck_x[1] - c[0]
    xs = np.linspace(x0 + SOCKET['reach'] * 0.5, x1 - SOCKET['reach'] * 0.5, 24)
    stake = tube(np.stack([xs, np.zeros_like(xs), np.zeros_like(xs)], -1), np.full(len(xs), stake_r), 'stake', m=28,
                 density=0.6)                                # plain polished
    sockets = [socket(x0, 1.0, neck_half, stake_r), socket(x1, -1.0, neck_half, stake_r)]
    bracelet = thorn_bracelet(join, shaft_r)
    import roses                                             # the rose vine up the forearm, bracelet to wrist
    top = float(np.mean(arm[0][:, 1]))
    garden = roses.forearm_roses(ring_surface(arm), join + ROSE_VINE[0], top - ROSE_VINE[1])
    for g in garden:
        g.meta['group'] = 'roses'                            # its own shape (one holds at most 65,535 triangles)
    for g in [stake] + sockets + bracelet + garden:
        g.paint = g.P / ks
        g.paint_cap0 = None if g.cap0 is None else g.cap0 / ks
        g.paint_cap1 = None if g.cap1 is None else g.cap1 / ks
        g.meta['mm'] = 1.0 / ks
        g.apply(lambda P: c + np.asarray(P))
    grids += [stake] + sockets + bracelet + garden
    info = dict(shaft_join_y=c[1] + join, shaft_held_y=c[1] + held, stake_r=stake_r, units_per_mm=ks,
                hand_x=(c[0] - BUILD_HALF_W * sc, c[0] + BUILD_HALF_W * sc))
    return grids, info
