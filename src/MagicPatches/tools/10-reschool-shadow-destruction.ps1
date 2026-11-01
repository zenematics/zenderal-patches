# Move Triumvirate's five Shadow Mage "Destruction" spells (Draining Touch, Shadow's Wrath,
# Nightblade, Draining Shroud, Draining Mist) from Elementalism to Entropy, with their tomes and
# staff. Mirror of 09-reschool-warlock-destruction.ps1.
#
# Why (arch-docs/enderal/magic-schools.md): absorb-health/magicka drains and raw magic damage are
# Entropy's "altering a being's life force", not environment-drawn Elementalism; EGO's own
# Sinistrope cost perks call Entropy "Schattenzauber" (shadow spells). No Elementalist damage/
# duration perk applied (none carry MagicDamageFire/Frost/Shock or MagicRune), so nothing is lost,
# and the Shadow Mage becomes Thaumaturge (Mentalism mobility) + Sinistrope (Entropy + Psionics).
#
# Records (verbatim copies, guardrail 4; only school fields change):
#   Spells       5  in-place edit of 06's output: HalfCostPerk Destruction<tier> -> Conjuration<tier>
#   MagicEffects 15 copied: MagicSkill Destruction -> Conjuration (= Entropy). Covers the 5 spells
#                   AND their hidden procs - the Draining Shroud cloak proc (31C5BE), the Draining
#                   Mist hazard proc (3216CF via hazard 330A36) and the Nightblade on-hit proc
#                   (335B4F via TVR_BlinkStrikes_Script) - which deal the actual drain/damage.
#                   Every one is used only by this chain (+ Draining Touch's own staff ENCH).
#   Books        5  Destruction tome mesh + inventory art -> the Conjuration ones
#   Weapons      1  Draining Touch staff Data.Skill Destruction -> Conjuration (the only D staff)
# Untouched on purpose: the 3 proc SPELs (their HalfCostPerk only feeds ModSpellCost, and procs
# are never paid for); the school-less MGEFs in the chain (self-damage, Nightblade_0..3, ShortRange);
# the staff ENCH 419B13 (points at the MGEFs above); distribution (all three Shadow schools feed the
# same merchants: BibliothekarMarius, SisterEnvy, UndercityHehler02, Wildmage_Undercity); no scrolls
# exist. Scripts on the chain (TVR_BlinkStrikes, TVR_PercentageDamage, TVR_Flash, TVR_SoundAndImod)
# read no skill - PercentageDamage's GetActorValue is the caster's Magicka (decompiled 2026-10-13).
#
# ORDER: 06 -> 07 -> 09 -> 10. Safe to re-run on its own.
# PS 5.1. Every replacement is counted and asserted (CRLF regex trap, CLAUDE.md guardrail 10).
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$ref = Join-Path $repoRoot 'reference\mods\Triumvirate'
$esp = Join-Path $repoRoot 'src\MagicPatches\MagicPatchesESP'
if (-not (Test-Path $ref)) { throw "reference tree missing: $ref - run /spriggit-decompile-reference on the converted Triumvirate esp first" }

$suffix = '_Triumvirate - Mage Archetypes.esp.yaml'
$utf8 = New-Object System.Text.UTF8Encoding($false)

function Find-Ref([string]$folder, [string]$hex) {
    $hits = @(Get-ChildItem (Join-Path $ref $folder) -Filter "* - ${hex}$suffix")
    if ($hits.Count -ne 1) { throw "$folder ${hex}: expected 1 reference file, found $($hits.Count)" }
    return $hits[0]
}

# Literal replace that must hit exactly $expect times.
function Replace-Exact([string]$text, [string]$old, [string]$new, [int]$expect, [string]$what) {
    $n = ([regex]::Matches($text, [regex]::Escape($old))).Count
    if ($n -ne $expect) { throw "${what}: expected $expect x '$old', found $n" }
    return $text.Replace($old, $new)
}

function Copy-WithEdits([string]$folder, [string[]]$hexes, [object[]]$edits) {
    $out = Join-Path $esp $folder
    New-Item -ItemType Directory -Force $out | Out-Null
    $count = 0
    foreach ($hex in $hexes) {
        $src = Find-Ref $folder $hex
        $text = [System.IO.File]::ReadAllText($src.FullName)
        foreach ($e in $edits) { $text = Replace-Exact $text $e[0] $e[1] 1 "$folder $($src.Name)" }
        [System.IO.File]::WriteAllText((Join-Path $out $src.Name), $text, $utf8)
        $count++
    }
    if ($count -ne $hexes.Count) { throw "$folder wrote $count of $($hexes.Count)" }
    Write-Host ("  {0,-13} {1} overrides" -f $folder, $count)
}

Write-Host 'Shadow Mage Destruction -> Entropy'

