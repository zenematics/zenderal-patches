"""Zenderal - Flintlock Overhaul: pistol damage + bow-perk scaling. GENERATED records - never hand-edit
the ObjectEffects/, Weapons/, Statics/, MagicEffects/, Keywords/ or Perks/ folders; re-run this instead.

A Gentleman's Flintlock Armoury fires a staff enchantment (`PMPistolShot`, flat 100-300 health damage)
shared four ways across eight pistols. This script:
  * gives each pistol its own enchantment (0x804-0x80B), copied verbatim from the one it used, with the
    PMPistolShot magnitude set to MULT x the pistol's own Damage stat (the author's tier ranking), which
    puts each pistol just under the Ordo Legionis (Enderal) musket of its tier (weapon + ammo). That magnitude is the Archery-50 value, which is what NPCs fire;
  * overrides the eight weapons to point at them, and their eight
    FirstPersonModel statics (the equipped model in both views) at the rotated meshes for Loop's pistol
    animations (records otherwise verbatim);
  * does the same for Loop's four Hunter Pistols (0x817-0x81A; their own models stay);
  * tags PMPistolShot with keyword ZP_FlintlockShot (0x80C) - MGEF verbatim + Keywords;
  * builds hidden perk ZP_FlintlockArcheryScaling (0x80D) that the player script adds: x0.5 then
    x(1 + Archery*0.02) = bow skill scaling (fDamagePCSkillMin 0.5 .. fDamagePCSkillMax 1.5), Fortify
    Archery (MarksmanModifier, as PerkSkillBoosts does for bows), and every bow-damage talent, with the
    talent's own owner/target conditions (EGO's winning records).

Run from the repo root: python -I src/FlintlockOverhaul/tools/01-build-damage.py
"""
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
SRC = os.path.join(ROOT, 'reference', 'mods', 'FlintlockPack')
OUT = os.path.join(ROOT, 'src', 'FlintlockOverhaul', 'FlintlockOverhaulESP')
ME = 'Zenderal - Flintlock Overhaul.esp'
FP = 'AdventurerFlintlockPack.esp'
EGO = 'Enderal SE - Gameplay Overhaul.esp'

MULT = 1.2   # curator 2026-10-12: each pistol just under the Ordo musket of its tier (was 1.5 * 1.17)
SHOT_MGEF = '000802:' + FP

# pistol FormID -> new enchantment FormID (contiguous block 0x804-0x80B, in weapon FormID order)
PISTOLS = ['000816', '000817', '000818', '000819', '000834', '000838', '000839', '00083A']
ENCH_IDS = ['%06X' % (0x804 + i) for i in range(len(PISTOLS))]
MODEL_PREFIX = 'PowderMagePack\\weapons\\'
LOOP_MODEL_PREFIX = 'Zenderal\\LoopPistols\\'
# EitherHand 013F44 is the pack's own value: Loop's clips serve the left hand and mirrored copies the right hand
# (src/LoopPistolAnims). LeftHand 013F43 (reference/base/Skyrim/EquipTypes) if the right hand is ever dropped.
EQUIP_TYPE = '013F44:Skyrim.esm'
KYWD_ID = '00080C'
PERK_ID = '00080D'

# Loop's "Simple Pistol Shooting Animation" ships four example Hunter Pistols (staves on soul gems, craftable at any
# forge since the player starts with DwarvenSmithing). Curator 2026-10-22: every pistol runs on Flintlock Bullets, so
# they get the same treatment: a shot enchantment copied from the Flintlock Pistol's (PMPistolShot, so the perk
# scales it) at the pack's lower tier magnitudes, and the weapon pointed at it. Their own mesh/animations stay.
LOOP_SRC = os.path.join(ROOT, 'reference', 'mods', 'LoopPistol')
LOOP = 'Pistol animation by Loop.esp'
TEMPLATE_PISTOL = '000838'   # Flintlock Pistol: its generated enchantment is the template
LOOP_PISTOLS = [  # Loop weapon, new enchantment, magnitude (Archery 50) = Flintlock / Priest's / Officer's / Aristocrat's
    ('000802', '000817', 10.8),
    ('00080B', '000818', 14.4),
    ('00080C', '000819', 18.0),
    ('00080D', '00081A', 21.6),
]


def read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


def write(folder, name, text):
    d = os.path.join(OUT, folder)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, name), 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


def find(folder, fid):
    hits = [f for f in os.listdir(os.path.join(SRC, folder)) if ' - %s_' % fid in f]
    if len(hits) != 1:
        sys.exit('expected one %s record %s, found %r' % (folder, fid, hits))
    return os.path.join(SRC, folder, hits[0])


def sub1(pattern, repl, text, what):
    new, n = re.subn(pattern, repl, text, flags=re.M)
    if n != 1:
        sys.exit('%s: expected 1 replacement, got %d' % (what, n))
    return new


# clean the generated folders so a re-run never leaves stale files
for folder in ('ObjectEffects', 'Weapons', 'Statics', 'MagicEffects', 'Keywords', 'Perks'):
    d = os.path.join(OUT, folder)
    if os.path.isdir(d):
        for f in os.listdir(d):
            os.remove(os.path.join(d, f))

