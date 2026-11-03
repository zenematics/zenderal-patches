"""Add first-person reloads to `Zenderal - Pistol Ramrod Reload`: tools/01's third-person reloads (either hand)
retargeted onto the first-person arms with src/FlintlockOverhaul/tools/10's Retarget (everything under Spine2 mapped
through the eye with the first-person bone lengths, both hands solved onto the mapped hands, the arms turned by the
head's look-down so the loading happens in view; head, camera and the bones above Spine2 stay first person's own).

What first person plays (2026-11-02): vanilla's staff clips. No list mod replaces the first-person `stfmagic_*`,
`staff_idle` or their right-hand twins, and the first-person magic graph's `StfMagic_Release` carries the third
person's triggers (fire 0.334 s, re-cast window 0.337-0.667 s, the state left only at the clip's end), so a longer clip
holds the reload here too. Per pistol group, the first-person `stfmagic_release` (played for a requested reload only,
tools/01 REQUEST; the third-person clip starts from the hold, tools/01 TRIM):
  - vanilla's `staff_idle` (what the graph shows the pistol in), blended into the retargeted reload by BLEND_IN;
  - blended into vanilla's `staff_idle` again over the last BLEND_OUT, ending on it.
The free arm starts and ends on its first-person rest: the standing unarmed idle `H2H_Idle` (the left hand's
1stP_WeapIdle_MSG -> Weap_H2H_Idle_MSG, the right hand's 0_master LeftHandWeapIdle_MSG, both for an empty free hand),
won by SIGMA Fisting's `h` (FREE_IDLE; either hand unarmed, the right hand not a one-hander), at its least-swaying
frame. Its seam was not seen in game (left hand verified 2026-11-02, "works perfectly"). The Pandora patch's
first-person half (`firstperson~1hm_behavior`, `firstperson~0_master`) hands the arm to the clip for the reload.
Props: the third-person clip's AnimObject offsets (kept by the retarget: AnimObjectR for a left-hand pistol, L for a
right-hand one) and its prop annotations; vanilla's first-person aim clips are copied with `AnimObjectUnequip` at 0.
The right hand (2026-11-02) is the same from tools/01's right-hand clips, on vanilla's `stfmagicright_release` (fire
0.341 s, also held to the clip's end) and `staffright_idle`; it needed the gun at full size in third person too
(LoopPistolAnims' mirror_hkx now moves scale tracks to the partner bone, tools/01 RIGHT_GUN_SCALE).

Two pistols (2026-11-02): tools/01's two-pistol clips the same way. The free arm's rest is the other gun's hold:
vanilla's first-person idle for that hand, frame 0 (in third person traced; first person read from the graph, which is
the same), and the clip ends where the graph hands back: both idles' frame 0 by arm (they agree off the arms, so the
camera does not move), from the third-person clip's DUAL_MOTION_END on. The tucked gun maps below the view.

OAR, first person: `Reload 1P <label>[ (two pistols)][ (right hand)]` at the third-person submod's priority and
conditions. Run after tools/01 (which leaves this folder alone), then tools/02.
Usage:  python src/PistolRamrodReload/tools/04-build-pistol-reload-1p.py [<modlist root>]   (needs numpy)
"""
import importlib.util
import json
import math
import os
import shutil
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PR = _load('pistol_reload', os.path.join(HERE, '01-build-pistol-reload.py'))
R10 = _load('ramrod1p', os.path.join(ROOT, 'src', 'FlintlockOverhaul', 'tools', '10-build-ramrod-reload-1p.py'))
ADS = PR.ADS
anim_skyrim, QRS, _bsa = ADS.anim_skyrim, ADS.QRS, ADS._bsa
smooth, blend, split = PR.smooth, R10.blend, R10.split

OAR_1P = ADS.ANIMS_1P + ['OpenAnimationReplacer', PR.MOD]
BLEND_IN = 0.2             # from the first-person hold into the retargeted reload (the pistol leaves its hold at once)
BLEND_OUT = 0.34           # into vanilla's first-person staff_idle over the clip's last seconds (stowed at 2.32)
SHOT, IDLE = PR.CLIP, PR.IDLE
STOW_SHORT = 3.0           # a melee stow's free hand may fall this short (the sheath, cross-body at the hip, below the
                           # view: the first-person arms are shorter; the left sword's reach missed by 1.5 on 4 frames)
