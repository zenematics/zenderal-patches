"""Rebuild the `Zenderal - FHR First Person` MO2 mod: For Honor Reforged 2.4's directional attacks and parry in
first person, on the list's own first-person animations (SIGMA, SigmaJelly, JellyFish).

Why (arch-docs/patches/FHRFirstPerson.md has the evidence):
  - FHR 2.4 puts its mechanics inside its third-person clips as Payload Interpreter annotations
    (`PIE.$ParrySpell`, `$ParryKnockdown`, `$BackHeavy`, `$LeftLight`...; macros in FHR's
    `SKSE/PayloadInterpreter/Config/For Honor In Skyrim.ini`), gated by OAR on DMK's `DirecionalCycleMoveset`
    (right 3, back 5, left 7). First-person clips carry none of them, so nothing of FHR fires in first person.
  - Zenderal - MCO Directional Power Attacks (and Attack_MCO for forward) make every directional power attack send
    `attackPowerStartInPlace`, which the first-person graph routes only to the standing power attack.

What it builds, under `_1stperson/animations/OpenAnimationReplacer/Zenderal - FHR First Person/`:
  - Parry: back + light attack plays one of Enhanced 1stperson Parry Animation's three parry moves for the weapon
    type (its loose `*_blockhit*.hkx`, which SIGMA's block sets otherwise outrank), with $ParrySpell at 0.10 s
    (FHR's window) and $BackLight at 0.20 s, gated like FHR's back-light submods on the player cooldown 5F9, and off
    while parried (the riposte wins). One submod above
    everything (the clip does not depend on the submod that would have played). The graph's own `attackStop` trigger
    is timed from the clip's end, so the shorter clip still ends the attack.
  - For every enabled first-person OAR submod that replaces one of the files below, "twins": the same conditions plus
    the twin's own, priority + OFFSET (so twins keep the originals' order and sit above all of them), and copies of
    its clips with FHR's annotations added (hkx_annotate.py, binary, nothing else touched):
      light attacks  riposte (FHR's parried mark 82A/811 on the player) -> $BackLight at 0.05 s and $ParryKnockdown
                              0.133 s before contact: the hit FHR's perk turns into parry poise damage (it needs
                              BackLight 88A + 82A when the player's hit lands)
                     left/right (not while parried) -> $LeftLight / $RightLight at 0.10 s
      power attacks  the standing clip replaced by the submod's own left/right/back/forward clip;
                     left/right -> $LeftHeavy / $RightHeavy at 0.10 s; back -> $BackHeavy (guard break) at 0.10 s;
                     $FHFX at 0.20 s; forward -> no tags
    Timings are FHR's own: every directional tag sits at 0.10 s in all 171 of its sampled clips, the knockdowns
    most often 0.133 s before its HitFrame; a second tag moves TAG_GAP later (same-time PIE tags collapse).
  - "Vanilla" twins with the load order's winning loose/BSA clip, lowest of all twins, for when no OAR submod would
    have played (DAR sets such as Stances based animations for 1st person combat are not twinned).
  Direction = the key held (Keytrace.esp's held-key effects, pure direction), or moving that way with DMK reading
  that direction or 0 (cond_direction).

The clips come from the user's installed mods and are never committed.

Usage:  python 01-build-fhr-first-person.py [<modlist root>] [<profile>]     (default E:/Zenderal Ultra)
"""
import copy
import hashlib
import json
import os
import re
import shutil
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, 'src', 'SettingsApplier', 'tools', 'capture'))
import hkx_annotate  # noqa: E402
from bsa import lz4_frame  # noqa: E402

ROOT = sys.argv[1] if len(sys.argv) > 1 else 'E:/Zenderal'
PROFILE = os.path.join(ROOT, 'profiles', sys.argv[2] if len(sys.argv) > 2 else 'Ultra')
MODS = os.path.join(ROOT, 'mods')
BS = chr(92)

MOD = 'Zenderal - FHR First Person'
ANIM_REL = ['meshes', 'actors', 'character', '_1stperson', 'animations']
OAR_REL = ANIM_REL + ['OpenAnimationReplacer']
OUT = os.path.join(MODS, MOD, *OAR_REL, MOD)
GAME_BSAS = [os.path.join(ROOT, 'Stock Game', 'Data', b)
             for b in ('E - Update.bsa', 'E - Meshes.bsa', 'Skyrim - Animations.bsa')]

