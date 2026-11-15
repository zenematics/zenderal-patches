"""Whisper's snake grip (curator 2026-11-15): "rework the handle itself, make it thinner with a metal snake coiling
round it the pommel is formed from the snakes head, the Ruby is inside the snakes open mouth", with a drawing: four
diagonal coil strokes from under the top band down the grip, the head looped in at the bottom, the ruby below it.
The curator asked for Triumvirate's snake ("isn't their a snake from triumvirate ?").

The snake is Mihail's rattlesnake as Triumvirate - Mage Archetypes ships it (`meshes\\mihail monsters and
animals\\ice wraith\\snakes\\mihailrattlesnake.nif` in its archive; Mihail's assets are free to use with credit:
"You are allowed to use the assets in this file without permission as long as you credit me", Nexus 36548 /
56523). It is read from the installed archive at build time, never committed.

The snake's own coordinates (bind pose, straight): snout tip at +y 33.93, tail tip at -y -171.5, back +z, belly -z
(its belly line sits at z ~122.2 the whole way), head 14 units long (y 20 .. 33.93), 8.4 wide at the jaw hinge. The
mouth is a shallow closed cavity under the lip line z ~124.24 (palate above, floor below) with no jaw bone.

Laid on the axe (y up the handle, its axis x 1.25, z 0):
  - the head points straight down the axis below the grip's end, its top toward -z (the face the drawing shows),
    the jaw open (the lower jaw turned down about the gape, the head tilted up by half as much, so the mouth's
    bisector stays on the axis): the pommel;
  - the neck arches back over the head's top and climbs into the coil;
  - the body coils WRAPS times up the thinned grip, its belly on the grip (the centre line follows the grip's
    ellipse out by each ring's own belly depth), its back outward, descending toward -x on the -z face as drawn;
  - the tail tip ends just under the top band.
The head keeps its own proportions (cross-section and length scale SIGMA_HEAD); along the neck the scale eases to
SIGMA_BODY, and the body's length is stretched to fill the path (the snake is 205 units long; the path is not).
Normals, tangents and bitangents go through the mapping's own Jacobian (finite differences), so the normal map keeps
lining up through the bends and the non-uniform scale.
"""
import json, os, sys, tempfile
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'src', 'StingAndRise', 'tools'))
sys.path.insert(0, os.path.join(REPO, 'src', 'Prophecy', 'tools'))
sys.path.insert(0, HERE)
import _bsa  # noqa: E402
import gamespine  # noqa: E402

SNAKE_MOD = 'Triumvirate - Mage Archetypes'
SNAKE_BSA = SNAKE_MOD + '.bsa'
SNAKE_TEX_BSA = SNAKE_MOD + ' - Textures.bsa'
_DIR = ('mihail monsters and animals', 'ice wraith', 'snakes')
SNAKE_KEY = chr(92).join(('meshes',) + _DIR + ('mihailrattlesnake.nif',))
SNAKE_D = chr(92).join(('textures',) + _DIR + ('rattlesnake.dds',))
SNAKE_N = chr(92).join(('textures',) + _DIR + ('rattlesnake_n.dds',))
SNAKE_VERTS, SNAKE_TRIS = 1133, 2002             # asserted: an archive that changed it stops the build

# ---- the snake's own coordinates -------------------------------------------------------------------------------
SNOUT_Y, TAIL_Y = 33.93, -171.5
HEAD_Y = 20.0            # the head's back: the head keeps SIGMA_HEAD from here to the snout
NECK_Y = 0.0             # the neck's end: SIGMA_BODY (and the body's stretch) from here to the tail
CX = 0.78                # the snake's lateral centre (its head is symmetric about it)
CZ = 124.3               # the head's dorsal centre: the path runs through it (the belly line is z ~122.2)
TEAR_Y = 26.3            # in front of this the mouth parts the head into its two jaws (cavity back wall y 26.1)
HINGE = (25.8, 124.4)    # (y, z): just behind the mouth's corners (y 27.0, z 124.55)
JAW_OPEN = 36.0          # degrees between the jaws: the lower jaw turns down by this, the head up by half
                         # (the jaws close on the ruby 0.6 - 0.9 inside the snout and flare round it at the tips)
THROAT = 21.0            # behind the hinge the lower jaw's turn fades out to here (the throat stretches)
TILT_NECK = (14.0, 21.0) # the head's tilt fades in along the neck between these heights
TESSELLATE = 3           # each game triangle split n x n (Phong tessellation, as the spine)

# ---- the axe ---------------------------------------------------------------------------------------------------
AXIS_X = 1.25            # the handle's axis (x; z 0)
GRIP_A, GRIP_B = 0.85, 0.62   # the thinned grip's half-axes (x, z); billyro's was ~1.4 x 1.05 with a finger swell
SIGMA_HEAD = 0.34        # the head's scale: 2.9 wide at the hinge, 4.7 long (the drawing's loop); its back is
                         # wider than the grip, so it caps the grip's end
SIGMA_BODY = 0.15        # the body's cross-section scale: 1.2 wide, 0.9 deep at its thickest
OCCIPUT_Y = -6.5         # where the head's back sits on the axis, just under the grip's end (the snout lands
                         # near y -11.1); lower, a bare stretch of neck showed between grip and head
# the neck (curator, in game, on the neck leaving the head: "just need to fix the neck of the snake leading to the
# head", lines drawn from the head's back down the grip into the first turn; on the renders: "I want the neck to
# connect to the top of the head on the pommel not from underneath"). It was a cubic from the occiput up the axis,
# half inside the grip, out round its -x side into the coil: it left the head from underneath and the leather showed
# between them. Now the head's top runs on into the neck: from the jaw hinge the centre line lifts onto the grip's -z
# face (the side the head's top faces) over NECK_LIFT, runs up it and eases into the coil's helix over NECK_BEND. The
# lift starts at the hinge, not the occiput: open_jaw turns the head up about the hinge, which swings the head's back
# 0.55 into the grip on that side (its top met the grip at y -7.8, 1.3 below the occiput). The jaws, the crystal and
# the snout (in front of the hinge) stay on the axis. The belly is then settled onto the leather by measurement
# (02-build-mesh: settle_neck, h_fix)
COIL_Y0 = -4.6           # the helix's phase: it passes the -z face here (the coil's turns stay where they were)
NECK_LIFT = 1.8          # the centre line from the axis onto the -z face over this height above the jaw hinge (2.4
                         # left the neck in the grip at the head: bare leather between them); a smootherstep, so the
                         # bend starts with no curvature (a smoothstep's showed as a seam across the head's top)
