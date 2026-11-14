"""Generate Sting's and Rise's enchant-art meshes: the green poison coat on Sting's blade and the small
flickering flames on Rise's blade.

Both daggers keep Pretty Enderal Armory's own meshes, untouched and referenced by path (curator 2026-11-13:
"use something from Pretty Armory"): Sting = the assassin blade (Blood Needle's model,
Enderal\\weapons\\Iron\\irondagger2.nif), Rise = the Aeterna dagger (Weapons\\Elven\\1stPersonElvenDagger.nif).
Each WEAP and its first-person STAT use the same file, so one art mesh fits both views. The effects are
**enchant art** (MGEF EnchantArt -> ARTO), the mechanism Chillrend and the bound weapons use: the engine
attaches the art's root to the weapon's root while the enchanted weapon is drawn. So nothing of Pretty's is
copied; only its blade's shape is measured.

Inputs (the curator's installed list, nothing committed; winners resolved like the game does):
  Pretty's two dagger meshes     the blade = the welded mesh island holding the tip (both blades are their own
                                 island: assassin 75 triangles, Aeterna 1040)
  meshes/clutter/dwemer/dweichorgoo01.nif   the green Dwemer ichor puddle the curator saw in game (JS Dwemer Ichor
                                 Barrels' mesh through PG Patcher); its goo surface L1_GooBase09's material:
                                 BSLightingShaderProperty (glow, green own-emit, green specular), texture set
                                 FX_IchorBarrel.dds + water_v2_n.dds and its two UV-scroll controllers (the slow
                                 flow), copied block for block
  meshes/magic/ChillrendEnchFX.nif          Chillrend's enchant art (one particle system, box emitter sized to a
                                 blade, lag bone): the frame of Rise's art
  meshes/weapons/torch/torch.nif            the held torch's flame (pFireballCore04): its shader (FXFireAtlas04 +
                                 GradFireExplosion palette), alpha, particle data (8-frame atlas), colour and size
                                 curves are copied into Chillrend's blocks

Outputs, into <mods>/<target mod>/ (default Zenderal - Patch Collection):
  meshes/Zenderal/StingAndRise/StingEnchFX.nif
      BSFadeNode + BSXFlags (Chillrend's) + one BSTriShape: a shell over the assassin blade (welded, subdivided
      until no edge is over 0.4 units, pushed out along the averaged normal by 0.05-0.17 units of 3D noise so it reads as lumpy goo),
      cut along a ragged line above the guard with a few runs reaching down to it, thinning to the steel at its
      edge. Planar UVs at the puddle's own texel density, tangents in the puddle's convention, vertex colours in
      the puddle's range. Material = the puddle's, block for block.
  meshes/Zenderal/StingAndRise/RiseEnchFX.nif
      ChillrendEnchFX.nif with the torch flame's look: emitter box fitted to the Aeterna blade (guard + 1.5 to
      tip - 1, 70% of its width), small flames (radius 2.2), short lives, world-up gravity so they lick upward
      whichever way the blade points. Every other block byte-identical (asserted).
  meshes/Zenderal/StingAndRise/BloodBoilBurst.nif
      Blood Boil's pop (curator 2026-11-13: "more of a blood splatter effect that pops", not the red flames):
      Forgotten Stories' gore burst swordbloodexplosion.nif (Father's Legacy's exploding enemies) with its 14
      meat-chunk nodes (Havok debris, man's skin and horse-meat textures) and its meat-chunk particle emitter
      taken off the scene root; the blood drops and blood streams stay, emitted at chest height (z 63-77) as
      Enderal made them. Every block stays in the file (the controllers keep their targets); only the root's
      child list changes (asserted).

Usage:  python 01-build-assets.py [--mods <MO2 mods dir>] [--target <mod name>] [--out-root <dir>] [--preview <png>]
"""
import argparse
import importlib.util
import json
import math
import os
import shutil
import struct
import subprocess
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE)
import nifse  # noqa: E402

TOOLS = json.load(open(os.path.join(ROOT, '.claude', 'config', 'tools.json'), encoding='utf-8-sig'))
_spec = importlib.util.spec_from_file_location('_bsa', os.path.join(ROOT, 'src', 'Prophecy', 'tools', '_bsa.py'))
_bsa = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bsa)

MO2 = TOOLS['modlistRoot']
DATA = TOOLS['gameDataDir']
PROFILE = 'Ultra'
MESH_BSAS = ['E - Meshes.bsa', 'Skyrim - Meshes0.bsa', 'Skyrim - Meshes1.bsa']

STING_MESH = 'meshes/Enderal/weapons/Iron/irondagger2.nif'      # Pretty Enderal Armory's assassin blade
RISE_MESH = 'meshes/Weapons/Elven/1stPersonElvenDagger.nif'       # Pretty Enderal Armory's Aeterna dagger
EXPECT_SOURCE = 'Pretty Enderal Armory'
GOO_MESH = 'meshes/clutter/dwemer/dweichorgoo01.nif'
GOO_SHAPE = 'L1_GooBase09'
GOO_TEXTURE = 'FX_IchorBarrel.dds'
ART_TEMPLATE = 'meshes/magic/ChillrendEnchFX.nif'
TORCH_MESH = 'meshes/weapons/torch/torch.nif'
FLAME_PSYS = 'pFireballCore04'

BURST_MESH = 'meshes/Enderal/ForgottenStories/effects/swordbloodexplosion.nif'   # FS's gore burst
BURST_DROP = ('meatChunk', 'pBloodMeatChunk')     # root children whose names start so are taken off the scene
BURST_KEEP_PSYS = ('pBloodDrops10', 'pBloodLines04')
OUT_BURST = 'meshes/Zenderal/StingAndRise/BloodBoilBurst.nif'
OUT_STING_MESH = 'meshes/Zenderal/StingAndRise/Sting.nif'   # Pretty's assassin blade + the pommel spider
# The rework (curator 2026-11-13): Sting's spiderlings burst in venom when they die; Rise marks undead with a mote of
# sunlight that bursts in a weak fire nova when the marked enemy dies (curator, same evening: instead of Dawnbreaker's
# burst). Three generated meshes and three palettes for them:
NOVA_SRC = 'meshes/magic/FireStormAreaEffect.nif'    # vanilla Fire Storm's ring of flame (Enderal's Wayfarer nova uses it)
NOVA_MARKER = 'BlastRadiusNode'                      # the mesh's own marker of the ring's reach (615 units)
OUT_NOVA = 'meshes/Zenderal/StingAndRise/RiseNova.nif'
NOVA_SCRIPT = os.path.join(HERE, '..', 'Scripts', 'source', 'ZP_RiseMoteEffect.psc')   # its Radius = the ring's reach
# The spiderling's web (curator 2026-11-13: "webs attached to them"): vanilla's web strip (two web sheets from the
# ground up, pinched in the middle, 270 tall; the game's own copy, not Particle Patch's) as the Webbed effect's hit
# art, without its collision, havok flags and blast node, scaled to an actor's legs: ground to the waist.
WEB_SRC = 'meshes/effects/fxspiderwebhitstrip01.nif'
OUT_WEB = 'meshes/Zenderal/StingAndRise/StingWebStrands.nif'
WEB_SCALE = 0.4              # 0.3 was easy to miss (curator); 0.4 = ground to about the chest
MOTE_SRC = 'meshes/magic/lightspellactorfx.nif'      # the Mage Light / Candlelight orb (Enderal's, E - Meshes.bsa)
OUT_MOTE = 'meshes/Zenderal/StingAndRise/RiseMote.nif'
MOTE_TINT = (1.0, 0.80, 0.42)                         # its glow and glare layers' base colour: sun gold
OUT_SPIDER_BURST = 'meshes/Zenderal/StingAndRise/StingSpiderBurst.nif'
SPIDER_BURST_SCALE = 0.40                             # Blood Boil's burst (chest-high on a man) shrunk to a spiderling
VENOM_RAMP = ((0.0, (0.01, 0.05, 0.0)), (0.45, (0.16, 0.50, 0.05)), (0.8, (0.50, 0.90, 0.20)), (1.0, (0.85, 1.0, 0.55)))
SUN_RAMP = ((0.0, (0.20, 0.09, 0.0)), (0.45, (0.95, 0.62, 0.15)), (0.8, (1.0, 0.86, 0.45)), (1.0, (1.0, 0.98, 0.85)))
PALETTES = {     # Bethesda's palette (read from the game BSAs, never a replacer) -> ours, recoloured by luminance
    'textures/effects/gradients/GradBlood.dds': ('textures/Zenderal/StingAndRise/GradVenom.dds', VENOM_RAMP),
    'textures/effects/gradients/GradBlood02.dds': ('textures/Zenderal/StingAndRise/GradVenom02.dds', VENOM_RAMP),
    'textures/effects/gradients/gradlightspell.dds': ('textures/Zenderal/StingAndRise/GradSunMote.dds', SUN_RAMP),
}
SPIDER_UV_SCALE = 0.003    # the spider's UVs: a small patch of the blade's own metal (UV per unit), so it is plain blackened steel
SPIDER_MIN_CLEARANCE = 1.15   # each leg's centre line stays this many of its radii clear of the pommel
OUT_STING = 'meshes/Zenderal/StingAndRise/StingEnchFX.nif'
OUT_RISE = 'meshes/Zenderal/StingAndRise/RiseEnchFX.nif'

