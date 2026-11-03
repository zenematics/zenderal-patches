"""Build the `Zenderal - Pistol Ramrod Reload` MO2 mod: a ramrod reload on the flintlock pistols, third person, either
hand (the right hand's is solved mirrored: Variant, unmirror(); tools/04 adds first person).

Our own animation (no third-party motion), made the way tools/09-11 of src/FlintlockOverhaul fit Zodd's musket reload:
shoulder-elbow-hand IK onto keyed targets, a lead ball and a ramrod in the hand through an AnimObject, props loaded and
drawn by clip annotations.

Why the shot clip (magic behaviour graph, Pandora output, read 2026-11-01): the pistols are staves, so a shot plays
`StfMagic_Release` in `MLh_AimedSpellReleaseState`. Its graph triggers fire the shot (`MLh_SpellFire_Event`) at 0.334 s
and open the re-cast window `MLh_WinStart`-`MLh_WinEnd` at 0.337-0.667 s (`MLh_SpellAimedStart -> PreCharge` uses that
initiate interval); otherwise the state is only left by `MLh_Equipped_Event` at the clip's end. So a longer shot clip
holds the reload, as Zodd's musket shot clip does. Bone masks: standing, `LeftHandMagicCast_MSG[8] ->
LHStaff_RHMagicCast_MSG[iRightHandType 0] -> MLh_ReadyCast_Behavior` has no mask (whole body); moving, sneaking and
turning take the `UpperBody` mask. Both arms follow the clip whenever the right hand is empty; with a weapon in it the
sword arm would ram, so the submods require IsEquippedType right = 0 (unarmed).

The clip: Loop's `stfmagic_release` (Simple Pistol Shooting Animation by Loop, via `Zenderal - Loop Pistol
Animations`) up to the top of his recoil (KEEP_FRAMES, 0.555 s), then the reload (BEATS), ending on his `staff_idle`
frame 0, which the graph plays next. Body bones ease from his recoil pose to his idle pose; the arms are solved:
  - left hand: the pistol (Shield node, Loop's Shield-in-hand transform) eases into a load pose, muzzle up in front of
    the body (load_pose(): the lowest muzzle height and least tilt from which both arms reach every beat), and back to
    the idle pose at the end;
  - right hand: pouch at the right hip (ball pinched: male mt_idlehhleftexitfast's fingers), over the muzzle (ball
    dropped in), the ramrod's top under the muzzle (fist: 1hm_staggeridle's fingers; the rod rides the `Weapon` node,
    the fist's grip centre), drawn up out of its pipes, over into the bore, rammed, one short stroke, drawn back out,
    stowed, back to the idle pose. Elbows bend toward POLE directions; the wrist roll is split over the two forearm
    twist bones 2/3 : 1/3, as Loop's clips do.
  - head and neck turn toward the muzzle while loading (LOOK).

Props on AnimObjectR (meshes and ANIO records by tools/02): `AnimObjLoad.<EditorID>` LOAD_LEAD before
`AnimObjDraw.<EditorID>`, `AnimObjectUnequip` to drop. The magic behaviour lists none of these events; the Pandora patch
`zpistolreload` (this patch's Pandora_Engine folder, copied into the MO2 mod) adds them, so Pandora must be rerun with
it ticked.

OAR, one submod per pistol mesh geometry (priority PRIORITY + i, above Loop's 1000012345-1000013348): drawn, one of the
mesh's pistols in the left hand, right hand unarmed. Fan the Hammer reloads within the re-cast window and so cuts this
clip as it does Loop's. (Prophecy's Hair Trigger no longer speeds the reload up, 2026-11-02: no perk condition.)

Inputs (never committed): Loop's clips from the active profile's `Zenderal - Loop Pistol Animations`, the pistol meshes
the equipped statics use, the skeleton and finger-pose clips from the user's Skyrim - Animations.bsa. Every written clip
is decoded again: the build fails unless Loop's frames are kept, every hand target is reached, the end matches the idle.

Rerun after Loop Pistol Animations, the pistol meshes or the Flintlock Overhaul's statics change, then tools/02.
Usage:  python src/PistolRamrodReload/tools/01-build-pistol-reload.py [<modlist root>]   (needs numpy)
"""
import copy
import glob
import importlib.util
import math
import os
import re
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


R3P = _load('ramrod3p', os.path.join(ROOT, 'src', 'FlintlockOverhaul', 'tools', '09-build-ramrod-reload.py'))
LOOP = _load('loop', os.path.join(ROOT, 'src', 'LoopPistolAnims', 'tools', '01-build-loop-pistol-anims.py'))
ADS = R3P.ADS
anim_skyrim, QRS, _bsa = ADS.anim_skyrim, ADS.QRS, ADS._bsa
HF = _load('hkx_floats', os.path.join(HERE, 'hkx_floats.py'))

MOD = 'Zenderal - Pistol Ramrod Reload'
# The MO2 mod the files go in (2026-11-03): the standalone mod was merged into Patch Collection and moved out of mods/
# (E:/Zenderal-backups/2026-11-03-patch-collection-merge), so every tool writes there; MOD names the OAR sets, plugin
# and Pandora patch inside it. tools/01 replaces only its own OAR set and Pandora patch folder.
DEPLOY = 'Zenderal - Patch Collection'
ANIMS_3P = ['meshes', 'actors', 'character', 'animations']
OAR = ANIMS_3P + ['OpenAnimationReplacer', MOD]
LOOP_SUB = ANIMS_3P + ['OpenAnimationReplacer', LOOP.MOD, 'Pistol']
CLIP = 'stfmagic_release.hkx'
IDLE = 'staff_idle.hkx'
# Loop's aim clips (one identical file under six names): copies start with AnimObjectUnequip, so a reload cut short
# (dodge, stagger) drops its prop when the gun is raised again
AIM_CLIPS = ['stfmagic_precharge.hkx', 'stfmagic_chargeloop.hkx', 'stfmagic_preready.hkx', 'stfmagic_readyloop.hkx',
             'stfmagic_preaimcon.hkx', 'stfmagic_aimconloop.hkx']
PRIORITY = 1000020000      # above Loop's left (1000012345-8) and right-hand (+1000) submods
FLINTLOCK_ESP = LOOP.FLINTLOCK_ESP
REVERSAL_ESP = 'Zenderal - Reversal Shadow.esp'
ESP_DIRS = [os.path.join(ROOT, 'src', 'FlintlockOverhaul', 'FlintlockOverhaulESP'),
            os.path.join(ROOT, 'src', 'ReversalShadow', 'ReversalShadowESP')]
PROPHECY_ESP = 'Zenderal - Prophecy.esp'

KEEP_FRAMES = 16           # the reload's motion starts here (0.555 s; where Loop's recoil tops out, pistol upright)
# Reloads start from the hold (2026-11-02, curator: reloads now play only on a fire press, and "go straight to the
# reload"): the clip's first KEEP_FRAMES are Loop's idle hold instead of his shot, and are cut off once the clip is
# checked (trim()). The pistol leaves the hold as the clip starts; every beat lies TRIM earlier in the written clip.
LOOP_FD = 0.034667         # Loop's clips: 0.8667 s over 25 frames (asserted)
TRIM = KEEP_FRAMES * LOOP_FD
# right-hand beats, seconds into the clip (the shot is at 0.334, the gun reloads ReloadDelay 2.0 s after it)
BEATS = dict(pouch_near=0.78, pouch=0.86, over_muzzle=1.04, drop=1.10, grab=1.30, drawn=1.50, over_bore=1.58,
             rammed=1.76, stroke_up=1.83, stroke_down=1.90, withdrawn=2.08, over_stow=2.16, stowed=2.32, end=2.66)
LOAD_AT = 0.78             # the pistol is in its load pose from here ...
UNLOAD_AT = 2.32           # ... until here, then eases back to the idle pose by the end
LOAD_LEAD = 0.19           # AnimObjLoad this long before AnimObjDraw (Eating Animations and Sounds: 0.2)
BALL_DROP = 0.06           # the ball leaves the fingers for the muzzle over this long
# Loading sounds (2026-11-02, curator: "add loading gun 5 and then 9 sounds at the point the ball goes into the
# barrel"): `SoundPlay.<SNDR>` as the ball starts into the muzzle, the second once the first has died away (Motion
# Array's Amenteramco "Loading Gun 5" is loud for its first 0.67 s). Vanilla puts its bow and crossbow SoundPlay events
# in both views' clips; tools/04 copies these. The SNDRs are tools/02's, the .wavs tools/06's (licensed, not committed).
SOUNDS = (('ZEN_PistolLoadGun5', 0.0), ('ZEN_PistolLoadGun9', 0.67))    # (EditorID, seconds after the ball starts in)
BALL_RADIUS = 1.0          # pistol ball (a .60 ball is ~1.07 units across; the musket's 1.3 reads, 0.85 barely did)
FINGER_TIP = 0.7           # a finger's tip lies this fraction of its middle segment past its last joint
ROD_MAX = 24.0             # the ramrod prop: as long as the barrel allows, at most this (both arms must reach its top)
ROD_SHORT = 4.0            # ... and this much shorter than the muzzle's distance from the grip
ROD_GAP = 0.3              # the stowed rod's axis this far beyond the barrel's surface (pistol's +X, away from the body)
ROD_RADIUS = 0.3           # tools/02 builds the rod this thick
ROD_TOP_STOWED = -1.0      # the stowed rod's top end, along the bore from the muzzle face
ROD_ABOVE_FIST = 2.5       # this much rod above the fist's grip centre
FIST_ABOVE_MUZZLE = 2.5    # rammed, the fist's grip centre stays this far above the muzzle face
STROKE = 6.0               # the short stroke's length
BALL_ABOVE_MUZZLE = 2.0    # the pinched ball's centre this far above the muzzle face before it drops
POUCH = (10.0, 7.0, 8.0)   # belt pouch at the right hip: right, forward, up from the pelvis (lower is out of reach)
REACH_SLACK = 1.0          # every target's wrist at least this far inside the arm's length
PINCH_SOURCE = ('male\\mt_idlehhleftexitfast.hkx', 27)    # thumb and index tips 0.82 apart, others half curled
FIST_SOURCE = ('1hm_staggeridle.hkx', 9)                    # the one-handed grip
IK_EASE = 0.15             # the arms' elbows ease from the pose's own into POLE over this long (and back at the end)
LOOK = 0.65                # head and neck turn this fraction of the way toward the muzzle while loading
NECK_SHARE = 0.4           # ... the neck taking this share of it
SIDES = {'L': ('NPC L UpperArm [LUar]', 'NPC L Forearm [LLar]', 'NPC L Hand [LHnd]',
               'NPC L ForearmTwist1 [LLt1]', 'NPC L ForearmTwist2 [LLt2]'),
         'R': ('NPC R UpperArm [RUar]', 'NPC R Forearm [RLar]', 'NPC R Hand [RHnd]',
               'NPC R ForearmTwist1 [RLt1]', 'NPC R ForearmTwist2 [RLt2]')}
TWIST_SHARE = (2.0 / 3.0, 1.0 / 3.0)    # wrist roll on ForearmTwist1 / ForearmTwist2 (Loop's: 31.5 / 15.7 deg)
PINCH_AIM = 0.7            # a pinching hand turns this fraction of the way from a straight wrist to fingers-on-target
FACE = (0.0, 2.0, 4.0)     # the middle of the face in the head bone's frame
HEAD_CLEAR = 15.0          # the right arm and its grip keep this far from the face (solve_beat's cost) ...
HEAD_CLEAR_MIN = 10.0      # ... and the build fails if any frame comes closer than this
CONTINUITY = 0.5           # cost per degree a beat's hand (and half for its elbow) turns from the last beat's
LOAD_CANDIDATES = 12     # the cheapest load poses whose right-hand beats are solved before one is picked
WRIST_BEND_MAX = 80       # the build fails past these (degrees from the skeleton's straight, unrolled wrist)
WRIST_ROLL_MAX = 100
UNEQUIP = R3P.UNEQUIP
# The ball is rammed home: the Flintlock Overhaul's ammo script loads the gun on this event, not on a timer, so an attack
# that cuts the reload short leaves the gun empty (2026-11-02, curator: no reloading by animation-cancelling). Per hand:
# the right hand's clips carry the R one (unmirror renames it). The Pandora patch lists both.
LOADED, LOADED_RIGHT = 'ZenPistolLoadedL', 'ZenPistolLoadedR'
PROP_PLUGIN = 'Zenderal - Pistol Ramrod Reload.esp'
BALL_EDID = 'ZEN_PistolBall'
ROD_EDID = 'ZEN_PistolRod_%s'     # % group label: one rod per barrel length
R_FINGERS = ['NPC R Finger%d%d [RF%d%d]' % (a, b, a, b) for a in range(5) for b in range(3)]
# The free right arm (ZenBoneTrace 2026-11-01): in 1hm_behavior's MLh_1HM_Idle_Blend the clip gets the bones below at
# half weight (HALF) or not at all (IDLE); the rest comes from the unarmed + staff 1hm_idle that wins (IDLE_SOURCE,
# matched to the traced forearm and hand within 0.1 deg). The Pandora patch lets ZP_PistolReloadArmScript hand the
# whole arm to the clip for a reload, so the clip's right arm starts and ends on what the game showed before the switch:
# HALF bones halfway between the clip's own and the idle's, IDLE bones the idle's.
RIGHT_HALF = ['NPC R Clavicle [RClv]', 'NPC R UpperArm [RUar]', 'NPC R Pauldron', 'NPC R UpperarmTwist1 [RUt1]',
              'NPC R UpperarmTwist2 [RUt2]']
RIGHT_IDLE = ['NPC R Forearm [RLar]', 'NPC R Hand [RHnd]', 'AnimObjectR', 'Weapon', 'NPC R MagicNode [RMag]',
              'NPC R ForearmTwist1 [RLt1]', 'NPC R ForearmTwist2 [RLt2]'] + R_FINGERS
IDLE_SOURCE = ('Goetia Animations - Enchanted Magic Staves', ANIMS_3P + ['OpenAnimationReplacer', 'Enchanted Staves',
                                                                       'Unarmed R Staff L sprint', '1hm_idle.hkx'])
# The right hand (2026-11-01): a staff in the right hand with the left hand empty is 0_master's H2H_MRh idle, whose
# bone switch gives the whole LeftArm mask (clavicle to fingers, no halves) to 1HM_Idle: Goetia's "unarmed left, staff
# right" submod wins there. The Pandora patch frees that arm with fZenPistolLeftArmIdle. The clips are solved in a
# mirrored world (Variant) from Loop's right-hand set.
LOOP_SUB_RIGHT = 'Pistol (right hand)'                      # next to LOOP_SUB in Loop's OAR set (mirrored clips)
CLIP_RIGHT = 'stfmagicright_release.hkx'
IDLE_RIGHT = 'staffright_idle.hkx'
AIM_CLIPS_RIGHT = [c.replace('stfmagic_', 'stfmagicright_') for c in AIM_CLIPS]
IDLE_SOURCE_RIGHT = ('Goetia Animations - Enchanted Magic Staves', ANIMS_3P + ['OpenAnimationReplacer', 'Enchanted Staves',
                                                                             'Unarmed L Staff R sprint', '1hm_idle.hkx'])
PRIORITY_RIGHT = 1000021000                                 # above Loop's right-hand submods (1000013345-8)
BALL_EDID_L = 'ZEN_PistolBallL'                             # the left hand's props (Prn AnimObjectL, tools/02)
ROD_EDID_L = 'ZEN_PistolRodL_%s'
# Loop's clips scale `NPC R Hand` by 0.852 on every frame: in his left-hand clips the free hand (the engine applies
# animated bone scale, but the one-handed idle owns that hand). The free arm takes its scale from the idle it hands
# over to (Goetia's: 1.0), and the solver works with the gun at its real scale (build_clip: c and radius times the gun
# hand's scale). Until 2026-11-02 mirror_hkx left scale tracks on their bone, so Loop's right-hand set scaled the GUN
# hand and right-hand pistols showed at 85%; mirror_hkx now moves them to the partner and the right-hand set was
# regenerated. RIGHT_GUN_SCALE is what the build expects to measure (it fails otherwise: e.g. the old right-hand set
# still installed); tools/02 cuts the right hand's rods (AnimObjectL) for it.
RIGHT_GUN_SCALE = 1.0
# Two pistols (2026-11-02, curator: "tuck and ram one gun at a time"). magicbehavior's DualStaff_Blend gives the other arm
# to the other gun's own graph; the Pandora patch's wrapper hands the whole body to the firing gun's clip
# (fZenPistolDualReload, set by ZP_PistolReloadArmScript). The clip carries the other gun from its idle hold (Loop's
# idle for that hand, frame 0: traced, ZenBoneTrace 1.1.0) to the belt (its attach node pinned there: belt_pose), lets go,
# reloads (the one-gun beats DUAL_SHIFT later), takes the gun again and carries it back, and holds the vanilla
# two-staff pose (each arm on its own Loop idle, frame 0) from DUAL_MOTION_END to DUAL_END while the script resets the
# variable. ZP_PistolReloadArmScript's DUAL_RESET_AFTER and DUAL_LOCK (3.27: clip time 3.60, the middle of the hold,
# counted from the shot at 0.334 s; Papyrus is never early and rarely 0.3 s late) must stay inside it. On the way
# down and back up the gun passes level and pointing forward at the waist (lower / raise): turned the short way from
# barrel up to barrel down, it swept back through the torso (rendered 2026-11-02).
DUAL_SHIFT = 0.45
DUAL_LOWER, DUAL_TUCKED, DUAL_RELEASE, DUAL_REGRIP, DUAL_RAISE = 0.75, 0.95, 1.05, 3.02, 3.22
DUAL_MOTION_END, DUAL_END = 3.42, 3.95
DUAL_BEATS = dict({k: v + DUAL_SHIFT for k, v in BEATS.items() if k != 'end'}, lower=DUAL_LOWER, tucked=DUAL_TUCKED,
                  release=DUAL_RELEASE, regrip=DUAL_REGRIP, raise_=DUAL_RAISE, end=DUAL_END)
