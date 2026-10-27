# ZenRagdollTrace

- **Source:** `src/ZenRagdollTrace/` (SKSE plugin, CommonLibSSE-NG, Address Library; `build.cmd`)
- **Ships:** nothing. **Testing tool, not part of the list.** Deployed as the MO2 mod `Zenderal - Ragdoll Trace`
  (`SKSE/Plugins/ZenRagdollTrace.dll`); disable it when the investigation is done.
- **Log:** `Documents/My Games/Skyrim Special Edition/SKSE/ZenRagdollTrace.log`
- **Status:** built 2026-10-22. Unverified in game.
- **2026-10-25: suspected of a hard freeze, disabled in Ultra.** The game froze four times in a row in the prologue
  temple vision (MQP03, after `_00E_MQP03_Thoughts05` "The corpses and the light... they are gone."). No crash log;
  this log and `skse64.log` both stop at 19:12:49, 0.1 s after `TRACE start 0007AF9E 'Corpse'` (a `StartsDead` corpse in
  `MQP03TempleBeacon 074AF1`) entered `Ragdoll`, in the middle of graph events logged from several threads. `Touch()`
  holds `g_lock` while calling back into the game (`Describe` → `GetName`/`GetActorBase`/`GetRace`) from inside the
  engine's `NotifyAnimationGraph`/graph-event dispatch, a likely lock-order deadlock. Not proven; if the freeze persists
  with this mod off, bisect `ZenAirborneGetUpFix`, then `Zenderal - Creature Ragdoll Fix` + Death and Ragdoll Behavior
  Fix, then the Precision fork. The tool's job (the mid-air freeze) is done: `AirborneGetUpFix` was verified in game. A fifth freeze at 19:30 was
  identical (same corpse, same last event `InterruptCast` after `RemoveCharacterControllerFromWorld`) but the tool was
  still loaded: MO2, running at the time, wrote its profile back over the `modlist.txt` edit. The DLL is now renamed
  `ZenRagdollTrace.dll.mohidden` in the mod folder, which MO2 can't undo. Airborne Get-Up Fix reviewed: for a dead actor
  its update hook only erases a map entry under its lock and returns, so it's a weaker suspect. **Cleared:** a sixth freeze
  (19:33:01) happened with the DLL hidden (`skse64.log` doesn't list it). It stays hidden as it's no longer needed. That
  session's logs end with the tutorial Mud Elemental `11A6B7` (`_03E_MudElementalTutorial 11A6B8`,
  `_00E_StoneGolemRaceBig` on the troll skeleton and graph) loading at 19:33:00.8 (BehaviorDataInjector touches
  `TrollBehavior.hkb`), then a MessageBox movie loading at 19:33:01.1 (InfinityUI), then nothing.

## Why

Lost One skeletons (and Wood Elementals) knocked into the air sometimes hang there alive and rigid. Editing their
behaviour graphs on the human pattern did not help and broke get-up (see [`CreatureRagdollFix.md`](CreatureRagdollFix.md)),
so this records what the engine and the graph actually do.

## What it logs

For every non-player actor (hooks on the `Character` vtable, so the player is skipped):

| Line | Source | Meaning |
|---|---|---|
| `IN` | `IAnimationGraphManagerHolder::NotifyAnimationGraph` (vtable [3], vfunc 1) | event sent into the behaviour graph; `(not accepted)` when the graph rejected it |
| `OUT` | `BSTEventSink<BSAnimationGraphEvent>::ProcessEvent` (vtable [2], vfunc 1) | event the graph sent back: clip triggers, state enter/exit notifies (`RemoveCharacterControllerFromWorld`, `AddCharacterControllerToWorld`, `GetUpEnd`) |
| `STATE` | `Actor::Update` (vtable [0], vfunc 0xAD), 4 Hz | knock state, `IsInRagdollState`, dead, character controller present, `bAnimationDriven`, reference z, pelvis bone world z |

An actor is traced for 20 s after any event containing `ragdoll`, `getup`, `death`, `charactercontroller` or
`reanimat`. A rigid hang shows as `pelvisZ` frozen while `STATE` lines keep coming.
