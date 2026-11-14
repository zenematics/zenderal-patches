"""Argent Verdict's gauntlet variant (curator 2026-11-14: "save what we have but make a variant that is a spiked
Gauntlet instead of a hand with a poorly blended wrist"). The same clenched grip on the stake as the hand (fist.py's
pose: its finger joints, thumb and palm), armoured: our own geometry, every part a fist.Grid.

- each finger and the thumb: three plate lames following the hand's phalanges, a little larger than the fingers they
  cover, squarish in section, the far end of each flared into a lip that overlaps the next, two rivets near the start
  of each (painted); a small spike over each middle knuckle and the thumb's joint;
- a knuckle guard across the four knuckles carrying a spike (gadling) over each;
- a back plate over the back of the hand, a ridge down its middle, a domed rivet near each corner and a spike in
  the middle;
- the palm, the curl inside the fist and the thumb's pad are the glove under the armour: navy leather (as the grip);
- the wrist: telescoping armour lames, each a band with a rolled lower rim, stepping down in size from the wrist onto
  the shaft (their centres moving from behind the stake onto the shaft's axis), the top one ringed with spikes, and
  a collar on the shaft below the last: armour blends the wrist into the handle;
- the stake out to the face's and spike's necks and their sockets, as the hand variant.

`gauntlet(c, neck_x, neck_half, shaft_r)` returns (grids, info) like fist.fist.
"""
import numpy as np

import fist
from fist import unit, se, Grid

PLATE = (1.12, 1.16)       # a lame's half extents, x the finger's (side, depth)
PLATE_E = 3.2              # its section's squareness
FLARE = 0.08               # its far end's lip
SPIKE_PIP = (15.0, 4.2)    # middle-knuckle spikes: length, base radius (mm, x the finger's size)
GADLING = (25.0, 6.6)      # knuckle-guard spikes: length, base radius (mm)
BACK_SPIKE = (22.0, 7.0)   # the back plate's central spike
BACK_RIVETS = ((-0.62, 0.18), (0.62, 0.18), (-0.62, 0.82), (0.62, 0.82))   # (x / half width, along the plate 0..1)
GUARD = (5.5, 9.0, 0.55)   # knuckle guard: half thickness out, half width along the finger (mm), lift (x depth)
BACK_PLATE = (2.4, 2.2, 0.9)   # back plate thickness, ridge height (mm), width (x the palm's)
LAMES = dict(count=4, height=0.85, step=0.7, top=1.0, rim=((0.0, 0.94), (0.06, 1.0), (0.75, 1.03), (0.88, 1.08),
                                                           (0.96, 1.07), (1.0, 1.0)),
             first=(1.12, 1.15), last=1.18, spikes=6, spike=(0.8, 0.16))    # mesh units; first = x the wrist's
COLLAR = ((0.05, 1.17), (0.4, 1.21), (0.7, 0.95))   # below the last lame: (depth, x the shaft's radius)


def lame(A, B, side_ref, dors_ref, half_a, half_b, rivets=True, rings_n=16, m=20, cap=0.55, tip=False):
    """A plate lame from A to B: a superellipse section a little squarer than a finger's, its far end flared into a
    lip, the near end rounded short, the far end rounded short (or longer at a fingertip)."""
    A, B = np.asarray(A, float), np.asarray(B, float)
    L = np.linalg.norm(B - A)
    t = (B - A) / L
    dors = unit(dors_ref - t * (dors_ref @ t))
    side = np.cross(t, dors)
    if side @ side_ref < 0:
        side = -side
    ea = cap * half_a[1]
    eb = (0.95 if tip else cap) * half_b[1]
    S = np.array([-ea * np.cos(np.pi / 2 * k / 5) for k in range(1, 5)] + list(np.linspace(0, L, rings_n))
                 + [L + eb * np.sin(np.pi / 2 * k / 5) for k in range(1, 5)])
    cs, sn = se(2 * np.pi * np.arange(m) / m, PLATE_E)
    R = []
    for s in S:
        f = min(max(s / L, 0.0), 1.0)
        hs = half_a[0] + (half_b[0] - half_a[0]) * f
        hd = half_a[1] + (half_b[1] - half_a[1]) * f
        lip = 1.0 if tip else 1.0 + FLARE * fist_smooth((f - 0.72) / 0.28)
        if s < 0:
            q = np.sqrt(max(1.0 - (s / ea) ** 2, 0.0))
        elif s > L:
            q = np.sqrt(max(1.0 - ((s - L) / eb) ** 2, 0.0)) * lip
        else:
            q = lip
        R.append(A + t * s + q * (hs * cs[:, None] * side + hd * sn[:, None] * dors))
    return Grid(R, 'plate', cap0=A - t * ea, cap1=B + t * eb,
                meta=dict(rivets=rivets, ends=(S[0], S[-1]), L=L))


