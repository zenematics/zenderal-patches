"""Generate Sting and Rise's records: two unique daggers on Pretty Enderal Armory's models.

Every copied record is its live winner verbatim with only the listed fields changed (00-scan-overriders.py
lists the winners; this script refuses to run if one changed hands).

  800 WEAP ZP_Sting            <- Yero's Last Words 13C2AF (EGO's record: Enderal's unique dagger, 20 damage,
           crit 15, WeapTypeUnique); Name, Model = Pretty's assassin blade (Blood Needle's model, irondagger2.nif)
           with Blood Needle's bounds and first-person static 14483F, ObjectEffect 801, Value
  801 ENCH ZP_StingVenom       weapon enchantment (Touch), 802 for STING_DPS a second, EFFECT_SECONDS
  802 MGEF ZP_StingVenomEffect <- EGO's weapon poison EnchPoisonNoShader 001F73 (Zenderal - No Screen Flashes'
           copy: poison resist, EGO's poison + weapon-enchant keywords, the green chaurus-poison hit shader);
           no PowerAffectsDuration (always EFFECT_SECONDS), no "target lacks it" condition (a new hit refreshes the
           6 seconds), no DispelWithKeywords (it would dispel Rise's burn, which shares XionWeaponEnch),
           EnchantArt 803
  803 ARTO ZP_StingVenomCoatFX <- ChillrendEnchFX 10A045, model = tools/01's poison coat
  804 WEAP ZP_Rise             <- Yero's Last Words 13C2AF like Sting; Model = Pretty's Aeterna dagger
           (1stPersonElvenDagger.nif) with bounds measured from it and its blade shape's texture set swapped for
           80C (alternate textures), first-person static 80D, ObjectEffect 805, + keyword 808, script
           ZP_RiseArmorPierceScript (gives the player perk 809 on first equip)
  805 ENCH ZP_RiseFlame        weapon enchantment (Touch), 806 for RISE_DPS a second, EFFECT_SECONDS
  806 MGEF ZP_RiseBurnEffect   <- Enderal's Burning _00E_A1_FireArrowEnchME 067252 (Flame Shot's copy: the Fire
           Arrow talent's 6-second fire damage over time); no NoRecast (a new hit refreshes the burn), the fire
           hit shader every fire damage effect uses (FireFXShader 01B212: the target is seen burning),
           EGO's XionWeaponEnch keyword (like Sting's: EGO's spell-damage perk skips weapon enchantments),
           EnchantArt 807
  807 ARTO ZP_RiseFlameFX      <- ChillrendEnchFX 10A045, model = tools/01's flames
  808 KYWD ZP_RiseKeyword      on Rise only: the perk's weapon condition
  809 PERK ZP_RiseArmorPierce  Mod Target Damage Resistance x0 (the engine's "ignore armor", as Enderal's Bone
           Breaker / EGO's mace bonus at x0.65), weapon has 808, target has 802 (Sting's venom)
  80A COBJ ZP_TemperSting      <- Yero's Last Words' temper 02A26E, new product
  80B COBJ ZP_TemperRise       <- same
  80C TXST ZP_RiseGold         <- Nettlebane's 0777C3 (the vanilla unique dagger that is the ebony dagger mesh + a
           texture set): tools/01's gold diffuse, env mask and gold cubemap, Pretty's own normal map
  80D STAT 1stPersonZP_Rise    <- 1stPersonElvenDagger 036BD0 + the same swap (a WEAP's first-person model is
           its STAT, so the swap goes on both, as Nettlebane's 1st-person STAT carries it)
  80E MGEF ZP_BloodBoilTrigger <- Prophecy's relay shape (ZP_Prophecy_BleedingShot_Relay B4A: script, Touch,
           hidden, painless), script ZP_BloodBoilEffect. Second effect of BOTH enchantments, conditioned on the
           struck target carrying the OTHER dagger's damage over time and no 812: the blood boil
  80F SPEL ZP_BloodBoilBlast   <- Prophecy's A Willing Sacrifice blast 99D: hostile, TargetActor, remote-cast by the
           script on the target and every enemy around it, blamed on the wielder; 810 for BOIL_DAMAGE
  810 MGEF ZP_BloodBoilBlastEffect     <- Willing Sacrifice's 99E: damage Health, EGO's XionWeaponEnch keyword
  811 SPEL ZP_BloodBoilCooldown        <- Willing Sacrifice's cooldown 9A0, cast on the target: 812, BOIL_COOLDOWN
  812 MGEF ZP_BloodBoilCooldownEffect  <- Willing Sacrifice's 9A1: a marker (script archetype, no script), hidden
  813 EFSH ZP_EnchantArtCarrierFXS <- Chillrend's FrostChillrendFXShader 10A043 with every colour, alpha and its sound
           taken out: draws nothing. The EnchantShader of 802 and 806. The first build had no EnchantShader and the
           curator saw neither the coat nor the flames (2026-11-13); every enchant art that shows in the game pairs it
           with one (Chillrend's art 10A045 with this very shader on Enderal's Druid affinity 02F1A1, the bound
           weapons, Elemental Fury, Kittytails' Aero), so the art rides on a shader that shows nothing of its own
  814 EXPL ZP_BloodBoilBurst   <- FS's gore burst _00E_FS_MAGGoreExplosion 06A18E (Father's Legacy's exploding
           enemies): model = tools/01's BloodBoilBurst.nif (its blood drops and streams, no meat), no Force (pushes
           nothing), Radius 512 -> BOIL_DECAL_RADIUS and the blood-spray impact set 01F82A, so it also leaves blood
           decals around the target (vanilla BloodDecalPlaceExplosion 0F3A8C's way); its own FS sound kept. Placed
           by the script at the struck target (curator 2026-11-13: "a blood splatter effect that pops", replacing
           FS's ground splash 02F27F and Apocalypse's Blood Boil shader, which read as red flames)
  815 EFSH ZP_BloodBoilSplatterFXS  <- Enderal's _00E_BloodyFXShader 144758 (the blood-splatter decal texture over
           the body), fading in in BOIL_SPLATTER_FADE_IN s instead of 1: played by the script on everyone the boil hurts
  816 TXST ZP_RiseScabbardGold <- 80C's shape for the scabbard (Pretty's `scb` shape, index 1): tools/01's scabbard
           gold (its metal fittings; the leather wrap kept, like the blade's grip), Pretty's sheath_n.dds (curator)
  818 STAT 1stPersonZP_Sting   <- Blood Needle's 1st-person static 14483F on Sting's own mesh (tools/01: Pretty's assassin
           blade + the metal spider on its pommel; curator: always visible, so this copy of Pretty's mesh ships);
           Sting's WEAP 800 uses that mesh too
  817 MGEF ZP_StingSlowEffect  <-Enderal's Shadowtongue Oil slow 0F8641 (SpeedMult, Peak Value Modifier): Sting's
           enchantment slows by STING_SLOW% for EFFECT_SECONDS (curator); hidden, named in the venom's text

Usage:  python src/StingAndRise/tools/02-build-records.py
"""
import importlib.util
import json
import math
import os
import re
import shutil
import sys

import struct

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
EGO = os.path.join(ROOT, 'reference', 'mods', 'EGO')
BASE = os.path.join(ROOT, 'reference', 'base')
NSF = os.path.join(ROOT, 'src', 'NoScreenFlashes', 'NoScreenFlashesESP')
FLAMESHOT = os.path.join(ROOT, 'src', 'FlameShot', 'FlameShotESP')
OUT = os.path.join(ROOT, 'src', 'StingAndRise', 'StingAndRiseESP')
ME = 'Zenderal - Sting and Rise.esp'
EGO_ESP = 'Enderal SE - Gameplay Overhaul.esp'

EFFECT_SECONDS = 6      # curator: each dagger's damage over time lasts 6 seconds
STING_DPS = 5           # poison damage a second (30 over the 6 s)
STING_SLOW = 10         # curator: Sting's hits slow enemies by 10% (for EFFECT_SECONDS, like the venom)
SILVER = '10AA1A:Skyrim.esm'   # WeapMaterialSilver, on Rise (curator): EGO's silver perks (x2.15 vs undead; ghosts
                               # take full damage) and Prophecy's Smite key on it, as on the Relentless Sword
RISE_DPS = 5            # fire damage a second: Enderal's own Burning (the Fire Arrow talent) is 5 for 6 s
VALUE = 1000
CHARGE = 3000           # NoAutoCalc, cost 1 a hit: never runs dry in practice; soul gems still recharge it
BOIL_DAMAGE = 40        # curator: a strike with one dagger on a target carrying the other's damage over time
BOIL_COOLDOWN = 6       # boils its blood; then not again on that target for this long (dual wielding the pair
                        # would otherwise boil every other hit)
BOIL_RADIUS = 250       # ZP_BloodBoilEffect's Radius (AutoReadOnly there; blood_boil() checks the two agree)
BOIL_BURST_MODEL = r'Zenderal\StingAndRise\BloodBoilBurst.nif'   # tools/01
BOIL_DECAL_RADIUS = 128   # blood decals land this far round the target (BloodDecalPlaceExplosion's is 92)
BOIL_SPLATTER_FADE_IN = 0.1   # s; Enderal's bloody shader takes 1 s to show, which is no pop
BOIL_TEXT = ('boil its blood, %d damage to it and every enemy around it, once every %d seconds a target'
             % (BOIL_DAMAGE, BOIL_COOLDOWN))   # no ': ' (plain YAML scalar)

