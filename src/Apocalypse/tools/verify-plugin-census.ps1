#requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-Census($path) {
  $d=[IO.File]::ReadAllBytes($path)
  $ds=[BitConverter]::ToUInt32($d,4)
  $map=@{}
  $stack=New-Object System.Collections.Generic.Stack[object]
  $stack.Push(@((24+$ds),$d.Length))
  while($stack.Count -gt 0){
    $r=$stack.Pop(); $p=$r[0]; $stop=$r[1]
    while($p -lt $stop -and $p -lt $d.Length-24){
      $sig=[Text.Encoding]::ASCII.GetString($d,$p,4)
      if($sig -eq 'GRUP'){
        $g=[BitConverter]::ToUInt32($d,$p+4); if($g -lt 24){break}
        $stack.Push(@(($p+24),($p+$g))); $p+=$g
      } else {
        $rs=[BitConverter]::ToUInt32($d,$p+4); $fid=[BitConverter]::ToUInt32($d,$p+12)
        $map[('{0:X8}' -f $fid)] = $sig
        $p += 24+$rs
      }
    }
  }
  ,$map
}
function Get-Header($path){
  $fs=[IO.File]::OpenRead($path)
  try{
    $br=New-Object IO.BinaryReader($fs); $null=$br.ReadBytes(4)
    $ds=$br.ReadUInt32(); $fl=$br.ReadUInt32(); $null=$br.ReadBytes(12)
    $end=24+$ds; $m=@(); $ver=-1
    while($fs.Position -lt $end){
      $t=[Text.Encoding]::ASCII.GetString($br.ReadBytes(4)); $sz=$br.ReadUInt16(); $b=$br.ReadBytes($sz)
      if($t -eq 'MAST'){ $m+=[Text.Encoding]::GetEncoding(1252).GetString($b).TrimEnd([char]0) }
      if($t -eq 'HEDR'){ $ver=[BitConverter]::ToSingle($b,0) }
    }
    [pscustomobject]@{ Flags=$fl; Masters=$m; Hedr=$ver }
  } finally { $fs.Close() }
}

$a=$args[0]; $b=$args[1]
$ha=Get-Header $a; $hb=Get-Header $b
"{0,-12} {1,-10} {2,-6} {3}" -f 'FILE','FLAGS','HEDR','MASTERS'
"{0,-12} 0x{1:X4}     {2,-6} {3}" -f 'ORIGINAL', $ha.Flags, $ha.Hedr, ($ha.Masters -join ', ')
"{0,-12} 0x{1:X4}     {2,-6} {3}" -f 'REBUILT',  $hb.Flags, $hb.Hedr, ($hb.Masters -join ', ')
''
$ca=Get-Census $a; $cb=Get-Census $b
"records: original=$($ca.Count)  rebuilt=$($cb.Count)"
''
$onlyA=@($ca.Keys | Where-Object { -not $cb.ContainsKey($_) })
$onlyB=@($cb.Keys | Where-Object { -not $ca.ContainsKey($_) })
$typeDiff=@($ca.Keys | Where-Object { $cb.ContainsKey($_) -and $cb[$_] -ne $ca[$_] })
"only in ORIGINAL : $($onlyA.Count)"
$onlyA | Select-Object -First 10 | ForEach-Object { "   $_ ($($ca[$_]))" }
"only in REBUILT  : $($onlyB.Count)"
$onlyB | Select-Object -First 10 | ForEach-Object { "   $_ ($($cb[$_]))" }
"type mismatches  : $($typeDiff.Count)"
$typeDiff | Select-Object -First 10 | ForEach-Object { "   $_ : $($ca[$_]) -> $($cb[$_])" }
''
'-- record counts by signature --'
$ga=$ca.Values | Group-Object | ForEach-Object { @{$_.Name=$_.Count} }
$sa=@{}; $ca.Values | Group-Object | ForEach-Object { $sa[$_.Name]=$_.Count }
$sb=@{}; $cb.Values | Group-Object | ForEach-Object { $sb[$_.Name]=$_.Count }
$all=@($sa.Keys + $sb.Keys | Sort-Object -Unique)
$diffs=0
foreach($k in $all){
  $x=if($sa.ContainsKey($k)){$sa[$k]}else{0}
  $y=if($sb.ContainsKey($k)){$sb[$k]}else{0}
  if($x -ne $y){ "   {0}  original={1}  rebuilt={2}" -f $k,$x,$y; $diffs++ }
}
if($diffs -eq 0){ '   identical across every record type' }