LEVEL_OFF = (0.0, 7.0, 6.0)        # lower / raise: the grip this far right / forward / up from its belt place
# The free arm between the hand-offs (2026-11-02, curator, first person: the reloading arm "appears inverted", "does not
# look natural"). It rested on the other gun's hold for the whole clip, clavicle and fingers too, so its shoulder stayed
# 8.6 units forward and 4 out while it reloaded, and the beats solved from there put the pinch over the muzzle and the
# drawn rod in front of the face (first person: the forearm hanging from a fist at the top of the view, the elbow in
# the middle of it). From letting go of the gun (`release`) to `pouch_near`, and back from `stowed` to `regrip`, the
# free arm's rest blends to the one-gun reload's (Variant.relaxed); the carry beats keep the hold's. The melee stows
# already rest on the one-gun reload's shoulder (half the idle's).
RELAX_SKIP = ('AnimObjectR', 'Weapon')    # the gun's node (pinned to the belt meanwhile) and the props' node
# The melee arm's hand-back (2026-11-02, curator: after the reload "the right hand reverts back to neutral holding weapon
# before changing to the actual stance idle"). ZP_PistolReloadArmScript handed the arm back on a Papyrus timer, which
# landed after the clip had ended (Hair Trigger's: 1.95 s, the hand-back ~2.0; traced), so for those frames the arm was
# the magic graph's, the plain staff idle's weapon-holding pose; without Hair Trigger it landed on the clip's held end,
# vanilla's one-handed idle. The stow clips now say ARM_BACK ARM_BACK_AFTER seconds after the regrip (the weapon in the hand
# again, out of its sheath), and the script hands the arm to the game's idle on it (SIGMA's, by stance: OAR's log
# showed "Daggers Low" starting at the hand-back), while the draw still moves the arm. In the Pandora patch's event
# lists (tools/03); tools/04 copies it, tools/07 scales it with the twins.
ARM_BACK = 'ZenPistolArmBack'
ARM_BACK_AFTER = 0.05
CARRY_FOLLOW = 0.3                 # carrying: cost per degree the elbow leaves the beats' blended one ...
CARRY_HOLD = 5.0                   # ... rising by this much toward an idle hold (exactly there it is the hold's own)
CARRY_STEADY = 1.0                 # ... and per degree it moves from the last frame's
# Flips (2026-11-02, curator: a flick of the arm carrying the other gun): where another elbow side strains the wrist less
# the solvers swing the arm across in one frame (the two-pistol carry 145-179 deg in a key, raising the gun back too;
# the pinch 110). Smoothing the elbow's path instead rolled the carrying wrist up to 178 deg (every load pose failed).
# deflick() blends an arm across each key where one of its bones turns more than DEFLICK_DEG, in its own joints, from
# DEFLICK_SPAN keys before to as many after: the hand leaves its path for a moment instead of the arm snapping. Never
# across a reload beat (the hand must be there) or the other item's hand-offs (tucked, release, regrip); while it is in
# the belt or sheath it is pinned there again after (its node hangs on the hand).
DEFLICK_DEG = 60.0
DEFLICK_SPAN = 5
ARM_BONE = re.compile(r'NPC ([LR]) (Clavicle|UpperArm|UpperarmTwist\d|Forearm|ForearmTwist\d|Hand) \[')
BELT_RIGHT = (-6.0, -2.0, 3.0)     # the tucked gun's grip (attach node), from the pelvis: right / forward / up
BELT_FWD = (10.0, 13.0)
BELT_UP = (8.0, 12.0)
BELT_CLEAR = 6.0                   # every point of the barrel at least this far in front of the pelvis
BARREL_MAX = 41.0                  # the longest pistol's muzzle (flintlockpistol 40.6): any gun can be the tucked one
RELEASE_OFF = (0.0, 2.5, 3.0)      # the hand lets go: this much right / forward / up from the grip
PRIORITY_DUAL = 1000022000         # above the one-gun submods (their other hand must be empty anyway)
PRIORITY_DUAL_RIGHT = 1000023000
DUAL = ' (two pistols)'
# Both pistols fired at once had a "second" clip for the left gun (Loop's shot, held while the right gun reloaded, then
# its own reload); retired 2026-11-02 with reloads on the fire button (REQUEST): one press asks for one reload, and the
# other gun's press waits until that reload ends. Variant's `shift` (a reload starting later in its clip) and
# SECOND_SETTLE (the body settled into the idle hold by then) stay.
SECOND_SETTLE = 0.9
# A reload plays only when asked for (2026-11-02, curator: "it does not reload until I press to fire it again", so the
# other hand is free after a shot). A shot plays Loop's shot clip alone; pressing fire on the empty gun sets that hand's
# request variable (the Pandora patch's, default 0) for the cast ZP_PistolReloadArmScript starts, and every submod
# here (and tools/04's, which copy these conditions) requires it.
REQUEST = {True: 'fZenPistolReloadL', False: 'fZenPistolReloadR'}
# A one-handed melee weapon in the other hand (2026-11-02, curator: "sheathe, reload, draw"): on the two-pistol timeline
# (DUAL_BEATS) the free hand puts it in its sheath instead of the belt, rams, and draws it again. The sheath is where the
# engine shows that weapon sheathed: XPMSE's skeleton mesh, the node under its weapon-style nodes (all at their
# defaults) down to the bone the clips animate (Ctx.sheath); a left-hand weapon on the *Left node (Simple Dual Sheath).
# Weapon meshes run the blade (and the scabbard) along +Y from the grip, so STOW_APPROACH out of the sheath is -Y.
# The free arm and the weapon's grip in it (graph, read 2026-11-02):
#   - pistol left, weapon right: 1hm_behavior's MLh_1HM_Idle_Blend as for an empty hand (fZenPistolRightArmIdle frees
#     it); the arm's idle is whatever moveset wins 1hm_idle (122 OAR submods compete: vanilla's stands in, and
#     ZP_PistolReloadArmScript fades the arm over instead of switching);
#   - pistol right, weapon left: 0_master's MRh_1HM_Idle_BoneSwitch_3rdP, DW1HM1HMIdle on the LeftForearm mask (the
#     upper arm stays the shot clip's), and the root's DualWieldShieldBone_BoneSwitchGen sets the grip (`Shield`) from
#     DW_ShieldAdjustment, the dual-wield idle's own; the Pandora patch frees both with fZenPistolLeftStow.
STOW = {1: ('sword', 'WeaponSword'), 2: ('dagger', 'WeaponDagger'), 3: ('axe', 'WeaponAxe'), 4: ('mace', 'WeaponMace')}
STOW_SEXED = {2}           # XPMSE's female dagger sheath sits ~8 units and 18 deg off the male's: one clip per sex
STOW_APPROACH = 15.0       # on the way in and out the weapon is this far further out of its sheath, along its blade
# Out of the sheath is whichever way along the blade points up (sword, dagger and mace hang blade down, the axe head up).
# The arm alone reaches few sheaths with the idle's grip (cross-body, low on the hip; the axe's grip hangs at the thigh),
# so, as Skyrim's own sheathing does (the hand near, then the weapon on its sheath node): the hand pushes the weapon in
# only as deep as it comfortably reaches (STOW_DEPTH_STEP, at most STOW_DEPTH_MAX out, wrist inside STOW_WRIST), lets go,
# and the weapon slides the rest of the way over DUAL_TUCKED -> DUAL_RELEASE (and out again before DUAL_REGRIP); and
# the hand turns on the handle (a roll about the blade, STOW_ROLL_STEP) for the least wrist strain at each beat.
STOW_DEPTH_STEP, STOW_DEPTH_MAX = 2.0, 30.0
STOW_WRIST = (65.0, 75.0)  # bend / roll
STOW_ROLL_STEP = 15
XPMSE = 'XP32 Maximum Skeleton Special Extended'
XPMSE_NIF = {False: ['meshes', 'actors', 'character', 'character assets', 'skeleton.nif'],
             True: ['meshes', 'actors', 'character', 'character assets female', 'skeleton_female.nif']}
FREE_IDLE_1HM = '1hm_idle.hkx'          # vanilla's: a right one-hander's arm beside a left staff
FREE_IDLE_DW = 'dw1hm1hmidle.hkx'       # vanilla's: the left forearm (and grip) beside a right staff
PRIORITY_STOW = 1000024000
PRIORITY_STOW_RIGHT = 1000025000
# A shield in the other hand (2026-11-03, curator: "Shields + pistol are allowing players to infinitely shoot with no
# reload": no clip played, so the Flintlock script loaded the gun on its old timer; the curator chose the shield slung on
# the back). Shields are left-hand only: a right-hand pistol, solved mirrored like the others. In third person 0_master's
# MRh_Shield_Ready -> MRh_Shd_Blend puts Shd_BlockIdle on the left hand, its fingers, Shield, AnimObjectL and the magic
# node only; the arm above is the magic graph's, our clip's (read 2026-11-03). The Pandora patch frees it with
# fZenPistolLeftStow (tools/03 stow_release). The free arm rests on SHIELD_ARM_SOURCE's (below). On the two-pistol timeline the
# free hand carries the shield (strapped: the grip never turns) behind the back, lets go where it reaches with an easy
# wrist (shield_letgo), and the shield settles onto XPMSE's ShieldBack (the node a sheathed shield hangs on, below
# Spine2; 4 units apart by sex, so a clip per sex) over DUAL_TUCKED -> DUAL_RELEASE, the way back the same. The shield
# meshes lie in their node's XY plane, the face toward -Z (measured on five of the list's shields: rims 19-26 across,
# kite shields 56 long).
SHIELD = 10                       # GetEquippedItemType (Papyrus) ...
OAR_SHIELD = 11                   # ... and OAR's IsEquippedType (214 of the list's shield submods use 11, crossbows 9)
SHIELD_NODE = 'ShieldBack'
# The shield arm (2026-11-03, curator: "change the 3rd person shield + pistol animation to look more natural, normal
# shield idle with a 1 handed weapon"): with a shield, Loop's right-hand clips move the whole left arm (posed by him as
# a free arm) and Shd_BlockIdle's winner (Dynamic Block Hit, Goetia's "Shield & Staff") only the hand, so the shield hand
# sat on an arm posed for nothing. tools/07 gives every Loop right-hand clip, and Shd_BlockIdle, the left arm of Smooth
# Moveset's sword-and-shield idle at its least swaying frame (SHIELD_ARM_SOURCE); the shield reload rests on the same
# arm, whole (clavicle to fingers, Shield), so it starts and ends on what tools/07's idle shows.
SHIELD_ARM_SOURCE = ('Smooth Moveset - OAR', ANIMS_3P + ['OpenAnimationReplacer', 'Smooth Moveset - 1hm Shield',
                                                         '1hm Shield Non-Combat idle Loop', '1hm_idle.hkx'])
# where the hand may let go, from ShieldBack in the body's frame at the 'tucked' beat: down, out (along the shield's
# face, away from the back), toward the free arm's side; the shield turned in its own plane by SHIELD_ROLL (it turns
# back as it settles)
SHIELD_DOWN = tuple(range(0, 41, 5))
SHIELD_OUT = (4.0, 8.0, 12.0, 16.0, 20.0)
SHIELD_SIDE = (-6.0, 0.0, 6.0, 12.0, 18.0)
SHIELD_ROLL = tuple(range(-90, 91, 15))
SHIELD_WRIST = (65.0, 75.0)       # bend / roll at the let-go, as STOW_WRIST ...
SHIELD_APPROACH_WRIST = (75.0, 90.0)  # ... and at the approach, passed through on the way (inside WRIST_*_MAX): resting
                                      # on the sword-and-shield arm, the female approach missed 65 by 0.01 deg
SHIELD_APPROACH = (10.0, 8.0)     # 'lower' / 'raise_': the shield this much further toward the free side / out
SHIELD_RIM = (0.0, 12.0, 20.0)    # the shield sampled on rings of these radii (8 points each), 4 into its face ...
SHIELD_CLEAR = 7.0                # ... each at least this far from the spine and leg lines while the hand carries it
PRIORITY_SHIELD_RIGHT = 1000026000
# Keys (2026-11-02, curator: the dagger jittered in first person). The engine interpolates each bone's local track
# linearly between keys (PyNifly writes degree-1 splines), and Loop's clips, so ours, run at 28.8 keys a second. A
# weapon pinned in its sheath or the belt hangs on its hand's attach node with a large, fast-changing local offset, so
# halfway between keys it swings off its spot with the hand: up to 4.5 units on the dagger's regrip (decoded), and in
# game, at 60 fps, every other frame (traced, ZenBoneTrace 1.6). Clips with a weapon off the hand (two pistols, a melee
# weapon) get DENSE keys per frame (densify), the pinned node's world interpolated between them: ~1/DENSE^2 of the
# swing. More than 256 frames run over several of PyNifly's blocks, which start one frame later than Havok's
# (fpb - 1 apart): each later block plays one key (8.7 ms) early, which our decoder reads back the same.
DENSE = 4
DENSE_NODES = ('Weapon', 'Shield')


smooth = R3P.smooth


def unit(v):
    v = np.asarray(v, dtype=float)
    return v / np.linalg.norm(v)


def basis_map(a_from, b_from, a_to, b_to):
    """Rotation taking a_from onto a_to exactly and b_from as close to b_to as possible (all unit 3-vectors)."""
    def frame(a, b):
        b = unit(b - a * (a @ b))
        return np.column_stack([a, b, np.cross(a, b)])
    return frame(unit(a_to), b_to) @ frame(unit(a_from), b_from).T


def pose_at(anim, f):
    return [(list(t.translations[f]), list(t.rotations[f]), list(t.scales[f])) for t in anim.tracks]


def mix_pose(a, b, s):
    out = []
    for (ta, qa, sa), (tb, qb, sb) in zip(a, b):
        out.append((ADS.lerp(ta, tb, s), ADS.slerp(qa, qb, s), ADS.lerp(sa, sb, s)))
    return out


def set_pose(anim, f, pose):
    for tr, (t, q, s) in zip(anim.tracks, pose):
        tr.translations[f], tr.rotations[f], tr.scales[f] = [float(x) for x in t], [float(x) for x in q], [float(x) for x in s]


def local_mat(anim, i, f):
    t = anim.tracks[i]
    return ADS.trs(t.translations[f], t.rotations[f], t.scales[f][0])


def mat_trs(m):
    r = m[:3, :3] / np.linalg.norm(m[:3, 0])
    return m[:3, 3].copy(), ADS.mat_quat(r)


def unscaled(m):
    out = m.copy()
    out[:3, :3] /= np.linalg.norm(m[:3, 0])
    return out


def blend_mat(a, b, s):
    (ta, qa), (tb, qb) = mat_trs(a), mat_trs(b)
    return ADS.trs(ADS.lerp(ta, tb, s), ADS.slerp(qa, qb, s), 1.0)


def nif_local(node):
    """A PyNifly node's transform (to its parent) as a 4x4: its rotation matrix is the clips' convention (checked on the
    sheath bones, which both carry)."""
    t = node.transform
    m = np.eye(4)
    m[:3, :3] = np.array(t.rotation, dtype=float).reshape(3, 3) * t.scale
    m[:3, 3] = list(t.translation)
    return m


def rot_axis(axis, deg):
    a = unit(axis)
    x, y, z = a
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.array([[c + x * x * (1 - c), x * y * (1 - c) - z * s, x * z * (1 - c) + y * s],
                     [y * x * (1 - c) + z * s, c + y * y * (1 - c), y * z * (1 - c) - x * s],
                     [z * x * (1 - c) - y * s, z * y * (1 - c) + x * s, c + z * z * (1 - c)]])


# ---- the pistols ----------------------------------------------------------------------------------------------

def pistol_bore(V):
    """(muzzle centre, unit bore axis, barrel radius) in the attach node's frame. The rotated pistol meshes
    (src/LoopPistolAnims/tools/02) run their barrel along +Y with +X straight down (Loop's aim pose); +Z is the lock's
    side. 1-unit slabs back from the muzzle over its front 60%: the barrel's top edge (least X) and lateral centre."""
    ymax, ymin = V[:, 1].max(), V[:, 1].min()
    ring = V[V[:, 1] > ymax - 0.6]
    r = (ring[:, 2].max() - ring[:, 2].min()) / 2          # lateral half-width at the muzzle
    rows, y = [], ymax - 1.0
    while y > ymax - 0.6 * (ymax - ymin):
        s = V[(V[:, 1] > y - 0.5) & (V[:, 1] <= y + 0.5)]
        if len(s) >= 4:
            top = s[:, 0].min()
            upper = s[s[:, 0] < top + 0.5 * r]
            rows.append((y, top, (upper[:, 2].max() + upper[:, 2].min()) / 2))
        y -= 1.0
    rows = np.array(rows)
    kt, bt, _ = ADS.robust_line(rows[:, 0], rows[:, 1])
    kz, bz, _ = ADS.robust_line(rows[:, 0], rows[:, 2])
    return np.array([kt * ymax + bt + r, ymax, kz * ymax + bz]), unit([kt, 1.0, kz]), float(r)


def pistol_groups(mods_dir, mods):
    """[(label, mesh path, [(plugin, form id hex)], bore)] - one per distinct barrel, from the WEAPs' FirstPersonModel
    statics (the equipped model in third person too, src/LoopPistolAnims doc)."""
    def field(text, key):
        m = re.search(r'^%s:\s*\r?\n\s+File:\s*(.+?)\s*$' % key, text, re.M)
        return m.group(1) if m else None
    statics, weapons = {}, []
    for d in ESP_DIRS:
        for p in glob.glob(os.path.join(d, 'Statics', '*.yaml')):
            t = open(p, encoding='utf-8').read()
            statics[re.search(r'^FormKey:\s*(\S+)', t, re.M).group(1)] = field(t, 'Model')
        for p in glob.glob(os.path.join(d, 'Weapons', '*.yaml')):
            t = open(p, encoding='utf-8').read()
            fk = re.search(r'^FormKey:\s*(\w+):(.+?)\s*$', t, re.M)
            fp = re.search(r'^FirstPersonModel:\s*(\S+)', t, re.M)
            if fk.group(2) in (FLINTLOCK_ESP, REVERSAL_ESP) and fp:
                weapons.append((fk.group(2), '%X' % int(fk.group(1), 16), fp.group(1)))
    by_mesh = {}
    for plugin, fid, st in weapons:
        model = statics.get(st)
        if not model:
            sys.exit('%s %s: FirstPersonModel %s has no model' % (plugin, fid, st))
        by_mesh.setdefault(model.replace('\\', '/').lower(), []).append((plugin, fid))
    want = {(FLINTLOCK_ESP, f) for f in LOOP.PISTOLS} | {(p, f) for p, f in LOOP.EXTRA_PISTOLS}
    got = {w for ws in by_mesh.values() for w in ws}
    if not want <= got:
        sys.exit('pistols without an equipped mesh: %s' % sorted(want - got))
    groups = {}
    for mesh_rel, ws in sorted(by_mesh.items()):
        ws = [w for w in ws if w in want]
        if not ws:
            continue
        _, path = ADS.winning_loose(mods_dir, mods, mesh_rel)
        V = ADS.mesh_surface(path)
        c, axis, r = pistol_bore(V)
        key = tuple(np.round(np.r_[c, axis * 10, r], 1))
        if key in groups:
            groups[key][2].extend(ws)
        else:
            label = os.path.splitext(os.path.basename(mesh_rel))[0]
            groups[key] = [label, path, list(ws), (c, axis, r), V[::5]]
    return sorted(groups.values(), key=lambda g: g[0])


