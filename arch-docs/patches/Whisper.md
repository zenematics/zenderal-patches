# Whisper

- **Source:** `src/Whisper/` (`tools/01-convert-stalwart.py`, `tools/02-build-mesh.py`, `tools/gamespine.py`,
  `tools/snake.py`, `tools/03-build-records.py`, `WhisperESP/`)
- **Ships (so far):** its own mesh `meshes\Zenderal\Whisper\Whisper.nif` + 14 textures under
  `textures\Zenderal\Whisper\` in **Zenderal - Patch Collection** (generated from billyro's, vanilla's and Mihail's
  files, not committed), and a test plugin `Zenderal - Whisper.esp` (ESL, HEDR 1.7; live copy in Patch Collection)
  with the weapon alone: no charge, no release, not placed, not craftable
- **Credits:** billyro (the axe), **Mihail** (the rattlesnake, via Triumvirate - Mage Archetypes), **Caenraes** (the
  Noble Armory upper shaft, socket and spike, via Pretty Enderal Armory)
- **FormID block:** `0x800–0x801` (WEAP 800 `ZP_Whisper`, STAT 801 `1stPersonZP_Whisper`); masters Skyrim.esm,
  Update.esm, Enderal - Forgotten Stories.esm only
- **Pillar:** modern combat (curator's request, 2026-11-15)

## What it will be

A unique one-handed axe themed on **Entropy**, named **Whisper** by the curator. Entropy absorb/drain spells cast
while it is carried show souls leaving the target and charge the axe; a power attack releases the charge. The
curator: "once we have the base weapon to work from we will modify the design". Charge style and release are not
picked yet; the options offered are in the curator conversation and summarised under *Design notes* below.

## The base: billyro's Stalwart Axe

- **Model:** billyro, [Stalwart Axe](https://www.nexusmods.com/skyrim/mods/70388) (Skyrim LE, version 1, 2015):
  a crescent bearded blade on a curved neck, a ring on the neck, a turned and banded handle; one-handed, with a
  two-handed variant mesh. **billyro gave the curator permission to use his weapons** (2026-11-15). Credit billyro.
- **Downloads** (in MO2 `downloads/`, unpacked into the gitignored `reference/mods/_raw/StalwartAxe/`):
  `Stalwart Axe-70388-1.7z` → `main/` (meshes `axe1h.nif`/`axe2h.nif`, 2K textures, the holder's textures, the
  original plugin `Stalwart Axe.esp`), `Stalwart Axe - 4K Textures-70388-1.7z` → `4k/` (`axe.dds` 4096² DXT1,
  `axe_n.dds` 4096² DXT5, `axe_m.dds` 2048² DXT1).
- **The mesh is LE** (NIF stream 83, `NiTriShape`s). `tools/01` converts `axe1h.nif` to SE through PyNifly into
  `reference/mods/_raw/StalwartAxe/se/meshes/billyro/stalwartaxe/axe1h.nif` (gitignored: the author's mesh):
  4 shapes - the axe `1stPersonSteelWarAxe:0` (1307 verts, 1724 tris), the hip holder `Scb` (488/480), the blood
  edge pair `EdgeBlood01` (lighting) and `EdgeBlood` (effect shader) - with shaders, texture slots, alpha, the
  root's `BSXFlags` (194) and `BSInvMarker`, and the collision (`bhkRigidBody` mass 9, layer 5, a 50-vertex convex
  hull). Every part is read back and asserted; the SE file also parses with `src/StingAndRise/tools/nifse.py`, so
  the Sunrise/Argent Verdict tooling (texture recipes, ornaments, `set_triangles`) applies.
- **PyNifly lesson:** an effect shader written by replacing the shape's shader buffer (or carrying the source's
  block IDs) produced a file nifly could not read back. Fill the shape's own `shader.properties` field by field,
  skipping `*ID` fields and `bufSize`, then set `bufType` (and `bBSLightingShaderProperty = 0` for an effect
  shader), as PyNifly's own exporter does.
- **PyNifly lesson 2 (cost two in-game tests): carry every root extra-data block.** The first conversion copied
  only `BSXFlags` and `BSInvMarker` and dropped billyro's `NiStringExtraData` **`Prn` = `WeaponAxe`**, the skeleton
  node an equipped axe hangs from (every vanilla weapon has one: the Ebony War Axe `WeaponAxe`, Argent Verdict's
  base `WeaponBack`). Without it the equipped axe was **invisible** while the inventory preview (which needs no
  skeleton) showed it. `tools/01` now copies every root extra-data block and asserts there is nothing else and that
  `Prn` is `WeaponAxe`; `tools/02` asserts it on the written mesh.
- **PyNifly lesson 3:** `createShapeFromData` also writes the shape's NiAVObject flags as **0**. billyro's shapes
  carry `0x8000E` (the blood edges `0x8000F`: hidden until a hit shows them), so the blood edges were drawn all the
  time. This was my first guess for the invisible axe; the curator's retest showed it was not the cause (the `Prn`
  was), but the flags were wrong anyway. `tools/01` now sets `d.flags = s.flags` and asserts them; `tools/02` asserts
  `0xE` on every shape and the hidden bit on exactly the holder and the blood edges. Our own new shapes copy the
  axe's flags.

## The design: the game's own spine in dark iron (round 3, 2026-11-15)

Curator, on the base render with the neck circled: "make the highlighted area a Metal skeleton spine". What shipped
is round 3:

- **Rounds 1-2, rejected.** Round 1 generated our own vertebrae (waisted barrels, spike processes) with five
  open-mouthed generated skulls on the outer ridge (layout B picked, then "make sure the skulls are symmetrically
  spaced": solved to exactly 3.0087 apart). Round 2, curator: "shaped more bonelike ... a rounded end at the top,
  instead of 5 skulls ... one larger skull shrouded with a hood protruding from the back of the head": knobbed
  processes, a tip knob, one big hooded skull on the poll. Curator, mid-way through its fixes: **"use actual
  skeleton parts from the game, what you've done so far doesn't look good, just do the spine no skull and hood"**.
  Lesson: for an organic part, start from the game's own mesh; procedural bone read as machined. `bones.py` is gone.
- **The spine** (`gamespine.py`): vanilla's `meshes\clutter\bones\humanspine.nif` (`Skyrim - Meshes0.bsa`, read at
  build time, never committed; 483 vertices, 934 triangles, asserted). In its own coordinates (shape scale 1.058) it
  is 64.7 units along y, sacrum and curled tail bone at +y, neck vertebrae at -y, spinous processes on -z, with its
  natural S-curve in y-z. It is laid along the neck path: straight up the handle axis (x 1.25) from the top band,
  then over the blade's concave back edge (apex touching the old neck at (x -0.48, y 28)) and along its upper back
  edge offset ~0.55 outward, 25.87 units. The S-curve is straightened first (front-to-back midpoints over 40 height
  bins, smoothed); each vertex's height picks its arc length, its lateral and front-to-back offsets go along the
  path frame, spinous processes toward the poll, vertebral bodies toward the blade so its back edge sits inside
  them. The neck vertebrae end, smallest, at the blade's upper back corner; the game spine is open at its neck end
  (where a skull sits), and that ring lands inside the blade's thickness there (z ±0.72 against ±0.84), hidden.
  Normals, tangents and bitangents turn with the same local rotation; the cross-section scale is non-uniform, so
  normals take its inverse and surface directions the scale itself, and vanilla's normal map still lines up. x is
  mirrored (the spine is symmetric) so the mapping keeps the triangles' winding.
- **The joint with the handle** (curator: "the spine needs to connect to the handle more smoothly"). First fit: the
  whole spine at scale 0.459 with the sacrum on the band like a collar, its tail bone sunk into the grip; the
  sacrum sat on the band like a lump wider than it. Now: the **sacrum and tail bone are cut off** (`SACRUM_CUT`, the
  game spine's own y 4.0: 18 triangles cross there and no vertex lies within 0.3, the fewest of any height, so the
  cut edge is one clean ring of the tube), leaving 265 vertices and 512 triangles; the rest is fitted to the path at
  scale 0.828 with the **cross-section ×0.65** (about the band's width: at the game's own proportions it would be
  ~1.6× the band). The **base narrows** into the band: below the band top the cross-section shrinks to fit 1.0
  lateral / 1.45 front-to-back (×0.742), widening back to full over 3.5 units (smoothstep). It goes `BASE_SINK` 2.3
  into band and grip, so the whole open cut ring sits at y 7.70-9.93, |z| ≤ 1.00 against the grip's 1.10 (at 1.4
  the ring, slanted by the S-curve, reached 0.76 above the band top). `tools/02` asserts the base stays inside the
  grip's footprint. Rendered: the spine grows straight out of the band.
- **Higher poly, higher resolution** (curator: "make the spine more high poly and higher resolution textures").
  The list's Skeletons SE (4thUnknown, Nexus 124394) has a 23,905-triangle spine on 4K textures, but its page
  forbids any asset use, and no other skeleton texture in the list beats vanilla's 2048 (SMIM's is the same size).
  So, in-house: **Phong tessellation** (`gamespine.tessellate`, Boubekeur & Alexa 2008): each kept triangle split
  4×4, new points pulled toward the original vertices' tangent planes (α 0.65), original vertices unmoved (Loop
  subdivision would shrink the processes); the projection uses normals averaged per position, so edges across UV
  seams get identical points: the open edges went from 18 to exactly 72 (18 × 4), no cracks. 512 → **8,192
  triangles**, 4,132 vertices; bounds within 0.1 of the untessellated spine. **Textures**: the spine uses only a
  strip of the 2048 skeleton atlas (u 0.012-0.134, v 0.203-0.633, 262 × 894 px with the margin), so it gets its own
  **1024 × 4096** set cut from that strip (~4× the texel density): Lanczos upscale, then generated detail so it is
  not just softer pixels: grain (value noise, ±7%) and sparse pitting in the diffuse, the same as micro-relief
  whiteout-blended into the normal map (alpha = vanilla's specular, upscaled). Diffuse and normal BC7 (5.3 MB
  each), env mask BC1 (2.7 MB); UVs remapped onto the crop (asserted inside 0..1). The preview renderer shades with
  vertex normals, so the normal-map relief is unseen there.
- **Cut** (`tools/02` `cut()`, asserted by the parts' measured extents): the curved neck tube, the collar band, the
  two collar rivets, and every handle triangle reaching above the top band's top face (y 10.05): 452 of the axe
  shape's 1724 triangles. The blade, its rivets and blood edges, the grip below the band and the collision stay.
- **Material**: one shape `ZP_WhisperSpine` with vanilla's UVs and vertex colours (baked shading), its own copy of
  the axe's environment-map shader (never shared: Clockwork Thunder's freeze) with `SLSF2_Vertex_Colors` set. Dark
  iron (`spine_d.dds`): vanilla `textures\actors\skeleton\skeleton.dds`'s brightness on a cool tint (0.62, 0.62,
  0.68) × 1.35; env mask `spine_m.dds` = 0.22 + 0.30 × brightness; normal map = vanilla `skeleton_n.dds` **copied**
  as `spine_n.dds` (a skeleton retexture in the list, e.g. Skeletons SE, may be laid out for its own meshes). A
  bone-coloured version (vanilla's own diffuse) was rendered alongside; the curator kept dark iron ("Keep dark
  iron", 2026-11-15).
- **Ruby crystal pommel** (curator, circling billyro's turned knob: "change this to a ruby crystal pommel (we
  will make this glow when the weapon is charged)"). The knob goes: every handle triangle reaching below y -10.6
  (154; its top quads run from y -12.2 up to -10.0 inside the bottom band, so "wholly below" left a stub). In its
  place, vanilla's **black soul gem** (`meshes\clutter\soulgem\soulgemblack01.nif`, read at build time, 62
  triangles asserted): a single faceted crystal prism with one fine point, chosen over Enderal's red cave clusters
  (`enderal\dungeons\crystals\crystal0Nred`, 130-200 units of fanned points) and vanilla's flat cut ruby. Its long
  axis (z) down the handle at scale 0.43. First build: the whole gem, 9.5 units (the old knob's length). Curator,
  circling a stub just under the band: "reduce its length": now only its **pointed lower 3.8 units** (0.3 of
  them inside the band, y -10.2 .. -14.0): the gem is clipped at that height across its full-width body
  (`clip_below`: triangles split at the plane, attributes interpolated at the cut) and the slice sealed with a
  flat cap (a fan round the cut's centre, its own up-facing normals, wound as the gem's own faces), so the point
  keeps its proportions (a squash along the axis would blunt it); 68 triangles, closed (no open edge, signed
  volume positive like the source's). Seated at x 1.15, slice up inside the bottom band; its top corners sit
  ~0.2 wider than the band (z +-1.32 against +-1.15). x along the axe's x, its y along -z, a proper rotation so
  the winding holds; its facets stay flat (no tessellation). Shape `ZP_WhisperPommel`, its own copy of the axe's
  env-map shader: `ruby_d.dds` = vanilla `soulgemblack.dds`'s normalised luminance × (0.55 .. 1.40) on ruby (0.62,
  0.035, 0.07), BC7; `ruby_n.dds` = vanilla `soulgemcommon_n.dds` copied; env mask `ruby_m.dds` 0.85 (glassy). The
  soul gem's own shader carries an emissive pulse (colour/float controllers); for the charged glow the simplest
  proven route is Argent Verdict's: a glowing copy of the crystal under a node at scale 0, scaled up by SKSE
  `NetImmerse.SetNodeScale` while charged.
- **The ruby since the snake grip** (below): the same gem now sits in the snake's open mouth, its slice inside
  the mouth and its point down past the snout on the mouth's bisector (the handle axis). Scale 0.19 (1.3 wide, so
  the jaws close on it 0.6-0.9 inside the snout and flare round it at the tips). First build: the whole gem, 2.5
  out of the mouth. Curator: "shorten the ruby pommel further into the mouth": its pointed lower 2.9, sliced
  1.45 inside the snout. Curator, on that: "theres a gap in the snakes mouth" (from the side the open jaws showed
  daylight above the crystal: the mouth is hollow between palate and floor). Now the crystal reaches back to the
  jaw hinge: its **pointed lower 4.15** (`GEM_LENGTH`, the blunt end sliced flat), the slice **2.7** inside the
  snout (`GEM_INSET`), still **1.45 showing**; y -8.54 .. -12.69. Its part between the jaws is narrowed height by
  height in the direction the jaws open (axe z) to the gap between them (`fit_gem_to_mouth`: per 0.05 the upper
  jaw's innermost point (largest z of upper-jaw vertices over the crystal's own x range) and the lower jaw's; the
  jaws sink `MOUTH_BITE` 0.04 into it; eased in over 0.15 below the tips; normals by the inverse transpose), so the
  crystal is a wedge filling the V up to the hinge and the jaws close on it everywhere. Same textures, same separate
  shape `ZP_WhisperPommel` (for the glow).
- **The hip holder is hidden** (`HIDE_HOLDER`): billyro's `Scb` is a leather cup with a ring hooked round the old
  neck, drawn only while sheathed; the sacrum would sit in it. Flag bit 0 on the shape; its textures still ship.
- **billyro's textures** ship under Whisper's paths (the Stalwart Axe is not in the list): the 2K axe set, the
  holder's set and the cubemap (`nissibeach.dds`, Humus via billyro) as `nissibeach_e.dds`; no texture path in the
  mesh still points at `textures\billyro` (asserted).
- **Charge display**: the five skull mouths are gone with the skulls; where charges show is open again (the ruby
  is the curator's pick for the glow).

## The snake grip (2026-11-15)

Curator: "rework the handle itself, make it thinner with a metal snake coiling round it the pommel is formed from
the snakes head, the Ruby is inside the snakes open mouth", with a drawing on the back view: four diagonal coil
strokes from under the top band down the grip (upper left to lower right), the head looped in at the bottom, the
ruby below it. Then: "isn't their a snake from triumvirate ?". The two drawings are the reference; they were pulled
back out of the session transcript to check the layout.

- **The snake:** Mihail's rattlesnake as **Triumvirate - Mage Archetypes** ships it
  (`meshes\mihail monsters and animals\ice wraith\snakes\mihailrattlesnake.nif` in its BSA, textures
  `rattlesnake.dds` / `_n.dds` in its textures BSA; read at build time, never committed). Mihail's terms: "You are
  allowed to use the assets in this file without permission as long as you credit me" (Nexus 36548 / 56523).
  **Credit Mihail.** One skinned shape (1133 vertices, 2002 triangles, asserted), so it is read with PyNifly
  (nifse reads unskinned shapes only). Its bind pose is straight: snout +y 33.93, tail -171.5, back +z, belly line
  z ~122.2 all along; head 14 long, 8.4 wide at the jaw hinge; no jaw bone. Tangents are computed from its UVs the
  game's way (measured on vanilla's humanspine: tangent = +dP/dv, bitangent = +dP/du).
- **Opening the mouth.** The mouth is a closed cavity: in every slice from y 26.3 to the snout the head is two
  surfaces, the upper (top + palate, palate normals down) and the lower (underside + floor, normals up), meeting
  only at the lip corners, which sit 0.06-0.15 apart along the sides. A height rule cannot tell those apart (the
  first try split the upper lip's corner row into the lower jaw and stretched the snout into a membrane), and a
  rule on normals against the head's middle misread the palate (it lies below the middle). So `snake.lower_jaw`
  splits it by the mesh's own topology: flood fill from the topmost and the lowest triangle at y 29-31 without
  crossing y 26.3 (the cavity's back wall is at 26.1); the halves never meet, they share only the two mouth corners
  (weight 0.5). Behind 26.3 the throat's underside follows, faded out toward y 21. `open_jaw` turns the lower jaw
  down by `JAW_OPEN` 36° about the hinge (y 25.8, z 124.4, just behind the mouth corners) and tilts the whole head
  up by half that (faded in along the neck, y 14-21), so the mouth's bisector stays the head's axis. The jaw weight
  rides through the tessellation in the vertex-colour channel.
- **The layout** (`snake.Layout`): the path, from the snout up: the head straight up the handle axis (top toward -z,
  the face the drawing shows), the neck a cubic arching back over the head's top into the coil, then 3.6 turns of a
  helix round the thinned grip from y -4.6 to the tail tip at 8.72 (just under the top band's underside, 9.0),
  descending toward -x on the -z face as drawn, ending on the -z face where its outward normal is the head's top
  direction (the frames stay continuous). The coil's centre line is the grip's ellipse pushed out along its normal
  by each ring's own belly depth (iterated with the arc length), so the belly rests on the grip all the way (the
  tail tip thinner, closer). The head keeps its own proportions at scale **0.34** (2.9 wide at the hinge, 4.7 long:
  the drawing's loop, and wider than the grip); along the neck (snake y 20 → 0) the scale eases to the body's
  **0.15** (1.2 wide, 0.9 deep), and the body's length is fitted to the path (×0.977). Each vertex: its height picks
  the arc length, its lateral and dorsal offsets go along the path frame (right-handed, so winding holds). Phong
  tessellation 3×3 before mapping (18,018 triangles, 9,403 vertices). Normals, tangents and bitangents go through
  the mapping's own Jacobian (central differences): normals by its inverse transpose. Asserted: 97 %+ of triangles
  face the way their normals do; no coil vertex deeper than 0.85 of the grip's radius (0.866).
- **The grip** (`ZP_WhisperGrip`): billyro's shaft below the top band (442 triangles), its finger swells gone:
  every vertex moved onto a **1.70 × 1.24 ellipse** round the handle axis (billyro's ~2.8 × 2.1), same height and
  direction from the axis, normals the ellipse's, tangent frames re-orthogonalised; its own copy of the axe's shader
  and billyro's textures. The two lower bands and the turned knob are gone (the head is the pommel). The top band
  stays. First build stopped the grip just above the head's back; the head is tilted with its open jaws, so its back
  stood off the grip's end on the top side (curator, circling it: "make sure there isn't a gap between the head
  and the handle"). Now the grip **runs down into the head** to y -8.30 (`GRIP_END`, 1.8 below the occiput) and is
  capped flat there; `tools/02` asserts all 49 vertices of the capped end lie inside the snake's surface (ray
  parity test).
- **Material:** `ZP_WhisperSnake`, its own copy of the axe's shader, no vertex colours; first dark iron from the
  rattlesnake's textures, now the blade's smooth steel (see *Materials* below).

## Materials: the blade's steel and a burgundy grip (2026-11-15)

Curator: "make the texture of the snake and spine smooth shiny metal instead of grey bone and snake skin", then
"match the metal of the axe blade" and "make the leather of the handle under the snake a dark burgundy". Until
then the spine and snake were dark iron carrying vanilla's bone grain and the rattlesnake's skin pattern (each a
cropped, upscaled set with generated grain and pitting; that pipeline is gone).

- **The blade's metal, measured:** billyro's blade is a dark, neutral diffuse whose shine is the env-map shader's
  cubemap. `blade_metal()` takes the medians of `axe.dds`, `axe_m.dds` and `axe_n.dds`'s alpha over the texels
  under the crescent blade's UVs (1,066,568 texels): diffuse **0.106** grey, env mask **0.231**, specular **0.416**
  (asserted dark, neutral and in range, so a different blade texture stops the build).
- **One shared smooth set**, `metal_d / _n / _m.dds` (256², uniform: diffuse = those values, env mask = 0.231,
  normal map flat with specular 0.416 in its alpha): no bone grain, no scales. Spine and snake each keep their own
  shader copy, already the blade's settings (env-map type, `nissibeach_e` cubemap, glossiness 80, specular 1); the
  spine keeps its vertex colours (vanilla's baked shading darkens its crevices). With smooth normals the snake's
  painted eyes are gone; engraved scales or eyes would come back through a normal map if wanted.
- **The grip:** its own diffuse `grip_d.dds`: billyro's `axe.dds` with the texels under the grip shape's UVs (the
  shaft's island, grown 2 px) recoloured by Sunrise's `recolor_leather` to **#4A0E18** at the leather's
  75th-percentile brightness, its light and dark kept at 0.75 of their depth (269,321 texels, mean 0.244 0.046
  0.079); the grip's normal map and env mask stay billyro's (matte). The top band keeps billyro's texture (it is
  on the axe shape).
- **Preview:** `render_env.py` (scratch) adds the shader's reflection, cubemap(reflect) × env mask, to the textured
  preview: without it the curved snake and spine read near black beside the flat blade, which catches the plain
  highlight. With it they read as the blade's dark polished steel.
- The old `spine_*` and `snake_*` textures are deleted from Patch Collection by `tools/02`; 14 textures ship.
- **Sizes:** the axe is now ~27,000 triangles (snake 18,018, spine 8,192); heavy for a weapon, within what the
  list's other uniques carry. `TESSELLATE = 2` in `snake.py` would halve the snake.

## Spikes, the ouroboros and the blade's snakes (2026-11-15)

Curator, on the smooth-metal build: "the snake looks great but the spine lost a lot of its definition maybe remake
the spine with defined ridges and spikes"; then, circling the band with a pale sliver under it: "clean up the
connector and handle too, the connecting piece is a snake eating its own tail"; then, with three strokes drawn
fanning from the spine's middle rivet across the blade: "add 3 fanning metal snakes to either side of the blade".

- **The spine's definition** (`gamespine.sharpen_processes`, `crease_normals`): the bone texture had drawn its gaps
  and ridges; on plain metal only the shape is left, so the shape is sharpened in the game spine's own coordinates
  before tessellation. The spinous processes (dorsal offset past 1.2 from the S-curve's centre line) reach 2.1×
  further and narrow toward their tips (up to 65 %): pointed spikes along the outer edge; the transverse processes
  (lateral past 1.5) reach 1.5× further: side ridges. Both fade out over the last 4-10 game units at the base
  (squeezed into the grip they crumpled). Phong tessellation softened to α 0.30 (0.65 rounded the edges away);
  normals rebuilt from the laid shape and split across edges sharper than 38° (crisp ridges catch the cubemap);
  vanilla's baked shading (vertex colours) deepened to the power 1.6. 8,198 triangles, 6,342 vertices.
- **The pale sliver** under billyro's band was the spine's base: fitted to billyro's grip, it stuck out of the thinned
  one below the band by up to 1.64 of its radius. Now the spine is laid 1.0 below the old band top
  (`SPINE_SINK`), its base narrowed to fit (`BAND_FIT` 0.90 / 1.10), and **cut flat at y 9.4** (`SPINE_BASE_Y`) and
  sealed: its own open end is slanted by the S-curve (a shallow sink left it spanning y 9.3-11.4, above the ring).
  `tools/02` asserts nothing lies below the cut and the section stays within the ring's outer edge. A fit to the
  thin grip itself (0.50 / 0.70 with the old 2.3 sink) squeezed the base into folds.
- **The ouroboros** (`ZP_WhisperOuroboros`, `snake.RingLayout`): billyro's top band (y 9-10) is cut from the axe
  shape and the same rattlesnake rings the grip's top at y 9.6, belly on the grip, back outward, its body 0.9 tall
  (scale 0.11; the band was 1.0), compressed along its length (×0.167) to one turn. The head (scale 0.15, 2.1 long)
  is a straight chord of the ring on the -z face, facing -x; the body runs round to the snout and its tail turns in
  along the chord, 0.55 of a head length into the mouth; jaws open 30° (the grip snake's flood-fill split). The
  corners where the straight head meets the ring are rounded over 0.12 (`smooth_after`). Tessellated 2×2: 8,008
  triangles. The grip is now clipped and capped at y 9.5 inside the ring (billyro's band had closed it), and the grip
  snake's tail tip ends inside the ring's body (`COIL_TOP` 9.5).
- **The blade's snakes** (`ZP_WhisperBladeSnakes`, `snake.BladeLayout`): three relief snakes on each face, six in one
  shape, from the middle rivet (x -1.52, y 27.52: where the drawing's strokes meet) to snouts at (-8.4, 33.3),
  (-9.5, 27.9), (-8.4, 21.9), short of the blade's outer bevel (the flat face is z ±0.84 to about x -10) and clear of
  the other two rivets. Each tail tip sits 0.25 out of the rivet's centre, under its head; the body waves sideways
  (1.25-1.5 waves, 0.40-0.45 amplitude, vanishing at both ends); the head is straight. The belly follows the face's
  own height (`face_height`: the axe shape's faces rasterised per side at 0.04, holes filled from neighbours).
  Scale: head 0.10 (1.4 long), body 0.075 (0.62 wide, 0.45 proud); 0.075 / 0.055 read as thin lines. Untessellated:
  12,012 triangles. Each face's set is the same paths, mapped right-handed, so the back set is not mirrored geometry.
- **The layouts** are one class now (`snake.Layout`: a path from the snout to the tail tip with the wanted dorsal
  direction; the head keeps its proportions, the body is stretched or compressed to fill the path): `CoilLayout`
  (the grip), `RingLayout`, `BladeLayout`. The tail tip can land a hair past the path's end through the length grid's
  rounding; `frames()` runs straight on past both ends (a clamped end gave a singular Jacobian).
- **Totals:** 8 added shapes; ~57,000 triangles in all (grip snake 18,018, blade snakes 12,012, spine 8,198, ring
  8,008); the mesh is 1.2 MB. Heavy for a weapon; the grip snake's 3×3 tessellation (`snake.TESSELLATE`) is the
  first thing to lower if it shows in game.

## The neck snake: the spine is gone (2026-11-15)

Curator, on the spiked spine: "everything but the spine looks good, forget the spine design you have, I want an
actual human spine but made from metal". The most detailed human spine in the list that is not forbidden is Mihail's
Ancient Skeletons body (Nexus 34368: the lumbar, thoracic, cervical and atlas vertebrae are separate pieces, 2,826
triangles, three times vanilla's), but its page credits **CD PROJEKT RED** for the "original models and textures of
bones": Witcher assets, not Mihail's to pass on, so not used; Skeletons SE forbids asset use. Before a metal version
of vanilla's spine was built, the curator changed course, with a drawing (a stroke rising from the connector and
bending toward the blade, its end split like open jaws round the blade's back): **"make the spine of the axe a snake
with its mouth open spanning into the axe blade"**, then **"add some scales to it like the palm of the hand you did
for Argent Verdict"**.

- **`ZP_WhisperNeckSnake`** (`snake.NeckLayout`): the same rattlesnake, tail tip on the handle axis inside the
  ouroboros (y 9.7), straight up the axis to y 23, a cubic curving into the head; its back faces +x (the poll) all
  the way, so the bend's outer side and the head's top face up and away from the blade. Body scale 0.24 (2.0 wide;
  compressed ×0.29 to the path), head 0.42 (5.9 long, jaws 3.4 from the corner to the snout, 3.5 wide).
- **The bite:** the blade's back is a V (apex x -0.48, y 28; upper edge at 138°, lower at 230°). The mouth's corner
  sits at (-0.25, 28.0), the apex just inside it; the head runs along 134° with the skull turned up 10° (upper jaw
  at 124°) and the lower jaw down 110° (244°), so both jaws lie outside the blade's edges with the blade's back
  between them. First build: jaws along the edges (133° / 228°), half buried in the blade, and a 32° skull tilt that
  kinked the neck behind the head. `open_jaw` now takes the skull's and the lower jaw's angles apart.
- **The scales** (`neck_scale_textures`, its own set `neck_d / _n / _m.dds`, 4096 × 512): Argent Verdict's scale
  mail (`fist_tex` 'mail': staggered rows of overlapping round scales, each rising to its free edge, the rim dipped
  all round), laid in world units on the snake as laid: along the body by the layout's own arc length (the body is
  compressed along the path, so a grid in the texture's own units would squash), round it by each ring's
  circumference (the rattlesnake's skin UVs: u along the body, v round it). Rows 0.22 apart, columns 0.44 wide, rise
  0.035; free edges toward the tail; on the blade's metal (diffuse, env mask and specular, darker in the rims). The
  head's UV islands stay smooth and the scales fade in over the neck. The other snakes stay smooth.
- **The blade snakes' meeting point** moved from the middle rivet (under the lower jaw now) into the open mouth,
  (-1.75, 28.05): the three come out of the big snake's mouth.
- `gamespine.py` lays no spine any more (its Phong `tessellate` is still the snakes'); the spine's textures are
  deleted from Patch Collection by `tools/02`.

## The Noble mount: neck snake and ring dropped (2026-11-15)

Curator, on the neck snake: "not really what I had in mind, re add the original upper shaft section and the ring
(change the ring to an oroboros". That build (billyro's neck, collar band and rivets back; his hip holder renamed
`ZP_WhisperCollar` so the cup stayed on the axe; its belt ring, a torus of radius 3.0 fitted from the holder, replaced
by an ouroboros on the same circle: `snake.CircleRingLayout`, `holder_ring`) was rendered and then replaced at once:
"sorry changing it again, instead go for a simple spike top and extend the back of the blade to mount like the Noble
axe does" (with a photo of the Noble axe's socket and spike), **"use the noble axe upper shaft for Whisper"**, and a
drawing: a straight shaft from the connector to a spike near y 37, the socket where the blade meets it, the blade's
back drawn out to it along two lines meeting the blade's back edges at about y 25 and y 32. (A horizontal stroke on
the poll side was left out: the Noble axe has no back spike.)

- **The Noble upper shaft** (`noble.py`, shape `ZP_WhisperNobleShaft`): Caenraes' Noble Armory war axe as Pretty
  Enderal Armory ships it (`meshes\weapons\elven\elvenwaraxe.nif`, shape `Noble_Axe_MP`, 5,050 triangles asserted;
  **credit Caenraes**, open with credit as for Argent Verdict). Its pieces by island extents: the twisted steel shaft,
  the collar under the socket, the socket block (fused to the Noble blade, cut away at the Noble's x -1.3), the ring on
  the socket's top and the spike; its grip, ferrule, pommel and blade are not used. Moved onto Whisper's handle axis at
  scale 0.9 with the socket's middle at y 28.6 (between the drawing's lines at the blade); the shaft clipped to start at
  y 9.8, inside the connector ouroboros; the spike's tip at y 38.1. The Noble shape's own normals, tangent frames and
  UVs, on a copy of its own shader: its textures stay on Pretty Enderal Armory's paths (`textures\weapons\noble
  armory\war axe\`), never copied. 1,668 triangles.
- **The blade's back plate** (`ZP_WhisperNeckPlate`, `noble.neck_plate`): an outline along the socket's blade side
  (into the block, x 0.15, y 26.5 - 30.7), the drawing's two lines to the blade's back edges at (-4.10, 32.20) and
  (-2.85, 25.10), and billyro's back edges between them pushed 0.18 into the blade; ear-clipped and extruded ±0.80
  (the blade's flat is ±0.84), flat faces, wound as the axe's own triangles; the shared blade-steel set. 32 triangles.
- Billyro's neck tube, collar band, collar rivets and upper shaft are cut again; his hip holder (`Scb`) is hidden again.
  The blade snakes meet at the middle rivet (x -1.52, y 27.52) again. `snake.NeckLayout`, `CircleRingLayout`,
  `neck_scale_textures` and `holder_ring` stay in the code, unused (the scale mail could go on any snake).
- The mesh is 1.0 MB, ~49,000 triangles.
- **One metal, a closer blade** (curator: "placement is good but the metals need to align the shaft from Noble needs
  retexturing to the same metal as the blade and bring the blade closer into the shaft and make the connection look
  more seemless, remove the yellow from the Noble elements"):
  - The Noble pieces now use a copy of the **blade's shader** (env map, billyro's cubemap) and their own generated set
    `noble_d / _n / _m.dds` (`noble_textures`): from the Noble's own diffuse and normal map (Pretty's), the gold inlay
    found by colour (saturation ramp 0.18 - 0.35, red over blue: 24% of the atlas, the unused leather included) and
    painted out with the steel round it (normalised blur, three box passes of radius 6), the steel's brightness kept at
    0.8 of its depth round its median (0.239) and put on the blade's diffuse (0.106), env mask and specular. The normal
    map's relief stays: the engravings read as plain engraved steel.
  - **billyro's blade moved 2.0 toward the shaft** (`noble.BLADE_SHIFT`; `shift_blade`: the blade island, its six
    rivet heads and both blood edges; 490 vertices rewritten in place with `set_positions`, bound spheres refitted).
    Its back's apex now sits inside the socket block, so the plate only fills small wedges above and below it (its
    socket side runs 0.3 past the apex into the block). The relief snakes follow (their snouts and the rivet they meet
    at, shifted). The weapon's reach shrinks by 2 (blade edge x -11.6); the WEAP's bounds are now -12, -13, -2 .. 4,
    43, 3. The collision hull (billyro's, for a dropped axe) is not moved.
- **No plate** (curator, circling its wedge above the socket: "if you move the blade up slightly you can lose this
  additional piece you added"): billyro's back is a V whose point is at y 27.5 with symmetric edges (measured from
  edge crossings; an earlier vertex table put it at 28). Moved **(2.8, 1.1)**, the point sits centred on the socket's
  height (y 28.6) and 2.8 in, and both back edges stay **0.41 or more inside the socket's blade side** over its whole
  height (`tools/02` asserts it from the blade's edge crossings), leaving it at the socket's top and bottom corners.
  Raising alone would not do it: (2.0, 1.3) left a gap below y 27, (2.0, 0) one above 29.8. `ZP_WhisperNeckPlate` is
  gone (`noble.neck_plate` stays in the code, unused). The relief snakes' tails now start inside the socket. WEAP
  bounds -11, -13, -2 .. 4, 45, 3.

## Scale mail, the ouroboros on the shaft, ruby eyes, one root (2026-11-15)

Curator, on the in-game build ("composition looks good just a few tweaks"), in four notes:

- **Scale mail on the coil and the ouroboros** ("add the same texture pattern you used on the Argent Verdict palm
  ... to the snake handle and ouroboros ring") and then **on both heads** ("add scales and ruby eyes to the ouroboros
  snake head and the pommel snake head"). `scale_textures` (the retired neck snake's painter, generalised) writes one
  set per snake, `coil_*` and `ouroboros_*`: Argent Verdict's `mail` (staggered rows of round scales rising to their
  free edges, rims dipped) on the blade's measured steel, laid in world units along each layout's own arc length
  (the ouroboros' body is compressed to about a quarter of its length; a grid in texture units would squash).
  - Row pitch = 0.7 snake units x the body scale (`SCALE_PITCH`): 0.105 on the coil, 0.091 on the ouroboros, about
    15 scales round both (as on a real snake). The neck snake's 0.22 gave ~7 round and read as cobbles.
  - Texture width per snake: the narrowest of 2048 / 4096 / 8192 that gives every row 8 texels (`SCALE_MIN_TEXELS`;
    4096 gave 4.6 a row on the coil). Both came out 8192 x 512 (~14 MB a set with mips).
  - The head's UV islands lie apart from the body's strip (the skull seen from above, the lower jaw's halves beside
    it), so the head's lattice comes from the surface: each head texel rasterised to its point on the snake, along =
    the layout's arc length at its height, round = its angle from the back x the cross-section's mean radius there,
    texel sizes per triangle for the normal map, the islands' gutters filled 6 texels out (`raster`, `texel_sizes`,
    `grow_into`). The mouth's floor (the rattlesnake's second, 47-vertex island) is dark and dull (`MOUTH_DARK`): its
    flat plate caught the cubemap as pale shards between the ouroboros' open jaws.
  - The blade snakes stay smooth.
- **The ouroboros was buried** ("tidy this up as the ouroboros is clipping, needs to be more visible"). It lay on
  the grip's ellipse (0.85 x 0.62) while the Noble shaft came down into its middle (y 9.8, ring 8.96 - 10.24), so
  only 0.2 - 0.4 of it stood out. The shaft's open lower end is round and **fluted**: six ridges at r 0.974,
  grooves at 0.851, on the handle axis (measured by `tools/02` from the Noble shape). Now:
  - the ring rests on the ridges' circle (+0.02), centred on the shaft's lower end (`snake.RING_Y` 9.8), thicker
    (head 0.17, body 0.13: 1.06 tall, 0.78 thick); `tools/02` asserts no ring vertex inside the ridges above y 9.8;
  - the grip flares from its ellipse to just inside the grooves over y 9.3 - 9.8 (`GRIP_FLARE`) and runs on to
    y 9.95, plugging the shaft's open end, so no slot shows under the ring. billyro's handle triangles past the old
    band are long (y 9.54 to 20): the grip now takes every handle triangle starting below its top and clips it;
  - the head lies on the ring's **tangent** (`RingLayout(tangent_head=True)`), resting at its hinge (`RING_TOUCH`
    0.65 head lengths from the snout), its ends standing off; the body leaves the head straight and joins the ring
    over 0.6 head lengths through cubic Hermite curves (`RING_RISE`). As a chord its middle sank 0.7 into the shaft.
  - **only the lower jaw drops** (`RING_JAW` (0, 24)). A lifted skull turns about the jaw hinge and levers the neck
    behind it down into a fold where the head meets the ring: an even 30 stretched triangles 5x (a spike at the
    throat), (22, 2) 4.3x, (0, 24) 1.24x. The coil's head keeps its even 36 (3x at its neck, hidden in the loop; its
    ruby is fitted to that mouth).
- **Ruby eyes on both heads.** Mihail's mesh has no eyes; they are painted on its skin. At their pupils (the darkest
  texels there, UV (0.0481, 0.3496) / (0.0471, 0.6543); on the head they land mirror-symmetric, x 0.78 +- 2.55,
  y 30.4) `eye_domes` seats a ruby dome (icosphere, radius 0.5 snake units, 0.75 deep, 0.45 of it proud) on the
  ruby's textures: shape `ZP_WhisperEyes`, its own shader copy, so it can glow with the pommel. Coil eyes 0.17
  radius, 1.73 apart; ouroboros 0.085, 0.87 apart (its eyes face up and down the handle: its back faces out).
- **The blade snakes meet in one root** ("bring the right snake a little more to the left so theres equal spacing
  between the base of the snakes", then, on the render: "now the top snakes base so it meets the other two"). The
  bases are where the bodies run under the socket's blade face (x -0.37). Their centre lines crossed it 0.95 and
  1.92 apart; spaced evenly by centre line, the downward body (crossing steeply, so 1.2 wide there) touched the
  middle one while the upward one stood 0.39 off. `snake.blade_tails` now slides both outer tails along y until each
  body's edge lies `BLADE_ROOT_GAP` (0.06) from the middle one's at the socket face (a slanted body's width there:
  `BLADE_ROOT_HALF` / its x direction); the heads stay. Built gaps, asserted on the mesh: +z 0.08 / 0.11, -z 0.07 /
  0.01.
- Mesh 1.06 MB; ~51,000 triangles. Rendered offline (normal maps now in the preview); unverified in game.

## The grip: even leather, no specks (2026-11-15)

- **"this section needs to be the same handle leather"** (curator, circling the band just above the pommel head).
  billyro's leather is near black at the grip's two ends (y < -7 and y > 9: ~0.1 of the middle's brightness): they
  lay under his lower and top handle bands, and their baked shadow survived the burgundy recolour. A brightness gain
  (capped 4x) reached only half and would raise the noise, so `mirror_grip_ends` gives every vertex past
  `GRIP_MIRROR` (-6.9 / 8.7) the UV of its mirror point back across that height, at its own angle, looked up in
  billyro's main UV piece (it wraps the whole way round, so it is searched cut at 0 and at 180 deg; his two thin end
  strips and the caps are pieces of their own). The leather runs on with its grain reflected at the mirror line; the
  ends now read 0.96 / 1.00 of the middle's brightness (asserted 0.85 - 1.2).
- **"spotted the handle clipping here"** (a red speck in the coil's neck), then red flecks on the head's back, both
  sides of the neck. The neck rises from the head's back inside the grip and leaves it through its side, and the
  head is thinner than the grip where it caps it, so patches of leather crossed the snake's skin apart from the
  visible grip: two on the head's back (y -8.05 to -7.78, angles 17-43 and 146-161 deg) and a sliver on the neck
  (y -4.72). `tuck_grip` finds them on the grip's own ellipse (a 1.5 deg x 0.03 grid below y -3.5, three-ray
  inside votes with the loose mouth floor left out): outside cells not joined round the wrap to the visible grip
  above are islands, and grip vertices on or 2 cells from one are pushed in 0.04 under the snake's surface; then
  points sampled over every grip triangle below -3.5 that fall on an island are asserted inside. Two traps on the
  way: a test on the mesh's own points joined the flecks to the visible leather across the 0.05 of head between
  them, and billyro's row there is tall (no vertex between y -8.125 and well above the flecks), so the grip is now
  split 3 x 3 before shaping and cut by horizontal planes every 0.06 over y -8.10 .. -7.56 (`slice_mesh`, shared edge
  points, no T-junctions). Grip 7,416 triangles (was 384); 136 vertices tucked.

## Langets: the socket blended into the blade (2026-11-15)

Curator, circling the socket's blade side on both faces: "how can we blend these 2 elements together better?";
offered langets, a flared lip, a snake-root boss or a steel fillet, picked **langets** ("two tapered steel straps
run from the socket onto each blade face, riveted ... The snakes' root comes out from under their ends").

- The socket stands well proud of the blade: its side panels at z +-1.5 .. 2.1, the blade's faces at +-0.844. Each
  langet (`ZP_WhisperLangets`, `langets`) is a tongue on its blade face: from x -0.2 (inside the socket's chamfer:
  its blade face is at x -0.37, its panel edge -0.03) to a rounded tip at x -2.0, 3.8 wide at the socket narrowing
  smoothly to a 0.7-radius tip (`langet_half`); its height over the blade ramps 0.6 -> 0.32 toward the tip and
  rounds off over 0.14 at its edges, sinking 0.03 into the blade (`langet_height`); a structured mesh, dense at the
  tip and the edges. `LANGET` holds the numbers.
- Texture: the socket's own steel. Its side is several facets mapped to scattered strips of the Noble atlas, so
  mirroring the panel put seams on the langet; `panel_uv` instead projects each langet linearly into the strip the
  socket's main side facets use (picked as the facet group with the largest UV box), at their own density
  (0.03 UV a unit) and orientation, x mirrored out of the socket. The -z face's strip carries engraved arcs, so both
  langets take the +z face's.
- billyro's own middle rivet head (hidden in the socket since the blade moved) copied onto each langet at x -1.0,
  0.62 across and 1.2 tall (scaled evenly it stood 0.03 proud and vanished), turned to the langet's slope
  (`ZP_WhisperLangetRivets`, billyro's textures). Seat it on its own underside: `face_height` there returns the
  rivet's top, and the first build buried it 0.12. Asserted proud.
- The blade snakes' tails now end under the langets' tips (0.45 in, 0.36 apart: `LANGET_TAILS`), so all three come
  out from under each tip; their bodies are shorter, squashed to 0.24 - 0.35 of their length (smooth metal, nothing
  shows; `BladeLayout.STRETCH` floor 0.2). Asserted: no snake vertex within 0.13 of a langet's top where it stands
  full height. `snake.blade_tails` (the single root at the socket face) is unused now.
- Mesh 1.42 MB. Rendered offline; unverified in game.
- **"It doesnt look aligned"** (curator, on the first langets). Two faults:
  - The Noble mount leaned. Its own shaft is not parallel to its y: placed by one axis point (`NOBLE_AXIS`), the
    mount's centre drifted front to back from z -0.05 at the shaft's foot through +0.21 at the socket to +0.28 at
    the spike (0.72 deg), so the socket stood 0.6 off the blade on its +z face and 0.15 on its -z face. `noble.
    upper_shaft` now fits a line through the centres of its round parts (`LEAN_BANDS`: shaft, collar, ring, spike;
    the socket block left out) and turns the mount upright about x onto the grip axis (z 0 at the shaft's foot);
    side to side it was true (centre x 1.251 at every height, asserted).
  - The langets were centred on the nominal socket middle (y 28.6) and 3.8 tall, so their top edge met the socket
    below its top corner and their bottom ran into its V. `socket_fit` measures the socket's flat blade-side face
    (the Noble vertices at its x: y 27.26 .. 30.87, middle 29.06, which is also the middle blade snake's snout): the
    root spans it (less 0.06 each end) and the tip, rivet and snake tails centre on it. Each face's root height is
    the socket's own surface over the blade there, less 0.03 (0.40 on +z, 0.38 on -z now the mount is upright), so
    the langet runs on under the socket's chamfer.

## The neck off the top of the head; dark purple and amethyst (2026-11-15)

Curator, in game, with two lines drawn from the head's back down the grip into the first turn: "just need to fix the
neck of the snake leading to the head", and "change the leather handle color to a very dark purple and the crystal
pommel and snake eyes to purple amethyst". Then, on the renders: "the neck still doesn't connect", "I don't want the
snake to clip through the handle", "darken the leather handle even more, almost black", "I want the neck to connect to
the top of the head on the pommel not from underneath" with an S drawn on the view from -z ("like this"), and last
"almost just to fix this handle clipping and make the neck attach to the head smoother".

- **What was wrong.** The neck was a cubic from the occiput up the axis, half inside the grip (mid-neck 0.96 of the
  grip's radius from the axis, body 1.2 wide), out round the -x side into the coil: it left the head from underneath
  and the leather showed between them. Behind it all: `open_jaw` turns the head up 18 deg about the jaw hinge, which
  swings the head's back 0.55 into the grip on the -z side (its top met the grip at y -7.8, 1.3 below the occiput), and
  the snake just behind the jaws (1.43 wide) is narrower than the grip (1.70): nothing behind the head can lie on the
  leather without leaving the axis.
- **The path now** (`snake.CoilLayout`): in front of the hinge on the axis as before (snout, jaws, crystal untouched);
  from the hinge the centre line lifts onto the grip's -z face (the side the head's top faces) over `NECK_LIFT` 1.8 by
  a smootherstep (a smoothstep's curvature switching on showed as a seam across the head's top). Round the grip
  (`psi_of_y`) the neck goes straight up from the middle of the head's top, swings out toward -x (`NECK_SWAY` 0.75 rad,
  peak y -5.5, smootherstep from 1.55 above the hinge) and comes back across the face into the coil, joining the helix
  at y -4.6 with the helix's own slope (cubic Hermite): the coil's turns above are where they were.
- **Tried and dropped:** a lift from the occiput (bare leather between the head and the neck's start, the neck coming
  out of the grip as a stub); a longer lift, 2.4 (the same); the old cubic pushed radially out of the grip (three
  kinks: its push direction jumped, a hard limit, a 0.06 step at the coil; then "from underneath"); keeping the head's
  back round the grip (`ENCLOSE`: the neck sank 0.29 into the leather); sections upright at 0.9 (a thin waist).
- **No creases.** The head's back is 1.4 deep; bent onto the face on a curve tighter than its half-depth, its top
  folded into itself (20% of the skin points there overlapped: a point just inside the skin read outside). The
  sections through the lift turn only half as far as the path (`UPRIGHT` 0.5, `Layout.upright`), and the coil's belly
  depth is smoothed along the path (`H_SMOOTH` 0.15: the belly line is piecewise linear in 300 bins and where it changes
  fast each corner bent the centre line; the coil had a 795 deg/unit spike near its tail too). The coil's belly line
  is measured on the head tilted but with its jaw shut (the dropped throat lay deeper than the neck's belly).
- **Settled onto the leather** (`settle_neck` in 02): the smoothed belly line left the neck up to 0.12 over the -z face
  in places and touching it in flecks elsewhere. Over y -6.6 .. -3.3 the build measures the grip's surface point
  under the centre line against the snake and corrects the belly depth (`h_fix`, blurred over 0.2 of arc, faded in and
  out over 0.8) until the belly lies 0.02 - 0.15 inside the leather all along (the coil's own turns sink ~0.09 - 0.12);
  it settles in 2 rounds. Below y -6.2 it would not converge (the thin neck meets the head's throat fold there).
- **The slot on the head's top** was the grip's end: right behind the jaws the head's skin lies 0.0 - 0.1 under the
  grip's -z face, and with the head lifted that patch reached round to the open throat, so the tuck took it for
  visible leather. The grip's -z half is narrowed over its last stretch inside the head (`END_TUCK` 0.3 at its end,
  from y -7.3; `end_tuck`, also in `grip_point`). The tuck itself now repeats (a triangle whose surface still shows has
  its vertices tucked a `TUCK_DEPTH` deeper next round) and a patch over `TUCK_ISLAND_MAX` cells counts as visible
  leather, not a fleck. Final build: no poking cell left, the grip's end ring inside the head.
- **Scale texture fix (all snakes).** `scale_textures` mapped texture u to the snake's height by binned medians, which
  snapped to the body rings' heights: every third bin repeated its neighbour's, a flat step over 60 texels where the
  rows stretched into long pills (a "collar" across the neck once it lay on top). Now each ring's height and median u
  (82 rings of 11 vertices, strictly ordered), joined linearly. Coil rows get 14+ texels (was 8.5), and the ouroboros
  set fits 4096 wide (was 8192).
- **Colours.** Leather `LEATHER` (0.050, 0.016, 0.072), `#0D0412` at its 75th-percentile brightness (luminance 0.032;
  the first purple, `#1C0928`, matched Midnight Sting's very dark green and was "darken ... even more, almost black").
  Crystal and eyes `AMETHYST` (0.40, 0.11, 0.64) on the same soul-gem texture, written as `amethyst_d/_n/_m.dds`; the
  old `ruby_*.dds` were deleted from Patch Collection.

