"""Rebuild the `Zenderal - Le Sentiment du Fer High Stance` MO2 mod: Khonraad's Le Sentiment du Fer - HEMA Combat
Overhaul (SSE 1.01, Nexus 50798) converted from SkySA to ADXP|MCO, as the Stances mod's High stance (F1), in third
person, with For Honor Reforged's mechanics left working.

Why (arch-docs/patches/LSdFHighStance.md has the evidence):
  - LSdF is a SkySA moveset: DAR folders of `skysa_<weapon>N` / `skysa_power<weapon>N` clips (5 attacks, each can
    turn into power attack N: SkySA's combo position), gated by One-/Two-Handed skill (25/50/75), plus guard
    animations (idle, walks, turns). The list runs ADXP|MCO, which plays `mco_attackN` / `mco_powerattackN` and reads
    its combo windows from annotations: `MCO_WinOpen`/`MCO_WinClose`, `MCO_PowerWinOpen`/`MCO_PowerWinClose`,
    `MCO_Recovery`, and the next slots from `PIE.@SGVI|MCO_nextattack|N` / `MCO_nextpowerattack|N` (MCO's own
    SkySA-converted defaults in Attack MCO-DXP show the mapping: SkySA_AttackWinstart -> both WinOpens,
    SkySA_AttackWinEnd -> both WinCloses + Recovery).
  - LSdF's dual-wield left-hand hits were HitFrame triggers in its own SkySA behavior patch, not in the clips; MCO
    does not run that patch, so they are written into the clips here.
  - For Honor Reforged owns the same MCO slots. Its special submods (directional attacks on DMK's
    `DirecionalCycleMoveset`, the back-light parry, parry/block-slide/knockdown follow-ups, combo layers) are
    distinguished by conditions, not by a priority gap; every generated attack submod carries NOT(<that submod's
    whole condition set>) for each one, so FHR's clip (with its PIE mechanics) plays in those windows at any priority.

What it builds, under `meshes/actors/character/animations/OpenAnimationReplacer/<MOD>/`:
  - LSdF's DAR folders are evaluated exactly (DAR semantics: OR lines group, groups AND; higher folder number wins
    per file; loose root files lowest) for every right/left weapon type and every One-/Two-Handed skill band
    (<25, 25-49, 50-74, 75+). Each distinct result becomes one submod: HasPerk(High Stance 42518) AND player AND
    the weapon/skill cells that produce it.
  - Attack submods: `mco_attack1..10` / `mco_powerattack1..10` (slots past LSdF's count repeat its sequence, so an
    FHR directional clip that hands over a higher slot still lands on LSdF), annotated in the binary
    (hkx_annotate.py; nothing else in the clip changes). Power attacks get FHR's heavy tell `PIE.$FHFX`.
  - Guard submods: LSdF's idles, turns, walks, runs, equips. Not its block, bash or recoil clips (FHR, Dynamic Block
    Hit and the stagger mods own those), not its sneak or NPC folders, not first person.

The clips come from the user's LSdF download and are never committed.

Usage:  python 01-build-lsdf-high-stance.py [<modlist root>] [<profile>]     (default: tools.json modlistRoot, Ultra)
"""
import fnmatch
import hashlib
import io
import itertools
import json
import math
import os
import re
import shutil
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'FHRFirstPerson', 'tools'))
import hkx_annotate  # noqa: E402


def _tools_root():
    cfg = os.path.join(HERE, '..', '..', '..', '.claude', 'config', 'tools.json')
    try:
        with open(cfg, encoding='utf-8-sig') as fh:
            return json.load(fh).get('modlistRoot') or 'E:/Zenderal'
    except OSError:
        return 'E:/Zenderal'


ROOT = sys.argv[1] if len(sys.argv) > 1 else _tools_root()
PROFILE = os.path.join(ROOT, 'profiles', sys.argv[2] if len(sys.argv) > 2 else 'Ultra')
MODS = os.path.join(ROOT, 'mods')
DOWNLOADS = os.path.join(ROOT, 'downloads')
MOD = 'Zenderal - Le Sentiment du Fer High Stance'
OAR_REL = ('meshes', 'actors', 'character', 'animations', 'OpenAnimationReplacer')
OUT = os.path.join(MODS, MOD, *OAR_REL, MOD)

SOURCE_GLOB = 'Le Sentiment du Fer - HEMA Combat Overhaul-50798-1-01-*.zip'   # SSE 1.01 (the LE 107910 is 32-bit)
SOURCE_MD5 = None   # filled in below from the first build; a different archive is reported, not refused
ANIM = 'meshes/actors/character/animations/'
DAR = ANIM + 'dynamicanimationreplacer/_customconditions/'
SKYSA_1HM = 'nemesis_engine/mod/skysa/1hm_behavior/'

STANCE_PERK = ('Stances - Dynamic Weapon Movesets SE.esp', '42518')   # stances_highstance_perk; F1 = switchspell_H
FHR_MOD = 'For Honor Reforged'
PRIORITY_ATTACK = 1_500_000_100   # above all FHR attack submods (max 80,860,070); exclusive among themselves
PRIORITY_GUARD = 1_500_000_000    # above every moveset's idles/walks; below Beam Walking Assist (2.11e9),
                                  # UNDERDOG states (2.0e9) and RaySense (2.13e9+)