# ---- MagicEffects: Destruction -> Conjuration (displayed as Entropy) -------------------------
$mgefs = @(
    '33FD5C', '33FD62', '33FD65', # Draining Touch: AbsorbHealth / AbsorbMagicka / KeywordHolder
    '3216C9',                     # Shadow's Wrath (TVR_Shadow_Rift_Effect_AzrasWrath)
    '335B49', '335B53',           # Nightblade + KeywordHolder
    '335B51',                     # Nightblade proc: Debuff
    '31C5C0',                     # Draining Shroud (cloak)
    '31C5BC', '31C5BD', '381AE5', # Draining Shroud cloak proc: AbsorbHealth / AbsorbMagicka / KeywordHolder
    '330A2D',                     # Draining Mist (spawn hazard)
    '3216CD', '3216CE', '381AE6'  # Draining Mist hazard proc: AbsorbHealth / AbsorbMagicka / KeywordHolder
)
# Self-check: re-derive the Destruction MGEFs reachable from the 5 spells + 3 procs in the
# reference tree, and require it to equal the list above (catches a Triumvirate update that adds
# or re-schools an effect).
$chain = @('2FDF7D', '3216CA', '330A43', '31C5C1', '330A2E', '31C5BE', '3216CF', '335B4F')
$derived = New-Object System.Collections.Generic.SortedSet[string]
foreach ($hex in $chain) {
    $text = [System.IO.File]::ReadAllText((Find-Ref 'Spells' $hex).FullName)
    foreach ($m in [regex]::Matches($text, 'BaseEffect: ([0-9A-F]{6}):Triumvirate - Mage Archetypes\.esp')) {
        $e = $m.Groups[1].Value
        if ([System.IO.File]::ReadAllText((Find-Ref 'MagicEffects' $e).FullName) -match '(?m)^MagicSkill: Destruction(?=\r?$)') { [void]$derived.Add($e) }
    }
}
$listed = New-Object System.Collections.Generic.SortedSet[string] (, [string[]]$mgefs)
if (-not $derived.SetEquals($listed)) { throw "MGEF list drifted: reference chain has [$($derived -join ',')], script lists [$($listed -join ',')]" }
Copy-WithEdits 'MagicEffects' $mgefs @(, @('MagicSkill: Destruction', 'MagicSkill: Conjuration'))

# ---- Books: tome mesh + inventory art -----------------------------------------------------
$books = @('419B20', '419B21', '419B22', '419B23', '419B24')
Copy-WithEdits 'Books' $books @(
    @('SpellTomeDestructionLowPoly.nif', 'SpellTomeConjurationLowPoly.nif'),
    @('InventoryArt: 02FBB5:Skyrim.esm', 'InventoryArt: 02FBB6:Skyrim.esm')  # HighPolyDestructionBook -> Conjuration
)

# ---- Weapons: staff skill ----------------------------------------------------------------------
Copy-WithEdits 'Weapons' @('419B19') @(, @('Skill: Destruction', 'Skill: Conjuration'))

# ---- Spells: HalfCostPerk in 06's generated overrides ----------------------------------------
$perkMap = [ordered]@{
    '0F2CA8:Skyrim.esm' = '0F2CA7:Skyrim.esm'  # DestructionNovice00     -> ConjurationNovice00
    '0C44BF:Skyrim.esm' = '0C44BB:Skyrim.esm'  # DestructionApprentice25 -> ConjurationApprentice25
    '0C44C0:Skyrim.esm' = '0C44BC:Skyrim.esm'  # DestructionAdept50      -> ConjurationAdept50
    '0C44C1:Skyrim.esm' = '0C44BD:Skyrim.esm'  # DestructionExpert75     -> ConjurationExpert75
    '0C44C2:Skyrim.esm' = '0C44BE:Skyrim.esm'  # DestructionMaster100    -> ConjurationMaster100
}
$spells = @('2FDF7D', '3216CA', '330A43', '31C5C1', '330A2E')
$spellDir = Join-Path $esp 'Spells'
$moved = 0; $already = 0
foreach ($hex in $spells) {
    $hits = @(Get-ChildItem $spellDir -Filter "* - ${hex}$suffix")
    if ($hits.Count -ne 1) { throw "Spells ${hex}: no override from 06 - run 06-apply-triumvirate-cost-table.ps1 first" }
    $f = $hits[0]
    $text = [System.IO.File]::ReadAllText($f.FullName)
    $m = [regex]::Match($text, '(?m)^HalfCostPerk: (\S+)(?=\r?$)')
    if (-not $m.Success) { throw "$($f.Name): no HalfCostPerk line" }
    $cur = $m.Groups[1].Value
    if ($perkMap.Values -contains $cur) { $already++; continue }
    if (-not $perkMap.Contains($cur)) { throw "$($f.Name): unexpected HalfCostPerk $cur" }
    $text = Replace-Exact $text "HalfCostPerk: $cur" "HalfCostPerk: $($perkMap[$cur])" 1 $f.Name
    [System.IO.File]::WriteAllText($f.FullName, $text, $utf8)
    $moved++
}
if ($moved + $already -ne $spells.Count) { throw "Spells: handled $($moved + $already) of $($spells.Count)" }
Write-Host ("  {0,-13} {1} moved, {2} already Conjuration" -f 'Spells', $moved, $already)
Write-Host 'next: build/build.ps1'
