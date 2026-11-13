"""Generate Clockwork Thunder's records: a unique Starling rifle whose shot sends a weak chain lightning
into the enemy it hits. Every record is a verbatim copy of its live winner with only the listed fields
changed (00-scan-overriders.py lists the winners; this script refuses to run if one changed hands).

  800 WEAP ZP_ClockworkThunder        <- OL_Musket_Rifle 002F9B (Muskets of the Enderal; the only plugin with it)
           Name, Model (tools/01's mesh), FirstPersonModel 801, ObjectEffect 802 + EnchantmentAmount,
           Value 666 -> 3200, Damage 20 -> 28 / crit 9 -> 10 (Ordo's range is 6-35), + keyword
           WeapTypeRifleBoltAction 000800:DAR Rifles.esp (what Flintlock Overhaul's KID gives Ordo's 14 muskets:
           DAR Rifles' animations, Quick Reload Stack). Still a crossbow-type WEAP firing Ordo's ammo, so the
           HWYA Musket Fix's projectiles (Gravity 0) are the ones it shoots.
  801 STAT 1stPersonZP_ClockworkThunder <- OLM_1stPersonMusketRifle 002F9A, Model -> tools/01's mesh
  802 ENCH ZP_ClockworkThunderShot    weapon enchantment (Touch, Enchantment), 803 only. NoAutoCalc, cost 1 a shot,
           charge 3000: in practice never runs dry; soul gems still recharge it
  803 MGEF ZP_ClockworkThunderChainEffect  Script archetype (Touch, fire and forget) running our
           ZP_ClockworkThunderChainScript: the struck enemy gets only the ball; the bolt 804 starts FROM it and
           jumps up to CHAIN_JUMPS times to the nearest hostile enemy within CHAIN_RANGE (RemoteCast from the last
           one struck, blamed on the player, from an
           empty activator aimed at one on the next enemy). Its description is the item card text
  804 SPEL ZP_ClockworkThunderChainLightning <- Prophecy's Flow State chain lightning 000B02, its effect swapped
           for 80A, Magnitude 40 -> CHAIN_DAMAGE, no Area (the script picks the targets), + the stun check 809
  80A MGEF ZP_ClockworkThunderBoltEffect <- Prophecy's Invoker shock 000AFD (vanilla Chain Lightning's bolt),
           Explosion -> 80B
  80B EXPL ZP_ClockworkThunderBoltBlast <- Prophecy's flash-less chain explosion 000B01 minus the Chain flag
           (the engine's chain jumps are player-shooter projectiles that Hit Where You Aim re-aims at the
           crosshair, and reach only the spell's 13 ft Area; the curator wants visible bounces, 2026-11-13)
  805 COBJ ZP_TemperClockworkThunder  <- Ordo's matchlock temper 00F5D6 (gold ingot + ...), the second item a
           Starling ingot 0DB8A2 instead of 0F11C0; new product. No forge recipe: the rifle is unique
  806 REFR the rifle on the broken altar (RuinsAltarBroken ref 07410A) in Old Askamahn's throne room
           (DesertAltAskamahnL2 07336E, Enma Darkhand's room), plus the cell header (Skyrim.esm's, the only
           plugin with the cell in the live order) and its two group files. Lies on its side along the altar;
           Havok settles it on load (no Don't Havok Settle: it should come to rest by itself on the rubble top)

Usage:  python src/ClockworkThunder/tools/02-build-records.py [--mods <MO2 mods dir>] [--target <mod>]
"""
import argparse
import json
import math
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
TOOLS = json.load(open(os.path.join(ROOT, '.claude', 'config', 'tools.json'), encoding='utf-8-sig'))
sys.path.insert(0, TOOLS['pynifly'])

ORDO_REF = os.path.join(ROOT, 'reference', 'mods', 'OrdoEnderal')    # Muskets of the Enderal = the live Ordo plugin
PROPHECY = os.path.join(ROOT, 'src', 'Prophecy', 'ProphecyESP')
BASE = os.path.join(ROOT, 'reference', 'base', 'Skyrim')
OUT = os.path.join(ROOT, 'src', 'ClockworkThunder', 'ClockworkThunderESP')
ME = 'Zenderal - Clockwork Thunder.esp'
ORDO = 'OrdoLegionisMuskets.esp'

