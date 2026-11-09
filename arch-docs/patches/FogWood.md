# FogWood

- **Source:** `src/FogWood/` (generated from scratch by `tools/01-build-wood.py`; never hand-edit the generated YAML)
- **Ships:** `Zenderal - Fog Wood.esp` (**full plugin**, not ESL; HEDR 1.7; masters Skyrim.esm, Update.esm, FS and, since
  2026-11-06, `Zenderal - Goblins.esp` for the goblin waves) + 4 scripts
- **FormID block:** `0x800–0x337A` (see below)

> **Not ESL: the light flag left the wood with no ground.** **[observed in game 2026-11-05]** As an ESL plugin the
> worldspace loaded but none of its 25 new cells showed terrain: no floor, the player fell through
> (`player.getpos z` -1064 standing on the marker at 4520). The structure was correct (each LAND inside its own
> cell's temporary group). In the list, the two ESL plugins that add terrain (EVGAT_Enderal, Temple of Malphas -
> Neo Enderal) put it only into cells Skyrim.esm defines; Vyn Full Extend adds ~10,000 *new* cells with terrain as
> a **full** plugin and they work. So: new exterior cells with LAND go in a full plugin. Rebuilt without `Small`
> (135 full plugins in Ultra with it). **Whether the full plugin fixes it is unverified in game.**
- **Pillar:** modern combat (curator's design, 2026-11-05): a build-testing arena

## What it is

The Fog Wood is a separate small worldspace, `ZFW_FogWood 0x800` ("The Fog Wood"), where endless waves of
Enderal's own creatures come for the player. The curator's design:

- **Practice deaths.** Dying ends the run: the player drops into bleedout, is sent back to the entry stone and
  shown the wave reached.
- **Fixed ladder.** Waves climb through Enderal's creature levels (`_NNE_` EditorID prefix = level), the same for
  every build, so "wave 12" means the same thing for everyone.
- **No rewards.** No experience and no loot from arena enemies: infinite waves can't be farmed.
- **Entrance:** a stone in Enderal's own pine forest (the north Heartland, between the Tower Encampment and Castle
  Bleakstar; until 2026-11-06 deep in Whisperwood), a quiet spot away from quests and Enemy Density groups.

## Status (2026-11-07)

**Space verified, arena built and deployed, arena unverified.** The worldspace, its navmesh, weather, walls and markers
are verified in game (2026-11-05, after the coordinate fix below: a Vyn save loads, the player arrives on the ground
among the pines, spawned creatures move on the generated navmesh). The arena (quest, stones, waves, elites, bosses,
drops, practice death, no rewards) is built, compiled and deployed (as MO2 mod `Zenderal - Fog Wood` until
2026-11-06, now inside `Zenderal - Patch Collection`; ships from list 0.9.4),
and **partly verified**: the first tests (2026-11-05) confirmed the stone, the entry, waves spawning and the arena loop;
they found mixed-species infighting (fixed by spawning disabled), then two Arps of one faction fighting each other,
and the elemental hit-registration problem below. The themed-horde build of 2026-11-06 (one kind per wave, 20+,
more elites, werewolves, always chasing) still had spawns fighting each other in its first test: **members of one
faction are not allies unless the faction is Ally to itself** (postmortem below). Fixed the same night; the next
test still had it, and found that dying left the player on the floor and that the loot never showed: the alias
script had never bound (postmortem below), so bleedout had no listener. Alias binding, a bleedout fallback in
the loop, loot dropped on the ground and 40 spawn aliases that log spawn-on-spawn hits are in the build of
2026-11-06 00:53, deployed, **unverified**. The infighting's cause is still open: read `ZFW hit:` lines in the
Papyrus log after the next run.

