"""Generate Clockwork Thunder's mesh and textures: Ordo Legionis' Nehrimese Flintlock Fucile
(OL_Musket_Rifle 002F9B) in polished Starling gold, with Starling cogs on its forestock, a cog-shaped trigger guard,
a round barrel (Ordo's is hexagonal) and a cog round the muzzle.

Inputs (the curator's installed list, nothing committed):
  rifle mesh   the WINNING loose meshes/OLM/OL_Musket/OL_Musket_Rifle_Animated.nif (Ordo Legionilis
               (Imperial Muskets)' loose copy beats Muskets of the Enderal's BSA). Same file is the
               world model and the 1st-person static OLM_1stPersonMusketRifle 002F9A.
  rifle tex    textures/olm/ol_engflintlockrifle/englishflintlockrifle_{basecolor,metallic,height}.dds
  cog          meshes/clutter/dwemer/dwecog01.nif (Enderal's own Starling cog, E - Meshes.bsa) and its
               diffuse textures/dungeons/dwemerruins/DweMetalSheet01Small.dds
  scope        Scoped Bows SE's Nordic bow (OutLaw666, assets free to use; extracted from the curator's download)
               and the rifle's corrected 1st-person aim clip (FlintlockOverhaul tools/06, run it first): scope.py

Outputs, into <mods>/<target mod>/ (default Zenderal - Patch Collection):
  meshes/Zenderal/ClockworkThunder/ClockworkThunder.nif
      The rifle mesh rebuilt block by block (nifsplice; every original block byte-identical, asserted)
      with (1) the rifle's texture set pointing at the recoloured diffuse and env mask, and (2) ONE new
      NiTriShape holding all the cogs: same parent and transform as the rifle's own shape, the rifle's
      shader property copied with its own texture set (gold cog textures).
  textures/Zenderal/ClockworkThunder/ClockworkThunder_d.dds    (BC7, mips)  rifle diffuse
  textures/Zenderal/ClockworkThunder/ClockworkThunder_n.dds    (BC7, mips)  rifle normal, highlights raised on metal
  textures/Zenderal/ClockworkThunder/ClockworkThunder_m.dds    (BC7, mips)  Complex Material mask
  textures/Zenderal/ClockworkThunder/ClockworkThunderCog_d/_n/_m.dds          the same for the cogs
  textures/Zenderal/ClockworkThunder/ClockworkThunder_e.dds    gold cubemap (shared by both texture sets)

Polished gold (curator 2026-11-13, after Rise: "the gun metal shiny gold now that we have those new
cubemaps"): Rise's build-4 recipe = Precious Objects Complex Material and Dynamic Cubemap's gold, imported
from src/StingAndRise/tools/01-build-assets.py (GOLD_RAMP, SPEC level, COMPLEX, the gold chrome cubemap).
Metal (the rifle's own metallic map) -> the gold ramp by luminance; wood kept, a little darker. Ordo's
shader was type 0 without Environment_Mapping, so it never reflected at all (why the first, rusted build
read flat): every shader in our mesh is now Environment Map (type 1) with the flag and env scale ENV_SCALE.

Cog placement: in the rifle shape's own space (Z along the gun, muzzle +Z; Y up; X across, scale 0.62
to world). Each cog lies flat on one side of the gun; its inner face sits just under the lowest point of
the gun's surface under the disc and its outer face clear of the highest (so no gap shows under the rim
and the teeth stand proud). The surface is sampled from the rifle's triangles; a disc that leaves the
silhouette, or a surface that varies more than MAX_RELIEF under it, stops the build.

Tangents: computed from UVs in the convention the rifle's own NiTriShapeData uses (checked against it
on every build).

Usage:  python 01-build-assets.py [--mods <MO2 mods dir>] [--target <mod name>] [--preview <png prefix>]
"""
import argparse
import importlib.util
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE)
import nifsplice as ns  # noqa: E402
import scope  # noqa: E402   (the ring scope, from Scoped Bows SE's Nordic bow)

TOOLS = json.load(open(os.path.join(ROOT, '.claude', 'config', 'tools.json'), encoding='utf-8-sig'))
sys.path.insert(0, TOOLS['pynifly'])
from pyn.pynifly import NifFile  # noqa: E402

_spec = importlib.util.spec_from_file_location('_bsa', os.path.join(ROOT, 'src', 'Prophecy', 'tools', '_bsa.py'))
_bsa = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bsa)
_spec = importlib.util.spec_from_file_location('_rise', os.path.join(ROOT, 'src', 'StingAndRise', 'tools', '01-build-assets.py'))
_rise = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_rise)      # Rise's gold: GOLD_RAMP, COMPLEX, gold_cubemap, write_texture, smallest_mip

MO2 = TOOLS['modlistRoot']
DATA = TOOLS['gameDataDir']
PROFILE = 'Ultra'

RIFLE_MESH = 'meshes/OLM/OL_Musket/OL_Musket_Rifle_Animated.nif'
RIFLE_TEX = 'textures/olm/ol_engflintlockrifle/englishflintlockrifle_%s.dds'
COG_MESH = 'meshes/clutter/dwemer/dwecog01.nif'
COG_TEX = 'textures/dungeons/dwemerruins/DweMetalSheet01Small.dds'
COG_NORMAL = 'textures\\dungeons\\dwemerruins\\DweMetalSheet01Small_n.dds'
MESH_BSAS = ['E - Meshes.bsa', 'Skyrim - Meshes0.bsa', 'Skyrim - Meshes1.bsa']
TEX_BSAS = ['E - Textures1.bsa', 'E - Textures2.bsa'] + ['Skyrim - Textures%d.bsa' % k for k in range(9)]

OUT_MESH = 'meshes/Zenderal/ClockworkThunder/ClockworkThunder.nif'
OUT_D = 'textures/Zenderal/ClockworkThunder/ClockworkThunder_d.dds'
OUT_M = 'textures/Zenderal/ClockworkThunder/ClockworkThunder_m.dds'
OUT_N = 'textures/Zenderal/ClockworkThunder/ClockworkThunder_n.dds'
OUT_E = 'textures/Zenderal/ClockworkThunder/ClockworkThunder_e.dds'
OUT_COG = 'textures/Zenderal/ClockworkThunder/ClockworkThunderCog_d.dds'
OUT_COG_N = 'textures/Zenderal/ClockworkThunder/ClockworkThunderCog_n.dds'
OUT_COG_M = 'textures/Zenderal/ClockworkThunder/ClockworkThunderCog_m.dds'
OUT_GLASS_D = 'textures/Zenderal/ClockworkThunder/ClockworkThunderGlass_d.dds'
OUT_GLASS_N = 'textures/Zenderal/ClockworkThunder/ClockworkThunderGlass_n.dds'
OUT_GLASS_M = 'textures/Zenderal/ClockworkThunder/ClockworkThunderGlass_m.dds'

COG_SHAPE_NAME = 'ClockworkThunderCogs'
OUT_SCOPE_D = 'textures/Zenderal/ClockworkThunder/ClockworkThunderScope_d.dds'
OUT_SCOPE_N = 'textures/Zenderal/ClockworkThunder/ClockworkThunderScope_n.dds'
OUT_SCOPE_M = 'textures/Zenderal/ClockworkThunder/ClockworkThunderScope_m.dds'
OUT_RETICLE = 'textures/Zenderal/ClockworkThunder/ClockworkThunderReticle.dds'
SCOPE_SHAPE = 'ClockworkThunderScope'
SCOPE_LENS_SHAPE = 'ClockworkThunderScopeLens'
SCOPE_RETICLE_SHAPE = 'ClockworkThunderScopeReticle'

# (side, Z along the gun, Y height, radius, in-plane turn in degrees), rifle shape space.
# side -1 = the lock side, +1 = the side-plate side. Big + meshing cog on each side of the butt, one on the
# wrist (lock side) / side plate, a small one on each side of the forestock.
# Curator 2026-11-13 (screenshot): the cogs belong where they make mechanical sense - a gear train on the
# forestock straight in front of the lock, as if the lock drove it. One train, mirrored on both sides; nothing
# on the butt or wrist any more. TRAIN = first cog (Z, Y, radius), then each next cog as (radius, direction in
# degrees from the previous cog's centre, 0 = towards the muzzle, 90 = up). Centres sit MESH x (r1 + r2) apart
# and each cog is turned so its teeth fall into the previous cog's gaps (meshed_turns).
# The forestock's side is a flat band y 22.3..27.2 from the lock plate's front edge (z -13) forward (surface scan
# 2026-11-13), so the train runs along it; the first, largest cog sits against the lock plate.
TRAIN_START = (-10.6, 24.8, 2.2)
TRAIN = [(1.5, -12), (1.9, 12), (1.3, -10)]
MESH = 0.9             # centre distance / (r1 + r2): teeth overlap by ~10% of the radii


def cog_train(teeth):
    z, y, r = TRAIN_START
    chain = [(z, y, r, 0.0)]
    for r2, ang in TRAIN:
        z1, y1, r1, t1 = chain[-1]
        a = math.radians(ang)
        d = MESH * (r1 + r2)
        z2, y2 = z1 + d * math.cos(a), y1 + d * math.sin(a)
        # meshing: rotation of gear 2 mirrors gear 1's about the line of centres (ratio r1/r2), plus half a
        # tooth so a tooth faces a gap; the cog's teeth start at in-plane angle 0
        t2 = -(r1 / r2) * (t1 - ang) + ang + 180.0 + 180.0 / teeth
        chain.append((z2, y2, r2, t2))
    return [(side, z, y, r, t) for side in (-1, +1) for z, y, r, t in chain]


def cog_profile(CV):
    """(teeth, angle of the first tooth's centre in degrees, hole radius / tip radius) of the cog mesh.
    Enderal's dwecog01: 6 teeth (tips 23.6, body 18.1), finger-sized hole (~9.7)."""
    ang = np.degrees(np.arctan2(CV[:, 1], CV[:, 0])) % 360
    rad = np.hypot(CV[:, 0], CV[:, 1])
    tips = np.sort(ang[rad > 0.95 * rad.max()])
    gaps = np.diff(np.concatenate([tips, tips[:1] + 360]))
    cut = np.where(gaps > 15)[0]           # a gap of more than 15 degrees separates two teeth
    teeth = len(cut)
    first = tips[(cut[0] + 1) % len(tips)]
    last = tips[cut[1 % teeth]] if teeth > 1 else tips[-1]
    centre = (first + ((last - first) % 360) / 2) % 360
    return teeth, centre, float(rad.min() / rad.max())


# Curator 2026-11-13: "make the trigger guard ... cog shaped". The guard piece is dropped from the rifle's
# triangles and the cog stands in its place round the trigger (trigger piece: z -34.1..-28.9, y 17.5..22.1).
GUARD_BOX = ((-1.6, 1.6), (11.5, 22.5), (-55.5, -18.0))   # (x, y, z) bounds the guard piece must lie in
GUARD_MIN_TRIS = 500
# Curator 2026-11-13: "on the right side where the cogs are there's a gold panel underneath, just remove it". Ordo's
# oval escutcheon on the lock side of the forestock (its own welded piece, 64 triangles, x -3.05..-2.68,
# y 24.1..25.9, z -4.5..-1.3 on the 2026-11-13 mesh) sat under the third and fourth cogs; it is dropped, and the cogs
# are seated on the stock without it. The stock's own surface runs on underneath it.
OVAL_BOX = ((-3.6, -2.0), (23.0, 27.0), (-6.0, 0.0))
OVAL_TRIS = (40, 100)

# Curator 2026-11-15: "a glass tube with a lightning bolt sparking in it ... with some gold fittings", then
# (the first build sat on the side-plate side's lock panel) "not on the side, on the top, just before the hammer":
# on the TOP of the wrist, on the centre line, from just behind the barrel's tang (its top strip ends at z -26.6)
# back along the wrist. The wrist top falls from y 29.4 at z -27 to 26.9 at z -37 (convex), 3-4 units wide; the
# hammer stands on the lock side at x <= -2.3 (surface scan 2026-11-15). (The second build followed the wrist's
# slope; the third was enlarged; the fourth, below, is horizontal.)
#   glass     an alpha-blended Environment Map shader (Bethesda's chrome cubemap path; our own faint tint)
#   lightning two crossed cards with Bethesda's FXLightningBolt01 (two forked bolts) + one with ShockBoltTile01
#             (a glowing core), on effect shaders with additive blending; float controllers make the bolt jump
#             (stepped U/V offsets) and flicker (emissive multiple), looping. Bethesda's own lightning meshes
#             only animate through such controllers; the rifle's BSXFlags already has the Animated bit.
#   fittings  gold (the cog shape and shader): collars with a bead and a terminal nub at both ends, a strap
#             round the middle with a screw head on the wood each side.
# Third pass, same day (curator's mark on the second build's render: "enlarge the tube, have it extend from the
# barrel"): the front collar is the barrel's width (the breech plug is x +-2.23) and butts against the breech
# plug's rear face (z -25.33) with no nub, so the barrel runs into the tube; the axis sits ON the wrist's crown
# (half the tube in the wood, under the first-person sight line) and 0.6 toward the side-plate side, where the mark
# lies and away from the hammer (x <= -2.33; pan x >= -1.78 only below y 26.7). The strap keeps no screws: the
# tube now covers the wrist's width.
# Fourth pass (curator's highlight on a side view: "the tube is horizontal matching the barrel"): the tube runs
# straight back from the breech along the barrel's line, not down the wrist: axis parallel to the barrel (+Z), its
# collars the barrel's width (round barrel r 1.94), sunk TUBE_SINK into the wrist's crown just behind the tang.
# The wrist falls away under it (y 29.4 at z -27 to 26.6 at z -38), so two gold legs (at the strap and near the
# rear cap) carried it down to the wood; then, against the highlight, it was lowered so its axis sits about at
# the barrel's top, slimmed and shortened: it rests in the wrist all along, so no legs.
# Fifth pass (curator's mark on the fourth: "hollow out the wood to align the tube with the barrel"): the tube is
# COAXIAL with the barrel (axis x 0, y = the round barrel's axis, collars the barrel's radius) and a channel is cut
# into the wrist for it, down to just under the tube (`cut_channel`: the rifle's own triangles split along the
# channel's five planes, the inside dropped; `channel_walls` closes the cut with wood: the wall planes' cut edges
# carried down to a floor). Only the stock and the tang (wholly inside the channel's width) are cut; the lock plate
# (x <= -1.87) and the breech plug are left alone.
TUBE_Z = (None, -25.35)        # rear end cap: found by tube_axis (clear of the wood); the front cap's outer face
CAP_CLEARANCE = 0.1            # the wrist top this far under the rear cap's bead ring
END_COG_THICK = 0.4            # the cog on the rear end cap (the nub, 0.45 x FIT long, stands through it)
END_COG_TOOTH = 0.45
PLATE_COG_RADII = (0.55, 0.45, 0.38, 0.3, 0.24, 0.18)  # the cogs packed over the gold floor plate, largest first
PLATE_COG_MAX = 40             # the plate-cog shape stays under 65535 vertices (about 1490 a cog)
PLATE_COG_LAYER = 0.09         # a cog overlapping earlier ones sits this much higher per layer
PLATE_COG_INNER = 1.74         # their inner edges this far from the axis (glass 1.55, strap ring 1.67)
COLLAR_CLEAR = 2.08            # ... and this far beside the collars (bead ring 2.0)
PLATE_COG_MARGIN = 0.05        # plate outline left past each cog's rim
PLATE_COG_OVERHANG = 0.1       # ... though a cog may reach this far over the panel's bevel
PLATE_COG_PACK = 0.88          # centre distance / sum of radii within a layer: teeth interleave
PLATE_COG_TOP_BELOW = 0.35     # cogs smaller than this sit one layer up, over the gaps between the big ones
PLATE_COG_OVER = 0.55          # ... and may come this close to a big one (overlapping its edge)
PLATE_COG_GRID = 0.1           # candidate centre spacing
PLATE_COG_THICK = 0.16         # for the largest; smaller ones thinner (square root of the radius ratio)
PLATE_COG_SHAPE = 'ClockworkThunderPlateCogs'   # its own shape: the cog shape would pass 65535 vertices
PANEL_H = 0.1                  # the plate panel stands this far over the cut's floor ...
PANEL_BEVEL = 0.14             # ... its top inset this far from the outline, a bevel between (like the lock plate)
PANEL_CELL = 0.25              # panel cell size (UV sampling)
GROOVE_SIDES = 48              # the groove's prism round the tube's rear half (24 showed kinks along its edge)
GROOVE_STEP = 0.1              # its faces filled in z steps of this
EDGE_TUBE_R = 0.24             # the gold tubes along the groove's edges
EDGE_TUBE_BIN = 0.2
EDGE_TUBE_TRIM = 0.4           # the fitted middle stops this far inside the traced edge at each end
EDGE_TUBE_COLLAR_ANGLE = 40.0  # where the pipe enters the rear collar's front shoulder: degrees below the side
SIDE_TUBE_R = 0.2              # the metal side tubes on the plate, one a side
SIDE_TUBE_COLLAR = 0.28
SIDE_TUBE_COLLAR_LEN = 0.22
SIDE_TUBE_COG_R = 0.4          # their end cogs (tips); the tube's axis stands this high over the panel
SIDE_TUBE_COG_T = 0.12
SIDE_TUBE_X_MAX = 2.9          # the outermost axis offset tried
SIDE_TUBE_X_MIN = 2.05         # ... and the innermost (end cogs clear of the main glass, r 1.55)
SIDE_TUBE_MIN_LEN = 2.0
PANEL_TAIL_MID = 3.8           # the lock plate's tail: its middle this far in front of the plate's rear end
RIVET_R = 0.17                 # the panel's rivets, a pair a side
RIVET_GAP = 0.5                # between the two of a pair (along the gun)
RIVET_MIN_X = 2.3              # a rivet's inner edge at least this far from the axis
WIRE_R = 0.065                 # the wires on the panel
WIRE_LANES = ((1.95, 0.0),)   # (offset from the axis, wave phase) per wire, each side (one: the side tubes)
WIRE_WAVE = 0.14
WIRE_EDGE = 0.08               # panel top left past a wire
TUBE_X = 0.0
TUBE_LEGS = ()                 # z of legs to the wood (none: it lies in its channel)
TUBE_FRONT_NUB = False
TUBE_SCREWS = False
TUBE_TOP_FRONT = 29.39         # the wrist top at z -27 (asserted: the stock moved if this changes)
GLASS_R = 1.55
COLLAR_R = 1.94                # the round barrel's radius at the breech
TUBE_BEAD = 0.06               # the bead ring stands this far over the collar
CHANNEL_GAP = 0.05             # wood clearance round the widest gold (beads) and behind the rear nub
CHANNEL_FLOOR_BELOW_AXIS = 0.2 # the cut's floor this far under the tube's axis: the wood hugs its lower half
CHANNEL_RAMP = 0.8             # behind the rear cap the floor rises this much per unit back (about 39 deg)
CHANNEL_RAMP_REACH = 12.0      # a back bound for the cut, well past where the ramp leaves the wrist
POCKET_GAP = 0.08              # the rear cap's pocket: this far under its bead ring and in front of it
CHANNEL_FRONT = -25.33         # the breech plug's rear face
# Curator's outline (an "L" on the side view: down the breech face, then straight back at the barrel's underside):
# the wood is taken down across the stock's WHOLE width, not a slot (a slot's side walls hid the tube from the side).
CHANNEL_HALF_WIDTH = 5.0       # wider than the stock: no side walls, the floor is the stock's own cross-section
FIT = COLLAR_R / 1.5           # the end fitting's profile was drawn for a 1.5 collar
TUBE_SEG = 32
BOLT_TEX = 'textures\\effects\\FXLightningBolt01.dds'
GLOW_TEX = 'textures\\effects\\ShockBoltTile01.dds'
GLASS_ENV = 'textures\\cubemaps\\chrome_e.dds'
GLASS_TINT = (0.80, 0.88, 0.95, 0.18)   # diffuse RGB + alpha
BOLT_EMISSIVE = (0.72, 0.84, 1.0, 1.0)
BOLT_SHAPE = 'ClockworkThunderBolt'
GLOW_SHAPE = 'ClockworkThunderGlow'
GLASS_SHAPE = 'ClockworkThunderGlass'
ALPHA_ADDITIVE = 0x100D        # Bethesda's lightning (testlightninggeo.nif): src alpha, dest one
ALPHA_BLEND = 0x00ED           # src alpha, inverse src alpha
GUARD_CENTRE = (-31.5, 19.6)   # (z, y): the hole's centre, round the trigger's tip
GUARD_HOLE = 3.6               # hole radius: clears the trigger tip (5.2 long, 4.6 tall; its top is in the wood)
GUARD_THICK = 1.4              # across the gun (the old guard was 2.8 wide; curator: subtle)
GUARD_BAND = 0.9               # ring width from the hole to the rim between the teeth
GUARD_TOOTH = 0.8              # tooth height above that rim
# Round barrel (curator 2026-11-13: "make the barrel cylindrical"). Ordo's barrel is one welded hexagonal tube
# (240 triangles, every vertex on a hexagon round the bore axis, corners at 0/60/.. deg): each triangle is split
# BARREL_SPLITS times (midpoints, so the 60 deg faces become 15 deg) and every point mapped from its hexagon onto
# the circle of BARREL_K x the hexagon's corner radius (0.909 = the circle with the hexagon's area). UVs follow
# each triangle, so the texture is the barrel's own. The new barrel is its own shape on the rifle's shader.
BARREL_MIN_TRIS = 200
RIB_MIN_TRIS = 100       # the hexagonal rib between barrel and ramrod (108 triangles) is rounded too
MUZZLE_REACH = 1.5
BARREL_SPLITS = 2
BARREL_K = 0.909
BARREL_SHAPE_NAME = 'ClockworkThunderBarrel'
# Muzzle cog (curator 2026-11-13: "a cog over the hole"): dwecog01 remapped like the guard, standing across the
# barrel at its muzzle face, its hole the bore's circle, one tooth straight up. The rifle has no front-sight blade
# (the aim line runs over the muzzle top), so the top tooth reads as one; it rises about 0.4 world units over the
# muzzle, under the crosshair dot (1 deg above the muzzle = ~1.1 units at that distance).
MUZZLE_BAND = 0.55     # ring from the bore out to the rim between the teeth
MUZZLE_TOOTH = 0.45    # tooth height above that rim
MUZZLE_THICK = 0.6     # along the barrel
MUZZLE_PROUD = 0.15    # its front face this far ahead of the muzzle face
THICKNESS = 0.9        # cog thickness above the surface's highest point under it (shape units)
SINK = 0.15            # inner face this far under the surface's lowest point under the disc
MAX_RELIEF = 4.0       # surface may vary this much under a disc, else the spot is too curved
SAMPLE_STEP = 0.3      # surface sample spacing (shape units)
CELL = 0.35            # surface height under a cog vertex = highest sample within this distance

