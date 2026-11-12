# StancesSwitchBlockFix

- **Source:** `src/StancesSwitchBlockFix/Scripts/source/stances_script.psc` (the Stances mod's own shipped source,
  changes marked `; ZSB`)
- **Ships:** *(no plugin)* recompiled `Scripts/stances_script.pex` (+ source). **Live copy in
  `Zenderal - Patch Collection`** (outranks `Stances - Dynamic Animation Sets` in MO2); manifest release
  `Zenderal - Stances Switch Block Fix` for a standalone build.
- **FormID block:** _(none)_

## What it does

Curator's report (2026-11-12): with a dagger in each hand in first person, pressing F4 (neutral stance)
"seems to lock up and stop working". After this fix a stance key no longer puts a dual-wielding player into a block.

## Cause [verified in logs 2026-11-12]

Every stance key (F1–F4, via ZenKeyTrace) casts a `stances_switch_*` ability whose script `stances_script`
swaps the perks and then, unless the player is attacking, refreshes the idle by sending
`blockStart` and `blockStop` in the same call (the author's `wait(0.1)` between them is commented out).
The `blockStop` is lost: the player stays in a block that no key holds.

The curator's session that morning shows it. The Papyrus log has 28 neutral switches between 09:12:51 and 09:15:40
(each logs `Attempted to add invalid perk`: neutral's `add` property is empty). `ZenBlockReleaseFix.log` has
`Ended stuck block (IsBlocking=true wantBlocking=false … ms after last block key-up)` in the same second as nearly
every one (09:13:05, 09:13:24, 09:13:33–35, 09:14:26, 09:14:39–40, 09:14:55, 09:15:02, 09:15:33–40). No block key was
held (up to 12 s since the last key-up). So each F4 left the player blocking until
[`BlockReleaseFix`](BlockReleaseFix.md)'s 200 ms grace ended it. That doc's "Limits" names exactly this case: a block
started from script with no key held. While blocking, a dual-wielding player cannot attack.

Ruled out first (graph and data, same day): the 1P `1hm_behavior` changes since the 2026-10-26 Pandora output are
only `zfistcombo` (its transitions are gated `iRightHandType == 0 && iLeftHandType == 0`, so they never fire with
daggers) and `zpistolreload`'s idle-blend weight binding. The 1P `BlockState` has its usual `blockStop` exits. With
no stance perk, dual daggers in first person play JellyFishFP DAGGER's `FFPD/dw attack` (and FHR First Person's
twins of it).

## Fix

`; ZSB`: skip the block flick while both hands hold a one-handed weapon (`GetEquippedItemType` 1–4 in each hand).
Dual wield has no block-idle stance to refresh, and in this list it blocks through Dual Wield Parrying's key only.
Everything else is the author's script verbatim, with no property added or removed (the script-only rule). Other
weapon setups keep the flick, and its lost `blockStop` still costs them up to ~200 ms of block per stance key.
`BlockReleaseFix` ends that. If that bothers anyone, the next step is restoring the author's `wait(0.1)`.

## Known gaps / open

- **Did not fix the curator's dual-dagger lock-up** (2026-11-12 retest: "not fixed"). The real cause was a
  first-person power attack that never ended (JellyFish's `FFPD/dw attack` + `triggersFromAnnotationsOnly`), fixed in
  [`FHRFirstPerson`](FHRFirstPerson.md). This fix still stops the stance keys from leaving the player in a block
  no key holds.

- **Unverified in game.** Test: dual daggers, first person, F4 (and F1–F3), then attack at once. Afterwards
  `ZenBlockReleaseFix.log` should have no `Ended stuck block` line at the time of each stance key.
- Why the `blockStop` is lost was not traced (the two events go out back to back, and the second likely arrives
  before the block state is entered). The fix avoids the block rather than repairing it.
- Rebuild from the new source if the Stances mod updates its script.

## Install / regenerate

Compile `src/StancesSwitchBlockFix/Scripts/source/stances_script.psc` (papyrus-compile skill), copy the `.pex` to
`Zenderal - Patch Collection/Scripts/` and the `.psc` to `Scripts/Source/`.
