"""Caldera's records (curator 2026-11-16: "lets make a Unique 1handed Mace, I want it to look like a Forge Hammer with
cracks in it with Molten lava in them"; effect: "Burning hits, but charge enough light attacks and a power attack can
trigger a volcanic eruption (look for a spell effect or 2 to combine)").

  800 WEAP ZP_Caldera                 <- EGO's Aeterna Mace 07C990 (the winner): DAMAGE, SPEED (Mace Speed's 1H mace
                                         speed), REACH (Precision's weapon capsule follows it), CRIT, VALUE, WEIGHT; keywords Aeterna material (EGO's smithing),
                                         melee, mace, no enchanting, unique (no VendorItemWeapon); tools/01's mesh, both
                                         views, bounds measured from it; enchantment 803; script ZP_CalderaEquipScript
  801 STAT 1stPersonZP_Caldera        <- 1stPersonElvenMace 036BCF on the same mesh (Pretty's two are one file)
  802 COBJ ZP_TemperCaldera           <- the Aeterna Mace's grindstone temper 148ABB, new product
  803 ENCH ZP_CalderaEnchant          weapon enchantment, on every hit (instant effects: their conditions are tested
                                         once per hit): 804 always; 805 on a light attack on an actor hostile to the
                                         player while 807 is below HITS; 806 on a power attack on one while 807 is HITS
                                         and the player has MANA_COST Mana (the fallback: the eruption normally starts
                                         at the swing, 81B)
  804 MGEF ZP_CalderaBurnEffect       "Burning": Enderal's Fire Arrow burn _00E_A1_FireArrowEnchME 067252 (Flame Shot's
                                         copy, the winner) as Sting and Rise's Sunrise has it: no NoRecast (a new hit
                                         refreshes the burn), the fire hit shader FireFXShader 01B212; BURN
  805 MGEF ZP_CalderaChargeMGEF       a charge: an instant script effect (ZP_CalderaChargeScript), hidden
  806 MGEF ZP_CalderaEruptionEffect   "Eruption": the release on a hit (ZP_CalderaEruptionScript), with the item
                                         card's text; the fallback for a swing the game never reported
  807 GLOB ZP_CalderaCharges          0..HITS
  808 MGEF ZP_CalderaTiersMGEF        the cracks' display: a constant script effect (ZP_CalderaTiersScript), which
                                         also hears the hammer's swings and casts 81B on a full-charge power attack
  809 SPEL ZP_CalderaTiers            the ability carrying 808, added while the hammer is equipped and by a charge
  80A EXPL ZP_CalderaShockwave        <- Fire Storm's explosion 08196B (Embers XD's, the winner) on tools/01's
                                         CalderaShockwave.nif (its ring scaled to SHOCK_RADIUS); no force, damage or
                                         image space: the blast is the spell
  80B SPEL ZP_CalderaBlast            80C (fire damage) + 80D (stagger), applied by the eruption script, which sets
                                         the damage by the player's Elementalism (BLAST); the record carries it at 50
  80C MGEF ZP_CalderaBlastDamage      <- Apocalypse's lava bomb damage 0834B5 (Unresolved References Cleanup's, the
                                         winner), Touch, no projectile, no script; never the player (its condition)
  80D MGEF ZP_CalderaBlastStagger     <- Apocalypse's lava bomb stagger 0834BA, Touch, no projectile
  80E EXPL ZP_CalderaVolcano          <- Apocalypse's Volcano explosion 0834AE (Pyroclasm), placing 80F; no image space;
                                         its sound the curator's volcano eruption (814)
  80F ACTI ZP_CalderaVolcanoController <- Apocalypse's volcano controller 0834AD (WB_VolcanoController2_Script): the
                                         fountain and its light as Apocalypse's, ERUPT seconds, bombs within
                                         ERUPT_RADIUS, firing 810
  810 SPEL ZP_CalderaLavaBomb         <- Apocalypse's lava bomb 0834B3: its damage 0834B5 (BOMB, by Elementalism, set
                                         by the eruption script; the record carries it at 50), its stagger 0834BA;
                                         without the Intense Flames fear 0F392D (enemies running from a melee weapon)
  811 SOUN ZP_CalderaChargedSound     the full charge: 815 (vanilla's oil trap igniting TRPOilIgniteHighSD 04251D
                                         until the curator: "add this sound when the hammer is charged")
  812 ---- retired: ACTI ZP_CalderaFissures, the glowing cracked field (curator 2026-11-16: "remove the fissure
                                         effect and instead add smaller volcanos scattered around"); never reuse
  813 SNDR ZP_CalderaLavaLoopSD       the curator's lava river ("add this sound for the lava fissures"; it now plays
                                         once at the eruption, through 81A, while the small volcanoes spit), tools/03,
                                         looping, mono, heard within 1800 (SOMMono01800_verb, Whisper's wisp's)
  814 SNDR ZP_CalderaEruptionSD       the curator's volcano eruption ("and this one too"), tools/03, mono, heard within
                                         6000 (SOMMono06000_verb)
  815 SNDR ZP_CalderaChargedSD        the curator's metal whoosh (MA_Floraphonic_Swing_Whoosh_Metal_Hit_39), tools/03,
                                         mono, SOMMono06000_verb (Argent Verdict's charged bell's)
  816 ACTI ZP_CalderaVentController   a small volcano ("smaller volcanos scattered around, they do very little damage
                                         mainly there for effect"): Apocalypse's volcano controller 0834AD again
                                         (80F's record), its fountain 817, its light 818, VENT_ERUPT seconds, a bomb
                                         (819) every VENT_RATE seconds within VENT_RADIUS, lobbed VENT_HEIGHT up, the
                                         fountain rising 28 x VENT_SCALE; no looping sound of its own. The eruption
                                         script places VENTS of them on the ground round the volcano
  817 ACTI ZP_CalderaVentFountain     <- Apocalypse's volcano fountain 0834B2 on tools/01's CalderaVent.nif (VENT_SCALE),
                                         bounds scaled; no looping sound (five large-fire loops drowned the volcano)
  818 LIGH ZP_CalderaVentLight        <- Apocalypse's fountain light 0834B8, radius VENT_LIGHT
  819 SPEL ZP_CalderaVentBomb         <- Apocalypse's lava bomb 0834B3 as 810, VENT_BOMB fire damage (flat), no stagger,
                                         no fear: for show
  81A SOUN ZP_CalderaLavaLoopSound    the curator's lava river (813), played by the eruption script at the volcano for
                                         ERUPT + 1 seconds (Sound.Play, then Sound.StopInstance)
  81B SPEL ZP_CalderaEruptionSwing    the eruption on the swing (curator 2026-11-16: "add a mana cost to the power
                                         attack trigger and make it so you don't need to hit to trigger it"): a
                                         self spell carrying 81C, cast on the player by ZP_CalderaTiersScript when a
                                         power attack swings the hammer at a full charge, hit or miss (Orbit Ward's
                                         self spell shape, Prophecy B76)
  81C MGEF ZP_CalderaEruptionSwingEffect  the same eruption script as 806 on the player (Self, hidden): it erupts
                                         under the enemy swung at, or in front of the player, and spends MANA_COST

Masters Apocalypse (its volcano's script, meshes and effects run as they are). The scripts' constants are checked
against the ones here (HITS, TIERS, SHOCK_RADIUS, MANA_COST).

Usage:  python 02-build-records.py
"""
import importlib.util
import math
import os
import re
import shutil
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
OUT = os.path.join(ROOT, 'src', 'Caldera', 'CalderaESP')
SCRIPTS = os.path.join(ROOT, 'src', 'Caldera', 'Scripts', 'source')
BASE = os.path.join(ROOT, 'reference', 'base', 'Skyrim')
EGO = os.path.join(ROOT, 'reference', 'mods', 'EGO - Enderal Gameplay Overhaul')
APOC = os.path.join(ROOT, 'reference', 'mods', 'Apocalypse - Magic of Skyrim')
EMBERS = os.path.join(ROOT, 'reference', 'mods', 'EmbersXDesp')
FLAMESHOT = os.path.join(ROOT, 'src', 'FlameShot', 'FlameShotESP')
CLEANUP = os.path.join(ROOT, 'src', 'UnresolvedRefsCleanup')
APOC_ESP = 'Apocalypse - Magic of Skyrim.esp'
EGO_ESP = 'Enderal SE - Gameplay Overhaul.esp'
ME = 'Zenderal - Caldera.esp'
TARGET = 'Zenderal - Patch Collection'

