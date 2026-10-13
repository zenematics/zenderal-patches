#!/usr/bin/env python3
"""Forward Undead Creatures Replacer's visuals onto EGO's NPCs for
Zenderal - Undead Creatures Replacer EGO Patch.esp.

Why: Kolapon's Undead Creatures Replacer.esp (UCR) masters only Skyrim/Update/FS, yet it
loads after EGO (175 vs 39 in Alpha 0.5) and overrides 44 Lost One / Ahnengeist NPCs, 36
of which EGO also overrides. Each UCR override is FS's (or base Enderal's) record plus the
new race/skin - so it silently reverts EGO on every one: stats, perks, inventories, death
items. Visible symptom: Zu-Sherath 04459F drops the FS tome 'Spell Tome: Chaosnova (Rank I)'
02F2A1, which EGO removed because it retired that spell (EGO's spell 02F297 carries the
'This spell is no longer used in the "Gameplay Overhaul"' description).

Rule, per UCR NPC (UCR's deleted 02F518 is left alone - its only two refs are deleted too):
  record  = the previous winner verbatim (EGO SE - Leveling Redone > EGO > FS > Skyrim)
  + every field UCR changed vs the record it was copied from (FS, else Skyrim), if in FORWARD
  + Configuration: only UCR's add/remove of Flags / TemplateFlags entries (Female flag; the
    template-flag drops that go with UCR unlinking a Template) - never its stat scalars
  Fields in DROP are stale FS data, not visual work, and are NOT forwarded: UCR strips
  ActorTypeBoss from four bosses, a package from the trigger NPCs, an AIData warn radius,
  and swaps one boss template's combat Class.
An NPC is emitted only if the result differs from what UCR already ships in game, i.e. the
previous winner is not UCR's own base, or UCR changed a DROP field.

Any UCR field change in neither set fails the script - classify it before shipping.

Inputs (regenerate with /spriggit-decompile-reference):
  reference/base/{Skyrim,EnderalFS}/Npcs
  reference/mods/EGO/Npcs                     (Enderal SE - Gameplay Overhaul.esp)
  reference/mods/LevelingRedoneEGO/Npcs       (EGO SE - Leveling Redone.esp)
  reference/mods/UndeadCreaturesReplacer/Npcs (Undead Creatures Replacer.esp)
The winner chain was taken from a binary scan of every active plugin in 'Alpha 0.5':
only Skyrim, FS, Enderal SE - Bug Fixes (090A0F, 1401A4; both lose to EGO), EGO,
Leveling Redone.esp + EGO SE - Leveling Redone (1401A4) and UCR touch these NPCs, and UCR
wins every one. Re-run that scan if the list changes.
Output: src/UndeadCreaturesReplacerEGO/UndeadCreaturesReplacerEGOESP/Npcs/*.yaml (regenerated)
"""
import collections
import glob
import os
import re
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
REF = os.path.join(ROOT, "reference")
OUT = os.path.join(ROOT, "src", "UndeadCreaturesReplacerEGO", "UndeadCreaturesReplacerEGOESP", "Npcs")

# Previous-winner search order, latest first. Bug Fixes is absent on purpose: EGO beats it.
WINNERS = [("EGO SE - Leveling Redone", "mods/LevelingRedoneEGO"),
           ("EGO", "mods/EGO"),
           ("FS", "base/EnderalFS"),
           ("Skyrim", "base/Skyrim")]
FORWARD = {"Race", "WornArmor", "Height", "AttackRace", "Attacks", "Template", "Name"}
DROP = {"Keywords", "Packages", "AIData", "Class"}
NOISE = {"IsCompressed", "MajorRecordFlagsRaw", "SkyrimMajorRecordFlags", "MajorFlags", "Version2"}
CONFIG_LISTS = ("Flags", "TemplateFlags")


def blocks(text):
    """Top-level YAML keys -> their verbatim lines."""
    out = collections.OrderedDict()
    cur = None
    for line in text.splitlines():
        if line and line[0] not in " -":
            cur = line.split(":", 1)[0]
            out[cur] = [line]
        else:
            out[cur].append(line)
    return out


def english(b):
    t = "\n".join(b)
    m = re.search(r"Language: English\n\s+String: (.*)", t) or re.search(r"Value: (.*)", t)
    return m.group(1) if m else t


def delocalize(lines):
    """FS strings are Values lists; this plugin is not Localized, so keep English as Value."""
    out, i = [], 0
    while i < len(lines):
        m = re.match(r"^(\s*)Values:$", lines[i])
        if m:
            ind = m.group(1)
            j, eng = i + 1, None
            while j < len(lines) and (lines[j].startswith(ind + "- ") or lines[j].startswith(ind + "  ")):
                s = re.match(r"^\s+String: (.*)$", lines[j])
                if s and re.match(r"^\s*- Language: English$", lines[j - 1]):
                    eng = s.group(1)
                j += 1
            if eng is None:
                sys.exit(f"no English string in Values block: {lines[i-1:i+3]}")
            out.append(f"{ind}Value: {eng}")
            i = j
            continue
        out.append(lines[i])
        i += 1
    return out


