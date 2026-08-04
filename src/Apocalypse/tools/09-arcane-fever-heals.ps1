#requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Make Apocalypse's self-heals pay Enderal's Arcane Fever tax.
#
# WHY. Enderal taxes healing MAGIC. Every one of its own healing spells pays Arcane Fever - the
# negated LastFlattered ActorValue, where 100 = death - and only 11 of its 837 spells raise Fever at
# all, every one of them a self-heal. Apocalypse adds 19 self-heals that pay nothing, which makes
# them inconsistent with every Enderal spell in their class.
#
# NOTE Enderal DOES have healing potions - five tiers of _NNE_Genesungstrank (36-160 HP over 4s,
# 25-190 gold) plus _00E_Medicine - and none of them costs Fever. So the design is a trade, not a
# prohibition: potions are the finite gold-priced heal, magic is the renewable one and Fever is its
# price. An untaxed Apocalypse heal beats both. (This script's header used to claim Enderal had no
# healing potions; that was wrong, from an English-only name search - the EditorIDs are German.)
#
# HOW ENDERAL DOES IT. _00E_IncreaseArcaneFeverFFSelf (11A4B6:Skyrim.esm) - FireAndForget, Self (no
# TargetType line), Archetype Type: Script -> _00E_ArkanistenfieberBlitzheilungSCN. That script reads
# Self.GetMagnitude() (the EFFECT ITEM's Magnitude, not Area - the potion path 11A4B6's sibling uses
# is the one that reads Area), applies the Mental Expert reduction itself (x0.67 with perk 069D07),
# and fires on akCaster == PlayerREF || akTarget == PlayerREF. So records using it need no perk
# condition of their own.
#
# There is a second effect, _00E_IncreaseArcaneFeverConcSelf (106EA4) for Concentration casts, which
# needs a two-effect perk-gated pair with FS's 02F42E. It is NOT used here: the only Apocalypse
# Concentration/Self record with a Health archetype is Breath of Tyr's parent 12B063, whose sole
# effect is Type: Script and heals nothing.
#
# THE RATES ARE ENDERAL'S OWN. Enderal charges a FLAT fever cost per line - every FlashHeal is 5,
# every Boon 0.5/s - so HP-per-fever-point IMPROVES as spells get stronger. Its best rates are the
# ceilings we price against, and we never beat them:
#
#   burst     26 HP/point   _55E_SpellFlashHeal 12E168, 130 HP / 5 AF
#   overtime  78 HP/point   _40E_SpellBoon      12E165, 39 HP/s / 0.5 AF/s
#   floors    5 (spells, Enderal's basic FlashHeal)   2.5 (scrolls, 01E_ScrollBoon)
#
# Both ceilings are the UN-perked figures; with Ambrosia (069D05) Enderal's rise to 30 and 92, so
# pricing at 26/78 keeps Apocalypse strictly below Enderal either way.
#
# Idempotent: strips any block we previously appended, then re-appends. It deliberately does NOT use
# 08-reprice's "recompute from Enai's untouched tree" trick, because 01-gen-renames has already
# rewritten Name: on these very files (Breath of Arkay -> Breath of Tyr, Lamb of Mara -> Lamb of
# Irlanda) and rebuilding from the reference tree would silently revert step 1.
#
# Run after 05-merge-tree.ps1. Disjoint from 06/07/08 (they touch LeveledItems / Containers / Value:,
# this touches Effects:).

$repo = 'C:\modding\mod-projects\zenderal-patches'
$mine = Join-Path $repo 'src\Apocalypse\ApocalypseESP'
$enc  = New-Object System.Text.UTF8Encoding($false)

$FeverKey                 = '11A4B6:Skyrim.esm'
$BurstHpPerPoint    = 26
$OverTimeHpPerPoint = 78

