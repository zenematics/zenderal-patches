"""Whisper's spine (curator 2026-11-15, round 3): "use actual skeleton parts from the game ... just do the spine no
skull and hood". The game's own human spine (vanilla `meshes\\clutter\\bones\\humanspine.nif`, read from the
player's `Skyrim - Meshes0.bsa` at build time, never committed) laid along the neck path of billyro's Stalwart Axe
in place of the neck the curator outlined.

The game's spine (its own coordinates, after its shape's scale 1.058): 64.7 units along y, the sacrum and its
curled tail at +y, the neck vertebrae at -y, the spinous processes on its -z side, its natural S-curve in the y-z
plane; 483 vertices, 934 triangles, vertex colours (baked shading), the skeleton textures.

Laid on the axe: the sacrum sits on the top handle band like a bony collar, the vertebrae climb the handle line and
curve over the blade's concave back edge (the old neck's course) to its upper back corner, the neck vertebrae
smallest at the top. The S-curve is straightened first (its centre line, measured per height, is subtracted), then
every vertex goes to the path: its height picks the arc length, its lateral and front-to-back offsets go along the
path's frame, the spinous processes toward the poll (the curve's outer side), the vertebral bodies toward the blade
so the blade's back edge sits inside them. Normals, tangents and bitangents are turned by the same local rotation,
so the game's normal map keeps lining up; the uniform scale needs nothing else. The x axis is mirrored (the spine is
symmetric) so the mapping keeps the triangles' winding.
"""
import os, struct, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'src', 'StingAndRise', 'tools'))
sys.path.insert(0, os.path.join(REPO, 'src', 'Prophecy', 'tools'))
from angel import catmull_rom  # noqa: E402
import nifse  # noqa: E402
import _bsa  # noqa: E402

SPINE_BSA = 'Skyrim - Meshes0.bsa'
SPINE_KEY = chr(92).join(('meshes', 'clutter', 'bones', 'humanspine.nif'))
SPINE_VERTS, SPINE_TRIS = 483, 934                 # asserted: an archive that changed it stops the build

# ---- the neck path (axe coordinates, z = 0): measured on tools/01's base -------------------------------------
HANDLE_X = 1.25          # the handle's axis (the top band's centre)
BAND_TOP = 10.0          # the top handle band's top face
# up the handle axis, the old neck's outward bulge, over the blade's apex (x -0.48, y 28) and along the blade's
# upper back edge (measured: (-2.17, 29.5), (-3.52, 31), (-4.54, 33), (-5.16, 34)), offset outward
PATH = ((HANDLE_X, BAND_TOP), (HANDLE_X, 14.0), (HANDLE_X, 18.5), (1.40, 22.0), (1.05, 25.2), (0.10, 28.2),
        (-1.55, 30.0), (-2.95, 31.55), (-4.05, 33.15), (-4.65, 33.95))
CROSS = 0.65             # cross-section scale on top of the length fit: about the band's width (the length fit
                         # without the sacrum is 0.756, so at the game's own proportions it was ~1.6x the band)
BASE_SINK = 2.3          # the base goes this far down past the band's top, so its open cut ring sits wholly inside
                         # band and grip (at 1.4 the ring, slanted by the S-curve, reached 0.76 above the band top)
                         # The game spine is also open at its neck end; that ring lands inside the blade's thickness
                         # at its upper back corner (z +-0.72 against the blade's +-0.84), hidden.
SACRUM_CUT = 4.0         # the game spine's own height (after its shape scale) above which triangles go: the sacrum
                         # and tail bone (curator: "the spine needs to connect to the handle more smoothly"; on the
                         # band the sacrum sat like a lump wider than it). 18 triangles cross here, no vertex within
                         # 0.3: the fewest of any height, so the cut edge is one clean ring of the tube
BASE_TAPER = 3.5         # the cross-section narrows over this many units above the band's top, down to what fits
BAND_FIT = (0.90, 1.10)  # at the base: lateral half-width, front-to-back half-depth. (1.0, 1.45) fitted billyro's
                         # band; since the ouroboros (tools/02) the base is cut flat inside the ring's body (sink
                         # SPINE_SINK in tools/02), and this keeps that section within the ring's outer edge. A fit to
                         # the thinned grip itself (0.50, 0.70) squeezed the base into crumpled folds
VENTRAL = 0.0            # shifts the spine toward the blade (+) or the poll (-), in axe units
CENTRE_BINS = 40         # the S-curve's centre line: front-to-back midpoints over this many height bins


def spine_path(n=600):
    """Points along the centre line, resampled to equal arc length; and the total length."""
    P = catmull_rom(np.array([(x, y, 0.0) for x, y in PATH]), n)
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    t = np.linspace(0, s[-1], n)
    return np.stack([np.interp(t, s, P[:, i]) for i in range(3)], -1), s[-1]


