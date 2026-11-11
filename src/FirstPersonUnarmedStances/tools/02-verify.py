"""Check the first-person unarmed stance sets without the game, over the profile's whole first-person OAR tree (every
enabled mod + overwrite, MO2's file winner per path, a user.json replacing its config.json).

  - No submod of the three sets can ever play outside its own stance, or with a weapon in the right hand
    (every stance x right-hand weapon type x left-hand type).
  - In each stance, with the right hand unarmed and the left hand unarmed / shield / spell / torch: every clip the
    stance's set carries is won by that set. A higher-priority submod of another mod whose conditions this check
    cannot decide (a magic effect, IsAttacking, Random...) is listed as 'may win'.
  - With no stance, no submod of the three sets is live (SIGMA plays).
Prints, per stance, which mod plays how many fist clips.

Conditions are evaluated for the player with the weapon drawn: IsEquippedType, the three stance perks, IsActorBase,
IsRace (the player is no Argonian/Khajiit), IsWeaponDrawn; anything else is undecided.

Usage:  python 02-verify.py [<modlist root>] [<profile>]
"""
import collections
import itertools
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fpu_sources as fs  # noqa: E402

BEAST = {'13740', '13745'}            # ArgonianRace, KhajiitRace (Skyrim.esm)
STANCES = [None, 'High', 'Mid', 'Low']
WEAPONS = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
LEFTS = (0, 1, 2, 11, 12, 18)


def enabled_mods():
    with open(os.path.join(fs.PROFILE, 'modlist.txt'), encoding='utf-8') as fh:
        mods = [l[1:].strip() for l in fh if l.startswith('+')]
    ours = [s['mod'] for s in fs.SOURCES.values()] + [fs.OVERLAY_MOD]
    missing = [m for m in ours if m not in mods]
    if missing:
        print('NOTE: not ticked in the profile yet, checked as if ticked on top:', ', '.join(missing))
    return missing + mods          # highest priority first


def vfs_submods():
    files = {}                     # rel lower -> abs path, MO2 winner
    for m in list(reversed(enabled_mods())) + [None]:
        base = fs.OVERWRITE if m is None else os.path.join(fs.MODS, m)
        oar = fs.find_ci(base, fs.OAR_1P)
        if oar is None:
            continue
        for dp, _dn, fn in os.walk(oar):
            for f in fn:
                ab = os.path.join(dp, f)
                files[os.path.relpath(ab, oar).replace(os.sep, '/').lower()] = (m or 'overwrite', ab)
    dirs = collections.defaultdict(dict)
    for rel, v in files.items():
        d, f = rel.rsplit('/', 1) if '/' in rel else ('', rel)
        dirs[d][f] = v
    out = {}
    for d, fl in dirs.items():
        if 'config.json' not in fl:
            continue
        with open(fl['config.json'][1], encoding='utf-8-sig') as fh:
            cfg = json.load(fh)
        if 'priority' not in cfg:
            continue
        if 'user.json' in fl:
            with open(fl['user.json'][1], encoding='utf-8-sig') as fh:
                cfg = json.load(fh)
        clips = {f[:-4] for f in fl if f.endswith('.hkx')}
        clips |= {k.rsplit('/_variants_', 1)[1] for k in dirs if k.startswith(d + '/_variants_')}
        out[d] = {'mod': fl['config.json'][0], 'cfg': cfg, 'clips': clips}
    return out


