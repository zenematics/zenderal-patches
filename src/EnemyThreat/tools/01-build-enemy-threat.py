"""Build Zenderal - Enemy Threat.esp (curator 2026-11-13: "because of the power boost the Prophecy tree provides, we
need more difficulty in the mid and endgame" ... "bosses should be way more threatening").

Two parts, both delivered by SPID (no Enderal or mod record is edited except EGO's power-attack stagger effect):

1. Scaling (every NPC gets ZET_ScalingPerk): enemies grow with the Prophecy points the player has EARNED
   (ZP_ProphecyPointsEarned 0x809, one point every 3 levels, 30 at most). In steps of 3 points, up to +25% damage
   dealt and -30% damage taken at 30 points. Weapons (ModAttackDamage / ModIncomingDamage) and damage spells
   (ModSpellMagnitude / ModIncomingSpellMagnitude, keyed on the damage keywords EGO's own XionMagicDamage uses plus
   Prophecy's). The owner must be hostile to the player or in combat, and neither a teammate nor a summon.

2. Bosses (every NPC with ActorTypeBoss, 91 in 2.1 + EGO, get ZET_BossPerk and ZET_BossAbility):
   - take half damage (weapons and damage spells), deal +30%;
   - 3x poise: Chocolate Poise Reforged multiplies poise damage by the target's ModIncomingStagger entry
     (PoiseAV.cpp, entry point 33), and it replaces every vanilla hit stagger;
   - can't be stun-locked: when the boss is staggered (IsStaggered, re-checked by the engine about once a second)
     it gets 5 s of ZET_StaggerLockout, an effect with Prophecy's ZP_StaggerLockout keyword: poise damage x0
     (the perk), and none of Prophecy's 10 stagger effects or EGO's power-attack stagger land (their conditions);
   - at half health, once: enrages (Enderal's Fury shader, +25 SpeedMult, +20% damage), roars (Enderal's Primal
     Force shockwave, harmless, staggers the player and followers within 600 units) and calls 2 adds of its own
     kind (only bosses that pay kill EP, i.e. not scripted quest kills, and never inside the Fog Wood arena).

Writes src/EnemyThreat/EnemyThreatESP/, spid/Zenderal - Enemy Threat_DISTR.ini and tools/boss-adds.json.
Never hand-edit what this writes: change the constants below and rerun. Rerun after EGO, an undead overrider or
Prophecy's stagger effects change.
"""
import glob
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _npcs as N  # noqa: E402

REPO = N.REPO
PATCH = os.path.join(REPO, 'src', 'EnemyThreat')
ESP = os.path.join(PATCH, 'EnemyThreatESP')
SPID = os.path.join(PATCH, 'spid', 'Zenderal - Enemy Threat_DISTR.ini')
ADDS_JSON = os.path.join(HERE, 'boss-adds.json')

OWN = 'Zenderal - Enemy Threat.esp'
PROPHECY = 'Zenderal - Prophecy.esp'
EGO = 'Enderal SE - Gameplay Overhaul.esp'
SK = ':Skyrim.esm'


def fk(local):
    return '%06X:%s' % (local, OWN)


ID = dict(scaling_perk=0x800, boss_perk=0x801, boss_ability=0x802, boss_effect=0x803, stagger_watch=0x804,
          lockout_spell=0x805, lockout_effect=0x806, enrage_spell=0x807, enrage_effect=0x808, roar_spell=0x809,
          roar_effect=0x80A, roar_explosion=0x80B, phase_faction=0x80C, add_bosses=0x80D, add_bases=0x80E)
K = {k: fk(v) for k, v in ID.items()}

# --- tuning (curator 2026-11-13) -----------------------------------------------------------------------------
MAX_POINTS = 30           # Prophecy's cap (ZP_ProphecyMenu.PointsDueAt)
STEP = 3                  # points per step: one step every 9 levels
DEALT_AT_MAX = 0.25       # enemies' damage dealt +25% at 30 points
TAKEN_AT_MAX = 0.30       # enemies' damage taken -30% at 30 points
BOSS_TAKEN = 0.5          # bosses take half damage (~2x health)
BOSS_DEALT = 1.3          # and deal +30%
BOSS_POISE_TAKEN = 1 / 3  # 3x poise
ENRAGE_DEALT = 1.2        # +20% more while enraged
ENRAGE_SPEED = 25         # SpeedMult +25 while enraged
ENRAGE_SECONDS = 600
LOCKOUT_SECONDS = 5       # stagger immunity after a stagger is noticed (the stagger itself ~1-2 s of it)
ROAR_STAGGER = 0.75       # stagger magnitude on the player/followers
ADD_LEVEL_RATIO = 0.7     # an add's level aims at 70% of its boss's
# the script's own constants (EnrageAt 0.5, RoarRadius 600, AddCount 2) are AutoReadOnly in ZET_BossEffect.psc

