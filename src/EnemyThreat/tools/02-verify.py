"""Check Zenderal - Enemy Threat's generated YAML against its masters. Run after tools/01 (and after Prophecy's
tools/01). Exits non-zero on any problem.

1. Every FormKey the plugin references resolves in its masters (Enderal 2.1.4.4's Skyrim/Update/FS, EGO, Prophecy)
   or in the plugin itself; PlayerRef 000014 is allow-listed (CLAUDE.md guardrail 11).
2. The add table: ZET_AddBosses and ZET_AddBases have the same length, every boss carries ActorTypeBoss, no add does.
3. The lockout: Prophecy defines ZP_StaggerLockout 0xB4C, every Stagger-archetype effect in Prophecy and EGO's
   XionStagger override here refuse targets with it, and ZET_StaggerLockoutEffect carries it.
4. The SPID ini hands out exactly 0x800 (perk), 0x801 (perk) and 0x802 (ability spell).
"""
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _npcs as N  # noqa: E402

REPO = N.REPO
ESP = os.path.join(REPO, 'src', 'EnemyThreat', 'EnemyThreatESP')
PROPHECY_ESP = os.path.join(REPO, 'src', 'Prophecy', 'ProphecyESP')
SPID = os.path.join(REPO, 'src', 'EnemyThreat', 'spid', 'Zenderal - Enemy Threat_DISTR.ini')
OWN = 'Zenderal - Enemy Threat.esp'
LOCKOUT_KW = '000B4C:Zenderal - Prophecy.esp'
MASTER_TREES = {
    'Skyrim.esm': [os.path.join(N.REF, 'base-2.1.4.4', 'Skyrim')],
    'Update.esm': [os.path.join(N.REF, 'base-2.1.4.4', 'Update')],
    'Enderal - Forgotten Stories.esm': [os.path.join(N.REF, 'base-2.1.4.4', 'EnderalFS')],
    'Enderal SE - Gameplay Overhaul.esp': [os.path.join(N.REF, 'mods', 'EGO')],
    'Zenderal - Prophecy.esp': [PROPHECY_ESP],
    OWN: [ESP],
}
ALLOW = {'000014:Skyrim.esm'}
FK = re.compile(r'\b([0-9A-F]{6}):((?:[^\s:\'"]|(?<=\S) (?=\S))+?\.(?:esm|esp|esl))\b')

problems = []


def defined(trees):
    out = set()
    for t in trees:
        for p in glob.glob(os.path.join(t, '**', '*.yaml'), recursive=True):
            m = re.search(r' - ([0-9A-F]{6})_(.+)\.yaml$', os.path.basename(p))
            if m:
                out.add('%s:%s' % (m.group(1), m.group(2)))
    return out


def main():
    have = set()
    for plugin, trees in MASTER_TREES.items():
        have |= {k for k in defined(trees) if k.endswith(':' + plugin)}
    refs = {}
    for p in glob.glob(os.path.join(ESP, '**', '*.yaml'), recursive=True):
        for line in open(p, encoding='utf-8-sig'):
            for m in FK.finditer(line):
                refs.setdefault('%s:%s' % (m.group(1), m.group(2)), p)
    for k, p in sorted(refs.items()):
        plugin = k.split(':', 1)[1]
        if plugin not in MASTER_TREES:
            problems.append('reference to a non-master: %s (%s)' % (k, os.path.basename(p)))
        elif k not in have and k not in ALLOW:
            problems.append('unresolved: %s (%s)' % (k, os.path.basename(p)))
    print('%d FormKeys referenced, all checked against %d masters' % (len(refs), len(MASTER_TREES) - 1))

    def items(edid):
        p = glob.glob(os.path.join(ESP, 'FormLists', '%s - *' % edid))[0]
        return re.findall(r'^- (.+?)\s*$', open(p, encoding='utf-8-sig').read(), re.M)
    bosses, adds = items('ZET_AddBosses'), items('ZET_AddBases')
    if len(bosses) != len(adds):
        problems.append('add table: %d bosses, %d adds' % (len(bosses), len(adds)))
    npcs = N.load_npcs()
    for b in bosses:
        if N.BOSS_KEYWORD not in N.resolve(npcs, b)['keywords']:
            problems.append('add table boss without ActorTypeBoss: ' + b)
    for a in adds:
        if N.BOSS_KEYWORD in N.resolve(npcs, a)['keywords']:
            problems.append('add is itself a boss: ' + a)
    print('add table: %d bosses' % len(bosses))

    if not glob.glob(os.path.join(PROPHECY_ESP, 'Keywords', 'ZP_StaggerLockout - 000B4C_*')):
        problems.append('Prophecy has no ZP_StaggerLockout 0xB4C: rerun src/Prophecy/tools/01')
    guarded = 0
    for p in glob.glob(os.path.join(PROPHECY_ESP, 'MagicEffects', '*.yaml')) + \
            glob.glob(os.path.join(ESP, 'MagicEffects', 'XionStagger - *')):
        t = open(p, encoding='utf-8-sig').read()
        if re.search(r'^  Type: Stagger\r?$', t, re.M):
            if 'HasMagicEffectKeywordConditionData' not in t or LOCKOUT_KW not in t:
                problems.append('stagger effect without the lockout guard: ' + os.path.basename(p))
            else:
                guarded += 1
    print('stagger effects guarded: %d (Prophecy 10 + EGO 1 expected)' % guarded)
    if guarded != 11:
        problems.append('guarded %d stagger effects, expected 11' % guarded)
    lock = open(glob.glob(os.path.join(ESP, 'MagicEffects', 'ZET_StaggerLockoutEffect - *'))[0], encoding='utf-8-sig').read()
    if LOCKOUT_KW not in lock:
        problems.append('ZET_StaggerLockoutEffect does not carry ZP_StaggerLockout')

    ini = open(SPID, encoding='utf-8-sig').read()
    lines = [l for l in ini.splitlines() if l.strip() and not l.startswith(';')]
    want = {'Perk = 0x800~%s' % OWN: 'Perks', 'Perk = 0x801~%s|ActorTypeBoss' % OWN: 'Perks',
            'Spell = 0x802~%s|ActorTypeBoss' % OWN: 'Spells'}
    if sorted(lines) != sorted(want):
        problems.append('SPID lines changed: %r' % lines)
    for line, sub in want.items():
        local = re.search(r'0x([0-9A-F]{3})', line).group(1)
        if not glob.glob(os.path.join(ESP, sub, '* - 000%s_*' % local)):
            problems.append('SPID hands out 0x%s, which is not a %s record' % (local, sub))
    ab = open(glob.glob(os.path.join(ESP, 'Spells', 'ZET_BossAbility - *'))[0], encoding='utf-8-sig').read()
    if 'Type: Ability' not in ab:
        problems.append('ZET_BossAbility is not an ability')

    for p in problems:
        print('PROBLEM:', p)
    print('OK' if not problems else '%d problem(s)' % len(problems))
    sys.exit(1 if problems else 0)


if __name__ == '__main__':
    main()