def sublist(cfg, key):
    """Entries of Configuration.<key> list, or None if absent."""
    items, on = [], False
    for line in cfg:
        if line == f"  {key}:":
            on = True
            continue
        if on:
            if line.startswith("  - "):
                items.append(line[4:])
            else:
                break
    return items if on else None


def set_sublist(cfg, key, items):
    """Rewrite Configuration.<key> (dropping it if empty), keeping its position."""
    out, i, done = [], 0, False
    while i < len(cfg):
        if cfg[i] == f"  {key}:":
            i += 1
            while i < len(cfg) and cfg[i].startswith("  - "):
                i += 1
            if items:
                out.append(f"  {key}:")
                out += [f"  - {x}" for x in items]
            done = True
            continue
        out.append(cfg[i])
        i += 1
    if not done and items:  # Flags goes first, TemplateFlags after the level block
        at = 1 if key == "Flags" else len(out)
        out[at:at] = [f"  {key}:"] + [f"  - {x}" for x in items]
    return out


def find(tree, fk):
    h, m = fk.split(":", 1)
    g = glob.glob(os.path.join(REF, tree, "Npcs", f"* - {h}_{m}.yaml"))
    return g[0] if g else None


def read(p):
    with open(p, encoding="utf-8", newline="") as f:
        return f.read()


if os.path.isdir(OUT):
    shutil.rmtree(OUT)
os.makedirs(OUT)

ucr_files = sorted(glob.glob(os.path.join(REF, "mods", "UndeadCreaturesReplacer", "Npcs", "*.yaml")))
assert len(ucr_files) == 44, f"expected 44 UCR NPCs, found {len(ucr_files)}"
emitted, skipped, deleted = [], [], []
counts = collections.Counter()
for uf in ucr_files:
    u = blocks(read(uf))
    fk = u["FormKey"][0].split(": ", 1)[1]
    if "IsDeleted" in u:
        deleted.append(fk)
        continue
    base_path = find("base/EnderalFS", fk) or find("base/Skyrim", fk)
    assert base_path, fk
    b = blocks(read(base_path))
    win_name, win_path = next((n, find(t, fk)) for n, t in WINNERS if find(t, fk))
    w = blocks(read(win_path))

    changed = []
    for k in dict.fromkeys(list(u) + list(b)):
        if k in NOISE or u.get(k) == b.get(k):
            continue
        if k == "Name" and k in u and k in b and english(u[k]) == english(b[k]):
            continue
        changed.append(k)
    unknown = [k for k in changed if k not in FORWARD | DROP | {"Configuration"}]
    if unknown:
        sys.exit(f"{fk}: unclassified UCR change(s) {unknown}")

    out = collections.OrderedDict((k, list(v)) for k, v in w.items())
    for k in changed:
        if k in FORWARD:
            counts[k] += 1
            if k in u:
                out[k] = list(u[k])
                if k not in w:  # new key: place it where UCR has it
                    keys = list(out)
                    keys.remove(k)
                    prev = list(u)[list(u).index(k) - 1]
                    keys.insert(keys.index(prev) + 1 if prev in keys else len(keys), k)
                    out = collections.OrderedDict((x, out[x]) for x in keys)
            else:
                out.pop(k, None)
        elif k == "Configuration":
            cfg = out["Configuration"]
            for key in CONFIG_LISTS:
                bu, bb = sublist(u["Configuration"], key) or [], sublist(b["Configuration"], key) or []
                add = [x for x in bu if x not in bb]
                rem = [x for x in bb if x not in bu]
                if add or rem:
                    counts[f"Configuration.{key}"] += 1
                    cur = sublist(cfg, key) or []
                    cfg = set_sublist(cfg, key, [x for x in cur if x not in rem] + [x for x in add if x not in cur])
            out["Configuration"] = cfg
        else:
            counts[f"dropped {k}"] += 1

    needed = win_path != base_path or any(k in DROP for k in changed)
    if not needed:
        skipped.append(fk)
        continue
    lines = delocalize([l for v in out.values() for l in v])
    text = "\r\n".join(lines) + "\r\n"
    with open(os.path.join(OUT, os.path.basename(win_path)), "w", encoding="utf-8", newline="") as f:
        f.write(text)
    emitted.append((fk, win_name, changed))

for fk, wn, ch in emitted:
    print(f"  {fk:42} from {wn:26} UCR changed {ch}")
print(f"emitted {len(emitted)}, skipped {len(skipped)} (UCR already right: {skipped}), deleted left alone {deleted}")
print(dict(counts))
# Pinned expectations - a mod update must fail here, not ship quietly.
assert deleted == ["02F518:Enderal - Forgotten Stories.esm"], deleted
assert len(emitted) == 38, len(emitted)