def ev(c, stance, r, l):
    n = c['condition']
    if n in ('AND', 'OR'):
        vals = [ev(x, stance, r, l) for x in c.get('Conditions', [])]
        if n == 'AND':
            v = False if False in vals else (True if all(x is True for x in vals) else None)
        else:
            v = True if True in vals else (False if all(x is False for x in vals) else None)
    elif n == 'IsEquippedType':
        v = (l if c.get('Left hand') else r) == int(c['Type']['value'])
    elif n == 'HasPerk' and c['Perk'].get('pluginName') == fs.STANCES_ESP:
        v = stance is not None and c['Perk']['formID'].upper() == fs.PERKS[stance].upper()
    elif n == 'IsActorBase':
        v = c['Actor base'].get('pluginName', '').lower() == 'skyrim.esm' and c['Actor base']['formID'] in ('7', '07')
    elif n == 'IsRace' and c['Race'].get('pluginName', '').lower() == 'skyrim.esm' and c['Race']['formID'] in BEAST:
        v = False
    elif n == 'IsWeaponDrawn':
        v = True
    elif n == 'Random' and c.get('Comparison') == '<' and             c['Numeric value']['value'] >= c['Maximum random value']['value']:
        v = True                   # '< max': always true (First-Person Boxing's Combo1, the combo floor)
    else:
        return None
    return None if v is None else v != c.get('negated', False)


def live(sub, stance, r, l):
    if sub['cfg'].get('disabled'):
        return False
    return ev({'condition': 'AND', 'Conditions': sub['cfg'].get('conditions', [])}, stance, r, l)


def main():
    subs = vfs_submods()
    owner = {s['mod']: k for k, s in fs.SOURCES.items()}
    ours = {d: s for d, s in subs.items() if s['mod'] in owner}
    if not ours:
        raise SystemExit('none of the three sets found in the first-person OAR tree')
    problems = []
    # 1. never outside its stance, never with a weapon in the right hand
    for (d, s), stance, r, l in itertools.product(ours.items(), STANCES, (0,) + WEAPONS, LEFTS):
        v = live(s, stance, r, l)
        allowed = r == 0 and stance == fs.SOURCES[owner[s['mod']]]['stance']
        if v is not False and not allowed:
            problems.append(f'{s["mod"]} / {d} can play: stance {stance}, right {r}, left {l} ({v})')
    # 2./3. who plays each fist clip
    fist_clips = set().union(*(s['clips'] for s in ours.values() if not s['cfg'].get('disabled')))
    for stance in STANCES:
        tally, maybe = collections.Counter(), set()
        for l in (0, 11, 12, 18):
            for clip in sorted(fist_clips):
                cands = sorted((s for s in subs.values() if clip in s['clips']), key=lambda s: -s['cfg']['priority'])
                above, winner = [], None
                for s in cands:
                    v = live(s, stance, 0, l)
                    if v is True:
                        winner = s
                        break
                    if v is None:
                        above.append(s)
                own = stance and next(k for k, src in fs.SOURCES.items() if src['stance'] == stance)
                own_has = own and any(clip in s['clips'] and live(s, stance, 0, l) is not False
                                      for s in ours.values() if owner[s['mod']] == own)
                tally[winner['mod'] if winner else '(vanilla)'] += 1
                for s in above:
                    if s['mod'] not in owner or owner[s['mod']] != own:
                        maybe.add(f'{s["mod"]} ({s["cfg"].get("name")}, {s["cfg"]["priority"]}), left hand {l}')
                if own_has and (winner is None or owner.get(winner['mod']) != own):
                    problems.append(f'stance {stance}, left {l}: {clip} won by '
                                    f'{winner["mod"] if winner else "vanilla"}, not {fs.SOURCES[own]["mod"]}')
                if stance is None and winner is not None and winner['mod'] in owner:
                    problems.append(f'no stance, left {l}: {clip} won by {winner["mod"]}')
        print(f'{stance or "no stance"}: ' + ', '.join(f'{m} {n}' for m, n in tally.most_common())
              + ' (clip x left-hand cases)')
        for m in sorted(maybe):
            print(f'    may win above it (undecided conditions): {m}')
    for p in problems:
        print('PROBLEM', p)
    print(f'{len(ours)} submods of the three sets, {len(problems)} problems')
    sys.exit(1 if problems else 0)


if __name__ == '__main__':
    main()
