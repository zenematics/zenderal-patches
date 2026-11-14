"""Vagrant light armor rework (curator, 2026-11-13): four EGO perks get an Ordinator Evasion idea each.

  Wind Walker   069CF5  + As a Leaf: half damage from power attacks while sprinting
  Perfect Fit   069CF8  + spells cost 10% less (Requiem/LoreRim's Agile Spellcasting idea)
  Snakeblood    069CFA  + Into the Maelstrom: 10% less damage from attackers other than the last hostile actor
  High Dexterity 069CFC + Wardancer: +20% attack and critical damage, lost for 6 s after an unblocked hostile hit
                          (global ZEN_PO_HighDexterityStruck 804, set by ZEN_PO_HighDexterityWardancerSC on
                          ability 805 / effect 806)

Every new entry uses EGO's light armor rule ("no heavy armor worn", WornHasKeyword ArmorHeavy 06BBD2 == 0) in
place of Ordinator's all-slots check, so the tree keeps one rule. The perks and their Hero Menu MESGs are EGO's
winning records (live scan: EGO wins all eight) copied verbatim with entries appended / text replaced; each text
replacement must match exactly once.

Run from the repo root: python -I src/PerkOverhaul/tools/02-build-light-armor.py
"""
import glob
import os
import sys

EGO = 'reference/mods/EGO'
OUT = 'src/PerkOverhaul/PerkOverhaulESP'
MOD = 'Zenderal - Perk Overhaul.esp'
STRUCK = f'000804:{MOD}'      # GLOB ZEN_PO_HighDexterityStruck
ABILITY = f'000805:{MOD}'     # SPEL ZEN_PO_HighDexterityWardancerAb
EFFECT = f'000806:{MOD}'      # MGEF ZEN_PO_HighDexterityWardancerME

NO_HEAVY = ('    - MutagenObjectType: ConditionFloat\n'
            '      Data:\n'
            '        MutagenObjectType: WornHasKeywordConditionData\n'
            '        Keyword: 06BBD2:Skyrim.esm\n')


def entry(entry_point, tabs, value, owner_conds, tab1_conds=''):
    t = ('- MutagenObjectType: PerkEntryPointModifyValue\n'
         '  Conditions:\n'
         '  - Conditions:\n' + owner_conds)
    if tab1_conds:
        t += '  - RunOnTabIndex: 1\n    Conditions:\n' + tab1_conds
    return t + (f'  EntryPoint: {entry_point}\n  PerkConditionTabCount: {tabs}\n'
                f'  Modification: Multiply\n  Value: {value}\n')


AS_A_LEAF = entry('ModIncomingDamage', 3, 0.5,
                  '    - MutagenObjectType: ConditionFloat\n      Data:\n'
                  '        MutagenObjectType: IsSprintingConditionData\n      ComparisonValue: 1\n' + NO_HEAVY,
                  '    - MutagenObjectType: ConditionFloat\n      Data:\n'
                  '        MutagenObjectType: IsPowerAttackingConditionData\n      ComparisonValue: 1\n')
AGILE_CASTING = entry('ModSpellCost', 2, 0.9, NO_HEAVY)
MAELSTROM = entry('ModIncomingDamage', 3, 0.9, NO_HEAVY,
                  '    - MutagenObjectType: ConditionFloat\n      Data:\n'
                  '        MutagenObjectType: IsLastHostileActorConditionData\n')
NOT_STRUCK = ('    - MutagenObjectType: ConditionFloat\n      Data:\n'
              '        MutagenObjectType: GetGlobalValueConditionData\n'
              f'        Global: {STRUCK}\n')
WARDANCER = (entry('ModAttackDamage', 3, 1.2, NO_HEAVY + NOT_STRUCK)
             + entry('CalculateMyCriticalHitDamage', 3, 1.2, NO_HEAVY + NOT_STRUCK)
             + f'- MutagenObjectType: PerkAbilityEffect\n  Ability: {ABILITY}\n')

PERKS = {'069CF5': AS_A_LEAF, '069CF8': AGILE_CASTING, '069CFA': MAELSTROM, '069CFC': WARDANCER}

