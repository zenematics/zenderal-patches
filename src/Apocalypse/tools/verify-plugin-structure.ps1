#requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Dump($path) {
  "===== $(Split-Path $path -Leaf)  ($((Get-Item -LiteralPath $path).Length) bytes) ====="
  $d  = [IO.File]::ReadAllBytes($path)
  $enc = [Text.Encoding]::GetEncoding(1252)
  $pos = 0

  function Sig($d,$p) { [Text.Encoding]::ASCII.GetString($d, $p, 4) }
  function U32($d,$p) { [BitConverter]::ToUInt32($d, $p) }
  function U16($d,$p) { [BitConverter]::ToUInt16($d, $p) }

  # --- TES4 ---
  $sig = Sig $d 0
  $dataSize = U32 $d 4
  $flags = U32 $d 8
  $formId = U32 $d 12
  "TES4  dataSize=$dataSize flags=0x$('{0:X8}' -f $flags) formID=0x$('{0:X8}' -f $formId)"
  $p = 24
  $end = 24 + $dataSize
  while ($p -lt $end) {
    $s = Sig $d $p
    $sz = U16 $d ($p+4)
    $val = ''
    switch ($s) {
      'HEDR' { $val = "version={0} numRecords={1} nextObjectID=0x{2:X}" -f ([BitConverter]::ToSingle($d,$p+6)), (U32 $d ($p+10)), (U32 $d ($p+14)) }
      'CNAM' { $val = $enc.GetString($d,$p+6,$sz).TrimEnd([char]0) }
      'MAST' { $val = $enc.GetString($d,$p+6,$sz).TrimEnd([char]0) }
      'DATA' { $val = "0x{0:X16}" -f ([BitConverter]::ToUInt64($d,$p+6)) }
      'INTV' { $val = (U32 $d ($p+6)) }
      default { $val = "($sz bytes)" }
    }
    "  {0} size={1,-5} {2}" -f $s, $sz, $val
    $p += 6 + $sz
  }

  # --- top-level groups ---
  while ($p -lt $d.Length) {
    $s = Sig $d $p
    if ($s -ne 'GRUP') { "  !! expected GRUP at $p, got '$s'"; break }
    $gsize = U32 $d ($p+4)
    $label = $enc.GetString($d, $p+8, 4)
    $gtype = U32 $d ($p+12)
    "GRUP  size=$gsize label='$label' type=$gtype   (spans $p .. $($p+$gsize))"
    if ($p + $gsize -gt $d.Length) { "  !! GROUP OVERRUNS FILE by $(($p+$gsize)-$d.Length) bytes" }

    # records inside
    $q = $p + 24
    while ($q -lt $p + $gsize -and $q -lt $d.Length) {
      $rs = Sig $d $q
      $rsz = U32 $d ($q+4)
      $rfl = U32 $d ($q+8)
      $rid = U32 $d ($q+12)
      "    {0} size={1,-6} flags=0x{2:X8} formID=0x{3:X8}" -f $rs, $rsz, $rfl, $rid
      if ($q + 24 + $rsz -gt $d.Length) { "      !! RECORD OVERRUNS FILE" }
      $q += 24 + $rsz
    }
    if ($q -ne $p + $gsize) { "  !! group content ended at $q, group says $($p+$gsize)" }
    $p += $gsize
  }
  "trailing bytes after last group: $($d.Length - $p)"
  ''
}

foreach ($f in $args) { Dump $f }