# ---- the rig ---------------------------------------------------------------------------------------------------

class Ctx:
    """Everything shared by the groups: skeleton, Loop's clips, finger poses."""
    def __init__(self, root):
        self.root = root
        self.mods_dir = os.path.join(root, 'mods')
        self.profile, self.mods = QRS.profile_mods(root)
        self.bsa = _bsa.listing(os.path.join(root, 'Stock Game', 'Data', 'Skyrim - Animations.bsa'))
        self.tmp = os.path.join(os.environ.get('TEMP', '.'), '_pistol_reload.hkx')
        with open(self.tmp, 'wb') as fh:
            fh.write(_bsa.read(self.bsa[0], self.bsa[1][R3P.SKELETON]))
        self.rig = R3P.Rig3P(anim_skyrim.load_skyrim_skeleton(self.tmp))
        self.ix = self.rig.index
        # Loop's OAR set loads from Patch Collection's copy (the standalone mod is disabled): the winning one
        self.loop_mod, self.loop_dir = next(((m, p) for m, p in ((m, QRS.find_ci(os.path.join(self.mods_dir, m), LOOP_SUB))
                                                                 for m in self.mods) if p), (None, None))
        if not self.loop_dir:
            sys.exit('no enabled mod in %s has %s' % (self.profile, '/'.join(LOOP_SUB)))
        self.release_path = os.path.join(self.loop_dir, CLIP)
        self.idle = self.loop_clip(IDLE)
        self.pinch = self.finger_pose(*PINCH_SOURCE)
        self.fist = self.finger_pose(*FIST_SOURCE)
        # grip frames in the right hand's frame: the fist's (Weapon node: the one-handed grip centre, +Y up the grip)
        # and the pinch's (between the thumb and index tips, the hand's own axes)
        self.fist_in_hand = self.local_weapon()
        self.pinch_in_hand = self.pinch_frame()
        self.left = Variant(self, 'left', lambda: self.loop_clip(CLIP), self.idle,
                            self.free_arm_idle(self.idle_clip(IDLE_SOURCE)), RIGHT_HALF, RIGHT_IDLE)
        self._right = None
        self._dual_left = None
        self._dual_right = None
        self._sheaths, self._stows = {}, {}

    def sheath(self, node, female):
        """(the animated bone `node` hangs from, that bone's frame -> `node`) in XPMSE's skeleton mesh for that sex (None:
        either, and both must agree), through its weapon-style nodes at their defaults. A sheath node the clips also
        animate (WeaponSword...) takes its transform from the clip in game: the mesh's must be the same (checked)."""
        key = (node, female)
        if key not in self._sheaths:
            if female is None:
                (a, m), (b, n) = self.sheath(node, False), self.sheath(node, True)
                if a != b or np.abs(m - n).max() > 0.05:
                    sys.exit('XPMSE puts %s elsewhere for each sex: add its type to STOW_SEXED' % node)
                self._sheaths[key] = (a, m)
                return self._sheaths[key]
            path = QRS.find_ci(os.path.join(self.mods_dir, XPMSE), XPMSE_NIF[female]) if XPMSE in self.mods else None
            if not path:
                sys.exit('%s is not enabled in %s (or has no %s)' % (XPMSE, self.profile, XPMSE_NIF[female][-1]))
            nodes = ADS.NifFile(path).nodes
            if node not in nodes:
                sys.exit('%s has no node %s' % (path, node))
            n = nodes[node]
            m = nif_local(n)
            if node in self.ix and np.abs(m - local_mat(self.idle, self.ix[node], 0)).max() > 0.01:
                sys.exit('%s: XPMSE\'s %s differs from the clips\' track' % (path, node))
            cur = n.parent
            while cur is not None and cur.name not in self.ix:
                m = nif_local(cur) @ m
                cur = cur.parent
            if cur is None:
                sys.exit('%s: %s hangs from no bone the clips animate' % (path, node))
            self._sheaths[key] = (cur.name, m)
        return self._sheaths[key]

    def stow(self, right, typ, female):
        """A one-handed melee weapon (OAR type `typ`) in the free hand, sheathed for the reload (STOW): the variant for a
        left-hand pistol, or (`right`) a right-hand one, solved in the mirrored world like the others. `female`: the
        sheath of that sex (STOW_SEXED), None for either. `real_sheath` (anchor bone, its frame -> the sheath) is the
        real world's, for check_stow."""
        key = (right, typ, female)
        if key in self._stows:
            return self._stows[key]
        item, node = STOW[typ]
        iw = self.ix['Weapon']
        name = 'stow-%s-%s%s' % ('right' if right else 'left', item, {None: '', True: '-female', False: '-male'}[female])
        if not right:
            idle = self.bsa_clip(FREE_IDLE_1HM)
            anchor, L = self.sheath(node, female)
            ia = self.ix[anchor]
            var = Variant(self, name, lambda: self.loop_clip(CLIP), self.idle, self.free_arm_idle(idle), RIGHT_HALF,
                          RIGHT_IDLE, dual=True, wl=local_mat(idle, iw, self.still_frame(idle)),
                          stow=lambda w: unscaled(w[ia]) @ L)
        else:
            right_v = self.right
            tmp = os.path.join(os.environ.get('TEMP', '.'), '_pistol_reload_dw.hkx')
            with open(tmp, 'wb') as fh:
                fh.write(_bsa.read(self.bsa[0], self.bsa[1]['\\'.join(ANIMS_3P).lower() + '\\' + FREE_IDLE_DW]))
            real = anim_skyrim.load_skyrim_animation(tmp)
            mir = self.mirrored(tmp)
            os.remove(tmp)
            f = self.still_frame(mir)
            anchor, L = self.sheath(node + 'Left', female)
            ia = self.ix[anchor]
            # the mirror per node: world_m = REFLECT world_r C (the left grip has no gun turn either way: unmirror())
            wr, wm = self.rig.world(real, f), self.rig.world(mir, f)
            fix = lambda r, m: np.linalg.inv(REFLECT @ unscaled(wr[self.ix[r]])) @ unscaled(wm[self.ix[m]])  # noqa: E731
            P = np.linalg.inv(fix(anchor, anchor)) @ L @ fix('Shield', 'Weapon')
            var = Variant(self, name, right_v.source, right_v.idle, self.free_arm_idle(mir), [], RIGHT_IDLE, dual=True,
                          wl=local_mat(mir, iw, f), stow=lambda w: unscaled(w[ia]) @ P)
            var.real_rest = (real, [f])
        var.real_sheath = (ia, L)
        self._stows[key] = var
        return var

    def shield(self, female):
        """A shield in the free (left) hand, slung on the back for the reload: the right-hand pistol's variant, solved
        mirrored. The free arm rests, whole, on SHIELD_ARM_SOURCE's at its least swaying frame (tools/07's shield arm,
        `shield_frame`). `female`: XPMSE's ShieldBack of that sex."""
        key = ('shield', female)
        if key in self._stows:
            return self._stows[key]
        right_v = self.right
        iw = self.ix['Weapon']
        real = self.idle_clip(SHIELD_ARM_SOURCE)
        mir = self.mirrored(self.idle_path(SHIELD_ARM_SOURCE))
        f = self.still_frame(mir)
        anchor, L = self.sheath(SHIELD_NODE, female)
        ia = self.ix[anchor]
        wr, wm = self.rig.world(real, f), self.rig.world(mir, f)
        fix = lambda r, m: np.linalg.inv(REFLECT @ unscaled(wr[self.ix[r]])) @ unscaled(wm[self.ix[m]])  # noqa: E731
        P = np.linalg.inv(fix(anchor, anchor)) @ L @ fix('Shield', 'Weapon')
        name = 'shield-right%s' % ('-female' if female else '-male')
        var = Variant(self, name, right_v.source, right_v.idle, self.free_arm_idle(mir), [], RIGHT_HALF + RIGHT_IDLE,
                      dual=True, wl=local_mat(mir, iw, f), stow=lambda w: unscaled(w[ia]) @ P, shield=True)
        var.real_rest = (real, [f])
        self.shield_frame = f
        var.real_sheath = (ia, L)
        self._stows[key] = var
        return var

    @property
    def dual_left(self):
        """Two pistols, the left one fired: the right hand tucks its gun, from Loop's right idle, frame 0 (traced)."""
        if self._dual_left is None:
            self.right   # the mirror and Loop's right-hand folder
            other = anim_skyrim.load_skyrim_animation(os.path.join(self.right_dir, IDLE_RIGHT))
            self._dual_left = Variant(self, 'dual-left', lambda: self.loop_clip(CLIP), self.idle, self.arm_at(other, 0),
                                      [], RIGHT_HALF + RIGHT_IDLE, dual=True, gun_axes=(1.0, 1.0),
                                      wl=local_mat(other, self.ix['Weapon'], 0), relaxed=self.left)
        return self._dual_left

    @property
    def dual_right(self):
        """Two pistols, the right one fired, in the mirrored world: the (mirrored) right hand tucks the real left gun,
        from Loop's left idle, frame 0, mirrored. That gun hangs on the mirrored Weapon node without the right hand's
        180 deg turn, so its barrel and grip axes there are measured against the real one (gun_axes)."""
        if self._dual_right is None:
            right = self.right
            real = self.loop_clip(IDLE)
            other = self.mirrored(os.path.join(self.loop_dir, IDLE))
            iw, ish = self.ix['Weapon'], self.ix['Shield']
            rm = unscaled(self.rig.world(other, 0)[iw])[:3, :3]
            rr = unscaled(self.rig.world(real, 0)[ish])[:3, :3]
            refl = np.diag([-1.0, 1.0, 1.0])
            sb = float(np.sign((rm @ [0, 1.0, 0]) @ (refl @ rr @ [0, 1.0, 0])))
            sg = float(np.sign((rm @ [1.0, 0, 0]) @ (refl @ rr @ [1.0, 0, 0])))
            self._dual_right = Variant(self, 'dual-right', right.source, right.idle, self.arm_at(other, 0), [],
                                       RIGHT_HALF + RIGHT_IDLE, dual=True, gun_axes=(sb, sg), wl=local_mat(other, iw, 0),
                                       relaxed=right)
        return self._dual_right

    def arm_at(self, anim, f):
        """{bone index: (rotation, scale)} of the right arm at frame f."""
        return {self.ix[n]: (list(anim.tracks[self.ix[n]].rotations[f]), list(anim.tracks[self.ix[n]].scales[f]))
                for n in RIGHT_HALF + RIGHT_IDLE}

    @property
    def right(self):
        """The right hand's variant, built in a MIRRORED world (Variant docstring)."""
        if self._right is None:
            self.mirror = LOOP.mirror_hkx.Mirror(self.mods_dir)
            self.right_dir = os.path.join(os.path.dirname(self.loop_dir), LOOP_SUB_RIGHT)
            if not os.path.isdir(self.right_dir):
                sys.exit('no %s next to %s' % (LOOP_SUB_RIGHT, self.loop_dir))
            src = self.mirrored(os.path.join(self.right_dir, CLIP_RIGHT))
            idle = self.mirrored(os.path.join(self.right_dir, IDLE_RIGHT))
            goetia = self.mirrored(self.idle_path(IDLE_SOURCE_RIGHT))
            self._right = Variant(self, 'right', lambda: copy.deepcopy(src), idle, self.free_arm_idle(goetia),
                                  [], RIGHT_HALF + RIGHT_IDLE)
        return self._right

    def mirrored(self, path, turned='Shield'):
        """A clip mirrored left <-> right (LoopPistolAnims/tools/mirror_hkx.py), the gun's 180 deg turn on `turned`."""
        out = os.path.join(os.environ.get('TEMP', '.'), '_pistol_reload_mirror.hkx')
        anim = self.mirror.mirror(path, out, turned=turned)
        os.remove(out)
        ADS.check_finite(anim, path)
        return anim

    def idle_path(self, source):
        mod, parts = source
        if mod not in self.mods:
            sys.exit('%s is not enabled in %s: find the 1hm_idle the free arm plays (ZenBoneTrace) and update the '
                     'IDLE_SOURCE constants' % (mod, self.profile))
        path = QRS.find_ci(os.path.join(self.mods_dir, mod), parts)
        if not path:
            sys.exit('no %s in %s' % ('/'.join(parts), mod))
        return path

    def idle_clip(self, source):
        return anim_skyrim.load_skyrim_animation(self.idle_path(source))

    def still_frame(self, idle, names=None):
        """The free right arm's frame in `idle` closest to all the others (the idle sways a few degrees over its loop;
        the game is at an unknown point of it when a shot switches the arm). `names`: those bones only."""
        bones = [self.ix[n] for n in (names or RIGHT_HALF + RIGHT_IDLE)]
        ang = lambda a, b: math.degrees(2 * math.acos(min(1.0, abs(sum(x * y for x, y in zip(a, b))))))  # noqa: E731
        return min(range(idle.num_frames), key=lambda f: max(ang(idle.tracks[b].rotations[f], idle.tracks[b].rotations[g])
                                                            for b in bones for g in range(0, idle.num_frames, 6)))

    def free_arm_idle(self, idle, names=None):
        """{bone index: (rotation, scale)} of the free right arm's idle at its still_frame() (`names`: those bones)."""
        f = self.still_frame(idle, names)
        return {self.ix[n]: (list(idle.tracks[self.ix[n]].rotations[f]), list(idle.tracks[self.ix[n]].scales[f]))
                for n in (names or RIGHT_HALF + RIGHT_IDLE)}

    def loop_clip(self, name):
        anim = anim_skyrim.load_skyrim_animation(os.path.join(self.loop_dir, name))
        ADS.check_finite(anim, name)
        return anim

    def bsa_clip(self, rel):
        key = '\\'.join(ANIMS_3P).lower() + '\\' + rel.lower()
        if key not in self.bsa[1]:
            sys.exit('%s not in Skyrim - Animations.bsa' % key)
        with open(self.tmp, 'wb') as fh:
            fh.write(_bsa.read(self.bsa[0], self.bsa[1][key]))
        return anim_skyrim.load_skyrim_animation(self.tmp)

    def bsa_floats(self, rel):
        """The float (node visibility) tracks of vanilla's clip `rel` (hkx_floats)."""
        key = '\\'.join(ANIMS_3P).lower() + '\\' + rel.lower()
        if key not in self.bsa[1]:
            sys.exit('%s not in Skyrim - Animations.bsa' % key)
        return HF.read(_bsa.read(self.bsa[0], self.bsa[1][key]))

    def finger_pose(self, rel, f):
        anim = self.bsa_clip(rel)
        return {self.ix[n]: list(anim.tracks[self.ix[n]].rotations[f]) for n in R_FINGERS}

    def local_weapon(self):
        rel = self.loop_clip(CLIP)
        return local_mat(rel, self.ix['Weapon'], 0)

    def pinch_frame(self):
        rel = self.loop_clip(CLIP)
        for i, q in self.pinch.items():
            rel.tracks[i].rotations[0] = q
        w = self.rig.world(rel, 0)
        hand = w[self.ix['NPC R Hand [RHnd]']]
        tip = lambda a, b: w[self.ix[b]][:3, 3] + FINGER_TIP * (w[self.ix[b]][:3, 3] - w[self.ix[a]][:3, 3])  # noqa: E731
        p = (tip('NPC R Finger01 [RF01]', 'NPC R Finger02 [RF02]') + tip('NPC R Finger11 [RF11]', 'NPC R Finger12 [RF12]')) / 2
        m = np.eye(4)
        m[:3, 3] = (np.linalg.inv(hand) @ np.r_[p, 1])[:3]
        return m


class Variant:
    """One hand's build. The solver always works on a LEFT-hand pistol rammed by the right hand: the left hand's variant
    on Loop's own clips; the right hand's on Loop's right-hand clips mirrored left <-> right (and Goetia's idle for a
    free LEFT arm, mirrored), its result mirrored back by main(). A double mirror is the identity (rest-corrected
    reflections, the gun's 180 deg turn on Shield one way and Weapon the other), so the body, Loop's first frames and the
    idle come back exactly. `source()` is a fresh copy of the shot clip, `idle` what the graph plays after it, and the
    free arm rests HALF bones halfway to the idle's, IDLE bones on it. A two-pistol variant (`dual`) runs on DUAL_BEATS:
    the free hand tucks the other gun (its attach node's local in that hand `wl`, its barrel and grip along the node's
    +Y and +X times `gun_axes`), and its free arm rests on the other gun's idle hold. A melee variant (`stow`, Ctx.stow)
    is a two-pistol one whose other item goes in its sheath: `stow(world)` is that sheath's 4x4 in this world (a
    `shield`: ShieldBack, Ctx.shield). A two-pistol variant's free arm rests on the one-gun variant `relaxed` while its
    gun is in the belt (RELAX_SKIP)."""
    def __init__(self, ctx, name, source, idle, free_rot, half, full, dual=False, gun_axes=(1.0, 1.0), wl=None,
                 stow=None, shift=0.0, relaxed=None, shield=False):
        self.ctx, self.name, self.source, self.idle = ctx, name, source, idle
        self.free_rot, self.half, self.full = free_rot, half, full
        self.dual, self.gun_axes, self.wl, self.stow, self.shift = dual, gun_axes, wl, stow, shift
        self.relaxed, self.shield = relaxed, shield
        self.letgo = None         # a shield's let-go and approach (4x4 in ShieldBack's frame): shield_letgo()
        self.real_rest = self.real_sheath = None
        self.beats = {k: v + shift for k, v in (DUAL_BEATS if dual else BEATS).items()}
        lead = (DUAL_SHIFT if dual else 0.0) + shift
        self.load_at, self.unload_at = LOAD_AT + lead, UNLOAD_AT + lead
        self.motion_end = (DUAL_MOTION_END if dual else BEATS['end']) + shift

    def rest(self, anim, f):
        """The free arm as the game shows it before the switch, written into frame f."""
        ix = self.ctx.ix
        for n in self.half:
            b = ix[n]
            q, sc = self.free_rot[b]
            tr = anim.tracks[b]
            tr.rotations[f] = [float(x) for x in ADS.slerp(tr.rotations[f], q, 0.5)]
            tr.scales[f] = [float(x) for x in ADS.lerp(tr.scales[f], sc, 0.5)]
        for n in self.full:
            b = ix[n]
            q, sc = self.free_rot[b]
            anim.tracks[b].rotations[f], anim.tracks[b].scales[f] = list(q), list(sc)
        if self.stow:     # the weapon's grip where its idle holds it
            anim.tracks[ix['Weapon']].translations[f] = [float(x) for x in self.wl[:3, 3]]


