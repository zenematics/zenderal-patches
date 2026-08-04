#requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repo = 'C:\modding\mod-projects\zenderal-patches'
$apoc = Join-Path $repo 'reference\mods\Apocalypse\esp'
$dst  = Join-Path $repo 'src\Apocalypse\ApocalypseESP'
$enc  = New-Object System.Text.UTF8Encoding($false)

# old -> new, ordered longest-first so no pair is a prefix of another
$renames = [ordered]@{
  "Silmane's Spell Sentinel"        = 'Spell Sentinel'
  "Welloc's Instant Forest"         = 'Instant Forest'
  "Hrormir's Misdirection"          = 'Veil of Misdirection'
  "Malviser's Gauntlet"             = 'Telekinetic Gauntlet'
  "Hethoth's Grimoire"              = 'Eventuality Grimoire'
  "Sotha's Maelstrom"               = 'Thaumaturgic Maelstrom'
  "Stendarr's Embrace"              = "Erodan's Embrace"
  "Medora's Memory"                 = "Esara's Memory"
  "Meridia's Wrath"                 = "Malphas' Wrath"
  "Ocato's Recital"                 = "Baledor's Recital"
  "Tharn's Prison"                  = "Girath" + [char]0x00FB + "'s Prison"   # Girathu-circumflex
  'Oblivion Unbound'                = 'Sinistra Unbound'
  'Breath of Arkay'                 = 'Breath of Tyr'
  'Talons of Nirn'                  = 'Talons of Vyn'
  'Lamb of Mara'                    = 'Lamb of Irlanda'
  "Reynos' Fins"                    = 'Fins of Kil' + [char]0x00E9                # Kile-acute
  # description-only rewrites
  'Banish a living creature to Oblivion.' = 'Banish a living creature into the Sea of Eventualities.'
  'serving the will of the Dragonborn.'   = 'serving your will.'
}

# folders that can hold user-visible strings for these spells
$dirs = 'Books','Spells','Scrolls','MagicEffects','Perks','Weapons','Messages'

$touched = 0; $byDir = @{}; $perName = @{}
foreach ($dir in $dirs) {
  $srcDir = Join-Path $apoc $dir
  if (-not (Test-Path $srcDir)) { continue }
  foreach ($f in Get-ChildItem "$srcDir\*.yaml") {
    $inSrc   = Join-Path (Join-Path $dst $dir) $f.Name
    $origin  = if (Test-Path $inSrc) { $inSrc } else { $f.FullName }
    $t       = [IO.File]::ReadAllText($origin)
    $t2      = $t
    $applied = @()
    foreach ($old in $renames.Keys) {
      if ($t2.Contains($old)) {
        $n = ([regex]::Matches($t2, [regex]::Escape($old))).Count
        $t2 = $t2.Replace($old, $renames[$old])
        $applied += $old
        $perName[$old] = $n + $(if ($perName.ContainsKey($old)) { $perName[$old] } else { 0 })
      }
    }
    if ($applied.Count -eq 0) { continue }
    $outDir = Join-Path $dst $dir
    New-Item -ItemType Directory -Force $outDir | Out-Null
    [IO.File]::WriteAllText((Join-Path $outDir $f.Name), $t2, $enc)
    $touched++
    $byDir[$dir] = 1 + $(if ($byDir.ContainsKey($dir)) { $byDir[$dir] } else { 0 })
  }
}

"Records overridden for renames: $touched"
''
'-- by record type --'
$byDir.GetEnumerator() | Sort-Object Name | ForEach-Object { "  {0,-14} {1,3}" -f $_.Key, $_.Value }
''
'-- string replacements applied --'
foreach ($old in $renames.Keys) {
  $c = if ($perName.ContainsKey($old)) { $perName[$old] } else { 0 }
  $flag = if ($c -eq 0) { '  <-- NEVER MATCHED' } else { '' }
  "  {0,-42} -> {1,-42} x{2}{3}" -f $old, $renames[$old], $c, $flag
}
''
$missed = @($renames.Keys | Where-Object { -not $perName.ContainsKey($_) })
if ($missed.Count -gt 0) { throw "these renames matched nothing: $($missed -join '; ')" }
'All renames matched at least one record.'
