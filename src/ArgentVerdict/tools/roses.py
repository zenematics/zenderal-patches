"""Argent Verdict's forearm roses (curator 2026-11-14, of the bare forearm between the hand and the bracelet of
thorns: "can we add some detail to this, maybe leaves and roses"): a thorny rose vine winding up the forearm from the
bracelet toward the wrist, carrying roses, a bud and leaves. Our own geometry, every part a fist.Grid (thin closed
shells and tubes); built lean, since the whole fist is one BSTriShape (at most 65,535 triangles).

- two vines winding round each other up the arm, standing just off its surface, with small thorns, five roses
  between them and a closed bud at the top of each;
- each rose: a tight centre, then rings of cupped petals (3 wrapped round the centre, then 5, 5 and 5, each ring
  more open, the outer ones curling back at the tips), every petal a thin closed shell;
- leaves: pointed ovals folded along the midrib, drooping a little, in pairs along the vine and beside each rose.

`forearm_roses(surface, y_lo, y_hi)` returns the parts in the mesh frame centred on the shaft's axis: surface(y,
theta) gives the forearm's surface point and outward normal at height y and angle theta round its axis, y_lo .. y_hi
the stretch of arm the vine climbs.

`column_roses(surface, y_lo, y_hi)` is the gauntlet variant's (curator 2026-11-14: "add some metal Rose and
thorns"): two thorny vines, mirror images of each other, rise from the back (theta -90 deg) at y_lo, wind round
either side of the wrist lames and meet at the front (theta 90 deg, the fingers' side) at y_hi under one rose with a
leaf pair; leaves and thorns along both.
"""
import numpy as np

import fist

# two vines winding round each other up the arm: start angle (rad), turns, stem radius, its roses (along the vine 0..1,
# size, turn deg), its leaves (along the vine; one leaf each, sides alternating; besides a pair under each rose), a
# closed bud at its top (along the vine, or None), its thorns
VINES = (dict(start=1.35, turns=1.15, radius=0.08,
              roses=((0.1, 0.86, 0.0), (0.42, 0.98, 40.0), (0.74, 0.86, 75.0)),
              leaves=(0.04, 0.22, 0.27, 0.55, 0.6, 0.86, 0.9), bud=0.98, thorns=8),
         dict(start=1.35 + np.pi, turns=0.95, radius=0.06,
              roses=((0.28, 0.74, 20.0), (0.62, 0.8, 60.0)),
              leaves=(0.08, 0.14, 0.44, 0.5, 0.82, 0.88), bud=0.95, thorns=6))
VINE_SAMPLES, VINE_LIFT = 110, 0.9    # points along a vine; how far it stands off the arm (x its radius)
LEAF_SIZE = (0.62, 0.25)
# petal rings: (count, opening from the rose's axis (deg), length, width (x the rose's size), cup, tip curl back
# (rad), start radius from the axis (x size), turn (deg))
LAYERS = ((3, 6.0, 0.50, 0.58, 0.95, 0.0, 0.02, 0.0), (5, 24.0, 0.68, 0.62, 0.65, 0.25, 0.06, 36.0),
          (5, 46.0, 0.82, 0.70, 0.45, 0.65, 0.10, 0.0), (5, 70.0, 0.90, 0.74, 0.30, 0.95, 0.14, 36.0))
PETAL_THICK = 0.035        # x the rose's size
PETAL_RES = (7, 8)         # rings along a petal, points round it
LEAF_RES = (9, 8)


def unit(v):
    return fist.unit(v)


def perp(ax):
    ref = np.array([0.0, 1.0, 0.0]) if abs(ax[1]) < 0.9 else np.array([1.0, 0.0, 0.0])
    return unit(ref - ax * (ref @ ax))


def sheet(C, d, side, w, thick, cup, m):
    """A thin closed shell along the centre line C (directions d) with half widths w across `side`; its section is a
    flat ellipse bent `cup` x w toward the inside (positive) or folded along the middle (negative cup)."""
    a = 2 * np.pi * np.arange(m) / m
    x, y = np.cos(a), np.sin(a)
    R = []
    for k in range(len(C)):
        n = unit(np.cross(d[k], side))
        bend = cup * w[k] * (x * x if cup >= 0 else -np.abs(x))
        R.append(C[k] + side * (x * w[k])[:, None] + n * (bend + y * thick[k])[:, None])
    return R


def curve(O, d0, bend_dir, angle0, bend, length, n=48):
    """A centre line from O, leaving at angle0 from d0 toward bend_dir and bending by `bend` (rad) to its end."""
    ss = np.linspace(0, 1, n)
    phi = angle0 + bend * ss ** 2
    d = np.cos(phi)[:, None] * d0 + np.sin(phi)[:, None] * bend_dir
    C = O + np.concatenate([[np.zeros(3)], np.cumsum((d[1:] + d[:-1]) / 2 / (n - 1), axis=0)]) * length
    return ss, C, d