STING_MODEL = r'Enderal\weapons\Iron\irondagger2.nif'          # Pretty's assassin blade
RISE_MODEL = r'Weapons\Elven\1stPersonElvenDagger.nif'          # Pretty's Aeterna dagger
STING_ART = r'Zenderal\StingAndRise\StingEnchFX.nif'
STING_OWN_MODEL = r'Zenderal\StingAndRise\Sting.nif'   # tools/01: Pretty's assassin blade + the pommel spider
RISE_OWN_MODEL = r'Zenderal\StingAndRise\Rise.nif'     # tools/01: Pretty's Aeterna dagger + the angel and wings
OWN_SOURCE = 'Zenderal - Patch Collection'              # where tools/01 writes it
RISE_ART = r'Zenderal\StingAndRise\RiseEnchFX.nif'
GOLD_D = r'Zenderal\StingAndRise\RiseGold_d.dds'      # tools/01's gold textures (TXST paths are under textures\)
GOLD_M = r'Zenderal\StingAndRise\RiseGold_m.dds'
GOLD_E = r'Zenderal\StingAndRise\RiseGold_e.dds'
SCB_D = r'Zenderal\StingAndRise\RiseScabbardGold_d.dds'   # tools/01's scabbard gold
SCB_M = r'Zenderal\StingAndRise\RiseScabbardGold_m.dds'
GOLD_N = r'Zenderal\StingAndRise\RiseGold_n.dds'           # tools/01: Pretty's normals, metal highlights raised
SCB_N = r'Zenderal\StingAndRise\RiseScabbardGold_n.dds'

EXPECTED_WINNERS = {
    '13C2AF:Skyrim.esm': EGO_ESP,
    '02A26E:Enderal - Forgotten Stories.esm': 'Enderal - Forgotten Stories.esm',
    '015AA7:Skyrim.esm': EGO_ESP,
    '14483F:Skyrim.esm': 'Skyrim.esm',
    '07C98E:Skyrim.esm': EGO_ESP,
    '036BD0:Skyrim.esm': 'Skyrim.esm',
    '001F73:%s' % EGO_ESP: 'Zenderal - No Screen Flashes.esp',
    '067252:Skyrim.esm': 'Zenderal - Flame Shot.esp',
    '10A045:Skyrim.esm': 'Skyrim.esm',
    '0777C3:Skyrim.esm': 'Skyrim.esm',
    '06A18E:Skyrim.esm': 'Enderal - Forgotten Stories.esm',     # FS's gore burst (copied)
    '144758:Skyrim.esm': 'Skyrim.esm',                          # _00E_BloodyFXShader (copied)
    '01F82A:Skyrim.esm': 'Skyrim.esm',                          # BloodSprayImpactSetRed (referenced)
    '02E28E:Enderal - Forgotten Stories.esm': 'Enderal - Forgotten Stories.esm',   # the burst's sound (referenced)
    '10A043:Skyrim.esm': 'Skyrim.esm',
    '01CB69:Skyrim.esm': EGO_ESP,                               # young Moss Crawler (copied)
    '01EA6D:Skyrim.esm': EGO_ESP,                               # Mage Light (EGO's copied)
    '03FA58:Skyrim.esm': 'Skyrim.esm',
    '041F06:Skyrim.esm': 'Skyrim.esm',
    '143325:Skyrim.esm': 'Zenderal - Flame Shot.esp',           # Enderal's Wayfarer fire nova (Flame Shot's, copied)
    '046008:Skyrim.esm': 'Skyrim.esm',
    '02E1CD:Skyrim.esm': 'Skyrim.esm',                          # WebbedFXS (copied)
    '0F8641:Skyrim.esm': 'Skyrim.esm',                          # Shadowtongue Oil's slow (copied)
}
CARRIER = '000813'      # the invisible enchant shader the enchant art needs (see 813 above)
# The on-hit rework (curator 2026-11-13). Sting: an enemy that dies poisoned bursts into a spiderling that fights for
# SPIDER_LIFE s and bursts in venom when it dies; enemies that venom kills burst too. Rise: undead it strikes are marked
# with a mote of sunlight; a marked enemy that dies bursts in a weak fire nova (curator, same evening: "instead of the
# Dawnbreaker effect"), marking the undead around it; since 2026-11-15 only a successful Turn Undead on a marked undead
# sets the nova off (curator: "remove the on kill Fire Nova, keep the Turn undead fire nova"). Blood Boil and Rise's armor bonus stay, as hidden effects (out
# of the descriptions).
SPIDER_LIFE = 30            # s, curator (15 until 2026-11-14); ZP_StingSpiderlingEffect's LifeSeconds (AutoReadOnly)
SPIDER_SPEED = 200          # SpeedMult (100 = the race's own): curator 2026-11-14, "twice as fast"; the script's SpeedMult
SPIDER_HEIGHT = 0.5         # the young Moss Crawler is 0.49 (x its race's 0.75). 0.30 until 2026-11-14: a bite reach
                            # of ~22 units (race unarmed reach 96 x scale), so the spiderlings barely ever bit
BITE_DAMAGE = 15            # the spiderling's assisted bite (Venom Bite 82F/830), poison; the script lands it on a
BITE_REACH = 110            # hit frame the game's own check missed, target within this (its BiteReach)
SPIDER_BURST_DAMAGE = 25    # the venom burst, to every enemy within SPIDER_BURST_RADIUS
SPIDER_BURST_RADIUS = 200   # ZP_StingSpiderlingEffect's Radius (AutoReadOnly there; rework() checks all three)
MOTE_SECONDS = 30           # a mote lasts this long unless its bearer dies first
NOVA_DAMAGE = 25            # the fire nova's fire damage at level 0, to every enemy within NOVA_RADIUS ...
NOVA_PER_LEVEL = 2.5        # ... + this per player level, set on 826 by ZP_RiseMoteEffect before each nova (SKSE);
                            # curator: the first 20 flat "doesn't seem to do much" (EGO's difficulty multipliers are 1)
NOVA_RADIUS = 300           # ZP_RiseMoteEffect's Radius; tools/01 scales the nova's ring to it
MOTE_LIGHT_COLOR = "'#00FFC060'"   # the mote's light: warm sun gold (Mage Light's is pale blue #0081AFE2)
MOTE_LIGHT_RADIUS = 320
UNDEAD = '013796:Skyrim.esm'       # ActorTypeUndead
NOVA_SOURCE = '_00E_A1_FireArrowWayfarerExp - 143325_Skyrim.esm.yaml'   # Enderal's own fire nova: Fire Arrow's
                                   # Wayfarer burst, vanilla Fire Storm's ring of flame at radius 256
NOVA_MODEL = r'Zenderal\StingAndRise\RiseNova.nif'                     # tools/01: that ring scaled to NOVA_RADIUS
SPIT_IMPACTS = '046008:Skyrim.esm' # MAGSpiderSpitImpactSet: the spider spit's splats
WEB_SECONDS = 6             # curator: "takes them 3 seconds to break free"; 6 since 2026-11-15 ("extend ... to 6")
WEB_FREE_SECONDS = 3        # then free of webs this long (a spiderling bites often)
WEB_MODEL = r'Zenderal\StingAndRise\StingWebStrands.nif'   # tools/01: vanilla web strands, scaled to an actor's legs
WEB_SHADER = {              # vanilla WebbedFXS 02E1CD, quick in and out (its fill fades out over 100 s); curator: the
    'FillAlphaFadeInTime': 0.2, 'FillFullAlphaTime': 0.3, 'FillFadeOutTime': 0.6,     # first look "never appeared
    'FillPersistentAlphaRatio': 1, 'FillFullAlphaRatio': 1,                            # noticeably": opaque white
    'FillColorKey1': "'#00F4F4F0'", 'FillColorKey2': "'#00F4F4F0'", 'FillColorKey3': "'#00F4F4F0'"}  # (was pale teal)
STING_TEXT = ('Deals <mag> poison damage per second and slows the target by %d%% for <dur> seconds. An enemy that '
              'dies poisoned bursts into a spiderling that fights at your side for %d seconds and bursts in venom when '
              'it dies, and enemies its venom kills burst too.' % (STING_SLOW, SPIDER_LIFE))
RISE_TEXT = ('Sets the target ablaze for <dur> seconds, <mag> fire damage per second. Undead it strikes are marked with '
             'a mote of sunlight. A marked undead that is turned bursts in a fire nova that deals %d fire damage, '
             'plus %g per level, to it and to the enemies around it, marking the undead among them.'
             % (NOVA_DAMAGE, NOVA_PER_LEVEL))   # turned: ZP_RiseMoteEffect; the on-death nova went 2026-11-15 (curator)
RISE_NAME = 'Sunrise'       # curator 2026-11-15 (was Rise; EditorIDs, files and the plugin keep "Rise")
SPIDER_BURST_MODEL = r'Zenderal\StingAndRise\StingSpiderBurst.nif'    # tools/01
MOTE_MODEL = r'Zenderal\StingAndRise\RiseMote.nif'                    # tools/01
PROPHECY = os.path.join(ROOT, 'src', 'Prophecy', 'ProphecyESP')
PROPHECY_ESP = 'Zenderal - Prophecy.esp'
SCRIPT = os.path.join(ROOT, 'src', 'StingAndRise', 'Scripts', 'source', 'ZP_BloodBoilEffect.psc')


def read(path):
    with open(path, encoding='utf-8-sig', newline='') as f:
        return f.read().replace('\r\n', '\n')


