"""Rebuild the `Zenderal - Musket Aim Fix` MO2 mod: first-person aim-down-sights for Ordo Legionis' 14 muskets.

v5 (2026-11-01, ADS). Measured on the vanilla first-person skeleton (`Camera1st [Cam1]` is the view: +Y
forward, +Z up; calibrated on the vanilla crossbow under Crosshair-aligned Crossbow's pose, whose bolt tip lands
0.1 deg / -1.8 deg off the crosshair):
  - DAR Rifles' bolt-action set (432101, which the _KID.ini puts on the muskets, see 05-dar-rifles.py) holds every
    musket rolled ~15.5 deg, with the front sight 2.5-7 deg below and up to 5 deg beside the crosshair.
  - Ordo's meshes are not straight: each barrel sits -4.7..+0.4 deg (yaw) and 0..5 deg (tilt) off its own mesh
    axis, differently per mesh. No single hold clip can line them all up.
So each mesh gets its own clips. Its sight line (rear: top of the barrel at the breech, front: the front-sight
tip) is read from the winning mesh, and one rigid correction is solved that puts the front sight SIGHT_DROP_DEG
below the crosshair (the dot rests just above the muzzle) and the rear sight EYE_HEIGHT below the eye (you look
down the barrel, as over a real musket), upright, keeping
the breech's distance from the eye. Nothing on the gun may rise into the line of sight. The correction is written
into ONE track, `NPC Spine2 [Spn2]` (parent of both clavicles): both arms and the gun move together, so the grip
is unchanged, and the camera (a child of the root) does not move. It is applied in the camera's frame on every
frame of the hold, the shot (release) and the reload, so recoil and reload keep their motion and every hand-off
between them stays as seamless as DAR made it (its reload starts and ends at the hold).

The raise (CrossBow_Aim) is synthesised as in v4: the first-person 1hm_behavior clip generator `CrossBow Aim`
fires a TRIGGER `bowDrawn` at 0.200 s and CrossBowDrawing -> CrossBow_IdleDrawn takes it with
fastBlendTransition, so the raise is cut at 0.2 s whatever its length (v3 learned that). It is exactly 0.2 s:
vanilla's raise frame 0 (~ the hip pose) smoothstep-eased into the corrected hold, vanilla's annotations kept.
History: v1 shipped DAR's parked raise clips (byte-identical to vanilla); v2 used the hold as the raise (gap moved
into the blend); v3 a 0.5 s raise (cut at bowDrawn); v4 the 0.2 s raise into DAR's uncorrected hold, behind one
keyword submod. v5 replaces that submod.

Per mesh, two OAR submods keyed on the WEAPs that use it (IsEquipped, right hand):
  `ADS <mesh>`                       432400+i: raise, hold, shot, reload (+ dwarven and sneak variants)
  `ADS <mesh>, both reload perks`    432450+i: the corrected reload retimed exactly like Quick Reload Stack
                                     (src/Prophecy/tools/04, imported), so both perks still stack. Its own
                                     musket submod (432301) is now shadowed for these 14 muskets.
DAR ships no first-person sneak reload; vanilla's (the hip pose) still plays there, as before.

Inputs: the winning loose musket meshes (active MO2 profile order), the 1st-person skeleton and vanilla raise
clips from the user's `Skyrim - Animations.bsa`, DAR's clips from its install, the WEAP/STAT records from
reference/mods/OrdoEnderal. HKX via PyNifly's anim_skyrim, NIF via PyNifly. Nothing third-party is committed.
Every written clip is decoded again and re-measured: the build fails unless each musket comes out upright with
both sights on the crosshair and nothing on the gun rising into the line of sight.

Rerun after DAR Rifles, Ordo Legionis, PG Patcher Output or Quick Reload Stack (STACK_FACTOR) changes.

Usage:  python src/FlintlockOverhaul/tools/06-build-musket-aim-fix.py [<modlist root>]   (needs numpy)
"""
import glob
import importlib.util
import json
import math
import os
import re
import shutil
import sys

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
TOOLS = json.load(open(os.path.join(ROOT, '.claude', 'config', 'tools.json'), encoding='utf-8-sig'))
sys.path.insert(0, os.path.join(TOOLS['pynifly'], 'hkx'))
sys.path.insert(0, TOOLS['pynifly'])
import anim_skyrim  # noqa: E402  (PyNifly, no Blender dependency)
from pyn.pynifly import NifFile  # noqa: E402


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


QRS = _load('qrs', os.path.join(ROOT, 'src', 'Prophecy', 'tools', '04-build-quick-reload-stack.py'))
_bsa = QRS._bsa