def resample(ss, A, s):
    return np.stack([np.interp(s, ss, A[:, i]) for i in range(3)], -1)


def petal(O, ax, e1, az, open_deg, length, width, thick, cup, reflex, r0):
    e2 = np.cross(ax, e1)
    er = np.cos(az) * e1 + np.sin(az) * e2
    et = np.cross(ax, er)
    ss, C, d = curve(O + er * r0, ax, er, np.radians(open_deg), reflex, length)
    s = np.linspace(0, 1, PETAL_RES[0] + 2)[1:-1]
    w = width * np.sqrt(s) * np.sqrt(np.clip(1 - s ** 3, 0, 1))
    th = thick * (0.45 + 0.55 * np.sqrt(1 - s))
    R = sheet(resample(ss, C, s), unit(resample(ss, d, s)), et, w, th, cup, PETAL_RES[1])
    return fist.Grid(R, 'petal', cap0=C[0], cap1=C[-1])


def bloom(O, ax, R, turn=0.0, layers=LAYERS):
    ax = unit(ax)
    e1 = perp(ax)
    c, s_ = np.cos(np.radians(turn)), np.sin(np.radians(turn))
    e1 = c * e1 + s_ * np.cross(ax, e1)
    out = [fist.ellipsoid(O + ax * 0.22 * R, np.array([e1, ax, np.cross(ax, e1)]), (0.13 * R, 0.2 * R, 0.13 * R),
                          kind='petal', nu=10, nv=7)]
    for count, op, ln, wd, cup, refl, r0, rot in layers:
        for i in range(count):
            az = np.radians(rot + 360.0 * i / count + 11.0 * len(out))
            out.append(petal(O, ax, e1, az, op, ln * R, wd * R, PETAL_THICK * R, cup, refl, r0 * R))
    return out


def leaf(base, direction, normal, length, width, droop=0.3):
    """A pointed oval leaf from `base` along `direction`, its face toward `normal`, folded along the midrib and
    drooping at the tip."""
    d0 = unit(direction)
    n0 = unit(normal - d0 * (normal @ d0))
    side = np.cross(d0, n0)
    ss, C, d = curve(base, d0, n0, 0.0, -droop, length, 36)
    s = np.linspace(0, 1, LEAF_RES[0] + 2)[1:-1]
    w = width * np.sin(np.pi * s) ** 0.75 * (1 - 0.3 * s)
    R = sheet(resample(ss, C, s), unit(resample(ss, d, s)), side, w, np.full(len(s), 0.012), -0.12, LEAF_RES[1])
    return fist.Grid(R, 'leaf', cap0=C[0], cap1=C[-1])


def thorn(base, direction, length, radius):
    d = unit(direction)
    C = base + np.outer(np.linspace(0, 1, 5), d) * length
    return fist.tube(C, radius * np.linspace(1, 0.05, 5) ** 1.2, 'thorn', m=6)


def forearm_roses(surface, y_lo, y_hi):
    out = []
    for V in VINES:
        out += vine(surface, y_lo, y_hi, V)
    return out


# the gauntlet's two vines: stem radius, angle from the back where they start and from the front where they end (rad),
# leaves and thorns along each (0..1; thorn length, base radius), a smaller rose on each (along, size, turn deg), the
# rose at the front (size, turn deg), how far above y_hi it sits. The first build's (stem 0.07, one rose 0.86) was lost
# under the fist in the preview.
COLUMN = dict(radius=0.1, ends=(0.32, 0.2), leaves=(0.12, 0.3, 0.62, 0.8), thorns=7, thorn=(0.26, 0.06),
              side_roses=((0.46, 0.74, 40.0),), rose=(1.3, 18.0), rose_lift=0.0, leaf=1.0)


