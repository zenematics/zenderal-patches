"""Generate the No Lightning Flash plugin YAML -- never hand-edit its Weathers/.

Curator's taste (2026-10-20). During a lightning strike the engine moves the directional (sun) light to
the strike and tints it with the weather's LightningColor, then fades back -- so every strike relights the
whole scene from a new angle and the "sun" visibly jumps (recorded on the intro beach, 4 strikes in 7.7 s).
Diverse Weather - True Storms.esp sets LightningColor white on 13 rain/storm weathers; base Enderal had
black (no flash) on 8 of them and pale #DBDCEE/#D5FFFF on its 5 storm weathers.

This copies each of the 13 records verbatim from Diverse Weather - True Storms.esp (the last overrider of
all 13 in the Ultra load order, binary scan 2026-10-20) and turns their lightning off:
  * ThunderLightningBeginFadeIn / ThunderLightningEndFadeOut removed (= 0). This is the actual switch:
    across all 204 Enderal 2.1 weathers, every weather with lightning has an EndFadeOut of ~0.85-1 and
    every weather without it has none. True Storms added EndFadeOut 0.50 to 8 weathers base Enderal ships
    without lightning (incl. the intro beach's 021311) -- blacking the colour alone left the strikes on,
    still re-aiming the sun (v1.0.0, still flickered in game).
  * LightningColor black, in case a strike still fires.
Precipitation, rain sounds and colours stay True Storms'. Re-serialize the source into
reference/mods/DiverseWeatherTrueStorms and re-check the winners before re-running.
"""
import glob
import os
import re
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "reference", "mods", "DiverseWeatherTrueStorms", "Weathers")
OUT = os.path.join(ROOT, "src", "NoLightningFlash", "NoLightningFlashESP", "Weathers")
WHITE = "LightningColor: '#00FFFFFF'"
BLACK = "LightningColor: '#00000000'"
EXPECTED = 13
FADE_OUT = re.compile(r"^ThunderLightningEndFadeOut: [^\r\n]*\r?\n", re.M)
FADE_IN = re.compile(r"^ThunderLightningBeginFadeIn: [^\r\n]*\r?\n", re.M)

if os.path.isdir(OUT):
    shutil.rmtree(OUT)
os.makedirs(OUT)
n = 0
for p in sorted(glob.glob(os.path.join(SRC, "*.yaml"))):
    with open(p, encoding="utf-8", newline="") as f:
        text = f.read()
    hits = len(re.findall(re.escape(WHITE) + r"(?=\r?$)", text, re.M))
    if hits == 0:
        continue
    if hits != 1:
        raise SystemExit(f"{os.path.basename(p)}: {hits} LightningColor lines")
    text, n_out = FADE_OUT.subn("", text.replace(WHITE, BLACK))
    if n_out != 1:
        raise SystemExit(f"{os.path.basename(p)}: {n_out} ThunderLightningEndFadeOut lines, expected 1")
    text = FADE_IN.sub("", text)
    with open(os.path.join(OUT, os.path.basename(p)), "w", encoding="utf-8", newline="") as f:
        f.write(text)
    n += 1
    print("black lightning:", os.path.basename(p))
if n != EXPECTED:
    raise SystemExit(f"expected {EXPECTED} weathers, wrote {n}")
print(f"wrote {n} weathers to {OUT}")
