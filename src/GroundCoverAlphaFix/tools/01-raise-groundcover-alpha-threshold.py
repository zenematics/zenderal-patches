"""Build the ground cover meshes for `Zenderal - Ground Cover Alpha Fix` from the installed Fixed Mesh Lighting.

Enderal's tropical ground cover (`_00E_TropicalTree_GroundCover01/02`, Starling city and the jungle) is a flat
square of leaves cut out by alpha test, with threshold 0: every texel above alpha 0 is drawn. That works with
Enderal's own `coverground01/02.dds`, whose background is alpha 0. ETATU - Plants Leaves Grass Upscaled 2x
replaces both with 2x upscales whose background came out at alpha 1-15 (about 41% of texels, against 1% in
Enderal's), so the whole square is drawn in the light green under it.

This copies Fixed Mesh Lighting's two meshes (the winners; their alpha settings are identical to Enderal's)
and raises the NiAlphaProperty threshold of the one shape from 0 to 128, the usual foliage cutoff. It asserts
each mesh has exactly one alpha property, with alpha test on and threshold 0, before changing one byte.

The meshes are the mod authors' work, so they are generated from the user's own install, never committed.

Usage:  python 01-raise-groundcover-alpha-threshold.py [<mods dir>] [--dry-run]     (default E:/Zenderal/mods)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'HorseCloakFluffFix', 'tools'))
from nif import Nif, Reader  # noqa: E402

MOD = 'Zenderal - Ground Cover Alpha Fix'
SRC_MOD = 'Enderal - Fixed Mesh Lighting'
DIR = os.path.join('meshes', 'enderal', 'landscape', 'tropical', 'vegetation')
MESHES = ('groundcover01.nif', 'groundcover02.nif')
THRESHOLD = 128


def raise_threshold(src, dst, dry):
    nif = Nif(src)
    alphas = [i for i, (typ, _, _) in enumerate(nif.blocks) if typ == 'NiAlphaProperty']
    assert len(alphas) == 1, (src, alphas)
    r = Reader(nif.data, nif.blocks[alphas[0]][1])
    r.skip(4)                                   # name
    r.skip(4 * r.take('I'))                     # extra data refs
    r.skip(4)                                   # controller
    flags = r.take('H')
    at = r.p
    assert flags & 0x200, (src, hex(flags))     # alpha test on
    assert nif.data[at] == 0, (src, nif.data[at])
    nif.data[at] = THRESHOLD
    print(f'{os.path.basename(src)}: alpha flags {flags:#06x}, threshold 0 -> {THRESHOLD}')
    if not dry:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, 'wb') as f:
            f.write(nif.data)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    dry = '--dry-run' in sys.argv
    mods = args[0] if args else 'E:/Zenderal/mods'
    for m in MESHES:
        raise_threshold(os.path.join(mods, SRC_MOD, DIR, m), os.path.join(mods, MOD, DIR, m), dry)


if __name__ == '__main__':
    main()
