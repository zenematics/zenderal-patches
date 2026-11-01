"""Add first-person ramrod reloads to `Zenderal - Musket Ramrod Reload`: Zodd's per-musket third-person reload
(built by tools/09) retargeted onto the first-person arms, lifted into view.

Zodd's clips are third person only. Seen from the eyes with a level camera, the reload happens below the screen
(rendered 2026-11-01: only the muzzle tip shows). In Zodd's own video the camera follows the head, which looks down
10-20 deg (and turns +-15-20 deg toward the pouch) through the reload. The list's camera stays level (Improved Camera
head bob off, first-person arms), so instead the arms are turned by the head's turn: what the eyes see of the hands is
what Zodd's video shows, while the world stays level.

Per frame, for each musket mesh (from tools/09's third-person clips, gun already slid to fit that mesh):
  - the camera: the third-person `NPCEyeBone`, facing the actor's forward; the head's pitch and yaw relative to the
    clip's first frame give the lift L (+ LIFT_EXTRA_DEG of extra pitch);
  - everything under `NPC Spine2 [Spn2]` is mapped by M = Camera1st * L * inv(eye) into the first-person rig, keeping
    the third-person local rotations, the first-person bone lengths (upper arm 20.26 vs 22.83, finger bases) and the
    third-person `Weapon` offset (the slid gun);
  - both arms are solved shoulder-elbow-hand so each hand lands exactly on its mapped third-person hand (position and
    rotation), elbows bending toward the mapped third-person elbows;
  - bones above Spine2 and `Camera1st` stay at the first-person aim-down-sights hold (no camera kick at the shot);
  - the shot clip holds that aim-down-sights pose (the shot fires at 0.2 s) until HOLD_ADS and blends into the motion
    by BLEND_IN; the reload clip blends in from the idle hold over BLEND_IN_RELOAD; both blend into the idle hold
    (`crossbow_idleheld.hkx`) over their last BLEND_OUT and end exactly on it: after either the graph is back in
    1HM_Ready_State, which plays that hold (1.1 ended on the aim-down-sights hold: the gun snapped to the hip).
    Blended bone by bone, the left hand swung up to 12 units beside the gun on its way (4.4-4.6 s), so during the
    blend-out it is re-solved onto the gun, its grip blended from the motion's to the idle hold's (left_on_gun).
    The shot clip's blend-in got the same: bone by bone the hand went from the aim-down-sights hold's forestock grip
    (13 units up the gun) to Zodd's at the stock wrist (1-3 units up, other side) through the stock, the fingers
    inside the gun at 0.40, 0.54 and 0.74 s ("the musket clips through the left hand just after firing", 2026-11-01).
The SHOT clip is the reload. Traced 2026-11-01 (SpellAimTrace 1.3.0): after a shot the game never sends `reloadStart`;
the 1hm graph stays in its attack state, plays the shot clip to its end (Zodd's 5.1 s carries the whole ramrod work;
vanilla's 2.83 s carries its reload too) and leaves on the clip's own `attackStop`. The separate reload clip plays
only when the game sends `reloadStart` (e.g. drawing an unloaded crossbow). 1.0 froze the shot clip on the reload
clip's first pose after `arrowAttach` (assumed hand-over): "starts but stops and just holds the gun". Timing and
annotations are Zodd's, so first and third person reload alike. Sneak shots/reloads (2026-11-01) are the same motion
from the standing third-person clips, between the aim-down-sights set's sneak hold and the crouched `sneakmtidle`.

OAR, first person, per mesh:  `Ramrod 1P <mesh>` 432600+i (shot + reload, plain and dwarven names) and
`Ramrod 1P <mesh>, both reload perks` 432650+i (the reload retimed like Quick Reload Stack), above the aim-down-sights
set's 432400+i / 432450+i. Run after tools/06 and tools/09 (tools/09 rebuilds the mod folder and drops these).
Derived from Zodd's clips: covered by the same permission note as tools/09 (the mod is Wabbajack-ignored).

Usage:  python src/FlintlockOverhaul/tools/10-build-ramrod-reload-1p.py [<modlist root>]   (needs numpy)
"""
import importlib.util
import json
import math
import os
import shutil
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


