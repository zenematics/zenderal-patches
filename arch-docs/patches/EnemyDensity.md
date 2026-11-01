# EnemyDensity

- **Source:** `src/EnemyDensity/` (generated: `tools/01-plan-groups.py` → `tools/02-build-groups.py`)
- **Ships:** `Zenderal - Enemy Density.esp` (ESL, HEDR 1.7), placed refs only. MO2 mod `Zenderal - Enemy Density`.
- **Masters:** `Skyrim.esm`, `Update.esm`, `Enderal - Forgotten Stories.esm`, `Zenderal - Goblins.esp` (its goblins).
- **Load order:** **right after `Zenderal - Goblins Dismembering.esp`.** It forwards the same WRLD and cell
  headers Zenderal - Goblins does (from the last overrider before Goblins), so **rerun `01` and `02` whenever
  Goblins' `02`/`03` are rerun** (i.e. when a Vyn cell editor changes).
- **FormID block:** `0x800–0xD9B`, the placed refs (922 in use after the third build, 2026-10-24; IDs of dropped
  groups are not reused). A rerun keeps each surviving group's refs.

## What it does

Curator's brief (2026-10-24): more enemies where it makes sense, so the player meets more combat while
exploring, keeping Enderal's themes. **In addition to** every existing creature: nothing is removed, moved or
replaced. Every group is made of base NPCs Enderal itself places in that region (the EditorID's `_NNE_`
prefix is the creature's level, so each region uses its map level band), or of Zenderal - Goblins' goblins.

| Region (region record) | Groups | Enemies | Mix |
|---|---|---|---|
| Fogville (`Nebelhaim 10A875`) | 27 (target 34, ran out of valid ground) | 168 | 16 goblin packs (Goblins' recipe: ours + Mihail's goblins + durzogs) and 11 Arp camps (`_17E_Arp*`, archers, 35% shaman). The town, harbor, mill, mine and woodworks keep Goblins' marker clearances. Goblins itself excluded Fogville entirely |
| Whisperwood (`PilzwaldRegion 00703D`, in-game "Whisperwoods") | 34 | 223 | Hordes of 5–8 weak undead: low Lost Ones (`_08E`/`_14E`/`_16E`), Enderal skeletons on the vanilla race, 1–2 Lost One archers, 0–1 Lost One mage. No Mihail skeletons (postmortems) |
| Powder Desert (`Wueste 139C4D`, `WuesteSandsturm 09A9BF`, `Desert 043C5D`) | 30 | 165 | Desert marauder camps, Sere Lost Ones (`_30E_LostOneDesert*`), lion prides, Pus Beetle swarms, panthers |
| Crystal Forest (`KristallwaldRegion 12ECF1`) | 14 | 50 | Crystal Specters + Mighty Wisps, Elemental Wolves, Crystal Elementals. No goblins (curator) |
| Frostcliff Mountains (`Nordwindgebirge 0823E4`) | 40 | 137 | Snow wolf packs, Lost One patrols, ice bears, glacier hounds |
| Thalgard (`eThalgardRegion 0022AB`) | 12 (target 16) | 46 | Sunborn patrols, restless spirits (ghost Monks, Elemental Ghost) |
| Goldenforst (`QuellwachtRegion 035CCA`) | 14 | 64 | Vatyr warbands (`_30E_Vatyr01–03`) |
| Western Cliff (`WesternCliff 048089`) | 16 | 69 | Lost One graves, moss crawler nests |

The group tables (sizes, slots, weights, targets, spacing) are the `REGIONS` list at the top of `tools/01`.
To tune a region: edit it, rerun `01` and `02`, deserialize.

## How a site is chosen (`tools/01-plan-groups.py`)

It imports Zenderal - Goblins' planner (`src/Goblins/tools/02-plan-packs.py`) for reading the load order,
the navmesh and every clearance rule (roads, water and waterfalls, people, farm animals, settlement markers,
objects mods added). What differs:

- A site is any walkable navmesh triangle in a cell whose header lists the region; no wild-animal anchor.
- **Quest spots:** no site within 3000 units of a placed ref whose base EditorID names a quest
  (`MQ…`/`NQ…`/`FS…NQ…`), a trigger box, a travel box or a scene trigger, or of **any persistent placed NPC**
  (quest aliases need persistent refs). 602 such refs on 2026-10-24. In Whisperwood that covers MQ05's
  possessed merchant, its scene trigger and dead donkey, MQ12c's Natara voice trigger and the Vatyr Leader.
- No site within 3500 units of a Zenderal - Goblins pack, 3000 between groups of different regions, and
  1200 from any existing creature (decorative dead skeletons ignored) so a group does not merge into a camp.
- Never in Ark, the star city, the intro/temple regions, the tropical idyll or the Isle of Kor.

## How it is built (`tools/02-build-groups.py`)

Imports Zenderal - Goblins' builder helpers (`03-build-packs.py`) and writes the same WRLD/cell scaffolding.
Each EditorID in the plan is resolved from `reference/base/` and **checked against its winning record** in
the load order: present, not deleted, not Unique/Essential/Protected. The winners on 2026-10-24 were mostly
EGO, `mihailancientskeletons.esp` (Lost Ones Revised's copy), Lost Ones Revised - EGO Patch, VicnReplacer,
mihailcrystalgolem and Zenderal - Flintlock Overhaul (the desert marauders' guns).

Respawn: the goblins carry `ZEN_GoblinRespawn`, so they come back after `ZEN_GoblinRespawnDays` (3). Every
other enemy is an ordinary temporary ref and comes back with the engine's cell reset, like Enderal's own.

## Build and deploy

```
python src/EnemyDensity/tools/01-plan-groups.py <all dir> [<cache.pickle>]
python src/EnemyDensity/tools/02-build-groups.py <all dir>
spriggit deserialize src/EnemyDensity/EnemyDensityESP -> Zenderal - Enemy Density.esp
```

`<all dir>` is `src/UnresolvedRefsCleanup/tools/00a-serialize-all.py` output (the 2026-10-21 one was used).

Third build 2026-10-24: 922 enemies in 187 groups. The Spriggit round trip keeps all 922 placed NPCs (first build: 987 in 172 cells ; differs only in float
formatting). All 77 distinct base FormKeys resolve. **Not checked in xEdit.** Deployed to Ultra (profile backup
in `E:\Zenderal-backups\2026-10-24-enemy-density-profile`). The first two builds crashed in game (postmortems below); the third build is **unverified in game**.

## Postmortem: crash on Mihail's skinned bow (2026-10-24, first build)

The first build crashed after 13 minutes (`crash-2026-10-24-17-11-38.log`): `EXCEPTION_ACCESS_VIOLATION` at
`SkyrimSE.exe+0FDDB2D` (`call [rax+0x150]`, read of `0xFFFFFFFFFFFFFFFF`), called from
`ImmersiveEquipmentDisplays.dll+0160DE7`, on node `WeaponBow` (under `NPC Spine2`) of our ref `FE10E963`, an
"Awoken Lost Archer" `_20E_SkelettBogen_Range1200 0FE46C` in a Whisperwood horde (Abandoned Farm, cell -23,5).

`mihailancientskeletons.esp` (Lost Ones Revised's copy) gives 16 skeleton archer bases Mihail's bow
`EAWO_LostOneBow 00463A`, whose world model is a **skinned** mesh, `draugrbowskinned.nif`. Mihail's swords and axes
are not skinned. The list already placed 53 of these archers across Vyn without a crash; the first build added
104, 68 of them in the Whisperwood hordes, 2–3 per group loading together. **Hypothesis, not proven:**
the crash comes from many skinned bows loading their sheathed display at once. Fix: no base carrying `00463A`. The
Whisperwood and Western Cliff archers became `_20E_LostOne01Bow_Range1200`/`_1500` (EGO's Rune Bow `07C983`) and
the `_30E_SkelettGhost_Range1200` became `_40E_SkelettGhost_Range1200` (sword). The tables keep their lengths, so the
rerun kept every site, position and ref: only 92 bases changed. It did recur (below).

## Postmortem: second crash, same spot (2026-10-24, second build)

`crash-2026-10-24-17-58-53.log`: the identical fault (`SkyrimSE.exe+0FDDB2D`, `call [rax+0x150]`, read of
`0xFFFFFFFFFFFFFFFF`, from `ImmersiveEquipmentDisplays.dll+0160DE7`), now on node `WEAPON` (right hand) of our ref
`FE10E9E0`, an "Awoken Lost One" `_10E_Skelett_Aggressive` (melee, Mihail's sword) in a Whisperwood horde near the
Abandoned hunting Cabin. So the bow was not the cause. What the two crashes share: a Whisperwood horde (the
densest groups, up to 14 actors loading together) and a skeleton on Mihail's race
(`000800:mihailancientskeletons.esp`). Mihail skeletons were 125 of Whisperwood's 271, so two hits could still
be chance. **Cause not proven.** The third build removes both suspects:

- **No Mihail skeletons anywhere.** `02` refuses any base won by `mihailancientskeletons.esp` or on its race.
  Whisperwood's weak undead are now Lost Ones (`_08E_LostOne`, `_14E_LostOne`, `_16E_LostOneBlackVer1`, Lost Ones
  Revised's race) plus Enderal's `_20E_Skelett_Range1500` on the vanilla skeleton race; Frostcliff's patrols use
  `_25E_Skelett02/03` and `_26E_LostOne01`; Thalgard's spirits are the ghost Monks and Elemental Ghost only.
- **Smaller, more spread-out hordes:** Whisperwood 34 groups of 5–8 (was 26 of 8–14), spacing 2800.

Changing the tables re-rolled every region after Whisperwood (one shared random sequence), so most groups moved.
If it crashes again with neither suspect left, the next step is turning IED off for a test run.

## What to check in game

- Performance in Whisperwood (about 3.5 enemies per cell, hordes up to 14): frame rate and Papyrus load.
- Groups stand on the ground, not in rocks, water or houses, and none sit on a quest scene (MQ05 road
  through Whisperwood, Fogville's MQ08/MQ09a).
- Fogville goblins and Arps fight side by side (Goblins makes them allies).
- Difficulty per region: the Whisperwood undead should be weak; Frostcliff glacier hounds are level 55.
- Respawn: goblins after 3 days; the rest with cell reset.
