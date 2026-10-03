#!/usr/bin/env python3
"""Generate Zenderal - Pretty Armory EGO Patch.esp: Pretty's looks, EGO's gameplay.

The eleven Pretty * Armory / Clothing / Backpacks plugins load after EGO and were authored
against vanilla Enderal records, so every record they override silently reverts EGO's
armour ratings, weapon stats, prices, weights, enchantments, armour types and keywords
(and, on five NPCs, EGO's perks and skills). They also revert a few Enderal SE - Bug Fixes
values and Audio Overhaul's footstep sounds.

For every record with a Pretty plugin in its live override chain, this emits one override:
the in-game WINNER's record (Pretty's, so its meshes/armatures/outfits survive) with the
DONOR plugins' gameplay changes forwarded on top. Field policy:

  PRETTY_FIELDS   always the winner's: models, armatures, bounds, templates, outfits, items,
                  head parts. Pretty's whole point; EGO's model swaps lose to them.
  ARMA records    winner's in full EXCEPT FootstepSound (donor) and AdditionalRaces (union).
                  Mixing another mod's slot/weight-slider data onto Pretty's mesh is unsafe.
  STAT records    untouched (no donor ever changes them).
  Keywords        set merge: winner's set + every donor addition - every donor removal,
                  except a keyword the winner itself added is never removed.
  BodyTemplate    sub-field merge: FirstPersonFlags from the winner, everything else
                  (ArmorType, ...) follows the donor rule.
  Name/Desc       compared on the English string (EGO and Pretty are both non-localized,
                  so the format difference is a null diff); a genuine Pretty rename wins.
  anything else   the donor's value when any donor changed it from base, else the winner's.

"Donor value" = the base record with each DONOR plugin's own changes applied in load order
(a later donor's change to a field wins). Base = the last of Skyrim/Update/FS in the chain.

Only records whose merged result differs from the winner are written. Visual replacers that
lose to Pretty (Unique Amulet Replacer, Guard Armor Replacer Falconer, ...) are deliberately
NOT donors - the in-game look stays exactly what it is today.

Inputs:
  reference/mods/Pretty/_chains.json        <- 01-build-override-chains.py
  reference/mods/Pretty/<plugin>/           <- /spriggit-decompile-reference, one per Pretty plugin
  reference/mods/PrettyContext/<plugin>/    <- same, for Bug Fixes + the two AOS plugins
  reference/mods/EGO, reference/base/{Skyrim,Update,EnderalFS}

Output: src/PrettyArmoryEGO/PrettyArmoryEGOESP/<RecordType>/*.yaml plus the master list in
RecordData.yaml. The record folders are wiped and regenerated - never hand-edit them.
"""
import collections
import json
import os
import re
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
REF = os.path.join(ROOT, "reference")
ESP = os.path.join(ROOT, "src", "PrettyArmoryEGO", "PrettyArmoryEGOESP")
CHAINS = os.path.join(REF, "mods", "Pretty", "_chains.json")

BASE = ["Skyrim.esm", "Update.esm", "Enderal - Forgotten Stories.esm"]
EGO = "Enderal SE - Gameplay Overhaul.esp"
DONORS = [EGO, "Enderal SE - Bug Fixes.esp",
          "Audio Overhaul Skyrim.esp", "Audio Overhaul - Enderal patch.esp"]

TREES = {
    "Skyrim.esm": os.path.join(REF, "base", "Skyrim"),
    "Update.esm": os.path.join(REF, "base", "Update"),
    "Enderal - Forgotten Stories.esm": os.path.join(REF, "base", "EnderalFS"),
    EGO: os.path.join(REF, "mods", "EGO"),
}
for sub in ("Pretty", "PrettyContext"):
    d = os.path.join(REF, "mods", sub)
    for n in os.listdir(d):
        if os.path.isdir(os.path.join(d, n)):
            TREES[n + ".esp"] = os.path.join(d, n)

