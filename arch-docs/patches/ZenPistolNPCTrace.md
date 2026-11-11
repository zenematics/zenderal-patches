# ZenPistolNPCTrace

- **Source:** `src/ZenPistolNPCTrace/` (CommonLibSSE-NG, `build.cmd`; `compiled/ZenPistolNPCTrace.dll`)
- **Ships:** nothing. **Testing tool, not part of the list.** Was deployed 2026-11-11 to MO2's `overwrite/SKSE/Plugins/`
  (no profile change needed) and deleted there after the fix was confirmed; copy `compiled/ZenPistolNPCTrace.dll` back
  there to use it again, and delete it after.
- **FormID block:** _(none)_

## Why

[`PistolRamrodReload`](PistolRamrodReload.md)'s enemy reload (*Enemies reload too*): `ZP_PistolReloadArmNPCEffect`
starts the reload cast on an NPC the way the player's script does (`bWantCast<side>`, `M?h_SpellAimedStart`,
`M?h_SpellRelease_Event`), and for NPCs the graph mostly refuses it (seventh test: every kick refused, with
`bWantCast` already false). Papyrus sees neither the AI's casting state nor the graph's.

## What it logs

For every non-player actor (the `Character` vtable) with a weapon carrying `Pistol_Animation_By_Loop` (`0x801`, Loop's
plugin) in either hand, to `My Games/Skyrim Special Edition/SKSE/ZenPistolNPCTrace.log`, each line starting with the
local wall-clock time (to line up with the Papyrus log's `[ZP PistolReload NPC]` lines):

- `IN` every event sent into its behaviour graph (`IAnimationGraphManagerHolder::NotifyAnimationGraph`, vfunc 0x01 of
  `VTABLE_Character[3]`), with `(NOT ACCEPTED)` when the graph refused it; `M?h_` / cast events carry a `VARS` snapshot.
- `OUT` every event the graph sends back (`VTABLE_Character[2]` vfunc 0x01), footsteps left out.
- `VARS` whenever one changes (10 Hz sample from `Actor::Update`): per hand `bWantCast`, `IsCasting`, the
  `MagicCaster` state (0 none, 1 start, 2 startCharge, 3 ready, 4 preStart, 5 charging, 6 casting, 8/9 interrupt), the
  reload request, the hand type, item charge, whether it holds the pistol; attacking, blocking, staggering, combat.
- `NODES` the magic-related active nodes of its behaviour graph (names containing mlh/mrh/magic/cast/stf/staff/spell/
  ready/release/equip; `n:` = depth inside behaviour references), as `+entered` / `-left` since the last sample. The
  references are followed through `hkbBehaviorReferenceGenerator`'s `behavior` pointer at +0x50 (Havok's layout, not in
  CommonLib), only when that pointer's vtable is `hkbBehaviorGraph`'s; read under the graph manager's update lock.

## Found (2026-11-11, the eighth enemy reload test)

Ran in game the first time (no crash). The enemy script's reload cast reached the graph **before** the graph had taken
the `bWantCastLeft` flip: `MLh_SpellAimedStart` and `MLH_SpellRelease_event` `(NOT ACCEPTED)` at 21:23:46.83–.85,
`BeginCastLeft` only at 47.014, `CastStop` at 47.098 (the casting state left again, no aimed cast in it). The one reload
that played (21:23:58.137) had `BeginCastLeft` out and `MLh_SpellAimedStart` in within the same millisecond, then
`AnimObjLoad ZEN_PistolBall`, the rod, both `SoundPlay.ZEN_PistolLoadGun*`, `ZenPistolLoadedL`. The AI's own casts send
`MLh_SpellAimedStart` from the same worker thread, the same millisecond, as their `BeginCastLeft`; NPC graph events and
updates come on six different worker threads. Fixed in [`MusketHandling`](MusketHandling.md) 1.4.0 (section 4).
