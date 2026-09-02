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

## Knowledge base (oculory-rag) — search it before answering

If the `oculory-rag` MCP tools are available, use them **before** answering from memory and
before grepping `reference/` by hand:

- **`search`** — the written knowledge base: engine behaviour, record patterns, SPID, Spriggit
  and Mutagen workflow, third-party mod analyses, prior art and design notes.
- **`game_search` / `game_read`** — the decompiled game files themselves: ~331k records and
  ~19k Papyrus scripts, looked up by EditorID, FormID, FormKey or in-game name. Prefer these
  over walking `reference/` by hand; they are indexed and answer in milliseconds.
- Pass `game="enderal"` for this repo. Enderal ships a MODIFIED `Skyrim.esm`, so a
  vanilla-Skyrim answer is often the wrong one.

Cite the doc id or FormKey a claim rests on, and keep the `[verified]` / `[community]` /
`[unverified]` marks honest — retrieved text is evidence, not proof.

These tools are an optional local index. If they are not present, work in this repo exactly as
before: nothing here depends on them.

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
    tools/*.ps1            # only for REPLACEMENT releases — the generators that rebuild the tree
    spid/*_DISTR.ini       # SPID configs — COMMITTED; shipped via the manifest's "files" key
build/                     # build.ps1 + manifest.json (+ a committed FOMOD tree per release that has
                           #   one - none currently do; releases carry "fomod": false)
arch-docs/                 # patch-authoring guide, curation docs, generated build report
arch-docs/magic/           # GENERATED magic dataset: every SPEL/MGEF/ENCH/SCRL/ALCH/SHOU/GMST with
                           #   load-order-WINNING values + provenance; /magic-extract regenerates it
arch-docs/tools/           # third-party tool docs: SPID reference + its Enderal guide
reference/base/            # gitignored — Enderal/vanilla decompiles + script source, LOOKUP ONLY
reference/mods/            # gitignored — third-party list mods, serialized for lookup
reference/mods/EGO/        #   `-- EGO's .esp + its loose scripts; documented in arch-docs/EGO/
modlist/                   # gitignored — the installed Zenderal MO2 instance, hundreds of GB
papyrus-source/            # gitignored — spare slot for unpacked .psc trees (see reference/base)
```

> **Two shapes of release exist.** Most are **patches**: a small plugin of overrides that masters the
> mod it fixes — everything in this repo is one. A few mods must instead be **replacements**: the
> third-party plugin itself, rebuilt with our changes and shipped under its *original filename* so
> its BSAs keep loading, with `src/<Name>/<Name>ESP/` holding *all* of the author's records rather
> than just our edits, because that is what the build deserializes. A replacement is only legitimate
> when the author's permissions allow modification and re-upload, and it must ship credit in the
> plugin header and on the mod page. It also needs a `tools/` folder of generators that can rebuild
> the tree against a new upstream version — without those, an update means redoing the analysis from
> scratch.
>
> **Replacements are not built here.** The form-version ceiling below forces some Enderal ports into
> that shape, and those live in the
> [`enderal-mods`](https://github.com/whisperdealer/enderal-mods) repo, which holds Enderal SE mods
> in general rather than this list's patches. `Apocalypse - Magic of Skyrim` is the worked example and
> the source of most of what the ceiling section below records.

> **A third shape: the SCRIPT-ONLY release — no plugin at all.** **[verified 2026-08-08]** When a
> third-party mod's misbehaviour lives entirely in a *loose* `.pex` and not in its records, the patch
> is one recompiled script and nothing else. `build/manifest.json` supports it directly: set
> `"plugins": []` alongside `"fomod": false` and a `"scripts": { "from": …, "to": "Scripts" }` block.
> `build.ps1` handles that without changes — the `foreach ($p in $rel.plugins)` loop simply runs zero
> times, and the release contributes an archive but no row to the build report's Plugins table.
>
> Four rules, learned building `Zenderal - No Kata Debug Prompt` (that release was later absorbed
> into `Zenderal - Kata Fixes`, which ships the recompiled script *alongside* a plugin — a release
> may mix both; the rules below apply to its `scripts` block unchanged):
> 1. **Start from the author's own `.psc`, copied verbatim**, and change the fewest lines possible
>    (guardrail 4). Most mods that ship loose scripts ship their `source/` next to them.
> 2. **Never add or remove a `Property` declaration.** The host plugin's quest record stores the
>    property *values* in its `VMAD` and binds them **by name** at load. Drop a declaration and
>    Papyrus logs an unresolved property every load; rename one and its value silently never arrives.
>    Read the values out of the serialized record and diff the property set against your script before
>    compiling — `rg -a -o '<names>' both.pex | sort -u` on the two `.pex` is the cheap confirmation.
> 3. **It only wins if it sorts ABOVE the mod it overrides in `modlist.txt`** — MO2 writes that file
>    highest-priority-first (the list's `EGO SE - *` patches sit ~20 lines above the `KataPUMB *` mods
>    they patch). Getting this backwards is invisible: the game runs and the original script wins.
> 4. **A `.pex` override only bites where the script re-runs.** An `OnInit()` fix reaches new games
>    and saves that never had the mod; a save where `OnInit` already fired is untouched.
>
> This shape carries an obligation the others don't: it redistributes a **modified copy of someone
> else's script**, so check the author's permissions and credit them in the source header.

> **A fourth shape: the SPID CONFIG release — no plugin, no script, one `.ini`.** **[verified
> 2026-08-13]** *Spell Perk Item Distributor* 7.3.2 is in the list, and a fix that only needs to hand
> a spell/perk/keyword/outfit to a set of NPCs is a text file, not a plugin. `build/manifest.json`
> carries it with `"plugins": []`, `"fomod": false` and a **`"files"`** block:
>
> ```json
> "files": [ { "from": "src/<PatchName>/spid/Zenderal - <Name>_DISTR.ini", "to": "" } ]
> ```
>
> `"to": ""` is the **archive root** and it has to be, because SPID scans the Data folder with a
> *non-recursive* `directory_iterator` — a config one folder down is never seen and nothing warns.
> Three rules:
> 1. **Prefix the shipped filename `Zenderal - `.** Two mods shipping the same `_DISTR.ini` name are
>    an ordinary MO2 file conflict and only the winner deploys, silently. This list already has one:
>    10 `_DISTR.ini` on disk, `9 matching inis found` in the log.
> 2. **Write it pre-sanitised** — `~` not ` - `, no spaces around `|` or `,`, `0x` FormIDs with no
>    leading zeros. SPID rewrites any config it has to normalise, in place, inside the deployed mod
>    folder, so the committed and deployed copies otherwise drift.
> 3. **Verify with `Registered X/Y` in `po3_SpellPerkItemDistributor.log`, not by launching.** Every
>    unresolvable filter is skipped per entry and logged, never surfaced in game — Enderal currently
>    registers **198/318** of the list's keyword entries.
>
> Full detail in [`arch-docs/tools/spid.md`](arch-docs/tools/spid.md) and
> [`spid-in-enderal.md`](arch-docs/tools/spid-in-enderal.md). Read the second one before porting a
> Skyrim config: faction, NPC and location filters almost never survive, and `NordRace` resolves in
> Enderal to **Half Arazealean**.

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
    explicitly when a file will be read by other tools. Two further traps when bulk-editing YAML:
    - **The Spriggit YAML is CRLF, so `$` in a multiline regex does not match.** `'(?m)^Foo: bar$'`
      silently fails on `Foo: bar\r\n` because `$` anchors before `\n` and the `\r` is in the way.
      Use `(?=\r?$)` or drop the anchor. **[verified]** — this cost a full pass on the Apocalypse
      recipes and it fails *silently*, so always assert the replacement count and throw on zero.
    - `Join-Path` takes **two** arguments in 5.1; `Join-Path $a $b $c` is a parameter-binding error.
      Nest the calls.
11. **Bulk record edits should be scripted, verified by count, and re-validated after.** When a patch
    touches dozens of records, generate them from `reference/` with a script that *asserts* what it
    changed (entry counts before/after, every intended replacement matched at least once) and fails
    loudly otherwise. Then re-resolve every FormKey the patch emits against the serialized masters —
    that catches the dangling references xEdit would, without needing the mod installed. Note
    `000014:Skyrim.esm` (PlayerRef) is **absent from `reference/base/Skyrim/`** despite being valid
    and used by 77 of Enderal's own recipes, so allow-list it rather than chasing it. **[verified]**

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
| `RelentlessSwordPatreon` → `Zenderal - Relentless Sword.esp` | `0x800–0x831` | `800–806` statics (1st-person models), `809–80F` weapons, `811–81F` forge + temper recipes (johnskyrim's original offsets, preserved for traceability), `820–825` dismantle recipes (new, this repo's), `826` crafting blueprint, `827` its placed reference in Riverville Temple — those 33 records were the free six-blade Nexus release. Then `828–829` statics, `82A–82B` weapons, `82C–82D` forge recipes, `82E–82F` tempers, `830–831` dismantle recipes for johnskyrim's Patreon "Zen" blade, allocated **above** the first block so a user coming from the six-blade build keeps every FormID. **The six-blade release was removed on 2026-08-16** (`src/RelentlessSword/`, plus `build-zen-tree.ps1`, which derived this tree from it and had no input left) — this folder is now hand-edited source of truth, and its assertions (42 record files, 8 blueprint-gated recipes, no `0F46CE`/`0F46D1` Skyforge refs) went with it. The **plugin filename was deliberately NOT renamed with the release**, for the same FormID reason |
| `MagicPatches` → `Zenderal - Magic Patches.esp` | _(none used)_ | ALL magic compat/balance patches for the list live in this one plugin. Currently: **Apocalypse cost-ladder repricing** — 175 overrides of the book-taught Apocalypse player spells (their live costs ran 4–7× EGO's ladder: FF tier medians 56/83/175/393/720 vs EGO's 30/53/76/97/124). Mechanism: the spells are ALL auto-calc, so the engine reprices them from effects at runtime and a bare `BaseCost` override does nothing — each override adds `ManualCostCalc` + a hand `BaseCost` (EGO's own archetype, 78/81 of its Kata patch overrides). New cost = per-(tier, FF/conc) ratio onto EGO medians, from `src/MagicPatches/tools/01-build-cost-table.py`; YAML generated by `02-apply-cost-table.ps1` from `reference/mods/Apocalypse`, then `03-retune-fever.ps1` retunes the heals' Arcane Fever tax (Wild Healing 5→1.5 to EGO's flat burst rate, Resurgence 5→4 and King's Heart 12→5 to Enderal's 78-HP-per-point / Panacea precedents; Healing Blossom's 8 was already on the rule). **Regeneration order is 02 then 03** — never hand-edit the Spells folder. Also one MGEF override, NOT script-generated (the `MagicEffects/` folder survives regeneration): `_00E_IncreaseArcaneFeverFFSelf 11A4B6:Skyrim.esm`, EGO's record forwarded verbatim except its fever description — EGO baked the literal `<1,5>%` into the shared effect's text (safe for EGO, whose every user is 1.5), so all four Apocalypse heals displayed "1,5%"; restored base Enderal's `<mag>` token so each spell shows its real fever. Plus **five LVLI distribution-list merges** from `04-merge-distribution-lists.py`: the four `_00E_SpellBooksLoot*` lists (winner = the EGO-Kata patch, which dropped Apocalypse's 8 loot injections each) and `02E_Scrolls 0905A5` (winner was Apocalypse itself, whose override reverted EGO's rebalance — renamed EditorID, `ChanceNone` 0.5→0.15, entry trims — while adding its 4 scrolls). Each = deliberate winner's record verbatim + Apocalypse's additions re-appended. **Ownership split: Magic Patches owns these five LVLIs; `KataFixes` owns the three vendor chests — neither plugin may touch the other's records.** Since 2026-08-27 also the **Triumvirate cost-ladder repricing + fever tax** (the Triumvirate — Enderal Conversion v1.0.0 deliberately ships Enai's costs untouched, and its master FF tier ran ~10× EGO's ladder: live medians 46/82/168/356/1207): 75 overrides from `05-build-triumvirate-cost-table.py` (tier from Enai's own `TVR_<Arch>_<School><Tier>_` EditorID encoding — known outlier `TVR_Cleric_R025_Spell_Aura_1` carries a shared skill-75 proc) + `06-apply-triumvirate-cost-table.ps1` + `07-add-triumvirate-fever.ps1`, which taxes its three self-heals: Aura of Vigor gets EGO's whole Boon fever block copied verbatim (`106EA4` 0.25/s + the two Mental-perk-conditioned `0083D3:EGO` variants — the magnitude is NOT tunable, `106EA4`'s description bakes in "0,25% per second"), Mass Immortality `11A4B6`@5 (King's Heart/Panacea ceiling), Spirit of the Sun `11A4B6`@10. Drains, fortifies and Aura of Thorns' scripted release-heal stay untaxed, documented in 07's header. **Regeneration order: 02→03 (Apocalypse), 06→07 (Triumvirate) — the two pairs share the Spells folder and each deletes only its own mod's suffix.** **`halfCostPerk` is kept, not cleared**: 274/278 of EGO's own player spells carry the vanilla half-cost perks, so they are live in Enderal's cost system. Masters now eight: base three + `KataPUMBSpellPack.esp` + EGO + Apocalypse + `EGO - KataPUMB Spell Package.esp` + `Triumvirate - Mage Archetypes.esp` — **which forces Magic Patches to load AFTER Triumvirate (319 in the Alpha 0.3 order, i.e. after our old slot 292); move it when deploying** |
| `KataFixes` → `Zenderal - Kata Fixes.esp` | _(none used)_ | Kata-related fixes. Currently the **magic-vendor chest merge**, covering the **three** contested chests: Funkentanz `102AD5`, Torius `118050` and Tarhutie `05BCD6`. Base = `EGO SE - Leveling Redone.esp`'s record (its trims are deliberate leveling work; every other overrider is EGO-lineage without mastering LR, so their reverts of its trims are collateral — verified 2026-08-27 on Emberlord's 18 base-book carries at Funkentanz) + each loser's own-suffix additions: Kata's 15 staves per chest, xxOpenSpells' 4 books and the Emberlord patch's 5 entries at Funkentanz. 54 entries restored across the three. Derived (not hardcoded) by `src/KataFixes/tools/01-merge-vendor-chests.py` from the reference trees (`LevelingRedoneEGO`, `KataPUMB`, `xxOpenSpells`, `KataEmberlord`), which asserts every count AND fails if Apocalypse's reference tree ever overrides a foreign container again. **Until 2026-08-27 this was a SEVEN-chest merge restoring Apocalypse's 160 tomes; its Enderal Patch v1.2.0 moved all vendor stock into the `<Merchant>_CustomMerchandise` hook lists, so the four Apocalypse-only chests (Milbert `127928`, Maxus `022BF2`, Barnabas `13824A`, Ora `0F9320`) were retired — keeping them would have double-stocked every tome — and the Tarhutie novice-tome CURATION stage went with them (upstream now sells every tome deterministically at exactly one shop, Apprentice tier at Tarhutie in Riverville). Our three chest overrides are the final winners, so they MUST keep the chest's `*_CustomMerchandise` hook entry (`0302D5`/`0302FE`/`0302F7:Enderal - Forgotten Stories.esm`) — dropping it kills Apocalypse's distribution at that shop; verified present in all three.** `_00E_Test_Container_Weapons 0465BB` deliberately untouched. Eight masters incl. `EGO SE - Leveling Redone.esp` (content-unused, mastered to force load-after); `Apocalypse - Magic of Skyrim.esp` is no longer one. **Whoever owns these chest records owns them alone** — no other Zenderal plugin may override them (the RelentlessSword lesson). Also ships the recompiled `Kata_Enderal_SpellPackageAddToLLists.pex` (absorbed from the retired `Zenderal - No Kata Debug Prompt` release): kills pack 2's debug prompt AND comments out (`;ZP-DEDUPE`) the 58 `AddForm` lines injecting the **29 spell lines duplicated between the two Kata packs** — the injection is `Books.GetAt(<hardcoded index>)`, so the script is the only place it can be fixed (editing the FormList would shift every index). Dedupe reaches **new games only** (`StartGameEnabled` + `RunOnce`); the mod folder must win the loose-script file conflict with `KataPUMB Magic Package` |
| `SkipPrologue` → `Zenderal - Skip The Prologue.esp` | `0x800–0x802` | `800` Quest `ZP_SkipProlog`, `801` Activator `ZP_SkipProlog_StartTrigger`, `802` its placed trigger ref in Ark market cell `070793`. Overrides `MQ101 03372B` (alias 183 `StartMarkerRef` → `TeleportMarker_ArkMarket 0EAB74`) and forwards FS's `CapitalCityMarketArea 07072A` header — neither costs anything from the block. Lands the player awake at Jespar's camp with `MQ02` *"The Void"* running; see the note below the table for the mechanism |
| `FasterSprint` → `Zenderal - Faster Sprint.esp` | none (overrides only) | Global (player + NPC) sprint speed +20% on top of EGO's current values — overrides `NPC_Sprinting_MT` (`034D9C:Skyrim.esm`, `ForwardWalk`/`ForwardRun` 440→528) and `AIControlledNPC_Sprinting_MT` (`0F3469:Skyrim.esm`, 450→540). `BackWalk`/`BackRun`/rotation fields left untouched. Master: `Skyrim.esm` only (no EGO FormKey is referenced, only its record is overridden — but this plugin **must load after** `Enderal SE - Gameplay Overhaul.esp` in-game to win the conflict; declaring it as a master isn't required since no FormLink to it exists). See `arch-docs/zenderal-curation.md`. |
| `BrawlFixes` → *(no plugin — two recompiled scripts)* | _(none)_ | Forks SureAI's two brawl scripts, `_00E_DGIntimidateAliasScript` and `_00E_DGIntimidatePlayerScript`, which **every** brawl in Enderal runs through (NQ12 Silia Foxhand, NQ_G_04 Duul, FS_NQ06 Darius Kupferhammer, the EnvironmentScene01 drunk). Both were tripping constantly next to the list's combat framework — see the `OnHit`/`akSource` gotcha below for the mechanism and the four wrong diagnoses it cost. Two `; ZP` guards: (1) `OnHit` requires `akWeapon as Weapon` to be non-None before converting the brawl to a real fight, since the parameter is really the hit *source* and is a **Spell** for a magic hit; (2) both `OnMagicEffectApply` handlers require `MagicEffect.GetAssociatedSkill()` to be one of the five schools before flagging stage 150, because Enderal's own offensive effects all carry a `MagicSkill` and combat-framework markers carry none (**verified**: zero across `For Honor in Skyrim` + `For Honor Reforged`, 482 across base Enderal). NO Property added/removed/renamed — the quest VMAD binds `UnarmedWeapon`, `DGIntimidateFaction`, `Opponent` and `OpponentFriend` by name. Nothing else in the list ships either script loose (they live only in `E - Misc.bsa`), so no sort position is required. **Credit SureAI** |
| `NpcPotions` → `Zenderal - NPC Potions_DISTR.ini` | _(none — SPID config, no plugin)_ | **The repo's first worked example of the fourth release shape** (`"plugins": []` + a `files` block, `"to": ""`). 16 `Item =` lines distributing Enderal's three restore-consumable lines plus Ambrosia to `ActorTypeNPC` humanoids, level-banded `1/9`, `10/17`, `18/27`, `28/37`, `38` — the same 10/18/28/38 ladder as `_00ETraderPotion10/20/30`. Health `_NNE_Genesungstrank` (`0028C8`, `0028C5`, `0028C6`, `0028C7`, `0028C9` — **non-monotonic, do not sort**) at chance 55; mana `_NNE_Manatrank` (`0028DB`, `019E3B`, `090892`, `09B6CB`, `1037F7`) and stamina `_NNE_Morgenlufttrank` (`0028DE`, `085668`, `09B6CA`, `1037F5`, `1037F6`) at 45; **all count `1`** — cut from `1-2` once NUP's corpse-stripping was turned off, since nothing trims the piles any more. Ambrosia `_00E_Ambrosia 0FEC69` is a **`DeathItem =`**, count 1, chance 10 — see the NUP note below for why it is not an `Item =`. Traits `-S/-C/-D` exclude summons, children and StartsDead props. For the `Item =` lines, **chance is rolled per BASE NPC record, not per corpse, and it is all-or-nothing** — win and every instance of that base carries the item, lose and none ever do. A single low-chance line therefore reads as "never drops": Ambrosia at 12 hit 22 of 182 bases exactly as configured, but ~16 of those were townsfolk, leaving a typical fight (5–10 distinct enemy bases) a ~36% chance of yielding none. **[verified in-game 2026-08-13]** Budget per-base, not per-kill, and remember `ActorTypeNPC` is mostly civilians. **`DeathItem =` rolls per CORPSE instead**, which is the fix for that whole class of problem whenever the item is meant as loot rather than as something the NPC uses **`Morgenlufttrank` is the restore-stamina line** — `_NNE_Ausdauertrank` is *fortify* stamina and has only 2 tiers in base Enderal (a 3rd is EGO's new `0008C0`), so it is the wrong record. **Supersedes `Zenderal - Enemy Potions.esp`** — an untracked mod at MO2 priority 24 with no source in this repo, which banded the same three lines into the `_00E_MOB_Bandit` / `DeathItemDraugr` / `_00E_FS_DeathItem_Human` death-item lists; disable it or those NPCs draw from both. Unlike death items, SPID puts these in the base NPC's *live* container, so `Smart NPC Potions` and `NPCs Use Potions` will make enemies drink them — that is intentional (modern combat pillar), not a side effect. **`NPCs Use Potions` STRIPS EVERY CORPSE and will silently eat a distributed item — see the section below; this release depends on its `RemoveItemsOnDeath` being off** |
| `ControllerTweaks` → *(no plugin — three file overrides)* | _(none)_ | **The repo's first release that ships NO plugin but DOES ship a script**, and its first fork of an **Enderal** script rather than a third-party one. Adapts the Complete Controller Setup stack to Enderal, and **must sort above `Complete Controller Setup` and `Dear Diary Dark Mode`** to win the file conflicts. (1) `Interface\Controls\PC\controlmap.txt` — CCS 5.3.5's, `Quick Stats` gamepad combo (B+DpadUp, `0x2000+0x0001`) unbound to `0xff`; it opened Skyrim's vanilla perk starfield, a UI Enderal never uses. (2) `interface\skyui\config.txt` — forked from **Dear Diary Dark Mode's** copy (its wins over SkyUI's), `[Input]` gamepad sort bindings moved off CCS's equip/drop buttons: `prevColumn` 274→280 (LT), `nextColumn` 275→281 (RT), `sortOrder` 272→273 (R3), so RB-equip and L3-drop stop re-sorting the item list. (3) `Scripts\_00E_Game_SkillmenuSC.pex` — SureAI's script recompiled with four `; ZP` additions binding **B + D-pad-Up → open Hero Menu, B → close**; see the controller gotcha below for why the chord cannot live in Gamepad++. Setup, required Nexus files and the `bGamepadEnable` INI trap are in [`arch-docs/zenderal-controller-setup.md`](arch-docs/zenderal-controller-setup.md). **Credit SureAI on any mod page** — this redistributes a modified copy of their script |
| `LearningBooks` → `Zenderal - Learning Books Grant Learning Points.esp` | `0x800–0x802` | `800` MGEF `ZP_LearningPointGrantME`, `801` MGEF `ZP_CraftingPointGrantME`, `802` MSG `ZP_sCraftingPointGained`. Inverts every learning/crafting book: instead of spending a point to raise a skill (redundant — `EGO SE - Leveling Redone` provides the spend path), each book **GRANTS** +1 of its currency on read — 48 `_00E_Lehrbuch*To*` → Lernpunkte `031ACB`, 24 `_00E_Handwerksbuch*To*` → Handwerkspunkte `085A79` — via one script (`ZP_GrantPointsOnRead`, `Points.Mod(Value)` + notification; learning reuses `_00E_MQP03_sLearningPointGained 037171`). The 72 ALCH overrides are **EGO's winning records verbatim** (prices/names kept) with only `BaseEffect` swapped, generated by `src/LearningBooks/tools/01-generate-book-overrides.py` from `reference/mods/EGO` — **never hand-edit `Ingestibles/`**; `MagicEffects/`+`Messages/` are hand-authored and survive regeneration. The generator asserts 48/24 counts, that every detached MGEF carried a spend script (incl. SureAI's `_00E_Lehrboch*` typo on the four Block books), and that exactly the 8 Conjuration/Illusion books carry EGO's `LehrbuchForbidden 001FB7` keyword — which is why **EGO is a declared master** (also engine-forces load-after-EGO, required to win). New MGEFs copied verbatim from EGO's `XionHandicraftPoints 00775D` shape. **Deliberately untouched: `_00E_Erinnerungsbuch` (+1 MEMORY point — separate currency, `TalentPoints 05BCFA` + `dragonsouls` mirror), the `Plus2*` grant books, `_00E_KnowledgeBook`, FS Apotheosis books.** This plugin OWNS the 72 ALCH records — no other Zenderal plugin may override them |

> ### `NPCs Use Potions` STRIPS EVERY CORPSE — it will silently eat anything you distribute
>
> **[verified in-game 2026-08-14]** The list runs *NPCs Use Potions* (SKSE DLL + `*_NUP_DIST.ini`
> rules), and its live settings in `zenderal/overwrite/SKSE/Plugins/NPCsUsePotions.ini` ship as:
>
> ```ini
> [Removal]
> RemoveItemsOnDeath = true
> ChanceToRemoveItem = 90
> MaxItemsLeftAfterRemoval = 2
> ```
>
> Every dying NPC has its alchemy items culled — each item faces a **90% removal roll**, and at most
> **2 survive**. NUP does this on a **worker thread** (`Started RemoveItemsHandler`,
> `[TESDeathEvent] Removed item {}`), so it runs *after* anything else hooked to `TESDeathEvent`.
>
> **This cost a full diagnosis cycle on Ambrosia.** A single-count item cannot win that lottery
> against the ~6 potions the same config distributes: at SPID chance **100**, on **every humanoid
> base in the game**, Ambrosia reached **zero** corpses. The SPID log was clean and correct
> throughout — `Registered 17/17 Items`, then `[📦] _00E_Ambrosia [ALCH:000FEC69]` on base after
> base. Switching to `DeathItem =` did not help either: the log showed `[💀][📦]` delivering to all
> four test corpses and the loot was still empty, because NUP's thread strips it afterwards. Only
> `RemoveItemsOnDeath = false` made it appear, on every corpse, immediately.
>
> Generalise the *diagnosis*, not just the fix:
> - **A clean SPID log does not mean the item reached the player.** SPID reports what it distributed,
>   not what survived. Prove delivery *and* survival separately.
> - **Test at chance 100 before tuning a chance.** It converts "is it rare?" into "does it work?" in
>   one launch. Zero hits at 100% is proof of removal, not of bad luck.
> - **A rare item competing with common ones is the worst case**, because the cull keeps a fixed
>   *count*. The commons crowd out the rare even when the rare survives its own roll.
> - NUP also has `DistributePotions = true`, and Enderal's potions live in a plugin literally named
>   `Skyrim.esm` — which NUP's whitelist covers. So NUP is probably already handing out Enderal's
>   restore potions on its own, which would make our three potion lines largely redundant.
>   **Unverified** — NUP's `EnableLogging` is off; one run with it on would settle it.

> **To skip to a point in Enderal's main quest, find the SetStage that Enderal's own fragment
> already implements — do not re-author the transition.** **[verified 2026-08-09]**
> `Zenderal - Skip The Prologue` is one `SetStage` call, because `MQ01.SetStage(130)` fires
> `_00E_MQ01_Functions.CleanUp()`, which resets the timescale, opens the dam gate, unlocks the MQ01
> doors, calls `Self.CompleteQuest()`, then `MQ02.Start()` + `MQ02.SetStage(10)`. MQ02 stage 10
> (`MovePlayerAndJesparToStart`) teleports the player to `MQ02_D0_PlayersWakeUpmarker02 0C41D9` and
> Jespar to `MQ02_D0_JesparSpawnMarker 07321F`, skips to 05:30 and chains to stage 15
> (`WakeUpPlayer`) for the fade-in and the get-up idle. The earlier version of this patch walked
> MQ01→MQ02→MQ03→MQ04 by hand for the same reason and only needed the first line of it.
>
> Three things that follow, all of which are cheaper to read here than to rediscover:
> - **Quests can start themselves off dialogue.** `NQ41` *"Arcane Fever"* needs no property, no
>   `Start()` and no stage: `TIF__000C3FE4`, on Jespar's first camp topic (`MQ02_D0_4b 0C3FD6`),
>   calls `NQ41.SetStage(5)`. Likewise the class — MQ02's later Jespar topics (`146654`, `14664F`)
>   set `iPlayerClass` and call `GivePlayerSkillbook()`, so pre-setting it double-grants the
>   starting skillbooks. Grep the `TIF__*` fragments for the quest before writing any of it yourself.
> - **Arcane Fever is the actor value `LastFlattered`, negated.** MQ01's `BeginHeadache()` does
>   `ModAV("LastFlattered", -15)`, so 15 fever is what a natural arrival at MQ02 carries. The fever
>   *ability* is `_00E_MQP03_MagicFeverSpell 02506B`, added by `MQP03.StrandingCutscene()` and
>   removed by MQ04's `FinishUp()` — present or absent tells you which side of Lishari's ritual a
>   start point is on.
> - **A skipped stage's side effects stay skipped, and that is sometimes correct.** `KillFinn()`
>   never runs, so `_00E_MQ01_FinnREF 085998` stays alive at the dam camp. Do **not** "fix" that by
>   disabling him — `CleanUp()` has that exact line commented out with `; SE: Fixes "cannot disable
>   an object with an enable state parent"`. Carbos `08599A` is `InitiallyDisabled` and never
>   appears at all. Faking the prologue quests into the journal is likewise wrong: `MQP01` 40,
>   `MQP02` 75 and `MQP03` 70 all carry fragments, and `MQP03`'s is `FinishQuestAndStartMQ01`,
>   which would restart MQ01 at stage 5.
>
> The player still spawns at `TeleportMarker_ArkMarket 0EAB74` and the trigger still lives in the
> Ark market cell, because that is what keeps them out of `MQP01Home` — `MQP01` is started by a
> trigger inside that worldspace, not by `MQ101`, whose `Fragment_332` only does
> `MoveTo(StartMarkerRef)`. `BeginSkip()` then `MoveTo`s the camp marker before racemenu, so
> character creation happens at the camp with **no new cell override** — placing the trigger in
> Vyn's `01A3F5` instead would have added an exterior cell to our conflict surface for nothing.

> **When a mod has two mutually exclusive upstream builds, ship two ARCHIVES of ONE ModKey — not
> two plugins.** **[verified 2026-08-06]** johnskyrim's Relentless Sword exists as a free Nexus
> build (6 swords) and a Patreon "ZEN" build (the same 6 plus a Zen-design pair). The user owns one
> or the other, never both — the ZEN download is a rebuild of the whole mod, not an add-on.
>
> Two shapes were tried. **An add-on plugin mastering the base patch was wrong**, and its failure
> mode is the generalisable part: the base patch overrides `FlusshaimTemple 015282` (to place the
> blueprint) and `_00ETraderCraftingPlansC 148ABE` (to stock it), so *any* second plugin of ours
> touching either would win on load order and **silently delete the first patch's entry** —
> guardrail 5, turned against our own repo.
>
> The shape that works: **two releases, both emitting `Zenderal - Relentless Sword.esp`**, one with
> 33 records and one with 43. Same filename ⇒ they physically cannot both be enabled, no conflict
> is possible, and because the Zen tree copies the base records **byte-identically** and allocates
> its additions **above** them at `0x828+`, a user swapping builds keeps every FormID — swords
> already in a save survive. `manifest.json` allows this directly: two releases may share a `dest`.
>
> The cost is a duplicated YAML tree, which the build requires (it deserializes a folder), plus a
> generator to keep the two from drifting (`build-zen-tree.ps1`, which rebuilt the Zen tree from the
> base one and asserted file counts, blueprint gating and the absence of dead Skyforge refs).
>
> **This repo no longer ships that pair.** On 2026-08-16 the six-blade release and its generator
> were removed and the Zen tree was renamed `src/RelentlessSwordPatreon/`, leaving one release that
> requires the Patreon build. The note stays because the *shape* is the reusable part — and note the
> two things the retirement had to preserve: the **plugin filename** (renaming it would strand every
> sword in an existing save) and the `0x828+` allocation above the retired block.
>
> Verified on the built plugin: `MAST Skyrim.esm` + `MAST Enderal - Forgotten Stories.esm` (no
> third master), HEDR 1.7, ESL flag intact, `nextObjectId 0x832`, and all 244 FormKey references
> resolving. **That is a verified BUILD, not a verified RUN** (guardrail 8).

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
| Extract `.bsa` | `bsab.exe`, or `BSArch64.exe` (see below) | `$Tools.bsab` / `$Tools.bsarch` |
| Decompile `.pex`→`.psc` | `Champollion.exe` | `$Tools.champollion` |
| Compile `.psc`→`.pex` | `PapyrusCompiler.exe` (from Skyrim SE) | `$Tools.papyrusCompiler` |
| Open Creation Kit | `CreationKit.exe` (from Skyrim SE) | `$Tools.creationKit` |

> **`bae.exe` has no usable CLI — do not reach for it.** **[verified]** It rejects `-e`,
> `--extract` and even `--help` ("Unknown option"); the `extract` string in the binary is a Qt slot
> name, not a command-line option. It is GUI/drag-and-drop only. When `bsab` is not installed, use
> **`BSArch64.exe unpack "<archive.bsa>" "<outdir>" -mt`** (bundled in xEdit's folder,
> `$Tools.bsarch`) — it is the reliable headless extractor here. Note it **requires the output
> directory to already exist** and fails with "Folder does not exist" otherwise.

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
plugins at all. Pass the switch yourself — there is no skill that does it for you.

> **xEdit lives inside the instance now, and the release archive contains no `EnderalSEEdit.exe` —
> you make it yourself.** **[verified 2026-08-27]** xEdit **4.1.5f** is installed at
> `<modlistRoot>/Tools/EnderalSEEdit 4.1.5f/`, which is the exact path the Zenderal
> `ModOrganizer.ini` "EnderalSEEdit" entry already expected (it also passes
> `-D:"<Stock game\Data>" -enderalse`). The `.7z` from
> [TES5Edit releases](https://github.com/TES5Edit/TES5Edit/releases) ships **only** the generic
> per-family binaries — `xTESEdit64.exe`, `xFOEdit64.exe`, `xSFEdit64.exe`, plus `BSArch64.exe` and
> `Edit Scripts/`. **xEdit selects its game mode from the executable's NAME**, so
> `EnderalSEEdit.exe` and `EnderalSEEditQuickAutoClean.exe` here are plain copies of
> `xTESEdit64.exe`. Confirmed working: the running process's window title reads
> `EnderalSEEdit 4.1.5f x64`, and the binary carries `EnderalSE` as a recognised mode string.
>
> Before this, **every** `xedit`/`bsarch` path in `tools.json` pointed into
> `C:/modding/mod-projects/claudemoddev/modlist/tools/`, **which no longer exists** — that whole
> shared tools folder is gone. `tools.json` now points at the in-instance install. **`champollion`
> was in that same dead folder and is still NOT installed**; its key is blanked so `Assert-Tool`
> fails loudly. Reinstall from
> [Orvid/Champollion releases](https://github.com/Orvid/Champollion/releases) if you need to
> decompile a third-party `.pex` — Enderal's own scripts need no decompiler, `ScriptsEnderal.zip`
> is real source.

### Crash logs are written to the SKYRIM SE folder, not Enderal's

**[verified]** Crash Logger SSE (and the other SKSE plugin logs — `skse64.log`, `EnderalSE.log`,
`po3_*.log`) land in:

```
C:\Users\<you>\Documents\My Games\Skyrim Special Edition\SKSE\crash-<timestamp>.log
```

**not** `…\My Games\Enderal Special Edition\SKSE\`, which holds only the INIs and saves. Looking in
the Enderal folder and finding nothing is what makes a crash look like it produced no log at all —
it did. Read the newest `crash-*.log` by mtime and check `Working Directory:` says Enderal before
trusting it.

Two fields to read first, before the call stack:

| Field | Means |
|---|---|
| `PLUGINS: Total: 0` | crashed **during** file loading — the data handler never populated. Suspect the plugin header/masters, not records |
| `PLUGINS: Total: <n>` with a full list | plugins loaded fine; it is a content or runtime problem |

The plugin list in a `.ess` save is a second, independent source for what the engine actually
loaded — useful when the game will not start at all.

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
| **[`arch-docs/magic/`](arch-docs/magic/)** | **The actual in-game value of every magic record** — load-order-winning SPEL/MGEF/ENCH/SCRL/ALCH/SHOU/GMST as JSON/CSV, with override chains, per-field diffs and recomputed spell costs. Start any magic-rebalance work here; regenerate with the `magic-extract` skill |
| [`arch-docs/tools/spid.md`](arch-docs/tools/spid.md) | **SPID reference** — `_DISTR.ini` grammar and runtime behaviour for 7.3.x, rebuilt from upstream source. Corrects three things powerof3's [Nexus article](https://www.nexusmods.com/skyrimspecialedition/articles/6617) gets wrong |
| **[`arch-docs/tools/spid-in-enderal.md`](arch-docs/tools/spid-in-enderal.md)** | **SPID in Enderal** — what a ported `_DISTR.ini` silently loses and why. Read before installing or authoring one: the list currently registers only **198/318** keyword entries |

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

### A LIST-SHAPED record is replaced wholesale, so a late override silently deletes stock

**[verified 2026-08-11]** This is the single most productive bug class found in this list so far —
**214 entries across seven merchant chests**, every one installed, enabled and unobtainable, all
now restored by `Zenderal - Kata Fixes.esp`. Read this before authoring any patch that touches a
vendor chest, an NPC inventory or a leveled list.

The engine does not merge a Container's `Items:`, an NPC's inventory or a LeveledItem's `Entries:`.
**The last plugin to override the record supplies the entire list.** So when mod A adds 45 spell
tomes to a merchant, and unrelated mod B overrides that same merchant later for its own reasons,
A's 45 tomes are gone. This is guardrail 5 seen from the receiving end, and it is invisible: both
mods are installed, both enabled, the merchant exists and has plenty of stock, and the items are
simply not in the game. No log line, no missing master, nothing to notice.

**`EGO SE - Leveling Redone.esp` is the list's second dominant conflict source, after EGO itself.**
It sits at load order **138** — far later than the content mods — and overrides **50 containers**,
carrying none of any earlier mod's additions. It cost this list 160 Apocalypse spell tomes across
seven merchant chests, plus Kata's staves and xxOpenSpells' books.
`Zenderal - Kata Fixes.esp` now repairs all seven. Treat any record it touches as contested.

> **The load order MOVED under this analysis once already — re-read `loadorder.txt`, don't trust
> numbers written here.** **[verified 2026-08-20]** The 2026-08-11 audit saw Apocalypse at 125 and
> Leveling Redone at 166; the live Alpha 0.3 profile now has Leveling Redone at **138** and
> Apocalypse at **291** — the order *flipped*, so on any chest a Zenderal patch does not override,
> **Apocalypse's base-derived container records now win**, reverting EGO's and Leveling Redone's
> chest work. That is exactly how the "Ora Stonehand sells deprecated *Fire Ball*/*Chain Lightning*
> tomes" bug report happened: the rebuilt Apocalypse's Funkentanz/Torius/Steinschlag chest overrides
> were copied from **base Enderal's** records, which directly stock `_05E_SpellBookFireBall 08564A`
> and `_05E_SpellBookChainLightning 04DC94` — tomes teaching spells EGO renamed `*unused` with the
> "no longer used in the Gameplay Overhaul" description (EGO deliberately dropped both from its own
> chest overrides and never overrides those two Book records, so they keep the base "Fire Ball"
> spaced name). The seven-chest Kata Fixes merge already covers all three chests — but the bug
> shipped anyway because the **deployed `Zenderal - Kata Fixes.esp` was a stale 2026-08-09
> three-chest build** (no Steinschlag override): Gabrielle (Funkentanz, covered since the first
> build) looked fine while Ora (Steinschlag, added 2026-08-11) stayed broken. The auditor audits the
> *serialized source*, not the deployed binary, so it reports clean over a stale deploy — after any
> chest-merge change, verify the deployed `.esp` actually contains the new override (guardrail 7:
> `grep -c CCSteinschlag <esp>` is enough).

