# ZenMountTrace

- **Source:** `src/ZenMountTrace/` (CommonLibSSE-NG, `build.cmd`; `compiled/ZenMountTrace.dll`)
- **Ships:** nothing. **Testing tool, not part of the list.** Deployed 2026-11-12 as MO2 mod
  `Zenderal - Mount Trace (testing)`, ticked at the top of the Ultra profile, with a Wabbajack Ignore rule in
  `Zenderal.compiler_settings`. **Untick it after the test.**
- **FormID block:** _(none)_

## Why

Player report (2026-11-12): *"The mount you get at the end of the questline - Shadow of Transience - only goes in one
direction and cannot turn"*. That mount is **Father Shadow** (Enderal wiki: *Shadow of Transcience* / *Father's
Shadow*, the reward of the Rhalâta questline `FS_NQR01`–`05` if the player sides with the Father): NPC
`_00E_FS_NQR05_FatherShadow 0450F9:Skyrim.esm`, race `HorseFluteWolfMountRace 0450F7:Skyrim.esm`. **It is a wolf, not a
horse**: graph `Actors\Canine\WolfProject.hkx`, male skeleton `Enderal\actors\canine\character assets wolf\skeleton_mount.nif`
(`E - Meshes.bsa`), `SpeedMultiplier 120`, essential.

## What was ruled out (2026-11-12, by reading files, before any test)

| Suspect | Evidence | Verdict |
|---|---|---|
| A wolf behaviour replacer | The wolf graph files in game (`behaviors wolf/forwardlocomotion`, `noncombatidle`, `quadrupedbehavior.hkx`) come from *Nemesis Creatures BEHAVIOUR compatibility* and are **md5-identical** to Enderal's `Skyrim - Animations.bsa` copies; `wolfbehavior.hkx` and `wolfproject.hkx` are overridden by no mod | stock graph |
| Pandora output (incl. our patches) | `Pandora Output - Zenderal` has no `actors/canine` file | not involved |
| Race / NPC records | Only EGO overrides the race (`Regen Health 0 → 0.15`); MountData, flags, angular acceleration 0.3 / tolerance 5 and graph unchanged | stock |
| Skeleton | Canidae and XPMSE replace the plain wolf `skeleton.nif`/`skeleton.hkx`; the mount's male skeleton is Enderal's own `skeleton_mount.nif`, which nothing overrides (PG Patcher only re-ships `wolf_mount.nif`, the body) | animation skeleton changed (XPMSE `skeleton.hkx`), nif not |
| True Directional Movement 2.3.1 | Its source (ersh1/TrueDirectionalMovement `Hooks.cpp`, `DirectionalMovementHandler.cpp`): movement input is transformed only when not `IsOnMount()`, `UpdateRotation` returns on a mount, the `HorseCameraState` hooks move the camera only, `SetRotationZ`/`SetRotationSpeedZ` hooks act only on the player. Mount strings in the DLL are mounted-archery only (`TDM_HorseAimTurn_*`) | unlikely |
| Missing DLC IDLE tree (the Ravagor case, [`project_ravagor_boar_idles`]) | The wolf graph is a base-game graph whose IDLEs live in `Skyrim.esm`; wild wolves in the list turn | unlikely |

Left: SmoothCam / Improved Camera's mount camera (vanilla steers a ridden mount toward the camera's heading), the XPMSE
wolf animation skeleton, and whatever the engine does differently for a non-horse mount. Not yet known whether stock
Enderal's Father Shadow turns either.

## What it logs

To `Documents/My Games/Skyrim Special Edition/SKSE/ZenMountTrace.log` (or `OneDrive/Documents/...`), only while the
player rides anything (`PlayerCharacter::GetMount`):

