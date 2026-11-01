r"""Would EnderalSE.dll 2.1's "OUTDATED MOD: Levelsystem" popup fire? Scans an MO2 profile for its 3 triggers.

Triggers (fs_src.zip, Util.h CheckIncompatibleMods): scripts/_00e_game_skillmenusc.pex or
scripts/_00e_questfunctions.pex present (loose or in any BSA), or any plugin defining QUST 010AA2:Skyrim.esm.

Usage: python 04-check-levelsystem-triggers.py [--modlist E:\Zenderal] [--profile Ultra] [mod names to treat as enabled ...]
Positive control: pass "KataPUMB New Affinities" (the original) -- it must report its BSA script and its quest.
"""
import argparse
import os
import re
import struct
import sys

BAD = {"scripts\\_00e_game_skillmenusc.pex", "scripts\\_00e_questfunctions.pex"}


def bsa_names(p):
    f = open(p, "rb")
    magic, ver, off, flags, nfold, nfile, lfold, lfile, _ = struct.unpack("<4sIIIIIIIH", f.read(34))
    if magic != b"BSA\0":
        return []
    f.seek(off)
    rs = 24 if ver == 105 else 16
    counts = [struct.unpack("<QI", f.read(rs)[:12])[1] for _ in range(nfold)]
    dirs = []
    for c in counts:
        d = f.read(f.read(1)[0])[:-1].decode("cp1252")
        f.read(16 * c)
        dirs += [d] * c
    names = f.read(lfile).split(b"\0")
    return [(dirs[i] + "\\" + names[i].decode("cp1252")).lower() for i in range(len(dirs))]


def masters(b):
    hsz = struct.unpack_from("<I", b, 4)[0]
    hdr, ms, i = b[24:24 + hsz], [], 0
    while i < len(hdr):
        t, s = hdr[i:i + 4], struct.unpack_from("<H", hdr, i + 4)[0]
        if t == b"MAST":
            ms.append(hdr[i + 6:i + 6 + s - 1].decode("cp1252"))
        i += 6 + s
    return ms


ap = argparse.ArgumentParser()
ap.add_argument("--modlist", default=r"E:\Zenderal")
ap.add_argument("--profile", default="Ultra")
ap.add_argument("extra", nargs="*")
a = ap.parse_args()
mods = []
for l in open(os.path.join(a.modlist, "profiles", a.profile, "modlist.txt"), encoding="utf-8"):
    l = l.rstrip("\r\n")
    if l.startswith("+") or (l.startswith("-") and l[1:] in a.extra):
        mods.append(l[1:])
mods += [e for e in a.extra if e not in mods]

hits = []
dirs = [(m, os.path.join(a.modlist, "mods", m)) for m in mods] + [("Stock Game", os.path.join(a.modlist, "Stock Game", "Data"))]
for m, base in dirs:
    if not os.path.isdir(base):
        continue
    for f in os.listdir(base):
        p = os.path.join(base, f)
        if f.lower().endswith(".bsa"):
            hits += [f"BSA {m}/{f}: {n}" for n in bsa_names(p) if n in BAD]
        elif f.lower().endswith((".esp", ".esm", ".esl")) and m != "Stock Game":
            b = open(p, "rb").read()
            ms = masters(b)
            if "Skyrim.esm" in ms:
                fid = struct.pack("<I", (ms.index("Skyrim.esm") << 24) | 0x010AA2)
                if any(b[x.start() - 12:x.start() - 8] == b"QUST" for x in re.finditer(re.escape(fid), b)):
                    hits.append(f"QUST 010AA2 in {m}/{f}")
    sdir = next((os.path.join(base, d) for d in os.listdir(base) if d.lower() == "scripts"), None)
    if sdir:
        hits += [f"LOOSE {m}: scripts\\{f}" for f in os.listdir(sdir) if "scripts\\" + f.lower() in BAD]
print("\n".join(hits) if hits else "no Levelsystem trigger in the enabled set")
sys.exit(1 if hits else 0)
