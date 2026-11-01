"""Zenderal - Stances No Icon: hides the stance icon Stances - Dynamic Weapon Movesets SE floats over the
player's head. Each stance applies a *_icon_mgef whose HitEffectArt is an ART0 using Stances\\<stance>_icon.nif;
the override is the Stances record verbatim minus that one line. The stance perks, switch effects and the
coloured body shaders (*_shader_mgef) are untouched.

Usage: python 01-build-stances-no-icon.py <serialized Stances plugin folder>
(e.g. serialize mods/Stances - Dynamic Animation Sets/Stances - Dynamic Weapon Movesets SE.esp with Spriggit 0.40.0)."""
import os
import re
import shutil
import sys

SRC = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "StancesNoIconESP")
ICON_MGEFS = {  # FormID -> its ART0
    "06AD25": "06AD22",  # high
    "06AD26": "06AD23",  # mid
    "06AD27": "06AD24",  # low
    "07F13A": "07F139",  # neutral
}
PLUGIN = "Stances - Dynamic Weapon Movesets SE.esp"

mg_out = os.path.join(OUT, "MagicEffects")
if os.path.isdir(mg_out):
    shutil.rmtree(mg_out)
os.makedirs(mg_out)
done = 0
for f in os.listdir(os.path.join(SRC, "MagicEffects")):
    m = re.search(r" - ([0-9A-F]{6})_", f)
    fid = m.group(1) if m else None
    if fid not in ICON_MGEFS:
        continue
    raw = open(os.path.join(SRC, "MagicEffects", f), "rb").read()
    nl = b"\r\n" if b"\r\n" in raw else b"\n"
    lines = raw.split(nl)
    art = ("HitEffectArt: %s:%s" % (ICON_MGEFS[fid], PLUGIN)).encode()
    assert lines.count(art) == 1, (f, "HitEffectArt line not found exactly once")
    lines.remove(art)
    open(os.path.join(mg_out, f), "wb").write(nl.join(lines))
    done += 1
    print("override", f)
assert done == len(ICON_MGEFS), done
print("wrote", done, "overrides")