# Kind: Burst = Magnitude is the heal. OverTime = Magnitude x Duration. Fixed = script-driven, no
# magnitude in the record, so FixedAf is a judgement call (see the Stendarr note below).
# CondFrom: copy the Conditions block verbatim off that effect (guardrail 4 - never retype one).
$plan = @(
  [pscustomobject]@{ Folder='Spells'; Id='082483'; EditorId='WB_Res_Heal1_Spell_WildHealing';          Kind='Burst';    HealEffect='086054'; ExpectedHp=40;  Floor=5;   CondFrom=$null;     FixedAf=$null }
  [pscustomobject]@{ Folder='Spells'; Id='083A47'; EditorId='WB_Res_Heal5_Spell_BreathOfArkay_Level0'; Kind='Burst';    HealEffect='082460'; ExpectedHp=50;  Floor=5;   CondFrom=$null;     FixedAf=$null }
  [pscustomobject]@{ Folder='Spells'; Id='083A4A'; EditorId='WB_Res_Heal5_Spell_BreathOfArkay_Level1'; Kind='Burst';    HealEffect='082460'; ExpectedHp=100; Floor=5;   CondFrom=$null;     FixedAf=$null }
  [pscustomobject]@{ Folder='Spells'; Id='083A4C'; EditorId='WB_Res_Heal5_Spell_BreathOfArkay_Level2'; Kind='Burst';    HealEffect='082460'; ExpectedHp=150; Floor=5;   CondFrom=$null;     FixedAf=$null }
  [pscustomobject]@{ Folder='Spells'; Id='083A4E'; EditorId='WB_Res_Heal5_Spell_BreathOfArkay_Level3'; Kind='Burst';    HealEffect='082460'; ExpectedHp=200; Floor=5;   CondFrom=$null;     FixedAf=$null }
  [pscustomobject]@{ Folder='Spells'; Id='083A50'; EditorId='WB_Res_Heal5_Spell_BreathOfArkay_Level4'; Kind='Burst';    HealEffect='082460'; ExpectedHp=250; Floor=5;   CondFrom=$null;     FixedAf=$null }
  [pscustomobject]@{ Folder='Spells'; Id='083A52'; EditorId='WB_Res_Heal5_Spell_BreathOfArkay_Level5'; Kind='Burst';    HealEffect='082460'; ExpectedHp=300; Floor=5;   CondFrom=$null;     FixedAf=$null }
  [pscustomobject]@{ Folder='Spells'; Id='083A54'; EditorId='WB_Res_Heal5_Spell_BreathOfArkay_Level6'; Kind='Burst';    HealEffect='082460'; ExpectedHp=350; Floor=5;   CondFrom=$null;     FixedAf=$null }
  [pscustomobject]@{ Folder='Spells'; Id='083A56'; EditorId='WB_Res_Heal5_Spell_BreathOfArkay_Level7'; Kind='Burst';    HealEffect='082460'; ExpectedHp=400; Floor=5;   CondFrom=$null;     FixedAf=$null }
  [pscustomobject]@{ Folder='Spells'; Id='083A58'; EditorId='WB_Res_Heal5_Spell_BreathOfArkay_Level8'; Kind='Burst';    HealEffect='082460'; ExpectedHp=450; Floor=5;   CondFrom=$null;     FixedAf=$null }
  [pscustomobject]@{ Folder='Spells'; Id='083A5A'; EditorId='WB_Res_Heal5_Spell_BreathOfArkay_Level9'; Kind='Burst';    HealEffect='082460'; ExpectedHp=500; Floor=5;   CondFrom=$null;     FixedAf=$null }
  [pscustomobject]@{ Folder='Spells'; Id='01E701'; EditorId='WB_Res_Heal4_Spell_Resurgence_NPC';       Kind='OverTime'; HealEffect='07BD56'; ExpectedHp=300; Floor=5;   CondFrom='07BD56'; FixedAf=$null }
  [pscustomobject]@{ Folder='Spells'; Id='05F74D'; EditorId='WB_Res_HealRegen4_Spell_HealingBlossom';  Kind='OverTime'; HealEffect='02023E'; ExpectedHp=600; Floor=5;   CondFrom=$null;     FixedAf=$null }
  [pscustomobject]@{ Folder='Spells'; Id='033CCA'; EditorId='WB_Res_Buff5_Spell_KingsHeart';           Kind='OverTime'; HealEffect='0B9E2B'; ExpectedHp=900; Floor=5;   CondFrom=$null;     FixedAf=$null }

  [pscustomobject]@{ Folder='Scrolls'; Id='0896E2'; EditorId='WB_R000_WildHealing_Scroll';       Kind='Burst';    HealEffect='086054'; ExpectedHp=40;  Floor=2.5; CondFrom=$null;     FixedAf=$null }
  [pscustomobject]@{ Folder='Scrolls'; Id='03AF4B'; EditorId='WB_R075_Resurgence_Scroll';        Kind='OverTime'; HealEffect='07BD56'; ExpectedHp=300; Floor=2.5; CondFrom='07BD56'; FixedAf=$null }
  [pscustomobject]@{ Folder='Scrolls'; Id='03B4B4'; EditorId='WB_R075_HealingBlossom_Scroll';    Kind='OverTime'; HealEffect='02023E'; ExpectedHp=600; Floor=2.5; CondFrom=$null;     FixedAf=$null }
  [pscustomobject]@{ Folder='Scrolls'; Id='03B4BE'; EditorId='WB_R100_KingsHeart_Scroll';        Kind='OverTime'; HealEffect='0B9E2B'; ExpectedHp=900; Floor=2.5; CondFrom=$null;     FixedAf=$null }
  # Stendarr's Embrace is wb_stendarr_script: RestoreActorValue to full + 25% max Health for 60s.
  # There is no magnitude in the record - the amount IS the player's max Health. 20 assumes ~450-550
  # endgame Enderal Health (HP/26 -> 17-21). Re-check `player.getav health` on a real endgame save.
  [pscustomobject]@{ Folder='Scrolls'; Id='09957C'; EditorId='WB_X100_StendarrsEmbrace_Scroll';  Kind='Fixed';    HealEffect='09957A'; ExpectedHp=$null; Floor=2.5; CondFrom=$null;   FixedAf=20 }
)

