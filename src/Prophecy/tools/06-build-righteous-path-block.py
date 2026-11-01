"""Build the `Zenderal - Righteous Path Shield Block` MO2 mod: while Righteous Path's ward is up, the player blocks
with the shield animations instead of the one-handed weapon ones (curator 2026-10-25).

Why a clip mod: the block pose comes from the behavior graph, which plays shield-block clips only when a real shield
is in the left hand. Righteous Path's ward (ZP_Prophecy_RighteousPath_Ward, see 01) is worn in the FX01 slot so a
spell can stay in the left hand, so the graph keeps the one-handed block state and asks for its 1hm_* clips.

What this does: it mirrors every non-javelin shield set of Dynamic Block Hit (the list's shield block idles and
Maxsu Block Overhaul hit reactions: base, randoms, power attack, stagger) as an OAR submod that serves the shield
clips under the one-handed names. Each set keeps its own conditions (random rolls, power-attack effect, javelin
check, right-hand weapon types) except "a shield in the left hand", which becomes Righteous Path's: the perk
(Zenderal - Prophecy.esp 0x811) and a left hand that is empty (type 0) or holds a spell or scroll (12-17), as
ZP_RighteousPathEffect checks. Priorities sit above every set that applies to the player (NPC Block Loop Fix's
2147483501+ are NPC-only), keeping Dynamic Block Hit's order among themselves.

Source: whichever of Dynamic Block Hit / Dynamic Block Hit Rebalanced is enabled with the higher MO2 priority.
First person (curator 2026-10-25) is one more submod under _1stperson: the shield idle, anticipate and hit clips of
SIGMA - Shield animations - 1st person (its OAR set; vanilla's from Skyrim - Animations.bsa when SIGMA is off) served
as their 1hm_* names, on the same Righteous Path conditions, above every first-person 1hm block set (top: SigmaJelly
Katana, 800000003). Bashes and the shield equip clip are left alone.
Nothing third-party is committed: the clips are copied straight into the MO2 mods folder. Rerun after a Dynamic
Block Hit or SIGMA Shield update.

Usage:  python -I src/Prophecy/tools/06-build-righteous-path-block.py [<modlist root>]   (default: tools.json)
"""
import copy
import json
import os
import re
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
TOOLS = json.load(open(os.path.join(ROOT, '.claude', 'config', 'tools.json'), encoding='utf-8-sig'))

MOD = 'Zenderal - Righteous Path Shield Block'
SOURCES = ['Dynamic Block Hit Rebalanced', 'Dynamic Block Hit']
SET_ROOT = ['meshes', 'actors', 'character', 'animations', 'OpenAnimationReplacer', 'Dynamic Block Hit']
PRIORITY_BASE = 2100000000          # + (the set's own priority - 8970000)
RENAME = {'shd_blockidle.hkx': '1hm_blockidle.hkx',
          'shd_blockanticipate.hkx': '1hm_blockanticipate.hkx',
          'maxsublockoverhaul/maxsu_shieldblockhit.hkx': 'MaxsuBlockOverhaul/Maxsu_WeaponBlockHit.hkx'}
SHIELD_LEFT = {'condition': 'IsEquippedType', 'Type': {'value': 11.0}, 'Left hand': True}
RIGHTEOUS_PATH = [
    {'condition': 'HasPerk', 'requiredVersion': '1.0.0.0',
     'Perk': {'pluginName': 'Zenderal - Prophecy.esp', 'formID': '811'}},       # ZP_Prophecy_RighteousPath
    {'condition': 'OR', 'requiredVersion': '1.0.0.0', 'Conditions': [
        {'condition': 'IsEquippedType', 'requiredVersion': '1.0.0.0', 'Type': {'value': float(v)}, 'Left hand': True}
        for v in (0, 12, 13, 14, 15, 16, 17)]},                                  # empty, a spell or a scroll
]


FP_SIGMA = 'SIGMA - Shield animations - 1st person'
FP_SIGMA_SET = ['meshes', 'actors', 'character', '_1stperson', 'animations', 'OpenAnimationReplacer', 'SigmaBoy_shield',
                'shield']
FP_RENAME = {'shd_blockidle.hkx': '1hm_blockidle.hkx', 'shd_blockanticipate.hkx': '1hm_blockanticipate.hkx',
             'shd_blockhit.hkx': '1hm_blockhit.hkx', 'shd_blockhit_vara.hkx': '1hm_blockhita.hkx',
             'shd_blockhit_varb.hkx': '1hm_blockhitb.hkx'}
FP_PRIORITY = 2100002000