FOLDER = {"ARMO": "Armors", "WEAP": "Weapons", "AMMO": "Ammunitions", "ARMA": "ArmorAddons",
          "OUTF": "Outfits", "NPC_": "Npcs", "STAT": "Statics", "PROJ": "Projectiles"}
PRETTY_FIELDS = {"Model", "WorldModel", "FirstPersonModel", "Armature", "ObjectBounds",
                 "TemplateArmor", "Template", "DefaultOutfit", "Items", "HeadParts",
                 "EditorID", "FormKey"}
ARMA_DONOR_FIELDS = {"FootstepSound", "AdditionalRaces"}
STRING_FIELDS = {"Name", "Description", "ShortName"}
# Spriggit bookkeeping - never a gameplay change, never forwarded.
# IsCompressed / MajorRecordFlagsRaw and a MajorFlags of only 0x40000 are the record-compression
# bit - storage, not content (EGO's five NPC overrides differ from base by nothing else there).
IGNORE = {"FormVersion", "Version2", "VersionControl", "SkyrimMajorRecordFlags",
          "IsCompressed", "MajorRecordFlagsRaw"}

FILE_RE = re.compile(r"(?:^|.* - )([0-9A-F]{6})_(.+)\.yaml$")
FK_RE = re.compile(r"\b[0-9A-F]{6}:([^\r\n:]+?\.es[pml])\b")

_index = {}


def index(plugin):
    if plugin not in _index:
        if plugin not in TREES:
            sys.exit(f"no reference tree for {plugin} - serialize it with /spriggit-decompile-reference")
        m = {}
        for dp, _, fs in os.walk(TREES[plugin]):
            for f in fs:
                g = FILE_RE.match(f)
                if g:
                    m[f"{g.group(1)}:{g.group(2)}"] = os.path.join(dp, f)
        _index[plugin] = m
    return _index[plugin]


def load(plugin, fk):
    """OrderedDict field -> list of lines (no line endings). Top-level YAML keys only."""
    path = index(plugin).get(fk)
    if not path:
        sys.exit(f"{fk} is in {plugin}'s chain but not in its reference tree - re-serialize it")
    out = collections.OrderedDict()
    cur = None
    with open(path, encoding="utf-8-sig", newline="") as f:
        for line in f.read().splitlines():
            if line and not line[0].isspace() and not line.startswith("- "):
                cur = line.split(":", 1)[0]
                out[cur] = [line]
            elif cur is not None:
                out[cur].append(line)
    if out.get("MajorFlags") == ["MajorFlags:", "- 0x40000"]:
        del out["MajorFlags"]
    return out


def english(block):
    """The English text of a Name/Description block, whatever its localization shape."""
    if block is None:
        return None
    lines = block[1:]
    for i, l in enumerate(lines):
        if l.strip() == "- Language: English" and i + 1 < len(lines):
            return lines[i + 1].split("String:", 1)[1].strip()
    for l in lines:
        if l.strip().startswith("Value:"):
            return l.split("Value:", 1)[1].strip()
    return block[0].split(":", 1)[1].strip()


def non_localized(field, block):
    """Rewrite a localized Values: block as the plugin's non-localized single English Value."""
    if block is None or not any(l.strip() == "Values:" for l in block):
        return block
    return [f"{field}:", "  TargetLanguage: English", f"  Value: {english(block)}"]


def garbled(block):
    """True for UTF-8 Cyrillic that was decoded as cp1252 ('Ð°Ð½...')."""
    text = english(block) or ""
    return bool(re.search(r"[ÐÑ][-¿ŒœŠšŸŽžƒˆ˜–-›€™]", text))


def keywords(block):
    return [l[2:].strip() for l in (block or [])[1:] if l.startswith("- ")]


