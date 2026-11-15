"""Whisper's mount (curator 2026-11-15): "instead go for a simple spike top and extend the back of the blade to mount
like the Noble axe does", "use the noble axe upper shaft for Whisper", with a drawing: a straight shaft from the
connector up to a spike, a socket where the blade meets it, and the blade's back drawn out to the socket along two
lines (meeting the blade's back edges at about y 25 and y 32).

The Noble axe is Caenraes' Noble Armory war axe as Pretty Enderal Armory ships it (`meshes\\weapons\\elven\\
elvenwaraxe.nif`, shape `Noble_Axe_MP`; Caenraes' model is open with credit: credit Caenraes, as for Argent Verdict).
Read from the installed list at build time; its textures are referenced by their own paths (Pretty Enderal Armory is
in the list), never copied. Its pieces (islands, after the shape's own scale 1.25): the twisted steel shaft (y 16 -
39.7), a collar under the socket (39.4 - 43.9), the socket block fused to the Noble blade (the blade cut away here
at x NOBLE_SOCKET_X), a ring on the socket's top (47.0 - 47.8) and the spike (47.6 - 55.2); its grip, ferrule,
pommel and blade are not used.

Placed on Whisper's handle axis (x 1.25, z 0) at SCALE, the socket's centre at SOCKET_Y; the shaft cut where it
starts, inside the connector ouroboros. The blade's back reaches the socket through a generated plate (`neck_plate`):
the drawing's two lines from the socket to the blade's back edges and those edges themselves, as thick as the blade's
flat (it overlaps the blade a little and runs into the socket, so no seam shows).
"""
import os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'src', 'StingAndRise', 'tools'))
import nifse  # noqa: E402

NOBLE_MESH = 'meshes/weapons/elven/elvenwaraxe.nif'
NOBLE_SHAPE = 'Noble_Axe_MP'
NOBLE_SOURCE = 'Pretty Enderal Armory'
NOBLE_TRIS = 5050                      # asserted: a different mesh stops the build
NOBLE_AXIS = (0.495, 0.095)            # its shaft's axis (x, z): the shaft island's centre
NOBLE_SOCKET_Y = 44.65                 # the socket block's middle (y 42.1 - 47.2)
NOBLE_SOCKET_X = -1.3                  # the socket block ends here on the blade side (its blade starts past it)
# the pieces, told apart by their extents (Noble coordinates): (name, y range of the island, x range)
PIECES = {'shaft': ((16.0, 39.8), (-0.7, 1.7)),
          'collar': ((39.3, 43.9), (-1.1, 2.1)),
          'socket+blade': ((35.1, 51.8), (-14.4, 2.9)),
          'ring': ((46.9, 47.9), (-1.1, 2.1)),
          'spike': ((47.5, 55.2), (-0.9, 1.9))}
AXIS_X = 1.25                          # Whisper's handle axis
SCALE = 0.9                            # the socket 4.6 tall, the spike's tip near y 37.7 (the drawing's ~37.4)
SOCKET_Y = 28.6                        # the socket's middle on Whisper: between the drawing's lines at the blade
LEAN_BANDS = ((9.8, 11.0), (11.0, 14.0), (14.0, 20.0), (20.0, 24.0), (31.0, 32.5), (34.0, 38.5))   # Whisper y: the
                                       # mount's round parts (shaft, collar, ring, spike), centred on its axis
SHAFT_FROM_Y = 9.8                    # the shaft starts here (open: fluted, ridges r 0.974), in the middle of the
                                       # connector ouroboros (snake.RING_Y), which rests on its ridges
# the plate from the socket to the blade's back (Whisper coordinates, z = 0 plane): its edge along the socket's
# blade side, the drawing's two lines, and billyro's blade's back edges between them (measured: apex x -0.48, y 28;
# upper edge (-2.17, 29.5), (-3.52, 31.0), (-4.54, 33.0); lower (-1.06, 27.0), (-2.17, 26.0), (-3.52, 24.0))
SOCKET_FACE_X = -0.37                  # the socket block's blade side on Whisper (the Noble's x -1.3)
# curator: "bring the blade closer into the shaft and make the connection look more seemless": billyro's blade (its
# island, rivets, blood edges and the relief snakes on it) moves this far toward the shaft; its back's apex then
# sits inside the socket block and the plate only fills the wedges above and below it
BLADE_SHIFT = (2.8, 1.1)               # (x, y): curator, on the plate's wedge above the socket: "if you move the blade up
                                       # slightly you can lose this additional piece". billyro's back is a V (its point at
                                       # y 27.5, edges symmetric); centred on the socket's height (y 28.6) and 2.8 in, both
                                       # back edges stay ~0.4 the socket's blade side over its whole height (tools/02 asserts)
                                       # and leave it at its top and bottom corners: no plate. (2.0, 0) left a gap above y
                                       # 29.8, (2.0, 1.3) one below y 27