# the neck's S on the -z face (curator's drawing on the render from -z: "like this"): up from the middle of the head's
# top, swinging out toward -x, then back across the face into the coil's turn (it joins the helix at COIL_Y0 with the
# helix's own slope: a Hermite curve, no kink; the coil above is unchanged)
NECK_SWAY = 0.75         # radians round toward -x at the swing's peak
NECK_SWAY_Y = -5.5       # the peak's height
NECK_SWAY_FROM = 1.55    # the swing starts this far above the jaw hinge, slowly (a smootherstep): first straight
                         # up from the middle of the head's top, as drawn (from 0.3 it left the head off-centre;
                         # 0.85 rad from the occiput in 0.9 bent the neck at 460 deg a unit)
# the cross-sections through the lift stay nearer upright: they turn UPRIGHT less than the path (blended toward +y
# over the lift, faded out above it). Turned with the path, the head's back (1.4 deep) bent onto the face on a curve
# tighter than its half-depth and its top folded into itself: a crease where the neck met the head (20% of the skin
# there overlapped, 2026-11-15). Upright sections shear instead of folding (13% thinner across at the steepest)
UPRIGHT = 0.5
COIL_TOP = 9.5          # the tail tip's centre: tucked inside the ouroboros ring's body (curator: "clean up the
                         # connector and handle"; under billyro's band it showed as a pale sliver)
WRAPS = 3.6              # turns from the neck up to the tail tip (the drawing: four strokes on the -z face)
PATH_SAMPLES = 4000
# the connector (curator 2026-11-15: "the connecting piece is a snake eating its own tail"): an ouroboros of the
# same rattlesnake in place of billyro's top band, round the joint of the grip and the Noble mount's shaft. It lay
# on the grip's ellipse (0.85 x 0.62) while the Noble shaft (0.86 x 0.98 round) came down into its middle, so only
# 0.2 - 0.4 of it stood out of the shaft (curator: "tidy this up as the ouroboros is clipping, needs to be more
# visible"): now its belly rests on the shaft's own ellipse (measured by tools/02, passed as RingLayout's
# `ellipse`), centred on the shaft's lower end, and the grip flares out to the shaft under it
RING_Y = 9.8             # the ring's centre height: the Noble shaft's lower end (noble.SHAFT_FROM_Y)
SIGMA_RING_HEAD = 0.17   # head 2.4 long, 1.5 tall (0.13 read as a lump)
SIGMA_RING_BODY = 0.13   # body 1.06 tall, 0.78 thick (0.11 on the grip's ellipse was swallowed by the shaft)
RING_JAW = (0.0, 24.0)   # the jaws part round the tail: the lower jaw drops, the skull stays on the path. A lifted
                         # skull turns about the jaw hinge and levers the neck down into a fold where the head meets
                         # the ring (30 split evenly: triangles stretched 5x, a spike at the throat; (22, 2): 4.3x)
RING_TOUCH = 0.65        # where the head's belly rests on the ring, in head lengths from the snout (the hinge): the
                         # snout end stands off far enough for the dropped jaw
RING_RISE = 0.6          # the body joins the ring this many head lengths round from the tangent head's ends
RING_TAIL_IN = 0.55      # how far the tail tip runs into the mouth, in head lengths
RING_SMOOTH = 0.12       # the corners where the straight head meets the ring rounded over this
RING_TESS = 2
# the blade (curator 2026-11-15: "add 3 fanning metal snakes to either side of the blade", with a drawing: three
# wavy strokes fanning from the spine's middle rivet toward the edge, upward, outward, downward). Relief snakes
# on each face, belly on the blade, tails under the middle rivet (x -1.52, y 27.52), heads toward the edge
SIGMA_BLADE_HEAD = 0.10   # head 1.4 long, 0.84 wide (0.075 read as thin lines)
SIGMA_BLADE_BODY = 0.075  # body 0.62 wide, standing 0.45 off the face
BLADE_TESS = 1
BLADE_JAW = 0.0
BLADE_ORIGIN = (-1.52, 27.52)  # where the tails meet: the middle rivet next to billyro's neck (the drawing's
                               # meeting point); inside the neck snake's mouth while that stood
BLADE_SNAKES = (          # (snout (x, y), waves, amplitude): upward, outward, downward
    ((-8.4, 33.3), 1.25, 0.45),
    ((-9.5, 27.9), 1.5, 0.40),
    ((-8.4, 21.9), 1.25, 0.45))
BLADE_TAIL_OFF = 0.25     # each tail tip this far out of the rivet's centre, toward its own snout
# curator, in game (2026-11-15): "bring the right snake a little more to the left so theres equal spacing between the
# base of the snakes", then, on the render of that: "now the top snakes base so it meets the other two". The bases
# are where the bodies run under the socket's blade face; spaced by centre line, the downward body (crossing it
# steeply, so 1.2 wide there) touched the middle one and the upward one stood 0.39 off. tools/02 slides both outer
# tails along y (blade_tails) until each body's edge lies BLADE_ROOT_GAP from the middle one's at the socket face:
# the three meet in one root; the heads stay
BLADE_ROOT_GAP = 0.06     # between the bodies' edges at the socket face
BLADE_ROOT_HALF = 0.26    # a body's half-width there (measured on the built mesh: the middle snake, 0.51 wide)
# billyro's belt ring on the neck (the holder's ring, hanging from a clasp on the collar cup), an ouroboros since the
# curator's "re add the original upper shaft section and the ring (change the ring to an oroboros" (2026-11-15):
# a torus of centreline radius 3.0, tube radius 0.5, centre (1.25, 23.56, 4.92), plane normal (0, 0.5, -0.866),
# fitted by tools/02 from the holder shape; the snake on that circle, as thick as the tube
SIGMA_NECKRING_HEAD = 0.17  # head 2.4 long
SIGMA_NECKRING_BODY = 0.14  # body 1.15 wide, 0.84 deep (the ring's tube is 1.0)
NECKRING_TESS = 2
NECKRING_JAW = 30.0
# the neck (curator 2026-11-15, after the spine: "make the spine of the axe a snake with its mouth open spanning
# into the axe blade", drawn rising from the connector, bending toward the blade, jaws gaping round its back): the
# same rattlesnake from inside the ouroboros up the handle axis, curving into its head, which faces the blade with
# its jaws round the blade's back. The blade's back is a V (apex x -0.48, y 28; edges at 138 deg and 230 deg): the
# jaws gape wider (124 / 244 deg) so the blade sits between them, the apex just inside the mouth's corner
NECK_SIGMA_HEAD = 0.42    # head 5.9 long, 3.5 wide; jaws 3.4 from the corner to the snout (the drawing's ~4)
NECK_SIGMA_BODY = 0.24    # body 2.0 wide, 1.4 deep (the spine was 2.7)
NECK_HINGE = (-0.25, 28.0)   # where the mouth's corners sit: the blade's apex just inside them
NECK_HEAD_DIR = 134.0     # the head's path direction (deg from +x, in the blade's plane): the neck's bend goes on
NECK_SKULL_UP = 10.0      # the skull turned up from it (upper jaw at 124 deg; 32 kinked the neck behind it) ...
NECK_JAW_DOWN = 110.0     # ... the lower jaw down (244 deg): both jaws outside the blade's edges (138 / 230 deg;
                          # jaws along them were half buried in the blade)
