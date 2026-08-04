# EGO — the shipped scripts

EGO ships **7 compiled `.pex` as loose files** in `scripts/`, plus 14 `.psc` in `scripts/source/`.
Six of the seven **replace Enderal's own scripts**; one is EGO's own.

> **Loose scripts are not resolved by plugin load order.** They beat `E - Misc.bsa` because loose
> files win over archives, and they beat each other by **MO2 mod priority**. Nothing in xEdit shows
> this conflict. If another list mod ships any of the six names below, whichever mod sits lower in
> the MO2 left pane wins — regardless of where the plugins sit. Check this before debugging "EGO's
> apparition balance isn't applying".

| Script | Replaces Enderal's | `.pex` compiled | Source shipped |
|---|---|---|---|
| `_00e_a0_banksystemquest.pex` | yes | 2020-08-05 | **no** |
| `_00e_eisprankepotionscn.pex` | yes | 2021-03-09 | yes |
| `_00E_Phasmalist_ApparationAlias.pex` | yes | 2021-05-09 | yes |
| `_00E_Phasmalist_NewApparitionAlias.pex` | yes | 2022-01-12 | yes |
| `_00e_theriantrophist_detoxification.pex` | yes | 2021-03-30 | yes |
| `_00E_Theriantrophist_PlayerAsWerewolf.pex` | yes | 2021-04-12 | yes |
| `EGO_perkSpellFix.pex` | **no — new** | 2020-03-02 | yes |

All timestamps are the `Compiled :` header Champollion reads out of the `.pex`. **[verified]**

## `EGO_perkSpellFix`

EGO's own script, attached to the quest `XionPerkSpellFix 001F2A` (`StartGameEnabled`, `RunOnce`)
via a `PlayerAlias` forced to `PlayerRef 000014`. It does one thing **[verified]**:

```papyrus
Event OnPlayerLoadGame()
	; RemoveSpell x7 then AddSpell x7
EndEvent
```

on `XionZZZAnathemaCurse 001EC4`, `XionZZZMovementHeavyArmorSlow 0008D1`,
`XionZZZLightArmorScaling 001DD4`, `XionZZZMovementRobeBonusSpeed 001DC5`,
`XionZZZStaminaAttack 001D89`, `XionZZZStaminaAttackUnarmed 001E09` and
`XionZZZStaminaBowShieldSwim 001CAC`.

**Why it exists.** Those seven are conditioned multi-effect Ability spells granted by perks. Ability
spells whose conditions changed between saves keep the stale evaluation until the spell is
re-applied; removing and re-adding them on every load forces re-evaluation. It is also what makes
EGO partially work on an existing save — it re-applies the abilities without needing the perks to be
re-granted.

**Patching consequence.** If a Zenderal patch retunes any of those seven ability spells, the change
takes effect on the next load without a clean save — but if a patch *adds* a comparable ability
spell of its own, it needs its own re-apply quest; EGO's list is hard-coded.

## `_00e_a0_banksystemquest`

No source shipped; the analysis below is from Champollion output. **The compound-interest ladder is
flattened** **[verified]**:

| Deposit | Enderal `ZinsPercent` | EGO |
|---|---|---|
| < 100 | 0.3 | 0.3 |
| 100–299 | 0.5 | **1.0** |
| 300–399 | 0.8 | 1.0 |
| 400–499 | 1.2 | 1.0 |
| 500–599 | 1.6 | 1.0 |
| 600–699 | 1.9 | 1.0 |
| 700–799 | 2.1 | 1.0 |
| 800–899 | 2.4 | 1.0 |
| 900–999 | 2.6 | 1.0 |
| ≥ 1000 | 2.8 | 1.0 |

Ten branches become two. The 250-gold/day cap (`if Zins > 250`) is untouched, so at ≥ 25 000 gold
deposited the cap binds either way; below that, EGO's bank pays a third of Enderal's.

## `_00e_eisprankepotionscn`

One line **[verified]**:

```diff
-	akTarget.ModActorValue("CarryWeight", 1)
+	akTarget.ModActorValue("CarryWeight", 0.5)
```

The Ice Ranke potion's carry-weight effect is halved.

## `_00e_theriantrophist_detoxification`

One line **[verified]** — the Detoxification talent's chance to keep the chymikum doubles:

```diff
-	Float chanceToKeepChymikum = (talentLevel - 1) * 0.25
+	Float chanceToKeepChymikum = (talentLevel - 1) * 0.5
```

## `_00E_Theriantrophist_PlayerAsWerewolf`

**[author]** *"Fixed and rebalanced Lycanthrope (fixed fleeing enemies, fixed range issues, fixed
damage calculation)."*

**Mechanism [verified].** Balancing constants:

| Property | Enderal | EGO |
|---|---|---|
| `AlchemyPercentageDmg` | — | **0.25** (new: damage per Alchemy point) |
| `AlchemyPercentage` | 0.03 | 0.03 |
| `StaminaPercentage` | 0.005 | **0.06** |
| `BalancingDamageMalusPercent` | 33 | **5** |
| `BalancingHealthMalusPercent` | 85 | 85 |

Structural changes:

