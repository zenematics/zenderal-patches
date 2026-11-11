"""Check zpairset's Nemesis cache sets the way Pandora's preview builds read them.

Pandora preview builds since 2c7dace (2026-10-14) read anim-set patches only through
NemesisCachePatcher (Pandora.Skyrim/Format/Nemesis/NemesisCachePatcher.cs). This is a line-for-line
port of the part of it that handles our files - ApplyAnimSets -> ApplyExistingSetProject ->
AddOrReplaceSet -> ReadSet (LineCursor, ReadCounted, ReadGrouped, ReadAttacks, the marker tests) -
run against Pandora's template. It asserts, for every set of every project:

- the human sets (DefaultMale, DefaultFemale) read back as the template set plus exactly our six
  clips appended, with triggers, conditions and attack entries unchanged (a matching file REPLACES
  the whole set in the preview, so anything else would change the game's sets);
- every other project's sets are untouched;
- the plain 5.0.0-beta lists are skipped by this reader (no markers), and the cache folders are
  skipped by 5.0.0-beta's reader (`ProjectManager.TryGetProject` is a plain name lookup, and no
  project is named `<X>Data~<X>`).

Run after 02-build-animset-patch.py.
usage: python 03-verify-cache-sets.py <Pandora>/Pandora_Engine/Skyrim/Template/animationsetdatasinglefile.txt <zpairset dir>
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("animset", os.path.join(HERE, "02-build-animset-patch.py"))
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)


# ---- the preview's reader ---------------------------------------------------------------------
def is_open(line):
    t = line.strip()
    return t.startswith("<!--") and "MOD_CODE" in t and "OPEN" in t


def is_close(line):
    t = line.strip()
    return t.startswith("<!--") and "CLOSE" in t and "MOD_CODE" not in t


def is_original(line):
    t = line.strip()
    return t.startswith("<!--") and "ORIGINAL" in t


def is_delete(line):
    return line.strip() == "//* delete this line *//"


class Cursor:
    def __init__(self, lines):
        self.lines, self.i = lines, 0

    @property
    def end(self):
        return self.i >= len(self.lines)

    def open(self):
        return not self.end and is_open(self.lines[self.i])

    def take(self):
        v = self.lines[self.i]
        self.i += 1
        return v

    def take_block(self):
        self.take()
        edited, original, in_orig = [], [], False
        while not self.end and not is_close(self.lines[self.i]):
            line = self.take()
            if is_original(line):
                in_orig = True
                continue
            if is_delete(line):
                continue
            (original if in_orig else edited).append(line)
        if not self.end and is_close(self.lines[self.i]):
            self.take()
        return edited, original


def read_counted(c):
    count, items, consumed = int(c.take()), [], 0
    while consumed < count or (not c.end and c.open()):
        if not c.end and c.open():
            e, o = c.take_block()
            items += e
            consumed += len(o)
            continue
        if consumed >= count or c.end:
            break
        items.append(c.take())
        consumed += 1
    return items


def read_grouped(c, width):
    count, items, consumed = int(c.take()), [], 0
    while consumed < count or (not c.end and c.open()):
        if not c.end and c.open():
            e, o = c.take_block()
            items += [tuple(e[k:k + width]) for k in range(0, len(e) - width + 1, width)]
            consumed += len(o) // width
            continue
        if consumed >= count or c.end:
            break
        items.append(tuple(c.take() for _ in range(width)))
        consumed += 1
    return items


def read_one_attack(c):
    trigger, flag, n = c.take(), int(c.take()), int(c.take())
    return (trigger, flag, tuple(c.take() for _ in range(n)))


def read_attacks(c):
    count, items, consumed = int(c.take()), [], 0
    while consumed < count or (not c.end and c.open()):
        if not c.end and c.open():
            e, o = c.take_block()
            ce = Cursor(e)
            while not ce.end:
                items.append(read_one_attack(ce))
            co, n = Cursor(o), 0
            while not co.end:
                read_one_attack(co)
                n += 1
            consumed += n
            continue
        if consumed >= count or c.end:
            break
        items.append(read_one_attack(c))
        consumed += 1
    return items


def read_set(lines):
    c = Cursor(lines)
    c.take()  # version
    triggers = read_counted(c)
    conditions = read_grouped(c, 3)
    attacks = read_attacks(c)
    infos = read_grouped(c, 3)
    return triggers, conditions, attacks, infos


def is_set_document(lines):
    for line in lines:
        if not line.strip() or is_open(line) or is_close(line) or is_original(line):
            continue
        t = line.strip()
        return len(t) > 1 and t[0] in "Vv" and t[1].isdigit()
    return False


def set_project_key(folder):
    parts = folder.split("~")
    return parts[-1] if len(parts) >= 2 else parts[0]


# ---- the check ----------------------------------------------------------------------------------
def template_sets(path):
    """{project key: {set name lower: (name, triggers, conditions, attacks, infos)}} for every project."""
    lines = [x.rstrip("\r") for x in open(path, encoding="ascii").read().split("\n")]
    c = Cursor(lines)
    paths = [c.take() for _ in range(int(c.take()))]
    out = {}
    for pj in paths:
        names = [c.take() for _ in range(int(c.take()))]
        key = os.path.splitext(pj.split("\\")[-1])[0]
        out[key] = {}
        for name in names:
            # the template has no markers, so the same reader parses it, set after set
            c.take()  # version
            t = read_counted(c)
            cd = read_grouped(c, 3)
            a = read_attacks(c)
            inf = read_grouped(c, 3)
            out[key][name.lower()] = (name, t, cd, a, inf)
    if any(x.strip() for x in lines[c.i:]):
        raise SystemExit("trailing data after the last project: template parse error")
    return out


def main():
    template, mod_dir = sys.argv[1], sys.argv[2]
    base = template_sets(template)
    want = [tuple(B.anim_info_lines()[k:k + 3]) for k in range(0, 18, 3)]
    root = os.path.join(mod_dir, "animationsetdatasinglefile")
    patched = {k: dict(v) for k, v in base.items()}
    skipped_plain = 0
    for folder in sorted(os.listdir(root)):
        d = os.path.join(root, folder)
        if not os.path.isdir(d) or folder == "$header$":
            continue
        key = set_project_key(folder)
        if key not in base:
            raise SystemExit(f"{folder}: project {key} is not in the template")
        if os.path.exists(os.path.join(d, "$header$.txt")):
            raise SystemExit(f"{folder}: has a $header$.txt (would replace the set list)")
        for fn in sorted(os.listdir(d)):
            if not fn.lower().endswith(".txt"):
                continue
            lines = [x.rstrip("\r") for x in open(os.path.join(d, fn), encoding="ascii").read().split("\n")]
            if lines and lines[-1] == "":
                lines.pop()
            if not any(is_open(x) or is_close(x) for x in lines):
                skipped_plain += 1        # 5.0.0-beta's list form: the preview skips it
                continue
            if "~" not in folder:
                raise SystemExit(f"{folder}/{fn}: a marked file outside a <X>Data~<X> folder")
            if not is_set_document(lines):
                raise SystemExit(f"{folder}/{fn}: not a set document")
            if fn.lower() not in base[key]:
                raise SystemExit(f"{folder}/{fn}: no such set in {key} (the preview would ADD a new set)")
            patched[key][fn.lower()] = (fn,) + read_set(lines)

    n = 0
    for key, sets in base.items():
        for low, (name, t, cd, a, inf) in sets.items():
            _, t2, cd2, a2, inf2 = patched[key][low]
            if (t2, cd2, a2) != (t, cd, a):
                raise SystemExit(f"{key}/{name}: triggers, conditions or attacks changed")
            if key in ("DefaultMale", "DefaultFemale"):
                if inf2 != inf + want:
                    raise SystemExit(f"{key}/{name}: infos are not the template's plus our six")
                n += 1
            elif inf2 != inf:
                raise SystemExit(f"{key}/{name}: a non-human set changed")
    if n != 748:
        raise SystemExit(f"{n} human sets patched, expected 748")
    print(f"ok: 748 human sets = template + 6 clips; {sum(len(v) for v in base.values()) - 748} other sets "
          f"untouched; {skipped_plain} plain 5.0.0-beta lists skipped by the preview reader")


if __name__ == "__main__":
    main()
