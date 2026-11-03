"""Build the `Zenderal - Musket Ramrod Reload` MO2 mod: Zodd's ramrod reload on Ordo Legionis' 14 muskets, third person.

Zodd's 4 ramrod-loaded muskets animated (Nexus 191481, Zodd) ships five third-person DAR clips (raise, aimed hold,
hip hold, shot, reload) for four GLEN-MORIL muskets (`IsEquippedRight("Glenmoril.esm" | ...)`, not in the list):
folder 90070009 ("ramrod", one musket) and 90070010 ("ramrod fat", three). No first-person clips, no anim object:
the ramrod work is in the hands. The shot fires at 0.2 s and the shot clip carries the whole ramrod reload (5.1 s,
`arrowAttach` at 1.567 s): after a shot the game never sends `reloadStart` (traced, SpellAimTrace 1.3.0), so Zodd's
separate 4.43 s reload clip plays only when the game does (e.g. drawing an unloaded musket).

The clips are made for a gun whose muzzle is ~55 units from its grip origin (measured 2026-11-01: the left hand
works at the muzzle 51-72 units out along the barrel). Ordo's muzzles sit 33-90 units out, so on long guns the hand
rammed mid-barrel and on blunderbuss/musketoons it rammed air. Per mesh, this slides the gun along its own barrel
through the right hand while that hand holds the barrel (Zodd's right hand regrips from the stock wrist to the
barrel and back during the reload): the Weapon bone's local translation moves by -w*delta along the gun's axis,
delta = the mesh's muzzle distance - ZODD_MUZZLE, w = 0 with the right hand at its stock grip and 1 at its barrel
grip (smoothstep in between). The muzzle then sits where Zodd's left hand works; the right hand ends further up or
down the barrel. Nothing changes while the gun is held at the stock (raise, holds, the shot).

Props (curator's request 2026-11-01: "a pellet and stick loading with the left hand"): the shot and reload clips get
a lead ball and a ramrod in the left hand through `AnimObjectL` (see props(); meshes and ANIO records by tools/11).
Every clip in the submod starts with `AnimObjectUnequip`, so a reload cut short can't leave a prop in the hand.
Loading sounds (2026-11-02): two `SoundPlay` events from the moment the ball reaches the muzzle (SOUNDS; the SNDRs by
tools/11, the .wavs by tools/12).

Per mesh, two OAR submods keyed on its WEAPs (IsEquipped, right hand), third person only:
  `Ramrod <mesh>`                       432500+i: raise, holds, shot, reload (variant by barrel thickness)
  `Ramrod <mesh>, both reload perks`    432550+i: the reload retimed like Quick Reload Stack (src/Prophecy/tools/04)
Sneak (2026-11-01): Zodd ships no sneak clips, so `sneakcrossbow_release`/`_reload` are his standing ones crouched
(crouch(): lower body from `sneakmtidle`, chest kept upright, as deep as the gun's fit allows: 80-90% for the two
longest) between DAR Rifles' sneak hold and the crouched idle (settle()). The sneak raise and hold stay DAR Rifles'.

PERMISSION: Zodd's page asks for permission before modifying the files or using the assets. This mod contains
modified copies, so it is in `Zenderal.compiler_settings`' Ignore list (never compiled into the list) until Zodd
agrees. Nothing third-party is committed: clips are read from the downloaded archive and written to the MO2 mod.

Usage:  python src/FlintlockOverhaul/tools/09-build-ramrod-reload.py [<modlist root>]   (needs numpy)
"""
import glob
import importlib.util
import io
import math
import os
import shutil
import sys
import zipfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ADS = _load('ads', os.path.join(HERE, '06-build-musket-aim-fix.py'))  # meshes, maths, OAR helpers, QRS
anim_skyrim, QRS, _bsa = ADS.anim_skyrim, ADS.QRS, ADS._bsa

MOD = 'Zenderal - Musket Ramrod Reload'
ARCHIVE = "Zodd'S 4 Ramrod Loaded Muskets 191481*.zip"
ZODD_DIR = 'DynamicAnimationReplacer/_CustomConditions/'
VARIANTS = {'slim': '90070009', 'fat': '90070010'}   # "ramrod" / "ramrod fat"
FAT_RADIUS = 2.0           # muzzle radius (units) from which a gun gets the "ramrod fat" hands
ZODD_MUZZLE = 55.0         # muzzle distance from the grip origin the clips are made for (left hand at 51-72)
ANIMS_3P = ['meshes', 'actors', 'character', 'animations']
OAR = ANIMS_3P + ['OpenAnimationReplacer', MOD]
SKELETON = '\\'.join(['meshes', 'actors', 'character', 'character assets', 'skeleton.hkx'])
CLIPS = ['crossbow_aim.hkx', 'crossbow_idledrawn.hkx', 'crossbow_idleheld.hkx', 'crossbow_release.hkx', 'crossbow_reload.hkx']
# Sneak (curator 2026-11-01: "apply these animations to the stealth / crouch too"; Zodd ships none): the sneak shot and
# reload are his standing ones crouched (crouch()), starting on the sneak hold that wins for the muskets (DAR Rifles'
# 432101) and ending on what the 1hm graph plays next: SneakCrossBowLoweredState -> `sneakmtidle.hkx` (1P and 3P,
# vanilla wins for muskets: Dynamic Bow Animation's sneak idles are bow-only, RaySense Cover is off).
SNEAK = {'sneakcrossbow_release.hkx': 'crossbow_release.hkx', 'sneakcrossbow_reload.hkx': 'crossbow_reload.hkx'}
SNEAK_IDLE = 'sneakmtidle.hkx'
SNEAK_HOLD = ['DynamicAnimationReplacer', '_CustomConditions', '432101', 'dlc01', 'sneakcrossbow_idledrawn.hkx']
HOLD_SHOT = 0.30           # the sneak shot keeps the sneak hold until here (shot at 0.2 s) ...
BLEND_IN = 0.80            # ... and is in the crouched motion by here (tools/10's first-person values)
BLEND_IN_RELOAD = 0.30     # the sneak reload blends in from the crouched idle the graph enters it from
BLEND_OUT = 1.00           # both end on the crouched idle over their last second
ON_GUN = 20.0              # a pose's left hand is on the gun when it is this close to the gun's origin
CROUCH_STEP = 0.1          # a gun that does not fit at full crouch (its butt would go into the ground while its muzzle
                           # meets the ramming hand: the long guns) crouches this much less per try