**Run the auditor rather than remembering this:**

```
python src/KataFixes/tools/00-audit-vendor-conflicts.py        # read-only; --all shows patched ones too
```

It reads the live load order from the MO2 profile, walks every serialized plugin under
`reference/mods/`, and reports each list-shaped record where a later plugin drops an earlier one's
entries — filtering out deliberate drops (see below) and what a Zenderal patch already covers.
**It currently reports the list clean: no collateral stock loss across 1837 records.** It only sees
what is serialized, so a silent report means "none among the trees present", **not** "none":
decompile the mod first if you are patching near it.

> **COLLATERAL vs DELIBERATE — check this before calling anything a bug.** A dropped entry is only
> a defect if **the winner does not declare the loser as a master.** A plugin cannot make a decision
> about records it cannot see. Leveling Redone masters only `Skyrim.esm`, FS and EGO, so it had no
> idea Apocalypse's tomes or Kata's staves were ever in those seven chests — pure collateral. But it
> *does* master EGO, so its Gaboff chest dropping EGO's two Gaboff-priced learning books and
> substituting the standard cheaper ones (`00775E` at 265g for `00840A` at 400g, base Enderal's
> `0CE135` for `00840B`) is the mod doing its job — as is stripping ~25 `_00E_Lehrbuch*` /
> `_00E_Handwerksbuch*` skill books off Adlerauge and the Blacksmith. It is a **leveling** overhaul
> and those are leveling items. Likewise `EGO - KataPUMB Spell Package.esp` swapping
> `_60E_XionFireNovaMythic` for its own `_60E_XionRecitalMythic`.
>
> **[verified 2026-08-11]** All five of those read as "lost stock" on a naive entry diff and all five
> are correct behaviour; the auditor's first version reported them and nearly bought a patch that
> would have fought a rebalance mod. And note the second trap inside the collateral class: a
> **substitution is not a deletion** — compare entry counts and read both records before patching.

