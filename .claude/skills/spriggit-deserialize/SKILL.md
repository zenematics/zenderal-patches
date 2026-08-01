---
name: spriggit-deserialize
description: Rebuild a Bethesda plugin (.esp/.esm/.esl) from its Spriggit YAML folder in this Enderal SE workspace. Use when the user wants to deserialize, re-pack, build, or compile the plugin from the edited YAML.
---

# Spriggit: Deserialize (YAML → plugin)

Rebuild the binary plugin from the edited YAML. Run this after editing records.

## Workspace settings (from config)

- CLI: `$Tools.spriggitCli` from `.claude/config/tools.json` (loaded via
  `.claude/config/tools.ps1`). Run the **modlist-install** skill or edit `tools.json` to repoint it.

## Inputs to collect

1. **YAML folder** (`--InputPath`) — the Spriggit text folder under `src/`, e.g.
   `./src/ZenderalBugfixes/ZenderalBugfixesESP`.
2. **Output plugin** (`--OutputPath`) — the plugin to (re)build, e.g. `ZenderalBugfixes.esp`.

## Steps

1. Confirm the YAML folder exists and contains `spriggit-meta.json`.
2. Run (PowerShell):

```powershell
. ".claude/config/tools.ps1"
& (Assert-Tool $Tools.spriggitCli 'spriggitCli') deserialize `
  --InputPath  "./src/<PatchName>/<PatchName>ESP" `
  --OutputPath "<MyPatch.esp>"
```

3. `--PackageName` / `--PackageVersion` are intentionally omitted — Spriggit auto-detects them
   from the folder's `spriggit-meta.json`. Only pass them if asked to override.

## After deserializing — ALWAYS remind

- The rebuilt `.esp/.esm` is a **build artifact** and is gitignored (commit the YAML, not the binary).
- **Load the plugin in xEdit — in `-EnderalSE` mode — to verify it before shipping.** Plain SSEEdit
  mode reads the Skyrim game folder and will not see Enderal's plugins at all. Use the
  **xedit-audit** skill, which passes the switch.
- Deserialize succeeding does not guarantee the records are correct, and a clean xEdit report does
  not mean the patch works. Only launching Enderal proves that.
