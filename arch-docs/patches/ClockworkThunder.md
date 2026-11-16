# ClockworkThunder

- **Source:** `src/ClockworkThunder/`
- **Ships:** `Zenderal - Clockwork Thunder.esp` + `ZP_ClockworkThunderChainScript.pex` + `ZP_ClockworkThunderStunScript.pex` + 1 generated mesh + 3 generated
  textures (not committed), all inside **Zenderal - Patch Collection** (curator's choice, 2026-11-13)
- **FormID block:** `0x800–0x80B`
- **Pillar:** modern combat (curator's request, 2026-11-13)

## What it does

**Clockwork Thunder** is a unique rifle that looks like Starling work: Ordo Legionis' *Nehrimese Flintlock Fucile*
(`OL_Musket_Rifle 002F9B`) in polished, reflective gold, with a cog train on the forestock and a cog-shaped trigger guard. Every
shot that hits sends a **weak chain lightning** out of the enemy it hit, which only takes the ball: the lightning
**bounces on from enemy to enemy**, up to 4 of them, 15 shock damage each, and **stuns every enemy it strikes that is
below the player's level** for 3 seconds.

| FormKey | Record | From |
|---|---|---|
| `800` | WEAP `ZP_ClockworkThunder` "Clockwork Thunder" | `OL_Musket_Rifle 002F9B` (Muskets of the Enderal, the only plugin with it) verbatim; Name, Model, FirstPersonModel `801`, ObjectEffect `802` + charge 3000, Value 666 → 3200, Damage 20 → 28 / crit 9 → 10 (Ordo's range is 6–35), + `WeapTypeRifleBoltAction 000800:DAR Rifles.esp`, equip sounds → Skyrim.esm's bow sounds (Ordo's are Dawnguard.esm's, an empty stub here) |
| `801` | STAT `1stPersonZP_ClockworkThunder` | `OLM_1stPersonMusketRifle 002F9A` verbatim; Model → the new mesh |
| `802` | ENCH `ZP_ClockworkThunderShot` "Chain Lightning" | weapon enchantment (Touch), `803` only; `NoAutoCalc`, cost 1, charge 3000 (never runs dry in practice; soul gems still recharge it) |
| `803` | MGEF `ZP_ClockworkThunderChainEffect` | Script effect running `ZP_ClockworkThunderChainScript` (`Bolt` = `804`): the bounces, below. Its description is the item-card text |
| `804` | SPEL `ZP_ClockworkThunderChainLightning` | Prophecy's Flow State chain lightning `000B02`, its effect swapped for `80A`, Magnitude 40 → **15** ("weak"), **no Area** (one target per bolt), + `809` |
| `80A` | MGEF `ZP_ClockworkThunderBoltEffect` | Prophecy's Invoker shock `000AFD` (vanilla Chain Lightning's bolt `0A9D92`) verbatim, Explosion → `80B` |
| `80B` | EXPL `ZP_ClockworkThunderBoltBlast` | Prophecy's flash-less chain explosion `000B01` **minus the `Chain` flag** |
| `807` | MGEF `ZP_ClockworkThunderStunEffect` "Stunned" | Enderal's Arcane Archer affinity paralysis `_00E_AbAffinityArcaneArcher_ParalysisME 14CEBD` (only Skyrim.esm has it): Target Actor, no projectile, no `PowerAffectsDuration`; shock hit shader `057C67`, `MagicParalysis` keyword and its conditions (no Starling constructs `035D59`/`0F23C5`, not restrained) kept |
| `808` | SPEL `ZP_ClockworkThunderStun` | Target Actor, `807` for **3 s** (`STUN_SECONDS`) |
| `809` | MGEF `ZP_ClockworkThunderStunCheck` | Script effect (Aimed, hidden) running `ZP_ClockworkThunderStunScript` (`StunSpell` = `808`) |
| `805` | COBJ `ZP_TemperClockworkThunder` | Ordo's matchlock temper `00F5D6`: gold ingot + **Starling ingot** `0DB8A2` (was `0F11C0`); new product. **No forge recipe**: the rifle is unique |
| `806` | REFR | the rifle on the broken altar in **Old Askamahn's throne room** (cell `DesertAltAskamahnL2 07336E`, Enma Darkhand's room) |
| override | CELL `07336E:Skyrim.esm` header | Skyrim.esm's, verbatim (only the English name: the plugin is not localized). **This plugin now owns that cell's header**; no other plugin in Ultra touches it (`tools/00`, 2026-11-13) |

### The bounces (curator 2026-11-13: "the effect should bounce between enemies")

The first build used the engine's own chain (vanilla Chain Lightning's Chain explosion), which did not visibly
bounce. Two reasons, read from the records rather than seen in a trace: its reach is the spell's Area (13 ft, so
only enemies standing close together), and every jump is a new projectile with the player as shooter, which Hit
Where You Aim re-aims at the crosshair (the enemy just struck). So the chain is scripted, the same shape as Sting
and Rise's Blood Boil. **The enemy the shot hits gets only the ball** (curator, same day: "nothing but the bullet
firing from the actual gun, the proc of chain lightning applies and deploys from the hit enemy"; the first build
also sent a bolt from the player into it): `ZP_ClockworkThunderChainScript` starts there and up to **4** times (`Jumps`, `CHAIN_JUMPS`) finds the **nearest** living actor within **700** units
(`Range`, `CHAIN_RANGE`) of the last one struck that is hostile to the player, not a teammate, not disabled and not
struck yet (powerofthree's `FindAllReferencesOfFormType`), waits 0.15 s and fires the bolt **from the last enemy
struck at it** with `RemoteCast`, blamed on the player (kills and Enderal's EP stay the player's). Those bolts start
away from the player, so [`RemoteCastAimFix`](RemoteCastAimFix.md) leaves their aim alone. The bolt's explosion has
no Chain flag and the spell no Area, so each bolt strikes exactly one enemy and the script alone picks where it
goes. The effect has no duration, so after its first line the script runs on locals and a Global function.
`02-build-records.py` refuses to run if the script's `Jumps`/`Range` differ from its own constants (the item card
quotes them). **[unverified in game]**