- `RIDE start` mount FormID, name, race, the race's angular acceleration/tolerance, acceleration and graph path;
- `SAMPLE` at 10 Hz: heading and its change since the last sample (`dHeading`, degrees), the mount's AI
  `rotationSpeed` (`MiddleHighProcessData`), movement speed, `IsMoving`, the graph variables `Speed`, `Direction`,
  `TurnDelta`, `TurnDeltaDamped`, `SpeedSampled`, `SpeedDamped`, `TurnMin/Max`, `iTurnDelta`, `bAnimationDriven`,
  `bMotionDriven`, `bAllowRotation`, `IsMoving`, `bHeadTrackSpine`, `bIsSynced`, `IsAttackReady`, `iState`,
  `iSyncTurnState`, `iSyncIdleLocomotion` (`-` = the graph has no such variable), the player's `moveInputVec` /
  `lookInputVec` / autoMove / running, the camera state id (10 = mount) and the horse camera's `horseCurrentDirection`
  and `freeRotation`;
- `IN` / `OUT` every event into the mount's graph (with `(NOT ACCEPTED)`) and out of it, footsteps left out;
- `RIDE end`.

Hooks: `Character::Update` (vfunc 0xAD of `VTABLE_Character[0]`), the graph event sink and `NotifyAnimationGraph`
(vfunc 0x01 of `VTABLE_Character[2]` / `[3]`), as in [`ZenPistolNPCTrace`](ZenPistolNPCTrace.md). Read-only.

## In-game test for the curator

1. Load any exterior save (the trace is ticked in Ultra).
2. Console: `player.placeatme 12791F` (a horse, for comparison). Ride it ~10 s: forward, then turn left/right with
   A/D, then turn with the mouse while moving. Dismount.