NAME = 'Caldera'
MODEL = r'Zenderal\Caldera\Caldera.nif'
SHOCK_MODEL = r'Zenderal\Caldera\CalderaShockwave.nif'
PRETTY = r'Weapons\Elven\ElvenMace.nif'
DAMAGE, SPEED, CRIT, VALUE, WEIGHT = 33, 0.9, 24, 1500, 19     # EGO's Aeterna Mace: 29 / 0.8 (0.9 under Mace Speed)
REACH = 1.15                       # (1H's 1.0 until the curator: "increase the hit range on the weapon a little too it
#                                    seems a little short"; the hammer is 38 units long)
CHARGE = 3000                                                    # enchantment charge (Argent Verdict's)
KEYWORDS = ['01E71B:Skyrim.esm',   # WeapMaterialElven (EGO's Aeterna smithing)
            '06727B:Skyrim.esm',   # WeapTypeMelee
            '08F958:Skyrim.esm',   # WeapTypeMace
            '0C27BD:Skyrim.esm',   # MagicDisallowEnchanting
            '14CE9A:Skyrim.esm']   # WeapTypeUnique
HITS = 8                           # light-attack hits for a full charge (the scripts' Hits, checked)
TIERS = 5                          # the head's crack tiers (tools/01 TIERS, the scripts' Tiers, checked)
BURN = (5, 6)                      # fire damage a second, seconds: Enderal's own Burning (Sunrise's)
MANA_COST = 20                     # each eruption (curator 2026-11-16: "add a mana cost to the power attack trigger";
#                                    Argent Verdict's Smite costs the same); the eruption script's ManaCost, checked
# the eruption's fire damage by the player's Elementalism (curator 2026-11-16: "I want the damage of the fissure /
# volcano to scale with elementalism", then "lower the damage of the fissure / volcano by 25 %"): base + per point,
# set by the eruption script before each eruption (the script's BlastBase / BlastPerPoint / BombBase / BombPerPoint,
# checked), up to SKILL_CAP; the records carry the numbers at SKILL_RECORD
BLAST = (22.5, 0.45)               # the ring of fire, to each enemy in it: 22.5 at 0, 45 at 50, 67.5 at 100
BOMB = (7.5, 0.19)                 # each lava bomb: 7.5 at 0, 17 at 50, 26.5 at 100 (Apocalypse's 40)
SKILL_CAP = 100
SKILL_RECORD = 50
BLAST_STAGGER = 0.5
SHOCK_RADIUS = 350                 # the eruption script's ShockRadius (checked; tools/01 scales the ring to it)
ERUPT = 6                          # seconds the volcano spits (Apocalypse's 10)
ERUPT_RADIUS = 450                 # bombs land within this of it (Apocalypse's 750)
BOMB_STAGGER = 0.25
VENT_MODEL = r'Zenderal\Caldera\CalderaVent.nif'                       # tools/01 OUT_VENT (checked)
VENT_ERUPT = 4                     # seconds a small volcano spits
VENT_RATE = 0.5                    # seconds between its bombs (the volcano's 0.125)
VENT_RADIUS = 160                  # its bombs land within this of it
VENT_HEIGHT = 700                  # its bombs are lobbed at a point this far up (the volcano's 2000)
VENT_BOMB = 3                      # fire damage a bomb, flat
VENT_LIGHT = 192                   # its light's radius (the volcano's 384)
LAVA_FILE = r'data\sound\fx\Zenderal\Caldera\CalderaLavaLoop.wav'     # tools/03 --lava (checked)
ERUPTION_FILE = r'data\sound\fx\Zenderal\Caldera\CalderaEruption.wav' # tools/03 --eruption (checked)
CHARGED_FILE = r'data\sound\fx\Zenderal\Caldera\CalderaCharged.wav'   # tools/03 --charged (checked)
TEXT = ('Sets the enemy ablaze, %d fire damage a second for %d seconds. Its cracks start cold, and every two light '
        'attacks that hit an enemy fill more of them with molten fire. Once it is full, your next power attack, hit '
        'or miss, spends %d Mana and splits the ground before you, under the enemy you swing at. A ring of fire '
        'bursts out, %g fire damage plus %g for every point of '
        'Elementalism to every enemy within it, and a volcano erupts there for %d seconds, raining lava bombs that '
        'strike for %g fire damage plus %g for every point of Elementalism, and smaller volcanoes break open round it.'
        % (BURN[0], BURN[1], MANA_COST, BLAST[0], BLAST[1], ERUPT, BOMB[0], BOMB[1]))
