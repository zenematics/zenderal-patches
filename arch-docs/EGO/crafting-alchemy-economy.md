# EGO — crafting, alchemy and economy

## Crafting: 727 ConstructibleObjects

**[author]** *"Completely reworked and fixed armor/weapon blueprint recipes, fixed/balanced all the
entries (about 600) of dismantle recipes. Added arrow crafting, added a new armor-piercing arrow
type."*

**Mechanism [verified].** 653 COBJ overrides + 72 new + 2 injected (`_02E_RecipeWeapon_19ESilberschwert
1489F0`, `…19ESilbergrossschwert 1489F1` — see [`plugin-anatomy.md`](plugin-anatomy.md#injected-records)).
Distribution by workbench keyword:

| Workbench keyword | Recipes | What |
|---|---|---|
| `InvisibleDismantling 02F336:FS.esm` | **344** | Enderal's dismantle/salvage system |
| `CraftingSmithingArmorTable 0ADB78` | 115 | armour tempering |
| `CraftingSmithingForge 088105` | 113 | forging |
| `_00E_Phasmalist_CraftingSummoningWorkbench 01E945:FS.esm` | 49 | phasmalist trinkets |
| `CraftingTanningRack 07866A` | 31 | leather |
| `CraftingSmithingSharpeningWheel 088108` | 28 | weapon tempering |
| `CraftingCookpot 0A5CB3` | 27 | food |
| `CraftingSmelter 0A5CCE` | 20 | ingots |

Conditions used across all 727 **[verified]**: `GetItemCount` ×655, `HasPerk` ×280,
`GetActorValue` ×125, `EPTemperingItemIsEnchanted` ×72. The perk conditions break down as:

| Perk | Recipes |
|---|---|
| `_00E_Class_Phasmalist_P04_B_ArcaneSmith 05218E` (Enderal's Arcane Blacksmith) | 215 |
| `GetActorValue Smithing >= N` | 125 |
| `_00E_Class_Phasmalist_*` (`01E95E`, `01E972`, `01E95D`, `01E96B`, `01E96C`, `02A2A0`) | 59 |

That is **exactly the archetype CLAUDE.md documents for Enderal's own forge recipes** — an AV check
plus a `GetItemCount <blueprint> >= 1`. EGO does not invent a new gating mechanism; it re-tunes the
existing one. A Zenderal recipe patch written to the Enderal pattern stays compatible.

Two new GMST records raise the tempering ceiling: `fSmithingArmorMax 001F04` = **9.25** and
`fSmithingWeaponMax 001F05` = **8.75** (both authored by EGO; no master defines them).

### New recipe families

| Family | Records |
|---|---|
| **Arrow crafting** | `XionArrow1Iron` … `XionArrow7Qyran` (`001E61`–`001E71`) — eight arrow recipes covering iron, steel, rune, silver, starling, righteous, aeterna and the new Qyran armour-piercing arrow |
| **Bolt crafting** | `XionBolt1Steel`, `XionBolt2Silver`, `XionBolt3Starling` (`002C72`–`002C74`) |
| **Crossbows** | `XionRecipeCrossbowForged 002C3D`, `XionRecipeStarlingCrossbowForged 002C42`, plus four temper recipes (`002C3E`–`002C41`) |
| **Silver weapons** | `_02E_RecipeWeapon_19_SilverSteelMaceForged 005E66`, `…WarhammerForged 005E65`, `_02E_RecipeWeapon_19ESilberkriegsaxt2 001D35`, `…schlachtaxt2 001D36` + their tempers |
| **New dismantles** | 15 `_02E_/_03E_DismantleWeapon_*ToMoonstoneIngot` / `…ToShadowSteelIngot`, plus `XionDismantle*` for Anathema and the corroded swords |
| **Cooking / utility** | `XionRecipeFoodMammothSoup 1–4`, `XionRecipeFoodMudcrabLegsCooked`, `XionRecipeFoodPriseSalz`, `XionRecipeCoal 008406`, `XionRecipeNails 008407`, `XionRecipeLeatherVatyrPelt`, `XionRecipeLeatherSteppecrusherHide2` |

Recall from CLAUDE.md that `05AD9D:Skyrim.esm` is `IngotShadowsteel` (Enderal's ebony rename); EGO's
dismantle outputs use that and moonstone as the two silver/high tiers.

## Alchemy and consumables

**[author]** *"35 new Potions/Poisons and rebalanced the others."*

**Mechanism [verified].** 252 ALCH overrides (161 change `Effects` **and** `Value`, 89 change
`Weight`) plus **44 new** ingestibles, and 114 INGR overrides of which **113 change `Effects`**.

`XionAlchemySpecificTweaks 001D4B` reweights `ModAlchemyEffectiveness` by effect keyword:

| Effect keyword | Multiplier |
|---|---|
| `MagicAlchResistPoison/Fire/Frost/Shock/Magic` (`10EB5F`, `065A37`–`065A3A`) | **×2.25** |
| EGO's `XionRestStam 001D0F` | ×1.334 |
| EGO's `XionRestHealth 001D0D` / `XionRestMana 001D0E` / `XionRestStam` | ×1.0 |
| `_00E_Theriantrophist_ChymikumEffect 02EA99:FS.esm` | ×1.1 |
| `MagicParalysis 01EA70` | **×0.7** |

`XionAlchemyTweak 001CC7` is a global `ModAlchemyEffectiveness ×1` — a neutral tuning hook.

Four new consumable keywords classify the results: `XionFood 001D11`, `XionElixir 001F16`,
`XionAmbrosia 002C9C`, `XionPoison 001EA1`, alongside the three restore-type keywords above.
`XionGeisterflucht 001D3D` ("Ghost Curse") is the consumable that unlocks full damage against ghosts
— see [`combat-and-damage.md`](combat-and-damage.md#silver-ghosts-and-undead).

Arcane Fever tuning lives in the scripts, not the plugin: the apparition alias scripts move tier-I
fever 7 % → 8 % and tier-III 5 % → 4 %, and zero out the class modifiers. See
[`scripts.md`](scripts.md).

## Vendor lists

**126 leveled-item lists are overridden** and 135 new ones added. The overrides include **every**
Enderal trader list **[verified]**:

```
_00ETraderCraftingPlansA 137A06   _00ETraderCraftingPlansB 148ABD   _00ETraderCraftingPlansC 148ABE
_00ETraderCraftingIngredientsA    _00ETraderPotionA/B/C/D            _00ETraderMagicBasics
_00ETraderMagicJewelry (injected) _00ETraderSmithingLVL6/LVL10       _00ETraderWeapArmA/B
_00ETraderWeapArmCSilverSteel     _00ETraderWeapArmDStarling         _00ETraderSpellBooksLevelA–D
_00ETraderAmmounused
```

plus the loot families `01E_*`/`02E_*`/`03E_*`/`04E_*` (Beute, Traenke, Zutaten, Kampfitems,
Schmuckstck, Edelsteine, Clutter, Gold, Rucksack, Wardrobe, Sack, Sargitems), all the
`DeathItem*` lists, the FS forbidden lists and the spell-book loot lists.

> **This is the concrete collision for a new-gear patch.** `Zenderal - Relentless Sword.esp` puts
> its blueprint in `_00ETraderCraftingPlansC 148ABE` (CLAUDE.md). EGO **rewrites that record
> wholesale** — it sets `ChanceNone: 0.4` (Enderal had none) and drops every entry's `Level` from
> 19 to **1**, while adding roughly twenty more plans **[verified]**. Level-gating of blueprint
> vendors is gone. A patch that loads after EGO and carries Enderal's version of the list reverts all
> of that; a patch that loads *before* EGO is simply overwritten. The only correct move is a patch
> that loads **after EGO** and is built from **EGO's** copy of the list.

Faction-side, 11 `VendorBuySellList` FormLists are re-pointed
(`Merchant_Flusshaim_Ester`, `FS_Merchant_Wildmage_*`, `UC_Zorkban`, `UC_Barnabas`,
`UCHehler01/02`, `AlethorVendorFac`, `_00E_FS_Undercity_MerchantBashHoleFaction`) so the new
"forbidden" lists take effect.

## Prices, respawn and the bank

| Setting | Enderal | EGO | Effect |
|---|---|---|---|
| `fBarterMin` | 1.75 | **2.3** | you pay more |
| `fBarterMax` | 2.85 | **3.3** | |
| `XionEconomy 001D4A` → `ModSellPrices` | — | **×0.88** | you receive less |
| `XionEconomy` → `ModBuyPrices` | — | **×1.15** vs vendors with `XionNoble 001F71` | noble merchants gouge |
| `iDaysToRespawnVendor` | 2 | **5** | vendor stock refreshes less often |
| `iHoursToRespawnCell` | 124 | **360** | cells (and their loot) respawn far less often |
| `fLevelUpCarryWeightMod` | 5 | **0** | levelling no longer grants carry weight |

**The bank's compound interest is flattened.** Enderal's `_00E_A0_BankSystemQuest` scales
`ZinsPercent` across ten brackets from 0.3 % (< 100 gold) to 2.8 % (≥ 1000 gold). EGO's recompiled
`.pex` keeps only two branches **[verified]**:

```papyrus
if Deposited < 100.0
    ZinsPercent = 0.3
elseIf Deposited >= 100.0
    ZinsPercent = 1.0
endIf
```

The 250-gold-per-day cap is unchanged. See [`scripts.md`](scripts.md#_00e_a0_banksystemquest).

## Crime and stealth

**[author]** *"Rebalanced stealth/pickpocketing/lockpicking and overall made harder."*

EGO authors **seven new crime GMST records** and overrides two more **[verified]**:

| GMST | Value | Note |
|---|---|---|
| `iCrimeGoldMurder 01DCFA` | 7500 | new record |
| `iCrimeGoldEscape 01DCFC` | 500 | new record |
| `iCrimeGoldAttack 01DCFB` | 300 | new record |
| `iCrimeGoldPickpocket 01DCFD` | 125 | new record |
| `iCrimeGoldTrespass 01DCFE` | 50 | new record |
| `iCrimeAlarmRecDistance 0058FE` | 2000 | new record |
| `iCrimeAlarmLowRecDistance 0058FF` | 1000 | new record |
| `iCrimeGoldStealHorse` | 100 → **1000** | override |
| `iCrimeGoldWerewolf` | 1000 → **7500** | override |

Four crime factions (`D_CrimeFaction 02E9AD`, `FL_CrimeFaction 07286C`, `A_CrimeFaction 08D90C`,
`UCCrimeFaction 137A04`) have their `CrimeValues`, `Ranks` and flags rewritten to match.

Stealth is retuned hard:

| GMST | Enderal | EGO |
|---|---|---|
| `fCombatStealthPointDrainMult` | 3 | **12** |
| `fCombatStealthPointRegenAttackedWaitTime` | 15 | **120** |
| `fCombatStealthPointRegenDetectedEventWaitTime` | 10 | **60** |
| new `fCombatStealthPointRegenAlertWaitTime 007EA6` | — | 30 |
| new `fCombatStealthPointRegenLostWaitTime 007EA7` | — | 30 |
| `fSneakBaseValue` | −19 | **−13** |
| `fSneakLightMult` | 0.3 | **1.0** |
| `fSneakLightExteriorMult` | 0.5 | **1.0** |
| `fDetectionSneakLightMod` | 18 | **8.5** |
| `fSneakExteriorDistanceMult` | 2.1 | **1.2** |
| `fSneakSoundsMult` | 1 | **1.2** |
| `fSneakSleepBonus` | 0 | **−0.2** |
| new `fSneakEquippedWeightBase 007EA2` / `…Mult 007EA3` | — | 5 / 1 |
| new `fSneakDistanceAttenuationExponent 000803` | — | 3 |
| `fPickPocketActorSkillBase` | 20 | **5** |
| `fPickPocketMaxChance` | 90 | **100** |
| `fPickPocketAmountMult` | −0.1 | −0.11 |

Light now matters at full strength (`fSneakLightMult` 0.3 → 1.0) while distance matters much less
outdoors — a deliberate shift from "crouch anywhere in daylight" to "stay out of the light".
