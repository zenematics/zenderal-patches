r"""Generate the Jespar Merge plugin YAML -- never hand-edit its Npcs/.

Curator's request (2026-11-11): Hands of the Prophet (Enderal Nexus 1175) for Jespar only, not Calia. Three plugins
already edit Jespar's main record _00E_MC_Jespar 018A9A: EGO (stats, perks, keywords, combat style, one Steel Dagger),
Malphas' Blessing + MB - EGO (face) and Jespar Has Better Steel - Malphas' Blessing (his own JesparDagger x2). Better
Steel is built on the non-EGO Malphas record and loaded last, so Jespar had EGO's perks/stats undone.

Hands of the Prophet's EGO SE / Jespar plugin is EGO 1.93.1's record (the installed EGO) with its own face. This
plugin is that record verbatim with only the inventory replaced by Better Steel's (asserted: Hands of the Prophet's
items are EGO's Iron Dagger + Steel Dagger + MQ09 key, Better Steel's are JesparDagger x2 + the key). Its Purge twin
14BE8F needs nothing: only Malphas' Blessing touches it, and Hands of the Prophet loads after it.

Re-serialize both plugins into reference/mods/HandsOfTheProphet/Jespar EGO and reference/mods/JesparHasBetterSteel
before re-running.
"""
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
NAME = "_00E_MC_Jespar - 018A9A_Skyrim.esm.yaml"
HOTP = os.path.join(ROOT, "reference", "mods", "HandsOfTheProphet", "Jespar EGO", "Npcs", NAME)
STEEL = os.path.join(ROOT, "reference", "mods", "JesparHasBetterSteel", "Npcs", NAME)
OUT = os.path.join(ROOT, "src", "JesparMerge", "JesparMergeESP")
MASTERS = ["Skyrim.esm", "Update.esm", "Enderal - Forgotten Stories.esm", "Enderal SE - Gameplay Overhaul.esp",
           "Jespar Has Better Steel - Malphas' Blessing.esp",
           "Hands of the Prophet - A Jespar and Calia NPC Replacer.esp"]
ITEMS = re.compile(r"^Items:\r?\n(?:[- ] .*\r?\n)*", re.M)


def read(p):
    return open(p, encoding="utf-8", newline="").read()


def items(text):
    m = ITEMS.search(text)
    if not m:
        raise SystemExit("no Items block")
    pairs = re.findall(r"Item: (\S.*?)\r?\n +Count: (\d+)", m.group(0))
    return m, [(k, int(c)) for k, c in pairs]


hotp, steel = read(HOTP), read(STEEL)
hm, hotp_items = items(hotp)
sm, steel_items = items(steel)
if hotp_items != [("0028D2:Skyrim.esm", 1), ("019E7F:Skyrim.esm", 1), ("0EAA0D:Skyrim.esm", 1)]:
    raise SystemExit(f"Hands of the Prophet's items are not EGO's: {hotp_items}")
if steel_items != [("000800:Jespar Has Better Steel - Malphas' Blessing.esp", 2), ("0EAA0D:Skyrim.esm", 1)]:
    raise SystemExit(f"Better Steel's items changed: {steel_items}")
merged = hotp[:hm.start()] + sm.group(0) + hotp[hm.end():]

for key in sorted(set(re.findall(r"\b[0-9A-F]{6}:([^\r\n]+?\.es[mpl])\b", merged))):
    if key not in MASTERS:
        raise SystemExit(f"merged record references {key}, which is not a master")
os.makedirs(os.path.join(OUT, "Npcs"), exist_ok=True)
with open(os.path.join(OUT, "Npcs", NAME), "w", encoding="utf-8", newline="") as f:
    f.write(merged)
print("wrote", NAME, "(Hands of the Prophet's Jespar with Better Steel's JesparDagger x2 + key)")
