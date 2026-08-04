#requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Rescale Apocalypse's tome and scroll gold values onto Enderal's economy.
#
# WHY. Apocalypse prices its tomes on VANILLA SKYRIM's spell-tome ladder - roughly 50 / 175 / 330 /
# 700 / 1300 for novice through master. Enderal does not use that ladder. Measured against
# reference/base/Skyrim/Books, Enderal's ENTIRE spell-tome range is 20-350, with exactly two
# outliers above it (Paralyze Rank II at 400, the unique Death Storm at 600). Its scrolls run 10-100
# with two at 500.
#
# So Apocalypse's masters at a 1407 median were 5.6x Enderal's top-tier tome, and its X-school
# scrolls at 2500 were 5x Enderal's most expensive scroll - priced like unique weapons rather than
# like books. On a shop shelf next to Enderal's own tomes it reads as another game's currency.
#
# WHAT THIS DOES. A per-tier RATIO, not a flat value: Enai's internal ordering inside each tier is
# preserved exactly, only the scale changes. Tiers are allowed to overlap at the edges, as Enderal's
# own ranks do (its Rank II tops out at 400, above its Rank VI median of 250).
#
# Resulting medians: 45 / 93 / 180 / 279 / 394 against Enderal's Rank I-VI at 30 / 68 / 95 / 140 /
# 180 / 250. Apocalypse still sits above Enderal at the top, which is deliberate: an Enderal spell is
# bought six times as it ranks up (~760 gold all told) while an Apocalypse spell is one purchase at
# terminal power. The ceiling lands under Enderal's 600 Death Storm either way.
#
# Idempotent: values are always recomputed from Enai's untouched tree, never from our own output.

$repo = 'C:\modding\mod-projects\zenderal-patches'
$orig = Join-Path $repo 'reference\mods\Apocalypse\esp'
$mine = Join-Path $repo 'src\Apocalypse\ApocalypseESP'
$enc  = New-Object System.Text.UTF8Encoding($false)

# tier -> multiplier applied to Enai's original value
$tomeRatio = @{ '000' = 0.72; '025' = 0.92; '050' = 0.50; '075' = 0.39; '100' = 0.28 }
$scrollRatio = @{
  'A000'=0.60; 'C000'=0.60; 'D000'=0.60; 'I000'=0.60; 'R000'=0.60; 'X000'=0.30
  'A025'=0.60; 'C025'=0.60; 'D025'=0.60; 'I025'=0.60; 'R025'=0.60
  'A050'=0.60; 'C050'=0.60; 'D050'=0.60; 'I050'=0.60; 'R050'=0.60
  'A075'=0.50; 'C075'=0.50; 'D075'=0.50; 'I075'=0.50; 'R075'=0.50
  'A100'=0.50; 'C100'=0.50; 'D100'=0.50; 'I100'=0.50; 'R100'=0.50; 'X100'=0.20
}

# CRLF: no '$' anchors (CLAUDE.md guardrail 10). A record's gold value is the Value: at column 0 -
# the indented ones are localised name/text strings.
$valueRx = '(?m)^Value: (\d+)(?=\r?\n)'

function Invoke-Reprice {
  param([string]$Folder, [string]$EditorRx, [hashtable]$Ratios, [scriptblock]$KeyOf)

  $changed = 0; $skipped = 0
  $rows = @()
  foreach ($f in Get-ChildItem (Join-Path (Join-Path $mine $Folder) '*.yaml')) {
    $ours = [IO.File]::ReadAllText($f.FullName)
    $eid  = [regex]::Match($ours, '(?m)^EditorID: (.+?)\s*\r?\n').Groups[1].Value
    if ($eid -notmatch $EditorRx) { $skipped++; continue }

    $key = & $KeyOf $eid
    if (-not $Ratios.ContainsKey($key)) { throw "$eid : no ratio for tier '$key'" }

    $origPath = Join-Path (Join-Path $orig $Folder) $f.Name
    if (-not (Test-Path $origPath)) { throw "$($f.Name) : not present in Enai's tree - cannot reprice idempotently" }
    $om = [regex]::Match([IO.File]::ReadAllText($origPath), $valueRx)
    if (-not $om.Success) { throw "$($f.Name) : no Value: in Enai's copy" }

    $old = [int]$om.Groups[1].Value
    $new = [int][math]::Round(($old * $Ratios[$key]) / 5) * 5
    if ($new -lt 5) { $new = 5 }

    $cur = [regex]::Matches($ours, $valueRx)
    if ($cur.Count -ne 1) { throw "$($f.Name) : expected exactly 1 top-level Value:, found $($cur.Count)" }

    $upd = [regex]::Replace($ours, $valueRx, "Value: $new")
    if ($upd -ne $ours) { [IO.File]::WriteAllText($f.FullName, $upd, $enc) }
    $changed++
    $rows += [pscustomobject]@{ Tier = $key; Old = $old; New = $new }
  }

  "  repriced $changed, skipped $skipped"
  foreach ($t in ($rows.Tier | Sort-Object -Unique)) {
    $g = @($rows | Where-Object { $_.Tier -eq $t })
    $o = @($g.Old | Sort-Object); $n = @($g.New | Sort-Object)
    "    {0,-5} n={1,-3} {2,5}-{3,-5} (med {4,5})  ->  {5,4}-{6,-4} (med {7,4})" -f `
      $t, $g.Count, $o[0], $o[-1], $o[[int]($o.Count/2)], $n[0], $n[-1], $n[[int]($n.Count/2)]
  }
}

'Books (spell tomes):'
Invoke-Reprice -Folder 'Books' -EditorRx '^WB_[ACDIR](000|025|050|075|100)_.+_Book$' `
  -Ratios $tomeRatio -KeyOf { param($e) $e -replace '^WB_[ACDIR](\d{3})_.*','$1' }

''
'Scrolls:'
Invoke-Reprice -Folder 'Scrolls' -EditorRx '^WB_[ACDIRX](000|025|050|075|100)_.+_Scroll$' `
  -Ratios $scrollRatio -KeyOf { param($e) $e -replace '^WB_([ACDIRX]\d{3})_.*','$1' }

''
'Done. Staves are not repriced - they have no recipes and no distribution, so nothing sells them.'
