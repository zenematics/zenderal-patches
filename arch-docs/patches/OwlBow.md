# OwlBow — Snowveil, a unique silver bow that needs no arrows

In game **Snowveil** (curator 2026-11-16, "for now"; EditorIDs, files and the plugin keep OwlBow). `Zenderal - Owl Bow.esp` (ESL, masters `Skyrim.esm` only) + 3 scripts + generated mesh, textures, energy
arrow models and snowfall art, all shipped in **Zenderal - Patch Collection**. Curator's design, 2026-11-16, agreed
over a series of rendered mocks. **Unverified in game. Not placed yet** (location still open); for testing,
`help "Snowveil"` in the console, then `player.additem <id> 1`.

## The look (tools/01)

- **Model:** Real Bows' Daedric bow by **DecimusMaximus** (open permissions; credit him). Pretty Enderal Armory ships
  it as Firewind's model, `enderal\weapons\bows\firewind.nif`, with its textures in `textures\weapons\realbows\`. The
  curator chose it from rendered open-permission candidates.
- **Silver:** the whole bow is polished silver, using Argent Verdict's values: `SILVER_RAMP`, its cubemap
  `ArgentVerdict_e.dds`, and Complex Material R .94 / G .93 / B 1 / A 0. Silver keeps a third of Real Bows' normal
  relief.
- **Wraps:** the grip's leather and the cord wraps near the tips are gray (`GRAY`). This was royal blue first, then
  dark brown, then gray, all on the curator's word. Their own grain and stripes are kept.
  - Silver bands run at each wrap's ends.
  - The grip's stitched seam is silver lacing (`LACE_U`: a column of Real Bows' atlas).