NECK_BEND_Y = 23.0        # the body runs straight up the handle axis to here, then curves into the head
NECK_HANDLES = (1.6, 1.4) # the curve's tangent lengths at the head's back and at the bend
NECK_TAIL_Y = 9.7         # the tail tip, on the axis inside the ouroboros
NECK_TESS = 2


def smoothstep(a, b, x):
    u = np.clip((np.asarray(x, float) - a) / (b - a), 0, 1)
    return u * u * (3 - 2 * u)


def load_snake(mods_dir):
    """The rattlesnake's one shape through PyNifly (it is skinned: nifse reads unskinned shapes only): positions,
    normals, UVs, triangles."""
    tools = json.load(open(os.path.join(REPO, '.claude', 'config', 'tools.json'), encoding='utf-8-sig'))
    sys.path.insert(0, tools['pynifly'])
    from pyn.pynifly import NifFile
    bsa = os.path.join(mods_dir, SNAKE_MOD, SNAKE_BSA)
    assert os.path.isfile(bsa), f'{bsa} missing: Triumvirate - Mage Archetypes must be installed'
    d, listing = _bsa.listing(bsa)
    raw = _bsa.read(d, listing[SNAKE_KEY])
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, 'snake.nif')
        open(path, 'wb').write(raw)
        nif = NifFile(path)
        assert len(nif.shapes) == 1, len(nif.shapes)
        s = nif.shapes[0]
        P = np.array(s.verts, float)
        N = np.array(s.normals, float)
        UV = np.array(s.uvs, float)
        T = np.array(s.tris, np.int64)
    assert len(P) == SNAKE_VERTS and len(T) == SNAKE_TRIS, (len(P), len(T))
    assert abs(P[:, 1].max() - SNOUT_Y) < 0.05 and abs(P[:, 1].min() - TAIL_Y) < 0.05, (P[:, 1].min(), P[:, 1].max())
    return P, N, UV, T


def snake_texture(mods_dir, rel):
    d, listing = _bsa.listing(os.path.join(mods_dir, SNAKE_MOD, SNAKE_TEX_BSA))
    return _bsa.read(d, listing[rel.lower()])


def nz(v):
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-12)


def tangents(P, N, UV, T):
    """Per-vertex tangent frame the game's way (measured on vanilla's humanspine: tangent = +dP/dv, bitangent =
    +dP/du), each orthogonalised to the normal."""
    du, dv = np.zeros_like(P), np.zeros_like(P)
    e1, e2 = P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]
    a1, a2 = UV[T[:, 1]] - UV[T[:, 0]], UV[T[:, 2]] - UV[T[:, 0]]
    det = a1[:, 0] * a2[:, 1] - a2[:, 0] * a1[:, 1]
    ok = np.abs(det) > 1e-12
    dPu = (e1 * a2[:, 1:2] - e2 * a1[:, 1:2]) / np.where(ok, det, 1)[:, None]
    dPv = (e2 * a1[:, 0:1] - e1 * a2[:, 0:1]) / np.where(ok, det, 1)[:, None]
    for i in range(3):
        np.add.at(du, T[ok, i], dPu[ok])
        np.add.at(dv, T[ok, i], dPv[ok])
    Tg = nz(dv - N * (dv * N).sum(1, keepdims=True))
    Bt = nz(du - N * (du * N).sum(1, keepdims=True))
    return Tg, Bt


def lower_jaw(P, T):
    """1.0 for every vertex of the lower jaw, by the mesh's own split: in front of TEAR_Y the mouth parts the head
    into an upper half (the head's top and the palate) and a lower half (its underside and the mouth's floor) that
    meet only at the two mouth corners; each half is flood-filled from a seed triangle (the topmost / lowest one at
    y 29 - 31) without crossing TEAR_Y, so no height rule has to tell the lip edges apart (along the sides the upper
    and lower lip edges are 0.06 - 0.15 apart). The corners take 0.5 (they stay put while the jaws part); behind
    TEAR_Y the throat's underside (below the hinge) takes 1.0 and open_jaw fades it out toward THROAT."""
    from collections import defaultdict, deque
    key = {}
    rep = np.array([key.setdefault(tuple(p), len(key)) for p in np.round(P, 5)])
    by_edge = defaultdict(list)
    for i, t in enumerate(T):
        for a in range(3):
            u, v = rep[t[a]], rep[t[(a + 1) % 3]]
            by_edge[(min(u, v), max(u, v))].append(i)
    nb = defaultdict(list)
    for tris in by_edge.values():
        for a in tris:
            nb[a] += [b for b in tris if b != a]
    front = P[T][:, :, 1].min(1) > TEAR_Y
    cen = P[T].mean(1)
    band = np.where(front & (cen[:, 1] > 29) & (cen[:, 1] < 31))[0]
    up, lo = band[np.argmax(cen[band, 2])], band[np.argmin(cen[band, 2])]
    lab = np.zeros(len(T), int)
    lab[up], lab[lo] = 1, 2
    queue, meet = deque([up, lo]), 0
    while queue:
        a = queue.popleft()
        for b in nb[a]:
            if front[b] and lab[b] == 0:
                lab[b] = lab[a]
                queue.append(b)
            elif front[b] and lab[b] != lab[a]:
                meet += 1
    assert meet == 0 and not (front & (lab == 0)).any(), (meet, (front & (lab == 0)).sum())
    upper_v, lower_v = np.unique(T[lab == 1]), np.unique(T[lab == 2])
    corners = np.intersect1d(upper_v, lower_v)
    assert len(corners) <= 4 and (lab == 2).sum() >= 60, (len(corners), (lab == 2).sum())  # the two mouth corners
    w = ((P[:, 1] > HEAD_Y - 1) & (P[:, 2] < HINGE[1])).astype(float)     # behind the tear: the throat's underside
    w[upper_v] = 0.0
    w[lower_v] = 1.0
    w[corners] = 0.5
    return w


