# MusketHandling

- **Source:** `src/MusketHandling/`
- **Ships:** *(no plugin — `SKSE/Plugins/ZenMusketHandling.dll` + `ZenMusketHandling.ini`)*
- **FormID block:** _(none)_

## Goal

Curator's direction (2026-10-19): **bows agile, muskets powerful but slower to use.** Two changes,
both for muskets only. A "musket" is a right-hand weapon that is a crossbow (`AnimationType: Crossbow`)
and whose record comes from a plugin in `[Muskets] Plugins` (default `OrdoLegionisMuskets.esp`, whose
14 WEAPs are all guns; both Ordo mods ship that filename). Bows, Enderal SE - Crossbows' crossbows and
the flintlock pistols (staves) are not affected.

## 1. No dodge straight after a shot

**Report:** dodging right after a musket shot skipped the reload.

**Why TK Dodge allowed it.** The active dodge DLL in Alpha 0.6 is **TK Dodge NG** (it outranks TK Dodge
RE's same-named `TK_Dodge_RE.dll`; its ini sets `EnableDodgeAttackCancel = false`). Its `canDodge`
(`itahol/TK-Dodge-NG`, `src/TKRE.cpp`) refuses only while `GetAttackState() != kNone` [upstream]. A
musket shot runs kBowReleasing → kBowReleased → kBowAttached (~1.6 s) → kBowNextAttack → kNone
(measured for [`CrossbowDrawFix`](CrossbowDrawFix.md)), but DAR Rifles' musket fire clip
`432102/dlc01/crossbow_release.hkx` is **2.4 s** long — `arrowRelease@0.133`, `arrowAttach@0.667`,
reload sound `@1.6` [verified, read with PyNifly]. So the engine is back at kNone while the reload is
still on screen, TK accepts the dodge, and the dodge clip replaces the rest of the reload.
Dynamic Dodge Shot is not involved: its `BowDodge 000802` needs `GetEquippedItemType == 7` (bow);
crossbows are 12 [verified from records].

**Fix.** TK starts a dodge with `player->NotifyAnimationGraph("TKDodge<Forward|Back|Left|Right>")` and
charges stamina only on the resulting `TKDR_DodgeStart` event [upstream]. The plugin hooks the player's
`IAnimationGraphManagerHolder::NotifyAnimationGraph` (`VTABLE_PlayerCharacter[3]`, vfunc `0x01`) and
drops any event starting with a `[Dodge] BlockedEvents` prefix (`TKDodge`) for `LockAfterShotMs`
(2300) after the attack state enters kBowReleasing/kBowReleased with a drawn musket. The lock ends
early if the musket is sheathed or swapped. A dropped dodge plays nothing and costs no stamina.

## 2. Slower movement while aiming

Bows and crossbows both move on `NPC_BowDrawn_MT 03580C` while drawn (EGO DS sets all speeds 80), so a
record edit cannot single out muskets. While a musket is raised or held aimed (attack state kBowDraw or
kBowDrawn) the plugin takes `[Aim] SpeedMultPenalty` (35) off the player's SpeedMult through the
**temporary** modifier — the one magic effects use — and gives it back the frame aiming ends (the shot,
a cancel, a sheathe). SpeedMult only takes effect when the engine recomputes movement speed, which a
carry-weight change forces, so each change is followed by a ±0.1 CarryWeight nudge.

**Saves.** A modifier is written into the save. The penalty is lifted on SKSE's `kSaveGame` message
(re-applied next frame if still aiming), and the amount still applied when SKSE writes the co-save
(`ZMSH`/`SLOW`) is undone on load. Uninstalling mid-aim is the one way to keep it: aim nothing while
saving before removing the DLL.

## Tuning

All in `ZenMusketHandling.ini`: `LockAfterShotMs`, `BlockedEvents`, `SpeedMultPenalty` (0 = off),
`Plugins`, `Log`. With `Log=1`, `My Games\Skyrim Special Edition\SKSE\ZenMusketHandling.log` records
each musket shot and each dropped dodge with its delay after the shot — use it to tune the lock.

## Status

1.0.0 built 2026-10-19 and copied to MO2 mod `Zenderal - Musket Handling` (enable it in the profile).
**Unverified in game:** that the lock covers the whole visible reload (both first and third person),
and that the SpeedMult change is felt at once while aiming.

## If it misbehaves

- Dodge still cuts the reload: check the log. No "Musket shot" line → the weapon is not matched (check
  `Plugins`). Shot logged but no "Dropped" line → the dodge came after `LockAfterShotMs`; raise it.
- Speed stays low after aiming: check `player.getav speedmult` (100 expected with no other effects).