- **Tips: Real Bows' own sleeve and spike, in silver** (curator 2026-11-16, late: "I don't like these odd shaped
  ends, just remove them for something like the original bow").
  - The first build capped the sleeve with a dome and grew talons from it. The rework replaced the whole tip metal
    with a lofted 32-sided ferrule (its widths later measured across the curve after wood showed through).
  - In game the ferrule's swollen, odd shape was rejected, so its code is removed. The original metal is kept and
    painted silver like the rest.
  - **No talons since 2026-11-16 evening** (curator: "ditch the talons from the tips and instead add more
    feathers"). Three jointed toes with keeled claws stood there from the rework until then; that code is removed.
  - **Plume** (`PLUME`): seven feathers with their stems in the sleeve's mouth around the spike's base, spreading out past the end of the
    bow, up to 36° out of the bow's plane and up to 16° toward its back. Their broad side faces the bow's side;
    each is drawn on both faces.
  - **Collar** (`COLLAR`, replaces the first rework's face fans): six feathers a face, rooted on the gray cord wrap
    2.4 units before its end (y 40.6) and fanned toward the tip, so their broad parts cover the wrap's fringed end
    and its junction with the tip metal. The curator's in-game crops showed clipping and odd texture there. A
    ferrule started at y 41 to cover that junction ballooned to 3.8 wide over the flared fringe, so it was rejected.
  - **Feathers** are **attached by their stems** (curator; the first build put the rounded tip on the bow: the stem
    is the end at the texture's top). They are the game's own hawk feather ingredient
    (`clutter\ingredients\hawkfeather01.nif`, Bethesda's copy: SMIM's loose one has no alpha), one feather cut
    from it. Its photo texture is made white (`OwlBowFeather_d.dds`, `FEATHER_RAMP`). The collar and grip fans lie
    flat on each face of the limb. **Every stem sits on the bow** (`seat_feather`, curator: "some are
    floating"; "nothing clipping on the wrappings"). Its foot is 0.08 below the surface under it, measured on the
    triangles (`surface_z`: the limb and the ferrule; a nearest-vertex search missed the sparse grip rings). The
    feather then rises along its length just enough to clear every surface beneath it by 0.05, including the gray
    cord wraps and their fringe. The fan's layers part toward the tips. Tip roots sit on the ferrule's own curved
    axis. A stem with no surface under it stops the build. (The first rework lifted whole feathers as flat cards,
    `bow_z_extent`, which left stems floating.) Their own shape: `OwlBowFeathers`, alpha-tested, double-sided.
  - **Grip fans** (`grip_feathers`, `GRIP_FEATHERS`): four more feathers a face where each limb leaves the grip, lying
    along the limb toward its tip. The curator asked for "more feathers on other areas of the bow". They are weighted
    to `Bow_UpBone1` / `Bow_LoBone1`.
  - **Skinning:** the plume and collar are weighted 1.0 to `Bow_UpBone2` / `Bow_LoBone2`, the bones
    that carry the tips. The silver parts take their texture from an unused atlas corner (`ORN_UV`, asserted empty)
    painted plain silver.
- **String:** its own shape on a lighting shader with `OWN_EMIT`, white with a faint blue tint (`STRING_EMIT`). The
  bow shape needs the environment-map shader for silver, and the original's glow shader can't do both.
- **Arrows (curator: no quiver, pure white energy):** both models come from the game's bound arrow.
  - The ammo model (`IceArrow.nif`, shown on the back at the QUIVER node) keeps its blocks, but its root has no
    children: nothing on the back.
  - The flight model (`IceArrowFlight.nif`) is white energy: a near-white diffuse from the Daedric arrow's, and a
    white own-emit.
  - **The game also shows the flight model on the string while drawing.** Confirmed in game: the string arrow
    glowed white.
  - **Controllers on that model hold at their first key while it is on the string, and run once it is fired.** In
    game 2026-11-16, with alpha keyed 0→1, the arrow was invisible until fired, even on a fresh equip. So a fade on
    the arrow model cannot follow the draw.
  - The flight model carries a clamped alpha controller, 0→1 over `FLIGHT_SHOW` (0.05 s): invisible on the string,
    visible once fired.
  - **The arrow that forms on the draw is the bow's own** (`nock_arrow`, shape `OwlBowNockArrow`, white own-emit):
    - It is collapsed to nothing at the string's nock ring in the bind pose.
    - Its nock end carries that ring's exact weights (`Bow_StringBone1` 1.0) and its head the riser's
      (`Bow_MidBone`), with every ring between a linear blend.
    - So drawing stretches it from the string's rest line back to the hand, and the release snaps it away.
    - Its head stays at the rest line, about 25 units short of the riser's front.
    - Checked with a rendered simulated draw (the string bone pulled back 55 units).
    - **Seen working in game 2026-11-16.** The curator then asked for it "much bigger": shaft radius 0.32, head
      radius 1.1, fins 1.1 (`NOCK_ARROW`; it was 0.13 / 0.5 / 0.45). "Still small": shaft 0.65, head 2.0, fins 2.0,
      glow 4.5. Undrawn, the collapsed head shows as a small star at the string's middle, seen from the front or back.
    - **Longer, not fatter (curator).** The head now **moves forward** as the string comes back
      (`NOCK_ARROW['reach']` 0.7): a ring at t follows 1 − 1.7 (1 − t) of the string's travel.
      - At the head that is −0.7: weight 1.7 on `Bow_MidBone` and **−0.7 on `Bow_StringBone1`**. Every vertex
        still sums to 1, so the arrow rides the bow's own motion.
      - A 55-unit draw gives about 94 units from the nock to past the grip (simulated with the file's own
        weights). Thickness is back to shaft 0.45, head 1.5, fins 1.5, glow 4.0.
      - **PyNifly drops negative weights on write and read.** The arrow is written with absolute values, then
        `signed_weights` rewrites the signed ones in `NiSkinData`, in the partition's float weights (by the
        partition's bone table) and in the vertex data's half-float weights (by each vertex's own 4 index bytes,
        whose slot order differs). It asserts every vertex sums to 1.
      - Negative weights work in game (seen in the curator's recording 2026-11-16: the arrow grew both ways from the
        string).
    - **Solved from the bow's own draw animation (2026-11-16, late).** The curator's full-draw screenshot showed the
      back end above the fingers.
      - The bow animation (`bow_drawheavy.hkx`, Skyrim - Animations.bsa) **swings** each string half about its limb
        tip, by about 38° (`string_full_draw`: forward kinematics of the bow skeleton). It does not slide the string
        straight back.
      - Under linear blend skinning a vertex 18 units from the nock was carried about 12 units up by that rotation,
        and its cross-section was stretched.
      - So the arrow is now **designed in its full-draw pose** (from the animation's nock K to 12 past the grip) and
        each vertex's rest position is solved: `v = A(f)^-1 (P − f t)`, where `A(f) = f R + (1 − f) I`.
      - Each ring's factor f is chosen so the folded ring is inside the riser (a ray test against the riser's
        triangles), then so it lies nearest a half-formed arrow at the clip's middle frame.
      - Simulated with every bone and the file's own weights, the full-draw back end is 0.3 from the string's notch.
      - At half draw it is still not a clean straight arrow (rings fold to different spots). Unverified in game.
    - **Formed at the arrow rest, not the string** (curator: "form from where the bow is notched rather than from
      the string"; and "remove this circle on the string", the collapsed head showing at rest).
      - Every ring now collapses at C, inside the grip at the arrow rest (`collapse_x` 0.9; the riser there is
        x −2.4..2.3, z ±1.08). The radii are sized to stay inside: head 0.85, shaft 0.33, fins 0.6. Nothing shows
        at rest.
      - The nock end follows `f_nock = 1 + (C − nock) / DRAW` of the string's travel (1.58), so it meets the string
        at full draw. The head follows `f_head` (−0.94), so it ends `head_past` 12 beyond the grip's front.
      - `DRAW` = 31 units was measured from the curator's screenshot of the first forming arrow (whose length then
        equalled the draw), as a ratio along the arrow's own line.
      - **If the real draw differs, the nock end misses the string at full draw by (f_nock − 1) × the difference:
        tune `draw`.** Simulated: 65 units at full draw, nock on the string.
- **Snowfall:** `OwlBowSnowFX.nif` is Chillrend's enchant art (the frame Rise's flames use) carrying the look of the
  game's gently falling snow:
  - `FXSnowSub` flakes: its shader, alpha, particle data and colour curve.
  - An emitter box over the whole bow, slow flakes falling in world space, about 9 a second.
  - Enchant art shows only while the bow is drawn.
- **Not shipped:** no engravings. An owl / falling-feather / snowflake line-art set was drawn and removed the same
  day, on the curator's call. The scratch tools are not committed.

### How the mesh is written

Real Bows' file keeps every block byte for byte except the shape: collision, BSX, `Prn = WeaponBow`, the bow-draw
behavior graph data and the seven draw bones.

PyNifly writes the three new skinned shapes (bow + ferrules, toes and claws; string; feathers) into a scratch file, using the original skin:
global-to-skin, skin-to-bone transforms, weights and partition. Their six blocks are then spliced in:

- The bow's group goes at the old shape's block indices. PyNifly writes a `BSDismemberSkinInstance`, which is
  truncated back to the original's plain `NiSkinInstance`.
- The string's, the feathers' and the forming arrow's groups are appended and added to the root's children (the feathers' with an
  `NiAlphaProperty`).
- Refs are remapped by name: bones to the original nodes, strings to the original string table.

PyNifly's skin data is not byte-identical to the original (it reorders and re-quantises weights), but it has the same
sizes and structure.

## The mechanics (tools/02, scripts)

| Record | What |
|---|---|
| `800` WEAP `ZP_OwlBow` | Firewind 054029's record (Pretty Armory EGO Patch's). 23 damage, crit 17 (unique bows run 20–27), `WeapTypeUnique`, enchantment `804`, NoAutoCalc cost 1 / 3000 charge (Sting's shape), script `ZP_OwlBowScript` |
| `801` STAT | first-person model = the same mesh (Pretty's 1stPersonFirewindBow's shape) |
| `802` AMMO `ZP_OwlBowIceArrow` | EGO's Starling Arrow, **NonPlayable** (never listed, never picked up), 8 damage, weightless |
| `803` PROJ | ArrowDwarvenProjectile without CanBePickedUp |
| `804` ENCH | `806` slow 30% / 4 s; `807` freeze 3 s behind `GetRandomPercent < 5` |
| `805`/`808` | the quiver ability and its script effect |
| `806` MGEF | Sting's slow (Shadowtongue Oil's), Chillrend's frost hit shader, EnchantArt `809` + invisible EnchantShader `80A` |
| `807` MGEF | `ZP_OwlBowFreezeEffect`: Ice Shot's rule (no higher level than the player, not unique, not a follower or MagicNoFreeze), AI off + Paralysis, Enderal's frozen shader, Arctic Wind's sound, no shatter |
| `809` ARTO / `80A` EFSH | the snowfall; Sting and Rise's carrier shader copy |
| `80B` FLST | the arrows equipped before the bow |

- **No arrows needed:**
  - `ZP_OwlBowScript` (on the bow) remembers the equipped arrows (powerofthree's `GetEquippedAmmo`) and gives the
    quiver ability.
  - `ZP_OwlBowQuiverEffect` keeps 50 ice arrows in stock and equipped: at the start, and again 0.25 s after every
    `arrowRelease` / `BowDraw`.
  - Unequipping removes the ability and every ice arrow, then re-equips the remembered arrows.
- **Glow Be Gone** nulls every unprotected enchant shader, which would kill the snowfall.
  `src/StingAndRise/tools/03-glow-be-gone-exclusion.py` now writes `Zenderal - Owl Bow.esp:00000806` beside Sting and
  Rise's entries. Rerun it after a Glow Be Gone update.

## Regenerate

`python src/OwlBow/tools/01-build-assets.py` (mesh, textures, energy arrows, snow → Patch Collection), then
`python src/OwlBow/tools/02-build-records.py`, deserialize, copy the `.esp` and the `.pex` into Patch Collection.
Rerun 01 after a Pretty Enderal Armory update (Real Bows' mesh/texture) or an Argent Verdict cubemap change.

## Open

- Placement (the curator's call). Until then the bow is console-only.
- Seen in game 2026-11-16 (first build): it loads and draws, and the string arrow glows white. The tip rework, the
  grip fans and the steady-glow arrow are not yet seen. To check:
  - The tips have no clipping, and the feathers read as white feathers.
  - The silver reflects.
  - The string glows.
  - Snow falls while drawn.
  - The quiver refills and NPC corpses hold no ice arrows.
  - The slow, and the freeze on a low-level enemy (5%).

**Reverted at 23:47 on 2026-11-16 (curator: "bank where we are but revert").**

- Snowveil is back to its state at 21:52: the skinned forming arrow inside the bow mesh, which passes through the grip.
- Build used: `tools/01` and `02` as they stood at 21:52, rebuilt and deployed.
- The later energy-arrow work is banked whole in `E:/Zenderal-backups/2026-11-16-snowveil-energy-arrow-bank` (repo sources incl. `arrowfade/`, docs, deployed files). It covered:
  - playable bound ammo cloned into the hand;
  - the `ZenSnowveilArrow.dll` 1.0–1.12 (SKSE) string-bone draw reading;
  - the steel-arrow shape;
  - the tip-to-nock alpha-test reveal.
- What that work found, which still holds:
  - The nocked arrow is the ammo model's `Arrow:0`, cloned into the right hand's `WEAPON` node; it copies the back copy's hidden flag.
  - The game never puts NonPlayable ammo in the hand.
  - Shader-property alpha does nothing.
  - Material alpha and alpha-test threshold can be set at runtime.
  - A first-person pull takes about 0.2 s.

**The hole (2026-11-16, curator's idea: "this magical bow draws and fires its arrows through this hole").**

- `tools/01` `arrow_hole` cuts a round hole through the riser along the forming arrow's full-draw line (`ARROW_LINE`, set by `nock_arrow`). It runs from the string side to the head side.
- **Cut.** Per face, the riser triangles reaching within `r_ring` 0.72 of the line (17 triangles) are replaced by a fan between their own outer boundary and a circle of radius `r_tube` 0.42 on the original surface.
  - The boundary keeps the original vertex positions, so there are no cracks.
  - Asserts check that the boundary is star-shaped around the line and stays outside the ring.
- **Silver parts.** A tube joins the two circles, and a raised silver ring 0.14 high sits on each face (ornament UVs).
- **Weights.** Every new vertex takes the UV and bone weights of the surface under it, so the hole bends with the riser.
- **Riser shape.** At y ~7.4 the riser is octagonal: flat faces and chamfers out to +-0.75, sides at +-1.0. That is why the ring is small; at 1.0 it caught the side faces.
- **Line lift.** The arrow's line is lifted 2.5 units at the riser (`NOCK_ARROW lift`, centre y 7.44) because in first person the hand grips higher and the arrow ran through the fist; third person had sat well.
- Unverified in game.

**Snow from the bow and the arrow (2026-11-17)**

- **Bow.** The bow's snowfall enchant art is denser: 24 flakes/s instead of 9, up to 90 instead of 40, radius 0.45 instead of 0.35. The old values were hardly visible.
- **Fired arrow trail.** `tools/01` `flight_snow` builds the fired arrow (`IceArrowFlight.nif`) from the bow's snowfall nif, with the flight arrow's blocks copied in and references remapped:
  - copied: the shape, its lighting shader with the show-in-flight alpha controller, the texture set, and the alpha property;
  - root renamed, BSX flags taken from the flight nif, the Chillrend billboard dropped;
  - the emitter box runs along the shaft (y 2..66) and the particles are world space, so the flakes stay behind as a trail;
  - flakes are 0.8 radius, live 0.8 s, 220/s.
- **No snow on the string.** The trail's birth rate is keyed 0 to 220 over `FLIGHT_SHOW` and clamped. The game holds a flight model's controllers at their first key on the string, so it only snows once the arrow is loosed.
- **Status:** `sr.check_refs` passes. Unverified in game.

**Draw and release sounds (2026-11-17, `0x80C–0x811`).** The curator's licensed files, converted by `tools/03-install-draw-sounds.py` into Patch Collection (not committed). They are played by `ZP_OwlBowQuiverEffect`, which is on the player while the bow is equipped. The WEAP record has no draw-sound slot; vanilla's come from `SoundPlay.WPNBowNock*`/`WPNBowPullLPM` clip annotations, and those are global.

| Sound | Source and trim | Plays on |
|---|---|---|
| Whoosh (`80C`/`80D`) | "Whoosh Transition Elements 7": a riser peaking 1.50 s in, with its first 1.0 s cut, so it peaks 0.5 s after the trigger | `arrowAttach` |
| Saber (`80E`/`80F`) | "MA_SoundBox_Lightsaber_003", ignition and hum, played whole | `bowDrawn`, or 0.5 s after `arrowAttach` if that never arrives |
| Owl hoot (`810`/`811`) | "Owl in Forest 02": the second hoot only, cut at 0.29 s and 12 dB quieter | `arrowRelease`, over the bow's shot |

- **Timing.** Vanilla's draw clips put `arrowAttach` at 0.3 s and start the pull at 0.8 s. In game the string goes from rest to full in about 0.3 s, roughly 0.5 s after attach. That estimate comes from the 2026-11-16 `ZenSnowveilArrow` logs.
- **Cancelled draws.** `bowReset` before the saber has played stops the whoosh and the saber.
- **Log.** Every bow event is logged as `[ZP Snowveil sound] <event> +<s since arrowAttach>` in the Papyrus log, to tune `DRAW_TIME` (tools/03) and `SaberFallback`.
- **Status.** Unverified in game.

**First test of the sounds and snow (2026-11-17): nothing played, no snow.**

- **Sounds.** The Papyrus log showed `Cannot call Play() on a None object`, and only `BowDraw`/`arrowRelease` arrived.
  - Cause: the quiver effect had been running when the save was made. It keeps that build's event registrations and property values until the bow is re-equipped.
  - Fix: `Setup()`, run on every event (`setupVersion` 2), registers all the events and fills any empty Sound from `GetFormFromFile`.
  - If `arrowAttach` never arrives, the draw sounds start `AttachWait` 0.35 s after `BowDraw`.
- **Snow.** The particles were far too small. The game's own falling snow (`PCloudSnowFlakes09`) has particle radius 3.5, because each particle is a sprite with a flake inside it; ours were 0.45 (bow) and 0.8 (trail).
  - Now 1.6 and 2.2.
  - The snow particle system is set to world space, so the trail stays behind the arrow. Chillrend's template is local, which also meant the old trail flew with the arrow.

**Wind around the fired arrow (2026-11-17, curator: "a subtle wind effect around the arrow").**

- **Source.** `tools/01` `import_tracer` copies the vanilla arrow's own tracer back into the flight nif. `TracerRoot` comes from the bound arrow's flight nif and carries:
  - `trailShort`, the long faint bluish streak along the flight line;
  - `Flow:0`, a swirl that its NiTransformController spins;
  - their effect shaders and alpha properties.
- **Import.** 12 blocks, with references remapped per block type; any other type raises an error.
- **Opacity.** Each effect shader's base alpha is x0.35 (`WIND_ALPHA`).
- **No wind on the string.** Each shader gets a BSEffectShaderPropertyFloatController (variable 5, Alpha Transparency) keyed 0 to that alpha over `FLIGHT_SHOW`. This is the arrow's own trick: on the string the controller holds at its first key, so the wind only shows in flight.
- **Why it was missing.** `flight_snow` builds the flight nif from the snowfall nif, so the bound arrow's tracer had been dropped.
- **Status.** Unverified in game.

**Second sound and visual pass (2026-11-17)**

- **Draw sounds.** The whoosh and lightsaber were removed (curator: "doesn't work well"); `80C`–`80F` are retired.
  - The log explains it: the whoosh peaked 0.5 s after `arrowAttach`, but `BowDrawn` arrives 0.91 s after it.
  - Measured over 5 draws: `BowDraw` → `arrowAttach` 0.18 s → `BowDrawn` 0.91 s → `arrowRelease` 1.06–1.33 s. `bowReset` never arrived.
- **New draw sound.** One of three air swells per draw, in turn (`812`–`817`, `tools/03-install-sounds.py`), from the curator's "DeepLongAirTransition4_001..003".
  - Each starts on `arrowAttach`, cut so its loudest 100 ms lands 0.91 s later (peaks at 3.05 / 2.05 / 1.98 s in the sources).
  - Each runs 2.5 s past the peak, fading over the last 1.2 s.
  - The next draw stops the previous one.
- **Owl hoot** on release kept.
- **Snow and wind were still invisible after the size fix**, in a game started after the rebuild.
  - The snow had copied the ambient snowfall's look: colour alpha at most 0.35, normal blending, Effect Lighting on (lit by the scene, so dark in a dark wood).
  - It now takes Rise's working look (Chillrend art + torch, additive): alpha flags `100d`, Effect Lighting off, colour (0.92, 0.96, 1.0) at 0.85, radius 2.4 at the bow and 3.0 on the trail.
  - The wind tracer is at full vanilla opacity (it showed nothing at 0.35).

**Third visual pass (2026-11-17): still no snow or wind after the look fix.**

- **Bow snowfall.** Snowveil's slow effect `806` lacked `FXPersist`. Every enchant art that shows in game carries it: Rise `806`, Sting `802`, Clockwork Thunder `807`, Whisper `80B`, and Enderal's own Chillrend-art frost affinity `02F1A1:FS`. `tools/02` now adds it.
- **Arrow trail and wind.** The trail's birth rate and the tracers' alpha are now constant; the 0 → value release keys are gone.
  - The keys were meant to spare the string, but the arrow on the string is the ammo model's `Arrow:0` (traced 2026-11-16), not the flight model.
  - They were one more thing that could fail silently.
- **Status.** Unverified in game.

**Shot sounds and the 5th-shot crit (2026-11-17)**

- **Wing beats.** The curator's "BigBirdFlappingWings_02" was split at its digital silence into its 8 single wing beats (`tools/03`, `--flaps`). Each is started 0.06 s before it comes within 20 dB of its peak, so the whump lands on the release.
  - SNDR `818` lists all 8, so the game picks one at random per shot. SOUN `819` plays it.
- **The fifth shot** plays the owl's hoot instead and is a guaranteed critical hit.
  - `ZP_OwlBowQuiverEffect` counts releases and sets global `81A` to 1 on the 5th, and to 0 on every other release.
  - Hidden perk `81B`, added by the script, applies `CalculateMyCriticalHitChance` +100 while `81A` = 1 and the weapon is Snowveil. This is Prophecy Deadeye's entry; the tabs are owner = global, weapon = GetIsID 800.
- **ZenSnowveilTrace.dll** (`src/OwlBow/trace`, testing only, put in MO2 `overwrite/SKSE/Plugins`) — built because the snow and wind still did not show after `FXPersist`. It logs twice a second while Snowveil is equipped:
  - the bow's enchantment effects' art and shader;
  - every attached `OwlBowSnowFX` node, with its flags, particles and bound;
  - each fired arrow's 3D, with its shapes and particle counts.
  - Delete it from overwrite after use.

**Found with ZenSnowveilTrace (2026-11-17/19): why no snow or wind ever showed.**

- **The snow drew transparent.** The art attaches in both views and its particles are alive: 15–29 at the bow, 88–180 in each fired arrow's world-space trail. The fired arrows do use `IceArrowFlight.nif`.
  - Cause: the list's winning `textures/effects/FXSnowSub.dds` is **The Weathers of Enderal - for CS - HDR's blank 4×4 with alpha 0**, which switches vanilla's particle snow off. Every flake drew as nothing.
  - `tools/01` now copies the game's own flake texture (from `Skyrim - Textures5.bsa`: 128×128, white, four flakes in its alpha) to `textures/Zenderal/OwlBow/SnowveilFlakes.dds` (`OUT_FLAKE`, not committed). It rewrites the shader's source path to it.
  - Every look change before this (size, blending, alpha, `FXPersist`) was answering the wrong question.
- **The wind was hidden.** The bound arrow keeps its tracer under `AddOnNode99`, a BSValueNode hidden in the nif. The game shows it only on a tracer roll. `import_tracer` now clears the hidden flag on every node it copies.
- **Lesson.** Check what the winning copy of a vanilla texture actually is before building on its path. Weather mods blank vanilla FX textures.
