"""Dakeyras' Tracker cuirass without its mouth wrap (curator, 2026-11-19: "remove the tracker helmet / mask too").

The Set of the Tracker's cuirass mesh (Enderal's BosmerArmorMATY743 torsoMetal, the list's winning copy is Pretty
Enderal Armory's) carries the face wrap as its own shape, `BBHatMaskBCollar`. This copies the winning weight-0 and
weight-1 meshes to
    meshes\\Zenderal\\FogWood\\DakeyrasCuirass_0.nif / _1.nif
with that one shape's NiAVObject Hidden flag set (bit 0; geometry, skin and shaders untouched, so the body under it
is exactly Pretty's), into Zenderal - Patch Collection (not committed). tools/02's ARMA 0x83A points the male world
model at the _1 copy (the engine finds _0 by name); the first-person model stays Pretty's (no wrap in it).

Usage: python src/FogWood/tools/05-build-dakeyras-cuirass.py [--target <MO2 mod folder>]
Rerun after a Pretty Enderal Armory update.
"""
import argparse
import importlib.util
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
SR_TOOLS = os.path.join(ROOT, 'src', 'StingAndRise', 'tools')
sys.path.insert(0, SR_TOOLS)
import nifse  # noqa: E402
import surface  # noqa: E402

TOOLS = json.load(open(os.path.join(ROOT, '.claude', 'config', 'tools.json'), encoding='utf-8-sig'))
SOURCE = 'armor/BosmerArmorMATY743/torsoMetal_%d.nif'
OUT_REL = os.path.join('meshes', 'Zenderal', 'FogWood', 'DakeyrasCuirass_%d.nif')
MASK = 'BBHatMaskBCollar'
HIDDEN = 0x1


def shape_name(nif, i):
    return nif.string(struct.unpack_from('<I', nif.blocks[i], 0)[0])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--target', default=os.path.join(TOOLS['modlistRoot'], 'mods', 'Zenderal - Patch Collection'))
    args = ap.parse_args()
    spec = importlib.util.spec_from_file_location('sr_assets', os.path.join(SR_TOOLS, '01-build-assets.py'))
    sr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sr)
    for weight in (0, 1):
        src, nif = surface.winning_model(sr, SOURCE % weight)
        hidden = []
        for i, b in enumerate(nif.blocks):
            if nif.btype(i) in ('BSTriShape', 'BSDynamicTriShape', 'BSSubIndexTriShape') and shape_name(nif, i) == MASK:
                f = nifse.av_fields(b)
                flags = struct.unpack_from('<I', b, f['flags'])[0]
                nb = bytearray(b)
                struct.pack_into('<I', nb, f['flags'], flags | HIDDEN)
                nif.blocks[i] = bytes(nb)
                hidden.append((i, flags, flags | HIDDEN))
        assert len(hidden) == 1, (SOURCE % weight, 'mask shapes found:', hidden)
        out = os.path.join(args.target, OUT_REL % weight)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        data = nif.tobytes()
        open(out, 'wb').write(data)
        print('%s <- %s (%s): block %d %s flags 0x%X -> 0x%X, %d bytes' % (OUT_REL % weight, SOURCE % weight, os.path.basename(str(src)), hidden[0][0], MASK, hidden[0][1], hidden[0][2], len(data)))
        # read back: the flag is set and nothing else moved
        back = nifse.Nif(data)
        assert len(back.blocks) == len(nif.blocks)
        i = hidden[0][0]
        assert struct.unpack_from('<I', back.blocks[i], nifse.av_fields(back.blocks[i])['flags'])[0] & HIDDEN


if __name__ == '__main__':
    main()
