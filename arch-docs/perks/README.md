# Memory-Point perks dataset

[`perks.json`](perks.json) lists **every perk and talent the player can buy with Memory Points in
the meditation space**, using the load-order-WINNING records of the installed Zenderal list.

Regenerate after any modlist change:

```powershell
powershell -NoProfile -File arch-docs/perks/Run-PerkExtract.ps1
```

It runs the read-only `MagicExtract` tool in `--perks` mode (`arch-docs/magic/tools/MagicExtract/PerkExtract.cs`),
so the same load-order, BEES and strings checks apply. See [`../magic/README.md`](../magic/README.md).

## Where the data comes from **[verified]**

The memory trees are **not** the vanilla perk constellation: every AVIF `PerkTree` in Enderal is
empty. The meditation power (`_00E_Class_OpenClassMenuScript`) teleports the player into cell
`ClassMenue 0A7FBC:Skyrim.esm` (worldspace `Akropolis`). There, every "memory star" is a placed
reference carrying `_00E_Class_PerkScript`. The extractor follows each star like this:

| Step | Record | What it gives |
|---|---|---|
| star REFR + its base Activator | script properties (`Flags: Inherited`: base props apply unless the ref overrides them) | the 1–3 rank perks, talent Shout + Words, `AdditionalPerk`, quest, cooldowns |
| `__Config_DisplayMessage` | MESG | title, description, **buttons whose conditions are the real purchase gate** |
| button conditions | `HasPerk == 1` / `GetGlobalValue TalentPoints >= 1` | prerequisites + Memory Point cost per rank |
| the 11 `*Perks` FormLists | FLST (winning) | which tree a star belongs to, and whether a rank **counts toward tree points/affinities** |

Button index maps onto the rank exactly as `_00E_Class_PerkScript.OnActivate` does: single stars
unlock on button 0, ranked perks and talents on buttons 0–1 or 0–2. The rest are info/back buttons.

## Schema (per entry in `perks[]`)

| Field | Meaning |
|---|---|
| `name` / `nameInBaseEnderal` | winning Message title; base Enderal's title when a later plugin changed it |
| `tree` / `treeSource` | tree code (`Bastion` … `Theriantrophist`, or `root`); `perkFormList` or `editorIdFallback` |
| `kind` / `ranks` | `perk`, `rankedPerk` or `talent`; number of Memory Points to max it |
| `description` | the winning Message text (what the player reads), tier lines included |
| `prerequisites` | rank-1 requirements on perks outside the star (`allOf` / `anyOf` groups) |
| `rankDetails[]` | per rank: `perk` (winning PERK + provenance), `memoryPointCost`, `requiresAllOf`, `requiresAnyOf`, `otherConditions`, **`inTreeFormList`** |
| `talent` | Shout, its three Words, recovery times (record and script overrides) |
| `messageButtons[]` | raw button text + conditions, for anything the parsed fields miss |
| `star` | ref FormKey, base Activator, cell, position (enough to redraw the constellation), provenance |

`inertStars[]` holds refs that carry the script with no properties on either the ref or its base.
They show no message box and teach nothing. `treePerksWithNoStar[]` holds tree perks that no star
teaches; it is empty in the current list.

## What the current list says (profile `Alpha 0.5`, 2026-10-13)

- **170 stars, 263 ranks** = 263 Memory Points to buy everything. That is 28 talents (3 of them the class
  roots), 30 ranked perks and 112 single perks, across the 11 trees plus `root`.
- Ranks reconcile exactly with every tree's winning FormList, with three exceptions (`inTreeFormList: false`):
  - **Root talents** (Focus / Tempest / Assassination, 9 ranks). They are in no tree, so they count toward no tree and unlock no affinity.
  - **Phasmalist: Arcane Disassembling** (`02F130:Enderal - Forgotten Stories.esm`). FS never added its perk to `FS_PhasmalistPerks`.
  - **Vagrant: Sensitive Tongue ranks 2–3** (`085AB0`, `0BFA3A`). Base Enderal lists them, but EGO's `VagabondPerks`
    override drops them, and `EGO SE - KataPUMB New Affinities.esp` (the winner) inherits that. Buying those two
    ranks no longer counts toward Vagrant points or affinity unlocks.
- **97 star titles are German in game.** EGO is not Localized and ships German `Name` strings on its
  Message overrides (`'Hüter: Fester Stand'` vs base `'Keeper: Firm State'`). Its descriptions are
  English. This is a candidate bugfix patch: forward base titles over EGO's messages, keeping everything else EGO's.
- `0ACAF0` and `0ACCFD` (`Skyrim.esm`) are inert, in base Enderal too.
