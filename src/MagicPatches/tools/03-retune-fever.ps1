# Retune the Arcane Fever tax on Apocalypse's self-heals, inside the overrides that
# 02-apply-cost-table.ps1 generated. RUN AFTER 02 - regenerating the Spells folder wipes this.
#
# Targets (ground-truthed against EGO's live design, 2026-08-09):
#   - EGO charges burst self-heals a FLAT 1.5 fever at every rank (Flash Heal I..V: 18..82 HP,
#     all 1.5). The port taxed Wild Healing's 40 HP burst at 5 - 3.3x the line rate.
#   - Base Enderal's over-time rule is ~78 HP per fever point. Resurgence (300 HP over 15s)
#     prices to 4; Healing Blossom (600 over 20s) was ALREADY on the rule at 8 - kept.
#   - Panacea (Mystical), the game's biggest heal, costs 5 - the ceiling precedent King's
#     Heart (12) had no business exceeding.
# The edit is the Magnitude inside each spell's _00E_IncreaseArcaneFeverFFSelf (11A4B6)
# effect item; everything else stays as 02 wrote it.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$spellsDir = Join-Path $repoRoot 'src\MagicPatches\MagicPatchesESP\Spells'

# formKey hex -> @(editorId fragment, old fever, new fever). Old value asserted so a change
# in the source mod (or a re-run) cannot silently double-apply or miss.
$retunes = @(
    @{ hex = '082483'; id = 'WildHealing';    old = '5';  new = '1.5' },
    @{ hex = '01E701'; id = 'Resurgence';     old = '5';  new = '4'   },
    @{ hex = '033CCA'; id = 'KingsHeart';     old = '12'; new = '5'   }
    # 05F74D HealingBlossom stays at 8 - already on Enderal's 78-HP-per-point over-time rule
)

$utf8 = New-Object System.Text.UTF8Encoding($false)
$done = 0
foreach ($r in $retunes) {
    $file = @(Get-ChildItem $spellsDir -Filter "*$($r.hex)_Apocalypse - Magic of Skyrim.esp.yaml")
    if ($file.Count -ne 1) { throw "$($r.id): expected exactly 1 override YAML for $($r.hex), found $($file.Count) - run 02-apply-cost-table.ps1 first" }
    $text = [System.IO.File]::ReadAllText($file[0].FullName)

    # anchor on the fever effect's BaseEffect line, then its Data.Magnitude
    $rx = [regex]("(?s)(BaseEffect: 11A4B6:Skyrim\.esm\s*\r?\n\s*Data:\s*\r?\n\s*Magnitude: )" + [regex]::Escape($r.old) + "(?=\r?\n)")
    $n = $rx.Matches($text).Count
    if ($n -ne 1) { throw "$($r.id): expected exactly 1 fever Magnitude $($r.old), found $n - source changed, revisit the table" }
    $text = $rx.Replace($text, ('${1}' + $r.new), 1)

    [System.IO.File]::WriteAllText($file[0].FullName, $text, $utf8)
    Write-Host "$($r.id): fever $($r.old) -> $($r.new)"
    $done++
}
if ($done -ne $retunes.Count) { throw "applied $done of $($retunes.Count)" }
Write-Host "done - rebuild with build/build.ps1"
