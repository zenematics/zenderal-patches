"""Build the ichor-puddle meshes for `Zenderal - Ichor Goo No Glow` from the installed JS Dwemer Ichor Barrels SE.

JS's `clutter\\dwemer\\dweichorgoo01/02.nif` (the green Dwemer ichor puddles, e.g. DweIchorGoo02 088896)
hang two effects off the root BSFadeNode beside the puddle shape:
  - `PCloud0N-Emitter`  a NiParticleSystem of additive green haze puffs;
  - `ENBLight`          a billboard LightMesh that ENB turns into a green point light, washing the
                        surrounding clutter green.
This script detaches exactly those two children (their root child ref -> -1). The puddle shape and the
`L2_warp0N` shimmer billboard are kept. Orphaned blocks stay in the file unreferenced, so the output
is byte-identical to JS's file apart from 8 bytes.

The meshes are JS's work, so they are generated from the user's own install, never committed.

Usage:  python 01-strip-goo-glow.py [<mods dir>] [--dry-run]     (default E:/Zenderal/mods)
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'HorseCloakFluffFix', 'tools'))
from nif import Nif, Reader  # noqa: E402

MOD = 'Zenderal - Ichor Goo No Glow'
JS_MOD = 'JS Dwemer Ichor Barrels SE'
MESH_DIR = os.path.join('meshes', 'clutter', 'dwemer')
MESHES = ['dweichorgoo01.nif', 'dweichorgoo02.nif']
NODE_TYPES = ('NiNode', 'BSFadeNode', 'NiBillboardNode')


def node_name(nif, i):
    typ, p, _ = nif.blocks[i]
    if typ not in NODE_TYPES:
        return None
    return nif.string(Reader(nif.data, p).take('i'))


def strip(src, dst, dry):
    nif = Nif(src)
    typ, p, _ = nif.blocks[0]
    assert typ == 'BSFadeNode', typ
    r = Reader(nif.data, p)
    r.skip(4)                                   # name
    r.skip(4 * r.take('I'))                     # extra data refs
    r.skip(4 + 4 + 12 + 36 + 4 + 4)             # controller, flags, translation, rotation, scale, collision
    count = r.take('I')
    dropped = []
    for k in range(count):
        at = r.p + 4 * k
        ref = struct.unpack_from('<i', nif.data, at)[0]
        name = node_name(nif, ref) if ref >= 0 else None
        if name and (name == 'ENBLight' or name.startswith('PCloud')):
            struct.pack_into('<i', nif.data, at, -1)
            dropped.append(name)
    assert len(dropped) == 2, (src, dropped)    # one particle cloud + one ENB light, nothing else
    print(f'{os.path.basename(src)}: detached {dropped}')
    if not dry:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, 'wb') as f:
            f.write(nif.data)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    dry = '--dry-run' in sys.argv
    mods = args[0] if args else 'E:/Zenderal/mods'
    for name in MESHES:
        strip(os.path.join(mods, JS_MOD, MESH_DIR, name), os.path.join(mods, MOD, MESH_DIR, name), dry)


if __name__ == '__main__':
    main()
