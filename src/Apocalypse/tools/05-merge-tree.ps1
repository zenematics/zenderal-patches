#requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Build the merged Apocalypse tree: Enai's records + our edits, minus the groups we drop.
$repo = 'C:\modding\mod-projects\zenderal-patches'
$ref  = Join-Path $repo 'reference\mods\Apocalypse\esp'
$dst  = Join-Path $repo 'src\Apocalypse\ApocalypseESP'
$enc  = New-Object System.Text.UTF8Encoding($false)

# Groups deliberately NOT carried over from Enai's tree:
#   ConstructibleObjects - all 67 are the Dragonborn staff recipes (134 of the 138 DLC refs)
#   Worldspaces          - its only record overrides Enderal's MQP01Home with Tamriel's data
$skipGroups = @('ConstructibleObjects','Worldspaces')

$before = @(Get-ChildItem $dst -Recurse -Filter *.yaml -File).Count
"our edits already present : $before files"

$copied = 0; $kept = 0
foreach ($f in Get-ChildItem $ref -Recurse -File) {
  $rel = $f.FullName.Substring($ref.Length + 1)
  $grp = $rel.Split('\')[0]
  if ($skipGroups -contains $grp) { continue }
  if ($rel -eq 'RecordData.yaml' -or $rel -eq 'spriggit-meta.json') { continue }  # header written below
  $target = Join-Path $dst $rel
  if (Test-Path -LiteralPath $target) { $kept++; continue }                        # our edit wins
  $dir = Split-Path $target -Parent
  if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force $dir | Out-Null }
  Copy-Item -LiteralPath $f.FullName -Destination $target
  $copied++
}
"copied from Enai's tree   : $copied"
"our edits preserved       : $kept"

# --- drop our now-redundant MQP01Home forward: we no longer override 00003C at all ---
$mq = Join-Path $dst 'Worldspaces\MQP01Home - 00003C_Skyrim.esm'
if (Test-Path -LiteralPath $mq) {
  Get-ChildItem $mq -File | ForEach-Object { Remove-Item -LiteralPath $_.FullName -Force }
  Remove-Item -LiteralPath $mq -Force
  $ws = Join-Path $dst 'Worldspaces'
  if ((Test-Path -LiteralPath $ws) -and @(Get-ChildItem $ws).Count -eq 0) { Remove-Item -LiteralPath $ws -Force }
  "removed the MQP01Home forward (no worldspace override remains)"
}

# --- re-home our six new records into Apocalypse's own FormID space ---
$map = [ordered]@{
  '000800' = '1C1E71'   # ZP_Apoc_Tomes_R000
  '000801' = '1C1E72'   # ZP_Apoc_Tomes_R025
  '000802' = '1C1E73'   # ZP_Apoc_Tomes_R050
  '000803' = '1C1E74'   # ZP_Apoc_Tomes_R075
  '000804' = '1C1E75'   # ZP_Apoc_Tomes_R100
  '000805' = '1C1E76'   # ZP_Apoc_Scrolls
}
$oldMaster = 'Zenderal - Apocalypse.esp'
$newMaster = 'Apocalypse - Magic of Skyrim.esp'

# rewrite references inside every file
$refHits = @{}
foreach ($f in Get-ChildItem $dst -Recurse -Filter *.yaml -File) {
  $t = [IO.File]::ReadAllText($f.FullName); $o = $t
  foreach ($k in $map.Keys) {
    $needle = "${k}:$oldMaster"
    if ($t.Contains($needle)) {
      $n = ([regex]::Matches($t, [regex]::Escape($needle))).Count
      $refHits[$k] = $n + $(if ($refHits.ContainsKey($k)) { $refHits[$k] } else { 0 })
      $t = $t.Replace($needle, "$($map[$k]):$newMaster")
    }
  }
  if ($t -ne $o) { [IO.File]::WriteAllText($f.FullName, $t, $enc) }
}
''
'-- sublist references rewritten in host lists --'
foreach ($k in $map.Keys) {
  $c = if ($refHits.ContainsKey($k)) { $refHits[$k] } else { 0 }
  "   {0} -> {1}   {2} reference(s){3}" -f $k, $map[$k], $c, $(if ($c -eq 0) { '   <-- NEVER REFERENCED' } else { '' })
}
$missed = @($map.Keys | Where-Object { -not $refHits.ContainsKey($_) })
if ($missed.Count) { throw "these sublists are referenced by nothing: $($missed -join ', ')" }

# rename the six record files themselves
$renamed = 0
foreach ($f in Get-ChildItem (Join-Path $dst 'LeveledItems') -Filter *.yaml -File) {
  if ($f.Name -match " - ([0-9A-F]{6})_$([regex]::Escape($oldMaster))\.yaml$") {
    $old = $Matches[1]
    if (-not $map.Contains($old)) { throw "unexpected own-record FormID $old in $($f.Name)" }
    $newName = $f.Name -replace " - $old`_$([regex]::Escape($oldMaster))\.yaml$", " - $($map[$old])_$newMaster.yaml"
    $t = [IO.File]::ReadAllText($f.FullName)
    $t = $t.Replace("FormKey: ${old}:$oldMaster", "FormKey: $($map[$old]):$newMaster")
    [IO.File]::WriteAllText((Join-Path $f.DirectoryName $newName), $t, $enc)
    Remove-Item -LiteralPath $f.FullName -Force
    $renamed++
  }
}
"record files re-homed     : $renamed"
if ($renamed -ne 6) { throw "expected to re-home 6 records, did $renamed" }

# --- header ---
$header = @"
SpriggitSource:
  PackageName: Spriggit.Yaml.Skyrim
  Version: 0.40
ModKey: Apocalypse - Magic of Skyrim.esp
GameRelease: EnderalSE
ModHeader:
  Stats:
    Version: 1.7
  Author: Enai Siaion / Zenderal
  Description: >-
    Apocalypse - Magic of Skyrim by Enai Siaion, converted for Enderal: Forgotten Stories by
    Zenderal. Form version lowered to 1.70 so Enderal's 1.5.97 engine will load it, Dragonborn
    master removed, staff recipes and the Tamriel worldspace override deleted, Elder Scrolls
    proper nouns renamed, and the spell tomes and scrolls distributed through Enderal's own
    vendor and loot lists. Original mod and all assets are Enai Siaion's.
  MasterReferences:
  - Master: Skyrim.esm
    FileSize: 0
  - Master: Update.esm
    FileSize: 0
  INTV: 1
"@
[IO.File]::WriteAllText((Join-Path $dst 'RecordData.yaml'), ($header -replace "`r?`n", "`r`n"), $enc)

$meta = @"
{
  "PackageName": "Spriggit.Yaml.Skyrim",
  "Version": "0.40.0",
  "Release": "EnderalSE",
  "ModKey": "Apocalypse - Magic of Skyrim.esp"
}
"@
[IO.File]::WriteAllText((Join-Path $dst 'spriggit-meta.json'), ($meta -replace "`r?`n", "`r`n"), $enc)

''
$total = @(Get-ChildItem $dst -Recurse -Filter *.yaml -File | Where-Object { $_.Name -ne 'RecordData.yaml' -or $_.DirectoryName -ne $dst }).Count
"merged tree total records : $total"
'-- Dragonborn references remaining --'
$dragon = @(Get-ChildItem $dst -Recurse -Filter *.yaml -File | Where-Object { ([IO.File]::ReadAllText($_.FullName)) -match 'Dragonborn\.esm' })
if ($dragon.Count -eq 0) { '   none' } else { $dragon | ForEach-Object { "   $($_.Name)" } }
