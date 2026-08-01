---
name: modlist-install
description: Install the Zenderal (Enderal SE) modlist into a gitignored location and auto-discover its tool paths (game folder, xEdit, BSA Browser, Champollion, Papyrus source trees) into .claude/config/tools.json. Use when the user wants to set up the modlist, point the workspace at an installed modlist, install a .wabbajack file, or stop using hardcoded tool paths.
---

# Install the modlist & wire it into the workspace

A Wabbajack modlist is a self-contained MO2 instance — game folder, mods, and tools — that can be
**hundreds of GB**. It is **never committed**; it lives outside or under a gitignored path and the
workspace points at it through `.claude/config/tools.json`. This skill (1) guides the install, then
(2) discovers the tool paths inside it and writes them to the config so every other skill uses them
automatically.

## Enderal-specific facts that shape this

- **The game is Enderal Special Edition**, a separate Steam app, not a folder inside Skyrim SE.
  Wabbajack's game type for it is *Enderal Special Edition*.
- **Enderal ships no Creation Kit and no Papyrus compiler.** Those come from an ordinary Skyrim SE
  install and go in `skyrimSeRoot` / `papyrusCompiler` / `creationKit`. Do not expect to find them
  under the modlist root, and do not leave them pointing at an Enderal path.
- **xEdit must run in `-EnderalSE` mode.** The discovered executable may be named `EnderalSEEdit.exe`,
  `SSEEdit.exe` or `xEdit.exe` — they are the same program; the mode comes from the name or the
  switch. The `xedit-audit` skill passes `-EnderalSE` explicitly.
- **There are three Papyrus source trees**, two of which need unpacking. Part 3 handles them.

## Part 1 — Install the `.wabbajack` (manual, GUI step)

The actual install is done by the **Wabbajack** app; it cannot be driven headlessly here. Guide
the user:

1. Get Wabbajack from <https://www.wabbajack.org/> and the `.wabbajack` file for the list.
2. Make sure a **Steam-owned Enderal Special Edition** is installed and has been launched once —
   Wabbajack copies from it.
3. In Wabbajack: select the `.wabbajack` file, then set:
   - **Install Location** — where the modlist (MO2 instance) is built. Pick a big drive. If you
     want it *inside* the repo, use `modlist/` (already gitignored); otherwise any external path
     like `D:/Modlists/Zenderal` is fine.
   - **Download Location** — where mod archives are cached (also huge; keep outside git).
4. Click **Install** and wait (long — tens of minutes to hours).
5. When done, the **Install Location** is the *modlist root* (it contains `ModOrganizer.exe`,
   `mods/`, `profiles/`, usually `tools/` and a game copy like `Stock Game/` or `Game Root/`).

**Confirm the modlist root path with the user before continuing.**

## Part 2 — Discover tools & write `tools.json`

Run this with the confirmed modlist root. It probes the usual Wabbajack layout, fills in whatever
it finds, and **preserves existing values** for anything it can't locate. Review the output, then
hand-fill any blanks.

