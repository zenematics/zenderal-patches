"""Generate the 2.1 Levelsystem Cleanup plugin YAML -- never hand-edit its record folders.

Enderal SE 2.1 deleted quest Levelsystem 010AA2:Skyrim.esm (the level system moved into EnderalSE.dll).
2.0-era overrides in the list still point at it, so xEdit/DynDOLOD stop on "Unresolved FormID [00010AA2]"
(first hit: Castle Bleakstar's chest 0201D9). In game those references already resolve to None, so removing
them changes no behaviour; it matches what SureAI did on their own records in 2.1:
  * script property pointing at 010AA2 ("Levelsystem" on _00E_ArmorSetScript, _00E_FS_A3_TalentBookSC, ...):
    removed -- base 2.1 removed that property (or the whole script) on every such record it ships;
  * script property "Player" = 010AA2 alias 0 (xion_playerhouse_document on mod house deeds): repointed to
    CustomNameControlQuest 0493BE alias 0 -- exactly how 2.1 repointed its own _00E_Game_Playerhouse deeds;
  * MESG "Quest: 010AA2" (EGO's _00E_Levelsystem_s* relationship messages): removed -- base 2.1 has no Quest.
Every other field is the winning override, copied verbatim, so the patch must load LAST.

Input: tools/00's winners.json (record -> winning plugin) and each winner serialized with Spriggit 0.40.0
into <serialized>/<plugin name, alphanumerics only>/. Usage: 01-build-levelsystem-cleanup.py <serialized> <winners.json>
"""
import glob
import json
import os
import re
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OUT = os.path.join(ROOT, "src", "Levelsystem21Cleanup", "Levelsystem21CleanupESP")
DEAD = "010AA2:Skyrim.esm"
PLAYER_ALIAS_QUEST = "0493BE:Skyrim.esm"  # CustomNameControlQuest, alias 0 (base 2.1's house deeds)
SER, WINNERS = sys.argv[1], sys.argv[2]


def drop_dead_properties(lines, rec):
    """Remove / repoint ScriptObjectProperty entries whose Object is DEAD. Returns (lines, removed, repointed)."""
    out, i, removed, repointed = [], 0, 0, 0
    while i < len(lines):
        l = lines[i]
        if l.strip() == "- MutagenObjectType: ScriptObjectProperty":
            ind = l[: len(l) - len(l.lstrip())]
            j = i + 1
            while j < len(lines) and lines[j].startswith(ind + "  "):
                j += 1
            blk = lines[i:j]
            if any(b.strip() == "Object: " + DEAD for b in blk):
                name = next(b.strip()[6:] for b in blk if b.strip().startswith("Name: "))
                if name == "Player" and any(b.strip() == "Alias: 0" for b in blk):
                    out += [b.replace(DEAD, PLAYER_ALIAS_QUEST) for b in blk]
                    repointed += 1
                else:
                    removed += 1
                i = j
                continue
        out.append(l)
        i += 1
    return out, removed, repointed


winners = json.load(open(WINNERS, encoding="utf-8"))
for d in ("RecordData.yaml", "spriggit-meta.json"):
    pass
for e in os.listdir(OUT) if os.path.isdir(OUT) else []:
    if e not in ("RecordData.yaml", "spriggit-meta.json"):
        shutil.rmtree(os.path.join(OUT, e))
tot = {"records": 0, "removed": 0, "repointed": 0, "quest": 0}
for w in winners:
    src_dir = os.path.join(SER, re.sub(r"[^A-Za-z0-9]", "", w["winner"]))
    hits = glob.glob(os.path.join(src_dir, "*", f"* - {w['id']}_{w['origin']}.yaml"))
    if len(hits) != 1:
        raise SystemExit(f"{w}: found {len(hits)} YAML files")
    text = open(hits[0], encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(nl)
    lines, rem, rep = drop_dead_properties(lines, w)
    q = [k for k, l in enumerate(lines) if l == "Quest: " + DEAD]
    for k in reversed(q):
        del lines[k]
    out = nl.join(lines)
    if DEAD in out:
        raise SystemExit(f"{w['edid']} ({w['id']}:{w['origin']}): 010AA2 still referenced after cleanup")
    if rem + rep + len(q) == 0:
        raise SystemExit(f"{w['edid']}: nothing removed -- winners.json is stale")
    dst = os.path.join(OUT, os.path.basename(os.path.dirname(hits[0])), os.path.basename(hits[0]))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, "w", encoding="utf-8", newline="").write(out)
    tot["records"] += 1
    tot["removed"] += rem
    tot["repointed"] += rep
    tot["quest"] += len(q)
print(tot)
EXPECTED = len(winners)
if tot["records"] != EXPECTED:
    raise SystemExit(f"expected {EXPECTED} records")
