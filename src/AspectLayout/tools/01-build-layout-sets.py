"""Build the MO2 mod `Zenderal - Aspect Layout`: Vel'dun's three screen-shape HUD layouts in one mod, for
`_ZenAspectLayout.dll` to switch between at startup (no preset for the user to pick).

The three `Vel'dun Zenderal patches 16x9/21x9/32x9` mods share most files and differ in a handful (TrueHUD /
Casting Bar / Oxygen Meter / SkyUI / Compass Navigation settings, SkyHUD's compass, the loading screen, map and
main-menu art). This writes:

  * every file the three patches have identical copies of, at its real path (static, always active);
  * for every file that differs: one copy per layout under `SKSE/Plugins/ZenAspectLayout/<layout>/<path>`, plus a
    `manifest.txt` per layout, plus an initial active copy (the 16x9 one) at the real path. A layout that has no
    copy of a varying file gets the file that wins WITHOUT the aspect patches (the next enabled mod down, or the
    game's BSA); if nothing provides it, the manifest leaves it alone (`keep`), which only happens for art that only
    another layout's own meshes reference.

The DLL copies the chosen layout's files over the active ones when the detected layout changes.
Everything is generated from the user's install (Vel'dun's work, Bethesda/SureAI assets), so nothing here is
committed but this script.

Usage: python 01-build-layout-sets.py [<MO2 root>] [<profile>]      (defaults E:/Zenderal, Ultra)
"""
import hashlib
import os
import shutil
import struct
import sys

import lz4.frame

MO2 = sys.argv[1] if len(sys.argv) > 1 else "E:/Zenderal"
PROFILE = sys.argv[2] if len(sys.argv) > 2 else "Ultra"
LAYOUTS = {"16x9": "Vel'dun Zenderal patches 16x9", "21x9": "Vel'dun Zenderal patches 21x9", "32x9": "Vel'dun Zenderal patches 32x9"}
OUT_MOD = "Zenderal - Aspect Layout"
# never a fallback source: the aspect patches themselves, this mod, and the curator's own ultrawide mod
SKIP = set(LAYOUTS.values()) | {OUT_MOD, "Zen's Ultrawide - 3360x1440 - Do not use"}
SETS = os.path.join("SKSE", "Plugins", "ZenAspectLayout")


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def files_of(root):
    out = {}
    for r, _, fs in os.walk(root):
        for f in fs:
            if f.lower() == "meta.ini":
                continue
            p = os.path.join(r, f)
            out[os.path.relpath(p, root).replace(os.sep, "/").lower()] = (os.path.relpath(p, root).replace(os.sep, "/"), p)
    return out


def bsa_index(path):
    f = open(path, "rb")
    hdr = f.read(36)
    if hdr[:4] != b"BSA\0":
        return {}
    _, ver, _, aflags, nfold, _, _, lfile, _ = struct.unpack("<4sIIIIIIII", hdr)
    folders = [struct.unpack("<QIIQ", f.read(24)) for _ in range(nfold)]
    recs = []
    for _, cnt, _, _ in folders:
        n = f.read(1)[0]
        name = f.read(n)[:-1].decode("cp1252")
        for _ in range(cnt):
            _, size, off = struct.unpack("<QII", f.read(16))
            recs.append((name, size, off))
    names = f.read(lfile).split(b"\0")
    return {(folder + "/" + n.decode("cp1252")).replace("\\", "/").lower(): (path, size, off, aflags)
            for (folder, size, off), n in zip(recs, names)}


def bsa_read(entry):
    path, size, off, aflags = entry
    f = open(path, "rb")
    comp = bool(aflags & 4) ^ bool(size & 0x40000000)
    f.seek(off)
    data = f.read(size & 0x3FFFFFFF)
    if aflags & 0x100:
        data = data[1 + data[0]:]
    return lz4.frame.decompress(data[4:]) if comp else data


def main():
    prof = os.path.join(MO2, "profiles", PROFILE)
    enabled = [l[1:].rstrip("\r\n") for l in open(os.path.join(prof, "modlist.txt"), encoding="utf-8") if l.startswith("+")]
    sets = {k: files_of(os.path.join(MO2, "mods", m)) for k, m in LAYOUTS.items()}
    allpaths = set().union(*sets.values())
    common, varying = [], []
    for low in sorted(allpaths):
        hashes = {k: md5(s[low][1]) if low in s else None for k, s in sets.items()}
        (common if len(set(hashes.values())) == 1 else varying).append(low)
    print(f"{len(common)} identical files, {len(varying)} varying across the three layouts")

    # fallback for a layout without its own copy: next enabled mod down (loose), then the game's BSAs
    loose = {}
    for m in enabled:
        if m in SKIP:
            continue
        root = os.path.join(MO2, "mods", m)
        if not os.path.isdir(root):
            continue
        for low in varying:
            if low in loose:
                continue
            for cand in (low,):
                p = os.path.join(root, *cand.split("/"))
                if os.path.isfile(p):
                    loose[low] = (m, p)
    bsa = {}
    data = os.path.join(MO2, "Stock Game", "Data")
    for b in sorted(os.listdir(data)):
        if b.lower().endswith(".bsa"):
            for k, v in bsa_index(os.path.join(data, b)).items():
                bsa.setdefault(k, v)

    out = os.path.join(MO2, "mods", OUT_MOD)
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out)
    for low in common:
        real, src = sets["16x9"][low]
        dst = os.path.join(out, real)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
    for k in LAYOUTS:
        lines = []
        for low in varying:
            real = next(s[low][0] for s in sets.values() if low in s)
            dst = os.path.join(out, SETS, k, real)
            if low in sets[k]:
                src, how = sets[k][low][1], "layout"
            elif low in loose:
                src, how = loose[low][1], "fallback " + loose[low][0]
            elif low in bsa:
                src, how = None, "fallback BSA " + os.path.basename(bsa[low][0])
            else:
                lines.append(f"keep\t{real}")
                print(f"  {k}: {real}: nothing provides it -> keep")
                continue
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if src:
                shutil.copy2(src, dst)
            else:
                open(dst, "wb").write(bsa_read(bsa[low]))
            lines.append(f"copy\t{real}")
            print(f"  {k}: {real}: {how}")
        open(os.path.join(out, SETS, k, "manifest.txt"), "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    # initial active copies = 16x9 (the DLL replaces them on first launch on any other shape)
    for low in varying:
        real = next(s[low][0] for s in sets.values() if low in s)
        src = os.path.join(out, SETS, "16x9", real)
        if os.path.isfile(src):
            dst = os.path.join(out, real)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
    with open(os.path.join(out, "meta.ini"), "w", encoding="utf-8", newline="\r\n") as f:
        f.write("[General]\ngameName=EnderalSE\nmodid=0\nversion=1.0.0\n"
                "comments=Generated by zenderal-patches src/AspectLayout/tools/01 from Vel'dun's 16x9/21x9/32x9 patches. "
                "_ZenAspectLayout.dll picks the layout at startup.\n")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