def body_frame(w, ix):
    """(right, forward, up) of the chest: shoulders' line levelled; the stance turns the torso ~30 deg."""
    x = w[ix['NPC R UpperArm [RUar]']][:3, 3] - w[ix['NPC L UpperArm [LUar]']][:3, 3]
    x[2] = 0
    x = unit(x)
    z = np.array([0, 0, 1.0])
    return x, np.cross(z, x), z


def arm_chain(rig, w, side, W, pole_dir):
    """Shoulder-elbow-hand IK for the wrist (hand bone origin) at W, the elbow toward pole_dir (world): (elbow, reached
    wrist, upper arm and forearm world rotations, miss). The rotations are the smallest turns from the pose `w`, exactly
    as solve_arm() writes them."""
    iu, ifa, ih = (rig.index[n] for n in SIDES[side][:3])
    S, E0, H0 = w[iu][:3, 3], w[ifa][:3, 3], w[ih][:3, 3]
    a, b = np.linalg.norm(E0 - S), np.linalg.norm(H0 - E0)
    d = max(np.linalg.norm(W - S), 1e-6)
    dc = min(max(d, abs(a - b) + 1e-3), a + b - 1e-3)
    u = (W - S) / d
    v = np.asarray(pole_dir, dtype=float) - u * (u @ pole_dir)
    v = unit(v) if np.linalg.norm(v) > 1e-6 else unit(np.cross(u, [0, 0, 1.0]))
    cos_a = (a * a + dc * dc - b * b) / (2 * a * dc)
    E = S + a * (cos_a * u + math.sqrt(max(0.0, 1 - cos_a * cos_a)) * v)
    Hc = S + u * dc
    q1 = R3P.rot_between(unit(E0 - S), unit(E - S))
    upper = q1 @ (w[iu][:3, :3] / np.linalg.norm(w[iu][:3, 0]))
    q2 = R3P.rot_between(unit(q1 @ (H0 - E0)), unit(Hc - E))
    fore = q2 @ q1 @ (w[ifa][:3, :3] / np.linalg.norm(w[ifa][:3, 0]))
    return E, Hc, upper, fore, float(np.linalg.norm(Hc - W))


def wrist(rig, side, fore, hand_rot):
    """(bend, roll) in degrees of the hand against the forearm, from the skeleton's straight, unrolled wrist: the roll
    about the forearm's axis (the hand's local translation) and the bend left once it is taken out."""
    ih = rig.index[SIDES[side][2]]
    ref = rig.ref[ih]
    axis = unit(np.array(ref.translation, dtype=float))
    q = ADS.mat_quat(fore.T @ hand_rot @ ADS.quat_mat(ref.rotation).T)
    tw = math.atan2(np.dot(q[:3], axis), q[3])
    roll = (math.degrees(2 * tw) + 180.0) % 360.0 - 180.0
    qt = [axis[0] * math.sin(tw), axis[1] * math.sin(tw), axis[2] * math.sin(tw), math.cos(tw)]
    # swing = q * conj(twist): its angle
    x1, y1, z1, w1 = q
    x2, y2, z2, w2 = -qt[0], -qt[1], -qt[2], qt[3]
    sw = w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2
    bend = math.degrees(2 * math.acos(min(1.0, abs(sw))))
    return bend, roll


def wrist_cost(bend, roll):
    """Degrees of strain; a wrist bends ~70 deg and rolls ~90 deg either way before it looks broken."""
    return bend + 0.5 * abs(roll) + 4.0 * max(0.0, bend - 60.0) + 4.0 * max(0.0, abs(roll) - 80.0)


def elbow_cost(side, S, E, body):
    """An elbow above the shoulder or across the chest costs (per unit)."""
    right, fwd, up = body
    out = right if side == 'R' else -right
    return 0.6 * max(0.0, (E - S) @ up) + 1.0 * max(0.0, -((E - S) @ out))


def seg_dist(p, a, b):
    ab = b - a
    t = max(0.0, min(1.0, float((p - a) @ ab / max(ab @ ab, 1e-9))))
    return float(np.linalg.norm(p - (a + ab * t)))


def face(rig, w):
    """A point in the middle of the face (the head bone sits at the back of the skull's base)."""
    h = w[rig.index['NPC Head [Head]']]
    return (h @ np.r_[FACE, 1])[:3]


def head_clearance(face_p, S, E, W, grip):
    return min(seg_dist(face_p, S, E), seg_dist(face_p, E, W), seg_dist(face_p, W, grip))


def solve_arm(rig, anim, f, side, target, pole_dir, k=1.0, twist_k=None):
    """Hand bone of `side` onto `target` (4x4 world): shoulder-elbow-hand IK, the elbow toward pole_dir (world),
    blended with the frame's own elbow by 1 - k (k = 0 reproduces the pose's own arm when the target is its own hand).
    The wrist roll about the forearm goes onto the twist bones (TWIST_SHARE, blended with the pose's own by twist_k,
    default k). Returns (how far the hand ended from target, (bend, roll) of the wrist)."""
    twist_k = k if twist_k is None else twist_k
    iu, ifa, ih, it1, it2 = (rig.index[n] for n in SIDES[side])
    w = rig.world(anim, f)
    S, E0, H0 = w[iu][:3, 3], w[ifa][:3, 3], w[ih][:3, 3]
    own = E0 - S - unit(H0 - S) * ((E0 - S) @ unit(H0 - S))       # the pose's own elbow, off its shoulder-hand line
    if np.linalg.norm(own) > 1e-6:
        pole_dir = unit(own) * (1 - k) + unit(pole_dir) * k
    base_twist = [list(anim.tracks[b].rotations[f]) for b in (it1, it2)]
    E, Hc, upper, fore, _ = arm_chain(rig, w, side, target[:3, 3], pole_dir)
    R3P.set_rotation(anim, iu, f, (w[rig.parents[iu]][:3, :3] / np.linalg.norm(w[rig.parents[iu]][:3, 0])).T @ upper)
    R3P.set_rotation(anim, ifa, f, upper.T @ fore)
    hand_rot = target[:3, :3] / np.linalg.norm(target[:3, 0])
    hand_local = fore.T @ hand_rot
    R3P.set_rotation(anim, ih, f, hand_local)
    axis = unit(np.array(anim.tracks[ih].translations[f], dtype=float))
    bend, roll = wrist(rig, side, fore, hand_rot)
    for ib, share, q0 in zip((it1, it2), TWIST_SHARE, base_twist):
        R3P.set_rotation(anim, ib, f, rot_axis(axis, roll * share) @ ADS.quat_mat(rig.ref[ib].rotation))
        anim.tracks[ib].rotations[f] = [float(x) for x in ADS.slerp(q0, anim.tracks[ib].rotations[f], twist_k)]
    return float(np.linalg.norm(rig.world(anim, f)[ih][:3, 3] - target[:3, 3])), (bend, roll)


def pole_dirs(S, W, steps):
    """Elbow directions around the shoulder-wrist line, starting straight down."""
    u = unit(W - S)
    e1 = np.array([0, 0, -1.0]) - u * (-u[2])
    e1 = unit(e1) if np.linalg.norm(e1) > 1e-6 else unit(np.cross(u, [1.0, 0, 0]))
    e2 = np.cross(u, e1)
    return [math.cos(a) * e1 + math.sin(a) * e2 for a in np.linspace(0, 2 * math.pi, steps, endpoint=False)]


# ---- the motion ------------------------------------------------------------------------------------------------

def rod_length(c, scale=1.0):
    """The rod for muzzle c (mesh units) on a gun shown at `scale` (tools/02 builds the meshes with the same call)."""
    return min(ROD_MAX, c[1] * scale - ROD_SHORT)


def targets(load, c, axis, radius, body, pelvis):
    """Right-hand beats: {beat: (kind, grip position, direction, finger weight)} given the pistol's load pose (4x4 world
    of the Shield node). Kind 'pinch': the pinch point, the fingers' direction; 'fist': the grip centre (the Weapon
    node), the grip's +Y (up the rod)."""
    right, fwd, up = body
    R = load[:3, :3]
    muzzle = (load @ np.r_[c, 1])[:3]
    bore = unit(R @ axis)
    rod_side = unit(R @ np.array([1.0, 0, 0]) - bore * (bore @ (R @ np.array([1.0, 0, 0]))))   # the pistol's +X
    stow = muzzle + rod_side * (radius + ROD_GAP + ROD_RADIUS)          # the stowed rod's line, at the muzzle face
    Lr = rod_length(c)
    pouch = pelvis + right * POUCH[0] + fwd * POUCH[1] + up * POUCH[2]
    over = muzzle + bore * (BALL_ABOVE_MUZZLE + BALL_RADIUS)
    grab = ROD_TOP_STOWED - ROD_ABOVE_FIST
    out = ROD_TOP_STOWED + Lr + 0.5 - ROD_ABOVE_FIST                     # the rod's foot just clears the muzzle
    down = unit(-up + fwd * 0.3)
    k = {'pouch_near': ('pinch', pouch + up * 5, down, 0.5),
         'pouch': ('pinch', pouch, down, 1.0),
         'over_muzzle': ('pinch', over, -bore, 1.0),
         'drop': ('pinch', over + bore * 0.8, -bore, 0.4),
         'grab': ('fist', stow + bore * grab, bore, 1.0),
         'drawn': ('fist', stow + bore * out, bore, 1.0),
         'over_bore': ('fist', muzzle + bore * out, bore, 1.0),
         'rammed': ('fist', muzzle + bore * FIST_ABOVE_MUZZLE, bore, 1.0),
         'stroke_up': ('fist', muzzle + bore * (FIST_ABOVE_MUZZLE + STROKE), bore, 1.0),
         'stroke_down': ('fist', muzzle + bore * FIST_ABOVE_MUZZLE, bore, 1.0),
         'withdrawn': ('fist', muzzle + bore * out, bore, 1.0),
         'over_stow': ('fist', stow + bore * out, bore, 1.0),
         'stowed': ('fist', stow + bore * grab, bore, 1.0)}
    return k, dict(muzzle=muzzle, bore=bore, stow=stow, rod_side=rod_side, Lr=Lr)


def grip_offset(ctx, kind):
    """(grip centre in the hand's frame, the grip's 'direction' axis in the hand's frame): the fist's Weapon node and
    its +Y; the pinch point and the fingers (+Z)."""
    if kind == 'fist':
        g = ctx.fist_in_hand
        return g[:3, 3], unit(g[:3, :3] @ np.array([0, 1.0, 0]))
    if kind == 'carry':       # holding the other gun: its attach node (build_clip sets ctx.carry_in_hand)
        g = ctx.carry_in_hand
        return g[:3, 3], unit(g[:3, :3] @ np.array([0, 1.0, 0]))
    return ctx.pinch_in_hand[:3, 3], np.array([0, 0, 1.0])


def hand_at(ctx, kind, pos, hand_rot):
    off, _ = grip_offset(ctx, kind)
    m = np.eye(4)
    m[:3, :3] = hand_rot
    m[:3, 3] = pos - hand_rot @ off
    return m


def solve_beat(ctx, w, side, kind, pos, dirn, body, steps=24, roll_step=15, prev=None):
    """The least strained way for `side`'s hand to hold `kind` at `pos` along `dirn`: (hand rotation 3x3, elbow
    direction, cost, miss). Searched over the elbow's direction around the shoulder-wrist line; the hand starts from the
    forearm's straight wrist and turns the least way that lines its grip axis up with `dirn` (a fist also tries every
    roll about the rod; a pinch only turns PINCH_AIM of the way: fingers roughly toward the muzzle is enough)."""
    rig = ctx.rig
    ih = rig.index[SIDES[side][2]]
    iu = rig.index[SIDES[side][0]]
    neutral = ADS.quat_mat(rig.ref[ih].rotation)
    off, g = grip_offset(ctx, kind)
    S = w[iu][:3, 3]
    face_p = face(rig, w)
    best = None
    guess = w[ih][:3, :3] / np.linalg.norm(w[ih][:3, 0])
    # a fist holds the rod either way up (thumb toward or away from the muzzle): props() lays the rod on the bore
    signs = (1.0, -1.0) if kind == 'fist' else (1.0,)
    for pole in pole_dirs(S, pos - guess @ off, steps):
        for sign in signs:
            want = unit(dirn) * sign
            H = guess
            for _ in range(3):
                E, _, _, fore, miss = arm_chain(rig, w, side, pos - H @ off, pole)
                Hn = fore @ neutral
                turn = R3P.rot_between(unit(Hn @ g), want)
                if kind == 'fist':
                    H0 = turn @ Hn
                    H = min((rot_axis(want, r) @ H0 for r in range(-180, 180, roll_step)),
                            key=lambda h: wrist_cost(*wrist(rig, side, fore, h)) +
                            (CONTINUITY * angle_between(prev[0], h) if prev else 0.0))
                else:
                    H = blend_mat(rot4(Hn), rot4(turn @ Hn), PINCH_AIM)[:3, :3]
            E, Wc, _, fore, miss = arm_chain(rig, w, side, pos - H @ off, pole)
            clear = head_clearance(face_p, S, E, Wc, pos)
            elbow = unit(E - S - unit(pos - S) * ((E - S) @ unit(pos - S)))
            cost = (wrist_cost(*wrist(rig, side, fore, H)) + elbow_cost(side, S, E, body) + 50.0 * miss +
                    40.0 * max(0.0, HEAD_CLEAR - clear))
            if prev:   # neighbouring beats alike: the frames between them must not swing the wrist through a flip
                cost += CONTINUITY * angle_between(prev[0], H) + 0.5 * CONTINUITY * angle_between_dirs(prev[1], elbow)
            if best is None or cost < best[2]:
                best = (H, elbow, cost, miss)
    return best


def belt_pose(ctx, w, body, var):
    """Where the other gun goes: its attach node (the grip) in front of the belly (BELT_*), the barrel down, tilted
    forward / sideways, the grip turned about the barrel; the hand that carries it holds it as in its idle (var.wl). The
    least strained grip that reaches, with the whole barrel BELT_CLEAR in front of the pelvis. Returns (attach node 4x4
    world, hand rotation, elbow direction, cost, parameters)."""
    rig, ix = ctx.rig, ctx.ix
    right, fwd, up = body
    pelvis = w[ix['NPC Pelvis [Pelv]']][:3, 3]
    S = w[ix['NPC R UpperArm [RUar]']][:3, 3]
    sb, sg = var.gun_axes
    wl_rot = var.wl[:3, :3] / np.linalg.norm(var.wl[:3, 0])
    wl_t = var.wl[:3, 3]
    best = None
    for r_off in BELT_RIGHT:
        for f_off in BELT_FWD:
            for u_off in BELT_UP:
                pos = pelvis + right * r_off + fwd * f_off + up * u_off
                for tilt_f in (0.0, 15.0, 30.0):
                    for tilt_r in (-20.0, 0.0, 20.0):
                        d = unit(-up + fwd * math.tan(math.radians(tilt_f)) + right * math.tan(math.radians(tilt_r)))
                        if min(((pos + d * L) - pelvis) @ fwd for L in np.linspace(0.0, BARREL_MAX, 6)) < BELT_CLEAR:
                            continue
                        g0 = unit(fwd - d * (d @ fwd))
                        for yaw in range(0, 360, 30):
                            g = rot_axis(d, yaw) @ g0
                            xc, yc = sg * g, sb * d
                            rb = np.column_stack([xc, yc, np.cross(xc, yc)])
                            H = rb @ wl_rot.T
                            hand = pos - H @ wl_t
                            for pole in pole_dirs(S, hand, 12):
                                E, _, _, fore, miss = arm_chain(rig, w, 'R', hand, pole)
                                if miss > 0.05:
                                    continue
                                cost = (wrist_cost(*wrist(rig, 'R', fore, H)) + elbow_cost('R', S, E, body) +
                                        0.2 * abs(tilt_r) + 0.1 * tilt_f)
                                if best is None or cost < best[3]:
                                    m = np.eye(4)
                                    m[:3, :3], m[:3, 3] = rb, pos
                                    elbow = unit(E - S - unit(hand - S) * ((E - S) @ unit(hand - S)))
                                    best = (m, H, elbow, cost, dict(right=r_off, fwd=f_off, up=u_off, tilt_f=tilt_f,
                                                                    tilt_r=tilt_r, yaw=yaw))
    if best is None:
        sys.exit('%s: no belt pose the hand reaches with the barrel clear of the body' % var.name)
    return best


def solve_carry(ctx, w, H, pos, body, prev=None, steps=24):
    """The hand holding the other gun's grip at `pos` with rotation H (both fixed): the least strained elbow.
    Returns (H, elbow direction, cost, miss)."""
    rig = ctx.rig
    S = w[rig.index['NPC R UpperArm [RUar]']][:3, 3]
    off, _ = grip_offset(ctx, 'carry')
    hand = pos - H @ off
    face_p = face(rig, w)
    best = None
    for pole in pole_dirs(S, hand, steps):
        E, Wc, _, fore, miss = arm_chain(rig, w, 'R', hand, pole)
        elbow = unit(E - S - unit(hand - S) * ((E - S) @ unit(hand - S)))
        cost = (wrist_cost(*wrist(rig, 'R', fore, H)) + elbow_cost('R', S, E, body) + 50.0 * miss +
                40.0 * max(0.0, HEAD_CLEAR - head_clearance(face_p, S, E, Wc, pos)))
        if prev:
            cost += 0.5 * CONTINUITY * angle_between_dirs(prev[1], elbow)
        if best is None or cost < best[2]:
            best = (H, elbow, cost, miss)
    return best


def stow_grip(wl, roll, reverse):
    """The melee weapon's attach node in the hand (4x4): the idle's grip `wl` turned `roll` degrees on the handle (about
    the blade, +Y) and, `reverse`, the blade out of the little finger's side (half a turn about +X). Both turns are
    about the grip point, so the hand stays on the handle."""
    m = np.eye(4)
    m[:3, :3] = rot_axis([1.0, 0.0, 0.0], 180.0 if reverse else 0.0) @ rot_axis([0.0, 1.0, 0.0], roll)
    return unscaled(wl) @ m