# ---- Rise: shiny gold (curator 2026-11-13) ----------------------------------------------------------------
# Pretty's Aeterna blade shape keeps its mesh; Rise's WEAP and first-person STAT swap its texture set for TXST
# 80C through the model's alternate textures (Bethesda's Nettlebane: the ebony dagger mesh + a TXST). The TXST
# points at these three generated textures + Pretty's own normal map.
RISE_TEX_DIR = 'textures/weapons/noble armory/short sword/'
RISE_DIFFUSE = RISE_TEX_DIR + 'shortsword.dds'
RISE_ENVMASK = RISE_TEX_DIR + 'shortsword_m.dds'
CHROME_CUBEMAP = 'textures/cubemaps/chrome_e.dds'    # Bethesda's chrome studio cubemap (read from the game BSAs)
CHROME_BSAS = ['Skyrim - Textures%d.bsa' % k for k in range(9)]
OUT_GOLD_D = 'textures/Zenderal/StingAndRise/RiseGold_d.dds'
OUT_GOLD_N = 'textures/Zenderal/StingAndRise/RiseGold_n.dds'
OUT_GOLD_M = 'textures/Zenderal/StingAndRise/RiseGold_m.dds'
OUT_GOLD_E = 'textures/Zenderal/StingAndRise/RiseGold_e.dds'
RISE_NORMAL = RISE_TEX_DIR + 'shortsword_n.dds'
RISE_SCB_DIFFUSE = RISE_TEX_DIR + 'sheath.dds'       # the scabbard (shape `scb`, its own texture set)
RISE_SCB_NORMAL = RISE_TEX_DIR + 'sheath_n.dds'
RISE_SCB_ENVMASK = RISE_TEX_DIR + 'sheath_m.dds'
OUT_SCB_D = 'textures/Zenderal/StingAndRise/RiseScabbardGold_d.dds'
OUT_SCB_N = 'textures/Zenderal/StingAndRise/RiseScabbardGold_n.dds'
OUT_SCB_M = 'textures/Zenderal/StingAndRise/RiseScabbardGold_m.dds'
METAL_MASK = (0.02, 0.08)   # env mask -> metal weight (smoothstep): the leather grip's mask is black
# Polished gold (curator 2026-11-13: "shiny / reflective metallic gold"; then "it's matte"). Build 3, the classic way
# vanilla's shiny metal works, which shines whatever the scene: a plain env mask (no alpha, so Bottled Shaders'
# Complex Material stays off and the texture set's cubemap is reflected, Lighting.hlsl's `!dynamicCubemap` path)
# at full strength on the metal, a high-contrast gold cubemap made from Bethesda's chrome studio cubemap, and the
# highlights' mask (the normal map's alpha) raised: Pretty's is 0.18 on the blade's metal (dull steel), the main
# reason it read matte. Build 2's Complex Material (metal reflecting Dynamic Cubemaps' live surroundings) read as
# matte gold in game: its reflections are only as bright and as patterned as the scene around the blade.
# Build 4 (curator added Precious Objects Complex Material and Dynamic Cubemap, Nexus 114727: "make it actually
# shiny now"): that mod's gold recipe, read from its files, on Rise. Its gold (textures/rci/goldclutter*):
# a Complex Material mask R 0.94 / G 0.93 / B 1.0 / A 0, a pale bright gold diffuse (mean 0.95/0.83/0.58), normal-map
# highlight mask 0.63-0.88, env scale 5 in its meshes (Vanilla Fresnel saturates the mask at 1, so R = 1 here is the
# same). Build 2 was Complex Material with Pretty's 0.18 highlight mask and an orange gold: read matte. The texture
# set keeps build 3's gold chrome cubemap: a complex material ignores it (it reflects Dynamic Cubemaps' live
# surroundings), and where Complex Material is off it is the shine.
GOLD_RAMP = ((0.0, (0.74, 0.60, 0.34)), (0.5, (0.98, 0.86, 0.60)), (1.0, (1.0, 0.95, 0.80)))   # ~Precious's
SPEC = (0.78, 1.5, 0.13)    # metal's highlight mask = clip(a + b * (Pretty's normal alpha - c)): ~0.8, as Precious's
COMPLEX = (0.94, 0.93, 1.0)  # metal's mask: reflection, glossiness (roughness 0.07), metalness; alpha 0. R as
                             # Precious's: at 1.0 the mask's 1x1 mip came out grey (0.72/0.73/0.72) and Bottled
                             # Shaders refuses a grey mask as complex (Lighting.hlsl `grayscaleMask`)
COMPLEX_GLOSS_VAR = 0.04    # glossiness - this * (Pretty's mask stretched 1..0): a little wear where Pretty's is dull
LEATHER_GLOSS = 0.2         # non-metal: no reflection (R = 0, B = 0), matt highlights
CUBE_SIZE = 256             # the chrome cubemap (32 per face) is resampled to this before grading
CUBE_GAMMA = 1.3            # contrast: luminance ** gamma ...
CUBE_GAIN = 1.5             # ... * gain, then graded dark gold -> gold -> pale gold
CUBE_RAMP = ((0.0, (0.10, 0.06, 0.01)), (0.35, (0.55, 0.38, 0.10)), (0.7, (1.0, 0.80, 0.36)),
             (1.0, (1.0, 0.95, 0.75)))
TEX_BSAS = ['E - Textures1.bsa', 'E - Textures2.bsa'] + ['Skyrim - Textures%d.bsa' % k for k in range(9)]

# ---- the grips (curator 2026-11-13: Sting's leather "very dark green", Rise's "ivory white leather") ---------
# The grip = the mesh's UV islands holding a triangle wholly between the pommel and the guard, kept when most of
# their texels are leather (non-metal, warm); every leather texel inside them is moved to the new colour, its
# brightness relative to the leather's own 75th percentile kept (the wrap's bands, cracks, stitches).
STING_GRIP_Y = (-7.6, 2.95)    # assassin blade: ring pommel to Y -8, guard from 3
RISE_GRIP_Y = (-7.4, 5.4)      # Aeterna dagger: pommel to -7.5, cross guard from 5.5
STING_LEATHER = ((0.030, 0.100, 0.050), 1.0)   # (colour at the leather's 75th-percentile brightness, contrast kept)
RISE_LEATHER = ((0.92, 0.88, 0.78), 0.6)       # ivory; the wrap's dark bands at 60% of their depth
LEATHER_WARM = 0.012           # a leather texel: R - B above this (Pretty's leathers are brown / oxblood) ...
LEATHER_ISLAND = 0.6           # ... and an island is leather when this share of its texels is
OUT_STING_D = 'textures/Zenderal/StingAndRise/StingBlade_d.dds'   # Pretty's blade.dds with the green grip

# ---- Rise's ornaments (curator 2026-11-13): an angel holding a sun on the pommel, wings spread from the guard,
# polished gold (angel.py). Rise gets its own mesh: Pretty's Aeterna dagger + two shapes appended to the root
# (so the blade's and scabbard's alternate-texture indices do not move; 02 asserts it), each on its own copy of
# the blade's shader whose texture set is a plain polished-gold set built on the blade gold's recipe.
OUT_RISE_MESH = 'meshes/Zenderal/StingAndRise/Rise.nif'
RISE_POMMEL_Y = -8.71          # the pommel knob's lowest point (asserted within 0.05): the knob is removed ...
KNOB_TRIS = 280                # ... (its triangles: a separate piece, asserted) ...
BAND_BOTTOM = -6.13            # ... and the angel's socket caps the grip's ring band, whose bottom is here
RISE_GUARD_X = (6.25, -6.02)   # the guard arms' ends (asserted within 0.15)
GUARD_ARM_FROM = 2.1           # |x| where an arm leaves the guard's centre block: the wing's sheath starts here
ORNAMENT_GOLD = (0.92, 0.80, 0.55)   # the blade gold's mean on metal (gold_set: 0.90 0.79 0.55)
ORNAMENT_SPEC = 0.85                 # its highlight mask (the blade gold's on metal)
ORNAMENT_UV = 0.01                   # planar UVs (the textures are plain)
OUT_ORN_D = 'textures/Zenderal/StingAndRise/RiseOrnament_d.dds'
OUT_ORN_N = 'textures/Zenderal/StingAndRise/RiseOrnament_n.dds'
OUT_ORN_M = 'textures/Zenderal/StingAndRise/RiseOrnament_m.dds'

WELD = 1e-4            # positions closer than this are one vertex

# ---- Sting: the poison coat ------------------------------------------------------------------------------
MAX_EDGE = 0.4         # the blade is refined until no edge is longer (its 75 triangles are long slivers)
OFFSET = 0.05          # coat floor above the steel (shape units; the blade is 0.38 thick)
LUMP = 0.12            # + up to this much of 3D noise: lumpy goo
LUMP_FREQ = 0.45       # noise cells per unit
# Curator 2026-11-13: "just have the tip and another 15% of the blade". The tip = the point, from where the blade
# is down to TIP_WIDTH of its full width (assassin blade: Y ~38 of 4.4..42.9); the coat line sits COVER_BELOW_TIP
# of the blade's length below that (~top 28% of the blade; the first build covered all but the 3 units above the
# guard) ...
TIP_WIDTH = 0.5
COVER_BELOW_TIP = 0.15
RAG = 1.2              # ... +- half this much noise across the blade (each face its own) ...
RAG_FREQ = 0.8
DRIPS = ((-0.85, 1.4, 0.32), (0.15, 2.2, 0.28), (0.95, 1.0, 0.24))   # ... minus runs (x, length, half width):
                       # rounded at the end (an ellipse), front face; the back face's are 60% as long
DRIP_FLOOR = 0.4       # runs stop this far above the guard
GREY_PCT = (25, 90)    # vertex grey taken from these percentiles of the puddle's own vertex colours
TAPER = 1.2            # the coat thins to MIN_OFFSET over this distance from its cut edge
MIN_OFFSET = 0.015
SEED = 1302

# ---- Rise: the flames ------------------------------------------------------------------------------------
FLAME_GAP_BASE = 1.5   # flames start this far above the blade's base ...
FLAME_GAP_TIP = 1.0    # ... and stop this far short of the tip
FLAME_WIDTH = 0.7      # fraction of the blade's width the box spans (flames hug the blade, not its edges)
FLAME_RADIUS = 2.2     # particle radius (the torch's is 13): subtle
FLAME_RADIUS_VAR = 0.4
FLAME_LIFE = 0.35      # s (the torch's 0.33)
FLAME_LIFE_VAR = 0.08
FLAME_SPEED = 3.0
FLAME_SPEED_VAR = 2.0
FLAME_GRAVITY = 90.0   # world up (the torch's 405 throws its flame ~20 units up; this licks ~5)
BIRTH_RATE = 36.0      # per second: ~12 flames alive along the blade
MAX_PARTICLES = 32     # NiPSysData's particle cap (the torch's 7 would starve the blade)
MAX_TILT_DEG = 3.0     # the box is axis-aligned; a blade leaning more than this needs a rotated box


# ---- inputs ----------------------------------------------------------------------------------------------

def profile_mods():
    lines = open(os.path.join(MO2, 'profiles', PROFILE, 'modlist.txt'), encoding='utf-8').read().splitlines()
    return [l[1:] for l in lines if l.startswith('+')]


def find_ci(base, rel):
    cur = base
    for part in rel.replace('\\', '/').split('/'):
        if not os.path.isdir(cur):
            return None
        hit = [e for e in os.listdir(cur) if e.lower() == part.lower()]
        if not hit:
            return None
        cur = os.path.join(cur, hit[0])
    return cur if os.path.isfile(cur) else None


_bsa_cache = {}


def winner(mods_dir, mods, rel, bsas=None):
    """(source label, bytes): the highest-priority loose copy, else the first BSA that has it."""
    for mod in mods:
        p = find_ci(os.path.join(mods_dir, mod), rel)
        if p:
            return mod, open(p, 'rb').read()
    key = rel.replace('/', '\\').lower()
    for name in bsas or MESH_BSAS:
        path = os.path.join(DATA, name)
        if not os.path.isfile(path):
            continue
        if name not in _bsa_cache:
            _bsa_cache[name] = _bsa.listing(path)
        data, listing = _bsa_cache[name]
        if key in listing:
            return name, _bsa.read(data, listing[key])
    sys.exit('no source for ' + rel)


def load(mods_dir, mods, rel):
    src, raw = winner(mods_dir, mods, rel)
    nif = nifse.Nif(raw)
    assert nif.tobytes() == raw, 'round trip failed: ' + rel
    print('%-48s from %s' % (rel, src))
    return src, nif


def name_of(nif, k):
    return nif.string(struct.unpack_from('<i', nif.blocks[k], 4 if nif.btype(k) == 'BSLightingShaderProperty' else 0)[0])


# ---- geometry helpers ------------------------------------------------------------------------------------

