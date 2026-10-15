# Move eleven Apocalypse spells to the Enderal discipline their effects belong to, with their tomes
# and staffs. Same template as 09/10 (Triumvirate), applied to Apocalypse.
#
#   Mentalism -> Elementalism (Alteration -> Destruction): earth and weather are Elementalism's
#     ("fire, earth, water and air"); Mentalism is hardened air and telekinetic impulse.
#       Talons of Vyn, Raise Wall, Undermine, Entomb, Thrumming Stone, Control Weather
#   Mentalism -> Entropy (Alteration -> Conjuration):
#       Wither (a withering slow), Prepare for Adventure (conjured gear = Entropy's "otherworldly weapons")
#   Psionics -> Entropy (Illusion -> Conjuration): real, lasting harm or the dead, not illusion
#       Blood for Blood, Pull From Eternity, Magicka Void
# Lore: arch-docs/enderal/magic-schools.md. Review doc: "Apocalypse School Review" (2026-10-15);
# its Light Magic -> Entropy group was deliberately NOT taken (the list keeps offensive Light Magic).
#
# Records (verbatim copies from reference/mods/Apocalypse, guardrail 4; only school fields change):
#   Spells       11 in-place edit of 02's output: HalfCostPerk <old school><tier> -> <new school><tier>
#   MagicEffects 18 copied: MagicSkill -> Destruction / Conjuration. Covers the 11 spells AND their
#                   procs: Talons' hazard spell 097A50 (via explosion 097A47 -> hazard 097A45) and
#                   Wither's stacking-debuff spell 083FCB. Every one is used only by its own spell,
#                   scroll and staff enchantment (arch-docs/magic usedBy, 2026-10-15).
#   Books        11 tome mesh + inventory art -> the new school's
#   Weapons       3 staff Data.Skill (Wither, Undermine, Entomb - the only staffs in the set)
# Untouched on purpose: the 4 proc SPELs' HalfCostPerk (procs are never paid for); the school-less
# MGEFs in the chains (Undermine procs 098FF8/098FFA, PullFromEternity_Ab 085B00, the shared
# AbilityFX 006FB1); the 10 scrolls and 3 staff ENCHs (their school comes from the MGEFs above);
# distribution (the ZP_Apoc_Tomes_R* lists are by tier, not school). Scripts: WB_Undermine_Script,
# WB_BloodForBlood_Script and WB_ManaVoid_Script hardcode Game.AdvanceSkill("Alteration"/"Illusion"),
# which is inert in Enderal (no skill-use advancement, arch-docs/enderal/progression-and-classes.md),
# so they are not recompiled. No other script on the chains reads a skill (decompiled 2026-10-15).
#
# ORDER: 02 -> 03 -> 11 (02 rewrites the Apocalypse spells). Safe to re-run on its own.
# PS 5.1. Every replacement is counted and asserted (CRLF regex trap, CLAUDE.md guardrail 10).
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$ref = Join-Path $repoRoot 'reference\mods\Apocalypse'
$esp = Join-Path $repoRoot 'src\MagicPatches\MagicPatchesESP'
if (-not (Test-Path $ref)) { throw "reference tree missing: $ref - run /spriggit-decompile-reference on the converted Apocalypse esp first" }

$suffix = '_Apocalypse - Magic of Skyrim.esp.yaml'
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
    return $count
}

