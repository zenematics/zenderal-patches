# EGO — Enderal SE: Gameplay Overhaul

Reference documentation for **`Enderal SE - Gameplay Overhaul.esp`** ("EGO"), the mod Zenderal
builds its combat pillar on. Everything here was read off the plugin serialized to Spriggit YAML and
off the loose scripts it ships — not from the Nexus page. Facts marked **[verified]** were measured
against this machine's copy on **2026-08-04**; the mod's own claims are quoted as **[author]** and
are not the same thing.

> **Why this exists.** EGO overrides **6203** existing records. Zenderal patches that touch combat,
> loot, crafting, spells or NPCs will land on top of it constantly, and CLAUDE.md guardrail 5 — *a
> patch's job is to forward, not to author* — is impossible to honour against a mod this size
> without knowing exactly what it changed. Read [`patching-ego.md`](patching-ego.md) before writing
> any patch that could conflict.

## The documents

| Read | For |
|---|---|
| [`plugin-anatomy.md`](plugin-anatomy.md) | Header, masters, FormID blocks, injected records, the localisation problem, shipped assets. **Start here.** |
| [`combat-and-damage.md`](combat-and-damage.md) | The stamina/damage/armour/stagger rework, weapon-type matrix, creature resistances, GMSTs, combat styles |
| [`magic-and-talents.md`](magic-and-talents.md) | Mana-cost architecture, skill scaling, the 26 new spells, talent-tree perk overrides |
| [`crafting-alchemy-economy.md`](crafting-alchemy-economy.md) | 727 recipes, potions/ingredients, vendor lists, prices, crime, the bank |
| [`world-npcs-and-loot.md`](world-npcs-and-loot.md) | 1118 NPC records, cells and worldspaces, secure chests, loot lists, containers |
| [`scripts.md`](scripts.md) | The 7 loose `.pex` EGO ships and exactly what each one changes |
| [`patching-ego.md`](patching-ego.md) | **The practical guide** — load order, conflict surface, and rules for writing Zenderal patches against EGO |
| [`conflict-index.md`](conflict-index.md) | *Generated.* Every one of the 6203 overridden records, by type |
| [`new-records.md`](new-records.md) | *Generated.* Every one of the 974 new records, by FormID |

## What EGO is

A single-plugin, whole-game gameplay overhaul for Enderal SE by **Ixion XVII (aka Reltilie)**,
in development since 2016 (EGO 1.00, July 2016). The copy documented here:

| | |
|---|---|
| Plugin | `Enderal SE - Gameplay Overhaul.esp`, 3 043 237 bytes **[verified]** |
| Version | `1.93.1.0` (Nexus file `Enderal SE - Gameplay Overhaul-3-1-93-1-1775492797.rar`) **[verified from `meta.ini`]** |
| Nexus | Enderal SE mod **3** |
| Author (TES4 CNAM) | `Ixion XVII aka Reltilie` **[verified]** |
| Masters | `Skyrim.esm`, `Update.esm`, `Enderal - Forgotten Stories.esm` **[verified]** |
| Flags | none — **not ESM, not ESL, not localized** **[verified]** |
| Records | **7177** total = 6203 overrides + 974 new **[verified]** |
| Supported game | "Only supports Enderal SE 2.0.12" **[author]** — matches this machine's 2.0.12.4 |
| Also ships | 7 loose `.pex`, 14 loose `.psc`, and `Enderal SE - Gameplay Overhaul.ini` |

The author's own load-order guidance is: **Bug Fixes → other mods → EGO → EGO patches → exceptions
like DynDOLOD** **[author]**, and *"this is a complete overhaul of the game and as such most mods
will cause conflicts"* **[author]**. Zenderal's own patches belong in the "EGO patches" slot,
**after** EGO.

## Where the source material lives

Both trees are gitignored — regenerate them locally, never commit them.

| Path | What | How to rebuild |
|---|---|---|
| `reference/mods/EGO/esp/` | EGO serialized to Spriggit YAML (~29 MB, 7328 files) | `/spriggit-serialize` style call against the mod's `.esp`, `--GameRelease EnderalSE` |
| `reference/mods/EGO/scripts/` | The mod's loose `scripts/` folder, verbatim (7 `.pex` + `source/`) | copy from the MO2 mod folder |
| `reference/mods/EGO/*.ini` | `Enderal SE - Gameplay Overhaul.ini` and MO2's `meta.ini` | copy from the MO2 mod folder |

Source mod folder on this machine: `C:/modding/modlists/thepath/mods/EGO SE - Enderal Gameplay Overhaul`.

The exact serialize command used:

```powershell
. ".claude/config/tools.ps1"
& (Assert-Tool $Tools.spriggitCli 'spriggitCli') serialize `
  --InputPath  "<modfolder>/Enderal SE - Gameplay Overhaul.esp" `
  --OutputPath "./reference/mods/EGO/esp" `
  --GameRelease $Tools.spriggit.gameRelease `
  --PackageName $Tools.spriggit.packageName `
  --PackageVersion $Tools.spriggit.packageVersion
```

It round-trips cleanly under Spriggit **0.40.0** — the CLI's built-in correctness check rebuilt the
plugin from the YAML without error. **[verified]** EGO's leveled lists contain **no** COED owner
ExtraData, so the 0.41.0 leveled-list corruption described in CLAUDE.md does not apply to this
tree. **[verified]**

## Regenerating the appendices

`conflict-index.md` and `new-records.md` are generated. After re-serializing, run:

```bash
python arch-docs/EGO/tools/ego_report.py index
python arch-docs/EGO/tools/ego_report.py appendices
```

The same script answers ad-hoc questions while patching:

```bash
python arch-docs/EGO/tools/ego_report.py fields Weapons   # which fields EGO changes on WEAP
python arch-docs/EGO/tools/ego_report.py diff 148ABE      # base -> EGO diff for one record
```

## The five things to remember

1. **EGO is not localized.** Every string on every record it overrides collapses to English only.
   See [`plugin-anatomy.md`](plugin-anatomy.md#localisation-is-stripped).
2. **The Player NPC record is the delivery mechanism.** EGO's whole player-facing ruleset is 42
   perks bolted onto `Player 000007:Skyrim.esm`. Overriding that record without forwarding them
   silently deletes the mod. See [`combat-and-damage.md`](combat-and-damage.md#how-the-rules-reach-the-player).
3. **61 records are injected**, not overridden — FormIDs in `Skyrim.esm`'s space that `Skyrim.esm`
   does not define. See [`plugin-anatomy.md`](plugin-anatomy.md#injected-records).
4. **EGO rewrites the vendor and loot leveled lists**, including all three blueprint lists
   (`_00ETraderCraftingPlansA/B/C`) — the exact lists a new-weapon patch needs.
   See [`crafting-alchemy-economy.md`](crafting-alchemy-economy.md#vendor-lists).
5. **It ships 7 loose `.pex` that override Enderal's own scripts.** Those conflicts are resolved by
   MO2 file order, not plugin order, and are invisible in xEdit.
   See [`scripts.md`](scripts.md).