def open_jaw(P, N, Tg, Bt, w, jaw_open=JAW_OPEN):
    """The head tilted up about the hinge (faded in along the neck) and the lower jaw (weight w) turned down relative
    to it (faded out behind the hinge toward the throat): positions and frames turned in the y-z plane. jaw_open: the
    angle between the jaws (the head up by half, so the mouth's bisector stays the path's direction), or (skull up,
    lower jaw down) in degrees from the path's direction."""
    up, down = (0.5 * jaw_open, 0.5 * jaw_open) if np.isscalar(jaw_open) else jaw_open
    th_up, th = np.radians(up), np.radians(up + down)
    tilt = th_up * smoothstep(TILT_NECK[0], TILT_NECK[1], P[:, 1])
    jaw = th * w * np.where(P[:, 1] >= HINGE[0], 1.0, smoothstep(THROAT, HINGE[0], P[:, 1]))
    a = tilt - jaw                                         # + turns the snout toward +z (up)
    c, s = np.cos(a), np.sin(a)

    def turn(v, about=None):
        v = v.copy()
        y0, z0 = (HINGE if about else (0.0, 0.0))
        dy, dz = v[:, 1] - y0, v[:, 2] - z0
        v[:, 1] = y0 + dy * c - dz * s
        v[:, 2] = z0 + dy * s + dz * c
        return v
    return turn(P, True), turn(N), turn(Tg), turn(Bt)


def offset_polyline(base, normal, h_fn, u0=0.0, iters=3):
    """base + h(u) * normal, h by each point's arc length from the snout (u0 at the first point), iterated."""
    Q = base.copy()
    for _ in range(iters):
        u = u0 + np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(Q, axis=0), axis=1))])
        Q = base + h_fn(u)[:, None] * normal
    return Q


def smooth_after(Q, u_from, width):
    """The polyline smoothed (Gaussian over `width` of arc length) beyond arc length u_from, eased in, so a straight
    head stays straight and the corners behind it round off."""
    s = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(Q, axis=0), axis=1))])
    step = max(s[-1] / (len(Q) - 1), 1e-6)
    k = max(int(width / step), 1)
    w = np.exp(-0.5 * (np.arange(-3 * k, 3 * k + 1) / k) ** 2)
    w /= w.sum()
    pad = np.vstack([np.repeat(Q[:1], 3 * k, 0), Q, np.repeat(Q[-1:], 3 * k, 0)])
    sm = np.stack([np.convolve(pad[:, i], w, mode='valid') for i in range(3)], -1)
    a = smoothstep(u_from, u_from + 2 * width, s)[:, None]
    return Q * (1 - a) + sm * a


class Layout:
    """A path on the axe and the mapping of the snake's own coordinates onto it. Subclasses give path(): the centre
    line from the snout tip to the tail tip (dense points) and the dorsal direction wanted at each. The head keeps
    its proportions at sigma_head; the body (past NECK_Y) has sigma_body across and is stretched or compressed along
    the path to fill it."""
    STRETCH = (0.6, 2.5)
    H_SMOOTH = 0.0           # the belly depth smoothed along the path over this (world units); 0: as measured

    def __init__(self, P0, sigma_head=SIGMA_HEAD, sigma_body=SIGMA_BODY):
        self.sigma_head, self.sigma_body = sigma_head, sigma_body
        # the belly's depth below the dorsal centre per height (the snake's own rings): how far the centre line
        # stands off the surface the belly rests on
        ys = np.linspace(TAIL_Y, SNOUT_Y, 300)
        zmin = np.array([P0[np.abs(P0[:, 1] - y) < 1.5, 2].min() if (np.abs(P0[:, 1] - y) < 1.5).any() else np.nan
                         for y in ys])
        ok = np.isfinite(zmin)
        self.belly_y, self.belly_z = ys[ok], np.convolve(np.pad(zmin[ok], 3, mode='edge'), np.ones(7) / 7, 'valid')
        self.stretch = 1.0
        self.grid = np.linspace(TAIL_Y - 1, SNOUT_Y + 12, 6000)
        self.h_of_u = None
        for _ in range(4):                                   # path <-> stretch <-> belly depth: converges fast
            Q, target = self.path()
            self.set_path(Q, target)
            self.fit_length()

    @property
    def head_len(self):
        return (SNOUT_Y - HEAD_Y) * self.sigma_head

    def h(self, u):
        """The belly depth at arc lengths u (before the first fit: the body's)."""
        if self.h_of_u is None:
            return np.full(len(u), 2.05 * self.sigma_body)
        return self.h_of_u(u)

    # -- scales along the snake --
    def sigma(self, y):
        return self.sigma_body + (self.sigma_head - self.sigma_body) * smoothstep(NECK_Y, HEAD_Y, y)

    def lam(self, y):
        w = 1 - smoothstep(NECK_Y, HEAD_Y, y)
        return self.sigma(y) * (1 + (self.stretch - 1) * w)

    def u_of_y(self, y):
        """Arc length from the snout tip (u 0) toward the tail, for snake heights y."""
        g = self.grid
        lam = self.lam(g)
        cum = np.concatenate([[0.0], np.cumsum((lam[1:] + lam[:-1]) / 2 * np.diff(g))])   # from the grid's bottom
        at_snout = np.interp(SNOUT_Y, g, cum)
        return at_snout - np.interp(y, g, cum)

    def fit_length(self):
        g = self.grid
        w = 1 - smoothstep(NECK_Y, HEAD_Y, g)
        m = (g >= TAIL_Y) & (g <= SNOUT_Y)
        A = np.trapezoid(self.sigma(g[m]), g[m])
        B = np.trapezoid((self.sigma(g) * w)[m], g[m])
        self.stretch = 1 + (self.L - A) / B
        assert self.STRETCH[0] < self.stretch < self.STRETCH[1], (type(self).__name__, self.stretch)
        yy = np.linspace(TAIL_Y, SNOUT_Y, 2000)
        uu = self.u_of_y(yy)
        depth = (CZ - np.interp(yy, self.belly_y, self.belly_z)) * self.sigma(yy)
        order = np.argsort(uu)
        uo, do = uu[order], depth[order]
        if self.H_SMOOTH:
            # the belly line is piecewise linear (300 bins): where the depth changes fast (the coil's neck) each corner
            # bent the centre line (a crease across the body); smoothed along the path, resampled evenly
            ug = np.linspace(uo[0], uo[-1], 4000)
            dg = np.interp(ug, uo, do)
            k = max(int(self.H_SMOOTH / (ug[1] - ug[0])), 1)
            w = np.exp(-0.5 * (np.arange(-3 * k, 3 * k + 1) / k) ** 2)
            uo, do = ug, np.convolve(np.pad(dg, 3 * k, mode='edge'), w / w.sum(), 'valid')
        self.h_of_u = lambda u: np.interp(u, uo, do)  # noqa: E731

    def set_path(self, Q, target):
        seg = np.linalg.norm(np.diff(Q, axis=0), axis=1)
        keep = np.concatenate([[True], seg > 1e-7])
        Q, target = Q[keep], target[keep]
        s = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(Q, axis=0), axis=1))])
        self.Q, self.s, self.L = Q, s, s[-1]
        self.t = nz(np.gradient(Q, s, axis=0))
        self.d = nz(target - (target * self.t).sum(1, keepdims=True) * self.t)

    def path(self):
        raise NotImplementedError

    def upright(self, u):
        """How far each section at arc length u is blended toward +y (None: they follow the path)."""
        return None

    def frames(self, u):
        """Centre, path tangent (toward the tail) and dorsal direction at arc lengths u (straight on past the
        snout)."""
        s = self.s
        c = np.stack([np.interp(u, s, self.Q[:, i]) for i in range(3)], -1)
        t = nz(np.stack([np.interp(u, s, self.t[:, i]) for i in range(3)], -1))
        a = self.upright(u)
        if a is not None:                                   # the sections turned less than the path (CoilLayout)
            t = nz(t * (1 - a)[:, None] + a[:, None] * np.array([0.0, 1.0, 0.0]))
        d = np.stack([np.interp(u, s, self.d[:, i]) for i in range(3)], -1)
        d = nz(d - (d * t).sum(1, keepdims=True) * t)
        past = u < 0
        c[past] = self.Q[0] + self.t[0] * u[past, None]
        beyond = u > s[-1]                                  # the tail tip, by the length grid's rounding
        c[beyond] = self.Q[-1] + self.t[-1] * (u[beyond] - s[-1])[:, None]
        return c, t, d

    def map(self, X):
        """Snake coordinates -> axe coordinates."""
        y = X[:, 1]
        c, t, d = self.frames(self.u_of_y(y))
        l = np.cross(-t, d)                                # (lateral, toward the head, dorsal): right-handed
        sg = self.sigma(y)
        return c + ((X[:, 0] - CX) * sg)[:, None] * l + ((X[:, 2] - CZ) * sg)[:, None] * d

    def jacobian(self, X, h=0.01):
        J = np.empty((len(X), 3, 3))
        for k in range(3):
            e = np.zeros(3)
            e[k] = h
            J[:, :, k] = (self.map(X + e) - self.map(X - e)) / (2 * h)
        return J