DWARVEN = {'sneakcrossbow_release.hkx': 'sneakcrossbow_releasedwarven.hkx',
           'sneakcrossbow_reload.hkx': 'sneakcrossbow_reloaddwarven.hkx',
           'crossbow_aim.hkx': 'crossbow_aimdwarven.hkx', 'crossbow_idledrawn.hkx': 'crossbow_idledrawndwarven.hkx',
           'crossbow_release.hkx': 'crossbow_releasedwarven.hkx', 'crossbow_reload.hkx': 'crossbow_reloaddwarven.hkx'}
SLIDE = ('crossbow_release.hkx', 'crossbow_reload.hkx')
GROUND_CLEARANCE = 1.0     # the gun's lowest point stays this far above the actor's root (the ground)
PRIORITY = 432500          # above DAR Rifles' 432101-432103 and Quick Reload Stack's 432300/432301
PRIORITY_QUICK = 432550
# Props (tools/11 writes their meshes and ANIO records): a ball and a ramrod in the left hand, through `AnimObjectL`
PROP_PLUGIN = 'Zenderal - Musket Ramrod Reload.esp'
BALL_EDID = 'ZEN_RamrodBall'
ROD_EDID = 'ZEN_Ramrod_%s'         # % mesh label: one rod per musket, as long as its barrel allows
UNEQUIP = 'AnimObjectUnequip'      # every vanilla ANIO's unload event; 1hm_behavior (1P and 3P) knows it
LOAD_LEAD = 0.2            # AnimObjLoad this long before AnimObjDraw (Eating Animations and Sounds' spacing)
BALL_DROP = 0.15           # the ball leaves the fingers for the muzzle over this long before it is unloaded
BALL_RADIUS = 1.3          # a .69-calibre ball is ~1.2 units across; larger reads in first person (tools/11 builds it);
                           # at 0.85 it could barely be seen in the hand (curator, 2026-11-01)
FINGER_TIP = 0.7           # a finger's tip lies this fraction of its middle segment past its last joint
ROD_EASE = 0.15            # the left hand eases onto the rod over this long before the grab and after the stow
ROD_GAP = 0.6              # the stowed rod lies this far below the barrel (rod line = bore axis + down * (r + gap))
ROD_SHORT = 12.0           # rod length = the muzzle's distance from the grip origin - this
ROD_TOP_STOWED = -1.0      # the stowed rod's top end, along the bore from the muzzle face
ROD_ABOVE_FIST = 3.0       # in the bore, this much rod shows above the fist
FIST_ABOVE_MUZZLE = 2.5    # in the bore the fist stays this far above the muzzle face (Zodd's hand went 7 below it)
REGRIP_DIST = 6.0          # the left hand holds the stock again from the frame it stays this close to its last pose
# Loading sounds (2026-11-02, curator: "add load 7 then load 1 sound effect here when the reload animation puts the ball
# in the barrel"): `SoundPlay.<SNDR>` as the ball reaches the muzzle, the second once the first has died away (Motion
# Array's BBRealSound "Gun Reload And Load 7", its leading silence trimmed by tools/12, stays within 30 dB of its
# loudest 50 ms for 1.20 s; tools/12 checks it). Both 1hm graphs list a bare `SoundPlay`, so no behavior patch is
# needed; tools/10 copies the events into first person. The SNDRs are tools/11's, the .wavs tools/12's (licensed, not
# committed).
SOUNDS = (('ZEN_MusketLoad7', 0.0), ('ZEN_MusketLoad1', 1.2))   # (EditorID, seconds after the ball reaches the muzzle)


class Rig3P:
    def __init__(self, skeleton):
        self.parents = skeleton.parents
        self.ref = skeleton.reference_pose
        self.index = {n: i for i, n in enumerate(skeleton.bones)}
        self.weapon = self.index['Weapon']
        self.rhand = self.index['NPC R Hand [RHnd]']
        self.lfinger = self.index['NPC L Finger20 [LF20]']
        assert self.parents[self.weapon] == self.rhand, 'Weapon is not a child of the right hand'

    def world(self, anim, f):
        out = [None] * len(self.parents)
        for i, p in enumerate(self.parents):
            if i < len(anim.tracks):
                t = anim.tracks[i]
                local = ADS.trs(t.translations[f], t.rotations[f], t.scales[f][0])
            else:
                r = self.ref[i]
                local = ADS.trs(r.translation, r.rotation, r.scale[0])
            out[i] = local if p < 0 else out[p] @ local
        return out

    def in_weapon(self, anim, f, bone):
        w = self.world(anim, f)
        return (np.linalg.inv(w[self.weapon]) @ w[bone])[:3, 3]


def muzzle(V):
    """(distance along the barrel, radius) of the muzzle face, mesh space (+Y forward)."""
    ymax = V[:, 1].max()
    ring = V[V[:, 1] > ymax - 0.6]
    return float(ymax), float((ring[:, 2].max() - ring[:, 2].min()) / 2)