assert ': ' not in TEXT
EXPECTED_WINNERS = {
    '07C990:Skyrim.esm': EGO_ESP,                          # Aeterna Mace
    '036BCF:Skyrim.esm': 'Skyrim.esm',                     # its first-person static
    '148ABB:Skyrim.esm': 'Skyrim.esm',                     # its temper
    '067252:Skyrim.esm': 'Zenderal - Flame Shot.esp',      # Enderal's Fire Arrow burn
    '08196B:Skyrim.esm': 'Embers XD.esp',                  # Fire Storm's explosion
    '0834AD:' + APOC_ESP: APOC_ESP,                        # Volcano's controller
    '0834AE:' + APOC_ESP: APOC_ESP,                        # Volcano's explosion
    '0834B2:' + APOC_ESP: APOC_ESP,                        # its fountain
    '0834B8:' + APOC_ESP: APOC_ESP,                        # the fountain's light
    '0834B3:' + APOC_ESP: APOC_ESP,                        # its lava bomb
    '0834B5:' + APOC_ESP: 'Zenderal - Unresolved References Cleanup.esp',   # the bomb's damage
    '0834BA:' + APOC_ESP: APOC_ESP,                        # the bomb's stagger
}


def read(path):
    with open(path, encoding='utf-8-sig', newline='') as f:
        return f.read().replace('\r\n', '\n')


def sub1(text, pattern, repl):
    out, n = re.subn(pattern, repl, text, count=1, flags=re.M)
    if n != 1:
        sys.exit('pattern not found: ' + pattern)
    return out


def drop(text, pattern):
    out, n = re.subn(pattern, '', text, count=1, flags=re.M)
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


def at_record(scaled):
    """A base + per-point damage at SKILL_RECORD: what the record carries until the script sets it."""
    return round(scaled[0] + scaled[1] * SKILL_RECORD, 2)


def script_const(name, script, kind='Int'):
    m = re.search(r'^%s Property %s = ([\d.]+) AutoReadOnly' % (kind, name), read(os.path.join(SCRIPTS, script)), re.M)
    if not m:
        sys.exit('%s: no %s' % (script, name))
    return float(m.group(1))


DOC_LIMIT = 3000      # characters a script's docstring may have: the game's .pex loader copies each string into a
#                       fixed buffer and crashed at load on a 4407-byte one (2026-11-16; the list's longest working
#                       string is 3854 bytes, so the buffer is most likely 4096); detail belongs in arch-docs/


def check_docstrings():
    for name in sorted(os.listdir(SCRIPTS)):
        if name.lower().endswith('.psc'):
            m = re.search(r'^Scriptname .*\n\{(.*?)\}', read(os.path.join(SCRIPTS, name)), re.S | re.M)
            if m and len(m.group(1)) > DOC_LIMIT:
                sys.exit('%s: its docstring is %d characters, over %d: the game crashes loading a .pex string over '
                         '~4 KB; move the detail to arch-docs/patches/Caldera.md' % (name, len(m.group(1)), DOC_LIMIT))


def check_constants():
    check_docstrings()
    tools01 = read(os.path.join(HERE, '01-build-mesh.py'))
    if int(re.search(r'^TIERS = (\d+)', tools01, re.M).group(1)) != TIERS:
        sys.exit('tools/01 builds a different number of tiers')
    for script in ('ZP_CalderaTiersScript.psc', 'ZP_CalderaChargeScript.psc', 'ZP_CalderaEruptionScript.psc'):
        for const, want in (('Hits', HITS), ('Tiers', TIERS)):
            if script_const(const, script) != want:
                sys.exit('%s: %s is not %d' % (script, const, want))
    if script_const('ShockRadius', 'ZP_CalderaEruptionScript.psc', 'Float') != SHOCK_RADIUS:
        sys.exit('the eruption script\'s ShockRadius is not %d' % SHOCK_RADIUS)
    if script_const('ManaCost', 'ZP_CalderaEruptionScript.psc', 'Float') != MANA_COST:
        sys.exit('the eruption script spends %g Mana, the item card says %d'
                 % (script_const('ManaCost', 'ZP_CalderaEruptionScript.psc', 'Float'), MANA_COST))
    if script_const('SoundLife', 'ZP_CalderaEruptionScript.psc', 'Float') != ERUPT + 1:
        sys.exit('the eruption script\'s SoundLife is not %d' % (ERUPT + 1))
    for const, want in (('BlastBase', BLAST[0]), ('BlastPerPoint', BLAST[1]), ('BombBase', BOMB[0]),
                        ('BombPerPoint', BOMB[1]), ('SkillCap', SKILL_CAP)):
        if abs(script_const(const, 'ZP_CalderaEruptionScript.psc', 'Float') - want) > 1e-6:
            sys.exit('the eruption script\'s %s is not %g' % (const, want))
    out_vent = re.search(r"^OUT_VENT = '(.*)'", tools01, re.M).group(1)
    if out_vent.replace('/', chr(92)) != 'meshes' + chr(92) + VENT_MODEL:
        sys.exit('tools/01 writes %s, the fountain shows %s' % (out_vent, VENT_MODEL))
    sounds = _module('cal_sounds', os.path.join(HERE, '03-install-sounds.py'))
    for out, rel in ((sounds.LAVA_OUT, LAVA_FILE), (sounds.ERUPTION_OUT, ERUPTION_FILE),
                     (sounds.CHARGED_OUT, CHARGED_FILE)):
        if out.replace('/', chr(92)) != rel[len('data' + chr(92)):]:
            sys.exit('tools/03 writes %s, the record plays %s' % (out, rel))


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


