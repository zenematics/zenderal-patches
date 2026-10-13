# Install, engine and lookup ground truth

Facts read off the installed game. See also [`plugin-architecture.md`](plugin-architecture.md).

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

## Enderal ground truth

Everything in this section was read off the installed game, not recalled. Re-verify with the same
commands if the install moves or updates.

**Install** — Enderal SE is a *separate Steam app* with its own copy of the engine; it is not a mod
folder inside Skyrim SE. On this machine:
`C:/Gaming/steamapps/common/Enderal Special Edition` (version **2.0.12.4**). **[verified]**

**Engine / SKSE version.** The game folder ships `skse64_1_5_97.dll` — Enderal SE is pinned to
**SSE 1.5.97**, not 1.6.x. **[verified]** Every SKSE plugin (`.dll`) in the list must be a **1.5.97
(“Special Edition”, pre-AE)** build. A 1.6.640/AE build loads nothing and usually takes SKSE down
with it. This is the single most common source of "the list doesn't launch" reports.

**Masters.** `Enderal - Forgotten Stories.esm` declares exactly **two** masters — `Skyrim.esm` and
`Update.esm`. **[verified]** (Read from the TES4 header: two `MAST` subrecords, then `ONAM`. Author
`Niseam`, HEDR version 1.7, flags `0x81` = ESM + Localized.)

> **Do not master the DLC — they are empty stubs.** `Dawnguard.esm`, `HearthFires.esm` and
> `Dragonborn.esm` sit in Enderal's `Data/`, but they are **not** in `plugins.txt`, **not** mastered
> by Enderal, and **not the real DLC**: they are 44 KB, 80 bytes and 44 KB respectively, and
> serializing them yields **1–2 records each**. **[verified]** `HearthFires.esm` at 80 bytes is a
> bare TES4 header with no content at all. Enderal ships them only so the SSE engine finds the
> filenames it expects.
>
> Mutagen's *implicit* base-master list for `EnderalSE` does include them **[upstream]**, so Spriggit
> will not object if you add one. There is nothing in them to reference anyway, so don't. Compare
> `reference/base/Dawnguard-stub/` with `reference/base/EnderalFS/` if you ever doubt it.
>
> **But the engine DOES load all three stubs, always, whether or not `plugins.txt` lists them.**
> **[verified 2026-08-02]** — read straight out of a running game's plugin table via a Crash Logger
> dump on a profile that never enabled them:
>
> ```
> PLUGINS: Light: 13  Regular: 31  Total: 44
>   [ 0] Skyrim.esm   [ 1] Dawnguard.esm   [ 2] HearthFires.esm
>   [ 3] Dragonborn.esm   [ 4] Update.esm   [ 5] Enderal - Forgotten Stories.esm
> ```
>
> Corroborated independently by the plugin array inside a `.ess` save. So the older claim here — that
> a plugin mastering a DLC "fails to load" and that users must tick the stub — was **wrong**, and it
> shipped in a patch's FOMOD before anyone tested it. A third-party mod that masters `Dragonborn.esm`
> loads in Enderal with no user action at all; its references into the stub simply resolve to nothing.
> Note also that the engine's real order puts the DLC **before** `Update.esm`, which is not the order
> `loadorder.txt` shows.

**Stock load order** (`%LOCALAPPDATA%\Enderal Special Edition\plugins.txt`) **[verified]**:

```
*Enderal - Forgotten Stories.esm
*SkyUI_SE.esp
```

SkyUI is **built into Enderal**, not an add-on. Do not let the list install a second copy.

**Archives.** Enderal's own content is in `E - *.bsa`; voices in `L - Voices.bsa`; the vanilla
`Skyrim - *.bsa` are also present. **[verified]**

| Archive | Holds |
|---|---|
| `E - Meshes.bsa`, `E - Textures1.bsa`, `E - Textures2.bsa` | Enderal meshes/textures |
| `E - Misc.bsa` | interface, **scripts** and misc |
| `E - Sounds.bsa`, `L - Voices.bsa` | audio, voiced dialogue |
| `E - Update.bsa` | later-patch overrides — **loads last, so it wins** |
| `Skyrim - *.bsa` | untouched vanilla assets Enderal still uses |

**No Creation Kit and no Papyrus compiler ship with Enderal.** **[verified]** Both come from an
ordinary Skyrim SE install (`skyrimSeRoot` in `tools.json`). They are the correct tools — Enderal SE
*is* SSE — you just point them at Enderal's `Data`.

## `Skyrim.esm` is base Enderal