## The test plugin (2026-11-15)

Curator: "build the weapon so I can see in game". `tools/03-build-records.py` writes two records into
`WhisperESP/` on Argent Verdict's pattern (it refuses if a copied record changed hands):

- **800 WEAP `ZP_Whisper` "Whisper"** = EGO's Aeterna War Axe `07C992` (EGO wins it; unenchanted, no template, no
  EGO-defined reference): **30 damage, crit 21, speed 0.9, value 1200** (provisional: between EGO's forged Aeterna War
  Axe 28 and Uunil'Yâr's Promise 35); keywords war axe, Aeterna material (EGO's smithing perks, as Argent Verdict),
  melee, unique, no enchanting; no vendor keyword. Model `Zenderal\Whisper\Whisper.nif` (the old texture hashes
  dropped), bounds measured from the mesh's visible shapes (-14, -13, -2 .. 3, 43, 2; the hidden hip holder left
  out); its sounds, impact sets and block material stay EGO's (vanilla axe ones).
- **801 STAT `1stPersonZP_Whisper`** = `1stPersonElvenWarAxe` `036BCC` (vanilla wins it) on the same mesh: the
  weapon's first-person model.

Every reference resolves in the masters. Built with Spriggit 0.40.0 (4 records, ESL, HEDR 1.70) and copied into
Patch Collection; it must be ticked in MO2. In game: `help whisper 4` gives its form ID, then `player.additem <id> 1`.

