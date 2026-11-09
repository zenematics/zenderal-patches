# ResponsiveGroundsEnderal

- **Source:** `src/ResponsiveGroundsEnderal/tools/01-build-config.py` → `src/ResponsiveGroundsEnderal/SKSE/Plugins/ResponsiveGrounds.json`
- **Ships:** MO2 mod `Zenderal - Responsive Grounds Enderal` (that JSON only); `build/manifest.json` release of the
  same name. Wabbajack `Include` rule.
- **FormID block:** none (no plugin, no DLL)
- **Status:** built and enabled 2026-11-09 (Ultra, directly above `Responsive Grounds`); **unverified in game** —
  Responsive Grounds itself had not been launched yet either

## The mod it configures

[Responsive Grounds](https://www.nexusmods.com/skyrimspecialedition/mods/197435) 3.0 (W1terr, GPL-3.0,
[source](https://github.com/W1terr/Responsive-Grounds)), installed 2026-11-09: footsteps, sprints, hooves, weapon
swings, shouts and explosions kick up leaves, green leaves (pine needles), dust, pebbles or snow, by the ground
underfoot. One SKSE DLL, a few meshes/textures/sounds, no plugin. Optional: Dynamic Wind Framework (in the list).

**Why it should load on the list's 1.7.104** (checked 2026-11-09 from source and the DLL, not in game):

- Built against alandtse's CommonLibVR 10.1.0 (2026-09-30, submodule `39f9d07`), whose `IDDB.cpp` reads Address
  Library format 5 (1.7.104's) and whose `PlayerCharacter.h` carries the 1.7.99 runtime-data shift
  (`kAE1799ShiftBytes`, `RelocateMemberIfNewer(RUNTIME_SSE_1_7_99, …)`). **[upstream]**
- Its `SKSEPlugin_Version` block has the same flags as our `ZenWheelerSaveFix.dll` (address-library independent,
  `versionIndependenceEx` 3), which runs on 1.7.104. **[verified]** (DLL bytes)
- No hardcoded addresses or member offsets: two vtable hooks through CommonLib (`PlayerCharacter` slot `0xAD`,
  `Explosion::Initialize` `0xA2`) plus `BSAnimationGraphEvent`/`TESSpellCastEvent`/`TESDeathEvent` sinks.
- Its one hardcoded form, sound template `03F3A1` `PHYGenericGrassLightLSD`, exists in Enderal's Skyrim.esm under
  that EditorID (`reference/base/Skyrim/SoundDescriptors/`), so its rustle/pebble sounds work. If it were missing
  the DLL only logs `no sounds`. Seasons of Skyrim and Northern Roads support stay off (neither is in Enderal).

In game, its log `ResponsiveGrounds.log` (next to `skse64.log`) should say `settings loaded from
Data/SKSE/Plugins/ResponsiveGrounds.json` and `landscape textures: … records, … files`. Its menu (SKSE Menu
Framework) shows the texture under the player and what it gives, which is the quickest way to check a spot.

## Why Enderal needs a settings file

The land is read from the per-vertex texture layers of the cell's LAND, and each landscape texture is classified by
its **diffuse file name** (`Terrain.cpp` `DefaultStrength`): `fallforest` → autumn leaves, `pineforest` → green
leaves, `dirt`/`mud` → dust, `rock`/`gravel` → pebbles, `snow` → snow. Objects (rocks, cliffs, mountains) go by mesh
path and their own texture names (`mountain`, `rock`, `cliff`, `slab`, `dirt`, `snow`) and their collision material;
that part already fits Enderal's meshes and isn't configurable per object.

Where Enderal paints each file (2026-11-09 survey: every exterior cell's land layers in `reference/base`, FS's land
over Skyrim.esm's, 3,497 cells; share of all painted land, nearest map markers):

| File | Share | Where | Rule gives |
|---|---|---|---|
| `snow01` / `snow02` / `snowrocks01` / `grasssnow01` | 26.3 / 0.3 / 3.5 / 0.5% | Northwind Mountains, Frostcliff, Icecrack | snow ✔ |
| `ground_wet_sand01_dxt1` | 19.2% | the coasts and shallows (Fogville harbour, wrecks, lighthouses); the mod kicks nothing up under water | nothing ✘ |
| `volcanictundrarocks01` | 14.0% | desert, Sun Coast, Thalgard, Ark's north | pebbles ✔ |
| `fieldgrass02` (42 LTEX) | 5.4% | Heartland and Sun Coast fields, Riverville, Castle Goldenford | nothing (grass) |
| `rocks01` | 5.0% | everywhere rocky | pebbles ✔ |
| `desertdunes` / `02` / `03` | 3.8 / 0.1 / 1.4% | Powder Desert (Duneville, Old Yogosh, Hollow Hand) | nothing ✘ |
| `pineforest01/02/03` | 0.7 / 2.6 / 0.1% | Tower Encampment, Westgard, Bleakstar, Ad'Balor, Dark Valley | green leaves ✔ |
| `fallforest*` | 1.6% | **Goldenforst** (Fortress Goldenforst, Gravespath, Wellwatch, Dal'Marak) | autumn leaves ✔ |
| `reachdirt01` | 0.8% | Whisperwood (`_00E_PilzwaldDirt`) | dust |
| `tropicalbeach01/02`, `coastbeach01/02` | 0.8 / 0.2% | desert coast, Qyra Island; Wellwatch coast, Northwind shore | nothing ✘ |
| `rockpathiced_dxt1` | 0.3% | Northwind Camp, Excavation Site | pebbles ✘ (ice) |
| `tropicalfloor`, `dryground01`, `cavebaseground01` | 0.3 / 0.01 / 0.3% | dry ground: desert, Goldenforst, Old Darkesh; pirate hideout | nothing ✘ |
| `cobblestone02`, `stonepath`, `tropicalstonepath`, `rockpath*` | small | Ark and Riverville roads, Wellwatch paths | nothing / full pebbles ✘ |
| `mountainslab01desert` | 0.04% | desert rock, Qyra Island | nothing ✘ |

So Skyrim's names still fit wherever Enderal kept Skyrim's files — the Riften leaves land in Goldenforst, which is
Enderal's autumn forest — and miss Enderal's own sand, beach, dry-ground, path and desert-rock files.

## What the file changes

Only entries that differ from the mod's default are written (the tool refuses a no-op entry and any name that is not
one of Enderal's 91 landscape texture files). Strengths are on the mod's own scale: dirt 0.8, mud 0.6, rock 0.75,
its Sand object material 0.7, its stone road 0.2 dust / 0.25 pebbles, Whiterun stone 0.15 dust.

- **Dust:** desert dunes 0.7; dry ground (`tropicalfloor`, `dryground01`) 0.7; cave dirt 0.6; desert-coast and
  Qyra beaches 0.5, `sand_beach_01` 0.5; wet coastal sand 0.4; pebbly beaches 0.3; cobbles and stone paths 0.15,
  tropical stone path and rock paths 0.2; tropical forest floor 0.2.
- **Pebbles:** desert rock slabs 0.6; river-bed edge 0.5; pebbly beaches 0.3; rock paths 0.25 (were 0.75: a path,
  not scree); iced rock path off.
- **Green leaves:** tropical forest floor 0.6 (Qyra Island, the Duneville oasis).
- **Snow:** iced rock path 0.4; `LCaveGroundSnow` (Crystal Temple entrance) 0.5.

Left alone on purpose:

- **Grass** (`fieldgrass01/02`, `reachgrass01`, `frozenmarshgrass01`, tropical grasses, hay): the mod's design kicks
  nothing up from grass fields, in Skyrim too.
- **`tundra01`** (0.5%, 78% around Goldenforst/Wellwatch but also Thalgard and the desert): dry grass; leaves on it
  would carry Goldenforst's leaves into the desert. Candidate for leaves ~0.3 if Goldenforst's grassy patches look
  bare in game.
- **Unpainted files** (`diverse\ground1–6`, `diverse\grass1/2`, `new\ground_forest_dry`, `new\grass_dead_ground`,
  `new\ground_wet`, `woodchips01`): on no land in Enderal. A list mod that repaints land with them would need entries.
- **Whisperwood's soil** keeps the default dust 0.8.

**Limit:** choices are per file, not per LTEX record. `fieldgrass02.dds` alone backs 42 records (Heartland fields,
forest flowers, savanna, heath), so they can only share one choice.

## Load order, regeneration, menu edits

- The MO2 mod sits directly above `Responsive Grounds`. Nothing else ships `SKSE/Plugins/ResponsiveGrounds.json`.
- Texture replacers don't matter: only the file name counts, and the list's PBR landscape mods (PBR Landscapes of
  Vyn, TomatoRim PBR) move files under `pbr\` with the same names (TomatoRim's `FrozenMarshIce01` → `02` is the one
  rename, and ice gets nothing either way). The tool warns if a serialized mod renames a mapped file.
- Rerun after a Responsive Grounds update (check `Terrain.cpp`'s defaults against `default_strength`) or when a list
  mod adds or repaints landscape textures:

  ```
  python -I src/ResponsiveGroundsEnderal/tools/01-build-config.py [<MO2 instance dir>]
  ```

- A change in the mod's own menu rewrites the **whole** file (`Settings::Save`). Under MO2 that write goes either to
  this mod's copy or to overwrite (unverified which); either way, check before a Wabbajack compile that the shipped
  copy is still the generated one, and rerun the tool to restore it.
