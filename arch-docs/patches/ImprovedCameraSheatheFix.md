# ImprovedCameraSheatheFix

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/ImprovedCameraSheatheFix/`
- **Ships:** *(no plugin — `SKSE/Plugins/ZenICSheatheFix.dll` + `ZenICSheatheFix.ini`; the live copy is Patch Collection's)*
- **FormID block:** _(none)_

## What it does

**Every first-person sheathe ended with a small camera snap upwards, on all weapons.** Not an animation, setting or other mod (bisected in game 2026-10-11: OAR clips forced vanilla, IC-VanillaAnims off, head bob off, First Person Combat event off, First Person Overhaul off, Adjust Player Scale off, First Person Height Fix SKSE off — all still snapped; IC disabled — gone). Cause is hard-coded in Improved Camera SE 1.1.2.4228 `ImprovedCameraSE::TranslateCamera()` (ArranzCNL/ImprovedCameraSE-NG, source matches the shipped build): `upDisplacement = NPCEyeBone.local.z + HighHeelsOffset` (0 while sneaking) is zeroed `if (IsWeaponDrawn())`, so the camera drops by the eye-bone height while drawn and jumps back the frame the weapon state leaves Drawn/WantToSheathe/Sheathing. Head bob only changes how big it looks. Fix: SKSE plugin that on `kPostLoad` verifies 24 bytes at `ImprovedCameraSE.dll+0x78276` and NOPs the inlined `xorps xmm11,xmm11` at `+0x78282` (`0F 1F 40 00`) — the raise now always applies (the curator chose "always raised" over "never"). Other IC builds are logged and left alone; re-derive the RVA from IC's shipped `.pdb` with `dumpbin /disasm` (symbol `?TranslateCamera@ImprovedCameraSE@ImprovedCamera@@AEAAXXZ`) after any IC update. Log: `…\My Games\Skyrim Special Edition\SKSE\ZenICSheatheFix.log`. Also learned: `First Person Height Fix SKSE` duplicates IC's `bAdjustPlayerScale` (its author says not to run both) and was disabled in the same session. Built and deployed 2026-10-11, not yet verified in game.

## Status 2026-11-03: inert on Improved Camera 2.0 (superseded below)

The list moved to Improved Camera SE 2.0.0.2226 (Wabbajack CDN copy, `authored-files.wabbajack.org/ImprovedCameraSE-2.0.0.2226-RelWithDebInfo.zip_d9f12fc4-…`). The plugin's byte check fails there and it patches nothing (`ImprovedCameraSE.dll bytes at RVA 78276 do not match build 1.1.2.4228 - NOT patched`). The curator has seen no sheathe snap on 2.0 so far, so it is not being re-derived. Its DLL still ships in Patch Collection (harmless; it also logs camera state every few seconds); drop it at the next Patch Collection rebuild unless the snap returns.

## 2026-11-08: 1.2.0 — Improved Camera 2.0.0.2226 writes the third-person FOV

**Symptom (curator, 2026-11-08, right after IC went body-only):** third person "zoomed further out than the
SmoothCam preset intends"; first person zoomed in when eating (immersive eating animation) or sitting in a chair
during an Enderal cutscene. Not CINEMACAM (the curator ruled it out). Both are FOV writes, from two mods.

**Cause 1 — IC itself.** `CAMERA::Manager::UpdateFOV` (RVA `0x36700`; the build ships its `.pdb`, so
`dumpbin /DISASM:NOBYTES ImprovedCameraSE.dll` with the `.pdb` beside it is symbolized) runs every frame from
`Manager::Update`. It lerps `PlayerCamera::worldFOV` (`+0x13C`, `+0x158` on VR) toward the profile's FOV for IC's
**own** camera state (`manager+0x1B8`) with factor 1−exp(−6·dt) and writes the camera every frame. Only two states
take the hands-off path that writes the current FOV back unchanged (`0x36ACB`): Free (3) and Cinematic (0x1D);
TweenMenu (7) gets a write-through flag. ThirdPerson (9) lerps like the rest, so SmoothCam's FOV offsets (the active
`Zenderal - Settings/SKSE/Plugins/SmoothCam.json`: exploration −25, melee −25, vanity −25; the Apostate preset's
sitting −15, bow aim −15) are overwritten. A FOV table value ≤ 0 is not an off switch (the code then chases the
stale `+0x238` value). Trace (this plugin's Debug=1, 14:00 session): `cam=9 worldFOV=90..100`, the frustum
flickering between 90 and ~95 on alternate frames — IC's lerp against the FOV mod's 90 (cause 2).

IC's state enum (`CAMERA::CameraState::ToString` jump table, RVA `0x31F20`): 0 FirstPerson, 1 Vanity, 2 VATS,
3 Free, 4 IronSight, 5 Furniture, 6 Transition, 7 TweenMenu, 8 Animated, 9 ThirdPerson, 0xA Horse, 0xB Bleedout,
0xC Dragon, 0xD Animation, 0xE Crafting, 0xF Dead, 0x10 Dialogue, 0x11 DragonDismounting, 0x12 DragonMounting,
0x13 Gathering, 0x14 HorseDismounting, 0x15 HorseMounting, 0x16 MapMenu, 0x17 RaceMenu, 0x18 Spectator,
0x19 VampirelordTransition, 0x1A Vampirelord, 0x1B WerewolfTransition, 0x1C Werewolf, 0x1D Cinematic,
0x1E LichTransition, 0x1F Lich, 0x20 Sex, 0x21 SexTFC, 0x22 Unknown. `UpdateCameraState` derives it from the
vanilla camera state plus menus (a DialogueMenu without a BarterMenu is Dialogue, in first and third person alike);
`SetMode` returns 3 when IC is not in control (body disabled, MapMenu, RaceMenu).

**Fix (1.2.0).** On `kPostLoad`, if the 24 bytes at `ImprovedCameraSE.dll+0x367DC` read
`83 F8 03 0F 84 E6 02 00 00 83 F8 1D 0F 84 DD 02 00 00 F3 0F 10 83 64 02` (build 2.0.0.2226, TimeDateStamp
`0x6ADFE470`, md5 `75018b6c89d39f5343c0531283576758`), the 18-byte `cmp eax,3 / je / cmp eax,1Dh / je` pair becomes
a 14-byte absolute jump (+ 4 `int3`) into a VirtualAlloc'd stub: `cmp eax,<state> / je hands-off` for 3, 0x1D and
every state in `[ImprovedCamera2] HandsOffFOVStates` (default `9`), then `jmp 0x367EE` (normal path) or
`jmp 0x36ACB` (hands-off). Nothing else branches into the window (checked in the disassembly); neither continuation
consumes the flags; the stub's encoding was disassembled offline with capstone before deploying. The hands-off path
also resets IC's lerp value to the real FOV, so the lerp back to first person starts from SmoothCam's value, as the
vanilla 3P→1P FOV change does. The list is an ini so more states (Dialogue 0x10, Horse 0xA…) can be added without a
rebuild once the trace shows they occur while the player actually sees third person — IC's Furniture/Animation/
Crafting states are its first-person-with-body views and must keep the table, or SmoothCam's "sitting" value would
show inside them. On 1.1.2.4228 the old patches run as before; any other build is logged and left alone. `Mode=off`
disables everything. Debug=1 now also logs IC's own state / mode / target / lerp FOV
(`REX::Singleton<CAMERA::Manager>::GetSingleton` at RVA `0x2E9C0`; fields `+0x1B8`, `+0x1C0`, `+0x1A0`, `+0x23C`)
on every change.

**Cause 2 — First Person FOV and Tween Menu Fix SKSE outranks Zenderal - Settings.** `FirstPersonFOV.dll` hooks
the engine's first-person FOV (hands + world) and, with `bEnableThirdPersonFOVOverride`, the third-person FOV too;
its MenuZoomPatch blocks the kTween camera state (so IC's TweenMenu state never happens). Its own
`skse/plugins/FirstPersonFOV.ini` ships 100/100 and third person 90; Settings carries a 94/94 copy — but the mod is
at `modlist.txt` line 55 and Settings at 57 (top of the file = highest priority), so the mod's ini wins
(`FirstPersonFOV.log`: `Hands FOV: 100 … Third Person World FOV: 90`). Trace: plain first person `cam=0
worldFOV=100`; IC's Animation/Furniture states apply the profile's 94 → the "zoom in" on eating and cutscene chairs
appeared the day the profile went 100→94. Fix: Settings' `FirstPersonFOV.ini` gained `bEnableThirdPersonFOVOverride
= false` (+ `fThirdPersonWorldFOV = 94.0` and the `[Compatibility]` section) — **and the mod has to be dragged below
`Zenderal - Settings` in MO2's left pane** (MO2 was open, so modlist.txt was not edited). After both: plain first
person 94 (FOV mod), IC's states 94 (profile), third person SmoothCam alone.

**Status:** DLL built 2026-11-08 (`compiled/ZenICSheatheFix.dll`), the 24 bytes verified against the installed DLL
offline, deployed into Patch Collection with `Debug=1` for the first test. **Unverified in game.** Expected log:
`Patched ImprovedCameraSE.dll+367DC: UpdateFOV leaves the camera FOV alone in Free (3), Cinematic (29), ThirdPerson (9)`;
expected trace in third person: `cam=9 … ic=ThirdPerson(9)` with `worldFOV` at SmoothCam's value (69 in exploration
with the Apostate preset) and a steady `frustumW`. Re-derive every RVA after an Improved Camera update.

## 2026-11-08: 1.3.0 — IC 2.0 forces first person in its Animation state (Immersive Interactions, sitting) (not enough on its own, see 1.4.0)

**Symptom (curator, same day):** Immersive Interactions' MCM *Camera Mode: Force 3rd Person* had no effect, and
sitting stayed first person. **Cause:** `CAMERA::Manager::UpdateCameraState` turns IC's body action into its camera
state through a jump table (RVA `0x34404`) over IC's action enum — 0 None, 1 AI, 2 Animation, 3 Bathing, 4 BoatRide,
5 CartRide, 6 Craft, 7 Dialogue, 8 Fall, 9 Fish, 0xA Gather, 0xB Giantess, 0xC LichTransition, 0xD Parkour, 0xE Ride,
0xF Sex, 0x10 Sit, 0x11 Sleep, 0x12 Sneak, 0x13 Stagger, 0x14 Swim, 0x15 VampirelordTransition, 0x16 View,
0x17 WerewolfTransition (the profile's `Body/Action` list, alphabetical, with None in front) — and Animation,
Bathing, BoatRide, CartRide, Fish, **Sit**, **Sleep** and View all become the **Animation** camera state (0xD);
Craft → Crafting, Gather → Gathering, the transformations and Sex to their own states. For the Animation state
`CAMERA::Manager::SetMode` (RVA `0x34A30`) calls `PlayerCamera::ForceFirstPerson` whenever the camera is not first
person and IC's internal camera lock (`manager+0x18`; set only around the RaceMenu and the intro cart, console log
`<Camera Lock>`) is 0. Nothing in the profile gates it: `bEnableFakeFirstPerson` is General byte +2 (parser at RVA
`0xD2512`) and only *adds* forcing for the other third-person states; it is off in Zen.json. So Immersive
Interactions' `Game.ForceThirdPerson()` is undone within a frame, and a chair is first person even without No
Furniture Camera (which is also enabled, `modlist.txt` line 128, and keeps furniture first person on its own).

```
34B46  8B 43 38             mov eax,[rbx+38h]
34B49  83 F8 0D 0F 85 ..    cmp eax,0Dh ; jne 34BD6
34B52  83 7B 18 00 75 7E    cmp [rbx+18h],0 ; jne 34BD6
34B58  48 8B CE E8 ..       mov rcx,rsi ; call IsInFirstPerson (1216A0)
34B60  84 C0 75 08          test al,al ; jne 34B6C
34B64  48 8B CE E8 ..       mov rcx,rsi ; call ForceFirstPerson (121520)   <- 5-byte NOP
34B6C  C6 83 35 02 00 00 00 mov byte [rbx+235h],0
```

**Fix (1.3.0):** `[ImprovedCamera2] ForceFirstPersonAnimations=0` (default) verifies those 45 bytes and NOPs the
`call ForceFirstPerson` at `+0x34B67`. The branch still clears `[235h]` and returns IC's mode (CartRide ? 1 : 0),
so first-person animations are unchanged (the camera is already first person; `Update` runs the body block only for
modes 1/2) and a third-person one is left to whoever asked for it. `HandsOffFOVStates` now defaults to `9,13`: with
the force gone, a third-person animation would otherwise get IC's `fAnimation` lerped over SmoothCam's FOV; in first
person, hands-off means the FOV mod's value stays (no 100→94 zoom on eating even before the MO2 reorder). Open point
for the test: IC still believes it is in its Animation state while the camera is third person (mode 0) — body
anchoring/head hiding is expected to follow the real camera, unverified. Sitting goes third person only if No
Furniture Camera is also unticked (vanilla furniture camera); with it on, sitting stays first person by that mod's
design while Immersive Interactions' animations follow its MCM. Built and deployed into Patch Collection 2026-11-08
(Debug=1 kept). **Unverified in game.** Expected log line:
`Patched ImprovedCameraSE.dll+34B67: SetMode no longer forces first person in the Animation state (sit, sleep, scripted idles...)`.

## 2026-11-08: 1.4.0 — the 1.3.0 NOP changed nothing visible; the real switch is IC's ForceThirdPerson hook

**Test of 1.3.0 (curator, 20:05 launch):** both patches applied, yet sitting still looked first person. The
trace shows why: at 20:07:40 the vanilla camera went `cam=5` (Furniture) then `cam=9` (ThirdPerson) — the camera
*was* third person — with `ic=Animation(13) icMode=2`. Mode 2 is IC's head-camera view: it zooms the third-person
camera to −0.275 and positions it at the head, so it reads as first person. The `ForceFirstPerson` call 1.3.0
NOPed is only reached when IC's internal camera lock (`manager+0x18`) is 0, and in this flow it is 9.

**Mechanism.** `HOOK::MISC::ForceThirdPerson::func` (RVA `0xB3EB0`) is IC's hook on the engine's
`PlayerCamera::ForceThirdPerson` — the call behind Papyrus `Game.ForceThirdPerson()` (Immersive Interactions)
and the furniture camera switch. It runs the engine call, then, if `bEnableBody`, sets `manager+0x235 = 1`
("pending third-person body"); that flag is set nowhere else in the DLL. `SetMode` (`0x34A9F`) consumes it:
`[235h] = 0; [30h] = 1 (third-person body mode); zoom offsets = −0.275`, and `UpdateCameraState` (`0x33381`) locks
the state to ThirdPerson (9) while it is set, which is why SetMode's Animation branch was skipped. `SetMode` is
called from `CaptureCameraState` with `[30h]` as its argument and its result lands in `manager+0x40`, copied to
`+0x1C0` (what the trace logs as `icMode`). With `[30h]` set and the zoom at IC's −0.275 the third-person branch
returns 2. The POV key goes another way (`TogglePOV` sets `+0x261`) and stays a real third person — hence "IC only
hijacks forced third person".

**Fix (1.4.0), two single-site changes, both ini-gated and byte-verified:**

- `TakeOverForcedThirdPerson=0`: in the hook, `cmp byte [rcx],0 ; je +7` (skip the flag when the body is off)
  becomes `jmp +7` (`74 07` → `EB 07` at `+0xB3EDA`, 38 bytes from `+0xB3EC3` verified). The engine call still
  runs; IC just no longer flags it. A forced third person is then a plain third person to IC, like the POV key's.
- `ForceFirstPersonAnimations=0` now replaces `mov rcx,rsi ; call ForceFirstPerson` (8 bytes at `+0x34B64`) with
  `jmp 0x34CFB` (= `mov eax,3`, IC not in control) + a 3-byte nop: in the Animation state with the camera already
  third person IC steps aside; in first person the branch runs as before. 1.3.0's NOP had left IC in mode 0 on a
  third-person camera.

Expected after both: sit in a chair → the vanilla furniture camera (third person, SmoothCam's "sitting" offset)
unless No Furniture Camera keeps it first person; Immersive Interactions on *Force 3rd Person* → third person for
the animation, back to first person after if its *Return to 1st Person* is on; eating in first person → unchanged
(body shown). The trace now also logs `lock`, `tp` (`+0x30`) and `pend` (`+0x235`). Built and deployed into Patch
Collection 2026-11-08 (Debug=1 kept). **Unverified in game.** Expected log lines:
`Patched ImprovedCameraSE.dll+34B64: SetMode steps aside instead of forcing first person in the Animation state …`
and `Patched ImprovedCameraSE.dll+B3EDA: a forced third person (furniture, Game.ForceThirdPerson) stays a plain third person`.

## 2026-11-08: 1.4.0 tested — still the head camera; 1.4.1 instruments the path

**Test of 1.4.0 (20:19 launch, with the curator's recording):** all three patch lines logged, yet a bench still
gives IC's head camera (trace: `cam=5` then `cam=9`, `ic=Furniture(5)`→`Animation(13)`, `icMode=2`, `tp=1`,
`pend=0`, `lock=34`). Facts the trace settles: IC's internal lock (`+0x18`) idles at `0x22` ("Released"), never 0,
so SetMode's Animation branch (and 1.3.0/1.4.0's change to it) is dead code in practice. `tp` (`+0x30`) is written
only inside SetMode (whole-DLL scan, every width), and only its pending-flag block or the `bEnableFakeFirstPerson`
block can set it; the latter would force third person every frame in plain first person (lock ≠ 0), which does not
happen, and General byte +2 is only written by the profile parser (DetectMods writes a different struct at
`Plugin+0x118`). So the pending-flag block ran, i.e. `+0x235` was still raised although the only instruction that
writes it (`+0xB3EDC`) sits behind the `je` 1.4.0 turned into `jmp`. `pend=0` in the trace proves nothing: the flag
is set and consumed inside one frame, before the HUD tick that samples it. Also learned: the user's 14:08 rewrite of
Zen.json was their own save (FOV back to 100); the profile IC loads is the right file.

**1.4.1 (deployed 2026-11-08, unverified):** `IgnorePendingThirdPerson=1` (default) turns the `je` of SetMode's
`cmp byte [rbx+235h],0` (`74 3B` at `+0x34AA6`, 18 bytes from `+0x34A9F` verified) into `jmp`, so the block that
sets third-person body mode and the −0.275 zoom is skipped whoever raised the flag. With `Debug=1` the build also
installs two entry loggers (5/6-byte `jmp` to a stub allocated within 1 GB of the DLL that saves rcx/rdx/r8/r9,
calls the logger, restores, runs the displaced instructions and jumps back): one on IC's ForceThirdPerson hook
(`+0xB3EB0`, logs every call with the manager flags and the live byte at `+0xB3EDA`), one on SetMode
(`+0x34A30`, logs when `pend` is non-zero or `pend`/`tp` change). The first traced frame logs a read-back of every
patched site, the engine `ForceThirdPerson` entry (ID 50796) with the address IC's `mov rax,imm64 ; jmp rax` points
at, and the General bytes. Expected if the hook patch holds: `[IC hook]` lines with `pend=0` and `byte … = EB`;
if `pend=1` ever shows at `[SetMode in]`, something other than that hook raises it.

## 2026-11-08: 1.4.2 write watch names the real path; 1.5.0 fixes it

**1.4.1 proved the hook theory wrong.** Read-back: every patched byte in place, General = body on / fake first
person off; the engine's `ForceThirdPerson` (ID 50796) still starts with its original prologue, so IC's "replace"
hook is on something else, and the logger on IC's hook never fired while sitting. At the furniture frame SetMode was
entered with `tp` (`manager+0x30`) already 1 while `pend` was 0. Every static search for stores to `+0x30` found
only SetMode, so 1.4.2 armed a hardware write breakpoint (DR0/DR1 on `+0x30` / `+0x235`, ZenBoneTrace's mechanism)
with a vectored handler logging writer and stack.

**What the watch caught (20:48 launch, one bench):**

```
manager+30 0 -> 1  just before ImprovedCameraSE.dll+0x3824E  <- +0x34295 (UpdateCameraState, vcall [vtbl+18h]) <- +0x3258A (Manager::Update)
manager+30 1 -> 1  just before ImprovedCameraSE.dll+0x39699  <- +0x32A7F (SetCamera, vcall [vtbl+10h]) <- +0x34182 (UpdateCameraState)
manager+30 1 -> 1  just before ImprovedCameraSE.dll+0x3D0C5  <- +0x34295 ...   (every frame while seated)
```

`+0x3824E` is the `ret` after `mov byte ptr [r8+10h],1` in the folded `*State::OnUpdate(PlayerCamera*, Modifier&)`
shared by FurnitureState, DragonDismountingState and others (the symbol says DragonDismounting; identical code
folding); `+0x39699` is `FurnitureState::OnExit(Modifier&)` (`[rdx+10h] = 1` when the next action is Animation,
Sit or Sleep); `+0x3D0C5` is `AnimationState::OnUpdate` copying its own byte +8 (set in OnEnter) into `[r8+10h]`.
So: **the Manager embeds a `Modifier` at `+0x20`, byte `+0x10` of it (= `manager+0x30`) is "third-person body",
every IC camera state writes it from its OnUpdate/OnExit, CaptureCameraState hands it to SetMode as `r8b`
(`movzx ebp,r8b` at `+0x34A48`), and SetMode's third-person branch returns mode 2 once the state's OnEnter has
zoomed the ThirdPersonState to −0.275** (`FurnitureState::OnEnter` `+0x395FB`; `AnimationState::OnEnter` `+0x3CFD3`
for the cart ride and `+0x3D07C` after a `ForceThirdPerson` at `+0x3D077` when the vanilla camera was first person;
`+0x3CF71` forces third person for Bathing/CartRide/Dialogue/Fish/Swim/View). The pending flag `+0x235`, IC's hook
and the lock were a side path that never ran for a chair. The static scans missed the writes because the states
address the flag through the Modifier pointer (`[r8+10h]`, `[rdx+10h]`), not through the manager base.

**Fix (1.5.0), `ThirdPersonBody=0` (default):** five byte-verified edits — `movzx ebp,r8b` → `xor ebp,ebp ; nop`
(SetMode never honours the request: FirstPerson state keeps mode 0/1, every other state returns 3 = IC not in
control), and NOPs over FurnitureState::OnEnter's two zoom stores (14 bytes), AnimationState::OnEnter's bitmask
`ForceThirdPerson` (5), its cart-ride zoom (14) and its from-first-person `ForceThirdPerson` + zoom (19). Improved
Camera then acts only while the game's camera is really first person; a chair, a scripted third person, a mount
are the vanilla / SmoothCam camera. `HandsOffFOVStates` now defaults to every IC state but FirstPerson, for the same
reason. The earlier switches stay (harmless; `ForceFirstPersonAnimations` is dead code since the lock never reads 0,
`TakeOverForcedThirdPerson` / `IgnorePendingThirdPerson` cover a path furniture does not take). Debug=1 keeps the
entry loggers, the read-back (now also the five new sites) and the write watch. Deployed into Patch Collection
2026-11-08. **Unverified in game.** Expected: no `[watch] manager+30 0 -> 1` from the folded OnUpdate changing the
outcome — the byte may still flip, but `[SetMode in]` must show `mode40=3` on furniture and the camera must stay
`cam=5`/`cam=9` at the game's own distance. Sitting goes third person only if No Furniture Camera is also unticked.

## 2026-11-08: 1.5.0 verified for furniture; 1.5.1 splits scripted third person from furniture

**1.5.0 test (20:57 launch):** a bench is the vanilla furniture camera now — `cam=5` for the whole sit,
`ic=Furniture`→`Animation`, `icMode=3`, `tp=1` ignored. Eating, though, went to a plain third person: Eating
Animations and Sounds SE calls `Game.ForceThirdPerson()` when you eat in first person (its one-hand/two-hand
scripts carry `ForceThirdPerson` / `ForceFirstPerson` / `i1stPerson`; the MCM has no camera option, only chair and
table settings), and the trace shows IC's hook firing once per bite (`[IC hook] ForceThirdPerson #1..#3`, pending
flag suppressed by 1.4.0) followed by `cam=9 ic=ThirdPerson icMode=3`. So IC's hook *is* installed, on the Papyrus
side of `ForceThirdPerson`, not on the engine function the 1.4.1 read-back probed — that read-back was looking at
the wrong address, and the 1.4.0 patch did work for scripted calls. Furniture never goes through the hook.

