#requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repo = 'C:\modding\mod-projects\zenderal-patches'
$dst  = Join-Path $repo 'src\Apocalypse\ApocalypseESP\LeveledItems'
$fs   = Join-Path $repo 'reference\base\EnderalFS\LeveledItems'
$base = Join-Path $repo 'reference\base\Skyrim\LeveledItems'
$enc  = New-Object System.Text.UTF8Encoding($false)

# host list -> the sublists injected into it, with the host's own level band
#
# LOOT ONLY - the four _00ETraderSpellBooksLevel* vendor lists were dropped when the tomes moved to
# direct placement on merchant chests (07-place-vendor-tomes.ps1). This plugin no longer overrides
# them, so Forgotten Stories' own copies win untouched.
$inject = [ordered]@{
  '_00E_SpellBooksLootA - 13798C_Skyrim.esm.yaml'       = @(@{S='000800';L=1},  @{S='000801';L=5})
  '_00E_SpellBooksLootB - 13798D_Skyrim.esm.yaml'       = @(@{S='000801';L=10})
  '_00E_SpellBooksLootC - 1447A2_Skyrim.esm.yaml'       = @(@{S='000802';L=18}, @{S='000803';L=30})
  '_00E_SpellBooksLootD - 1447A3_Skyrim.esm.yaml'       = @(@{S='000803';L=30}, @{S='000804';L=40})
  '00E_ScrollsLowChance - 0905A5_Skyrim.esm.yaml'       = @(@{S='000805';L=1})
}

"{0,-46} {1,-9} {2,6} {3,6} {4}" -f 'HOST LIST','SOURCE','WAS','NOW','INJECTED'
foreach ($name in $inject.Keys) {
  # winning source: Forgotten Stories if it overrides the record, else base Enderal
  $srcFile = Join-Path $fs $name
  $origin  = 'FS'
  if (-not (Test-Path -LiteralPath $srcFile)) { $srcFile = Join-Path $base $name; $origin = 'base' }
  if (-not (Test-Path -LiteralPath $srcFile)) { throw "no source record for $name" }

  $text = [IO.File]::ReadAllText($srcFile)
  if ($text -notmatch '(?m)^Entries:') { throw "$name has no Entries block" }

  $wasOurs = 0
  $ourFile = Join-Path $dst $name
  if (Test-Path -LiteralPath $ourFile) {
    $wasOurs = @([regex]::Matches([IO.File]::ReadAllText($ourFile), '(?m)^\s*Reference: [0-9A-F]{6}:')).Count
  }
  $before = @([regex]::Matches($text, '(?m)^\s*Reference: [0-9A-F]{6}:')).Count

  $add = ''
  foreach ($e in $inject[$name]) {
    $add += "- Data:`r`n    Level: $($e.L)`r`n    Reference: $($e.S):Zenderal - Apocalypse.esp`r`n    Count: 1`r`n"
  }
  $text = $text.TrimEnd("`r","`n") + "`r`n" + $add

  $after = @([regex]::Matches($text, '(?m)^\s*Reference: [0-9A-F]{6}:')).Count
  if ($after -ne $before + $inject[$name].Count) { throw "$name : entry count did not grow as expected ($before -> $after)" }

  [IO.File]::WriteAllText((Join-Path $dst $name), $text, $enc)
  "{0,-46} {1,-9} {2,6} {3,6} {4}" -f $name.Substring(0,[Math]::Min(45,$name.Length)), $origin, $wasOurs, $after, (($inject[$name] | ForEach-Object { $_.S }) -join ',')
}
''
'Rewritten from the winning record in every case (FS where FS overrides it).'