# colours (linear-ish sRGB 0..1)
WOOD_DARKEN = 0.82
METAL_SPEC = 0.85      # normal-map alpha (highlight mask) on metal: Precious's 0.63-0.88, Rise's ~0.8
WOOD_GLOSS = 0.2       # Complex Material glossiness off the metal (no reflection, no metalness there)
ENV_SCALE = 1.0        # as Rise's blade shader (Vanilla Fresnel saturates the mask)
SLSF1_ENVIRONMENT_MAPPING = 0x80
SHADER_TYPE_ENVMAP = 1


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


def winner(mods_dir, mods, rel, bsas):
    """(source label, bytes): the highest-priority loose copy, else the first BSA that has it."""
    for mod in mods:
        p = find_ci(os.path.join(mods_dir, mod), rel)
        if p:
            return mod, open(p, 'rb').read()
    key = rel.replace('/', '\\').lower()
    for name in bsas:
        path = os.path.join(DATA, name)
        if not os.path.isfile(path):
            continue
        if name not in _bsa_cache:
            _bsa_cache[name] = _bsa.listing(path)
        data, listing = _bsa_cache[name]
        if key in listing:
            return name, _bsa.read(data, listing[key])
    sys.exit('no source for ' + rel)


def load_dds(raw):
    tmp = tempfile.NamedTemporaryFile(suffix='.dds', delete=False)
    tmp.write(raw)
    tmp.close()
    im = Image.open(tmp.name)
    im.load()
    os.remove(tmp.name)
    return im


def texconv():
    p = os.path.join(os.path.dirname(TOOLS['xedit']), 'Edit Scripts', 'Texconvx64.exe')
    assert os.path.isfile(p), p
    return p