# CRLF everywhere: no '$' anchors (CLAUDE.md guardrail 10). Every line break is written \r?\n.
$afStripRx = '(?m)^- BaseEffect: 11A4B6:Skyrim\.esm\r?\n[\s\S]*\z'

function Get-EffectBlocks {
  param([string]$Text)
  $m = [regex]::Match($Text, '(?m)^Effects:\r?\n')
  if (-not $m.Success) { throw 'no Effects: block' }
  $body = $Text.Substring($m.Index + $m.Length)
  $parts = [regex]::Split($body, '(?m)^(?=- BaseEffect: )') | Where-Object { $_ -match '^- BaseEffect: ' }
  return $parts
}

$rows = @()
foreach ($r in $plan) {
  $dir = Join-Path $mine $r.Folder
  $hits = @(Get-ChildItem $dir -Filter "* - $($r.Id)_Apocalypse - Magic of Skyrim.esp.yaml")
  if ($hits.Count -ne 1) { throw "$($r.EditorId) ($($r.Id)): expected exactly 1 file, found $($hits.Count)" }
  $path = $hits[0].FullName
  $t = [IO.File]::ReadAllText($path)

  # --- identity
  if ($t -notmatch [regex]::Escape("FormKey: $($r.Id):Apocalypse - Magic of Skyrim.esp")) {
    throw "$($r.EditorId): FormKey $($r.Id) not found in $($hits[0].Name)"
  }
  $eid = [regex]::Match($t, '(?m)^EditorID: (.+?)\s*\r?\n').Groups[1].Value
  if ($eid -ne $r.EditorId) { throw "$($r.Id): EditorID is '$eid', expected '$($r.EditorId)' - upstream rename?" }

  # --- delivery. 11A4B6 is Self/FireAndForget. A Self MGEF on an Aimed spell has ZERO precedent in
  #     370 non-Self spells across Enderal, Forgotten Stories and Apocalypse - it builds clean and
  #     does nothing in game. This is the check that stops that ever shipping.
  if ([regex]::IsMatch($t, '(?m)^TargetType:')) {
    throw "$($r.EditorId): has a top-level TargetType (not Self). 11A4B6 is Self-delivery - do not tax this record."
  }
  $wantCast = if ($r.Folder -eq 'Scrolls') { '3' } else { 'FireAndForget' }
  $cast = [regex]::Match($t, '(?m)^CastType: (.+?)\s*\r?\n').Groups[1].Value
  if ($cast -ne $wantCast) { throw "$($r.EditorId): CastType is '$cast', expected '$wantCast'" }

  # --- idempotency: strip any block we appended before (we always append last)
  $existing = [regex]::Matches($t, [regex]::Escape($FeverKey)).Count
  if ($existing -gt 1) { throw "$($r.EditorId): found $existing references to $FeverKey - hand-edited? refusing to guess" }
  if ($existing -eq 1) {
    $t = [regex]::Replace($t, $afStripRx, '')
    if ([regex]::IsMatch($t, [regex]::Escape($FeverKey))) { throw "$($r.EditorId): strip failed" }
  }

  # @() matters: several of these records have exactly one effect, and PowerShell would hand back a
  # bare string whose [-1] is its last CHARACTER.
  $blocks = @(Get-EffectBlocks -Text $t)
  $heal = @($blocks | Where-Object { $_ -match "^- BaseEffect: $($r.HealEffect):" })
  if ($heal.Count -ne 1) { throw "$($r.EditorId): expected 1 effect $($r.HealEffect), found $($heal.Count)" }

  # --- measure, and assert the number has not moved upstream
  if ($r.Kind -eq 'Fixed') {
    $hp = $null
    $af = [double]$r.FixedAf
    $rate = $null
  } else {
    $mm = [regex]::Match($heal[0], '(?m)^    Magnitude: ([\d.]+)(?=\r?\n)')
    if (-not $mm.Success) { throw "$($r.EditorId): no Magnitude on effect $($r.HealEffect)" }
    $mag = [double]::Parse($mm.Groups[1].Value, [Globalization.CultureInfo]::InvariantCulture)
    if ($r.Kind -eq 'OverTime') {
      $dm = [regex]::Match($heal[0], '(?m)^    Duration: ([\d.]+)(?=\r?\n)')
      if (-not $dm.Success) { throw "$($r.EditorId): OverTime but no Duration on $($r.HealEffect)" }
      $hp = $mag * [double]::Parse($dm.Groups[1].Value, [Globalization.CultureInfo]::InvariantCulture)
      $rate = $OverTimeHpPerPoint
    } else {
      $hp = $mag
      $rate = $BurstHpPerPoint
    }
    if ($hp -ne $r.ExpectedHp) {
      throw "$($r.EditorId): heal changed upstream, expected $($r.ExpectedHp) HP but read $hp - re-derive the fever value before shipping"
    }
    # AwayFromZero explicitly: PowerShell's [math]::Round is banker's rounding by default.
    $af = [math]::Round($hp / $rate, 0, [MidpointRounding]::AwayFromZero)
    if ($af -lt $r.Floor) { $af = [double]$r.Floor }
  }

  # --- conditions, copied verbatim off the heal effect (guardrail 4)
  $cond = ''
  if ($null -ne $r.CondFrom) {
    $src = @($blocks | Where-Object { $_ -match "^- BaseEffect: $($r.CondFrom):" })
    if ($src.Count -ne 1) { throw "$($r.EditorId): no effect $($r.CondFrom) to copy conditions from" }
    $cm = [regex]::Match($src[0], '(?ms)^  Conditions:\r?\n.*')
    if (-not $cm.Success) { throw "$($r.EditorId): effect $($r.CondFrom) has no Conditions to copy" }
    $cond = $cm.Value.TrimEnd("`r", "`n")
  }

  # --- append. InvariantCulture so 2.5 never writes as 2,5 on a comma-decimal machine.
  $nl = if ($t -match "`r`n") { "`r`n" } else { "`n" }
  $mags = ([double]$af).ToString([Globalization.CultureInfo]::InvariantCulture)
  if (-not $t.EndsWith($nl)) { $t += $nl }
  $t += "- BaseEffect: $FeverKey$nl  Data:$nl    Magnitude: $mags$nl    Duration: 1$nl"
  if ($cond -ne '') { $t += ($cond -replace "`r?`n", $nl) + $nl }

  [IO.File]::WriteAllText($path, $t, $enc)

  # --- read back and verify what actually landed
  $v = [IO.File]::ReadAllText($path)
  if ([regex]::Matches($v, [regex]::Escape($FeverKey)).Count -ne 1) { throw "$($r.EditorId): post-write $FeverKey count wrong" }
  $vb = @(Get-EffectBlocks -Text $v)
  if ($vb[-1] -notmatch "^- BaseEffect: $([regex]::Escape($FeverKey))") {
    throw "$($r.EditorId): fever effect is not last - existing effect indices would shift"
  }
  $vm = [regex]::Match($vb[-1], '(?m)^    Magnitude: ([\d.]+)(?=\r?\n)')
  if (-not $vm.Success -or [double]::Parse($vm.Groups[1].Value, [Globalization.CultureInfo]::InvariantCulture) -ne $af) {
    throw "$($r.EditorId): post-write magnitude mismatch"
  }
  if ($null -ne $r.CondFrom -and $vb[-1] -notmatch '(?m)^  Conditions:') {
    throw "$($r.EditorId): conditions did not land"
  }

  $rows += [pscustomobject]@{
    Folder = $r.Folder; EditorId = $r.EditorId; Kind = $r.Kind
    Hp = $hp; Af = $af; Rate = $rate
    HpPerPt = if ($null -eq $hp) { $null } else { [math]::Round($hp / $af, 1) }
  }
}

