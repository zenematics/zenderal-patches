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

## Postmortem: third crash, a player's, third build (2026-10-31)

A player's `crash-2026-10-31-13-30-29.log` (53 min in) has the identical fault (`SkyrimSE.exe+0FDDB2D`,
`call [rax+0x150]`, from `ImmersiveEquipmentDisplays.dll+0160DE7`), now on node `WeaponBack` (under `NPC Spine2`)
of our ref `FE10FC7D` = `000C7D`, a "Lost Swordsman" (base `09286C`, cell `0052B7` -2,-2 in the build, on the coast).
No Mihail skeleton was involved this time, so neither suspect above was the cause. The player blamed the
pistol holsters ([`IEDPistolHolsters`](IEDPistolHolsters.md), 2026-10-29), but the first two crashes predate them.

**What the code shows** (the list's `SkyrimSE.exe` 1.7.104 has the player's MD5, disassembled 2026-10-31):

- The chain is the game's own `15656` → IED's hook → `15659` → `15661` → `76207`. IED only sits on the stack as the
  hook trampoline; the fault is in vanilla code.
- `15661` re-hangs a sheathed weapon. It reads the item (`[rdi]`, form type `0x29` = WEAP), **skips staff-type
  weapons** (`cmp byte [weap+0x19D], 8`), takes the sheathe node name for the weapon type (`0x2887E0`) and calls
  `76207(BipedAnim->root = [r13+8], name)`. r13 is the actor's `BipedAnim` (its `actorRef` handle is at `+0x2770`).
- `76207` is a node lookup by name, a virtual call on that root. The root's vtable pointer was a heap address
  (`0x1CF28E3C280`), so **the biped still pointed at a 3D root that had already been freed**. The weapon's own 3D
  was still attached to a live `WeaponBack` node.
- The pistols are staff-type weapons, so they never reach this path: **the holsters are not the cause.**
- `76207` returns 0 for a null root, and `15661` checks `test r12, r12` before using the result. So a guard on
  the call at `+0x2180F9` that answers "not found" when the root's vtable is not in the exe image takes a path
  the game already handles.

All three crashes were Enemy Density undead (Lost Ones/skeletons) loading in groups. Their races are all ones
[`LostOnesDismembering`](LostOnesDismembering.md) gave DF limbs: the two Awoken skeletons were on
`mihailancientskeletonrace 000800`, and the Lost Swordsman `_16ELostOneBlackVer1 09286C` is on `LostOneTemplateRace
00398C` (Lost Ones Revised - EGO Patch's winning record). That patch was live from 2026-10-19, before the first
crash. Those races are also almost all of Enemy Density's undead, though, so these crashes can't separate the two.
**Next evidence to collect:** the player's `DismemberingFramework.log` from the crashing session, before
relaunching. DF stamps its hit-time warnings with the time, so it shows whether DF was working at the second of
the crash. What frees the root while the biped keeps it is **not known**. Candidates: Dismembering Framework (it rebuilds 3D; our Lost Ones Dismembering
patch gave these races DF limbs), Next-Gen Decapitations, or many actors' 3D loading at once. Enemy Density makes
it more frequent rather than causing it: its refs are plain (base, position and rotation, no flags).

## Postmortem: fourth crash, a second player, at a Goblins pack (2026-10-31)

Another player's `crash-2026-10-31-20-01-28.log` (1 h 51 min in, "after killing some goblins") has the same
fault through the same chain: `15656` → IED → `15659` → `15661` → `76207`, `call [rax+0x150]`, on a job thread.
This time the weapon hung on `WEAPON` under `NPC R Hand`. The log does not name the actor.

- **The root was freed again.** The root's "vtable" `0x25333A27880` lies `0x180` below the root
  `0x25333A27A00`. That is the free-list link of a freed block in the same size class. By the time Crash
  Logger wrote the log, the block had been reused: it labels the root a tree `BSTriShape`.
- **Enemy Density was not involved.** The player stood in Vyn -9,9 (`001F90`). The nearest group is
  [`Goblins`](Goblins.md)' Old Dolesh pack at -9,8 (Mihail's goblins and 2 durzogs), and no Enemy Density group
  is within 5 cells.
- **DF is the leading suspect, but not proven.** All four crashes were on actors whose races our DF patches give
  limbs: [`LostOnesDismembering`](LostOnesDismembering.md), and Goblins Dismembering for Mihail's goblins and ours.
  That points at Dismembering Framework, or DF running our configs. These are also the only races Enemy Density
  and Goblins spawn in numbers, though.
- **A threading race is plausible but unshown.** DF 1.2.3 runs work on threads of its own (strings
  `_beginthreadex`, `WaitAndCall`, `WaitUntilRagdollReady`), while `15661` runs on a job thread.

## Postmortem: fifth crash, the same player, an Enemy Density skeleton (2026-11-01)

The same player's `crash-2026-11-01-01-01-06.log` (3 h 14 min in) has the same fault and chain, this time with the
actor named: our ref `FE10FB45` = `000B45`, a "Fleshless Lost One". That is Enderal's `_20E_Skelett_Range1500`
(`048388`, EGO's record) on `SkeletonRace 0B7998`, in a Whisperwood undead horde at -24,6 near Abandoned Farm.
[`LostOnesDismembering`](LostOnesDismembering.md)'s DATA covers `mihailancientskeletonrace|SkeletonRace`, so this is
**five of five crashes on races our DF patches give limbs.**

- **The ref flags differ between crashes.** Here they are `0x00450C0A`: `0x800` (the bit `IsDisabled()` reads) and
  `0x400` are set. Pixel's Lost Swordsman had `0x00450408`, not disabled. So disabling is not common to all the crashes.
- **The player's `DismemberingFramework.log` could not settle it.** It was taken from the crashing session (started
  21:46:57) and is clean up to 00:51:19, 10 minutes before the crash. The only runtime lines are DF's
  `The form obtained from the "IsEquipped" condition parameters is not valid` warnings. Those come from the 22
  `IsEquipped` conditions in our `LostOneTemplateRace` neck entries, which name Skyrim draugr helmets
  (`Skyrim.esm:0x1F6AD`…) that Enderal lacks. So they mark DF choosing a Lost One's head, nothing else. The
  skeleton entry has no conditions, and DF logs nothing on a normal cut, so the log can neither show nor exclude a
  cut at 01:01.
