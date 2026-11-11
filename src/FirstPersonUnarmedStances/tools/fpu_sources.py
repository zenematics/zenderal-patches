"""Shared table for FirstPersonUnarmedStances: the three first-person unarmed sets, the stance each plays in, and which
of their OAR submods are used. Change a set's stance here, then rerun 01 and 02.

Neutral (no stance) stays SIGMA - Fisting animations - 1st person, untouched. It sits below all three sets, so in a
stance it fills in every clip that stance's set does not have (stagger, dodge, sneak roll...).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def _tools_root():
    cfg = os.path.join(HERE, '..', '..', '..', '.claude', 'config', 'tools.json')
    if os.path.exists(cfg):
        with open(cfg, encoding='utf-8-sig') as fh:
            return json.load(fh).get('modlistRoot') or 'E:/Zenderal'
    return 'E:/Zenderal'


ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
ROOT = ARGS[0] if ARGS else _tools_root()
PROFILE = os.path.join(ROOT, 'profiles', ARGS[1] if len(ARGS) > 1 else 'Ultra')
MODS = os.path.join(ROOT, 'mods')
DOWNLOADS = os.path.join(ROOT, 'downloads')
OVERWRITE = os.path.join(ROOT, 'overwrite')
OAR_1P = ('meshes', 'actors', 'character', '_1stperson', 'animations', 'OpenAnimationReplacer')
OVERLAY_MOD = 'Zenderal - 1P Unarmed Stance Overlays'
NEUTRAL_MOD = 'SIGMA - Fisting animations - 1st person'

STANCES_ESP = 'Stances - Dynamic Weapon Movesets SE.esp'
PERKS = {'High': '42518', 'Mid': '42519', 'Low': '4251A'}   # F1 / F2 / F3 (stances_*stance_perk)

# 'use': submod folders (relative to the 1P OAR root) that play in the stance; every other submod is disabled.
# 'priority_add': added to the author's priority so the set outranks SIGMA's 1000010-1000021 (CFPAO ships 1-4).
# 'fists': True adds right AND left hand unarmed (First-Person Boxing ships with NO conditions, so raw it replaced
# every 1H weapon's first-person block idle and bash as well).
SOURCES = {
    'jelly': {'mod': 'JellyFishFP (un)armed (1st person animations series)', 'glob': 'JellyFishFP Unarmed*180197*',
              'nexus': (180197, 754110, '1.01'), 'credit': 'JellyFishInLoop', 'stance': 'High',
              'use': ('JFFPU/unrmd', 'JFFPU/unrmdm'), 'priority_add': 0, 'fists': False},
    'cfpao': {'mod': 'Comprehensive First Person Animation Overhaul - CFPAO',
              'glob': 'Comprehensive First Person Animation Overhaul-87169-*', 'nexus': (87169, 584071, '1.5.1'),
              'credit': 'polar', 'stance': 'Mid',
              'use': ('CFPAO/UnarmedDefault', 'CFPAO/UnarmedDefaultH', 'CFPAO/UnarmedDefaultHT'),
              'priority_add': 1_000_100, 'fists': False},
    'boxing': {'mod': 'First-Person Boxing Animation', 'glob': 'First Person Boxing Animation-179716-*',
               'nexus': (179716, 750996, '1.0'), 'credit': 'modbom1', 'stance': 'Low',
               'use': ('First-Person Boxing Animation/First-Person Boxing',) +
                      tuple(f'First-Person Boxing Animation/Combo{i}' for i in range(1, 6)),
               'priority_add': 0, 'fists': True},
}

# Clips 01 writes into the overlay mod as copies with annotations added (nothing else changed), so the first-person
# fist combo (src/FirstPersonFistCombo: the next punch starts at AttackWinStart / AttackWinStartLeft) reaches them.
# First-Person Boxing's 0.67 s jabs carry no annotations and keep the vanilla H2H_RightHook / H2H_LeftHook triggers,
# whose AttackWinStart(Left) (0.700 s) lies past the clip's end: attackStop comes at end - 0.1 = 0.567 s (right) /
# end - 0.05 = 0.617 s (left). The markers go just after the vanilla HitFrame (0.533 s), so the hit lands first.
# (source, clip relative to the 1P OAR root, expected duration, [(time, annotation)])
CLIP_MARKERS = [
    ('boxing', 'First-Person Boxing Animation/First-Person Boxing/h2h_attackright.hkx', 0.6667, [(0.54, 'AttackWinStart')]),
    ('boxing', 'First-Person Boxing Animation/First-Person Boxing/h2h_attackleft.hkx', 0.6667, [(0.54, 'AttackWinStartLeft')]),
]


def has_perk(stance):
    return {'condition': 'HasPerk', 'requiredVersion': '1.0.0.0',
            'Perk': {'pluginName': STANCES_ESP, 'formID': PERKS[stance]}}


def equipped(hand_left, type_value):
    return {'condition': 'IsEquippedType', 'requiredVersion': '1.0.0.0', 'Type': {'value': float(type_value)},
            'Left hand': hand_left}


FISTS = [equipped(False, 0), equipped(True, 0)]
PLAYER = {'condition': 'IsActorBase', 'requiredVersion': '1.0.0.0',
          'Actor base': {'pluginName': 'Skyrim.esm', 'formID': '7'}}
NEVER = [PLAYER, dict(PLAYER, negated=True)]    # player AND NOT player: a second lock on disabled submods


def find_ci(base, parts):
    """Walk `parts` below `base` case-insensitively; None if any part is missing."""
    p = base
    for part in parts:
        if not os.path.isdir(p):
            return None
        hit = [d for d in os.listdir(p) if d.lower() == part.lower()]
        if not hit:
            return None
        p = os.path.join(p, hit[0])
    return p


def submods(oar_root):
    """{rel path ('A/B'): (abs dir, config dict)} for every OAR submod (a config.json with a priority) below oar_root."""
    out = {}
    for dp, _dn, fn in os.walk(oar_root):
        if 'config.json' not in fn:
            continue
        with open(os.path.join(dp, 'config.json'), encoding='utf-8-sig') as fh:
            cfg = json.load(fh)
        if 'priority' in cfg:
            out[os.path.relpath(dp, oar_root).replace(os.sep, '/')] = (dp, cfg)
    return out
