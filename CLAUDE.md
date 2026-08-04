# Zenderal Patches — Spriggit Workspace Guide

> **This file is the most valuable thing in the repo.** It is what a future session reads instead of
> re-deriving these conventions from scratch. When you learn something the hard way — a FormID
> allocation, a record shape that didn't work, a compile import you needed — write it here.
>
> Facts below marked **[verified]** were checked against this machine's actual Enderal install or
> toolchain on 2026-08-01. Facts marked **[upstream]** come from Mutagen/Spriggit/SureAI source or
> documentation. Anything unmarked is convention, not measurement — treat it as changeable.

## What this is

**Zenderal** is an Enderal: Forgotten Stories (Special Edition) modlist aiming at three things:
**bug fixes**, **modern combat**, and **modern visuals**. *This repo is not the modlist.* It is the
workspace where the **patch plugins Zenderal ships** are authored, built and released — the
compatibility and bugfix `.esp` files that make the list's third-party mods work together on
Enderal — plus the curation docs that record what the list does and why.

Plugins are decompiled to YAML, edited as text, and re-packed to `.esp`.
**Never hand-edit binary plugins — edit the YAML.**

- Game: **Enderal: Forgotten Stories (Special Edition)**, running on the SkyrimSE engine.
- Spriggit game release: **`EnderalSE`** — *not* `SkyrimSE`. See "Why EnderalSE" below.
- Spriggit package/source: `Spriggit.Yaml.Skyrim`
- Spriggit CLI version: **`0.40.0` — deliberately pinned, do not upgrade** (see below).
- CLI path + all tool paths: `.claude/config/tools.json` (gitignored; see Tooling config below).

### Why `EnderalSE` and not `SkyrimSE`

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
> will not object if you add one — the game will. A patch that masters a DLC in Enderal is a patch
> that fails to load, and there is nothing in them to reference anyway. Compare
> `reference/base/Dawnguard-stub/` with `reference/base/EnderalFS/` if you ever doubt it.

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

## Tooling config (no hardcoded paths)

All tool paths and per-machine settings live in **`.claude/config/tools.json`** (gitignored;
template at `tools.example.json`). Skills load it via `.claude/config/tools.ps1`, which exposes
`$Tools` (e.g. `$Tools.spriggitCli`, `$Tools.papyrusCompiler`, `$Tools.papyrusSource.enderal`,
`$Tools.xedit`) and an `Assert-Tool` guard. **Never reintroduce a hardcoded path into a skill —
change the config instead.**

Note that `gameRoot` is **Enderal's** folder while `skyrimSeRoot` is the **Skyrim SE** folder. They
are separate installs, and several steps need both.

- **The Zenderal modlist itself** installs a full MO2 instance (Enderal copy + mods + tools) that
  can be hundreds of GB. It is gitignored (`/modlist/`, `/downloads/`). Run the **`modlist-install`**
  skill to install it and auto-discover its tool paths into `tools.json`.
- Without a modlist, fill `tools.json` by hand from `tools.example.json`.

## Workflow (round-trip)

```
.esp/.esm  ──serialize──►  YAML (committed)  ──deserialize──►  .esp/.esm
                 ▲                                                  │
                 └──────────── you edit the YAML ◄──────────────────┘
```

Serialize/deserialize commands: see `README.md`. After editing YAML, deserialize and load the plugin
in xEdit (**in `-EnderalSE` mode**) to verify before shipping.

## Folder map