**First tester report (Discord, 2026-11-07, on list 0.9.4's build):** (1) enemies, Lost Ones especially, lose
the player and stand around; (2) items dropped in the wood are gone for good, a warning would do; (3) wave 2
(werewolves) cleared and no wave 3 came; (4) one wave's Apothecarius ghosts and skeleton ghosts fought each
other. (1) and (4) are the curator's own findings of 2026-11-06, addressed in the builds after 0.9.4 (converge /
stuck / far relocation; the friendly-fire GMSTs). (2) and (3) got the 2026-11-07 build: the loop registers its
next tick FIRST (an error anywhere in `OnUpdate` used to end the loop and with it the waves), a wave's last
few are gathered to the player after 20 s without a kill, a spawn outside the walls is brought back, the
caches give back anything that is not the fog's stock, and the entry message warns that loot left lying is
swept. Nothing in the script deletes an item the player drops (`RotateDrops` sweeps only the fog's own drops,
two waves on), so why the tester's items were gone is open: the sweep of unlooted drops is the likeliest
reading of "dropping items". All unverified in game.
Next test: find the Fogbound Stone in the pine forest (`cow Vyn -18 8`, then `player.setpos x -72640` and
`player.setpos y 33856`) (`player.moveto <slot>000961` puts you
at the wood's exit stone instead; the Whisperwood stone is script-placed, so `prid` has no fixed ID), activate it,
survive a few waves, die on purpose, leave by the stone.

To visit: `cow ZFW_FogWood 0 0`, or `player.moveto <slot>000954` (the entry marker; slot = the plugin's two-digit
Mod Index in MO2, `86` in Ultra on 2026-11-05). To test pathing, spawn a creature and let it chase you:
`player.placeatme 0FE4B3 1` (wolf), `player.placeatme 046EDC 1` (Lost One).

### History of the space

1. **Whisperwood copy, ESL** (first build): a 3x3-cell patch of Whisperwood with SureAI's navmesh. Loaded with no
   ground: the player fell through (`getpos z` -1064). As an ESL, none of the new cells showed terrain. In the
   list, the two ESL plugins that add terrain (EVGAT_Enderal, Temple of Malphas - Neo Enderal) put it only into
   cells Skyrim.esm defines; Vyn Full Extend adds ~10,000 new cells with terrain as a **full** plugin and they
   work. **New exterior cells with LAND go in a full plugin.**
2. **Whisperwood copy, full plugin**: terrain loaded; the curator found the mushroom forest the wrong look.
3. **Vyn pine-forest copy** (cells -20..-18 / 8..10): the entry marker, picked by distance from object *centres*,
   landed inside a rock. The curator asked for a fresh area instead: flat woodland terrain, lots of trees, a
   large space, dense but easy to path through. Copying a Vyn patch is retired; its generator (navmesh copy with
   edge/door cutting, NAVI re-parenting) is in git history before this build.
4. **Fresh build, first version**: crashed every load of a Dark Valley save (`SkyrimSE.exe+1215C4B`, ID 91891, a
   null interface in a Lost One archer's `MovementControllerNPC`, nowhere near the wood). Cause: the generator wrote
   the navmesh parent cell as X, Y; **Spriggit's YAML holds it as Y, X** (NAVM `Coordinates` and NVMI
   `ParentWorldspaceCoord`; all 3,001 / 5,823 of SureAI's checked), so every off-diagonal navmesh was registered under
   the transposed cell. Fixed; the save loads and the wood works (verified 2026-11-05). On the way, a test build
   without the NAVI record crashed at boot inside `NavMeshInfoMap` init (`SkyrimSE.exe+04E0234`, ID 30780,
   `InitTESThread`): **every NAVM needs its NVMI entry.**

## How the wood is built (fresh, `tools/01`)

A `PATCH`x`PATCH` (6x6) cell arena, cells -3..2 on both axes (24,576 units square, the entry at the origin), with a
`RING` of 1 cell of scenery around it: 64 cells of terrain and trees, 36 of them navmeshed. Everything is generated:

- **Terrain:** a few long swells within about +-50 units (`height()`, quantised to the engine's 8-unit steps), so it
  reads as ground and not a plane; normals from the same function. Floor texture `LPineForest02DensityGrass
  010B5D` (pine needles + 2 dense grasses) as the base layer of all 4 quadrants, with blotches of `LFieldGrass02
  01342A` as an alpha layer from a noise field. The list's grass mods win on the GRAS records as usual.
- **Trees:** stand on the navmesh lattice's vertices. Big pines (Skyrim's `TreePineForest01/02/04`, Enderal's
  `_00E_ScotsPine01-03`) every 3 vertices (768 units), jittered +-1, never closer than `TREE_MIN_GAP` 2 vertices
  (512 units); small pines (`TreePineForest03/05`) on free vertices; a floor of pine shrubs, reach ferns, clover
  and vurt fern fields (no collision) anywhere. Nothing else with collision: no rocks, logs or ruins. Scales
  0.9-1.25 / 0.8-1.1, random rotation. Each sits on the terrain height **interpolated** at its spot (the first
  build took the nearest 128-unit vertex and the small plants floated on the 8-unit steps between vertices), trunks
  sunk 4 units, floor plants 6, plus each mesh's own lift above its origin (`base_lift`: vurt_fernfield's lowest
  point is 19 units up). 2,061 pines + 7,040 floor plants (seed `SEED`).
- **Navmesh:** one per patch cell, a 256-unit lattice (17x17 vertices on the terrain heights, 2 triangles per
  square, consistent diagonal). Every triangle touching a tree vertex is removed: a 6-triangle hole (radius 256)
  around each trunk, and with the 2-vertex minimum gap every lane between trees stays at least two triangles
  wide. Parent cell coordinates are written **Y, X** (NAVM and NVMI alike; see the history). Triangles the entry
  cannot reach (small pockets sealed in by tree holes, 130 of 11,622 in the first build) are dropped, so nothing
  spawns where it cannot walk out. Border edges link to the neighbouring cell's
  navmesh (shared edge found by world position; `EdgeLinks` + `EdgeLink_x_y` flag). Winding follows SureAI's
  (read from a reference navmesh at run time: +1). The navmesh grid (NVGD) is built like SureAI's: divisor 10,
  cells y-major, a triangle listed in every grid cell its bounding box overlaps (96% match against a reference
  navmesh, the rest being SureAI's tighter test). The NAVI override (`000802:FS`) holds only our 36 entries, each
  `MergedTo` its linked neighbours, `Unknown2` = Enderal's constant.
- **Weather `ZFW_FogWoodWeather 0x803`:** FS's `SkyrimFog_HerzlandNebel 048085` with every colour, image space
  (`ISSkyrimFogNIGHT 0C820E`), volumetric light and directional ambient set to its Night value (dark at any hour),
  fog from 0 to 2500 (night 0 to 2250), max 1. FS's copy references `Update.esm`, hence that master. Climate
  `ZFW_FogWoodClimate 0x802` = DefaultClimate with only this weather.
- **Worldspace:** no parent, SmallWorld + CannotFastTravel, default water at -30000 (none), music
  `_00E_Music_Atmosphere_DeadForest 097C29`.
- **Walls:** four invisible planes (`CollisionMarker 000021`, `PortalBox` 2 units thick) `WALL_INSET` 512 inside
  the patch edge; the ring's trees run on beyond them into the fog.
- **Markers** (persistent, `XMarkerHeading`): the entry `0x954` at the origin (3 lattice vertices around it kept
  free of trees) and 12 spawn markers `0x955`-`0x960` on a 2,300-unit ring, each on a walkable lattice vertex,
  facing the centre: the wave quest's spawn points.

## The arena (`tools/02-build-arena.py` + `Scripts/source/`)

- **Entrance:** the Fogbound Stone, ACTI `ZFW_FogStone 0x805` (Skyrim's Shadow Stone mesh from `Skyrim - Meshes0.bsa`,
  which the list ships), **placed by the quest script, not by a cell record**: `ZFW_ArenaQuest.EnsureStone` does
  `PlaceAtMe` on the Tower Encampment map marker `132F43` (a persistent Vyn ref) and moves the ref to
  (-72640, 33856, 642) in cell (-18, 8) of the north-Heartland pine forest (curator, 2026-11-06: the Fog Wood is a
  pine wood, so its door belongs in Enderal's; 369 units from the nearest placed ref, Castle Bleakstar's refs 4,283
  away, the nearest Goblins pack 1,343; `scratchpad/pine_spot.py` scored every navmesh vertex of cells -20..-18 /
  8..10). Until 2026-11-06 the stone stood in Whisperwood at (-83776, 16832, 4452), cell (-21, 4), anchored on the
  Grimlight Gallery marker; `STONE_VERSION` (script constant, now 3) moves a save's already placed stone to the
  new spot on the next load. **The spot and the anchor are `AutoReadOnly` constants in the script** (`STONE_X/Y/Z`,
  `STONE_ANCHOR_ID`, resolved with `GetFormFromFile`), not quest properties: property values live in the save, so
  the first move (version 2) ran against the saved Whisperwood coordinates and changed nothing. So the plugin edits no Vyn cell and nothing of EPPI's or Enemy Density's can revert
  it. A second ref of the
  same stone stands in the wood's persistent cell (`0x961`, 320 units north of the entry marker) as the way out; the
  script tells entrance from exit by the player's worldspace.
- **The run** (`ZFW_ArenaQuest`, quest `ZFW_Arena 0x804`, start-game-enabled, player alias `ZFW_PlayerAlias`): the
  stone shows `ZFW_EnterMsg 0x810`; on Enter the player leaves **`EPFaction 039DCE`** (Enderal's `_00E_EPOnDeath` pays
  kill EP only to a killer in it; the faction is used by nothing else but the Overstrain scripts' own kill credit),
  is made essential (`ActorBase.SetEssential`), fades to the entry marker, and the first wave comes 10 s later.
  A 1 s `OnUpdate` loop (real time, so timescale is irrelevant) counts the living; when the wave is dead the next
  comes 8 s later. The loop also ends the run if the player is found outside `ZFW_FogWood`.
- **Waves are themed hordes** (curator, 2026-11-05: "20+ skeletons", "waves should all be part of the same faction -
  skeleton wave, goblin wave etc"): each wave draws ONE theme from the tier for its number (`ZFW_Tier1-5
  0x807-0x80B` = waves 1-3 / 4-6 / 7-9 / 10-12 / 13+; a theme may sit in several tiers; the theme just fought is
  re-rolled once). A theme `ZFW_Theme_<X> 0x4000+5n` is a FormList the script reads by index: [0] regulars (one kind),
  [1] elites, [2] bosses, [3] a MESG whose `Name` is shown ("Wave 4: 22 Fleshless Lost Ones, 2 elite."), [4] a
  GlobalVariable scaling the pack (`ZFW_PackFull/Most/Half/Third 0x813/0x816/0x814/0x815` = 1 / 0.7 / 0.5 / 0.35:
  trolls, bears, giants, Lost One lords come in smaller packs). Pack size `20 + 2*(wave-1)`, cap `MAX_SPAWNS` 30 (the
  arrays hold 40; this many live actors with the list's physics, dismemberment and equipment-display plugins is
  untested), times the theme's scale, never under 6, spread over the 12 markers (shuffled; the second and third on a
  marker are offset up to 120 units). The 26 themes are the `THEMES` table in `tools/02` (below).
  `PlaceAtMe(base, 1, false, true)` on the marker = **spawned disabled** (a live `PlaceActorAtMe` spawn runs its own
  AI with its own factions at once, and in the first test two species next to each other were already fighting before
  `Prepare` reached them), then `Prepare`: all factions dropped for `ZFW_ArenaFaction 0x806` (enemy of PlayerFaction),
  which is **Ally to itself** (see the postmortem: that is what makes its members allies), `IgnoreFriendlyHits()`
  (allies' stray blows otherwise add up to a fight; called again after `Enable`, since a disabled actor may not
  take it), Aggression 1 / Confidence 4 / Assistance 0, and **for the run `iFriendHitCombatAllowed` /
  `iFriendHitNonCombatAllowed` are raised to 100,000** (`FriendlyFire`, `Game.SetGameSettingInt`, restored at the
  run's end and re-applied on load: the hit log of 2026-11-06 showed bandits turning on bandits after their own
  spell projectiles struck them), then
  `Enable` and `StartCombat(player)`. **Always chasing** (curator: "alert to the player no matter what"): every
  second a spawn whose combat state is not *fighting* (idle, searching) or whose target is not the player is
  `StopCombat`ed and `StartCombat(player)`ed again (`Refocus`), which hands it the player's current position, so the
  fog never loses them and nothing else is ever their target. That was not enough (curator, 2026-11-06: enemies
  stood in the distance doing nothing, the last one could not be found, the run never ended): **a spawn farther
  than 1,800 units from the player for 5 s, or one that has not moved for 8 s while out of reach, is moved to the
  cache or spawn marker nearest the player that is at least 500 away** (`WatchFar`, `WatchStuck`, `Relocate`,
  `MarkerNearPlayer`: a clear lattice vertex, so nothing lands in a tree) and restarted on them, logged (`ZFW:
  brought`). The player is bounded too: past 11,500 on either axis (the curator ran off the edge; the invisible
  walls did not hold) the loop puts them back at the entry.
- **Elites** (curator: "additional elites"): `1 + (wave-1)/3` per wave, up to 5, counted inside the pack, from the
  theme's own elite list - Lords of the Lost Ones (Enderal's lich: dragon-priest body) with every undead theme, Arp
  shamans with goblins, werewolves with wolves, Vatyr Leaders with vatyrs, the Frost Crawler with spiders, lions
  with the cats, Ice Bears with bears, the Conjured Guardian with skeletons. Named `Elite <name>` (SKSE
  `SetDisplayName`), 1.6x base Health, drop a potion.
- **Bosses** every 5th wave: one from the theme's boss list (Goblin Chieftain, Tomb Guardian, Werewolf Alpha, Vatyr
  Leader, Desert Spider Queen, Grotesque Lost One, Lord of the Lost Ones L55, Glacier Hound, Conjured Guardian...)
  named `<name> of the Fog`, 2.5x Health, leading half a pack plus the elites; drops 2 potions and 12 ammo.
  **No elementals among elites or bosses** until this is understood: in the first test most direct musket shots at
  an elite Ice Elemental did no damage (hit registration on that creature's mesh, not the arena; the list's ice
  elementals already carry mesh and physics fixes). Open. **No goblin shamans** either: a goblin shaman's lightning
  freeing a dead Havok body is an open crash (2026-10-26 minidump work).
- **Werewolves** (curator: "werewolves with wolves"): Enderal has no werewolf creature base - the NQ29 boss
  `_00E_NQ29_Boss_Arveldhiin 14DA48` is a human who transforms, as the Theriantrophist player does. `ZFW_Werewolf
  0x4100` (L30, +350 Health) and `ZFW_WerewolfAlpha 0x4101` (L45, +700, height 1.15, `EncClassWerewolfBoss`) are the
  Snow Wolf's record rewritten by `tools/02` onto Skyrim's `WerewolfBeastRace 0CDD84`, which Enderal's Skyrim.esm
  keeps whole: skin `SkinNakedWerewolfBeast`, `WerewolfBeastProject.hkx`, attack data with `werewolfKnockbackSpell`,
  `csWerewolf 0A199D`, `EncClassWerewolf 0A1993`, `CrWerewolfVoice 01F2E6`, `AbWerewolf 0A1A3E`. No scripts, no
  factions, no death item. (Pandora builds the list's werewolf behaviour: see the Pandora overwrite memory.)
- **Skeleton waves use only vanilla-race bases.** Lost Ones Revised re-races most of Enderal's Fleshless Lost Ones
  onto `mihailancientskeletons.esp`'s race `000800`, and two Enemy Density hordes crashed on exactly that race's
  weapon attach (`EnemyDensity.md`; Enemy Density refuses them). The Skeletons / Fleshless Host themes therefore
  use the 13 bases whose winning record keeps `SkeletonRace 0B7998` (`_05E_SkelettBogen`, `_20E_Skelett_Range1200/
  1500`, `_20E_Skelett_Aggressive`, the `_25E_Skelett*` FS variants, `_25E_SkelettGhost`); the Conjured Guardians
  theme was dropped for it. `tools/02` resolves each base's winning race through the list's creature overriders
  (EGO, UCR, Lost Ones Revised and its EGO patch) and prints a WARNING for any Mihail-race base; the build must print
  none.
- **No rewards, but ammo and potions, on the ground:** a dead spawn is locked against looting (`BlockActivation`;
  the first builds used `RemoveAllItems`, which also takes the worn armour off, so dismembered bandits lay naked -
  curator 2026-11-06, traced by the DF session), then its loot is added and at once dropped beside it (`DropObject`): nobody opens 20 corpses in a horde (curator, 2026-11-06:
  nothing but silver bullets was found). 70% of the time (always for elites and bosses) 4-8 (boss 12) of the
  ammo the player has equipped (Papyrus Extender's `GetEquippedAmmo`: bow, crossbow, musket) **and** the Flintlock
  Overhaul's bullet `0x800` whenever the player carries any pistol of its `ZP_FlintlockWeapons 0x802` list (both
  `GetFormFromFile`, so that plugin is not a master). Potions by wave tier (`PotionTier`: Cheap waves 1-4, Standard
  5-8, Quality 9-12, Exclusive 13+; `ZFW_HealthPotions 0x80D` = `02E-05E_Genesungstrank`, `ZFW_ManaPotions 0x817` =
  `02E-05E_Manatrank`; never `01E_Lebenstrank`, the Rancid one the first build used): a boss drops 2 health potions,
  an Ambrosia `0FEC69` and a mana potion; an elite a health potion, 50% an Ambrosia, 30% a mana potion; a regular
  10% a health potion. Corpses are deleted when the next wave spawns; dropped items that were not picked up are
  swept one wave later (`RotateDrops`, two generations of 128 refs) and at the end of the run.
- **Practice death:** the player is essential for the run, so 0 Health is bleedout; `ZFW_PlayerAlias.OnEnterBleedout`
  **and** the 1 s loop (`IsBleedingOut()` or Health <= 0: Enderal has no health regeneration, so an essential player
  never gets up on their own, as the first death showed) end the run: spawns, corpses and drops deleted,
  Health/Magicka/Stamina restored (`RestoreActorValue` in bleedout stands the player up, as SureAI's Well of Life
  `_00E_A2_WellOfLifeScript` does), the player back beside the Whisperwood stone, EPFaction and essential state
  restored, a message box with the wave reached and the best (`ZFW_BestWave 0x80E`; `ZFW_CurrentWave 0x80F` is 0
  outside a run). The exit stone (`ZFW_LeaveMsg 0x811`) ends it the same way. Console escape from a stuck run:
  `cqf ZFW_Arena EndRun true`.
- **Wave banners are quest objectives** (curator, 2026-11-06: "large in the centre screen like the quest text"):
  the quest (`Type: Misc`) carries 55 objectives, shown with `SetObjectiveDisplayed(id, true, true)` and hidden
  again when the next shows (`ShowBanner`, `HideBanner` at the run's end), so the journal never piles them up. Text
  replacement fills them: `OBJ_WAVE0 + theme index` = "Wave <Global=ZFW_CurrentWave>: <Global=ZFW_WaveSize> <theme
  name>", `OBJ_BOSS0 + index` = "...: <Alias=ZFW_Spawn01> leads ..." (the boss always fills alias 1), 1 = cleared,
  2 = start, 3 = new caches. The theme index comes from `ZFW_Themes 0x818` (every theme in `tools/02` order);
  `ZFW_CurrentWave`, `ZFW_BestWave` and `ZFW_WaveSize 0x819` are GlobalShorts so the replacement prints whole
  numbers. **The three globals are the quest's `TextDisplayGlobals` (QTGL)** and `ShowBanner` calls
  `UpdateCurrentInstanceGlobal` on them first: a quest instance captures the globals QTGL names when the quest
  STARTS and the tags read that snapshot, which the call refreshes (every SureAI quest with such tags lists them,
  MQ04 `0A5820`/`0A581F`, and 37 scripts refresh). Without QTGL the tag is never replaced, and an unreplaced tag
  reaches the HUD's Scaleform text field as markup, which swallows it and the rest of the line: two tests read
  "Wave ..." (curator, 2026-11-06). Because the capture happens at quest start, a save whose quest started
  earlier needs the quest restarted once: **`ZFW_StoneScript` (outside the quest) stops and starts it** when
  `ZFW_QuestVersion 0x81C` is below the script's `QUEST_VERSION`, after the quest stored its placed stone in
  `ZFW_Persist 0x81D` (`PrepareRestart`; `EnsureStone` takes it back). The restart also re-reads every script
  property from the plugin. Bump `QUEST_VERSION` whenever the quest record gains objectives, globals or
  properties an old save must see.
- **Fogbound Caches** (curator, 2026-11-06): `ZFW_Chest 0x81A` (Skyrim's `ChestSmall02EMPTY` record, Chest01.nif,
  renamed) placed by the script: 6 at the start of a run and 3 more after every boss wave (array of 32), each on
  one of 40 **cache markers** `0x962`-`0x989` that `tools/01` puts on walkable lattice vertices with no tree within
  a vertex, none within 2 of a spawn marker, at least 2 apart (512 units), outside the entry clearing and **within
  2,700 units of the entry** (the first set was spread over the whole 6x6 wood, and in 2,500 units of fog the
  curator never saw one; the log showed them placed); a marker is used once per run, and each placement is
  logged (`ZFW: cache N at x, y, z`). The first build snapped random spots onto the navmesh with Papyrus Extender's
  `MoveToNearestNavmeshLocation`, which picks the nearest navmesh **vertex**, and `build_navmeshes` keeps every
  tree's vertex (only its triangles are cut), so a chest stood inside a trunk (curator, 2026-11-06).
  Stock by wave tier: 1-2 health potions, 60% a mana potion, 40% a stamina potion, 40% an Ambrosia, 1-2 from
  `ZFW_CachePotions 0x81B` = every Protection potion Enderal ships (Fire Cheap/Exclusive, Frost Cheap, Shock
  Cheap/Enhanced, Magic: only the Rancid `01E_Magieschutz 014E2C` exists). Deleted at the run's end, **after the
  stock is taken back out and whatever else is in them (the player's deposits) goes to the player**
  (`ClearChests` / `RemoveStock`; a tester lost items left in the wood, 2026-11-07).
- **Spawn aliases:** `ZFW_Spawn01-40` (alias IDs 1-40, Optional), filled with `ForceRefTo` as each spawn is placed and
  cleared at its death; their script `ZFW_SpawnAlias` forwards every `OnHit` from a non-player aggressor to
  `ZFW_ArenaQuest.SpawnHit`, which logs aggressor, victim, source, projectile, factions, the aggressor's combat
  target and the victim's hostility (`ZFW hit:` lines; `ZFW target:` lines from `Refocus`), `TRACE_BUDGET` 120 lines
  a run. That is the evidence for the open infighting question.
- **No console, no god mode** (curator, 2026-11-06): the stone refuses a run while god mode is on (Papyrus
  Extender `GetGodMode`), the loop ends a run the moment it turns on, and the quest registers for the `Console`
  menu during a run (SKSE `RegisterForMenu`): opening it ends the run, with the reason in the end message. Papyrus
  cannot disable the console itself; ending the run is the deterrent, and every command, `tgm` included, needs
  the menu open.
- **Every game load** (`OnPlayerLoadGame`) re-checks the stone and restarts the loop if a run was in progress.
- **The loop cannot die of an error** (2026-11-07): `OnUpdate` calls `RegisterForSingleUpdate` before any work.
  It used to register at the end, so one aborting error (a fatal cast, a stack dump) anywhere in the tick ended
  the loop for the rest of the run: no deaths processed, no next wave. A tester's wave 3 never came after wave 2's
  werewolves (2026-11-07); whether this or a lost werewolf was the cause is unknown, both are covered now.
  **Postmortem (2026-11-09): registering first made the tick reentrant.** Papyrus runs every event on its own
  thread, so the tick that arrived a second later ran while `SpawnWave` was still placing its 20-30 actors (a
  `PlaceAtMe` per actor, several seconds), saw `WaveActive` still false and the wave time passed, and spawned a
  second theme on top of the first (the curator: "multiple factions spawn in at the same time"); concurrent
  `ProcessDeaths` would also have paid a death's drops twice. The tick body is `Tick()` now, run under an `InTick`
  flag: a tick that finds the flag up returns, unless the flag is older than `TICK_TIMEOUT` (30 s), which means
  the earlier tick died of an error and never cleared it. `SpawnWave` also stops placing when the run ended under
  it (a bleedout from the alias, the console). The registration-first build shipped only in Patch Collection,
  not in a list release.
- **Every spawn alias carries a package** (`PackageData` = `_DefaultSandboxEditorLocation512 01B217`, 2026-11-09).
  The Vagrant `_10E_Bandit05_Range2500 02F48C` stood in combat, target set, never moving, every time she spawned
  (curator, 2026-11-09). She is the one base of the 145 in `THEMES` whose own package overrides combat: no
  `AIPackages` template flag (the working `_10E_Bandit09_Range2500 02F44A` has it), own package
  `_DefaultSitLinkedRef 0DD723`, whose **`InterruptOverride: Combat`** makes the package run *instead of* the
  combat behaviour, and a `PlaceAtMe` copy has no linked chair to sit on (Enderal places her with a linked ref at
  the Eisbrecherwarte). An alias package outranks an actor's own list, so every spawn now runs a plain sandbox out
  of combat and the engine's combat behaviour in it; `tools/02` prints the bases with such packages
  (`combat_override_packages`). The stuck Vagrant in the 12:25 log was the ranged `02F442` (crossbow, 15 bolts:
  an archer holding position), a different base. Unverified in game.
- **The last few are gathered** (2026-11-07): with `LAST_FEW` (3) or fewer alive and no kill for `NO_KILL_SECONDS`
  (20), every live spawn farther than `NO_KILL_RANGE` (600) is `Relocate`d to the clear marker nearest the
  player (`GatherLastFew`, `ZFW: gathering` lines); nearer ones are left alone, so a long boss fight is not
  mistaken for a lost enemy. A live spawn outside the walls (`Outside`, the player's `BOUND` check) is brought
  back at once: a ragdoll can leave through the edge wall, and the player cannot follow.
- **Bodies are disabled now and deleted a tick later** (the DF session, 2026-11-07): `ClearCorpses` /
  `ClearSpawns` `Doom()` a body (disable it and queue it) and `DeleteDoomed()` runs on the next 1 s tick and at
  the end of `EndRun`, so no body is disabled and deleted in one frame and none in the tick that spawns the next
  wave: a player's crash (2026-11-07) freed an arena skeleton's 3D while IED's weapon re-hang job for it was still
  queued (the `0FDDB2D` chain; postmortem in [`EnemyDensity.md`](EnemyDensity.md)).

## Postmortem: the alias script never bound (2026-11-06)

The first death left the player lying in the fog: no bleedout handler ran. The Papyrus log had it from the start:
`Unable to bind script ZFW_PlayerAlias to <nullptr alias> (0) on <nullptr quest> (00000000) because their base
types do not match`. In the quest's VMAD, each alias script binding is a `Property` whose **`Object` is the quest
itself** and whose `Alias` is the alias ID; `tools/02` wrote `Alias: 0` with no `Object:` (every SureAI quest has
`Object: <the quest>`, e.g. `Abilities 0EEE9B`), so the VM had a null quest and bound nothing. Everything on the
alias was dead: `OnEnterBleedout` (practice death) and `OnPlayerLoadGame` (array growth, stone re-check). Fixed in
the generator (`alias_binding`), and the quest loop now also ends the run on `IsBleedingOut()`. Recorded in
`arch-docs/workspace/spriggit.md`. Lesson: a quest script that never reports anything on an alias is not "quiet",
grep the Papyrus log for `Unable to bind` after every first launch.

**Second half (01:03 launch):** with the alias bound, `OnGameLoaded` died on its first line, `Error: Cannot cast
from None to Actor[]`: `If Spawned == None` is a **fatal** Papyrus error for an array (the VM cannot cast None to an
array type) and aborts the function, so the stone move it was about to do never ran (curator: "it doesn't look like
you actually moved the stone"). Arrays are tested as booleans: `If !Spawned` (false for a None array and for an
empty one). Same fix in `StartRun`. Recorded in `arch-docs/workspace/papyrus.md`.

## Postmortem: same faction is not the same side (2026-11-06)

Three builds in a row had spawns fighting each other, and three fixes in a row were guesses that treated the
symptom: spawning them disabled so no AI ran before `Prepare`, Assistance 0, `IgnoreFriendlyHits`. The third test
(one kind per wave, so species had nothing to do with it) still showed it. The cause is a faction fact read from
Enderal's own data: **the engine does not treat two members of one faction as allies.** A faction's members are
allies only when the faction carries an interfaction relation **to itself**. 102 of Enderal's 339 factions declare
exactly that (`Reaction: Ally`, target = own FormKey): `UndeadFaction 005104`, `AnimalFaction 046E73`, and
`Creature_WolfFaction 103D94`, whose *only* relation is to itself (that is what makes a wolf pack a pack). The
arena faction declared only `PlayerFaction: Enemy`, so every spawn was **neutral** to every other, and a neutral
hit by a stray swing or an area spell is being attacked, which `IgnoreFriendlyHits` does not cover (it is for
*friendly* hits). Fix: `ZFW_ArenaFaction` is `Ally` to itself (`tools/02`). `Refocus` now also writes a line to
the Papyrus log whenever a spawn's combat target is not the player (both names, `IsHostileToActor` both ways,
faction membership, relationship rank), so a recurrence is read, not guessed. Lesson, kept in
`arch-docs/enderal-record-patterns.md`: a new faction whose members must not fight needs itself in its
relations.

**It recurred with the self-Ally faction** (test of 00:31): `ZFW target:` lines show Fleshless Lost Hunters (the
skeleton archers) targeting each other, `hostile TRUE/False` (one way: the attacker holds the victim as a target,
the victim does not yet), both in the arena faction, relationship 0. Those bases share only `UndeadFaction`
(itself Ally to itself), so faction relations are ruled out. Archers in a ring around the player shoot through
each other, so friendly fire from arrows is the suspect, which would mean `IgnoreFriendlyHits` does not cover
NPC-on-NPC hits the way it covers the player's. **Open**: the spawn aliases now log every spawn-on-spawn hit
with its source and the victim's hostility before and after; the next run's `ZFW hit:` lines decide it. If arrows
are the cause, the fix is to make the spawns unable to hit each other (a perk on each spawn with `Mod Attack
Damage` x0 against the arena faction does not stop the hit event; a cleaner route is a dedicated combat style
or spacing the archers so the ring does not fire through itself).

## FormID layout

| Range | Use |
|---|---|
| `0x800` | worldspace `ZFW_FogWood` |
| `0x801` | its persistent cell |
| `0x802`-`0x803` | climate, weather |
| `0x804` | quest `ZFW_Arena` (scripts `ZFW_ArenaQuest`, alias `ZFW_PlayerAlias`) |
| `0x805` | ACTI `ZFW_FogStone` (script `ZFW_StoneScript`) |
| `0x806` | `ZFW_ArenaFaction` |
| `0x807`-`0x80B` | `ZFW_Tier1`-`5` |
| `0x80C` | retired (`ZFW_Bosses` of the first arena), never reuse |
| `0x80D` | `ZFW_Potions` |
| `0x80E`-`0x80F` | globals `ZFW_BestWave`, `ZFW_CurrentWave` |
| `0x810`-`0x811` | `ZFW_EnterMsg`, `ZFW_LeaveMsg` |
| `0x812` | retired (`ZFW_Elites` of the first arena), never reuse |
| `0x813`-`0x816` | pack-size globals `ZFW_PackFull`, `ZFW_PackHalf`, `ZFW_PackThird`, `ZFW_PackMost` |
| `0x817` | `ZFW_ManaPotions` (`0x80D` is `ZFW_HealthPotions`) |
| `0x818`-`0x819` | `ZFW_Themes` (all themes, objective index), global `ZFW_WaveSize` |
| `0x81A`-`0x81B` | CONT `ZFW_Chest` (Fogbound Cache), `ZFW_CachePotions` |
| `0x81C`-`0x81D` | global `ZFW_QuestVersion`, FormList `ZFW_Persist` (the one-time quest restart); `0x81E`-`0x84F` free |
| `0x850`-`0x88F` | the 64 cells |
| `0x8B0`-`0x8EF` | their 64 landscapes |
| `0x910`-`0x933` | the 36 navmeshes |
| `0x950`-`0x953` | the 4 walls |
| `0x954` | entry marker; `0x955`-`0x960` the 12 spawn markers; `0x961` the exit stone's ref; `0x962`-`0x989` the 40 cache markers; `0x98A`-`0x9FF` free |
| `0x1000`-`0x337A` | 9,101 trees and floor plants |
| `0x4000`-`0x4081` | 26 themes, 5 records each: `ZFW_Theme_<X>` (+0), `_Regulars` (+1), `_Elites` (+2), `_Bosses` (+3), `_Name` MESG (+4) |
| `0x4100`-`0x4102` | NPCs `ZFW_Werewolf` (L30, +350 Health), `ZFW_WerewolfAlpha` (L45, +700, height 1.15), `ZFW_WerewolfYoung` (L15, +100, height 0.95: the first-tier pack) |

A regeneration with the same `SEED` and parameters gives the same IDs. **Changing the patch size, the tree
rules or the seed renumbers the refs**: fine while nothing ships, never after.

## The themes (`THEMES` in `tools/02`, 2026-11-06)

| Tier (waves) | Theme | Regulars | Elites | Boss | Pack |
|---|---|---|---|---|---|
| 1 (1-3), 2 | Fleshless Lost Ones | vanilla-race skeletons L5-25 | Conjured Guardian | Conjured Guardian | 1 |
| 1 | Lost Ones | `_08E`/`_14E`/`_16E` Lost Ones + mage | Lord of the Lost Ones L35 | Grotesque L20 / Lord L38 | 1 |
| 1 | Goblins | `ZEN_Goblin/Scout/Archer`, Mihail's goblin/archer/skirmisher | Arp Shaman | Goblin Chieftain | 1 |
| 1 | Wolves and Werewolves | `_10E`/`_18E_Wolf` : 2 Young Werewolves (50/50, curator 2026-11-06) | Werewolf | Werewolf Alpha | 1 |
| 2 (4-6) | Arps | `_17E_Arp01/02/03` + archer | Arp Shaman | Tomb Guardian (L35 Arp) | 1 |
| 2 | Goblin Warband | berserkers, skirmishers, archers, 2x durzogs | Arp Shaman, Goblin Warlord | Goblin Chieftain | 1 |
| 2 | Lost One Warband | `_20E`-`_26E` Lost Ones + archers | Lord L35 | Lord L38 / Grotesque L20 | 1 |
| 2, 3 | Fleshless Host | `_25E_Skelett*` (FS), `_25E_Skelett03/02`, archer | Conjured Guardian | Lord L35 | 1 |
| 2 | Vatyrs | `_15E_VatyrVar01-03`, `_20E_Vatyr/02/03` | Vatyr Leader L24 | Vatyr Leader L35 | 1 |
| 2 | Pus Beetles | `_20E_Pusbug` | `_31E_Pusbug` | `_31E_Pusbug` | 0.7 |
| 3 (7-9), 5 | Withered Lost Ones | `_30E_LostOneDesert01-06` + mage | Lord L38 | Grotesque L50 | 1 |
| 3 | Spiders | Desert Spider, Sand Spider | Frost Crawler | Desert Spider Queen | 1 |
| 3 | Hunting Cats | panthers, Shadow Deerstalker, Lioness | Lion | Lion | 0.7 |
| 3, 4, 5 | Snow Wolves and Werewolves | Young Snow Wolf, Snow Wolf, Elemental Wolf : 3 Werewolves (50/50) | Werewolf Alpha | Werewolf Alpha | 1 |
| 3 | Cave Trolls | L5/15/25 | L33 | L33 | 0.35 |
| 3 | Bears | Young Brown Bear, Brown Bear | Ice Bear L29 | Powerful Brown Bear | 0.5 |
| 4 (10-12) | Spirits | Ancestral Spirit, Crystal Specters L20/30 | Crystal Specter L40 | Crystal Specter L40 | 1 |
| 4 | Vatyr Warband | `_30E_Vatyr01-03` | Vatyr Leader L35 | Vatyr Leader L55 | 1 |
| 4, 5 | Lords of the Lost Ones and their Dead | 1 Lord L35 : 3 Withered Lost Ones (melee) | Lord L38 | Lord L55 | 0.5 |
| 5 (13+) | Elder Vatyrs | `_45E_Vatyr01-03` | Vatyr Leader L55 | Vatyr Leader L55 | 1 |
| 5 | Ice Bears | Ice Bear L29/45 | Ice Bear L45 | Glacier Hound | 0.5 |
| 5 | Grotesque Lost Ones | Grotesque L20 | Grotesque L50 | Grotesque L50 | 0.35 |
| 1, 2 | Bandits (humans, 2026-11-06) | 6 L10 bandits + 3 archers | L17 / L20 bandits | L20 bandit | 1 |
| 3 | Marauders | 5 L20 bandits + 2 archers | Mercenaries L25 | Mercenary (High Elf) | 1 |
| 2, 3 | Wild Mages and Thralls | 4 L20 bandit melee : 3 L12/L26 Wild Mages (a whole wave of casters was too much, curator 2026-11-06) | L30 / L33 Wild Mages | the Oorbaya-summoning Wild Mage | 0.7 |
| 3, 4 | Restless Spirits | 3 Conjured Guardians (melee) : 2 Spectral Apothecarii (casters) | Monk ghost L40 | Monk ghost | 0.7 |

Humans: Enderal's generic bandits, Wild Mages and mercenaries (the `_RangeNNNN`/`_Aggressive` suffix is only the
base's aggro variant); their gear goes with `RemoveAllItems` like every other corpse. Never the `NoRespawn` (Unique)
bandits. Not used, on purpose: elementals (hit registration, above), goblin shamans (lightning crash), Mihail-race
skeletons (horde crash), Oorbayas and wisps as regulars (floating), Nehrimese soldiers and Rhalata (main-quest
factions).

## Regenerating

```
python -I src/FogWood/tools/01-build-wood.py
python -I src/FogWood/tools/02-build-arena.py
```

Then compile `Scripts/source/` with the `papyrus-compile` recipe (Papyrus Extender's source must be on the import path;
`IgnoreFriendlyHits` is on `ObjectReference` in Enderal's and SKSE's source). `tools/02` reads the Snow Wolf's record
from `reference/base-2.1.4.4/Skyrim/Npcs/` and the creature overriders from `reference/mods/`, so both must be
serialized. Deploy: the `.esp` and the four `.pex` into **`mods/Zenderal - Patch Collection`** (the plugin loads after
`Zenderal - Goblins.esp`, its master). Since 2026-11-06 (list 0.9.4, Patch Collection 1.8) Fog Wood ships inside Patch
Collection; the standalone MO2 mod `Zenderal - Fog Wood` is gone (backup in
`E:/Zenderal-backups/2026-11-06-compile-prep/`), so don't let a deploy recreate it.

The script asserts every ID budget, the navmesh edge interpretation, and that no copied ref still points at
another form.
