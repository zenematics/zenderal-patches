# EGO — magic, spells and talents

## Enderal's five schools, and the actor values behind them

EGO's perks make the mapping explicit — each `XionManaTweaks*` perk is named for an Enderal school
and gates on the vanilla novice/apprentice/adept/expert/master casting perk of the matching vanilla
school **[verified]**:

| Enderal school | Vanilla AV / perk chain |
|---|---|
| Elementarism | `Destruction` (`0F2CA8`, `0C44BF`, `0C44C0`, `0C44C1`, `0C44C2`) |
| Light Magic | `Restoration` (`0F2CAA`, `0C44C7` … `0C44CA`) |
| Entropy | `Conjuration` (`0F2CA7`, `0C44BB` … `0C44BE`) |
| Psionic | `Illusion` (`0F2CA9`, `0C44C3` … `0C44C6`) |
| Mentalism | `Alteration` (`0F2CA6`, `0C44B7` … `0C44BA`) |

Anything you write that touches Enderal magic should use this table rather than guessing from the
in-game school name.

## Mana cost is roughly doubled

**[author]** *"Manacost is drastically increased, Manacost reduction perks are now mandatory …
Manacost of spells is increased if you have a low skill and cast high level spells."*

**Mechanism [verified]** — two five-perk families, all on the Player record.

`XionManaTweaks 00081F` … `XionManaTweaks5 00082B` apply a flat `ModSpellCost` multiplier per spell
tier, one perk per school:

| Spell tier (casting perk) | `ModSpellCost` |
|---|---|
| Novice | ×2.083 |
| Apprentice | ×2.126 |
| Adept | ×2.169 |
| Expert | ×2.212 |
| Master | ×2.255 |

`XionManaSkillScaling 001ED5` … `XionManaSkillScaling5 001EDA` add the skill-vs-tier penalty on top,
per school:

| Your skill | Casting an Apprentice spell | an Adept spell | an Expert spell |
|---|---|---|---|
| < 25 | ×1.1 | ×1.2 | ×1.3 |
| 25–49 | — | ×1.1 | ×1.2 |
| 50–74 | — | — | ×1.1 |

Supporting GMSTs:

| GMST | Enderal | EGO | Meaning |
|---|---|---|---|
| `fMagicCasterSkillCostMult` | 0.5 | **1.1** | skill reduces cost more than twice as strongly |
| `fMagicSkillCostScale` | 0.5 | **0.65** | steeper cost curve across tiers |
| `fMagicDualCastingCostMult` | 2.8 | **2.3** | dual-casting is relatively cheaper |
| `fCombatMagickaRegenRateMult` | 0.33 | **0.8** | mana regenerates in combat |
| `iMaxPlayerRunes` | 1 | **3** | three runes can be active |

`XionManaDualCastingDestr 001D95` is a `ModSpellCost ×1` on dual-cast `ElementalMagic` — a no-op as
shipped, presumably a tuning hook left at neutral.

## Summons, enchanting and durations

| Perk | Effect |
|---|---|
| `XionMultipleSummon 001F6D` | `ModCommandedActorLimit → 3` |
| `XionSummonManaRegen 001F38` | grants `XionSummonManaRegen 001F3A` — **−2.5 `MagickaRate`** while a summon is active ("Summoning Nerf") |
| `XionMultipleEnchants 001F6C` | `ModNumAppliedEnchantmentsAllowed → 3` |
| `XionEnchantmentBuff 001ECD` | `ModEnchantmentPower ×0.75`, 2 enchantments allowed |
| `XionEnchantDouble 006AEE` | `ModEnchantmentPower ×0.6`, 2 enchantments allowed |
| `XionSpellIncreasedDuration 0083E8` | the **Stable Spellwork** line: ×1.4 / ×1.7 / ×2.0 spell duration by rank, excluding elemental-damage and `XionLightNoDurationScaling`/`XionPsionicNoDurationScaling` spells |
| `XionRedSun 001F8A` | `ModIncomingSpellMagnitude ×1.15` for fire — the "Red Sun" state |

`fEnchantingSkillFactor` drops 2.4039 → **1.8**; `fAlchemySkillFactor` rises 2 → **2.2**.

## New player spells

**[author]** *"26 completely new Spells, 5 of them are mystical spells."* The plugin carries 171 new
SPEL records, most of them NPC-only casts and ability spells; the **player-obtainable** ones each
have a matching spell tome BOOK record. Full list **[verified]** — see
[`new-records.md`](new-records.md) for FormIDs:

| Line | Ranks | Records |
|---|---|---|
| Magelight | I–IV | `XionSpellRealMagelight1–4` (`000861`, `000862`, `001D67`, `001E40`) |
| Light Beam | I–IV | `XionSpellLightbeam1–4` (`001CC9`, `001D0A`, `001E43`, `006AE7`) |
| Healing Aura | I–II | `XionSpellHealAura1/2` (`0008A3`, `0008A4`) |
| Resistance against Poison | I–II | `XionSpellPoisonResistance1/2` (`0008A8`, `0008A9`) |
| Banish | I–III | `XionSpellBanish1–3` (`0083E9`, `0083ED`, `0083EE`) |
| Stable Spellwork | I–III | `XionSpellDuration1–3` (`0083E6`, `0083EB`, `0083F9`) |
| Transmute Self | Fire / Ice / Lightning | `0083D7`, `0083DA`, `0083DC` |
| Singles | — | Night Eye `000875`, Nightmare `000878`, Waterwalking `001CCA`, Unstable Thoughts `001CCB`, Soothing Rune `001CCC`, Panic Rune `001CCD`, Create Illusion `001CCE`, Kinetic Blast `001EAB`, Safe Fall `001E39`, Circle of Invigoration `0083F3`, Blindness `0083FB`, Water Breathing III `0083F1`, Poisonous Touch `00086A` (**unused**) |
| **Mystical** (`_60E_`) | — | Fire Nova `000800`, Kinetic Nova `00086E`, Mindstorm `00087C`, Hysteria `001CBF`, Lightblade `001F7E`, plus a Death Storm tome `001DFD` |

