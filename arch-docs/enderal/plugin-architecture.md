# Plugin architecture

**The single most important fact about modding Enderal**, and the one that invalidates most Skyrim
modding intuition.

## `Skyrim.esm` in Enderal's Data folder is not Skyrim

Enderal SE ships its own `Skyrim.esm`. It is **not** Bethesda's file — it is a wholesale replacement
that *is* the base Enderal game. **[verified]**

| | Enderal's `Skyrim.esm` | Real Skyrim SE `Skyrim.esm` |
|---|---|---|
| Size | **191,827,554 bytes** | 249,753,412 bytes |
| `CNAM` (author) | **`mcarofano`** | Bethesda's |
| `_00E_`-prefixed records | **12,223** | 0 |
| Tamriel worldspace | **absent** | present |
| Main worldspace | **`Vyn`** | Tamriel |
| Climates | `SternenstadtClimate`, `SkyrimClimate`, `DefaultClimate`, `UnderwaterClimate` | vanilla set |

Verify it yourself in one line — the author field is in the TES4 header:

```bash
head -c 200 "$GAMEDATA/Skyrim.esm" | od -c | grep -A1 CNAM
```

### What this means in practice

- **`reference/base/Skyrim/` is Enderal's content**, not vanilla lookup material. When you grep it
  for a record, you are reading Enderal.
- **A `:Skyrim.esm` FormKey suffix does not mean "vanilla record".** In Enderal it usually means
  "base Enderal game", as opposed to `:Enderal - Forgotten Stories.esm` meaning "the Forgotten
  Stories expansion".
- **Real vanilla Skyrim records mostly do not exist here.** Do not copy a FormID out of a Skyrim
  wiki or the real Skyrim SE `Skyrim.esm` and assume it resolves to the same thing.
- The engine-level FormIDs Bethesda hardcodes *are* still present and still mean what they always
  did — `000014` PlayerRef, `000039` GameDaysPassed, `000010` MapMarker. Those are safe.

> **Note on the `reference/base/VanillaScripts/` tree.** That one *is* genuinely from your Skyrim SE
> install (unpacked from its `Scripts.zip`), because Enderal ships no full vanilla script source and
> the Papyrus compiler needs the base types plus `TESV_Papyrus_Flags.flg`. It is the one place in
> `reference/base/` where "vanilla" means vanilla.

## The two plugins

| Plugin | Size | Author | Role |
|---|---|---|---|
| `Skyrim.esm` | 191 MB | `mcarofano` | **Base Enderal.** Everything in the original release |
| `Enderal - Forgotten Stories.esm` | 10.8 MB | `Niseam` | **The Forgotten Stories expansion.** Adds two classes, new quests, and overrides base Enderal |

`Enderal - Forgotten Stories.esm` declares exactly two masters: `Skyrim.esm` and `Update.esm`.
**[verified]** Its records split:

| Defining master | Records | Share | Meaning |
|---|---|---|---|
| `Enderal - Forgotten Stories.esm` | 6815 | **71.2%** | new in the expansion |
| `Skyrim.esm` | 2749 | **28.7%** | **FS overriding base Enderal** |
| `Update.esm` | 2 | 0.0% | — |

So when you see `_00E_Class_Infiltrator_P03_C_Assassin - 069D32_Skyrim.esm` inside the FS plugin,
that is the expansion overriding a base-Enderal record — not touching anything of Bethesda's.

### The DLC ESMs are empty stubs

`Dawnguard.esm` (44 KB), `Dragonborn.esm` (44 KB) and `HearthFires.esm` (**80 bytes**) sit in
Enderal's Data folder but are **not** in `plugins.txt`, **not** mastered by anything, and contain
1–2 records each. **[verified]** `HearthFires.esm` is a bare TES4 header. They exist so the engine
finds the filenames it expects.

**Never master a DLC.** Mutagen's implicit base-master list for `EnderalSE` includes them, so
Spriggit will not warn you — the game simply won't load your plugin, and there is nothing in them to
reference anyway.

### `SkyUI_SE.esp` is part of the game

8 records, shipped in Enderal's Data folder and active in the stock `plugins.txt`. **[verified]**
Never install a second copy of SkyUI.

## Stock load order

`%LOCALAPPDATA%\Enderal Special Edition\plugins.txt` **[verified]**:

```
*Enderal - Forgotten Stories.esm
*SkyUI_SE.esp
```

`Skyrim.esm` and `Update.esm` are implicit. Everything else in that file is Zenderal.

**Your patch's masters**, in order: `Skyrim.esm`, `Update.esm`,
`Enderal - Forgotten Stories.esm`, then third-party plugins in load order.

## Record inventory

Counts of serialized records, taken 2026-08-01. **[verified]** Use these to calibrate how big a
change you are proposing — "Enderal has 316 weapons" makes a weapon overhaul a very different
proposition than it is in Skyrim.

| Record type | base Enderal (`Skyrim.esm`) | Forgotten Stories |
|---|---:|---:|
| MagicEffects | 1008 | 335 |
| Lights | 1195 | 122 |
| Armors | 993 | 160 |
| Spells | 837 | 311 |
| Keywords | 693 | 57 |
| ConstructibleObjects | 639 | 1220 |
| Globals | 417 | 95 |
| ImageSpaces | 339 | 28 |
| ImageSpaceAdapters | 328 | 29 |
| Weapons | 316 | 34 |
| Perks | 291 | 82 |
| Quests | 193 | 65 |
| Weathers | 147 | 57 |
| CombatStyles | 121 | 7 |
| Races | 117 | 51 |
| Regions | 100 | 14 |
| WordsOfPower | 85 | 42 |
| LightingTemplates | 60 | 6 |
| Shouts | 41 | 15 |
| Worldspaces | 23 | 812 files* |
| Cells | 524 files* | 291 files* |
| Climates | 4 | 0 |
| DialogTopics | — | 5264 |

\* Worldspace and cell records nest into folders, so the file count is not a record count. Treat
these as "large" rather than an exact figure.

## Patching rules that follow from all this

1. **Grep `reference/base/Skyrim/` before `reference/base/EnderalFS/`** when looking for base-game
   content. Most of Enderal is in the former.
2. **Check both** before assuming you have found the live version of a record. If FS overrides it,
   FS wins.
3. **Never assume a vanilla FormID means the vanilla record.** Look it up.
4. **A patch that masters only `Enderal - Forgotten Stories.esm`** cannot override base Enderal
   records — it needs `Skyrim.esm` too, which it gets automatically as an implicit base master, but
   the record must still carry the `:Skyrim.esm` suffix.
5. **Load your patch after everything it forwards.** See
   [`../enderal-record-patterns.md`](../enderal-record-patterns.md) §0.1.
