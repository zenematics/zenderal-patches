# FemaleCrossbowAimWalk

- **Source:** `src/FemaleCrossbowAimWalk/tools/01-build-female-crossbow-aim-walk.py`
- **Ships:** *(no plugin — one OAR submod with three vanilla clips, MO2 mod `Zenderal - Female Crossbow Aim Walk`; clips not committed)*
- **FormID block:** _(none)_

## Problem (2026-11-01)

A **female** character aiming a musket (any crossbow-type weapon) in third person and walking W+A swung the
gun to the left, off the crosshair. Male characters didn't. [`AimFacingLock`](AimFacingLock.md) was built for
the same report on 2026-10-21; its log showed the heading moving at most ~3°, so the turn was in the animation,
and that DLL is no longer in the list.

## Cause

Aiming walks come from `crossbow_direction_behavior`, which blends the eight `CrossBow_Walk*` clips by direction
(it has no run clips; `1hm_locomotion` plays the same clips for the held, unaimed walk). The aim is layered on
top and rides on the body.

The only female-only crossbow clips in the list are **Smooth Combat non Combat Animation**'s legacy DAR folder
`602901` (`IsFemale() AND IsEquippedRightType(9)`, no other gate): forward, forward-left and forward-right walks
and runs. Body heading (`NPC COM`, mean over the clip, + = left, measured on XPMSE's skeleton):

| Aimed walk | Vanilla (male) | Smooth Combat 602901 (female) |
|---|---|---|
| `crossbow_walkforward` | −27.7 | +0.3 |
| `crossbow_walkforwardleft` | −27.7 | **+37.2** |
| `crossbow_walkforwardright` | −27.7 | −38.5 |

Vanilla keeps one stance in every direction, so the aim stays put; Smooth Combat turns the whole body toward the
walk direction, which suits an unaimed walk, but it carries the aim with it: W+A comes out ~65° left of a male
character's stance. W alone and W+D are off too (28° left, 11° right), less visibly.

No other enabled mod replaces these clips: Tactical Crossbow Movement's `Standing` is disabled by
[`CrossbowSprintSwap`](CrossbowSprintSwap.md), and Vanargand's crossbow sets are disabled in MO2.

## Fix

One OAR submod, `Vanilla crossbow movement`, priority **602950** (above 602901), with 602901's own gate:
`IsFemale` + `IsEquippedType` 9 (right hand). It ships **every clip 602901 ships** (forward, forward-left and
forward-right walks and runs), each the clip that wins its vanilla path (today `Skyrim - Animations.bsa`). So a
female character moves with a crossbow-type weapon exactly like a male one, aimed or not; Smooth Combat's female
crossbow set is always outranked, and Smooth Combat is not edited. Real crossbows are covered too (same weapon
type).

**Why not only while aiming (v1, same day).** v1 gated on aiming (OAR `IsAttacking` OR graph variable
`bBowDrawn`, interruptible) and replaced only the three walks. W+A was fixed in game, but aiming from a forward run
still pulled the gun left for a moment, then corrected. The OAR animation log (curator's video) showed why: the
aim walk (`CrossBow_WalkForward`, clip generator `CrossBow_WalkForwardFast`) activates **before** `CrossBow_Aim`,
while neither condition is true yet, so 602901's walk was picked; a legacy DAR clip is not interruptible, so OAR
only swapped it in at the clip's **Loop**. An instant swap would not have been enough either: the run → aim blend
starts from the running stance, and

| Forward | Vanilla (male) | Smooth Combat 602901 (female) |
|---|---|---|
| `crossbow_runforward` | −25.9 | −2.6 |
| `crossbow_walkforward` (the aim walk) | −27.7 | +0.3 |

vanilla's forward run is already within 2° of the aim stance, which is why male characters never see the pull,
while Smooth Combat's starts the blend ~25° left. Any female clip that turns the body shows it, so the whole set
goes. Cost: female characters lose Smooth Combat's gun-carrying walk/run style.

Vanilla's diagonal runs do face the travel direction (forward-left +19.0, forward-right −71.0), so aiming out of a
diagonal run swings through the blend for every character; that is vanilla behaviour, not this patch.

The generator refuses to build if 602901 stops gating on `IsFemale` + crossbow, stops shipping one of the three
aim walks, or if the winning vanilla-path walks stop holding one stance (COM spread over 2°). Rerun it after a
Smooth Combat update or after installing any crossbow walk/run replacer. Its position in MO2 doesn't matter (no
file conflicts; OAR priority decides).

## Status

Built 2026-11-01 into `E:\Zenderal\mods\Zenderal - Female Crossbow Aim Walk` (enabled in MO2). v1 (aim-gated
walks): W+A verified fixed in game; the run-to-aim pull remained. v2 (no gate, walks + runs): **unverified in game.**
