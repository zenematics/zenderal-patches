# CrossbowSprintSwap

- **Source:** `src/CrossbowSprintSwap/tools/01-build-crossbow-sprint-swap.py`
- **Ships:** *(no plugin — seven OAR `user.json` files + Tactical's sprint clip and Zodd's standing idle, copied, MO2 mod `Zenderal - Crossbow Sprint Swap`; clip not committed)*
- **FormID block:** _(none)_

## What it does

**Curator's taste (2026-10-14):** crossbow-type weapons — Ordo's muskets and real crossbows — sprint
with **Tactical Crossbow Movement (OAR)**'s shouldered sprint. Third person only (the clip slot is
`animations/dlc01/crossbowsprintforward.hkx`).

Every crossbow sprint in the list, with its OAR priority and gate:

| Submod | Priority | Gate |
|---|---|---|
| Dynamic Sprint `CrossBow Combat / Non-Combat × Sprint / Per-Sprint` | 93931210–93931240 | drawn + `IsEquippedType 9` (+ combat / per-sprint) |
| **Tactical Crossbow Movement `Standing`** | **838295** | drawn, not sneaking, `IsEquippedType 9` |
| Vanargand Sneak Crossbows `Crossbows to sneak blend` / `Sneak Crossbows` | 68393 / 68392 | drawn, not / sneaking, type 9 |
| Vanargand Crossbows `Crossbows` | 68382 | not sneaking |

Dynamic Sprint's four outrank Tactical with the same weapon gate, so this mod ships one `user.json`
per Dynamic Sprint crossbow submod: the author's `config.json` verbatim + `"disabled": true`. An OAR
`user.json` replaces its submod's config, so Dynamic Sprint itself is untouched (the
[`DynamicDodgeNoSway`](DynamicDodgeNoSway.md) pattern). The sprint then falls to Tactical's `Standing`.

**Sprint only** (curator, 2026-10-14: "I just want the tactical sprint not the other animations"). Tactical's
three submods (`Standing` walk/run 838295, `Sneak` 838294, `Sneak Moving` 838296) get the same `user.json`
+ `"disabled": true` treatment, and the mod's own `Tactical sprint` submod (Standing's conditions and
priority) plays a copy of Standing's `crossbowsprintforward.hkx`, the only Tactical clip kept. The copy
keeps working if Tactical is later disabled in MO2. Zodd's and both Vanargand mods were already disabled
in MO2 by the curator. Built 2026-10-14, not yet verified in game; re-run the generator after a Tactical
or Dynamic Sprint update.

**Standing idle** (curator, 2026-10-14). The standing drawn idle (`crossbow_idleheld`) was Smooth Combat
non Combat Animation's legacy DAR `702901` (female, out of combat; `701901` male, `601901` always). The
`Tactical idle` submod (838290; drawn, not sneaking, crossbow) now plays **Zodd's Tactical Crossbows'**
`crossbow_idleheld`, chosen from measured candidates (first frame, forward kinematics on the XPMSE
skeleton):

| Idle | Left hand → weapon | Gun points |
|---|---|---|
| Smooth Combat `702901` (was playing) | **45** (off the gun) | steeply down |
| Smooth Combat `601901` | 10 | level, ahead |
| DAR `432102` / `432103` | 15 | down-forward, across |
| **Zodd (shipped)** | **12** | **forward, ~23° down** |
| Vanargand (tried, reverted) | 12 | low, sideways across the body |
| Tactical (`Sneak Moving` clip, tried first) | 10 | forward, down; a sneak-walk clip |

Tactical's own idle (its `Sneak Moving` submod) was tried first and didn't hold the gun the way the
curator wanted. Built 2026-10-14, not yet verified in game.

**Zodd's loose files (reverted guard).** Enabling Zodd's Tactical Crossbows (Nexus 190415, which Tactical
requires) also activates its loose vanilla-path clips (`animations/dlc01/crossbow_aim`, `_idledrawn`,
`_idleheld`, `_release`, `_reload`; Sneak: `sneakcrossbow_*`), which a `user.json` can't disable. A priority-1
`Vanilla crossbow base` submod restoring Bethesda's clips was built 2026-10-14 and reverted at the curator's
request, so with Zodd enabled those loose clips play wherever no replacer wins.

## Reverted experiments (2026-10-14)

Everything below was built, and all of it except the sprint swap was **reverted at the curator's request**
the same day. The generator now ships only the four `user.json` files above. Kept for the measurements,
so none of it is retried blindly.

