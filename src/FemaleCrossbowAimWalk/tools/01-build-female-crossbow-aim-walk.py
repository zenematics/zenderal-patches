"""Rebuild the `Zenderal - Female Crossbow Aim Walk` MO2 mod: a female character aiming a crossbow-type weapon
(Ordo's muskets, real crossbows) no longer swings the weapon off the crosshair.

Aiming walks play `crossbow_direction_behavior`'s CrossBow_Walk* clips (the behaviour has no run clips); the held,
unaimed gun walks and runs on the same clip names in `1hm_locomotion`. For female characters Smooth Combat non
Combat Animation's legacy DAR folder 602901 (`IsFemale() AND IsEquippedRightType(9)`, no other gate) replaces the
forward, forward-left and forward-right walks and runs. Vanilla's crossbow walks hold the body (NPC COM) at one
stance in every direction, so the layered aim stays on the crosshair; Smooth Combat's turn the whole body with the
walk: COM 0 deg forward, +37 deg (left) forward-left, -38.5 deg forward-right, against vanilla's -27.7 deg in all
three (measured 2026-11-01, printed again on every run). The aim rides on that body, so W+A swung the gun ~65 deg
left of where a male character aims.

One OAR submod, `Vanilla crossbow movement` (priority 602950, above 602901), with 602901's own gate (female +
crossbow-type in the right hand): every clip 602901 ships is replaced by the clip that wins its vanilla path, i.e.
exactly what male characters play, aimed or not. Smooth Combat itself is untouched; its female crossbow set is
simply always outranked.

v1 (same day) gated on aiming (OAR IsAttacking OR graph variable bBowDrawn) and replaced only the walks. W+A was
fixed, but aiming from a forward run still pulled the gun left for a moment (OAR animation log, in game): the
aim walk activates before CrossBow_Aim, while neither is true, so 602901's walk played, and a legacy DAR clip is
not interruptible, so OAR only swapped it at the clip's loop. Even an instant swap could not fix it: the run ->
aim blend starts from Smooth Combat's forward run (COM -2.6 deg) instead of vanilla's (-25.9 deg, the aim
stance's -27.7 within 2 deg), which is why male characters never see it. Hence no aim gate, and the runs too.

Inputs: the selected MO2 profile, Smooth Combat's 602901 folder, the winning loose copy of each vanilla clip
(else Skyrim - Animations.bsa), the winning skeleton.hkx for the measurement. Nothing third-party is committed.

Usage:  python 01-build-female-crossbow-aim-walk.py [<modlist root>]     (default: tools.json modlistRoot)
"""
import importlib.util
import json
import math
import os
import shutil
import sys

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
TOOLS = json.load(open(os.path.join(ROOT, '.claude', 'config', 'tools.json'), encoding='utf-8-sig'))
sys.path.insert(0, os.path.join(TOOLS['pynifly'], 'hkx'))
sys.path.insert(0, TOOLS['pynifly'])
import anim_skyrim  # noqa: E402  (PyNifly, no Blender dependency)


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


QRS = _load('qrs', os.path.join(ROOT, 'src', 'Prophecy', 'tools', '04-build-quick-reload-stack.py'))
_bsa = QRS._bsa

MOD = 'Zenderal - Female Crossbow Aim Walk'
SUBMOD = 'Vanilla crossbow movement'
PRIORITY = 602950  # above Smooth Combat's 602901; Tactical Crossbow Movement's Standing (838295) is disabled
ANIMS = ['meshes', 'actors', 'character', 'animations']
SMOOTH = ['Smooth Combat non Combat Animation'] + ANIMS + ['DynamicAnimationReplacer', '_CustomConditions', '602901']
SKELETON = ['meshes', 'actors', 'character', 'character assets', 'skeleton.hkx']
COM = 'NPC COM [COM ]'
# what crossbow_direction_behavior plays while aiming (it has no run clips); Smooth Combat must ship each one
AIM_CLIPS = ['crossbow_walkforward.hkx', 'crossbow_walkforwardleft.hkx', 'crossbow_walkforwardright.hkx']
VANILLA_SPREAD_MAX = 2.0  # deg: vanilla's COM heading must be the same stance in all three, or the premise is gone
NL = chr(10)

CONDITIONS = [  # 602901's own gate, so this wins wherever 602901 would
    {'condition': 'IsFemale', 'requiredVersion': '1.0.0.0'},
    {'condition': 'IsEquippedType', 'requiredVersion': '1.0.0.0', 'Type': {'value': 9.0}, 'Left hand': False},
]


def write_json(path, data):
    with open(path, 'w', encoding='utf-8', newline=NL) as fh:
        json.dump(data, fh, indent=4)
        fh.write(NL)


def quat_mat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def load_anim(data, tmp):
    with open(tmp, 'wb') as fh:
        fh.write(data)
    return anim_skyrim.load_skyrim_animation(tmp)


