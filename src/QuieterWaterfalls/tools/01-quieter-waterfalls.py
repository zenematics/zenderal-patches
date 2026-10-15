#!/usr/bin/env python3
"""Turn every waterfall / rapids sound down for Zenderal - Quieter Waterfalls.esp.

Why: waterfalls drown out other sound. Reverb and Ambiance Overhaul - Enderal (RAO) wins
67 of the 72 waterfall/rapids SoundDescriptors and LOWERED StaticAttenuation (= louder) on
many of them, the distant loops most of all (AMBWaterfallLargeDistantLPSD 5.29 -> 2,
...MediumDistantCloseLPSD 5.29 -> 1, ...MediumDistantLPSD 7.93 -> 0). Waterfalls have no
category of their own - they share AudioCategoryMuteSubmerged / RAO's ambient category
with cave drips, wind, ship creaks - so a category volume cannot target them.

Rule: every SoundDescriptor whose EditorID matches WATER_RE gets
  StaticAttenuation = winner's value + EXTRA_DB   (dB; higher = quieter; absent = 0)
Source record = the live winner: RAO's YAML where RAO overrides it, else base Enderal's
(FS over Skyrim). Everything else in the winner is forwarded verbatim.

Winner set was established by scanning every ACTIVE plugin in the 'Zenderal Alpha 0.3'
profile for waterfall EditorIDs: only Skyrim.esm, Enderal - Forgotten Stories.esm,
Audio Overhaul Skyrim.esp (204) and RAO (227) carry them, and RAO overrides every record
Audio Overhaul does - so AOS never wins. Re-run that scan if the audio mods change.

Inputs (regenerate with /spriggit-decompile-reference):
  reference/base/{Skyrim,EnderalFS}/SoundDescriptors
  reference/mods/RAO   (Reverb and Ambiance Overhaul - Enderal.esp)
  reference/mods/PrettyContext/Audio Overhaul Skyrim   (asserted to never win)
Second rule: the coast wind bed near Ark gets an attenuating output model - see WINDBED.

Output: src/QuieterWaterfalls/QuieterWaterfallsESP/SoundDescriptors/*.yaml (regenerated)
"""
import glob
import os
import re
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
BASE = os.path.join(ROOT, "reference", "base")
RAO = os.path.join(ROOT, "reference", "mods", "RAO", "SoundDescriptors")
AOS = os.path.join(ROOT, "reference", "mods", "PrettyContext", "Audio Overhaul Skyrim", "SoundDescriptors")
OUT = os.path.join(ROOT, "src", "QuieterWaterfalls", "QuieterWaterfallsESP", "SoundDescriptors")

EXTRA_DB = 6.0
WATER_RE = re.compile(r"aterfall|WaterRapids", re.I)
EXPECTED = 72

# The "waterfall" that cut in approaching Ark (found 2026-10-15 by moving RAO's Ambiance loops onto
# other audio sliders until one slider alone silenced it): AMBrWindBedCoastLP. Its only marker
# (13C956, cell CapitalCityWatchTowerSouth -6,0 on Ark's west shore) plays it through SOMStereo
# 07EDCA, which has NO AttenuatesWithDistance - so the bed starts at full level the moment that
# cell attaches (2 cells out, from any direction) and cuts off when it detaches. Re-pointed at
# SOMStereoRad05000Linear 09173E (linear stereo, 200-5000 vanilla / 200-7500 under Audio Overhaul -
# silent before the cell can attach at 8192), the model vanilla's own AMBWindloopMountainsCLPSD
# uses. RAO's winning descriptor is forwarded with only OutputModel changed. Also safe for any
# region use: region sounds play at the listener, where an attenuating model is at full volume.
WINDBED = "0DB6DD:Skyrim.esm"           # AMBrWindBedCoastLP
WINDBED_FROM = "07EDCA:Skyrim.esm"      # SOMStereo
WINDBED_TO = "09173E:Skyrim.esm"        # SOMStereoRad05000Linear


def index(folder):
    out = {}
    for f in glob.glob(os.path.join(folder, "*.yaml")):
        t = open(f, encoding="utf-8").read()
        out[re.search(r"^FormKey: ([^\r\n]+)", t, re.M).group(1)] = (f, t)
    return out


def fmt(x):
    return str(int(x)) if float(x).is_integer() else f"{x:.2f}".rstrip("0")


def main():
    base = index(os.path.join(BASE, "Skyrim", "SoundDescriptors"))
    base.update(index(os.path.join(BASE, "EnderalFS", "SoundDescriptors")))
    rao = index(RAO)
    aos = index(AOS)
    if not rao:
        sys.exit("reference/mods/RAO is empty - serialize Reverb and Ambiance Overhaul - Enderal.esp first")

    targets = [fk for fk, (_, t) in base.items()
               if WATER_RE.search(re.search(r"^EditorID: ([^\r\n]+)", t, re.M).group(1))]
    stray = [fk for fk in aos if fk in targets and fk not in rao]
    if stray:
        sys.exit(f"Audio Overhaul wins {stray} - this script assumes RAO overrides all of AOS's waterfalls")

    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    rows = []
    for fk in targets:
        path, text = rao[fk] if fk in rao else base[fk]
        m = re.search(r"^StaticAttenuation: ([\d.]+)$", text, re.M)
        old = float(m.group(1)) if m else 0.0
        new = min(old + EXTRA_DB, 100.0)
        line = f"StaticAttenuation: {fmt(new)}"
        if m:
            text = text[:m.start()] + line + text[m.end():]
        else:
            text, n = re.subn(r"^(Priority: \d+)$", lambda mm: mm.group(1) + "\n" + line, text, count=1, flags=re.M)
            if n != 1:
                sys.exit(f"{fk}: no Priority line to anchor StaticAttenuation after")
        with open(os.path.join(OUT, os.path.basename(path)), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        eid = re.search(r"^EditorID: ([^\r\n]+)", text, re.M).group(1)
        rows.append(f"{eid[:62]:<62} {'RAO ' if fk in rao else 'base'} {fmt(old):>6} -> {fmt(new)}")

    for r in sorted(rows):
        print(r)
    if len(rows) != EXPECTED:
        sys.exit(f"expected {EXPECTED} waterfall descriptors, wrote {len(rows)} - review before updating EXPECTED")
    print(f"OK: {len(rows)} waterfall/rapids sounds +{fmt(EXTRA_DB)} dB")

    if WINDBED not in rao:
        sys.exit(f"{WINDBED}: expected RAO to win the coast wind bed")
    path, text = rao[WINDBED]
    text, n = re.subn(r"^OutputModel: " + re.escape(WINDBED_FROM) + r"$", "OutputModel: " + WINDBED_TO, text, flags=re.M)
    if n != 1:
        sys.exit(f"{WINDBED}: OutputModel is no longer {WINDBED_FROM} in {path} - re-check before forcing")
    with open(os.path.join(OUT, os.path.basename(path)), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print(f"OK: coast wind bed {WINDBED} {WINDBED_FROM} -> {WINDBED_TO}")


if __name__ == "__main__":
    main()
