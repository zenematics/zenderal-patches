"""Rebuild `Zenderal - Stance Overlays`: OAR user.json files only, over the UNTOUCHED High (F1) / Mid (F2) / Low (F3)
stance sources that 00-install-sources.py installed as their own MO2 mods. No animation is copied or changed.

An OAR user.json beside a submod's config.json (or in a legacy DAR folder) replaces its settings. Every submod
folder of every source gets one:
  - used by a stance: priority in that stance's band (layer order), conditions = the stance perk + the player + the
    weapon pairs it serves; attack-bearing folders also carry NOT(<FHR special submod>) for each For Honor Reforged
    special submod that shares a clip (LSdFHighStance's fhr_negations), so FHR's directional attacks, parry,
    follow-ups, knockdowns and combo layers keep playing FHR's own clips with their mechanics;
  - not used (NPC folders, Keytrace direction folders, Vanargand's Sprint): disabled, with
    conditions that can never be true as a second lock. So nothing of these mods reaches NPCs or other stances.

Which folder serves which weapon pair is decided as in the earlier copy build: each source's own conditions are
evaluated for the player with the weapon drawn, in combat and out of it (race/actor-base tests dropped, Keytrace
effects and sneaking false). The attack set of a pair is the WHOLE set of its highest live layer with attack clips
(an attack folder is switched on only where it wins, so sets never mix); guard-only folders are on wherever they are
live, and OAR's per-clip priority (layer order) picks the guard clip. A guard folder live only out of (or only in)
combat keeps that as an IsInCombat gate: the race packs' relaxed weapon-drawn locomotion.

Usage:  python 01-build-stance-overlays.py [<modlist root>] [<profile>]
"""
import json
import os
import re
import shutil
import sys

import stance_sources as ss

lsdf = ss.lsdf
MODS = lsdf.MODS
TWO = lsdf.TWO_HANDED
PAIRS = [(r, 0) for r in TWO] + [(r, l) for r in lsdf.RIGHT_TYPES if r not in TWO for l in lsdf.LEFT_TYPES]
ATTACK = re.compile(r'^mco_(power)?attack\d+$')
GUARD = re.compile(r'^((1hm|2hm|2hw|h2h|shd|2hc)_(idle|turn\w*|walk\w*|run\w*|equip|unequip|locomotionpose)'
                   r'|dw1hm1hmidle|dw_shieldadjustment)$')
NEVER = [lsdf.BASE_CONDS[1], dict(lsdf.BASE_CONDS[1], negated=True)]   # player AND NOT player
# A guard folder its author shows only in or only out of combat keeps that split (2026-11-10: the race packs' relaxed
# weapon-drawn locomotion, Nordic 31002 / Desert 32003 / Imperium 33002, was disabled, so running with a weapon out
# and no enemy played the combat guard jog - Nordic's: arms locked, hand swing 11.8 vs 30.8 relaxed)
IN_COMBAT = {'condition': 'IsInCombat', 'requiredVersion': '1.0.0.0'}
OUT_OF_COMBAT = dict(IN_COMBAT, negated=True)
# Weapon drawn (2026-11-12, player report: in High/Mid, sprinting with the weapon sheathed held the right hand at an
# angle). The race packs ship mt_sprintforward - the SHEATHED sprint - beside their drawn sprints, and OAR's
# IsEquippedType counts a sheathed weapon, so a gate of perk + player + weapon pair played the pack's sword sprint
# without a sword. Nordic and Desert require IsWeaponDrawn in their own conditions (dropped by the first build);
# Imperium does not. Kept from the author, and forced on any folder holding a clip the sheathed state plays.
IS_DRAWN = {'condition': 'IsWeaponDrawn', 'requiredVersion': '1.0.0.0'}
DRAWN_ONLY_MT = {'mt_sprintforwardsword'}          # the only mt_ (movement-type) clip that plays with a weapon out