def stow_hold(ctx, w, item, body, reverse, prev=None, rolls=None):
    """The hand holding the melee weapon at `item` (4x4 world) in the grip (stow_grip, `reverse` fixed) whose roll
    strains the wrist least: (hand rotation, elbow direction, grip 4x4, cost, miss, (wrist bend, roll), roll). `rolls`:
    the grip rolls tried (a shield's grip never turns: (0,))."""
    rig = ctx.rig
    best = None
    for roll in (range(-180, 180, STOW_ROLL_STEP) if rolls is None else rolls):
        g = stow_grip(ctx.carry_in_hand, roll, reverse)
        H = item[:3, :3] @ g[:3, :3].T
        H, pole, cost, miss = solve_carry(ctx, w, H, item[:3, 3], body, prev=prev)
        cost += 0.02 * abs(roll)
        if prev:
            cost += CONTINUITY * angle_between(prev[0], H)
        if best is None or cost < best[3]:
            hand = item[:3, 3] - H @ grip_offset(ctx, 'carry')[0]
            fore = arm_chain(rig, w, 'R', hand, pole)[3]
            best = (H, pole, g, cost, miss, wrist(rig, 'R', fore, H), roll)
    return best


def flip_grip(wl, roll, reverse, u, path):
    """The grip `u` (0..1) of the way from the idle's (wl) to a stow beat's (stow_grip(wl, roll, reverse)), along
    `path` = (phi, sign): a reverse grip's half turn about the axis phi degrees round the blade from +X (in direction
    `sign`) and the roll about the blade that makes every path end on the same grip, both progressive, so the blade
    swings one known way through the fingers (a blend of the two grips picked its own: through the hips)."""
    m = np.eye(4)
    if not reverse:
        m[:3, :3] = rot_axis([0.0, 1.0, 0.0], roll * u)
        return unscaled(wl) @ m
    phi, sign = path
    a = [math.cos(math.radians(phi)), 0.0, math.sin(math.radians(phi))]
    end = rot_axis(a, 180.0).T @ rot_axis([1.0, 0.0, 0.0], 180.0) @ rot_axis([0.0, 1.0, 0.0], roll)   # about +Y
    r = math.degrees(math.atan2(end[0, 2], end[0, 0]))
    m[:3, :3] = rot_axis(a, sign * 180.0 * u) @ rot_axis([0.0, 1.0, 0.0], r * u)
    return unscaled(wl) @ m


FLIP_PATHS = [(phi, sign) for phi in range(0, 180, 30) for sign in (1.0, -1.0)]


BODY_SEGMENTS = [('NPC Pelvis [Pelv]', 'NPC Spine2 [Spn2]'), ('NPC Spine2 [Spn2]', 'NPC Neck [Neck]'),
                 ('NPC L Thigh [LThg]', 'NPC L Calf [LClf]'), ('NPC L Calf [LClf]', 'NPC L Foot [Lft ]'),
                 ('NPC R Thigh [RThg]', 'NPC R Calf [RClf]'), ('NPC R Calf [RClf]', 'NPC R Foot [Rft ]')]
BLADE_SAMPLES = (-8.0, 15.0, 30.0, 45.0, 60.0)   # along a flipping weapon (pommel to a longsword's tip): clearance


def blade_clearance(ctx, w, item):
    """The least distance from the BLADE_SAMPLES on `item` to the spine and legs (bone lines)."""
    segs = [(w[ctx.ix[a]][:3, 3], w[ctx.ix[b]][:3, 3]) for a, b in BODY_SEGMENTS]
    pts = [(item @ np.r_[0.0, y, 0.0, 1.0])[:3] for y in BLADE_SAMPLES]
    return min(seg_dist(p, a, b) for p in pts for a, b in segs)


def stow_glide(t, beats):
    """How far (0..1) the weapon is out of the sheath at t while the hand is off it: out as the hand left it at
    'tucked', in by 'release', out again by 'regrip'."""
    glide = beats['release'] - beats['tucked']
    if t <= beats['release']:
        return 1.0 - smooth((t - beats['tucked']) / glide)
    return smooth((t - (beats['regrip'] - glide)) / glide)


SHIELD_ARM_ROOT = 'NPC L Clavicle [LClv]'


def shield_arm(ctx):
    """The shield arm in the real world (tools/07, and the shield reloads' aim copies), set the way the shield reload
    rests (Variant.rest, unmirror): {bone: (translation or None to keep the clip's, rotation, scale)} over the left
    clavicle's subtree, SHIELD_ARM_SOURCE at the frame the reload rests on; the bone offsets stay the clip's but for
    `Shield` (the grip, Variant.wl), and AnimObjectL (the props' node, which unmirror rebuilds on Loop's idle) stays
    the clip's. Copying the source's offsets too put the thumb 2.6 units off the reload's ends."""
    src, (f,) = ctx.shield(False).real_rest
    root, grip, props = ctx.ix[SHIELD_ARM_ROOT], ctx.ix['Shield'], ctx.ix['AnimObjectL']
    pose = {}
    for b in range(len(ctx.rig.parents)):
        p = b
        while p >= 0 and p != root:
            p = ctx.rig.parents[p]
        if p == root and b != props:
            tr = src.tracks[b]
            pose[b] = (list(tr.translations[f]) if b == grip else None, list(tr.rotations[f]), list(tr.scales[f]))
    return pose


def with_arm(anim, pose):
    """A copy of `anim` with the bones of `pose` ({bone: (translation or None, rotation, scale)}) on it in every
    frame."""
    out = copy.deepcopy(anim)
    for b, (t, q, s) in pose.items():
        tr = out.tracks[b]
        if t is not None:
            tr.translations = [list(t) for _ in range(out.num_frames)]
        tr.rotations = [list(q) for _ in range(out.num_frames)]
        tr.scales = [list(s) for _ in range(out.num_frames)]
    return out


def stowed_at(var, w, t, beats):
    """Where the other item hangs at t while the hand is off it (4x4 world): a melee weapon gliding along its blade into
    the sheath and out, a shield from where the hand let it go onto ShieldBack and back (shield_letgo)."""
    u = stow_glide(t, beats)
    if var.shield:
        return var.stow(w) @ blend_mat(np.eye(4), var.letgo[0], u)
    return var.stow(w) @ ADS.trs([0.0, var.stow_sign * var.stow_depth * u, 0.0], [0, 0, 0, 1.0], 1.0)


SHIELD_POINTS = np.array([[r * math.cos(a), r * math.sin(a), -4.0, 1.0] for r in SHIELD_RIM
                          for a in np.linspace(0.0, 2 * math.pi, 8 if r else 1, endpoint=False)])


def shield_clearance(ctx, w, item):
    """The least distance from the shield's sample points (SHIELD_POINTS on `item`, 4x4 world) to the spine and legs."""
    segs = [(w[ctx.ix[a]][:3, 3], w[ctx.ix[b]][:3, 3]) for a, b in BODY_SEGMENTS]
    return min(seg_dist((item @ p)[:3], a, b) for p in SHIELD_POINTS for a, b in segs)


def shield_letgo(ctx, anim, var, body):
    """Where the free hand lets go of the shield behind the back, and the approach it comes in by: (let-go, approach),
    each a 4x4 in ShieldBack's frame. From SHIELD_DOWN / OUT / SIDE (body frame at 'tucked') and a turn in the shield's
    plane (SHIELD_ROLL): the nearest to ShieldBack that the hand holds with the wrist inside SHIELD_WRIST (at the approach
    SHIELD_APPROACH_WRIST) and the shield SHIELD_CLEAR off the body, at the approach too (that much further toward the
    free side and out). Cached on `var` (the body at 'tucked' is the same for every pistol)."""
    if var.letgo is not None:
        return var.letgo
    rig, fd = ctx.rig, anim.frame_duration
    right, _, up = body
    w = rig.world(anim, int(round(var.beats['tucked'] / fd)))
    back = var.stow(w)
    out_dir = -back[:3, 2]            # the shield's face points away from the back
    found = []
    for down in SHIELD_DOWN:
        for out in SHIELD_OUT:
            for side in SHIELD_SIDE:
                off = -up * down + out_dir * out + right * side
                app = off + right * SHIELD_APPROACH[0] + out_dir * SHIELD_APPROACH[1]
                for roll in SHIELD_ROLL:
                    spin = rot4(rot_axis([0.0, 0.0, 1.0], roll))
                    cost0 = down + 0.5 * out + 0.5 * abs(side) + 0.1 * abs(roll)
                    if found and cost0 >= found[0][0]:
                        continue
                    ok, hold_cost = True, 0.0
                    for o, limit in ((off, SHIELD_WRIST), (app, SHIELD_APPROACH_WRIST)):
                        item = back.copy()
                        item[:3, 3] += o
                        item = item @ spin
                        if shield_clearance(ctx, w, item) < SHIELD_CLEAR:
                            ok = False
                            break
                        hold = stow_hold(ctx, w, item, body, False, rolls=(0,))
                        if hold[4] > 0.05 or abs(hold[5][0]) > limit[0] or abs(hold[5][1]) > limit[1]:
                            ok = False
                            break
                        hold_cost += hold[3]
                    if not ok:
                        continue

                    def local(o):
                        m = back.copy()
                        m[:3, 3] += o
                        return np.linalg.inv(back) @ m @ spin
                    found = [(cost0 + 0.05 * hold_cost, local(off), local(app),
                              dict(down=down, out=out, side=side, roll=roll))]
    if not found:
        sys.exit('%s: the hand lets go of the shield nowhere near its back' % var.name)
    var.letgo = (found[0][1], found[0][2], found[0][3])
    return var.letgo


def angle_between(a, b):
    """Degrees between two rotations (3x3)."""
    return math.degrees(math.acos(max(-1.0, min(1.0, (np.trace(a.T @ b) - 1) / 2))))


def angle_between_dirs(a, b):
    return math.degrees(math.acos(max(-1.0, min(1.0, float(unit(a) @ unit(b))))))


def left_hold(ctx, w, load, slide, shield_local, body, steps=12):
    """The left hand holding the pistol in its load pose, `slide` units up the pistol from its grip (a long pistol is
    held by the lock): (hand 4x4 world, elbow direction, cost, miss)."""
    rig = ctx.rig
    iu = rig.index[SIDES['L'][0]]
    hand = load @ ADS.trs([0.0, slide, 0.0], [0, 0, 0, 1.0], 1.0) @ np.linalg.inv(shield_local)
    H = hand[:3, :3] / np.linalg.norm(hand[:3, 0])
    S = w[iu][:3, 3]
    best = None
    for pole in pole_dirs(S, hand[:3, 3], steps):
        E, _, _, fore, miss = arm_chain(rig, w, 'L', hand[:3, 3], pole)
        cost = wrist_cost(*wrist(rig, 'L', fore, H)) + elbow_cost('L', S, E, body) + 50.0 * miss
        if best is None or cost < best[2]:
            best = (hand, unit(E - S - unit(hand[:3, 3] - S) * ((E - S) @ unit(hand[:3, 3] - S))), cost, miss)
    return best


def load_pose(ctx, w, c, axis, radius):
    """Candidate load poses for the pistol (4x4 world of the Shield node), cheapest first: [(cost, pose, parameters)].
    Muzzle up in front of the body, as low and as upright as both arms allow, the left wrist least strained.
    Candidates: muzzle height (from the shoulders), distance ahead, tilt forward and sideways, roll about the bore (the
    rod's side from forward toward the right), and how far up the pistol the left hand holds it (long pistols). The left
    hand must reach exactly; the right hand's beats only roughly (REACH_SLACK): build_clip() solves them on the cheapest
    LOAD_CANDIDATES (solve_beat) and keeps the least strained that reaches."""
    ix = ctx.ix
    body = right, fwd, up = body_frame(w, ix)
    mid = (w[ix['NPC R UpperArm [RUar]']][:3, 3] + w[ix['NPC L UpperArm [LUar]']][:3, 3]) / 2
    pelvis = w[ix['NPC Pelvis [Pelv]']][:3, 3]
    iu, ifa, ih = (ix[n] for n in SIDES['R'][:3])
    SR = w[iu][:3, 3]
    arm_r = np.linalg.norm(w[ifa][:3, 3] - SR) + np.linalg.norm(w[ih][:3, 3] - w[ifa][:3, 3])
    shield_local = np.linalg.inv(unscaled(w[ix['NPC L Hand [LHnd]']])) @ unscaled(w[ix['Shield']])   # world units
    fist_off, _ = grip_offset(ctx, 'fist')
    pinch_off, _ = grip_offset(ctx, 'pinch')
    slides = [s for s in (0.0, 6.0, 12.0, 18.0, 24.0) if c[1] - s >= 16.0]
    found = []
    for tilt_f in (0.0, 10.0, 20.0):
        for tilt_r in (-20.0, -10.0, 0.0, 10.0, 20.0, 30.0):
            b = unit(up + fwd * math.tan(math.radians(tilt_f)) + right * math.tan(math.radians(tilt_r)))
            for roll in (0.0, 30.0, 60.0):
                # Loop's upright idle keeps the underside (+X, the rod's side) away from the body; rolled toward the
                # right it faces the ramming hand
                xa = unit(fwd - b * (b @ fwd))
                xa = rot_axis(b, -roll) @ xa
                R = np.column_stack([xa, b, np.cross(xa, b)])
                R = R @ basis_map(np.array([1.0, 0, 0]), np.array([0, 1.0, 0]), np.array([1.0, 0, 0]), axis).T
                for height in np.arange(-16.0, 14.0, 2.0):
                    for ahead in np.arange(12.0, 32.0, 2.0):
                        load = np.eye(4)
                        load[:3, :3] = R
                        load[:3, 3] = mid + up * height + fwd * ahead - R @ c
                        ks, _ = targets(load, c, axis, radius, body, pelvis)
                        # the right hand's beats: the grip half its offset beyond the wrist (the hand points at it);
                        # solve_beat() then checks each exactly
                        slack = min(arm_r + 0.5 * np.linalg.norm(fist_off if kd == 'fist' else pinch_off) -
                                    np.linalg.norm(p - SR) for kd, p, _, _ in ks.values())
                        if slack < REACH_SLACK:
                            continue
                        for slide in slides:
                            hand, pole, lcost, miss = left_hold(ctx, w, load, slide, shield_local, body)
                            if miss > 0.01:
                                continue
                            fist_top = max(p @ up for kd, p, _, _ in ks.values() if kd == 'fist') - SR @ up
                            cost = (abs(height + 8.0) + 0.5 * abs(ahead - 22.0) + 0.1 * (tilt_f + tilt_r) + 0.05 * roll +
                                    0.3 * slide + 0.15 * lcost + 0.6 * max(0.0, fist_top))
                            found.append((cost, load, dict(height=height, ahead=ahead, tilt_f=tilt_f, tilt_r=tilt_r,
                                                           roll=roll, slide=slide, slack=slack, left_cost=lcost,
                                                           left_pole=pole)))
    if not found:
        sys.exit('no load pose lets both arms reach every beat')
    return sorted(found, key=lambda x: x[0])


def interp_keys(keys, t):
    """keys: [(time, value)] sorted; returns (i, s): between keys i and i+1 at smoothstep fraction s."""
    if t <= keys[0][0]:
        return 0, 0.0
    for i in range(len(keys) - 1):
        if t <= keys[i + 1][0]:
            return i, smooth((t - keys[i][0]) / (keys[i + 1][0] - keys[i][0]))
    return len(keys) - 2, 1.0


def rot4(r):
    m = np.eye(4)
    m[:3, :3] = r
    return m