def grip_ellipse(psi, y, h=0.0, ellipse=None):
    """The grip's ellipse point at parameter psi (pushed out along its normal by h) and that normal. psi grows toward
    -x on the -z face (psi = pi/2). `ellipse` = (cx, cz, a, b) for another ellipse round the handle (the Noble
    shaft's); the grip's by default."""
    cx, cz, a, b = ellipse if ellipse is not None else (AXIS_X, 0.0, GRIP_A, GRIP_B)
    psi = np.asarray(psi, float)
    y = np.broadcast_to(np.asarray(y, float), psi.shape)
    e = np.stack([cx + a * np.cos(psi), y, cz - b * np.sin(psi)], -1)
    n = nz(np.stack([np.cos(psi) / a, np.zeros_like(psi), -np.sin(psi) / b], -1))
    return e + np.asarray(h, float)[..., None] * n, n


class CoilLayout(Layout):
    """The grip snake: head straight down the axis below the grip (top toward -z), its top running on into the neck
    up the grip's -z face, easing into WRAPS turns up the grip, the tail tip at COIL_TOP. h_fix(u): a correction to
    the belly depth (the neck settled onto the leather by measurement)."""

    H_SMOOTH = 0.15

    def __init__(self, P0, h_fix=None):
        self.h_fix = h_fix
        super().__init__(P0)

    def h(self, u):
        h = super().h(u)
        return h if self.h_fix is None else h + self.h_fix(u)

    def psi_of_y(self, y):
        """The coil's angle round the grip at heights y (psi grows going down; the -z face is pi/2 mod 2 pi, where x
        falls going down): the helix from COIL_Y0 up (psi_end there, psi_tail at COIL_TOP); below it the neck's S: from
        the -z face at NECK_SWAY_FROM above the hinge out to NECK_SWAY toward -x at NECK_SWAY_Y (level there), then a
        Hermite curve back to the face at COIL_Y0 arriving with the helix's slope."""
        psi_end = np.pi / 2 + 2 * np.pi * np.ceil(WRAPS)
        rate = 2 * np.pi * WRAPS / (COIL_TOP - COIL_Y0)
        y = np.asarray(y, float)
        helix = psi_end - rate * (y - COIL_Y0)
        a = np.clip((y - self.y_hinge - NECK_SWAY_FROM) / (NECK_SWAY_Y - self.y_hinge - NECK_SWAY_FROM), 0.0, 1.0)
        out = NECK_SWAY * a ** 3 * (a * (6 * a - 15) + 10)               # smootherstep
        L = COIL_Y0 - NECK_SWAY_Y
        t = np.clip((y - NECK_SWAY_Y) / L, 0.0, 1.0)
        back = NECK_SWAY * (2 * t ** 3 - 3 * t ** 2 + 1) - rate * L * (t ** 3 - t ** 2)
        neck = psi_end + np.where(y < NECK_SWAY_Y, out, back)
        return np.where(y < COIL_Y0, neck, helix), psi_end, psi_end - 2 * np.pi * WRAPS

    def upright(self, u):
        u_hinge = (SNOUT_Y - HINGE[0]) * self.sigma_head
        u_end = np.interp(self.y_hinge + NECK_LIFT, self.Q[:, 1][self.s >= u_hinge], self.s[self.s >= u_hinge])             if hasattr(self, 's') else u_hinge + NECK_LIFT * 1.4
        return UPRIGHT * smoothstep(u_hinge - 0.2, u_hinge + 0.3, u) * (1 - smoothstep(u_end, u_end + 0.8, u))

    @property
    def y_hinge(self):
        return OCCIPUT_Y - self.head_len + (SNOUT_Y - HINGE[0]) * self.sigma_head

    def path(self):
        snout_y = OCCIPUT_Y - self.head_len
        u_hinge = (SNOUT_Y - HINGE[0]) * self.sigma_head                  # the head keeps sigma_head: exact
        y_hinge = snout_y + u_hinge
        snout, hinge = np.array([AXIS_X, snout_y, 0.0]), np.array([AXIS_X, y_hinge, 0.0])
        front = snout + (hinge - snout) * np.linspace(0, 1, 150)[:, None]   # the snout and jaws, on the axis
        # behind the hinge: on the grip's surface (the belly resting on it), the centre line lifted from the axis
        # onto it over NECK_LIFT
        y = np.linspace(y_hinge, COIL_TOP, PATH_SAMPLES)
        psi, psi_end, psi_tail = self.psi_of_y(y)
        base, normal = grip_ellipse(psi, y)
        axis = np.stack([np.full_like(y, AXIS_X), y, np.zeros_like(y)], -1)
        t = np.clip((y - y_hinge) / NECK_LIFT, 0.0, 1.0)
        lift = (t ** 3 * (t * (6 * t - 15) + 10))[:, None]                  # smootherstep
        body = base.copy()
        for _ in range(3):
            u = u_hinge + np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(body, axis=0), axis=1))])
            body = axis * (1 - lift) + (base + self.h(u)[:, None] * normal) * lift
        Q = np.vstack([front[:-1], body])
        target = np.vstack([np.repeat([[0.0, 0.0, -1.0]], len(front) - 1, 0), normal])   # normal = -z up the neck
        self.psi_end, self.psi_tail, self.y_low = psi_end, psi_tail, y_hinge + NECK_LIFT
        return Q, target