R3P = _load('ramrod3p', os.path.join(HERE, '09-build-ramrod-reload.py'))
ADS = R3P.ADS
anim_skyrim, QRS, _bsa = ADS.anim_skyrim, ADS.QRS, ADS._bsa

OAR_1P = ADS.ANIMS_1P + ['OpenAnimationReplacer', R3P.MOD]
PRIORITY = 432600          # above the aim-down-sights set (432400+i) and its quick reloads (432450+i)
PRIORITY_QUICK = 432650
LIFT_EXTRA_DEG = 0.0       # extra upward turn of the arms during the reload, on top of the head's look-down
HOLD_ADS = 0.30            # the shot clip stays in the aim-down-sights pose until here (shot at 0.2 s)
BLEND_IN = 0.80            # ... and is fully in the reload motion by here
BLEND_IN_RELOAD = 0.30     # the separate reload clip blends in from the idle hold (the graph enters it from Ready)
BLEND_OUT = 1.00           # both clips' last seconds blend into the first-person idle hold, the pose the graph plays
                           # next (1HM_Behavior: attackStop and reloadStop both go to 1HM_Ready_State, which plays
                           # IDLE). 1.1 ended on the aim-down-sights hold, and the gun snapped from the sights down to
                           # the hip as the clip ended (in game 2026-11-01). 0.6 s popped the gun up from below the view.
IDLE = 'crossbow_idleheld.hkx'   # vanilla's wins for the Ordo muskets: DAR Rifles' 432101 set has none
# Copied into each mesh's submod with `AnimObjectUnequip` at 0 (with IDLE), so a reload cut short unloads its prop
SAFETY_ADS = ['crossbow_aim.hkx', 'crossbow_aimdwarven.hkx', 'crossbow_idledrawn.hkx', 'crossbow_idledrawndwarven.hkx',
              'sneakcrossbow_aim.hkx', 'sneakcrossbow_aimdwarven.hkx', 'sneakcrossbow_idledrawn.hkx',
              'sneakcrossbow_idledrawndwarven.hkx']
# The head's turn is followed unsmoothed: it tracks the gun through Zodd's fast muzzle-down swing, so following it
# steadies the gun on screen. Smoothed (Gaussian sigma 0.15 s) the gun's peak speed in the view rose 35.8 -> 39.4
# units/frame and the right hand's 13.8 -> 15.9 (measured 2026-11-01).
CLIPS = {'crossbow_release.hkx': 'crossbow_releasedwarven.hkx', 'crossbow_reload.hkx': 'crossbow_reloaddwarven.hkx',
         'sneakcrossbow_release.hkx': 'sneakcrossbow_releasedwarven.hkx',
         'sneakcrossbow_reload.hkx': 'sneakcrossbow_reloaddwarven.hkx'}
# Sneak (2026-11-01): the same motion, retargeted from the STANDING third-person clips (the arms relative to the eye
# are the same crouched; the standing gun slide needs no crouched ground clamp), starting on the aim-down-sights set's
# sneak hold and ending on the first-person crouched idle the graph plays next (both with the camera at 86.4, not 120.5)
SNEAK_IDLE = R3P.SNEAK_IDLE
ARM_SIDES = (('NPC L UpperArm [LUar]', 'NPC L Forearm [LLar]', 'NPC L Hand [LHnd]'),
             ('NPC R UpperArm [RUar]', 'NPC R Forearm [RLar]', 'NPC R Hand [RHnd]'))


rot_between, smooth = R3P.rot_between, R3P.smooth


def rx(deg):
    a = math.radians(deg)
    return np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])


def rz(deg):
    a = math.radians(deg)
    return np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])


def local_of(parent_world, world):
    return np.linalg.inv(parent_world) @ world


def split(m):
    s = float(np.linalg.norm(m[:3, 0]))
    return [float(x) for x in m[:3, 3]], ADS.mat_quat(m[:3, :3] / s), s