def mesh_bounds():
    """tools/01's mesh as the load order sees it (it must win its path): bounds of every shape at the scale it shows
    (the lit tier: Tier0; the others are the same head)."""
    sr = _module('sr_assets', os.path.join(ROOT, 'src', 'StingAndRise', 'tools', '01-build-assets.py'))
    mods = os.path.join(sr.MO2, 'mods')
    src, _ = sr.winner(mods, sr.profile_mods(), 'meshes/' + PRETTY.replace(chr(92), '/'))
    if src != sr.EXPECT_SOURCE:
        sys.exit('%s now comes from %s, not %s' % (PRETTY, src, sr.EXPECT_SOURCE))
    src, nif = sr.load(mods, sr.profile_mods(), 'meshes/' + MODEL.replace(chr(92), '/'))
    if src != TARGET:
        sys.exit('%s comes from %s, not %s: run tools/01 first' % (MODEL, src, TARGET))
    pts, names = [], []

    def walk(k, M):
        t, R, sc = sr.nifse.transform(nif.blocks[k])
        L = np.eye(4)
        L[:3, :3] = R * (sc if sc > 0 else 1.0)              # the tier nodes at scale 0 show at 1 when lit
        L[:3, 3] = t
        W = M @ L
        if nif.btype(k) == 'BSTriShape':
            s = sr.nifse.read_trishape(nif.blocks[k])
            names.append(sr.name_of(nif, k))
            P = s['pos'][np.unique(s['tris'])]
            pts.append(P @ W[:3, :3].T + W[:3, 3])
        elif nif.btype(k) in ('BSFadeNode', 'NiNode'):
            for c in sr.nifse.node_children(nif.blocks[k])[1]:
                if c >= 0 and nif.btype(c) in ('NiNode', 'BSTriShape'):
                    walk(c, W)
    walk(nif.roots[0], np.eye(4))
    assert 'ZP_CalderaHead0' in names, ('not tools/01\'s mesh', names)
    P = np.concatenate(pts)
    lo = [int(math.floor(v)) for v in P.min(0)]
    hi = [int(math.ceil(v)) for v in P.max(0)]
    print('caldera bounds', lo, hi)
    return 'ObjectBounds:\n  First: %d, %d, %d\n  Second: %d, %d, %d\n' % (*lo, *hi)


def script_effect(fid, editor_id, name, script, props, text, hidden, target='Touch'):
    lines = ['FormKey: %s:%s' % (fid, ME), 'EditorID: ' + editor_id, 'VirtualMachineAdapter:', '  Scripts:',
             '  - Name: ' + script, '    Properties:']
    for pname, obj in sorted(props.items()):
        lines += ['    - MutagenObjectType: ScriptObjectProperty', '      Name: ' + pname, '      Object: ' + obj]
    lines += ['Name:', '  TargetLanguage: English', '  Value: ' + name, 'Flags:', '- NoDuration', '- NoMagnitude',
              '- NoArea'] + (['- HideInUI'] if hidden else []) + ['- Painless', 'Archetype:',
              '  MutagenObjectType: MagicEffectArchetype', '  Type: Script', 'CastType: FireAndForget'] + (
              ['TargetType: ' + target] if target != 'Self' else []) + [   # Self is 0, the default: Spriggit omits it
              'DualCastScale: 1', 'CastingSoundLevel: Silent', 'Sounds: []', 'Description:',
              '  TargetLanguage: English', "  Value: %s" % (text if text else "''")]
    return '\n'.join(lines)


def cond_hostile():
    return ['  - MutagenObjectType: ConditionFloat', '    Data:', '      MutagenObjectType: IsHostileToActorConditionData',
            '      TargetNpc: 000014:Skyrim.esm', '    ComparisonValue: 1']


def cond_power(value):
    return ['  - MutagenObjectType: ConditionFloat', '    Data:', '      MutagenObjectType: IsPowerAttackingConditionData',
            '      RunOnType: Reference', '      Reference: 000014:Skyrim.esm'] + (['    ComparisonValue: 1'] if value else [])


def cond_charges(op, value):
    return ['  - MutagenObjectType: ConditionFloat', '    CompareOperator: ' + op, '    Data:',
            '      MutagenObjectType: GetGlobalValueConditionData', '      Global: 000807:' + ME,
            '    ComparisonValue: %d' % value]

def cond_mana():
    return ['  - MutagenObjectType: ConditionFloat', '    CompareOperator: GreaterThanOrEqualTo', '    Data:',
            '      MutagenObjectType: GetActorValueConditionData', '      RunOnType: Reference',
            '      Reference: 000014:Skyrim.esm', '      ActorValue: Magicka', '    ComparisonValue: %d' % MANA_COST]


