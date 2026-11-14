"""Argent Verdict's records (curator 2026-11-13): a unique silver great hammer on Pretty Enderal Armory's Aeterna
Warhammer, all silver with a dark navy leather grip and a clenched fist for its head's centre (tools/01's own mesh),
whose power attacks have a 25% chance to Smite (Prophecy's Hallowed Flare sky-bolt).

  800 WEAP ZP_ArgentVerdict          <- EGO's Aeterna Warhammer 07C993: 46 damage (EGO 42; Qalian's Absolution 44),
                                        crit 23, speed 0.65, value 1500; keywords: Aeterna material (EGO's smithing),
                                        silver (EGO's silver perks vs undead, Prophecy's Smite talent), unique, no
                                        enchanting, no vendor; tools/01's mesh (its textures in the mesh), bounds
                                        measured from it; enchantment 803
  801 STAT 1stPersonZP_ArgentVerdict <- 1stPersonElvenWarhammer 036BD2 on the same mesh (Pretty's two are one file)
  802 retired (the first build's texture swap, TXST ZP_ArgentVerdictSilver): never reuse
  803 ENCH ZP_ArgentVerdictSmite     weapon enchantment: 804 when the PLAYER is power attacking, 25% (the effect's
                                        conditions; it is instant, so they are tested once per hit)
  804 MGEF ZP_ArgentVerdictSmiteEffect <- Prophecy's Smite effect A67 (ZP_HolyPlaceExplosion places the sky-bolt
                                        explosion A54, whose activator casts as the player), shown on the item card
  805 COBJ ZP_TemperArgentVerdict    <- the Aeterna Warhammer's grindstone temper 148AB7, new product
  806 WEAP ZP_ArgentVerdictGauntlet  "Argent Verdict (Gauntlet)": 800 on the gauntlet variant's mesh, for comparing the
                                        two in game (curator 2026-11-14: "save what we have but make a variant that is
                                        a spiked Gauntlet"); its own first-person static 807; shares 803/804
  807 STAT 1stPersonZP_ArgentVerdictGauntlet  801 on the gauntlet mesh

Usage:  python 02-build-records.py
"""
import importlib.util
import math
import os
import re
import shutil
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
OUT = os.path.join(ROOT, 'src', 'ArgentVerdict', 'ArgentVerdictESP')
BASE = os.path.join(ROOT, 'reference', 'base')
EGO = os.path.join(ROOT, 'reference', 'mods', 'EGO - Enderal Gameplay Overhaul')
PROPHECY = os.path.join(ROOT, 'src', 'Prophecy', 'ProphecyESP')
PROPHECY_ESP = 'Zenderal - Prophecy.esp'
EGO_ESP = 'Enderal SE - Gameplay Overhaul.esp'
ME = 'Zenderal - Argent Verdict.esp'

NAME = 'Argent Verdict'
PRETTY = r'Weapons\Elven\ElvenWarHammer.nif'         # Pretty's (Caenraes' Noble Armory model), the base record's
PRETTY_1P = r'Weapons\Elven\1stPersonElvenWarHammer.nif'
MODEL = r'Zenderal\ArgentVerdict\ArgentVerdict.nif'    # tools/01's, both views (the hand variant)
MODEL_GAUNTLET = r'Zenderal\ArgentVerdict\ArgentVerdictGauntlet.nif'   # tools/01's gauntlet variant
NAME_GAUNTLET = 'Argent Verdict (Gauntlet)'
TARGET = 'Zenderal - Patch Collection'                 # where tools/01 writes it
DAMAGE, CRIT, SPEED, VALUE = 46, 23, 0.65, 1500
CHARGE = 3000                                          # Sting and Rise's: ~3000 hits before a recharge
SMITE_CHANCE = 25                                      # curator: "Power attacks have a 25% chance to Smite"
KEYWORDS = ['01E71B:Skyrim.esm',   # WeapMaterialElven: Aeterna (EGO's smithing perks)
            '06727B:Skyrim.esm',   # WeapTypeMelee
            '06D930:Skyrim.esm',   # WeapTypeWarhammer
            '0C27BD:Skyrim.esm',   # MagicDisallowEnchanting (as Qalian's Absolution)
            '10AA1A:Skyrim.esm',   # WeapMaterialSilver
            '14CE9A:Skyrim.esm']   # WeapTypeUnique