OFFSET = 1000000000      # twins = original priority + OFFSET; every first-person original is below it
INT_MAX = 2147483647

FHR_BALANCE = 'For Honor Balance Patch.esp'
KEYTRACE = 'Keytrace.esp'
REQUIRED_PLUGINS = ['For Honor in Skyrim.esp', FHR_BALANCE, 'Reforged Directional Combat.esp', KEYTRACE]
DMK_VAR = 'DirecionalCycleMoveset'
# name: (DMK value, OAR IsMovementDirection value, Keytrace.esp MGEF). DMK: FHR's own configs (right 3, back 5,
# left 7); forward 1 completes its clockwise eight-way numbering. OAR: floor(angle/90 deg + 0.5) + 1
# (Conditions.cpp). Keytrace: PaulMix's dTry Key Utils extend keeps ForwardMGEF 801 / LeftMGEF 802 / BackwardMGEF 803 /
# RightMGEF 804 on the player while that movement key is held.
DIRECTIONS = {'Forward': (1, 1, '801'), 'Right': (3, 2, '804'), 'Back': (5, 3, '803'), 'Left': (7, 4, '802')}
PERPENDICULAR = {'Forward': ('Left', 'Right'), 'Back': ('Left', 'Right'), 'Left': ('Forward', 'Back'),
                 'Right': ('Forward', 'Back')}

# Player light-attack clips of the first-person graph's AttackRight_State/AttackLeft_State (Pandora output
# `_1stperson/behaviors/1hm_behavior.hkx`, locomotion/staff/unarmed clips left out). `*intro` clips are left out
# too: two-handers play the intro first and switch to the main clip on its end-timed `attackRelease`, so tagging or
# replacing both would cast (and, for the parry, play) everything twice; one-handers' intros sit in the
# `1HM_AttackRightRoot_Player_OLD` branch, unreachable (the branch is picked by `iIsPlayer`).
LIGHT = ['1hm_attackright.hkx', '1hm_attackrightdiagonal.hkx', '1hm_attackleft.hkx', '1hm_attacklefttdiagonal.hkx',
         '2hm_attackright.hkx', '2hm_attackleft.hkx', '2hw_attackright.hkx', '2hw_attackleft.hkx',
         'sneak_1hmattack.hkx', 'sneak_2hmattack.hkx', 'sneak_2hwattack.hkx']
# The standing power attack (state AttackPowerInPlace) -> the clip each direction's own state would have played.
POWER = {
    '1hm_attackpower.hkx': {'Left': '1hm_attackpowerleft.hkx', 'Right': '1hm_attackpowerright.hkx',
                            'Back': '1hm_attackpowerbwd.hkx', 'Forward': '1hm_attackpowerfwd.hkx'},
    '1hm_sneakattackpower.hkx': {'Left': '1hm_sneakattackpowerleft.hkx', 'Right': '1hm_sneakattackpowerright.hkx',
                                 'Back': '1hm_sneakattackpowerback.hkx', 'Forward': '1hm_sneakattackpowerforward.hkx'},
    '2hm_attackpower.hkx': {'Left': '2hm_attackpowerleft.hkx', 'Right': '2hm_attackpowerright.hkx',
                            'Back': '2hm_attackpowerbwd.hkx', 'Forward': '2hm_attackpowerforward.hkx'},
    '2hw_attackpower.hkx': {'Left': '2hw_attackpowerleft.hkx', 'Right': '2hw_attackpowerright.hkx',
                            'Back': '2hw_attackpowerbwd.hkx', 'Forward': '2hw_attackpowerforward.hkx'},
}
HIT = 'hit'   # placeholder time: 0.133 s before the clip's first contact
# Two PIE tags at the same time reach the player's event sink as ONE event (ZenParryTrace, 2026-10-31: the parry's
# $BackLight + $ParrySpell at 0.10 s gave 36 $BackLight and not one $ParrySpell, so FHR's window never opened). FHR's
# own clips stack them at 0.10 s; here they sit TAG_GAP apart, the FHR-critical tag on FHR's time.
TAG_GAP = 0.1
TAGS = {
    ('Parry', 'Back'): [(0.1, 'PIE.$ParrySpell'), (0.2, 'PIE.$BackLight')],
    ('Riposte', None): [(0.05, 'PIE.$BackLight'), (HIT, 'PIE.$ParryKnockdown')],
    ('Light', 'Left'): [(0.1, 'PIE.$LeftLight')],
    ('Light', 'Right'): [(0.1, 'PIE.$RightLight')],
    ('Power', 'Left'): [(0.1, 'PIE.$LeftHeavy'), (0.2, 'PIE.$FHFX')],
    ('Power', 'Right'): [(0.1, 'PIE.$RightHeavy'), (0.2, 'PIE.$FHFX')],
    # FHR's back-power clips also carry `PIE.$StaggerKnockDown`, but 2.4's config comments that macro out (inert)
    ('Power', 'Back'): [(0.1, 'PIE.$BackHeavy'), (0.2, 'PIE.$FHFX')],
    ('Power', 'Forward'): [],
}
KNOCKDOWN_LEAD = 0.133   # FHR's most common gap between $ParryKnockdown and HitFrame
KNOCKDOWN_MIN = 0.15     # after the 0.10 s tags
SWING_TO_HIT = 0.1       # FHR clips: HitFrame ~0.1 s after weaponSwing, for clips with neither HitFrame nor Collision_Add
KNOCKDOWN_DEFAULT = 0.3  # FHR's most common absolute time, for clips with no contact annotation at all