table = []
for pid, eid in zip(PISTOLS, ENCH_IDS):
    wpath = find('Weapons', pid)
    w = read(wpath)
    name = re.search(r'^Name:\n  TargetLanguage: English\n  Value: (.+)$', w, re.M).group(1)
    dmg = int(re.search(r'^BasicStats:\n(?:  .*\n)*?  Damage: (\d+)$', w, re.M).group(1))
    old_ench = re.search(r'^ObjectEffect: (\S+)$', w, re.M).group(1)
    if not old_ench.endswith(':' + FP):
        sys.exit('%s: unexpected enchantment %s' % (pid, old_ench))

    # --- enchantment: verbatim copy of the one the pistol used, new FormKey/EditorID, new magnitude
    e = read(find('ObjectEffects', old_ench.split(':')[0]))
    old_edid = re.search(r'^EditorID: (\S+)$', e, re.M).group(1)
    edid = 'ZP_FlintlockShot_' + re.sub(r'\W', '', name)
    e = sub1(r'^FormKey: .*$', 'FormKey: %s:%s' % (eid, ME), e, eid + ' FormKey')
    e = sub1(r'^EditorID: .*$', 'EditorID: ' + edid, e, eid + ' EditorID')
    mag = round(MULT * dmg, 2)
    e = sub1(r'(- BaseEffect: %s\n  Data:\n    Magnitude: )[\d.]+$' % re.escape(SHOT_MGEF),
             r'\g<1>%s' % mag, e, eid + ' shot magnitude')
    write('ObjectEffects', '%s - %s_%s.yaml' % (edid, eid, ME), e)
    if pid == TEMPLATE_PISTOL:
        template_ench = e

    # --- weapon: verbatim except the enchantment (EQUIP_TYPE is the pack's own EitherHand)
    w = sub1(r'^ObjectEffect: .*$', 'ObjectEffect: %s:%s' % (eid, ME), w, pid + ' ObjectEffect')
    w = sub1(r'^EquipmentType: .*$', 'EquipmentType: ' + EQUIP_TYPE, w, pid + ' EquipmentType')
    write('Weapons', os.path.basename(wpath), w)

    # --- equipped model: the FirstPersonModel static. The game draws an equipped weapon that has one from
    # this static in THIRD person too (verified in game 2026-10-17: 3x-scaled copies at the WEAP Model path
    # changed nothing, 3x copies at the static's path turned the held pistol giant); the WEAP Model is only
    # the world/dropped model and stays original (its collision matches). The staff meshes need rotated
    # copies (barrel on +Y), which LoopPistolAnims/tools/02 writes into the `Zenderal - Loop Pistol
    # Animations` MO2 mod. First person draws the same static, so it gets the rotated mesh as well.
    stat = re.search(r'^FirstPersonModel: (\S+)$', w, re.M).group(1)
    if not stat.endswith(':' + FP):
        sys.exit('%s: unexpected FirstPersonModel %s' % (pid, stat))
    spath = find('Statics', stat.split(':')[0])
    s = sub1(r'^(  File: )%s(\S+\.nif)$' % re.escape(MODEL_PREFIX),
             r'\g<1>%s\g<2>' % LOOP_MODEL_PREFIX.replace('\\', '\\\\'), read(spath), stat + ' Model')
    write('Statics', os.path.basename(spath), s)
    table.append((name, dmg, old_edid, mag))

# --- Loop's Hunter Pistols: template enchantment with their own magnitude; weapon verbatim except the enchantment
for wid, eid, mag in LOOP_PISTOLS:
    hits = [f for f in os.listdir(os.path.join(LOOP_SRC, 'Weapons')) if ' - %s_' % wid in f]
    if len(hits) != 1:
        sys.exit('expected one Loop weapon %s, found %r' % (wid, hits))
    w = read(os.path.join(LOOP_SRC, 'Weapons', hits[0]))
    name = re.search(r'^Name:\n  TargetLanguage: English\n  Value: (.+)$', w, re.M).group(1)
    if 'Data:\n  AnimationType: Staff' not in w:
        sys.exit('%s: not a staff' % wid)
    edid = 'ZP_FlintlockShot_' + re.sub(r'\W', '', name)
    e = sub1(r'^FormKey: .*$', 'FormKey: %s:%s' % (eid, ME), template_ench, eid + ' FormKey')
    e = sub1(r'^EditorID: .*$', 'EditorID: ' + edid, e, eid + ' EditorID')
    e = sub1(r'(- BaseEffect: %s\n  Data:\n    Magnitude: )[\d.]+$' % re.escape(SHOT_MGEF),
             r'\g<1>%s' % mag, e, eid + ' shot magnitude')
    write('ObjectEffects', '%s - %s_%s.yaml' % (edid, eid, ME), e)
    w = sub1(r'^ObjectEffect: .*$', 'ObjectEffect: %s:%s' % (eid, ME), w, wid + ' ObjectEffect')
    write('Weapons', hits[0], w)
    table.append((name, 0, 'Loop', mag))

