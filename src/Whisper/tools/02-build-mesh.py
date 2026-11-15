"""Whisper's own mesh (curator 2026-11-15): billyro's Stalwart Axe (SE base from tools/01) with
  - the curved neck, the collar block with its band and rivets, and the handle above the top band replaced by the
    Noble Armory war axe's upper shaft, socket, collar and spike (Caenraes, via Pretty Enderal Armory; noble.py),
    in the blade's steel with the gold painted out; billyro's blade moved so its back runs into the socket;
  - the handle below thinned to a plain elliptical shaft ending inside the snake's head, with Triumvirate's
    rattlesnake (Mihail) coiled up it, its open-mouthed head the pommel and an amethyst crystal (vanilla's black soul gem,
    recoloured) in its mouth (curator: "rework the handle itself, make it thinner with a metal snake coiling round
    it the pommel is formed from the snakes head, the Ruby is inside the snakes open mouth"; snake.py). The lower
    handle bands and billyro's knob are gone; the grip's leather is very dark purple;
  - an ouroboros (the same snake) in place of billyro's top band, and three wavy relief snakes on each blade face;
  - every snake in the blade's own steel (curator: "match the metal of the axe blade"); the coil and the ouroboros
    carry Argent Verdict's palm scale mail (curator: "add the same texture pattern you used on the Argent Verdict
    palm ... to the snake handle and ouroboros ring"), the blade snakes stay smooth.

Writes into Zenderal - Patch Collection (the axe's textures under Whisper's own paths: the Stalwart Axe itself is
not installed in the list, and billyro gave the curator permission to use it):
    meshes/Zenderal/Whisper/Whisper.nif
    textures/Zenderal/Whisper/axe.dds, axe_n.dds, axe_m.dds         (billyro's 2K set, copied)
    textures/Zenderal/Whisper/holder.dds, holder_n.dds, holder_m.dds (the hip holder's, copied)
    textures/Zenderal/Whisper/nissibeach_e.dds                       (the axe's cubemap, Humus via billyro, copied)
    textures/Zenderal/Whisper/metal_d.dds, metal_n.dds, metal_m.dds  (the blade's steel, uniform: the blade snakes)
    textures/Zenderal/Whisper/coil_d.dds, coil_n.dds, coil_m.dds     (the blade's steel + scale mail: the coil)
    textures/Zenderal/Whisper/ouroboros_d.dds, _n, _m                (the same, laid on the ouroboros)
    textures/Zenderal/Whisper/noble_d.dds, noble_n.dds, noble_m.dds  (the Noble mount on the blade's steel)
    textures/Zenderal/Whisper/grip_d.dds                             (billyro's diffuse, the grip's leather dark purple)
    textures/Zenderal/Whisper/amethyst_d.dds, _n, _m                 (vanilla's black soul gem, recoloured amethyst)

Shapes added, each on its own copy of the axe's environment-map shader (never shared: Clockwork Thunder's freeze):
ZP_WhisperNobleShaft, ZP_WhisperGrip (billyro's textures), ZP_WhisperSnake (the coil), ZP_WhisperOuroboros,
ZP_WhisperBladeSnakes, ZP_WhisperPommel (the amethyst: its own shape so it can glow when the axe is charged).

Usage:  python src/Whisper/tools/02-build-mesh.py [--out-root <dir>]   (default: the Patch Collection mod folder)
"""
import importlib.util, json, os, shutil, struct, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
TOOLS = json.load(open(os.path.join(REPO, '.claude', 'config', 'tools.json'), encoding='utf-8-sig'))
SR = os.path.join(REPO, 'src', 'StingAndRise', 'tools')
sys.path.insert(0, SR)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, 'src', 'Prophecy', 'tools'))
import nifse  # noqa: E402
import gamespine  # noqa: E402
import snake  # noqa: E402
import noble  # noqa: E402
import _bsa  # noqa: E402

_spec = importlib.util.spec_from_file_location('sr_assets', os.path.join(SR, '01-build-assets.py'))
sr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sr)

RAW = os.path.join(REPO, 'reference', 'mods', '_raw', 'StalwartAxe')
BASE = os.path.join(RAW, 'se', 'meshes', 'billyro', 'stalwartaxe', 'axe1h.nif')
PATCH_COLLECTION = os.path.join(TOOLS['modsDir'], 'Zenderal - Patch Collection')
DATA = TOOLS['gameDataDir']
MODS = TOOLS['modsDir']
MESH_OUT = 'meshes/Zenderal/Whisper/Whisper.nif'
TEX_DIR = 'textures/Zenderal/Whisper/'
AXE_SHAPE, HOLDER_SHAPE = '1stPersonSteelWarAxe:0', 'Scb'
GRIP_SHAPE, SNAKE_SHAPE, POMMEL_SHAPE = 'ZP_WhisperGrip', 'ZP_WhisperSnake', \
    'ZP_WhisperPommel'
NOBLE_SHAPE = 'ZP_WhisperNobleShaft'  # the Noble axe's upper shaft, socket and spike (noble.py)
NOBLE_GOLD = (0.18, 0.35)             # saturation over which a Noble texel counts as gold inlay (ramp)
NOBLE_FILL = 6.0                      # px: the blur that paints the inlay out with the steel round it
NOBLE_CONTRAST = 0.8                  # the Noble steel's own light and dark kept at this much of its depth
# billyro's files copied under Whisper's paths: (source in RAW, our name)
COPIES = {r'textures\billyro\stalwartaxe\axe.dds': ('main/textures/billyro/stalwartaxe/axe.dds', 'axe.dds'),
          r'textures\billyro\stalwartaxe\axe_n.dds': ('main/textures/billyro/stalwartaxe/axe_n.dds', 'axe_n.dds'),
          r'textures\billyro\stalwartaxe\axe_m.dds': ('main/textures/billyro/stalwartaxe/axe_m.dds', 'axe_m.dds'),
          r'textures\billyro\stalwartaxe\holder.dds': ('main/textures/billyro/stalwartaxe/holder.dds', 'holder.dds'),
          r'textures\billyro\stalwartaxe\holder_n.dds': ('main/textures/billyro/stalwartaxe/holder_n.dds',
                                                          'holder_n.dds'),
          r'textures\billyro\stalwartaxe\holder_m.dds': ('main/textures/billyro/stalwartaxe/holder_m.dds',
                                                          'holder_m.dds'),
          r'textures\cubemaps\nissibeach.dds': ('main/textures/cubemaps/nissibeach.dds', 'nissibeach_e.dds')}
TEXTURE_BSAS = ['Skyrim - Textures%d.bsa' % i for i in range(9)]
# the spine's and snake's metal (curator 2026-11-15: "make the texture of the snake and spine smooth shiny metal
# instead of grey bone and snake skin", "match the metal of the axe blade"; until then dark iron carrying the bone's
# and the snakeskin's patterns). One shared set, metal_d / _n / _m, uniform: the blade's own values, measured at build
# time from billyro's textures under the blade's UVs (medians: diffuse ~0.105 neutral grey, env mask ~0.21, specular
# ~0.39; the shine is the shader's cubemap, as on the blade, and the shapes use copies of the blade's shader), with a
# flat normal map (smooth: no bone grain, no scales). The spine keeps its vertex colours (vanilla's baked shading)
METAL_TEX = 256                       # uniform: the size only sets the mip chain
BLADE_X = -3.5                        # the crescent blade: axe triangles whose centre lies past this x
VERTEX_COLOURS = 0x20                 # SLSF2_Vertex_Colors
METAL = {0: 'metal_d.dds', 1: 'metal_n.dds', 5: 'metal_m.dds'}
# the grip's leather under the snake (curator 2026-11-15: "make the leather of the handle under the snake a dark
# burgundy"): its own copy of billyro's diffuse, grip_d, with the texels under the grip's UVs recoloured (Sunrise's
# recolor_leather: its own light and dark kept at LEATHER_CONTRAST of their depth); normal map and env mask stay
# billyro's (the leather stays matte)
# then (2026-11-15, after an in-game look): "lets change the leather handle color to a very dark purple", and on the
# render of that (#1C0928, as dark as Midnight Sting's very dark green grip): "darken the leather handle even more,
# almost black"
LEATHER = (0.050, 0.016, 0.072)       # #0D0412 at the leather's 75th-percentile brightness (luminance 0.032; the
                                      # burgundy was #4A0E18, 0.130)
LEATHER_CONTRAST = 0.75
# the grip: billyro's shaft (one island, the finger-swelled grip between the bands) below the top band, laid onto
# the thin ellipse snake.GRIP_A x snake.GRIP_B round the handle axis and run down INTO the snake's head, its end
# capped flat inside it (curator, on a render where the grip stopped at the head's back: "make sure there isn't a
# gap between the head and the handle"; the head is tilted with its open jaws, so its back stood off the grip's
# end on the top side). At GRIP_END the head's cross-section holds the whole ellipse (asserted in main)
GRIP_END = snake.OCCIPUT_Y - 1.8
GRIP_TOP = snake.RING_Y + 0.15        # the grip's top, capped flat just inside the Noble shaft's lower end (the
                                      # ouroboros ring sits on that joint)
# under the ring the grip flares out to the Noble shaft's grooves (x GRIP_FLARE_IN, just inside them), so no slot
# opens between the ring's belly and the thin grip (the ring now rests on the shaft's ridges, 0.36 wider than the
# grip in z), and plugs the shaft's open end
GRIP_FLARE = (snake.RING_Y - 0.5, snake.RING_Y)   # heights: the thin ellipse below, the grooves' circle at the top
GRIP_FLARE_IN = 0.98
GRIP_SUBDIVIDE = 3                    # billyro's shaft triangles split 3 x 3 before shaping: the mesh follows its
                                      # ellipse, and has vertices on the leather's flecks (tuck_grip)
TUCK_TOP = -3.5                       # below this, grip patches poking out of the coil's neck/head are tucked in
TUCK_GRID = (240, 0.03)               # the grip surface's test grid: cells round (1.5 deg), cell height
TUCK_NEAR = 2                         # grid cells round an island whose grip vertices are tucked too
TUCK_ISLAND_MAX = 600                 # grid cells: a bigger patch outside the snake is leather that shows, not a fleck
GRIP_SLICES = np.arange(-8.28, -7.55, 0.06)   # horizontal cuts through the grip where the head caps it: billyro's
                                      # rows there are tall, and the flecks (0.27 tall) fell between two of them
TUCK_DEPTH = 0.04                     # under the snake's surface
# the grip's end inside the head, narrowed on its -z side (curator, on the neck lifted onto the -z face: "almost just
# to fix this handle clipping": a slot of leather on the head's top right behind the jaws, where the head's skin lies
# 0.0 - 0.1 under the grip's -z face; the slot reached round to the open throat, so tuck_grip took it for visible
# leather). That half's z semi-axis falls by END_TUCK at GRIP_END, faded in from END_TUCK_TOP (all of it inside the
# head: the leather shows only on the throat's +z side there)
END_TUCK, END_TUCK_TOP = 0.3, -7.3
# the neck's belly settled onto the leather by measurement (settle_neck): the belly line the layout offsets by is a
# smoothed per-height minimum, which left the neck floating up to 0.12 over the grip's -z face and touching it in
# flecks. Over SETTLE (heights: from where the head has lifted onto the face to the end of the turn into the coil;
# faded in and out over its last value, arc length) the grip's surface point under the centre line is measured
# against the snake and the belly depth corrected until it lies NECK_SINK inside (the coil's turns sink ~0.09)
# (over the back of the head, y < -6.2, it would not converge: the head is thick, tilted and narrowing fast there,
# and moving the path does not move its belly predictably; tuck_grip covers the flecks there, on GRIP_SLICES)
NECK_SINK = 0.06
SETTLE = (-6.6, -3.3, 0.8)
SETTLE_BLUR = 0.2                     # the correction blurred over this much arc (a sharp one bent the neck: a crease)
SETTLE_BAND, SETTLE_ROUNDS = (0.02, 0.15), 6   # accepted: in contact all along, about as deep as the coil turns sink
# billyro's leather is near black at the grip's two ends (y < -7, y > 9: ~0.1 of the middle's brightness): they lay
# under his lower and top handle bands, whose baked shadow the burgundy kept (curator, circling the band above the
# pommel head: "this section needs to be the same handle leather"). A brightness gain capped at 4x reached only half
# and would raise the noise; instead the ends wear the leather next to them (mirror_grip_ends: UVs mirrored back
# across GRIP_MIRROR)
GRIP_MIRROR = (-6.9, 8.7)             # heights: the leather below / above these comes from just above / below them
GRIP_EVEN = (-6.0, 8.5)               # the grip's evenly lit middle (the check's reference)
RING_CLEAR = 0.02                     # the ouroboros' belly this far off the Noble shaft's ridges
RING_SHAPE, BLADE_SNAKES_SHAPE = 'ZP_WhisperOuroboros', 'ZP_WhisperBladeSnakes'
# the snakes' scales (curator, on the coil and the ouroboros: "add the same texture pattern you used on the Argent
# Verdict palm ... to the snake handle and ouroboros ring"; first asked for on the retired neck snake): Argent
# Verdict's scale mail (fist_tex 'mail') on the blade's metal, each snake in its own texture set (coil_*,
# ouroboros_*), since a set is laid in world units along that snake's own layout. The row pitch follows each snake's
# body width (SCALE_PITCH snake units x its sigma_body: the same number of scales round both, as on a real snake);
# the rise follows the pitch
SCALE_TEX = ((2048, 4096, 8192), 512)  # along (u: the narrowest giving SCALE_MIN_TEXELS a row), round (v)
SCALE_MIN_TEXELS = 8                  # texels per scale row and column at least (4.6 a row aliased)
SCALE_PITCH = 0.7                     # row pitch in the snake's own units (the coil, body 0.15: 0.105 world units,
                                      # ~15 scales round; 1.47, ~7 round, read as cobbles)
SCALE_MAIL = (1.08, 0.16)             # scale radius (x the covering radius), rise (x the pitch)
SCALE_GUTTER = 6                      # texels the head's lattice (and the dark mouth) reach past their UV islands
MOUTH_DARK = (0.3, 0.25)              # the mouth's floor: diffuse, reflection (x the metal's): shadowed, no shine (its
                                      # flat plate caught the cubemap as pale shards between the open jaws)
# the ruby (curator, on round 3's pommel: "change this to a ruby crystal pommel (we will make this glow when the
# weapon is charged)"): vanilla's black soul gem, a faceted crystal 22 units long, whole, its blunter end deep in
# the snake's mouth, its fine point out past the snout on the mouth's bisector
GEM_BSA = 'Skyrim - Meshes0.bsa'
GEM_KEY = chr(92).join(('meshes', 'clutter', 'soulgem', 'soulgemblack01.nif'))
GEM_D = chr(92).join(('textures', 'clutter', 'soulgem', 'soulgemblack.dds'))
GEM_N = chr(92).join(('textures', 'clutter', 'soulgem', 'soulgemcommon_n.dds'))
GEM_SCALE = 0.19                      # 1.3 wide: the jaws close on it just inside the snout
# curator, on the whole crystal (2.5 out of the mouth): "shorten the ruby pommel further into the mouth"; then, on
# a crystal sliced 1.45 inside the snout: "theres a gap in the snakes mouth" (the open jaws showed daylight above
# it). So the crystal reaches back to the jaw hinge (GEM_INSET inside the snout tip, its blunt end sliced flat) with
# GEM_LENGTH - GEM_INSET = 1.45 showing below the snout, and its part between the jaws is narrowed, height by
# height, in the direction the jaws open, to the gap between them (fit_gem_to_mouth): the crystal fills the mouth
GEM_LENGTH = 4.15
GEM_INSET = 2.7
MOUTH_BITE = 0.04                     # the jaws' inner surfaces sink this far into the crystal (no sliver of gap)
# then (2026-11-15): "the crystal pommel and snake eyes to purple amethyst" (it was ruby, (0.62, 0.035, 0.07))
AMETHYST = (0.40, 0.11, 0.64)         # deep violet; the gem texture's light/dark variation runs through it
GEM_SPREAD = (0.55, 0.85)             # brightness = a + b * the gem texture's normalised luminance
GEM_ENV = 0.85                        # strong reflections: glassy
GEM_TEX = {0: 'amethyst_d.dds', 1: 'amethyst_n.dds', 5: 'amethyst_m.dds'}
# ruby eyes (curator: "add ... ruby eyes to the ouroboros snake head and the pommel snake head"): Mihail's mesh has no
# eyes, they are painted on its skin; at their pupils (the darkest texels there; mapped onto the head they lie
# mirror-symmetric, x 0.78 +- 2.55, y 30.4) a dome on the crystal's textures (amethyst since 2026-11-15), its own shape (it can glow with the
# pommel when the axe is charged)
EYES_SHAPE = 'ZP_WhisperEyes'
# the souls' glow (curator 2026-11-15: "5 souls, eyes then crystal": each soul makes the amethyst eyes glow brighter, at
# 5 the crystal blazes): copies of the four eye domes, one per soul, each brighter than the last, and of the crystal,
# GLOW_LIFT out along their normals, each on its own copy of the gem's shader with Own_Emit on (emissive GLOW_COLOUR x
# its multiple), each under its own node at scale 0 (unlit). ZP_WhisperSoulsScript shows the eyes' step for the souls
# held (one node at a time) and the crystal at a full charge by setting the node's scale to 1 (SKSE
# NetImmerse.SetNodeScale, both views)
SOUL_NODE, SOUL_SHAPE = 'ZP_WhisperSoul%d', 'ZP_WhisperSoulGlow%d'
BLAZE_NODE, BLAZE_SHAPE = 'ZP_WhisperBlaze', 'ZP_WhisperBlazeGlow'
GLOW_STEPS = (0.4, 0.8, 1.3, 1.9, 2.6)       # the eyes' emissive multiple at 1..5 souls
BLAZE_MULT = 2.4                             # the crystal's at 5
GLOW_COLOUR = (0.75, 0.40, 1.0)              # amethyst light
GLOW_LIFT = 0.01                             # (the jaws bite 0.04 into the crystal: its copy stays inside them)
SLSF1_OWN_EMIT = 1 << 22
# the halo at a full charge (curator 2026-11-15: "its also not obvious if the weapon is charged ready to trigger the
# power attack, we need a glowing purple light coming from the pommel crystal"): Candlelight's two flare sprites
# (vanilla magic\LightSpellActorFX.nif: "Flash", a soft round glow, FXGlowSpotLinear; "Circle02", a bright flash,
# FXBrightFash01; additive), each under its own camera-facing billboard node (the vanilla node's mode) at the visible
# part of the crystal, inside the blaze node: they show with the blazing crystal. Copied with their own shader and
# alpha blocks, no controllers (a weapon runs none: their colour alpha, which Candlelight's controllers raise, is set
# to 1), the shader colour and the vertex colours purple (the rim's alpha fade kept). A real light comes with it
# (03-build-records.py: the charged light)
HALO_BSA = 'Skyrim - Meshes1.bsa'
HALO_KEY = chr(92).join(('meshes', 'magic', 'lightspellactorfx.nif'))
HALO_PARTS = {'Flash': (4.2, 1.6), 'Circle02': (2.4, 2.2)}   # sprite: (its size across, emissive multiple)
HALO_COLOUR = (0.78, 0.42, 1.0)
HALO_RGB = {'Flash': ((150, 70, 255), (225, 170, 255)), 'Circle02': ((165, 80, 255), (255, 225, 255))}   # rim, centre
# every sprite on the crystal fades out within SOFT_DEPTH units of what stands behind it (the effect shader's soft
# depth, Bottled Shaders' Effect.hlsl: softMul = (scene depth - sprite depth) / soft depth). Candlelight's flash brought
# 128, made for a glow floating in the air: on the pommel, with the snake's head, the hand and the body a few units
# behind, it faded the halo's soft glow to almost nothing
SOFT_DEPTH = 0.75
# the Smite orb at a full charge (curator 2026-11-15: "still need to add aditional glow effect of some kind to the
# pommel crystall", then "add a purple smite orb shining on the crystal" / "something like the smite orb but glowing
# purple", "Only at 5, much stronger"): Prophecy's Smite orb (Kittytail's Holy Templar meshes\lightpower\
# holyboltproj.nif, the copy Patch Collection ships) on the crystal, inside the blaze node. Its static parts, each
# on its own camera-facing billboard (the orb's own node mode) at the crystal: the bright core flash (Circle05), the
# wisps (Wisps04:0) and the wide soft glow (Flash03), each at ORB_PARTS' size across and
# about twice the orb's own emissive multiple. Its two particle systems (the sparkles) stay off: a weapon runs no
# controllers (nor do these copies: its shaders' UV scrolls are dropped, the vapour stands still). Purple: the palette
# parts take their colour from the palette alone (Effect.hlsl: colour = multiple x palette(texture green, shader
# colour red x vertex red); the shader and vertex colours only pick the palette's row, so they stay the orb's), so
# their palette is the game's own gradient (Glorious Gradients recolours the vanilla ones) with the brightness
# laid on ORB_RAMP; the glow (no palette) gets purple vertex colours (ORB_FLASH_RGB)
ORB_SRC = 'meshes/lightpower/holyboltproj.nif'
ORB_SOURCE = 'Zenderal - Patch Collection'
ORB_BILLBOARD = 'Wisps04'
# (its vapour halo `Halo:0`, the wispy purple ring 7.5 across, came off the same evening: curator "can you cut the out
# ring of the orb so its just the shining centre?")
ORB_PARTS = {'Circle05': (3.4, 2.4),        # part: (size across, emissive multiple; the orb's: 1.2, 0.7, 1.0)
             'Wisps04:0': (10.0, 1.4),      # (on the crystal its wisps read as a ray burst round the core)
             'Flash03': (13.0, 1.6)}