class RingLayout(Layout):
    """An ouroboros: one ring, back outward; the head a straight chord of the ring centred on psi_head (facing growing
    psi), the body round the ring back to the snout, the tail tip turning in along the chord into the open mouth
    (RING_TAIL_IN of it). The ring is curve(psi, h): by default round the grip at RING_Y, its belly on the grip (h:
    the belly's depth), the head on the -z face (facing -x)."""
    STRETCH = (0.12, 1.5)
    psi_head = np.pi / 2
    tangent_head = False

    def __init__(self, P0, sigma_head=SIGMA_RING_HEAD, sigma_body=SIGMA_RING_BODY, ellipse=None, tangent_head=False):
        self.ellipse = ellipse                                # (cx, cz, a, b) the belly rests on; the grip's if None
        self.tangent_head = tangent_head                      # the head on the ring's tangent, not a chord
        super().__init__(P0, sigma_head, sigma_body)

    def curve(self, psi, h=0.0):
        return grip_ellipse(psi, RING_Y, h, getattr(self, 'ellipse', None))

    def path(self):
        L = self.head_len
        hh = float(self.h(np.array([0.5 * L]))[0])           # the head's belly depth
        mid = self.psi_head

        def chord(alpha):
            a = self.curve(np.array([mid + alpha / 2]), hh)[0][0]
            b = self.curve(np.array([mid - alpha / 2]), hh)[0][0]
            return np.linalg.norm(a - b)
        lo, hi = 1e-3, np.pi
        for _ in range(60):                                   # the chord one head long
            m = (lo + hi) / 2
            lo, hi = (m, hi) if chord(m) < L else (lo, m)
        alpha = (lo + hi) / 2
        snout = self.curve(np.array([mid + alpha / 2]), hh)[0][0]
        back = self.curve(np.array([mid - alpha / 2]), hh)[0][0]
        psi_s, psi_b = mid + alpha / 2, mid - alpha / 2
        if self.tangent_head:
            # the head straight along the ring's tangent at its middle, its belly resting there; its ends stand off
            # (a chord's middle sank 0.7 into the Noble shaft: the ring is small against the head)
            c_mid = self.curve(np.array([mid]), hh)[0][0]
            t = nz(self.curve(np.array([mid + 1e-4]), hh)[0][0] - self.curve(np.array([mid - 1e-4]), hh)[0][0])
            snout, back = c_mid + t * L * RING_TOUCH, c_mid - t * L * (1 - RING_TOUCH)
            ps = mid + np.linspace(-np.pi / 2, np.pi / 2, 4001)
            pts = self.curve(ps, hh)[0]
            psi_s = ps[np.argmin(np.linalg.norm(pts - snout, axis=1))]   # the ring's points under the head's ends
            psi_b = ps[np.argmin(np.linalg.norm(pts - back, axis=1))]
            self.standoff = float(np.linalg.norm(back - self.curve(np.array([psi_b]), hh)[0][0]))
        head = snout + (back - snout) * np.linspace(0, 1, 120)[:, None]
        n_mid = self.curve(np.array([mid]))[1][0]
        if not self.tangent_head:
            psi = np.linspace(psi_b, psi_s - 2 * np.pi, PATH_SAMPLES)      # round, back to the snout
            base, normal = self.curve(psi)
            arc = offset_polyline(base, normal, self.h, L)
        else:
            # the body leaves the head's back straight on and settles onto the ring RING_RISE head lengths round,
            # and leaves the ring as far before the snout to arrive heading into the mouth: cubic Hermite joins,
            # tangent-continuous at both ends (a straight lift put a ~40 deg kink at the head's back: the neck tore)
            dpsi = RING_RISE * L / np.linalg.norm(self.curve(np.array([psi_b + 1e-4]), hh)[0][0]
                                                  - self.curve(np.array([psi_b - 1e-4]), hh)[0][0]) * 2e-4
            psi = np.linspace(psi_b - dpsi, psi_s - 2 * np.pi + dpsi, PATH_SAMPLES)
            base, normal = self.curve(psi)
            ring = offset_polyline(base, normal, self.h, L + RING_RISE * L)

            def hermite(p0, m0, p1, m1, n=200):
                k = np.linspace(0, 1, n)[:, None]
                return ((2 * k ** 3 - 3 * k ** 2 + 1) * p0 + (k ** 3 - 2 * k ** 2 + k) * m0
                        + (-2 * k ** 3 + 3 * k ** 2) * p1 + (k ** 3 - k ** 2) * m1)
            c0, c1 = np.linalg.norm(ring[0] - back), np.linalg.norm(snout - ring[-1])
            lead = hermite(back, -t * c0, ring[0], nz(ring[1] - ring[0]) * c0)
            trail = hermite(ring[-1], nz(ring[-1] - ring[-2]) * c1, snout, -t * c1)
            k = np.linspace(0, 1, 200)[:, None]
            arc = np.vstack([lead[:-1], ring, trail[1:]])
            normal = np.vstack([nz((1 - k) * n_mid + k * normal[0])[:-1], normal, nz((1 - k) * normal[-1] + k * n_mid)[1:]])
        into = nz(back - snout)
        tail = arc[-1] + into * (RING_TAIL_IN * L) * np.linspace(0, 1, 80)[1:, None]
        Q = np.vstack([head[:-1], arc, tail])
        target = np.vstack([np.repeat(n_mid[None], len(head) - 1, 0), normal, np.repeat(n_mid[None], len(tail), 0)])
        Q = smooth_after(Q, L * 0.95, RING_SMOOTH)
        self.alpha = alpha
        return Q, target


