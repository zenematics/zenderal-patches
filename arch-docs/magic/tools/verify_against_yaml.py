#!/usr/bin/env python3
"""Differential check: MagicExtract JSON vs the Spriggit YAML reference trees.

Two independent decoders read the same plugin bytes — MagicExtract (Mutagen 0.54.4)
and Spriggit 0.40.0 (serialized into reference/). For every record whose WINNER has a
serialized tree, every scalar field PRESENT in the winner's YAML must match the JSON.

The comparison is deliberately ONE-DIRECTIONAL: Spriggit omits default-valued fields,
so absence in YAML proves nothing — but presence with a different value proves a bug
in one of the two decoders (or in MagicExtract's load-order resolution).

Match on FormKey, never EditorID — EGO renames records (_21E_SpellFireball_NPC → NPCFireball).

Usage (from the repo root, after Run-MagicExtract.ps1):

    python arch-docs/magic/tools/verify_against_yaml.py

Requires PyYAML. Exits 1 on any mismatch.
"""
import json
import os
import re
import sys

try:
    import yaml
    try:
        from yaml import CSafeLoader as Loader
    except ImportError:
        from yaml import SafeLoader as Loader
except ImportError:
    sys.exit("PyYAML required: pip install pyyaml")

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
DATA = os.path.join(ROOT, "arch-docs", "magic", "data")
REF = os.path.join(ROOT, "reference")

# winner plugin -> serialized Spriggit tree. Only these winners are checkable.
TREES = {
    "Skyrim.esm": os.path.join(REF, "base", "Skyrim"),
    "Enderal - Forgotten Stories.esm": os.path.join(REF, "base", "EnderalFS"),
    "Enderal SE - Gameplay Overhaul.esp": os.path.join(REF, "mods", "EGO", "esp"),
    "KataPUMBSpellPack.esp": os.path.join(REF, "mods", "KataPUMB"),
}

# dataset file -> Spriggit type dir + (yamlKey, jsonPath) scalar field map
SPELL_FIELDS = [
    ("EditorID", "editorId"), ("Type", "type"), ("CastType", "castType"),
    ("TargetType", "targetType"), ("BaseCost", "cost.baseCost"), ("ChargeTime", "chargeTime"),
    ("CastDuration", "castDuration"), ("Range", "range"),
]
DATASETS = {
    "spells.json": ("Spells", SPELL_FIELDS),
    "scrolls.json": ("Scrolls", SPELL_FIELDS + [("Value", "value"), ("Weight", "weight")]),
    "magic-effects.json": ("MagicEffects", [
        ("EditorID", "editorId"), ("BaseCost", "baseCost"), ("MagicSkill", "magicSkill"),
        ("ResistValue", "resistValue"), ("CastType", "castType"), ("TargetType", "targetType"),
        ("MinimumSkillLevel", "minimumSkillLevel"), ("SpellmakingCastingTime", "spellmakingCastingTime"),
        ("TaperWeight", "taperWeight"), ("TaperCurve", "taperCurve"), ("TaperDuration", "taperDuration"),
        ("DualCastScale", "dualCastScale"), ("SkillUsageMultiplier", "skillUsageMultiplier"),
    ]),
    "enchantments.json": ("ObjectEffects", [
        ("EditorID", "editorId"), ("EnchantmentCost", "enchantmentCost"),
        ("EnchantmentAmount", "enchantmentAmount"), ("CastType", "castType"),
        ("TargetType", "targetType"), ("ChargeTime", "chargeTime"),
    ]),
    "ingestibles.json": ("Ingestibles", [
        ("EditorID", "editorId"), ("Value", "value"), ("Weight", "weight"),
        ("AddictionChance", "addictionChance"),
    ]),
    "shouts.json": ("Shouts", [("EditorID", "editorId")]),
}

FILE_RE = re.compile(r" - ([0-9A-Fa-f]{6})_(.+)\.yaml$")


def index_tree(tree_path, type_dir):
    """(FID_upper, master) -> yaml path for one record-type folder of one tree."""
    d = os.path.join(tree_path, type_dir)
    idx = {}
    if not os.path.isdir(d):
        return idx
    for fn in os.listdir(d):
        m = FILE_RE.search(fn)
        if m:
            idx[(m.group(1).upper(), m.group(2))] = os.path.join(d, fn)
    return idx


def json_path(record, dotted):
    node = record
    for seg in dotted.split("."):
        if node is None:
            return None
        node = node.get(seg) if isinstance(node, dict) else None
    return node


