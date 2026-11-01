r"""Build a cleaned copy of Mihail's Iron Golem plugin that Enderal SE can load safely -- never hand-edit the copy.

mihailirongolem.esp (Iron Golem - Mihail Monsters and Animals, Skyrim SE mod 29228) places its golems in Skyrim
locations: LabyrinthianWorld04 021EDB + its cell 021EEA, the interior Labyrinthian03 091872, Dawnguard's
DLC1HunterHQWorld (4 cells) and Dragonborn's DLC2TempleofMiraak02. None exist in Enderal, and two of those
FormIDs are DIFFERENT record types in Enderal (021EDB and 091872 are placed references), so the plugin redefines
Enderal forms as a worldspace/cell -- DynDOLOD "Record [REFR:00021EDB] ... is being overridden by record
[WRLD:00021EDB]", and a real CTD risk. It has no leveled-list distribution, so in Enderal those placements are its
only use of the golem -- but Steel Warden Replacer - EGO.esp masters it for the golem's race, skin, weapon, voice,
AI package and combat style.

This writes a NEW mod folder from the user's install; the original mod stays enabled for its meshes, textures,
sounds and scripts:
  * mihailirongolem.esp, same filename (Steel Warden Replacer - EGO masters it), minus every Worldspaces/ and
    Cells/ record (the Skyrim placements) and nothing else.
The new folder must sit ABOVE the original in MO2's mod list so its .esp wins the file conflict. The copy is
third-party content, generated on the user's machine, never committed. Its remaining references to missing
Skyrim/DLC forms are handled by src/UnresolvedRefsCleanup (re-run its tools after building this).

Usage: python 01-build-cleaned-golem.py [--modlist E:\Zenderal]
"""
import argparse
import os
import shutil
import struct
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC_MOD = "Iron Golem -Mihail Monsters and Animals (SE-AE)"
OUT_MOD = "Iron Golem - Enderal cleaned plugin (Zenderal)"
PLUGIN = "mihailirongolem.esp"
DROP = ("Worldspaces", "Cells")
EXPECTED_DROPPED = 9  # 7 worldspace/exterior-cell records + 2 interior cells, as of mod 4.0.0


def spriggit(*args):
    ps = (". '{0}'; & (Assert-Tool $Tools.spriggitCli 'spriggitCli') {1}; exit $LASTEXITCODE"
          .format(os.path.join(ROOT, ".claude", "config", "tools.ps1"), " ".join(args)))
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0 or "Finished" not in r.stdout:
        sys.exit(f"spriggit {args[0]} failed:\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}")


def header(path):
    b = open(path, "rb").read(64)
    return struct.unpack_from("<f", b, 30)[0], struct.unpack_from("<I", b, 8)[0]


ap = argparse.ArgumentParser()
ap.add_argument("--modlist", default=r"E:\Zenderal")
a = ap.parse_args()
src = os.path.join(a.modlist, "mods", SRC_MOD, PLUGIN)
out_dir = os.path.join(a.modlist, "mods", OUT_MOD)
tmp = tempfile.mkdtemp(prefix="golem_")
yaml = os.path.join(tmp, "yaml")
spriggit("serialize", "--InputPath", f"'{src}'", "--OutputPath", f"'{yaml}'", "--GameRelease", "EnderalSE",
         "--PackageName", "Spriggit.Yaml.Skyrim", "--PackageVersion", "0.40.0")
dropped = 0
for d in DROP:
    p = os.path.join(yaml, d)
    if os.path.isdir(p):
        dropped += sum(1 for dp, _, fn in os.walk(p) for n in fn if n == "RecordData.yaml")
        shutil.rmtree(p)
if dropped != EXPECTED_DROPPED:
    sys.exit(f"expected to drop {EXPECTED_DROPPED} cell/worldspace records, found {dropped} -- mod changed? re-check")
kept = sum(1 for dp, _, fn in os.walk(yaml) for n in fn if n.endswith(".yaml") and not n.startswith("Group")) - 1
os.makedirs(out_dir, exist_ok=True)
built = os.path.join(out_dir, PLUGIN)
spriggit("deserialize", "--InputPath", f"'{yaml}'", "--OutputPath", f"'{built}'")
v0, f0 = header(src)
v1, f1 = header(built)
if (round(v0, 3), f0 & 0x200) != (round(v1, 3), f1 & 0x200):
    sys.exit(f"header changed: {v0:.2f}/{f0:#x} -> {v1:.2f}/{f1:#x}")
meta = os.path.join(out_dir, "meta.ini")
if not os.path.exists(meta):
    open(meta, "w", encoding="utf-8", newline="\r\n").write("[General]\nmodid=0\nversion=4.0.0\ninstalled=true\n")
shutil.rmtree(tmp)
print(f"dropped {dropped} worldspace/cell records, kept {kept} records -> {built} (HEDR {v1:.2f}, flags {f1:#x})")
