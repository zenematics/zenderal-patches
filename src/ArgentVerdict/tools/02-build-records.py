"""Argent Verdict's records (curator 2026-11-13): a unique silver great hammer on Pretty Enderal Armory's Aeterna
Warhammer, all silver with a dark navy leather grip and a spiked gauntlet for its head's centre (tools/01's own mesh),
whose light-attack hits light four tiny rune-circle motes on the gauntlet's knuckles, one every two; once all four are
lit, the next power
attack calls Kittytail's Absolution beam down from the sky onto up to four enemies round the player (version 3,
curator 2026-11-14: "Keep the 4 knuckle motes / instead of the Chain lightning, smite 4 enemies in proximity to the
player on charged power attack. the smite beams come from the sky like regular smite. but the effect is like the
effect from the picture (I believe this is the Absolution spell in Dark hierohant)"); 2026-11-15: "this version
we've made is THE Argent Verdict", "remove the other versions"). Version 2 (the bolt from the hammer, chaining to 4
enemies; records 841-844, 848-84A, 84C-84E) and version 1 (20% of hits, the bolt from the sky) are gone, their
backups deleted (git history has them); their FormIDs stay retired.

  800 WEAP ZP_ArgentVerdict          <- EGO's Aeterna Warhammer 07C993: 46 damage (EGO 42; Qalian's Absolution 44),
                                        crit 23, speed 0.65, value 1500; keywords: Aeterna material (EGO's smithing),
                                        silver (EGO's silver perks vs undead, Prophecy's Smite talent), unique, no
                                        enchanting, no vendor; tools/01's mesh, the spiked gauntlet head (its
                                        textures in the mesh), bounds measured from it; enchantment 803
  801 STAT 1stPersonZP_ArgentVerdict <- 1stPersonElvenWarhammer 036BD2 on the same mesh (Pretty's two are one file)
  803 ENCH ZP_ArgentVerdictSmite     weapon enchantment, on hits on an actor hostile to the player (instant effects:
                                        their conditions are tested once per hit): 851 on a light attack while 852 is
                                        below HITS; 804 on a power attack while 852 is HITS and the player has
                                        MANA_COST Mana
  804 MGEF ZP_ArgentVerdictSmiteEffect "Smite", the release: Prophecy's Smite effect A67's shape (an instant script
                                        effect on the struck target) running ZP_ArgentVerdictSmiteScript (Scripts/source),
                                        shown on the item card
  805 COBJ ZP_TemperArgentVerdict    <- the Aeterna Warhammer's grindstone temper 148AB7, new product
  806, 807 retired (2026-11-15): "Argent Verdict (Gauntlet)" and its first-person static, the gauntlet beside the
                                        hand head while the curator compared them; the gauntlet is now 800's own mesh

The charges (the motes are nodes in tools/01's meshes, motes.py):
  851 MGEF ZP_ArgentVerdictChargeMGEF  a charge: A67's shape running ZP_ArgentVerdictChargeScript, hidden
  852 GLOB ZP_ArgentVerdictCharges   0..HITS (GlobalVariable.Mod: thread-safe); a mote per HITS / KNUCKLES
  853 MGEF ZP_ArgentVerdictMotesMGEF   the motes' display: a constant script effect (Prophecy's AD6's shape) running
                                        ZP_ArgentVerdictMotesScript (SetNodeScale every second)
  854 SPEL ZP_ArgentVerdictMotes     the ability carrying 853, added while a hammer is equipped (the weapons' script
                                        ZP_ArgentVerdictEquipScript) and by the first charge
The release (tools/03 writes the beam, the impact, their textures and the sounds):
  856 ACTI ZP_ArgentVerdictBeamFX    a smite beam: tools/03's VerdictSmiteBeam.nif (Kittytail's Absolution beam on end,
                                        her rune circle at the top), nameless; FXEmptyActivator 0B79FF's record. The
                                        release script places one BeamLength above each enemy's feet and deletes it
The orbs (curator 2026-11-14: "add the motes we use on the knuckles as orbs that fire out of the smite beams (just
like the regular Smith from Prophecy talent but dark heirophant effect)"):
  85A PROJ ZP_ArgentVerdictOrbProj   <- Prophecy's Smite orb ZP_Holy_LightshaftScatterProj A4B (Kittytails' Holy
                                        Templar light shaft: 540 a second, range 1620; curator, with a picture of
                                        Prophecy's Smite orbs: "I want this but the Dark heirophant effects / colors")
                                        on tools/03's VerdictOrb.nif (that orb in white and black), light 85F; her
                                        Cone type (one build's Missile changed nothing: the orbs flew along the floor
                                        because of the spawner script, see ZP_ArgentVerdictOrbSpawnerScript)
  85F LIGH ZP_ArgentVerdictOrbLight  <- its light ZP_Holy_MagicHealProj A49 in a cool white, ORB_LIGHT_RADIUS
  85B MGEF ZP_ArgentVerdictOrbMGEF   an orb's damage to Health <- her Absolution effect 801 as 845, but Aimed on 85A
  85C MGEF ZP_ArgentVerdictOrbUndeadMGEF  85B on undead only
  85D SPEL ZP_ArgentVerdictOrb       85B / 85C (ORB_DAMAGE), Aimed: the beam script RemoteCasts it
  860 ACTI ZP_ArgentVerdictOrbSpawner  the orbs' spawner, 857's PlacedObject (Prophecy's Smite chain: its explosion
                                        A54 places activator A46, whose script fires the light shafts from OnInit):
                                        FXEmptyActivator 0B79FF's record, nameless, script
                                        ZP_ArgentVerdictOrbSpawnerScript (OnInit fires the orbs, then deletes itself).
                                        Two builds fired them from the beam (OnLoad, then OnActivate): never seen
  85E retired: the first orb's impact (that orb, the knuckle motes' circle on Kittytail's Penance blade projectile,
      was never seen in game; Prophecy's Smite orb has none); never reuse
  857 EXPL ZP_ArgentVerdictBeamImpact  where a beam lands: tools/03's VerdictImpact.nif (Kittytail's impact, white and
                                        black) with the strike's sound 80C, placing the orb spawner 860; Enderal's
                                        Wayfarer fire nova 143325's record without its enchantment, screen effect,
                                        decals, push and damage
  845 MGEF ZP_ArgentVerdictStrikeMGEF  a beam's damage to Health <- Kittytail's Absolution effect _BL_DischargeMGEF 801
                                        (ResistMagic), Touch, fixed numbers, hidden, her white glow 84B, no projectile,
                                        casting art, screen flash or sounds, hostile actors only
  846 MGEF ZP_ArgentVerdictStrikeUndeadMGEF  845 on undead only (their double damage)
  855 MGEF ZP_ArgentVerdictStrikeSMMGEF  to Stamina and Magicka <- her _BL_DischargeStaminaMagickaMGEF 802, trimmed so
  847 SPEL ZP_ArgentVerdictStrike    845 / 846 / 855 (STRIKE: 80 / 80 / 40), Touch: the script applies it with
                                        DoCombatSpellApply
  84B EFSH ZP_ArgentVerdictShockGlow <- Kittytail's _BL_EffectShaderWhiteShockGlow 848 on our white palette
  80C SNDR ZP_ArgentVerdictStrikeSD  <- Kittytail's _BL_ExpFlareSD 863 on tools/03's SmiteStrike.wav (FlareBig faster)
  84F SNDR ZP_ArgentVerdictBellSD    80C's record on tools/03's SmiteBell.wav (the curator's church bell, 2026-11-14:
                                        "add this sound addtionally to the smite")
  850 SOUN ZP_ArgentVerdictBellSound plays 84F (the script rings it once a release)
  858 SNDR ZP_ArgentVerdictChargedSD 84F's record on tools/03's SmiteCharged.wav (the curator's second church bell,
                                        2026-11-14: "add this sound once the weapon is full charged ready to release
                                        its payload")
  859 SOUN ZP_ArgentVerdictChargedSound plays 858: the charge script rings it when the last knuckle lights

Retired, never reuse: 802 (the first build's texture swap TXST), 806-807 (the gauntlet's second record and static
while it was compared with the hand head), 808-80B and 80D-840 (the Judgement Blade and the Penance fan of
2026-11-14, scrapped: "lets scrap this idea for the unique weapons effect"), 841-844, 848-84A, 84C-84E (version 2's,
removed 2026-11-15 with its backup).

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
MODEL = r'Zenderal\ArgentVerdict\ArgentVerdict.nif'    # tools/01's, both views: the spiked gauntlet head
# where Argent Verdict is found (curator 2026-11-15, from a shortlist: "Destroyed Abbey"): Thalgard's ruined abbey of the
# Order, laid on the socket of the Malphas statue (refs 128502 / 128503) at the far end of its Halls, past Sunborn mages
# and archers (level 45) and monk ghosts; in front of the statue, across the socket's front edge (y 7512), clear of the
# statue's base. The cell header is Skyrim.esm's (the only plugin with it)
PLACE = dict(cell='ThalgardOrdensklosterL1', header='Skyrim.esm', surface='128502:Skyrim.esm', socket_rot=0.03000412,
             top=1.35,                       # the socket's top in the winning mesh (PG Patcher Output's; surface.levels)
             statue='128503:Skyrim.esm', prefer=(1918.47, 7512.0))
TARGET = 'Zenderal - Patch Collection'                 # where tools/01 writes it
DAMAGE, CRIT, SPEED, VALUE = 46, 23, 0.65, 1500
CHARGE = 3000                                          # Sting and Rise's: ~3000 hits before a recharge
KEYWORDS = ['01E71B:Skyrim.esm',   # WeapMaterialElven: Aeterna (EGO's smithing perks)
            '06727B:Skyrim.esm',   # WeapTypeMelee
            '06D930:Skyrim.esm',   # WeapTypeWarhammer
            '0C27BD:Skyrim.esm',   # MagicDisallowEnchanting (as Qalian's Absolution)
            '10AA1A:Skyrim.esm',   # WeapMaterialSilver
            '14CE9A:Skyrim.esm']   # WeapTypeUnique
SMITE_NAME = 'Smite'
KNUCKLES = 4                       # the motes (one per knuckle); the scripts' Knuckles (checked)
HITS = 8                           # the light-attack hits a full charge takes, two a mote; the scripts' Hits (checked);
#                                    4, any hit, until the curator's balance pass (2026-11-15: "make the charge up be 8
#                                    light attacks not 4")
MANA_COST = 20                     # each release (2026-11-15: "each power attack smite requires 20 mana"); the
#                                    release script's ManaCost (checked)
STRIKE = (80, 80, 40)              # each beam: Health, undead extra, Stamina and Magicka (Absolution's three);
#                                    40 / 40 / 20 until the curator's first test (2026-11-14: "Raise the damage")
TARGETS = 4                        # the release script's Targets (checked)
ORBS = 4                           # the beam script's Orbs (checked): orbs out of each beam
ORB_DAMAGE = (15, 15)              # each orb: Health, undead extra
ORB_LIGHT_RADIUS = 300             # Prophecy's 600: up to 16 orbs at once
ORB_LIGHT = '#00F2F8FF'            # a cool white (Prophecy's is gold)
SMITE_TEXT = ('Every %s light attacks that hit an enemy light a mote of runic light on one of the four knuckles. Once '
              'all four are lit, the next power attack spends %d Mana to call beams of light down from the sky on up '
              'to %d enemies around you, %d damage to Health and %d to Stamina and Magicka each, and each beam '
              'scatters %d orbs of runic light that strike the enemies in their path for %d. Undead take double '
              'damage.' % ({2: 'two', 3: 'three', 4: 'four'}[HITS // KNUCKLES], MANA_COST, TARGETS, STRIKE[0],
                           STRIKE[2], ORBS, ORB_DAMAGE[0]))
assert HITS % KNUCKLES == 0        # a mote per whole number of hits (the item card says how many)
SCRIPTS = os.path.join(ROOT, 'src', 'ArgentVerdict', 'Scripts', 'source')
assert ': ' not in SMITE_TEXT      # a plain YAML value
BEAM_MODEL = r'Zenderal\ArgentVerdict\VerdictSmiteBeam.nif'   # tools/03: Absolution's beam on end
ORB_MODEL = r'Zenderal\ArgentVerdict\VerdictOrb.nif'          # tools/03: the knuckle motes' circle as an orb
SPAWNER_SCRIPT = os.path.join(ROOT, 'src', 'ArgentVerdict', 'Scripts', 'source', 'ZP_ArgentVerdictOrbSpawnerScript.psc')
IMPACT_MODEL = r'Zenderal\ArgentVerdict\VerdictImpact.nif'     # tools/03: Kittytail's impact, white and black
GLOW_PALETTE = r'Zenderal\ArgentVerdict\Verdict_gradshockhitW.dds'   # tools/03
STRIKE_FILE = r'data\sound\fx\Zenderal\ArgentVerdict\SmiteStrike.wav'   # tools/03: FlareBig faster, shorter
BELL_FILE = r'data\sound\fx\Zenderal\ArgentVerdict\SmiteBell.wav'       # tools/03 --bell: the curator's church bell
CHARGED_FILE = r'data\sound\fx\Zenderal\ArgentVerdict\SmiteCharged.wav' # tools/03 --charged: fully charged
SCRIPT = os.path.join(ROOT, 'src', 'ArgentVerdict', 'Scripts', 'source', 'ZP_ArgentVerdictSmiteScript.psc')
GL = os.path.join(ROOT, 'reference', 'mods', 'DarkHierophantMagic')
GL_ESP = 'Ghostlight.esl'
# Ghostlight records copied: (its id, folder, ours, our EditorID)
GL_COPY = [('000863', 'SoundDescriptors', '00080C', 'ZP_ArgentVerdictStrikeSD'),
           ('000848', 'EffectShaders', '00084B', 'ZP_ArgentVerdictShockGlow')]
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


def gl(folder, fid):
    return one(os.path.join(GL, folder), fid + '_' + GL_ESP)


def gl_remap(text):
    for fid, _, ours, _ in GL_COPY:
        text = text.replace('%s:%s' % (fid, GL_ESP), '%s:%s' % (ours, ME))
    if GL_ESP in text:
        sys.exit('a Ghostlight reference left over: ' + re.search(r'\S+:' + re.escape(GL_ESP), text).group(0))
    return text


def drop(text, pattern):
    out, n = re.subn(pattern, '', text, count=1, flags=re.M)
    if n != 1:
        sys.exit('pattern not found: ' + pattern)
    return out


def cond(kind, value=None, **fields):
    lines = ['- MutagenObjectType: ConditionFloat', '  Data:', '    MutagenObjectType: %sConditionData' % kind]
    lines += ['    %s: %s' % (k, v) for k, v in fields.items()]
    if value is not None:
        lines.append('  ComparisonValue: %s' % value)
    return lines


HOSTILE = cond('IsHostileToActor', 1, TargetNpc='000014:Skyrim.esm')
UNDEAD = cond('HasKeyword', 1, Keyword='013796:Skyrim.esm')   # ActorTypeUndead


def script_const(name, script=SCRIPT):
    m = re.search(r'^Int Property %s = (\d+) AutoReadOnly' % name, read(script), re.M)
    if not m:
        sys.exit('%s: no %s' % (script, name))
    return int(m.group(1))


def script_float(name, script):
    m = re.search(r'^Float Property %s = ([\d.]+) AutoReadOnly' % name, read(script), re.M)
    if not m:
        sys.exit('%s: no %s' % (script, name))
    return float(m.group(1))


def light_mgef(src_fid, fid, editor_id, undead=False, projectile=None):
    """A beam's damage from Kittytail's Absolution effect (801 Health, 802 Stamina + Magicka; verbatim, then trimmed):
    Touch (the script's DoCombatSpellApply), fixed numbers, hidden, her white glow 84B, no menu model, keyword,
    projectile, casting light or art, screen flash, impacts or sounds, hostile actors only, undead only for the twin."""
    t = gl('MagicEffects', src_fid)
    assert 'ResistValue: ResistMagic' in t and 'HitShader: 000848:' + GL_ESP in t
    t = sub1(t, r'^FormKey: .*$', 'FormKey: %s:%s' % (fid, ME))
    t = sub1(t, r'^EditorID: .*$', 'EditorID: ' + editor_id)
    t = english(t, 'Name', SMITE_NAME)
    if projectile:                                                  # an orb: Aimed on our projectile
        t = sub1(t, r'^Projectile: .*$', 'Projectile: %s:%s' % (projectile, ME))
    for pattern in (r'^MenuDisplayObject: .*\n', r'^Keywords:\n(?:- .*\n)+', r'^CastingLight: .*\n', r'^Projectile: 0+83B.*\n',
                    r'^CastingArt: .*\n', r'^ImpactData: .*\n', r'^ImageSpaceModifier: .*\n', r'^MinimumSkillLevel: \d+\n'):
        t = re.sub(pattern, '', t, count=1, flags=re.M)               # not every field is on both effects
    t = sub1(t, r'^Flags:\n(?:- .*\n)+', 'Flags:\n- Hostile\n- Detrimental\n- NoArea\n- FXPersist\n- HideInUI\n'
             '- NoRecast\n- NoDeathDispel\n')                         # no PowerAffectsMagnitude: fixed numbers
    t = sub1(t, r'^CastType: Concentration$', 'CastType: FireAndForget')
    if not projectile:
        t = sub1(t, r'^TargetType: Aimed$', 'TargetType: Touch')
    t = sub1(t, r'^Sounds:(?: \[\])?\n(?:- .*\n|  .*\n)*', 'Sounds: []\n')
    t = english(t, 'Description', "''")
    assert 'Conditions:' not in t
    t = t.rstrip('\n') + '\n' + '\n'.join(['Conditions:'] + HOSTILE + (UNDEAD if undead else [])) + '\n'
    return gl_remap(t)


def spell(fid, editor_id, target_type, effects):
    lines = ['FormKey: %s:%s' % (fid, ME), 'EditorID: ' + editor_id,
             'Name:', '  TargetLanguage: English', '  Value: ' + SMITE_NAME,
             'EquipmentType: 013F44:Skyrim.esm',
             'Description:', '  TargetLanguage: English', "  Value: ''",
             'Flags:', '- ManualCostCalc', '- NoAbsorbOrReflect',
             'CastType: FireAndForget', 'TargetType: ' + target_type, 'Effects:']
    for e, mag in effects:
        lines += ['- BaseEffect: %s:%s' % (e, ME)] + (['  Data:', '    Magnitude: %g' % mag] if mag else ['  Data: {}'])
    return '\n'.join(lines)


def smite():
    """845-847, 84B, 80C, 84F-850, 855-857: the release's records (see the docstring)."""
    if not os.path.isdir(GL):
        sys.exit('serialize Ghostlight.esl into %s first (Spriggit serialize, EnderalSE)' % GL)
    if script_const('Targets') != TARGETS:
        sys.exit('the script smites %d enemies, the item card says %d' % (script_const('Targets'), TARGETS))
    if script_const('Orbs', SPAWNER_SCRIPT) != ORBS:
        sys.exit('the spawner fires %d orbs, the item card says %d' % (script_const('Orbs', SPAWNER_SCRIPT), ORBS))
    for name in ('ZP_ArgentVerdictSmiteScript', 'ZP_ArgentVerdictChargeScript', 'ZP_ArgentVerdictMotesScript'):
        for const, want in (('Knuckles', KNUCKLES), ('Hits', HITS)):
            got = script_const(const, os.path.join(SCRIPTS, name + '.psc'))
            if got != want:
                sys.exit('%s: %s is %d, not %d' % (name, const, got, want))
    if script_float('ManaCost', SCRIPT) != MANA_COST:
        sys.exit('the release script spends %g Mana, the item card says %d' % (script_float('ManaCost', SCRIPT), MANA_COST))
    for fid, folder, ours, editor_id in GL_COPY:
        t = gl(folder, fid)
        t = sub1(t, r'^FormKey: .*$', 'FormKey: %s:%s' % (ours, ME))
        t = sub1(t, r'^EditorID: .*$', 'EditorID: ' + editor_id)
        if fid == '000863':                                           # the strike: tools/03's faster, shorter copy
            t = sub1(t, r'^SoundFiles:\n- .*\n', lambda m: 'SoundFiles:\n- %s\n' % STRIKE_FILE)
        if fid == '000848':                                           # the glow: on our white palette
            t = sub1(t, r'^ParticlePaletteTexture: Effects\\Gradients\\GradShockHit\.dds$',
                     lambda m: 'ParticlePaletteTexture: ' + GLOW_PALETTE)
        rec(folder, editor_id, ours, gl_remap(t))
    # 845 / 846 / 855 a beam's damage, 847 the spell the script applies
    rec('MagicEffects', 'ZP_ArgentVerdictStrikeMGEF', '000845', light_mgef('000801', '000845', 'ZP_ArgentVerdictStrikeMGEF'))
    rec('MagicEffects', 'ZP_ArgentVerdictStrikeUndeadMGEF', '000846',
        light_mgef('000801', '000846', 'ZP_ArgentVerdictStrikeUndeadMGEF', undead=True))
    rec('MagicEffects', 'ZP_ArgentVerdictStrikeSMMGEF', '000855', light_mgef('000802', '000855', 'ZP_ArgentVerdictStrikeSMMGEF'))
    rec('Spells', 'ZP_ArgentVerdictStrike', '000847', spell('000847', 'ZP_ArgentVerdictStrike', 'Touch',
                                                            [('000845', STRIKE[0]), ('000846', STRIKE[1]),
                                                             ('000855', STRIKE[2])]))
    # 856 the beam: FXEmptyActivator's record, nameless, on tools/03's mesh
    a = one(os.path.join(BASE, 'Skyrim', 'Activators'), '0B79FF_Skyrim.esm')
    a = sub1(a, r'^FormKey: .*$', 'FormKey: 000856:' + ME)
    a = drop(a, r'^MajorRecordFlagsRaw: .*\n')
    a = sub1(a, r'^EditorID: .*$', 'EditorID: ZP_ArgentVerdictBeamFX')
    a = drop(a, r'^Version2: .*\n')
    a = drop(a, r'^SkyrimMajorRecordFlags:\n(?:- .*\n)+')
    a = drop(a, r'^Name:\n(?:  .*\n)+')
    a = sub1(a, r'^  File: Effects\\FXEmptyObject\.nif$', lambda m: '  File: ' + BEAM_MODEL)
    a = drop(a, r'^MajorFlags:\n(?:- .*\n)+')
    assert 'VirtualMachineAdapter' not in a
    # 860 the orbs' spawner: the same record (FXEmptyActivator's model), with the orb script
    sp = sub1(a, r'^FormKey: .*$', 'FormKey: 000860:' + ME)
    sp = sub1(sp, r'^EditorID: .*$', 'EditorID: ZP_ArgentVerdictOrbSpawner')
    sp = sub1(sp, r'^  File: .*$', lambda m: '  File: Effects\\FXEmptyObject.nif')
    sp = sub1(sp, r'^(EditorID: ZP_ArgentVerdictOrbSpawner\n)', lambda m: m.group(1) + '\n'.join([
        'VirtualMachineAdapter:', '  Scripts:', '  - Name: ZP_ArgentVerdictOrbSpawnerScript', '    Properties:',
        '    - MutagenObjectType: ScriptObjectProperty', '      Name: EmptyActivator', '      Object: 0B79FF:Skyrim.esm',
        '    - MutagenObjectType: ScriptObjectProperty', '      Name: Orb', '      Object: 00085D:' + ME,
        '    - MutagenObjectType: ScriptObjectProperty', '      Name: PlayerRef', '      Object: 000014:Skyrim.esm', '']))
    rec('Activators', 'ZP_ArgentVerdictOrbSpawner', '000860', sp)
    rec('Activators', 'ZP_ArgentVerdictBeamFX', '000856', a)
    # 857 where a beam lands: Enderal's Wayfarer nova 143325 (Rise's nova's record), only a look and the strike's sound
    x = one(os.path.join(BASE, 'Skyrim', 'Explosions'), '143325_Skyrim.esm')
    assert 'File: Magic\\FireStormAreaEffect.nif' in x
    x = sub1(x, r'^FormKey: .*$', 'FormKey: 000857:' + ME)
    x = sub1(x, r'^EditorID: .*$', 'EditorID: ZP_ArgentVerdictBeamImpact')
    x = drop(x, r'^Version2: .*\n')
    x = sub1(x, r'^Model:\n  File: Magic\\FireStormAreaEffect\.nif\n(?:  Data: .*\n)?', lambda m: 'Model:\n  File: %s\n' % IMPACT_MODEL)
    x = drop(x, r'^ObjectEffect: .*\n')                                # its damage enchantment
    x = drop(x, r'^ImageSpaceModifier: .*\n')                          # its screen effect
    x = sub1(x, r'^Sound1: .*$', 'Sound1: 00080C:%s\nPlacedObject: 000860:%s' % (ME, ME))   # the strike; the orbs
    x = drop(x, r'^ImpactDataSet: .*\n')                               # fire scorch decals
    x = drop(x, r'^Force: .*\n')
    x = drop(x, r'^Damage: .*\n')
    x = sub1(x, r'^Radius: \d+$', 'Radius: 100')
    x = drop(x, r'^ISRadius: .*\n')
    rec('Explosions', 'ZP_ArgentVerdictBeamImpact', '000857', x)
    # 85A the orb: Prophecy's Smite orb projectile on tools/03's white and black copy, 85F its light
    pr = one(os.path.join(PROPHECY, 'Projectiles'), '000A4B_' + PROPHECY_ESP)
    assert 'Type: Cone' in pr and 'File: Lightpower\\HolyBoltProj.nif' in pr and 'Light: 000A49:' + PROPHECY_ESP in pr
    pr = sub1(pr, r'^FormKey: .*$', 'FormKey: 00085A:' + ME)
    pr = sub1(pr, r'^EditorID: .*$', 'EditorID: ZP_ArgentVerdictOrbProj')
    pr = sub1(pr, r'^Model:\n  File: .*\n  Data: .*\n', lambda m: 'Model:\n  File: %s\n' % ORB_MODEL)
    pr = sub1(pr, r'^Light: .*$', 'Light: 00085F:' + ME)
    # her Cone type kept (2026-11-14: one build made it a Missile because the orbs flew along the floor; the cause was
    # the spawner script's x/y/z locals, which the compiler read as the spawner's own X/Y/Z properties in the loop)
    if PROPHECY_ESP in pr:
        sys.exit('a Prophecy reference left in 85A: ' + re.search(r'\S+:' + re.escape(PROPHECY_ESP), pr).group(0))
    rec('Projectiles', 'ZP_ArgentVerdictOrbProj', '00085A', pr)
    li = one(os.path.join(PROPHECY, 'Lights'), '000A49_' + PROPHECY_ESP)
    li = sub1(li, r'^FormKey: .*$', 'FormKey: 00085F:' + ME)
    li = sub1(li, r'^EditorID: .*$', 'EditorID: ZP_ArgentVerdictOrbLight')
    li = sub1(li, r"^Color: '#[0-9A-F]{8}'$", "Color: '%s'" % ORB_LIGHT)
    li = sub1(li, r'^Radius: \d+$', 'Radius: %d' % ORB_LIGHT_RADIUS)
    rec('Lights', 'ZP_ArgentVerdictOrbLight', '00085F', li)
    # 85B / 85C an orb's damage, 85D the spell the beam script RemoteCasts
    rec('MagicEffects', 'ZP_ArgentVerdictOrbMGEF', '00085B', light_mgef('000801', '00085B', 'ZP_ArgentVerdictOrbMGEF',
                                                                     projectile='00085A'))
    rec('MagicEffects', 'ZP_ArgentVerdictOrbUndeadMGEF', '00085C',
        light_mgef('000801', '00085C', 'ZP_ArgentVerdictOrbUndeadMGEF', undead=True, projectile='00085A'))
    rec('Spells', 'ZP_ArgentVerdictOrb', '00085D', spell('00085D', 'ZP_ArgentVerdictOrb', 'Aimed',
                                                         [('00085B', ORB_DAMAGE[0]), ('00085C', ORB_DAMAGE[1])]))
    # 84F the bell (80C's record on the curator's file), 850 its Sound (Ghostlight's sound marker's record)
    b = gl_remap(gl('SoundDescriptors', '000863'))
    b = sub1(b, r'^FormKey: .*$', 'FormKey: 00084F:' + ME)
    b = sub1(b, r'^EditorID: .*$', 'EditorID: ZP_ArgentVerdictBellSD')
    b = sub1(b, r'^SoundFiles:\n- .*\n', lambda m: 'SoundFiles:\n- %s\n' % BELL_FILE)
    b = sub1(b, r'^PercentFrequencyVariance: \d+\n', '')                # the bell keeps its pitch
    rec('SoundDescriptors', 'ZP_ArgentVerdictBellSD', '00084F', b)
    sb = gl('SoundMarkers', '00088D')
    sb = sub1(sb, r'^FormKey: .*$', 'FormKey: 000850:' + ME)
    sb = sub1(sb, r'^EditorID: .*$', 'EditorID: ZP_ArgentVerdictBellSound')
    sb = sub1(sb, r'^SoundDescriptor: .*$', 'SoundDescriptor: 00084F:' + ME)
    rec('SoundMarkers', 'ZP_ArgentVerdictBellSound', '000850', gl_remap(sb))
    # 858 the fully-charged bell (84F's record on the curator's second file), 859 its Sound
    c = sub1(b, r'^FormKey: .*$', 'FormKey: 000858:' + ME)
    c = sub1(c, r'^EditorID: .*$', 'EditorID: ZP_ArgentVerdictChargedSD')
    c = sub1(c, r'^SoundFiles:\n- .*\n', lambda m: 'SoundFiles:\n- %s\n' % CHARGED_FILE)
    rec('SoundDescriptors', 'ZP_ArgentVerdictChargedSD', '000858', c)
    sc = sub1(gl_remap(sb), r'^FormKey: .*$', 'FormKey: 000859:' + ME)
    sc = sub1(sc, r'^EditorID: .*$', 'EditorID: ZP_ArgentVerdictChargedSound')
    sc = sub1(sc, r'^SoundDescriptor: .*$', 'SoundDescriptor: 000858:' + ME)
    rec('SoundMarkers', 'ZP_ArgentVerdictChargedSound', '000859', sc)


def main():
    check_winners()
    bounds = mesh_facts(MODEL, 'ZP_ArgentGauntlet')
    for sub in ('Weapons', 'Statics', 'TextureSets', 'ObjectEffects', 'MagicEffects', 'ConstructibleObjects',   # TextureSets: the retired 802
                'Projectiles', 'Explosions', 'Lights', 'SoundDescriptors', 'ImpactDataSets', 'Impacts', 'EffectShaders',
                'Spells', 'Activators', 'SoundMarkers', 'Globals', 'ArtObjects', 'FormLists', 'Cells'):   # ArtObjects, FormLists: retired
        shutil.rmtree(os.path.join(OUT, sub), ignore_errors=True)

    # 800 the hammer
    w = one(os.path.join(EGO, 'Weapons'), '07C993_Skyrim.esm')
    assert re.search(r'^  Damage: 42$', w, re.M) and 'Speed: 0.6\n' in w and re.search(r'^Critical:\n  Damage: 21$', w, re.M)
    w = sub1(w, r'^FormKey: .*$', 'FormKey: 000800:' + ME)
    w = sub1(w, r'^EditorID: .*$', 'EditorID: ZP_ArgentVerdict')
    assert 'VirtualMachineAdapter' not in w
    w = sub1(w, r'^(EditorID: ZP_ArgentVerdict\n)', lambda m: m.group(1) + '\n'.join([   # equipped: the motes show
        'VirtualMachineAdapter:', '  Scripts:', '  - Name: ZP_ArgentVerdictEquipScript', '    Properties:',
        '    - MutagenObjectType: ScriptObjectProperty', '      Name: Hammer', '      Object: 000800:' + ME,
        '    - MutagenObjectType: ScriptObjectProperty', '      Name: MoteAbility', '      Object: 000854:' + ME,
        '    - MutagenObjectType: ScriptObjectProperty', '      Name: PlayerRef', '      Object: 000014:Skyrim.esm', '']))
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

    # 801 its first-person static
    st = one(os.path.join(BASE, 'Skyrim', 'Statics'), '036BD2_Skyrim.esm')
    assert 'File: ' + PRETTY_1P in st
    st = sub1(st, r'^FormKey: .*$', 'FormKey: 000801:' + ME)
    st = sub1(st, r'^EditorID: .*$', 'EditorID: 1stPersonZP_ArgentVerdict')
    st = sub1(st, r'^Model:\n  File: .*\n  Data: .*\n', lambda m: 'Model:\n  File: %s\n' % MODEL)
    rec('Statics', '1stPersonZP_ArgentVerdict', '000801', st)

    # 803 the enchantment: a charge on every light-attack hit on a hostile actor until HITS, then the release on a
    # power attack with MANA_COST Mana
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
        '- BaseEffect: 000851:' + ME,                                   # a charge, until the knuckles are full
        '  Data: {}',
        '  Conditions:',
        '  - MutagenObjectType: ConditionFloat',
        '    Data:',
        '      MutagenObjectType: IsHostileToActorConditionData',
        '      TargetNpc: 000014:Skyrim.esm',
        '    ComparisonValue: 1',
        '  - MutagenObjectType: ConditionFloat',                         # light attacks only
        '    Data:',
        '      MutagenObjectType: IsPowerAttackingConditionData',
        '      RunOnType: Reference',
        '      Reference: 000014:Skyrim.esm',
        '  - MutagenObjectType: ConditionFloat',
        '    CompareOperator: LessThan',
        '    Data:',
        '      MutagenObjectType: GetGlobalValueConditionData',
        '      Global: 000852:' + ME,
        '    ComparisonValue: %d' % HITS,
        '- BaseEffect: 000804:' + ME,                                   # full: a power attack releases them
        '  Data: {}',
        '  Conditions:',
        '  - MutagenObjectType: ConditionFloat',
        '    Data:',
        '      MutagenObjectType: IsHostileToActorConditionData',
        '      TargetNpc: 000014:Skyrim.esm',
        '    ComparisonValue: 1',
        '  - MutagenObjectType: ConditionFloat',
        '    Data:',
        '      MutagenObjectType: IsPowerAttackingConditionData',
        '      RunOnType: Reference',
        '      Reference: 000014:Skyrim.esm',
        '    ComparisonValue: 1',
        '  - MutagenObjectType: ConditionFloat',
        '    CompareOperator: GreaterThanOrEqualTo',
        '    Data:',
        '      MutagenObjectType: GetGlobalValueConditionData',
        '      Global: 000852:' + ME,
        '    ComparisonValue: %d' % HITS,
        '  - MutagenObjectType: ConditionFloat',                         # the Mana it spends
        '    CompareOperator: GreaterThanOrEqualTo',
        '    Data:',
        '      MutagenObjectType: GetActorValueConditionData',
        '      RunOnType: Reference',
        '      Reference: 000014:Skyrim.esm',
        '      ActorValue: Magicka',
        '    ComparisonValue: %d' % MANA_COST]))

    # 804 the Smite: Prophecy's Smite effect A67's shape (instant script effect on the struck target) running
    # ZP_ArgentVerdictSmiteScript, with a description on the item card
    e = one(os.path.join(PROPHECY, 'MagicEffects'), '000A67_' + PROPHECY_ESP)
    assert 'Name: ZP_HolyPlaceExplosion' in e and 'Object: 000A54:' + PROPHECY_ESP in e and '- HideInUI\n' in e
    e = sub1(e, r'^FormKey: .*$', 'FormKey: 000804:' + ME)
    e = sub1(e, r'^EditorID: .*$', 'EditorID: ZP_ArgentVerdictSmiteEffect')
    e = sub1(e, r'^VirtualMachineAdapter:\n(?:  .*\n)+', '\n'.join([
        'VirtualMachineAdapter:', '  Scripts:', '  - Name: ZP_ArgentVerdictSmiteScript', '    Properties:',
        '    - MutagenObjectType: ScriptObjectProperty', '      Name: BeamBase', '      Object: 000856:' + ME,
        '    - MutagenObjectType: ScriptObjectProperty', '      Name: BellSound', '      Object: 000850:' + ME,
        '    - MutagenObjectType: ScriptObjectProperty', '      Name: Charges', '      Object: 000852:' + ME,
        '    - MutagenObjectType: ScriptObjectProperty', '      Name: Impact', '      Object: 000857:' + ME,
        '    - MutagenObjectType: ScriptObjectProperty', '      Name: PlayerRef', '      Object: 000014:Skyrim.esm',
        '    - MutagenObjectType: ScriptObjectProperty', '      Name: Strike', '      Object: 000847:' + ME, '']))
    e = english(e, 'Name', SMITE_NAME)
    e = sub1(e, r'^- HideInUI\n', '')
    e = sub1(e, r'^- NoMagnitude\n- NoArea\n- NoDuration\n', '- NoDuration\n- NoMagnitude\n- NoArea\n')   # flag-bit order
    e = english(e, 'Description', SMITE_TEXT)
    rec('MagicEffects', 'ZP_ArgentVerdictSmiteEffect', '000804', e)

    # 851 a charge: the same shape, ZP_ArgentVerdictChargeScript, hidden (804 carries the item card's text)
    c = sub1(e, r'^FormKey: .*$', 'FormKey: 000851:' + ME)
    c = sub1(c, r'^EditorID: .*$', 'EditorID: ZP_ArgentVerdictChargeMGEF')
    c = sub1(c, r'^VirtualMachineAdapter:\n(?:  .*\n)+', '\n'.join([
        'VirtualMachineAdapter:', '  Scripts:', '  - Name: ZP_ArgentVerdictChargeScript', '    Properties:',
        '    - MutagenObjectType: ScriptObjectProperty', '      Name: ChargedSound', '      Object: 000859:' + ME,
        '    - MutagenObjectType: ScriptObjectProperty', '      Name: Charges', '      Object: 000852:' + ME,
        '    - MutagenObjectType: ScriptObjectProperty', '      Name: MoteAbility', '      Object: 000854:' + ME,
        '    - MutagenObjectType: ScriptObjectProperty', '      Name: PlayerRef', '      Object: 000014:Skyrim.esm',
        '    - MutagenObjectType: ScriptObjectProperty', '      Name: TimeScale', '      Object: 00003A:Skyrim.esm', '']))
    c = english(c, 'Name', 'Argent Charge')
    c = sub1(c, r'^- Painless\n', '- HideInUI\n- Painless\n')
    c = english(c, 'Description', "''")
    rec('MagicEffects', 'ZP_ArgentVerdictChargeMGEF', '000851', c)
    # 852 the charges
    rec('Globals', 'ZP_ArgentVerdictCharges', '000852', '\n'.join([
        'MutagenObjectType: GlobalShort', 'FormKey: 000852:' + ME, 'EditorID: ZP_ArgentVerdictCharges', 'Data: 0']))
    # 853 the motes' display (Prophecy's constant script effect AD6's shape), 854 the ability carrying it
    m = one(os.path.join(PROPHECY, 'MagicEffects'), '000AD6_' + PROPHECY_ESP)
    assert 'CastType: ConstantEffect' in m and 'Type: Script' in m and '- HideInUI\n' in m
    m = sub1(m, r'^FormKey: .*$', 'FormKey: 000853:' + ME)
    m = sub1(m, r'^EditorID: .*$', 'EditorID: ZP_ArgentVerdictMotesMGEF')
    m = sub1(m, r'^VirtualMachineAdapter:\n(?:  .*\n)+', '\n'.join([
        'VirtualMachineAdapter:', '  Scripts:', '  - Name: ZP_ArgentVerdictMotesScript', '    Properties:',
        '    - MutagenObjectType: ScriptObjectProperty', '      Name: Charges', '      Object: 000852:' + ME, '']))
    m = english(m, 'Name', 'Argent Charge')
    m = sub1(m, r'^Flags:\n(?:- .*\n)+', 'Flags:\n- NoDuration\n- NoMagnitude\n- NoArea\n- HideInUI\n- Painless\n')  # bit order
    m = drop(m, r'^CastType: ConstantEffect\n')                     # the defaults (Spriggit leaves them out)
    m = drop(m, r'^TargetType: Self\n')
    if PROPHECY_ESP in m:
        sys.exit('a Prophecy reference left in 853: ' + re.search(r'\S+:' + re.escape(PROPHECY_ESP), m).group(0))
    rec('MagicEffects', 'ZP_ArgentVerdictMotesMGEF', '000853', m)
    rec('Spells', 'ZP_ArgentVerdictMotes', '000854', '\n'.join([
        'FormKey: 000854:' + ME, 'EditorID: ZP_ArgentVerdictMotes',
        'Name:', '  TargetLanguage: English', '  Value: Argent Charge',
        'EquipmentType: 013F44:Skyrim.esm',
        'Description:', '  TargetLanguage: English', "  Value: ''",
        'Flags:', '- ManualCostCalc', '- IgnoreResistance', '- NoAbsorbOrReflect',
        'Type: Ability',                                              # CastType: ConstantEffect, the default
        'Effects:', '- BaseEffect: 000853:' + ME, '  Data: {}']))

    smite()

    # 805 its grindstone temper (Aeterna material; enchanted, so Enderal's Arcane Blacksmith rule applies)
    c = one(os.path.join(BASE, 'Skyrim', 'ConstructibleObjects'), '148AB7_Skyrim.esm')
    c = sub1(c, r'^FormKey: .*$', 'FormKey: 000805:' + ME)
    c = sub1(c, r'^EditorID: .*$', 'EditorID: ZP_TemperArgentVerdict')
    c = sub1(c, r'^CreatedObject: .*$', 'CreatedObject: 000800:' + ME)
    rec('ConstructibleObjects', 'ZP_TemperArgentVerdict', '000805', c)
    place_record()
    print('records written to', OUT)


def place_record():
    """861 REFR: the hammer on the Malphas statue's socket in the Destroyed Abbey's Halls (see PLACE)."""
    sys.path.insert(0, os.path.join(ROOT, 'src', 'StingAndRise', 'tools'))
    import surface
    sr = _module('sr_assets', os.path.join(ROOT, 'src', 'StingAndRise', 'tools', '01-build-assets.py'))
    th = PLACE['socket_rot']
    files, spot = surface.place_unique(sr, PLACE['cell'], PLACE['header'], PLACE['surface'], PLACE['top'], MODEL,
                                       '000800:' + ME, '000861:' + ME, [th + math.pi / 2, th - math.pi / 2],
                                       blockers=[(PLACE['statue'], None)], prefer=PLACE['prefer'], cell_size=2.0)
    for rel, text in files.items():
        path = os.path.join(OUT, *rel.split('/'))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
    print('  Argent Verdict placed at %s, heading %.3f, on the socket (z %.2f), %.1f from the preferred spot' % (
        tuple(round(v, 2) for v in spot['position']), spot['heading'], spot['top'], spot['distance']))


if __name__ == '__main__':
    main()
