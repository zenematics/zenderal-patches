# CrossbowDrawFix

- **Source:** `src/CrossbowDrawFix/`
- **Ships:** *(no plugin — `SKSE/Plugins/ZenCrossbowDrawFix.dll` + `ZenCrossbowDrawFix.ini`)*
- **FormID block:** _(none)_

## What it does

**After some crossbow draws (Ordo muskets and plain crossbows alike) the player could neither sprint
nor sheathe until they fired once.** [reported 2026-10-14] Melee and bows were unaffected, and graph
events (`player.sae attackStop` / `bowEnd` / `reloadStop`) did nothing.

**Cause, measured in game 2026-10-14.** A temporary trace in `ZenICSheatheFix` logged the player's
`ATTACK_STATE_ENUM` every frame. Every crossbow draw sets it to **`kBowAttached` (9)** ~50 ms after
`weaponState` reaches drawn and normally clears it ~0.9 s later. The two stuck draws stayed at 9 until
the shot (then 8 → 10 → 11 → 12 → 9 → 13 → 0). The engine refuses sprint and sheathe while the attack
state is not `kNone`. In both `weapequip.hkx` (1st and 3rd person, Pandora output) the clip generator
`CrossBow_Equip` carries the behaviour triggers `arrowAttach@0.571` (sets 9) and `WeapEquip_Out` /
`WeapEquip_OutMoving` at the clip's end (1.47 s, the ~0.9 s later reset). A draw cut short gets the
first and never the second. Both stuck draws started 0.2–0.3 s after a sprint ended, the good ones
≥0.5 s after. The likely cutter is Sprint Draw And Sheath Fixes, whose script answers the draw's
`EnableBumper` with `SprintStop` + `SprintStart` while `IsSprinting()` [unverified which mod cuts it].

**Not the cause** (each checked): DAR Rifles Standalone (its clips need its keywords; plain crossbows
lock too, and the musket's third-person draw plays vanilla `CrossBow_Equip`), `Zenderal - Musket Aim
Fix`, Classic Sprinting Redone, SSMT_Fix, EGO movement types, SCAR (its `1hmReadyDummy` loop wraps
`1HM_Ready_State` for every drawn weapon), our Block Release Fix and IC Sheathe Fix.

**Fix:** an SKSE plugin hooking `PlayerCharacter::Update` (vfunc `0xAD`). While the right hand holds a
crossbow, the weapon state is drawn, the graph is not `IsEquipping`, and the attack state has been
`kBowAttached` continuously for `HoldMs` (2500; normal draw ~0.9 s, post-shot reload ~1.6 s), it sets
`actorState1.meleeAttackState = kNone` — the reset `WeapEquip_Out` would have done. Each reset is logged
to `…\My Games\Skyrim Special Edition\SKSE\ZenCrossbowDrawFix.log`.

**History.** 1.0.0 reset after 2500 ms for both cases: the log showed both stuck draws cleared, but a
2.5 s lock still read as "did nothing" in game. 1.1.0 split it (`DrawHoldMs` 1000 for a draw, `HoldMs`
2500 for a post-shot reload): "releases after a second or two" [user, 2026-10-14]. **1.2.0** also resets a
draw's `kBowAttached` at once while Sprint is held or on a Ready Weapon press (input sink on
`BSInputDeviceManager`), and on Ready Weapon then calls `DrawWeaponMagicHands(false)` because that press
is already spent. The timer remains as the fallback.

**Limits.** Without a Sprint/Ready Weapon input, up to `DrawHoldMs` of lock remains after a cut draw. The graph is not told anything; if a later
crossbow attack misbehaves after a reset, look here first.

1.2.0 built and deployed (MO2 mod `Zenderal - Crossbow Draw Fix`) 2026-10-14, **verified in game 2026-10-14** ("works great now").