# --- global assertions -------------------------------------------------------------------------

if ($rows.Count -ne 19) { throw "expected 19 records, touched $($rows.Count)" }
$nSpell  = @($rows | Where-Object { $_.Folder -eq 'Spells' }).Count
$nScroll = @($rows | Where-Object { $_.Folder -eq 'Scrolls' }).Count
if ($nSpell -ne 14 -or $nScroll -ne 5) { throw "expected 14 spells / 5 scrolls, got $nSpell / $nScroll" }

# nothing anywhere else in the tree may carry the fever effect
$sweep = @(Get-ChildItem $mine -Recurse -Filter *.yaml |
           Where-Object { [IO.File]::ReadAllText($_.FullName) -match [regex]::Escape($FeverKey) })
if ($sweep.Count -ne 19) { throw "tree sweep: $FeverKey appears in $($sweep.Count) files, expected 19" }

# the design principle, enforced in code: never more fever-efficient than Enderal's best heal.
# 1.05 slack absorbs integer rounding on Breath of Tyr Level6-9 (26.3-26.9); all four remain below
# the perked ceiling of 30.
foreach ($x in $rows) {
  if ($null -eq $x.HpPerPt) { continue }
  $ceil = if ($x.Kind -eq 'OverTime') { $OverTimeHpPerPoint } else { $BurstHpPerPoint * 1.05 }
  if ($x.HpPerPt -gt $ceil) { throw "$($x.EditorId): $($x.HpPerPt) HP/point exceeds the $($x.Kind) ceiling $ceil" }
}