# Self-check: re-derive the schooled MGEFs reachable from a group's spells + procs in the
# reference tree and require it to equal the listed set (catches an Apocalypse update that adds
# or re-schools an effect).
function Assert-MgefSet([string[]]$chain, [string[]]$oldSchool, [string[]]$listed, [string]$what) {
    $derived = New-Object System.Collections.Generic.SortedSet[string]
    foreach ($hex in $chain) {
        $text = [System.IO.File]::ReadAllText((Find-Ref 'Spells' $hex).FullName)
        foreach ($m in [regex]::Matches($text, 'BaseEffect: ([0-9A-F]{6}):Apocalypse - Magic of Skyrim\.esp')) {
            $e = $m.Groups[1].Value
            $mt = [System.IO.File]::ReadAllText((Find-Ref 'MagicEffects' $e).FullName)
            $sk = [regex]::Match($mt, '(?m)^MagicSkill: (\S+)(?=\r?$)')
            if ($sk.Success) {
                if ($oldSchool -notcontains $sk.Groups[1].Value) { throw "${what}: MGEF $e is $($sk.Groups[1].Value), expected one of $oldSchool" }
                [void]$derived.Add($e)
            }
        }
    }
    $set = New-Object System.Collections.Generic.SortedSet[string] (, [string[]]$listed)
    if (-not $derived.SetEquals($set)) { throw "${what}: MGEF list drifted: reference chain has [$($derived -join ',')], script lists [$($set -join ',')]" }
}

# Tome mesh + inventory art per school (vanilla HighPoly<School>Book STATs).
$tome = @{
    Alteration  = @('SpellTomeAlterationLowPoly.nif',  'InventoryArt: 02FBB3:Skyrim.esm')
    Illusion    = @('SpellTomeIllusionLowPoly.nif',    'InventoryArt: 02FBB4:Skyrim.esm')
    Destruction = @('SpellTomeDestructionLowPoly.nif', 'InventoryArt: 02FBB5:Skyrim.esm')
    Conjuration = @('SpellTomeConjurationLowPoly.nif', 'InventoryArt: 02FBB6:Skyrim.esm')
}
# Half-cost perks by school, Novice00 / Apprentice25 / Adept50 / Expert75 / Master100.
$tiers = @{
    Alteration  = @('0F2CA6', '0C44B7', '0C44B8', '0C44B9', '0C44BA')
    Illusion    = @('0F2CA9', '0C44C3', '0C44C4', '0C44C5', '0C44C6')
    Destruction = @('0F2CA8', '0C44BF', '0C44C0', '0C44C1', '0C44C2')
    Conjuration = @('0F2CA7', '0C44BB', '0C44BC', '0C44BD', '0C44BE')
}

$groups = @(
    @{
        Name   = 'Mentalism -> Elementalism'
        To     = 'Destruction'
        Spells = @('07FE79', '00CC14', '002E31', '04581C', '124EC7', '084A9C')
        Procs  = @('097A50', '098FF6')   # Talons hazard spell; Undermine proc (its MGEFs are school-less)
        Mgefs  = @(
            '097A48', '097A4E', '097A55', # Talons of Vyn: place explosion / hazard / rock spike
            '09852E', '09852F',           # Raise Wall + Fail
            '098A93',                     # Undermine
            '0AE5AE', '0ABFE0', '0AE5BA', # Entomb: spawner / entomb / panic
            '0A5392',                     # Thrumming Stone
            '07FE70'                      # Control Weather
        )
        Books  = @{ Alteration = @('047E25', '03C519', '03C520', '03F65B', '03C530', '089704') }
        Staffs = @{ Alteration = @('0896FA', '07A7B3') }   # Undermine, Entomb
    },
    @{
        Name   = 'Mentalism/Psionics -> Entropy'
        To     = 'Conjuration'
        Spells = @('12649C', '007FFD', '127FA7', '085B03', '00B5B7')
        Procs  = @('083FCB', '085B01')   # Wither stacking debuff; Pull From Eternity ability (school-less)
        Mgefs  = @(
            '12649A', '0A5397', '083FCA', # Wither + stacking debuff attack / speed
            '0DD9D0',                     # Prepare for Adventure
            '0488FF',                     # Blood for Blood
            '085AFA',                     # Pull From Eternity
            '00B5B6'                      # Magicka Void
        )
        Books  = @{ Alteration = @('03C51E', '089703'); Illusion = @('03E608', '08970D', '03E611') }
        Staffs = @{ Alteration = @('07A79A') }             # Wither
    }
)

