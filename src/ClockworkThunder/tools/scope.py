"""Clockwork Thunder's ring scope (curator 2026-11-16: "add this style scope", Scoped Bows' Nordic bow).

Geometry: OutLaw666's Scoped Bows SE (Nexus 912; "You are allowed to use all of my assets in your own mods!"),
its Nordic bow's PRECISE scope: the rear ring `ring_2` with its rim `rim006:1`, knobs `bolts_1` and lens `part4`,
and the front reticle `ring`, `retfront`, `retfront_1`. Dropped: the two forward spikes `part4_3`/`part4_4`
(curator, side view), the reticle's own stem `part4_5` (a mount like the rear one instead) and the quick scope
(`ring_1` ...). Textures: none of theirs (the rings wore Dragonborn's Nordic textures, Bethesda DLC that Enderal
lacks): our own polished gold with a key (meander) band on the ring faces, the tube's glass on the lens, and an
emissive cyan effect shader on the reticle.

Placement (the mockup the curator approved, 2026-11-16): every part centred on the crosshair ray of the rifle's
corrected first-person aim (FlintlockOverhaul tools/06 output, read from Patch Collection), rear ring at root y
REAR_Y (over the breech), reticle SPACING further along the ray; the rear knobs rolled to 12/3/6/9 o'clock as
the aiming eye sees them, the reticle's ticks likewise; a tapered gold post from each ring's bottom into the
barrel top (curator: "needs a mount ... to attach to the barrel").

Root space (the nif as PyNifly reads it, the aim tool's frame): +Y forward, -Z up. The rifle build works in the
rifle shape's own space (Z forward, Y up); `to_shape` converts.
"""
import math
import os
import subprocess
import tempfile
import importlib.util

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

REAR_Y = 7.9          # root y of the rear ring (the sight line's rear point, the breech)
SPACING = 22.0        # rear ring -> reticle along the ray (the bow's own spacing)
REAR_PARTS = ('ring_2', 'rim006:1', 'bolts_1')
LENS_PART = 'part4'
FRONT_GOLD = ('ring',)
RETICLE_PARTS = ('retfront', 'retfront_1')
STEM_PART = 'part4_5'          # used to square the reticle, then dropped (a mount instead)
SCOPED_BOWS_ARCHIVE = 'Scoped Bows SE 1.3.1-912-1-3-1.7z'
SCOPED_BOWS_NIF = '01.DATA/meshes/weapons/scoped bows/nordic/nordicbow.nif'
SEVEN_ZIP = r'C:\Program Files\7-Zip\7z.exe'
REAR_MOUNT = (0.9, 1.4, 0.8)      # top width, base width, depth along the gun (root units)
FRONT_MOUNT = (0.5, 0.8, 0.5)
MOUNT_INTO_RING = 0.15
MOUNT_INTO_BARREL = 0.25
KEY_REPEATS_REAR = 12             # meander units round the rear ring face
KEY_REPEATS_FRONT = 6
TEX_W, TEX_H = 2048, 512          # top half: the key band; bottom half: plain gold
RETICLE_EMISSIVE = (0.35, 0.95, 1.0, 1.0)


def scoped_bows_nif(downloads, tmpdir):
    """The Nordic scoped bow mesh, extracted from the curator's download (never committed)."""
    arc = os.path.join(downloads, SCOPED_BOWS_ARCHIVE)
    assert os.path.isfile(arc), 'Scoped Bows SE download missing: %s' % arc
    subprocess.run([SEVEN_ZIP, 'x', '-y', '-o' + tmpdir, arc, SCOPED_BOWS_NIF.replace('/', os.sep)],
                   check=True, stdout=subprocess.DEVNULL)
    p = os.path.join(tmpdir, *SCOPED_BOWS_NIF.split('/'))
    assert os.path.isfile(p), p
    return p


def read_parts(NifFile, path):
    """name -> (V, N, T) in the bow's root space."""
    out = {}
    for s in NifFile(path).shapes:
        V = np.array(s.verts, float)
        N = np.array(s.normals, float) if s.normals else np.zeros_like(V)
        xf = s.transform
        R = np.array(xf.rotation.matrix if hasattr(xf.rotation, 'matrix') else xf.rotation, float).reshape(3, 3)
        if not s.has_skin_instance:
            V = (V @ R.T) * xf.scale + np.array(xf.translation)
            N = N @ R.T
        out[s.name] = (V, N, np.array(s.tris, int))
    for k in REAR_PARTS + (LENS_PART,) + FRONT_GOLD + RETICLE_PARTS + (STEM_PART,):
        assert k in out, ('Scoped Bows nordic mesh changed: no %s' % k, sorted(out))
    return out


