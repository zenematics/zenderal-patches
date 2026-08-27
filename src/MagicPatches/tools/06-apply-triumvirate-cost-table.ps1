# Generate the Triumvirate cost-ladder overrides for Zenderal - Magic Patches.esp.
#
# Mirror of 02-apply-cost-table.ps1, pointed at Triumvirate: for every spell in
# triumvirate-cost-table.json, copy its YAML verbatim from reference/mods/Triumvirate/Spells
# (guardrail 4 - never retype records), then make exactly two changes: BaseCost -> the table's
# newCost, and add the ManualCostCalc flag (the spells are auto-calc, so without the flag the
# engine reprices them from effects and ignores the override entirely). Everything else -
# effects, perks, keywords, name - is carried verbatim (guardrail 5).
#
# The output folder is SHARED with the Apocalypse overrides: each script deletes only files
# carrying its own mod's FormKey suffix. RUN 07-add-triumvirate-fever.ps1 AFTER this -
# regenerating the Triumvirate overrides wipes the fever additions.
#
# PS 5.1. Asserts every intended edit landed and throws on zero matches (CLAUDE.md: the CRLF
# regex trap fails SILENTLY, so every replacement is counted).
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$refSpells = Join-Path $repoRoot 'reference\mods\Triumvirate\Spells'
$outSpells = Join-Path $repoRoot 'src\MagicPatches\MagicPatchesESP\Spells'
$tablePath = Join-Path $PSScriptRoot 'triumvirate-cost-table.json'

if (-not (Test-Path $refSpells)) { throw "reference tree missing: $refSpells - run /spriggit-decompile-reference on the converted Triumvirate esp first" }
if (-not (Test-Path $tablePath)) { throw "pricing table missing - run 05-build-triumvirate-cost-table.py first" }

$table = (Get-Content $tablePath -Raw -Encoding UTF8 | ConvertFrom-Json).spells
if (-not $table -or $table.Count -ne 75) { throw "pricing table unexpected size ($($table.Count) entries, expected 75)" }

# fresh output for THIS mod's overrides only (folder shared with the Apocalypse overrides)
New-Item -ItemType Directory -Force $outSpells | Out-Null
Get-ChildItem $outSpells -Filter '*_Triumvirate - Mage Archetypes.esp.yaml' | Remove-Item -Force -Confirm:$false

$refFiles = Get-ChildItem $refSpells -Filter '*.yaml'
$byHex = @{}
foreach ($f in $refFiles) {
    if ($f.Name -match ' - ([0-9A-Fa-f]{6})_Triumvirate - Mage Archetypes\.esp\.yaml$') {
        $byHex[$Matches[1].ToUpper()] = $f
    }
}

$written = 0
$flagsAppended = 0
$flagsCreated = 0
$utf8 = New-Object System.Text.UTF8Encoding($false)

foreach ($row in $table) {
    if ($row.formKey -notmatch '^([0-9A-Fa-f]{6}):Triumvirate - Mage Archetypes\.esp$') { throw "unexpected formKey in table: $($row.formKey)" }
    $hex = $Matches[1].ToUpper()
    $src = $byHex[$hex]
    if (-not $src) { throw "no reference YAML for $($row.formKey) ($($row.editorId))" }

    $text = [System.IO.File]::ReadAllText($src.FullName)
    if ($text -match 'ManualCostCalc') { throw "$($row.editorId): source already ManualCostCalc - table stale, rebuild it" }

    # 1) BaseCost -> newCost (anchor tolerates CRLF; count asserted)
    $costRx = [regex]'(?m)^BaseCost: \d+(\.\d+)?(?=\r?$)'
    $n = $costRx.Matches($text).Count
    if ($n -ne 1) { throw "$($row.editorId): expected exactly 1 BaseCost line, found $n" }
    $text = $costRx.Replace($text, "BaseCost: $($row.newCost)", 1)

    # 2) ManualCostCalc: prepend to an existing Flags list, else create the block after BaseCost
    $flagsRx = [regex]'(?m)^Flags:(?=\r?\n)'
    if ($flagsRx.IsMatch($text)) {
        $text = $flagsRx.Replace($text, "Flags:`r`n- ManualCostCalc", 1)
        $flagsAppended++
    } else {
        $text = [regex]::Replace($text, "(?m)^(BaseCost: $($row.newCost))(?=\r?$)",
            "`$1`r`nFlags:`r`n- ManualCostCalc", 1)
        $flagsCreated++
    }
    if (([regex]::Matches($text, 'ManualCostCalc')).Count -ne 1) { throw "$($row.editorId): ManualCostCalc insertion failed" }
    if ($text -notmatch [regex]::Escape("BaseCost: $($row.newCost)")) { throw "$($row.editorId): BaseCost replacement failed" }

    [System.IO.File]::WriteAllText((Join-Path $outSpells $src.Name), $text, $utf8)
    $written++
}

Write-Host "wrote $written spell overrides -> $outSpells"
Write-Host "  Flags list existed (prepended): $flagsAppended"
Write-Host "  Flags block created:            $flagsCreated"
if ($written -ne $table.Count) { throw "wrote $written but table has $($table.Count)" }
Write-Host "next: 07-add-triumvirate-fever.ps1, then build/build.ps1"