NAME = 'Clockwork Thunder'
DAMAGE, CRIT_DAMAGE, VALUE = 28, 10, 3200
CHARGE = 3000
CHAIN_DAMAGE = 15           # curator: "weak" chain lightning (Prophecy's Flow State bolt is 40)
STUN_SECONDS = 3            # curator 2026-11-13: the lightning stuns "for a few seconds", only enemies below the
                            # player's level (ZP_ClockworkThunderStunScript decides)
RIFLE_KEYWORD = '000800:DAR Rifles.esp'   # WeapTypeRifleBoltAction
CHAIN_SCRIPT = 'ZP_ClockworkThunderChainScript'
CHAIN_JUMPS = 4             # bounces after the first strike (the script's Jumps; checked below)
CHAIN_RANGE = 700.0         # units from the last enemy struck (the script's Range; checked below)
STARLING_INGOT = '0DB8A2:Skyrim.esm'      # IngotStarling
MODEL = r'Zenderal\ClockworkThunder\ClockworkThunder.nif'
MESH_REL = 'meshes/Zenderal/ClockworkThunder/ClockworkThunder.nif'

CELL_DIR = 'Cells/8/1/DesertAltAskamahnL2 - 07336E_Skyrim.esm'
ALTAR_POS = (4372.4653, -5912.3335, 7429.4985)    # RuinsAltarBroken 07410A (no plugin overrides it, 00-scan)
ALTAR_ROT_Z = 1.5881906
ALTAR_TOP = 14.0            # the broken slab's top in the winning mesh (PG Patcher Output's RuinsFurnitureRubble15,
                            # height field sampled 2026-11-13: a flat z 14 plane with gaps down to -2; rails at 19-21)
ALTAR_SPOT = (0.0, -28.0)   # altar-local XY of the rifle's centre: the slab, clear of the rails (y +-68)
DROP = 1.0                  # start this far above the slab and let Havok settle it

EXPECTED_WINNERS = {
    '14CEBD:Skyrim.esm': 'Skyrim.esm',
    '002F9B:OrdoLegionisMuskets.esp': ORDO,
    '002F9A:OrdoLegionisMuskets.esp': ORDO,
    '00F5D6:OrdoLegionisMuskets.esp': ORDO,
    '07336E:Skyrim.esm': 'Skyrim.esm',
    '07410A:Skyrim.esm': 'Skyrim.esm',
    '000B02:Zenderal - Prophecy.esp': 'Zenderal - Prophecy.esp',
    '000AFD:Zenderal - Prophecy.esp': 'Zenderal - Prophecy.esp',
    '000B01:Zenderal - Prophecy.esp': 'Zenderal - Prophecy.esp',
}


def read(path):
    with open(path, encoding='utf-8-sig', newline='') as f:
        return f.read().replace('\r\n', '\n')


def one(folder, stem):
    hits = [f for f in os.listdir(folder) if f.startswith(stem)]
    if len(hits) != 1:
        sys.exit('%s: expected one %s*, found %s' % (folder, stem, hits))
    return read(os.path.join(folder, hits[0]))


def sub1(text, pattern, repl):
    out, n = re.subn(pattern, repl, text, count=1, flags=re.M)
    if n != 1:
        sys.exit('pattern not found: ' + pattern)
    return out


def write(rel, text):
    p = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    if not text.endswith('\n'):
        text += '\n'
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(text.replace('\n', '\r\n'))


def rec(folder, editor_id, formid, text):
    write('%s/%s - %s_%s.yaml' % (folder, editor_id, formid, ME), text)


def check_winners():
    p = os.path.join(HERE, 'overriders.json')
    if not os.path.isfile(p):
        sys.exit('run 00-scan-overriders.py first')
    chains = json.load(open(p, encoding='utf-8'))
    for fk, want in EXPECTED_WINNERS.items():
        chain = [c for c in chains.get(fk, []) if c != ME]
        if not chain or chain[-1] != want:
            sys.exit('%s: winner is now %s, not %s - rebase the copy' % (fk, chain[-1:] or None, want))


def rifle_lying_bounds(mesh_path):
    """Root-space bounds of the built mesh (all shapes). NIF shape transforms apply as R*(s*v) + t."""
    import numpy as np
    from pyn.pynifly import NifFile
    nif = NifFile(mesh_path)
    pts = []
    for s in nif.shapes:
        xf = s.transform
        R = np.array([[xf.rotation[i][j] for j in range(3)] for i in range(3)])
        t = np.array([xf.translation[i] for i in range(3)])
        pts.append((np.array(s.verts) * xf.scale) @ R.T + t)
    P = np.concatenate(pts)
    return P.min(0), P.max(0)