# --- keyword
write('Keywords', 'ZP_FlintlockShot - %s_%s.yaml' % (KYWD_ID, ME),
      'FormKey: %s:%s\nEditorID: ZP_FlintlockShot\n' % (KYWD_ID, ME))

# --- PMPistolShot: verbatim + our keyword
mpath = find('MagicEffects', '000802')
m = read(mpath)
if '\nKeywords:' in m:
    sys.exit('PMPistolShot already has keywords - merge instead of inserting')
m = sub1(r'^(MenuDisplayObject: .*)$', r'\1\nKeywords:\n- %s:%s' % (KYWD_ID, ME), m, 'MGEF keywords')
write('MagicEffects', os.path.basename(mpath), m)

# --- perk
SPELL_TAB = """  - RunOnTabIndex: 1
    Conditions:
    - MutagenObjectType: ConditionFloat
      Data:
        MutagenObjectType: EPMagic_SpellHasKeywordConditionData
        Keyword: %s:%s
      ComparisonValue: 1
""" % (KYWD_ID, ME)


def has_perk(perk, value=1):
    cv = '      ComparisonValue: 1\n' if value else ''
    return ("    - MutagenObjectType: ConditionFloat\n      Data:\n"
            "        MutagenObjectType: HasPerkConditionData\n        Perk: %s\n%s" % (perk, cv))


def entry(value, owner='', target='', mod='Multiply'):
    s = '- MutagenObjectType: PerkEntryPointModifyValue\n  Conditions:\n'
    if owner:
        s += '  - Conditions:\n' + owner
    s += SPELL_TAB
    if target:
        s += '  - RunOnTabIndex: 2\n    Conditions:\n' + target
    s += '  EntryPoint: ModSpellMagnitude\n  PerkConditionTabCount: 3\n  Modification: %s\n  Value: %s\n' % (mod, value)
    return s


def av_entry(av, mult):
    return ('- MutagenObjectType: PerkEntryPointModifyActorValue\n  Conditions:\n' + SPELL_TAB +
            '  EntryPoint: ModSpellMagnitude\n  PerkConditionTabCount: 3\n'
            '  ActorValue: %s\n  Value: %s\n  Modification: MultiplyOnePlusAVMult\n' % (av, mult))


effects = ''.join([
    entry(0.5),                                     # skill 0 = x0.5 ...
    av_entry('Archery', 0.02),                      # ... skill 100 = x1.5, like a bow
    av_entry('MarksmanModifier', 0.01),             # Fortify Archery (PerkSkillBoosts' bow entry)
    # Strong Bowstring I: only without rank II (EGO 069CF0 conditions on NOT having 085AB5)
    entry(1.15, has_perk('069CF0:Skyrim.esm') + has_perk('085AB5:Skyrim.esm', 0)),
    entry(1.29, has_perk('085AB5:Skyrim.esm')),     # Strong Bowstring II
    entry(1.18, has_perk('069CD2:Skyrim.esm') +     # Concentration, at >= 80% stamina
          "    - MutagenObjectType: ConditionFloat\n      CompareOperator: GreaterThanOrEqualTo\n"
          "      Data:\n        MutagenObjectType: GetActorValuePercentConditionData\n"
          "        ActorValue: Stamina\n      ComparisonValue: 0.8\n"),
    entry(1.1, has_perk('069CD7:Skyrim.esm'),       # Expert Locksmith, same target filter as EGO's
          target="    - MutagenObjectType: ConditionFloat\n      Data:\n"
                 "        MutagenObjectType: HasKeywordConditionData\n        Keyword: 001DA7:%s\n"
                 "      ComparisonValue: 1\n"
                 "    - MutagenObjectType: ConditionFloat\n      Data:\n"
                 "        MutagenObjectType: HasKeywordConditionData\n        Keyword: 0D205E:Skyrim.esm\n" % EGO),
    entry(1.15, has_perk('001CAF:' + EGO)),         # EGO's bow bonus (on the Player record)
])
perk = ('FormKey: %s:%s\nEditorID: ZP_FlintlockArcheryScaling\nName:\n  TargetLanguage: English\n'
        '  Value: Flintlock Marksmanship\nDescription:\n  TargetLanguage: English\n  Value: \'\'\n'
        'Hidden: True\nNumRanks: 1\nPlayable: True\nEffects:\n' % (PERK_ID, ME)) + effects
if perk.count('EntryPoint: ModSpellMagnitude') != 8:
    sys.exit('perk: expected 8 entries')
write('Perks', 'ZP_FlintlockArcheryScaling - %s_%s.yaml' % (PERK_ID, ME), perk)

if len(table) != 8 + len(LOOP_PISTOLS):
    sys.exit('expected 12 pistols')
print('%-34s %4s  %-22s %8s %8s %8s' % ('pistol', 'dmg', 'old enchantment', 'Arch 0', 'Arch 50', 'Arch 100'))
for name, dmg, old, mag in table:
    print('%-34s %4d  %-22s %8.1f %8.1f %8.1f' % (name, dmg, old, mag * 0.5, mag, mag * 1.5))