# Not sprinting (2026-11-12, curator: "the sprinting for F1 F2 and F3 is not correct, it's the wrong sprint
# animations"). The race packs' guard folders carry their NPC sprints (mt_/1hm_/2hm_/2hw_/dw_sprintforwardsword,
# mt_sprintforward) under the same clip names as the list's sprint mods (Dynamic Sprint, JellyFish one handed Sprint,
# Smooth Moveset, CATA, priorities < 1e9), and the stance band (1.5e9) outranked them all. OAR conditions are per
# folder, so a folder holding a sprint clip is switched off while the player sprints: the stances keep their guard,
# walks and runs, and every stance sprints like F4.
NOT_SPRINTING = {'condition': 'IsSprinting', 'requiredVersion': '1.0.0.0', 'negated': True}
# ... but NOT IsSprinting alone cannot win the sprint's FIRST frame (curator, the same day: "it's not" the same as F4):
# the engine sets the sprint flag only after the sprint clip has started, which is why Dynamic Sprint's own "Per-Sprint"
# folders (the sprint start) are gated on NOT IsSprinting and interruptible. So the list's sprint-only submods (every
# enabled third-person OAR submod outside the stances whose clips are all sprint clips, not sprint attacks: Dynamic Sprint,
# JellyFish one handed Sprint, Smooth Moveset's sprint folders, Goetia's staff sprints, ...; or a submod that itself
# requires IsSprinting) are lifted above every
# stance band by a user.json with only their priority changed, their own order kept (rank-mapped). They hold nothing
# but sprints, so nothing else moves; F4 keeps the same winner wherever no mixed folder ranked above a lifted one
# (02 lists those inversions).
SPRINT_LIFT_BASE = 1_600_000_000            # above the stance bands (<= 1,500,030,090), below RaySense/UNDERDOG
SPRINT_CLIP = re.compile(r'^(?!.*attack).*sprint')   # sprint locomotion clips; never sprint attacks (FHR/MCO)
# Mixed submods lifted anyway, each checked by hand: Dynamic Sprint's spell + shield sprint start ranks above its own
# lifted 'Spell Shield Sprint'; its one other clip, shd_blockidle with a spell in the right hand and a shield, has no
# other provider above it (the stances' packs need a melee right hand)
ALSO_LIFT = {'Dynamic Sprint/Dynamic Sprint/Spell Shield Per-Sprint'}
# (2026-11-12: lifting Smooth Moveset's '<weapon> move' stop-settle idles too was tried for the looping lantern arm
# after a sprint and backed out the same hour: 02 showed it reorders Smooth's own idle start/loop chain in F4, 79
# overlaps. See the doc's postmortem.)
SKIP_MODS = {ss.OVERLAY_MOD, 'Zenderal - Le Sentiment du Fer High Stance'} | {v['mod'] for v in ss.SOURCES.values()}


def oar_submods():
    """Every enabled third-person OAR submod outside the stances, read through MO2's merged view (CATA's addons put
    clips into submods whose config.json is in another mod): winning config.json + user.json from any other enabled
    mod, clips from every mod. [{'mod', 'rel', 'cfg', 'clips', 'lift'}] ('mod' = the config.json's mod).
    lift = it outranks the stances (sprint-only)."""
    mods = lsdf.enabled_mods()                 # lowest priority first
    dirs = {}                                  # rel dir (lower) -> {'rel', 'clips', 'config': (mod, path), 'user'}
    for m in mods:
        if m in SKIP_MODS:
            continue
        oar = _find_dir(os.path.join(MODS, m), ss.OAR)
        if not oar:
            continue
        for dp, _dn, fn in os.walk(oar):
            if '_1stperson' in dp.lower():
                continue
            sub = os.path.relpath(dp, oar).replace(os.sep, '/')
            d = dirs.setdefault(sub.lower(), {'rel': f'{ss.OAR}/{sub}', 'clips': set(), 'config': None, 'user': None})
            d['clips'] |= {f[:-4].lower() for f in fn if f.lower().endswith('.hkx')}
            if 'config.json' in fn:
                d['config'] = (m, os.path.join(dp, 'config.json'))
            if 'user.json' in fn:
                d['user'] = os.path.join(dp, 'user.json')
    owned = {k: set(d['clips']) for k, d in dirs.items() if d['config']}
    for k, d in dirs.items():                  # male/female (and other non-submod) subfolders -> nearest submod
        if d['config']:
            continue
        parts = k.split('/')
        for i in range(len(parts) - 1, 0, -1):
            parent = '/'.join(parts[:i])
            if parent in owned:
                owned[parent] |= d['clips']
                break
    out = []
    for key, clips in owned.items():
        d = dirs[key]
        with open(d['config'][1], encoding='utf-8-sig') as fh:
            cfg = json.load(fh)
        if 'priority' not in cfg:
            continue                           # a replacer mod's root config
        if d['user']:
            with open(d['user'], encoding='utf-8-sig') as fh:
                cfg = dict(cfg, **json.load(fh))
        if cfg.get('disabled') or not clips:
            continue
        f = {'mod': d['config'][0], 'rel': d['rel'], 'cfg': cfg, 'clips': clips}
        sprinting = any(SPRINT_CLIP.search(c) for c in clips) and (
            # every clip a sprint, or the submod itself requires IsSprinting (Dynamic Sprint's spell folders: their
            # 1hm_idle / shd_blockidle / mag_runforward only ever play while sprinting)
            all(SPRINT_CLIP.search(c) for c in clips)
            or any(c['condition'] == 'IsSprinting' and not c.get('negated') for c in cfg['conditions'])
            or f'{f["mod"]}/{f["rel"].split(ss.OAR + "/")[1]}' in ALSO_LIFT)
        f['lift'] = sprinting
        out.append(f)
    return out