PLATE_SOCKET_Y = (26.5, 30.7)          # along the socket's height (4.6 tall, y 26.3 - 30.9)
PLATE_IN_SOCKET = 0.3                  # the plate's socket side this far into the block past the blade's apex
PLATE_BLADE = ((-4.10, 32.20), (-3.52, 31.00), (-2.17, 29.50), (-0.48, 28.00), (-1.06, 27.00), (-2.17, 26.00),
               (-2.85, 25.10))         # top line's end, the blade's back edges, bottom line's end (before the shift)
PLATE_INTO_BLADE = 0.18                # the blade-side outline pushed this far into the blade (no gap)
PLATE_HALF = 0.80                      # half thickness (the blade's flat is +-0.84)


def islands(P, T):
    key = {}
    rep = np.array([key.setdefault(tuple(p), i) for i, p in enumerate(np.round(P, 4))])
    par = np.arange(len(P))

    def f(a):
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a
    for t in T:
        a = f(rep[t[0]])
        for x in t[1:]:
            par[f(rep[x])] = a
    return np.array([f(rep[i]) for i in range(len(P))])[T[:, 0]]


def load(sr):
    """The Noble axe as the list has it: (nif, its shape's block index, read_trishape dict, positions after the
    shape's transform)."""
    mods = os.path.join(sr.MO2, 'mods')
    src, nif = sr.load(mods, sr.profile_mods(), NOBLE_MESH)
    assert src == NOBLE_SOURCE, (NOBLE_MESH, src)
    k = [k for k in nif.find('BSTriShape') if sr.name_of(nif, k) == NOBLE_SHAPE]
    assert len(k) == 1, k
    s = nifse.read_trishape(nif.blocks[k[0]])
    assert len(s['tris']) == NOBLE_TRIS, len(s['tris'])
    t, R, sc = nifse.transform(nif.blocks[k[0]])
    return nif, k[0], s, s['pos'] * sc @ R.T + t, R


def clip(P, A, T, dist):
    """Triangles clipped to dist <= 0 (dist per vertex, linear), attributes interpolated (no cap)."""
    P, A, dist = list(P), [list(a) for a in A], list(dist)
    cache, out = {}, []

    def cut(i, j):
        key = (min(i, j), max(i, j))
        if key not in cache:
            f = dist[i] / (dist[i] - dist[j])
            P.append(P[i] + (P[j] - P[i]) * f)
            for a in A:
                a.append(a[i] + (a[j] - a[i]) * f)
            dist.append(0.0)
            cache[key] = len(P) - 1
        return cache[key]
    for tri in T:
        inside = [dist[v] <= 0 for v in tri]
        if all(inside):
            out.append(tuple(tri))
            continue
        if not any(inside):
            continue
        n = sum(inside)
        r = inside.index(True) if n == 1 else inside.index(False)
        a, b, c = tri[r], tri[(r + 1) % 3], tri[(r + 2) % 3]
        ab, ac = cut(a, b), cut(a, c)
        if n == 1:
            out.append((a, ab, ac))
        else:
            out.append((ab, b, c))
            out.append((ab, c, ac))
    return np.array(P), [np.array(a) for a in A], np.array(out)


def compact(P, A, T):
    used = np.unique(T)
    remap = np.full(len(P), -1)
    remap[used] = np.arange(len(used))
    return P[used], [a[used] for a in A], remap[T]


