"""Generate the Owl Bow's records (working name; curator 2026-11-16) - never hand-edit the YAML this writes.

  800 WEAP ZP_OwlBow             <- Firewind Bow 054029 (Zenderal - Pretty Armory EGO Patch's record: Real Bows'
           Daedric bow, Pretty's model). Name, Model = tools/01's OwlBow.nif, its bounds, first-person static 801,
           unique, BOW_DAMAGE / BOW_CRIT (the list's unique bows run 20-27: Moonwind 22, Mad Hermit 23, Bone Bow 27),
           ObjectEffect 804 (NoAutoCalc, cost 1 a hit, CHARGE), script ZP_OwlBowScript (the endless quiver)
  801 STAT 1stPersonZP_OwlBow    <- Pretty's 1stPersonFirewindBow 00080B (its bounds), Model = OwlBow.nif
  802 AMMO ZP_OwlBowIceArrow     <- EGO's Starling Arrow 10A86E: non-playable (never listed, never picked up),
           ARROW_DAMAGE, weightless, worthless, Model = tools/01's IceArrow.nif, projectile 803
  803 PROJ ZP_OwlBowIceArrowProj <- ArrowDwarvenProjectile 03BE14 without CanBePickedUp, Model IceArrowFlight.nif
  804 ENCH ZP_OwlBowFrost        weapon enchantment (Touch): 806 (slow) and 807 (freeze, GetRandomPercent < FREEZE_CHANCE)
  805 SPEL ZP_OwlBowQuiver       ability: 808 (given while the bow is equipped)
  806 MGEF ZP_OwlBowSlowEffect   <- Sting's slow 817 (Enderal's Shadowtongue Oil slow 0F8641: SpeedMult, Peak Value
           Modifier), SLOW% for SLOW_SECONDS, Chillrend's frost hit shader 10A044 on the target; EnchantArt 809 (the
           snowfall) on the invisible enchant shader 80A (Sting and Rise's lesson: enchant art shows only with one)
  807 MGEF ZP_OwlBowFreezeEffect script ZP_OwlBowFreezeEffect: weak enemies frozen solid FREEZE_SECONDS
  808 MGEF ZP_OwlBowQuiverEffect script ZP_OwlBowQuiverEffect (constant, hidden)
  809 ARTO ZP_OwlBowSnowFX       <- ChillrendEnchFX 10A045, Model = tools/01's OwlBowSnowFX.nif
  80A EFSH ZP_OwlBowCarrierFXS   <- Sting and Rise's ZP_EnchantArtCarrierFXS 813 (Chillrend's shader, every colour
           and alpha zero: draws nothing). Glow Be Gone must leave 806's shader: src/StingAndRise/tools/03
  80B FLST ZP_OwlBowOldAmmo      the arrows equipped before the bow (ZP_OwlBowScript)
  80C-80F retired (2026-11-17: the draw whoosh + lightsaber, removed by the curator: "doesn't work well"), never reuse
  810 SNDR ZP_OwlBowReleaseHootSD the owl's second hoot (tools/03), quiet; Argent Verdict's bell descriptor's settings
  811 SOUN ZP_OwlBowReleaseHoot   plays 810: ZP_OwlBowQuiverEffect, on arrowRelease
  812-817 SNDR/SOUN ZP_OwlBowDrawAir1-3(SD)  the curator's three air swells (tools/03), one per draw in turn,
           started on arrowAttach, peaking at BowDrawn
  818 SNDR ZP_OwlBowShotFlapSD    the curator's single wing beats (tools/03, FLAPS files), one at random per shot
  819 SOUN ZP_OwlBowShotFlap      plays 818: ZP_OwlBowQuiverEffect, on arrowRelease, except every 5th shot
  81A GLOB ZP_OwlBowCritReady     1 from the 5th shot's release to the next release (ZP_OwlBowQuiverEffect)
  81B PERK ZP_OwlBowCritPerk      hidden; Calculate My Critical Hit Chance +100 while 81A = 1 with Snowveil
           (Prophecy Deadeye's entry; tabs: owner = global, weapon = GetIsID 800). The 5th shot also hoots (811)

Usage:  python src/OwlBow/tools/02-build-records.py
"""
import os
import re
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
REF = os.path.join(ROOT, 'reference')
OUT = os.path.join(ROOT, 'src', 'OwlBow', 'OwlBowESP')
STING = os.path.join(ROOT, 'src', 'StingAndRise', 'StingAndRiseESP')
ME = 'Zenderal - Owl Bow.esp'