# Smooth Moveset's idle chain is a state machine (2026-11-12, curator's video: the lantern arm looping every 1.667 s
# after a sprint in F1; "we've had a ton of loop animation issues with Smooth Moveset"). Its states (start 801, loop
# 802, move 803, combat 804 ...) are switched by Dynamic Animation Casting on events that sit in Smooth's own
# 1hm_idle / 2hm_idle / dw1hm1hmidle ... clips (Smooth_loop, Smooth_Stop, Smooth_Combat). Where a stance's guard
# outranks those clips the events never fire, and the clips of the same submod the stance does not replace
# (Smooth's left-arm MLh_Idle) loop the state they were left in: here the 1.667 s move-stop settle. So in each stance,
# at the weapon pairs where a stance folder replaces one of a Smooth submod's clips, that submod is switched off:
# its winning settings + NOT(stance perk AND those pairs). F4 (no stance perk) is untouched.
SMOOTH_ESP = 'smooth moveset.esp'


def _tests_smooth(conds):
    for c in conds:
        if c['condition'] == 'HasMagicEffect' and c.get('Magic effect', {}).get('pluginName', '').lower() == SMOOTH_ESP:
            return True
        if _tests_smooth(c.get('Conditions', [])):
            return True
    return False


def smooth_chain_blocks(f, owned):
    """NOT(perk AND pairs) blocks for a Smooth state-machine submod, one per stance that replaces one of its
    non-sprint clips; [] for any other submod."""
    if not _tests_smooth(f['cfg']['conditions']):
        return []
    mine = {c for c in f['clips'] if not SPRINT_CLIP.search(c)}
    by_perk = {}
    for perk, clips, pairs in owned:
        if mine & clips:
            key = json.dumps(perk, sort_keys=True)
            by_perk.setdefault(key, (perk, set()))[1].update(pairs)
    return [{'condition': 'AND', 'requiredVersion': '1.0.0.0', 'negated': True,
             'Conditions': [perk, lsdf.weapon_cond(pairs)]} for perk, pairs in by_perk.values()]


def lifted_priorities(submods, stance_clips):
    """{rel: new priority} for the lifted submods, their order (and ties) kept. All of them, not only those sharing
    a clip with a stance folder: leaving some behind lets the lifted ones jump over them in F4 (Dynamic Sprint's
    dual-spell sprints, 2026-11-12). stance_clips is kept for the report."""
    lift = [f for f in submods if f['lift']]
    ranks = {p: i for i, p in enumerate(sorted({f['cfg']['priority'] for f in lift}))}
    return {f['rel']: SPRINT_LIFT_BASE + ranks[f['cfg']['priority']] for f in lift}


def has_sprint(f):
    return any('sprint' in c for c in f['clips'])


def needs_drawn(f):
    """The folder's author requires the weapon drawn, or it holds a clip the sheathed state also plays."""
    if any(c.startswith('mt_') and c not in DRAWN_ONLY_MT for c in f['clips']):
        return True
    if f['kind'] == 'dar':
        return any(len(g) == 1 and g[0][1] == 'isweapondrawn' and not g[0][0] for g in f['groups'])
    return any(c['condition'] == 'IsWeaponDrawn' and not c.get('negated') for c in f['config']['conditions'])


def _find_dir(base, rel):
    """Case-insensitive path under base, or None."""
    cur = base
    for part in rel.split('/'):
        if not os.path.isdir(cur):
            return None
        hit = [d for d in os.listdir(cur) if d.lower() == part.lower()]
        if not hit:
            return None
        cur = os.path.join(cur, hit[0])
    return cur