## The souls: charge, glow, Soul Cleave, soul trap (2026-11-15)

Curator, once the look was final ("it looks great now we need to work on the actual effects and what the Unique
does"), picking from offered options: "5 souls, eyes then crystal"; Soul Rend; "Soul trap on kill". The charge went
three ways in one evening: every Entropy spell with a drain the axe added (an option I had recommended over the
curator's own idea; records 807/808 retired), then the curator's "Absorb spells charge the weapon..... meaning any
spell that absorbs health mana or stamina in the Entropy category" (only Triumvirate's three Shadow drains qualified,
and finding them in the console was a chore: "yikes"), then **"lets make it entropy spells in general"**, with no
drain from the axe. Soul Rend gave way to **Reaping Souls**: "I don't actually see any Soul Tear effect when power
attacking. the reaping souls seems more impactful" (the Papyrus log shows Soul Rend did fire and deal its damage,
139 to three goblins at 20:19; its soul streams were too faint to read). Then "remove the enchantment visual effect
coating the weapon in purple". Built on Argent Verdict's verified pattern (an enchantment whose effects are gated by conditions,
a global for the charge, an ability that re-sets glow nodes while the weapon is in hand). Masters stay Skyrim.esm,
Update.esm and Forgotten Stories; every visual and sound is vanilla (Enderal keeps them). Needs powerofthree's Papyrus
Extender. `tools/03` checks the numbers it writes on the item card against the scripts' constants.

