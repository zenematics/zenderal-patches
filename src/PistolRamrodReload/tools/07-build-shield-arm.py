"""Build the OAR set `Zenderal - Pistol Shield Arm` (third person): with a shield in the left hand and one of Loop's
pistols in the right, the left arm holds the shield the way Smooth Moveset's sword-and-shield idle does, while the body,
legs and gun arm stay Loop's.

Curator, 2026-11-03: "change the 3rd person shield + pistol animation to look more natural, normal shield idle with a 1
handed weapon", "make sure the pistol animation in 3rd person is also the correct Loop one". With a shield, the magic
graph plays Loop's right-hand clips on the whole body (magicbehavior `MRh_Ready_MSG` [8] `StaffRight_Idle`, the aimed
cast, the turns and moving casts), so the left arm took the pose Loop gave his free arm; 0_master's `MRh_Shd_Blend`
then laid `Shd_BlockIdle`'s winner (Dynamic Block Hit's shield idle, else Goetia's "Shield & Staff") on the left hand,
fingers, `Shield`, `AnimObjectL` and magic node only: a shield hand on an arm posed for nothing (read 2026-11-03).

Here each of Loop's right-hand submods gets a twin `<its name> (shield)`: every clip with the left arm (the clavicle's
whole subtree: arm, twists, pauldron, hand, fingers, `Shield`, `AnimObjectL`, magic node) set on every frame to
tools/01 SHIELD_ARM_SOURCE's at the frame tools/01's shield reload rests on, set the way the reload rests (`shield_arm()`:
rotations and scales, the source's offset only for `Shield`, Loop's `AnimObjectL` kept; it also goes on the shield
reloads' aim copies), so a reload starts and ends on the same arm. Every other bone, the timing and the annotations
are Loop's. The hand: MRh_Shd_Blend lays Shd_BlockIdle on it, so the Pandora patch's VAR_SHIELD (tools/03, held at 0 by
ZP_PistolReloadArmScript while a pistol and a shield are equipped) hands it to these clips. No shd_blockidle here: the
block graph's shield block is that clip name too, and a twin of it (the first build, 2026-11-03) replaced the block
("the block doesn't move to protect the body"). Conditions: Loop's own, plus a shield in the left hand (OAR type
tools/01 OAR_SHIELD) and not blocking (the block graph's StaffRight_Idle keeps Loop's: only its hand is used there).
Priority: Loop's + SHIELD_STEP, so the twins keep his order and stay below the reloads (tools/01, 1000020000 and up).

Loop's right-hand clips carry no float tracks (LoopPistolAnims' mirror_hkx drops them); the twins get vanilla's same-name
clip's (static node visibility 1.0, tools/hkx_floats), as tools/01's clips do, or none where vanilla has no such clip.
Writes into tools/01 DEPLOY (Patch Collection) and replaces only its own OAR set. Run after tools/01; rerun after Loop's
right-hand set, Smooth Moveset or tools/01's shield rest changes.
Usage:  python src/PistolRamrodReload/tools/07-build-shield-arm.py [<modlist root>]   (needs numpy)
"""
import copy
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


PR = _load('pistol_reload', os.path.join(HERE, '01-build-pistol-reload.py'))
ADS, anim_skyrim = PR.ADS, PR.anim_skyrim

MOD = 'Zenderal - Pistol Shield Arm'
OAR = PR.ANIMS_3P + ['OpenAnimationReplacer', MOD]
LOOP_SUBS = ['Pistol (right hand)', 'Pistol moving idle (right hand)', 'Pistol standing turns (right hand)',
             'Crossbow release (right hand)']
IDLE_SUB = 'Pistol (right hand)'        # the idle's (the shield's clearance is measured on it)
SHIELD_STEP = 155                        # 1000013345-8 -> 1000013500-3
# Not blocking. (2026-11-03: the graph variable iWantBlock == 0 lost the idle: 0_master only tests it inside the magic
# block, on bashExit, MagicBlock vs MagicBlockShieldCharge, and it is not 0 at idle; curator's recording.)
NOT_BLOCKING = {'condition': 'IsBlocking', 'requiredVersion': '1.0.0.0', 'negated': True}


def shield_conditions(conditions):
    """Loop's conditions, plus a shield in the left hand and not blocking."""
    return copy.deepcopy(conditions) + [
        {'condition': 'IsEquippedType', 'requiredVersion': '1.0.0.0', 'Type': {'value': float(PR.OAR_SHIELD)},
         'Left hand': True}, NOT_BLOCKING]