def write_bc7(rgb_float, out_path, fmt="BC7_UNORM"):
    """rgb(a) float 0..1 array -> BC7 DDS with a full mip chain."""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    arr = np.clip(rgb_float * 255.0 + 0.5, 0, 255).astype(np.uint8)
    mode = 'RGB' if arr.ndim == 3 and arr.shape[2] == 3 else 'L'
    tmpdir = tempfile.mkdtemp()
    png = os.path.join(tmpdir, os.path.splitext(os.path.basename(out_path))[0] + '.png')
    Image.fromarray(arr, mode).save(png)
    r = subprocess.run([texconv(), '-nologo', '-y', '-f', fmt, '-m', '0', '-o', tmpdir, png],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    dds = png[:-4] + '.dds'
    shutil.move(dds, out_path)
    os.remove(png)
    os.rmdir(tmpdir)


# ---- recolour --------------------------------------------------------------------------------------------

def fbm(h, w, seed, octaves=6, base=8):
    """Fractal value noise 0..1, tileable enough for a weapon atlas."""
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, total = 1.0, 0.0
    for o in range(octaves):
        n = base * (2 ** o)
        grid = rng.random((n + 1, n + 1)).astype(np.float32)
        im = Image.fromarray((grid * 65535).astype(np.uint16).astype(np.int32), 'I').resize((w, h), Image.BICUBIC)
        out += amp * (np.asarray(im, np.float32) / 65535.0)
        total += amp
        amp *= 0.55
    out /= total
    lo, hi = np.percentile(out, 1), np.percentile(out, 99)
    return np.clip((out - lo) / (hi - lo), 0, 1)


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def polished_gold(rgb, metal, normal, label):
    """rgb HxWx3, metal HxW 0..1 (weight), normal HxWx4 (alpha = highlight mask). Rise's recipe (see the
    docstring): returns (diffuse RGB, normal RGBA, Complex Material mask RGBA)."""
    on = metal > 0.5
    lum = (rgb * np.array([0.299, 0.587, 0.114])).sum(-1)
    lo, hi = np.percentile(lum[on], [5, 95])
    gold = _rise.ramp(np.clip((lum - lo) / max(hi - lo, 1e-3), 0, 1), _rise.GOLD_RAMP)
    out = rgb * WOOD_DARKEN * (1 - metal[..., None]) + gold * metal[..., None]
    n = normal.copy()
    n[..., 3] = METAL_SPEC * metal + normal[..., 3] * (1 - metal)
    cm = np.stack([_rise.COMPLEX[0] * metal,                       # R: reflects
                   _rise.COMPLEX[1] * metal + WOOD_GLOSS * (1 - metal),   # G: glossiness
                   _rise.COMPLEX[2] * metal,                       # B: metalness
                   np.zeros_like(metal)], -1)                      # A: no parallax (and marks it complex)
    print('%s gold: %d%% metal, luminance %.2f..%.2f onto the gold ramp, diffuse mean on metal %s'
          % (label, 100 * metal.mean(), lo, hi, ' '.join('%.2f' % v for v in out[on].mean(0))))
    return np.clip(out, 0, 1), np.clip(n, 0, 1), cm


def write_complex_mask(cm, path):
    """Bottled Shaders' own test on the 1x1 mip it samples: alpha below 1 - eps and not grey (Rise's checks)."""
    _rise.write_texture(cm, path, 'BC7_UNORM')
    mip = _rise.smallest_mip(path)
    eps = 4.0 / 255.0
    assert mip[3] < 1 - eps, 'alpha lost: the mask would not be complex (%s)' % mip
    assert max(abs(mip[0] - mip[1]), abs(mip[0] - mip[2]), abs(mip[1] - mip[2])) >= 2 * eps, \
        'grey 1x1 mip %s: Bottled Shaders would read a plain env mask' % mip
    print('complex mask %s: 1x1 mip %s' % (os.path.basename(path), ' '.join('%.3f' % v for v in mip)))


def make_envmapped(b):
    """BSLightingShaderProperty (BS 83) of type 0 -> Environment Map (type 1): the type, the SLSF1 flag, and
    the type's trailing env-map scale. Layout after the texture-set ref: emissive colour 12, emissive mult 4,
    clamp 4, alpha 4, refraction 4, glossiness 4, specular colour 12, specular strength 4, lighting effects 8."""
    t = ns.shader_texset_offset(b)
    assert struct.unpack_from('<I', b, 0)[0] == 0 and len(b) == t + 60, ('not a plain type-0 shader', len(b), t)
    f1 = 8 + 4 * struct.unpack_from('<I', b, 8)[0] + 4 + 4
    out = bytearray(b)
    struct.pack_into('<I', out, 0, SHADER_TYPE_ENVMAP)
    struct.pack_into('<I', out, f1, struct.unpack_from('<I', out, f1)[0] | SLSF1_ENVIRONMENT_MAPPING)
    return out + struct.pack('<f', ENV_SCALE)


# ---- geometry --------------------------------------------------------------------------------------------

def tri_normals(V, T):
    n = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    return n / np.maximum(ln, 1e-12)


def uv_derivatives(V, UV, T):
    """Per-vertex dP/du and dP/dv, area-weighted, orthogonalised against nothing (raw)."""
    du = np.zeros_like(V)
    dv = np.zeros_like(V)
    p0, p1, p2 = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    t0, t1, t2 = UV[T[:, 0]], UV[T[:, 1]], UV[T[:, 2]]
    e1, e2 = p1 - p0, p2 - p0
    a1, a2 = t1 - t0, t2 - t0
    det = a1[:, 0] * a2[:, 1] - a2[:, 0] * a1[:, 1]
    ok = np.abs(det) > 1e-12
    r = np.where(ok, 1.0 / np.where(ok, det, 1), 0)[:, None]
    dpdu = (e1 * a2[:, 1:2] - e2 * a1[:, 1:2]) * r
    dpdv = (e2 * a1[:, 0:1] - e1 * a2[:, 0:1]) * r
    for k in range(3):
        np.add.at(du, T[:, k], dpdu)
        np.add.at(dv, T[:, k], dpdv)
    return du, dv


def ortho(vec, N):
    v = vec - (vec * N).sum(1, keepdims=True) * N
    ln = np.linalg.norm(v, axis=1, keepdims=True)
    return v / np.maximum(ln, 1e-12)


def tangent_convention(d):
    """Which UV derivative the NIF's 'tangents' / 'bitangents' arrays hold, read off the rifle itself.
    Returns (tangent_is, tangent_sign, bitangent_is, bitangent_sign) with *_is in {'du', 'dv'}."""
    V = np.array(d['verts'])
    N = np.array(d['normals'])
    UV = np.array(d['uvs'])
    T = np.array(d['tris'])
    du, dv = uv_derivatives(V, UV, T)
    du, dv = ortho(du, N), ortho(dv, N)
    st = np.array(d['tangents'])
    sb = np.array(d['bitangents'])
    res = []
    for stored in (st, sb):
        best = None
        for name, ref in (('du', du), ('dv', dv)):
            dot = (stored * ref).sum(1)
            good = np.linalg.norm(ref, axis=1) > 0.5
            m = float(np.median(dot[good]))
            if best is None or abs(m) > abs(best[2]):
                best = (name, 1 if m > 0 else -1, m)
        assert abs(best[2]) > 0.9, ('tangent convention unclear', best)
        res.append(best)
    return res[0][0], res[0][1], res[1][0], res[1][1]


def surface_samples(V, T, sign):
    """Points densely sampled on the rifle's triangles that face the given side (X sign)."""
    N = tri_normals(V, T)
    face = N[:, 0] * sign > 0.2
    P0, P1, P2 = V[T[face, 0]], V[T[face, 1]], V[T[face, 2]]
    # about one sample every SAMPLE_STEP along a triangle's longest edge (the forestock is long thin triangles)
    edge = np.max([np.linalg.norm(P1 - P0, axis=1), np.linalg.norm(P2 - P1, axis=1),
                   np.linalg.norm(P0 - P2, axis=1)], axis=0)
    ks = np.clip(np.ceil(edge / SAMPLE_STEP), 6, 160).astype(int)
    pts = []
    for k in np.unique(ks):
        sel = ks == k
        A, B, C = P0[sel], P1[sel], P2[sel]
        for a in range(k + 1):
            for b in range(k + 1 - a):
                u, v = a / k, b / k
                pts.append(A * (1 - u - v) + B * u + C * v)
    return np.concatenate(pts)


def place_cog(cog, samples, side, z, y, r, turn_deg):
    """Cog verts/normals/tris placed on the rifle (shape space). cog = (V, N, T) in its own XY plane."""
    CV, CN, CT = cog
    rad = np.max(np.linalg.norm(CV[:, :2], axis=1))
    k = r / rad
    # surface under the disc: outwardness = X * side
    d = np.hypot(samples[:, 2] - z, samples[:, 1] - y)
    under = samples[d <= r]
    assert len(under) > 200, ('cog leaves the gun', side, z, y, r, len(under))
    # disc coverage: every ring sector must have surface under it
    ang = np.arctan2(under[:, 1] - y, under[:, 2] - z)
    rr = np.hypot(under[:, 2] - z, under[:, 1] - y)
    for a0 in np.linspace(-math.pi, math.pi, 12, endpoint=False):
        sel = (ang >= a0) & (ang < a0 + math.pi / 6) & (rr > 0.7 * r)
        assert sel.sum() > 3, ('cog overhangs the silhouette', side, z, y, r, a0)
    out_w = under[:, 0] * side
    zmin, zmax = CV[:, 2].min(), CV[:, 2].max()
    tz = (THICKNESS + SINK) / (zmax - zmin)
    t = math.radians(turn_deg)
    c, s = math.cos(t), math.sin(t)
    # cog local (x, y, zc): in-plane turn, then x -> gun Z, y -> gun Y, zc -> outward. The cog is bent onto the
    # gun: each vertex rides on the surface height under it (the highest sample within CELL), like an inlay.
    rx = CV[:, 0] * c - CV[:, 1] * s
    ry = CV[:, 0] * s + CV[:, 1] * c
    gy, gz = y + ry * k, z + rx * k
    surf = np.empty(len(CV))
    for i in range(len(CV)):
        dd = np.hypot(under[:, 1] - gy[i], under[:, 2] - gz[i])
        near = dd < CELL
        surf[i] = out_w[near].max() if near.any() else out_w[np.argmin(dd)]
    # a cell holding only hidden inner faces (the forestock's barrel channel, the lock's inside) reads far below
    # the visible surface; such cells take the disc's median instead
    med = float(np.median(surf))
    holes = surf < med - 0.6
    surf[holes] = med
    lo, hi = float(surf.min()), float(surf.max())
    assert hi - lo <= MAX_RELIEF, ('surface too curved under cog', side, z, y, r, hi - lo)
    P = np.stack([side * (surf - SINK + (CV[:, 2] - zmin) * tz), gy, gz], axis=1)
    M = np.array([[0, 0, side * tz], [s * k, c * k, 0], [c * k, -s * k, 0]], float)
    tris = CT.copy()
    if np.linalg.det(M) < 0:
        tris = tris[:, [0, 2, 1]]
    # normals from the bent mesh (the cog's vertices are already split at its hard edges)
    PN = np.zeros_like(P)
    fn_raw = np.cross(P[tris[:, 1]] - P[tris[:, 0]], P[tris[:, 2]] - P[tris[:, 0]])
    for kk in range(3):
        np.add.at(PN, tris[:, kk], fn_raw)
    PN /= np.maximum(np.linalg.norm(PN, axis=1, keepdims=True), 1e-12)
    # same split structure as the source: a vertex's new normal must stay near its transformed original
    ref = CN @ np.linalg.inv(M)
    ref /= np.linalg.norm(ref, axis=1, keepdims=True)
    agree = (PN * ref).sum(1)
    assert np.median(agree) > 0.9, ('bent normals disagree with the cog', float(np.median(agree)))
    # sanity: the face normal of the outer face points outward
    fn = tri_normals(P, tris)
    outward = (fn[:, 0] * side > 0.9).sum()
    assert outward > len(tris) * 0.2, ('cog faces inward', side, z, y)
    return P, PN, tris, (lo, hi)


def piece_in_box(V, T, box, tris_range, label):
    """Indices of the one position-welded piece of the rifle mesh lying wholly inside box, with a triangle count
    in tris_range."""
    comp = components(V, T)
    (x0, x1), (y0, y1), (z0, z1) = box
    hits = []
    for c in np.unique(comp):
        n = int((comp == c).sum())
        if not tris_range[0] <= n <= tris_range[1]:
            continue
        pv = V[np.unique(T[comp == c])]
        lo, hi = pv.min(0), pv.max(0)
        if lo[0] >= x0 and hi[0] <= x1 and lo[1] >= y0 and hi[1] <= y1 and lo[2] >= z0 and hi[2] <= z1:
            hits.append(c)
    assert len(hits) == 1, (label + ' not found uniquely', hits)
    return np.where(comp == hits[0])[0]


def guard_triangles(V, T):
    """Indices of the trigger guard's triangles: the position-welded piece of the rifle mesh that lies in
    GUARD_BOX (bounds z -54.9..-18.5, y 11.9..22.1, x +-1.4 on the 2026-11-13 mesh: loop + rear scroll)."""
    key = {}
    wid = np.array([key.setdefault(tuple(np.round(v, 3)), i) for i, v in enumerate(V)])
    parent = list(range(len(V)))

    def f(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for tr in T:
        a = f(wid[tr[0]])
        for k in (1, 2):
            b = f(wid[tr[k]])
            parent[b] = a
    comp = np.array([f(wid[tr[0]]) for tr in T])
    (x0, x1), (y0, y1), (z0, z1) = GUARD_BOX
    hits = []
    for c in np.unique(comp):
        pv = V[np.unique(T[comp == c])]
        lo, hi = pv.min(0), pv.max(0)
        if lo[0] >= x0 and hi[0] <= x1 and lo[1] >= y0 and hi[1] <= y1 and lo[2] >= z0 and hi[2] <= z1                 and (comp == c).sum() > GUARD_MIN_TRIS:
            hits.append(c)
    assert len(hits) == 1, ('trigger guard not found uniquely', hits)
    return np.where(comp == hits[0])[0]


def guard_cog(cog, hole, tooth0):
    """The cog standing in the gun's side plane round the trigger, as the trigger guard: centred on X = 0,
    GUARD_THICK thick, one tooth pointing straight down. Curator 2026-11-13 ("thinner, subtle"): the cog is
    remapped radially, piecewise linear: its finger hole -> GUARD_HOLE, its body rim -> + GUARD_BAND, its tooth
    tips -> + GUARD_TOOTH, so the ring is a thin band with short teeth instead of the cog's broad disc."""
    CV, CN, CT = cog
    H, B, T = GUARD_HOLE, GUARD_HOLE + GUARD_BAND, GUARD_HOLE + GUARD_BAND + GUARD_TOOTH
    x, y = remap_cog_radii(CV, H, B, T)
    zmin, zmax = CV[:, 2].min(), CV[:, 2].max()
    tz = GUARD_THICK / (zmax - zmin)
    t = math.radians(-90.0 - tooth0)
    c, s = math.cos(t), math.sin(t)
    gz, gy = GUARD_CENTRE
    rx, ry = x * c - y * s, x * s + y * c
    P = np.stack([(CV[:, 2] - (zmin + zmax) / 2) * tz, gy + ry, gz + rx], axis=1)
    M = np.array([[0, 0, tz], [s, c, 0], [c, -s, 0]], float)
    tris = CT.copy()
    if np.linalg.det(M) < 0:
        tris = tris[:, [0, 2, 1]]
    # normals from the remapped mesh (its vertices are split at the hard edges)
    PN = np.zeros_like(P)
    fn_raw = np.cross(P[tris[:, 1]] - P[tris[:, 0]], P[tris[:, 2]] - P[tris[:, 0]])
    for kk in range(3):
        np.add.at(PN, tris[:, kk], fn_raw)
    PN /= np.maximum(np.linalg.norm(PN, axis=1, keepdims=True), 1e-12)
    print('guard cog: hole %.1f, band to %.1f, tips %.1f, %.1f thick; z %.1f..%.1f, y %.1f..%.1f'
          % (H, B, T, GUARD_THICK, P[:, 2].min(), P[:, 2].max(), P[:, 1].min(), P[:, 1].max()))
    return P, PN, tris


def components(V, T):
    """Per-triangle id of the position-welded piece it belongs to."""
    key = {}
    wid = np.array([key.setdefault(tuple(np.round(v, 3)), i) for i, v in enumerate(V)])
    parent = list(range(len(V)))

    def f(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for tr in T:
        a = f(wid[tr[0]])
        for k in (1, 2):
            parent[f(wid[tr[k]])] = a
    return np.array([f(wid[tr[0]]) for tr in T])


def hex_factor(theta):
    """Radius of a unit-corner hexagon (corners at multiples of 60 deg) at angle theta (radians)."""
    a = np.mod(theta, math.pi / 3) - math.pi / 6
    return math.cos(math.pi / 6) / np.cos(a)


def barrel_triangles(V, T):
    """The hexagonal tubes along the muzzle: every welded piece of >= BARREL_MIN_TRIS (or the 108-triangle rib under
    the barrel, >= RIB_MIN_TRIS) that reaches within MUZZLE_REACH of the mesh's max Z and has every vertex on a
    hexagon round its own axis (the round ramrod does not). Returns [(triangle indices, axis (x, y))], the barrel
    (the piece reaching the max Z) first."""
    comp = components(V, T)
    zmax = V[:, 2].max()
    out = []
    for c in np.unique(comp):
        tris = np.where(comp == c)[0]
        P = V[np.unique(T[tris])]
        if len(tris) < RIB_MIN_TRIS or P[:, 2].max() < zmax - MUZZLE_REACH:
            continue
        ax = np.array([(P[:, 0].max() + P[:, 0].min()) / 2, (P[:, 1].max() + P[:, 1].min()) / 2])
        d = P[:, :2] - ax
        keep = np.hypot(d[:, 0], d[:, 1]) > 1e-3
        ang = np.degrees(np.arctan2(d[keep, 1], d[keep, 0]))
        off = np.abs(np.mod(ang + 180, 60))
        off = np.minimum(off, 60 - off)
        if off.max() < 1.0:
            out.append((abs(P[:, 2].max() - zmax) < 0.01 and len(tris) >= BARREL_MIN_TRIS, tris, ax))
    out.sort(key=lambda o: not o[0])
    assert out and out[0][0] and sum(o[0] for o in out) == 1, ('barrel not found uniquely', [len(o[1]) for o in out])
    return [(tris, ax) for _, tris, ax in out]


def round_barrel(V, T, UV, tris, ax):
    """New (V, N, T, UV) for the barrel: split, mapped onto circles, normals smoothed within 45 deg."""
    pts, uvs = [], []
    for t in T[tris]:
        tri_list = [[(V[i], UV[i]) for i in t]]
        for _ in range(BARREL_SPLITS):
            nxt = []
            for a, b, c in tri_list:
                ab = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
                bc = ((b[0] + c[0]) / 2, (b[1] + c[1]) / 2)
                ca = ((c[0] + a[0]) / 2, (c[1] + a[1]) / 2)
                nxt += [[a, ab, ca], [ab, b, bc], [ca, bc, c], [ab, bc, ca]]
            tri_list = nxt
        for tri in tri_list:
            for pp, uu in tri:
                pts.append(pp)
                uvs.append(uu)
    P = np.array(pts, float)
    UVn = np.array(uvs, float)
    d = P[:, :2] - ax
    rho = np.hypot(d[:, 0], d[:, 1])
    th = np.arctan2(d[:, 1], d[:, 0])
    rn = BARREL_K * rho / hex_factor(th)
    P[:, 0] = ax[0] + rn * np.cos(th)
    P[:, 1] = ax[1] + rn * np.sin(th)
    TT = np.arange(len(P)).reshape(-1, 3)
    fn = tri_normals(P, TT)
    # normals smoothed over welded positions, only between faces within 45 deg (muzzle and breech steps stay hard)
    key = {}
    wid = np.array([key.setdefault(tuple(np.round(p, 4)), i) for i, p in enumerate(P)])
    acc = {}
    for k in range(len(P)):
        acc.setdefault(wid[k], []).append(k // 3)
    N = np.zeros_like(P)
    for k in range(len(P)):
        own = fn[k // 3]
        fs = fn[acc[wid[k]]]
        fs = fs[fs @ own > math.cos(math.radians(45))]
        n = fs.sum(0)
        N[k] = n / max(np.linalg.norm(n), 1e-12)
    # weld identical (position, uv, normal) corners
    uniq = {}
    idx = np.array([uniq.setdefault((tuple(np.round(P[k], 4)), tuple(np.round(UVn[k], 5)),
                                     tuple(np.round(N[k], 3))), len(uniq)) for k in range(len(P))])
    first = np.zeros(len(uniq), int)
    first[idx[::-1]] = np.arange(len(P))[::-1]
    TT = idx.reshape(-1, 3)
    TT = TT[(TT[:, 0] != TT[:, 1]) & (TT[:, 1] != TT[:, 2]) & (TT[:, 0] != TT[:, 2])]
    out_r = np.hypot(P[first][:, 0] - ax[0], P[first][:, 1] - ax[1])
    print('round barrel: %d -> %d triangles, %d verts; radius %.2f..%.2f (hexagon corners were %.2f..%.2f)'
          % (len(tris), len(TT), len(first), out_r[out_r > 0.01].min(), out_r.max(), rho[rho > 0.01].min(),
             rho.max()))
    return P[first], N[first], TT, UVn[first]


def remap_cog_radii(CV, H, B, T):
    """dwecog01 remapped radially, piecewise linear: finger hole -> H, body rim -> B, tooth tips -> T.
    Returns (x, y) of the remapped disc (its thickness axis Z untouched)."""
    r = np.linalg.norm(CV[:, :2], axis=1)
    h0, t0 = r.min(), r.max()
    b0 = r[r < 0.9 * t0].max()                  # the body rim between the teeth (18.1 of 23.6 on dwecog01)
    assert h0 < b0 < t0, (h0, b0, t0)
    rn = np.where(r <= h0 + 1e-6, H * r / h0,
                  np.where(r <= b0, H + (r - h0) / (b0 - h0) * (B - H), B + (r - b0) / (t0 - b0) * (T - B)))
    scale = rn / np.maximum(r, 1e-9)
    return CV[:, 0] * scale, CV[:, 1] * scale


def muzzle_cog(cog, tooth0, ax, bore, zface):
    """The cog standing across the barrel at the muzzle: its disc in X/Y round the bore axis, hole = the bore,
    one tooth straight up (+Y), front face MUZZLE_PROUD ahead of the muzzle face."""
    CV, CN, CT = cog
    H = bore
    B, T = H + MUZZLE_BAND, H + MUZZLE_BAND + MUZZLE_TOOTH
    x, y = remap_cog_radii(CV, H, B, T)
    t = math.radians(90.0 - tooth0)
    c, s = math.cos(t), math.sin(t)
    zmin, zmax = CV[:, 2].min(), CV[:, 2].max()
    tz = MUZZLE_THICK / (zmax - zmin)
    P = np.stack([ax[0] + x * c - y * s, ax[1] + x * s + y * c,
                  zface + MUZZLE_PROUD - (zmax - CV[:, 2]) * tz], axis=1)
    tris = CT.copy()
    PN = np.zeros_like(P)
    fn_raw = np.cross(P[tris[:, 1]] - P[tris[:, 0]], P[tris[:, 2]] - P[tris[:, 0]])
    for kk in range(3):
        np.add.at(PN, tris[:, kk], fn_raw)
    PN /= np.maximum(np.linalg.norm(PN, axis=1, keepdims=True), 1e-12)
    print('muzzle cog: hole %.2f, band to %.2f, tips %.2f, %.2f thick, z %.2f..%.2f'
          % (H, B, T, MUZZLE_THICK, P[:, 2].min(), P[:, 2].max()))
    return P, PN, tris


def outline_span(fs, z):
    """(min x, max x) where the cut outline segments fs (on a plane through z) cross z, or None."""
    xs = []
    for p, q in fs:
        a, b = (p, q) if p[2] <= q[2] else (q, p)
        if a[2] - 1e-7 <= z <= b[2] + 1e-7 and b[2] - a[2] > 1e-9:
            xs.append(a[0] + (b[0] - a[0]) * (z - a[2]) / (b[2] - a[2]))
    return (min(xs), max(xs)) if len(xs) >= 2 else None


def plate_cogs(cog, floor_segs, y_floor, z_front, z_back, collar_zs, wires=(), rivets=()):
    """Curator 2026-11-15: "add some metallic pieces with small cogs on the cut out parts", then (the plate kept over
    a two-strip version) "cover the plate in cogs". The floor beside the tube is a gold plate (close_cut's floor
    group goes to the gold shape); cogs lying flat are packed over it, both sides: candidate centres on a fine grid,
    front to back and outward from the tube, each taking the largest of PLATE_COG_RADII that fits inside the plate's
    outline (PLATE_COG_MARGIN left past its rim), stays clear of the tube (PLATE_COG_INNER; COLLAR_CLEAR beside the
    collars, z ranges collar_zs) and meets every placed cog no closer than PLATE_COG_PACK x the sum of the radii
    (teeth just interleaving). Each turned by its index, so the field does not read as a pattern; placed by size,
    largest first."""
    CV, CN, CT = cog
    rad = np.max(np.linalg.norm(CV[:, :2], axis=1))
    zmin, zmax = CV[:, 2].min(), CV[:, 2].max()
    parts, placed = [], []
    cap = min(PLATE_COG_MAX, 65000 // max(len(CV), len(CT)))      # one shape: vertices and triangles both < 65535

    def inner(z):
        for za, zb in collar_zs:
            if za - 0.6 <= z <= zb + 0.6:
                return COLLAR_CLEAR
        return PLATE_COG_INNER

    def fits(xc, zc, r):
        for zz in np.linspace(zc - r, zc + r, 9):
            sp = outline_span(floor_segs, zz)
            if sp is None or not (sp[0] + PLATE_COG_MARGIN <= xc - r and xc + r <= sp[1] - PLATE_COG_MARGIN):
                return False
            if abs(xc) - r < inner(zz):
                return False
            # a cog may overhang the panel's bevel by up to PLATE_COG_OVERHANG
            if not (PANEL_BEVEL - PLATE_COG_OVERHANG <= xc - r - sp[0] and PANEL_BEVEL - PLATE_COG_OVERHANG <= sp[1] - xc - r):
                return False
        for path in wires:                             # off the wires
            for wx, wz in path:
                if abs(wz - zc) < r + WIRE_R + 0.03 and math.hypot(wx - xc, wz - zc) < r + WIRE_R + 0.03:
                    return False
        for rx_, rz_, rr in rivets:
            if math.hypot(rx_ - xc, rz_ - zc) < r + rr + 0.04:
                return False
        lay = r < PLATE_COG_TOP_BELOW
        return all(math.hypot(xc - x2, zc - z2) >= (PLATE_COG_PACK if lay == (r2 < PLATE_COG_TOP_BELOW)
                                                    else PLATE_COG_OVER) * (r + r2) for x2, z2, r2 in placed)

    for r in PLATE_COG_RADII:                         # every cog of one size before the next, largest first
        for z in np.arange(z_front - 0.3, z_back, -PLATE_COG_GRID):
            for side in (-1, 1):
                for a in np.arange(PLATE_COG_INNER, 3.4, PLATE_COG_GRID):     # a = the cog's inner edge
                    if len(placed) < cap and fits(side * (a + r), z, r):
                        placed.append((side * (a + r), float(z), r))
    # two layers: the big cogs on the plate, the small ones one layer up over the gaps (they may overlap a big cog's
    # edge, never each other)
    layer = [1 if r < PLATE_COG_TOP_BELOW else 0 for _, _, r in placed]
    for n_, (xc, zc, r) in enumerate(placed):
        thick = PLATE_COG_THICK * (r / max(PLATE_COG_RADII)) ** 0.5
        tz = thick / (zmax - zmin)
        t = math.radians(37.0 * n_)
        c, s = math.cos(t), math.sin(t)
        sc = r / rad
        rx = (CV[:, 0] * c - CV[:, 1] * s) * sc
        ry = (CV[:, 0] * s + CV[:, 1] * c) * sc
        # cog plane (x, y) -> gun (x, z), thickness -> up: a mirror, so the winding flips
        P = np.stack([xc + rx, y_floor + layer[n_] * PLATE_COG_LAYER + (CV[:, 2] - zmin) * tz - 0.02, zc + ry],
                     axis=1)
        tris = CT[:, [0, 2, 1]].copy()
        PN = np.zeros_like(P)
        fn_raw = np.cross(P[tris[:, 1]] - P[tris[:, 0]], P[tris[:, 2]] - P[tris[:, 0]])
        for kk in range(3):
            np.add.at(PN, tris[:, kk], fn_raw)
        PN /= np.maximum(np.linalg.norm(PN, axis=1, keepdims=True), 1e-12)
        top = P[:, 1] > y_floor + layer[n_] * PLATE_COG_LAYER + 0.5 * thick
        assert (PN[top, 1] > 0).mean() > 0.3, 'plate cog faces down'
        parts.append((P, PN, tris))
    by = {r: sum(1 for p in placed if p[2] == r) for r in PLATE_COG_RADII}
    print('plate cogs: %d (by radius %s; side -1: %d, +1: %d; layers %s)'
          % (len(placed), by, sum(1 for p in placed if p[0] < 0), sum(1 for p in placed if p[0] > 0),
             {k_: layer.count(k_) for k_ in sorted(set(layer))}))
    return parts


def tube_end_cog(cog, tooth0, o):
    """Curator 2026-11-15: "add a Cog to the end of the Tube". The same cog standing on the rear end cap's outer face,
    coaxial with the tube, facing back: hole round the terminal nub (which stands through it like an axle), tooth
    tips at the cap's bead ring (so it clears the wood with the cap), END_COG_THICK thick, one tooth straight up."""
    CV, CN, CT = cog
    k = FIT
    H = 0.30 * k + 0.04
    T = COLLAR_R + TUBE_BEAD
    B = T - END_COG_TOOTH
    x, y = remap_cog_radii(CV, H, B, T)
    t = math.radians(90.0 - tooth0)
    c, s = math.cos(t), math.sin(t)
    zmin, zmax = CV[:, 2].min(), CV[:, 2].max()
    tz = END_COG_THICK / (zmax - zmin)
    # the cog's front (its max Z) faces back (-Z): Z mirrored, so the winding flips
    P = np.stack([o[0] + x * c - y * s, o[1] + x * s + y * c, o[2] - (CV[:, 2] - zmin) * tz], axis=1)
    tris = CT[:, [0, 2, 1]].copy()
    PN = np.zeros_like(P)
    fn_raw = np.cross(P[tris[:, 1]] - P[tris[:, 0]], P[tris[:, 2]] - P[tris[:, 0]])
    for kk in range(3):
        np.add.at(PN, tris[:, kk], fn_raw)
    PN /= np.maximum(np.linalg.norm(PN, axis=1, keepdims=True), 1e-12)
    back = P[:, 2] < o[2] - 0.5 * END_COG_THICK
    assert (PN[back, 2] < 0).mean() > 0.3, 'end cog faces the wrong way'
    print('tube end cog: hole %.2f, rim %.2f, tips %.2f, %.2f thick, z %.2f..%.2f'
          % (H, B, T, END_COG_THICK, P[:, 2].min(), P[:, 2].max()))
    return P, PN, tris


# ---- preview ---------------------------------------------------------------------------------------------

def lathe(profile, origin, axis, nseg, u_scale=1.0, v_scale=0.1):
    """Surface of revolution: profile = [(t along axis, radius), ...] in order. Every profile segment gets its own
    two rings (hard edge between segments, smooth around). Returns V, N, T, UV."""
    axis = np.asarray(axis, float) / np.linalg.norm(axis)
    a = np.array([1.0, 0, 0]) if abs(axis[0]) < 0.9 else np.array([0, 1.0, 0])
    e1 = np.cross(axis, a)
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(axis, e1)
    th = np.linspace(0, 2 * math.pi, nseg + 1)
    V, N, T, UV = [], [], [], []
    run = 0.0
    for (t0, r0), (t1, r1) in zip(profile[:-1], profile[1:]):
        dt, dr = t1 - t0, r1 - r0
        L = math.hypot(dt, dr)
        if L < 1e-9:
            continue
        nr, na = dt / L, -dr / L                         # outward normal in the (radius, axis) plane
        base = len(V)
        for t, r, v in ((t0, r0, run), (t1, r1, run + L)):
            for k, a_ in enumerate(th):
                radial = math.cos(a_) * e1 + math.sin(a_) * e2
                V.append(origin + axis * t + radial * r)
                N.append(radial * nr + axis * na)
                UV.append((u_scale * k / nseg, v_scale * v))
        for k in range(nseg):
            p, q = base + k, base + k + 1
            pn, qn = p + nseg + 1, q + nseg + 1
            T += [(p, q, qn), (p, qn, pn)]
        run += L
    V, N, T, UV = np.array(V), np.array(N), np.array(T, int), np.array(UV)
    fn = tri_normals(V, T)
    vn = N[T].mean(1)
    flip = (fn * vn).sum(1) < 0
    T[flip] = T[flip][:, [0, 2, 1]]
    return V, N, T, UV


def top_samples(V, T):
    """Points densely sampled on the rifle's upward-facing triangles (the wrist's top)."""
    N = tri_normals(V, T)
    up = T[N[:, 1] > 0.3]
    P0, P1, P2 = V[up[:, 0]], V[up[:, 1]], V[up[:, 2]]
    pts = []
    k = 10
    for a in range(k + 1):
        for b in range(k + 1 - a):
            u, v = a / k, b / k
            pts.append(P0 * (1 - u - v) + P1 * u + P2 * v)
    return np.concatenate(pts)


def top_height(samples, x, z, half=0.3):
    m = (np.abs(samples[:, 2] - z) < half) & (np.abs(samples[:, 0] - x) < half)
    assert m.any(), ('no wrist top at', x, z)
    return float(samples[m, 1].max())


def tube_axis(samples, barrel_y):
    """(origin at the rear end cap, unit direction rear -> front, length, axis height over the original wood along
    the tube): coaxial with the barrel (its axis y, x 0), running back from the breech. The rear end is found, not
    set (curator 2026-11-15, after the in-game look: "instead of cutting away just extend the tube length further
    out so it clears the wood"): the first z, going back, where the wrist top under the whole rear end fitting
    (cap, bevel and bead, across the bead's width) lies CAP_CLEARANCE under the bead ring's lowest point."""
    _, z1 = TUBE_Z
    front = top_height(samples, 0.0, -27.0)
    assert abs(front - TUBE_TOP_FRONT) < 0.15, ('wrist top moved', front)
    y = barrel_y
    k = FIT
    low = y - COLLAR_R - TUBE_BEAD - CAP_CLEARANCE
    reach = COLLAR_R + TUBE_BEAD
    cap_len = 0.44 * k
    z0 = None
    for z in np.arange(-34.0, -60.0, -0.05):
        m = ((samples[:, 2] > z - END_COG_THICK) & (samples[:, 2] < z + cap_len)
             & (np.abs(samples[:, 0] - TUBE_X) < reach))
        if m.any() and samples[m, 1].max() < low:
            z0 = float(z)
            break
    assert z0 is not None, 'the wrist never drops under the rear cap'
    zs = np.linspace(z0, z1, 41)
    ys = np.array([top_height(samples, TUBE_X, z) for z in zs])
    o = np.array([TUBE_X, y, z0])
    return o, np.array([0.0, 0.0, 1.0]), z1 - z0, y - ys


def channel_box(o, L):
    """The cut for the tube, a convex region given by its planes (n, c, name): inside where p . n >= c.
    floor  y >= yf (just under the tube's axis: the wood comes up round the tube's lower half)
    ramp   behind the rear cap the floor rises at CHANNEL_RAMP (rise per unit back) into the wrist
    front  z <= the breech plug's rear face
    sides  |x| <= CHANNEL_HALF_WIDTH (wider than the stock: no side walls)
    back   z >= the ramp's foot - CHANNEL_RAMP_REACH (a bound; the ramp has left the wood by then)
    Returns (planes, yf, z_ramp, z1)."""
    k = FIT
    yf = o[1] - CHANNEL_FLOOR_BELOW_AXIS
    zr = o[2] - 0.45 * k - CHANNEL_GAP
    z1 = CHANNEL_FRONT
    t = CHANNEL_RAMP
    half = CHANNEL_HALF_WIDTH
    planes = [(np.array([0, 1.0, 0]), yf, 'floor'),
              (np.array([0, 1.0, t]), yf + t * zr, 'ramp'),
              (np.array([0, 0, -1.0]), -z1, 'front'),
              (np.array([1.0, 0, 0]), -half, 'left'),
              (np.array([-1.0, 0, 0]), -half, 'right'),
              (np.array([0, 0, 1.0]), zr - CHANNEL_RAMP_REACH, 'back')]
    return planes, yf, zr, z1


def cut_channel(V, A, T, comp, planes):
    """Cut the convex region out of the chosen pieces of the rifle mesh. V = positions (n,3); A = per-vertex
    attributes (n,m) interpolated linearly on cut edges; T = triangles. Each triangle that meets the region is split
    plane by plane (Sutherland-Hodgman): the part outside a plane is kept, the part inside goes on to the next plane,
    and what is inside all of them is dropped. Returns new V, A, T and, per plane, the cut segments that bound the
    hole (each clipped to the region), for the closing faces."""
    newV, newA = [V], [A]
    nv = [len(V)]
    segs = {p[2]: [] for p in planes}

    def add(p, a):
        newV.append(p[None])
        newA.append(a[None])
        nv[0] += 1
        return nv[0] - 1

    def clip_seg(p, q, skip):
        """The part of segment p-q inside every plane but `skip`."""
        t0, t1 = 0.0, 1.0
        for n, c, name in planes:
            if name == skip:
                continue
            dp, dq = p @ n - c, q @ n - c
            if dp < 0 and dq < 0:
                return None
            if dp < 0:
                t0 = max(t0, dp / (dp - dq))
            elif dq < 0:
                t1 = min(t1, dp / (dp - dq))
        if t1 - t0 < 1e-6:
            return None
        return p + (q - p) * t0, p + (q - p) * t1

    # a triangle can only meet the region if every vertex is not outside one same plane
    D = np.stack([V @ n - c for n, c, _ in planes], 1)          # (nv, planes)
    meets = comp & ~(D[T] < 0).all(1).any(1)
    kept = [tuple(t) for t in T[~meets]]
    flags = list(comp[~meets])
    dropped = 0
    for tri in T[meets]:
        pieces = [[(int(i), V[i], A[i]) for i in tri]]
        for n, c, name in planes:
            nxt = []
            for poly in pieces:
                d = [p @ n - c for _, p, _ in poly]                 # >= 0: inside this plane
                if min(d) >= -1e-7:
                    nxt.append(poly)
                    continue
                if max(d) <= 1e-7:
                    out, ins = poly, []
                else:
                    out, ins, cut = [], [], []
                    for j in range(len(poly)):
                        a, b = poly[j], poly[(j + 1) % len(poly)]
                        da, db = d[j], d[(j + 1) % len(poly)]
                        if da >= 0:
                            ins.append(a)
                        else:
                            out.append(a)
                        if (da < 0) != (db < 0):
                            tt = da / (da - db)
                            p = a[1] + (b[1] - a[1]) * tt
                            at = a[2] + (b[2] - a[2]) * tt
                            vi = add(p, at)
                            out.append((vi, p, at))
                            ins.append((vi, p, at))
                            cut.append(p)
                    if len(cut) == 2:
                        s = clip_seg(cut[0], cut[1], name)
                        if s is not None:
                            segs[name].append(s)
                if len(out) >= 3:
                    for j in range(1, len(out) - 1):
                        kept.append((out[0][0], out[j][0], out[j + 1][0]))
                        flags.append(True)
                if len(ins) >= 3:
                    nxt.append(ins)
            pieces = nxt
        dropped += len(pieces)
    return (np.concatenate(newV), np.concatenate(newA), np.array(kept, int), np.array(flags, bool), segs,
            int(meets.sum()), dropped)


def pocket_box(o):
    """The second, deeper cut round the rear end cap (curator 2026-11-15, on the first in-game look: "cut away so that
    the end cap of the tube gold casing is fully visible"): floor just under the cap's bead ring, from in front of the
    bead back past the nub, then a ramp at CHANNEL_RAMP up into the wrist. Same plane form as channel_box."""
    k = FIT
    yp = o[1] - COLLAR_R - TUBE_BEAD - POCKET_GAP
    zr = o[2] - 0.45 * k - CHANNEL_GAP
    zf = o[2] + 0.44 * k + POCKET_GAP                  # just in front of the bead ring
    t = CHANNEL_RAMP
    half = CHANNEL_HALF_WIDTH
    planes = [(np.array([0, 1.0, 0]), yp, 'pfloor'),
              (np.array([0, 1.0, t]), yp + t * zr, 'pramp'),
              (np.array([0, 0, -1.0]), -zf, 'pfront'),
              (np.array([1.0, 0, 0]), -half, 'left'),
              (np.array([-1.0, 0, 0]), -half, 'right'),
              (np.array([0, 0, 1.0]), zr - CHANNEL_RAMP_REACH, 'back')]
    return planes, yp, zr, zf


def slot_box(o, z_front):
    """Curator 2026-11-15, in game: "might need cut away the wood a little to house the tube better" - from the strap
    back the wrist top ran through the glass's lower part, under the first cut's floor. A slot for the tube's rear
    half: floor just under the collars' bead ring, as wide as the bead ring (+CHANNEL_GAP), from z_front (the strap)
    back past the end cog and nub; wood walls wherever the wrist is wider than the slot. Same plane form."""
    k = FIT
    w = COLLAR_R + TUBE_BEAD + CHANNEL_GAP
    ys = o[1] - COLLAR_R - TUBE_BEAD - CHANNEL_GAP
    zb = o[2] - max(0.45 * k, END_COG_THICK) - CHANNEL_GAP
    planes = [(np.array([0, 1.0, 0]), ys, 'sfloor'),
              (np.array([0, 0, -1.0]), -z_front, 'sfront'),
              (np.array([0, 0, 1.0]), zb, 'sback'),
              (np.array([1.0, 0, 0]), -w, 'sleft'),
              (np.array([-1.0, 0, 0]), -w, 'sright')]
    return planes, ys, z_front, zb, w


def lockplate_uv_map(V, T, UV, comp):
    """Curator 2026-11-15: "make the plate look more like the side panels" (picture: the lock plate). UVs for the
    plate panel from the lock plate's own outer face: a panel point (x, z) is laid proportionally onto the lock
    plate's face (z along, |x| across -> y) and takes the UV of the lock-plate triangle there (barycentric in the
    face's (z, y) projection; nearest one, clamped, outside it), so the panel carries the lock plate's polished
    metal, grime and edge wear in the rifle's own texture set and shader."""
    ids, counts = np.unique(comp, return_counts=True)
    best = None
    for c in ids:
        sel = np.where(comp == c)[0]
        pv = V[np.unique(T[sel])]
        if pv[:, 0].max() < -1.5 and pv[:, 2].max() - pv[:, 2].min() > 15 and (best is None or len(sel) > best[1]):
            best = (c, len(sel))
    assert best is not None, 'no lock plate'
    sel = np.where(comp == best[0])[0]
    n = tri_normals(V, T[sel])
    face = sel[n[:, 0] < -0.7]
    assert len(face) > 10, ('lock plate outer face', len(face))
    P = V[T[face]]
    U = UV[T[face]]
    a, b, cc = P[:, 0, [2, 1]], P[:, 1, [2, 1]], P[:, 2, [2, 1]]
    den = (b[:, 1] - cc[:, 1]) * (a[:, 0] - cc[:, 0]) + (cc[:, 0] - b[:, 0]) * (a[:, 1] - cc[:, 1])
    ok = np.abs(den) > 1e-9
    a, b, cc, den, U = a[ok], b[:, :][ok], cc[ok], den[ok], U[ok]
    cen = (a + b + cc) / 3
    fz0, fz1 = cen[:, 0].min(), cen[:, 0].max()
    fy0, fy1 = cen[:, 1].min(), cen[:, 1].max()
    print('plate panel UVs from the lock plate (piece %d, %d outer-face triangles, z %.1f..%.1f, y %.1f..%.1f)'
          % (best[0], len(face), fz0, fz1, fy0, fy1))

    def make(z0, z1, xmax):
        def uvmap(p):
            # onto the lock plate's smooth tail (the curator's picture), 0.75 along / 1:1 across: its polish and
            # wear at about their own size; the middle of the face holds the dark hammer-pivot area
            zz = fz0 + PANEL_TAIL_MID + 0.75 * (p[2] - 0.5 * (z0 + z1))
            yy = 0.5 * (fy0 + fy1) + (abs(p[0]) - 0.5 * xmax)
            l1 = ((b[:, 1] - cc[:, 1]) * (zz - cc[:, 0]) + (cc[:, 0] - b[:, 0]) * (yy - cc[:, 1])) / den
            l2 = ((cc[:, 1] - a[:, 1]) * (zz - cc[:, 0]) + (a[:, 0] - cc[:, 0]) * (yy - cc[:, 1])) / den
            L = np.stack([l1, l2, 1 - l1 - l2], 1)
            inside = np.where((L >= -1e-6).all(1))[0]
            if len(inside):
                i = inside[0]
                w = L[i]
            else:
                i = int(np.argmin(((cen - [zz, yy]) ** 2).sum(1)))
                w = np.clip(L[i], 0, None)
                w = w / w.sum()
            u, v = w @ U[i]
            return (float(u), float(v))
        return uvmap
    return make


def plate_panel(floor_segs, y_floor, z_lo, z_hi, uvmap):
    """The plate as a panel like the lock plate: raised PANEL_H over the cut's floor, its top inset PANEL_BEVEL from
    the cut's outline on both sides, a bevel running down to the outline; it runs from z_hi (the breech wall) back to
    z_lo (the slot's front), across under the tube. Cut into cells about PANEL_CELL square, so each vertex's UV
    (sampled from the lock plate) is interpolated over a small patch only. (V, N, T, UV) for the rifle shape."""
    zs = sorted({round(float(p[2]), 6) for s in floor_segs for p in s} | {round(z_lo, 6), round(z_hi, 6)}
                | {round(float(z), 6) for z in np.arange(z_lo, z_hi, PANEL_CELL)})
    zs = [z for z in zs if z_lo - 1e-6 <= z <= z_hi + 1e-6]
    rows = []
    for z in zs:
        sp = outline_span(floor_segs, min(max(z, z_lo + 1e-5), z_hi - 1e-5))
        if sp is not None and sp[1] - sp[0] > 2 * PANEL_BEVEL + 0.05:
            rows.append((z, sp[0], sp[1]))
    assert len(rows) > 3, 'no panel'
    V, N, T, UV = [], [], [], []
    yt = y_floor + PANEL_H

    def quad(ps, n):
        base = len(V)
        for p in ps:
            V.append(np.array(p, float))
            N.append(np.array(n, float) / np.linalg.norm(n))
            UV.append(uvmap(p))
        tri = [(base, base + 1, base + 2), (base, base + 2, base + 3)]
        if np.cross(V[base + 1] - V[base], V[base + 2] - V[base]) @ np.array(n, float) < 0:
            tri = [(a, c, b) for a, b, c in tri]
        T.extend(tri)

    bev_n = lambda s: (s * PANEL_H, PANEL_BEVEL, 0.0)
    for (za, la, ra), (zb, lb, rb) in zip(rows[:-1], rows[1:]):
        ncol = max(1, int(math.ceil(max(ra - la, rb - lb) / PANEL_CELL)))
        for c_ in range(ncol):
            f0, f1 = c_ / ncol, (c_ + 1) / ncol
            xa0, xa1 = la + PANEL_BEVEL + f0 * (ra - la - 2 * PANEL_BEVEL), la + PANEL_BEVEL + f1 * (ra - la - 2 * PANEL_BEVEL)
            xb0, xb1 = lb + PANEL_BEVEL + f0 * (rb - lb - 2 * PANEL_BEVEL), lb + PANEL_BEVEL + f1 * (rb - lb - 2 * PANEL_BEVEL)
            quad([(xa0, yt, za), (xa1, yt, za), (xb1, yt, zb), (xb0, yt, zb)], (0, 1, 0))
        quad([(ra - PANEL_BEVEL, yt, za), (ra, y_floor, za), (rb, y_floor, zb), (rb - PANEL_BEVEL, yt, zb)], bev_n(1))
        quad([(la + PANEL_BEVEL, yt, za), (la, y_floor, za), (lb, y_floor, zb), (lb + PANEL_BEVEL, yt, zb)],
             bev_n(-1))
    z, l, r = rows[0]                                  # the rear end: a bevel down toward the slot
    quad([(l + PANEL_BEVEL, yt, z), (r - PANEL_BEVEL, yt, z), (r, y_floor, z - PANEL_BEVEL),
          (l, y_floor, z - PANEL_BEVEL)], (0, PANEL_BEVEL, -PANEL_H))
    return np.array(V), np.array(N), np.array(T, int), np.array(UV)


def plate_rivets(floor_segs, y_top, z_lo, z_hi, tubes=()):
    """A pair of round rivets on each side of the panel, like the lock plate's (one behind the other, near the outer
    edge), at the first z (from the front) with room. Returns (parts [(P, PN, T, UV)], circles [(x, z, r)])."""
    parts, circles = [], []
    prof = [(-0.1, 0.0), (-0.1, RIVET_R), (0.03, RIVET_R), (0.09, RIVET_R * 0.75), (0.12, RIVET_R * 0.35),
            (0.13, 0.0)]
    for side in (-1, 1):
        for z in np.arange(z_hi - 1.0, z_lo + 1.0, -0.1):
            sp1, sp2 = outline_span(floor_segs, z), outline_span(floor_segs, z - RIVET_GAP)
            if sp1 is None or sp2 is None:
                continue
            e = min((sp1[1] if side > 0 else -sp1[0]), (sp2[1] if side > 0 else -sp2[0]))
            x = e - PANEL_BEVEL - RIVET_R - 0.12
            clear = all(abs(side * x - tx) > SIDE_TUBE_COG_R + RIVET_R + 0.05 or not (tr - RIVET_R - 0.4 < zz_ < tf + RIVET_R + 0.4)
                        for _s, tx, tr, tf in tubes for zz_ in (z, z - RIVET_GAP))
            if x - RIVET_R >= RIVET_MIN_X and clear:
                for zz in (z, z - RIVET_GAP):
                    V, N, T, UV = lathe(prof, np.array([side * x, y_top, zz]), (0, 1.0, 0), 12)
                    parts.append((V, N, T, UV))
                    circles.append((side * x, zz, RIVET_R))
                break
    print('plate rivets: %s' % [(round(x, 2), round(z, 2)) for x, z, _ in circles])
    return parts, circles


def plate_wires(floor_segs, y_top, z_start, z_end, tubes=()):
    """Curator 2026-11-15: "could you add some wires maybe to the plate?" (sketch: two per side, from under the front
    collar, snaking back along the plate). Each wire is a gold tube (WIRE_R, 8 sides) lying on the panel along a wavy
    path: offset from the axis = its lane + WIRE_WAVE x sin (growing in from the collar), clamped inside the panel's
    top (less WIRE_EDGE) and outside the glass; from under the front collar's edge back to z_end. Returns (parts
    [(V, N, T, UV)], paths [[(x, z), ...]]) - the paths keep the plate cogs off the wires."""
    parts, paths = [], []
    for side in (-1, 1):
        for lane, phase in WIRE_LANES:
            pts = []
            for z in np.arange(z_start, z_end, -0.08):
                t = (z_start - z) / max(z_start - z_end, 1e-6)
                off = lane + WIRE_WAVE * math.sin(2 * math.pi * (1.6 * t + phase)) * min(1.0, t * 4)
                sp = outline_span(floor_segs, z)
                lo = GLASS_R + WIRE_R + 0.03
                hi = ((sp[1] if side > 0 else -sp[0]) - PANEL_BEVEL - WIRE_EDGE - WIRE_R) if sp is not None else lo
                for ts, tx, tr, tf in tubes:                # inboard of the side tube
                    if ts == side and tr - SIDE_TUBE_COG_R - 0.1 <= z <= tf + SIDE_TUBE_COG_R + 0.1:
                        hi = min(hi, abs(tx) - SIDE_TUBE_COG_R - WIRE_R - 0.04)
                pts.append((side * min(max(off, lo), max(hi, lo)), float(z)))
            if len(pts) < 4:
                continue
            P = np.array([[x, y_top + WIRE_R - 0.01, z] for x, z in pts])
            V, N, T, UV = [], [], [], []
            seg = 8
            for i, p in enumerate(P):
                d = P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]
                d /= np.linalg.norm(d)
                e1 = np.cross(d, [0, 1.0, 0])
                e1 /= np.linalg.norm(e1)
                e2 = np.cross(e1, d)
                for k in range(seg + 1):
                    a = 2 * math.pi * k / seg
                    nn = math.cos(a) * e1 + math.sin(a) * e2
                    V.append(p + nn * WIRE_R)
                    N.append(nn)
                    UV.append((k / seg * 0.1, i * 0.02))
            for i in range(len(P) - 1):
                for k in range(seg):
                    a, b = i * (seg + 1) + k, i * (seg + 1) + k + 1
                    T += [(a, a + seg + 1, b), (b, a + seg + 1, b + seg + 1)]
            V, N, T = np.array(V), np.array(N), np.array(T, int)
            fn = tri_normals(V, T)
            flip = (fn * N[T].mean(1)).sum(1) < 0
            T[flip] = T[flip][:, [0, 2, 1]]
            parts.append((V, N, T, np.array(UV)))
            paths.append(pts)
    print('plate wires: %d' % len(paths))
    return parts, paths


def groove_box(o, z_front):
    """Curator 2026-11-15 (in game, after a box slot left only a gap): "I still want the wood, just space for the
    tube to sit in". A groove: a GROOVE_SIDES-sided prism round the tube's axis, circumscribing a circle of the bead
    ring's radius + CHANNEL_GAP, from z_front (the strap) back past the end cog and nub. Only wood inside it goes;
    the wood beside and under the tube stays. Planes in the cut's form (inside where p . n >= c); also returns the
    prism's faces (n, centre offset, half width) for groove_faces."""
    k = FIT
    r_in = COLLAR_R + TUBE_BEAD + CHANNEL_GAP          # the faces' distance from the axis
    R = r_in / math.cos(math.pi / GROOVE_SIDES)          # the corners'

    zb = o[2] - max(0.45 * k, END_COG_THICK) - CHANNEL_GAP
    planes, faces = [], []
    for i in range(GROOVE_SIDES):
        a = 2 * math.pi * (i + 0.5) / GROOVE_SIDES
        radial = np.array([math.cos(a), math.sin(a), 0.0])
        n = -radial                                         # inside = toward the axis
        c = float(n @ (np.array([o[0], o[1], 0.0]) + radial * r_in))
        planes.append((n, c, 'g%d' % i))
        faces.append((n, radial, r_in * math.tan(math.pi / GROOVE_SIDES)))
    planes += [(np.array([0, 0, -1.0]), -z_front, 'gfront'), (np.array([0, 0, 1.0]), zb, 'gback')]
    return planes, faces, r_in, zb


def groove_faces(segs, faces, o, r_in, z_lo, z_hi, inside, y_front, uvmap):
    """Closing faces of the groove. Each prism face is filled where it lies in the wood: for each z interval (break
    points at the cut segments' ends and every GROOVE_STEP), the face's width is split at the cut outline's
    crossings and each piece whose middle is inside the wood (inside(p)) becomes a quad. The front end wall (the
    prism's cross-section at z_hi clipped at the wood's height there, y_front) is a fan. (V, N, T, UV)."""
    V, N, T, UV = [], [], [], []
    ax = np.array([o[0], o[1], 0.0])

    def quad(ps, n):
        base = len(V)
        for p in ps:
            V.append(np.array(p, float))
            N.append(np.array(n, float))
            UV.append(uvmap(p))
        tri = [(base, base + 1, base + 2), (base, base + 2, base + 3)]
        if np.cross(V[base + 1] - V[base], V[base + 2] - V[base]) @ np.array(n, float) < 0:
            tri = [(a, c, b) for a, b, c in tri]
        T.extend(tri)

    for i, (n, radial, h) in enumerate(faces):
        t = np.array([-radial[1], radial[0], 0.0])
        fc = ax + radial * r_in
        fs = segs['g%d' % i]
        zs = sorted({round(float(p[2]), 6) for s in fs for p in s}
                    | {round(float(z), 6) for z in np.arange(z_lo, z_hi, GROOVE_STEP)} | {round(z_lo, 6), round(z_hi, 6)})
        zs = [z for z in zs if z_lo - 1e-6 <= z <= z_hi + 1e-6]

        def cuts(z):
            us = []
            for p, q in fs:
                a_, b_ = (p, q) if p[2] <= q[2] else (q, p)
                if a_[2] - 1e-7 <= z <= b_[2] + 1e-7 and b_[2] - a_[2] > 1e-9:
                    m = a_ + (b_ - a_) * (z - a_[2]) / (b_[2] - a_[2])
                    us.append(float((m - fc) @ t))
            return sorted(us)

        def strip(za, zb, depth=0):
            """Fill one z interval of this face; where the outline crosses it a different number of times at its two
            ends, split it until they agree (skipping it left notches in the groove's edge)."""
            if zb - za < 1e-5:
                return
            ca, cb = cuts(za + 1e-6), cuts(zb - 1e-6)
            if len(ca) != len(cb):
                if depth < 10:
                    zm_ = 0.5 * (za + zb)
                    strip(za, zm_, depth + 1)
                    strip(zm_, zb, depth + 1)
                return
            ba, bb = [-h] + ca + [h], [-h] + cb + [h]
            for k in range(len(ba) - 1):
                um = 0.25 * (ba[k] + ba[k + 1] + bb[k] + bb[k + 1])
                pm = fc + t * um
                pm[2] = 0.5 * (za + zb)
                if max(ba[k + 1] - ba[k], bb[k + 1] - bb[k]) < 1e-6 or not inside(pm):
                    continue
                pts = []
                for z, u in ((za, ba[k]), (za, ba[k + 1]), (zb, bb[k + 1]), (zb, bb[k])):
                    p = fc + t * u
                    p[2] = z
                    pts.append(p)
                quad(pts, n)

        for za, zb in zip(zs[:-1], zs[1:]):
            strip(za, zb)
    # the front end wall: the prism's cross-section at z_hi, below the wood, facing back into the groove
    poly = [ax + radial * r_in + np.array([-radial[1], radial[0], 0.0]) * h for n, radial, h in faces]
    clipped = []                                       # Sutherland-Hodgman: keep y <= y_front
    for j in range(len(poly)):
        a, b = poly[j], poly[(j + 1) % len(poly)]
        da, db = y_front - a[1], y_front - b[1]
        if da >= 0:
            clipped.append(a)
        if (da >= 0) != (db >= 0):
            clipped.append(a + (b - a) * (da / (da - db)))
    pts = [np.array([p[0], p[1], z_hi]) for p in clipped]
    if len(pts) >= 3:
        cen = np.mean(pts, 0)
        for a, b in zip(pts, pts[1:] + pts[:1]):
            base = len(V)
            for p in (cen, a, b):
                V.append(p)
                N.append(np.array([0, 0, -1.0]))
                UV.append(uvmap(p))
            tri = (base, base + 1, base + 2)
            if np.cross(V[base + 1] - V[base], V[base + 2] - V[base]) @ np.array([0, 0, -1.0]) < 0:
                tri = (base, base + 2, base + 1)
            T.append(tri)
    return np.array(V), np.array(N), np.array(T, int), np.array(UV)


def sweep_tube(P, r, seg=10):
    """A tube of radius r swept along the polyline P (n, 3), with rounded ends. (V, N, T, UV)."""
    V, N, T, UV = [], [], [], []
    frames = []
    for i, p in enumerate(P):
        d = P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]
        d /= np.linalg.norm(d)
        e1 = np.cross(d, [0, 1.0, 0])
        e1 /= np.linalg.norm(e1)
        e2 = np.cross(e1, d)
        frames.append((d, e1, e2))
        for k in range(seg + 1):
            a = 2 * math.pi * k / seg
            nn = math.cos(a) * e1 + math.sin(a) * e2
            V.append(p + nn * r)
            N.append(nn)
            UV.append((k / seg * 0.15, i * 0.03))
    for i in range(len(P) - 1):
        for k in range(seg):
            a, b = i * (seg + 1) + k, i * (seg + 1) + k + 1
            T += [(a, a + seg + 1, b), (b, a + seg + 1, b + seg + 1)]
    V, N, T, UV = np.array(V), np.array(N), np.array(T, int), np.array(UV)
    fn = tri_normals(V, T)
    flip = (fn * N[T].mean(1)).sum(1) < 0
    T[flip] = T[flip][:, [0, 2, 1]]
    parts = [(V, N, T, UV)]
    cap = [(0.0, r), (0.35 * r, 0.94 * r), (0.7 * r, 0.7 * r), (0.95 * r, 0.3 * r), (r, 0.0)]
    for p, (d, _e1, _e2), sgn in ((P[0], frames[0], -1.0), (P[-1], frames[-1], 1.0)):
        parts.append(lathe(cap, p, d * sgn, seg))
    return parts


def bezier(A, dA, B, dB, n):
    """n points of the cubic from A (leaving along dA) to B (arriving along dB), A and B included."""
    s_ = np.linalg.norm(B - A) / 3.0
    c1, c2 = A + dA / np.linalg.norm(dA) * s_, B - dB / np.linalg.norm(dB) * s_
    t = np.linspace(0, 1, n)[:, None]
    return (1 - t) ** 3 * A + 3 * (1 - t) ** 2 * t * c1 + 3 * (1 - t) * t ** 2 * c2 + t ** 3 * B


def groove_edge_tubes(gsegs, z_lo, z_hi, o, side_tubes, y_side):
    """Curator 2026-11-15, in game: the groove's edges looked jagged - "maybe we could hide them with more metal
    tubing?" - then "the pipes aren't connected to anything and look a little creased in areas, have them bow
    smoothly and then connect to the end of the tube parts". A gold tube (EDGE_TUBE_R) along each side's groove edge:
    the edge traced from the groove's own cut outline (per EDGE_TUBE_BIN of z, the outline point farthest from the
    axis on that side) and fitted with a cubic in z (no kinks); its front end bends (cubic Bezier, tangents matched)
    into the rear end of that side's metal side tube, along its axis; its rear end into the main tube's rear collar,
    entering its front shoulder low on that side."""
    pts = np.array([p for name, ss in gsegs.items() if name.startswith('g') and name[1:].isdigit()
                    for s in ss for p in s])
    assert len(pts), 'no groove outline'
    k = FIT
    parts, report = [], []
    for side in (-1, 1):
        sel = pts[(pts[:, 0] - o[0]) * side > 0.3]
        path = []
        for z in np.arange(z_lo + 0.5 * EDGE_TUBE_BIN, z_hi, EDGE_TUBE_BIN):
            m = np.abs(sel[:, 2] - z) < 0.5 * EDGE_TUBE_BIN
            if m.any():
                q = sel[m][np.argmax((sel[m][:, 0] - o[0]) * side)]
                path.append((q[0], q[1], z))
        assert len(path) > 6, ('no groove edge', side)
        P = np.array(path)
        cx = np.polyfit(P[:, 2], P[:, 0], 3)
        cy = np.polyfit(P[:, 2], P[:, 1] + EDGE_TUBE_R * 0.4, 3)
        curve = lambda z: np.array([np.polyval(cx, z), np.polyval(cy, z), z])
        tangent = lambda z: np.array([np.polyval(np.polyder(cx), z), np.polyval(np.polyder(cy), z), 1.0])
        z0, z1 = P[0, 2] + EDGE_TUBE_TRIM, P[-1, 2] - EDGE_TUBE_TRIM
        mid = np.array([curve(z) for z in np.arange(z0, z1 + 1e-6, 0.12)])
        # front: into the rear end of this side's side tube, along its axis
        st = [t_ for t_ in side_tubes if t_[0] == side][0]
        F = np.array([st[1], y_side, st[2] - SIDE_TUBE_COG_T - 0.03])
        front = bezier(mid[-1], tangent(z1), F, np.array([0, 0, 1.0]), 14)
        # rear: into the rear collar's front shoulder, low on this side
        a = math.radians(EDGE_TUBE_COLLAR_ANGLE)
        rr = 1.3 * k - 0.05
        Rt = np.array([o[0] + side * rr * math.cos(a), o[1] - rr * math.sin(a), o[2] + 0.95 * k - 0.05])
        rear = bezier(Rt, np.array([0, 0, 1.0]), mid[0], tangent(z0), 14)
        S = np.concatenate([rear[:-1], mid, front[1:]])
        parts += sweep_tube(S, EDGE_TUBE_R, 12)
        report.append((side, round(float(S[0, 2]), 2), round(float(S[-1, 2]), 2), len(S)))
    print('groove edge tubes (side, z from, z to, points): %s' % report)
    return parts


def side_tube_layout(floor_segs, z_lo, z_hi):
    """Curator 2026-11-15: "on either side of the plate add 2 tubes with cogs on the end". One small tube a side,
    lying on the panel along the gun: for each side, over axis offsets x from SIDE_TUBE_X_MAX inward to
    SIDE_TUBE_X_MIN (clear of the main glass), the longest stretch within z_lo..z_hi where the panel's top leaves
    room for the end cogs; the longest overall (the outermost among lengths within 0.2), at least SIDE_TUBE_MIN_LEN. Returns [(side, x (signed), z_rear,
    z_front)]."""
    out = []
    reach = SIDE_TUBE_COG_R + 0.04
    zs = np.arange(z_hi, z_lo, -0.05)
    for side in (-1, 1):
        best = None
        for x in np.arange(SIDE_TUBE_X_MAX, SIDE_TUBE_X_MIN - 1e-6, -0.05):
            run, best_run = [], []
            for z in zs:
                sp = outline_span(floor_segs, z)
                ok = sp is not None and (sp[1] if side > 0 else -sp[0]) - PANEL_BEVEL - reach >= x
                if ok:
                    run.append(z)
                    if len(run) > len(best_run):
                        best_run = list(run)
                else:
                    run = []
            if best_run:
                length = best_run[0] - best_run[-1]
                # the longest tube; among nearly equal lengths the outermost (x runs outward-first)
                if best is None or length > best[4] + 0.2:
                    best = (side, float(side * x), float(best_run[-1]) + reach, float(best_run[0]) - reach, length)
        assert best is not None and best[4] >= SIDE_TUBE_MIN_LEN, ('no room for a side tube', side, best)
        out.append(best[:4])
    print('side tubes (side, x, z rear, z front): %s' % [tuple(round(v, 2) for v in b) for b in out])
    return out


def side_tube_parts(cog, tooth0, tubes, y_top):
    """The side tubes, all gold metal (curator: "metal tubes"): a pipe of SIDE_TUBE_R, a collar at each end and a cog
    on each end face (axis along the gun, an axle nub through it), standing on the panel. (V, N, T, UV or None for
    the cog's own UVs) each."""
    CV, CN, CT = cog
    parts = []
    zmin, zmax = CV[:, 2].min(), CV[:, 2].max()
    collar = [(0.0, 0.0), (0.0, SIDE_TUBE_COLLAR), (SIDE_TUBE_COLLAR_LEN, SIDE_TUBE_COLLAR),
              (SIDE_TUBE_COLLAR_LEN, SIDE_TUBE_R + 0.02), (SIDE_TUBE_COLLAR_LEN + 0.15, SIDE_TUBE_R + 0.02)]
    nub = [(-0.06, 0.0), (-0.06, 0.08), (SIDE_TUBE_COG_T + 0.08, 0.08), (SIDE_TUBE_COG_T + 0.08, 0.0)]
    for side, x, zr, zf in tubes:
        y = y_top + SIDE_TUBE_COG_R + 0.01                  # the end cogs stand on the panel
        parts.append(lathe([(0.0, SIDE_TUBE_R), (zf - zr, SIDE_TUBE_R)], np.array([x, y, zr]), (0, 0, 1.0), 16,
                           u_scale=0.5, v_scale=0.15))
        for zend, d in ((zr, 1.0), (zf, -1.0)):
            o = np.array([x, y, zend])
            V, N, T, UV = lathe(collar, o, (0, 0, d), 16)
            parts.append((V, N, T, UV))
            # the cog on the end face, facing out (along -d), its hole round the nub
            H = 0.1
            Tt = SIDE_TUBE_COG_R
            B = Tt - 0.12
            xx, yy = remap_cog_radii(CV, H, B, Tt)
            tz = SIDE_TUBE_COG_T / (zmax - zmin)
            t = math.radians(90.0 - tooth0)
            c, s_ = math.cos(t), math.sin(t)
            P = np.stack([x + xx * c - yy * s_, y + xx * s_ + yy * c, zend - d * (CV[:, 2] - zmin) * tz], axis=1)
            tris = CT[:, [0, 2, 1]].copy() if d > 0 else CT.copy()
            PN = np.zeros_like(P)
            fn_raw = np.cross(P[tris[:, 1]] - P[tris[:, 0]], P[tris[:, 2]] - P[tris[:, 0]])
            for kk in range(3):
                np.add.at(PN, tris[:, kk], fn_raw)
            PN /= np.maximum(np.linalg.norm(PN, axis=1, keepdims=True), 1e-12)
            outward = P[:, 2] * d < (zend - d * 0.5 * SIDE_TUBE_COG_T) * d
            assert (PN[outward, 2] * -d > 0).mean() > 0.3, 'side tube cog faces the wrong way'
            parts.append((P, PN, tris, None))
            V, N, T, UV = lathe(nub, np.array([x, y, zend]), (0, 0, -d), 10)
            parts.append((V, N, T, UV))
    return parts


def close_cut(segs, planes, fills, drops, floor_y, uvmaps):
    """Faces closing a cut. Fill planes (floor, ramp: not vertical, normal without X): each plane's cross-section of
    the stock, filled from its cut outline by strips between the outline's break points (between two, each side is
    one straight segment; inner cavities such as the lock mortise are covered over: the lock stands in the wood).
    Drop planes (vertical): each cut edge carried straight down to floor_y. Returns {group: (V, N, T, UV)}, groups
    each fill plane's name and each drop plane's name; uvmaps[group](point) gives a vertex's UVs."""
    out = {}
    pl = {name: (n, c) for n, c, name in planes}

    def group(name):
        if name not in out:
            out[name] = ([], [], [], [])
        return out[name]

    def quad(gname, ps, n, coords):
        V, N, T, UV = group(gname)
        base = len(V)
        for p in ps:
            V.append(p)
            N.append(n)
            UV.append(uvmaps[gname](p))
        tri = [(base, base + 1, base + 2), (base, base + 2, base + 3)]
        if np.cross(ps[1] - ps[0], ps[2] - ps[0]) @ n < 0:
            tri = [(a, c, b) for a, b, c in tri]
        T.extend(tri)

    def fill(gname, fs, yfun, n):
        zs = sorted({round(float(p[2]), 6) for s in fs for p in s})

        def span(z):
            xs = []
            for p, q in fs:
                a, b = (p, q) if p[2] <= q[2] else (q, p)
                if a[2] - 1e-7 <= z <= b[2] + 1e-7 and b[2] - a[2] > 1e-9:
                    xs.append(a[0] + (b[0] - a[0]) * (z - a[2]) / (b[2] - a[2]))
            return (min(xs), max(xs)) if len(xs) >= 2 else None

        made = 0
        for za, zb in zip(zs[:-1], zs[1:]):
            if zb - za < 1e-5:
                continue
            sa, sb = span(za + 1e-5), span(zb - 1e-5)
            if sa is None or sb is None:
                continue
            ps = [np.array([x, yfun(z), z]) for x, z in ((sa[0], za), (sa[1], za), (sb[1], zb), (sb[0], zb))]
            quad(gname, ps, n, lambda p: (p[2], p[0]))
            made += 1
        return made

    for name in fills:
        n, c = pl[name]
        assert abs(n[0]) < 1e-9 and n[1] > 0, name
        made = fill(name, segs[name], lambda z, n=n, c=c: (c - n[2] * z) / n[1], n / np.linalg.norm(n))
        # the floor must close something; the ramp only where the wrist still stands over the floor behind the tube
        assert made or name != fills[0], ('no faces for', name)
    for name in drops:
        n, c = pl[name]
        for p, q in segs[name]:
            if abs(p[1] - floor_y) < 1e-4 and abs(q[1] - floor_y) < 1e-4:
                continue
            pd, qd = p.copy(), q.copy()
            pd[1] = qd[1] = floor_y
            quad(name, [p, q, qd, pd], n, lambda p: (p[0], p[1]))
    for name in ('left', 'right', 'back'):
        assert not segs.get(name), ('the cut reached a side or its back bound', name)
    return {k: (np.array(v[0]), np.array(v[1]), np.array(v[2], int), np.array(v[3])) for k, v in out.items()}


def wood_uv_map(V, T, UV, metal, mask, z0, z1):
    """UVs for cut faces: a point takes the UV of the original stock surface straight above it (projected along Y
    onto the upward-facing stock triangles between z0 and z1, the wood the cut removes; the highest one if several),
    so the cut faces carry the wood that was there and meet the uncut wood without a seam. Outside the top's
    footprint, the nearest top triangle's barycentric weights, clamped. (A single planar map through one triangle,
    the first try, ran off its UV island onto metal; the butt-side source of the first build read paler in game.)"""
    n = tri_normals(V, T)
    c = V[T].mean(1)
    sel = np.where(mask & (n[:, 1] > 0.2) & (c[:, 2] > z0 - 1) & (c[:, 2] < z1 + 1))[0]
    assert len(sel) > 20, ('no wrist top to take wood from', len(sel))
    P = V[T[sel]]                       # (k, 3, 3)
    U = UV[T[sel]]                      # (k, 3, 2)
    a, b, cc = P[:, 0, [0, 2]], P[:, 1, [0, 2]], P[:, 2, [0, 2]]
    den = (b[:, 1] - cc[:, 1]) * (a[:, 0] - cc[:, 0]) + (cc[:, 0] - b[:, 0]) * (a[:, 1] - cc[:, 1])
    ok = np.abs(den) > 1e-9
    P, U, a, b, cc, den = P[ok], U[ok], a[ok], b[ok], cc[ok], den[ok]
    cen = (a + b + cc) / 3
    H, W = metal.shape

    def uvmap(p):
        x, z = p[0], p[2]
        l1 = ((b[:, 1] - cc[:, 1]) * (x - cc[:, 0]) + (cc[:, 0] - b[:, 0]) * (z - cc[:, 1])) / den
        l2 = ((cc[:, 1] - a[:, 1]) * (x - cc[:, 0]) + (a[:, 0] - cc[:, 0]) * (z - cc[:, 1])) / den
        l3 = 1 - l1 - l2
        L = np.stack([l1, l2, l3], 1)
        inside = (L >= -1e-6).all(1)
        if inside.any():
            ys = (L[inside, :, None] * P[inside]).sum(1)[:, 1]
            i = np.where(inside)[0][np.argmax(ys)]
            w = L[i]
        else:
            i = int(np.argmin(((cen - [x, z]) ** 2).sum(1)))
            w = np.clip(L[i], 0, None)
            w = w / w.sum()
        u, v = w @ U[i]
        assert metal[int(v % 1 * (H - 1)), int(u % 1 * (W - 1))] < 0.5, ('cut-face wood UV landed on metal', p, u, v)
        return (float(u), float(v))
    print('cut faces take their wood from %d wrist-top triangles straight above them' % len(P))
    return uvmap


def tube_fittings(o, d, L, samples):
    """Gold: an end fitting at each end (terminal nub, cap, bevel, bead, collar running into the glass), a strap
    round the middle and a screw head on the wood at each of its feet. (V, N, T, UV) lists for the cog shape."""
    G = GLASS_R
    k = FIT
    end = [(-0.45 * k, 0.0), (-0.45 * k, 0.30 * k), (0.0, 0.30 * k), (0.0, 1.25 * k), (0.12 * k, COLLAR_R),
           (0.30 * k, COLLAR_R), (0.30 * k, COLLAR_R + TUBE_BEAD), (0.44 * k, COLLAR_R + TUBE_BEAD),
           (0.44 * k, COLLAR_R),
           (0.80 * k, COLLAR_R), (0.95 * k, 1.30 * k), (0.95 * k, G + 0.03), (1.30 * k, G + 0.03)]
    front = end if TUBE_FRONT_NUB else [(0.0, 0.0)] + end[3:]
    parts = [lathe(end, o, d, TUBE_SEG), lathe(front, o + d * L, -d, TUBE_SEG)]
    m = o + d * (0.5 * L)
    rs = G + 0.12
    strap = [(-0.2, G - 0.02), (-0.2, rs), (0.2, rs), (0.2, G - 0.02)]
    parts.append(lathe(strap, m, d, TUBE_SEG))
    # a screw head on the wood just outside each side of the strap; its axis is the wrist's up at the strap
    up = np.cross(d, np.array([1.0, 0, 0]))
    up = up if up[1] > 0 else -up
    screw = [(-0.25 * k, 0.0), (-0.25 * k, 0.36 * k), (0.10 * k, 0.36 * k), (0.18 * k, 0.27 * k), (0.24 * k, 0.0)]
    # legs: a post from under the tube to the wrist top, a flange on the wood (sunk 0.2) and a saddle under the tube
    for zl in TUBE_LEGS:
        assert TUBE_Z[0] + 1.5 * k < zl < TUBE_Z[1] - 1.5 * k, ('leg off the tube', zl)
        wood = top_height(samples, o[0], zl, 0.25)
        top = o[1] - G + 0.1                               # just inside the glass's underside
        h = top - wood + 0.2
        assert h > 0.5, ('leg too short: the tube sits on the wood there', zl, h)
        leg = [(-0.2, 0.0), (-0.2, 0.75), (0.0, 0.75), (0.12, 0.42), (h - 0.35, 0.36), (h - 0.2, 0.62),
               (h, 0.62), (h, 0.0)]
        parts.append(lathe(leg, np.array([o[0], wood, zl]), (0, 1.0, 0), 16))
    for sgn in ((-1, 1) if TUBE_SCREWS else ()):
        x = sgn * (rs + 0.25)
        y = top_height(samples, x, m[2], 0.25)
        parts.append(lathe(screw, np.array([x, y, m[2]]), up, 16))
    return parts


def tube_glass(o, d, L):
    return lathe([(0.0, GLASS_R), (L - 1.8 * FIT, GLASS_R)], o + d * (0.9 * FIT), d, TUBE_SEG,
                 u_scale=1.0, v_scale=1.0 / L)


def tube_cards(o, d, L, half_width, angles, u_span):
    """Flat cards through the axis (both faces drawn by the shader): u across (0..u_span), v along 0..1.
    0 deg lies flat (across the gun, facing up), so it faces a player looking down at the wrist."""
    a0, a1 = o + d * (1.1 * FIT), o + d * (L - 1.1 * FIT)
    ex = np.array([1.0, 0, 0])
    ey = np.cross(d, ex)
    V, T, UV = [], [], []
    for ang in angles:
        a = math.radians(ang)
        w = (math.cos(a) * ex + math.sin(a) * ey) * half_width
        base = len(V)
        for (u, v, pt) in ((0, 0, a0 - w), (u_span, 0, a0 + w), (u_span, 1, a1 + w), (0, 1, a1 - w)):
            V.append(np.array(pt, float))
            UV.append((u, v))
        T += [(base, base + 1, base + 2), (base, base + 2, base + 3)]
    V, T, UV = np.array(V), np.array(T, int), np.array(UV, float)
    n = tri_normals(V, T)
    N = np.zeros_like(V)
    for k in range(3):
        np.add.at(N, T[:, k], n)
    N /= np.linalg.norm(N, axis=1, keepdims=True)
    return V, N, T, UV


def sized(s):
    e = s.encode()
    return struct.pack('<I', len(e)) + e


def effect_shader(tex, emissive, mult, flags1, flags2, falloff=(1.0, 1.0, 1.0, 1.0)):
    """BSEffectShaderProperty (BS 83/100 share this layout; decoded from Bethesda's testlightninggeo.nif):
    name, extra data, controller, flags 1/2, UV offset/scale, source texture, clamp/lighting influence/env LOD,
    falloff (start angle, stop angle, start opacity, stop opacity), emissive colour, emissive multiple, soft
    falloff depth, greyscale texture. Controller ref patched by the caller."""
    return (struct.pack('<iIi', -1, 0, -1) + struct.pack('<II', flags1, flags2) +
            struct.pack('<4f', 0.0, 0.0, 1.0, 1.0) + sized(tex) + bytes([3, 255, 0, 0]) +
            struct.pack('<4f', *falloff) + struct.pack('<4f', *emissive) + struct.pack('<2f', mult, 100.0) +
            sized(''))


EFFECT_CONTROLLER_OFFSET = 8   # name + extra-data count (0), then the controller ref


def add_float_controllers(nif, shader_i, tracks):
    """tracks = [(controlled variable, period, [(t, value), ...])]: one BSEffectShaderPropertyFloatController
    each (looping, Active + Compute Scaled Time like Bethesda's: flags 0x48), chained, linear keys. Variables:
    0 emissive multiple, 6 U offset, 8 V offset. Steps are written as two keys 0.001 s apart."""
    first = prev = -1
    made = []
    for var, period, keys in tracks:
        data = struct.pack('<II', len(keys), 1) + b''.join(struct.pack('<2f', t, v) for t, v in keys)
        d = nif.add_block('NiFloatData', data)
        it = nif.add_block('NiFloatInterpolator', struct.pack('<fi', -3.4028234663852886e+38, d))
        c = nif.add_block('BSEffectShaderPropertyFloatController',
                          struct.pack('<iHffffiiI', -1, 0x48, 1.0, 0.0, 0.0, period, shader_i, it, var))
        if prev < 0:
            first = c
        else:
            struct.pack_into('<i', nif.blocks[prev], 0, c)
        prev = c
        made += [d, it, c]
    struct.pack_into('<i', nif.blocks[shader_i], EFFECT_CONTROLLER_OFFSET, first)
    return made


def steps(period, values, dt):
    """Stepped keys: values held dt each, looping over period."""
    keys, t = [], 0.0
    for k, v in enumerate(values):
        if k:
            keys.append((t - 0.001, values[k - 1]))
        keys.append((t, v))
        t += dt
    keys.append((period, values[-1]))
    return keys


def alpha_property(flags, threshold):
    return struct.pack('<iIiHB', -1, 0, -1, flags, threshold)


def preview(prefix, layers):
    """Side views (lock side, plate side): painter's algorithm over (V, T, UV, texture) layers."""
    SC = 8
    for side, sign in (('lock', -1), ('plate', 1)):
        img = Image.new('RGB', (180 * SC, 40 * SC), (38, 40, 52))
        from PIL import ImageDraw
        dr = ImageDraw.Draw(img)
        items = []
        for V, T, UV, tex in layers:
            W, H = tex.size
            px = tex.load()
            depth = V[T].mean(1)[:, 0] * sign
            fn = tri_normals(V, T)
            for i in range(len(T)):
                u = UV[T[i]].mean(0)
                col = px[int(u[0] % 1 * (W - 1)), int(u[1] % 1 * (H - 1))]
                shade = 0.55 + 0.45 * max(0.0, fn[i, 0] * sign * 0.7 + fn[i, 1] * 0.3)
                col = tuple(int(c * shade) for c in col[:3])
                items.append((depth[i], [((V[j, 2] + 84) * SC, (36 - V[j, 1]) * SC) for j in T[i]], col))
        items.sort(key=lambda it: it[0])
        for _, pts, col in items:
            dr.polygon(pts, fill=col)
        img.save('%s_%s.png' % (prefix, side))


# ---- main ------------------------------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mods', default=os.path.join(MO2, 'mods'))
    ap.add_argument('--target', default='Zenderal - Patch Collection')
    ap.add_argument('--preview', default=None)
    ap.add_argument('--out-root', default=None, help='write here instead of <mods>/<target> (dry run)')
    args = ap.parse_args()
    mods = profile_mods()
    out_root = args.out_root or os.path.join(args.mods, args.target)
    assert os.path.isdir(out_root), out_root

    src, raw = winner(args.mods, mods, RIFLE_MESH, MESH_BSAS)
    print('rifle mesh from', src)
    nif = ns.Nif(raw)
    assert nif.tobytes() == raw, 'nifsplice round trip'
    shapes = nif.find('NiTriShape')
    assert len(shapes) == 1, shapes
    sh = shapes[0]
    fo = ns.trishape_fields(nif.blocks[sh])
    data_i = struct.unpack_from('<i', nif.blocks[sh], fo['data'])[0]
    shader_i = struct.unpack_from('<i', nif.blocks[sh], fo['shader'])[0]
    texset_i = struct.unpack_from('<i', nif.blocks[shader_i], ns.shader_texset_offset(nif.blocks[shader_i]))[0]
    assert nif.btype(data_i) == 'NiTriShapeData' and nif.btype(texset_i) == 'BSShaderTextureSet'
    root = nif.roots[0]
    _, kids = ns.node_children(nif.blocks[root])
    assert sh in kids, 'rifle shape is not a child of the root'
    rd = ns.read_trishape_data(nif.blocks[data_i])
    RV, RT, RUV = np.array(rd['verts']), np.array(rd['tris']), np.array(rd['uvs'])
    drop = guard_triangles(RV, RT)
    keep = np.setdiff1d(np.arange(len(RT)), drop)
    print('trigger guard: %d of %d rifle triangles dropped' % (len(drop), len(RT)))
    RT = RT[keep]
    oval = piece_in_box(RV, RT, OVAL_BOX, OVAL_TRIS, 'lock-side oval escutcheon')
    print('oval escutcheon under the cogs: %d rifle triangles dropped' % len(oval))
    RT = RT[np.setdiff1d(np.arange(len(RT)), oval)]
    tubes = barrel_triangles(RV, RT)
    btris, bax = tubes[0]
    bP = RV[np.unique(RT[btris])]
    bd = np.hypot(bP[:, 0] - bax[0], bP[:, 1] - bax[1])
    bzface = float(bP[:, 2].max())
    bore = BARREL_K * float(bd[np.abs(bP[:, 2] - bzface) < 0.02].min())
    print('barrel axis (%.2f, %.2f), muzzle face z %.2f, bore radius %.2f; %d hexagonal tube(s)'
          % (bax[0], bax[1], bzface, bore, len(tubes)))
    BV, BN, BT, BUV = [], [], [], []
    for tris_, ax_ in tubes:
        v_, n_, t_, uv_ = round_barrel(RV, RT, RUV, tris_, ax_)
        BT.append(t_ + sum(len(x) for x in BV))
        BV.append(v_)
        BN.append(n_)
        BUV.append(uv_)
    BV, BN, BT, BUV = np.concatenate(BV), np.concatenate(BN), np.concatenate(BT), np.concatenate(BUV)
    RT_SURF = RT          # the cogs sit on the rifle as it was (old barrel included)
    RT = RT[np.setdiff1d(np.arange(len(RT)), np.concatenate([t for t, _ in tubes]))]
    nif.blocks[data_i] = bytearray(ns.replace_triangles(nif.blocks[data_i], RT.tolist()))
    conv = tangent_convention(rd)
    print('tangent convention (tangents, bitangents):', conv)

    # ---- textures
    tex = {}
    for k in ('basecolor', 'metallic', 'height'):
        s, b = winner(args.mods, mods, RIFLE_TEX % k, TEX_BSAS)
        print('rifle', k, 'from', s)
        tex[k] = load_dds(b)
    base = np.asarray(tex['basecolor'].convert('RGB'), np.float32) / 255.0
    size = base.shape[1], base.shape[0]
    metal = np.asarray(tex['metallic'].convert('L').resize(size, Image.BILINEAR), np.float32) / 255.0
    height = np.asarray(tex['height'].convert('L').resize(size, Image.BILINEAR), np.float32) / 255.0
    s, b = winner(args.mods, mods, RIFLE_TEX % 'normal', TEX_BSAS)
    print('rifle normal from', s)
    rnorm = _rise.load_image(b)
    assert rnorm.shape[:2] == base.shape[:2], (rnorm.shape, base.shape)
    rgb, rnorm, cm = polished_gold(base, metal, rnorm, 'rifle')
    write_bc7(rgb, os.path.join(out_root, OUT_D))
    _rise.write_texture(rnorm, os.path.join(out_root, *OUT_N.split('/')), 'BC7_UNORM')
    write_complex_mask(cm, os.path.join(out_root, *OUT_M.split('/')))
    s, b = winner(args.mods, mods, COG_TEX, TEX_BSAS)
    print('cog texture from', s)
    cogtex = np.asarray(load_dds(b).convert('RGB'), np.float32) / 255.0
    s, b = winner(args.mods, mods, COG_NORMAL.replace('\\', '/'), TEX_BSAS)
    print('cog normal from', s)
    cognorm = _rise.load_image(b)
    cogtex = np.asarray(Image.fromarray((cogtex * 255).astype(np.uint8)).resize(cognorm.shape[1::-1], Image.BILINEAR),
                        np.float32) / 255.0
    cog_rgb, cognorm, cog_cm = polished_gold(cogtex, np.ones(cogtex.shape[:2], np.float32), cognorm, 'cog')
    write_bc7(cog_rgb, os.path.join(out_root, OUT_COG))
    _rise.write_texture(cognorm, os.path.join(out_root, *OUT_COG_N.split('/')), 'BC7_UNORM')
    write_complex_mask(cog_cm, os.path.join(out_root, *OUT_COG_M.split('/')))
    src_e, raw_e = winner(args.mods, [], _rise.CHROME_CUBEMAP, _rise.CHROME_BSAS)   # Bethesda's, never a replacer's
    print('chrome cubemap from', src_e)
    _rise.gold_cubemap(raw_e, os.path.join(out_root, *OUT_E.split('/')))

    # ---- cogs
    s, b = winner(args.mods, mods, COG_MESH, MESH_BSAS)
    print('cog mesh from', s)
    tmp = tempfile.NamedTemporaryFile(suffix='.nif', delete=False)
    tmp.write(b)
    tmp.close()
    cn = NifFile(tmp.name)
    assert len(cn.shapes) == 1
    cs = cn.shapes[0]
    CV = np.array(cs.verts, float)
    CN = np.array(cs.normals, float)
    CT = np.array(cs.tris, int)
    CUV = np.array(cs.uvs, float)
    ctx = cs.transform
    assert abs(ctx.scale - 1) < 1e-6 and np.allclose(np.array(ctx.translation), 0), 'cog shape transform'
    del cn
    os.remove(tmp.name)
    CV -= CV.mean(0) * np.array([1, 1, 0])
    CV[:, 2] -= (CV[:, 2].max() + CV[:, 2].min()) / 2

    samples = {s_: surface_samples(RV, RT_SURF, s_) for s_ in (-1, 1)}
    AV, AN, AT, AUV = [], [], [], []
    teeth, tooth0, hole = cog_profile(CV)
    print('cog: %d teeth, first tooth at %.1f deg, hole %.2f of the tip radius' % (teeth, tooth0, hole))
    assert 4 <= teeth <= 40 and 0.2 < hole < 0.6, (teeth, hole)
    for side, z, y, r, turn in cog_train(teeth):
        P, PN, tris, (lo, hi) = place_cog((CV, CN, CT), samples[side], side, z, y, r, turn)
        print('cog side %+d at z %.1f y %.1f r %.1f: surface %.2f..%.2f' % (side, z, y, r, lo, hi))
        AT.append(tris + sum(len(v) for v in AV))
        AV.append(P)
        AN.append(PN)
        AUV.append(CUV)
    tops = top_samples(RV, RT_SURF)
    t_o, t_d, t_L, t_clear = tube_axis(tops, bax[1])

    # ---- the channel for the tube, cut into the rifle's own mesh
    planes, c_yf, c_zr, c_z1 = channel_box(t_o, t_L)
    comp = components(RV, RT)
    ids, counts = np.unique(comp, return_counts=True)
    cut_ids = {int(ids[np.argmax(counts)])}            # the stock: the largest welded piece
    for c in ids:
        pv = RV[np.unique(RT[comp == c])]
        if (np.abs(pv[:, 0]).max() <= COLLAR_R and pv[:, 2].max() > c_zr - CHANNEL_RAMP_REACH
                and pv[:, 2].min() < c_z1 and pv[:, 1].max() > c_yf):
            cut_ids.add(int(c))                        # e.g. the tang: wholly under the tube
    RN, RTg, RBt = np.array(rd['normals']), np.array(rd['tangents']), np.array(rd['bitangents'])
    RC = np.array(rd['colors'])
    nv_before = len(RV)
    wood = wood_uv_map(RV, RT, RUV, metal, np.isin(comp, list(cut_ids)), c_zr - 4.0, c_z1)  # the wrist as it was
    gold_uv = lambda p: (0.5 + 0.12 * p[0], 0.5 + 0.12 * p[1])          # vertical faces: across, up
    gold_floor_uv = lambda p: (0.5 + 0.12 * p[0], 0.5 + 0.12 * p[2])

    def add_faces(groups, names):
        """Append closing faces to the rifle shape (tangents from UVs as the cogs, white vertex colours)."""
        nonlocal RV, RN, RTg, RBt, RUV, RC, RT, flags
        for g in names:
            if g not in groups:
                continue
            WV, WN, WT, WUV = groups[g]
            du_, dv_ = uv_derivatives(WV, WUV, WT)
            wder = {'du': ortho(du_, WN), 'dv': ortho(dv_, WN)}
            RT = np.concatenate([RT, WT + len(RV)])
            flags = np.concatenate([flags, np.ones(len(WT), bool)])
            RV = np.concatenate([RV, WV])
            RN = np.concatenate([RN, WN])
            RTg = np.concatenate([RTg, wder[conv[0]] * conv[1]])
            RBt = np.concatenate([RBt, wder[conv[2]] * conv[3]])
            RUV = np.concatenate([RUV, WUV])
            RC = np.concatenate([RC, np.ones((len(WV), 4))])

    report = []
    flags = np.isin(comp, list(cut_ids))
    # (a second, deeper cut round the rear cap, `pocket_box`, was built and replaced the same day by a longer tube
    # whose rear cap clears the wood: curator, "instead of cutting away just extend the tube length")
    for planes_, fills, drops, floor_y, label in ((planes, ('floor', 'ramp'), ('front',), c_yf, 'channel'),):
        A = np.c_[RN, RTg, RBt, RUV, RC]
        RV, A, RT, flags, segs, n_meet, n_drop = cut_channel(RV, A, RT, flags, planes_)
        RN, RTg, RBt, RUV, RC = A[:, 0:3], A[:, 3:6], A[:, 6:9], A[:, 9:11], A[:, 11:15]
        for arr in (RN, RTg, RBt):
            arr /= np.maximum(np.linalg.norm(arr, axis=1, keepdims=True), 1e-9)
        # metal (the gold shape): the front face round the front collar against the breech ("should be metal not
        # wood") and the floor beside the tube (a gold plate the small cogs lie on); wood: the ramp behind
        GOLD_FACES = ('front',)
        uvmaps = {g: (gold_uv if g in GOLD_FACES else wood) for g in tuple(fills) + tuple(drops)}
        uvmaps['floor'] = wood
        groups = close_cut(segs, planes_, fills, drops, floor_y, uvmaps)
        add_faces(groups, [g for g in groups if g not in GOLD_FACES and g != 'floor'])   # floor: the panel instead
        for g in GOLD_FACES:
            if g in groups:
                FV, FN, FT, FUV = groups[g]
                AT.append(FT + sum(len(v) for v in AV))
                AV.append(FV)
                AN.append(FN)
                AUV.append(FUV)
        floor_segs = segs['floor']
        floor_group = groups['floor']
        report.append('%s: %d triangles met it, %d inside pieces dropped, closing faces %s'
                      % (label, n_meet, n_drop, {g: len(v[2]) for g, v in groups.items()}))
    # behind the plate (z < z_slot) the first cut's floor stays wood: its closing faces, cut off at z_slot
    z_slot = t_o[2] + 0.5 * t_L
    FV, FN, FT, FUV = floor_group
    FV, FA, FT, _f, _s, _m, _d = cut_channel(FV, np.c_[FN, FUV], FT, np.ones(len(FT), bool),
                                             [(np.array([0, 0, 1.0]), z_slot, 'plate')])
    add_faces({'floor': (FV, FA[:, 0:3], FT, FA[:, 3:5])}, ['floor'])
    flags = np.ones(len(RT), bool) & flags
    # the groove the tube's rear half lies in (from the strap back): a prism round the tube, wood kept round it
    g_planes, g_faces, g_r, g_zb = groove_box(t_o, z_slot)
    A = np.c_[RN, RTg, RBt, RUV, RC]
    RV, A, RT, flags, gsegs, g_meet, g_drop = cut_channel(RV, A, RT, flags, g_planes)
    RN, RTg, RBt, RUV, RC = A[:, 0:3], A[:, 3:6], A[:, 6:9], A[:, 9:11], A[:, 11:15]
    for arr in (RN, RTg, RBt):
        arr /= np.maximum(np.linalg.norm(arr, axis=1, keepdims=True), 1e-9)

    def in_wood(p_):
        """Below the wood's top: the original wrist top, and the first cut's floor where it reaches."""
        m_ = (np.abs(tops[:, 2] - p_[2]) < 0.3) & (np.abs(tops[:, 0] - p_[0]) < 0.3)
        if not m_.any():
            return False
        top_ = float(tops[m_, 1].max())
        if c_zr <= p_[2] <= c_z1:
            top_ = min(top_, c_yf)
        return p_[1] < top_
    assert not gsegs['gback'], 'the groove has wood at its back end'
    GV, GN, GT, GUV = groove_faces(gsegs, g_faces, t_o, g_r, g_zb, z_slot, in_wood, c_yf, wood)
    add_faces({'groove': (GV, GN, GT, GUV)}, ['groove'])
    report.append('groove: %d sides, r %.2f, z %.2f..%.2f; %d triangles met it, %d inside pieces dropped, %d closing '
                  'triangles' % (GROOVE_SIDES, g_r, g_zb, z_slot, g_meet, g_drop, len(GT)))
    # the plate: a panel like the lock plate (bevelled edge, rivets), gold as before
    PV_, PN__, PT_, PUV_ = plate_panel(floor_segs, c_yf, z_slot, c_z1, gold_floor_uv)
    AT.append(PT_ + sum(len(v) for v in AV))
    AV.append(PV_)
    AN.append(PN__)
    AUV.append(PUV_)
    assert len(RV) < 65535
    nif.blocks[data_i] = bytearray(ns.trishape_data(RV.tolist(), RN.tolist(), RTg.tolist(), RBt.tolist(),
                                                     RUV.tolist(), RT.tolist(), list(rd['center']), rd['radius'],
                                                     RC.tolist()))
    print('channel: floor y %.2f from z %.2f (ramp %.2f per unit behind) to %.2f; pieces %s cut; %d -> %d vertices'
          % (c_yf, c_zr, CHANNEL_RAMP, c_z1, sorted(cut_ids), nv_before, len(RV)))
    for r_ in report:
        print('  ' + r_)
    fittings = tube_fittings(t_o, t_d, t_L, tops)
    for P, PN, tris, uv in fittings:
        AT.append(tris + sum(len(v) for v in AV))
        AV.append(P)
        AN.append(PN)
        AUV.append(uv)
    print('lightning tube on the wrist top: axis y %.2f at z %.1f -> y %.2f at z %.1f (%.1f deg), length %.2f, axis '
          '%.2f..%.2f over the wood; %d gold fitting parts, %d triangles'
          % (t_o[1], t_o[2], t_o[1] + t_d[1] * t_L, t_o[2] + t_d[2] * t_L, math.degrees(math.asin(t_d[1])), t_L,
             t_clear.min(), t_clear.max(), len(fittings), sum(len(f[2]) for f in fittings)))
    for P, PN, tris in (guard_cog((CV, CN, CT), hole, tooth0),
                        muzzle_cog((CV, CN, CT), tooth0, bax, bore, bzface),
                        tube_end_cog((CV, CN, CT), tooth0, t_o)):
        AT.append(tris + sum(len(v) for v in AV))
        AV.append(P)
        AN.append(PN)
        AUV.append(CUV)
    y_panel = c_yf + PANEL_H
    side_tubes = side_tube_layout(floor_segs, z_slot + 0.3, TUBE_Z[1] - 1.3 * FIT - 0.15)
    side_parts = side_tube_parts((CV, CN, CT), tooth0, side_tubes, y_panel)
    rivet_parts, rivet_circles = plate_rivets(floor_segs, y_panel, z_slot, c_z1, side_tubes)
    wire_parts, wire_paths = plate_wires(floor_segs, y_panel, TUBE_Z[1] - 0.9 * FIT, z_slot + 0.6, side_tubes)
    edge_parts = groove_edge_tubes(gsegs, g_zb, z_slot, t_o, side_tubes, y_panel + SIDE_TUBE_COG_R + 0.01)
    for P, PN, tris, uv in rivet_parts + wire_parts + side_parts + edge_parts:
        AT.append(tris + sum(len(v) for v in AV))
        AV.append(P)
        AN.append(PN)
        AUV.append(CUV if uv is None else uv)
    # the plate cogs keep off the side tubes' end cogs and collars; under the pipe itself they fit (the pipe's
    # underside is SIDE_TUBE_COG_R - SIDE_TUBE_R over the panel, more than a cog is thick), so the strip outside
    # the side tube takes large, medium and small cogs (curator, "various different sized Cogs in this space")
    assert SIDE_TUBE_COG_R - SIDE_TUBE_R > PLATE_COG_THICK + 0.02
    for ts, tx, tr, tf in side_tubes:
        for zz_ in (tr - 0.5 * SIDE_TUBE_COG_T, tr + 0.5 * SIDE_TUBE_COLLAR_LEN,
                    tf - 0.5 * SIDE_TUBE_COLLAR_LEN, tf + 0.5 * SIDE_TUBE_COG_T):
            rivet_circles.append((tx, float(zz_), SIDE_TUBE_COG_R))
    V = np.concatenate(AV)
    N = np.concatenate(AN)
    T = np.concatenate(AT)
    UV = np.concatenate(AUV)
    assert len(V) < 65535
    collar_zs = [(t_o[2], t_o[2] + 1.3 * FIT), (TUBE_Z[1] - 1.3 * FIT, TUBE_Z[1])]
    plate = plate_cogs((CV, CN, CT), floor_segs, y_panel, c_z1, z_slot, collar_zs, wire_paths, rivet_circles)
    PV = np.concatenate([p_[0] for p_ in plate])
    PN_ = np.concatenate([p_[1] for p_ in plate])
    PT = np.concatenate([p_[2] + k_ * len(CV) for k_, p_ in enumerate(plate)])
    PUV = np.concatenate([CUV] * len(plate))
    assert len(PV) < 65535, ('plate cogs past one shape', len(PV))
    du, dv = uv_derivatives(V, UV, T)
    der = {'du': ortho(du, N), 'dv': ortho(dv, N)}
    tan = der[conv[0]] * conv[1]
    bit = der[conv[2]] * conv[3]
    center = (V.min(0) + V.max(0)) / 2
    radius = float(np.linalg.norm(V - center, axis=1).max())

    # ---- mesh
    rifle_set = ns.read_texture_set(nif.blocks[texset_i])
    print('rifle texture set was', rifle_set)
    nif.blocks[texset_i] = bytearray(ns.texture_set(
        [OUT_D.replace('/', '\\'), OUT_N.replace('/', '\\')] + rifle_set[2:4] +
        [OUT_E.replace('/', '\\'), OUT_M.replace('/', '\\')] + rifle_set[6:]))
    nif.blocks[shader_i] = make_envmapped(nif.blocks[shader_i])   # before the cog/barrel copies are taken
    old = ns.read_texture_set(nif.blocks[texset_i])
    assert old[0].endswith('ClockworkThunder_d.dds') and old[5].endswith('ClockworkThunder_m.dds'), old
    cog_texset = nif.add_block('BSShaderTextureSet', ns.texture_set(
        [OUT_COG.replace('/', '\\'), OUT_COG_N.replace('/', '\\'), '', '', OUT_E.replace('/', '\\'),
         OUT_COG_M.replace('/', '\\')] + [''] * (len(rifle_set) - 6)))
    shader = bytearray(nif.blocks[shader_i])
    struct.pack_into('<i', shader, ns.shader_texset_offset(shader), cog_texset)
    cog_shader = nif.add_block('BSLightingShaderProperty', shader)
    cog_data = nif.add_block('NiTriShapeData', ns.trishape_data(
        V.tolist(), N.tolist(), tan.tolist(), bit.tolist(), UV.tolist(), T.tolist(), center.tolist(), radius))
    shape = bytearray(nif.blocks[sh])
    struct.pack_into('<I', shape, fo['name'], nif.add_string(COG_SHAPE_NAME))
    struct.pack_into('<i', shape, fo['data'], cog_data)
    struct.pack_into('<i', shape, fo['shader'], cog_shader)
    cog_shape = nif.add_block('NiTriShape', shape)
    # the round barrel: a copy of the rifle's shape with its own data, and its OWN copies of the rifle's shader
    # property and texture set (same textures). Sharing the rifle's shader block froze the game on equip
    # (curator 2026-11-13); the cog shape, which never shared one, equipped fine.
    du, dv = uv_derivatives(BV, BUV, BT)
    bder = {'du': ortho(du, BN), 'dv': ortho(dv, BN)}
    bcenter = (BV.min(0) + BV.max(0)) / 2
    barrel_data = nif.add_block('NiTriShapeData', ns.trishape_data(
        BV.tolist(), BN.tolist(), (bder[conv[0]] * conv[1]).tolist(), (bder[conv[2]] * conv[3]).tolist(),
        BUV.tolist(), BT.tolist(), bcenter.tolist(), float(np.linalg.norm(BV - bcenter, axis=1).max())))
    bshape = bytearray(nif.blocks[sh])
    struct.pack_into('<I', bshape, fo['name'], nif.add_string(BARREL_SHAPE_NAME))
    struct.pack_into('<i', bshape, fo['data'], barrel_data)
    barrel_texset = nif.add_block('BSShaderTextureSet', bytes(nif.blocks[texset_i]))
    bshader = bytearray(nif.blocks[shader_i])
    struct.pack_into('<i', bshader, ns.shader_texset_offset(bshader), barrel_texset)
    struct.pack_into('<i', bshape, fo['shader'], nif.add_block('BSLightingShaderProperty', bshader))
    barrel_shape = nif.add_block('NiTriShape', bshape)

    # ---- the lightning tube: glass, then the bolts inside (each shape its own shader block)
    blocks_before_tube = len(nif.blocks)
    def new_shape(name, V_, N_, T_, UV_, shader_block, alpha_block):
        du_, dv_ = uv_derivatives(V_, UV_, T_)
        d_ = {'du': ortho(du_, N_), 'dv': ortho(dv_, N_)}
        c_ = (V_.min(0) + V_.max(0)) / 2
        data_ = nif.add_block('NiTriShapeData', ns.trishape_data(
            V_.tolist(), N_.tolist(), (d_[conv[0]] * conv[1]).tolist(), (d_[conv[2]] * conv[3]).tolist(),
            UV_.tolist(), T_.tolist(), c_.tolist(), float(np.linalg.norm(V_ - c_, axis=1).max())))
        s_ = bytearray(nif.blocks[sh])
        struct.pack_into('<I', s_, fo['name'], nif.add_string(name))
        struct.pack_into('<i', s_, fo['data'], data_)
        struct.pack_into('<i', s_, fo['shader'], shader_block)
        struct.pack_into('<i', s_, fo['alpha'], alpha_block)
        return nif.add_block('NiTriShape', s_)

    gD = np.zeros((64, 64, 4), np.float32) + np.array(GLASS_TINT, np.float32)
    _rise.write_texture(gD, os.path.join(out_root, *OUT_GLASS_D.split('/')), 'BC7_UNORM')
    gN = np.zeros((64, 64, 4), np.float32) + np.array([0.5, 0.5, 1.0, 1.0], np.float32)
    _rise.write_texture(gN, os.path.join(out_root, *OUT_GLASS_N.split('/')), 'BC7_UNORM')
    gM = np.zeros((64, 64, 4), np.float32) + np.array([0.75, 0.75, 0.75, 1.0], np.float32)  # alpha 1: no CM
    _rise.write_texture(gM, os.path.join(out_root, *OUT_GLASS_M.split('/')), 'BC7_UNORM')
    glass_texset = nif.add_block('BSShaderTextureSet', ns.texture_set(
        [OUT_GLASS_D.replace('/', '\\'), OUT_GLASS_N.replace('/', '\\'), '', '', GLASS_ENV,
         OUT_GLASS_M.replace('/', '\\')] + [''] * (len(rifle_set) - 6)))
    gshader = bytearray(nif.blocks[shader_i])          # the rifle's, already Environment Map
    t_ = ns.shader_texset_offset(gshader)
    struct.pack_into('<i', gshader, t_, glass_texset)
    f1_ = 16 + 4 * struct.unpack_from('<I', gshader, 8)[0]
    struct.pack_into('<I', gshader, f1_ + 4, struct.unpack_from('<I', gshader, f1_ + 4)[0] & ~1)  # no Z write
    # after the texture-set ref: emissive colour 12, mult 4, clamp 4, alpha 4, refraction 4, glossiness, specular
    struct.pack_into('<f', gshader, t_ + 32, 300.0)                     # glossiness
    struct.pack_into('<3f', gshader, t_ + 36, 1.0, 1.0, 1.0)            # specular colour
    struct.pack_into('<f', gshader, t_ + 48, 3.0)                       # specular strength
    GV, GN, GT, GUV = tube_glass(t_o, t_d, t_L)
    glass_shape = new_shape(GLASS_SHAPE, GV, GN, GT, GUV, nif.add_block('BSLightingShaderProperty', gshader),
                            nif.add_block('NiAlphaProperty', alpha_property(ALPHA_BLEND, 0)))
    # effect shaders: SLSF1 ZBuffer test + falloff, SLSF2 double sided; no palette, no vertex colours
    bolt_shader = nif.add_block('BSEffectShaderProperty', effect_shader(BOLT_TEX, BOLT_EMISSIVE, 3.0,
                                                                        0x80000040, 0x10, (1.0, 0.3, 1.0, 0.0)))
    bolt_ctl = add_float_controllers(nif, bolt_shader, [
        (6, 1.32, steps(1.32, [0.0, 0.5, 0.0, 0.5, 0.25, 0.5, 0.0, 0.75, 0.5, 0.0, 0.5], 0.12)),   # which bolt
        (8, 0.91, steps(0.91, [0.0, 0.37, 0.71, 0.18, 0.55, 0.86, 0.29], 0.13)),                # where along
        (0, 1.10, [(0.0, 4.0), (0.07, 8.0), (0.15, 2.5), (0.24, 6.5), (0.33, 1.5), (0.41, 7.5), (0.52, 3.0),
                   (0.61, 9.0), (0.70, 2.0), (0.82, 6.0), (0.93, 3.5), (1.10, 4.0)]),          # flicker
    ])
    BV_, BN_, BT_, BUV_ = tube_cards(t_o, t_d, t_L, GLASS_R * 0.85, (0.0, 60.0, -60.0), 0.5)
    bolt_shape = new_shape(BOLT_SHAPE, BV_, BN_, BT_, BUV_, bolt_shader,
                           nif.add_block('NiAlphaProperty', alpha_property(ALPHA_ADDITIVE, 128)))
    glow_shader = nif.add_block('BSEffectShaderProperty', effect_shader(GLOW_TEX, BOLT_EMISSIVE, 0.8,
                                                                        0x80000040, 0x10, (1.0, 0.3, 1.0, 0.0)))
    glow_ctl = add_float_controllers(nif, glow_shader, [
        (8, 0.6, [(0.0, 0.0), (0.6, 1.0)]),                                                   # crawls along
        (0, 0.85, [(0.0, 0.8), (0.2, 1.4), (0.45, 0.5), (0.65, 1.2), (0.85, 0.8)]),
    ])
    WV_, WN_, WT_, WUV_ = tube_cards(t_o, t_d, t_L, GLASS_R * 0.45, (0.0, 90.0), 1.0)
    glow_shape = new_shape(GLOW_SHAPE, WV_, WN_, WT_, WUV_, glow_shader,
                           nif.add_block('NiAlphaProperty', alpha_property(ALPHA_ADDITIVE, 128)))
    # the cogs packed over the plate: their own shape, shader property and texture set (copies of the cogs')
    plate_texset = nif.add_block('BSShaderTextureSet', bytes(nif.blocks[cog_texset]))
    pshader = bytearray(nif.blocks[cog_shader])
    struct.pack_into('<i', pshader, ns.shader_texset_offset(pshader), plate_texset)
    plate_shape = new_shape(PLATE_COG_SHAPE, PV, PN_, PT, PUV, nif.add_block('BSLightingShaderProperty', pshader), -1)

    # ---- the ring scope (scope.py): gold rings + mounts, lens glass, glowing reticle; each its own shader block
    fd_, tmpn = tempfile.mkstemp(suffix='.nif')
    os.close(fd_)
    with open(tmpn, 'wb') as fh_:
        fh_.write(raw)
    rx = NifFile(tmpn).shapes[0].transform
    R_sh = np.array(rx.rotation.matrix if hasattr(rx.rotation, 'matrix') else rx.rotation, float).reshape(3, 3)
    t_sh, s_sh = np.array(rx.translation, float), float(rx.scale)
    os.remove(tmpn)
    sb_dir = tempfile.mkdtemp()
    sb_parts = scope.read_parts(NifFile, scope.scoped_bows_nif(os.path.join(MO2, 'downloads'), sb_dir))
    shutil.rmtree(sb_dir, ignore_errors=True)
    eye_, ray_, cam_ = scope.crosshair_ray(
        os.path.join(ROOT, 'src', 'FlintlockOverhaul', 'tools', '06-build-musket-aim-fix.py'),
        os.path.join(args.mods, 'Zenderal - Patch Collection'), DATA)
    top_pts = np.concatenate([BV, RV[np.unique(RT)]])

    def barrel_top(x_, z_):
        m_ = (np.abs(top_pts[:, 0] - x_) < 0.6) & (np.abs(top_pts[:, 2] - z_) < 0.5)
        assert m_.any(), ('nothing under the scope mount', x_, z_)
        return float(top_pts[m_, 1].max())
    (SGV, SGN, SGT, SGUV), (SLV, SLN, SLT, SLUV), (SRV, SRN, SRT, SRUV) = scope.build(
        sb_parts, eye_, ray_, cam_, R_sh, t_sh, s_sh, barrel_top)
    k_rgb, k_metal, k_norm = scope.key_band_texture()
    k_rgb, k_norm, k_cm = polished_gold(k_rgb, k_metal, k_norm, 'scope')
    write_bc7(k_rgb, os.path.join(out_root, OUT_SCOPE_D))
    _rise.write_texture(k_norm, os.path.join(out_root, *OUT_SCOPE_N.split('/')), 'BC7_UNORM')
    write_complex_mask(k_cm, os.path.join(out_root, *OUT_SCOPE_M.split('/')))
    scope_texset = nif.add_block('BSShaderTextureSet', ns.texture_set(
        [OUT_SCOPE_D.replace('/', '\\'), OUT_SCOPE_N.replace('/', '\\'), '', '', OUT_E.replace('/', '\\'),
         OUT_SCOPE_M.replace('/', '\\')] + [''] * (len(rifle_set) - 6)))
    sshader = bytearray(nif.blocks[cog_shader])
    struct.pack_into('<i', sshader, ns.shader_texset_offset(sshader), scope_texset)
    scope_shape = new_shape(SCOPE_SHAPE, SGV, SGN, SGT, SGUV, nif.add_block('BSLightingShaderProperty', sshader), -1)
    lens_texset = nif.add_block('BSShaderTextureSet', bytes(nif.blocks[glass_texset]))
    lshader = bytearray(gshader)
    struct.pack_into('<i', lshader, ns.shader_texset_offset(lshader), lens_texset)
    lens_shape = new_shape(SCOPE_LENS_SHAPE, SLV, SLN, SLT, SLUV, nif.add_block('BSLightingShaderProperty', lshader),
                           nif.add_block('NiAlphaProperty', alpha_property(ALPHA_BLEND, 0)))
    wD = np.ones((64, 64, 4), np.float32)
    _rise.write_texture(wD, os.path.join(out_root, *OUT_RETICLE.split('/')), 'BC7_UNORM')
    ret_shader = nif.add_block('BSEffectShaderProperty', effect_shader(
        OUT_RETICLE.replace('/', '\\'), scope.RETICLE_EMISSIVE, 2.0, 0x80000040, 0x10, (1.0, 1.0, 1.0, 1.0)))
    reticle_shape = new_shape(SCOPE_RETICLE_SHAPE, SRV, SRN, SRT, SRUV, ret_shader,
                              nif.add_block('NiAlphaProperty', alpha_property(ALPHA_ADDITIVE, 128)))
    print('scope: gold %d tris, lens %d, reticle %d' % (len(SGT), len(SLT), len(SRT)))
    tube_blocks = len(nif.blocks) - blocks_before_tube
    print('lightning tube: glass %d tris, bolt cards %d, glow cards %d; %d controller blocks'
          % (len(GT), len(BT_), len(WT_), len(bolt_ctl) + len(glow_ctl)))

    at = kids.index(sh) + 1
    nif.blocks[root] = ns.set_children(nif.blocks[root], kids[:at] + [barrel_shape, cog_shape, plate_shape, glass_shape,
                                                                      glow_shape, bolt_shape, scope_shape, lens_shape,
                                                                      reticle_shape] + kids[at:])
    out = nif.tobytes()
    # read back: our parser, then PyNifly (an independent reader)
    back = ns.Nif(out)
    rb = ns.read_trishape_data(back.blocks[cog_data])
    assert len(rb['verts']) == len(V) and len(rb['tris']) == len(T)
    orig = ns.Nif(raw)
    assert len(back.blocks) == len(orig.blocks) + 8 + tube_blocks
    rbb = ns.read_trishape_data(back.blocks[barrel_data])
    assert len(rbb['verts']) == len(BV) and len(rbb['tris']) == len(BT)
    for k in range(len(orig.blocks)):
        if k not in (root, texset_i, data_i, shader_i):
            assert back.blocks[k] == orig.blocks[k], 'original block %d changed' % k
    mesh_path = os.path.join(out_root, OUT_MESH)
    os.makedirs(os.path.dirname(mesh_path), exist_ok=True)
    with open(mesh_path, 'wb') as fh:
        fh.write(out)
    chk = NifFile(mesh_path)
    names = sorted(s_.name for s_ in chk.shapes)
    assert COG_SHAPE_NAME in names and BARREL_SHAPE_NAME in names and GLASS_SHAPE in names and BOLT_SHAPE in names and GLOW_SHAPE in names and PLATE_COG_SHAPE in names and SCOPE_SHAPE in names and SCOPE_LENS_SHAPE in names and SCOPE_RETICLE_SHAPE in names and len(chk.shapes) == 10, names
    cog_chk = [s_ for s_ in chk.shapes if s_.name == COG_SHAPE_NAME][0]
    assert len(cog_chk.verts) == len(V) and np.allclose(np.array(cog_chk.verts), V, atol=1e-3)
    print('wrote', mesh_path, len(out), 'bytes;', len(V), 'cog verts,', len(T), 'tris')
    for p in (OUT_D, OUT_N, OUT_M, OUT_COG, OUT_COG_N, OUT_COG_M, OUT_E):
        print('wrote', os.path.join(out_root, p))

    if args.preview:
        preview(args.preview, [
            (RV, RT, RUV, Image.fromarray((rgb * 255).astype(np.uint8)).resize((1024, 1024))),
            (BV, BT, BUV, Image.fromarray((rgb * 255).astype(np.uint8)).resize((1024, 1024))),
            (V, T, UV, Image.fromarray((cog_rgb * 255).astype(np.uint8)).resize((512, 512))),
        ])
        Image.fromarray((rgb * 255).astype(np.uint8)).resize((1024, 1024)).save(args.preview + '_atlas.png')


if __name__ == '__main__':
    main()