MUZZLE_BELOW = 14.0        # extra arm lift (per barrel) so the muzzle sits this far below the view's centre while
                           # ramming: the head's look-down alone left the whole loading below the screen (rendered
                           # 2026-11-02; at 21:9 and 85 deg the view reaches ~21 deg down)
# Two pistols (2026-11-02, curator: "the arm is upside down" reloading with things in both hands): carrying the other gun
# down to the belly and taking it back (lower -> pouch, regrip -> raise) the third-person elbow sits up to 14 units ahead
# of its wrist, the forearm pointing back at the body, and first person showed that elbow in front of the face (20
# ahead, just under the crosshair) with the forearm hanging back under it. Wherever a third-person elbow is more than
# ELBOW_AHEAD[0] ahead of its wrist, the first-person arm bends its elbow down (and ELBOW_DOWN_OUT out) instead, in full
# ELBOW_AHEAD[1] further on; the hand and what it holds stay put, below the view. The bend fades in and out over
# ELBOW_FADE either side (switched where the third person's elbow drops behind the wrist, the forearm turned 110 deg in
# one frame: 12.6 deg/ms, the one-gun reload's arms never pass 1.4), and only while the hand is below the view: in
# full ELBOW_VIEW[1] degrees under the camera's forward, none from ELBOW_VIEW[0] up (a 16:10 85 deg view reaches 30
# down, 21:9 21). The hand keeps its third-person turn, so under the bent elbow its wrist twists up to 165 deg; faded by
# time alone, the hand came into view still twisted. The one-gun and melee reloads keep their elbows behind the wrist
# (at most 2 ahead): unchanged.
ELBOW_AHEAD = (3.0, 6.0)
ELBOW_DOWN_OUT = 0.5
ELBOW_FADE = 0.12
ELBOW_VIEW = (32.0, 55.0)
FREE_IDLE = ('SIGMA - Fisting animations - 1st person',
             ADS.ANIMS_1P + ['OpenAnimationReplacer', 'Sigma - fists', 'h', 'h2h_idle.hkx'])
FREE_ARM = PR.RIGHT_HALF + PR.RIGHT_IDLE       # first person's RightArm mask, by name (tools/03 asserts the mask)
PROP_EVENTS = ('AnimObjLoad.', 'AnimObjDraw.', PR.UNEQUIP, 'ZenPistolLoaded',   # + the loaded event (tools/01)
               'SoundPlay.', PR.ARM_BACK)                                      # its loading sounds, the melee arm back
RIGHT = ' (right hand)'
# per pistol hand: vanilla's first-person shot and idle, its aim clips, the gun's attach node, the free arm's bones
FREE_ARM_LEFT = [PR.swap_side(n) for n in FREE_ARM]
# `other`: the free arm rests on that vanilla first-person idle's frame 0 (two pistols) instead of FREE_IDLE's
HANDS = {'left': dict(shot=PR.CLIP, idle=PR.IDLE, aim=PR.AIM_CLIPS, gun='Shield', free=FREE_ARM, suffix='',
                      other=None, beats=PR.BEATS, motion_end=None),
         'right': dict(shot=PR.CLIP_RIGHT, idle=PR.IDLE_RIGHT, aim=PR.AIM_CLIPS_RIGHT, gun='Weapon',
                       free=FREE_ARM_LEFT, suffix=RIGHT, other=None, beats=PR.BEATS, motion_end=None),
         'two left': dict(shot=PR.CLIP, idle=PR.IDLE, aim=PR.AIM_CLIPS, gun='Shield', free=FREE_ARM, suffix=PR.DUAL,
                          other=PR.IDLE_RIGHT, beats=PR.DUAL_BEATS, motion_end=PR.DUAL_MOTION_END),
         'two right': dict(shot=PR.CLIP_RIGHT, idle=PR.IDLE_RIGHT, aim=PR.AIM_CLIPS_RIGHT, gun='Weapon',
                           free=FREE_ARM_LEFT, suffix=PR.DUAL + RIGHT, other=PR.IDLE, beats=PR.DUAL_BEATS,
                           motion_end=PR.DUAL_MOTION_END)}
