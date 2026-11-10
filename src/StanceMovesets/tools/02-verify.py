"""Check the three stances without the game: High (F1), Mid (F2) and Low (F3), each = untouched sources +
`Zenderal - Stance Overlays`. Fails if the shelved LSdF High mod is enabled alongside.

  - Gating: every enabled submod starts with its stance's perk and the player; every submod folder of every source
    has an overlay user.json (a folder without one would run on its own conditions: NPCs, all stances), and the
    unused ones are disabled with never-true conditions.
  - Coverage: at every weapon pair at most one attack-bearing submod per stance matches by its own weapon conditions.
  - For Honor Reforged: for every attack-bearing submod, every weapon pair it serves and every enabled FHR special
    submod (directional, parry, follow-ups, knockdowns, combo layers) that shares a clip and can be true there, the
    submod holds a negated block whose conjuncts are a subset of that FHR submod's at that pair: whenever FHR's
    special submod is true, the stance's submod is false and FHR's clip plays. FHR is re-read from the live profile.

Usage:  python 02-verify.py [<modlist root>] [<profile>]
"""
import importlib.util
import json
import os
import re
import sys

import stance_sources as ss

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location('overlays', os.path.join(HERE, '01-build-stance-overlays.py'))
ov = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ov)

lsdf = ss.lsdf
MODS = lsdf.MODS
TWO = lsdf.TWO_HANDED
PAIRS = ov.PAIRS
ATTACK = re.compile(r'^mco_(power)?attack\d+$')
SHELVED_HIGH = 'Zenderal - Le Sentiment du Fer High Stance'


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
    else:
        raise ValueError(f'unexpected own condition {n}')
    return v != c.get('negated', False)


def conj(v):
    v = lsdf.canonical(v)
    items = v['Conditions'] if v.get('condition') == 'AND' and not v.get('negated') else [v]
    return frozenset(json.dumps(k, sort_keys=True) for k in items)


DIRECTION_GATES = [ov.direction_cond(n) for n in ss.ADDON_DIRECTIONS]


def gate_ok(conds, perk):
    """Perk, player, weapon pairs, then only FHR exceptions (negated) - or, for a directional addon, one direction
    gate first (01's direction_cond)."""
    rest = conds[3:]
    if rest and (rest[0] in DIRECTION_GATES or rest[0] == ov.IN_COMBAT):    # an addon's or an in-combat guard's gate
        rest = rest[1:]
    return (conds[0]['condition'] == 'HasPerk' and conds[0]['Perk']['formID'] == perk
            and conds[0]['Perk']['pluginName'] == ss.STANCES_ESP
            and conds[1]['condition'] == 'IsActorBase' and conds[1]['Actor base']['formID'] == '7'
            and not conds[1].get('negated') and not conds[2].get('negated')
            and all(x.get('negated') for x in rest))


def is_addon(conds):
    return len(conds) > 3 and conds[3] in DIRECTION_GATES


def fhr_check(label, own, negs, clips, skills, specials):
    pairs = {(r, l) for r, l in PAIRS if any(ev(own, r, l, oh, th) for oh, th in skills)}
    blocks = []
    for b in negs:
        inner = json.loads(json.dumps(b))
        inner['negated'] = not inner.get('negated', False)
        if not inner['negated']:
            del inner['negated']
        blocks.append(inner)
    checked = missing = 0
    for s in specials:
        if not s['clips'] & clips:
            continue
        for p in pairs:
            sv = lsdf.simplify(lsdf.c_and(s['conditions']), {p})
            if sv is False:
                continue
            if sv is True:
                print(f'{label}: FHR {s["dir"]} always true at {p}')
                missing += 1
                continue
            sc = conj(sv)
            checked += 1
            if not any((lambda bv: bv is True or (isinstance(bv, dict) and conj(bv) <= sc))(lsdf.simplify(b, {p}))
                       for b in blocks):
                missing += 1
                print(f'{label}: no exception for FHR {s["dir"]} at {p}')
    return checked, missing


def main():
    specials = [s for s in lsdf.fhr_submods()
                if lsdf._distinguishing(s['conditions']) and not lsdf._player_excluded(s['conditions'])]
    problems = 0

    # High was LSdFHighStance's generated mod until 2026-11-10 (shelved; its own tools/02 still checks it). It gates on
    # the same perk as the Nordic overlay, so both enabled = two attack sets on F1.
    with open(os.path.join(lsdf.PROFILE, 'modlist.txt'), encoding='utf-8-sig') as fh:
        if any(ln.strip() == '+' + SHELVED_HIGH for ln in fh):
            print(f'{SHELVED_HIGH} is enabled too: it competes with the Nordic set on F1')
            problems += 1

    # High / Mid / Low: overlays over the untouched sources
    for st in ss.STANCES:
        enabled, n_disabled, leaks = [], 0, 0
        for key in {k for k, *_ in st['layers']}:
            for f in ov.source_folders(key):
                p = os.path.join(MODS, ss.OVERLAY_MOD, *f['rel'].split('/'), 'user.json')
                label = f'{st["name"]}: {ss.SOURCES[key]["mod"]} / {f["id"]}'
                if not os.path.exists(p):
                    print(f'{label}: NO user.json - runs ungated')
                    leaks += 1
                    continue
                with open(p, encoding='utf-8') as fh:
                    cfg = json.load(fh)
                if cfg.get('disabled'):
                    n_disabled += 1
                    if not (cfg['conditions'] == ov.NEVER):
                        print(f'{label}: disabled without the never-true lock')
                        leaks += 1
                    continue
                if not gate_ok(cfg['conditions'], st['perk']):
                    print(f'{label}: gating wrong')
                    leaks += 1
                    continue
                enabled.append((label, cfg['conditions'], f['clips'], key, cfg['priority']))
        attack = [e for e in enabled if any(ATTACK.match(x) for x in e[2])]
        sets = [e for e in attack if not is_addon(e[1])]
        addons = [e for e in attack if is_addon(e[1])]
        overlaps = 0
        for r, l in PAIRS:
            hits = [lb for lb, c, *_ in sets if ev(c[2], r, l, 80, 80)]
            if len(hits) > 1:
                overlaps += 1
                print(f'{st["name"]}: overlap at {(r, l)}: {hits}')
        # an addon (directional extra) must sit on its own source's set, above it, at every pair it serves
        for lb, c, _cl, key, prio in addons:
            for r, l in PAIRS:
                if not ev(c[2], r, l, 80, 80):
                    continue
                base = [e for e in sets if ev(e[1][2], r, l, 80, 80)]
                if not (base and base[0][3] == key and base[0][4] < prio):
                    overlaps += 1
                    print(f'{lb}: at {(r, l)} not over its own set ({[e[0] for e in base]})')
        checked = missing = 0
        for lb, c, cl, *_ in attack:
            negs = [x for x in c[3:] if x.get('negated')]
            a, b = fhr_check(lb, c[2], negs, cl, [(80, 80)], specials)
            checked, missing = checked + a, missing + b
        problems += leaks + overlaps + missing
        print(f'{st["name"]} (overlays): {len(enabled)} enabled ({len(sets)} attack sets, {len(addons)} addons), '
              f'{n_disabled} disabled, '
              f'{leaks} ungated/mis-gated, {overlaps} overlaps, {checked} FHR cases covered, {missing} uncovered')
    print(f'{len(specials)} FHR special submods; {problems} problems')
    sys.exit(1 if problems else 0)


if __name__ == '__main__':
    main()