**The curator wants both:** a chair → real third person; a first-person animation (eating) → first-person look with
no zoom. IC's head camera (mode 2) is the only way to watch an idle from the eyes: the first-person arms have no
eating/idle animations, the body does. Immersive Interactions' own MCM text says the same ("If you want animations
in 1st person … Immersive First Person View or Improved Camera").

**1.5.1:** `TakeOverForcedThirdPerson` defaults to 1 and `IgnorePendingThirdPerson` to 0 again, so a *scripted*
forced third person (eating, Immersive Interactions on *Force 3rd Person*, any `Game.ForceThirdPerson`) becomes
IC's head camera as IC designed it, while `ThirdPersonBody=0` keeps furniture, beds and mounts on the vanilla /
SmoothCam camera (the two paths are separate: hook + pending flag vs the states' Modifier byte; SetMode's pending
block sets `bpl` itself after the `xor ebp,ebp`, so the two switches compose). Consequence to know: IC cannot tell
Eating Animations' forced third person from Immersive Interactions', so with these defaults II's *Force 3rd Person*
also shows as the head camera; set `TakeOverForcedThirdPerson=0` + `IgnorePendingThirdPerson=1` to get a real third
person for both instead.

**The zoom in that head camera** is the First Person FOV mod's third-person override (90) applying because the
camera is technically `kThirdPerson` (trace: `fov=90` whenever `cam=9`), not anything IC does (IC's FOV table is
hands-off outside its FirstPerson state since 1.5.0). Settings' `FirstPersonFOV.ini` already turns that override off;
it only counts once *First Person FOV and Tween Menu Fix SKSE* is dragged below *Zenderal - Settings* in MO2 (still
above it at `modlist.txt` 57 vs 59; MO2 was open at every point today, so not edited here). Also seen: in the
vanilla furniture camera nothing writes the FOV, so it keeps IC's last FirstPerson-state lerp value (~91–93 instead
of 100); with the FOV mod reordered the furniture camera will be whatever that mod leaves - another reason to keep
its third-person override off. 1.5.1 deployed into Patch Collection (Debug=1 kept). **Eating with the head camera
unverified in game**; furniture verified.

