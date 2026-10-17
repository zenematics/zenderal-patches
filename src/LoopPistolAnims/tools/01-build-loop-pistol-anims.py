"""Rebuild the `Zenderal - Loop Pistol Animations` MO2 mod: Simple Pistol Shooting Animation by Loop 3.0's
clips re-published as an OAR mod that outranks the list's staff animations.

Loop's mod is a legacy DAR mod (`_CustomConditions/12345-12348`). It fires on a LEFT-hand staff carrying
keyword `Pistol_Animation_By_Loop 0x801:Pistol animation by Loop.esp`, which the KID ini
`AdventurerFlintlockPack_PABL_KID.ini` gives the 8 Gentleman's Flintlock pistols (KID log 2026-10-17:
"added to 8/588"). But DAR priority 12345 loses every shared clip to:
  - Goetia Enchanted Staves `Main`                68000  NO conditions: all stfmagic_* aim/release + staff_idle
  - Goetia Enchanted Staves `Staves blend override` 68360  any staff drawn: all magcast_* movement
  - Goetia Enchanted Staves `Shield & Staff`      68364
  - Goetia Sneak Magic `_CustomConditions/68445`    sneaking with a staff
  - Smooth Moveset `Base - 1hm`                83030000  right hand unarmed..1h: magcast_* movement
  - Smooth Moveset `1hm/Staff`                999999010  any staff: staff_idle
so the pistol played Goetia's staff casting.

DAR condition files read OR as binding tighter than AND (`A AND B OR C` = `A AND (B OR C)`), so each folder is
`drawn AND left staff AND (Vigilant pistol OR Glenmoril keyword OR Loop keyword) [AND direction]`. Vigilant.esm
and Glenmoril.esm are not in the list, so only the Loop keyword is kept. Folder order is preserved.

The clips are copied from the user's installed Loop mod, never committed.

Usage:  python 01-build-loop-pistol-anims.py [<mods dir>]     (default E:/Zenderal/mods)
"""
import os, sys, json, hashlib, shutil
import importlib.util

_spec = importlib.util.spec_from_file_location('mirror_hkx', os.path.join(os.path.dirname(__file__), 'mirror_hkx.py'))
mirror_hkx = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mirror_hkx)

MOD = 'Zenderal - Loop Pistol Animations'
SOURCE_MOD = 'Simple Pistol Shooting Animation by loop 3.0 - SSE'
DAR = ['meshes', 'actors', 'character', 'animations', 'DynamicAnimationReplacer', '_CustomConditions']
OAR = ['meshes', 'actors', 'character', 'animations', 'OpenAnimationReplacer', MOD]
LOOP_ESP = 'Pistol animation by Loop.esp'
# above Smooth Moveset's 999999010 staff_idle; below RaySense cover loops (2110000004+)
BASE_PRIORITY = 1000000000

FLINTLOCK_ESP = 'AdventurerFlintlockPack.esp'
# The 8 Gentleman's Flintlock pistols (src/FlintlockOverhaul/FlintlockOverhaulESP/Weapons/).
PISTOLS = ['816', '817', '818', '819', '834', '838', '839', '83A']

DRAWN = {'condition': 'IsWeaponDrawn', 'requiredVersion': '1.0.0.0'}


def equipped(plugin, form_id, left):
    return {'condition': 'IsEquipped', 'requiredVersion': '1.0.0.0',
            'Form': {'pluginName': plugin, 'formID': form_id}, 'Left hand': left}


def has_keyword(form_id, left):
    return {'condition': 'IsEquippedHasKeyword', 'requiredVersion': '1.0.0.0',
            'Keyword': {'pluginName': LOOP_ESP, 'formID': form_id}, 'Left hand': left}


def any_of(conditions):
    return {'condition': 'OR', 'requiredVersion': '1.0.0.0', 'Conditions': conditions}


# v2 (2026-10-17): v1 required Loop's keyword on a LEFT-hand staff, and in game Goetia's unconditional `Main`
# still won every stfmagic_* clip, i.e. v1's conditions failed; v2 matches the pistols by form as well as by keyword.
# Loop's clips are left-hand clips (FK: the aim pose puts the Shield node level and forward), verified in the left
# hand 2026-10-17 (v5). The right hand plays its OWN files (stfmagicright_*, staffright_idle, staffmagicright_*arm;
# v6 in game: right hand still played staff animations), so the right-hand submods serve MIRRORED copies
# (mirror_hkx.py) under those names.


def pistol(left):
    return any_of([equipped(FLINTLOCK_ESP, f, left) for f in PISTOLS] + [has_keyword('801', left)])


def direction(value):
    return {'condition': 'IsMovementDirection', 'requiredVersion': '1.0.0.0', 'Direction': {'value': value}}


def submods(left):
    """DAR folder -> (submod name, description, conditions) for one hand."""
    hand = 'left' if left else 'right'
    tag = '' if left else ' (right hand)'
    moving = {'condition': 'OR', 'requiredVersion': '1.0.0.0',
              'Conditions': [direction(1.0), direction(2.0), direction(3.0), direction(4.0)]}
    return {
        '12345': ('Pistol' + tag, f'Flintlock pistol in the {hand} hand: aim, fire, idle, movement.',
                  [DRAWN, pistol(left)]),
        '12346': ('Pistol moving idle' + tag, f'Flintlock pistol in the {hand} hand while moving: idle.',
                  [DRAWN, pistol(left), moving]),
        '12347': ('Pistol standing turns' + tag, f'Flintlock pistol in the {hand} hand while standing: turns.',
                  [DRAWN, pistol(left), direction(0.0)]),
        '12348': ('Crossbow release' + tag, f"Loop's own keyword 0x822 in the {hand} hand: release.",
                  [DRAWN, has_keyword('822', left)]),
    }