def one(folder, stem):
    hits = [f for f in os.listdir(folder) if stem in f]
    if len(hits) != 1:
        sys.exit('%s: expected one *%s*, found %s' % (folder, stem, hits))
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


def english(text, field, value):
    """A localized field (Values list) or a plain one -> the plain English form (the plugin is not localized)."""
    out, n = re.subn(r'^%s:\n  TargetLanguage: English\n(?:  Value: .*\n|  Values:\n(?:  - .*\n(?:    .*\n)?)+)' % field,
                     '%s:\n  TargetLanguage: English\n  Value: %s\n' % (field, value), text, count=1, flags=re.M)
    if n != 1:
        sys.exit('no %s field' % field)
    return out


def mesh_bounds(model, source=None):
    """ObjectBounds of the WINNING mesh (Pretty's), every shape: floor of the minimum, ceiling of the maximum.
    Yero's bounds fit Qalian's dagger, Blood Needle's are not Pretty's blade, and the Aeterna dagger has none."""
    assets = _assets()
    rel = 'meshes/' + model.replace(chr(92), '/')
    src, nif = assets.load(os.path.join(assets.MO2, 'mods'), assets.profile_mods(), rel)
    if src != (source or assets.EXPECT_SOURCE):
        sys.exit('%s now comes from %s, not %s' % (rel, src, source or assets.EXPECT_SOURCE))
    pts = []
    for k in nif.find('BSTriShape'):
        s = assets.nifse.read_trishape(nif.blocks[k])
        t, R, sc = assets.nifse.transform(nif.blocks[k])
        pts.append(s['pos'] * sc @ R.T + t)
    P = np.concatenate(pts)
    lo = [int(math.floor(v)) for v in P.min(0)]
    hi = [int(math.ceil(v)) for v in P.max(0)]
    return 'ObjectBounds:\n  First: %d, %d, %d\n  Second: %d, %d, %d\n' % (*lo, *hi)


def _assets():
    spec = importlib.util.spec_from_file_location('assets', os.path.join(HERE, '01-build-assets.py'))
    assets = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(assets)
    return assets


def swap_targets(model, source=None):
    """{'blade': ..., 'scb': ...}, each (shape name, alternate-texture index, normal map), in the WINNING mesh. The
    index is the shape's place among the mesh's geometry in depth-first order: vanilla Nettlebane's 1st-person STAT
    swaps `1stPersonEbonyDagger:0` at index 3, its fourth shape in that order (after Scb and two blood edges)."""
    assets = _assets()
    rel = 'meshes/' + model.replace(chr(92), '/')
    src, nif = assets.load(os.path.join(assets.MO2, 'mods'), assets.profile_mods(), rel)
    if src != (source or assets.EXPECT_SOURCE):
        sys.exit('%s now comes from %s, not %s' % (rel, src, source or assets.EXPECT_SOURCE))
    order = []

    def walk(k):
        t = nif.btype(k)
        if t in ('BSTriShape', 'NiTriShape', 'BSDynamicTriShape', 'NiParticleSystem'):
            order.append(k)
        elif t in ('BSFadeNode', 'NiNode', 'NiBillboardNode', 'BSLeafAnimNode', 'BSValueNode'):
            for c in assets.nifse.node_children(nif.blocks[k])[1]:
                if c >= 0:
                    walk(c)
    walk(nif.roots[0])

    def target(k):
        s = assets.nifse.read_trishape(nif.blocks[k])
        tex_i = struct.unpack_from('<i', nif.blocks[s['shader']], assets.nifse.LSP_TEXSET)[0]
        b = nif.blocks[tex_i]
        p = 4
        paths = []
        for _ in range(struct.unpack_from('<I', b, 0)[0]):
            m = struct.unpack_from('<I', b, p)[0]
            paths.append(b[p + 4:p + 4 + m].decode('latin1'))
            p += 4 + m
        normal = paths[1]
        assert normal.lower().startswith('textures' + chr(92)), normal
        return assets.name_of(nif, k), order.index(k), normal[len('textures') + 1:], paths[0].lower()

    bl = target(assets.blade(nif)['block'])
    scb = [k for k in order if nif.btype(k) == 'BSTriShape' and assets.name_of(nif, k).lower() == 'scb']
    assert len(scb) == 1, 'no single scb shape'
    sc = target(scb[0])
    assert sc[3].endswith(chr(92) + 'sheath.dds'), sc        # tools/01 golds Pretty's sheath.dds for it
    return {'blade': bl[:3], 'scb': sc[:3]}


def alternate_textures(entries):
    """Model alternate textures: (shape, index, texture set) per swapped shape."""
    lines = ['  AlternateTextures:']
    for shape, index, txst in entries:
        lines += ['  - Name: ' + shape, '    NewTexture: %s:%s' % (txst, ME)]
        if index:
            lines.append('    Index: %d' % index)               # Spriggit writes no Index when it is 0
    return '\n'.join(lines + [''])


def gold_txst(formkey, editor_id, diffuse, normal, mask):
    """Nettlebane's texture set (0777C3) with tools/01's gold diffuse, normal map (Pretty's, its metal's highlight
    mask raised), plain env mask and gold chrome cubemap."""
    x = one(os.path.join(BASE, 'Skyrim', 'TextureSets'), '0777C3_Skyrim.esm')
    x = sub1(x, r'^FormKey: .*$', 'FormKey: %s:%s' % (formkey, ME))
    x = sub1(x, r'^EditorID: .*$', 'EditorID: ' + editor_id)
    x = sub1(x, r'^Diffuse: .*$', lambda m: 'Diffuse: ' + diffuse)          # lambdas: the paths hold backslashes
    x = sub1(x, r'^NormalOrGloss: .*$', lambda m: 'NormalOrGloss: ' + normal)
    x = sub1(x, r'^EnvironmentMaskOrSubsurfaceTint: .*$', lambda m: 'EnvironmentMaskOrSubsurfaceTint: ' + mask)
    x = sub1(x, r'^Environment: .*$', lambda m: 'Environment: ' + GOLD_E)
    rec('TextureSets', editor_id, formkey, x)


def slow_effect():
    """817: Enderal's Shadowtongue Oil slow (_00E_A1_ShadowtongueoilSlowME 0F8641, a weapon oil's: Peak Value
    Modifier on SpeedMult, Recover) without its script (it only resets the oil's global), hit shader or power
    scaling: Sting's hits slow by STING_SLOW percent for EFFECT_SECONDS."""
    s = one(os.path.join(BASE, 'Skyrim', 'MagicEffects'), '0F8641_Skyrim.esm')
    assert 'ActorValue: SpeedMult' in s and 'MagicEffectPeakValueModArchetype' in s and '- Recover' in s
    s = sub1(s, r'^FormKey: .*$', 'FormKey: 000817:' + ME)
    s = sub1(s, r'^EditorID: .*$', 'EditorID: ZP_StingSlowEffect')
    s = sub1(s, r'^VirtualMachineAdapter:\n(?:  .*\n)+', '')
    s = english(s, 'Name', 'Sting Venom')
    s = sub1(s, r'^- FXPersist\n', '')
    s = sub1(s, r'^- PowerAffectsMagnitude\n', '')
    s = sub1(s, r'^HitShader: .*\n', '')
    s = sub1(s, r'^Description:\n(?:  .*\n)*', "Description:\n  TargetLanguage: English\n  Value: ''\n")
    rec('MagicEffects', 'ZP_StingSlowEffect', '000817', s)


def dagger(formkey, editor_id, name, model, model_rec, first_person, ench, extra_keywords=(), script=None, alt=None,
           bounds_source=None):
    w = one(os.path.join(EGO, 'Weapons'), '13C2AF_Skyrim.esm')
    assert '_04E_30_Unique_YerosLastWords' in w
    w = sub1(w, r'^FormKey: .*$', 'FormKey: %s:%s' % (formkey, ME))
    w = sub1(w, r'^EditorID: .*$', 'EditorID: ' + editor_id)
    if script:
        w = sub1(w, r'^(EditorID: .*\n)', r'\g<1>' + script)
    w = sub1(w, r'^ObjectBounds:\n  First: .*\n  Second: .*\n', mesh_bounds(model, bounds_source))
    w = english(w, 'Name', name)
    w = sub1(w, r'^(Model:\n  File: ).*$', lambda m: m.group(1) + model)
    w = sub1(w, r'^(Model:\n  File: .*\n)  Data: .*\n', r'\g<1>')     # texture hashes belong to the old mesh
    if alt:
        w = sub1(w, r'^(Model:\n  File: .*\n)', lambda m: m.group(1) + alt)
    w = sub1(w, r'^ObjectEffect: .*$', 'ObjectEffect: %s:%s' % (ench, ME))
    w = sub1(w, r'^EnchantmentAmount: .*$', 'EnchantmentAmount: %d' % CHARGE)
    w = sub1(w, r'^FirstPersonModel: .*$', 'FirstPersonModel: ' + first_person)
    if extra_keywords:
        w = sub1(w, r'^(Keywords:\n(?:- .*\n)+)', lambda m: m.group(1) + ''.join('- %s\n' % k for k in extra_keywords))
    w = sub1(w, r'^(BasicStats:\n  Value: )\d+$', r'\g<1>%d' % VALUE)
    assert re.search(r'^  Damage: 20$', w, re.M) and re.search(r'^Critical:\n  Damage: 15$', w, re.M), 'Yero stats moved'
    rec('Weapons', editor_id, formkey, w)