ORB_RAMP = ((0.0, (0.0, 0.0, 0.0)), (0.3, (0.20, 0.04, 0.42)), (0.65, (0.58, 0.22, 1.0)), (1.0, (0.88, 0.70, 1.0)))
ORB_FLASH_RGB = ((150, 70, 255), (220, 150, 255))   # Flash03's rim, centre (its alpha kept)
ORB_PALETTE = 'WhisperOrb_%s.dds'                    # under TEX_DIR
# the blade snakes' orbs at a full charge (curator 2026-11-15: "just like the pommel glow effect can you add 3 very small
# glowing orbs (with no outer circles) to the 3 snakes snakeheads on the Axe blade. each side", "when its charged I
# mean"): on each of the six relief snakes' heads, between its painted eyes (eye_domes' points), BLADE_ORB_LIFT above
# its crown, a tiny copy of the pommel's orb, its bright core and soft glow only, inside the blaze node (lit with the
# crystal). Their sprites lie on the blade, so they have no soft fade (the soft depth would fade a sprite to nothing
# where the head and blade stand just behind it: a hard z-test edge instead, out of sight face-on)
BLADE_ORB_PARTS = {'Circle05': (0.7, 3.0),          # part: (size across, emissive multiple)
                   'Flash03': (1.5, 1.4)}
BLADE_ORB_LIFT = 0.06                                # above the head's crown, along the blade face's normal
SLSF1_SOFT = 1 << 30
LSP_FLAGS1, LSP_EMISSIVE, LSP_EMIT_MULT = 16, 44, 56   # BSLightingShaderProperty (SE, no extra data)
# the langets (curator: "how can we blend these 2 elements together better?" - the socket's hard edge on the blade -
# then picked "Langets"): one per blade face, the socket's straps over the blade, its engraving mirrored onto them,
# billyro's own rivet head on each, the blade snakes' tails tucked under their tips (they leave from under them)
LANGET_SHAPE, RIVETS_SHAPE = 'ZP_WhisperLangets', 'ZP_WhisperLangetRivets'
LANGET = dict(root_x=-0.2, tip_x=-2.0,        # x: in the socket's chamfer (its blade face x -0.37, panel -0.03) .. tip
              root_half=None, tip_half=0.7,   # half-widths: at the socket (socket_fit: its face's), the tip's radius
              tip_h=0.32,                     # height over the blade face at the tip (at the root: socket_fit, per face;
                                              # the snakes' tails are ~0.25 thick)
              bevel=0.14, skirt=0.03,         # the rounded edge's width; how far the edge sinks into the blade
              rows=56, cols=41)
LANGET_INSET = 0.06                   # the langet root's ends short of the socket face's (y)
LANGET_TUCK = 0.03                    # its root this far under the socket's outer surface
LANGET_TAILS = (0.36, 0.0, -0.36)     # the blade snakes' tail tips under the langet's tip: y off its middle (upward,
                                      # outward, downward snakes)
LANGET_TAIL_IN = 0.45                 # how far in from the tip
LANGET_RIVET = (-1.0, 0.62, 1.2)      # x, scale across, scale in height of billyro's rivet head (0.12 tall: scaled
                                      # evenly it stood 0.03 proud and vanished)
LANGET_RIVET_SINK = 0.015
BLADE_RIVET_SRC = (snake.BLADE_ORIGIN[0] + noble.BLADE_SHIFT[0], snake.BLADE_ORIGIN[1] + noble.BLADE_SHIFT[1])
EYE_UV = ((0.0481, 0.3496), (0.0471, 0.6543))
EYE_R = 0.5                           # the dome's radius, the snake's own units (the painted eye: ~0.45)
EYE_FLAT = 0.75                       # its depth along the head's normal, x the radius
EYE_PROUD = 0.45                      # how far it stands out of the head, x the radius


def name_of(nif, k):
    return nif.string(struct.unpack_from('<i', nif.blocks[k], 0)[0])


def shape(nif, name):
    k = [k for k in nif.find('BSTriShape') if name_of(nif, k) == name]
    assert len(k) == 1, (name, len(k))
    return k[0]


def islands(P, T):
    """Island id per triangle (triangles joined through shared vertex positions)."""
    key = {}
    rep = np.array([key.setdefault(tuple(p), i) for i, p in enumerate(np.round(P, 4))])
    par = np.arange(len(P))

    def f(a):
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a
    for t in T:
        a = f(rep[t[0]])
        for x in t[1:]:
            par[f(rep[x])] = a
    return np.array([f(rep[i]) for i in range(len(P))])[T[:, 0]]


def cut(s):
    """The axe shape loses: the neck tube, the collar band and its two rivets (the spine's place), the two lower
    handle bands and the whole shaft (rebuilt as the grip shape). Returns the dropped triangles and, among them,
    the shaft's below the top band's top (the grip's source). Asserted by the parts' measured extents (tools/01's
    base)."""
    P, T = s['pos'], s['tris']
    isl = islands(P, T)
    ext = {r: (P[np.unique(T[isl == r])].min(0), P[np.unique(T[isl == r])].max(0)) for r in np.unique(isl)}
    neck = [r for r, (lo, hi) in ext.items() if lo[1] > 19 and hi[1] > 33 and hi[0] > 3]
    band = [r for r, (lo, hi) in ext.items() if abs(lo[1] - 17.54) < 0.05]
    rivets = [r for r, (lo, hi) in ext.items() if abs(lo[1] - 19.48) < 0.05]
    handle = [r for r, (lo, hi) in ext.items() if lo[1] < -19]
    low_bands = [r for r, (lo, hi) in ext.items() if (abs(lo[1] + 8.5) < 0.05 and abs(hi[1] + 7.5) < 0.05)
                 or (abs(lo[1] + 10.5) < 0.05 and abs(hi[1] + 9.5) < 0.05)]
    top_band = [r for r, (lo, hi) in ext.items() if abs(lo[1] - 9.0) < 0.05 and abs(hi[1] - 10.0) < 0.05]
    assert (len(neck), len(band), len(rivets), len(handle), len(low_bands), len(top_band)) == (1, 1, 2, 1, 2, 1), \
        (neck, band, rivets, handle, low_bands, top_band)
    # billyro's neck, collar band and rivets go (the Noble axe's upper shaft and socket take their place: noble.py),
    # the shaft too (the grip shape replaces its lower part), the top band (the connector ouroboros)
    drop = np.isin(isl, neck + band + rivets + handle + low_bands + top_band)
    shaft = np.isin(isl, handle) & (P[T][:, :, 1].min(1) < GRIP_TOP)   # build_grip clips at GRIP_TOP (the tube's
                                                                        # triangles run on from y 9.54 to 20)
    return drop, shaft


def holder_ring(hs):
    """billyro's belt ring in the holder shape: the island that is a flat torus (fitted: centre, plane normal,
    centreline radius ~3, tube ~0.5), and the clasp it hangs from (the small island nearest it). Returns the ring's
    triangles and (centre, normal, radius, tube radius, clasp centre)."""
    P, T = hs['pos'], hs['tris']
    isl = islands(P, T)
    fits = {}
    for r in np.unique(isl):
        Q = P[np.unique(T[isl == r])]
        c = Q.mean(0)
        _, _, Vt = np.linalg.svd(Q - c)
        n = Vt[2]
        d = Q - c
        rr = np.linalg.norm(d - np.outer(d @ n, n), axis=1)
        fits[r] = (c, n, rr.min(), rr.max(), np.abs(d @ n).max(), len(Q))
    ring = [r for r, f in fits.items() if 2.0 < f[2] < 3.0 and 3.0 < f[3] < 4.0 and f[4] < 0.7]
    assert len(ring) == 1, {r: (f[0].round(2), round(f[2], 2), round(f[3], 2)) for r, f in fits.items()}
    c, n, rmin, rmax, _, _ = fits[ring[0]]
    others = [r for r in fits if r != ring[0]]
    clasp = min(others, key=lambda r: (fits[r][5], np.linalg.norm(fits[r][0] - c)))   # the small one
    return isl == ring[0], (c, n, (rmin + rmax) / 2, (rmax - rmin) / 2, fits[clasp][0])


def clip_keep(P, A, T, dist):
    """Triangles clipped to dist <= 0 (dist: one signed value per vertex, linear in position), per-vertex attribute
    arrays A interpolated at the cut; returns positions, attributes, triangles and the cut's new edges (vertex index
    pairs)."""
    P, A, dist = list(P), [list(a) for a in A], list(dist)
    cache, out, cut_edges = {}, [], []

    def cut_point(i, j):
        key = (min(i, j), max(i, j))
        if key not in cache:
            f = dist[i] / (dist[i] - dist[j])
            P.append(P[i] + (P[j] - P[i]) * f)
            for a in A:
                a.append(a[i] + (a[j] - a[i]) * f)
            dist.append(0.0)
            cache[key] = len(P) - 1
        return cache[key]
    for tri in T:
        inside = [dist[v] <= 0 for v in tri]
        if all(inside):
            out.append(tuple(tri))
            continue
        if not any(inside):
            continue
        n = sum(inside)
        r = inside.index(True) if n == 1 else inside.index(False)      # the lone vertex
        a, b, c = tri[r], tri[(r + 1) % 3], tri[(r + 2) % 3]
        ab, ac = cut_point(a, b), cut_point(a, c)
        if n == 1:                                                     # a inside: one triangle
            out.append((a, ab, ac))
            cut_edges.append((ab, ac))
        else:                                                          # a outside: a quad
            out.append((ab, b, c))
            out.append((ab, c, ac))
            cut_edges.append((ac, ab))
    return np.array(P), [np.array(a) for a in A], np.array(out), cut_edges


def compact(P, A, T):
    used = np.unique(T)
    remap = np.full(len(P), -1)
    remap[used] = np.arange(len(used))
    return P[used], [a[used] for a in A], remap[T]


def winding_outward(P, N, T):
    """+1 when the triangles' (b - a) x (c - a) faces the way their vertex normals do (counter-clockwise outward)."""
    fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    s = np.sign((fn * N[T].sum(1)).sum(1))
    assert abs(s.mean()) > 0.95, s.mean()
    return 1.0 if s.mean() > 0 else -1.0


def cap(P, A, T, cut_edges, normal, wind):
    """The cut sealed with a flat fan round its centre, facing `normal`; cap vertices duplicated so the cap keeps its
    own flat normal. A = [normals, tangents, bitangents, uvs, colours]."""
    ring = sorted({v for e in cut_edges for v in e})
    centre = P[ring].mean(0)
    capv = {v: len(P) + 1 + i for i, v in enumerate(ring)}
    nrm = np.asarray(normal, float)
    tg = np.cross(nrm, [0.0, 0.0, 1.0]) if abs(nrm[2]) < 0.9 else np.cross(nrm, [1.0, 0.0, 0.0])
    tg /= np.linalg.norm(tg)
    bt = np.cross(nrm, tg)
    P = np.vstack([P, centre, P[ring]])
    N, Tg, Bt, UV, C = A
    k = len(ring) + 1
    N = np.vstack([N, np.repeat(nrm[None], k, 0)])
    Tg = np.vstack([Tg, np.repeat(tg[None], k, 0)])
    Bt = np.vstack([Bt, np.repeat(bt[None], k, 0)])
    UV = np.vstack([UV, UV[ring].mean(0)[None], UV[ring]])
    C = np.vstack([C, C[ring].mean(0)[None], C[ring]])
    cidx = len(P) - k
    faces = []
    for a, b in cut_edges:
        f = (cidx, capv[a], capv[b])
        if np.sign(np.cross(P[f[1]] - centre, P[f[2]] - centre) @ nrm) != wind:
            f = (cidx, capv[b], capv[a])
        faces.append(f)
    return P, [N, Tg, Bt, UV, C], np.vstack([T, np.array(faces)])


def build_grip(s, shaft, mount):
    """billyro's shaft below the top band, cut at GRIP_END, every vertex moved onto the thin ellipse round the
    handle axis (same height and direction from the axis), flaring over GRIP_FLARE to the Noble shaft's ellipse
    `mount` (cx, cz, a, b) x GRIP_FLARE_IN; its normals the ellipse's, its tangent frame re-orthogonalised to them;
    both cut ends capped. Returns positions, normals, tangents, bitangents, UVs, colours, triangles."""
    P, T = s['pos'], s['tris'][shaft]
    A = [s['normal'], s['tangent'], s['bitangent'], s['uv'].astype(float), s['color'].astype(float)]
    wind = winding_outward(P, s['normal'], T)
    P, A, T = subdivide(P, A, T, GRIP_SUBDIVIDE)                        # fine enough to tuck under the snake's neck
    P, A, T = slice_mesh(P, A, T, GRIP_SLICES)                          # vertex rows where the head caps the grip
    P, A, T, edges = clip_keep(P, A, T, GRIP_END - P[:, 1])            # keep y >= GRIP_END
    assert edges, 'the grip cut missed the shaft'
    P, A, T, top_edges = clip_keep(P, A, T, P[:, 1] - GRIP_TOP)          # keep y <= GRIP_TOP (billyro's band is gone)
    assert top_edges, 'the grip top cut missed the shaft'
    keep_bottom = {v for e in edges for v in e}
    edges = [e for e in edges if e[0] < len(P) and e[1] < len(P)]
    assert {v for e in edges for v in e} == keep_bottom
    # onto the ellipse
    dx, dz = P[:, 0] - snake.AXIS_X, P[:, 2]
    phi = np.arctan2(dz, dx)
    w = snake.smoothstep(GRIP_FLARE[0], GRIP_FLARE[1], P[:, 1])   # 0 on the grip, 1 at the shaft's lower end
    cx = snake.AXIS_X + (mount[0] - snake.AXIS_X) * w
    cz = mount[1] * w
    a = snake.GRIP_A + (mount[2] * GRIP_FLARE_IN - snake.GRIP_A) * w
    b = snake.GRIP_B + (mount[3] * GRIP_FLARE_IN - snake.GRIP_B) * w
    b = b * end_tuck(P[:, 1], phi)
    r = a * b / np.sqrt((b * np.cos(phi)) ** 2 + (a * np.sin(phi)) ** 2)
    P = np.stack([cx + r * np.cos(phi), P[:, 1], cz + r * np.sin(phi)], -1)
    N = snake.nz(np.stack([(P[:, 0] - cx) / a ** 2, np.zeros(len(P)), (P[:, 2] - cz) / b ** 2], -1))
    Tg = snake.nz(A[1] - N * (A[1] * N).sum(1, keepdims=True))
    Bt = A[2] - N * (A[2] * N).sum(1, keepdims=True) - Tg * (A[2] * Tg).sum(1, keepdims=True)
    Bt = snake.nz(Bt)
    P, A, T = cap(P, [N, Tg, Bt, A[3], A[4]], T, edges, (0.0, -1.0, 0.0), wind)
    P, A, T = cap(P, A, T, top_edges, (0.0, 1.0, 0.0), wind)
    P, A, T = compact(P, A, T)
    N, Tg, Bt, UV, C = A
    return P, N, Tg, Bt, UV, np.clip(np.round(C), 0, 255).astype(np.uint8), T