- Claw damage is no longer derived from equipped weapon/spell strength:
  `fClawDamage = boostFactor * _CalcWeaponSpellStrength(player) * …` becomes
  `fClawDamage = 1 + boostFactor * …`, and the `LastBribedIntimidated` bonus is dropped from the
  final `ForceWolfUnarmedDmg` call.
- Damage resist no longer inherits the pre-transform value
  (`fDamageResist = preTransformDmgResist + bonus` → `fDamageResist = bonus`).
- Stamina is computed from a flat 115 base (90 with `_00E_Class_Theriantrophist_P09c_AetherBlood`)
  instead of the player's base stamina.
- `player.restoreav("stamina"/"magicka", 9999)` on transform.
- `Steam.UnlockAchievement("END_WEREWOLF_01")` → `Game.UnlockAchievement(…)`. Both functions exist
  in Enderal's script tree (`Game.psc:457`), so this is a call-site change, not a fix for a missing
  API. **[verified]**

## The two apparition alias scripts

Both implement Enderal FS's Phasmalism apparitions. EGO's edits **[verified]**:

| Property | Enderal | EGO |
|---|---|---|
| `fArcaneFeverLevel01` | 7.00 | **8.00** |
| `fArcaneFeverLevel02` | 6.00 | 6.00 |
| `fArcaneFeverLevel03` | 5.00 | **4.00** |
| `fArcaneFeverModWarrior` | −1 | **0** |
| `fArcaneFeverModMage` | +1 | **0** |
| `iGhostlyMageBoostDestructionPowerMod1 / 3` | 7 / 25 | **8 / 22** |
| `iGhostlyMageBoostMagicka1 / 2 / 3` | 15 / 40 / 75 | **40 / 70 / 100** |
| `iGhostlyRangerBoostArchery1 / 2 / 3` | 7 / 17 / 30 | **10 / 18 / 26** |

Plus mechanical changes: the melee boost is applied to `onehanded` **and** `twohanded` instead of the
composite `MeleeDamage` AV, and the hard-coded `HealRate 50` on summon is removed (out-of-combat
apparition regeneration now comes from `XionApparitionRegeneration 001E75` in the plugin instead).

The tier-I figure change is mirrored in the plugin's own `_00E_Message_Phasmalist_P03` tooltip
(7 % → 8 %) — see [`magic-and-talents.md`](magic-and-talents.md#talent-memory-tree-perk-overrides).

### ⚠ These scripts predate Enderal 2.0.12

`_00E_Phasmalist_ApparationAlias.pex` was compiled **2021-05-09**; Enderal SE 2.0.12's own copy of
the same script (in `ScriptsEnderal.zip`) uses a **different health-bar API**. **[verified]**

| | Enderal 2.0.12 source | EGO's compiled script |
|---|---|---|
| show | `HealthBarManager.Show(actor)` | `ActorHealthBarShower.AddActors(actor)` where `ActorHealthBarShower = Game.GetFormFromFile(0x01024B66, "Enderal - Forgotten Stories.esm")` — i.e. `_00E_SkyUI_Widgets 024B66` |
| hide | `HealthBarManager.Hide(actor)` | `ActorHealthBarShower.RemoveActors(actor)` |

`_00E_Phasmalist_NewApparitionAlias` (compiled 2022-01-12) likewise calls
`ForgottenStoriesMiscDialogue.showActorHealthBars(akSelf)` where 2.0.12 calls
`HealthBarManager.Show(akSelf)`, and it uses `ModAV`/`ForceAV` where 2.0.12 uses
`ModActorValue`/`ForceActorValue`.

Both `HealthBarManager.psc` and `_00e_gui_actorhealthbar.psc` exist in Enderal 2.0.12's script tree,
so EGO's version should still *run* — but it is built on SureAI's **older** implementation and does
not carry whatever the `HealthBarManager` refactor was meant to fix. It also removes the
`ForceActorValue("HealRate", DEFAULT_HEAL_RATE)` restore in `NewApparitionAlias`'s teleport
`OnUpdate` handler.

**This is unverified in game** — it is a source-level divergence, not an observed bug. It is the
first place to look if apparition health bars or apparition regeneration misbehave in Zenderal, and
a legitimate candidate for a Zenderal script patch that forward-ports EGO's balance constants onto
Enderal 2.0.12's current script body.

## Dead files

`scripts/source/` also contains seven `.psc` with no matching `.pex` and no matching record in the
plugin: `_sycccobookscript`, `_sycmainquestscript`, `_sycmainquestscript - Copy`,
`_sycMainQuestScript balanced`, `_sycMainQuestScript balanced - Copy`, `_sycMainQuestScript BASE`,
`_sycmaintenancerefaliasscript`, `_sycmaintenancerefaliasscript - Copy`. They are packaging
leftovers. **[verified]**

## Recompiling any of these

Use the `papyrus-compile` skill. The import order matters more than usual here, because five of the
six names collide with Enderal's own:

```
-i="<papyrusSource.enderal>;<papyrusSource.skse>;<papyrusSource.vanilla>"
```

Enderal's tree **must be first** (first-wins — see CLAUDE.md). To rebuild EGO's version you also
need EGO's `scripts/source/` on the path *ahead* of Enderal's, since the whole point is to compile
EGO's copy rather than SureAI's.
