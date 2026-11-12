# FirstPersonDrawFix

- **Source:** `src/FirstPersonDrawFix/Pandora_Engine/mod/zfpd/` (`info.xml`, `patches/firstperson~weapequip.xml`)
- **Ships:** *(no plugin)* Pandora-native patch `zfpd`, MO2 mod `Zenderal - First Person Draw Fix` (manifest release
  of the same name). **Needs a Pandora run with `zfpd` ticked.**
- **FormID block:** _(none)_

## What it does

Curator's report (2026-11-12): with a dagger in each hand in first person, equipping a weapon "bricks the
animations": attacks and block stop working until a 3rd → 1st person camera switch. After this patch, a
weapon equipped while another is drawn finishes drawing in first person, so attacks work right away.

## Cause [verified in trace 2026-11-12]

[`ZenParryTrace`](ZenParryTrace.md) 1.4.1, three re-equips while drawn (`WeapOutRightReplaceForceEquip` /
`WeapOutLeftReplaceForceEquip`):

- after each one that bricked, the first-person graph sent only `WeapEquip_Out` (the draw's end). For the next
  9 s every click produced only `attackRelease`, refused; the game never sent `attackStart`.
- the one re-equip that worked sent `IuEquip`, `BeginWeaponDraw`, `weaponDraw` from the first-person graph, and the
  next click attacked.

The first-person `weapequip` graph (Pandora template, nodes `#0078`–`#0092`) plays the dagger, axe and mace draws
`Dag_Equip`, `Dag_Dual_Equip`, `Axe_Equip`, `Axe_Dual_Equip`, `Mac_Equip`, `Mac_Dual_Equip` in `MODE_LOOPING`;
`1HM_Equip`, `WeapSoloEquip` and the rest are `MODE_SINGLE_PLAY`. Re-equipping re-enters the draw state while it
plays (or its echo), and a looping clip does not restart, so the clip's early `BeginWeaponDraw` (0.0 s) and
`weaponDraw` (0.067 s in JellyFish's `FFPD/dw_eq` clip) never fire again. Without `weaponDraw` from the active graph
the game never counts the new weapon as drawn. Third person gets the events from its own graph, which is why a camera
switch frees it.

Found once before (2026-10-07, under Nemesis: "ANY OAR replacement on them echoes and never completes") and fixed as
the Nemesis patch `zfpd`, MO2 mod `Zenderal - 1st Person Dagger Draw Fix`. That mod was lost in the Nemesis →
Pandora switch and never committed, so the bug came back. This is the same change as a Pandora-native patch, now
including the axe and mace draws, which loop the same way.

## Mechanism

Six `Replace` operations on the template nodes' `mode` field → `MODE_SINGLE_PLAY`. Node IDs from the template
converted with `hkxconv --meta` (the numbering `zfistcombo`'s `#4328`/`#3425` come from):

| Node | Clip generator |
|---|---|
| `#0090` / `#0092` | `Dag_Equip` / `Dag_Dual_Equip` |
| `#0084` / `#0086` | `Axe_Equip` / `Axe_Dual_Equip` |
| `#0078` / `#0080` | `Mac_Equip` / `Mac_Dual_Equip` |

The `Replace` body form (a whole `<hkparam>` element at a field path) is inferred from Pandora's own patch
(`#0077/variableNames/Element31` replaced with an `<hkcstring>` element); Pandora's source was not reachable to confirm.
**Check after the Pandora run:** convert the output's `_1stperson/behaviors/weapequip.hkx` and confirm the six
clip generators read `MODE_SINGLE_PLAY`.

## Known gaps / open

- Pandora applies this `Replace` form: the 2026-11-12 10:37 output reads `MODE_SINGLE_PLAY` on all six. **Verified in game 2026-11-12** (curator: "seemed to be fixed"; trace: five re-equips while drawn, then every click attacked).
- The two earlier fixes this day ([`StancesSwitchBlockFix`](StancesSwitchBlockFix.md) and the `FFPD/dw attack`
  power-attack flag in [`FHRFirstPerson`](FHRFirstPerson.md)) addressed real faults seen in the logs, but not this one.

## Install / regenerate

Tick `Zenderal - First Person Draw Fix` in MO2, run Pandora with *Zenderal - First Person Draw Fix* ticked, then (as
after every Pandora run) move the creature behaviors from `overwrite` into `Pandora Output - Zenderal`.
