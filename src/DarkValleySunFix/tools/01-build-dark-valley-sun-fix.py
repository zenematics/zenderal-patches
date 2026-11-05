"""Generate the Dark Valley Sun Fix plugin YAML -- never hand-edit its Weathers/.

Player reports: GreaseLord (2026-10-31), white sun rays filling the screen looking up in Dark Valley;
Longinus (2026-11-04), "so bright when looking at the sky at a specific angle when raining" in Ark.
Enderal 2.1 ships its fog, rain, storm and snow weathers sunless: a black SunColor by day, or no SunGlare.
The Weathers of Enderal (Enderal Weather - HDR.esp, the last overrider of every weather below in the Ultra
load order, scans 2026-10-31 and 2026-11-05) gives them a visible sun and a glare (0.39-0.47), so the ENB
sun rays (Steamin, EnableSunRays) bloom off it under thin overcast and white out the screen.

Rule: a TWoE weather is restored when Enderal's record has a black day sun and TWoE's does not, or has no
SunGlare and TWoE's does. 2026-10-31 covered only Dark Valley's four (048085, 048087, 10A23E, 10A242);
2026-11-05 the rule covers every such weather (Ark rains on 021311 and 0C8220).

Each record is TWoE's verbatim with only Enderal's sun put back:
  * SunColor and SunGlareColor blocks replaced by Enderal 2.1's (FS's record, else Skyrim.esm's).
  * SunGlare set to Enderal's (removed when Enderal has none, = 0).
Clouds, fog, lighting, precipitation and sounds stay TWoE's. Re-serialize TWoE (the Hotfix copy, which
wins) into reference/mods/TWoE and re-check the winners before re-running.
"""
import glob
import os
import re
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
TWOE = os.path.join(ROOT, "reference", "mods", "TWoE", "Weathers")
BASES = [os.path.join(ROOT, "reference", "base-2.1.4.4", d, "Weathers") for d in ("EnderalFS", "Skyrim")]
OUT = os.path.join(ROOT, "src", "DarkValleySunFix", "DarkValleySunFixESP", "Weathers")
BLACK = "'#00000000'"
# The four the first build covered; the rule must still pick them.
DARK_VALLEY = {"048085", "048087", "10A23E", "10A242"}


def block(name):
    return re.compile(r"^" + name + r":\r?\n(?:  [^\r\n]*\r?\n){4}", re.M)


GLARE = re.compile(r"^SunGlare: ([^\r\n]*)\r?\n", re.M)


def read(path):
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def day_sun(text, name):
    m = block("SunColor").search(text)
    if not m:
        raise SystemExit(f"{name}: no SunColor block")
    d = re.search(r"  Day: (\S+)", m.group(0))
    return d.group(1)


def glare(text):
    m = GLARE.search(text)
    return float(m.group(1)) if m else 0.0


if os.path.isdir(OUT):
    shutil.rmtree(OUT)
os.makedirs(OUT)
picked = set()
for path in sorted(glob.glob(os.path.join(TWOE, "*.yaml"))):
    name = os.path.basename(path)
    base_path = next((os.path.join(b, name) for b in BASES if os.path.exists(os.path.join(b, name))), None)
    if not base_path:
        continue                                      # a weather TWoE adds itself: no Enderal sun to restore
    text, base = read(path), read(base_path)
    lost_black = day_sun(base, name) == BLACK and day_sun(text, name) != BLACK
    new_glare = glare(base) == 0.0 and glare(text) > 0.0
    if not (lost_black or new_glare):
        continue
    for field in ("SunColor", "SunGlareColor"):
        want = block(field).search(base)
        if not want:
            raise SystemExit(f"{name}: Enderal's record has no {field} block")
        text, n = block(field).subn(want.group(0).replace("\\", "\\\\"), text)
        if n != 1:
            raise SystemExit(f"{name}: {n} {field} blocks in TWoE's record")
    base_glare = GLARE.search(base)
    if base_glare:
        text, n = GLARE.subn(base_glare.group(0).replace("\\", "\\\\"), text)
        if n != 1:
            raise SystemExit(f"{name}: {n} SunGlare lines in TWoE's record, expected 1")
    else:
        text, n = GLARE.subn("", text)
        if n > 1:
            raise SystemExit(f"{name}: {n} SunGlare lines in TWoE's record")
    with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="") as f:
        f.write(text)
    picked.add(re.search(r" - ([0-9A-F]{6})_", name).group(1))
    print(f"sunless: {name}  (black day sun lost: {lost_black}, glare added: {new_glare})")
missing = DARK_VALLEY - picked
if missing:
    raise SystemExit(f"the rule no longer picks Dark Valley's {sorted(missing)}")
print(f"wrote {len(picked)} weathers to {OUT}")
