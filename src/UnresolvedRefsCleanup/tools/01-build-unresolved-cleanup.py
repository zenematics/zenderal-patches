"""Generate the Unresolved References Cleanup plugin YAML -- never hand-edit its record folders.

DynDOLOD/xEdit stop on "Unresolved FormID" errors. A load-order scan (scratch unresolved_winners.py over every
enabled plugin serialized with Spriggit 0.40.0) found ~530 references in ~220 WINNING records that point at forms
no loaded plugin defines -- almost all vanilla-Skyrim/DLC forms left in mods ported from Skyrim (Apocalypse,
Dynamic Impact, Deflection, AOS, Taberu, ...). In game such references already resolve to None; this removes them
so the load order is resolvable, changing as little as possible:
  * bare list entry ("- XXXXXX:File", keywords / form-list items)       -> entry dropped
  * reference inside a list item (container item, leveled entry, impact,
    alternate texture, perk, faction, effect, relation, recipe component) -> that item dropped
  * scalar field of the record                                           -> field cleared
  * placed object whose Base is missing                                   -> Base = XMarker 000034 (invisible, valid)
A list item is never a record ("- MutagenObjectType"), so no record is ever dropped. Cells: only the cell
header (if it carries a bad ref) and the affected placed objects are written, with the Cells/ group scaffolding.
Each record is otherwise its winner verbatim, so the plugin must load LAST.

Usage: 01-build-unresolved-cleanup.py <serializedRoot> <unresolved.json>
"""
import collections
import json
import os
import re
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OUT = os.path.join(ROOT, "src", "UnresolvedRefsCleanup", "UnresolvedRefsCleanupESP")
SER, JS = sys.argv[1], sys.argv[2]
XMARKER = "000034:Skyrim.esm"
SECTIONS = re.compile(r"^(Temporary|Persistent|NavigationMeshes|Landscape|SubCells|TopCell|MajorFlags):")

bad = json.load(open(JS, encoding="utf-8"))
by_file = collections.defaultdict(list)
for b in bad:
    by_file[b["file"]].append(b)


def indent(l):
    return len(l) - len(l.lstrip(" "))


def block_end(lines, i):
    """End (exclusive) of the list item / mapping starting at line i."""
    ind = indent(lines[i])
    j = i + 1
    while j < len(lines) and (lines[j].strip() == "" or indent(lines[j]) > ind):
        j += 1
    return j


def plan(lines, ln, field):
    """Return ('del', a, b) | ('set', ln, newline) for an unresolved ref on line ln."""
    l = lines[ln]
    s = l.strip()
    if re.fullmatch(r"- [0-9A-F]{6}:[^:]+\.es[mpl]", s):
        return ("del", ln, ln + 1)
    if field == "Base":
        return ("set", ln, re.sub(r"[0-9A-F]{6}:.+$", XMARKER, l))
    if s.startswith("- ") and not s.startswith("- MutagenObjectType"):
        return ("del", ln, block_end(lines, ln))  # the ref is the item's own first line: drop the whole item
    ind = indent(l) - (2 if s.startswith("- ") else 0)
    k = ln
    while k > 0:
        k -= 1
        if lines[k].strip() and indent(lines[k]) < ind and lines[k].lstrip().startswith("- "):
            break
        if lines[k].strip() and indent(lines[k]) < ind and not lines[k].lstrip().startswith("- ") and indent(lines[k]) == 0:
            k = -1
            break
    else:
        k = -1
    if k >= 0 and not lines[k].lstrip().startswith("- MutagenObjectType"):
        return ("del", k, block_end(lines, k))
    return ("del", ln, ln + 1) if not s.endswith(":") else ("del", ln, block_end(lines, ln))


def apply(lines, ops):
    dels = sorted({(a, b) for o, a, b in ops if o == "del"})
    sets = {a: b for o, a, b in ops if o == "set"}
    out, skip_until = [], -1
    merged = []
    for a, b in dels:
        if merged and a < merged[-1][1]:
            merged[-1] = (merged[-1][0], max(b, merged[-1][1]))
        else:
            merged.append((a, b))
    drop = set()
    for a, b in merged:
        drop.update(range(a, b))
    for i, l in enumerate(lines):
        if i in drop:
            continue
        out.append(sets.get(i, l))
    return drop_empty_keys(out)


