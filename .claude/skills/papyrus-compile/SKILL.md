---
name: papyrus-compile
description: Compile Papyrus source (.psc) into bytecode (.pex) for Enderal SE using the Creation Kit's command-line PapyrusCompiler.exe, with the correct Enderal-first import order. Use when the user wants to build/compile scripts without opening the Creation Kit GUI.
---

# Compile .psc → .pex (PapyrusCompiler.exe)

Compile Papyrus source to the `.pex` the game loads — from the command line, no CK GUI needed.

## Tool (from config)

- `$Tools.papyrusCompiler` — from `.claude/config/tools.json` (loaded via `.claude/config/tools.ps1`).
  **Enderal ships no compiler**; this comes from a Skyrim SE install, normally
  `<skyrimSeRoot>/Papyrus Compiler/PapyrusCompiler.exe`. That is correct — Enderal SE *is* the SSE
  engine.
- Usage: `PapyrusCompiler <object|folder> [args]`
  - `-all|a` compile every `.psc` in the folder (treat the positional arg as the folder)
  - `-import|i="<dir;dir;…>"` import directories (where referenced scripts' source lives)
  - `-output|o="<dir>"` output directory for `.pex`
  - `-flags|f="<file>"` user-flags file (`TESV_Papyrus_Flags.flg`)
  - `-optimize|op`, `-debug|d`, `-quiet|q`

## The import order is the whole point — get it right or nothing else matters

Enderal has **three** Papyrus source trees, and **55 script names exist in both Enderal's and
Skyrim's** (`critter.psc`, `dgintimidateplayerscript.psc`, `dragonactorscript.psc`, the `default*`
handlers, …).

**The compiler's `-i` path is FIRST-WINS** — verified directly against this toolchain by putting a
deliberately broken copy of a script in the first import dir and a good copy in the second: with
`-i="broken;good"` the compile **failed**; with `-i="good;broken"` it **succeeded**. So:

```
-i="<your source>;<papyrusSource.enderal>;<papyrusSource.skse>;<papyrusSource.vanilla>;<importDirs…>"
```

Getting this backwards compiles against **vanilla signatures**, which fails at *runtime*, not at
compile time — there is no error to see.

> SureAI's `How to modify Enderal scripts.txt` (in `ScriptsEnderal.zip`) says the sources "must be
> loaded in the following order: Creation Kit scripts, SKSE scripts, Enderal scripts". That is
> **precedence** order (last wins) for the CK's source-folder list — the **reverse** of `-i` order.
> Both mean the same thing: Enderal's copy must be the one used. Do not paste that order into `-i`.

## ONE-TIME setup (required before first compile)

Two of the three trees ship zipped. Unpack each once and record the path in `tools.json`.
`/papyrus-source/` is gitignored for this purpose.

| Key | Unpack from | Notes |
|---|---|---|
| `papyrusSource.enderal` | `<gameDataDir>/ScriptsEnderal.zip` → its `source/scripts/` | ~5000 `.psc`, Enderal's real source |
| `papyrusSource.skse` | `<gameDataDir>/Source/Scripts` | 74 `.psc`, already loose in an Enderal install — nothing to unpack |
| `papyrusSource.vanilla` | `<skyrimSeRoot>/Data/Scripts.zip` → its `Source/Scripts/` | ~14300 `.psc` **and** `TESV_Papyrus_Flags.flg` |

**The flags file only exists in the vanilla zip.** Neither Enderal tree contains one, so the vanilla
tree must be on the path even when you are only touching Enderal code — that is how
`-f=TESV_Papyrus_Flags.flg` resolves.

Check each key before unpacking; if the folder already exists and has `.psc` files, skip it.

## Steps

1. Compile all source in `src/<PatchName>/Scripts/source/` into `src/<PatchName>/Scripts/compiled/`.
   Paths come from the config; `$Tools.importDirs` (extra API source dirs) are appended last:

```powershell
. ".claude/config/tools.ps1"
$compiler = Assert-Tool $Tools.papyrusCompiler 'papyrusCompiler'
$src      = "src/<PatchName>/Scripts/source"

# ORDER MATTERS - first wins. Own source, then Enderal, then SKSE, then vanilla, then extras.
$imports = @(
    $src,
    (Assert-Tool $Tools.papyrusSource.enderal 'papyrusSource.enderal'),
    (Assert-Tool $Tools.papyrusSource.skse    'papyrusSource.skse'),
    (Assert-Tool $Tools.papyrusSource.vanilla 'papyrusSource.vanilla')
) + @($Tools.importDirs)

& $compiler $src -all `
  -f="$($Tools.papyrusFlags)" `
  -i="$($imports -join ';')" `
  -o="src/<PatchName>/Scripts/compiled" `
  -optimize
```

2. **Surface compiler output verbatim** — report every error/warning line; do not summarize away
   failures. A nonzero/`failed` result means no usable `.pex`.

3. **Commit the `.pex`.** CI cannot compile Papyrus, so `src/<PatchName>/Scripts/compiled/*.pex` is
   committed via an explicit `.gitignore` exception. `build/build.ps1` fails on a *missing* `.pex`
   but cannot detect a *stale* one — recompiling and forgetting to commit ships stale scripts.

## Per-project imports (the common failure)

If compilation reports an **unknown type / unresolved script** (e.g. `UI`, `SkyUI`, `MCM`,
`PapyrusUtil`, or another mod's script), that API's **source `.psc`** must be on the import path.
Persist it by adding the dir to **`importDirs`** in `.claude/config/tools.json` so the block above
picks it up on every compile:

```jsonc
"importDirs": ["C:/path/to/SkyUI/Source/Scripts", "C:/path/to/PapyrusUtil/Source/Scripts"]
```

Then record it in `CLAUDE.md`'s per-project imports table.

> SKSE's own types are already covered by `papyrusSource.skse` — an unresolved SKSE type means that
> key is wrong or empty, not that you need a new `importDirs` entry.

## Notes

- **Read Enderal's source, don't decompile it.** `ScriptsEnderal.zip` is real source with real names
  and comments; Champollion output is a reconstruction. Only decompile when no source exists.
- Enderal's own scripts are prefixed `_00E_`. Patch by adding your own script rather than shipping a
  modified `_00E_` file, unless overriding it *is* the fix — and say so in the patch's notes if it is.
- For decompiled scripts that won't compile cleanly, use the **papyrus-script-engineer** subagent.
- After a successful compile, use **package-mod** to assemble the installable mod folder.
