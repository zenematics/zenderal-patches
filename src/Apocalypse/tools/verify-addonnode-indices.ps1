#requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# AddonNode (ADDN) records carry a NodeIndex; two records sharing an index is what
# Engine Fixes warns about. Collect every index in play.
$repo = 'C:\modding\mod-projects\zenderal-patches'

function Get-Nodes($root, $label) {
  $dir = Join-Path $root 'AddonNodes'
  if (-not (Test-Path $dir)) { return @() }
  $out = @()
  foreach ($f in Get-ChildItem $dir -Filter *.yaml -File) {
    $t = [IO.File]::ReadAllText($f.FullName)
    $idx = $null; $ed = $null
    if ($t -match '(?m)^NodeIndex:\s*(-?\d+)') { $idx = [int]$Matches[1] }
    if ($t -match '(?m)^EditorID:\s*(.+?)\s*$') { $ed = $Matches[1] }
    $out += [pscustomobject]@{ Source=$label; Index=$idx; EditorID=$ed; File=$f.Name }
  }
  ,$out
}

$all = @()
$all += Get-Nodes (Join-Path $repo 'reference\base\Skyrim')   'Enderal (Skyrim.esm)'
$all += Get-Nodes (Join-Path $repo 'reference\base\EnderalFS') 'Forgotten Stories'
$all += Get-Nodes (Join-Path $repo 'reference\base\Update')    'Update.esm'
$all += Get-Nodes (Join-Path $repo 'reference\mods\Apocalypse\esp') 'Apocalypse'

"AddonNode records found:"
$all | Group-Object Source | Sort-Object Name | ForEach-Object { "  {0,-22} {1}" -f $_.Name, $_.Count }
''
$apoc = @($all | Where-Object { $_.Source -eq 'Apocalypse' })
$base = @($all | Where-Object { $_.Source -ne 'Apocalypse' })
$baseIdx = @{}
foreach ($b in $base) { if ($null -ne $b.Index) { $baseIdx[$b.Index] = $b.EditorID } }

"-- Apocalypse AddonNodes and whether their index collides with Enderal --"
$clash = @()
foreach ($a in ($apoc | Sort-Object Index)) {
  if ($null -eq $a.Index) { "  {0,-46} (no NodeIndex)" -f $a.EditorID; continue }
  if ($baseIdx.ContainsKey($a.Index)) {
    "  index {0,-5} {1,-42} COLLIDES with {2}" -f $a.Index, $a.EditorID, $baseIdx[$a.Index]
    $clash += $a
  } else {
    "  index {0,-5} {1,-42} free" -f $a.Index, $a.EditorID
  }
}
''
"collisions: $($clash.Count)"
if ($clash.Count) {
  $used = New-Object 'System.Collections.Generic.HashSet[int]'
  foreach ($x in $all) { if ($null -ne $x.Index) { [void]$used.Add($x.Index) } }
  $free = @(); $i = 1
  while ($free.Count -lt $clash.Count -and $i -lt 4000) { if (-not $used.Contains($i)) { $free += $i }; $i++ }
  "lowest free indices available: $($free -join ', ')"
}