def _dar_leaf(neg, fn, args, right, left, combat=True):
    if fn in ('isactorbase', 'israce'):
        return True
    if fn == 'isequippedrighttype':
        v = right == int(args[0])
    elif fn == 'isequippedlefttype':
        v = left == int(args[0])
    elif fn == 'isincombat':
        v = combat
    elif fn == 'isweapondrawn':
        v = True
    elif fn in ('issneaking', 'hasmagiceffect', 'random'):
        v = False
    else:
        raise ValueError(f'unknown DAR function {fn}')
    return v != neg


def _oar_eval(c, right, left, effects=False, combat=True):
    n = c['condition']
    neg = bool(c.get('negated'))
    if n in ('AND', 'OR'):
        vals = [_oar_eval(x, right, left, effects, combat) for x in c.get('Conditions', [])]
        v = all(vals) if n == 'AND' else any(vals)
    elif n == 'IsEquippedType':
        v = (left if c.get('Left hand') else right) == int(c['Type']['value'])
    elif n == 'IsActorBase':
        v = True
    elif n in ('IsSneaking', 'IsSprinting'):
        v = False
    elif n == 'IsInCombat':
        v = combat
    elif n == 'IsWeaponDrawn':
        v = True
    elif n == 'HasMagicEffect':
        v = effects                      # Keytrace direction effects: never seen in game; an addon's gate (see main)
    else:
        raise ValueError(f'unknown OAR condition {n}')
    return v != neg


def _clips(folder):
    out = set()
    for dp, _dn, fn in os.walk(folder):
        out |= {f[:-4].lower() for f in fn if f.lower().endswith('.hkx')}
    return out


def source_folders(key):
    """Every submod folder of an installed source: [{'rel', 'kind', 'order', 'clips', 'config'|'dar', ...}]."""
    src = ss.SOURCES[key]
    mod_dir = os.path.join(MODS, src['mod'])
    if not os.path.isdir(mod_dir):
        raise SystemExit(f'{src["mod"]} is not installed: run 00-install-sources.py')
    out = []
    dar = _find_dir(mod_dir, ss.DAR)
    if dar:
        for d in os.listdir(dar):
            p = os.path.join(dar, d)
            if not (d.isdigit() and os.path.isdir(p)):
                continue
            cond = os.path.join(p, '_conditions.txt')
            with open(cond, encoding='utf-8', errors='replace') as fh:
                text = fh.read()
            out.append({'source': key, 'kind': 'dar', 'id': int(d), 'order': int(d), 'path': p,
                        'rel': f'{ss.DAR}/{d}', 'clips': _clips(p), 'groups': lsdf.parse_dar(text)})
    oar = _find_dir(mod_dir, ss.OAR)
    if oar:
        for dp, _dn, fn in os.walk(oar):
            if 'config.json' not in fn:
                continue
            with open(os.path.join(dp, 'config.json'), encoding='utf-8-sig') as fh:
                cfg = json.load(fh)
            if 'priority' not in cfg:
                continue                     # replacer mod's root config
            sub = os.path.relpath(dp, oar).replace(os.sep, '/')
            out.append({'source': key, 'kind': 'oar', 'id': sub, 'order': cfg['priority'], 'path': dp,
                        'rel': f'{ss.OAR}/{sub}', 'clips': _clips(dp), 'config': cfg})
    for f in out:
        if os.path.exists(os.path.join(f['path'], 'user.json')):
            raise SystemExit(f'{f["path"]} already has a user.json: it would be shadowed')
    return sorted(out, key=lambda f: f['order'])


def live(folder, rights, r, l, effects=False, combat=True):
    if rights is not None and r not in rights:
        return False
    if folder['kind'] == 'dar':
        return all(any(_dar_leaf(*c, r, l, combat) for c in grp) for grp in folder['groups'])
    return all(_oar_eval(c, r, l, effects, combat) for c in folder['config']['conditions'])


def _guard_only(f):
    return not any(ATTACK.match(c) for c in f['clips']) and any(GUARD.match(c) for c in f['clips'])


def _dmk(value):
    return {'condition': 'CompareValues', 'requiredVersion': '1.0.0.0', 'Value A': {'value': float(value)},
            'Comparison': '==', 'Value B': {'graphVariable': 'DirecionalCycleMoveset', 'graphVariableType': 'Int'}}


def direction_cond(name):
    """Moving that way (OAR IsMovementDirection) with DMK reading that direction or 0: FHRFirstPerson's test (its
    Keytrace branch is dead in this list). FHR's own directional submods need DMK 3/5/7, so this never meets them."""
    dmk, move = ss.ADDON_DIRECTIONS[name]
    return {'condition': 'AND', 'requiredVersion': '1.0.0.0', 'Conditions': [
        {'condition': 'IsMovementDirection', 'requiredVersion': '1.0.0.0', 'Direction': {'value': float(move)}},
        {'condition': 'OR', 'requiredVersion': '1.0.0.0', 'Conditions': [_dmk(dmk), _dmk(0)]}]}


