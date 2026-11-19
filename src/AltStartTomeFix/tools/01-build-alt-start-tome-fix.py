r"""Generate the Alt Start Tome Fix plugin YAML -- never hand-edit its Containers/.

Report (player, 2026-11-16): the starting chest at Jespar's camp gives "Spell Tome: Psionic Push (Rank I)", whose
spell reads "This spell is no longer used in the Gameplay Overhaul". EGO renumbered the Psionic Push line: base
Enderal's Rank I spell 06FF25 is retired (description replaced, BaseCost 999), EGO's Rank I is the old Rank II
06FF26, taught by tome 01E8E2:FS (EGO's override names it Rank I). EGO also took the old tome 01E8DF:FS out of
every loot and trader list. Juno's Alt Start - Jespars Camp.esp (Enderal Nexus 1152) chest AltStart_CampChest
000800 still lists 01E8DF; a master-aware scan of the live load order found no other winning container, leveled
list or NPC carrying it (2026-11-16).

Fix: Juno's chest verbatim with that one entry pointing at EGO's Rank I tome 01E8E2:FS. Asserted: exactly one line
changes. Rerun after an Alt Start update (re-serialize it into reference/mods/AltStartJesparsCamp first).
"""
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
NAME = "AltStart_CampChest - 000800_Alt Start - Jespars Camp.esp.yaml"
SRC = os.path.join(ROOT, "reference", "mods", "AltStartJesparsCamp", "Containers", NAME)
OUT = os.path.join(ROOT, "src", "AltStartTomeFix", "AltStartTomeFixESP", "Containers", NAME)
OLD = "Item: 01E8DF:Enderal - Forgotten Stories.esm"
NEW = "Item: 01E8E2:Enderal - Forgotten Stories.esm"


def main():
    text = open(SRC, encoding="utf-8", newline="").read()
    if text.count(OLD) != 1:
        raise SystemExit(f"{SRC}: expected exactly one '{OLD}'")
    if NEW in text:
        raise SystemExit(f"{SRC}: already carries '{NEW}' (Alt Start updated? merge counts by hand)")
    new = text.replace(OLD, NEW)
    nl = "\r\n" if "\r\n" in text else "\n"
    changed = [a for a, b in zip(text.split(nl), new.split(nl)) if a != b]
    assert len(changed) == 1, changed
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8", newline="").write(new)
    print(f"wrote {OUT}: 01E8DF -> 01E8E2")


if __name__ == "__main__":
    main()
