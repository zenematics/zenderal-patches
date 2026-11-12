r"""Generate the Malphas Fixes Merge plugin YAML -- never hand-edit its Npcs/.

Player report (2026-11-12): the Purge Calia (_00E_MC_Calia_Purge 14BE90) had a black face. Malphas' Blessing gives
her its own face file but keeps Enderal's Purge head parts on her record. NAUT1CAY's "Malphas' Blessing - Fixes" 1.5
(Enderal Nexus 822, plain-plugin version) fixes her and 16 other NPCs (head parts, names with accents, Yuslan's
beard, Tharael, Daddy...).

That plugin masters only Malphas' Blessing, so each of its records is Malphas' (or the base game's) record plus its
fixes. On NPCs another plugin edits after Malphas (EGO, MB - EGO, MB - Unique Aeterna), loading it would undo those
plugins' changes. For each such NPC this writes the record that currently wins without the Fixes plugin, with only
the top-level fields the Fixes plugin changes from its own base replaced by the Fixes plugin's blocks. NPCs no other
plugin edits after Malphas need nothing here: the Fixes plugin wins them as it is.

Base of a Fixes record = Malphas' record if Malphas overrides it, else the FS record, else Skyrim.esm's.
The current winner comes from a binary scan of the Ultra load order (plugins.txt), skipping the Fixes plugin and this
plugin. Re-serialize into reference/mods/ before re-running: MBFixes, MalphasBlessing, MBEGO, MBUniqueAeterna, and EGO
(reference/mods/EGO - Enderal Gameplay Overhaul).
"""
import os
import re
import struct
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
REF = os.path.join(ROOT, "reference")
OUT = os.path.join(ROOT, "src", "MalphasFixesMerge", "MalphasFixesMergeESP")
MO2 = r"E:\Zenderal"
FIXES = "Malphas' Blessing - Fixes.esp"
SELF = "Zenderal - Malphas Fixes Merge.esp"
MB = "Malphas' Blessing - Enderal.esp"
TREES = {
    "Skyrim.esm": os.path.join(REF, "base", "Skyrim"),
    "Enderal - Forgotten Stories.esm": os.path.join(REF, "base", "EnderalFS"),
    MB: os.path.join(REF, "mods", "MalphasBlessing"),
    "MB - EGO.esp": os.path.join(REF, "mods", "MBEGO"),
    "MB - Unique Aeterna.esp": os.path.join(REF, "mods", "MBUniqueAeterna"),
    "Enderal SE - Gameplay Overhaul.esp": os.path.join(REF, "mods", "EGO - Enderal Gameplay Overhaul"),
    FIXES: os.path.join(REF, "mods", "MBFixes"),
}
BASE_MASTERS = ["Skyrim.esm", "Update.esm", "Enderal - Forgotten Stories.esm"]
# Bookkeeping, not content (a missing Version2 is only the file format the Fixes author saved with).
IGNORE = {"FormKey", "Version2", "FormVersion"}
KEY = re.compile(r"^([A-Za-z0-9]+):")
FK = re.compile(r"\b[0-9A-F]{6}:([^\r\n:]+?\.es[mpl])\b")


def npc_file(plugin, fk):
    d = os.path.join(TREES[plugin], "Npcs")
    hits = [f for f in os.listdir(d) if f.endswith(f" - {fk}.yaml")] if os.path.isdir(d) else []
    if len(hits) > 1:
        raise SystemExit(f"{plugin}: {len(hits)} files for {fk}")
    return os.path.join(d, hits[0]) if hits else None


def blocks(text):
    """Top-level YAML keys in order -> their lines (CRLF kept)."""
    out, order, k = {}, [], None
    for line in text.splitlines(keepends=True):
        m = KEY.match(line)
        if m:
            k = m.group(1)
            order.append(k)
            out[k] = [line]
        elif k:
            out[k].append(line)
    return order, out