```powershell
$modlistRoot  = "<CONFIRMED MODLIST ROOT>"   # e.g. D:/Modlists/Zenderal  or  modlist
$skyrimSeRoot = "<SKYRIM SE ROOT>"           # for the CK + Papyrus compiler + vanilla script source

$cfgPath = ".claude/config/tools.json"
if (-not (Test-Path $cfgPath)) { Copy-Item ".claude/config/tools.example.json" $cfgPath }
$cfg = Get-Content -Raw $cfgPath | ConvertFrom-Json

function First-Path { param([string[]]$Candidates) foreach ($c in $Candidates) { if ($c -and (Test-Path -LiteralPath $c)) { return ((Resolve-Path -LiteralPath $c).Path -replace '\\','/') } } return $null }
function Find-One { param([string]$Root,[string]$Filter) if (Test-Path -LiteralPath $Root) { $h = Get-ChildItem -LiteralPath $Root -Recurse -Filter $Filter -File -ErrorAction SilentlyContinue | Select-Object -First 1; if ($h) { return ($h.FullName -replace '\\','/') } } return $null }
# Add-Member -Force so a key missing from an older tools.json is created rather than throwing.
function Set-Cfg { param($Obj,$Key,$Val) if ($Val) { $Obj | Add-Member -NotePropertyName $Key -NotePropertyValue $Val -Force } }

# Game root: Wabbajack lists name the self-contained game folder a few different ways.
$gameRoot = First-Path @(
  (Join-Path $modlistRoot 'Stock Game'),
  (Join-Path $modlistRoot 'Game Root'),
  (Join-Path $modlistRoot 'Stock Game Folder'),
  (Join-Path $modlistRoot 'root'),
  $modlistRoot
)

Set-Cfg $cfg 'modlistRoot' ($modlistRoot -replace '\\','/')
if ($gameRoot) {
  Set-Cfg $cfg 'gameRoot'    $gameRoot
  Set-Cfg $cfg 'gameDataDir' "$gameRoot/Data"
  # Sanity check: this should be Enderal, not Skyrim.
  if (-not (Test-Path -LiteralPath "$gameRoot/Data/Enderal - Forgotten Stories.esm")) {
    Write-Warning "No 'Enderal - Forgotten Stories.esm' under $gameRoot/Data - is this really the Enderal game folder?"
  }
}

# Creation Kit + Papyrus compiler come from Skyrim SE, NOT from Enderal.
if ($skyrimSeRoot -and (Test-Path -LiteralPath $skyrimSeRoot)) {
  Set-Cfg $cfg 'skyrimSeRoot'    ($skyrimSeRoot -replace '\\','/')
  Set-Cfg $cfg 'creationKit'     (First-Path @("$skyrimSeRoot/CreationKit.exe"))
  Set-Cfg $cfg 'papyrusCompiler' (First-Path @("$skyrimSeRoot/Papyrus Compiler/PapyrusCompiler.exe"))
}

# SKSE Papyrus source is loose in an Enderal install; the other two trees are unpacked in Part 3.
if ($gameRoot) {
  $skseSrc = First-Path @("$gameRoot/Data/Source/Scripts")
  if ($skseSrc) {
    if (-not $cfg.papyrusSource) { $cfg | Add-Member -NotePropertyName 'papyrusSource' -NotePropertyValue ([pscustomobject]@{}) -Force }
    Set-Cfg $cfg.papyrusSource 'skse' $skseSrc
  }
}

# Tools bundled in the modlist (xEdit/bsab/Champollion often live under tools/ or mods/).
$bsab = First-Path @((Join-Path $modlistRoot 'tools/BSA Browser/bsab.exe')); if (-not $bsab) { $bsab = Find-One $modlistRoot 'bsab.exe' }
Set-Cfg $cfg 'bsab' $bsab
Set-Cfg $cfg 'champollion' (Find-One $modlistRoot 'Champollion*.exe')

# xEdit: any of these names is the same program - mode comes from the name or the -EnderalSE switch.
$xedit = $null
foreach ($n in @('EnderalSEEdit.exe','SSEEdit.exe','xEdit.exe')) { if (-not $xedit) { $xedit = Find-One $modlistRoot $n } }
Set-Cfg $cfg 'xedit' $xedit
$qac = $null
foreach ($n in @('EnderalSEEditQuickAutoClean.exe','SSEEditQuickAutoClean.exe','xEditQuickAutoClean.exe')) { if (-not $qac) { $qac = Find-One $modlistRoot $n } }
Set-Cfg $cfg 'xeditQuickAutoClean' $qac
# xEdit 'Edit Scripts' dir (holds 'Check for Errors.pas') - derive from the exe we found.
if ($cfg.xedit) { $es = Join-Path (Split-Path $cfg.xedit) 'Edit Scripts'; if (Test-Path -LiteralPath $es) { Set-Cfg $cfg 'xeditScriptsDir' ($es -replace '\\','/') } }

foreach ($pair in @(
    @('bsarch','BSArch64.exe'), @('synthesis','Synthesis.exe'), @('resaver','ReSaver.exe'),
    @('cao','Cathedral_Assets_Optimizer.exe'), @('nifskope','NifSkope.exe'), @('bae','bae.exe')
)) { Set-Cfg $cfg $pair[0] (Find-One $modlistRoot $pair[1]) }

# Auto-populate EXTRA Papyrus importDirs from framework mods that ship loose .psc source. These are
# appended AFTER the three papyrusSource trees, so they never shadow Enderal's copies.
$frameworks = @(
  'MCM SDK','MCM Helper','PapyrusUtil SE - Modders Scripting Utility Functions','JContainers SE',
  'powerofthree Papyrus Extender',"Scrab's Papyrus Extender",'ConsoleUtilSSE NG'
)
$imports = [System.Collections.Generic.List[string]]::new()
if ($cfg.importDirs) { foreach ($d in $cfg.importDirs) { if ($d) { [void]$imports.Add($d) } } }
$modsDir = Join-Path $modlistRoot 'mods'
foreach ($fw in $frameworks) {
  $hit = First-Path @(
    (Join-Path $modsDir "$fw/Source/Scripts"),
    (Join-Path $modsDir "$fw/Scripts/Source"),
    (Join-Path $modsDir "$fw/scripts/source"),
    (Join-Path $modsDir "$fw/source/scripts")
  )
  if ($hit -and ($imports -notcontains $hit)) { [void]$imports.Add($hit) }
}
$cfg | Add-Member -NotePropertyName 'importDirs' -NotePropertyValue @($imports) -Force

# Deploy target for the mod-deploy skill.
if (Test-Path -LiteralPath $modsDir) { Set-Cfg $cfg 'modsDir' ($modsDir -replace '\\','/') }

$cfg | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 $cfgPath
Write-Host "Wrote $cfgPath. Review below:"
Get-Content $cfgPath
```