def cond_dmk(value):
    return {'condition': 'CompareValues', 'requiredVersion': '1.0.0.0', 'Value A': {'value': float(value)},
            'Comparison': '==', 'Value B': {'graphVariable': DMK_VAR, 'graphVariableType': 'Int'}}


def cond_effect(form_id, negated=False, plugin=FHR_BALANCE):
    c = {'condition': 'HasMagicEffect', 'requiredVersion': '1.0.0.0',
         'Magic effect': {'pluginName': plugin, 'formID': form_id}, 'Active effects only': False}
    if negated:
        c['negated'] = True
    return c


def cond_direction(name):
    """That key held and neither perpendicular one (Keytrace; FHR's DMK test also counts diagonals as neutral), or
    actually moving that way with DMK reading that direction or 0. v1 was `DMK == N or (DMK == 0 and moving)`: in
    game an attack after the parry replayed the parry with S released, so DMK alone is no longer trusted."""
    dmk, move, key = DIRECTIONS[name]
    held = [cond_effect(key, plugin=KEYTRACE)] + \
        [cond_effect(DIRECTIONS[p][2], negated=True, plugin=KEYTRACE) for p in PERPENDICULAR[name]]
    moving = [{'condition': 'IsMovementDirection', 'requiredVersion': '1.0.0.0', 'Direction': {'value': float(move)}},
              {'condition': 'OR', 'requiredVersion': '1.0.0.0', 'Conditions': [cond_dmk(dmk), cond_dmk(0)]}]
    return {'condition': 'OR', 'requiredVersion': '1.0.0.0', 'Conditions': [
        {'condition': 'AND', 'requiredVersion': '1.0.0.0', 'Conditions': held},
        {'condition': 'AND', 'requiredVersion': '1.0.0.0', 'Conditions': moving}]}


# FHR's parried marks on the player: WeaponParryTrigger 82A / ShieldParryTrigger 811 (2 s, from the attacker's
# HitFrameTriggerSpell 803 when its hit lands inside the parry window).
PARRIED = {'condition': 'OR', 'requiredVersion': '1.0.0.0', 'Conditions': [cond_effect('82A'), cond_effect('811')]}
EXTRA = {
    # FHR's back-light (parry) submods also require the player's directional cooldown to be off (all 25 of them);
    # and while parried the next attack is the riposte, S held or not
    ('Parry', 'Back'): [cond_effect('5F9', negated=True), cond_effect('82A', negated=True),
                        cond_effect('811', negated=True)],
    ('Riposte', None): [PARRIED],
    ('Light', 'Left'): [cond_effect('82A', negated=True), cond_effect('811', negated=True)],
    ('Light', 'Right'): [cond_effect('82A', negated=True), cond_effect('811', negated=True)],
}

