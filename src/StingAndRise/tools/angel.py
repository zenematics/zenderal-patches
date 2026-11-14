"""Rise's ornaments (curator 2026-11-13): "an Angel on the pommel ... and wings on the cross guard". Curator's picks:
the angel holds a sun overhead, the guard's wings spread out sideways, both polished gold. Our own geometry,
generated here (as Sting's spider, spider.py).

Rise is Pretty Enderal Armory's Aeterna dagger: one shape, blade along +Y, the grip's wrap ending in a ring band
(bottom y -6.13, about 2.9 x 2.2), under it a faceted pommel knob down to y -8.71; a cross guard whose twisted arms
run from the centre block (|x| ~1.9) to blocks at x +6.25 / -6.02 (y 5.6 .. 7.8, z +-0.97). Curator, after the
first build (wings on the guard's ends, the angel under the knob): "I wanted them overlaying the existing
crossguard ... the pommel should be replaced with the angel". So (tools/01 removes the knob):

- the angel replaces the knob: a socket caps the ring band, the figure stands on it, its "up" along -Y (away from
  the blade), facing +Z: a robe with folds, head and hair, both arms raised holding a rayed sun disc above its head,
  and two small raised wings on its back;
- each guard arm lies INSIDE a wing spread sideways: the wing's leading edge is a sheath sized from the measured
  arm (+ a margin) all along it, then it carries on past the arm's end to the tip; coverts over both faces,
  secondaries hanging toward the grip, primaries fanning at the tip.

Every part is a closed volume, oriented outward (counter-clockwise seen from outside, as Pretty's mesh: checked by
signed volume), with smooth normals of its own. `angel(base, socket)` and `overlay_wing(env, sx)` return a list of
(V, N, T) in the dagger's own coordinates.
"""
import numpy as np

# ---- the angel, in its own frame: x right, h up (away from the blade), z front -----------------------------
SCALE = 1.3                           # the figure (not the socket); at 1.0 it was the size of the old knob
# the socket that caps the ring band, in absolute units: (h, radius as a fraction of the band's half width); oval as
# the band; from 0.3 inside it, flaring a little over its rim, then narrowing to the robe's hem
SOCKET = ((-0.30, 0.90), (-0.14, 1.07), (0.0, 1.10), (0.12, 1.08), (0.24, 0.98), (0.38, 0.78), (0.50, 0.58),
          (0.60, 0.46))      # its rim clears the band's (1.10 x): equal radii made the two surfaces flicker
FIGURE_SINK = 0.08                    # the robe's hem sits this far into the socket's top
ROBE = ((0.28, 0.60), (0.40, 0.63), (0.65, 0.54), (1.00, 0.43), (1.35, 0.34), (1.60, 0.30), (1.85, 0.33),
        (2.10, 0.37), (2.30, 0.40), (2.45, 0.30), (2.52, 0.14))
ROBE_Z = 0.78                         # front-to-back depth of the robe against its width
SHOULDER_X = 0.12                     # the chest and shoulders are this much wider than round (h 1.85 .. 2.3)
SHOULDER_H = (1.85, 2.30, 2.50)       # widening starts, full width, gone (the neck)
FOLDS, FOLD_DEPTH = 9, 0.09           # vertical folds in the skirt, fading out at the waist
WAIST_H = 1.60
NECK = ((2.46, 0.11), (2.60, 0.10), (2.74, 0.10))
HEAD = dict(c=(0.0, 2.95, 0.03), r=(0.28, 0.32, 0.30))
HAIR = (dict(c=(0.0, 3.00, -0.05), r=(0.30, 0.32, 0.30)), dict(c=(0.0, 2.72, -0.15), r=(0.25, 0.32, 0.16)))
ARM = ((0.38, 2.26, 0.00), (0.56, 2.56, 0.06), (0.62, 2.88, 0.10), (0.50, 3.22, 0.12), (0.40, 3.47, 0.13))
ARM_R = (0.14, 0.14, 0.16, 0.12, 0.10)   # a bell sleeve at the elbow
HAND = dict(c=(0.33, 3.62, 0.13), r=(0.09, 0.12, 0.08))
SUN = (0.0, 4.18, 0.12)               # the sun disc's centre: held overhead, its lower rim in the hands
SUN_R, SUN_T = (0.58, 0.07), (0.125, 0.07)   # radius; half thickness at the centre / at the rim
RAYS = tuple(range(-30, 211, 30))     # degrees (0 = right, 90 = up): none below, where the hands hold it
RAY_LEN = (0.46, 0.30)                # alternating long / short
RAY_W, RAY_T, RAY_FROM = 0.11, 0.05, 0.50
BACK_WING = dict(root=(0.12, 2.12, -0.22), length=1.35, rise=0.55, yaw=30.0, lift=58.0)   # lift: span above level
# (the angel was Rise's pommel until the curator's "change the angel for just a Sun"; angel() stays for reference)