SLOTS = 10                        # MCO_Attack1..10 / MCO_PowerAttack1..10, as FHR fills them
PIE_GAP = 0.0                     # same-time PIE tags DO arrive (FHR's three at 0.0 s, 2026-11-10 trace); the old
                                  # 0.1 s "collapse" was the odd-offset string bug (see the doc's postmortem)
NEXT_ATTACK_AT, NEXT_POWER_AT, FHFX_AT = 0.06, 0.16, 0.0   # MCO's own time for the next slots
# Pace (curator 2026-11-10: "fast and fluid"). LSdF opens its window 0.34-0.54 s after the hit (median 0.54; FHR
# ~0.17), so the next attack started half a second late. All in clip time, before MCO_AttackSpeed.
SPEED_LIGHT, SPEED_POWER = 0.96, 0.88  # PIE.@SGVF|MCO_AttackSpeed at 0.0 s (FHR uses 0.85-1.1, MCO's defaults 1.0-1.3);
                                       # 1.2/1.1 felt ~20% too fast (curator 2026-11-10)
MOTION_STEP = 1 / 30              # AMR keys (animmotion/animrotation) sampled from LSdF's motion data at this step
STEP_DONE_BY_WINDOW = True        # LSdF steps AFTER the hit (light: one shared 62.5-unit ramp 0.26-0.66 s); with the
                                  # combo window at ~0.41 s a chained attack kept 35% of it. The whole curve moves
                                  # earlier (never before 0 s) so it ends at the window: the step drives into the hit
                                  # (FHR's attacks are ~50% moved by their hit) and every chained attack gets it all
WIN_AFTER_HIT = 0.15              # light attack: window opens this long after its last hit (or LSdF's, if earlier)
POWER_WIN_AFTER_HIT = 0.25        # power attack: window back into the combo
MIN_WINDOW = 0.35                 # the window stays open at least this long (or to LSdF's own end, if later)
RECOVERY_AFTER_OPEN = 0.10        # MCO_Recovery (move/block/dodge out) this long after the window opens
OH, TH = 6, 7                     # One-Handed, Two-Handed actor values (Enderal's skill tiers end at 25/50/75)
BANDS = (10, 30, 60, 80)          # sample skill per band: <25, 25-49, 50-74, 75+
EDGES = (0, 25, 50, 75)

# weapon types (DAR == OAR numbering): 0 fists, 1 sword, 2 dagger, 3 war axe, 4 mace, 5 greatsword, 6 battleaxe,
# 8 staff, 10 warhammer, 11 shield, 12-16 spells, 17 scroll, 18 torch
RIGHT_TYPES = (0, 1, 2, 3, 4, 5, 6, 10)
LEFT_TYPES = (0, 1, 2, 3, 4, 8, 11, 12, 13, 14, 15, 16, 17, 18)
TWO_HANDED = (5, 6, 10)
PREFIX = {0: 'h2h', 1: 'sword', 2: 'dagger', 3: 'axe', 4: 'mace', 5: '2hm', 6: '2hw', 10: '2hw'}
TYPE_NAME = {0: 'Fists', 1: 'Sword', 2: 'Dagger', 3: 'War Axe', 4: 'Mace', 5: 'Greatsword', 6: 'Battleaxe',
             8: 'Staff', 10: 'Warhammer', 11: 'Shield', 12: 'Spell', 13: 'Spell', 14: 'Spell', 15: 'Spell',
             16: 'Spell', 17: 'Scroll', 18: 'Torch'}
GUARD = re.compile(r'^((1hm|2hm|2hw|h2h|shd|2hc)_(idle|turn\w*|walk\w*|run\w*|equip|unequip|locomotionpose)'
                   r'|dw1hm1hmidle|dw_sprintforwardsword)$')


# --------------------------------------------------------------------------------------------- LSdF source ----

class Source:
    def __init__(self, path):
        self.path = path
        self.zip = zipfile.ZipFile(path)
        self.files = {}
        for info in self.zip.infolist():
            if not info.is_dir():
                self.files[info.filename.replace('\\', '/').lower()] = info
        self.folders = {}   # DAR folder number -> (conditions text, {clip name: member})
        self.root = {}      # loose root clip name -> member
        for name, info in self.files.items():
            if name.startswith(DAR):
                rest = name[len(DAR):].split('/')
                if len(rest) != 2:
                    continue
                num = int(rest[0])
                cond, clips = self.folders.setdefault(num, [None, {}])
                if rest[1] == '_conditions.txt':
                    self.folders[num][0] = self.zip.read(info).decode('utf-8', 'replace')
                elif rest[1].endswith('.hkx'):
                    clips[rest[1][:-4]] = info
            elif name.startswith(ANIM) and name.count('/') == ANIM.count('/') and name.endswith('.hkx'):
                self.root[name[len(ANIM):-4]] = info

    def read(self, info):
        return self.zip.read(info)


# DAR condition evaluation for the player (not sneaking), at a weapon pair and skill levels.
_DAR_LINE = re.compile(r'^\s*(NOT\s+)?(\w+)\((.*?)\)\s*(AND|OR)?\s*$', re.I)


def parse_dar(text):
    """-> list of AND-groups, each a list of OR-ed (negated, function, [args])."""
    groups, current = [], []
    for line in text.replace('\r', '').split('\n'):
        if not line.strip():
            continue
        m = _DAR_LINE.match(line)
        if not m:
            raise ValueError(f'unparsed DAR line: {line!r}')
        args = [a.strip().strip('"') for a in m.group(3).split(',')] if m.group(3).strip() else []
        current.append((bool(m.group(1)), m.group(2).lower(), args))
        if (m.group(4) or 'AND').upper() == 'AND':
            groups.append(current)
            current = []
    if current:
        groups.append(current)
    return groups


