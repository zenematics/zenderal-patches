# CCCStandDown

- **Source:** `src/CCCStandDown/` (C++ in `src/`, build with `build.cmd`; `SmoothCamAPI.h` is
  SmoothCam's public modder header, copied as its comment asks)
- **Ships:** *(no plugin — `SKSE/Plugins/ZenCCCStandDown.dll` + `ZenCCCStandDown.ini`)*; the live copy
  is in `Zenderal - Patch Collection` (deploy rebuilds there)
- **FormID block:** _(none)_

## What it does

Cinematic Conversation Camera (CCC, `SceneDirector.dll` 1.5.0) stays out of Enderal's first-person
memory scenes. The game's own first-person dialogue camera is used while the player is:

- **shrunk to a child.** The ref scale is below `ScaleBelowPct` (90).
- **a child race.** `ChildRace=1`.
- **hidden or faded.** The alpha is below `AlphaBelowPct` (99).
- **in the prologue before character creation** (1.1.0, `BeforeChargen=1`). That is MQP01 running, or MQP02
  ("A New Life", the ship with Sirius) running below stage 17.

CCC works normally again on the next frame after none of these is true.

Before character creation it also **hides the player's body meshes in first person**
(`HideBodyBeforeChargen=1`). Improved Camera draws the body there, and until the race menu that body is
Enderal's placeholder male.

## Why

The report (2026-10-18): the cinematic camera breaks in the intro, when the player is a child talking
to Daddy. It is likely to break wherever the player is a child or has no body.

**The intro scene is MQP01 "A Summer's Day"** **[verified]**. CCC's `SceneDirector.log` filmed it as
two ordinary conversations with `Daddy [00046F93]`. Its voice files are
`VT_Father\MQP01_MQP01_D1_*`, and the log ends with "Returned the player to first person".
`_00E_MQP01_Functions.SetUpScene()` does not use a child race. It **shrinks the adult player**
(`PlayerREF.SetScale(0.85)`), then calls `Game.ForceFirstPerson()` and
`DisablePlayerControls(..., abCamSwitch = true, ...)`. `PlayIntroAndMovePlayerToShip()` restores the
scale to 1. So the scene is built for first person. A third-person crew camera shows a shrunken
adult in a child's memory.

**Bodyless scenes** come from `SetAlpha` on the player (grep of `ScriptsEnderal.zip`'s source):

| Alpha | Script |
|---|---|
| 0 | `_00E_MQP03_Functions.MovePlayerToStart` (near-death vision / class menu origin) |
| 0 | `_00E_MQ00TempelKonstruktTriggBoxB` |
| 0 | `_00E_A0_MyradFlightControlQuest` |
| 0.1 | `_00E_QuestFunctions` (line 741) |
| 0.5 | `_00E_MQ07a_Functions`, `_00E_FS_NQ03_Functions` |

The only `SetRace(NordRaceChild)` in Enderal's source is `_00E_MQ00_TrigBox00Script`. It is a
developer test box (its message box reads "Yippee, jetzt bin ich Jorle Rostlöffel!"). The child-race
check is kept as a cheap guard for any mod that does the same.

### 1.1.0: Sirius and the placeholder body (2026-11-12)

The curator's report: CCC still filmed the talk with Sirius in the intro, and the camera showed a male
body. Sirius is MQP02 `003158`, on the ship (`MQP02StartShip 046ECC`). There the player is a normal-sized,
visible adult, so none of 1.0's checks fired. Character creation is `_00E_MQP02_Functions.StartCharacterGeneration()`
(`Game.ShowRaceMenu()`, then `GoToState("Chargen")`). That state's `OnUpdate` calls `SetStage(17)` once
no menu is open. So "before character creation" = MQP01 running, or MQP02 running below 17. A Skip
the Prologue start runs neither. The Daddy scene was confirmed held off in the 2026-11-12 `SceneDirector.log`
(`SmoothCam camera already held by another plugin (owner 159); not staging this conversation`). The Sirius
lines had already rotated out of both kept logs.

**Body, first try (1.1.0, failed):** this version wrote 0 to IC's `bEnableBody`. IC's General settings
block is `*(DLLMAIN::Plugin singleton + 0x1A8)`, getter at RVA `0x2570`, byte 0. The curator found the
first-person body then **ran ahead of the camera**. With the flag off, IC stopped putting the camera at
the head, but it went on drawing the body it had already un-culled. **Do not toggle IC's body setting
live.**

**1.2.1, the end condition:** 1.2.0 counted "MQP01 running" as before character creation, but **Enderal
never stops MQP01**. The SmoothCam hold and the body hiding therefore stayed on for the whole game: the
log showed one `Holding …` and no release. Now character creation counts as done for good once MQP02
reaches stage 17, MQP02 finishes, or MQP03 `07B1E5` has started. Before that, it is MQP02 running, or
MQP01 running while MQP02 hasn't started.

**1.2.2, the real cause of both:** CommonLibSSE-NG's `TESQuest::IsRunning()` is only `!IsStopping() &&
!promoteTask`. It never checks that the quest was started (`kEnabled`), so **every never-started quest
reads as running**. That is why MQP01 "ran" all game in 1.2.0, and MQP03 "ran" from the intro in 1.2.1, so
the body showed at once. Now running = `IsEnabled() && !IsStopping()` (Papyrus's sense). The 1.2.1 note
above, that "Enderal never stops MQP01", was a wrong diagnosis caused by this. **Never use CommonLib's
`IsRunning()` alone.**

**Body, 1.2.0:** while the camera is first person and before character creation, every `BSGeometry`
under the player's third-person root gets `SetAppCulled(true)`. This is re-applied every frame, in case
IC un-culls its parts. Only the meshes this plugin culled are shown again afterwards. The skeleton still
animates, so IC's head camera doesn't move. The race menu is a third-person camera, so the body shows
there.

## How it works

**CCC already has a "stand down" path, so nothing in CCC is patched** **[upstream: github.com/fatalCMD/ccc
at `5927e40`]**. Before it stages a conversation, and again on every restage, resume and
visibility recovery, `SD::Compat::SmoothCam::Acquire()` asks SmoothCam for camera control
(`src/Compat/SmoothCam.cpp`). On `AlreadyTaken` it logs "SmoothCam camera already held by another
plugin …; not staging this conversation." and returns false. `Director::Open` then gives up
("Filming declined; the camera was not available."). The list's CCC goes through SmoothCam: the log
reads "SmoothCam interface obtained (V2)" and "SmoothCam camera control acquired" for every
conversation **[verified, SceneDirector.log 2026-10-18]**.

The DLL hooks `PlayerCharacter::Update` (vfunc `0xAD`, main thread). SmoothCam answers `BadThread` off
it, and CCC makes its own requests from there. While a condition holds, it calls
`RequestCameraControl`. When the condition ends, it calls `ReleaseCameraControl`. If CCC is already
filming when a scene hides the player, the request gets `AlreadyTaken`. It is retried every 250 ms
until CCC lets go at the end of that conversation. The interface is requested as V2 at
`kPostPostLoad`, the same version CCC uses.

Side effect: while it holds the camera, SmoothCam itself stands aside, so any third-person moment in
those scenes uses the vanilla camera. Every scene above forces first person, where SmoothCam does
nothing anyway.

**Limitation:** without SmoothCam, CCC takes the camera directly ("SmoothCam not present; taking the
camera directly"), and this plugin can do nothing. Its log says so at startup.

## Status

**1.2.2 verified in game 2026-11-12** by the curator: CCC stays out of the Sirius talk, and the first-person
body is hidden through the prologue and shows again after character creation. To re-check, `ZenCCCStandDown.log`
should show `Holding SmoothCam's camera (MQP02 stage …)`, `Player body hidden before character creation (N
meshes)` and, after the race menu, `Player body shown again`.

**Verified in game 2026-10-18:** in a new game, the MQP01 talks with Daddy stayed in the first-person
dialogue camera. The MQP03 and alpha scenes have not been checked separately.

To re-check after a CCC or SmoothCam update, look for:

- `ZenCCCStandDown.log` (My Games\Skyrim Special Edition\SKSE): `Holding SmoothCam's camera (player
  scale 0.85)` when the memory begins, and `Released …` when you wake on the ship.
- `SceneDirector.log`: `not staging this conversation` for each talk with Daddy, in place of `SmoothCam
  camera control acquired`.