def islands(T, wid):
    parent = np.arange(wid.max() + 1)

    def f(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for t in T:
        a, b, c = f(wid[t[0]]), f(wid[t[1]]), f(wid[t[2]])
        parent[b] = a
        parent[f(c)] = a
    return np.array([f(wid[t[0]]) for t in T])


def blade(nif):
    """The blade: in the lit (non-blood, non-sheath) shape reaching highest, the welded island holding the tip.
    Returns its shape block, transform and triangles (shape space)."""
    t0, R0, s0 = nifse.transform(nif.blocks[nif.roots[0]])
    assert np.allclose(t0, 0) and np.allclose(R0, np.eye(3), atol=1e-5) and abs(s0 - 1) < 1e-6, 'root transform'
    best = None
    for k in nif.find('BSTriShape'):
        nm = (name_of(nif, k) or '').lower()
        if nm == 'scb' or 'blood' in nm:
            continue
        s = nifse.read_trishape(nif.blocks[k])
        if s['shader'] < 0 or nif.btype(s['shader']) != 'BSLightingShaderProperty':
            continue
        t, R, sc = nifse.transform(nif.blocks[k])
        W = s['pos'] * sc @ R.T + t
        if best is None or W[:, 1].max() > best[0]:
            best = (W[:, 1].max(), k, s, (t, R, sc))
    _, k, s, (t, R, sc) = best
    P, T = s['pos'], s['tris']
    _, wid = np.unique(np.round(P / WELD).astype(np.int64), axis=0, return_inverse=True)
    wid = wid.reshape(-1)
    lab = islands(T, wid)
    W = P * sc @ R.T + t
    tip = int(np.argmax(W[:, 1]))
    tri_tip = np.where((T == tip).any(1))[0][0]
    keep = lab == lab[tri_tip]
    # the coat is pushed along normals built from the winding: it must agree with the normals the mesh stores
    Tk = T[keep]
    fn = normalize(np.cross(P[Tk[:, 1]] - P[Tk[:, 0]], P[Tk[:, 2]] - P[Tk[:, 0]]))
    agree = np.sign((fn * normalize(s['normal'][Tk].mean(1))).sum(1)).mean()
    assert agree > 0.9, 'blade winding disagrees with its stored normals (%.2f)' % agree
    return dict(block=k, name=name_of(nif, k), xf=(t, R, sc), pos=P, tris=T[keep],
                flags=struct.unpack_from('<I', nif.blocks[k], nifse.av_fields(nif.blocks[k])['flags'])[0])


def weld(P, T):
    key = np.round(P / WELD).astype(np.int64)
    _, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
    Tw = inv.reshape(-1)[T]
    ok = (Tw[:, 0] != Tw[:, 1]) & (Tw[:, 1] != Tw[:, 2]) & (Tw[:, 0] != Tw[:, 2])
    used = np.unique(Tw[ok])
    remap = -np.ones(len(first), int)
    remap[used] = np.arange(len(used))
    return P[first][used], remap[Tw[ok]]


def refine(V, T, max_edge):
    """Split every edge longer than max_edge at its midpoint (shared, so the mesh stays watertight), each
    triangle into 2, 3 or 4 by how many of its edges split, winding kept; repeat until none is longer."""
    V = [np.asarray(v, float) for v in V]
    T = [tuple(t) for t in T]
    for _ in range(40):
        mids = {}
        for a, b, c in T:
            for u, w in ((a, b), (b, c), (c, a)):
                key = (u, w) if u < w else (w, u)
                if key not in mids and np.linalg.norm(V[u] - V[w]) > max_edge:
                    mids[key] = len(V)
                    V.append((V[u] + V[w]) / 2)
        if not mids:
            return np.array(V), np.array(T)
        out = []
        for a, b, c in T:
            m = [mids.get((u, w) if u < w else (w, u)) for u, w in ((a, b), (b, c), (c, a))]
            k = sum(x is not None for x in m)
            if k == 0:
                out.append((a, b, c))
                continue
            # rotate so the pattern starts at a split edge: (a, b) split first
            while m[0] is None or (k == 2 and m[1] is None):
                a, b, c = b, c, a
                m = m[1:] + m[:1]
            ab, bc, ca = m
            if k == 1:
                out += [(a, ab, c), (ab, b, c)]
            elif k == 2:
                out += [(ab, b, bc), (a, ab, bc), (a, bc, c)]
            else:
                out += [(a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca)]
        T = out
    sys.exit('refine did not converge')


def normalize(v):
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-12)


def vertex_normals(V, T):
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])     # area weighted
    N = np.zeros_like(V)
    for i in range(3):
        np.add.at(N, T[:, i], fn)
    return normalize(N)


def uv_derivatives(V, UV, T):
    du = np.zeros_like(V)
    dv = np.zeros_like(V)
    e1, e2 = V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]]
    a1, a2 = UV[T[:, 1]] - UV[T[:, 0]], UV[T[:, 2]] - UV[T[:, 0]]
    det = a1[:, 0] * a2[:, 1] - a2[:, 0] * a1[:, 1]
    ok = np.abs(det) > 1e-12
    dPu = (e1 * a2[:, 1:2] - e2 * a1[:, 1:2]) / np.where(ok, det, 1)[:, None]
    dPv = (e2 * a1[:, 0:1] - e1 * a2[:, 0:1]) / np.where(ok, det, 1)[:, None]
    for i in range(3):
        np.add.at(du, T[ok, i], dPu[ok])
        np.add.at(dv, T[ok, i], dPv[ok])
    return du, dv


def ortho(v, N):
    return normalize(v - N * (v * N).sum(1, keepdims=True))


def tangent_convention(s):
    """Which UV derivative the shape's stored tangent / bitangent follow: ('dv', 'du') means tangent = dP/dv,
    bitangent = dP/du (what the puddle stores)."""
    du, dv = uv_derivatives(s['pos'], s['uv'], s['tris'])
    du, dv = normalize(du), normalize(dv)
    T, B = normalize(s['tangent']), normalize(s['bitangent'])
    m = {('tan', 'du'): (T * du).sum(1).mean(), ('tan', 'dv'): (T * dv).sum(1).mean(),
         ('bit', 'du'): (B * du).sum(1).mean(), ('bit', 'dv'): (B * dv).sum(1).mean()}
    tan = max(('du', 'dv'), key=lambda d: abs(m[('tan', d)]))
    bit = max(('du', 'dv'), key=lambda d: abs(m[('bit', d)]))
    assert tan != bit and abs(m[('tan', tan)]) > 0.9 and abs(m[('bit', bit)]) > 0.9, m
    return tan, np.sign(m[('tan', tan)]), bit, np.sign(m[('bit', bit)])


def value_noise(P, freq, seed, size=48):
    """Smooth 3D value noise in 0..1 (trilinear over a random lattice, smoothstep weights)."""
    G = np.random.RandomState(seed).rand(size, size, size)
    q = np.asarray(P, float) * freq + 7.3
    i = np.floor(q).astype(int)
    f = q - i
    f = f * f * (3 - 2 * f)
    out = np.zeros(len(q))
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (f[:, 0] if dx else 1 - f[:, 0]) * (f[:, 1] if dy else 1 - f[:, 1]) * (f[:, 2] if dz else 1 - f[:, 2])
                out += w * G[(i[:, 0] + dx) % size, (i[:, 1] + dy) % size, (i[:, 2] + dz) % size]
    return out


def fbm(P, freq, seed):
    return 0.65 * value_noise(P, freq, seed) + 0.35 * value_noise(P, freq * 2.3, seed + 1)


# ---- Sting -----------------------------------------------------------------------------------------------

def goo_material(nif):
    """The goo surface: (shape dict, shader block index, texture paths)."""
    hits = [k for k in nif.find('BSTriShape') if name_of(nif, k) == GOO_SHAPE]
    assert len(hits) == 1, hits
    s = nifse.read_trishape(nif.blocks[hits[0]])
    sh = s['shader']
    tex_i = struct.unpack_from('<i', nif.blocks[sh], nifse.LSP_TEXSET)[0]
    b = nif.blocks[tex_i]
    n = struct.unpack_from('<I', b, 0)[0]
    paths, p = [], 4
    for _ in range(n):
        m = struct.unpack_from('<I', b, p)[0]
        paths.append(b[p + 4:p + 4 + m].decode('latin1'))
        p += 4 + m
    assert GOO_TEXTURE.lower() in paths[0].lower(), paths
    return s, sh, paths


def tip_start(P, step=0.5):
    """Lowest Y from which the blade stays narrower than TIP_WIDTH of its full width: where the point begins."""
    ys = np.arange(P[:, 1].min(), P[:, 1].max(), step)
    widths = []
    for y in ys:
        m = np.abs(P[:, 1] - y) < step
        widths.append(P[m, 0].max() - P[m, 0].min() if m.any() else 0.0)
    widths = np.array(widths)
    narrow = widths < TIP_WIDTH * widths.max()
    k = len(ys)
    while k > 0 and narrow[k - 1]:
        k -= 1
    assert k < len(ys), 'no tapered point found'
    return float(ys[k])


def coat(bl, goo, conv, units_per_uv, grey_range):
    P, T = weld(bl['pos'], bl['tris'])
    P, T = refine(P, T, MAX_EDGE)
    N = vertex_normals(P, T)
    y0 = P[:, 1].min()
    tip = tip_start(P)
    base = tip - COVER_BELOW_TIP * (P[:, 1].max() - y0)
    print('sting coat line: tip from Y %.2f, line at Y %.2f (%.0f%% of the blade from the point)' % (
        tip, base, 100 * (P[:, 1].max() - base) / (P[:, 1].max() - y0)))
    face = np.where(P[:, 2] >= 0, 0.0, 17.0)                      # each face its own ragged line
    cut = base + RAG * (value_noise(np.stack([P[:, 0] + face, np.zeros(len(P)), np.zeros(len(P))], 1), RAG_FREQ, SEED + 5) - 0.5)
    side = np.where(P[:, 2] >= 0, 1.0, 0.6)                      # the back face runs a little shorter
    for x, length, half in DRIPS:
        r = np.clip(1 - ((P[:, 0] - x) / half) ** 2, 0, 1)
        cut -= length * side * np.sqrt(r)                         # a run with a rounded end
    cut = np.maximum(cut, y0 + DRIP_FLOOR)
    above = P[:, 1] - cut
    keep = (above[T] >= 0).all(1)
    T = T[keep]
    used = np.unique(T)
    remap = -np.ones(len(P), int)
    remap[used] = np.arange(len(used))
    P, N, above, T = P[used], N[used], above[used], remap[T]
    depth = OFFSET + LUMP * fbm(P, LUMP_FREQ, SEED)
    taper = np.clip(above / TAPER, 0, 1)
    taper = taper * taper * (3 - 2 * taper)
    D = P + N * np.maximum(depth * taper, MIN_OFFSET)[:, None]
    N2 = vertex_normals(D, T)
    UV = np.stack([D[:, 0], D[:, 1]], 1) / units_per_uv
    du, dv = uv_derivatives(D, UV, T)
    der = {'du': ortho(du, N2), 'dv': ortho(dv, N2)}
    tan = der[conv[0]] * conv[1]
    bit = der[conv[2]] * conv[3]
    lo, hi = grey_range
    g = np.clip(lo + (hi - lo) * fbm(D, 0.6, SEED + 9), 0, 255).astype(np.uint8)
    col = np.stack([g, g, g, np.full(len(g), 255, np.uint8)], 1)
    return D, UV, N2, tan, bit, col, T