def eval_dar(groups, right, left, skill):
    def one(neg, fn, args):
        if fn == 'isequippedrighttype':
            v = right == int(args[0])
        elif fn == 'isequippedlefttype':
            v = left == int(args[0])
        elif fn == 'isactorvaluelessthan':
            v = skill[int(args[0])] < float(args[1])
        elif fn == 'isactorbase':
            v = args[0].lower().endswith('|0x000007') or args[0].lower().endswith('|0x7')
        elif fn == 'issneaking':
            v = False
        elif fn == 'random':
            v = False       # only NPC folders roll dice
        else:
            raise ValueError(f'unknown DAR function {fn}')
        return v != neg
    return all(any(one(*c) for c in g) for g in groups)


def effective(src, right, left, skill):
    """Winning clip per name for this pair and skill: DAR folders by number (high wins), loose root files lowest."""
    out = {name: ('root', info) for name, info in src.root.items()}
    for num in sorted(src.folders):
        cond, clips = src.folders[num]
        if cond is not None and eval_dar(src.dar[num], right, left, skill):
            for name, info in clips.items():
                out[name] = (num, info)
    return out


def dw_left_hits(src):
    """skysa_dwN / skysa_powerdwN -> [HitFrame times] from LSdF's SkySA behavior patch (event 36 = HitFrame in
    1hm_behavior's event list; Attack MCO-DXP's #0085 lists it at 36 too)."""
    objs = {}
    for name, info in src.files.items():
        if name.startswith(SKYSA_1HM) and name.endswith('.txt'):
            text = src.zip.read(info).decode('utf-8', 'replace')
            for m in re.finditer(r'<hkobject name="(#[^"]+)" class="(\w+)"(.*?)\n\t\t</hkobject>', text, re.S):
                objs[m.group(1)] = (m.group(2), m.group(3))
    out = {}
    for cls, body in objs.values():
        if cls != 'hkbClipGenerator':
            continue
        anim = re.search(r'name="animationName">Animations\\(skysa_(?:power)?dw\d+)\.hkx<', body, re.I)
        trig = re.search(r'name="triggers">(#[^<]+)<', body)
        if not anim or not trig or trig.group(1) not in objs:
            continue
        times = []
        for t in re.finditer(r'localTime">([0-9.]+)</hkparam>\s*<hkparam name="event">\s*<hkobject>\s*'
                             r'<hkparam name="id">(-?\d+)</hkparam>.*?relativeToEndOfClip">(\w+)<',
                             objs[trig.group(1)][1], re.S):
            if t.group(2) == '36' and t.group(3) == 'false':
                times.append(float(t.group(1)))
        if times:
            out[anim.group(1).lower()] = sorted(times)
    return out


SKYSA_ADSF = 'nemesis_engine/mod/skysa/animationdatasinglefile/defaultmale~1/'


def skysa_motion(src):
    """skysa clip name (e.g. 'skysa_sword1') -> (translations [(t, x, y, z)], rotations [(t, qx, qy, qz, qw)]).

    In Skyrim a clip's root motion is not in the .hkx: it is the behavior project's animation data, per CLIP
    GENERATOR. LSdF's SkySA patch adds it (`animationdatasinglefile/DefaultMale~1/SkySA_clipgenerator_<x>~skysa$N`
    names the generator's motion entry `skysa$N`, a duration, translation and rotation keys); its 1hm_behavior patch
    says which file each generator plays. MCO does not run that patch, so MCO played LSdF's clips without their
    forward steps: they are written into the clips as Animation Motion Revolution keys instead."""
    gen_motion, motion = {}, {}
    for name, info in src.files.items():
        if not name.startswith(SKYSA_ADSF) or not name.endswith('.txt'):
            continue
        lines = [ln.strip() for ln in src.zip.read(info).decode('utf-8', 'replace').splitlines() if ln.strip()]
        base = name[len(SKYSA_ADSF):-4]
        if '~' in base and lines and lines[0].lower().startswith('skysa_clipgenerator_'):
            gen_motion[lines[0].lower()] = lines[1].lower()
        elif base.startswith('skysa$') and len(lines) >= 4 and not any(ln.startswith('<!--') for ln in lines):
            # by line shape, not by the counts: LSdF's own skysa$11 says 4 translation keys and lists 3
            rows = [ln.split() for ln in lines[3:]]
            trans = [tuple(float(v) for v in r) for r in rows if len(r) == 4]
            rots = [tuple(float(v) for v in r) for r in rows if len(r) == 5]
            motion[lines[0].lower()] = (trans, rots)
    out = {}
    for name, info in src.files.items():
        if not (name.startswith(SKYSA_1HM) and name.endswith('.txt')):
            continue
        text = src.zip.read(info).decode('utf-8', 'replace')
        for m in re.finditer(r'name="name">(SkySA_clipgenerator_\w+)</hkparam>\s*<hkparam name="animationName">'
                             r'Animations\\(skysa_\w+)\.hkx<', text, re.I):
            mid = gen_motion.get(m.group(1).lower())
            if mid in motion:
                out.setdefault(m.group(2).lower(), motion[mid])
    return out


