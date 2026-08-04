#requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Which unresolved references does OUR tree have that Enai's original did not?
# Apocalypse already points at thousands of vanilla FormIDs Enderal lacks; those are his, not ours.
$repo = 'C:\modding\mod-projects\zenderal-patches'
$ours = Join-Path $repo 'src\Apocalypse\ApocalypseESP'
$orig = Join-Path $repo 'reference\mods\Apocalypse\esp'

function Load-Set($root) {
  $set = New-Object 'System.Collections.Generic.HashSet[string]'
  if (-not (Test-Path $root)) { return ,$set }
  Get-ChildItem $root -Recurse -Filter *.yaml -File | ForEach-Object {
    if ($_.Name -match ' - ([0-9A-F]{6})_') { [void]$set.Add($Matches[1]) }
  }
  Get-ChildItem $root -Recurse -Filter 'RecordData.yaml' -File | ForEach-Object {
    foreach ($m in [regex]::Matches([IO.File]::ReadAllText($_.FullName), '(?m)^\s*FormKey: ([0-9A-F]{6}):')) {
      [void]$set.Add($m.Groups[1].Value)
    }
  }
  ,$set
}

$sky = Load-Set (Join-Path $repo 'reference\base\Skyrim')
$upd = Load-Set (Join-Path $repo 'reference\base\Update')
$fs  = Load-Set (Join-Path $repo 'reference\base\EnderalFS')
$dbs = Load-Set (Join-Path $repo 'reference\base\Dragonborn-stub')

function Get-Unresolved($tree) {
  $own = Load-Set $tree
  $idx = @{
    'Skyrim.esm' = $sky; 'Update.esm' = $upd
    'Enderal - Forgotten Stories.esm' = $fs
    'Dragonborn.esm' = $dbs
    'Apocalypse - Magic of Skyrim.esp' = $own
    'Zenderal - Apocalypse.esp' = $own
  }
  $bad = @{}
  Get-ChildItem $tree -Recurse -Filter *.yaml -File | ForEach-Object {
    $fname = $_.Name
    foreach ($m in [regex]::Matches([IO.File]::ReadAllText($_.FullName), '\b([0-9A-F]{6}):([^\r\n''"]+?\.(?:esm|esp))\b')) {
      $hex = $m.Groups[1].Value; $mk = $m.Groups[2].Value.Trim()
      if ($hex -eq '000014') { continue }
      if (-not $idx.Contains($mk)) { continue }
      if (-not $idx[$mk].Contains($hex)) {
        $key = "${hex}:$mk"
        if (-not $bad.ContainsKey($key)) { $bad[$key] = @() }
        if ($bad[$key] -notcontains $fname) { $bad[$key] += $fname }
      }
    }
  }
  ,$bad
}

'indexing Enai''s original tree...'
$a = Get-Unresolved $orig
'indexing our converted tree...'
$b = Get-Unresolved $ours

"unresolved FormKeys in ORIGINAL : $($a.Count)"
"unresolved FormKeys in OURS     : $($b.Count)"
''
$new = @($b.Keys | Where-Object { -not $a.ContainsKey($_) })
$gone = @($a.Keys | Where-Object { -not $b.ContainsKey($_) })
"NEW unresolved introduced by us : $($new.Count)"
foreach ($k in ($new | Sort-Object)) { "   $k   in: $(($b[$k] | Select-Object -First 3) -join ', ')" }
''
"resolved BY us (were dangling, now gone) : $($gone.Count)"
