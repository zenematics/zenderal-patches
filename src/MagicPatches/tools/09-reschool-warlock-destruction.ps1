# Move Triumvirate's five Warlock "Destruction" spells (Eldritch Blast, Balefire, Witch Bolt,
# Cloudkill, Hurl Into Sinistra) from Elementalism to Entropy, with their tomes and staves.
#
# Why (arch-docs/enderal/magic-schools.md): Elementalism is environment-drawn fire/frost/shock
# magic; these are raw/magic/poison damage + spirit binding - Entropy's necromancy. And no
# Elementalist damage/duration perk applies to them (every one keys MagicDamageFire/Frost/Shock
# or MagicRune, which these effects lack), so the move costs no perk benefit and puts the whole
# Warlock kit - damage, summons, curses - under the Sinistrope tree.
#
# Records (all verbatim copies, guardrail 4; only the school fields change):
#   Spells       5  in-place edit of 06's output: HalfCostPerk Destruction<tier> -> Conjuration<tier>
#                   (Sinistrope's "... of the Dark Arts" discounts test Conjuration*/Illusion* perks)
#   MagicEffects 7  copied from reference/mods/Triumvirate: MagicSkill Destruction -> Conjuration
#                   (= Entropy). All 7 are used ONLY by these spells and their staff enchantments;
#                   the shared vanilla Stagger 0153D3 and the school-less Bind Spirit/Prey MGEFs stay.
#   Books        5  copied: Destruction tome mesh + inventory art -> the Conjuration ones
#                   (what Triumvirate's own Warlock summon tomes and Enderal's Entropy tomes use)
#   Weapons      4  copied: staff Data.Skill Destruction -> Conjuration (Hurl has no staff)
# Untouched on purpose: the 4 staff ENCH (they only point at the MGEFs above); the tome/staff
# leveled lists (all three Warlock schools go to the same merchants: BashHole, Sister Envy,
# Wildmage Undercity); no scrolls exist. Triumvirate's TVR_Branded/Damnation/SoundAndImod
# scripts read no skill or school (decompiled 2026-10-13), so nothing scripted needs changing.
#
# ORDER: 06 -> 07 -> 09. Re-running 06 regenerates the Spells folder and wipes the HalfCostPerk
# edits; this script then re-applies them. Safe to re-run on its own (already-moved spells are
# skipped, the other three folders are rebuilt from reference).
#
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

Write-Host 'Warlock Destruction -> Entropy'

# ---- MagicEffects: Destruction -> Conjuration (displayed as Entropy) -------------------------
$mgefs = @(
    '19B464', # TVR_Warlock_Balefire_Effect_EldritchBlast
    '1A0580', # TVR_Warlock_Hellfire_Effect_Balefire
    '1AF894', # TVR_Warlock_Hellfire_Effect_Balefire_Poison
    '1A0587', # TVR_Warlock_Hellfire_Effect_Cloudkill
    '1AF897', # TVR_Warlock_Balefire_Effect_HurlIntoOblivion_Aoe
    '1AF89C', # TVR_Warlock_Balefire_Effect_HurlIntoOblivion_Aoe_Stun
    '1BEBB6'  # TVR_Warlock_Balefire_Effect_WitchBolt
)
Copy-WithEdits 'MagicEffects' $mgefs @(, @('MagicSkill: Destruction', 'MagicSkill: Conjuration'))

# ---- Books: tome mesh + inventory art -----------------------------------------------------
$books = @('419B53', '419B54', '419B55', '419B56', '419B57')
Copy-WithEdits 'Books' $books @(
    @('SpellTomeDestructionLowPoly.nif', 'SpellTomeConjurationLowPoly.nif'),
    @('InventoryArt: 02FBB5:Skyrim.esm', 'InventoryArt: 02FBB6:Skyrim.esm')  # HighPolyDestructionBook -> Conjuration
)

# ---- Weapons: staff skill ----------------------------------------------------------------------
$staves = @('419B42', '419B43', '419B44', '419B45')
Copy-WithEdits 'Weapons' $staves @(, @('Skill: Destruction', 'Skill: Conjuration'))

# ---- Spells: HalfCostPerk in 06's generated overrides ----------------------------------------
$perkMap = [ordered]@{
    '0F2CA8:Skyrim.esm' = '0F2CA7:Skyrim.esm'  # DestructionNovice00     -> ConjurationNovice00
    '0C44BF:Skyrim.esm' = '0C44BB:Skyrim.esm'  # DestructionApprentice25 -> ConjurationApprentice25
    '0C44C0:Skyrim.esm' = '0C44BC:Skyrim.esm'  # DestructionAdept50      -> ConjurationAdept50
    '0C44C1:Skyrim.esm' = '0C44BD:Skyrim.esm'  # DestructionExpert75     -> ConjurationExpert75
    '0C44C2:Skyrim.esm' = '0C44BE:Skyrim.esm'  # DestructionMaster100    -> ConjurationMaster100
}
$spells = @('19B465', '1A0577', '1AF89A', '1A0588', '1AF898')
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