def _lerp_keys(keys, t):
    """Linear interpolation of [(time, values...)] at t (held before the first / after the last key)."""
    if t <= keys[0][0]:
        return keys[0][1:]
    for a, b in zip(keys, keys[1:]):
        if a[0] <= t <= b[0]:
            f = 0.0 if b[0] == a[0] else (t - a[0]) / (b[0] - a[0])
            return tuple(x + (y - x) * f for x, y in zip(a[1:], b[1:]))
    return keys[-1][1:]


def motion_shift(motion, done_by):
    """How much earlier the motion curve may move so its translation is complete by done_by (STEP_DONE_BY_WINDOW):
    by (its end - done_by), at most to the moment it starts moving, never earlier than 0 s."""
    trans = [(0.0, 0.0, 0.0, 0.0)] + [k for k in motion[0] if k[0] > 0]
    final = trans[-1][1:]
    if max(abs(v) for v in final) < 0.01:
        return 0.0
    still = max(t for t, *v in trans if max(abs(a) for a in v) < 0.01)
    # nor past the first turn: both curves must still read 0 at the new clip start
    yaws = [(0.0, 0.0)] + [(t, math.degrees(2 * math.atan2(qz, qw))) for t, _qx, _qy, qz, qw in motion[1] if t > 0]
    turning = [t for (t, a), (_t2, b) in zip(yaws, yaws[1:]) if abs(b) > 0.01]
    if turning:
        still = min(still, turning[0])
    end = min(t for t, *v in trans if max(abs(a - b) for a, b in zip(v, final)) < 0.01)
    return max(0.0, min(end - done_by, still))


def motion_annotations(motion, dur, shift=0.0):
    """AMR keys: `animmotion x y z` (root position since the clip start) and, when the clip turns,
    `animrotation <yaw degrees>`, every MOTION_STEP from 0 to the end. The curve is played `shift` s early:
    the key at clip time t is LSdF's value at t + shift."""
    trans, rots = motion
    trans = [(0.0, 0.0, 0.0, 0.0)] + [k for k in trans if k[0] > 0]
    steps = int(dur / MOTION_STEP + 1e-6)
    times = [round(i * MOTION_STEP, 4) for i in range(steps + 1)]
    if dur - times[-1] > 1e-3:
        times.append(dur)
    out = []
    for t in times:
        x, y, z = _lerp_keys(trans, t + shift)
        out.append((t, f'animmotion {x:.2f} {y:.2f} {z:.2f}'))
    yaws = [(t, math.degrees(2 * math.atan2(qz, qw))) for t, _qx, _qy, qz, qw in rots]
    if any(abs(a) > 0.01 for _t, a in yaws):
        keys = [(0.0, 0.0)] + [k for k in yaws if k[0] > 0]
        out += [(t, f'animrotation {_lerp_keys(keys, t + shift)[0]:.2f}') for t in times]
    return out


# ---------------------------------------------------------------------------------------- MCO conversion ----

def _time(anns, name):
    hits = [t for t, x in anns if x.lower() == name.lower()]
    return min(hits) if hits else None


def convert(blob, kind, src_index, n_attacks, n_powers, left_hits, label, motion=None):
    """Annotate one LSdF clip for MCO. kind 'A' (attack) or 'P' (power attack); src_index is its SkySA position;
    motion = its SkySA root motion (skysa_motion), written as AMR keys."""
    pf = hkx_annotate.Packfile(blob)
    dur = pf.duration()
    anns = pf.annotations()
    if any(x.lower().startswith(('animmotion', 'animrotation')) for _t, x in anns):
        raise AssertionError(f'{label}: already carries AMR keys')
    ws, we = _time(anns, 'SkySA_AttackWinstart'), _time(anns, 'SkySA_AttackWinEnd')
    hits = [t for t, x in anns if x.lower() == 'hitframe']
    all_hits = sorted(hits + [t for t in left_hits if t < dur])
    last_hit = all_hits[-1] if all_hits else (ws if ws is not None else (we - 0.3 if we is not None else dur / 2))
    new = []
    # Every attack and power attack gets a window (the combo loops; a power attack chains back in), opened soon
    # after its last hit: LSdF's own windows sat 0.34-0.54 s later and its tiers' last attacks had none.
    after = WIN_AFTER_HIT if kind == 'A' else POWER_WIN_AFTER_HIT
    w_open = last_hit + after
    if kind == 'A' and ws is not None:
        w_open = min(w_open, ws)
    w_close = min(max(we if we is not None else 0.0, w_open + MIN_WINDOW), dur - 0.05)
    if not (NEXT_POWER_AT < w_open < w_close):
        raise AssertionError(f'{label}: window {w_open:.3f}-{w_close:.3f} in a {dur:.3f} s clip')
    if kind == 'A':
        nxt = src_index + 1 if src_index < n_attacks else 1
        nxt_power = src_index + 1 if src_index + 1 <= n_powers else 1
        new += [(0.0, f'PIE.@SGVF|MCO_AttackSpeed|{SPEED_LIGHT}'),
                (NEXT_ATTACK_AT, f'PIE.@SGVI|MCO_nextattack|{nxt}'),
                (NEXT_POWER_AT, f'PIE.@SGVI|MCO_nextpowerattack|{nxt_power}')]
    else:
        new += [(FHFX_AT, 'PIE.$FHFX'), (0.0, f'PIE.@SGVF|MCO_AttackSpeed|{SPEED_POWER}'),
                (NEXT_ATTACK_AT, 'PIE.@SGVI|MCO_nextattack|1'), (NEXT_POWER_AT, 'PIE.@SGVI|MCO_nextpowerattack|1')]
    new += [(w_open, 'MCO_WinOpen'), (w_close, 'MCO_WinClose'),
            (w_open, 'MCO_PowerWinOpen'), (w_close, 'MCO_PowerWinClose'),
            (min(w_open + RECOVERY_AFTER_OPEN, w_close), 'MCO_Recovery')]
    for t in left_hits:
        if t < dur and not any(abs(t - h) < 0.03 for h in hits):
            new.append((t, 'HitFrame'))
    if motion:
        new += motion_annotations(motion, dur, motion_shift(motion, w_open) if STEP_DONE_BY_WINDOW else 0.0)
    pie = sorted(t for t, x in new + anns if x.startswith('PIE.'))
    if any(b - a < PIE_GAP - 1e-6 for a, b in zip(pie, pie[1:])):
        raise AssertionError(f'{label}: PIE tags closer than {PIE_GAP} s: {pie}')
    pf.add(new)
    out = pf.save()
    check = hkx_annotate.Packfile(out)
    have = check.annotations()
    for t, x in new:
        if not any(abs(t - a) < 1e-6 and x == b for a, b in have):
            raise AssertionError(f'{label}: {x} at {t} missing after write')
    if abs(check.duration() - dur) > 1e-6:
        raise AssertionError(f'{label}: duration changed')
    hkx_annotate.check_string_alignment(check, label)   # odd-offset texts arrive empty in game (2026-11-10 trace)
    return out


