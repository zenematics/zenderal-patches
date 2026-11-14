"""Argent Verdict's fist: its UV atlas and its painted texture set (curator 2026-11-13: "can you add more complex
detailing to the hand itself? engravings or skin texture, still metallic silver"; 2026-11-14: the hand human again,
its forearm molding into the handle, no base; bones instead of the engraving on the back of the hand).

Every Grid from fist.py gets its own rectangle in one SIZE x SIZE atlas: columns run round its rings (plus a seam
column), rows along it by surface length, so texels keep roughly one size everywhere (shelf packing, one density
for all, as high as fits). Each texel is then traced back to its point on the part (bilinear over the rings, in the
part's paint coordinates: millimetres of the full-size hand) and given a height in mm:

- skin (fingers, thumb, palm, knuckles, thenar, hypothenar, the curl): solid 3D noise, so the micro-relief runs on
  across every seam: soft undulation and pores;
- knuckle wrinkles: a few wavy creases across the back of each middle and end joint (and the thumb's), fading round
  the sides, shallower away from the joint;
- nails: polished, fine lengthwise ridges, no pores;
- the forearm (the palm's surface running on into the shaft): skin at the wrist, fading to plain polished silver
  as it becomes the shaft;
- the bones breaking through the back of the hand (metacarpals, knuckle heads, carpals): a fine, slightly uneven
  grain with sparse small pits, a touch brighter than the skin;
- engravings (silver work, cut lines filled dark like niello): grooves and a bead row round the neck sockets; the
  stake polished;
- the gauntlet variant's plate (lames, knuckle guard, back plate, wrist lames): polished, a shade darker at each
  edge, two raised rivets near the start of each finger lame; its spikes polished, brighter toward the point; its
  glove (palm, thumb pad) navy leather, matt and not metal;
- the bracelet of thorns and the rose vine: polished, a shade darker, faint lengthwise lines;
- rose petals: smooth and polished, shaded darker toward the heart of each rose; leaves: a midrib and paired side
  veins, pressed in.

From the heights: a tangent-space normal map (DirectX: green = +v, measured on vanilla normal maps), its alpha the
highlight mask; a diffuse on the hammer's silver ramp, darker in pores and wrinkles and nearly black in the cut lines;
a Complex Material mask (reflective, glossy silver; the cut lines matte).
"""
import math

import numpy as np

SIZE = 2048
PAD = 4
NIELLO = np.array([0.11, 0.11, 0.12])        # the dark fill in the cut lines
COMPLEX = (0.94, 0.93, 1.0)                  # reflect, gloss, metal on polished silver (Sting and Rise's)
ENGRAVE_DEPTH = 0.12                         # mm: the cut lines
WRINKLE_DEPTH = 0.05
SKIN = (0.07, 0.015, 0.025)                  # undulation, fine grain, pore depth (mm)
BONE = (0.035, 0.012, 0.04)                  # bone: undulation, fine grain, pit depth (mm)
VEIN_DEPTH = 0.05                            # leaf veins (mm)
RIVET = (1.3, 0.25, 0.11, 0.16)              # gauntlet rivets: radius, height (mm), off the back (x round), along (x length)
LEATHER = ((0.05, 0.075, 0.18), 0.03)        # the gauntlet's glove: navy (the grip's), grain depth (mm)


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def value_noise(P, freq, seed, size=96):
    G = np.random.RandomState(seed).rand(size, size, size)
    q = np.asarray(P, float) * freq + 7.3
    i = np.floor(q).astype(int)
    f = q - i
    f = f * f * (3 - 2 * f)
    out = np.zeros(len(q))
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (f[:, 0] if dx else 1 - f[:, 0]) * (f[:, 1] if dy else 1 - f[:, 1]) * (f[:, 2] if dz else 1 - f[:, 2])
                out += w * G[(i[:, 0] + dx) % size, (i[:, 1] + dy) % size, (i[:, 2] + dz) % size]
    return out


# ---- the atlas

def chart_metrics(P):
    """Surface length down the rings (mean over columns) and each ring's circumference."""
    rowlen = np.linalg.norm(np.diff(P, axis=0), axis=2).mean(1)
    s = np.concatenate([[0.0], np.cumsum(rowlen)])
    Pw = np.concatenate([P, P[:, :1]], 1)
    circ = np.linalg.norm(np.diff(Pw, axis=1), axis=2).sum(1)
    return s, circ