TWIN_KINDS = [('Riposte', None), ('Light', 'Left'), ('Light', 'Right')] + [('Power', d) for d in DIRECTIONS]

# Parry clips: Enhanced 1stperson Parry Animation (Nexus 20374) ships three first-person parry moves per weapon
# type as loose block-hit clips; the load order's winning loose copies are used, never a SIGMA OAR one.
PARRY_MOD = '1stperson Parry Animation'
PARRY_CLIPS = {'1hm': ['1hm_blockhit.hkx', '1hm_blockhita.hkx', '1hm_blockhitb.hkx'],
               '2hm': ['2hm_blockhit.hkx', '2hm_blockhita.hkx', '2hm_blockhitb.hkx'],
               '2hw': ['2hw_blockhit.hkx', '2hw_blockhita.hkx', '2hw_blockhitb.hkx']}
PARRY_PRIORITY = OFFSET + 900000000   # above every twin (max original 800000004 + OFFSET)


def family(light_file):
    for fam in PARRY_CLIPS:
        if light_file.startswith(fam) or light_file.startswith('sneak_' + fam):
            return fam
    raise SystemExit(f'{light_file}: no weapon family')


def label(kind, direction):
    return kind if direction is None else f'{direction} {kind}'


# --- load order --------------------------------------------------------------------------------------------------
def enabled(profile_file, prefix):
    return [ln[1:].strip() for ln in open(os.path.join(PROFILE, profile_file), encoding='utf-8')
            if ln.startswith(prefix)]


def ci_join(base, parts):
    cur = base
    for part in parts:
        if not os.path.isdir(cur):
            return None
        hit = [e for e in os.listdir(cur) if e.lower() == part.lower()]
        if not hit:
            return None
        cur = os.path.join(cur, hit[0])
    return cur


def sources():
    """(name, folder) in MO2 priority order, highest first; our own output excluded."""
    out = [('overwrite', os.path.join(ROOT, 'overwrite'))]
    return out + [(m, os.path.join(MODS, m)) for m in enabled('modlist.txt', '+') if m != MOD]


class Submod:
    def __init__(self, oar_mod, name):
        self.oar_mod, self.name = oar_mod, name
        self.files = {}      # lower name -> path (winning)
        self.variants = {}   # lower stem -> {lower variant file -> path}
        self.config = None   # (mo2 mod, path) of the effective config
        self.user = None
        self.mo2 = None

    def anim(self, name):
        """name -> ('file', path) | ('variants', {file: path}) | None. A _variants_ folder wins over a plain file."""
        stem = name[:-4]
        if stem in self.variants:
            return 'variants', self.variants[stem]
        if name in self.files:
            return 'file', self.files[name]
        return None


def collect():
    subs = {}
    for mo2, base in sources():
        oar = ci_join(base, OAR_REL)
        if not oar:
            continue
        for oar_mod in os.listdir(oar):
            mdir = os.path.join(oar, oar_mod)
            if not os.path.isdir(mdir):
                continue
            for sub in os.listdir(mdir):
                sdir = os.path.join(mdir, sub)
                if not os.path.isdir(sdir):
                    continue
                key = (oar_mod.lower(), sub.lower())
                s = subs.setdefault(key, Submod(oar_mod, sub))
                if s.mo2 is None:
                    s.mo2 = mo2
                for e in os.listdir(sdir):
                    p = os.path.join(sdir, e)
                    low = e.lower()
                    if os.path.isdir(p) and low.startswith('_variants_'):
                        v = s.variants.setdefault(low[len('_variants_'):], {})
                        for f in os.listdir(p):
                            if f.lower().endswith('.hkx'):
                                v.setdefault(f, os.path.join(p, f))
                    elif low.endswith('.hkx'):
                        s.files.setdefault(low, p)
                    elif low == 'user.json' and s.user is None:
                        s.user = (mo2, p)
                    elif low == 'config.json' and s.config is None:
                        s.config = (mo2, p)
    return subs


def effective_config(s):
    src = s.user or s.config
    if src is None:
        return None
    with open(src[1], encoding='utf-8-sig') as fh:
        return json.load(fh)


