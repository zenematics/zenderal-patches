#requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Raise the weight of the ZP_Apoc_* sublists inside Enderal's host leveled lists.
#
# 02-gen-distribution.ps1 injects ONE entry per sublist per host list. That is correct but far too
# thin: all 160 Apocalypse tomes then share a single slot against ~150 individually-listed Enderal
# books, so a big spell vendor (Tarhutie, 8+10+10 draws) yields ~1 Apocalypse tome and a small one
# (Milbert, 3+4 draws) usually yields none. Verified in-game 2026-08-02.
#
# This duplicates each injected entry - same Level, same Reference - until it appears $Target times.
# Duplicating the ENTRY is the right lever: it does not touch a single one of Enderal's own entries
# (guardrail 5), and it keeps one sublist per rank so the diff stays readable.
#
# Idempotent: it counts what is already there and only tops up the difference.

$repo = 'C:\modding\mod-projects\zenderal-patches'
$out  = Join-Path $repo 'src\Apocalypse\ApocalypseESP\LeveledItems'
$enc  = New-Object System.Text.UTF8Encoding($false)

# Target multiplicity per host list. The aim is a comparable Apocalypse share (~11-19% of the spell
# books a player sees) across every list, so no route to the spells is dead.
#
# Two corrections to the first pass, both measured rather than assumed:
#
#  * Loot was set to 3 on the reasoning that those lists "already carry a ChanceNone of 0.3-0.7".
#    That was wrong. ChanceNone gates whether the list yields anything at all; it does not change
#    the ratio of our entries to Enderal's. There is no reason for loot to sit below vendor.
#
#  * LootB gets 8, not 4, because only ONE of our sublists falls in its level band (R025) where
#    A/C/D take two. Left at 4 it ends up on half the share of its neighbours - an artifact of how
#    the ranks map onto Enderal's bands, not a decision anyone made.
#
# The four _00ETraderSpellBooksLevel* vendor lists are NOT here any more. Weighting them was never
# enough: a list is rolled per draw, so a shop's Apocalypse stock stayed random and most of the 160
# tomes were purchasable nowhere. 07-place-vendor-tomes.ps1 puts them straight into six named
# merchant chests instead, and this plugin no longer overrides those four lists at all.
$targets = @{
  '_00E_SpellBooksLootA - 13798C_Skyrim.esm.yaml'       = 4
  '_00E_SpellBooksLootB - 13798D_Skyrim.esm.yaml'       = 8
  '_00E_SpellBooksLootC - 1447A2_Skyrim.esm.yaml'       = 4
  '_00E_SpellBooksLootD - 1447A3_Skyrim.esm.yaml'       = 4
  '00E_ScrollsLowChance - 0905A5_Skyrim.esm.yaml'       = 4
}

# NOTE: the YAML is CRLF, so '$' in a multiline regex will not match (CLAUDE.md guardrail 10).
# Match the line breaks explicitly instead of anchoring.
$entryRx = '(?m)^- Data:\r?\n    Level: (?<lvl>\d+)\r?\n    Reference: (?<ref>1C1E7[0-9A-F]:Apocalypse - Magic of Skyrim\.esp)\r?\n    Count: 1\r?\n'

$totalAdded = 0
foreach ($file in ($targets.Keys | Sort-Object)) {
  $path = Join-Path $out $file
  if (-not (Test-Path $path)) { throw "host list not found: $path" }

  $t      = [IO.File]::ReadAllText($path)
  $nl     = if ($t.Contains("`r`n")) { "`r`n" } else { "`n" }
  $before = ([regex]::Matches($t, '(?m)^- Data:')).Count

  $matches = @([regex]::Matches($t, $entryRx))
  if ($matches.Count -eq 0) { throw "no ZP_Apoc entry found in $file - has 02-gen-distribution run?" }

  # Collapse to distinct (Level, Reference) injections and how many copies each already has.
  $seen = @{}
  foreach ($m in $matches) {
    $key = '{0}|{1}' -f $m.Groups['lvl'].Value, $m.Groups['ref'].Value
    if ($seen.ContainsKey($key)) { $seen[$key]++ } else { $seen[$key] = 1 }
  }

  $target = $targets[$file]
  $add    = ''
  $added  = 0
  foreach ($key in ($seen.Keys | Sort-Object)) {
    $parts = $key -split '\|', 2
    $need  = $target - $seen[$key]
    if ($need -lt 0) { throw "$file already has $($seen[$key]) copies of $key, above target $target" }
    for ($i = 0; $i -lt $need; $i++) {
      $add += "- Data:$nl    Level: $($parts[0])$nl    Reference: $($parts[1])$nl    Count: 1$nl"
      $added++
    }
  }

  if ($added -gt 0) {
    if (-not $t.EndsWith($nl)) { $t += $nl }
    $t += $add
    [IO.File]::WriteAllText($path, $t, $enc)
  }

  $after = ([regex]::Matches($t, '(?m)^- Data:')).Count
  if ($after -ne $before + $added) { throw "entry count wrong for ${file}: $before + $added != $after" }

  $ours = ([regex]::Matches($t, $entryRx)).Count
  if ($ours -ne $seen.Keys.Count * $target) {
    throw "${file}: expected $($seen.Keys.Count * $target) ZP_Apoc entries at target $target, got $ours"
  }

  $totalAdded += $added
  "  {0,-34} {1,3} -> {2,3} entries   ({3} ours = {4} injections x{5})" -f `
    ($file -replace ' - .*',''), $before, $after, $ours, $seen.Keys.Count, $target
}

"`nAdded $totalAdded entries."
if ($totalAdded -eq 0) { "(already at target - nothing to do)" }
