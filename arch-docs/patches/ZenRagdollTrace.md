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

## 1.1.0: vanishing corpses (2026-10-30)

Curator: on a killing blow, enemies of any kind often vanish instead of falling: sometimes for good, sometimes back
a few seconds later, sometimes flung away. 1.1.0 adds a `DEATH` trace: every `TESDeathEvent` (dying and dead, with the
killer) starts a 15 s trace, sampled from the **player's** update (`PlayerCharacter` vtable [0], vfunc 0xAD), so it keeps
logging while the corpse's own update stops or its 3D is gone. 20 Hz for the first 4 s, then 4 Hz.

| Field | Tells apart |
|---|---|
| `3D=NO` / `(NEW 3D)` | 3D unloaded / rebuilt (a reload is "gone, then back") |
| `rootCulled`, `geom=hidden/total` | 3D present but hidden (a hide script or a culled slot) |
| `disabled`, `deleted`, `alpha` | the reference disabled, deleted or faded by a script |
| `pos`, `moved`, `pelvis` | flung (pelvis far from the death spot) vs reference moved |
| `distPlayer`, `cell` | left the loaded area |

Mods in play at the time (Ultra): Death Drop Overhaul 1.3.6 (gear only, clean log), Guaranteed Death Animations,
UNDERDOG Death Animations (OAR), No Spinning Death Animation, Precision + Precision Creatures, Core Impact Framework,
Dismembering Framework, Immersive Death Cycle (+ Enderal patch: corpse swaps on animals/Falmer only, by SPID race,
so not humans). Wabbajack-ignored. Results: pending.

Leads before the trace (settings read 2026-10-30, web search):
- **Dismembering Framework cuts on ~every killing blow**: `Zenderal - Settings`' `DismemberingFramework.ini` sets
  regular and power-attack chance 1.0 for every weapon type. A cut is already known here to rebuild the corpse's 3D
  (blink, then back) and, with a limb hull that overlaps the body, to fling the corpse
  ([`LostOnesDismembering.md`](LostOnesDismembering.md), spiders).
- **Precision's kill impulse is on**: our `Precision.ini` turns only `bApplyImpulseOnHit` off; `bApplyImpulseOnKill` stays
  at Precision's default 1 (`fHitImpulseKillMult` 1). UNDERDOG Death Animations' page advises turning kill impulse off
  because killmoves otherwise make the dead NPC ragdoll wildly. **Turned off 2026-10-30** (`bApplyImpulseOnKill = 0`
  added to `Zenderal - Settings/MCM/Settings/Precision.ini`; original in `E:/Zenderal-backups/Precision-killimpulse-2026-10-30`).
  Curator's symptom then: on a dismember the corpse jumps in a blink instead of falling. Unverified in game.
- FSMP: an hdtSMP64 issue (#104) reports corpses warped away at huge speed by SMP physics on the body.

## 1.2.0 (2026-11-01): player damage after Seismic Stomp

Two players reported that after Seismic Stomp, enemies take "next to no damage after the first hit". Ruled out
offline first:
- Precision has no damage scaling for ragdolled targets. Its only damage scaling is the sweep falloff, and the list's
  `uSweepAttackMode` is 0 (unlimited).
- No game setting or perk in the list keys incoming damage on knock state (only Ordinator, which is not installed,
  uses `GetKnockedState`).
- The stomp's bleed is plain Health damage.

1.2.0 adds two line types, and every player hit or player damage also starts a trace of its target:
- `HIT`: every `TESHitEvent` caused by the player, with its source, hit flags, knock/ragdoll state and Health.
- `DAMAGE`: every Health damage the player deals (`Actor::HandleHealthDamage`, Character vfunc `0x104`), with the
  amount and Health before and after.

`STATE` lines now carry Health too. The log shows whether hits after the stomp arrive, what the engine applies, and in
which knock state (and so whether Airborne Get-Up Fix's hold is involved). Results: pending.

## 1.3.0 (2026-11-01): corpses standing in the air after a cell reload

Player report (GreaseLord, 2026-10-31): Vatyrs killed, then the player entered an interior and came back out, and
the corpses stood upright in mid-air. Vatyrs (`VatyrRace 0133E4` + Large/Giant, EGO's records) use the werewolf
skeleton (XPMSE's winning `skeleton.nif`/`.hkx`) and the werewolf behaviour Pandora built on 2026-10-29, with Precision's
edits in it. Dismembering Framework has no werewolf or Vatyr entry, and no Zenderal plugin touches the race or NPCs.
*Vatyrs can hit you - Precision* only enlarges their attack capsules.

A corpse that comes back with its cell gets no `TESDeathEvent`, so 1.2.0 never traced it. 1.3.0 listens to
`TESObjectLoadedEvent`: whenever a dead actor's 3D loads or unloads it writes a `CORPSE loaded/unloaded` line with a
`DEATH` snapshot, and on load it starts the usual 15 s `DEATH` trace. `DEATH` lines now also carry `charCtrl` and the
pelvis height over the reference (`+N over ref`): a lying corpse sits near the reference, a standing one far above it.
The unload snapshot shows the pose the corpse was saved in. A kill's own `IN`/`OUT` lines show whether Airborne Get-Up
Fix was holding a `GetUpBegin` when the actor died. Results: pending. Re-enabled in Ultra 2026-11-01; disable after use.