class Retarget:
    def __init__(self, sk1, sk3):
        self.sk1, self.sk3 = sk1, sk3
        self.i1 = {n: i for i, n in enumerate(sk1.bones)}
        self.i3 = {n: i for i, n in enumerate(sk3.bones)}
        spine2 = self.i1['NPC Spine2 [Spn2]']
        under = set()
        for i, p in enumerate(sk1.parents):    # bones under Spine2 (parents come before children)
            if p == spine2 or p in under:
                under.add(i)
        self.mapped = sorted(under)
        self.reparented = set()   # different parent in the two rigs (the pauldrons): placed at their mapped world
        for i in self.mapped:
            name = sk1.bones[i]
            if name not in self.i3:
                sys.exit('first-person bone %s has no third-person twin' % name)
            if sk1.bones[sk1.parents[i]] != sk3.bones[sk3.parents[self.i3[name]]]:
                self.reparented.add(i)
        self.spine2, self.spine1 = spine2, self.i1['NPC Spine1 [Spn1]']
        self.cam1 = self.i1['Camera1st [Cam1]']
        self.fingers = {i for i in self.mapped if 'Finger' in sk1.bones[i]}
        self.forearms = {self.i1['NPC L Forearm [LLar]'], self.i1['NPC R Forearm [RLar]']}

    def world3(self, anim, f):
        out = [None] * len(self.sk3.parents)
        for i, p in enumerate(self.sk3.parents):
            if i < len(anim.tracks):
                t = anim.tracks[i]
                local = ADS.trs(t.translations[f], t.rotations[f], t.scales[f][0])
            else:
                r = self.sk3.reference_pose[i]
                local = ADS.trs(r.translation, r.rotation, r.scale[0])
            out[i] = local if p < 0 else out[p] @ local
        return out

    def locals1(self, anim, f):
        return [ADS.trs(t.translations[f], t.rotations[f], t.scales[f][0]) for t in anim.tracks]

    def head_angles(self, w3):
        h = w3[self.i3['NPC Head [Head]']][:3, 1]
        return math.degrees(math.atan2(h[2], math.hypot(h[0], h[1]))), math.degrees(math.atan2(h[0], h[1]))

    def pose(self, a3, f, base_locals, lift_pitch, lift_yaw):
        """First-person local transforms (4x4 list) for frame f of the third-person clip a3."""
        w3 = self.world3(a3, f)
        eye = w3[self.i3['NPCEyeBone']][:3, 3]
        lift = rx(lift_pitch) @ rz(lift_yaw)               # camera follows the head -> arms turn opposite
        M = np.eye(4)
        M[:3, :3] = lift
        M[:3, 3] = -lift @ eye
        loc = [m.copy() for m in base_locals]
        w1 = [None] * len(self.sk1.parents)
        for i, p in enumerate(self.sk1.parents):          # base world (bones above Spine2, camera)
            w1[i] = loc[i] if p < 0 else w1[p] @ loc[i]
        cam = w1[self.cam1]
        M = cam @ M
        targets = {}
        for i in self.mapped:                              # mapped third-person pose, first-person lengths
            n = self.sk1.bones[i]
            l3 = local_of(w3[self.i3[self.sk3.bones[self.sk3.parents[self.i3[n]]]]], w3[self.i3[n]])
            if i in self.fingers:
                l3[:3, 3] = base_locals[i][:3, 3]
            elif i in self.forearms:
                l3[:3, 3] *= np.linalg.norm(self.sk1.reference_pose[i].translation) / np.linalg.norm(l3[:3, 3])
            loc[i] = l3
            targets[n] = M @ w3[self.i3[n]]
        w1[self.spine2] = M @ w3[self.i3['NPC Spine2 [Spn2]']]
        loc[self.spine2] = local_of(w1[self.spine1], w1[self.spine2])
        self.refresh(loc, w1, targets)
        for ua, fa, hand in ARM_SIDES:                      # shoulder-elbow-hand onto the mapped hand
            iu, ifa, ih = self.i1[ua], self.i1[fa], self.i1[hand]
            S = w1[iu][:3, 3]
            H = targets[hand][:3, 3]
            P = targets[fa][:3, 3]                          # mapped third-person elbow: the bend direction
            a = np.linalg.norm(loc[ifa][:3, 3])
            b = np.linalg.norm(loc[ih][:3, 3])
            if hand == ARM_SIDES[0][2] and np.linalg.norm(H - S) > a + b - 0.05:
                # tools/09 stretches the third-person left arm onto the ramrod; the first-person arm is shorter, so
                # the hand slides along the rod (AnimObjectL's +Y) to within reach, the rod riding along its own axis
                r = ADS.unit(targets['AnimObjectL'][:3, 1])
                q, reach = H - S, a + b - 0.05
                disc = (q @ r) ** 2 - (q @ q - reach * reach)
                if disc >= 0:
                    s = min((-(q @ r) + math.sqrt(disc), -(q @ r) - math.sqrt(disc)), key=abs)
                    H = H + s * r
                    targets[hand] = targets[hand].copy()
                    targets[hand][:3, 3] = H
            self.solve_arm(loc, w1, (iu, ifa, ih), targets[hand], P)
            self.refresh(loc, w1, targets)
        return loc, w1, targets

    def solve_arm(self, loc, w1, arm, target, P):
        """Shoulder-elbow-hand: the hand (iu, ifa, ih) onto `target` (4x4 world; its rotation is kept), the elbow bending
        toward P. Updates loc and the arm's entries of w1."""
        iu, ifa, ih = arm
        S, H = w1[iu][:3, 3], target[:3, 3]
        a = np.linalg.norm(loc[ifa][:3, 3])
        b = np.linalg.norm(loc[ih][:3, 3])
        d = np.linalg.norm(H - S)
        d = min(max(d, abs(a - b) + 1e-3), a + b - 1e-3)
        u = (H - S) / max(np.linalg.norm(H - S), 1e-6)
        v = (P - S) - u * ((P - S) @ u)
        v = v / np.linalg.norm(v) if np.linalg.norm(v) > 1e-6 else np.cross(u, [0, 0, 1.0])
        cos_a = (a * a + d * d - b * b) / (2 * a * d)
        E = S + a * (cos_a * u + math.sqrt(max(0.0, 1 - cos_a * cos_a)) * v)
        # turn the upper arm so its forearm offset points at E, then the forearm so its hand offset points at H
        c0 = w1[iu][:3, :3] @ loc[ifa][:3, 3]
        q = rot_between(c0 / np.linalg.norm(c0), (E - S) / np.linalg.norm(E - S))
        w1[iu][:3, :3] = q @ w1[iu][:3, :3]
        loc[iu] = local_of(w1[self.sk1.parents[iu]], w1[iu])
        w1[ifa] = w1[iu] @ loc[ifa]
        c1 = w1[ifa][:3, :3] @ loc[ih][:3, 3]
        q = rot_between(c1 / np.linalg.norm(c1), (H - E) / max(np.linalg.norm(H - E), 1e-6))
        w1[ifa][:3, :3] = q @ w1[ifa][:3, :3]
        loc[ifa] = local_of(w1[iu], w1[ifa])
        hw = target.copy()
        hw[:3, 3] = (w1[ifa] @ np.r_[loc[ih][:3, 3], 1])[:3]     # where the solved forearm puts the wrist
        loc[ih] = local_of(w1[ifa], hw)
        w1[ih] = w1[ifa] @ loc[ih]

    def world1(self, loc):
        w = [None] * len(self.sk1.parents)
        for i, p in enumerate(self.sk1.parents):
            w[i] = loc[i] if p < 0 else w[p] @ loc[i]
        return w

    def left_on_gun(self, final, w_motion, w_end, s):
        """The blend into the idle hold, per bone, swung the left hand up to 12 units beside the gun (4.4-4.6 s): keep
        it on the gun instead, its grip relative to the gun blended (weight s) from w_motion's to w_end's (the shot
        clip's blend-in passes the aim-down-sights hold and the motion as these two),
        the arm re-solved with the blended elbow as the bend hint; out of the shorter arm's reach, the grip slides along
        the gun to the nearest point in reach. Returns (the hand's world shift, its miss), in units."""
        iw = self.i1['Weapon']
        arm = tuple(self.i1[n] for n in ARM_SIDES[0])
        rel = [np.linalg.inv(w[iw]) @ w[arm[2]] for w in (w_motion, w_end)]
        t0, q0, _ = split(rel[0])
        t1, q1, _ = split(rel[1])
        w1 = self.world1(final)
        target = w1[iw] @ ADS.trs(ADS.lerp(t0, t1, s), ADS.slerp(q0, q1, s), 1.0)
        S, H = w1[arm[0]][:3, 3], target[:3, 3]
        reach = np.linalg.norm(final[arm[1]][:3, 3]) + np.linalg.norm(final[arm[2]][:3, 3]) - 0.05
        if np.linalg.norm(H - S) > reach:
            r, q = ADS.unit(w1[iw][:3, 1]), H - S
            disc = (q @ r) ** 2 - (q @ q - reach * reach)
            if disc >= 0:
                target[:3, 3] = H + min((-(q @ r) + math.sqrt(disc), -(q @ r) - math.sqrt(disc)), key=abs) * r
        before = w1[arm[2]][:3, 3].copy()
        self.solve_arm(final, w1, arm, target, w1[arm[1]][:3, 3])
        return float(np.linalg.norm(w1[arm[2]][:3, 3] - before)), float(np.linalg.norm(w1[arm[2]][:3, 3] - target[:3, 3]))

    def refresh(self, loc, w1, targets):
        """World transforms of everything under Spine2 from its locals; reparented bones keep their mapped world."""
        for i in self.mapped:
            p = self.sk1.parents[i]
            if i in self.reparented:
                loc[i] = local_of(w1[p], targets[self.sk1.bones[i]])
            w1[i] = w1[p] @ loc[i]