Two new scrolls (`XionRolleFeuerpfeil2 001CC5` Scroll of Firebolt, `XionFrostCloak 001CC6` Scroll of
Winter Skin) and 34 scroll overrides round it out.

Distribution is through **seven new leveled spell lists** — `XionElementalSpell_26`,
`…_26_All`, `…_26_50none`, `…_30`, `…_30_All`, `…_30_50none`, `XionSummonSpells_30` — plus the
overridden vendor/loot book lists (`_00ETraderSpellBooksLevelA–D`, `_00E_SpellBooksLootA–D`,
`_00E_FS_MysticalSpellBooks`, `_00E_FS_Forbidden_TraderSpellBooks_*`).

Three new "forbidden" keywords and form lists control what vendors may not sell:
`VendorItemForbidden 001E29`, `VendorItemSpellTomeForbidden 001FB9`, `LehrbuchForbidden 001FB7`,
with `VendorItemsAlchAndMagicForbidden 001E2A`, `VendorItemsKreamerForbidden 001FB8` and
`VendorItemsFoodIngredientNoSkill 001FB1`.

## Talent (memory-tree) perk overrides

**[author]** *"Talents/Perks rebalanced and completely reworked some of them, added cooldown
description to memory trees."*

**Mechanism [verified].** 122 perk overrides, of which **116 change `Effects`**. Every one of
Enderal's nine memory-tree classes is touched:

`_00E_Class_BladeDancer_*`, `_00E_Class_Elementalist_*`, `_00E_Class_Infiltrator_*`,
`_00E_Class_Keeper_*`, `_00E_Class_Phasmalist_*`, `_00E_Class_Sinistrope_*`,
`_00E_Class_Thaumaturge_*`, `_00E_Class_Theriantrophist_*`, `_00E_Class_Trickster_*`,
`_00E_Class_Vagrant_*`, `_00E_Class_Vandal_*` — plus the affinity perks
(`_00E_Affinity_AbDarkKeeperPerk 143337`, `…AbDrifterPerk_BoostChymikumEffectiveness 02F18C`,
`…AbDruidPerk_… 02F18D`), the three `_00E_A0_*` talent perks (Focus, Shadow of the Wind,
Steeltempest) and `_00E_FS_Alchemy_BalancingPerk` / `…_RestorePotions`.

The commonest edit is **narrowing an existing entry point with extra conditions** rather than
retuning a value. `_00E_Class_BladeDancer_P03_A_Carnage 069D51` is typical: EGO leaves the
`ApplyCombatHitSpell` bleed intact and adds two exclusions — `ActorTypeUndeadHumanoid 03346E` and
EGO's own `XionNoBleeding 001F13` **[verified]**, so skeletons and constructs stop bleeding.

The matching **209 Message overrides** are the memory-tree tooltip text (`_00E_Message_*`,
`_00E_FS_A3_*`), rewritten so the displayed numbers match the new balance. They also lose their
non-English translations — see [`plugin-anatomy.md`](plugin-anatomy.md#localisation-is-stripped).
`_00E_Message_Phasmalist_P03` shows both at once: the Arcane Fever tier-I figure moves 7 % → **8 %**
in the text, matching the identical change in the shipped
`_00e_phasmalist_apparationalias.psc` **[verified]** — plugin and script must be kept in step.

> **If you rebalance a talent perk, you must also edit its Message.** Enderal's memory-tree UI reads
> the MESG record, not the perk, so a perk-only change produces a tooltip that lies.

## Shouts and creature magic

35 Shout overrides plus three new ones (`_00E_DwarvenCenturionSteamBreath02 002C91`,
`_00E_MyradPoisonBreathShoutBounty 008408`, `XionGulFireBreath 001E53`) implement the "Starling
Centurios use their steam breath / Starling Spiders shoot lightning sparks" changes **[author]**.

The bulk of the 171 new spells are NPC casts named `NPC*` / `cr*` (`NPCChainLightning`,
`NPCXionDeathstorm`, `crWispMelee*`, `crXionFrostspiderBite1/2`, `crXionParalyzeBite`, …) and race
ability spells applied through the 89 Race overrides:

| Race ability | Races |
|---|---|
| `Xion20%PoisonRes 000893` | 11 |
| `Xion75%PoisonRes 000810` | 10 |
| `AbSchlammelementar 000818` (Mud Golem) | 7 |
| `AbVatyrFireVulnerability 001E74` | 6 |
| `Xion30%PoisonRes 001EF0` / `Xion10%PoisonRes 008405` | 4 each |
| `Xion50%PoisonRes 00089D` | 2 |
| `AbCrystalEle 001D2A`, `AbOorbaya 001D1A`, `XionPoisonResWolf 001EBA`, `crChaurusPoisonSpit00 008409` | 1 each |

Race records also change `UnarmedDamage` (64), `Attacks` (61), `Starting` attributes (58),
`ActorEffect` (49), `EquipmentFlags` (35), `Regen` (27), `UnarmedReach` (26) and `BaseMass` (25)
**[verified]** — this is the "more diversity between creatures" work.