def face_height(s, side, step=0.04):
    """The axe shape's face height (z) over x, y on one side (+1: the +z face, its highest surface; -1: the -z face,
    its lowest), rasterised from the triangles facing that way; a function of (n, 2) points (bilinear, holes filled
    from the nearest cell)."""
    P, T = s['pos'], s['tris']
    fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
    wind = winding_outward(P, s['normal'], T)
    tris = T[fn[:, 2] * wind * side > 0.3]
    x0, y0 = P[:, 0].min() - 0.5, P[:, 1].min() - 0.5
    nx, ny = int((P[:, 0].max() + 0.5 - x0) / step) + 1, int((P[:, 1].max() + 0.5 - y0) / step) + 1
    Z = np.full((ny, nx), np.nan)
    for t in tris:
        q = P[t]
        ix0, ix1 = int((q[:, 0].min() - x0) / step), int((q[:, 0].max() - x0) / step) + 1
        iy0, iy1 = int((q[:, 1].min() - y0) / step), int((q[:, 1].max() - y0) / step) + 1
        gx, gy = np.meshgrid(x0 + step * np.arange(ix0, ix1 + 1), y0 + step * np.arange(iy0, iy1 + 1))
        d = (q[1, 1] - q[2, 1]) * (q[0, 0] - q[2, 0]) + (q[2, 0] - q[1, 0]) * (q[0, 1] - q[2, 1])
        if abs(d) < 1e-12:
            continue
        w0 = ((q[1, 1] - q[2, 1]) * (gx - q[2, 0]) + (q[2, 0] - q[1, 0]) * (gy - q[2, 1])) / d
        w1 = ((q[2, 1] - q[0, 1]) * (gx - q[2, 0]) + (q[0, 0] - q[2, 0]) * (gy - q[2, 1])) / d
        w2 = 1 - w0 - w1
        m = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        z = w0 * q[0, 2] + w1 * q[1, 2] + w2 * q[2, 2]
        sub = Z[iy0:iy1 + 1, ix0:ix1 + 1]
        cur = np.where(np.isnan(sub), -np.inf * side, sub)
        better = m & ((z - cur) * side > 0)
        sub[better] = z[better]
    assert (~np.isnan(Z)).mean() > 0.2, (~np.isnan(Z)).mean()
    for _ in range(40):                                       # holes (rivet holes, gaps) from their neighbours
        hole = np.isnan(Z)
        if not hole.any():
            break
        pad = np.pad(Z, 1, constant_values=np.nan)
        nb = np.stack([pad[:-2, 1:-1], pad[2:, 1:-1], pad[1:-1, :-2], pad[1:-1, 2:]])
        cnt = (~np.isnan(nb)).sum(0)
        mean = np.where(cnt > 0, np.nansum(nb, 0) / np.maximum(cnt, 1), np.nan)
        Z = np.where(hole & (cnt > 0), mean, Z)
    Z = np.where(np.isnan(Z), np.nanmedian(Z), Z)

    def f(xy):
        gx = np.clip((xy[:, 0] - x0) / step, 0, nx - 1.001)
        gy = np.clip((xy[:, 1] - y0) / step, 0, ny - 1.001)
        i, j = gx.astype(int), gy.astype(int)
        a, b = gx - i, gy - j
        return (Z[j, i] * (1 - a) * (1 - b) + Z[j, i + 1] * a * (1 - b) + Z[j + 1, i] * (1 - a) * b
                + Z[j + 1, i + 1] * a * b)
    return f


def inside_mesh(points, V, T):
    """Per point: inside the closed surface (V, T)? A ray along +x counted against the triangles near its height
    (an odd count is inside)."""
    out = []
    d = np.array([1.0, 0.0, 0.0])
    for p in points:
        near = T[np.abs(V[T][:, :, 1] - p[1]).min(1) < 1.0]
        a, b, c = V[near[:, 0]], V[near[:, 1]], V[near[:, 2]]
        e1, e2 = b - a, c - a
        h = np.cross(d, e2)
        det = (e1 * h).sum(1)
        ok = np.abs(det) > 1e-12
        f = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
        sv = p - a
        u = f * (sv * h).sum(1)
        q = np.cross(sv, e1)
        v = f * (q @ d)
        t = f * (q * e2).sum(1)
        hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-9)
        out.append(hit.sum() % 2 == 1)
    return np.array(out)


def repoint(nif, shader_k, swaps):
    ts = struct.unpack_from('<i', nif.blocks[shader_k], nifse.LSP_TEXSET)[0]
    paths = nifse.texture_paths(nif.blocks[ts])
    out = []
    for p in paths:
        if p.lower() in swaps:
            out.append(swaps[p.lower()])
        else:
            assert not p.lower().startswith((r'textures\billyro', r'textures\cubemaps\nissibeach')), p
            out.append(p)
    nif.blocks[ts] = nifse.texture_set(out)
    return out


def vanilla_texture(rel):
    for name in TEXTURE_BSAS:
        path = os.path.join(DATA, name)
        if not os.path.isfile(path):
            continue
        d, listing = _bsa.listing(path)
        if rel.lower() in listing:
            return _bsa.read(d, listing[rel.lower()]), name
    raise SystemExit(f'{rel} is in none of {TEXTURE_BSAS} under {DATA}')


def uv_mask(uv, T, W, H, grow=2):
    """Texels under the triangles' UVs (W x H), grown by `grow` pixels (mip bleed)."""
    from PIL import Image, ImageDraw, ImageFilter
    im = Image.new('L', (W, H), 0)
    dr = ImageDraw.Draw(im)
    for t in T:
        dr.polygon([(uv[v, 0] * W, uv[v, 1] * H) for v in t], fill=255)
    if grow:
        im = im.filter(ImageFilter.MaxFilter(2 * grow + 1))
    return np.asarray(im) > 0


def billyro_texture(name):
    return sr.load_image(open(os.path.join(RAW, 'main', 'textures', 'billyro', 'stalwartaxe', name), 'rb').read())


def blade_metal(s):
    """The blade's material as billyro painted it: medians of the diffuse, the env mask and the normal map's alpha
    (specular) over the texels under the crescent blade's UVs."""
    from PIL import Image
    d, m, n = billyro_texture('axe.dds'), billyro_texture('axe_m.dds'), billyro_texture('axe_n.dds')
    H, W = d.shape[:2]
    m = np.asarray(Image.fromarray((m[..., 0] * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR), np.float32) / 255
    blade = s['tris'][s['pos'][s['tris']].mean(1)[:, 0] < BLADE_X]
    sel = uv_mask(s['uv'], blade, W, H, grow=0)
    assert sel.mean() > 0.15, sel.mean()                     # the crescent fills a quarter of the atlas
    diffuse = np.median(d[..., :3][sel], 0)
    env, spec = float(np.median(m[sel])), float(np.median(n[..., 3][sel]))
    # billyro's steel: dark, neutral, a cubemap's shine
    assert 0.06 < diffuse.mean() < 0.2 and np.ptp(diffuse) < 0.02 and 0.1 < env < 0.4 and 0.2 < spec < 0.6, \
        (diffuse, env, spec)
    return diffuse, env, spec, int(sel.sum())


def metal_textures(out_root, s):
    """The shared smooth metal set: the blade's diffuse, env mask and specular, a flat normal map."""
    diffuse, env, spec, texels = blade_metal(s)
    k = METAL_TEX
    write = lambda a, name, fmt: sr.write_texture(a.astype(np.float32), os.path.join(out_root, *(TEX_DIR + name).split('/')), fmt)  # noqa: E731
    write(np.broadcast_to(diffuse, (k, k, 3)).copy(), 'metal_d.dds', 'BC7_UNORM')
    write(np.full((k, k, 3), env), 'metal_m.dds', 'BC1_UNORM')
    write(np.broadcast_to(np.array([0.5, 0.5, 1.0, spec]), (k, k, 4)).copy(), 'metal_n.dds', 'BC7_UNORM')
    print(f'  metal textures: the blade\'s own ({texels} texels of billyro\'s axe.dds): diffuse '
          f'{" ".join("%.3f" % v for v in diffuse)}, env mask {env:.3f}, specular {spec:.3f}; flat normals')
    return diffuse, env, spec


RAYS = ((1.0, 0.013, 0.017), (-0.011, 0.019, 1.0), (0.007, -0.013, -1.0))   # skewed: never along an edge


def snake_inside(points, V, T):
    """Per point: inside the snake's closed body? Three rays vote (odd crossings = inside); the loose mouth floor
    (its own little piece, an open sheet that flips a single ray's count) left out."""
    comp = components(V, T)
    T = T[comp[T[:, 0]] == np.bincount(comp).argmax()]
    lo, hi = points[:, 1].min() - 0.5, points[:, 1].max() + 0.5
    T = T[(V[T][:, :, 1].max(1) > lo) & (V[T][:, :, 1].min(1) < hi)]
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    e1, e2 = b - a, c - a
    ty0, ty1 = V[T][:, :, 1].min(1), V[T][:, :, 1].max(1)
    reach = 0.15                                               # the rays are near level: a point's triangles span its
    votes = np.zeros(len(points), int)                         # height within this
    for d in RAYS:
        d = snake.nz(np.array(d))
        h = np.cross(d, e2)
        det = (e1 * h).sum(1)
        ok = np.abs(det) > 1e-12
        f = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
        for i, p in enumerate(points):
            m = (ty0 < p[1] + reach) & (ty1 > p[1] - reach)
            sv = p - a[m]
            u = f[m] * (sv * h[m]).sum(1)
            q = np.cross(sv, e1[m])
            v = f[m] * (q @ d)
            t = f[m] * (q * e2[m]).sum(1)
            votes[i] += (ok[m] & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-9)).sum() % 2
    return votes >= 2


def surface_distance(points, V, T):
    """Per point: the distance to the nearest of the triangles (V, T)."""
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    ab, ac = b - a, c - a
    n = np.cross(ab, ac)
    nn = np.maximum((n * n).sum(1), 1e-18)
    d00, d01, d11 = (ab * ab).sum(1), (ab * ac).sum(1), (ac * ac).sum(1)
    den = np.maximum(d00 * d11 - d01 * d01, 1e-18)
    out = []
    for p in points:
        ap = p - a
        q = p - ((ap * n).sum(1) / nn)[:, None] * n             # onto each plane
        v2 = q - a
        d20, d21 = (v2 * ab).sum(1), (v2 * ac).sum(1)
        v = (d11 * d20 - d01 * d21) / den
        w = (d00 * d21 - d01 * d20) / den
        inside = (v >= 0) & (w >= 0) & (v + w <= 1)
        plane = np.abs((ap * n).sum(1)) / np.sqrt(nn)
        corner = np.min([np.linalg.norm(p - a, axis=1), np.linalg.norm(p - b, axis=1), np.linalg.norm(p - c, axis=1)], 0)
        out.append(np.where(inside, plane, corner).min())
    return np.array(out)