def upper_shaft(sr):
    """The Noble axe's upper shaft on Whisper: positions, normals, tangents, bitangents, UVs, colours, triangles (the
    Noble shape's own vertex data, moved and scaled), and the Noble nif and its shader block (to copy the shader)."""
    nif, k, s, P, R = load(sr)
    T = s['tris']
    isl = islands(P, T)
    ext = {r: (P[np.unique(T[isl == r])].min(0), P[np.unique(T[isl == r])].max(0)) for r in np.unique(isl)}

    def find(name):
        (y0, y1), (x0, x1) = PIECES[name]
        hits = [r for r, (lo, hi) in ext.items() if abs(lo[1] - y0) < 0.3 and abs(hi[1] - y1) < 0.3
                and abs(lo[0] - x0) < 0.3 and abs(hi[0] - x1) < 0.3]
        assert len(hits) == 1, (name, {r: (lo.round(2), hi.round(2)) for r, (lo, hi) in ext.items()})
        return hits[0]
    pieces = {name: find(name) for name in PIECES}
    keep = np.isin(isl, [pieces[n] for n in ('shaft', 'collar', 'socket+blade', 'ring', 'spike')])
    A = [s['normal'] @ R.T, s['tangent'] @ R.T, s['bitangent'] @ R.T, s['uv'].astype(float),
         (s['color'] if 'color' in s else np.full((len(P), 4), 255, np.uint8)).astype(float)]
    Tk = T[keep]
    tri_isl = isl[keep]
    # the Noble blade goes: the socket+blade island cut at NOBLE_SOCKET_X (the rest untouched)
    sock = Tk[tri_isl == pieces['socket+blade']]
    rest = Tk[tri_isl != pieces['socket+blade']]
    P2, A2, sock = clip(P, A, sock, NOBLE_SOCKET_X - P[:, 0])
    # the shaft starts inside the connector ouroboros
    noble_from = NOBLE_SOCKET_Y + (SHAFT_FROM_Y - SOCKET_Y) / SCALE
    P3, A3, rest = clip(P2, A2, rest, noble_from - P2[:, 1])
    T3 = np.vstack([sock, rest])
    P3, A3, T3 = compact(P3, A3, T3)
    V = np.column_stack([AXIS_X + (P3[:, 0] - NOBLE_AXIS[0]) * SCALE,
                         SOCKET_Y + (P3[:, 1] - NOBLE_SOCKET_Y) * SCALE,
                         (P3[:, 2] - NOBLE_AXIS[1]) * SCALE])
    N, Tg, Bt, UV, C = A3
    # the lean (curator, on the langets: "It doesnt look aligned"): the Noble's own shaft is not parallel to its y,
    # it leans front to back (z), so placed by one axis point the mount's centre drifted from z -0.05 at the shaft's
    # foot through +0.21 at the socket to +0.28 at the spike (~0.75 deg), and the socket stood 0.6 off the blade on
    # its +z face and 0.15 on its -z face. Its round parts' centres (LEAN_BANDS: shaft, collar, ring, spike; the
    # socket block is left out) are fitted with a line and the mount turned upright about x, its axis onto the grip's
    # (z 0) at the shaft's foot. Side to side (x) it is true already (asserted).
    ys, zs, xs = [], [], []
    for lo, hi in LEAN_BANDS:
        q = V[(V[:, 1] >= lo) & (V[:, 1] < hi)]
        assert len(q) > 10, ('a lean band is empty', lo, hi)
        ys.append((q[:, 1].min() + q[:, 1].max()) / 2)
        zs.append((q[:, 2].min() + q[:, 2].max()) / 2)
        xs.append((q[:, 0].min() + q[:, 0].max()) / 2)
    b, a = np.polyfit(ys, zs, 1)
    assert abs(np.polyfit(ys, xs, 1)[0]) < 0.003, 'the Noble shaft leans side to side too'
    phi = -np.arctan(b)
    y0, z0 = SHAFT_FROM_Y, a + b * SHAFT_FROM_Y
    cph, sph = np.cos(phi), np.sin(phi)

    def turn(v, about):
        v = v.copy()
        dy, dz = v[:, 1] - about[0], v[:, 2] - about[1]
        v[:, 1] = about[0] + dy * cph - dz * sph
        v[:, 2] = dy * sph + dz * cph
        return v
    V = turn(V, (y0, z0))
    N, Tg, Bt = (turn(x, (0.0, 0.0)) for x in (N, Tg, Bt))
    upper_shaft.lean = (float(np.degrees(np.arctan(b))), float(z0))
    nz = lambda v: v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-12)  # noqa: E731
    C = np.clip(np.round(C), 0, 255).astype(np.uint8)
    return V, nz(N), nz(Tg), nz(Bt), UV, C, T3, nif, s['shader'], {n: int((tri_isl == pieces[n]).sum())
                                                                    for n in pieces}