## 2026-11-08: 1.5.1 tested; 1.5.2 — the request stays, the queued FOV goes

**Goal, in the curator's words:** IC must not change FOV / zoom in when any interaction is happening. Chairs third
person, eating first-person-looking, nothing moves the FOV.

**1.5.1 test (21:26 launch):** the FOV mod now loads Settings' ini (100/100, third-person override off — the MO2
reorder worked). A bench is the vanilla furniture camera (`cam=5`, `icMode=3`). Eating: IC's hook fired, the
pending block set `tp=1`, zoom −0.275, `icMode=2` — for **one frame**; the next frame `icMode=3` with `tp=1` still
set. Cause: 1.5.0's `xor ebp,ebp` at SetMode's entry discarded the persisted request on every later frame, so the
head camera could never last. The furniture camera also sat at 90.95 → 95.5 (one lerp step higher per sit) instead
of 100: UpdateFOV's hands-off path applies the FOV that TransitionCameraState queues in `manager+0x264` once per
state change (`movaps xmm6,xmm1` at `+0x36ADD`), and that queue carries IC's stale FirstPerson-state lerp.

**1.5.2:** the `xor ebp,ebp` site is dropped (SetMode honours the request again). That is enough for furniture
because the head camera also needs the −0.275 zoom, which only the four NOPed entry handlers and the pending block
write: a chair's request now hits the zoom check (`comiss -0.275,[tps+74h]`) with a vanilla zoom and returns 3,
while a scripted forced third person zooms itself in the pending block and keeps mode 2 as long as `tp` stays 1
(it is cleared when the camera returns to first person with a non-animation action, `+0x34C28`). The queued-FOV
`movaps` becomes a 3-byte nop (34 bytes from `+0x36ACB` verified), so the hands-off path writes the camera's own
FOV back and nothing else; with the FOV mod writing last in first person, a chair or the head camera inherits 100.
`ThirdPersonBody=0` now means only the four entry-handler NOPs. Deployed into Patch Collection 2026-11-08
(Debug=1 kept). **Unverified in game.** Expected: eating → `icMode=2` for the whole animation, `fov=100`
throughout; chair → `cam=5 icMode=3 fov=100`.