def settle_neck():
    """The coil snake built with its neck's belly settled NECK_SINK into the leather over SETTLE (see there):
    snake.build's outputs plus the remaining worst error and the rounds taken."""
    fix, y0, y1, fade = None, *SETTLE
    for rnd in range(SETTLE_ROUNDS):
        out = snake.build(MODS, h_fix=fix)
        SV, ST, lay = out[0], out[5], out[6]
        idx = np.where((lay.Q[:, 1] > y0) & (lay.Q[:, 1] < y1) & (lay.s > lay.head_len - 2.5))[0]
        idx = idx[::max(len(idx) // 160, 1)]
        u, y = lay.s[idx], lay.Q[idx, 1]
        pts, _ = snake.grip_ellipse(lay.psi_of_y(y)[0], y)
        ins = snake_inside(pts, SV, ST)
        sunk = np.where(ins, 1.0, -1.0) * surface_distance(pts, SV, ST)
        err = sunk - NECK_SINK
        w = snake.smoothstep(u[0], u[0] + fade, u) * (1 - snake.smoothstep(u[-1] - fade, u[-1], u))
        full = w > 0.999                                            # judged where the correction is whole
        worst = float(np.abs(err[full]).max())
        print(f'  settle {rnd}: the neck belly {sunk.min():+.3f} .. {sunk.max():+.3f} into the leather (want '
              f'{NECK_SINK}); worst error {worst:.3f}')
        if os.environ.get('SETTLE_DEBUG'):
            for j in range(0, len(y), max(len(y) // 24, 1)):
                print(f'      y {y[j]:6.2f} u {u[j]:6.2f} sunk {sunk[j]:+.3f} fix {float(fix(u[j:j+1])[0]) if fix else 0:+.3f}')
        if sunk[full].min() >= SETTLE_BAND[0] and sunk[full].max() <= SETTLE_BAND[1]:
            return out, (float(sunk[full].min()), float(sunk[full].max())), rnd
        k = max(int(SETTLE_BLUR / max(np.median(np.diff(u)), 1e-6)), 1)
        g = np.exp(-0.5 * (np.arange(-3 * k, 3 * k + 1) / k) ** 2)
        err = np.convolve(np.pad(err, 3 * k, mode='edge'), g / g.sum(), 'valid')
        vals = (fix(u) if fix else 0.0) + err * w
        fix = lambda q, uu=u, vv=vals: np.interp(q, uu, vv, left=0.0, right=0.0)  # noqa: E731
    raise AssertionError(f'the neck did not settle onto the leather (worst error {worst:.3f} after {SETTLE_ROUNDS} rounds)')


def end_tuck(y, phi):
    """The grip's z semi-axis factor at heights y, angles phi round the axis (the -z half narrowed at its end)."""
    k = END_TUCK * snake.smoothstep(END_TUCK_TOP, GRIP_END, np.asarray(y, float))
    return np.where(np.sin(phi) < 0, 1.0 - k, 1.0)


def grip_point(th, y):
    """The grip's ellipse (below its flare; its end narrowed: end_tuck) at angles th round the axis and heights y."""
    a, b = snake.GRIP_A, snake.GRIP_B * end_tuck(y, th)
    r = a * b / np.sqrt((b * np.cos(th)) ** 2 + (a * np.sin(th)) ** 2)
    return np.stack([snake.AXIS_X + r * np.cos(th), np.asarray(y, float) + 0 * th, r * np.sin(th)], -1)


def grid_labels(mask):
    """4-connected labels of the True cells of a (height, angle) grid, the angle wrapping round; -1 elsewhere."""
    lab = np.full(mask.shape, -1)
    nx = mask.shape[1]
    n = 0
    for sy, sx in zip(*np.where(mask)):
        if lab[sy, sx] >= 0:
            continue
        stack = [(sy, sx)]
        lab[sy, sx] = n
        while stack:
            y, x = stack.pop()
            for yy, xx in ((y + 1, x), (y - 1, x), (y, (x + 1) % nx), (y, (x - 1) % nx)):
                if 0 <= yy < mask.shape[0] and mask[yy, xx] and lab[yy, xx] < 0:
                    lab[yy, xx] = n
                    stack.append((yy, xx))
        n += 1
    return lab


def tuck_grip(P, N, T, SV, ST):
    """The leather's little islands that poke out through the coil's head and neck (curator, on a red speck: "spotted
    the handle clipping here"; a render crop then showed red flecks on the head's back, both sides of the neck,
    where the head is thinner than the grip it caps). The grip's surface (the ellipse it is laid on; split
    GRIP_SUBDIVIDE x so the mesh follows it) is tested on an angle x height grid (TUCK_GRID) below TUCK_TOP; patches
    outside the snake not joined (through outside cells, round the wrap) to the grip above are islands. The flecks
    are ~0.08 across and only ~0.05 of head lies between them and the visible leather, so a test on the mesh's own
    points (spaced wider than that) joined them across it. Grip vertices on an island or TUCK_NEAR cells from one
    are moved inward until TUCK_DEPTH under the snake's surface; points sampled over the tucked mesh on the islands
    are asserted inside. Returns the new positions, the vertices moved, the island cells."""
    nth, dy = TUCK_GRID
    ths = (np.arange(nth) + 0.5) / nth * 2 * np.pi - np.pi
    ys = np.arange(GRIP_END + dy / 2, TUCK_TOP, dy)
    TH, Y = np.meshgrid(ths, ys)
    out = ~snake_inside(grip_point(TH.ravel(), Y.ravel()), SV, ST).reshape(Y.shape)
    assert out[-1].mean() > 0.6, 'the snake covers most of the grip at TUCK_TOP: raise it'   # (the coil's belly sits
    lab = grid_labels(out)                                                                    # in it: a band covered)
    island = out & ~np.isin(lab, np.unique(lab[-1][out[-1]]))
    size = np.bincount(lab[lab >= 0])                           # flecks are small: a big patch shut in by the
    island &= (lab >= 0) & (size[np.maximum(lab, 0)] <= TUCK_ISLAND_MAX)   # snake is visible leather (2026-11-15:
                                                                # the neck's S seals one off on the -x side)
    near = island.copy()
    for _ in range(TUCK_NEAR):
        grown = near.copy()
        grown |= np.roll(near, 1, axis=1) | np.roll(near, -1, axis=1)
        grown[1:] |= near[:-1]
        grown[:-1] |= near[1:]
        near = grown

    def cell(Q):
        iy = np.floor((Q[:, 1] - ys[0] + dy / 2) / dy).astype(int)
        ith = (np.floor((grip_angle(Q) + np.pi) / (2 * np.pi) * nth).astype(int)) % nth
        ok = (iy >= 0) & (iy < len(ys))
        return ok, np.clip(iy, 0, len(ys) - 1), ith
    if not island.any():
        return P, 0, 0
    ok, iy, ith = cell(P)
    sel = np.where(ok & near[iy, ith])[0]
    assert len(sel), 'islands with no grip vertex on them: split the grip finer'
    P = P.copy()
    w = np.random.default_rng(5).dirichlet((1, 1, 1), 24)       # every grip triangle below TUCK_TOP, not just those
    moved = set()                                               # moved
    for rnd in range(4):
        # tuck `sel`; then sample the triangles over the islands, and a triangle whose surface still shows (billyro's
        # rows are tall: one can span the edge of a contact patch, 2026-11-15 at the coil's first turn) has its own
        # vertices tucked in the next round, a TUCK_DEPTH deeper each time (the belly is round over a flat triangle)
        ins = snake_inside(P[sel], SV, ST)
        depth = surface_distance(P[sel], SV, ST)
        want = TUCK_DEPTH * (rnd + 1)
        P[sel] -= N[sel] * np.where(ins, np.maximum(want - depth, 0.0), depth + want)[:, None]
        moved |= set(sel.tolist())
        tt = T[(np.ptp(P[T][:, :, 1], axis=1) > 1e-3) & (P[T][:, :, 1].min(1) < TUCK_TOP)]
        Q = np.einsum('sk,tkc->tsc', w, P[tt]).reshape(-1, 3)
        okq, qy, qth = cell(Q)
        on = okq & island[qy, qth]
        bad = on.copy()
        bad[on] = ~snake_inside(Q[on], SV, ST)
        left, total = int(bad.sum()), int(on.sum())
        if not left:
            break
        sel = np.unique(tt[np.unique(np.where(bad)[0] // len(w))])
    assert left == 0, f'{left} of {total} points sampled on the tucked islands still show'
    return P, len(moved), int(island.sum())


def slice_mesh(P, A, T, cuts):
    """The mesh cut by the horizontal planes y = each of `cuts` (both sides kept): each crossing triangle split into
    the two polygons either side, fanned; a crossing edge's new point shared by its triangles (no T-junctions).
    Attributes interpolated along the edges."""
    for c in cuts:
        d = P[:, 1] - c
        d = np.where(np.abs(d) < 1e-7, 0.0, d)
        cross = (d[T].min(1) < 0) & (d[T].max(1) > 0)
        if not cross.any():
            continue
        n0, key, extra_P, extra_A = len(P), {}, [], [[] for _ in A]

        def cut(i, j):
            k = (min(i, j), max(i, j))
            if k not in key:
                t = d[i] / (d[i] - d[j])
                extra_P.append(P[i] + t * (P[j] - P[i]))
                for m, a in enumerate(A):
                    extra_A[m].append(a[i] + t * (a[j] - a[i]))
                key[k] = n0 + len(extra_P) - 1
            return key[k]
        new = []
        for t in T[cross]:
            pos, neg = [], []
            for k in range(3):
                i, j = int(t[k]), int(t[(k + 1) % 3])
                if d[i] >= 0:
                    pos.append(i)
                if d[i] <= 0:
                    neg.append(i)
                if d[i] * d[j] < 0:
                    m = cut(i, j)
                    pos.append(m)
                    neg.append(m)
            for poly in (pos, neg):
                new += [(poly[0], poly[k], poly[k + 1]) for k in range(1, len(poly) - 1)]
        P = np.vstack([P, np.array(extra_P)])
        A = [np.vstack([a, np.array(e)]) for a, e in zip(A, extra_A)]
        T = np.vstack([T[~cross], np.array(new)])
    return P, A, T


def subdivide(P, A, T, n):
    """Each triangle split n x n (linear; the points on a shared edge shared). Attributes interpolated."""
    if n <= 1:
        return P, A, T
    keys, rows = {}, []                                        # point key -> new index; (vertex ids, weights)

    def point(t, i, j):
        k = (n - i - j, i, j)
        corners = [(c, w) for c, w in zip(t, k) if w]
        if len(corners) == 1:
            key = ('v', corners[0][0])
        elif len(corners) == 2:
            (a, wa), (b, wb) = sorted(corners)
            key = ('e', a, b, wb)
        else:
            key = ('f', tuple(t), i, j)
        if key not in keys:
            keys[key] = len(rows)
            rows.append(([c for c, _ in corners], [w / n for _, w in corners]))
        return keys[key]
    T2 = []
    for t in T:
        t = tuple(int(x) for x in t)
        idx = {(i, j): point(t, i, j) for i in range(n + 1) for j in range(n + 1 - i)}
        for i in range(n):
            for j in range(n - i):
                T2.append((idx[(i, j)], idx[(i + 1, j)], idx[(i, j + 1)]))
                if i + j < n - 1:
                    T2.append((idx[(i + 1, j)], idx[(i + 1, j + 1)], idx[(i, j + 1)]))

    def mix(X):
        return np.array([sum(w * X[c] for c, w in zip(cs, ws)) for cs, ws in rows])
    return mix(P), [mix(a) for a in A], np.array(T2)


def components(P, T):
    """Each vertex's connected piece (union-find over the triangles)."""
    parent = np.arange(len(P))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for t in T:
        a = find(t[0])
        for b in t[1:]:
            parent[find(b)] = a
    roots = np.array([find(i) for i in range(len(P))])
    return np.unique(roots, return_inverse=True)[1]


def raster(UV, T, W, H):
    """The triangles drawn into a W x H texture (texel centres): each texel's triangle (-1: none) and barycentrics."""
    tid = np.full((H, W), -1)
    bary = np.zeros((H, W, 3))
    X, Y = UV[:, 0] * W - 0.5, UV[:, 1] * H - 0.5
    for k, t in enumerate(T):
        xs, ys = X[t], Y[t]
        x0, x1 = max(int(np.floor(xs.min())), 0), min(int(np.ceil(xs.max())), W - 1)
        y0, y1 = max(int(np.floor(ys.min())), 0), min(int(np.ceil(ys.max())), H - 1)
        if x0 > x1 or y0 > y1:
            continue
        d = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
        if abs(d) < 1e-12:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        a = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / d
        b = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / d
        m = (a >= -1e-6) & (b >= -1e-6) & (1 - a - b >= -1e-6)
        tid[y0:y1 + 1, x0:x1 + 1][m] = k
        bary[y0:y1 + 1, x0:x1 + 1][m] = np.stack([a[m], b[m], 1 - a[m] - b[m]], -1)
    return tid, bary


def cross_perimeter(P, y, band=0.8):
    """The snake's cross-section perimeter (its own units) at height y, from the vertices within `band`."""
    m = np.abs(P[:, 1] - y) < band
    if m.sum() < 6:
        return np.nan
    q = P[m][:, [0, 2]]
    c = q.mean(0)
    ring = q[np.argsort(np.arctan2(q[:, 1] - c[1], q[:, 0] - c[0]))]
    return float(np.linalg.norm(np.diff(np.vstack([ring, ring[:1]]), axis=0), axis=1).sum())


def texel_sizes(P, UV, T, W, H, lay):
    """World units per texel along u and along v, per triangle (the snake's own units x the layout's scale)."""
    e1, e2 = P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]
    a1, a2 = UV[T[:, 1]] - UV[T[:, 0]], UV[T[:, 2]] - UV[T[:, 0]]
    det = a1[:, 0] * a2[:, 1] - a2[:, 0] * a1[:, 1]
    det = np.where(np.abs(det) < 1e-12, 1e-12, det)
    dpdu = (e1 * a2[:, 1:2] - e2 * a1[:, 1:2]) / det[:, None]
    dpdv = (e2 * a1[:, 0:1] - e1 * a2[:, 0:1]) / det[:, None]
    sg = lay.sigma(P[T][:, :, 1].mean(1))
    return np.linalg.norm(dpdu, axis=1) * sg / W, np.linalg.norm(dpdv, axis=1) * sg / H


def _neighbours(a, dy, dx):
    """a shifted by (dy, dx), edges repeated."""
    out = a.copy()
    H, W = a.shape[:2]
    out[max(dy, 0):H + min(dy, 0), max(dx, 0):W + min(dx, 0)] = a[max(-dy, 0):H + min(-dy, 0), max(-dx, 0):W + min(-dx, 0)]
    return out


def grow_into(hit, arrays, n):
    """Each array's values at `hit` copied out into the texels around it, n texels deep (in place, hit too)."""
    for _ in range(n):
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            src = _neighbours(hit, dy, dx)
            new = src & ~hit
            for a in arrays:
                a[new] = _neighbours(a, dy, dx)[new]
            hit |= new


def grow_mask(mask, n):
    mask = mask.copy()
    for _ in range(n):
        mask |= _neighbours(mask, 0, 1) | _neighbours(mask, 0, -1) | _neighbours(mask, 1, 0) | _neighbours(mask, -1, 0)
    return mask


def scale_textures(out_root, lay, metal, name):
    """A snake's own set (<name>_d / _n / _m): the blade's metal with Argent Verdict's scale mail (fist_tex's
    'mail': staggered rows of overlapping round scales, each rising to its free edge, its rim dipped all round),
    laid in world units on the snake as `lay` lays it: along its length by the layout's own arc length (the body is
    compressed or stretched along the path, so a grid in the texture's own units would squash), round it by each
    ring's circumference (the rattlesnake's skin UVs: u along the body, head at u ~0, tail at u ~1; v round it). Free
    edges toward the tail. The head (its UV islands, rasterised) stays smooth; the scales fade in over the neck.
    Returns the row pitch (world units) and the share of texels carrying scales."""
    P, N, UV, T = snake._SOURCE['raw'][:4]
    H = SCALE_TEX[1]
    diffuse, env, spec = metal
    pitch = SCALE_PITCH * lay.sigma_body
    # u -> the snake's height y -> arc length on the path. The body is rings of 11 vertices (y 2.3 apart): each ring's
    # height and its median u, joined linearly (and carried on linearly past both end rings). Binned medians snapped to
    # the rings' heights, so every third bin repeated its neighbour's: a flat step in y over 60 texels, where the rows
    # stretched into long pills (worst on the neck, whose scales are biggest; it shows on top since the neck lies on
    # the grip's face)
    body = P[:, 1] < snake.HEAD_Y - 1
    order = np.argsort(-P[body, 1])
    y_s, u_s = P[body, 1][order], UV[body, 0][order]
    rings = np.split(np.arange(len(y_s)), np.where(np.diff(y_s) < -0.3)[0] + 1)
    yb = np.array([y_s[g].mean() for g in rings])
    ub = np.array([np.median(u_s[g]) for g in rings])
    assert len(rings) > 60 and (np.diff(ub) > 0).all(), ('the body rings are not in order along u', len(rings))

    def y_of_u(us):
        y = np.interp(us, ub, yb)
        lo, hi = us < ub[0], us > ub[-1]
        y[lo] = yb[0] + (us[lo] - ub[0]) * (yb[1] - yb[0]) / (ub[1] - ub[0])
        y[hi] = yb[-1] + (us[hi] - ub[-1]) * (yb[-1] - yb[-2]) / (ub[-1] - ub[-2])
        return y
    for W in SCALE_TEX[0]:                                     # the narrowest width giving every row its texels
        us = (np.arange(W) + 0.5) / W
        ycol = y_of_u(us)
        scol = lay.u_of_y(ycol)                                # world units from the snout
        body_cols = (ycol < snake.HEAD_Y - 2) & (ycol > snake.TAIL_Y + 20)
        px_row = pitch / np.gradient(scol)[body_cols].max()     # texels per row where the rows are thinnest
        if px_row >= SCALE_MIN_TEXELS:
            break
    # round the body: world units per v at each u (ring perimeter in snake units x its scale / its v span)
    kcol = np.empty(W)
    vmid = np.empty(W)
    circ = np.full(W, np.nan)                                  # the ring's circumference, world units
    for i, y in enumerate(ycol):
        m = body & (np.abs(P[:, 1] - y) < 1.2)
        if m.sum() < 4:
            kcol[i], vmid[i] = np.nan, 0.5
            continue
        q = P[m][:, [0, 2]]
        c = q.mean(0)
        order = np.argsort(np.arctan2(q[:, 1] - c[1], q[:, 0] - c[0]))
        ring = q[order]
        perim = np.linalg.norm(np.diff(np.vstack([ring, ring[:1]]), axis=0), axis=1).sum()
        span = UV[m, 1].max() - UV[m, 1].min()
        circ[i] = perim * lay.sigma(np.array([y]))[0]
        kcol[i] = circ[i] / max(span, 1e-3)
        vmid[i] = (UV[m, 1].max() + UV[m, 1].min()) / 2
    good = np.isfinite(kcol)
    kcol = np.interp(np.arange(W), np.where(good)[0], kcol[good])
    vs = (np.arange(H) + 0.5) / H
    S = np.repeat(scol[None, :], H, 0)                         # (H, W): along, world units
    C = (vs[:, None] - vmid[None, :]) * kcol[None, :]          # round, world units
    DU = np.repeat(np.maximum(np.gradient(scol), 1e-4)[None, :], H, 0)   # world units per texel along u, round v
    assert (np.gradient(scol) >= -1e-9).all(), 'arc length must not fall along u'
    DV = np.repeat((kcol / H)[None, :], H, 0)
    # the head (curator: "add scales ... to the ouroboros snake head and the pommel snake head"): its UV islands lie
    # apart from the body's strip (the skull from above, the lower jaw's halves beside it), so its lattice comes from
    # the surface: each head texel's point on the snake, along = the layout's arc length at its height (as the body),
    # round = its angle from the back x the cross-section's mean radius there; texel sizes from each triangle
    comp = components(P, T)
    main = np.bincount(comp).argmax()
    tri_main = comp[T[:, 0]] == main
    head_t = np.where(tri_main & (P[T][:, :, 1].mean(1) > snake.HEAD_Y - 0.5))[0]
    mouth_t = np.where(~tri_main)[0]                           # the mouth's floor: its own little island
    tid, bary = raster(UV, T[head_t], W, H)
    hit = tid >= 0
    q = (bary[hit][:, :, None] * P[T[head_t][tid[hit]]]).sum(1)   # the texels' points on the snake
    ygrid = np.linspace(snake.HEAD_Y - 3, snake.SNOUT_Y, 80)
    rbar = np.array([cross_perimeter(P[comp == main], y) for y in ygrid]) / (2 * np.pi)
    ok = np.isfinite(rbar)
    rbar = np.interp(ygrid, ygrid[ok], rbar[ok])
    S[hit] = lay.u_of_y(q[:, 1])
    C[hit] = np.arctan2(q[:, 0] - snake.CX, q[:, 2] - snake.CZ) * np.interp(q[:, 1], ygrid, rbar) * lay.sigma(q[:, 1])
    du_t, dv_t = texel_sizes(P, UV, T[head_t], W, H, lay)
    DU[hit], DV[hit] = du_t[tid[hit]], dv_t[tid[hit]]
    grow_into(hit, (S, C, DU, DV), SCALE_GUTTER)             # the islands' gutters carry their own lattice (mips)
    mtid, _ = raster(UV, T[mouth_t], W, H)
    mouth = grow_mask(mtid >= 0, SCALE_GUTTER)
    colw = 2 * pitch
    half = colw / 2
    y0 = (pitch ** 2 - half ** 2) / (2 * pitch)
    rc = SCALE_MAIL[0] * max(np.sqrt(half ** 2 + y0 ** 2), pitch)
    col = C / colw
    jb = np.floor(S / pitch).astype(int)
    rise = np.full(S.shape, -1.0)
    ringd = np.zeros(S.shape)
    for dj in (0, 1):                                          # the row nearer the head lies on top: free edges
        j = jb + dj                                            # toward the tail (growing s)
        off = 0.5 * (j % 2)
        dx = (col - (np.floor(col - off) + 0.5 + off)) * colw
        dy = S - j * pitch
        d = np.hypot(dx, dy)
        take = (d < rc) & (rise < 0)
        rise = np.where(take, np.clip(dy / rc, 0, 1), rise)       # rising toward its free edge
        ringd = np.where(take, d / rc, ringd)
    rise = np.clip(rise, 0, 1)
    rim = snake.smoothstep(0.84, 1.0, ringd)
    wsc = np.where(mouth, 0.0, 1.0)                            # scales everywhere but inside the mouth
    hgt = SCALE_MAIL[1] * pitch * (0.45 + 0.55 * rise) * (1 - rim) * wsc
    # normal map: slopes per world unit along (u, red) and round (v, green), as Argent Verdict's (DirectX)
    gy, gx = np.gradient(hgt)
    nx, ny = -gx / DU, -gy / np.maximum(DV, 1e-6)
    ln = np.sqrt(nx * nx + ny * ny + 1)
    tone = (-0.08 + 0.12 * rise - 0.16 * rim) * wsc
    shade = np.clip(1 + 1.6 * tone, 0, 1.3) * np.where(mouth, MOUTH_DARK[0], 1.0)
    d_rgb = np.clip(shade[..., None] * np.array(diffuse)[None, None, :], 0, 1)
    refl = np.clip(1 + 1.2 * tone, 0.4, 1.2) * np.where(mouth, MOUTH_DARK[1], 1.0)
    nrm = np.stack([nx / ln * 0.5 + 0.5, ny / ln * 0.5 + 0.5, 1 / ln * 0.5 + 0.5, np.clip(spec * refl, 0, 1)], -1)
    write = lambda a, name, fmt: sr.write_texture(a.astype(np.float32), os.path.join(out_root, *(TEX_DIR + name).split('/')), fmt)  # noqa: E731
    write(d_rgb, name + '_d.dds', 'BC7_UNORM')
    write(nrm, name + '_n.dds', 'BC7_UNORM')
    write(np.repeat(np.clip(env * refl, 0, 1)[..., None], 3, -1), name + '_m.dds', 'BC1_UNORM')
    share = float(hit.mean())
    rounds = np.nanmedian(circ[body_cols]) / colw
    px_col = np.min(colw / (kcol[body_cols] / H))               # texels per column round
    assert px_row >= SCALE_MIN_TEXELS and px_col >= SCALE_MIN_TEXELS, ('scales too fine', W, px_row, px_col)
    print(f'  {name} textures: {W}x{H}, scale rows {pitch:.3f} apart (world units), {colw:.3f} wide (~{rounds:.1f} '
          f'round the body), {px_row:.1f}+ texels a row, {px_col:.1f}+ a '
          f'column; the head\'s islands {share:.0%} of the texture, the mouth dark')
    return pitch, share


def grip_angle(P):
    """Each point's angle round the handle's axis."""
    return np.arctan2(P[:, 2], P[:, 0] - snake.AXIS_X)


def mirror_grip_ends(P, UV, T):
    """The grip's two ends wear the leather next to them: each vertex past GRIP_MIRROR takes the UV of the point at
    its own angle mirrored back across that height, found in its own UV piece of billyro's layout (no UV seam
    crossed), so the leather runs on without a seam. The caps (inside head and shaft) keep theirs. Returns the UVs
    and how many moved."""
    comp = components(P, T)                                    # by index: billyro's UV pieces, the caps apart
    side = np.ptp(P[T][:, :, 1], axis=1) > 1e-3
    main = np.bincount(comp[T[side][:, 0]]).argmax()           # his wrap from y -8.12 to 9.54 (two thin end strips
    tris = T[side & (comp[T[:, 0]] == main)]                   # and the caps are pieces of their own): every
    ang = grip_angle(P)                                        # mirrored point is looked up in it
    UV0, UV = UV, UV.copy()
    moved = 0
    targets = [(i, y0) for sign, y0 in ((-1, GRIP_MIRROR[0]), (1, GRIP_MIRROR[1]))
               for i in np.where(((P[:, 1] - y0) * sign > 0) & np.isin(np.arange(len(P)), T[side]))[0]]
    for cut in (0.0, np.pi):                                   # the wrap: angles cut on one side, then the other;
        th = (ang - cut + np.pi) % (2 * np.pi) - np.pi         # triangles across the cut left out
        ok = np.ptp(th[tris], axis=1) < np.pi
        tt = tris[ok]
        A, B, C = [np.stack([th[tt[:, k]], P[tt[:, k], 1]], 1) for k in range(3)]
        d = (B[:, 1] - C[:, 1]) * (A[:, 0] - C[:, 0]) + (C[:, 0] - B[:, 0]) * (A[:, 1] - C[:, 1])
        d = np.where(np.abs(d) < 1e-14, 1e-14, d)
        left = []
        for i, y0 in targets:
            q = np.array([th[i], 2 * y0 - P[i, 1]])
            l0 = ((B[:, 1] - C[:, 1]) * (q[0] - C[:, 0]) + (C[:, 0] - B[:, 0]) * (q[1] - C[:, 1])) / d
            l1 = ((C[:, 1] - A[:, 1]) * (q[0] - C[:, 0]) + (A[:, 0] - C[:, 0]) * (q[1] - C[:, 1])) / d
            l2 = 1 - l0 - l1
            k = np.where((l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6))[0]
            if not len(k):
                left.append((i, y0))
                continue
            k = k[0]
            UV[i] = l0[k] * UV0[tt[k, 0]] + l1[k] * UV0[tt[k, 1]] + l2[k] * UV0[tt[k, 2]]
            moved += 1
        targets = left
    assert not targets, f'{len(targets)} grip end vertices found no leather to mirror'
    return UV, moved


def grip_texture(out_root, uv, T, P):
    """billyro's diffuse with the texels under the grip's UVs recoloured very dark purple. Returns the leather's texels
    and the brightness of the grip's ends against its middle (sampled through the final UVs: mirror_grip_ends)."""
    d = billyro_texture('axe.dds')
    H, W = d.shape[:2]
    sel = uv_mask(uv, T, W, H).astype(np.float32)
    rgb = sr.recolor_leather(d, sel, LEATHER, LEATHER_CONTRAST, 'whisper grip')
    out = np.concatenate([rgb, d[..., 3:4]], -1) if d.shape[-1] == 4 else rgb
    # the ends now match the middle: the written colours sampled over the side triangles' surfaces, by height
    side = T[np.ptp(P[T][:, :, 1], axis=1) > 1e-3]
    w = np.random.default_rng(3).dirichlet((1, 1, 1), 24)
    y = np.einsum('sk,tk->ts', w, P[side][:, :, 1]).ravel()
    u = np.einsum('sk,tkc->tsc', w, uv[side]).reshape(-1, 2)
    lum = rgb[np.clip((u[:, 1] * H).astype(int), 0, H - 1), np.clip((u[:, 0] * W).astype(int), 0, W - 1)] @ \
        np.array([0.299, 0.587, 0.114])
    mid = np.median(lum[(y > GRIP_EVEN[0]) & (y < GRIP_EVEN[1])])
    low, top = np.median(lum[y < GRIP_MIRROR[0] - 0.2]) / mid, np.median(lum[y > GRIP_MIRROR[1] + 0.2]) / mid
    assert 0.85 < low < 1.2 and 0.85 < top < 1.2, ('the grip ends still differ', low, top)
    sr.write_texture(out.astype(np.float32), os.path.join(out_root, *(TEX_DIR + 'grip_d.dds').split('/')), 'BC7_UNORM')
    return int(sel.sum()), low, top


def load_gem():
    d, listing = _bsa.listing(os.path.join(DATA, GEM_BSA))
    raw = _bsa.read(d, listing[GEM_KEY])
    g = nifse.Nif(raw)
    k = g.find('BSTriShape')
    assert len(k) == 1, len(k)
    s = nifse.read_trishape(g.blocks[k[0]])
    t, R, sc = nifse.transform(g.blocks[k[0]])
    assert len(s['tris']) == 62, len(s['tris'])               # vanilla's black soul gem
    return s, (t, R, sc)


def place_gem(s, xf, top, out_dir):
    """The gem's pointed lower part (its long axis z, the fine point at -z): clipped GEM_LENGTH / GEM_SCALE up from
    the point, the slice sealed with a flat cap, at GEM_SCALE, centred on its own axis: the slice's centre at `top`,
    the point along `out_dir`; its x along the axe's x (a proper rotation, so the winding holds). Returns positions,
    normals, tangents, bitangents, UVs and triangles in axe coordinates."""
    t, R, sc = xf
    P = s['pos'] * sc @ R.T + t
    rot = lambda v: v @ R.T  # noqa: E731
    N, Tg, Bt = rot(s['normal']), rot(s['tangent']), rot(s['bitangent'])
    wind = winding_outward(P, N, s['tris'])
    zc = P[:, 2].min() + GEM_LENGTH / GEM_SCALE
    assert zc < P[:, 2].max(), 'GEM_LENGTH longer than the gem'
    C0 = np.zeros((len(P), 4))
    P, (N, Tg, Bt, UV, _), T, edges = clip_keep(P, [N, Tg, Bt, s['uv'].astype(float), C0], s['tris'], P[:, 2] - zc)
    assert edges, 'the slice missed the gem'
    P, A, T = cap(P, [N, Tg, Bt, UV, np.zeros((len(P), 4))], T, edges, (0.0, 0.0, 1.0), wind)
    P, (N, Tg, Bt, UV, _), T = compact(P, A, T)
    c = (P.min(0) + P.max(0)) / 2
    Pc = (P - np.array([c[0], c[1], zc])) * GEM_SCALE      # the slice's centre at the origin
    down = snake.nz(np.asarray(out_dir, float))
    ex = np.array([1.0, 0.0, 0.0])
    ex = snake.nz(ex - (ex @ down) * down)
    ez = -down                                             # the gem's +z goes back into the mouth
    ey = np.cross(ez, ex)                                  # (ex, ey, ez) right-handed
    M = np.stack([ex, ey, ez], 1)                          # columns: where the gem's x, y, z go
    assert np.linalg.det(M) > 0.999
    V = Pc @ M.T + np.asarray(top, float)
    return V, snake.nz(N @ M.T), snake.nz(Tg @ M.T), snake.nz(Bt @ M.T), UV, T


def fit_gem_to_mouth(V, N, Tg, Bt, SV, jaw, top, out_dir):
    """The crystal's part between the jaws narrowed to the gap between them. The jaws open in the plane of the head's
    axis and its dorsal direction (axe z); at each height the gap is measured over the crystal's own width (axe x):
    the upper jaw's innermost point (its palate, the largest z among upper-jaw vertices there) and the lower jaw's
    (its floor, the smallest z among lower-jaw vertices). Each crystal vertex's offset from the gap's middle is
    scaled so the crystal's widest point meets both, MOUTH_BITE inside them; below the jaws' tips nothing changes.
    Normals and tangent frames follow the squash (inverse transpose for the normals)."""
    axis = snake.nz(np.asarray(out_dir, float))
    assert abs(axis @ np.array([0.0, -1.0, 0.0])) > 0.999, axis       # the head hangs straight down the axis
    x0, x1 = V[:, 0].min(), V[:, 0].max()
    near = (SV[:, 0] > x0) & (SV[:, 0] < x1) & (SV[:, 1] < top[1] + 0.6) & (SV[:, 1] > V[:, 1].min())
    up, lo = near & (jaw < 0.25), near & (jaw > 0.75)
    tip = max(SV[up, 1].min(), SV[lo, 1].min())                       # below this the jaws no longer close round it
    half = np.abs(V[:, 2] - top[2]).max()
    ys = np.arange(tip, V[:, 1].max() + 0.1, 0.05)
    zu = np.array([SV[up & (np.abs(SV[:, 1] - y) < 0.08), 2].max(initial=-np.inf) for y in ys])
    zl = np.array([SV[lo & (np.abs(SV[:, 1] - y) < 0.08), 2].min(initial=np.inf) for y in ys])
    ok = np.isfinite(zu) & np.isfinite(zl)
    ys, zu, zl = ys[ok], zu[ok], zl[ok]
    zl = np.maximum(zl, zu)                                           # closed at the hinge
    V, N, Tg, Bt = V.copy(), N.copy(), Tg.copy(), Bt.copy()
    m = V[:, 1] > tip
    mid = np.interp(V[m, 1], ys, (zu + zl) / 2)
    gap = np.interp(V[m, 1], ys, (zl - zu) / 2) + MOUTH_BITE
    k = np.clip(gap / half, 0.04, 1.0)
    # blend in over the top 0.15 below the tips so the facets do not crease where the narrowing starts
    w = np.clip((V[m, 1] - tip) / 0.15, 0, 1)
    k = 1 + (k - 1) * w
    cz = top[2] + (mid - top[2]) * w
    V[m, 2] = cz + (V[m, 2] - top[2]) * k
    N[m, 2] /= k
    Tg[m, 2] *= k
    Bt[m, 2] *= k
    return V, snake.nz(N), snake.nz(Tg), snake.nz(Bt), tip, float(np.interp(tip + 0.6, ys, zl - zu))


def gem_textures(out_root):
    raw_d, src_d = vanilla_texture(GEM_D)
    raw_n, src_n = vanilla_texture(GEM_N)
    gem = sr.load_image(raw_d)[..., :3]
    lum = gem.mean(-1)
    lum = (lum - lum.min()) / (lum.max() - lum.min() + 1e-9)
    col = np.clip((GEM_SPREAD[0] + GEM_SPREAD[1] * lum)[..., None] * np.array(AMETHYST), 0, 1).astype(np.float32)
    sr.write_texture(col, os.path.join(out_root, *(TEX_DIR + GEM_TEX[0]).split('/')), 'BC7_UNORM')
    sr.write_texture(np.full(gem.shape, GEM_ENV, np.float32), os.path.join(out_root, *(TEX_DIR + GEM_TEX[5]).split('/')),
                     'BC1_UNORM')
    dst = os.path.join(out_root, *(TEX_DIR + GEM_TEX[1]).split('/'))
    open(dst, 'wb').write(raw_n)
    print(f'  amethyst textures: from {GEM_D} ({src_d}) recoloured {AMETHYST}, normal map copied from {GEM_N} ({src_n})')


def langet_half(x):
    """The langet's half-width at x: a rounded tip (radius tip_half) widening smoothly to root_half at the socket."""
    L = LANGET
    c = L['tip_x'] + L['tip_half']
    body = L['tip_half'] + (L['root_half'] - L['tip_half']) * snake.smoothstep(c, L['root_x'], x)
    tip = np.sqrt(np.clip(L['tip_half'] ** 2 - (c - x) ** 2, 0, None))
    return np.where(x < c, tip, body)


def langet_height(x, y, y_mid, root_h):
    """The langet's height over the blade face at (x, y): root_h at the socket (per face: socket_fit) sloping to
    tip_h, rounded down over `bevel` at its edges (to below the face: the skirt), negative outside it."""
    L = LANGET
    H = L['tip_h'] + (root_h - L['tip_h']) * snake.smoothstep(L['tip_x'], L['root_x'], x)
    edge = langet_half(x) - np.abs(y - y_mid)                 # distance in from its edge, across
    edge = np.minimum(edge, x - L['tip_x'])
    t = np.clip(edge / L['bevel'], 0, 1)
    return H * np.sin(0.5 * np.pi * t) - L['skirt'] * (1 - t)


def socket_fit(MV, MN, MT, s_blade):
    """Where the langets meet the socket (curator, on the first langets: "It doesnt look aligned": they were centred
    on the nominal socket middle y 28.6 and 3.8 tall, so their top edge met the socket below its top corner and their
    bottom ran into its pointed V). The socket's flat blade-side face (the Noble vertices at its x, SOCKET_FACE_X) runs
    y 27.0 .. 31.0: the langet's root spans it (LANGET['root_half'] set here, the inset left at its ends) and is
    centred on it (y 29.0, which is also the middle blade snake's snout). The socket is not symmetric front to back
    (its +z panel stands higher off the blade than its -z one), so each face's root height is the socket's own outer
    surface over the blade there, less LANGET_TUCK: the langet runs on under the socket's chamfer. Returns the middle
    and {side: root height}."""
    at = MV[np.abs(MV[:, 0] - noble.SOCKET_FACE_X) < 0.02]
    at = at[(at[:, 1] > 25) & (at[:, 1] < 33)]
    y_lo, y_hi = at[:, 1].min(), at[:, 1].max()
    assert 3.5 < y_hi - y_lo < 5.0, ('the socket face', y_lo, y_hi)
    y_mid = (y_lo + y_hi) / 2
    LANGET['root_half'] = (y_hi - y_lo) / 2 - LANGET_INSET
    c = MV[MT].mean(1)
    block = MT[(c[:, 1] > 25) & (c[:, 1] < 33) & (c[:, 0] < 2.5)]
    vs = np.unique(block)
    remap = np.full(len(MV), -1)
    remap[vs] = np.arange(len(vs))
    sock = {'pos': MV[vs], 'tris': remap[block], 'normal': MN[vs]}
    roots = {}
    for side in (1, -1):
        outer = face_height(sock, side, step=0.02)
        blade = face_height(s_blade, side)
        q = np.array([[LANGET['root_x'], y] for y in np.linspace(y_mid - 1.0, y_mid + 1.0, 9)])
        roots[side] = float((side * (outer(q) - blade(q))).min() - LANGET_TUCK)
        assert 0.2 < roots[side] < 1.2, ('the socket over the blade', side, roots[side])
    print(f'  socket face y {y_lo:.2f} .. {y_hi:.2f} (middle {y_mid:.2f}); langet roots {LANGET["root_half"] * 2:.2f} '
          f'tall, {roots[1]:.3f} (+z) / {roots[-1]:.3f} (-z) over the blade')
    return y_mid, roots


def panel_uv(MV, MUV, MT, side, xy, y_mid):
    """UVs for points on a langet: one linear projection (no seams) into the strip of the Noble texture the socket's
    own side facets on that face sample (their largest group), at the facets' own texel density and orientation,
    centred on it: the langet wears the socket's steel. (Its side is several facets mapped to scattered strips, so
    mirroring them put seams on the langet.)"""
    fn = np.cross(MV[MT[:, 1]] - MV[MT[:, 0]], MV[MT[:, 2]] - MV[MT[:, 0]])
    fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
    c = MV[MT].mean(1)
    tri = MT[(fn[:, 2] * side > 0.9) & (c[:, 1] > 24) & (c[:, 1] < 33) & (c[:, 0] > -0.6) & (c[:, 0] < 3.2)]
    area = np.abs(np.cross(MV[tri[:, 1]] - MV[tri[:, 0]], MV[tri[:, 2]] - MV[tri[:, 0]])[:, 2]) / 2
    # the facets' strips: triangles grouped by UV position (within 0.05 of each other, chained); the strip with the
    # largest UV box (the socket's main faces: ~0.13 x 0.09; the others are 0.03 wide)
    cen = MUV[tri].mean(1)
    grp = np.arange(len(tri))
    for _ in range(len(tri)):
        changed = False
        for i in range(len(tri)):
            j = np.where(np.linalg.norm(cen - cen[i], axis=1) < 0.05)[0]
            g = grp[j].min()
            if (grp[j] != g).any():
                grp[j] = g
                changed = True
        if not changed:
            break
    boxes = {g: (MUV[tri[grp == g]].reshape(-1, 2).min(0), MUV[tri[grp == g]].reshape(-1, 2).max(0)) for g in set(grp)}
    g = max(boxes, key=lambda k: np.prod(boxes[k][1] - boxes[k][0]))
    lo, hi = boxes[g]
    sub = np.where(grp == g)[0]
    big = tri[sub[np.argmax(area[sub])]]
    M = np.array([MV[big[1], :2] - MV[big[0], :2], MV[big[2], :2] - MV[big[0], :2]]).T
    A = np.array([MUV[big[1]] - MUV[big[0]], MUV[big[2]] - MUV[big[0]]]).T
    J = A @ np.linalg.inv(M)                                   # dUV / d(x, y) on the socket's face
    cx = (LANGET['tip_x'] + LANGET['root_x']) / 2
    uv = (lo + hi) / 2 + (np.stack([-(xy[:, 0] - cx), xy[:, 1] - y_mid], 1) @ J.T)   # x mirrored: out of the socket
    span = uv.max(0) - uv.min(0)
    assert (span <= (hi - lo) + 0.02).all(), ('the langet overruns the socket\'s strip', span, hi - lo)
    return uv


def langets(s_blade, MV, MUV, MT, y_mid, roots):
    """The two langets (curator, asked how to blend the Noble socket into billyro's blade, picked "Langets": "two
    tapered steel straps run from the socket onto each blade face, riveted, like a real axe head held in its socket.
    The snakes' root comes out from under their ends"). Each is a tongue on its blade face (langet_half: a rounded
    tip widening to the socket) whose height (langet_height) ramps from the socket's chamfer down to its tip and
    rounds off at its edges into the blade; a structured mesh (along x, across t). UVs from the socket's own side
    panel, mirrored (panel_uv). Returns positions, normals, tangents, bitangents, UVs, triangles, and the face
    height functions."""
    L = LANGET
    s_ = np.linspace(0, 1, L['rows'])
    xs = L['tip_x'] + 0.004 + (L['root_x'] - L['tip_x'] - 0.004) * (1 - np.cos(0.5 * np.pi * s_))   # dense at the tip
    k = np.linspace(-1, 1, L['cols'])
    ts = np.sign(k) * np.sin(0.5 * np.pi * np.abs(k))          # dense at the edges
    out = []
    faces = {}
    for side in (1, -1):
        face = face_height(s_blade, side)
        faces[side] = face
        X, Tt = np.meshgrid(xs, ts, indexing='ij')
        Y = y_mid + Tt * langet_half(X)
        h = langet_height(X, Y, y_mid, roots[side])
        xy = np.stack([X.ravel(), Y.ravel()], 1)
        Z = face(xy) + side * h.ravel()
        P = np.column_stack([xy, Z])
        nr, nc = X.shape
        idx = np.arange(nr * nc).reshape(nr, nc)
        T = []
        for i in range(nr - 1):
            for j in range(nc - 1):
                a, b, c, d = idx[i, j], idx[i + 1, j], idx[i + 1, j + 1], idx[i, j + 1]
                T += [(a, b, c), (a, c, d)]
        T = np.array(T)
        fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
        if (fn[:, 2] * side).sum() < 0:
            T = T[:, [0, 2, 1]]
            fn = -fn
        N = np.zeros_like(P)
        for c_ in range(3):
            np.add.at(N, T[:, c_], fn)
        N = snake.nz(N)
        UV = panel_uv(MV, MUV, MT, 1, xy, y_mid)               # both from the +z face's strip (the -z one carries
                                                                # engraved arcs): the two langets alike
        out.append((P, N, UV, T))
    P = np.vstack([o[0] for o in out])
    N = np.vstack([o[1] for o in out])
    UV = np.vstack([o[2] for o in out])
    T = np.vstack([out[0][3], out[1][3] + len(out[0][0])])
    Tg, Bt = snake.tangents(P, N, UV, T)
    return P, N, Tg, Bt, UV, T, faces


def langet_rivets(s_blade, faces, y_mid, roots):
    """billyro's own rivet head (the middle one, hidden in the socket since the blade moved), copied onto each
    langet at LANGET_RIVET, scaled, turned to the langet's surface and seated on it. Positions, normals, tangents,
    bitangents, UVs, triangles."""
    P, T = s_blade['pos'], s_blade['tris']
    isl = islands(P, T)
    out = []
    for side in (1, -1):
        best = None
        for r in np.unique(isl):
            vs = np.unique(T[isl == r])
            Q = P[vs]
            lo, hi = Q.min(0), Q.max(0)
            if hi[0] - lo[0] < 1.2 and hi[1] - lo[1] < 1.2 and 0.8 < np.abs(Q[:, 2]).max() < 1.0 and \
                    np.sign(Q[:, 2].mean()) == side:
                dist = np.linalg.norm((lo + hi)[:2] / 2 - (np.array(BLADE_RIVET_SRC)))
                if best is None or dist < best[0]:
                    best = (dist, r, vs)
        assert best is not None and best[0] < 0.3, ('billyro\'s middle rivet', side, best and best[0])
        _, r, vs = best
        tris = T[isl == r]
        remap = {v: i for i, v in enumerate(vs)}
        tt = np.vectorize(remap.get)(tris)
        Q = P[vs]
        base = np.array([(Q[:, 0].min() + Q[:, 0].max()) / 2, (Q[:, 1].min() + Q[:, 1].max()) / 2,
                         Q[:, 2].min() if side > 0 else Q[:, 2].max()])   # its underside (the face height there
                                                                          # is the rivet's own top)
        x0, sc, sh = LANGET_RIVET
        at = np.array([[x0, y_mid]])
        e = 0.02
        hz = lambda xy: faces[side](xy) + side * langet_height(xy[:, 0], xy[:, 1], y_mid, roots[side])   # noqa: E731
        top = np.array([x0, y_mid, hz(at)[0]])
        gx = (hz(at + [[e, 0]])[0] - hz(at - [[e, 0]])[0]) / (2 * e)
        gy = (hz(at + [[0, e]])[0] - hz(at - [[0, e]])[0]) / (2 * e)
        n = side * snake.nz(np.array([-gx, -gy, 1.0]))          # the langet's outward normal there
        up = np.array([0.0, 0.0, float(side)])                  # the rivet's own up, turned onto n
        v = np.cross(up, n)
        s_, c_ = np.linalg.norm(v), up @ n
        K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
        R = np.eye(3) + K + K @ K * ((1 - c_) / max(s_ ** 2, 1e-12)) if s_ > 1e-9 else np.eye(3)
        Pn = top - n * LANGET_RIVET_SINK + ((Q - base) * np.array([sc, sc, sh])) @ R.T
        out.append((Pn, snake.nz(s_blade['normal'][vs] @ R.T), snake.nz(s_blade['tangent'][vs] @ R.T),
                    snake.nz(s_blade['bitangent'][vs] @ R.T), s_blade['uv'][vs], tt))
    P_ = np.vstack([o[0] for o in out])
    T_ = np.vstack([out[0][5], out[1][5] + len(out[0][0])])
    return (P_, np.vstack([o[1] for o in out]), np.vstack([o[2] for o in out]), np.vstack([o[3] for o in out]),
            np.vstack([o[4] for o in out]), T_)


def icosphere(level=2):
    """A unit icosphere: vertices, triangles (outward winding)."""
    g = (1 + 5 ** 0.5) / 2
    V = [(-1, g, 0), (1, g, 0), (-1, -g, 0), (1, -g, 0), (0, -1, g), (0, 1, g), (0, -1, -g), (0, 1, -g),
         (g, 0, -1), (g, 0, 1), (-g, 0, -1), (-g, 0, 1)]
    V = [np.array(v, float) / np.linalg.norm(v) for v in V]
    F = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6),
         (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10),
         (8, 6, 7), (9, 8, 1)]
    for _ in range(level):
        cache, F2 = {}, []

        def mid(a, b):
            key = (min(a, b), max(a, b))
            if key not in cache:
                m = V[a] + V[b]
                V.append(m / np.linalg.norm(m))
                cache[key] = len(V) - 1
            return cache[key]
        for a, b, c in F:
            ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
            F2 += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
        F = F2
    V, F = np.array(V), np.array(F)
    assert (np.einsum('ij,ij->i', np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]), V[F].mean(1)) > 0).all()
    return V, F


def eye_domes(V, N, UV2, T2, sigma_head):
    """Ruby domes at the painted eyes of a laid snake (its vertices, normals, UVs, triangles): positions, normals,
    UVs, triangles, and each eye's point on the head."""
    S, F = icosphere(2)
    out_P, out_N, out_UV, out_T, points = [], [], [], [], []
    r = EYE_R * sigma_head
    for u, v in EYE_UV:
        a, b, c = UV2[T2[:, 0]], UV2[T2[:, 1]], UV2[T2[:, 2]]
        d = (b[:, 1] - c[:, 1]) * (a[:, 0] - c[:, 0]) + (c[:, 0] - b[:, 0]) * (a[:, 1] - c[:, 1])
        d = np.where(np.abs(d) < 1e-14, 1e-14, d)
        l0 = ((b[:, 1] - c[:, 1]) * (u - c[:, 0]) + (c[:, 0] - b[:, 0]) * (v - c[:, 1])) / d
        l1 = ((c[:, 1] - a[:, 1]) * (u - c[:, 0]) + (a[:, 0] - c[:, 0]) * (v - c[:, 1])) / d
        inside = np.where((l0 >= -1e-6) & (l1 >= -1e-6) & (1 - l0 - l1 >= -1e-6))[0]
        assert len(inside) == 1, ('the eye is not on exactly one triangle', u, v, len(inside))
        k = inside[0]
        w = np.array([l0[k], l1[k], 1 - l0[k] - l1[k]])
        p = w @ V[T2[k]]
        n = snake.nz(w @ N[T2[k]])
        e1 = snake.nz(np.cross(n, [0.0, 1.0, 0.0]) if abs(n[1]) < 0.9 else np.cross(n, [1.0, 0.0, 0.0]))
        e2 = np.cross(n, e1)
        centre = p + n * r * (EYE_PROUD - EYE_FLAT)
        loc = S * np.array([1.0, 1.0, EYE_FLAT])
        out_P.append(centre + r * (loc[:, :1] * e1 + loc[:, 1:2] * e2 + loc[:, 2:3] * n))
        g = S / np.array([1.0, 1.0, EYE_FLAT]) ** 2            # the ellipsoid's normal
        out_N.append(snake.nz(g[:, :1] * e1 + g[:, 1:2] * e2 + g[:, 2:3] * n))
        out_UV.append(np.stack([0.5 + 0.45 * S[:, 0], 0.5 + 0.45 * S[:, 1]], 1))   # facing straight on: the gem's face
        out_T.append(F + sum(len(x) for x in out_P[:-1]))
        points.append(p)
    P_, N_, UV_, T_ = np.vstack(out_P), np.vstack(out_N), np.vstack(out_UV), np.vstack(out_T)
    Tg_, Bt_ = snake.tangents(P_, N_, UV_, T_)
    return P_, N_, Tg_, Bt_, UV_, T_, points


def glow_node(nif, axe_k, node_name, shape_name, V, N, Tg, Bt, uv, T, mult):
    """A glowing copy of a shape (GLOW_LIFT out along its normals) on its own copy of the gem's shader with Own_Emit on
    (emissive GLOW_COLOUR x mult), under a new node at scale 0 (unlit until a script sets its scale to 1). Returns the
    node's and the shape's block indices."""
    k = add_shape(nif, axe_k, shape_name, V + N * GLOW_LIFT, N, Tg, Bt, uv, T, None, GEM_TEX)
    sh = nifse.read_trishape(nif.blocks[k])['shader']
    b = bytearray(nif.blocks[sh])
    assert len(b) in (100, 104) and struct.unpack_from('<I', b, 8)[0] == 0, ('not the SE lighting shader layout', len(b))
    old_mult = struct.unpack_from('<f', b, LSP_EMIT_MULT)[0]
    assert 0.0 <= old_mult <= 10.0, ('the emissive multiple is not where expected', old_mult)
    struct.pack_into('<I', b, LSP_FLAGS1, struct.unpack_from('<I', b, LSP_FLAGS1)[0] | SLSF1_OWN_EMIT)
    struct.pack_into('<3f', b, LSP_EMISSIVE, *GLOW_COLOUR)
    struct.pack_into('<f', b, LSP_EMIT_MULT, mult)
    nif.blocks[sh] = bytes(b)
    root = nif.roots[0]
    _, kids = nifse.node_children(nif.blocks[root])
    node = struct.pack('<iIiI', nif.add_string(node_name), 0, -1, 14) + struct.pack('<3f', 0.0, 0.0, 0.0)
    node += struct.pack('<9f', *np.eye(3).reshape(-1)) + struct.pack('<fi', 0.0, -1)       # scale 0, no collision
    node += struct.pack('<Ii', 1, k) + struct.pack('<I', 0)                                 # the shape; no effects
    n = nif.add_block('NiNode', node)
    nif.blocks[root] = nifse.set_children(nif.blocks[root], [x for x in kids if x != k] + [n])
    return n, k


def add_halo(nif, axe_k, parent, centre):
    """Candlelight's flare sprites as the crystal's halo (see HALO_PARTS), appended under `parent` (the blaze node),
    each on a billboard node at `centre`. Returns {sprite: (billboard node, shape)}."""
    d, listing = _bsa.listing(os.path.join(DATA, HALO_BSA))
    src = nifse.Nif(_bsa.read(d, listing[HALO_KEY]))
    names = {}
    for k in range(len(src.blocks)):
        if src.btype(k) in ('BSTriShape', 'NiBillboardNode'):
            names.setdefault(src.string(struct.unpack_from('<i', src.blocks[k], 0)[0]), k)
    wisps = names['Wisps']
    assert src.btype(wisps) == 'NiBillboardNode'
    o, kids = nifse.node_children(src.blocks[wisps])
    mode = bytes(src.blocks[wisps][o + 4 + 4 * len(kids) + 4:])
    assert len(mode) == 2, ('billboard layout', mode)
    av_flags = struct.unpack_from('<I', nif.blocks[axe_k], nifse.read_trishape(nif.blocks[axe_k])['av']['flags'])[0]
    out = {}
    for part, (size, mult) in HALO_PARTS.items():
        k = names[part]
        assert k in kids, (part, 'is not a sprite of the billboard')
        sh = nifse.read_trishape(src.blocks[k])
        assert sh['skin'] < 0 and src.btype(sh['shader']) == 'BSEffectShaderProperty'
        # its shader: no name, no controller, colour purple at alpha 1, the multiple
        b = bytearray(src.blocks[sh['shader']])
        assert struct.unpack_from('<I', b, 4)[0] == 0, 'extra data on the sprite shader'
        struct.pack_into('<ii', b, 0, -1, 0)
        struct.pack_into('<i', b, 8, -1)
        at = 36
        ln = struct.unpack_from('<I', b, at)[0]
        tex = bytes(b[at + 4:at + 4 + ln]).decode('latin-1')
        at += 4 + ln + 4 + 16
        struct.pack_into('<4f', b, at, *HALO_COLOUR, 1.0)
        struct.pack_into('<ff', b, at + 16, mult, SOFT_DEPTH)
        at += 16 + 4 + 4
        ln = struct.unpack_from('<I', b, at)[0]
        assert at + 4 + ln == len(b), ('not the SE effect shader layout', part)
        shader = nif.add_block('BSEffectShaderProperty', bytes(b))
        al = bytearray(src.blocks[sh['alpha']])
        assert struct.unpack_from('<I', al, 4)[0] == 0
        struct.pack_into('<ii', al, 0, -1, 0)
        struct.pack_into('<i', al, 8, -1)
        alpha = nif.add_block('NiAlphaProperty', bytes(al))
        # its vertex colours purple: the rim's, the centre's (the brightest vertex); alpha kept
        C = sh['color'].copy()
        bright = C[:, :3].astype(int).sum(1)
        rim, mid = HALO_RGB[part]
        C[:, :3] = np.array(rim, np.uint8)
        C[bright == bright.max(), :3] = np.array(mid, np.uint8)
        P = sh['pos']
        across = float(max(np.ptp(P[:, 0]), np.ptp(P[:, 1])))
        xf = nifse.transform(src.blocks[k])
        data = nifse.write_trishape(nif.add_string('ZP_WhisperHalo' + part), av_flags, xf, sh['desc'], P, sh['uv'],
                                    sh['normal'], sh['tangent'], sh['bitangent'], C, sh['tris'], shader, alpha)
        shape_i = nif.add_block('BSTriShape', data)
        node = struct.pack('<iIiI', nif.add_string('ZP_WhisperHaloNode' + part), 0, -1, 14)
        node += struct.pack('<3f', *[float(v) for v in centre]) + struct.pack('<9f', *np.eye(3).reshape(-1))
        node += struct.pack('<fi', size / across, -1) + struct.pack('<Ii', 1, shape_i) + struct.pack('<I', 0) + mode
        bb = nif.add_block('NiBillboardNode', node)
        _, pk = nifse.node_children(nif.blocks[parent])
        nif.blocks[parent] = nifse.set_children(nif.blocks[parent], pk + [bb])
        out[part] = (bb, shape_i, tex)
    return out


def orb_palette(rel):
    """One of the orb's palettes in purple: the game's own gradient (not Glorious Gradients' recolour), its brightness
    (normalised) laid on ORB_RAMP, its alpha kept. Rows and columns keep their places (the shader and vertex colours
    pick the row)."""
    src, raw = sr.winner(TOOLS['modsDir'], [], rel, sr.TEX_BSAS)        # no mods: the game's own archives
    img = sr.load_image(raw).astype(np.float64)
    lum = img[..., 0] * 0.2126 + img[..., 1] * 0.7152 + img[..., 2] * 0.0722
    lum = lum / max(float(lum.max()), 1e-6)
    return np.concatenate([sr.ramp(lum, ORB_RAMP), img[..., 3:4]], -1), src


def add_orb(nif, axe_k, parent, centre, out_root, parts=None, tag='', soft=True, palettes=None):
    """The purple Smite orb (see ORB_PARTS, or `parts`), appended under `parent` (the blaze node), each part on its
    own billboard at `centre`, its shapes and nodes named with `tag` after the part; `soft` False takes the soft fade off
    (SLSF1_SOFT). Writes its palettes, or adds them to `palettes` for the caller to write. Returns {part: (billboard
    node, shape, source texture, palette or '')}."""
    parts = ORB_PARTS if parts is None else parts
    write_now = palettes is None
    palettes = {} if palettes is None else palettes
    src_label, raw = sr.winner(TOOLS['modsDir'], sr.profile_mods(), ORB_SRC)
    assert src_label == ORB_SOURCE, ('Prophecy\'s Smite orb now comes from', src_label)
    src = nifse.Nif(raw)
    names = {}
    for k in range(len(src.blocks)):
        if src.btype(k) in ('BSTriShape', 'NiBillboardNode'):
            names.setdefault(src.string(struct.unpack_from('<i', src.blocks[k], 0)[0]), k)
    bb_src = names[ORB_BILLBOARD]
    assert src.btype(bb_src) == 'NiBillboardNode'
    o, kids = nifse.node_children(src.blocks[bb_src])
    mode = bytes(src.blocks[bb_src][o + 4 + 4 * len(kids) + 4:])
    assert len(mode) == 2, ('billboard layout', mode)
    av_flags = struct.unpack_from('<I', nif.blocks[axe_k], nifse.read_trishape(nif.blocks[axe_k])['av']['flags'])[0]
    out = {}
    for part, (size, mult) in parts.items():
        k = names[part]
        assert k in kids, (part, 'is not under', ORB_BILLBOARD)
        sh = nifse.read_trishape(src.blocks[k])
        assert sh['skin'] < 0 and src.btype(sh['shader']) == 'BSEffectShaderProperty'
        # its shader: no name, no controller (its UV scrolls), the multiple, the soft depth, our purple palette
        b = bytearray(src.blocks[sh['shader']])
        assert struct.unpack_from('<I', b, 4)[0] == 0, 'extra data on the orb shader'
        struct.pack_into('<ii', b, 0, -1, 0)
        struct.pack_into('<i', b, 8, -1)
        f1 = struct.unpack_from('<I', b, 12)[0]
        if not soft:
            assert f1 & SLSF1_SOFT, (part, 'no soft flag to take off')
            struct.pack_into('<I', b, 12, f1 & ~SLSF1_SOFT)
        at = 36
        ln = struct.unpack_from('<I', b, at)[0]
        tex = bytes(b[at + 4:at + 4 + ln]).decode('latin-1')
        at += 4 + ln + 4 + 16
        struct.pack_into('<ff', b, at + 16, mult, SOFT_DEPTH)
        at += 16 + 4 + 4
        ln = struct.unpack_from('<I', b, at)[0]
        assert at + 4 + ln == len(b), ('not the SE effect shader layout', part)
        grey = bytes(b[at + 4:at + 4 + ln]).decode('latin-1')
        assert bool(grey) == bool(f1 & 0x10), (part, 'a palette without its flag, or the flag without one')
        if grey:
            base = os.path.splitext(grey.replace('/', chr(92)).split(chr(92))[-1])[0].lower()
            ours = ORB_PALETTE % base
            if ours not in palettes:
                rel = grey.replace(chr(92), '/').lower()
                palettes[ours] = orb_palette(rel if rel.startswith('textures/') else 'textures/' + rel)
            enc = (TEX_DIR + ours).replace('/', chr(92)).encode('latin-1')
            b = b[:at] + struct.pack('<I', len(enc)) + enc
            grey = enc.decode('latin-1')
        shader = nif.add_block('BSEffectShaderProperty', bytes(b))
        al = bytearray(src.blocks[sh['alpha']])
        assert struct.unpack_from('<I', al, 4)[0] == 0
        struct.pack_into('<ii', al, 0, -1, 0)
        struct.pack_into('<i', al, 8, -1)
        alpha = nif.add_block('NiAlphaProperty', bytes(al))
        C = sh['color'].copy()
        if not grey:                                            # the glow: purple vertex colours, alpha kept
            rim, mid = ORB_FLASH_RGB
            C[:, :3] = np.array(rim, np.uint8)
            C[C[:, 3] == C[:, 3].max(), :3] = np.array(mid, np.uint8)
        P = sh['pos']
        across = float(max(np.ptp(P[:, 0]), np.ptp(P[:, 1])))
        xf = (np.zeros(3), np.eye(3), 1.0)                      # its offset and scale in the orb: the node's size instead
        data = nifse.write_trishape(nif.add_string('ZP_WhisperOrb' + part.split(':')[0] + tag), av_flags, xf, sh['desc'],
                                    P, sh['uv'], sh['normal'], sh['tangent'], sh['bitangent'], C, sh['tris'], shader, alpha)
        shape_i = nif.add_block('BSTriShape', data)
        node = struct.pack('<iIiI', nif.add_string('ZP_WhisperOrbNode' + part.split(':')[0] + tag), 0, -1, 14)
        node += struct.pack('<3f', *[float(v) for v in centre]) + struct.pack('<9f', *np.eye(3).reshape(-1))
        node += struct.pack('<fi', size / across, -1) + struct.pack('<Ii', 1, shape_i) + struct.pack('<I', 0) + mode
        bb = nif.add_block('NiBillboardNode', node)
        _, pk = nifse.node_children(nif.blocks[parent])
        nif.blocks[parent] = nifse.set_children(nif.blocks[parent], pk + [bb])
        out[part] = (bb, shape_i, tex, grey)
    for t in {v[2] for v in out.values()}:                      # the orb's own textures: the game must have them
        sr.winner(TOOLS['modsDir'], sr.profile_mods(), t.replace(chr(92), '/'), sr.TEX_BSAS)
    if write_now:
        write_orb_palettes(palettes, out_root)
    return out


def write_orb_palettes(palettes, out_root):
    for ours, (img, srcname) in palettes.items():
        sr.write_texture(img.astype(np.float32), os.path.join(out_root, *(TEX_DIR + ours).split('/')), 'BC7_UNORM')
        print(f'  orb palette {TEX_DIR + ours}: {img.shape[1]}x{img.shape[0]} from {srcname}, purple')


def add_shape(nif, axe_k, name, V, N, Tg, Bt, uv, T, colour=None, textures=None, vertex_colours=False):
    """A new shape beside the axe: its vertex layout and transform, on its own copy of the axe's shader with the
    given texture slots (slot -> our file name under TEX_DIR) swapped in."""
    s = nifse.read_trishape(nif.blocks[axe_k])
    flags, _, _ = nifse._layout(s['desc'])
    assert np.isfinite(V).all() and np.isfinite(N).all() and np.isfinite(Tg).all() and np.isfinite(Bt).all(), name
    if colour is None:
        colour = np.full((len(V), 4), 255, np.uint8)
    assert flags & nifse.VF_COLORS, 'the axe shape has no vertex colour slot'
    shader = nifse.copy_lighting_shader(nif, nif, s['shader'])
    if vertex_colours:
        b = bytearray(nif.blocks[shader])
        struct.pack_into('<I', b, 20, struct.unpack_from('<I', b, 20)[0] | VERTEX_COLOURS)
        nif.blocks[shader] = bytes(b)
    ts = struct.unpack_from('<i', nif.blocks[shader], nifse.LSP_TEXSET)[0]
    paths = nifse.texture_paths(nif.blocks[ts])
    assert paths[4] == (TEX_DIR + 'nissibeach_e.dds').replace('/', chr(92)), paths[4]   # repointed by main()
    for slot, file in (textures or {}).items():
        paths[slot] = (TEX_DIR + file).replace('/', chr(92))
    nif.blocks[ts] = nifse.texture_set(paths)
    av_flags = struct.unpack_from('<I', nif.blocks[axe_k], s['av']['flags'])[0]
    data = nifse.write_trishape(nif.add_string(name), av_flags, nifse.transform(nif.blocks[axe_k]), s['desc'],
                                V, uv, N, Tg, Bt, colour, T, shader, -1)
    new = nif.add_block('BSTriShape', data)
    root = nif.roots[0]
    _, kids = nifse.node_children(nif.blocks[root])
    nif.blocks[root] = nifse.set_children(nif.blocks[root], kids + [new])
    return new


def set_positions(b, P):
    """An unskinned SE BSTriShape with its vertex positions replaced (full-precision layout: the first 12 bytes of
    each vertex) and its bound sphere refitted; everything else kept."""
    o = nifse.av_fields(b)['end']
    desc = struct.unpack_from('<Q', b, o + 28)[0]
    ntri, nvert, dsize = struct.unpack_from('<HHI', b, o + 36)
    _, _, vs = nifse._layout(desc)
    assert len(P) == nvert, (len(P), nvert)
    out = bytearray(b)
    for i, p in enumerate(np.asarray(P, '<f4')):
        out[o + 44 + i * vs:o + 44 + i * vs + 12] = p.tobytes()
    c = (P.min(0) + P.max(0)) / 2
    struct.pack_into('<4f', out, o, *c, float(np.linalg.norm(P - c, axis=1).max()))
    return bytes(out)


def shift_blade(nif, axe_k):
    """billyro's blade moved BLADE_SHIFT toward the shaft (curator: "bring the blade closer into the shaft"): the
    blade island and its six rivet heads in the axe shape, and both blood-edge shapes. Returns the axe shape re-read."""
    d = np.array([noble.BLADE_SHIFT[0], noble.BLADE_SHIFT[1], 0.0])
    s = nifse.read_trishape(nif.blocks[axe_k])
    P, T = s['pos'], s['tris']                                 # the kept triangles (cut() already applied)
    isl = islands(P, T)
    moved = set()
    for r in np.unique(isl):
        Q = P[np.unique(T[isl == r])]
        lo, hi = Q.min(0), Q.max(0)
        blade = lo[0] < -10
        rivet = hi[0] - lo[0] < 1.2 and hi[1] - lo[1] < 1.2 and hi[0] < 0 and 0.8 < np.abs(Q[:, 2]).max() < 1.0
        if blade or rivet:
            moved |= set(np.unique(T[isl == r]).tolist())
    moved = np.array(sorted(moved))
    assert len(moved) > 100, len(moved)
    P2 = P.copy()
    P2[moved] += d
    nif.blocks[axe_k] = set_positions(nif.blocks[axe_k], P2)
    for k in nif.find('BSTriShape'):
        if name_of(nif, k) in ('EdgeBlood01', 'EdgeBlood'):
            e = nifse.read_trishape(nif.blocks[k])
            nif.blocks[k] = set_positions(nif.blocks[k], e['pos'] + d)
    return nifse.read_trishape(nif.blocks[axe_k]), len(moved)


def noble_textures(out_root, noble_nif, noble_shader, metal):
    """The Noble pieces in the blade's steel (curator: "the shaft from Noble needs retexturing to the same metal as the
    blade", "remove the yellow from the Noble elements"): from the Noble axe's own diffuse and normal map (Pretty
    Enderal Armory's), its gold inlay found by colour (saturated, red over blue) and painted out with the steel round it
    (normalised blur), the rest's brightness kept relative to its median at NOBLE_CONTRAST and put on the blade's
    diffuse, env mask and specular; the normal map's relief kept (engraved steel, no colour). noble_d / _n / _m."""
    from PIL import Image, ImageFilter
    mods = os.path.join(sr.MO2, 'mods')
    ts = struct.unpack_from('<i', noble_nif.blocks[noble_shader], nifse.LSP_TEXSET)[0]
    paths = nifse.texture_paths(noble_nif.blocks[ts])

    def pretty(rel):
        src, raw = sr.winner(mods, sr.profile_mods(), rel.replace(chr(92), '/'))
        assert src == noble.NOBLE_SOURCE, (rel, src)
        return sr.load_image(open(raw, 'rb').read() if isinstance(raw, str) else raw)
    d, n = pretty(paths[0]), pretty(paths[1])
    rgb = d[..., :3]
    mx, mn = rgb.max(-1), rgb.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1e-3)
    gold = np.clip((sat - NOBLE_GOLD[0]) / (NOBLE_GOLD[1] - NOBLE_GOLD[0]), 0, 1) * (rgb[..., 0] - rgb[..., 2] > 0.04)
    lum = rgb @ np.array([0.299, 0.587, 0.114])
    keep = 1 - gold

    def blur(a):                                               # three box passes: about a Gaussian of NOBLE_FILL
        r = max(int(round(NOBLE_FILL)), 1)
        a = a.astype(np.float64)
        for _ in range(3):
            for ax in (0, 1):
                c = np.cumsum(np.pad(a, [(r + 1, r) if i == ax else (0, 0) for i in range(2)], mode='edge'), axis=ax)
                hi = np.take(c, np.arange(2 * r + 1, c.shape[ax]), axis=ax)
                lo = np.take(c, np.arange(0, c.shape[ax] - 2 * r - 1), axis=ax)
                a = (hi - lo) / (2 * r + 1)
        return a
    fill = blur(lum * keep) / np.maximum(blur(keep), 1e-3)
    plain = lum * keep + fill * gold
    steel = plain[(keep > 0.9) & (lum > 0.02)]
    med = float(np.median(steel))
    rel = np.clip(1 + NOBLE_CONTRAST * (plain / med - 1), 0.15, 2.5)
    diffuse, env, spec = metal
    write = lambda a, name, fmt: sr.write_texture(a.astype(np.float32), os.path.join(out_root, *(TEX_DIR + name).split('/')), fmt)  # noqa: E731
    write(np.clip(rel[..., None] * np.array(diffuse)[None, None, :], 0, 1), 'noble_d.dds', 'BC7_UNORM')
    if n.shape[:2] != rel.shape:
        reln = np.asarray(Image.fromarray(rel.astype(np.float32), 'F').resize(n.shape[1::-1], Image.BILINEAR))
    else:
        reln = rel
    nrm = n.copy()
    nrm[..., 3] = np.clip(spec * np.sqrt(reln), 0, 1)
    write(nrm, 'noble_n.dds', 'BC7_UNORM')
    write(np.repeat(np.clip(env * reln, 0, 1)[..., None], 3, -1), 'noble_m.dds', 'BC1_UNORM')
    print(f'  noble textures: {d.shape[1]}x{d.shape[0]} from {paths[0]} (Pretty Enderal Armory); gold inlay on '
          f'{(gold > 0.5).mean():.1%} of the texels painted out; the steel\'s median brightness {med:.3f} -> the blade\'s '
          f'{np.mean(diffuse):.3f}')


def add_noble_shape(nif, axe_k, name, V, N, Tg, Bt, uv, colour, T, src_nif, src_shader):
    """A shape on the axe's vertex layout and transform with a copy of the Noble axe's own shader (its texture paths
    as they are: Pretty Enderal Armory's, which must be in the list)."""
    s = nifse.read_trishape(nif.blocks[axe_k])
    assert np.isfinite(V).all() and np.isfinite(N).all() and np.isfinite(Tg).all() and np.isfinite(Bt).all(), name
    shader = nifse.copy_lighting_shader(nif, src_nif, src_shader)
    av_flags = struct.unpack_from('<I', nif.blocks[axe_k], s['av']['flags'])[0]
    data = nifse.write_trishape(nif.add_string(name), av_flags, nifse.transform(nif.blocks[axe_k]), s['desc'],
                                V, uv, N, Tg, Bt, colour, T, shader, -1)
    new = nif.add_block('BSTriShape', data)
    root = nif.roots[0]
    _, kids = nifse.node_children(nif.blocks[root])
    nif.blocks[root] = nifse.set_children(nif.blocks[root], kids + [new])
    return new


def main():
    out_root = sys.argv[sys.argv.index('--out-root') + 1] if '--out-root' in sys.argv else PATCH_COLLECTION
    assert os.path.isfile(BASE), f'{BASE} missing: run tools/01-convert-stalwart.py first'
    raw = open(BASE, 'rb').read()
    nif = nifse.Nif(raw)
    assert nif.tobytes() == raw, 'nifse round trip failed on the base mesh'
    axe_k, holder_k = shape(nif, AXE_SHAPE), shape(nif, HOLDER_SHAPE)
    s = nifse.read_trishape(nif.blocks[axe_k])
    drop, shaft = cut(s)
    nif.blocks[axe_k] = nifse.set_triangles(nif.blocks[axe_k], s['tris'][~drop])
    s_blade, n_moved = shift_blade(nif, axe_k)
    print(f'  blade moved {noble.BLADE_SHIFT} (toward the shaft, up) ({n_moved} vertices: the blade, its rivets; both blood '
          f'edges)')
    print(f'axe: {drop.sum()} of {len(drop)} triangles cut (the top band and two lower bands, the shaft below y '
          f'{GRIP_TOP} with the knob: {shaft.sum()} shaft triangles become the grip); billyro\'s neck, collar band, '
          f'rivets and upper shaft cut too (the Noble mount replaces them)')

    # the axe's and holder's textures under Whisper's paths
    swaps = {src.lower(): (TEX_DIR + ours).replace('/', chr(92)) for src, (_, ours) in COPIES.items()}
    for k in (axe_k, holder_k):
        print(f'  {name_of(nif, k)} textures: {repoint(nif, nifse.read_trishape(nif.blocks[k])["shader"], swaps)[:6]}')
    # billyro's hip holder (Scb: a leather cup and a belt ring hooked round his neck, drawn only while sheathed) has
    # no neck to hang on now: hidden (NiAVObject flag bit 0)
    hs = nifse.read_trishape(nif.blocks[holder_k])
    b = bytearray(nif.blocks[holder_k])
    struct.pack_into('<I', b, hs['av']['flags'], struct.unpack_from('<I', b, hs['av']['flags'])[0] | 1)
    nif.blocks[holder_k] = bytes(b)
    print('  Scb (hip holder): hidden')

    # ---- the mount: the Noble axe's upper shaft, socket and spike, and the blade's back drawn out to the socket ----
    metal = metal_textures(out_root, s)
    wind = winding_outward(s['pos'], s['normal'], s['tris'])     # the axe's own convention
    MV, MN, MTg, MBt, MUV, MC, MT, noble_nif, noble_shader, noble_pieces = noble.upper_shaft(sr)
    assert winding_outward(MV, MN, MT) == wind, 'the Noble shape winds the other way'
    lean, lz = noble.upper_shaft.lean
    print(f'  the Noble mount leaned {lean:+.2f} deg front to back (centre z {lz:+.3f} at its foot): turned upright onto '
          f'the grip axis')
    noble_textures(out_root, noble_nif, noble_shader, metal)
    add_shape(nif, axe_k, NOBLE_SHAPE, MV, MN, MTg, MBt, MUV, MT, MC, {0: 'noble_d.dds', 1: 'noble_n.dds',
                                                                      5: 'noble_m.dds'})
    # no plate: the moved blade's back runs into the socket over its whole height (its back edge, the blade
    # island's furthest x at each height, inside the socket's blade side)
    sb_P, sb_T = s_blade['pos'], s_blade['tris']
    sb_isl = islands(sb_P, sb_T)
    blade_isl = [r for r in np.unique(sb_isl) if sb_P[np.unique(sb_T[sb_isl == r])][:, 0].min() < -8]
    assert len(blade_isl) == 1, blade_isl
    bt = sb_T[sb_isl == blade_isl[0]]
    ea, eb = sb_P[np.concatenate([bt[:, 0], bt[:, 1], bt[:, 2]])], sb_P[np.concatenate([bt[:, 1], bt[:, 2], bt[:, 0]])]
    sy0, sy1 = noble.SOCKET_Y - 2.3, noble.SOCKET_Y + 2.3
    back = []
    for y in np.linspace(sy0, sy1, 24):                        # the blade's furthest x at each height: edge crossings
        c = (ea[:, 1] - y) * (eb[:, 1] - y) <= 0
        f = (y - ea[c, 1]) / np.where(np.abs(eb[c, 1] - ea[c, 1]) < 1e-9, 1, eb[c, 1] - ea[c, 1])
        back.append(float((ea[c, 0] + (eb[c, 0] - ea[c, 0]) * np.clip(f, 0, 1)).max()))
    assert min(back) >= noble.SOCKET_FACE_X + 0.05, ('a gap between the blade and the socket', min(back))
    print(f'mount: the Noble axe\'s upper shaft ({", ".join(f"{k} {v}" for k, v in noble_pieces.items())} triangles '
          f'in the source; its blade cut away at its x {noble.NOBLE_SOCKET_X}) at scale {noble.SCALE}, the socket\'s '
          f'middle at y {noble.SOCKET_Y}, the shaft from y {noble.SHAFT_FROM_Y}; {len(MV)} vertices, {len(MT)} triangles, '
          f'y {MV[:, 1].min():.2f} .. {MV[:, 1].max():.2f}; the blade\'s back {min(back) - noble.SOCKET_FACE_X:.2f} or more '
          f'inside the socket over its height')

    # ---- the grip ----
    # the Noble shaft's open lower end: round and fluted (six ridges, grooves between). The ouroboros rests on the
    # ridges' circle; the grip flares to just inside the grooves (it never shows through them) and plugs the tube
    lo = MV[np.abs(MV[:, 1] - noble.SHAFT_FROM_Y) < 0.05]
    c = np.array([(lo[:, 0].max() + lo[:, 0].min()) / 2, (lo[:, 2].max() + lo[:, 2].min()) / 2])
    rr = np.hypot(lo[:, 0] - c[0], lo[:, 2] - c[1])
    assert len(lo) >= 16 and rr.min() / rr.max() > 0.8, ('the shaft end is not round', len(lo), rr.min(), rr.max())
    ridges = (c[0], c[1], rr.max(), rr.max())
    grooves = (c[0], c[1], rr.min(), rr.min())
    print(f'  the Noble shaft\'s lower end (y {noble.SHAFT_FROM_Y}): centre x {c[0]:.3f} z {c[1]:.3f}, ridges r '
          f'{rr.max():.3f}, grooves r {rr.min():.3f} ({len(lo)} vertices)')
    GP, GN, GTg, GBt, GUV, GC, GT = build_grip(s, shaft, grooves)

    # ---- the snake ----
    (SV, SN, STg, SBt, SUV, ST, lay, info), settled, settle_rounds = settle_neck()
    # the grip, tucked under the coil's neck and head where it poked through, then its leather
    GP, tucked, island_pts = tuck_grip(GP, GN, GT, SV, ST)
    GUV, mirrored = mirror_grip_ends(GP, GUV, GT)
    leather, ends_low, ends_top = grip_texture(out_root, GUV, GT, GP)
    add_shape(nif, axe_k, GRIP_SHAPE, GP, GN, GTg, GBt, GUV, GT, GC, {0: 'grip_d.dds'})
    print(f'grip: billyro\'s shaft (split {GRIP_SUBDIVIDE}x{GRIP_SUBDIVIDE}) from y {GRIP_END:.2f} to y '
          f'{GRIP_TOP:.2f} (both ends capped) on a {2 * snake.GRIP_A:.2f} x {2 * snake.GRIP_B:.2f} ellipse; '
          f'{len(GP)} vertices, {len(GT)} triangles; {island_pts} poking grid cells, {tucked} vertices tucked under the snake; leather near-black purple '
          f'({leather} texels); {mirrored} end vertices wear the leather next to them (ends {ends_low:.2f} / '
          f'{ends_top:.2f} of the middle\'s brightness)')
    coil_pitch, _ = scale_textures(out_root, lay, metal, 'coil')
    add_shape(nif, axe_k, SNAKE_SHAPE, SV, SN, STg, SBt, SUV, ST, None,
              {0: 'coil_d.dds', 1: 'coil_n.dds', 5: 'coil_m.dds'})
    # the coil hugs the grip: no coil vertex inside the thinned shaft (the belly rests on it)
    above = SV[:, 1] > lay.y_low + 0.6                        # the coil proper (the neck dips into the grip)
    q = ((SV[above, 0] - snake.AXIS_X) / snake.GRIP_A) ** 2 + (SV[above, 2] / snake.GRIP_B) ** 2
    assert np.sqrt(q.min()) > 0.85, np.sqrt(q.min())
    # the grip's end is inside the head: every vertex of its capped end ring lies inside the snake's surface
    ring = GP[GP[:, 1] < GRIP_END + 1e-4]
    hidden = snake_inside(ring, SV, ST)
    assert hidden.all(), f'{(~hidden).sum()} of the grip end\'s {len(ring)} vertices stick out of the head'
    print(f'snake: Mihail\'s rattlesnake (Triumvirate), tessellated {snake.TESSELLATE}x{snake.TESSELLATE}, head at '
          f'scale {snake.SIGMA_HEAD}, body {snake.SIGMA_BODY} (length x{info["stretch"]:.3f}), {snake.WRAPS} turns, '
          f'jaw open {snake.JAW_OPEN} deg; {len(SV)} vertices, {len(ST)} triangles; bounds {SV.min(0).round(2)} .. '
          f'{SV.max(0).round(2)}; the coil\'s deepest point at {np.sqrt(q.min()):.3f} of the grip\'s radius; the grip\'s '
          f'end ({len(ring)} vertices) inside the head')

    # ---- the ouroboros (the connector) ----
    RV, RN, RTg, RBt, RUV, RT, rlay, rinfo = snake.build(
        MODS, lambda P0: snake.RingLayout(P0, snake.SIGMA_RING_HEAD, snake.SIGMA_RING_BODY,
                                          (ridges[0], ridges[1], ridges[2] + RING_CLEAR, ridges[3] + RING_CLEAR),
                                          tangent_head=True),
        snake.RING_TESS,
        snake.RING_JAW)
    # nothing of the ring inside the Noble shaft's ridges (a little slack: the belly is rounded, the ridges are not)
    rr_ring = np.hypot(RV[:, 0] - ridges[0], RV[:, 2] - ridges[1])
    sunk = (rr_ring < ridges[2] - 0.03) & (RV[:, 1] > noble.SHAFT_FROM_Y)
    print(f'  ouroboros head on the ring\'s tangent, its ends {rlay.standoff:.2f} off the ring; {sunk.sum()} vertices '
          f'inside the shaft\'s ridges above its lower end (deepest {ridges[2] - rr_ring[sunk].min() if sunk.any() else 0:.3f})')
    assert sunk.sum() == 0, 'the ouroboros sinks into the Noble shaft'
    ring_pitch, _ = scale_textures(out_root, rlay, metal, 'ouroboros')
    assert abs(ring_pitch / coil_pitch - snake.SIGMA_RING_BODY / snake.SIGMA_BODY) < 1e-9   # one scale count round both
    add_shape(nif, axe_k, RING_SHAPE, RV, RN, RTg, RBt, RUV, RT, None,
              {0: 'ouroboros_d.dds', 1: 'ouroboros_n.dds', 5: 'ouroboros_m.dds'})
    gt = GP[GP[:, 1] > GRIP_TOP - 1e-4]                         # the grip's capped top lies inside the ring's reach
    print(f'ouroboros: the same rattlesnake round the Noble shaft\'s lower end at y {snake.RING_Y} (head {snake.SIGMA_RING_HEAD}, body '
          f'{snake.SIGMA_RING_BODY}, length x{rinfo["stretch"]:.3f}, jaws {snake.RING_JAW} deg round its tail); '
          f'{len(RV)} vertices, {len(RT)} triangles; y {RV[:, 1].min():.2f} .. {RV[:, 1].max():.2f}; grip top at '
          f'y {gt[:, 1].max():.2f}')

    # ---- the blade's snakes ----
    # ---- the langets: the socket's straps over the blade, the snakes' tails tucked under their tips ----
    y_mid, roots = socket_fit(MV, MN, MT, s_blade)
    LV, LN, LTg, LBt, LUV, LT, faces = langets(s_blade, MV, MUV, MT, y_mid, roots)
    add_shape(nif, axe_k, LANGET_SHAPE, LV, LN, LTg, LBt, LUV, LT, None,
              {0: 'noble_d.dds', 1: 'noble_n.dds', 5: 'noble_m.dds'})
    RVt, RNt, RTgt, RBtt, RUVt, RTt = langet_rivets(s_blade, faces, y_mid, roots)
    for side in (1, -1):                                      # each rivet stands proud of its langet
        r = RVt[np.sign(RVt[:, 2]) == side]
        proud = side * (r[:, 2] - faces[side](r[:, :2])) - langet_height(r[:, 0], r[:, 1], y_mid, roots[side])
        assert proud.max() > 0.08, ('the rivet is buried in the langet', side, proud.max())
    add_shape(nif, axe_k, RIVETS_SHAPE, RVt, RNt, RTgt, RBtt, RUVt, RTt, None,
              {0: 'axe.dds', 1: 'axe_n.dds', 5: 'axe_m.dds'})
    print(f'langets: two tongues from x {LANGET["root_x"]} (in the socket\'s chamfer) to {LANGET["tip_x"]}, '
          f'{2 * LANGET["root_half"]:.2f} wide at the socket, {roots[1]:.2f} / {roots[-1]:.2f} -> {LANGET["tip_h"]} over the blade; '
          f'in the socket\'s own steel (its face strip, +z for both); {len(LV)} vertices, {len(LT)} triangles; billyro\'s rivet '
          f'at x {LANGET_RIVET[0]} (x{LANGET_RIVET[1]} across)')

    # ---- the blade's snakes: their tails under the langets' tips ----
    BV, BN, BTg, BBt, BUV, BT = [], [], [], [], [], []
    shift = np.array(noble.BLADE_SHIFT)
    blade_snakes = [(np.array(sn) + shift, np.array([LANGET['tip_x'] + LANGET_TAIL_IN, y_mid + off]), waves, amp)
                    for (sn, waves, amp), off in zip(snake.BLADE_SNAKES, LANGET_TAILS)]
    blade_heads = []                    # each head's orb (BLADE_ORB_*): between its painted eyes, above its crown
    for side in (1, -1):
        face = faces[side]
        for snout, tail, waves, amp in blade_snakes:
            v, n_, tg, bt, uv_, t_, _, binfo = snake.build(
                MODS, lambda P0: snake.BladeLayout(P0, face, side, tail, snout, waves, amp, snake.SIGMA_BLADE_HEAD,
                                                   snake.SIGMA_BLADE_BODY), snake.BLADE_TESS, snake.BLADE_JAW)
            eye_pts = eye_domes(v, n_, uv_, t_, snake.SIGMA_BLADE_HEAD)[6]
            mid = (eye_pts[0] + eye_pts[1]) / 2
            near = np.linalg.norm(v[:, :2] - mid[:2], axis=1) < 0.45
            crown = float((side * v[near, 2]).max())
            blade_heads.append(np.array([mid[0], mid[1], side * (crown + BLADE_ORB_LIFT)]))
            BT.append(t_ + sum(len(x) for x in BV))
            BV.append(v), BN.append(n_), BTg.append(tg), BBt.append(bt), BUV.append(uv_)
    # under the langets' tops the snakes stay under: where a langet stands full height (off its rounded edges), no
    # snake vertex reaches its surface
    per = len(BV) // 2
    for f_, side in enumerate((1, -1)):
        v = np.vstack(BV[f_ * per:(f_ + 1) * per])
        lh = langet_height(v[:, 0], v[:, 1], y_mid, roots[side])
        Hx = LANGET['tip_h'] + (roots[side] - LANGET['tip_h']) * snake.smoothstep(LANGET['tip_x'], LANGET['root_x'], v[:, 0])
        flat = (v[:, 0] > LANGET['tip_x']) & (v[:, 0] < LANGET['root_x']) & (lh > 0.95 * Hx)
        over = side * (v[:, 2] - faces[side](v[:, :2])) - lh
        worst = over[flat].max() if flat.any() else -1
        print(f'  face {("+z", "-z")[f_]}: snakes under the langet: {flat.sum()} vertices, highest {worst:+.3f} to its top')
        assert worst < -0.01, ('a snake shows through the langet', ("+z", "-z")[f_], worst)
    BV, BN, BTg, BBt, BUV, BT = (np.vstack(x) for x in (BV, BN, BTg, BBt, BUV, BT))
    add_shape(nif, axe_k, BLADE_SNAKES_SHAPE, BV, BN, BTg, BBt, BUV, BT, None, METAL)
    print(f'blade snakes: {2 * len(snake.BLADE_SNAKES)} relief snakes (head {snake.SIGMA_BLADE_HEAD}, body '
          f'{snake.SIGMA_BLADE_BODY}), tails meeting at {snake.BLADE_ORIGIN}; {len(BV)} vertices, {len(BT)} '
          f'triangles; x {BV[:, 0].min():.2f} .. {BV[:, 0].max():.2f}, y {BV[:, 1].min():.2f} .. {BV[:, 1].max():.2f}')

    # ---- the crystal (amethyst) ----
    top, out_dir = snake.mouth_axis(lay, GEM_INSET)
    gs_, gxf = load_gem()
    GV, GNn, GTt, GBb, GUVg, GTRI = place_gem(gs_, gxf, top, out_dir)
    GV, GNn, GTt, GBb, tip, gap06 = fit_gem_to_mouth(GV, GNn, GTt, GBb, SV, info['jaw'], top, out_dir)
    print(f'  the crystal fills the mouth from the jaws\' tips (y {tip:.2f}) to the hinge (gap 0.6 above the tips '
          f'{gap06:.2f})')
    gem_textures(out_root)
    add_shape(nif, axe_k, POMMEL_SHAPE, GV, GNn, GTt, GBb, GUVg, GTRI, None,
              GEM_TEX)
    print(f'crystal (amethyst): the pointed lower {GEM_LENGTH} of vanilla\'s black soul gem at scale {GEM_SCALE}, sealed at the '
          f'slice, the slice {GEM_INSET} inside the snout on the mouth\'s bisector; y {GV[:, 1].min():.2f} .. {GV[:, 1].max():.2f}, x {GV[:, 0].min():.2f} .. '
          f'{GV[:, 0].max():.2f}, z {GV[:, 2].min():.2f} .. {GV[:, 2].max():.2f}')

    # ---- the eyes (amethyst): the coil's head (the pommel) and the ouroboros' ----
    eyes = [eye_domes(SV, SN, SUV, ST, lay.sigma_head), eye_domes(RV, RN, RUV, RT, rlay.sigma_head)]
    EV, EN, ETg, EBt, EUV = (np.vstack([e[i] for e in eyes]) for i in range(5))
    ET = np.vstack([eyes[0][5], eyes[1][5] + len(eyes[0][0])])
    for e, sg, nm in ((eyes[0], lay.sigma_head, 'coil'), (eyes[1], rlay.sigma_head, 'ouroboros')):
        gap = np.linalg.norm(e[6][0] - e[6][1])
        assert 4.5 * sg < gap < 5.7 * sg, (nm, 'the eyes are not across the head', gap / sg)
        print(f'  {nm} eyes: {EYE_R * sg:.3f} radius, {gap:.2f} apart; at {np.round(e[6][0], 2)} and {np.round(e[6][1], 2)}')
    add_shape(nif, axe_k, EYES_SHAPE, EV, EN, ETg, EBt, EUV, ET, None,
              GEM_TEX)
    print(f'eyes: 4 amethyst domes (the painted eyes\' pupils), {len(EV)} vertices, {len(ET)} triangles')

    # ---- the souls' glow: the eyes, one step per soul, and the crystal at a full charge ----
    glows = []
    for i, mult in enumerate(GLOW_STEPS, 1):
        glows.append(glow_node(nif, axe_k, SOUL_NODE % i, SOUL_SHAPE % i, EV, EN, ETg, EBt, EUV, ET, mult))
    glows.append(glow_node(nif, axe_k, BLAZE_NODE, BLAZE_SHAPE, GV, GNn, GTt, GBb, GUVg, GTRI, BLAZE_MULT))
    shown = GV[GV[:, 1] < tip]                                    # the crystal below the jaws' tips: what shows
    centre = np.array([(shown[:, 0].min() + shown[:, 0].max()) / 2, (shown[:, 1].min() + shown[:, 1].max()) / 2,
                       (shown[:, 2].min() + shown[:, 2].max()) / 2])
    halo = add_halo(nif, axe_k, glows[-1][0], centre)
    print(f'  halo: Candlelight\'s {", ".join(f"{p} ({t})" for p, (_, _, t) in halo.items())} at the shown crystal\'s '
          f'middle {np.round(centre, 2)}, sizes {[v[0] for v in HALO_PARTS.values()]}, inside {BLAZE_NODE}, soft depth '
          f'{SOFT_DEPTH}')
    orb = add_orb(nif, axe_k, glows[-1][0], centre, out_root)
    print(f'  Smite orb: {", ".join(f"{p} {s} across x {m}" for p, (s, m) in ORB_PARTS.items())} at the same middle, '
          f'inside {BLAZE_NODE}')
    blade_pal = {}
    blade_orbs = [add_orb(nif, axe_k, glows[-1][0], c, out_root, BLADE_ORB_PARTS, 'Blade%d' % i, False, blade_pal)
                  for i, c in enumerate(blade_heads, 1)]
    write_orb_palettes(blade_pal, out_root)
    print(f'  blade orbs: {len(blade_orbs)} ({", ".join(f"{p} {s} across x {m}" for p, (s, m) in BLADE_ORB_PARTS.items())}, '
          f'no soft fade) at {[tuple(np.round(c, 2)) for c in blade_heads]}, inside {BLAZE_NODE}')
    print(f'glow: {len(GLOW_STEPS)} steps of the eyes (emissive x {GLOW_STEPS}) and the crystal (x {BLAZE_MULT}), '
          f'{GLOW_LIFT} out, colour {GLOW_COLOUR}; nodes {SOUL_NODE % 1}..{len(GLOW_STEPS)}, {BLAZE_NODE} at scale 0')

    out = os.path.join(out_root, *MESH_OUT.split('/'))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    data = nif.tobytes()
    open(out, 'wb').write(data)
    for src, (rel, ours) in COPIES.items():
        dst = os.path.join(out_root, *(TEX_DIR + ours).split('/'))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(os.path.join(RAW, *rel.split('/')), dst)
    for old in ('bone_d.dds', 'bone_n.dds', 'bone_m.dds',         # rounds 1-2's bone set, no longer used
                'spine_d.dds', 'spine_n.dds', 'spine_m.dds',      # the dark-iron spine and snake sets, replaced by the
                'snake_d.dds', 'snake_n.dds', 'snake_m.dds',      # blade's metal
                'neck_d.dds', 'neck_n.dds', 'neck_m.dds',         # the neck snake's scales (replaced by the mount)
                ORB_PALETTE % 'gradtelekinesis01'):               # the orb's ring's palette (the ring came off)
        p = os.path.join(out_root, *(TEX_DIR + old).split('/'))
        if os.path.isfile(p):
            os.remove(p)

    # ---- read back ----
    back = nifse.Nif(open(out, 'rb').read())
    assert back.tobytes() == data
    names = [name_of(back, k) for k in back.find('BSTriShape')]
    glow_shapes = [SOUL_SHAPE % i for i in range(1, len(GLOW_STEPS) + 1)] + [BLAZE_SHAPE]
    halo_shapes = ['ZP_WhisperHalo' + p for p in HALO_PARTS]
    orb_shapes = ['ZP_WhisperOrb' + p.split(':')[0] for p in ORB_PARTS]
    orb_shapes += ['ZP_WhisperOrb%sBlade%d' % (p.split(':')[0], i) for i in range(1, len(blade_heads) + 1)
                   for p in BLADE_ORB_PARTS]
    assert len(blade_heads) == 2 * len(snake.BLADE_SNAKES), ('a blade snake without its orb', len(blade_heads))
    assert sorted(names) == sorted([HOLDER_SHAPE, 'EdgeBlood01', 'EdgeBlood', AXE_SHAPE, NOBLE_SHAPE, GRIP_SHAPE,
                                    SNAKE_SHAPE, RING_SHAPE, BLADE_SNAKES_SHAPE, POMMEL_SHAPE, EYES_SHAPE,
                                    LANGET_SHAPE, RIVETS_SHAPE] + glow_shapes + halo_shapes + orb_shapes), names
    # the halo and the orb: each sprite alone on a billboard inside the blaze node, on its own effect shader and alpha
    # property, no controller, the soft depth ours, a palette (if any) ours and written
    blaze_kids = nifse.node_children(back.blocks[glows[-1][0]])[1]
    sprite_props = set()
    sprites = [(p, v[:2], True) for p, v in halo.items()] + [(p, v[:2], True) for p, v in orb.items()]
    sprites += [(p, v[:2], False) for bo in blade_orbs for p, v in bo.items()]
    for part, (bb, k), soft in sprites:
        assert back.btype(bb) == 'NiBillboardNode' and bb in blaze_kids and nifse.node_children(back.blocks[bb])[1] == [k]
        rs = nifse.read_trishape(back.blocks[k])
        sb = back.blocks[rs['shader']]
        assert back.btype(rs['shader']) == 'BSEffectShaderProperty' and struct.unpack_from('<i', sb, 8)[0] == -1, part
        assert bool(struct.unpack_from('<I', sb, 12)[0] & SLSF1_SOFT) == soft, (part, 'soft flag')
        o = 36 + 4 + struct.unpack_from('<I', sb, 36)[0] + 4 + 16 + 16
        assert not soft or struct.unpack_from('<f', sb, o + 4)[0] == SOFT_DEPTH, (part, 'soft depth')
        ln = struct.unpack_from('<I', sb, o + 8)[0]
        grey = bytes(sb[o + 12:o + 12 + ln]).decode('latin-1')
        if grey:
            assert grey.lower().startswith(r'textures\zenderal\whisper' + chr(92)), (part, grey)
            assert os.path.isfile(os.path.join(out_root, *grey.split(chr(92)))), (part, grey)
        sprite_props |= {rs['shader'], rs['alpha']}
    assert len(sprite_props) == 2 * len(sprites), 'a sprite shader or alpha property is shared'
    # the glow: each shape alone under its node, the node on the root at scale 0, its shader emitting
    _, root_kids = nifse.node_children(back.blocks[back.roots[0]])
    for (node_i, shape_i), want in zip(glows, [SOUL_NODE % i for i in range(1, len(GLOW_STEPS) + 1)] + [BLAZE_NODE]):
        assert back.btype(node_i) == 'NiNode' and name_of(back, node_i) == want and node_i in root_kids, want
        assert nifse.transform(back.blocks[node_i])[2] == 0.0, (want, 'not at scale 0')
        node_kids = nifse.node_children(back.blocks[node_i])[1]
        assert node_kids[0] == shape_i and shape_i not in root_kids, want
        assert len(node_kids) == (1 + len(sprites) if want == BLAZE_NODE else 1), (want, node_kids)
        sb = back.blocks[nifse.read_trishape(back.blocks[shape_i])['shader']]
        assert struct.unpack_from('<I', sb, LSP_FLAGS1)[0] & SLSF1_OWN_EMIT, (want, 'no Own_Emit')
    # the root names the skeleton node the equipped axe hangs from (Prn = WeaponAxe; without it the axe was invisible
    # equipped while the inventory preview showed it)
    prn = [(back.string(struct.unpack_from('<i', back.blocks[k], 0)[0]),
            back.string(struct.unpack_from('<i', back.blocks[k], 4)[0])) for k in back.find('NiStringExtraData')]
    assert ('Prn', 'WeaponAxe') in prn, prn
    # every shape keeps the selective-update bits (0xE): without them the equipped axe is invisible (it never moves
    # with the hand); only the blood edges carry the hidden bit (shown on a hit)
    for k in back.find('BSTriShape'):
        fl = struct.unpack_from('<I', back.blocks[k], nifse.av_fields(back.blocks[k])['flags'])[0]
        want_hidden = name_of(back, k) in (HOLDER_SHAPE, 'EdgeBlood01', 'EdgeBlood')
        assert fl & 0xE == 0xE and bool(fl & 1) == want_hidden, (name_of(back, k), hex(fl))
    shaders = set()
    for nm, (V_, T_) in {NOBLE_SHAPE: (MV, MT), GRIP_SHAPE: (GP, GT), SNAKE_SHAPE: (SV, ST),
                         RING_SHAPE: (RV, RT), BLADE_SNAKES_SHAPE: (BV, BT), POMMEL_SHAPE: (GV, GTRI),
                         EYES_SHAPE: (EV, ET), LANGET_SHAPE: (LV, LT), RIVETS_SHAPE: (RVt, RTt)}.items():
        rs = nifse.read_trishape(back.blocks[shape(back, nm)])
        assert len(rs['tris']) == len(T_) and np.abs(rs['pos'] - V_).max() < 1e-4, nm
        shaders.add(rs['shader'])
    shaders.add(nifse.read_trishape(back.blocks[shape(back, AXE_SHAPE)])['shader'])
    for nm in glow_shapes:
        shaders.add(nifse.read_trishape(back.blocks[shape(back, nm)])['shader'])
    assert len(shaders) == 10 + len(glow_shapes), 'a shader is shared'
    assert len(nifse.read_trishape(back.blocks[shape(back, AXE_SHAPE)])['tris']) == int((~drop).sum())
    for k in back.find('BSLightingShaderProperty'):
        ts = struct.unpack_from('<i', back.blocks[k], nifse.LSP_TEXSET)[0]
        for p in nifse.texture_paths(back.blocks[ts]):
            if p.lower().startswith(r'textures\zenderal'):
                assert os.path.isfile(os.path.join(out_root, *p.split(chr(92)))), p
            assert not p.lower().startswith(r'textures\billyro'), p
    print('Wrote', out, f'({len(data)} bytes) and {len(COPIES) + 7} textures under', os.path.join(out_root, TEX_DIR))


if __name__ == '__main__':
    main()