def boil_trigger(other_dot):
    """The enchantment's second effect: the blood boil, only on a target that carries the other dagger's damage
    over time (other_dot) and no Blood Boil cooldown. Duration 1, a relay read once at the hit: the engine re-checks
    an active effect's conditions while it runs, and the cooldown the script casts would end it at once anyway."""
    return [
        '- BaseEffect: 00080E:' + ME,
        '  Data:',
        '    Duration: 1',
        '  Conditions:',
        '  - MutagenObjectType: ConditionFloat',
        '    Data:',
        '      MutagenObjectType: HasMagicEffectConditionData',
        '      MagicEffect: %s:%s' % (other_dot, ME),
        '    ComparisonValue: 1',
        '  - MutagenObjectType: ConditionFloat',               # == 0: no cooldown on the target
        '    Data:',
        '      MutagenObjectType: HasMagicEffectConditionData',
        '      MagicEffect: 000812:' + ME,
    ]


def enchantment(formkey, editor_id, name, effect, dps, extra=()):
    rec('ObjectEffects', editor_id, formkey, '\n'.join([
        'FormKey: %s:%s' % (formkey, ME),
        'EditorID: ' + editor_id,
        'Name:',
        '  TargetLanguage: English',
        '  Value: ' + name,
        'EnchantmentCost: 1',
        'Flags:',
        '- NoAutoCalc',
        'CastType: FireAndForget',
        'EnchantmentAmount: %d' % CHARGE,
        'TargetType: Touch',
        'EnchantType: Enchantment',
        'Effects:',
        '- BaseEffect: %s:%s' % (effect, ME),
        '  Data:',
        '    Magnitude: %d' % dps,
        '    Duration: %d' % EFFECT_SECONDS,
    ] + list(extra)))


def art(formkey, editor_id, model):
    a = one(os.path.join(BASE, 'Skyrim', 'ArtObjects'), '10A045_Skyrim.esm')
    a = sub1(a, r'^FormKey: .*$', 'FormKey: %s:%s' % (formkey, ME))
    a = sub1(a, r'^EditorID: .*$', 'EditorID: ' + editor_id)
    a = sub1(a, r'^(Model:\n  File: ).*$', lambda m: m.group(1) + model)
    a = sub1(a, r'^(Model:\n  File: .*\n)  Data: .*\n', r'\g<1>')
    rec('ArtObjects', editor_id, formkey, a)


def blood_burst():
    """814 + 815: Blood Boil's look, the pop at the target and the splatter on everyone it hurts."""
    x = read(os.path.join(BASE, 'EnderalFS', 'Explosions', '_00E_FS_MAGGoreExplosion - 06A18E_Skyrim.esm.yaml'))
    assert 'swordbloodexplosion.nif' in x and 'ObjectEffect' not in x and 'ImageSpaceModifier' not in x
    x = sub1(x, r'^FormKey: .*$', 'FormKey: 000814:' + ME)
    x = sub1(x, r'^EditorID: .*$', 'EditorID: ZP_BloodBoilBurst')
    x = sub1(x, r'^(Model:\n  File: ).*$', lambda m: m.group(1) + BOIL_BURST_MODEL)
    x = sub1(x, r'^(Model:\n  File: .*\n)  Data: .*\n', r'\g<1>')
    x = sub1(x, r'^(Sound1: .*\n)', r'\g<1>ImpactDataSet: 01F82A:Skyrim.esm\n')   # BloodSprayImpactSetRed: decals
    x = sub1(x, r'^Force: .*\n', '')                       # 240 threw loose items about; Spriggit omits 0
    x = sub1(x, r'^Radius: .*$', 'Radius: %d' % BOIL_DECAL_RADIUS)
    x = sub1(x, r'^ISRadius: .*\n', '')                    # it has no image-space modifier
    rec('Explosions', 'ZP_BloodBoilBurst', '000814', x)

    s = one(os.path.join(BASE, 'Skyrim', 'EffectShaders'), '144758_Skyrim.esm')
    assert 'EditorID: _00E_BloodyFXShader' in s and 'DecalsBloodSplatter01' in s
    s = sub1(s, r'^FormKey: .*$', 'FormKey: 000815:' + ME)
    s = sub1(s, r'^EditorID: .*$', 'EditorID: ZP_BloodBoilSplatterFXS')
    s = sub1(s, r'^FillAlphaFadeInTime: .*$', 'FillAlphaFadeInTime: %g' % BOIL_SPLATTER_FADE_IN)
    s = sub1(s, r'^EdgeEffectAlphaFadeInTime: .*$', 'EdgeEffectAlphaFadeInTime: %g' % BOIL_SPLATTER_FADE_IN)
    rec('EffectShaders', 'ZP_BloodBoilSplatterFXS', '000815', s)


def carrier_shader():
    """813: Chillrend's enchant shader with nothing left to draw or hear."""
    s = one(os.path.join(BASE, 'Skyrim', 'EffectShaders'), '10A043_Skyrim.esm')
    assert 'EditorID: FrostChillrendFXShader' in s and '- NoParticleShader' in s
    s = sub1(s, r'^FormKey: .*$', 'FormKey: %s:%s' % (CARRIER, ME))
    s = sub1(s, r'^EditorID: .*$', 'EditorID: ZP_EnchantArtCarrierFXS')
    for field in ('FillColorKey1', 'FillColorKey2', 'FillColorKey3', 'EdgeEffectColor', 'EdgeColor'):
        s = sub1(s, r"^%s: .*$" % field, "%s: '#00000000'" % field)
    # the membrane's alpha: Spriggit writes no float that is 0, so the lines go
    for field in ('FillPersistentAlphaRatio', 'FillFullAlphaRatio', 'EdgeEffectPersistentAlphaRatio',
                  'EdgeEffectFullAlphaRatio', 'ColorKey2Alpha', 'ParticleFullBirthRatio', 'ParticlePeristentCount'):
        s = sub1(s, r'^%s: .*\n' % field, '')
    s = sub1(s, r'^AmbientSound: .*\n', '')          # Chillrend's frost hum
    rec('EffectShaders', 'ZP_EnchantArtCarrierFXS', CARRIER, s)


def renamed(text, formkey, editor_id):
    text = sub1(text, r'^FormKey: .*$', 'FormKey: %s:%s' % (formkey, ME))
    text = sub1(text, r'^EditorID: .*$', 'EditorID: ' + editor_id)
    return sub1(text, r'^(Name:\n  TargetLanguage: English\n  Value: ).*$', r'\g<1>Blood Boil')


def blood_boil():
    """80E-812: the blood boil either dagger sets off on a target that carries the other's damage over time."""
    radius = re.search(r'^Float Property Radius = ([\d.]+) AutoReadOnly', read(SCRIPT), re.M)
    if not radius or float(radius.group(1)) != BOIL_RADIUS:
        sys.exit('%s: Radius is not BOIL_RADIUS %d' % (SCRIPT, BOIL_RADIUS))

    t = one(os.path.join(PROPHECY, 'MagicEffects'), '000B4A_' + PROPHECY_ESP)       # Bleeding Shot's relay
    assert 'Name: ZP_CastOnTargetEffect' in t and 'TargetType: Touch' in t and '- Painless' in t
    t = renamed(t, '00080E', 'ZP_BloodBoilTrigger')
    props = [('Blast', '00080F:' + ME), ('BoilShader', '000815:' + ME), ('BoilVisual', '000814:' + ME),
             ('Cooldown', '000811:' + ME), ('CooldownEffect', '000812:' + ME)]       # Spriggit's order: by name
    vmad = ['VirtualMachineAdapter:', '  Scripts:', '  - Name: ZP_BloodBoilEffect', '    Properties:']
    for name, obj in props:
        vmad += ['    - MutagenObjectType: ScriptObjectProperty', '      Name: ' + name, '      Object: ' + obj]
    t = sub1(t, r'^VirtualMachineAdapter:\n(?:  .*\n)+', '\n'.join(vmad) + '\n')
    rec('MagicEffects', 'ZP_BloodBoilTrigger', '00080E', t)

    b = one(os.path.join(PROPHECY, 'Spells'), '00099D_' + PROPHECY_ESP)             # A Willing Sacrifice's blast
    assert 'TargetType: TargetActor' in b and 'CastType: FireAndForget' in b
    b = renamed(b, '00080F', 'ZP_BloodBoilBlast')
    b = sub1(b, r'^- BaseEffect: .*$', '- BaseEffect: 000810:' + ME)
    b = sub1(b, r'^    Magnitude: 1$', '    Magnitude: %d' % BOIL_DAMAGE)
    rec('Spells', 'ZP_BloodBoilBlast', '00080F', b)

    e = one(os.path.join(PROPHECY, 'MagicEffects'), '00099E_' + PROPHECY_ESP)
    assert 'ActorValue: Health' in e and '- Hostile' in e
    e = renamed(e, '000810', 'ZP_BloodBoilBlastEffect')
    # BlameSpellKeyword stays; Conjuration goes for EGO's XionWeaponEnch, as on the daggers' own effects, so EGO's
    # spell-damage perks leave it alone
    e = sub1(e, r'^- 1076F4:Skyrim.esm\n', '- 001F93:%s\n' % EGO_ESP)
    e = sub1(e, r'^HitShader: .*\n', '')          # Apocalypse's Blood Boil shader: the script plays it
    e = sub1(e, r'^- NoArea\n- NoDuration\n', '- NoDuration\n- NoArea\n')     # Spriggit's order (flag bits)
    rec('MagicEffects', 'ZP_BloodBoilBlastEffect', '000810', e)

    c = one(os.path.join(PROPHECY, 'Spells'), '0009A0_' + PROPHECY_ESP)             # its cooldown
    c = renamed(c, '000811', 'ZP_BloodBoilCooldown')
    c = sub1(c, r'^(CastType: FireAndForget\n)', r'\g<1>TargetType: TargetActor\n')     # cast on the target
    c = sub1(c, r'^- BaseEffect: .*$', '- BaseEffect: 000812:' + ME)
    c = sub1(c, r'^    Duration: \d+$', '    Duration: %d' % BOIL_COOLDOWN)
    rec('Spells', 'ZP_BloodBoilCooldown', '000811', c)

    d = one(os.path.join(PROPHECY, 'MagicEffects'), '0009A1_' + PROPHECY_ESP)
    d = renamed(d, '000812', 'ZP_BloodBoilCooldownEffect')
    d = sub1(d, r'^Flags:\n- Recover\n', 'Flags:\n- NoMagnitude\n- NoArea\n- HideInUI\n')
    d = sub1(d, r'^(CastType: FireAndForget\n)', r'\g<1>TargetType: TargetActor\n')
    d = sub1(d, r'^(Description:\n  TargetLanguage: English\n  Value: ).*$', r"\g<1>''")
    rec('MagicEffects', 'ZP_BloodBoilCooldownEffect', '000812', d)