$spellDir = Join-Path $esp 'Spells'
$totals = @{ MagicEffects = 0; Books = 0; Weapons = 0; Spells = 0 }
foreach ($g in $groups) {
    $to = $g.To
    Write-Host $g.Name
    Assert-MgefSet ($g.Spells + $g.Procs) @('Alteration', 'Illusion') $g.Mgefs $g.Name

    # ---- MagicEffects: MagicSkill -> new school (each MGEF is Alteration or Illusion) ------------
    $n = 0
    foreach ($hex in $g.Mgefs) {
        $mt = [System.IO.File]::ReadAllText((Find-Ref 'MagicEffects' $hex).FullName)
        $from = [regex]::Match($mt, '(?m)^MagicSkill: (\S+)(?=\r?$)').Groups[1].Value
        $n += Copy-WithEdits 'MagicEffects' @($hex) @(, @("MagicSkill: $from", "MagicSkill: $to"))
    }
    Write-Host ("  {0,-13} {1} overrides" -f 'MagicEffects', $n); $totals.MagicEffects += $n

    # ---- Books: tome mesh + inventory art ------------------------------------------------------
    $n = 0
    foreach ($from in $g.Books.Keys) {
        $n += Copy-WithEdits 'Books' $g.Books[$from] @(
            @($tome[$from][0], $tome[$to][0]),
            @($tome[$from][1], $tome[$to][1])
        )
    }
    Write-Host ("  {0,-13} {1} overrides" -f 'Books', $n); $totals.Books += $n

    # ---- Weapons: staff skill ------------------------------------------------------------------
    $n = 0
    foreach ($from in $g.Staffs.Keys) {
        $n += Copy-WithEdits 'Weapons' $g.Staffs[$from] @(, @("Skill: $from", "Skill: $to"))
    }
    Write-Host ("  {0,-13} {1} overrides" -f 'Weapons', $n); $totals.Weapons += $n

    # ---- Spells: HalfCostPerk in 02's generated overrides --------------------------------------
    $moved = 0; $already = 0
    foreach ($hex in $g.Spells) {
        $hits = @(Get-ChildItem $spellDir -Filter "* - ${hex}$suffix")
        if ($hits.Count -ne 1) { throw "Spells ${hex}: no override from 02 - run 02-apply-cost-table.ps1 first" }
        $f = $hits[0]
        $text = [System.IO.File]::ReadAllText($f.FullName)
        $m = [regex]::Match($text, '(?m)^HalfCostPerk: ([0-9A-F]{6}):Skyrim\.esm(?=\r?$)')
        if (-not $m.Success) { throw "$($f.Name): no HalfCostPerk line" }
        $cur = $m.Groups[1].Value
        if ($tiers[$to] -contains $cur) { $already++; continue }
        $tier = -1
        foreach ($s in @('Alteration', 'Illusion')) { $i = [array]::IndexOf($tiers[$s], $cur); if ($i -ge 0) { $tier = $i } }
        if ($tier -lt 0) { throw "$($f.Name): unexpected HalfCostPerk $cur" }
        $text = Replace-Exact $text "HalfCostPerk: ${cur}:Skyrim.esm" "HalfCostPerk: $($tiers[$to][$tier]):Skyrim.esm" 1 $f.Name
        [System.IO.File]::WriteAllText($f.FullName, $text, $utf8)
        $moved++
    }
    if ($moved + $already -ne $g.Spells.Count) { throw "Spells: handled $($moved + $already) of $($g.Spells.Count)" }
    Write-Host ("  {0,-13} {1} moved, {2} already {3}" -f 'Spells', $moved, $already, $to); $totals.Spells += $moved + $already
}

if ($totals.MagicEffects -ne 18 -or $totals.Books -ne 11 -or $totals.Weapons -ne 3 -or $totals.Spells -ne 11) {
    throw "totals drifted: $($totals.MagicEffects) MGEF / $($totals.Books) BOOK / $($totals.Weapons) WEAP / $($totals.Spells) SPEL (expected 18/11/3/11)"
}
Write-Host 'next: build/build.ps1'