def build_sting(blade_nif, goo_nif, template):
    bl = blade(blade_nif)
    gs, gshader, gpaths = goo_material(goo_nif)
    conv = tangent_convention(gs)
    gt, gR, gsc = nifse.transform(goo_nif.blocks[[k for k in goo_nif.find('BSTriShape') if name_of(goo_nif, k) == GOO_SHAPE][0]])
    T = gs['tris']
    e = np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
    dp = np.linalg.norm(gs['pos'][e[:, 0]] - gs['pos'][e[:, 1]], axis=1) * gsc
    duv = np.linalg.norm(gs['uv'][e[:, 0]] - gs['uv'][e[:, 1]], axis=1)
    units = float(np.median(dp[duv > 1e-6] / duv[duv > 1e-6])) / bl['xf'][2]   # in the blade shape's units
    grey = np.percentile(gs['color'][:, 0], GREY_PCT)
    print('sting blade: shape %r, %d triangles, Y %.2f..%.2f' % (bl['name'], len(bl['tris']),
          bl['pos'][np.unique(bl['tris'])][:, 1].min(), bl['pos'][np.unique(bl['tris'])][:, 1].max()))
    print('goo material: %s; %.1f units per UV; vertex grey %d..%d; tangent convention %s' % (
        gpaths[:2], units, grey[0], grey[1], conv))
    D, UV, N, tan, bit, col, T = coat(bl, gs, conv, units, grey)
    print('sting coat: %d vertices, %d triangles, Y %.2f..%.2f, offset %.3f..%.3f' % (
        len(D), len(T), D[:, 1].min(), D[:, 1].max(), 0, OFFSET + LUMP))

    art = nifse.Nif(template)
    root_b, bsx_b = bytes(art.blocks[0]), bytes(art.blocks[1])
    assert art.btype(0) == 'BSFadeNode' and art.btype(1) == 'BSXFlags' and art.string(0) == 'ChillrendEnchFX'
    assert struct.unpack_from('<i', bsx_b, 0)[0] == 1 and art.string(1) == 'BSX'
    art.types, art.type_idx, art.blocks, art.strings, art.roots = [], [], [], [], [0]
    assert art.add_string('StingEnchFX') == 0 and art.add_string('BSX') == 1
    shape_name = art.add_string('StingVenomCoat')
    art.add_block('BSFadeNode', nifse.set_children(bytearray(root_b), [2]))
    art.add_block('BSXFlags', bsx_b)
    art.add_block('BSTriShape', b'')                          # placeholder: the shader index is not known yet
    shader = nifse.copy_lighting_shader(art, goo_nif, gshader)
    t, R, sc = bl['xf']
    art.blocks[2] = bytearray(nifse.write_trishape(
        shape_name, bl['flags'], (t, R, sc), gs['desc'], D, UV, N, tan, bit, col, T, shader, -1))
    return art, dict(blade=bl, coat=(D, T))


# ---- Rise ------------------------------------------------------------------------------------------------

def flame_box(bl):
    t, R, sc = bl['xf']
    W = bl['pos'][np.unique(bl['tris'])] * sc @ R.T + t
    xy = W[:, :2] - W[:, :2].mean(0)
    w, v = np.linalg.eigh(xy.T @ xy)
    axis = v[:, np.argmax(w)]
    tilt = math.degrees(math.atan2(abs(axis[0]), abs(axis[1])))
    assert tilt < MAX_TILT_DEG, 'blade leans %.1f deg: the box would need a rotation' % tilt
    y0, y1 = W[:, 1].min() + FLAME_GAP_BASE, W[:, 1].max() - FLAME_GAP_TIP
    xs = W[:, 0]
    centre = np.array([(xs.min() + xs.max()) / 2, (y0 + y1) / 2, (W[:, 2].min() + W[:, 2].max()) / 2])
    whd = ((xs.max() - xs.min()) * FLAME_WIDTH, y1 - y0, W[:, 2].max() - W[:, 2].min())
    return centre, whd, tilt


def psys_parts(nif, psys):
    f = nifse.particle_system_fields(nif.blocks[psys])
    mods = {}
    for m in f['mods']:
        mods.setdefault(nif.btype(m), []).append(m)
    ctrl = struct.unpack_from('<i', nif.blocks[psys], nifse.av_fields(nif.blocks[psys])['ctrl'])[0]
    emitter_ctlr = None
    while ctrl >= 0:
        if nif.btype(ctrl) == 'NiPSysEmitterCtlr':
            emitter_ctlr = ctrl
        ctrl = struct.unpack_from('<i', nif.blocks[ctrl], 0)[0]
    return f, mods, emitter_ctlr


def build_rise(blade_nif, template, torch):
    bl = blade(blade_nif)
    centre, whd, tilt = flame_box(bl)
    print('rise blade: shape %r, %d triangles; flame box centre %s size %s (tilt %.2f deg)' % (
        bl['name'], len(bl['tris']), centre.round(2), np.round(whd, 2), tilt))
    art = nifse.Nif(template)
    orig = nifse.Nif(template)
    assert art.string(0) == 'ChillrendEnchFX'
    art.strings[0] = b'RiseEnchFX'
    (psys,) = art.find('NiParticleSystem')
    f, mods, ectl = psys_parts(art, psys)
    tsys = [k for k in torch.find('NiParticleSystem') if name_of(torch, k) == FLAME_PSYS]
    assert len(tsys) == 1, tsys
    tf, tmods, _ = psys_parts(torch, tsys[0])
    changed = set()

    def put(k, b):
        art.blocks[k] = bytearray(b)
        changed.add(k)

    # the torch flame's look: shader, alpha, particle data (8-frame atlas, cap raised), colour and size curves
    for k, tk in ((f['shader'], tf['shader']), (f['alpha'], tf['alpha'])):
        assert art.btype(k) == torch.btype(tk) and nifse.net_end(torch.blocks[tk]) == 12
        assert struct.unpack_from('<2i', torch.blocks[tk], 0) == (-1, 0) and struct.unpack_from('<i', torch.blocks[tk], 8)[0] == -1
        put(k, torch.blocks[tk])
    data = bytearray(torch.blocks[tf['data']])
    assert struct.unpack_from('<i', data, 0)[0] == 0 and 0 < struct.unpack_from('<H', data, 4)[0] < MAX_PARTICLES
    struct.pack_into('<H', data, 4, MAX_PARTICLES)
    put(f['data'], data)
    (col,), (tcol,) = mods['BSPSysSimpleColorModifier'], tmods['BSPSysSimpleColorModifier']
    put(col, nifse.set_simple_color_values(art.blocks[col], nifse.simple_color_values(torch.blocks[tcol])))
    (scl,), (tscl,) = mods['BSPSysScaleModifier'], tmods['BSPSysScaleModifier']
    put(scl, nifse.set_scale_values(art.blocks[scl], nifse.scale_values(torch.blocks[tscl])))
    # small, short-lived flames anywhere in the blade box, pushed up in world space
    (emi,) = mods['NiPSysBoxEmitter']
    e = nifse.box_emitter(art.blocks[emi])
    e.update(speed=FLAME_SPEED, speedvar=FLAME_SPEED_VAR, decl=0.0, declvar=math.pi, planar=0.0, planarvar=2 * math.pi,
             radius=FLAME_RADIUS, radiusvar=FLAME_RADIUS_VAR, life=FLAME_LIFE, lifevar=FLAME_LIFE_VAR,
             whd=tuple(float(x) for x in whd))
    put(emi, nifse.set_box_emitter(art.blocks[emi], e))
    (spn,) = mods['NiPSysSpawnModifier']
    put(spn, nifse.set_spawn_life(art.blocks[spn], FLAME_LIFE, FLAME_LIFE_VAR))
    (rot,) = mods['NiPSysRotationModifier']
    put(rot, nifse.set_rotation_speed(art.blocks[rot], 0.0, 0.0))        # flames stay upright
    (grv,) = mods['NiPSysGravityModifier']
    gobj = struct.unpack_from('<i', art.blocks[grv], nifse.MOD_BASE)[0]
    put(grv, nifse.set_gravity(art.blocks[grv], (0.0, 0.0, 1.0), FLAME_GRAVITY, 1))
    t, R, s = nifse.transform(art.blocks[gobj])
    put(gobj, nifse.set_transform(art.blocks[gobj], t, np.eye(3), s))      # the torch's gravity node keeps +Z
    interp = struct.unpack_from('<i', art.blocks[ectl], 26)[0]     # NiTimeController (26) -> interpolator
    assert art.btype(interp) == 'NiFloatInterpolator' and struct.unpack_from('<i', art.blocks[interp], 4)[0] == -1
    b = bytearray(art.blocks[interp])
    struct.pack_into('<f', b, 0, BIRTH_RATE)
    put(interp, b)
    # the emitter node and the particle system sit on the blade box's centre
    for k in (e['obj'], psys):
        t, R, s = nifse.transform(art.blocks[k])
        put(k, nifse.set_transform(art.blocks[k], centre, np.eye(3), 1.0))
    for k in range(len(orig.blocks)):
        if k not in changed:
            assert art.blocks[k] == orig.blocks[k], 'block %d changed' % k
    print('rise: %d of %d blocks changed: %s' % (len(changed), len(art.blocks), sorted(art.btype(k) for k in changed)))
    return art, dict(blade=bl, box=(centre, whd))


# ---- checks, preview, main -------------------------------------------------------------------------------

def check_refs(nif):
    """Every BSTriShape/node/particle reference this tool writes must point inside the file."""
    n = len(nif.blocks)
    for k in nif.find('BSTriShape'):         # refs only: skin, shader, alpha follow the AV object and bound
        o = nifse.av_fields(nif.blocks[k])['end']
        assert all(-1 <= struct.unpack_from('<i', nif.blocks[k], o + at)[0] < n for at in (16, 20, 24))
    for k in range(n):
        if nif.btype(k) in ('BSFadeNode', 'NiNode', 'NiBillboardNode'):
            assert all(-1 <= c < n for c in nifse.node_children(nif.blocks[k])[1])