def subfields(block):
    """BodyTemplate -> OrderedDict subkey -> lines."""
    out = collections.OrderedDict()
    cur = None
    for l in (block or [])[1:]:
        if l.startswith("  ") and not l.startswith("  -") and not l.startswith("   "):
            cur = l.strip().split(":", 1)[0]
            out[cur] = [l]
        elif cur is not None:
            out[cur].append(l)
    return out


def same(field, a, b):
    if field in STRING_FIELDS:
        return english(a) == english(b)
    if field == "Keywords":
        return set(keywords(a)) == set(keywords(b))
    return a == b


def merge_record(typ, fk, chain):
    winner = chain[-1]
    base = [p for p in chain if p in BASE][-1]
    donors = [p for p in chain[:-1] if p in DONORS]
    B = load(base, fk)
    W = load(winner, fk)
    D = {p: load(p, fk) for p in donors}
    out = collections.OrderedDict((k, list(v)) for k, v in W.items())
    changed = []

    def donor_value(field):
        """(changed?, value) - the last donor whose value differs from base wins."""
        hit, val = False, B.get(field)
        for p in donors:
            if not same(field, D[p].get(field), B.get(field)):
                hit, val = True, D[p].get(field)
        return hit, val

    fields = list(W.keys())
    for p in donors:
        for f in D[p]:
            if f not in fields:
                fields.append(f)
    for f in B:
        if f not in fields:
            fields.append(f)

    for f in fields:
        if f in IGNORE or f in PRETTY_FIELDS:
            continue
        if typ == "STAT" or (typ == "ARMA" and f not in ARMA_DONOR_FIELDS):
            continue
        if f == "Keywords" or (typ == "ARMA" and f == "AdditionalRaces"):
            bset = keywords(B.get(f))
            wl = keywords(W.get(f))
            own_adds = set(wl) - set(bset)
            adds, rems = [], set()
            for p in donors:
                dl = keywords(D[p].get(f))
                adds += [k for k in dl if k not in bset and k not in adds]
                rems |= set(bset) - set(dl)
            if f == "AdditionalRaces":
                rems = set()
            new = [k for k in wl if not (k in rems and k not in own_adds)]
            new += [k for k in adds if k not in new]
            if set(new) != set(wl):
                out[f] = [f"{f}:"] + [f"- {k}" for k in new] if new else None
                changed.append(f)
            continue
        if f == "BodyTemplate" and typ == "ARMO":
            wsub = subfields(W.get(f))
            bsub = subfields(B.get(f))
            msub = collections.OrderedDict((k, v) for k, v in wsub.items())
            for p in donors:
                for k in subfields(D[p].get(f)):
                    if k not in msub and k != "FirstPersonFlags":
                        msub[k] = None
            for k in list(msub.keys()) + [k for k in bsub if k not in msub]:
                if k == "FirstPersonFlags":
                    continue
                hit, val = False, bsub.get(k)
                for p in donors:
                    dv = subfields(D[p].get(f)).get(k)
                    if dv != bsub.get(k):
                        hit, val = True, dv
                if hit:
                    msub[k] = val
            canon = []
            for p in reversed(donors):
                canon += [k for k in subfields(D[p].get(f)) if k not in canon]
            canon += [k for k in bsub if k not in canon]
            keyorder = ["FirstPersonFlags"] + [k for k in canon if k in msub and k != "FirstPersonFlags"]
            keyorder += [k for k in msub if k not in keyorder]
            new = [l for k in keyorder if msub.get(k) for l in msub[k]]
            if new != (W.get(f) or [None])[1:]:
                # keep the winner's key order: FirstPersonFlags first, as Spriggit writes it
                out[f] = ["BodyTemplate:"] + new
                changed.append(f)
            continue
        hit, val = donor_value(f)
        if f in STRING_FIELDS:
            if garbled(W.get(f)):
                # Pretty Unique Armory ships 3 weapon descriptions as mis-encoded Russian
                # (UTF-8 read as cp1252) - they display as garbage today. Never keep those.
                hit, val = True, (val if val is not None else B.get(f))
            elif not hit or not same(f, W.get(f), B.get(f)):
                continue  # nothing to forward, or a genuine Pretty rename wins
            val = non_localized(f, val)
        elif not hit:
            continue
        if same(f, val, W.get(f)) and (f in STRING_FIELDS or val == W.get(f)):
            continue
        out[f] = val
        changed.append(f)

    if not changed:
        return None, []
    # place fields the winner lacks right after their predecessor in the donor/base file
    order = list(W.keys())
    for f in changed:
        if f not in order and out.get(f) is not None:
            ref = next((D[p] for p in reversed(donors) if f in D[p]), B)
            keys = list(ref.keys())
            prev = [k for k in keys[:keys.index(f)] if k in order]
            order.insert(order.index(prev[-1]) + 1 if prev else len(order), f)
    lines = []
    for k in order:
        if out.get(k) is not None:
            lines += out[k]
    return lines, changed