SMITE_TEXT = ('Power attacks have a %d%% chance to call down a pillar of holy light on the target, 40 damage, while '
              'beams of light strike the enemies around it for 10 each. Undead take double damage.' % SMITE_CHANCE)
# the records copied, and the plugin each must still come from (scan of the Ultra load order)
EXPECTED_WINNERS = {
    '07C993:Skyrim.esm': EGO_ESP,           # Aeterna Warhammer
    '036BD2:Skyrim.esm': 'Skyrim.esm',      # its first-person static
    '148AB7:Skyrim.esm': 'Skyrim.esm',      # its temper
}


def read(path):
    with open(path, encoding='utf-8-sig', newline='') as f:
        return f.read().replace('\r\n', '\n')


def sub1(text, pattern, repl):
    out, n = re.subn(pattern, repl, text, count=1, flags=re.M)
    if n != 1:
        sys.exit('pattern not found: ' + pattern)
    return out


def one(folder, stem):
    hits = [f for f in os.listdir(folder) if stem in f]
    if len(hits) != 1:
        sys.exit('%s: expected one *%s*, found %s' % (folder, stem, hits))
    return read(os.path.join(folder, hits[0]))


def rec(folder, editor_id, formid, text):
    path = os.path.join(OUT, folder, '%s - %s_%s.yaml' % (editor_id, formid, ME))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text if text.endswith('\n') else text + '\n')


def english(text, field, value):
    out, n = re.subn(r'^%s:\n  TargetLanguage: English\n(?:  Value: .*\n|  Values:\n(?:  - .*\n(?:    .*\n)?)+)' % field,
                     '%s:\n  TargetLanguage: English\n  Value: %s\n' % (field, value), text, count=1, flags=re.M)
    if n != 1:
        sys.exit('no %s field' % field)
    return out


def _module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def check_winners():
    scan = _module('sr_scan', os.path.join(ROOT, 'src', 'StingAndRise', 'tools', '00-scan-overriders.py'))
    chains = {fk: [] for fk in EXPECTED_WINNERS}
    for name, path in scan.plugin_paths():
        for fk in scan.scan(path, set(EXPECTED_WINNERS)):
            chains[fk].append(name)
    for fk, want in EXPECTED_WINNERS.items():
        if not chains[fk] or chains[fk][-1] != want:
            sys.exit('%s: the winner is now %s, not %s: rebuild from it' % (fk, chains[fk][-1:] or 'nothing', want))
    print('winners unchanged:', ', '.join('%s %s' % (fk.split(':')[0], c[-1]) for fk, c in chains.items()))


def mesh_facts(model, shape):
    """tools/01's mesh, as the load order sees it (it must win its path): its bounds, every shape (the vertices the
    triangles use)."""
    sr = _module('sr_assets', os.path.join(ROOT, 'src', 'StingAndRise', 'tools', '01-build-assets.py'))
    mods = os.path.join(sr.MO2, 'mods')
    for rel in (PRETTY, PRETTY_1P):          # the base the mesh was built from
        src, _ = sr.winner(mods, sr.profile_mods(), 'meshes/' + rel.replace(chr(92), '/'))
        if src != sr.EXPECT_SOURCE:
            sys.exit('%s now comes from %s, not %s' % (rel, src, sr.EXPECT_SOURCE))
    src, nif = sr.load(mods, sr.profile_mods(), 'meshes/' + model.replace(chr(92), '/'))
    if src != TARGET:
        sys.exit('%s comes from %s, not %s: run tools/01 first' % (model, src, TARGET))
    names, pts = [], []
    for k in sr.nifse.node_children(nif.blocks[nif.roots[0]])[1]:
        if nif.btype(k) == 'BSTriShape':
            names.append(sr.name_of(nif, k))
            s = sr.nifse.read_trishape(nif.blocks[k])
            t, R, sc = sr.nifse.transform(nif.blocks[k])
            pts.append(s['pos'][np.unique(s['tris'])] * sc @ R.T + t)
    assert shape in names, ('not tools/01\'s mesh', model, names)
    P = np.concatenate(pts)
    lo = [int(math.floor(v)) for v in P.min(0)]
    hi = [int(math.ceil(v)) for v in P.max(0)]
    return 'ObjectBounds:\n  First: %d, %d, %d\n  Second: %d, %d, %d\n' % (*lo, *hi)


