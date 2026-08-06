# Regenerates src/RelentlessSwordZen/RelentlessSwordZenESP/ from the base patch.
#
# The Zen release is a SUPERSET of the Relentless Sword patch, shipped under the SAME
# plugin filename so the two archives are mutually exclusive: you install one or the
# other depending on which build of johnskyrim's mod you own (Nexus = 6 swords,
# Patreon "ZEN" = 8). Same filename means they cannot both be enabled, and the six
# original swords keep their FormIDs, so swapping builds later leaves blades already
# in a save intact.
#
# Because the build deserializes a YAML folder, the 33 base records have to physically
# exist in both trees. This script is what keeps them from drifting: edit
# src/RelentlessSword/, then re-run this. Do not hand-edit the generated tree.
#
#   pwsh src/RelentlessSwordZen/tools/build-zen-tree.ps1
#
# Requires the ZEN plugin serialized to reference/mods/relentlessSword/esps/ZEN
# (gitignored - johnskyrim's Patreon records are not redistributed here). Recreate with:
#   Spriggit.CLI.exe serialize --InputPath "<ZEN>/CORE/Relentless Sword SE - Johnskyrim.esp" `
#     --OutputPath reference/mods/relentlessSword/esps/ZEN --GameRelease EnderalSE `
#     --PackageName Spriggit.Yaml.Skyrim --PackageVersion 0.40.0

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repo    = Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
$baseSrc = Join-Path $repo 'src\RelentlessSword\RelentlessSwordESP'
$zenRef  = Join-Path $repo 'reference\mods\relentlessSword\esps\ZEN'
$out     = Join-Path $repo 'src\RelentlessSwordZen\RelentlessSwordZenESP'

# Both plugins carry the same ModKey on purpose - see header comment.
$MK = 'Zenderal - Relentless Sword.esp'
$JS = 'Relentless Sword SE - Johnskyrim.esp'

foreach ($p in @($baseSrc, $zenRef)) {
    if (-not (Test-Path $p)) { throw "missing required input tree: $p" }
}

if (Test-Path $out) { Remove-Item $out -Recurse -Force }
New-Item -ItemType Directory -Path $out | Out-Null

$CR = [string][char]13
function Sub([string]$text, [string]$from, [string]$to, [string]$label) {
    $n = ([regex]::Matches($text, [regex]::Escape($from))).Count
    if ($n -ne 1) { throw "[$label] expected 1 match for '$from', found $n" }
    return $text.Replace($from, $to)
}
function Emit([string]$dir, [string]$editorId, [string]$hex, [string]$text) {
    $d = Join-Path $out $dir
    if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d | Out-Null }
    [System.IO.File]::WriteAllText((Join-Path $d "$editorId - ${hex}_$MK.yaml"),
        $text, (New-Object System.Text.UTF8Encoding($false)))
}
# .gitattributes forces LF on *.yaml; the reference tree is CRLF. Normalise on read.
function ReadRef([string]$dir, [string]$file) {
    return ([System.IO.File]::ReadAllText((Join-Path (Join-Path $zenRef $dir) $file))).Replace($CR, "")
}
function ReadBase([string]$dir, [string]$file) {
    return ([System.IO.File]::ReadAllText((Join-Path (Join-Path $baseSrc $dir) $file))).Replace($CR, "")
}

# ---------------------------------------------------------------- 1. base records
# Copied verbatim: same ModKey, so FormKeys and filenames need no rewriting at all.
# RecordData.yaml is replaced below; spriggit-meta.json is identical either way.
Copy-Item (Join-Path $baseSrc '*') -Destination $out -Recurse -Force
$copied = @(Get-ChildItem $out -Recurse -Filter '*.yaml' |
            Where-Object { $_.Name -ne 'RecordData.yaml' }).Count
if ($copied -ne 32) { throw "expected 32 base record files (33 records incl. the cell), found $copied" }
Write-Host "copied $copied base record files"

# ------------------------------------------------------------------- 2. the header
# Same ModKey and master list as the base patch; only the description differs.
$header = @'
SpriggitSource:
  PackageName: Spriggit.Yaml.Skyrim
  Version: 0.40
ModKey: Zenderal - Relentless Sword.esp
GameRelease: EnderalSE
ModHeader:
  Flags:
  - Small
  Stats:
    Version: 1.7
  Author: johnskyrim
  Description: >-
    Relentless Sword SE by johnskyrim, converted for Enderal: Forgotten Stories SE by Zenderal.
    ZEN edition - eight blades, including the Patreon-only Zen design. Requires johnskyrim's
    ZEN build installed for its meshes and textures; disable its own .esp. Do not install
    alongside the six-blade version of this patch; they are the same plugin.
  MasterReferences:
  - Master: Skyrim.esm
    FileSize: 0
  - Master: Enderal - Forgotten Stories.esm
    FileSize: 0
  INTV: 1