Two more things to get right when fixing a genuine one, both easy to get backwards:

1. **Start from the WINNER's record, not the master's.** The winner's trims and value changes are
   deliberate balance work and must be forwarded.
2. **Re-append only entries whose FormKey suffix is the LOSER'S OWN plugin.** An entry carrying a
   *master's* suffix that the winner lacks is the winner deliberately deleting the master's stock —
   restoring those reverts its rebalance. Leveling Redone trims hard: it cuts Milbert from 91
   entries to 33. `src/KataFixes/tools/01-merge-vendor-chests.py` is the worked example, and it
   asserts every count so a mod update fails the build instead of shipping quietly.

**One owner per record.** Whichever Zenderal plugin overrides a contested record owns it alone; a
second one of ours touching it re-creates the exact bug (`Kata Fixes` is 303, `Magic Patches` 304,
so Magic Patches would win and wipe Kata's staves). See the ownership split in the allocations table.

## How Enderal differs (and what that breaks)

This is the section to read before assuming a Skyrim mod "just works". Each entry is a verified
mechanism plus the class of patch it invalidates.

> **Porting a Skyrim mod? Use the `skyrim-to-enderal-porter` subagent first**, before planning or
> authoring anything. It runs the kill-checks in order — form version, load-proof, SKSE build,
> masters, distribution, override collisions — and decides whether the mod is portable at all and
> whether it needs a *patch* or a *replacement plugin*. The first two checks take minutes and both
> have already cost this repo a full build-and-debug cycle when skipped.
>
> **For a spell or magic mod, follow it with `enderal-magic-porter`.** That one carries everything the
> Apocalypse port cost: the five renamed schools (Alteration is *Mentalism*, Illusion is *Psionics* —
> the intuitive pairing is wrong), rebuilding distribution when Enderal has no spell tomes at all,
> repricing onto a 20–350 range, making self-heals pay Arcane Fever, renaming the Elder Scrolls gods
> out of every string, and cutting the Daedra and Dwemer summons.

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

**The five magic schools are renamed, not replaced.** Enderal keeps all five vanilla magic
ActorValues and only changes what they are *called*. **[verified]** — read off the `AlchFortify*`
magic effects' display strings in `reference/base/Skyrim/MagicEffects/`, and corroborated by
`_00E_BookMagicDisciplines*` and the `_00E_MagicSchool*` load screens:

| Vanilla `MagicSkill` | Enderal discipline | Higher school |
|---|---|---|
| Destruction | **Elementalism** | (an art of its own) |
| Conjuration | **Entropy** | Sinistra |
| Restoration | **Light Magic** | Thaumaturgy |
| Alteration | **Mentalism** | Thaumaturgy |
| Illusion | **Psionics** | Sinistra |

> Note the last two: **Alteration is Mentalism and Illusion is Psionics.** The intuitive pairing
> (Illusion→Mentalism) is wrong, and getting it backwards mis-files every spell in a magic patch.

The consequence is good news for ported spell mods: a Skyrim spell's `MagicSkill`, magicka cost and
skill scaling all work unchanged in Enderal. What does *not* carry over is anything user-visible
that names a school — spell tomes, load screens, descriptions — because the player has never heard
of "the School of Conjuration". Enderal's own magic metaphysics vocabulary, for rewriting those
strings, is the **Sea of Eventualities** (mages "manifest an eventuality"), **Lost Ones** (its
undead), and the two higher schools above. All from `_00E_BookMagicDisciplines*`.

**Enderal-only systems to look for** before touching anything nearby (script names verified in
`ScriptsEnderal.zip`): Arcane Fever (`_00E_FS_AlchAddArcaneFever`), Phasmalism/Apparitions
(`_fs_phasmalist_controlquest`, `_00E_Phasmalist_*`), the affinity system inside
`_00E_Game_SkillmenuSC`, memory/learning points (`_00E_Lehrbuch_Plus1MemoryPointSC`,
`_00E_Lehrbuch_Plus2SkillPointsScript`), crafting books (`_00E_Handwerksbuch*`), and the
talent cooldown/control quests (`_00E_Game_TalentControlSC`, `_00E_Game_TalentCooldownSC`).

> **Enderal taxes healing MAGIC, not healing — so a ported healing spell is free money unless you tax
> it.** **[verified 2026-08-03]** Only 11 of base Enderal's 837 spells raise Arcane Fever and every
> one is a self-heal (the `_NNE_SpellBoon` and `_NNE_SpellFlashHeal` lines), plus FS's Mystical
> Panacea and two Boon scrolls. Nothing else in the game raises it — a master-tier damage spell costs
> zero, so a ported one costing zero is *correct*.
>
> **Enderal DOES have healing potions**, and none of them costs Fever: five tiers of
> `_NNE_Genesungstrank` (`01E` `0028C8` → `05E` `0028C9`, 36 → 160 HP over 4 s, 25 → 190 gold) plus
> `_00E_Medicine` `07071F`. **[verified]** So the design is a trade — potions are the finite,
> gold-priced heal and magic is the renewable one that costs Fever instead. This repo asserted the
> opposite ("Enderal has no healing potions") for a while, from an English-only name search;
> Enderal's EditorIDs are German and `Genesungstrank` displays as *"Health Potion (Cheap)"*. **Search
> `reference/base/Skyrim/Ingestibles/` by effect FormKey, not by English name.**
> Attach `11A4B6:Skyrim.esm` (`_00E_IncreaseArcaneFeverFFSelf`, FireAndForget/**Self**) as an extra
> effect item with `Magnitude` + `Duration: 1`; its script applies the Mental Expert reduction for
> you. Concentration casts need `106EA4` paired with FS's `02F42E` instead. Price against Enderal's
> own ceilings — **26 HP per fever point burst, 78 over-time** — and note that Enderal charges a
> *flat* cost per line, so HP-per-point improves with tier. **`11A4B6` is Self-delivery and has zero
> precedent on an Aimed spell across 370 non-Self spells**, so leech/drain heals cannot be taxed this
> way. Full mechanism and the worked example in
> [`crafting-alchemy-economy.md`](arch-docs/enderal/crafting-alchemy-economy.md#arcane-fever); the
> worked example is `src/Apocalypse/tools/09-arcane-fever-heals.ps1` in the
> [`enderal-mods`](https://github.com/whisperdealer/enderal-mods) repo.

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

**A ported mod's DISTRIBUTION is the most likely thing to be silently dead — check it first.**
**[verified]** on Apocalypse — Magic of Skyrim, whose entire loot/vendor system is inert in Enderal.
It runs a `StartGameEnabled` quest (`WB_PopulateLists_Quest`) that copies three FormLists into **54
vanilla Skyrim vendor and loot leveled lists** — and **not one of those 54 exists in Enderal**.
Neither do the five College-of-Winterhold ritual globals it gates on (`0FDE72`–`0FDE76`), nor the
`Tamriel` worldspace it places its containers in. The mod loads, its 373 spells are all present and
mechanically fine, and the player can never obtain a single one.

This generalises: **Enderal's `Skyrim.esm` is Enderal**, so a vanilla FormID is only present if
Enderal happened to keep it. Bethesda's leveled-list IDs largely did *not* survive. So for any mod
that distributes items, the port checklist is: resolve its leveled-list targets against
`reference/base/Skyrim/` **before** assuming anything else about it — a dead distribution makes every
other consideration moot. The same applies to `MenuDisplayObject`, `LoadingScreenNif`,
`FirstPersonModel` and script `Object` properties, all of which are commonly vanilla FormIDs that
Enderal lacks.

> **A vanilla FormID that survived may be a completely different record — check what a ported mod
> OVERRIDES, not just what it references.** **[verified]** Apocalypse overrides exactly one Enderal
> record, and it is worldspace **`00003C`**. In Skyrim that is `Tamriel`; **in Enderal it is
> `MQP01Home`**, the prologue house. Its override stamps Tamriel's `MaxHeight` grid and map bounds
> over a `SmallWorld` interior-ish worldspace, drops `Parent: Vyn`, `Location` and the
> `SmallWorld`/`CannotFastTravel` flags, and gives the persistent cell a `Regions` list of five
> FormIDs — **four absent from Enderal, and the fifth (`041449`) is `_00E_Ark_1024WallRound01`, a
> Static.** The rebuilt `Apocalypse - Magic of Skyrim.esp` forwards Enderal's own record back (from
> **Forgotten Stories**, which also overrides it — guardrail 5).
>
> Generalise the *check*, not the fix: for any ported mod, list every record it overrides whose
> FormKey suffix is `:Skyrim.esm` / `:Update.esm` and confirm the Enderal record at that ID is the
> same record type **and the same thing**. A script that maps FormID → record group for both trees
> does this in seconds. Note this override was **not** the crash it looked like — it is a real
> defect, found while chasing an unrelated bug, and worth fixing on its own merits.

**Enderal's own distribution slots**, for re-homing a ported mod's items **[verified]**
(`reference/base/Skyrim/LeveledItems/`). Note Enderal has **no spell tomes at all** — it teaches
spells from `_01E_SpellBook*` Books:

| Purpose | Lists | Level bands |
|---|---|---|
| Spell books, vendor | `_00ETraderSpellBooksLevelA/B/C/D` = `118209` / `11820A` / `1376C8` / `14479B` | 1–12 / 1–18 / 14–40 / 30–55 |
| Spell books, loot | `_00E_SpellBooksLootA/B/C/D` = `13798C` / `13798D` / `1447A2` / `1447A3` | 1–7 / 10–18 / 18–33 / 30–55 |
| Scrolls, loot | `00E_ScrollsLowChance` = `0905A5` | 1+, `ChanceNone: 0.5` |
| Crafting blueprints, vendor | `_00ETraderCraftingPlans` / `…PlansB` / `…PlansC` = `137A06` / `148ABD` / `148ABE` | 1 / 10+ / 19–30 |

> **`(Rank N)` on an Enderal spell tome is an upgrade chain, not a power tier — do not add it to a
> ported mod's tomes.** **[verified]** Enderal ships the *same spell* at six strengths, and the record
> prefix is the **player level** each unlocks at: `_01E_SpellBookFireBolt` = *Spell Tome: Firebolt
> (Rank I)* at level 1, then `_10E_` (II), `_18E_` (III), `_28E_` (IV), `_38E_` (V), `_48E_` (VI) at
> levels 10/18/28/38/48. So "(Rank I)" promises the player a Rank II of that exact spell exists.
>
> Enderal follows its own rule: **13 of its 201 spell tomes carry no suffix** — Clairvoyance, Mark,
> Return, Telekinesis, Detect Life, Detect Dead, the three Wall spells, the ghostly summons, Death
> Storm — precisely the spells that exist at one strength only. A ported spell with a single version
> therefore belongs in that group, unsuffixed. Apocalypse's tomes ship as `Spell Tome: <name>` for
> this reason; it looks inconsistent next to Enderal's and is in fact the consistent choice.

**Inject, don't rewrite.** Add entries to the host list pointing at your own sublist, and carry
every existing entry through untouched (guardrail 5). One new LeveledItem per tier keeps the diff
readable and leaves Enderal's own list contents byte-identical.

> **But one entry is not enough — weight it, or your items are statistically invisible.**
> **[verified in-game 2026-08-02]** A host list picks **one entry per draw**, so a single injected
> entry gives your entire sublist the same odds as one of Enderal's individual books, no matter how
> many items are behind it. Apocalypse's 160 tomes sat behind one slot in `_00ETraderSpellBooksLevelA`
> (15 entries): even Tarhutie, the richest spell vendor at 8+10+10 draws, worked out to **~1 Apocalypse
> tome out of ~28 books**, and Milbert at 3+4 draws expected **0.3** — i.e. usually none. The
> distribution was correct and looked completely broken.
>
> Do the arithmetic before shipping: `draws x (your entries / entries at or below player level)`.
> Duplicating the injected entry — same `Level`, same `Reference` — is the lever, because it still
> touches none of Enderal's own entries. `enderal-mods`' `src/Apocalypse/tools/06-weight-distribution.ps1` tops each
> injection up to a target multiplicity and is idempotent.
>
> Two traps when picking that multiplicity, both found by measuring rather than reasoning:
> **`ChanceNone` does not dilute your share** — it gates whether the list yields anything at all, so
> a loot list does *not* need a higher weight to compensate. And **a list whose band takes only one
> of your sublists ends up on half the share of its neighbours**, so weight per *list*, not per
> injection: Enderal's `…LevelB` / `…LootB` bands admit one Apocalypse rank where A/C/D admit two.
>
> Two things that make this look like a bug when it is not: vendor stock is **cached in the save**
> (`iDaysToRespawnVendor: 2`, so a merchant only re-rolls every 2 in-game days), and
> `player.additem <LVLI FormID> 1` **resolves a leveled list on the spot** — that command is the way
> to prove distribution works without waiting or starting a new game.

> **Weighting has a ceiling: a leveled list makes an item AVAILABLE, never FINDABLE.** **[verified
> in-game 2026-08-02]** A list is rolled per draw, so *which* of your items a shop has is random
> every restock. With 160 tomes behind one sublist, even at a healthy 38% share of a big vendor's
> spell stock, most of the 160 were purchasable **nowhere**, and a player hunting one named spell had
> no route to it at all. Two rounds of weighting did not fix that, because it is not a weighting
> problem.
>
> **If every item must be reachable, place it directly** — write the item into a named merchant's
> `Container` record as an ordinary `Items:` entry. Deterministic, restocks forever, and a player can
> be told where to go. Enderal's spell merchants, ranked by the gold in their chest (the natural
> wealth ladder for tiering what each one sells) **[verified]**:
>
> | Chest | FormKey | Gold | Shop |
> |---|---|---|---|
> | `_00E_Merchant_CCFunkentanz` | `102AD5` | 1800 | Ark, Emberlord and Fireflash (`coc CapitalCityMagierkram`) |
> | `_00E_Merchant_STTurious` | `118050` | 1430 | Sun Temple, Torius Flameling (`coc SuntempleAlchemy`) |
> | `_00E_Merchant_UC_Barnabas` | `13824A` | 1050 | Undercity, Barnabas (`coc UndercityBarracks2Barnabas`) |
> | `_00E_Merchant_CCSteinschlag` | `0F9320` | 980 | Ark, Ora Stonehand |
> | `_00E_Merchant_MaxusTabbakus02` | `022BF2` | 620 | Duneville, Maxus Tabbakus |
> | `_00E_Merchant_CCMilbert` | `127928` | 530 | Ark, Milbert Foxhand |
>
> Richer merchants exist (`Nordwind_Traveller_01` 3700, `Rhalata_SisterEnvy` 2700, `DunenhaimKarymea`
> 2700) but draw from only 1–2 spell lists, so they read as incidental rather than as mage shops.
>
> **Reprice what you distribute — Enderal's gold scale is much flatter than Skyrim's.** **[verified]**
> Enderal's *entire* spell-tome range is **20–350**, with two outliers (Paralyze Rank II 400, the
> unique Death Storm 600); scrolls run **10–100** with two at 500. Vanilla Skyrim's tome ladder is
> ~50/175/330/700/1300, and a ported mod carries it in silently — Apocalypse's masters sat at a 1407
> median, 5.6x Enderal's dearest tome, and its X-school scrolls at 2500. For scale, Enderal's
> *unique weapons and armour* run 1100–4000, so a Skyrim-priced master tome costs about what a unique
> greataxe does. Rescale by a **per-tier ratio** rather than a flat value so the author's ordering
> inside each tier survives, and let tiers overlap at the edges — Enderal's own do.
> **Forgotten Stories overrides all of these**, so copy the FS record, not base Enderal's (guardrail 5).
>
> **Check what else overrides the chest before claiming it.** `KataPUMBSpellPack.esp` adds the same 15
> staves to `CCFunkentanz`, `STTurious` and `FlusshaimTarhutieContainer`, and those three shops are
> their only vendor. **[verified]** A plugin loading after it that overrides one of those chests
> without mastering it silently deletes them. Where a mod repeats an identical set across several
> chests, **sparing one chest preserves the whole set** — that is why `Apocalypse` leaves Tarhutie
> alone and hosts its Apprentice tier at Maxus Tabbakus (620 gold vs Tarhutie's 630) instead.

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

- **Standalone xEdit reads its OWN configured game path, not `tools.json`'s `gameDataDir`.**
  **[verified]** On this machine `tools.json.gameDataDir` is `E:/Zenderal/Stock Game/Data` (the MO2
  instance's self-contained copy), but launching `EnderalSEEditQuickAutoClean.exe`/`EnderalSEEdit.exe`
  directly (bypassing MO2) reads `EnderalSEEdit_log.txt`'s own `Using Enderal Special Edition Data
  Path:` line — which pointed at a completely different, genuinely separate Steam install,
  `E:\Steam\SteamApps\common\Enderal Special Edition\Data\`, apparently configured the one time
  someone ran the tool standalone in the past. Staging a built plugin into `$Tools.gameDataDir` and
  then running xEdit standalone silently does nothing — the QuickAutoClean process reports exit 0
  but never touches the file, because it never looked in that folder. **Check the tool's own log file
  in its install folder for the actual `Using ... Data Path:` line before staging anything**, don't
  trust `tools.json` alone for this specific step. Both paths share the same
  `C:\Users\frien\AppData\Local\Enderal Special Edition\Plugins.txt` load order, confirming the Steam
  folder is the real live target MO2's USVFS overlays onto when launched normally.
  **The reliable defence is to stop relying on the tool's remembered path at all: pass
  `-D:"<data dir>"` on the command line every time**, which is what the instance's MO2 entry does
  (`-D:"…\Stock game\Data" -enderalse`). The paths above are from an older machine state and the
  fresh 4.1.5f install has no remembered path yet — so set it explicitly rather than discovering
  which folder it picked. **[verified 2026-08-27]**
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
- **`bGamepadEnable` lives in `[MAIN]` of `EnderalPrefs.ini`, not `[Controls]` — and the list ships
  it `=0`.** **[verified in-game 2026-08-16]** The launcher-style `[Controls]` placement is ignored;
  the game-written INI puts the setting in `[MAIN]` (next to `bSaveOn*`/`bCrosshairEnabled`), and
  only a value there takes effect. Bethesda's INI reader is section-scoped, so a right-named key in
  the wrong section fails silently. Three companion facts from the same diagnosis: (1) the **live**
  INI is the MO2 profile's copy (`profiles/<profile>/EnderalPrefs.ini`, `LocalSettings=true`), and it
  wins even through PrivateProfileRedirector — proven by A/B: Documents=0 + profile=1 → pad works;
  (2) engine 1.5.97 is one-input-at-a-time (gamepad mode locks out the mouse and vice versa) — the
  *Auto Input Switch* SKSE mod is the switcher, and its current Nexus build is AE-only, rejected by
  SKSE 2.0.20 as `does not appear to be an SKSE plugin` (no `SKSEPlugin_Query` export — the quick
  binary test for any DLL); a 1.5.97 build exists in the mod's old files / the mod-166519 backport;
  (3) an XInput pad's health is testable outside the game — poll `XInputGetState` slot 0 from
  PowerShell before blaming the game. Controller stack in the list: Complete Controller Setup's
  `controlmap.txt` wins the 3-way conflict (over Gamepad++ and Modern Toggle Walk-Run Fix), and its
  eight required mods are all present. Two follow-up fixes live as in-place edits that a mod
  reinstall reverts: CCS's controlmap has `Quick Stats`' gamepad combo (B+DpadUp) unbound → `0xff`
  (it opened Skyrim's vanilla perk starfield, which Enderal never uses), and **SkyUI's gamepad sort
  bindings are NOT in any MCM — they live in `interface\skyui\config.txt`, whose winning copy is
  Dear Diary Dark Mode's**, edited to CCS's scheme (prevColumn 274→280 LT, nextColumn 275→281 RT,
  sortOrder 272→273 R3) so RB-equip and L3-drop stop re-sorting the item list. Third file in that
  mod: a recompile of **SureAI's `_00E_Game_SkillmenuSC`** binding **B + D-pad-Up → Hero Menu, B →
  close** (four `; ZP`-marked additions: `ZP_iGamepadModifier` 277/B, `ZP_iGamepadOpenKey` 266/D-pad
  Up, a held-flag, an `OnKeyUp` event, two `RegisterForKey` calls, and the chord in the existing
  `OnKeyDown`). **A GAMEPAD CHORD MUST LIVE IN A SCRIPT THAT STAYS REGISTERED — do not route one
  through Gamepad++.** **[verified in-game 2026-08-16, the expensive way]** Gamepad++ *can* emulate
  a keyboard key on a combo (`Input.HoldKey`) and it works in gameplay, but it **goes inert while
  any menu is open**, so nothing it binds can ever *close* a menu — the Hero Menu could only be
  shut with Esc. (Its `OnMenuOpen` guard `if !MenuName == "FavoritesMenu"` *looks* like a
  precedence bug that would keep it live; the observed behaviour says otherwise, so trust the
  test.) Two further reasons the script is the right home: Gamepad++ **stores its bindings IN THE
  SAVE**, reloading its `.gppd` only via MCM → Info → "Reset to Defaults" — so editing that file
  changes nothing in an existing save, and a distributed list would need every user to press it —
  and the script route needs no MCM step at all. If you ever do edit a `.gppd`, note its JSON order
  is **[single, double, triple, LONG press] per D-pad direction**, not the Papyrus array's index
  order (`i*4 + iMultiTap`) — read `gpp_mcm_combo_one.psc`'s `saveData()` first. Enderal's other
  script hotkeys (Meditate, Phasmalist teleport, Horseflute) are listed in `_00e_enderalmcm.psc`
  and can take the same treatment; **`_00E_Game_SkillmenuSC` compiles clean from SureAI's source**
  with the standard three-tree `-i` order, and `UIExtensions`/`UIListMenu` are already inside
  `reference/base/EnderalScripts`. Note there is **no free gamepad button** left in this layout to
  bind Enderal's MCM hero-menu key to instead: X is Wheeler's `toggleWheel`, LT is Dual Wield
  Parrying, and the four D-pad long-presses are Stances (`[ ] ; '` = 26/27/39/40). Also: CCS ships
  its own `gpp_keyhandler.pex`/`gpp_mcm_*.pex` that **override Gamepad++'s** — diffing the `.pex`
  string tables shows the only change is the version-nag `Debug.MessageBox` calls stripped, so
  Gamepad++'s `.psc` source is still accurate for reading. **`.pex` is BIG-ENDIAN** — a
  little-endian string-table reader fails immediately.
- **`OnHit`'s second parameter is the hit SOURCE, not a weapon — and a modern combat
  framework makes it a Spell on every single blow.** **[verified in-game 2026-08-28, after
  four wrong diagnoses]** The signature reads `OnHit(ObjectReference akAggressor, Form akWeapon,
  Projectile akProjectile, …)`, but that `Form` is a `Weapon` for a swing and a **`Spell`** for a
  magic hit. Any script testing it as *"the source exists and is not X"* therefore fires on every
  spell that lands. Enderal's brawl script does exactly that:

  ```papyrus
  if akProjectile || (akWeapon && akWeapon != UnarmedWeapon)   ; "the player swung a weapon"
      pPlayer.RemoveFromFaction(DGIntimidateFaction)
      pActor.RemoveFromFaction(DGIntimidateFaction)
      pActor.StopCombat()  /  SendAssaultAlarm()  /  StartCombat(pPlayer)
      GetOwningQuest().SetStage(150)
  ```

  `For Honor Reforged` casts `HitFrameTriggerSpell 000803` at the target on **every landed hit**
  (`ReforgedParryController`'s unconditional `ApplyCombatHitSpell` entry), plus
  `Parry Knockdown Spell 000836`, `ParryStaggerKnockdownSpell 0008B1` and `SP_Stagger_Parry 00082F`
  on a parry — and **none of those effects carries the `NoHitEvent` flag**, so `OnHit` fires. Result:
  the brawl ran its full "you cheated" teardown on every punch, and the `StopCombat()`/`StartCombat()`
  pair restarted combat on an **Essential** actor, snapping her health back to full. Fix is a type
  check: `akWeapon as Weapon` is `None` for a spell. Three things to generalise:
  - **`NoHitEvent` on an MGEF is what stops a marker spell reaching `OnHit`.** Auditing a combat
    mod's spells for its *absence* is the fast way to find which of them will trip host scripts;
    `MagicEffect.IsEffectFlagSet` and the serialized `Flags:` list both show it.
  - **A parry/block payload fires in FIRST person too**, because blocking is a shared behaviour —
    unlike an OAR move-set, which is third-person only. "It only happens in third person" is
    therefore evidence about *move-sets*, not about the whole framework, and reading it as the
    latter cost a whole diagnosis here.
  - **Take the player's animation report literally.** "The animation for going from normal to fists
    ready was playing" *was* the `StopCombat`→`StartCombat` round trip, and it identified the guilty
    function faster than four passes over the records did. An actor visibly leaving and re-entering
    combat means something called those two.

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

> ### THE FORM-VERSION CEILING: Enderal will not load a plugin whose `HEDR` version is 1.71
>
> **[verified in-game 2026-08-02. Read this before porting any Skyrim mod.]**
>
> Enderal SE runs SSE **1.5.97**, and that engine **silently refuses any plugin written at `HEDR`
> form version 1.71**. No warning, no log entry, no missing-master dialog — the plugin is simply
> absent from the game. `HEDR` 1.70 is the ceiling; 1.71 is what the 1.6/AE-era Creation Kit and
> newer tools emit.
>
> **BUT: the Zenderal modlist lifts this ceiling with BEES.** **[verified in-game 2026-08-08]**
> The list ships **Backported Extended ESL Support** (Nukem, Nexus 106441, v1.2.0.0 — SKSE plugin,
> `mods\Backported Extended ESL Support\`), which replicates SSE 1.6.1130's plugin-loading code on
> 1.5.97 so 1.71 plugins load normally. Proof from a live run:
> `Documents\My Games\Skyrim Special Edition\SKSE\BackportedESLSupport.log` logs
> `Emulated old header version for <plugin>` for **exactly the 68 plugins** an independent HEDR
> scan of the profile found at 1.71 (`DynDOLOD.esp`, the `Pretty * Armory` set, `ForHonorBFCO.esp`,
> `Smart_NPC_Potions.esp`, …). BEES was added to the list on 2026-08-08 — *after* the 2026-08-02
> ceiling verification; both observations were correct when made.
>
> Consequences: (a) everything below still applies verbatim to a BEES-less Enderal install, to
> plugins WE author (keep writing `Version: 1.7` — do not make Zenderal patches depend on BEES),
> and to debugging reports from users who dropped BEES; (b) inside *this* list, a 1.71 third-party
> plugin is **not** inert — the "five inert `thepath` plugins" note below describes a list without
> BEES, so audit any Enderal list for 1.71 **or** for BEES; (c) BEES
> is now load-bearing — removing it silently disables 68 plugins. `arch-docs/magic/` datasets mark
> every record whose winner needs it (`winnerNeedsBees`), and the `magic-extract` tool hard-fails
> if 1.71 plugins are present without BEES.
>
> **Proof:** `Apocalypse - Magic of Skyrim.esp` is 1.71. With it enabled, `help wither 4` in the
> console finds nothing, though the mod defines a spell whose EditorID and name both contain
> "Wither". Change **four bytes** — the `HEDR` version float at file offset 30 — from 1.71 to 1.70,
> leave every other byte identical, and the spell appears. Single variable, both directions.
>
> **How this presents, and why it is so hard to spot:**
>
> - The mod appears installed and enabled. MO2 is happy. The game launches.
> - Nothing it adds exists. `help <anything> 4` finds none of its records.
> - **A patch that masters it crashes the game**, because the patch loads, tries to bind to a master
>   the engine skipped, and dereferences null during data load:
>   ```
>   EXCEPTION_ACCESS_VIOLATION  SkyrimSE.exe+05E1F22   mov rdx, [rax+0x158]   rax = 0
>   PROBABLE CALL STACK: ... InitTESThread
>   PLUGINS: Light: 0  Regular: 0  Total: 0      <-- data handler never finished
>   ```
> - Setting the *patch* to 1.71 makes the crash disappear — because the patch is now skipped too.
>   **That is a false fix and it was shipped once.** A crash that vanishes because both plugins
>   became invisible looks exactly like a crash that was fixed.
>
> **Check `HEDR` before you plan anything.** Read the float at offset 30 of the `.esp`
> (`enderal-mods`' `src/Apocalypse/tools/verify-plugin-structure.ps1` prints it, or read the four
> bytes directly). If it is 1.71:
>
> - a patch plugin **cannot** work — the only route is to rebuild the mod's own plugin at 1.70,
>   which means shipping a modified copy under the same filename (keeps its BSAs loading). Check the
>   author's permissions first.
> - when authoring with Spriggit, set `ModHeader.Stats.Version: 1.7` **explicitly**. Mutagen's
>   default is **1.71**, so a plugin that never mentions the field builds itself invisible.
>
> **This is not rare.** Five other plugins in the `thepath` modlist are 1.71 and therefore inert:
> `CS Light.esp`, `DynDOLOD.esp`, `Enderal Weather - HDR.esp`, `standard_lighting_templates.esp`,
> `TerrainHelper.esp` — most of a visuals layer, loading nothing, with no error anywhere. Audit any
> Enderal list for this.

> ### Debugging a load crash: bisect the PLUGIN, not the records
>
> **[verified — learned the expensive way on the Apocalypse patch.]** When a patch crashes the game
> at load, the instinct is to suspect the records. Six record-level hypotheses were tested and all
> six were wrong, because the cause was in the 24-byte header. **Run the cheap controls first, in
> this order** — each is one launch and each halves the search space:
>
> 1. **Empty plugin.** Hand-write a valid TES4 with no masters and no records under the same
>    filename. If that crashes, nothing you authored is involved.
> 2. **Masters only, no records.** Add the real master list, still zero records. This separates
>    "header/masters" from "content" in one launch.
> 3. **Bisect the master list**, then the header fields (`HEDR` version, flags), then records.
>
> `scratchpad/make-masters.ps1`-style hand-built plugins are better than toolchain output here
> precisely because they remove the toolchain as a variable. Also: **isolate one variable per
> launch** — an early run changed the ESL flag and the record set together and proved nothing.
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