def yaml_name_string(val):
    """Spriggit Name/Description shapes: plain string; single-language block with `Value:`
    (non-Localized plugins like EGO); or localized block with a `Values:` list."""
    if isinstance(val, str):
        return val
    if isinstance(val, dict):
        if "Value" in val:
            return val["Value"]
        for entry in val.get("Values") or []:
            if entry.get("Language") == "English":
                return entry.get("String")
        return None
    return None


def values_match(y, j):
    if y is None and j is None:
        return True
    # empty string vs null are the same authored state
    if (y == "" and j is None) or (y is None and j == ""):
        return True
    if isinstance(y, bool) or isinstance(j, bool):
        return bool(y) == bool(j)
    if isinstance(y, (int, float)) and isinstance(j, (int, float)):
        return abs(float(y) - float(j)) <= max(1e-4, abs(float(y)) * 1e-4)
    return str(y) == str(j)


def main():
    missing_trees = [k for k, v in TREES.items() if not os.path.isdir(v)]
    for k in missing_trees:
        print(f"note: no serialized tree for {k} ({TREES[k]}) — its records are skipped")
    trees = {k: v for k, v in TREES.items() if os.path.isdir(v)}
    if not trees:
        sys.exit("no reference trees found — run /spriggit-decompile-reference first")

    checked = matched = 0
    mismatches = []
    files_missing = 0

    for ds_file, (type_dir, fields) in DATASETS.items():
        with open(os.path.join(DATA, ds_file), encoding="utf-8") as f:
            records = json.load(f)["records"]
        tree_idx = {w: index_tree(p, type_dir) for w, p in trees.items()}

        for rec in records:
            winner = rec["provenance"]["winner"]
            idx = tree_idx.get(winner)
            if idx is None:
                continue
            fid, master = rec["formKey"].split(":", 1)
            ypath = idx.get((fid.upper(), master))
            if ypath is None:
                # The winner's tree must contain the record it wins with.
                files_missing += 1
                mismatches.append(f"{ds_file} {rec['formKey']}: no YAML in {winner}'s tree ({type_dir})")
                continue
            with open(ypath, encoding="utf-8") as f:
                y = yaml.load(f, Loader=Loader)

            checked += 1
            rec_ok = True
            for ykey, jpath in fields:
                if ykey not in y:
                    continue  # omitted = default; proves nothing
                yv, jv = y[ykey], json_path(rec, jpath)
                if not values_match(yv, jv):
                    rec_ok = False
                    mismatches.append(f"{ds_file} {rec['formKey']} {ykey}: yaml={yv!r} json={jv!r} ({ypath})")
            # Name (localized block or plain string)
            if "Name" in y:
                yn = yaml_name_string(y["Name"])
                if not values_match(yn, rec.get("name")):
                    rec_ok = False
                    mismatches.append(f"{ds_file} {rec['formKey']} Name: yaml={yn!r} json={rec.get('name')!r}")
            # Effects: count + per-entry BaseEffect/Magnitude/Area/Duration
            if "Effects" in y and isinstance(y["Effects"], list):
                je = rec.get("effects") or []
                ye = y["Effects"]
                if len(ye) != len(je):
                    rec_ok = False
                    mismatches.append(f"{ds_file} {rec['formKey']} Effects: yaml has {len(ye)}, json has {len(je)}")
                else:
                    for i, (yeff, jeff) in enumerate(zip(ye, je)):
                        ybase = str(yeff.get("BaseEffect", "")).upper()
                        jbase = str((jeff.get("baseEffect") or {}).get("formKey", "")).upper()
                        if ybase and ybase != jbase:
                            rec_ok = False
                            mismatches.append(f"{ds_file} {rec['formKey']} effect[{i}].BaseEffect: yaml={ybase} json={jbase}")
                        ydata = yeff.get("Data") or {}
                        for dk, jk in (("Magnitude", "magnitude"), ("Area", "area"), ("Duration", "duration")):
                            if dk in ydata and not values_match(ydata[dk], jeff.get(jk)):
                                rec_ok = False
                                mismatches.append(
                                    f"{ds_file} {rec['formKey']} effect[{i}].{dk}: yaml={ydata[dk]!r} json={jeff.get(jk)!r}")
            if rec_ok:
                matched += 1

    print(f"\nchecked {checked} records against Spriggit YAML; {matched} fully matched, "
          f"{len(mismatches)} field mismatches, {files_missing} YAML files missing")
    if mismatches:
        print("\n--- mismatches (decoder or load-order bug in one of the two tools) ---")
        for m in mismatches[:80]:
            print("  " + m)
        if len(mismatches) > 80:
            print(f"  … and {len(mismatches) - 80} more")
        sys.exit(1)
    print("PASS — the two independent decoders agree on every present field")


if __name__ == "__main__":
    main()
