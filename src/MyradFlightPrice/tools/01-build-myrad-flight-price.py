"""Generate the Myrad Flight Price plugin YAML -- never hand-edit its DialogTopics/.

Player report (GreaseLord, 2026-11-06): the Myrad keeper in Ark says a flight costs 25 pennies but actually needs 50.
Enderal 2.1 prices a flight at 25 everywhere: the topic text "(25 pennies)", the four responses' gold gates (>= 25 to
fly, < 25 to be refused) and the charge itself (_00E_MyradSystem02 removes the MyradTripPrice global 0493E1 = 25).
EGO (a 2.0-era plugin) raised it to 50: its copies of the four responses gate at 50, and its quest record gives the
script an int Price = 50 that 2.1's script no longer reads (and leaves MyradTripPrice unfilled). DBVO_EnderalPatch
(Ciri - Enderal Dialogue Fixes) wins the topic and keeps 2.1's "(25 pennies)" text. The curator chose 25.

This plugin carries DBVO's topic header verbatim (overriding the responses requires the topic) and EGO's four
responses verbatim with only the gold gate's ComparisonValue 50 -> 25 (asserted: one gold GetItemCount per response,
value 50). The charge half lives in Levelsystem21Cleanup, which owns quest 0D9B17 and now fills MyradTripPrice.
Re-serialize EGO into reference/mods/EGO and DBVO_EnderalPatch into reference/mods/DBVOEnderalPatch before re-running.
"""
import os
import re
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OUT = os.path.join(ROOT, "src", "MyradFlightPrice", "MyradFlightPriceESP", "DialogTopics")
TOPIC = "MyradDialogue_StartTopic_T1Topic01 - 12E0EC_Skyrim.esm"
DBVO = os.path.join(ROOT, "reference", "mods", "DBVOEnderalPatch", "DialogTopics", TOPIC, "RecordData.yaml")
EGO = os.path.join(ROOT, "reference", "mods", "EGO", "DialogTopics", TOPIC, "Responses")
RESPONSES = ["12E110", "12E111", "14CB50", "14CB51"]
OLD, NEW = "50", "25"


def read(p):
    return open(p, encoding="utf-8", newline="").read()


def regate(text, rid):
    nl = "\r\n" if "\r\n" in text else "\n"
    blocks = re.split(r"(?=^- MutagenObjectType: Condition)", text, flags=re.M)
    hits = 0
    for i, b in enumerate(blocks):
        if "GetItemCountConditionData" in b and "00000F:Skyrim.esm" in b:
            n = b.count(f"ComparisonValue: {OLD}{nl}")
            if n != 1:
                raise SystemExit(f"{rid}: gold gate is not {OLD}")
            blocks[i] = b.replace(f"ComparisonValue: {OLD}{nl}", f"ComparisonValue: {NEW}{nl}")
            hits += 1
    if hits != 1:
        raise SystemExit(f"{rid}: expected one gold GetItemCount condition, found {hits}")
    return "".join(blocks)


if os.path.isdir(OUT):
    shutil.rmtree(OUT)
os.makedirs(os.path.join(OUT, TOPIC, "Responses"))
head = read(DBVO)
if "(25 pennies)" not in head:
    raise SystemExit("DBVO's topic text no longer says 25 pennies; re-check")
open(os.path.join(OUT, TOPIC, "RecordData.yaml"), "w", encoding="utf-8", newline="").write(head)
for rid in RESPONSES:
    src = os.path.join(EGO, f"{rid}_Skyrim.esm.yaml")
    open(os.path.join(OUT, TOPIC, "Responses", f"{rid}_Skyrim.esm.yaml"), "w", encoding="utf-8", newline="").write(
        regate(read(src), rid))
print(f"topic {TOPIC} (DBVO's header) + {len(RESPONSES)} responses, gold gate {OLD} -> {NEW}")