def placement(mesh_path):
    """Position + rotation of the rifle lying on its side on the altar slab.

    In root space the rifle is upright (length along +Y, its side faces +-X, upside down: up is -Z). A quarter
    turn about Y lays it on a side; with no Z turn its length stays along world Y, which is the altar's long axis
    (the altar is turned 1.588 rad, so its local X runs along world -Y). Which side ends down depends on the
    engine's sign for Y; the height clears both, and Havok settles it on load."""
    lo, hi = rifle_lying_bounds(mesh_path)
    th = ALTAR_ROT_Z
    ax, ay = ALTAR_SPOT
    cx = ALTAR_POS[0] + ax * math.cos(th) + ay * math.sin(th)
    cy = ALTAR_POS[1] - ax * math.sin(th) + ay * math.cos(th)
    # lying: root (x, y, z) -> world (+-z, y, -+x); centre the root bounds on (cx, cy)
    y = cy - (lo[1] + hi[1]) / 2
    x = cx - (lo[2] + hi[2]) / 2      # the other sign moves it by < 8 units across a 190-wide altar
    z = ALTAR_POS[2] + ALTAR_TOP + max(hi[0], -lo[0]) + DROP
    # the rifle must lie inside the altar's long extent (local X -108..108 between the end posts)
    half = (hi[1] - lo[1]) / 2
    assert half < 100, half
    return (x, y, z), (0.0, -math.pi / 2, 0.0), (lo, hi)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mods', default=os.path.join(TOOLS['modlistRoot'], 'mods'))
    ap.add_argument('--target', default='Zenderal - Patch Collection')
    args = ap.parse_args()
    check_winners()
    mesh = os.path.join(args.mods, args.target, *MESH_REL.split('/'))
    if not os.path.isfile(mesh):
        sys.exit('run 01-build-assets.py first (no %s)' % mesh)

    for sub in ('Weapons', 'Statics', 'ObjectEffects', 'MagicEffects', 'Spells', 'Explosions', 'ConstructibleObjects', 'Cells'):
        shutil.rmtree(os.path.join(OUT, sub), ignore_errors=True)

    # 800 WEAP
    w = one(os.path.join(ORDO_REF, 'Weapons'), 'OL_Musket_Rifle - 002F9B')
    w = sub1(w, r'^FormKey: .*$', 'FormKey: 000800:' + ME)
    w = sub1(w, r'^EditorID: .*$', 'EditorID: ZP_ClockworkThunder')
    w = sub1(w, r'^(Name:\n  TargetLanguage: English\n  Value: ).*$', r'\g<1>' + NAME)
    w = sub1(w, r'^(Model:\n  File: ).*$', lambda m: m.group(1) + MODEL)
    w = sub1(w, r'^(Model:\n  File: .*\n)  Data: .*\n', r'\g<1>')     # model texture hashes belong to the old mesh
    w = sub1(w, r'^(Keywords:\n(?:- .*\n)+)', r'\g<1>- ' + RIFLE_KEYWORD + '\n')
    w = sub1(w, r'^(Model:\n  File: .*\n)', r'\g<1>ObjectEffect: 000802:' + ME + '\nEnchantmentAmount: %d\n' % CHARGE)
    w = sub1(w, r'^(FirstPersonModel: ).*$', r'\g<1>000801:' + ME)
    # Ordo's equip sounds are Dawnguard.esm's, an empty stub in Enderal that a patch never masters; the bows'
    # own (35/40 of Skyrim.esm's bows and crossbows use these) instead
    w = sub1(w, r'^EquipSound: 017EC9:Dawnguard\.esm$', 'EquipSound: 03D78C:Skyrim.esm')
    w = sub1(w, r'^UnequipSound: 017ECA:Dawnguard\.esm$', 'UnequipSound: 03D882:Skyrim.esm')
    assert 'Dawnguard' not in w
    w = sub1(w, r'^(BasicStats:\n  Value: )666$', r'\g<1>' + str(VALUE))
    w = sub1(w, r'^(BasicStats:\n(?:  .*\n)*?  Damage: )20$', r'\g<1>' + str(DAMAGE))
    w = sub1(w, r'^(Critical:\n  Damage: )9$', r'\g<1>' + str(CRIT_DAMAGE))
    rec('Weapons', 'ZP_ClockworkThunder', '000800', w)

    # 801 STAT
    s = one(os.path.join(ORDO_REF, 'Statics'), 'OLM_1stPersonMusketRifle - 002F9A')
    s = sub1(s, r'^FormKey: .*$', 'FormKey: 000801:' + ME)
    s = sub1(s, r'^EditorID: .*$', 'EditorID: 1stPersonZP_ClockworkThunder')
    s = sub1(s, r'^(Model:\n  File: ).*$', lambda m: m.group(1) + MODEL)
    s = sub1(s, r'^(Model:\n  File: .*\n)  Data: .*\n', r'\g<1>')
    rec('Statics', '1stPersonZP_ClockworkThunder', '000801', s)

    # the script's tunables must match the generator's (description text)
    psc = read(os.path.join(ROOT, 'src', 'ClockworkThunder', 'Scripts', 'source', CHAIN_SCRIPT + '.psc'))
    assert re.search(r'^Int Property Jumps = %d AutoReadOnly' % CHAIN_JUMPS, psc, re.M), 'Jumps differs'
    assert re.search(r'^Float Property Range = %s AutoReadOnly' % CHAIN_RANGE, psc, re.M), 'Range differs'

    # 80B EXPL: Prophecy's flash-less chain explosion without the Chain flag
    e = one(os.path.join(PROPHECY, 'Explosions'), 'ZP_Prophecy_DragonsBreath_Blast_Shock - 000B01')
    e = sub1(e, r'^FormKey: .*$', 'FormKey: 00080B:' + ME)
    e = sub1(e, r'^EditorID: .*$', 'EditorID: ZP_ClockworkThunderBoltBlast')
    e = sub1(e, r'^- Chain\n', '')
    rec('Explosions', 'ZP_ClockworkThunderBoltBlast', '00080B', e)

    # 80A MGEF: the bolt's damage effect on that explosion
    b = one(os.path.join(PROPHECY, 'MagicEffects'), 'ZP_Prophecy_DragonsBreath_Effect_Shock - 000AFD')
    b = sub1(b, r'^FormKey: .*$', 'FormKey: 00080A:' + ME)
    b = sub1(b, r'^EditorID: .*$', 'EditorID: ZP_ClockworkThunderBoltEffect')
    b = sub1(b, r'^(Name:\n  TargetLanguage: English\n  Value: ).*$', r'\g<1>' + NAME)
    b = sub1(b, r'^Explosion: .*$', 'Explosion: 00080B:' + ME)
    b = sub1(b, r'^(Description:\n  TargetLanguage: English\n  Value: ).*$', r'\g<1>' + NAME + ' deals <mag> shock damage.')
    rec('MagicEffects', 'ZP_ClockworkThunderBoltEffect', '00080A', b)

    # 804 SPEL: Prophecy's chain lightning bolt, weaker, one target per cast (the script chains it)
    c = one(os.path.join(PROPHECY, 'Spells'), 'ZP_Prophecy_FlowStateChainLightning - 000B02')
    c = sub1(c, r'^FormKey: .*$', 'FormKey: 000804:' + ME)
    c = sub1(c, r'^EditorID: .*$', 'EditorID: ZP_ClockworkThunderChainLightning')
    c = sub1(c, r'^(Name:\n  TargetLanguage: English\n  Value: ).*$', r'\g<1>' + NAME)
    c = sub1(c, r'^- BaseEffect: 000AFD:Zenderal - Prophecy\.esp\n  Data:\n    Magnitude: 40\n    Area: \d+\n',
             '- BaseEffect: 00080A:%s\n  Data:\n    Magnitude: %d\n' % (ME, CHAIN_DAMAGE))
    # + the stun check on the same target
    c = c.rstrip('\n') + '\n' + '\n'.join([
        '- BaseEffect: 000809:' + ME,
        '  Data: {}',
    ]) + '\n'
    rec('Spells', 'ZP_ClockworkThunderChainLightning', '000804', c)

    # 807 MGEF: the stun. Enderal's Arcane Archer affinity paralysis 14CEBD (shock hit shader, MagicParalysis
    # keyword, its immunity conditions: Starling constructs 035D59 / 0F23C5 and restrained actors) as a Target
    # Actor effect: no projectile, duration fixed (no PowerAffectsDuration)
    p = one(os.path.join(BASE, 'MagicEffects'), '_00E_AbAffinityArcaneArcher_ParalysisME - 14CEBD')
    p = sub1(p, r'^FormKey: .*$', 'FormKey: 000807:' + ME)
    p = sub1(p, r'^EditorID: .*$', 'EditorID: ZP_ClockworkThunderStunEffect')
    p = sub1(p, r'^Name:\n  TargetLanguage: English\n  Values:\n(?:  - .*\n    .*\n)+', 'Name:\n  TargetLanguage: English\n  Value: Stunned\n')
    p = sub1(p, r'^- PowerAffectsDuration\n', '')
    p = sub1(p, r'^Projectile: .*\n', '')
    p = sub1(p, r'^TargetType: Aimed$', 'TargetType: TargetActor')
    p = sub1(p, r'^Description:\n  TargetLanguage: English\n  Values:\n(?:  - .*\n    .*\n)+',
             'Description:\n  TargetLanguage: English\n  Value: Stunned by lightning for <dur> seconds.\n')
    rec('MagicEffects', 'ZP_ClockworkThunderStunEffect', '000807', p)

    # 808 SPEL: the stun, cast by 809's script from the player straight onto the target
    rec('Spells', 'ZP_ClockworkThunderStun', '000808', '\n'.join([
        'FormKey: 000808:' + ME,
        'EditorID: ZP_ClockworkThunderStun',
        'Name:',
        '  TargetLanguage: English',
        '  Value: Clockwork Thunder',
        'EquipmentType: 013F44:Skyrim.esm',
        'Description:',
        '  TargetLanguage: English',
        "  Value: ''",
        'Flags:',
        '- ManualCostCalc',
        '- NoAbsorbOrReflect',
        'CastType: FireAndForget',
        'TargetType: TargetActor',
        'Effects:',
        '- BaseEffect: 000807:' + ME,
        '  Data:',
        '    Duration: %d' % STUN_SECONDS,
    ]))

    # 809 MGEF: the level check on every actor the chain lightning reaches
    rec('MagicEffects', 'ZP_ClockworkThunderStunCheck', '000809', '\n'.join([
        'FormKey: 000809:' + ME,
        'EditorID: ZP_ClockworkThunderStunCheck',
        'VirtualMachineAdapter:',
        '  Scripts:',
        '  - Name: ZP_ClockworkThunderStunScript',
        '    Properties:',                 # Spriggit's order: by name
        '    - MutagenObjectType: ScriptObjectProperty',
        '      Name: PlayerRef',
        '      Object: 000014:Skyrim.esm',
        '    - MutagenObjectType: ScriptObjectProperty',
        '      Name: StunSpell',
        '      Object: 000808:' + ME,
        'Name:',
        '  TargetLanguage: English',
        '  Value: Clockwork Thunder',
        'Flags:',
        '- Hostile',
        '- NoHitEvent',
        '- NoDuration',
        '- NoMagnitude',
        '- HideInUI',
        '- NoHitEffect',
        'Archetype:',
        '  MutagenObjectType: MagicEffectArchetype',
        '  Type: Script',
        'CastType: FireAndForget',
        'TargetType: Aimed',
        'DualCastScale: 1',
        'CastingSoundLevel: Silent',
        'Sounds: []',
        'Description:',
        '  TargetLanguage: English',
        "  Value: ''",
    ]))

    # 803 MGEF: script effect that starts the chain on the struck enemy
    rec('MagicEffects', 'ZP_ClockworkThunderChainEffect', '000803', '\n'.join([
        'FormKey: 000803:' + ME,
        'EditorID: ZP_ClockworkThunderChainEffect',
        'VirtualMachineAdapter:',
        '  Scripts:',
        '  - Name: ' + CHAIN_SCRIPT,
        '    Properties:',                 # Spriggit's order: by name
        '    - MutagenObjectType: ScriptObjectProperty',
        '      Name: Bolt',
        '      Object: 000804:' + ME,
        '    - MutagenObjectType: ScriptObjectProperty',
        '      Name: EmptyActivator',
        '      Object: 0B79FF:Skyrim.esm',  # FXEmptyActivator: bolts fly marker to marker (an actor casts along its facing)
        '    - MutagenObjectType: ScriptObjectProperty',
        '      Name: PlayerRef',
        '      Object: 000014:Skyrim.esm',
        'Name:',
        '  TargetLanguage: English',
        '  Value: Chain Lightning',
        'Keywords:',
        '- 01CEAF:Skyrim.esm',             # MagicDamageShock (same as the chain bolt's effect)
        'Flags:',
        '- Hostile',
        '- Detrimental',
        '- NoHitEvent',
        '- NoDuration',
        '- NoMagnitude',
        '- NoArea',
        '- NoHitEffect',
        'Archetype:',
        '  MutagenObjectType: MagicEffectArchetype',
        '  Type: Script',
        'CastType: FireAndForget',
        'TargetType: Touch',
        'DualCastScale: 1',
        'CastingSoundLevel: Silent',
        'Sounds: []',
        'Description:',
        '  TargetLanguage: English',
        '  Value: Every shot that hits sends a chain of lightning from the enemy to up to %d enemies nearby, '
        'bouncing from one to the next, %d shock damage each, and stuns those below your level for %d seconds.'
        % (CHAIN_JUMPS, CHAIN_DAMAGE, STUN_SECONDS),
        # no "target alive" condition: a killing shot still sends the lightning on to the enemies around
    ]))

    # 802 ENCH
    rec('ObjectEffects', 'ZP_ClockworkThunderShot', '000802', '\n'.join([
        'FormKey: 000802:' + ME,
        'EditorID: ZP_ClockworkThunderShot',
        'Name:',
        '  TargetLanguage: English',
        '  Value: Chain Lightning',
        'EnchantmentCost: 1',
        'Flags:',
        '- NoAutoCalc',
        'CastType: FireAndForget',
        'EnchantmentAmount: %d' % CHARGE,
        'TargetType: Touch',
        'EnchantType: Enchantment',
        'Effects:',
        '- BaseEffect: 000803:' + ME,
        '  Data: {}',
    ]))

    # 805 COBJ temper
    t = one(os.path.join(ORDO_REF, 'ConstructibleObjects'), 'OLMTemperMatchlock_AlikrRifle - 00F5D6')
    t = sub1(t, r'^FormKey: .*$', 'FormKey: 000805:' + ME)
    t = sub1(t, r'^EditorID: .*$', 'EditorID: ZP_TemperClockworkThunder')
    t = sub1(t, r'^(    Item: )0F11C0:Skyrim\.esm$', r'\g<1>' + STARLING_INGOT)
    t = sub1(t, r'^CreatedObject: .*$', 'CreatedObject: 000800:' + ME)
    rec('ConstructibleObjects', 'ZP_TemperClockworkThunder', '000805', t)

    # 806 REFR + cell header
    (x, y, z), (rx, ry, rz), (lo, hi) = placement(mesh)
    cell = read(os.path.join(BASE, CELL_DIR, 'RecordData.yaml'))
    # a non-localized plugin keeps only the English name (Spriggit writes it back that way)
    cell = sub1(cell, r'^Name:\n  TargetLanguage: English\n  Values:\n  - Language: English\n    String: (.*)\n(?:  - .*\n    .*\n)*',
                r'Name:\n  TargetLanguage: English\n  Value: \g<1>\n')
    cut = min(cell.index(k) for k in ('\nNavigationMeshes:', '\nPersistent:', '\nTemporary:') if k in cell)
    import numpy as np
    f32 = [str(np.float32(v)) for v in (x, y, z)]    # the float the plugin stores, as Spriggit prints it
    cell = cell[:cut + 1] + '\n'.join([
        'Temporary:',
        '- MutagenObjectType: PlacedObject',
        '  FormKey: 000806:' + ME,
        '  Base: 000800:' + ME,
        '  Placement:',
        '    Position: %s, %s, %s' % tuple(f32),
        '    Rotation: %g, %.7f, %g' % (rx, ry, rz),
    ])
    write(CELL_DIR + '/RecordData.yaml', cell)
    for g in ('Cells/8/GroupRecordData.yaml', 'Cells/8/1/GroupRecordData.yaml'):
        write(g, read(os.path.join(BASE, g)))
    write('Cells/GroupRecordData.yaml', '{}')     # what Spriggit writes back for this plugin's cell group
    print('rifle root bounds %s .. %s' % (lo.round(1), hi.round(1)))
    print('placed at %.1f, %.1f, %.1f rotation %s' % (x, y, z, (rx, round(ry, 4), rz)))
    print('records written to', OUT)


if __name__ == '__main__':
    main()