# ---- the sun pommel (sun_pommel), on the same socket, absolute units --------------------------------------------
SUN_NECK = ((0.50, 0.46), (0.62, 0.40), (0.80, 0.38), (0.95, 0.42))   # (h, r): the socket's top into the disc
SUN_PM_SINK = 0.25                    # the disc's rim reaches this far into the neck
SUN_PM_R = 1.35                       # disc radius (the grip band is ~1.4 x 1.1)
SUN_PM_T = (0.42, 0.24)               # half thickness at the centre / at the rim (domed both faces)
SUN_PM_RING = (0.70, 0.075)           # a raised ring on each face: at this fraction of the radius, tube radius
SUN_PM_RAYS = 16                      # rays every 360/16 deg, alternating long / short ...
SUN_PM_RAY_LEN = (1.05, 0.62)
SUN_PM_RAY_W, SUN_PM_RAY_T = 0.24, 0.14
SUN_PM_GAP = 35                       # ... none within this many degrees of the neck

# ---- the guard wings, in the dagger's frame ------------------------------------------------------------------
SHEATH_MARGIN = (0.14, 0.12)          # the leading edge clears the guard arm by this much (in y, in z)
SHEATH_P = 4.0                        # its section: a superellipse this square (tools/01 asserts it holds the arm)
# Curator 2026-11-13: "a little smaller in length": the part past the arm's end 2.5 -> 1.9, primaries 3.0/2.3 ->
# 2.4/1.9, covert rows pulled in; span ~11.7 -> ~10 each side (the sheath over the arm itself cannot shrink)
PAST_END = ((0.5, 0.10, 0.86, 0.80), (1.1, 0.35, 0.56, 0.48), (1.9, 0.80, 0.28, 0.24))   # beyond the arm's end:
                                      # (dx, dy, y half and z half as fractions of the end's): a smooth taper
COVERT_ROWS = (                       # rows on each face: (from x, to x past the end, count, hang angle from
    (0.15, 0.9, 8, -48.0, 0.95, 0.38, 0.07, 0.50),       # outward, length, half width, half thickness, how far up
    (0.3, 1.2, 6, -70.0, 1.85, 0.46, 0.08, -0.10))      # the sheath its base sits (fraction of the y half));
                                      # the upper row: short overlapping scales over the leading edge
SECONDARIES = (0.4, 0.4, 6, -82.0, -74.0, 2.45, 0.50, 0.11)   # from x, to x past the end, count, angles, len, w, t
PRIMARIES = (6, -6.0, -62.0, 2.4, 1.9, 0.50, 0.11)            # count, angles, length tip -> inner, w, t


def oriented(V, T):
    """Flip the winding if the closed volume came out inside-out (signed volume < 0)."""
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    vol = np.einsum('ij,ij->i', a, np.cross(b, c)).sum() / 6.0
    return T if vol > 0 else T[:, ::-1].copy()


def normals(V, T):
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    fn = np.cross(b - a, c - a)
    N = np.zeros_like(V)
    for i in range(3):
        np.add.at(N, T[:, i], fn)
    n = np.linalg.norm(N, axis=1, keepdims=True)
    return N / np.where(n > 1e-12, n, 1.0)


def part(V, T):
    V = np.asarray(V, float)
    T = oriented(V, np.asarray(T, np.int64))
    return V, normals(V, T), T


def catmull_rom(P, steps):
    P = np.asarray(P, float)
    P = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    out = []
    segs = len(P) - 3
    for k in range(steps):
        t = k / (steps - 1) * segs
        s = min(int(t), segs - 1)
        u = t - s
        p0, p1, p2, p3 = P[s:s + 4]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u
                          + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3))
    return np.array(out)