- **Charging** (`ZP_WhisperSoulsScript`, ability 806 via MGEF 804; `ZP_WhisperEquipScript` on the weapon gives it while
  the axe is in either hand and takes it back when it is in neither). PO3's `OnMagicHit`, registered on the ability's
  effect, reports the player's magic landing (its `akTarget` parameter: the event is the caster's, as Sting's
  spiderlings use `OnWeaponHit`). A spell counts when one of its effects is hostile (flag 0x1) and of Conjuration,
  Enderal's Entropy (`GetAssociatedSkill`); the target must be a living actor hostile to the player. The axe adds no
  drain. Each counts as one soul at most every 0.75 s (a beam or cloak lands again and again): the soul stream
  from the enemy to the player (`SoulTrapPVFX01` 0531AF on the enemy aimed at the player, `SoulTrapPVFX02` 0531B1 on
  the player aimed at it, 1.5 s), the soul trap shimmer 054223 on the enemy, and a soul (GLOB 803, `Mod`, up to 5);
  the fifth plays the charged sound (below). Each soul logs `[ZP Whisper] soul n/5 from <spell> on
  <actor>`. Death Breath, Death Spark, Soul Trap, Chaos Nova, Grave Curse, the Triumvirate Warlock and Shadow spells,
  Kata's Death Beam and curses and Apocalypse's Entropy set all count (the absorb-only build's PO3 archetype /
  actor-value test is in git history, if wanted back).
