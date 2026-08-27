# Add the Arcane Fever tax to Triumvirate's self-heals, inside the overrides that
# 06-apply-triumvirate-cost-table.ps1 generated. RUN AFTER 06 - regenerating wipes this.
#
# The upstream Triumvirate - Enderal Conversion (v2026.08.27) deliberately ships no balance
# changes, so its self-heals bypass Enderal's central survival mechanic - the same gap the
# Apocalypse conversion closed for its own 19 heals. Only SELF-targeted healing pays fever in
# Enderal's design; drain/absorb heals (Life Tap, Visions of Healing, Spirit Fire) stay free,
# as do fortifies (Spirit of the Oak) and potions (Goodberry). Aura of Thorns' 100-point
# release heal is scripted-on-release and cannot be priced per-cast without charging for its
# reflect channel, so it stays untaxed - a conditional combat reward, like the drains.
#
# Three spells qualify (swept from arch-docs/magic/data, 2026-08-27):
#   - Aura of Vigor (1E7429, conc, heals caster+allies 15/s): gets EGO's own Boon fever block
#     COPIED VERBATIM from _05E_Wohltat - the 106EA4 0.25/s effect plus its two Mental-perk
#     reduced variants (0083D3:EGO at 0.2193/0.1984). 106EA4's description bakes in "0,25%
#     per second", so the magnitude is not tunable without lying to the player; Boon heals
#     18-39/s at the same flat rate, so 15/s rides the same line comfortably.
#   - Mass Immortality (1EC531, FF, 30 s unlimited group Health regen): 11A4B6 at 5 - the
#     King's Heart / Panacea ceiling this repo already applies (03-retune-fever.ps1).
#   - Spirit of the Sun (27F3B6, FF, 20/s for 120 s = up to 2400): 11A4B6 at 10. The strict
#     78-HP-per-point over-time rule says 31, far past every precedent; 10 sits inside the
#     dear-heal band (Healing Blossom 8, Breath of Tyr's full channel 19, Erodan's 20).
#
# All three spell files end with their Effects list, so the block is appended at EOF; the
# script asserts that shape and every insertion.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$spellsDir = Join-Path $repoRoot 'src\MagicPatches\MagicPatchesESP\Spells'
$egoBoon = Join-Path $repoRoot 'reference\mods\EGO\esp\Spells\_05E_Wohltat - 03B82E_Skyrim.esm.yaml'
$utf8 = New-Object System.Text.UTF8Encoding($false)

function Get-Override([string]$hex) {
    $f = @(Get-ChildItem $spellsDir -Filter "*$hex`_Triumvirate - Mage Archetypes.esp.yaml")
    if ($f.Count -ne 1) { throw "expected exactly 1 override YAML for $hex, found $($f.Count) - run 06 first" }
    return $f[0]
}

function Add-Tail([System.IO.FileInfo]$file, [string]$block, [string]$marker) {
    $text = [System.IO.File]::ReadAllText($file.FullName)
    if ($text -match [regex]::Escape($marker)) { throw "$($file.Name): fever effect already present - 06 not re-run?" }
    if ($text -notmatch '(?s)\r?\nEffects:\r?\n.*\z') { throw "$($file.Name): does not end with an Effects list - shape drift, re-derive the append point" }
    if (-not $text.EndsWith("`n")) { $text += "`r`n" }
    $text += $block
    if (([regex]::Matches($text, [regex]::Escape($marker))).Count -lt 1) { throw "$($file.Name): append failed" }
    [System.IO.File]::WriteAllText($file.FullName, $text, $utf8)
}

# --- 1) Aura of Vigor: EGO Boon's conc fever block, derived not retyped (guardrail 4) ---
if (-not (Test-Path $egoBoon)) { throw "EGO reference missing: $egoBoon - run /spriggit-decompile-reference on EGO" }
$boon = [System.IO.File]::ReadAllText($egoBoon)
$idx = $boon.IndexOf('- BaseEffect: 106EA4:Skyrim.esm')
if ($idx -lt 0) { throw "EGO Boon: 106EA4 fever effect not found - EGO changed, re-verify the archetype" }
$feverBlock = $boon.Substring($idx)
$n106 = ([regex]::Matches($feverBlock, '- BaseEffect: 106EA4:Skyrim\.esm')).Count
$n83  = ([regex]::Matches($feverBlock, '- BaseEffect: 0083D3:Enderal SE - Gameplay Overhaul\.esp')).Count
if ($n106 -ne 1 -or $n83 -ne 2) { throw "EGO Boon fever tail unexpected shape (106EA4 x$n106, 0083D3 x$n83) - re-verify before copying" }
foreach ($mag in '0.25', '0.2193', '0.1984') {
    if ($feverBlock -notmatch [regex]::Escape("Magnitude: $mag")) { throw "EGO Boon fever tail missing Magnitude $mag" }
}
Add-Tail (Get-Override '1E7429') $feverBlock '106EA4:Skyrim.esm'
Write-Host "AuraOfVigor: appended EGO Boon fever block (0.25/s + Mental-perk variants)"

# --- 2) FF heals: bare 11A4B6, magnitude per the header comment ---
$ff = @(
    @{ hex = '1EC531'; id = 'MassImmortality'; mag = '5'  },
    @{ hex = '27F3B6'; id = 'SpiritOfTheSun';  mag = '10' }
)
foreach ($r in $ff) {
    $block = "- BaseEffect: 11A4B6:Skyrim.esm`r`n  Data:`r`n    Magnitude: $($r.mag)`r`n    Duration: 1`r`n"
    Add-Tail (Get-Override $r.hex) $block '11A4B6:Skyrim.esm'
    Write-Host "$($r.id): fever $($r.mag) added"
}
Write-Host "done - rebuild with build/build.ps1"