- **DF's source has a mechanism that fits.** In `Seb263/SkyrimSE_DismemberingFramework` `eacedd8`, `Main.cpp`:
  - each cut in `ProcessDismemberment`, run inside the game's hit processing, calls `DropTargetItem`. That is a
    `RemoveItem(kDropping)` of the worn armour in the limb's slot.
  - It then calls `EquipArmorAddon`, an `ActorEquipManager::EquipObject` of the stump-cap ARMO on the dying actor.

  The stump-cap equip is the step that made Spider SE corpses vanish and reload their whole 3D for ~8 s
  (LostOnesDismembering, spiders shelved). A whole-3D reload frees the old root, which is exactly what `15661`
  then dereferences. Our goblin, Lost One and skeleton limbs all use cap templates. **Still a hypothesis:** no crash
  has been timed to a cut. The one crash seen exactly at a cut, an Arp head on 2026-10-26, lost its log
  ([`ArpDismembering`](ArpDismembering.md)).
- **No-DLL test, deployed 2026-11-01:** our goblin, Lost One and skeleton limbs now use actor-addon templates with
  only `ActorArtObject` (blood) and no `ActorArmorAddon`, as the spider plan already did. `STUMP_CAPS = False` in
  LostOnesDismembering `tools/01` and Goblins `tools/06`. Details and the verdict rule are in
  [`LostOnesDismembering`](LostOnesDismembering.md#stump-caps-off-a-crash-test-2026-11-01-deployed-unverified).
  **Counterpoint:** human enemies (DF's humanoid pack) still get caps on every cut and have never shown this crash.
  So the caps alone may not be it.

## Postmortem: sixth crash, a player's, in the Fog Wood arena, stump caps off (2026-11-07)

A player's `crash-2026-11-07-05-00-46.log` (28 min in, same exe MD5) has the same fault through the same chain:
`15656` → `ImmersiveEquipmentDisplays.dll+0160DE7` → `15659` → `15661` → `76207+0x6D` `call [rax+0x150]` on a job
thread (`69378`/`69380` → `36468`/`36477`), the weapon on `WEAPON` under `NPC R Hand`. Three things are new:

- **It is a [`FogWood`](FogWood.md) arena spawn, not Enemy Density.** The actor is `FF0012FB` "Decayed Lost one",
  a `PlaceAtMe` ref of EGO's `_25E_Skelett02`/`03` (`090BBF`/`090BBE`, the arena's skeleton theme in `tools/02`) on
  `SkeletonRace 0B7998`; its parent cell is Fog Wood's `Wilderness 0x85000874`. Sixth crash, sixth DF-limbed race.
- **The actor was already deleted.** Its flags are `0x00570D2A`: `0x20` (deleted) and `0x800` (disabled). That is
  the arena's `ClearCorpses()` / `ClearSpawns()`: `Disable()` then `Delete()` back to back, for every corpse of the
  wave in one Papyrus frame, and `SpawnWave` in the same tick. A deleted actor's 3D is freed while the weapon
  re-hang job for it is still queued, which is exactly the freed root `15661` dereferences. The five earlier
  victims were not deleted (`0x00450C0A`, `0x00450408`), so deletion is the arena's trigger, not the common cause.
- **The stump caps were off.** Patch Collection 1.8 (installed 2026-11-06 16:53) ships
  `Zenderal_LostOnes_TEMPLATES.json` with no `ActorArmorAddon`, and Fog Wood ships only inside that build, which the
  player's load order has. **By the verdict rule in
  [`LostOnesDismembering`](LostOnesDismembering.md#stump-caps-off-a-crash-test-2026-11-01-deployed-unverified), the
  caps were not the cause**; `STUMP_CAPS = True` again in both generators the same day, output identical to the
  caps-on backups, deployed into Patch Collection.

**Arena mitigation, applied 2026-11-07 (script only, no DLL):** `ClearCorpses()`/`ClearSpawns()` now `Doom()` a body
(disable it and queue it) and `DeleteDoomed()` runs on the next 1 s tick and at the end of `EndRun`, so no body is
disabled and deleted in the same frame, and none in the tick that spawns the next wave. **Caveat:** the fifth
victim was disabled but not deleted, so a disable alone (the 3D release) can be enough to free the root; if the
arena crash recurs with the split in place, the Delete half is cleared and the remaining levers are not unloading
corpses during a run or IED's handling of dead actors. Does not touch the vanilla use-after-free.
A `TempleCutContent.esp` "Perversion" sits deeper in the same stack (`RSP+328`, a different frame of the job
thread's loop) and is not involved.

## What to check in game

- Performance in Whisperwood (about 3.5 enemies per cell, hordes up to 14): frame rate and Papyrus load.
- Groups stand on the ground, not in rocks, water or houses, and none sit on a quest scene (MQ05 road
  through Whisperwood, Fogville's MQ08/MQ09a).
- Fogville goblins and Arps fight side by side (Goblins makes them allies).
- Difficulty per region: the Whisperwood undead should be weak; Frostcliff glacier hounds are level 55.
- Respawn: goblins after 3 days; the rest with cell reset.