def com_yaw(skeleton, anim):
    """NPC COM's heading over the clip, deg (0 = the actor's forward +Y, + = left). The clip's tracks are the
    skeleton's first bones in order (its bone names are blank), so COM's chain is read from them."""
    i = skeleton.bones.index(COM)
    chain = []
    while i >= 0:
        if i >= len(anim.tracks):
            sys.exit('clip has %d tracks; %s chain needs bone %d' % (len(anim.tracks), COM, i))
        chain.append(i)
        i = skeleton.parents[i]
    out = []
    for f in range(anim.num_frames):
        rot = np.eye(3)
        for b in reversed(chain):
            rot = rot @ quat_mat(anim.tracks[b].rotations[f])
        fwd = rot @ np.array([0.0, 1.0, 0.0])
        out.append(math.degrees(math.atan2(-fwd[0], fwd[1])))
    return out


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else TOOLS['modlistRoot']
    mods_dir = os.path.join(root, 'mods')
    profile, mods = QRS.profile_mods(root)
    smooth = QRS.find_ci(mods_dir, SMOOTH)
    if not smooth or SMOOTH[0] not in mods:
        sys.exit('Smooth Combat non Combat Animation 602901 is not installed and enabled in %s - nothing to fix' % profile)
    cond = open(os.path.join(smooth, '_conditions.txt'), encoding='utf-8', errors='replace').read()
    if 'IsFemale()' not in cond or 'IsEquippedRightType(9)' not in cond:
        sys.exit('602901 no longer gates on IsFemale + IsEquippedRightType(9) - re-check: %r' % cond)
    bsa = _bsa.listing(os.path.join(root, 'Stock Game', 'Data', 'Skyrim - Animations.bsa'))
    tmp = os.path.join(os.environ.get('TEMP', '.'), '_female_xbow_walk.hkx')
    label, data = QRS.winner(mods_dir, mods, bsa, SKELETON)
    with open(tmp, 'wb') as fh:
        fh.write(data)
    skeleton = anim_skyrim.load_skyrim_skeleton(tmp)
    print('skeleton: %s' % label)

    dlc01 = QRS.find_ci(smooth, ['dlc01'])
    clips = sorted(f.lower() for f in os.listdir(dlc01) if f.lower().endswith('.hkx')) if dlc01 else []
    missing = [c for c in AIM_CLIPS if c not in clips]
    if missing:
        sys.exit('602901 no longer ships %s - re-check which aimed walks it replaces' % ', '.join(missing))
    sources, rows = {}, []
    for clip in clips:
        female = QRS.find_ci(dlc01, [clip])
        label, data = QRS.winner(mods_dir, mods, bsa, ANIMS + ['dlc01', clip])
        sources[clip] = (label, data)
        van = com_yaw(skeleton, load_anim(data, tmp))
        fem = com_yaw(skeleton, load_anim(open(female, 'rb').read(), tmp))
        rows.append((clip, label, float(np.mean(van)), float(np.mean(fem))))
    os.remove(tmp)
    print('%-32s %-28s %10s %14s' % ('602901 clip', 'male / now female', 'COM deg', 'Smooth female'))
    for clip, label, van, fem in rows:
        print('%-32s %-28s %+10.1f %+14.1f' % (clip, label, van, fem))
    aim = [r[2] for r in rows if r[0] in AIM_CLIPS]
    spread = max(aim) - min(aim)
    if spread > VANILLA_SPREAD_MAX:
        sys.exit('the clips that win the vanilla paths turn the body by %.1f deg between directions - '
                 'they are no longer a fixed aiming stance; re-check before shipping them' % spread)

    out_mod = os.path.join(mods_dir, MOD)
    if os.path.isdir(out_mod):
        shutil.rmtree(out_mod)
    own = os.path.join(out_mod, *ANIMS, 'OpenAnimationReplacer', MOD)
    sub = os.path.join(own, SUBMOD)
    os.makedirs(os.path.join(sub, 'dlc01'))
    write_json(os.path.join(own, 'config.json'),
               {'name': MOD, 'author': 'Zenderal',
                'description': 'Female characters move with a crossbow or musket on the same clips as male '
                               'characters, so the aim keeps its stance (vanilla over Smooth Combat 602901).'})
    for clip, (label, data) in sources.items():
        with open(os.path.join(sub, 'dlc01', clip), 'wb') as fh:
            fh.write(data)
    write_json(os.path.join(sub, 'config.json'),
               {'name': SUBMOD,
                'description': 'Female, crossbow-type weapon: the crossbow walks and runs male characters play. '
                               "Smooth Combat's female ones turn the body with the direction, and the aim with it.",
                'priority': PRIORITY,
                'conditions': CONDITIONS})
    print('%s (priority %d): %s' % (SUBMOD, PRIORITY, ', '.join(clips)))
    print('built %s' % out_mod)


if __name__ == '__main__':
    main()