- **The glow** (`tools/02`): copies of the four eye domes, one per soul, each brighter (emissive 0.4 / 0.8 / 1.3 /
  1.9 / 2.6), and of the crystal (2.4), 0.01 out along their normals, each on its own copy of the gem's shader with
  Own_Emit on (`GLOW_COLOUR` amethyst light), each under its own node at scale 0: `ZP_WhisperSoul1..5`,
  `ZP_WhisperBlaze`. `Show` sets the node for the souls held (one at a time) and the blaze at 5 to scale 1 with SKSE
  `NetImmerse.SetNodeScale` in both views, again every second (a weapon's 3D is rebuilt with its nodes at scale 0 on
  equip, load and race change). The circling wisps the curator's option mentioned are not built: a weapon runs no
  controllers (Argent Verdict's motes stand still), so they need another route.
- **Charged, ready** (curator, after the first in-game look: "its also not obvious if the weapon is charged ready to
  trigger the power attack, we need a glowing purple light coming from the pommel crystal"): inside the blaze node a
  halo of Candlelight's two flare sprites (vanilla `magic\LightSpellActorFX.nif`: "Flash", a soft glow disk on
  FXGlowSpotLinear, 4.2 across; "Circle02", a bright flash on FXBrightFash01, 2.4 across; additive), each on its own
  camera-facing billboard node (the vanilla node's mode 2, the node type Argent Verdict's motes use on a weapon) at
  the middle of the crystal below the jaws (1.25, -11.89, -0.07); copied with their own effect shader and alpha
  blocks, no controllers, shader colour purple at alpha 1 (Candlelight's controllers raise it from 0), vertex colours
  repainted purple with the rim's alpha fade kept. And a real light: ability 806's second effect 80D, a constant
  Light effect (vanilla `LightFFSelfConstant` 146677's shape, no orb, no sounds, hidden) on LIGH 80C
  (Candlelight's `MagicLightLightSpell01` 03FA58 in purple `#B450FF`, radius 320), conditioned on 803 >= 5: it comes
  on within a second of the fifth soul and goes out after the release (an ability's effect conditions are rechecked
  about every second). Where the engine hangs a Light effect with no art is unverified (the wielder, it should be).
  And a sound (curator: "add this sound when its fully charged", their licensed Motion Audio file
  `MA_MotionAudio_SpookyBreath_02.wav`, a 5.25 s spooky breath): `tools/04-install-sound.py --charged <file>` converts
  it with Argent Verdict's converter (24-bit / 48 kHz stereo -> 16-bit / 44.1 kHz, the game plays no 24-bit PCM;
  dithered, level untouched, peak -3 dBFS) into Patch Collection's `sound/fx/Zenderal/Whisper/WhisperCharged.wav`
  (not committed); SNDR 80E (Argent's charged bell's record shape: vanilla category 0172A1, output 0F1B1A) and SOUN
  80F, which the souls script plays on the fifth soul. The release rings the soul trap's capture sound.
- **The purple Smite orb** (curator, the same evening: "still need to add aditional glow effect of some kind to the
  pommel crystall", then "add a purple smite orb shining on the crystal" / "something like the smite orb but glowing
  purple", "Only at 5, much stronger"): Prophecy's Smite orb (Kittytail's Holy Templar `meshes\lightpower\
  holyboltproj.nif`, the copy Patch Collection ships; `tools/02` `add_orb`, `ORB_PARTS`) on the crystal, inside the
  blaze node beside the halo: its static parts, each on its own billboard (the orb's own node mode 4, the one
  Argent Verdict's motes use, verified on a weapon) at the same middle: the core flash `Circle05` 3.4 across, the
  wisps `Wisps04:0` 10 (a ray burst round the core here) and the wide soft glow `Flash03` 13, each at about twice the
  orb's emissive multiple (2.4 / 1.4 / 1.6). Its vapour halo `Halo:0`, a wispy purple ring 7.5 across, was in the first
  build and came off the same evening (curator: "can you cut the out ring of the orb so its just the shining
  centre?"); its palette went with it. Its two particle systems (the sparkles) are left off, and its
  shaders' UV scrolls dropped: a weapon runs no controllers, the vapour stands still. **How the purple is made**
  (Bottled Shaders' `Effect.hlsl`, read in the installed mod): a palette shader's colour is `multiple x palette(texture
  green, shader colour red x vertex red)`; the shader and vertex colours only pick the palette's row (the orb's
  `Circle05` runs from row 1 at its centre to row 0 at its rim through its vertex reds), so they stay the orb's, and
  its palette is written purple instead: the game's own `GradHealMagic` (not Glorious Gradients' recolour),
  brightness normalised and laid on `ORB_RAMP` (black -> violet -> lilac), alpha kept, as
  `textures\Zenderal\Whisper\WhisperOrb_gradhealmagic.dds` (256x64, BC7; the ring's `gradtelekinesis01` copy is
  deleted by the build). `Flash03` has no palette: its vertex colours purple. Offline preview (the shader's formula,
  composited over the render): a white-hot purple core with a ray burst and a soft purple glow round the crystal.
- **The blade snakes' orbs** (curator: "just like the pommel glow effect can you add 3 very small glowing orbs (with no
  outer circles) to the 3 snakes snakeheads on the Axe blade. each side", "when its charged I mean"): six tiny copies
  of the pommel's orb, its bright core `Circle05` (0.7 across, x 3.0) and soft glow `Flash03` (1.5, x 1.4) only, each
  part on its own billboard inside the blaze node (lit with the crystal at 5 souls). Each sits on its relief snake's
  head between the painted eyes (`eye_domes`' two points on the head, Mihail's UVs, which `snake.build` returns for
  the blade snakes too), `BLADE_ORB_LIFT` 0.06 above the crown (the highest snake vertex within 0.45 of that point;
  the crowns stand at z +-1.27 there). **No soft fade** on them (`SLSF1_SOFT` cleared): a sprite lying on the blade,
  with the head 0.06 and the blade a little more behind it, would fade to nothing under any soft depth; the z-test
  edge that replaces it is hidden face-on. Preview (both faces, and 30 degrees off): a small purple light on each
  head.
- **Soft depth** (found building the orb): every sprite on the crystal, the halo's too, now fades within 0.75 units of
  what stands behind it (`SOFT_DEPTH`; the shader's soft depth: alpha x (scene depth - sprite depth) / soft depth).
  Candlelight's "Flash" brought 128, made for a glow floating in the air; on the pommel, with the snake's head, the hand
  and the body a few units behind, it faded the halo's soft glow to almost nothing (its "Circle02" had 8).
- **Soul Cleave** (`ZP_WhisperCleaveScript`, MGEF 805 on the item card). The third release of the evening: Soul Rend
  fired but its soul streams were too faint to see; Reaping Souls' five orbs were "very underwelming"; the curator
  then asked for "a horizonal purple slash the fires out in a conal wave infront of us dealing magic damage". Enchantment
  802 starts it on the enemy a power attack hits while 803 is 5 and the target is hostile (`IsPowerAttacking` on the
  player; this trigger is verified by the Soul Rend log). It claims the souls (`Mod`, thread-safe), puts the glow out,
  rings the capture sound and plays the soul trap stream round the player, then RemoteCasts spell 80A, blamed on the
  player, from an empty activator (`FXEmptyActivator` 0B79FF) 120 units ahead of the player at 95 up, at one 1500
  ahead at the same height: straight out along the player's facing and level, whatever the camera's pitch. Starting
  120 out clears every player magic node by more than RemoteCastAimFix's 64, so Hit Where You Aim leaves it alone
  (Argent Verdict's orbs launch the same way, verified). A struck enemy nearer than 120 (inside where the wave begins)
  takes 80A directly (`DoCombatSpellApply`). The wave: spell 80A (Aimed) with effect 809 (80 Health damage,
  ResistMagic: magic damage; Destruction so it never feeds the axe; hostile actors only; the soul trap shimmer as hit
  shader) on projectile 811 = Fire Breath's wave `VoiceFireWaveProjectile01` 0647BF (a Cone projectile: it passes
  through and hits every actor in its cone; speed 1500, range 1000, spread 12, collision radius 64) with light 810
  (Candlelight's in purple, radius 400: it lights the ground it crosses) and flight sound SNDR 812 (Kittytail's
  `DarkWarriorSlashProj.wav` from A Dark Warrior's Tale's archive, by path; positional output 0FD93D). The mesh,
  `tools/05-soul-wave.py` -> `WhisperWave.nif`: a horizontal crescent (arc radius 170, its centre 110 behind the origin,
  68 deg each side: 322 across, the crest 100 ahead), three layers along it, each tapering to points at the tips and
  fading to its edges in vertex alpha: a wide purple glow lying flat (80 across), a narrow lilac core (22) and an
  upright purple ribbon (60 tall) so it still reads edge-on from behind; each on its own copy of Candlelight's "Flash"
  soft-glow shader (FXGlowSpotLinear, additive), coloured, double-sided, no controller; in vanilla
  `Effects\FXEmptyObject.nif` with its spinning child node left off the root. A Dark Warrior's Tale's own slash meshes
  were looked at first: Shadow Carve's are skinned claws raking the ground, Bloodletter's a slash that stays at the
  caster; neither is a crescent that flies. Logs `[ZP Whisper release] souls claimed; the wave thrown`. Reaping Souls'
  records 809-811 (and Soul Rend's before them) were repurposed; its orb mesh, palettes, tool and script are gone.
- **The release on the swing** (curator, later that night: "make the the power attack not require a hit to trigger
  the wave"): the release is a Global function now (`ZP_WhisperCleaveScript.Release`), and its main caller is the souls
  script (804, on the player while the axe is in hand): it registers for SKSE's actor action 0 (weapon swing) and, on
  a swing whose source is Whisper (800) while 803 is 5 and powerofthree's `IsPowerAttacking` says the player is power
  attacking, releases at once, hit or miss. With no struck enemy, the blows inside where the wave begins come from a
  scan: every living actor hostile to the player within 120 and 70 degrees of the player's facing takes 80A directly.
  Enchantment 802's Soul Cleave effect (805) stays as the item card's text and as a fallback for a power attack whose
  swing the game never reported (a clip without a `weaponSwing`): the swing comes first, so normally the souls are
  spent by the hit and its conditions fail. The log says which path released (`souls claimed on the swing` / `on the
  hit`). Unverified in game: whether every power-attack clip in the list reports its swing in both views.
- **The Soul Wisp** (curator, the same message: "if the wave kills an enemy, let it spawn a purple wisp"; asked what
  it does, "Fights for you"; then "the wisp lasts for 30 seconds, only 1 wisp at a time"). Midnight Sting's spiderling
  pattern on Enderal's own Wisp:
  - **the mark** (813, `ZP_WhisperWispMarkEffect`): the wave's first effect (its spell 80A carries it before the
    damage, so it lands before the kill; base cost 0, so the damage stays the costliest effect and the projectile is
    the wave's), hidden, 1 s, `NoDeathDispel`, hostile actors only, so every enemy the wave hits (in its cone or
    directly) carries it. When it ends on a corpse (vanilla soul trap's test: `OnEffectFinish`, then `IsDead`) a wisp
    rises from the corpse (`PlaceActorAtMe`): Health 40 + 4 per player level, the player's teammate, sent after the
    nearest enemy within 2500.
  - **one at a time**: the new wisp fades the one out (`Disable(True)` + `Delete`), except that a wisp that rose within
    the last 2 s stays (one wave killing several raises one wisp). FormList 814 holds the wisp out; each wisp stamps
    the game time it rose into its `Variable08`, and a wisp that finds a newer one in the list fades itself (two
    marks ending at once).
  - **the wisp** (815 "Soul Wisp"): Enderal's Wisp `_20E_IrrlichtGrouped` 0D0D69, EGO's record (EGO wins it), with its
    scripts (EP on death, which pays a killer of None; the ghost script; combat music), its loot, EGO's perk (Whisper
    masters only vanilla and FS), its respawn and template flags dropped; the player's level, `PlayerFaction`,
    aggressive and helping friends, SureAI's `_DefaultFollowPlayer`, Enderal's `_00E_SummonedCreature` keyword. It
    fights with its race's attack (Wisp's Kiss 091F78 on its strike: small damage, slows, hampers Magicka).
  - **its ability** (816 / 817, `ZP_WhisperWispEffect`): plays the purple glow once its 3D is in, stamps its end time
    into `Variable07` (30 s of real time at the current timescale, kept across loads), checks the clock every 0.5 s and
    fades away when its time is up; with no live hostile target it goes for the nearest enemy; killed, it fades 2 s
    later. Each step logs `[ZP Whisper wisp]`.
  - **purple**: a Wisp's glow is not its body (`Witchlight.nif`, a tiny sphere) but `WitchlightMesh.nif`, which
    vanilla's `FXWitchlightAttachSCRIPT` plays on it from the race's ability `AbWitchlight` 08CDD1. So the wisp has its
    own race (818, EGO's `WitchlightRace` 013209 without 08CDD1 and without EGO's own keyword 0008C7), skin (819 / 81A,
    `SkinWitchlight` / `NakedWitchlight` for that race, same mesh), and its own glow: visual effect 81B on art 81C on
    `tools/06-soul-wisp.py`'s `WhisperWisp.nif`, the vanilla glow mesh byte for byte but for its colours: its swirl
    spheres and main glow repointed at a purple copy of their palette `GradWhitchlight` (a palette shader takes its
    colour from the palette alone), its body a purple copy of `FXfluidStream01` and a purple emissive (0.70, 0.30,
    1.0), its rainbow glare and glow streak purple shader colours. Its controllers stay (an actor runs them). Not
    previewed (skinned shapes; the offline renderer draws none).
- **The wave where the player aims** (curator, the next message: "make the projectile from the power attack fire where
  the player is aiming rather than always just horizontal to the player"). Papyrus has no camera, and the player's
  own angles are not the aim in third person: True Directional Movement turns the body away from the crosshair
  (`bFaceCrosshairWhileAttacking = 0` in the list's MCM settings). Hit Where You Aim does not help either: the wave is
  a remote cast, which it leaves alone by design (RemoteCastAimFix), and its crosshair aim runs only for auto-aimed
  launches. So `ZenProphecyRage.dll` 1.10.0 (Prophecy's, already in Patch Collection) gained one Papyrus native,
  `ZP_Aim.CameraAim()` (`src/Prophecy/Scripts/source/ZP_Aim.psc`): the render camera's position (`WorldRootCamera`)
  and the camera root's +Y axis, the frame SpellAimTrace measured shots against. `Release` starts the wave on that
  ray, 120 units past the point of it abreast of the player's chest, aimed 1500 further along it: it flies along the
  crosshair, up or down, in both views. Without the DLL (the native unbound) it falls back to the player's look
  angles from the chest (`GetAngleX` positive = looking down). The direct blows inside where the wave begins take the
  aim's heading instead of the body's. The log line gives the aim vector and its source.
- **The poof** (curator: "add this to the special power attack wave on trigger", their licensed
  `02. Cartoon Poof SFX.wav`): SNDR 822 / SOUN 823 (stereo kept; output `SOMStereoRad03000_verb`, the wave's flight
  sound's), played on the player by `Release` with the capture sound. Installed by `tools/04 --poof`.
- **The wisp's whisper** (curator: "add this whisper sound effect looped for when the Wisp is active", their licensed
  `MA_MotionAudio_GhostWhispering_03.wav`, 46.5 s, 24-bit / 48 kHz stereo): `tools/04 --wisp` converts it to 16-bit /
  44.1 kHz mono (the game places only mono sounds in 3D) and makes it loop without a seam (its last second faded,
  equal power, into its first; 45.5 s); SNDR 820 (looping, `SOMMono01800_verb`: heard within 1800 units) / SOUN 821.
  The wisp's script plays it with the glow and stops it whenever the wisp goes (`Sound.StopInstance`). It peaks at
  -11 dBFS as the curator's file does, so it is a quiet bed. A sound instance is not saved: a wisp out over a save
  and load stays silent for the rest of its 30 s.
- **The wisp's burst** (curator: "If you hit the Wisp with an Entropy spell it explodes reducing enemies magic
  resistance by 15% and gives 30 mana to the player"): the wisp's script bursts it when the player's Entropy spell
  strikes it (`OnHit` with a spell that has a hostile Conjuration effect, or such an effect landing:
  `OnMagicEffectApply`; Enderal's Entropy is Conjuration, the souls' own test): a purple flash where it was (81F: the
  Wisp's own death explosion `wispDeathExplosion` 0F1189 without its stray armour enchantment and its screen flash, on
  `tools/06`'s `WhisperWispBurst.nif`, vanilla `ExplosionIllusionLight01.nif` with its two palettes, which Glorious
  Gradients makes teal, repointed at purple copies of the game's own), **Soul Rupture** (81E / 81D: magic resistance
  -15 for 15 s, Detrimental + Recover, Alteration so it feeds no souls, the soul trap shimmer) RemoteCast from the
  player onto every living actor hostile to the player within 400, and 30 Magicka back to the player along a soul
  stream. The 15 s is ours (the curator gave no time). A wisp a killing Entropy spell drops still bursts: `OnDying`
  waits 0.3 s for the hit before it fades. Logs `[ZP Whisper wisp] ... burst by <spell>`.
- **Soul trap on kill**: enchantment 802's first effect is 80B, vanilla `EnchSoulTrapFFContact` 05B452 verbatim (its
  script and properties: Enderal's own soul trap script fills a soul gem when the target dies in time, as Forgotten
  Stories' Souleater's Mace does; its shimmer on the target) **without its enchant shader 05D607**, which coated the
  whole axe in purple in game (Glow Be Gone did not remove it). Names English only (the plugin is not localized), so
  the record round-trips. 5 s on every hit; charge 3000 (cost 1 a hit).
- **Balance, unverified**: 5 souls from any Entropy spell, a wave of 80 magic damage to every enemy in its path. Argent
  Verdict for comparison: 8 light hits and 20 Mana for 80 + 40 on up to 4 enemies plus orbs.
- **First in-game test**: equip Whisper again once after installing (an axe already in hand when the plugin loads
  gets no equip event, so no ability), cast any Entropy spell at enemies (Death Spark: a soul a hit; Death Breath: a
  soul each 0.75 s), watch the eyes step up and the crystal blaze, then power-attack an enemy; the Papyrus log shows
  each soul and the release.

## Regenerate

```
python src/Whisper/tools/01-convert-stalwart.py    # LE -> SE base mesh, read back and asserted
python src/Whisper/tools/02-build-mesh.py          # Whisper.nif + textures into Patch Collection (--out-root <dir> for a dry run)
python src/Whisper/tools/03-build-records.py       # WhisperESP/ YAML (needs 02's mesh deployed: the bounds)
Spriggit.CLI.exe deserialize --InputPath src/Whisper/WhisperESP --OutputPath "<Patch Collection>/Zenderal - Whisper.esp"
```

Rerun `03` after a mesh change (the bounds) or after EGO changes the Aeterna War Axe. `04-install-sound.py --charged
<MA_MotionAudio_SpookyBreath_02.wav> --wisp <MA_MotionAudio_GhostWhispering_03.wav> --poof <"02. Cartoon Poof
SFX.wav">` installs the curator's three sounds (licensed; not committed; each flag optional);
`05-soul-wave.py` writes Soul Cleave's purple crescent (from vanilla meshes only); `06-soul-wisp.py` writes the Soul
Wisp's purple glow (`03` checks its path). Compile the five scripts (`papyrus-compile`, own source first) after a
`.psc` change (Prophecy's script source on the import path too, for `ZP_Aim`) and copy the `.pex` into Patch
Collection; `ZP_Aim.pex` and `ZenProphecyRage.dll` (1.10.0+) ship with Prophecy in Patch Collection.

## Status

2026-11-15: base mesh converted; round 3 (the game's spine in dark iron) built and deployed into Patch
Collection, replacing rounds 1-2; then the snake grip (thinned grip, Mihail's rattlesnake coiled up it, its open
mouth holding the shortened ruby); then spine and snake in the blade's smooth steel and the grip's leather dark
burgundy. The written mesh (688 KB, 8 shapes) reads back in nifse; every added shape's
geometry, UVs and shader uniqueness asserted, collision kept. Rendered offline (textured preview). Test plugin
(weapon + first-person static) built and deployed the same day, so the curator can hold it in game; **not yet seen
in game**.
Later the same day: the Noble mount, then scale mail on the coil, ouroboros and both heads, ruby eyes, the
ouroboros moved onto the Noble shaft's lower end, and the blade snakes' single root (section above); deployed,
unverified in game. Then the neck off the top of the head in the curator's S, the grip near-black purple, crystal
and eyes amethyst, the grip's end slot closed and the scale texture's pill bands fixed (section above); deployed
with the plugin rebuilt; checked in offline renders only. A slight pinch remains where the neck leaves the head,
seen from the side (±x). Then the souls (section above): charge from Entropy spells, the glow, Soul Rend and soul
trap on kill; then absorb-only charging, then (the same evening) every Entropy spell again, the purple coating
removed, the charged halo, light and sound, and the release twice replaced (Soul Rend, Reaping Souls' orbs, now Soul
Cleave's purple wave); all installed; Soul Cleave unverified in game. Then the purple Smite orb on the crystal at a
full charge and the sprites' soft depth (section above); mesh and palettes installed, checked in an offline preview
only; the orb's outer ring came off the same evening. Then the release on the swing (no hit needed) and the Soul Wisp
(section above): plugin (813-81C), five scripts and the wisp's glow installed; the plugin round-trips through Spriggit
and masters only vanilla and FS; nothing of it seen in game. Then the aim (the camera, through ZenProphecyRage.dll
1.10.0's new `ZP_Aim.CameraAim`), the poof, the wisp's looping whisper and its Entropy burst (sections above); DLL,
plugin (81D-823 added), scripts, meshes, textures and sounds installed; the plugin round-trips; unverified in game.
Next: the curator's in-game test (re-equip the axe first): the charged look (orb, halo, light), Soul Cleave on a
missed power attack and along the crosshair (looking up and down, both views), the poof, a wave kill raising a purple
wisp that whispers, fights and fades after 30 s, one at a time, and bursts when struck by an Entropy spell (enemies'
magic resistance, +30 Magicka), the six blade-snake orbs lighting with the crystal; the balance; placement.
