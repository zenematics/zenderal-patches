"""Zenderal - FHR Directional Strip Fix: side attacks strip For Honor Reforged's empowered-attack arrows (Reforged
Directional Combat) again. Two overrides, both generated here from the serialized winners:

1. ReforgedEnemyDirectionalDispels 00082C:Reforged Directional Combat.esp - its four ApplyCombatHitSpell entries
   (the dispels): every entry also needs the hit actor to carry the matching arrow in a state the dispel spell can
   strip (the arrow, and not blocking or FHR's 8BC - the spell's purge / block-purge rule), so an entry only takes
   the one combat-hit-spell slot when it strips. The heavy entries also accept the side LIGHT marker while power
   attacking: every 1P power attack starts as a light attack (the light tag fires), while annotations on the 1P
   power-attack clips never become events (their clip generators carry FLAG_DONT_CONVERT_ANNOTATIONS_TO_TRIGGERS),
   so 882/883 never go up in first person. The light entries need not power attacking (FHR: lights strip lights).
2. XionPowerStagger 001DBD:Enderal SE - Gameplay Overhaul.esp, as EGO SE - KataPUMB Hidden Powers.esp wins it - its
   one entry split into four mutually exclusive copies (by which side markers the attacker has) that fail exactly
   when a heavy dispel above would strip, so EGO's power-attack stagger yields the slot only then. Independent of
   how the engine orders entries across perks (one hit spell per hit; trace: EGO beat Directional beat FHR).

Usage: python 01-build-fhr-directional-strip-fix.py
Reads reference/mods/FHRDirectional (Reforged Directional Combat.esp) and reference/mods/EGOKataPUMBHiddenPowers
(EGO SE - KataPUMB Hidden Powers.esp), both serialized with Spriggit 0.40.0. Rerun after either plugin updates.
Evidence: arch-docs/patches/FHRDirectionalStripFix.md."""
import os
import re
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
OUT = os.path.join(HERE, '..', 'FHRDirectionalStripFixESP', 'Perks')
DIR_PERK = os.path.join(REPO, 'reference', 'mods', 'FHRDirectional', 'Perks',
                        'ReforgedEnemyDirectionalDispels - 00082C_Reforged Directional Combat.esp.yaml')
EGO_PERK = os.path.join(REPO, 'reference', 'mods', 'EGOKataPUMBHiddenPowers', 'Perks',
                        'XionPowerStagger - 001DBD_Enderal SE - Gameplay Overhaul.esp.yaml')
BAL = 'For Honor Balance Patch.esp'
DIRP = 'Reforged Directional Combat.esp'

# For Honor Balance Patch.esp: the side markers PIE's $LeftLight/$RightLight/$LeftHeavy/$RightHeavy cast on the attacker
MARK = {'LL': '000880', 'RL': '000881', 'LH': '000882', 'RH': '000883'}
BLOCK_SLIDE_CD = '0008BC'  # BackPowerBlockSlideSelfCD: the dispel's block-purge variant needs it on a blocking target
# Reforged Directional Combat.esp: the arrows (empowered attacks) on the hit actor
ARROW = {'RH': '000801', 'LH': '000802', 'RL': '000804', 'LL': '000805'}


def cond(kind, ref=None, value=0, orf=False, indent='    '):
    """One Spriggit ConditionFloat item (EqualTo); kind = HasMagicEffect, IsBlocking or IsPowerAttacking."""
    lines = [f'{indent}- MutagenObjectType: ConditionFloat']
    if orf:
        lines += [f'{indent}  Flags:', f'{indent}  - OR']
    lines += [f'{indent}  Data:', f'{indent}    MutagenObjectType: {kind}ConditionData']
    if ref:
        lines.append(f'{indent}    MagicEffect: {ref}')
    if value:
        lines.append(f'{indent}  ComparisonValue: {value}')
    return lines


def mark(side, value=1, orf=False):
    return cond('HasMagicEffect', f'{MARK[side]}:{BAL}', value, orf)


def strippable(side):
    """The dispel spell strips when the target has the arrow and (is not blocking, or has 8BC): its purge MGEF needs
    arrow + not blocking, its block-purge MGEF arrow + 8BC + blocking."""
    return (cond('HasMagicEffect', f'{ARROW[side]}:{DIRP}', 1)
            + cond('IsBlocking', orf=True) + cond('HasMagicEffect', f'{BLOCK_SLIDE_CD}:{BAL}', 1))


def not_strippable(side):
    """NOT strippable(side) = (no arrow OR blocking) AND (no arrow OR no 8BC)."""
    arrow = f'{ARROW[side]}:{DIRP}'
    return (cond('HasMagicEffect', arrow, 0, orf=True) + cond('IsBlocking', value=1)
            + cond('HasMagicEffect', arrow, 0, orf=True) + cond('HasMagicEffect', f'{BLOCK_SLIDE_CD}:{BAL}', 0))


def read(path):
    raw = open(path, 'rb').read().decode('utf-8')
    return raw.replace('\r\n', '\n'), ('\r\n' if '\r\n' in raw else '\n')


def write(path, text, nl):
    open(path, 'wb').write(text.replace('\n', nl).encode('utf-8'))


