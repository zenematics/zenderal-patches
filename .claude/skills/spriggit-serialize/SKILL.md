---
name: spriggit-serialize
description: Serialize a Bethesda plugin (.esp/.esm/.esl) into an editable Spriggit YAML folder for this Enderal SE workspace. Use when the user wants to decompile/convert a plugin to text, import a plugin into the workspace, or "serialize" a mod.
---

# Spriggit: Serialize (plugin → YAML)

Convert a binary plugin into the git-friendly YAML representation.

## Workspace settings (from config)

Paths and Spriggit settings come from `.claude/config/tools.json` (loaded via
`.claude/config/tools.ps1`). Defaults: GameRelease **`EnderalSE`** (not `SkyrimSE` — see CLAUDE.md "Why EnderalSE"), PackageName
`Spriggit.Yaml.Skyrim`, PackageVersion `0.40.0`, CLI at `$Tools.spriggitCli`. To repoint paths, run the **modlist-install**
skill or edit `tools.json`.

## Inputs to collect

1. **Plugin path** (`--InputPath`) — e.g. `MyPatch.esp`. Ask if not given.
2. **Output folder** (`--OutputPath`) — a *dedicated* folder under `src/`, conventionally
   `./src/<PatchName>/<PatchName>ESP` (e.g. `./src/ZenderalBugfixes/ZenderalBugfixesESP`). All patch
   content lives under `src/`; it must be a folder used only for this plugin.

## Steps

1. Confirm the plugin file exists.
2. Warn the user if the output folder already contains YAML — **serialize overwrites it**. If it
   holds committed work, confirm before proceeding.
3. Run (PowerShell):

```powershell
. ".claude/config/tools.ps1"
& (Assert-Tool $Tools.spriggitCli 'spriggitCli') serialize `
  --InputPath   "<MyPatch.esp>" `
  --OutputPath  "./src/<PatchName>/<PatchName>ESP" `
  --GameRelease $Tools.spriggit.gameRelease `
  --PackageName $Tools.spriggit.packageName `
  --PackageVersion $Tools.spriggit.packageVersion
```

4. After it runs, **check `RecordData.yaml` and `spriggit-meta.json` say `GameRelease: EnderalSE`**,
   and that `MasterReferences` lists no DLC (`Dawnguard.esm`/`HearthFires.esm`/`Dragonborn.esm`) —
   Enderal does not load them and Spriggit will not warn. Then report the generated layout and remind
   the user this YAML folder **is committed** to git.

## Notes

- For decompiling Enderal's ESM or a third-party master for FormKey *lookup only*, use the
  **spriggit-decompile-reference** skill instead (it targets the gitignored `reference/`).
- The binary plugin itself is gitignored — only the YAML is tracked.