def blend(la, lb, w):
    """Per-bone blend of two local-pose lists: w = 0 -> la, 1 -> lb."""
    out = []
    for a, b in zip(la, lb):
        ta, qa, sa = split(a)
        tb, qb, sb = split(b)
        out.append(ADS.trs(ADS.lerp(ta, tb, w), ADS.slerp(qa, qb, w), sa + (sb - sa) * w))
    return out


def build(rt, a3, ads_hold, idle, hold_path, clip):
    """First-person clip for one third-person clip; returns (anim, max hand error, frames solved short).
    The shot clip starts on the aim-down-sights hold, the reload clip on the idle hold; both end on the idle hold."""
    shot = 'release' in clip
    end = rt.locals1(idle, 0)
    w_end = rt.world1(end)
    start = rt.locals1(ads_hold, 0) if shot else end
    w_start = rt.world1(start)
    # the left hand is kept on the gun only through a blend whose far pose holds the gun with it: the crouched idle
    # (`sneakmtidle`) hangs it 58 units away, so into that the hand lets go bone by bone (as tools/09's settle)
    iw, ilh = rt.i1['Weapon'], rt.i1[ARM_SIDES[0][2]]
    on_start, on_end = (np.linalg.norm((np.linalg.inv(w[iw]) @ w[ilh])[:3, 3]) < R3P.ON_GUN for w in (w_start, w_end))
    out = anim_skyrim.load_skyrim_animation(hold_path)      # template with the first-person track layout
    for t in out.tracks:
        t.translations, t.rotations, t.scales = [], [], []
    worst, short, kept = 0.0, 0, 0.0
    n = a3.num_frames
    head = np.array([rt.head_angles(rt.world3(a3, f)) for f in range(n)])
    for f in range(n):
        t_s = f * a3.frame_duration
        if shot:
            w_in = smooth((t_s - HOLD_ADS) / (BLEND_IN - HOLD_ADS))
        else:
            w_in = smooth(t_s / BLEND_IN_RELOAD)
        w_out = smooth((t_s - (a3.duration - BLEND_OUT)) / BLEND_OUT)
        lift_pitch = (head[0, 0] - head[f, 0]) + LIFT_EXTRA_DEG * w_in * (1 - w_out)
        loc, w1, targets = rt.pose(a3, f, start, lift_pitch, head[f, 1] - head[0, 1])
        for _, _, hand in ARM_SIDES:
            err = float(np.linalg.norm(w1[rt.i1[hand]][:3, 3] - targets[hand][:3, 3]))
            worst = max(worst, err)
            short += err > 0.5
        final = blend(blend(start, loc, w_in), end, w_out)
        if shot and 0 < w_in < 1 and on_start:   # the blend out of the aim-down-sights hold: same, from its grip
            moved, miss = rt.left_on_gun(final, w_start, w1, w_in)
            kept = max(kept, moved)
            worst = max(worst, miss)
            short += miss > 0.5
        if 0 < w_out < 1 and on_end:
            moved, miss = rt.left_on_gun(final, w1, w_end, w_out)
            kept = max(kept, moved)
            worst = max(worst, miss)
            short += miss > 0.5
        for tr, m in zip(out.tracks, final):
            tt, q, s = split(m)
            if tr.rotations and sum(x * y for x, y in zip(q, tr.rotations[-1])) < 0:
                q = [-x for x in q]
            tr.translations.append(tt)
            tr.rotations.append(q)
            tr.scales.append([s, s, s])
    out.duration = a3.duration
    out.num_frames = n
    out.frame_duration = a3.frame_duration
    out.annotations = list(a3.annotations)
    return ADS.havok_blocks(out), worst, short, kept


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else ADS.TOOLS['modlistRoot']
    mods_dir = os.path.join(root, 'mods')
    oar3 = os.path.join(mods_dir, R3P.MOD, *R3P.OAR)
    ads_oar = os.path.join(mods_dir, ADS.MOD, *ADS.OAR)
    if not os.path.isdir(oar3):
        sys.exit('run tools/09 first: %s is missing' % oar3)
    bsa = _bsa.listing(os.path.join(root, 'Stock Game', 'Data', 'Skyrim - Animations.bsa'))
    tmp = os.path.join(os.environ.get('TEMP', '.'), '_ramrod1p.hkx')
    with open(tmp, 'wb') as fh:
        fh.write(_bsa.read(bsa[0], bsa[1][ADS.SKELETON]))
    sk1 = anim_skyrim.load_skyrim_skeleton(tmp)
    with open(tmp, 'wb') as fh:
        fh.write(_bsa.read(bsa[0], bsa[1][R3P.SKELETON]))
    sk3 = anim_skyrim.load_skyrim_skeleton(tmp)
    rt = Retarget(sk1, sk3)
    _, mods = QRS.profile_mods(root)
    idle_src, idle_data = QRS.winner(mods_dir, mods, bsa, ADS.ANIMS_1P + ['dlc01', IDLE])
    with open(tmp, 'wb') as fh:
        fh.write(idle_data)
    idle = anim_skyrim.load_skyrim_animation(tmp)
    if len(idle.tracks) != len(sk1.bones):
        sys.exit('%s from %s has %d tracks, the first-person skeleton %d' % (IDLE, idle_src, len(idle.tracks), len(sk1.bones)))
    print('idle hold: %s from %s' % (IDLE, idle_src))
    sneak_src, data = QRS.winner(mods_dir, mods, bsa, ADS.ANIMS_1P + [SNEAK_IDLE])
    with open(tmp, 'wb') as fh:
        fh.write(data)
    sneak_idle = anim_skyrim.load_skyrim_animation(tmp)
    if len(sneak_idle.tracks) != len(sk1.bones):
        sys.exit('%s from %s has %d tracks, the first-person skeleton %d' % (SNEAK_IDLE, sneak_src, len(sneak_idle.tracks), len(sk1.bones)))
    print('crouched idle: %s from %s' % (SNEAK_IDLE, sneak_src))
    oar1 = os.path.join(mods_dir, R3P.MOD, *OAR_1P)
    if os.path.isdir(oar1):
        shutil.rmtree(oar1)
    labels = sorted(d[len('Ramrod '):] for d in os.listdir(oar3) if d.startswith('Ramrod ') and 'perks' not in d)
    written = 0
    for i, label in enumerate(labels):
        cfg3 = os.path.join(oar3, 'Ramrod %s' % label, 'config.json')
        conds = json.load(open(cfg3, encoding='utf-8'))['conditions']
        hold_path = os.path.join(ads_oar, 'ADS %s' % label, 'dlc01', 'crossbow_idledrawn.hkx')
        if not os.path.isfile(hold_path):
            sys.exit('run tools/06 first: %s is missing' % hold_path)
        ads_hold = anim_skyrim.load_skyrim_animation(hold_path)
        ads_sneak = anim_skyrim.load_skyrim_animation(os.path.join(ads_oar, 'ADS %s' % label, 'dlc01', 'sneakcrossbow_idledrawn.hkx'))
        sub = os.path.join(oar1, 'Ramrod 1P %s' % label)
        quick = os.path.join(oar1, 'Ramrod 1P %s, both reload perks' % label)
        os.makedirs(os.path.join(sub, 'dlc01'))
        os.makedirs(os.path.join(quick, 'dlc01'))
        for clip, dwarven in CLIPS.items():
            sneak = clip in R3P.SNEAK
            a3 = anim_skyrim.load_skyrim_animation(os.path.join(oar3, 'Ramrod %s' % label, 'dlc01', R3P.SNEAK.get(clip, clip)))
            end_idle = sneak_idle if sneak else idle
            anim, worst, short, kept = build(rt, a3, ads_sneak if sneak else ads_hold, end_idle, hold_path, clip)
            for name in (clip, dwarven):
                out = os.path.join(sub, 'dlc01', name)
                anim_skyrim.write_skyrim_animation(out, anim, ptr_size=8)
                ADS.check_blocks(out)
                written += 1
            got = anim_skyrim.load_skyrim_animation(os.path.join(sub, 'dlc01', clip))
            ADS.check_finite(got, clip)
            if [(round(a.time, 4), a.text) for a in got.annotations] != [(round(a.time, 4), a.text) for a in a3.annotations] \
                    or abs(got.duration - a3.duration) > 1e-4:
                sys.exit('%s %s: timing or annotations differ from the third-person clip' % (label, clip))
            gap = max(float(np.linalg.norm(np.subtract(t.translations[-1], i.translations[0])))
                      for t, i in zip(got.tracks, end_idle.tracks))
            turn = min(abs(float(np.dot(t.rotations[-1], i.rotations[0]))) for t, i in zip(got.tracks, end_idle.tracks))
            if gap > 0.05 or turn < 0.9999:
                sys.exit('%s %s: last frame is off the idle hold (%.2f units, quaternion dot %.5f)' % (label, clip, gap, turn))
            print('%-24s %-22s %.2f s, %d frames; hands on target within %.2f units (%d frames out of reach); left hand '
                  'kept on the gun in the blend-out (moved up to %.1f)' % (label, clip, got.duration, got.num_frames,
                                                                         worst, short, kept))
        for reload_clip in ('crossbow_reload.hkx', 'sneakcrossbow_reload.hkx'):
            data = open(os.path.join(sub, 'dlc01', reload_clip), 'rb').read()
            for name in (reload_clip, CLIPS[reload_clip]):
                anim, before = QRS.retime(data, tmp)
                out = os.path.join(quick, 'dlc01', name)
                anim_skyrim.write_skyrim_animation(out, ADS.havok_blocks(anim), ptr_size=8)
                ADS.check_blocks(out)
                QRS.check(out, before, tmp)
                written += 1
        # a reload cut short (dodge, stagger) must not leave a prop in the hand: the holds it returns to unload props
        for name in [IDLE] + SAFETY_ADS:
            if name == IDLE:
                with open(tmp, 'wb') as fh:
                    fh.write(idle_data)
                src = tmp
            else:
                src = os.path.join(ads_oar, 'ADS %s' % label, 'dlc01', name)
            a = anim_skyrim.load_skyrim_animation(src)
            a.annotations.append(anim_skyrim.Annotation(time=0.0, text=R3P.UNEQUIP))
            out = os.path.join(sub, 'dlc01', name)
            anim_skyrim.write_skyrim_animation(out, ADS.havok_blocks(a), ptr_size=8)
            ADS.check_blocks(out)
            written += 1
        ADS.write_config(sub, {
            'name': 'Ramrod 1P %s' % label,
            'description': "Zodd's ramrod reload, first person: the third-person clip of this musket retargeted onto the "
                           "first-person arms and turned up by the head's look-down.",
            'priority': PRIORITY + i,
            'conditions': conds,
        })
        ADS.write_config(quick, {
            'name': 'Ramrod 1P %s, both reload perks' % label,
            'description': 'Quick Reload + Rapid Shot: the first-person ramrod reload retimed %.2fx shorter.' % QRS.STACK_FACTOR,
            'priority': PRIORITY_QUICK + i,
            'conditions': QRS.BOTH_PERKS + conds,
        })
    ADS.write_config(oar1, {
        'name': R3P.MOD, 'author': 'Zenderal',
        'description': "Zodd's ramrod reload in first person, retargeted from the third-person set. Not for distribution "
                       "without Zodd's permission.",
    })
    os.remove(tmp)
    print('built %s: %d meshes, %d clips' % (oar1, len(labels), written))


if __name__ == '__main__':
    main()