class CircleRingLayout(RingLayout):
    """An ouroboros on a free circle (centre, plane normal, centreline radius): the snake's centre line on the circle
    itself (no surface to rest on), its back outward, its width across the ring's plane; psi = 0 toward `zero` (a
    point in or near the plane), the head centred on psi_head."""

    def __init__(self, P0, centre, normal, radius, zero, psi_head, sigma_head, sigma_body):
        n = nz(np.asarray(normal, float))
        e1 = np.asarray(zero, float) - np.asarray(centre, float)
        e1 = nz(e1 - (e1 @ n) * n)
        self.c, self.n, self.e1, self.e2, self.r = np.asarray(centre, float), n, e1, np.cross(n, e1), float(radius)
        self.psi_head = psi_head
        super().__init__(P0, sigma_head, sigma_body)

    def h(self, u):
        return np.zeros(len(u))                               # the centre line is the ring's own

    def curve(self, psi, h=0.0):
        psi = np.asarray(psi, float)
        radial = np.cos(psi)[:, None] * self.e1 + np.sin(psi)[:, None] * self.e2
        return self.c + self.r * radial, radial


class NeckLayout(Layout):
    """The neck snake: the head straight along NECK_HEAD_DIR, placed so the mouth's corner (the hinge) sits at
    NECK_HINGE; behind it a cubic down to the handle axis at NECK_BEND_Y (heading down), then straight down the axis
    to the tail tip. Its back faces +x (the poll) all the way, so the bend's outer side and the head's top face up
    and away from the blade, the belly toward it."""
    STRETCH = (0.2, 1.5)

    def path(self):
        L = self.head_len
        a = np.radians(NECK_HEAD_DIR)
        t = np.array([np.cos(a), np.sin(a), 0.0])             # toward the snout
        hinge = np.array([NECK_HINGE[0], NECK_HINGE[1], 0.0])
        occ = hinge - (HINGE[0] - HEAD_Y) * self.sigma_head * t
        snout = occ + L * t
        head = snout + (occ - snout) * np.linspace(0, 1, 150)[:, None]
        bend = np.array([AXIS_X, NECK_BEND_Y, 0.0])
        h0, h1 = NECK_HANDLES
        c0, c1, c2, c3 = occ, occ - t * h0, bend + np.array([0.0, h1, 0.0]), bend
        k = np.linspace(0, 1, 600)[:, None]
        curve = (1 - k) ** 3 * c0 + 3 * (1 - k) ** 2 * k * c1 + 3 * (1 - k) * k ** 2 * c2 + k ** 3 * c3
        down = bend + np.array([0.0, -1.0, 0.0]) * (NECK_BEND_Y - NECK_TAIL_Y) * np.linspace(0, 1, 800)[1:, None]
        Q = np.vstack([head[:-1], curve, down])
        Q = smooth_after(Q, L * 0.95, 0.25)
        target = np.repeat([[1.0, 0.0, 0.0]], len(Q), 0)
        self.hinge_at, self.occ_at = hinge, occ
        return Q, target


def blade_path_xy(S, O, waves, amplitude, head_len):
    """A blade snake's centre line on the face (x, y), snout first: the head straight from the snout S toward the
    tail tip O, one head long, then the body to O with a sideways wave that vanishes at both ends (flattened under
    the head's back)."""
    S, O = np.asarray(S, float), np.asarray(O, float)
    direction = (O - S) / np.linalg.norm(O - S)
    H = S + direction * head_len                              # the head's back: the head points along the line
    k = np.linspace(0, 1, PATH_SAMPLES)
    side = np.array([-direction[1], direction[0]])
    env = np.sin(np.pi * k) ** 0.8 * smoothstep(0.0, 0.18, k)
    body = H + (O - H) * k[:, None] + side * (amplitude * env * np.sin(2 * np.pi * waves * k))[:, None]
    head = S + (H - S) * np.linspace(0, 1, 60)[:, None]
    return np.vstack([head[:-1], body])


def crossing(xy, x):
    """Where a centre line (snout first) last crosses the line x on its way to the tail: its y and its direction."""
    d = xy[:, 0] - x
    i = np.where(np.sign(d[:-1]) != np.sign(d[1:]))[0]
    assert len(i), ('the snake never crosses x', x)
    i = i[-1]
    f = d[i] / (d[i] - d[i + 1])
    return float(xy[i, 1] + f * (xy[i + 1, 1] - xy[i, 1])), nz(xy[i + 1] - xy[i])


