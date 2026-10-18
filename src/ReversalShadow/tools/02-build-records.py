"""Generate Reversal Shadow's records from the Flintlock Overhaul's Priest's Dueling Pistol.

Every record is a verbatim copy of its Flintlock Overhaul / Gentleman's source YAML with only
the listed fields changed, so rerun this after the Flintlock Overhaul's tools/01 (damage,
Loop meshes) or its ZP_FlintlockWeapons list change.

  800 WEAP ReversalShadow            <- PMDuelingPistol02 000817 (Flintlock Overhaul's winning copy); Damage 30 (top tier)
  801 STAT 1stPersonReversalShadow   <- 1stPersonPMDuelingPistol02 00080A
  802 ENCH ZP_ReversalShadowShot     <- ZP_FlintlockShot_PriestsDuelingPistol 000805 + Witch Bolt's effects
  803 MGEF ZP_ReversalShadowBullet   <- PMPistolShot 000802, BaseCost 1.2 -> 50
  804 COBJ ZP_RecipeReversalShadow   Priest's Dueling Pistol + 2 Silver Ingots, Smithing >= 50
  805 COBJ ZP_TemperReversalShadow   <- PMTemperDueling02 000830
  806 MGEF ZP_EldritchBlastWitchBoltBonus <- TVR_Warlock_Balefire_Effect_EldritchBlast 19B464 (Triumvirate):
           20 extra raw damage, flat (no PowerAffectsMagnitude, DualCastScale 1), no hit art and no
           IsBalefireSpell keyword, so it neither doubles the visuals nor counts as a second balefire hit
  override ZP_FlintlockWeapons 000802:Zenderal - Flintlock Overhaul.esp (+800), so the
           Flintlock Overhaul's reload script treats it as a pistol.
  807 REFR the pistol on the lower board of the CommonShelf04 at Old Crosswatch (shelf ref 0F916D,
           exterior cell 001F20 in Vyn) + the WRLD/group/cell scaffolding, headers from Forts of Enderal
  override TVR_Warlock_D000_Spell_EldritchBlast 19B465 = Zenderal - Magic Patches' copy (cost ladder) + 806
  override TVR_Warlock_D000_StaffEnchantment_EldritchBlast 419B32 = Triumvirate's record + 806
           806's entry carries the condition Subject HasMagicEffect Witch Bolt 1BEBB6; on a
           fire-and-forget spell the effect's Subject is the target, so the bonus lands only on a target
           Witch Bolt (pistol or spell) is burning. Rerun after Magic Patches regenerates its Triumvirate spells.

Why 803 exists: an enchantment's projectile, sounds and casting art come from its COSTLIEST
effect. Witch Bolt's effect costs 168 at magnitude 3 / 60 s; the bullet costs ~23
(1.2 x 14.4^1.1), so the shot would fly as Witch Bolt's dark-fire bolt. The copy only raises
BaseCost (enchantment cost is NoAutoCalc, so nothing else reads it).

Usage:  python 02-build-records.py
"""
import os
import re

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
FO = os.path.join(ROOT, 'src/FlintlockOverhaul/FlintlockOverhaulESP')
GENTLEMAN = os.path.join(ROOT, 'reference/mods/FlintlockPack')
TRIUMVIRATE = os.path.join(ROOT, 'reference/mods/Triumvirate')   # spriggit-decompile-reference of the installed esp
MAGIC_PATCHES = os.path.join(ROOT, 'src/MagicPatches/MagicPatchesESP')
TVR = 'Triumvirate - Mage Archetypes.esp'
OUT = os.path.join(ROOT, 'src/ReversalShadow/ReversalShadowESP')
ME = 'Zenderal - Reversal Shadow.esp'
FO_KEY = 'Zenderal - Flintlock Overhaul.esp'