NAME = 'Snowveil'             # curator 2026-11-16 ("for now"); EditorIDs, files and the plugin keep OwlBow
BOW_DAMAGE, BOW_CRIT = 23, 17
ARROW_DAMAGE = 8              # the list's arrows: steel 5 .. Righteous Path 9
SLOW, SLOW_SECONDS = 30, 4
FREEZE_CHANCE, FREEZE_SECONDS = 5, 3   # curator: 5% to freeze weak targets
FLAPS = 8                     # tools/03's single wing beats (SnowveilShotFlap1..8.wav)
CHARGE = 3000
VALUE = 1500
BOUNDS = ('-19, -63, -4', '7, 63, 4')   # tools/01's mesh: plumes to 62.2 and z 4, string -18.7, grip feathers 6.5
MODEL = r'Zenderal\OwlBow\OwlBow.nif'
ARROW_MODEL = r'Zenderal\OwlBow\IceArrow.nif'
ARROW_FLIGHT = r'Zenderal\OwlBow\IceArrowFlight.nif'
SNOW_MODEL = r'Zenderal\OwlBow\OwlBowSnowFX.nif'
UNIQUE = '14CE9A:Skyrim.esm'            # WeapTypeUnique

SRC = {
    'bow': os.path.join(REF, 'mods', 'PEAEGO', 'Weapons', '_01E_04_FirewindBow - 054029_Skyrim.esm.yaml'),
    'stat': os.path.join(REF, 'mods', 'Pretty', 'Pretty Unique Armory', 'Statics',
                         '1stPersonFirewindBow - 00080B_Pretty Unique Armory.esp.yaml'),
    'ammo': os.path.join(REF, 'mods', 'EGO', 'Ammunitions', '_20E_StarlingArrow - 10A86E_Skyrim.esm.yaml'),
    'proj': os.path.join(REF, 'base', 'Skyrim', 'Projectiles', 'ArrowDwarvenProjectile - 03BE14_Skyrim.esm.yaml'),
    'art': os.path.join(REF, 'base', 'Skyrim', 'ArtObjects', 'ChillrendEnchFX - 10A045_Skyrim.esm.yaml'),
    'slow': os.path.join(STING, 'MagicEffects', 'ZP_StingSlowEffect - 000817_Zenderal - Sting and Rise.esp.yaml'),
    'carrier': os.path.join(STING, 'EffectShaders', 'ZP_EnchantArtCarrierFXS - 000813_Zenderal - Sting and Rise.esp.yaml'),
}


def read(path):
    with open(path, encoding='utf-8-sig', newline='') as f:
        return f.read().replace('\r\n', '\n')


def sub1(t, pat, rep):
    r = rep if callable(rep) else (lambda m: rep)        # replacement text is literal (Windows paths)
    t2, n = re.subn(pat, r, t, count=1, flags=re.M)
    assert n == 1, pat
    return t2


def drop_block(t, key):
    """Remove a top-level YAML key with its indented children."""
    t2, n = re.subn(r'^%s:.*\n(?:[ -].*\n)*' % re.escape(key), '', t, count=1, flags=re.M)
    assert n == 1, key
    return t2


def name(v):
    return 'Name:\n  TargetLanguage: English\n  Value: %s\n' % v


def fk(i):
    return '%06X:%s' % (i, ME)


written = []


def rec(folder, edid, i, text):
    assert text.startswith('FormKey: %s\n' % fk(i)) or ('\nFormKey: %s\n' % fk(i)) in text, (edid, text[:80])
    d = os.path.join(OUT, folder)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, '%s - %06X_%s.yaml' % (edid, i, ME))
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    written.append(p)


def script(nm, props):
    out = 'VirtualMachineAdapter:\n  Scripts:\n  - Name: %s\n    Properties:\n' % nm
    for pn, val in props:
        out += '    - MutagenObjectType: ScriptObjectProperty\n      Name: %s\n      Object: %s\n' % (pn, val)
    return out