# --- vanilla clips -------------------------------------------------------------------------------------------------
class BsaIndex:
    """Seek-based BSA v105 reader: index read once, files read on demand (E - Meshes.bsa is 1.5 GB)."""

    def __init__(self, path):
        self.path = path
        with open(path, 'rb') as fh:
            head = fh.read(36)
            magic, ver, _fro, self.flags, fcount, filecount, tfnl, tfil, _ff = struct.unpack('<4sIIIIIIII', head)
            if magic != b'BSA\x00' or ver != 105:
                raise SystemExit(f'{path}: not a v105 BSA')
            size = 36 + 24 * fcount + tfnl + fcount + 16 * filecount + tfil
            fh.seek(0)
            d = fh.read(size)
        p = 36
        counts = []
        for _ in range(fcount):
            counts.append(struct.unpack_from('<QIIQ', d, p)[1])
            p += 24
        recs = []
        for c in counts:
            ln = d[p]
            folder = d[p + 1:p + ln].rstrip(b'\0').decode('latin1')
            p += 1 + ln
            for _ in range(c):
                _h, fsize, off = struct.unpack_from('<QII', d, p)
                p += 16
                recs.append((folder, fsize, off))
        names = d[p:p + tfil].split(b'\0')
        self.index = {(folder + BS + n.decode('latin1')).lower(): (fsize, off)
                      for (folder, fsize, off), n in zip(recs, names)}

    def read(self, want):
        if want not in self.index:
            return None
        size, off = self.index[want]
        comp = bool(self.flags & 4) ^ bool(size & 0x40000000)
        size &= 0x3FFFFFFF
        with open(self.path, 'rb') as fh:
            fh.seek(off)
            blob = fh.read(size)
        if self.flags & 0x100:
            ln = blob[0]
            blob = blob[1 + ln:]
        if not comp:
            return blob
        data = lz4_frame(blob[4:])
        if len(data) != struct.unpack_from('<I', blob, 0)[0]:
            raise SystemExit(f'{want}: bad size after LZ4')
        return data


class Vanilla:
    def __init__(self, tmp):
        self.tmp = tmp
        self.bsas = None
        self.srcs = sources()

    def resolve(self, name):
        """The load order's winning `_1stperson\\animations\\<name>`: loose file, else BSA. -> (path, origin)."""
        for mo2, base in self.srcs:
            p = ci_join(base, ANIM_REL + [name])
            if p and os.path.isfile(p):
                return p, mo2
        if self.bsas is None:
            self.bsas = [BsaIndex(b) for b in GAME_BSAS if os.path.getsize(b) > 1024]
        want = BS.join(ANIM_REL + [name]).lower()
        for b in self.bsas:
            blob = b.read(want)
            if blob is not None:
                out = os.path.join(self.tmp, name)
                with open(out, 'wb') as fh:
                    fh.write(blob)
                return out, os.path.basename(b.path)
        return None, None


# --- annotations ---------------------------------------------------------------------------------------------------
def contact_time(annotations):
    hits = [t for t, x in annotations if x.lower() == 'hitframe' or x.lower().startswith('collision_add')]
    if hits:
        return min(hits)
    swings = [t for t, x in annotations if x.lower() == 'weaponswing']
    if swings:
        return min(swings) + SWING_TO_HIT
    return None


def tags_for(path, kind, direction):
    duration, annotations = hkx_annotate.read(path)
    have = {x for _, x in annotations}
    pie_times = [t for t, x in annotations if x.startswith('PIE.')]
    out = []
    for t, text in TAGS[(kind, direction)]:
        if text in have:
            raise SystemExit(f'{path} already carries {text}')
        if t == HIT:
            c = contact_time(annotations)
            t = KNOCKDOWN_DEFAULT if c is None else max(KNOCKDOWN_MIN, c - KNOCKDOWN_LEAD)
        t = round(min(t, duration), 6)
        for other in pie_times + [o for o, _ in out]:
            if abs(other - t) < TAG_GAP - 1e-6:
                raise SystemExit(f'{path}: {text} at {t} is within {TAG_GAP} s of another PIE tag at {other}')
        out.append((t, text))
    return out


def write_clip(src, dst, kind, direction):
    tags = tags_for(src, kind, direction)
    if tags:
        hkx_annotate.annotate(src, dst, tags)
    else:
        shutil.copyfile(src, dst)
    return tags