# --------------------------------------------------------------------------------------- OAR conditions ----

def c_type(value, left):
    return {'condition': 'IsEquippedType', 'requiredVersion': '1.0.0.0', 'Type': {'value': float(value)},
            'Left hand': left}


def c_or(conds):
    return conds[0] if len(conds) == 1 else {'condition': 'OR', 'requiredVersion': '1.0.0.0', 'Conditions': conds}


def c_and(conds, negated=False):
    c = {'condition': 'AND', 'requiredVersion': '1.0.0.0', 'Conditions': conds}
    if negated:
        c['negated'] = True
    return c


def c_av(av, comparison, value):
    return {'condition': 'CompareValues', 'requiredVersion': '1.0.0.0',
            'Value A': {'actorValue': av, 'actorValueType': 'Value'}, 'Comparison': comparison,
            'Value B': {'value': float(value)}}


BASE_CONDS = [
    {'condition': 'HasPerk', 'requiredVersion': '1.0.0.0',
     'Perk': {'pluginName': STANCE_PERK[0], 'formID': STANCE_PERK[1]}},
    {'condition': 'IsActorBase', 'requiredVersion': '1.0.0.0', 'Actor base': {'pluginName': 'Skyrim.esm', 'formID': '7'}},
]


def _runs(indices):
    idx = sorted(indices)
    out, start = [], idx[0]
    for a, b in zip(idx, idx[1:] + [None]):
        if b != a + 1:
            out.append((start, a))
            start = b
    return out


def band_cond(av, indices):
    if len(indices) == len(BANDS):
        return None
    parts = []
    for lo, hi in _runs(indices):
        c = []
        if lo > 0:
            c.append(c_av(av, '>=', EDGES[lo]))
        if hi < len(BANDS) - 1:
            c.append(c_av(av, '<', EDGES[hi + 1]))
        parts.append(c[0] if len(c) == 1 else c_and(c))
    return c_or(parts)


def factor(pairs):
    """{(a, b), ...} -> [(frozenset a's, frozenset b's)] rectangles covering it exactly."""
    by_a = {}
    for a, b in pairs:
        by_a.setdefault(a, set()).add(b)
    rows = {}
    for a, bs in by_a.items():
        rows.setdefault(frozenset(bs), set()).add(a)
    return sorted(((frozenset(a), bs) for bs, a in rows.items()), key=lambda r: (sorted(r[0]), sorted(r[1])))


def weapon_cond(pairs):
    """Two-handed rights are factored apart and never get a left-hand condition."""
    parts = []
    two = {p for p in pairs if p[0] in TWO_HANDED}
    for rights, lefts in factor(two) + factor(set(pairs) - two):
        c = [c_or([c_type(r, False) for r in sorted(rights)])]
        if not set(rights) <= set(TWO_HANDED):
            c.append(c_or([c_type(l, True) for l in sorted(lefts)]))
        parts.append(c[0] if len(c) == 1 else c_and(c))
    return c_or(parts)


def skill_cond(cells):
    parts = []
    for ohs, ths in factor(cells):
        c = [x for x in (band_cond(OH, ohs), band_cond(TH, ths)) if x]
        if not c:
            return None
        parts.append(c[0] if len(c) == 1 else c_and(c))
    return c_or(parts)


def describe(pairs):
    """Folder label for a set of weapon pairs (the exact rule is in the conditions)."""
    rights = sorted({r for r, _ in pairs})
    lefts = set(l for _, l in pairs)
    names = ' & '.join(dict.fromkeys(TYPE_NAME[r] for r in rights))
    if not set(rights) <= set(TWO_HANDED):
        if lefts <= {1, 2, 3, 4}:
            names = 'Dual ' + names
        elif lefts <= {8, 11, 18}:
            names += ' + Shield'
    return names


def tier_name(cells):
    """LSdF's progression bands, by the One-/Two-Handed cells a submod covers."""
    if all(a == 0 and b == 0 for a, b in cells):
        return 'Untrained'
    top = {max(a, b) for a, b in cells}
    return ' & '.join(('Untrained', 'Trained', 'Adept', 'Master')[t] for t in sorted(top))


