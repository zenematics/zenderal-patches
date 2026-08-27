# Generate the Apocalypse cost-ladder overrides for Zenderal - Magic Patches.esp.
#
# For every spell in apocalypse-cost-table.json: copy its YAML verbatim from
# reference/mods/Apocalypse/Spells (guardrail 4 - never retype records), then make exactly
# two changes: BaseCost -> the table's newCost, and add the ManualCostCalc flag (the spells
# are auto-calc, so without the flag the engine reprices them from effects and ignores the
# override entirely). Everything else - effects, perks, keywords, name - is carried verbatim,
# so the override forwards the author's record (guardrail 5).
#
# PS 5.1. Asserts every intended edit landed and throws on zero matches (CLAUDE.md: the CRLF
# regex trap fails SILENTLY, so every replacement is counted).
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$refSpells = Join-Path $repoRoot 'reference\mods\Apocalypse\Spells'
$outSpells = Join-Path $repoRoot 'src\MagicPatches\MagicPatchesESP\Spells'
$tablePath = Join-Path $PSScriptRoot 'apocalypse-cost-table.json'

if (-not (Test-Path $refSpells)) { throw "reference tree missing: $refSpells - run /spriggit-decompile-reference on the Apocalypse esp first" }
if (-not (Test-Path $tablePath)) { throw "pricing table missing - run 01-build-cost-table.py first" }

$table = (Get-Content $tablePath -Raw -Encoding UTF8 | ConvertFrom-Json).spells
if (-not $table -or $table.Count -lt 100) { throw "pricing table suspiciously small ($($table.Count) entries)" }

# fresh output for THIS mod's overrides only, so removed table entries do not leave stale
# overrides behind. The Spells folder is shared with the Triumvirate overrides (05/06/07) -
# delete only files whose FormKey suffix is Apocalypse's, never the whole folder.
New-Item -ItemType Directory -Force $outSpells | Out-Null
Get-ChildItem $outSpells -Filter '*_Apocalypse - Magic of Skyrim.esp.yaml' | Remove-Item -Force -Confirm:$false

$refFiles = Get-ChildItem $refSpells -Filter '*.yaml'
$byHex = @{}
foreach ($f in $refFiles) {
    if ($f.Name -match ' - ([0-9A-Fa-f]{6})_Apocalypse - Magic of Skyrim\.esp\.yaml$') {
        $byHex[$Matches[1].ToUpper()] = $f
    }
}

$written = 0
$flagsAppended = 0
$flagsCreated = 0
$utf8 = New-Object System.Text.UTF8Encoding($false)

foreach ($row in $table) {
    if ($row.formKey -notmatch '^([0-9A-Fa-f]{6}):Apocalypse - Magic of Skyrim\.esp$') { throw "unexpected formKey in table: $($row.formKey)" }
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
Write-Host "next: powershell build/build.ps1, then verify the built esp's masters and record count"
