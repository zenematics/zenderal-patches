#requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Place every Apocalypse spell tome directly into a named Enderal merchant chest.
#
# WHY THIS EXISTS. Injecting sublists into Enderal's vendor leveled lists (02/03/06) makes the tomes
# *available* but never *findable*: a list is rolled per draw, so which spells a shop has is random,
# most of the 160 are never purchasable anywhere, and a player hunting one specific spell has no
# route to it. Weighting was raised twice and it still did not deliver in play. Direct placement is
# deterministic - every tome is buyable from one known shop, forever.
#
# Vendors are ranked by the gold in their chest, richest selling the master spells. The Adept tier
# splits by magic school so the two middle vendors each get a share.
#
# The loot lists (_00E_SpellBooksLoot*) keep their random injections. Random is the right shape for
# loot; it is the wrong shape for a shop.

$repo = 'C:\modding\mod-projects\zenderal-patches'
$src  = Join-Path $repo 'reference\base\EnderalFS\Containers'   # FS wins all six - see below
$book = Join-Path $repo 'src\Apocalypse\ApocalypseESP\Books'
$out  = Join-Path $repo 'src\Apocalypse\ApocalypseESP\Containers'
$enc  = New-Object System.Text.UTF8Encoding($false)
$mod  = 'Apocalypse - Magic of Skyrim.esp'

# The 15 summons cut as un-Enderal. Kept in sync with 02-gen-distribution.ps1 by the assertion at
# the end, which requires the placed set to equal exactly 160 tomes.
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

# --- the six chests -----------------------------------------------------------
#
# NOTE ON TARHUTIE. KataPUMBSpellPack.esp overrides three of Enderal's spell-merchant chests -
# Funkentanz, Turious and Tarhutie - adding the SAME 15 staves (Kata_W_Staff_*) to each, and those
# three shops are the only place those staves are sold. Apocalypse loads after it and does not
# master it, so any chest we override loses them. Because the staff set is identical in all three,
# sparing ONE keeps all 15 purchasable. Tarhutie is the one spared, and the Apprentice tier moves to
# Maxus Tabbakus in Duneville instead - 620 gold against Tarhutie's 630, so the wealth ladder barely
# moves. Do not repoint the Apprentice tier back at Tarhutie without re-checking that.
$vendors = @(
  @{ File = '_00E_Merchant_CCFunkentanz - 102AD5_Skyrim.esm.yaml';             Shop = 'Ark, Emberlord and Fireflash'; Gold = 1800; Rank = '100'; Schools = 'ACDIR'; Expect = 45 }
  @{ File = '_00E_Merchant_STTurious - 118050_Skyrim.esm.yaml';                Shop = 'Sun Temple, Torius Flameling'; Gold = 1430; Rank = '075'; Schools = 'ACDIR'; Expect = 39 }
  @{ File = '_00E_Merchant_UC_Barnabas - 13824A_Skyrim.esm.yaml';              Shop = 'Undercity, Barnabas';          Gold = 1050; Rank = '050'; Schools = 'ACD';   Expect = 19 }
  @{ File = '_00E_Merchant_CCSteinschlag - 0F9320_Skyrim.esm.yaml';            Shop = 'Ark, Ora Stonehand';           Gold =  980; Rank = '050'; Schools = 'IR';    Expect = 14 }
  @{ File = '_00E_Merchant_MaxusTabbakus02 - 022BF2_Skyrim.esm.yaml';          Shop = 'Duneville, Maxus Tabbakus';    Gold =  620; Rank = '025'; Schools = 'ACDIR'; Expect = 28 }
  @{ File = '_00E_Merchant_CCMilbert - 127928_Skyrim.esm.yaml';                Shop = 'Ark, Milbert Foxhand';         Gold =  530; Rank = '000'; Schools = 'ACDIR'; Expect = 15 }
)

New-Item -ItemType Directory -Force $out | Out-Null

