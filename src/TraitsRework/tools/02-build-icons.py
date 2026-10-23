"""Convert the trait artwork into the menu's DDS images.

Biggie's Traits.dll built each row's image path as "TraitPics/" + the trait SPEL's EditorID + ".dds" (strings in
Traits.dll), and the B612 menu loadMovie()s it from Interface/ into ItemPic_mc at native size. Traits_Utils.psc
passes the same path, so the output is Interface/TraitPics/<EditorID>.dds: ZEN_TR_<Stem>Ab for our 16 traits,
ZenTraits_<Stem>Ab for Zen Traits' 9.

Input:  outputs/trait-icons/NN-<Trait-Name>.png (the curator's artwork; not committed, ~2.5 MB each)
Output: src/TraitsRework/Interface/TraitPics/*.dds - 932x760 BC1 (DXT1), no mips. COMMITTED: CI can't run texconv.

The menu draws images at native size (a 256 px test icon drew ~93 px in a 1741-wide screenshot); 932x760 fills
the details pane the curator marked (2026-10-21) with a margin above the description. The square art is
center-cropped to that aspect (~9% off top and bottom), never stretched.

Run from the repo root:  python src/TraitsRework/tools/02-build-icons.py
"""
import glob
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
SRC = os.path.join(REPO, "outputs", "trait-icons")
OUT = os.path.join(HERE, "..", "Interface", "TraitPics")
WIDTH, HEIGHT = 932, 760   # multiples of 4 for BC1


def texconv_path():
    cfg = json.load(open(os.path.join(REPO, ".claude", "config", "tools.json"), encoding="utf-8-sig"))
    path = f"{cfg['modlistRoot']}/Tools/EnderalSEEdit 4.1.5f/Edit Scripts/Texconvx64.exe"
    if not os.path.isfile(path):
        sys.exit(f"texconv not found: {path}")
    return path


def fit(im):
    """Center-crop to WIDTH:HEIGHT, then scale."""
    w, h = im.size
    if w / h > WIDTH / HEIGHT:
        cw = round(h * WIDTH / HEIGHT)
        im = im.crop(((w - cw) // 2, 0, (w - cw) // 2 + cw, h))
    else:
        ch = round(w * HEIGHT / WIDTH)
        im = im.crop((0, (h - ch) // 2, w, (h - ch) // 2 + ch))
    return im.resize((WIDTH, HEIGHT), Image.LANCZOS)


# Zen Traits' 9 (the abilities its Zen Traits_FLM.ini adds to Traits_AbilityList). Art stem -> SPEL EditorID.
ZEN_TRAITS = ["AeternaVeins", "ArcaneAddict", "Beacon", "CleansedSoul", "Lightborn", "NightFever",
              "PurifiedBlood", "RadiantSoul", "TwilightDisciple"]


def trait_editor_ids():
    """Art stem -> the SPEL EditorID the menu looks the image up by."""
    spec = importlib.util.spec_from_file_location("traits", os.path.join(HERE, "01-build-traits.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    ids = {t[0]: f"ZEN_TR_{t[0]}Ab" for t in mod.TRAITS}
    ids.update({stem: f"ZenTraits_{stem}Ab" for stem in ZEN_TRAITS})
    return ids


def main():
    editor_ids = trait_editor_ids()
    stems = list(editor_ids)
    files = sorted(glob.glob(os.path.join(SRC, "*.png")))
    by_stem = {}
    for f in files:
        # only NN-<Trait-Name>.png is trait art; the folder also holds other art (e.g. ZP_Prophecy_*.png)
        m = re.match(r"\d+-(.+)\.png$", os.path.basename(f))
        if m:
            by_stem[m.group(1).replace("-", "")] = f
    missing = [s for s in stems if s not in by_stem]
    extra = [s for s in by_stem if s not in stems]
    if missing or extra:
        sys.exit(f"icon/trait mismatch - missing: {missing}, unknown: {extra}")

    texconv = texconv_path()
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(OUT)
    with tempfile.TemporaryDirectory() as tmp:
        for stem in stems:
            png = os.path.join(tmp, f"{editor_ids[stem]}.png")
            fit(Image.open(by_stem[stem]).convert("RGB")).save(png)
            r = subprocess.run([texconv, "-nologo", "-y", "-f", "BC1_UNORM", "-m", "1", "-o", OUT, png],
                               capture_output=True, text=True)
            if r.returncode != 0:
                sys.exit(f"texconv failed on {png}:\n{r.stdout}{r.stderr}")
            # this texconv has no -l and writes ".DDS"; the menu asks for ".dds"
            os.replace(os.path.join(OUT, f"{editor_ids[stem]}.DDS"), os.path.join(OUT, f"{editor_ids[stem]}.dds"))
    made = sorted(os.listdir(OUT))
    assert len(made) == len(stems) == 27 and all(x.endswith(".dds") for x in made), made
    print(f"{len(made)} icons -> {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