def preview(path, sting, rise):
    from PIL import Image, ImageDraw
    SC = 16
    tiles = []
    for tag, info in (('Sting', sting), ('Rise', rise)):
        bl = info['blade']
        t, R, sc = bl['xf']
        W = bl['pos'] * sc @ R.T + t
        lo, hi = W[np.unique(bl['tris'])].min(0) - 3, W[np.unique(bl['tris'])].max(0) + 3
        for a, b in ((0, 1), (2, 1)):
            w, h = int((hi[a] - lo[a]) * SC), int((hi[b] - lo[b]) * SC)
            im = Image.new('RGB', (w, h + 16), 'white')
            d = ImageDraw.Draw(im)
            tr = lambda p: ((p[a] - lo[a]) * SC, (hi[b] - p[b]) * SC + 16)
            for tri in bl['tris']:
                d.polygon([tr(W[i]) for i in tri], fill=(170, 170, 180), outline=(90, 90, 100))
            if 'coat' in info:
                D, T = info['coat']
                Dw = D * sc @ R.T + t
                for tri in T:
                    d.polygon([tr(Dw[i]) for i in tri], fill=(60, 200, 90), outline=(30, 120, 50))
            if 'box' in info:
                c, whd = info['box']
                half = np.array(whd) / 2
                (x0, y0), (x1, y1) = tr(c - half), tr(c + half)
                d.rectangle([min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)], outline=(240, 120, 0), width=2)
            d.text((2, 2), '%s %s' % (tag, 'front' if a == 0 else 'side'), fill=(0, 0, 0))
            tiles.append(im)
    W_ = sum(i.width for i in tiles) + 10 * len(tiles)
    out = Image.new('RGB', (W_, max(i.height for i in tiles)), 'white')
    x = 0
    for i in tiles:
        out.paste(i, (x, 0))
        x += i.width + 10
    out.save(path)
    print('preview ->', path)


def build_burst(nif):
    """FS's gore burst minus its meat: the chunk nodes and the chunk emitter leave the root's child list. Detached,
    not hidden: 14 chunks carry Havok bodies, which a hidden node would still simulate."""
    root = nif.roots[0]
    assert nif.btype(root) == 'BSFadeNode'
    _, kids = nifse.node_children(nif.blocks[root])
    keep, drop = [], []
    for c in kids:
        (drop if c >= 0 and name_of(nif, c).startswith(BURST_DROP) else keep).append(c)
    names = sorted(name_of(nif, c) for c in drop)
    assert sum(n.startswith('meatChunk') for n in names) == 14 and 'pBloodMeatChunk01-Emitter' in names, names
    nif.blocks[root] = nifse.set_children(nif.blocks[root], keep)
    attached = set()

    def walk(k):
        attached.add(k)
        if nif.btype(k) in ('BSFadeNode', 'NiNode'):
            for c in nifse.node_children(nif.blocks[k])[1]:
                if c >= 0:
                    walk(c)
    walk(root)
    psys = sorted(name_of(nif, k) for k in attached if nif.btype(k) == 'NiParticleSystem')
    assert psys == sorted(BURST_KEEP_PSYS), psys
    assert not any(nif.btype(k) in ('BSTriShape', 'bhkCollisionObject') for k in attached), 'meat left on the scene'
    print('blood boil burst: %d root children taken off (%s ...), particle systems left: %s'
          % (len(drop), ', '.join(names[:3]), ', '.join(psys)))
    return nif


def main_shape(nif, prefix):
    """The single BSTriShape whose name starts with `prefix`, read."""
    hit = [k for k in nif.find('BSTriShape') if name_of(nif, k).startswith(prefix)]
    assert len(hit) == 1, (prefix, len(hit))
    return nifse.read_trishape(nif.blocks[hit[0]])


def build_sting_mesh(nif):
    """Sting's own mesh (curator 2026-11-13: always visible, so a copy of Pretty's mesh ships): Pretty's assassin
    blade unchanged + one new shape, the metal spider of spider.py clutching the ring pommel, in blackened steel: its
    own copy of the blade's shader (never shared: two shapes on one lighting shader froze the game, Clockwork Thunder)
    with its UVs on a plain patch of the blade's metal, so it has the blade's colour, env mask and sheen."""
    import spider
    main = [k for k in nif.find('BSTriShape') if name_of(nif, k).startswith('1stPerson')]
    assert len(main) == 1, 'no single main shape'
    k = main[0]
    s = nifse.read_trishape(nif.blocks[k])
    t, R, sc = nifse.transform(nif.blocks[k])
    assert np.allclose(t, 0) and np.allclose(R, np.eye(3)) and abs(sc - 1) < 1e-6, 'main shape is transformed'
    P, T = s['pos'], s['tris']
    plate = (P[:, 1] > -11.6) & (P[:, 1] < -9.6)
    face = float(np.abs(P[plate, 2]).max())

    def rim(y):
        sel = (np.abs(P[:, 1] - y) < 0.2) & (np.abs(P[:, 2]) <= face + 0.05)
        return float(np.abs(P[sel, 0]).max())
    assert 0.3 < face < 0.5 and 1.7 < rim(-10.0) < 2.1, ('the pommel changed shape', face, rim(-10.0))
    V, N, Tri, legs = spider.make(rim, face)
    clear = spider.clearance(legs, spider.surface_points(P, T))
    assert clear >= SPIDER_MIN_CLEARANCE, 'a leg sinks into the pommel (%.2f radii)' % clear
    # UVs: one plain patch of the blade's metal, inside its largest UV triangle (the blade's 75 triangles are slivers;
    # a patch near the island's edge would read texture outside the blade)
    blade_t = np.where((P[T][:, :, 1] > 8).all(1) & (P[T][:, :, 1] < 38).all(1))[0]
    tuv = s['uv'][T[blade_t]]
    area = 0.5 * np.abs((tuv[:, 1, 0] - tuv[:, 0, 0]) * (tuv[:, 2, 1] - tuv[:, 0, 1])
                        - (tuv[:, 2, 0] - tuv[:, 0, 0]) * (tuv[:, 1, 1] - tuv[:, 0, 1]))
    best = int(np.argmax(area))
    u0, v0 = tuv[best].mean(0)
    inradius = 2 * area[best] / sum(np.linalg.norm(tuv[best][i] - tuv[best][(i + 1) % 3]) for i in range(3))
    off = (V[:, :2] - V[:, :2].mean(0)) * SPIDER_UV_SCALE
    assert np.linalg.norm(off, axis=1).max() < 0.8 * inradius, "the spider's UV patch spills out of the blade"
    uv = np.array([u0, v0]) + off
    # tangent frame in the mesh's own convention (stored tangent / bitangent = dP/du or dP/dv, signed)
    tan_axis, tan_sign, bit_axis, bit_sign = tangent_convention(s)
    axis = {'du': np.array([1.0, 0.0, 0.0]), 'dv': np.array([0.0, 1.0, 0.0])}

    def frame(d, alt):
        f = d[None, :] - N * (N @ d)[:, None]
        weak = np.linalg.norm(f, axis=1) < 1e-3
        f[weak] = np.cross(N[weak], alt)
        return normalize(f)
    tangent = tan_sign * frame(axis[tan_axis], axis[bit_axis])
    bitangent = bit_sign * frame(axis[bit_axis], axis[tan_axis])
    # the blade's diffuse -> Sting's own (the grip's leather very dark green, sting_texture); the texture set is the
    # blade shape's alone (asserted), and the spider's copy below inherits the new path (its patch is plain metal)
    ts = struct.unpack_from('<i', nif.blocks[s['shader']], nifse.LSP_TEXSET)[0]
    users = [k2 for k2 in nif.find('BSLightingShaderProperty')
             if struct.unpack_from('<i', nif.blocks[k2], nifse.LSP_TEXSET)[0] == ts]
    assert users == [s['shader']], 'the blade texture set is shared'
    paths = nifse.texture_paths(nif.blocks[ts])
    assert paths[0].lower() == chr(92).join(['textures', 'billyro', 'assassin', 'blade.dds']), paths[0]
    paths[0] = OUT_STING_D.replace('/', chr(92))
    nif.blocks[ts] = nifse.texture_set(paths)
    # its own shader + texture set (+ controllers), copied from the blade's
    shader = nifse.copy_lighting_shader(nif, nif, s['shader'])
    av_flags = struct.unpack_from('<I', nif.blocks[k], s['av']['flags'])[0]
    assert np.isfinite(uv).all() and np.isfinite(tangent).all() and np.isfinite(bitangent).all()
    shape = nifse.write_trishape(nif.add_string('ZP_StingSpider'), av_flags, (np.zeros(3), np.eye(3), 1.0), s['desc'],
                                 V, uv, N, tangent, bitangent, None, Tri, shader, -1)
    new = nif.add_block('BSTriShape', shape)
    root = nif.roots[0]
    _, kids = nifse.node_children(nif.blocks[root])
    nif.blocks[root] = nifse.set_children(nif.blocks[root], kids + [new])
    print('sting spider: %d vertices, %d triangles on the pommel ring (face %.3f, rim %.2f..%.2f), legs clear by %.2f '
          'radii, UV patch at %.3f %.3f' % (len(V), len(Tri), face, rim(-11.4), rim(-10.0), clear, u0, v0))
    return nif


def add_ornament(nif, blade_k, name, V, N, T, xf):
    """Append a gold ornament shape to the root, with transform xf (the blade's): its own copy of the blade's
    shader (never shared: Clockwork Thunder's freeze) with the plain gold texture set, planar UVs, tangents in the
    blade's own convention."""
    s = nifse.read_trishape(nif.blocks[blade_k])
    b = nif.blocks[s['shader']]
    assert struct.unpack_from('<I', b, 0)[0] == 1 and not struct.unpack_from('<I', b, 16)[0] & 0x1000, \
        'the blade shader is no longer a tangent-space environment-map shader'
    uv = 0.5 + (V[:, :2] - V[:, :2].mean(0)) * ORNAMENT_UV
    assert (uv > 0).all() and (uv < 1).all()
    tan_axis, tan_sign, bit_axis, bit_sign = tangent_convention(s)
    axis = {'du': np.array([1.0, 0.0, 0.0]), 'dv': np.array([0.0, 1.0, 0.0])}

    def frame(d, alt):
        f = d[None, :] - N * (N @ d)[:, None]
        weak = np.linalg.norm(f, axis=1) < 1e-3
        f[weak] = np.cross(N[weak], alt)
        return normalize(f)
    tangent = tan_sign * frame(axis[tan_axis], axis[bit_axis])
    bitangent = bit_sign * frame(axis[bit_axis], axis[tan_axis])
    shader = nifse.copy_lighting_shader(nif, nif, s['shader'])
    ts = struct.unpack_from('<i', nif.blocks[shader], nifse.LSP_TEXSET)[0]
    paths = nifse.texture_paths(nif.blocks[ts])
    assert paths[4].lower().startswith('textures' + chr(92) + 'cubemaps') and paths[5].lower().endswith('_m.dds'), paths
    for slot, rel in ((0, OUT_ORN_D), (1, OUT_ORN_N), (4, OUT_GOLD_E), (5, OUT_ORN_M)):
        paths[slot] = rel.replace('/', chr(92))
    nif.blocks[ts] = nifse.texture_set(paths)
    av_flags = struct.unpack_from('<I', nif.blocks[blade_k], s['av']['flags'])[0]
    assert np.isfinite(tangent).all() and np.isfinite(bitangent).all()
    shape = nifse.write_trishape(nif.add_string(name), av_flags, xf, s['desc'],
                                 V, uv, N, tangent, bitangent, None, T, shader, -1)
    new = nif.add_block('BSTriShape', shape)
    root = nif.roots[0]
    _, kids = nifse.node_children(nif.blocks[root])
    nif.blocks[root] = nifse.set_children(nif.blocks[root], kids + [new])