def pack(sizes):
    order = sorted(range(len(sizes)), key=lambda i: -sizes[i][1])
    x = y = shelf = 0
    pos = [None] * len(sizes)
    for i in order:
        w, h = sizes[i]
        if w > SIZE:
            return None
        if x + w > SIZE:
            y, x, shelf = y + shelf, 0, 0
        if y + h > SIZE:
            return None
        pos[i] = (x, y)
        x += w
        shelf = max(shelf, h)
    return pos


def layout(grids):
    metrics = [chart_metrics(g.P) for g in grids]

    def sizes(d):
        return [(int(math.ceil(c.max() * d * g.density)) + 2 * PAD, int(math.ceil(s[-1] * d * g.density)) + 2 * PAD)
                for g, (s, c) in zip(grids, metrics)]
    lo, hi = 1.0, 2000.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if pack(sizes(mid)):
            lo = mid
        else:
            hi = mid
    sz = sizes(lo)
    return lo, sz, pack(sz), metrics


def assemble(grids):
    """One mesh from the grids: vertices, normals, UVs (0..1), triangles; plus each chart's placement."""
    density, sizes, pos, metrics = layout(grids)
    Vs, UVs, Ts, charts, off, toff = [], [], [], [], 0, 0
    for g, (w, h), (x0, y0), (s, circ) in zip(grids, sizes, pos, metrics):
        n, m = g.P.shape[:2]
        cw, ch = w - 2 * PAD, h - 2 * PAD
        U = x0 + PAD + np.arange(m + 1) / m * cw
        Vr = y0 + PAD + s / s[-1] * ch
        P = np.concatenate([g.P, g.P[:, :1]], 1).reshape(-1, 3)
        uv = np.stack(np.broadcast_arrays(U[None, :], Vr[:, None]), -1).reshape(-1, 2)
        idx = np.arange(n * (m + 1)).reshape(n, m + 1)
        a, b, c, d = idx[:-1, :-1], idx[:-1, 1:], idx[1:, :-1], idx[1:, 1:]
        T = [np.stack([a, b, c], -1).reshape(-1, 3), np.stack([b, d, c], -1).reshape(-1, 3)]
        extra = []
        if g.cap0 is not None:
            ci = len(P) + len(extra)
            extra.append((g.cap0, (x0 + PAD + cw / 2, Vr[0])))
            T.append(np.stack([np.full(m, ci), idx[0, 1:], idx[0, :-1]], -1))
        if g.cap1 is not None:
            ci = len(P) + len(extra)
            extra.append((g.cap1, (x0 + PAD + cw / 2, Vr[-1])))
            T.append(np.stack([np.full(m, ci), idx[-1, :-1], idx[-1, 1:]], -1))
        if extra:
            P = np.vstack([P] + [e[0][None] for e in extra])
            uv = np.vstack([uv] + [np.array(e[1])[None] for e in extra])
        T = np.vstack(T)
        o = P.mean(0)
        A, B, C = P[T[:, 0]] - o, P[T[:, 1]] - o, P[T[:, 2]] - o
        if np.einsum('ij,ij->i', A, np.cross(B, C)).sum() < 0:      # inside out: flip
            T = T[:, ::-1].copy()
        Vs.append(P)
        UVs.append(uv / SIZE)
        Ts.append(T + off)
        charts.append(dict(grid=g, x0=x0, y0=y0, w=w, h=h, s=s, circ=circ, n=n, m=m, first=off, nv=len(P),
                           tri=(toff, toff + len(T))))
        off += len(P)
        toff += len(T)
    V, UV, T = np.vstack(Vs), np.vstack(UVs), np.vstack(Ts)
    # smooth normals per part, the seam column sharing its partner's
    fa, fb, fc = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    fn = np.cross(fb - fa, fc - fa)
    N = np.zeros_like(V)
    for i in range(3):
        np.add.at(N, T[:, i], fn)
    for ch in charts:
        n, m, f = ch['n'], ch['m'], ch['first']
        idx = f + np.arange(n * (m + 1)).reshape(n, m + 1)
        both = N[idx[:, 0]] + N[idx[:, m]]
        N[idx[:, 0]] = both
        N[idx[:, m]] = both
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    for ch in charts:
        n, m, f = ch['n'], ch['m'], ch['first']
        ch['N'] = N[f:f + n * (m + 1)].reshape(n, m + 1, 3)
    return dict(V=V, N=N, UV=UV, T=T, charts=charts, density=density)


