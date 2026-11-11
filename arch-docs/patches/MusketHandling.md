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

**1.1.0 (2026-10-21): attack-cancel is on now.** Since the 1.7.104 update the list's TK ini (shipped by
`Zenderal - Settings`, also `Input Defaults`/`Personal Keybinds`/CCS) has `enableDodgeAttackCancel =
true` [verified, `TK_Dodge_RE.log` 2026-10-21: "found enableDodgeAttackCancel with value true"], so TK
accepts a dodge in **any** attack state and fire → dodge → fire skips the reload outright, not only the
last 0.8 s of it. The setting stays on (it is how melee dodge-cancels work); instead, after
`LockAfterShotMs` the lock now also holds while the musket is still in its post-shot cycle
(kBowReleasing … kBowFollowThrough, the reload being kBowAttached), capped at `MaxLockMs` (5000) so a
stuck state cannot disable the dodge.

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

## 3. Reload on demand (1.2.0, 2026-11-03)

**Curator:** "the reload mechanic we did for pistols, where they don't immediately reload until you press the fire
button again". [`FlintlockOverhaul`](FlintlockOverhaul.md)'s ramrod reload now plays the shot alone (its *Reload on
demand* section), and the engine fires a musket whose shot did not reload it: five shots in 6.8 s, no `reloadStart`
(traced 2026-11-03, SpellAimTrace 1.4.1). So:

- **A shot empties the musket.** The same detection as the dodge lock (attack state into kBowReleasing/kBowReleased
  with a drawn musket) records that weapon's FormID as empty.
- **The next press reloads it.** While that musket is drawn and empty, the engine's attack press
  (`crossbowAttackStart` through `NotifyAnimationGraph`, `[Reload] AttackEvents`) is dropped, so it never fires, and
  `reloadStart` is sent in its place. Both 1hm graphs take that from `1HM_Ready_State` and from `CrossBow_AttackState`
  (a press during the short shot clip) into `CrossBow_ReloadState`, Zodd's reload clip with the ball, rod and loading
  sounds. That state has no `reloadStart` transition of its own, so the engine's repeats while the button is held,
  and presses during the reload, are refused and restart nothing.
- **The reload clip's `reloadStop` loads it** (its clip trigger, 0.195 s before the end), heard through the
  player's own `BSAnimationGraphEvent` sink (`VTABLE_PlayerCharacter[2]`, vfunc 0x01, as SpellAimTrace). A reload cut
  short (dodge, stagger, sheathe) leaves the musket empty, and the next press starts it again.
- The empty musket is kept in the co-save (`ZMSH`/`EMPT`, its FormID). Another musket drawn is loaded (the engine's
  draw loads it); the emptied one stays empty until its reload. NPCs are untouched.
- Quick Reload / Rapid Shot now count after a shot: the reload state plays `CrossBow_ReloadFast` (1.3x), and the
  ramrod mod's *both reload perks* copies retime exactly that clip.
- `[Reload] OnDemand=0` turns it off (then use shot clips that reload, or every shot fires again unloaded).
- **NPCs reload inside their shot.** This plugin only hooks the player, so the short shot clips are the player's
  alone (`Ramrod <mesh>, player`, 2026-11-05); musket NPCs play Zodd's whole shot with the reload in it. Before that
  they had the short shot too and fired every ~1.5 s ([`FlintlockOverhaul`](FlintlockOverhaul.md), *NPCs keep the
  whole shot*). Verified in game 2026-11-05.

The dodge lock is unchanged: `LockAfterShotMs` still holds 2.3 s after a shot, now longer than the 1.24 s shot clip.

**1.3.0 (2026-11-03, curator: "users are also exploiting unequipping muskets and pistols to avoid the reload"):**
1.2.0 kept one FormID, the musket the last shot emptied. Re-equipping that one kept it empty, but firing a second
musket replaced the record, so two muskets swapped back and forth never needed a reload. Now:
- The musket in hand (drawn or not) and whether it is empty (`g_handForm`, `g_handEmpty`); every musket put away
  empty is kept by base form with a count (`g_stowedEmpty`). `SyncHand`, once a frame in the player's update, sees
  the hand change: a swap and back inside the inventory menu changes nothing.
- Taken up again, a musket is empty if **every** one of its form the player has out of the hand is. The engine
  doesn't say which of several alike it equipped, so a loaded one is assumed while the player has any (a second
  loaded musket of the same kind is a fair spare). Counts are capped by what the player still has: one sold or
  dropped counts as a loaded one gone.
- Co-save `ZMSH`/`EMPT` version 2: the hand's musket and flag, then (FormID, count) pairs. A 1.2.0 save's single
  FormID (version 1) loads as one musket put away empty, which the first frame takes up if it is in hand.