def build_rise_mesh(nif):
    """Rise's own mesh (curator: "the pommel should be replaced with the angel", the wings "overlaying the existing
    crossguard"): Pretty's Aeterna dagger without its pommel knob, + the angel on a socket capping the grip's ring
    band, + a wing sheathing each guard arm (angel.py)."""
    import angel
    k = [k for k in nif.find('BSTriShape') if name_of(nif, k).startswith('Noble')]
    assert len(k) == 1
    k = k[0]
    s = nifse.read_trishape(nif.blocks[k])
    xf = nifse.transform(nif.blocks[k])     # Pretty's: (0, -0.6, 0), scale 0.95 on every shape; the ornaments
    root = nif.roots[0]                     # are built in the blade's own space and take the same transform
    assert k in nifse.node_children(nif.blocks[root])[1], 'the blade is not a child of the root'
    P, T = s['pos'], s['tris']
    # the mesh's pieces (triangles joined through shared positions): the knob is the one holding the lowest point,
    # the ring band the one right above it, the guard the one reaching furthest out in x
    _, wid = np.unique(np.round(P * 1e4).astype(np.int64), axis=0, return_inverse=True)
    lab = islands(T, wid.ravel())
    knob = lab[np.where((T == int(np.argmin(P[:, 1]))).any(1))[0][0]]
    kp = P[T[lab == knob]].reshape(-1, 3)
    assert (lab == knob).sum() == KNOB_TRIS and abs(kp[:, 1].min() - RISE_POMMEL_Y) < 0.05, \
        ('the pommel knob changed', (lab == knob).sum(), kp[:, 1].min())
    band = [l for l in np.unique(lab) if l != knob and np.abs(P[T[lab == l]][..., 1].min() - BAND_BOTTOM) < 0.05]
    assert len(band) == 1, 'no single ring band above the knob'
    bp = P[T[lab == band[0]]].reshape(-1, 3)
    base = np.array([(bp[:, 0].min() + bp[:, 0].max()) / 2, bp[:, 1].min(), (bp[:, 2].min() + bp[:, 2].max()) / 2])
    socket = ((bp[:, 0].max() - bp[:, 0].min()) / 2, (bp[:, 2].max() - bp[:, 2].min()) / 2)
    nif.blocks[k] = nifse.set_triangles(nif.blocks[k], T[lab != knob])
    guard = max(np.unique(lab), key=lambda l: np.abs(P[T[lab == l]][..., 0]).max())
    gt = P[T[lab == guard]]                                   # the guard's triangles (n, 3, 3)
    gp = np.unique(gt.reshape(-1, 3), axis=0)
    right, left = float(gp[:, 0].max()), float(gp[:, 0].min())
    assert abs(right - RISE_GUARD_X[0]) < 0.15 and abs(left - RISE_GUARD_X[1]) < 0.15, ('the guard moved', right, left)

    def section(x):
        """Where the plane X = x cuts the guard's triangles (its long faces have few vertices: slice, don't sample)."""
        pts = []
        for i, j in ((0, 1), (1, 2), (2, 0)):
            a, b = gt[:, i], gt[:, j]
            cross = (a[:, 0] - x) * (b[:, 0] - x) <= 0
            cross &= np.abs(b[:, 0] - a[:, 0]) > 1e-9
            f = (x - a[cross, 0]) / (b[cross, 0] - a[cross, 0])
            pts.append(a[cross] + f[:, None] * (b[cross] - a[cross]))
        return np.concatenate(pts)
    wings_parts, outside = [], []
    for sx, end in ((1.0, right), (-1.0, left)):
        arm = gp[gp[:, 0] * sx > GUARD_ARM_FROM - 0.3]
        xs = np.arange(GUARD_ARM_FROM, abs(end) - 0.02, 0.25)
        xs = np.append(xs, abs(end) - 0.02)
        env = []
        for x in xs:          # the arm's section at x, widest of x +- 0.15: y centre, y half, z half
            cut = np.concatenate([section(sx * (x + d)) for d in (-0.15, 0.0, 0.15)])
            assert len(cut) >= 4, ('the guard arm has no section at', sx * x)
            env.append((x, (cut[:, 1].min() + cut[:, 1].max()) / 2, (cut[:, 1].max() - cut[:, 1].min()) / 2,
                        np.abs(cut[:, 2]).max()))
        wings_parts += angel.overlay_wing(env, sx)
        C, yh, zh = angel.overlay_wing.last
        test = arm[np.abs(arm[:, 0]) >= GUARD_ARM_FROM]
        outside.append(int((angel.inside_sheath(test, C, yh, zh) > 1.0).sum()))
        outside.append(len(test))
    assert outside[0] == 0 and outside[2] == 0, ('guard arm vertices outside the wing sheath (right, of, left, of)',
                                                 outside)
    sun = angel.merge(angel.sun_pommel(base, socket))     # curator: "change the angel for just a Sun"
    wings = angel.merge(wings_parts)
    for nm, (V, N, Tr) in (('ZP_RiseSun', sun), ('ZP_RiseWings', wings)):
        add_ornament(nif, k, nm, V, N, Tr, xf)
    print('rise: pommel knob removed (%d triangles); sun %d vertices / %d triangles on a socket capping the ring '
          'band (y %.2f, half widths %.2f x %.2f), down to y %.2f, x %.2f .. %.2f; wings %d / %d sheathing the guard '
          'arms (all %d + %d arm vertices inside), out to x %.1f / %.1f' % (
              KNOB_TRIS, len(sun[0]), len(sun[2]), base[1], socket[0], socket[1], sun[0][:, 1].min(),
              sun[0][:, 0].min(), sun[0][:, 0].max(), len(wings[0]), len(wings[2]), outside[1], outside[3],
              wings[0][:, 0].max(), wings[0][:, 0].min()))
    return nif


def ornament_textures(out_root):
    """The ornaments' plain polished gold: diffuse, a flat normal map carrying the highlight mask, a Complex
    Material mask (as the blade gold's metal); the gold cubemap is the blade's."""
    size = (64, 64)
    write_texture(np.broadcast_to(np.array(ORNAMENT_GOLD, np.float32), size + (3,)).copy(),
                  os.path.join(out_root, *OUT_ORN_D.split('/')), 'BC7_UNORM')
    write_texture(np.broadcast_to(np.array([0.5, 0.5, 1.0, ORNAMENT_SPEC], np.float32), size + (4,)).copy(),
                  os.path.join(out_root, *OUT_ORN_N.split('/')), 'BC7_UNORM')
    mask_path = os.path.join(out_root, *OUT_ORN_M.split('/'))
    write_texture(np.broadcast_to(np.array(list(COMPLEX) + [0.0], np.float32), size + (4,)).copy(), mask_path,
                  'BC7_UNORM')
    mip = smallest_mip(mask_path)
    eps = 4.0 / 255.0
    assert mip[3] < 1 - eps and max(abs(mip[0] - mip[1]), abs(mip[0] - mip[2]), abs(mip[1] - mip[2])) >= 2 * eps, mip
    print('rise ornament gold: diffuse %s, highlight %.2f, complex mask 1x1 mip %s' % (
        ORNAMENT_GOLD, ORNAMENT_SPEC, ' '.join('%.3f' % v for v in mip)))


def effect_shader(b):
    """SE BSEffectShaderProperty: offsets of its base colour and greyscale (palette) texture. Layout: NiObjectNET,
    flags 1+2, UV offset + scale, source texture, 4 bytes (clamp, lighting influence, env min LOD, unused), falloff
    4f, base colour 4f, base colour scale, soft falloff depth, greyscale texture; SE ends there."""
    o = nifse.net_end(b) + 8 + 16
    o += 4 + struct.unpack_from('<I', b, o)[0]
    o += 4 + 16
    base_at = o
    grey_at = o + 16 + 8
    n = struct.unpack_from('<I', b, grey_at)[0]
    assert grey_at + 4 + n == len(b), 'not an SE effect shader layout'
    return base_at, grey_at, bytes(b[grey_at + 4:grey_at + 4 + n]).decode('latin1')


def set_palette(nif, k, path):
    b = nif.blocks[k]
    _, grey_at, old = effect_shader(b)
    new = path.encode('latin1')
    nif.blocks[k] = bytearray(b[:grey_at]) + struct.pack('<I', len(new)) + new
    return old


def build_mote(nif):
    """Rise's mote of sunlight: Enderal's Mage Light orb, its palette layer on GradSunMote, its glow and glare
    layers' base colour MOTE_TINT. Nothing else changes."""
    swapped, tinted = 0, 0
    for k in nif.find('BSEffectShaderProperty'):
        base_at, _, grey = effect_shader(nif.blocks[k])
        if grey.lower().endswith(chr(92) + 'gradlightspell.dds'):
            set_palette(nif, k, PALETTES['textures/effects/gradients/gradlightspell.dds'][0].replace('/', chr(92)))
            swapped += 1
        else:
            c = struct.unpack_from('<4f', nif.blocks[k], base_at)
            struct.pack_into('<3f', nif.blocks[k], base_at, *[c[i] * MOTE_TINT[i] for i in range(3)])
            tinted += 1
    assert swapped == 1 and tinted == 4, (swapped, tinted)
    print('rise mote: Mage Light orb, palette layer -> sun gold, %d glow/glare layers tinted %s' % (tinted, MOTE_TINT))
    return nif


def build_spider_burst(nif):
    """The spiderling's death burst: Blood Boil's burst (build_burst's blood drops and streams) on the venom palettes,
    shrunk to SPIDER_BURST_SCALE."""
    swapped = []
    for k in nif.find('BSEffectShaderProperty'):
        _, _, grey = effect_shader(nif.blocks[k])
        key = 'textures/effects/gradients/' + grey.replace(chr(92), '/').split('/')[-1]
        match = [src for src in PALETTES if src.lower() == key.lower()]
        if match and 'Venom' in PALETTES[match[0]][0]:
            swapped.append(set_palette(nif, k, PALETTES[match[0]][0].replace('/', chr(92))))
    assert len(swapped) == 3, swapped
    root = nif.roots[0]
    t, R, _ = nifse.transform(nif.blocks[root])
    nif.blocks[root] = nifse.set_transform(nif.blocks[root], t, R, SPIDER_BURST_SCALE)
    print('spider burst: Blood Boil burst on the venom palettes (%d layers), scale %.2f' % (len(swapped), SPIDER_BURST_SCALE))
    return nif


def build_nova(nif):
    """The mote's fire nova: Fire Storm's ring of flame (Enderal's Wayfarer nova) scaled so its reach - the mesh's
    own BlastRadiusNode - is the nova's damage radius (ZP_RiseMoteEffect's Radius): a small, weak nova."""
    import re
    radius = float(re.search(r'^Float Property Radius = ([\d.]+) AutoReadOnly', open(NOVA_SCRIPT).read(), re.M).group(1))
    marker = [k for k in nif.find('NiNode') if name_of(nif, k) == NOVA_MARKER]
    assert len(marker) == 1, 'no single ' + NOVA_MARKER
    reach = float(np.linalg.norm(nifse.transform(nif.blocks[marker[0]])[0][:2]))
    assert 500 < reach < 700, ('the ring changed size', reach)
    root = nif.roots[0]
    t, R, sc = nifse.transform(nif.blocks[root])
    assert abs(sc - 1) < 1e-6
    nif.blocks[root] = nifse.set_transform(nif.blocks[root], t, R, radius / reach)
    print('fire nova: Fire Storm ring, reach %.0f -> %.0f (scale %.3f)' % (reach, radius, radius / reach))
    return nif