def blade_tails(shift, face_x):
    """The blade snakes as laid: [(snout, tail, waves, amplitude)] on the moved blade (`shift`), each tail
    BLADE_TAIL_OFF out of the rivet toward its snout, the outer two then slid along y (bisection) until each body's
    edge lies BLADE_ROOT_GAP from the middle one's where they cross the socket face x = face_x (a body crossing it at
    a slant is wider there: BLADE_ROOT_HALF / |its x direction|). Returns them, the edge gaps and the slides."""
    head_len = (SNOUT_Y - HEAD_Y) * SIGMA_BLADE_HEAD
    r = np.array(BLADE_ORIGIN) + shift
    snakes = []
    for snout, waves, amp in BLADE_SNAKES:
        snout = np.array(snout) + shift
        snakes.append([snout, r + BLADE_TAIL_OFF * (snout - r) / np.linalg.norm(snout - r), waves, amp])
    assert len(snakes) == 3

    def edges(i, dy=0.0):                                     # (lower, upper) edge of body i at the socket face
        sn, tail, waves, amp = snakes[i]
        y, d = crossing(blade_path_xy(sn, tail + np.array([0.0, dy]), waves, amp, head_len), face_x)
        half = BLADE_ROOT_HALF / max(abs(d[0]), 0.2)
        return y - half, y + half
    mid = edges(1)
    gap = {0: lambda dy: edges(0, dy)[0] - mid[1], 2: lambda dy: mid[0] - edges(2, dy)[1]}
    slides = {}
    for i in (0, 2):
        lo, hi = -3.0, 3.0
        f = lambda dy: gap[i](dy) - BLADE_ROOT_GAP              # noqa: E731
        assert f(lo) * f(hi) < 0, ('the slide cannot reach the root', i)
        for _ in range(60):
            m = (lo + hi) / 2
            lo, hi = (m, hi) if f(m) * f(lo) > 0 else (lo, m)
        slides[i] = (lo + hi) / 2
    for i, dy in slides.items():
        snakes[i][1] = snakes[i][1] + np.array([0.0, dy])
    gaps = (edges(0)[0] - mid[1], mid[0] - edges(2)[1])
    assert max(abs(g - BLADE_ROOT_GAP) for g in gaps) < 1e-3, gaps
    return [tuple(s_) for s_ in snakes], gaps, slides


class BladeLayout(Layout):
    """A relief snake on a face of the blade (side +1: +z, -1: -z), its belly on the face: the tail tip at `tail`,
    the body a wave to the head's back, the head straight to the snout at `snout` (x, y points)."""
    STRETCH = (0.2, 1.6)                                     # tails under the langets: 0.24 - 0.35 (smooth: no scales to squash)

    def __init__(self, P0, face, side, tail, snout, waves, amplitude, sigma_head, sigma_body):
        self.face, self.side = face, side
        self.tail_xy, self.snout_xy = np.asarray(tail, float), np.asarray(snout, float)
        self.waves, self.amplitude = waves, amplitude
        super().__init__(P0, sigma_head, sigma_body)

    def path(self):
        L = self.head_len
        xy = blade_path_xy(self.snout_xy, self.tail_xy, self.waves, self.amplitude, L)
        z = self.face(xy)
        base = np.column_stack([xy[:, 0], xy[:, 1], z])
        normal = np.repeat([[0.0, 0.0, float(self.side)]], len(base), 0)
        Q = offset_polyline(base, normal, self.h, 0.0)
        Q = smooth_after(Q, L * 0.95, 0.15)
        return Q, normal


_SOURCE = {}


def source(mods_dir, tess):
    """The rattlesnake (cached per tessellation level): original positions, then the tessellated positions,
    normals, tangents, bitangents, UVs, jaw weights and triangles."""
    if tess not in _SOURCE:
        if 'raw' not in _SOURCE:
            P, N, UV, T = load_snake(mods_dir)
            Tg, Bt = tangents(P, N, UV, T)
            _SOURCE['raw'] = (P, N, UV, T, Tg, Bt, lower_jaw(P, T))
        P, N, UV, T, Tg, Bt, w = _SOURCE['raw']
        C = np.zeros((len(P), 4), np.uint8)
        C[:, 0] = np.round(w * 255).astype(np.uint8)      # the jaw weight rides through the tessellation
        C[:, 3] = 255
        if tess > 1:
            P2, N2, Tg2, Bt2, UV2, C2, T2 = gamespine.tessellate(P, N, Tg, Bt, UV, C, T, n=tess)
        else:
            P2, N2, Tg2, Bt2, UV2, C2, T2 = P, N, Tg, Bt, UV, C, T
        _SOURCE[tess] = (P, P2, N2, Tg2, Bt2, UV2, C2[:, 0] / 255.0, T2)
    return _SOURCE[tess]


def build(mods_dir, make=None, tess=TESSELLATE, jaw_open=JAW_OPEN, h_fix=None):
    """A snake laid on the axe: positions, normals, tangents, bitangents, UVs, triangles (axe coordinates), plus the
    layout (for the ruby) and a summary. `make(P0)` builds the layout (default: the grip coil)."""
    P, P2, N2, Tg2, Bt2, UV2, w2, T2 = source(mods_dir, tess)
    w = _SOURCE['raw'][6]
    if make:
        lay = make(P)
    else:
        # the coil's belly line from the tilted head: the tilt swings the head's back and the neck's start toward the
        # belly (up to 1.8 snake units at the occiput), so measured on the closed mesh the neck sank into the grip. The
        # lower jaw stays shut for this (its dropped throat lay deeper than the neck's belly: the neck floated, and
        # the settle pulled a waist into it)
        Pr, Nr, _, _, Tgr, Btr, wr = _SOURCE['raw']
        lay = CoilLayout(open_jaw(Pr, Nr, Tgr, Btr, np.zeros_like(wr), jaw_open)[0], h_fix)
    Po, No, Tgo, Bto = open_jaw(P2, N2, Tg2, Bt2, w2, jaw_open)
    V = lay.map(Po)
    J = lay.jacobian(Po)
    Jinv_t = np.transpose(np.linalg.inv(J), (0, 2, 1))
    Nn = nz(np.einsum('nij,nj->ni', Jinv_t, No))
    Tn = nz(np.einsum('nij,nj->ni', J, Tgo))
    Bn = nz(np.einsum('nij,nj->ni', J, Bto))
    # orientation: the mapping keeps the winding, so the normals must still face the way the triangles do
    fn = np.cross(V[T2[:, 1]] - V[T2[:, 0]], V[T2[:, 2]] - V[T2[:, 0]])
    agree = (fn * (Nn[T2[:, 0]] + Nn[T2[:, 1]] + Nn[T2[:, 2]])).sum(1)
    assert (agree > 0).mean() > 0.97, (agree > 0).mean()
    info = dict(stretch=lay.stretch, L=lay.L, n_src=(len(P), len(_SOURCE['raw'][3])), jaw_verts=int(w.sum()), jaw=w2)
    return V, Nn, Tn, Bn, UV2, T2, lay, info


def mouth_axis(lay, inset):
    """The ruby's seat: the point on the mouth's bisector `inset` axe units inside the snout tip, and the
    direction out of the mouth (axe coordinates)."""
    tip = np.array([[CX, SNOUT_Y, HINGE[1]]])
    inner = np.array([[CX, SNOUT_Y - inset / SIGMA_HEAD, HINGE[1]]])
    a, b = lay.map(inner)[0], lay.map(tip)[0]
    return a, nz(b - a)
