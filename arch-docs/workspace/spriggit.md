# Spriggit in this workspace

How the Spriggit/Mutagen toolchain behaves against Enderal SE, and the YAML-level traps that build clean and do nothing.

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

## Why `EnderalSE` and not `SkyrimSE`

`GameRelease.EnderalSE` is a real Mutagen release (value `6`), and `GameCategory.cs` maps
`GameRelease.EnderalSE => GameCategory.Skyrim`, which is why the **Skyrim** serializer package
still handles it. **[upstream]** What differs is the implicit **base-master set**:

```csharp
// Mutagen.Bethesda.Core/Plugins/Implicit/Implicits.cs
EnderalSE = SkyrimSE with { BaseMasters = new ImplicitModKeyCollection(SkyrimSE.Listings.And(enderal)) };
//   where enderal = ModKey.FromFileName("Enderal - Forgotten Stories.esm")
```

So under `EnderalSE`, `Enderal - Forgotten Stories.esm` is treated as an implicit base master
alongside the five Bethesda ones. Under `SkyrimSE` it is not, and a patch that overrides Enderal
records is handled as though it depended on an ordinary third-party mod. **Keep
`.spriggit`, `spriggit-meta.json` and `tools.json`'s `spriggit.gameRelease` all reading
`EnderalSE`.**

Mutagen also resolves the load order from `%LOCALAPPDATA%\Enderal Special Edition\plugins.txt` for
this release **[upstream]**, which is the correct file on this machine **[verified]**.

**`--GameRelease EnderalSE` is confirmed working end to end with Spriggit CLI 0.40.0. [verified]**
Every plugin in `reference/base/` was serialized with it; the CLI picks up the repo-root `.spriggit`
(`Release = EnderalSE`), resolves the `Spriggit.Yaml.Skyrim.0.40.0` entry point, and its built-in
correctness check round-trips the result back to a plugin. The three-tree import order is likewise
confirmed by compiling real Enderal scripts (`_00E_TalentLibrary`, `_00E_Game_TalentControlSC`,
`dgintimidateplayerscript`) clean against `reference/base`. **[verified]**

> **Why Spriggit 0.40.0 is pinned.** Spriggit **0.41.0 silently corrupts leveled-list entries that
> carry COED owner ExtraData**, verified 2026-07-31 and reverted. Its deserializer throws a
> `NullReferenceException` on the 0.40 shape (`MutagenObjectType: NoOwner` + `RawOwnerData`), and its
> serializer rewrites that as `UntypedOwner` + FormKeys while **dropping the next entry's `Data:`
> block** — an entry vanishes from the built plugin with no error. There is no YAML workaround: the
> `0xFFFFFFFF` "no variable" sentinel cannot survive FormKey encoding and returns as `0x04FFFFFF`, so
> even a hand-corrected record builds a different plugin.
>
> This bites Zenderal specifically: **loot/vendor patches are exactly the leveled-list-heavy records
> that trip it.** Before ever unpinning: confirm the bug is fixed upstream, grep the tracked YAML for
> `MutagenObjectType: (No|Untyped|Typed)Owner` and `RawOwnerData`, and prove the upgrade by
> rebuilding every `.esp` and comparing SHA-256 against the previous release's. A clean build on a
> repo with no such record proves nothing. 0.41.0 also requires the **.NET 10 SDK** (its serializer
> package ships `tools/net10.0` only), failing with a `DotnetToolSettings.xml was not found` error
> that never mentions .NET.

## What's in `reference/base/` (built 2026-08-01, ~0.9 GB, gitignored)

Regenerate any of these with `/spriggit-decompile-reference`; the script trees are plain unzips.
**Grep these instead of guessing a FormKey or a script signature.**

| Folder | Source | Contents |
|---|---|---|
| `Skyrim/` | `Skyrim.esm` | **87322 records — this is BASE ENDERAL, not vanilla Skyrim.** Start here for base-game content |
| `EnderalFS/` | `Enderal - Forgotten Stories.esm` | 14061 records across 86 types — the FS expansion, overriding the above |
| `Update/` | `Update.esm` | 404 records |
| `SkyUI_SE/` | `SkyUI_SE.esp` | 8 records (SkyUI is built into Enderal) |
| `Dawnguard-stub/`, `Dragonborn-stub/`, `HearthFires-stub/` | the DLC ESMs | **1–2 records each — they are empty stubs** (see below) |
| `EnderalScripts/source/scripts/` | `ScriptsEnderal.zip` | **5029 real `.psc`** from SureAI — not decompiles |
| `SKSEScripts/` | `Data/Source/Scripts` | 74 SKSE-extended vanilla types |
| `VanillaScripts/Source/Scripts/` | Skyrim SE `Scripts.zip` | 14301 `.psc` **plus `TESV_Papyrus_Flags.flg`** |

`tools.json`'s `papyrusSource` points at the three script trees here, so the compiler and the
lookup copies are the same files — there is no second copy to drift.

