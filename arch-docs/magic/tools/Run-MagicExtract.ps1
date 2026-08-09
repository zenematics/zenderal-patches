# Re-extract every magic record in the installed Zenderal modlist into arch-docs/magic/data/.
# Read-only against the modlist; regenerates the committed JSON/CSV/Markdown. Run from anywhere.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
. (Join-Path $repoRoot '.claude\config\tools.ps1')

$modlistRoot = $Tools.modlistRoot
$profileName = $Tools.modlistProfile
$gameData = $Tools.gameDataDir
if (-not $modlistRoot -or -not (Test-Path $modlistRoot)) { throw "tools.json modlistRoot missing or not found: '$modlistRoot'" }
if (-not $profileName) { throw "tools.json modlistProfile is empty" }
if (-not $gameData -or -not (Test-Path $gameData)) { throw "tools.json gameDataDir missing or not found: '$gameData'" }

$project = Join-Path $repoRoot 'arch-docs\magic\tools\MagicExtract'
$outDir = Join-Path $repoRoot 'arch-docs\magic\data'
$reports = Join-Path $repoRoot 'arch-docs\magic'

dotnet run -c Release --project $project -- `
    --modlist-root $modlistRoot `
    --profile $profileName `
    --game-data $gameData `
    --out $outDir `
    --reports $reports
if ($LASTEXITCODE -ne 0) { throw "MagicExtract failed (exit $LASTEXITCODE) - do NOT commit the outputs" }

Write-Host ''
Write-Host 'Optional differential check against the Spriggit reference trees:'
Write-Host "  python `"$repoRoot\arch-docs\magic\tools\verify_against_yaml.py`""
