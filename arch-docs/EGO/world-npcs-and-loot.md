# EGO — NPCs, the world and loot

## NPC records

**1118 NPC records: 1106 overrides + 12 new.** **[verified]** What EGO changes, by frequency:

| Field | Records | What it is |
|---|---|---|
| `IsCompressed` / `MajorRecordFlagsRaw` | 1095 | EGO compresses almost every NPC record (cosmetic; Spriggit round-trips it) |
| `Name` | 940 | localisation stripped — see [`plugin-anatomy.md`](plugin-anatomy.md#localisation-is-stripped) |
| `Configuration` | 896 | health/magicka/stamina offsets, level, speed multiplier |
| `Items` | 732 | inventory / equipped gear |
| `Perks` | 666 | **the combat rework** — see below |
| `PlayerSkills` | 457 | per-skill values |
| `AIData` | 370 | aggression, confidence, morality, assistance |
| `EditorID` | 326 | renames (mostly `_01E_` → `_02E_` tier retags) |
| `ActorEffect` | 318 | ability spells |
| `Attacks` | 300 | attack data — "many enemies have slightly different attack patterns" |
| `FaceMorph` | 166 | |
| `VirtualMachineAdapter` | 165 | script property re-binding |
| `CombatStyle` | 157 | which of the 59 reworked styles an actor uses |
| `Keywords` | 119 | EGO's immunity/classification keywords |
| `DeathItem` | 95 | **loot** — see below |
| `AttackRace` | 65, `Height` 60, `DefaultOutfit` 47, `Factions` 27, `Race` 17, `WornArmor` 8, `Class` 8 | |

The perk grants are the mechanism behind the whole difficulty rework; the counts are in
[`combat-and-damage.md`](combat-and-damage.md#how-the-rules-reach-the-player).

The **12 new NPCs** are all summonable/ambush actors backing the new conjuration spells:
`_05E_SkelettSummon_NPC`, `_10E_SkelettAmbush`, `_10E_SkelettBogenAmbush`,
`_10E_SkelettSummonKrustis`, `_10E_SummonGeisterschwarzbaer_NPC`,
`_15E_SummonableFrostElemental_NPC`, `_15E_SummonableMudElemental_NPC`,
`_15E_SummonableSoilElemental_NPC`, `_25E_SummonableElementalWolf_NPC`,
`_45E_SummonableFrostEleDarkhand`, `XionSummonedVatyr`, `XionIllu2`.

One new Race (`TyargeRace 001D98`) and one new Class (`CombatMageAlteration 001D8D`) support them;
14 new Outfits cover the seven Dragon Priest sets plus bandit/NPC-specific kits.

## Cells and worldspaces

**[verified]** EGO touches:

- **125 interior cells** — one `RecordData.yaml` each, carrying `Name`, `Persistent` and
  `Temporary` ref lists.
- **10 worldspaces** — `Vyn 001D3C`, `Akropolis`, `CapitalCityCastleWorld`, `CapitalCityMarketArea`,
  `CapitalCityStrangerArea`, `CapitalCityUpperCity`, `CapitalCityUpperTemple`, `MQ07aDreamRealm`,
  `MQP03Temple`, `PresentationDungeon` — plus **126 exterior cells** under them.
- **433 placed references** total: 394 `PlacedObject` + 39 `PlacedNpc` **[verified]**.

> **EGO carries no navmesh at all.** Of the 140 cell records it overrides where the master has a
> `NavigationMeshes:` block, **140 ship that block empty and 0 carry NAVM data**. **[verified]** That
> is exactly the pattern CLAUDE.md prescribes for our own cell edits — EGO gets this right, so a
> Zenderal patch never has to reconcile EGO navmeshes.
>
> It does carry `Landscape` on 66 exterior cells and `Regions` on 41, which are ordinary CK
> by-products of editing an exterior cell. Treat them as EGO's, not as something to forward.

### How the secure chests were removed

**[author]** *"Removed Secure Chests and replaced them with 3 safe chests in locations where they
made sense."*

**Mechanism [verified].** Two moves, both done on the placed reference rather than the base object:

1. **Re-base.** Existing `_00E_Camp_SecureChest 02EDD7` refs are re-pointed to EGO's new
   `XionSecureChest 001E73` (6 refs) — e.g. in `CapitalCityPlayerhouse`, `FlusshaimHousePhasmalism`,
   `CapitalCityPlayerHouseUpper`.
2. **Permanently disable.** The rest get `MajorRecordFlagsRaw: 2048` (Initially Disabled) plus an
   enable parent of **`PlayerRef 000014` with `SetEnableStateToOppositeOfParent`**. The player is
   always enabled, so the chest is always disabled. This is a clean, save-safe way to delete a
   placed object without setting the Deleted flag.

If a Zenderal patch ever wants a container back, copy that ref and clear `EnableParent` — do not
resurrect the base object, and do not delete the ref.

### Other world edits

The most-placed base objects across those 433 refs **[verified]** are ammunition and consumables
being scattered into the world:

| Base | Refs |
|---|---|
| `_00E_ForgottenTempleKey_01 0479FF` | 24 |
| `_30E_AeternaArrow 13E219` | 23 |
| `_00E_Camp_SecureChest 02EDD7` | 15 |
| `_20E_StarlingArrow 10A86E`, `_25E_ArrowOfTheRighteousPath 1337DB` | 14 each |
| `_02E_Coastprawler 047C3C` (an NPC) | 14 |
| `XionSilverArrow 001D03` (new) | 11 |
| `01E_Genesungstrank 0028C8`, `_01E_01_OldIronArrow 0028B0` | 10 each |
| `XionGeisterflucht 001D3D` (Ghost Curse, new) | 7 |
| `XionSecureChest 001E73` (new) | 6 |

Seven new containers back this up: `XionSecureChest`, `XionDwemerDresserArrows`,
`01E_ChestSmall02Beute01MittelGhostCurse`, `_00E_ScrollStack_LowerLevel` and three Undercity
wardrobes/dressers.

## Loot

**126 leveled-item lists overridden, 135 new.** The overrides change `Entries` (102) and
`ChanceNone` (86) **[verified]**, i.e. both what drops and how often nothing drops.

**[author]** *"Loot is much more diverse. Animals/Creatures will drop appropriate items."*
The mechanism is the `DeathItem*` family — 24 overridden (`DeathItemBear`, `…BearCave`, `…BearSnow`,
`…Cow`, `…DeerNew`, `…Dragon01`, `…DwarvenCenturion/Sphere/Spider`, `…FrostbiteSpiderMother`,
`…Ghost`, `…Goat`, `…Horker`, `…Horse`, `…Mammoth`, `…MudCrab01`, `…Pig`, `…Sabrecat`,
`…Slaughterfish`, `…Spriggan`, `…StormAtronach`, `…Tyarge`, `DeathItem_Human`,
`_00E_FS_DeathItemLostOneGiant`, `_00E_WolfDeathItem`) — six of which are *injected*, i.e. EGO
creates a `DeathItem` list at a `Skyrim.esm` FormID that base Enderal never used
(`DeathItemChaurusXion 03ADA1`, `DeathItemChaurusEggs25 03ADA2`, `DeathItemDragon01 03ADA5`,
`DeathItemDwarvenSphere 03AD82`, `DeathItemDwarvenSpider 03AD83`,
`DeathItemFrostbiteSpiderMother 03AD89`).

New drops such as `XionVatyrPelt 00082D`, `XionPriseSalz 000831`,
`XionFrostbiteVenomMother 000833`, `XionDeathItemVatyr 00082F` and
`XionDeathItemSpiderEggs65 000832` feed the new recipes described in
[`crafting-alchemy-economy.md`](crafting-alchemy-economy.md).

Container contents are rewritten too: **319 Container overrides, 295 of which change `Items`.**

## Loading-screen hints

**[author]** *"Many hints that had unimmersive or simply too much information were removed."*

**Mechanism [verified].** 36 LoadScreen overrides. Hints are not deleted — they are:

1. **Renamed with an `X_` prefix** (`X_00E_FS_Gameplay_HiddenTalents`,
   `X_00E_FS_Gameplay_Theriantrophist_01/03/04`, …) and
2. given **`GetInCell` conditions** naming cells the player will not be in, so they never display.

Others are *rewritten* to teach EGO's own mechanics — the renames go the other way for
`_00E_Gameplay_LightArmorScaling`, `_00E_Gameplay_StaggerResistances`,
`_00E_Gameplay_ManacostScaling`, `_00E_Gameplay_ResistanceImmunity`, `_00E_Gameplay_ShieldArrows`.

## A known defect worth patching

**72 string fields where EGO's single English `Value:` holds the base record's *German* text.**
**[verified]** — a side effect of collapsing the localised `Values:` list and picking the wrong
entry. 49 are merchant-container names the player never sees; **23 are player-facing**:

| Type | Records |
|---|---|
| Perks (11 fields) | `_00E_Class_Infiltrator_P03_C_Assassin`, `_00E_Class_Infiltrator_P07_Bloodlust`, `_00E_Class_Phasmalist_P04_C_Sage_01/02/03`, `_00E_Class_Vagrant_P02_OintmentLore_02`, `_00E_Class_Vagrant_P09_HighDexterity` |
| Messages (4) | `_00E_Message_Phasmalist_P03/P04c/P09`, `_00E_Message_Theriantrophist_P01_StrongBlood` |
| LoadScreens (4) | the four `X_`-disabled hints above (invisible in play, but still wrong) |
| Races (2), MagicEffects (1), Shouts (1) | |

That is a small, self-contained, verifiable bugfix — a good candidate for a Zenderal
`Zenderal - EGO Fixes.esp`. Regenerate the list any time with the scan in
[`patching-ego.md`](patching-ego.md#finding-the-german-text-defects).