> **`reference/base/Skyrim/` is lookup-only and cannot be rebuilt.** Spriggit 0.40.0 serializes it
> fine but **fails its own round-trip check**: `Skyrim.esm`'s NavigationMeshInfoMap (NAVI) record has
> a **null FormKey**, so Spriggit writes it as `NavigationMeshInfoMaps/Null.yaml` with no `FormKey:`
> line, then on read-back parses the next line as the FormKey and throws
> `Malformed FormKey string: 89103`. **[verified]** The serialized tree is complete and correct for
> grepping — we never deserialize a reference tree — so this is a caveat, not a problem.
>
> **Enderal's own NAVI record is unaffected**: it has a real FormKey
> (`000802:Enderal - Forgotten Stories.esm`) and `EnderalFS/` passed its round-trip check. **[verified]**
> That matters because it means navmesh-adjacent bugfix patches on Enderal *are* buildable. Only the
> null-FormKey case breaks, and only in `Skyrim.esm`.

> **`Enderal - Forgotten Stories.esm` survives as a declared master.** It is an *implicit* base
> master under `GameRelease.EnderalSE`, so there was reason to fear Mutagen would drop it from the
> written master list and leave `:Enderal - Forgotten Stories.esm` FormKeys dangling. It does not:
> `Zenderal - Relentless Sword.esp` builds with `MAST Skyrim.esm` + `MAST Enderal - Forgotten
> Stories.esm`, and its `02F336` references resolve at master index **1**. **[verified]** So a patch
> may reference FS records freely — just declare the master and confirm it in the built header.

## YAML and cell-record gotchas

- **Placed references live inside the cell's single `RecordData.yaml`, not in per-ref files.**
  Interior cells serialize to one file (`Cells/<block>/<sub>/<EditorID> - <hex>_<master>/RecordData.yaml`)
  holding the cell record, its `NavigationMeshes:`, then `Persistent:` and `Temporary:` lists.
  Exterior refs are under `Worldspaces/`. **[verified]** A `find` that turns up only `RecordData.yaml`
  does not mean the refs are missing.
- **To add one object to an existing cell, copy the winning cell record and give it a one-entry
  child group.** **[verified]** — this is exactly what FS does to `FlusshaimTemple`, and what
  `Zenderal - Relentless Sword.esp` now does. Three rules learned building it:
  1. Copy the cell from the **winning** plugin, not from `Skyrim/`. FS overrides many cells and
     changes their data (for `FlusshaimTemple` it rewrites the `Name` from 3 localisations to 10) —
     copying base Enderal's version silently reverts that. Guardrail 5 applies to cells too.
  2. **Delete the `NavigationMeshes:` block.** Those are full NAVM record overrides carrying vertex
     and grid data; carrying them means overriding Enderal's navmesh for no reason.
  3. List **only** your new ref under `Temporary:`. Refs are independent records — omitting the
     hundreds you aren't touching does not remove them, and re-listing them invites conflicts.

  Spriggit 0.40.0 round-trips this correctly, emitting the canonical
  `GRUP CELL → block → sub-block → CELL → GRUP cellchildren → GRUP celltemp → REFR` nesting, and a
  new `REFR` in an ESL-flagged plugin keeps the flag. **[verified]**
- **Placing a ref in an EXTERIOR cell needs three scaffolding files, or Spriggit silently drops the
  whole tree.** **[verified 2026-08-03]** An interior cell is one `RecordData.yaml` (see above), but
  a worldspace cell will not build from the cell file alone — the plugin comes out with **zero**
  `WRLD`/`CELL`/`REFR` records, no error, no warning. The build succeeds and the ref simply is not
  there. Four files are required:

  ```
  Worldspaces/<WS EditorID> - <hex>_<master>/RecordData.yaml   # the WRLD record itself
  Worldspaces/<WS…>/<blockX, blockY>/GroupRecordData.yaml      # GroupType: ExteriorCellBlock
  Worldspaces/<WS…>/<blockX, blockY>/<subX, subY>/GroupRecordData.yaml  # ExteriorCellSubBlock
  Worldspaces/<WS…>/<blockX, blockY>/<subX, subY>/<cell>/RecordData.yaml
  ```

  Folder names are `<X>, <Y>`; block = `floor(coord/32)`, sub-block = `floor(coord/8)`. Inside the
  `GroupRecordData.yaml` the fields are `BlockNumberY` **then** `BlockNumberX` plus `GroupType`, and
  a zero is **omitted** (Spriggit drops defaults) — so folder `0, -1` yields only `BlockNumberY: -1`.
  A cell with no EditorID gets a folder of just `<hex>_<master>` with no `" - "` prefix.

  **Truncate the WRLD record before its `TopCell:` block** unless you actually mean to override the
  worldspace's persistent cell. Copying the master's record whole drags in every persistent ref
  (Ark's market is ~40 of them) as an override you then have to be right about. Header-only builds
  fine and keeps the conflict surface to the WRLD fields. Copy the file and cut it with a script —
  do not retype it (guardrail 4).

- **A `PlacedObject`'s record flags are raw, not named.** **[verified 2026-10-18]** `MajorFlags: [DoNotHavokSettle]`
  works on a `PlacedNpc` but is **silently dropped** on a `PlacedObject` (built REFR flags = 0). Write the
  raw form right after `FormKey:`, as Spriggit itself serializes it:
  `MajorRecordFlagsRaw: 536870912` plus `SkyrimMajorRecordFlags: [0x20000000]` (Don't Havok Settle).
  Check the built REFR's header flags, not the YAML.
- **YAML comments do not survive a re-serialize.** Spriggit rewrites the folder from the binary
  plugin, so any `#` comment you add to a record file is lost the next time anyone runs
  `/spriggit-serialize`. Put durable explanation in `arch-docs/`, not in the record YAML.