def vmad(script, props):
    """A single-script VMAD with object properties, in Spriggit's order (by name)."""
    lines = ['VirtualMachineAdapter:', '  Scripts:', '  - Name: ' + script, '    Properties:']
    for name, obj in sorted(props):
        lines += ['    - MutagenObjectType: ScriptObjectProperty', '      Name: ' + name, '      Object: ' + obj]
    return '\n'.join(lines) + '\n'


def mote_entry():
    """Rise's enchantment: the mote, on undead only."""
    return [
        '- BaseEffect: 000823:' + ME,
        '  Data:',
        '    Duration: %d' % MOTE_SECONDS,
        '  Conditions:',
        '  - MutagenObjectType: ConditionFloat',
        '    Data:',
        '      MutagenObjectType: HasKeywordConditionData',
        '      Keyword: ' + UNDEAD,
        '    ComparisonValue: 1',
    ]


def blast_spell(formkey, editor_id, name, effects):
    """A hostile TargetActor spell the scripts remote-cast from the player (A Willing Sacrifice's blast 99D's shape)."""
    b = one(os.path.join(PROPHECY, 'Spells'), '00099D_' + PROPHECY_ESP)
    b = sub1(b, r'^FormKey: .*$', 'FormKey: %s:%s' % (formkey, ME))
    b = sub1(b, r'^EditorID: .*$', 'EditorID: ' + editor_id)
    b = sub1(b, r'^(Name:\n  TargetLanguage: English\n  Value: ).*$', lambda m: m.group(1) + name)
    b = sub1(b, r'^Effects:\n(?:- .*\n(?:  .*\n)*)+', 'Effects:\n' + '\n'.join(effects) + '\n')
    rec('Spells', editor_id, formkey, b)


def damage_effect(formkey, editor_id, name, resist=None):
    """Instant Health damage (Willing Sacrifice's 99E): BlameSpellKeyword + EGO's XionWeaponEnch, no hit shader."""
    e = one(os.path.join(PROPHECY, 'MagicEffects'), '00099E_' + PROPHECY_ESP)
    e = sub1(e, r'^FormKey: .*$', 'FormKey: %s:%s' % (formkey, ME))
    e = sub1(e, r'^EditorID: .*$', 'EditorID: ' + editor_id)
    e = sub1(e, r'^(Name:\n  TargetLanguage: English\n  Value: ).*$', lambda m: m.group(1) + name)
    e = sub1(e, r'^- 1076F4:Skyrim.esm\n', '- 001F93:%s\n' % EGO_ESP)
    e = sub1(e, r'^HitShader: .*\n', '')
    e = sub1(e, r'^- NoArea\n- NoDuration\n', '- NoDuration\n- NoArea\n')
    if resist:
        e = sub1(e, r'^(Flags:\n(?:- .*\n)+)', lambda m: m.group(1) + 'ResistValue: %s\n' % resist)
    rec('MagicEffects', editor_id, formkey, e)


def relay(formkey, editor_id, name, script, props, no_death_dispel=False):
    """A hidden, painless script effect (Prophecy's relay B4A's shape)."""
    t = one(os.path.join(PROPHECY, 'MagicEffects'), '000B4A_' + PROPHECY_ESP)
    assert 'TargetType: Touch' in t and '- Painless' in t
    t = sub1(t, r'^FormKey: .*$', 'FormKey: %s:%s' % (formkey, ME))
    t = sub1(t, r'^EditorID: .*$', 'EditorID: ' + editor_id)
    t = sub1(t, r'^VirtualMachineAdapter:\n(?:  .*\n)+', vmad(script, props))
    t = sub1(t, r'^(Name:\n  TargetLanguage: English\n  Value: ).*$', lambda m: m.group(1) + name)
    if no_death_dispel:
        t = sub1(t, r'^(- Painless\n)', r'\g<1>- NoDeathDispel\n')
    rec('MagicEffects', editor_id, formkey, t)