def build_clip(ctx, label, c, axis, radius, var):
    """The reload clip for one barrel, on `var`'s shot clip (Variant: the right hand's in its mirrored world). Returns
    (anim, info, annotations added, worst misses, worst wrists, load pose)."""
    rig, ix = ctx.rig, ctx.ix
    anim = var.source()
    fd = anim.frame_duration
    if abs(fd - LOOP_FD) > 1e-5:
        sys.exit('%s: Loop\'s clip runs %.5f s a frame, not LOOP_FD %.5f (TRIM)' % (label, fd, LOOP_FD))
    beats = var.beats
    n = int(round(beats['end'] / fd)) + 1
    n_motion = int(round(var.motion_end / fd)) + 1      # a two-pistol clip holds its last pose from here
    idle0 = pose_at(var.idle, 0)
    keep = idle0                        # the hold, not Loop's recoil top: the reload starts from it (TRIM)
    for tr in anim.tracks:
        for seq in (tr.translations, tr.rotations, tr.scales):
            del seq[KEEP_FRAMES + 1:]
            while len(seq) < n:
                seq.append(list(seq[-1]))
    for f in range(KEEP_FRAMES + 1):
        set_pose(anim, f, idle0)
    anim.num_frames = n
    anim.duration = (n - 1) * fd
    t_end = (n_motion - 1) * fd
    t_keep = KEEP_FRAMES * fd
    t_go = t_keep + var.shift           # the reload's motion starts here (later by a Variant's shift)
    f_go = int(round(t_go / fd))
    # the body from Loop's recoil top into his idle: over the whole reload, or (a shifted reload) settled by SECOND_SETTLE
    n_body = n_motion if not var.shift else min(n_motion, KEEP_FRAMES + int(round(SECOND_SETTLE / fd)))
    # body: Loop's recoil top into his idle over the reload; the right arm, every frame, the free arm as the game shows
    # it (var.rest): the reload's right-arm motion starts and ends there, so the switch is seamless
    for f in range(KEEP_FRAMES + 1, n):
        set_pose(anim, f, mix_pose(keep, idle0, smooth(min(1.0, (f - KEEP_FRAMES) / (n_body - 1 - KEEP_FRAMES)))))
    iwp = ix['Weapon']
    relax = [ix[b] for b in RIGHT_HALF + RIGHT_IDLE if b not in RELAX_SKIP] if var.relaxed else []
    calm_go = None
    for f in range(n):
        t = f * fd
        w_relax = smooth((t - beats['release']) / (beats['pouch_near'] - beats['release'])) * \
            (1 - smooth((t - beats['stowed']) / (beats['regrip'] - beats['stowed']))) if relax else 0.0
        if w_relax > 0 or (relax and f == f_go):      # the one-gun reload's rest, read off before the hold's goes in
            before = [(list(anim.tracks[b].rotations[f]), list(anim.tracks[b].scales[f])) for b in relax]
            var.relaxed.rest(anim, f)
            calm = [(list(anim.tracks[b].rotations[f]), list(anim.tracks[b].scales[f])) for b in relax]
            for b, (q, sc) in zip(relax, before):
                anim.tracks[b].rotations[f], anim.tracks[b].scales[f] = q, sc
            if f == f_go:
                calm_go = calm
        var.rest(anim, f)
        if w_relax > 0:
            for b, (q, sc) in zip(relax, calm):
                tr = anim.tracks[b]
                tr.rotations[f] = [float(x) for x in ADS.slerp(tr.rotations[f], q, w_relax)]
                tr.scales[f] = [float(x) for x in ADS.lerp(tr.scales[f], sc, w_relax)]
        if var.dual:     # the other gun in its hand as in its idle hold
            anim.tracks[iwp].translations[f] = [float(x) for x in var.wl[:3, 3]]
    w_keep = rig.world(anim, f_go)       # the body as the reload starts (= KEEP_FRAMES but for a shifted reload)
    # the gun hand's scale (RIGHT_GUN_SCALE): a scaled pistol's muzzle, barrel and rod scale with it
    gun_scale = float(np.linalg.norm(w_keep[ix['Shield']][:3, 0]))
    c, radius = np.asarray(c, dtype=float) * gun_scale, radius * gun_scale
    body = right, fwd, up = body_frame(w_keep, ix)
    pelvis = w_keep[ix['NPC Pelvis [Pelv]']][:3, 3]
    # the reload itself (load pose, pouch, beats) is set in the body as it starts with the free arm the beats see: a
    # relaxed free arm's (RELAX_SKIP), as in the one-gun reload. body_frame() levels the shoulders' line, and from the
    # other gun's hold the free shoulder turned it, the pouch landing 15 units further forward
    w_load = w_keep
    if calm_go is not None:
        hold = [(anim.tracks[b].rotations[f_go], anim.tracks[b].scales[f_go]) for b in relax]
        for b, (q, sc) in zip(relax, calm_go):
            anim.tracks[b].rotations[f_go], anim.tracks[b].scales[f_go] = q, sc
        w_load = rig.world(anim, f_go)
        for b, (q, sc) in zip(relax, hold):
            anim.tracks[b].rotations[f_go], anim.tracks[b].scales[f_go] = q, sc
    body_load = body_frame(w_load, ix)
    order = ['pouch_near', 'pouch', 'over_muzzle', 'drop', 'grab', 'drawn', 'over_bore', 'rammed', 'stroke_up',
             'stroke_down', 'withdrawn', 'over_stow', 'stowed']
    carry = []
    grips = {}            # a carry beat's attach node in the hand (a melee weapon turns on its handle: STOW)
    if var.shield:    # the shield behind the back, let go, settled onto ShieldBack, and back (Ctx.shield)
        ctx.carry_in_hand = var.wl
        right_, fwd_, up_ = body
        letgo, approach, _ = shield_letgo(ctx, anim, var, body)
        carry, prev = [], None
        for beat, local in (('lower', approach), ('tucked', letgo), ('regrip', letgo), ('raise_', approach)):
            w_b = rig.world(anim, int(round(beats[beat] / fd)))
            item = var.stow(w_b) @ local
            H, pole, g, _, miss, _, _ = stow_hold(ctx, w_b, item, body, False, prev=prev, rolls=(0,))
            carry.append((beat, item[:3, 3], H))
            grips[beat] = (g, 0.0, False)
            prev = (H, pole)
            if beat == 'tucked':        # the hand lets go, straight off the grip
                let_go = item[:3, 3] + right_ * RELEASE_OFF[0] + fwd_ * RELEASE_OFF[1] + up_ * RELEASE_OFF[2]
                carry.append(('release', let_go, H))
                grips['release'] = (g, 0.0, False)
    elif var.stow:    # the melee weapon into its sheath and back (STOW)
        ctx.carry_in_hand = var.wl
        right_, fwd_, up_ = body

        def sheathed(beat, out):
            w_b = rig.world(anim, int(round(beats[beat] / fd)))
            s = var.stow(w_b)
            sign = 1.0 if s[:3, 1] @ up_ > 0 else -1.0     # out of the sheath = up along the blade
            return w_b, s @ ADS.trs([0.0, sign * out, 0.0], [0, 0, 0, 1.0], 1.0), sign
        # the shallowest hold the hand reaches with the wrist inside STOW_WRIST, the idle's grip before a reverse one
        # (blade-down weapons: the reverse grip keeps the wrist nearly straight right at the sheath; the axe the idle's)
        found = None
        for depth in np.arange(0.0, STOW_DEPTH_MAX + 1e-6, STOW_DEPTH_STEP):
            for reverse in (False, True):
                w_in, item_in, sign = sheathed('tucked', depth)
                hold = stow_hold(ctx, w_in, item_in, body, reverse)
                if hold[4] <= 0.05 and abs(hold[5][0]) <= STOW_WRIST[0] and abs(hold[5][1]) <= STOW_WRIST[1]:
                    found = (reverse, float(depth), sign)
                    break
            if found:
                break
        if not found:
            sys.exit('%s %s: the hand holds the weapon nowhere within %.0f of its sheath' % (var.name, label,
                                                                                         STOW_DEPTH_MAX))
        reverse, depth, var.stow_sign = found
        var.stow_depth, var.stow_reverse = depth, reverse
        carry, prev = [], None
        for beat, out in (('lower', depth + STOW_APPROACH), ('tucked', depth), ('regrip', depth),
                          ('raise_', depth + STOW_APPROACH)):
            w_b, item, _ = sheathed(beat, out)
            H, pole, g, _, miss, _, roll = stow_hold(ctx, w_b, item, body, reverse, prev=prev)
            carry.append((beat, item[:3, 3], H))
            grips[beat] = (g, roll, reverse)
            prev = (H, pole)
            if beat == 'tucked':        # the hand lets go, straight off the grip
                let_go = item[:3, 3] + right_ * RELEASE_OFF[0] + fwd_ * RELEASE_OFF[1] + up_ * RELEASE_OFF[2]
                carry.append(('release', let_go, H))
                grips['release'] = (g, roll, reverse)
    elif var.dual:      # the other gun to the belt and back: fixed beats, the same for every load pose
        ctx.carry_in_hand = var.wl
        belt, belt_h, _, _, belt_params = belt_pose(ctx, w_keep, body, var)
        right_, fwd_, up_ = body
        let_go = belt[:3, 3] + right_ * RELEASE_OFF[0] + fwd_ * RELEASE_OFF[1] + up_ * RELEASE_OFF[2]
        level = belt[:3, 3] + right_ * LEVEL_OFF[0] + fwd_ * LEVEL_OFF[1] + up_ * LEVEL_OFF[2]
        sb, sg = var.gun_axes
        xc, yc = sg * -up_, sb * fwd_          # the grip down, the barrel forward
        wl_rot = var.wl[:3, :3] / np.linalg.norm(var.wl[:3, 0])
        level_h = np.column_stack([xc, yc, np.cross(xc, yc)]) @ wl_rot.T
        carry = [('lower', level, level_h), ('tucked', belt[:3, 3], belt_h), ('release', let_go, belt_h),
                 ('regrip', belt[:3, 3], belt_h), ('raise_', level, level_h)]
    beat_w = {name: rig.world(anim, int(round(beats[name] / fd))) for name in order + [b for b, _, _ in carry]}
    carry_solved = {}
    prev = None
    for name, pos, ch in carry[:3]:
        H, pole, _, miss = solve_carry(ctx, beat_w[name], ch, pos, body, prev=prev)
        if miss > 0.05:
            sys.exit('%s %s: the hand misses the %s beat %s by %.2f' % (var.name, label, 'sheath' if var.stow else 'belt',
                                                                     name, miss))
        carry_solved[name] = (H, pole)
        prev = (H, pole)
    # the reload's beats chain on from the hand letting go of the other item, except a relaxed free arm's (RELAX_SKIP),
    # which start fresh as the one-gun reload's do: chained on, the pouch kept the carrying elbow 20 in front
    chain = None if var.relaxed else carry_solved.get('release')
    cands = []
    for cost, load, params in load_pose(ctx, w_load, c, axis, radius)[:LOAD_CANDIDATES]:
        ks, _ = targets(load, c, axis, radius, body_load, pelvis)
        strain, prev = 0.0, chain
        for name in order:
            kind, pos, dirn, _ = ks[name]
            H, pole, bc, miss = solve_beat(ctx, beat_w[name], 'R', kind, pos, dirn, body_load, steps=12, roll_step=30,
                                           prev=prev)
            if miss > 0.05:
                break
            strain += bc
            prev = (H, pole)
        else:
            cands.append((cost + 0.1 * strain, load, dict(params, right_strain=strain)))
    if not cands:
        sys.exit('%s: the right hand reaches every beat in none of the %d cheapest load poses' % (label, LOAD_CANDIDATES))
    # the frames between the beats can still break a wrist or pass the face (a 130 deg roll, right-hand pistool03):
    # then the next cheapest load pose
    base = copy.deepcopy(anim)
    for attempt, (_, load, params) in enumerate(sorted(cands, key=lambda x: x[0])):
        anim = copy.deepcopy(base)
        ks, geo = targets(load, c, axis, radius, body_load, pelvis)
        solved, prev = {}, None
        for name, pos, _ in carry[:3]:
            H, pole = carry_solved[name]
            fore = arm_chain(rig, beat_w[name], 'R', pos - H @ grip_offset(ctx, 'carry')[0], pole)[3]
            solved[name] = ('carry', pos, H, pole, 0.0, fore.T @ H) + grips.get(name, (unscaled(var.wl), 0.0, False))
        prev = chain
        for name in order:      # in order: each beat's hand stays near the last one's (CONTINUITY)
            kind, pos, dirn, fw = ks[name]
            H, pole, cost, miss = solve_beat(ctx, beat_w[name], 'R', kind, pos, dirn, body_load, prev=prev)
            if miss > 0.05:
                sys.exit('%s: the right hand misses %s by %.2f' % (label, name, miss))
            fore = arm_chain(rig, beat_w[name], 'R', pos - H @ grip_offset(ctx, kind)[0], pole)[3]
            solved[name] = (kind, pos, H, pole, fw, fore.T @ H)    # last: the hand's rotation against its forearm
            prev = (H, pole)
        for name, pos, ch in carry[3:]:
            H, pole, _, miss = solve_carry(ctx, beat_w[name], ch, pos, body, prev=prev)
            if miss > 0.05:
                sys.exit('%s %s: the hand misses the belt beat %s by %.2f' % (var.name, label, name, miss))
            fore = arm_chain(rig, beat_w[name], 'R', pos - H @ grip_offset(ctx, 'carry')[0], pole)[3]
            solved[name] = ('carry', pos, H, pole, 0.0, fore.T @ H) + grips.get(name, (unscaled(var.wl), 0.0, False))
            prev = (H, pole)
        sequence =[b for b, _, _ in carry[:3]] + order + [b for b, _, _ in carry[3:]]
        w_idle = rig.world(var.idle, 0)
        shield_keep, shield_idle = w_keep[ix['Shield']], w_idle[ix['Shield']]
        ish, irh, ihead, ineck = (ix[n] for n in ('Shield', 'NPC R Hand [RHnd]', 'NPC Head [Head]', 'NPC Neck [Neck]'))
        misses, wrists = {'L': 0.0, 'R': 0.0}, {'L': (0.0, 0.0), 'R': (0.0, 0.0)}
        right_arm, clear = [ix[n] for n in SIDES['R'][:3]], math.inf
        carry_pole = None
        flip_sign, flip_clear = {}, math.inf        # a melee weapon's grip flips: which way, per segment
        shield_clear = math.inf                     # a shield off the body while the hand carries it
        for f in range(KEEP_FRAMES + 1, n_motion):
            t = f * fd
            # elbows from the pose's own into the solved directions and back: no pop at Loop's last frame or into his idle
            k = smooth((t - t_go) / IK_EASE) * (1 - smooth((t - (t_end - IK_EASE)) / IK_EASE))
            # --- the pistol (left hand): into the load pose, held there (slid up the pistol), back to Loop's idle
            u_in = smooth((t - t_go) / (var.load_at - t_go))
            u_out = smooth((t - var.unload_at) / (t_end - var.unload_at))
            sh = blend_mat(blend_mat(shield_keep, load, u_in), shield_idle, u_out)
            # held further up the pistol: the pistol (on the Shield node, a child of the hand) slides down through the
            # hand, so the Shield node's own track moves too (Loop's clips animate it; the engine follows)
            sl = ADS.trs([0.0, -params['slide'] * u_in * (1 - u_out) / gun_scale, 0.0], [0, 0, 0, 1.0], 1.0)
            shield_local = local_mat(anim, ish, f) @ sl
            anim.tracks[ish].translations[f] = [float(x) for x in shield_local[:3, 3]]
            shield_world = shield_local.copy()          # the offset as the scaled hand puts it in the world
            shield_world[:3, 3] *= gun_scale
            lh = sh @ np.linalg.inv(shield_world)
            miss, wl = solve_arm(rig, anim, f, 'L', lh, params['left_pole'], min(k, u_in * (1 - u_out)))
            misses['L'] = max(misses['L'], miss)
            wrists['L'] = tuple(max(a, abs(b)) for a, b in zip(wrists['L'], wl))
            # --- the right hand: its own (body-blended) pose at the start and the end, the solved beats in between
            w = rig.world(anim, f)
            keys = [(t_go, None)] + [(beats[k_], solved[k_]) for k_ in sequence] + [(t_end, None)]
            i, s = interp_keys(keys, t)
            A, B = keys[i][1], keys[i + 1][1]
            own = w[irh]
            iu_r, ifa_r = right_arm[0], right_arm[1]
            own_local = (w[ifa_r][:3, :3] / np.linalg.norm(w[ifa_r][:3, 0])).T @ (own[:3, :3] / np.linalg.norm(own[:3, 0]))
            pa = A[3] if A else None
            pb = B[3] if B else None
            pole = unit((pa if pa is not None else pb) * (1 - s) + (pb if pb is not None else pa) * s)
            # next to a rest key the elbow eases over the whole segment, with the hand (else it flings out sideways)
            kr = k * (s if A is None else 1.0) * ((1.0 - s) if B is None else 1.0)
            S_r, E_r, H_r = w[iu_r][:3, 3], w[ifa_r][:3, 3], own[:3, 3]
            own_elbow = E_r - S_r - unit(H_r - S_r) * ((E_r - S_r) @ unit(H_r - S_r))
            pole = unit(unit(own_elbow) * (1 - kr) + pole * kr)
            # the hand's rotation against its forearm is what blends between beats (a world-space blend let the forearm
            # roll its own way: 150 deg wrist rolls between two beats of 50), solved twice with the arm
            # a shield, strapped to the forearm, rides it from and to the idle's hold: the hand blends against its forearm
            # like the reload's beats (its world pose blended, the wrist bent 111 deg swinging the shield round the hip)
            strapped = var.shield and (A is None or B is None)
            if var.dual and all(x is None or x[0] == 'carry' for x in (A, B)) and not strapped:
                # carrying the other gun (to the belt and back): the GUN's world pose blends, the hand under it, so the
                # barrel turns the short way in the world (blended against the forearm, it swung back through the body)
                wl = unscaled(var.wl)
                ha = hand_at(ctx, 'carry', A[1], A[2]) if A else unscaled(own)
                hb = hand_at(ctx, 'carry', B[1], B[2]) if B else unscaled(own)
                # a melee weapon turns on its handle between beats (STOW): the weapon's pose and its grip blend
                ga, gb = (A[6] if A else wl), (B[6] if B else wl)
                grip = blend_mat(ga, gb, s)
                if var.stow and (A is None or B is None):
                    # from / to the idle's hold the grip may flip (reverse, half a turn): the hand blends and the weapon
                    # turns in its fingers (blending the weapon's pose dragged the wrist through 159 deg), the way
                    # round that keeps the blade furthest from the body (flip_grip)
                    beat = B if A is None else A
                    hand = blend_mat(ha, hb, s)
                    if i not in flip_sign:
                        t0, t1 = keys[i][0], keys[i + 1][0]
                        clear_by = {}
                        for sg in FLIP_PATHS:
                            c_min = math.inf
                            for fs in range(int(round(t0 / fd)), int(round(t1 / fd)) + 1, 2):
                                ss = smooth((fs * fd - t0) / (t1 - t0))
                                w_s = rig.world(anim, fs)
                                own_s = unscaled(w_s[irh])
                                h_s = blend_mat(own_s if A is None else ha, own_s if B is None else hb, ss)
                                g_s = flip_grip(var.wl, beat[7], beat[8], ss if A is None else 1.0 - ss, sg)
                                c_min = min(c_min, blade_clearance(ctx, w_s, h_s @ g_s))
                            clear_by[sg] = c_min
                        flip_sign[i] = max(clear_by, key=clear_by.get)
                        flip_clear = min(flip_clear, clear_by[flip_sign[i]])
                    grip = flip_grip(var.wl, beat[7], beat[8], s if A is None else 1.0 - s, flip_sign[i])
                else:
                    hand = blend_mat(ha @ ga, hb @ gb, s) @ np.linalg.inv(grip)
                # the elbow per frame for the least wrist strain (the beats' elbows, blended, rolled the wrist 168 deg),
                # steady from frame to frame and pulled onto the blended one near the idle holds (kr -> 0)
                best = None
                for cand in pole_dirs(S_r, hand[:3, 3], 24) + [pole]:     # the blended one too: at a hold it is exact
                    E_c, _, _, fore_c, miss_c = arm_chain(rig, w, 'R', hand[:3, 3], cand)
                    el = unit(E_c - S_r - unit(hand[:3, 3] - S_r) * ((E_c - S_r) @ unit(hand[:3, 3] - S_r)))
                    cost_c = (wrist_cost(*wrist(rig, 'R', fore_c, hand[:3, :3])) + elbow_cost('R', S_r, E_c, body) +
                              50.0 * miss_c + (CARRY_FOLLOW + CARRY_HOLD * (1.0 - kr)) * angle_between_dirs(pole, el) +
                              (CARRY_STEADY * angle_between_dirs(carry_pole, el) if carry_pole is not None else 0.0))
                    if best is None or cost_c < best[0]:
                        best = (cost_c, el)
                pole = carry_pole = best[1]
            else:
                carry_pole, grip = None, None
                local = blend_mat(rot4(A[5] if A else own_local), rot4(B[5] if B else own_local), s)[:3, :3]
                same = A and B and A[0] == B[0]
                if same:   # one grip moving: the grip point in a straight line (the rod's line, the pinch's path)
                    gpos = A[1] + (B[1] - A[1]) * s
                    off = grip_offset(ctx, A[0])[0]
                else:
                    ha = hand_at(ctx, A[0], A[1], A[2]) if A else own
                    hb = hand_at(ctx, B[0], B[1], B[2]) if B else own
                    hpos = blend_mat(ha, hb, s)[:3, 3]
                own_rot = own[:3, :3] / np.linalg.norm(own[:3, 0])
                H = blend_mat(rot4(A[2] if A else own_rot), rot4(B[2] if B else own_rot), s)[:3, :3]
                for _ in range(2):
                    fore = arm_chain(rig, w, 'R', gpos - H @ off if same else hpos, pole)[3]
                    H = fore @ local
                hand = rot4(H)
                hand[:3, 3] = gpos - H @ off if same else hpos
            miss, wr = solve_arm(rig, anim, f, 'R', hand, pole, 1.0, twist_k=kr)
            if var.stow and grip is not None:     # in the hand, in its blended grip (pinned below while sheathed)
                anim.tracks[iwp].translations[f] = [float(x) for x in grip[:3, 3]]
                anim.tracks[iwp].rotations[f] = [float(x) for x in ADS.mat_quat(grip[:3, :3])]
            misses['R'] = max(misses['R'], miss)
            wrists['R'] = tuple(max(a, abs(b)) for a, b in zip(wrists['R'], wr))
            w = rig.world(anim, f)
            if var.dual and beats['tucked'] <= t <= beats['regrip']:     # the other item stays in the belt / sheath
                # a melee weapon slides in and out of its sheath while the hand is off it, a shield onto its back
                target = stowed_at(var, w, t, beats) if var.stow else belt
                R3P.place(anim, iwp, f, w[irh], target)
                w = rig.world(anim, f)
            if var.shield and not (beats['release'] <= t <= beats['regrip'] - (beats['release'] - beats['tucked'])):
                shield_clear = min(shield_clear, shield_clearance(ctx, w, unscaled(w[iwp])))
            clear = min(clear, head_clearance(face(rig, w), *(w[i][:3, 3] for i in right_arm),
                                              (w[irh] @ ctx.fist_in_hand)[:3, 3]))
            # --- right fingers: relaxed (the body pose's) -> pinch / fist
            fa = (A[0], A[4]) if A else ('rest', 0.0)
            fb = (B[0], B[4]) if B else ('rest', 0.0)
            wp = (fa[1] if fa[0] == 'pinch' else 0.0) * (1 - s) + (fb[1] if fb[0] == 'pinch' else 0.0) * s
            wf = (fa[1] if fa[0] == 'fist' else 0.0) * (1 - s) + (fb[1] if fb[0] == 'fist' else 0.0) * s
            for name in R_FINGERS:
                bi = ix[name]
                q = anim.tracks[bi].rotations[f]
                q = ADS.slerp(q, ctx.pinch[bi], wp)
                q = ADS.slerp(q, ctx.fist[bi], wf)
                anim.tracks[bi].rotations[f] = [float(x) for x in q]
            # --- head and neck toward the muzzle
            look = LOOK * u_in * (1 - u_out)
            if look > 0:
                w = rig.world(anim, f)
                head = w[ihead]
                want = unit(geo['muzzle'] + geo['bore'] * 6.0 - head[:3, 3])
                have = unit(head[:3, :3] @ np.array([0, 1.0, 0]))
                turn = R3P.rot_between(have, want)
                ang = math.degrees(math.acos(max(-1.0, min(1.0, (np.trace(turn) - 1) / 2))))
                if ang > 0.01:
                    ax = unit(np.array([turn[2, 1] - turn[1, 2], turn[0, 2] - turn[2, 0], turn[1, 0] - turn[0, 1]]))
                    for bone, share in ((ineck, NECK_SHARE), (ihead, 1.0 - NECK_SHARE)):
                        w = rig.world(anim, f)
                        r = rot_axis(ax, ang * look * share) @ (w[bone][:3, :3] / np.linalg.norm(w[bone][:3, 0]))
                        R3P.set_rotation(anim, bone, f, (w[rig.parents[bone]][:3, :3] /
                                                         np.linalg.norm(w[rig.parents[bone]][:3, 0])).T @ r)
        if (max(wrists['L'][0], wrists['R'][0]) <= WRIST_BEND_MAX and
                max(wrists['L'][1], wrists['R'][1]) <= WRIST_ROLL_MAX and clear >= HEAD_CLEAR_MIN):
            break
    keep = {int(round(beats[b] / fd)) for b in order + (['tucked', 'release', 'regrip'] if var.dual else [])}

    def repin(f):         # the other item back in the belt / sheath under the hand deflick() moved
        t = f * fd
        if var.dual and beats['tucked'] <= t <= beats['regrip']:
            w = rig.world(anim, f)
            R3P.place(anim, iwp, f, w[irh], stowed_at(var, w, t, beats) if var.stow else belt)
    flips = deflick(ctx, anim, KEEP_FRAMES + 1, n_motion - 1, keep, repin)
    for f in range(n_motion, n):     # the last pose held (two pistols: while the script hands the body back)
        set_pose(anim, f, pose_at(anim, n_motion - 1))
    params = dict(params, attempt=attempt)
    added, prop_frames = props(ctx, anim, label, geo, beats)
    if var.stow:      # the melee arm back to the game's idle (ZP_PistolReloadArmScript, ARM_BACK)
        added.append((beats['regrip'] + ARM_BACK_AFTER, ARM_BACK))
        anim.annotations.append(anim_skyrim.Annotation(time=round(added[-1][0], 4), text=ARM_BACK))
    info = dict(params, Lr=geo['Lr'], head_clear=clear, prop_frames=prop_frames, gun_scale=gun_scale, flip_clear=flip_clear,
                flips=flips, shield_clear=shield_clear)
    if var.dual and not var.stow:
        info.update(belt=belt, belt_params=belt_params)
    if var.shield:
        info.update(letgo=var.letgo[2])
    return anim, info, added, misses, wrists, load