# ----------------------------------------------------------------------------------------- For Honor Reforged ----

def enabled_mods():
    with open(os.path.join(PROFILE, 'modlist.txt'), encoding='utf-8') as fh:
        mods = [ln[1:].strip() for ln in fh if ln.startswith('+')]
    return list(reversed(mods))   # lowest priority first


def fhr_submods():
    """Every enabled third-person OAR submod whose config.json comes from FHR, with user.json overrides applied from
    whichever mod wins it in MO2."""
    files = {}
    for m in enabled_mods():
        oar = os.path.join(MODS, m, *OAR_REL)
        if not os.path.isdir(oar):
            continue
        for dp, _dn, fn in os.walk(oar):
            for f in fn:
                files[os.path.relpath(os.path.join(dp, f), oar).replace(os.sep, '/').lower()] = (m, os.path.join(dp, f))
    dirs = {}
    for rel, hit in files.items():
        d, _, f = rel.rpartition('/')
        dirs.setdefault(d, {})[f] = hit
    out = []
    for d, fs in dirs.items():
        if 'config.json' not in fs or fs['config.json'][0] != FHR_MOD:
            continue
        with open(fs['config.json'][1], encoding='utf-8-sig') as fh:
            cfg = json.load(fh)
        if 'priority' not in cfg:
            continue
        if 'user.json' in fs:
            with open(fs['user.json'][1], encoding='utf-8-sig') as fh:
                cfg.update({k: v for k, v in json.load(fh).items() if k in ('priority', 'disabled', 'conditions')})
        if cfg.get('disabled'):
            continue
        clips = {f[:-4] for f in fs if f.endswith('.hkx')}
        clips |= {k.rsplit('/_variants_', 1)[1] for k in dirs if k.startswith(d + '/_variants_')}
        out.append({'dir': d, 'conditions': cfg.get('conditions', []), 'clips': clips})
    return out


WEAPON_CONDS = {'IsEquippedType', 'IsEquippedHasKeyword', 'IsEquipped', 'IsEquippedShout', 'IsActorBase'}


def _distinguishing(conds):
    """True if a condition list has anything beyond weapon / actor-base checks (FHR's special triggers)."""
    for c in conds:
        n = c.get('condition')
        if n in ('AND', 'OR'):
            if _distinguishing(c.get('Conditions', [])):
                return True
        elif n not in WEAPON_CONDS:
            return True
    return False


def _player_excluded(conds):
    return any(c.get('condition') == 'IsActorBase' and c.get('negated')
               and str(c['Actor base'].get('formID')).lstrip('0').upper() == '7' for c in conds)


def _leaf(c, right, left):
    """True/False for a weapon or player leaf at one weapon pair, else None (unknown)."""
    n = c.get('condition')
    if n == 'IsEquippedType':
        if c.get('Left hand') and right in TWO_HANDED:
            return None          # what a two-hander reports for the left hand is not modelled
        return (left if c.get('Left hand') else right) == int(c['Type']['value'])
    if n == 'IsActorBase':
        base = c['Actor base']
        if base.get('pluginName', '').lower() == 'skyrim.esm' and str(base.get('formID')).lstrip('0').upper() == '7':
            return True
    return None


def simplify(c, pairs):
    """Partially evaluate an OAR condition over a set of weapon pairs: a leaf that is the same known value at every
    pair becomes that constant. Returns True, False or a (copied) condition that is exact for those pairs."""
    n = c.get('condition')
    neg = bool(c.get('negated'))
    if n in ('AND', 'OR'):
        kids = []
        for x in c.get('Conditions', []):
            v = simplify(x, pairs)
            if v is (n == 'OR'):        # OR with a True child, AND with a False child
                return (n == 'OR') != neg
            if isinstance(v, dict):     # the other constant is neutral: dropped
                kids.append(v)
        if not kids:
            return (n == 'AND') != neg
        if len(kids) == 1:
            kid = json.loads(json.dumps(kids[0]))
            if neg:
                kid['negated'] = not kid.get('negated', False)
                if not kid['negated']:
                    del kid['negated']
            return kid
        out = {'condition': n, 'requiredVersion': c.get('requiredVersion', '1.0.0.0'), 'Conditions': kids}
        if neg:
            out['negated'] = True
        return out
    vals = {_leaf(c, r, l) for r, l in pairs}
    if len(vals) == 1 and None not in vals:
        return vals.pop() != neg
    return json.loads(json.dumps(c))


def canonical(c):
    """Same meaning, one spelling: numbers as floats, no `"negated": false`, AND/OR children flattened and sorted."""
    if isinstance(c, dict):
        out = {k: canonical(v) for k, v in c.items() if not (k == 'negated' and v is False)}
        if out.get('condition') in ('AND', 'OR'):
            kids = []
            for k in out['Conditions']:
                if k.get('condition') == out['condition'] and not k.get('negated'):
                    kids.extend(k['Conditions'])     # (a AND (b AND c)) == (a AND b AND c)
                else:
                    kids.append(k)
            out['Conditions'] = sorted(kids, key=lambda k: json.dumps(k, sort_keys=True))
        return out
    if isinstance(c, list):
        return [canonical(x) for x in c]
    if isinstance(c, (int, float)) and not isinstance(c, bool):
        return float(c)
    return c


