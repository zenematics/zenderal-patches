# Re-extract every Memory-Point perk in the installed Zenderal modlist into arch-docs/perks/perks.json.
# Read-only against the modlist; reuses the MagicExtract project (--perks mode). Run from anywhere.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
. (Join-Path $repoRoot '.claude\config\tools.ps1')

$modlistRoot = $Tools.modlistRoot
$profileName = $Tools.modlistProfile
$gameData = $Tools.gameDataDir
if (-not $modlistRoot -or -not (Test-Path $modlistRoot)) { throw "tools.json modlistRoot missing or not found: '$modlistRoot'" }
if (-not $profileName) { throw "tools.json modlistProfile is empty" }
if (-not $gameData -or -not (Test-Path $gameData)) { throw "tools.json gameDataDir missing or not found: '$gameData'" }

$project = Join-Path $repoRoot 'arch-docs\magic\tools\MagicExtract'
$outFile = Join-Path $repoRoot 'arch-docs\perks\perks.json'

dotnet run -c Release --project $project -- `
    --modlist-root $modlistRoot `
    --profile $profileName `
    --game-data $gameData `
    --perks $outFile
if ($LASTEXITCODE -ne 0) { throw "PerkExtract failed (exit $LASTEXITCODE) - do NOT commit the output" }
