#requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Hand-build a TES4 plugin with a chosen master list and NO records.
#   make-masters.ps1 "Skyrim.esm,Update.esm,Enderal - Forgotten Stories.esm,Apocalypse - Magic of Skyrim.esp"
$masters = @()
if ($args.Count -ge 1 -and $args[0]) { $masters = @($args[0] -split ',' | Where-Object { $_ -ne '' }) }

$sub = New-Object IO.MemoryStream
$sw  = New-Object IO.BinaryWriter($sub)
$enc = [Text.Encoding]::GetEncoding(1252)

$sw.Write([Text.Encoding]::ASCII.GetBytes('HEDR'))
$ver=1.7; if ($args.Count -ge 2 -and $args[1]) { $ver=[single]$args[1] }
$sw.Write([uint16]12); $sw.Write([single]$ver); $sw.Write([int32]0); $sw.Write([uint32]0x800)

$a = $enc.GetBytes("Zenderal`0")
$sw.Write([Text.Encoding]::ASCII.GetBytes('CNAM')); $sw.Write([uint16]$a.Length); $sw.Write($a)

foreach ($m in $masters) {
  $mb = $enc.GetBytes("$m`0")
  $sw.Write([Text.Encoding]::ASCII.GetBytes('MAST')); $sw.Write([uint16]$mb.Length); $sw.Write($mb)
  $sw.Write([Text.Encoding]::ASCII.GetBytes('DATA')); $sw.Write([uint16]8); $sw.Write([uint64]0)
}
$sw.Flush(); $subBytes = $sub.ToArray()

$ms = New-Object IO.MemoryStream
$bw = New-Object IO.BinaryWriter($ms)
$bw.Write([Text.Encoding]::ASCII.GetBytes('TES4'))
$bw.Write([uint32]$subBytes.Length); $bw.Write([uint32]0); $bw.Write([uint32]0)
$bw.Write([uint32]0); $bw.Write([uint16]0); $bw.Write([uint16]0)
$bw.Write($subBytes); $bw.Flush()

$out = 'C:\modding\modlists\thepath\mods\Zenderal - Apocalypse\Zenderal - Apocalypse.esp'
[IO.File]::WriteAllBytes($out, $ms.ToArray())
"masters written ($($masters.Count)):"
$masters | ForEach-Object { "   $_" }
powershell -NoProfile -File "C:\Users\stefa\AppData\Local\Temp\claude\C--modding-mod-projects-zenderal-patches\f260cc32-1cca-423a-9082-9d3a50aac01c\scratchpad\dump-plugin.ps1" $out
