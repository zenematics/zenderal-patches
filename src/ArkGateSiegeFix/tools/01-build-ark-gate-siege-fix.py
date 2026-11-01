"""Generate the Ark Gate Siege Fix plugin YAML (Enderal 2.0 / old Zenderal release only).

During the Ark siege (MQ12b "Black Light" stages 5-125) Enderal 2.0's `_00E_ChestAndDoorLockScript`,
which Forgotten Stories puts on the door bases, shows "requires a key" on every scripted door outside
the Sun Temple. SureAI keeps the story path open by placing the Castle Quarters gate 09EECD with that
script flagged InheritedAndRemoved. Ark City Gate Consistency Patch (Enderal SE Nexus 839, f1.01)
rebuilds 09EECD on the 2.1 record, which has no scripts, and swaps its base to 11B116 (same script),
so on 2.0 the lock comes back and the quest path is shut.

This writes 09EECD as the gate patch has it, verbatim, plus 2.0's VirtualMachineAdapter. The
worldspace and persistent-cell headers are forwarded from the gate patch, which the plugin must load
directly after. The other side of the gate, 096F6A, is left alone: Perpetuum Theater - Neo Enderal
loads after the gate patch and already restores 2.0's record there, exemption included.

Enderal 2.1 needs none of this: it dropped the script and exempts 09EECD by reference ID in
`_00E_ArkSiegeLockedGatesPerk 0493DB`. Do not ship this plugin with the 2.1 list.

Reads reference/mods/ArkCityGateConsistencyPatch (gitignored; re-serialize it with
spriggit-decompile-reference) and reference/base/Skyrim (Enderal 2.0.12.4).
"""
import os
import re
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
WSNAME = "CapitalCityCastleWorld - 070729_Skyrim.esm"
GATE = os.path.join(ROOT, "reference", "mods", "ArkCityGateConsistencyPatch", "Worldspaces", WSNAME, "RecordData.yaml")
BASE20 = os.path.join(ROOT, "reference", "base", "Skyrim", "Worldspaces", WSNAME, "RecordData.yaml")
OUT = os.path.join(ROOT, "src", "ArkGateSiegeFix", "ArkGateSiegeFixESP")
OUTWS = os.path.join(OUT, "Worldspaces", WSNAME)
CRLF = "\r\n"
FK = "09EECD:Skyrim.esm"


def read(path):
    with open(path, "r", encoding="utf-8", newline="") as f:
        return f.read()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def persistent_items(lines, start):
    """(first, end) line ranges of each '  - MutagenObjectType:' item under 'TopCell: Persistent:'."""
    items, i = [], start + 1
    while i < len(lines) and (lines[i].startswith("  - ") or lines[i].startswith("    ")):
        j = i + 1
        while j < len(lines) and lines[j].startswith("    "):
            j += 1
        items.append((i, j))
        i = j
    return items, i


def ref_block(path, fk):
    lines = read(path).split(CRLF)
    start = lines.index("  Persistent:")
    items, _ = persistent_items(lines, start)
    hits = [lines[a:b] for a, b in items if lines[a + 1] == "    FormKey: " + fk]
    if len(hits) != 1:
        raise SystemExit(f"{fk}: found {len(hits)} times in {path}")
    return hits[0]


def vmad(block):
    """The VirtualMachineAdapter sub-block of a ref, verbatim."""
    i = block.index("    VirtualMachineAdapter:")
    j = i + 1
    while j < len(block) and block[j].startswith("      "):
        j += 1
    return block[i:j]


gate_lines = read(GATE).split(CRLF)
p_start = gate_lines.index("  Persistent:")
items, p_end = persistent_items(gate_lines, p_start)

ref = ref_block(GATE, FK)
if any(l.startswith("    VirtualMachineAdapter:") for l in ref):
    raise SystemExit(f"{FK}: the gate patch now carries scripts; re-check before building")
script = vmad(ref_block(BASE20, FK))
if script != ["    VirtualMachineAdapter:", "      Scripts:", "      - Name: _00E_ChestAndDoorLockScript",
              "        Flags: InheritedAndRemoved"]:
    raise SystemExit(f"{FK}: unexpected 2.0 VirtualMachineAdapter {script}")

# Spriggit's field order puts VirtualMachineAdapter right before Base.
at = [i for i, l in enumerate(ref) if l.startswith("    Base: ")]
if len(at) != 1:
    raise SystemExit(f"{FK}: expected one Base line, found {len(at)}")