def main():
    data = json.load(open(CHAINS, encoding="utf-8"))
    chains, load_order = data["chain"], data["order"]
    for folder in FOLDER.values():
        shutil.rmtree(os.path.join(ESP, folder), ignore_errors=True)

    stats = collections.Counter()
    per_winner = collections.Counter()
    referenced = set()
    written = 0
    candidates = 0
    for fk, v in sorted(chains.items()):
        chain, typ = v["chain"], v["type"]
        owner = fk.split(":", 1)[1]
        if owner.startswith("Pretty") or not any(p.startswith("Pretty") for p in chain):
            continue
        if not any(p in DONORS for p in chain[:-1]):
            continue
        candidates += 1
        lines, changed = merge_record(typ, fk, chain)
        if lines is None:
            continue
        for f in changed:
            stats[(typ, f)] += 1
        per_winner[chain[-1]] += 1
        name = os.path.basename(index(chain[-1])[fk])
        d = os.path.join(ESP, FOLDER[typ])
        os.makedirs(d, exist_ok=True)
        text = "\r\n".join(lines) + "\r\n"
        with open(os.path.join(d, name), "w", encoding="utf-8", newline="") as f:
            f.write(text)
        referenced |= set(FK_RE.findall(text))
        referenced.add(chain[-1])  # master every winner so the engine enforces load-after
        written += 1

    # ---- masters: everything referenced or overridden, in live load order ------------------
    referenced |= {p for p in BASE}
    for p in referenced:
        if p not in load_order:
            sys.exit(f"output references {p}, which is not in the active load order")
    masters = [p for p in load_order if p in referenced]
    if "Dawnguard.esm" in masters or "Dragonborn.esm" in masters or "HearthFires.esm" in masters:
        sys.exit("refusing to master a DLC stub - see CLAUDE.md 'Masters'")
    rd = os.path.join(ESP, "RecordData.yaml")
    text = open(rd, encoding="utf-8", newline="").read()
    mblock = "  MasterReferences:\r\n" + "".join(
        f"  - Master: {m}\r\n    FileSize: 0\r\n" for m in masters)
    text, n = re.subn(r"  MasterReferences:\r?\n(?:  - Master: .*\r?\n    FileSize: .*\r?\n)+",
                      lambda _: mblock, text)
    if n != 1:
        sys.exit("could not find the MasterReferences block in RecordData.yaml")
    with open(rd, "w", encoding="utf-8", newline="") as f:
        f.write(text)

    # ---- report + assertions -------------------------------------------------------------------
    print(f"candidates (Pretty + a donor in chain): {candidates}, overrides written: {written}")
    for (t, f), n in sorted(stats.items()):
        print(f"  {n:4} {t} {f}")
    print("by winner:")
    for p, n in per_winner.most_common():
        print(f"  {n:4} {p}")
    print("masters:", ", ".join(masters))
    if written < 100:
        sys.exit(f"only {written} overrides - expected ~140; a reference tree is probably stale")


if __name__ == "__main__":
    main()