def rings(R, close_start=True, close_end=True):
    """Triangles of a stack of rings (rows of R[k] points, wrapped), each end closed with a centre vertex."""
    R = np.asarray(R, float)
    n, m = R.shape[:2]
    V = list(R.reshape(-1, 3))
    T = []
    for k in range(n - 1):
        for i in range(m):
            a, b = k * m + i, k * m + (i + 1) % m
            T += [(a, b, a + m), (b, b + m, a + m)]
    if close_start:
        c = len(V)
        V.append(R[0].mean(0))
        T += [(c, (i + 1) % m, i) for i in range(m)]
    if close_end:
        c = len(V)
        V.append(R[-1].mean(0))
        last = (n - 1) * m
        T += [(c, last + i, last + (i + 1) % m) for i in range(m)]
    return np.array(V), np.array(T)


def lathe(profile, m=32, zscale=1.0, xwide=None, ripple=None, steps=None):
    """Around the h axis: profile = ((h, r), ...); x radius r * (1 + xwide(h)), z radius r * zscale, optional
    ripple(h, phi) multiplying the radius."""
    prof = catmull_rom(np.array([(r, h, 0.0) for h, r in profile]), steps or 4 * len(profile))
    phi = 2 * np.pi * np.arange(m) / m
    R = []
    for r, h, _ in prof:
        r = max(r, 0.0)
        xr = r * (1.0 + (xwide(h) if xwide else 0.0))
        rr = (ripple(h, phi) if ripple else 1.0)
        R.append(np.stack([xr * rr * np.cos(phi), np.full(m, h), r * zscale * rr * np.sin(phi)], -1))
    return rings(R)


def ellipsoid(c, r, nu=20, nv=12):
    c, r = np.asarray(c, float), np.asarray(r, float)
    th = np.pi * np.arange(1, nv) / nv
    ph = 2 * np.pi * np.arange(nu) / nu
    R = [c + r * np.stack([np.sin(t) * np.cos(ph), np.full(nu, np.cos(t)), np.sin(t) * np.sin(ph)], -1)
         for t in th]
    V, T = rings(R, close_start=False, close_end=False)
    top, bot = len(V), len(V) + 1
    V = np.vstack([V, c + r * np.array([0.0, 1.0, 0.0]), c + r * np.array([0.0, -1.0, 0.0])])
    m, n = nu, len(th)
    T = list(T) + [(top, (i + 1) % m, i) for i in range(m)]
    last = (n - 1) * m
    T += [(bot, last + i, last + (i + 1) % m) for i in range(m)]
    return np.array(V), np.array(T)


