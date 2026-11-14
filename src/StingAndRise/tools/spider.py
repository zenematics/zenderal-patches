"""A small metal spider clutching Sting's pommel (curator 2026-11-13: "add a metal spider to the hilt of Sting";
on the pommel, blackened steel, always visible). Our own geometry, generated here.

Sting is Pretty Enderal Armory's assassin blade: one shape, blade along +Y, its pommel a flat RING at y -12 .. -9.5
(about 3.8 wide in X, 0.77 thick in Z, open in the middle), then a thicker collar where the grip starts. The spider
straddles the ring's opening on its +Z face: cephalothorax towards the grip, abdomen towards the butt, eight jointed
legs that arch a little, come down onto the ring's outer rim and curl round it to grip the back face.

`make(rim, face)` builds it against the measured plate: rim(y) = the plate's half width at y, face = half its
thickness. Returns (vertices, normals, triangles) in the dagger's own coordinates.
"""
import numpy as np

# body (dagger units; the plate is ~3.8 x 2.5)
CEPH = dict(c=(0.0, -9.95, 0.33), r=(0.42, 0.48, 0.30))      # centre z is above the face
ABDO = dict(c=(0.0, -11.02, 0.46), r=(0.58, 0.80, 0.42))
FANGS = [dict(c=(sx, -9.42, 0.20), r=(0.09, 0.15, 0.09)) for sx in (-0.13, 0.13)]
EYES = [dict(c=(sx, -9.62, 0.53), r=(0.055, 0.055, 0.045)) for sx in (-0.17, -0.06, 0.06, 0.17)]
# legs, front to back: where each leaves the cephalothorax (y offset), where it reaches the rim (y), knee shift in y
HIP_DY = (0.30, 0.10, -0.10, -0.28)
RIM_Y = (-9.62, -10.10, -10.75, -11.40)
KNEE_DY = (0.30, 0.08, -0.08, -0.30)
KNEE_X = (0.78, 0.92, 0.92, 0.78)
KNEE_Z = 0.62                  # above the face: the legs hug the ring
LEG_R = (0.095, 0.040)         # tube radius at the hip -> at the tip
KNEE_BULGE = 0.035             # joints a little thicker
RING = 7                       # tube sides
STEPS = 44                     # samples along each leg


def ellipsoid(c, r, nu=16, nv=10):
    c, r = np.asarray(c, float), np.asarray(r, float)
    V, N, T = [], [], []
    for j in range(nv + 1):
        th = np.pi * j / nv
        for i in range(nu):
            ph = 2 * np.pi * i / nu
            d = np.array([np.sin(th) * np.cos(ph), np.sin(th) * np.sin(ph), np.cos(th)])
            V.append(c + r * d)
            n = d / r
            N.append(n / np.linalg.norm(n))
    for j in range(nv):
        for i in range(nu):
            a, b = j * nu + i, j * nu + (i + 1) % nu
            c2, d2 = a + nu, b + nu
            T += [(a, c2, b), (b, c2, d2)]
    return np.array(V), np.array(N), np.array(T)


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


def tube(C, radius):
    """A tube along curve C (n x 3) with per-sample radius; a pointed tip at the end."""
    n = len(C)
    tang = np.gradient(C, axis=0)
    tang /= np.linalg.norm(tang, axis=1, keepdims=True)
    ref = np.array([0.0, 0.0, 1.0]) if abs(tang[0, 2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    nrm = np.cross(tang[0], ref)
    nrm /= np.linalg.norm(nrm)
    V, N, T = [], [], []
    for k in range(n):                      # parallel transport
        if k:
            nrm = nrm - tang[k] * (nrm @ tang[k])
            nrm /= np.linalg.norm(nrm)
        b = np.cross(tang[k], nrm)
        for i in range(RING):
            a = 2 * np.pi * i / RING
            d = np.cos(a) * nrm + np.sin(a) * b
            V.append(C[k] + radius[k] * d)
            N.append(d)
    for k in range(n - 1):
        for i in range(RING):
            a, b2 = k * RING + i, k * RING + (i + 1) % RING
            T += [(a, b2, a + RING), (b2, b2 + RING, a + RING)]
    tip = len(V)
    V.append(C[-1] + tang[-1] * radius[-1] * 1.5)
    N.append(tang[-1])
    last = (n - 1) * RING
    T += [(last + i, last + (i + 1) % RING, tip) for i in range(RING)]
    return np.array(V), np.array(N), np.array(T)


def leg(side, i, rim, face):
    """Control points: hip (inside the cephalothorax) -> knee (raised) -> down onto the rim's top edge -> round the
    rim's side -> under its bottom edge -> gripping the back face."""
    cy = CEPH['c'][1]
    hip = (side * 0.30, cy + HIP_DY[i], face + 0.30)
    y = RIM_Y[i]
    w = rim(y)
    knee = (side * KNEE_X[i], (cy + HIP_DY[i] + y) / 2 + KNEE_DY[i], face + KNEE_Z)
    top = (side * (w - 0.10), y, face + 0.20)
    edge = (side * (w + 0.13), y, 0.0)
    under = (side * (w - 0.02), y, -(face + 0.14))
    grip = (side * (w - 0.42), y + (0.06 if i < 2 else -0.06), -(face + 0.09))
    return [hip, knee, top, edge, under, grip]


def make(rim, face):
    """-> vertices, normals, triangles, [(leg centre line, radii)]."""
    parts, legs = [], []
    for e in [CEPH, ABDO] + FANGS + EYES:
        c = np.array(e['c'], float)
        c[2] += face
        parts.append(ellipsoid(c, e['r'], 18 if e in (CEPH, ABDO) else 8, 12 if e in (CEPH, ABDO) else 6))
    s = np.linspace(0, 1, STEPS)
    for side in (1, -1):
        for i in range(4):
            C = catmull_rom(leg(side, i, rim, face), STEPS)
            r = LEG_R[0] + (LEG_R[1] - LEG_R[0]) * s
            r += KNEE_BULGE * np.exp(-((s - 0.2) / 0.05) ** 2) + KNEE_BULGE * np.exp(-((s - 0.48) / 0.05) ** 2)
            parts.append(tube(C, r))
            legs.append((C, r))
    V, N, T, base = [], [], [], 0
    for v, n, t in parts:
        V.append(v)
        N.append(n)
        T.append(t + base)
        base += len(v)
    return np.vstack(V), np.vstack(N), np.vstack(T), legs


def surface_points(P, T, ymax=-9.2, per_edge=6):
    """Dense points on the dagger's triangles below ymax (the pommel and collar)."""
    T = T[(P[T][:, :, 1] < ymax).all(1)]
    out = []
    for i in range(per_edge + 1):
        for j in range(per_edge + 1 - i):
            a, b = i / per_edge, j / per_edge
            out.append(P[T[:, 0]] * (1 - a - b) + P[T[:, 1]] * a + P[T[:, 2]] * b)
    return np.vstack(out)


def clearance(legs, S):
    """Smallest (distance from a leg's centre line to the dagger surface) / (the leg's radius there): above 1 = the
    tube never sinks into the pommel (the body sits over the ring's opening, the legs alone touch metal)."""
    worst = np.inf
    for C, r in legs:
        d = np.sqrt(((C[:, None, :] - S[None, :, :]) ** 2).sum(-1)).min(1)
        worst = min(worst, float((d / r).min()))
    return worst