# A melee weapon in the other hand (tools/01 STOW): on the two-pistol timeline, the free arm resting on vanilla's
# first-person one-handed idle (pistol left) or dual-wield idle (pistol right), frame 0; the sheathed weapon maps below
# the view like the tucked gun.
for _typ in sorted(PR.STOW):
    for _female in ((True, False) if _typ in PR.STOW_SEXED else (None,)):
        _sfx = PR.stow_suffix(_typ, _female)
        HANDS['stow left' + _sfx] = dict(shot=PR.CLIP, idle=PR.IDLE, aim=PR.AIM_CLIPS, gun='Shield', free=FREE_ARM,
                                         suffix=_sfx, other=PR.FREE_IDLE_1HM, beats=PR.DUAL_BEATS,
                                         motion_end=PR.DUAL_MOTION_END)
        HANDS['stow right' + _sfx] = dict(shot=PR.CLIP_RIGHT, idle=PR.IDLE_RIGHT, aim=PR.AIM_CLIPS_RIGHT, gun='Weapon',
                                          free=FREE_ARM_LEFT, suffix=_sfx + RIGHT, other=PR.FREE_IDLE_DW,
                                          beats=PR.DUAL_BEATS, motion_end=PR.DUAL_MOTION_END)
# A shield (tools/01 Ctx.shield, right-hand pistol only): first person's MRh_Shd_Blend gives the whole left arm to the
# first-person 1HM_Idle standing (read 2026-11-03), so the free arm rests on vanilla's first-person one-handed idle,
# frame 0; the shield on the back maps behind the view.
# First person's shield style is tools/01 SHIELD_STYLE_1P (2026-11-03: the back sling; on the arm the shield covered the
# view), read from its third-person clips in SHIELD_1P_SOURCES when third person uses the other style (`src`).
_back = PR.SHIELD_STYLE_1P == 'back'
for _female in ((True, False) if _back else (None,)):    # 'arm': the one-gun reload, unsexed
    _sfx = PR.stow_suffix(PR.SHIELD, _female)
    HANDS['stow right' + _sfx] = dict(shot=PR.CLIP_RIGHT, idle=PR.IDLE_RIGHT, aim=PR.AIM_CLIPS_RIGHT, gun='Weapon',
                                      free=FREE_ARM_LEFT, suffix=_sfx + RIGHT, other=PR.FREE_IDLE_1HM,
                                      beats=PR.DUAL_BEATS if _back else PR.BEATS,
                                      motion_end=PR.DUAL_MOTION_END if _back else None,
                                      src=PR.SHIELD_1P_SOURCES if PR.SHIELD_STYLE_1P != PR.SHIELD_STYLE else None)


def clip(tmp, data):
    with open(tmp, 'wb') as fh:
        fh.write(data)
    return anim_skyrim.load_skyrim_animation(tmp)


def rest_pose(idle, bones):
    """{bone: (rotation, scale)} of the free arm's idle at its least-swaying frame (tools/01's free_arm_idle rule)."""
    ang = lambda a, b: math.degrees(2 * math.acos(min(1.0, abs(sum(x * y for x, y in zip(a, b))))))  # noqa: E731
    f = min(range(idle.num_frames), key=lambda f: max(ang(idle.tracks[b].rotations[f], idle.tracks[b].rotations[g])
                                                     for b in bones for g in range(0, idle.num_frames, 6)))
    return {b: (list(idle.tracks[b].rotations[f]), idle.tracks[b].scales[f][0]) for b in bones}


def with_rest(locals_, rest):
    out = [m.copy() for m in locals_]
    for b, (q, s) in rest.items():
        out[b] = ADS.trs(out[b][:3, 3], q, s)
    return out


def muzzle_elevation(rt, a3, f, base, lift_pitch, lift_yaw, c, gun):
    """Degrees above the camera's forward of the muzzle (mesh point c on the gun node), mapped at third-person frame f."""
    _, w1, _ = rt.pose(a3, f, base, lift_pitch, lift_yaw)
    q = np.linalg.inv(PR.unscaled(w1[rt.cam1])) @ (w1[rt.i1[gun]] @ np.r_[c, 1])
    return math.degrees(math.atan2(q[2], q[1]))          # Camera1st: +Y forward, +Z up