NAME = 'Reversal Shadow'
LOOP_KEYWORD = '000801:Pistol animation by Loop.esp'   # Pistol_Animation_By_Loop; LoopPistolAnims' OAR submods match it
WITCHBOLT_DAMAGE = '1BEBB6:Triumvirate - Mage Archetypes.esp'   # TVR_Warlock_Balefire_Effect_WitchBolt
BIND_SPIRIT = '19B46E:Triumvirate - Mage Archetypes.esp'        # TVR_Warlock_Balefire_Effect_BindSpirit_FFAimed
SILVER_INGOT = '05ACE3:Skyrim.esm'
PRIESTS_PISTOL = '000817:AdventurerFlintlockPack.esp'
# Curator 2026-10-18: top of the pistol range. The Flintlock Overhaul's best pistol (PMFlintlockPistool04 00083A)
# has Damage 30 / critical 20; the shot magnitude follows its tools/01 rule, MULT 1.2 x Damage.
DAMAGE = 30
CRIT_DAMAGE = 20
SHOT_MULT = 1.2
# Curator 2026-10-18: Eldritch Blast does 20 more damage to a target under Witch Bolt.
WITCHBOLT_BONUS = 20
BONUS_ENTRY = '\r\n'.join([
    f'- BaseEffect: 000806:{ME}',
    '  Data:',
    f'    Magnitude: {WITCHBOLT_BONUS}',
    '    Duration: 1',
    '  Conditions:',
    '  - MutagenObjectType: ConditionFloat',
    '    Data:',
    '      MutagenObjectType: HasMagicEffectConditionData',
    f'      MagicEffect: {WITCHBOLT_DAMAGE}',
    '    ComparisonValue: 1',
]) + '\r\n'


def read(path):
    with open(path, encoding='utf-8-sig', newline='') as f:
        return f.read()


def sub1(text, pattern, repl):
    out, n = re.subn(pattern, repl, text, count=1, flags=re.M)
    if n != 1:
        raise SystemExit(f'pattern not found: {pattern}')
    return out


def write(folder, editor_id, formid, text):
    d = os.path.join(OUT, folder)
    os.makedirs(d, exist_ok=True)
    if not text.endswith('\n'):
        text += '\r\n'
    with open(os.path.join(d, f'{editor_id} - {formid}_{ME}.yaml'), 'w', encoding='utf-8', newline='') as f:
        f.write(text.replace('\r\n', '\n').replace('\n', '\r\n'))


def write_override(folder, editor_id, formid, master, text):
    d = os.path.join(OUT, folder)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, f'{editor_id} - {formid}_{master}.yaml'), 'w', encoding='utf-8', newline='') as f:
        f.write(text.replace('\r\n', '\n').replace('\n', '\r\n'))


def one(folder, stem):
    hits = [f for f in os.listdir(folder) if f.startswith(stem)]
    if len(hits) != 1:
        raise SystemExit(f'{folder}: expected one {stem}*, found {hits}')
    return read(os.path.join(folder, hits[0]))


FORTS = os.path.join(ROOT, 'reference/mods/FortsOfEnderal')   # spriggit-decompile-reference of Forts of Enderal.esp
VYN = 'Worldspaces/Vyn - 001D3C_Skyrim.esm'
CELL_DIR = VYN + '/-1, 0/-3, 0/001F20_Skyrim.esm'

# CommonShelf04 0CE786 ref 0F916D:Skyrim.esm (no plugin in profile Ultra overrides it, 2026-10-18 scan)
SHELF_POS = (-84407.83, 14267.719, 5484.4707)
SHELF_ROT_Z = 2.3231914
# Winning mesh (Skyrim 3D Furniture, above SMIM in modlist.txt): lower board top at z ~17.5, interior
# x +-68 / y +-27. The pistol world model lies flat in its XY plane, bounds x -7..16.7, y -9.3..38.6,
# z -2.9..3.2 (tools/01 output measured with PyNifly).
SHELF_BOARD_Z = 17.5
PISTOL_BOUNDS = ((-7.0, 16.7), (-9.3, 38.6), (-2.9, 3.2))