> **`Skyrim.esm` in Enderal's Data folder is not Skyrim — it *is* base Enderal.** **[verified]**
> Enderal ships a wholesale replacement: **191,827,554 bytes** (vs 249,753,412 for the real SSE
> file), author `mcarofano` in the TES4 `CNAM` (not Bethesda), **12,223 `_00E_`-prefixed records**,
> **no Tamriel worldspace** — Enderal's overworld is `Vyn`. All nine base memory-tree perk FormLists
> (`BastionPerks` `06686B:Skyrim.esm`, …) live in it.
>
> So the two plugins are: **`Skyrim.esm` = base Enderal** (author `mcarofano`) and
> **`Enderal - Forgotten Stories.esm` = the FS expansion** (author `Niseam`). Of the FS plugin's
> 9566 records, **28.7% (2749) carry `:Skyrim.esm` FormKeys — that is FS overriding base Enderal**,
> not touching anything of Bethesda's.
>
> Consequences: `reference/base/Skyrim/` is **Enderal content, not vanilla lookup material**; a
> `:Skyrim.esm` suffix means "base Enderal"; and a FormID copied from a Skyrim wiki will not resolve
> to the same record. The engine-hardcoded IDs (`000014` PlayerRef, `000039` GameDaysPassed,
> `000010` MapMarker) are still safe. Full detail in
> [`arch-docs/enderal/plugin-architecture.md`](../enderal/plugin-architecture.md).

## Engine-hardcoded FormKeys

These are **engine-hardcoded** FormIDs — Bethesda's own code depends on them, so Enderal's replacement
`Skyrim.esm` keeps them. They are safe to reference.

> **This table is deliberately short.** Because Enderal's `Skyrim.esm` *is* Enderal (see "Masters"
> above), an ordinary-looking vanilla FormID usually resolves to an Enderal record. Do not extend this
> table from Skyrim documentation — look the record up in `reference/base/Skyrim/` and cite the
> EditorID you actually found. Enderal's own worldspace, keyword, bench and talent FormKeys are
> documented in [`arch-docs/enderal/`](../enderal/).

| FormKey | Meaning |
|---|---|
| `000014:Skyrim.esm` | PlayerRef |
| `000038:Skyrim.esm` | GameHour global |
| `000039:Skyrim.esm` | GameDaysPassed global |
| `000010:Skyrim.esm` | MapMarker base |
| `000034:Skyrim.esm` | XMarker base |
| `10F63C:Skyrim.esm` | MapMarkerRef LocationRefType (required for discoverability) |
| `013F42:Skyrim.esm` | `RightHand` EquipType |

> Enderal's own worldspace, keywords, crafting benches and talent perks are **not** listed here on
> purpose. Look them up in a serialized copy of `Enderal - Forgotten Stories.esm` with the
> `spriggit-decompile-reference` skill and add the ones you actually use, with the EditorID you
> found them under. A constants table copied out of Skyrim documentation is worse than no table.

## Lookup gotchas

- **Before "injecting" a vanilla FormID Enderal lacks, search for it as a PLACED REFERENCE too.** **[verified 2026-10-05]** `10CED7:Skyrim.esm` (vanilla `ForceFullBodyStagger`) looked absent because a `^FormKey:` grep only finds top-level records; in Enderal it is a `PlacedObject` inside `Cells/.../QKerker - 10BBC4/RecordData.yaml` (nested as `  FormKey:`). A FACT supplied at that ID — ESL or full plugin alike — is ignored in game and collides with a live record of another type. Grep `FormKey: <id>` unanchored.
- **Enderal's cell EditorIDs are German; the display names are English.** Riverville is
  **`Flusshaim*`**, Ark is **`CapitalCity*`**, and the Sun Temple is `Suntemple*`. **[verified]**
  Searching `reference/base/*/Cells/` by the English town name returns **nothing** — grep the
  localized `String:` values instead, then read the EditorID off the match. This is also what a `coc`
  command needs: `coc FlusshaimShopSura` lands in "Riverville, Sura's Sharp Steel".

- **`E - Update.bsa` loads last and wins.** When a record or asset doesn't look like the one you
  found in `E - Meshes.bsa`, check `E - Update.bsa` before concluding your patch is wrong.
- **Don't give a patch you author a DLC master** — there is nothing in the stubs to reference. But
  the stubs *do* load (see "Masters" above), so a third-party plugin that masters one is fine and
  needs no user action. What you get is *loading*, not *working*: every FormID into a stub resolves
  to null, because the stubs hold 1–2 records between them. `Dragonborn.esm`'s single record is
  `DLC2MiraakRace` `03CA97`. **[verified]** Adding the DLC to your own master list does **not** help a
  dependent patch either — tested directly, it changes nothing. **[verified]**
  - A patch may override each record carrying a DLC reference and repoint or drop it, but weigh that
    against doing nothing: a dangling FormID is **proven harmless** here (Apocalypse ships 67 recipes
    and 144 scrolls full of them and the game runs), whereas a *null* is not automatically better.
    **Null `BNAM` on a `COBJ` has zero precedent in Enderal** — all 1,859 of its recipes carry a real
    bench keyword, none null, none absent. **[verified]** We shipped 67 null ones on the reasoning
    that null "is a real engine sentinel"; that reasoning was never tested and the overrides were
    later dropped entirely. If a dangling reference already makes the record unreachable, **leave it
    alone** — that is the proven archetype (guardrail 3), and an override that achieves nothing is
    still a record you have to be right about.