def drop_empty_keys(lines):
    """Remove 'Key:' lines whose list/mapping became empty (Spriggit rejects an empty sequence)."""
    changed = True
    while changed:
        changed = False
        for i, l in enumerate(lines):
            m = re.match(r"^( *)(- )?[A-Za-z0-9_]+:$", l)
            if not m:
                continue
            ind = indent(l) + (2 if m.group(2) else 0)
            nxt = next((x for x in lines[i + 1:] if x.strip()), "")
            child = indent(nxt) > ind or (indent(nxt) == ind and nxt.lstrip().startswith("- ") and not m.group(2))
            if not child and not m.group(2):
                del lines[i]
                changed = True
                break
    return lines


def rel_out(path):
    parts = os.path.normpath(path).split(os.sep)
    i = parts.index("all")
    return os.path.join(OUT, *parts[i + 2:])


if os.path.isdir(OUT):
    for e in os.listdir(OUT):
        if e not in ("RecordData.yaml", "spriggit-meta.json"):
            shutil.rmtree(os.path.join(OUT, e))
stats = collections.Counter()
for path, items in by_file.items():
    text = open(path, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(nl)
    parts = os.path.normpath(path).split(os.sep)
    is_cell = "Cells" in parts or "Worldspaces" in parts
    if "Worldspaces" in parts:
        raise SystemExit(f"exterior cell edit not supported by this generator: {path}")
    ops = []
    for b in items:
        assert b["ref"].split(":")[0] in lines[b["line"]], (path, b)
        op = plan(lines, b["line"], b["field"])
        if op[0] == "del" and any(lines[x].lstrip().startswith("- MutagenObjectType") for x in range(op[1], op[2])):
            raise SystemExit(f"refusing to drop a record: {path}:{b['line']} {b}")
        ops.append(op)
        stats["set" if op[0] == "set" else ("entry" if op[2] - op[1] == 1 and lines[op[1]].lstrip().startswith("- ") else "item/field")] += 1
    new = apply(lines, ops)
    if is_cell:
        # keep the cell header + only placed objects that carried a bad ref
        bad_refs = {b["record"] for b in items}
        head = []
        for l in new:
            if SECTIONS.match(l):
                break
            head.append(l)
        body = []
        sect = None
        cur = None
        for l in new[len(head):]:
            m = SECTIONS.match(l)
            if m:
                sect = m.group(1)
                continue
            if sect in ("Temporary", "Persistent"):
                if l.startswith("- MutagenObjectType"):
                    cur = [l]
                    body.append((sect, cur))
                elif cur is not None:
                    cur.append(l)
        keep = collections.defaultdict(list)
        for sect, blk in body:
            fk = next((x.strip()[9:] for x in blk[:3] if x.strip().startswith("FormKey:")), None)
            if fk in bad_refs:
                keep[sect] += blk
        trailer = new[new.index("MajorFlags:"):] if "MajorFlags:" in new else []
        out = head[:]
        for sect in ("Persistent", "Temporary"):
            if keep[sect]:
                out += [sect + ":"] + keep[sect]
        out += trailer
        new = out
        # scaffolding
        cells_root = os.path.join(*parts[: parts.index("Cells") + 1])
        rel = parts[parts.index("Cells"):]
        for depth in range(1, len(rel) - 1):
            g = os.path.join(cells_root, *rel[1:depth], "GroupRecordData.yaml")
            if os.path.isfile(g):
                dst = os.path.join(OUT, *rel[:depth], "GroupRecordData.yaml")
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copyfile(g, dst)
    out_text = nl.join(new)
    for b in items:
        if b["ref"] in out_text and not (b["field"] == "Base"):
            raise SystemExit(f"still referenced after cleanup: {b}")
    dst = rel_out(path)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, "w", encoding="utf-8", newline="").write(out_text)
    stats["files"] += 1
print(dict(stats), "refs:", len(bad))
