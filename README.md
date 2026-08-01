# zenderal-patches

The patch plugins for **Zenderal** — an [Enderal: Forgotten Stories (Special Edition)](https://www.nexusmods.com/enderalspecialedition)
modlist aiming at **bug fixes**, **modern combat** and **modern visuals** — plus the curation docs
that record what the list does and why.

This is **not** the modlist. It is the workspace where the list's compatibility and bugfix `.esp`
files are authored, built and released. It uses
[Spriggit](https://github.com/Mutagen-Modding/Spriggit) to convert Bethesda plugin files to and from
human-editable YAML kept under git, and adds a command-line Papyrus toolchain, a manifest-driven
FOMOD build, GitHub Actions CI, and a set of Claude Code skills and subagents that know how to drive
all of it. **You edit the YAML, not the binary plugin.**

- **Game:** Enderal: Forgotten Stories (Special Edition), on the SkyrimSE engine
- **Spriggit game release:** **`EnderalSE`** — *not* `SkyrimSE` ([why](#why-enderalse))
- **Spriggit package/source:** `Spriggit.Yaml.Skyrim`
- **Spriggit version:** `0.40.0` (CLI, deliberately pinned)
- **Tool paths:** resolved from `.claude/config/tools.json` (gitignored, per-machine) — **no
  hardcoded paths in the skills.** See [Tool config](#tool-config--the-modlist) below.

> `src/` ships **empty**. There is no starter plugin; `build/manifest.json` has `"releases": []` and
> the build reports "nothing to build" and exits 0. The repo is green from the first commit. Run
> **`/mod-new-plugin`** when you have a real patch to write.

Start with **`CLAUDE.md`** — it carries the verified Enderal facts (masters, SKSE version, archive
order, Papyrus import order) that everything else assumes.

## Why `EnderalSE`

Enderal SE runs the SkyrimSE engine, so it is tempting to treat it as Skyrim. Don't.
`GameRelease.EnderalSE` is a distinct Mutagen release whose implicit **base-master set** includes
`Enderal - Forgotten Stories.esm`:

```csharp
// Mutagen.Bethesda.Core/Plugins/Implicit/Implicits.cs
EnderalSE = SkyrimSE with { BaseMasters = new ImplicitModKeyCollection(SkyrimSE.Listings.And(enderal)) };
```

It maps to `GameCategory.Skyrim`, which is why the **Skyrim** serializer package still handles it.
Keep `.spriggit`, each plugin's `spriggit-meta.json` and `tools.json`'s `spriggit.gameRelease` all
reading `EnderalSE`.

There is a matching trap on the other side: Mutagen's implicit base masters for `EnderalSE` include
the three Bethesda DLC, but **Enderal does not load them**. A plugin that masters a DLC passes every
build check here and then fails to load in-game. See CLAUDE.md → "Masters".

## Fresh clone — first-run setup

Cloning brings the skills, agents, config **template**, and docs — but **not** machine-specific
paths or any large/derived content (those are gitignored). Do this once on a new machine:

1. **Create your tool config.**

   ```powershell
   Copy-Item ".claude/config/tools.example.json" ".claude/config/tools.json"
   ```

2. **Point it at your two game folders.** Enderal SE and Skyrim SE are separate installs and you
   need both — Enderal ships **no Creation Kit and no Papyrus compiler**, so those (and the vanilla
   Papyrus source) come from Skyrim SE:

   - `gameRoot` / `gameDataDir` → your **Enderal Special Edition** folder
   - `skyrimSeRoot` → your **Skyrim Special Edition** folder
   - `papyrusCompiler`, `creationKit` → under `skyrimSeRoot`

3. **Install the Spriggit CLI** (standalone — *not* part of a modlist). Grab it from the
   [Spriggit releases](https://github.com/Mutagen-Modding/Spriggit/releases), install the .NET
   runtime if prompted, then set `spriggitCli`. See [Installing Spriggit](#installing-spriggit-locally).

4. **Install the Zenderal modlist (optional but recommended for testing).** Run
   **`/modlist-install`** — it walks you through the install, then auto-discovers tool paths into
   `tools.json`. Skip this if you'll test against a plain Enderal install.

5. **Unpack the Papyrus source trees** (only if you'll compile scripts). See
   [Papyrus scripts](#papyrus-scripts--packaging) — there are **three**, and their order matters.

6. **Verify.**

   ```powershell
   . ".claude/config/tools.ps1"
   Assert-Tool $Tools.spriggitCli     'spriggitCli'
   Assert-Tool $Tools.papyrusCompiler 'papyrusCompiler'   # if you'll compile scripts
   $Tools | ConvertTo-Json -Depth 4
   ```

   `Assert-Tool` throws on a missing/empty path — fix those before running the skills.

## Installing Spriggit locally

[Spriggit](https://github.com/Mutagen-Modding/Spriggit) converts Bethesda plugins to and from a
git-friendly text format so you can version-control patches like source code (diffs, branches, PRs).
It ships as a **CLI** (`Spriggit.CLI.exe`, what this workspace uses, needs a .NET runtime) and a
Windows **GUI**.

1. Download the CLI zip from the [Releases page](https://github.com/Mutagen-Modding/Spriggit/releases).
   Unzip it anywhere.
2. Install the **.NET runtime** if prompted on first run.
3. Set the CLI path **once** in `.claude/config/tools.json` (`spriggitCli`); every skill reads it
   from there. If you move or upgrade the CLI, edit that one file — not the skills.

The serializer itself (`Spriggit.Yaml.Skyrim`) is a NuGet package the CLI fetches on demand. The
**`.spriggit`** file in this repo pins its name, version and game release, so `deserialize`
automatically uses the exact serializer that produced the YAML — everyone builds byte-identical
plugins.

> **`0.40.0` is pinned deliberately. Do not upgrade without reading the note in `CLAUDE.md`** —
> 0.41.0 silently drops leveled-list entries carrying owner ExtraData, which is exactly the record
> shape a loot/vendor patch is made of.

## Tool config & the modlist

Every tool path the skills use lives in one place:

- **`.claude/config/tools.json`** — your machine's actual paths. **Gitignored** (per-machine).
- **`.claude/config/tools.example.json`** — committed template with documented keys.
- **`.claude/config/tools.ps1`** — dot-sourced by the skills (`. ".claude/config/tools.ps1"`) to
  expose `$Tools` (e.g. `$Tools.papyrusCompiler`) plus an `Assert-Tool` guard that fails loudly on a
  missing/empty path.

**Change a path? Edit `tools.json` — never the skills.**

The installed Zenderal MO2 instance is **hundreds of GB**, so it is gitignored (`/modlist/`,
`/downloads/`) and never committed. Use the **`modlist-install`** skill: it walks you through the
install, then probes the instance and writes the discovered paths into `tools.json`.

## The round-trip workflow

```
.esp/.esm  ──serialize──►  YAML (committed to git)  ──deserialize──►  .esp/.esm
                 ▲                                                          │
                 └──────────────── you edit the YAML ◄─────────────────────┘
```

1. **Serialize** a plugin once to create its YAML folder.
2. Edit the YAML as text (and commit it).
3. **Deserialize** to rebuild the plugin.
4. Load the rebuilt plugin in **xEdit in `-EnderalSE` mode** to verify before shipping.

## What is committed vs. ignored

| Committed (your authored work)          | Ignored (`.gitignore`)                                   |
|-----------------------------------------|----------------------------------------------------------|
| Each patch's YAML folder                | Binary plugins (`*.esp/*.esm/*.esl`)                     |
| Papyrus source `src/<PatchName>/Scripts/source/*.psc` | Compiled scripts (`*.pex`)\*, archives (`*.bsa`) |
| Each release's FOMOD stub (`build/staging/<release>/fomod/`) | Build output (`dist/`, `build/dist/`) and the derived `.esp`/`.pex` inside `build/staging/<release>/` |
| `.spriggit`, configs, docs, `CLAUDE.md` | Enderal/third-party reference decompiles (`/reference/`) |
| `arch-docs/` curation + patterns docs   | Unpacked Papyrus source (`/papyrus-source/`), the modlist (`/modlist/`), editor dirs |

**You commit source, not build artifacts.**

\* **One deliberate exception.** Compiled `.pex` are ignored by default, but a patch that ships
scripts opts its `Scripts/compiled/` folder back in through an explicit `.gitignore` rule. CI cannot
run the Papyrus compiler, so it packages the committed `.pex` as-is. This is the only build artifact
in the repo and it exists for that single reason.

## Per-plugin folder layout

Created automatically when you serialize a plugin:

```
src/<PatchName>/<pluginFolderName>/
  RecordData.yaml        # plugin header: ModKey, GameRelease (EnderalSE), masters, author, Stats.Version
  spriggit-meta.json     # { PackageName, Version, Release, ModKey }
  <RecordType>/          # one folder per record type: Weapons, MagicEffects, Quests, Perks, ...
    <EditorID> - <FormID>_<Master>.esp.yaml
```

File naming is fixed by Spriggit: `<EditorID> - <FormID>_<Master>.esp.yaml`.

## Spriggit commands (CLI 0.40.0)

Paths/settings come from `.claude/config/tools.json` via `. ".claude/config/tools.ps1"`.

### Serialize (plugin → YAML)

```powershell
. ".claude/config/tools.ps1"
& (Assert-Tool $Tools.spriggitCli 'spriggitCli') serialize `
  --InputPath   "MyPatch.esp" `
  --OutputPath  "./MyPatch" `
  --GameRelease $Tools.spriggit.gameRelease `
  --PackageName $Tools.spriggit.packageName `
  --PackageVersion $Tools.spriggit.packageVersion
```

`$Tools.spriggit.gameRelease` is **`EnderalSE`**.

### Deserialize (YAML → plugin)

```powershell
. ".claude/config/tools.ps1"
& (Assert-Tool $Tools.spriggitCli 'spriggitCli') deserialize `
  --InputPath   "./MyPatch" `
  --OutputPath  "MyPatch.esp"
```

On deserialize, `--PackageName`/`--PackageVersion` can be left blank — Spriggit auto-detects them
from the folder's `spriggit-meta.json`.

### Decompiling reference masters (lookup only)

Serialize Enderal's ESM or third-party plugins into a **gitignored** `reference/` folder so you can
grep them for FormKeys without committing them. This is how you find Enderal's own worldspace,
keyword and talent-perk FormKeys — do **not** copy a constants table out of Skyrim documentation:

```powershell
. ".claude/config/tools.ps1"
& (Assert-Tool $Tools.spriggitCli 'spriggitCli') serialize `
  --InputPath   "$($Tools.gameDataDir)/Enderal - Forgotten Stories.esm" `
  --OutputPath  "./reference/base/EnderalFS" `
  --GameRelease $Tools.spriggit.gameRelease `
  --PackageName $Tools.spriggit.packageName `
  --PackageVersion $Tools.spriggit.packageVersion
```

Or just run **`/spriggit-decompile-reference`**.

## FormKey discipline

- New records use **the patch plugin's** name as the FormKey suffix (`000801:YourPatch.esp`).
- Overrides keep the **defining master's** suffix — `:Enderal - Forgotten Stories.esm` for Enderal
  records, `:Skyrim.esm` for ones Enderal left vanilla, `:<SomeMod>.esp` for third-party.
- Masters in `RecordData.yaml` go in load order: `Skyrim.esm`, `Update.esm`,
  `Enderal - Forgotten Stories.esm`, then third-party plugins.
- **Always grep the whole workspace for a hex FormID before assigning it** (`/formkey-check`).
- ESL-flagged plugins are limited to `0x800–0xFFF` for **new** records; overrides cost nothing.

See `CLAUDE.md` for the full conventions, guardrails and gotchas, and
`arch-docs/enderal-record-patterns.md` for record shapes that build cleanly and still do nothing
in-game.

## Papyrus scripts & packaging

### Toolchain (paths from `tools.json`)

| Step | Tool | Config key |
|------|------|------------|
| Extract `.bsa` | BSA Browser CLI (`bsab.exe`) | `$Tools.bsab` |
| Decompile `.pex` → `.psc` | Champollion | `$Tools.champollion` |
| Compile `.psc` → `.pex` | Papyrus Compiler (from Skyrim SE) | `$Tools.papyrusCompiler` |
| Build `.esp` | Spriggit | `$Tools.spriggitCli` |
| Verify | xEdit **in `-EnderalSE` mode** | `$Tools.xedit` |

### The three source trees (and why order matters)

Enderal has **three** Papyrus source trees, and **55 script names exist in both Enderal's and
Skyrim's**. The compiler's `-i` path is **first-wins** (verified against this toolchain), so Enderal
must come first or you compile against vanilla signatures — which fails at *runtime*, not at compile
time.

| Order | Tree | Unpack from | `tools.json` key |
|---|---|---|---|
| 1 | Enderal (~5000 `.psc`) | `<gameDataDir>/ScriptsEnderal.zip` → `source/scripts/` | `papyrusSource.enderal` |
| 2 | SKSE (74 `.psc`) | `<gameDataDir>/Source/Scripts` (already loose) | `papyrusSource.skse` |
| 3 | Vanilla (~14300 `.psc`) | `<skyrimSeRoot>/Data/Scripts.zip` → `Source/Scripts/` | `papyrusSource.vanilla` |

`TESV_Papyrus_Flags.flg` ships only in the **vanilla** zip — that is why tree 3 must be on the path
even when you're only touching Enderal code. Unpack trees 1 and 3 anywhere; `/papyrus-source/` is
gitignored for the purpose. The `/papyrus-compile` skill assembles `-i` in this order for you.

> Enderal ships **real source** for its own scripts in `ScriptsEnderal.zip`. Read it rather than
> decompiling — Champollion output is a reconstruction with auto-named variables and lost comments.

### Pipeline

```
.bsa ──bsa-extract──► .pex ──pex-decompile──► .psc ──(edit)──► .psc
                                                                 │
   dist/<PatchName>/ ◄──package-mod──┬── .pex ◄──papyrus-compile─┘
   (install in MO2)                  └── <PatchName>.esp ◄──spriggit-deserialize
```

### Testing

Use the **`mod-deploy`** skill rather than copying by hand: it reads the destination from
`tools.json` and then *verifies* the mod landed under the exact expected folder name. A mod in a
wrongly-named folder is invisible to MO2 and the game runs happily without it, so the symptom looks
like a broken record rather than a bad path.

Then in MO2: refresh, enable the mod and its `.esp`, set load order, and launch through MO2.
**A clean compile is necessary but not sufficient — verify it actually runs in-game.**

## CI build & release (GitHub Actions)

`.github/workflows/build.yml` rebuilds every release archive on each push to `main` (publishing them
to a **timestamped pre-release**), and cuts a named GitHub Release when you push a `v*` tag. It runs
on a free `windows-latest` runner and is driven by **`build/build.ps1`** + **`build/manifest.json`**.
The build script contains no patch-specific names — everything it builds comes from the manifest, so
adding a patch means editing JSON, not PowerShell.

What CI does: download the pinned Spriggit CLI → `deserialize` every plugin's YAML into the
committed `build/staging/<release>/` (whose `fomod/` subfolder is already checked into git; only the
derived `.esp`/`.pex` are regenerated) → copy the committed `.pex` into that release's `Scripts/` →
`7z` each release into `build/dist/*.7z` → attach the archives to a GitHub Release → regenerate
`arch-docs/build-report.md`.

**An empty manifest is fine.** `build.ps1` reports "nothing to build", writes an empty report and
exits 0 without needing Spriggit or 7-Zip; the release/upload steps are skipped. A `v*` tag that
builds nothing *is* an error and fails the workflow.

**CI does NOT compile Papyrus.** The Papyrus compiler needs the licensed base-game and Enderal script
source, so each script-shipping patch's compiled scripts are **committed** at
`src/<PatchName>/Scripts/compiled/*.pex` (an explicit exception in `.gitignore`).

> **Contract:** whenever you change a `.psc`, recompile (`/papyrus-compile`) and **commit the
> updated `.pex`** — otherwise the packaged patch ships stale scripts. `build/build.ps1` fails the
> build if any `.pex` is missing, but it cannot detect a *stale* one.

Run the same build locally:

```powershell
pwsh build/build.ps1              # full build -> build/dist/*.7z + arch-docs/build-report.md
pwsh build/build.ps1 -CheckFomod  # only verify manifest <-> fomod/ModuleConfig.xml parity
                                  # (also checks installer image paths resolve + aren't progressive JPEGs)
```

To release: `git tag v1.0 && git push origin v1.0`. The **`github-release`** skill automates the
curated flow: changelog from the previous tag, promote the CI-built assets, clean up the `build-*`
tags.

**PR test builds.** `.github/workflows/pr-build.yml` runs the *same* build on every pull request and
attaches the archives as an Actions artifact named `pr-<number>-test-builds`, plus a sticky comment
linking to the run. Each push replaces the previous artifact; merging or closing the PR deletes it.
A PR that produces no archives (docs/tooling only) skips the upload and comment instead of failing.
Shared setup+build steps live in the composite action `.github/actions/build-mod-archives/`.

## Claude skills & subagents

This workspace ships Claude Code helpers under `.claude/` (committed, so they're shared). They bundle
the verified CLI paths and flags so you don't retype them.

**Skills** (invoke with `/<name>`):

| Skill | What it does |
|-------|--------------|
| `modlist-install` | Install the Zenderal modlist (gitignored) and auto-discover tool paths into `tools.json` |
| `mod-new-plugin` | **Scaffold a new patch** — YAML folder + manifest entry + FOMOD stub, buildable from the first commit |
| `spriggit-serialize` | Serialize a plugin → its YAML folder |
| `spriggit-deserialize` | Rebuild a plugin from its YAML folder (+ xEdit verify reminder) |
| `spriggit-decompile-reference` | Serialize Enderal's ESM or a third-party mod into gitignored `reference/` for lookups |
| `formkey-check` | Scan the workspace (+ `reference/`) for FormID collisions or the next free block |
| `bsa-extract` | Extract/list files from Enderal's `E - *.bsa` and friends (`bsab.exe`) |
| `pex-decompile` | Decompile `.pex` → editable `.psc` (Champollion) |
| `papyrus-compile` | Compile `.psc` → `.pex` with the correct three-tree import order |
| `package-mod` | Assemble `dist/<PatchName>/` (esp + scripts) for MO2 testing |
| `mod-deploy` | **Deploy into an MO2 instance and verify it landed** under the exact expected folder name |
| `xedit-audit` | Headless xEdit clean + "Check for Errors" pass, in `-EnderalSE` mode |
| `github-release` | Cut a curated `vX.Y.Z` release from the CI-built assets and tidy the `build-*` tags |

**Subagents:**

| Subagent | Role |
|----------|------|
| `spriggit-record-editor` | Creates/edits Spriggit YAML records following this repo's naming & FormKey conventions |
| `spriggit-formkey-auditor` | Read-only audit for collisions, dangling references, broken invariants, and in-game anti-patterns |
| `papyrus-script-engineer` | Cleans decompiled `.psc`, fixes compile errors, drives the extract→compile→package loop |

**Automatic checks.** `.claude/settings.json` registers a `PostToolUse` hook that runs
`build/Test-RecordYaml.ps1` after every edit to a Spriggit record file — a fast structural check
(tabs, BOMs, odd indentation, ESL FormID range, and whether the filename's `<EditorID>`/`<FormID>`
still agree with the contents). Run it by hand over the whole repo with:

```powershell
pwsh build/Test-RecordYaml.ps1
```

## Docs

| File | What it's for |
|---|---|
| `CLAUDE.md` | **Read first.** Verified Enderal facts, conventions, guardrails, gotchas |
| **`arch-docs/enderal/`** | **How Enderal works** — plugin architecture, progression, combat, visuals, crafting, scripting. Mined from the serialized plugins and SureAI's own source |
| `arch-docs/enderal-record-patterns.md` | Record shapes that work, and the ones that silently don't |
| `arch-docs/zenderal-curation.md` | What's in the list, why, load order, conversion hazards |
| `arch-docs/build-report.md` | Auto-generated by `build/build.ps1` — do not edit |
| `CONTRIBUTING.md` | How to propose a patch |

## Credits & licence

Enderal: Forgotten Stories is by **SureAI**. This repo contains no Enderal or Bethesda assets —
`reference/`, `papyrus-source/` and `modlist/` are gitignored precisely so none can be committed.
Tooling in this repo is licensed under `LICENSE`; the mods Zenderal installs remain under their
authors' own terms.
