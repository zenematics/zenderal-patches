"""Whisper's records (curator 2026-11-15: "build the weapon so I can see in game"). A test build: the weapon and its
first-person static only, so the mesh can be held and looked at in game; the charge (souls from Entropy absorb
spells) and the power-attack release come later, as Argent Verdict's did.

  800 WEAP ZP_Whisper          <- EGO's Aeterna War Axe 07C992 (EGO wins it; 26 damage, speed 0.9, unenchanted):
                                  DAMAGE / CRIT / VALUE below (provisional, between EGO's forged Aeterna War Axe 28
                                  and Uunil'Yar's Promise 35), keywords: war axe, Aeterna material (EGO's smithing
                                  perks), melee, unique, no enchanting (its own effect comes later), no vendor; on
                                  tools/02's Whisper.nif, bounds measured from its visible shapes
  801 STAT 1stPersonZP_Whisper <- 1stPersonElvenWarAxe 036BCC (vanilla wins it) on the same mesh

The souls (curator 2026-11-15, once the look was final: "lets make it entropy spells in general" (after an absorb-only
build), "5 souls, eyes then crystal", Soul Cleave on a full charge ("can we have a horizonal purple slash the fires
out in a conal wave infront of us dealing magic damage?"; Soul Rend, then Reaping Souls' orbs before it), "Soul trap on
kill"; "remove the enchantment visual effect coating the weapon in purple"):
  802 ENCH ZP_WhisperEnch           weapon enchantment, on every hit: Soul Trap 80B for SOUL_TRAP s (Enderal's soul trap
                                    script fills a soul gem if the target dies); and Soul Cleave 805 on a power attack
                                    that hits an actor hostile to the player while 803 is SOULS (the card's text and a
                                    fallback: the release comes on the swing, below)
  80B MGEF ZP_WhisperSoulTrapMGEF   vanilla EnchSoulTrapFFContact 05B452 verbatim (its script and properties, its shimmer
                                    on the target) without its enchant shader 05D607, which coated the axe in purple
  803 GLOB ZP_WhisperSouls          0..SOULS (GlobalVariable.Mod: thread-safe)
  804 MGEF ZP_WhisperSoulsMGEF      a constant script effect, hidden: ZP_WhisperSoulsScript (Entropy spells landing on
                                    enemies add a soul; the axe's glow follows the souls)
  806 SPEL ZP_WhisperSoulsAbility   the ability carrying 804, given while the axe is in hand (ZP_WhisperEquipScript);
                                    and 80D while 803 is SOULS
  80C LIGH ZP_WhisperChargedLight   Candlelight's light MagicLightLightSpell01 03FA58 in purple, CHARGED_RADIUS
  80D MGEF ZP_WhisperChargedLightMGEF  a constant Light effect (vanilla LightFFSelfConstant 146677's shape, no orb, no
                                    sounds, hidden) on 80C: the charged axe lights its wielder (curator: "it's not obvious
                                    if the weapon is charged"); with the halo in tools/02's mesh
  807, 808 retired (2026-11-15: the axe's own drain, added to every Entropy spell, before the curator's correction);
                                    never reuse
  805 MGEF ZP_WhisperCleaveEffect   "Soul Cleave", the release: an instant script effect on the struck enemy running
                                    ZP_WhisperCleaveScript (the wave, straight out ahead and level), on the item card
                                    (Soul Rend's, then Reaping Souls', 2026-11-15)
  809 MGEF ZP_WhisperCleaveMGEF     the wave's blow: Health damage (magic: ResistMagic), Aimed on 811, fixed, hidden,
                                    hostile actors only, the soul trap shimmer on the target; Destruction, so it never
                                    feeds the axe
  80A SPEL ZP_WhisperCleave         809 at CLEAVE_DAMAGE, Aimed: the release script RemoteCasts it (and applies it
                                    directly to a struck enemy inside where the wave begins)
  810 LIGH ZP_WhisperWaveLight      Candlelight's light 03FA58 in purple, WAVE_LIGHT_RADIUS: it lights the ground the
                                    wave crosses
  811 PROJ ZP_WhisperWaveProj       Fire Breath's wave VoiceFireWaveProjectile01 0647BF (a Cone projectile: it passes
                                    through and hits every actor in its cone) on tools/05's WhisperWave.nif (a horizontal
                                    purple crescent), light 810, sound 812, WAVE_SPEED / WAVE_RANGE / WAVE_SPREAD
  812 SNDR ZP_WhisperWaveSD         its flight: A Dark Warrior's Tale's slash (Kittytail's
                                    DarkWarriorSlashProj.wav, from the pack's archive; her permission covers patching
                                    her mods for Zenderal), vanilla category and positional output
(809-811 were Reaping Souls' orb records before; Soul Rend's before that.)
The release on the swing (curator 2026-11-15: "make the the power attack not require a hit to trigger the wave"):
ZP_WhisperSoulsScript (804) hears the player's weapon swings and releases Soul Cleave on a power-attack swing of
Whisper's while full; 805 on the enchantment stays as the item card's text and as a fallback for a power attack whose
swing the game never reported (by then the souls are spent, so normally its conditions fail).
The soul wisp (curator: "if the wave kills an enemy, let it spawn a purple wisp", "Fights for you", "the wisp lasts for
30 seconds, only 1 wisp at a time"); Midnight Sting's spiderling pattern, Enderal's Wisp in purple:
  813 MGEF ZP_WhisperWispMark       on the wave (80A, its first effect): a hidden 1 s script effect that survives death,
                                    ZP_WhisperWispMarkEffect: an enemy dead when it ends raises the wisp
  814 FLST ZP_WhisperWisps          the wisp out (one at a time: the scripts fade an older one)
  815 NPC_ ZP_WhisperWisp           "Soul Wisp" <- Enderal's Wisp _20E_IrrlichtGrouped 0D0D69 (EGO's record): its scripts
                                    (EP, ghost, combat music), items, EGO's perk, respawn and template flags dropped;
                                    the player's level, PlayerFaction, follows the player (SureAI's _DefaultFollowPlayer),
                                    aggressive, Enderal's summoned-creature keyword, our race and ability
  816 SPEL ZP_WhisperWispAbility    its ability: 817
  817 MGEF ZP_WhisperWispEffect     ZP_WhisperWispEffect: the purple glow, WISP_LIFE s, the hunt, one at a time
  818 RACE ZP_WhisperWispRace       WitchlightRace 013209 (EGO's record) without AbWitchlight 08CDD1 (the blue glow
                                    FXWitchlightAttachSCRIPT plays; and water walking) and EGO's own keyword; skin 819
  819 ARMO ZP_WhisperWispSkin       SkinWitchlight 086F42 for 818, armature 81A
  81A ARMA ZP_WhisperWispSkinAA     NakedWitchlight 086F41 for 818 (the same mesh)
  81B RFCT ZP_WhisperWispFX         FXWitchlightMeshEffect 08CDCF on 81C
  81C ARTO ZP_WhisperWispFXArt      FXWitchlightMeshObject 08CDCE on tools/06's purple WhisperWisp.nif
The wisp's attack is its race's (Wisp's Kiss, 091F78, on its unarmed strike).
The wisp's whisper and burst, the poof, the aim (curator 2026-11-15: "add this whisper sound effect looped for when the
Wisp is active"; "If you hit the Wisp with an Entropy spell it explodes reducing enemies magic resistance by 15% and
gives 30 mana to the player"; the poof "on trigger"; "fire where the player is aiming"):
  81D MGEF ZP_WhisperWispRuptureMGEF  "Soul Rupture": magic resistance -RUPTURE (Detrimental, Recover) for RUPTURE_SECONDS,
                                    Alteration (never an Entropy hit), hostile actors only, the soul trap shimmer
  81E SPEL ZP_WhisperWispRupture    81D, TargetActor: the wisp's script RemoteCasts it from the player onto every enemy
                                    within WISP_BURST_RADIUS when the player's Entropy spell strikes the wisp (and gives
                                    the player WISP_MANA Magicka)
  81F EXPL ZP_WhisperWispBurst      the Wisp's death explosion wispDeathExplosion 0F1189 on tools/06's purple copy of its
                                    mesh, without its enchantment and screen flash: a harmless purple flash
  820 SNDR / 821 SOUN ZP_WhisperWispLoop   the curator's MA_MotionAudio_GhostWhispering_03.wav (tools/04: mono, made
                                    seamless), looping, positional within 1800 (SOMMono01800_verb): the wisp's script
                                    plays it while the wisp is out
  822 SNDR / 823 SOUN ZP_WhisperPoof       the curator's 02. Cartoon Poof SFX.wav (tools/04, stereo kept; output
                                    SOMStereoRad03000_verb, the wave's): Soul Cleave's release plays it on the player
The aim is the script's (ZP_WhisperCleaveScript.Release: the camera, ZP_Aim.CameraAim in ZenProphecyRage.dll 1.10.0).
  80E SNDR ZP_WhisperChargedSD      the fully charged sound (curator 2026-11-15: "add this sound when its fully charged":
                                    their licensed MA_MotionAudio_SpookyBreath_02.wav, installed by tools/04, not
                                    committed), Argent Verdict's charged bell's record shape (vanilla category and output)
  80F SOUN ZP_WhisperChargedSound   plays 80E: the souls script rings it on the fifth soul
Visuals are vanilla (Enderal keeps them): the soul trap streams SoulTrapPVFX01/02 0531AF/0531B1, its shimmer
SoulTrapTargetActFXS 054223; the release rings the soul trap's capture sound MAGMysticismSoulTrapCapture 056AC6. The
glow and the halo are in tools/02's mesh.

Usage:  python src/Whisper/tools/03-build-records.py      (then deserialize: see arch-docs/patches/Whisper.md)
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
OUT = os.path.join(ROOT, 'src', 'Whisper', 'WhisperESP')
BASE = os.path.join(ROOT, 'reference', 'base')
EGO = os.path.join(ROOT, 'reference', 'mods', 'EGO - Enderal Gameplay Overhaul')
EGO_ESP = 'Enderal SE - Gameplay Overhaul.esp'
ME = 'Zenderal - Whisper.esp'

NAME = 'Whisper'
MODEL = chr(92).join(('Zenderal', 'Whisper', 'Whisper.nif'))
DAMAGE, CRIT, VALUE = 30, 21, 1200
KEYWORDS = ['01E712:Skyrim.esm',   # WeapTypeWarAxe
            '01E71B:Skyrim.esm',   # WeapMaterialElven: Aeterna (EGO's smithing perks), as Argent Verdict
            '06727B:Skyrim.esm',   # WeapTypeMelee
            '0C27BD:Skyrim.esm',   # MagicDisallowEnchanting
            '14CE9A:Skyrim.esm']   # WeapTypeUnique
EXPECTED_WINNERS = {'07C992:Skyrim.esm': EGO_ESP,      # the war axe
                    '036BCC:Skyrim.esm': 'Skyrim.esm',  # its first-person static
                    '05B452:Skyrim.esm': 'Skyrim.esm',  # Soul Trap (the enchantment's)
                    '0D0D69:Skyrim.esm': EGO_ESP,       # Enderal's Wisp (the soul wisp's)
                    '013209:Skyrim.esm': EGO_ESP,       # WitchlightRace
                    '086F42:Skyrim.esm': 'Skyrim.esm',  # SkinWitchlight
                    '086F41:Skyrim.esm': 'Skyrim.esm',  # NakedWitchlight
                    '08CDCF:Skyrim.esm': 'Skyrim.esm',  # FXWitchlightMeshEffect
                    '08CDCE:Skyrim.esm': 'Skyrim.esm'}  # FXWitchlightMeshObject
SCRIPTS = os.path.join(ROOT, 'src', 'Whisper', 'Scripts', 'source')
CHARGE = 3000             # the enchantment's charge: ~3000 hits before a recharge (Argent Verdict's)
SOULS = 5                 # a full charge (the scripts' Full, checked)
SOUL_GAP = 0.75           # seconds between two souls at least (the souls script's Gap, checked)
SOUL_TRAP = 5             # seconds: a target that dies within them fills a soul gem
CLEAVE_DAMAGE = 80        # each actor the wave passes through (magic damage)
WAVE_SPEED = 1500         # Fire Breath's 1200
WAVE_RANGE = 1000         # Fire Breath's 1200
WAVE_SPREAD = 12          # Fire Breath's 8: a wider cone
WAVE_COLLISION = 64       # Fire Breath's 16; Kittytail's Shadow Carve's 64
WAVE_LIGHT_RADIUS = 400
WAVE_LIGHT_COLOUR = '#00B450FF'
WAVE_MODEL = chr(92).join(('Zenderal', 'Whisper', 'WhisperWave.nif'))   # tools/05's
WAVE_SOUND = chr(92).join(('data', 'sound', 'fx', 'KittyClass_DarkWarrior', 'DarkWarriorSlashProj.wav'))
CHARGED_RADIUS = 320      # the charged light's reach (Candlelight's 450)
CHARGED_FILE = chr(92).join(('data', 'sound', 'fx', 'Zenderal', 'Whisper', 'WhisperCharged.wav'))   # tools/04's output
CHARGED_COLOUR = '#00B450FF'   # purple (Mutagen's #AARRGGBB; Candlelight's #0081AFE2)
STREAM, GATHER = '0531AF:Skyrim.esm', '0531B1:Skyrim.esm'    # SoulTrapPVFX01 / 02
SHIMMER, CAPTURE = '054223:Skyrim.esm', '056AC6:Skyrim.esm'  # SoulTrapTargetActFXS, MAGMysticismSoulTrapCapture
WISP_LIFE = 30            # seconds (curator); ZP_WhisperWispEffect's LifeSeconds (checked)
WISP_MODEL = chr(92).join(('Zenderal', 'Whisper', 'WhisperWisp.nif'))   # tools/06's
WISP_BURST_MODEL = chr(92).join(('Zenderal', 'Whisper', 'WhisperWispBurst.nif'))   # tools/06's
WISP_MANA = 30            # Magicka back to the player when an Entropy spell bursts the wisp (curator)
WISP_BURST_RADIUS = 400   # the burst reaches enemies this far from the wisp
RUPTURE = 15              # the burst: magic resistance -15 (curator: "reducing enemies magic resistance by 15%")
RUPTURE_SECONDS = 15      # for this long (not stated by the curator)
WISP_LOOP_FILE = chr(92).join(('data', 'sound', 'fx', 'Zenderal', 'Whisper', 'WhisperWispLoop.wav'))   # tools/04's
POOF_FILE = chr(92).join(('data', 'sound', 'fx', 'Zenderal', 'Whisper', 'WhisperPoof.wav'))            # tools/04's
CLEAVE_TEXT = ('While Whisper is in hand, each Entropy spell that strikes an enemy pulls its soul into the axe, and its '
               'eyes glow brighter with each. With %d souls the crystal blazes, and the next power attack releases them '
               'as a wave of purple light that cleaves through every enemy before you for %d magic damage. An enemy the '
               'wave kills rises as a Soul Wisp that fights at your side for %d seconds, one at a time; strike it with '
               'an Entropy spell and it bursts, lowering the magic resistance of nearby enemies by %d%% and restoring '
               '%d Magicka.' % (SOULS, CLEAVE_DAMAGE, WISP_LIFE, RUPTURE, WISP_MANA))


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
    out, n = re.subn(r'^%s:\n  TargetLanguage: English\n  Value: .*\n' % field,
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


def mesh_bounds():
    """tools/02's mesh as the load order sees it (it must win its path): the bounds of its visible shapes (the
    vertices their triangles use; the hidden hip holder left out)."""
    sr = _module('sr_assets', os.path.join(ROOT, 'src', 'StingAndRise', 'tools', '01-build-assets.py'))
    mods = os.path.join(sr.MO2, 'mods')
    src, nif = sr.load(mods, sr.profile_mods(), 'meshes/' + MODEL.replace(chr(92), '/'))
    if src != 'Zenderal - Patch Collection':
        sys.exit('%s comes from %s, not Zenderal - Patch Collection: run tools/02 first' % (MODEL, src))
    names, pts = [], []
    for k in sr.nifse.node_children(nif.blocks[nif.roots[0]])[1]:
        if nif.btype(k) != 'BSTriShape':
            continue
        s = sr.nifse.read_trishape(nif.blocks[k])
        names.append(sr.name_of(nif, k))
        if struct.unpack_from('<I', nif.blocks[k], s['av']['flags'])[0] & 1:          # hidden
            continue
        t, R, sc = sr.nifse.transform(nif.blocks[k])
        pts.append(s['pos'][np.unique(s['tris'])] * sc @ R.T + t)
    assert {'ZP_WhisperSnake', 'ZP_WhisperOuroboros', 'ZP_WhisperPommel'} <= set(names), ('not tools/02\'s mesh', names)
    P = np.concatenate(pts)
    lo = [int(math.floor(v)) for v in P.min(0)]
    hi = [int(math.ceil(v)) for v in P.max(0)]
    return 'ObjectBounds:\n  First: %d, %d, %d\n  Second: %d, %d, %d\n' % (*lo, *hi)


def script_number(script, name):
    m = re.search(r'^(?:Int|Float) Property %s = ([\d.]+) AutoReadOnly' % name,
                  read(os.path.join(SCRIPTS, script + '.psc')), re.M)
    if not m:
        sys.exit('%s: no %s' % (script, name))
    return float(m.group(1))


def check_scripts():
    """The numbers the item card and the records state, as the scripts have them."""
    for script, name, want in (('ZP_WhisperSoulsScript', 'Full', SOULS), ('ZP_WhisperCleaveScript', 'Full', SOULS),
                               ('ZP_WhisperSoulsScript', 'Gap', SOUL_GAP), ('ZP_WhisperWispEffect', 'LifeSeconds', WISP_LIFE),
                               ('ZP_WhisperWispEffect', 'ManaGain', WISP_MANA),
                               ('ZP_WhisperWispEffect', 'BurstRadius', WISP_BURST_RADIUS)):
        got = script_number(script, name)
        if abs(got - want) > 1e-9:
            sys.exit('%s: %s is %g, the records say %g' % (script, name, got, want))


def props(*pairs):
    lines = ['VirtualMachineAdapter:', '  Scripts:']
    for script, plist in pairs:
        lines += ['  - Name: ' + script, '    Properties:']
        for name, obj in sorted(plist):
            lines += ['    - MutagenObjectType: ScriptObjectProperty', '      Name: ' + name, '      Object: ' + obj]
    return '\n'.join(lines)


HOSTILE = ['  - MutagenObjectType: ConditionFloat', '    Data:', '      MutagenObjectType: IsHostileToActorConditionData',
           '      TargetNpc: 000014:Skyrim.esm', '    ComparisonValue: 1']


def me(fid):
    return '%s:%s' % (fid, ME)


def value_mgef(fid, editor_id, name, absorb):
    """A fixed Health effect on a Touch spell the scripts apply: hidden, hostile actors only, no visuals of its own;
    Destruction (never an Entropy hit itself)."""
    return '\n'.join([
        'FormKey: ' + me(fid), 'EditorID: ' + editor_id,
        'Name:', '  TargetLanguage: English', '  Value: ' + name,
        'Flags:', '- Hostile', '- Detrimental', '- NoArea', '- HideInUI', '- NoRecast', '- NoDeathDispel',
        'BaseCost: 1', 'MagicSkill: Destruction', 'ResistValue: ResistMagic',
        'Archetype:', '  MutagenObjectType: MagicEffectArchetype', '  ActorValue: Health'] +
        (['  Type: Absorb'] if absorb else []) + [
        'CastType: FireAndForget', 'TargetType: Touch', 'SkillUsageMultiplier: 1', 'DualCastScale: 1',
        'Sounds: []',
        'Description:', '  TargetLanguage: English', "  Value: ''",
        'Conditions:'] + [line[2:] for line in HOSTILE])


def touch_spell(fid, editor_id, name, effect, magnitude):
    return '\n'.join([
        'FormKey: ' + me(fid), 'EditorID: ' + editor_id,
        'Name:', '  TargetLanguage: English', '  Value: ' + name,
        'EquipmentType: 013F44:Skyrim.esm',
        'Description:', '  TargetLanguage: English', "  Value: ''",
        'Flags:', '- ManualCostCalc', '- NoAbsorbOrReflect',
        'CastType: FireAndForget', 'TargetType: Touch', 'Effects:',
        '- BaseEffect: ' + me(effect), '  Data:', '    Magnitude: %d' % magnitude])


def souls_records():
    """802-812: the souls, Soul Cleave, the soul trap, the charged light and sound (see the docstring)."""
    vfx = [('StreamVFX', STREAM), ('GatherVFX', GATHER), ('SoulFXS', SHIMMER), ('PlayerRef', '000014:Skyrim.esm')]
    # 80B Soul Trap: vanilla 05B452 verbatim minus its enchant shader (the purple coat on the axe)
    st = one(os.path.join(BASE, 'Skyrim', 'MagicEffects'), '05B452_Skyrim.esm')
    assert 'EnchantShader: 05D607:Skyrim.esm' in st and 'Name: magicsoultrapfxscript' in st
    st = sub1(st, r'^FormKey: .*$', 'FormKey: ' + me('00080B'))
    st = sub1(st, r'^EditorID: .*$', 'EditorID: ZP_WhisperSoulTrapMGEF')
    st = sub1(st, r'^EnchantShader: .*\n', '')
    for field, value in (('Name', 'Soul Trap'), ('Description', 'If target dies within <dur> seconds, it fills a soul gem')):
        st = sub1(st, r'^%s:\n  TargetLanguage: English\n  Values:\n(?:  .*\n)+' % field,      # not localized: English
                  '%s:\n  TargetLanguage: English\n  Value: %s\n' % (field, value))
    rec('MagicEffects', 'ZP_WhisperSoulTrapMGEF', '00080B', st)
    # 802 the enchantment: Soul Trap on every hit; Soul Cleave on a power attack that hits a hostile actor, full
    rec('ObjectEffects', 'ZP_WhisperEnch', '000802', '\n'.join([
        'FormKey: ' + me('000802'), 'EditorID: ZP_WhisperEnch',
        'Name:', '  TargetLanguage: English', '  Value: ' + NAME,
        'EnchantmentCost: 1', 'Flags:', '- NoAutoCalc', 'CastType: FireAndForget',
        'EnchantmentAmount: %d' % CHARGE, 'TargetType: Touch', 'EnchantType: Enchantment',
        'Effects:',
        '- BaseEffect: ' + me('00080B'),                                # Soul Trap: its own conditions
        '  Data:', '    Duration: %d' % SOUL_TRAP,
        '- BaseEffect: ' + me('000805'),                                # Soul Cleave
        '  Data: {}', '  Conditions:'] + HOSTILE + [
        '  - MutagenObjectType: ConditionFloat', '    Data:',
        '      MutagenObjectType: IsPowerAttackingConditionData', '      RunOnType: Reference',
        '      Reference: 000014:Skyrim.esm', '    ComparisonValue: 1',
        '  - MutagenObjectType: ConditionFloat', '    CompareOperator: GreaterThanOrEqualTo', '    Data:',
        '      MutagenObjectType: GetGlobalValueConditionData', '      Global: ' + me('000803'),
        '    ComparisonValue: %d' % SOULS]))
    # 803 the souls
    rec('Globals', 'ZP_WhisperSouls', '000803', '\n'.join([
        'MutagenObjectType: GlobalShort', 'FormKey: ' + me('000803'), 'EditorID: ZP_WhisperSouls', 'Data: 0']))
    # 804 the souls' effect (Argent Verdict's constant script effect shape), 806 the ability carrying it
    rec('MagicEffects', 'ZP_WhisperSoulsMGEF', '000804', '\n'.join(
        ['FormKey: ' + me('000804'), 'EditorID: ZP_WhisperSoulsMGEF',
         props(('ZP_WhisperSoulsScript', vfx + [('Souls', me('000803')), ('FullSound', me('00080F')),
                                                ('Axe', me('000800')), ('Wave', me('00080A')),       # the release
                                                ('EmptyActivator', '0B79FF:Skyrim.esm'), ('ReleaseSound', CAPTURE),
                                                ('PoofSound', me('000823'))]))] +
        ['Name:', '  TargetLanguage: English', '  Value: Whisper Souls',
         'Flags:', '- NoDuration', '- NoMagnitude', '- NoArea', '- HideInUI', '- Painless',
         'Archetype:', '  MutagenObjectType: MagicEffectArchetype', '  Type: Script',
         'DualCastScale: 1', 'Sounds: []',
         'Description:', '  TargetLanguage: English', "  Value: ''"]))
    rec('Spells', 'ZP_WhisperSoulsAbility', '000806', '\n'.join(
        ['FormKey: ' + me('000806'), 'EditorID: ZP_WhisperSoulsAbility',
         'Name:', '  TargetLanguage: English', '  Value: Whisper Souls',
         'EquipmentType: 013F44:Skyrim.esm',
         'Description:', '  TargetLanguage: English', "  Value: ''",
         'Flags:', '- ManualCostCalc', '- IgnoreResistance', '- NoAbsorbOrReflect',
         'Type: Ability', 'Effects:', '- BaseEffect: ' + me('000804'), '  Data: {}',
         '- BaseEffect: ' + me('00080D'), '  Data: {}', '  Conditions:',                 # the light, while full
         '  - MutagenObjectType: ConditionFloat', '    CompareOperator: GreaterThanOrEqualTo', '    Data:',
         '      MutagenObjectType: GetGlobalValueConditionData', '      Global: ' + me('000803'),
         '    ComparisonValue: %d' % SOULS]))
    # 80E / 80F the fully charged sound (the curator's file, tools/04), Argent Verdict's charged bell's record shape
    inst = _module('w_sound', os.path.join(HERE, '04-install-sound.py'))
    if inst.CHARGED_OUT.replace('/', chr(92)) != CHARGED_FILE[len('data' + chr(92)):]:
        sys.exit('tools/04 writes %s, the record plays %s' % (inst.CHARGED_OUT, CHARGED_FILE))
    rec('SoundDescriptors', 'ZP_WhisperChargedSD', '00080E', '\n'.join([
        'FormKey: ' + me('00080E'), 'EditorID: ZP_WhisperChargedSD', 'Type: Standard',
        'Category: 0172A1:Skyrim.esm', 'SoundFiles:', '- ' + CHARGED_FILE, 'OutputModel: 0F1B1A:Skyrim.esm',
        'LoopAndRumble: {}', 'Priority: 128']))
    rec('SoundMarkers', 'ZP_WhisperChargedSound', '00080F', '\n'.join([
        'FormKey: ' + me('00080F'), 'EditorID: ZP_WhisperChargedSound', 'FormVersion: 43',
        'SoundDescriptor: ' + me('00080E')]))
    # 80C the charged light: Candlelight's light in purple
    li = one(os.path.join(BASE, 'Skyrim', 'Lights'), '03FA58_Skyrim.esm')
    assert "Color: '#0081AFE2'" in li and 'Radius: 450' in li and '- Dynamic' in li
    li = sub1(li, r'^FormKey: .*$', 'FormKey: ' + me('00080C'))
    li = sub1(li, r'^EditorID: .*$', 'EditorID: ZP_WhisperChargedLight')
    li = sub1(li, r"^Color: '#[0-9A-F]{8}'$", "Color: '%s'" % CHARGED_COLOUR)
    li = sub1(li, r'^Radius: \d+$', 'Radius: %d' % CHARGED_RADIUS)
    rec('Lights', 'ZP_WhisperChargedLight', '00080C', li)
    # 80D the charged light's effect: LightFFSelfConstant 146677's shape, no orb, casting art or sounds, hidden
    rec('MagicEffects', 'ZP_WhisperChargedLightMGEF', '00080D', '\n'.join([
        'FormKey: ' + me('00080D'), 'EditorID: ZP_WhisperChargedLightMGEF',
        'Name:', '  TargetLanguage: English', '  Value: Whisper Charged',
        'Flags:', '- NoDuration', '- NoMagnitude', '- NoArea', '- HideInUI', '- Painless',
        'MagicSkill: Alteration',
        'Archetype:', '  MutagenObjectType: MagicEffectLightArchetype', '  Association: ' + me('00080C'),
        'DualCastScale: 1', 'Sounds: []',                                       # ConstantEffect, Self: the defaults
        'Description:', '  TargetLanguage: English', "  Value: ''"]))
    # 810 the wave's light (Candlelight's in purple), 812 its flight sound, 811 the wave (Fire Breath's cone projectile
    # on tools/05's crescent)
    li = one(os.path.join(BASE, 'Skyrim', 'Lights'), '03FA58_Skyrim.esm')
    li = sub1(li, r'^FormKey: .*$', 'FormKey: ' + me('000810'))
    li = sub1(li, r'^EditorID: .*$', 'EditorID: ZP_WhisperWaveLight')
    li = sub1(li, r"^Color: '#[0-9A-F]{8}'$", "Color: '%s'" % WAVE_LIGHT_COLOUR)
    li = sub1(li, r'^Radius: \d+$', 'Radius: %d' % WAVE_LIGHT_RADIUS)
    rec('Lights', 'ZP_WhisperWaveLight', '000810', li)
    rec('SoundDescriptors', 'ZP_WhisperWaveSD', '000812', '\n'.join([
        'FormKey: ' + me('000812'), 'EditorID: ZP_WhisperWaveSD', 'Type: Standard',
        'Category: 0172A1:Skyrim.esm', 'SoundFiles:', '- ' + WAVE_SOUND, 'OutputModel: 0FD93D:Skyrim.esm',
        'LoopAndRumble: {}', 'Priority: 128']))
    wave_tool = _module('w_wave', os.path.join(HERE, '05-soul-wave.py'))
    if wave_tool.WAVE_OUT.replace('/', chr(92)) != 'meshes' + chr(92) + WAVE_MODEL:
        sys.exit('tools/05 writes %s, the projectile shows %s' % (wave_tool.WAVE_OUT, WAVE_MODEL))
    pr = one(os.path.join(BASE, 'Skyrim', 'Projectiles'), '0647BF_Skyrim.esm')
    assert 'Type: Cone' in pr and 'File: Magic' + chr(92) + 'VoiceFlameWaveProject01.nif' in pr
    pr = sub1(pr, r'^FormKey: .*$', 'FormKey: ' + me('000811'))
    pr = sub1(pr, r'^EditorID: .*$', 'EditorID: ZP_WhisperWaveProj')
    pr = sub1(pr, r'^Model:\n  File: .*\n  Data: .*\n', lambda m: 'Model:\n  File: %s\n' % WAVE_MODEL)
    pr = sub1(pr, r'^Speed: \d+$', 'Speed: %d' % WAVE_SPEED)
    pr = sub1(pr, r'^Range: \d+$', 'Range: %d' % WAVE_RANGE)
    pr = sub1(pr, r'^Light: .*$', 'Light: ' + me('000810'))
    pr = sub1(pr, r'^Sound: .*$', 'Sound: ' + me('000812'))
    pr = sub1(pr, r'^ConeSpread: \d+$', 'ConeSpread: %d' % WAVE_SPREAD)
    pr = sub1(pr, r'^CollisionRadius: \d+$', 'CollisionRadius: %d' % WAVE_COLLISION)
    rec('Projectiles', 'ZP_WhisperWaveProj', '000811', pr)
    # 809 the wave's blow (magic damage, Aimed on 811, the soul trap shimmer on the target), 80A its spell
    om = value_mgef('000809', 'ZP_WhisperCleaveMGEF', 'Soul Cleave', False)
    om = sub1(om, r'^TargetType: Touch$', 'TargetType: Aimed')
    om = sub1(om, r'^(CastType: FireAndForget)$', lambda m: 'Projectile: ' + me('000811') + '\n' + m.group(1))
    om = sub1(om, r'^(ResistValue: ResistMagic)$', lambda m: m.group(1) + '\nHitShader: ' + SHIMMER)
    rec('MagicEffects', 'ZP_WhisperCleaveMGEF', '000809', om)
    osp = touch_spell('00080A', 'ZP_WhisperCleave', 'Soul Cleave', '000809', CLEAVE_DAMAGE)
    osp = sub1(osp, r'^TargetType: Touch$', 'TargetType: Aimed')
    osp = sub1(osp, r'^Effects:\n', 'Effects:\n- BaseEffect: %s\n  Data:\n    Duration: 1\n' % me('000813'))  # the wisp's mark
    rec('Spells', 'ZP_WhisperCleave', '00080A', osp)
    # 805 Soul Cleave (Argent Verdict's Smite effect shape: an instant script effect on the struck enemy), on the card
    rec('MagicEffects', 'ZP_WhisperCleaveEffect', '000805', '\n'.join(
        ['FormKey: ' + me('000805'), 'EditorID: ZP_WhisperCleaveEffect',
         props(('ZP_WhisperCleaveScript', [('Wave', me('00080A')), ('EmptyActivator', '0B79FF:Skyrim.esm'),
                                         ('Souls', me('000803')), ('ReleaseSound', CAPTURE), ('GatherVFX', GATHER),
                                         ('PoofSound', me('000823')), ('PlayerRef', '000014:Skyrim.esm')]))] +
        ['Name:', '  TargetLanguage: English', '  Value: Soul Cleave',
         'Flags:', '- NoDuration', '- NoMagnitude', '- NoArea', '- Painless',
         'Archetype:', '  MutagenObjectType: MagicEffectArchetype', '  Type: Script',
         'CastType: FireAndForget', 'TargetType: Touch', 'DualCastScale: 1', 'CastingSoundLevel: Silent',
         'Sounds: []',
         'Description:', '  TargetLanguage: English',                       # quoted only for a ': '
         "  Value: '%s'" % CLEAVE_TEXT.replace("'", "''") if ': ' in CLEAVE_TEXT else '  Value: ' + CLEAVE_TEXT]))


def wisp_records():
    """813-81C: the soul wisp (see the docstring)."""
    wisp_tool = _module('w_wisp', os.path.join(HERE, '06-soul-wisp.py'))
    if wisp_tool.OUT.replace('/', chr(92)) != 'meshes' + chr(92) + WISP_MODEL:
        sys.exit('tools/06 writes %s, the art shows %s' % (wisp_tool.OUT, WISP_MODEL))
    # 813 the mark on the wave: hidden, 1 s, survives death; hostile actors only
    rec('MagicEffects', 'ZP_WhisperWispMark', '000813', '\n'.join(
        ['FormKey: ' + me('000813'), 'EditorID: ZP_WhisperWispMark',
         props(('ZP_WhisperWispMarkEffect', [('Wisp', me('000815')), ('Wisps', me('000814')),
                                            ('PlayerRef', '000014:Skyrim.esm')]))] +
        ['Name:', '  TargetLanguage: English', '  Value: Soul Wisp',
         'Flags:', '- NoMagnitude', '- NoArea', '- HideInUI', '- Painless', '- NoDeathDispel',
         'Archetype:', '  MutagenObjectType: MagicEffectArchetype', '  Type: Script',
         'Projectile: ' + me('000811'), 'CastType: FireAndForget', 'TargetType: Aimed',
         'DualCastScale: 1', 'CastingSoundLevel: Silent', 'Sounds: []',
         'Description:', '  TargetLanguage: English', "  Value: ''",
         'Conditions:'] + [line[2:] for line in HOSTILE]))
    # 814 the wisp out
    rec('FormLists', 'ZP_WhisperWisps', '000814', 'FormKey: %s\nEditorID: ZP_WhisperWisps' % me('000814'))
    # 815 the wisp: Enderal's Wisp (EGO's record), made a short-lived ally as Midnight Sting's spiderling
    n = one(os.path.join(EGO, 'Npcs'), '0D0D69_Skyrim.esm')
    assert 'EditorID: _20E_IrrlichtGrouped' in n and 'Race: 013209:Skyrim.esm' in n and 'WornArmor: 086F42:Skyrim.esm' in n
    n = sub1(n, r'^FormKey: .*$', 'FormKey: ' + me('000815'))
    n = sub1(n, r'^EditorID: .*$', 'EditorID: ZP_WhisperWisp')
    n = sub1(n, r'^VirtualMachineAdapter:\n(?:  .*\n)+', '')    # EP (pays a killer of None), ghost, combat music
    n = sub1(n, r'^  Flags:\n  - Respawn\n  - UseTemplate\n', '')
    n = sub1(n, r'^(  Level:\n)    MutagenObjectType: NpcLevel\n    Level: \d+\n',
             r'\g<1>    MutagenObjectType: PcLevelMult\n    LevelMult: 1\n  CalcMinLevel: 1\n  CalcMaxLevel: 100\n')
    n = sub1(n, r'^Factions:\n(?:- .*\n  .*\n)+', 'Factions:\n- Faction: 000DB1:Skyrim.esm\n  Fluff: 0x000000\n')  # PlayerFaction
    n = sub1(n, r'^Race: 013209:Skyrim.esm\n', 'Race: %s\nActorEffect:\n- %s\n' % (me('000818'), me('000816')))
    n = sub1(n, r'^WornArmor: .*$', 'WornArmor: ' + me('000819'))
    n = sub1(n, r'^AttackRace: .*$', 'AttackRace: ' + me('000818'))
    n = sub1(n, r'^Perks:\n(?:- .*\n(?:  .*\n)*)+', '')         # EGO's: no EGO master
    n = sub1(n, r'^Items:\n(?:- .*\n(?:  .*\n)*)+', '')
    n = sub1(n, r'^AIData:\n(?:  .*\n)+', 'AIData:\n  Aggression: Aggressive\n  Confidence: Foolhardy\n'
             '  EnergyLevel: 50\n  Responsibility: NoCrime\n  Assistance: HelpsFriendsAndAllies\n')
    n = sub1(n, r'^Packages:\n- 046189:Skyrim.esm\n', 'Packages:\n- 04B037:Skyrim.esm\nKeywords:\n- 044FEA:Skyrim.esm\n')
    n = english(n, 'Name', 'Soul Wisp')
    assert EGO_ESP not in n, 'an EGO reference left on the wisp'
    rec('Npcs', 'ZP_WhisperWisp', '000815', n)
    # 816 / 817 its ability (Midnight Sting's spiderling ability shape)
    rec('MagicEffects', 'ZP_WhisperWispEffect', '000817', '\n'.join(
        ['FormKey: ' + me('000817'), 'EditorID: ZP_WhisperWispEffect',
         props(('ZP_WhisperWispEffect', [('GlowFX', me('00081B')), ('Wisps', me('000814')),
                                        ('LoopSound', me('000821')), ('Rupture', me('00081E')),
                                        ('BurstFX', me('00081F')), ('StreamVFX', STREAM), ('GatherVFX', GATHER)]))] +
        ['Name:', '  TargetLanguage: English', '  Value: Soul Wisp',
         'Flags:', '- NoDuration', '- NoMagnitude', '- NoArea', '- HideInUI', '- Painless',
         'Archetype:', '  MutagenObjectType: MagicEffectArchetype', '  Type: Script',
         'DualCastScale: 1', 'CastingSoundLevel: Silent', 'Sounds: []',
         'Description:', '  TargetLanguage: English', "  Value: ''"]))
    rec('Spells', 'ZP_WhisperWispAbility', '000816', '\n'.join(
        ['FormKey: ' + me('000816'), 'EditorID: ZP_WhisperWispAbility',
         'Name:', '  TargetLanguage: English', '  Value: Soul Wisp',
         'MenuDisplayObject: 0435A5:Skyrim.esm', 'EquipmentType: 013F44:Skyrim.esm',
         'Description:', '  TargetLanguage: English', "  Value: ''",
         'Type: Ability', 'Effects:', '- BaseEffect: ' + me('000817'), '  Data: {}']))
    # 818 its race: WitchlightRace without the blue glow's ability and EGO's own keyword
    r = one(os.path.join(EGO, 'Races'), '013209_Skyrim.esm')
    r = sub1(r, r'^FormKey: .*$', 'FormKey: ' + me('000818'))
    r = sub1(r, r'^EditorID: .*$', 'EditorID: ZP_WhisperWispRace')
    r = english(r, 'Name', 'Soul Wisp')
    r = sub1(r, r'^ActorEffect:\n- 08CDD1:Skyrim.esm\n- 0D2060:Skyrim.esm\n', 'ActorEffect:\n- 0D2060:Skyrim.esm\n')
    r = sub1(r, r'^Skin: 086F42:Skyrim.esm$', 'Skin: ' + me('000819'))
    r = sub1(r, r'^- 0008C7:%s\n' % re.escape(EGO_ESP), '')
    assert EGO_ESP not in r and '091F78:Skyrim.esm' in r, 'the race copy'
    rec('Races', 'ZP_WhisperWispRace', '000818', r)
    # 819 / 81A its skin, for its race
    a = one(os.path.join(BASE, 'Skyrim', 'Armors'), '086F42_Skyrim.esm')
    a = sub1(a, r'^FormKey: .*$', 'FormKey: ' + me('000819'))
    a = sub1(a, r'^EditorID: .*$', 'EditorID: ZP_WhisperWispSkin')
    a = sub1(a, r'^Race: 013209:Skyrim.esm$', 'Race: ' + me('000818'))
    a = sub1(a, r'^Armature:\n- 086F41:Skyrim.esm$', 'Armature:\n- ' + me('00081A'))
    a = sub1(a, r'^(Description:\n  TargetLanguage: English\n)(?!  Value)', r"\g<1>  Value: ''\n")   # as Spriggit writes it
    rec('Armors', 'ZP_WhisperWispSkin', '000819', a)
    aa = one(os.path.join(BASE, 'Skyrim', 'ArmorAddons'), '086F41_Skyrim.esm')
    aa = sub1(aa, r'^FormKey: .*$', 'FormKey: ' + me('00081A'))
    aa = sub1(aa, r'^EditorID: .*$', 'EditorID: ZP_WhisperWispSkinAA')
    aa = sub1(aa, r'^Race: 013209:Skyrim.esm$', 'Race: ' + me('000818'))
    rec('ArmorAddons', 'ZP_WhisperWispSkinAA', '00081A', aa)
    # 81B / 81C its glow, on tools/06's purple mesh
    v = one(os.path.join(BASE, 'Skyrim', 'VisualEffects'), '08CDCF_Skyrim.esm')
    v = sub1(v, r'^FormKey: .*$', 'FormKey: ' + me('00081B'))
    v = sub1(v, r'^EditorID: .*$', 'EditorID: ZP_WhisperWispFX')
    v = sub1(v, r'^EffectArt: 08CDCE:Skyrim.esm$', 'EffectArt: ' + me('00081C'))
    rec('VisualEffects', 'ZP_WhisperWispFX', '00081B', v)
    o = one(os.path.join(BASE, 'Skyrim', 'ArtObjects'), '08CDCE_Skyrim.esm')
    o = sub1(o, r'^FormKey: .*$', 'FormKey: ' + me('00081C'))
    o = sub1(o, r'^EditorID: .*$', 'EditorID: ZP_WhisperWispFXArt')
    o = sub1(o, r'^Model:\n  File: .*\n  Data: .*\n', lambda m: 'Model:\n  File: %s\n' % WISP_MODEL)
    rec('ArtObjects', 'ZP_WhisperWispFXArt', '00081C', o)
    # 81D / 81E the burst's Rupture: magic resistance -RUPTURE for RUPTURE_SECONDS on enemies (Alteration: never an
    # Entropy hit, so it feeds no souls), the soul trap shimmer on them
    rec('MagicEffects', 'ZP_WhisperWispRuptureMGEF', '00081D', '\n'.join([
        'FormKey: ' + me('00081D'), 'EditorID: ZP_WhisperWispRuptureMGEF',
        'Name:', '  TargetLanguage: English', '  Value: Soul Rupture',
        'Flags:', '- Hostile', '- Recover', '- Detrimental', '- NoArea',
        'BaseCost: 1', 'MagicSkill: Alteration', 'HitShader: ' + SHIMMER,
        'Archetype:', '  MutagenObjectType: MagicEffectArchetype', '  ActorValue: ResistMagic',
        'CastType: FireAndForget', 'TargetType: TargetActor', 'SkillUsageMultiplier: 1', 'DualCastScale: 1',
        'Sounds: []',
        'Description:', '  TargetLanguage: English', '  Value: Magic resistance reduced by <mag>% for <dur> seconds.',
        'Conditions:'] + [line[2:] for line in HOSTILE]))
    rs = touch_spell('00081E', 'ZP_WhisperWispRupture', 'Soul Rupture', '00081D', RUPTURE)
    rs = sub1(rs, r'^TargetType: Touch$', 'TargetType: TargetActor')
    rs = sub1(rs, r'^(    Magnitude: \d+)$', lambda m: m.group(1) + '\n    Duration: %d' % RUPTURE_SECONDS)
    rec('Spells', 'ZP_WhisperWispRupture', '00081E', rs)
    # 81F the burst's flash: the Wisp's own death explosion wispDeathExplosion 0F1189 on tools/06's purple copy, without
    # its enchantment (a stray armour enchantment) and its screen flash: harmless
    x = one(os.path.join(BASE, 'Skyrim', 'Explosions'), '0F1189_Skyrim.esm')
    assert 'File: Magic' + chr(92) + 'ExplosionIllusionLight01.nif' in x
    x = sub1(x, r'^FormKey: .*$', 'FormKey: ' + me('00081F'))
    x = sub1(x, r'^EditorID: .*$', 'EditorID: ZP_WhisperWispBurst')
    x = sub1(x, r'^Model:\n  File: .*\n  Data: .*\n', lambda m: 'Model:\n  File: %s\n' % WISP_BURST_MODEL)
    x = sub1(x, r'^ObjectEffect: .*\n', '')
    x = sub1(x, r'^ImageSpaceModifier: .*\n', '')
    rec('Explosions', 'ZP_WhisperWispBurst', '00081F', x)
    # 820-823 the wisp's whisper (looping, mono, heard within 1800) and Soul Cleave's poof (stereo), the curator's files
    inst = _module('w_sound2', os.path.join(HERE, '04-install-sound.py'))
    for out, rel in ((inst.WISP_OUT, WISP_LOOP_FILE), (inst.POOF_OUT, POOF_FILE)):
        if out.replace('/', chr(92)) != rel[len('data' + chr(92)):]:
            sys.exit('tools/04 writes %s, the record plays %s' % (out, rel))
    for sd, sm, eid, path, model, loop in (('000820', '000821', 'ZP_WhisperWispLoop', WISP_LOOP_FILE, '10E425:Skyrim.esm', True),
                                           ('000822', '000823', 'ZP_WhisperPoof', POOF_FILE, '0FD93D:Skyrim.esm', False)):
        rec('SoundDescriptors', eid + 'SD', sd, '\n'.join([
            'FormKey: ' + me(sd), 'EditorID: %sSD' % eid, 'Type: Standard',
            'Category: 0172A1:Skyrim.esm', 'SoundFiles:', '- ' + path, 'OutputModel: ' + model] +
            (['LoopAndRumble:', '  Loop: Loop'] if loop else ['LoopAndRumble: {}']) + ['Priority: 128']))
        rec('SoundMarkers', eid + 'Sound', sm, '\n'.join([
            'FormKey: ' + me(sm), 'EditorID: %sSound' % eid, 'FormVersion: 43', 'SoundDescriptor: ' + me(sd)]))


def main():
    check_winners()
    check_scripts()
    bounds = mesh_bounds()
    for sub in ('Weapons', 'Statics', 'ObjectEffects', 'Globals', 'MagicEffects', 'Spells', 'Lights',
                'SoundDescriptors', 'SoundMarkers', 'Projectiles', 'FormLists', 'Npcs', 'Races', 'Armors',
                'ArmorAddons', 'VisualEffects', 'ArtObjects', 'Explosions'):
        shutil.rmtree(os.path.join(OUT, sub), ignore_errors=True)

    # 800 the axe
    w = one(os.path.join(EGO, 'Weapons'), '07C992_Skyrim.esm')
    assert re.search(r'^  Damage: 26$', w, re.M) and 'Speed: 0.9\n' in w and 'ObjectEffect' not in w
    assert 'Template' not in w and 'VirtualMachineAdapter' not in w and EGO_ESP not in w   # nothing of EGO's own
    w = sub1(w, r'^FormKey: .*$', 'FormKey: 000800:' + ME)
    w = sub1(w, r'^EditorID: .*$', 'EditorID: ZP_Whisper')
    w = sub1(w, r'^(EditorID: ZP_Whisper\n)', lambda m: m.group(1) + props(       # in hand: the souls ability
        ('ZP_WhisperEquipScript', [('Axe', '000800:' + ME), ('SoulsAbility', '000806:' + ME),
                                   ('PlayerRef', '000014:Skyrim.esm')])) + '\n')
    w = sub1(w, r'^ObjectBounds:\n  First: .*\n  Second: .*\n', bounds)
    w = english(w, 'Name', NAME)
    assert 'File: ' + r'Weapons\Elven\ElvenWarAxe.nif' in w
    w = sub1(w, r'^Model:\n  File: .*\n  Data: .*\n', lambda m: 'Model:\n  File: %s\n' % MODEL)   # Data = old hashes
    w = sub1(w, r'^Keywords:\n(?:- .*\n)+', 'Keywords:\n' + ''.join('- %s\n' % k for k in KEYWORDS))
    w = sub1(w, r'^(EquipmentType: )', lambda m: 'ObjectEffect: 000802:%s\nEnchantmentAmount: %d\n' % (ME, CHARGE) + m.group(1))
    w = sub1(w, r'^FirstPersonModel: .*$', 'FirstPersonModel: 000801:' + ME)
    w = sub1(w, r'^(BasicStats:\n  Value: )\d+$', r'\g<1>%d' % VALUE)
    w = sub1(w, r'^(  Weight: \d+\n  Damage: )\d+$', r'\g<1>%d' % DAMAGE)
    w = sub1(w, r'^(Critical:\n  Damage: )\d+$', r'\g<1>%d' % CRIT)
    rec('Weapons', 'ZP_Whisper', '000800', w)

    # 801 its first-person static
    st = one(os.path.join(BASE, 'Skyrim', 'Statics'), '036BCC_Skyrim.esm')
    assert 'File: ' + r'Weapons\Elven\1stPersonElvenWarAxe.nif' in st
    st = sub1(st, r'^FormKey: .*$', 'FormKey: 000801:' + ME)
    st = sub1(st, r'^EditorID: .*$', 'EditorID: 1stPersonZP_Whisper')
    st = sub1(st, r'^ObjectBounds:\n  First: .*\n  Second: .*\n', bounds)
    st = sub1(st, r'^Model:\n  File: .*\n  Data: .*\n', lambda m: 'Model:\n  File: %s\n' % MODEL)
    rec('Statics', '1stPersonZP_Whisper', '000801', st)
    souls_records()
    wisp_records()
    print('wrote', OUT, '(800 WEAP ZP_Whisper, 801 STAT 1stPersonZP_Whisper, 802-806, 809-812 the souls, Soul Cleave, '
          'soul trap, the charged light and sound; 813-81C the soul wisp);',
          bounds.replace('\n', ' '))


if __name__ == '__main__':
    main()
