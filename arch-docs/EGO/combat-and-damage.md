# EGO — combat, damage and defence

How EGO's combat rework is actually built. Every mechanic below was read out of the records; the
author's marketing claims are marked **[author]** and the measured mechanism follows.

## How the rules reach the player

**EGO's entire player-facing ruleset is delivered by perks on the `Player` NPC record**
(`000007:Skyrim.esm`). Enderal's own Player record already grants 20 perks (including all the
vanilla smithing perks — see CLAUDE.md); EGO's override grants **62**, of which **42 are EGO's own**.
**[verified]**

It also, on the same record:

| Field | Enderal FS | EGO |
|---|---|---|
| `HealthOffset` | 40 | **50** |
| `MagickaOffset` | 38 | **55** |
| `StaminaOffset` | 45 | **35** |
| `SpeedMultiplier` | 95 | **100** |
| `ActorEffect` | +`_00E_Game_AbBlockWaiting 0EEE86` | **removed** |
| `Perks` | +`_00E_FS_Alchemy_BalancingPerk_RestorePotions 02F219` | **removed** |
| `Perks` | — | + vanilla `SavageStrike 03AF81`, `DevastatingBlow 052D52`, `DeflectArrows 058F68` (injected) |

> **This is the single most important conflict surface in the whole mod.** Any plugin that overrides
> `Player 000007:Skyrim.esm` and does not carry EGO's 42 perks silently deletes EGO's combat,
> economy, alchemy, mana and stagger rules while leaving every other record intact — the mod appears
> installed and does almost nothing. If a Zenderal patch must touch `Player`, copy **EGO's** record
> and edit that.

