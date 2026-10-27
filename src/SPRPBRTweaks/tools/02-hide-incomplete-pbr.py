"""Hide SPR PBR's PBR colour maps that ship without a normal map (MO2 `.mohidden`).

SPR PBR (Enderal Nexus 1063) 1.0.0 ships 62 `textures/PBR/**/*.dds` colour maps with no `_n` beside them and no
`PBRNifPatcher` JSON, so PGPatcher never turns any mesh onto them. TexGen (DynDOLOD 3) does use them: when
`textures\\pbr\\<path>.dds` exists it takes the whole PBR set, and stops with "File not found ..._n.dds"
(first hit: `pyrean\\dwemetaltiles03pyr_n.dds`, 2026-10-26).

This renames each such file to `<name>.dds.mohidden` (MO2 hides it; undo by removing the suffix) after copying it to
the backup folder. It refuses to hide a file that any PG Patcher Output mesh points at through a `pbr\\` path.

Usage: python 02-hide-incomplete-pbr.py [<MO2 root>] [<backup dir>] [--dry-run]
       (defaults E:/Zenderal, E:/Zenderal-backups/2026-10-26-spr-pbr-incomplete)
"""
import glob
import os
import re
import shutil
import sys

args = [a for a in sys.argv[1:] if not a.startswith("--")]
DRY = "--dry-run" in sys.argv
MO2 = args[0] if len(args) > 0 else "E:/Zenderal"
BACKUP = args[1] if len(args) > 1 else "E:/Zenderal-backups/2026-10-26-spr-pbr-incomplete"
MOD = os.path.join(MO2, "mods", "SPR PBR - Architecture Dungeons Misc")
ROOT = os.path.join(MOD, "textures", "PBR")
SUFFIXES = ("_n", "_p", "_rmaos", "_s", "_g", "_cnr", "_f", "_m", "_e")


def norm(p):
    return p.lower().replace(os.sep, "/").replace("\\", "/")


files = {}
for r, _, fs in os.walk(ROOT):
    for f in fs:
        p = os.path.join(r, f)
        files[norm(os.path.relpath(p, ROOT))] = p
bases = [k[:-4] for k in files if k.endswith(".dds") and not k[:-4].endswith(SUFFIXES)]
incomplete = sorted(b for b in bases if b + "_n.dds" not in files)

used = set()
rx = re.compile(rb"pbr[\\/]([\x20-\x7e]{3,160}?)\.dds", re.I)
for nif in glob.glob(os.path.join(MO2, "mods", "PG Patcher Output", "meshes", "**", "*.nif"), recursive=True):
    for m in rx.finditer(open(nif, "rb").read()):
        used.add(norm(m.group(1).decode()))
clash = [b for b in incomplete if any(u == b or u.startswith(b + "_") for u in used)]
if clash:
    raise SystemExit("refusing: PG Patcher meshes use %s" % clash)

print("%d colour maps without a normal map; none used by PG Patcher Output" % len(incomplete))
done = 0
for b in incomplete:
    src = files[b + ".dds"]
    rel = os.path.relpath(src, MOD)
    print("  " + rel.replace(os.sep, "/"))
    if DRY:
        continue
    dst = os.path.join(BACKUP, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    os.rename(src, src + ".mohidden")
    done += 1
if not DRY:
    assert done == len(incomplete)
    print("hid %d, backups in %s" % (done, BACKUP))