def main():
    check_winners()
    bounds = mesh_facts(MODEL, 'ZP_ArgentFist')
    bounds_g = mesh_facts(MODEL_GAUNTLET, 'ZP_ArgentGauntlet')
    for sub in ('Weapons', 'Statics', 'TextureSets', 'ObjectEffects', 'MagicEffects', 'ConstructibleObjects'):   # TextureSets: the retired 802
        shutil.rmtree(os.path.join(OUT, sub), ignore_errors=True)

    # 800 the hammer
    w = one(os.path.join(EGO, 'Weapons'), '07C993_Skyrim.esm')
    assert re.search(r'^  Damage: 42$', w, re.M) and 'Speed: 0.6\n' in w and re.search(r'^Critical:\n  Damage: 21$', w, re.M)
    w = sub1(w, r'^FormKey: .*$', 'FormKey: 000800:' + ME)
    w = sub1(w, r'^EditorID: .*$', 'EditorID: ZP_ArgentVerdict')
    w = sub1(w, r'^ObjectBounds:\n  First: .*\n  Second: .*\n', bounds)
    w = english(w, 'Name', NAME)
    assert 'File: ' + PRETTY in w
    w = sub1(w, r'^Model:\n  File: .*\n  Data: .*\n', lambda m: 'Model:\n  File: %s\n' % MODEL)   # Data = the old texture hashes
    w = sub1(w, r'^(EquipmentType: )', lambda m: 'ObjectEffect: 000803:%s\nEnchantmentAmount: %d\n' % (ME, CHARGE) + m.group(1))
    w = sub1(w, r'^Keywords:\n(?:- .*\n)+', 'Keywords:\n' + ''.join('- %s\n' % k for k in KEYWORDS))
    w = sub1(w, r'^FirstPersonModel: .*$', 'FirstPersonModel: 000801:' + ME)
    w = sub1(w, r'^(BasicStats:\n  Value: )\d+$', r'\g<1>%d' % VALUE)
    w = sub1(w, r'^(  Weight: \d+\n  Damage: )\d+$', r'\g<1>%d' % DAMAGE)
    w = sub1(w, r'^(  Speed: )[\d.]+$', r'\g<1>%g' % SPEED)
    w = sub1(w, r'^(Critical:\n  Damage: )\d+$', r'\g<1>%d' % CRIT)
    rec('Weapons', 'ZP_ArgentVerdict', '000800', w)

    # 806 the gauntlet variant: the same hammer on the gauntlet mesh, its own first-person static 807
    g = sub1(w, r'^FormKey: .*$', 'FormKey: 000806:' + ME)
    g = sub1(g, r'^EditorID: .*$', 'EditorID: ZP_ArgentVerdictGauntlet')
    g = sub1(g, r'^ObjectBounds:\n  First: .*\n  Second: .*\n', bounds_g)
    g = english(g, 'Name', NAME_GAUNTLET)
    g = sub1(g, r'^Model:\n  File: .*\n', lambda m: 'Model:\n  File: %s\n' % MODEL_GAUNTLET)
    g = sub1(g, r'^FirstPersonModel: .*$', 'FirstPersonModel: 000807:' + ME)
    rec('Weapons', 'ZP_ArgentVerdictGauntlet', '000806', g)

    # 801 its first-person static
    st = one(os.path.join(BASE, 'Skyrim', 'Statics'), '036BD2_Skyrim.esm')
    assert 'File: ' + PRETTY_1P in st
    st = sub1(st, r'^FormKey: .*$', 'FormKey: 000801:' + ME)
    st = sub1(st, r'^EditorID: .*$', 'EditorID: 1stPersonZP_ArgentVerdict')
    st = sub1(st, r'^Model:\n  File: .*\n  Data: .*\n', lambda m: 'Model:\n  File: %s\n' % MODEL)
    rec('Statics', '1stPersonZP_ArgentVerdict', '000801', st)
    sg = sub1(st, r'^FormKey: .*$', 'FormKey: 000807:' + ME)
    sg = sub1(sg, r'^EditorID: .*$', 'EditorID: 1stPersonZP_ArgentVerdictGauntlet')
    sg = sub1(sg, r'^Model:\n  File: .*\n', lambda m: 'Model:\n  File: %s\n' % MODEL_GAUNTLET)
    rec('Statics', '1stPersonZP_ArgentVerdictGauntlet', '000807', sg)

    # 803 the enchantment: Smite on the player's power attacks, SMITE_CHANCE percent
    rec('ObjectEffects', 'ZP_ArgentVerdictSmite', '000803', '\n'.join([
        'FormKey: 000803:' + ME,
        'EditorID: ZP_ArgentVerdictSmite',
        'Name:', '  TargetLanguage: English', '  Value: ' + NAME,
        'EnchantmentCost: 1',
        'Flags:', '- NoAutoCalc',
        'CastType: FireAndForget',
        'EnchantmentAmount: %d' % CHARGE,
        'TargetType: Touch',
        'EnchantType: Enchantment',
        'Effects:',
        '- BaseEffect: 000804:' + ME,
        '  Data: {}',
        '  Conditions:',
        '  - MutagenObjectType: ConditionFloat',
        '    Data:',
        '      MutagenObjectType: IsPowerAttackingConditionData',
        '      RunOnType: Reference',
        '      Reference: 000014:Skyrim.esm',
        '    ComparisonValue: 1',
        '  - MutagenObjectType: ConditionFloat',
        '    CompareOperator: LessThan',
        '    Data:',
        '      MutagenObjectType: GetRandomPercentConditionData',
        '    ComparisonValue: %d' % SMITE_CHANCE]))

    # 804 Smite, Prophecy's effect with a description on the item card
    e = one(os.path.join(PROPHECY, 'MagicEffects'), '000A67_' + PROPHECY_ESP)
    assert 'Name: ZP_HolyPlaceExplosion' in e and 'Object: 000A54:' + PROPHECY_ESP in e and '- HideInUI\n' in e
    e = sub1(e, r'^FormKey: .*$', 'FormKey: 000804:' + ME)
    e = sub1(e, r'^EditorID: .*$', 'EditorID: ZP_ArgentVerdictSmiteEffect')
    e = sub1(e, r'^- HideInUI\n', '')
    e = sub1(e, r'^- NoMagnitude\n- NoArea\n- NoDuration\n', '- NoDuration\n- NoMagnitude\n- NoArea\n')   # flag-bit order
    e = english(e, 'Description', SMITE_TEXT)
    rec('MagicEffects', 'ZP_ArgentVerdictSmiteEffect', '000804', e)

    # 805 its grindstone temper (Aeterna material; enchanted, so Enderal's Arcane Blacksmith rule applies)
    c = one(os.path.join(BASE, 'Skyrim', 'ConstructibleObjects'), '148AB7_Skyrim.esm')
    c = sub1(c, r'^FormKey: .*$', 'FormKey: 000805:' + ME)
    c = sub1(c, r'^EditorID: .*$', 'EditorID: ZP_TemperArgentVerdict')
    c = sub1(c, r'^CreatedObject: .*$', 'CreatedObject: 000800:' + ME)
    rec('ConstructibleObjects', 'ZP_TemperArgentVerdict', '000805', c)
    print('records written to', OUT)


if __name__ == '__main__':
    main()