def scan_chains(wanted):
    mods = [l[1:].strip() for l in open(os.path.join(MO2, "profiles", "Ultra", "modlist.txt"), encoding="utf-8") if l.startswith("+")]
    plugins = [l[1:].strip() for l in open(os.path.join(MO2, "profiles", "Ultra", "plugins.txt"), encoding="utf-8") if l.startswith("*")]
    order = BASE_MASTERS + [p for p in plugins if p not in (FIXES, SELF)]

    def find(p):
        for m in mods:
            f = os.path.join(MO2, "mods", m, p)
            if os.path.isfile(f):
                return f
        f = os.path.join(MO2, "Stock Game", "Data", p)
        return f if os.path.isfile(f) else None

    chain = {k: [] for k in wanted}
    for p in order:
        f = find(p)
        if not f:
            continue
        b = open(f, "rb").read()
        hs = struct.unpack_from("<I", b, 4)[0]
        hdr, ms, i = b[24:24 + hs], [], 0
        while i < len(hdr):
            t, s = hdr[i:i + 4], struct.unpack_from("<H", hdr, i + 4)[0]
            if t == b"MAST":
                ms.append(hdr[i + 6:i + 5 + s].decode("cp1252"))
            i += 6 + s
        pos = 24 + hs
        while pos + 24 <= len(b) and b[pos:pos + 4] == b"GRUP":
            gs = struct.unpack_from("<I", b, pos + 4)[0]
            if b[pos + 8:pos + 12] == b"NPC_":
                q = pos + 24
                while q < pos + gs:
                    sz, fid = struct.unpack_from("<I", b, q + 4)[0], struct.unpack_from("<I", b, q + 12)[0]
                    hi = fid >> 24
                    k = f"{fid & 0xFFFFFF:06X}_{ms[hi] if hi < len(ms) else p}"
                    if k in chain:
                        chain[k].append(p)
                    q += 24 + sz
            pos += gs
    return order, chain


fixes_dir = os.path.join(TREES[FIXES], "Npcs")
fks = sorted(re.search(r" - ([0-9A-F]{6}_.+)\.yaml$", f).group(1) for f in os.listdir(fixes_dir))
order, chain = scan_chains(fks)
for d in ("Npcs",):
    p = os.path.join(OUT, d)
    if os.path.isdir(p):
        for f in os.listdir(p):
            os.remove(os.path.join(p, f))
os.makedirs(os.path.join(OUT, "Npcs"), exist_ok=True)
used, written = set(), 0
for fk in fks:
    ch = chain[fk]
    base_plugin = MB if MB in ch else ("Enderal - Forgotten Stories.esm" if "Enderal - Forgotten Stories.esm" in ch else "Skyrim.esm")
    winner = ch[-1]
    if winner == base_plugin:
        print(f"{fk}: only {base_plugin} edits it before the Fixes plugin - nothing to merge")
        continue
    if winner not in TREES:
        raise SystemExit(f"{fk}: winner {winner} has no reference tree (chain {ch})")
    fx_order, fx = blocks(open(npc_file(FIXES, fk), encoding="utf-8", newline="").read())
    _, base = blocks(open(npc_file(base_plugin, fk), encoding="utf-8", newline="").read())
    win_path = npc_file(winner, fk)
    w_order, win = blocks(open(win_path, encoding="utf-8", newline="").read())
    changed = [k for k in dict.fromkeys(fx_order + list(base)) if fx.get(k) != base.get(k) and k not in IGNORE]
    if not changed:
        raise SystemExit(f"{fk}: the Fixes plugin changes nothing on {base_plugin}'s record")
    for k in changed:
        if k in fx:
            if k not in win:  # insert after the closest preceding key the winner has
                prev = [x for x in fx_order[:fx_order.index(k)] if x in win]
                w_order.insert(w_order.index(prev[-1]) + 1 if prev else len(w_order), k)
            win[k] = fx[k]
        elif k in win:
            w_order.remove(k)
            del win[k]
    text = "".join("".join(win[k]) for k in w_order)
    used |= set(FK.findall(text))
    with open(os.path.join(OUT, "Npcs", os.path.basename(win_path)), "w", encoding="utf-8", newline="") as f:
        f.write(text)
    written += 1
    print(f"{fk}: {winner}'s record + Fixes' {', '.join(changed)} (base {base_plugin})")

masters = [p for p in order if p in used or p in BASE_MASTERS]
missing = used - set(order)
if missing:
    raise SystemExit(f"references plugins outside the load order: {missing}")
rd = os.path.join(OUT, "RecordData.yaml")
head = ("SpriggitSource:\r\n  PackageName: Spriggit.Yaml.Skyrim\r\n  Version: 0.40\r\nModKey: " + SELF + "\r\n"
        "GameRelease: EnderalSE\r\nModHeader:\r\n  Flags:\r\n  - Small\r\n  Stats:\r\n    Version: 1.7\r\n"
        "  Author: Zenderal\r\n  Description: Malphas' Blessing - Fixes (NAUT1CAY) merged onto the NPCs EGO and Malphas'"
        " EGO patches edit, so their gameplay changes stay. Load after Malphas' Blessing - Fixes.\r\n  MasterReferences:\r\n")
head += "".join(f"  - Master: {m}\r\n    FileSize: 0\r\n" for m in masters) + "  INTV: 1\r\n"
open(rd, "w", encoding="utf-8", newline="").write(head)
meta = os.path.join(OUT, "spriggit-meta.json")
open(meta, "w", encoding="utf-8").write('{\n  "PackageName": "Spriggit.Yaml.Skyrim",\n  "Version": "0.40.0",\n'
                                       '  "Release": "EnderalSE",\n  "ModKey": "' + SELF + '"\n}\n')
print(f"{written} merged records; masters: {masters}")