### Why the lightning is an enchantment with a script

A musket is a crossbow-type WEAP, so a **weapon enchantment applies to the enemy the shot hits** (unlike the
staff-based pistols, where the enchantment *is* the shot: [`ReversalShadow`](ReversalShadow.md)). But an
enchantment's effects are delivered by contact: the MGEF's projectile and explosion are never used, so an effect with
a Chain explosion would not leap. The enchantment therefore runs a script effect that casts a real lightning bolt
from the player at the struck enemy: vanilla Chain Lightning's bolt (`0A9D92`) flies from the player into the
enemy, with Prophecy's explosion (its copy of `ChainLightningExplosion 05DBAD` **without the image-space flash**,
here also without the Chain flag). The bolt is the same one Prophecy's Flow State and Invoker use, so it is proven
in this list:

- **The copied effect `80A`** keeps `PowerAffectsMagnitude`, so the player's Elementalism/Destruction perks raise
  the 15. Accepted as a feature.
- The first build ran Ordinator's `ORD_CastSpellPlayer_Script`; the bounces need our own script (above).
- **Killing shots chain too:** the effect has no "target alive" condition, so a shot that kills still sends the
  lightning on to the enemies around.
- Nothing flies from the shooter: the first bolt leaves the enemy the ball hit, 0.15 s after the hit.
- **Bolts fly marker to marker (2026-11-13, third build).** The second build cast each bolt with the struck enemy
  itself as the source, and the curator saw it "fire the initial lightning in a random direction" with no bounce:
  an **actor** casting an aimed spell fires along its own facing, whatever target `RemoteCast` names. Each bolt is
  now cast from an empty activator (`FXEmptyActivator 0B79FF`, property `EmptyActivator`) at 0.6 of the struck
  enemy's height, 70 units (at most half the gap) toward the next enemy so it clears the struck body, at a second
  one at 0.6 of the next enemy's height. A non-actor source aims at its target: the same shape as Ordinator's
  autocannon (Prophecy's Clockwork Turret). The markers are deleted 2 s after the last bolt. **Verified in game 2026-11-13** (curator: "Bounces right").

### The stun (curator 2026-11-13: "stun / stagger enemies for a few seconds", "only on enemies lower level than the player")

No condition compares the target's level with the player's (`GetLevel` compares with a number or a global, and no
global holds the player's level), so a script decides. The check `809` is an effect **of the bolt spell itself**,
so every bolt (the first and each bounce) runs it on the enemy it strikes. `ZP_ClockworkThunderStunScript` (`Scripts/source`, compiled `.pex` committed) skips the player, the
dead and player teammates. If `akTarget.GetLevel() < PlayerRef.GetLevel()` it casts `808` from the player onto the
target: 3 s of **paralysis** with the shock hit shader (the engine's stun; it ragdolls, so the enemy crumples and gets
up). The paralysis is Enderal's own Arcane Archer affinity effect, so Starling constructs and restrained actors are
immune, as they are to it. A plain stagger (`Stagger` archetype) was the alternative: it only plays one ~1 s stagger,
not "a few seconds". Equal level = no stun. **[unverified in game]**

### Musket systems

The WEAP is a new record of a new plugin, so every system that recognises Ordo's muskets by plugin or form had to be
told about it:

| System | How it picks muskets | What was done |
|---|---|---|
| [`MusketHandling`](MusketHandling.md) (`ZenMusketHandling.dll`): reload on demand, dodge lock, aim slowdown | crossbow-type WEAP from a plugin in `[Muskets] Plugins` | `Plugins=OrdoLegionisMuskets.esp, Zenderal - Clockwork Thunder.esp` (repo `src/MusketHandling/data/` + Patch Collection's live copy; old ini in `E:/Zenderal-backups/2026-11-13-clockwork-thunder/`) |
| DAR Rifles' animations, Quick Reload Stack | keyword `WeapTypeRifleBoltAction` (KID gives it to Ordo's 14) | the keyword is on the record itself (masters `DAR Rifles.esp`) |
| First-person aim down sights + the ramrod reload (3P/1P, ball and ramrod props) | per Ordo **mesh**, `IsEquipped` OR lists ([`FlintlockOverhaul`](FlintlockOverhaul.md) `tools/06`, `09`–`12`) | the mesh keeps the rifle's barrel, sights, grip and muzzle, so the gun joins **the rifle's group**: `tools/06` `EXTRA_MUSKETS` for future reruns, and `tools/03` here adds `IsEquipped(Zenderal - Clockwork Thunder.esp \| 800)` next to the rifle in the 7 installed configs (2 ADS in Patch Collection, 5 in `Zenderal - Musket Ramrod Reload`) without rerunning that chain (06's standalone mod is gone and 12 needs the curator's .wav files). Backups: same folder |
| [`HWYAMusketFix`](HWYAMusketFix.md) (Gravity 0) | the **ammo's** projectile | nothing: the rifle fires Ordo's Musket Balls / Rifled Bullets, whose PROJ the fix already covers |

**If Flintlock Overhaul's `tools/09` is rerun**, it rebuilds the ramrod configs from `tools/06`'s `muskets()`,
which already includes this gun; rerunning `tools/03` afterwards is harmless (it reports `have`).

## The mesh (`tools/01`)

The winning rifle mesh is Ordo Legionilis (Imperial Muskets)' **loose** `OL_Musket_Rifle_Animated.nif` (it beats
Muskets of the Enderal's BSA). It is an **LE-format** file (NIF 20.2.0.7, BS 83) built on the Dawnguard crossbow
skeleton, with 18 transform controllers, behaviour-graph extra data and collision. PyNifly would drop the
controllers, so `tools/nifsplice.py` rebuilds the file **block by block**: every original block is written back
byte for byte (asserted), except:

- the rifle's **texture set** (diffuse, normal, gold cubemap and Complex Material mask → `ClockworkThunder_d/_n/_e/_m.dds`;
  Ordo's slots 2–3 kept) and its **shader property**, made Environment Map (below);
- the rifle's **NiTriShapeData**, with the trigger guard's 1198 triangles, the lock-side oval escutcheon (64) and the two
  hexagonal tubes (348) removed
  (vertices kept);
- the root's child list, plus new blocks: one NiTriShape for all the cogs, same parent and transform as the
  rifle's shape, a copy of the rifle's shader property and its own texture set (`ClockworkThunderCog_d/_n/_m.dds` + the
  gold cubemap); and one NiTriShape + data for the **round barrel**, with its own copies of the rifle's
  shader property and texture set (same textures; **8 new blocks** in all).

The file is then read back with PyNifly as an independent check. NIF trap found on the way: in 20.2.0.7
NiGeometryData, a 4-byte **Material CRC** follows the BS vector flags.

**Cogs.** The cog is Enderal's own Starling cog `clutter\dwemer\dwecog01.nif` (6 teeth, a finger-sized hole); the
winning copy is Zenderal - Convex Planes Fix's. Placement is in the rifle shape's own space (Z along the gun, Y up,
X across; ×0.62 to world):

- **Gear train** (curator's screenshot, 2026-11-13: "where they mechanically make sense"): four meshing cogs on the
  forestock straight in front of the lock plate, the largest against the plate, mirrored on both sides
  (`TRAIN_START`, `TRAIN`). The forestock's side there is a flat band y 22.3–27.2 (surface scan), so the train
  runs along it. Centres are `MESH` × (r1 + r2) apart and each cog is turned so its teeth fall into the previous
  cog's gaps. A first build with cogs on the butt and wrist was rejected.
- Each cog is **bent onto the surface** like an inlay: every vertex rides on the gun's surface height under it
  (highest sample within 0.35), `THICKNESS` proud, `SINK` under. Normals are recomputed from the bent mesh. The
  build stops if a cog leaves the silhouette or the surface under it varies more than `MAX_RELIEF`. Cells that only
  see hidden inner faces take the disc's median height. The surface is sampled about every 0.3 units, because the
  forestock is long thin triangles.
- **Lightning tube** (curator 2026-11-15: "a glass tube with a lightning bolt sparking in it ... with some gold
  fittings"; the first build sat on the side-plate side's lock panel, read from a screenshot, and was wrong: "not
  on the side, on the top, just before the hammer"; a slim tube sloping down the wrist top, then an enlarged one,
  were both wrong too: the curator's highlight on a side view, "the tube is horizontal matching the barrel", then
  on the horizontal build sitting over the wrist: "hollow out the wood to align the tube with the barrel", with an
  L outline down the breech face and back at the barrel's underside). The tube is **coaxial with the barrel**
  (axis x 0, y 27.17 = the round barrel's axis; collars r 1.94 = the barrel's radius, bead +0.06, glass r 1.55),
  from the breech plug's rear face (z -25.33; front collar at -25.35, no nub, the tang under it) back to the rear
  cap at z -35.8 (with its terminal nub); 10.45 long. **The wood is cut away for it** (`cut_channel`, `channel_box`):
  the stock (the largest welded piece) and the tang are split along a convex region's planes (any plane, inside
  where p . n >= c) - Sutherland-Hodgman per triangle, every attribute interpolated on the cut edges, the inside
  dropped. The region: floor y 26.97 (`CHANNEL_FLOOR_BELOW_AXIS` 0.2 under the axis), full width
  (`CHANNEL_HALF_WIDTH` 5: a slot's side walls hid the tube from the side), front the breech plug's rear face, and
  behind the rear nub (z -36.43) a **ramp** rising 0.8 per unit back (`CHANNEL_RAMP`, about 39 deg) into the wrist.
  `channel_walls` closes it: floor and ramp each filled from their plane's cut outline (strips between the
  outline's break points: the stock's own cross-section; the lock mortise is covered over), the front plane's cut
  edges carried down to the floor. New faces take wood by a planar map through the largest butt-side triangle
  (`wood_uv_map`, asserted to land on wood in the metallic map). The lock (plate x <= -1.87, hammer) and the side
  plate are not cut. **Embedding** (curator after the first in-game look: "the cutaway wood gaps on the right side
  by the hammer and back are too noticeable ... more embedded and seamless"): the first cut went down to the
  barrel's underside (y 25.19, the curator's L outline) with a vertical rear wall; on the hammer side the lock
  plate then stood 2.3 above bare floor beside the tube, and the back was a step with a ledge. Raised to just under
  the axis, the wood holds the tube's lower half and meets the lock plate's top (27.5), and the ramp replaces the
  step. Previous (flat) cut kept as `before-lightning-tube/ClockworkThunder-flat-cut.nif`. The rifle's NiTriShapeData is
  now written whole (`nifsplice.trishape_data` gained vertex colours; Ordo's block rewrites byte-identical, checked
  2026-11-15). Top y 29.2, below the breech top. Three new shapes, each with its own shader block:
  **After the first in-game look (2026-11-15)**, in order: (1) the front face of the cut, round the front collar
  against the breech, is **gold** ("should be metal not wood"; `close_cut` groups go to the gold shape); (2) a
  deeper pocket round the rear cap was built, then dropped for **a longer tube whose rear end clears the wood**
  ("instead of cutting away just extend the tube length"): `tube_axis` finds the rear cap as the first z, going
  back, where the wrist top under the whole end fitting (and the end cog) is `CAP_CLEARANCE` 0.1 under the bead
  ring - z -42.0, 16.65 long (`pocket_box` is kept, unused); the ramp then closes nothing and is optional;
  (3) **a cog on the tube's end** (`tube_end_cog`: the same cog, coaxial, on the rear cap's face, facing back, the
  nub through its hole, tips at the bead ring, 0.4 thick); (4) the **floor beside the tube is a gold plate** (a
  two-strip version was built; the curator kept the plate) **covered in cogs** (`plate_cogs`: packed by size,
  largest first, on a 0.1 grid, inside the plate's outline and clear of glass, strap and collars; big ones
  (r >= 0.38) on the plate with teeth interleaving, smaller ones a layer up over the gaps; 28 cogs, capped by one
  shape's 65535 vertices/triangles), in their own shape `ClockworkThunderPlateCogs` with its own copies of the cog
  shader and texture set. Cut faces take their UVs from the original wrist top straight above them
  (`wood_uv_map`), so the remaining wood (the ramp, when there is one) carries the wood that was there.
  **Second in-game round (same day):** (5) a **slot** for the tube's rear half (`slot_box`: from the strap back past
  the end cog, floor 0.05 under the bead rings, x +-2.05; wood walls where the wrist is wider) - the wrist top had run
  through the glass's lower part ("cut away the wood a little to house the tube better"; the "tube is clipping"
  picture); (6) the plate is now a **panel like the lock plate** ("make the plate look more like the side panels",
  picture of the lock plate's tail): `plate_panel` raised 0.1 with a 0.14 bevel to the cut's outline, from the slot
  forward, in the RIFLE's shape and texture set, UVs sampled from the lock plate's outer face (`lockplate_uv_map`:
  its tail, 0.75 along / 1:1 across, cells of 0.25 so nothing smears), plus a pair of round rivets a side
  (`plate_rivets`); (7) **wires** on it ("could you add some wires maybe to the plate?", sketch): two gold tubes a
  side (`plate_wires`, r 0.065) from under the front collar, snaking back to the slot; the plate cogs keep off the
  wires, rivets and the slot (12 now).
  **Third in-game round:** the box slot left only a gap ("I still want the wood, just space for the tube to sit
  in") and the lock-plate texture read worse than the gold: (8) the slot is now a **groove** (`groove_box`,
  `groove_faces`): a 24-sided prism round the tube's rear half (inradius = bead ring + 0.05), only the wood inside it
  removed; each prism face is filled where it lies in the wood (split at the cut outline's crossings, the middle of
  each piece tested against the wrist top / first cut's floor), plus a front end wall (the prism's cross-section
  clipped at the floor height); behind the plate the first cut's own wood floor is kept (cut off at the strap).
  (9) The panel keeps its shape, bevel and rivets but is gold again (cog shape, planar UVs); `lockplate_uv_map` is
  kept, unused. (10) **Two metal side tubes** ("on either side of the plate add 2 tubes with cogs on the end", then
  "metal tubes"): one gold pipe a side (`side_tube_layout`, `side_tube_parts`: r 0.2, the longest stretch the panel
  allows, collars and a small cog on each end with an axle nub); one wire a side now, held inboard of the tube;
  rivets and plate cogs keep off them.
  **Fourth in-game round:** "all looks good but I don't like these jagged edges from the cut out" / "maybe we could
  hide them with more metal tubing?": the groove went to 48 sides with 0.1 z steps, and a fill strip whose two ends
  see a different number of outline crossings is split until they agree (skipped strips had left notches); and
  **gold tubes run along both groove edges** (`groove_edge_tubes`, `sweep_tube`: r 0.24, the edge traced from the
  groove's own cut outline per 0.2 of z, smoothed over 3 bins either side, rounded ends), from the strap back to
  about z -40.5, where the wrist drops below the groove. Then ("the pipes aren't connected to anything and look a
  little creased in areas, have them bow smoothly and then connect to the end of the tube parts"): each pipe's middle
  is a cubic in z fitted to the traced edge (no kinks), its front end bends (cubic Bezier, tangents matched) into
  the rear end cog of that side's metal side tube along its axis, and its rear end into the rear collar's front
  shoulder, 40 deg below the side (`bezier`, `EDGE_TUBE_COLLAR_ANGLE`); 12-sided.
  (11) "add various different sized Cogs in this space, from large / medium and small" (the strip outside the
  side tube): the plate cogs no longer keep off the side tube's whole length, only its end cogs and collars (a cog,
  0.16 thick, fits under the pipe, whose underside is 0.2 over the panel; asserted), and may overhang the panel's
  bevel by 0.1; 28 cogs, r 0.55 down to 0.18.
- **Shot sound** (curator 2026-11-15: "add this noise to when it's fired", their licensed Motion Array
  `MA_SoundsByGFXSounds_Sci-FiLaserGunShot_1.wav`): SNDR `ZP_ClockworkThunderShotSD 80C` = Ordo's
  `OLM_WPNMusketFire 002F9C` verbatim (category, output model, priority, 8% pitch variance) with its four musket
  shots replaced by `sound\fx\Zenderal\ClockworkThunder\ClockworkThunderShot.wav`; the rifle's AttackSound and
  AttackSound2D point at it (tools/02; 002F9C added to tools/00's winner scan). `tools/04-install-shot-sound.py
  <wav>` converts the file (24-bit -> 16-bit PCM, 48 kHz stereo kept, peak-normalised, Reversal Shadow's
  converter) into Patch Collection; the wav is not committed. Then ("add this sound effect to the fire"):
  `tools/04` takes several wavs and mixes them as layers from 0; the shipped shot = the laser shot + `Blaster Rifle
  Shot V03.wav` (16-bit 44.1 kHz, resampled to 48 kHz), 2.64 s, scaled 0.854 to stay under the 16-bit peak. The
  laser-only file is kept in `E:/Zenderal-backups/2026-11-13-clockwork-thunder/`. Then ("turn up the newer shot
  sounds, they're a little quiet"): the plain mix already peaked at 0.96 of full scale, loudest 50 ms at -9.5 dB RMS,
  so `tools/04` now runs it through a soft limiter (`--drive 2.5`: tanh(k x)/tanh(k) on the peak-normalised mix),
  -9.5 -> -4.8 dB RMS, peak still 32000; the plain mix is kept as `ClockworkThunderShot-laser-blaster-plain.wav` in
  that backup folder. Then ("add this shot sound on top of the others"): a third layer,
  `MA_SoundsByGFXSounds_SniperRifleShot_4.wav` (licensed Motion Array, 24-bit 48 kHz stereo, 2.2 s), all three from
  0, same limiter: -10.2 -> -4.9 dB RMS, 2.64 s (the two-layer version kept as
  `ClockworkThunderShot-laser-blaster-loud.wav`). Then ("I want the shot sounds fired at the same time, not
  staggered"): the files open on different lead-ins (attacks at 0.113 s laser, 0.003 s blaster, 0.253 s sniper), so
  mixed from their file starts the bangs came one after another; `tools/04` now cuts each layer to 2 ms before its
  own attack (first frame at 10% of its peak) before summing, so all three hit together, 2 ms after the trigger.
  Then ("add this on shot too"): a fourth layer, `MA_MotionAudio_Sci-FiBlasterShot_04.wav` (licensed Motion Array;
  attack at 0.007 s), aligned the same way; -9.3 -> -4.8 dB RMS, 2.63 s (three-layer version kept as
  `ClockworkThunderShot-3-layers.wav`). **[unverified in game]**
- **Reload sounds** (curator 2026-11-15: "add these to the reload, decide how they're paced based on the animation
  movement", their licensed Motion Array `MA_Designed_SciFiWeaponsReload_1/_2.wav`; `tools/05`). The rifle shares
  OL_Musket_Rifle's ramrod reload (FlintlockOverhaul tools/09-12), whose reload clip (4.43 s) moves: handling click
  0.17, ball drawn 0.84, **ball into the muzzle 1.71**, ramrod drawn 2.22, **rod stowed 2.96**, back on aim 4.43.
  Both sounds are short two-hit designed reloads with their attack at the start (first loud 50 ms at 0.05 s; 0.8 and
  0.6 s audible), so `ZP_CTReload1` (SNDR 80D) lands on the ball going in (the loading) and `ZP_CTReload2` (80E) on
  the rod being stowed (the closing), each starting 0.05 s before its beat; asserted that Reload 1 has died away
  before Reload 2 starts in every clip. Clockwork Thunder gets its own copies of the rifle's four reload submods
  (third person, its *both reload perks* faster copy, first person and its faster copy; reload clips only, 16 in
  all) under OAR mod `Zenderal - Clockwork Thunder Reload` in Patch Collection, keyed on Clockwork Thunder alone,
  priority +200000 (order kept). In each copy the two musket loading-sound annotations (`SoundPlay.ZEN_MusketLoad7`
  / `ZEN_MusketLoad1`) are edited in place, text and time (no size change; the faster copies scale the beats, not
  the sounds); Zodd's handling clicks stay. SNDR 80D/80E = vanilla's bow nock verbatim, one file each,
  `Data\Sound\FX\Zenderal\ClockworkThunder\ZP_CTReload1/2.wav` (16-bit mono 48 kHz, not committed). Rerun
  `tools/05 <Reload_1.wav> <Reload_2.wav>` after FlintlockOverhaul tools/09-10 rebuild the ramrod reload (and after
  `tools/03`). Volume: `--gain 0.85` by default since 2026-11-15 ("lower the reload sounds by 15%"), about -1.4 dB
  (peaks ~23450 of 32767). **[unverified in game]**
  - `ClockworkThunderGlass`: radius 1.55, a copy of the rifle's Environment Map shader with ZBuffer write off,
    specular white/3.0, glossiness 300, our own faint tint (`ClockworkThunderGlass_d/_n/_m.dds`, alpha 0.18; the
    env mask's alpha is 1 so Complex Material stays off) and Bethesda's `textures\cubemaps\chrome_e.dds` path
    (the list's TB's HD Cubemaps copy wins); NiAlphaProperty 0x00ED (blend).
  - `ClockworkThunderBolt`: three cards through the axis (0 deg lies flat, facing a player looking down at the
    wrist; then +-60 deg) with `FXLightningBolt01.dds` (two forked
    bolts side by side; each card shows one half), `ClockworkThunderGlow`: two narrow cards with `ShockBoltTile01.dds`.
    BSEffectShaderProperty (layout decoded from Bethesda's `meshes\magic\testlightninggeo.nif`), SLSF1 ZBuffer
    test + falloff, SLSF2 double-sided, pale blue emissive, additive NiAlphaProperty 0x100D like Bethesda's.
    **Animated by our own float controllers** (`add_float_controllers`; Bethesda's test mesh has one key and
    zero length, so nothing to copy): the bolt's U offset steps between the two bolts every 0.12 s and its V offset
    jumps along the tube every 0.13 s (stepped keys), its emissive multiple flickers 1.5..9 over 1.1 s; the glow
    crawls (V offset 0..1 in 0.6 s) and pulses. Flags 0x48 (Active + Compute Scaled Time, loop) as Bethesda's;
    the rifle's BSXFlags (203) already carries the Animated bit. The textures are the list's winners (Rustic
    Daedra's bolt, SRW0 Voltage's tile), referenced by vanilla path.
  - Gold fittings in the cog shape (`tube_fittings`, `lathe`): an end fitting at each end (terminal nub, cap,
    bevel, bead, collar sleeving the glass; the profile drawn for a 1.5 collar, scaled by `FIT`; the front one
    without a nub) and a strap round the middle (`TUBE_SCREWS` off); 1600 triangles.
  Previous mesh in `E:/Zenderal-backups/2026-11-13-clockwork-thunder/before-lightning-tube/`. Built and deployed
  2026-11-15. **[unverified in game]**: whether the controllers animate on an equipped weapon / world model and how
  the glass sorts against the bolt.
- **Oval escutcheon removed** (curator 2026-11-13: "on the right side where the cogs are there's a gold panel
  underneath, just remove it so the cogs aren't overlapping on it"): Ordo's oval plate on the lock side of the
  forestock (its own welded piece, `OVAL_BOX`, 64 triangles) sat under the third and fourth cogs. It is dropped
  before the cogs are seated, so they rest on the stock (lock side now 2.73–2.83 out, as the plate side); the
  stock's surface runs on beneath it (checked: no hole). Previous mesh in
  `E:/Zenderal-backups/2026-11-13-clockwork-thunder/before-oval-removal/`. **[unverified in game]**
- **Trigger guard** (curator: "make the trigger guard cog shaped", then "thinner, I want it to be subtle"): the
  guard piece (the welded component in `GUARD_BOX`: loop + rear scroll) is removed, and a cog stands in the side
  plane round the trigger, centred on X = 0. It is remapped radially so it is a **thin ring**: hole 3.6, band 0.9,
  teeth 0.8, 1.4 thick across the gun (the old guard was 2.8), one tooth straight down. The trigger piece
  (z −34.1…−28.9, y 17.5…22.1) sits inside the hole.
- **Muzzle cog** (curator 2026-11-13: "a cog over the hole"): the same cog, remapped like the guard, standing across
  the barrel at the muzzle face: hole = the bore (0.92), band to 1.47 (just over the muzzle lip, 1.36), teeth to
  1.92, 0.6 long, front face 0.15 ahead of the muzzle, one tooth straight up. The rifle has no front-sight blade
  (the aim line runs over the muzzle top), so that tooth reads as one. In both ADS holds its tip is 0.76° under the
  crosshair (the bare muzzle was 0.99°), nothing in the line of sight (`tools/06` `measure`).
- **Tangents** are computed from UVs in the convention read off the rifle's own data on every build: NIF
  "tangents" = dP/dv, "bitangents" = dP/du (matches the Silvergrove note).

**Round barrel** (curator 2026-11-13: "make the barrel cylindrical"). Ordo's barrel is one welded hexagonal tube
(240 triangles, every vertex on a hexagon round the bore axis (0, 27.17), corners at 0/60/… deg, bore face at the
muzzle); the thin rib between barrel and ramrod is another (108). `barrel_triangles` finds every such piece that
reaches the muzzle and asserts the hexagons; the round ramrod is left alone. Each triangle is split twice at its
midpoints (60° faces → 15°, 24 sides) and every point mapped from its hexagon onto the circle of 0.909 × the corner
radius (the circle with the hexagon's area), so the breech steps, muzzle lip and bore keep their profile. UVs are
interpolated inside each original triangle, so the texture is the barrel's own. Normals are smoothed across
welded points only between faces within 45°, so the step and muzzle faces stay hard. The cogs are still placed on
the rifle surface as it was (old barrel included). First build froze the game on equip (curator, 2026-11-13): the barrel shape shared the
rifle's shader block, the one structural difference from the cog build that equipped fine (data checked clean: no
NaN, no zero-area triangles, indices in range). The barrel now has its own shader and texture-set copies: **equips without the freeze (curator,
2026-11-13)**, so the shared shader block was the cause. Never point two NiTriShapes at one
BSLightingShaderProperty in a weapon mesh. Round barrel and muzzle cog **verified in game 2026-11-13** (curator: "looks right"). The cog-only mesh is backed up in `E:/Zenderal-backups/2026-11-13-clockwork-thunder/mesh-before-round-barrel/`.

**Polished gold** (`polished_gold`, curator 2026-11-13: "the gun metal shiny gold now that we have those new
cubemaps"; it was rusted gold before). **Ordo's rifle never reflected anything:** its shader is type 0 (Default)
without SLSF1 `Environment_Mapping`, so its cubemap and env mask (`englishflintlockrifle_metallic.dds`) were never
read. Every shader in our mesh is now **Environment Map (type 1)** with that flag and env scale 1.0
(`make_envmapped`: the type, the flag, and the type's trailing env-scale float; asserts the block was a plain type 0).
The textures are **Rise's build-4 recipe** ([`StingAndRise`](StingAndRise.md#rise-in-gold): Precious Objects Complex
Material and Dynamic Cubemap's gold), imported from `src/StingAndRise/tools/01-build-assets.py`, not copied:
- the rifle's own metallic map separates metal from wood; metal goes onto Rise's `GOLD_RAMP` by luminance (pale bright
  gold, mean 0.93/0.84/0.64), wood kept ×0.82;
- our own normal map: Ordo's with the highlight mask (alpha) at 0.85 on metal (Ordo's is 1.0 everywhere, wood keeps it);
- a **Complex Material** mask on metal (R 0.94 reflection / G 0.93 gloss / B 1.0 metalness / A 0), wood G 0.2 only;
  written with `-sepalpha` and checked on its 1×1 mip the way Bottled Shaders tests it (rifle 0.30/0.43/0.32/0,
  cogs 0.95/0.93/1.0/0: not grey, alpha 0), so the metal reflects Dynamic Cubemaps' live surroundings;
- Rise's gold chrome cubemap (`ClockworkThunder_e.dds`, made the same way from Bethesda's `chrome_e.dds`), the shine
  wherever Complex Material is off.
The cogs get the same from Enderal's cog texture and normal map (all metal). All BC7 through texconv (xEdit's
`Texconvx64.exe`); the rusted build is in `E:/Zenderal-backups/2026-11-13-clockwork-thunder/before-polished-gold/`.
Verified in game 2026-11-13 (curator: "gold looks great now").

`--preview <prefix>` writes flat side renders (`_lock.png`, `_plate.png`) and the recoloured atlas; `--out-root`
writes somewhere other than Patch Collection (dry run).

### The ring scope (`tools/scope.py`, 2026-11-16)

Curator: "can we attempt to add this style scope to the Clockwork Thunder?" (a screenshot of Scoped Bows' Nordic
bow sight). The geometry is OutLaw666's **Scoped Bows SE** (Nexus 912): "You are allowed to use all of my assets in
your own mods!" (only re-uploading the mod is refused). **Credit OutLaw666.** Scoped Bows itself is not installed;
`scope.py` extracts `nordicbow.nif` from the curator's download (`downloads/Scoped Bows SE 1.3.1-912-1-3-1.7z`, 7-Zip)
at build time. The scope is part of the rifle's mesh: no script, no zoom (Scoped Bows has none either).

- **Which parts:** the Nordic bow carries two scopes; the screenshot is its *precise* one: rear ring `ring_2`, rim
  `rim006:1`, knobs `bolts_1`, lens `part4`, and the front reticle `ring` + `retfront` + `retfront_1` 22 units ahead
  (the bow's own spacing). Dropped: the ring's two forward spikes `part4_3`/`part4_4` (curator, side view: "need
  removing"), the reticle's stem `part4_5` (used only to square the reticle, then replaced by a mount), the quick scope.
- **Where:** each ring's own centre on the crosshair ray of the rifle's corrected first-person hold (Flintlock
  Overhaul `tools/06`'s `ADS ol_musket_rifle/crossbow_idledrawn.hkx`, read from Patch Collection, so run 06 before
  01): rear ring at root y 7.9 (the breech, where the ray is 3 units over the barrel and the ring's 2.86 radius just
  reaches it), reticle 22 further along the ray. Measured in the mockup the curator approved: horizontally on the
  barrel's centre line within 0.03 units. The rear knobs are rolled (8°) to 12/3/6/9 o'clock as the aiming eye sees
  them and the reticle's stem to 6 o'clock (curator: "have the scope 12 o'clock be at a 90 degree angle").
- **Mounts:** a tapered gold post from inside each ring's bottom into the barrel top (curator: "needs a mount adding
  for the scope to attach to the barrel"): rear 0.7 shape units (~0.4 in game), front ~4 in game (the reticle stands
  well over the barrel there).
- **Look:** the rings wore Dragonborn's Nordic bow/mace textures (Bethesda DLC, absent in Enderal, not ours to
  ship), so every gold part (rings, knobs, rim, mounts) uses our own `ClockworkThunderScope_d/_n/_m.dds`: a meander
  (Greek key) band drawn by `key_band_texture` on the ring faces (12 repeats round the rear ring, 6 round the
  reticle's), plain gold elsewhere, through the same polished-gold recipe as the rifle (Complex Material, gold
  cubemap). Ring UVs are generated by angle (`ring_uvs`, triangles unwelded at the seam). The lens is the tube's
  glass shader (alpha blend); the reticle is an emissive cyan `BSEffectShaderProperty` on a white texture
  (`ClockworkThunderReticle.dds`), additive. Three shapes, each its own shader block and texture set:
  `ClockworkThunderScope`, `ClockworkThunderScopeLens`, `ClockworkThunderScopeReticle`.
Verified in game 2026-11-16 (curator: "Looks right").

## Placement (`tools/02`)

On the broken altar `RuinsAltarBroken 07410A` (its mesh `RuinsFurnitureRubble15.nif`, PG Patcher Output's copy wins)
in the throne room: a height field sampled from the mesh shows a flat broken slab at local z 14 with gaps, end
posts and rails at 19–21 (y ±68). The rifle lies along the altar's long axis, centred at altar-local (0, −28), on its
side: rotation (0, −π/2, 0). In root space the rifle is upright (length +Y, upside down: up is −Z). A quarter turn
about Y lays it down, and with no Z turn its length stays on world Y, the altar's long axis (the altar is turned
1.588 rad). Which side faces up depends on the engine's sign for Y. The height clears both sides by 1 unit and the
REFR has **no** Don't Havok Settle, so Havok lets it come to rest on the slab. **[unverified in game]**: if it lands
badly, set Don't Havok Settle as [`ReversalShadow`](ReversalShadow.md) does and adjust the height.

## Regenerate

```
python src/ClockworkThunder/tools/00-scan-overriders.py   # live winners of every copied record -> overriders.json
python src/ClockworkThunder/tools/01-build-assets.py      # mesh + textures into Patch Collection
python src/ClockworkThunder/tools/02-build-records.py     # YAML (refuses if a copied record changed hands)
python src/ClockworkThunder/tools/03-add-to-musket-clips.py   # after Flintlock Overhaul regenerates its clips
```

Rerun `00` → `02` after Ordo Legionis, Prophecy's chain lightning or the Askamahn cell changes hands. Rerun `01` after
the rifle mesh/textures, the cog mesh or the altar change, and after Flintlock Overhaul `tools/06` (the scope sits
on its aim ray); then `02` (placement reads the built mesh). Load after
`Zenderal - Prophecy.esp`.

## Status

Built 2026-11-13: deserializes clean, HEDR 1.7, ESL. The plugin round-trips through Spriggit with no differences.
Deployed into Patch Collection (plugin, mesh, textures, `ZP_ClockworkThunderStunScript.pex` + source). **Not yet ticked in Ultra's load order:** MO2 was open, so
the curator places `Zenderal - Clockwork Thunder.esp` after `Zenderal - Prophecy.esp`. **Unverified in game**: the
look in both views and when dropped, the lightning on hit (and its leap), the stun (lower-level enemies only), reload on demand / dodge lock, ADS and
the ramrod reload with this gun, and the rest pose on the altar (`help "Clockwork Thunder"` →
`player.additem <id> 1` to test without the trip; `coc DesertAltAskamahnL2` for the altar).

First in-game look (2026-11-13, curator): ADS works, but the left hand clipped into the forestock. The cause was
the rifle mesh's shared ADS clips (Ordo's Fucile had it too), not the cogs; fixed there, see
[`FlintlockOverhaul`](FlintlockOverhaul.md) "Left hand in the Fucile's stock". Verified in game 2026-11-13 (first person).
