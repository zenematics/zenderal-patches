"""Check the generated `Zenderal - Le Sentiment du Fer High Stance` mod without the game.

  - Every weapon pair (right type x left type, none for two-handers) at every One-/Two-Handed band pair matches
    exactly one attack submod and at most one guard submod, by the submods' own weapon/skill conditions (the FHR
    exception blocks are not evaluated here; they only ever switch a submod off).
  - Every submod is gated on the High stance perk 042518 and the player.
  - Prints the MCO annotations of a few converted clips for a by-eye check.

Usage:  python 02-verify.py [<modlist root>]
"""
import itertools
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'FHRFirstPerson', 'tools'))
import hkx_annotate  # noqa: E402

ROOT = sys.argv[1] if len(sys.argv) > 1 else 'E:/Zenderal'
MOD = 'Zenderal - Le Sentiment du Fer High Stance'
OUT = os.path.join(ROOT, 'mods', MOD, 'meshes', 'actors', 'character', 'animations', 'OpenAnimationReplacer', MOD)
TWO = (5, 6, 10)
PAIRS = [(r, 0) for r in TWO] + [(r, l) for r in (0, 1, 2, 3, 4)
                                  for l in (0, 1, 2, 3, 4, 8, 11, 12, 13, 14, 15, 16, 17, 18)]
SKILLS = [(oh, th) for oh in (10, 30, 60, 80) for th in (10, 30, 60, 80)]


def ev(c, r, l, oh, th):
    n = c['condition']
    if n in ('AND', 'OR'):
        vals = [ev(x, r, l, oh, th) for x in c['Conditions']]
        v = all(vals) if n == 'AND' else any(vals)
    elif n == 'IsEquippedType':
        v = (l if c['Left hand'] else r) == int(c['Type']['value'])
    elif n == 'CompareValues' and 'actorValue' in c['Value A']:
        a = {6: oh, 7: th}[c['Value A']['actorValue']]
        v = a >= c['Value B']['value'] if c['Comparison'] == '>=' else a < c['Value B']['value']
    elif n in ('HasPerk', 'IsActorBase'):
        v = True
    else:
        raise ValueError(f'unexpected own condition {n}')
    return v != c.get('negated', False)


def main():
    subs = {}
    for d in sorted(os.listdir(OUT)):
        if not os.path.isdir(os.path.join(OUT, d)):
            continue
        with open(os.path.join(OUT, d, 'config.json'), encoding='utf-8') as fh:
            cfg = json.load(fh)
        perk, player, own = cfg['conditions'][:3]
        assert perk['condition'] == 'HasPerk' and perk['Perk']['formID'] == '42518', d
        assert player['condition'] == 'IsActorBase' and player['Actor base']['formID'] == '7', d
        assert all(c.get('negated') for c in cfg['conditions'][3:]), d
        subs[d] = cfg['conditions'][:3]
    bad = 0
    for (r, l), (oh, th) in itertools.product(PAIRS, SKILLS):
        hits = [d for d, own in subs.items() if all(ev(c, r, l, oh, th) for c in own)]
        att = [d for d in hits if d.startswith('Attacks')]
        grd = [d for d in hits if d.startswith('Guard')]
        if len(att) != 1 or len(grd) > 1:
            bad += 1
            print('PROBLEM', (r, l, oh, th), att, grd)
    print(f'{len(subs)} submods, {len(PAIRS) * len(SKILLS)} cases, {bad} problems')
    for d in sorted(subs):
        if d.startswith('Attacks - Sword - Master') or d.startswith('Attacks - Dual') and d.endswith('Master'):
            print('==', d)
            for f in ('mco_attack1', 'mco_attack5', 'mco_powerattack5'):
                dur, anns = hkx_annotate.read(os.path.join(OUT, d, f + '.hkx'))
                keep = [(round(t, 3), x) for t, x in sorted(anns)
                        if x.startswith(('MCO', 'PIE', 'HitFrame', 'Hitframe', 'weaponLeft'))]
                print(f'  {f} {dur:.2f} s', keep)
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