def build_web(nif):
    """The Webbed effect's strands (see WEB_SRC): no collision (the root's link and the collision object's target
    both cleared, so the loader cannot re-attach it), BSXFlags without Havok/Articulated (ExternalEmit kept), the
    empty blast node off the root, the root scaled to WEB_SCALE."""
    root = nif.roots[0]
    assert name_of(nif, root) == 'FXSpiderwebHitStrip01', name_of(nif, root)
    f = nifse.av_fields(nif.blocks[root])
    struct.pack_into('<i', nif.blocks[root], f['coll'], -1)
    for k in nif.find('bhkCollisionObject'):
        struct.pack_into('<i', nif.blocks[k], 0, -1)             # NiCollisionObject's target
    bsx = nif.find('BSXFlags')
    assert len(bsx) == 1 and struct.unpack_from('<I', nif.blocks[bsx[0]], len(nif.blocks[bsx[0]]) - 4)[0] == 642
    struct.pack_into('<I', nif.blocks[bsx[0]], len(nif.blocks[bsx[0]]) - 4, 642 & ~(2 | 128))
    _, kids = nifse.node_children(nif.blocks[root])
    keep = [c for c in kids if nif.btype(c) != 'BSBlastNode']
    assert len(keep) == len(kids) - 1
    nif.blocks[root] = nifse.set_children(nif.blocks[root], keep)
    t, R, sc = nifse.transform(nif.blocks[root])
    nif.blocks[root] = nifse.set_transform(nif.blocks[root], t, R, WEB_SCALE)
    print('spider web: vanilla web strip without collision / havok / blast node, scale %.2f (about %.0f tall)'
          % (WEB_SCALE, 281 * WEB_SCALE))
    return nif


def palettes(mods_dir, out_root):
    """Bethesda's palettes recoloured by luminance (alpha kept), for the spider burst and the mote."""
    for src, (out, stops) in PALETTES.items():
        where, raw = winner(mods_dir, [], src, TEX_BSAS)            # the game's own, never a replacer
        img = load_image(raw)
        lum = img[..., :3] @ np.array([0.299, 0.587, 0.114])
        lum = (lum - lum.min()) / max(lum.max() - lum.min(), 1e-6)
        rgba = np.concatenate([ramp(lum, stops), img[..., 3:4]], -1)
        write_texture(rgba, os.path.join(out_root, *out.split('/')), 'BC3_UNORM')
        print('palette %s (%s, %dx%d) -> %s' % (src.split('/')[-1], where, img.shape[1], img.shape[0], out.split('/')[-1]))


def readback(path):
    """An independent reader: PyNifly must open the file and see the coat's geometry and textures."""
    sys.path.insert(0, TOOLS['pynifly'])
    from pyn.pynifly import NifFile
    nif = NifFile(path)
    return [(s.name, len(s.verts), len(s.tris), s.textures.get('Diffuse')) for s in nif.shapes]


# ---- Rise's gold ------------------------------------------------------------------------------------------

def texconv():
    p = os.path.join(os.path.dirname(TOOLS['xedit']), 'Edit Scripts', 'Texconvx64.exe')
    assert os.path.isfile(p), p
    return p


def run_texconv(args):
    r = subprocess.run([texconv(), '-nologo', '-y'] + args, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def load_image(raw):
    """A 2D DDS -> float RGBA array (texconv to PNG, so every BC format decodes the same way)."""
    from PIL import Image
    d = tempfile.mkdtemp()
    src = os.path.join(d, 'src.dds')
    open(src, 'wb').write(raw)
    run_texconv(['-ft', 'png', '-f', 'R8G8B8A8_UNORM', '-m', '1', '-o', d, src])
    a = np.asarray(Image.open(os.path.join(d, 'src.png')).convert('RGBA'), np.float32) / 255.0
    shutil.rmtree(d)
    return a


def write_texture(rgb, out_path, fmt):
    """float RGB or RGBA 0..1 -> DDS with a full mip chain."""
    from PIL import Image
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    d = tempfile.mkdtemp()
    png = os.path.join(d, os.path.splitext(os.path.basename(out_path))[0] + '.png')
    Image.fromarray(np.clip(rgb * 255.0 + 0.5, 0, 255).astype(np.uint8), 'RGBA' if rgb.shape[-1] == 4 else 'RGB').save(png)
    # RGBA: mips filter alpha on its own (-sepalpha). texconv's default weights colour by alpha, so a mask whose
    # alpha is 0 got black mips: build 2's Complex Material mask was grey (refused) and reflected nothing past mip 0
    run_texconv(['-f', fmt, '-m', '0'] + (['-sepalpha'] if rgb.shape[-1] == 4 else []) + ['-o', d, png])
    shutil.move(png[:-4] + '.dds', out_path)
    shutil.rmtree(d)


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def ramp(t, stops):
    xs = [p for p, _ in stops]
    cols = np.array([c for _, c in stops])
    return np.stack([np.interp(t, xs, cols[:, i]) for i in range(3)], -1)


def pretty(mods_dir, mods, rel):
    src, raw = winner(mods_dir, mods, rel, TEX_BSAS)
    if src != EXPECT_SOURCE:
        sys.exit('%s now comes from %s, not %s' % (rel, src, EXPECT_SOURCE))
    return load_image(raw)


def gold_set(mods_dir, mods, out_root, label, diffuse_rel, normal_rel, mask_rel, out_d, out_n, out_m, grip=None):
    """One of Pretty's texture sets with its metal (Pretty's own env mask) turned to polished gold: the gold diffuse,
    Pretty's normal map with the metal's highlight mask (alpha) raised, and a Complex Material mask (COMPLEX: gold
    metal reflecting Dynamic Cubemaps' live surroundings). Leather keeps Pretty's diffuse and highlights, and no
    reflection; with `grip` = (shape, grip Y range, colour, contrast) the grip's leather is recoloured."""
    from PIL import Image
    d = pretty(mods_dir, mods, diffuse_rel)
    nrm = pretty(mods_dir, mods, normal_rel)
    m = pretty(mods_dir, mods, mask_rel)[..., 0]
    m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).resize(d.shape[1::-1], Image.BILINEAR), np.float32) / 255
    metal = smoothstep(METAL_MASK[0], METAL_MASK[1], m)
    on = metal > 0.5
    if grip:
        shape, grip_y, colour, contrast = grip
        d = d.copy()
        d[..., :3] = recolor_leather(d, grip_mask(shape, grip_y, d, metal, label), colour, contrast, label)
    lum = d[..., :3] @ np.array([0.299, 0.587, 0.114])
    lo, hi = np.percentile(lum[on], [5, 95])
    rgb = ramp(np.clip((lum - lo) / (hi - lo), 0, 1), GOLD_RAMP) * metal[..., None] + d[..., :3] * (1 - metal[..., None])
    write_texture(rgb, os.path.join(out_root, *out_d.split('/')), 'BC7_UNORM')
    assert nrm.shape[:2] == d.shape[:2], (nrm.shape, d.shape)
    a0 = nrm[..., 3]
    spec = np.clip(SPEC[0] + SPEC[1] * (a0 - SPEC[2]), 0, 1)
    n_out = nrm.copy()
    n_out[..., 3] = spec * metal + a0 * (1 - metal)
    write_texture(n_out, os.path.join(out_root, *out_n.split('/')), 'BC7_UNORM')
    mlo, mhi = np.percentile(m[on], [5, 95])
    worn = 1.0 - np.clip((m - mlo) / max(mhi - mlo, 1e-3), 0, 1)
    gloss = COMPLEX[1] - COMPLEX_GLOSS_VAR * worn
    cm = np.stack([COMPLEX[0] * metal,                               # R: reflects
                   gloss * metal + LEATHER_GLOSS * (1 - metal),      # G: glossiness
                   COMPLEX[2] * metal,                               # B: metalness
                   np.zeros_like(metal)], -1)                        # A: no parallax (and marks it complex)
    mask_path = os.path.join(out_root, *out_m.split('/'))
    write_texture(cm, mask_path, 'BC7_UNORM')
    back = load_image(open(mask_path, 'rb').read())
    mip = smallest_mip(mask_path)
    eps = 4.0 / 255.0
    # Bottled Shaders' own test, on the mip it samples (SampleLevel 15 = the 1x1 mip): alpha below 1 - eps, and
    # not grey (every channel pair within eps); then per pixel G above eps
    assert back[..., 3].max() <= eps and mip[3] < 1 - eps, 'alpha lost: the mask would not be complex'
    assert max(abs(mip[0] - mip[1]), abs(mip[0] - mip[2]), abs(mip[1] - mip[2])) >= 2 * eps,         'grey 1x1 mip %s: Bottled Shaders would read a plain env mask' % mip
    assert (back[..., 1][on] > eps).all()
    print('%s gold: %d%% metal; metal luminance %.2f..%.2f onto the gold ramp (diffuse mean on metal %s); highlight '
          'mask on metal %.2f -> %.2f; complex mask on metal RGBA %s, 1x1 mip %s' % (
              label, 100 * metal.mean(), lo, hi, ' '.join('%.2f' % v for v in rgb[on].mean(0)), a0[on].mean(),
              n_out[..., 3][on].mean(), ' '.join('%.2f' % v for v in back[on].mean(0)),
              ' '.join('%.3f' % v for v in mip)))
    return rgb, cm


def grip_mask(shape, grip_y, rgb, metal, label):
    """Texture-space weight 0..1 of the grip's leather (see STING_GRIP_Y): its UV islands rasterised (wrapped UVs,
    dilated 3 texels into their padding), each kept only when LEATHER_ISLAND of its texels are leather, times the
    texel's own leather weight (warm, not metal)."""
    from PIL import Image, ImageDraw, ImageFilter
    P, T, UV = shape['pos'], shape['tris'], shape['uv']
    H, W = rgb.shape[:2]
    _, uv_id = np.unique(np.round(UV * 1e5).astype(np.int64), axis=0, return_inverse=True)
    lab = islands(T, uv_id.ravel())     # UV islands: vertices joined where their UVs meet (seams split positions)
    yc = P[T][:, :, 1]
    grip = (yc >= grip_y[0]).all(1) & (yc <= grip_y[1]).all(1)
    warm = smoothstep(LEATHER_WARM * 0.5, LEATHER_WARM * 2, rgb[..., 0] - rgb[..., 2]) * (1 - metal)
    out = np.zeros((H, W), np.float32)
    kept, dropped = [], []
    for isl in np.unique(lab[grip]):
        im = Image.new('L', (W, H), 0)
        dr = ImageDraw.Draw(im)
        for t in np.where(lab == isl)[0]:
            uv = UV[T[t]]
            shift = np.floor(uv.min(0))
            dr.polygon([((u - shift[0]) * W, (v - shift[1]) * H) for u, v in uv], fill=255)
        inside = np.asarray(im) > 0
        share = float((warm[inside] > 0.5).mean()) if inside.any() else 0.0
        if share >= LEATHER_ISLAND:
            grown = np.asarray(im.filter(ImageFilter.MaxFilter(7)), np.float32) / 255
            out = np.maximum(out, grown)
            kept.append(round(share, 2))
        else:
            dropped.append(round(share, 2))
    assert kept, label + ': no leather island on the grip'
    print('%s grip: %d leather islands kept (leather share %s), %d dropped (%s)' % (label, len(kept), kept, len(dropped), dropped))
    return out * warm