def first_person(root, mods_dir, mods, out_mod):
    """The first-person submod: SIGMA's (else vanilla's) shield block clips under the one-handed names."""
    sigma = find_ci(os.path.join(mods_dir, FP_SIGMA), FP_SIGMA_SET) if FP_SIGMA in mods else None
    bsa = None
    if not sigma:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import _bsa
        bsa = (_bsa, _bsa.listing(os.path.join(root, 'Stock Game', 'Data', 'Skyrim - Animations.bsa')))
    dst = os.path.join(out_mod, 'meshes', 'actors', 'character', '_1stperson', 'animations', 'OpenAnimationReplacer',
                       MOD, 'Righteous Path Shield 1st person')
    os.makedirs(dst)
    for src_name, out_name in FP_RENAME.items():
        if sigma:
            hit = [f for f in os.listdir(sigma) if f.lower() == src_name]
            assert hit, 'SIGMA shield set lacks %s' % src_name
            shutil.copyfile(os.path.join(sigma, hit[0]), os.path.join(dst, out_name))
        else:
            mod, (d, l) = bsa
            k = 'meshes\\actors\\character\\_1stperson\\animations\\' + src_name
            open(os.path.join(dst, out_name), 'wb').write(mod.read(d, l[k]))
    label = FP_SIGMA if sigma else 'Skyrim - Animations.bsa'
    with open(os.path.join(dst, 'config.json'), 'w', encoding='utf-8') as fh:
        json.dump({'name': 'Righteous Path Shield 1st person',
                   'description': "Righteous Path's ward: %s's shield block clips under the one-handed names." % label,
                   'priority': FP_PRIORITY, 'conditions': copy.deepcopy(RIGHTEOUS_PATH)}, fh, indent=4)
    with open(os.path.join(os.path.dirname(dst), 'config.json'), 'w', encoding='utf-8') as fh:
        json.dump({'name': MOD, 'author': 'Zenderal',
                   'description': "Prophecy's Righteous Path: shield block animations while its ward is up."}, fh, indent=4)
    print('1st person: %d clips from %s, prio %d' % (len(FP_RENAME), label, FP_PRIORITY))


def profile_mods(root):
    """Enabled mods, highest MO2 priority first (modlist.txt order), for the selected profile."""
    ini = open(os.path.join(root, 'ModOrganizer.ini'), encoding='utf-8', errors='replace').read()
    m = re.search(r'^selected_profile=@ByteArray\((.+)\)\s*$', ini, re.M)
    if not m:
        sys.exit('no selected_profile in ModOrganizer.ini')
    profile = m.group(1)
    lines = open(os.path.join(root, 'profiles', profile, 'modlist.txt'), encoding='utf-8').read().splitlines()
    return profile, [l[1:] for l in lines if l.startswith('+')]


def find_ci(base, parts):
    """Case-insensitive path walk (mods mix Meshes/meshes). Returns the real path or None."""
    cur = base
    for p in parts:
        if not os.path.isdir(cur):
            return None
        hit = [e for e in os.listdir(cur) if e.lower() == p.lower()]
        if not hit:
            return None
        cur = os.path.join(cur, hit[0])
    return cur


def is_shield_left(c):
    return all(c.get(k) == v for k, v in SHIELD_LEFT.items()) and not c.get('negated')


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else TOOLS['modlistRoot']
    mods_dir = os.path.join(root, 'mods')
    profile, mods = profile_mods(root)
    src_mod = next((m for m in mods if m in SOURCES), None)
    if not src_mod:
        sys.exit('neither Dynamic Block Hit nor its Rebalanced version is enabled in %s' % profile)
    sets_dir = find_ci(os.path.join(mods_dir, src_mod), SET_ROOT)
    assert sets_dir, 'no Dynamic Block Hit OAR folder in %s' % src_mod
    out_mod = os.path.join(mods_dir, MOD)
    if os.path.isdir(out_mod):
        shutil.rmtree(out_mod)
    oar = os.path.join(out_mod, *SET_ROOT[:-1], MOD)
    built = 0
    for name in sorted(os.listdir(sets_dir)):
        if not name.startswith('Shield '):
            continue                       # Javelin Shield sets: a javelin and a ward is not a Righteous Path pairing
        src = os.path.join(sets_dir, name)
        cfg = json.load(open(os.path.join(src, 'config.json'), encoding='utf-8-sig'))
        conds = [c for c in cfg['conditions'] if not is_shield_left(c)]
        assert len(conds) == len(cfg['conditions']) - 1, '%s: expected one shield-in-left-hand condition' % name
        files = []
        for dp, _, fn in os.walk(src):
            for f in fn:
                rel = os.path.relpath(os.path.join(dp, f), src).replace(os.sep, '/').lower()
                if rel != 'config.json':
                    files.append(rel)
        unknown = [f for f in files if f not in RENAME]
        assert not unknown, '%s: unmapped clips %s' % (name, unknown)
        dst = os.path.join(oar, 'Righteous Path ' + name)
        for f in files:
            out = os.path.join(dst, *RENAME[f].split('/'))
            os.makedirs(os.path.dirname(out), exist_ok=True)
            shutil.copyfile(os.path.join(src, *f.split('/')), out)
        new = {'name': 'Righteous Path ' + name,
               'description': "Righteous Path's ward: %s's '%s' shield clips under the one-handed names." % (src_mod, name),
               'priority': PRIORITY_BASE + (cfg['priority'] - 8970000),
               'conditions': copy.deepcopy(RIGHTEOUS_PATH) + conds}
        if cfg.get('interruptible') is not None: new['interruptible'] = cfg['interruptible']
        with open(os.path.join(dst, 'config.json'), 'w', encoding='utf-8') as fh:
            json.dump(new, fh, indent=4)
        print('%-28s prio %d  %s' % (name, new['priority'], ', '.join(RENAME[f] for f in files)))
        built += 1
    with open(os.path.join(oar, 'config.json'), 'w', encoding='utf-8') as fh:
        json.dump({'name': MOD, 'author': 'Zenderal',
                   'description': "Prophecy's Righteous Path: shield block animations while its ward is up."}, fh, indent=4)
    first_person(root, mods_dir, mods, out_mod)
    print('built %s from %s for profile %s: %d sets + 1st person' % (MOD, src_mod, profile, built))


if __name__ == '__main__':
    main()