# --- twins -----------------------------------------------------------------------------------------------------------
def safe(name):
    return re.sub(r'[<>:"/\\|?*]', '_', name).strip()


def twin_conditions(base, kind, direction):
    extra = [] if direction is None else [cond_direction(direction)]
    return copy.deepcopy(base) + extra + copy.deepcopy(EXTRA.get((kind, direction), []))


def plan(sub, kind, direction):
    """{target file: source file} this submod contributes to one twin."""
    if kind in ('Light', 'Riposte'):
        return {f: f for f in LIGHT if sub.anim(f)}
    return {target: by_dir[direction] for target, by_dir in POWER.items() if sub.anim(by_dir[direction])}


def variant_datas(cfg, sub, source_stem, folder, target_stem):
    """The original's replacementAnimDatas entry for a _variants_ folder, re-pointed at the twin's folder."""
    out = []
    for e in cfg.get('replacementAnimDatas', []) or []:
        path = e.get('path', '').lower().replace('/', BS)
        tail = BS.join([sub.oar_mod, sub.name, '_variants_' + source_stem]).lower()
        if path.endswith(tail):
            e2 = copy.deepcopy(e)
            e2['path'] = BS.join(['data'] + OAR_REL + [MOD, folder, '_variants_' + target_stem])
            out.append(e2)
    return out


def convert_annotations(cfg):
    """A submod with triggersFromAnnotationsOnly drops the graph's own triggers and takes the clip's annotations
    instead, but the player's first-person power-attack clip generators carry FLAG_DONT_CONVERT_ANNOTATIONS_TO_TRIGGERS
    (16), so their annotations never become events either: the power attack sent no attackStop and the 1P graph stayed
    in it until a camera switch (JellyFishFP DAGGER's FFPD/dw attack, ZenParryTrace 2026-11-12). Such a submod needs
    ignoreDontConvertAnnotationsToTriggersFlag, as JellyFish's own equip submods already set."""
    if cfg.get('triggersFromAnnotationsOnly') and not cfg.get('ignoreDontConvertAnnotationsToTriggersFlag'):
        cfg['ignoreDontConvertAnnotationsToTriggersFlag'] = True