POINTS_GLOBAL = '000809:' + PROPHECY      # ZP_ProphecyPointsEarned
LOCKOUT_KW = '000B4C:' + PROPHECY         # ZP_StaggerLockout (Prophecy's tools/01 STAGGER_LOCKOUT_KW)
PLAYER_REF = '000014' + SK
FURY_SHADER = '07FA6E' + SK               # _00E_FuryFXShader (Enderal's Rage class: Steel Tempest)
PRIMAL_FORCE = os.path.join(N.REF, 'base-2.1.4.4', 'Skyrim', 'Explosions', '_00E_A2_PrimalForceExp - 066898_Skyrim.esm.yaml')
STAGGER_SRC = os.path.join(N.REF, 'base-2.1.4.4', 'Skyrim', 'MagicEffects', 'StaggerAttackFFContact - 07809B_Skyrim.esm.yaml')
EGO_STAGGER = os.path.join(N.REF, 'mods', 'EGO', 'MagicEffects', 'XionStagger - 001D16_Enderal SE - Gameplay Overhaul.esp.yaml')
SPEEDMULT_SCRIPT = '_00E_UpdateSpeedmult'  # Enderal's own: nudges InventoryWeight so a SpeedMult change applies

# damage keywords a spell must carry (EPMagic_SpellHasKeyword) for the spell entries: EGO's XionMagicDamage set
# (fire, frost, shock, EGO poison/light/psionic, Eldritch) + drain life, FS's Eldritch spells and Prophecy's own
DAMAGE_KEYWORDS = ['01CEAD' + SK, '01CEAE' + SK, '01CEAF' + SK, '0164B1' + SK, '0164B2' + SK,
                   '02F286:Enderal - Forgotten Stories.esm',
                   '001DC7:' + EGO, '001DC9:' + EGO, '001E05:' + EGO,
                   '0008D8:' + PROPHECY, '0008D7:' + PROPHECY, '00082B:' + PROPHECY, '0008D6:' + PROPHECY]

# --- adds ------------------------------------------------------------------------------------------------------
# factions that say nothing about what a creature is (or don't make members allies) never pick an add
BROAD_FACTIONS = {'AnimalFaction', 'BanditVoiceFaction', 'PlayerEnemyFaction', 'BanditFriendFaction',
                  'UndercityFriendFaction', 'EPFaction', 'ImportantNPCs', 'PlayerAlliesFaction',
                  'AnimalIgnoredByEnemiesFaction', 'BossesFaction'}
ADD_SCRIPTS_OK = {'_00E_EPOnDeath', '_00E_CombatSoundtrackScript'}
ADD_EDID_BAD = re.compile(r'(^|_)(MQ|NQ|FS_?NQ|FS_?MQ|FSNQ|SQ|CQ|DLC)\d|Ambush|Summon|Sleep|Sit|Dead|Corpse|Prison|'
                          r'Sklave|Test|Dummy|Uni|Boss|Patrol|Tutorial|Arena|Brawl|Illusion|Ghost|Hallu|Vision|Dream',
                          re.I)
# an add is a generic tier enemy: _NNE_Stem (or _NN_ / NNE_), never _00E_ (Enderal's quest/town namespace) or a
# named sibling like _Dunkel_33_SabatDunkelhand (the Darkhands would each call two Sabats)
ADD_EDID_TIER = re.compile(r'^_?(\d\d)E?_')
# a boss may call another race only when both are people, or when the shared faction is a creature family
CROSS_RACE_FAMILIES = ('Creature_', 'UndeadFaction', 'SpiderFaction')
NO_ADD_RACE = re.compile(r'Atronach|Elemental', re.I)   # Fog Wood: musket hits on an elite Ice Elemental mostly missed
RACE_PLUGINS_OK = ('Skyrim.esm', 'Update.esm', 'Enderal - Forgotten Stories.esm', EGO, 'Undead Creatures Replacer.esp')