3. Console: `player.placeatme 0450F9` (Father Shadow; or use the player's own if they finished the quest). Same
   moves, same order. Dismount.
4. Send `ZenMountTrace.log`. (Note in the message what you saw: did the camera turn while the wolf ran straight?)

Reading it: if the horse's `dHeading` follows A/D and mouse and the wolf's stays 0 while `move`/`look` change, compare
`rotationSpeed` and the turn variables between the two. `rotationSpeed` 0 with input = the engine never asks the wolf to
turn (camera/input side: SmoothCam, IC); `rotationSpeed` non-zero but heading frozen = the graph or character controller
refuses (graph/skeleton side: `bAnimationDriven`, missing `TurnDelta`, XPMSE skeleton).

## Results

**1.0.0, curator's ride on Father Shadow (2026-11-12 16:44, 167 samples).** The curator and other players report
that **all mounts** behave the same way (horses from player reports only, not tested here). In the log:

- The mount's heading stays **307.5° for the whole ride** (`dHeading` +0.0 in every sample). Its AI `rotationSpeed`
  is 0, `TurnDelta`/`Direction` are 0, `bAllowRotation` is 0. It still walks and runs (`Speed` up to 667,
  `moveStart`/`walkStart`/`runStart` accepted).
- **Input arrives**: `move` hits (±1, 0) (A/D) and (0, ±1); `look` reaches ±4.
- The horse camera (`cam=10`) swings freely (`freeRot.x` −124° … +209°) with `freeRotationEnabled=1` throughout. Its
  own `horseCurrentDirection` **never leaves 307.5°** either.

So the input gets to the horse camera, but the camera never turns it into a new mount direction. The fault is on the
camera/input side (`HorseCameraState`), not the wolf's graph. That also explains why every mount is affected.

**1.1.0 (2026-11-12)**, at each `RIDE start`, writes `OWNERS` blocks. For the current camera state's vtable,
`HorseCameraState`, `ThirdPersonState`, `MovementHandler`, `LookHandler` and `PlayerCharacter`/`Character` vfuncs
0xA0–0xB0, it gives the module + RVA that owns each function. Where the function starts with a jump (an inline
detour), it follows the jump to the module that owns the detour. Whatever replaced `HorseCameraState` 0x0E
(`UpdateRotation`) or 0x0F (`HandleLookInput`), or detoured them, is named there (TDM hooks both and calls the
original; SmoothCam and Improved Camera are the other candidates). Test: mount anything for 2 s and send the log.

**1.1.0 ride (2026-11-12 16:53).** The mount camera (`HorseCameraState`, the current state) is split between two
plugins:

| vfunc | Owner |
|---|---|
| 0x01 Begin, 0x02 End | `TrueDirectionalMovement.dll+376D0` / `+37A00` |
| 0x03 Update | `SmoothCam.dll+6DAB0` |
| 0x0E UpdateRotation (mount direction) | `TrueDirectionalMovement.dll+3AD20` |
| 0x0F HandleLookInput | `SmoothCam.dll+6E5C0` (TDM hooks this slot too; SmoothCam's write is the one in the vtable) |
| input vtable 0x04 ProcessButton | `SmoothCam.dll+6EB40` |

The other hooked slots are elsewhere: `MovementHandler` CanProcess is SkyParkourNG's, ProcessThumbstick Precision's
and ProcessButton DtryKeyUtil's; `LookHandler` belongs to TDM. Improved Camera hooks none of these. TDM 2.3.1
(built 2026-09-01) and SmoothCam 1.8.1 are the suspects. Next: an A/B in the MCM (TDM directional movement off, then
SmoothCam off), with the trace still on. (The curator declined that test: both mods stay. The work went into the
code instead.)

**Static reading (SkyrimSE.exe 1.7.104, on-disk vtable `HorseCameraState` at RVA `196CE48`):**

- Vanilla `HorseCameraState::UpdateRotation` (`8F7360`, ID 50771) copies the mount's heading into
  `horseCurrentDirection` (+0xEC). While the mount moves, it wraps the camera's yaw offset `freeRotation.x` (+0xD4) to
  follow the mount, clamps it, and sets +0xF0. It never turns the mount.
- Vanilla `HandleLookInput` (`8F71E0`, ID 50770) only adds look input to `freeRotation`.
- Vanilla `SetFreeRotationMode` for the horse camera (slot 0x0D, `8F6D10`) is an empty `ret`. `GetFreeRotationMode`
  (`8F76A0`, ID 50775) returns +0xDC, or a PlayerControls flag at +0x4B.
- **TDM's `UpdateRotation` hook** (`TrueDirectionalMovement.dll+3AD20`), while TDM's free camera is on, writes
  `freeRotationEnabled` (+0xDC) = 1. It then calls vanilla, puts back +0xEC/+0xD4, adds (old direction − heading)
  to +0xD4 (the camera keeps its world yaw) and sets +0xEC = heading. That is why free rotation is on throughout.

**1.2.0 ride (17:03), hardware watch on +0xD4 / +0xDC / the mount's heading, 15 s.** The mount's heading was
**never written** (no DR2 hit). Readers of +0xD4 and +0xDC are camera code only: vanilla `UpdateRotation`,
`HandleLookInput` and `GetFreeRotationMode` (via ID 50840 ← TDM+3372D ← ID 50896 ← SmoothCam+6E16F), TDM's hooks, and
SmoothCam+A7B19/A7B20/A7B49. The last reader was `PlayerCamera::Update` (ID 50784 +222, ← ID 40449 ← ID 40748 ←
player update ID 40447), and all it does is set `PlayerCamera.yaw` (+0x154) = mount heading + freeRotation.x. So the
steering code reads neither field; it must read the move input and/or `PlayerCamera.yaw`.

**1.3.0** watches `PlayerControls.data.moveInputVec.x`, `PlayerCamera.yaw` (reads and writes) and the mount's
heading (writes). It also dumps the `MovementHandlerAgentPlayerControls` and `MovementControllerNPC` vtables (the
agents that drive a controlled actor).

**1.3.0 ride (17:08).** The mount's heading was again never written. Readers of `moveInputVec`:

- vanilla ID 42162 (+5D), ID 42338 (+3D/+52D/+556; called through `KickTheDoor.dll+4222E` at ID 68655 +188) and
  ID 42426 (+B8/+E2, ← MCO+1E35F ← TDM+38234 ← ID 523956 +13E ← ID 42338 +1AB);
- TDM+3822E/39/48/443.

**ID 42162** (`7A8060`, called from ID 92401 ← ID 91877 ← actor movement update ID 37356 +2F4) is the player-controls
movement agent's output. With input above a threshold it writes desired heading = atan2(input) +
`PlayerCamera.yaw`; otherwise it writes the actor's own angle. So the desired heading is produced. TDM's only hook on
`MovementHandlerAgentPlayerControls` (vtable [1] slot 0x02, TDM+33670) sets a dampening flag and tail-calls vanilla.

TDM's source (second read): its three `AIProcess::SetRotationSpeedZ` call-site hooks (ID 37356 +0x3EF / +0x632, ID
42373 +0x49) skip only the player's own process, while `IsFreeCamera()`, which is false on the mount camera. The
offsets are right on 1.7.104: on disk, ID 37356 +0x3EF and +0x632 are `call 7234B0` on `[actor+0xF8]`
(`currentProcess`), +0xA87 is `call 6740B0` (`SetRotationZ`, a special branch that needs a byte of the actor's
+0x60 object == 7), and HWYA's +0xC3A is `call 723430`.

**1.4.0** watches writes to the mount's `rotationSpeed.z`, the player's `rotationSpeed.z` and the mount's heading,
with the value written. (Never ridden: the curator asked, rightly, why the same test kept being asked for with
nothing changed. From here every build carries a fix attempt.)

**TDM's compiled hooks (2.3.1).** The three `SetRotationSpeedZ` thunks are at `TrueDirectionalMovement.dll+32EF0`,
`+32F40` and `+32F90`. Each compares the process with `[GetActorRuntimeData(player)+0x10]` and, if they match and
TDM's handler byte +0x78 is set, returns without calling the game. `GetActorRuntimeData` (TDM+27F50) picks offset
0xE0 below runtime 1.6.629 and 0xE8 from it on, so on 1.7.104 that is `player+0xF8`, the player's real
`currentProcess`: the hooks work as written. Vanilla `SetRotationSpeedZ` (`7234B0`) is only
`middleHigh->rotationSpeed.z = value`.

**1.5.0, fix candidate + trace.** Hypothesis: vanilla steers a ridden mount from the **rider's** rotation speed, and
TDM's skip of the player's write (its free-camera flag stays on while riding) leaves it at 0. While the player is
mounted, 1.5.0 chains in front of TDM at ID 37356 +0x3EF and +0x632 (`write_call`, at kDataLoaded, after TDM) and does
the game's own write for the player's process. Everything else still goes to TDM. `SAMPLE` also logs the player's
`rotationSpeed.z` and how many writes the fix made (`fixWrites` / `fixNonzero`). If the mount turns, this is the
cause and the fix belongs in a small shipped plugin. If not, the watch block shows who writes the turn speed.

**1.5.0 ride (17:29): no change; the hypothesis is wrong.** The fix wrote the player's rotation speed 85 times, all
in the first ~1 s (mounting). After that the player's movement update stops running, so riding never goes
through the player's process. The **mount's own** `rotationSpeed.z` is written every frame by vanilla's setter, via
TDM's thunk (passed through, the mount is not the player), from ID 37356 +0x3F4, with value 0. So the mount's own
movement controller produces a turn speed of 0, although the player-controls agent (ID 42162) gives it a desired
heading. Its thresholds are fine: heading is computed for input length ≥ 0.1, the input is clamped to 1. (The log
ended at 17:29:42 without its WATCH count block.) MOVT `Horse_Default_MT` is stock (rotate in place 90/270, while
running 270).

Open: between the agent's desired heading and the controller's rotation speed. The agent's update (vtable [0]
slot 0x02, `7A3FD0`) smooths the heading (`120F7E0`) when a game byte at `20B80F8` is set. TDM's agent hook writes a
"dampen player controls" game global on every call (true unless locked on + sprinting); whether that is this byte
is not checked yet.

**Solved (static, 2026-11-12).** The arbiter (ID 92401, `1225280`, reached from ID 37356 +0x2F1 via the movement
controller at actor +0x150, vfunc 0x38 → ID 91877) clamps the output against the movement interface's current
movement-type data (`[this+0x10]` vfunc 0x78 → `1226ED0` / `1227060`). The ride ran at 666.7 = 555.56 × 1.2, i.e. on
the wolf movement types, and EGO's `Wolf_Default_MT` / `Wolf_Run_MT` have `RotateWhileMovingRun` 0. Fix:
[`WolfMountTurning`](WolfMountTurning.md). The 1.5.0 fix candidate in this trace was wrong and is dead code for that
purpose; the trace is no longer needed once the fix is confirmed.