MOD = 'Zenderal - Musket Aim Fix'
ORDO = 'OrdoLegionisMuskets.esp'
REF = os.path.join(ROOT, 'reference', 'mods', 'OrdoEnderal')
ANIMS_1P = ['meshes', 'actors', 'character', '_1stperson', 'animations']
DAR = ANIMS_1P + ['DynamicAnimationReplacer', '_CustomConditions', '432101', 'dlc01']
OAR = ANIMS_1P + ['OpenAnimationReplacer', MOD]
VANILLA = 'meshes\\actors\\character\\_1stperson\\animations\\dlc01\\'
SKELETON = 'meshes\\actors\\character\\_1stperson\\characterassets\\skeletonfirst.hkx'
PRIORITY = 432400          # above DAR Rifles' 432101-432103 and Quick Reload Stack's 432300/432301
PRIORITY_QUICK = 432450    # above PRIORITY, so both perks pick the retimed reload
FPS = 30
BOW_DRAWN_AT = 0.2         # 1st-person 1hm_behavior: `CrossBow Aim` (and Sneak/Dwarven) trigger bowDrawn@0.200
MESH_UP = np.array([0.0, 0.0, -1.0])  # weapon meshes are built upside down: their up is -Z (forward +Y)
EYE_HEIGHT = 3.0           # the eye this far above the rear sight (game units): you look down the barrel to the
                           # front sight. 0 = eye on the sight line: the breech then hides the barrel (rendered
                           # 2026-11-01: 1.5 still crowded, 3.0 clean, 4.5 looks over the gun)
SIGHT_DROP_DEG = 1.0       # the front-sight tip this far below the crosshair, so the crosshair dot sits in clear air
                           # just above the muzzle (6 o'clock hold) where the ball goes. At 0 the dot covered the
                           # muzzle in game (2026-11-01 screenshot: dot radius ~0.2 deg, muzzle top ~0.4 deg above
                           # the dot's centre: an in-game offset this model doesn't capture, so keep the margin)
NEAR = 1.0                 # line-of-sight check starts here: Improved Camera's 1st-person combat near distance is
                           # 15 (Zenderal.ini [NEARDISTANCE]), but whether it clips the weapon pass is unverified
BREECH_BACK = 15.0         # first pass: how far behind the rear sight the clearance check looks; the second pass
                           # looks all the way back to the eye
# family -> (DAR hold clip the correction is solved on, clips it applies to). Dwarven clips are DAR's copies.
FAMILIES = {
    'stand': ('crossbow_idledrawn.hkx',
              ['crossbow_idledrawn.hkx', 'crossbow_idledrawndwarven.hkx', 'crossbow_release.hkx',
               'crossbow_releasedwarven.hkx', 'crossbow_reload.hkx', 'crossbow_reloaddwarven.hkx']),
    'sneak': ('sneakcrossbow_idledrawn.hkx',
              ['sneakcrossbow_idledrawn.hkx', 'sneakcrossbow_idledrawndwarven.hkx', 'sneakcrossbow_release.hkx',
               'sneakcrossbow_releasedwarven.hkx']),
}
# raise clip -> the corrected hold it must end on (vanilla's clip of the same name gives the start + annotations)
RAISES = {
    'crossbow_aim.hkx': 'crossbow_idledrawn.hkx',
    'crossbow_aimdwarven.hkx': 'crossbow_idledrawndwarven.hkx',
    'sneakcrossbow_aim.hkx': 'sneakcrossbow_idledrawn.hkx',
    'sneakcrossbow_aimdwarven.hkx': 'sneakcrossbow_idledrawndwarven.hkx',
}
QUICK = ['crossbow_reload.hkx', 'crossbow_reloaddwarven.hkx']
# DAR's shot clips kick the first-person camera node and the arms 2.9 deg up AT the shot (frame 4, `arrowRelease`
# 0.133 s), and the camera follows (recording 2026-11-01: up ~2 deg within 33 ms). Hit Where You Aim sets the ball's
# angle one game frame after the launch, along the camera ray of that frame (traced: camera already 0.40 deg up,
# ball 0.32 deg above the view the shot was fired from, +12..+17 units high at 2200-2700 units; third person, with
# no kick, was within 0.05 deg). So every bone of the shot clip holds its pre-shot pose until this long after
# `arrowRelease`: two game frames at 30 fps. The recoil then plays unchanged, just later.
REST_AFTER_SHOT = 0.067


# ---- small maths ---------------------------------------------------------------------------------------------

