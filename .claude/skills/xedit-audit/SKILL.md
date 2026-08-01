---
name: xedit-audit
description: Verify a built SkyrimSE plugin in xEdit (SSEEdit) — headless QuickAutoClean to strip ITMs/UDRs/deleted refs, and a "Check for Errors" pass for dangling references. Use after spriggit-deserialize and before package-mod to catch problems the YAML round-trip can't.
---

# Audit a built plugin in xEdit (SSEEdit)

CLAUDE.md's workflow says *"load the plugin in xEdit/CK to verify before shipping."* This skill does
that from the command line: it (1) **QuickAutoClean**s the `.esp` (removes Identical-To-Master
records, undeletes-and-disables deleted references) and (2) runs xEdit's **Check for Errors** script
to surface dangling/injected/unresolved references. Run it **after `spriggit-deserialize`** (you need
the built `.esp`) and **before `package-mod`**.

## Tools (from config)

- `$Tools.sseeditQuickAutoClean` — `SSEEditQuickAutoClean.exe` (headless master cleaner).
- `$Tools.sseedit` — `SSEEdit.exe` (for the error-check script run).
- `$Tools.xeditScriptsDir` — the `Edit Scripts` folder holding `Check for Errors.pas`.
- `$Tools.gameDataDir` — the game `Data` folder (holds the masters: `Skyrim.esm`, `Update.esm`, …).

All from `.claude/config/tools.json` via `.claude/config/tools.ps1`; populated by **modlist-install**.

## Why staging is required

xEdit only loads plugins that sit in a **data directory alongside their masters**. Your built `.esp`
lives in the repo, so both steps below **stage a copy into `$Tools.gameDataDir`**, operate on it, and
copy the result back / clean up. Never point xEdit at the repo folder directly — it won't find the
masters.

## Step 1 — QuickAutoClean (headless, reliable)

```powershell
. ".claude/config/tools.ps1"
$qac    = Assert-Tool $Tools.sseeditQuickAutoClean 'sseeditQuickAutoClean'
$dataDir = $Tools.gameDataDir
$plugin  = "MyPlugin.esp"                 # <-- the built plugin, in the repo
$built   = Resolve-Path $plugin

# Stage a copy into the game Data dir next to its masters.
$staged  = Join-Path $dataDir (Split-Path $built -Leaf)
Copy-Item -LiteralPath $built $staged -Force

# Clean it. QuickAutoClean loads the plugin + masters, strips ITMs, undeletes+disables deleted refs,
# and saves in place (it keeps a backup under "<Data>\SSEEdit Backups\").
& $qac -autoload (Split-Path $built -Leaf)

# Copy the cleaned plugin back over the repo copy, then remove the staged file.
Copy-Item -LiteralPath $staged $built -Force
Remove-Item -LiteralPath $staged -Force
```

**Report what was removed verbatim** from xEdit's output (ITM count, UDR count). If the plugin is a
master (`.esm`) or you intend records to *override* vanilla, review the diff before accepting — not
every "identical to master" record is safe to strip in a patch that must stay a winning override.

## Step 2 — Check for Errors (dangling / unresolved references)

```powershell
. ".claude/config/tools.ps1"
$sseedit = Assert-Tool $Tools.sseedit 'sseedit'
$plugin  = "MyPlugin.esp"
$staged  = Join-Path $Tools.gameDataDir $plugin
Copy-Item -LiteralPath (Resolve-Path $plugin) $staged -Force

# Run the bundled "Check for Errors" script against just this plugin (+ its masters), then exit.
& $sseedit -SSE -autoexit -script:"Check for Errors.pas" $plugin

Remove-Item -LiteralPath $staged -Force
```

- xEdit writes findings to its **messages log**; read them back and surface every `<Error:` /
  `Found ... errors` line. Common hits: *"Could not be resolved"* (a FormKey points at a record/master
  that isn't loaded), *"reference below decoding size"*, injected/unexpected records.
- **GUI caveat:** unlike QuickAutoClean, the error-check run may briefly show the xEdit window and,
  depending on the build/flags, a module-selection or script prompt. If it blocks, tell the user to
  confirm the dialogs, or run the check by launching `$Tools.sseedit` through MO2 manually. The
  QuickAutoClean step (Step 1) is the fully headless one.

## Triage

- **Unresolved FormID / "could not be resolved"** → a record references a master not in this plugin's
  master list, or a FormKey typo. Fix in the YAML (hand off to **spriggit-record-editor**) and
  re-deserialize before re-auditing.
- **Deleted reference (UDR)** → Step 1 already undeleted+disabled it; confirm that's the intended
  behavior (deleting refs outright breaks other mods; disable is the safe form).
- **ITMs you meant to keep** → if this is an override/conflict-winning patch, re-add the record in YAML
  and re-deserialize; ITM removal is only correct when the record truly matches the master.

## Notes

- Operates on the **built `.esp`**, never the YAML — fix findings in YAML and re-run
  `spriggit-deserialize`, then re-audit. Don't hand-edit the `.esp`.
- Staged copies and xEdit backups live under `$Tools.gameDataDir` — the staged copy is removed above;
  clear old `SSEEdit Backups\` yourself if they accumulate. Neither belongs in the repo.
- This is verification, not packaging — once clean, run **package-mod** (and optionally **bsa-pack**).