'@
[System.IO.File]::WriteAllText((Join-Path $out 'RecordData.yaml'),
    ($header.Replace($CR, "") + "`n"), (New-Object System.Text.UTF8Encoding($false)))

# -------------------------------------------------------------- 3. the Zen records
# Allocated ABOVE the base patch's 0x800-0x827 so every existing FormID is untouched.
Write-Host "generating Zen records at 0x828-0x831"

$t = ReadRef 'Statics' "JS_1stPersonRelentlessSwordZen - 000803_$JS.yaml"
$t = Sub $t "FormKey: 000803:$JS" "FormKey: 000828:$MK" 'static1H'
Emit 'Statics' 'JS_1stPersonRelentlessSwordZen' '000828' $t

$t = ReadRef 'Statics' "JS_1stPersonRelentlessSwordZen2H - 000807_$JS.yaml"
$t = Sub $t "FormKey: 000807:$JS" "FormKey: 000829:$MK" 'static2H'
Emit 'Statics' 'JS_1stPersonRelentlessSwordZen2H' '000829' $t

# Retuned to Enderal's shadowsteel tier (11/5 -> 23/6, 20/9 -> 37/11) and given the
# WeapTypeMelee keyword, exactly as the base patch does to its six.
$t = ReadRef 'Weapons' "JS_RelentlessSwordZen - 00080C_$JS.yaml"
$t = Sub $t "FormKey: 00080C:$JS" "FormKey: 00082A:$MK" 'weap1H.formkey'
$t = Sub $t "  Value: Zen" "  Value: Relentless Zen" 'weap1H.name'
$t = Sub $t "- 01E71E:Skyrim.esm" "- 01E71E:Skyrim.esm`n- 06727B:Skyrim.esm" 'weap1H.keyword'
$t = Sub $t "FirstPersonModel: 000803:$JS" "FirstPersonModel: 000828:$MK" 'weap1H.1stperson'
$t = Sub $t "  Damage: 11" "  Damage: 23" 'weap1H.damage'
$t = Sub $t "  Damage: 5"  "  Damage: 6"  'weap1H.crit'
Emit 'Weapons' 'JS_RelentlessSwordZen' '00082A' $t

$t = ReadRef 'Weapons' "JS_RelentlessSwordZen2H - 000808_$JS.yaml"
$t = Sub $t "FormKey: 000808:$JS" "FormKey: 00082B:$MK" 'weap2H.formkey'
$t = Sub $t "  Value: Zen" "  Value: Relentless Zen" 'weap2H.name'
$t = Sub $t "- 01E71E:Skyrim.esm" "- 01E71E:Skyrim.esm`n- 06727B:Skyrim.esm" 'weap2H.keyword'
$t = Sub $t "FirstPersonModel: 000807:$JS" "FirstPersonModel: 000829:$MK" 'weap2H.1stperson'
$t = Sub $t "  Damage: 20" "  Damage: 37" 'weap2H.damage'
$t = Sub $t "  Damage: 9"  "  Damage: 11" 'weap2H.crit'
Emit 'Weapons' 'JS_RelentlessSwordZen2H' '00082B' $t

# johnskyrim's Zen recipes gate on the Skyforge (0F46CE) and the Companions global
# (0F46D1); neither exists in Enderal, so they could never fire. Build from OUR
# recipes, which already gate the Enderal way (Handicraft 50 + the blueprint), and
# keep his extra ingredient - 063B47 IS present in Enderal, as GemDiamond.
$leather = "- Item:`n    Item: 0DB5D2:Skyrim.esm`n    Count: 1"
$diamond = $leather + "`n- Item:`n    Item: 063B47:Skyrim.esm`n    Count: 1"

$t = ReadBase 'ConstructibleObjects' "JS_RelentlessSword_Recipe - 000812_$MK.yaml"
$t = Sub $t "FormKey: 000812:$MK" "FormKey: 00082C:$MK" 'recipe1H.formkey'
$t = Sub $t "EditorID: JS_RelentlessSword_Recipe" "EditorID: JS_RelentlessSwordZen_Recipe" 'recipe1H.edid'
$t = Sub $t $leather $diamond 'recipe1H.diamond'
$t = Sub $t "CreatedObject: 000809:$MK" "CreatedObject: 00082A:$MK" 'recipe1H.created'
Emit 'ConstructibleObjects' 'JS_RelentlessSwordZen_Recipe' '00082C' $t