# right-hand submods sit above the left ones (both hands holding pistols: the right-hand files differ anyway)
RIGHT_PRIORITY_OFFSET = 1000
# mirrored clip -> the file it replaces for a right-hand staff. Left-hand-only files get their right-hand twin;
# shared movement/turn files swap left <-> right (a mirrored left sidestep is a right sidestep).
RIGHT_FILES = {'staff_idle.hkx': 'staffright_idle.hkx',
               'staffmagic_runarm.hkx': 'staffmagicright_runarm.hkx',
               'staffmagic_walkarm.hkx': 'staffmagicright_walkarm.hkx'}
LR_PAIRS = [('mag_runbackwardleft', 'mag_runbackwardright'), ('mag_runstrafeleft', 'mag_runstraferight'),
            ('magcast_runbackwrdleft', 'magcast_runbckwrdright'), ('magcast_runforwardleft', 'magcast_runfrwrdright'),
            ('magcast_runleft', 'magcast_runright'), ('magcast_runstrafeleft', 'magcast_runstraferight'),
            ('magcast_turnleft180', 'magcast_turnright180'), ('magcast_turnleft60', 'magcast_turnright60'),
            ('magcast_walkbckwrdleft', 'magcast_walkbckwrdrht'), ('magcast_walkforwrdleft', 'magcast_walkfrwrdright'),
            ('magcast_walkleft', 'magcast_walkright'),
            ('staffmagiccast_turnleft180', 'staffmagiccast_turnright180'),
            ('staffmagiccast_turnleft60', 'staffmagiccast_turnright60')]
for _a, _b in LR_PAIRS:
    RIGHT_FILES[_a + '.hkx'] = _b + '.hkx'
    RIGHT_FILES[_b + '.hkx'] = _a + '.hkx'


# v11: Bethesda's own right-hand staff clips keep pelvis, legs and spine IDENTICAL to the left-hand ones and differ
# only in the arms, so every right-hand clip keeps Loop's body and mirrors only the arms (mirror_hkx.mirror_arms).
# Earlier mirrors of the whole body (v7/v8) or the spine up (v9) made running right-handed glitch while the left
# hand ran clean, aiming or not. Looping strides take the arms from half a stride later. Clip files keep their own
# names except the left-hand-only ones, which take their right-hand twin (stfmagic_ -> stfmagicright_, ...).
LOCOMOTION = ('mag_', 'magcast_', 'staffmagiccast_turn')
CYCLIC = ('mag_run', 'magcast_run', 'magcast_walk')


def right_file(clip):
    low = clip.lower()
    if low.startswith('stfmagic_'):
        return 'stfmagicright_' + low[len('stfmagic_'):]
    if low.startswith(LOCOMOTION):
        return low  # the body is the original's, so the clip keeps its own direction
    return RIGHT_FILES.get(low, low)


MOD_CONFIG = {
    'name': MOD,
    'author': 'Zenderal',
    'description': "Simple Pistol Shooting Animation by Loop's DAR folders as OAR submods above Goetia "
                   'Enchanted Staves and Smooth Moveset, so the flintlock pistols use them.',
}


def main():
    mods = sys.argv[1] if len(sys.argv) > 1 else 'E:/Zenderal/mods'
    src_root = os.path.join(mods, SOURCE_MOD, *DAR)
    if not os.path.isdir(src_root):
        raise SystemExit(f'not found: {src_root}')
    mod_dir = os.path.join(mods, MOD, *OAR)
    if os.path.isdir(mod_dir):
        shutil.rmtree(mod_dir)  # generated by this script only
    os.makedirs(mod_dir)
    with open(os.path.join(mod_dir, 'config.json'), 'w', encoding='utf-8') as fh:
        json.dump(MOD_CONFIG, fh, indent=4)
    total = 0
    mirror = None
    for left in (True, False):
        for folder, (name, desc, conditions) in submods(left).items():
            src = os.path.join(src_root, folder)
            clips = sorted(f for f in os.listdir(src) if f.lower().endswith('.hkx'))
            if not clips:
                raise SystemExit(f'no clips in {src}')
            sub_dir = os.path.join(mod_dir, name)
            os.makedirs(sub_dir)
            priority = BASE_PRIORITY + int(folder) + (0 if left else RIGHT_PRIORITY_OFFSET)
            config = {'name': name, 'description': desc, 'priority': priority, 'conditions': conditions}
            with open(os.path.join(sub_dir, 'config.json'), 'w', encoding='utf-8') as fh:
                json.dump(config, fh, indent=4)
            outs = set()
            for clip in clips:
                if left:
                    out = clip
                    shutil.copyfile(os.path.join(src, clip), os.path.join(sub_dir, out))
                else:
                    if mirror is None:
                        mirror = mirror_hkx.Mirror(mods)
                    out = right_file(clip)
                    mirror.mirror_arms(os.path.join(src, clip), os.path.join(sub_dir, out),
                                       half_cycle=clip.lower().startswith(CYCLIC))
                if out.lower() in outs:
                    raise SystemExit(f'{name}: two clips map to {out}')
                outs.add(out.lower())
                with open(os.path.join(sub_dir, out), 'rb') as fh:
                    digest = hashlib.sha1(fh.read()).hexdigest()[:12]
                print(f'{digest}  {name}/{out}' + ('' if left else f'  <- mirrored {clip}'))
            if left:
                total += len(clips)
            print(f'  {len(clips)} clips, priority {priority}  <- {folder}')
    if total != 46:
        raise SystemExit(f'expected 46 clips from Loop 3.0, copied {total}')
    print(f'{total} clips per hand -> {mod_dir}')


if __name__ == '__main__':
    main()
