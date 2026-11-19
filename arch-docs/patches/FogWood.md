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
swept. Nothing in the script deleted an item the player dropped until 2026-11-09 (the sweep took only the fog's
own drops, two waves on), so why the tester's items were gone is open: the sweep of unlooted drops is the likeliest
reading of "dropping items". All unverified in game.

**Co-op session, 2026-11-10 ("Fog wood isn't clearing up bodies"):** the curator ran two arena runs (00:56 and 01:06)
as host of a Skyrim Together session with three other players (GreaseBall, Yamato SenJi, Monk MAN; the host's
`tp_client.log` 00:48-01:11). The script's own path was sound (no error on any `Doom`/`Delete`, the loop ticked),
and the bodies still stood, for two co-op reasons found in the logs - postmortem below. Fixed on the Papyrus side
the same night (`SweepCorpses`; the EP fork's `receiveEP` gate in [`FeverDeathLatchFix.md`](FeverDeathLatchFix.md)),
deployed into Patch Collection 01:45, **unverified in game**; the Skyrim Together side (a deleted temporary actor
should be removed on the server, not handed on) is a separate task on the co-op fork.

**Waves that never came (curator, 2026-11-15):** several times the next wave did not spawn after the last visible
kill. The 2026-11-14 solo logs show it: wave 3 of the 22:42 run (24 spawns) had 23 corpses listed when the player
gave up six minutes later, one spawn alive and uncounted, no error and no relocation line (the trace budget was
spent). Two answers in the 01:00 build, deployed into Patch Collection: the stone in the wood now offers **Call the
next wave** during a run (`RunMsg`), and a stall is handled and logged (`STALL_SECONDS`, `TraceSpawns`; both
below). Why the spawn would not die is still open; the next stall's `ZFW left:` lines will say. Unverified in game.

**The Rogue (curator, 2026-11-15):** the entry stone in the pine forest is gone. A man called Rogue, in the Set of the
Tracker, sits on the fence base beside the Castle Bleakstar road sign in Dark Valley and takes the player in through
dialogue; the stone inside the wood is still the way out (section below). Built 13:17, deployed into Patch Collection,
**unverified in game**: the seat height and his facing are first guesses (`ROGUE_Z`, `ROGUE_ANGLE`; bump
`ROGUE_VERSION` after moving them, a save moves him on its next load).

**He was never there (2026-11-19, curator):** both `PlaceAtMe` calls placed him and the seat with `abInitiallyDisabled`
and nothing enabled either (the stone's placement had its `Enable()`; his was dropped), so from 2026-11-15 to 11-19 every
save carried an invisible Rogue and an unusable seat. Fixed the same day: both enabled (existing saves too, on their next
load), the seat moved to the wall's front edge (`ROGUE_VERSION` 2), the player's return spot lowered to the ground, and a
10 s idle tick that re-seats him and logs `ZFW: the Rogue at ...; sit state N (3 = sitting)` once per load when his cell
is in. Deployed into Patch Collection. **The log answered it the same evening (18:46):** `ZFW: the Rogue moved to
-79195.6, 43215.1, 1144.6 (version 2)` on load, then `ZFW: the Rogue at ...; sit state 3 (3 = sitting), 0.01 from the
seat, package _DefaultSitLinkedRef, disabled False/False, linked TRUE`: the AI does sit an actor in a chair marker with
no navmesh under it when he is moved onto it. Whether he *looks* right on the wall is the curator's call. **Voiced the same evening:** the curator recorded his first three lines
through Motion Array (MP3) and asked for *greeting and goodbyes, additional lore and lines for if a player has TGM*; he
now has 15 lines (`0x827`-`0x838`, bullets below). By the end of the evening the curator had recorded all 15 (MP3) and
reworded seven after recording (`who_1` became a 29 s monologue): the texts below are the final ones and every recording
is installed through `tools/03` with lip sync from those texts. Plugin and script redeployed into Patch Collection.
Unverified in game.
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
  swept when the next wave comes and at the end of the run. **The ground is cleaned each wave** (curator,
  2026-11-09): corpses are doomed `CORPSE_WIPE_DELAY` (2 s) after the wave clears, and before the next wave spawns
  `ClearDrops` takes both drop generations and `SweepGround` deletes every loose weapon, armour piece, ammo stack
  and potion in the wood (Papyrus Extender `FindAllReferencesOfFormType` within `SWEEP_RADIUS` 24,000 of the
  player, loaded refs only): the weapons the dead dropped from their hands, severed limbs' gear, and anything the
  player set down, which the entry message warns of. Until then a drop survived one wave (`RotateDrops`, two
  generations of 128 refs).
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
- **Every dead arena actor in the wood is swept, listed or not** (`SweepCorpses`, from `ClearCorpses`, 2026-11-10):
  Papyrus Extender `FindAllReferencesOfFormType(PlayerRef, 43, SWEEP_RADIUS)` (NPC_ bases = every actor), then
  dead + in `ZFW_ArenaFaction` + in the wood + not the player → `Doom`. It catches the corpses Skyrim Together sends
  back (postmortem below; spawned characters get their factions back, so the faction test finds them) and any
  body the 80-slot list never held. Companions, summons and remote players are not in the faction. `ClearCorpses`
  now traces once per call outside the budget (`ZFW: doomed N listed corpses, swept M other dead arena actors`),
  and the wave clear traces `ZFW: wave N cleared, K corpses listed`: the 2026-11-10 log could not say whether the
  wipe had run because the `ZFW target:`/`ZFW hit:` lines had spent `TRACE_BUDGET` in the first wave.
- **The stone calls the next wave** (`ZFW_RunMsg 0x81E`, 2026-11-15): activated during a run it asks *Call the next
  wave / Leave the Fog Wood / Stay*. The call only raises `ForceNext`; the loop acts on it at the top of its next
  tick (never beside `SpawnWave` or `ProcessDeaths`): whatever still stands is `ClearSpawns`'d and the wave ends
  without caches (a forced wave is not a cleared one), the next spawns after `FORCED_WAVE_DELAY` (3 s); called
  between waves it just shortens the wait. `QUEST_VERSION` is 3, so a save from before `RunMsg` existed restarts the
  quest once at its next stone activation and gets the property; until then the stone shows the old leave box.
- **Stalls are escalated and logged** (2026-11-15): the 20 s gather (`NO_KILL_SECONDS`) now runs on its own clock
  (`LastGatherAt`; it used to reset `LastKillAt`, so "no kill for N seconds" could never grow past 20). With
  `LAST_FEW` or fewer alive and no kill for `STALL_SECONDS` (60), `GatherLastFew` also brings every remaining
  spawn that has no line of sight to the player (`HasLOS`, valid with the player as target: under the ground,
  behind a wall; a boss in plain sight keeps its fight) and `KillEssential`s one bleeding out at 0 Health (no theme
  base is Essential or Protected - 131 scanned on 2026-11-15 - so this is a net, not a fix). The first three gathers
  of a wave and every forced wave log each remaining spawn outside the budget (`TraceSpawns`: dead, Health,
  bleedout, 3D, disabled, distance, Z against the player's, LOS, combat state and target, AI, worldspace).

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

## The Rogue at the signpost (2026-11-15) - Dakeyras since 2026-11-19

The curator wanted a person instead of the Vyn stone: *a male Rogue wearing the Tracker armor, sat on a wall somewhere
in Dark Valley, that you speak to*. Dark Valley is region `Jonas 0023A3` (123 Vyn cells; the Old Watermill, Bone Farm,
Castle Bleakstar, the Alchemist's camp). Its only low walls are Whiterun-kit farm-fence bases (`WRFenceBase*`, 75 units
high) in a few roadside stubs; the one a traveller passes is the fence base `032FEA` (`WRFenceBaseEnd01`, at
(-79220.68, 43170.23, 1101.59), yaw 0.744 rad) 42 units from the Fahlstern road sign `0297A5`/`0297A6` (FS; Fahlstern =
Castle Bleakstar) in cell `WaldTuerme 001D6C`. EPPI Improved Locations overrides that cell with one far object; nothing
moves the fence or the sign; a Goblins pack stands 1,450-1,740 units east of the seat.

- **Records** (`tools/02`, `0x81F`-`0x826`): NPC `ZFW_Rogue 0x81F` = `_03E_BanditSunCoastDamCamp 02F435`'s record (FS,
  Traits-templated on the male Highwayman face `02A1BA`, so it needs no facegen of ours) made ours: Essential + Unique,
  level 10, `TemplateFlags: Traits` only, no factions, no scripts, no items, Unaggressive / Cowardly / HelpsNobody,
  class `CombatRogue 013180`, outfit `ZFW_RogueOutfit 0x820` = the Set of the Tracker (`_25E_LSet_Pathfinders*`
  cuirass `0508C6`, boots `0508C4`, gauntlets `0508C8`, hood `0508CB`; the set bonus item is not worn), packages
  `_DefaultSitLinkedRef 0DD723` then a sandbox. Two top-level player branches (`Category: Player`, `TopLevel`) on the
  arena quest: *Take me to the Fog Wood.* (`0x821`-`0x823`; the response carries the TopicInfo fragment
  `ZFW_RogueTake`, run **OnEnd** so his line finishes, → `ZFW_ArenaQuest.RogueTake` → god-mode check → `StartRun`) and
  *What is the Fog Wood?* (`0x824`-`0x826`, two lines). Every response is conditioned `GetIsID ZFW_Rogue`. Topics are
  folders (`DialogTopics/<EditorID> - <FormKey>/RecordData.yaml` + `Responses/`), the shape of
  `ArkGenericDialogue_Museum1_0 028EA4`; `topicinfo.psc` for the fragment is in `papyrus-source/vanilla-stubs`.
- **Placement by script, no Vyn cell edited** (as the stone was): `EnsureRogue` reads the NPC base, the furniture
  `InvisibleChairMarker 06411B` and the anchor (Alchemist's Abandoned Camp map marker `053B65`, a persistent Vyn ref
  5,400 units away) **by FormID with `GetFormFromFile`, not through properties**: a quest's properties are captured at
  its start and the stone that used to trigger the one-time restart is gone, so an existing save gets him on its next
  load with no restart. It places the seat at `ROGUE_X/Y/Z/ANGLE`, places him, links the seat to him (Papyrus
  Extender `SetLinkedRef`, which `_DefaultSitLinkedRef` sits him in), moves him onto it and `EvaluatePackage`s; both
  are persistent and kept in `ZFW_Persist` across a quest restart (an actor = the Rogue, the furniture = the seat,
  anything else = an old stone). Every load and idle tick it puts him back on the seat if he is more than 200 units
  from it and not fighting, and `RetireStone` deletes the Vyn stone of a save from before. `ReturnToRogue` (run end,
  console exit) drops the player 160 units in front of him, facing him, 17 above the road there (ground 1082; the
  first build's `ROGUE_Z - 20` dropped him 42 units). The seat, in the fence base's own frame: (-12, 50, 75) = world
  (-79195.6, 43215.1, 1176.6), 12 toward the road so the hips sit at the front edge and the lower legs hang in front
  of the stone (the wall is 64 thick), 50 along it (47 from the sign board at its near end); the chair marker's root
  is the sitter's feet, so it sits 32 lower (`ROGUE_Z` 1144.6) and faces the wall's left normal (yaw - 90° = -47.4°),
  where the sign and the road are. The ground round the wall is 1068-1073 (the cell's LAND), so the wall top is 106
  up and his feet hang 72 above the road. Whether the AI sits him in a seat with no navmesh under it is the open
  question: the idle tick (`IDLE_TICK` 10 s) logs `ZFW: the Rogue at ...; sit state N (3 = sitting), <distance> from
  the seat, package ...` once per load when his 3D is in; the fallback is to move the seat down to the ground in
  front of the wall.
- **Postmortem, the disabled Rogue (2026-11-19):** `PlaceAtMe(form, 1, True, True)` places *disabled* (the fourth
  argument) so the position can be set before anything shows; the stone's placement followed it with `Enable()`, the
  Rogue's and the seat's did not, and no log says so (a disabled actor raises nothing). Four days of "unverified" were
  really "not there"; the curator noticed. `EnsureRogue` now enables both whenever either is disabled, so the saves
  from those days heal on their next load. Rule: after a `PlaceAtMe` whose fourth argument is true, the `Enable()`
  goes on the next line.
- **More of him (2026-11-19, curator: greetings, goodbyes, lore, god mode):** three more top-level player topics
  (`tools/02` `ROGUE_LORE`, branch / topic / INFO each): *Who are you?* `0x830`-`0x832` (*Me? A Hunter of sorts, tracked my prey a
  little too far into the Fog... it was only then... I realised... I wasn't the one hunting... The Fog it's unnatural...
  it changed me... Now I listen... Fog shifts, it beckons... I just point the way to those worthy of it... safer that
  way I suppose... The woods are my home now, never much liked stone walls and people anyway.* / *It's not me you
  should concern yourself with, I can take you to that which you seek.*), *What walks in the fog?* `0x833`-`0x835`
  (*Everything Vyn has to offer with teeth or a blade. Lost Ones, Arps, goblins, wolves, men. Worse, deeper in.* /
  *They come in waves, each thicker than the last. If you fall, the fog spits you out. I don't know what magic rests
  within it, but my guess is... it gauges strength... awaiting a worthy challenger... Why else would it manifest such
  entities within it, beckoning those with strength to tread deeper into its fog...*), *Is there anything to gain in
  there?* `0x836`-`0x838` (*Practice. The fog takes its
  dead back, so there's no loot worth the name and nothing to remember them by.* / *There are caches, if you look.
  Potions, mostly. The fog is generous with those, and with nothing else.*). Hellos `ZFW_RogueHello 0x828` and
  goodbyes `ZFW_RogueBye 0x82C` are Misc topics on the quest (`ArkGenericDialogue_Hellos 132D46`'s shape: Category
  Misc, Subtype Hello/Goodbye, no branch), one INFO per line flagged Random (+ RandomEnd on the last) so he varies
  them: *The mist's creeping in... what do you want?* / *The fog's still there... It always is.* / *The Fog's thick
  tonight...* (`0x829`-`0x82B`); *Mind the fog.* / *Don't get lost in the woods now...* (`0x82D`-`0x82E`). The curator
  reworded hello_1, hello_3, bye_2, who_1, who_2 and walks_2 (and hello_2's pause) after recording; my first drafts
  are in the git history. Only punctuation was normalised (dot runs to three, apostrophes, a capital after `?`). **God mode:** no condition function reads it, so GLOB `ZFW_GodMode 0x827` is set by the script
  (`UpdateGodMode`, PO3 `GetGodMode`) when the dialogue menu opens (`RegisterForMenu("Dialogue Menu")`; an INFO's
  conditions run when the player picks the topic, a few frames later) and each idle tick; *Take me to the Fog Wood.*
  then answers with `ZFW_RogueTakeRefuseInfo 0x82F` (*No. The fog wants something it can take. Come back when you can
  bleed.*, `GetGlobalValue == 1`, no fragment, so no run) instead of the normal line (now `== 0`); `RogueTake` keeps its
  message box for a stale global. Every INFO still carries `GetIsID ZFW_Rogue`. Round-tripped through Spriggit: 11
  INFOs, 15 lines, flags and conditions identical.
- **Voice (2026-11-19):** `tools/03-install-rogue-voice.py --lines` prints the 15 lines with the file names they become;
  `--src <folder>` turns `<name>.wav` or `<name>.mp3` (`take_1`, `tgm_1`, `what_1/2`, `who_1/2`, `walks_1/2`, `gain_1/2`,
  `hello_1/2/3`, `bye_1/2`; MP3 through imageio-ffmpeg's bundled ffmpeg, the only decoder on this machine) into
  `Sound\Voice\Zenderal - Fog Wood.esp\VT_Male_Bandit01\zfw_arena_zfw_rogue<topic cut to 16>_000008xx_<n>.fuz` in
  Patch Collection, through the Creation Kit's LipGenerator / xwmaencode / LIPFuzer with the records' own text
  (`--silent` = silent placeholders of the reading time, so an unrecorded line's subtitle still stays up). The naming
  rule and the recipe: [`workspace/voice-files.md`](../workspace/voice-files.md). Installed 2026-11-19: the curator's
  Motion Array recordings of all 15 lines (kept under their line names in `E:/Zenderal-backups/2026-11-19-rogue-voice`,
  not committed; the lip sync inside them is 7-37 KB of phonemes, a test tone's was 75 bytes). When a recording's wording differs from the INFO text,
  change the text and rerun: the lip sync is generated from it. Finding the reworded ones without the author's text:
  Windows' offline `System.Speech` dictation (`SpeechRecognitionEngine`, `SetInputToWaveFile` on a 16 kHz mono WAV)
  is rough but enough to tell a changed line from an unchanged one; its `Recognize()` repeats the result until the
  stream ends and then throws, so dedupe and catch.
- **Dakeyras (curator, 2026-11-19 evening):** *change his appearance to my preset "Zen's Joseph Goatee"*, *rename
  him to: Dakeyras*, *remove the tracker helmet / mask too*, and *make him sit on this rock* (a screenshot of a boulder
  by the hay cart 540 units south-west of the sign). The record (`tools/02` `DAKEYRAS_*`): Name Dakeyras; the Traits
  template on the Highwayman face dropped; race Half Qyranian `013748` (the preset's face part is High Poly Head's
  `00KLH_MaleHeadRedguard 000805`); the seven head parts, 18 NAM9 morphs, NAMA presets 9/1/15, skin-tone tint
  (`#615349`, race tint index 1, also QNAM), weight 75 and head texture `SkinHeadMaleRedGuard20 05164B` read from the
  `.jslot` in `overwrite/SKSE/Plugins/CharGen/Presets/` (a RaceMenu `formIdentifier` of an ESL carries the index
  bits: *Beards of Power.esp|032974* is `000974`); a hair-colour record of his own, `ZFW_DakeyrasHair 0x839`
  (`#1A1C1C`). The plugin masters `High Poly Head.esm`, `Beards of Power.esp` and `Brows.esp` since (Brows.esp will
  not serialize in Spriggit 0.40 - its one brow record was read from the binary). Outfit `0x820` without the hood.
  **The face itself comes from RaceMenu at runtime** (the curator: *you have the facedata, get it applied however you
  can*): `ApplyDakeyrasFace` calls `CharGen.LoadCharacterPresetEx(him, "Zen's Joseph Goatee", ZFW_DakeyrasHair, -1)`
  once per `DAKEYRAS_FACE_VERSION` while his 3D is loaded (idle tick), which puts the `.jslot`'s head parts, every
  slider including the six RaceMenu-only ones, and tints on him and rebuilds his head; the preset file ships in Patch
  Collection under `SKSE/Plugins/CharGen/Presets/` (not committed). `chargen.psc` warns *DO NOT USE ON NPCs* because
  it changes the actor base for good; he is unique and that is wanted. The open risk is the tint (a dark face) if
  RaceMenu does not generate one for an NPC without facegen files: the log line `ZFW: Dakeyras takes the preset`
  says whether the call succeeded, the in-game look says the rest. Fallbacks, both needing baked files: RaceMenu's
  Export Head with the preset on the player (the curator's character, Gunslinger, is a female Breton, so not as
  is), or `cqf ZFW_Arena DakeyrasFace 2` (`CharGen.ExportHead`, same thing, into `SKSE/Plugins/CharGen/`), then
  `tools/04-install-dakeyras-face.py --export <name>` copies `<name>.nif` + `.dds` to `FaceGeom`/`FaceTint\Zenderal -
  Fog Wood.esp\0000081F.*` in Patch Collection; a Creation Kit bake would drop the six RaceMenu-only sliders, and
  the list's CK (CKPE 0.4, CK 1.5.73, Root Builder) exits within ten seconds of launch anyway (2026-11-19, from
  MO2's Run button and from `moshortcut://`; no CKPE log written), cause not looked into. **The boulder** (confirmed by the curator: the one their last save stood on): `RockL05 0548FA` at
  (-80154.4, 42882.8, 1152.1), yaw 314.2, crown 1338, 300 across, beside the hay cart `12DABB` on the road 540 units
  south-west of the sign. `ROGUE_VERSION` 3: the seat at (-80026.4, 42826.2, 1271.0) facing 105 (the road and the
  cart) = the crown's eastern edge on the list's winning mesh (PG Patcher's copy of ERM's RockL05), computed by
  `scratchpad/rock_seat.py` the wall's way: hips 12 units inside the point where the surface falls 40, chair-marker
  root 32 below the surface (1303), so the lower legs hang over a 60-unit drop; the LAND under that edge is ~1177.
  `ReturnToRogue` now puts the player 200 units ahead of him at `ROGUE_Z - 79.2` (LAND 1176.8 there, clear of the
  small rock `0548FC` and the cart). A save from before moves him on load. Voice type unchanged, so his 15 lines stay.
  Plugin and script redeployed 2026-11-19 evening; the face still waits for the RaceMenu export (`tools/04`).
- **Kept:** the exit stone in the wood (`0x961`, `ZFW_StoneScript`) and its run-time box; the `EnterMsg` path in
  `StoneActivated` is only reachable through a console-placed stone now.

## Postmortem: the bodies that came back (co-op, 2026-11-10)

Two mechanisms, both outside the arena script, both read off the host's logs of the 2026-11-10 session (Papyrus
`Papyrus.1.log` 00:40-01:11, `overwrite/SkyrimTogetherReborn/logs/tp_client.log` 00:48-01:11).

**1. Skyrim Together hands a deleted corpse to another player instead of removing it.** When any local actor
leaves the game - unloaded *or* deleted - the client's `OnActorRemoved` → `CancelServerAssignment` sends the server
`RequestOwnershipTransfer{Relinquish}` for an actor it owns (`Transferring ownership of local actor`, 202 times that
session); the server's `OnOwnershipTransferRequest` then looks for the next player in range and only removes the
character when nobody can take it (`TransferToNextOwner`; a *player summon* is the one case it removes at once). So
every corpse `Doom`/`DeleteDoomed` deleted on the host lived on, owned by GreaseBall or Yamato, visible on their
screens, and when the host left and re-entered the wood the server sent them all back as
`CharacterSpawnRequest ... dead: true` - **89 of them within seven seconds at 01:06**, right as the second run began.
With quest sync off each player's arena is its own quest, so the other players' waves' corpses arrive the same
way. Host-side answer: `SweepCorpses` (above) deletes them locally each wave; they return on the next re-entry
until the client tells the server a *deleted* temporary should be removed everywhere (the client can tell: the
removal scan still sees `IsDeleted()`/`IsDisabled()` on the actor; the server already deletes temporaries on
`NotifyRemoveCharacter`). That is the Skyrim Together task, not this patch's.

**2. Every synced death pays the host EP, and 100+ of those spun on Enderal's level-up lock.** Enderal's
`_00E_EPOnDeath.OnDeath(akKiller)` pays `RewardExp` when the killer is in `EPFaction` **or when `akKiller` is None**.
A death another player caused reaches the host as a state change (`Killing actor ... to match server state`, or the
health broadcast), with no killer actor - every one of the 455 `OnDeath` frames in the session's stack dumps had
`[akKiller]: None`. The arena takes the host out of `EPFaction`, which stops the host's *own* kills from paying,
and nothing else: each synced kill called `_00E_EPHandler.GiveEP(225)` → `receiveEP` → `_LockLevelUpSystem`, a
spinlock on `Utility.WaitMenuMode(0.1)`. From 01:07:19 the VM logged `Suspended stack count is over our warning
threshold` every minute with 103-123 of these stacks waiting, which is the Papyrus budget gone: our one-second
loop, `Disable()` and `Delete()` crawl behind them. Fixed in the shipped fork of `_00E_EPUpdateFunctions`
(`receiveEP` returns before the lock when the player is outside `EPFaction 039DCE`,
[`FeverDeathLatchFix.md`](FeverDeathLatchFix.md)). Solo, the player is the killer, so neither the EP nor the
storm happened; this is why the 2026-11-05 solo tests never showed it.

Also in that log: the host's companions/co-players in the hit traces are the `FF` actors named GreaseBall,
Yamato SenJi and Monk MAN (Skyrim Together builds remote players as runtime actors); the arena's `StartCombat` and
relocations only bind spawns the host still owns. What the waves should chase with several players in the wood is
an open design question, not a bug of this build.

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
| `0x81C`-`0x81D` | global `ZFW_QuestVersion`, FormList `ZFW_Persist` (the one-time quest restart) |
| `0x81E` | `ZFW_RunMsg` (the stone during a run: call the next wave / leave / stay) |
| `0x81F`-`0x820` | NPC `ZFW_Rogue`, OTFT `ZFW_RogueOutfit` (the Set of the Tracker) |
| `0x821`-`0x826` | the Rogue's dialogue: branch / topic / response for *Take me to the Fog Wood.* and *What is the Fog Wood?* |
| `0x827` | GLOB `ZFW_GodMode` (set by the script as the dialogue menu opens; the *Take me* answers condition on it) |
| `0x828`-`0x82B` | `ZFW_RogueHello` (Misc, HELO) + 3 Random greeting INFOs |
| `0x82C`-`0x82E` | `ZFW_RogueBye` (Misc, GBYE) + 2 Random goodbye INFOs |
| `0x82F` | `ZFW_RogueTakeRefuseInfo`: *Take me* with god mode on |
| `0x830`-`0x838` | lore topics *Who are you?* / *What walks in the fog?* / *Is there anything to gain in there?* (branch / topic / INFO each) |
| `0x839` | CLFM `ZFW_DakeyrasHair` (the preset's near-black hair); `0x83A`-`0x84F` free |
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