def crosshair_ray(ads_tool, patch_collection, data_dir):
    """Eye, direction and the mesh->camera matrix of the rifle's corrected first-person hold (root space)."""
    spec = importlib.util.spec_from_file_location('ads', ads_tool)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    bsa = m._bsa.listing(os.path.join(data_dir, 'Skyrim - Animations.bsa'))
    fd, tmp = tempfile.mkstemp(suffix='.hkx')
    os.close(fd)
    with open(tmp, 'wb') as fh:
        fh.write(m._bsa.read(bsa[0], bsa[1][m.SKELETON]))
    rig = m.Rig(m.anim_skyrim.load_skyrim_skeleton(tmp))
    os.remove(tmp)
    clip = os.path.join(patch_collection, *m.ANIMS_1P, 'OpenAnimationReplacer', m.MOD, 'ADS ol_musket_rifle', 'dlc01',
                        'crossbow_idledrawn.hkx')
    assert os.path.isfile(clip), 'run FlintlockOverhaul tools/06 first (no %s)' % clip
    cam = rig.weapon_in_camera(m.anim_skyrim.load_skyrim_animation(clip), 0)
    inv = np.linalg.inv(cam)
    eye = (inv @ np.r_[0, 0, 0, 1.0])[:3]
    d = inv[:3, :3] @ np.array([0, 1.0, 0])
    return eye, d / np.linalg.norm(d), cam


def _axis_rot(k, deg):
    th = math.radians(deg)
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return math.cos(th) * np.eye(3) + math.sin(th) * K + (1 - math.cos(th)) * np.outer(k, k)


def _clock(cam, V, c):
    d = (np.c_[V - c, np.zeros(len(V))] @ cam.T)[:, :3]
    return np.degrees(np.arctan2(d[:, 0], d[:, 2])) % 360


def _grid_offset(angles, fold):
    return float(np.degrees(np.angle(np.mean(np.exp(1j * fold * np.radians(angles))))) / fold)


def place(parts, eye, ray, cam):
    """Root-space geometry of every kept part: name -> (V, N, T); and the two ring centres + the ray's up."""
    B2R = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]], float)     # bow X (aim), Y, Z -> rifle Y, -X, Z
    up = np.array([0, 0, -1.0]) - ray * (-ray[2])
    up /= np.linalg.norm(up)
    right = np.cross(ray, -up)
    align = np.c_[right, ray, -up]

    def at(y):
        return eye + (y - eye[1]) / ray[1] * ray

    def put(names, centre_part, c_root):
        rv = parts[centre_part][0]
        c = (rv.min(0) + rv.max(0)) / 2
        M = align @ B2R
        return {n: ((parts[n][0] - c) @ M.T + c_root, parts[n][1] @ M.T, parts[n][2]) for n in names}, c_root

    rear, rc = put(REAR_PARTS + (LENS_PART,), 'ring_2', at(REAR_Y))
    front, fc = put(FRONT_GOLD + RETICLE_PARTS + (STEM_PART,), 'retfront_1', at(REAR_Y + SPACING))
    rad = parts['ring_2'][0]
    r_rear = float((rad.max(0) - rad.min(0))[1:].max()) / 2
    rad = parts['ring'][0]
    r_front = float((rad.max(0) - rad.min(0))[1:].max()) / 2

    def roll(group, c, names_for_angle, fold):
        a = np.concatenate([_clock(cam, group[n][0], c) for n in names_for_angle])
        off = _grid_offset(a, fold)
        for sgn in (1, -1):
            R = _axis_rot(ray, sgn * off)
            test = np.concatenate([_clock(cam, (group[n][0] - c) @ R.T + c, c) for n in names_for_angle])
            if abs(_grid_offset(test, fold)) < 0.5:
                return {n: ((V - c) @ R.T + c, N @ R.T, T) for n, (V, N, T) in group.items()}, off
        raise SystemExit('scope: roll did not square up')
    rear, r_off = roll(rear, rc, ('bolts_1',), 4)
    # the reticle: its own stem (dropped below) turned straight down, as in the approved mockup
    sa = float(np.degrees(np.angle(np.mean(np.exp(1j * np.radians(_clock(cam, front[STEM_PART][0], fc)))))))
    f_off = None
    for sgn in (1, -1):
        Rf = _axis_rot(ray, sgn * (180.0 - sa))
        t2 = (front[STEM_PART][0] - fc) @ Rf.T + fc
        a2 = float(np.degrees(np.angle(np.mean(np.exp(1j * np.radians(_clock(cam, t2, fc)))))))
        if abs(((a2 - 180.0) + 180.0) % 360.0 - 180.0) < 1.0:
            front = {n: ((V - fc) @ Rf.T + fc, N @ Rf.T, T) for n, (V, N, T) in front.items()}
            f_off = 180.0 - sa
            break
    assert f_off is not None, 'scope: reticle roll'
    del front[STEM_PART]
    print('scope: rear ring at root y %.2f (%.2f, %.2f), knobs rolled %.1f deg to 12/3/6/9; reticle %.1f further, '
          'its stem squared to 6 o clock (rolled %.1f deg); ring radii %.2f / %.2f' % (REAR_Y, rc[0], rc[2], r_off, SPACING, f_off, r_rear, r_front))
    rear.update(front)
    return rear, rc, fc, up, r_rear, r_front


