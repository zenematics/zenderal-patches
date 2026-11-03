"""Generate the Dark Valley Sun Fix plugin YAML -- never hand-edit its Weathers/.

Player report (2026-10-31, GreaseLord): in Dark Valley, looking up filled the screen with white sun rays.
Enderal 2.1 keeps the valley sunless: the four weathers only its region (Jonas/Dark Valley 0023A3, plus its
HerzlandNebel sub-region) uses ship a black SunColor, a black SunGlareColor and no SunGlare. The Weathers
of Enderal (Enderal Weather - HDR.esp, their last overrider in the Ultra load order, binary scan
2026-10-31) gives all four a visible sun (#698B96-#BBCBD8 by day, glare 0.39-0.47) and thinner clouds, so
Steamin ENB's sun rays (EnableSunRays, multiplier 1.0 by day) bloom off it in the near-black valley.

This copies each record verbatim from TWoE and puts back only Enderal's sun:
  * SunColor and SunGlareColor blocks replaced by Enderal 2.1's (FS's record; black, except 10A242's dim
    #405355 sunset sun, kept as Enderal ships it).
  * SunGlare removed (= 0, as in Enderal).
Clouds, fog, lighting, precipitation and sounds stay TWoE's. Re-serialize TWoE into reference/mods/TWoE
and re-check the winners before re-running.
"""
import os
import re
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
TWOE = os.path.join(ROOT, "reference", "mods", "TWoE", "Weathers")
BASE = os.path.join(ROOT, "reference", "base-2.1.4.4", "EnderalFS", "Weathers")
OUT = os.path.join(ROOT, "src", "DarkValleySunFix", "DarkValleySunFixESP", "Weathers")
FILES = [
    "SkyrimFog_HerzlandNebel - 048085_Skyrim.esm.yaml",
    "SkyrimStormRain_DarkValley - 048087_Skyrim.esm.yaml",
    "SkyrimFogFF - 10A23E_Skyrim.esm.yaml",
    "SkyrimOvercastRainTU - 10A242_Skyrim.esm.yaml",
]
BLACK = "'#00000000'"


def block(name):
    return re.compile(r"^" + name + r":\r?\n(?:  [^\r\n]*\r?\n){4}", re.M)


GLARE = re.compile(r"^SunGlare: [^\r\n]*\r?\n", re.M)


def read(path):
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


if os.path.isdir(OUT):
    shutil.rmtree(OUT)
os.makedirs(OUT)
for name in FILES:
    text, base = read(os.path.join(TWOE, name)), read(os.path.join(BASE, name))
    if GLARE.search(base):
        raise SystemExit(f"{name}: Enderal's record has a SunGlare; recheck")
    for field in ("SunColor", "SunGlareColor"):
        want = block(field).search(base)
        if not want or "  Day: " + BLACK not in want.group(0):
            raise SystemExit(f"{name}: Enderal's {field} is not black by day")
        text, n = block(field).subn(want.group(0).replace("\\", "\\\\"), text)
        if n != 1:
            raise SystemExit(f"{name}: {n} {field} blocks in TWoE's record")
    text, n = GLARE.subn("", text)
    if n != 1:
        raise SystemExit(f"{name}: {n} SunGlare lines in TWoE's record, expected 1")
    with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="") as f:
        f.write(text)
    print("sunless:", name)
print(f"wrote {len(FILES)} weathers to {OUT}")