def write(sub, text):
    m = re.search(r'^FormKey: (.+?)\s*$', text, re.M)
    e = re.search(r'^EditorID: (\S+)', text, re.M)
    local, plugin = m.group(1).split(':', 1)
    d = os.path.join(ESP, sub)
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, '%s - %s_%s.yaml' % (e.group(1), local, plugin)), 'w', encoding='utf-8',
         newline='\r\n').write(text)


def name(value):
    return 'Name:\n  TargetLanguage: English\n  Value: %s\n' % value


def desc(value=''):
    v = "''" if not value else "'" + value.replace("'", "''") + "'"
    return 'Description:\n  TargetLanguage: English\n  Value: %s\n' % v


def cond(data, value=None, op=None, flags=None, indent=''):
    s = indent + '- MutagenObjectType: ConditionFloat\n'
    if op:
        s += indent + '  CompareOperator: %s\n' % op
    if flags:
        s += indent + '  Flags:\n' + ''.join(indent + '  - %s\n' % f for f in flags)
    s += indent + '  Data:\n' + ''.join(indent + '    %s\n' % line for line in data)
    if value is not None:
        s += indent + '  ComparisonValue: %s\n' % value
    return s


def c_global(op, value, indent):
    return cond(['MutagenObjectType: GetGlobalValueConditionData', 'Global: ' + POINTS_GLOBAL], value, op, indent=indent)


def owner_is_enemy(indent):
    """(hostile to the player OR in combat) AND not a teammate AND not commanded. Skyrim groups an OR with the
    condition after it before applying the ANDs."""
    return (cond(['MutagenObjectType: IsHostileToActorConditionData', 'TargetNpc: ' + PLAYER_REF], 1, flags=['OR'], indent=indent) +
            cond(['MutagenObjectType: IsInCombatConditionData'], 1, indent=indent) +
            cond(['MutagenObjectType: GetPlayerTeammateConditionData'], indent=indent) +
            cond(['MutagenObjectType: IsCommandedActorConditionData'], indent=indent))


def damage_spell_tab(tab):
    s = '  - RunOnTabIndex: %d\n    Conditions:\n' % tab
    for i, kw in enumerate(DAMAGE_KEYWORDS):
        last = i == len(DAMAGE_KEYWORDS) - 1
        s += cond(['MutagenObjectType: EPMagic_SpellHasKeywordConditionData', 'Keyword: ' + kw], 1,
                  flags=None if last else ['OR'], indent='    ')
    return s


def entry(ep, tabs, value, owner=None, spell_tab=None, priority=None):
    s = '- MutagenObjectType: PerkEntryPointModifyValue\n'
    if priority is not None:
        s += '  Priority: %d\n' % priority
    if owner or spell_tab is not None:
        s += '  Conditions:\n'
        if owner:
            s += '  - Conditions:\n' + owner
        if spell_tab is not None:
            s += damage_spell_tab(spell_tab)
    s += '  EntryPoint: %s\n  PerkConditionTabCount: %d\n  Modification: Multiply\n  Value: %s\n' % (ep, tabs, fmt(value))
    return s


def fmt(v):
    s = ('%.4f' % v).rstrip('0').rstrip('.')
    return s if s else '0'


def perk(key, edid, title, text, effects):
    write('Perks', 'FormKey: %s\nEditorID: %s\n%s%sNumRanks: 1\nPlayable: True\nEffects:\n%s' % (
        K[key], edid, name(title), desc(text), effects))