def place_on_shelf():
    """Barrel along the shelf, pistol centred on the lower board, lying flat 0.1 above it (DoNotHavokSettle).
    Bethesda Z rotation is clockwise from +Y: local (x, y) -> (x cos t + y sin t, -x sin t + y cos t)."""
    import math

    def rot(x, y, t):
        return x * math.cos(t) + y * math.sin(t), -x * math.sin(t) + y * math.cos(t)

    t = (SHELF_ROT_Z + math.pi / 2) % (2 * math.pi)
    cx = sum(PISTOL_BOUNDS[0]) / 2
    cy = sum(PISTOL_BOUNDS[1]) / 2
    ox, oy = rot(cx, cy, t)
    x, y = SHELF_POS[0] - ox, SHELF_POS[1] - oy
    z = SHELF_POS[2] + SHELF_BOARD_Z - PISTOL_BOUNDS[2][0] + 0.1
    # assert every corner stays inside the shelf interior
    for lx in PISTOL_BOUNDS[0]:
        for ly in PISTOL_BOUNDS[1]:
            wx, wy = rot(lx, ly, t)
            wx += x - SHELF_POS[0]
            wy += y - SHELF_POS[1]
            sx = wx * math.cos(SHELF_ROT_Z) - wy * math.sin(SHELF_ROT_Z)
            sy = wx * math.sin(SHELF_ROT_Z) + wy * math.cos(SHELF_ROT_Z)
            assert abs(sx) < 66 and abs(sy) < 25, (sx, sy)

    # WRLD header: Forts of Enderal's, truncated before TopCell (a later plugin, BristlebacksInEnderal,
    # wins the header in the live order anyway)
    wrld = read(os.path.join(FORTS, VYN, 'RecordData.yaml'))
    head, _, tail = wrld.partition('TopCell:')
    assert tail and 'SubCellsUnknown: 1' in tail
    wrld = head + 'SubCellsUnknown: 1\r\n'
    # cell header: Forts of Enderal's (the winning CELL; FS/EGO/Forts headers match bar Grid.Flags)
    cell = read(os.path.join(FORTS, CELL_DIR, 'RecordData.yaml'))
    cell = cell[:cell.index('Temporary:')]
    assert 'Persistent' not in cell and 'NavigationMeshes' not in cell
    cell += '\r\n'.join([
        'Temporary:',
        '- MutagenObjectType: PlacedObject',
        f'  FormKey: 000807:{ME}',
        # 2026-10-18 in game: settled by Havok it propped up on the grip at an angle, so it stays as placed.
        # Don't Havok Settle = 0x20000000; Spriggit drops a named 'MajorFlags' entry on a PlacedObject.
        '  MajorRecordFlagsRaw: 536870912',
        '  SkyrimMajorRecordFlags:',
        '  - 0x20000000',
        f'  Base: 000800:{ME}',
        '  Placement:',
        f'    Position: {x:.3f}, {y:.3f}, {z:.3f}',
        f'    Rotation: 0, -0, {t:.7f}',
    ]) + '\r\n'
    files = {
        VYN + '/RecordData.yaml': wrld,
        VYN + '/-1, 0/GroupRecordData.yaml': read(os.path.join(FORTS, VYN, '-1, 0', 'GroupRecordData.yaml')),
        VYN + '/-1, 0/-3, 0/GroupRecordData.yaml': read(os.path.join(FORTS, VYN, '-1, 0', '-3, 0', 'GroupRecordData.yaml')),
        CELL_DIR + '/RecordData.yaml': cell,
    }
    for rel, text in files.items():
        p = os.path.join(OUT, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'w', encoding='utf-8', newline='') as f:
            f.write(text.replace('\r\n', '\n').replace('\n', '\r\n'))