def fhr_negations(specials, pairs, clips):
    """NOT(<FHR special submod's conditions>) for each one that shares a clip and can be true at these pairs,
    simplified for these pairs, deduplicated, and without blocks a smaller one already implies
    (NOT(A) makes NOT(A AND B) redundant)."""
    blocks = {}
    for s in specials:
        if not s['clips'] & clips:
            continue
        v = simplify(c_and(s['conditions']), pairs)
        if v is False:
            continue
        if v is True:
            raise AssertionError(f'{s["dir"]} is always true for {sorted(pairs)}: nothing of LSdF would play')
        v = canonical(v)
        conj = v['Conditions'] if v.get('condition') == 'AND' and not v.get('negated') else [v]
        key = frozenset(json.dumps(k, sort_keys=True) for k in conj)
        blocks.setdefault(key, (s['dir'], v))
    keep = [k for k in blocks if not any(o < k for o in blocks)]
    out = []
    for key in sorted(keep, key=lambda k: blocks[k][0]):
        d, v = blocks[key]
        neg = json.loads(json.dumps(v))
        neg['negated'] = not neg.get('negated', False)
        if not neg['negated']:
            del neg['negated']
        out.append((d, neg))
    return out


# ------------------------------------------------------------------------------------------------- build ----

def main():
    hits = sorted(fnmatch.filter(os.listdir(DOWNLOADS), SOURCE_GLOB))
    if not hits:
        raise SystemExit(f'{SOURCE_GLOB} not in {DOWNLOADS}: download Le Sentiment du Fer SSE 1.01 (Nexus 50798)')
    src = Source(os.path.join(DOWNLOADS, hits[-1]))
    with open(src.path, 'rb') as fh:
        md5 = hashlib.md5(fh.read()).hexdigest()
    src.dar = {n: parse_dar(c) for n, (c, _) in src.folders.items() if c is not None}
    left_hits = dw_left_hits(src)
    motions = skysa_motion(src)

    digests = {}

    def digest(member):
        if member not in digests:
            digests[member] = hashlib.md5(src.zip.read(member)).hexdigest()
        return digests[member]

    pairs = [(r, 0) for r in TWO_HANDED] + [(r, l) for r in RIGHT_TYPES if r not in TWO_HANDED for l in LEFT_TYPES]
    cells = list(itertools.product(range(len(BANDS)), repeat=2))
    attack_plans, guard_plans = {}, {}
    for (r, l), (i, j) in itertools.product(pairs, cells):
        eff = effective(src, r, l, {OH: BANDS[i], TH: BANDS[j]})
        prefix = 'dw' if r in (1, 2, 3, 4) and l in (1, 2, 3, 4) else PREFIX[r]
        attacks, powers, k = [], [], 1
        while f'skysa_{prefix}{k}' in eff:
            folder, info = eff[f'skysa_{prefix}{k}']
            attacks.append((f'skysa_{prefix}{k}', folder, info.filename))
            k += 1
        k = 1
        while f'skysa_power{prefix}{k}' in eff:
            folder, info = eff[f'skysa_power{prefix}{k}']
            powers.append((f'skysa_power{prefix}{k}', folder, info.filename))
            k += 1
        stray = [n for n in eff if re.fullmatch(rf'skysa_(power)?{prefix}\d+', n)
                 and n not in {f'skysa_{prefix}{x}' for x in range(1, len(attacks) + 1)}
                 and n not in {f'skysa_power{prefix}{x}' for x in range(1, len(powers) + 1)}]
        if stray:
            raise AssertionError(f'{(r, l, i, j)}: non-contiguous {prefix} slots {stray}')
        if attacks or powers:
            # keyed by content, so byte-identical sets (LSdF's axe and mace clips) share one submod
            content = tuple((digest(m), tuple(left_hits.get(c, ()))) for c, _f, m in attacks), \
                tuple((digest(m), tuple(left_hits.get(c, ()))) for c, _f, m in powers)
            plan = attack_plans.setdefault(content, {'prefixes': set(), 'attacks': attacks, 'powers': powers,
                                                     'members': set()})
            plan['prefixes'].add(prefix)
            plan['members'].add(((r, l), (i, j)))
        guard = {}
        for name, (folder, info) in eff.items():
            if not GUARD.match(name):
                continue
            if folder == 'root' and name not in ('2hc_equip', '2hc_unequip', 'dw1hm1hmidle', 'dw_sprintforwardsword'):
                continue
            relevant = (name.startswith('1hm_') and r not in TWO_HANDED) or (name.startswith('h2h_') and r == 0) \
                or (name.startswith('2hm_') and r in TWO_HANDED) or (name.startswith('2hw_') and r in (6, 10)) \
                or (name.startswith('2hc_') and r == 5) or (name.startswith('shd_') and l in (8, 11, 18)) \
                or (name.startswith('dw') and prefix == 'dw')
            if relevant:
                guard[name] = info.filename
        if guard:
            guard_plans.setdefault(tuple(sorted(guard.items())), set()).add(((r, l), (i, j)))

    specials = [s for s in fhr_submods() if _distinguishing(s['conditions']) and not _player_excluded(s['conditions'])]
    if not specials:
        raise SystemExit(f'no For Honor Reforged submods found through {PROFILE}')

    if os.path.isdir(os.path.join(MODS, MOD)):
        shutil.rmtree(os.path.join(MODS, MOD))   # generated by this script only
    os.makedirs(OUT)
    with open(os.path.join(OUT, 'config.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump({'name': MOD, 'author': 'Zenderal (animations: Khonraad, Le Sentiment du Fer)',
                   'description': 'Le Sentiment du Fer (SkySA) converted to MCO as the High stance (F1); generated '
                                  'by src/LSdFHighStance/tools/01-build-lsdf-high-stance.py'}, fh, indent=4)

    def conditions_for(members):
        by_cells = {}
        for pair, cell in members:
            by_cells.setdefault(pair, set()).add(cell)
        groups = {}
        for pair, cs in by_cells.items():
            groups.setdefault(frozenset(cs), set()).add(pair)
        out = []
        for cs, prs in sorted(groups.items(), key=lambda g: sorted(g[1])):
            c = [weapon_cond(prs)]
            sk = skill_cond(cs)
            if sk:
                c.append(sk)
            out.append(c[0] if len(c) == 1 else c_and(c))
        return [c_or(out)], groups

    report, used_names, stats = [], set(), {'clips': 0, 'negations': 0}

    def folder_name(base):
        name, n = base, 2
        while name.lower() in used_names:
            name, n = f'{base} #{n}', n + 1
        used_names.add(name.lower())
        return name

    plans = sorted(attack_plans.values(), key=lambda p: (sorted(p['prefixes']), sorted(p['members'])))
    for idx, plan in enumerate(plans):
        attacks, powers, members = plan['attacks'], plan['powers'], plan['members']
        prefix = '/'.join(sorted(plan['prefixes']))
        conds, groups = conditions_for(members)
        pairs_all = {p for p, _ in members}
        tier = 'Untrained' if attacks and attacks[0][1] in ('root', 899) else \
            {2: 'Trained', 4: 'Adept', 5: 'Master'}.get(len(attacks), f'{len(attacks)} attacks')
        title = ' + '.join(describe(prs) for _cs, prs in sorted(groups.items(), key=lambda g: sorted(g[1])))
        name = folder_name(f'Attacks - {title} - {tier}'[:120])
        tdir = os.path.join(OUT, name)
        os.makedirs(tdir)
        clip_names = set()
        for slot in range(1, SLOTS + 1):
            for kind, seq, stem in (('A', attacks, 'mco_attack'), ('P', powers, 'mco_powerattack')):
                if not seq:
                    continue
                s = (slot - 1) % len(seq) + 1
                clip, _folder, member = seq[s - 1]
                if clip not in motions:
                    raise AssertionError(f'{name}/{stem}{slot}: no SkySA motion data for {clip}')
                blob = convert(src.zip.read(member), kind, s, len(attacks), len(powers), left_hits.get(clip, []),
                               f'{name}/{stem}{slot}', motions[clip])
                with open(os.path.join(tdir, f'{stem}{slot}.hkx'), 'wb') as fh:
                    fh.write(blob)
                clip_names.add(f'{stem}{slot}')
        neg = fhr_negations(specials, pairs_all, clip_names)
        stats['negations'] += len(neg)
        stats['clips'] += len(clip_names)
        origin = lambda seq: ', '.join(f'{f}/{c}' for c, f, _m in seq)  # noqa: E731
        config = {'name': name, 'description': f'LSdF {prefix}: attacks {origin(attacks)}; power attacks '
                  f'{origin(powers)}; steps aside for {len(neg)} For Honor Reforged submods',
                  'priority': PRIORITY_ATTACK + idx, 'conditions': BASE_CONDS + conds + [n for _, n in neg]}
        with open(os.path.join(tdir, 'config.json'), 'w', encoding='utf-8', newline='\n') as fh:
            json.dump(config, fh, indent=1)
        report.append(f'{name}: {len(attacks)}A/{len(powers)}P, {len(neg)} FHR exceptions')

    for idx, (guard, members) in enumerate(sorted(guard_plans.items(), key=lambda kv: sorted(kv[1]))):
        conds, groups = conditions_for(members)
        title = ' + '.join(describe(prs) for _cs, prs in sorted(groups.items(), key=lambda g: sorted(g[1])))
        name = folder_name(f'Guard - {title} - {tier_name({c for _p, c in members})}'[:120])
        tdir = os.path.join(OUT, name)
        os.makedirs(tdir)
        for clip, member in guard:
            with open(os.path.join(tdir, clip + '.hkx'), 'wb') as fh:
                fh.write(src.zip.read(member))
        stats['clips'] += len(guard)
        config = {'name': name, 'description': 'LSdF guard: ' + ', '.join(c for c, _ in guard),
                  'priority': PRIORITY_GUARD + idx, 'conditions': BASE_CONDS + conds}
        with open(os.path.join(tdir, 'config.json'), 'w', encoding='utf-8', newline='\n') as fh:
            json.dump(config, fh, indent=1)
        report.append(f'{name}: {len(guard)} clips')

    size = sum(os.path.getsize(os.path.join(dp, f)) for dp, _dn, fn in os.walk(os.path.join(MODS, MOD)) for f in fn)
    print(f'source {os.path.basename(src.path)} md5 {md5}')
    print(f'dual-wield left HitFrames from the SkySA patch: {left_hits}')
    print(f'{len(specials)} FHR special submods considered')
    print('\n'.join(report))
    print(f'{len(attack_plans)} attack + {len(guard_plans)} guard submods, {stats["clips"]} clips, '
          f'{stats["negations"]} FHR exceptions, {size / 1e6:.1f} MB -> {OUT}')


if __name__ == '__main__':
    main()
