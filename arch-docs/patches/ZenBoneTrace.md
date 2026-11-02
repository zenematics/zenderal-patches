# ZenBoneTrace

- **Source:** `src/ZenBoneTrace/` (SKSE plugin, CommonLibSSE-NG, Address Library; `build.cmd`; `compare.py`)
- **Ships:** nothing. **Testing tool, not part of the list**: MO2 mod `Zenderal - Bone Trace (testing)`
  (`SKSE/Plugins/ZenBoneTrace.dll`); disable it when the investigation is done.
- **Log:** `Documents/My Games/Skyrim Special Edition/SKSE/ZenBoneTrace.log`

Built 2026-11-01 for [`PistolRamrodReload`](PistolRamrodReload.md): in game the right arm went out to the side while
the clip, decoded offline, keeps the hand at the muzzle (the decode matches what was solved, no behaviour mask covers
the arm, no modifier drives it). Read-only; logs what the game actually poses.

After each player spell-fire action (SKSE `ActionEvent` kSpellFire; a pistol shot is a staff release), for 3.2 s:
`EV` every graph event the player's graphs send (clip annotations, `MLh_` triggers), `ROOT` the third-person 3D root's
world transform, `BONE` world positions of the arm, hand, `Shield`, `AnimObjectR`, head, spine and pelvis, `LOCAL` the
local rotations of the right arm bones, the left forearm and `Shield`, every frame (PlayerCharacter update hook).

`python src/ZenBoneTrace/compare.py <log> <clip.hkx>` puts each frame in model space (the matrix convention picked on
Loop's untouched recoil frames), then prints every bone's distance from the clip's forward kinematics at the same
clip time (log time + 0.334 s, the shot's graph trigger) and the right arm's local rotation differences.

**Result (2026-11-01, 4 shots with Pistool 03):** the left forearm and `Shield` followed the clip to 0–2°; the right
forearm and hand matched Goetia's unarmed + staff `1hm_idle` within 0.1° and barely moved; the right upper arm fitted a
50/50 blend of that idle and the clip. That pinned the one-handed graph's `MLh_1HM_Idle_Blend` (see
[`PistolRamrodReload`](PistolRamrodReload.md)). `compare.py` read the log's spdlog prefix wrongly at first (fixed).

**1.1.0 (2026-11-02), for the reload with a pistol in each hand:** also a `VAR` line every frame with the graph
variables `CastBlend`, `CastBlendDamped` (the two-staff blend's −1 left … +1 right), `IsCastingLeft/Right/Dual`,
`iLeftHandType`, `iRightHandType` and the reload's `fZenPistolRightArmIdle` / `fZenPistolLeftArmIdle` (`?` when a graph
lacks one), and `LOCAL` for both clavicles, upper arms, forearms, hands, first forearm twists and both attach nodes
(`Weapon`, `Shield`). Wanted from it: one shot from each gun while dual wielding, standing still.

**1.2.0 (2026-11-02):** `VIS` every frame: each child on the third-person `Weapon`, `Shield`, `AnimObjectR`,
`AnimObjectL` (name, hidden flag, world scale, distance from the node) and the node's own hidden flag and scale. Built
because the guns vanished during the two-pistol reload while every clip track is unit-scale. The third-person nodes
were never hidden.

**1.3.0 (2026-11-02):** `FP` every frame: the first-person skeleton's hands, `Weapon`, `Shield` and AnimObject nodes in
its `Camera1st [Cam1]` frame (x right, y forward, z up), their hidden flags, and the meshes on `Weapon` / `Shield`.
**Result:** in first person, after a right-gun shot while dual wielding, the first-person `Weapon` and `Shield` nodes
both get `hidden=1` 0.13–0.57 s after the shot. The flag clears in the frame the graph leaves the staff release state
(`SBF_CastStopRight`, or `tailCombatLocomotion` / `SprintStop` / `MCO_nextattack*`), 2.27–2.60 s after the shot. A
left-gun dual reload is never hidden. The onset spread matches Papyrus latency; no graph event lines up with it.
Improved Camera SE (ArranzCNL/ImprovedCameraSE-NG source) only toggles `kHidden` on the whole 3D roots. It shrinks the
first-person upper arms (scale 0.001), and it never touches these nodes' flags.

**1.4.0 (2026-11-02):** `WATCH`, a hardware write watch on the first-person `Weapon` / `Shield` nodes' flags. It uses
DR0 / DR1, set on every thread from a helper thread that suspends one thread at a time, and is armed only while a shot's
window is open. A vectored handler records each write that flips `kHidden`, plus the first 3 writes per node:
- the writing code: module + RVA, and for `SkyrimSE.exe` the nearest Address Library ID below it (`REL::Offset2ID`,
  loaded at `kDataLoaded`);
- the stack, from `RtlCaptureStackBackTrace`.

The main thread logs the records. `VAR` also logs `LeftItemCharge` / `RightItemCharge`, because the Flintlock holster
(`ZP_FlintlockHolster`) drains the tucked gun's charge about when the hide starts.

**Result (1.4.0, 2026-11-02, 5 shots):** the engine sets the flag itself, 0.16 s after each right-gun two-pistol shot.
The write is `SkyrimSE.exe` ID 63835 +0x42, on an animation job thread, reached through
ID 69344 → 41371 → 40521 (via TDM's and TimedBlockDodgeCounter's hooks) → 32899 → 63358 → 63589 → 63568 → 63573.
ID 63573 loops over the graph's float-slot channels; ID 63835 hides a node exactly when its slot reads 0.
The skeletons' `hkVis:Shield` / `hkVis:Weapon` slots read 0 because our PyNifly-written clip carries no float tracks.
Fixed in [`PistolRamrodReload`](PistolRamrodReload.md) (`tools/hkx_floats.py`). The unhide wasn't logged, because the
3.2 s window closes before the release state ends.

**1.5.0 (2026-11-02):** the mod event `ZP_PistolDryReload` (`DRY`) and the player equipping or unequipping a weapon
(`EQUIP`) also open the window.

**1.6.0 (2026-11-02):** `IN` logs every event sent into the player's graphs while the window is open, and whether the
graph took it. It hooks `IAnimationGraphManagerHolder::NotifyAnimationGraph`, `VTABLE_PlayerCharacter[3]` slot 1, the
same slot other plugins chain on. That covers the engine's idle/action events and Papyrus' `Debug.SendAnimationEvent`.
The start of a spell cast (SKSE `kSpellCast`, `CAST`) also opens the window. `VAR` adds `NotCasting`, `bWantCastLeft`
and `bWantCastRight`.

**Result (1.6.0):** a real staff shot is `bWantCastLeft` → the graph's own `BeginCastLeft`, then
`IN MLh_SpellAimedStart` in the same frame. `MLh_PreChargeOut` follows at 0.5 s, `IN MLh_SpellReady_event` at 0.7 s
and `IN MLH_SpellRelease_event` on the button's release. That is how [`PistolRamrodReload`](PistolRamrodReload.md)'s
reload on fire now starts its cast.

**1.6.1:** `ROOT`'s `cam1st` reads the camera's state (`PlayerCamera::currentState->id == kFirstPerson`). Through 1.6.0
it compared `Get3D(true)` with `Get3D(false)`, which never match, so it said `false` in first person too. The 1.5 and
1.6 dry-reload runs read as "third person" were first person (ZenSpellAimTrace logged camera state 0 at every shot).