def column_roses(surface, y_lo, y_hi):
    C = COLUMN
    up = np.array([0.0, 1.0, 0.0])
    out = []
    for sgn in (1.0, -1.0):
        ts = np.linspace(0, 1, VINE_SAMPLES)
        pts, nrm = [], []
        for f in ts:
            th = -np.pi / 2 + sgn * (C['ends'][0] + (np.pi - C['ends'][0] - C['ends'][1]) * f)
            P, n = surface(y_lo + (y_hi - y_lo) * f, th)
            pts.append(P + n * C['radius'] * VINE_LIFT)
            nrm.append(n)
        Cv, Nv = np.array(pts), np.array(nrm)
        out.append(fist.tube(Cv, C['radius'] * np.interp(ts, [0, 0.06, 0.94, 1], [0.6, 1, 1, 0.75]), 'thorn', m=8))
        tang = unit(np.gradient(Cv, axis=0))

        def at(f):
            k = int(round(f * (len(Cv) - 1)))
            return Cv[k], Nv[k], tang[k]
        for i, f in enumerate(C['leaves']):
            P, n, t = at(f)
            side = unit(np.cross(n, t)) * (1 if i % 2 else -1) * sgn
            out.append(leaf(P + n * C['radius'] * 0.8, unit(0.7 * t + side + 0.3 * n), unit(n + 0.3 * up),
                            LEAF_SIZE[0] * C['leaf'], LEAF_SIZE[1] * C['leaf']))
        for i in range(C['thorns']):
            f = (i + 0.5) / C['thorns']
            P, n, t = at(f)
            side = unit(np.cross(n, t)) * (1 if i % 2 else -1) * sgn
            out.append(thorn(P + n * C['radius'] * 0.6, unit(n + 0.4 * side - 0.4 * t), *C['thorn']))
        for f, size, turn in C['side_roses']:                       # a smaller rose on each, mirrored
            P, n, t = at(f)
            out += bloom(P + n * C['radius'] * 1.1, unit(n + 0.3 * up), size, sgn * turn)
            for s2 in (-1, 1):
                out.append(leaf(P + n * C['radius'], unit(s2 * t + 0.5 * n - 0.2 * up), unit(n + 0.4 * up),
                                LEAF_SIZE[0] * 0.9, LEAF_SIZE[1] * 0.9))
    P, n = surface(y_hi + C['rose_lift'], np.pi / 2)                  # the rose where they meet
    size, turn = C['rose']
    out += bloom(P + n * C['radius'] * 1.1, unit(n + 0.3 * up), size, turn)
    across = unit(np.cross(up, n))
    for sgn in (-1, 1):                                              # a leaf pair tucked under it
        out.append(leaf(P + n * C['radius'], unit(sgn * across + 0.5 * n - 0.2 * up), unit(n + 0.4 * up),
                        LEAF_SIZE[0] * 0.9, LEAF_SIZE[1] * 0.9))
    return out


def vine(surface, y_lo, y_hi, V):
    up = np.array([0.0, 1.0, 0.0])
    ts = np.linspace(0, 1, VINE_SAMPLES)
    pts, nrm = [], []
    for f in ts:
        P, n = surface(y_lo + (y_hi - y_lo) * f, V['start'] + 2 * np.pi * V['turns'] * f)
        pts.append(P + n * V['radius'] * VINE_LIFT)
        nrm.append(n)
    C, Nv = np.array(pts), np.array(nrm)
    out = [fist.tube(C, np.full(len(C), V['radius']) * np.interp(ts, [0, 0.9, 1], [1, 1, 0.6]), 'thorn', m=8)]
    tang = unit(np.gradient(C, axis=0))

    def at(f):
        k = int(round(f * (len(C) - 1)))
        return C[k], Nv[k], tang[k]
    for f, size, turn in V['roses']:
        P, n, t = at(f)
        out += bloom(P + n * V['radius'] * 1.1, unit(n + 0.3 * up), size, turn)
        for sgn in (-1, 1):                                          # a leaf pair tucked under the rose
            out.append(leaf(P + n * V['radius'], unit(sgn * t + 0.5 * n - 0.2 * up), unit(n + 0.4 * up),
                            LEAF_SIZE[0] * 0.9, LEAF_SIZE[1] * 0.9))
    for i, f in enumerate(V['leaves']):
        P, n, t = at(f)
        sgn = 1 if i % 2 else -1
        side = unit(np.cross(n, t)) * sgn
        out.append(leaf(P + n * V['radius'] * 0.8, unit(0.7 * t + side + 0.3 * n), unit(n + 0.3 * up), *LEAF_SIZE))
    for i in range(V['thorns']):
        f = (i + 0.5) / V['thorns']
        P, n, t = at(f)
        side = unit(np.cross(n, t)) * (1 if i % 2 else -1)
        out.append(thorn(P + n * V['radius'] * 0.6, unit(n + 0.4 * side - 0.4 * t), 0.17, 0.045))
    if V['bud'] is not None:                                         # a closed bud, its sepals round it
        P, n, t = at(V['bud'])
        bud_ax = unit(0.6 * t + n + 0.3 * up)
        out += bloom(P + n * V['radius'], bud_ax, 0.45, layers=((3, 4.0, 0.62, 0.62, 1.0, 0.0, 0.02, 0.0),
                                                                  (3, 10.0, 0.7, 0.64, 0.9, 0.05, 0.04, 60.0)))
        e1 = perp(bud_ax)
        for i in range(4):
            a = 2 * np.pi * i / 4
            dirn = np.cos(a) * e1 + np.sin(a) * np.cross(bud_ax, e1)
            out.append(leaf(P + n * V['radius'] + dirn * 0.04, unit(bud_ax * 0.55 + dirn), unit(-dirn + 0.3 * bud_ax),
                            0.26, 0.05, droop=-0.6))
    return out