def elbow_weights(rt, a3):
    """Per frame of a3 and arm (R10.ARM_SIDES), the weight of the first-person elbow's down bend: from how far the
    third-person elbow is ahead of its wrist (ELBOW_AHEAD), faded over ELBOW_FADE either side."""
    n = a3.num_frames
    raw = np.zeros((n, len(R10.ARM_SIDES)))
    for f in range(n):
        w3 = rt.world3(a3, f)
        fwd = PR.unscaled(w3[0])[:3, 1]
        for s, (_, fa, hand) in enumerate(R10.ARM_SIDES):
            ahead = (w3[rt.i3[fa]][:3, 3] - w3[rt.i3[hand]][:3, 3]) @ fwd
            raw[f, s] = smooth((ahead - ELBOW_AHEAD[0]) / ELBOW_AHEAD[1])
    span = max(1, int(round(ELBOW_FADE / a3.frame_duration)))
    k = raw.copy()
    for f in range(n):
        for g in range(max(0, f - span), min(n, f + span + 1)):
            k[f] = np.maximum(k[f], raw[g] * smooth(1.0 - abs(f - g) / span))
    return k


def drop_elbows(rt, k, loc, w1, targets):
    """The arms re-solved with the elbow bent down and out by their weights k (elbow_weights, one per arm) while the
    hand is below the view (ELBOW_VIEW). Updates loc and w1; returns the largest weight used."""
    cam = PR.unscaled(w1[rt.cam1])
    ci = np.linalg.inv(cam)
    top = 0.0
    for (ua, fa, hand), out, k in zip(R10.ARM_SIDES, (-1.0, 1.0), k):      # left arm out = the camera's -X
        q = (ci @ np.r_[targets[hand][:3, 3], 1])[:3]
        below = math.degrees(math.atan2(-q[2], q[1]))                       # Camera1st: +Y forward, +Z up
        k *= smooth((below - ELBOW_VIEW[0]) / (ELBOW_VIEW[1] - ELBOW_VIEW[0]))
        if k <= 0:
            continue
        arm = rt.i1[ua], rt.i1[fa], rt.i1[hand]
        S = w1[arm[0]][:3, 3]
        down = PR.unit(-cam[:3, 2] + ELBOW_DOWN_OUT * out * cam[:3, 0])    # Camera1st: +X right, +Z up
        d = (1 - k) * PR.unit(targets[fa][:3, 3] - S) + k * down
        d = PR.unit(d) if np.linalg.norm(d) > 1e-3 else down
        rt.solve_arm(loc, w1, arm, targets[hand], S + 10.0 * d)
        rt.refresh(loc, w1, targets)
        top = max(top, k)
    return top


def build(rt, a3, idle, rest, template, c, gun, beats=PR.BEATS, motion_end=None):
    """First-person clip from the third-person clip a3: (anim, worst hand error, frames solved short, extra lift).
    The blend into the idle ends at `motion_end` (a two-pistol clip holds its last pose after it) or the clip's end;
    `beats` and `motion_end` are tools/01's, before its TRIM."""
    n, fd = a3.num_frames, a3.frame_duration
    end_t = motion_end - PR.TRIM if motion_end is not None else a3.duration
    end = with_rest(rt.locals1(idle, 0), rest)
    head = np.array([rt.head_angles(rt.world3(a3, f)) for f in range(n)])
    fr = int(round((beats['rammed'] - PR.TRIM) / fd))
    base = end
    extra = 0.0
    for _ in range(3):    # the lift turns about the eye, so the muzzle's elevation follows it almost one to one
        extra += -MUZZLE_BELOW - muzzle_elevation(rt, a3, fr, base, head[0, 0] - head[fr, 0] + extra,
                                                  head[fr, 1] - head[0, 1], c, gun)
    out = anim_skyrim.load_skyrim_animation(template)
    for t in out.tracks:
        t.translations, t.rotations, t.scales = [], [], []
    worst, short, dropped = 0.0, 0, [0, 0.0]
    bends = elbow_weights(rt, a3)
    for f in range(n):
        t_s = f * fd
        start = end
        w_in = smooth(t_s / BLEND_IN)
        w_out = smooth((t_s - (end_t - BLEND_OUT)) / BLEND_OUT)
        final = start
        if w_in > 0 and w_out < 1:
            lift = head[0, 0] - head[f, 0] + extra * w_in * (1 - w_out)
            loc, w1, targets = rt.pose(a3, f, start, lift, head[f, 1] - head[0, 1])
            k = drop_elbows(rt, bends[f], loc, w1, targets)
            if k > 0:
                dropped = [dropped[0] + 1, max(dropped[1], float(k))]
            for _, _, hand in R10.ARM_SIDES:
                err = float(np.linalg.norm(w1[rt.i1[hand]][:3, 3] - targets[hand][:3, 3]))
                worst = max(worst, err)
                short += err > 0.5
            final = blend(start, loc, w_in)
        final = blend(final, end, w_out)
        for tr, m in zip(out.tracks, final):
            tt, q, s = split(m)
            if tr.rotations and sum(x * y for x, y in zip(q, tr.rotations[-1])) < 0:
                q = [-x for x in q]
            tr.translations.append(tt)
            tr.rotations.append(q)
            tr.scales.append([s, s, s])
    out.duration, out.num_frames, out.frame_duration = a3.duration, n, fd
    out.annotations = [a for a in a3.annotations if a.text.startswith(PROP_EVENTS)]
    return ADS.havok_blocks(out), worst, short, extra, dropped