def rework():
    """819-827: Sting's spiderlings and Rise's motes of sunlight (see the constants above)."""
    scripts = os.path.dirname(SCRIPT)
    for name, prop, want in (('ZP_StingSpiderlingEffect', 'LifeSeconds', SPIDER_LIFE),
                             ('ZP_StingSpiderlingEffect', 'SpeedMult', SPIDER_SPEED),
                             ('ZP_StingSpiderlingEffect', 'BiteReach', BITE_REACH),
                             ('ZP_StingSpiderlingEffect', 'Radius', SPIDER_BURST_RADIUS),
                             ('ZP_RiseMoteEffect', 'Radius', NOVA_RADIUS),
                             ('ZP_RiseMoteEffect', 'DamageBase', NOVA_DAMAGE),
                             ('ZP_RiseMoteEffect', 'DamagePerLevel', NOVA_PER_LEVEL)):
        m = re.search(r'^Float Property %s = ([\d.]+) AutoReadOnly' % prop, read(os.path.join(scripts, name + '.psc')), re.M)
        if not m or float(m.group(1)) != want:
            sys.exit('%s.psc: %s is not %s' % (name, prop, want))
    # ---- Sting: the brood mark (on the enchantment, 6 s) and the venom-burst mark (1 s, survives death so a kill by
    # the burst itself still counts); both run ZP_StingBroodMarkEffect, which spawns the spiderling
    brood = [('Spawned', '00081B:' + ME), ('SpawnBurst', '000822:' + ME), ('Spiderling', '00081C:' + ME),
             ('Spiderlings', '00081F:' + ME)]
    relay('000819', 'ZP_StingBroodMark', 'Sting Venom', 'ZP_StingBroodMarkEffect', brood)
    relay('00081A', 'ZP_StingBroodMarkBurst', 'Sting Venom', 'ZP_StingBroodMarkEffect', brood, no_death_dispel=True)
    rec('Factions', 'ZP_StingBroodSpawned', '00081B', '\n'.join([
        'FormKey: 00081B:' + ME, 'EditorID: ZP_StingBroodSpawned', 'Flags:', '- HiddenFromPC']))
    rec('FormLists', 'ZP_StingSpiderlings', '00081F', 'FormKey: 00081F:%s\nEditorID: ZP_StingSpiderlings' % ME)

    # the spiderling: Enderal's young Moss Crawler (EGO's record), made a short-lived ally the way Prophecy's Legion of
    # the Damned is (player's faction, teammate, SureAI's _DefaultFollowPlayer, its own ability that ends it)
    n = one(os.path.join(EGO, 'Npcs'), '01CB69_Skyrim.esm')
    assert 'EditorID: _03E_JungerMooskrabbler' in n and 'Race: 0EAA8E:Skyrim.esm' in n
    n = sub1(n, r'^FormKey: .*$', 'FormKey: 00081C:' + ME)
    n = sub1(n, r'^EditorID: .*$', 'EditorID: ZP_StingSpiderling')
    n = sub1(n, r'^VirtualMachineAdapter:\n(?:  .*\n)+', '')     # _00E_EPOnDeath: no EP, and it pays a killer of None
    n = sub1(n, r'^  Flags:\n  - Respawn\n', '')
    n = sub1(n, r'^(  Level:\n)    MutagenObjectType: NpcLevel\n    Level: \d+\n',
             r'\g<1>    MutagenObjectType: PcLevelMult\n    LevelMult: 1\n  CalcMinLevel: 1\n  CalcMaxLevel: 100\n')
    n = sub1(n, r'^Factions:\n- Faction: 018724:Skyrim.esm\n  Fluff: 0x000000\n',
             'Factions:\n- Faction: 000DB1:Skyrim.esm\n  Fluff: 0x000000\n')               # PlayerFaction
    n = sub1(n, r'^(Race: .*\n)', lambda m: m.group(1) + 'ActorEffect:\n- 00081D:%s\n' % ME)
    n = sub1(n, r'^AIData:\n(?:  .*\n)+', 'AIData:\n  Aggression: Aggressive\n  Confidence: Foolhardy\n'
             '  EnergyLevel: 50\n  Responsibility: NoCrime\n  Assistance: HelpsFriendsAndAllies\n')
    n = sub1(n, r'^Packages:\n- 10F7A5:Skyrim.esm\n', 'Packages:\n- 04B037:Skyrim.esm\n')  # _DefaultFollowPlayer
    n = sub1(n, r'^(Packages:\n(?:- .*\n)+)', lambda m: m.group(1) + 'Keywords:\n- 044FEA:Skyrim.esm\n')  # summoned
    n = english(n, 'Name', 'Venom Spiderling')
    n = sub1(n, r'^Height: .*$', 'Height: %g' % SPIDER_HEIGHT)
    rec('Npcs', 'ZP_StingSpiderling', '00081C', n)
    s = one(os.path.join(PROPHECY, 'Spells'), '0009A7_' + PROPHECY_ESP)          # Legion's ability
    s = sub1(s, r'^FormKey: .*$', 'FormKey: 00081D:' + ME)
    s = sub1(s, r'^EditorID: .*$', 'EditorID: ZP_StingSpiderlingAbility')
    s = sub1(s, r'^(Name:\n  TargetLanguage: English\n  Value: ).*$', r'\g<1>Venom Spiderling')
    s = sub1(s, r'^- BaseEffect: .*$', '- BaseEffect: 00081E:' + ME)
    s = sub1(s, r'^CastType: ConstantEffect\n', '')       # the default: Spriggit leaves it out
    rec('Spells', 'ZP_StingSpiderlingAbility', '00081D', s)
    a = one(os.path.join(PROPHECY, 'MagicEffects'), '0009A8_' + PROPHECY_ESP)    # Legion's skeleton effect
    a = sub1(a, r'^FormKey: .*$', 'FormKey: 00081E:' + ME)
    a = sub1(a, r'^EditorID: .*$', 'EditorID: ZP_StingSpiderlingEffect')
    a = sub1(a, r'^VirtualMachineAdapter:\n(?:  .*\n)+', vmad('ZP_StingSpiderlingEffect', [
        ('Burst', '000820:' + ME), ('BurstFX', '000822:' + ME), ('Spiderlings', '00081F:' + ME),
        ('WebCooldown', '00082E:' + ME), ('WebSpell', '00082A:' + ME), ('Bite', '00082F:' + ME)]))
    a = sub1(a, r'^(Name:\n  TargetLanguage: English\n  Value: ).*$', r'\g<1>Venom Spiderling')
    a = sub1(a, r'^CastType: ConstantEffect\n', '')
    a = sub1(a, r'^- NoMagnitude\n- NoArea\n- NoDuration\n', '- NoDuration\n- NoMagnitude\n- NoArea\n')   # flag bits
    rec('MagicEffects', 'ZP_StingSpiderlingEffect', '00081E', a)
    blast_spell('000820', 'ZP_StingSpiderBurst', 'Venom Burst', [
        '- BaseEffect: 00081A:' + ME, '  Data:', '    Duration: 1',             # the mark first: its kills spawn too
        '- BaseEffect: 000821:' + ME, '  Data:', '    Magnitude: %d' % SPIDER_BURST_DAMAGE])
    damage_effect('000821', 'ZP_StingSpiderBurstDamage', 'Venom Burst', resist='PoisonResist')
    x = read(os.path.join(BASE, 'EnderalFS', 'Explosions', '_00E_FS_MAGGoreExplosion - 06A18E_Skyrim.esm.yaml'))
    x = sub1(x, r'^FormKey: .*$', 'FormKey: 000822:' + ME)
    x = sub1(x, r'^EditorID: .*$', 'EditorID: ZP_StingSpiderBurstFX')
    x = sub1(x, r'^(Model:\n  File: ).*$', lambda m: m.group(1) + SPIDER_BURST_MODEL)
    x = sub1(x, r'^(Model:\n  File: .*\n)  Data: .*\n', r'\g<1>')
    x = sub1(x, r'^(Sound1: .*\n)', lambda m: m.group(1) + 'ImpactDataSet: %s\n' % SPIT_IMPACTS)
    x = sub1(x, r'^Force: .*\n', '')
    x = sub1(x, r'^Radius: .*$', 'Radius: 64')
    x = sub1(x, r'^ISRadius: .*\n', '')
    rec('Explosions', 'ZP_StingSpiderBurstFX', '000822', x)

    # ---- Rise: the mote of sunlight = vanilla Mage Light (LightFFAimed 01EA6D: a light on the target + the orb art
    # above it) in sun gold, on undead; a successful Turn Undead on its bearer makes ZP_RiseMoteEffect burst it
    t = one(os.path.join(EGO, 'MagicEffects'), '01EA6D_Skyrim.esm')            # EGO's record wins
    assert 'MagicEffectLightArchetype' in t and 'HitEffectArt: 041F06' in t
    t = sub1(t, r'^FormKey: .*$', 'FormKey: 000823:' + ME)
    t = sub1(t, r'^EditorID: .*$', 'EditorID: ZP_RiseMote')
    t = re.sub(r'^Version2: .*\n', '', t, flags=re.M)
    t = sub1(t, r'^VirtualMachineAdapter:\n(?:  .*\n)+', vmad('ZP_RiseMoteEffect', [
        ('BurstFX', '000828:' + ME), ('Nova', '000826:' + ME)]))
    t = english(t, 'Name', 'Mote of Sunlight')
    t = sub1(t, r'^Keywords:\n(?:- .*\n)+', '')
    t = sub1(t, r'^Flags:\n(?:- .*\n)+', 'Flags:\n- FXPersist\n- Painless\n')
    for field in ('BaseCost', 'MagicSkill', 'CastingLight', 'MinimumSkillLevel', 'SpellmakingCastingTime', 'Projectile',
                  'CastingArt', 'ImpactData', 'SkillUsageMultiplier'):
        t = re.sub(r'^%s: .*\n' % field, '', t, flags=re.M)   # BaseCost 0 too: never the costliest (enchant-art) effect
    assert not re.search(r'^(BaseCost|Projectile|CastingArt|MagicSkill): ', t, re.M)
    t = sub1(t, r'^(  Association: ).*$', r'\g<1>000824:' + ME)
    t = sub1(t, r'^TargetType: .*$', 'TargetType: Touch')
    t = sub1(t, r'^HitEffectArt: .*$', 'HitEffectArt: 000825:' + ME)
    t = sub1(t, r'^Sounds:\n(?:- .*\n(?:  .*\n)*)+', 'Sounds: []\n')
    t = english(t, 'Description', "''")
    rec('MagicEffects', 'ZP_RiseMote', '000823', t)
    li = one(os.path.join(BASE, 'Skyrim', 'Lights'), '03FA58_Skyrim.esm')
    li = sub1(li, r'^FormKey: .*$', 'FormKey: 000824:' + ME)
    li = sub1(li, r'^EditorID: .*$', 'EditorID: ZP_RiseMoteLight')
    li = sub1(li, r'^Color: .*$', 'Color: ' + MOTE_LIGHT_COLOR)
    li = sub1(li, r'^Radius: .*$', 'Radius: %d' % MOTE_LIGHT_RADIUS)
    rec('Lights', 'ZP_RiseMoteLight', '000824', li)
    o = one(os.path.join(BASE, 'Skyrim', 'ArtObjects'), '041F06_Skyrim.esm')
    o = sub1(o, r'^FormKey: .*$', 'FormKey: 000825:' + ME)
    o = sub1(o, r'^EditorID: .*$', 'EditorID: ZP_RiseMoteFX')
    o = sub1(o, r'^(Model:\n  File: ).*$', lambda m: m.group(1) + MOTE_MODEL)
    o = sub1(o, r'^(Model:\n  File: .*\n)  Data: .*\n', r'\g<1>')
    rec('ArtObjects', 'ZP_RiseMoteFX', '000825', o)
    blast_spell('000826', 'ZP_RiseFireNova', 'Fire Nova', mote_entry() + [
        '- BaseEffect: 000827:' + ME, '  Data:', '    Magnitude: %d' % NOVA_DAMAGE])
    damage_effect('000827', 'ZP_RiseFireNovaDamage', 'Fire Nova', resist='ResistFire')
    web_records()
    blast_spell('00082F', 'ZP_StingSpiderBite', 'Venom Bite', [                 # the spiderling's assisted bite
        '- BaseEffect: 000830:' + ME, '  Data:', '    Magnitude: %d' % BITE_DAMAGE])
    damage_effect('000830', 'ZP_StingSpiderBiteDamage', 'Venom Bite', resist='PoisonResist')