def fist_smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def spike(base, direction, length, radius, kind='spike', n=7, m=10):
    """A cone, a little concave, from base (sunk into what carries it) along direction."""
    d = unit(direction)
    f = np.linspace(0, 1, n)
    C = np.asarray(base, float) + np.outer(f, d) * length
    return fist.tube(C, radius * np.maximum((1 - f) ** 1.25, 0.02), kind, m=m)


def swept(C, outs, half_out, half_side, e=3.0, m=20, kind='plate', cap=0.6):
    """A bar along C, its depth toward outs, superellipse section, ends rounded."""
    C = np.asarray(C, float)
    tang = unit(np.gradient(C, axis=0))
    cs, sn = se(2 * np.pi * np.arange(m) / m, e)
    frames = []
    for i in range(len(C)):
        o = unit(outs[i] - tang[i] * (outs[i] @ tang[i]))
        frames.append((o, np.cross(tang[i], o)))
    rings = []
    for j in range(1, 5):
        q = np.cos(np.pi / 2 * j / 5)
        o, sd = frames[0]
        rings.insert(0, C[0] - tang[0] * cap * half_side[0] * q + np.sqrt(1 - q * q) * (
            half_side[0] * cs[:, None] * sd + half_out[0] * sn[:, None] * o))
    for i in range(len(C)):
        o, sd = frames[i]
        rings.append(C[i] + half_side[i] * cs[:, None] * sd + half_out[i] * sn[:, None] * o)
    for j in range(1, 5):
        q = np.sin(np.pi / 2 * j / 5)
        o, sd = frames[-1]
        rings.append(C[-1] + tang[-1] * cap * half_side[-1] * q + np.sqrt(1 - q * q) * (
            half_side[-1] * cs[:, None] * sd + half_out[-1] * sn[:, None] * o))
    return Grid(rings, kind, cap0=C[0] - tang[0] * cap * half_side[0], cap1=C[-1] + tang[-1] * cap * half_side[-1],
                meta=dict(rivets=False))