def check(path, src, arm, pose, rig):
    """Decode: every other bone is Loop's (0.05 units), the arm is the pose (0.1 deg), the annotations and length his."""
    got = anim_skyrim.load_skyrim_animation(path)
    ADS.check_blocks(path)
    if got.num_frames != src.num_frames or abs(got.duration - src.duration) > 1e-4:
        sys.exit('%s: %d frames / %.4f s, Loop\'s %d / %.4f' % (path, got.num_frames, got.duration, src.num_frames,
                                                                src.duration))
    if sorted((round(a.time, 4), a.text) for a in got.annotations) != sorted((round(a.time, 4), a.text)
                                                                            for a in src.annotations):
        sys.exit('%s: annotations differ from Loop\'s' % path)
    ang = lambda a, b: math.degrees(2 * math.acos(min(1.0, abs(sum(x * y for x, y in zip(a, b))))))  # noqa: E731
    root = rig.index[PR.SHIELD_ARM_ROOT]

    def in_arm(b):                       # the clavicle's subtree (AnimObjectL too: it rides the hand)
        while b >= 0 and b != root:
            b = rig.parents[b]
        return b == root
    keep = [b for b in range(len(got.tracks)) if not in_arm(b)]
    worst_body = worst_arm = 0.0
    for f in range(0, got.num_frames, max(1, got.num_frames // 12)):
        wg, ws = rig.world(got, f), rig.world(src, f)
        worst_body = max(worst_body, max(float(np.linalg.norm(wg[b][:3, 3] - ws[b][:3, 3])) for b in keep))
        worst_arm = max(worst_arm, max(ang(got.tracks[b].rotations[f], pose[b][1]) for b in arm))
    if worst_body > 0.05 or worst_arm > 0.1:
        sys.exit('%s: body %.3f units off Loop\'s, arm %.2f deg off the shield pose' % (path, worst_body, worst_arm))


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else ADS.TOOLS['modlistRoot']
    ctx = PR.Ctx(root)
    rig, ix = ctx.rig, ctx.ix
    pose = PR.shield_arm(ctx)               # either sex's shield reload rests on the same arm
    arm = sorted(pose)
    f = ctx.shield_frame
    ctx.right                               # Loop's right-hand folder
    loop_set = os.path.dirname(ctx.right_dir)
    out_set = os.path.join(ctx.mods_dir, PR.DEPLOY, *OAR)
    if os.path.isdir(out_set):
        shutil.rmtree(out_set)
    os.makedirs(out_set)
    written = 0
    for name in LOOP_SUBS:
        sub_src = os.path.join(loop_set, name)
        cfg = json.load(open(os.path.join(sub_src, 'config.json'), encoding='utf-8'))
        sub = os.path.join(out_set, name + ' (shield)')
        os.makedirs(sub)
        clips = sorted(c for c in os.listdir(sub_src) if c.lower().endswith('.hkx'))
        jobs = [(c, c) for c in clips]
        for clip, out_name in jobs:
            src = anim_skyrim.load_skyrim_animation(os.path.join(sub_src, clip))
            # his right-hand set (mirror_hkx) tracks the first 97 of the 99 bones, in skeleton order
            mapping = list(src.track_to_bone_indices) if src.track_to_bone_indices is not None else None
            if mapping != list(range(len(src.tracks))) or max(arm) >= len(src.tracks):
                sys.exit('%s/%s: %d tracks not bound to the first bones in order, or missing an arm bone'
                         % (name, clip, len(src.tracks)))
            key = '\\'.join(PR.ANIMS_3P).lower() + '\\' + out_name.lower()
            floats = ctx.bsa_floats(out_name) if key in ctx.bsa[1] else None
            out = os.path.join(sub, out_name)
            PR.write_clip(out, ADS.havok_blocks(PR.with_arm(src, pose)), floats, reference=True)
            check(out, src, arm, pose, rig)
            written += 1
        ADS.write_config(sub, {'name': name + ' (shield)',
                               'description': '%s, with a shield in the left hand: the left arm holds it as Smooth '
                                              'Moveset\'s sword-and-shield idle does (tools/07).'
                                              % cfg.get('description', name),
                               'priority': cfg['priority'] + SHIELD_STEP,
                               'conditions': shield_conditions(cfg['conditions'])})
        print('%-36s %d clips, priority %d' % (name + ' (shield)', len(jobs), cfg['priority'] + SHIELD_STEP))
    # how close the shield comes to the spine and legs in the idle (the source's own hold, on Loop's body)
    idle = anim_skyrim.load_skyrim_animation(os.path.join(out_set, IDLE_SUB + ' (shield)', PR.IDLE_RIGHT))
    clear = min(PR.shield_clearance(ctx, w, PR.unscaled(w[ix['Shield']]))
                for w in (rig.world(idle, g) for g in range(0, idle.num_frames, 4)))
    ADS.write_config(out_set, {'name': MOD, 'author': 'Zenderal',
                               'description': 'A shield with a right-hand flintlock pistol: the left arm holds it as '
                                              'with a one-handed weapon, the rest is Loop\'s (tools/07).'})
    os.remove(ctx.tmp)
    print('built %s: %d clips; the idle\'s shield %.1f off the spine and legs; arm from %s frame %d'
          % (out_set, written, clear, '/'.join(PR.SHIELD_ARM_SOURCE[1][-3:]), f))


if __name__ == '__main__':
    main()
