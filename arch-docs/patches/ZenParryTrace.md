# ZenParryTrace

- **Source:** `src/ZenParryTrace/` (SKSE plugin, CommonLibSSE-NG, Address Library; `build.cmd`)
- **Ships:** nothing. **Testing tool, not part of the list.** Deployed as the MO2 mod `Zenderal - Parry Trace (testing)`
  (`SKSE/Plugins/ZenParryTrace.dll`); disable it when the investigation is done.
- **Log:** `Documents/My Games/Skyrim Special Edition/SKSE/ZenParryTrace.log`
- **Status:** 1.0.0 built and run 2026-10-31: found that same-time PIE tags arrive as one event (`$ParrySpell`
  never fired) — see [`FHRFirstPerson`](FHRFirstPerson.md) v3. 1.1.0 (same day) adds the `DIR` line (found: DMK not sticky; Keytrace effects never present).
  1.2.0 (same day) follows every actor the player hits for 6 s: `ENEMY … IN/OUT` graph events (stagger, knock,
  get-up, ragdoll, MSL, PIE…, via the Character vtable hooks ZenRagdollTrace used — lock-free, formID only),
  `ENEMY … STATE` (knock state, ragdoll, `IsStaggering`, dead) and `APPLY*` = any effect from any plugin applied to
  it within 1.5 s of the hit (which combat hit spell won).
  1.3.0 (same day) adds, for the side-attack strip: `BUFF` = Reforged Directional Combat's empowered arrows
  (`801`–`806`) on every loaded actor, on change, with the player's `[fx]` and time since the player's hit; the
  player's side markers `880`–`883` in `[fx]`; and at load one `SETUP hit spell entry` line per `ApplyCombatHitSpell`
  entry the player has (priority, rank, condition count, perk → spell) — the entries competing for the one hit spell.
  1.4.0 (2026-11-10), for first-person unarmed power attacks that never start: `IN` = every attack/power/block/H2H/equip
  event sent **into** the player's graphs (PlayerCharacter's `IAnimationGraphManagerHolder::NotifyAnimationGraph`,
  vtable `[3]` slot 1) with `(NOT ACCEPTED)` when the manager refused it; `VARS` = each graph's `iState` tag and the
  variables the H2H attack transitions test (`iRightHandType`, `iLeftHandType`, `bWantCastLeft`, `iWantBlock`), on change.
  1.4.1 (2026-11-12), for first-person dual daggers that stop attacking after a weapon is equipped (freed by a
  camera switch): graph events sent **out** of the player's graphs now also include equip/draw tags (`WeapEquip_Out`,
  `WeaponDraw`, `BeginWeaponDraw`…), to show whether the first-person graph ever leaves its equip state. Run from
  MO2's `overwrite` (no ticking) the same day: equip was fine. A 1P dual-dagger power attack never sent `attackStop`
  (fixed in [`FHRFirstPerson`](FHRFirstPerson.md)). Removed from `overwrite` after.
  An `APPLY` line alone does not prove an effect took: the apply event fires before the effect's conditions are
  checked (the v3 log shows `803`'s mutually exclusive `874` and `82A` applied together).

## Why

With [`FHRFirstPerson`](FHRFirstPerson.md) enabled, first-person directional power attacks worked in game
(2026-10-31) but the back-light parry seemed not to. FHR's parry is a chain across three actors' perks and
effects (records in `reference/mods/FHRBalance`):

1. the back light attack's `PIE.$ParrySpell` casts `BackLightParrySpell 80E` on the player →
   `ParryWeaponSelf 810` (no shield) / `ParryShieldSelf 80F` (shield) = the window; `$BackLight` → `BackLight 88A`;
2. an enemy hit landing in the window: the attacker's `ReforgedParryController 876` (SPID, NPCs) applies
   `HitFrameTriggerSpell 803` to the player → `WeaponParryTrigger 82A` / `ShieldParryTrigger 811` if the window was
   open, `ParryDamageCheck 874` if not (hit before the window = no parry); `ParrySlowTimeMGEF 82F` (MCM global);
3. the player's own swing lands with `88A` + `82A`: the player's `876` (from start-game quest `806`'s player alias
   ability `807`, since SPID never targets the player) applies `Weapon Parry Poise Damage 892` to the enemy.

Each link can fail silently, so this logs all of them instead of guessing.

## What it logs

| Line | Source | Shows |
|---|---|---|
| `EVENT 1P*/3P` | PlayerCharacter's `BSTEventSink<BSAnimationGraphEvent>` (the hook Payload Interpreter uses) | every `PIE` payload and hit/swing/window/SBF/MCO event, and **which graph sent it** (`*` = active graph) |
| `FX` | player update | FHR's parry effects on the player switching on/off, attack state, blocking |
| `APPLY` | `TESMagicEffectApplyEvent` | every FHR-plugin effect applied to or by the player, with caster and target |
| `HIT` | `TESHitEvent` | every hit to or from the player, with the player's parry effects at that moment |
| `SETUP` | load | whether the player has perk `876` and quest `806` runs |
| `DIR` (1.1.0) | player update, on change; also appended to each `ATTACK state 0 -> 1` | DMK's `DirecionalCycleMoveset` in each graph (`absent` = not injected), PaulMix's `KDForward/KDLeft/KDBack/KDRight` per graph, Keytrace's held-key effects 801–804 and the actor's moving flags, as `FLBR` masks |
| `GRAPH` / `CAMERA` / `ATTACK` | player update | the player's graphs' project names, active graph, view, melee attack state |
| `IN` (1.4.0) | PlayerCharacter's `NotifyAnimationGraph` | attack/power/block/H2H/equip events sent into the player's graphs, and whether they were accepted |
| `VARS` (1.4.0) | player update, on change | per graph: `iState`, `iRightHandType`, `iLeftHandType`, `bWantCastLeft`, `iWantBlock` |

## How to read a parry attempt

With FHRFirstPerson v2 (parry move, then riposte), S + light attack into an enemy swing should show, in order:
`EVENT 1P* PIE $BackLight` / `$ParrySpell` (the parry move played and PIE got it) → `APPLY PLAYER -> PLAYER …
ParryWeaponSelf` and `FX on [ParryWeaponSelf…]` → `HIT <enemy> -> PLAYER` → `APPLY <enemy> -> PLAYER …
WeaponParryTrigger` / `FX on [WeaponParryTrigger(parried)]`; then the riposte: `EVENT 1P* PIE $BackLight` /
`$ParryKnockdown` → `HIT PLAYER -> <enemy>` → `APPLY PLAYER -> <enemy> … Poise Damage Parry`. The first missing
line is the broken link (`ParryDamageCheck` instead of `WeaponParryTrigger` = the hit landed before the window).