```
src/                       # EVERY patch lives here — one folder per patch
  <PatchName>/
    <PatchName>ESP/        # Spriggit YAML — COMMITTED, source of truth
    Scripts/source/*.psc   # Papyrus source — COMMITTED
    Scripts/compiled/*.pex # COMMITTED via a .gitignore exception (CI can't compile Papyrus)
build/                     # build.ps1 + manifest.json + committed FOMOD trees
arch-docs/                 # patch-authoring guide, curation docs, generated build report
reference/base/            # gitignored — Enderal/vanilla decompiles + script source, LOOKUP ONLY
reference/mods/            # gitignored — third-party list mods, serialized for lookup
reference/mods/EGO/        #   `-- EGO's .esp + its loose scripts; documented in arch-docs/EGO/
modlist/                   # gitignored — the installed Zenderal MO2 instance, hundreds of GB
papyrus-source/            # gitignored — spare slot for unpacked .psc trees (see reference/base)
```

`src/` is the only place patch content goes, and it holds as many patches as the list needs. Each
gets its own `src/<PatchName>/` folder and its own `build/manifest.json` release entry; the
`/mod-new-plugin` skill sets both up.

### What's in `reference/base/` (built 2026-08-01, ~0.9 GB, gitignored)

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

**There is deliberately no starter plugin.** `build/manifest.json` ships with `"releases": []`, and
the build reports "nothing to build" and exits 0 in that state — the repo is green from the first
commit and stays green until there is a real patch to ship.

## Guardrails — how to work in this repo

These are distilled from real failures in this workspace's lineage. They cost test cycles to learn.

1. **Ground-truth before claiming.** Do not conclude a patch is or isn't needed, or that a record
   does what its name suggests, from the name alone. Read the serialized record, trace the
   FormKeys, and **show the evidence alongside the verdict**. If a mechanic depends on a third-party
   mod's compiled script, read that script's decompiled source — data-driven parts extend to your
   records, hardcoded index checks do not.
2. **Assume nothing transfers from Skyrim.** Enderal reuses the engine and almost none of the
   design. Progression, crafting, lighting, economy and the perk UI are all Enderal's own (see
   "How Enderal differs" below). A pattern that is correct for Skyrim modding is a *hypothesis* here
   until you have read Enderal's record or script.
3. **Prefer a proven archetype to an invented mechanism.** Read
   `arch-docs/enderal-record-patterns.md` first. The engine fails silently: an inert record produces
   no error, so an invented mechanism costs a full build-deploy-launch-test cycle to disprove.
4. **Copy records verbatim; never retype hex.** When basing a record on an existing one, copy the
   file and edit the fields that differ. Hand-transcribing `Data:` blobs has produced odd-length hex
   that fails the build, and dropped array entries that fail silently. Prefer a script over
   retyping. Re-check array lengths after any edit.
5. **A patch's job is to forward, not to author.** The commonest patch bug is not a wrong value —
   it is an override that carries *your* change and silently reverts someone else's. Before
   overriding a record, look at every plugin in the list that already touches it and confirm the
   winning version of every field you are not deliberately changing.
6. **Ask for paths; don't hunt for them.** Install locations, modlist names, MO2 folders and mod
   names live in `tools.json` or in the user's head. Read the config or ask — filesystem-searching
   for them wastes time and lands on the wrong candidate.
7. **Verify the deploy target before blaming the records.** A mod in a wrongly-named MO2 folder is
   invisible; the game runs fine and the change simply isn't there. The `mod-deploy` skill checks
   this. Rule out "never loaded" before debugging "loaded but broken".
8. **A clean build is not a working patch.** Deserialize, xEdit and the Papyrus compiler all passing
   proves it *builds*. Only launching Enderal proves it *runs*. Say which of the two you have
   actually established.
9. **Recompile and re-commit `.pex` whenever a `.psc` changes.** CI cannot run the Papyrus
   compiler. `build/build.ps1` fails on a *missing* `.pex` but cannot detect a *stale* one.
10. **PowerShell 5.1 is the target** for build scripts and skills: `Set-StrictMode` is on, there is
    no `&&`/`||`, no ternary, no null-coalescing, and no built-in YAML parser. Write `-Encoding utf8`
    explicitly when a file will be read by other tools.

## FormKey discipline

- **New** records use the patch plugin's own name as the FormKey suffix: `<hex>:<PatchName>.esp`.
- **Overrides keep the defining master's suffix** — that is how you tell at a glance which records
  you invented and which you are modifying:

  | Suffix | Means |
  |---|---|
  | `:Enderal - Forgotten Stories.esm` | a record Enderal itself created — **71%** of its records |
  | `:Skyrim.esm` / `:Update.esm` | a vanilla FormID. May be untouched vanilla, **or Enderal content sitting on an overridden vanilla record** — see below |
  | `:<SomeMod>.esp` | overriding a third-party list mod — check *its* load position |
  | `:<PatchName>.esp` | a record this patch invented |

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
> [`arch-docs/enderal/plugin-architecture.md`](arch-docs/enderal/plugin-architecture.md).

- **Master order in `RecordData.yaml`** is load order:
  `Skyrim.esm`, `Update.esm`, `Enderal - Forgotten Stories.esm`, then any third-party plugin you
  override, in list order.
- **ESL (`Small`) plugins are constrained to FormIDs `0x800–0xFFF`.** Patches should almost always
  be ESL-flagged — a list carries a lot of them and the 254-plugin limit is real. Note that
  *overrides consume no new FormID*, so an ESL patch can override thousands of records and still
  only need a handful of the 2048 new-record slots.
- Allocate a **contiguous block per feature** for readable diffs.
- ALWAYS grep the whole workspace (your patch folders + `reference/`) for a hex FormID before
  assigning it — use the `formkey-check` skill.

### Allocations in use

Each patch's own ESL block. Overrides are not listed — they consume nothing.

| Patch / plugin | Block | Contents |
|---|---|---|
| `RelentlessSword` → `Zenderal - Relentless Sword.esp` | `0x800–0x827` | `800–806` statics (1st-person models), `809–80F` weapons, `811–81F` forge + temper recipes (johnskyrim's original offsets, preserved for traceability), `820–825` dismantle recipes (new, this repo's), `826` crafting blueprint, `827` its placed reference in Riverville Temple |
| `SkipToTamingTheWaves` → `Zenderal - Skip To Taming The Waves.esp` | `0x800–0x803` | `800` Quest `ZP_SkipTTW`, `801` Activator `ZP_SkipTTW_StartTrigger`, `802` its placed trigger ref in Ark market cell `070793`, `803` Message `ZP_SkipTTW_sClassChoice`. Overrides `MQ101 03372B` (alias 183 `StartMarkerRef` → `TeleportMarker_ArkMarket 0EAB74`) and forwards FS's `CapitalCityMarketArea 07072A` header — neither costs anything from the block. **No `MQP01PrologStart` override**: `QF_MQ101_0003372B.Fragment_332` only does `MoveTo(StartMarkerRef)`, and nothing else starts the prologue — `MQP01` is started by the trigger inside `MQP01Home`, which a player spawning in Ark never reaches. SkipIntro disables that trigger defensively; it is not needed |

> **`Enderal - Forgotten Stories.esm` survives as a declared master.** It is an *implicit* base
> master under `GameRelease.EnderalSE`, so there was reason to fear Mutagen would drop it from the
> written master list and leave `:Enderal - Forgotten Stories.esm` FormKeys dangling. It does not:
> `Zenderal - Relentless Sword.esp` builds with `MAST Skyrim.esm` + `MAST Enderal - Forgotten
> Stories.esm`, and its `02F336` references resolve at master index **1**. **[verified]** So a patch
> may reference FS records freely — just declare the master and confirm it in the built header.

## Papyrus toolchain

Scripts go through extract → decompile → edit → compile → package. Use the matching skills; the
`papyrus-script-engineer` subagent handles decompiled-source cleanup and compile-error fixing.

**Tool paths:** all resolved from `.claude/config/tools.json` — do not hardcode.

| Step | Tool | Config key |
|------|------|------------|
| Extract `.bsa` | `bsab.exe` | `$Tools.bsab` |
| Decompile `.pex`→`.psc` | `Champollion.exe` | `$Tools.champollion` |
| Compile `.psc`→`.pex` | `PapyrusCompiler.exe` (from Skyrim SE) | `$Tools.papyrusCompiler` |
| Open Creation Kit | `CreationKit.exe` (from Skyrim SE) | `$Tools.creationKit` |

### The import path is first-wins, and Enderal must be first

There are **three** Papyrus source trees in an Enderal setup, and **55 script names exist in both
Enderal's and Skyrim's** — `critter.psc`, `dgintimidateplayerscript.psc`, `dragonactorscript.psc`,
the `default*` handlers, and so on. Compile against the wrong copy and you get code built on vanilla
signatures that fails at runtime, not at compile time.

**All 55 differ from vanilla — not one is an accidental identical duplicate.** **[verified]** by
byte-comparing `reference/base/EnderalScripts` against `reference/base/VanillaScripts`. Two of them
are explicit `; DUMMY, DO NOTHING` stubs: `dgintimidateplayerscript.psc` and
`dgintimidatealiasscript.psc`, where Enderal has gutted the vanilla brawl/intimidate system down to
4 lines from 59. **[verified]** That is the concrete cost of getting the order wrong: compile
against vanilla's copy and you link in brawl logic Enderal deliberately deleted.

**The Papyrus compiler's `-i` path is FIRST-WINS. [verified]** — tested directly on this machine's
`PapyrusCompiler.exe` by putting a deliberately broken copy of a script in the first import dir and
a good copy in the second: with `-i="broken;good"` the compile **failed** on the broken copy; with
`-i="good;broken"` it **succeeded**. So the correct order is:

```
-i="<papyrusSource.enderal>;<papyrusSource.skse>;<papyrusSource.vanilla>;<importDirs...>"
```

> SureAI's own `How to modify Enderal scripts.txt` (inside `ScriptsEnderal.zip`) states the sources
> "must be loaded in the following order: Creation Kit scripts (Scripts.zip), SKSE scripts, Enderal
> scripts (ScriptsEnderal.zip)". That is **precedence** order — last one wins — describing the CK's
> source-folder list. It is the **reverse** of the `-i` order above. Both say the same thing:
> *Enderal's copy is the one that must be used.* Don't paste that readme's order into `-i`.

**Where the three trees come from** (unpack once; `papyrus-source/` is gitignored):

| Tree | Source | `tools.json` key |
|---|---|---|
| Enderal (~5000 `.psc`) | `<gameDataDir>/ScriptsEnderal.zip` → its `source/scripts/` | `papyrusSource.enderal` |
| SKSE (74 `.psc`) | `<gameDataDir>/Source/Scripts` — already loose in an Enderal install | `papyrusSource.skse` |
| Vanilla (~14300 `.psc`) | `<skyrimSeRoot>/Data/Scripts.zip` → its `Source/Scripts/` | `papyrusSource.vanilla` |

**Flags file.** `TESV_Papyrus_Flags.flg` ships only in the **vanilla** `Scripts.zip` — neither
Enderal tree contains one. **[verified]** It resolves off the `-i` path, so having vanilla on the
path is what makes `-f=TESV_Papyrus_Flags.flg` work.

**Enderal's own scripts are prefixed `_00E_`** (1257 of them). **[verified]** A script name starting
`_00E_` is Enderal's; treat it as third-party source you read but do not edit in place — patch by
adding your own script, not by shipping a modified `_00E_` file, unless overriding it *is* the fix
and you have said so in the patch's notes.

**Per-project import dirs** — persist in `tools.json`'s `importDirs` array (the `papyrus-compile`
skill appends them to `-i` after the three trees). Record each one here as you discover it:

| API / framework | Source `.psc` dir |
|-----------------|-------------------|
| _(none yet)_ | Add SkyUI/MCM, PapyrusUtil, etc. here when a patch's script needs them. |

### Creation Kit against Enderal

The CK is only needed for asset work and for the compiler binary — **all record editing here happens
in the Spriggit YAML**, so most sessions never open it. If you do:

- Use the **Skyrim SE** CK (`$Tools.creationKit`), pointed at Enderal's `Data`.
- `bAllowMultipleMasterLoads=1` must be set in `CreationKit.ini` (already set on this machine
  **[verified]**) — without it the CK refuses to load an ESP on top of an ESM chain.
- The CK's `sResourceArchiveList` lists the *Skyrim* BSAs; it does not know about `E - *.bsa`, so
  Enderal assets will be missing in the render window unless you add them.

## Testing

MO2 instances under `$Tools.modlistsRoot`, or the Zenderal instance at `$Tools.modlistRoot`.
Use the `mod-deploy` skill rather than copying by hand.

**xEdit must run in Enderal mode:** use a copy named `EnderalSEEdit.exe` or pass **`-EnderalSE`**.
**[upstream]** Plain SSEEdit mode reads the Skyrim game folder and INI and will not see Enderal's
plugins at all. The `xedit-audit` skill passes the switch.

---

# Zenderal — the list

## The three pillars

Every patch in this repo should trace back to one of these. If it doesn't, it probably belongs in a
different repo.

| Pillar | Goal | What patches here typically do |
|---|---|---|
| **Bug fixes** | Ship Enderal as SureAI intended, minus the bugs | Fix broken records, quest blockers, bad navmesh/refs, dangling references; forward community bugfix mods onto Enderal's ESM |
| **Modern combat** | Contemporary combat feel without breaking Enderal's balance | Reconcile combat overhauls with Enderal's talent/perk system, weapon/armor keywords and combat styles |
| **Modern visuals** | Current-generation look, Enderal's art direction intact | Reconcile lighting/weather/ENB-adjacent mods with Enderal's own lighting, and mesh/texture replacers with Enderal's assets |

### Where the documentation is

| Read this | For |
|---|---|
| **[`arch-docs/enderal/`](arch-docs/enderal/)** | **How Enderal actually works** — six documents mined from the serialized plugins and SureAI's own source. Start with [`plugin-architecture.md`](arch-docs/enderal/plugin-architecture.md) |
| **[`arch-docs/EGO/`](arch-docs/EGO/)** | **How EGO works and how to patch around it** — the list's gameplay overhaul, 6203 overridden records. Start with [`patching-ego.md`](arch-docs/EGO/patching-ego.md) before any combat/loot/crafting patch |
| `arch-docs/enderal-record-patterns.md` | Record shapes that build clean and do nothing in-game |
| `arch-docs/zenderal-curation.md` | What is actually in the list and why |

Per pillar: combat patches start at [`arch-docs/enderal/combat.md`](arch-docs/enderal/combat.md),
visuals at [`visuals-and-world.md`](arch-docs/enderal/visuals-and-world.md), and anything touching
progression, potions or scripts at
[`progression-and-classes.md`](arch-docs/enderal/progression-and-classes.md) /
[`crafting-alchemy-economy.md`](arch-docs/enderal/crafting-alchemy-economy.md) /
[`scripting-and-actorvalues.md`](arch-docs/enderal/scripting-and-actorvalues.md).

### EGO is the list's dominant conflict source

`Enderal SE - Gameplay Overhaul.esp` (v1.93.1.0, author *Ixion XVII*) overrides **6203** records and
adds **974**. **[verified 2026-08-04]** Zenderal patches load **after** it. Four facts that change
how you write a patch, all documented in [`arch-docs/EGO/`](arch-docs/EGO/):

1. **EGO is not `Localized`.** Every string on every record it overrides collapses from a
   multi-language `Values:` list to a single English `Value:`. So `['Name', 'Description',
   'Version2']` is the **null diff** — filter it out — and copying the FS/Skyrim version of a record
   EGO also overrides re-adds the `Values:` block, which is the tell that you copied the wrong source.
2. **`Player 000007:Skyrim.esm` carries 42 EGO perks.** That record *is* EGO's player ruleset.
   Overriding it without forwarding them deletes the mod's combat, economy, alchemy and mana rules
   while everything else still looks installed.
3. **61 records are injected**, not overridden — FormIDs in `Skyrim.esm`'s space that `Skyrim.esm`
   does not define (`ChaurusChitin 03AD57`, `DeflectArrows 058F68`, the Dragon Priest masks, six
   `DeathItem*` lists…). Referencing one means declaring EGO as a master.
4. **EGO rewrites all three blueprint vendor lists** (`_00ETraderCraftingPlansA/B/C`) — the exact
   records a new craftable-weapon patch needs — plus 123 other leveled lists, 99 GMSTs and 18 GMSTs
   it creates outright.

Before touching a record, `grep` its FormKey in
[`arch-docs/EGO/conflict-index.md`](arch-docs/EGO/conflict-index.md); if it is listed, build your
version from **EGO's** YAML file, not the master's.

## How Enderal differs (and what that breaks)

This is the section to read before assuming a Skyrim mod "just works". Each entry is a verified
mechanism plus the class of patch it invalidates.

**Progression is not Skyrim's.** There is no learn-by-doing and no vanilla perk tree UI. Enderal's
*talents* are three-tier **Perks** paired with **WordOfPower** unlocks, read back via
`_00E_TalentLibrary.GetPlayerTalentLevel(Perk01, Perk02, Perk03)` and
`GetTalentLevel(Word01, Word02, Word03)`. **[verified]** The character sheet is a **custom menu** —
`_00E_Game_SkillmenuSC`, a script on a ReferenceAlias that registers for `"Journal Menu"` and draws
Enderal's own UI. **[verified]**

> **Consequence.** A combat mod that adds perks to vanilla perk trees puts them somewhere the player
> can never see or buy. Combat patches must hang new behaviour off Enderal's own perks/talents, or
> off keywords and combat styles, not off the vanilla progression UI.

**Lighting is wholly replaced.** SureAI's own readme: *"since Enderal changes all light settings, no
ENB preset made for Skyrim would produce adequate lighting in Enderal. Furthermore, ENB mods may
deactivate fadeouts in cutscenes, leading to visual bugs."* **[verified — quoted from
`enderal readme.txt`]**

> **Consequence.** For the visuals pillar, a Skyrim ENB/weather/lighting mod is a starting point, not
> a drop-in. Budget for an Enderal-specific reconciliation pass, and watch cutscene fades — they are
> a known ENB casualty and they are everywhere in Enderal's story.

**Skyrim mods need conversion, by the author's own statement.** *"Enderal uses its own master file
(ESM). Mods that were developed for Skyrim must be adjusted to it before they can safely be used in
Enderal."* **[verified — `enderal readme.txt`]** In practice a Skyrim mod that only edits
`Skyrim.esm` records may load, but Enderal has usually already overridden the record you care about,
and Enderal's copy wins or loses purely on load order.

**Enderal-only systems to look for** before touching anything nearby (script names verified in
`ScriptsEnderal.zip`): Arcane Fever (`_00E_FS_AlchAddArcaneFever`), Phasmalism/Apparitions
(`_fs_phasmalist_controlquest`, `_00E_Phasmalist_*`), the affinity system inside
`_00E_Game_SkillmenuSC`, memory/learning points (`_00E_Lehrbuch_Plus1MemoryPointSC`,
`_00E_Lehrbuch_Plus2SkillPointsScript`), crafting books (`_00E_Handwerksbuch*`), and the
talent cooldown/control quests (`_00E_Game_TalentControlSC`, `_00E_Game_TalentCooldownSC`).

**A ported Skyrim gear mod's recipes are the part most likely to be silently inert.** Enderal keeps
the crafting *plumbing* (bench keywords are vanilla — see
[`crafting-alchemy-economy.md`](arch-docs/enderal/crafting-alchemy-economy.md)) but not everything
around it. Two concrete traps, both found in Relentless Sword **[verified]**:

| Vanilla FormID | In Enderal | Consequence |
|---|---|---|
| `0F46CE` `CraftingSmithingSkyforge`, `0F46D1` (Companions global) | **Do not exist** — no record at either ID in `Skyrim.esm`, `Update.esm` or the FS ESM | A Skyforge recipe can never appear. Repoint to `CraftingSmithingForge` `088105`. |
| `05218E` — vanilla's Arcane Blacksmith | `_00E_Class_Phasmalist_P04_B_ArcaneSmith`, *"You can improve enchanted armors and weapons"* | A **false friend that happens to be correct**: the standard temper condition means in Enderal exactly what it meant in Skyrim. Leave it alone. |

Enderal's own forge recipes gate on **`GetActorValue Smithing >= N`** (`RunOnType: Reference`,
`Reference: 000014:Skyrim.esm`) plus, usually, owning a `_00E_CraftingPlan_*` blueprint — **not** on
smithing perks. The vanilla smithing perks `0CB40D–0CB414` all still exist, but Enderal's `Player`
NPC record **grants every one of them at rank 1 from the start** **[verified]**, so `HasPerk
EbonySmithing` is a condition that is always true and gates nothing. Copy **both** conditions from
`_03E_RecipeWeapon_27_SwordOfTheRighteousPathForged` (`148A89:Skyrim.esm`) instead — the AV check and
the `GetItemCount <blueprint> >= 1` that follows it. Shipping only the first is the easy mistake:
the recipe works, but the item unlocks on level alone, unlike every one of its tier peers.

**Blueprints are `MiscItem`s, not Books** **[verified]** — `_00E_CraftingPlan_*`, model
`Enderal\books\Craftingplans\Craftingplan.nif` with an `AlternateTextures` entry selecting a
per-weapon-type TextureSet (`_00E_CraftingPlan_OneHandedSword` `09D079`, `…TwoHandedSword` `09D07A`,
and 22 more). Keywords `VendorItemClutter` + `VendorItemTool` + `Blueprint` (`0493B5`), `Value: 150`,
`Weight: 0.1`. Their in-game names read **`Blueprint: <item> (Handicraft <N>)`** — note **Enderal
displays the `Smithing` AV as "Handicraft"** (`_00E_Levelsystem_sSkillNameSmithing`), so a blueprint
naming the vanilla skill will look wrong to a player. Vendors stock them through three level-tiered
leveled lists — `_00ETraderCraftingPlans` `137A06` (level 1), `…PlansB` `148ABD` (10+), `…PlansC`
`148ABE` (19–30). A Handicraft-50 blueprint belongs in **C at Level 30**, where the Righteous Path
and Aeterna plans sit.

For weapon balance, Enderal's scale runs ~1.6× Skyrim's: its shadowsteel (ebony) tier sword is
**23 damage / crit 6** and its greatsword **37 / crit 11** **[verified]**. Note also that
`05AD9D:Skyrim.esm` is **`IngotShadowsteel`** here, Enderal's rename of ebony — so an ebony-tier
Skyrim recipe's *materials* usually port across unchanged even when its gating does not.

## Useful FormKey constants

These are **engine-hardcoded** FormIDs — Bethesda's own code depends on them, so Enderal's replacement
`Skyrim.esm` keeps them. They are safe to reference.

> **This table is deliberately short.** Because Enderal's `Skyrim.esm` *is* Enderal (see "Masters"
> above), an ordinary-looking vanilla FormID usually resolves to an Enderal record. Do not extend this
> table from Skyrim documentation — look the record up in `reference/base/Skyrim/` and cite the
> EditorID you actually found. Enderal's own worldspace, keyword, bench and talent FormKeys are
> documented in [`arch-docs/enderal/`](arch-docs/enderal/).

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

## Gotchas

- **Enderal's cell EditorIDs are German; the display names are English.** Riverville is
  **`Flusshaim*`**, Ark is **`CapitalCity*`**, and the Sun Temple is `Suntemple*`. **[verified]**
  Searching `reference/base/*/Cells/` by the English town name returns **nothing** — grep the
  localized `String:` values instead, then read the EditorID off the match. This is also what a `coc`
  command needs: `coc FlusshaimShopSura` lands in "Riverville, Sura's Sharp Steel".
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
- **Never rewrite a UTF-8 doc with PowerShell 5.1's `Set-Content -Encoding utf8`.** **[verified
  2026-08-03]** It reads the file as the system ANSI codepage and writes it back as UTF-8 **with a
  BOM**, double-encoding every non-ASCII character — every `—` in this file became `â€"` in one
  pass, and `git diff` then reports the whole file as changed. It happened here while resolving a
  rebase conflict in `CLAUDE.md`. Use the Edit tool for surgical text changes, or `git checkout` the
  file and redo them; if you must script it, read and write with an explicit
  `[System.Text.UTF8Encoding]::new($false)` rather than the `-Encoding utf8` shorthand.
- **`E - Update.bsa` loads last and wins.** When a record or asset doesn't look like the one you
  found in `E - Meshes.bsa`, check `E - Update.bsa` before concluding your patch is wrong.
- **A DLC master silently breaks the plugin.** Spriggit accepts it (Mutagen's implicit base-master
  set for `EnderalSE` includes the DLC) but Enderal does not load them. See "Masters" above.
- **Compiling against vanilla signatures.** If a script compiles clean and then misbehaves on an
  Enderal type, check the `-i` order — Enderal's tree must be first. 55 names collide.
- **FOMOD images that actually render in MO2** — a config can build clean, pass
  `build.ps1 -CheckFomod`, open its wizard normally, and still show *no image at all*. Nothing
  warns you. This recipe is confirmed working in MO2; copy its shape rather than re-deriving:
  1. `path=` is relative to the **archive root**, so an image at `fomod/images/foo.jpg` is
     referenced as `path="fomod\images\foo.jpg"` — *including* the `fomod` prefix.
  2. Use **backslashes** in `path=`.
  3. Declare an `<installSteps>` block, even for a patch with no real choices (one
     `SelectExactlyOne` group holding a single `Recommended` plugin). A config with only
     `<requiredInstallFiles>` gives MO2 no wizard page to draw the banner on.
  4. Use a **baseline** JPEG or a PNG, not a progressive JPEG. Check with
     `od -A d -t x1 -v img.jpg | grep -oE 'ff c[0-9a-f]'`: `ff c0` is baseline (fine), `ff c2` is
     progressive. Re-encode progressive files via `System.Drawing` before shipping.

  These four were fixed **together** after several one-at-a-time attempts each failed, so which is
  individually decisive is unverified — treat the set as the known-good recipe, and do not drop one
  on the assumption it does not matter.

  `build/build.ps1 -CheckFomod` enforces points 1, 2 and 4: an unresolvable `path=` or a
  progressive JPEG **fails** the check (with a "did you mean `fomod\…`?" hint for the missing
  prefix), and forward slashes warn. It cannot check point 3 — whether an `<installSteps>` block
  exists at all — because a config legitimately may not want one.
- **Decompiled `.psc` is a reconstruction** (Champollion): auto-named vars, reconstructed control
  flow, lost comments/flags. Enderal ships real source for its own scripts in `ScriptsEnderal.zip` —
  **read that instead of decompiling** whenever the script is Enderal's.
- **Missing-type compile errors** → the referenced API's source isn't on the import path; add its
  `Source\Scripts` dir to `importDirs` in `tools.json` and record it in the imports table above.
- **YAML comments do not survive a re-serialize.** Spriggit rewrites the folder from the binary
  plugin, so any `#` comment you add to a record file is lost the next time anyone runs
  `/spriggit-serialize`. Put durable explanation in this file, not in the record YAML.
- Edit `.psc`/YAML, never the binary `.pex`/`.esp`. Commit source, not build artifacts.
- See `arch-docs/enderal-record-patterns.md` for the in-game failure modes that produce no build
  error — that list is the single highest-value read before authoring a new patch.