def check(rt, path, idle, rest, added):
    """Decode: the first and last frames on the idle with the free arm's rest, the props' events."""
    got = anim_skyrim.load_skyrim_animation(path)
    ADS.check_blocks(path)
    world = lambda a, f, r=None: rt.world1(with_rest(rt.locals1(a, f), r) if r else rt.locals1(a, f))  # noqa: E731
    e = world(idle, 0, rest)
    g = world(got, 0)
    d = max(np.linalg.norm(g[i][:3, 3] - e[i][:3, 3]) for i in range(len(g)))
    if d > 0.3:
        sys.exit('%s: the first frame is %.2f off the idle (the reload starts from the hold)' % (path, d))
    g = world(got, got.num_frames - 1)
    gap = max(np.linalg.norm(g[i][:3, 3] - e[i][:3, 3]) for i in range(len(g)))
    if gap > 0.5:
        sys.exit('%s: the last frame is %.2f off the idle' % (path, gap))
    if sorted((round(a.time, 4), a.text) for a in got.annotations) != sorted((round(x, 4), s) for x, s in added):
        sys.exit('%s: annotations differ from the props\' events' % path)
    return got, gap


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else ADS.TOOLS['modlistRoot']
    mods_dir = os.path.join(root, 'mods')
    oar3 = os.path.join(mods_dir, PR.DEPLOY, *PR.OAR)
    if not os.path.isdir(oar3):
        sys.exit('run tools/01 first: %s is missing' % oar3)
    bsa = _bsa.listing(os.path.join(root, 'Stock Game', 'Data', 'Skyrim - Animations.bsa'))
    tmp = os.path.join(os.environ.get('TEMP', '.'), '_pistol_reload_1p.hkx')
    with open(tmp, 'wb') as fh:
        fh.write(_bsa.read(bsa[0], bsa[1][ADS.SKELETON]))
    sk1 = anim_skyrim.load_skyrim_skeleton(tmp)
    with open(tmp, 'wb') as fh:
        fh.write(_bsa.read(bsa[0], bsa[1][R10.R3P.SKELETON]))
    sk3 = anim_skyrim.load_skyrim_skeleton(tmp)
    rt = R10.Retarget(sk1, sk3)
    profile, mods = QRS.profile_mods(root)
    vanilla, floats = {}, {}
    for name in sorted({n for h in HANDS.values() for n in [h['shot'], h['idle']] + h['aim'] + [h['other'] or h['idle']]}):
        src, data = QRS.winner(mods_dir, mods, bsa, ADS.ANIMS_1P + [name])
        vanilla[name] = clip(tmp, data)
        floats[name] = PR.HF.read(data)  # node visibility: written back into every clip made from it (PR.write_clip)
        if len(vanilla[name].tracks) != len(sk1.bones):
            sys.exit('%s from %s has %d tracks, the first-person skeleton %d' % (name, src, len(vanilla[name].tracks),
                                                                                  len(sk1.bones)))
        print('first person %-28s from %s' % (name, src))
    if FREE_IDLE[0] not in mods:
        sys.exit('%s is not enabled in %s: find the first-person unarmed idle the free arm plays and update FREE_IDLE'
                 % (FREE_IDLE[0], profile))
    free_idle = anim_skyrim.load_skyrim_animation(QRS.find_ci(os.path.join(mods_dir, FREE_IDLE[0]), FREE_IDLE[1]))
    rest_at = lambda a, bones: {b: (list(a.tracks[b].rotations[0]), a.tracks[b].scales[0][0]) for b in bones}  # noqa: E731
    oar1 = os.path.join(mods_dir, PR.DEPLOY, *OAR_1P)
    if os.path.isdir(oar1):
        shutil.rmtree(oar1)
    muzzles = {g[0]: g[3][0] for g in PR.pistol_groups(mods_dir, mods)}
    written, built = 0, 0
    for hand, h in HANDS.items():
        bones = [rt.i1[n] for n in h['free']]
        rest = rest_at(vanilla[h['other']], bones) if h['other'] else rest_pose(free_idle, bones)
        template = os.path.join(os.environ.get('TEMP', '.'), '_pistol_reload_1p_%s.hkx' % hand)  # 1P track layout
        with open(template, 'wb') as fh:
            fh.write(_bsa.read(bsa[0], bsa[1]['\\'.join(ADS.ANIMS_1P).lower() + '\\' + h['shot']]))
        # this kind's third-person submods: 'Reload <pistol group><suffix>' exactly (from the deployed set, or for
        # first person's own shield style, tools/01's SHIELD_1P_SOURCES)
        src3 = h.get('src') or oar3
        subs = sorted(d for d in os.listdir(src3) if d.startswith('Reload ') and d.endswith(h['suffix'])
                      and d[len('Reload '):len(d) - len(h['suffix'])] in muzzles) if os.path.isdir(src3) else []
        if len(subs) != len(muzzles):
            sys.exit('%d third-person %s reloads in %s for %d pistol groups: run tools/01' % (len(subs), hand, src3,
                                                                                          len(muzzles)))
        for sub3 in subs:
            label = sub3[len('Reload '):len(sub3) - len(h['suffix'])]
            cfg3 = json.load(open(os.path.join(src3, sub3, 'config.json'), encoding='utf-8'))
            a3 = anim_skyrim.load_skyrim_animation(os.path.join(src3, sub3, h['shot']))
            added = [(a.time, a.text) for a in a3.annotations if a.text.startswith(PROP_EVENTS)]
            anim, worst, short, extra, dropped = build(rt, a3, vanilla[h['idle']], rest, template, muzzles[label],
                                                       h['gun'], h['beats'], h['motion_end'])
            if short and (worst > STOW_SHORT or not hand.startswith('stow')):
                sys.exit('%s %s: %d hand targets out of reach (worst %.2f)' % (hand, label, short, worst))
            name = 'Reload 1P %s%s' % (label, h['suffix'])
            sub = os.path.join(oar1, name)
            os.makedirs(sub)
            out = os.path.join(sub, h['shot'])
            PR.write_clip(out, anim, floats[h['shot']], reference=True)
            got, gap = check(rt, out, vanilla[h['idle']], rest, added)
            for aim in h['aim']:
                a = vanilla[aim]
                a.annotations = [x for x in a.annotations if x.text != PR.UNEQUIP] + \
                    [anim_skyrim.Annotation(time=0.0, text=PR.UNEQUIP)]
                PR.write_clip(os.path.join(sub, aim), ADS.havok_blocks(a), floats[aim])
                ADS.check_blocks(os.path.join(sub, aim))
            written += 1 + len(h['aim'])
            built += 1
            cfg = {'name': name,
                   'description': 'First person: %s, retargeted from the third-person reload (tools/04).'
                                  % cfg3['description'],
                   'priority': cfg3['priority'], 'conditions': cfg3['conditions']}
            ADS.write_config(sub, cfg)
            print('1P %-9s %-18s hands on target (worst %.3f); arms lifted %+.1f deg; elbow down on %d frames (up to '
                  '%.2f); %.2f s; end %.2f off the idle' % (hand, label, worst, extra, dropped[0], dropped[1],
                                                          got.duration, gap))
        os.remove(template)
    ADS.write_config(oar1, {'name': PR.MOD, 'author': 'Zenderal',
                            'description': 'First-person ramrod reload for the flintlock pistols, either hand (tools/04).'})
    os.remove(tmp)
    print('built %s: %d clips, %d with the reload' % (oar1, written, built))


if __name__ == '__main__':
    main()