def to_shape(V, R, t, s):
    """Root space -> the rifle shape's own space (its transform R, t, s)."""
    return ((V - t) @ R) / s


def mount(c_shape, ring_bottom_y, barrel_top_y, top_w, base_w, depth):
    """Tapered post in shape space (Y up): from inside the ring's bottom into the barrel top. Box UVs."""
    top, bot = ring_bottom_y + MOUNT_INTO_RING, barrel_top_y - MOUNT_INTO_BARREL
    assert top > bot, ('mount', top, bot)
    corners = []
    for y, w, dd in ((top, top_w, depth), (bot, base_w, depth * 1.4)):
        for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            corners.append((c_shape[0] + sx * w / 2, y, c_shape[2] + sz * dd / 2))
    C = np.array(corners)
    V, N, T, UV = [], [], [], []
    for q in ((0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7), (3, 2, 1, 0)):
        P = C[list(q)]
        n = np.cross(P[1] - P[0], P[3] - P[0])
        n /= np.linalg.norm(n)
        if n @ (P.mean(0) - C.mean(0)) < 0:
            n = -n
        b = len(V)
        for k, p in enumerate(P):
            V.append(p)
            N.append(n)
            UV.append((0.1 + 0.3 * (k in (1, 2)), 0.6 + 0.3 * (k in (2, 3))))
        T += [(b, b + 1, b + 2), (b, b + 2, b + 3)] if np.cross(P[1] - P[0], P[2] - P[0]) @ n > 0 else \
             [(b, b + 2, b + 1), (b, b + 3, b + 2)]
    print('scope mount: %.2f tall (ring bottom %.2f, barrel top %.2f)' % (top - bot, ring_bottom_y, barrel_top_y))
    return np.array(V), np.array(N), np.array(T), np.array(UV)


def ring_uvs(V, N, T, centre, axis, repeats):
    """Unwelded triangles with UVs: faces looking along the axis get the key band (u round the ring, v across its
    width), the rest plain gold. Returns V, N, T, UV."""
    e1 = np.cross(axis, [0, 1.0, 0] if abs(axis[1]) < 0.9 else [1.0, 0, 0])
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(axis, e1)
    rel = V - centre
    rad = np.linalg.norm(rel - np.outer(rel @ axis, axis), axis=1)
    ang = (np.arctan2(rel @ e2, rel @ e1) / (2 * math.pi)) % 1.0
    face = np.abs(N @ axis) > 0.6
    rin, rout = rad[face].min() if face.any() else 0, rad[face].max() if face.any() else 1
    OV, ON, OT, OUV = [], [], [], []
    for tri in T:
        u = ang[tri] * repeats
        if u.max() - u.min() > repeats / 2:
            u = np.where(u < repeats / 2, u + repeats, u)
        on_face = face[tri].all()
        b = len(OV)
        for k, i in enumerate(tri):
            OV.append(V[i])
            ON.append(N[i])
            if on_face:
                OUV.append((u[k], 0.03 + 0.44 * (rad[i] - rin) / max(rout - rin, 1e-6)))
            else:
                OUV.append((u[k] * 0.25, 0.75))
        OT.append((b, b + 1, b + 2))
    return np.array(OV), np.array(ON), np.array(OT), np.array(OUV)