## 2026-11-08: 1.5.3 watches the camera FOV; 1.5.4 — Improved Camera never writes it

**1.5.2 test (21:48):** eating keeps the head camera for the whole animation now, but its FOV drops 100 → 94.53 on
the first frame; a chair drops to 93.30. Both are IC's own stale FirstPerson-state lerp (`icLerp` of the previous
first-person stint). Inside IC only UpdateFOV's two stores write `PlayerCamera::worldFOV` (the others are
SexTFCState::OnEnter and the console command), both offset terms of the hands-off path are zero here (`+0x244` is
only ever cleared, `+0x240` is the free camera's mouse-wheel step, `+0x264` is queued only by the free camera,
SexTFC and DialogueState::OnExit), so the hands-off path echoes what it reads — the writer was not visible
statically.

**1.5.3 (instrumentation only):** the write watch moved to `PlayerCamera::worldFOV` (DR0, 4 bytes) and
`manager+0x264` (DR1), ignoring writes that leave the value unchanged, IC's first-person store (`+0x368FB`) and
anything from `FirstPersonFOV.dll`. **Result (21:58 launch):** one hit at load (`memcpy` from `SkyrimSE.exe`
restoring the save's 90), then nothing during a bench (100 → 90.96) or a bite (100 → 91.82). The drop therefore
comes from one of the two writers the watch skipped, and the FOV mod only ever writes 100: **IC's first-person-state
store writes its lagging lerp into the camera every first-person frame, the FOV mod overwrites it a moment later,
and on the frame the camera leaves first person nothing follows, so the stale value sticks.** (Why the lerp lags
the 100 target by 5–9 degrees and advances one step per state cycle was not pursued; it is IC's internal business.)

**1.5.4, `CameraFOV=0` (default):** both `movss dword ptr [rdi+rbp],xmm6` stores (`+0x368FB` normal path,
`+0x36B63` hands-off; 16 bytes of context each verified) become 5-byte NOPs. Improved Camera no longer writes the
camera FOV at all: first person is the First Person FOV mod's (100 in Settings' ini), third person SmoothCam's, a
chair or the head camera keep whatever the last first-person frame left (100). IC's FOV sliders are inert with
this on; its hands-FOV modifier write (`fWorldFOVModifier`, 100 = the FOV mod's hands value) is untouched.
Deployed into Patch Collection 2026-11-08 (Debug=1 kept, the FOV watch still armed). **Unverified in game.**
Expected: `fov=100` in every `[cam]` line after the load, no `[watch] worldFOV` hit from IC.

## 2026-11-08: 1.5.4 tested; the base FOV was the save game's; 1.5.5 holds SmoothCam during the head camera

**1.5.4 test (22:02):** IC's camera-FOV stores gone (`[verify]` NOPs in place), and the FOV outside first person is
now a flat **90.00** everywhere (bench, bite) instead of IC's lerp — with no writer caught by the camera-FOV watch
except one at load: `memcpy` from `SkyrimSE.exe+0x637E95` restoring **90 from the save game** (94 from
`Enderal.ini` until then). The engine saves `PlayerCamera::worldFOV`; the save carried the FOV mod's old
third-person override (90). In first person the FOV mod writes 100 every frame; nothing wrote the non-first-person
value, so it stayed at the save's 90. **Fix:** Settings' `FirstPersonFOV.ini` turns the third-person override
back **on, at 100** — the same base in every camera state, written each frame, so the save stops mattering.
SmoothCam's preset offsets ride on top of that base (it adjusts the frustum, not `worldFOV`: the watch never saw
it), so the earlier worry that the override "fights SmoothCam" was wrong; the 90 value was the problem.

**The remaining narrowing is SmoothCam on IC's head camera.** During the bite the frustum read 75° equivalent
(`frustumW=2.0142`) against a `worldFOV` of 90: SmoothCam's `standing.fovOffset = −15` (the active preset: −15 in
every movement state, −25 in melee), applied to the ThirdPersonState that IC's head camera (mode 2) is riding.
Without IC a forced third person is a normal distant third-person view, so the same offset is just framing — the
curator's "it only happens with IC" is exactly right. IC is a SmoothCam API consumer (`Added API consumer
'ImprovedCameraSE'`) but never takes the camera for its head view, so SmoothCam keeps driving (and offsetting) it.

**1.5.5, `HoldSmoothCamInHeadCamera=1` (default):** the plugin registers for SmoothCam's interface (V2, the one
CCCStandDown proved on this list), hooks `PlayerCharacter::Update` (vfunc 0xAD, main thread) and, whenever IC's
mode (`manager+0x1C0`) is 2, calls `RequestCameraControl`; the frame the mode changes it calls
`ReleaseCameraControl`. With control held SmoothCam does nothing to the camera (API contract: "you get the camera
as-is"), so the head camera keeps the FOV mod's 100 and IC's own positioning. `AlreadyTaken` is logged once and
left alone. Deployed into Patch Collection 2026-11-08 (Debug=1 kept). **Unverified in game.** Expected: during a
bite `[cam]` shows `icMode=2`, `fov=100.00`, `frustumW=3.1284`, and the log has `Holding SmoothCam's camera …` /
`Released SmoothCam's camera …` around it; a bench stays `cam=5 fov=100`.