def armoured_hand(b, half_w):
    """The gauntlet at the hand's build size, local frame (fist.hand's pose)."""
    k = 2 * half_w * 0.97 / fist.HAND_BREADTH_MM
    widths = np.array([f['width'] for f in fist.FINGERS])
    widths = widths / widths.sum() * 2 * half_w * 0.97
    xs = -half_w * 0.97 + np.concatenate([[0.0], np.cumsum(widths)[:-1]]) + widths / 2
    J = fist.finger_joints(b, k, xs)
    X = np.array([1.0, 0.0, 0.0])
    grids = []
    guard_pts, guard_out = [], []
    for j in J:
        hs, hd = j['hs'], j['hd']
        ext = [(hs * t * PLATE[0], hd * t * PLATE[1]) for t in fist.TAPER]
        segs = ((j['M'], j['P'], ext[0], ext[1], False), (j['P'], j['D'], ext[1], ext[2], False),
                (j['D'], j['T'], ext[2], ext[3], True))
        for A, B, ha, hb, tip in segs:
            grids.append(lame(A, B, X, fist.away(A, B, j['x']), ha, hb, tip=tip))
        # a spike over the middle knuckle, out of the corner
        n1, n2 = fist.away(j['M'], j['P'], j['x']), fist.away(j['P'], j['D'], j['x'])
        out = unit(n1 + n2)
        size = hd / (k * 10.0)
        grids.append(spike(j['P'] + out * ext[1][1] * 0.55, out, k * SPIKE_PIP[0] * size, k * SPIKE_PIP[1] * size))
        # the knuckle guard runs over the metacarpal heads
        kd = unit(0.45 * n1 + np.array([0.0, 0.0, -1.0]))
        guard_pts.append(j['M'] + kd * GUARD[2] * hd)
        guard_out.append(kd)
    G = np.array(guard_pts)
    O = np.array(guard_out)
    row = unit(G[-1] - G[0])
    ends = (G[0] - row * widths[0] * 0.45, G[-1] + row * widths[-1] * 0.45)
    P = np.vstack([ends[0], G, ends[1]])
    Ov = np.vstack([O[0], O, O[-1]])
    import angel
    C = angel.catmull_rom(P, 30)
    Oc = unit(np.stack([np.interp(np.linspace(0, 1, 30), np.linspace(0, 1, len(Ov)), Ov[:, i]) for i in range(3)], -1))
    grids.append(swept(C, Oc, np.full(30, k * GUARD[0]), np.full(30, k * GUARD[1])))
    for g_, o in zip(G, O):                                     # a gadling over each knuckle
        grids.append(spike(g_ + o * k * GUARD[0] * 0.2, unit(o + np.array([0.0, 0.15, 0.0])), k * GADLING[0],
                           k * GADLING[1]))
    # the glove under the armour: palm, the curl, the thumb's pad
    S = fist.palm_shape(b, half_w, k, J)
    grids.append(fist.deformed_box(S, 'leather'))
    grids.append(fist.deformed_box(fist.curl_filler(b, half_w, J), 'leather', nu=36, nv=26, density=0.5))
    grids.append(fist.ellipsoid((half_w * 0.6, 0.52 * S['u_bot'], -1.25 * b / 1.55), np.eye(3),
                                (k * 13.0, k * 21.0, k * 9.0), kind='leather'))
    # the back plate over the back of the hand, a ridge down its middle
    Mx = np.array([j['x'] for j in J])
    Mu = np.array([j['M'][1] for j in J])
    hdv = np.array([j['hd'] for j in J])
    t_, rid, wid = BACK_PLATE
    Bp = dict(e=4.0, u_bot=S['u_bot'] + k * 3.0,
              xl=lambda u: S['xl'](u) * wid, xr=lambda u: S['xr'](u) * wid,
              u_top=lambda x: np.interp(x, Mx, Mu - 0.95 * hdv), u_top_mean=float(np.mean(Mu - 0.95 * hdv)),
              w_back=lambda x, u: fist.palm_back(S, x, u) - k * t_ - k * rid * np.exp(-(np.asarray(x) / (k * 7.0)) ** 2),
              w_front=lambda x, u: fist.palm_back(S, x, u) + k * 2.5)
    grids.append(fist.deformed_box(Bp, 'plate', nu=44, nv=26))
    # its rivets near the corners and a spike in the middle, standing out of the plate's back
    u_lo, u_hi = Bp['u_bot'], float(np.mean(Mu - 0.95 * hdv))
    for fx, fu in BACK_RIVETS:
        u = u_lo + (u_hi - u_lo) * fu
        x = fx * S['xr'](u) * wid
        w = float(fist.palm_back(S, x, u)) - k * t_
        grids.append(fist.ellipsoid((x, u, w), np.eye(3), (k * 2.4, k * 2.4, k * 1.4), kind='plate'))
    u = u_lo + (u_hi - u_lo) * 0.5
    w = float(fist.palm_back(S, 0.0, u)) - k * (t_ + rid)
    grids.append(spike((0.0, u, w + k * 2.0), np.array([0.0, 0.35, -1.0]), k * BACK_SPIKE[0], k * BACK_SPIKE[1]))
    # the thumb: three lames over its bones, the pad leather, a spike over its joint
    th = fist.THUMB
    p = {n: np.array([th[n][0] * half_w, k * th[n][1], k * th[n][2]]) for n in ('cmc', 'mcp', 'ip', 'tip')}
    rad = [(k * a * PLATE[0], k * d_ * PLATE[1]) for a, d_ in th['radii']]
    refs = ((-0.85, 0.0, 0.55), (-0.25, 0.15, 1.0), (0.0, 0.3, 1.0))
    names = ('cmc', 'mcp', 'ip', 'tip')
    for i in range(3):
        grids.append(lame(p[names[i]], p[names[i + 1]], np.array([0.0, 1.0, 0.0]), np.array(refs[i]), rad[i],
                          rad[i + 1], tip=(i == 2)))
    d = unit(p['mcp'] - p['cmc'])
    toward = np.array([0.6, 0.0, -0.5])
    inward = unit(toward - d * (toward @ d))
    grids.append(fist.ellipsoid(p['cmc'] + (p['mcp'] - p['cmc']) * 0.46 + inward * k * 8.0,
                                (inward, d, np.cross(d, inward)), (k * 16.0, k * 31.0, k * 15.0), kind='leather'))
    o = unit(np.array(refs[1]) + np.array(refs[2]))
    grids.append(spike(p['ip'] + o * rad[2][1] * 0.8, o, k * SPIKE_PIP[0], k * SPIKE_PIP[1]))
    return grids, k, S