def props(ctx, anim, label, geo, beats=BEATS):
    """Ball and rod on AnimObjectR, with their annotations. Ball: between the thumb and index tips, one radius out from
    the palm, from its draw at the pouch; over the muzzle it slides in over BALL_DROP and is dropped. Rod: from the
    grab to the stow it rides the fist, its top ROD_ABOVE_FIST above the grip centre along the grip's +Y. Returns (annotations added, the frames the
    props are placed on)."""
    rig, ix = ctx.rig, ctx.ix
    fd, n = anim.frame_duration, anim.num_frames
    iao, irh = ix['AnimObjectR'], ix['NPC R Hand [RHnd]']
    rf = lambda a: ix['NPC R Finger%s [RF%s]' % (a, a)]  # noqa: E731
    b = beats
    f_of = lambda t: int(round(t / fd))  # noqa: E731
    frames = []
    for f in range(f_of(b['pouch'] - LOAD_LEAD), f_of(b['drop']) + 1):
        frames.append(f)
        w = rig.world(anim, f)
        tip = lambda j0, j1: w[rf(j1)][:3, 3] + FINGER_TIP * (w[rf(j1)][:3, 3] - w[rf(j0)][:3, 3])  # noqa: E731
        pinch = (tip('01', '02') + tip('11', '12')) / 2
        pinch = pinch + unit(pinch - w[irh][:3, 3]) * BALL_RADIUS
        into = geo['muzzle'] - geo['bore'] * 0.6
        s = smooth((f * fd - (b['drop'] - BALL_DROP)) / BALL_DROP)
        m = w[irh].copy()
        m[:3, :3] /= np.linalg.norm(m[:3, 0])
        m[:3, 3] = pinch + (into - pinch) * s
        R3P.place(anim, iao, f, w[irh], m)
    rod_load = max(b['grab'] - LOAD_LEAD, b['drop'] + 1.5 * fd)   # AnimObjectUnequip drops every prop: after the ball
    rod_rot = np.column_stack([unit(np.cross(geo['bore'], geo['rod_side'])), geo['bore'], geo['rod_side']])
    for f in range(f_of(rod_load), f_of(b['stowed']) + 1):
        frames.append(f)
        w = rig.world(anim, f)
        grip = w[irh] @ ctx.fist_in_hand
        m = np.eye(4)
        m[:3, :3] = rod_rot        # up the bore, through the grip centre, whichever way up the fist holds it
        m[:3, 3] = grip[:3, 3] + geo['bore'] * ROD_ABOVE_FIST
        R3P.place(anim, iao, f, w[irh], m)
    added = [(0.0, UNEQUIP),
             (b['pouch'] - LOAD_LEAD, 'AnimObjLoad.' + BALL_EDID), (b['pouch'], 'AnimObjDraw.' + BALL_EDID),
             (b['drop'], UNEQUIP),
             (rod_load, 'AnimObjLoad.' + ROD_EDID % label), (b['grab'], 'AnimObjDraw.' + ROD_EDID % label),
             (b['stowed'], UNEQUIP), (b['withdrawn'], LOADED)]
    added += [(b['drop'] - BALL_DROP + after, 'SoundPlay.' + edid) for edid, after in SOUNDS]
    times = sorted(x for x, _ in added)
    if any(y - x < fd for x, y in zip(times, times[1:])):
        sys.exit('%s: prop beats closer than a frame: %s' % (label, times))
    for x, s in added:
        anim.annotations.append(anim_skyrim.Annotation(time=round(x, 4), text=s))
    return added, frames


# ---- checks and output -----------------------------------------------------------------------------------------

def deflick(ctx, anim, lo, hi, keep, after):
    """Blend each arm across its flips (DEFLICK_DEG) between frames lo and hi, never moving a frame in `keep`; then
    after(f) for every frame moved. Returns [(side, frame, degrees)] of the flips found (one with a kept frame on both
    sides stays)."""
    rig = ctx.rig
    ws = {f: rig.world(anim, f) for f in range(lo, hi + 1)}
    found, moved = [], set()
    for side in 'LR':
        bones = [i for n, i in ctx.ix.items() if (m := ARM_BONE.match(n)) and m.group(1) == side]
        windows = []
        for f in range(lo + 1, hi + 1):
            turn = max(angle_between(unscaled(ws[f - 1][b])[:3, :3], unscaled(ws[f][b])[:3, :3]) for b in bones)
            if turn <= DEFLICK_DEG:
                continue
            found.append((side, f, turn))
            a = max([lo, f - 1 - DEFLICK_SPAN] + [k for k in keep if k <= f - 1])
            b = min([hi, f + DEFLICK_SPAN] + [k for k in keep if k >= f])
            if b - a < 2:
                continue
            # windows meeting on a kept frame stay apart (merged, the regrip moved 134 deg off the gun's grip)
            if windows and (a < windows[-1][1] or (a == windows[-1][1] and a not in keep)):
                windows[-1] = (windows[-1][0], max(b, windows[-1][1]))
            else:
                windows.append((a, b))
        for a, b in windows:
            for g in range(a + 1, b):
                u = smooth((g - a) / (b - a))
                for i in bones:
                    tr = anim.tracks[i]
                    tr.rotations[g] = [float(x) for x in ADS.slerp(tr.rotations[a], tr.rotations[b], u)]
                    tr.translations[g] = [float(x) for x in ADS.lerp(tr.translations[a], tr.translations[b], u)]
                moved.add(g)
    for g in sorted(moved):
        after(g)
    return found


def trim(anim, k=KEEP_FRAMES):
    """`anim` without its first k frames, the hold before the reload (TRIM); its annotations k frames earlier (the
    first ones, Loop's tag, at 0)."""
    out = copy.deepcopy(anim)
    for tr in out.tracks:
        for seq in (tr.translations, tr.rotations, tr.scales):
            del seq[:k]
    out.num_frames -= k
    out.duration = (out.num_frames - 1) * out.frame_duration
    for a in out.annotations:
        a.time = max(0.0, a.time - k * out.frame_duration)
    return out


def densify(ctx, anim, k=DENSE):
    """`anim` with each frame interval split into k keys (see DENSE). Every bone's local track is interpolated as the
    engine would (lerp / slerp), except an attach node (DENSE_NODES) that moves less in the world than on its parent over
    the interval, a weapon pinned while the hand moves: its world transform is interpolated and its local solved from
    it. The source keys are kept as they are, every k-th key; quaternions stay in one hemisphere along each track."""
    rig = ctx.rig
    n, fd = anim.num_frames, anim.frame_duration
    nodes = [ctx.ix[x] for x in DENSE_NODES]
    keys = [pose_at(anim, f) for f in range(n)]
    worlds = [rig.world(anim, f) for f in range(n)]
    out = copy.deepcopy(anim)
    for tr in out.tracks:
        tr.translations, tr.rotations, tr.scales = [], [], []
    pinned = []                  # (dense frame, node, world target)
    m = 0
    for f in range(n):
        for j in range(k if f < n - 1 else 1):
            u = j / k
            set_pose_append(out, keys[f] if j == 0 else mix_pose(keys[f], keys[f + 1], u))
            for b in nodes if j else ():
                dw = np.linalg.norm(worlds[f + 1][b][:3, 3] - worlds[f][b][:3, 3])
                dl = np.linalg.norm(np.subtract(keys[f + 1][b][0], keys[f][b][0]))
                if dw < dl - 0.01:
                    s0, s1 = (float(np.linalg.norm(w[b][:3, 0])) for w in (worlds[f], worlds[f + 1]))
                    target = blend_mat(worlds[f][b], worlds[f + 1][b], u)
                    target[:3, :3] *= s0 + (s1 - s0) * u
                    pinned.append((m, b, target))
            m += 1
    out.num_frames, out.frame_duration = m, fd / k
    out.duration = (m - 1) * out.frame_duration
    for i, b, target in pinned:
        local = np.linalg.inv(rig.world(out, i)[rig.parents[b]]) @ target
        s = float(np.linalg.norm(local[:3, 0]))
        tr = out.tracks[b]
        tr.translations[i] = [float(x) for x in local[:3, 3]]
        tr.rotations[i] = [float(x) for x in ADS.mat_quat(local[:3, :3] / s)]
        tr.scales[i] = [s, s, s]
    for tr in out.tracks:        # one hemisphere along the track: the spline interpolates the quaternions' components
        for i in range(1, m):
            if sum(x * y for x, y in zip(tr.rotations[i], tr.rotations[i - 1])) < 0:
                tr.rotations[i] = [-x for x in tr.rotations[i]]
    for f in range(n):
        for b, (t, q, _) in enumerate(keys[f]):
            got = out.tracks[b]
            dq = abs(abs(sum(x * y for x, y in zip(q, got.rotations[f * k]))) - 1.0)
            if np.linalg.norm(np.subtract(t, got.translations[f * k])) > 1e-5 or dq > 1e-6:
                sys.exit('densify moved key %d of track %d' % (f, b))
    return out


def set_pose_append(anim, pose):
    for tr, (t, q, s) in zip(anim.tracks, pose):
        tr.translations.append([float(x) for x in t])
        tr.rotations.append([float(x) for x in q])
        tr.scales.append([float(x) for x in s])


def write_clip(path, anim, floats, reference=False):
    """Write `anim` with the float (node visibility) tracks `floats` (hkx_floats: PyNifly writes none, and a slot no
    playing clip carries reads 0, which hides the gun nodes). `reference`: also decode a plain write and require the
    same transforms."""
    HF.write(path, anim, floats)
    plain = None
    if reference:
        plain = os.path.join(os.environ.get('TEMP', '.'), '_pistol_reload_plain.hkx')
        anim_skyrim.write_skyrim_animation(plain, anim, ptr_size=8)
    HF.check(path, floats, plain)
    if plain:
        os.remove(plain)


def check(ctx, path, added, var):
    """Decode the written clip: the hold (Loop's idle with the free right arm's rest pose) until the reload starts and
    again at the end, the annotations as written (`var`'s world: the right hand's is checked mirrored, before
    unmirror(), and again by check_right())."""
    got = anim_skyrim.load_skyrim_animation(path)
    src = var.source()
    rig = ctx.rig
    ADS.check_blocks(path)
    end = copy.deepcopy(var.idle)
    var.rest(end, 0)
    wi = rig.world(end, 0)
    for f in range(KEEP_FRAMES + 1):
        for b in (ctx.ix['NPC L Hand [LHnd]'], ctx.ix['Shield'], ctx.ix['NPC Head [Head]']):
            d = np.linalg.norm(rig.world(got, f)[b][:3, 3] - wi[b][:3, 3])
            if d > 0.2:
                sys.exit('%s: frame %d is %.2f off the hold on bone %d (the reload starts from it)' % (path, f, d, b))
    wl = rig.world(got, got.num_frames - 1)
    worst = max(np.linalg.norm(wl[b][:3, 3] - wi[b][:3, 3]) for b in range(len(got.tracks)))
    if worst > 0.5:
        sys.exit('%s: last frame %.2f units off Loop\'s idle' % (path, worst))
    want = sorted([(round(a.time, 4), a.text) for a in src.annotations] + [(round(x, 4), s) for x, s in added])
    if sorted((round(a.time, 4), a.text) for a in got.annotations) != want:
        sys.exit('%s: annotations differ from those written' % path)
    return got, worst


def swap_side(name):
    """A bone's left <-> right partner (mirror_hkx.partners' rule; AnimObjectR/L, which it keeps, swapped too)."""
    special = {'Shield': 'Weapon', 'Weapon': 'Shield', 'AnimObjectR': 'AnimObjectL', 'AnimObjectL': 'AnimObjectR'}
    if name in special:
        return special[name]
    return (name.replace(' L ', ' \0 ').replace(' R ', ' L ').replace(' \0 ', ' R ')
            .replace('[L', '[\0').replace('[R', '[L').replace('[\0', '[R'))


REFLECT = np.diag([-1.0, 1.0, 1.0, 1.0])     # mirror_hkx's reflection across the model's YZ plane
MESH_FLIP = np.array([1.0, 1.0, -1.0])       # the pistol mesh in the mirrored world's Shield frame: (x, y, -z)


def unmirror(ctx, label, anim_m, path_m, info, added, out, floats):
    """The right hand's clip from its mirrored build `anim_m` (written to path_m): mirrored back, the gun's 180 deg turn
    on Weapon. mirror_hkx keeps AnimObjectR as AnimObjectR (and L as L): each is placed at the reflection of itself,
    so it hangs from the other side's hand, and once the arms move it drifts from both (32 units at the end). So both
    tracks are rebuilt the way build_clip() holds the body: on his right idle (frame 0). Over the prop frames the props move onto the ramming hand's AnimObjectL, reflected (position S p,
    rotation S R S: the rod's +Y stays on the reflected bore); the annotations name the AnimObjectL records. Writes
    `out` with `floats`; returns the annotations added."""
    rig, ix = ctx.rig, ctx.ix
    anim = ctx.mirror.mirror(path_m, out, turned='Weapon')
    idle = anim_skyrim.load_skyrim_animation(os.path.join(ctx.right_dir, IDLE_RIGHT))
    iao_r, iao_l = ix['AnimObjectR'], ix['AnimObjectL']
    n = anim.num_frames
    for b in (iao_r, iao_l):
        tr, z = anim.tracks[b], idle.tracks[b]
        for f in range(n):
            tr.translations[f] = [float(x) for x in z.translations[0]]
            tr.rotations[f] = [float(x) for x in z.rotations[0]]
    for f in sorted(info['prop_frames']):
        w = rig.world(anim, f)
        R3P.place(anim, iao_l, f, w[rig.parents[iao_l]], REFLECT @ rig.world(anim_m, f)[iao_r] @ REFLECT)
    names = {BALL_EDID: BALL_EDID_L, ROD_EDID % label: ROD_EDID_L % label}

    def rename(text):
        if text == LOADED:
            return LOADED_RIGHT
        head, _, edid = text.partition('.')
        return '%s.%s' % (head, names[edid]) if head in ('AnimObjLoad', 'AnimObjDraw') and edid in names else text
    for a in anim.annotations:
        a.text = rename(a.text)
    write_clip(out, ADS.havok_blocks(anim), floats, reference=True)
    return [(x, rename(s)) for x, s in added]


