r"""Build a cleaned copy of KataPUMB New Affinities that Enderal SE 2.1 accepts -- never hand-edit the copy.

EnderalSE.dll 2.1 (fs_src.zip, Util.h CheckIncompatibleMods) pops "OUTDATED MOD: Levelsystem" when any
plugin defines quest Levelsystem 010AA2 (removed in 2.1) or scripts/_00e_game_skillmenusc.pex exists.
KataPUMBAffinities.esp re-creates 010AA2 -- the whole 2.0 level-system quest with its config-menu,
quest-function and skill-menu scripts, which would run beside 2.1's DLL-driven level system -- and
KataPUMBAffinities.bsa ships Kata's 2.0 _00e_game_skillmenusc. Everything else Kata adds (perks, spells,
effects, messages, its own kata_*.pex) is independent and still needed.

This writes a NEW mod folder from the user's install; the original mod stays untouched (and disabled):
  * KataPUMBAffinities.esp, same filename (the EGO patch masters it), minus QUST 010AA2 and nothing else
  * Kata's scripts as loose files, minus _00e_game_skillmenusc.{pex,psc} (no BSA in the copy)
The copy is third-party content, generated on the user's machine, never committed. Kata's 24 affinities
then reach the game through src/KataAffinities21 (ported _00E_AffinityControl + its quest properties).

Usage: python 02-build-cleaned-kata.py [--modlist E:\Zenderal]
"""
import argparse
import os
import shutil
import struct
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC_MOD = "KataPUMB New Affinities"
OUT_MOD = "KataPUMB New Affinities - Enderal 2.1 (Zenderal cleaned)"
PLUGIN = "KataPUMBAffinities.esp"
BSA = "KataPUMBAffinities.bsa"
QUEST = "Levelsystem - 010AA2_Skyrim.esm.yaml"
DROP_SCRIPTS = {"_00e_game_skillmenusc.pex", "_00e_game_skillmenusc.psc"}


def spriggit(*args):
    ps = (". '{0}'; & (Assert-Tool $Tools.spriggitCli 'spriggitCli') {1}; exit $LASTEXITCODE"
          .format(os.path.join(ROOT, ".claude", "config", "tools.ps1"), " ".join(args)))
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0 or "Finished" not in r.stdout:
        sys.exit(f"spriggit {args[0]} failed:\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}")


def bsa_files(path):
    """(relative path, bytes) for every file in an uncompressed SSE (v105) BSA."""
    f = open(path, "rb")
    magic, ver, off, flags, nfold, nfile, lfold, lfile, _ = struct.unpack("<4sIIIIIIIH", f.read(34))
    if magic != b"BSA\0" or ver != 105:
        sys.exit(f"{path}: not an SSE BSA")
    f.seek(off)
    counts = [struct.unpack("<QI", f.read(24)[:12])[1] for _ in range(nfold)]
    entries = []
    for c in counts:
        d = f.read(f.read(1)[0])[:-1].decode("cp1252")
        for _ in range(c):
            _, size, foff = struct.unpack("<QII", f.read(16))
            entries.append((d, size, foff))
    names = f.read(lfile).split(b"\0")
    for i, (d, size, foff) in enumerate(entries):
        if bool(flags & 0x4) ^ bool(size & 0x40000000):
            sys.exit(f"{path}: compressed entry {names[i]!r}; this generator only handles uncompressed archives")
        f.seek(foff)
        size &= 0x3FFFFFFF
        if flags & 0x100:
            n = f.read(1)[0]
            f.read(n)
            size -= n + 1
        yield os.path.join(d, names[i].decode("cp1252")), f.read(size)


ap = argparse.ArgumentParser()
ap.add_argument("--modlist", default=r"E:\Zenderal")
a = ap.parse_args()
src = os.path.join(a.modlist, "mods", SRC_MOD)
out = os.path.join(a.modlist, "mods", OUT_MOD)

with tempfile.TemporaryDirectory(dir=os.path.join(ROOT, "src", "KataAffinities21", "build")) as tmp:
    yaml_dir = os.path.join(tmp, "yaml")
    spriggit("serialize", f"--InputPath '{os.path.join(src, PLUGIN)}'", f"--OutputPath '{yaml_dir}'",
             "--GameRelease EnderalSE", "--PackageName Spriggit.Yaml.Skyrim", "--PackageVersion 0.40.0")
    quests = os.listdir(os.path.join(yaml_dir, "Quests"))
    if quests != [QUEST]:
        sys.exit(f"expected exactly {QUEST} under Quests/, found {quests}")
    shutil.rmtree(os.path.join(yaml_dir, "Quests"))
    for dp, _, fn in os.walk(yaml_dir):
        for n in fn:
            if "010AA2" in open(os.path.join(dp, n), encoding="utf-8").read():
                sys.exit(f"{n} still references 010AA2")
    built = os.path.join(tmp, PLUGIN)
    spriggit("deserialize", f"--InputPath '{yaml_dir}'", f"--OutputPath '{built}'")

    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out)
    shutil.copy2(built, os.path.join(out, PLUGIN))

kept = dropped = 0
for rel, data in bsa_files(os.path.join(src, BSA)):
    if os.path.basename(rel).lower() in DROP_SCRIPTS:
        dropped += 1
        continue
    p = os.path.join(out, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "wb").write(data)
    kept += 1
if dropped != 2:
    sys.exit(f"expected to drop 2 skill-menu files, dropped {dropped}")

with open(os.path.join(out, "meta.ini"), "w", encoding="utf-8", newline="\r\n") as f:
    f.write("[General]\ngameName=EnderalSE\nmodid=0\nversion=2.1.0.0-zenderal\ninstalled=true\n"
            "comments=Generated by zenderal-patches src/KataAffinities21/tools/02-build-cleaned-kata.py\n")
print(f"wrote {OUT_MOD}: {PLUGIN} without QUST 010AA2, {kept} loose scripts ({dropped} skill-menu files dropped)")