# --- 1. scaling ------------------------------------------------------------------------------------------------
def build_scaling():
    effects = ''
    steps = MAX_POINTS // STEP
    rows = []
    for k in range(1, steps + 1):
        lo = k * STEP
        hi = None if k == steps else lo + STEP
        dealt = 1 + DEALT_AT_MAX * k / steps
        taken = 1 - TAKEN_AT_MAX * k / steps
        rows.append((lo, hi, dealt, taken))
        own = c_global('GreaterThanOrEqualTo', lo, '    ')
        if hi is not None:
            own += c_global('LessThan', hi, '    ')
        own += owner_is_enemy('    ')
        effects += entry('ModAttackDamage', 3, dealt, own)
        effects += entry('ModSpellMagnitude', 3, dealt, own, spell_tab=1)
        effects += entry('ModIncomingDamage', 3, taken, own)
        effects += entry('ModIncomingSpellMagnitude', 2, taken, own, spell_tab=1)
    perk('scaling_perk', 'ZET_ScalingPerk', 'Prophecy\'s Shadow',
         'The world answers the Prophecy: hostile actors deal up to 25% more damage and take up to 30% less, '
         'in steps of 3 Prophecy points earned.', effects)
    return rows


# --- 2. bosses -------------------------------------------------------------------------------------------------
def build_boss_records():
    enraged = cond(['MutagenObjectType: HasMagicEffectConditionData', 'MagicEffect: ' + K['enrage_effect']], 1, indent='    ')
    locked = cond(['MutagenObjectType: HasMagicEffectKeywordConditionData', 'Keyword: ' + LOCKOUT_KW], 1, indent='    ')
    effects = (entry('ModIncomingDamage', 3, BOSS_TAKEN) +
               entry('ModIncomingSpellMagnitude', 2, BOSS_TAKEN, spell_tab=1) +
               entry('ModAttackDamage', 3, BOSS_DEALT) +
               entry('ModSpellMagnitude', 3, BOSS_DEALT, spell_tab=1) +
               entry('ModAttackDamage', 3, ENRAGE_DEALT, enraged) +
               entry('ModSpellMagnitude', 3, ENRAGE_DEALT, enraged, spell_tab=1) +
               entry('ModIncomingStagger', 2, BOSS_POISE_TAKEN) +
               entry('ModIncomingStagger', 2, 0, locked))
    perk('boss_perk', 'ZET_BossPerk', 'Boss', 'Takes half damage, deals 30% more, has three times the poise and '
         'cannot be staggered again for a few seconds after a stagger. Enraged: 20% more damage.', effects)

    script_flags = 'Flags:\n- NoMagnitude\n- NoArea\n- NoDuration\n- HideInUI\n- Painless\n'
    props = lambda pairs: ''.join('    - MutagenObjectType: ScriptObjectProperty\n      Name: %s\n      Object: %s\n' % p
                                  for p in pairs)
    # the boss ability: phase script + stagger watch
    write('MagicEffects', 'FormKey: %s\nEditorID: ZET_BossEffect\nVirtualMachineAdapter:\n  Scripts:\n'
          '  - Name: ZET_BossEffect\n    Properties:\n%s%s%s'
          'Archetype:\n  MutagenObjectType: MagicEffectArchetype\n  Type: Script\nCastType: ConstantEffect\n'
          'DualCastScale: 1\nCastingSoundLevel: Silent\nSounds: []\n%s' % (
              K['boss_effect'],
              props([('EnrageSpell', K['enrage_spell']), ('EnrageEffect', K['enrage_effect']),
                     ('RoarStagger', K['roar_spell']), ('RoarExplosion', K['roar_explosion']),
                     ('PhaseFaction', K['phase_faction']), ('AddBosses', K['add_bosses']),
                     ('AddBases', K['add_bases']), ('PlayerRef', PLAYER_REF)]),
              name('Boss'), script_flags, desc()))
    write('MagicEffects', 'FormKey: %s\nEditorID: ZET_StaggerWatchEffect\nVirtualMachineAdapter:\n  Scripts:\n'
          '  - Name: ZET_StaggerWatchEffect\n    Properties:\n%s%s%s'
          'Archetype:\n  MutagenObjectType: MagicEffectArchetype\n  Type: Script\nCastType: ConstantEffect\n'
          'DualCastScale: 1\nCastingSoundLevel: Silent\nSounds: []\n%s' % (
              K['stagger_watch'], props([('LockoutSpell', K['lockout_spell'])]), name('Boss Poise'), script_flags, desc()))
    write('Spells', 'FormKey: %s\nEditorID: ZET_BossAbility\n%sMenuDisplayObject: 0435A5%s\nEquipmentType: 013F44%s\n%s'
          'Type: Ability\nCastType: ConstantEffect\nEffects:\n'
          '- BaseEffect: %s\n  Data: {}\n'
          '- BaseEffect: %s\n  Data: {}\n  Conditions:\n%s' % (
              K['boss_ability'], name('Boss'), SK, SK, desc(), K['boss_effect'], K['stagger_watch'],
              cond(['MutagenObjectType: IsStaggeredConditionData'], 1, indent='  ')))

    # stagger lockout: a timed effect carrying Prophecy's ZP_StaggerLockout keyword
    write('MagicEffects', 'FormKey: %s\nEditorID: ZET_StaggerLockoutEffect\n%sKeywords:\n- %s\n'
          'Flags:\n- Recover\n- NoMagnitude\n- NoArea\n- HideInUI\n- Painless\n'
          'Archetype:\n  MutagenObjectType: MagicEffectArchetype\n  Type: Script\nCastType: FireAndForget\n'
          'DualCastScale: 1\nCastingSoundLevel: Silent\nSounds: []\n%s' % (
              K['lockout_effect'], name('Steadied'), LOCKOUT_KW, desc()))
    write('Spells', 'FormKey: %s\nEditorID: ZET_StaggerLockout\n%sMenuDisplayObject: 0435A5%s\nEquipmentType: 013F44%s\n%s'
          'Flags:\n- NoAbsorbOrReflect\nCastType: FireAndForget\nEffects:\n- BaseEffect: %s\n  Data:\n    Duration: %d\n' % (
              K['lockout_spell'], name('Steadied'), SK, SK, desc(), K['lockout_effect'], LOCKOUT_SECONDS))

    # enrage: Enderal's own SpeedMult buff shape (_00E_A1_QyraiStanceSpeedMEHidden 067247 + its _00E_UpdateSpeedmult)
    write('MagicEffects', 'FormKey: %s\nEditorID: ZET_EnrageEffect\nVirtualMachineAdapter:\n  Scripts:\n  - Name: %s\n'
          '%sMenuDisplayObject: 0435A5%s\nFlags:\n- Recover\n- NoArea\n- FXPersist\n- HideInUI\n'
          'HitShader: %s\nArchetype:\n  MutagenObjectType: MagicEffectPeakValueModArchetype\n  ActorValue: SpeedMult\n'
          'CastType: FireAndForget\nDualCastScale: 1\nCastingSoundLevel: Silent\nSounds: []\n%s' % (
              K['enrage_effect'], SPEEDMULT_SCRIPT, name('Enraged'), SK, FURY_SHADER, desc()))
    write('Spells', 'FormKey: %s\nEditorID: ZET_Enrage\n%sMenuDisplayObject: 0435A5%s\nEquipmentType: 013F44%s\n%s'
          'Flags:\n- NoAbsorbOrReflect\nCastType: FireAndForget\nEffects:\n- BaseEffect: %s\n  Data:\n'
          '    Magnitude: %d\n    Duration: %d\n' % (
              K['enrage_spell'], name('Enraged'), SK, SK, desc(), K['enrage_effect'], ENRAGE_SPEED, ENRAGE_SECONDS))

    # roar: a verbatim copy of the vanilla stagger effect (target actor, as Prophecy's droid copy) ...
    t = open(STAGGER_SRC, encoding='utf-8-sig').read().replace('\r\n', '\n')
    t = re.sub(r'^Name:\n  TargetLanguage: English\n(?:  .*\n)*', name('Boss Roar'), t, count=1, flags=re.M)
    t, n = re.subn(r'^TargetType: Touch$', 'TargetType: TargetActor', t, flags=re.M)
    assert n == 1, 'StaggerAttackFFContact layout changed'
    t = re.sub(r'^Description:\n  TargetLanguage: English\n(?:  .*\n)*', desc(), t, count=1, flags=re.M)
    t = re.sub(r'^Version2: .*\n', '', t, flags=re.M)
    t = t.replace('FormKey: 07809B' + SK, 'FormKey: ' + K['roar_effect']).replace('EditorID: StaggerAttackFFContact',
                                                                                  'EditorID: ZET_RoarStaggerEffect')
    assert 'Type: Stagger' in t and K['roar_effect'] in t
    write('MagicEffects', t)
    write('Spells', 'FormKey: %s\nEditorID: ZET_RoarStagger\n%sMenuDisplayObject: 0435A5%s\nEquipmentType: 013F44%s\n%s'
          'Flags:\n- NoAbsorbOrReflect\nCastType: FireAndForget\nTargetType: TargetActor\nEffects:\n'
          '- BaseEffect: %s\n  Data:\n    Magnitude: %s\n' % (
              K['roar_spell'], name('Boss Roar'), SK, SK, desc(), K['roar_effect'], fmt(ROAR_STAGGER)))
    # ... and Enderal's Primal Force explosion as pure visuals + sound: no enchantment, no screen effect, no force
    t = open(PRIMAL_FORCE, encoding='utf-8-sig').read().replace('\r\n', '\n')
    for field in ('ObjectEffect', 'ImageSpaceModifier', 'ISRadius', 'Version2'):
        t, n = re.subn(r'^%s: .*\n' % field, '', t, flags=re.M)
        assert n == 1, (field, 'Primal Force layout changed')
    t, n = re.subn(r'^Force: .*$', 'Force: 0', t, flags=re.M)
    assert n == 1
    t = t.replace('FormKey: 066898' + SK, 'FormKey: ' + K['roar_explosion']).replace(
        'EditorID: _00E_A2_PrimalForceExp', 'EditorID: ZET_RoarExplosion')
    assert K['roar_explosion'] in t and 'Damage:' not in t
    write('Explosions', t)

    write('Factions', 'FormKey: %s\nEditorID: ZET_BossPhaseFaction\nFlags:\n- HiddenFromPC\n' % K['phase_faction'])