ref = ref[:at[0]] + script + ref[at[0]:]

out = gate_lines[:p_start + 1] + ref + gate_lines[p_end:]

if os.path.isdir(os.path.join(OUT, "Worldspaces")):
    shutil.rmtree(os.path.join(OUT, "Worldspaces"))
write(os.path.join(OUTWS, "RecordData.yaml"), CRLF.join(out))

text = read(os.path.join(OUTWS, "RecordData.yaml"))
if text.count("    FormKey: ") != 1 or text.count("InheritedAndRemoved") != 1:
    raise SystemExit("expected exactly one ref with one InheritedAndRemoved script")
print(f"wrote {FK} with the 2.0 lock-script exemption to {OUTWS}")

# The record alone only helps a new game: a save keeps the lock script it already attached to 09EECD.
# So a hidden perk replaces the player's activation of 09EECD during the siege and opens it with default
# processing only, which skips that script's OnActivate and any BlockActivation it left. Shape copied
# from SureAI's own 2.1 siege perk _00E_ArkSiegeLockedGatesPerk 0493DB. A start-game-enabled quest
# gives the perk; such a quest also starts on the first load of an existing save.
MOD = "Zenderal - Ark Gate Siege Fix.esp"
PERK = "ZEN_ArkGateSiegeOpenPerk"
FRAG = "PRKF_ZEN_ArkGateSiegeOpenPerk_00000800"
QUEST = "ZEN_ArkGateSiegeQuest"
MQ12B = "02EBAD:Skyrim.esm"

perk = f"""FormKey: 000800:{MOD}
MajorRecordFlagsRaw: 4
EditorID: {PERK}
SkyrimMajorRecordFlags:
- NotPlayable
VirtualMachineAdapter:
  Scripts:
  - Name: {FRAG}
  ScriptFragments:
    FileName: {FRAG}
    Fragments:
    - FragmentIndex: 1
      Unknown2: 1
      ScriptName: {FRAG}
      FragmentName: Fragment_1
Description:
  TargetLanguage: English
  Value: ''
NumRanks: 1
Hidden: True
Effects:
- MutagenObjectType: PerkEntryPointAddActivateChoice
  Conditions:
  - Conditions:
    - MutagenObjectType: ConditionFloat
      Data:
        MutagenObjectType: GetIsIDConditionData
        Object: 000007:Skyrim.esm
      ComparisonValue: 1
  - RunOnTabIndex: 1
    Conditions:
    - MutagenObjectType: ConditionFloat
      Data:
        MutagenObjectType: GetIsReferenceConditionData
        Target: {FK}
      ComparisonValue: 1
    - MutagenObjectType: ConditionFloat
      CompareOperator: GreaterThanOrEqualTo
      Data:
        MutagenObjectType: GetStageConditionData
        Quest: {MQ12B}
      ComparisonValue: 5
    - MutagenObjectType: ConditionFloat
      CompareOperator: LessThanOrEqualTo
      Data:
        MutagenObjectType: GetStageConditionData
        Quest: {MQ12B}
      ComparisonValue: 125
  Flags:
    Flags:
    - RunImmediately
    - ReplaceDefault
    FragmentIndex: 1
  EntryPoint: Activate
  PerkConditionTabCount: 2
MajorFlags:
- NonPlayable
"""

quest = f"""FormKey: 000801:{MOD}
EditorID: {QUEST}
VirtualMachineAdapter:
  Scripts:
  - Name: ZEN_ArkGateSiegeQuestScript
    Properties:
    - MutagenObjectType: ScriptObjectProperty
      Name: {PERK}
      Object: 000800:{MOD}
  FileName: ''
Flags:
- StartGameEnabled
- RunOnce
NextAliasID: 0
"""

for sub in ("Perks", "Quests"):
    if os.path.isdir(os.path.join(OUT, sub)):
        shutil.rmtree(os.path.join(OUT, sub))
write(os.path.join(OUT, "Perks", f"{PERK} - 000800_{MOD}.yaml"), perk.replace("\n", CRLF))
write(os.path.join(OUT, "Quests", f"{QUEST} - 000801_{MOD}.yaml"), quest.replace("\n", CRLF))
for name in (FRAG, "ZEN_ArkGateSiegeQuestScript"):
    if not os.path.isfile(os.path.join(OUT, "..", "Scripts", "compiled", name + ".pex")):
        raise SystemExit(f"{name}.pex missing: compile Scripts/source first")
print(f"wrote {PERK} 000800 and {QUEST} 000801")