def slide(rig, anim, delta, V):
    """Move the gun along its own axis by -w*delta through the right hand (see the docstring), then keep its lowest
    point at least GROUND_CLEARANCE above the actor's root (the ground). Before the ram Zodd swings the gun muzzle-down
    (47 deg, reload 0.54-0.67 s / shot 1.21-1.34 s): his 55-unit gun clears the ground, the long Ordo guns dug their
    muzzles 6-13 units in. A slide moves every point of the gun by -amount * (its forward axis' world z), so the
    clearance is a bound on the amount: an upper one while the muzzle points up, a lower one while it points down (the
    gun then slides back through the right hand, briefly, just far enough). Returns (max w, frames adjusted)."""
    ys = [rig.in_weapon(anim, f, rig.rhand)[1] for f in range(anim.num_frames)]
    rest, grip = ys[0], max(ys)
    if grip - rest < 10:
        return 0.0, 0
    pts = np.c_[V, np.ones(len(V))].T
    tr = anim.tracks[rig.weapon]
    wmax, capped = 0.0, 0
    for f, y in enumerate(ys):
        u = min(1.0, max(0.0, (y - rest) / (grip - rest)))
        w = u * u * (3 - 2 * u)
        wmax = max(wmax, w)
        amount = w * delta
        wp = rig.world(anim, f)[rig.weapon]
        lowest = (wp @ pts)[2].min()                     # with no slide
        az = wp[2, 1] / np.linalg.norm(wp[:3, 1])        # lowest(amount) = lowest - amount * az
        if az > 1e-3 and lowest - amount * az < GROUND_CLEARANCE:
            amount = (lowest - GROUND_CLEARANCE) / az
            capped += 1
        elif az < -1e-3 and lowest - amount * az < GROUND_CLEARANCE:
            amount = (GROUND_CLEARANCE - lowest) / -az
            capped += 1
        r = ADS.quat_mat(tr.rotations[f])
        s = tr.scales[f][0]
        tr.translations[f] = [float(v) for v in np.array(tr.translations[f]) + r @ np.array([0.0, -amount * s, 0.0])]
    return wmax, capped


def ram_gap(rig, anim, ymuzzle):
    """Smallest distance along the barrel between the left hand's middle finger and the muzzle, over the frames where
    that hand is out at the barrel's far end (the ramming)."""
    best = None
    for f in range(anim.num_frames):
        p = rig.in_weapon(anim, f, rig.lfinger)
        if p[1] > 30:
            gap = abs(p[1] - ymuzzle)
            best = gap if best is None else min(best, gap)
    return best


LEFT_ARM = ('NPC L UpperArm [LUar]', 'NPC L Forearm [LLar]', 'NPC L Hand [LHnd]')


def rot_between(a, b):
    """Smallest rotation matrix turning unit vector a onto unit vector b."""
    v = np.cross(a, b)
    c = float(a @ b)
    if c < -0.999999:
        axis = np.cross(a, [1.0, 0, 0])
        if np.linalg.norm(axis) < 1e-6:
            axis = np.cross(a, [0, 1.0, 0])
        axis /= np.linalg.norm(axis)
        return 2 * np.outer(axis, axis) - np.eye(3)
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + vx + vx @ vx / (1 + c)


