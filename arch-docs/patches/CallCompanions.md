# CallCompanions

- **Source:** `src/CallCompanions/` (hand-written records + two scripts)
- **Ships:** `Zenderal - Call Companions.esp` (ESL, HEDR 1.7; masters Skyrim, Update, FS) + `ZEN_CC_CallEffect.pex`, `ZEN_CC_Init.pex`
- **Requires:** powerofthree's Papyrus Extender (`GetPlayerFollowers`, `GetCommandedActors`), already in the list. Prophecy is optional.
- **FormID block:** `0x800–0x803`: `800` power `ZEN_CC_Power`, `801` effect `ZEN_CC_PowerEffect`, `802` StartGameEnabled+RunOnce quest `ZEN_CC_Init` (gives the power, existing saves included), `803` FormList `ZEN_CC_Known` (remembered companions, filled at runtime)
- **MO2 mod:** `Zenderal - Call Companions` (deployed 2026-10-29; enable it and its plugin, any load position)
- **Status:** built 2026-10-29. Scripts compile, plugin deserializes. **Verified in game 2026-10-29** (curator: "it works"). Not loaded in xEdit.

The lesser power **Call Companions** brings your companions, followers and summons to you. They appear in an
arc about 120 units behind you, facing the way you face, and a notification says how many came.

## Why not a Nexus mod (checked 2026-10-29)

Nexus has no Enderal mod that does this. The Skyrim SE candidates are all *mark-and-recall* spells:
*Get Over Here - Spells* and its *Exploit Fixes* patch (SSE 125204) teleport NPCs you marked by hand, and the
patch's "followers only" rule uses vanilla follower checks. *Summon NPCs* (SSE 99809) recalls the NPCs you
grabbed last. None of them handles conjured summons. *Talk to Summons*, which is already in the list
(`Simply Order Summons` folder, `talkToSummons.esp`), only does wait/follow/dismiss/trade and has no teleport.
A 90-line script was less risk than porting any of these.

## How Enderal's companions are found [verified from Enderal's source, 2.1.4.4]

Enderal does not use Skyrim's `DialogueFollower`/`CurrentFollowerFaction` for its story companions.
`_00E_Func_SetNPCAsCompanion.SetNPCAsCompanion` (Jespar, Calia, Yero and the rest) calls
**`SetPlayerTeammate(True)`**, shows the health bar and clears the ghost flag. Dismissing them sets the
teammate flag back to False and turns ghost on again. Hirelings go through Enderal's copy of
`DialogueFollowerScript`, which also calls `SetPlayerTeammate`. Prophecy's Legion of the Damned skeletons
(`ZP_LegionEffect`) and Andrasta's Owl (`ZP_SendRavenEffect`) are set as teammates too. So the
**teammate flag** is the one test that covers all of them. Summons are **commanded actors**.

## What the power does

`ZEN_CC_CallEffect.OnEffectStart`:

1. `PO3_SKSEFunctions.GetPlayerFollowers()` returns the teammates in the high process (loaded). Each living
   one that is still a teammate is added to `ZEN_CC_Known` and called.
2. `PO3_SKSEFunctions.GetCommandedActors(player)` returns the summons, and each one is called.
3. Each `ZEN_CC_Known` entry not already near the player is called if it is still a living teammate. Entries
   that are dead, gone or no longer teammates are removed from the list. This is how a companion left in an
   unloaded cell still comes, as long as an earlier cast saw them while they were loaded.

`Call` skips:
- the dead and the disabled;
- actors with `WaitingForPlayer > 0`, so anyone you told to wait stays put;
- actors in a scene (`GetCurrentScene()`), so quest scenes are not broken;
- mounted actors;
- actors already loaded in your cell and within 400 units;
- Prophecy's owl (base `00097F`, looked up with `GetFormFromFile`, so Prophecy is not a master). The owl is
  script-flown.

Then `MoveTo` with an offset behind the player, spread ±30° per actor, then `SetAngle` and `EvaluatePackage`.
There is no navmesh snap: per [`Prophecy.md`](Prophecy.md), PO3's `MoveToNearestNavmeshLocation` jumps to the
nearest navmesh **vertex**.

## Known limits / to check in game

- A companion who has **never** been loaded during a cast is not in `ZEN_CC_Known`, and an unloaded companion
  is not in PO3's high-process list. So the first time you call, that companion does not come.
- In a tight corridor the 120-unit offset can land behind a wall. Physics usually pushes the actor out.
- Quest-controlled companions held back by a quest package (not a scene and not `WaitingForPlayer`) will be
  moved. Their package then decides whether they walk back.

## In-game test

1. Start or load a save with Jespar following and cast the power. Check that he arrives behind you.
2. Conjure a summon, run about 50 m away, then cast. Check that the summon comes too.
3. Tell a hireling to wait, then cast. Check that the hireling stays.
4. Leave a companion in an interior, cast once while they are still loaded, go outside, then cast again. Check
   that they come.