def web_records():
    """82A-82E (curator 2026-11-13: the spiderling's attacks "stop enemies in place with web", "webs attached to
    them", "takes them 3 seconds to break free"): the spiderling's own ability script (ZP_StingSpiderlingEffect, PO3
    OnWeaponHit / OnMagicHit) casts 82A on everything hostile it hits that is not still in the break-free cooldown 82E;
    82A = Webbed 82B (movement speed -100 for WEB_SECONDS: rooted, can still turn and swing; vanilla's web body
    shader 82C over it and web strands 82D from the ground up its legs) + the cooldown 82E for WEB_SECONDS +
    WEB_FREE_SECONDS (a spiderling bites often: without it a webbed enemy never got free). 829 RETIRED, never reuse:
    the first build's perk (ApplyCombatHitSpell on the spiderling) never went off in game - its bites carry the
    race's own attack spell 0638B2."""
    s = one(os.path.join(PROPHECY, 'Spells'), '000910_' + PROPHECY_ESP)        # the gun hit spell's shape
    assert 'TargetType: Touch' in s and 'CastType: FireAndForget' in s
    s = sub1(s, r'^FormKey: .*$', 'FormKey: 00082A:' + ME)
    s = sub1(s, r'^EditorID: .*$', 'EditorID: ZP_StingWebSpell')
    s = english(s, 'Name', 'Spider Web')
    s = sub1(s, r'^Effects:\n(?:- .*\n(?:  .*\n)*)+', '\n'.join([
        'Effects:',
        '- BaseEffect: 00082B:' + ME, '  Data:', '    Magnitude: 100', '    Duration: %d' % WEB_SECONDS,
        '- BaseEffect: 00082E:' + ME, '  Data:', '    Duration: %d' % (WEB_SECONDS + WEB_FREE_SECONDS)]) + '\n')
    rec('Spells', 'ZP_StingWebSpell', '00082A', s)
    w = read(os.path.join(OUT, 'MagicEffects', 'ZP_StingSlowEffect - 000817_%s.yaml' % ME))   # Sting's slow
    assert 'ActorValue: SpeedMult' in w and 'MagicEffectPeakValueModArchetype' in w
    w = sub1(w, r'^FormKey: .*$', 'FormKey: 00082B:' + ME)
    w = sub1(w, r'^EditorID: .*$', 'EditorID: ZP_StingWebbedEffect')
    w = english(w, 'Name', 'Webbed')
    w = sub1(w, r'^- NoArea\n', '- NoArea\n- FXPersist\n')       # the shader and strands last the whole effect
    w = sub1(w, r'^(SpellmakingCastingTime: .*\n)', lambda m: 'HitShader: 00082C:%s\n' % ME + m.group(1))
    w = sub1(w, r'^(TargetType: .*\n)', lambda m: m.group(1) + 'HitEffectArt: 00082D:%s\n' % ME)
    rec('MagicEffects', 'ZP_StingWebbedEffect', '00082B', w)
    x = read(os.path.join(BASE, 'Skyrim', 'EffectShaders', 'WebbedFXS - 02E1CD_Skyrim.esm.yaml'))   # vanilla, unused
    assert r'FillTexture: Effects\FXSpiderwebs01.dds' in x
    x = sub1(x, r'^FormKey: .*$', 'FormKey: 00082C:' + ME)
    x = sub1(x, r'^EditorID: .*$', 'EditorID: ZP_StingWebbedFXS')
    x = re.sub(r'^Version2: .*\n', '', x, flags=re.M)
    for field, value in WEB_SHADER.items():
        x = sub1(x, r'^%s: .*$' % field, '%s: %s' % (field, value))
    rec('EffectShaders', 'ZP_StingWebbedFXS', '00082C', x)
    o = one(os.path.join(BASE, 'Skyrim', 'ArtObjects'), '041F06_Skyrim.esm')    # a magic hit-effect art's shape
    o = sub1(o, r'^FormKey: .*$', 'FormKey: 00082D:' + ME)
    o = sub1(o, r'^EditorID: .*$', 'EditorID: ZP_StingWebbedFX')
    o = sub1(o, r'^(Model:\n  File: ).*$', lambda m: m.group(1) + WEB_MODEL)
    o = sub1(o, r'^(Model:\n  File: .*\n)  Data: .*\n', r'\g<1>')
    rec('ArtObjects', 'ZP_StingWebbedFX', '00082D', o)
    d = one(os.path.join(PROPHECY, 'MagicEffects'), '0009A1_' + PROPHECY_ESP)  # a marker, as Blood Boil's 812
    d = renamed(d, '00082E', 'ZP_StingWebCooldown')
    d = sub1(d, r'^Flags:\n- Recover\n', 'Flags:\n- NoMagnitude\n- NoArea\n- HideInUI\n')
    d = sub1(d, r'^(CastType: FireAndForget\n)', r'\g<1>TargetType: Touch\n')
    d = sub1(d, r'^(Description:\n  TargetLanguage: English\n  Value: ).*$', r"\g<1>''")
    rec('MagicEffects', 'ZP_StingWebCooldown', '00082E', d)
    # the nova's look: Enderal's Wayfarer fire nova on tools/01's scaled ring; no damage, push, enchantment or screen
    # effect of its own (826 carries the damage; the curator removes screen flashes, No Screen Flashes)
    x = read(os.path.join(ROOT, 'src', 'FlameShot', 'FlameShotESP', 'Explosions', NOVA_SOURCE))   # the winner
    assert r'File: Magic\FireStormAreaEffect.nif' in x, 'the Wayfarer nova changed its mesh'
    x = re.sub(r'^ImageSpaceModifier: .*\n', '', x, flags=re.M)       # Flame Shot already took it off
    x = sub1(x, r'^FormKey: .*$', 'FormKey: 000828:' + ME)
    x = sub1(x, r'^EditorID: .*$', 'EditorID: ZP_RiseFireNovaFX')
    x = re.sub(r'^Version2: .*\n', '', x, flags=re.M)
    x = sub1(x, r'^(Model:\n  File: ).*$', lambda m: m.group(1) + NOVA_MODEL)
    x = sub1(x, r'^(Model:\n  File: .*\n)  Data: .*\n', r'\g<1>')
    for field in ('ObjectEffect', 'Damage', 'Force', 'ISRadius'):
        x = sub1(x, r'^%s: .*\n' % field, '')
    x = sub1(x, r'^Radius: .*$', 'Radius: %d' % NOVA_RADIUS)
    rec('Explosions', 'ZP_RiseFireNovaFX', '000828', x)


