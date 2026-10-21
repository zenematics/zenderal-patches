"""Generate the Qyra Island EditorID Fix plugin YAML -- never hand-edit its Worldspaces/.

Enderal 2.1 renamed Forgotten Stories' worldspace 00A6A0 ("Strange Place", Qyra's island) from
FS_NQ01_Qyra_Island to FSNQ01QyraIsland. Ships of the First Vassals.esp (built on 2.0, its last overrider)
carries a full copy of the 2.0 header, so it puts the old EditorID back. DynDOLOD refuses that ("Worldspace
Editor ID changed"), because LOD files are named by EditorID and 2.1's own LOD uses the new name.

Ships changed nothing on purpose in this header: its only other differences from FS 2.0 are an English-only
Name (unlocalized plugin) and SubCellsUnknown. So this is Ships' header verbatim with 2.1's EditorID.
Header only; the worldspace's cells and refs stay whatever wins them. Re-serialize Ships into
reference/mods/ShipsOfTheFirstVassals and re-check the winner (tools: scratch wrldedid scan) before re-running.
"""
import glob
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = glob.glob(os.path.join(ROOT, "reference", "mods", "ShipsOfTheFirstVassals", "Worldspaces", "* - 00A6A0_Enderal - Forgotten Stories.esm", "RecordData.yaml"))
OLD, NEW = "FS_NQ01_Qyra_Island", "FSNQ01QyraIsland"
WS = f"{NEW} - 00A6A0_Enderal - Forgotten Stories.esm"
OUT = os.path.join(ROOT, "src", "QyraIslandEditorIdFix", "QyraIslandEditorIdFixESP", "Worldspaces", WS, "RecordData.yaml")
SECTIONS = re.compile(r"^(TopCell|SubCells|NavigationMeshes|Persistent|Temporary):")

if len(SRC) != 1:
    raise SystemExit(f"expected Ships' 00A6A0 worldspace once, found {len(SRC)}")
text = open(SRC[0], encoding="utf-8", newline="").read()
nl = "\r\n" if "\r\n" in text else "\n"
head = []
for line in text.split(nl):
    if SECTIONS.match(line):
        break
    head.append(line)
head = nl.join(head).rstrip(nl) + nl
n = head.count(f"EditorID: {OLD}{nl}")
if n != 1:
    raise SystemExit(f"expected Ships' EditorID {OLD} once, found {n}")
head = head.replace(f"EditorID: {OLD}{nl}", f"EditorID: {NEW}{nl}")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w", encoding="utf-8", newline="").write(head)
print("wrote", OUT)