def frames(Q, L, s):
    """Vectorised: centre, tangent (toward the tip), dorsal (in-plane, the outer side) at arc lengths s."""
    u = np.clip(s / L, 0, 1) * (len(Q) - 1)
    k = np.minimum(u.astype(int), len(Q) - 2)
    f = (u - k)[:, None]
    c = Q[k] * (1 - f) + Q[k + 1] * f
    idx = np.arange(len(Q))
    tq = Q[np.minimum(idx + 3, len(Q) - 1)] - Q[np.maximum(idx - 3, 0)]
    tq /= np.linalg.norm(tq, axis=1, keepdims=True)
    below = s < 0                                         # past the band: straight on down the handle axis
    c[below] = Q[0] + tq[0] * s[below, None]
    t = tq[k] * (1 - f) + tq[k + 1] * f
    t /= np.linalg.norm(t, axis=1, keepdims=True)
    d = np.stack([t[:, 1], -t[:, 0], np.zeros(len(t))], -1)
    return c, t, d


def load_spine(data_dir):
    """The game's spine shape: (Nif, shape index, read_trishape dict, its transform)."""
    d, listing = _bsa.listing(os.path.join(data_dir, SPINE_BSA))
    raw = _bsa.read(d, listing[SPINE_KEY])
    nif = nifse.Nif(raw)
    assert nif.tobytes() == raw
    k = nif.find('BSTriShape')
    assert len(k) == 1, len(k)
    s = nifse.read_trishape(nif.blocks[k[0]])
    assert len(s['pos']) == SPINE_VERTS and len(s['tris']) == SPINE_TRIS, (len(s['pos']), len(s['tris']))
    return nif, k[0], s, nifse.transform(nif.blocks[k[0]])


def centre_line(P):
    """z of the S-curve's centre line as a function of y (front-to-back midpoints per height bin, smoothed), and
    its slope."""
    y0, y1 = P[:, 1].min(), P[:, 1].max()
    edges = np.linspace(y0, y1, CENTRE_BINS + 1)
    mids, zc = [], []
    for a, b in zip(edges[:-1], edges[1:]):
        m = (P[:, 1] >= a) & (P[:, 1] <= b)
        if m.sum() >= 3:
            mids.append((a + b) / 2)
            zc.append((P[m, 2].min() + P[m, 2].max()) / 2)
    mids, zc = np.array(mids), np.array(zc)
    zc = np.convolve(np.pad(zc, 2, mode='edge'), np.ones(5) / 5, mode='valid')     # smoothed
    f = lambda y: np.interp(y, mids, zc)  # noqa: E731
    g = lambda y: np.interp(y, mids, np.gradient(zc, mids))  # noqa: E731
    return f, g


TESSELLATE = 4           # each game triangle split n x n (curator: "make the spine more high poly")
PHONG_ALPHA = 0.65       # Phong tessellation's shape factor: new points curve between the original normals


def tessellate(P, N, Tg, Bt, UV, C, T, n=TESSELLATE, alpha=PHONG_ALPHA):
    """Phong tessellation (Boubekeur & Alexa 2008): every triangle split into n x n, each new point the linear point
    pulled toward the original vertices' tangent planes, so the silhouette rounds out between the game's vertices
    without moving them (Loop subdivision would shrink the processes). The projection uses normals averaged per
    position, so edges shared across UV seams get identical points (no cracks); shading normals, tangent frames,
    UVs and vertex colours are interpolated. Vertices are welded by (position, UV)."""
    key = {}
    pid = np.array([key.setdefault(tuple(p), len(key)) for p in np.round(P, 5)])
    Nw = np.zeros((len(key), 3))
    np.add.at(Nw, pid, N)
    Nw /= np.linalg.norm(Nw, axis=1, keepdims=True)
    Np = Nw[pid]
    bary = [(a / n, b / n) for a in range(n + 1) for b in range(n + 1 - a)]       # (u, v): weights of j and k
    index = {ab: i for i, ab in enumerate((a, b) for a in range(n + 1) for b in range(n + 1 - a))}
    local = []
    for a in range(n):
        for b in range(n - a):
            local.append((index[(a, b)], index[(a + 1, b)], index[(a, b + 1)]))
            if a + b < n - 1:
                local.append((index[(a + 1, b)], index[(a + 1, b + 1)], index[(a, b + 1)]))
    U = np.array([u for u, _ in bary])
    W2 = np.array([v for _, v in bary])
    W0 = 1 - U - W2
    out = {'P': [], 'N': [], 'Tg': [], 'Bt': [], 'UV': [], 'C': []}
    tris, weld = [], {}
    for t in T:
        i, j, k = t
        lin = W0[:, None] * P[i] + U[:, None] * P[j] + W2[:, None] * P[k]
        proj = lambda q, pv, nv: q - ((q - pv) @ nv)[:, None] * nv  # noqa: E731
        ph = W0[:, None] * proj(lin, P[i], Np[i]) + U[:, None] * proj(lin, P[j], Np[j]) + W2[:, None] * proj(lin, P[k], Np[k])
        pos = (1 - alpha) * lin + alpha * ph
        lerp = lambda A: W0[:, None] * A[i] + U[:, None] * A[j] + W2[:, None] * A[k]  # noqa: E731
        nrm, tg, bt, uv = lerp(N), lerp(Tg), lerp(Bt), lerp(UV)
        col = lerp(C.astype(float))
        ids = []
        for q in range(len(bary)):
            kk = (tuple(np.round(pos[q], 5)), tuple(np.round(uv[q], 5)))
            if kk not in weld:
                weld[kk] = len(out['P'])
                out['P'].append(pos[q]); out['N'].append(nrm[q]); out['Tg'].append(tg[q]); out['Bt'].append(bt[q])
                out['UV'].append(uv[q]); out['C'].append(col[q])
            ids.append(weld[kk])
        tris += [(ids[x], ids[y], ids[z]) for x, y, z in local]
    nz = lambda A: A / np.linalg.norm(A, axis=1, keepdims=True)  # noqa: E731
    return (np.array(out['P']), nz(np.array(out['N'])), nz(np.array(out['Tg'])), nz(np.array(out['Bt'])),
            np.array(out['UV']), np.clip(np.round(np.array(out['C'])), 0, 255).astype(np.uint8), np.array(tris))