def main():
    import shutil
    shutil.rmtree(os.path.join(OUT, 'Worldspaces'), ignore_errors=True)
    for sub in ('Weapons', 'Statics', 'ObjectEffects', 'MagicEffects', 'ConstructibleObjects', 'FormLists', 'Spells'):
        d = os.path.join(OUT, sub)
        if os.path.isdir(d):
            for f in os.listdir(d):
                os.remove(os.path.join(d, f))

    # 800 WEAP
    w = one(os.path.join(FO, 'Weapons'), 'PMDuelingPistol02 - 000817')
    w = sub1(w, r'^FormKey: .*?(?=\r?$)', f'FormKey: 000800:{ME}')
    w = sub1(w, r'^EditorID: .*?(?=\r?$)', 'EditorID: ZP_ReversalShadow')
    w = sub1(w, r'^(Name:\r?\n  TargetLanguage: English\r?\n  Value: ).*?(?=\r?$)', r'\g<1>' + NAME)
    w = sub1(w, r'^(Model:\r?\n  File: ).*?(?=\r?$)', r'\g<1>Zenderal\\ReversalShadow\\ReversalShadow.nif')
    w = sub1(w, r'^ObjectEffect: .*?(?=\r?$)', f'ObjectEffect: 000802:{ME}')
    w = sub1(w, r'^FirstPersonModel: .*?(?=\r?$)', f'FirstPersonModel: 000801:{ME}')
    w = sub1(w, r'^(Keywords:\r?\n(?:- .*\r?\n)+)', r'\g<1>- ' + LOOP_KEYWORD + '\r\n')
    w = sub1(w, r'^(  Value: )700(?=\r?$)', r'\g<1>2400')
    w = sub1(w, r'^(BasicStats:\r?\n(?:  .*\r?\n)*?  Damage: )\d+(?=\r?$)', r'\g<1>' + str(DAMAGE))
    w = sub1(w, r'^(Critical:\r?\n  Damage: )\d+(?=\r?$)', r'\g<1>' + str(CRIT_DAMAGE))
    write('Weapons', 'ZP_ReversalShadow', '000800', w)

    # 801 STAT (equipped model, 1st and 3rd person)
    s = one(os.path.join(FO, 'Statics'), '1stPersonPMDuelingPistol02 - 00080A')
    s = sub1(s, r'^FormKey: .*?(?=\r?$)', f'FormKey: 000801:{ME}')
    s = sub1(s, r'^EditorID: .*?(?=\r?$)', 'EditorID: 1stPersonZP_ReversalShadow')
    s = sub1(s, r'^(  File: ).*?(?=\r?$)', r'\g<1>Zenderal\\ReversalShadow\\ReversalShadow1st.nif')
    write('Statics', '1stPersonZP_ReversalShadow', '000801', s)

    # 803 MGEF bullet copy (costliest effect -> keeps the musket-ball projectile and shot sound)
    m = one(os.path.join(FO, 'MagicEffects'), 'PMPistolShot - 000802')
    m = sub1(m, r'^FormKey: .*?(?=\r?$)', f'FormKey: 000803:{ME}')
    m = sub1(m, r'^EditorID: .*?(?=\r?$)', 'EditorID: ZP_ReversalShadowBullet')
    m = sub1(m, r'^BaseCost: .*?(?=\r?$)', 'BaseCost: 50')
    m = sub1(m, r'^(Description:\r?\n  TargetLanguage: English\r?\n  Value: )Fires a musket ball(?=\r?$)',
             r'\g<1>Fires a Flintlock bullet.')   # curator 2026-10-18: it loads Flintlock Bullets, not musket balls
    write('MagicEffects', 'ZP_ReversalShadowBullet', '000803', m)

    # 802 ENCH: Priest's shot (bullet swapped for 803) + Witch Bolt's two effects at Triumvirate's values
    e = one(os.path.join(FO, 'ObjectEffects'), 'ZP_FlintlockShot_PriestsDuelingPistol - 000805')
    e = sub1(e, r'^FormKey: .*?(?=\r?$)', f'FormKey: 000802:{ME}')
    e = sub1(e, r'^EditorID: .*?(?=\r?$)', 'EditorID: ZP_ReversalShadowShot')
    e = sub1(e, r'^(Name:\r?\n  TargetLanguage: English\r?\n  Value: ).*?(?=\r?$)', r'\g<1>Witch Bolt Shot')
    e = sub1(e, r'^- BaseEffect: 000802:AdventurerFlintlockPack\.esp(?=\r?$)', f'- BaseEffect: 000803:{ME}')
    e = sub1(e, r'^(- BaseEffect: 000803:.*\r?\n  Data:\r?\n    Magnitude: )[\d.]+(?=\r?$)',
             r'\g<1>' + str(round(SHOT_MULT * DAMAGE, 1)))
    e = e.rstrip('\r\n') + '\r\n' + '\r\n'.join([
        f'- BaseEffect: {WITCHBOLT_DAMAGE}',
        '  Data:',
        '    Magnitude: 3',
        '    Duration: 60',
        f'- BaseEffect: {BIND_SPIRIT}',
        '  Data:',
        '    Magnitude: 1000',
        '    Duration: 60',
    ]) + '\r\n'
    write('ObjectEffects', 'ZP_ReversalShadowShot', '000802', e)

    # 804 COBJ craft
    write('ConstructibleObjects', 'ZP_RecipeReversalShadow', '000804', '\r\n'.join([
        f'FormKey: 000804:{ME}',
        'EditorID: ZP_RecipeReversalShadow',
        'Items:',
        '- Item:',
        f'    Item: {PRIESTS_PISTOL}',
        '    Count: 1',
        '- Item:',
        f'    Item: {SILVER_INGOT}',
        '    Count: 2',
        'Conditions:',
        '- MutagenObjectType: ConditionFloat',
        '  CompareOperator: GreaterThanOrEqualTo',
        '  Data:',
        '    MutagenObjectType: GetActorValueConditionData',
        '    ActorValue: Smithing',
        '  ComparisonValue: 50',
        f'CreatedObject: 000800:{ME}',
        'WorkbenchKeyword: 088105:Skyrim.esm',
        'CreatedObjectCount: 1',
    ]) + '\r\n')

    # 805 COBJ temper (Priest's temper verbatim, new product)
    t = read(os.path.join(GENTLEMAN, 'ConstructibleObjects', 'PMTemperDueling02 - 000830_AdventurerFlintlockPack.esp.yaml'))
    t = sub1(t, r'^FormKey: .*?(?=\r?$)', f'FormKey: 000805:{ME}')
    t = sub1(t, r'^EditorID: .*?(?=\r?$)', 'EditorID: ZP_TemperReversalShadow')
    t = sub1(t, r'^CreatedObject: .*?(?=\r?$)', f'CreatedObject: 000800:{ME}')
    write('ConstructibleObjects', 'ZP_TemperReversalShadow', '000805', t)

    # 806 MGEF: Eldritch Blast's damage effect as a flat, art-less bonus
    b = one(os.path.join(TRIUMVIRATE, 'MagicEffects'), 'TVR_Warlock_Balefire_Effect_EldritchBlast - 19B464')
    b = sub1(b, r'^FormKey: .*?(?=\r?$)', f'FormKey: 000806:{ME}')
    b = sub1(b, r'^EditorID: .*?(?=\r?$)', 'EditorID: ZP_EldritchBlastWitchBoltBonus')
    b = sub1(b, r'^(Name:\r?\n  TargetLanguage: English\r?\n  Value: ).*?(?=\r?$)', r'\g<1>Witch Bolt Resonance')
    b = sub1(b, r'^- 19B468:Triumvirate - Mage Archetypes\.esp\r?\n', '')
    b = sub1(b, r'^- PowerAffectsMagnitude\r?\n', '')
    b = sub1(b, r'^HitEffectArt: .*\r?\n', '')
    b = sub1(b, r'^ImageSpaceModifier: .*\r?\n', '')
    b = sub1(b, r'^DualCastScale: .*?(?=\r?$)', 'DualCastScale: 1')
    # never the costliest effect (that one picks projectile/sounds/casting art), and adds ~nothing to autocalc
    b = sub1(b, r'^BaseCost: .*?(?=\r?$)', 'BaseCost: 0')
    b = sub1(b, r'^(Description:\r?\n  TargetLanguage: English\r?\n  Value: ).*?(?=\r?$)',
             r'\g<1>Deals <mag> extra raw damage to a target burning with Witch Bolt.')
    write('MagicEffects', 'ZP_EldritchBlastWitchBoltBonus', '000806', b)

    # Eldritch Blast spell (Magic Patches' winning copy) and staff enchantment (Triumvirate's) + 806
    def add_bonus(text):
        return text.rstrip('\r\n') + '\r\n' + BONUS_ENTRY

    sp = add_bonus(one(os.path.join(MAGIC_PATCHES, 'Spells'), 'TVR_Warlock_D000_Spell_EldritchBlast - 19B465'))
    write_override('Spells', 'TVR_Warlock_D000_Spell_EldritchBlast', '19B465', TVR, sp)
    st = add_bonus(one(os.path.join(TRIUMVIRATE, 'ObjectEffects'), 'TVR_Warlock_D000_StaffEnchantment_EldritchBlast - 419B32'))
    # Triumvirate's staff autocalcs its charge cost (32); pin it so the extra entry cannot change it
    st = sub1(st, r'^(EnchantmentCost: 32\r?\n)', r'\g<1>Flags:\r\n- NoAutoCalc\r\n')
    write_override('ObjectEffects', 'TVR_Warlock_D000_StaffEnchantment_EldritchBlast', '419B32', TVR, st)

    # 807 REFR: the pistol on the lower board of CommonShelf04 ref 0F916D, Old Crosswatch (cell 001F20)
    place_on_shelf()

    # FormList override: the Flintlock Overhaul's list + 800
    fl = one(os.path.join(FO, 'FormLists'), 'ZP_FlintlockWeapons - 000802')
    fl = fl.rstrip('\r\n') + f'\r\n- 000800:{ME}\r\n'
    d = os.path.join(OUT, 'FormLists')
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, f'ZP_FlintlockWeapons - 000802_{FO_KEY}.yaml'), 'w', encoding='utf-8', newline='') as f:
        f.write(fl.replace('\r\n', '\n').replace('\n', '\r\n'))
    print('records written to', OUT)


if __name__ == '__main__':
    main()
