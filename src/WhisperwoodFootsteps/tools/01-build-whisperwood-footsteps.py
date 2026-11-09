"""Generate `WhisperwoodFootstepsESP/`: footsteps on Whisperwood's soil.

Player report (2026-11-03, GreaseLord): no footstep sounds on the soil in the Whisperwood, only on roads and rocks.
Whisperwood's soil is base Enderal's `_00E_PilzwaldDirt 016680` (29% of the region's ground) and
`_00E_PilzwaldDirt_Fern 02142D`; SureAI gave both `MaterialOrganicLarge 0D309F`, the material for flesh and large
creatures. No footstep impact set maps that material - neither base Enderal's 18 `FST*ImpactSet`s nor Audio Overhaul's
21 - so the ground is silent even in stock Enderal, and weapon/spell impacts on it use the flesh entries.
They are the only two landscape textures with that material, and no list plugin overrides them (scan 2026-11-08).

Each override is base Enderal 2.1's record verbatim with `MaterialType` -> `MaterialDirt 012F38`, the material of
the region's other dirt textures (`LReachDirt01`, `LPineForest01/02`, `LDirt01`).

Usage: python 01-build-whisperwood-footsteps.py [<reference/base-2.1.4.4 dir>]
"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REF = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "..", "..", "reference", "base-2.1.4.4")
OUT = os.path.join(HERE, "..", "WhisperwoodFootstepsESP", "LandscapeTextures")
RECORDS = ["_00E_PilzwaldDirt - 016680_Skyrim.esm.yaml", "_00E_PilzwaldDirt_Fern - 02142D_Skyrim.esm.yaml"]
OLD = b"MaterialType: 0D309F:Skyrim.esm"
NEW = b"MaterialType: 012F38:Skyrim.esm"

if os.path.isdir(OUT):
    shutil.rmtree(OUT)
os.makedirs(OUT)
for name in RECORDS:
    src = None
    for root in ("EnderalFS", "Skyrim"):  # Forgotten Stories wins if it overrides one
        p = os.path.join(REF, root, "LandscapeTextures", name)
        if os.path.isfile(p):
            src = p
            break
    if not src:
        raise SystemExit("not found: " + name)
    raw = open(src, "rb").read()
    if raw.count(OLD) != 1:
        raise SystemExit(f"{name}: expected one {OLD.decode()}, found {raw.count(OLD)} - re-check the record")
    open(os.path.join(OUT, name), "wb").write(raw.replace(OLD, NEW))
    print(f"{name.split(' - ')[0]}: MaterialOrganicLarge -> MaterialDirt ({os.path.basename(os.path.dirname(os.path.dirname(src)))})")