$t = ReadBase 'ConstructibleObjects' "JS_RelentlessSword2H_Recipe - 000819_$MK.yaml"
$t = Sub $t "FormKey: 000819:$MK" "FormKey: 00082D:$MK" 'recipe2H.formkey'
$t = Sub $t "EditorID: JS_RelentlessSword2H_Recipe" "EditorID: JS_RelentlessSwordZen2H_Recipe" 'recipe2H.edid'
$t = Sub $t $leather $diamond 'recipe2H.diamond'
$t = Sub $t "CreatedObject: 00080D:$MK" "CreatedObject: 00082B:$MK" 'recipe2H.created'
Emit 'ConstructibleObjects' 'JS_RelentlessSwordZen2H_Recipe' '00082D' $t

$t = ReadBase 'ConstructibleObjects' "JS_RelentlessSword_Temper - 000811_$MK.yaml"
$t = Sub $t "FormKey: 000811:$MK" "FormKey: 00082E:$MK" 'temper1H.formkey'
$t = Sub $t "EditorID: JS_RelentlessSword_Temper" "EditorID: JS_RelentlessSwordZen_Temper" 'temper1H.edid'
$t = Sub $t "CreatedObject: 000809:$MK" "CreatedObject: 00082A:$MK" 'temper1H.created'
Emit 'ConstructibleObjects' 'JS_RelentlessSwordZen_Temper' '00082E' $t

$t = ReadBase 'ConstructibleObjects' "JS_RelentlessSword2H_Temper - 00081D_$MK.yaml"
$t = Sub $t "FormKey: 00081D:$MK" "FormKey: 00082F:$MK" 'temper2H.formkey'
$t = Sub $t "EditorID: JS_RelentlessSword2H_Temper" "EditorID: JS_RelentlessSwordZen2H_Temper" 'temper2H.edid'
$t = Sub $t "CreatedObject: 00080D:$MK" "CreatedObject: 00082B:$MK" 'temper2H.created'
Emit 'ConstructibleObjects' 'JS_RelentlessSwordZen2H_Temper' '00082F' $t

$t = ReadBase 'ConstructibleObjects' "JS_DismantleRelentlessSwordToShadowSteelIngot - 000820_$MK.yaml"
$t = Sub $t "FormKey: 000820:$MK" "FormKey: 000830:$MK" 'dis1H.formkey'
$t = Sub $t "EditorID: JS_DismantleRelentlessSwordToShadowSteelIngot" "EditorID: JS_DismantleRelentlessSwordZenToShadowSteelIngot" 'dis1H.edid'
$t = Sub $t "    Item: 000809:$MK" "    Item: 00082A:$MK" 'dis1H.item'
$t = Sub $t "    ItemOrList: 000809:$MK" "    ItemOrList: 00082A:$MK" 'dis1H.cond'
Emit 'ConstructibleObjects' 'JS_DismantleRelentlessSwordZenToShadowSteelIngot' '000830' $t

$t = ReadBase 'ConstructibleObjects' "JS_DismantleRelentlessSword2HToShadowSteelIngot - 000823_$MK.yaml"
$t = Sub $t "FormKey: 000823:$MK" "FormKey: 000831:$MK" 'dis2H.formkey'
$t = Sub $t "EditorID: JS_DismantleRelentlessSword2HToShadowSteelIngot" "EditorID: JS_DismantleRelentlessSwordZen2HToShadowSteelIngot" 'dis2H.edid'
$t = Sub $t "    Item: 00080D:$MK" "    Item: 00082B:$MK" 'dis2H.item'
$t = Sub $t "    ItemOrList: 00080D:$MK" "    ItemOrList: 00082B:$MK" 'dis2H.cond'
Emit 'ConstructibleObjects' 'JS_DismantleRelentlessSwordZen2HToShadowSteelIngot' '000831' $t

# ------------------------------------------------------------------- 4. assertions
$total = @(Get-ChildItem $out -Recurse -Filter '*.yaml' |
           Where-Object { $_.Name -ne 'RecordData.yaml' }).Count
if ($total -ne 42) { throw "expected 42 record files (32 base + 10 Zen), found $total" }

# The Zen recipes must gate on the blueprint this same plugin defines at 0x826.
$blueprintRefs = @(Get-ChildItem (Join-Path $out 'ConstructibleObjects') -Filter '*.yaml' |
    Where-Object { (Get-Content $_.FullName -Raw) -match 'ItemOrList: 000826:' }).Count
if ($blueprintRefs -ne 8) { throw "expected 8 recipes gated on blueprint 000826, found $blueprintRefs" }

# Nothing may reference the Skyforge or the Companions global - they don't exist in Enderal.
$dead = @(Get-ChildItem $out -Recurse -Filter '*.yaml' |
    Where-Object { (Get-Content $_.FullName -Raw) -match '0F46CE:|0F46D1:' })
if ($dead.Count -ne 0) { throw "Skyforge/Companions reference survived in: $($dead.Name -join ', ')" }

Write-Host ""
Write-Host "OK - $total record files (32 base + 10 Zen), 8 blueprint-gated recipes, no dead Skyforge refs."