Then:

1. **Report what was found vs. left blank.** Expect `creationKit` / `papyrusCompiler` to be blank
   unless a Skyrim SE root was supplied — that is normal, not a failure. `deployModName` is never
   auto-filled: it must be the exact MO2 folder name and is the user's call.
2. **Spriggit CLI is independent** of the modlist — leave `spriggitCli` pointing at its standalone
   install unless the user moved it.
3. Any tool reached **through MO2** (so it sees virtual files) should be launched via
   `ModOrganizer.exe`; the discovered paths are the raw executables, fine for our CLI steps which
   operate on files in this repo, not on the virtual file system.

## Part 3 — Unpack the Papyrus source trees

Only needed if scripts will be compiled. Two of the three trees ship zipped. Unpack outside the repo
or into the gitignored `papyrus-source/`, then record the paths.

```powershell
. ".claude/config/tools.ps1"
$out = "papyrus-source"     # gitignored

# 1. Enderal's own source (~5000 .psc) - MUST be first on the compiler's -i path.
Expand-Archive "$($Tools.gameDataDir)/ScriptsEnderal.zip" "$out/enderal" -Force
#    -> the .psc land under $out/enderal/source/scripts

# 2. SKSE source - already loose in an Enderal install, discovered in Part 2. Nothing to unpack.

# 3. Vanilla source (~14300 .psc) + TESV_Papyrus_Flags.flg - from SKYRIM SE, not Enderal.
Expand-Archive "$($Tools.skyrimSeRoot)/Data/Scripts.zip" "$out/vanilla" -Force
#    -> the .psc land under $out/vanilla/Source/Scripts
```

Then set in `tools.json`:

```jsonc
"papyrusSource": {
  "enderal": "papyrus-source/enderal/source/scripts",
  "skse":    "<gameDataDir>/Source/Scripts",
  "vanilla": "papyrus-source/vanilla/Source/Scripts"
}
```

**The order in that object is the precedence order** and the `papyrus-compile` skill relies on it —
the compiler's `-i` path is first-wins and Enderal overrides 55 vanilla script names. The flags file
only exists in the vanilla tree, which is why all three must be present.

## Part 4 — Verify

```powershell
. ".claude/config/tools.ps1"
Assert-Tool $Tools.gameDataDir            'gameDataDir'
Assert-Tool $Tools.papyrusCompiler        'papyrusCompiler'       # if compiling
Assert-Tool $Tools.papyrusSource.enderal  'papyrusSource.enderal' # if compiling
Assert-Tool $Tools.papyrusSource.vanilla  'papyrusSource.vanilla' # if compiling
Assert-Tool $Tools.xedit                  'xedit'                 # if auditing
$Tools | ConvertTo-Json -Depth 4
```

`Assert-Tool` throws on a missing/empty path — fix those before relying on the toolchain.

## Notes

- The modlist and the unpacked source trees are gitignored (`modlist/`, `downloads/`,
  `papyrus-source/`, plus `tools.json`). Never commit them — they are enormous and licensed
  third-party content.
- Re-run Part 2 any time you reinstall or move the modlist; it's idempotent, preserves keys it can't
  rediscover, and never drops `importDirs` entries you added by hand.
- After this, `papyrus-compile`, `bsa-extract`, `pex-decompile`, `package-mod`, `mod-deploy`,
  `xedit-audit` and the Spriggit skills all resolve their paths from `tools.json` — no manual edits
  to each skill needed.
