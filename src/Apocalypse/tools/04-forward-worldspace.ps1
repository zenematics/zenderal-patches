#requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Forward Enderal's MQP01Home worldspace (Forgotten Stories' winning version) while KEEPING
# Apocalypse's three persistent refs, which other Apocalypse records still point at.
$repo = 'C:\modding\mod-projects\zenderal-patches'
$fsFile   = Join-Path $repo 'reference\base\EnderalFS\Worldspaces\MQP01Home - 00003C_Skyrim.esm\RecordData.yaml'
$apocFile = Join-Path $repo 'reference\mods\Apocalypse\esp\Worldspaces\Tamriel - 00003C_Skyrim.esm\RecordData.yaml'
$dstDir   = Join-Path (Join-Path $repo 'src\Apocalypse\ApocalypseESP\Worldspaces') 'MQP01Home - 00003C_Skyrim.esm'
$enc      = New-Object System.Text.UTF8Encoding($false)

$fs   = [IO.File]::ReadAllLines($fsFile)
$apoc = [IO.File]::ReadAllLines($apocFile)

# --- Enderal's worldspace + cell fields, up to (not including) its Persistent list ---
$pStart = [array]::IndexOf($fs, '  Persistent:')
if ($pStart -lt 0) { throw "no '  Persistent:' in the FS record" }
$pEnd = -1
for ($i = $pStart + 1; $i -lt $fs.Count; $i++) { if ($fs[$i] -eq '  MajorFlags:') { $pEnd = $i; break } }
if ($pEnd -lt 0) { throw "no closing '  MajorFlags:' in the FS record" }

# --- Apocalypse's persistent refs ---
$aStart = [array]::IndexOf($apoc, '  Persistent:')
if ($aStart -lt 0) { throw "no '  Persistent:' in the Apocalypse record" }
$aEnd = -1
for ($i = $aStart + 1; $i -lt $apoc.Count; $i++) { if ($apoc[$i] -eq '  MajorFlags:') { $aEnd = $i; break } }
if ($aEnd -lt 0) { throw "no closing '  MajorFlags:' in the Apocalypse record" }

$apocRefs = $apoc[$aStart..($aEnd - 1)]
$kept = @($apocRefs | Where-Object { $_ -like '  - MutagenObjectType:*' }).Count
"Apocalypse persistent refs carried over : $kept"
if ($kept -ne 3) { throw "expected 3 Apocalypse persistent refs, found $kept" }
foreach ($need in @('041153','08500A','08A1DB')) {
  if (-not (($apocRefs -join "`n") -match $need)) { throw "ref $need missing from the carried block" }
}

$out = @()
$out += $fs[0..($pStart - 1)]     # worldspace + cell fields, FS's version
$out += $apocRefs                 # Persistent: + Apocalypse's three refs only
$out += $fs[$pEnd..($fs.Count - 1)]

$text = ($out -join "`r`n")
foreach ($must in @('FormKey: 00003C:Skyrim.esm','EditorID: MQP01Home','Worldspace: 001D3C:Skyrim.esm',
                    'Location: 04BBEE:Skyrim.esm','- SmallWorld','- CannotFastTravel',
                    'FormKey: 000D74:Skyrim.esm','041153:Apocalypse','08500A:Apocalypse','08A1DB:Apocalypse')) {
  if (-not $text.Contains($must)) { throw "result is missing: $must" }
}
if ($text -match '(?m)^\s*Regions:') { throw "result still carries a Regions list" }
if ($text -match 'MaxHeight') { throw "result still carries Tamriel's MaxHeight grid" }

New-Item -ItemType Directory -Force $dstDir | Out-Null
[IO.File]::WriteAllText((Join-Path $dstDir 'RecordData.yaml'), $text + "`r`n", $enc)
"wrote $((Get-Item (Join-Path $dstDir 'RecordData.yaml')).Length) bytes"
"  Enderal's worldspace data + Apocalypse's 3 persistent refs, no Regions, no Tamriel grid"