def build_ego_stagger_guard():
    """EGO casts XionStagger on every player power-attack hit (XionPowerStagger 001DBD): the lockout stops it too."""
    t = open(EGO_STAGGER, encoding='utf-8-sig').read().replace('\r\n', '\n')
    assert 'Type: Stagger' in t and '\nConditions:' not in t, 'EGO XionStagger changed: review the guard'
    t = t.rstrip('\n') + '\nConditions:\n' + cond(['MutagenObjectType: HasMagicEffectKeywordConditionData',
                                                   'Keyword: ' + LOCKOUT_KW])
    write('MagicEffects', t)


# --- adds ------------------------------------------------------------------------------------------------------
def pick_adds(npcs, factions, packages, bosses, races):
    resolved = {k: N.resolve(npcs, k) for k in npcs}
    humanoid = lambda race: races.get(race, ('', False))[1]

    def family(r):
        out = []
        for f in r['factions']:
            info = factions.get(f)
            if not info or not info['self_ally']:
                continue
            if info['edid'] in BROAD_FACTIONS or info['edid'].startswith('IsVoiceActor'):
                continue
            out.append(f)
        # the most specific first: a Creature_* faction says what the creature is
        return sorted(out, key=lambda f: (not factions[f]['edid'].startswith('Creature_'), factions[f]['edid']))

    def usable(r):
        if N.BOSS_KEYWORD in r['keywords'] or not r['level']:
            return False
        if '_00E_EPOnDeath' not in r['scripts'] or not r['reward']:
            return False
        if set(r['scripts']) - ADD_SCRIPTS_OK:
            return False
        if {'Unique', 'Essential', 'Protected'} & set(r['flags']):
            return False
        tier = ADD_EDID_TIER.match(r['edid'])
        if not tier or tier.group(1) == '00' or ADD_EDID_BAD.search(r['edid']):
            return False
        if not r['race'] or not r['race'].endswith(RACE_PLUGINS_OK) or NO_ADD_RACE.search(races.get(r['race'], ('', 0))[0]):
            return False
        if any(p in packages for p in r['packages']):
            return False
        return True

    pool = [r for r in resolved.values() if usable(r)]
    table = []
    for b in bosses:
        fam = family(b)
        row = {'boss': b['fk'], 'edid': b['edid'], 'name': b['name'], 'level': b['level'], 'add': None,
               'why': ''}
        if '_00E_EPOnDeath' not in b['scripts'] or not b['reward']:
            row['why'] = 'scripted kill (no kill EP): no adds'
        elif not fam:
            row['why'] = 'no family faction'
        else:
            target = max(1, round(b['level'] * ADD_LEVEL_RATIO))
            for f in fam:
                cands = [r for r in pool if f in r['factions'] and r['level'] <= b['level']]
                if not cands:
                    continue
                same = [r for r in cands if r['race'] == b['race']]
                if same:
                    use = same
                elif factions[f]['edid'].startswith(CROSS_RACE_FAMILIES):
                    use = cands
                else:   # people only call people
                    use = [r for r in cands if humanoid(r['race']) and humanoid(b['race'])]
                if not use:
                    continue
                best = min(use, key=lambda r: (abs(r['level'] - target), -r['level'], r['fk']))
                row.update(add=best['fk'], add_edid=best['edid'], add_name=best['name'], add_level=best['level'],
                           faction=factions[f]['edid'], same_race=bool(same))
                break
            if not row['add']:
                row['why'] = 'no usable add in ' + ', '.join(factions[f]['edid'] for f in fam)
        table.append(row)
    return table


