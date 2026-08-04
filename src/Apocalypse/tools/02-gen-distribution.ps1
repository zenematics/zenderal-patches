#requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repo    = 'C:\modding\mod-projects\zenderal-patches'
$apoc    = Join-Path $repo 'reference\mods\Apocalypse\esp'
$enderal = Join-Path $repo 'reference\base\Skyrim\LeveledItems'
$out     = Join-Path $repo 'src\Apocalypse\ApocalypseESP\LeveledItems'
$modKey  = 'Zenderal - Apocalypse.esp'
$enc     = New-Object System.Text.UTF8Encoding($false)

New-Item -ItemType Directory -Force $out | Out-Null

# --- the 15 summons cut as un-Enderal (Daedra + Atronach + Dwemer) -------------
$removed = @(
  'WB_C025_ConjureDremoraChurl',      'WB_C050_ConjureDremoraPitFighter',
  'WB_C075_ConjureDremoraChampion',   'WB_C075_ConjureDremoraHonorGuard',
  'WB_C075_ConjureDremoraMentor',     'WB_C100_ConjureDremoraAssassin',
  'WB_C050_ConjureXivilaiSorcerer',   'WB_C075_ConjureXivilaiLord',
  'WB_C100_ConjureWeepingDaedra',     'WB_C100_ConjureLordOfBindings',
  'WB_C075_SixDemonBag',              'WB_C075_ConjureHerne',
  'WB_C100_ConjureKyrkrim',           'WB_C025_AtronachMark',
  'WB_C100_ConjureCraftlord'
)

function Read-Recs([string]$dir) {
  Get-ChildItem (Join-Path $apoc "$dir\*.yaml") | ForEach-Object {
    $t = [IO.File]::ReadAllText($_.FullName)
    [pscustomobject]@{
      EditorID = [regex]::Match($t, '(?m)^EditorID: (.+?)\s*$').Groups[1].Value
      FormKey  = [regex]::Match($t, '(?m)^FormKey: (.+?)\s*$').Groups[1].Value
    }
  }
}

function New-LeveledList {
  param([string]$Hex, [string]$EditorID, [object[]]$Refs, [int]$Level = 1)
  $sb = New-Object Text.StringBuilder
  [void]$sb.AppendLine("FormKey: ${Hex}:$modKey")
  [void]$sb.AppendLine("EditorID: $EditorID")
  [void]$sb.AppendLine('Version2: 1')
  [void]$sb.AppendLine('Flags:')
  [void]$sb.AppendLine('- CalculateFromAllLevelsLessThanOrEqualPlayer')
  [void]$sb.AppendLine('- CalculateForEachItemInCount')
  [void]$sb.AppendLine('Entries:')
  foreach ($r in $Refs) {
    [void]$sb.AppendLine('- Data:')
    [void]$sb.AppendLine("    Level: $Level")
    [void]$sb.AppendLine("    Reference: $($r.FormKey)")
    [void]$sb.AppendLine('    Count: 1')
  }
  $path = Join-Path $out "$EditorID - ${Hex}_$modKey.yaml"
  [IO.File]::WriteAllText($path, $sb.ToString(), $enc)
  "  {0}  {1,-24} {2,3} entries" -f $Hex, $EditorID, $Refs.Count
}

# --- tome sublists, one per Apocalypse spell rank -----------------------------
$books = Read-Recs 'Books' | Where-Object { $_.EditorID -match '^WB_[ACDIR](000|025|050|075|100)_.+_Book$' }
$keptBooks = $books | Where-Object { $b = $_.EditorID -replace '_Book$',''; $removed -notcontains $b }
$cutBooks  = $books | Where-Object { $b = $_.EditorID -replace '_Book$',''; $removed -contains $b }

'Tome sublists:'
$rankHex = @{ '000' = '000800'; '025' = '000801'; '050' = '000802'; '075' = '000803'; '100' = '000804' }
foreach ($rank in '000','025','050','075','100') {
  $refs = @($keptBooks | Where-Object { $_.EditorID -match "^WB_[ACDIR]$rank`_" } | Sort-Object EditorID)
  New-LeveledList -Hex $rankHex[$rank] -EditorID "ZP_Apoc_Tomes_R$rank" -Refs $refs
}

# --- scroll sublist -----------------------------------------------------------
$scrolls = Read-Recs 'Scrolls'
$keptScrolls = @($scrolls | Where-Object { $s = $_.EditorID -replace '_Scroll$',''; $removed -notcontains $s } | Sort-Object EditorID)
$cutScrolls  = @($scrolls | Where-Object { $s = $_.EditorID -replace '_Scroll$',''; $removed -contains $s })
"`nScroll sublist:"
New-LeveledList -Hex '000805' -EditorID 'ZP_Apoc_Scrolls' -Refs $keptScrolls

"`nCut from distribution: $($cutBooks.Count) tomes, $($cutScrolls.Count) scrolls"
if ($cutBooks.Count -ne 15) { throw "expected 15 cut tomes, got $($cutBooks.Count)" }
$cutScrolls | ForEach-Object { "   scroll cut: $($_.EditorID)" }

# --- inject one entry into each Enderal host list -----------------------------
# hostFile = @( @{ Sub = '000800'; Level = 1 }, ... )
#
# LOOT ONLY. The four _00ETraderSpellBooksLevel* vendor lists used to be injected here too, and are
# not any more: a leveled list is rolled per draw, so a shop's Apocalypse stock stayed random no
# matter how it was weighted, and most of the 160 tomes were purchasable nowhere at all.
# 07-place-vendor-tomes.ps1 writes them straight into six named merchant chests instead. Random is
# the right shape for loot and the wrong shape for a shop.
$injections = @{
  '_00E_SpellBooksLootA - 13798C_Skyrim.esm.yaml'       = @(@{S='000800';L=1},  @{S='000801';L=5})
  '_00E_SpellBooksLootB - 13798D_Skyrim.esm.yaml'       = @(@{S='000801';L=10})
  '_00E_SpellBooksLootC - 1447A2_Skyrim.esm.yaml'       = @(@{S='000802';L=18}, @{S='000803';L=30})
  '_00E_SpellBooksLootD - 1447A3_Skyrim.esm.yaml'       = @(@{S='000803';L=30}, @{S='000804';L=40})
  '00E_ScrollsLowChance - 0905A5_Skyrim.esm.yaml'       = @(@{S='000805';L=1})
}

"`nHost list overrides:"
foreach ($file in ($injections.Keys | Sort-Object)) {
  $srcPath = Join-Path $enderal $file
  if (-not (Test-Path $srcPath)) { throw "host list not found: $srcPath" }
  $t = [IO.File]::ReadAllText($srcPath)
  $before = ([regex]::Matches($t, '(?m)^- Data:')).Count
  $nl = if ($t.Contains("`r`n")) { "`r`n" } else { "`n" }
  if (-not $t.EndsWith($nl)) { $t += $nl }
  $add = ''
  foreach ($inj in $injections[$file]) {
    $add += "- Data:$nl    Level: $($inj.L)$nl    Reference: $($inj.S):$modKey$nl    Count: 1$nl"
  }
  $t2 = $t + $add
  $after = ([regex]::Matches($t2, '(?m)^- Data:')).Count
  if ($after -ne $before + $injections[$file].Count) { throw "entry count wrong for $file" }
  [IO.File]::WriteAllText((Join-Path $out $file), $t2, $enc)
  "  {0,-52} {1,3} -> {2,3} entries" -f ($file -replace ' - .*',''), $before, $after
}
"`nDone."