def check_right(ctx, path, added, c, axis, var):
    """Decode a right-hand clip in the real world: on Loop's right idle (gun side) until the reload starts, the end on
    his right idle with the free left arm on Goetia's (two pistols: on Loop's left idle, frame 0; the double mirror is the
    identity), the props on the real bore, the annotations as written."""
    got = anim_skyrim.load_skyrim_animation(path)
    src = anim_skyrim.load_skyrim_animation(os.path.join(ctx.right_dir, CLIP_RIGHT))
    idle = anim_skyrim.load_skyrim_animation(os.path.join(ctx.right_dir, IDLE_RIGHT))
    if var.real_rest:          # a melee weapon: the dual-wield idle's forearm
        goetia, rest_frames = var.real_rest
    elif var.dual:
        goetia, rest_frames = ctx.loop_clip(IDLE), [0]
    else:
        goetia = ctx.idle_clip(IDLE_SOURCE_RIGHT)
        rest_frames = range(goetia.num_frames)
    rig, ix = ctx.rig, ctx.ix
    ADS.check_blocks(path)
    w_hold = rig.world(idle, 0)
    for f in range(KEEP_FRAMES + 1):
        for b in (ix['NPC R Hand [RHnd]'], ix['Weapon'], ix['NPC Head [Head]']):
            d = np.linalg.norm(rig.world(got, f)[b][:3, 3] - w_hold[b][:3, 3])
            if d > 0.3:
                sys.exit('%s: frame %d is %.2f off the hold on bone %d (the reload starts from it)' % (path, f, d, b))
    last = got.num_frames - 1
    clav = ix['NPC L Clavicle [LClv]']

    def in_left_arm(b):
        while b >= 0:
            if b == clav:
                return True
            b = rig.parents[b]
        return False
    wl, wi = rig.world(got, last), rig.world(idle, 0)
    worst = max(np.linalg.norm(wl[b][:3, 3] - wi[b][:3, 3]) for b in range(len(got.tracks)) if not in_left_arm(b))
    if worst > 0.5:
        sys.exit('%s: last frame %.2f units off Loop\'s right idle' % (path, worst))
    ang = lambda a, b: math.degrees(2 * math.acos(min(1.0, abs(sum(x * y for x, y in zip(a, b))))))  # noqa: E731
    free = [ix[swap_side(n)] for n in var.half + var.full if n not in ('AnimObjectR', 'Weapon')]
    arm = min(max(ang(got.tracks[b].rotations[last], goetia.tracks[b].rotations[g]) for b in free)
              for g in rest_frames)
    if arm > 1.5:
        sys.exit('%s: the free left arm ends %.1f deg off its idle' % (path, arm))
    f_of = lambda t: int(round(t / got.frame_duration))  # noqa: E731
    for beat, what, tol in (('drop', 'ball', 1.5), ('rammed', 'rod', 0.5), ('stroke_up', 'rod', 0.5)):
        w = rig.world(got, f_of(var.beats[beat]))
        gun, prop = w[ix['Weapon']], w[ix['AnimObjectL']]
        muzzle = (gun @ np.r_[c, 1])[:3]
        bore = unit(gun[:3, :3] @ axis)
        off = prop[:3, 3] - muzzle
        dist = float(np.linalg.norm(np.cross(off, bore)))
        par = abs(float(unit(prop[:3, :3] @ np.array([0, 1.0, 0])) @ bore))
        if dist > tol or off @ bore < -1.0 or (what == 'rod' and par < 0.99):
            sys.exit('%s: the %s at %s is %.2f off the bore line (%.2f along it, axis cos %.3f)'
                     % (path, what, beat, dist, off @ bore, par))
    src_ann = [(round(a.time, 4), a.text) for a in src.annotations]
    if sorted((round(a.time, 4), a.text) for a in got.annotations) != sorted(src_ann + [(round(x, 4), s) for x, s in added]):
        sys.exit('%s: annotations differ from those written' % path)
    return got, worst


def check_stow(ctx, path, var, mirrored, dense=1):
    """The melee weapon sits in its sheath while the hand is off it (DUAL_RELEASE to the glide out before DUAL_REGRIP):
    its real attach node (`Shield` for a right-hand pistol's clip, mirrored back) against the real sheath from the
    decoded clip's own body. A `dense` clip (densify) is checked on every frame from the first source key in that window
    to the last. Returns the worst (offset, degrees)."""
    got = anim_skyrim.load_skyrim_animation(path)
    node = ctx.ix['Shield' if mirrored else 'Weapon']
    anchor, L = var.real_sheath
    fd = got.frame_duration * dense
    worst = (0.0, 0.0)
    for f in range(math.ceil((DUAL_RELEASE - TRIM) / fd - 1e-6) * dense,
                   math.floor((DUAL_REGRIP - (DUAL_RELEASE - DUAL_TUCKED) - TRIM) / fd + 1e-6) * dense + 1):
        w = ctx.rig.world(got, f)
        s, have = unscaled(w[anchor]) @ L, unscaled(w[node])
        worst = (max(worst[0], float(np.linalg.norm(have[:3, 3] - s[:3, 3]))),
                 max(worst[1], angle_between(have[:3, :3], s[:3, :3])))
    if worst[0] > 0.3 or worst[1] > 1.0:
        sys.exit('%s: the sheathed weapon is %.2f units / %.1f deg off its sheath' % (path, worst[0], worst[1]))
    return worst


def requested(left):
    """That hand's reload asked for (REQUEST): its request variable at 1 as the clip starts."""
    return {'condition': 'CompareValues', 'requiredVersion': '1.0.0.0', 'Value A': {'value': 1.0}, 'Comparison': '==',
            'Value B': {'graphVariable': REQUEST[left], 'graphVariableType': 'Float'}}


def conditions(weapons, left):
    """Drawn, one of `weapons` in the pistol hand (`left`), the other hand unarmed, asked for. (Until 2026-11-02 also
    not Hair Trigger: that talent's faster reload is gone, so every reload is this clip.)"""
    return [LOOP.DRAWN,
            LOOP.any_of([LOOP.equipped(p, f, left) for p, f in weapons]),
            {'condition': 'IsEquippedType', 'requiredVersion': '1.0.0.0', 'Type': {'value': 0.0}, 'Left hand': not left},
            requested(left)]


def conditions_dual(weapons, left, pistols):
    """Drawn, one of `weapons` in the firing hand (`left`), any of `pistols` in the other, asked for."""
    return [LOOP.DRAWN,
            LOOP.any_of([LOOP.equipped(p, f, left) for p, f in weapons]),
            LOOP.any_of([LOOP.equipped(p, f, not left) for p, f in pistols]),
            requested(left)]


def item_name(typ):
    """'sword', 'dagger', 'axe', 'mace' (STOW) or 'shield' (SHIELD)."""
    return 'shield' if typ == SHIELD else STOW[typ][0]


def stow_suffix(typ, female):
    """The submod name's part for a melee weapon or a shield in the other hand: ' (sword)', ' (dagger, female)'."""
    return ' (%s%s)' % (item_name(typ), {None: '', True: ', female', False: ', male'}[female])


def conditions_stow(weapons, left, typ, female):
    """Drawn, one of `weapons` in the pistol hand (`left`), a one-handed melee weapon of type `typ` (or a SHIELD) in the
    other, the player's sex where the sheath depends on it (`female`, None for either), asked for. OAR numbers the
    melee types as Papyrus does, a shield OAR_SHIELD."""
    out = [LOOP.DRAWN,
           LOOP.any_of([LOOP.equipped(p, f, left) for p, f in weapons]),
           {'condition': 'IsEquippedType', 'requiredVersion': '1.0.0.0',
            'Type': {'value': float(OAR_SHIELD if typ == SHIELD else typ)}, 'Left hand': not left},
           requested(left)]
    if female is not None:
        out.append({'condition': 'IsFemale', 'requiredVersion': '1.0.0.0', 'negated': not female})
    return out


def check_belt(ctx, path, belt_t, mirrored, beats=DUAL_BEATS, dense=1):
    """The other gun stays put while it is in the belt: its attach node's world drift from `beats` tucked to regrip
    (the real Shield for a right-hand clip, whose tucked gun is the left one); a `dense` clip on every frame between
    those source keys."""
    got = anim_skyrim.load_skyrim_animation(path)
    node = ctx.ix['Shield' if mirrored else 'Weapon']
    fd = got.frame_duration * dense
    ps = [ctx.rig.world(got, f)[node][:3, 3]
          for f in range(int(round((beats['tucked'] - TRIM) / fd)) * dense,
                         int(round((beats['regrip'] - TRIM) / fd)) * dense + 1)]
    drift = max(np.linalg.norm(p - ps[0]) for p in ps)
    if drift > 0.3:
        sys.exit('%s: the tucked gun drifts %.2f units in the belt' % (path, drift))
    return drift


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else ADS.TOOLS['modlistRoot']
    ctx = Ctx(root)
    groups = pistol_groups(ctx.mods_dir, ctx.mods)
    out_mod = os.path.join(ctx.mods_dir, DEPLOY)
    oar = os.path.join(out_mod, *OAR)
    if os.path.isdir(oar):
        shutil.rmtree(oar)
    os.makedirs(oar)
    written = 0
    pistols = [w for g in groups for w in g[2]]
    stows = [(typ, female) for typ in sorted(STOW) for female in ((True, False) if typ in STOW_SEXED else (None,))]
    shields = [(SHIELD, female) for female in (True, False)]
    shield_pose = shield_arm(ctx)
    jobs = [(h, k) for k in [None, 'two'] for h in ('left', 'right')]
    jobs += [(h, k) for k in stows for h in ('left', 'right')]
    jobs += [('right', k) for k in shields]  # shields are left-hand only
    for hand, kind in jobs:
        right = hand == 'right'
        dual = kind is not None              # a pistol, a melee weapon or a shield in the other hand
        stow = kind if isinstance(kind, tuple) else None
        if stow:
            var = ctx.shield(stow[1]) if stow[0] == SHIELD else ctx.stow(right, *stow)
            suffix = stow_suffix(*stow)
        else:
            var = {(False, False): ctx.left, (True, False): ctx.right, (False, True): ctx.dual_left,
                   (True, True): ctx.dual_right}[(right, dual)]
            suffix = DUAL if dual else ''
        loop_dir, aim_clips = (ctx.right_dir, AIM_CLIPS_RIGHT) if right else (ctx.loop_dir, AIM_CLIPS)
        for i, (label, path, weapons, (c, axis, radius), _) in enumerate(groups):
            # the right hand is solved as a left-hand clip in the mirrored world (Variant), where the mesh is z-flipped
            flip = MESH_FLIP if right else np.ones(3)
            anim, info, added, misses, wrists, _ = build_clip(ctx, label, c * flip, axis * flip, radius, var)
            if max(misses.values()) > 0.5:
                sys.exit('%s: a hand misses its target by %.2f' % (label, max(misses.values())))
            if abs(info['gun_scale'] - (RIGHT_GUN_SCALE if right else 1.0)) > 0.002:
                sys.exit('%s %s: the gun hand is scaled %.3f, not %.3f: update RIGHT_GUN_SCALE (tools/02 sizes the '
                         'rods with it)' % (hand, label, info['gun_scale'], RIGHT_GUN_SCALE if right else 1.0))
            name = 'Reload %s%s%s' % (label, suffix, ' (right hand)' if right else '')
            sub = os.path.join(oar, name)
            os.makedirs(sub)
            out = os.path.join(sub, CLIP_RIGHT if right else CLIP)
            floats = ctx.bsa_floats(CLIP_RIGHT if right else CLIP)  # vanilla's: Loop's shot clips carry none
            if right:
                tmp = os.path.join(os.environ.get('TEMP', '.'), '_pistol_reload_right.hkx')
                anim_skyrim.write_skyrim_animation(tmp, ADS.havok_blocks(anim), ptr_size=8)
                check(ctx, tmp, added, var)
                added = unmirror(ctx, label, anim, tmp, info, added, out, floats)
                os.remove(tmp)
                got, end_gap = check_right(ctx, out, added, c, axis, var)
            else:
                write_clip(out, ADS.havok_blocks(anim), floats, reference=True)
                got, end_gap = check(ctx, out, added, var)
            got = trim(got)                  # the hold before the reload off (TRIM), after the per-frame checks
            if dual:                         # a weapon off the hand: DENSE keys
                got = densify(ctx, got)
            write_clip(out, ADS.havok_blocks(got), floats, reference=True)
            ADS.check_blocks(out)
            if stow:
                print('      sheath: the %s %.2f units / %.1f deg off it' % ((item_name(stow[0]),) +
                                                                       check_stow(ctx, out, var, right, DENSE)))
                if var.shield:
                    print('      shield: let go %s; carried at least %.1f off the spine and legs'
                          % (info['letgo'], info['shield_clear']))
            elif dual:
                drift = check_belt(ctx, out, info['belt'], right, var.beats, DENSE)
                print('      belt: %s; the tucked gun drifts %.2f' % (info['belt_params'], drift))
            for clip in aim_clips:
                a = anim_skyrim.load_skyrim_animation(os.path.join(loop_dir, clip))
                if stow and stow[0] == SHIELD:      # the arm tools/07 gives Loop's clips with a shield
                    a = with_arm(a, shield_pose)
                a.annotations.append(anim_skyrim.Annotation(time=0.0, text=UNEQUIP))
                write_clip(os.path.join(sub, clip), ADS.havok_blocks(a), HF.read_file(os.path.join(loop_dir, clip)))
                ADS.check_blocks(os.path.join(sub, clip))
            written += 1 + len(aim_clips)
            print('%-5s%s %-18s %s: muzzle %.1f out, r %.2f, rod %.1f; load pose: muzzle %+.0f above the shoulders, %.0f '
                  'ahead, tilt %.0f fwd %.0f out, roll %.0f, held %.0f up (slack %.1f, candidate %d); misses gun %.2f '
                  'ram %.2f; worst wrist bend/roll gun %.0f/%.0f ram %.0f/%.0f deg; %.2f s; end %.2f off'
                  % (hand, suffix, label, ', '.join('%s %s' % w for w in weapons), c[1], radius, info['Lr'],
                     info['height'],
                     info['ahead'], info['tilt_f'], info['tilt_r'], info['roll'], info['slide'], info['slack'],
                     info['attempt'],
                     misses['L'], misses['R'], wrists['L'][0], wrists['L'][1], wrists['R'][0], wrists['R'][1],
                     got.duration, end_gap))
            if max(wrists['L'][0], wrists['R'][0]) > WRIST_BEND_MAX or max(wrists['L'][1], wrists['R'][1]) > WRIST_ROLL_MAX:
                sys.exit('%s: a wrist bends or rolls past %d / %d deg' % (label, WRIST_BEND_MAX, WRIST_ROLL_MAX))
            if info['head_clear'] < HEAD_CLEAR_MIN:
                sys.exit('%s: the ramming arm comes within %.1f of the face' % (label, info['head_clear']))
            if stow and stow[0] == SHIELD:
                cfg = {'name': name,
                       'description': 'Ramrod reload after the shot, right-hand pistol, a shield in the other hand: %s '
                                      '(%s). The shield goes on the back for the ball and ramrod and is taken again.'
                                      % (', '.join('%s %s' % w for w in weapons), os.path.basename(path)),
                       'priority': PRIORITY_SHIELD_RIGHT + 10 * shields.index(stow) + i,
                       'conditions': conditions_stow(weapons, False, *stow)}
            elif stow:
                cfg = {'name': name,
                       'description': 'Ramrod reload after the shot, %s-hand pistol, a %s in the other hand: %s (%s). '
                                      'The %s goes in its sheath for the ball and ramrod and is drawn again.'
                                      % (hand, STOW[stow[0]][0], ', '.join('%s %s' % w for w in weapons),
                                         os.path.basename(path), STOW[stow[0]][0]),
                       'priority': (PRIORITY_STOW_RIGHT if right else PRIORITY_STOW) + 10 * stows.index(stow) + i,
                       'conditions': conditions_stow(weapons, not right, *stow)}
            elif dual:
                cfg = {'name': name,
                       'description': 'Ramrod reload after the shot, %s-hand pistol, a pistol in the other hand: %s '
                                      '(%s). The other gun goes in the belt for the ball and ramrod and comes back.'
                                      % (hand, ', '.join('%s %s' % w for w in weapons), os.path.basename(path)),
                       'priority': (PRIORITY_DUAL_RIGHT if right else PRIORITY_DUAL) + i,
                       'conditions': conditions_dual(weapons, not right, pistols)}
            else:
                cfg = {'name': name,
                       'description': 'Ramrod reload after the shot, %s-hand pistol, other hand free: %s (%s). Loop\'s '
                                      'shot to the top of his recoil, then ball and ramrod; ends on his idle.'
                                      % (hand, ', '.join('%s %s' % w for w in weapons), os.path.basename(path)),
                       'priority': (PRIORITY_RIGHT if right else PRIORITY) + i,
                       'conditions': conditions(weapons, not right)}
            ADS.write_config(sub, cfg)
    ADS.write_config(oar, {'name': MOD, 'author': 'Zenderal',
                           'description': 'A ramrod reload on the flintlock pistols (third person, either hand, the '
                                          'other one free): the shot clip carries it. Needs the Pandora patch '
                                          'zpistolreload.'})
    patch = ['Pandora_Engine', 'mod', 'zpistolreload']     # only ours: Patch Collection carries other Pandora patches
    dst = os.path.join(out_mod, *patch)
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    shutil.copytree(os.path.join(ROOT, 'src', 'PistolRamrodReload', *patch), dst)
    os.remove(ctx.tmp)
    print('built %s for profile %s: %d groups x 2 hands x one or two pistols, %d clips'
          % (out_mod, ctx.profile, len(groups), written))


if __name__ == '__main__':
    main()