def recolor_leather(rgb, weight, colour, contrast, label):
    """The leather under `weight` moved to `colour`, brightness relative to its own 75th percentile kept at
    `contrast` of its depth."""
    lum = rgb[..., :3] @ np.array([0.299, 0.587, 0.114])
    sel = weight > 0.5
    ref = float(np.percentile(lum[sel], 75))
    rel = 1.0 - contrast * (1.0 - lum / ref)
    new = np.clip(np.array(colour)[None, None, :] * rel[..., None], 0, 1)
    out = rgb[..., :3] * (1 - weight[..., None]) + new * weight[..., None]
    print('%s leather: %d texels, %.2f..%.2f of its 75th-percentile brightness %.3f -> mean %s' % (
        label, int(sel.sum()), np.percentile(lum[sel] / ref, 5), np.percentile(lum[sel] / ref, 95), ref,
        ' '.join('%.3f' % v for v in out[sel].mean(0))))
    return out


def sting_texture(mods_dir, mods, out_root, shape):
    """Sting's diffuse: Pretty's blade.dds with the grip's leather very dark green (Sting.nif points at it)."""
    d = pretty(mods_dir, mods, 'textures/billyro/assassin/blade.dds')
    assert d[..., 3].min() == 1.0, 'the blade diffuse has an alpha now'
    w = grip_mask(shape, STING_GRIP_Y, d, np.zeros(d.shape[:2], np.float32), 'sting')
    rgb = recolor_leather(d, w, STING_LEATHER[0], STING_LEATHER[1], 'sting')
    write_texture(rgb, os.path.join(out_root, *OUT_STING_D.split('/')), 'BC7_UNORM')


def smallest_mip(path):
    """The 1x1 mip of a 2D DDS as RGBA floats (decoded by texconv with its whole mip chain: the last pixel)."""
    d = tempfile.mkdtemp()
    src = os.path.join(d, 'm.dds')
    shutil.copy(path, src)
    o = os.path.join(d, 'o')
    os.makedirs(o)
    run_texconv(['-f', 'R8G8B8A8_UNORM', '-o', o, src])
    b = open(os.path.join(o, 'm.dds'), 'rb').read()
    shutil.rmtree(d)
    assert struct.unpack_from('<I', b, 28)[0] > 1, 'no mip chain'
    return np.frombuffer(b[-4:], np.uint8).astype(np.float32) / 255.0


def gold_textures(mods_dir, mods, out_root, rise_shape):
    """Rise's blade and scabbard in polished gold (the grip's leather ivory), and the gold cubemap both texture sets
    reflect (the scabbard's shader has no environment mapping, so only the blade reflects it). Returns the blade's
    diffuse and mask."""
    out = gold_set(mods_dir, mods, out_root, 'rise blade', RISE_DIFFUSE, RISE_NORMAL, RISE_ENVMASK,
                   OUT_GOLD_D, OUT_GOLD_N, OUT_GOLD_M, grip=(rise_shape, RISE_GRIP_Y) + RISE_LEATHER)
    gold_set(mods_dir, mods, out_root, 'rise scabbard', RISE_SCB_DIFFUSE, RISE_SCB_NORMAL, RISE_SCB_ENVMASK,
             OUT_SCB_D, OUT_SCB_N, OUT_SCB_M)
    src, raw = winner(mods_dir, [], CHROME_CUBEMAP, CHROME_BSAS)      # Bethesda's, never a loose replacer's
    gold_cubemap(raw, os.path.join(out_root, *OUT_GOLD_E.split('/')))
    return out


def gold_cubemap(raw, out_path):
    """Bethesda's chrome studio cubemap (bright light bands over a dark room: what reads as polish) resampled to
    CUBE_SIZE, its contrast raised and graded to gold. The env-map shader adds reflections untinted, so a gold item
    needs a gold cubemap; vanilla's gold items use one too."""
    d = tempfile.mkdtemp()
    src = os.path.join(d, 'cube.dds')
    open(src, 'wb').write(raw)
    plain = os.path.join(d, 'plain')
    os.makedirs(plain)
    run_texconv(['-f', 'R8G8B8A8_UNORM', '-m', '1', '-w', str(CUBE_SIZE), '-h', str(CUBE_SIZE), '-if', 'CUBIC',
                 '-o', plain, src])
    b = bytearray(open(os.path.join(plain, 'cube.dds'), 'rb').read())
    assert b[:4] == b'DDS '
    h, w = struct.unpack_from('<II', b, 12)
    assert (w, h) == (CUBE_SIZE, CUBE_SIZE), (w, h)
    caps2 = struct.unpack_from('<I', b, 112)[0]
    off = 128 + (20 if b[84:88] == b'DX10' else 0)
    if b[84:88] == b'DX10':
        assert struct.unpack_from('<I', b, 128 + 8)[0] & 4, 'not a cube'
    else:
        assert caps2 & 0x200, 'not a cube'
    n = len(b) - off
    assert n == 6 * w * h * 4, (n, w, h)
    px = np.frombuffer(bytes(b[off:]), np.uint8).reshape(-1, 4).astype(np.float32) / 255.0
    lum = px[:, :3] @ np.array([0.299, 0.587, 0.114])
    t = np.clip(CUBE_GAIN * lum ** CUBE_GAMMA, 0, 1)
    px[:, :3] = ramp(t, CUBE_RAMP)
    px[:, 3] = 1.0
    b[off:] = (px * 255 + 0.5).astype(np.uint8).tobytes()
    tinted = os.path.join(d, 'gold')
    os.makedirs(tinted)
    open(os.path.join(tinted, 'cube.dds'), 'wb').write(b)
    outd = os.path.join(d, 'out')
    os.makedirs(outd)
    run_texconv(['-f', 'BC1_UNORM', '-m', '0', '-o', outd, os.path.join(tinted, 'cube.dds')])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    shutil.move(os.path.join(outd, 'cube.dds'), out_path)
    shutil.rmtree(d)
    print('rise gold cubemap: chrome %dx%d x 6 faces, luminance mean %.2f -> graded mean %.2f, p95 %.2f'
          % (w, h, lum.mean(), px[:, :3].mean(), np.percentile(px[:, :3] @ np.array([0.299, 0.587, 0.114]), 95)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mods', default=os.path.join(MO2, 'mods'))
    ap.add_argument('--target', default='Zenderal - Patch Collection')
    ap.add_argument('--out-root', default=None, help='write here instead of <mods>/<target> (dry run)')
    ap.add_argument('--preview', default=None, help='PNG of both blades with the coat and the flame box')
    args = ap.parse_args()
    mods = profile_mods()
    out_root = args.out_root or os.path.join(args.mods, args.target)
    assert os.path.isdir(out_root), out_root

    s_src, sting_nif = load(args.mods, mods, STING_MESH)
    r_src, rise_nif = load(args.mods, mods, RISE_MESH)
    for src, rel in ((s_src, STING_MESH), (r_src, RISE_MESH)):
        if src != EXPECT_SOURCE:
            sys.exit('%s now comes from %s, not %s: check the blade fits before shipping' % (rel, src, EXPECT_SOURCE))
    _, goo = load(args.mods, mods, GOO_MESH)
    t_src, template = winner(args.mods, mods, ART_TEMPLATE)
    assert nifse.Nif(template).tobytes() == template
    print('%-48s from %s' % (ART_TEMPLATE, t_src))
    _, torch = load(args.mods, mods, TORCH_MESH)

    _, burst_nif = load(args.mods, mods, BURST_MESH)        # the winner (2026-11-13: PG Patcher Output's copy)

    sting, s_info = build_sting(sting_nif, goo, template)
    rise, r_info = build_rise(rise_nif, template, torch)
    burst = build_burst(burst_nif)
    _, sting_mesh_nif = load(args.mods, mods, STING_MESH)      # a fresh copy: build_sting reads the first one
    sting_mesh = build_sting_mesh(sting_mesh_nif)
    _, burst_nif2 = load(args.mods, mods, BURST_MESH)          # a second trimmed burst, for the spiderlings
    spider_burst = build_spider_burst(build_burst(burst_nif2))
    m_src, m_raw = winner(args.mods, [], MOTE_SRC)               # Enderal's own orb, not a loose replacer's
    print('%-48s from %s' % (MOTE_SRC, m_src))
    mote = build_mote(nifse.Nif(m_raw))
    _, nova_nif = load(args.mods, mods, NOVA_SRC)               # the winner (2026-11-13: PG Patcher Output's copy)
    nova = build_nova(nova_nif)
    w_src, w_raw = winner(args.mods, [], WEB_SRC)                 # the game's own, not Particle Patch's copy
    print('%-48s from %s' % (WEB_SRC, w_src))
    web = build_web(nifse.Nif(w_raw))
    _, rise_mesh_nif = load(args.mods, mods, RISE_MESH)        # a fresh copy: build_rise reads the first one
    rise_mesh = build_rise_mesh(rise_mesh_nif)
    for art, rel in ((sting, OUT_STING), (rise, OUT_RISE), (burst, OUT_BURST), (sting_mesh, OUT_STING_MESH),
                     (spider_burst, OUT_SPIDER_BURST), (mote, OUT_MOTE), (nova, OUT_NOVA), (rise_mesh, OUT_RISE_MESH),
                     (web, OUT_WEB)):
        out = art.tobytes()
        back = nifse.Nif(out)
        assert back.tobytes() == out
        check_refs(back)
        p = os.path.join(out_root, *rel.split('/'))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'wb') as fh:
            fh.write(out)
        print('wrote %s (%d bytes, %d blocks)' % (p, len(out), len(back.blocks)))
    print('PyNifly reads the coat as', readback(os.path.join(out_root, *OUT_STING.split('/'))))
    print('PyNifly reads Sting as', readback(os.path.join(out_root, *OUT_STING_MESH.split('/'))))
    print('PyNifly reads Rise as', readback(os.path.join(out_root, *OUT_RISE_MESH.split('/'))))
    _, plain_sting = load(args.mods, mods, STING_MESH)
    sting_texture(args.mods, mods, out_root, main_shape(plain_sting, '1stPerson'))
    gold_textures(args.mods, mods, out_root, main_shape(rise_nif, 'Noble'))
    ornament_textures(out_root)
    palettes(args.mods, out_root)
    if args.preview:
        preview(args.preview, s_info, r_info)


if __name__ == '__main__':
    main()