## 2026-11-08: 1.5.5 verified; 1.5.6 holds one frame earlier

**1.5.5 test (22:12 launch):** `SmoothCam interface obtained (V2)`; the FOV mod loads the third-person override at
100. A bench: `cam=5` the whole sit, `icMode=3`, `fov=100.00`, `frustumW=3.1284` (= 100) throughout — **the vanilla
furniture camera with no FOV change, verified.** Two bites: `Holding SmoothCam's camera …` the frame IC's pending
block fires, `icMode=2` for the whole 4.5 s animation, `fov=100.00`, `frustumW=3.1284`, `Released … (result 0)` the
frame the mode drops — **IC's first-person-look head camera at the game's FOV, verified**, with one exception: a
single frame at the start of each bite showed `frustumW=2.4054` (SmoothCam's −15 landing once), because the
`PlayerCharacter::Update` hook sees IC's mode 2 one frame after the camera update sets it.

**1.5.6:** the hold also triggers on IC's pending flag (`manager+0x235`), which IC's ForceThirdPerson hook raises
earlier in that same frame, so SmoothCam is held before its update runs. Deployed into Patch Collection 2026-11-08
(Debug=1 kept). The one-frame blip is unverified fixed; everything else above is verified.

**Where the switches stand (Patch Collection ini):** `CameraFOV=0` (IC never writes the camera FOV),
`HandsOffFOVStates` = all but FirstPerson, `ThirdPersonBody=0` (chairs / beds / mounts = vanilla camera; set 1 for
IC's head camera on furniture — with the two fixes above that is the first-person look at the game's FOV),
`TakeOverForcedThirdPerson=1` + `IgnorePendingThirdPerson=0` (scripted forced third person = IC's head camera),
`HoldSmoothCamInHeadCamera=1`, `ForceFirstPersonAnimations=0` (dead code, lock never 0). Settings'
`FirstPersonFOV.ini`: 100/100, third-person override ON at 100 (the save game carries `worldFOV`; the override
makes the save irrelevant). The FOV mod sorts directly below *Zenderal - Settings* since 21:08.

## 2026-11-08 evening: the curator chose the head camera on chairs too (1.5.7)

With eating verified as IC's head camera at the game's FOV, the curator asked for the same on chairs instead of the
vanilla third person they had picked in the morning. That is `ThirdPersonBody=1` (IC's furniture / mount takeover
left alone; the four entry-handler NOPs are not applied), now the shipped value in both the repo ini and Patch
Collection's. One addition for it: furniture raises no pending flag, so the SmoothCam hold would have started a
frame after IC's mode became 2 and SmoothCam's offset would land once per sit, as it did on bites before 1.5.6. The
actor's sit/sleep state (`ActorState::GetSitSleepState() != kNormal`, which also covers mounting) changes before the
camera does, so with `ThirdPersonBody=1` the hold also starts on it. Deployed 2026-11-08 ~22:30 (Debug=1 still on).
**Unverified:** chair → IC head camera at FOV 100 with no first-frame blip. Set `ThirdPersonBody=0` to go back to
the vanilla furniture camera (verified earlier today).

## 2026-11-08 late: chairs verified on the head camera; jitter and the eating cut are IC settings; 1.5.8

**1.5.7 test (22:21 launch):** a chair now gives IC's head camera at FOV 100 with no first-frame offset — the hold
starts on the sit state, before the camera changes (`Holding …` logged with the Furniture SetMode entry). The save
now carries 100 (`[watch] worldFOV 94 -> 100` at load). Bites still showed SmoothCam's offset for one frame
(`frustumW=2.4054` at the mode-2 frame), which pins the frame order: PlayerCharacter::Update, where the hold was
decided, runs **after** the camera update, and IC's ForceThirdPerson hook raises the pending flag on a Papyrus
thread (`[IC hook]` lines carry a non-main tid), where SmoothCam refuses requests. A seated stretch at `icMode=3`
(22:23:30–37) followed a scroll-out: IC's own "zoom out of the head camera into third person" on furniture.

**Curator's two new reports, both IC settings this morning's body-only profile had turned off:** sitting down in
first person "the head camera doesn't turn with the body and starts to jitter" → **Stabilization** (IC's tooltip:
off = the camera tracks the head exactly; the sit-down idle's head motion is copied 1:1, and the sit transition is
not smoothed); "a noticeable switch in camera when eating, like the height changes" → **Advanced.bCameraTransition**
(IC's blend between its camera states; off = a cut from the first-person camera to the head anchor). Zen.json now
has `bCameraTransition = true` and all 11 `Stabilization.*.bEnable = true` again (IC's defaults; parameters were
already IC's: head follow 0.35, max offset 6, speed 14). Backup: scratchpad `Zen.before-stabilization.json`.
Everything else in the body-only profile stays (free look, yaw smoothing, sway, free camera, dialogue/vanity off).

**1.5.8:** the SmoothCam hold is decided in a hook on `PlayerCamera::Update` (TESCamera vfunc 02) installed at
`kDataLoaded`, i.e. after SmoothCam's and IC's hooks, so it runs first in the chain and before SmoothCam's update
of the same frame; the log names the module the vtable slot pointed at before. Same decision (IC mode 2, pending
flag, or sit/sleep state with `ThirdPersonBody=1`). Deployed into Patch Collection 2026-11-08 ~22:40 (Debug=1
kept). **Unverified:** bite with no first-frame offset; chair without jitter and turning with the body; eating
blend. If the jitter persists with Stabilization on, the next knob is `fHeadFollowStrength` (lower = less head
motion) in the Furniture entry.

## 2026-11-08 night: 1.5.8 reverted — the camera vtable slot is never called; profile change reverted too

**1.5.8 test (22:33):** `SmoothCam interface obtained (V2)` and `PlayerCamera::Update hooked at data load (slot
previously SceneDirector.dll+0xAD7A0)`, yet **no `Holding …` line at all**: the game does not call the player
camera's Update through the PlayerCamera vtable slot (SceneDirector's hook there is as dead as ours was). So
SmoothCam's offset was back for the whole bite and the whole sit (`frustumW=2.4054` throughout), on top of the two
IC settings turned on an hour earlier — the curator: "you made things back to how they were when we started".

**1.5.9:** the hold decision is back in the `PlayerCharacter::Update` hook (vfunc 0xAD), verified in 1.5.5 and
1.5.7; the one-frame offset at a bite's first frame comes with it (the player update runs after the camera update;
IC's hook that would be earlier runs on a Papyrus thread, where SmoothCam refuses requests). Zen.json reverted to
`Zen.before-stabilization.json`: camera transitions off, all Stabilization off — the curator's body-only profile.
Deployed 2026-11-08 ~22:45 (Debug=1 kept). This is the state verified at 22:23: FOV 100 in every state, a chair =
IC's head camera from the first frame, a bite = IC's head camera with SmoothCam's offset on its first frame only.

**Open, and a design conflict rather than a bug:** with IC's head camera and IC's stabilization / transitions off,
a chair's camera copies the sit idle's head motion (jitter), does not follow the body's turn during the sit-down,
and a bite cuts from the first-person camera to the head anchor (height jump). IC's own remedies are exactly the
two settings the curator rejected as "IC doing more than the body". Remaining knobs, untested: a *weaker*
Stabilization on the Furniture entry alone (`fHeadFollowStrength` below 0.35, `fSmoothingSpeed` above 14) instead of
IC's default; transitions on with a much faster blend if IC exposes `fCameraSpeed` for it (string present in the
DLL, not in the profile); or `ThirdPersonBody=0` again (vanilla third person on chairs, verified clean) and the
head camera only for scripted animations.

## 2026-11-08 night: vanilla chairs chosen; 1.6.0 decides the hold late in the frame and measures the bite cut

**Decision:** the curator chose the vanilla camera on chairs (`ThirdPersonBody=0` again, both ini copies; verified
clean this afternoon) and asked to fix the two blemishes on a bite: SmoothCam's offset on the first frame, and the
hard cut from the first-person camera to IC's head camera.

**First frame:** the traces give the frame order. IC's ForceThirdPerson hook raises the pending flag on a Papyrus
thread during frame N; the `[cam]` line of frame N (written from `HUDMenu::AdvanceMovie`, late in the frame) already
shows `pend=1` and the engine's `cam=9`; IC's camera update consumes the flag in frame N+1, where SmoothCam's offset
landed once; `PlayerCharacter::Update` runs after that camera update, so the hold decided there was a frame late.
**1.6.0** decides the hold in the `HUDMenu::AdvanceMovie` tick as well (now installed whenever the hold is on, not
only with Debug=1; the trace functions stay Debug-gated), i.e. late in frame N, ahead of SmoothCam's update in N+1.
The PlayerCharacter::Update decision stays as the second point. Main thread in both, so SmoothCam accepts.

**The cut:** IC places the head camera from the head bone plus per-action offsets in the profile
(`Body/Action/<action>/fForward|fRight|fUp`, all 0 for `Animation`, the action eating is). To put the head camera
where the first-person camera was, the difference has to be measured: 1.6.0 logs, for 4 frames after every
camera-state / IC-state / mode change, the camera root relative to the player in the player's frame
(`[campos] cam=… ic=… fwd= right= up= near=`). The bite's first `[campos]` lines before and after the switch give
the forward / up delta to enter as `Body/Action/Animation` offsets in Zen.json. Deployed 2026-11-08 ~23:00
(Debug=1 kept for the measurement). **Unverified:** first-frame offset gone; cut delta still to be measured.

## 2026-11-08 late night: 1.6.0 verified; the bite's cut explained; 1.7.0 + a profile offset close it

**1.6.0 test (22:48 launch):** `Holding SmoothCam's camera` 2 ms after IC's hook on both bites, `frustumW=3.1284`
throughout - **the first-frame SmoothCam offset is gone (verified in the log).** Chair = `cam=5 … mode=3 fov=100`,
the vanilla furniture camera (verified).

**What the `[campos]` lines showed for a bite** (camera root relative to the player, in the player's frame):

| frame | engine cam | IC state | fwd | right | up |
|---|---|---|---|---|---|
| before | 0 FirstPerson | FirstPerson | 0.00 | 0.00 | 120.5-121.2 |
| N (IC's hook fires) | 9 ThirdPerson | FirstPerson | 0.00 | 0.00 | 121.07 |
| N+1 | 9 | ThirdPerson, mode 2 | **-169.92** (bite 1) / **-80.66** (bite 2) | 0 / 30 | **205** / **129** |
| N+2 on | 9 | ThirdPerson, mode 2 | 8.65 / 10.64-10.85 | 13.3 / 3.0 | 115.6 / 122.8 |
| end | 0 | ThirdPerson for one frame | 15.5 | ~2 | 123-124 |
| back in 1P | 0 | FirstPerson | 0.00 | 0.00 | 120.5 then a 123.3 → 122.2 bob |

So the "height cut" is two things: **one frame of the vanilla third-person camera from behind the player** (N+1:
IC enters its ThirdPersonState that frame but only writes its own position from the next), and a steady **~10-unit
forward jump** into the head camera (right/up vary with the pose: bite 1 came 0.13 s after a 3P→1P switch with the
body still turning, bite 2 after 2.4 s standing in 1P and is the clean sample).

**Where the head camera sits (disassembly, IC 2.0.0.2226 with its .pdb):** `CAMERA::ThirdPersonState::OnUpdate`
(RVA 39B60) copies the profile's `Camera/Firstperson/{forward, up, right}` (its `Combat` set with a weapon drawn;
`ProfileCamera` hangs off Plugin+220h, the struct is laid out forward/up/right, loader at E7CBE) into the Manager's
Modifier (+8 / +0Ch / +4), and `CAMERA::Manager::BasePosition` (35EC0, head-anchor branch - taken for every state
above IronSight) returns `SmoothHeadAnchor(head node) + scale × ((forward + 8) × bodyForward + right × bodyRight +
(up + 1) × bodyUp)`; `Manager::Update` (32490) adds that to the captured camera position and writes the camera
root (modes 1 and 2 only - in mode 0, IC's plain first person, the offsets never apply, so this knob is free for
the head camera). The vanilla first-person camera is on the root's axis ~120.5 up; IC's built-in +8 plus the head
node's own 1-3 units forward is the measured 8.7-10.9. **Zen.json `Camera/Firstperson/forward = -10` (main and
Combat)** puts the head camera where the first-person camera was (up/right left at 0: ±2-5 and 3-13 between the
two bites, pose-dependent). `Body/Action/Animation/f*` (named in the previous section) are BODY offsets - the body
relative to the camera in IC's first-person mode - not the camera's; wrong lead.

**1.7.0 `HoldCameraOnHeadCameraEntry=1`:** `PlayerCharacter::Update` (after the camera update) keeps the previous
frame's camera-root transform (`local` + `NiAVObject::Update`) on the one frame where IC's state has just gone
FirstPerson → ThirdPerson with mode 2 on the engine's ThirdPerson camera, so the view goes first-person camera →
head camera with no third-person frame between. The player-update hook is now installed when either hold is on;
`g_scManager` is cached whenever IC 2.0 is present. One info line per entry. Built + deployed to Patch Collection
2026-11-08 23:17, Debug=1 kept for one more `[campos]` reading. **Unverified in game:** the held frame, the
offset's effect (expect `fwd≈0` on the N+2 lines), and whether the residual up/right wobble still reads as a cut.
The end of a bite still cuts ~5 units back (the head leans forward during the animation; nothing constant fixes it).

## 2026-11-08 23:21: 1.7.0 + the -10 offset verified on five bites; what is left

Five bites, 1.7.0 with `Camera/Firstperson/forward = -10`, Debug=1 (`[campos]` = camera root vs player, player frame):

| bite | frame N+1 (held) | N+2 on: fwd / right / up | end of the bite (last head-camera frame) |
|---|---|---|---|
| 1 | 0.00 / 0.00 / 120.50 | 1.07-1.21 / 1.0-1.1 / 122.4 | 5.79 / 0 / 123.3 |
| 2 | 0.00 / 0.00 / 120.50 | 0.13 / 2.4 / 122.6 | 9.40 / -0.4 / 120.7 |
| 3 | 0.00 / 0.00 / 120.50 | -1.7..-1.4 / -1.4 / 121.3 | 11.45 / 0.4 / 119.4 |
| 4 | 0.00 / 0.00 / 120.50 | 1.56 / -0.95 / 121.7 | 10.65 / 0.3 / 120.3 |
| 5 | 0.00 / 0.00 / 120.50 | -0.2 / -4.4 / 117.3 | 4.06 / -0.5 / 124.6 |

First person before each bite: 0 / 0 / 120.5-120.9. **Verified:** `Head camera entered` once per bite, and that
frame's camera is the first-person transform (it was -170 / 0 / 205 and -81 / 30 / 129 in the 22:48 log) - the
third-person flash is gone. The head camera then starts within 1.7 units forward/back of the first-person camera
(was 8.7-10.9), 1-4 units sideways and 1-3 units higher (bite 5: 3 lower) - the pose, not a constant.

**Still there:**
- **The end of a bite** cuts 4-11.5 units back: the head camera is 4-11 units ahead of the root on the animation's
  last frame (the head leans forward during the eat), then the engine's first-person camera is back on the axis
  (120.5, then the 1P camera's own 123.3 -> 122.2 bob). No constant offset fixes it; only an exit blend would
  (IC's own `bCameraTransition` is the rejected whole-camera version; a plugin-side blend of the last head-camera
  position into the first-person one over ~150 ms is possible, not built; **the curator chose to leave it**, 2026-11-08).
- **Bite 2 dropped out for 0.6 s mid-animation:** 42.032-42.649 IC's mode went 2 -> 3 with its state still
  ThirdPerson and the body request still up (`tp=1`), i.e. the plain third-person camera (near 15, SmoothCam's
  offset back: `frustumW=2.4054`; the hold released and re-took correctly), then mode 2 again with no second hook
  call. SetMode's zoom check (vanilla third-person zoom must stay <= -0.275) is the only path to mode 3 with `tp=1`;
  a mouse-wheel tick during the bite would do exactly that (IC hooks the wheel in these states). Not reproduced in
  the other four; cause open.
- IC's `UpdateNearDistance` lerps the near plane 7.7-15 in these states (10.5 in plain first person); with the camera
  now 2 units behind the head anchor nothing of the head showed in five bites, but a near plane below ~8 could.

Debug=0 in Patch Collection's ini since 23:25 (repo copy identical). Nothing committed.

## 2026-11-09: 1.8.0 - the food was sliced by the near plane in the head camera

**Report (recording 2026-11-08 23:59, Ark, eating bread in first person):** as the hand brings the bread to the
mouth it turns into a thin crescent - the camera's near plane cutting through it, the flat cut face visible - and the
hand is cut the same way; the bread is whole only while it is still further away. Camera position was right (1.7.0
+ the -10 offset): this is clipping, not placement.

**Cause (disassembly):** `CAMERA::Manager::UpdateNearDistance` (RVA 36BD0) sets the near plane every frame. In a
third-person state not zoomed onto the head it writes `fNearDistanceDefault` (15). In IC's first-person state **and
in a third-person state zoomed to <= -0.27 - the head camera -** it runs the profile's pitch rule instead:
`fNearDistanceMax` (15) while the camera looks less than `fNearDistanceStartAngle` (15 deg) down, lerping to
`fNearDistanceMin` (4) at `fNearDistanceEndAngle` (50 deg down) (Combat set with a weapon drawn; a fixed 2.0 for
the Sex camera); the value is smoothed (lerp 0.15 per frame) and written to the NiCamera's `fNear` and the game's
`fNearDistance` whenever it is more than 0.05 off. The 1.7.0 log shows exactly that in the bites: `near=10.1-10.5`
looking a little down, 15 when level. The mouth is ~10 units ahead of the camera, so the food is inside the near
plane for most of the animation. (In plain first person the same rule is what keeps the body from clipping when you
look down - the 1P view is designed around 15.)

**Fix, 1.8.0 `HeadCameraNearDistance=4`** (both ini copies): in `PlayerCharacter::Update`, after IC's write, while
IC's mode is 2 the NiCamera's `fNear` and the `fNearDistance:Display` setting are capped at the value (4 = IC's own
minimum, which it already uses when you look 50 deg down, so no new depth-precision regime); logged once. IC
rewrites its own value the frame the head camera ends (it writes whenever the plane is > 0.05 off its smoothed
value), so plain first person and third person are untouched. 0 = leave IC's rule. Rejected alternative: lowering
`Advanced/fNearDistanceMax` in Zen.json, which would change plain first person too. Built 2026-11-09 ~00:10 (`compiled/` updated); the Patch Collection copy landed once the
game was closed (its DLL had been locked), so the next launch runs 1.8.0. **Verified in game 2026-11-09 00:10** (four bites: the log's `near plane 10.53 -> 4.0`
line, the curator: "food looks fine").