**Idles (reverted).** Tactical ships no standing idle; its description leaves idles to Zodd's Tactical Crossbows,
whose `crossbow_idleheld` overwrites Vanargand's `Crossbows to sneak blend` (68393) and whose `sneakidle`
submod (68394, sneaking + standing still) adds a sneak one. Smooth Combat non Combat Animation's legacy
DAR folders replace `crossbow_idleheld` above both: `601901` (`IsEquippedRightType(9)`, always), `701901` /
`702901` (male / female, out of combat, not sneaking). A legacy DAR folder can't take a `user.json`, so
the mod adds two OAR submods of its own, between Smooth Combat (≤ 702901) and Tactical (≥ 838294):
`Zodd standing idle` (838290: Vanargand blend's conditions + Zodd's clip) and `Zodd sneak idle` (838291:
Zodd's `sneakidle` config and both its clips). Tactical's `Sneak Moving` (838296) still wins while moving.

**Sneak aiming (reverted)** ("janky", 2026-10-14). The raise → aimed hold → release chain mixed families; largest
key-bone rotation gap at each hand-off (PyNifly for spline clips, a small reader for Tactical's
`hkaInterleavedUncompressedAnimation` ones):

| Hand-off | Gap |
|---|---|
| Tactical `Sneak` aim → Zodd hold (crossbow, still) | 3° |
| Zodd hold → Tactical `Sneak` release | **69°** |
| Tactical aim → DAR `432101` hold (musket, still) | **67°** |
| DAR hold → Tactical release | **46°** |
| Tactical aim → Tactical `Sneak Moving` hold | **69°** |
| Zodd aim → Zodd hold → Zodd release | 3° / 0.3° |

Tactical's sneak aim ends on Zodd's pose while its release and moving hold use its own, and starting or
stopping while aimed swapped the two holds. `Zodd sneak aim` (838297, above all of Tactical; Tactical
`Sneak`'s conditions — drawn, sneaking, crossbow — with no movement split) plays Zodd's
`sneakcrossbow_aim` / `_idledrawn` / `_release` for every sneak shot, muskets included.

That alone was **still "janky and jarring"** (OAR log: all three Zodd clips playing). Two more causes:
(a) `1hm_behavior`'s `SneakCrossBow Aim` clip generator fires **`bowDrawn@0.200`**, which cuts the raise
and fast-blends to the hold, the same mechanism as the first-person musket snap
([`FlintlockOverhaul`](FlintlockOverhaul.md)). Zodd's raise is 0.5 s and still 40° off the hold at
0.2 s, so the generator now **retimes** it: 15 frames resampled into 0.2 s (7 frames, slerp), the last
three eased onto hold frame 0 (0.0° at the cut), annotations scaled. (b) While moving, the lowered pose
was Tactical `Sneak Moving`'s `crossbow_idleheld`, 75° from the start of Zodd's raise (Zodd's still idle:
0.4°), so `Zodd sneak idle` drops Zodd's `IsMovementDirection == 0` and sits at 838298, above
`Sneak Moving`. **Any crossbow raise replacement must land on its hold by 0.2 s.**

**Muskets: DAR's sneak aim (reverted).** Zodd's sneak aim read as "aiming at the floor" on a musket, so the curator
asked for DAR Rifles'. DAR `432101` (bolt-action, the keyword the Flintlock `_KID.ini` gives the 14
muskets) has a third-person sneak set: its hold → release is 0.0°, but its raise is 0.2 s and still
**53°** off its own hold at the end, and starts 92° from the sneak idle. `DAR musket sneak aim` (838299;
drawn + sneaking + `IsEquippedHasKeyword` DAR Rifles `0x800`) ships DAR's `sneakcrossbow_idledrawn` and
`_release` plus a generated 0.2 s raise: Zodd's sneak idle frame 0 smoothstep-eased into DAR's hold
frame 0 (0.0° at the cut). Real crossbows keep Zodd's set.

**Directional movement (reverted)** (2026-10-14: "when I strafe backward it uses a different animation").
Tactical's `Standing` ships only 7 of the 18 drawn-crossbow locomotion clips (walk forward,
forward-left/-right, left, right, backward; run forward); the rest fell to Vanargand (68393) or Smooth
Combat `602901`, so the style changed mid-strafe. A Tactical-everywhere fill (its walks retimed into the
missing runs) was built and reverted unseen. Vanargand everywhere was then built and also reverted: `Vanargand movement`
(838301, above Tactical `Standing` 838295; Vanargand `Crossbows to sneak blend`'s conditions: drawn, not
sneaking, crossbow) plays all 18 of that folder's `crossbow_walk*` / `crossbow_run*` clips. Tactical now
supplies only the sprint.

The `DAR musket standing` 432101/432102 combination built the same day was reverted at the curator's
request before testing.

**History.** v1 and v2 played Dynamic Sprint's two-handed-axe ("2hw") sprint under the crossbow name.
v1 held the musket "the wrong way round": the 2hw clip offsets the `Weapon` bone (child of
`NPC R Hand`) ~38 units the other way along the hand — (−22.0, −5.6, 4.6) vs the crossbow sprint's
(16.2, −0.3, 12.5) — for an axe gripped near the end of its haft. v2 spliced the crossbow clip's own
`Weapon` track into the 2hw clip (PyNifly `anim_skyrim`, frame counts asserted) and "made it look
worse": the 2hw hand pose itself is too different. **A one-bone splice can't adapt a clip to a weapon
it wasn't animated for.** Both dropped for Tactical's dedicated crossbow sprint.

Re-run the generator after a Dynamic Sprint update (it refuses if a submod already has a `user.json`
or stops gating on `IsEquippedType 9`). Built 2026-10-14, **not yet verified in game**; a new OAR
folder needs a CRDW cache rebuild before OAR sees it.
