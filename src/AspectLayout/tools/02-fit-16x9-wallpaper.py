"""Fit the list's main-menu wallpaper to the 16x9 layout's menu mesh. Run after 01-build-layout-sets.py.

Vel'dun's 16x9 patch has no main-menu meshes, so 01 gives the 16x9 set the fallback `logo.nif`/`logo01ae.nif`
from Vel'dun UI Enderal Default. Those meshes map the wallpaper texture as Vel'dun's own: a 4096x4096 square with
the picture in a 16:9 band across the full width (rows 614-2929) and black above and below. The list's wallpaper
is Classic Enderal Main Menu Background 4K: 4096x2048 with the picture in the right two thirds (Enderal's own
layout). Through Vel'dun's mesh only part of it showed, shifted right with black on the left (beta report,
2026-10-29, 1920x1080).

This writes the 16x9 set's `mainmenuwallpaper.dds` in Vel'dun's layout, filled with the Classic picture (cropped
to the band's aspect, centred). The 21x9 and 32x9 sets keep theirs: their meshes are Vel'dun's Zenderal patches,
made for the list's wallpaper.

Usage: python 02-fit-16x9-wallpaper.py [<MO2 root>]      (default E:/Zenderal)
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

MO2 = sys.argv[1] if len(sys.argv) > 1 else "E:/Zenderal"
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
REL = os.path.join("Textures", "interface", "Objects", "mainmenuwallpaper.dds")
SET16 = os.path.join(MO2, "mods", "Zenderal - Aspect Layout", "SKSE", "Plugins", "ZenAspectLayout", "16x9")
VELDUN = os.path.join(MO2, "mods", "Vel'dun UI Enderal Default", REL)
VELDUN_LOGO = os.path.join(MO2, "mods", "Vel'dun UI Enderal Default", "meshes", "interface", "logo", "logo.nif")


def texconv():
    tools = json.load(open(os.path.join(REPO, ".claude", "config", "tools.json"), encoding="utf-8-sig"))
    p = os.path.join(os.path.dirname(tools.get("xedit", "")), "Edit Scripts", "Texconvx64.exe")
    assert os.path.isfile(p), f"texconv not found next to tools.json xedit: {p}"
    return p


def bounds(a):
    """first/last row and column with picture (not near-black)"""
    lum = a.astype(int).sum(2)
    rows, cols = np.where(lum.max(1) > 40)[0], np.where(lum.max(0) > 40)[0]
    return rows[0], rows[-1] + 1, cols[0], cols[-1] + 1


def main():
    logo16 = os.path.join(SET16, "meshes", "interface", "logo", "logo.nif")
    if open(logo16, "rb").read() != open(VELDUN_LOGO, "rb").read():
        sys.exit("16x9 logo.nif is no longer Vel'dun UI Enderal Default's: check which wallpaper layout it maps first")
    src = os.path.join(SET16, REL)  # 01 put the list's winning wallpaper here
    pic = np.asarray(Image.open(src).convert("RGB"))
    ref = np.asarray(Image.open(VELDUN).convert("RGB"))
    t0, t1, l0, l1 = bounds(ref)  # Vel'dun's band
    assert (l0, l1) == (0, ref.shape[1]), f"Vel'dun's picture no longer spans the full width: cols {l0}-{l1}"
    s0, s1, c0, c1 = bounds(pic)
    band_w, band_h = l1 - l0, t1 - t0
    want_w = round((s1 - s0) * band_w / band_h)
    if want_w <= c1 - c0:  # wider than the band: trim both sides
        c0 += (c1 - c0 - want_w) // 2
        c1 = c0 + want_w
    else:  # taller: trim top and bottom
        want_h = round((c1 - c0) * band_h / band_w)
        s0 += (s1 - s0 - want_h) // 2
        s1 = s0 + want_h
    crop = Image.fromarray(pic[s0:s1, c0:c1]).resize((band_w, band_h), Image.LANCZOS)
    out = Image.new("RGB", (ref.shape[1], ref.shape[0]), (0, 0, 0))
    out.paste(crop, (l0, t0))
    with tempfile.TemporaryDirectory() as tmp:
        png = os.path.join(tmp, "mainmenuwallpaper.png")
        out.save(png)
        r = subprocess.run([texconv(), "-nologo", "-y", "-f", "BC7_UNORM", "-o", tmp, png], capture_output=True, text=True)
        assert r.returncode == 0, f"texconv failed: {r.stdout}{r.stderr}"
        dds = next(os.path.join(tmp, f) for f in os.listdir(tmp) if f.lower() == "mainmenuwallpaper.dds")
        shutil.move(dds, src)
    print(f"picture rows {s0}-{s1}, cols {c0}-{c1} of {pic.shape[1]}x{pic.shape[0]} -> Vel'dun band rows {t0}-{t1} "
          f"of {ref.shape[1]}x{ref.shape[0]}; wrote {src}")


if __name__ == "__main__":
    main()