def smooth(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def bore(V):
    """(muzzle centre, unit bore axis, barrel radius) in mesh space: the barrel's centre line, found the way tools/06
    finds the sight line (1-unit slabs back from the muzzle: the barrel's top edge and centre), lowered by the
    muzzle's radius. Ordo's barrels are skewed per mesh (tools/06), so the axis is not the mesh's +Y."""
    ymax, ymin = V[:, 1].max(), V[:, 1].min()
    ring = V[V[:, 1] > ymax - 0.6]
    r = (ring[:, 2].max() - ring[:, 2].min()) / 2
    w = ring[:, 0].max() - ring[:, 0].min()
    cx = (ring[:, 0].max() + ring[:, 0].min()) / 2
    rows, y = [], ymax - 1.0
    while y > ymax - 0.62 * (ymax - ymin):
        s = V[(V[:, 1] > y - 0.5) & (V[:, 1] <= y + 0.5) & (np.abs(V[:, 0] - cx) < w / 2 + 1.5)]
        if len(s) >= 4:
            top = s[:, 2].min()
            upper = s[s[:, 2] < top + 0.5 * r]
            cx = (upper[:, 0].max() + upper[:, 0].min()) / 2
            rows.append((y, cx, top))
        y -= 1.0
    rows = np.array(rows)
    kx, bx, _ = ADS.robust_line(rows[:, 0], rows[:, 1])
    kt, bt, _ = ADS.robust_line(rows[:, 0], rows[:, 2])
    return np.array([kx * ymax + bx, ymax, kt * ymax + bt + r]), ADS.unit(np.array([kx, 1.0, kt])), float(r)


def phases(rig, anim, c, axis):
    """Frames of Zodd's left-hand beats, from its middle finger against the muzzle (`along` the bore from the muzzle
    face, `off` the bore axis) and the hand's height over the pelvis. Shot clip (traced 2026-11-01, ol_musket01): the
    hand leaves the stock (1.07 s), dips to the hip pouch (lowest 1.48), pours at the muzzle (closest 2.35), takes the
    rod from under the barrel (2.85), draws it past the muzzle (3.0), rams twice (3.15-3.45), slides it back home (to
    3.62) and returns to the stock (4.4). The reload clip is the same from 0.67 s on; both hand variants alike."""
    n = anim.num_frames
    along, off, height = np.zeros(n), np.zeros(n), np.zeros(n)
    lh, pelvis = rig.index['NPC L Hand [LHnd]'], rig.index['NPC Pelvis [Pelv]']
    for f in range(n):
        w = rig.world(anim, f)
        rel = (np.linalg.inv(w[rig.weapon]) @ w[rig.lfinger])[:3, 3] - c
        along[f] = rel @ axis
        off[f] = np.linalg.norm(rel - along[f] * axis)
        height[f] = w[lh][2, 3] - w[pelvis][2, 3]
    away = np.flatnonzero(off > 30)
    if not len(away):
        sys.exit('the left hand never leaves the gun')
    trip = [int(away[0])]
    while trip[-1] + 1 < n and off[trip[-1] + 1] > 30:
        trip.append(trip[-1] + 1)
    ball_on = trip[int(np.argmin(height[trip]))]          # the pouch
    f, pour = trip[-1] + 1, []
    while f < n and along[f] > -12:                        # at the muzzle until the hand drops for the rod
        if along[f] > -10:
            pour.append(f)
        f += 1
    dip = []
    while f < n and along[f] < -8:
        dip.append(f)
        f += 1
    if not pour or not dip:
        sys.exit('no pour / rod grab found')
    ball_off = pour[int(np.argmin(off[pour]))]
    grab = dip[int(np.argmin(off[dip]))]
    up = next(g for g in range(grab, n) if along[g] >= 0)
    gone = next(g for g in range(up, n) if off[g] > 16)    # the hand leaves the barrel for the stock
    last_peak = max(g for g in range(up, gone) if along[g] > 8)
    stow = next((g for g in range(last_peak, gone) if along[g] < -4), gone - 1)
    stowed = next((g for g in range(stow, gone) if along[g] < -14), gone - 1)
    return dict(ball_on=ball_on, ball_off=ball_off, grab=grab, up=up, last_peak=last_peak, stow=stow,
                stowed=stowed, rod_off=gone - 1, along=along, off=off)


def set_rotation(anim, bone, f, m):
    tr = anim.tracks[bone]
    q = ADS.mat_quat(m / np.linalg.norm(m[:, 0]))
    if sum(x * y for x, y in zip(q, tr.rotations[f])) < 0:
        q = [-x for x in q]
    tr.rotations[f] = [float(x) for x in q]


def reach(rig, anim, f, shift, rot=None):
    """Move the left hand by `shift` (world), keeping its world rotation (or turning it to `rot`, 3x3 world):
    shoulder-elbow-hand IK, the elbow staying in its own bend plane. Returns how far the hand ended from the target
    (0 unless it is out of reach)."""
    iu, ifa, ih = (rig.index[n] for n in LEFT_ARM)
    w = rig.world(anim, f)
    S, E0, H0 = w[iu][:3, 3], w[ifa][:3, 3], w[ih][:3, 3]
    H = H0 + shift
    a, b = np.linalg.norm(E0 - S), np.linalg.norm(H0 - E0)
    d = max(np.linalg.norm(H - S), 1e-6)
    dc = min(max(d, abs(a - b) + 1e-3), a + b - 1e-3)
    u = (H - S) / d
    v = (E0 - S) - u * ((E0 - S) @ u)
    v = v / np.linalg.norm(v) if np.linalg.norm(v) > 1e-6 else ADS.unit(np.cross(u, [0, 0, 1.0]))
    cos_a = (a * a + dc * dc - b * b) / (2 * a * dc)
    E = S + a * (cos_a * u + math.sqrt(max(0.0, 1 - cos_a * cos_a)) * v)
    q1 = rot_between(ADS.unit(E0 - S), ADS.unit(E - S))
    upper = q1 @ w[iu][:3, :3]
    q2 = rot_between(ADS.unit(q1 @ (H0 - E0)), ADS.unit(H - E))
    fore = q2 @ q1 @ w[ifa][:3, :3]
    set_rotation(anim, iu, f, w[rig.parents[iu]][:3, :3].T @ upper)
    set_rotation(anim, ifa, f, upper.T @ fore)
    set_rotation(anim, ih, f, fore.T @ (w[ih][:3, :3] if rot is None else rot))
    return float(np.linalg.norm(rig.world(anim, f)[ih][:3, 3] - H))


def place(anim, bone, f, parent_world, target):
    """Set `bone`'s local transform at frame f so that its world transform is `target` (4x4, unit scale)."""
    local = np.linalg.inv(parent_world) @ target
    tr = anim.tracks[bone]
    tr.translations[f] = [float(x) for x in local[:3, 3]]
    set_rotation(anim, bone, f, local[:3, :3])
    tr.scales[f] = [1.0, 1.0, 1.0]


def props(rig, anim, label, c, axis, radius):
    """The ball and the ramrod in the left hand (AnimObjectL), with their annotations. Returns (annotations added,
    beats in seconds, worst hand miss).

    Ball: drawn at the pouch, between the thumb and index tips one radius out from the palm, moved into the muzzle over its last
    BALL_DROP and unloaded there. Ramrod: drawn as the hand takes it from its stowed place under the barrel (the rod
    line ROD_GAP below the barrel), drawn up into the bore line as the hand passes the muzzle, rammed with the fist
    held FIST_ABOVE_MUZZLE over the muzzle face, slid back under the barrel and unloaded as the hand leaves for the
    stock. Zodd's ramming hand works 8-16 units off Ordo's bores (his muskets are built differently), so the left
    hand is eased onto the rod line (shoulder-elbow-hand IK, its rotation kept) from ROD_EASE before the grab to
    ROD_EASE after the stow; tools/10 inherits all of it in first person. The loading SOUNDS start as the ball reaches
    the muzzle."""
    fd, n = anim.frame_duration, anim.num_frames
    iao, ih = rig.index['AnimObjectL'], rig.index['NPC L Hand [LHnd]']
    lf01, lf02 = rig.index['NPC L Finger01 [LF01]'], rig.index['NPC L Finger02 [LF02]']
    lf11, lf12 = rig.index['NPC L Finger11 [LF11]'], rig.index['NPC L Finger12 [LF12]']
    if len(anim.tracks) <= max(iao, lf12):
        sys.exit('clip has no AnimObjectL / finger tracks')
    ao = rig.ref[iao]
    grip_local = ADS.trs(ao.translation, ao.rotation, ao.scale[0])
    down = ADS.unit(np.array([0, 0, 1.0]) - axis * axis[2])    # meshes are built upside down: +Z is down
    basis = np.eye(4)
    basis[:3, :3] = np.column_stack([np.cross(axis, -down), axis, -down])   # rod mesh: +Y up the rod, top end at 0
    ph = phases(rig, anim, c, axis)
    t = lambda f: f * fd  # noqa: E731

    shortest = int(math.ceil(0.1 / fd))   # no faster switch between the two lines than 0.1 s

    def bore_weight(f):        # 0 = stowed line under the barrel, 1 = the bore
        rise = smooth((f - ph['grab']) / max(shortest, ph['up'] - ph['grab']))
        return min(rise, 1.0 - smooth((f - ph['stow']) / max(shortest, ph['stowed'] - ph['stow'])))

    def line(b):
        return c + down * (radius + ROD_GAP) * (1 - b)

    worst = 0.0
    g_grab = None
    load_rod = t(ph['grab']) - LOAD_LEAD
    rod_frames = range(max(0, int(math.floor(load_rod / fd))), min(n, ph['rod_off'] + 1))
    for f in range(n):
        k = smooth((t(f) - (t(ph['grab']) - ROD_EASE)) / ROD_EASE) * (1 - smooth((t(f) - t(ph['rod_off'])) / ROD_EASE))
        b = bore_weight(f) if ph['grab'] <= f <= ph['rod_off'] else 0.0
        w = rig.world(anim, f)
        wpn = w[rig.weapon]
        grip = np.linalg.inv(wpn) @ (w[ih] @ grip_local)[:, 3]
        g_along = (grip[:3] - c) @ axis
        t_along = g_along + b * max(0.0, FIST_ABOVE_MUZZLE - g_along)
        if k > 0:   # Zodd's arm is straight at the stroke tops: slide the fist down the rod line to within reach
            iu, ifa = rig.index[LEFT_ARM[0]], rig.index[LEFT_ARM[1]]
            S = w[iu][:3, 3]
            arm = np.linalg.norm(w[ifa][:3, 3] - S) + np.linalg.norm(w[ih][:3, 3] - w[ifa][:3, 3]) - 0.05
            q = (np.linalg.inv(wpn) @ np.r_[S + (w[ih] @ grip_local)[:3, 3] - w[ih][:3, 3], 1])[:3] - line(b)
            s0 = q @ axis
            perp = np.linalg.norm(q - s0 * axis)
            if perp < arm:
                h = math.sqrt(arm * arm - perp * perp)
                t_along = min(max(t_along, s0 - h), s0 + h)
        target = line(b) + axis * t_along
        if f == ph['grab']:
            g_grab = ROD_TOP_STOWED - t_along
        if k > 0:
            worst = max(worst, reach(rig, anim, f, (wpn[:3, :3] @ (target - grip[:3])) * k))
        if f in rod_frames:
            if f <= ph['grab']:
                top = ROD_TOP_STOWED
            else:
                g = g_grab + (ROD_ABOVE_FIST - g_grab) * b
                top = max(t_along + g, ROD_TOP_STOWED)
            m = basis.copy()
            m[:3, 3] = line(b) + axis * top
            w = rig.world(anim, f)
            place(anim, iao, f, w[ih], wpn @ m)
    load_ball = max(fd, t(ph['ball_on']) - LOAD_LEAD)
    for f in range(int(math.floor(load_ball / fd)), ph['ball_off'] + 1):
        w = rig.world(anim, f)
        # between the thumb and index tips, one radius out from the palm: at the last joints (1.0) the ball sat
        # inside the gloved fingers and never showed in game
        thumb = w[lf02][:3, 3] + FINGER_TIP * (w[lf02][:3, 3] - w[lf01][:3, 3])
        index = w[lf12][:3, 3] + FINGER_TIP * (w[lf12][:3, 3] - w[lf11][:3, 3])
        pinch = (thumb + index) / 2
        pinch = pinch + ADS.unit(pinch - w[ih][:3, 3]) * BALL_RADIUS
        muzzle = (w[rig.weapon] @ np.r_[c + axis * -0.6, 1])[:3]
        s = smooth((t(f) - (t(ph['ball_off']) - BALL_DROP)) / BALL_DROP)
        m = w[ih].copy()
        m[:3, :3] /= np.linalg.norm(m[:3, 0])
        m[:3, 3] = pinch + (muzzle - pinch) * s
        place(anim, iao, f, w[ih], m)
    beats = {k: round(t(v), 3) for k, v in ph.items() if k not in ('along', 'off')}
    added = [(0.0, UNEQUIP),
             (load_ball, 'AnimObjLoad.' + BALL_EDID), (t(ph['ball_on']), 'AnimObjDraw.' + BALL_EDID),
             (t(ph['ball_off']), UNEQUIP),
             (load_rod, 'AnimObjLoad.' + ROD_EDID % label), (t(ph['grab']), 'AnimObjDraw.' + ROD_EDID % label),
             (t(ph['rod_off']), UNEQUIP)]
    times = sorted(x for x, _ in added)
    if any(b - a < fd for a, b in zip(times, times[1:])) or load_rod <= t(ph['ball_off']):
        sys.exit('%s: prop beats overlap %s' % (label, beats))
    sounds = [(t(ph['ball_off']) + after, 'SoundPlay.' + edid) for edid, after in SOUNDS]
    if sounds[-1][0] > (n - 1) * fd:
        sys.exit('%s: the last loading sound (%.2f s) is past the clip end' % (label, sounds[-1][0]))
    added += sounds
    taken = [a.time for a in anim.annotations]
    added = [(x + fd if any(abs(x - y) < 0.01 for y in taken) else x, s) for x, s in added]
    for x, s in added:
        anim.annotations.append(anim_skyrim.Annotation(time=round(x, 4), text=s))
    return added, beats, worst


def quick_clip(data, tmp, out):
    """Quick Reload Stack's retime of a reload clip (its bytes), written to `out` and checked; the loading sounds after
    the first keep their gap to it (SOUNDS: a sound is no shorter when the clip is)."""
    anim, (dur, frames, anns) = QRS.retime(data, tmp)
    first_name = 'SoundPlay.' + SOUNDS[0][0]
    later = {'SoundPlay.' + e: after - SOUNDS[0][1] for e, after in SOUNDS[1:]}
    first = next((a.time for a in anim.annotations if a.text == first_name), None)
    if first is not None:
        for i, a in enumerate(anim.annotations):
            if a.text in later:
                a.time = round(first + later[a.text], 4)
                if a.time > anim.duration:
                    sys.exit('%s: %s at %.3f s is past the faster clip\'s end (%.3f s)' % (out, a.text, a.time,
                                                                                         anim.duration))
                anns[i] = (a.time * QRS.STACK_FACTOR, a.text)   # QRS.check expects every time / STACK_FACTOR
    anim_skyrim.write_skyrim_animation(out, ADS.havok_blocks(anim), ptr_size=8)
    ADS.check_blocks(out)
    QRS.check(out, (dur, frames, anns), tmp)


def carry(rig, anim, rod_off):
    """Keep the left hand on the gun from the stow until it holds the stock again. Zodd's hand lets go under the barrel
    as the rod is stowed (rod_off), passes back over the top of the gun (up to 17 units above it) while the gun swings
    from muzzle-up to level under it, and only takes the stock again at 4.36 s (shot clip): in game the gun dipped
    below the hand (curator, 2026-11-01). Instead, its pose relative to the gun eases (smoothstep; position lerped,
    rotation slerped) from where it let go to the first frame it stays within REGRIP_DIST of its last pose, the arm
    solved onto it; where that is out of the arm's reach (the long guns' forestock early on), the hand slides along the
    gun to the nearest point in reach. Returns (first and last frame moved, worst miss, longest slide)."""
    iu, ifa, ih = (rig.index[b] for b in LEFT_ARM)
    n = anim.num_frames
    rel = []
    for f in range(n):
        w = rig.world(anim, f)
        rel.append(np.linalg.inv(w[rig.weapon]) @ w[ih])
    home, on = rel[-1][:3, 3], n - 1
    while on - 1 > rod_off and np.linalg.norm(rel[on - 1][:3, 3] - home) < REGRIP_DIST:
        on -= 1
    ends = [(m[:3, 3], ADS.mat_quat(m[:3, :3] / np.linalg.norm(m[:3, 0]))) for m in (rel[rod_off], rel[on])]
    worst, slid = 0.0, 0.0
    for f in range(rod_off + 1, on):
        s = smooth((f - rod_off) / (on - rod_off))
        m = ADS.trs(ADS.lerp(ends[0][0], ends[1][0], s), ADS.slerp(ends[0][1], ends[1][1], s), 1.0)
        w = rig.world(anim, f)
        target = w[rig.weapon] @ m
        S, H = w[iu][:3, 3], target[:3, 3]
        arm = np.linalg.norm(w[ifa][:3, 3] - S) + np.linalg.norm(w[ih][:3, 3] - w[ifa][:3, 3]) - 0.05
        if np.linalg.norm(H - S) > arm:
            r, q = ADS.unit(w[rig.weapon][:3, 1]), H - S
            disc = (q @ r) ** 2 - (q @ q - arm * arm)
            if disc >= 0:
                k = min((-(q @ r) + math.sqrt(disc), -(q @ r) - math.sqrt(disc)), key=abs)
                H = H + k * r
                slid = max(slid, abs(k))
        worst = max(worst, reach(rig, anim, f, H - w[ih][:3, 3], target[:3, :3]))
    return (rod_off + 1, on - 1), worst, slid


def subtree(rig, name):
    out = {rig.index[name]}
    for i, p in enumerate(rig.parents):          # parents come before their children
        if p in out:
            out.add(i)
    return out


def frame_pose(anim, f):
    """One frame of a clip: [(translation, rotation, scale)] per track."""
    return [(list(t.translations[f]), list(t.rotations[f]), list(t.scales[f])) for t in anim.tracks]


def pose_world(rig, pose):
    out = [None] * len(rig.parents)
    for i, p in enumerate(rig.parents):
        if i < len(pose):
            t, q, s = pose[i]
            local = ADS.trs(t, q, s[0])
        else:
            r = rig.ref[i]
            local = ADS.trs(r.translation, r.rotation, r.scale[0])
        out[i] = local if p < 0 else out[p] @ local
    return out


def crouch(rig, anim, low, depth):
    """Zodd's standing clip, crouched: every bone outside `NPC Spine2`'s subtree (root, pelvis, legs, lower spine)
    plays `low` (looped, by time; blended with Zodd's own standing ones by `depth`, 1 = full crouch), and Spine2 turns
    so the chest keeps Zodd's orientation in the actor's frame. Everything above rides on it unchanged: arms, gun and
    props move as standing, only lower (eye 112 -> ~93 at full depth)."""
    upper = subtree(rig, 'NPC Spine2 [Spn2]')
    s1, s2 = rig.index['NPC Spine1 [Spn1]'], rig.index['NPC Spine2 [Spn2]']
    for f in range(anim.num_frames):
        chest = rig.world(anim, f)[s2][:3, :3]
        fl = int(round(f * anim.frame_duration / low.frame_duration)) % low.num_frames
        for i, tr in enumerate(anim.tracks):
            if (i not in upper or i == s2) and i < len(low.tracks):
                lt = low.tracks[i]
                tr.translations[f] = ADS.lerp(tr.translations[f], lt.translations[fl], depth)
                tr.rotations[f] = ADS.slerp(tr.rotations[f], lt.rotations[fl], depth)
                tr.scales[f] = ADS.lerp(tr.scales[f], lt.scales[fl], depth)
        set_rotation(anim, s2, f, rig.world(anim, f)[s1][:3, :3].T @ (chest / np.linalg.norm(chest[:, 0])))


def settle(rig, anim, start, end, hold, blend_in):
    """Bone-by-bone blends of a crouched clip: `start` (a pose) until `hold`, into the motion by `blend_in`, and into
    `end` (what the graph plays next) over the last BLEND_OUT. Bone by bone the left hand would pass through the gun
    (first person, 2026-11-01), so its grip relative to the gun is blended instead and the arm solved onto it (as
    tools/10's left_on_gun). Returns the worst hand miss."""
    ih = rig.index[LEFT_ARM[2]]

    def grip(w):
        m = np.linalg.inv(w[rig.weapon]) @ w[ih]
        return m[:3, 3], ADS.mat_quat(m[:3, :3] / np.linalg.norm(m[:3, 0]))

    def mix(a, b, s):            # (translation, rotation[, scale]) blended
        out = (ADS.lerp(a[0], b[0], s), ADS.slerp(a[1], b[1], s))
        if len(a) == 3:
            k = a[2][0] + (b[2][0] - a[2][0]) * s
            out += ([k, k, k],)
        return out

    g_start, g_end = grip(pose_world(rig, start)), grip(pose_world(rig, end))
    # only a pose whose left hand is on the gun gets the grip blend: `sneakmtidle` (the bow's crouched idle too) hangs
    # it at the hip, ~68 units from the gun, so the hand leaves the gun into it bone by bone
    on_start, on_end = (np.linalg.norm(g[0]) < ON_GUN for g in (g_start, g_end))
    worst = 0.0
    for f in range(anim.num_frames):
        t = f * anim.frame_duration
        w_in = smooth((t - hold) / (blend_in - hold))
        w_out = smooth((t - (anim.duration - BLEND_OUT)) / BLEND_OUT)
        if w_in >= 1 and w_out <= 0:
            continue
        g = grip(rig.world(anim, f))
        for i, tr in enumerate(anim.tracks):
            m = (tr.translations[f], tr.rotations[f], tr.scales[f])
            m = mix(mix(start[i], m, w_in), end[i], w_out)
            tr.translations[f], tr.rotations[f], tr.scales[f] = [list(map(float, x)) for x in m]
        if 0 < w_in < 1 and on_start:
            g = mix(g_start, g, w_in)
        elif 0 < w_out < 1 and on_end:
            g = mix(g, g_end, w_out)
        else:
            continue
        w = rig.world(anim, f)
        target = w[rig.weapon] @ ADS.trs(g[0], g[1], 1.0)
        worst = max(worst, reach(rig, anim, f, target[:3, 3] - w[ih][:3, 3], target[:3, :3]))
    return worst


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else ADS.TOOLS['modlistRoot']
    mods_dir = os.path.join(root, 'mods')
    profile, mods = QRS.profile_mods(root)
    found = glob.glob(os.path.join(root, 'downloads', ARCHIVE))
    if len(found) != 1:
        sys.exit('expected one %s in %s/downloads, found %d' % (ARCHIVE, root, len(found)))
    zf = zipfile.ZipFile(found[0])
    names = {n.replace('\\', '/'): n for n in zf.namelist()}
    tmp = os.path.join(os.environ.get('TEMP', '.'), '_ramrod.hkx')

    def load_zodd(variant, clip):
        hits = [n for n in names if n.endswith(ZODD_DIR + VARIANTS[variant] + '/dlc01/' + clip)]
        if len(hits) != 1:
            sys.exit('%s/%s not in %s' % (VARIANTS[variant], clip, found[0]))
        with open(tmp, 'wb') as fh:
            fh.write(zf.read(names[hits[0]]))
        anim = anim_skyrim.load_skyrim_animation(tmp)
        ADS.check_finite(anim, clip)
        return anim

    bsa = _bsa.listing(os.path.join(root, 'Stock Game', 'Data', 'Skyrim - Animations.bsa'))
    with open(tmp, 'wb') as fh:
        fh.write(_bsa.read(bsa[0], bsa[1][SKELETON]))
    rig = Rig3P(anim_skyrim.load_skyrim_skeleton(tmp))
    low_src, data = QRS.winner(mods_dir, mods, bsa, ANIMS_3P + [SNEAK_IDLE])
    with open(tmp, 'wb') as fh:
        fh.write(data)
    low = anim_skyrim.load_skyrim_animation(tmp)
    hold_path = next((p for p in (QRS.find_ci(os.path.join(mods_dir, m), ANIMS_3P + SNEAK_HOLD) for m in mods) if p), None)
    if not hold_path:
        sys.exit('no %s in the active profile' % '/'.join(SNEAK_HOLD))
    sneak_hold = frame_pose(anim_skyrim.load_skyrim_animation(hold_path), 0)
    low_pose = frame_pose(low, 0)
    print('crouched idle: %s from %s; sneak hold: %s' % (SNEAK_IDLE, low_src, hold_path))

    groups = []
    for mesh_rel, weapons in sorted(ADS.muskets().items()):
        mod, path = ADS.winning_loose(mods_dir, mods, mesh_rel)
        V = ADS.mesh_surface(path)
        ymuz, radius = muzzle(V)
        groups.append((mesh_rel, sorted(weapons), ymuz, radius, V[::7], bore(V)))
    out_mod = os.path.join(mods_dir, MOD)
    if os.path.isdir(out_mod):
        shutil.rmtree(out_mod)
    oar = os.path.join(out_mod, *OAR)
    written = 0
    for i, (mesh_rel, weapons, ymuz, radius, V, (bore_c, bore_axis, bore_r)) in enumerate(groups):
        label = os.path.basename(mesh_rel).replace('_animated.nif', '')
        variant = 'fat' if radius >= FAT_RADIUS else 'slim'
        delta = ymuz - ZODD_MUZZLE
        sub = os.path.join(oar, 'Ramrod %s' % label)
        quick = os.path.join(oar, 'Ramrod %s, both reload perks' % label)
        os.makedirs(os.path.join(sub, 'dlc01'))
        os.makedirs(os.path.join(quick, 'dlc01'))
        print('%s (%s): muzzle %.1f units out (delta %+.1f), radius %.2f -> %s hands; bore yaw %+.1f tilt %+.1f deg'
              % (label, ', '.join(e for e, _ in weapons), ymuz, delta, radius, variant,
                 math.degrees(math.atan2(bore_axis[0], bore_axis[1])), math.degrees(math.atan2(-bore_axis[2], bore_axis[1]))))
        def build_clip(clip, source, sneak):
            nonlocal written
            depth = 1.0
            while True:   # crouched, the long guns' butts reach the ground before their muzzles reach the ramming hand
                anim = load_zodd(variant, source)
                if sneak:
                    crouch(rig, anim, low, depth)
                before = ram_gap(rig, anim, ZODD_MUZZLE) if source in SLIDE else None
                wmax, capped = slide(rig, anim, delta, V) if source in SLIDE else (0.0, 0)
                after = ram_gap(rig, anim, ymuz) if source in SLIDE else None   # before the props move the left hand
                if not sneak:
                    break
                try:
                    phases(rig, anim, bore_c, bore_axis)
                    fits = after <= before + 1.0
                except (ValueError, StopIteration):
                    fits = False
                if fits:
                    break
                if depth <= 0:
                    sys.exit('%s %s: no crouch depth fits the ramming' % (label, clip))
                depth = round(depth - CROUCH_STEP, 2)
            if sneak:
                print('  %-24s crouched to %d%%' % (clip, round(100 * depth)))
            if source in SLIDE:
                added, beats, miss = props(rig, anim, label, bore_c, bore_axis, bore_r)
                print('  %-24s props: %s; left hand within %.2f of the rod' % (
                    clip, ', '.join('%s %.2f' % (k, v) for k, v in beats.items()), miss))
                if miss > 0.5:
                    sys.exit('%s %s: the left hand cannot reach the rod (%.2f units short)' % (label, clip, miss))
                (c0, c1), miss, slid = carry(rig, anim, int(round(beats['rod_off'] / anim.frame_duration)))
                print('  %-24s left hand kept on the gun %.2f-%.2f s (within %.2f, slid up to %.1f along it)' % (
                    clip, c0 * anim.frame_duration, c1 * anim.frame_duration, miss, slid))
                if miss > 0.5:
                    sys.exit('%s %s: the left hand cannot stay on the gun (%.2f units short)' % (label, clip, miss))
            else:   # a reload cut short (dodge, stagger) must not leave a prop in the hand
                added = [(0.0, UNEQUIP)]
                anim.annotations.append(anim_skyrim.Annotation(time=0.0, text=UNEQUIP))
            if sneak:
                shot = source == 'crossbow_release.hkx'
                miss = settle(rig, anim, sneak_hold if shot else low_pose, low_pose,
                              HOLD_SHOT if shot else 0.0, BLEND_IN if shot else BLEND_IN_RELOAD)
                print('  %-24s crouched; %s -> motion -> %s, left hand kept on the gun within %.2f'
                      % (clip, 'sneak hold' if shot else SNEAK_IDLE, SNEAK_IDLE, miss))
                if miss > 0.5:
                    sys.exit('%s %s: the left hand cannot stay on the gun in the blends (%.2f units short)' % (label, clip, miss))
            for name in [clip] + ([DWARVEN[clip]] if clip in DWARVEN else []):
                out = os.path.join(sub, 'dlc01', name)
                anim_skyrim.write_skyrim_animation(out, anim, ptr_size=8)
                ADS.check_blocks(out)
                written += 1
            got = anim_skyrim.load_skyrim_animation(os.path.join(sub, 'dlc01', clip))
            src = load_zodd(variant, source)
            if got.num_frames != src.num_frames or abs(got.duration - src.duration) > 1e-4 or \
                    sorted((round(a.time, 4), a.text) for a in got.annotations) != \
                    sorted([(round(a.time, 4), a.text) for a in src.annotations] + [(round(x, 4), s) for x, s in added]):
                sys.exit('%s: timing or annotations changed' % clip)
            # every bone but the Weapon (and the left arm, moved onto the ramrod) must be the source's; crouched, the
            # right hand relative to the chest, between the blends
            s2 = rig.index['NPC Spine2 [Spn2]']
            for b in (rig.rhand,) if source in SLIDE else (rig.rhand, rig.lfinger):
                frames = [f for f in range(0, got.num_frames, 5)
                          if not sneak or BLEND_IN <= f * got.frame_duration <= got.duration - BLEND_OUT]
                rel = (lambda w: np.linalg.inv(w[s2]) @ w[b]) if sneak else (lambda w: w[b])
                worst = max(np.linalg.norm(rel(rig.world(got, f))[:3, 3] - rel(rig.world(src, f))[:3, 3]) for f in frames)
                if worst > 0.5:
                    sys.exit('%s: bone %d moved %.2f units' % (clip, b, worst))
            if source in SLIDE:
                src_low = min((rig.world(src, f)[rig.weapon] @ np.c_[V, np.ones(len(V))].T)[2].min() for f in range(src.num_frames))
                lowest = min((rig.world(got, f)[rig.weapon] @ np.c_[V, np.ones(len(V))].T)[2].min() for f in range(got.num_frames))
                print('  %-24s slide %.0f%% at most, %d frames capped at the ground (gun lowest %.1f); left hand to muzzle '
                      "at the ram: Zodd's gun %.1f units, this one %.1f" % (clip, 100 * wmax, capped, lowest, before, after))
                if after > before + 1.0:
                    sys.exit('%s: the slide left the hand %.1f units from the muzzle' % (label, after))
                if lowest < (GROUND_CLEARANCE - 0.5 if sneak else min(GROUND_CLEARANCE - 0.5, src_low - 0.5)):
                    sys.exit('%s: the gun goes %.1f units into the ground' % (label, -lowest))

        for clip in CLIPS:
            build_clip(clip, clip, False)
        for clip, source in SNEAK.items():
            build_clip(clip, source, True)
        for reload_clip in ('crossbow_reload.hkx', 'sneakcrossbow_reload.hkx'):
            data = open(os.path.join(sub, 'dlc01', reload_clip), 'rb').read()
            for name in (reload_clip, DWARVEN[reload_clip]):
                quick_clip(data, tmp, os.path.join(quick, 'dlc01', name))
                written += 1
        cond = ADS.or_equipped(weapons)
        ADS.write_config(sub, {
            'name': 'Ramrod %s' % label,
            'description': "Zodd's ramrod reload (Nexus 191481, %s), third person: %s (%s). The gun slides %+.1f units "
                           'along its barrel through the right hand while that hand holds the barrel, so its muzzle '
                           "sits where Zodd's hand rams." % (VARIANTS[variant], ', '.join(e for e, _ in weapons), mesh_rel, -delta),
            'priority': PRIORITY + i,
            'conditions': [cond],
        })
        ADS.write_config(quick, {
            'name': 'Ramrod %s, both reload perks' % label,
            'description': 'Quick Reload + Rapid Shot: the ramrod reload retimed %.2fx shorter, as Quick Reload Stack.'
                           % QRS.STACK_FACTOR,
            'priority': PRIORITY_QUICK + i,
            'conditions': QRS.BOTH_PERKS + [cond],
        })
    ADS.write_config(oar, {
        'name': MOD, 'author': 'Zenderal',
        'description': "Zodd's ramrod reload (Zodd's 4 ramrod-loaded muskets animated, Nexus 191481) fitted to each "
                       'Ordo Legionis musket in third person. Not for distribution without Zodd\'s permission.',
    })
    os.remove(tmp)
    print('built %s for profile %s: %d meshes, %d clips' % (out_mod, profile, len(groups), written))


if __name__ == '__main__':
    main()