def wrist_lames(k, base_y, base_z, shaft_r):
    """Mesh frame round the shaft: telescoping lames from the wrist onto the shaft, spikes round the first, a collar
    below the last. Returns the parts, the y where the shaft comes out, and the lames' rings (for how high the shaft
    may run up inside them)."""
    L = LAMES
    hx, hz = k * fist.WRIST_MM[0] / 2, k * fist.WRIST_MM[1] / 2
    s = k / (2 * fist.BUILD_HALF_W * 0.97 / fist.HAND_BREADTH_MM)
    m = 48
    a = 2 * np.pi * np.arange(m) / m
    parts, all_rings = [], []
    for i in range(L['count']):
        f = i / (L['count'] - 1)
        g = f * f * (3 - 2 * f)
        rx = hx * L['first'][0] * (1 - g) + shaft_r * L['last'] * g
        rz = hz * L['first'][1] * (1 - g) + shaft_r * L['last'] * g
        e = 2.8 - 0.8 * g
        zc = base_z * (1 - g)
        top = base_y + L['top'] * s - i * L['step']
        cs, sn = se(a, e)
        R = []
        for tt, q in L['rim']:
            R.append(np.stack([q * rx * cs, np.full(m, top - tt * L['height']), zc + q * rz * sn], -1))
        R = np.array(R)
        all_rings += list(R)
        parts.append(Grid(R, 'lame', cap0=R[0].mean(0), cap1=R[-1].mean(0)))
        if i == 0:                                              # spikes round the first lame
            for j in range(L['spikes']):
                ang = 2 * np.pi * (j + 0.5) / L['spikes']
                c_, s_ = se(np.array([ang]), e)
                P = np.array([1.08 * rx * c_[0], top - 0.88 * L['height'], zc + 1.08 * rz * s_[0]])
                out = unit(np.array([P[0], 0.0, P[2] - zc]) + np.array([0.0, -0.25, 0.0]))
                parts.append(spike(P - out * 0.12, out, L['spike'][0], L['spike'][1]))
    bottom = base_y + L['top'] * s - (L['count'] - 1) * L['step'] - L['height']
    R = []
    for dd, q in COLLAR:
        cs, sn = se(a, 2.0)
        R.append(np.stack([shaft_r * q * cs, np.full(m, bottom + 0.15 - dd), shaft_r * q * sn], -1))
    R = np.array(R)
    parts.append(Grid(R, 'lame', cap0=R[0].mean(0), cap1=R[-1].mean(0)))
    join = bottom + 0.15 - COLLAR[-1][0]
    return parts, join, all_rings


def gauntlet(c, neck_x, neck_half, shaft_r):
    c = np.asarray(c, float)
    grids, k, S = armoured_hand(fist.BUILD_STAKE_R, fist.BUILD_HALF_W)
    th = -np.radians(fist.TILT)
    cth, sth = np.cos(th), np.sin(th)
    R = np.array([[1.0, 0.0, 0.0], [0.0, cth, -sth], [0.0, sth, cth]])
    sc = fist.HAND_SCALE
    for g in grids:
        g.paint = g.P / k
        g.paint_cap0 = None if g.cap0 is None else g.cap0 / k
        g.paint_cap1 = None if g.cap1 is None else g.cap1 / k
        g.paint_rot = R.T
        g.meta['mm'] = 1.0 / k
        g.apply(lambda P: c + (sc * np.asarray(P)) @ R.T)
    ks = k * sc
    base = R @ np.array([0.0, S['u_bot'], S['wrist_w']]) * sc
    wrist, join, rings = wrist_lames(ks, base[1], base[2], shaft_r)
    circle = shaft_r * np.stack([np.cos(np.linspace(0, 2 * np.pi, 24, endpoint=False)),
                                 np.sin(np.linspace(0, 2 * np.pi, 24, endpoint=False))], -1)
    held = join
    for ring in sorted(rings, key=lambda r: r[:, 1].mean()):      # bottom up: as high as the lames hold the shaft
        if not fist.inside(circle, ring[:, [0, 2]]).all():
            break
        held = float(ring[:, 1].mean())
    stake_r = fist.BUILD_STAKE_R * sc * fist.STAKE_PRESS
    x0, x1 = neck_x[0] - c[0], neck_x[1] - c[0]
    xs = np.linspace(x0 + fist.SOCKET['reach'] * 0.5, x1 - fist.SOCKET['reach'] * 0.5, 24)
    stake = fist.tube(np.stack([xs, np.zeros_like(xs), np.zeros_like(xs)], -1), np.full(len(xs), stake_r), 'stake',
                      m=28, density=0.6)
    sockets = [fist.socket(x0, 1.0, neck_half, stake_r), fist.socket(x1, -1.0, neck_half, stake_r)]
    for g in wrist + [stake] + sockets:
        g.paint = g.P / ks
        g.paint_cap0 = None if g.cap0 is None else g.cap0 / ks
        g.paint_cap1 = None if g.cap1 is None else g.cap1 / ks
        g.meta['mm'] = 1.0 / ks
        g.apply(lambda P: c + np.asarray(P))
    grids += wrist + [stake] + sockets
    info = dict(shaft_join_y=c[1] + join, shaft_held_y=c[1] + held, stake_r=stake_r, units_per_mm=ks,
                hand_x=(c[0] - fist.BUILD_HALF_W * sc, c[0] + fist.BUILD_HALF_W * sc))
    return grids, info
