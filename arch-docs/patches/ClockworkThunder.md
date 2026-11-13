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
the rifle mesh/textures, the cog mesh or the altar change; then `02` (placement reads the built mesh). Load after
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