def main():
    for p in SRC.values():
        assert os.path.isfile(p), p
    for d in os.listdir(OUT):                       # regenerate: every record folder is ours
        if os.path.isdir(os.path.join(OUT, d)):
            shutil.rmtree(os.path.join(OUT, d))

    # 800 the bow
    t = read(SRC['bow'])
    t = sub1(t, r'^FormKey: .*$', 'FormKey: ' + fk(0x800))
    t = sub1(t, r'^EditorID: .*$', 'EditorID: ZP_OwlBow\n' + script('ZP_OwlBowScript', [
        ('Bow', fk(0x800)), ('IceArrow', fk(0x802)), ('OldAmmo', fk(0x80B)), ('PlayerRef', '000014:Skyrim.esm'),
        ('QuiverAbility', fk(0x805))]).rstrip('\n') + '\nObjectBounds:\n  First: %s\n  Second: %s' % BOUNDS)
    t = sub1(t, r'^Name:\n  TargetLanguage: English\n  Value: .*\n', name(NAME))
    t = sub1(t, r'^Model:\n  File: .*\n  Data: .*$', 'Model:\n  File: ' + MODEL)
    t = sub1(t, r'^ObjectEffect: .*$', 'ObjectEffect: ' + fk(0x804))
    t = sub1(t, r'^EnchantmentAmount: .*$', 'EnchantmentAmount: %d' % CHARGE)
    t = sub1(t, r'^(Keywords:\n(?:- .*\n)*)', lambda m: m.group(1) + '- %s\n' % UNIQUE)
    t = sub1(t, r'^FirstPersonModel: .*$', 'FirstPersonModel: ' + fk(0x801))
    t = sub1(t, r'^  Value: 10\n  Weight: (.*)\n  Damage: .*$',
             lambda m: '  Value: %d\n  Weight: %s\n  Damage: %d' % (VALUE, m.group(1), BOW_DAMAGE))
    t = sub1(t, r'^Critical:\n  Damage: .*$', 'Critical:\n  Damage: %d' % BOW_CRIT)
    rec('Weapons', 'ZP_OwlBow', 0x800, t)

    # 801 first-person static
    t = read(SRC['stat'])
    t = sub1(t, r'^FormKey: .*$', 'FormKey: ' + fk(0x801))
    t = sub1(t, r'^EditorID: .*$', 'EditorID: 1stPersonZP_OwlBow')
    t = sub1(t, r'^ObjectBounds:\n  First: .*\n  Second: .*$', 'ObjectBounds:\n  First: %s\n  Second: %s' % BOUNDS)
    t = sub1(t, r'^Model:\n  File: .*\n  Data: .*$', 'Model:\n  File: ' + MODEL)
    rec('Statics', '1stPersonZP_OwlBow', 0x801, t)

    # 802 the ice arrow
    t = read(SRC['ammo'])
    t = sub1(t, r'^FormKey: .*$', 'FormKey: ' + fk(0x802))
    t = sub1(t, r'^EditorID: .*$', 'EditorID: ZP_OwlBowIceArrow')
    t = sub1(t, r'^Name:\n  TargetLanguage: English\n  Value: .*\n', name('Ice Arrow'))
    t = sub1(t, r'^Model:\n  File: .*\n  Data: .*$', 'Model:\n  File: ' + ARROW_MODEL)
    t = sub1(t, r'^Projectile: .*$', 'Projectile: ' + fk(0x803))
    t = sub1(t, r'^Flags:\n- NonBolt$', 'Flags:\n- NonBolt\n- NonPlayable')
    t = sub1(t, r'^Damage: .*$', 'Damage: %d' % ARROW_DAMAGE)
    t = sub1(t, r'^Value: .*$', 'Value: 0')
    t = sub1(t, r'^Weight: .*$', 'Weight: 0')
    rec('Ammunitions', 'ZP_OwlBowIceArrow', 0x802, t)

    # 803 its projectile
    t = read(SRC['proj'])
    t = sub1(t, r'^FormKey: .*$', 'FormKey: ' + fk(0x803))
    t = sub1(t, r'^EditorID: .*$', 'EditorID: ZP_OwlBowIceArrowProj')
    t = re.sub(r'^Name:\n  TargetLanguage: English\n  Values:\n(?:  .*\n)*', name('Ice Arrow'), t, count=1, flags=re.M)
    t = sub1(t, r'^Model:\n  File: .*\n  Data: .*$', 'Model:\n  File: ' + ARROW_FLIGHT)
    t = sub1(t, r'^Flags:\n- CanBePickedUp\n', '')
    rec('Projectiles', 'ZP_OwlBowIceArrowProj', 0x803, t)

    # 804 the enchantment
    rec('ObjectEffects', 'ZP_OwlBowFrost', 0x804, f"""FormKey: {fk(0x804)}
EditorID: ZP_OwlBowFrost
{name('Owl Frost')}EnchantmentCost: 1
Flags:
- NoAutoCalc
CastType: FireAndForget
EnchantmentAmount: {CHARGE}
TargetType: Touch
EnchantType: Enchantment
Effects:
- BaseEffect: {fk(0x806)}
  Data:
    Magnitude: {SLOW}
    Duration: {SLOW_SECONDS}
- BaseEffect: {fk(0x807)}
  Data:
    Duration: {FREEZE_SECONDS}
  Conditions:
  - MutagenObjectType: ConditionFloat
    CompareOperator: LessThan
    Data:
      MutagenObjectType: GetRandomPercentConditionData
    ComparisonValue: {FREEZE_CHANCE}
""")

    # 805 the quiver ability, 808 its effect
    rec('Spells', 'ZP_OwlBowQuiver', 0x805, f"""FormKey: {fk(0x805)}
EditorID: ZP_OwlBowQuiver
{name(NAME)}EquipmentType: 013F44:Skyrim.esm
Description:
  TargetLanguage: English
  Value: ''
Flags:
- ManualCostCalc
- IgnoreResistance
- NoAbsorbOrReflect
Type: Ability
Effects:
- BaseEffect: {fk(0x808)}
  Data: {{}}
""")
    rec('MagicEffects', 'ZP_OwlBowQuiverEffect', 0x808, f"""FormKey: {fk(0x808)}
EditorID: ZP_OwlBowQuiverEffect
{script('ZP_OwlBowQuiverEffect', [('IceArrow', fk(0x802)), ('ReleaseHoot', fk(0x811)), ('ShotFlap', fk(0x819)), ('CritReady', fk(0x81A)), ('CritPerk', fk(0x81B)), ('DrawAir1', fk(0x813)), ('DrawAir2', fk(0x815)), ('DrawAir3', fk(0x817))])}{name(NAME)}Flags:
- NoDuration
- NoMagnitude
- NoArea
- HideInUI
- Painless
Archetype:
  MutagenObjectType: MagicEffectArchetype
  Type: Script
DualCastScale: 1
Sounds: []
Description:
  TargetLanguage: English
  Value: ''
""")

    # 806 the slow, carrying the snowfall
    t = read(SRC['slow'])
    t = sub1(t, r'^FormKey: .*$', 'FormKey: ' + fk(0x806))
    t = sub1(t, r'^EditorID: .*$', 'EditorID: ZP_OwlBowSlowEffect')
    t = sub1(t, r'^Name:\n  TargetLanguage: English\n  Value: .*\n', name('Owl Frost'))
    t = sub1(t, r'^- HideInUI\n', '')
    # FXPersist: every enchant art that shows in game carries it (Rise 806, Sting 802, Clockwork Thunder 807, Whisper
    # 80B, Enderal's own Chillrend-art frost affinity 02F1A1:FS); without it the snowfall never showed (2026-11-17)
    t = sub1(t, r'^(Flags:\n(?:- .*\n)*)', lambda m: m.group(1) + '- FXPersist\n')
    t = sub1(t, r'^SpellmakingCastingTime: .*$', 'SpellmakingCastingTime: 0.5\nHitShader: 10A044:Skyrim.esm\n'
                                                  'EnchantShader: %s' % fk(0x80A))
    t = sub1(t, r"^Description:\n  TargetLanguage: English\n  Value: ''$",
             'Description:\n  TargetLanguage: English\n  Value: Arrows of ice that slow the target by <mag>% for <dur> seconds.')
    assert 'EnchantArt' not in t
    t = sub1(t, r'^CastType: FireAndForget$', 'EnchantArt: %s\nCastType: FireAndForget' % fk(0x809))
    rec('MagicEffects', 'ZP_OwlBowSlowEffect', 0x806, t)

    # 807 the freeze
    rec('MagicEffects', 'ZP_OwlBowFreezeEffect', 0x807, f"""FormKey: {fk(0x807)}
EditorID: ZP_OwlBowFreezeEffect
{script('ZP_OwlBowFreezeEffect', [('FreezeSound', '10A6A0:Skyrim.esm'), ('IceShader', '0DC20E:Skyrim.esm'),
                                    ('MagicNoFreeze', '0EEE66:Skyrim.esm')])}{name('Frozen Solid')}Flags:
- Hostile
- Detrimental
- NoMagnitude
- NoArea
Archetype:
  MutagenObjectType: MagicEffectArchetype
  Type: Script
CastType: FireAndForget
TargetType: Touch
DualCastScale: 1
Sounds: []
Description:
  TargetLanguage: English
  Value: A {FREEZE_CHANCE}% chance to freeze a weak enemy solid for <dur> seconds.
""")

    # 809 the snowfall art, 80A its invisible carrier shader
    t = read(SRC['art'])
    t = sub1(t, r'^FormKey: .*$', 'FormKey: ' + fk(0x809))
    t = sub1(t, r'^EditorID: .*$', 'EditorID: ZP_OwlBowSnowFX')
    t = sub1(t, r'^Model:\n  File: .*\n  Data: .*$', 'Model:\n  File: ' + SNOW_MODEL)
    rec('ArtObjects', 'ZP_OwlBowSnowFX', 0x809, t)
    t = read(SRC['carrier'])
    t = sub1(t, r'^FormKey: .*$', 'FormKey: ' + fk(0x80A))
    t = sub1(t, r'^EditorID: .*$', 'EditorID: ZP_OwlBowCarrierFXS')
    rec('EffectShaders', 'ZP_OwlBowCarrierFXS', 0x80A, t)

    # 80B the remembered arrows
    rec('FormLists', 'ZP_OwlBowOldAmmo', 0x80B, f'FormKey: {fk(0x80B)}\nEditorID: ZP_OwlBowOldAmmo\n')

    # 810/811 the release hoot (curator 2026-11-17): descriptor + sound marker, tools/03 installs the wav
    for sd, sm, eid, wav in ((0x810, 0x811, 'ZP_OwlBowReleaseHoot', 'SnowveilReleaseHoot.wav'),
                             (0x812, 0x813, 'ZP_OwlBowDrawAir1', 'SnowveilDrawAir1.wav'),
                             (0x814, 0x815, 'ZP_OwlBowDrawAir2', 'SnowveilDrawAir2.wav'),
                             (0x816, 0x817, 'ZP_OwlBowDrawAir3', 'SnowveilDrawAir3.wav'),
                             (0x818, 0x819, 'ZP_OwlBowShotFlap', ['SnowveilShotFlap%d.wav' % i for i in range(1, FLAPS + 1)])):
        files = ''.join('- data\\sound\\fx\\Zenderal\\OwlBow\\%s\n' % w for w in ([wav] if isinstance(wav, str) else wav))
        rec('SoundDescriptors', eid + 'SD', sd, f"""FormKey: {fk(sd)}
EditorID: {eid}SD
Type: Standard
Category: 0172A1:Skyrim.esm
SoundFiles:
{files}OutputModel: 0F1B1A:Skyrim.esm
LoopAndRumble: {{}}
Priority: 128
""")
        rec('SoundMarkers', eid, sm, f'FormKey: {fk(sm)}\nEditorID: {eid}\nFormVersion: 43\nSoundDescriptor: {fk(sd)}\n')

    # 81A/81B the guaranteed crit every 5th shot (curator 2026-11-17)
    rec('Globals', 'ZP_OwlBowCritReady', 0x81A, f'MutagenObjectType: GlobalShort\nFormKey: {fk(0x81A)}\nEditorID: ZP_OwlBowCritReady\nData: 0\n')
    rec('Perks', 'ZP_OwlBowCritPerk', 0x81B, f"""FormKey: {fk(0x81B)}
MajorRecordFlagsRaw: 4
EditorID: ZP_OwlBowCritPerk
SkyrimMajorRecordFlags:
- NotPlayable
Name:
  TargetLanguage: English
  Value: '{NAME}'
Description:
  TargetLanguage: English
  Value: ''
NumRanks: 1
Hidden: True
Effects:
- MutagenObjectType: PerkEntryPointModifyValue
  Priority: 50
  Conditions:
  - Conditions:
    - MutagenObjectType: ConditionFloat
      Data:
        MutagenObjectType: GetGlobalValueConditionData
        Global: {fk(0x81A)}
      ComparisonValue: 1
  - RunOnTabIndex: 1
    Conditions:
    - MutagenObjectType: ConditionFloat
      Data:
        MutagenObjectType: GetIsIDConditionData
        Object: {fk(0x800)}
      ComparisonValue: 1
  EntryPoint: CalculateMyCriticalHitChance
  PerkConditionTabCount: 3
  Modification: Add
  Value: 100
MajorFlags:
- NonPlayable
""")

    for p in written:
        t = read(p)
        assert 'Pretty Unique Armory' not in t and 'Gameplay Overhaul' not in t, p
        for m in re.findall(r':([^\s:]+\.es[mp])', t):
            assert m in ('Skyrim.esm', ME), (p, m)
    print('%d records written to %s' % (len(written), OUT))


if __name__ == '__main__':
    main()