A second delivery path exists for the ability spells those perks hand out: the quest
**`XionPerkSpellFix 001F2A`** with script `EGO_perkSpellFix` removes and re-adds seven ability spells
on every `OnPlayerLoadGame`. See [`scripts.md`](scripts.md#ego_perkspellfix).

For NPCs the same trick is applied per-actor. Across 1118 NPC records **[verified]**:

| EGO perk | NPCs |
|---|---|
| `XionNPCHumanoid` | 386 |
| `XionNPCUndead` | 226 |
| `XionResistGhost` | 42 |
| `XionResistDraugrPlayerPerk` | 39 |
| the 22-perk apparition/follower bundle (`XionWeaponBonus*`, `XionSilver*`, `XionStaggerStuff`, …) | 21–22 each |
| `XionFollowerPerk` | 16 |

## Stamina governs melee damage

**[author]** *"All actions drain stamina, physical damage is now dependent on your current stamina
(also applies to human enemies)."*

**Mechanism [verified].** `XionStaminaManagement 001CAA` (player) and `XionNPCStaminaManagement
001E5C` / the stamina block inside `XionNPCHumanoid 001D7F` (NPCs) hang three
`ModAttackDamage` entry points off `GetActorValuePercent(Stamina)`:

| Stamina | Damage multiplier |
|---|---|
| ≥ 70 % | ×1.1 |
| 30 % – 10 % | ×0.9 |
| < 10 % | ×0.7 |

The drains themselves are `Ability` spells with `HideInUI`, `NoDuration`, `Painless` peak-value
effects on `Stamina`, granted by the same perk:

| Ability | Drain magnitudes (conditioned per effect) |
|---|---|
| `XionZZZStaminaAttack 001D89` | 0.3 / 1.125 per tick |
| `XionZZZStaminaAttackUnarmed 001E09` | 0.2 |
| `XionZZZStaminaBowShieldSwim 001CAC` | 1.0 / 1.35 / 1.8 / 2.5 |

`XionNPCHumanoid` additionally sets `ModPowerAttackStamina ×0.4`; `XionNPCUndead` sets it to **×0**
— undead power-attack for free.

## Armour, weight and mana

**[author]** *"Heavy Armor grants more protection and adds stagger reduction but will slow the wearer
and will increase mana cost for spells. Clothing/no armour increases movement speed and reduces
manacost but clothing no longer grants armor."*

**Mechanism [verified]** — `XionArmorHeavyPlayer 0008CE` (and its apparition twin
`XionArmorHeavyApparition 001FBC`):

| Entry point | Condition | Value |
|---|---|---|
| `ModArmorRating` | target has `ArmorHeavy 06BBD2` | **×1.65** (apparitions ×1.55; `XionNPCHumanoid` ×2.7) |
| `ModSpellCost` | 1 heavy piece worn | ×1.05 |
| `ModSpellCost` | 2 pieces | ×1.10 |
| `ModSpellCost` | 3 pieces | ×1.15 |
| `ModSpellCost` | 4 pieces | ×1.20 |
| `ModSpellCost` | wearing `XionArmorHeavyCuirass` (EGO keyword `0008D3`) | ×1.035 |

`XionArmorClothingPlayer 001EB8` mirrors it downward — **not** wearing a cuirass/boots/helmet/
gauntlets each reduce spell cost (×0.955 / ×0.975 / ×0.975 / ×0.975).

Movement is done with `SpeedMult` peak-value ability spells rather than perks:

| Ability | Effect |
|---|---|
| `XionZZZMovementHeavyArmorSlow 0008D1` | six conditioned `SpeedMult` penalties, −1.5 to −12 |
| `XionZZZMovementRobeBonusSpeed 001DC5` | +0.5 to +1.7 `SpeedMult` for robes/clothing |
| `XionZZZLightArmorScaling 001DD4` | twenty `SpeedMult` steps, +0.25 → +5.0, scaling with light-armour skill |

Supporting GMSTs: `fArmorBaseFactor` 0.03 → **0.01** and `fArmorRatingPCMax` 1.4 → **1.47**, so raw
armour rating contributes far less and the perk multipliers do the work.

`XionArmorHeavyScaling 00390D` is worth flagging as a **probable bug**: three
`ModIncomingDamage ×0.99` entries whose conditions are `HeavyArmor >= 5 && < 10` (twice, identical)
and `>= 10 && < 15`. It is not on the Player record, so it appears to be abandoned.

## Stagger and knockback

**[author]** *"Blocking … negates staggering effects."*

**Mechanism [verified]** — `XionStaggerStuff 001E60`, `ModIncomingStagger`:

| Condition | Result |
|---|---|
| `IsBlocking` | ×0 (immune) |
| 4 heavy pieces worn | ×0 |
| 3 pieces | ×0 on a 75 % roll |
| 2 pieces | ×0 on a 50 % roll |
| 1 piece | ×0 on a 25 % roll |
| wearing `XionArmorHeavyCuirass` | ×0 on a 15 % roll |
| otherwise | ×0.01 |

`XionPowerStagger 001DBD` applies the *outgoing* half: a `SelectSpell` entry point that fires
`XionStagger 001D15` on `ApplyCombatHitSpell` when the attacker is power-attacking, the weapon is
not a bow, and the target has neither `XionImmuneStrongForce` nor `XionImmuneMediumForce`.

> **`XionImmuneStrongForce 0172AC:Skyrim.esm` is a renamed base record.** Enderal's
> `ImmuneStrongUnrelentingForce` keyword is *re-purposed* by EGO — same FormID, new EditorID, same
> `Color`. A patch searching for `ImmuneStrongUnrelentingForce` by EditorID will not find it in an
> EGO load order. The companion `XionImmuneMediumForce 0008C7` is new. **[verified]**

Immunity keywords are applied at the **race** level: `XionImmuneMediumForce` on 33 races and 24 NPCs,
`XionImmuneSlow` on 22 races, `XionNoBleeding` on 13, `XionNoMaceArmorPen` on 10, `XionSkeleton` on 2.

## Weapon type identity

**[author]** *"Each weapon type has its own unique upside."*

**Mechanism [verified]** — five perks, all keyed on the vanilla `WeapType*` keywords:

| Perk | Weapon types | Effect |
|---|---|---|
| `XionWeaponBonusSwordDagger 001CEF` | Sword, Dagger, Greatsword | **+6 crit chance**; ×1.1 `ModPercentBlocked` when blocking with sword/greatsword |
| `XionWeaponBonusMace 001CEE` | Mace, Warhammer | **`ModTargetDamageResistance ×0.65`** — armour penetration |
| `XionWeaponBonusAxeStaff 001CED` | WarAxe, Battleaxe | ×1.1 damage, ×0.95 target resistance; **Staff ×0.6 damage** |
| `XionWeaponBonusBow 001CAF` | Bow | ×1.15 damage; `ModSneakAttackMult → 1` while the target is in combat (kills sneak-multiplier abuse) |
| `XionWeaponBonusOneTwoHanded 001D87` | all melee | flat +2 damage (−2 back off for bows), ×1.03 one-handed, ×1.13 two-handed |

Sweeping attacks come from `XionSweepingBlowPlayer 006AE5` — `SetSweepAttack 1` on side/back power
attacks with a two-handed weapon, paired with **×0.85 damage** as the cost. NPCs get the uncosted
`XionSweepingBlow 006AE4`.

Vanilla sneak multipliers are trimmed in parallel: `fCombatSneak1HSwordMult` 2 → **1.5**,
`fCombatSneak2HAxeMult`/`2HSwordMult` 1.5 → **1**, while `fCombatSneak1HDaggerMult` rises 2 → **2.5**.

## Creature resistance and vulnerability matrix

Enemies get per-family perks that read the *attacker's* weapon keyword (`[tab1]`) and the *target's*
actor keyword (`[tab2]`). All **[verified]**:

| Perk | Effect |
|---|---|
| `XionResistDragon 001DBF` | ×0.65 incoming from mace/warhammer/dagger/bow, ×0.8 from axe/battleaxe/sword/greatsword |
| `XionResistBoneshredder 001DBE` | ×0.8 / ×0.95 on the same split |
| `XionResistMudElemental 001DC0` | ×0.675 / ×0.8 |
| `XionVulnerableWoodElement 001DBC` | **×1.15** from axes/battleaxes, ×0.85 from everything else |
| `XionVulnerableSkeleton 001D9C` | target-resistance ×0.15 (warhammer), ×0.2 (mace), ×0.7 (battleaxe), ×0.85 (greatsword/waraxe) |
| `XionVulnerableStarling 001DDB` | ×0.45 target resistance from mace/warhammer vs `ActorTypeDwarven` |
| `XionResistSkeletonBow 001D7B` | arrows do **×0.55** vs skeletons — **×0.95 if the arrow is a silver arrow** |
| `XionResistDraugrPlayerPerk 001DBB` | ×0.6 / ×0.75 for undead carrying `XionNoMaceArmorPenUndead` |
| `XionNPCArmorPen 001F25` / `…Pen2 001F24` | flat `ModTargetDamageResistance` ×0.65 / ×0.5 for designated enemies |
| `XionNPCNonUndeadGiant 001FD2` | ×0.6 target resistance from mace/warhammer |

### Silver, ghosts and undead

**[author]** *"Undead have drastically increased armor and resistances. Added new silver weapons,
silver arrows. Ghosts have drastically increased resistances. Bypass it with silver weapons or with a
new consumable called 'Ghost Curse'."*

**Mechanism [verified].** `ActorTypeGhost 0D205E` targets take **×0.05** damage from ordinary
weapons (`XionSilverGhostDmg 001D3F`) unless the attacker has the magic effect
`XionGeisterfluchMagieres 001D3C` — the Ghost Curse consumable
(`XionGeisterflucht 001D3D`, 7 placed copies in the world). With silver:

| Attack | vs Ghost | vs `ActorTypeUndead` (non-ghost) |
|---|---|---|
| `WeapTypeBoundWeapon 0379E9` | **×15** | ×1.23, +1 flat |
| `WeapMaterialSilver 10AA1A` | **×30** | ×2.15, +5 flat |
| silver arrow (`XionSilverArrow 001D04`) | ×30 | ×2.15, +5 flat |
| vanilla-Enderal silver arrow | ×15 | ×1.23, +1 flat |

Ghosts also carry `XionGeisterfluchMagres50 001D3E` (+50 `ResistMagic`) and, on skeleton-ghosts, the
"Skeleton Ghost Abilities" spells `XionMagRes35 001D44`, `XionArmor350 001D48` and
`XionArmor150 001F0D`.

`XionQyranArrowsPerk 001E70` is the same shape for the Qyran arrow keyword: ×1.26 damage and
**×0.35 target resistance** — the armour-piercing arrow type from the changelog.

## Magic damage scaling

`XionMagicDamage 001DC8` scales spell magnitude by damage school **[verified]**:

- ×1.2 for shock, fire, `EldritchDamage 0164B1` and EGO's own `XionMagicDamagePoison 001DC7`,
  `XionMagicDamageLight 001DC9`, `XionMagicDamagePsionic 001E05` — **unless** the spell carries
  `XionWeaponEnch 001F93` (weapon enchantments are excluded).
- ×1.15 for frost.
- **×0.5** for `EldritchDamage` against `ActorTypeGhost` or `ActorTypeUndead`.
- ×1.08 / ×1.04 stacking bonuses for spells whose casting perk is a Novice / Apprentice tier perk —
  i.e. low-tier spells get a small top-up so they stay relevant.

## Difficulty is damage-only

**[author]** *"Difficulties no longer drastically change the damage multipliers and only change the
damage of enemies."*

**Mechanism [verified]** — the player-dealt multipliers are flattened to 1.0 across all six
difficulties, and only incoming damage varies:

| GMST | Enderal | EGO |
|---|---|---|
| `fDiffMultHPByPCVE` … `ByPCVH` (player → NPC) | 1.8 / 1.55 / 1.15 / 1.05 / 0.9 / 0.6 | **1.0 everywhere** |
| `fDiffMultHPToPCVE` (NPC → player, Very Easy) | 0.6 | **1.2** |
| `fDiffMultHPToPCE` | 0.8 | **1.4** |
| `fDiffMultHPToPCN` (Normal) | 0.95 | **1.6** |
| `fDiffMultHPToPCH` | 1.3 | **1.8** |
| `fDiffMultHPToPCVH` | 1.55 | **2.0** |
| `fDiffMultHPToPCL` (Legendary) | 3.0 | **2.2** |

Note Legendary is *easier* than Enderal's, and Normal is ~1.7× harder.

## AI, combat styles and movement

**[author]** *"AI reacts better, attacks/blocks more frequently. Archers now use Arrows and will
switch to melee weapons if needed."*

**Mechanism [verified].** 59 CombatStyle overrides. The recurring edits are `OffensiveMult` +
`GroupOffensiveMult` (56 records), `Melee` sub-struct (51), `CloseRange` (50), `DefensiveMult` (38)
and `LongRangeStrafeMult` (22). Representative — `csAtronachFlame 070FF9`:

```diff
-OffensiveMult: 0.76           +OffensiveMult: 1
-GroupOffensiveMult: 0.76      +GroupOffensiveMult: 1
-EquipmentScoreMultMagic: 1    +EquipmentScoreMultMagic: 2.1
 Melee:
-  AttackStaggeredMult: 1.1      +  AttackStaggeredMult: 5
-  PowerAttackStaggeredMult: 2.45+  PowerAttackStaggeredMult: 4.5
-  PowerAttackBlockingMult: 3.95 +  PowerAttackBlockingMult: 5.5
 CloseRange:
-  CircleMult: 0.3               +  CircleMult: 0.5
-  FallbackMult: 0.35            +  FallbackMult: 0.42
-LongRangeStrafeMult: 0.2      +LongRangeStrafeMult: 0.5
```

`EquipmentScoreMult*` is how "archers switch to melee" is achieved — the AI's weapon-choice
weighting. 58 MovementTypes are also overridden, almost entirely `RotateInPlaceRun` /
`RotateWhileMovingRun` (41 and 37 records) plus per-direction run/walk speeds — this is the
"different attack patterns / slower creatures" work.

Aim assist is switched off entirely: `fAutoAimMaxDegrees`, `…3rdPerson`, `…MaxDistance` and
`…ScreenPercentage` all → **0**, and `fBowNPCSpreadAngle` 4 → **1.5** (NPC archers are much more
accurate).

## Blocking, bashing and reach

| GMST | Enderal | EGO | Effect |
|---|---|---|---|
| `fBlockWeaponBase` | 0.35 | **0.57** | weapon blocking absorbs far more |
| `fBlockWeaponScaling` | 0.25 | **0.36** | and scales harder with skill |
| `fShieldBaseFactor` | 0.55 | **0.66** | shields likewise |
| `fShieldScalingFactor` | 0.2 | **0.37** | |
| `fBlockPowerAttackMult` | 0.8 | 0.75 | |
| `fStaminaBashBase` | 35 | **25** | bashing is cheaper |
| `fStaminaPowerBashBase` | 55 | **35** | |
| `fStaminaAttackWeaponBase` | 20 | **15** | attacks cost less base stamina… |
| `fStaminaAttackWeaponMult` | 1 | **0.8** | …and less per weapon weight |
| `fSprintStaminaDrainMult` | 7 | **4** | sprinting is cheaper |
| `fSprintStaminaWeightMult` | 0.02 | **0.04** | but weight matters twice as much |
| `fCombatStaminaRegenRateMult` | 0.35 | **1.0** | stamina regenerates fully in combat |
| `fCombatMagickaRegenRateMult` | 0.33 | **0.8** | so does mana |
| `fCombatDistance` | 141 | 135 | |
| `fCombatBashReach` | 141 | **110** | |
| new `fObjectHitWeaponReach` | — | 110 | EGO-authored GMST record |
| new `fObjectHitTwoHandReach` | — | 120 | EGO-authored GMST record |
| new `fDamageWeaponMult` | — | 1 | EGO-authored GMST record |

> **EGO ships 13 *new* GMST records** (`fDamageWeaponMult 001DC6`, `fObjectHitWeaponReach 0008D8`,
> `fObjectHitTwoHandReach 000D63`, `fSneakDistanceAttenuationExponent 000803`, `iMaxAttachedArrows
> 000D62`, `fSmithingArmorMax 001F04`, `fSmithingWeaponMax 001F05`, the sneak-weight pair
> `007EA2`/`007EA3`, the stealth-regen pair `007EA6`/`007EA7`, `iCrimeAlarmRecDistance 0058FE`,
> `iCrimeAlarmLowRecDistance 0058FF`) plus five new crime-gold GMSTs at `0x01DCFA–0x01DCFE`.
> The engine binds GMSTs **by EditorID**, so these override the engine's built-in defaults even
> though no master defines them. A patch that wants to change one must use *EGO's* record.

## Other combat-adjacent globals

| Global | Enderal | EGO |
|---|---|---|
| `DecapitationChance 000ECA` | 40 | **10** |
| `KillMoveRandom 05159D` | 50 | **12.5** |
| `EXPMult 008D2B` | 395 | **450** |

Killmoves and decapitations are heavily suppressed; XP gain is raised ~14 %.