# --- read every tome out of our own tree --------------------------------------
$tomes = Get-ChildItem (Join-Path $book '*.yaml') | ForEach-Object {
  $t = [IO.File]::ReadAllText($_.FullName)
  [pscustomobject]@{
    EditorID = [regex]::Match($t, '(?m)^EditorID: (.+?)\s*\r?\n').Groups[1].Value
    FormKey  = [regex]::Match($t, '(?m)^FormKey: (.+?)\s*\r?\n').Groups[1].Value
  }
}
$tomes = @($tomes | Where-Object {
  $_.EditorID -match '^WB_[ACDIR](000|025|050|075|100)_.+_Book$' -and
  $removed -notcontains ($_.EditorID -replace '_Book$','')
})
if ($tomes.Count -ne 160) { throw "expected 160 distributable tomes, found $($tomes.Count)" }

# --- write each chest ---------------------------------------------------------
# Always rebuilt from the Forgotten Stories record, never from our own previous output, which makes
# the script idempotent and guarantees we never stack our entries twice.
#
# FS is the WINNING version of all six of these records (guardrail 5) - base Enderal's copy would
# silently revert whatever FS changed, which is the exact mistake 03-forward-leveled-lists.ps1 was
# written to undo for the leveled lists.

$placed = @{}
"{0,-34} {1,5}  {2,-30} {3,5} -> {4,5}" -f 'chest','gold','tier','items','items'
foreach ($v in $vendors) {
  $srcPath = Join-Path $src $v.File
  if (-not (Test-Path $srcPath)) { throw "container not found in Forgotten Stories: $srcPath" }

  $mine = @($tomes | Where-Object {
    $_.EditorID -match "^WB_(?<s>[ACDIR])$($v.Rank)_" -and $v.Schools.Contains($Matches['s'])
  } | Sort-Object EditorID)
  if ($mine.Count -ne $v.Expect) {
    throw "$($v.Shop): expected $($v.Expect) tomes for rank $($v.Rank) schools $($v.Schools), got $($mine.Count)"
  }

  $lines = [IO.File]::ReadAllLines($srcPath)
  $nl    = "`r`n"

  # Find the Items: block and the line that ends it (the next top-level key).
  $start = -1
  for ($i = 0; $i -lt $lines.Length; $i++) { if ($lines[$i] -eq 'Items:') { $start = $i; break } }
  if ($start -lt 0) { throw "$($v.File): no Items: block" }
  $end = -1
  for ($i = $start + 1; $i -lt $lines.Length; $i++) {
    if ($lines[$i] -match '^[A-Za-z]') { $end = $i; break }
  }
  if ($end -lt 0) { $end = $lines.Length }
  $before = @($lines[$start..($end - 1)] | Where-Object { $_ -eq '- Item:' }).Count
  if ($before -eq 0) { throw "$($v.File): Items: block parsed as empty" }

  # COED owner ExtraData is what Spriggit 0.41 corrupts (CLAUDE.md). None of these six carry any;
  # assert it rather than assume, so a future Enderal version that adds one is caught here.
  $blockText = ($lines[$start..($end - 1)] -join $nl)
  if ($blockText -match 'ExtraData|MutagenObjectType') {
    throw "$($v.File): Items: block carries ExtraData - inspect before appending"
  }

  $add = foreach ($m in $mine) { '- Item:'; "    Item: $($m.FormKey)"; '    Count: 1' }
  $new = @()
  $new += $lines[0..($end - 1)]
  $new += $add
  if ($end -lt $lines.Length) { $new += $lines[$end..($lines.Length - 1)] }

  [IO.File]::WriteAllText((Join-Path $out $v.File), (($new -join $nl) + $nl), $enc)

  foreach ($m in $mine) {
    if ($placed.ContainsKey($m.EditorID)) {
      throw "$($m.EditorID) placed twice: $($placed[$m.EditorID]) and $($v.Shop)"
    }
    $placed[$m.EditorID] = $v.Shop
  }

  $after = $before + $mine.Count
  "{0,-34} {1,5}  {2,-30} {3,5} -> {4,5}" -f `
    ($v.File -replace ' - .*',''), $v.Gold, "R$($v.Rank) [$($v.Schools)] $($mine.Count) tomes", $before, $after
}

# --- final assertions ---------------------------------------------------------
if ($placed.Keys.Count -ne 160) { throw "placed $($placed.Keys.Count) tomes, expected 160" }
$missing = @($tomes | Where-Object { -not $placed.ContainsKey($_.EditorID) })
if ($missing.Count -gt 0) { throw "not placed: $($missing.EditorID -join ', ')" }

"`n$($placed.Keys.Count) tomes placed across $($vendors.Count) chests, each in exactly one."