- Only the musket's own reload (`reloadStop` with it in hand) loads it; NPCs untouched.

Built 2026-11-03 (backup of 1.2.0's source and DLL in `E:/Zenderal-backups/2026-11-03-musket-handling-1.2.0/`).
**Verified in game 2026-11-03**: the curator's musket ↔ pistols swaps; its log took the musket up `EMPTY` after every
swap and the next press played the reload. The pistols got the same in the Flintlock script ([`FlintlockOverhaul`](FlintlockOverhaul.md),
*Put away empty*).

## 4. Enemies' pistol reload casts (1.4.0, 2026-11-11)

Not about muskets: [`PistolRamrodReload`](PistolRamrodReload.md)'s enemy script (*Enemies reload too*) starts an NPC's
pistol reload the way the player's script does (the hand's request variable `fZenPistolReloadL/R` at 1, `bWantCast<side>`
false → true, `M?h_SpellAimedStart`, `M?h_SpellRelease_Event`). [`ZenPistolNPCTrace`](ZenPistolNPCTrace.md) showed
why most were refused: an NPC's graph takes the `bWantCast` edge on its own update, 0.1–0.2 s after Papyrus sent the
events, so they reached it before `BeginCastLeft` and were refused, and the graph then left its casting state
(`CastStop`). The one reload that played had `M?h_SpellAimedStart` land in the same millisecond as `BeginCastLeft`.

So this hooks the `Character` graph event sink (`VTABLE_Character[2]` vfunc 0x01: every non-player actor) and answers
`BeginCastLeft` / `BeginCastRight` of an actor whose request variable is set, at once, with `M?h_SpellAimedStart`
(+ `MRh_SpellReady_Event` for the right hand) and `M?h_SpellRelease_Event`. The engine answers its own casts the same
way, on the same thread (trace: the AI's `MLh_SpellAimedStart` in the same millisecond, same thread, as its
`BeginCastLeft`). The AI's own casts leave the request at 0 and are untouched; the player is a `PlayerCharacter` and
never comes through here. `[Pistols] NpcReloadCast` (1) turns it off; with `Log=1` each answer is logged with whether
the graph took the events. 1.3.0's DLL and ini are in `E:/Zenderal-backups/2026-11-11-musket-handling-1.3.0/`.
Built and deployed to Patch Collection 2026-11-11. Ninth test: every enemy reload asked for started, the events taken.
**1.4.1 (same day):** the request is cleared as it is answered, one answer per reload. With the request still set, a
second `BeginCast` (the graph raises one when a cast is thrown away and `bWantCast` is still on) was answered too, and
that cast, at a charge that pays for a bullet, fired a real shot mid-reload (eleventh test). Unverified in game.

## Tuning

All in `ZenMusketHandling.ini`: `LockAfterShotMs`, `MaxLockMs`, `BlockedEvents`, `SpeedMultPenalty` (0 = off),
`Plugins`, `Log`. With `Log=1`, `My Games\Skyrim Special Edition\SKSE\ZenMusketHandling.log` records
each musket shot and each dropped dodge with its delay after the shot — use it to tune the lock.

## Status

1.0.0 built 2026-10-19; **it never ran** — the mod sat unticked in Ultra (`-Zenderal - Musket Handling`)
and absent from Alpha 0.6, and no `ZenMusketHandling.log` existed on 2026-10-21. 1.1.0 built (SE + AE
address IDs; the list runs 1.7.104) and copied to the MO2 mod 2026-10-21; tick it in the profile.
**Unverified in game:** that the lock covers the whole visible reload (both first and third person),
and that the SpeedMult change is felt at once while aiming.

**The live copy is Patch Collection's** (`Zenderal - Patch Collection/SKSE/Plugins/`; the standalone MO2 mod is gone
from the list). 1.1.0 ran there on 2026-11-03 (its log caught all five test shots). **1.2.0** (reload on demand) built
and copied over it 2026-11-03; 1.1.0's DLL and ini are in `E:/Zenderal-backups/2026-11-03-musket-handling-1.1.0/`.
**Reload on demand verified in game 2026-11-03** (curator: "Musket reload works great"; its log: 6 shots, 5 presses
turned into reloads, each loaded on `reloadStop` 2.46 s later; no shot fired empty).

## If it misbehaves

- Dodge still cuts the reload: check the log. No "Musket shot" line → the weapon is not matched (check
  `Plugins`). Shot logged but no "Dropped" line → the dodge came after `LockAfterShotMs`; raise it.
- Speed stays low after aiming: check `player.getav speedmult` (100 expected with no other effects).