# guardrail 11: re-resolve the one master FormKey we emit
$afFile = @(Get-ChildItem (Join-Path $repo 'reference\base') -Recurse -Filter '*11A4B6_Skyrim.esm.yaml')
if ($afFile.Count -lt 1) { throw "$FeverKey does not resolve in reference/base - is the reference tree built?" }
$hdr = [IO.File]::ReadAllText((Join-Path $mine 'RecordData.yaml'))
if ($hdr -notmatch 'Master: Skyrim\.esm') { throw 'Skyrim.esm is not a declared master' }

# --- report ------------------------------------------------------------------------------------

foreach ($grp in @('Spells', 'Scrolls')) {
  "$($grp):"
  foreach ($x in @($rows | Where-Object { $_.Folder -eq $grp })) {
    $hpTxt = if ($null -eq $x.Hp) { '   full' } else { '{0,7:0.#}' -f $x.Hp }
    $ppTxt = if ($null -eq $x.HpPerPt) { '     -' } else { '{0,6:0.0}' -f $x.HpPerPt }
    "  {0,-44} {1,-8} {2} HP  ->  AF {3,-5} ({4} HP/pt)" -f $x.EditorId, $x.Kind, $hpTxt, $x.Af, $ppTxt
  }
  ''
}
"$($rows.Count) records taxed, 0 above ceiling."
'Leech/absorb spells (Decompose, Leech Seed, Lamb of Irlanda, Poisoned Chalice, Natures Balance) are'
'Aimed and deliberately untaxed - 11A4B6 is Self and has no precedent on an Aimed record.'
