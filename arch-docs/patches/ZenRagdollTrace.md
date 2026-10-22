# ZenRagdollTrace

- **Source:** `src/ZenRagdollTrace/` (SKSE plugin, CommonLibSSE-NG, Address Library; `build.cmd`)
- **Ships:** nothing. **Testing tool, not part of the list.** Deployed as the MO2 mod `Zenderal - Ragdoll Trace`
  (`SKSE/Plugins/ZenRagdollTrace.dll`); disable it when the investigation is done.
- **Log:** `Documents/My Games/Skyrim Special Edition/SKSE/ZenRagdollTrace.log`
- **Status:** built 2026-10-22. Unverified in game.

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