# MESG FormID -> (old, new) on EGO's English description ('%%' is how a MESG shows a percent sign)
TEXTS = {
    '069D8F': ('and enemies can no longer stagger you while sprinting.',
               'and enemies can no longer stagger you while sprinting. While sprinting, you also take 50%% less '
               'damage from power attacks.'),
    '069D94': ('you receive an armor bonus of 30%%.',
               'you receive an armor bonus of 30%% and your spells cost 10%% less.'),
    '069D97': ('caused by poisons.',
               'caused by poisons. If you are not wearing heavy armor, attacks from enemies other than the one you '
               'last fought deal 10%% less damage, so a crowd hurts less.'),
    '069D9A': ('If you are not wearing heavy armor, there is a chance of 15%% that the damage of a melee attack is '
               'completely intercepted.',
               'If you are not wearing heavy armor, there is a chance of 15%% (25%% with a four-piece light armor '
               'set) that the damage of an incoming attack is completely intercepted, and you deal 20%% more damage '
               'and critical damage. The damage bonus is lost for 6 seconds whenever an enemy\'s attack or spell '
               'hits you unblocked.'),
}

NEW_RECORDS = {
    f'Globals/ZEN_PO_HighDexterityStruck - 000804_{MOD}.yaml':
        'MutagenObjectType: GlobalShort\n'
        f'FormKey: {STRUCK}\n'
        'EditorID: ZEN_PO_HighDexterityStruck\n'
        'Data: 0\n',
    f'Spells/ZEN_PO_HighDexterityWardancerAb - 000805_{MOD}.yaml':
        f'FormKey: {ABILITY}\n'
        'EditorID: ZEN_PO_HighDexterityWardancerAb\n'
        'Name:\n  TargetLanguage: English\n  Value: High Dexterity\n'
        'MenuDisplayObject: 0435A5:Skyrim.esm\n'
        'EquipmentType: 013F44:Skyrim.esm\n'
        "Description:\n  TargetLanguage: English\n  Value: ''\n"
        'Type: Ability\n'
        f'Effects:\n- BaseEffect: {EFFECT}\n  Data: {{}}\n',
    f'MagicEffects/ZEN_PO_HighDexterityWardancerME - 000806_{MOD}.yaml':
        f'FormKey: {EFFECT}\n'
        'EditorID: ZEN_PO_HighDexterityWardancerME\n'
        'VirtualMachineAdapter:\n  Scripts:\n  - Name: ZEN_PO_HighDexterityWardancerSC\n    Properties:\n'
        '    - MutagenObjectType: ScriptFloatProperty\n      Name: LockSeconds\n      Data: 6\n'
        '    - MutagenObjectType: ScriptObjectProperty\n      Name: ZEN_PO_HighDexterityStruck\n'
        f'      Object: {STRUCK}\n'
        'Name:\n  TargetLanguage: English\n  Value: High Dexterity\n'
        'MenuDisplayObject: 0435A5:Skyrim.esm\n'
        'Flags:\n- HideInUI\n'
        'Archetype:\n  MutagenObjectType: MagicEffectArchetype\n  Type: Script\n'
        'DualCastScale: 1\nCastingSoundLevel: Normal\nSounds: []\n'
        "Description:\n  TargetLanguage: English\n  Value: ''\n",
}


def ego(kind, fid):
    hits = glob.glob(os.path.join(EGO, kind, f'* - {fid}_Skyrim.esm.yaml'))
    if len(hits) != 1:
        sys.exit(f'{kind} {fid}: {len(hits)} EGO records')
    return hits[0]


def write(rel, text):
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w', encoding='utf-8', newline='').write(text.replace('\n', '\r\n'))


def main():
    for fid, extra in PERKS.items():
        src = ego('Perks', fid)
        text = open(src, encoding='utf-8', newline='').read().replace('\r\n', '\n')
        if '\nEffects:\n' not in text or not text.endswith('\n'):
            sys.exit(f'{fid}: unexpected shape')
        if 'ZEN_PO' in text or STRUCK in text:
            sys.exit(f'{fid}: already patched?')
        write(os.path.join('Perks', os.path.basename(src)), text + extra)
        print(f'PERK {fid}: +{extra.count("MutagenObjectType: PerkEntryPoint") + extra.count("PerkAbilityEffect")} entries')
    for fid, (old, new) in TEXTS.items():
        src = ego('Messages', fid)
        text = open(src, encoding='utf-8', newline='').read().replace('\r\n', '\n')
        head, sep, rest = text.partition('\nName:')
        if head.count(old) != 1:
            sys.exit(f'MESG {fid}: {old!r} matched {head.count(old)}x')
        write(os.path.join('Messages', os.path.basename(src)), head.replace(old, new) + sep + rest)
        print(f'MESG {fid}: text replaced')
    for rel, text in NEW_RECORDS.items():
        write(rel, text)
        print(f'new  {rel.split(" - ")[0]}')


if __name__ == '__main__':
    main()
