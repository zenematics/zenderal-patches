---
name: xedit-audit
description: Verify a built Enderal SE plugin in xEdit — headless QuickAutoClean to strip ITMs/UDRs/deleted refs, and a "Check for Errors" pass for dangling references, both in -EnderalSE mode. Use after spriggit-deserialize and before package-mod to catch problems the YAML round-trip can't.
---

# Audit a built plugin in xEdit (Enderal SE mode)

CLAUDE.md's workflow says *"load the plugin in xEdit to verify before shipping."* This skill does
that from the command line: it (1) **QuickAutoClean**s the `.esp` (removes Identical-To-Master
records, undeletes-and-disables deleted references) and (2) runs xEdit's **Check for Errors** script
to surface dangling/injected/unresolved references. Run it **after `spriggit-deserialize`** (you need
the built `.esp`) and **before `package-mod`**.

## xEdit MUST run in Enderal mode

xEdit picks its game folder, INI and plugin list from its mode. For Enderal SE that is
**`-EnderalSE`**, or an executable copied/renamed to `EnderalSEEdit.exe`. Plain `-SSE` mode reads the
*Skyrim* game folder and `%LOCALAPPDATA%\Skyrim Special Edition\plugins.txt`, so it will not see
Enderal's plugins at all — the run either errors out or, worse, audits against the wrong masters.

**Always pass `-EnderalSE` in the commands below.**

## Tools (from config)

- `$Tools.xeditQuickAutoClean` — the QuickAutoClean executable (headless master cleaner).
- `$Tools.xedit` — the main xEdit executable (for the error-check script run).
- `$Tools.xeditScriptsDir` — the `Edit Scripts` folder holding `Check for Errors.pas`.
- `$Tools.gameDataDir` — **Enderal's** `Data` folder (holds `Enderal - Forgotten Stories.esm`,
  `Skyrim.esm`, `Update.esm`).

All from `.claude/config/tools.json` via `.claude/config/tools.ps1`; populated by **modlist-install**.

## Why staging is required

xEdit only loads plugins that sit in a **data directory alongside their masters**. Your built `.esp`
lives in the repo, so both steps below **stage a copy into `$Tools.gameDataDir`**, operate on it, and
copy the result back / clean up. Never point xEdit at the repo folder directly — it won't find the
masters.

## Step 1 — QuickAutoClean (headless, reliable)

```powershell
. ".claude/config/tools.ps1"
$qac     = Assert-Tool $Tools.xeditQuickAutoClean 'xeditQuickAutoClean'
$dataDir = $Tools.gameDataDir
$plugin  = "MyPatch.esp"                  # <-- the built plugin, in the repo
$built   = Resolve-Path $plugin

# Stage a copy into Enderal's Data dir next to its masters.
$staged  = Join-Path $dataDir (Split-Path $built -Leaf)
Copy-Item -LiteralPath $built $staged -Force

# Clean it. QuickAutoClean loads the plugin + masters, strips ITMs, undeletes+disables deleted refs,
# and saves in place (it keeps a backup under "<Data>\<mode> Backups\").
& $qac -EnderalSE -autoload (Split-Path $built -Leaf)

# Copy the cleaned plugin back over the repo copy, then remove the staged file.
Copy-Item -LiteralPath $staged $built -Force
Remove-Item -LiteralPath $staged -Force
```

**Report what was removed verbatim** from xEdit's output (ITM count, UDR count).

> **Do not accept ITM removal blindly on a patch.** This repo's plugins are mostly *forwarding*
> patches, and a record that is byte-identical to its master may be there deliberately — to win a
> conflict against a mod that loads earlier. QuickAutoClean cannot tell the difference. Review what
> it stripped against the patch's intent before committing the cleaned plugin.

## Step 2 — Check for Errors (dangling / unresolved references)

```powershell
. ".claude/config/tools.ps1"
$xedit  = Assert-Tool $Tools.xedit 'xedit'
$plugin = "MyPatch.esp"
$staged = Join-Path $Tools.gameDataDir $plugin
Copy-Item -LiteralPath (Resolve-Path $plugin) $staged -Force

# Run the bundled "Check for Errors" script against just this plugin (+ its masters), then exit.
& $xedit -EnderalSE -autoexit -script:"Check for Errors.pas" $plugin

Remove-Item -LiteralPath $staged -Force
```

- xEdit writes findings to its **messages log**; read them back and surface every `<Error:` /
  `Found ... errors` line. Common hits: *"Could not be resolved"* (a FormKey points at a record/master
  that isn't loaded), *"reference below decoding size"*, injected/unexpected records.
- **GUI caveat:** unlike QuickAutoClean, the error-check run may briefly show the xEdit window and,
  depending on the build/flags, a module-selection or script prompt. If it blocks, tell the user to
  confirm the dialogs, or run the check by launching `$Tools.xedit` through MO2 manually. The
  QuickAutoClean step (Step 1) is the fully headless one.

## Enderal-specific checks worth doing by eye

The scripted passes above will not catch these. If you have the list loaded in xEdit anyway, look:

1. **Masters.** No `Dawnguard.esm` / `HearthFires.esm` / `Dragonborn.esm`. Enderal does not load
   them, and neither Spriggit nor Check for Errors will complain — the plugin simply fails to load
   in-game. Order should be `Skyrim.esm`, `Update.esm`, `Enderal - Forgotten Stories.esm`, then
   third-party.
2. **Conflict column.** For each record the patch overrides, confirm it carries forward the *winning*
   mod's values for every field it is not deliberately changing. This is the single most common patch
   bug and no automated check finds it. See `arch-docs/enderal-record-patterns.md` §0.1.

## Triage

- **Unresolved FormID / "could not be resolved"** → a record references a master not in this plugin's
  master list, or a FormKey typo. Fix in the YAML (hand off to **spriggit-record-editor**) and
  re-deserialize before re-auditing.
- **Deleted reference (UDR)** → Step 1 already undeleted+disabled it; confirm that's the intended
  behavior (deleting refs outright breaks other mods; disable is the safe form).
- **ITMs you meant to keep** → see the warning in Step 1; re-add the record in YAML and
  re-deserialize.

## Notes

- Operates on the **built `.esp`**, never the YAML — fix findings in YAML and re-run
  `spriggit-deserialize`, then re-audit. Don't hand-edit the `.esp`.
- Staged copies and xEdit backups live under `$Tools.gameDataDir` — the staged copy is removed above;
  clear old backup folders yourself if they accumulate. Neither belongs in the repo.
- This is verification, not packaging — once clean, run **package-mod**.
- A clean xEdit report proves the plugin is *well-formed*. It proves nothing about whether the patch
  does what it's meant to. Launch Enderal.
