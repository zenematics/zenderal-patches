# AirborneGetUpFix

- **Source:** `src/AirborneGetUpFix/` (SKSE plugin, CommonLibSSE-NG, Address Library; `build.cmd`)
- **Ships:** `SKSE/Plugins/ZenAirborneGetUpFix.dll`, deployed as the MO2 mod `Zenderal - Airborne Get-Up Fix`
- **Log:** `Documents/My Games/Skyrim Special Edition/SKSE/ZenAirborneGetUpFix.log` (this machine: under `OneDrive/Documents`)
- **Status:** built 2026-10-22. **Unverified in game.**

## The bug

An enemy thrown into the air (most often by Seismic Stomp, whose SlowTime keeps it airborne three times longer) and
hit while still flying froze mid-air, alive and rigid, and never came down or moved again. Seen on Lost One
skeletons and Wood Elementals; nothing in it is race-specific.

## Cause [verified with ZenRagdollTrace, 2026-10-22]

About 55 ms after a hit on a flying ragdoll, the engine sends **`GetUpBegin`** (knock state → `kQueued`), wherever the
body is. The behaviour graph's 0.5 s timer answers `GetUpStart`, and the body turns animation-driven (knock → `kGetUp`,
not ragdoll). With no ragdoll and no character controller nothing pulls it down, so it hangs. The get-up never
completes (no `GetUpEnd` / `AddCharacterControllerToWorld`), so the knock state stays `kGetUp` for good. The full
timeline is in [`CreatureRagdollFix.md`](CreatureRagdollFix.md#cause-found-with-zenragdolltrace-2026-10-22-2117-session-verified-from-the-runtime-log).
Behaviour-graph edits do not touch this; they were tried and reverted.

## Fix

Hooks on the `Character` vtable (non-player actors only): `Actor::Update` (vfunc 0xAD) and
`IAnimationGraphManagerHolder::NotifyAnimationGraph` (vtable [3], vfunc 1).

- Every actor in ragdoll state keeps a 1 s history of its pelvis bone's (`NPC Pelvis [Pelv]`) world z, built from
  `Update` deltas.
- A `GetUpBegin` that arrives while that history spans more than 4 units is **held**: it never reaches the graph,
  but the caller is told it was accepted, so the engine simply waits in `kQueued`.
- `Update` sends the held event once the body has settled (1 s within 4 units), or after 8 s.
- A held event is dropped if the actor dies or leaves ragdoll state by itself. Actors with no pelvis bone pass through.

Constants are in `main.cpp` (`kWindow`, `kSettleRange`, `kTimeout`).

## History

- **1.0.0 (2026-10-22):** timed the settle window and timeout by summing `Actor::Update`'s float argument. In game,
  the held `GetUpBegin` was **never released**: the Wood Elemental and Awoken Lost Archer were held, then lay on the
  ground ragdolled in knock state 5 (queued) for good. Their pelvis z was steady to 0.1 units for 10 s+, yet neither
  "settled" nor the 8 s timeout fired. So that argument is not a usable frame delta for these actors.
- **1.0.1:** wall clock (`steady_clock`) for the window and timeout. Logs `ragdoll tracked` (with the Update argument)
  so the log also shows whether `Update` runs at all.

- **1.0.1 in game (21:43):** the log showed `Update arg 0` for every actor, confirming the 1.0.0 bug. Releases now
  work: a Wood Elemental hit mid-air was held at pelvis z 1610, fell to 1397, then got `GetUpBegin` and completed its
  get-up (`GetUpEnd` + `AddCharacterControllerToWorld`). But an **Awoken Lost Archer** (human graph) still froze. It got
  **`staggerStart` 0.1 s after `Ragdoll`, and the graph accepted it**: it left the ragdoll state for the stagger state,
  turned animation-driven, and the still-ragdolled body hung at a fixed position (z 1528, pelvis ~1592) for 17 s+.
  The released `GetUpBegin` was then refused.
- **1.1.0:** while an actor is ragdolled or not in the normal knock state, events starting with `stagger`, `recoil` or
  `bleedOutStart` are refused (returned as not accepted, as the graph does for events it can't take). This also covers
  a stagger cutting a get-up short, the "stuck in `kGetUp`" case below. Logs each refusal, and warns if the graph
  refuses a released `GetUpBegin`.

- **1.1.0 in game (21:53):** both actors hit mid-air came down and finished their get-up. The Wood Elemental got up
  and fought (user-confirmed). For the Awoken Lost Archer (race `mihailancientskeletonrace` 79000800, display name "Imperial"; **draugr graph** via `DraugrSkeletonProject.hkx`, not the human one): held at pelvis z 1513, sent settled at 1395,
  `GetUpStart` 2 s later, then `GetUpEnd` + `AddCharacterControllerToWorld` 4.2 s after that, knock 0, and it moved off.
  Staggers were refused many times a second throughout its knock-6 get-up. The user saw it "land rigid, then float up
  with no real animation". Its pelvis lay still ~1.3 s, jumped 1397 → 1441 in 0.25 s, then rose to 1463 over 2.5 s
  (SlowTime still on). Open: whether a ground knockdown of the same actor (no hold) looks the same, i.e. whether the
  look comes from the get-up itself rather than this fix. **Skeletons do have get-up clips:**
  `CharacterSkeleton\Draugr_Skeleton.hkx` (rig `SkeletonS.HKX`, graph `DraugrBehavior.hkx`) lists `Animations\GetUpFaceDown`,
  `GetUpFaceUp`, `ResurrectFaceDown`, `ResurrectFaceUp` (shared with draugr). All four are in `Skyrim - Animations.bsa`
  (`meshes\actors\draugr\animations\`), and no mod overrides them (loose, OAR/DAR or BSA). The draugr get-up state also runs
  `hkbGetUpModifier` (1 s ragdoll-to-animation blend, `KeyframeLowerBody`), which SlowTime stretches to ~3 s real time.

## Not covered

A get-up that starts on the ground but is interrupted (e.g. by a stagger) before its clip ends could still leave an
actor in `kGetUp` without a controller. Not seen in the log yet; check the trace if it happens.

## Verify

Run with `Zenderal - Ragdoll Trace` on. Expect `GetUpBegin held` / `GetUpBegin sent after … (settled)` lines in this
plugin's log. In the trace log, `GetUpStart` should come only once the pelvis z has stopped changing, followed by
`GetUpEnd` and `AddCharacterControllerToWorld`.