def build_twin(cfg, sub, kind, direction, mapping, stats):
    folder = safe(f'{sub.oar_mod} {sub.name} - {label(kind, direction)}')
    tdir = os.path.join(OUT, folder)
    os.makedirs(tdir)
    twin = {k: copy.deepcopy(v) for k, v in cfg.items()
            if k not in ('name', 'description', 'priority', 'conditions', 'disabled', 'replacementAnimDatas')}
    twin['name'] = f"{cfg.get('name', sub.name)} - {label(kind, direction)} (FHR first person)"
    twin['description'] = (f'{sub.oar_mod}/{sub.name} ({sub.mo2}) with For Honor Reforged\'s '
                           f'{label(kind, direction).lower()} tags.')
    twin['priority'] = cfg['priority'] + OFFSET
    twin['replaceOnEcho'] = True
    convert_annotations(twin)
    twin['conditions'] = twin_conditions(cfg.get('conditions', []), kind, direction)
    datas = []
    for target, source in mapping.items():
        how, what = sub.anim(source)
        if how == 'file':
            stats['tags'].append(write_clip(what, os.path.join(tdir, target), kind, direction))
            stats['clips'] += 1
        else:
            vdir = os.path.join(tdir, '_variants_' + target[:-4])
            os.makedirs(vdir)
            for vname, vpath in what.items():
                stats['tags'].append(write_clip(vpath, os.path.join(vdir, vname), kind, direction))
                stats['clips'] += 1
            datas += variant_datas(cfg, sub, source[:-4], folder, target[:-4])
    if datas:
        twin['replacementAnimDatas'] = datas
    with open(os.path.join(tdir, 'config.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(twin, fh, indent=4)
    return folder


def build_vanilla(vanilla, kind, direction, stats):
    names = {f: f for f in LIGHT} if kind in ('Light', 'Riposte') else {t: d[direction] for t, d in POWER.items()}
    folder = safe(f'Vanilla - {label(kind, direction)}')
    tdir = os.path.join(OUT, folder)
    os.makedirs(tdir)
    origins = {}
    for target, source in names.items():
        path, origin = vanilla.resolve(source)
        if path is None:
            stats['missing'].append(source)
            continue
        stats['tags'].append(write_clip(path, os.path.join(tdir, target), kind, direction))
        stats['clips'] += 1
        origins[target] = origin
    config = {'name': f'Vanilla - {label(kind, direction)} (FHR first person)',
              'description': f'The load order\'s own first-person clips with For Honor Reforged\'s '
                             f'{label(kind, direction).lower()} tags, for when no OAR submod would have played.',
              'priority': OFFSET,
              'replaceOnEcho': True,
              'conditions': twin_conditions([], kind, direction)}
    with open(os.path.join(tdir, 'config.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(config, fh, indent=4)
    return folder, origins


def write_echo_override(cfg, sub):
    """An attack started while the previous one still blends out restarts ("echoes") the same clip generator, and OAR
    re-picks the replacement only if the submod playing has replaceOnEcho (ActiveClip::OnLoopOrEcho; default false):
    in game the parry kept replaying (v2) and a quick S + attack after a SIGMA swing stayed SIGMA's. So every submod
    a twin copies gets a user.json in this mod = its effective config verbatim + replaceOnEcho (OAR's user.json
    replaces config.json; RaySensePriority's pattern). Returns a note when skipped."""
    if cfg.get('replaceOnEcho') and (cfg.get('ignoreDontConvertAnnotationsToTriggersFlag')
                                     or not cfg.get('triggersFromAnnotationsOnly')):
        return None
    if sub.user is not None:
        return f'{sub.oar_mod}/{sub.name}: already has a user.json in {sub.user[0]}, replaceOnEcho not added'
    out = os.path.join(MODS, MOD, *OAR_REL, sub.oar_mod, sub.name)
    os.makedirs(out, exist_ok=True)
    override = copy.deepcopy(cfg)
    override['replaceOnEcho'] = True
    convert_annotations(override)
    with open(os.path.join(out, 'user.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(override, fh, indent=4)
    return None


def build_parry(vanilla, stats):
    """One submod: every light-attack file -> a _variants_ folder of the weapon type's three parry moves."""
    folder = 'Parry - Back Light'
    tdir = os.path.join(OUT, folder)
    os.makedirs(tdir)
    clips, origins = {}, set()
    for fam, names in PARRY_CLIPS.items():
        for name in names:
            path, origin = vanilla.resolve(name)
            if path is None or origin != PARRY_MOD:
                raise SystemExit(f'{name}: winning loose copy is {origin}, not {PARRY_MOD}')
            clips.setdefault(fam, []).append((name, path))
            origins.add(origin)
    for target in LIGHT:
        vdir = os.path.join(tdir, '_variants_' + target[:-4])
        os.makedirs(vdir)
        for name, path in clips[family(target)]:
            stats['tags'].append(write_clip(path, os.path.join(vdir, name), 'Parry', 'Back'))
            stats['clips'] += 1
    config = {'name': 'Parry - Back Light (FHR first person)',
              'description': "Back + light attack: one of Enhanced 1stperson Parry Animation's parry moves for the "
                             "weapon type, with For Honor Reforged's parry window. Your next attack while parried is "
                             'the riposte.',
              'priority': PARRY_PRIORITY,
              'replaceOnEcho': True,
              'conditions': twin_conditions([], 'Parry', 'Back')}
    with open(os.path.join(tdir, 'config.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(config, fh, indent=4)
    return folder, sorted(origins)


# --- checks ----------------------------------------------------------------------------------------------------------
def pie_macros():
    """Every `$Name` the load order's Payload Interpreter configs define."""
    seen, names = set(), set()
    for _mo2, base in sources():
        cfg = ci_join(base, ['SKSE', 'PayloadInterpreter', 'Config'])
        if not cfg:
            continue
        for f in os.listdir(cfg):
            if f.lower() in seen or not f.lower().endswith('.ini'):
                continue
            seen.add(f.lower())
            for ln in open(os.path.join(cfg, f), encoding='utf-8', errors='replace'):
                m = re.match(r'\s*(\$[A-Za-z0-9_]+)\s*=', ln)
                if m:
                    names.add(m.group(1))
    return names


def main():
    plugins = enabled('plugins.txt', '*')
    for p in REQUIRED_PLUGINS:
        if p not in plugins:
            raise SystemExit(f'{p} is not enabled in {PROFILE}')
    macros = pie_macros()
    for tags in TAGS.values():
        for _, text in tags:
            if text[len('PIE.'):] not in macros:
                raise SystemExit(f'{text}: no Payload Interpreter config defines it')

    subs = collect()
    if os.path.isdir(os.path.join(MODS, MOD)):
        shutil.rmtree(os.path.join(MODS, MOD))   # generated by this script only
    os.makedirs(OUT)
    with open(os.path.join(OUT, 'config.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump({'name': MOD, 'author': 'Zenderal',
                   'description': "For Honor Reforged's directional attacks and parry in first person: twins of "
                                  'the first-person attack submods with FHR\'s Payload Interpreter tags, per '
                                  'direction.'}, fh, indent=4)

    stats = {'clips': 0, 'tags': [], 'missing': []}
    twins, skipped = [], []
    echo_overrides = 0
    for key in sorted(subs):
        sub = subs[key]
        work = {(k, d): plan(sub, k, d) for k, d in TWIN_KINDS}
        if not any(work.values()):
            continue
        cfg = effective_config(sub)
        if cfg is None:
            skipped.append(f'{sub.oar_mod}/{sub.name}: no config.json')
            continue
        if cfg.get('disabled'):
            skipped.append(f'{sub.oar_mod}/{sub.name}: disabled')
            continue
        if 'overrideAnimationsFolder' in cfg:
            raise SystemExit(f'{sub.oar_mod}/{sub.name}: overrideAnimationsFolder is not handled')
        prio = cfg.get('priority')
        if not isinstance(prio, int) or not 0 < prio < OFFSET or prio + OFFSET > INT_MAX:
            raise SystemExit(f'{sub.oar_mod}/{sub.name}: priority {prio} outside 1..{OFFSET - 1}')
        for (kind, direction), mapping in work.items():
            if mapping:
                twins.append((build_twin(cfg, sub, kind, direction, mapping, stats), sub.mo2, prio + OFFSET,
                              len(mapping)))
        note = write_echo_override(cfg, sub)
        if note:
            skipped.append(note)
        else:
            echo_overrides += 1

    vanilla_tmp = os.path.join(os.environ.get('TEMP', HERE), 'zen_fhr1p_vanilla')
    os.makedirs(vanilla_tmp, exist_ok=True)
    vanilla = Vanilla(vanilla_tmp)
    for kind, direction in TWIN_KINDS:
        folder, origins = build_vanilla(vanilla, kind, direction, stats)
        print(f'{folder}: {len(origins)} clips <- ' + ', '.join(sorted(set(origins.values()))))
    folder, origins = build_parry(vanilla, stats)
    print(f'{folder}: {len(LIGHT)} files x 3 parry moves <- ' + ', '.join(origins))
    shutil.rmtree(vanilla_tmp)

    by_mod = {}
    for folder, mo2, prio, n in twins:
        by_mod.setdefault(mo2, []).append(folder)
    for mo2, folders in sorted(by_mod.items()):
        print(f'{mo2}: {len(folders)} twins')
    for s in skipped:
        print('skipped', s)
    if stats['missing']:
        print('no vanilla clip for:', ', '.join(sorted(set(stats['missing']))))
    times = {}
    for tags in stats['tags']:
        for t, text in tags:
            times.setdefault(text, []).append(t)
    for text, ts in sorted(times.items()):
        print(f'  {text}: {len(ts)} clips, {min(ts):.3f}-{max(ts):.3f} s')
    digest = hashlib.sha1()
    for dp, _dn, fn in sorted(os.walk(os.path.join(MODS, MOD))):
        for f in sorted(fn):
            with open(os.path.join(dp, f), 'rb') as fh:
                digest.update(f.encode() + fh.read())
    print(f'{len(twins)} twins + {len(TWIN_KINDS)} vanilla submods + parry, {stats["clips"]} clips -> {OUT}')
    print(f'{echo_overrides} replaceOnEcho user.json overrides of the twinned submods')
    print(f'content sha1 {digest.hexdigest()[:12]}')


if __name__ == '__main__':
    main()