def main():
    for d in glob.glob(os.path.join(ESP, '*')):
        if os.path.isdir(d):
            shutil.rmtree(d)
    npcs = N.load_npcs()
    factions = N.load_factions()
    packages = N.load_package_overrides()
    bosses = sorted((N.resolve(npcs, k) for k in npcs if N.BOSS_KEYWORD in N.resolve(npcs, k)['keywords']),
                    key=lambda r: (r['level'] or 0, r['fk']))
    assert len(bosses) == 91, '%d bosses (was 91 on 2026-11-13): check the overriders' % len(bosses)

    rows = build_scaling()
    build_boss_records()
    build_ego_stagger_guard()
    table = pick_adds(npcs, factions, packages, bosses, N.load_races())
    with_adds = [r for r in table if r['add']]
    write('FormLists', 'FormKey: %s\nEditorID: ZET_AddBosses\nItems:\n%s' % (
        K['add_bosses'], ''.join('- %s\n' % r['boss'] for r in with_adds)))
    write('FormLists', 'FormKey: %s\nEditorID: ZET_AddBases\nItems:\n%s' % (
        K['add_bases'], ''.join('- %s\n' % r['add'] for r in with_adds)))
    json.dump(table, open(ADDS_JSON, 'w', encoding='utf-8', newline='\n'), indent=1, ensure_ascii=False)

    os.makedirs(os.path.dirname(SPID), exist_ok=True)
    open(SPID, 'w', encoding='utf-8', newline='\r\n').write(
        '; Zenderal - Enemy Threat (generated by src/EnemyThreat/tools/01-build-enemy-threat.py)\n'
        '; ----------------------------------------------------------------------------\n'
        '; Every NPC: ZET_ScalingPerk (0x800). Its entries only act on hostile/in-combat actors that are neither the\n'
        '; player\'s teammates nor summons, and only once the player has earned Prophecy points: up to +%d%% damage\n'
        '; dealt and -%d%% damage taken at %d points, in steps of %d. SPID never targets the player.\n'
        '; Every NPC with ActorTypeBoss (%d in Enderal 2.1 + EGO, all on their own record): ZET_BossPerk (0x801) and\n'
        '; ZET_BossAbility (0x802). Check po3_SpellPerkItemDistributor.log: the boss lines should reach %d bases.\n\n'
        'Perk = 0x800~%s\n'
        'Perk = 0x801~%s|ActorTypeBoss\n'
        'Spell = 0x802~%s|ActorTypeBoss\n' % (
            round(DEALT_AT_MAX * 100), round(TAKEN_AT_MAX * 100), MAX_POINTS, STEP, len(bosses), len(bosses),
            OWN, OWN, OWN))

    print('scaling steps (points from, to, dealt, taken):')
    for r in rows:
        print('  %2d-%-4s x%.3f  x%.3f' % (r[0], r[1] if r[1] else '', r[2], r[3]))
    print('%d bosses, %d with adds:' % (len(bosses), len(with_adds)))
    for r in table:
        if r['add']:
            print('  %3d %-34s -> %3d %-40s %s%s' % (r['level'], r['name'][:34], r['add_level'], r['add_edid'][:40],
                                                    r['faction'], '' if r['same_race'] else ' (other race)'))
    for r in table:
        if not r['add']:
            print('  %3d %-34s    %s' % (r['level'] or 0, (r['name'] or r['edid'])[:34], r['why']))


if __name__ == '__main__':
    main()