def key_band_texture():
    """(rgb HxWx3, metal HxW, normal HxWx4): a meander (Greek key) band on the top half, plain gold below. Our
    own drawing; heights -> normals; the gold itself comes from polished_gold."""
    unit = TEX_H // 2                       # one key unit is as wide as the band is tall
    SS = 4
    hi = Image.new('L', (TEX_W * SS, TEX_H * SS), 0)
    d = ImageDraw.Draw(hi)
    U = unit * SS / 10.0                    # the unit drawn on a 10 x 10 grid
    lw = int(0.9 * U)
    for k in range(TEX_W // unit):
        x0 = k * unit * SS

        def P(x, y):
            return (x0 + x * U, y * U)
        path = [P(0, 8.2), P(8.2, 8.2), P(8.2, 1.8), P(1.8, 1.8), P(1.8, 5.8), P(5.6, 5.8), P(5.6, 4.0), P(4.0, 4.0)]
        d.line(path, fill=255, width=lw, joint='curve')
        d.line([P(8.2, 8.2), P(10.0, 8.2)], fill=255, width=lw)
        d.line([P(0, 0.5), P(10.0, 0.5)], fill=255, width=lw)
        d.line([P(0, 9.5), P(10.0, 9.5)], fill=255, width=lw)
    band = np.asarray(hi.resize((TEX_W, TEX_H), Image.LANCZOS), np.float32) / 255.0
    band[TEX_H // 2:] = 0.55                 # plain lower half: no relief
    h = np.asarray(Image.fromarray((band * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.0)),
                   np.float32) / 255.0
    gy, gx = np.gradient(h)
    strength = 6.0
    n = np.stack([-gx * strength, gy * strength, np.ones_like(h)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    normal = np.concatenate([n * 0.5 + 0.5, np.ones(h.shape + (1,), np.float32)], -1)
    lum = 0.35 + 0.55 * h                    # raised key bright, recesses darker
    lum[TEX_H // 2:] = 0.75
    rgb = np.repeat(lum[..., None], 3, -1)
    return rgb, np.ones(h.shape, np.float32), normal


def build(parts, eye, ray, cam, R, t, s, barrel_top):
    """All scope geometry in the rifle shape's space: (gold V, N, T, UV), (lens ...), (reticle ...).
    barrel_top(x, z) -> the barrel's top y (shape space) under a point."""
    placed, rc, fc, up, r_rear, r_front = place(parts, eye, ray, cam)
    axis_s = (ray @ R) / np.linalg.norm(ray @ R)

    def S(V):
        return to_shape(V, R, t, s)

    def SN(N):
        n = N @ R
        return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
    gold, lens, ret = [], None, []
    for name, (V, N, T) in placed.items():
        Vs, Ns = S(V), SN(N)
        if name == LENS_PART:
            lens = (Vs, Ns, T, np.c_[0.5 + 0.1 * Vs[:, 0], 0.5 + 0.1 * Vs[:, 1]])
        elif name in RETICLE_PARTS:
            ret.append((Vs, Ns, T, np.c_[0.5 + 0.1 * Vs[:, 0], 0.5 + 0.1 * Vs[:, 1]]))
        else:
            c = S(rc[None])[0] if name in REAR_PARTS else S(fc[None])[0]
            reps = KEY_REPEATS_REAR if name in REAR_PARTS else KEY_REPEATS_FRONT
            if name in ('ring_2', 'ring'):
                gold.append(ring_uvs(Vs, Ns, T, c, axis_s, reps))
            else:
                gold.append((Vs, Ns, T, np.c_[0.1 + 0.2 * Vs[:, 2] % 1, np.full(len(Vs), 0.8)]))
    for name, c_root, ring_name, (tw, bw, dp) in (('rear', rc, 'ring_2', REAR_MOUNT),
                                                  ('front', fc, 'ring', FRONT_MOUNT)):
        cs = S(c_root[None])[0]
        rv = S(placed[ring_name][0])
        under = rv[(np.abs(rv[:, 0] - cs[0]) < 0.4) & (rv[:, 1] < cs[1])]
        ring_bottom = float(under[:, 1].min())
        gold.append(mount(cs, ring_bottom, barrel_top(cs[0], cs[2]), tw * 1 / s, bw / s, dp / s))
    def merge(items):
        V = np.concatenate([i[0] for i in items])
        N = np.concatenate([i[1] for i in items])
        UV = np.concatenate([i[3] for i in items])
        T, off = [], 0
        for i in items:
            T.append(i[2] + off)
            off += len(i[0])
        return V, N, np.concatenate(T), UV
    return merge(gold), lens, merge(ret)