def split_effects(text):
    head, body = text.split('\nEffects:\n', 1)
    parts = re.split(r'(?m)^(?=- MutagenObjectType: )', body)
    assert parts[0] == '', 'unexpected text before the first effect'
    return head + '\nEffects:\n', parts[1:]


# --- 1. Reforged Directional Combat's dispel perk -------------------------------------------------------------
text, nl = read(DIR_PERK)
head, effects = split_effects(text)
assert len(effects) == 5, f'82C: expected 5 entries, found {len(effects)}'
assert effects[0].startswith('- MutagenObjectType: PerkEntryPointModifyActorValue'), '82C: first entry changed'
# expected upstream entries: (spell, priority, the original owner conditions in order)
DISPELS = [
    ('RH', '000826', None, [(MARK['RH'], '1', False)]),
    ('LH', '000827', '1', [(MARK['LH'], '1', False)]),
    # upstream's last condition carries a stray OR (harmless alone; it would join an appended one, so the owner tab
    # is written fresh below, never appended to)
    ('RL', '000829', '3', [(MARK['RL'], '1', True), ('000498', '1', True)]),
    ('LL', '00082A', '4', [(MARK['LL'], '1', True), ('000497', '1', False)]),
]
new = [effects[0]]
for (side, spell, prio, orig), eff in zip(DISPELS, effects[1:]):
    assert f'  Spell: {spell}:{DIRP}' in eff, f'82C: entry for {side} no longer casts {spell}'
    got_prio = re.search(r'(?m)^  Priority: (\d+)$', eff)
    assert (got_prio.group(1) if got_prio else None) == prio, f'82C {side}: priority changed'
    got = re.findall(r'(?:Flags:\s*- (OR)\s*)?Data:\s*MutagenObjectType: HasMagicEffectConditionData\s*'
                     r'MagicEffect: (\w{6}):[^\n]*\s*ComparisonValue: (\S+)', eff)
    assert [(m, v, o == 'OR') for o, m, v in got] == orig and eff.count('MutagenObjectType: ConditionFloat') == len(orig), \
        f'82C {side}: upstream conditions changed: {got}'
    owner = []
    if side in ('RH', 'LH'):   # (heavy marker) OR (light marker AND power attacking), as (H OR L) AND (H OR PA)
        light = 'RL' if side == 'RH' else 'LL'
        owner = (mark(side, orf=True) + mark(light) + mark(side, orf=True) + cond('IsPowerAttacking', value=1))
    else:                      # FHR's own (marker OR unarmed buff), plus not power attacking
        unarmed = '000498' if side == 'RL' else '000497'
        owner = (mark(side, orf=True) + cond('HasMagicEffect', f'{unarmed}:{DIRP}', 1) + cond('IsPowerAttacking'))
    lines = ['- MutagenObjectType: PerkEntryPointSelectSpell']
    if prio:
        lines.append(f'  Priority: {prio}')
    lines += ['  Conditions:', '  - Conditions:'] + owner + ['  - RunOnTabIndex: 1', '    Conditions:'] + strippable(side)
    lines += ['  EntryPoint: ApplyCombatHitSpell', '  PerkConditionTabCount: 3', f'  Spell: {spell}:{DIRP}']
    new.append('\n'.join(lines) + '\n')

shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(OUT)
write(os.path.join(OUT, os.path.basename(DIR_PERK)), head + ''.join(new), nl)
print('82C: 4 dispel entries rewritten')

# --- 2. EGO's power-attack stagger (KataPUMB Hidden Powers' winning copy) ------------------------------------------
text, nl = read(EGO_PERK)
head, effects = split_effects(text)
assert len(effects) == 1 and 'Spell: 001D15:Enderal SE - Gameplay Overhaul.esp' in effects[0], 'XionPowerStagger changed'
entry = effects[0]
assert 'Priority:' not in entry and 'IsPowerAttackingConditionData' in entry, 'XionPowerStagger: priority/PA changed'
tab1, tab2 = '  - RunOnTabIndex: 1\n', '  - RunOnTabIndex: 2\n'
assert entry.count(tab1) == 1 and entry.count(tab2) == 1, 'XionPowerStagger: tabs changed'
owner_end, target_end = entry.index(tab1), entry.index(tab2)


def ego_entry(right, left):
    """right/left: whether the attacker carries that side's marker (heavy OR light; EGO already needs power attacking)."""
    owner = []
    owner += (mark('RH', orf=True) + mark('RL')) if right else (mark('RH', 0) + mark('RL', 0))
    owner += (mark('LH', orf=True) + mark('LL')) if left else (mark('LH', 0) + mark('LL', 0))
    target = (not_strippable('RH') if right else []) + (not_strippable('LH') if left else [])
    add_o = '\n'.join(owner) + '\n'
    add_t = ('\n'.join(target) + '\n') if target else ''
    return entry[:owner_end] + add_o + entry[owner_end:target_end] + add_t + entry[target_end:]


out = head + ''.join(ego_entry(r, l) for r, l in ((False, False), (True, False), (False, True), (True, True)))
assert out.count('PerkEntryPointSelectSpell') == 4
write(os.path.join(OUT, os.path.basename(EGO_PERK)), out, nl)
print('XionPowerStagger: 1 entry -> 4 mutually exclusive entries')