def lay(s, xf, Q, L, cut=SACRUM_CUT, sink=None, cross=None, taper=True, tess=TESSELLATE):
    """The game's spine laid along the path: positions, normals, tangents, bitangents (axe coordinates), UVs, vertex
    colours, triangles (after the cut and the tessellation), the length scale, and the base fit factor.
    `cut`: drop every triangle reaching above this height (the game spine's own y, after its shape scale), so the
    sacrum goes and the open cut sinks into the band (None keeps it); `sink`: how far the base goes past the band's
    top; `cross`: the cross-section's scale on top of the length fit (non-uniform: normals and tangent frames
    transform to match); `taper`: narrow the base into the band (BASE_TAPER, BAND_FIT)."""
    sink = BASE_SINK if sink is None else sink
    cross = CROSS if cross is None else cross
    t0, R0, sc0 = xf
    P = s['pos'] * sc0 @ R0.T + t0
    rot = lambda v: v @ R0.T  # noqa: E731
    N, Tg, Bt = rot(s['normal']), rot(s['tangent']), rot(s['bitangent'])
    T = s['tris']
    if cut is not None:
        T = T[P[T][:, :, 1].max(1) <= cut]
    keep = np.unique(T)
    remap = np.full(len(P), -1)
    remap[keep] = np.arange(len(keep))
    T = remap[T]
    zc, slope = centre_line(P)                          # measured on the whole spine (the S-curve)
    P, N, Tg, Bt, UV, C = P[keep], N[keep], Tg[keep], Bt[keep], s['uv'][keep], s['color'][keep]
    if tess and tess > 1:
        P, N, Tg, Bt, UV, C, T = tessellate(P, N, Tg, Bt, UV, C, T, n=tess)
    y0, y1 = P[:, 1].min(), P[:, 1].max()
    k = (L + sink) / (y1 - y0)                          # the length fit
    arc = (y1 - P[:, 1]) * k - sink                     # the base (+y) on the band, the neck at the tip
    c, t, d = frames(Q, L, arc)
    l = np.array([0.0, 0.0, 1.0])
    # the original's local frame at each height: X0 (lateral), T0 (up its centre line), D0 (its back, -z side)
    g = slope(P[:, 1])
    T0 = np.stack([np.zeros_like(g), np.ones_like(g), g], -1)
    T0 /= np.linalg.norm(T0, axis=1, keepdims=True)
    D0 = np.stack([np.zeros_like(g), g, -np.ones_like(g)], -1)
    D0 /= np.linalg.norm(D0, axis=1, keepdims=True)
    lat0 = -P[:, 0] * k * cross                         # mirrored: (-X0, T0, D0) maps onto (l, -t, d), same handedness
    dor0 = -(P[:, 2] - zc(P[:, 1])) * k * cross
    # the base taper: inside the band (arc <= 0) the cross-section shrinks to fit BAND_FIT, widening back to full
    # over BASE_TAPER units above the band's top (smoothstep), so the spine grows out of the handle
    f0 = 1.0
    if taper:
        inside = arc <= 0.3
        f0 = min(1.0, BAND_FIT[0] / np.abs(lat0[inside]).max(), BAND_FIT[1] / np.abs(dor0[inside]).max())
        u = np.clip(arc / BASE_TAPER, 0, 1)
        fac = f0 + (1 - f0) * u * u * (3 - 2 * u)
    else:
        fac = np.ones(len(P))
    lateral, dorsal = lat0 * fac, dor0 * fac - VENTRAL
    V = c + lateral[:, None] * l + dorsal[:, None] * d

    def turn(v, normal):
        a = -v[:, 0]
        b = np.einsum('ij,ij->i', v, T0)
        e = np.einsum('ij,ij->i', v, D0)
        sc = cross * fac
        f = 1.0 / sc if normal else sc                  # normals: inverse transpose; surface directions: as points
        out = (a * f)[:, None] * l - b[:, None] * t + (e * f)[:, None] * d
        return out / np.linalg.norm(out, axis=1, keepdims=True)
    N, Tg, Bt = turn(N, True), turn(Tg, False), turn(Bt, False)
    return V, N, Tg, Bt, UV, C, T, k, f0