def frames(C):
    """Parallel-transport frames along a curve: tangents, normals, binormals."""
    tang = np.gradient(C, axis=0)
    tang /= np.linalg.norm(tang, axis=1, keepdims=True)
    ref = np.array([0.0, 0.0, 1.0]) if abs(tang[0, 2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    nrm = np.cross(tang[0], ref)
    nrm /= np.linalg.norm(nrm)
    Ns, Bs = [], []
    for k in range(len(C)):
        if k:
            nrm = nrm - tang[k] * (nrm @ tang[k])
            nrm /= np.linalg.norm(nrm)
        Ns.append(nrm)
        Bs.append(np.cross(tang[k], nrm))
    return tang, np.array(Ns), np.array(Bs)


def tube(C, radius, m=12):
    """A closed tube along curve C with per-sample radius (both ends capped)."""
    tang, Nn, Bn = frames(C)
    a = 2 * np.pi * np.arange(m) / m
    R = [C[k] + radius[k] * (np.cos(a)[:, None] * Nn[k] + np.sin(a)[:, None] * Bn[k]) for k in range(len(C))]
    return rings(R)


def lens_disc(c, radius, half_t, m=36, nr=6):
    """A domed disc in the x-h plane (its axis along z): half thickness half_t[0] at the centre, half_t[1] at the
    rim, rounded edge."""
    c = np.asarray(c, float)
    prof = []
    for k in range(nr + 1):                          # front face, centre -> rim
        s = k / nr
        prof.append((s * radius[0], half_t[0] + (half_t[1] - half_t[0]) * s ** 2))
    for k in range(1, 6):                            # the rounded rim
        a = np.pi / 2 - np.pi * k / 6
        prof.append((radius[0] + half_t[1] * np.cos(a) * 0.6, half_t[1] * np.sin(a)))
    for k in range(nr, -1, -1):                      # back face, rim -> centre
        s = k / nr
        prof.append((s * radius[0], -(half_t[0] + (half_t[1] - half_t[0]) * s ** 2)))
    ph = 2 * np.pi * np.arange(m) / m
    R = [c + np.stack([max(r, 1e-4) * np.cos(ph), max(r, 1e-4) * np.sin(ph), np.full(m, z)], -1) for r, z in prof]
    return rings(R)


def ray(c, angle_deg, r0, length, w, t):
    """A flat pointed ray in the x-h plane, from radius r0 outward."""
    a = np.radians(angle_deg)
    d = np.array([np.cos(a), np.sin(a), 0.0])
    s = np.array([-np.sin(a), np.cos(a), 0.0])
    z = np.array([0.0, 0.0, 1.0])
    c = np.asarray(c, float)
    b = c + d * r0
    tip = c + d * (r0 + length)
    V = np.array([b + s * w + z * t, b - s * w + z * t, b - s * w - z * t, b + s * w - z * t,
                  tip + z * t * 0.25, tip - z * t * 0.25])
    T = np.array([(0, 1, 4), (2, 3, 5), (3, 0, 4), (3, 4, 5), (1, 2, 5), (1, 5, 4), (0, 3, 2), (0, 2, 1)])
    return V, T


# ---- feathers and wings (built in a wing plane: s outward along the span, t toward the leading edge, n its normal)

def feather(base, direction, plane_n, length, width, thick, bend=0.06, rings_n=14, m=8):
    """A closed, lens-section feather from `base` along `direction` (in the plane with normal plane_n): its vane
    widens from the quill, is widest at 55% and rounds off at the tip; it bends a little toward -side."""
    d = np.asarray(direction, float)
    d /= np.linalg.norm(d)
    n = np.asarray(plane_n, float)
    n = n - d * (n @ d)
    n /= np.linalg.norm(n)
    side = np.cross(n, d)
    u = np.linspace(0.0, 1.0, rings_n)
    C = np.asarray(base, float) + np.outer(u * length, d) - np.outer(bend * length * u ** 2, side)
    w = np.where(u <= 0.55, width * (0.45 + 0.55 * u / 0.55),
                 width * np.sqrt(np.clip(1 - ((u - 0.55) / 0.45) ** 2, 0, 1)))
    w = np.maximum(w, 0.004)
    t = np.maximum(thick * (1.0 - 0.55 * u), 0.003) * np.where(u < 0.98, 1.0, 0.4)
    a = 2 * np.pi * np.arange(m) / m
    R = [C[k] + w[k] * np.cos(a)[:, None] * side + t[k] * np.sin(a)[:, None] * n for k in range(rings_n)]
    return rings(R)


def wing(length, rise, n_dir, s_dir, t_dir, root, arm_r, layers=True, thick=0.035, rings_n=14, m=8):
    """One spread wing: root at `root`, its span along s_dir, leading edge toward t_dir, plane normal n_dir;
    feather half thickness `thick` x the span. Returns a list of (V, T)."""
    s_dir, t_dir, n_dir = (np.asarray(v, float) for v in (s_dir, t_dir, n_dir))
    root = np.asarray(root, float)
    L = length

    def at(s, t, nn=0.0):
        return root + s * s_dir + t * t_dir + nn * n_dir

    arm = catmull_rom([at(0, 0), at(0.42 * L, 0.38 * rise * L), at(0.78 * L, 0.82 * rise * L), at(L, rise * L)], 28)
    out = [tube(arm, np.interp(np.linspace(0, 1, len(arm)), [0, 0.5, 1], arm_r), m=12)]

    def on_arm(f):
        return arm[min(int(round(f * (len(arm) - 1))), len(arm) - 1)]

    def dirn(deg):
        a = np.radians(deg)
        return np.cos(a) * s_dir + np.sin(a) * t_dir

    fk = dict(rings_n=rings_n, m=m)
    # primaries: fan at the tip, from nearly outward (-8 deg) to downward (-72 deg)
    for i, f in enumerate(np.linspace(0.97, 0.56, 6)):
        ang = -8 - 64 * i / 5
        out.append(feather(on_arm(f), dirn(ang), n_dir, (0.62 - 0.10 * i / 5) * L, 0.13 * L, thick * L, **fk))
    # secondaries: hanging toward the trailing edge, tilted a little outward
    for i, f in enumerate(np.linspace(0.50, 0.06, 6)):
        ang = -76 - 12 * i / 5
        out.append(feather(on_arm(f), dirn(ang), n_dir, (0.47 - 0.07 * i / 5) * L, 0.12 * L, 0.9 * thick * L, **fk))
    if layers:      # coverts: a shorter row over the feather roots, on each face
        for face in (1.0, -1.0):
            for i, f in enumerate(np.linspace(0.86, 0.06, 6)):
                ang = -40 - 42 * i / 5
                base = on_arm(f) + face * thick * L * n_dir
                out.append(feather(base, dirn(ang), n_dir, 0.24 * L, 0.10 * L, 0.8 * thick * L, bend=0.03, **fk))
    return out


# ---- assembly --------------------------------------------------------------------------------------------------

def sun_pommel(base, socket):
    """Rise's pommel since the curator's "change the angel for just a Sun" (2026-11-13): the socket capping the ring
    band, a short neck, and a domed sun disc in the blade's plane (its faces toward +-Z) with a raised ring on each
    face and pointed rays all round, none where it meets the neck. Same frame as angel()."""
    base = np.asarray(base, float)
    Rm = np.diag([-1.0, -1.0, 1.0])
    rx, rz = socket
    parts = [lathe([(h, f * rx) for h, f in SOCKET], m=40, zscale=rz / rx)]
    parts.append(lathe(SUN_NECK, m=24, zscale=0.85))
    c = (0.0, SOCKET[-1][0] + SUN_PM_SINK + SUN_PM_R, 0.0)
    parts.append(lens_disc(c, (SUN_PM_R, 0.0), SUN_PM_T, m=48, nr=8))
    for face in (1.0, -1.0):                         # a raised ring on each face
        a = np.linspace(0, 2 * np.pi, 64, endpoint=False)
        ring_r = SUN_PM_RING[0] * SUN_PM_R
        zc = face * (SUN_PM_T[0] + (SUN_PM_T[1] - SUN_PM_T[0]) * SUN_PM_RING[0] ** 2 - 0.02)
        C = np.stack([c[0] + ring_r * np.cos(a), c[1] + ring_r * np.sin(a), np.full_like(a, zc)], -1)
        parts.append(torus(C, SUN_PM_RING[1]))
    # rays every 360/N deg from straight out along the axis (90 deg), so the pattern mirrors across the dagger's
    # axis (the first build stepped 360 // 16 = 22 deg and drifted round the disc: lopsided)
    angles = 90.0 + 360.0 * np.arange(SUN_PM_RAYS) / SUN_PM_RAYS
    kept = []
    for i, ang in enumerate(angles):
        off = (ang - 270 + 180) % 360 - 180          # 270 deg = toward the neck (local -h)
        if abs(off) < SUN_PM_GAP:
            continue
        kept.append((round(float(np.cos(np.radians(ang))), 6), round(float(np.sin(np.radians(ang))), 6),
                     SUN_PM_RAY_LEN[i % 2]))
        parts.append(ray(c, ang, SUN_PM_R * 0.9, SUN_PM_RAY_LEN[i % 2], SUN_PM_RAY_W, SUN_PM_RAY_T))
    assert sorted(kept) == sorted((-x, y, n) for x, y, n in kept), 'the rays are not symmetric across the axis'
    return [part(np.asarray(V, float) @ Rm.T + base, T) for V, T in parts]


def torus(C, r, m=10):
    """A closed ring tube along the closed curve C."""
    n = len(C)
    tang = np.roll(C, -1, 0) - np.roll(C, 1, 0)
    tang /= np.linalg.norm(tang, axis=1, keepdims=True)
    a = 2 * np.pi * np.arange(m) / m
    V = []
    for k in range(n):
        out = C[k] - C.mean(0)
        out -= tang[k] * (out @ tang[k])
        out /= np.linalg.norm(out)
        up = np.cross(tang[k], out)
        V.extend(C[k] + r * (np.cos(a)[:, None] * out + np.sin(a)[:, None] * up))
    T = []
    for k in range(n):
        k2 = (k + 1) % n
        for i in range(m):
            i2 = (i + 1) % m
            T += [(k * m + i, k * m + i2, k2 * m + i), (k * m + i2, k2 * m + i2, k2 * m + i)]
    return np.array(V), np.array(T)


def angel(base, socket):
    """The angel in the knob's place; `base` = the centre of the ring band's bottom (dagger coordinates), `socket` =
    the band's half widths (x, z). Its frame: up = -Y, front = +Z, right = -X (a half turn about Z, so no mirror).
    The socket is in absolute units, the figure at SCALE, standing on the socket."""
    base = np.asarray(base, float)
    Rm = np.diag([-1.0, -1.0, 1.0])
    rx, rz = socket
    sock = lathe([(h, f * rx) for h, f in SOCKET], m=40, zscale=rz / rx)
    lift = SOCKET[-1][0] - FIGURE_SINK - ROBE[0][0] * SCALE      # the robe's hem into the socket's top

    def to_dagger(V, s=SCALE, h0=lift):
        return (np.asarray(V, float) * s + np.array([0.0, h0, 0.0])) @ Rm.T + base

    out = [part(to_dagger(sock[0], 1.0, 0.0), sock[1])]
    parts = []

    def xwide(h):
        a, b, c = SHOULDER_H
        return SHOULDER_X * (np.clip((h - a) / (b - a), 0, 1) if h < b else np.clip((c - h) / (c - b), 0, 1))

    def ripple(h, phi):
        fade = np.clip((WAIST_H - h) / (WAIST_H - 0.45), 0, 1)
        return 1.0 + FOLD_DEPTH * fade * np.cos(FOLDS * phi)
    parts.append(lathe(ROBE, m=40, zscale=ROBE_Z, xwide=xwide, ripple=ripple, steps=44))
    parts.append(lathe(NECK, m=16, zscale=0.92))
    parts.append(ellipsoid(**HEAD))
    for h in HAIR:
        parts.append(ellipsoid(**h))
    for sx in (1.0, -1.0):
        P = np.array(ARM) * np.array([sx, 1.0, 1.0])
        C = catmull_rom(P, 30)
        r = np.interp(np.linspace(0, 1, len(C)), np.linspace(0, 1, len(ARM_R)), ARM_R)
        parts.append(tube(C, r, m=12))
        parts.append(ellipsoid(c=np.array(HAND['c']) * np.array([sx, 1, 1]), r=HAND['r'], nu=12, nv=8))
    parts.append(lens_disc(SUN, SUN_R, SUN_T))
    for i, a in enumerate(RAYS):
        parts.append(ray(SUN, a, RAY_FROM, RAY_LEN[i % 2], RAY_W, RAY_T))
    bw = BACK_WING
    for sx in (1.0, -1.0):
        rise = np.radians(bw['lift'])
        yaw = np.radians(bw['yaw'])
        s_dir = np.array([sx * np.cos(rise) * np.cos(yaw), np.sin(rise), -np.cos(rise) * np.sin(yaw)])
        n_dir = np.array([sx * np.sin(yaw), 0.0, np.cos(yaw)])      # faces front, turned with the wing's yaw
        n_dir -= s_dir * (n_dir @ s_dir)
        n_dir /= np.linalg.norm(n_dir)
        t_dir = np.cross(n_dir, s_dir)
        if t_dir[1] < 0:                          # toward the leading (upper) edge
            t_dir = -t_dir
        root = np.array(bw['root']) * np.array([sx, 1, 1])
        for V, T in wing(bw['length'], bw['rise'], n_dir, s_dir, t_dir, root, (0.09, 0.08, 0.05), layers=False,
                         thick=0.045, rings_n=10, m=6):
            parts.append((V, T))
    return out + [part(to_dagger(V), T) for V, T in parts]


def sheath(C, yh, zh, m=24, p=SHEATH_P):
    """A closed tube along C (in the x-y plane) with a superellipse section |y/yh|^p + |z/zh|^p = 1 (p 2 = an
    ellipse, higher = squarer: it has to hold the guard arm's square-ish section): half size yh across the curve in
    the plane, zh along z."""
    tang = np.gradient(C, axis=0)
    tang /= np.linalg.norm(tang, axis=1, keepdims=True)
    z = np.array([0.0, 0.0, 1.0])
    a = 2 * np.pi * np.arange(m) / m
    cy = np.sign(np.cos(a)) * np.abs(np.cos(a)) ** (2.0 / p)
    cz = np.sign(np.sin(a)) * np.abs(np.sin(a)) ** (2.0 / p)
    R = []
    for k in range(len(C)):
        across = np.cross(z, tang[k])
        across /= np.linalg.norm(across)
        R.append(C[k] + yh[k] * cy[:, None] * across + zh[k] * cz[:, None] * z)
    return rings(R)


def inside_sheath(Q, C, yh, zh, p=SHEATH_P):
    """For points Q near the sheath: the superellipse value at the nearest curve sample (< 1 = inside)."""
    k = np.argmin(np.abs(Q[:, None, 0] - C[None, :, 0]), axis=1)
    return np.abs((Q[:, 1] - C[k, 1]) / yh[k]) ** p + np.abs(Q[:, 2] / zh[k]) ** p


def overlay_wing(env, sx):
    """One guard wing over a guard arm. env = ((|x|, y centre, y half, z half), ...) measured along the arm from the
    centre block to its end; sx = +1 right, -1 left. Plane = the blade's x-y plane."""
    env = np.asarray(env, float)
    x_end, y_end = env[-1, 0], env[-1, 1]
    path = [(x, y, yh + SHEATH_MARGIN[0], zh + SHEATH_MARGIN[1]) for x, y, yh, zh in env]
    end_yh, end_zh = path[-1][2], path[-1][3]
    path += [(x_end + dx, y_end + dy, fy * end_yh, fz * end_zh) for dx, dy, fy, fz in PAST_END]
    path = np.array(path)
    steps = 40
    C = catmull_rom(np.stack([sx * path[:, 0], path[:, 1], np.zeros(len(path))], -1), steps)
    u_path = np.linspace(0, 1, len(path))
    u = np.linspace(0, 1, steps)
    # the half sizes follow the curve's own parameter (catmull_rom passes through the path points at even u)
    yh = np.interp(u, u_path, path[:, 2])
    zh = np.interp(u, u_path, path[:, 3])
    overlay_wing.last = (C, yh, zh)          # for tools/01's containment check
    out = [sheath(C, yh, zh)]
    s_dir, t_dir, n_dir = np.array([sx, 0.0, 0.0]), np.array([0.0, 1.0, 0.0]), np.array([0.0, 0.0, 1.0])

    def dirn(deg):
        a = np.radians(deg)
        return np.cos(a) * s_dir + np.sin(a) * t_dir

    def at(x):
        """Centre, y half, z half of the sheath at |x| (x past the end allowed up to the tip)."""
        k = int(np.argmin(np.abs(np.abs(C[:, 0]) - x)))
        return C[k], yh[k], zh[k]
    fk = dict(rings_n=10, m=8)
    x0 = env[0, 0]
    # coverts: rows on both faces, hanging over the sheath's lower half and past its edge
    for frm, past, n, ang, length, w, t, up in COVERT_ROWS:
        for i, x in enumerate(np.linspace(x0 + frm, x_end + past, n)):
            c, h, d = at(x)
            for face in (1.0, -1.0):
                base = c + up * h * t_dir + face * (d - 0.5 * t) * n_dir
                out.append(feather(base, dirn(ang + 10 * i / max(n - 1, 1)), n_dir, length, w, t, bend=0.04, **fk))
    # secondaries: in the middle plane, from the sheath's lower edge, hanging toward the grip
    frm, past, n, a0, a1, length, w, t = SECONDARIES
    for i, x in enumerate(np.linspace(x0 + frm, x_end + past, n)):
        c, h, d = at(x)
        out.append(feather(c - 0.6 * h * t_dir, dirn(a0 + (a1 - a0) * i / (n - 1)), n_dir, length, w, t, **fk))
    # primaries: fanning from the part past the arm's end, nearly outward at the tip to downward
    n, a0, a1, l0, l1, w, t = PRIMARIES
    x_tip = abs(C[-1, 0])
    for i, x in enumerate(np.linspace(x_tip - 0.15, x_end - 0.2, n)):
        c, h, d = at(x)
        out.append(feather(c, dirn(a0 + (a1 - a0) * i / (n - 1)), n_dir, l0 + (l1 - l0) * i / (n - 1), w, t, **fk))
    return [part(V, T) for V, T in out]


def merge(parts):
    """One mesh from parts: vertices, normals, triangles."""
    Vs, Ns, Ts, off = [], [], [], 0
    for V, N, T in parts:
        Vs.append(V)
        Ns.append(N)
        Ts.append(T + off)
        off += len(V)
    return np.vstack(Vs), np.vstack(Ns), np.vstack(Ts)
