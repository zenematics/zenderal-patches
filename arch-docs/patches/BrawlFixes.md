# BrawlFixes

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/BrawlFixes/`
- **Ships:** *(no plugin — two recompiled scripts)*
- **FormID block:** _(none)_

## What it does

Forks SureAI's two brawl scripts, `_00E_DGIntimidateAliasScript` and `_00E_DGIntimidatePlayerScript`, which **every** brawl in Enderal runs through (NQ12 Silia Foxhand, NQ_G_04 Duul, FS_NQ06 Darius Kupferhammer, the EnvironmentScene01 drunk). Both were tripping constantly next to the list's combat framework — see the `OnHit`/`akSource` gotcha below for the mechanism and the four wrong diagnoses it cost. Two `; ZP` guards: (1) `OnHit` requires `akWeapon as Weapon` to be non-None before converting the brawl to a real fight, since the parameter is really the hit *source* and is a **Spell** for a magic hit; (2) both `OnMagicEffectApply` handlers require `MagicEffect.GetAssociatedSkill()` to be one of the five schools before flagging stage 150, because Enderal's own offensive effects all carry a `MagicSkill` and combat-framework markers carry none (**verified**: zero across `For Honor in Skyrim` + `For Honor Reforged`, 482 across base Enderal). NO Property added/removed/renamed — the quest VMAD binds `UnarmedWeapon`, `DGIntimidateFaction`, `Opponent` and `OpponentFriend` by name. Nothing else in the list ships either script loose (they live only in `E - Misc.bsa`), so no sort position is required. **Credit SureAI**

## `OnHit`'s second parameter is the hit source

- **`OnHit`'s second parameter is the hit SOURCE, not a weapon — and a modern combat
  framework makes it a Spell on every single blow.** **[verified in-game 2026-08-28, after
  four wrong diagnoses]** The signature reads `OnHit(ObjectReference akAggressor, Form akWeapon,
  Projectile akProjectile, …)`, but that `Form` is a `Weapon` for a swing and a **`Spell`** for a
  magic hit. Any script testing it as *"the source exists and is not X"* therefore fires on every
  spell that lands. Enderal's brawl script does exactly that:

  ```papyrus
  if akProjectile || (akWeapon && akWeapon != UnarmedWeapon)   ; "the player swung a weapon"
      pPlayer.RemoveFromFaction(DGIntimidateFaction)
      pActor.RemoveFromFaction(DGIntimidateFaction)
      pActor.StopCombat()  /  SendAssaultAlarm()  /  StartCombat(pPlayer)
      GetOwningQuest().SetStage(150)
  ```

  `For Honor Reforged` casts `HitFrameTriggerSpell 000803` at the target on **every landed hit**
  (`ReforgedParryController`'s unconditional `ApplyCombatHitSpell` entry), plus
  `Parry Knockdown Spell 000836`, `ParryStaggerKnockdownSpell 0008B1` and `SP_Stagger_Parry 00082F`
  on a parry — and **none of those effects carries the `NoHitEvent` flag**, so `OnHit` fires. Result:
  the brawl ran its full "you cheated" teardown on every punch, and the `StopCombat()`/`StartCombat()`
  pair restarted combat on an **Essential** actor, snapping her health back to full. Fix is a type
  check: `akWeapon as Weapon` is `None` for a spell. Three things to generalise:
  - **`NoHitEvent` on an MGEF is what stops a marker spell reaching `OnHit`.** Auditing a combat
    mod's spells for its *absence* is the fast way to find which of them will trip host scripts;
    `MagicEffect.IsEffectFlagSet` and the serialized `Flags:` list both show it.
  - **A parry/block payload fires in FIRST person too**, because blocking is a shared behaviour —
    unlike an OAR move-set, which is third-person only. "It only happens in third person" is
    therefore evidence about *move-sets*, not about the whole framework, and reading it as the
    latter cost a whole diagnosis here.
  - **Take the player's animation report literally.** "The animation for going from normal to fists
    ready was playing" *was* the `StopCombat`→`StartCombat` round trip, and it identified the guilty
    function faster than four passes over the records did. An actor visibly leaving and re-entering
    combat means something called those two.