def ear_clip(poly):
    """Triangles (index triples) of a simple polygon given counter-clockwise."""
    idx = list(range(len(poly)))
    out = []

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    def inside(p, a, b, c):
        return cross(a, b, p) >= 0 and cross(b, c, p) >= 0 and cross(c, a, p) >= 0
    guard = 0
    while len(idx) > 3 and guard < 1000:
        guard += 1
        for i in range(len(idx)):
            a, b, c = idx[i - 1], idx[i], idx[(i + 1) % len(idx)]
            if cross(poly[a], poly[b], poly[c]) <= 1e-9:
                continue
            if any(inside(poly[j], poly[a], poly[b], poly[c]) for j in idx if j not in (a, b, c)):
                continue
            out.append((a, b, c))
            idx.pop(i)
            break
    assert len(idx) == 3, 'ear clipping failed'
    out.append(tuple(idx))
    return out


def neck_plate():
    """The plate from the socket to the blade's back: an outline (the socket side, the drawing's two lines, the
    blade's back edges pushed PLATE_INTO_BLADE into the blade), extruded +-PLATE_HALF in z, flat faces. Returns
    positions, normals, UVs (planar), triangles; counter-clockwise outward."""
    blade = np.array(PLATE_BLADE, float) + np.array(BLADE_SHIFT)
    socket_x = max(SOCKET_FACE_X + PLATE_IN_SOCKET, blade[:, 0].max() + PLATE_IN_SOCKET)
    # push the blade-side outline into the blade (toward -x, along each edge's own outward normal)
    pushed = blade.copy()
    for i in range(len(blade)):
        a, b = blade[max(i - 1, 0)], blade[min(i + 1, len(blade) - 1)]
        d = b - a
        nrm = np.array([d[1], -d[0]])
        nrm /= np.linalg.norm(nrm)
        if nrm[0] > 0:                                         # pointing out of the blade: flip
            nrm = -nrm
        pushed[i] = blade[i] + nrm * PLATE_INTO_BLADE
    outline = [(socket_x, PLATE_SOCKET_Y[1])] + [tuple(p) for p in pushed] + [(socket_x, PLATE_SOCKET_Y[0])]
    poly = np.array(outline)
    area = 0.5 * np.sum(poly[:, 0] * np.roll(poly[:, 1], -1) - np.roll(poly[:, 0], -1) * poly[:, 1])
    if area < 0:
        poly = poly[::-1]
    tris = ear_clip([tuple(p) for p in poly])
    n = len(poly)
    V, N, UV, T = [], [], [], []

    def add(pts, nrm, faces):
        base = len(V)
        for p in pts:
            V.append(p)
            N.append(nrm)
            UV.append((p[0] * 0.05 + 0.5, p[1] * 0.05 % 1.0) if abs(nrm[2]) > 0.5 else (p[2] * 0.05 + 0.5, p[1] * 0.05 % 1.0))
        T.extend([(base + a, base + b, base + c) for a, b, c in faces])
    front = [(x, y, PLATE_HALF) for x, y in poly]
    back = [(x, y, -PLATE_HALF) for x, y in poly]
    add(front, (0.0, 0.0, 1.0), tris)
    add(back, (0.0, 0.0, -1.0), [(a, c, b) for a, b, c in tris])
    for i in range(n):                                         # the side walls
        p, q = poly[i], poly[(i + 1) % n]
        d = q - p
        nrm = np.array([d[1], -d[0], 0.0])
        nrm /= np.linalg.norm(nrm)
        quad = [(p[0], p[1], -PLATE_HALF), (q[0], q[1], -PLATE_HALF), (q[0], q[1], PLATE_HALF), (p[0], p[1], PLATE_HALF)]
        add(quad, tuple(nrm), [(0, 1, 2), (0, 2, 3)])
    return np.array(V, float), np.array(N, float), np.array(UV, float), np.array(T, np.int64)