def main():
    specials = [s for s in lsdf.fhr_submods()
                if lsdf._distinguishing(s['conditions']) and not lsdf._player_excluded(s['conditions'])]
    if not specials:
        raise SystemExit(f'no For Honor Reforged submods found through {lsdf.PROFILE}')
    out_mod = os.path.join(MODS, ss.OVERLAY_MOD)
    if os.path.isdir(out_mod):
        shutil.rmtree(out_mod)          # generated by this script only
    report = [f'{len(specials)} FHR special submods considered']
    stance_clips = set()                  # every clip an enabled stance folder replaces
    owned = []                            # (stance perk condition, clips, weapon pairs) per enabled stance folder
    written = 0
    for st in ss.STANCES:
        perk = {'condition': 'HasPerk', 'requiredVersion': '1.0.0.0',
                'Perk': {'pluginName': ss.STANCES_ESP, 'formID': st['perk']}}
        layers = []                       # (folder, rights), low -> high
        addons = []                       # (folder, rights, direction)
        unused = []
        for spec in st['layers']:
            key, kind, pick, rights = spec[:4]
            extra = spec[4] if len(spec) > 4 else {}
            for f in source_folders(key):
                if f['kind'] == 'oar' and f['id'] in extra:
                    addons.append((f, rights, extra[f['id']]))
                    continue
                chosen = f['kind'] == kind and (pick is None or f['id'] in pick)
                (layers.append((f, rights)) if chosen else unused.append(f))
        active = {id(f): set() for f, _r in layers}
        guard_ooc = {id(f): set() for f, _r in layers}     # guard folders' pairs out of combat
        gaps = []
        winners = {}
        for r, l in PAIRS:
            on = [(f, rights) for f, rights in layers if live(f, rights, r, l)]
            winner = None
            for f, _rights in on:
                if any(ATTACK.match(c) for c in f['clips']):
                    winner = f
            winners[(r, l)] = winner
            if winner is None:
                gaps.append((r, l))
            for f, _rights in on:
                has_attack = any(ATTACK.match(c) for c in f['clips'])
                if (has_attack and f is winner) or (not has_attack and any(GUARD.match(c) for c in f['clips'])):
                    active[id(f)].add((r, l))
            for f, rights in layers:
                if _guard_only(f) and live(f, rights, r, l, combat=False):
                    guard_ooc[id(f)].add((r, l))
        report.append(f'{st["name"]} stance ({st["key"]}):')
        for idx, (f, _rights) in enumerate(layers):
            pairs = active[id(f)]
            gate, when = [], ''
            if _guard_only(f) and pairs != guard_ooc[id(f)]:
                if pairs and guard_ooc[id(f)]:
                    raise SystemExit(f'{f["rel"]}: guard folder live at different weapon pairs in and out of combat')
                gate, when = ([OUT_OF_COMBAT], ' (out of combat)') if guard_ooc[id(f)] else ([IN_COMBAT], ' (in combat)')
                pairs = pairs or guard_ooc[id(f)]
            if not pairs:
                unused.append(f)
                continue
            conds = [perk, lsdf.BASE_CONDS[1], lsdf.weapon_cond(pairs)] + gate
            if needs_drawn(f):
                conds.append(IS_DRAWN)
                when += ', weapon drawn'
            if has_sprint(f):
                if any(ATTACK.match(c) for c in f['clips']):
                    raise SystemExit(f'{f["rel"]}: attack folder with sprint clips - NOT IsSprinting would cut its attacks')
                conds.append(NOT_SPRINTING)
                when += ', not sprinting'
            neg = []
            if any(ATTACK.match(c) for c in f['clips']):
                neg = lsdf.fhr_negations(specials, pairs, f['clips'])
                conds += [n for _d, n in neg]
            prio = st['priority'] + 10 * idx
            write_user(f, prio, conds, False)
            stance_clips |= f['clips']
            owned.append((perk, f['clips'], set(pairs)))
            written += 1
            title = ' + '.join(lsdf.describe(p) for p in _groups(pairs))
            kind = 'attacks' if neg or any(ATTACK.match(c) for c in f['clips']) else 'guard'
            report.append(f'  {ss.SOURCES[f["source"]]["mod"]} / {f["id"]}: {kind}{when}, {title}'
                          + (f', {len(neg)} FHR exceptions' if kind == 'attacks' else ''))
        index = {id(f): i for i, (f, _r) in enumerate(layers)}
        for f, rights, direction in addons:
            pairs = {p for p in PAIRS if live(f, rights, *p, effects=True)
                     and winners[p] is not None and winners[p]['source'] == f['source']}
            if not pairs:
                unused.append(f)
                continue
            neg = lsdf.fhr_negations(specials, pairs, f['clips'])
            conds = [perk, lsdf.BASE_CONDS[1], lsdf.weapon_cond(pairs), direction_cond(direction)] + [n for _d, n in neg]
            prio = st['priority'] + 10 * max(index[id(winners[p])] for p in pairs) + 5
            write_user(f, prio, conds, False)
            stance_clips |= f['clips']
            owned.append((perk, f['clips'], set(pairs)))
            written += 1
            title = ' + '.join(lsdf.describe(p) for p in _groups(pairs))
            report.append(f'  {ss.SOURCES[f["source"]]["mod"]} / {f["id"]}: {direction.lower()} addon over its set, '
                          f'{title}, {len(neg)} FHR exceptions')
        for f in unused:
            write_user(f, f['order'] if isinstance(f['order'], int) else 0, list(NEVER), True)
            written += 1
        report.append(f'  disabled: ' + ', '.join(f'{ss.SOURCES[f["source"]]["mod"]} / {f["id"]}' for f in unused))
        report.append('  no attack set (For Honor Reforged plays): ' + (', '.join(
            f'{lsdf.TYPE_NAME[r]}+{lsdf.TYPE_NAME.get(l, l)}' for r, l in gaps if r not in TWO) or 'none'))
    providers = oar_submods()
    lifted = lifted_priorities(providers, stance_clips)
    for f in providers:
        if f['rel'] in lifted:
            cfg = json.loads(json.dumps(f['cfg']))
            cfg['priority'] = lifted[f['rel']]
            out = os.path.join(out_mod, *f['rel'].split('/'), 'user.json')
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with open(out, 'w', encoding='utf-8', newline='\n') as fh:
                json.dump(cfg, fh, indent=1)
            written += 1
    smooth = 0
    for f in providers:
        if f['rel'] in lifted:
            continue
        blocks = smooth_chain_blocks(f, owned)
        if not blocks:
            continue
        cfg = json.loads(json.dumps(f['cfg']))
        cfg['conditions'] = cfg['conditions'] + blocks
        out = os.path.join(out_mod, *f['rel'].split('/'), 'user.json')
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, 'w', encoding='utf-8', newline='\n') as fh:
            json.dump(cfg, fh, indent=1)
        written += 1
        smooth += 1
    report.append(f'Smooth idle chain: {smooth} submods switched off where a stance owns the idle')
    report.append(f'F4 lift: {len(lifted)} sprint-only submods of '
                  f'{len({f["mod"] for f in providers if f["rel"] in lifted})} mods lifted to '
                  f'{SPRINT_LIFT_BASE:,}+ (order kept), so every stance sprints like F4')
    with open(os.path.join(out_mod, 'meta.ini'), 'w', encoding='utf-8', newline='\r\n') as fh:
        fh.write('[General]\ngameName=SkyrimSE\nversion=1.0\nnotes=Generated by src/StanceMovesets/tools/'
                 '01-build-stance-overlays.py: OAR user.json overlays only\n')
    print('\n'.join(report))
    print(f'{written} user.json files -> {out_mod}')


def write_user(f, priority, conditions, disabled):
    if f['kind'] == 'oar':
        cfg = json.loads(json.dumps(f['config']))
        cfg.update({'priority': priority, 'disabled': disabled, 'conditions': conditions})
    else:
        cfg = {'priority': priority, 'disabled': disabled, 'conditions': conditions}
    out = os.path.join(MODS, ss.OVERLAY_MOD, *f['rel'].split('/'), 'user.json')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(cfg, fh, indent=1)


def _groups(pairs):
    groups = {}
    for r, l in pairs:
        cls = 'two' if r in TWO else 'dw' if l in (1, 2, 3, 4) else 'shd' if l in (8, 11, 18) else 'single'
        groups.setdefault(cls, set()).add((r, l))
    return [g for _k, g in sorted(groups.items(), key=lambda kv: sorted(kv[1]))]


if __name__ == '__main__':
    main()