def split(asm):
    """The assembled mesh as one piece per part group (a Grid's meta 'group', default 'fist'): each its own vertices
    (renumbered), normals, UVs and triangles. One BSTriShape holds at most 65,535 of either, so the rose vine is a
    shape of its own."""
    groups = {}
    for ch in asm['charts']:
        groups.setdefault(ch['grid'].meta.get('group', 'fist'), []).append(ch)
    out = {}
    for name, chs in groups.items():
        vidx = np.concatenate([np.arange(ch['first'], ch['first'] + ch['nv']) for ch in chs])
        remap = np.full(len(asm['V']), -1)
        remap[vidx] = np.arange(len(vidx))
        T = np.concatenate([asm['T'][ch['tri'][0]:ch['tri'][1]] for ch in chs])
        T = remap[T]
        assert (T >= 0).all()
        out[name] = (asm['V'][vidx], asm['N'][vidx], asm['UV'][vidx], T)
    return out


# ---- painting

def paint(asm, silver_ramp, preview=False):
    """The texture set for the assembled fist: diffuse RGB, normal RGBA (alpha = highlight), Complex Material
    RGBA. Returns float arrays (and, with preview, the diffuse shaded by its relief under a fixed light: a check of
    the normal map's directions, never shipped)."""
    D = np.zeros((SIZE, SIZE, 3), np.float32)
    D[:] = silver_ramp_at(silver_ramp, 0.62)
    NM = np.zeros((SIZE, SIZE, 4), np.float32)
    NM[:] = (0.5, 0.5, 1.0, 0.85)
    CM = np.zeros((SIZE, SIZE, 4), np.float32)
    CM[:] = COMPLEX + (0.0,)
    PV = D.copy() if preview else None
    light = np.array([-0.35, 0.55, -0.76]) / np.linalg.norm([-0.35, 0.55, -0.76])
    for ch in asm['charts']:
        g = ch['grid']
        n, m, w, h = ch['n'], ch['m'], ch['w'], ch['h']
        cw, ch_ = w - 2 * PAD, h - 2 * PAD
        py, px = np.mgrid[0:h, 0:w].astype(np.float64) + 0.5
        jf = np.clip((px - PAD) / cw * m, 0, m)
        sf = np.clip((py - PAD) / ch_ * ch['s'][-1], 0, ch['s'][-1])
        if_ = np.interp(sf, ch['s'], np.arange(n))
        Q = np.concatenate([g.paint, g.paint[:, :1]], 1)              # (n, m + 1, 3) paint coordinates
        Nn = ch['N'] @ g.paint_rot.T                                   # normals in the paint frame
        i0 = np.clip(np.floor(if_).astype(int), 0, n - 2)
        j0 = np.clip(np.floor(jf).astype(int), 0, m - 1)
        ti, tj = (if_ - i0)[..., None], (jf - j0)[..., None]

        def bil(A):
            return ((1 - ti) * ((1 - tj) * A[i0, j0] + tj * A[i0, j0 + 1]) + ti * ((1 - tj) * A[i0 + 1, j0]
                                                                                    + tj * A[i0 + 1, j0 + 1]))
        X = bil(Q)
        Nx = bil(Nn)
        Nx /= np.maximum(np.linalg.norm(Nx, axis=-1, keepdims=True), 1e-9)
        flat = X.reshape(-1, 3)
        hgt = np.zeros(h * w)
        groove = np.zeros(h * w)
        wr = np.zeros(h * w)
        pore = np.zeros(h * w)
        kind = g.kind
        skin = kind in ('phal', 'skin', 'palm')
        skinw = np.full(h * w, 1.0 if skin else 0.0)
        if 'skin_fade' in g.meta:                                      # the forearm: skin fading to metal down it
            skinw = smoothstep(g.meta['skin_fade'][0], g.meta['skin_fade'][1], flat[:, 1])
        if skin:
            sk = (value_noise(flat, 1 / 2.4, 11) * 0.65 + value_noise(flat, 1 / 1.05, 12) * 0.35 - 0.5) * SKIN[0]
            sk += (value_noise(flat, 1 / 0.45, 13) - 0.5) * SKIN[1]
            pores = smoothstep(0.68, 0.8, value_noise(flat, 1 / 0.55, 37))
            hgt += (sk - SKIN[2] * pores) * skinw
            pore = pores * skinw
        if kind == 'socket':
            xs = np.array(g.meta['x']) * g.meta['mm']
            xm = np.interp(if_.ravel(), np.arange(n), xs)
            lo, hi = xs[1], xs[2]
            span = hi - lo
            for fr in (0.18, 0.82):
                groove += np.exp(-((xm - (lo + span * fr)) / (0.03 * abs(span) + 0.25)) ** 2)
            a = (jf / m).ravel()
            beads = 36
            dx = (np.mod(a * beads, 1.0) - 0.5) / beads * ch['circ'][1] * g.meta['mm']
            dy = xm - (lo + span * 0.5)
            groove += np.exp(-(dx * dx + dy * dy) / (0.42 ** 2))
        if kind == 'phal':
            md = g.meta
            A, t, dors, side = md['A'], md['t'], md['dors'], md['side']
            rel = flat - A
            sax = rel @ t
            rv = rel - np.outer(sax, t)
            ang = np.arctan2(rv @ side, rv @ dors)
            dorsal = smoothstep(0.25, 0.75, np.cos(ang))
            sc = md['hd'] / 10.0
            for e in md.get('wrinkle_ends', ()):
                loc = (sax - (0.0 if e == 0 else md['L'])) / sc
                for kk, off in enumerate((-2.4, -1.2, 0.0, 1.2, 2.4)):
                    wob = 0.35 * np.sin(2.3 * ang + 1.7 * kk + e) + 0.18 * np.sin(5.2 * ang + 0.9 * kk)
                    amp = math.exp(-(off / 2.8) ** 2)
                    wr += np.exp(-((loc - off - wob) / 0.3) ** 2) * amp * dorsal
            wr = np.clip(wr, 0, 1)
            hgt -= WRINKLE_DEPTH * wr
        if kind == 'bone':                                             # the bones through the back of the hand
            und = (value_noise(flat, 1 / 3.5, 21) * 0.65 + value_noise(flat, 1 / 1.4, 22) * 0.35 - 0.5) * BONE[0]
            grain = (value_noise(flat, 1 / 0.5, 23) - 0.5) * BONE[1]
            pit = smoothstep(0.82, 0.9, value_noise(flat, 1 / 1.7, 47))
            hgt += und + grain - BONE[2] * pit
            pore = 0.6 * pit
        if kind == 'nail':
            hgt += 0.006 * np.sin(2 * np.pi * (flat @ g.meta['side']) / 0.5)
        if kind == 'thorn':                                            # vines, thorns: polished, faint bark lines
            hgt += 0.008 * np.sin(2 * np.pi * (jf / m).ravel() * 6)
        sfrac = (if_ / max(n - 1, 1)).ravel()                          # 0 at a part's start .. 1 at its end
        across = np.cos(2 * np.pi * jf / m).ravel()                    # -1..1 across a petal or leaf
        tone = np.zeros(h * w)
        if kind == 'petal':                                            # smooth, darker toward the rose's heart
            tone += -0.2 + 0.24 * sfrac ** 0.7
            hgt += 0.004 * np.sin(2 * np.pi * across * 3.0)
        if kind == 'leaf':                                             # a midrib and paired side veins
            mid = np.exp(-(across / 0.16) ** 2)
            v = sfrac * 5.0 - 2.2 * np.abs(across)
            side_v = np.exp(-((np.mod(v, 1.0) - 0.5) / 0.13) ** 2) * smoothstep(0.12, 0.3, np.abs(across)) \
                * (1 - smoothstep(0.75, 0.95, np.abs(across))) * (sfrac > 0.08) * (sfrac < 0.9)
            vein = np.clip(mid + 0.7 * side_v, 0, 1)
            hgt -= VEIN_DEPTH * vein
            tone += -0.08 - 0.12 * vein
            wr = 0.6 * vein
        if kind in ('plate', 'lame'):                                  # the gauntlet's armour: polished plate
            edge = np.exp(-(sfrac / 0.05) ** 2) + np.exp(-((1 - sfrac) / 0.05) ** 2)
            tone += -0.12 * np.clip(edge, 0, 1)                        # a shade darker at its edges
            if g.meta.get('rivets'):                                   # two rivets near its start, either side
                mm_ = g.meta['mm']
                row_ = np.clip(np.round(if_).astype(int), 0, n - 1).ravel()
                for jr in (0.25 - RIVET[2], 0.25 + RIVET[2]):
                    da = ((jf / m).ravel() - jr) * ch['circ'][row_] * mm_
                    db = (sfrac - RIVET[3]) * ch['s'][-1] * mm_
                    r2 = (da * da + db * db) / RIVET[0] ** 2
                    dome = np.sqrt(np.clip(1 - r2, 0, 1))
                    hgt += RIVET[1] * dome
                    tone += 0.06 * dome
        if kind == 'spike':                                            # polished, brighter toward the point
            tone += 0.06 * sfrac
        if kind == 'leather':                                          # the glove: navy leather grain
            grain = value_noise(flat, 1 / 0.7, 51) * 0.7 + value_noise(flat, 1 / 0.25, 52) * 0.3
            hgt += (grain - 0.5) * LEATHER[1]
            tone = grain
        groove = np.clip(groove, 0, 1)
        hgt -= ENGRAVE_DEPTH * groove
        hgt = hgt.reshape(h, w)
        # slopes per mm: across = round the ring (this row's circumference), down = along the part
        mm = g.meta['mm']
        row = np.clip(np.round(if_).astype(int), 0, n - 1)
        circ_mm = np.maximum(ch['circ'][row] * mm, 1e-3)
        mm_x = circ_mm / cw
        mm_y = ch['s'][-1] * mm / ch_
        gy, gx = np.gradient(hgt)
        nx, ny = -gx / mm_x, -gy / mm_y
        nz = np.ones_like(nx)
        ln = np.sqrt(nx * nx + ny * ny + nz * nz)
        nrm = np.stack([nx / ln, ny / ln, nz / ln], -1) * 0.5 + 0.5
        grv, wrk, por = groove.reshape(h, w), wr.reshape(h, w), pore.reshape(h, w)
        skw = skinw.reshape(h, w)
        skin_tone = (hgt + ENGRAVE_DEPTH * grv + WRINKLE_DEPTH * wrk) * 2.2 * skw
        bone_tone = (hgt + ENGRAVE_DEPTH * grv) * 2.5 + 0.04 if kind == 'bone' else 0.0
        bright = 0.6 + skin_tone + bone_tone + tone.reshape(h, w) - 0.06 * por - 0.12 * wrk \
            - (0.07 if kind == 'thorn' else 0.0)
        col = silver_ramp_at(silver_ramp, np.clip(bright, 0, 1))
        col = col * (1 - 0.92 * grv[..., None]) + NIELLO * 0.92 * grv[..., None]
        spec = 0.86 - 0.06 * skw - 0.6 * grv - 0.2 * wrk - 0.12 * por
        cmr = COMPLEX[0] * (1 - 0.75 * grv)
        cmg = COMPLEX[1] - 0.45 * grv - 0.12 * wrk - 0.08 * por - 0.05 * skw
        metal = np.full_like(cmr, COMPLEX[2])
        if kind == 'leather':                                          # not metal: the grip's navy, matt
            gr = tone.reshape(h, w)
            col = np.array(LEATHER[0])[None, None, :] * (0.7 + 0.6 * gr)[..., None]
            spec = np.full_like(cmr, 0.3)
            cmr = np.full_like(cmr, 0.03)
            cmg = np.full_like(cmr, 0.32)
            metal = np.zeros_like(cmr)
        sl = (slice(ch['y0'], ch['y0'] + h), slice(ch['x0'], ch['x0'] + w))
        D[sl] = col
        NM[sl] = np.concatenate([nrm, np.clip(spec, 0, 1)[..., None]], -1)
        CM[sl] = np.stack([cmr, np.clip(cmg, 0, 1), metal, np.zeros_like(cmr)], -1)
        if preview:
            tu = np.gradient(X, axis=1)
            tv = np.gradient(X, axis=0)
            tu = tu - Nx * (tu * Nx).sum(-1, keepdims=True)
            tv = tv - Nx * (tv * Nx).sum(-1, keepdims=True)
            tu /= np.maximum(np.linalg.norm(tu, axis=-1, keepdims=True), 1e-9)
            tv /= np.maximum(np.linalg.norm(tv, axis=-1, keepdims=True), 1e-9)
            nm = nrm * 2 - 1
            nw = nm[..., :1] * tu + nm[..., 1:2] * tv + nm[..., 2:3] * Nx
            nw /= np.linalg.norm(nw, axis=-1, keepdims=True)
            lit = np.clip(nw @ light, 0.08, 1) / np.clip(Nx @ light, 0.08, 1)
            PV[sl] = np.clip(col * np.clip(lit, 0.35, 1.8)[..., None], 0, 1)
    return (D, NM, CM, PV) if preview else (D, NM, CM)


def silver_ramp_at(stops, t):
    t = np.asarray(t, float)
    xs = [p for p, _ in stops]
    cols = np.array([c for _, c in stops])
    return np.stack([np.interp(t, xs, cols[:, i]) for i in range(3)], -1)