def main():
    check_constants()
    check_winners()
    bounds = mesh_bounds()
    for sub in os.listdir(OUT):
        if os.path.isdir(os.path.join(OUT, sub)):
            shutil.rmtree(os.path.join(OUT, sub))

    # 800 the hammer
    w = one(os.path.join(EGO, 'Weapons'), '07C990_Skyrim.esm')
    assert re.search(r'^  Damage: 29$', w, re.M) and 'Speed: 0.8\n' in w and 'File: ' + PRETTY in w
    w = sub1(w, r'^FormKey: .*$', 'FormKey: 000800:' + ME)
    w = sub1(w, r'^EditorID: .*$', 'EditorID: ZP_Caldera')
    assert 'VirtualMachineAdapter' not in w
    w = sub1(w, r'^(EditorID: ZP_Caldera\n)', lambda m: m.group(1) + '\n'.join([
        'VirtualMachineAdapter:', '  Scripts:', '  - Name: ZP_CalderaEquipScript', '    Properties:',
        '    - MutagenObjectType: ScriptObjectProperty', '      Name: Hammer', '      Object: 000800:' + ME,
        '    - MutagenObjectType: ScriptObjectProperty', '      Name: PlayerRef', '      Object: 000014:Skyrim.esm',
        '    - MutagenObjectType: ScriptObjectProperty', '      Name: TierAbility', '      Object: 000809:' + ME, '']))
    w = sub1(w, r'^ObjectBounds:\n  First: .*\n  Second: .*\n', bounds)
    w = english(w, 'Name', NAME)
    w = sub1(w, r'^Model:\n  File: .*\n  Data: .*\n', lambda m: 'Model:\n  File: %s\n' % MODEL)
    w = sub1(w, r'^(EquipmentType: )', lambda m: 'ObjectEffect: 000803:%s\nEnchantmentAmount: %d\n' % (ME, CHARGE) + m.group(1))
    w = sub1(w, r'^Keywords:\n(?:- .*\n)+', 'Keywords:\n' + ''.join('- %s\n' % k for k in KEYWORDS))
    w = sub1(w, r'^FirstPersonModel: .*$', 'FirstPersonModel: 000801:' + ME)
    w = sub1(w, r'^(BasicStats:\n  Value: )\d+$', r'\g<1>%d' % VALUE)
    w = sub1(w, r'^(  Weight: )\d+$', r'\g<1>%d' % WEIGHT)
    w = sub1(w, r'^(  Damage: )29$', r'\g<1>%d' % DAMAGE)
    w = sub1(w, r'^(  Speed: )[\d.]+$', r'\g<1>%g' % SPEED)
    w = sub1(w, r'^(  Reach: )[\d.]+$', r'\g<1>%g' % REACH)
    w = sub1(w, r'^(Critical:\n  Damage: )\d+$', r'\g<1>%d' % CRIT)
    rec('Weapons', 'ZP_Caldera', '000800', w)

    # 801 its first-person static
    st = one(os.path.join(BASE, 'Statics'), '036BCF_Skyrim.esm')
    st = sub1(st, r'^FormKey: .*$', 'FormKey: 000801:' + ME)
    st = sub1(st, r'^EditorID: .*$', 'EditorID: 1stPersonZP_Caldera')
    st = sub1(st, r'^Model:\n  File: .*\n(?:  Data: .*\n)?', lambda m: 'Model:\n  File: %s\n' % MODEL)
    rec('Statics', '1stPersonZP_Caldera', '000801', st)

    # 802 its temper
    t = one(os.path.join(BASE, 'ConstructibleObjects'), '148ABB_Skyrim.esm')
    t = sub1(t, r'^FormKey: .*$', 'FormKey: 000802:' + ME)
    t = sub1(t, r'^EditorID: .*$', 'EditorID: ZP_TemperCaldera')
    t = sub1(t, r'^CreatedObject: 07C990:Skyrim\.esm$', 'CreatedObject: 000800:' + ME)
    rec('ConstructibleObjects', 'ZP_TemperCaldera', '000802', t)

    # 803 the enchantment
    rec('ObjectEffects', 'ZP_CalderaEnchant', '000803', '\n'.join([
        'FormKey: 000803:' + ME, 'EditorID: ZP_CalderaEnchant',
        'Name:', '  TargetLanguage: English', '  Value: ' + NAME,
        'EnchantmentCost: 1', 'Flags:', '- NoAutoCalc', 'CastType: FireAndForget',
        'EnchantmentAmount: %d' % CHARGE, 'TargetType: Touch', 'EnchantType: Enchantment', 'Effects:',
        '- BaseEffect: 000804:' + ME, '  Data:', '    Magnitude: %d' % BURN[0], '    Duration: %d' % BURN[1],
        '- BaseEffect: 000805:' + ME, '  Data: {}', '  Conditions:'] + cond_hostile() + cond_power(False)
        + cond_charges('LessThan', HITS) + [
        '- BaseEffect: 000806:' + ME, '  Data: {}', '  Conditions:'] + cond_hostile() + cond_power(True)
        + cond_charges('GreaterThanOrEqualTo', HITS) + cond_mana()))

    # 804 Burning: Enderal's Fire Arrow burn, as Sunrise has it
    f = one(os.path.join(FLAMESHOT, 'MagicEffects'), '067252_Skyrim.esm')
    f = sub1(f, r'^FormKey: .*$', 'FormKey: 000804:' + ME)
    f = sub1(f, r'^EditorID: .*$', 'EditorID: ZP_CalderaBurnEffect')
    f = english(f, 'Name', 'Burning')
    f = sub1(f, r'^- NoRecast\n', '')
    f = sub1(f, r'^(TaperWeight: .*\n)', r'\g<1>HitShader: 01B212:Skyrim.esm\n')     # FireFXShader
    f = english(f, 'Description', 'Sets the enemy ablaze, <mag> fire damage a second for <dur> seconds.')
    assert 'NoRecast' not in f and 'Chinese' not in f
    rec('MagicEffects', 'ZP_CalderaBurnEffect', '000804', f)

    # 805 a charge, 806 the eruption, 807 the charges, 808/809 the cracks' display
    rec('MagicEffects', 'ZP_CalderaChargeMGEF', '000805', script_effect(
        '000805', 'ZP_CalderaChargeMGEF', 'Caldera Charge', 'ZP_CalderaChargeScript',
        {'Charges': '000807:' + ME, 'ChargedSound': '000811:' + ME, 'PlayerRef': '000014:Skyrim.esm',
         'TierAbility': '000809:' + ME, 'TimeScale': '00003A:Skyrim.esm'}, '', True))
    eruption_props = {'Blast': '00080B:' + ME, 'Charges': '000807:' + ME, 'PlayerRef': '000014:Skyrim.esm',
                      'Shockwave': '00080A:' + ME, 'Volcano': '00080E:' + ME, 'Vent': '000816:' + ME,
                      'LavaLoop': '00081A:' + ME, 'LavaBomb': '000810:' + ME, 'GroundMarker': '000034:Skyrim.esm'}
    rec('MagicEffects', 'ZP_CalderaEruptionEffect', '000806', script_effect(
        '000806', 'ZP_CalderaEruptionEffect', 'Eruption', 'ZP_CalderaEruptionScript', eruption_props, TEXT, False))
    rec('Globals', 'ZP_CalderaCharges', '000807', '\n'.join([
        'MutagenObjectType: GlobalShort', 'FormKey: 000807:' + ME, 'EditorID: ZP_CalderaCharges', 'Data: 0']))
    rec('MagicEffects', 'ZP_CalderaTiersMGEF', '000808', '\n'.join([
        'FormKey: 000808:' + ME, 'EditorID: ZP_CalderaTiersMGEF', 'VirtualMachineAdapter:', '  Scripts:',
        '  - Name: ZP_CalderaTiersScript', '    Properties:',
        '    - MutagenObjectType: ScriptObjectProperty', '      Name: Charges', '      Object: 000807:' + ME,
        '    - MutagenObjectType: ScriptObjectProperty', '      Name: Eruption', '      Object: 00081B:' + ME,
        '    - MutagenObjectType: ScriptObjectProperty', '      Name: Hammer', '      Object: 000800:' + ME,
        '    - MutagenObjectType: ScriptObjectProperty', '      Name: PlayerRef', '      Object: 000014:Skyrim.esm',
        'Name:', '  TargetLanguage: English',
        '  Value: Caldera Charge', 'Flags:', '- NoDuration', '- NoMagnitude', '- NoArea', '- HideInUI', '- Painless',
        'Archetype:', '  MutagenObjectType: MagicEffectArchetype', '  Type: Script', 'DualCastScale: 1', 'Sounds: []',
        'Description:', '  TargetLanguage: English', "  Value: ''"]))
    rec('Spells', 'ZP_CalderaTiers', '000809', '\n'.join([
        'FormKey: 000809:' + ME, 'EditorID: ZP_CalderaTiers', 'Name:', '  TargetLanguage: English',
        '  Value: Caldera Charge', 'EquipmentType: 013F44:Skyrim.esm', 'Description:', '  TargetLanguage: English',
        "  Value: ''", 'Flags:', '- ManualCostCalc', '- IgnoreResistance', '- NoAbsorbOrReflect', 'Type: Ability',
        'Effects:', '- BaseEffect: 000808:' + ME, '  Data: {}']))

    # 80A the shockwave: Fire Storm's explosion on our scaled ring
    x = one(os.path.join(EMBERS, 'Explosions'), '08196B_Skyrim.esm')
    x = sub1(x, r'^FormKey: .*$', 'FormKey: 00080A:' + ME)
    x = sub1(x, r'^EditorID: .*$', 'EditorID: ZP_CalderaShockwave')
    x = sub1(x, r'^Model:\n  File: .*\n  Data: .*\n', lambda m: 'Model:\n  File: %s\n' % SHOCK_MODEL)
    x = drop(x, r'^Force: .*\n')
    x = drop(x, r'^Damage: .*\n')
    x = drop(x, r'^ISRadius: .*\n')
    x = sub1(x, r'^Radius: .*$', 'Radius: %d' % SHOCK_RADIUS)
    x = drop(x, r'^Version2: .*\n')
    assert 'ImageSpaceModifier' not in x
    rec('Explosions', 'ZP_CalderaShockwave', '00080A', x)

    # 80B-80D the blast
    d = one(os.path.join(CLEANUP, [n for n in os.listdir(CLEANUP) if n.endswith('ESP')][0], 'MagicEffects'),
            '0834B5_' + APOC_ESP)
    d = sub1(d, r'^FormKey: .*$', 'FormKey: 00080C:' + ME)
    d = sub1(d, r'^EditorID: .*$', 'EditorID: ZP_CalderaBlastDamage')
    d = drop(d, r'^VirtualMachineAdapter:\n(?:  .*\n)+')
    d = english(d, 'Name', 'Eruption')
    d = drop(d, r'^Projectile: .*\n')
    d = sub1(d, r'^TargetType: Aimed$', 'TargetType: Touch')
    assert 'GetIsIDConditionData' in d and 'Object: 000007:Skyrim.esm' in d            # never the player
    rec('MagicEffects', 'ZP_CalderaBlastDamage', '00080C', d)
    g = one(os.path.join(APOC, 'MagicEffects'), '0834BA_' + APOC_ESP)
    g = sub1(g, r'^FormKey: .*$', 'FormKey: 00080D:' + ME)
    g = sub1(g, r'^EditorID: .*$', 'EditorID: ZP_CalderaBlastStagger')
    g = english(g, 'Name', 'Eruption Stagger')
    g = drop(g, r'^Projectile: .*\n')
    g = sub1(g, r'^TargetType: Aimed$', 'TargetType: Touch')
    rec('MagicEffects', 'ZP_CalderaBlastStagger', '00080D', g)
    rec('Spells', 'ZP_CalderaBlast', '00080B', '\n'.join([
        'FormKey: 00080B:' + ME, 'EditorID: ZP_CalderaBlast', 'Name:', '  TargetLanguage: English',
        '  Value: Eruption', 'EquipmentType: 013F44:Skyrim.esm', 'Description:', '  TargetLanguage: English',
        "  Value: ''", 'Flags:', '- ManualCostCalc', '- NoAbsorbOrReflect', 'CastType: FireAndForget',
        'TargetType: Touch', 'Effects:', '- BaseEffect: 00080C:' + ME, '  Data:', '    Magnitude: %g' % at_record(BLAST),
        '- BaseEffect: 00080D:' + ME, '  Data:', '    Magnitude: %g' % BLAST_STAGGER]))

    # 80E-810 the volcano: Apocalypse's, ours to tune
    v = one(os.path.join(APOC, 'Explosions'), '0834AE_' + APOC_ESP)
    v = sub1(v, r'^FormKey: .*$', 'FormKey: 00080E:' + ME)
    v = sub1(v, r'^EditorID: .*$', 'EditorID: ZP_CalderaVolcano')
    v = sub1(v, r'^PlacedObject: .*$', 'PlacedObject: 00080F:' + ME)
    v = drop(v, r'^ImageSpaceModifier: .*\n')
    v = drop(v, r'^ISRadius: .*\n')
    v = sub1(v, r'^Sound1: .*$', 'Sound1: 000814:' + ME)              # the curator's volcano eruption
    rec('Explosions', 'ZP_CalderaVolcano', '00080E', v)
    c = one(os.path.join(APOC, 'Activators'), '0834AD_' + APOC_ESP)
    c = sub1(c, r'^FormKey: .*$', 'FormKey: 00080F:' + ME)
    c = sub1(c, r'^EditorID: .*$', 'EditorID: ZP_CalderaVolcanoController')
    c = sub1(c, r'^(      Name: WB_Duration\n      Data: )[\d.]+$', r'\g<1>%d' % ERUPT)
    c = sub1(c, r'^(      Name: WB_FireballRadius\n      Data: )[\d.]+$', r'\g<1>%d' % ERUPT_RADIUS)
    c = sub1(c, r'^(      Name: WB_S_D100_VolcanoNew_Spell_PC\n      Object: ).*$', r'\g<1>000810:' + ME)
    rec('Activators', 'ZP_CalderaVolcanoController', '00080F', c)
    b = one(os.path.join(APOC, 'Spells'), '0834B3_' + APOC_ESP)
    b = sub1(b, r'^FormKey: .*$', 'FormKey: 000810:' + ME)
    b = sub1(b, r'^EditorID: .*$', 'EditorID: ZP_CalderaLavaBomb')
    b = english(b, 'Name', 'Lava Bomb')
    b = sub1(b, r'^(- BaseEffect: 0834B5:.*\n  Data:\n    Magnitude: )40$', r'\g<1>%g' % at_record(BOMB))
    b = drop(b, r'^- BaseEffect: 0F392D:Skyrim\.esm\n  Data:\n(?:    .*\n)+')
    b = sub1(b, r'^(- BaseEffect: 0834BA:.*\n  Data:\n    Magnitude: )[\d.]+$', r'\g<1>%g' % BOMB_STAGGER)
    rec('Spells', 'ZP_CalderaLavaBomb', '000810', b)

    # 811 the full charge: the curator's metal whoosh (815)
    rec('SoundMarkers', 'ZP_CalderaChargedSound', '000811', '\n'.join([
        'FormKey: 000811:' + ME, 'EditorID: ZP_CalderaChargedSound', 'FormVersion: 43',
        'SoundDescriptor: 000815:' + ME]))
    # 813-815 the curator's three sounds (812, the cracked field, retired)
    for fid, eid, path, model, loop in (('000813', 'ZP_CalderaLavaLoopSD', LAVA_FILE, '10E425:Skyrim.esm', True),
                                        ('000814', 'ZP_CalderaEruptionSD', ERUPTION_FILE, '0F1B1A:Skyrim.esm', False),
                                        ('000815', 'ZP_CalderaChargedSD', CHARGED_FILE, '0F1B1A:Skyrim.esm', False)):
        rec('SoundDescriptors', eid, fid, '\n'.join([
            'FormKey: %s:%s' % (fid, ME), 'EditorID: ' + eid, 'Type: Standard', 'Category: 0172A1:Skyrim.esm',
            'SoundFiles:', '- ' + path, 'OutputModel: ' + model] +
            (['LoopAndRumble:', '  Loop: Loop'] if loop else ['LoopAndRumble: {}']) + ['Priority: 128']))

    # 816-819 the small volcanoes: Apocalypse's volcano again, smaller and for show
    scale = float(re.search(r'^VENT_SCALE = ([\d.]+)', read(os.path.join(HERE, '01-build-mesh.py')), re.M).group(1))
    c = one(os.path.join(APOC, 'Activators'), '0834AD_' + APOC_ESP)
    c = sub1(c, r'^FormKey: .*$', 'FormKey: 000816:' + ME)
    c = sub1(c, r'^EditorID: .*$', 'EditorID: ZP_CalderaVentController')
    c = sub1(c, r'^(      Name: WB_DestructionFire_Activator_VolcanoNew_Fountain\n      Object: ).*$', r'\g<1>000817:' + ME)
    c = sub1(c, r'^(      Name: WB_DestructionFire_Light_Volcano_Fountain\n      Object: ).*$', r'\g<1>000818:' + ME)
    c = sub1(c, r'^(      Name: WB_Duration\n      Data: )[\d.]+$', r'\g<1>%d' % VENT_ERUPT)
    c = sub1(c, r'^(      Name: WB_EndLocZ\n      Data: )[\d.]+$', r'\g<1>%d' % VENT_HEIGHT)
    c = sub1(c, r'^(      Name: WB_FireballRadius\n      Data: )[\d.]+$', r'\g<1>%d' % VENT_RADIUS)
    c = sub1(c, r'^(      Name: WB_S_D100_VolcanoNew_Spell_PC\n      Object: ).*$', r'\g<1>000819:' + ME)
    c = sub1(c, r'^(      Name: WB_TotalHeight\n      Data: )28$', r'\g<1>%g' % round(28 * scale, 2))
    c = sub1(c, r'^(      Name: WB_UpdateRate\n      Data: )[\d.]+$', r'\g<1>%g' % VENT_RATE)
    c = drop(c, r'^LoopingSound: .*\n')
    rec('Activators', 'ZP_CalderaVentController', '000816', c)
    f = one(os.path.join(APOC, 'Activators'), '0834B2_' + APOC_ESP)
    m = re.search(r'^ObjectBounds:\n  First: (-?\d+), (-?\d+), (-?\d+)\n  Second: (-?\d+), (-?\d+), (-?\d+)\n', f, re.M)
    lo = [int(math.floor(int(v) * scale)) for v in m.groups()[:3]]
    hi = [int(math.ceil(int(v) * scale)) for v in m.groups()[3:]]
    f = sub1(f, r'^FormKey: .*$', 'FormKey: 000817:' + ME)
    f = sub1(f, r'^EditorID: .*$', 'EditorID: ZP_CalderaVentFountain')
    f = sub1(f, r'^ObjectBounds:\n  First: .*\n  Second: .*\n', 'ObjectBounds:\n  First: %d, %d, %d\n  Second: %d, %d, %d\n'
             % (*lo, *hi))
    f = sub1(f, r'^Model:\n  File: .*\n  Data: .*\n', lambda _: 'Model:\n  File: %s\n' % VENT_MODEL)
    f = drop(f, r'^LoopingSound: .*\n')
    rec('Activators', 'ZP_CalderaVentFountain', '000817', f)
    li = one(os.path.join(APOC, 'Lights'), '0834B8_' + APOC_ESP)
    li = sub1(li, r'^FormKey: .*$', 'FormKey: 000818:' + ME)
    li = sub1(li, r'^EditorID: .*$', 'EditorID: ZP_CalderaVentLight')
    li = sub1(li, r'^Radius: 384$', 'Radius: %d' % VENT_LIGHT)
    rec('Lights', 'ZP_CalderaVentLight', '000818', li)
    b = one(os.path.join(APOC, 'Spells'), '0834B3_' + APOC_ESP)
    b = sub1(b, r'^FormKey: .*$', 'FormKey: 000819:' + ME)
    b = sub1(b, r'^EditorID: .*$', 'EditorID: ZP_CalderaVentBomb')
    b = english(b, 'Name', 'Lava Bomb')
    b = sub1(b, r'^(- BaseEffect: 0834B5:.*\n  Data:\n    Magnitude: )40$', r'\g<1>%g' % VENT_BOMB)
    b = drop(b, r'^- BaseEffect: 0F392D:Skyrim\.esm\n  Data:\n(?:    .*\n)+')
    b = drop(b, r'^- BaseEffect: 0834BA:.*\n  Data:\n(?:    .*\n)+')
    assert b.count('- BaseEffect:') == 1
    rec('Spells', 'ZP_CalderaVentBomb', '000819', b)
    # 81A the lava river at the eruption
    rec('SoundMarkers', 'ZP_CalderaLavaLoopSound', '00081A', '\n'.join([
        'FormKey: 00081A:' + ME, 'EditorID: ZP_CalderaLavaLoopSound', 'FormVersion: 43',
        'SoundDescriptor: 000813:' + ME]))
    # 81B/81C the eruption on the swing: a self spell the cracks' ability casts, the same script as 806
    rec('MagicEffects', 'ZP_CalderaEruptionSwingEffect', '00081C', script_effect(
        '00081C', 'ZP_CalderaEruptionSwingEffect', 'Eruption', 'ZP_CalderaEruptionScript', eruption_props, '', True,
        target='Self'))
    sp = one(os.path.join(ROOT, 'src', 'Prophecy', 'ProphecyESP', 'Spells'), '000B76_Zenderal - Prophecy.esp')
    assert 'TargetType: Self' in sp and 'CastType: FireAndForget' in sp and sp.count('- BaseEffect:') == 1
    sp = sub1(sp, r'^FormKey: .*$', 'FormKey: 00081B:' + ME)
    sp = sub1(sp, r'^EditorID: .*$', 'EditorID: ZP_CalderaEruptionSwing')
    sp = english(sp, 'Name', 'Eruption')
    sp = drop(sp, r'^MenuDisplayObject: .*\n')
    sp = drop(sp, r'^TargetType: Self\n')                 # Self is 0, the default: Spriggit omits it
    sp = sub1(sp, r'^Effects:\n(?:- .*\n?|  .*\n?)+', 'Effects:\n- BaseEffect: 00081C:%s\n  Data: {}\n' % ME)
    assert sp.endswith('Effects:\n- BaseEffect: 00081C:%s\n  Data: {}\n' % ME) and 'Duration' not in sp, sp
    rec('Spells', 'ZP_CalderaEruptionSwing', '00081B', sp)
    print('small volcanoes: fountain x%g, bounds %s..%s, %d s, a bomb every %g s within %d (%d fire)' % (
        scale, lo, hi, VENT_ERUPT, VENT_RATE, VENT_RADIUS, VENT_BOMB))
    print('records written to', OUT)


if __name__ == '__main__':
    main()