def main():
    check_winners()
    for sub in ('Weapons', 'ObjectEffects', 'MagicEffects', 'ArtObjects', 'Keywords', 'Perks', 'ConstructibleObjects',
                'TextureSets', 'Statics', 'Spells', 'EffectShaders', 'Explosions', 'Npcs', 'Factions',
                'FormLists', 'Lights'):
        shutil.rmtree(os.path.join(OUT, sub), ignore_errors=True)

    blood = one(os.path.join(EGO, 'Weapons'), '015AA7_Skyrim.esm')
    aeterna = one(os.path.join(EGO, 'Weapons'), '07C98E_Skyrim.esm')
    assert 'File: ' + STING_MODEL in blood and 'FirstPersonModel: 14483F:Skyrim.esm' in blood
    assert 'File: ' + RISE_MODEL in aeterna and 'FirstPersonModel: 036BD0:Skyrim.esm' in aeterna

    # ---- Sting
    # curator 2026-11-13: a metal spider on the pommel, always visible -> Sting has its own mesh (tools/01) and so its
    # own first-person static (818 = Blood Needle's 14483F on that mesh)
    st = one(os.path.join(BASE, 'Skyrim', 'Statics'), '14483F_Skyrim.esm')
    assert 'File: ' + STING_MODEL in st
    st = sub1(st, r'^FormKey: .*$', 'FormKey: 000818:' + ME)
    st = sub1(st, r'^EditorID: .*$', 'EditorID: 1stPersonZP_Sting')
    st = sub1(st, r'^(Model:\n  File: ).*$', lambda m: m.group(1) + STING_OWN_MODEL)
    st = sub1(st, r'^(Model:\n  File: .*\n)  Data: .*\n', r'\g<1>')
    rec('Statics', '1stPersonZP_Sting', '000818', st)
    dagger('000800', 'ZP_Sting', 'Midnight Sting', STING_OWN_MODEL, blood, '000818:' + ME, '000801', bounds_source=OWN_SOURCE)
    enchantment('000801', 'ZP_StingVenom', 'Sting Venom', '000802', STING_DPS, [
        '- BaseEffect: 000817:' + ME,                       # the slow: hidden, named in the venom's text
        '  Data:',
        '    Magnitude: %d' % STING_SLOW,
        '    Duration: %d' % EFFECT_SECONDS,
        '- BaseEffect: 000819:' + ME,                       # the brood mark: a spiderling if it dies poisoned
        '  Data:',
        '    Duration: %d' % EFFECT_SECONDS,
    ] + boil_trigger('000806'))
    slow_effect()
    m = one(os.path.join(NSF, 'MagicEffects'), '001F73_%s' % EGO_ESP)
    m = sub1(m, r'^FormKey: .*$', 'FormKey: 000802:' + ME)
    m = sub1(m, r'^EditorID: .*$', 'EditorID: ZP_StingVenomEffect')
    m = english(m, 'Name', 'Sting Venom')
    m = sub1(m, r'^- PowerAffectsDuration\n', '')
    # EGO's poison dispels every effect sharing a keyword with it; XionWeaponEnch is on Rise's burn too, so a
    # Sting hit would put Rise's fire out (and wipe other poisons the player applied)
    m = sub1(m, r'^- DispelWithKeywords\n', '')
    m = sub1(m, r'^(DualCastScale: .*\n)', r'\g<1>EnchantArt: 000803:%s\n' % ME)
    m = sub1(m, r'^(HitShader: .*\n)', r'\g<1>EnchantShader: %s:%s\n' % (CARRIER, ME))   # the art needs one
    m = english(m, 'Description', STING_TEXT)    # Blood Boil and Rise's armor bonus are hidden (curator)
    m = sub1(m, r'^Conditions:\n(?:- .*\n(?:  .*\n)*)+', '')                # its "target lacks it" check
    assert 'Conditions' not in m and 'PowerAffects' not in m
    rec('MagicEffects', 'ZP_StingVenomEffect', '000802', m)
    art('000803', 'ZP_StingVenomCoatFX', STING_ART)

    # ---- Rise: shiny gold through alternate textures on Pretty's blade shape (WEAP + its own 1st-person STAT)
    # curator 2026-11-13: an angel on the pommel and wings on the guard -> Rise has its own mesh (tools/01) with the
    # ornaments appended, so the swapped shapes keep Pretty's names and indices (asserted)
    t = swap_targets(RISE_OWN_MODEL, OWN_SOURCE)
    assert t == swap_targets(RISE_MODEL), ('Rise.nif moved a swapped shape', t)
    print('rise gold: blade %r (index %d, normal %s), scabbard %r (index %d, normal %s)' % (t['blade'] + t['scb']))
    alt = alternate_textures([(t['blade'][0], t['blade'][1], '00080C'), (t['scb'][0], t['scb'][1], '000816')])
    gold_txst('00080C', 'ZP_RiseGold', GOLD_D, GOLD_N, GOLD_M)
    gold_txst('000816', 'ZP_RiseScabbardGold', SCB_D, SCB_N, SCB_M)      # curator: "the scabbard matches"
    st = one(os.path.join(BASE, 'Skyrim', 'Statics'), '036BD0_Skyrim.esm')
    assert 'File: ' + RISE_MODEL in st
    st = sub1(st, r'^FormKey: .*$', 'FormKey: 00080D:' + ME)
    st = sub1(st, r'^EditorID: .*$', 'EditorID: 1stPersonZP_Rise')
    st = sub1(st, r'^(Model:\n  File: ).*\n  Data: .*\n', lambda m: m.group(1) + RISE_OWN_MODEL + '\n' + alt)
    rec('Statics', '1stPersonZP_Rise', '00080D', st)
    dagger('000804', 'ZP_Rise', RISE_NAME, RISE_OWN_MODEL, aeterna, '00080D:' + ME, '000805', alt=alt,
           bounds_source=OWN_SOURCE,
           extra_keywords=['000808:' + ME, SILVER], script='\n'.join([
               'VirtualMachineAdapter:',
               '  Scripts:',
               '  - Name: ZP_RiseArmorPierceScript',
               '    Properties:',                 # Spriggit's order: by name
               '    - MutagenObjectType: ScriptObjectProperty',
               '      Name: ArmorPiercePerk',
               '      Object: 000809:' + ME,
               '    - MutagenObjectType: ScriptObjectProperty',
               '      Name: PlayerRef',
               '      Object: 000014:Skyrim.esm',
               '']))
    enchantment('000805', 'ZP_RiseFlame', 'Burning', '000806', RISE_DPS, mote_entry() + boil_trigger('000802'))
    f = one(os.path.join(FLAMESHOT, 'MagicEffects'), '067252_Skyrim.esm')
    f = sub1(f, r'^FormKey: .*$', 'FormKey: 000806:' + ME)
    f = sub1(f, r'^EditorID: .*$', 'EditorID: ZP_RiseBurnEffect')
    f = english(f, 'Name', 'Burning')
    f = sub1(f, r'^(Keywords:\n(?:- .*\n)+)', r'\g<1>- 001F93:%s\n' % EGO_ESP)    # XionWeaponEnch
    f = sub1(f, r'^- NoRecast\n', '')
    f = sub1(f, r'^(TaperWeight: .*\n)', r'\g<1>HitShader: 01B212:Skyrim.esm\n')   # FireFXShader
    f = sub1(f, r'^(DualCastScale: .*\n)', r'\g<1>EnchantArt: 000807:%s\n' % ME)
    f = sub1(f, r'^(HitShader: .*\n)', r'\g<1>EnchantShader: %s:%s\n' % (CARRIER, ME))
    f = english(f, 'Description', RISE_TEXT)     # Blood Boil and the armor bonus are hidden (curator)
    assert 'NoRecast' not in f and 'HitShader: 01B212' in f
    rec('MagicEffects', 'ZP_RiseBurnEffect', '000806', f)
    art('000807', 'ZP_RiseFlameFX', RISE_ART)
    rec('Keywords', 'ZP_RiseKeyword', '000808', '\n'.join([
        'FormKey: 000808:' + ME,
        'EditorID: ZP_RiseKeyword',
        "Color: '#00000000'",
    ]))
    rec('Perks', 'ZP_RiseArmorPierce', '000809', '\n'.join([
        'FormKey: 000809:' + ME,
        'EditorID: ZP_RiseArmorPierce',
        'Name:',
        '  TargetLanguage: English',
        '  Value: ' + RISE_NAME,
        'Description:',
        '  TargetLanguage: English',
        "  Value: ''",                                  # a hidden effect (curator 2026-11-13)
        'NumRanks: 1',
        'Hidden: True',
        'Effects:',
        '- MutagenObjectType: PerkEntryPointModifyValue',
        '  Conditions:',
        '  - RunOnTabIndex: 1',                          # the weapon
        '    Conditions:',
        '    - MutagenObjectType: ConditionFloat',
        '      Data:',
        '        MutagenObjectType: HasKeywordConditionData',
        '        Keyword: 000808:' + ME,
        '      ComparisonValue: 1',
        '  - RunOnTabIndex: 2',                          # the target
        '    Conditions:',
        '    - MutagenObjectType: ConditionFloat',
        '      Data:',
        '        MutagenObjectType: HasMagicEffectConditionData',
        '        MagicEffect: 000802:' + ME,
        '      ComparisonValue: 1',
        '  EntryPoint: ModTargetDamageResistance',
        '  PerkConditionTabCount: 3',
        '  Modification: Multiply',
        '  Value: 0',
    ]))

    blood_boil()
    carrier_shader()
    blood_burst()
    rework()

    # ---- grindstone tempering, as Yero's Last Words
    t0 = read(os.path.join(BASE, 'EnderalFS', 'ConstructibleObjects',
                           '_04E_Temper_Unique_YerosLastWords - 02A26E_Enderal - Forgotten Stories.esm.yaml'))
    for formkey, editor_id, product in (('00080A', 'ZP_TemperSting', '000800'), ('00080B', 'ZP_TemperRise', '000804')):
        t = sub1(t0, r'^FormKey: .*$', 'FormKey: %s:%s' % (formkey, ME))
        t = sub1(t, r'^EditorID: .*$', 'EditorID: ' + editor_id)
        t = sub1(t, r'^CreatedObject: .*$', 'CreatedObject: %s:%s' % (product, ME))
        rec('ConstructibleObjects', editor_id, formkey, t)
    place_records()
    print('records written to', OUT)


# where the daggers are found (curator 2026-11-15, from a shortlist):
# - Midnight Sting: "Undercity Old Vault", Forgotten Stories' vault in Ark's underworld overrun by tunnel spiders
#   (level 25): inside the open coffin that lies on a table in its coffin room (CommonCoffinOpen01 ref 02AF7A; the
#   second coffin 02AF7B is stacked under it and stays below its floor). The cell header is FS's (the only plugin)
# - Sunrise: "Old Soltyris, The Void", the end of the Sun Path desert ruin: on the Dwemer pedestal (06EEB4) beside the
#   tome, potions, soul gem and helmet the dungeon already leaves there, clear of each. The header is Skyrim.esm's
PLACE_STING = dict(cell='FSNQ03Hideout', header='Enderal - Forgotten Stories.esm',
                   surface='02AF7A:Enderal - Forgotten Stories.esm', top=3.79,      # the coffin's floor (surface.levels)
                   headings=[math.pi / 2, -math.pi / 2], band=30.0,                # along the coffin; its walls block
                   blockers=[('02AF7B:Enderal - Forgotten Stories.esm', None)])
TOME = ((-13.0, -10.0, -1.0), (13.0, 10.0, 6.0))       # a spell tome, generously: its mesh has no shape surface reads
PLACE_RISE = dict(cell='DesertAltSoltyrisL2KeyLvl2', header='Skyrim.esm', surface='06EEB4:Skyrim.esm',
                  top=87.42,                             # the pedestal's top (PG Patcher Output's mesh; surface.levels)
                  headings=[math.radians(a) for a in np.arange(0.0, 180.0, 7.5)], band=60.0,
                  blockers=[('03A2EB:Skyrim.esm', None), ('03A2EC:Skyrim.esm', None),      # the two potions
                            ('03A2ED:Skyrim.esm', None), ('03A2EE:Skyrim.esm', None),      # the soul gem, the helmet
                            ('03A2EF:Skyrim.esm', TOME)])                                  # the Wall of Frost tome


def place_records():
    """831 / 832 REFR: Midnight Sting in the Old Vault's coffin, Sunrise on the Void's pedestal (see PLACE_*)."""
    sys.path.insert(0, HERE)
    import surface
    spec = importlib.util.spec_from_file_location('sr_assets', os.path.join(HERE, '01-build-assets.py'))
    sr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sr)
    files = {}
    for name, place, model, base, ref in (('Midnight Sting', PLACE_STING, STING_OWN_MODEL, '000800', '000831'),
                                          ('Sunrise', PLACE_RISE, RISE_OWN_MODEL, '000804', '000832')):
        f, spot = surface.place_unique(sr, place['cell'], place['header'], place['surface'], place['top'], model,
                                       '%s:%s' % (base, ME), '%s:%s' % (ref, ME), place['headings'],
                                       blockers=place['blockers'], band=place['band'])
        files.update(f)
        print('  %s placed at %s, heading %.3f, on %s (z %.2f), %.1f from its middle' % (
            name, tuple(round(v, 2) for v in spot['position']), spot['heading'], place['surface'], spot['top'],
            spot['distance']))
    shutil.rmtree(os.path.join(OUT, 'Cells'), ignore_errors=True)
    for rel, text in files.items():
        path = os.path.join(OUT, *rel.split('/'))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(text)


if __name__ == '__main__':
    main()