def quat_mat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def mat_quat(m):
    t = m[0, 0] + m[1, 1] + m[2, 2]
    if t > 0:
        s = math.sqrt(t + 1.0) * 2
        q = [(m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s, 0.25 * s]
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2
        q = [0.25 * s, (m[0, 1] + m[1, 0]) / s, (m[0, 2] + m[2, 0]) / s, (m[2, 1] - m[1, 2]) / s]
    elif m[1, 1] > m[2, 2]:
        s = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2
        q = [(m[0, 1] + m[1, 0]) / s, 0.25 * s, (m[1, 2] + m[2, 1]) / s, (m[0, 2] - m[2, 0]) / s]
    else:
        s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2
        q = [(m[0, 2] + m[2, 0]) / s, (m[1, 2] + m[2, 1]) / s, 0.25 * s, (m[1, 0] - m[0, 1]) / s]
    n = math.sqrt(sum(c * c for c in q))
    return [c / n for c in q]


def trs(t, q, s):
    m = np.eye(4)
    m[:3, :3] = quat_mat(q) * s
    m[:3, 3] = t
    return m


def unit(v):
    return v / np.linalg.norm(v)


def angle_deg(m):
    return math.degrees(math.acos(max(-1.0, min(1.0, (np.trace(m[:3, :3]) - 1) / 2))))


# ---- skeleton and poses ----------------------------------------------------------------------------------------

class Rig:
    def __init__(self, skeleton):
        self.parents = skeleton.parents
        self.index = {n: i for i, n in enumerate(skeleton.bones)}
        self.cam = self.index['Camera1st [Cam1]']
        self.weapon = self.index['Weapon']
        self.spine2 = self.index['NPC Spine2 [Spn2]']
        self.spine1 = self.index['NPC Spine1 [Spn1]']
        self.look = self.index['NPC LookNode [Look]']
        # attachment bones a musket never shows (AnimObjectR sits 180 deg apart between vanilla and DAR)
        self.anim_objects = {i for n, i in self.index.items() if n.startswith('AnimObject')}
        assert self.parents[self.spine2] == self.spine1 and self.parents[self.cam] == 0, 'unexpected 1P skeleton'

    def world(self, anim, f):
        if len(anim.tracks) != len(self.parents):
            sys.exit('clip has %d tracks, skeleton %d bones' % (len(anim.tracks), len(self.parents)))
        out = [None] * len(self.parents)
        for i, p in enumerate(self.parents):
            t = anim.tracks[i]
            local = trs(t.translations[f], t.rotations[f], t.scales[f][0])
            out[i] = local if p < 0 else out[p] @ local
        return out

    def weapon_in_camera(self, anim, f):
        w = self.world(anim, f)
        return np.linalg.inv(w[self.cam]) @ w[self.weapon]


def check_finite(anim, name):
    for i, tr in enumerate(anim.tracks):
        for seq in (tr.translations, tr.rotations, tr.scales):
            if any(math.isnan(x) for v in seq for x in v):
                sys.exit('%s: NaN in track %d' % (name, i))


# ---- meshes and sight lines ------------------------------------------------------------------------------------

def mesh_surface(path, density=6.0):
    """Points sampled over every unskinned triangle (long barrel triangles have vertices only at their ends),
    in the nif root's frame = the Weapon node's frame. Skinned shapes are the moving lock parts; left out."""
    nif = NifFile(path)
    pts, rng = [], np.random.default_rng(1)
    for s in nif.shapes:
        if s.has_skin_instance:
            continue
        chain, p = [s], s.parent
        while p is not None:
            chain.append(p)
            p = p.parent
        v = np.array(s.verts, dtype=float)
        for obj in chain:
            t = obj.transform
            v = v @ np.array(t.rotation, dtype=float).T * t.scale + np.array(t.translation, dtype=float)
        for a, b, c in (v[list(t)] for t in s.tris):
            n = int(np.linalg.norm(np.cross(b - a, c - a)) / 2 * density) + 1
            u = rng.random((n, 2))
            m = u.sum(1) > 1
            u[m] = 1 - u[m]
            pts.append(a + u[:, :1] * (b - a) + u[:, 1:] * (c - a))
        pts.append(v)
    if not pts:
        sys.exit('%s: no unskinned shapes' % path)
    return np.vstack(pts)


def robust_line(y, v, tol=0.25):
    keep = np.ones(len(y), bool)
    for _ in range(8):
        k, b = np.polyfit(y[keep], v[keep], 1)
        r = np.abs(v - (k * y + b))
        new = r < max(tol, 2.5 * float(np.median(r[keep])))
        if new.sum() < 4 or (new == keep).all():
            break
        keep = new
    return k, b, keep


def sight_line(V, back=BREECH_BACK):
    """(rear, front) of the sight line in mesh space (+Y forward, -Z up). Nothing between `back` units behind the
    rear sight and the front sight may rise above it."""
    ymax, ymin = V[:, 1].max(), V[:, 1].min()
    length = ymax - ymin
    ring = V[V[:, 1] > ymax - 0.6]                          # the muzzle face
    r = (ring[:, 2].max() - ring[:, 2].min()) / 2
    w = ring[:, 0].max() - ring[:, 0].min()
    cx = (ring[:, 0].max() + ring[:, 0].min()) / 2
    rows, y = [], ymax - 1.0
    while y > ymax - 0.62 * length:                        # walk back along the barrel, 1-unit slabs
        s = V[(V[:, 1] > y - 0.5) & (V[:, 1] <= y + 0.5) & (np.abs(V[:, 0] - cx) < w / 2 + 1.5)]
        if len(s) >= 4:
            top = s[:, 2].min()
            upper = s[s[:, 2] < top + 0.5 * r]             # the barrel's upper half: stock edges sit lower
            cx = (upper[:, 0].max() + upper[:, 0].min()) / 2
            rows.append((y, cx, top))
        y -= 1.0
    rows = np.array(rows)
    if len(rows) < 8:
        sys.exit('barrel not found (%d slabs)' % len(rows))
    kx, bx, _ = robust_line(rows[:, 0], rows[:, 1])
    kt, bt, keep = robust_line(rows[:, 0], rows[:, 2])
    yr = rows[keep, 0].min()
    centre = lambda yy: kx * yy + bx  # noqa: E731
    near_muzzle = V[(V[:, 1] > ymax - 10) & (np.abs(V[:, 0] - centre(V[:, 1])) < r)]
    i = int(np.argmin(near_muzzle[:, 2] - (kt * near_muzzle[:, 1] + bt)))
    tip = near_muzzle[i]
    blade = (kt * tip[1] + bt) - tip[2]                    # front sight height over the barrel top
    front = tip if blade > 0.15 else np.array([centre(ymax), ymax, kt * ymax + bt])
    # Nothing over the barrel between the breech and the front sight may rise into the line: raise the rear end
    # of the line (height = -z) until it clears every such point (rear sight blocks, breech plugs, tangs).
    win = V[(V[:, 1] >= yr - back) & (V[:, 1] < front[1] - 1.0)
            & (np.abs(V[:, 0] - centre(V[:, 1])) < 0.8 * r)]
    h_front = -front[2]
    slope = (h_front + (kt * yr + bt)) / (front[1] - yr)
    if len(win):
        slope = min(slope, float(((h_front + win[:, 2]) / (front[1] - win[:, 1])).min()))
    rear = np.array([centre(yr), yr, -(h_front - slope * (front[1] - yr))])
    return rear, front, float(blade)


# ---- correction ------------------------------------------------------------------------------------------------

def solve_correction(rig, hold, rear, front):
    """Rigid transform in the camera frame that puts the front sight SIGHT_DROP_DEG below the crosshair and the rear
    sight EYE_HEIGHT below the eye, upright, keeping the rear sight's forward distance."""
    cam = rig.weapon_in_camera(hold, 0)
    rc = (cam @ np.r_[rear, 1])[:3]
    fc = (cam @ np.r_[front, 1])[:3]
    length = float(np.linalg.norm(fc - rc))
    a = (fc - rc) / length
    u = cam[:3, :3] @ MESH_UP
    u = unit(u - a * (u @ a))
    current = np.c_[np.cross(a, u), a, u]                 # columns: right, forward, up of the gun
    rear_t = np.array([0.0, rc[1], -EYE_HEIGHT])
    # front on the ray (0, y, -y tan(drop)) at `length` from the rear: (1+t^2)y^2 - 2(d + h t)y + d^2 + h^2 - L^2 = 0
    t, d, h = math.tan(math.radians(SIGHT_DROP_DEG)), rc[1], EYE_HEIGHT
    qa, qb, qc = 1 + t * t, -2 * (d + h * t), d * d + h * h - length * length
    y = (-qb + math.sqrt(qb * qb - 4 * qa * qc)) / (2 * qa)
    fwd = (np.array([0.0, y, -y * t]) - rear_t) / length
    target = np.c_[[1.0, 0, 0], fwd, [0, -fwd[2], fwd[1]]]
    rot = target @ current.T
    c = np.eye(4)
    c[:3, :3] = rot
    c[:3, 3] = rear_t - rot @ rc
    return c


def apply_correction(rig, anim, c):
    """Write c (camera frame) into the Spine2 track of every frame."""
    tr = anim.tracks[rig.spine2]
    for f in range(anim.num_frames):
        w = rig.world(anim, f)
        cam = w[rig.cam]
        new_world = cam @ c @ np.linalg.inv(cam) @ w[rig.spine2]
        local = np.linalg.inv(w[rig.spine1]) @ new_world
        s = float(np.linalg.norm(local[:3, 0]))
        if abs(s - tr.scales[f][0]) > 1e-3:
            sys.exit('Spine2 scale changed (%.4f vs %.4f)' % (s, tr.scales[f][0]))
        q = mat_quat(local[:3, :3] / s)
        if sum(x * y for x, y in zip(q, tr.rotations[f])) < 0:
            q = [-x for x in q]                           # same hemisphere as the source: smooth splines
        tr.rotations[f] = q
        tr.translations[f] = [float(x) for x in local[:3, 3]]
    return anim  # same frames and duration: the source's block header stays as it is


def delay_recoil(rig, anim, name):
    """Shot clips only: hold the pose before the kick until REST_AFTER_SHOT after `arrowRelease`. The kick is the first
    frame where the camera node or the LookNode (the parent of the arms) turns; every track is shifted later by
    whole frames (the last frames drop off; timing and annotations stay). Returns the shift."""
    shot = [a.time for a in anim.annotations if a.text == 'arrowRelease']
    if 'release' not in name or not shot:
        return 0
    kick_tracks = [anim.tracks[rig.cam], anim.tracks[rig.look]]
    first_motion = next((f for f in range(1, anim.num_frames)
                         if max(math.degrees(2 * math.acos(min(1.0, abs(sum(x * y for x, y in zip(t.rotations[f], t.rotations[0]))))))
                                for t in kick_tracks) > 0.05), anim.num_frames)
    # the pose is still frame 0 up to frame first_motion - 1; it must stay there until rest_until
    rest_until = shot[0] + REST_AFTER_SHOT
    shift = max(0, math.ceil(rest_until / anim.frame_duration - 1e-6) - (first_motion - 1))
    for t in anim.tracks:
        for seq in ('translations', 'rotations', 'scales'):
            v = getattr(t, seq)
            setattr(t, seq, [v[max(0, f - shift)] for f in range(anim.num_frames)])
    print('  %-30s shot at %.3f s, first motion at frame %d (%.3f s): recoil held %d frames, to %.3f s'
          % (name, shot[0], first_motion, first_motion * anim.frame_duration, shift,
             (first_motion + shift) * anim.frame_duration))
    return shift


def havok_blocks(anim):
    """Havok's own block header. Zeroing it lets PyNifly write blockDuration = clip length, which Havok's spline
    decompressor uses to find frames (LoopPistolAnims v12 found the legs sampling wrong frames that way)."""
    fpb = anim.max_frames_per_block or 256
    anim.max_frames_per_block = fpb
    anim.num_blocks = max(1, (anim.num_frames + fpb - 1) // fpb)
    anim.block_duration = (fpb - 1) * anim.frame_duration
    return anim


def check_blocks(path):
    a = anim_skyrim.load_skyrim_animation(path)
    if abs(a.block_duration - (a.max_frames_per_block - 1) * a.frame_duration) > 1e-3:
        sys.exit('%s: blockDuration %.4f is not Havok\'s (%d - 1) x %.5f' % (path, a.block_duration,
                                                                             a.max_frames_per_block, a.frame_duration))


def measure(rig, anim, rear, front, V, f=0):
    """Angles of both sights from the crosshair, the gun's roll, and points rising into the line of sight (the
    view axis, eye to front sight)."""
    cam = rig.weapon_in_camera(anim, f)
    rc = (cam @ np.r_[rear, 1])[:3]
    fc = (cam @ np.r_[front, 1])[:3]
    ang = lambda p: (math.degrees(math.atan2(p[0], p[1])), math.degrees(math.atan2(p[2], p[1])))  # noqa: E731
    a = unit(fc - rc)
    u = cam[:3, :3] @ MESH_UP
    u = unit(u - a * (u @ a))
    up = unit(np.array([0.0, 0, 1]) - a * a[2])
    roll = math.degrees(math.atan2(np.cross(up, u) @ a, up @ u))
    pc = (cam @ np.c_[V, np.ones(len(V))].T).T[:, :3]
    pc = pc[(pc[:, 1] > NEAR) & (pc[:, 1] < fc[1] - 1.0)]
    off = np.degrees(np.arctan2(np.hypot(pc[:, 0], pc[:, 2]), pc[:, 1]))
    blocking = int(((off < 0.75) & (pc[:, 2] > 0.05)).sum())
    return ang(rc), ang(fc), roll, blocking, float(rc[1]), float(fc[1])


# ---- raise (v4's synthesis) ------------------------------------------------------------------------------------

def slerp(a, b, t):
    d = sum(x * y for x, y in zip(a, b))
    if d < 0:
        b, d = [-x for x in b], -d
    if d > 0.9995:
        q = [x + (y - x) * t for x, y in zip(a, b)]
    else:
        th = math.acos(d)
        s = math.sin(th)
        wa, wb = math.sin((1 - t) * th) / s, math.sin(t * th) / s
        q = [wa * x + wb * y for x, y in zip(a, b)]
    n = math.sqrt(sum(x * x for x in q))
    return [x / n for x in q]


def lerp(a, b, t):
    return [x + (y - x) * t for x, y in zip(a, b)]


def build_raise(start, end):
    """start: vanilla raise (frame 0 used), end: corrected hold (frame 0 used)."""
    if len(start.tracks) != len(end.tracks):
        sys.exit('track count mismatch %d vs %d' % (len(start.tracks), len(end.tracks)))
    n = int(round(BOW_DRAWN_AT * FPS)) + 1
    for tr_s, tr_e in zip(start.tracks, end.tracks):
        b = (tr_e.translations[0], tr_e.rotations[0], tr_e.scales[0])
        # PyNifly decodes one track of vanilla sneakcrossbow_aim (41) with NaN translation/scale: start that
        # component from the hold value instead.
        a = tuple(bv if any(math.isnan(x) for x in av) else av
                  for av, bv in zip((tr_s.translations[0], tr_s.rotations[0], tr_s.scales[0]), b))
        tr_s.translations, tr_s.rotations, tr_s.scales = [], [], []
        for f in range(n):
            u = f / (n - 1)
            w = u * u * (3 - 2 * u)  # smoothstep: no velocity jump at either end
            tr_s.translations.append(lerp(a[0], b[0], w))
            tr_s.rotations.append(slerp(a[1], b[1], w))
            tr_s.scales.append(lerp(a[2], b[2], w))
    start.duration = BOW_DRAWN_AT
    start.num_frames = n
    start.frame_duration = BOW_DRAWN_AT / (n - 1)
    return havok_blocks(start)


def max_gap(a, fa, b, fb, skip=()):
    return max(math.degrees(2 * math.acos(min(1.0, abs(sum(x * y for x, y in zip(ta.rotations[fa], tb.rotations[fb]))))))
               for i, (ta, tb) in enumerate(zip(a.tracks, b.tracks)) if i not in skip)


# ---- inputs ----------------------------------------------------------------------------------------------------

def muskets():
    """{mesh path (lowercase, under meshes/): [(EditorID, formID int)]} - the model the first-person view draws
    (FirstPersonModel's static, else the WEAP's own model)."""
    def field(text, key):
        m = re.search(r'^%s:\s*\r?\n\s+File:\s*(.+?)\s*$' % key, text, re.M)
        return m.group(1) if m else None
    statics = {}
    for p in glob.glob(os.path.join(REF, 'Statics', '*.yaml')):
        t = open(p, encoding='utf-8').read()
        statics[re.search(r'^FormKey:\s*(\w+):', t, re.M).group(1)] = field(t, 'Model')
    out = {}
    for p in glob.glob(os.path.join(REF, 'Weapons', '*.yaml')):
        t = open(p, encoding='utf-8').read()
        fk = re.search(r'^FormKey:\s*(\w+):(.+?)\s*$', t, re.M)
        if fk.group(2) != ORDO:
            continue
        fp = re.search(r'^FirstPersonModel:\s*(\w+):', t, re.M)
        model = statics.get(fp.group(1)) if fp else None
        model = model or field(t, 'Model')
        eid = re.search(r'^EditorID:\s*(\S+)', t, re.M).group(1)
        out.setdefault(model.replace('\\', '/').lower(), []).append((eid, int(fk.group(1), 16)))
    if sum(len(v) for v in out.values()) != 14:
        sys.exit('expected 14 Ordo muskets in %s, found %d' % (REF, sum(len(v) for v in out.values())))
    return out


def winning_loose(mods_dir, mods, rel):
    for mod in mods:
        p = QRS.find_ci(os.path.join(mods_dir, mod), ['meshes'] + rel.split('/'))
        if p and os.path.isfile(p):
            return mod, p
    sys.exit('no loose %s in the active profile (only BSA copies?)' % rel)


def vanilla_clip(bsa, name, tmp):
    data, listing = bsa
    key = (VANILLA + name).lower()
    if key not in listing:
        sys.exit('%s not in Skyrim - Animations.bsa' % key)
    with open(tmp, 'wb') as fh:
        fh.write(_bsa.read(data, listing[key]))
    anim = anim_skyrim.load_skyrim_animation(tmp)
    os.remove(tmp)
    return anim


def or_equipped(weapons):
    return {'condition': 'OR', 'requiredVersion': '1.0.0.0', 'Conditions': [
        {'condition': 'IsEquipped', 'requiredVersion': '1.0.0.0',
         'Form': {'pluginName': ORDO, 'formID': '%X' % fid}, 'Left hand': False} for _, fid in weapons]}


def write_config(path, cfg):
    with open(os.path.join(path, 'config.json'), 'w', encoding='utf-8') as fh:
        json.dump(cfg, fh, indent=4)


# ---- main ------------------------------------------------------------------------------------------------------

def main():
    root = sys.argv[1] if len(sys.argv) > 1 else TOOLS['modlistRoot']
    mods_dir = os.path.join(root, 'mods')
    profile, mods = QRS.profile_mods(root)
    for need in ('DAR Rifles Standalone', MOD):
        if need not in mods:
            sys.exit('%s is not enabled in %s' % (need, profile))
    bsa = _bsa.listing(os.path.join(root, 'Stock Game', 'Data', 'Skyrim - Animations.bsa'))
    out_mod = os.path.join(mods_dir, MOD)
    tmp = os.path.join(os.environ.get('TEMP', '.'), '_musket_ads.hkx')
    with open(tmp, 'wb') as fh:
        fh.write(_bsa.read(bsa[0], bsa[1][SKELETON]))
    rig = Rig(anim_skyrim.load_skyrim_skeleton(tmp))
    os.remove(tmp)
    dar = QRS.find_ci(os.path.join(mods_dir, 'DAR Rifles Standalone'), DAR)
    if not dar:
        sys.exit('DAR Rifles Standalone has no first-person 432101 folder')
    src = {}
    for _, clips in FAMILIES.values():
        for c in clips:
            p = os.path.join(dar, c)
            if not os.path.isfile(p):
                sys.exit('missing %s - DAR Rifles Standalone layout changed' % p)
            src[c] = p
    holds_src = [anim_skyrim.load_skyrim_animation(src[h]) for h, _ in FAMILIES.values()]
    # every input is read before the mod folder is wiped
    groups = []
    for mesh_rel, weapons in sorted(muskets().items()):
        mod, path = winning_loose(mods_dir, mods, mesh_rel)
        V = mesh_surface(path)
        rear, front, blade = sight_line(V)
        # second pass: clear the line all the way back to the eye (the rear sight's distance from it, either hold)
        eye_back = max(float((rig.weapon_in_camera(h, 0) @ np.r_[rear, 1])[1]) for h in holds_src) - 1.0
        rear, front, blade = sight_line(V, max(BREECH_BACK, eye_back))
        groups.append((mesh_rel, sorted(weapons), mod, V, rear, front, blade))
    if os.path.isdir(out_mod):
        shutil.rmtree(out_mod)
    oar = os.path.join(out_mod, *OAR)
    written = 0
    for i, (mesh_rel, weapons, mesh_mod, V, rear, front, blade) in enumerate(groups):
        label = os.path.basename(mesh_rel).replace('_animated.nif', '')
        sub = os.path.join(oar, 'ADS %s' % label)
        quick = os.path.join(oar, 'ADS %s, both reload perks' % label)
        os.makedirs(os.path.join(sub, 'dlc01'))
        os.makedirs(os.path.join(quick, 'dlc01'))
        print('%s (%s; %s) <- %s; front sight %.2f over the barrel'
              % (label, ', '.join(e for e, _ in weapons), mesh_rel, mesh_mod, blade))
        holds = {}
        for family, (hold_name, clips) in FAMILIES.items():
            hold = anim_skyrim.load_skyrim_animation(src[hold_name])
            check_finite(hold, hold_name)
            c = solve_correction(rig, hold, rear, front)
            before = measure(rig, hold, rear, front, V)
            for clip in clips:
                anim = anim_skyrim.load_skyrim_animation(src[clip])
                check_finite(anim, clip)
                out = os.path.join(sub, 'dlc01', clip)
                apply_correction(rig, anim, c)
                shift = delay_recoil(rig, anim, clip)
                anim_skyrim.write_skyrim_animation(out, anim, ptr_size=8)
                check_blocks(out)
                got = anim_skyrim.load_skyrim_animation(out)
                orig = anim_skyrim.load_skyrim_animation(src[clip])
                if got.num_frames != orig.num_frames or abs(got.duration - orig.duration) > 1e-4 or \
                        [(round(a.time, 4), a.text) for a in got.annotations] != \
                        [(round(a.time, 4), a.text) for a in orig.annotations]:
                    sys.exit('%s: timing or annotations changed' % clip)
                # the camera-frame weapon pose must be the source's (shifted by the recoil hold) moved by c
                worst = max(angle_deg(np.linalg.inv(c @ rig.weapon_in_camera(orig, max(0, f - shift))) @ rig.weapon_in_camera(got, f))
                            for f in range(0, got.num_frames, 4))
                if worst > 0.5:
                    sys.exit('%s: re-encoded pose drifts %.2f deg from the correction' % (clip, worst))
                if clip in (hold_name,):
                    (ra, fa, roll, blocking, dr, df) = measure(rig, got, rear, front, V)
                    print('  %-30s before: front (%5.1f, %5.1f) deg, roll %5.1f | after: rear (%4.2f, %4.2f) '
                          'front (%4.2f, %4.2f) deg, roll %4.2f, sights %.0f / %.0f units from the eye, %d points '
                          'in the line of sight; correction %.1f deg'
                          % (clip, *before[1], before[2], *ra, *fa, roll, dr, df, blocking, angle_deg(c)))
                    rear_drop = math.degrees(math.atan2(-EYE_HEIGHT, dr))
                    if max(abs(fa[0]), abs(fa[1] + SIGHT_DROP_DEG), abs(ra[0]), abs(ra[1] - rear_drop),
                           abs(roll)) > 0.3:
                        sys.exit('%s: sights not where they belong after correction' % label)
                    if blocking:
                        sys.exit('%s: %d points of the gun rise into the line of sight' % (label, blocking))
                    holds[clip] = got
                written += 1
            holds.update({k: anim_skyrim.load_skyrim_animation(os.path.join(sub, 'dlc01', k))
                          for k in clips if 'idledrawn' in k})
        for raise_name, hold_name in RAISES.items():
            vanilla = vanilla_clip(bsa, raise_name, tmp)
            start_gap = max_gap(holds[hold_name], 0, vanilla, -1, rig.anim_objects)
            out = os.path.join(sub, 'dlc01', raise_name)
            anim_skyrim.write_skyrim_animation(out, build_raise(vanilla, holds[hold_name]), ptr_size=8)
            check_blocks(out)
            check = anim_skyrim.load_skyrim_animation(out)
            end_gap = max_gap(check, -1, holds[hold_name], 0, rig.anim_objects)
            if end_gap > 2.0:
                sys.exit('%s: raise ends %.1f deg off the hold pose' % (raise_name, end_gap))
            print('  %-30s %.2f s raise; vanilla raise end -> hold %.1f deg, ours %.1f deg'
                  % (raise_name, check.duration, start_gap, end_gap))
            written += 1
        for clip in QUICK:
            data = open(os.path.join(sub, 'dlc01', clip), 'rb').read()
            anim, before = QRS.retime(data, tmp)
            out = os.path.join(quick, 'dlc01', clip)
            anim_skyrim.write_skyrim_animation(out, havok_blocks(anim), ptr_size=8)
            check_blocks(out)
            got, drift = QRS.check(out, before, tmp)
            os.remove(tmp)
            print('  %-30s %.3f s -> %.3f s (both perks), drift %.2f deg' % (clip, before[0], got.duration, drift))
            written += 1
        cond = or_equipped(weapons)
        write_config(sub, {
            'name': 'ADS %s' % label,
            'description': 'Aim down sights: %s (%s). DAR Rifles 432101 clips with the arms moved so the gun is '
                           'upright, its front sight %.1f deg under the crosshair and the eye %.1f units above the '
                           'breech; %.1f s raise into it.'
                           % (', '.join(e for e, _ in weapons), mesh_rel, SIGHT_DROP_DEG, EYE_HEIGHT, BOW_DRAWN_AT),
            'priority': PRIORITY + i,
            'conditions': [cond],
        })
        write_config(quick, {
            'name': 'ADS %s, both reload perks' % label,
            'description': 'Quick Reload + Rapid Shot: the ADS reload retimed %.2fx shorter, as Quick Reload Stack.'
                           % QRS.STACK_FACTOR,
            'priority': PRIORITY_QUICK + i,
            'conditions': QRS.BOTH_PERKS + [cond],
        })
    write_config(oar, {
        'name': MOD, 'author': 'Zenderal',
        'description': 'First-person aim down sights for Ordo Legionis muskets: per-musket hold, shot, reload and '
                       'raise clips that put each gun upright with its sights on the crosshair.',
    })
    print('built %s for profile %s: %d meshes, %d clips' % (out_mod, profile, len(groups), written))


if __name__ == '__main__':
    main()
